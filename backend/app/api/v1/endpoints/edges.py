# Canvas Learning System - Edge Rationale API Endpoints
# Story 4.2: Edge Dialog — Agent Follow-up & Rationale Recording (AC-6)
# Story 4.3: EI+SE Dual Strategy (AC-6 strategy data)
# Story 4.4: Edge Dialog Fallback (AC-3, AC-4 partial failure handling)
"""
Edge rationale recording endpoint.

Exposes record_edge_rationale as a FastAPI endpoint (MCP tool target).
Performs dual-write to Neo4j (structured KG-triplet) and LanceDB (vector).
Supports partial failure semantics (207 Multi-Status).

[Source: _bmad-output/implementation-artifacts/4-2-edge-dialog-agent-reasoning.md#Task 2]
[Source: _bmad-output/implementation-artifacts/4-4-edge-dialog-fallback.md#Task 6]
"""

import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

# CARD-T-EDGES: 判定「对端写失败」用. ⛔ 必须是**模块级** import ——
# except 子句是发生异常时才求值的, 名字未绑定会先抛 NameError 把处理器自己炸掉
# (memory_service.py:44-50 记的就是这起事故)。同包先例: sync.py:16。
from neo4j.exceptions import DatabaseError, ServiceUnavailable, SessionExpired, TransientError
from tenacity import RetryError

from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id

# T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式 (graphiti_core validator 拒冒号)
from app.graphiti.group_id_compat import to_physical_group_id
from app.models.edge_rationale import (
    EdgeRationaleCreate,
    EdgeRationaleResponse,
    WriteStatus,
)

logger = logging.getLogger(__name__)

#: `_write_neo4j_triplet` 判定为「**对端**写失败」的类型集 —— 命中即记
#: `WriteStatus(success=False)`, 由 handler 按 Story 4.4 AC-4 判半成功 207,
#: 保住 LanceDB 侧那一半; 未命中的一律原样上抛成 500。
#:
#: ⛔ **刻意不收 `Neo4jError` / `ClientError` 族**(第十四批 T5-B 对抗复核裁定)。
#: `ClientError` 的语义是「**你发来的请求不对**」: `ParameterMissing`(params 少一个键)、
#: `CypherSyntaxError`(Cypher 写错)、`AuthError`/`Forbidden`(凭据或权限没配对)、
#: `ConstraintError`。这些全是**本进程 / 本部署的缺陷**, 收进 207 的后果是:
#: 每个请求都返 207 → 5xx 率恒 0 → 看板全绿 → 前端 Outbox 把 207 当「部分成功已保留」
#: 继续投递 → 全部 edge rationale 的 Neo4j 半边永久丢失且无人察觉。
#: 同理不收 `ConnectionPoolError`(连接池耗尽 = 我方 session 泄漏)、
#: `ResultError`/`SessionError`/`TransactionError` 族(驱动 API 误用)、
#: `ConfigurationError` 族(部署配置坏了) —— 它们都该响亮地 500。
#:
#: 收进来的这四类**只描述对端状态**, 与我方请求内容无关:
#: ServiceUnavailable/SessionExpired(连不上或会话失效)、TransientError(对端让重试)、
#: DatabaseError(对端内部错)。加上 tenacity `RetryError`(重试耗尽, 在已 fallback 态
#: 由 neo4j_client 裸 raise)与原有四类内建异常。
#:
#: ⚠️ 已知未覆盖(如实记, 已登记移交): `neo4j._exceptions.BoltError` 族与 packstream
#: 解码层的裸 `ValueError`/`struct.error` —— 握手完成后收到畸形 Bolt 帧时会逃出本元组
#: 而 500。驱动自己的连接池写的是 `except (Neo4jError, DriverError, BoltError)`,
#: 但 `BoltError` 在私有模块 `neo4j._exceptions` 里, 本卡不引私有 API。
_NEO4J_WRITE_FAILURES: tuple[type[Exception], ...] = (
    RuntimeError,  # neo4j_client.py:595-596 "Neo4j driver not initialized"
    ConnectionError,  # ⊂ OSError, 保留为可读性
    asyncio.TimeoutError,  # 实测 is TimeoutError 且 ⊂ OSError, 同上
    OSError,  # JSON fallback 侧的文件 IO
    AttributeError,  # 客户端缺方法(本卡原缺陷 execute_query 的那一类)
    ServiceUnavailable,  # 对端不可达
    SessionExpired,  # 对端会话失效
    TransientError,  # 对端让重试
    DatabaseError,  # 对端内部错误
    RetryError,  # tenacity 重试耗尽(已 fallback 态下裸 raise)
)

