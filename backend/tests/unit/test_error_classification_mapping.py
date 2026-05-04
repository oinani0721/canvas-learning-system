"""Story 2.5 — 4 主类映射 + 双标签分类单元测试 (D 方案).

覆盖:
- AC #2: 4 类映射 (legacy → pedagogy) 正确, AMBIGUOUS 标记
- AC #3: 补救策略映射对齐 PRD §FR-CONV-06
- D 方案 SUPERFICIAL 二义消解 (sub_tag + 关键词)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.graphiti.entity_types import (
    ERROR_TYPE_TO_REMEDY,
    LEGACY_TO_PEDAGOGY,
    PEDAGOGY_TYPE_TO_REMEDIES,
    ErrorType,
    PedagogyErrorType,
    RemedyStrategy,
    disambiguate_superficial,
    map_legacy_to_pedagogy,
)
from app.services.error_classifier import (
    ClassifiedError,
    ErrorClassifier,
)


# ════════════════════════════════════════════════════════════════════
# AC #2 — Legacy ErrorType → PedagogyErrorType 映射
# ════════════════════════════════════════════════════════════════════


def test_legacy_to_pedagogy_problem_framing_maps_to_careless_slip():
    """破题错误 (审题失误) → 粗心 (PRD AC#2)."""
    assert (
        LEGACY_TO_PEDAGOGY[ErrorType.PROBLEM_FRAMING]
        == PedagogyErrorType.CARELESS_SLIP
    )


def test_legacy_to_pedagogy_reasoning_fallacy_maps_to_procedural_error():
    """推理谬误 → 程序性错误 (几乎等价)."""
    assert (
        LEGACY_TO_PEDAGOGY[ErrorType.REASONING_FALLACY]
        == PedagogyErrorType.PROCEDURAL_ERROR
    )


def test_legacy_to_pedagogy_knowledge_gap_maps_to_conceptual_confusion():
    """知识点缺失 → 概念混淆 (缺概念也算混淆)."""
    assert (
        LEGACY_TO_PEDAGOGY[ErrorType.KNOWLEDGE_GAP]
        == PedagogyErrorType.CONCEPTUAL_CONFUSION
    )


def test_legacy_to_pedagogy_superficial_default_maps_to_conceptual_confusion():
    """SUPERFICIAL 默认 → CONCEPTUAL_CONFUSION (无 disambiguation)."""
    assert (
        LEGACY_TO_PEDAGOGY[ErrorType.SUPERFICIAL]
        == PedagogyErrorType.CONCEPTUAL_CONFUSION
    )


# ════════════════════════════════════════════════════════════════════
# D 方案 — SUPERFICIAL 二义性消解
# ════════════════════════════════════════════════════════════════════


def test_disambiguate_superficial_default_is_conceptual_confusion():
    """无 sub_tag 无关键词 → CONCEPTUAL_CONFUSION."""
    result = disambiguate_superficial("学生混淆了 X 和 Y", sub_tags=None)
    assert result == PedagogyErrorType.CONCEPTUAL_CONFUSION


def test_disambiguate_superficial_with_transfer_keyword_metacognitive():
    """关键词"迁移"/transfer → METACOGNITIVE_ERROR."""
    result = disambiguate_superficial(
        "学生能背定义但不能迁移到新场景", sub_tags=None
    )
    assert result == PedagogyErrorType.METACOGNITIVE_ERROR


def test_disambiguate_superficial_with_transfer_failure_subtag():
    """sub_tag transfer_failure → METACOGNITIVE_ERROR."""
    result = disambiguate_superficial(
        "无明显迁移描述", sub_tags=["transfer_failure"]
    )
    assert result == PedagogyErrorType.METACOGNITIVE_ERROR


def test_disambiguate_superficial_subtag_priority_over_keyword():
    """sub_tag 优先级 > 关键词 (即使 description 无关键词)."""
    result = disambiguate_superficial(
        "完全描述无关", sub_tags=["metacognitive"]
    )
    assert result == PedagogyErrorType.METACOGNITIVE_ERROR


def test_disambiguate_superficial_overconfidence_subtag():
    """过度自信 sub_tag → METACOGNITIVE_ERROR."""
    result = disambiguate_superficial(
        "学生说自己懂了", sub_tags=["overconfidence"]
    )
    assert result == PedagogyErrorType.METACOGNITIVE_ERROR


def test_map_legacy_to_pedagogy_uses_disambiguation_for_superficial():
    """统一映射函数对 SUPERFICIAL 自动调 disambiguate."""
    result = map_legacy_to_pedagogy(
        ErrorType.SUPERFICIAL,
        error_description="学生不能将定义迁移到新问题",
    )
    assert result == PedagogyErrorType.METACOGNITIVE_ERROR


def test_map_legacy_to_pedagogy_non_superficial_no_disambiguation():
    """非 SUPERFICIAL 直接查表, 不调 disambiguate."""
    result = map_legacy_to_pedagogy(
        ErrorType.PROBLEM_FRAMING,
        error_description="迁移 transfer 应用",  # 这些关键词不应影响
    )
    assert result == PedagogyErrorType.CARELESS_SLIP


# ════════════════════════════════════════════════════════════════════
# AC #3 — Pedagogy 4 类 → 补救策略映射 (PRD §FR-CONV-06)
# ════════════════════════════════════════════════════════════════════


def test_remedy_conceptual_confusion_is_discrimination_comparison():
    """conceptual_confusion → 辨析 + 对比 (PRD AC#3)."""
    remedies = PEDAGOGY_TYPE_TO_REMEDIES[PedagogyErrorType.CONCEPTUAL_CONFUSION]
    assert RemedyStrategy.DISCRIMINATION_COMPARISON in remedies


def test_remedy_procedural_error_is_find_error_counterexample():
    """procedural_error → 找错 + 反例 (PRD AC#3)."""
    remedies = PEDAGOGY_TYPE_TO_REMEDIES[PedagogyErrorType.PROCEDURAL_ERROR]
    assert RemedyStrategy.FIND_ERROR_COUNTEREXAMPLE in remedies


def test_remedy_careless_slip_is_same_structure():
    """careless_slip → 同结构新题 (PRD AC#3)."""
    remedies = PEDAGOGY_TYPE_TO_REMEDIES[PedagogyErrorType.CARELESS_SLIP]
    assert RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM in remedies


def test_remedy_metacognitive_error_is_transfer_self_explanation():
    """metacognitive_error → 迁移 + 自我解释 (PRD AC#3)."""
    remedies = PEDAGOGY_TYPE_TO_REMEDIES[PedagogyErrorType.METACOGNITIVE_ERROR]
    assert RemedyStrategy.TRANSFER_SELF_EXPLANATION in remedies


def test_all_pedagogy_types_have_remedy_mapping():
    """完整性: 4 个 PedagogyErrorType 都有 remedy 映射."""
    for ptype in PedagogyErrorType:
        assert ptype in PEDAGOGY_TYPE_TO_REMEDIES
        assert len(PEDAGOGY_TYPE_TO_REMEDIES[ptype]) >= 1


def test_legacy_remedy_unchanged_backward_compat():
    """向后兼容: ERROR_TYPE_TO_REMEDY (Story 3.6) 行为不变."""
    assert (
        ERROR_TYPE_TO_REMEDY[ErrorType.PROBLEM_FRAMING]
        == RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM
    )
    assert (
        ERROR_TYPE_TO_REMEDY[ErrorType.SUPERFICIAL]
        == RemedyStrategy.DISCRIMINATION_TRANSFER
    )


# ════════════════════════════════════════════════════════════════════
# ClassifiedError 双标签 + ErrorClassifier.classify_with_pedagogy()
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_classify_with_pedagogy_returns_dual_label():
    """classify_with_pedagogy 返回双标签 (legacy + pedagogy)."""
    classifier = ErrorClassifier()
    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=AsyncMock(return_value=(ErrorType.REASONING_FALLACY, 0.85)),
    ):
        result = await classifier.classify_with_pedagogy(
            error_description="学生因果倒置",
            node_id="节点/Causation.md",
        )

    assert isinstance(result, ClassifiedError)
    assert result.legacy_type == ErrorType.REASONING_FALLACY
    assert result.pedagogy_type == PedagogyErrorType.PROCEDURAL_ERROR
    assert result.legacy_remedy == RemedyStrategy.FIND_ERROR_COUNTEREXAMPLE
    assert RemedyStrategy.FIND_ERROR_COUNTEREXAMPLE in result.pedagogy_remedies
    assert result.confidence == 0.85
    assert result.is_ambiguous is False


