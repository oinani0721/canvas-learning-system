"""Fix-E1 (2026-06-10): 节点增殖原因边同步 — markdown frontmatter → Neo4j CANVAS_EDGE。

GAP-E: 用户拉新节点标的"相关原因"写在新节点 md frontmatter `relationships[]`
(node-derivation.ts: {type, target: [[源笔记]], description?})。但降级到 markdown 后:
  - 旧 `sync_all_edges_to_neo4j` 读 .canvas JSON (vault 里已 0 个 .canvas)
  - 后端无任何代码读 frontmatter relationships → CANVAS_EDGE
→ CANVAS_EDGE = 0, question_generator._get_edge_reasons (读 CANVAS_EDGE.label) 永远空。

本服务扫 vault md frontmatter relationships[] → MERGE CANVAS_EDGE{label=原因}, 让检验白板
能在针对性考察时拿到"用户为什么把这两个概念连起来"的原因 (用户 Q2: 出题时给 LLM 当上下文)。

触发: main.py 启动时搭车 Story 2.1 wikilink eager-build 之后 (与之同源扫 vault markdown)。
对齐架构方向: backend 从 .canvas 迁到 markdown 图遍历 (project_context_enrichment_gap)。

读侧契约 (question_generator.py:966-984 _get_edge_reasons):
  MATCH (n:CanvasNode {id: $node_id})-[r:CANVAS_EDGE]->(m) WHERE r.label IS NOT NULL
  RETURN r.label
→ 边方向: 持有 frontmatter 的节点(派生节点) -[CANVAS_EDGE{label}]-> target(源节点)。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

import frontmatter

logger = logging.getLogger(__name__)

_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _resolve_node_id(raw: Any) -> str:
    """'[[节点/base-case]]' / '[[源笔记|别名]]' / 'base-case' → 'base-case' (basename, 去别名)。"""
    text = str(raw or "")
    m = _WIKILINK_RE.search(text)
    inner = m.group(1) if m else text
    inner = inner.split("|", 1)[0]  # 去 [[target|alias]] 别名
    return inner.split("/")[-1].strip().removesuffix(".md")


class NodeRelationshipSyncService:
    """扫 vault md frontmatter relationships[] → Neo4j CANVAS_EDGE (原因边)。"""

    def __init__(self) -> None:
        self._neo4j = None

    def _client(self):
        if self._neo4j is None:
            from app.clients.neo4j_client import get_neo4j_client

            self._neo4j = get_neo4j_client()
        return self._neo4j

    async def sync(self, vault_path: str) -> dict[str, int]:
        """扫描 vault, 把节点 frontmatter relationships 同步成 CANVAS_EDGE。

        Returns: {nodes_with_relationships, edges_synced, failed}。
        """
        base = Path(vault_path)
        if not base.exists():
            logger.warning("[Fix-E1] vault path 不存在, 跳过原因边同步: %s", vault_path)
            return {"nodes_with_relationships": 0, "edges_synced": 0, "failed": 0}

        client = self._client()
        nodes_with_rel = 0
        edges_synced = 0
        failed = 0

        for md in base.rglob("*.md"):
            rels = self._read_relationships(md)
            if not rels:
                continue
            source_id = md.stem  # node_id = 文件 basename (扁平节点池约定)
            nodes_with_rel += 1
            for rel in rels:
                target_id = _resolve_node_id(rel.get("target"))
                rel_type = str(rel.get("type") or "related_to")
                description = str(rel.get("description") or "").strip()
                # 原因优先; 无原因时退到关系类型, 保证 label 非空 (否则 _get_edge_reasons 过滤掉)
                label = description or rel_type
                if not target_id or target_id == source_id:
                    continue
                try:
                    await self._merge_edge(
                        client, source_id, target_id, rel_type, label
                    )
                    edges_synced += 1
                except Exception as e:  # noqa: BLE001 — 单边失败不阻断批量
                    failed += 1
                    logger.debug(
                        "[Fix-E1] edge sync failed %s->%s: %s", source_id, target_id, e
                    )

        logger.info(
            "[Fix-E1] 原因边同步: %d 节点有 relationships, %d 边写入, %d 失败",
            nodes_with_rel,
            edges_synced,
            failed,
        )
        return {
            "nodes_with_relationships": nodes_with_rel,
            "edges_synced": edges_synced,
            "failed": failed,
        }

    @staticmethod
    def _read_relationships(md_path: Path) -> Optional[list[dict[str, Any]]]:
        """读单个 md 的 frontmatter relationships[] (非 list 或解析失败 → None)。"""
        try:
            post = frontmatter.load(str(md_path))
        except Exception as e:  # noqa: BLE001 — 损坏 frontmatter 不阻断扫描
            logger.debug("[Fix-E1] frontmatter 解析失败 %s: %s", md_path.name, e)
            return None
        rels = post.metadata.get("relationships")
        if not isinstance(rels, list):
            return None
        return [r for r in rels if isinstance(r, dict)]

    async def _merge_edge(
        self, client: Any, source_id: str, target_id: str, rel_type: str, label: str
    ) -> None:
        """MERGE (source)-[CANVAS_EDGE{label=原因}]->(target) (确定性 edge id 幂等)。"""
        edge_id = f"rel-{source_id}-{rel_type}-{target_id}"
        await client.run_query(
            """
            MERGE (s:CanvasNode {id: $source_id})
            MERGE (t:CanvasNode {id: $target_id})
            MERGE (s)-[e:CANVAS_EDGE {id: $edge_id}]->(t)
            SET e.label = $label,
                e.relation_type = $rel_type,
                e.synced_from = 'frontmatter'
            """,
            source_id=source_id,
            target_id=target_id,
            edge_id=edge_id,
            label=label,
            rel_type=rel_type,
        )


_node_relationship_sync_service: Optional[NodeRelationshipSyncService] = None


def get_node_relationship_sync_service() -> NodeRelationshipSyncService:
    """Singleton accessor。"""
    global _node_relationship_sync_service
    if _node_relationship_sync_service is None:
        _node_relationship_sync_service = NodeRelationshipSyncService()
    return _node_relationship_sync_service
