"""D5 Graphiti 精确读: node_id → entity_uuid → get_by_node_uuid → 属性过滤。

Phase 3 (GRAPHITI-NATIVE-MEMORY-2026-06-10)。

替代 question_generator 的裸 Cypher 读取器 (G-FAKE: 查 :EpisodicNode{node_id},
但 Graphiti 写的是 :Episodic 无 node_id → 恒为空集)。本 reader 读的是
structured_writer 写入的 :Entity-[RELATES_TO]->:Entity canonical 图。

D9 (ChatGPT 计划审查, 实读 edges.py:535):
- get_by_node_uuid 是 undirected (MATCH (n)-[e]-(m)) 返回全部 incident 边
  → active-only 过滤 (invalid_at is None, 排除 belief supersede 旧版)
  → relation 边方向过滤 (source==本节点, 对齐旧 _get_edge_reasons 只查出边)
不用 search(property_filters) — 声明但 search.py 零消费 (D1)。
语义扩展 (search center_node_uuid) 是补充, 不是本 reader 的职责。

group_id 契约: 写侧 (tips.py 4 处) 统一 DEFAULT_GROUP_ID → 读侧默认同一常量,
保证 uuid5(node_id:gid) 两侧一致。

[Source: _bmad-output/研究/2026-06-10-graphiti-native-记忆重构-落地计划.md §Phase 3]
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from graphiti_core.edges import EntityEdge
from graphiti_core.errors import EdgeNotFoundError, NodeNotFoundError

from app.config import DEFAULT_GROUP_ID
from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
from app.graphiti.identity_registry import entity_uuid_for_node

logger = logging.getLogger(__name__)


async def _node_uuid_and_active_edges(
    driver: Any, node_id: str, group_id: Optional[str]
) -> tuple[str, list[EntityEdge]]:
    """解析 uuid + 取该节点全部 active 边 (D9 active-only)。"""
    gid = sanitize_group_id_for_graphiti(group_id or DEFAULT_GROUP_ID)
    uuid = entity_uuid_for_node(node_id, gid)
    try:
        edges = await EntityEdge.get_by_node_uuid(driver, uuid)
    except (EdgeNotFoundError, NodeNotFoundError):
        edges = []
    except Exception as e:  # noqa: BLE001 — 读失败降级为空, 不炸 ACP 组装
        logger.debug(f"[Graphiti-reader] get_by_node_uuid failed for {node_id}: {e}")
        edges = []
    active = [e for e in edges if e.invalid_at is None]
    return uuid, active


async def read_node_tips(
    driver: Any, node_id: str, group_id: Optional[str] = None
) -> list[str]:
    """累积批注 (source=callout) 的 fact 列表。"""
    _uuid, edges = await _node_uuid_and_active_edges(driver, node_id, group_id)
    return [e.fact for e in edges if (e.attributes or {}).get("source") == "callout"]


async def read_node_errors(
    driver: Any, node_id: str, group_id: Optional[str] = None
) -> list[dict[str, str]]:
    """错误史 (source=error), 形状对齐旧 _get_error_history。"""
    _uuid, edges = await _node_uuid_and_active_edges(driver, node_id, group_id)
    return [
        {
            "error_type": (e.attributes or {}).get("error_type", "unknown"),
            "description": e.fact,
        }
        for e in edges
        if (e.attributes or {}).get("source") == "error"
    ]


async def read_node_edge_reasons(
    driver: Any, node_id: str, group_id: Optional[str] = None
) -> list[str]:
    """节点增殖原因 (source=relation), D9 方向过滤: 只取本节点的出边。"""
    uuid, edges = await _node_uuid_and_active_edges(driver, node_id, group_id)
    return [
        e.fact
        for e in edges
        if (e.attributes or {}).get("source") == "relation"
        and e.source_node_uuid == uuid
    ]


async def read_node_conversation_summary(
    driver: Any, node_id: str, group_id: Optional[str] = None
) -> str:
    """最新对话摘要 (source=conversation), 对齐旧 ORDER BY created_at DESC LIMIT 1。"""
    _uuid, edges = await _node_uuid_and_active_edges(driver, node_id, group_id)
    convs = [e for e in edges if (e.attributes or {}).get("source") == "conversation"]
    if not convs:
        return ""
    latest = max(convs, key=lambda e: e.valid_at or e.created_at)
    return latest.fact