@pytest.mark.asyncio
async def test_classify_with_pedagogy_low_confidence_is_ambiguous():
    """confidence < 0.6 → is_ambiguous=True (PRD AC #2)."""
    classifier = ErrorClassifier()
    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=AsyncMock(return_value=(ErrorType.SUPERFICIAL, 0.45)),
    ):
        result = await classifier.classify_with_pedagogy(
            error_description="不确定的错误",
            node_id="节点/X.md",
        )

    assert result.confidence == 0.45
    assert result.is_ambiguous is True


@pytest.mark.asyncio
async def test_classify_with_pedagogy_superficial_disambiguated_by_keyword():
    """SUPERFICIAL + 描述含"迁移" → pedagogy_type=METACOGNITIVE_ERROR."""
    classifier = ErrorClassifier()
    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=AsyncMock(return_value=(ErrorType.SUPERFICIAL, 0.75)),
    ):
        result = await classifier.classify_with_pedagogy(
            error_description="能背定义但不能迁移到新问题",
            node_id="节点/X.md",
        )

    assert result.legacy_type == ErrorType.SUPERFICIAL
    assert result.pedagogy_type == PedagogyErrorType.METACOGNITIVE_ERROR
    assert RemedyStrategy.TRANSFER_SELF_EXPLANATION in result.pedagogy_remedies


