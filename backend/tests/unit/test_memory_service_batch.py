# Canvas Learning System - Story 30.9 Tests
# Task 8.6: Backend test for record_batch_learning_events concept field fallback
"""
Story 30.9 - NodeColorChangeWatcher Data Integrity: Backend Tests

Tests for record_batch_learning_events() concept field resolution:
- AC-30.9.3: concept field maps from metadata.concept
- Fallback: metadata.node_text when concept absent
- Default: "unknown" when neither present

[Source: docs/stories/30.9.story.md#Task-8.6]
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRecordBatchLearningEventsConcept:
    """Tests for concept field fallback in record_batch_learning_events."""

    @pytest.fixture
    def mock_neo4j(self):
        """Create a mock Neo4jClient."""
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True, "connected": True}
        neo4j.record_episode = AsyncMock()
        return neo4j

    @pytest.fixture
    def mock_learning_memory(self):
        """Create a mock LearningMemoryClient."""
        client = MagicMock()
        return client

    @pytest.fixture
    async def memory_service(self, mock_neo4j, mock_learning_memory):
        """Create a MemoryService with mocked dependencies."""
        from app.services.memory_service import MemoryService
        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()
        return service

    def _make_event(self, metadata: dict) -> dict:
        """Helper to create a valid batch event."""
        return {
            "event_type": "color_changed",
            "timestamp": "2026-01-20T10:00:00Z",
            "canvas_path": "Math/test.canvas",
            "node_id": "node_001",
            "metadata": metadata,
        }

    @pytest.mark.asyncio
    async def test_concept_field_used_when_present(self, memory_service, mock_neo4j):
        """AC-30.9.3: concept field from metadata is used directly."""
        event = self._make_event({
            "concept": "监督学习",
            "node_text": "监督学习的定义和分类",
        })

        result = await memory_service.record_batch_learning_events([event])

        assert result["success"] is True
        assert result["processed"] == 1

        # Verify Neo4j received concept from metadata.concept
        call_args = mock_neo4j.record_episode.call_args[0][0]
        assert call_args["concept"] == "监督学习"

    @pytest.mark.asyncio
    async def test_concept_fallback_to_node_text(self, memory_service, mock_neo4j):
        """Story 30.9: When concept absent, fallback to node_text."""
        event = self._make_event({
            "node_text": "逆否命题的定义",
            "old_color": "1",
            "new_color": "2",
        })

        result = await memory_service.record_batch_learning_events([event])

        assert result["success"] is True

        # Verify Neo4j received concept from metadata.node_text fallback
        call_args = mock_neo4j.record_episode.call_args[0][0]
        assert call_args["concept"] == "逆否命题的定义"

    @pytest.mark.asyncio
    async def test_concept_fallback_to_unknown(self, memory_service, mock_neo4j):
        """Story 30.9: When neither concept nor node_text, default to 'unknown'."""
        event = self._make_event({
            "old_color": "1",
            "new_color": "2",
        })

        result = await memory_service.record_batch_learning_events([event])

        assert result["success"] is True

        # Verify Neo4j received "unknown" as default
        call_args = mock_neo4j.record_episode.call_args[0][0]
        assert call_args["concept"] == "unknown"

    @pytest.mark.asyncio
    async def test_color_removed_event_type(self, memory_service, mock_neo4j):
        """Story 30.9: color_removed event type processed correctly."""
        event = self._make_event({
            "concept": "递归定义",
            "old_color": "1",
            "new_color": None,
        })
        event["event_type"] = "color_removed"

        result = await memory_service.record_batch_learning_events([event])

        assert result["success"] is True
        call_args = mock_neo4j.record_episode.call_args[0][0]
        assert call_args["agent_type"] == "color_removed"
        assert call_args["concept"] == "递归定义"

    @pytest.mark.asyncio
    async def test_node_removed_event_type(self, memory_service, mock_neo4j):
        """Story 30.9: node_removed event type processed correctly."""
        event = self._make_event({
            "old_color": "3",
            "new_color": None,
            "node_text": "已删除节点",
        })
        event["event_type"] = "node_removed"

        result = await memory_service.record_batch_learning_events([event])

        assert result["success"] is True
        call_args = mock_neo4j.record_episode.call_args[0][0]
        assert call_args["agent_type"] == "node_removed"
        # Fallback to node_text since no concept
        assert call_args["concept"] == "已删除节点"

    @pytest.mark.asyncio
    async def test_neo4j_disconnected_still_stores_in_memory(
        self, memory_service, mock_neo4j
    ):
        """Story 30.9: Events stored in-memory even when Neo4j disconnected."""
        mock_neo4j.stats = {"initialized": False, "connected": False}

        event = self._make_event({"concept": "测试概念"})
        result = await memory_service.record_batch_learning_events([event])

        assert result["success"] is True
        assert result["processed"] == 1
        # Neo4j.record_episode should NOT have been called
        mock_neo4j.record_episode.assert_not_called()
