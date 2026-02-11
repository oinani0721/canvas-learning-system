"""
ATDD tests for Story 34.12: 静默降级修复 + 死代码清理

Red-light tests verifying:
- AC1: except Exception specialization (18 → ≤5)
- AC2: Degradation path WARNING logs
- AC3: retention_rate real calculation (not hardcoded None)
"""
import ast
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Path to review_service.py for static analysis
REVIEW_SERVICE_PATH = Path(__file__).parent.parent.parent / "app" / "services" / "review_service.py"


# ============================================================
# AC1: except Exception specialization tests
# ============================================================

class TestExceptExceptionSpecialization:
    """AC1: except Exception count must be ≤5, each with INTENTIONAL comment."""

    def test_except_exception_count_le_5(self):
        """grep -c 'except Exception' review_service.py ≤ 5"""
        source = REVIEW_SERVICE_PATH.read_text(encoding="utf-8")
        count = len(re.findall(r"except\s+Exception\b", source))
        assert count <= 5, (
            f"Found {count} 'except Exception' in review_service.py, expected ≤5. "
            f"Specialize remaining catch-all handlers."
        )

    def test_remaining_except_exception_have_intentional_comment(self):
        """Each remaining except Exception must have # INTENTIONAL comment."""
        source = REVIEW_SERVICE_PATH.read_text(encoding="utf-8")
        lines = source.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"except\s+Exception\b", stripped):
                # Check surrounding lines (current, previous, next) for INTENTIONAL comment
                context = "\n".join(lines[max(0, i - 2):i + 3])
                assert "INTENTIONAL" in context, (
                    f"Line {i + 1}: 'except Exception' without # INTENTIONAL comment. "
                    f"Either specialize this exception or add comment explaining why catch-all is needed."
                )

    def test_file_io_uses_specific_exceptions(self):
        """File I/O operations must catch OSError/json.JSONDecodeError, not Exception."""
        source = REVIEW_SERVICE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Check if this handler catches bare Exception (named or unnamed)
                if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    # Get the line content to check context
                    line_start = node.lineno
                    lines = source.split("\n")
                    # Look at the try block above for file I/O indicators
                    context_lines = "\n".join(lines[max(0, line_start - 15):line_start])
                    if any(kw in context_lines for kw in ["read_text", "write_text", "json.loads", "json.dumps",
                                                           "_CARD_STATES_FILE", "tmp_file"]):
                        pytest.fail(
                            f"Line {line_start}: File I/O operation uses 'except Exception'. "
                            f"Should use (OSError, json.JSONDecodeError) or similar specific types."
                        )

    def test_import_operations_use_specific_exceptions(self):
        """Import/config operations must catch ImportError/RuntimeError, not Exception."""
        source = REVIEW_SERVICE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    line_start = node.lineno
                    lines = source.split("\n")
                    context_lines = "\n".join(lines[max(0, line_start - 10):line_start])
                    if any(kw in context_lines for kw in ["from app.config import", "from app.dependencies import",
                                                           "from app.services.memory_service import"]):
                        pytest.fail(
                            f"Line {line_start}: Import/config operation uses 'except Exception'. "
                            f"Should use (ImportError, RuntimeError) or similar specific types."
                        )


# ============================================================
# AC2: Degradation path WARNING log tests
# ============================================================

class TestDegradationLogging:
    """AC2: All degradation paths must produce WARNING logs."""

    def test_degradation_paths_have_warning_logs(self):
        """Every 'if xxx is None' or 'if not xxx' degradation path must log WARNING."""
        source = REVIEW_SERVICE_PATH.read_text(encoding="utf-8")
        lines = source.split("\n")

        # Known degradation patterns to check
        degradation_patterns = [
            "if not self.graphiti_client",
            "if self._fsrs_manager is None",
        ]

        issues = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            for pattern in degradation_patterns:
                if pattern in stripped:
                    # Check next 5 lines for logger.warning
                    following = "\n".join(lines[i:i + 6])
                    if "logger.warning" not in following and "logger.error" not in following:
                        issues.append(
                            f"Line {i + 1}: Degradation path '{pattern}' without WARNING log"
                        )

        assert not issues, (
            f"Found {len(issues)} degradation paths without WARNING logs:\n" +
            "\n".join(f"  - {issue}" for issue in issues)
        )

    def test_degradation_log_format_includes_required_fields(self):
        """Degradation WARNING logs must include feature name and dependency name."""
        source = REVIEW_SERVICE_PATH.read_text(encoding="utf-8")
        # Count lines containing '降级运行' near logger.warning (multiline format)
        # AC2 requires ≥3 graphiti_client degradation + ≥1 fsrs_manager degradation
        degradation_count = len(re.findall(r'降级运行', source))
        assert degradation_count >= 4, (
            f"Expected ≥4 degradation WARNING logs with '降级运行' keyword, found {degradation_count}. "
            f"AC2 requires all degradation paths (graphiti_client + fsrs_manager) to use unified format."
        )


