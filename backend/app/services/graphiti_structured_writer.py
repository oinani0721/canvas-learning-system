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
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import NAMESPACE_DNS, uuid5

from graphiti_core.edges import EntityEdge
from graphiti_core.errors import EdgeNotFoundError

from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
from app.graphiti.identity_registry import IdentityRegistry

logger = logging.getLogger(__name__)


async def _preserved_times(
    driver: Any, edge_uuid: str, occurred_at: datetime
) -> tuple[datetime, datetime]:
    """create-or-preserve (P3/A4 2026-06-26): 边已存在则保留其 (created_at, valid_at),
    否则用 occurred_at。

    根治时序污染: EntityEdge.save 用 `SET e=$edge_data` 全量覆写。启动回填用回填
    时刻 save 同 uuid 边时, 若不保留, 会把实时写入的真实事件时间冲成回填时刻
    (实测: 图里所有边 created_at 全=容器启动时刻)。保留原始时间后, 回填只补缺边、
    不篡改已有边的时间线。新边 (EdgeNotFoundError) 用 occurred_at (= 调用方传的
    真实源事件时间)。
    """
    try:
        existing = await EntityEdge.get_by_uuid(driver, edge_uuid)
        return (existing.created_at or occurred_at, existing.valid_at or occurred_at)
    except EdgeNotFoundError:
        return occurred_at, occurred_at
    except Exception as e:  # noqa: BLE001 — 查询失败退新建语义, 不阻断写入
        logger.debug("[A4] preserve-times 查询失败, 用 occurred_at: %s", e)
        return occurred_at, occurred_at


def _deterministic_edge_uuid(kind: str, node_key: str, gid: str, fact: str) -> str:
    """同 (类型, 节点, group, 内容) → 同 uuid → save 的 MERGE 语义幂等。

    重跑回填 / 重存同文件不重复建边; 内容变了 = 新边 (累积模型)。
    """
    fact_hash = hashlib.sha256(fact.encode("utf-8")).hexdigest()[:16]
    return str(uuid5(NAMESPACE_DNS, f"{kind}:{node_key}:{gid}:{fact_hash}"))


def canonical_callout_fact(
    callout_type: str, understanding: Optional[str], body: str
) -> str:
    """三通道统一的批注存储格式 (去重修复 2026-06-13)。

    此前即时上报/停笔同步/启动回填各自包装 ("Tip:…|Content:…" /
    "Callout […]: … | [hash:…]" / "💡 Tips - [x] …") → 同一批注三个指纹
    三条边。writer 持有唯一格式, 调用方一律传裸文本。
    """
    head = f"[{callout_type}·{understanding}]" if understanding else f"[{callout_type}]"
    return f"{head} {body}"


def _identity_first_line(text: str) -> str:
    """批注的逻辑身份 = 首个非空行 (= 用户选中的文本, 三通道天然一致)。

    同一批注的不同版本 (即时上报的'仅选中' → 停笔同步的'含我的理解全文')
    → 同身份 → 同 uuid → MERGE 原地升级为最新最全, 不并排存多条。
    新批注 (不同选中文本) → 新身份 → 累积模型不受影响。
    """
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return text


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
    identity_text: Optional[str] = None,
) -> EntityEdge:
    """callout/error/conversation 的自环建模: 节点对自身的陈述。

    identity_text 给定时, uuid 按逻辑身份 (节点+批注首行) 而非全文指纹 —
    同一批注的版本演进 (选中→续写全文) MERGE 原地升级, 不并排存多条。
    """
    gid = sanitize_group_id_for_graphiti(group_id)  # C-3 边界 sanitize
    node_uuid = await IdentityRegistry.ensure_entity_node(
        driver, node_id, gid, embedder=embedder
    )
    edge_uuid = _deterministic_edge_uuid(name, node_id, gid, identity_text or fact)
    # P3 (A4): 边已存在则保留原始时间, 防回填覆写真实事件时间
    created_at, valid_at = await _preserved_times(driver, edge_uuid, occurred_at)
    edge = EntityEdge(
        uuid=edge_uuid,
        group_id=gid,
        source_node_uuid=node_uuid,
        target_node_uuid=node_uuid,
        created_at=created_at,
        valid_at=valid_at,
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
    understanding: Optional[str] = None,
    annotation_id: Optional[str] = None,
) -> EntityEdge:
    """用户批注 → 自环 SelfAnnotation 边。

    text 必须是裸批注正文 (选中文本 + 续写, 无通道包装) — 存储格式由
    canonical_callout_fact 统一。

    P0 (A+-prime 2026-06-26): 身份优先用稳定 annotation_id (cb-xxx, 前端
    wrapSelection 生成嵌入 callout 标题)。改批注正文不再换身份(防孤儿)，
    同节点同一句原文的两条不同批注不再因首行相同碰撞合并。无 id 的历史批注
    回退首行身份 (向后兼容)。
    """
    return await _self_loop_edge(
        driver,
        embedder,
        node_id=node_id,
        group_id=group_id,
        name="SelfAnnotation",
        fact=canonical_callout_fact(callout_type, understanding, text),
        occurred_at=occurred_at,
        attributes={
            "source": "callout",
            "event_type": "callout_added",
            "callout_type": callout_type,
            "understanding": understanding,
            "annotation_id": annotation_id or None,
        },
        identity_text=annotation_id or _identity_first_line(text),
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
    edge_uuid = _deterministic_edge_uuid(
        relation_type or "RelatedTo",
        f"{source_node_id}->{target_node_id}",
        gid,
        reason,
    )  # 幂等
    # P3 (A4): 边已存在则保留原始时间, 防回填覆写真实事件时间
    created_at, valid_at = await _preserved_times(driver, edge_uuid, occurred_at)
    edge = EntityEdge(
        uuid=edge_uuid,
        group_id=gid,
        source_node_uuid=su,
        target_node_uuid=tu,
        created_at=created_at,
        valid_at=valid_at,
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
