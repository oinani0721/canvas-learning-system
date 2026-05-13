"""Wikilink graph API — Story 1.2.

POST /api/v1/wikilink/build          — trigger full graph build
GET  /api/v1/wikilink/neighbors/{path} — N-hop neighbor query
GET  /api/v1/wikilink/stats          — graph statistics
POST /api/v1/wikilink/refresh        — hot update graph
"""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id
from app.config import get_settings
from app.services.wikilink_graph_service import get_wikilink_graph_service

logger = structlog.get_logger(__name__)

wikilink_router = APIRouter()


class BuildRequest(BaseModel):
    vault_path: Optional[str] = Field(
        None, description="Vault path override (defaults to CANVAS_BASE_PATH)"
    )
    # Wave-5 Stage B 续 — vault_id 注入 ContextVar 防多 vault 串库
    vault_id: Optional[str] = Field(
        default=None,
        min_length=1,
        description=(
            "Wave-5 Stage B (Multi-vault P0) — 推荐必填. Plugin inferVaultId. "
            "Wikilink 图是 per-vault state. 空时 fallback deprecated group_id."
        ),
    )
    subject_id: Optional[str] = Field(
        default=None, description="可选 vault 内学科二级 namespace."
    )
    group_id: Optional[str] = Field(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id.",
    )


class RefreshRequest(BaseModel):
    changed_files: Optional[list[str]] = Field(
        None, description="Files changed (None = full rebuild)"
    )
    vault_id: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Wave-5 Stage B — 推荐必填 Plugin inferVaultId.",
    )
    subject_id: Optional[str] = Field(
        default=None, description="可选 vault 内学科二级 namespace."
    )
    group_id: Optional[str] = Field(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id.",
    )


@wikilink_router.post("/build")
async def build_graph(request: BuildRequest = BuildRequest()):
    """Trigger full wikilink graph construction (Story 1.2 AC #1)."""
    resolve_vault_group_id(
        request.vault_id,
        subject_id=request.subject_id,
        legacy_group_id=request.group_id,
    )
    vault_path = request.vault_path or get_settings().CANVAS_BASE_PATH
    svc = get_wikilink_graph_service()
    result = await svc.build(vault_path)
    return {"data": result}


@wikilink_router.get("/neighbors/{note_path:path}")
async def get_neighbors(
    note_path: str,
    hop: int = Query(2, ge=1, le=5, description="N-hop depth"),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description=(
            "Wave-5 Stage B (Multi-vault P0) — 推荐必填. Plugin inferVaultId. "
            "Wikilink 邻居图 per-vault."
        ),
    ),
    subject_id: Optional[str] = Query(
        default=None, description="可选 vault 内学科二级 namespace."
    ),
    group_id: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id.",
    ),
):
    """Query N-hop neighbors of a note (Story 1.2 AC #2, #3, #5)."""
    resolve_vault_group_id(vault_id, subject_id=subject_id, legacy_group_id=group_id)
    svc = get_wikilink_graph_service()
    if not svc.is_built:
        raise HTTPException(
            status_code=409,
            detail="Graph not built yet. Call POST /wikilink/build first.",
        )
    neighbors = svc.get_neighbors(note_path, hop=hop)
    return {
        "data": {
            "note_path": note_path,
            "hop": hop,
            "count": len(neighbors),
            "neighbors": [
                {
                    "title": n.title,
                    "path": n.path,
                    "hop_distance": n.hop_distance,
                    "frontmatter": n.frontmatter,
                }
                for n in neighbors
            ],
        }
    }


@wikilink_router.get("/stats")
async def graph_stats(
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Wave-5 Stage B — 推荐必填. Stats per-vault.",
    ),
    subject_id: Optional[str] = Query(
        default=None, description="可选 vault 内学科二级 namespace."
    ),
    group_id: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id.",
    ),
):
    """Graph statistics (node/edge counts, build state)."""
    resolve_vault_group_id(vault_id, subject_id=subject_id, legacy_group_id=group_id)
    svc = get_wikilink_graph_service()
    return {"data": svc.get_stats()}


@wikilink_router.post("/refresh")
async def refresh_graph(request: RefreshRequest = RefreshRequest()):
    """Hot update the graph (Story 1.2 AC #4)."""
    resolve_vault_group_id(
        request.vault_id,
        subject_id=request.subject_id,
        legacy_group_id=request.group_id,
    )
    svc = get_wikilink_graph_service()
    if not svc.is_built:
        raise HTTPException(
            status_code=409,
            detail="Graph not built yet. Call POST /wikilink/build first.",
        )
    result = await svc.refresh(changed_files=request.changed_files)
    return {"data": result}
