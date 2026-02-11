# Canvas Learning System - Story 30.6 Backend Tests
# Story 30.6: Color Change Event Processing
"""
Unit tests for record_batch_learning_events() with color_changed
and color_removed event types.

Coverage:
- AC-30.6.1: Single color_changed event processed
- AC-30.6.2: Metadata preserved (old_color, new_color, level)
- AC-30.6.3: Missing field -> graceful partial failure
- AC-30.6.4: Duplicate events -> idempotent
- AC-30.6.5: Mixed batch (color_changed + color_removed)

[Source: docs/stories/30.6.story.md]
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.memory_service import MemoryService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_neo4j(*, mode="JSON_FALLBACK", initialized=True):
    """Create a mock Neo4jClient for unit testing."""
    mock = MagicMock()
    mock.initialize = AsyncMock()
    mock.cleanup = AsyncMock()
    mock.stats = {
        "enabled": mode == "NEO4J",
        "initialized": initialized,
        "mode": mode,
        "health_status": True,
        "connected": False,
        "node_count": 0,
    }
    mock.record_episode = AsyncMock()
    return mock


def _make_mock_learning_memory():
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


@pytest.fixture
def memory_service():
    neo4j = _make_mock_neo4j()
    lm = _make_mock_learning_memory()
    svc = MemoryService(neo4j_client=neo4j, learning_memory_client=lm)
    svc._initialized = True
    svc._episodes_recovered = True
    return svc


def _color_event(*, event_type="color_changed", canvas_path="test/math.canvas",
                 node_id=None, metadata=None, timestamp=None):
    """Build a single color event dict."""
    return {
        "event_type": event_type,
        "timestamp": timestamp or datetime.now().isoformat(),
        "canvas_path": canvas_path,
        "node_id": node_id or f"node-{uuid.uuid4().hex[:8]}",
        "metadata": metadata or {},
    }


# ===========================================================================
# Tests
# ===========================================================================


class TestStory306ColorChangeEvents:
    """Story 30.6: Color change event processing via batch API."""

    @pytest.mark.asyncio
    async def test_single_color_changed_event_processed(self, memory_service):
        """
        AC-30.6.1: 1 color_changed event -> processed=1, failed=0.
        """
        events = [_color_event(event_type="color_changed")]

        result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 1
        assert result["failed"] == 0
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_color_changed_metadata_preserved(self, memory_service):
        """
        AC-30.6.2: old_color, new_color, level fields in metadata
        are preserved in the stored episode.
        """
        meta = {"old_color": "0", "new_color": "6", "level": "beginner"}
        events = [_color_event(
            event_type="color_changed",
            node_id="node-meta-test",
            metadata=meta,
        )]

        await memory_service.record_batch_learning_events(events)

        # Find the stored episode
        stored = [
            ep for ep in memory_service._episodes
            if ep.get("node_id") == "node-meta-test"
        ]
        assert len(stored) == 1
        assert stored[0]["metadata"]["old_color"] == "0"
        assert stored[0]["metadata"]["new_color"] == "6"
        assert stored[0]["metadata"]["level"] == "beginner"

    @pytest.mark.asyncio
    async def test_multiple_color_changes_same_node_idempotent(self, memory_service):
        """
        AC-30.6.4: Duplicate events (same canvas, node, type, timestamp)
        are deduplicated — processed count stays at 1 on second call.
        """
        ts = datetime.now().isoformat()
        event = _color_event(
            event_type="color_changed",
            node_id="node-dup",
            canvas_path="dup.canvas",
            timestamp=ts,
        )

        r1 = await memory_service.record_batch_learning_events([event])
        assert r1["processed"] == 1

        # Same event again — should be deduplicated (episode already exists)
        r2 = await memory_service.record_batch_learning_events([event])
        assert r2["processed"] == 1  # still counted as processed

        # But only 1 episode stored
        matching = [
            ep for ep in memory_service._episodes
            if ep.get("node_id") == "node-dup"
        ]
        assert len(matching) == 1

    @pytest.mark.asyncio
    async def test_color_removed_event_processed(self, memory_service):
        """
        AC-30.6.2: color_removed event with old_color only -> processed.
        """
        meta = {"old_color": "6"}
        events = [_color_event(
            event_type="color_removed",
            node_id="node-removed",
            metadata=meta,
        )]

        result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 1
        assert result["success"] is True

        stored = [
            ep for ep in memory_service._episodes
            if ep.get("node_id") == "node-removed"
        ]
        assert len(stored) == 1
        assert stored[0]["metadata"]["old_color"] == "6"

    @pytest.mark.asyncio
    async def test_mixed_color_batch(self, memory_service):
        """
        AC-30.6.5: 3 color_changed + 2 color_removed -> all 5 succeed.
        """
        events = [
            _color_event(event_type="color_changed", node_id=f"cc-{i}")
            for i in range(3)
        ] + [
            _color_event(event_type="color_removed", node_id=f"cr-{i}")
            for i in range(2)
        ]

        result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 5
        assert result["failed"] == 0
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_color_event_missing_field_fails_gracefully(self, memory_service):
        """
        AC-30.6.3: Event missing required 'canvas_path' -> partial failure.
        """
        events = [
            _color_event(event_type="color_changed", node_id="good-node"),
            {
                "event_type": "color_changed",
                "timestamp": datetime.now().isoformat(),
                # canvas_path intentionally missing
                "node_id": "bad-node",
            },
        ]

        result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 1
        assert result["failed"] == 1
        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["index"] == 1
        assert "canvas_path" in result["errors"][0]["error"]
