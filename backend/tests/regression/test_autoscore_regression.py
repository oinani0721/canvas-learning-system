# Story 7.3: AutoSCORE Prompt Regression Tests
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
Regression tests for autoscore_v*.md prompt templates.

Verifies that prompt changes do not degrade scoring quality by checking:
  - Scoring consistency (>= 80% within expected range)
  - Average score difference (<= 0.5 from expected)
"""

import logging
from typing import Any, Dict

from app.services.prompt_registry import PromptRegistry

from tests.regression.conftest import BaselineLoader, RegressionMetricsCollector
from tests.regression.report_generator import (
    RegressionReportGenerator,
)

logger = logging.getLogger(__name__)


def _score_within_range(actual: int, expected_range: Dict[str, int]) -> bool:
    """Check if a score falls within the expected [min, max] range."""
    return expected_range["min"] <= actual <= expected_range["max"]


def _evaluate_replay_scores(
    replay_response: Dict[str, Any],
    expected_output: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate a replay response against expected score ranges.
    Returns dict with per-dimension results and aggregate metrics.
    """
    scores = replay_response.get("scores", {})
    dimensions = [
        "concept_accuracy",
        "reasoning_quality",
        "knowledge_coverage",
        "knowledge_integration",
    ]

    consistent_count = 0
    total_diff = 0.0
    dim_results = {}

    for dim in dimensions:
        score_data = scores.get(dim, {})
        actual_score = score_data.get("score", -1)
        expected = expected_output.get(dim, {})

        in_range = _score_within_range(actual_score, expected)
        if in_range:
            consistent_count += 1

        midpoint = (expected["min"] + expected["max"]) / 2.0
        diff = abs(actual_score - midpoint)
        total_diff += diff

        dim_results[dim] = {
            "actual": actual_score,
            "expected_range": expected,
            "in_range": in_range,
            "diff_from_midpoint": diff,
        }

    overall_actual = replay_response.get("overall_score", -1)
    overall_expected = expected_output.get("overall", {})
    overall_in_range = _score_within_range(overall_actual, overall_expected)

    consistency_rate = consistent_count / len(dimensions) if dimensions else 0.0
    avg_diff = total_diff / len(dimensions) if dimensions else 0.0

    return {
        "dimensions": dim_results,
        "overall": {
            "actual": overall_actual,
            "expected_range": overall_expected,
            "in_range": overall_in_range,
        },
        "scoring_consistency_rate": consistency_rate,
        "avg_score_diff": avg_diff,
    }


