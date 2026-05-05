"""Story 2.5.X Task 3+4 — Candidate accept/dismiss/dispute service.

业务逻辑层 (endpoint 调本服务, 本服务复用 error_writer + state_machine):

- accept_candidate: candidate (pending) → errors[] + Graphiti, status → accepted/edited
- dismiss_candidate: candidate → status=dismissed, 不入 errors[]
- dispute_candidate: candidate → status=disputed + dispute_reason, 不入 errors[]

原子性保证: 同一 file_path 用 _get_file_lock per-file async lock 防并发竞态.

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import structlog
import yaml
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.graphiti.entity_types import (
    ErrorType,
    PedagogyErrorType,
    RemedyStrategy,
)
from app.services.candidate_state_machine import (
    apply_status_change,
    validate_status_transition,
)
from app.services.error_classifier import ClassifiedError
from app.services.error_writer import (
    _get_file_lock,
    _make_dedupe_hash,
    _split_frontmatter,
    write_error_to_graphiti,
)

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class CandidateEdits(BaseModel):
    """用户接受 candidate 时可选编辑的字段 (AC #5)."""

    description: Optional[str] = Field(default=None, description="覆盖错误描述")
    pedagogy_type: Optional[str] = Field(default=None, description="覆盖 4 主类标签")
    legacy_type: Optional[str] = Field(default=None, description="覆盖 Story 3.6 兼容标签")


class AcceptCandidateResult(BaseModel):
    """AC #5 — accept_candidate 服务返回值."""

    candidate_id: str
    error_id: str  # 移入 errors[] 后的 id
    status: str  # accepted | edited
    frontmatter_written: bool
    graphiti_status: str  # queued | ok | failed | skipped
    elapsed_ms: float


class DismissCandidateResult(BaseModel):
    """AC #7 — dismiss/dispute 服务返回值."""

    candidate_id: str
    status: str  # dismissed | disputed
    dispute_reason: Optional[str] = None
    frontmatter_written: bool
    elapsed_ms: float


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _read_frontmatter_dict(file_path: Path) -> tuple[dict[str, Any], str]:
    """读 .md 文件 → (frontmatter_dict, body)."""
    text = file_path.read_text(encoding="utf-8")
    fm_str, body = _split_frontmatter(text)
    fm_dict = yaml.safe_load(fm_str) if fm_str else {}
    if not isinstance(fm_dict, dict):
        fm_dict = {}
    return fm_dict, body


def _atomic_write_frontmatter(
    file_path: Path, fm_dict: dict[str, Any], body: str
) -> None:
    """原子写回 frontmatter + body (临时文件 + os.replace)."""
    new_fm = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False)
    new_text = f"---\n{new_fm}---\n{body}"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=file_path.parent,
        prefix=f".{file_path.name}.tmp",
    ) as tmp:
        tmp.write(new_text)
        tmp_path = tmp.name
    os.replace(tmp_path, file_path)


def _find_candidate(
    candidates: list[dict[str, Any]], candidate_id: str
) -> tuple[Optional[int], Optional[dict[str, Any]]]:
    """从 candidates[] 找 by id, 返回 (idx, candidate)."""
    for i, cand in enumerate(candidates):
        if isinstance(cand, dict) and cand.get("id") == candidate_id:
            return i, cand
    return None, None


