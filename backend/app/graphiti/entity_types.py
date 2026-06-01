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
    Story 2.5 (2026-05-04 D 方案): 加 2 项细分策略对齐 PRD §FR-CONV-06.
    """

    SAME_STRUCTURE_NEW_PROBLEM = "same_structure_new_problem"  # 同结构新题练习
    FIND_ERROR_COUNTEREXAMPLE = "find_error_counterexample"  # 找错练习 + 反例构造
    BACKTRACK_DEFINITION = "backtrack_definition"  # 回退到定义题
    DISCRIMINATION_TRANSFER = "discrimination_transfer"  # 辨析题 + 迁移应用题
    # Story 2.5 — PRD §FR-CONV-06 期望的 2 项细分:
    DISCRIMINATION_COMPARISON = (
        "discrimination_comparison"  # 辨析题 + 对比练习 (conceptual_confusion)
    )
    TRANSFER_SELF_EXPLANATION = (
        "transfer_self_explanation"  # 迁移应用题 + 自我解释 (metacognitive_error)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 2.5 (2026-05-04) — PedagogyErrorType (D 方案: 双标签共存)
#
# PRD §FR-CONV-06 期望 4 主类与 Story 3.6 现有 ErrorType (production data 已存)
# 命名/概念都不完全一致. D 方案选择"扩展不破坏":
#
# - ErrorType (Story 3.6, 保留): 低层标签, 现 production data 用此
# - PedagogyErrorType (Story 2.5, 新增): 高层 pedagogy 标签, UI / remedy /
#   间隔复习算法用此
# - LEGACY_TO_PEDAGOGY: 自动映射, SUPERFICIAL 通过 sub_tag 二义性消解
#
# [Source: _bmad-output/implementation-artifacts/epic-2/2-5-error-extraction-classification.md]
# [Source: PRD §FR-CONV-06 (line 3387-3393)]
# ═══════════════════════════════════════════════════════════════════════════════


class PedagogyErrorType(str, Enum):
    """PRD §FR-CONV-06 教育心理学 4 主类 (Story 2.5)."""

    CONCEPTUAL_CONFUSION = "conceptual_confusion"  # 概念混淆: 混淆相关但不同的概念
    PROCEDURAL_ERROR = "procedural_error"  # 推理谬误: 逻辑跳跃, 因果倒置, 无效归纳
    CARELESS_SLIP = "careless_slip"  # 粗心: 已掌握但笔误, 计算错误, 遗漏条件
    METACOGNITIVE_ERROR = "metacognitive_error"  # 元认知错误: 能背但不能迁移, 过度自信


# ═══════════════════════════════════════════════════════════════════════════════
# Remedy Strategy Mapping
# ═══════════════════════════════════════════════════════════════════════════════

ERROR_TYPE_TO_REMEDY: dict[ErrorType, RemedyStrategy] = {
    ErrorType.PROBLEM_FRAMING: RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM,
    ErrorType.REASONING_FALLACY: RemedyStrategy.FIND_ERROR_COUNTEREXAMPLE,
    ErrorType.KNOWLEDGE_GAP: RemedyStrategy.BACKTRACK_DEFINITION,
    ErrorType.SUPERFICIAL: RemedyStrategy.DISCRIMINATION_TRANSFER,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Story 2.5 — PRD 4 主类 → 细分补救策略映射 (AC #3)
# ═══════════════════════════════════════════════════════════════════════════════

PEDAGOGY_TYPE_TO_REMEDIES: dict[PedagogyErrorType, list[RemedyStrategy]] = {
    PedagogyErrorType.CONCEPTUAL_CONFUSION: [
        RemedyStrategy.DISCRIMINATION_COMPARISON,  # 辨析 + 对比 (PRD AC#3)
    ],
    PedagogyErrorType.PROCEDURAL_ERROR: [
        RemedyStrategy.FIND_ERROR_COUNTEREXAMPLE,  # 找错 + 反例 (PRD AC#3)
    ],
    PedagogyErrorType.CARELESS_SLIP: [
        RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM,  # 同结构新题 (PRD AC#3)
    ],
    PedagogyErrorType.METACOGNITIVE_ERROR: [
        RemedyStrategy.TRANSFER_SELF_EXPLANATION,  # 迁移 + 自我解释 (PRD AC#3)
    ],
}


# 现有 4 类 → PRD 4 类映射 (Story 2.5 D 方案核心)
# SUPERFICIAL 是歧义点, 默认映射到 CONCEPTUAL_CONFUSION,
# 通过 disambiguate_superficial() 在分类时根据 sub_tag / 关键词二次拆分.
LEGACY_TO_PEDAGOGY: dict[ErrorType, PedagogyErrorType] = {
    ErrorType.PROBLEM_FRAMING: PedagogyErrorType.CARELESS_SLIP,  # 破题=粗心 (审题失误)
    ErrorType.REASONING_FALLACY: PedagogyErrorType.PROCEDURAL_ERROR,  # 推理谬误等价
    ErrorType.KNOWLEDGE_GAP: PedagogyErrorType.CONCEPTUAL_CONFUSION,  # 缺概念 ≈ 概念混淆
    ErrorType.SUPERFICIAL: PedagogyErrorType.CONCEPTUAL_CONFUSION,  # 默认, 可被二义消解覆盖
}


# 用于 SUPERFICIAL 二义性消解 — 含这些关键词倾向 METACOGNITIVE_ERROR
_METACOGNITIVE_KEYWORDS = (
    "迁移",
    "应用",
    "新场景",
    "新情境",
    "transfer",
    "metacogniti",
    "过度自信",
    "过度信心",
    "self-explanation",
    "无法应用",
)
_METACOGNITIVE_SUB_TAGS = frozenset(
    {
        "transfer_failure",
        "metacognitive",
        "overconfidence",
        "application_failure",
    }
)


def disambiguate_superficial(
    error_description: str,
    sub_tags: list[str] | None = None,
) -> PedagogyErrorType:
    """SUPERFICIAL 二义性消解: 决定映射到 CONCEPTUAL_CONFUSION 还是 METACOGNITIVE_ERROR.

    优先级:
    1. sub_tags 含 transfer_failure / metacognitive / overconfidence
       → METACOGNITIVE_ERROR (能背不能用, 过度自信)
    2. error_description 含"迁移/应用/新场景/transfer"等关键词
       → METACOGNITIVE_ERROR
    3. 否则 → CONCEPTUAL_CONFUSION (默认, 概念表面理解≈混淆)

    Args:
        error_description: 错误描述文本.
        sub_tags: 可选子标签列表 (Story 2.5 Task 2.3 引入).

    Returns:
        PedagogyErrorType.METACOGNITIVE_ERROR 或 CONCEPTUAL_CONFUSION.
    """
    if sub_tags:
        if any(t in _METACOGNITIVE_SUB_TAGS for t in sub_tags):
            return PedagogyErrorType.METACOGNITIVE_ERROR
    text = error_description.lower()
    if any(kw in text for kw in _METACOGNITIVE_KEYWORDS):
        return PedagogyErrorType.METACOGNITIVE_ERROR
    return PedagogyErrorType.CONCEPTUAL_CONFUSION


def map_legacy_to_pedagogy(
    legacy_type: ErrorType,
    error_description: str = "",
    sub_tags: list[str] | None = None,
) -> PedagogyErrorType:
    """统一映射函数: legacy ErrorType → PedagogyErrorType (含 SUPERFICIAL 消解).

    用于 Story 2.5 ErrorClassifier.classify_with_pedagogy() 的 D 方案.
    """
    if legacy_type == ErrorType.SUPERFICIAL:
        return disambiguate_superficial(error_description, sub_tags)
    return LEGACY_TO_PEDAGOGY[legacy_type]


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
    # P0-4 (2026-05-14): rename created_at → tip_created_at to avoid Graphiti
    # EntityNode protected attribute conflict (graphiti_core.nodes.Node reserves
    # uuid/name/group_id/labels/created_at).
    tip_created_at: str = Field(
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
    # P0-4 (2026-05-14): rename created_at → misconception_created_at to avoid
    # Graphiti protected attribute conflict.
    misconception_created_at: str = Field(
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


# ═══════════════════════════════════════════════════════════════════════════════
# S02: Graphiti Typed Extraction Models
# ═══════════════════════════════════════════════════════════════════════════════


class LearningConcept(BaseModel):
    """
    A structured learning concept extracted by Graphiti's LLM pipeline.

    Used as an entity_type in add_episode() so Graphiti can extract
    typed concept nodes instead of generic untyped entities.

    [Source: S02 T01 — Wire entity types into add_episode]

    P0-4 (2026-05-14): rename `name` → `concept_name` to avoid Graphiti's
    protected attribute namespace (graphiti_core reserves `name` for internal
    EntityNode identifier). 与同文件 MasteryRecord.concept_name 命名风格一致。
    """

    concept_name: str = Field(..., description="Concept name")
    description: str = Field(..., description="Brief description of the concept")
    subject_area: str = Field(
        ..., description="Subject/discipline area (e.g. 数学, 物理)"
    )
    difficulty_level: str = Field(
        default="", description="Difficulty level (e.g. beginner, intermediate)"
    )
    prerequisites: List[str] = Field(
        default_factory=list, description="Prerequisite concept names"
    )


class MasteryRecord(BaseModel):
    """
    A student's mastery status for a concept, extracted by Graphiti.

    Tracks mastery level, review recency, and error frequency.

    [Source: S02 T01 — Wire entity types into add_episode]
    """

    concept_name: str = Field(..., description="Name of the concept being tracked")
    mastery_level: str = Field(
        ..., description="Current mastery level (e.g. novice, proficient, expert)"
    )
    last_reviewed: str = Field(..., description="ISO timestamp of last review")
    error_count: int = Field(
        default=0, description="Number of errors made on this concept"
    )


class PrerequisiteRelation(BaseModel):
    """
    A prerequisite relationship between two concepts, used as an edge_type
    in Graphiti's add_episode() for typed edge extraction.

    [Source: S02 T01 — Wire entity types into add_episode]
    """

    source_concept: str = Field(..., description="The concept that is a prerequisite")
    target_concept: str = Field(
        ..., description="The concept that requires the prerequisite"
    )
    relation_strength: str = Field(
        default="strong",
        description="Strength of the prerequisite relation (strong/weak)",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# S02: Canvas Entity/Edge Type Registries for Graphiti add_episode()
# ═══════════════════════════════════════════════════════════════════════════════

CANVAS_ENTITY_TYPES: dict[str, type[BaseModel]] = {
    "LearningConcept": LearningConcept,
    "LearningTip": LearningTip,
    "Misconception": Misconception,
    "MasteryRecord": MasteryRecord,
}

CANVAS_EDGE_TYPES: dict[str, type[BaseModel]] = {
    "PrerequisiteRelation": PrerequisiteRelation,
}
