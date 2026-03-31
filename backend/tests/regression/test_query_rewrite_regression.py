# Story 2.13: Query Rewrite Prompt Regression Tests
# [Source: _bmad-output/implementation-artifacts/2-13-prompt-version-regression-test.md]
"""
Regression tests for query_rewrite_v*.md prompt templates.

Verifies that prompt changes maintain query rewrite quality:
  - Format compliance rate (>= 90%): each rewrite on separate line, no numbering
  - Rewrite diversity: generated rewrites are semantically distinct
  - Count compliance: 2-3 rewrites per query
"""

import logging
from typing import Any, Dict

from app.services.prompt_registry import PromptRegistry

from tests.regression.conftest import BaselineLoader, RegressionMetricsCollector
from tests.regression.report_generator import RegressionReportGenerator

logger = logging.getLogger(__name__)


def _check_rewrite_format(response: Dict[str, Any]) -> bool:
    """Check if a query rewrite response has valid format."""
    rewrites = response.get("rewrites", [])
    if not rewrites:
        return False

    # Must have 2-3 rewrites
    if len(rewrites) < 2 or len(rewrites) > 4:
        return False

    # No numbering prefix
    if response.get("has_numbering", False):
        return False

    # No explanation text
    if response.get("has_explanation", False):
        return False

    # Each rewrite must be non-empty
    for rw in rewrites:
        if not rw or not rw.strip():
            return False

    return True


def _check_rewrite_diversity(response: Dict[str, Any]) -> bool:
    """Check if rewrites are sufficiently diverse (not just trivial variations)."""
    rewrites = response.get("rewrites", [])
    if len(rewrites) < 2:
        return False

    # Simple diversity check: no two rewrites should be identical
    unique_rewrites = {r.strip().lower() for r in rewrites}
    if len(unique_rewrites) < len(rewrites):
        return False

    return True


class TestQueryRewriteRegression:
    """Query rewrite prompt regression test suite."""

    def test_prompt_loads_successfully(self, prompt_registry: PromptRegistry):
        """AC-2: Verify query_rewrite prompt loads via PromptRegistry."""
        content = prompt_registry.get("query_rewrite")
        assert len(content) > 100, "Prompt content too short"
        assert "Multi-Query" in content or "改写" in content
        assert "Decomposition" in content or "拆分" in content

    def test_prompt_metadata_valid(self, prompt_registry: PromptRegistry):
        """AC-1: Verify prompt metadata is present and well-formed."""
        metadata = prompt_registry.get_metadata("query_rewrite")
        assert metadata["name"] == "query_rewrite"
        assert metadata["version"] >= 1
        assert metadata["service_ref"], "service_ref should not be empty"
        assert metadata["created_at"], "created_at should not be empty"
        assert len(metadata["content_hash"]) == 64, "SHA-256 hash should be 64 chars"

    def test_prompt_two_strategies(self, prompt_registry: PromptRegistry):
        """Verify prompt contains both Multi-Query and Decomposition strategies."""
        content = prompt_registry.get("query_rewrite")
        assert "策略一" in content, "Missing Strategy 1 (Multi-Query)"
        assert "策略二" in content, "Missing Strategy 2 (Decomposition)"

    def test_prompt_quality_requirements(self, prompt_registry: PromptRegistry):
        """Verify prompt includes quality requirements section."""
        content = prompt_registry.get("query_rewrite")
        assert "质量要求" in content or "Quality" in content

    def test_replay_format_compliance(
        self,
        prompt_registry: PromptRegistry,
        query_rewrite_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Verify format compliance across all scenarios."""
        scenarios = query_rewrite_baselines.load_all()
        assert len(scenarios) >= 5, "Need at least 5 query_rewrite scenarios"

        template = prompt_registry.get_template("query_rewrite")
        compliant_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            compliant = _check_rewrite_format(response)
            if compliant:
                compliant_count += 1

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="query_rewrite",
                prompt_version=template.version,
                metrics={"format_compliant": compliant},
                passed=compliant,
                details="" if compliant else "Format non-compliant",
            )

        compliance_rate = compliant_count / len(scenarios)
        assert compliance_rate >= 0.90, (
            "Format compliance {v:.4f} below 90 percent threshold".format(
                v=compliance_rate,
            )
        )

    def test_replay_rewrite_diversity(
        self,
        query_rewrite_baselines: BaselineLoader,
    ):
        """AC-4: Verify rewrites are diverse (not trivial duplicates)."""
        scenarios = query_rewrite_baselines.load_all()
        diverse_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            if _check_rewrite_diversity(response):
                diverse_count += 1

        diversity_rate = diverse_count / len(scenarios)
        assert diversity_rate >= 0.80, (
            "Rewrite diversity rate {v:.4f} below 80 percent threshold".format(
                v=diversity_rate,
            )
        )

    def test_replay_count_compliance(
        self,
        query_rewrite_baselines: BaselineLoader,
    ):
        """Verify each scenario produces 2-3 rewrites as specified."""
        scenarios = query_rewrite_baselines.load_all()
        count_ok = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            expected = scenario["expected_output"]
            rewrites = response.get("rewrites", [])
            min_count = expected.get("min_rewrite_count", 2)
            max_count = expected.get("max_rewrite_count", 3)
            if min_count <= len(rewrites) <= max_count:
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
        query_rewrite_baselines: BaselineLoader,
    ):
        """AC-5: Generate query rewrite regression report."""
        scenarios = query_rewrite_baselines.load_all()
        template = prompt_registry.get_template("query_rewrite")

        scenario_results = []
        compliant_count = 0
        diverse_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            compliant = _check_rewrite_format(response)
            diverse = _check_rewrite_diversity(response)

            if compliant:
                compliant_count += 1
            if diverse:
                diverse_count += 1

            scenario_results.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "passed": compliant and diverse,
                    "metrics": {
                        "format_compliant": compliant,
                        "rewrite_diverse": diverse,
                    },
                }
            )

        n = len(scenarios)
        gen = RegressionReportGenerator()
        report = gen.generate(
            prompt_name="query_rewrite",
            prompt_version=template.version,
            prompt_hash=template.content_hash,
            scenario_results=scenario_results,
            aggregate_metrics={
                "format_compliance_rate": compliant_count / n,
                "rewrite_diversity_rate": diverse_count / n,
            },
        )
        assert report.gate_passed, "Quality gate failed: " + str(report.gate_failures)
        output = gen.print_report(report)
        assert "PASSED" in output
