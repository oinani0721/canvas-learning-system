"""
Exam Sessions API Routes (Story 5.4)

REST endpoints for examination session management:
  GET /exam_sessions - List all exam sessions (with optional board_id filter)

Exam sessions are stored as EpisodicNode entities in Neo4j with
source_description='exam_session'. Sessions are created by Story 6.1/6.2
when users start examinations; this endpoint provides read access for
the Dashboard's exam history tab.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.config import DEFAULT_GROUP_ID

logger = logging.getLogger(__name__)

exam_sessions_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class ExamSessionResponse(BaseModel):
    """A single exam session record."""

    id: str
    source_board_id: str = ""
    source_board_name: str = ""
    mode: str = Field(
        default="comprehensive", description="point-to-point | comprehensive | mixed"
    )
    status: str = Field(default="completed", description="in-progress | completed")
    nodes_examined: int = 0
    mastery_change_summary: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None


class ExamSessionListResponse(BaseModel):
    """Response for exam sessions list."""

    sessions: list[ExamSessionResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@exam_sessions_router.get("/exam_sessions", response_model=ExamSessionListResponse)
async def list_exam_sessions(
    board_id: Optional[str] = Query(
        default=None, description="Filter by source board ID"
    ),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 (Wave-5 Stage B) — 推荐必填. 注入 ContextVar 防跨 vault 会话串库.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
):
    """
    List all exam sessions, optionally filtered by source board ID.

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2: vault_id 推荐必填.

    Queries Neo4j for EpisodicNode entities with source_description='exam_session'.
    Returns empty list when no exam sessions exist (valid state before Story 6.1/6.2).
    """
    # Wave-5 Stage B — vault_id ContextVar 注入 + 派生 group_id
    from app.config import sanitize_vault_id
    from app.core.subject_config import (
        build_vault_group_id,
        canonical_group_id,
        set_current_subject_id,
    )

    if vault_id and vault_id.strip():
        sanitized = sanitize_vault_id(vault_id)
        resolved_group_id = build_vault_group_id(sanitized, subject_id=subject_id)
    elif group_id and group_id.strip():
        logger.warning(
            "Wave-5 Stage B: exam_sessions endpoint vault_id missing, "
            "falling back to deprecated group_id=%s",
            group_id,
        )
        resolved_group_id = canonical_group_id(group_id)
    else:
        logger.warning(
            "Wave-5 Stage B: exam_sessions endpoint both vault_id and group_id missing, "
            "falling back to DEFAULT_GROUP_ID"
        )
        resolved_group_id = DEFAULT_GROUP_ID

    set_current_subject_id(resolved_group_id)
    # 透传到 Cypher params
    group_id = resolved_group_id

    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()

    # Build query with optional board_id filter
    board_filter = ""
    if board_id:
        board_filter = "AND e.source_board_id = $board_id"

    query = f"""
    MATCH (e:EpisodicNode)
    WHERE e.group_id = $group_id
      AND e.source_description = 'exam_session'
      {board_filter}
    RETURN e.uuid AS id,
           COALESCE(e.source_board_id, '') AS source_board_id,
           COALESCE(e.source_board_name, '') AS source_board_name,
           COALESCE(e.exam_mode, 'comprehensive') AS mode,
           COALESCE(e.exam_status, 'completed') AS status,
           COALESCE(e.nodes_examined, 0) AS nodes_examined,
           COALESCE(e.mastery_change_summary, '') AS mastery_change_summary,
           COALESCE(toString(e.created_at), '') AS created_at,
           toString(e.completed_at) AS completed_at
    ORDER BY e.created_at DESC
    """

    params: dict = {"group_id": group_id}
    if board_id:
        params["board_id"] = board_id

    try:
        records = await client.run_query(query, **params)

        sessions = []
        for record in records or []:
            data = record if isinstance(record, dict) else record.data()
            sessions.append(
                ExamSessionResponse(
                    id=data.get("id", ""),
                    source_board_id=data.get("source_board_id", ""),
                    source_board_name=data.get("source_board_name", ""),
                    mode=data.get("mode", "comprehensive"),
                    status=data.get("status", "completed"),
                    nodes_examined=data.get("nodes_examined", 0),
                    mastery_change_summary=data.get("mastery_change_summary", ""),
                    created_at=data.get("created_at", ""),
                    completed_at=data.get("completed_at"),
                )
            )

        return ExamSessionListResponse(sessions=sessions, total=len(sessions))
    except Exception as e:
        logger.warning(f"Failed to list exam sessions: {e}")
        return ExamSessionListResponse(sessions=[], total=0)
