"""Exam ACP proxy router (Day 4 staging).

Usage in DeepTutor fork:
  Copy to: deeptutor-fork/backend/app/routers/exam_proxy.py
  Register: `app.include_router(exam_proxy.router)`

Proxies DeepTutor frontend → Canvas ACP/AutoSCORE pipeline.
Pipeline:
  1. POST /api/v1/exam/start         → returns pipeline_token + question
  2. (user answers in DeepTutor UI)
  3. POST /api/v1/exam/score         → returns grade + new pipeline_token
  4. POST /api/v1/mastery/update_fsrs → with new pipeline_token
  5. POST /api/v1/mastery/update_bkt  → with same pipeline_token
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.clients.canvas_client import CanvasClient, CanvasClientError, get_canvas_client


router = APIRouter(prefix="/api/v1/exam", tags=["exam"])


class StartRequest(BaseModel):
    node_id: str
    session_id: str | None = None


class ScoreRequest(BaseModel):
    node_id: str
    question_id: str
    student_answer: str = Field(..., min_length=1, max_length=10000)
    pipeline_token: str


class ACPRequest(BaseModel):
    node_id: str
    include_related: bool = True


@router.post("/start")
async def start_exam(req: StartRequest, client: CanvasClient = Depends(get_canvas_client)):
    """Generate question via ACP 5-layer prompt assembly."""
    try:
        return await client.exam_start(req.node_id, req.session_id)
    except CanvasClientError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/score")
async def score_answer(req: ScoreRequest, client: CanvasClient = Depends(get_canvas_client)):
    """Submit answer for AutoSCORE (4-dim grading + injection check)."""
    try:
        return await client.exam_score(
            node_id=req.node_id,
            question_id=req.question_id,
            student_answer=req.student_answer,
            pipeline_token=req.pipeline_token,
        )
    except CanvasClientError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/assemble_acp")
async def assemble_acp(req: ACPRequest, client: CanvasClient = Depends(get_canvas_client)):
    """Get full ACP context package for a concept node."""
    try:
        return await client.assemble_acp(req.node_id, include_related=req.include_related)
    except CanvasClientError as e:
        raise HTTPException(status_code=502, detail=str(e))