@pytest.mark.asyncio
async def test_classify_with_pedagogy_superficial_disambiguated_by_subtag():
    """SUPERFICIAL + sub_tag transfer_failure → METACOGNITIVE_ERROR."""
    classifier = ErrorClassifier()
    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=AsyncMock(return_value=(ErrorType.SUPERFICIAL, 0.7)),
    ):
        result = await classifier.classify_with_pedagogy(
            error_description="表面理解",  # 无迁移关键词
            node_id="节点/X.md",
            sub_tags=["transfer_failure"],
        )

    assert result.pedagogy_type == PedagogyErrorType.METACOGNITIVE_ERROR
    assert "transfer_failure" in result.sub_tags


@pytest.mark.asyncio
async def test_classify_with_pedagogy_superficial_default_conceptual():
    """SUPERFICIAL + 无关键词无 sub_tag → 默认 CONCEPTUAL_CONFUSION."""
    classifier = ErrorClassifier()
    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=AsyncMock(return_value=(ErrorType.SUPERFICIAL, 0.7)),
    ):
        result = await classifier.classify_with_pedagogy(
            error_description="学生混淆了 X 和 Y 两个概念",  # 无迁移关键词
            node_id="节点/X.md",
        )

    assert result.pedagogy_type == PedagogyErrorType.CONCEPTUAL_CONFUSION
    assert RemedyStrategy.DISCRIMINATION_COMPARISON in result.pedagogy_remedies


@pytest.mark.asyncio
async def test_classify_with_pedagogy_problem_framing_to_careless_slip():
    """PROBLEM_FRAMING → CARELESS_SLIP + same_structure_new_problem remedy."""
    classifier = ErrorClassifier()
    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=AsyncMock(return_value=(ErrorType.PROBLEM_FRAMING, 0.9)),
    ):
        result = await classifier.classify_with_pedagogy(
            error_description="学生漏看条件",
            node_id="节点/X.md",
        )

    assert result.legacy_type == ErrorType.PROBLEM_FRAMING
    assert result.pedagogy_type == PedagogyErrorType.CARELESS_SLIP
    assert RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM in result.pedagogy_remedies


# ════════════════════════════════════════════════════════════════════
# 向后兼容: 现有 classify() 行为不破坏
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_classify_legacy_method_still_works():
    """Story 3.6 的 classify() 方法保持原行为 (D 方案不破坏向后兼容)."""
    classifier = ErrorClassifier()
    with patch.object(
        classifier,
        "_llm_classify",
        new=AsyncMock(return_value=ErrorType.KNOWLEDGE_GAP),
    ):
        result = await classifier.classify(
            error_description="缺前置概念",
            node_id="节点/X.md",
        )

    # ClassificationResult 是 Story 3.6 的 schema, 字段不变
    assert result.error_type == ErrorType.KNOWLEDGE_GAP
    assert result.remedy_strategy == RemedyStrategy.BACKTRACK_DEFINITION
    assert result.misconception.error_type == ErrorType.KNOWLEDGE_GAP
