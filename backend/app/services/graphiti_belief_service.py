# Canvas Learning System - Graphiti Belief Version Chain (5-ge-2)
#
# 用户最在乎的 "Graphiti 时序图谱" 能力: 当同一节点的 callout/关系/calibration 写法
# 变化时, 保留旧版本 (invalid_at + status=superseded) + 标记新版本 (valid_at +
# status=active), 让用户未来能问 "我以前认为 X, 后来改成 Y"。
#
# ⚠️ 实读 graphiti-core 0.28.2 源码确诊的 spec 偏离 (记入 Change Log):
#   D1: spec 用 graphiti.search(query=belief_key) 查旧边 → search 是语义混合检索,
#       SearchFilters.property_filters 声明但全代码零消费, 无法按属性精确查。
#       本期改走 driver 原生 Cypher, 按已扁平化为顶层属性的 e.belief_key 精确 WHERE。
#   D2: spec 用 graphiti.driver.update_edge(edge) → driver 无此方法。改用
#       EntityEdge.save(driver) (edges.py:330-367, 纯写库 SET e=$edge_data, 无 LLM)。
#   D3: spec 用 add_triplet() 写新边 → 每次触发 LLM + 2×search + embedding, 对
#       "每次改批注都调" 成本不可接受。改用确定性 EntityEdge(...).save(driver) 直写。
#   R5: _ensure_entity_node 按 (name=node_id, group_id) 确定性复用/新建节点, 保证
#       belief 服务自身跨 run 不分裂版本链 (同 node_id+gid 永远落同一节点; 版本链查询
#       本就按边上 belief_key, 链内部自洽)。
#       ⚠️ 已知局限 (审查 M2, 架构待办): add_episode 用 LLM 抽取的实体名 + uuid4 建节点,
#       与本服务用的原始 node_id 名不同 → 两套节点命名空间暂未统一, belief 边与语义图
#       节点尚未落同一节点。统一 node_id↔实体名映射是架构级决策, 留待后续 (非本期)。
#
# [Source: _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-2-belief-key-version-chain.md]

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import NAMESPACE_DNS, uuid5

from graphiti_core.edges import EntityEdge, get_entity_edge_from_record
from graphiti_core.models.edges.edge_db_queries import get_entity_edge_return_query
from graphiti_core.nodes import EntityNode

from app.graphiti.canvas_episode import edge_name_for_relation
from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti

logger = logging.getLogger(__name__)


