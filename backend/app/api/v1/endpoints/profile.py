"""
Profile API Routes - Learning Profile Panel (Story 5.3)

REST endpoints for node-level learning profile data:
  GET /profile/{node_id}/summary     - Mastery summary + learning stats
  GET /profile/{node_id}/tips        - Tips annotations from Graphiti
  GET /profile/{node_id}/weaknesses  - Weakness patterns (positive framing)
  GET /profile/{node_id}/qa-highlights - Key QA pairs clustered by topic

All endpoints query real Neo4j/Graphiti data. Empty results when no data
exists yet are valid and handled by frontend empty-state UI.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.config import DEFAULT_GROUP_ID
from app.services.mastery_engine import get_mastery_engine
from app.services.mastery_store import get_mastery_store

logger = logging.getLogger(__name__)

profile_router = APIRouter()


def _get_engine():
    """Delegate to the service-level singleton."""
    return get_mastery_engine()


def _get_store():
    """Delegate to the service-level singleton."""
    return get_mastery_store()


def _get_neo4j_client():
    """Get raw Neo4j client for direct Cypher queries."""
    from app.clients.neo4j_client import get_neo4j_client

    return get_neo4j_client()


# ═══════════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class ProfileSummary(BaseModel):
    """Mastery summary for the learning profile header."""

    concept_id: str
    name: str
    mastery_level: int = Field(description="0-4 mastery level")
    mastery_label: str = Field(description="Human-readable mastery label")
    mastery_color: str = Field(description="Hex color for the mastery level")
    effective_proficiency: float = Field(description="Computed effective proficiency 0.0-1.0")
    prescriptive_message: str = Field(description="Supportive guidance message, not raw numbers")
    interaction_count: int = 0
    exam_count: int = 0
    last_exam_date: Optional[str] = None
    fsrs_due_date: Optional[str] = None
    freshness: str = "fresh"


class TipItem(BaseModel):
    """A single tip annotation."""

    tip_id: str
    content: str
    category: str = ""
    annotated_at: str
    context_messages: list[str] = Field(default_factory=list)
    source_canvas_id: Optional[str] = Field(None, description="Canvas board where this tip originated")
    source_node_id: Optional[str] = Field(None, description="Node ID where this tip originated")


class WeaknessItem(BaseModel):
    """A weakness direction (positive framing)."""

    direction: str = Field(description="What needs strengthening")
    frequency: int = Field(description="How many times this appeared")
    last_seen: Optional[str] = None
    related_exam_summaries: list[str] = Field(default_factory=list)
    source_canvas_id: Optional[str] = Field(None, description="Canvas board where this weakness was identified")
    source_node_id: Optional[str] = Field(None, description="Node ID where this weakness was identified")


class QAHighlight(BaseModel):
    """A single Q&A pair."""

    question: str
    answer: str
    extracted_at: str


class QAHighlightCluster(BaseModel):
    """Q&A pairs grouped by topic."""

    topic: str
    qa_pairs: list[QAHighlight]


# ═══════════════════════════════════════════════════════════════════════════════
# Prescriptive Message Generation (AC-1: supportive language, not raw numbers)
# ═══════════════════════════════════════════════════════════════════════════════

_PRESCRIPTIVE_MESSAGES = {
    0: "还没有开始学习，点击下方开始考察吧！",
    1: "基础还需要巩固，建议多做几次练习",
    2: "正在进步中，继续保持学习节奏",
    3: "掌握得不错，再巩固一下就能完全掌握了",
    4: "已经完全掌握，定期复习保持记忆",
}


def _get_prescriptive_message(level: int, freshness: str) -> str:
    """Generate supportive prescriptive message based on mastery level and freshness."""
    if freshness in ("due", "overdue") and level >= 2:
        return "距离上次复习有一段时间了，建议今天复习一下"
    return _PRESCRIPTIVE_MESSAGES.get(level, "继续学习吧！")


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@profile_router.get("/profile/{node_id}/summary", response_model=ProfileSummary)
async def get_profile_summary(
    node_id: str,
    group_id: str = Query(default=DEFAULT_GROUP_ID),
):
    """
    Get mastery summary and learning statistics for a node.

    Returns prescriptive (supportive) language rather than raw numeric scores.
    """
    engine = _get_engine()
    store = _get_store()

    concept = await store.get_concept(node_id, group_id)

    if concept is None:
        # Node has no mastery data yet - return default empty profile
        return ProfileSummary(
            concept_id=node_id,
            name=node_id,
            mastery_level=0,
            mastery_label="Not Assessed",
            mastery_color="#6c757d",
            effective_proficiency=0.0,
            prescriptive_message=_PRESCRIPTIVE_MESSAGES[0],
            interaction_count=0,
            exam_count=0,
            last_exam_date=None,
            fsrs_due_date=None,
            freshness="fresh",
        )

    resp = engine.concept_to_response(concept)
    level = resp["mastery_level"]
    freshness = resp["freshness"]

    # Count exam interactions (grades recorded = exam interactions)
    exam_count = concept.interaction_count

    return ProfileSummary(
        concept_id=concept.concept_id,
        name=concept.name,
        mastery_level=level,
        mastery_label=resp["mastery_label"],
        mastery_color=resp["mastery_color"],
        effective_proficiency=resp["effective_proficiency"],
        prescriptive_message=_get_prescriptive_message(level, freshness),
        interaction_count=concept.interaction_count,
        exam_count=exam_count,
        last_exam_date=concept.last_interaction_ts.isoformat() if concept.last_interaction_ts else None,
        fsrs_due_date=resp.get("fsrs_due_date"),
        freshness=freshness,
    )


@profile_router.get("/profile/{node_id}/tips")
async def get_profile_tips(
    node_id: str,
    group_id: str = Query(default=DEFAULT_GROUP_ID),
):
    """
    Get all tips annotations for a node from Graphiti.

    Tips are stored as EpisodicNode entities linked to the concept EntityNode
    with source_description containing 'tip' markers.
    """
    client = _get_neo4j_client()

    query = """
    MATCH (n:EntityNode)-[r]-(e:EpisodicNode)
    WHERE n.group_id = $group_id
      AND (n.mastery_concept_id = $node_id OR n.name = $node_id)
      AND (e.source_description CONTAINS 'tip' OR e.source_description CONTAINS 'Tip'
           OR r.name CONTAINS 'TIP' OR r.name CONTAINS 'tip')
    RETURN e.uuid AS tip_id,
           e.content AS content,
           COALESCE(e.source_description, '') AS category,
           COALESCE(toString(e.created_at), '') AS annotated_at,
           COALESCE(e.episode_body, '') AS context,
           COALESCE(e.source_canvas_id, '') AS source_canvas_id,
           COALESCE(e.source_node_id, n.mastery_concept_id, '') AS source_node_id
    ORDER BY e.created_at DESC
    """
    try:
        records = await client.run_query(
            query,
            group_id=group_id,
            node_id=node_id,
        )

        tips = []
        for record in records or []:
            data = record if isinstance(record, dict) else record.data()
            context_text = data.get("context", "")
            context_messages = [msg.strip() for msg in context_text.split("\n") if msg.strip()] if context_text else []

            tips.append(
                TipItem(
                    tip_id=data.get("tip_id", ""),
                    content=data.get("content", ""),
                    category=data.get("category", ""),
                    annotated_at=data.get("annotated_at", ""),
                    context_messages=context_messages[:5],  # Limit to 5 context messages
                    source_canvas_id=data.get("source_canvas_id") or None,
                    source_node_id=data.get("source_node_id") or None,
                ).model_dump()
            )

        return {"tips": tips, "total": len(tips)}
    except Exception as e:
        logger.warning(f"Failed to get tips for node {node_id}: {e}")
        return {"tips": [], "total": 0}


@profile_router.get("/profile/{node_id}/weaknesses")
async def get_profile_weaknesses(
    node_id: str,
    group_id: str = Query(default=DEFAULT_GROUP_ID),
):
    """
    Get weakness patterns for a node (positive framing: "areas to strengthen").

    Queries Graphiti for misconception and error entities linked to this concept,
    aggregates by pattern type and frequency.
    """
    client = _get_neo4j_client()

    query = """
    MATCH (n:EntityNode)-[r]-(e)
    WHERE n.group_id = $group_id
      AND (n.mastery_concept_id = $node_id OR n.name = $node_id)
      AND (r.name CONTAINS 'MISCONCEPTION' OR r.name CONTAINS 'misconception'
           OR r.name CONTAINS 'ERROR' OR r.name CONTAINS 'error'
           OR r.name CONTAINS 'WEAKNESS' OR r.name CONTAINS 'weakness'
           OR r.name CONTAINS 'PROBLEM_TRAP' OR r.name CONTAINS 'problem_trap'
           OR e.source_description CONTAINS 'misconception'
           OR e.source_description CONTAINS 'problem_trap')
    RETURN COALESCE(e.name, r.fact, e.content, '') AS direction,
           count(*) AS frequency,
           COALESCE(toString(max(e.created_at)), '') AS last_seen,
           COALESCE(head(collect(e.source_canvas_id)), '') AS source_canvas_id,
           COALESCE(head(collect(e.source_node_id)), n.mastery_concept_id, '') AS source_node_id
    ORDER BY frequency DESC
    LIMIT 20
    """
    try:
        records = await client.run_query(
            query,
            group_id=group_id,
            node_id=node_id,
        )

        weaknesses = []
        for record in records or []:
            data = record if isinstance(record, dict) else record.data()
            direction_text = data.get("direction", "")
            if not direction_text:
                continue

            weaknesses.append(
                WeaknessItem(
                    direction=direction_text,
                    frequency=data.get("frequency", 1),
                    last_seen=data.get("last_seen"),
                    related_exam_summaries=[],
                    source_canvas_id=data.get("source_canvas_id") or None,
                    source_node_id=data.get("source_node_id") or None,
                ).model_dump()
            )

        return {"weaknesses": weaknesses, "total": len(weaknesses)}
    except Exception as e:
        logger.warning(f"Failed to get weaknesses for node {node_id}: {e}")
        return {"weaknesses": [], "total": 0}


@profile_router.get("/profile/{node_id}/qa-highlights")
async def get_profile_qa_highlights(
    node_id: str,
    group_id: str = Query(default=DEFAULT_GROUP_ID),
):
    """
    Get key Q&A pairs for a node, clustered by topic.

    Queries Graphiti for episodic nodes linked to this concept that contain
    Q&A pair data (from Hot-Warm-Cold conversation archive pipeline).
    """
    client = _get_neo4j_client()

    query = """
    MATCH (n:EntityNode)-[r]-(e:EpisodicNode)
    WHERE n.group_id = $group_id
      AND (n.mastery_concept_id = $node_id OR n.name = $node_id)
      AND (e.source_description CONTAINS 'qa' OR e.source_description CONTAINS 'QA'
           OR e.source_description CONTAINS 'question' OR e.source_description CONTAINS 'highlight'
           OR r.name CONTAINS 'QA' OR r.name CONTAINS 'QUESTION')
    RETURN COALESCE(e.name, '') AS topic,
           COALESCE(e.content, e.episode_body, '') AS content,
           COALESCE(toString(e.created_at), '') AS extracted_at
    ORDER BY e.created_at DESC
    LIMIT 50
    """
    try:
        records = await client.run_query(
            query,
            group_id=group_id,
            node_id=node_id,
        )

        # Cluster by topic
        clusters: dict[str, list[QAHighlight]] = {}
        for record in records or []:
            data = record if isinstance(record, dict) else record.data()
            topic = data.get("topic", "") or "General"
            content = data.get("content", "")

            # Try to split content into Q and A parts
            if "?" in content or "？" in content:
                # Split on first question mark
                for separator in ["？", "?"]:
                    if separator in content:
                        parts = content.split(separator, 1)
                        question = parts[0].strip() + separator
                        answer = parts[1].strip() if len(parts) > 1 else ""
                        break
                else:
                    question = content
                    answer = ""
            else:
                question = content
                answer = ""

            if topic not in clusters:
                clusters[topic] = []

            clusters[topic].append(
                QAHighlight(
                    question=question,
                    answer=answer,
                    extracted_at=data.get("extracted_at", ""),
                )
            )

        cluster_list = [
            QAHighlightCluster(topic=topic, qa_pairs=pairs).model_dump() for topic, pairs in clusters.items()
        ]

        return {"clusters": cluster_list, "total": sum(len(c["qa_pairs"]) for c in cluster_list)}
    except Exception as e:
        logger.warning(f"Failed to get QA highlights for node {node_id}: {e}")
        return {"clusters": [], "total": 0}