class TestAutoScoreRegression:
    """AutoSCORE prompt regression test suite."""

    def test_prompt_loads_successfully(self, prompt_registry: PromptRegistry):
        """AC-2: Verify autoscore prompt loads via PromptRegistry."""
        content = prompt_registry.get("autoscore")
        assert len(content) > 100, "Prompt content too short"
        assert "AutoSCORE" in content
        assert "\u8bc1\u636e\u63d0\u53d6" in content or "Evidence Extraction" in content
        assert "\u6982\u5ff5\u51c6\u786e" in content or "Concept Accuracy" in content

    def test_prompt_metadata_valid(self, prompt_registry: PromptRegistry):
        """AC-1: Verify prompt metadata is present and well-formed."""
        metadata = prompt_registry.get_metadata("autoscore")
        assert metadata["name"] == "autoscore"
        assert metadata["version"] >= 1
        assert metadata["service_ref"], "service_ref should not be empty"
        assert metadata["created_at"], "created_at should not be empty"
        assert len(metadata["content_hash"]) == 64, "SHA-256 hash should be 64 chars"

    def test_prompt_contains_four_dimensions(self, prompt_registry: PromptRegistry):
        """Verify prompt defines all 4 scoring dimensions (SOLO-anchored)."""
        content = prompt_registry.get("autoscore")
        required_dims = ["\u6982\u5ff5\u51c6\u786e", "\u63a8\u7406\u8d28\u91cf",
                         "\u77e5\u8bc6\u8986\u76d6", "\u77e5\u8bc6\u6574\u5408"]
        for dim in required_dims:
            assert dim in content, "Missing scoring dimension: " + dim

    def test_prompt_contains_two_stages(self, prompt_registry: PromptRegistry):
        """Verify prompt defines both AutoSCORE stages."""
        content = prompt_registry.get("autoscore")
        assert "\u9636\u6bb5\u4e00" in content or "Phase 1" in content
        assert "\u9636\u6bb5\u4e8c" in content or "Phase 2" in content

    def test_prompt_solo_anchoring(self, prompt_registry: PromptRegistry):
        """Verify SOLO taxonomy anchoring in scoring rubric."""
        content = prompt_registry.get("autoscore")
        assert "SOLO" in content
        solo_levels = ["\u524d\u7ed3\u6784", "\u5355\u70b9\u7ed3\u6784",
                       "\u591a\u70b9\u7ed3\u6784", "\u5173\u8054\u7ed3\u6784"]
        for level in solo_levels:
            assert level in content, "Missing SOLO level: " + level

    def test_replay_scoring_consistency(
        self,
        prompt_registry: PromptRegistry,
        autoscore_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Replay mode - verify scoring consistency across all scenarios."""
        scenarios = autoscore_baselines.load_all()
        assert len(scenarios) >= 5, "Need at least 5 AutoSCORE scenarios"

        template = prompt_registry.get_template("autoscore")
        total_consistency = 0.0
        total_avg_diff = 0.0

        for scenario in scenarios:
            result = _evaluate_replay_scores(
                scenario["replay_response"],
                scenario["expected_output"],
            )

            passed = (
                result["scoring_consistency_rate"] >= 0.75
                and result["avg_score_diff"] <= 1.0
            )

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="autoscore",
                prompt_version=template.version,
                metrics={
                    "scoring_consistency_rate": result["scoring_consistency_rate"],
                    "avg_score_diff": result["avg_score_diff"],
                    "overall_in_range": result["overall"]["in_range"],
                },
                passed=passed,
                details="" if passed else "consistency={c:.2f}, avg_diff={d:.2f}".format(
                    c=result["scoring_consistency_rate"],
                    d=result["avg_score_diff"],
                ),
            )

            total_consistency += result["scoring_consistency_rate"]
            total_avg_diff += result["avg_score_diff"]

        n = len(scenarios)
        agg_consistency = total_consistency / n
        agg_avg_diff = total_avg_diff / n

        assert agg_consistency >= 0.80, (
            "Scoring consistency below 80 percent threshold: {v:.4f}".format(v=agg_consistency)
        )
        assert agg_avg_diff <= 0.5, (
            "Average score diff {v:.2f} above 0.5 threshold".format(v=agg_avg_diff)
        )

    def test_replay_full_score_scenario(self, autoscore_baselines: BaselineLoader):
        """Verify full-score scenario scores within expected range."""
        scenario = autoscore_baselines.load_one("scenario_01_full_score.json")
        result = _evaluate_replay_scores(
            scenario["replay_response"],
            scenario["expected_output"],
        )
        assert result["overall"]["in_range"], (
            "Full score overall {a} not in {r}".format(
                a=result["overall"]["actual"],
                r=result["overall"]["expected_range"],
            )
        )

    def test_replay_zero_score_scenario(self, autoscore_baselines: BaselineLoader):
        """Verify zero-score scenario scores within expected range."""
        scenario = autoscore_baselines.load_one("scenario_02_zero_score.json")
        result = _evaluate_replay_scores(
            scenario["replay_response"],
            scenario["expected_output"],
        )
        assert result["overall"]["in_range"], (
            "Zero score overall {a} not in {r}".format(
                a=result["overall"]["actual"],
                r=result["overall"]["expected_range"],
            )
        )

    def test_generate_report(
        self,
        prompt_registry: PromptRegistry,
        autoscore_baselines: BaselineLoader,
    ):
        """AC-5: Generate a structured regression report."""
        scenarios = autoscore_baselines.load_all()
        template = prompt_registry.get_template("autoscore")

        scenario_results = list()
        total_consistency = 0.0
        total_avg_diff = 0.0

        for scenario in scenarios:
            result = _evaluate_replay_scores(
                scenario["replay_response"],
                scenario["expected_output"],
            )
            passed = (
                result["scoring_consistency_rate"] >= 0.75
                and result["avg_score_diff"] <= 1.0
            )
            scenario_results.append({
                "scenario_id": scenario["scenario_id"],
                "passed": passed,
                "metrics": {
                    "scoring_consistency_rate": result["scoring_consistency_rate"],
                    "avg_score_diff": result["avg_score_diff"],
                },
            })
            total_consistency += result["scoring_consistency_rate"]
            total_avg_diff += result["avg_score_diff"]

        n = len(scenarios)
        gen = RegressionReportGenerator()
        report = gen.generate(
            prompt_name="autoscore",
            prompt_version=template.version,
            prompt_hash=template.content_hash,
            scenario_results=scenario_results,
            aggregate_metrics={
                "scoring_consistency_rate": total_consistency / n,
                "max_avg_score_diff": total_avg_diff / n,
            },
        )
        assert report.gate_passed, "Quality gate failed: " + str(report.gate_failures)
        output = gen.print_report(report)
        assert "PASSED" in output