edges_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Neo4j Write — Structured KG-Triplet
# ═══════════════════════════════════════════════════════════════════════════════


async def _write_neo4j_triplet(
    rationale: EdgeRationaleCreate,
    record_id: str,
    resolved_group_id: str,
) -> WriteStatus:
    """
    Write edge rationale to Neo4j as structured KG-triplet.

    Story 4.2 AC-3: Uses Agent self-report channel.
    Writes via Neo4j client directly as an :EdgeRationale node,
    following the existing Neo4j direct-write pattern.

    Story 4.2 AC-5: Time-series aware — new rationale creates new node,
    does not overwrite old (append-only for version history).

    Wave-5 Stage B 续: resolved_group_id 由 endpoint 顶部 resolve_vault_group_id 派生,
    确保 Neo4j 写入用 per-vault group_id 防多 vault 串库.
    """
    from app.clients.neo4j_client import get_neo4j_client

    neo4j = get_neo4j_client()
    if neo4j is None:
        return WriteStatus(
            success=False,
            error="Neo4j client not available",
        )

    # Build structured episode body
    episode_body = (
        f"Edge rationale: "
        f"{rationale.source_concept} --[{rationale.relation_type}]--> "
        f"{rationale.target_concept}. "
        f"Rationale: {rationale.rationale_text} "
        f"(confidence: {rationale.confidence:.2f}, "
        f"strategies: {','.join(rationale.strategies_applied)}, "
        f"depth: {rationale.explanation_depth_score}/5, "
        f"rounds: {rationale.questioning_rounds})"
    )

    # Write as :EdgeRationale node in Neo4j (time-series append-only)
    query = """
        CREATE (er:EdgeRationale {
            record_id: $record_id,
            edge_id: $edge_id,
            source_node_id: $source_node_id,
            target_node_id: $target_node_id,
            source_concept: $source_concept,
            target_concept: $target_concept,
            relation_type: $relation_type,
            rationale_text: $rationale_text,
            confidence: $confidence,
            strategies_applied: $strategies_applied,
            questioning_rounds: $questioning_rounds,
            explanation_depth_score: $explanation_depth_score,
            episode_body: $episode_body,
            group_id: $group_id,
            created_at: datetime()
        })
        RETURN er.record_id AS record_id
        """

    # CARD-T-EDGES (第十四批): 已改调 run_query(**params) —— Neo4jClient 上只有
    # run_query(query, **params)(neo4j_client.py:536), 从来没有 execute_query,
    # 旧写法每次调用都抛 AttributeError。run_query 收的是 **params 而非位置 dict,
    # 故参数同步展开(键名逐字不变)。
    params = {
        "record_id": record_id,
        "edge_id": rationale.edge_id,
        "source_node_id": rationale.source_node_id,
        "target_node_id": rationale.target_node_id,
        "source_concept": rationale.source_concept,
        "target_concept": rationale.target_concept,
        "relation_type": rationale.relation_type,
        "rationale_text": rationale.rationale_text,
        "confidence": rationale.confidence,
        "strategies_applied": rationale.strategies_applied,
        "questioning_rounds": rationale.questioning_rounds,
        "explanation_depth_score": rationale.explanation_depth_score,
        "episode_body": episode_body,
        # T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式
        "group_id": to_physical_group_id(resolved_group_id),
    }

    # ⛔ try 只包住**对端调用这一行**(第十四批 T5-B 第二轮收窄)。
    # 之前 try 包整个函数体, 于是 get_neo4j_client() 的配置缺陷、episode_body 的
    # f-string、params 里 14 次 rationale.<field> 取值、to_physical_group_id 的
    # punycode 路径, 任何一处的编程缺陷都会被记成「Neo4j 写失败」⇒ 每个请求静默 207
    # ⇒ 5xx 率恒 0 ⇒ 前端 Outbox 把 207 当「部分成功已保留」继续投递 ⇒ 数据永久丢失
    # 且无人察觉。收窄之后这些缺陷一律原样上抛成 500(响亮), 这也是补进元组的那几类
    # 能保持安全的前提。
    try:
        rows = await neo4j.run_query(query, **params)
    except _NEO4J_WRITE_FAILURES as e:
        # type(e).__name__ 是承重的: ServiceUnavailable(重试有用)与 DatabaseError
        # (对端内部错)在响应体里必须可分辨, 否则运维无法分流。
        logger.error(
            "Neo4j write failed for edge %s: type=%s detail=%s",
            rationale.edge_id,
            type(e).__name__,
            e,
        )
        return WriteStatus(success=False, error=f"{type(e).__name__}: {e}")

    # ⛔ 写确认: 上面的 Cypher 以 `RETURN er.record_id AS record_id` 收尾, 真写成功
    # 恒返回**恰 1 行**。返回 0 行意味着这次写**没有落盘**, 必须记成失败。
    # 为什么非查不可(本轮实测, 存档 evidence-t-edges/fallback-200-falsegreen-*.txt):
    # Neo4jClient 在 JSON fallback 态把查询交给 _run_query_json_fallback, 而那个
    # 分发器只认 MERGE+User+Concept / MATCH+LEARNED 两族, 本函数的
    # `CREATE (er:EdgeRationale …)` 三个分支全不命中 ⇒ 落 else 分支
    # `logger.warning("Unhandled query pattern"); return []` —— **不抛异常**。
    # 进入 fallback 态的路径有三条且都可达: NEO4J_ENABLED=false 构造即 fallback;
    # initialize() 健康检查/AuthError 失败转 fallback; _run_query_neo4j 重试耗尽
    # (ServiceUnavailable 等)转 fallback。⇒ 不查返回值的话, 「Neo4j 宕机」的实际
    # 产出是 **HTTP 200「双写全部成功」而图库里什么都没有**, 比 500 更坏。
    # ⚠️ 这条路是**本卡打通的**: 改前调的 execute_query 不存在, 每次都死在
    # AttributeError, 根本走不到 run_query, 所以 JSON fallback 分支此前不可达。
    if not rows:
        logger.error(
            "Neo4j write NOT confirmed for edge %s (record %s): run_query returned 0 rows "
            "(JSON fallback 的 unhandled-query 分支即如此) — 记为写失败, 不报成功",
            rationale.edge_id,
            record_id,
        )
        return WriteStatus(
            success=False,
            error="Neo4j write not confirmed: query returned no rows (write did not land)",
        )

    logger.info(
        "Neo4j write succeeded for edge %s (record %s)",
        rationale.edge_id,
        record_id,
    )
    return WriteStatus(success=True)


