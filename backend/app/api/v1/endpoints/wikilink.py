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

from app.config import get_settings
from app.services.wikilink_graph_service import get_wikilink_graph_service

logger = structlog.get_logger(__name__)

wikilink_router = APIRouter()


class BuildRequest(BaseModel):
    vault_path: Optional[str] = Field(
        None, description="Vault path override (defaults to CANVAS_BASE_PATH)"
    )


class RefreshRequest(BaseModel):
    changed_files: Optional[list[str]] = Field(
        None, description="Files changed (None = full rebuild)"
    )


@wikilink_router.post("/build")
async def build_graph(request: BuildRequest = BuildRequest()):
    """Trigger full wikilink graph construction (Story 1.2 AC #1)."""
    vault_path = request.vault_path or get_settings().CANVAS_BASE_PATH
    svc = get_wikilink_graph_service()
    result = await svc.build(vault_path)
    return {"data": result}


@wikilink_router.get("/neighbors/{note_path:path}")
async def get_neighbors(
    note_path: str,
    hop: int = Query(2, ge=1, le=5, description="N-hop depth"),
):
    """Query N-hop neighbors of a note (Story 1.2 AC #2, #3, #5)."""
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
async def graph_stats():
    """Graph statistics (node/edge counts, build state)."""
    svc = get_wikilink_graph_service()
    return {"data": svc.get_stats()}


@wikilink_router.post("/refresh")
async def refresh_graph(request: RefreshRequest = RefreshRequest()):
    """Hot update the graph (Story 1.2 AC #4)."""
    svc = get_wikilink_graph_service()
    if not svc.is_built:
        raise HTTPException(
            status_code=409,
            detail="Graph not built yet. Call POST /wikilink/build first.",
        )
    result = await svc.refresh(changed_files=request.changed_files)
    return {"data": result}
