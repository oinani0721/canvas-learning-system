"""
Mastery API Routes

REST endpoints for the BKT + FSRS hybrid mastery proficiency system.

Endpoints:
  GET  /mastery/batch           - Get all concepts' mastery state
  GET  /mastery/board/{board_id} - Get mastery data for all nodes on a board (Story 5.2)
  POST /mastery/{id}/grade      - Record an interaction grade (1-4)
  POST /mastery/{id}/override   - Set explicit override (Sidebar)
  POST /mastery/{id}/self-assess - Set implicit self-assessment (Canvas color)
  DELETE /mastery/{id}/override - Reset override to model value
  POST /mastery/{id}/calibration         - Record calibration data point (Story 5.5)
  GET  /mastery/{id}/calibration/summary - Get calibration summary (Story 5.5)
  GET  /mastery/calibration/dangerous    - List misconception nodes (Story 5.5)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import DEFAULT_GROUP_ID
from app.models.mastery_models import (
    CalibrationRequest,
)
from app.services.calibration_tracker import (
    get_calibration_summary,
    record_calibration,
)
from app.services.mastery_engine import get_mastery_engine
from app.services.mastery_store import get_mastery_store

logger = logging.getLogger(__name__)

mastery_router = APIRouter()


def _get_engine():
    """Delegate to the service-level singleton."""
    return get_mastery_engine()


def _get_store():
    """Delegate to the service-level singleton."""
    return get_mastery_store()


# Wave-5 Stage B (2026-05-12) — Multi-vault ContextVar 注入辅助。
# 67 endpoint 中此前零调用 set_current_subject_id → 67% endpoint 无隔离 →
# 5 vault 共存时跨 vault 数据泄漏。
# 此 helper 统一处理 vault_id → sanitize → build_vault_group_id → ContextVar 写入,
# 同时返回派生的 group_id 供 endpoint body 用作 store / service 调用参数,
# 保持向后兼容 (旧 group_id Query 仍读得到, 但优先 vault_id).
#
# 兼容策略:
#   - vault_id 提供 → 走新路径 (推荐, plugin 端 Phase B0 改完后所有调用走此路径)
#   - vault_id 空 + group_id 提供 → 走 deprecated 路径 (warning log, plugin 旧调用兼容)
#   - 两者都空 → DEFAULT_GROUP_ID fallback (背景任务 / 旧脚本)
def _resolve_vault_group_id(
    vault_id: Optional[str],
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
    legacy_group_id: Optional[str] = None,
) -> str:
    """Wave-5 Stage B — vault_id → ContextVar 注入 + group_id 派生.

    Args:
        vault_id: Plugin 端 inferVaultId(app.vault.getName()) 取的 raw vault name.
        subject_id: 可选 vault 内学科二级 (Stage A 透传).
        canvas_path: 可选 canvas 路径 (subject_id 为空时 fallback).
        legacy_group_id: 兼容旧 plugin 调用 (deprecated, 仅 vault_id 空时使用).

    Returns:
        Sanitized + canonical vault: 前缀 group_id (注入 ContextVar 后再返回).
    """
    from app.config import sanitize_vault_id
    from app.core.subject_config import (
        build_vault_group_id,
        canonical_group_id,
        set_current_subject_id,
    )

    if vault_id and vault_id.strip():
        sanitized = sanitize_vault_id(vault_id)
        derived = build_vault_group_id(
            sanitized,
            subject_id=subject_id,
            canvas_path=canvas_path,
        )
    elif legacy_group_id and legacy_group_id.strip():
        # Deprecated 路径 — 旧 plugin 调用兼容. 经 canonical_group_id 归一化避免
        # 'cs188' / 'canvas-dev' 等历史硬编码直进 Neo4j (Round-23 Patch 2).
        logger.warning(
            "Wave-5 Stage B: vault_id missing, falling back to deprecated "
            "group_id=%s. Update plugin caller to pass vault_id.",
            legacy_group_id,
        )
        derived = canonical_group_id(legacy_group_id)
    else:
        # 两者都空 — 极端 fallback (背景任务 / health check)
        logger.warning(
            "Wave-5 Stage B: both vault_id and group_id missing, "
            "falling back to DEFAULT_GROUP_ID=%s.",
            DEFAULT_GROUP_ID,
        )
        derived = DEFAULT_GROUP_ID

    set_current_subject_id(derived)
    return derived


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class GradeRequest(BaseModel):
    grade: int = Field(
        ...,
        ge=1,
        le=4,
        description="Student response grade (1=Forgot, 2=Struggled, 3=Correct, 4=Fluent)",
    )
    topic: str = Field(
        default="", description="Topic category (optional, for new concepts)"
    )
    name: str = Field(
        default="", description="Display name (optional, for new concepts)"
    )


class OverrideRequest(BaseModel):
    level: str = Field(
        ..., description="Override level: shaky/developing/proficient/mastered"
    )
    reason: str = Field(default="", description="Optional reason for override")


class SelfAssessRequest(BaseModel):
    color: str = Field(..., description="Canvas color code (1-6)")
    name: str = Field(
        default="",
        description="Display name from node text (optional, for concept identification)",
    )


class GraphitiSyncRequest(BaseModel):
    concept_name: str = Field(
        ..., description="Concept name from Graphiti episode (e.g. 'A* optimality')"
    )
    signal: str = Field(
        ...,
        description="Signal type: misconception, problem_trap, guided_thinking_correct",
    )
    severity: float = Field(
        default=0.15, ge=0.0, le=1.0, description="Adjustment magnitude"
    )
    topic: str = Field(default="", description="Topic category (optional)")


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@mastery_router.get("/mastery/batch")
async def get_batch_mastery(
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description=(
            "Multi-vault P0-2 (Wave-5 Stage B) — 推荐必填. 注入 ContextVar 防 5 vault 串库. "
            "Plugin 端 inferVaultId(app.vault.getName()). 空则 fallback 到 deprecated group_id."
        ),
    ),
    subject_id: Optional[str] = Query(
        default=None,
        description="可选 vault 内学科二级 namespace.",
    ),
    group_id: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id. 留兼容 plugin 尚未升级调用.",
    ),
):
    """
    Get all concepts' current mastery state (includes volatile computations).

    Returns concepts array with effective_proficiency, mastery_level, etc.
    Also returns topic_summary with aggregated proficiency per topic.
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    engine = _get_engine()
    store = _get_store()

    concepts = await store.get_all_concepts(resolved_group_id)

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

        config_path = (
            Path(__file__).parent.parent.parent.parent.parent / "mastery_config.json"
        )
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