def _to_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """归一化为 aware UTC (审查 M1: 防 naive/aware 混用导致 sort/比较 TypeError)。

    调用方传入的 occurred_at 可能是 naive; Neo4j 读回的 valid_at 是 aware。
    同一 belief_key 若混存 naive+aware, get_belief_history 排序/as_of 比较会崩。
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ═══════════════════════════════════════════════════════════════════════════════
# BeliefKeyResolver (AC#2 — 4 种 belief_key 生成, 纯函数)
# ═══════════════════════════════════════════════════════════════════════════════


class BeliefKeyResolver:
    """belief_key 是版本链的稳定身份: 同一 belief_key 的多次写入构成时序链。"""

    @staticmethod
    def make_callout_belief_key(node_id: str, node_path: str, offset: int) -> str:
        """callout:{node_id}:{anchor}, anchor = sha256(node_path + offset)[:16]。"""
        anchor = hashlib.sha256(f"{node_path}:{offset}".encode("utf-8")).hexdigest()[
            :16
        ]
        return f"callout:{node_id}:{anchor}"

    @staticmethod
    def make_edge_belief_key(
        source_node_id: str, relation_type: str, target_node_id: str
    ) -> str:
        """edge:{source_node_id}:{relation_type}:{target_node_id}。"""
        return f"edge:{source_node_id}:{relation_type}:{target_node_id}"

    @staticmethod
    def make_calibration_belief_key(question_id: str, vote_id: str) -> str:
        """calib:{question_id}:{vote_id}。"""
        return f"calib:{question_id}:{vote_id}"

    @staticmethod
    def make_error_belief_key(node_id: str, error_type: str) -> str:
        """error:{node_id}:{error_type}。"""
        return f"error:{node_id}:{error_type}"


def _self_loop_edge_name(belief_key: str) -> str:
    """自环事件 (callout/error/calib) 的 EntityEdge.name (CANVAS_GRAPH_EDGE_TYPES key)。"""
    if belief_key.startswith("callout:"):
        return "SelfAnnotation"
    if belief_key.startswith("error:"):
        return "SelfMisconception"
    if belief_key.startswith("calib:"):
        return "CalibrationVote"
    return "RelatedTo"


# ═══════════════════════════════════════════════════════════════════════════════
# Graphiti driver 接缝 (D1 — 原生 Cypher 精确查; 封装为可 monkeypatch 单测接缝)
# ═══════════════════════════════════════════════════════════════════════════════


async def _ensure_belief_key_index(driver: Any) -> None:
    """best-effort 建 belief_key 关系属性索引 (IF NOT EXISTS 幂等, 失败非致命)。"""
    try:
        await driver.execute_query(
            "CREATE INDEX canvas_belief_key IF NOT EXISTS "
            "FOR ()-[e:RELATES_TO]-() ON (e.belief_key)"
        )
    except Exception as e:  # noqa: BLE001 — 索引是优化, 缺失不影响正确性
        logger.debug("belief_key index ensure skipped (non-fatal): %s", e)


async def _query_edges_by_belief_key(
    driver: Any, group_id: str, belief_key: str, active_only: bool
) -> list[EntityEdge]:
    """driver 原生 Cypher 按 e.belief_key (+可选 status=active) 精确查 RELATES_TO 边。

    RETURN 列复刻 get_entity_edge_return_query 以喂 get_entity_edge_from_record 复用
    官方反序列化 (D1)。
    """
    provider = driver.provider
    return_cols = get_entity_edge_return_query(provider)
    status_clause = " AND e.status = 'active'" if active_only else ""
    query = (
        "MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity) "
        f"WHERE e.group_id = $group_id AND e.belief_key = $belief_key{status_clause} "
        f"RETURN {return_cols}"
    )
    records, _, _ = await driver.execute_query(
        query, group_id=group_id, belief_key=belief_key, routing_="r"
    )
    return [get_entity_edge_from_record(record, provider) for record in records]


async def _find_active_edges_by_belief_key(
    driver: Any, group_id: str, belief_key: str
) -> list[EntityEdge]:
    """查同 belief_key 的当前 active 边 (单测接缝: 可换 FakeEdgeStore)。"""
    return await _query_edges_by_belief_key(
        driver, group_id, belief_key, active_only=True
    )


async def _find_all_edges_by_belief_key(
    driver: Any, group_id: str, belief_key: str
) -> list[EntityEdge]:
    """查同 belief_key 的全部版本 (含 superseded; 单测接缝)。"""
    return await _query_edges_by_belief_key(
        driver, group_id, belief_key, active_only=False
    )


async def _ensure_entity_node(graphiti: Any, node_name: str, group_id: str) -> str:
    """按 (name=node_id, group_id) 确定性复用/新建 Entity 节点, 返回其 uuid。

    保证 belief 服务自身跨 run 不分裂: 同 node_id+gid 永远落同一节点 (先 Cypher 查复用,
    查不到才 uuid5 新建)。
    ⚠️ 局限 (审查 M2): add_episode 用 LLM 抽取的实体名 + uuid4, 与此处原始 node_id 名不同,
    两套节点命名空间暂未统一 — belief 边与语义图节点尚未落同一节点 (架构待办, 非本期)。
    """
    driver = graphiti.driver
    records, _, _ = await driver.execute_query(
        "MATCH (n:Entity {name: $name, group_id: $group_id}) RETURN n.uuid AS uuid LIMIT 1",
        name=node_name,
        group_id=group_id,
        routing_="r",
    )
    if records:
        return records[0]["uuid"]
    # 确定性 uuid5(name:group_id) — 同 name+gid 跨 run 稳定
    node_uuid = str(uuid5(NAMESPACE_DNS, f"{node_name}:{group_id}"))
    node = EntityNode(uuid=node_uuid, name=node_name, group_id=group_id)
    await node.save(driver)
    return node_uuid


# ═══════════════════════════════════════════════════════════════════════════════
# 版本链推进 (AC#3, #4 — 旧边 invalidate + 新边 active)
# ═══════════════════════════════════════════════════════════════════════════════


async def update_belief_version_chain(
    graphiti: Any,
    *,
    belief_key: str,
    group_id: str,
    fact: str,
    occurred_at: datetime,
    node_id: Optional[str] = None,
    source_node_id: Optional[str] = None,
    target_node_id: Optional[str] = None,
    relation_type: Optional[str] = None,
    edge_name: Optional[str] = None,
    source: str = "callout",
    use_bulk: bool = False,
) -> EntityEdge:
    """推进 belief 版本链: 旧 active 边标 superseded+invalid_at, 写新 active 边。

    self-loop 建模 (callout/error/calib): src==tgt, name=SelfAnnotation/... 。
    relation 建模 (wikilink): 真实 source/target, name=edge_name_for_relation(relation_type)。

    AC#7 契约: use_bulk=True 抛 ValueError (add_episode_bulk 不做 edge invalidation)。
    """
    if use_bulk:
        raise ValueError(
            "belief 版本链禁止 add_episode_bulk: bulk ingestion 不做 edge invalidation "
            "(5-ge-2 AC#7, ChatGPT 引用官方文档)"
        )

    occurred_at = _to_aware_utc(occurred_at)  # M1: 统一 aware UTC, 防时间线混存崩溃
    driver = graphiti.driver
    gid = sanitize_group_id_for_graphiti(group_id)  # C-3: Graphiti 边界 sanitize
    await _ensure_belief_key_index(driver)

    # 1. 旧 active 边 → invalid_at = 新 valid_at + status=superseded
    old_edges = await _find_active_edges_by_belief_key(driver, gid, belief_key)
    for old in old_edges:
        old.invalid_at = occurred_at
        old.expired_at = occurred_at
        old.attributes = {**(old.attributes or {}), "status": "superseded"}
        await old.save(driver)

    # 2. 解析 source/target 节点 (R5: 复用已存在 Entity)
    if source_node_id and target_node_id:
        src_uuid = await _ensure_entity_node(graphiti, source_node_id, gid)
        tgt_uuid = await _ensure_entity_node(graphiti, target_node_id, gid)
        name = edge_name or edge_name_for_relation(relation_type)
    else:
        loop_node = node_id or source_node_id or target_node_id
        if not loop_node:
            raise ValueError(
                "update_belief_version_chain: 自环事件缺 node_id (callout/error/calib 必须有)"
            )
        src_uuid = tgt_uuid = await _ensure_entity_node(graphiti, loop_node, gid)
        name = edge_name or _self_loop_edge_name(belief_key)

    # 3. 写新 active 边 (D3: 确定性直写, 不调 add_triplet)
    new_edge = EntityEdge(
        group_id=gid,
        source_node_uuid=src_uuid,
        target_node_uuid=tgt_uuid,
        created_at=occurred_at,
        valid_at=occurred_at,
        invalid_at=None,
        name=name,
        fact=fact,
        attributes={
            "belief_key": belief_key,
            "status": "active",
            "source": source,
        },
    )
    await new_edge.save(driver)
    logger.info(
        "belief chain advanced: bk=%s superseded=%d new_uuid=%s",
        belief_key,
        len(old_edges),
        new_edge.uuid,
    )
    return new_edge


# ═══════════════════════════════════════════════════════════════════════════════
# 历史查询 (AC#6 — 全版本链 + current + as_of 时序回溯)
# ═══════════════════════════════════════════════════════════════════════════════


async def get_belief_history(
    graphiti: Any,
    belief_key: str,
    group_id: str,
    as_of: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    """返回 belief_key 全部版本链 (按 valid_at 升序), 标记 current (最新 active)。

    as_of 给定时, 额外标记 active_at_as_of=True 在该时刻有效的版本 (时序回溯)。
    """
    driver = graphiti.driver
    gid = sanitize_group_id_for_graphiti(group_id)
    as_of = _to_aware_utc(as_of)  # M1: 防 naive/aware 混用
    edges = await _find_all_edges_by_belief_key(driver, gid, belief_key)

    # M1: 排序/比较前统一 aware UTC (历史数据可能混存 naive)
    def _vk(e: EntityEdge) -> datetime:
        return _to_aware_utc(e.valid_at or e.created_at)

    edges.sort(key=_vk)

    active_edges = [
        e
        for e in edges
        if (e.attributes or {}).get("status") == "active" and e.invalid_at is None
    ]
    current_uuid = max(active_edges, key=_vk).uuid if active_edges else None

    history: list[dict[str, Any]] = []
    for e in edges:
        valid_at = _vk(e)
        invalid_at = _to_aware_utc(e.invalid_at)
        active_at_as_of = False
        if as_of is not None and valid_at is not None:
            active_at_as_of = valid_at <= as_of and (
                invalid_at is None or as_of < invalid_at
            )
        history.append(
            {
                "uuid": e.uuid,
                "name": e.name,
                "fact": e.fact,
                "status": (e.attributes or {}).get("status"),
                "source": (e.attributes or {}).get("source"),
                "valid_at": e.valid_at,
                "invalid_at": e.invalid_at,
                "current": e.uuid == current_uuid,
                "active_at_as_of": active_at_as_of,
                "edge": e,
            }
        )
    return history


# ═══════════════════════════════════════════════════════════════════════════════
# episode_worker 协同入口 (AC#5 — 演化事件旁路, belief 业务不泄漏进 worker)
# ═══════════════════════════════════════════════════════════════════════════════


async def maybe_update_belief_from_task(
    graphiti: Any, task: Any
) -> Optional[EntityEdge]:
    """从 EpisodeTask.metadata 解 belief 字段并推进版本链 (供 Phase B hook 调)。

    metadata 无 belief_key → 直接 return None (非演化事件不进版本链)。
    """
    metadata = getattr(task, "metadata", None) or {}
    belief_key = metadata.get("belief_key")
    if not belief_key:
        logger.debug("belief skip: task.metadata 无 belief_key")
        return None

    occurred_at = metadata.get("occurred_at") or getattr(task, "reference_time", None)
    if occurred_at is None:
        occurred_at = datetime.now(timezone.utc)

    return await update_belief_version_chain(
        graphiti,
        belief_key=belief_key,
        group_id=metadata.get("group_id") or getattr(task, "group_id", ""),
        fact=metadata.get("fact") or getattr(task, "episode_body", "") or belief_key,
        occurred_at=occurred_at,
        node_id=metadata.get("node_id"),
        source_node_id=metadata.get("source_node_id"),
        target_node_id=metadata.get("target_node_id"),
        relation_type=metadata.get("relation_type"),
        edge_name=metadata.get("edge_name"),
        source=metadata.get("source", "callout"),
    )
