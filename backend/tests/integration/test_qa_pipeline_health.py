# Canvas Learning System - QA Pipeline Health Integration Tests
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Integration tests for the pipeline health aggregation system:
  - End-to-end: DifficultyMatcher -> stats -> PipelineHealthMonitor
  - End-to-end: ExtractionValidator -> stats -> QA metrics API
  - End-to-end: ErrorAggregator -> aggregation -> pipeline health
  - Full pipeline health metric collection

[Source: Story 7.4 Task 8.4, 8.5]
"""

import pytest
from app.models.qa_models import PipelineHealthStatus
from app.services.difficulty_matcher import DifficultyMatcher
from app.services.error_aggregator import ErrorAggregator
from app.services.extraction_validator import ExtractionValidator
from app.services.health_monitor import PipelineHealthMonitor

# ═══════════════════════════════════════════════════════════════════════════════
# End-to-end: Difficulty -> Stats -> Health
# ═══════════════════════════════════════════════════════════════════════════════


class TestDifficultyToHealth:
    """Test the full chain from difficulty evaluation to health metrics."""

    @pytest.mark.asyncio
    async def test_difficulty_evaluation_feeds_health(self, tmp_path):
        db_path = str(tmp_path / "test_health.db")
        matcher = DifficultyMatcher(db_path)

        # Provide a deterministic difficulty estimator for testing
        async def deterministic_estimate(question: str) -> float:
            return 0.5

        matcher.estimate_difficulty = deterministic_estimate

        # Generate 10 matched evaluations
        for i in range(10):
            await matcher.evaluate(f"node_{i}", f"Q{i}?", 0.5)

        stats = matcher.get_stats()
        assert stats.total_in_window == 10
        assert stats.match_rate == 1.0
        assert stats.is_healthy is True

    @pytest.mark.asyncio
    async def test_low_match_rate_triggers_unhealthy(self, tmp_path):
        db_path = str(tmp_path / "test_low.db")
        matcher = DifficultyMatcher(db_path)

        call_count = 0

        async def alternating_estimate(question: str) -> float:
            nonlocal call_count
            call_count += 1
            # Return 0.95 (way out of range) for most questions
            if call_count % 5 == 0:
                return 0.5
            return 0.95

        matcher.estimate_difficulty = alternating_estimate

        for i in range(10):
            await matcher.evaluate(f"node_{i}", f"Q{i}?", 0.5)

        stats = matcher.get_stats()
        assert stats.match_rate < 0.7
        assert stats.is_healthy is False


# ═══════════════════════════════════════════════════════════════════════════════
# End-to-end: Extraction -> Stats -> QA Metrics
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtractionToMetrics:
    """Test extraction validation through to QA metrics."""

    @pytest.mark.asyncio
    async def test_extraction_stats_reflect_annotations(self, tmp_path):
        db_path = str(tmp_path / "test_ext.db")
        v = ExtractionValidator(db_path)

        # Store and annotate records
        records = []
        for i in range(6):
            r = await v.store_record(
                f"s{i}",
                f"n{i}",
                f"orig_{i}",
                f"ext_{i}",
                "error" if i < 4 else "tip",
            )
            records.append(r)

        # Annotate: 4 correct out of 5 annotated
        await v.annotate(records[0].id, "correct")
        await v.annotate(records[1].id, "correct")
        await v.annotate(records[2].id, "correct")
        await v.annotate(records[3].id, "incorrect")
        await v.annotate(records[4].id, "correct")
        # records[5] left unannotated

        stats = await v.get_stats()
        assert stats.total_records == 6
        assert stats.annotated_count == 5
        assert stats.accuracy == pytest.approx(0.8, abs=0.01)
        assert "error" in stats.by_type
        assert "tip" in stats.by_type


# ═══════════════════════════════════════════════════════════════════════════════
# End-to-end: Error -> Aggregation
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorToAggregation:
    """Test error classification and aggregation chain."""

    @pytest.mark.asyncio
    async def test_mixed_errors_aggregate(self, tmp_path):
        db_path = str(tmp_path / "test_agg.db")
        agg = ErrorAggregator(db_path)

        # Record diverse error types
        await agg.record_error(ValueError("bad"))
        await agg.record_error(KeyError("missing"))
        await agg.record_error(ConnectionError("refused"))
        await agg.record_error(TimeoutError("slow"))

        result = await agg.get_aggregation()

        # 24h window
        assert result.last_24h.algorithm_errors == 2
        assert result.last_24h.network_errors == 2

        # 7d window (same data)
        assert result.last_7d.algorithm_errors == 2
        assert result.last_7d.network_errors == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline Health Monitor
# ═══════════════════════════════════════════════════════════════════════════════


class TestPipelineHealthMonitor:
    """Test the health monitor collects and aggregates metrics."""

    @pytest.mark.asyncio
    async def test_health_monitor_returns_valid_structure(self):
        """Health monitor should produce a valid PipelineHealthStatus even
        when upstream services are not fully configured."""
        monitor = PipelineHealthMonitor()
        health = await monitor.get_health()

        assert isinstance(health, PipelineHealthStatus)
        assert health.overall in ("healthy", "degraded", "critical")
        assert len(health.metrics) == 7
        assert health.last_updated

        # Each metric should have required fields
        for metric in health.metrics:
            assert metric.name
            assert metric.status in ("healthy", "warning", "critical")
            assert metric.threshold

    @pytest.mark.asyncio
    async def test_health_monitor_caching(self):
        """Second call within TTL should produce the cached result."""
        monitor = PipelineHealthMonitor()
        health1 = await monitor.get_health()
        health2 = await monitor.get_health()

        # Same object due to caching
        assert health1 is health2
