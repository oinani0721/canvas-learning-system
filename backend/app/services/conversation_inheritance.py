"""
Conversation Inheritance Service — F9 Edge-based context inheritance.

PRD: "Edge 标签语义检索 + LLM 摘要的分层继承方案"
Architecture: Fills Tier 2 (adjacent node summaries) of the three-tier context model.

When a user opens a conversation on node B which is connected to node A via an Edge,
this service fetches A's conversation summary (from ConversationDistiller output) and
the Edge label (relationship description), assembling inherited context for injection
into B's system prompt.

Callers:
- learning_context_service.get_node_context() — integrates inherited context into Tier 2
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

INHERITANCE_CHAR_BUDGET = 800
MAX_INHERITED_NEIGHBORS = 2


@dataclass
class InheritedNodeContext:
    """Context inherited from a connected neighbor node via Edge."""

    neighbor_name: str
    edge_label: str
    conversation_summary: str
    key_insights: list[str] = field(default_factory=list)


async def get_inherited_context(
    node_id: str,
    group_id: Optional[str] = None,
) -> list[InheritedNodeContext]:
    """Query Edge-connected neighbors and fetch their conversation summaries.

    Architecture ref: Tier 2 摘要注入 (adjacent node summaries).
    PRD ref: "Edge 标签语义检索 + LLM 摘要" layered inheritance.

    Args:
        node_id: The current node whose conversation needs inherited context.
        group_id: Subject isolation namespace.

    Returns:
        List of InheritedNodeContext for up to MAX_INHERITED_NEIGHBORS neighbors.
        Returns empty when no neighbors have conversation history (graceful degradation).
    """
    if group_id is None:
        from app.config import DEFAULT_GROUP_ID

        group_id = DEFAULT_GROUP_ID

    neighbor_records = await _fetch_neighbor_records_for_inheritance(node_id)

    if not neighbor_records:
        return list()

    results: list[InheritedNodeContext] = list()
    total_chars = 0

    for rec in neighbor_records[:MAX_INHERITED_NEIGHBORS]:
        neighbor_name = rec.get("name", "")
        edge_label = rec.get("reason") or rec.get("label") or ""
        neighbor_node_id = rec.get("node_id") or neighbor_name

        if not neighbor_name:
            continue

        summary, insights = await _fetch_distillation_summary(neighbor_node_id, group_id)

        if not summary:
            continue

        entry_chars = len(neighbor_name) + len(edge_label) + len(summary) + sum(len(i) for i in insights)
        if total_chars + entry_chars > INHERITANCE_CHAR_BUDGET:
            break

        total_chars += entry_chars
        results.append(
            InheritedNodeContext(
                neighbor_name=neighbor_name,
                edge_label=edge_label,
                conversation_summary=summary,
                key_insights=insights[:3],
            )
        )

    return results


async def _fetch_neighbor_records_for_inheritance(node_id: str) -> list[dict]:
    """Fetch 1-hop neighbor records from Neo4j for inheritance.

    Same Neo4j query pattern as learning_context_service._fetch_neighbor_records().
    Graceful degradation: returns empty on Neo4j failure (non-blocking).
    """
    try:
        from app.clients.neo4j_client import get_neo4j_client

        neo4j = get_neo4j_client()
        records = await neo4j.run_query(
            """
            MATCH (n:EntityNode)-[r]-(neighbor:EntityNode)
            WHERE n.name = $node_id OR n.mastery_concept_id = $node_id
            RETURN DISTINCT
                neighbor.name AS name,
                neighbor.mastery_concept_id AS node_id,
                r.label AS label,
                r.reason AS reason
            LIMIT $limit
            """,
            node_id=node_id,
            limit=MAX_INHERITED_NEIGHBORS * 2,
        )
        if records:
            return [dict(r) for r in records]
        return list()
    except Exception as e:
        logger.warning("Failed to fetch neighbors for inheritance (node=%s): %s", node_id, e)
        return list()


async def _fetch_distillation_summary(
    node_id: str,
    group_id: str,
) -> tuple[str, list[str]]:
    """Fetch the most recent conversation distillation summary for a node.

    Searches MemoryService for episodes with episode_type="conversation_distillation"
    matching the given node_id.

    Returns:
        Tuple of (summary_text, key_insights_list). Empty on no data (graceful degradation).
    """
    try:
        from app.services.memory_service import MemoryService

        memory = MemoryService()
        episodes = await memory.search_memories(
            query=f"conversation_distillation {node_id}",
            group_id=group_id,
            max_results=1,
        )

        if not episodes:
            return "", list()

        latest = episodes[0]
        content = latest.get("content", "")

        summary = ""
        insights: list[str] = list()

        if isinstance(content, str) and content:
            summary = content[:400] if len(content) > 400 else content

        metadata = latest.get("metadata", {})
        if isinstance(metadata, dict):
            if metadata.get("summary"):
                summary = metadata["summary"]
            tips_data = metadata.get("tips")
            if tips_data:
                insights = [t.get("content", "") for t in tips_data[:3] if isinstance(t, dict)]

        return summary, insights

    except Exception as e:
        logger.warning("Failed to fetch distillation for node %s: %s", node_id, e)
        return "", list()
