"""Index management API — Story 1.9 AC #4, #5 + Round-23 Story 8.1.

DELETE /api/v1/index/{vault_id} — delete all LanceDB tables for a vault
GET    /api/v1/index/stats      — per-vault table/row statistics
POST   /api/v1/index/refresh-changed — Round-23 Story 8.1 incremental refresh
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

index_router = APIRouter()


class RefreshChangedRequest(BaseModel):
    """Round-23 Story 8.1 — incremental refresh request from Tauri plugin."""

    paths: List[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="vault 相对路径列表 (如 ['节点/A.md', '节点/B.md'])",
    )
    vault_root: Optional[str] = Field(
        default=None,
        description="可选 vault 绝对路径 (默认从 settings.canvas_base_path 读取)",
    )


class RefreshChangedResponse(BaseModel):
    """Round-23 Story 8.1 — 返回已 schedule 的 paths."""

    scheduled: int
    debounce_ms: int
    paths: List[str]


def _get_lancedb_client():
    """Lazy import to avoid circular deps at module load time."""
    from app.services.lancedb_index_service import get_lancedb_index_service

    svc = get_lancedb_index_service()
    if svc is None:
        return None
    return svc._get_or_init_client()


@index_router.get("/stats", response_model=Dict[str, Any])
async def get_index_stats():
    """Per-vault LanceDB table and row statistics (Story 1.9 AC #5)."""
    client = _get_lancedb_client()
    if client is None:
        return {}
    return client.get_all_vault_stats()


@index_router.delete("/{vault_id}")
async def delete_vault_index(vault_id: str):
    """Delete all LanceDB tables for a specific vault (Story 1.9 AC #4)."""
    client = _get_lancedb_client()
    if client is None:
        raise HTTPException(status_code=503, detail="LanceDB client not available")

    dropped = client.drop_vault_tables(vault_id)
    if dropped == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No tables found for vault_id '{vault_id}'",
        )

    logger.info("vault.index_deleted", vault_id=vault_id, tables_dropped=dropped)
    return {"vault_id": vault_id, "tables_dropped": dropped}


@index_router.post("/refresh-changed", response_model=RefreshChangedResponse)
async def refresh_changed_paths(req: RefreshChangedRequest) -> RefreshChangedResponse:
    """Round-23 Story 8.1 — Incremental refresh after Tauri plugin file-save.

    Tauri Obsidian plugin 在 vault 文件保存时调本 endpoint, 推送已变更路径列表.
    Backend 使用 LanceDBIndexService.schedule_note_index() debounce 合并多条改动,
    最终触发 wikilink graph rebuild + (后续 Story) lancedb chunk re-index.

    Args:
        req: paths 必填 (1-500 路径), vault_root 可选 (默认 settings.canvas_base_path).

    Returns:
        RefreshChangedResponse — scheduled 数量 + debounce_ms + 接收到的 paths.

    Errors:
        404: vault_root 不可解析.
        503: LanceDB index service unavailable.
    """
    from app.config import settings
    from app.services.lancedb_index_service import get_lancedb_index_service

    vault_root = req.vault_root or getattr(settings, "canvas_base_path", None)
    if not vault_root:
        raise HTTPException(
            status_code=404,
            detail="vault_root not provided and canvas_base_path not configured",
        )

    svc = get_lancedb_index_service()
    if svc is None:
        raise HTTPException(
            status_code=503,
            detail="LanceDB index service disabled (ENABLE_LANCEDB_AUTO_INDEX=False)",
        )

    coalesce_key = f"vault:{vault_root}"
    for p in req.paths:
        svc.schedule_note_index(
            note_path=p, vault_root=vault_root, coalesce_key=coalesce_key
        )

    debounce_ms = int(svc._debounce_seconds * 1000)
    logger.info(
        "index.refresh_changed_scheduled",
        vault_root=vault_root,
        path_count=len(req.paths),
        debounce_ms=debounce_ms,
    )

    return RefreshChangedResponse(
        scheduled=len(req.paths), debounce_ms=debounce_ms, paths=req.paths
    )
