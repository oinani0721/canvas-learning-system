"""
Unit tests for QAGateGenerator.

Tests the QA Gate YAML file generation functionality.
"""

import pytest
import yaml
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from qa_gate_generator import QAGateGenerator, GateResult


class TestQAGateGenerator:
    """Test cases for QAGateGenerator."""

    @pytest.fixture
    def generator(self):
        return QAGateGenerator()

    @pytest.fixture
    def sample_result_success(self):
        """Sample .worktree-result.json data for SUCCESS outcome."""
        return {
            "story_id": "12.5",
            "outcome": "SUCCESS",
            "tests_passed": True,
            "test_count": 48,
            "test_coverage": 94.0,
            "qa_gate": "PASS",
            "commit_sha": "abc1234567890",
            "timestamp": "2025-11-29T18:00:00Z",
            "qa_record": {
                "quality_score": 88,
                "ac_coverage": {
                    "AC1": {"status": "PASS", "evidence": "test_app_creation"},
                    "AC2": {"status": "PASS", "evidence": "test_cors_middleware"},
                    "AC3": {"status": "FAIL", "evidence": "test_auth_header"}
                },
                "issues_found": [
                    {"severity": "low", "description": "Consider adding rate limiting"},
                    {"severity": "medium", "description": "Error messages could be more specific"}
                ],
                "recommendations": ["Add OpenTelemetry integration", "Improve error handling"]
            }
        }

    @pytest.fixture
    def sample_result_blocked(self):
        """Sample .worktree-result.json data for DEV_BLOCKED outcome."""
        return {
            "story_id": "12.6",
            "outcome": "DEV_BLOCKED",
            "tests_passed": False,
            "test_count": 20,
            "qa_gate": None,
            "blocking_reason": "Unit tests failing - import error in module",
            "qa_record": {}
        }

    @pytest.fixture
    def sample_result_concerns(self):
        """Sample .worktree-result.json data for QA_CONCERNS_UNFIXED outcome."""
        return {
            "story_id": "12.7",
            "outcome": "QA_CONCERNS_UNFIXED",
            "tests_passed": True,
            "test_count": 35,
            "qa_gate": "CONCERNS",
            "qa_record": {
                "quality_score": 65,
                "issues_found": [
                    {"severity": "high", "description": "Missing error handling for edge case"},
                    {"severity": "medium", "description": "Code duplication in handlers"}
                ],
                "recommendations": [
                    {"action": "Add error handling", "priority": "high"},
                    {"action": "Refactor handlers", "priority": "medium"}
                ]
            }
        }

    def test_slugify_basic(self, generator):
        """Test basic slugify functionality."""
        assert generator._slugify("User Authentication") == "user-authentication"
        assert generator._slugify("FastAPI Application") == "fastapi-application"

    def test_slugify_special_characters(self, generator):
        """Test slugify with special characters."""
        assert generator._slugify("User Auth - Login!") == "user-auth-login"
        assert generator._slugify("E2E Tests (integration)") == "e2e-tests-integration"
        assert generator._slugify("Story with 'quotes'") == "story-with-quotes"

    def test_slugify_chinese_characters(self, generator):
        """Test slugify removes non-ASCII (Chinese) characters."""
        slug = generator._slugify("FastAPI应用初始化")
        assert "应用" not in slug
        assert slug == "fastapi"

    def test_slugify_length_limit(self, generator):
        """Test slugify truncates long strings."""
        long_title = "This is a very long story title that should be truncated to fifty characters"
        slug = generator._slugify(long_title)
        assert len(slug) <= 50

    def test_slugify_empty_fallback(self, generator):
        """Test slugify returns 'story' for empty/non-ASCII-only strings."""
        assert generator._slugify("") == "story"
        assert generator._slugify("中文标题") == "story"

    def test_build_gate_data_success(self, generator, sample_result_success):
        """Test gate data building for SUCCESS outcome."""
        gate_data = generator._build_gate_data("12.5", "Test Story", sample_result_success)

        assert gate_data["schema"] == 1
        assert gate_data["story"] == "12.5"
        assert gate_data["story_title"] == "Test Story"
        assert gate_data["gate"] == "PASS"
        assert gate_data["quality_score"] == 88
        assert gate_data["reviewer"] == "Quinn (Test Architect)"

        # Check AC coverage
        assert 1 in gate_data["evidence"]["trace"]["ac_covered"]
        assert 2 in gate_data["evidence"]["trace"]["ac_covered"]
        assert 3 in gate_data["evidence"]["trace"]["ac_gaps"]

        # Check issues
        assert len(gate_data["top_issues"]) == 2
        assert gate_data["top_issues"][0]["severity"] == "low"

    def test_build_gate_data_blocked(self, generator, sample_result_blocked):
        """Test gate data building for DEV_BLOCKED outcome."""
        gate_data = generator._build_gate_data("12.6", "Blocked Story", sample_result_blocked)

        assert gate_data["gate"] == "FAIL"
        assert "Unit tests failing" in gate_data["status_reason"]

    def test_build_gate_data_concerns(self, generator, sample_result_concerns):
        """Test gate data building for QA_CONCERNS_UNFIXED outcome."""
        gate_data = generator._build_gate_data("12.7", "Concerns Story", sample_result_concerns)

        assert gate_data["gate"] == "CONCERNS"
        assert gate_data["quality_score"] == 65

        # Check high priority recommendations in must_fix
        assert len(gate_data["risk_summary"]["recommendations"]["must_fix"]) > 0

    def test_build_gate_data_risk_totals(self, generator, sample_result_success):
        """Test risk totals calculation."""
        gate_data = generator._build_gate_data("12.5", "Test", sample_result_success)

        risk_totals = gate_data["risk_summary"]["totals"]
        assert risk_totals["low"] == 1
        assert risk_totals["medium"] == 1
        assert risk_totals["high"] == 0
        assert risk_totals["critical"] == 0

    def test_build_gate_data_nfr_validation(self, generator, sample_result_success):
        """Test NFR validation structure."""
        gate_data = generator._build_gate_data("12.5", "Test", sample_result_success)

        nfr = gate_data["nfr_validation"]
        assert nfr["security"]["status"] == "PASS"
        assert nfr["performance"]["status"] == "PASS"
        assert nfr["reliability"]["status"] == "PASS"
        assert nfr["maintainability"]["status"] == "PASS"

    def test_build_gate_data_expiry_timestamp(self, generator, sample_result_success):
        """Test expires timestamp is set."""
        gate_data = generator._build_gate_data("12.5", "Test", sample_result_success)

        assert "expires" in gate_data
        assert "updated" in gate_data
        # Check format - should be ISO with Z
        assert gate_data["expires"].endswith("Z")
        assert gate_data["updated"].endswith("Z")

    def test_generate_gate_creates_file(self, generator, sample_result_success):
        """Test gate generation creates YAML file."""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            result = generator.generate_gate(
                story_id="12.5",
                story_title="Test Story Title",
                result=sample_result_success,
                output_dir=output_dir
            )

            assert result.success is True
            assert result.gate_status == "PASS"
            assert result.quality_score == 88
            assert result.gate_file.exists()
            assert "12.5-test-story-title.yml" == result.gate_file.name

    def test_generate_gate_valid_yaml(self, generator, sample_result_success):
        """Test generated file is valid YAML."""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            result = generator.generate_gate(
                story_id="12.5",
                story_title="Test Story",
                result=sample_result_success,
                output_dir=output_dir
            )

            # Read and parse YAML
            with open(result.gate_file, "r", encoding="utf-8") as f:
                gate_data = yaml.safe_load(f)

            assert gate_data["schema"] == 1
            assert gate_data["story"] == "12.5"
            assert gate_data["gate"] == "PASS"

    def test_generate_gate_creates_directory(self, generator, sample_result_success):
        """Test gate generation creates output directory if needed."""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "qa" / "gates"

            result = generator.generate_gate(
                story_id="12.5",
                story_title="Test Story",
                result=sample_result_success,
                output_dir=output_dir
            )

            assert result.success is True
            assert output_dir.exists()
            assert result.gate_file.exists()

    def test_generate_gate_error_handling(self, generator):
        """Test gate generation handles errors gracefully."""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Pass invalid result data that might cause issues
            bad_result = {"invalid": "data"}

            result = generator.generate_gate(
                story_id="12.5",
                story_title="Test",
                result=bad_result,
                output_dir=output_dir
            )

            # Should still succeed with defaults
            assert result.success is True

    def test_get_gate_file_path(self, generator):
        """Test get_gate_file_path returns expected path."""
        output_dir = Path("/fake/output")

        path = generator.get_gate_file_path("12.5", "Test Story Title", output_dir)

        assert path.name == "12.5-test-story-title.yml"
        assert path.parent == output_dir

    def test_waived_gate_includes_waiver_details(self, generator):
        """Test WAIVED gate includes waiver details."""
        result_waived = {
            "story_id": "12.8",
            "outcome": "SUCCESS",
            "qa_gate": "WAIVED",
            "waiver_reason": "Accepted minor issues for deadline",
            "qa_record": {}
        }

        gate_data = generator._build_gate_data("12.8", "Waived Story", result_waived)

        assert gate_data["gate"] == "WAIVED"
        assert gate_data["waiver"]["active"] is True
        assert "Accepted" in gate_data["waiver"]["reason"]

    def test_default_quality_score_calculation(self, generator):
        """Test quality score calculation when not provided."""
        result_no_score = {
            "story_id": "12.9",
            "outcome": "SUCCESS",
            "qa_gate": "PASS",
            "qa_record": {
                "issues_found": [
                    {"severity": "high", "description": "Issue 1"},
                    {"severity": "medium", "description": "Issue 2"},
                    {"severity": "low", "description": "Issue 3"}
                ],
                "ac_coverage": {
                    "AC1": {"status": "PASS"},
                    "AC2": {"status": "FAIL"}
                }
            }
        }

        gate_data = generator._build_gate_data("12.9", "Test", result_no_score)

        # Score should be calculated: 100 - 10(high) - 5(medium) - 2(low) - 5(1 gap) = 78
        assert gate_data["quality_score"] == 78


class TestGateResult:
    """Test cases for GateResult dataclass."""

    def test_gate_result_success(self):
        result = GateResult(
            gate_file=Path("test.yml"),
            story_id="12.5",
            gate_status="PASS",
            quality_score=88,
            success=True
        )
        assert result.success is True
        assert result.error is None

    def test_gate_result_error(self):
        result = GateResult(
            gate_file=Path("error.yml"),
            story_id="12.5",
            gate_status="ERROR",
            quality_score=0,
            success=False,
            error="File write failed"
        )
        assert result.success is False
        assert result.error == "File write failed"

    def test_gate_result_to_dict(self):
        result = GateResult(
            gate_file=Path("test.yml"),
            story_id="12.5",
            gate_status="PASS",
            quality_score=88,
            success=True
        )
        d = result.to_dict()
        assert d["story_id"] == "12.5"
        assert d["gate_status"] == "PASS"
        assert d["quality_score"] == 88
        assert d["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
