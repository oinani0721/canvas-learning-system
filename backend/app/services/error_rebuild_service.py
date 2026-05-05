"""Story 2.5.X Task 5 — rebuild Graphiti from frontmatter errors[].

兜底机制 (AC #6):
- 扫描 vault 所有 节点/*.md 的 frontmatter errors[]
- 调 write_error_to_graphiti 写入知识图谱
- 用户场景: 切设备 / Graphiti 失败丢失 / 主动重建索引

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

import asyncio
import time as _time
from pathlib import Path
from typing import Any, Optional

import structlog
import yaml
from pydantic import BaseModel, Field

from app.graphiti.entity_types import (
    ErrorType,
    PedagogyErrorType,
    RemedyStrategy,
)
from app.services.error_classifier import ClassifiedError
from app.services.error_writer import _split_frontmatter, write_error_to_graphiti

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class RebuildFailure(BaseModel):
    """单条失败记录."""

    file: str
    error_id: Optional[str] = None
    reason: str


class RebuildStats(BaseModel):
    """AC #6 — rebuild_graphiti 服务返回值."""

    group_id: str
    dry_run: bool = Field(
        default=False, description="True 仅扫描计数, 不调 Graphiti"
    )
    total_files_scanned: int = 0
    total_errors_scanned: int = 0
    newly_written: int = Field(default=0, description="dry_run=True 时为 0")
    failed: int = 0
    failures: list[RebuildFailure] = Field(default_factory=list)
    elapsed_ms: float


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _err_record_to_classified(record: dict[str, Any]) -> ClassifiedError:
    """从 frontmatter errors[] 单条 dict 重建 ClassifiedError (用于写 Graphiti)."""
    pedagogy_str = record.get("type") or "conceptual_confusion"
    legacy_str = record.get("legacy_type") or "knowledge_gap"
    legacy_remedy_str = record.get("legacy_remedy") or "backtrack_definition"
    remedy_strategies_str = record.get("remedy_strategies") or []
    sub_tags = record.get("tags") or []

    try:
        pedagogy_type = PedagogyErrorType(pedagogy_str)
    except ValueError:
        pedagogy_type = PedagogyErrorType.CONCEPTUAL_CONFUSION

    try:
        legacy_type = ErrorType(legacy_str)
    except ValueError:
        legacy_type = ErrorType.KNOWLEDGE_GAP

    try:
        legacy_remedy = RemedyStrategy(legacy_remedy_str)
    except ValueError:
        legacy_remedy = RemedyStrategy.BACKTRACK_DEFINITION

    pedagogy_remedies = []
    for r_str in remedy_strategies_str:
        try:
            pedagogy_remedies.append(RemedyStrategy(r_str))
        except ValueError:
            continue

    return ClassifiedError(
        legacy_type=legacy_type,
        pedagogy_type=pedagogy_type,
        description=record.get("description", ""),
        context=record.get("context", ""),
        confidence=float(record.get("confidence", 0.5)),
        legacy_remedy=legacy_remedy,
        pedagogy_remedies=pedagogy_remedies,
        sub_tags=list(sub_tags),
    )


def _scan_vault_md_files(vault_root: Path) -> list[Path]:
    """扫描 vault 节点/*.md (扁平架构, Round-11 固化).

    fallback 1: 节点/ 不存在 → 扫描 vault_root/*.md (兼容根目录节点)
    fallback 2: 都没有 → 返回空列表
    """
    nodes_dir = vault_root / "节点"
    if nodes_dir.exists() and nodes_dir.is_dir():
        return sorted(nodes_dir.glob("*.md"))
    # fallback: 根目录 .md 文件
    if vault_root.exists() and vault_root.is_dir():
        return sorted(p for p in vault_root.glob("*.md") if p.is_file())
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# Task 5 — rebuild_graphiti_from_frontmatter
# ═══════════════════════════════════════════════════════════════════════════════


