# Canvas Learning System - MVP-α-2: 一键考察 endpoint
# PLAN-NNN: EPIC1-BMAD-DEV-ASSESS-2026-04-17
#
# 输入: {node_id, vault_id}
# 流程: _fetch_tips_and_errors(node_id) -> generate_question(tips) -> store(uuid)
# 输出: {question_id, question_text, tip_count, tips_used, generated_at}
#
# 跳过的复杂度: IRT 难度匹配 / 模式选择 / 批量出题 / Persistent Store
# 闭环优先于精度: in-memory ring buffer, 重启清空 (与 Anki/Duolingo 第一版同思路).
"""MVP-α-2: POST /api/v1/exam/quick — 极简出题 endpoint.

依赖:
  - app.services.learning_context_service._fetch_tips_and_errors (frontmatter.tips 第 3 source)
  - app.services.question_generator.QuestionGenerator.generate_question (MVP-α-1)

被依赖:
  - exam_grade.py 通过 get_question_record(question_id) 读题面以评分
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.learning_context_service import _fetch_tips_and_errors
from app.services.question_generator import QuestionGenerator

logger = logging.getLogger(__name__)

exam_quick_router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# In-memory question store — α/β/γ 升级路径上 β 才换 Neo4j
# ─────────────────────────────────────────────────────────────────────────────

_QUESTION_STORE: Dict[str, Dict[str, Any]] = {}
_QUESTION_STORE_MAX = 200  # FIFO ring buffer; 重启清空 MVP 故意为之


def get_question_record(question_id: str) -> Optional[Dict[str, Any]]:
    """exam_grade 读题面用. 跨模块共享 in-memory store 的唯一入口."""
    return _QUESTION_STORE.get(question_id)


def _evict_if_full() -> None:
    if len(_QUESTION_STORE) < _QUESTION_STORE_MAX:
        return
    oldest_key = next(iter(_QUESTION_STORE))
    _QUESTION_STORE.pop(oldest_key, None)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────


class ExamQuickRequest(BaseModel):
    """POST /api/v1/exam/quick 请求体."""

    node_id: str = Field(
        ..., min_length=1, description="节点 ID (节点 md 文件名, 不含 .md)"
    )
    vault_id: str = Field(
        ..., min_length=1, description="vault 标识 (MVP-α 不做强校验, β 引入隔离)"
    )


class ExamQuickResponse(BaseModel):
    """POST /api/v1/exam/quick 响应体."""

    question_id: str = Field(..., description="题目 UUID, 评分时回传")
    question_text: str = Field(..., description="生成的题目文字")
    tip_count: int = Field(..., ge=0, description="本次出题引用的用户批注条数")
    tips_used: List[str] = Field(default_factory=list, description="实际引用的原话")
    generated_at: str = Field(..., description="生成时间 ISO 8601")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────


@exam_quick_router.post(
    "/exam/quick",
    response_model=ExamQuickResponse,
    summary="MVP-α-2: 一键基于批注出题",
)
async def exam_quick(req: ExamQuickRequest) -> ExamQuickResponse:
    """读 frontmatter.tips → LLM 拼 prompt 出题 → 返回 question_text.

    response time: ~3-5s (单 LLM call). 失败时降级到回退题模板.
    """
    try:
        tips, _errors = await _fetch_tips_and_errors(req.node_id)
    except Exception as e:
        # 上下文获取失败不应导致 500 — 降级为空 tips, 让 generate_question 走回退路径
        logger.warning(
            f"[MVP-α-2] _fetch_tips_and_errors failed for node={req.node_id}: {e}"
        )
        tips = []

    node_text = _read_node_markdown(req.node_id)

    generator = QuestionGenerator()
    try:
        result = await generator.generate_question(
            node_id=req.node_id,
            user_tips=tips,
            node_text=node_text,
        )
    except Exception as e:
        logger.error(f"[MVP-α-2] generate_question failed for node={req.node_id}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"question generation service unavailable: {e}",
        ) from e

    question_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    _evict_if_full()
    _QUESTION_STORE[question_id] = {
        "question_text": result["question_text"],
        "node_id": req.node_id,
        "vault_id": req.vault_id,
        "tips_used": result.get("tips_used", []),
        "generated_at": generated_at,
    }

    logger.info(
        f"[MVP-α-2] quick exam generated: node={req.node_id} "
        f"vault={req.vault_id} tips={result.get('tip_count', 0)} "
        f"qid={question_id[:8]}"
    )

    return ExamQuickResponse(
        question_id=question_id,
        question_text=result["question_text"],
        tip_count=int(result.get("tip_count", 0)),
        tips_used=list(result.get("tips_used", [])),
        generated_at=generated_at,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _read_node_markdown(node_id: str) -> str:
    """读节点 md 文件正文 (去 frontmatter), 找不到返回空串. 不抛异常."""
    try:
        from app.config import settings

        canvas_base = (
            getattr(settings, "CANVAS_BASE_PATH", None) or "/vaults/canvas-vault"
        )
        for prefix in ("节点", "原白板"):
            md_path = Path(canvas_base) / prefix / f"{node_id}.md"
            if not md_path.exists():
                continue
            text = md_path.read_text(encoding="utf-8")
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    text = parts[2]
            return text.strip()
    except OSError as e:
        logger.debug(f"[MVP-α-2] node md not found for {node_id}: {e}")
    except Exception as e:
        logger.debug(f"[MVP-α-2] unexpected error reading {node_id}: {e}")
    return ""
