# Canvas Learning System - Exam Service Extension
# Stories 6.5-6.8: Examination Whiteboard business logic extensions
#
# This module extends ExamService with methods for:
#   Story 6.5: Recursive exam node sync
#   Story 6.6: Progressive hints + skip
#   Story 6.7: Cognitive load pause/resume
#   Story 6.8: Exam record persistence
#
# [Source: _bmad-output/implementation-artifacts/6-5 through 6-8]

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import DEFAULT_GROUP_ID
from app.models.exam_models import (
    COGNITIVE_LOAD_MESSAGES,
    COGNITIVE_LOAD_THRESHOLDS,
    DiscoveredNode,
    ExamCompleteRequest,
    ExamCompleteResponse,
    ExamNodeSyncRequest,
    ExamNodeSyncResponse,
    ExamRecordDetail,
    ExamRecordListResponse,
    ExamRecordSummary,
    ExamStatus,
    ExamStatusUpdateResponse,
    HintRequest,
    HintResponse,
    SkipRequest,
    SkipResponse,
)

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "exam"


# ======================================================================
# Story 6.5: Recursive Exam -- Node Sync
# ======================================================================


async def sync_node_to_source_canvas(
    self, request: ExamNodeSyncRequest, group_id: str = DEFAULT_GROUP_ID
) -> ExamNodeSyncResponse:
    """Sync a newly discovered node from exam whiteboard back to source canvas.

    Performs dual-write: Neo4j MERGE node + CREATE edge to source_node,
    then updates the exam session discovered_nodes list.

    [Source: Story 6.5 AC-2, AC-3]
    """
    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    node_query = """
    MERGE (n:CanvasNode {uuid: $node_id})
    SET n.text = $node_text,
        n.canvas_id = $source_canvas_id,
        n.source_exam_id = $exam_id,
        n.source_node_id = $source_node_id,
        n.group_id = $group_id,
        n.created_at = datetime($created_at),
        n.node_type = 'discovered'
    RETURN n.uuid AS id
    """
    try:
        await client.run_query(
            node_query,
            node_id=request.node_id,
            node_text=request.node_text,
            source_canvas_id=request.source_canvas_id,
            exam_id=request.exam_id,
            source_node_id=request.source_node_id,
            group_id=group_id,
            created_at=now_iso,
        )
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.error(f"[Story 6.5] Failed to sync node to Neo4j: {e}")
        return ExamNodeSyncResponse(
            node_id=request.node_id,
            synced_to_canvas=False,
            synced_to_neo4j=False,
            edge_created=False,
            status="error",
            message=f"Neo4j node write failed: {e}",
        )

    edge_query = """
    MATCH (src:CanvasNode {uuid: $source_node_id})
    MATCH (tgt:CanvasNode {uuid: $node_id})
    MERGE (src)-[r:EXAM_DISCOVERED {relation_type: $relation}]->(tgt)
    SET r.exam_id = $exam_id,
        r.group_id = $group_id,
        r.created_at = datetime($created_at)
    RETURN type(r) AS rel_type
    """
    edge_created = True
    try:
        await client.run_query(
            edge_query,
            source_node_id=request.source_node_id,
            node_id=request.node_id,
            relation=request.suggested_relation,
            exam_id=request.exam_id,
            group_id=group_id,
            created_at=now_iso,
        )
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.warning(f"[Story 6.5] Edge creation failed (non-fatal): {e}")
        edge_created = False

    # Story 6.5 AC-7: Track discovered node with full metadata (depth, timestamp, source)
    session = await self.get_session(request.exam_id)
    if session and request.node_id not in session.discovered_nodes:
        session.discovered_nodes.append(request.node_id)
        self._sessions[request.exam_id] = session

    # Persist DiscoveredNode record to Neo4j for Story 6.8 exam record
    try:
        # 6-5 M1 fix: Walk the discovery chain to compute true recursion depth.
        # Query Neo4j for the chain: source_node -> its source_node -> ... until root.
        depth = 1
        current_source = request.source_node_id
        seen: set[str] = {request.node_id}  # Guard against cycles
        while current_source and current_source not in seen:
            seen.add(current_source)
            # Check if current_source was itself a discovered node in this exam
            depth_query = """
            MATCH (d:EpisodicNode)
            WHERE d.source_description = 'discovered_node'
              AND d.node_id = $node_id
              AND d.source_exam_id = $exam_id
            RETURN d.source_node_id AS parent, d.depth AS stored_depth
            LIMIT 1
            """
            try:
                depth_records = await client.run_query(
                    depth_query, node_id=current_source, exam_id=request.exam_id
                )
                if depth_records:
                    data = (
                        depth_records[0]
                        if isinstance(depth_records[0], dict)
                        else depth_records[0].data()
                    )
                    stored_depth = data.get("stored_depth")
                    if stored_depth is not None:
                        depth = int(stored_depth) + 1
                        break
                    current_source = data.get("parent")
                else:
                    break  # source_node is an original exam node (depth=1)
            except (RuntimeError, ConnectionError, asyncio.TimeoutError):
                break  # On query failure, use depth computed so far

        # DiscoveredNode model validates the data; we persist directly to Neo4j
        DiscoveredNode(
            node_id=request.node_id,
            source_node_id=request.source_node_id,
            depth=depth,
            source_exam_id=request.exam_id,
        )

        discovered_query = """
        MERGE (d:EpisodicNode {uuid: $disc_id})
        SET d.source_description = 'discovered_node',
            d.node_id = $node_id,
            d.source_node_id = $source_node_id,
            d.depth = $depth,
            d.source_exam_id = $exam_id,
            d.group_id = $group_id,
            d.created_at = datetime($created_at)
        """
        await client.run_query(
            discovered_query,
            disc_id=f"disc_{request.exam_id}_{request.node_id}",
            node_id=request.node_id,
            source_node_id=request.source_node_id,
            depth=depth,
            exam_id=request.exam_id,
            group_id=group_id,
            created_at=now_iso,
        )
    except (
        RuntimeError,
        ConnectionError,
        asyncio.TimeoutError,
        ValueError,
        TypeError,
    ) as e:
        logger.debug(f"[Story 6.5] DiscoveredNode record save failed (non-fatal): {e}")

    logger.info(
        f"[Story 6.5] Node {request.node_id} synced to canvas {request.source_canvas_id} from exam {request.exam_id}"
    )

    return ExamNodeSyncResponse(
        node_id=request.node_id,
        synced_to_canvas=True,
        synced_to_neo4j=True,
        edge_created=edge_created,
        status="ok",
    )