@mastery_router.get("/mastery/board/{board_id:path}")
async def get_board_mastery(
    board_id: str,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 防跨 vault 泄漏.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
):
    """
    Get mastery data for all nodes on a specific canvas board (Story 5.2 Task 7).

    Returns an array of per-node mastery data used by the frontend to colorize
    canvas nodes. The response matches the frontend NodeMasteryData type:
      - node_id: concept identifier
      - effective_proficiency: combined BKT + FSRS proficiency (null if never examined)
      - has_interaction: whether the user has interacted with this node
      - has_exam_record: whether the node has been graded at least once
      - fsrs_next_review: ISO-8601 timestamp of next FSRS review (null if no card)

    The board_id is the canvas file path (e.g. "学习笔记.canvas").
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, canvas_path=board_id, legacy_group_id=group_id
    )
    engine = _get_engine()
    store = _get_store()

    concepts = await store.get_board_concepts(board_id, resolved_group_id)

    # Build per-node mastery data matching frontend NodeMasteryData type
    items = []
    for concept in concepts:
        # has_exam_record: node has been graded at least once (AutoSCORE)
        has_exam_record = concept.interaction_count > 0
        # has_interaction: user has engaged with this node (any activity)
        has_interaction = (
            has_exam_record
            or concept.override_value is not None
            or concept.self_assess_value is not None
        )

        # effective_proficiency: null when never examined (matches frontend expectation)
        eff_raw = engine.effective_proficiency(concept)
        eff_value = round(eff_raw, 3) if has_exam_record else None

        # Determine FSRS next review date from card data
        fsrs_next_review = None
        if engine.fsrs_manager and concept.fsrs_card_data:
            try:
                card = engine.fsrs_manager.deserialize_card(concept.fsrs_card_data)
                due = getattr(card, "due", None)
                if due is not None:
                    if isinstance(due, str):
                        fsrs_next_review = due
                    elif hasattr(due, "isoformat"):
                        fsrs_next_review = due.isoformat()
            except Exception:
                pass  # Graceful degradation: no due date if card parse fails

        items.append(
            {
                "node_id": concept.concept_id,
                "effective_proficiency": eff_value,
                "has_interaction": has_interaction,
                "has_exam_record": has_exam_record,
                "fsrs_next_review": fsrs_next_review,
            }
        )

    return {"data": items}


@mastery_router.post("/mastery/{concept_id}/grade")
async def record_grade(
    concept_id: str,
    req: GradeRequest,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 防跨 vault 泄漏.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
):
    """
    Record a student interaction grade (1-4) and update BKT + FSRS.

    Grade mapping:
      1 = Forgot (completely wrong)
      2 = Struggled (needed hints)
      3 = Correct (answered and explained)
      4 = Fluent (fluent explanation with connections)
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    engine = _get_engine()
    store = _get_store()

    concept = await store.get_or_create_concept(
        concept_id,
        topic=req.topic,
        name=req.name,
        group_id=resolved_group_id,
    )

    concept = engine.update_on_interaction(concept, req.grade)
    await store.save_concept(concept, resolved_group_id)
    await store.record_interaction_event(concept_id, req.grade, resolved_group_id)

    return engine.concept_to_response(concept)


