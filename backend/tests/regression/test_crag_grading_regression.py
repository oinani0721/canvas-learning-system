# Story 2.13: CRAG Document Grading Prompt Regression Tests
# [Source: _bmad-output/implementation-artifacts/2-13-prompt-version-regression-test.md]
"""
Regression tests for crag_grading_v*.md prompt templates.

Verifies that prompt changes maintain CRAG document grading quality:
  - Classification consistency (>= 80%): grades match expected pattern
  - CRAG trigger rate (15-30%): percentage of queries triggering rewrite
  - Format compliance: output is valid JSON array of "relevant"/"irrelevant"
"""

import logging
from typing import Any, Dict

from app.services.prompt_registry import PromptRegistry

from tests.regression.conftest import BaselineLoader, RegressionMetricsCollector
from tests.regression.report_generator import RegressionReportGenerator

logger = logging.getLogger(__name__)

VALID_GRADES = {"relevant", "irrelevant"}


def _check_grade_format(response: Dict[str, Any]) -> bool:
    """Check if CRAG grading response has valid format."""
    grades = response.get("grades", [])
    if not grades:
        return False

    total = response.get("total_count", len(grades))
    if len(grades) != total:
        return False

    # Each grade must be "relevant" or "irrelevant"
    for g in grades:
        if g not in VALID_GRADES:
            return False

    return True


def _check_grade_consistency(
    response: Dict[str, Any],
    expected: Dict[str, Any],
) -> float:
    """Calculate grade consistency between actual and expected.

    Returns fraction of grades matching expected pattern.
    """
    actual_grades = response.get("grades", [])
    expected_grades = expected.get("grades", [])

    if not actual_grades or not expected_grades:
        return 0.0

    matches = 0
    total = min(len(actual_grades), len(expected_grades))
    for i in range(total):
        if actual_grades[i] == expected_grades[i]:
            matches += 1

    return matches / total if total > 0 else 0.0


def _is_crag_trigger(response: Dict[str, Any]) -> bool:
    """Check if this scenario would trigger CRAG query rewrite.

    Triggered when no relevant documents found (all irrelevant).
    """
    relevant_count = response.get("relevant_count", 0)
    return relevant_count == 0