# ======================================================================
# Story 6.6: Progressive Hints
# ======================================================================


async def generate_hint(self, request: HintRequest) -> HintResponse:
    """Generate a progressive hint using LLM based on hint level.

    Chain-of-Hints (2025): from vague direction to scaffolded guide.
    F12: Scaffolding gradual deprecation — restricts hint levels based on mastery.

    Fade policy (Vygotsky ZPD + Karpicke 2011 retrieval practice):
    - p_mastery < 0.50: All 4 levels available
    - p_mastery 0.50~0.65: Levels 1-3 (L4 disabled)
    - p_mastery 0.65~0.75: Levels 1-2 (L3-4 disabled)
    - p_mastery >= 0.75: All hints disabled

    [Source: Story 6.6 AC-1, AC-3, AC-6 + F12 Scaffolding Fade]
    """
    import litellm

    from app.config import settings

    # F12: Check mastery-based hint eligibility
    max_allowed_level = 4
    hint_available = True
    try:
        max_allowed_level = await _get_max_hint_level_by_mastery(request.node_id)
        hint_available = max_allowed_level > 0
    except (RuntimeError, AttributeError, ConnectionError) as e:
        logger.debug(f"[F12] Mastery check failed (allowing all hints): {e}")

    if not hint_available:
        return HintResponse(
            hint_text="",
            current_level=request.hint_level,
            remaining_levels=0,
            status="disabled",
            message="你已经掌握了这个知识点，不再需要提示了！继续独立思考吧。",
            hint_available=False,
            max_allowed_level=0,
        )

    level = max(1, min(max_allowed_level, request.hint_level))
    prompt_file = _PROMPTS_DIR / f"hint_level{level}.md"

    if not prompt_file.exists():
        logger.error(f"[Story 6.6] Hint prompt not found: {prompt_file}")
        return HintResponse(
            hint_text="",
            current_level=level,
            remaining_levels=4 - level,
            status="error",
            message=f"Hint prompt template not found for level {level}",
        )

    template = prompt_file.read_text(encoding="utf-8")

    # 6-6 M1 fix: Resolve real node title instead of using raw node_id as concept name
    concept_name = request.node_id  # Fallback to node_id
    try:
        from app.services.canvas_service import CanvasService

        canvas_svc = CanvasService(canvas_base_path=settings.canvas_base_path)
        _cname, node_data = await canvas_svc.find_node_across_canvases(request.node_id)
        if node_data:
            # Extract first line of text as concept name
            raw_text = node_data.get("text", "") or node_data.get("content", "")
            if raw_text:
                first_line = raw_text.strip().split("\n")[0].strip()
                # Strip markdown heading markers
                if first_line.startswith("#"):
                    first_line = first_line.lstrip("#").strip()
                if first_line:
                    concept_name = first_line[:100]
    except (
        OSError,
        json.JSONDecodeError,
        RuntimeError,
        ValueError,
        TypeError,
        AttributeError,
    ) as e:
        logger.debug(
            f"[Story 6.6] Failed to resolve node title for {request.node_id}: {e}"
        )

    system_prompt = template.replace("{{question}}", request.question_context)
    system_prompt = system_prompt.replace("{{concept}}", concept_name)
    system_prompt = system_prompt.replace("{{student_response}}", "")
    system_prompt = system_prompt.replace("{{previous_hint}}", "")
    system_prompt = system_prompt.replace("{{previous_hints}}", "")

    provider = settings.AI_PROVIDER
    model_name = settings.AI_MODEL_NAME
    if provider and not model_name.startswith(provider):
        litellm_model = f"{provider}/{model_name}"
    else:
        litellm_model = model_name

    try:
        response = await litellm.acompletion(
            model=litellm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Please generate a Level {level} hint.\n"
                        f"Question: {request.question_context}\n"
                        f"Concept: {request.node_id}"
                    ),
                },
            ],
            temperature=0.7,
            max_tokens=500,
        )
        hint_text = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[Story 6.6] Hint generation LLM call failed: {e}")
        hint_text = _get_fallback_hint(level)

    logger.info(
        f"[Story 6.6] Generated Level {level} hint for node {request.node_id} in exam {request.exam_id}"
    )

    return HintResponse(
        hint_text=hint_text,
        current_level=level,
        remaining_levels=max_allowed_level - level,
        status="ok",
        hint_available=True,
        max_allowed_level=max_allowed_level,
    )


