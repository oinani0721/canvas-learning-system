# Story 2.13: Search Intent Analysis Prompt Regression Tests
# [Source: _bmad-output/implementation-artifacts/2-13-prompt-version-regression-test.md]
"""
Regression tests for search_intent_v*.md prompt templates.

Verifies that prompt changes maintain intent analysis quality:
  - JSON format compliance (>= 90%): valid JSON with required fields
  - Intent classification accuracy (>= 80%): correct search decision
  - Search query generation quality: queries match user intent
"""

import logging
from typing import Any, Dict

from app.services.prompt_registry import PromptRegistry

from tests.regression.conftest import BaselineLoader, RegressionMetricsCollector
from tests.regression.report_generator import RegressionReportGenerator

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"intent", "has_specific_request", "needs_search", "search_queries"}


def _check_intent_format(response: Dict[str, Any]) -> bool:
    """Check if intent analysis response has valid JSON format with required fields."""
    if not response.get("json_format_valid", False):
        return False

    # Must have all required fields
    for field in REQUIRED_FIELDS:
        if field not in response:
            return False

    # intent must be a non-empty string
    if not response.get("intent", ""):
        return False

    # has_specific_request and needs_search must be boolean
    if not isinstance(response.get("has_specific_request"), bool):
        return False
    if not isinstance(response.get("needs_search"), bool):
        return False

    # search_queries must be a list
    if not isinstance(response.get("search_queries"), list):
        return False

    return True


def _check_search_decision(
    response: Dict[str, Any],
    expected: Dict[str, Any],
) -> bool:
    """Check if the search decision matches expected."""
    actual_needs = response.get("needs_search", None)
    expected_needs = expected.get("needs_search", None)
    return actual_needs == expected_needs


def _check_query_count(
    response: Dict[str, Any],
    expected: Dict[str, Any],
) -> bool:
    """Check if search query count is within expected range."""
    queries = response.get("search_queries", [])
    expected_range = expected.get("search_query_count_range", {})
    min_c = expected_range.get("min", 0)
    max_c = expected_range.get("max", 10)
    return min_c <= len(queries) <= max_c


class TestSearchIntentRegression:
    """Search intent analysis prompt regression test suite."""

    def test_prompt_loads_successfully(self, prompt_registry: PromptRegistry):
        """AC-2: Verify search_intent prompt loads via PromptRegistry."""
        content = prompt_registry.get("search_intent")
        assert len(content) > 100, "Prompt content too short"
        assert "意图" in content or "intent" in content.lower()
        assert "JSON" in content

    def test_prompt_metadata_valid(self, prompt_registry: PromptRegistry):
        """AC-1: Verify prompt metadata is present and well-formed."""
        metadata = prompt_registry.get_metadata("search_intent")
        assert metadata["name"] == "search_intent"
        assert metadata["version"] >= 1
        assert metadata["service_ref"], "service_ref should not be empty"
        assert metadata["created_at"], "created_at should not be empty"
        assert len(metadata["content_hash"]) == 64, "SHA-256 hash should be 64 chars"

    def test_prompt_analysis_dimensions(self, prompt_registry: PromptRegistry):
        """Verify prompt covers all analysis dimensions."""
        content = prompt_registry.get("search_intent")
        assert "意图识别" in content or "意图" in content
        assert "搜索" in content or "search" in content.lower()

    def test_prompt_output_schema(self, prompt_registry: PromptRegistry):
        """Verify prompt specifies correct JSON output schema."""
        content = prompt_registry.get("search_intent")
        assert "intent" in content
        assert "has_specific_request" in content
        assert "needs_search" in content
        assert "search_queries" in content

    def test_replay_format_compliance(
        self,
        prompt_registry: PromptRegistry,
        search_intent_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Verify JSON format compliance across all scenarios."""
        scenarios = search_intent_baselines.load_all()
        assert len(scenarios) >= 5, "Need at least 5 search_intent scenarios"

        template = prompt_registry.get_template("search_intent")
        compliant_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            compliant = _check_intent_format(response)
            if compliant:
                compliant_count += 1

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="search_intent",
                prompt_version=template.version,
                metrics={"format_compliant": compliant},
                passed=compliant,
                details="" if compliant else "JSON format non-compliant",
            )

        compliance_rate = compliant_count / len(scenarios)
        assert compliance_rate >= 0.90, "JSON format compliance {v:.4f} below 90 percent threshold".format(
            v=compliance_rate,
        )

    def test_replay_search_decision_accuracy(
        self,
        prompt_registry: PromptRegistry,
        search_intent_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Verify search decision accuracy across scenarios."""
        scenarios = search_intent_baselines.load_all()
        template = prompt_registry.get_template("search_intent")
        correct_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            expected = scenario["expected_output"]
            correct = _check_search_decision(response, expected)
            if correct:
                correct_count += 1

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="search_intent",
                prompt_version=template.version,
                metrics={"search_decision_correct": correct},
                passed=correct,
                details="" if correct else "Search decision mismatch",
            )

        accuracy = correct_count / len(scenarios)
        assert accuracy >= 0.80, "Search decision accuracy {v:.4f} below 80 percent threshold".format(
            v=accuracy,
        )

    def test_replay_query_count_compliance(
        self,
        search_intent_baselines: BaselineLoader,
    ):
        """Verify search query count is within expected range per scenario."""
        scenarios = search_intent_baselines.load_all()
        in_range_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            expected = scenario["expected_output"]
            if _check_query_count(response, expected):
                in_range_count += 1

        rate = in_range_count / len(scenarios)
        assert rate >= 0.80, "Query count compliance {v:.4f} below 80 percent".format(v=rate)

    def test_replay_no_search_empty_queries(
        self,
        search_intent_baselines: BaselineLoader,
    ):
        """Verify no-search scenarios return empty search_queries."""
        scenarios = search_intent_baselines.load_all()
        for scenario in scenarios:
            expected = scenario["expected_output"]
            response = scenario["replay_response"]
            if not expected.get("needs_search", True):
                queries = response.get("search_queries", ["non-empty"])
                assert len(queries) == 0, "Scenario {sid} needs_search=false but has queries".format(
                    sid=scenario["scenario_id"],
                )

    def test_generate_report(
        self,
        prompt_registry: PromptRegistry,
        search_intent_baselines: BaselineLoader,
    ):
        """AC-5: Generate search intent regression report."""
        scenarios = search_intent_baselines.load_all()
        template = prompt_registry.get_template("search_intent")

        scenario_results = []
        format_ok_count = 0
        decision_ok_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            expected = scenario["expected_output"]
            format_ok = _check_intent_format(response)
            decision_ok = _check_search_decision(response, expected)

            if format_ok:
                format_ok_count += 1
            if decision_ok:
                decision_ok_count += 1

            scenario_results.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "passed": format_ok and decision_ok,
                    "metrics": {
                        "format_compliant": format_ok,
                        "search_decision_correct": decision_ok,
                    },
                }
            )

        n = len(scenarios)
        gen = RegressionReportGenerator()
        report = gen.generate(
            prompt_name="search_intent",
            prompt_version=template.version,
            prompt_hash=template.content_hash,
            scenario_results=scenario_results,
            aggregate_metrics={
                "json_format_compliance_rate": format_ok_count / n,
                "intent_classification_accuracy": decision_ok_count / n,
            },
        )
        assert report.gate_passed, "Quality gate failed: " + str(report.gate_failures)
        output = gen.print_report(report)
        assert "PASSED" in output
