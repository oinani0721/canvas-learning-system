# Story 7.3: Prompt Regression Test — Report Generator
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
Generates structured regression test reports with before/after metric
comparison and quality threshold gate enforcement.

Usage:
    from tests.regression.report_generator import RegressionReportGenerator
    gen = RegressionReportGenerator()
    report = gen.generate(prompt_name, results, thresholds)
    gen.print_report(report)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Quality thresholds per prompt type (AC-5)
QUALITY_THRESHOLDS = {
    "autoscore": {
        "scoring_consistency_rate": 0.80,   # >= 80%
        "max_avg_score_diff": 0.5,          # <= 0.5 points
    },
    "question_gen": {
        "format_compliance_rate": 0.90,     # >= 90%
        "difficulty_match_rate": 0.70,      # >= 70%
    },
    "context_extract": {
        "extraction_recall": 0.85,          # >= 85%
        "classification_accuracy": 0.80,    # >= 80%
    },
}


class RegressionReport:
    """Structured regression test report."""

    def __init__(
        self,
        prompt_name: str,
        prompt_version: int,
        prompt_hash: str,
        timestamp: str,
        thresholds: Dict[str, float],
        scenario_results: List[Dict[str, Any]],
        aggregate_metrics: Dict[str, float],
        gate_passed: bool,
        gate_failures: List[str],
    ):
        self.prompt_name = prompt_name
        self.prompt_version = prompt_version
        self.prompt_hash = prompt_hash
        self.timestamp = timestamp
        self.thresholds = thresholds
        self.scenario_results = scenario_results
        self.aggregate_metrics = aggregate_metrics
        self.gate_passed = gate_passed
        self.gate_failures = gate_failures

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_name": self.prompt_name,
            "prompt_version": self.prompt_version,
            "prompt_hash": self.prompt_hash,
            "timestamp": self.timestamp,
            "thresholds": self.thresholds,
            "scenario_results": self.scenario_results,
            "aggregate_metrics": self.aggregate_metrics,
            "gate_passed": self.gate_passed,
            "gate_failures": self.gate_failures,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class RegressionReportGenerator:
    """Generates and evaluates regression test reports."""

    def generate(
        self,
        prompt_name: str,
        prompt_version: int,
        prompt_hash: str,
        scenario_results: List[Dict[str, Any]],
        aggregate_metrics: Dict[str, float],
        thresholds: Optional[Dict[str, float]] = None,
    ) -> RegressionReport:
        """
        Generate a regression report with quality gate evaluation.

        Args:
            prompt_name: Name of the prompt template (e.g., "autoscore")
            prompt_version: Version number
            prompt_hash: SHA-256 content hash
            scenario_results: Per-scenario test results
            aggregate_metrics: Aggregated metrics across all scenarios
            thresholds: Custom thresholds (defaults to QUALITY_THRESHOLDS)

        Returns:
            RegressionReport with gate pass/fail evaluation
        """
        if thresholds is None:
            thresholds = QUALITY_THRESHOLDS.get(prompt_name, {})

        timestamp = datetime.now(timezone.utc).isoformat()

        # Evaluate quality gates
        gate_failures = list()
        for metric_name, threshold_value in thresholds.items():
            actual = aggregate_metrics.get(metric_name)
            if actual is None:
                gate_failures.append(
                    f"{metric_name}: metric not reported (threshold={threshold_value})"
                )
                continue

            # For "max_" prefixed metrics, the actual must be <= threshold
            if metric_name.startswith("max_"):
                if actual > threshold_value:
                    gate_failures.append(
                        f"{metric_name}: {actual:.3f} > {threshold_value:.3f} (EXCEEDED)"
                    )
            else:
                # For rate/recall/accuracy metrics, actual must be >= threshold
                if actual < threshold_value:
                    gate_failures.append(
                        f"{metric_name}: {actual:.3f} < {threshold_value:.3f} (BELOW THRESHOLD)"
                    )

        gate_passed = len(gate_failures) == 0

        return RegressionReport(
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            prompt_hash=prompt_hash,
            timestamp=timestamp,
            thresholds=thresholds,
            scenario_results=scenario_results,
            aggregate_metrics=aggregate_metrics,
            gate_passed=gate_passed,
            gate_failures=gate_failures,
        )

    def print_report(self, report: RegressionReport) -> str:
        """Format the report as a human-readable terminal table."""
        lines = list()
        lines.append("=" * 72)
        lines.append(f"  PROMPT REGRESSION REPORT: {report.prompt_name} v{report.prompt_version}")
        lines.append(f"  Hash: {report.prompt_hash[:16]}...")
        lines.append(f"  Time: {report.timestamp}")
        lines.append("=" * 72)
        lines.append("")

        # Aggregate metrics
        lines.append("  AGGREGATE METRICS")
        lines.append("  " + "-" * 40)
        for k, v in sorted(report.aggregate_metrics.items()):
            threshold = report.thresholds.get(k)
            status = ""
            if threshold is not None:
                if k.startswith("max_"):
                    status = " OK" if v <= threshold else " FAIL"
                else:
                    status = " OK" if v >= threshold else " FAIL"
                status += f" (threshold: {threshold:.3f})"
            lines.append(f"  {k:40s} {v:8.3f}{status}")
        lines.append("")

        # Gate result
        if report.gate_passed:
            lines.append("  QUALITY GATE: PASSED")
        else:
            lines.append("  QUALITY GATE: FAILED")
            for f in report.gate_failures:
                lines.append(f"    - {f}")
        lines.append("")

        # Per-scenario results
        lines.append("  SCENARIO RESULTS")
        lines.append("  " + "-" * 40)
        for sc in report.scenario_results:
            sc_id = sc.get("scenario_id", "?")
            passed = sc.get("passed", False)
            status_str = "PASS" if passed else "FAIL"
            lines.append(f"  [{status_str}] {sc_id}")
            if not passed and sc.get("details"):
                lines.append(f"         {sc['details']}")
        lines.append("")
        lines.append("=" * 72)

        output = "\n".join(lines)
        print(output)
        return output

    def save_report(self, report: RegressionReport, output_dir: Path) -> Path:
        """Save report as JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"regression_{report.prompt_name}_v{report.prompt_version}"
            f"_{report.timestamp[:10]}.json"
        )
        path = output_dir / filename
        path.write_text(report.to_json(), encoding="utf-8")
        logger.info("[ReportGenerator] Report saved to %s", path)
        return path
