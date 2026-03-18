"""
EventBus Production Handlers - Story 5.7

Registers concrete event handlers that connect the mastery pipeline:
  SCORE_SUBMITTED -> mastery_engine (BKT/FSRS update) -> BKT_UPDATED/FSRS_UPDATED
  BKT_UPDATED -> mastery_store (persist to Neo4j) -> MASTERY_CHANGED
  MASTERY_CHANGED -> UI_MASTERY_PUSH (WebSocket broadcast)
  CALIBRATION_RECORDED -> calibration_tracker (record to Neo4j)
  MEMORY_WRITE_REQUESTED -> memory_service (write to Graphiti)

[Source: _bmad-output/implementation-artifacts/5-7-eventbus-triconnect.md]
"""

import logging
from typing import TYPE_CHECKING

from app.models.canvas_events import (
    LearningEvent,
    LearningEventType,
)

if TYPE_CHECKING:
    from app.services.event_bus import EventBus

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Handler: SCORE_SUBMITTED (Tier 1 CRITICAL)
# ═══════════════════════════════════════════════════════════════════════════════


async def handle_score_submitted(event: LearningEvent) -> None:
    """Process a score submission: update BKT and FSRS mastery models.

    On success, publishes BKT_UPDATED and FSRS_UPDATED events to continue
    the pipeline (persist to Neo4j, push to UI).

    Tier 1 (CRITICAL): awaited synchronously, failure propagates.
    """
    payload = event.payload
    node_id = payload.get("node_id")
    grade = payload.get("grade")
    session_id = payload.get("session_id")

    if not node_id or grade is None:
        logger.warning("handle_score_submitted: missing node_id or grade in payload")
        return

    from app.api.v1.endpoints.mastery import _get_engine, _get_store

    engine = _get_engine()
    store = _get_store()

    concept = await store.get_or_create_concept(
        concept_id=node_id,
        name=node_id,
    )

    updated = engine.update_on_interaction(concept, grade)
    await store.save_concept(updated)

    logger.info(f"handle_score_submitted: node={node_id} grade={grade} p_mastery={updated.p_mastery:.3f}")

    # Publish downstream events
    from app.services.event_bus import get_event_bus

    bus = get_event_bus()

    bkt_event = LearningEvent(
        event_type=LearningEventType.BKT_UPDATED,
        payload={
            "node_id": node_id,
            "session_id": session_id,
            "p_mastery": updated.p_mastery,
            "grade": grade,
        },
        source="mastery_engine",
    )
    await bus.publish(bkt_event)

    fsrs_event = LearningEvent(
        event_type=LearningEventType.FSRS_UPDATED,
        payload={
            "node_id": node_id,
            "session_id": session_id,
            "fsrs_stability": updated.fsrs_stability,
            "fsrs_difficulty": updated.fsrs_difficulty,
            "fsrs_state": updated.fsrs_state,
            "grade": grade,
        },
        source="mastery_engine",
    )
    await bus.publish(fsrs_event)


# ═══════════════════════════════════════════════════════════════════════════════
# Handler: BKT_UPDATED (Tier 2 IMPORTANT)
# ═══════════════════════════════════════════════════════════════════════════════


