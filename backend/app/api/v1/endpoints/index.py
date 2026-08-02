"""Index management API — Story 1.9 AC #4, #5 + Round-23 Story 8.1.

DELETE /api/v1/index/{vault_id} — delete all LanceDB tables for a vault
GET    /api/v1/index/stats      — per-vault table/row statistics
POST   /api/v1/index/refresh-changed — Round-23 Story 8.1 incremental refresh

Wave-5 Stage B 续 follow-up (2026-05-13): DELETE endpoint 走 _vault_id_resolver
注入 ContextVar (与其他 15 个 vault-aware endpoint 统一). 与 stats / refresh-changed
不同, stats 是 vault-agnostic admin 视图, refresh-changed 用 vault_root 路径 (Round-23
Story 8.1 设计, 不在 Wave-5 Stage B 范围, 需独立 design review).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id

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


class PathRefreshStatus(BaseModel):
    """RAG-S1: per-path structured outcome — no aggregate fabrication."""

    path: str
    status: str  # accepted | coalesced | excluded | disabled


class RefreshChangedResponse(BaseModel):
    """RAG-S1 (2026-08-03): structured per-path status.

    旧契约 `scheduled=len(req.paths)` 是无条件假成功 (服务关闭 / 路径被黑名单
    排除 / debounce 互相取消, 三种情况全报 scheduled=N)——已废除。
    """

    accepted: int
    coalesced: int
    excluded: int
    results: List[PathRefreshStatus]
    orchestrator_enabled: bool


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
    """Delete all LanceDB tables for a specific vault (Story 1.9 AC #4).

    Wave-5 Stage B 续 follow-up (2026-05-13): 走 resolver 模式注入 ContextVar.
    drop_vault_tables(vault_id) 维持接 raw path param 保向后兼容(表名查找), 但
    resolver 调用让 downstream service (audit log / 多 vault 监控 / 未来 ContextVar
    依赖的逻辑) 看到正确 group_id, 与 wave-2 F2 LanceDBClient direct instantiation
    风险同源 — 不破坏当前行为, 但消除未来 silent 串库回归窗口.
    """
    # Wave-5 Stage B 续 follow-up — ContextVar 注入 (vault_id sanitize 由 resolver 内部做)
    derived_group_id = resolve_vault_group_id(vault_id)

    client = _get_lancedb_client()
    if client is None:
        raise HTTPException(status_code=503, detail="LanceDB client not available")

    dropped = client.drop_vault_tables(vault_id)
    if dropped == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No tables found for vault_id '{vault_id}'",
        )

    logger.info(
        "vault.index_deleted",
        vault_id=vault_id,
        group_id=derived_group_id,
        tables_dropped=dropped,
    )
    return {"vault_id": vault_id, "tables_dropped": dropped}


@index_router.post("/refresh-changed", response_model=RefreshChangedResponse)
async def refresh_changed_paths(req: RefreshChangedRequest) -> RefreshChangedResponse:
    """RAG-S1 (2026-08-03) — manual/plugin trigger into the index orchestrator.

    此前实现: schedule_note_index → _debounced_note_index 只刷 wikilink 图,
    一行 LanceDB 写入都没有, 且整 vault 单 coalesce key 让 N 个 path 互相
    cancel — 配合 scheduled=N 假成功构成彻底空转链 (ChatGPT 反证 #1/#2)。

    现实现: 每个 path 独立进 orchestrator durable pending (per-path, 绝不互相
    取消), worker 真正写 LanceDB。返回体逐 path 申报真实状态。

    Args:
        req: paths 必填 (1-500 vault 相对路径)。vault_root 参数保留兼容但
             orchestrator 恒用 settings.canvas_base_path (P0-3: vault 部署期固定)。
    """
    from app.services.vault_index_orchestrator import get_vault_index_orchestrator

    orch = get_vault_index_orchestrator()
    if orch is None:
        results = [PathRefreshStatus(path=p, status="disabled") for p in req.paths]
        logger.warning(
            "index.refresh_changed_disabled",
            path_count=len(req.paths),
        )
        return RefreshChangedResponse(
            accepted=0,
            coalesced=0,
            excluded=0,
            results=results,
            orchestrator_enabled=False,
        )

    results = []
    counts = {"accepted": 0, "coalesced": 0, "excluded": 0}
    for p in req.paths:
        # reset_backoff: an explicit API push is a real user event — clear
        # any M1 failure backoff so the file retries immediately.
        status_slug = orch.enqueue("upsert", p, reset_backoff=True)
        counts[status_slug] = counts.get(status_slug, 0) + 1
        results.append(PathRefreshStatus(path=p, status=status_slug))

    logger.info(
        "index.refresh_changed_enqueued",
        accepted=counts["accepted"],
        coalesced=counts["coalesced"],
        excluded=counts["excluded"],
    )

    return RefreshChangedResponse(
        accepted=counts["accepted"],
        coalesced=counts["coalesced"],
        excluded=counts["excluded"],
        results=results,
        orchestrator_enabled=True,
    )
