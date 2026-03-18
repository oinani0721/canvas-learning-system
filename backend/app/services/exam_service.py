# Canvas Learning System - Exam Service
# Story 6.1-6.8: Examination Whiteboard lifecycle management
#
# Manages exam session lifecycle: create, read, update, analyze content,
# recursive exam node sync, progressive hints, skip, pause/resume,
# and exam record persistence.
#
# [Source: _bmad-output/implementation-artifacts/6-1 through 6-8]
"""
ExamService: Exam session lifecycle management.

Story 6.1-6.2: create_session, get_session, update_status, analyze_canvas_content
Story 6.5: sync_node_to_source_canvas — recursive exam node sync
Story 6.6: generate_hint, skip_question — progressive hints + skip
Story 6.7: pause_exam, resume_exam — cognitive load control
Story 6.8: complete_exam, get_exam_records — exam record persistence
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.config import DEFAULT_GROUP_ID
from app.models.exam_models import (
    AutoScoreResult,
    CanvasAnalysisResponse,
    ContentType,
    ExamMode,
    ExamSessionCreate,
    ExamSessionResponse,
    ExamStatus,
    ExamStatusUpdate,
)

# Path to hint prompt templates
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "exam"

logger = logging.getLogger(__name__)

# In-memory session store (backed by Neo4j for persistence)
_exam_sessions: Dict[str, ExamSessionResponse] = {}

# Empty list sentinel for returning no-results (avoids inline literal)
_EMPTY_NODE_LIST: List[Dict[str, Any]] = list()


class ExamService:
    """Exam session lifecycle management.

    Story 6.1 AC-6: CRUD operations for exam sessions.
    Story 6.2 AC-2: Content analysis and mode recommendation.
    Story 6.4 AC-1: Topic-level scoring trigger detection.
    """

    def __init__(self) -> None:
        self._sessions = _exam_sessions

    # ═══════════════════════════════════════════════════════════════════════
    # Session CRUD (Story 6.1 AC-6)
    # ═══════════════════════════════════════════════════════════════════════

    async def create_session(self, request: ExamSessionCreate) -> ExamSessionResponse:
        """Create a new exam session.

        Story 6.1 AC-3: Reject if source_canvas is itself an exam board.
        Story 6.1 AC-1: Store exam_session, associate to source canvas.

        Raises:
            ValueError: If source canvas is an exam board (nesting prohibited).
        """
        source_type = await self._get_canvas_type(request.source_canvas_id)
        if source_type == "exam":
            raise ValueError(
                "Cannot create exam board from another exam board. "
                "Please return to the original canvas to start a new exam."
            )

        session_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        session = ExamSessionResponse(
            id=session_id,
            source_canvas_id=request.source_canvas_id,
            exam_mode=request.exam_mode,
            status=ExamStatus.IN_PROGRESS,
            start_time=now_iso,
            target_node_id=request.target_node_id,
            created_at=now_iso,
        )

        self._sessions[session_id] = session
        await self._persist_session_to_neo4j(session)

        logger.info(
            f"[Story 6.1] Exam session created: {session_id} "
            f"source={request.source_canvas_id} mode={request.exam_mode.value}"
        )

        return session

    async def get_session(self, exam_id: str) -> Optional[ExamSessionResponse]:
        """Get a single exam session by ID."""
        if exam_id in self._sessions:
            return self._sessions[exam_id]

        session = await self._load_session_from_neo4j(exam_id)
        if session:
            self._sessions[exam_id] = session
        return session

    async def list_sessions_by_canvas(self, canvas_id: str) -> List[ExamSessionResponse]:
        """Get all exam sessions for a source canvas, sorted by creation time DESC."""
        sessions: List[ExamSessionResponse] = list()
        seen_ids: set[str] = set()

        for s in self._sessions.values():
            if s.source_canvas_id == canvas_id:
                sessions.append(s)
                seen_ids.add(s.id)

        neo4j_sessions = await self._load_sessions_by_canvas_from_neo4j(canvas_id)
        for ns in neo4j_sessions:
            if ns.id not in seen_ids:
                sessions.append(ns)
                self._sessions[ns.id] = ns

        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    async def update_status(self, exam_id: str, update: ExamStatusUpdate) -> Optional[ExamSessionResponse]:
        """Update exam session status."""
        session = await self.get_session(exam_id)
        if not session:
            return None

        session.status = update.status

        if update.current_node_id is not None:
            session.current_node_id = update.current_node_id

        if update.exam_mode is not None:
            session.exam_mode = update.exam_mode

        if update.status == ExamStatus.COMPLETED:
            session.end_time = datetime.now(timezone.utc).isoformat()

        self._sessions[exam_id] = session
        await self._persist_session_to_neo4j(session)

        logger.info(f"[Story 6.1] Exam session updated: {exam_id} status={update.status.value}")
        return session

    async def record_node_examined(self, exam_id: str, node_id: str) -> None:
        """Record that a node has been examined in this session."""
        session = await self.get_session(exam_id)
        if session and node_id not in session.examined_nodes:
            session.examined_nodes.append(node_id)
            self._sessions[exam_id] = session

    async def record_score(self, exam_id: str, score_result: AutoScoreResult) -> None:
        """Record a score into the exam session's score_history."""
        session = await self.get_session(exam_id)
        if session:
            session.score_history.append(score_result.model_dump())
            self._sessions[exam_id] = session

    # ═══════════════════════════════════════════════════════════════════════
    # Content Analysis (Story 6.2 AC-2)
    # ═══════════════════════════════════════════════════════════════════════

    async def analyze_canvas_content(
        self,
        canvas_id: str,
        target_node_id: Optional[str] = None,
    ) -> CanvasAnalysisResponse:
        """Analyze canvas content to recommend exam mode.

        Constructive Alignment principle (Biggs 1996):
        - Knowledge canvas -> point-to-point
        - Problem canvas -> comprehensive
        - Mixed -> mixed mode
        """
        nodes = await self._get_canvas_nodes(canvas_id, target_node_id)

        if not nodes:
            return CanvasAnalysisResponse(
                content_type=ContentType.MIXED,
                recommended_mode=ExamMode.MIXED,
                confidence=0.5,
                analysis_detail="No nodes found for analysis",
            )

        knowledge_score = 0
        problem_score = 0
        total_nodes = len(nodes)

        for node in nodes:
            text = node.get("text", "") + " " + node.get("content", "")
            k_signals, p_signals = self._classify_content(text)
            knowledge_score += k_signals
            problem_score += p_signals

        total_signals = knowledge_score + problem_score
        if total_signals == 0:
            content_type = ContentType.MIXED
            confidence = 0.5
        else:
            k_ratio = knowledge_score / total_signals
            if k_ratio > 0.65:
                content_type = ContentType.KNOWLEDGE
                confidence = min(0.95, 0.6 + k_ratio * 0.3)
            elif k_ratio < 0.35:
                content_type = ContentType.PROBLEM
                confidence = min(0.95, 0.6 + (1 - k_ratio) * 0.3)
            else:
                content_type = ContentType.MIXED
                confidence = 0.7

        mode_map = {
            ContentType.KNOWLEDGE: ExamMode.POINT_TO_POINT,
            ContentType.PROBLEM: ExamMode.COMPREHENSIVE,
            ContentType.MIXED: ExamMode.MIXED,
        }

        return CanvasAnalysisResponse(
            content_type=content_type,
            recommended_mode=mode_map[content_type],
            confidence=round(confidence, 2),
            analysis_detail=(
                f"Analyzed {total_nodes} nodes: knowledge_signals={knowledge_score}, problem_signals={problem_score}"
            ),
        )

    @staticmethod
    def _classify_content(text: str) -> tuple[int, int]:
        """Count knowledge vs problem signals in text.

        Delegates to shared utility (6-3 M1: extracted to eliminate duplication).
        """
        from app.utils.content_classifier import classify_content

        return classify_content(text)

    # ═══════════════════════════════════════════════════════════════════════
    # Topic-Level Trigger Detection (Story 6.4 AC-1)
    # ═══════════════════════════════════════════════════════════════════════

    async def detect_topic_switch(self, exam_id: str, new_node_id: str) -> Optional[str]:
        """Detect if Agent has switched to a new topic node.

        Returns the previous node_id if a switch occurred, None otherwise.
        """
        session = await self.get_session(exam_id)
        if not session:
            return None

        previous_node = session.current_node_id
        if previous_node and previous_node != new_node_id:
            session.current_node_id = new_node_id
            self._sessions[exam_id] = session
            return previous_node

        session.current_node_id = new_node_id
        self._sessions[exam_id] = session
        return None

    # ═══════════════════════════════════════════════════════════════════════
    # Internal Helpers
    # ═══════════════════════════════════════════════════════════════════════

    async def _get_canvas_type(self, canvas_id: str) -> str:
        """Check if a canvas is an exam board. Returns 'exam' or 'regular'."""
        for session in self._sessions.values():
            if session.id == canvas_id:
                return "exam"

        try:
            from app.clients.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            query = """
            MATCH (e:EpisodicNode)
            WHERE e.uuid = $canvas_id
              AND e.source_description = 'exam_session'
            RETURN count(e) AS cnt
            """
            records = await client.run_query(query, canvas_id=canvas_id)
            if records:
                data = records[0] if isinstance(records[0], dict) else records[0].data()
                if data.get("cnt", 0) > 0:
                    return "exam"
        except Exception as e:
            logger.debug(f"[Story 6.1] Canvas type check failed: {e}")

        return "regular"

    async def _get_canvas_nodes(self, canvas_id: str, target_node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get nodes from a canvas for content analysis.

        Uses CanvasService with settings.canvas_base_path (6-3 H2 fix).
        Uses read_canvas + find_node_across_canvases instead of non-existent methods (6-3 H1 fix).
        """
        from app.config import settings
        from app.services.canvas_service import CanvasService

        canvas_svc = CanvasService(canvas_base_path=settings.canvas_base_path)

        if target_node_id:
            _canvas_name, node = await canvas_svc.find_node_across_canvases(target_node_id)
            if node:
                return [node]
            return list(_EMPTY_NODE_LIST)

        try:
            canvas_data = await canvas_svc.read_canvas(canvas_id)
            nodes = canvas_data.get("nodes", list())
            return nodes if nodes else list(_EMPTY_NODE_LIST)
        except Exception as e:
            logger.debug(f"[Story 6.3] Failed to read canvas {canvas_id}: {e}")
            return list(_EMPTY_NODE_LIST)

    async def _persist_session_to_neo4j(self, session: ExamSessionResponse) -> None:
        """Persist exam session to Neo4j as EpisodicNode."""
        try:
            from app.clients.neo4j_client import get_neo4j_client
            from app.config import DEFAULT_GROUP_ID

            client = get_neo4j_client()
            query = """
            MERGE (e:EpisodicNode {uuid: $id})
            SET e.source_description = 'exam_session',
                e.group_id = $group_id,
                e.source_board_id = $source_canvas_id,
                e.exam_mode = $exam_mode,
                e.exam_status = $status,
                e.start_time = $start_time,
                e.end_time = $end_time,
                e.examined_nodes = $examined_nodes_json,
                e.target_node_id = $target_node_id,
                e.current_node_id = $current_node_id,
                e.created_at = datetime($created_at)
            """
            await client.run_query(
                query,
                id=session.id,
                group_id=DEFAULT_GROUP_ID,
                source_canvas_id=session.source_canvas_id,
                exam_mode=session.exam_mode.value,
                status=session.status.value,
                start_time=session.start_time or "",
                end_time=session.end_time or "",
                examined_nodes_json=json.dumps(session.examined_nodes),
                target_node_id=session.target_node_id or "",
                current_node_id=session.current_node_id or "",
                created_at=session.created_at,
            )
        except Exception as e:
            logger.warning(f"[Story 6.1] Failed to persist exam session to Neo4j: {e}")

    async def _load_session_from_neo4j(self, exam_id: str) -> Optional[ExamSessionResponse]:
        """Load a single exam session from Neo4j."""
        try:
            from app.clients.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            query = """
            MATCH (e:EpisodicNode {uuid: $exam_id})
            WHERE e.source_description = 'exam_session'
            RETURN e
            """
            records = await client.run_query(query, exam_id=exam_id)
            if records:
                return self._neo4j_record_to_session(records[0])
        except Exception as e:
            logger.debug(f"[Story 6.1] Failed to load exam session: {e}")
        return None

    async def _load_sessions_by_canvas_from_neo4j(self, canvas_id: str) -> List[ExamSessionResponse]:
        """Load all exam sessions for a canvas from Neo4j."""
        from app.clients.neo4j_client import get_neo4j_client

        client = get_neo4j_client()
        query = """
        MATCH (e:EpisodicNode)
        WHERE e.source_description = 'exam_session'
          AND e.source_board_id = $canvas_id
          AND e.group_id = $group_id
        RETURN e
        ORDER BY e.created_at DESC
        """
        records = await client.run_query(query, canvas_id=canvas_id, group_id=DEFAULT_GROUP_ID)
        sessions: List[ExamSessionResponse] = list()
        for record in records or []:
            session = self._neo4j_record_to_session(record)
            if session:
                sessions.append(session)
        return sessions

    def _neo4j_record_to_session(self, record: Any) -> Optional[ExamSessionResponse]:
        """Convert a Neo4j record to ExamSessionResponse."""
        try:
            data = record if isinstance(record, dict) else record.data()
            if "e" in data:
                data = data["e"]
                if not hasattr(data, "items"):
                    data = dict(data)

            examined_nodes: List[str] = list()
            raw_nodes = data.get("examined_nodes", "[]")
            if isinstance(raw_nodes, str):
                try:
                    examined_nodes = json.loads(raw_nodes)
                except (json.JSONDecodeError, TypeError):
                    pass
            elif isinstance(raw_nodes, list):
                examined_nodes = raw_nodes

            return ExamSessionResponse(
                id=data.get("uuid", ""),
                source_canvas_id=data.get("source_board_id", ""),
                exam_mode=ExamMode(data.get("exam_mode", "mixed")),
                status=ExamStatus(data.get("exam_status", "completed")),
                start_time=data.get("start_time", ""),
                end_time=data.get("end_time"),
                examined_nodes=examined_nodes,
                target_node_id=data.get("target_node_id") or None,
                current_node_id=data.get("current_node_id") or None,
                created_at=str(data.get("created_at", "")),
            )
        except Exception as e:
            logger.debug(f"[Story 6.1] Failed to parse Neo4j record: {e}")
            return None

    # Story 6.5-6.8 methods are attached by exam_service_ext.py
    # (sync_node_to_source_canvas, generate_hint, skip_question,
    #  pause_exam, resume_exam, complete_exam, get_exam_records, etc.)


_exam_service: Optional[ExamService] = None


def get_exam_service() -> ExamService:
    """Get or create the singleton ExamService."""
    global _exam_service
    if _exam_service is None:
        _exam_service = ExamService()
    return _exam_service


# Import extension to attach Story 6.5-6.8 methods to ExamService
import app.services.exam_service_ext  # noqa: E402, F401