@mastery_router.post("/mastery/{concept_id}/override")
async def set_override(
    concept_id: str,
    req: OverrideRequest,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
):
    """
    Set explicit mastery override from Sidebar (weight=0.8).

    Valid levels: shaky, developing, proficient, mastered
    Override decays exponentially with lambda from config.
    """
    valid_levels = {"shaky", "developing", "proficient", "mastered"}
    if req.level not in valid_levels:
        raise HTTPException(
            400, f"Invalid level '{req.level}'. Must be one of: {valid_levels}"
        )

    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    engine = _get_engine()
    store = _get_store()

    concept = await store.get_or_create_concept(concept_id, group_id=resolved_group_id)
    concept = engine.set_override(concept, req.level, req.reason)
    await store.save_concept(concept, resolved_group_id)
    await store.record_override_event(
        concept_id, req.level, req.reason, resolved_group_id
    )

    return engine.concept_to_response(concept)


@mastery_router.post("/mastery/{concept_id}/self-assess")
async def self_assess(
    concept_id: str,
    req: SelfAssessRequest,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
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
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    engine = _get_engine()
    store = _get_store()

    concept = await store.get_or_create_concept(
        concept_id,
        name=req.name or concept_id,
        group_id=resolved_group_id,
    )
    concept = engine.set_self_assess(concept, req.color)
    await store.save_concept(concept, resolved_group_id)
    await store.record_self_assess_event(concept_id, req.color, resolved_group_id)

    return engine.concept_to_response(concept)


@mastery_router.delete("/mastery/{concept_id}/override")
async def reset_override(
    concept_id: str,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
):
    """Reset override to model-computed value."""
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    engine = _get_engine()
    store = _get_store()

    concept = await store.get_concept(concept_id, resolved_group_id)
    if not concept:
        raise HTTPException(404, f"Concept '{concept_id}' not found")

    concept = engine.clear_override(concept)
    await store.save_concept(concept, resolved_group_id)

    return engine.concept_to_response(concept)


@mastery_router.post("/mastery/graphiti-sync")
async def knowledge_graph_sync(
    req: GraphitiSyncRequest,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
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
        raise HTTPException(
            400,
            f"Invalid signal type: {req.signal}. Must be: misconception, problem_trap, guided_thinking_correct",
        )

    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    engine = _get_engine()
    store = _get_store()

    # Try to find existing concept by name (fuzzy match)
    concept = await store.find_concept_by_name(req.concept_name, resolved_group_id)

    if not concept:
        # Create new concept with low initial mastery
        concept = await store.get_or_create_concept(
            concept_id=f"graphiti_{req.concept_name[:40]}",
            topic=req.topic or "Unknown",
            name=req.concept_name,
            group_id=resolved_group_id,
        )

    old_mastery = concept.p_mastery
    concept = engine.apply_external_signal(concept, req.signal, req.severity)
    await store.save_concept(concept, resolved_group_id)

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


# ═══════════════════════════════════════════════════════════════════════════════
# Story 5.5: Calibration API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@mastery_router.post("/mastery/{concept_id}/calibration")
async def record_calibration_endpoint(
    concept_id: str,
    req: CalibrationRequest,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
):
    """Record a calibration data point (self_confidence + actual_performance).

    Creates a CalibrationRecord with auto-classified Area9 quadrant.
    Persists to Neo4j for progressive calibration assessment.

    Quadrants:
      - Mastered: confident + correct
      - Misconception: confident + wrong (DANGEROUS)
      - Lucky: unsure + correct
      - Unlearned: unsure + wrong
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    store = _get_store()

    cal_record = record_calibration(
        node_id=concept_id,
        self_confidence=req.self_confidence,
        actual_performance=req.actual_performance,
        session_id=req.session_id,
    )

    await store.save_calibration_record(cal_record, resolved_group_id)

    return {
        "node_id": concept_id,
        "quadrant": cal_record.quadrant.value,
        "is_dangerous": cal_record.is_dangerous,
        "self_confidence": cal_record.self_confidence,
        "actual_performance": cal_record.actual_performance,
        "timestamp": cal_record.timestamp.isoformat(),
    }


@mastery_router.get("/mastery/{concept_id}/calibration/summary")
async def get_calibration_summary_endpoint(
    concept_id: str,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
):
    """Get calibration summary for a concept node.

    Three-stage progressive assessment:
      Stage 1 (< 10 records): Data collection, no assessment
      Stage 2 (10-20 records): Preliminary trends + signed_bias
      Stage 3 (20+ records): Full report + absolute_bias + rating
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    store = _get_store()

    records = await store.get_calibration_records(concept_id, resolved_group_id)
    summary = get_calibration_summary(records)

    return summary.model_dump()


@mastery_router.get("/mastery/calibration/dangerous")
async def get_dangerous_nodes_endpoint(
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
):
    """List all nodes with MISCONCEPTION quadrant records.

    Returns node IDs where user has high confidence but low performance
    (the most dangerous learning blind spots). Used for exam question
    prioritization.
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    store = _get_store()
    node_ids = await store.get_dangerous_nodes(resolved_group_id)

    return {
        "dangerous_nodes": node_ids,
        "count": len(node_ids),
    }
