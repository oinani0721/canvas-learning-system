# Canvas Learning System - MVP-α-4: 单题评分 endpoint
# PLAN-NNN: EPIC1-BMAD-DEV-ASSESS-2026-04-17
#
# 输入: {question_id, user_answer}
# 流程: 读 question_id 对应题面 -> 单次 gpt-4o-mini 评分 0-5 + 反馈 -> 返回
# 输出: {score, feedback, mastery_delta, graded_at}
#
# 跳过的复杂度: AutoSCORE 4 维 ×3 投票 / SOLO Rubric / 校准检测 / Faithfulness check
# 单一 rubric prompt -> 单 LLM call -> ~3s end-to-end
"""MVP-α-4: POST /api/v1/exam/grade — 极简评分 endpoint.

依赖:
  - app.api.v1.endpoints.exam_quick.get_question_record (in-memory question store)
  - app.config.settings.SCORING_MODEL (LiteLLM model string)
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.v1.endpoints.exam_quick import get_question_record

logger = logging.getLogger(__name__)

exam_grade_router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Rubric — 单一 prompt, 跳过 AutoSCORE 4 维
# ─────────────────────────────────────────────────────────────────────────────

_GRADE_SYSTEM_PROMPT = (
    "你是一位耐心的学习教练。学生回答了一道题, 请你按以下方式评分:\n"
    "\n"
    "1. 给一个 0-5 的整数分数 (0 = 完全错或空, 5 = 完美理解透彻)\n"
    "2. 写 60-100 字的简短反馈 — 必须先肯定一处具体亮点, 再指出一个改进方向\n"
    "3. 不要假装客观, 像导师一样直接说话, 用第二人称「你」\n"
    "\n"
    "用 JSON 返回:\n"
    '{"score": <int 0-5>, "feedback": "<60-100 字>"}'
)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────


class ExamGradeRequest(BaseModel):
    """POST /api/v1/exam/grade 请求体."""

    question_id: str = Field(..., min_length=1, description="α-2 返回的 UUID")
    user_answer: str = Field(..., min_length=1, description="学生手写答案")


class ExamGradeResponse(BaseModel):
    """POST /api/v1/exam/grade 响应体."""

    score: int = Field(..., ge=0, le=5, description="0-5 整数分")
    feedback: str = Field(..., description="60-100 字导师式反馈")
    mastery_delta: int = Field(
        ..., description="掌握度变化 (+1 / 0 / -1) — MVP-α 简化版"
    )
    graded_at: str = Field(..., description="评分时间 ISO 8601")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────


@exam_grade_router.post(
    "/exam/grade",
    response_model=ExamGradeResponse,
    summary="MVP-α-4: 单次 LLM 评分 + 文字反馈",
)
async def exam_grade(req: ExamGradeRequest) -> ExamGradeResponse:
    """gpt-4o-mini 单次评分 0-5 + 反馈. 失败抛 502."""
    record = get_question_record(req.question_id)
    if not record:
        # MVP-α 用 in-memory store, 重启或 200 条上限淘汰后会 404
        raise HTTPException(
            status_code=404,
            detail=(
                f"question_id {req.question_id} not found "
                "(可能 backend 重启或题目已被 ring buffer 淘汰)"
            ),
        )

    question_text = record["question_text"]
    user_msg = (
        f"## 题目\n{question_text}\n\n"
        f"## 学生回答\n{req.user_answer}\n\n"
        "## 你的评分 (JSON)"
    )

    try:
        from litellm import acompletion

        from app.config import settings

        model = settings.SCORING_MODEL
        if not model:
            provider = settings.AI_PROVIDER
            model_name = settings.AI_MODEL_NAME
            if provider and not model_name.startswith(provider):
                model = f"{provider}/{model_name}"
            else:
                model = model_name

        response = await acompletion(
            model=model,
            messages=[
                {"role": "system", "content": _GRADE_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content or ""
        data = json.loads(raw_content)

        score_raw = int(data.get("score", 0))
        score = max(0, min(5, score_raw))
        feedback = (data.get("feedback") or "").strip()
        if not feedback:
            feedback = "(模型未给出反馈, 你的回答已记录)"

    except json.JSONDecodeError as e:
        logger.error(f"[MVP-α-4] grade JSON parse failed: {e} raw={raw_content[:200]}")
        raise HTTPException(
            status_code=502,
            detail=f"grading service returned non-JSON response: {e}",
        ) from e
    except Exception as e:
        logger.error(
            f"[MVP-α-4] grade LLM call failed for qid={req.question_id[:8]}: {e}"
        )
        raise HTTPException(
            status_code=502,
            detail=f"grading service unavailable: {e}",
        ) from e

    # MVP-α mastery delta — 简化 heuristic (β 阶段才接 BKT/FSRS)
    if score >= 4:
        mastery_delta = 1
    elif score <= 1:
        mastery_delta = -1
    else:
        mastery_delta = 0

    graded_at = datetime.now(timezone.utc).isoformat()
    logger.info(
        f"[MVP-α-4] graded qid={req.question_id[:8]} "
        f"score={score} delta={mastery_delta} "
        f"node={record.get('node_id')} ans_len={len(req.user_answer)}"
    )

    return ExamGradeResponse(
        score=score,
        feedback=feedback,
        mastery_delta=mastery_delta,
        graded_at=graded_at,
    )
