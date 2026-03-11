"""
Mastery API Routes

REST endpoints for the BKT + FSRS hybrid mastery proficiency system.

Endpoints:
  GET  /mastery/batch           - Get all concepts' mastery state
  POST /mastery/{id}/grade      - Record an interaction grade (1-4)
  POST /mastery/{id}/override   - Set explicit override (Sidebar)
  POST /mastery/{id}/self-assess - Set implicit self-assessment (Canvas color)
  DELETE /mastery/{id}/override - Reset override to model value
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.mastery_engine import MasteryEngine, load_mastery_config
from app.services.mastery_store import MasteryStore

logger = logging.getLogger(__name__)

mastery_router = APIRouter()

# Singleton instances (initialized on first request)
_engine: MasteryEngine | None = None
_store: MasteryStore | None = None


def _get_engine() -> MasteryEngine:
    global _engine
    if _engine is None:
        _engine = MasteryEngine(load_mastery_config())
    return _engine


def _get_store() -> MasteryStore:
    global _store
    if _store is None:
        from app.clients.neo4j_client import get_neo4j_client
        client = get_neo4j_client()
        _store = MasteryStore(client)
    return _store


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════

class GradeRequest(BaseModel):
    grade: int = Field(..., ge=1, le=4, description="Student response grade (1=Forgot, 2=Struggled, 3=Correct, 4=Fluent)")
    topic: str = Field(default="", description="Topic category (optional, for new concepts)")
    name: str = Field(default="", description="Display name (optional, for new concepts)")


class OverrideRequest(BaseModel):
    level: str = Field(..., description="Override level: shaky/developing/proficient/mastered")
    reason: str = Field(default="", description="Optional reason for override")


class SelfAssessRequest(BaseModel):
    color: str = Field(..., description="Canvas color code (1-6)")
    name: str = Field(default="", description="Display name from node text (optional, for concept identification)")


class GraphitiSyncRequest(BaseModel):
    concept_name: str = Field(..., description="Concept name from Graphiti episode (e.g. 'A* optimality')")
    signal: str = Field(..., description="Signal type: misconception, problem_trap, guided_thinking_correct")
    severity: float = Field(default=0.15, ge=0.0, le=1.0, description="Adjustment magnitude")
    topic: str = Field(default="", description="Topic category (optional)")


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@mastery_router.get("/mastery/batch")
async def get_batch_mastery(group_id: str = Query(default="cs188")):
    """
    Get all concepts' current mastery state (includes volatile computations).

    Returns concepts array with effective_proficiency, mastery_level, etc.
    Also returns topic_summary with aggregated proficiency per topic.
    """
    engine = _get_engine()
    store = _get_store()

    concepts = await store.get_all_concepts(group_id)

    # Build response with volatile fields computed on the fly
    concept_responses = [engine.concept_to_response(c) for c in concepts]

    # Compute topic summary
    topic_map: dict[str, list[dict]] = {}
    for resp in concept_responses:
        topic = resp["topic"]
        if topic not in topic_map:
            topic_map[topic] = []
        topic_map[topic].append(resp)

    # Load exam weights from config
    exam_weights: dict = {}
    try:
        import json
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent.parent.parent / "mastery_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                exam_weights = json.load(f).get("topic_exam_weights", {})
    except Exception:
        pass

    topic_summary = {}
    for topic, items in topic_map.items():
        profs = [it["effective_proficiency"] for it in items]
        avg = sum(profs) / len(profs) if profs else 0.0
        topic_summary[topic] = {
            "avg_proficiency": round(avg, 3),
            "concept_count": len(items),
            "exam_weight": exam_weights.get(topic, 0),
        }

    return {
        "concepts": concept_responses,
        "topic_summary": topic_summary,
    }


@mastery_router.post("/mastery/{concept_id}/grade")
async def record_grade(
    concept_id: str,
    req: GradeRequest,
    group_id: str = Query(default="cs188"),
):
    """
    Record a student interaction grade (1-4) and update BKT + FSRS.

    Grade mapping:
      1 = Forgot (completely wrong)
      2 = Struggled (needed hints)
      3 = Correct (answered and explained)
      4 = Fluent (fluent explanation with connections)
    """
    engine = _get_engine()
    store = _get_store()

    concept = await store.get_or_create_concept(
        concept_id, topic=req.topic, name=req.name, group_id=group_id,
    )

    concept = engine.update_on_interaction(concept, req.grade)
    await store.save_concept(concept, group_id)
    await store.record_interaction_event(concept_id, req.grade, group_id)

    return engine.concept_to_response(concept)


@mastery_router.post("/mastery/{concept_id}/override")
async def set_override(
    concept_id: str,
    req: OverrideRequest,
    group_id: str = Query(default="cs188"),
):
    """
    Set explicit mastery override from Sidebar (weight=0.8).

    Valid levels: shaky, developing, proficient, mastered
    Override decays exponentially with lambda from config.
    """
    valid_levels = {"shaky", "developing", "proficient", "mastered"}
    if req.level not in valid_levels:
        raise HTTPException(400, f"Invalid level '{req.level}'. Must be one of: {valid_levels}")

    engine = _get_engine()
    store = _get_store()

    concept = await store.get_or_create_concept(concept_id, group_id=group_id)
    concept = engine.set_override(concept, req.level, req.reason)
    await store.save_concept(concept, group_id)
    await store.record_override_event(concept_id, req.level, req.reason, group_id)

    return engine.concept_to_response(concept)


@mastery_router.post("/mastery/{concept_id}/self-assess")
async def self_assess(
    concept_id: str,
    req: SelfAssessRequest,
    group_id: str = Query(default="cs188"),
):
    """
    Record implicit self-assessment from Canvas color change (weight=0.5).

    Color mapping:
      "1" (Red)    -> 0.20 (student thinks they don't know)
      "2" (Orange) -> 0.85 (student thinks they know)
      "3" (Yellow) -> 0.55 (student thinks partial)
      "4" (Green)  -> 0.85 (student thinks they know)
      "5" (Cyan)   -> 0.90 (student thinks mastered)
      "6" (Purple) -> 0.40 (student thinks weak)
    """
    engine = _get_engine()
    store = _get_store()

    concept = await store.get_or_create_concept(
        concept_id, name=req.name or concept_id, group_id=group_id,
    )
    concept = engine.set_self_assess(concept, req.color)
    await store.save_concept(concept, group_id)
    await store.record_self_assess_event(concept_id, req.color, group_id)

    return engine.concept_to_response(concept)


@mastery_router.delete("/mastery/{concept_id}/override")
async def reset_override(
    concept_id: str,
    group_id: str = Query(default="cs188"),
):
    """Reset override to model-computed value."""
    engine = _get_engine()
    store = _get_store()

    concept = await store.get_concept(concept_id, group_id)
    if not concept:
        raise HTTPException(404, f"Concept '{concept_id}' not found")

    concept = engine.clear_override(concept)
    await store.save_concept(concept, group_id)

    return engine.concept_to_response(concept)


@mastery_router.post("/mastery/graphiti-sync")
async def graphiti_sync(
    req: GraphitiSyncRequest,
    group_id: str = Query(default="cs188"),
):
    """
    Bridge: Graphiti misconception/ProblemTrap → mastery penalty.

    Called by Claude Code (via CLAUDE.md instruction) after recording a
    Misconception or ProblemTrap to the knowledge graph. Looks up the
    concept by name and applies a mastery adjustment.

    Signal types:
      - misconception: p_mastery -= severity (direct penalty)
      - problem_trap: p_mastery -= severity * 0.5 (softer penalty)
      - guided_thinking_correct: p_mastery += severity (small boost)
    """
    if req.signal not in ("misconception", "problem_trap", "guided_thinking_correct"):
        raise HTTPException(400, f"Invalid signal type: {req.signal}. Must be: misconception, problem_trap, guided_thinking_correct")

    engine = _get_engine()
    store = _get_store()

    # Try to find existing concept by name (fuzzy match)
    concept = await store.find_concept_by_name(req.concept_name, group_id)

    if not concept:
        # Create new concept with low initial mastery
        concept = await store.get_or_create_concept(
            concept_id=f"graphiti_{req.concept_name[:40]}",
            topic=req.topic or "Unknown",
            name=req.concept_name,
            group_id=group_id,
        )

    old_mastery = concept.p_mastery
    concept = engine.apply_external_signal(concept, req.signal, req.severity)
    await store.save_concept(concept, group_id)

    logger.info(
        f"Graphiti sync: {req.concept_name} ({req.signal}, severity={req.severity}) "
        f"p_mastery {old_mastery:.3f} -> {concept.p_mastery:.3f}"
    )

    return {
        "matched": True,
        "concept": engine.concept_to_response(concept),
        "adjustment": {
            "signal": req.signal,
            "severity": req.severity,
            "old_p_mastery": round(old_mastery, 3),
            "new_p_mastery": round(concept.p_mastery, 3),
        },
    }
