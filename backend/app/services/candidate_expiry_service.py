"""Story 2.5.X Task 9 — Expired candidate 自动归档 cron service.

每日扫描所有 vault `节点/*.md` 的 frontmatter `error_candidates[]`,
将 created_at < now - 30d AND status == pending 的标记为 expired.

不删除候选 (保留 frontmatter 供未来训练 prompt), 仅状态变更 + Dashboard 折叠显示.

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

import asyncio
import time as _time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import structlog
import yaml
from pydantic import BaseModel, Field

from app.services.candidate_service import (
    _atomic_write_frontmatter,
    _read_frontmatter_dict,
)
from app.services.candidate_state_machine import apply_status_change
from app.services.error_rebuild_service import _scan_vault_md_files
from app.services.error_writer import _get_file_lock

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════════


DEFAULT_EXPIRY_DAYS = 30


class ExpireFailure(BaseModel):
    """单条 expire 失败记录."""

    file: str
    candidate_id: str | None = None
    reason: str


class ExpireStats(BaseModel):
    """Story 2.5.X AC #2 + Task 9 — expire_pending_candidates 返回值."""

    expiry_days: int = DEFAULT_EXPIRY_DAYS
    cutoff_iso: str = Field(..., description="created_at 阈值 (ISO 8601 UTC)")
    total_files_scanned: int = 0
    total_pending_scanned: int = 0
    total_expired: int = 0
    failed: int = 0
    failures: list[ExpireFailure] = Field(default_factory=list)
    elapsed_ms: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_created_at(value: Any) -> datetime | None:
    """容错解析 created_at 字段 (ISO 8601 / datetime obj / None)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            # Python 3.11+ fromisoformat 支持 'Z' / 微秒
            iso_str = value.replace("Z", "+00:00") if value.endswith("Z") else value
            dt = datetime.fromisoformat(iso_str)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None
    return None


def _is_expired(candidate: dict[str, Any], cutoff: datetime) -> bool:
    """判断 candidate 是否应被 expired (status=pending AND created_at < cutoff)."""
    if (candidate.get("status") or "pending") != "pending":
        return False
    created = _parse_created_at(candidate.get("created_at"))
    if created is None:
        # 无 created_at 字段 → 保守不 expire (避免误伤无时间戳的旧数据)
        return False
    return created < cutoff


# ═══════════════════════════════════════════════════════════════════════════════
# Task 9 — expire_pending_candidates
# ═══════════════════════════════════════════════════════════════════════════════


async def expire_pending_candidates(
    vault_root: str | Path,
    *,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
    now: datetime | None = None,
) -> ExpireStats:
    """Story 2.5.X Task 9 + AC #2 — 自动归档过期候选 (status=pending AND created_at >= 30d ago).

    幂等性: 已 expired 的 candidate 不再处理 (status 不是 pending).
    并发安全: 每个文件用 _get_file_lock per-file lock.
    单条失败: 不中断, 记入 failures[].

    Args:
        vault_root: vault 根目录绝对路径
        expiry_days: 过期阈值 (默认 30 天, 测试时可传更短)
        now: 时间基准 (默认 datetime.now(UTC), 测试时可注入)

    Returns:
        ExpireStats — total/expired/failed counts + failures details

    Logging:
        每条 expire 触发 structlog info (含 file/candidate_id/created_at)
        每条失败触发 structlog warning
    """
    start = _time.monotonic()
    if now is None:
        now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=expiry_days)

    vault = Path(vault_root)
    if not vault.exists():
        return ExpireStats(
            expiry_days=expiry_days,
            cutoff_iso=cutoff.isoformat(),
            elapsed_ms=round((_time.monotonic() - start) * 1000.0, 2),
        )

    md_files = _scan_vault_md_files(vault)
    total_files_scanned = len(md_files)
    total_pending_scanned = 0
    total_expired = 0
    failed = 0
    failures: list[ExpireFailure] = []

    for f in md_files:
        # 文件 read-modify-write 在 per-file lock 内
        lock = _get_file_lock(f)
        async with lock:
            try:
                fm_dict, body = await asyncio.to_thread(_read_frontmatter_dict, f)
            except Exception as e:
                failed += 1
                failures.append(ExpireFailure(file=str(f), reason=f"parse: {e}"))
                logger.warning(
                    "candidate_expiry.parse_failed", file=str(f), error=str(e)
                )
                continue

            candidates = fm_dict.get("error_candidates") or []
            if not isinstance(candidates, list):
                continue

            file_expired_count = 0
            for cand in candidates:
                if not isinstance(cand, dict):
                    continue
                if (cand.get("status") or "pending") == "pending":
                    total_pending_scanned += 1
                if not _is_expired(cand, cutoff):
                    continue

                # apply_status_change pending → expired (changed_by="system")
                try:
                    apply_status_change(cand, "expired", changed_by="system")
                    file_expired_count += 1
                    total_expired += 1
                    logger.info(
                        "candidate_expiry.expired",
                        file=str(f),
                        candidate_id=cand.get("id"),
                        created_at=cand.get("created_at"),
                        cutoff=cutoff.isoformat(),
                    )
                except Exception as e:
                    failed += 1
                    failures.append(
                        ExpireFailure(
                            file=str(f),
                            candidate_id=cand.get("id"),
                            reason=f"state_change: {e}",
                        )
                    )
                    logger.warning(
                        "candidate_expiry.state_change_failed",
                        file=str(f),
                        candidate_id=cand.get("id"),
                        error=str(e),
                    )

            # 仅当有 expire 改动时才写回 (避免无意义的文件 mtime 更新)
            if file_expired_count > 0:
                try:
                    fm_dict["error_candidates"] = candidates
                    await asyncio.to_thread(
                        _atomic_write_frontmatter, f, fm_dict, body
                    )
                except Exception as e:
                    failed += 1
                    failures.append(
                        ExpireFailure(file=str(f), reason=f"write: {e}")
                    )
                    logger.warning(
                        "candidate_expiry.write_failed", file=str(f), error=str(e)
                    )

    elapsed_ms = (_time.monotonic() - start) * 1000.0
    logger.info(
        "candidate_expiry.completed",
        expiry_days=expiry_days,
        total_files_scanned=total_files_scanned,
        total_pending_scanned=total_pending_scanned,
        total_expired=total_expired,
        failed=failed,
        elapsed_ms=round(elapsed_ms, 2),
    )

    return ExpireStats(
        expiry_days=expiry_days,
        cutoff_iso=cutoff.isoformat(),
        total_files_scanned=total_files_scanned,
        total_pending_scanned=total_pending_scanned,
        total_expired=total_expired,
        failed=failed,
        failures=failures,
        elapsed_ms=round(elapsed_ms, 2),
    )
