"""Index management API — Story 1.9 AC #4, #5.

DELETE /api/v1/index/{vault_id} — delete all LanceDB tables for a vault
GET    /api/v1/index/stats      — per-vault table/row statistics
"""

from __future__ import annotations

from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException

logger = structlog.get_logger(__name__)

index_router = APIRouter()


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
