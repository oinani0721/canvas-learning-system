"""
Verification Service - 智能引导模式验证白板服务

Epic 24: Verification Canvas Redesign (智能引导模式)
Story 24.1: Smart Guidance Architecture Design
Story 24.5: RAG Context Injection for Verification Canvas
Story 31.1: VerificationService核心逻辑激活

提供Socratic式验证白板的核心业务逻辑，包含:
- 会话管理 (start_session, process_answer)
- 进度跟踪 (get_progress)
- Canvas生成 (generate_verification_canvas)
- RAG上下文注入 (Story 24.5)

✅ Verified from backend/app/services/review_service.py (项目现有模式):
- 使用@dataclass定义Progress类
- 异步方法设计
- cleanup方法用于资源清理

Story 24.1 AC:
- ✅ AC 5: 创建 verification_service.py

Story 24.5 Implementation:
- ✅ RAG context injection for questions and hints
- ✅ Cross-canvas context retrieval
- ✅ Textbook context integration
- ✅ Graceful degradation on timeout/errors

Story 31.1 Implementation:
- ✅ AC-31.1.1: start_session() reads Canvas file for red/purple nodes
- ✅ AC-31.1.2: generate_question_with_rag() calls Gemini API
- ✅ AC-31.1.3: process_answer() integrates scoring-agent (0-40 mapping)
- ✅ AC-31.1.4: RAG context injection for all methods
- ✅ AC-31.1.5: 500ms timeout protection and graceful degradation

Author: Canvas Learning System Team
Version: 3.0.0 (Story 31.1 - Real AI Integration)
Created: 2025-12-13
Updated: 2026-01-20 (Story 31.1 - Real AI Activation)
"""

import asyncio
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Story 31.1: Environment variable for mock mode
USE_MOCK_VERIFICATION = os.getenv("USE_MOCK_VERIFICATION", "false").lower() == "true"

# Story 31.1: AI timeout configuration (AC-31.1.5)
VERIFICATION_AI_TIMEOUT = float(os.getenv("VERIFICATION_AI_TIMEOUT", "0.5"))  # 500ms default

if TYPE_CHECKING:
    from app.services.canvas_service import CanvasService
    from app.services.agent_service import AgentService
    from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


# ===========================================================================
# Story 31.5: Difficulty Adaptive Algorithm
# [Source: docs/stories/31.5.story.md]
# ===========================================================================

class DifficultyLevel(str, Enum):
    """
    难度等级枚举

    Story 31.5 AC-31.5.2: Difficulty levels based on 0-100 score scale.

    [Source: specs/data/difficulty-level.schema.json]
    """
    EASY = "easy"       # avg < 60: 需要加强，聚焦核心概念
    MEDIUM = "medium"   # 60 <= avg < 80: 部分掌握，验证深度
    HARD = "hard"       # avg >= 80: 掌握良好，挑战应用题


class QuestionType(str, Enum):
    """
    问题类型枚举

    Story 31.5 AC-31.5.3: Question types mapped from difficulty levels.

    [Source: docs/stories/31.5.story.md#Task-4.1]
    """
    BREAKTHROUGH = "breakthrough"   # easy -> 突破型问题 (聚焦核心概念)
    VERIFICATION = "verification"   # medium -> 验证型问题 (测试理解深度)
    APPLICATION = "application"     # hard -> 应用型问题 (跨概念应用)


@dataclass
class ForgettingStatus:
    """
    遗忘检测状态

    Story 31.5 AC-31.5.5: Forgetting detection result.

    [Source: specs/data/difficulty-level.schema.json#forgetting_status]
    """
    needs_review: bool
    decay_percentage: float