def _candidate_to_classified_error(
    candidate: dict[str, Any], edits: Optional[CandidateEdits] = None
) -> ClassifiedError:
    """从 candidate dict + 用户 edits 构造 ClassifiedError.

    edits 优先级 > candidate 原值.
    """
    desc = candidate.get("description", "")
    pedagogy_str = candidate.get("pedagogy_type", "conceptual_confusion")
    legacy_str = candidate.get("legacy_type", "knowledge_gap")
    legacy_remedy_str = candidate.get("legacy_remedy", "backtrack_definition")
    pedagogy_remedies_str = candidate.get("suggested_remedy_strategies") or []
    sub_tags = candidate.get("sub_tags") or []
    confidence = candidate.get("confidence", 0.5)
    context_str = candidate.get("context", "")

    if edits:
        if edits.description is not None:
            desc = edits.description
        if edits.pedagogy_type is not None:
            pedagogy_str = edits.pedagogy_type
        if edits.legacy_type is not None:
            legacy_str = edits.legacy_type

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
    for r_str in pedagogy_remedies_str:
        try:
            pedagogy_remedies.append(RemedyStrategy(r_str))
        except ValueError:
            continue

    return ClassifiedError(
        legacy_type=legacy_type,
        pedagogy_type=pedagogy_type,
        description=desc,
        context=context_str,
        confidence=float(confidence),
        legacy_remedy=legacy_remedy,
        pedagogy_remedies=pedagogy_remedies,
        sub_tags=list(sub_tags),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Task 3 — accept_candidate
# ═══════════════════════════════════════════════════════════════════════════════


async def accept_candidate(
    file_path: str | Path,
    candidate_id: str,
    *,
    user_edits: Optional[CandidateEdits] = None,
    session_id: str = "",
    fire_and_forget_graphiti: bool = True,
) -> AcceptCandidateResult:
    """Story 2.5.X Task 3 + AC #5 — 接受候选错误, 移入 errors[] + Graphiti.

    流程 (per-file lock 内原子操作):
      1. 读 frontmatter → 找 candidate by id (不存在 → 404)
      2. 状态机校验 pending → accepted/edited (反向/终态间 → 422)
      3. 应用 user_edits 构造 ClassifiedError
      4. errors[] 追加新条 (含 user_confirmed=true / source=user_confirmed_ai)
      5. error_candidates[] 中 candidate.status 改为 accepted/edited (apply_status_change)
      6. 原子写回 frontmatter
      7. 写 Graphiti (fire-and-forget 默认)
      8. 返回 AcceptCandidateResult

    Args:
        file_path: 节点 .md 路径
        candidate_id: error_candidates[].id 要 accept 的那条
        user_edits: 可选编辑 (描述/类型覆盖)
        session_id: 当前 session ID (写入 errors[].session_id)
        fire_and_forget_graphiti: True 默认 → 后台 task; False 同步等待

    Returns:
        AcceptCandidateResult

    Raises:
        HTTPException(404): candidate 不存在
        HTTPException(422): candidate 状态非 pending (反向/终态间不可逆)
        HTTPException(500): file 读写失败
    """
    import time as _time

    start = _time.monotonic()
    p = Path(file_path)
    if not p.exists():
        raise HTTPException(
            status_code=404, detail=f"Node file not found: {file_path}"
        )

    lock = _get_file_lock(p)
    async with lock:
        # 读 frontmatter
        try:
            fm_dict, body = await asyncio.to_thread(_read_frontmatter_dict, p)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read frontmatter: {e}"
            )

        candidates = fm_dict.get("error_candidates") or []
        if not isinstance(candidates, list):
            candidates = []

        idx, candidate = _find_candidate(candidates, candidate_id)
        if candidate is None:
            raise HTTPException(
                status_code=404, detail=f"Candidate {candidate_id} not found"
            )

        # 状态机: 有 edits → "edited", 无 → "accepted"
        target_status = "edited" if user_edits else "accepted"
        # validate_status_transition + apply_status_change (抛 422 if illegal)
        apply_status_change(candidate, target_status, changed_by="user")

        # 应用 edits 构造 ClassifiedError
        try:
            classified = _candidate_to_classified_error(candidate, user_edits)
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Failed to construct error from candidate: {e}"
            )

        # errors[] 追加 (复用 candidate.id 作为 error_id, 与 frontmatter 一致)
        node_id_for_dedupe = candidate.get("node_id") or ""
        dedupe_hash = _make_dedupe_hash(classified, node_id_for_dedupe)
        now_iso = datetime.now(timezone.utc).isoformat()
        error_id = candidate_id  # AC #5: 复用 candidate_id 作为 error_id (frontmatter 一致)

        errors_list = fm_dict.get("errors") or []
        if not isinstance(errors_list, list):
            errors_list = []

        # errors[] dedupe (与 v1.0 同算法, 同 hash 的 corrected_at=null 视为重复 → update)
        existing_idx = None
        for i, rec in enumerate(errors_list):
            if (
                isinstance(rec, dict)
                and rec.get("dedupe_hash") == dedupe_hash
                and rec.get("corrected_at") is None
            ):
                existing_idx = i
                break

        if existing_idx is not None:
            existing = errors_list[existing_idx]
            existing["last_seen_at"] = now_iso
            existing["seen_count"] = int(existing.get("seen_count", 1)) + 1
            error_id = existing.get("id") or error_id
            existing["id"] = error_id
            logger.info(
                "candidate_service.accept_dedupe_into_existing_error",
                error_id=error_id,
                seen_count=existing["seen_count"],
            )
        else:
            new_error = {
                "id": error_id,
                "dedupe_hash": dedupe_hash,
                "type": classified.pedagogy_type.value,
                "legacy_type": classified.legacy_type.value,
                "legacy_remedy": classified.legacy_remedy.value,
                "description": classified.description,
                "corrected_at": None,
                "last_seen_at": now_iso,
                "seen_count": 1,
                "tags": list(classified.sub_tags),
                "remedy_strategies": [r.value for r in classified.pedagogy_remedies],
                "confidence": round(classified.confidence, 3),
                "created_at": now_iso,
                # Story 2.5.X 主权字段
                "source": "user_confirmed_ai",
                "user_confirmed": True,
                "user_confirmed_at": now_iso,
                "from_candidate_id": candidate_id,
            }
            errors_list.append(new_error)

        fm_dict["errors"] = errors_list
        # candidate 已 mutated by apply_status_change, candidates 引用未变
        fm_dict["error_candidates"] = candidates

        # 原子写回
        try:
            await asyncio.to_thread(_atomic_write_frontmatter, p, fm_dict, body)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Atomic write failed: {e}"
            )

        # Fire-and-forget Graphiti
        graphiti_status = "skipped"
        if fire_and_forget_graphiti:
            asyncio.create_task(
                write_error_to_graphiti(
                    classified,
                    node_id=node_id_for_dedupe,
                    session_id=session_id,
                    error_id=error_id,
                )
            )
            graphiti_status = "queued"
        else:
            ok = await write_error_to_graphiti(
                classified,
                node_id=node_id_for_dedupe,
                session_id=session_id,
                error_id=error_id,
            )
            graphiti_status = "ok" if ok else "failed"

        elapsed_ms = (_time.monotonic() - start) * 1000.0
        logger.info(
            "candidate_service.accepted",
            candidate_id=candidate_id,
            error_id=error_id,
            status=target_status,
            elapsed_ms=round(elapsed_ms, 2),
        )

        return AcceptCandidateResult(
            candidate_id=candidate_id,
            error_id=error_id,
            status=target_status,
            frontmatter_written=True,
            graphiti_status=graphiti_status,
            elapsed_ms=round(elapsed_ms, 2),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4 — dismiss / dispute candidate
# ═══════════════════════════════════════════════════════════════════════════════


async def dismiss_candidate(
    file_path: str | Path,
    candidate_id: str,
) -> DismissCandidateResult:
    """Story 2.5.X Task 4 + AC #7 — 用户标记 'AI 误判' (dismissed).

    candidate.status pending → dismissed. 不入 errors[]. 不写 Graphiti.
    保留 candidate 在 error_candidates[] 供未来训练 prompt.
    """
    return await _change_candidate_status_only(
        file_path, candidate_id, target_status="dismissed"
    )


async def dispute_candidate(
    file_path: str | Path,
    candidate_id: str,
    dispute_reason: str,
) -> DismissCandidateResult:
    """Story 2.5.X Task 4 + AC #7 — 用户提异议 (disputed) + 必填理由.

    candidate.status pending → disputed + dispute_reason 写入 candidate dict.
    不入 errors[]. 不写 Graphiti.
    """
    if not dispute_reason or not dispute_reason.strip():
        raise HTTPException(
            status_code=422, detail="dispute_reason is required for dispute"
        )

    return await _change_candidate_status_only(
        file_path,
        candidate_id,
        target_status="disputed",
        dispute_reason=dispute_reason,
    )


async def _change_candidate_status_only(
    file_path: str | Path,
    candidate_id: str,
    *,
    target_status: str,
    dispute_reason: Optional[str] = None,
) -> DismissCandidateResult:
    """共享路径 (dismiss/dispute) — 仅改 candidate.status, 不动 errors[]."""
    import time as _time

    start = _time.monotonic()
    p = Path(file_path)
    if not p.exists():
        raise HTTPException(
            status_code=404, detail=f"Node file not found: {file_path}"
        )

    lock = _get_file_lock(p)
    async with lock:
        try:
            fm_dict, body = await asyncio.to_thread(_read_frontmatter_dict, p)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read frontmatter: {e}"
            )

        candidates = fm_dict.get("error_candidates") or []
        if not isinstance(candidates, list):
            candidates = []

        idx, candidate = _find_candidate(candidates, candidate_id)
        if candidate is None:
            raise HTTPException(
                status_code=404, detail=f"Candidate {candidate_id} not found"
            )

        # 状态机 + auto-write timestamp/by
        apply_status_change(candidate, target_status, changed_by="user")

        if dispute_reason:
            candidate["dispute_reason"] = dispute_reason

        fm_dict["error_candidates"] = candidates

        try:
            await asyncio.to_thread(_atomic_write_frontmatter, p, fm_dict, body)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Atomic write failed: {e}"
            )

        elapsed_ms = (_time.monotonic() - start) * 1000.0
        logger.info(
            "candidate_service.status_changed",
            candidate_id=candidate_id,
            status=target_status,
            elapsed_ms=round(elapsed_ms, 2),
        )

        return DismissCandidateResult(
            candidate_id=candidate_id,
            status=target_status,
            dispute_reason=dispute_reason,
            frontmatter_written=True,
            elapsed_ms=round(elapsed_ms, 2),
        )
