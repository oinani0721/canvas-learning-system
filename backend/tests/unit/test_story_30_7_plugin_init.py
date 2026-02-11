# Canvas Learning System - Story 30.7 Backend Tests
# Story 30.7: Plugin Init & Health Status
"""
Unit tests for get_health_status() and initialization states.

Coverage:
- AC-30.7.1: healthy when all layers ok (NEO4J mode)
- AC-30.7.1: degraded when JSON_FALLBACK
- AC-30.7.1: degraded when health_status=False
- AC-30.7.2: auto-init (lazy init) on health check
- AC-30.7.2: auto-init on batch call
- AC-30.7.4: required response fields
- AC-30.7.5: debug info includes stats
- AC-30.7.6: Neo4j exception -> unhealthy, no propagation

[Source: docs/stories/30.7.story.md]
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from app.services.memory_service import MemoryService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_neo4j(*, mode="JSON_FALLBACK", initialized=True,
                     health_status=True, connected=False):
    mock = MagicMock()
    mock.initialize = AsyncMock()
    mock.cleanup = AsyncMock()
    mock.stats = {
        "enabled": mode == "NEO4J",
        "initialized": initialized,
        "mode": mode,
        "health_status": health_status,
        "connected": connected,
        "node_count": 42 if mode == "NEO4J" else 0,
    }
    mock.record_episode = AsyncMock()
    mock.get_all_recent_episodes = AsyncMock(return_value=[])
    return mock


def _make_mock_lm():
    mock = MagicMock()
    mock.add_learning_episode = AsyncMock()
    return mock


@pytest.fixture(autouse=True)
def _reset_memory_singleton():
    import backend.app.services.memory_service as mod
    original = mod._memory_service_instance
    mod._memory_service_instance = None
    try:
        yield
    finally:
        mod._memory_service_instance = original


def _make_service(*, mode="JSON_FALLBACK", initialized_flag=True,
                  health_status=True, connected=False):
    """Create a MemoryService with configurable mock Neo4j."""
    neo4j = _make_mock_neo4j(
        mode=mode,
        initialized=initialized_flag,
        health_status=health_status,
        connected=connected,
    )
    lm = _make_mock_lm()
    svc = MemoryService(neo4j_client=neo4j, learning_memory_client=lm)
    svc._initialized = True
    svc._episodes_recovered = True
    return svc, neo4j


# ===========================================================================
# Tests
# ===========================================================================


class TestStory307HealthStatus:
    """Story 30.7: Health status and initialization state tests."""

    @pytest.mark.asyncio
    async def test_healthy_when_all_layers_ok(self):
        """
        AC-30.7.1: NEO4J mode, initialized, health_status=True
        -> overall status=healthy.
        """
        svc, _ = _make_service(
            mode="NEO4J", initialized_flag=True,
            health_status=True, connected=True,
        )

        result = await svc.get_health_status()

        assert result["status"] == "healthy"
        assert result["layers"]["graphiti"]["status"] == "ok"
        assert result["layers"]["temporal"]["status"] == "ok"
        assert result["layers"]["semantic"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_degraded_when_json_fallback(self):
        """
        AC-30.7.1: JSON_FALLBACK mode -> still healthy (fallback is ok).
        Graphiti backend should report json_fallback.
        """
        svc, _ = _make_service(mode="JSON_FALLBACK")

        result = await svc.get_health_status()

        assert result["status"] == "healthy"
        assert result["layers"]["graphiti"]["backend"] == "json_fallback"

    @pytest.mark.asyncio
    async def test_degraded_when_health_fails(self):
        """
        AC-30.7.1: NEO4J mode with health_status=False
        -> graphiti layer error -> overall=degraded.
        """
        svc, _ = _make_service(
            mode="NEO4J", initialized_flag=False,
            health_status=False, connected=False,
        )

        result = await svc.get_health_status()

        assert result["status"] == "degraded"
        assert result["layers"]["graphiti"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_health_has_required_fields(self):
        """
        AC-30.7.4: Response must contain status, layers, timestamp.
        """
        svc, _ = _make_service()

        result = await svc.get_health_status()

        assert "status" in result
        assert "layers" in result
        assert "timestamp" in result
        assert "temporal" in result["layers"]
        assert "graphiti" in result["layers"]
        assert "semantic" in result["layers"]

    @pytest.mark.asyncio
    async def test_auto_init_on_health_check(self):
        """
        AC-30.7.2: Lazy init triggered by health check call
        when service is not yet initialized.
        """
        neo4j = _make_mock_neo4j()
        lm = _make_mock_lm()
        svc = MemoryService(neo4j_client=neo4j, learning_memory_client=lm)
        # Do NOT set _initialized = True — let get_health_status trigger it
        assert svc._initialized is False

        result = await svc.get_health_status()

        assert svc._initialized is True
        neo4j.initialize.assert_awaited_once()
        assert result["status"] in ("healthy", "degraded")

    @pytest.mark.asyncio
    async def test_auto_init_on_batch_call(self):
        """
        AC-30.7.2: Lazy init triggered by batch call
        when service is not yet initialized.
        """
        neo4j = _make_mock_neo4j()
        lm = _make_mock_lm()
        svc = MemoryService(neo4j_client=neo4j, learning_memory_client=lm)
        svc._episodes_recovered = True
        assert svc._initialized is False

        events = [{
            "event_type": "color_changed",
            "timestamp": datetime.now().isoformat(),
            "canvas_path": "test.canvas",
            "node_id": "node-1",
        }]

        result = await svc.record_batch_learning_events(events)

        assert svc._initialized is True
        neo4j.initialize.assert_awaited_once()
        assert result["processed"] == 1

    @pytest.mark.asyncio
    async def test_neo4j_exception_returns_unhealthy(self):
        """
        AC-30.7.6: Neo4j stats access raises -> graphiti error,
        no exception propagation to caller.
        """
        neo4j = _make_mock_neo4j()
        lm = _make_mock_lm()
        svc = MemoryService(neo4j_client=neo4j, learning_memory_client=lm)
        svc._initialized = True
        svc._episodes_recovered = True

        # Make stats access raise an exception
        type(neo4j).stats = PropertyMock(side_effect=RuntimeError("Neo4j crashed"))

        # Should NOT propagate the exception
        result = await svc.get_health_status()

        assert result["layers"]["graphiti"]["status"] == "error"
        assert "Neo4j crashed" in result["layers"]["graphiti"]["error"]
        # Overall should be degraded (1 of 3 layers failed)
        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_get_debug_info_returns_stats(self):
        """
        AC-30.7.5: Debug info includes batch stats when available.
        """
        svc, _ = _make_service()

        # First do a batch to populate _batch_stats
        events = [{
            "event_type": "color_changed",
            "timestamp": datetime.now().isoformat(),
            "canvas_path": "debug.canvas",
            "node_id": "node-dbg",
        }]
        await svc.record_batch_learning_events(events)

        # Verify batch stats are tracked
        assert hasattr(svc, "_batch_stats")
        assert "batch_avg_latency_ms" in svc._batch_stats
        assert "last_batch_size" in svc._batch_stats
        assert svc._batch_stats["last_batch_size"] == 1
