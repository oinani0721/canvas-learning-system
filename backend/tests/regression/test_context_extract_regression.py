# Story 7.3: Context Extraction Prompt Regression Tests
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
Regression tests for context_extract_v*.md prompt templates.

Verifies extraction quality:
  - Extraction recall (>= 85%)
  - Classification accuracy (>= 80%)
"""

import logging
from typing import Any, Dict

from app.services.prompt_registry import PromptRegistry

from tests.regression.conftest import BaselineLoader, RegressionMetricsCollector
from tests.regression.report_generator import RegressionReportGenerator

logger = logging.getLogger(__name__)

VALID_ERROR_TYPES = {
    "\u7834\u9898\u9519\u8bef",
    "\u63a8\u7406\u8c2c\u8bef",
    "\u77e5\u8bc6\u70b9\u7f3a\u5931",
    "\u4f3c\u61c2\u975e\u61c2",
}

VALID_TIP_SOURCES = {
    "user_marked", "ai_explanation", "self_summary", "confusion_resolved",
}

VALID_LEARNING_VALUES = {"high", "medium", "low"}


def _compute_extraction_recall(
    actual_response: Dict[str, Any],
    expected: Dict[str, Any],
) -> float:
    """
    Compute extraction recall: what fraction of expected items were found.
    Checks errors, tips, and key_qa counts against minimums.
    """
    checks_passed = 0
    total_checks = 0

    # Error count check
    min_errors = expected.get("min_errors", 0)
    actual_errors = len(actual_response.get("errors", list()))
    total_checks += 1
    if actual_errors >= min_errors:
        checks_passed += 1

    # Error type check
    expected_types = set(expected.get("expected_error_types", list()))
    if expected_types:
        total_checks += 1
        actual_types = {e.get("error_type") for e in actual_response.get("errors", list())}
        if expected_types.issubset(actual_types):
            checks_passed += 1

    # Tips count check
    min_tips = expected.get("min_tips", 0)
    actual_tips = len(actual_response.get("tips", list()))
    total_checks += 1
    if actual_tips >= min_tips:
        checks_passed += 1

    # Key QA count check
    min_qa = expected.get("min_key_qa", 0)
    actual_qa = len(actual_response.get("key_qa", list()))
    total_checks += 1
    if actual_qa >= min_qa:
        checks_passed += 1

    return checks_passed / total_checks if total_checks > 0 else 0.0


def _compute_classification_accuracy(
    actual_response: Dict[str, Any],
) -> float:
    """
    Compute classification accuracy: what fraction of extracted items
    have valid type/category assignments.
    """
    valid_count = 0
    total_count = 0

    # Check error type validity
    for error in actual_response.get("errors", list()):
        total_count += 1
        if error.get("error_type") in VALID_ERROR_TYPES:
            valid_count += 1

    # Check tip source validity
    for tip in actual_response.get("tips", list()):
        total_count += 1
        if tip.get("source") in VALID_TIP_SOURCES:
            valid_count += 1

    # Check key_qa learning_value validity
    for qa in actual_response.get("key_qa", list()):
        total_count += 1
        if qa.get("learning_value") in VALID_LEARNING_VALUES:
            valid_count += 1

    return valid_count / total_count if total_count > 0 else 1.0


def _check_evidence_present(actual_response: Dict[str, Any]) -> bool:
    """Check that every extracted item has an evidence field."""
    for error in actual_response.get("errors", list()):
        if not error.get("evidence"):
            return False
    for tip in actual_response.get("tips", list()):
        if not tip.get("evidence"):
            return False
    for qa in actual_response.get("key_qa", list()):
        if not qa.get("evidence"):
            return False
    return True


class TestContextExtractRegression:
    """Context extraction prompt regression test suite."""

    def test_prompt_loads_successfully(self, prompt_registry: PromptRegistry):
        """AC-2: Verify context_extract prompt loads via PromptRegistry."""
        content = prompt_registry.get("context_extract")
        assert len(content) > 100, "Prompt content too short"
        assert "\u5bf9\u8bdd" in content or "conversation" in content
        assert "\u63d0\u53d6" in content or "extract" in content

    def test_prompt_contains_error_types(self, prompt_registry: PromptRegistry):
        """Verify all 4 error types are defined in the prompt."""
        content = prompt_registry.get("context_extract")
        for et in VALID_ERROR_TYPES:
            assert et in content, "Missing error type: " + et

    def test_prompt_contains_extraction_categories(self, prompt_registry: PromptRegistry):
        """Verify prompt defines all 3 extraction categories."""
        content = prompt_registry.get("context_extract")
        categories = ["Tips", "\u5173\u952e\u95ee\u7b54", "\u9519\u8bef"]
        for cat in categories:
            assert cat in content, "Missing extraction category: " + cat

    def test_prompt_evidence_requirement(self, prompt_registry: PromptRegistry):
        """Verify prompt requires evidence for each extraction."""
        content = prompt_registry.get("context_extract")
        assert "evidence" in content.lower()
        assert "\u539f\u6587" in content or "\u5f15\u7528" in content

    def test_replay_extraction_recall(
        self,
        prompt_registry: PromptRegistry,
        context_extract_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Verify extraction recall across all scenarios."""
        scenarios = context_extract_baselines.load_all()
        assert len(scenarios) >= 5, "Need at least 5 context_extract scenarios"

        template = prompt_registry.get_template("context_extract")
        total_recall = 0.0

        for scenario in scenarios:
            recall = _compute_extraction_recall(
                scenario["replay_response"],
                scenario["expected_output"],
            )
            total_recall += recall

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="context_extract",
                prompt_version=template.version,
                metrics={"extraction_recall": recall},
                passed=recall >= 0.75,
                details="" if recall >= 0.75 else "recall={v:.2f}".format(v=recall),
            )

        avg_recall = total_recall / len(scenarios)
        assert avg_recall >= 0.85, (
            "Extraction recall {v:.4f} below 85 percent threshold".format(v=avg_recall)
        )

    def test_replay_classification_accuracy(
        self,
        prompt_registry: PromptRegistry,
        context_extract_baselines: BaselineLoader,
    ):
        """AC-4/AC-5: Verify classification accuracy."""
        scenarios = context_extract_baselines.load_all()
        total_accuracy = 0.0

        for scenario in scenarios:
            accuracy = _compute_classification_accuracy(scenario["replay_response"])
            total_accuracy += accuracy

        avg_accuracy = total_accuracy / len(scenarios)
        assert avg_accuracy >= 0.80, (
            "Classification accuracy {v:.4f} below 80 percent threshold".format(v=avg_accuracy)
        )

    def test_replay_evidence_present(
        self,
        context_extract_baselines: BaselineLoader,
    ):
        """Verify all extractions have evidence citations."""
        scenarios = context_extract_baselines.load_all()
        for scenario in scenarios:
            has_evidence = _check_evidence_present(scenario["replay_response"])
            assert has_evidence, (
                "Missing evidence in scenario: " + scenario["scenario_id"]
            )

    def test_generate_report(
        self,
        prompt_registry: PromptRegistry,
        context_extract_baselines: BaselineLoader,
    ):
        """AC-5: Generate context extraction regression report."""
        scenarios = context_extract_baselines.load_all()
        template = prompt_registry.get_template("context_extract")

        scenario_results = list()
        total_recall = 0.0
        total_accuracy = 0.0

        for scenario in scenarios:
            recall = _compute_extraction_recall(
                scenario["replay_response"],
                scenario["expected_output"],
            )
            accuracy = _compute_classification_accuracy(scenario["replay_response"])
            total_recall += recall
            total_accuracy += accuracy

            scenario_results.append({
                "scenario_id": scenario["scenario_id"],
                "passed": recall >= 0.75 and accuracy >= 0.75,
                "metrics": {
                    "extraction_recall": recall,
                    "classification_accuracy": accuracy,
                },
            })

        n = len(scenarios)
        gen = RegressionReportGenerator()
        report = gen.generate(
            prompt_name="context_extract",
            prompt_version=template.version,
            prompt_hash=template.content_hash,
            scenario_results=scenario_results,
            aggregate_metrics={
                "extraction_recall": total_recall / n,
                "classification_accuracy": total_accuracy / n,
            },
        )
        assert report.gate_passed, "Quality gate failed: " + str(report.gate_failures)