async def _get_max_hint_level_by_mastery(node_id: str) -> int:
    """F12: Determine max allowed hint level based on node mastery.

    Scaffolding fade policy (Vygotsky ZPD + Karpicke 2011 retrieval practice):
    - p_mastery < 0.50: All 4 levels (full scaffolding)
    - p_mastery 0.50~0.65: Levels 1-3 (L4 scaffolded guide disabled)
    - p_mastery 0.65~0.75: Levels 1-2 (L3-4 disabled, only direction + keywords)
    - p_mastery >= 0.75: 0 (all hints disabled — independent practice)

    Reference: Khanmigo (Khan Academy) implements similar mastery-based hint fading.

    Returns:
        Max allowed hint level (0=disabled, 1-4=available up to that level).
        Defaults to 4 (all available) on any error (graceful degradation).
    """
    try:
        from app.clients.neo4j_client import get_neo4j_client
        from app.services.mastery_store import MasteryStore

        neo4j = get_neo4j_client()
        store = MasteryStore(neo4j)

        from app.config import DEFAULT_GROUP_ID

        concept = await store.get_concept(concept_id=node_id, group_id=DEFAULT_GROUP_ID)

        if concept is None or concept.p_mastery is None:
            return 4  # No mastery data → full hints available

        p = concept.p_mastery

        if p >= 0.75:
            return 0  # Mastered → no hints
        if p >= 0.65:
            return 2  # Direction + keywords only
        if p >= 0.50:
            return 3  # Up to partial framework
        return 4  # Full scaffolding

    except (RuntimeError, AttributeError, ConnectionError) as e:
        logger.debug(
            f"[F12] Mastery lookup failed for {node_id}, defaulting to full hints: {e}"
        )
        return 4


