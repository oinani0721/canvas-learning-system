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
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id

logger = structlog.get_logger(__name__)

index_router = APIRouter()


class RefreshChangedRequest(BaseModel):
    """Round-23 Story 8.1 — incremental refresh request (手动/插件触发)."""

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
    status: str  # accepted | coalesced | excluded | disabled | persist_failed


class RefreshChangedResponse(BaseModel):
    """RAG-S1 (2026-08-03): structured per-path status.

    旧契约 `scheduled=len(req.paths)` 是无条件假成功 (服务关闭 / 路径被黑名单
    排除 / debounce 互相取消, 三种情况全报 scheduled=N)——已废除。

    CARD-G2-5 HIGH-3: durable journal 落盘失败的路径报 persist_failed；
    任一路径 persist_failed 时整个响应用 HTTP 503 + 完整 body 返回
    （durable=False），不再假报 200 成功。
    """

    accepted: int
    coalesced: int
    excluded: int
    results: List[PathRefreshStatus]
    orchestrator_enabled: bool
    persist_failed: int = 0
    durable: bool = True


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


@index_router.delete(
    "/{vault_id}",
    responses={
        207: {"description": "部分表删除失败 — 体内含 tables_failed 清单与已删数"},
        409: {"description": "为保护其它 vault 的数据整次拒绝删除 — 体内含 refusal_kind"},
        500: {"description": "名下每一张表都删除失败 — 体内含 tables_failed 清单"},
    },
)
async def delete_vault_index(vault_id: str):
    """Delete all LanceDB tables for a specific vault (Story 1.9 AC #4).

    Wave-5 Stage B 续 follow-up (2026-05-13): 走 resolver 模式注入 ContextVar.
    drop_vault_tables(vault_id) 维持接 raw path param 保向后兼容(表名查找), 但
    resolver 调用让 downstream service (audit log / 多 vault 监控 / 未来 ContextVar
    依赖的逻辑) 看到正确 group_id, 与 wave-2 F2 LanceDBClient direct instantiation
    风险同源 — 不破坏当前行为, 但消除未来 silent 串库回归窗口.

    CARD-LANCE-INDEX-DELETE-CONTRACT (BATCH-2026-09-18-第十五批) — 三合一 404 拆成五态:

    改前只看 ``drop_vault_tables`` 的 ``int``, 而 LanceDB 侧的**四道整次拒绝闸**全部返回
    0、"名下没有表"是 0、CARD-G2-9-F2 之后"每一张都删失败"也是 0 —— 三件性质完全不同的
    事共用同一个 ``404 No tables found``。部分失败更回 ``200`` 且不带失败清单, 调用方据此
    认为索引已清, 实际还留着几张。

    现在按 ``DropVaultReport.outcome`` 映射:

    ===========  =====  ====================================================
    outcome      HTTP   体
    ===========  =====  ====================================================
    no_tables    404    文案与改前**逐字**相同 (唯一保留 404 的分支)
    refused      409    ``{vault_id, refusal_kind, ambiguous_tables}``
    all_failed   500    ``{vault_id, tables_failed:[{table, error_type}]}``
    partial      207    ``{vault_id, tables_dropped, tables_failed, partial}``
    dropped      200    体与改前**逐字**相同
    ===========  =====  ====================================================

    ⛔ **脱敏**: 体里只许出现表名、``refusal_kind``、``error_type``。完整 refusal 文案
    (闸② 里嵌着 ``{e}``) 与异常 message 常带 LanceDB 库的**绝对路径**, 只进服务端日志。
    """
    # Wave-5 Stage B 续 follow-up — ContextVar 注入 (vault_id sanitize 由 resolver 内部做)
    derived_group_id = resolve_vault_group_id(vault_id)

    client = _get_lancedb_client()
    if client is None:
        raise HTTPException(status_code=503, detail="LanceDB client not available")

    report = client.drop_vault_tables_report(vault_id)
    outcome = report.outcome
    # 只上类型名, 不上 message —— message 里有库路径
    failed = [{"table": name, "error_type": kind} for name, kind in report.failures]

    if outcome == "refused":
        # 完整文案只落日志; 调用方拿 refusal_kind + 判不出主人的表名清单即可定位
        logger.error(
            "vault.index_delete_refused",
            vault_id=vault_id,
            group_id=derived_group_id,
            refusal_kind=report.refusal_kind,
            refusal=report.refusal,
            ambiguous_tables=list(report.ambiguous),
        )
        raise HTTPException(
            status_code=409,
            detail={
                "vault_id": vault_id,
                "refusal_kind": report.refusal_kind,
                "ambiguous_tables": list(report.ambiguous),
            },
        )

    if outcome == "no_tables":
        raise HTTPException(
            status_code=404,
            detail=f"No tables found for vault_id '{vault_id}'",
        )

    if outcome == "all_failed":
        logger.error(
            "vault.index_delete_all_failed",
            vault_id=vault_id,
            group_id=derived_group_id,
            tables_failed=[name for name, _ in report.failures],
        )
        raise HTTPException(
            status_code=500,
            detail={"vault_id": vault_id, "tables_failed": failed},
        )

    if outcome == "partial":
        logger.warning(
            "vault.index_delete_partial",
            vault_id=vault_id,
            group_id=derived_group_id,
            tables_dropped=len(report.dropped),
            tables_failed=[name for name, _ in report.failures],
        )
        # 与 edges.py / refresh-changed 的半成功语义同族: 非 2xx 会让调用方以为
        # 什么都没发生, 而这里**确实**删掉了一部分, 必须连清单一起回。
        # FastAPI 允许路由函数直接返回 Response 子类。⚠️ 这里**不需要**
        # refresh_changed_paths 末尾那条 reportReturnType 抑制注释: 本函数没有返回注解,
        # 加了反而会被 pyright 记成 reportUnnecessaryTypeIgnoreComment。
        # ⛔ 也不要在注释里写出那条指令的字面形态 —— pyright 会把它当成真指令解析
        # (本卡实测: 只是"提到"它, 警告数就从 80 涨到 81)。
        return JSONResponse(
            status_code=207,
            content={
                "vault_id": vault_id,
                "tables_dropped": len(report.dropped),
                "tables_failed": failed,
                "partial": True,
            },
        )

    logger.info(
        "vault.index_deleted",
        vault_id=vault_id,
        group_id=derived_group_id,
        tables_dropped=len(report.dropped),
    )
    return {"vault_id": vault_id, "tables_dropped": len(report.dropped)}


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
    counts = {"accepted": 0, "coalesced": 0, "excluded": 0, "persist_failed": 0}
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
        persist_failed=counts["persist_failed"],
    )

    resp = RefreshChangedResponse(
        accepted=counts["accepted"],
        coalesced=counts["coalesced"],
        excluded=counts["excluded"],
        results=results,
        orchestrator_enabled=True,
        persist_failed=counts["persist_failed"],
        durable=counts["persist_failed"] == 0,
    )
    # CARD-G2-5 HIGH-3: 任一路径 durable 落盘失败 → 503 + 完整 body
    # （默认裁决: 全仓无活消费方; 消费方按 resp.model_dump() 拿到逐 path 状态）。
    if counts["persist_failed"]:
        # FastAPI 允许路由函数直接返回 Response 子类; 改注解会改 openapi 生成面。
        return JSONResponse(status_code=503, content=resp.model_dump())  # pyright: ignore[reportReturnType]
    return resp
