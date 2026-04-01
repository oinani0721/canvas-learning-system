# Tests for Subtask 2: Differentiated remediation strategy consumption
# Verifies that question_generator.py correctly selects and injects
# remediation strategies based on student error history.
"""
Test the remediation strategy system in question_generator.py.

layer4_rules.md defines 4 error types (MathCCS) with differentiated strategies:
- 破题错误 (breakthrough error): same-structure-different-packaging questions
- 推理谬误 (reasoning fallacy): find-the-error or counterexample questions
- 知识点缺失 (knowledge gap): definition-level questions, then escalate
- 似懂非懂 (partial understanding): discrimination/counterexample/transfer questions

These tests verify:
1. Dominant error type is correctly identified from error history
2. Correct remediation strategy is selected for each error type
3. Strategy text is injected into Layer 4 of the 5-layer prompt
4. Edge cases (empty history, unknown types, ties) are handled
"""

import pytest

from app.models.exam_models import ACPData, ExamMode
from app.services.question_generator import QuestionGenerator


@pytest.fixture
def qgen():
    """Create QuestionGenerator instance."""
    return QuestionGenerator()


@pytest.fixture
def base_acp():
    """Create a base ACP for testing."""
    return ACPData(
        node_id="test-node-1",
        node_content="微积分基本定理",
        node_type="knowledge_point",
        effective_proficiency=0.4,
        p_mastery=0.3,
        retrievability=0.8,
        mastery_label="Developing",
    )


class TestRemediationStrategySelection:
    """Test _determine_remediation_strategy() picks the right strategy."""

    def test_breakthrough_error_chinese(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "破题错误", "description": "Unable to apply formula"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "破题错误" in result
        assert "同结构不同包装" in result

    def test_reasoning_fallacy_chinese(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "推理谬误", "description": "Logical error in proof"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "推理谬误" in result
        assert "错误推理" in result

    def test_knowledge_gap_chinese(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "知识点缺失", "description": "Does not know definition"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "知识点缺失" in result
        assert "定义" in result

    def test_partial_understanding_chinese(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "似懂非懂", "description": "Superficial understanding"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "似懂非懂" in result
        assert "辨析题" in result

    def test_english_alias_breakthrough_error(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "breakthrough_error", "description": "test"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "破题错误" in result

    def test_english_alias_reasoning_fallacy(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "reasoning_fallacy", "description": "test"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "推理谬误" in result

    def test_english_alias_knowledge_gap(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "knowledge_gap", "description": "test"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "知识点缺失" in result

    def test_english_alias_partial_understanding(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "partial_understanding", "description": "test"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "似懂非懂" in result

    def test_short_alias_reasoning(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "reasoning", "description": "test"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "推理谬误" in result


class TestDominantErrorTypePicking:
    """Test that the most frequent error type is selected."""

    def test_dominant_type_wins(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "破题错误", "description": "err1"},
            {"error_type": "破题错误", "description": "err2"},
            {"error_type": "推理谬误", "description": "err3"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "破题错误" in result
        assert "推理谬误" not in result

    def test_single_entry_is_dominant(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "知识点缺失", "description": "err1"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "知识点缺失" in result

    def test_mixed_with_unknowns_still_picks_known(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "unknown", "description": "err1"},
            {"error_type": "unknown", "description": "err2"},
            {"error_type": "似懂非懂", "description": "err3"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert "似懂非懂" in result


class TestEdgeCases:
    """Test edge cases in remediation strategy selection."""

    def test_empty_error_history(self, qgen, base_acp):
        base_acp.error_history = []
        result = qgen._determine_remediation_strategy(base_acp)
        assert result == ""

    def test_all_unknown_errors(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "unknown", "description": "err1"},
            {"error_type": "unknown", "description": "err2"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert result == ""

    def test_empty_error_type_string(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "", "description": "err1"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert result == ""

    def test_missing_error_type_key(self, qgen, base_acp):
        base_acp.error_history = [
            {"description": "err without type"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert result == ""

    def test_unrecognized_error_type_returns_empty(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "completely_novel_type", "description": "test"},
        ]
        result = qgen._determine_remediation_strategy(base_acp)
        assert result == ""


class TestPromptInjection:
    """Test that remediation strategy is injected into Layer 4 of the prompt."""

    def test_strategy_appears_in_prompt(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "破题错误", "description": "test error"},
        ]
        prompt = qgen.build_5_layer_prompt(base_acp, ExamMode.COMPREHENSIVE)
        assert "补救策略" in prompt
        assert "破题错误" in prompt
        assert "同结构不同包装" in prompt

    def test_no_strategy_when_no_errors(self, qgen, base_acp):
        base_acp.error_history = []
        prompt = qgen.build_5_layer_prompt(base_acp, ExamMode.COMPREHENSIVE)
        assert "补救策略" not in prompt

    def test_strategy_is_in_layer4_section(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "推理谬误", "description": "logic error"},
        ]
        prompt = qgen.build_5_layer_prompt(base_acp, ExamMode.MIXED)
        # Strategy should appear after Layer 3 (ACP) section separator and before Layer 5
        sections = prompt.split("---")
        # Prompt format: layer1 | layer2 | layer3 | layer4 | layer5
        # Strategy should be in the layer4 section (index 3)
        assert len(sections) >= 5
        layer4_section = sections[3]
        assert "补救策略" in layer4_section
        assert "推理谬误" in layer4_section

    def test_prompt_still_has_base_rules_with_strategy(self, qgen, base_acp):
        base_acp.error_history = [
            {"error_type": "知识点缺失", "description": "test"},
        ]
        prompt = qgen.build_5_layer_prompt(base_acp, ExamMode.POINT_TO_POINT)
        # Base rules from layer4_rules.md should still be present
        assert "一次只出一道题" in prompt or "弱点" in prompt or "基本出题规则" in prompt

    def test_all_four_strategies_have_unique_content(self, qgen, base_acp):
        """Each error type strategy has distinct remediation text."""
        strategies = set()
        for error_type in ["破题错误", "推理谬误", "知识点缺失", "似懂非懂"]:
            base_acp.error_history = [{"error_type": error_type, "description": "t"}]
            result = qgen._determine_remediation_strategy(base_acp)
            strategies.add(result)
        assert len(strategies) == 4  # All four should be distinct
