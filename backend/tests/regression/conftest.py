# Story 7.3: Prompt Regression Test — Shared Fixtures
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
Shared fixtures for prompt regression tests.

Provides:
  - prompt_registry: Pre-loaded PromptRegistry instance
  - baseline_loader: Helper to load baseline scenario JSON files
  - llm_mode: Dual mode support (replay vs live)
  - regression_report: Collects per-test metrics for report generation
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pytest
from app.services.prompt_registry import PromptRegistry

logger = logging.getLogger(__name__)

# Directories
_BACKEND_DIR = Path(__file__).parent.parent.parent
_PROMPTS_DIR = _BACKEND_DIR / "app" / "prompts"
_BASELINES_DIR = _BACKEND_DIR / "tests" / "fixtures" / "regression_baselines"


def pytest_addoption(parser):
    """Add --live and --prompt CLI options for regression tests."""
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run regression tests with real LLM calls (default: replay mode)",
    )
    parser.addoption(
        "--prompt",
        action="store",
        default=None,
        help="Run regression tests only for a specific prompt name (e.g., autoscore)",
    )


@pytest.fixture(scope="session")
def is_live_mode(request) -> bool:
    """Whether tests should call real LLM (True) or use replay fixtures (False)."""
    return request.config.getoption("--live", default=False)


@pytest.fixture(scope="session")
def prompt_registry() -> PromptRegistry:
    """
    Session-scoped PromptRegistry loaded with all prompt templates.

    This is a real PromptRegistry (no mocking), loaded from the actual
    prompts/ directory.
    """
    PromptRegistry.reset_instance()
    registry = PromptRegistry.get_instance(prompts_dir=_PROMPTS_DIR)
    registry.load_all()
    return registry


@pytest.fixture(scope="session")
def baselines_dir() -> Path:
    """Path to the regression_baselines/ directory."""
    return _BASELINES_DIR


class BaselineLoader:
    """Load baseline scenario JSON files for a specific prompt type."""

    def __init__(self, prompt_name: str, baselines_dir: Path):
        self._dir = baselines_dir / prompt_name
        self._prompt_name = prompt_name

    def load_all(self) -> List[Dict[str, Any]]:
        """Load all scenario JSON files, sorted by filename."""
        if not self._dir.exists():
            raise FileNotFoundError(
                f"Baseline directory not found: {self._dir}"
            )
        scenarios = list()
        for f in sorted(self._dir.glob("scenario_*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_source_file"] = f.name
            scenarios.append(data)
        if not scenarios:
            raise FileNotFoundError(
                f"No scenario_*.json files found in {self._dir}"
            )
        return scenarios

    def load_one(self, filename: str) -> Dict[str, Any]:
        """Load a specific scenario file."""
        path = self._dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Scenario file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_source_file"] = filename
        return data


@pytest.fixture
def autoscore_baselines(baselines_dir) -> BaselineLoader:
    """Loader for AutoSCORE regression baselines."""
    return BaselineLoader("autoscore", baselines_dir)


@pytest.fixture
def question_gen_baselines(baselines_dir) -> BaselineLoader:
    """Loader for question generation regression baselines."""
    return BaselineLoader("question_gen", baselines_dir)


@pytest.fixture
def context_extract_baselines(baselines_dir) -> BaselineLoader:
    """Loader for context extraction regression baselines."""
    return BaselineLoader("context_extract", baselines_dir)


class RegressionMetricsCollector:
    """Collects per-scenario metrics during a regression test run."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = list()

    def record(
        self,
        scenario_id: str,
        prompt_name: str,
        prompt_version: int,
        metrics: Dict[str, Any],
        passed: bool,
        details: str = "",
    ):
        self.results.append({
            "scenario_id": scenario_id,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "metrics": metrics,
            "passed": passed,
            "details": details,
        })

    def summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed_count = sum(1 for r in self.results if r["passed"])
        failed_count = total - passed_count
        pass_rate = (passed_count / total * 100) if total > 0 else 0.0
        return {
            "total_scenarios": total,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": pass_rate,
            "results": self.results,
        }


@pytest.fixture
def regression_metrics() -> RegressionMetricsCollector:
    """Per-test metrics collector for regression report generation."""
    return RegressionMetricsCollector()
