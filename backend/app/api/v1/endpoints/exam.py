# Canvas Learning System - Exam API Endpoints
# Story 6.1-6.8: Examination Whiteboard REST endpoints
#
# [Source: _bmad-output/implementation-artifacts/6-1 through 6-8]
"""
Exam REST endpoints:
  POST   /api/v1/exam/start                    -- Story 6.1: Create exam session
  GET    /api/v1/exam/{exam_id}                -- Story 6.1: Get exam session details
  GET    /api/v1/exam/by-canvas/{cid}          -- Story 6.1: List sessions by canvas
  PATCH  /api/v1/exam/{exam_id}/status         -- Story 6.1/6.7: Update status
  POST   /api/v1/exam/analyze-canvas           -- Story 6.2: Content analysis
  POST   /api/v1/exam/{exam_id}/sync-node      -- Story 6.5: Sync discovered node
  POST   /api/v1/exam/{exam_id}/hint           -- Story 6.6: Progressive hint
  POST   /api/v1/exam/{exam_id}/skip           -- Story 6.6: Skip question
  POST   /api/v1/exam/{exam_id}/complete       -- Story 6.8: Save exam record
  GET    /api/v1/exam/records                  -- Story 6.8: List records (paginated)
  GET    /api/v1/exam/records/{exam_id}        -- Story 6.8: Record detail
  GET    /api/v1/exam/records/by-canvas/{cid}  -- Story 6.8: Records by canvas
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import DEFAULT_GROUP_ID
from app.models.exam_models import (
    CanvasAnalysisRequest,
    CanvasAnalysisResponse,
    ExamCompleteRequest,
    ExamCompleteResponse,
    ExamNodeSyncRequest,
    ExamNodeSyncResponse,
    ExamRecordDetail,
    ExamRecordListResponse,
    ExamSessionCreate,
    ExamSessionListResponse,
    ExamSessionResponse,
    ExamStatusUpdate,
    ExamStatusUpdateResponse,
    HintRequest,
    HintResponse,
    SkipRequest,
    SkipResponse,
)
from app.services.exam_service import get_exam_service

logger = logging.getLogger(__name__)

exam_router = APIRouter()


# Wave-5 Stage B (2026-05-12) — Multi-vault ContextVar 注入辅助.
# Exam endpoints (4 个 group_id Query) 此前 ContextVar 未注入 → 跨 vault 考试记录串库.
def _resolve_vault_group_id(
    vault_id: Optional[str],
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
    legacy_group_id: Optional[str] = None,
) -> str:
    """Wave-5 Stage B — vault_id → ContextVar 注入 + 派生 group_id."""
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
        logger.warning(
            "Wave-5 Stage B: exam endpoint vault_id missing, "
            "falling back to deprecated group_id=%s",
            legacy_group_id,
        )
        derived = canonical_group_id(legacy_group_id)
    else:
        logger.warning(
            "Wave-5 Stage B: exam endpoint both vault_id and group_id missing, "
            "falling back to DEFAULT_GROUP_ID"
        )
        derived = DEFAULT_GROUP_ID

    set_current_subject_id(derived)
    return derived


@exam_router.post("/exam/start", response_model=ExamSessionResponse)
async def start_exam(request: ExamSessionCreate) -> ExamSessionResponse:
    """Create a new exam session.

    Story 6.1 AC-1: Generate exam board from source canvas.
    Story 6.1 AC-3: Rejects if source is already an exam board (400).

    Args:
        request: ExamSessionCreate with source_canvas_id and exam_mode.

    Returns:
        Created ExamSessionResponse.

    Raises:
        HTTPException 400: If source canvas is an exam board.
    """
    svc = get_exam_service()
    try:
        session = await svc.create_session(request)
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@exam_router.get("/exam/{exam_id}", response_model=ExamSessionResponse)
async def get_exam(exam_id: str) -> ExamSessionResponse:
    """Get exam session details.

    Args:
        exam_id: The exam session UUID.

    Returns:
        ExamSessionResponse.

    Raises:
        HTTPException 404: If exam session not found.
    """
    svc = get_exam_service()
    session = await svc.get_session(exam_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Exam session {exam_id} not found")
    return session


@exam_router.get(
    "/exam/by-canvas/{canvas_id}",
    response_model=ExamSessionListResponse,
)
async def list_exams_by_canvas(canvas_id: str) -> ExamSessionListResponse:
    """List all exam sessions for a source canvas.

    Args:
        canvas_id: The source canvas board ID.

    Returns:
        ExamSessionListResponse with sessions sorted by creation time DESC.
    """
    svc = get_exam_service()
    sessions = await svc.list_sessions_by_canvas(canvas_id)
    return ExamSessionListResponse(sessions=sessions, total=len(sessions))


@exam_router.patch(
    "/exam/{exam_id}/status",
    response_model=ExamSessionResponse,
)
async def update_exam_status(
    exam_id: str, update: ExamStatusUpdate
) -> ExamSessionResponse:
    """Update exam session status.

    Story 6.1 AC-5: Status transitions (idle -> in_progress -> paused/completed).
    Story 6.2 AC-5: Mode update after user selection.

    Args:
        exam_id: The exam session UUID.
        update: ExamStatusUpdate payload.

    Returns:
        Updated ExamSessionResponse.

    Raises:
        HTTPException 404: If exam session not found.
    """
    svc = get_exam_service()
    session = await svc.update_status(exam_id, update)
    if not session:
        raise HTTPException(status_code=404, detail=f"Exam session {exam_id} not found")
    return session


@exam_router.post(
    "/exam/analyze-canvas",
    response_model=CanvasAnalysisResponse,
)
async def analyze_canvas(
    request: CanvasAnalysisRequest,
) -> CanvasAnalysisResponse:
    """Analyze canvas content type and recommend exam mode.

    Story 6.2 AC-2: Constructive Alignment (Biggs 1996).
    - Knowledge canvas -> point-to-point
    - Problem canvas -> comprehensive
    - Mixed -> mixed mode

    Args:
        request: CanvasAnalysisRequest with canvas_id.

    Returns:
        CanvasAnalysisResponse with content_type, recommended_mode, confidence.
    """
    svc = get_exam_service()
    analysis = await svc.analyze_canvas_content(
        canvas_id=request.canvas_id,
        target_node_id=request.target_node_id,
    )
    return analysis


# ======================================================================
# Story 6.5: Recursive Exam -- Node Sync
# ======================================================================


@exam_router.post(
    "/exam/{exam_id}/sync-node",
    response_model=ExamNodeSyncResponse,
    summary="Sync discovered node to source canvas (Story 6.5)",
)
async def sync_exam_node(
    exam_id: str,
    request: ExamNodeSyncRequest,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 防跨 vault 考试节点串库.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
) -> ExamNodeSyncResponse:
    """Sync a node discovered during recursive exam back to source canvas.

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填.

    Creates the node and edge in Neo4j, updates the exam session.
    [Source: Story 6.5 AC-2, AC-3]
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    svc = get_exam_service()
    return await svc.sync_node_to_source_canvas(request, group_id=resolved_group_id)


