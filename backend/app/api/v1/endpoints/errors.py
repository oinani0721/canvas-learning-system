"""Story 2.5.X Task 3+4 — Errors candidate management endpoints.

POST /api/v1/errors/accept-candidate — AC #5: candidate → errors[] + Graphiti
POST /api/v1/errors/dismiss-candidate — AC #7: candidate → status=dismissed
POST /api/v1/errors/dispute-candidate — AC #7: candidate → status=disputed + reason

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.mcp.tools.error_tools import _resolve_node_file_path
from app.services.candidate_service import (
    AcceptCandidateResult,
    CandidateEdits,
    DismissCandidateResult,
    accept_candidate,
    dismiss_candidate,
    dispute_candidate,
)

logger = structlog.get_logger(__name__)

errors_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request models
# ═══════════════════════════════════════════════════════════════════════════════


class AcceptCandidateRequest(BaseModel):
    """AC #5 — accept candidate request."""

    candidate_id: str = Field(..., description="error_candidates[].id 要 accept 的那条")
    node_id: str = Field(..., description="vault-relative node path (如 '节点/X.md')")
    user_edits: Optional[CandidateEdits] = Field(
        default=None,
        description="可选编辑 (覆盖 description/pedagogy_type/legacy_type), 提供则 status=edited 否则 accepted",
    )
    session_id: str = Field(default="", description="对话 session ID")
    fire_and_forget_graphiti: bool = Field(
        default=True, description="True 默认 → 后台 task; False 同步等待 Graphiti"
    )


class DismissCandidateRequest(BaseModel):
    """AC #7 — dismiss candidate (AI 误判)."""

    candidate_id: str = Field(..., description="error_candidates[].id")
    node_id: str = Field(..., description="vault-relative node path")


class DisputeCandidateRequest(BaseModel):
    """AC #7 — dispute candidate (我有异议)."""

    candidate_id: str = Field(..., description="error_candidates[].id")
    node_id: str = Field(..., description="vault-relative node path")
    dispute_reason: str = Field(
        ..., min_length=1, description="用户简短说明为何认为 AI 判断错"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@errors_router.post("/accept-candidate", response_model=AcceptCandidateResult)
async def accept_candidate_endpoint(
    req: AcceptCandidateRequest,
) -> AcceptCandidateResult:
    """Story 2.5.X AC #5 — 用户接受 candidate, 移入 errors[] + Graphiti.

    若 user_edits 非空 → status=edited, 否则 status=accepted.
    复用 candidate_id 作为 error_id 保证 frontmatter 一致.

    Errors:
        404: candidate / node 不存在
        422: candidate 状态非 pending (反向/终态间不可逆) OR ClassifiedError 构造失败
        500: file 读写失败
    """
    file_path = _resolve_node_file_path(req.node_id)
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"Cannot resolve vault file path for node_id: {req.node_id}",
        )

    return await accept_candidate(
        file_path=file_path,
        candidate_id=req.candidate_id,
        user_edits=req.user_edits,
        session_id=req.session_id,
        fire_and_forget_graphiti=req.fire_and_forget_graphiti,
    )


@errors_router.post("/dismiss-candidate", response_model=DismissCandidateResult)
async def dismiss_candidate_endpoint(
    req: DismissCandidateRequest,
) -> DismissCandidateResult:
    """Story 2.5.X AC #7 — 用户标记 AI 误判 (dismissed).

    candidate.status pending → dismissed. 不入 errors[]. 不写 Graphiti.
    保留 candidate 供训练 prompt 改进.
    """
    file_path = _resolve_node_file_path(req.node_id)
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"Cannot resolve vault file path for node_id: {req.node_id}",
        )

    return await dismiss_candidate(
        file_path=file_path, candidate_id=req.candidate_id
    )


@errors_router.post("/dispute-candidate", response_model=DismissCandidateResult)
async def dispute_candidate_endpoint(
    req: DisputeCandidateRequest,
) -> DismissCandidateResult:
    """Story 2.5.X AC #7 — 用户提异议 (disputed) + 必填理由.

    candidate.status pending → disputed + dispute_reason 写入.
    不入 errors[]. 不写 Graphiti.
    """
    file_path = _resolve_node_file_path(req.node_id)
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"Cannot resolve vault file path for node_id: {req.node_id}",
        )

    return await dispute_candidate(
        file_path=file_path,
        candidate_id=req.candidate_id,
        dispute_reason=req.dispute_reason,
    )
