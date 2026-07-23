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


class CanvasProjectionSync:
    """扫 vault md frontmatter relationships[] → Neo4j CANVAS_EDGE (原因边)。"""

    def __init__(self) -> None:
        self._neo4j = None

    def _client(self):
        if self._neo4j is None:
            from app.clients.neo4j_client import get_neo4j_client

            self._neo4j = get_neo4j_client()
        return self._neo4j

    async def sync(self, vault_path: str, group_id: str = "") -> dict[str, int]:
        """扫描 vault, 把节点 frontmatter relationships 同步成 CANVAS_EDGE。

        Args:
            vault_path: vault 根目录。
            group_id: 逻辑 D16 group_id (如 vault:canvas_vault), 由调用方
                (main.py 启动流程) 经 build_vault_group_id 构造。T2 (2026-07-10):
                MERGE 的 CanvasNode / CANVAS_EDGE 均落此 group (物理 __ 格式),
                多 vault 不串。空值时回退当前 vault 推导。

        Returns: {nodes_with_relationships, edges_synced, failed}。
        """
        base = Path(vault_path)
        if not base.exists():
            logger.warning("[Fix-E1] vault path 不存在, 跳过原因边同步: %s", vault_path)
            return {"nodes_with_relationships": 0, "edges_synced": 0, "failed": 0}

        # T2 (2026-07-10): group 缺省回退当前 vault (与 vault_backfill 同源)
        if not group_id:
            from app.config import get_current_vault_id
            from app.core.subject_config import build_vault_group_id

            group_id = build_vault_group_id(get_current_vault_id())
        from app.graphiti.group_id_compat import to_physical_group_id

        physical_gid = to_physical_group_id(group_id)

        client = self._client()
        nodes_with_rel = 0
        edges_synced = 0
        failed = 0
        alive_edge_ids: list[str] = []
        # 终验审查修正 (2026-07-24, ChatGPT 第三轮 §幽灵边): 「未扫描到 ≠ 不存在」
        # — 解析失败的文件其旧边必须豁免失效 (保护前缀), 写入失败的边同样
        # 计入 alive (写失败 ≠ 边该死)。只有「文件确认无此关系」才允许失效。
        protected_prefixes: list[str] = []

        for md in base.rglob("*.md"):
            rels = self._read_relationships(md)
            if rels is None:
                # frontmatter 解析失败 — 无法确认该文件的关系现状, 旧边全部豁免
                protected_prefixes.append(f"rel-{physical_gid}-{md.stem}-")
                continue
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
                edge_id = f"rel-{physical_gid}-{source_id}-{rel_type}-{target_id}"
                alive_edge_ids.append(edge_id)  # 先记 alive — 写失败也不判死
                try:
                    await self._merge_edge(
                        client,
                        source_id,
                        target_id,
                        rel_type,
                        label,
                        physical_gid,
                        rel=rel,
                    )
                    edges_synced += 1
                except Exception as e:  # noqa: BLE001 — 单边失败不阻断批量
                    failed += 1
                    logger.debug("[Fix-E1] edge sync failed %s->%s: %s", source_id, target_id, e)

        # 批次4' 3-3 幽灵边对账 (MEM-FLYWHEEL): frontmatter 里已删/改名的
        # relationship, 旧 CANVAS_EDGE 此前永远留在图里 (MERGE 只增不删,
        # 拆分时间线越老越脏)。软失效不物理删 — 时间线可追溯, 查询侧过滤。
        invalidated = 0
        try:
            records = await client.run_query(
                """
                MATCH ()-[e:CANVAS_EDGE]-()
                WHERE e.group_id = $group_id AND e.synced_from = 'frontmatter'
                  AND NOT e.id IN $alive_ids AND e.invalidated_at IS NULL
                  AND NOT any(p IN $protected WHERE e.id STARTS WITH p)
                SET e.invalidated_at = datetime(), e.active = false
                RETURN count(DISTINCT e) AS c
                """,
                group_id=physical_gid,
                alive_ids=alive_edge_ids,
                protected=protected_prefixes,
            )
            if records:
                data = records[0] if isinstance(records[0], dict) else records[0].data()
                invalidated = int(data.get("c") or 0)
        except Exception as e:  # noqa: BLE001 — 对账失败不阻断同步
            logger.warning("[3-3] 幽灵边对账失败 (本轮跳过): %s", e)

        logger.info(
            "[Fix-E1] 原因边同步: %d 节点有 relationships, %d 边写入, %d 失败, %d 幽灵边失效",
            nodes_with_rel,
            edges_synced,
            failed,
            invalidated,
        )
        return {
            "nodes_with_relationships": nodes_with_rel,
            "edges_synced": edges_synced,
            "failed": failed,
            "edges_invalidated": invalidated,
        }

    @staticmethod
    def _read_relationships(md_path: Path) -> Optional[list[dict[str, Any]]]:
        """读单个 md 的 frontmatter relationships[]。

        终验审查修正 (2026-07-24) — 返回值语义承载幽灵边对账的保护判定:
        - None = **解析失败** (损坏 frontmatter) → 无法确认现状, 该文件旧边豁免失效
        - []   = 文件正常但无 relationships (缺失/非 list/空) → 旧边允许失效
                 (用户删光关系正是失效该发生的场景)
        """
        try:
            post = frontmatter.load(str(md_path))
        except Exception as e:  # noqa: BLE001 — 损坏 frontmatter 不阻断扫描
            logger.debug("[Fix-E1] frontmatter 解析失败 %s: %s", md_path.name, e)
            return None
        rels = post.metadata.get("relationships")
        if not isinstance(rels, list):
            return []
        return [r for r in rels if isinstance(r, dict)]

    async def _merge_edge(
        self,
        client: Any,
        source_id: str,
        target_id: str,
        rel_type: str,
        label: str,
        physical_gid: str,
        rel: Optional[dict[str, Any]] = None,
    ) -> str:
        """MERGE (source)-[CANVAS_EDGE{label=原因}]->(target) (确定性 edge id 幂等)。

        T2 (2026-07-10): 节点/边均 SET group_id (物理 __ 格式); edge_id 纳入
        group 前缀 — 跨 vault 同名节点对的边不再共享 id 互相覆盖 label。
        MERGE 键保持 {id} 不加 group, 对齐 SyncService / exam_service_ext 的
        CanvasNode 写契约 (键结构分叉会造重复节点)。

        批次4' (MEM-FLYWHEEL): 3-2 ON CREATE 打 created_at (首建时序, 幂等重跑
        不覆盖) + relationships[] 的 derived_at 透传; 3-1 派生时刻理解快照
        (source_mastery_at_derivation / confusion) 随边留档; 3-3 复活清除失效
        标记 (md 里边回来了 → 幽灵标记撤销)。边身份 = source→type→target
        (reason 变更走 SET label 属性更新, 不并排新增)。
        """
        rel = rel or {}
        edge_id = f"rel-{physical_gid}-{source_id}-{rel_type}-{target_id}"
        await client.run_query(
            """
            MERGE (s:CanvasNode {id: $source_id})
            SET s.group_id = coalesce(s.group_id, $group_id)
            MERGE (t:CanvasNode {id: $target_id})
            SET t.group_id = coalesce(t.group_id, $group_id)
            MERGE (s)-[e:CANVAS_EDGE {id: $edge_id}]->(t)
            ON CREATE SET e.created_at = datetime()
            SET e.label = $label,
                e.relation_type = $rel_type,
                e.group_id = $group_id,
                e.synced_from = 'frontmatter',
                e.active = true,
                e.derived_at = coalesce($derived_at, e.derived_at),
                e.source_mastery_at_derivation =
                    coalesce($source_mastery, e.source_mastery_at_derivation),
                e.confusion_at_derivation =
                    coalesce($confusion, e.confusion_at_derivation)
            REMOVE e.invalidated_at
            """,
            source_id=source_id,
            target_id=target_id,
            edge_id=edge_id,
            label=label,
            rel_type=rel_type,
            group_id=physical_gid,
            derived_at=str(rel.get("derived_at")) if rel.get("derived_at") else None,
            source_mastery=(
                float(rel["source_mastery_at_derivation"])
                if rel.get("source_mastery_at_derivation") is not None
                else None
            ),
            confusion=(str(rel.get("confusion"))[:300] if rel.get("confusion") else None),
        )
        return edge_id


_canvas_projection_sync: Optional[CanvasProjectionSync] = None


def get_canvas_projection_sync() -> CanvasProjectionSync:
    """Singleton accessor。"""
    global _canvas_projection_sync
    if _canvas_projection_sync is None:
        _canvas_projection_sync = CanvasProjectionSync()
    return _canvas_projection_sync