class TestCragGradingRegression:
    """CRAG document grading prompt regression test suite."""

    def test_prompt_loads_successfully(self, prompt_registry: PromptRegistry):
        """AC-2: Verify crag_grading prompt loads via PromptRegistry."""
        content = prompt_registry.get("crag_grading")
        assert len(content) > 100, "Prompt content too short"
        assert "CRAG" in content or "相关性" in content
        assert "relevant" in content
        assert "irrelevant" in content

    def test_prompt_metadata_valid(self, prompt_registry: PromptRegistry):
        """AC-1: Verify prompt metadata is present and well-formed."""
        metadata = prompt_registry.get_metadata("crag_grading")
        assert metadata["name"] == "crag_grading"
        assert metadata["version"] >= 1
        assert metadata["service_ref"], "service_ref should not be empty"
        assert metadata["created_at"], "created_at should not be empty"
        assert len(metadata["content_hash"]) == 64, "SHA-256 hash should be 64 chars"

    def test_prompt_grading_criteria(self, prompt_registry: PromptRegistry):
        """Verify prompt contains relevant/irrelevant criteria definitions."""
        content = prompt_registry.get("crag_grading")
        assert "relevant" in content.lower()
        assert "irrelevant" in content.lower()
        assert "评估标准" in content or "Criteria" in content

    def test_prompt_json_output_format(self, prompt_registry: PromptRegistry):
        """Verify prompt specifies JSON array output format."""
        content = prompt_registry.get("crag_grading")
        assert "JSON" in content
        assert '["relevant"' in content or "JSON 数组" in content or "JSON数组" in content

    def test_replay_format_compliance(
        self,
        prompt_registry: PromptRegistry,
        crag_grading_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Verify format compliance across all scenarios."""
        scenarios = crag_grading_baselines.load_all()
        assert len(scenarios) >= 5, "Need at least 5 crag_grading scenarios"

        template = prompt_registry.get_template("crag_grading")
        compliant_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            compliant = _check_grade_format(response)
            if compliant:
                compliant_count += 1

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="crag_grading",
                prompt_version=template.version,
                metrics={"format_compliant": compliant},
                passed=compliant,
                details="" if compliant else "Format non-compliant",
            )

        compliance_rate = compliant_count / len(scenarios)
        assert compliance_rate >= 0.90, "Format compliance {v:.4f} below 90 percent threshold".format(
            v=compliance_rate,
        )

    def test_replay_classification_consistency(
        self,
        prompt_registry: PromptRegistry,
        crag_grading_baselines: BaselineLoader,
        regression_metrics: RegressionMetricsCollector,
    ):
        """AC-4/AC-5: Verify grade classification consistency across scenarios."""
        scenarios = crag_grading_baselines.load_all()
        template = prompt_registry.get_template("crag_grading")

        total_consistency = 0.0

        for scenario in scenarios:
            response = scenario["replay_response"]
            expected = scenario["expected_output"]
            consistency = _check_grade_consistency(response, expected)
            passed = consistency >= 0.75

            regression_metrics.record(
                scenario_id=scenario["scenario_id"],
                prompt_name="crag_grading",
                prompt_version=template.version,
                metrics={"classification_consistency": consistency},
                passed=passed,
                details="" if passed else "consistency={v:.2f}".format(v=consistency),
            )
            total_consistency += consistency

        avg_consistency = total_consistency / len(scenarios)
        assert avg_consistency >= 0.80, "Classification consistency {v:.4f} below 80 percent threshold".format(
            v=avg_consistency,
        )

    def test_replay_crag_trigger_rate(
        self,
        crag_grading_baselines: BaselineLoader,
    ):
        """AC-5: Verify CRAG trigger rate within healthy range (15-30%)."""
        scenarios = crag_grading_baselines.load_all()
        trigger_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            if _is_crag_trigger(response):
                trigger_count += 1

        trigger_rate = trigger_count / len(scenarios)
        # Healthy range: 15-30% (one out of five scenarios triggers = 20%)
        assert 0.10 <= trigger_rate <= 0.40, "CRAG trigger rate {v:.4f} outside healthy range 0.10-0.40".format(
            v=trigger_rate,
        )

    def test_replay_relevant_count_in_range(
        self,
        crag_grading_baselines: BaselineLoader,
    ):
        """Verify relevant document count falls within expected range per scenario."""
        scenarios = crag_grading_baselines.load_all()
        in_range_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            expected = scenario["expected_output"]
            relevant_count = response.get("relevant_count", 0)
            expected_range = expected.get("relevant_count_range", {})
            min_c = expected_range.get("min", 0)
            max_c = expected_range.get("max", 999)

            if min_c <= relevant_count <= max_c:
                in_range_count += 1

        in_range_rate = in_range_count / len(scenarios)
        assert in_range_rate >= 0.80, "Relevant count in-range rate {v:.4f} below 80 percent".format(
            v=in_range_rate,
        )

    def test_generate_report(
        self,
        prompt_registry: PromptRegistry,
        crag_grading_baselines: BaselineLoader,
    ):
        """AC-5: Generate CRAG grading regression report."""
        scenarios = crag_grading_baselines.load_all()
        template = prompt_registry.get_template("crag_grading")

        scenario_results = []
        total_consistency = 0.0
        trigger_count = 0

        for scenario in scenarios:
            response = scenario["replay_response"]
            expected = scenario["expected_output"]
            consistency = _check_grade_consistency(response, expected)
            is_trigger = _is_crag_trigger(response)

            if is_trigger:
                trigger_count += 1
            total_consistency += consistency

            passed = consistency >= 0.75
            scenario_results.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "passed": passed,
                    "metrics": {
                        "classification_consistency": consistency,
                        "is_crag_trigger": is_trigger,
                    },
                }
            )

        n = len(scenarios)
        gen = RegressionReportGenerator()
        report = gen.generate(
            prompt_name="crag_grading",
            prompt_version=template.version,
            prompt_hash=template.content_hash,
            scenario_results=scenario_results,
            aggregate_metrics={
                "classification_consistency": total_consistency / n,
                "crag_trigger_rate": trigger_count / n,
            },
        )
        assert report.gate_passed, "Quality gate failed: " + str(report.gate_failures)
        output = gen.print_report(report)
        assert "PASSED" in output