# ======================================================================
# Story 6.6: Progressive Hints + Skip
# ======================================================================


@exam_router.post(
    "/exam/{exam_id}/hint",
    response_model=HintResponse,
    summary="Generate progressive hint (Chain-of-Hints Level 1-4) (Story 6.6)",
)
async def request_hint(exam_id: str, request: HintRequest) -> HintResponse:
    """Generate a hint at the requested level using LLM.

    Level 1=direction, 2=keyword, 3=framework, 4=scaffolded guide.
    [Source: Story 6.6 AC-1, AC-3, AC-6]
    """
    svc = get_exam_service()
    return await svc.generate_hint(request)


@exam_router.post(
    "/exam/{exam_id}/skip",
    response_model=SkipResponse,
    summary="Skip current question -- no BKT/FSRS penalty (Story 6.6)",
)
async def skip_exam_question(exam_id: str, request: SkipRequest) -> SkipResponse:
    """Skip the current question without mastery penalty.

    BKT p_mastery unchanged. FSRS: no rating event.
    [Source: Story 6.6 AC-4]
    """
    svc = get_exam_service()
    return await svc.skip_question(request)


# ======================================================================
# Story 6.7: Cognitive Load -- Pause / Resume
# (PATCH /exam/{exam_id}/status already handles this via ExamStatusUpdate)
# ======================================================================


