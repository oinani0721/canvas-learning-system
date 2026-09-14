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

from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id

# T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式 (graphiti_core validator 拒冒号)
from app.graphiti.group_id_compat import to_physical_group_id
from app.models.edge_rationale import (
    EdgeRationaleCreate,
    EdgeRationaleResponse,
    WriteStatus,
)

logger = logging.getLogger(__name__)

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
    try:
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

        # CARD-T-EDGES (第十四批): 已改调 run_query(**params) —— Neo4jClient 上
        # 只有 run_query(query, **params)(neo4j_client.py:536), 从来没有
        # execute_query, 旧写法每次调用都抛 AttributeError。run_query 收的是
        # **params 而非位置 dict, 故参数同步展开(键名逐字不变)。
        # 下面 except 元组同时补了 AttributeError 作纵深: **方法名**错配(属性解析
        # 失败)降级成 WriteStatus(success=False), 由 handler 记成半成功 207, 而不是
        # 穿透 asyncio.gather(无 return_exceptions=True)与无 try 的 handler 崩成
        # 500 —— 那会把 LanceDB 侧已经写成功的那一半也一起丢掉。
        # ⚠️ 如实声明覆盖边界(Codex r1 整改, 原注释写「任何方法名 / 签名错配」不实):
        #   - **签名**错配(实参与 run_query(self, query, **params) 不匹配)抛的是
        #     TypeError, **不在**本元组内, 仍会上抛 —— 这是有意的, 签名错配是本进程
        #     的编程缺陷, 不该伪装成「对端写失败」。
        #   - 本 except 覆盖整个函数体, 故 params 组装期的 AttributeError(如模型字段
        #     改名)也会被记成 Neo4j 写失败而非报错。收窄它需要改 try 范围 = 行为变更,
        #     已登记移交, 不在本卡范围。
        # 生产取回路仍由 get_neo4j_client() 决定(是否真连 Neo4j 不在本卡范围)。
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
        await neo4j.run_query(query, **params)

        logger.info(
            "Neo4j write succeeded for edge %s (record %s)",
            rationale.edge_id,
            record_id,
        )
        return WriteStatus(success=True)

    except (RuntimeError, ConnectionError, asyncio.TimeoutError, OSError, AttributeError) as e:
        logger.error(
            "Neo4j write failed for edge %s: %s",
            rationale.edge_id,
            str(e),
        )
        return WriteStatus(success=False, error=str(e))


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
