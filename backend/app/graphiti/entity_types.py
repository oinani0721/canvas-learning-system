# Canvas Learning System - Graphiti Entity Type Schemas
# Story 3.6: Tips Annotation + Error Archiving (AC-2, AC-3, AC-4)
#
# Defines Pydantic schemas for structured Graphiti entities:
#   - LearningTip: User-annotated knowledge tips from dialogue
#   - Misconception: Agent-detected error records with 4-type classification
#
# Edge types for Neo4j relationships:
#   - HAS_TIP: ConceptNode -> LearningTip
#   - HAS_MISCONCEPTION: ConceptNode -> Misconception
#
# [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 5]

from datetime import datetime, timezone
from enum import Enum
from typing import List

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Error Type Enum
# ═══════════════════════════════════════════════════════════════════════════════


class ErrorType(str, Enum):
    """
    4-type error classification for misconception archiving.

    [Source: architecture.md#Requirements Overview]
    """

    PROBLEM_FRAMING = "problem_framing"  # 破题错误: 审题失误, 条件遗漏
    REASONING_FALLACY = "reasoning_fallacy"  # 推理谬误: 逻辑跳步, 因果倒置
    KNOWLEDGE_GAP = "knowledge_gap"  # 知识点缺失: 缺前置知识
    SUPERFICIAL = "superficial"  # 似懂非懂: 能复述不能应用


class RemedyStrategy(str, Enum):
    """
    Differentiated remedy strategies mapped to error types.

    [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#AC-4]
    """

    SAME_STRUCTURE_NEW_PROBLEM = "same_structure_new_problem"  # 同结构新题练习
    FIND_ERROR_COUNTEREXAMPLE = "find_error_counterexample"  # 找错练习 + 反例构造
    BACKTRACK_DEFINITION = "backtrack_definition"  # 回退到定义题
    DISCRIMINATION_TRANSFER = "discrimination_transfer"  # 辨析题 + 迁移应用题


# ═══════════════════════════════════════════════════════════════════════════════
# Remedy Strategy Mapping
# ═══════════════════════════════════════════════════════════════════════════════

ERROR_TYPE_TO_REMEDY: dict[ErrorType, RemedyStrategy] = {
    ErrorType.PROBLEM_FRAMING: RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM,
    ErrorType.REASONING_FALLACY: RemedyStrategy.FIND_ERROR_COUNTEREXAMPLE,
    ErrorType.KNOWLEDGE_GAP: RemedyStrategy.BACKTRACK_DEFINITION,
    ErrorType.SUPERFICIAL: RemedyStrategy.DISCRIMINATION_TRANSFER,
}

# Human-readable descriptions for each error type
ERROR_TYPE_DESCRIPTIONS: dict[ErrorType, dict[str, str]] = {
    ErrorType.PROBLEM_FRAMING: {
        "label_zh": "破题错误",
        "description": "审题失误、条件遗漏、问题理解偏差",
        "remedy_zh": "同结构新题（改数字不改结构）",
    },
    ErrorType.REASONING_FALLACY: {
        "label_zh": "推理谬误",
        "description": "逻辑跳步、因果倒置、不当归纳",
        "remedy_zh": "找错练习 + 反例构造",
    },
    ErrorType.KNOWLEDGE_GAP: {
        "label_zh": "知识点缺失",
        "description": "缺前置知识、概念未学",
        "remedy_zh": "回退到定义题 + 基础概念补充",
    },
    ErrorType.SUPERFICIAL: {
        "label_zh": "似懂非懂",
        "description": "能复述不能应用、表面理解",
        "remedy_zh": "辨析题 + 迁移应用（换场景）",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Tag Enum for Tips
# ═══════════════════════════════════════════════════════════════════════════════


class TipTag(str, Enum):
    """Predefined tag categories for tip annotations."""

    IMPORTANT = "important"  # 重要 (red)
    CONFUSED = "confused"  # 困惑 (yellow)
    INSPIRATION = "inspiration"  # 灵感 (green)
    REVIEW = "review"  # 待复习 (blue)


# ═══════════════════════════════════════════════════════════════════════════════
# LearningTip Entity Schema
# ═══════════════════════════════════════════════════════════════════════════════


class LearningTip(BaseModel):
    """
    A user-annotated learning tip extracted from dialogue.

    Written to Graphiti via the Agent self-report channel.

    [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 5.2]
    """

    tip_id: str = Field(..., description="Unique identifier for this tip")
    content: str = Field(..., description="The selected text content of the tip")
    title: str = Field(..., description="User-provided title for the tip")
    tags: List[TipTag] = Field(default_factory=list, description="Classification tags")
    node_id: str = Field(..., description="Source canvas node ID")
    source_timestamp: str = Field(
        ..., description="ISO timestamp of the source dialogue message"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="When the tip was created",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Misconception Entity Schema
# ═══════════════════════════════════════════════════════════════════════════════


class Misconception(BaseModel):
    """
    An Agent-detected understanding error with 4-type classification.

    Written to Graphiti when Agent calls the record_error MCP tool.

    [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 5.3]
    """

    misconception_id: str = Field(..., description="Unique identifier")
    error_type: ErrorType = Field(..., description="One of 4 error categories")
    description: str = Field(..., description="Description of the error/misconception")
    context: str = Field(
        default="", description="Dialogue context where the error occurred"
    )
    remedy_strategy: RemedyStrategy = Field(
        ..., description="Mapped differentiated remedy strategy"
    )
    node_id: str = Field(..., description="Source canvas node ID")
    session_id: str = Field(default="", description="Dialogue session ID")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="When the misconception was recorded",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Type Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Neo4j relationship types for Tips and Misconceptions
EDGE_HAS_TIP = "HAS_TIP"
EDGE_HAS_MISCONCEPTION = "HAS_MISCONCEPTION"

# Story 3.7: Relation types for pullout nodes
EDGE_IS_PREREQUISITE = "IS_PREREQUISITE"
EDGE_IS_APPLICATION = "IS_APPLICATION"
EDGE_CONTRASTS_WITH = "CONTRASTS_WITH"
EDGE_IS_SUBCONCEPT = "IS_SUBCONCEPT"
EDGE_SUPPLEMENTS = "SUPPLEMENTS"

# Valid relation types for LLM suggestion
VALID_RELATION_TYPES = [
    EDGE_IS_PREREQUISITE,
    EDGE_IS_APPLICATION,
    EDGE_CONTRASTS_WITH,
    EDGE_IS_SUBCONCEPT,
    EDGE_SUPPLEMENTS,
]

RELATION_TYPE_LABELS: dict[str, str] = {
    EDGE_IS_PREREQUISITE: "是前置知识",
    EDGE_IS_APPLICATION: "是应用案例",
    EDGE_CONTRASTS_WITH: "是对比概念",
    EDGE_IS_SUBCONCEPT: "是子概念",
    EDGE_SUPPLEMENTS: "是补充说明",
}