@exam_router.get(
    "/exam/{exam_id}/cognitive-load",
    summary="Get cognitive load reminder message (Story 6.7)",
)
async def get_cognitive_load(
    exam_id: str,
    elapsed_minutes: int = Query(
        ..., ge=0, description="Elapsed active exam time in minutes"
    ),
) -> dict:
    """Check if a cognitive load rest reminder should be shown.

    Returns the appropriate reminder message for the given elapsed time,
    or null if no reminder is warranted.

    [Source: Story 6.7 AC-1]
    """
    svc = get_exam_service()
    session = await svc.get_session(exam_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Exam session {exam_id} not found")
    message = svc.get_cognitive_load_message(elapsed_minutes)
    return {"exam_id": exam_id, "elapsed_minutes": elapsed_minutes, "message": message}


@exam_router.post(
    "/exam/{exam_id}/pause",
    response_model=ExamStatusUpdateResponse,
    summary="Pause exam session (Story 6.7)",
)
async def pause_exam(exam_id: str) -> ExamStatusUpdateResponse:
    """Pause an active exam session for cognitive load rest.

    [Source: Story 6.7 AC-6]
    """
    svc = get_exam_service()
    return await svc.pause_exam(exam_id)


@exam_router.post(
    "/exam/{exam_id}/resume",
    response_model=ExamStatusUpdateResponse,
    summary="Resume paused exam session (Story 6.7)",
)
async def resume_exam(exam_id: str) -> ExamStatusUpdateResponse:
    """Resume a paused exam session.

    [Source: Story 6.7 AC-6]
    """
    svc = get_exam_service()
    return await svc.resume_exam(exam_id)


# ======================================================================
# Story 6.8: Exam Record Persistence
# ======================================================================


@exam_router.post(
    "/exam/{exam_id}/complete",
    response_model=ExamCompleteResponse,
    summary="Save complete exam record permanently (Story 6.8)",
)
async def complete_exam(
    exam_id: str,
    request: ExamCompleteRequest,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
) -> ExamCompleteResponse:
    """Finalize and permanently save the complete exam record.

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填.

    Records are immutable (no delete). Includes scores, conversations,
    discovered nodes, and mastery changes.
    [Source: Story 6.8 AC-1, AC-8]
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    svc = get_exam_service()
    return await svc.complete_exam(request, group_id=resolved_group_id)


@exam_router.get(
    "/exam/records",
    response_model=ExamRecordListResponse,
    summary="List all exam records paginated (Story 6.8)",
)
async def list_exam_records(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
) -> ExamRecordListResponse:
    """Get paginated list of exam records, newest first.

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2: vault_id 推荐必填.

    [Source: Story 6.8 AC-7]
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    svc = get_exam_service()
    return await svc.get_exam_records(
        page=page, limit=limit, group_id=resolved_group_id
    )


@exam_router.get(
    "/exam/records/by-canvas/{canvas_id}",
    response_model=ExamRecordListResponse,
    summary="Get exam records for a specific canvas (Story 6.8)",
)
async def get_records_by_canvas(
    canvas_id: str,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
) -> ExamRecordListResponse:
    """Get all exam records associated with a specific source canvas.

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2: vault_id 推荐必填.

    [Source: Story 6.8 AC-6, AC-7]
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id,
        subject_id=subject_id,
        canvas_path=canvas_id,
        legacy_group_id=group_id,
    )
    svc = get_exam_service()
    return await svc.get_records_by_canvas(
        canvas_id=canvas_id, group_id=resolved_group_id
    )


@exam_router.get(
    "/exam/records/{record_exam_id}",
    response_model=ExamRecordDetail,
    summary="Get single exam record with full detail (Story 6.8)",
)
async def get_exam_record_detail(
    record_exam_id: str,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
) -> ExamRecordDetail:
    """Get a complete exam record including conversation replay.

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2: vault_id 推荐必填.

    [Source: Story 6.8 AC-3, AC-7]
    """
    resolved_group_id = _resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )
    svc = get_exam_service()
    record = await svc.get_exam_record(
        exam_id=record_exam_id, group_id=resolved_group_id
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exam record {record_exam_id} not found",
        )
    return record