def _get_fallback_hint(level: int) -> str:
    """Generate a fallback hint when LLM is unavailable.

    These are real generic pedagogical prompts (not simulated) that
    work for any question, just less tailored than LLM output.
    """
    fallback_map = {
        1: "Try starting from the definition of this concept and think about how it connects to what you already know.",
        2: "Keyword hint: recall the core terms and related concept names involved.",
        3: (
            "Framework hint: list the key elements you know, "
            "think about their logical relationships, then organize your answer."
        ),
        4: (
            "Step-by-step guide:\n"
            "1. First, clarify the core definition of this concept\n"
            "2. Then list its key characteristics\n"
            "3. Consider how it differs from and connects to related concepts\n"
            "4. Based on this analysis, what conclusion can you draw?"
        ),
    }
    return fallback_map.get(level, fallback_map[1])


# ======================================================================
# Story 6.6: Skip Question
# ======================================================================


async def skip_question(self, request: SkipRequest) -> SkipResponse:
    """Skip the current question without BKT/FSRS penalty.

    Skip != wrong answer. p_mastery stays unchanged.
    FSRS: no rating event recorded.

    [Source: Story 6.6 AC-4]
    """
    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()

    read_query = """
    MATCH (e:EpisodicNode {uuid: $exam_id, source_description: 'exam_session'})
    RETURN COALESCE(e.skipped_nodes, '[]') AS existing
    """
    try:
        records = await client.run_query(read_query, exam_id=request.exam_id)
        existing_json = "[]"
        if records:
            data = records[0] if isinstance(records[0], dict) else records[0].data()
            existing_json = data.get("existing", "[]") or "[]"

        existing = _safe_json_to_list(existing_json)
        existing.append(
            {
                "node_id": request.node_id,
                "question_id": request.question_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        update_query = """
        MATCH (e:EpisodicNode {uuid: $exam_id, source_description: 'exam_session'})
        SET e.skipped_nodes = $skipped_json
        """
        await client.run_query(
            update_query,
            exam_id=request.exam_id,
            skipped_json=json.dumps(existing, ensure_ascii=False),
        )
    except (
        RuntimeError,
        ConnectionError,
        asyncio.TimeoutError,
        json.JSONDecodeError,
        TypeError,
    ) as e:
        logger.warning(f"[Story 6.6] Skip record save failed (non-fatal): {e}")

    logger.info(
        f"[Story 6.6] Skipped node {request.node_id} in exam {request.exam_id} -- no BKT/FSRS penalty"
    )

    return SkipResponse(
        skipped=True,
        bkt_penalized=False,
        fsrs_updated=False,
        status="ok",
    )


# ======================================================================
# Story 6.7: Cognitive Load -- Pause / Resume
# ======================================================================


async def pause_exam(self, exam_id: str) -> ExamStatusUpdateResponse:
    """Pause an active exam session. [Source: Story 6.7 AC-6]"""
    return await self._update_exam_lifecycle_status(exam_id, ExamStatus.PAUSED)


async def resume_exam(self, exam_id: str) -> ExamStatusUpdateResponse:
    """Resume a paused exam session. [Source: Story 6.7 AC-6]"""
    return await self._update_exam_lifecycle_status(exam_id, ExamStatus.IN_PROGRESS)


async def _update_exam_lifecycle_status(
    self, exam_id: str, new_status: ExamStatus
) -> ExamStatusUpdateResponse:
    """Update exam session status in both memory and Neo4j. [Story 6.7 AC-6]"""
    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    session = await self.get_session(exam_id)
    if session:
        session.status = new_status
        self._sessions[exam_id] = session

    query = """
    MATCH (e:EpisodicNode {uuid: $exam_id, source_description: 'exam_session'})
    SET e.exam_status = $status,
        e.updated_at = datetime($updated_at)
    RETURN e.uuid AS id
    """
    try:
        await client.run_query(
            query,
            exam_id=exam_id,
            status=new_status.value,
            updated_at=now_iso,
        )
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.error(f"[Story 6.7] Failed to update exam status: {e}")
        return ExamStatusUpdateResponse(
            exam_id=exam_id,
            status=new_status,
            updated_at=now_iso,
            message=f"Status update failed: {e}",
        )

    logger.info(f"[Story 6.7] Exam {exam_id} status -> {new_status.value}")
    return ExamStatusUpdateResponse(
        exam_id=exam_id,
        status=new_status,
        updated_at=now_iso,
    )


def get_cognitive_load_message(self, elapsed_minutes: int) -> Optional[str]:
    """Get the appropriate cognitive load reminder message.

    Returns the message for the highest crossed threshold, or None.
    [Source: Story 6.7 AC-1]
    """
    message = None
    for threshold in COGNITIVE_LOAD_THRESHOLDS:
        if elapsed_minutes >= threshold:
            message = COGNITIVE_LOAD_MESSAGES.get(threshold)
    return message


# ======================================================================
# Story 6.8: Exam Record Persistence
# ======================================================================


async def complete_exam(
    self, request: ExamCompleteRequest, group_id: str = DEFAULT_GROUP_ID
) -> ExamCompleteResponse:
    """Save a complete exam record permanently to Neo4j.

    Records are immutable. Stores scoring, conversation, discovery, skip data.
    [Source: Story 6.8 AC-1, AC-8]
    """
    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    mastery_trend = "stable"
    if request.mastery_changes:
        total_delta = sum(
            mc.proficiency_after - mc.proficiency_before
            for mc in request.mastery_changes
        )
        if total_delta > 0.01:
            mastery_trend = "up"
        elif total_delta < -0.01:
            mastery_trend = "down"

    score_history_json = json.dumps(
        [s.model_dump() for s in request.score_history], ensure_ascii=False
    )
    discovered_nodes_json = json.dumps(
        [d.model_dump(mode="json") for d in request.discovered_nodes],
        ensure_ascii=False,
    )
    skipped_nodes_json = json.dumps(
        [s.model_dump(mode="json") for s in request.skipped_nodes],
        ensure_ascii=False,
    )
    conversation_json = json.dumps(
        [c.model_dump() for c in request.conversation_log], ensure_ascii=False
    )
    mastery_changes_json = json.dumps(
        [m.model_dump() for m in request.mastery_changes], ensure_ascii=False
    )

    query = """
    MERGE (e:EpisodicNode {uuid: $exam_id})
    SET e.source_description = 'exam_record',
        e.group_id = $group_id,
        e.source_canvas_id = $source_canvas_id,
        e.source_canvas_name = $source_canvas_name,
        e.exam_mode = $exam_mode,
        e.exam_status = 'completed',
        e.start_time = $start_time,
        e.end_time = $end_time,
        e.active_duration_seconds = $active_duration_seconds,
        e.nodes_examined = $nodes_examined,
        e.discovered_nodes_count = $discovered_nodes_count,
        e.skipped_nodes_count = $skipped_nodes_count,
        e.mastery_trend = $mastery_trend,
        e.score_history = $score_history,
        e.discovered_nodes_data = $discovered_nodes,
        e.skipped_nodes_data = $skipped_nodes,
        e.conversation_log = $conversation_log,
        e.mastery_changes = $mastery_changes,
        e.created_at = datetime($created_at),
        e.completed_at = datetime($created_at)
    RETURN e.uuid AS id
    """

    try:
        records = await client.run_query(
            query,
            exam_id=request.exam_id,
            group_id=group_id,
            source_canvas_id=request.source_canvas_id,
            source_canvas_name=request.source_canvas_name,
            exam_mode=request.exam_mode,
            start_time=request.start_time,
            end_time=request.end_time,
            active_duration_seconds=request.active_duration_seconds,
            nodes_examined=len(request.score_history),
            discovered_nodes_count=len(request.discovered_nodes),
            skipped_nodes_count=len(request.skipped_nodes),
            mastery_trend=mastery_trend,
            score_history=score_history_json,
            discovered_nodes=discovered_nodes_json,
            skipped_nodes=skipped_nodes_json,
            conversation_log=conversation_json,
            mastery_changes=mastery_changes_json,
            created_at=now_iso,
        )

        record_id = request.exam_id
        if records:
            data = records[0] if isinstance(records[0], dict) else records[0].data()
            record_id = data.get("id", request.exam_id)

    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.error(f"[Story 6.8] Failed to save exam record: {e}")
        return ExamCompleteResponse(
            exam_id=request.exam_id,
            saved=False,
            status="error",
            message=f"Record save failed: {e}",
        )

    try:
        session_update = """
        MATCH (s:EpisodicNode {uuid: $exam_id, source_description: 'exam_session'})
        SET s.exam_status = 'completed',
            s.completed_at = datetime($completed_at),
            s.nodes_examined = $nodes_examined,
            s.mastery_change_summary = $mastery_trend
        """
        await client.run_query(
            session_update,
            exam_id=request.exam_id,
            completed_at=now_iso,
            nodes_examined=len(request.score_history),
            mastery_trend=mastery_trend,
        )
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.warning(f"[Story 6.8] Session status update failed (non-fatal): {e}")

    session = await self.get_session(request.exam_id)
    if session:
        session.status = ExamStatus.COMPLETED
        session.end_time = now_iso
        self._sessions[request.exam_id] = session

    logger.info(
        f"[Story 6.8] Exam record saved: {request.exam_id} "
        f"({len(request.score_history)} nodes, "
        f"{len(request.discovered_nodes)} discovered)"
    )

    return ExamCompleteResponse(
        exam_id=request.exam_id,
        saved=True,
        record_id=record_id,
        status="ok",
    )


async def get_exam_records(
    self,
    page: int = 1,
    limit: int = 20,
    group_id: str = DEFAULT_GROUP_ID,
) -> ExamRecordListResponse:
    """Get paginated list of all exam records. [Story 6.8 AC-7]"""
    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    skip_count = (page - 1) * limit

    count_query = """
    MATCH (e:EpisodicNode)
    WHERE e.group_id = $group_id AND e.source_description = 'exam_record'
    RETURN count(e) AS total
    """
    list_query = """
    MATCH (e:EpisodicNode)
    WHERE e.group_id = $group_id AND e.source_description = 'exam_record'
    RETURN e.uuid AS exam_id,
           COALESCE(e.source_canvas_id, '') AS source_canvas_id,
           COALESCE(e.source_canvas_name, '') AS source_canvas_name,
           COALESCE(e.exam_mode, 'comprehensive') AS exam_mode,
           COALESCE(toString(e.created_at), '') AS created_at,
           COALESCE(e.active_duration_seconds, 0) AS active_duration_seconds,
           COALESCE(e.nodes_examined, 0) AS nodes_examined,
           COALESCE(e.discovered_nodes_count, 0) AS discovered_nodes_count,
           COALESCE(e.skipped_nodes_count, 0) AS skipped_nodes_count,
           COALESCE(e.mastery_trend, 'stable') AS mastery_trend,
           COALESCE(e.exam_status, 'completed') AS status
    ORDER BY e.created_at DESC
    SKIP $skip_count LIMIT $limit
    """

    try:
        count_records = await client.run_query(count_query, group_id=group_id)
        total = 0
        if count_records:
            data = (
                count_records[0]
                if isinstance(count_records[0], dict)
                else count_records[0].data()
            )
            total = data.get("total", 0)

        records = await client.run_query(
            list_query, group_id=group_id, skip_count=skip_count, limit=limit
        )

        summaries: List[ExamRecordSummary] = list()
        for record in records or list():
            data = record if isinstance(record, dict) else record.data()
            summaries.append(ExamRecordSummary(**data))

        return ExamRecordListResponse(
            records=summaries, total=total, page=page, limit=limit
        )
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.warning(f"[Story 6.8] Failed to list exam records: {e}")
        return ExamRecordListResponse(records=list(), total=0, page=page, limit=limit)


async def get_exam_record(
    self, exam_id: str, group_id: str = DEFAULT_GROUP_ID
) -> Optional[ExamRecordDetail]:
    """Get a single exam record with full detail. [Story 6.8 AC-7]"""
    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    query = """
    MATCH (e:EpisodicNode {uuid: $exam_id})
    WHERE e.source_description = 'exam_record'
    RETURN e.uuid AS exam_id,
           COALESCE(e.source_canvas_id, '') AS source_canvas_id,
           COALESCE(e.source_canvas_name, '') AS source_canvas_name,
           COALESCE(e.exam_mode, 'comprehensive') AS exam_mode,
           COALESCE(toString(e.start_time), '') AS start_time,
           COALESCE(toString(e.end_time), '') AS end_time,
           COALESCE(e.active_duration_seconds, 0) AS active_duration_seconds,
           COALESCE(e.exam_status, 'completed') AS status,
           COALESCE(e.nodes_examined, 0) AS nodes_examined,
           e.score_history AS score_history_json,
           e.discovered_nodes_data AS discovered_nodes_json,
           e.skipped_nodes_data AS skipped_nodes_json,
           e.conversation_log AS conversation_log_json,
           e.mastery_changes AS mastery_changes_json
    """

    try:
        records = await client.run_query(query, exam_id=exam_id)
        if not records:
            return None

        data = records[0] if isinstance(records[0], dict) else records[0].data()

        return ExamRecordDetail(
            exam_id=data.get("exam_id", exam_id),
            source_canvas_id=data.get("source_canvas_id", ""),
            source_canvas_name=data.get("source_canvas_name", ""),
            exam_mode=data.get("exam_mode", "comprehensive"),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            active_duration_seconds=data.get("active_duration_seconds", 0),
            status=data.get("status", "completed"),
            nodes_examined=data.get("nodes_examined", 0),
            score_history=_safe_json_to_list(data.get("score_history_json")),
            discovered_nodes=_safe_json_to_list(data.get("discovered_nodes_json")),
            skipped_nodes=_safe_json_to_list(data.get("skipped_nodes_json")),
            conversation_log=_safe_json_to_list(data.get("conversation_log_json")),
            mastery_changes=_safe_json_to_list(data.get("mastery_changes_json")),
        )
    except (
        RuntimeError,
        ConnectionError,
        asyncio.TimeoutError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
        AttributeError,
    ) as e:
        logger.error(f"[Story 6.8] Failed to get exam record {exam_id}: {e}")
        return None


async def get_records_by_canvas(
    self, canvas_id: str, group_id: str = DEFAULT_GROUP_ID
) -> ExamRecordListResponse:
    """Get all exam records for a specific source canvas. [Story 6.8 AC-6, AC-7]"""
    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    query = """
    MATCH (e:EpisodicNode)
    WHERE e.group_id = $group_id
      AND e.source_description = 'exam_record'
      AND e.source_canvas_id = $canvas_id
    RETURN e.uuid AS exam_id,
           COALESCE(e.source_canvas_id, '') AS source_canvas_id,
           COALESCE(e.source_canvas_name, '') AS source_canvas_name,
           COALESCE(e.exam_mode, 'comprehensive') AS exam_mode,
           COALESCE(toString(e.created_at), '') AS created_at,
           COALESCE(e.active_duration_seconds, 0) AS active_duration_seconds,
           COALESCE(e.nodes_examined, 0) AS nodes_examined,
           COALESCE(e.discovered_nodes_count, 0) AS discovered_nodes_count,
           COALESCE(e.skipped_nodes_count, 0) AS skipped_nodes_count,
           COALESCE(e.mastery_trend, 'stable') AS mastery_trend,
           COALESCE(e.exam_status, 'completed') AS status
    ORDER BY e.created_at DESC
    """

    try:
        records = await client.run_query(query, group_id=group_id, canvas_id=canvas_id)

        summaries: List[ExamRecordSummary] = list()
        for record in records or list():
            data = record if isinstance(record, dict) else record.data()
            summaries.append(ExamRecordSummary(**data))

        return ExamRecordListResponse(
            records=summaries,
            total=len(summaries),
            page=1,
            limit=len(summaries),
        )
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.warning(f"[Story 6.8] Failed to get records for canvas {canvas_id}: {e}")
        return ExamRecordListResponse(records=list(), total=0)


# ======================================================================
# JSON parsing helper
# ======================================================================


def _safe_json_to_list(json_str: Optional[str]) -> List[Dict[str, Any]]:
    """Parse a JSON string into a list of dicts.

    Returns empty list on None/invalid input. This is correct behavior
    for fields that have not been populated yet (data naturally absent).
    """
    if not json_str:
        return list()
    try:
        result = json.loads(json_str)
        if isinstance(result, list):
            return result
        return list()
    except (json.JSONDecodeError, TypeError):
        return list()


# ======================================================================
# Attach methods to ExamService class
# ======================================================================


def attach_to_exam_service() -> None:
    """Attach Story 6.5-6.8 methods to ExamService class.

    Design rationale (6-5 H1):
    This module uses runtime method attachment (monkey-patching) rather than
    class inheritance or mixins. This is a deliberate architectural choice:

    1. **Separation of concerns**: Stories 6.5-6.8 are extension methods that
       would bloat ExamService (already ~480 lines) if placed inline.
    2. **Import cycle avoidance**: These methods depend on neo4j_client and
       litellm which would create circular imports if placed in exam_service.py.
    3. **Auto-attach on import**: The `import app.services.exam_service_ext`
       at the bottom of exam_service.py triggers attachment, ensuring methods
       are available to any code that imports ExamService.
    4. **Type safety**: All functions use `self` as first parameter and follow
       the ExamService method signature conventions.

    Alternative approaches considered:
    - Mixin class: rejected because Python MRO complexity adds no value here.
    - Subclass: rejected because the singleton pattern uses ExamService directly.
    - Protocol/ABC: unnecessary since this is internal extension, not a public API.
    """
    from app.services.exam_service import ExamService

    ExamService.sync_node_to_source_canvas = sync_node_to_source_canvas
    ExamService.generate_hint = generate_hint
    ExamService.skip_question = skip_question
    ExamService.pause_exam = pause_exam
    ExamService.resume_exam = resume_exam
    ExamService._update_exam_lifecycle_status = _update_exam_lifecycle_status
    ExamService.get_cognitive_load_message = get_cognitive_load_message
    ExamService.complete_exam = complete_exam
    ExamService.get_exam_records = get_exam_records
    ExamService.get_exam_record = get_exam_record
    ExamService.get_records_by_canvas = get_records_by_canvas


# Auto-attach on import
attach_to_exam_service()
