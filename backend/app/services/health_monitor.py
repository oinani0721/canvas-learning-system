# Canvas Learning System - Pipeline Health Monitor
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Aggregates 7 pipeline health indicators into a unified status view
with 30-second TTL caching to avoid real-time polling overhead.

Health metrics:
  1. Search channel liveness (6 channels)
  2. Config parameter propagation
  3. Index consistency (no duplicates)
  4. Reranker effectiveness
  5. CRAG trigger rate (healthy: 15-30%)
  6. Faithfulness average score (>= 0.85)
  7. Difficulty match rate (>= 70%)

Each metric is independently evaluated and assigned a traffic-light status:
  - healthy (green): within normal range
  - warning (yellow): approaching threshold
  - critical (red): below threshold

Overall status:
  - healthy: all metrics healthy
  - degraded: at least one warning
  - critical: at least one critical

[Source: Story 7.4 AC-5, AC-6]
[Source: architecture.md#Infrastructure — monitoring: pipeline health indicators]
"""

import asyncio
import logging
import time
from typing import Optional

from app.models.qa_models import (
    ErrorAggregation,
    HealthMetric,
    PipelineHealthStatus,
)

logger = logging.getLogger(__name__)

# Cache TTL in seconds
_CACHE_TTL_SECONDS = 30


class PipelineHealthMonitor:
    """Aggregates pipeline health metrics with caching.

    [Source: Story 7.4 Task 3]
    """

    def __init__(self):
        self._cache: Optional[PipelineHealthStatus] = None
        self._cache_time: float = 0.0
        self._refresh_lock = asyncio.Lock()

    async def get_health(self) -> PipelineHealthStatus:
        """Return cached or freshly computed pipeline health status.

        Uses a 30-second TTL cache to avoid expensive real-time checks
        on every request.

        [Source: Story 7.4 Dev Notes — 30s TTL cache]
        """
        now = time.monotonic()
        if self._cache and (now - self._cache_time) < _CACHE_TTL_SECONDS:
            return self._cache

        async with self._refresh_lock:
            # Double-check after acquiring lock
            if self._cache and (time.monotonic() - self._cache_time) < _CACHE_TTL_SECONDS:
                return self._cache

            status = await self._collect_metrics()
            self._cache = status
            self._cache_time = time.monotonic()
            return status

    async def _collect_metrics(self) -> PipelineHealthStatus:
        """Collect all 7 health metrics and compute overall status."""
        metrics = []

        # Collect each metric independently, catching errors per-metric
        collectors = [
            self._check_search_channels,
            self._check_config_propagation,
            self._check_index_consistency,
            self._check_reranker_status,
            self._check_crag_trigger_rate,
            self._check_faithfulness_score,
            self._check_difficulty_match_rate,
        ]

        for collector in collectors:
            try:
                metric = await collector()
                metrics.append(metric)
            except Exception as e:
                # If a collector fails, report the metric as critical
                metrics.append(
                    HealthMetric(
                        name=collector.__name__.replace("_check_", ""),
                        status="critical",
                        value="error",
                        threshold="N/A",
                        message=f"Health check failed: {str(e)[:200]}",
                    )
                )

        # Determine overall status
        statuses = [m.status for m in metrics]
        if "critical" in statuses:
            overall = "critical"
        elif "warning" in statuses:
            overall = "degraded"
        else:
            overall = "healthy"

        # Get error aggregation
        error_summary = await self._get_error_summary()

        # Log any unhealthy metrics
        unhealthy = [m for m in metrics if m.status != "healthy"]
        if unhealthy:
            names = ", ".join(f"{m.name}({m.status})" for m in unhealthy)
            logger.warning(f"[Story 7.4] Pipeline health: {overall} — unhealthy: {names}")

        from datetime import datetime, timezone

        return PipelineHealthStatus(
            overall=overall,
            metrics=metrics,
            last_updated=datetime.now(timezone.utc).isoformat(),
            error_summary=error_summary,
        )

    # ───────────────────────────────────────────────────────────────────────
    # Metric 1: Search channel liveness
    # [Source: Story 7.4 Task 3.2]
    # ───────────────────────────────────────────────────────────────────────

    async def _check_search_channels(self) -> HealthMetric:
        """Check if 6 search channels are alive.

        Channels: Dense, Sparse, Graphiti, Vault, CLI, Image.
        Reads from the latest search pipeline execution log rather than
        probing each channel in real-time.
        """
        # Read channel status from the search pipeline's last execution
        # This avoids expensive real-time probing
        try:
            from app.services.rag_service import get_rag_service

            rag = get_rag_service()
            channel_statuses = getattr(rag, "_last_channel_status", None)

            if channel_statuses is None:
                return HealthMetric(
                    name="search_channels",
                    status="warning",
                    value="no data",
                    threshold="6/6 channels alive",
                    message="No search execution data yet",
                )

            alive = sum(1 for v in channel_statuses.values() if v)
            total = len(channel_statuses)
            status = "healthy" if alive == total else ("warning" if alive >= 4 else "critical")

            return HealthMetric(
                name="search_channels",
                status=status,
                value=f"{alive}/{total}",
                threshold="6/6 channels alive",
                message=None if status == "healthy" else f"Only {alive}/{total} channels alive",
            )
        except Exception:
            return HealthMetric(
                name="search_channels",
                status="warning",
                value="unavailable",
                threshold="6/6 channels alive",
                message="RAG service not available for channel check",
            )

    # ───────────────────────────────────────────────────────────────────────
    # Metric 2: Config parameter propagation
    # [Source: Story 7.4 Task 3.3]
    # ───────────────────────────────────────────────────────────────────────

    async def _check_config_propagation(self) -> HealthMetric:
        """Verify key configuration parameters are valid and propagated."""
        try:
            from app.config import get_settings

            settings = get_settings()
            issues = []

            if not settings.CANVAS_BASE_PATH:
                issues.append("CANVAS_BASE_PATH empty")
            if not settings.NEO4J_URI:
                issues.append("NEO4J_URI empty")

            if issues:
                return HealthMetric(
                    name="config_propagation",
                    status="critical",
                    value=f"{len(issues)} issues",
                    threshold="All parameters valid",
                    message="; ".join(issues),
                )

            return HealthMetric(
                name="config_propagation",
                status="healthy",
                value="all valid",
                threshold="All parameters valid",
            )
        except Exception as e:
            return HealthMetric(
                name="config_propagation",
                status="critical",
                value="error",
                threshold="All parameters valid",
                message=str(e)[:200],
            )

    # ───────────────────────────────────────────────────────────────────────
    # Metric 3: Index consistency
    # [Source: Story 7.4 Task 3.4]
    # ───────────────────────────────────────────────────────────────────────

    async def _check_index_consistency(self) -> HealthMetric:
        """Check for duplicate indices in LanceDB."""
        try:
            from app.services.lancedb_index_service import get_lancedb_index_service

            index_svc = get_lancedb_index_service()
            duplicates = await index_svc.find_duplicates() if hasattr(index_svc, "find_duplicates") else []

            if duplicates:
                return HealthMetric(
                    name="index_consistency",
                    status="warning",
                    value=f"{len(duplicates)} duplicates",
                    threshold="No duplicate indices",
                    message=f"Duplicate files found: {', '.join(str(d) for d in duplicates[:3])}",
                )

            return HealthMetric(
                name="index_consistency",
                status="healthy",
                value="consistent",
                threshold="No duplicate indices",
            )
        except Exception:
            return HealthMetric(
                name="index_consistency",
                status="warning",
                value="unavailable",
                threshold="No duplicate indices",
                message="LanceDB index service not available",
            )

    # ───────────────────────────────────────────────────────────────────────
    # Metric 4: Reranker status
    # [Source: Story 7.4 Task 3.5]
    # ───────────────────────────────────────────────────────────────────────

    async def _check_reranker_status(self) -> HealthMetric:
        """Check if reranker is active (not pass-through)."""
        try:
            from app.services.rag_service import get_rag_service

            rag = get_rag_service()
            reranker_active = getattr(rag, "_reranker_active", None)

            if reranker_active is None:
                return HealthMetric(
                    name="reranker_status",
                    status="warning",
                    value="no data",
                    threshold="Reranker reorders results",
                    message="No reranker execution data yet",
                )

            status = "healthy" if reranker_active else "critical"
            return HealthMetric(
                name="reranker_status",
                status=status,
                value="active" if reranker_active else "pass-through",
                threshold="Reranker reorders results",
                message=None if reranker_active else "Reranker is not reordering (pass-through)",
            )
        except Exception:
            return HealthMetric(
                name="reranker_status",
                status="warning",
                value="unavailable",
                threshold="Reranker reorders results",
                message="RAG service not available for reranker check",
            )

    # ───────────────────────────────────────────────────────────────────────
    # Metric 5: CRAG trigger rate
    # [Source: Story 7.4 Task 3.6]
    # ───────────────────────────────────────────────────────────────────────

    async def _check_crag_trigger_rate(self) -> HealthMetric:
        """Check CRAG (Corrective RAG) trigger rate from logs.

        Healthy range: 15-30%. Below 10% or above 50% is concerning.
        """
        try:
            from app.services.rag_service import get_rag_service

            rag = get_rag_service()
            crag_stats = getattr(rag, "_crag_stats", None)

            if crag_stats is None or crag_stats.get("total", 0) == 0:
                return HealthMetric(
                    name="crag_trigger_rate",
                    status="warning",
                    value="no data",
                    threshold="15-30%",
                    message="No CRAG execution data yet",
                )

            rate = crag_stats["triggered"] / crag_stats["total"]
            if 0.15 <= rate <= 0.30:
                status = "healthy"
                msg = None
            elif 0.10 <= rate <= 0.50:
                status = "warning"
                msg = f"CRAG rate {rate:.1%} outside optimal range 15-30%"
            else:
                status = "critical"
                msg = f"CRAG rate {rate:.1%} far outside healthy range 15-30%"

            return HealthMetric(
                name="crag_trigger_rate",
                status=status,
                value=f"{rate:.1%}",
                threshold="15-30%",
                message=msg,
            )
        except Exception:
            return HealthMetric(
                name="crag_trigger_rate",
                status="warning",
                value="unavailable",
                threshold="15-30%",
                message="CRAG stats not available",
            )

    # ───────────────────────────────────────────────────────────────────────
    # Metric 6: Faithfulness average score
    # [Source: Story 7.4 Task 3.7]
    # ───────────────────────────────────────────────────────────────────────

    async def _check_faithfulness_score(self) -> HealthMetric:
        """Check average faithfulness score from Story 7.1 check logs."""
        try:
            from app.middleware.llm_call_logger import get_llm_call_logger

            llm_logger = get_llm_call_logger()
            faith_stats = getattr(llm_logger, "_faithfulness_stats", None)

            if faith_stats is None or faith_stats.get("count", 0) == 0:
                return HealthMetric(
                    name="faithfulness_score",
                    status="warning",
                    value="no data",
                    threshold=">= 0.85",
                    message="No faithfulness check data yet",
                )

            avg = faith_stats["total_score"] / faith_stats["count"]
            status = "healthy" if avg >= 0.85 else ("warning" if avg >= 0.70 else "critical")

            return HealthMetric(
                name="faithfulness_score",
                status=status,
                value=f"{avg:.3f}",
                threshold=">= 0.85",
                message=None if avg >= 0.85 else f"Average faithfulness {avg:.3f} below 0.85",
            )
        except Exception:
            return HealthMetric(
                name="faithfulness_score",
                status="warning",
                value="unavailable",
                threshold=">= 0.85",
                message="Faithfulness stats not available",
            )

    # ───────────────────────────────────────────────────────────────────────
    # Metric 7: Difficulty match rate
    # [Source: Story 7.4 Task 3.8]
    # ───────────────────────────────────────────────────────────────────────

    async def _check_difficulty_match_rate(self) -> HealthMetric:
        """Check difficulty matching rate from DifficultyMatcher window."""
        try:
            from app.services.difficulty_matcher import get_difficulty_matcher

            matcher = get_difficulty_matcher()
            stats = matcher.get_stats()

            if stats.total_in_window == 0:
                return HealthMetric(
                    name="difficulty_match_rate",
                    status="warning",
                    value="no data",
                    threshold=">= 70%",
                    message="No difficulty evaluation data yet",
                )

            rate = stats.match_rate
            status = "healthy" if rate >= 0.70 else ("warning" if rate >= 0.50 else "critical")

            return HealthMetric(
                name="difficulty_match_rate",
                status=status,
                value=f"{rate:.1%}",
                threshold=">= 70%",
                message=None if rate >= 0.70 else f"Match rate {rate:.1%} below 70%",
            )
        except Exception:
            return HealthMetric(
                name="difficulty_match_rate",
                status="warning",
                value="unavailable",
                threshold=">= 70%",
                message="Difficulty matcher not available",
            )

    # ───────────────────────────────────────────────────────────────────────
    # Error summary
    # ───────────────────────────────────────────────────────────────────────

    async def _get_error_summary(self) -> ErrorAggregation:
        """Get error aggregation from ErrorAggregator service."""
        try:
            from app.services.error_aggregator import get_error_aggregator

            aggregator = get_error_aggregator()
            return await aggregator.get_aggregation()
        except Exception as e:
            logger.warning(f"[Story 7.4] Failed to get error aggregation: {e}")
            return ErrorAggregation()


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[PipelineHealthMonitor] = None


def get_pipeline_health_monitor() -> PipelineHealthMonitor:
    """Get or create the singleton PipelineHealthMonitor."""
    global _instance
    if _instance is None:
        _instance = PipelineHealthMonitor()
    return _instance
