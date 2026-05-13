"""Story 2.5.X Task 3+4 — Errors candidate management endpoints.

POST /api/v1/errors/accept-candidate — AC #5: candidate → errors[] + Graphiti
POST /api/v1/errors/dismiss-candidate — AC #7: candidate → status=dismissed
POST /api/v1/errors/dispute-candidate — AC #7: candidate → status=disputed + reason

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import DEFAULT_GROUP_ID
from app.mcp.tools.error_tools import _resolve_node_file_path
from app.services.candidate_service import (
    AcceptCandidateResult,
    CandidateEdits,
    DismissCandidateResult,
    accept_candidate,
    dismiss_candidate,
    dispute_candidate,
)
from app.services.error_reader import (
    query_errors_by_canvas,
    query_errors_by_type,
    read_errors_from_node,
)
from app.services.error_rebuild_service import (
    RebuildStats,
    rebuild_graphiti_from_frontmatter,
)

logger = structlog.get_logger(__name__)

errors_router = APIRouter()


# Wave-5 Stage B (2026-05-12) — Multi-vault ContextVar 注入辅助.
# 4 errors 端点此前无 vault_id 隔离 → 跨 vault 错误记录泄漏 (P0).
def _resolve_vault_group_id(
    vault_id: Optional[str],
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
    legacy_group_id: Optional[str] = None,
) -> str:
    """Wave-5 Stage B — vault_id → ContextVar 注入 + 派生 group_id."""
    from app.config import sanitize_vault_id
    from app.core.subject_config import (
        build_vault_group_id,
        canonical_group_id,
        set_current_subject_id,
    )

    if vault_id and vault_id.strip():
        sanitized = sanitize_vault_id(vault_id)
        derived = build_vault_group_id(
            sanitized,
            subject_id=subject_id,
            canvas_path=canvas_path,
        )
    elif legacy_group_id and legacy_group_id.strip():
        logger.warning(
            "Wave-5 Stage B: errors endpoint vault_id missing, "
            "falling back to deprecated group_id=%s",
            legacy_group_id,
        )
        derived = canonical_group_id(legacy_group_id)
    else:
        logger.warning(
            "Wave-5 Stage B: errors endpoint both vault_id and group_id missing, "
            "falling back to DEFAULT_GROUP_ID"
        )
        derived = DEFAULT_GROUP_ID

    set_current_subject_id(derived)
    return derived


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
    # Wave-5 Stage B (2026-05-12) — Multi-vault P0-2.
    # 用户错误记录 / Graphiti misconception 必须 vault 隔离,
    # 否则 5 vault 并存 时跨 vault Misconception 串库.
    vault_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Multi-vault 隔离必填. Plugin 端 inferVaultId(app.vault.getName()) 取. "
            "Backend 用 sanitize_vault_id 标准化 → build_vault_group_id → "
            "set_current_subject_id 注入 ContextVar, "
            "让 candidate_service / error_reader 等 downstream 都看到同一 vault."
        ),
        examples=["cs_61b", "数学"],
    )
    subject_id: Optional[str] = Field(
        default=None,
        description="可选 vault 内学科二级 namespace.",
    )


class DismissCandidateRequest(BaseModel):
    """AC #7 — dismiss candidate (AI 误判)."""

    candidate_id: str = Field(..., description="error_candidates[].id")
    node_id: str = Field(..., description="vault-relative node path")
    vault_id: str = Field(
        ...,
        min_length=1,
        description="Multi-vault P0-2 — 必填. 注入 ContextVar 防跨 vault 泄漏.",
        examples=["cs_61b"],
    )
    subject_id: Optional[str] = Field(default=None)


class DisputeCandidateRequest(BaseModel):
    """AC #7 — dispute candidate (我有异议)."""

    candidate_id: str = Field(..., description="error_candidates[].id")
    node_id: str = Field(..., description="vault-relative node path")
    dispute_reason: str = Field(
        ..., min_length=1, description="用户简短说明为何认为 AI 判断错"
    )
    vault_id: str = Field(
        ...,
        min_length=1,
        description="Multi-vault P0-2 — 必填.",
        examples=["cs_61b"],
    )
    subject_id: Optional[str] = Field(default=None)


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
    # Wave-5 Stage B (2026-05-12) — 注入 ContextVar 防跨 vault Misconception 串库.
    _resolve_vault_group_id(
        req.vault_id,
        subject_id=req.subject_id,
        canvas_path=req.node_id,
    )

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
    _resolve_vault_group_id(
        req.vault_id, subject_id=req.subject_id, canvas_path=req.node_id
    )

    file_path = _resolve_node_file_path(req.node_id)
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"Cannot resolve vault file path for node_id: {req.node_id}",
        )

    return await dismiss_candidate(file_path=file_path, candidate_id=req.candidate_id)


@errors_router.post("/dispute-candidate", response_model=DismissCandidateResult)
async def dispute_candidate_endpoint(
    req: DisputeCandidateRequest,
) -> DismissCandidateResult:
    """Story 2.5.X AC #7 — 用户提异议 (disputed) + 必填理由.

    candidate.status pending → disputed + dispute_reason 写入.
    不入 errors[]. 不写 Graphiti.
    """
    _resolve_vault_group_id(
        req.vault_id, subject_id=req.subject_id, canvas_path=req.node_id
    )

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