# ============================================================
# AC3: retention_rate real calculation tests
# ============================================================

class TestRetentionRateCalculation:
    """AC3: retention_rate must not be hardcoded None."""

    def test_retention_rate_not_hardcoded_none(self):
        """retention_rate must not be '= None' hardcoded in get_history return."""
        source = REVIEW_SERVICE_PATH.read_text(encoding="utf-8")
        # Look for the specific pattern: "retention_rate": None
        hardcoded_none = re.findall(r'"retention_rate":\s*None', source)
        assert len(hardcoded_none) == 0, (
            f"Found {len(hardcoded_none)} hardcoded 'retention_rate: None'. "
            f"Must implement real calculation or remove field."
        )

    @pytest.mark.asyncio
    async def test_retention_rate_calculated_from_ratings(self):
        """retention_rate should be calculated as good_ratings / total_ratings."""
        from datetime import datetime, timezone
        from app.services.review_service import ReviewService

        # Create service WITHOUT graphiti (uses card_states path)
        mock_canvas = AsyncMock()
        mock_task_mgr = MagicMock()
        service = ReviewService(
            canvas_service=mock_canvas,
            task_manager=mock_task_mgr,
            graphiti_client=None
        )

        # Inject card_states with rating data
        today = datetime.now(timezone.utc).date()
        service._card_states = {
            f"test.canvas:concept_a": {"rating": 4, "last_review": today.isoformat()},
            f"test.canvas:concept_b": {"rating": 3, "last_review": today.isoformat()},
            f"test.canvas:concept_c": {"rating": 2, "last_review": today.isoformat()},
            f"test.canvas:concept_d": {"rating": 1, "last_review": today.isoformat()},
            f"test.canvas:concept_e": {"rating": 3, "last_review": today.isoformat()},
        }

        result = await service.get_history(days=7, limit=None)

        # 3 good ratings (≥3) out of 5 total = 0.6
        assert result.get("retention_rate") is not None, "retention_rate should not be None"
        assert isinstance(result["retention_rate"], float), "retention_rate should be a float"
        assert 0.0 <= result["retention_rate"] <= 1.0, "retention_rate should be between 0 and 1"
        assert abs(result["retention_rate"] - 0.6) < 0.01, f"Expected ~0.6, got {result['retention_rate']}"

    @pytest.mark.asyncio
    async def test_retention_rate_works_with_serialized_card_states(self):
        """retention_rate must work when _card_states values are JSON strings (production format)."""
        import json
        from datetime import datetime, timezone
        from app.services.review_service import ReviewService

        mock_canvas = AsyncMock()
        mock_task_mgr = MagicMock()
        service = ReviewService(
            canvas_service=mock_canvas,
            task_manager=mock_task_mgr,
            graphiti_client=None
        )

        # Production format: _card_states values are serialized JSON strings
        today = datetime.now(timezone.utc).date()
        service._card_states = {
            "test.canvas:concept_a": json.dumps({"rating": 4, "last_review": today.isoformat()}),
            "test.canvas:concept_b": json.dumps({"rating": 2, "last_review": today.isoformat()}),
            "test.canvas:concept_c": json.dumps({"rating": 3, "last_review": today.isoformat()}),
        }

        result = await service.get_history(days=7, limit=None)

        # 2 good ratings (≥3) out of 3 total ≈ 0.6667
        assert result.get("retention_rate") is not None, "retention_rate should work with string card_data"
        assert abs(result["retention_rate"] - 0.6667) < 0.01, f"Expected ~0.667, got {result['retention_rate']}"

    @pytest.mark.asyncio
    async def test_retention_rate_handles_empty_records(self):
        """retention_rate should be None when no records with ratings exist."""
        from app.services.review_service import ReviewService

        mock_canvas = AsyncMock()
        mock_task_mgr = MagicMock()
        service = ReviewService(
            canvas_service=mock_canvas,
            task_manager=mock_task_mgr,
            graphiti_client=None
        )
        service._card_states = {}

        result = await service.get_history(days=7)

        # With no records, retention_rate should be None (computed, not hardcoded)
        assert "retention_rate" in result
        assert result["retention_rate"] is None
