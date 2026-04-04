"""
Exam Domain Gateway — 考试与评分统一入口

Strangler Fig Pattern: 所有外部调用应通过此 gateway 访问 exam 领域。

包含: exam_service, exam_service_ext, question_generator, verification_service,
       autoscore, scoring_faithfulness, difficulty_matcher, calibration_tracker,
       topic_clustering
"""

from __future__ import annotations

# ── 考试会话 ──
from app.services.exam_service import get_exam_service, ExamService

# ── 出题 ──
from app.services.question_generator import QuestionGenerator

# ── 验证画布（苏格拉底式） ──
from app.services.verification_service import VerificationService

# ── 评分 ──
from app.services.autoscore import AutoScorer

# ── 评分可信度 ──
from app.services.scoring_faithfulness import ScoringFaithfulnessChecker

# ── 难度匹配 ──
from app.services.difficulty_matcher import DifficultyMatcher

# ── 元认知校准（Area9） ──
from app.services.calibration_tracker import (
    classify_quadrant,
    record_calibration,
    get_calibration_summary,
    compute_signed_bias,
)

# ── 话题聚类（验证画布用） ──
from app.services.topic_clustering import TopicClusterer

__all__ = [
    "get_exam_service",
    "ExamService",
    "QuestionGenerator",
    "VerificationService",
    "AutoScorer",
    "ScoringFaithfulnessChecker",
    "DifficultyMatcher",
    "classify_quadrant",
    "record_calibration",
    "get_calibration_summary",
    "compute_signed_bias",
    "TopicClusterer",
]