async def handle_bkt_updated(event: LearningEvent) -> None:
    """Persist BKT mastery state to Neo4j and publish MASTERY_CHANGED.

    Tier 2 (IMPORTANT): fire + retry + JSONL outbox on failure.
    """
    payload = event.payload
    node_id = payload.get("node_id")
    session_id = payload.get("session_id")

    if not node_id:
        logger.warning("handle_bkt_updated: missing node_id in payload")
        return

    from app.api.v1.endpoints.mastery import _get_engine, _get_store

    store = _get_store()
    engine = _get_engine()

    concept = await store.get_concept(node_id)
    if concept is None:
        logger.warning(f"handle_bkt_updated: concept {node_id} not found")
        return

    # Record interaction event on the EntityNode
    grade = payload.get("grade", 3)
    await store.record_interaction_event(
        concept_id=node_id,
        grade=grade,
        source="event_bus",
    )

    # Publish MASTERY_CHANGED for downstream consumers (UI push, etc.)
    from app.services.event_bus import get_event_bus

    bus = get_event_bus()
    mastery_event = LearningEvent(
        event_type=LearningEventType.MASTERY_CHANGED,
        payload={
            "node_id": node_id,
            "session_id": session_id,
            "p_mastery": concept.p_mastery,
            "effective_proficiency": engine.effective_proficiency(concept),
            "mastery_level": engine.mastery_level(concept),
            "mastery_label": engine.mastery_label(concept),
            "mastery_color": engine.mastery_color(concept),
        },
        source="mastery_store",
    )
    await bus.publish(mastery_event)

    logger.debug(f"handle_bkt_updated: persisted and published MASTERY_CHANGED for {node_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# Handler: MASTERY_CHANGED (Tier 2 IMPORTANT)
# ═══════════════════════════════════════════════════════════════════════════════


async def handle_mastery_changed(event: LearningEvent) -> None:
    """Publish UI_MASTERY_PUSH for WebSocket broadcast to connected clients.

    Tier 2 (IMPORTANT): fire + retry + JSONL outbox on failure.
    """
    payload = event.payload
    node_id = payload.get("node_id")

    if not node_id:
        logger.warning("handle_mastery_changed: missing node_id in payload")
        return

    from app.services.event_bus import get_event_bus

    bus = get_event_bus()
    ui_event = LearningEvent(
        event_type=LearningEventType.UI_MASTERY_PUSH,
        payload={
            "node_id": node_id,
            "session_id": payload.get("session_id"),
            "p_mastery": payload.get("p_mastery"),
            "effective_proficiency": payload.get("effective_proficiency"),
            "mastery_level": payload.get("mastery_level"),
            "mastery_label": payload.get("mastery_label"),
            "mastery_color": payload.get("mastery_color"),
        },
        source="mastery_pipeline",
    )
    await bus.publish(ui_event)

    logger.debug(f"handle_mastery_changed: published UI_MASTERY_PUSH for {node_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# Handler: CALIBRATION_RECORDED (Tier 2 IMPORTANT)
# ═══════════════════════════════════════════════════════════════════════════════


async def handle_calibration_recorded(event: LearningEvent) -> None:
    """Record a calibration entry to Neo4j via MasteryStore.

    Tier 2 (IMPORTANT): fire + retry + JSONL outbox on failure.
    """
    payload = event.payload
    node_id = payload.get("node_id")
    self_confidence = payload.get("self_confidence")
    actual_performance = payload.get("actual_performance")
    session_id = payload.get("session_id", "")

    if not node_id or self_confidence is None or actual_performance is None:
        logger.warning("handle_calibration_recorded: missing required fields in payload")
        return

    from app.services.calibration_tracker import record_calibration

    record = record_calibration(
        node_id=node_id,
        self_confidence=self_confidence,
        actual_performance=actual_performance,
        session_id=session_id,
    )

    from app.api.v1.endpoints.mastery import _get_store

    store = _get_store()
    await store.save_calibration_record(record)

    logger.info(
        f"handle_calibration_recorded: node={node_id} quadrant={record.quadrant.value} dangerous={record.is_dangerous}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Handler: MEMORY_WRITE_REQUESTED (Tier 2 IMPORTANT)
# ═══════════════════════════════════════════════════════════════════════════════


async def handle_memory_write_requested(event: LearningEvent) -> None:
    """Write a learning event to Graphiti via MemoryService.

    Tier 2 (IMPORTANT): fire + retry + JSONL outbox on failure.
    """
    payload = event.payload
    node_id = payload.get("node_id")
    concept = payload.get("concept", "")
    canvas_path = payload.get("canvas_path", "")
    user_id = payload.get("user_id", "default")
    agent_type = payload.get("agent_type", "system")
    score = payload.get("score")
    duration_seconds = payload.get("duration_seconds")

    if not node_id:
        logger.warning("handle_memory_write_requested: missing node_id")
        return

    from app.services.memory_service import get_memory_service

    memory_svc = await get_memory_service()
    await memory_svc.record_learning_event(
        user_id=user_id,
        canvas_path=canvas_path,
        node_id=node_id,
        concept=concept,
        agent_type=agent_type,
        score=score,
        duration_seconds=duration_seconds,
    )

    logger.info(f"handle_memory_write_requested: recorded learning event for node={node_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# Handler: FSRS_UPDATED (Tier 2 IMPORTANT)
# ═══════════════════════════════════════════════════════════════════════════════


async def handle_fsrs_updated(event: LearningEvent) -> None:
    """Write FSRS review schedule to Graphiti memory service.

    Records the FSRS stability/difficulty/state update as a learning event
    in Graphiti so the knowledge graph tracks review scheduling history.

    Tier 2 (IMPORTANT): fire + retry + JSONL outbox on failure.
    """
    payload = event.payload
    node_id = payload.get("node_id")
    session_id = payload.get("session_id", "")

    if not node_id:
        logger.warning("handle_fsrs_updated: missing node_id in payload")
        return

    from app.services.memory_service import get_memory_service

    memory_svc = await get_memory_service()
    await memory_svc.record_knowledge_entity(
        event_type="fsrs_review",
        content=(
            f"FSRS review update for node {node_id}: "
            f"stability={payload.get('fsrs_stability', 0):.2f} "
            f"difficulty={payload.get('fsrs_difficulty', 0):.2f} "
            f"state={payload.get('fsrs_state', 0)} "
            f"grade={payload.get('grade', 0)}"
        ),
        metadata={
            "node_id": node_id,
            "session_id": session_id,
            "fsrs_stability": payload.get("fsrs_stability"),
            "fsrs_difficulty": payload.get("fsrs_difficulty"),
            "fsrs_state": payload.get("fsrs_state"),
            "grade": payload.get("grade"),
        },
        group_id="default",
    )

    logger.debug(f"handle_fsrs_updated: recorded FSRS schedule for node={node_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# Handler: RAG_WEIGHT_ADJUST (Tier 3 BEST_EFFORT)
# ═══════════════════════════════════════════════════════════════════════════════


async def handle_rag_weight_adjust(event: LearningEvent) -> None:
    """Adjust RAG retrieval weights based on mastery level changes.

    Mastered nodes get deprioritized in retrieval; weak nodes get boosted.
    Currently logs the adjustment intent. Real LanceDB weight adjustment
    will be wired when the retrieval pipeline supports per-node boosting.

    Tier 3 (BEST_EFFORT): fire-and-forget, failure only logged.
    """
    payload = event.payload
    node_id = payload.get("node_id")
    mastery_level = payload.get("mastery_level", 0)

    if not node_id:
        return

    # Compute boost factor: low mastery = high boost, high mastery = low boost
    # Level 0 (not assessed) = 1.0, Level 1 (shaky) = 1.5, Level 4 (mastered) = 0.5
    boost_map = {0: 1.0, 1: 1.5, 2: 1.2, 3: 0.8, 4: 0.5}
    boost = boost_map.get(mastery_level, 1.0)

    logger.info(f"handle_rag_weight_adjust: node={node_id} mastery_level={mastery_level} boost_factor={boost}")


# ═══════════════════════════════════════════════════════════════════════════════
# Handler: UI_MASTERY_PUSH (Tier 3 BEST_EFFORT)
# ═══════════════════════════════════════════════════════════════════════════════


async def handle_ui_mastery_push(event: LearningEvent) -> None:
    """Push mastery update to connected WebSocket clients.

    Broadcasts the mastery state change to all connected frontends so
    canvas node colors update in real-time. Currently logs the broadcast
    intent. Real WebSocket broadcast will be wired when the WebSocket
    layer is available.

    Tier 3 (BEST_EFFORT): fire-and-forget, failure only logged.
    """
    payload = event.payload
    node_id = payload.get("node_id")

    if not node_id:
        return

    logger.info(
        f"handle_ui_mastery_push: node={node_id} "
        f"level={payload.get('mastery_level')} "
        f"color={payload.get('mastery_color')} "
        f"proficiency={payload.get('effective_proficiency')}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Registration
# ═══════════════════════════════════════════════════════════════════════════════


def register_all_handlers(event_bus: "EventBus") -> None:
    """Register all production event handlers on the EventBus.

    Called from main.py lifespan startup.
    """
    # Tier 1 CRITICAL: SCORE_SUBMITTED -> mastery engine update
    event_bus.subscribe(
        LearningEventType.SCORE_SUBMITTED,
        handle_score_submitted,
        subsystem="mastery_engine",
    )

    # Tier 2 IMPORTANT: BKT_UPDATED -> persist + publish MASTERY_CHANGED
    event_bus.subscribe(
        LearningEventType.BKT_UPDATED,
        handle_bkt_updated,
        subsystem="mastery_store",
    )

    # Tier 2 IMPORTANT: MASTERY_CHANGED -> UI_MASTERY_PUSH
    event_bus.subscribe(
        LearningEventType.MASTERY_CHANGED,
        handle_mastery_changed,
        subsystem="mastery_pipeline",
    )

    # Tier 2 IMPORTANT: CALIBRATION_RECORDED -> persist to Neo4j
    event_bus.subscribe(
        LearningEventType.CALIBRATION_RECORDED,
        handle_calibration_recorded,
        subsystem="calibration",
    )

    # Tier 2 IMPORTANT: MEMORY_WRITE_REQUESTED -> write to Graphiti
    event_bus.subscribe(
        LearningEventType.MEMORY_WRITE_REQUESTED,
        handle_memory_write_requested,
        subsystem="memory",
    )

    # Tier 2 IMPORTANT: FSRS_UPDATED -> write schedule to Graphiti
    event_bus.subscribe(
        LearningEventType.FSRS_UPDATED,
        handle_fsrs_updated,
        subsystem="memory",
    )

    # Tier 3 BEST_EFFORT: RAG_WEIGHT_ADJUST -> adjust retrieval weights
    event_bus.subscribe(
        LearningEventType.RAG_WEIGHT_ADJUST,
        handle_rag_weight_adjust,
    )

    # Tier 3 BEST_EFFORT: UI_MASTERY_PUSH -> WebSocket broadcast
    event_bus.subscribe(
        LearningEventType.UI_MASTERY_PUSH,
        handle_ui_mastery_push,
    )

    logger.info(
        "EventBus: registered 8 production handlers "
        "(SCORE_SUBMITTED, BKT_UPDATED, FSRS_UPDATED, MASTERY_CHANGED, "
        "CALIBRATION_RECORDED, MEMORY_WRITE_REQUESTED, "
        "RAG_WEIGHT_ADJUST, UI_MASTERY_PUSH)"
    )
