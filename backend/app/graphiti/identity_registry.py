"""D3 身份层: node_id ↔ Graphiti entity_uuid 的单一确定性映射真相源。

Phase 0 (GRAPHITI-NATIVE-MEMORY-2026-06-10)。

为什么需要这层 (审查 M2 + ChatGPT 计划审查"命门"):
当前图里存在三套实体命名空间 — Canvas node_id / belief 服务自造节点 /
add_episode LLM 抽取的实体名。不统一身份, 任何"按 node_id 精确读 Graphiti"
都会退回裸 Cypher 拼字段的老路 (G-FAKE)。

契约:
- 所有结构化 writer/reader 必须经 `entity_uuid_for_node()` 取 uuid, 禁止自造。
- 一期决策 (已拍板): 结构化层独占 node_id-uuid 命名空间 = "exact-read 主图";
  add_episode LLM 抽取节点是"语义影子图", 不合并、不参与 node 精确读。
  二期若需把语义扩展稳定挂到同一学习节点, 另加 alias/merge 表, 不在本层硬融合。
- D8: 新建节点时若给了 embedder 则生成 name_embedding —
  EntityNode.save() 是纯持久化不自动 embed (实读 nodes.py/edges.py 0.28.2==v0.29.1)。

[Source: _bmad-output/研究/2026-06-10-graphiti-native-记忆重构-落地计划.md §Phase 0]
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import NAMESPACE_DNS, uuid5

from graphiti_core.errors import NodeNotFoundError
from graphiti_core.nodes import EntityNode


def entity_uuid_for_node(node_id: str, sanitized_group_id: str) -> str:
    """node 的稳定 Graphiti 身份: uuid5(node_id:group_id)。

    同 (node_id, group_id) 跨 run 恒定; 不同 group 隔离 (防跨 vault 串)。
    group_id 必须已经过 sanitize_group_id_for_graphiti (冒号→双下划线)。
    """
    return str(uuid5(NAMESPACE_DNS, f"{node_id}:{sanitized_group_id}"))


class IdentityRegistry:
    """确保某 node_id 对应的 :Entity 节点存在并复用其 uuid (幂等)。"""

    @staticmethod
    async def ensure_entity_node(
        driver: Any,
        node_id: str,
        sanitized_group_id: str,
        embedder: Optional[Any] = None,
        title: str = "",
    ) -> str:
        """查到已有 → 复用 uuid; 不存在 → 确定性新建 (+D8 可选 embedding)。

        ⚠️ 只捕 NodeNotFoundError (审查: except Exception 会把驱动故障
        误判成"节点不存在"而盲目重建)。
        """
        uuid = entity_uuid_for_node(node_id, sanitized_group_id)
        try:
            await EntityNode.get_by_uuid(driver, uuid)
            return uuid
        except NodeNotFoundError:
            node = EntityNode(
                uuid=uuid,
                name=node_id,
                group_id=sanitized_group_id,
                summary=title or node_id,
                attributes={"node_id": node_id},
            )
            if embedder is not None:
                # D8: save() 不自动生成 embedding, 必须在此显式生成,
                # 否则结构化图无向量 → center_node_uuid 语义扩展失效。
                await node.generate_name_embedding(embedder)
            await node.save(driver)
            return uuid
