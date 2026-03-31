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
from typing import Dict, List, Set
from uuid import uuid4

from app.models.recommendation_models import (
    DismissedPair,
    Recommendation,
    RecommendationCandidate,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)

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
    ) -> RecommendationResponse:
        """
        Generate concept-relation recommendations with 5s timeout.

        Args:
            canvas_id: The canvas board ID.
            dismissed_pairs: Node pairs to exclude from results.

        Returns:
            RecommendationResponse with up to 5 recommendations.
        """
        try:
            return await asyncio.wait_for(
                self._generate_internal(canvas_id, dismissed_pairs),
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

    async def _generate_internal(
        self,
        canvas_id: str,
        dismissed_pairs: List[DismissedPair],
    ) -> RecommendationResponse:
        """Internal implementation with full analysis pipeline."""

        # Quick exit: count nodes
        node_count = await self._count_nodes(canvas_id)
        if node_count < 5:
            return RecommendationResponse(
                recommendations=list(),
                canvas_id=canvas_id,
            )

        # Get unconnected nodes
        unconnected = await self._get_unconnected_nodes(canvas_id)
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
        l2_candidates = await self._detect_graph_patterns(canvas_id, unconnected_ids)

        # Merge and deduplicate
        merged = self._merge_candidates(l1_candidates, l2_candidates)

        # Filter dismissed pairs
        filtered = [
            c
            for c in merged
            if self._make_pair_key(c.source_node_id, c.target_node_id)
            not in dismissed_set
        ]

        # Sort by confidence descending, take top-5
        filtered.sort(key=lambda c: c.confidence, reverse=True)
        top = filtered[:MAX_RECOMMENDATIONS]

        # Resolve node titles
        all_titles = await self._get_node_titles(canvas_id)

        # Determine suggested labels
        existing_labels = await self._get_existing_edge_labels(canvas_id)
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

    async def _count_nodes(self, canvas_id: str) -> int:
        """Count total CanvasNode entries for a canvas."""
        query = "MATCH (n:CanvasNode {canvasId: $canvas_id}) RETURN count(n) AS cnt"
        records = await self.neo4j_client.run_query(query, canvas_id=canvas_id)
        if records:
            return records[0].get("cnt", 0)
        return 0

    async def _get_unconnected_nodes(self, canvas_id: str) -> List[Dict]:
        """Get nodes with no CANVAS_EDGE connections."""
        query = """
        MATCH (n:CanvasNode {canvasId: $canvas_id})
        WHERE NOT (n)-[:CANVAS_EDGE]-() AND NOT (n)<-[:CANVAS_EDGE]-()
        RETURN n.id AS id, n.title AS title, n.content AS content
        """
        return await self.neo4j_client.run_query(query, canvas_id=canvas_id)

    async def _detect_graph_patterns(
        self,
        canvas_id: str,
        unconnected_ids: List[str],
    ) -> List[RecommendationCandidate]:
        """Detect 2-hop neighbor co-occurrence patterns."""
        if len(unconnected_ids) < 2:
            return list()

        query = """
        MATCH (a:CanvasNode {canvasId: $canvas_id})-[:CANVAS_EDGE*1..2]-(shared)-[:CANVAS_EDGE*1..2]-(b:CanvasNode {canvasId: $canvas_id})
        WHERE a.id IN $ids AND b.id IN $ids
          AND a.id < b.id
          AND NOT (a)-[:CANVAS_EDGE]-(b)
        RETURN a.id AS source_id, b.id AS target_id, count(shared) AS shared_neighbors
        ORDER BY shared_neighbors DESC
        """
        candidates: List[RecommendationCandidate] = list()
        try:
            records = await self.neo4j_client.run_query(
                query,
                canvas_id=canvas_id,
                ids=unconnected_ids,
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

    async def _get_node_titles(self, canvas_id: str) -> Dict[str, str]:
        """Get all node titles for a canvas."""
        query = """
        MATCH (n:CanvasNode {canvasId: $canvas_id})
        RETURN n.id AS id, n.title AS title
        """
        titles: Dict[str, str] = {}
        try:
            records = await self.neo4j_client.run_query(query, canvas_id=canvas_id)
            for rec in records:
                titles[rec["id"]] = rec.get("title") or "未命名"
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to fetch node titles: {e}")
        return titles

    async def _get_existing_edge_labels(self, canvas_id: str) -> List[str]:
        """Get all existing edge labels for label suggestion."""
        query = """
        MATCH (:CanvasNode {canvasId: $canvas_id})-[e:CANVAS_EDGE]-(:CanvasNode)
        WHERE e.label IS NOT NULL AND e.label <> ''
        RETURN e.label AS label, count(*) AS cnt
        ORDER BY cnt DESC
        LIMIT 5
        """
        labels: List[str] = list()
        try:
            records = await self.neo4j_client.run_query(query, canvas_id=canvas_id)
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
            key = RecommendationService._make_pair_key(
                c.source_node_id, c.target_node_id
            )
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