async def rebuild_graphiti_from_frontmatter(
    vault_root: str | Path,
    group_id: str,
    *,
    dry_run: bool = False,
) -> RebuildStats:
    """Story 2.5.X Task 5 + AC #6 — 从 frontmatter errors[] 重建 Graphiti misconception entities.

    用户场景:
    - 切设备 / 重建索引: dry_run=True 先看会写多少, 再 dry_run=False 实际跑
    - Graphiti 写入丢失: rebuild 兜底从本地 frontmatter 重新填充

    Args:
        vault_root: vault 根目录绝对路径
        group_id: Graphiti namespace (如 "vault:cs_61b" or "cs_61b:main")
        dry_run: True 仅扫描计数, 不调 Graphiti; False 实际写入

    Returns:
        RebuildStats — 含 total/written/failed counts + 失败详情

    Failure handling:
    - 单条失败 (file 损坏 / classifier 构造失败 / Graphiti 写入失败) → 记录到 failures[]
    - 不中断, 继续处理后续 errors
    - structlog warning 记录每条失败 (含 file path + error_id + reason)
    """
    start = _time.monotonic()
    vault = Path(vault_root)
    if not vault.exists():
        return RebuildStats(
            group_id=group_id,
            dry_run=dry_run,
            elapsed_ms=round((_time.monotonic() - start) * 1000.0, 2),
        )

    md_files = _scan_vault_md_files(vault)
    total_files_scanned = len(md_files)
    total_errors_scanned = 0
    newly_written = 0
    failed = 0
    failures: list[RebuildFailure] = []

    for f in md_files:
        # 解析 frontmatter (单文件失败不影响其他)
        try:
            text = f.read_text(encoding="utf-8")
            fm_str, _ = _split_frontmatter(text)
            fm_dict = yaml.safe_load(fm_str) if fm_str else {}
            if not isinstance(fm_dict, dict):
                continue
            errors_list = fm_dict.get("errors") or []
            if not isinstance(errors_list, list):
                continue
        except Exception as e:
            failed += 1
            failures.append(RebuildFailure(file=str(f), reason=f"parse_failed: {e}"))
            logger.warning(
                "error_rebuild.parse_failed",
                file=str(f),
                error=str(e),
            )
            continue

        # 推断 node_id 用于 Graphiti metadata (vault-relative path)
        try:
            node_id = str(f.relative_to(vault))
        except ValueError:
            node_id = f.name

        for err_record in errors_list:
            if not isinstance(err_record, dict):
                continue
            total_errors_scanned += 1

            if dry_run:
                continue

            err_id = err_record.get("id")

            # 构造 ClassifiedError (失败 → 记录但继续)
            try:
                classified = _err_record_to_classified(err_record)
            except Exception as e:
                failed += 1
                failures.append(
                    RebuildFailure(
                        file=str(f),
                        error_id=err_id,
                        reason=f"classify_failed: {e}",
                    )
                )
                logger.warning(
                    "error_rebuild.classify_failed",
                    file=str(f),
                    error_id=err_id,
                    error=str(e),
                )
                continue

            # 写 Graphiti (失败 → 记录但继续)
            try:
                ok = await write_error_to_graphiti(
                    classified,
                    node_id=node_id,
                    session_id="",
                    error_id=err_id,
                )
                if ok:
                    newly_written += 1
                else:
                    failed += 1
                    failures.append(
                        RebuildFailure(
                            file=str(f),
                            error_id=err_id,
                            reason="graphiti_write_failed",
                        )
                    )
                    logger.warning(
                        "error_rebuild.graphiti_write_failed",
                        file=str(f),
                        error_id=err_id,
                    )
            except Exception as e:
                failed += 1
                failures.append(
                    RebuildFailure(
                        file=str(f),
                        error_id=err_id,
                        reason=f"unexpected: {e}",
                    )
                )
                logger.warning(
                    "error_rebuild.unexpected_error",
                    file=str(f),
                    error_id=err_id,
                    error=str(e),
                )

    elapsed_ms = (_time.monotonic() - start) * 1000.0
    logger.info(
        "error_rebuild.completed",
        group_id=group_id,
        dry_run=dry_run,
        total_files_scanned=total_files_scanned,
        total_errors_scanned=total_errors_scanned,
        newly_written=newly_written,
        failed=failed,
        elapsed_ms=round(elapsed_ms, 2),
    )

    return RebuildStats(
        group_id=group_id,
        dry_run=dry_run,
        total_files_scanned=total_files_scanned,
        total_errors_scanned=total_errors_scanned,
        newly_written=newly_written,
        failed=failed,
        failures=failures,
        elapsed_ms=round(elapsed_ms, 2),
    )