@errors_router.post("/rebuild-graphiti", response_model=RebuildStats)
async def rebuild_graphiti_endpoint(
    group_id: str,
    dry_run: bool = False,
) -> RebuildStats:
    """Story 2.5.X AC #6 — 从 frontmatter errors[] 重建 Graphiti 知识图谱.

    用户场景:
    - 切设备 / 重建索引 (Graphiti 数据丢失但 markdown 保留)
    - 验证 frontmatter 与 Graphiti 一致性

    使用建议: 先 dry_run=True 看会写多少, 再 dry_run=False 实际跑.

    Args:
        group_id: Graphiti namespace (如 "vault:cs_61b" or "cs_61b:main"). Story 2.5.Y 后改为强制从 vault config 推断.
        dry_run: True 仅扫描计数 (不调 Graphiti), False 实际写入.

    Returns:
        RebuildStats — total_files_scanned / total_errors_scanned / newly_written / failed + failures details

    Errors:
        404: vault root 不可解析
        500: 致命错误 (单条失败不影响, 写入 failures[] 数组)
    """
    from app.config import settings

    vault_root_str = getattr(settings, "canvas_base_path", None)
    if not vault_root_str:
        raise HTTPException(
            status_code=404,
            detail="vault root (canvas_base_path) not configured",
        )

    return await rebuild_graphiti_from_frontmatter(
        vault_root=vault_root_str,
        group_id=group_id,
        dry_run=dry_run,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Round-23 Story 7.4 · Patch 4 — Error reading endpoints (Round-14 残缺 #1)
# [Source: _bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md]
# ═══════════════════════════════════════════════════════════════════════════════


class NodeErrorsResponse(BaseModel):
    """GET /by-node/{node_id} 响应."""

    node_id: str
    node_path: Optional[str] = None
    errors: list[dict] = Field(default_factory=list)
    count: int = 0


class TypeErrorsResponse(BaseModel):
    """GET /by-type/{misconception_type} 响应."""

    misconception_type: str
    errors: list[dict] = Field(default_factory=list)
    count: int = 0
    only_uncorrected: bool = True


@errors_router.get("/by-node/{node_id:path}", response_model=NodeErrorsResponse)
async def get_errors_by_node(node_id: str) -> NodeErrorsResponse:
    """读单节点 frontmatter errors[] (Round-23 Story 7.4).

    Args:
        node_id: vault 相对节点路径 (如 'admissibility' 或 '节点/heuristic.md').

    Returns:
        NodeErrorsResponse — 节点的全部错误记录.

    Errors:
        404: 节点路径无法解析或文件不存在.
    """
    file_path = _resolve_node_file_path(node_id)
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"Node file not found or path unsafe: {node_id}",
        )

    errors = await read_errors_from_node(file_path)
    return NodeErrorsResponse(
        node_id=node_id,
        node_path=file_path,
        errors=errors,
        count=len(errors),
    )


@errors_router.get("/by-type/{misconception_type}", response_model=TypeErrorsResponse)
async def get_errors_by_type(
    misconception_type: str,
    only_uncorrected: bool = Query(default=True, description="True 仅未纠正错误"),
    match_legacy_type: bool = Query(
        default=True, description="True 同时匹配 legacy_type"
    ),
    limit: int = Query(default=50, ge=1, le=500, description="结果上限"),
) -> TypeErrorsResponse:
    """按 misconception 类型查 vault 内全部历史错误 (Round-23 Story 7.4 核心需求).

    实现 ChatGPT Stage 1 Task 4 "按 misconception 类型查历史" — 修复 Round-14 残缺 #1.

    用户场景: 学到一个 misconception 后想看自己历史犯过的同类错误, 帮助巩固.

    Args:
        misconception_type: 类型字符串 (如 'conceptual_confusion' / 'knowledge_gap').
        only_uncorrected: True 仅活跃错误, False 含历史已纠正错误.
        match_legacy_type: True 同时匹配旧格式 legacy_type 字段.
        limit: 结果上限 (1-500).

    Returns:
        TypeErrorsResponse — 按 last_seen_at 降序排列.

    Errors:
        404: vault root 不可解析.
    """
    from app.config import settings

    vault_root_str = getattr(settings, "canvas_base_path", None)
    if not vault_root_str:
        raise HTTPException(
            status_code=404,
            detail="vault root (canvas_base_path) not configured",
        )

    errors = await query_errors_by_type(
        vault_path=vault_root_str,
        misconception_type=misconception_type,
        only_uncorrected=only_uncorrected,
        match_legacy_type=match_legacy_type,
        limit=limit,
    )
    return TypeErrorsResponse(
        misconception_type=misconception_type,
        errors=errors,
        count=len(errors),
        only_uncorrected=only_uncorrected,
    )


@errors_router.get("/list", response_model=TypeErrorsResponse)
async def list_errors(
    canvas_path: Optional[str] = Query(
        default=None, description="可选 canvas/board 过滤"
    ),
    only_uncorrected: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=500),
) -> TypeErrorsResponse:
    """列 vault (或某 canvas) 内全部错误 (Round-23 Story 7.4).

    Args:
        canvas_path: 可选 canvas/board 名 (frontmatter `canvas` 字段过滤).
        only_uncorrected: True 仅未纠正错误.
        limit: 结果上限.

    Returns:
        TypeErrorsResponse (misconception_type 为 'all').

    Errors:
        404: vault root 不可解析.
    """
    from app.config import settings

    vault_root_str = getattr(settings, "canvas_base_path", None)
    if not vault_root_str:
        raise HTTPException(
            status_code=404,
            detail="vault root (canvas_base_path) not configured",
        )

    errors = await query_errors_by_canvas(
        vault_path=vault_root_str,
        canvas_path=canvas_path,
        only_uncorrected=only_uncorrected,
        limit=limit,
    )
    return TypeErrorsResponse(
        misconception_type="all" if not canvas_path else f"canvas:{canvas_path}",
        errors=errors,
        count=len(errors),
        only_uncorrected=only_uncorrected,
    )
