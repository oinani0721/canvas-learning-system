# Story 7.3: Question Generation Prompt Regression Tests
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
Regression tests for question_gen_v*.md prompt templates.

Verifies that prompt changes maintain question generation quality:
  - Format compliance rate (>= 90%)
  - Difficulty matching rate (>= 70%)
"""

import logging
from typing import Any, Dict, List

from app.services.prompt_registry import PromptRegistry

from tests.regression.conftest import BaselineLoader, RegressionMetricsCollector
from tests.regression.report_generator import RegressionReportGenerator

logger = logging.getLogger(__name__)

VALID_QUESTION_TYPES = {
    "definition", "explanation", "analysis", "comparison",
    "application", "evaluation", "error_finding", "transfer",
}

VALID_BLOOM_LEVELS = {
    "remember", "understand", "apply", "analyze", "evaluate", "create",
}

MASTERY_TO_BLOOM = {
    (0.0, 0.3): {"remember"},
    (0.3, 0.5): {"remember", "understand"},
    (0.5, 0.7): {"understand", "apply", "analyze"},
    (0.7, 1.01): {"analyze", "evaluate", "create"},
}


def _check_format_compliance(response: Dict[str, Any]) -> bool:
    """Check if a question generation response has all required fields."""
    required_fields = ["question", "question_type", "target_bloom_level",
                       "difficulty_rationale", "scoring_hints"]
    for field in required_fields:
        if field not in response or not response[field]:
            return False
    if response.get("question_type") not in VALID_QUESTION_TYPES:
        return False
    if response.get("target_bloom_level") not in VALID_BLOOM_LEVELS:
        return False
    return True


def _check_difficulty_match(
    response: Dict[str, Any],
    mastery_level: float,
    expected_bloom_levels: List[str],
) -> bool:
    """Check if question difficulty matches student mastery level."""
    bloom = response.get("target_bloom_level", "")
    if expected_bloom_levels:
        return bloom in expected_bloom_levels

    # Fallback: check against mastery-to-bloom mapping
    for (low, high), valid_blooms in MASTERY_TO_BLOOM.items():
        if low <= mastery_level < high:
            return bloom in valid_blooms
    return False


class TestQuestionGenRegression:
    """Question generation prompt regression test suite."""

    def test_prompt_loads_successfully(self, prompt_registry: PromptRegistry):
        """AC-2: Verify question_gen prompt loads via PromptRegistry."""
        content = prompt_registry.get("question_gen")
        assert len(content) > 100, "Prompt content too short"
        assert "\u89d2\u8272\u5b9a\u4e49" in content or "Role" in content
        assert "\u8003\u5bdf\u6a21\u5f0f" in content or "exam_mode" in content

    def test_prompt_five_layer_structure(self, prompt_registry: PromptRegistry):
        """Verify prompt has all 5 layers (PRD requirement)."""
        content = prompt_registry.get("question_gen")
        layers = [
            ("\u7b2c 1 \u5c42", "\u89d2\u8272\u5b9a\u4e49"),
            ("\u7b2c 2 \u5c42", "\u8003\u5bdf\u6a21\u5f0f"),
            ("\u7b2c 3 \u5c42", "ACP"),
            ("\u7b2c 4 \u5c42", "\u51fa\u9898\u89c4\u5219"),
            ("\u7b2c 5 \u5c42", "\u8bc4\u5206\u9884\u8bbe"),
        ]
        for layer_id, keyword in layers:
            assert layer_id in content, "Missing layer: " + layer_id
            assert keyword in content, "Missing keyword: " + keyword

    def test_prompt_error_type_mapping(self, prompt_registry: PromptRegistry):
        """Verify 4-type error-to-strategy mapping is present."""
        content = prompt_registry.get("question_gen")
        error_types = [
            "\u7834\u9898\u9519\u8bef",
            "\u63a8\u7406\u8c2c\u8bef",
            "\u77e5\u8bc6\u70b9\u7f3a\u5931",
            "\u4f3c\u61c2\u975e\u61c2",
        ]
        for et in error_types:
            assert et in content, "Missing error type mapping: " + et

    def test_prompt_bloom_taxonomy(self, prompt_registry: PromptRegistry):
        """Verify Bloom's Taxonomy levels are referenced."""
        content = prompt_registry.get("question_gen")
        assert "Bloom" in content
        for level in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]:
            assert level.lower() in content.lower(), "Missing Bloom level: " + level

    def test_replay_format_compliance(
        self,
        prompt_registry: PromptRegistry,
        question_gen_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Verify format compliance across all scenarios."""
        scenarios = question_gen_baselines.load_all()
        assert len(scenarios) >= 5, "Need at least 5 question_gen scenarios"

        template = prompt_registry.get_template("question_gen")
        compliant_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            compliant = _check_format_compliance(response)
            if compliant:
                compliant_count += 1

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="question_gen",
                prompt_version=template.version,
                metrics={"format_compliant": compliant},
                passed=compliant,
                details="" if compliant else "Format non-compliant",
            )

        compliance_rate = compliant_count / len(scenarios)
        assert compliance_rate >= 0.90, (
            "Format compliance {v:.4f} below 90 percent threshold".format(v=compliance_rate)
        )

    def test_replay_difficulty_matching(
        self,
        prompt_registry: PromptRegistry,
        question_gen_baselines: BaselineLoader,
    ):
        """AC-4/AC-5: Verify difficulty matches mastery level."""
        scenarios = question_gen_baselines.load_all()
        match_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            mastery = scenario["input"]["mastery_level"]
            expected_blooms = scenario["expected_output"].get("valid_bloom_levels", list())
            matched = _check_difficulty_match(response, mastery, expected_blooms)
            if matched:
                match_count += 1

        match_rate = match_count / len(scenarios)
        assert match_rate >= 0.70, (
            "Difficulty match rate {v:.4f} below 70 percent threshold".format(v=match_rate)
        )

    def test_replay_addresses_weakness(
        self,
        question_gen_baselines: BaselineLoader,
    ):
        """Verify questions target student weaknesses."""
        scenarios = question_gen_baselines.load_all()
        addresses_count = 0

        for scenario in scenarios:
            expected = scenario["expected_output"]
            response = scenario["replay_response"]
            has_question = bool(response.get("question", "").strip())
            if has_question and expected.get("addresses_weakness", False):
                addresses_count += 1

        min_required = int(len(scenarios) * 0.70)
        assert addresses_count >= min_required, (
            "Too few questions address student weaknesses: {a}/{t}".format(
                a=addresses_count, t=len(scenarios),
            )
        )

    def test_generate_report(
        self,
        prompt_registry: PromptRegistry,
        question_gen_baselines: BaselineLoader,
    ):
        """AC-5: Generate question gen regression report."""
        scenarios = question_gen_baselines.load_all()
        template = prompt_registry.get_template("question_gen")

        scenario_results = list()
        compliant_count = 0
        match_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            compliant = _check_format_compliance(response)
            mastery = scenario["input"]["mastery_level"]
            expected_blooms = scenario["expected_output"].get("valid_bloom_levels", list())
            matched = _check_difficulty_match(response, mastery, expected_blooms)

            if compliant:
                compliant_count += 1
            if matched:
                match_count += 1

            scenario_results.append({
                "scenario_id": scenario["scenario_id"],
                "passed": compliant and matched,
                "metrics": {
                    "format_compliant": compliant,
                    "difficulty_matched": matched,
                },
            })

        n = len(scenarios)
        gen = RegressionReportGenerator()
        report = gen.generate(
            prompt_name="question_gen",
            prompt_version=template.version,
            prompt_hash=template.content_hash,
            scenario_results=scenario_results,
            aggregate_metrics={
                "format_compliance_rate": compliant_count / n,
                "difficulty_match_rate": match_count / n,
            },
        )
        assert report.gate_passed, "Quality gate failed: " + str(report.gate_failures)
