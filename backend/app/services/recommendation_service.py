# Canvas Learning System - Recommendation Service
# Story 1.7: Concept-relation recommendation analysis (AC-1, AC-2)
"""
Two-layer recommendation engine:
  L1: bge-m3 text similarity (cosine > 0.6 threshold)
  L2: Neo4j 2-hop neighbor co-occurrence

Returns top-5 recommendations per canvas, filtered by dismissed pairs.

[Source: _bmad-output/implementation-artifacts/1-7-concept-relation-recommendation.md#Task 1]
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set

import structlog
from uuid import uuid4

from app.models.recommendation_models import (
    DismissedPair,
    Recommendation,
    RecommendationCandidate,
    RecommendationResponse,
)

logger = structlog.get_logger(__name__)

# Similarity threshold for L1 text matching
TEXT_SIMILARITY_THRESHOLD = 0.6
# Max recommendations to return
MAX_RECOMMENDATIONS = 5
# Default label candidates
DEFAULT_LABEL_CANDIDATES = [
    "相关概念",
    "前置知识",
    "应用关系",
    "对比关系",
    "包含关系",
]


class RecommendationService:
    """Generates concept-relation recommendations for a canvas board."""

    def __init__(self, neo4j_client: object):
        """
        Args:
            neo4j_client: Neo4jClient instance with run_query() method.
        """
        self.neo4j_client = neo4j_client

    async def generate_recommendations(
        self,
        canvas_id: str,
        dismissed_pairs: List[DismissedPair],
        group_id: Optional[str] = None,
    ) -> RecommendationResponse:
        """
        Generate concept-relation recommendations with 5s timeout.

        Args:
            canvas_id: The canvas board ID.
            dismissed_pairs: Node pairs to exclude from results.
            group_id: Vault group_id (logical ``vault:x`` or physical
                ``vault__x``). Falls back to the request-context group
                injected by ``resolve_vault_group_id`` when omitted.

        Returns:
            RecommendationResponse with up to 5 recommendations.
        """
        try:
            physical_group_id = self._resolve_physical_group_id(group_id)
            return await asyncio.wait_for(
                self._generate_internal(canvas_id, dismissed_pairs, physical_group_id),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Recommendation analysis timed out for canvas {canvas_id}")
            return RecommendationResponse(
                recommendations=list(),
                canvas_id=canvas_id,
            )
        except Exception as e:
            logger.error(f"Recommendation analysis failed: {e}")
            return RecommendationResponse(
                recommendations=list(),
                canvas_id=canvas_id,
            )

    @staticmethod
    def _resolve_physical_group_id(group_id: Optional[str]) -> str:
        """Resolve the physical (``vault__x``) group_id for Cypher binding.

        P0-SYNC-ISO-2026-08-17 R10: every Canvas-graph read must be scoped to
        one vault. Priority: explicit ``group_id`` arg > request ContextVar
        (``get_current_subject_id()`` — misnamed, it returns the group_id
        injected by the endpoint layer's ``resolve_vault_group_id``).
        Whatever the source, the value is passed through
        ``to_physical_group_id()`` because Neo4j stores the double-underscore
        physical form — binding the logical ``vault:x`` form would silently
        filter out everything.
        """
        from app.core.subject_config import get_current_subject_id
        from app.graphiti.group_id_compat import to_physical_group_id

        logical = group_id if group_id and group_id.strip() else get_current_subject_id()
        return to_physical_group_id(logical)

    async def _generate_internal(
        self,
        canvas_id: str,
        dismissed_pairs: List[DismissedPair],
        group_id: str,
    ) -> RecommendationResponse:
        """Internal implementation with full analysis pipeline.

        Args:
            group_id: PHYSICAL group_id (``vault__x``), already resolved by
                ``_resolve_physical_group_id`` — bound as-is in all Cypher.
        """

        # Quick exit: count nodes
        node_count = await self._count_nodes(canvas_id, group_id)
        if node_count < 5:
            return RecommendationResponse(
                recommendations=list(),
                canvas_id=canvas_id,
            )

        # Get unconnected nodes
        unconnected = await self._get_unconnected_nodes(canvas_id, group_id)
        if len(unconnected) < 2:
            return RecommendationResponse(
                recommendations=list(),
                canvas_id=canvas_id,
            )

        # Build dismissed set for fast lookup
        dismissed_set: Set[str] = set()
        for dp in dismissed_pairs:
            pair_key = self._make_pair_key(dp.node_id_a, dp.node_id_b)
            dismissed_set.add(pair_key)

        # L1: Text similarity analysis
        l1_candidates = await self._compute_text_similarity(unconnected)

        # L2: Graph pattern analysis
        unconnected_ids = [n["id"] for n in unconnected]
        l2_candidates = await self._detect_graph_patterns(canvas_id, unconnected_ids, group_id)

        # Merge and deduplicate
        merged = self._merge_candidates(l1_candidates, l2_candidates)

        # Filter dismissed pairs
        filtered = [c for c in merged if self._make_pair_key(c.source_node_id, c.target_node_id) not in dismissed_set]

        # Sort by confidence descending, take top-5
        filtered.sort(key=lambda c: c.confidence, reverse=True)
        top = filtered[:MAX_RECOMMENDATIONS]

        # Resolve node titles
        all_titles = await self._get_node_titles(canvas_id, group_id)

        # Determine suggested labels
        existing_labels = await self._get_existing_edge_labels(canvas_id, group_id)
        default_label = self._pick_label(existing_labels)

        recommendations = [
            Recommendation(
                id=uuid4().hex[:16],
                source_node_id=c.source_node_id,
                source_node_title=all_titles.get(c.source_node_id, "未命名"),
                target_node_id=c.target_node_id,
                target_node_title=all_titles.get(c.target_node_id, "未命名"),
                confidence=c.confidence,
                reason=c.reason,
                suggested_label=default_label,
            )
            for c in top
        ]

        return RecommendationResponse(
            recommendations=recommendations,
            canvas_id=canvas_id,
        )

    # ─── Neo4j queries ──────────────────────────────────────────────────────

    async def _count_nodes(self, canvas_id: str, group_id: str) -> int:
        """Count total CanvasNode entries for a canvas (vault-scoped)."""
        query = "MATCH (n:CanvasNode {canvasId: $canvas_id, group_id: $group_id}) RETURN count(n) AS cnt"
        records = await self.neo4j_client.run_query(query, canvas_id=canvas_id, group_id=group_id)
        if records:
            return records[0].get("cnt", 0)
        return 0

    async def _get_unconnected_nodes(self, canvas_id: str, group_id: str) -> List[Dict]:
        """Get nodes with no *live* CANVAS_EDGE connections (vault-scoped).

        P1-05c (Codex 三轮 F-02): 墓碑边 (invalidated_at) 不算连接 — 否则孤立
        节点因幽灵边被误判"已连接"而漏出推荐面。模式谓词无法带属性过滤,
        改 EXISTS 子查询。
        """
        query = """
        MATCH (n:CanvasNode {canvasId: $canvas_id, group_id: $group_id})
        WHERE NOT EXISTS {
            MATCH (n)-[e:CANVAS_EDGE]-()
            WHERE e.invalidated_at IS NULL
        }
        RETURN n.id AS id, n.title AS title, n.content AS content
        """
        return await self.neo4j_client.run_query(query, canvas_id=canvas_id, group_id=group_id)

    async def _detect_graph_patterns(
        self,
        canvas_id: str,
        unconnected_ids: List[str],
        group_id: str,
    ) -> List[RecommendationCandidate]:
        """Detect 2-hop neighbor co-occurrence patterns (vault-scoped)."""
        if len(unconnected_ids) < 2:
            return list()

        # shared.group_id filter: the intermediate node must live in the same
        # vault too — otherwise a cross-vault edge (data corruption) would let
        # another vault's node act as evidence for a recommendation.
        # P1-05c (Codex 三轮 F-02): 变长路径的每一段都必须是 live 边 — 墓碑边
        # 不得充当共邻证据; "已有连接"的排除同样只认 live 边。
        query = """
        MATCH (a:CanvasNode {canvasId: $canvas_id, group_id: $group_id})-[es1:CANVAS_EDGE*1..2]-(shared)-[es2:CANVAS_EDGE*1..2]-(b:CanvasNode {canvasId: $canvas_id, group_id: $group_id})
        WHERE a.id IN $ids AND b.id IN $ids
          AND a.id < b.id
          AND shared.group_id = $group_id
          AND all(e IN es1 WHERE e.invalidated_at IS NULL)
          AND all(e IN es2 WHERE e.invalidated_at IS NULL)
          AND NOT EXISTS {
              MATCH (a)-[live:CANVAS_EDGE]-(b)
              WHERE live.invalidated_at IS NULL
          }
        RETURN a.id AS source_id, b.id AS target_id, count(shared) AS shared_neighbors
        ORDER BY shared_neighbors DESC
        """
        candidates: List[RecommendationCandidate] = list()
        try:
            records = await self.neo4j_client.run_query(
                query,
                canvas_id=canvas_id,
                ids=unconnected_ids,
                group_id=group_id,
            )
            if records:
                for rec in records:
                    shared = rec["shared_neighbors"]
                    confidence = min(shared / 3.0, 1.0)
                    candidates.append(
                        RecommendationCandidate(
                            source_node_id=rec["source_id"],
                            target_node_id=rec["target_id"],
                            confidence=confidence,
                            source_type="graph_pattern",
                            reason=f"共同关联 {shared} 个概念",
                        )
                    )
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Graph pattern detection failed: {e}")

        return candidates

    async def _get_node_titles(self, canvas_id: str, group_id: str) -> Dict[str, str]:
        """Get all node titles for a canvas (vault-scoped)."""
        query = """
        MATCH (n:CanvasNode {canvasId: $canvas_id, group_id: $group_id})
        RETURN n.id AS id, n.title AS title
        """
        titles: Dict[str, str] = {}
        try:
            records = await self.neo4j_client.run_query(query, canvas_id=canvas_id, group_id=group_id)
            for rec in records:
                titles[rec["id"]] = rec.get("title") or "未命名"
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to fetch node titles: {e}")
        return titles

    async def _get_existing_edge_labels(self, canvas_id: str, group_id: str) -> List[str]:
        """Get all existing edge labels for label suggestion (vault-scoped)."""
        # Both endpoints carry group_id — an edge reaching into another vault
        # must never contribute label suggestions.
        # P1-05c (F-02): 墓碑边的 label 不再进建议池。
        query = """
        MATCH (:CanvasNode {canvasId: $canvas_id, group_id: $group_id})-[e:CANVAS_EDGE]-(:CanvasNode {group_id: $group_id})
        WHERE e.label IS NOT NULL AND e.label <> ''
          AND e.invalidated_at IS NULL
        RETURN e.label AS label, count(*) AS cnt
        ORDER BY cnt DESC
        LIMIT 5
        """
        labels: List[str] = list()
        try:
            records = await self.neo4j_client.run_query(query, canvas_id=canvas_id, group_id=group_id)
            for rec in records:
                labels.append(rec["label"])
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to fetch edge labels: {e}")
        return labels

    # ─── L1: Text similarity ────────────────────────────────────────────────

    async def _compute_text_similarity(
        self,
        nodes: List[Dict],
    ) -> List[RecommendationCandidate]:
        """
        Compute pairwise text similarity using bge-m3 embeddings.
        Falls back to simple keyword overlap if embedding service is unavailable.
        """
        candidates: List[RecommendationCandidate] = list()

        # Try embedding-based similarity via LiteLLM
        try:
            import litellm
            import numpy as np

            texts = list()
            for n in nodes:
                text = f"{n.get('title', '')} {n.get('content', '')}".strip()
                texts.append(text if text else "empty")

            # Get embeddings via bge-m3
            response = await litellm.aembedding(
                model="ollama/bge-m3",
                input=texts,
                timeout=10,
            )

            embeddings = [d["embedding"] for d in response.data]
            emb_array = np.array(embeddings)

            # Normalize for cosine similarity
            norms = np.linalg.norm(emb_array, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            normalized = emb_array / norms

            # Compute pairwise cosine similarity
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    sim = float(np.dot(normalized[i], normalized[j]))
                    if sim >= TEXT_SIMILARITY_THRESHOLD:
                        candidates.append(
                            RecommendationCandidate(
                                source_node_id=nodes[i]["id"],
                                target_node_id=nodes[j]["id"],
                                confidence=sim,
                                source_type="text_similarity",
                                reason="内容相似",
                            )
                        )

        except Exception as e:
            logger.warning(f"Embedding similarity failed, using keyword fallback: {e}")
            # Fallback: simple keyword overlap (Jaccard on words)
            candidates = self._keyword_similarity_fallback(nodes)

        return candidates

    def _keyword_similarity_fallback(
        self,
        nodes: List[Dict],
    ) -> List[RecommendationCandidate]:
        """Simple keyword-based similarity when embeddings are unavailable."""
        candidates: List[RecommendationCandidate] = list()
        node_words: List[set] = list()

        for n in nodes:
            text = f"{n.get('title', '')} {n.get('content', '')}".lower()
            words = set(text.split())
            node_words.append(words)

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                intersection = node_words[i] & node_words[j]
                union = node_words[i] | node_words[j]
                if len(union) == 0:
                    continue
                jaccard = len(intersection) / len(union)
                if jaccard >= TEXT_SIMILARITY_THRESHOLD:
                    candidates.append(
                        RecommendationCandidate(
                            source_node_id=nodes[i]["id"],
                            target_node_id=nodes[j]["id"],
                            confidence=jaccard,
                            source_type="text_similarity",
                            reason="内容相似",
                        )
                    )

        return candidates

    # ─── Utilities ──────────────────────────────────────────────────────────

    @staticmethod
    def _make_pair_key(id_a: str, id_b: str) -> str:
        """Create a sorted pair key for deduplication."""
        ids = sorted([id_a, id_b])
        return f"{ids[0]}_{ids[1]}"

    @staticmethod
    def _merge_candidates(
        l1: List[RecommendationCandidate],
        l2: List[RecommendationCandidate],
    ) -> List[RecommendationCandidate]:
        """Merge L1 and L2 candidates, keeping highest confidence per pair."""
        best: Dict[str, RecommendationCandidate] = {}

        for c in l1 + l2:
            key = RecommendationService._make_pair_key(c.source_node_id, c.target_node_id)
            existing = best.get(key)
            if existing is None or c.confidence > existing.confidence:
                best[key] = c

        return list(best.values())

    @staticmethod
    def _pick_label(existing_labels: List[str]) -> str:
        """Pick suggested label based on existing labels or default."""
        if existing_labels:
            return existing_labels[0]  # Most frequent existing label
        return DEFAULT_LABEL_CANDIDATES[0]  # "相关概念"