# ═══════════════════════════════════════════════════════════════════════════════
# LanceDB Write — Vectorized Rationale Text
# ═══════════════════════════════════════════════════════════════════════════════


async def _write_lancedb(
    rationale: EdgeRationaleCreate,
    record_id: str,
) -> WriteStatus:
    """
    Write edge rationale to LanceDB for vector retrieval.

    Story 4.2 AC-3: rationale_text vectorized via bge-m3 (1024d Dense).
    Story 4.2 AC-5: delete-before-insert for dedup on update.

    Uses the agentic_rag LanceDBClient following the same pattern
    as lancedb_index_service.py.
    """
    try:
        from agentic_rag.clients.lancedb_client import LanceDBClient

        client = LanceDBClient()

        # Build document text for vectorization
        doc_text = (
            f"{rationale.source_concept} {rationale.relation_type} "
            f"{rationale.target_concept}: {rationale.rationale_text}"
        )

        metadata = {
            "record_id": record_id,
            "edge_id": rationale.edge_id,
            "source_node_id": rationale.source_node_id,
            "target_node_id": rationale.target_node_id,
            "source_concept": rationale.source_concept,
            "target_concept": rationale.target_concept,
            "relation_type": rationale.relation_type,
            "source_type": "edge_rationale",
            "confidence": rationale.confidence,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Delete existing rationale for this edge (delete-before-insert dedup)
        try:
            # extraPaths 让 LanceDBClient 可解析后才看得见: 它只有 add_documents,
            # 没有 delete/upsert/get_db ⇒ 本分支与下面两条 elif/else 都是运行期
            # 恒不进的死分支(TAIL T10)。本卡不删分支(删=改行为), 只关类型。
            if hasattr(client, "delete"):
                await asyncio.to_thread(
                    client.delete,  # pyright: ignore[reportAttributeAccessIssue]
                    table_name="edge_rationales",
                    filter_expr=f'edge_id = "{rationale.edge_id}"',
                )
        except Exception:
            # Table may not exist yet; will be created on insert
            pass

        # Insert new rationale with text + metadata
        # The LanceDBClient handles embedding internally
        if hasattr(client, "add_documents"):
            await asyncio.to_thread(
                client.add_documents,
                table_name="edge_rationales",
                documents=[{"text": doc_text, **metadata}],
            )
        elif hasattr(client, "upsert"):
            await asyncio.to_thread(
                client.upsert,  # pyright: ignore[reportAttributeAccessIssue]  # 见上: 死分支
                table_name="edge_rationales",
                data=[{"text": doc_text, **metadata}],
            )
        else:
            # Fallback: try direct table API
            # 见上: 死分支(LanceDBClient 无 get_db)
            db_conn = (
                client.get_db()  # pyright: ignore[reportAttributeAccessIssue]
                if hasattr(client, "get_db")
                else None
            )
            if db_conn is not None:
                try:
                    table = db_conn.open_table("edge_rationales")
                    table.add([{"text": doc_text, **metadata}])
                except Exception:
                    # Create table if it doesn't exist
                    db_conn.create_table(
                        "edge_rationales",
                        data=[{"text": doc_text, **metadata}],
                    )
            else:
                return WriteStatus(
                    success=False,
                    error="LanceDB client has no usable write method",
                )

        logger.info(
            "LanceDB write succeeded for edge %s (record %s)",
            rationale.edge_id,
            record_id,
        )
        return WriteStatus(success=True)

    except ImportError:
        logger.warning(
            "LanceDB client not available (agentic_rag not installed) for edge %s",
            rationale.edge_id,
        )
        return WriteStatus(
            success=False,
            error="LanceDB client not available (agentic_rag not installed)",
        )

    except (RuntimeError, ConnectionError, OSError, ValueError) as e:
        logger.error(
            "LanceDB write failed for edge %s: %s",
            rationale.edge_id,
            str(e),
        )
        return WriteStatus(success=False, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# POST /record-rationale — Dual-Write Endpoint
# ═══════════════════════════════════════════════════════════════════════════════


@edges_router.post(
    "/record-rationale",
    response_model=EdgeRationaleResponse,
    summary="记录 Edge 连线理由",
    description=(
        "Agent 调用此端点记录用户对连线理由的解释。执行 Neo4j + LanceDB 双写，支持部分失败（207 Multi-Status）。"
    ),
    responses={
        200: {"description": "双写全部成功"},
        207: {"description": "部分成功——一个写入成功，另一个失败"},
        500: {"description": "双写全部失败"},
    },
)
async def record_edge_rationale(
    rationale: EdgeRationaleCreate,
) -> JSONResponse:
    """
    Record edge rationale with dual-write semantics.

    Story 4.2 AC-6: MCP tool record_edge_rationale.
    Story 4.4 AC-3: MCP tool call failure → Outbox retry (frontend side).
    Story 4.4 AC-4: Partial failure → 207, successful part preserved.

    Dual-write flow:
    1. Generate unique record_id
    2. Write to Neo4j (structured KG-triplet) — independent try-catch
    3. Write to LanceDB (vectorized rationale) — independent try-catch
    4. Return combined status (200/207/500)
    """
    record_id = str(uuid.uuid4())

    # Wave-5 Stage B 续 — P0 双写路径! vault_id 注入 ContextVar +
    # 派生 group_id 供 Neo4j INSERT 用.
    resolved_group_id = resolve_vault_group_id(
        rationale.vault_id,
        subject_id=rationale.subject_id,
        legacy_group_id=rationale.group_id,
    )

    logger.info(
        "Recording edge rationale: edge=%s, %s --[%s]--> %s (confidence=%.2f)",
        rationale.edge_id,
        rationale.source_concept,
        rationale.relation_type,
        rationale.target_concept,
        rationale.confidence,
    )

    # Story 4.2 AC-3: Dual-write async — both writes run concurrently
    graphiti_status, lancedb_status = await asyncio.gather(
        _write_neo4j_triplet(rationale, record_id, resolved_group_id),
        _write_lancedb(rationale, record_id),
    )

    response = EdgeRationaleResponse(
        record_id=record_id,
        edge_id=rationale.edge_id,
        relation_type=rationale.relation_type,
        graphiti_status=graphiti_status,
        lancedb_status=lancedb_status,
    )

    # Story 4.4 AC-4: Determine HTTP status based on write results
    if response.fully_successful:
        http_status = status.HTTP_200_OK
    elif response.partially_successful:
        # 207 Multi-Status: one succeeded, one failed
        http_status = 207
        logger.warning(
            "Partial dual-write for edge %s: neo4j=%s, lancedb=%s",
            rationale.edge_id,
            graphiti_status.success,
            lancedb_status.success,
        )
    else:
        # Both failed
        http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.error(
            "Both writes failed for edge %s: neo4j=%s, lancedb=%s",
            rationale.edge_id,
            graphiti_status.error,
            lancedb_status.error,
        )

    return JSONResponse(
        status_code=http_status,
        content=response.model_dump(),
    )
