"""D2 结构化 Graphiti 写入适配器: 用户显式标注确定性写 :Entity/RELATES_TO (零 LLM)。

Phase 1 (GRAPHITI-NATIVE-MEMORY-2026-06-10)。

为什么不走 add_triplet: 实读 graphiti.py:1450-1568 (0.28.2) — add_triplet 跑
3×embedding + 2×hybrid search + resolve_extracted_edge(llm_client), 对"每打一条
批注/每拉一个节点"的高频显式事件成本/延迟不可接受, 且显式事件不需要 LLM 猜矛盾。
为什么不是裸 Cypher: 写的是 Graphiti canonical :Entity-[RELATES_TO]->:Entity
(经 EntityEdge.save, edges.py:330-367 官方持久化路径), 不伪造 :EpisodicNode/
:CanvasNode 冒充 Graphiti (G-FAKE 教训)。

建模约定 (读侧 graphiti_memory_reader 按 attributes 过滤):
- callout/error/conversation → 自环边 (src==tgt), attributes.source 区分
- relation 原因 → 真实 src→tgt 边, fact=用户写的"为什么"
- 全部带 attributes.node_id (持有方) + valid_at; D8 显式 embedding
- belief 版本链: D10 统一入口在此, 内部委托 graphiti_belief_service
  (不重写其旧边 supersede / as_of 版本语义)

[Source: _bmad-output/研究/2026-06-10-graphiti-native-记忆重构-落地计划.md §Phase 1]
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Optional
from uuid import NAMESPACE_DNS, uuid5

from graphiti_core.edges import EntityEdge

from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
from app.graphiti.identity_registry import IdentityRegistry


def _deterministic_edge_uuid(kind: str, node_key: str, gid: str, fact: str) -> str:
    """同 (类型, 节点, group, 内容) → 同 uuid → save 的 MERGE 语义幂等。

    重跑回填 / 重存同文件不重复建边; 内容变了 = 新边 (累积模型)。
    """
    fact_hash = hashlib.sha256(fact.encode("utf-8")).hexdigest()[:16]
    return str(uuid5(NAMESPACE_DNS, f"{kind}:{node_key}:{gid}:{fact_hash}"))


async def _save_edge_with_embedding(
    edge: EntityEdge, driver: Any, embedder: Optional[Any]
) -> EntityEdge:
    """D8: save() 纯持久化不自动 embed, 必须在此显式生成 fact_embedding。"""
    if embedder is not None:
        await edge.generate_embedding(embedder)
    await edge.save(driver)
    return edge


async def _self_loop_edge(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    name: str,
    fact: str,
    occurred_at: datetime,
    attributes: dict[str, Any],
) -> EntityEdge:
    """callout/error/conversation 的自环建模: 节点对自身的陈述。"""
    gid = sanitize_group_id_for_graphiti(group_id)  # C-3 边界 sanitize
    uuid = await IdentityRegistry.ensure_entity_node(
        driver, node_id, gid, embedder=embedder
    )
    edge = EntityEdge(
        uuid=_deterministic_edge_uuid(name, node_id, gid, fact),  # 幂等
        group_id=gid,
        source_node_uuid=uuid,
        target_node_uuid=uuid,
        created_at=occurred_at,
        valid_at=occurred_at,
        invalid_at=None,
        name=name,
        fact=fact,
        attributes={**attributes, "node_id": node_id},
    )
    return await _save_edge_with_embedding(edge, driver, embedder)


async def write_callout(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    callout_type: str,
    text: str,
    occurred_at: datetime,
) -> EntityEdge:
    """用户批注 → 自环 SelfAnnotation 边 (fact=批注正文)。"""
    return await _self_loop_edge(
        driver,
        embedder,
        node_id=node_id,
        group_id=group_id,
        name="SelfAnnotation",
        fact=text,
        occurred_at=occurred_at,
        attributes={
            "source": "callout",
            "event_type": "callout_added",
            "callout_type": callout_type,
        },
    )


async def write_error(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    error_type: str,
    description: str,
    occurred_at: datetime,
) -> EntityEdge:
    """错误标记 → 自环 SelfMisconception 边 (fact=错误描述)。"""
    return await _self_loop_edge(
        driver,
        embedder,
        node_id=node_id,
        group_id=group_id,
        name="SelfMisconception",
        fact=description,
        occurred_at=occurred_at,
        attributes={
            "source": "error",
            "event_type": "error_marked",
            "error_type": error_type,
        },
    )


async def write_conversation_summary(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    summary: str,
    occurred_at: datetime,
) -> EntityEdge:
    """对话归档摘要 → 自环 ConversationSummary 边 (fact=AI 生成的对话摘要)。

    用户拍板 (2026-06-10): 归档时写摘要边供检验白板精确读;
    对话全文仍走 add_episode 非结构化通道做语义抽取。
    """
    return await _self_loop_edge(
        driver,
        embedder,
        node_id=node_id,
        group_id=group_id,
        name="ConversationSummary",
        fact=summary,
        occurred_at=occurred_at,
        attributes={
            "source": "conversation",
            "event_type": "conversation_archived",
        },
    )


async def write_relation_reason(
    driver: Any,
    embedder: Optional[Any],
    *,
    source_node_id: str,
    target_node_id: str,
    group_id: str,
    relation_type: Optional[str],
    reason: str,
    occurred_at: datetime,
) -> EntityEdge:
    """节点增殖原因 → 真实 src→tgt 边 (fact=用户写的"为什么拉出/连接")。"""
    gid = sanitize_group_id_for_graphiti(group_id)
    su = await IdentityRegistry.ensure_entity_node(
        driver, source_node_id, gid, embedder=embedder
    )
    tu = await IdentityRegistry.ensure_entity_node(
        driver, target_node_id, gid, embedder=embedder
    )
    edge = EntityEdge(
        uuid=_deterministic_edge_uuid(
            relation_type or "RelatedTo",
            f"{source_node_id}->{target_node_id}",
            gid,
            reason,
        ),  # 幂等
        group_id=gid,
        source_node_uuid=su,
        target_node_uuid=tu,
        created_at=occurred_at,
        valid_at=occurred_at,
        invalid_at=None,
        name=relation_type or "RelatedTo",
        fact=reason,
        attributes={
            "node_id": source_node_id,  # 读侧按持有方 node 精确查
            "source": "relation",
            "event_type": "wikilink_added",
            "relation_type": relation_type,
        },
    )
    return await _save_edge_with_embedding(edge, driver, embedder)


async def write_belief_version(graphiti: Any, **kwargs: Any) -> Any:
    """D10: belief 版本链统一入口 — 内部委托 graphiti_belief_service。

    版本语义 (旧 active 边 supersede + 新 active 边 + as_of 回溯) 留在
    belief 服务, 不在此抽薄 (ChatGPT 计划审查)。
    """
    from app.services.graphiti_belief_service import update_belief_version_chain

    return await update_belief_version_chain(graphiti, **kwargs)
