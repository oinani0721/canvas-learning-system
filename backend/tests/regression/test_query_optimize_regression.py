# Story 2.13: Query Optimize Prompt Regression Tests
# [Source: _bmad-output/implementation-artifacts/2-13-prompt-version-regression-test.md]
"""
Regression tests for query_optimize_v*.md prompt templates.

Verifies that prompt changes maintain query optimization quality:
  - JSON format compliance rate (>= 90%): valid JSON array of query strings
  - Query diversity rate (>= 80%): optimized queries differ from originals
  - Count compliance: 2-3 optimized queries per scenario
"""

import logging
from typing import Any, Dict, List

from app.services.prompt_registry import PromptRegistry

from tests.regression.conftest import BaselineLoader, RegressionMetricsCollector
from tests.regression.report_generator import RegressionReportGenerator

logger = logging.getLogger(__name__)


def _check_optimize_format(response: Dict[str, Any]) -> bool:
    """Check if query optimize response has valid JSON array format."""
    if not response.get("json_format_valid", False):
        return False

    queries = response.get("queries", [])
    if not isinstance(queries, list):
        return False

    # Must have 2-3 queries
    if len(queries) < 2 or len(queries) > 3:
        return False

    # Each query must be a non-empty string
    for q in queries:
        if not q or not isinstance(q, str) or not q.strip():
            return False

    return True


def _check_query_diversity(
    response: Dict[str, Any],
    input_data: Dict[str, Any],
) -> bool:
    """Check if optimized queries differ meaningfully from original queries."""
    queries = response.get("queries", [])
    original_queries = input_data.get("original_queries", [])

    if not queries:
        return False

    # No optimized query should be identical to any original query
    original_set = {q.strip().lower() for q in original_queries}
    for q in queries:
        if q.strip().lower() in original_set:
            return False

    # Optimized queries should be unique among themselves
    unique_queries = {q.strip().lower() for q in queries}
    if len(unique_queries) < len(queries):
        return False

    return True


class TestQueryOptimizeRegression:
    """Query optimize prompt regression test suite."""

    def test_prompt_loads_successfully(self, prompt_registry: PromptRegistry):
        """AC-2: Verify query_optimize prompt loads via PromptRegistry."""
        content = prompt_registry.get("query_optimize")
        assert len(content) > 100, "Prompt content too short"
        assert "优化" in content or "optimize" in content.lower()
        assert "JSON" in content

    def test_prompt_metadata_valid(self, prompt_registry: PromptRegistry):
        """AC-1: Verify prompt metadata is present and well-formed."""
        metadata = prompt_registry.get_metadata("query_optimize")
        assert metadata["name"] == "query_optimize"
        assert metadata["version"] >= 1
        assert metadata["service_ref"], "service_ref should not be empty"
        assert metadata["created_at"], "created_at should not be empty"
        assert len(metadata["content_hash"]) == 64, "SHA-256 hash should be 64 chars"

    def test_prompt_optimization_strategies(self, prompt_registry: PromptRegistry):
        """Verify prompt contains optimization strategy guidance."""
        content = prompt_registry.get("query_optimize")
        assert "优化策略" in content or "策略" in content

    def test_prompt_output_schema(self, prompt_registry: PromptRegistry):
        """Verify prompt specifies JSON array output format."""
        content = prompt_registry.get("query_optimize")
        assert "JSON" in content
        assert "数组" in content or "array" in content.lower() or '["' in content

    def test_prompt_has_placeholders(self, prompt_registry: PromptRegistry):
        """Verify prompt contains required placeholders for variable substitution."""
        content = prompt_registry.get("query_optimize")
        assert "{{user_intent}}" in content, "Missing {{user_intent}} placeholder"
        assert "{{user_prompt}}" in content, "Missing {{user_prompt}} placeholder"
        assert "{{original_queries}}" in content, "Missing {{original_queries}} placeholder"

    def test_replay_format_compliance(
        self,
        prompt_registry: PromptRegistry,
        query_optimize_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Verify JSON format compliance across all scenarios."""
        scenarios = query_optimize_baselines.load_all()
        assert len(scenarios) >= 5, "Need at least 5 query_optimize scenarios"

        template = prompt_registry.get_template("query_optimize")
        compliant_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            compliant = _check_optimize_format(response)
            if compliant:
                compliant_count += 1

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="query_optimize",
                prompt_version=template.version,
                metrics={"format_compliant": compliant},
                passed=compliant,
                details="" if compliant else "JSON format non-compliant",
            )

        compliance_rate = compliant_count / len(scenarios)
        assert compliance_rate >= 0.90, (
            "JSON format compliance {v:.4f} below 90 percent threshold".format(
                v=compliance_rate,
            )
        )

    def test_replay_query_diversity(
        self,
        query_optimize_baselines: BaselineLoader,
    ):
        """AC-4: Verify optimized queries differ from original queries."""
        scenarios = query_optimize_baselines.load_all()
        diverse_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            input_data = scenario["input"]
            if _check_query_diversity(response, input_data):
                diverse_count += 1

        diversity_rate = diverse_count / len(scenarios)
        assert diversity_rate >= 0.80, (
            "Query diversity rate {v:.4f} below 80 percent threshold".format(
                v=diversity_rate,
            )
        )

    def test_replay_count_compliance(
        self,
        query_optimize_baselines: BaselineLoader,
    ):
        """Verify each scenario produces 2-3 optimized queries as specified."""
        scenarios = query_optimize_baselines.load_all()
        count_ok = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            expected = scenario["expected_output"]
            queries = response.get("queries", [])
            min_count = expected.get("min_query_count", 2)
            max_count = expected.get("max_query_count", 3)
            if min_count <= len(queries) <= max_count:
                count_ok += 1

        count_rate = count_ok / len(scenarios)
        assert count_rate >= 0.80, (
            "Count compliance {v:.4f} below 80 percent threshold".format(
                v=count_rate,
            )
        )

    def test_generate_report(
        self,
        prompt_registry: PromptRegistry,
        query_optimize_baselines: BaselineLoader,
    ):
        """AC-5: Generate query optimize regression report."""
        scenarios = query_optimize_baselines.load_all()
        template = prompt_registry.get_template("query_optimize")

        scenario_results: List[Dict[str, Any]] = []
        format_ok_count = 0
        diversity_ok_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            input_data = scenario["input"]
            format_ok = _check_optimize_format(response)
            diversity_ok = _check_query_diversity(response, input_data)

            if format_ok:
                format_ok_count += 1
            if diversity_ok:
                diversity_ok_count += 1

            scenario_results.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "passed": format_ok and diversity_ok,
                    "metrics": {
                        "format_compliant": format_ok,
                        "query_diverse": diversity_ok,
                    },
                }
            )

        n = len(scenarios)
        gen = RegressionReportGenerator()
        report = gen.generate(
            prompt_name="query_optimize",
            prompt_version=template.version,
            prompt_hash=template.content_hash,
            scenario_results=scenario_results,
            aggregate_metrics={
                "json_format_compliance_rate": format_ok_count / n,
                "query_diversity_rate": diversity_ok_count / n,
            },
        )
        assert report.gate_passed, "Quality gate failed: " + str(report.gate_failures)
        output = gen.print_report(report)
        assert "PASSED" in output