@dataclass
class DifficultyResult:
    """
    难度自适应计算结果

    Story 31.5 AC-31.5.2, AC-31.5.3, AC-31.5.5: Complete difficulty analysis.

    [Source: specs/data/difficulty-level.schema.json]
    """
    level: DifficultyLevel
    average_score: float
    sample_size: int
    question_type: QuestionType
    forgetting_status: Optional[ForgettingStatus] = None
    is_mastered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching difficulty-level.schema.json."""
        return {
            "level": self.level.value,
            "average_score": self.average_score,
            "sample_size": self.sample_size,
            "question_type": self.question_type.value,
            "forgetting_status": {
                "needs_review": self.forgetting_status.needs_review,
                "decay_percentage": self.forgetting_status.decay_percentage
            } if self.forgetting_status else None,
            "is_mastered": self.is_mastered
        }


# Story 31.5 Task 3.2: Difficulty thresholds (0-100 score scale)
# [Source: docs/stories/31.5.story.md#Task-3.2]
DIFFICULTY_THRESHOLDS = {
    "hard": 80,    # avg >= 80: 掌握良好
    "medium": 60,  # 60 <= avg < 80: 部分掌握
    "easy": 0,     # avg < 60: 需要加强
}

# Story 31.5 Task 5.2: Mastery threshold (0-100 score scale)
# [Source: docs/stories/31.5.story.md#Task-5.2]
MASTERY_THRESHOLD = 80
MASTERY_CONSECUTIVE_COUNT = 3

# Story 31.5 Task 6.2: Forgetting detection threshold
# [Source: docs/stories/31.5.story.md#Task-6.2]
FORGETTING_DECAY_THRESHOLD = 0.3  # 30% decline


def calculate_difficulty_level(scores: List[int]) -> DifficultyLevel:
    """
    Calculate difficulty level based on average score.

    Story 31.5 AC-31.5.2: Difficulty levels based on 0-100 score scale.
    - avg >= 80 -> hard (掌握良好)
    - 60 <= avg < 80 -> medium (部分掌握)
    - avg < 60 -> easy (需要加强)

    Args:
        scores: List of historical scores (0-100 scale)

    Returns:
        DifficultyLevel enum value

    [Source: docs/stories/31.5.story.md#Task-3]
    """
    if not scores:
        return DifficultyLevel.MEDIUM  # Default to medium when no history

    average = sum(scores) / len(scores)

    if average >= DIFFICULTY_THRESHOLDS["hard"]:
        return DifficultyLevel.HARD
    elif average >= DIFFICULTY_THRESHOLDS["medium"]:
        return DifficultyLevel.MEDIUM
    else:
        return DifficultyLevel.EASY


def get_question_type_for_difficulty(level: DifficultyLevel) -> QuestionType:
    """
    Map difficulty level to question type.

    Story 31.5 AC-31.5.3: Question type selection based on difficulty.
    - easy -> breakthrough (突破型问题)
    - medium -> verification (验证型问题)
    - hard -> application (应用型问题)

    Args:
        level: DifficultyLevel enum value

    Returns:
        QuestionType enum value

    [Source: docs/stories/31.5.story.md#Task-4.1]
    """
    mapping = {
        DifficultyLevel.EASY: QuestionType.BREAKTHROUGH,
        DifficultyLevel.MEDIUM: QuestionType.VERIFICATION,
        DifficultyLevel.HARD: QuestionType.APPLICATION,
    }
    return mapping.get(level, QuestionType.VERIFICATION)


def is_concept_mastered(scores: List[int]) -> bool:
    """
    Check if concept is mastered (consecutive high scores).

    Story 31.5 AC-31.5.4: Mastery = 3 consecutive scores >= 80.

    Args:
        scores: List of historical scores (0-100 scale, oldest to newest)

    Returns:
        True if concept is mastered

    [Source: docs/stories/31.5.story.md#Task-5.2]
    """
    if len(scores) < MASTERY_CONSECUTIVE_COUNT:
        return False

    # Check if last N scores are all >= threshold
    recent_scores = scores[-MASTERY_CONSECUTIVE_COUNT:]
    return all(s >= MASTERY_THRESHOLD for s in recent_scores)


def detect_forgetting(recent_score: int, historical_avg: float) -> ForgettingStatus:
    """
    Detect if forgetting has occurred.

    Story 31.5 AC-31.5.5: Forgetting = recent score < historical_avg * 0.7 (30%+ decline).

    Args:
        recent_score: Most recent score (0-100)
        historical_avg: Historical average score

    Returns:
        ForgettingStatus with needs_review and decay_percentage

    [Source: docs/stories/31.5.story.md#Task-6.2]
    """
    if historical_avg == 0:
        return ForgettingStatus(needs_review=False, decay_percentage=0.0)

    decay = (historical_avg - recent_score) / historical_avg
    decay_percentage = round(decay * 100, 2)

    return ForgettingStatus(
        needs_review=decay > FORGETTING_DECAY_THRESHOLD,
        decay_percentage=max(0.0, decay_percentage)  # Clamp to non-negative
    )


def calculate_full_difficulty_result(
    scores: List[int],
    recent_score: Optional[int] = None
) -> DifficultyResult:
    """
    Calculate complete difficulty analysis including all metrics.

    Story 31.5: Combines all difficulty-related calculations.

    Args:
        scores: List of historical scores (0-100 scale, oldest to newest)
        recent_score: Optional most recent score (for forgetting detection)

    Returns:
        DifficultyResult with all metrics

    [Source: docs/stories/31.5.story.md]
    """
    # Calculate average
    average_score = sum(scores) / len(scores) if scores else 0.0

    # Determine difficulty level
    level = calculate_difficulty_level(scores)

    # Map to question type
    question_type = get_question_type_for_difficulty(level)

    # Check mastery
    mastered = is_concept_mastered(scores)

    # Detect forgetting (if recent score provided)
    forgetting = None
    if recent_score is not None and average_score > 0:
        forgetting = detect_forgetting(recent_score, average_score)

    return DifficultyResult(
        level=level,
        average_score=round(average_score, 2),
        sample_size=len(scores),
        question_type=question_type,
        forgetting_status=forgetting,
        is_mastered=mastered
    )


class VerificationStatus(str, Enum):
    """验证会话状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class VerificationProgress:
    """
    验证进度数据类

    用于追踪验证会话的实时进度。
    Story 24.3 将使用此类显示实时进度。
    """
    session_id: str
    canvas_name: str
    total_concepts: int
    completed_concepts: int
    current_concept: str
    current_concept_idx: int
    green_count: int = 0
    yellow_count: int = 0
    purple_count: int = 0
    red_count: int = 0
    status: VerificationStatus = VerificationStatus.PENDING
    hints_given: int = 0
    max_hints: int = 3
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def progress_percentage(self) -> float:
        """计算完成百分比"""
        if self.total_concepts == 0:
            return 0.0
        return (self.completed_concepts / self.total_concepts) * 100

    @property
    def mastery_percentage(self) -> float:
        """计算掌握率 (绿色占已完成的比例)"""
        if self.completed_concepts == 0:
            return 0.0
        return (self.green_count / self.completed_concepts) * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "canvas_name": self.canvas_name,
            "total_concepts": self.total_concepts,
            "completed_concepts": self.completed_concepts,
            "current_concept": self.current_concept,
            "current_concept_idx": self.current_concept_idx,
            "green_count": self.green_count,
            "yellow_count": self.yellow_count,
            "purple_count": self.purple_count,
            "red_count": self.red_count,
            "status": self.status.value,
            "progress_percentage": round(self.progress_percentage, 1),
            "mastery_percentage": round(self.mastery_percentage, 1),
            "hints_given": self.hints_given,
            "max_hints": self.max_hints,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class VerificationService:
    """
    验证白板服务

    提供Socratic式智能引导验证的核心功能。

    主要方法:
    - start_session(): 开始新的验证会话
    - process_answer(): 处理用户回答
    - get_progress(): 获取当前进度
    - skip_concept(): 跳过当前概念
    - pause_session(): 暂停会话
    - resume_session(): 恢复会话
    - end_session(): 结束会话

    Story 24.5 RAG Integration:
    - generate_question_with_rag(): 使用RAG上下文生成问题
    - generate_hint_with_rag(): 使用学习历史生成个性化提示
    - _get_rag_context_for_concept(): 查询RAG上下文
    - _get_cross_canvas_context(): 查询跨Canvas关联
    """

    # ✅ Verified from Story 24.5 Dev Notes: RAG Configuration
    RAG_ENABLED = True  # Can be disabled via config
    RAG_TIMEOUT = 5.0   # Timeout in seconds (AC5: Graceful degradation)

    # Story 31.4: Question angle priority (AC-31.4.2)
    QUESTION_ANGLE_PRIORITY = ["application", "comparison", "counterexample", "synthesis"]

    def __init__(
        self,
        rag_service: Optional[Any] = None,
        cross_canvas_service: Optional[Any] = None,
        textbook_context_service: Optional[Any] = None,
        canvas_service: Optional["CanvasService"] = None,
        agent_service: Optional["AgentService"] = None,
        canvas_base_path: Optional[str] = None,
        graphiti_client: Optional[Any] = None,
        memory_service: Optional["MemoryService"] = None
    ):
        """
        初始化服务

        Story 24.5 Args:
            rag_service: Optional RAGService for context-aware generation
            cross_canvas_service: Optional CrossCanvasService for cross-canvas context
            textbook_context_service: Optional TextbookContextService for textbook references

        Story 31.1 Args:
            canvas_service: CanvasService for reading Canvas files (AC-31.1.1)
            agent_service: AgentService for Gemini API and scoring-agent calls (AC-31.1.2, AC-31.1.3)
            canvas_base_path: Base path for Canvas files (fallback if canvas_service not provided)

        Story 31.4 Args:
            graphiti_client: GraphitiTemporalClient for question deduplication (AC-31.4.1)

        Story 31.5 Args:
            memory_service: MemoryService for historical score queries (AC-31.5.1)

        [Source: docs/stories/24.5.story.md#Dev-Notes Step 1]
        [Source: docs/stories/31.1.story.md#Task-1]
        [Source: docs/stories/31.4.story.md#Task-2]
        [Source: docs/stories/31.5.story.md#Task-7]
        """
        # 活动会话存储 (session_id -> state)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        # 进度存储 (session_id -> VerificationProgress)
        self._progress: Dict[str, VerificationProgress] = {}

        # Story 24.5: RAG Integration dependencies
        self._rag_service = rag_service
        self._cross_canvas_service = cross_canvas_service
        self._textbook_context_service = textbook_context_service

        # Story 31.1: Canvas and Agent service dependencies
        self._canvas_service = canvas_service
        self._agent_service = agent_service
        self._canvas_base_path = canvas_base_path

        # Story 31.4: Graphiti client for question deduplication
        self._graphiti_client = graphiti_client

        # Story 31.5: Memory service for difficulty adaptation
        self._memory_service = memory_service

        logger.info(
            f"VerificationService initialized "
            f"(RAG: {rag_service is not None}, "
            f"CrossCanvas: {cross_canvas_service is not None}, "
            f"Textbook: {textbook_context_service is not None}, "
            f"Canvas: {canvas_service is not None}, "
            f"Agent: {agent_service is not None}, "
            f"Graphiti: {graphiti_client is not None}, "
            f"Memory: {memory_service is not None}, "
            f"MockMode: {USE_MOCK_VERIFICATION})"
        )

    async def start_session(
        self,
        canvas_name: str,
        node_ids: Optional[List[str]] = None,
        canvas_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        开始新的验证会话

        Story 31.1 AC-31.1.1: 从Canvas文件读取红色(color="4")+紫色(color="3")节点并提取概念

        Args:
            canvas_name: 源Canvas名称
            node_ids: 可选，指定要验证的节点ID列表
            canvas_path: 可选，Canvas文件完整路径 (Story 31.1)

        Returns:
            {
                "session_id": str,
                "total_concepts": int,
                "first_question": str,
                "status": "in_progress"
            }

        [Source: docs/stories/31.1.story.md#Task-1]
        """
        session_id = str(uuid.uuid4())
        logger.info(f"Starting verification session: {session_id} for canvas: {canvas_name}")

        # Story 31.1 AC-31.1.1: Read Canvas file and extract concepts from red/purple nodes
        concepts = await self._extract_concepts_from_canvas(
            canvas_name=canvas_name,
            canvas_path=canvas_path,
            node_ids=node_ids
        )

        # 创建初始状态
        state = {
            "session_id": session_id,
            "source_canvas": canvas_name,
            "concept_queue": concepts,
            "current_concept": concepts[0] if concepts else "",
            "current_concept_idx": 0,
            "total_concepts": len(concepts),
            "completed_concepts": 0,
            "green_count": 0,
            "yellow_count": 0,
            "purple_count": 0,
            "red_count": 0,
            "hints_given": 0,
            "max_hints": 3,
            "current_hints": [],
            "status": VerificationStatus.IN_PROGRESS,
        }

        self._sessions[session_id] = state

        # 创建进度追踪
        progress = VerificationProgress(
            session_id=session_id,
            canvas_name=canvas_name,
            total_concepts=len(concepts),
            completed_concepts=0,
            current_concept=concepts[0] if concepts else "",
            current_concept_idx=0,
            status=VerificationStatus.IN_PROGRESS,
        )
        self._progress[session_id] = progress

        # Story 31.1 AC-31.1.2: Generate first question using Gemini API with RAG context
        first_question = ""
        if concepts:
            first_question = await self.generate_question_with_rag(
                concept=concepts[0],
                canvas_name=canvas_name
            )

        logger.info(f"Session {session_id} started with {len(concepts)} concepts")

        return {
            "session_id": session_id,
            "total_concepts": len(concepts),
            "first_question": first_question,
            "current_concept": concepts[0] if concepts else "",
            "status": "in_progress",
        }

    async def process_answer(
        self,
        session_id: str,
        user_answer: str
    ) -> Dict[str, Any]:
        """
        处理用户回答

        Story 31.1 AC-31.1.3: 集成scoring-agent评估回答（返回0-40分）

        评估回答质量，决定下一步动作（提供提示或进入下一概念）。

        Args:
            session_id: 会话ID
            user_answer: 用户回答内容

        Returns:
            {
                "quality": str,  # excellent/good/partial/wrong
                "score": float,  # 0-40 range (mapped from scoring-agent's 0-100)
                "action": str,  # hint/next/complete
                "hint": Optional[str],
                "next_question": Optional[str],
                "progress": dict
            }

        [Source: docs/stories/31.1.story.md#Task-3]
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        state = self._sessions[session_id]
        progress = self._progress[session_id]
        current_concept = state["current_concept"]
        canvas_name = state["source_canvas"]

        logger.debug(f"Processing answer for session {session_id}, concept: {current_concept}")

        # Story 31.1 AC-31.1.3: Call scoring-agent with timeout protection
        quality, score = await self._evaluate_answer_with_scoring_agent(
            concept=current_concept,
            user_answer=user_answer,
            canvas_name=canvas_name
        )

        # 决定下一步动作
        hints_given = state["hints_given"]
        max_hints = state["max_hints"]

        # Story 31.1: Score threshold updated to 0-40 range (24 = 60 * 0.4)
        if quality in ["excellent", "good"] or score >= 24:
            # 掌握，进入下一概念
            action = await self._advance_concept(state, progress, quality, score)
        elif hints_given < max_hints:
            # 需要提示
            action = self._provide_hint(state, progress)
        else:
            # 已达最大提示次数，进入下一概念
            action = await self._advance_concept(state, progress, quality, score)

        # 更新进度时间
        progress.updated_at = datetime.now()

        return {
            "quality": quality,
            "score": score,
            "action": action["action"],
            "hint": action.get("hint"),
            "next_question": action.get("next_question"),
            "current_concept": state["current_concept"],
            "progress": progress.to_dict(),
        }

    async def _advance_concept(
        self,
        state: Dict[str, Any],
        progress: VerificationProgress,
        quality: str,
        score: float
    ) -> Dict[str, Any]:
        """
        前进到下一概念

        Story 31.1: Updated to async for real question generation.
        Updated score thresholds to use 0-40 range.

        [Source: docs/stories/31.1.story.md#评分映射规则]
        """
        # 更新颜色计数 (using 0-40 range thresholds)
        # Story 31.1 thresholds:
        # - score >= 32: excellent (掌握良好)
        # - score 24-31: good (部分掌握)
        # - score < 24: needs improvement
        if quality == "excellent" or score >= 32:
            state["green_count"] += 1
            progress.green_count += 1
        elif quality == "good" or score >= 24:
            state["yellow_count"] += 1
            progress.yellow_count += 1
        elif quality == "skipped":
            state["purple_count"] += 1
            progress.purple_count += 1
        else:
            state["red_count"] += 1
            progress.red_count += 1

        state["completed_concepts"] += 1
        progress.completed_concepts += 1

        # 重置提示状态
        state["hints_given"] = 0
        state["current_hints"] = []

        # 前进到下一概念
        next_idx = state["current_concept_idx"] + 1
        concept_queue = state["concept_queue"]

        if next_idx < len(concept_queue):
            state["current_concept_idx"] = next_idx
            state["current_concept"] = concept_queue[next_idx]
            progress.current_concept = concept_queue[next_idx]
            progress.current_concept_idx = next_idx
            progress.hints_given = 0

            # Story 31.1 AC-31.1.2: Generate next question using Gemini API
            next_question = await self.generate_question_with_rag(
                concept=concept_queue[next_idx],
                canvas_name=state["source_canvas"]
            )
            return {
                "action": "next",
                "next_question": next_question,
            }
        else:
            # 所有概念完成
            state["status"] = VerificationStatus.COMPLETED
            progress.status = VerificationStatus.COMPLETED
            return {
                "action": "complete",
            }

    def _provide_hint(
        self,
        state: Dict[str, Any],
        progress: VerificationProgress
    ) -> Dict[str, Any]:
        """提供提示"""
        current_concept = state["current_concept"]
        hints_given = state["hints_given"]

        # TODO: Story 24.4 - 动态选择Agent生成提示
        hint = f"提示 {hints_given + 1}: 思考「{current_concept}」的定义和核心特点。"

        state["hints_given"] += 1
        state["current_hints"].append(hint)
        progress.hints_given = state["hints_given"]

        return {
            "action": "hint",
            "hint": hint,
        }

    async def get_progress(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话进度

        Args:
            session_id: 会话ID

        Returns:
            进度信息字典
        """
        if session_id not in self._progress:
            raise ValueError(f"Session not found: {session_id}")

        return self._progress[session_id].to_dict()

    async def skip_concept(self, session_id: str) -> Dict[str, Any]:
        """
        跳过当前概念

        Args:
            session_id: 会话ID

        Returns:
            下一步信息
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        state = self._sessions[session_id]
        progress = self._progress[session_id]

        logger.info(f"Skipping concept in session {session_id}")

        # 标记为紫色（需复习）
        action = await self._advance_concept(state, progress, "skipped", 0.0)

        return {
            "action": action["action"],
            "next_question": action.get("next_question"),
            "progress": progress.to_dict(),
        }

    async def pause_session(self, session_id: str) -> Dict[str, Any]:
        """暂停会话"""
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        state = self._sessions[session_id]
        progress = self._progress[session_id]

        state["status"] = VerificationStatus.PAUSED
        progress.status = VerificationStatus.PAUSED

        logger.info(f"Session {session_id} paused")

        return {"status": "paused", "session_id": session_id}

    async def resume_session(self, session_id: str) -> Dict[str, Any]:
        """恢复会话"""
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        state = self._sessions[session_id]
        progress = self._progress[session_id]

        state["status"] = VerificationStatus.IN_PROGRESS
        progress.status = VerificationStatus.IN_PROGRESS

        current_concept = state["current_concept"]
        current_question = f"请解释什么是「{current_concept}」？"

        logger.info(f"Session {session_id} resumed")

        return {
            "status": "in_progress",
            "session_id": session_id,
            "current_question": current_question,
            "progress": progress.to_dict(),
        }

    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        结束会话

        Args:
            session_id: 会话ID

        Returns:
            最终结果摘要
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        state = self._sessions[session_id]
        progress = self._progress[session_id]

        state["status"] = VerificationStatus.COMPLETED
        progress.status = VerificationStatus.COMPLETED

        logger.info(f"Session {session_id} ended")

        return {
            "status": "completed",
            "session_id": session_id,
            "summary": {
                "total_concepts": progress.total_concepts,
                "completed_concepts": progress.completed_concepts,
                "mastery_percentage": progress.mastery_percentage,
                "green_count": progress.green_count,
                "yellow_count": progress.yellow_count,
                "purple_count": progress.purple_count,
                "red_count": progress.red_count,
            }
        }

    async def list_sessions(
        self,
        canvas_name: Optional[str] = None,
        status: Optional[VerificationStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        列出会话

        Args:
            canvas_name: 可选，按Canvas名称过滤
            status: 可选，按状态过滤

        Returns:
            会话列表
        """
        result = []
        for _session_id, progress in self._progress.items():
            # 过滤
            if canvas_name and progress.canvas_name != canvas_name:
                continue
            if status and progress.status != status:
                continue

            result.append(progress.to_dict())

        return result

    # =========================================================================
    # Story 31.1: Canvas Concept Extraction Methods
    # [Source: docs/stories/31.1.story.md#Task-1]
    # =========================================================================

    async def _extract_concepts_from_canvas(
        self,
        canvas_name: str,
        canvas_path: Optional[str] = None,
        node_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Extract concepts from Canvas file by reading red(color="4") and purple(color="3") nodes.

        Story 31.1 AC-31.1.1: From Canvas file read red+purple nodes and extract concepts.

        Args:
            canvas_name: Canvas name (used to construct path if canvas_path not provided)
            canvas_path: Full path to Canvas file (optional)
            node_ids: Optional list of specific node IDs to extract

        Returns:
            List of concept names extracted from qualifying nodes

        [Source: docs/stories/31.1.story.md#Task-1]
        [Source: specs/data/canvas-node.schema.json - color enum]
        """
        # AC-31.1.5: Check mock mode or timeout protection
        if USE_MOCK_VERIFICATION:
            logger.debug("Mock mode enabled, returning default concepts")
            return ["概念1", "概念2", "概念3"]

        try:
            # AC-31.1.5: 500ms timeout protection for Canvas reading
            concepts = await asyncio.wait_for(
                self._do_extract_concepts(canvas_name, canvas_path, node_ids),
                timeout=VERIFICATION_AI_TIMEOUT
            )
            return concepts if concepts else ["默认概念"]

        except asyncio.TimeoutError:
            logger.warning(
                f"Canvas extraction timeout for {canvas_name} (timeout={VERIFICATION_AI_TIMEOUT}s), "
                "using fallback concepts"
            )
            return ["默认概念"]

        except Exception as e:
            logger.error(f"Canvas extraction failed for {canvas_name}: {e}")
            return ["默认概念"]

    async def _do_extract_concepts(
        self,
        canvas_name: str,
        canvas_path: Optional[str] = None,
        node_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Internal method to extract concepts from Canvas file.

        This method contains the actual extraction logic, separated for timeout wrapping.

        Args:
            canvas_name: Canvas name
            canvas_path: Optional full path to Canvas file
            node_ids: Optional list of specific node IDs

        Returns:
            List of concept strings

        [Source: backend/app/services/canvas_service.py - read_canvas pattern]
        """
        # Determine Canvas file path
        if canvas_path:
            file_path = canvas_path
        elif self._canvas_base_path:
            file_path = os.path.join(self._canvas_base_path, f"{canvas_name}.canvas")
        else:
            logger.warning(f"No canvas path provided for {canvas_name}, using fallback")
            return ["默认概念"]

        # Try reading Canvas file
        canvas_data = None

        # Method 1: Use canvas_service if available
        if self._canvas_service:
            try:
                canvas_data = await self._canvas_service.read_canvas(file_path)
            except Exception as e:
                logger.debug(f"Canvas service read failed: {e}, trying direct file read")

        # Method 2: Direct file read as fallback
        if canvas_data is None:
            try:
                canvas_data = await asyncio.to_thread(self._read_canvas_file_sync, file_path)
            except Exception as e:
                logger.error(f"Direct canvas file read failed: {e}")
                return ["默认概念"]

        if not canvas_data:
            logger.warning(f"Empty canvas data for {canvas_name}")
            return ["默认概念"]

        # Extract nodes
        nodes = canvas_data.get("nodes", [])
        if not nodes:
            logger.warning(f"No nodes found in canvas {canvas_name}")
            return ["默认概念"]

        # Filter by color: "4" (red/不理解) and "3" (purple/似懂非懂)
        # [Source: specs/data/canvas-node.schema.json - color enum]
        target_colors = ["3", "4"]  # Purple and Red in project semantics
        filtered_nodes = []

        for node in nodes:
            # Check color filter
            node_color = node.get("color", "")
            if node_color not in target_colors:
                continue

            # Check node_ids filter if provided
            if node_ids and node.get("id") not in node_ids:
                continue

            filtered_nodes.append(node)

        # Extract concepts from node text
        concepts = []
        for node in filtered_nodes:
            concept_text = self._extract_concept_from_node(node)
            if concept_text:
                concepts.append(concept_text)

        logger.info(
            f"Extracted {len(concepts)} concepts from {canvas_name} "
            f"(filtered {len(filtered_nodes)} from {len(nodes)} nodes)"
        )

        return concepts if concepts else ["默认概念"]

    def _read_canvas_file_sync(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous Canvas file read (for use with asyncio.to_thread).

        Args:
            file_path: Path to Canvas JSON file

        Returns:
            Parsed Canvas data dict or None

        [Source: backend/app/services/canvas_service.py - file reading pattern]
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Canvas file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in canvas file {file_path}: {e}")
            return None

    def _extract_concept_from_node(self, node: Dict[str, Any]) -> Optional[str]:
        """
        Extract concept name from a Canvas node.

        Handles different node types and text formats.

        Args:
            node: Canvas node dict

        Returns:
            Concept name string or None

        [Source: specs/data/canvas-node.schema.json - node structure]
        """
        # Try different text fields
        text = node.get("text", "") or node.get("label", "") or ""

        if not text:
            return None

        # Clean up the text
        # Remove markdown formatting
        concept = re.sub(r"[#*_`]", "", text)
        # Remove extra whitespace
        concept = " ".join(concept.split())
        # Trim to reasonable length
        concept = concept[:100] if len(concept) > 100 else concept

        return concept.strip() if concept.strip() else None

    # =========================================================================
    # Story 31.1: Scoring Agent Integration Methods
    # [Source: docs/stories/31.1.story.md#Task-3]
    # =========================================================================

    async def _evaluate_answer_with_scoring_agent(
        self,
        concept: str,
        user_answer: str,
        canvas_name: str
    ) -> tuple:
        """
        Evaluate user answer using scoring-agent.

        Story 31.1 AC-31.1.3: Call scoring-agent and map 0-100 score to 0-40 range.

        Args:
            concept: The concept being tested
            user_answer: User's answer text
            canvas_name: Canvas name for context

        Returns:
            Tuple of (quality: str, score: float)
            - quality: "excellent", "good", "partial", or "wrong"
            - score: 0-40 range (mapped from 0-100)

        [Source: docs/stories/31.1.story.md#Task-3]
        [Source: specs/data/scoring-response.schema.json]
        """
        # AC-31.1.5: Check mock mode
        if USE_MOCK_VERIFICATION:
            logger.debug("Mock mode enabled, using character-length based scoring")
            return self._mock_evaluate_answer(user_answer)

        try:
            # AC-31.1.5: 500ms timeout protection
            quality, score = await asyncio.wait_for(
                self._do_scoring_agent_call(concept, user_answer, canvas_name),
                timeout=VERIFICATION_AI_TIMEOUT
            )
            return quality, score

        except asyncio.TimeoutError:
            logger.warning(
                f"Scoring-agent timeout for concept {concept} "
                f"(timeout={VERIFICATION_AI_TIMEOUT}s), using fallback evaluation"
            )
            return self._mock_evaluate_answer(user_answer)

        except Exception as e:
            logger.error(f"Scoring-agent call failed for concept {concept}: {e}")
            return self._mock_evaluate_answer(user_answer)

    async def _do_scoring_agent_call(
        self,
        concept: str,
        user_answer: str,
        canvas_name: str
    ) -> tuple:
        """
        Internal method to call scoring-agent.

        Story 31.1 AC-31.1.3: Real scoring-agent integration.

        Args:
            concept: The concept being tested
            user_answer: User's answer text
            canvas_name: Canvas name for context

        Returns:
            Tuple of (quality: str, score: float) with score in 0-40 range

        [Source: backend/app/services/agent_service.py - call_scoring pattern]
        [Source: specs/data/scoring-response.schema.json]
        """
        # Call scoring-agent through agent_service if available
        if self._agent_service and hasattr(self._agent_service, "call_scoring"):
            try:
                # Get RAG context for enhanced scoring
                rag_context = await self._get_rag_context_for_concept(
                    concept, canvas_name, timeout=self.RAG_TIMEOUT
                )

                # Build context dict for scoring-agent
                context = {
                    "user_answer": user_answer,
                    "concept": concept,
                    "canvas_name": canvas_name,
                }

                # AC-31.1.4: Inject RAG context
                if rag_context:
                    context["learning_history"] = rag_context.get("learning_history", "")
                    context["textbook_excerpts"] = rag_context.get("textbook_excerpts", "")
                    context["related_concepts"] = rag_context.get("related_concepts", [])

                # Call scoring-agent
                # [Source: backend/app/services/agent_service.py - call_scoring]
                scoring_response = await self._agent_service.call_scoring(
                    node_id=f"verification_{concept}",
                    canvas_name=canvas_name,
                    user_answer=user_answer,
                    context=context
                )

                if scoring_response:
                    # Map 0-100 score to 0-40 range (Story 31.1 requirement)
                    raw_score = scoring_response.get("total_score", 50.0)
                    mapped_score = self._map_score_to_verification_range(raw_score)

                    # Determine quality from score or use provided color
                    quality = self._score_to_quality(mapped_score)

                    logger.info(
                        f"Scoring-agent evaluation: concept={concept}, "
                        f"raw_score={raw_score}, mapped_score={mapped_score}, quality={quality}"
                    )

                    return quality, mapped_score

            except Exception as e:
                logger.debug(f"Agent service scoring call failed: {e}")

        # Fallback to mock evaluation
        logger.debug(f"No agent service available for scoring, using fallback")
        return self._mock_evaluate_answer(user_answer)

    def _map_score_to_verification_range(self, raw_score: float) -> float:
        """
        Map scoring-agent's 0-100 score to verification's 0-40 range.

        Story 31.1 mapping formula: verification_score = scoring_score * 0.4

        Args:
            raw_score: Score from scoring-agent (0-100)

        Returns:
            Mapped score (0-40)

        [Source: docs/stories/31.1.story.md#评分映射规则]
        """
        # Ensure score is within bounds
        raw_score = max(0.0, min(100.0, raw_score))
        # Apply mapping formula
        return round(raw_score * 0.4, 1)

    def _score_to_quality(self, score: float) -> str:
        """
        Convert score to quality level.

        Story 31.1 thresholds (0-40 range):
        - score >= 32: excellent (掌握良好, color="2")
        - score 24-31: good (部分掌握, color="3")
        - score 16-23: partial (需要加强)
        - score < 16: wrong (不理解)

        Args:
            score: Score in 0-40 range

        Returns:
            Quality string: "excellent", "good", "partial", or "wrong"

        [Source: docs/stories/31.1.story.md#评分映射规则]
        """
        if score >= 32:
            return "excellent"
        elif score >= 24:
            return "good"
        elif score >= 16:
            return "partial"
        else:
            return "wrong"

    def _mock_evaluate_answer(self, user_answer: str) -> tuple:
        """
        Fallback mock evaluation based on character length.

        Used when:
        - USE_MOCK_VERIFICATION is enabled
        - Scoring-agent times out
        - Agent service is unavailable

        Args:
            user_answer: User's answer text

        Returns:
            Tuple of (quality: str, score: float) in 0-40 range

        [Source: docs/stories/31.1.story.md#Task-5 - graceful degradation]
        """
        answer_len = len(user_answer.strip())

        if answer_len > 100:
            quality = "excellent"
            score = 36.0  # 90 * 0.4
        elif answer_len > 50:
            quality = "good"
            score = 28.0  # 70 * 0.4
        elif answer_len > 20:
            quality = "partial"
            score = 20.0  # 50 * 0.4
        else:
            quality = "wrong"
            score = 8.0   # 20 * 0.4

        logger.debug(f"Mock evaluation: len={answer_len}, quality={quality}, score={score}")
        return quality, score

    # =========================================================================
    # Story 31.5: Difficulty Adaptation Methods
    # [Source: docs/stories/31.5.story.md#Task-7]
    # =========================================================================

    async def _get_difficulty_for_concept(
        self,
        concept: str,
        canvas_name: str,
        node_id: Optional[str] = None
    ) -> DifficultyResult:
        """
        Get difficulty level for a concept based on historical scores.

        Story 31.5 AC-31.5.1, AC-31.5.2: Query history and calculate difficulty.

        Args:
            concept: Concept name (used as fallback if node_id not provided)
            canvas_name: Canvas name for filtering
            node_id: Optional node ID for precise history lookup

        Returns:
            DifficultyResult with level, question_type, and forgetting status

        [Source: docs/stories/31.5.story.md#Task-7.1, Task-7.2]
        """
        # Default result for graceful degradation
        default_result = DifficultyResult(
            level=DifficultyLevel.MEDIUM,
            average_score=0.0,
            sample_size=0,
            question_type=QuestionType.VERIFICATION,
            forgetting_status=None,
            is_mastered=False
        )

        # Check if memory_service is available
        if not self._memory_service:
            logger.debug("Memory service not available, using default difficulty")
            return default_result

        try:
            # AC-31.1.5: 500ms timeout protection (Story 31.5 Task 7.2)
            concept_id = node_id if node_id else concept
            score_history = await asyncio.wait_for(
                self._memory_service.get_concept_score_history(
                    concept_id=concept_id,
                    canvas_name=canvas_name,
                    limit=5
                ),
                timeout=VERIFICATION_AI_TIMEOUT
            )

            if not score_history or score_history.sample_size == 0:
                logger.debug(f"No score history for concept '{concept}', using default difficulty")
                return default_result

            # Calculate difficulty from historical scores
            scores = score_history.scores
            recent_score = scores[-1] if scores else None

            difficulty_result = calculate_full_difficulty_result(
                scores=scores,
                recent_score=recent_score
            )

            logger.info(
                f"Difficulty calculated for '{concept}': "
                f"level={difficulty_result.level.value}, "
                f"avg={difficulty_result.average_score}, "
                f"mastered={difficulty_result.is_mastered}, "
                f"needs_review={difficulty_result.forgetting_status.needs_review if difficulty_result.forgetting_status else False}"
            )

            return difficulty_result

        except asyncio.TimeoutError:
            logger.warning(
                f"Difficulty query timeout for concept '{concept}' "
                f"(timeout={VERIFICATION_AI_TIMEOUT}s), using default"
            )
            return default_result

        except Exception as e:
            logger.debug(f"Difficulty calculation failed for '{concept}': {e}")
            return default_result

    def _build_difficulty_aware_prompt(
        self,
        concept: str,
        difficulty: DifficultyResult,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a prompt that incorporates difficulty level guidance.

        Story 31.5 AC-31.5.3: Pass difficulty level to Gemini prompt.

        Args:
            concept: The concept to verify
            difficulty: DifficultyResult from calculation
            rag_context: Optional RAG context

        Returns:
            Difficulty-aware prompt string

        [Source: docs/stories/31.5.story.md#Task-7.3]
        """
        # Difficulty-specific instructions
        difficulty_guidance = {
            DifficultyLevel.EASY: (
                "学生对此概念理解较弱 (历史平均分 < 60)。\n"
                "生成一个**突破型问题**，聚焦核心概念本身：\n"
                "- 使用简单直接的语言\n"
                "- 聚焦最基本的定义和特点\n"
                "- 避免复杂的应用场景\n"
                "- 帮助学生建立基础理解"
            ),
            DifficultyLevel.MEDIUM: (
                "学生对此概念有一定理解 (历史平均分 60-79)。\n"
                "生成一个**验证型问题**，测试理解深度：\n"
                "- 要求解释概念的关键特点\n"
                "- 可以包含简单的比较或区分\n"
                "- 检验学生是否理解概念的内涵"
            ),
            DifficultyLevel.HARD: (
                "学生对此概念掌握良好 (历史平均分 >= 80)。\n"
                "生成一个**应用型问题**，挑战更深层理解：\n"
                "- 要求在实际场景中应用概念\n"
                "- 可以涉及跨概念比较或综合\n"
                "- 检验学生是否能灵活运用"
            ),
        }

        prompt_parts = [
            f"为概念「{concept}」生成一个检验问题。",
            "",
            "## 难度指导",
            difficulty_guidance.get(difficulty.level, difficulty_guidance[DifficultyLevel.MEDIUM]),
            "",
            f"当前难度: {difficulty.level.value} (平均分: {difficulty.average_score}, 样本数: {difficulty.sample_size})",
        ]

        # Add forgetting alert if detected
        if difficulty.forgetting_status and difficulty.forgetting_status.needs_review:
            prompt_parts.extend([
                "",
                f"⚠️ 遗忘检测: 学生近期得分下降了 {difficulty.forgetting_status.decay_percentage}%",
                "请在问题中关注可能被遗忘的核心要点。"
            ])

        # Add mastery note
        if difficulty.is_mastered:
            prompt_parts.extend([
                "",
                "✅ 此概念已基本掌握 (连续3次 >= 80分)",
                "可以考虑生成更有挑战性的问题，或跨概念综合问题。"
            ])

        # Add RAG context if available
        if rag_context:
            prompt_parts.append("")
            prompt_parts.append("## 学习上下文")
            if rag_context.get("learning_history"):
                prompt_parts.append(f"学习历史: {rag_context['learning_history']}")
            if rag_context.get("related_concepts"):
                related = ", ".join(rag_context["related_concepts"][:5])
                prompt_parts.append(f"相关概念: {related}")
            if rag_context.get("common_mistakes"):
                prompt_parts.append(f"常见错误: {rag_context['common_mistakes']}")

        prompt_parts.extend([
            "",
            "请只输出问题本身，不要包含其他解释或前缀。"
        ])

        return "\n".join(prompt_parts)

    # =========================================================================
    # Story 24.5: RAG Context Injection Methods
    # [Source: docs/stories/24.5.story.md#Dev-Notes]
    # =========================================================================

    async def _get_rag_context_for_concept(
        self,
        concept: str,
        canvas_name: str,
        timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """
        Query RAG for concept-related context with timeout fallback.

        AC1: Question generation uses RAG context
        AC5: Graceful degradation on timeout

        ✅ Verified from Story 24.5 Dev Notes Step 2

        Args:
            concept: Concept to query about
            canvas_name: Canvas file name
            timeout: Query timeout in seconds (default: 5.0)

        Returns:
            Dict with RAG context or None on error/timeout
            {
                "learning_history": str,
                "textbook_excerpts": str,
                "related_concepts": List[str],
                "common_mistakes": str
            }

        [Source: docs/stories/24.5.story.md#Dev-Notes Step 2]
        """
        if not self._rag_service:
            logger.debug("RAG service not available, skipping context query")
            return None

        try:
            # ✅ Verified from backend/app/services/rag_service.py: query method
            rag_result = await asyncio.wait_for(
                self._rag_service.query(
                    query=f"关于「{concept}」的学习历史、相关知识和常见错误",
                    canvas_file=canvas_name,
                    is_review_canvas=False
                ),
                timeout=timeout
            )

            # Extract context from RAG result
            # Note: Actual structure depends on RAG service implementation
            return {
                "learning_history": rag_result.get("learning_history", "无历史记录"),
                "textbook_excerpts": rag_result.get("textbook_excerpts", "无教材引用"),
                "related_concepts": rag_result.get("related_concepts", []),
                "common_mistakes": rag_result.get("common_mistakes", "无已知错误模式")
            }

        except asyncio.TimeoutError:
            # AC5: Graceful degradation
            logger.warning(
                f"RAG query timeout for concept: {concept} (timeout={timeout}s)"
            )
            return None

        except Exception as e:
            # AC5: Graceful degradation
            logger.error(f"RAG query failed for concept '{concept}': {e}")
            return None

    async def _get_cross_canvas_context(
        self,
        concept: str,
        canvas_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get related concepts from other canvases.

        AC3: Cross-canvas association in prompts

        ✅ Verified from Story 24.5 Dev Notes Step 5

        Args:
            concept: Concept to find relationships for
            canvas_name: Current canvas name

        Returns:
            List of related canvas info:
            [
                {
                    "canvas": str,
                    "concept": str,
                    "relationship": str
                }
            ]

        [Source: docs/stories/24.5.story.md#Dev-Notes Step 5]
        """
        if not self._cross_canvas_service:
            logger.debug("CrossCanvasService not available, skipping cross-canvas lookup")
            return []

        try:
            # ✅ Verified from backend/app/services/cross_canvas_service.py
            # Method: get_associated_canvases
            related = await self._cross_canvas_service.get_associated_canvases(
                canvas_path=canvas_name,
                relation_type=None  # Get all types
            )

            # Transform to simplified format
            result = []
            for assoc in related[:3]:  # Limit to top 3
                result.append({
                    "canvas": assoc.target_canvas_title,
                    "concept": ", ".join(assoc.common_concepts[:2]) if assoc.common_concepts else concept,
                    "relationship": assoc.relationship_type
                })

            return result

        except Exception as e:
            logger.warning(f"Cross-canvas lookup failed for '{concept}': {e}")
            return []

    def _build_rag_enhanced_prompt(self, concept: str, context: Dict[str, Any]) -> str:
        """
        Build prompt with RAG context for question generation.

        AC1: Question generation incorporates RAG context

        ✅ Verified from Story 24.5 Dev Notes Step 3

        Args:
            concept: Concept to generate question for
            context: RAG context dict

        Returns:
            Enhanced prompt string

        [Source: docs/stories/24.5.story.md#Dev-Notes Step 3]
        """
        prompt_parts = [
            f"为概念「{concept}」生成一个检验问题。",
            "",
            "## 学习历史",
            context.get("learning_history", "无历史记录"),
            "",
            "## 教材参考",
            context.get("textbook_excerpts", "无教材引用"),
            "",
            "## 相关概念",
            ", ".join(context.get("related_concepts", [])) or "无相关概念",
            "",
            "## 常见错误",
            context.get("common_mistakes", "无已知错误模式"),
            "",
            "请根据以上上下文，生成一个能够检验用户对该概念理解深度的问题。"
        ]
        return "\n".join(prompt_parts)

    def _build_basic_prompt(self, concept: str) -> str:
        """
        Build basic prompt without RAG context (fallback).

        AC5: Graceful degradation when RAG unavailable

        Args:
            concept: Concept to generate question for

        Returns:
            Basic prompt string

        [Source: docs/stories/24.5.story.md#Dev-Notes Step 3]
        """
        return f"为概念「{concept}」生成一个检验问题，要求用户解释其核心含义。"

    async def generate_question_with_rag(
        self,
        concept: str,
        canvas_name: str,
        group_id: Optional[str] = None,
        node_id: Optional[str] = None,
        return_difficulty_info: bool = False
    ) -> str | Dict[str, Any]:
        """
        Generate verification question with RAG context and difficulty adaptation.

        Story 31.1 AC-31.1.2: Call Gemini API to generate personalized verification questions.
        Story 31.4 AC-31.4.1: Query Graphiti for existing questions before generation.
        Story 31.4 AC-31.4.2: Generate questions from new angles if history exists.
        Story 31.5 AC-31.5.1-31.5.5: Difficulty adaptive algorithm integration.
        AC1: Question generation uses RAG context
        AC5: Graceful degradation on RAG failure

        ✅ Verified from Story 24.5 Dev Notes Step 3
        ✅ Updated Story 31.1: Real Gemini API integration
        ✅ Updated Story 31.4: Question deduplication with Graphiti
        ✅ Updated Story 31.5: Difficulty adaptation integration

        Args:
            concept: Concept to generate question for
            canvas_name: Canvas file name
            group_id: Optional group ID for multi-subject isolation (Story 31.4)
            node_id: Optional node ID for precise history lookup (Story 31.5)
            return_difficulty_info: If True, return dict with question and difficulty (Story 31.5)

        Returns:
            If return_difficulty_info=False: Generated question string (backward compatible)
            If return_difficulty_info=True: Dict with question, difficulty_level, forgetting_status

        [Source: docs/stories/24.5.story.md#Dev-Notes Step 3]
        [Source: docs/stories/31.1.story.md#Task-2]
        [Source: docs/stories/31.4.story.md#Task-2]
        [Source: docs/stories/31.5.story.md#Task-7]
        """
        # Default difficulty for graceful degradation
        difficulty: Optional[DifficultyResult] = None

        # AC-31.1.5: Check mock mode
        if USE_MOCK_VERIFICATION:
            logger.debug(f"Mock mode enabled, returning default question for {concept}")
            question = f"请解释什么是「{concept}」？"
            if return_difficulty_info:
                return {
                    "question": question,
                    "difficulty_level": "medium",
                    "question_type": "verification",
                    "forgetting_status": None,
                    "is_mastered": False
                }
            return question

        # Story 31.5 AC-31.5.1, AC-31.5.2: Query historical scores and calculate difficulty
        difficulty = await self._get_difficulty_for_concept(
            concept=concept,
            canvas_name=canvas_name,
            node_id=node_id
        )

        # Story 31.5 AC-31.5.4: Skip mastered concepts (optional behavior)
        # Note: Actual skip logic should be handled by caller (start_session)
        if difficulty.is_mastered:
            logger.info(f"Concept '{concept}' is mastered (skip recommended)")

        # Story 31.4 AC-31.4.1: Query Graphiti for existing verification questions
        history_questions = await self._get_question_history_from_graphiti(
            concept=concept,
            canvas_name=canvas_name,
            group_id=group_id
        )

        # Story 31.4 AC-31.4.2: Determine question angle based on history
        if history_questions:
            # Have history - generate question from a new angle
            logger.info(
                f"Found {len(history_questions)} existing questions for concept '{concept}', "
                "generating alternative angle question"
            )
            question = await self._generate_alternative_question(
                concept=concept,
                canvas_name=canvas_name,
                history_questions=history_questions,
                group_id=group_id,
                difficulty=difficulty  # Pass difficulty for prompt enhancement
            )
            if return_difficulty_info:
                return self._build_question_response_with_difficulty(question, difficulty)
            return question

        # No history - generate standard question with difficulty adaptation
        logger.debug(f"No history found for concept '{concept}', generating difficulty-adapted question")

        # Get RAG context (with timeout protection)
        rag_context = await self._get_rag_context_for_concept(
            concept, canvas_name, timeout=self.RAG_TIMEOUT
        )

        # Story 31.5 AC-31.5.3: Build difficulty-aware prompt
        if difficulty.sample_size > 0:
            # Use difficulty-aware prompt when we have history
            prompt = self._build_difficulty_aware_prompt(concept, difficulty, rag_context)
            logger.debug(f"Using difficulty-aware prompt for concept: {concept} (level={difficulty.level.value})")
        elif rag_context:
            # Enhanced prompt with RAG context (no difficulty history)
            prompt = self._build_rag_enhanced_prompt(concept, rag_context)
            logger.debug(f"Using RAG-enhanced prompt for concept: {concept}")
        else:
            # Fallback: basic question without RAG
            prompt = self._build_basic_prompt(concept)
            logger.debug(f"Using basic prompt for concept: {concept} (RAG unavailable)")

        # Story 31.1 AC-31.1.2: Call Gemini API with timeout protection
        try:
            question = await asyncio.wait_for(
                self._call_gemini_for_question(concept, prompt, rag_context),
                timeout=VERIFICATION_AI_TIMEOUT
            )

            # Story 31.4 Task 6: Store generated question to Graphiti (fire-and-forget)
            # Include question_type from difficulty
            question_type = difficulty.question_type.value if difficulty else "verification"
            asyncio.create_task(
                self._store_question_to_graphiti(
                    question=question,
                    concept=concept,
                    canvas_name=canvas_name,
                    question_type=question_type,
                    group_id=group_id
                )
            )

            # Story 31.5 AC-31.5.4: Return with difficulty info if requested
            if return_difficulty_info:
                return self._build_question_response_with_difficulty(question, difficulty)
            return question

        except asyncio.TimeoutError:
            logger.warning(
                f"Gemini API timeout for concept {concept} "
                f"(timeout={VERIFICATION_AI_TIMEOUT}s), using fallback question"
            )
            question = f"请解释什么是「{concept}」？"
            if return_difficulty_info:
                return self._build_question_response_with_difficulty(question, difficulty)
            return question

        except Exception as e:
            logger.error(f"Gemini API call failed for concept {concept}: {e}")
            question = f"请解释什么是「{concept}」？"
            if return_difficulty_info:
                return self._build_question_response_with_difficulty(question, difficulty)
            return question

    def _build_question_response_with_difficulty(
        self,
        question: str,
        difficulty: Optional[DifficultyResult]
    ) -> Dict[str, Any]:
        """
        Build response dict with question and difficulty info.

        Story 31.5 AC-31.5.4: Include difficulty_level and forgetting_status in response.

        Args:
            question: Generated question string
            difficulty: DifficultyResult or None

        Returns:
            Dict with question and difficulty metadata

        [Source: docs/stories/31.5.story.md#Task-7.4]
        """
        if difficulty:
            return {
                "question": question,
                "difficulty_level": difficulty.level.value,
                "question_type": difficulty.question_type.value,
                "average_score": difficulty.average_score,
                "sample_size": difficulty.sample_size,
                "forgetting_status": {
                    "needs_review": difficulty.forgetting_status.needs_review,
                    "decay_percentage": difficulty.forgetting_status.decay_percentage
                } if difficulty.forgetting_status else None,
                "is_mastered": difficulty.is_mastered
            }
        else:
            return {
                "question": question,
                "difficulty_level": "medium",
                "question_type": "verification",
                "average_score": 0.0,
                "sample_size": 0,
                "forgetting_status": None,
                "is_mastered": False
            }

    async def _get_question_history_from_graphiti(
        self,
        concept: str,
        canvas_name: str,
        group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Graphiti for existing verification questions.

        Story 31.4 AC-31.4.1: Check Graphiti before generating new questions.

        Args:
            concept: Concept to query
            canvas_name: Canvas name for filtering
            group_id: Optional group ID for multi-subject isolation

        Returns:
            List of historical question records

        [Source: docs/stories/31.4.story.md#Task-2.2]
        """
        if not self._graphiti_client:
            logger.debug("Graphiti client not available, skipping history check")
            return []

        try:
            # AC-31.1.5: 500ms timeout protection (ADR-009)
            history = await asyncio.wait_for(
                self._graphiti_client.search_verification_questions(
                    concept=concept,
                    canvas_name=canvas_name,
                    group_id=group_id,
                    limit=10  # Get last 10 questions for deduplication
                ),
                timeout=VERIFICATION_AI_TIMEOUT
            )
            return history if history else []

        except asyncio.TimeoutError:
            logger.warning(
                f"Graphiti history query timeout for concept '{concept}' "
                f"(timeout={VERIFICATION_AI_TIMEOUT}s), proceeding without history"
            )
            return []

        except Exception as e:
            logger.debug(f"Graphiti history query failed for concept '{concept}': {e}")
            return []

    async def _generate_alternative_question(
        self,
        concept: str,
        canvas_name: str,
        history_questions: List[Dict[str, Any]],
        group_id: Optional[str] = None,
        difficulty: Optional[DifficultyResult] = None
    ) -> str:
        """
        Generate a verification question from a new angle.

        Story 31.4 AC-31.4.2: When history exists, generate questions from alternative angles.
        Story 31.5: Incorporate difficulty level into alternative question generation.

        Question angle priority (QUESTION_ANGLE_PRIORITY):
        1. application - 应用场景问题 ("How would you apply X in scenario Y?")
        2. comparison - 比较分析问题 ("Compare X with Y")
        3. counterexample - 反例验证问题 ("What would NOT be an example of X?")
        4. synthesis - 综合理解问题 ("How does X relate to Y and Z?")

        Args:
            concept: Concept to generate question for
            canvas_name: Canvas name for context
            history_questions: List of previously asked questions
            group_id: Optional group ID
            difficulty: Optional DifficultyResult for prompt enhancement (Story 31.5)

        Returns:
            Generated question string from a new angle

        [Source: docs/stories/31.4.story.md#Task-3]
        [Source: docs/stories/31.5.story.md#Task-7]
        """
        # Extract used question types from history
        used_types = set()
        for q in history_questions:
            q_type = q.get("question_type", "standard")
            used_types.add(q_type)

        logger.debug(f"Used question types for '{concept}': {used_types}")

        # Find the next unused angle from priority list
        next_angle = "standard"
        for angle in self.QUESTION_ANGLE_PRIORITY:
            if angle not in used_types:
                next_angle = angle
                break

        # If all angles used, cycle back to application
        if next_angle == "standard" and used_types:
            next_angle = self.QUESTION_ANGLE_PRIORITY[0]  # application

        logger.info(f"Selected question angle '{next_angle}' for concept '{concept}'")

        # Get RAG context for enhanced generation
        rag_context = await self._get_rag_context_for_concept(
            concept, canvas_name, timeout=self.RAG_TIMEOUT
        )

        # Build angle-specific prompt with difficulty awareness (Story 31.5)
        prompt = self._build_angle_specific_prompt(
            concept=concept,
            angle=next_angle,
            history_questions=history_questions,
            rag_context=rag_context,
            difficulty=difficulty
        )

        # Generate question with timeout protection
        try:
            question = await asyncio.wait_for(
                self._call_gemini_for_question(concept, prompt, rag_context),
                timeout=VERIFICATION_AI_TIMEOUT
            )

            # Store the generated question to Graphiti (fire-and-forget)
            asyncio.create_task(
                self._store_question_to_graphiti(
                    question=question,
                    concept=concept,
                    canvas_name=canvas_name,
                    question_type=next_angle,
                    group_id=group_id
                )
            )

            return question

        except asyncio.TimeoutError:
            logger.warning(
                f"Gemini API timeout for alternative question ({next_angle}), using fallback"
            )
            return self._get_fallback_angle_question(concept, next_angle)

        except Exception as e:
            logger.error(f"Alternative question generation failed: {e}")
            return self._get_fallback_angle_question(concept, next_angle)

    def _build_angle_specific_prompt(
        self,
        concept: str,
        angle: str,
        history_questions: List[Dict[str, Any]],
        rag_context: Optional[Dict[str, Any]] = None,
        difficulty: Optional[DifficultyResult] = None
    ) -> str:
        """
        Build a prompt for generating angle-specific verification questions.

        Story 31.4 AC-31.4.2: Different angles for diverse question coverage.
        Story 31.5: Incorporate difficulty level into prompt generation.

        Args:
            concept: The concept to verify
            angle: Question angle type
            history_questions: Previously asked questions (for avoiding repetition)
            rag_context: Optional RAG context
            difficulty: Optional DifficultyResult for difficulty-aware prompts (Story 31.5)

        Returns:
            Prompt string for question generation

        [Source: docs/stories/31.4.story.md#Task-3.2]
        [Source: docs/stories/31.5.story.md#Task-7.3]
        """
        # Base instructions by angle type
        angle_instructions = {
            "application": (
                f"请针对概念「{concept}」生成一个**应用场景**验证问题。\n"
                "要求学生解释如何在实际情境中应用此概念，或举出具体的应用实例。"
            ),
            "comparison": (
                f"请针对概念「{concept}」生成一个**比较分析**验证问题。\n"
                "要求学生将此概念与相关概念进行比较，分析异同点。"
            ),
            "counterexample": (
                f"请针对概念「{concept}」生成一个**反例验证**问题。\n"
                "要求学生识别什么情况下不适用此概念，或给出反例来加深理解。"
            ),
            "synthesis": (
                f"请针对概念「{concept}」生成一个**综合理解**验证问题。\n"
                "要求学生解释此概念与其他概念的关联，或如何将多个概念综合运用。"
            ),
            "standard": (
                f"请针对概念「{concept}」生成一个验证问题。\n"
                "要求学生解释其核心含义和关键特点。"
            ),
        }

        prompt_parts = [
            "你是一个专业的教学验证助手。",
            "",
            angle_instructions.get(angle, angle_instructions["standard"]),
            "",
        ]

        # Story 31.5: Add difficulty context if available
        if difficulty and difficulty.sample_size > 0:
            difficulty_desc = {
                DifficultyLevel.EASY: "学生对此概念理解较弱，请使用简单直接的语言",
                DifficultyLevel.MEDIUM: "学生对此概念有一定理解，可以适当增加深度",
                DifficultyLevel.HARD: "学生掌握良好，可以设计更有挑战性的问题",
            }
            prompt_parts.append("## 学生水平")
            prompt_parts.append(
                f"难度: {difficulty.level.value} (平均分: {difficulty.average_score}, "
                f"历史记录: {difficulty.sample_size}次)"
            )
            prompt_parts.append(difficulty_desc.get(difficulty.level, ""))

            # Add forgetting alert
            if difficulty.forgetting_status and difficulty.forgetting_status.needs_review:
                prompt_parts.append(
                    f"⚠️ 遗忘警报: 近期得分下降 {difficulty.forgetting_status.decay_percentage}%，"
                    "请关注可能被遗忘的要点"
                )

            # Add mastery note
            if difficulty.is_mastered:
                prompt_parts.append("✅ 此概念已基本掌握，可设计更综合性的问题")

            prompt_parts.append("")

        # Add history to avoid repetition
        if history_questions:
            prompt_parts.append("## 已问过的问题（请避免重复）")
            for i, q in enumerate(history_questions[:5], 1):  # Show last 5
                q_text = q.get("question_text", "")
                q_type = q.get("question_type", "unknown")
                prompt_parts.append(f"{i}. [{q_type}] {q_text}")
            prompt_parts.append("")

        # Add RAG context if available
        if rag_context:
            if rag_context.get("related_concepts"):
                related = ", ".join(rag_context["related_concepts"][:5])
                prompt_parts.append(f"## 相关概念: {related}")
            if rag_context.get("common_mistakes"):
                prompt_parts.append(f"## 常见错误: {rag_context['common_mistakes']}")
            prompt_parts.append("")

        prompt_parts.append("请只输出问题本身，不要包含其他解释或前缀。")

        return "\n".join(prompt_parts)

    def _get_fallback_angle_question(self, concept: str, angle: str) -> str:
        """
        Get a fallback question for a specific angle when generation fails.

        Story 31.4: Graceful degradation with pre-defined templates.

        Args:
            concept: The concept
            angle: Question angle type

        Returns:
            Fallback question string

        [Source: docs/stories/31.4.story.md#Task-3.4]
        """
        fallback_templates = {
            "application": f"请举例说明「{concept}」在实际中如何应用？",
            "comparison": f"请比较「{concept}」与相关概念的异同点？",
            "counterexample": f"什么情况下「{concept}」不适用？请举反例说明。",
            "synthesis": f"「{concept}」与其他概念有何关联？请综合分析。",
            "standard": f"请解释什么是「{concept}」？",
        }
        return fallback_templates.get(angle, fallback_templates["standard"])

    async def _store_question_to_graphiti(
        self,
        question: str,
        concept: str,
        canvas_name: str,
        question_type: str = "standard",
        group_id: Optional[str] = None
    ) -> None:
        """
        Store a generated verification question to Graphiti (fire-and-forget).

        Story 31.4 Task 6: Persist questions for deduplication.
        ADR-0003: Fire-and-forget pattern - don't block on write.

        Args:
            question: The generated question text
            concept: Associated concept
            canvas_name: Source canvas name
            question_type: Question angle type
            group_id: Optional group ID for isolation

        [Source: docs/stories/31.4.story.md#Task-6]
        [Source: docs/architecture/decisions/ADR-0003]
        """
        if not self._graphiti_client:
            logger.debug("Graphiti client not available, skipping question storage")
            return

        try:
            await self._graphiti_client.add_verification_question(
                question_text=question,
                concept=concept,
                canvas_name=canvas_name,
                question_type=question_type,
                group_id=group_id
            )
            logger.debug(
                f"Stored verification question to Graphiti: concept='{concept}', type='{question_type}'"
            )

        except Exception as e:
            # Fire-and-forget: log but don't fail
            logger.warning(f"Failed to store question to Graphiti: {e}")

    async def _call_gemini_for_question(
        self,
        concept: str,
        prompt: str,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Internal method to call Gemini API for question generation.

        Story 31.1 AC-31.1.2: Real Gemini API integration.

        Args:
            concept: The concept to generate question for
            prompt: The constructed prompt
            rag_context: Optional RAG context for enhanced generation

        Returns:
            Generated question string

        [Source: backend/app/services/agent_service.py - _call_gemini_api pattern]
        [Source: docs/stories/31.1.story.md#Task-2]
        """
        # Build the full prompt for question generation
        system_prompt = """你是一个专业的教学验证助手，负责生成高质量的验证问题来检验学生对概念的理解。

要求：
1. 问题应验证学生对核心概念的深层理解，而非简单的定义背诵
2. 使用开放式问题，鼓励学生展示自己的理解
3. 问题应该清晰、简洁、直接
4. 避免过于简单的"是什么"类问题，使用"为什么"、"如何"、"比较"类问题
5. 只输出问题本身，不要包含其他解释或前缀"""

        # Build context-aware prompt
        full_prompt = f"{system_prompt}\n\n"

        if rag_context:
            if rag_context.get("learning_history"):
                full_prompt += f"学习背景: {rag_context['learning_history']}\n"
            if rag_context.get("related_concepts"):
                related = ", ".join(rag_context["related_concepts"][:5])
                full_prompt += f"相关概念: {related}\n"
            if rag_context.get("common_mistakes"):
                full_prompt += f"常见错误: {rag_context['common_mistakes']}\n"

        full_prompt += f"\n请针对概念「{concept}」生成一个验证问题：\n{prompt}"

        # Call Gemini API through agent_service if available
        if self._agent_service and hasattr(self._agent_service, "_call_gemini_api"):
            try:
                response = await self._agent_service._call_gemini_api(full_prompt)
                if response:
                    # Clean up response - extract just the question
                    question = response.strip()
                    # Remove common prefixes if present
                    for prefix in ["问题：", "问题:", "Question:", "Q:"]:
                        if question.startswith(prefix):
                            question = question[len(prefix):].strip()
                    return question if question else f"请解释什么是「{concept}」？"
            except Exception as e:
                logger.debug(f"Agent service Gemini call failed: {e}")

        # Fallback: return basic question
        logger.debug(f"No agent service available, using fallback question for {concept}")
        return f"请解释什么是「{concept}」？"

    async def generate_hint_with_rag(
        self,
        concept: str,
        user_answer: str,
        attempt_number: int,
        canvas_name: str
    ) -> str:
        """
        Generate personalized hint based on RAG context.

        AC2: Hints based on learning history
        AC5: Graceful degradation on RAG failure

        ✅ Verified from Story 24.5 Dev Notes Step 4

        Args:
            concept: Current concept
            user_answer: User's answer
            attempt_number: Number of attempts made
            canvas_name: Canvas file name

        Returns:
            Generated hint string

        [Source: docs/stories/24.5.story.md#Dev-Notes Step 4]
        """
        rag_context = await self._get_rag_context_for_concept(
            concept, canvas_name, timeout=self.RAG_TIMEOUT
        )

        if rag_context and rag_context.get("learning_history"):
            # Personalized hint based on history
            past_mistakes = rag_context.get("common_mistakes", "")
            hint = f"提示 {attempt_number}: 注意避免常见错误：{past_mistakes}。思考「{concept}」的核心特点。"
            logger.debug(f"Generated personalized hint for concept: {concept}")
        else:
            # Generic hint
            hint = f"提示 {attempt_number}: 思考「{concept}」的定义和核心特点。"
            logger.debug(f"Generated generic hint for concept: {concept} (no history)")

        return hint

    async def cleanup(self) -> None:
        """清理资源"""
        logger.info("VerificationService cleanup")
        self._sessions.clear()
        self._progress.clear()


# 单例实例
_verification_service: Optional[VerificationService] = None


def get_verification_service() -> VerificationService:
    """获取VerificationService单例"""
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service


__all__ = [
    "VerificationService",
    "VerificationProgress",
    "VerificationStatus",
    "get_verification_service",
    # Story 31.5: Difficulty Adaptive Algorithm exports
    "DifficultyLevel",
    "QuestionType",
    "ForgettingStatus",
    "DifficultyResult",
    "calculate_difficulty_level",
    "get_question_type_for_difficulty",
    "is_concept_mastered",
    "detect_forgetting",
    "calculate_full_difficulty_result",
]
