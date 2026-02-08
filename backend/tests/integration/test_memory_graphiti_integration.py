# Canvas Learning System - Integration Tests for Graphiti JSON Dual-Write
# Story 36.9: 学习记忆双写（Neo4j + Graphiti JSON存储）
# ✅ Verified from docs/stories/36.9.story.md#Task-5
"""
Integration tests for Graphiti JSON dual-write functionality.

Test Coverage (Story 36.9 Task 5):
- 5.1: Test full flow: Agent → memory write → Neo4j + Graphiti JSON dual-write
- 5.2: Test LearningMemoryClient unavailable scenario (graceful degradation)
- 5.3: Verify JSON episode format matches LearningMemory schema

[Source: docs/stories/36.9.story.md#Testing]
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.clients.graphiti_client import (
    LearningMemory,
    LearningMemoryClient,
)
from app.services.memory_service import MemoryService
from tests.conftest import wait_for_condition, yield_to_event_loop


@pytest.fixture
def temp_storage_path():
    """Create a temporary storage path for LearningMemoryClient."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_learning_memories.json"
        yield storage_path


@pytest.fixture
def real_learning_memory_client(temp_storage_path):
    """Create a real LearningMemoryClient with temporary storage."""
    return LearningMemoryClient(storage_path=temp_storage_path)


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4jClient for integration testing."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.stats = {"connected": True, "mode": "NEO4J", "initialized": True}
    client.create_learning_relationship = AsyncMock(return_value=True)
    client.get_concept_history = AsyncMock(return_value=[])
    client.record_episode = AsyncMock(return_value=True)
    client.create_canvas_node_relationship = AsyncMock(return_value=True)
    return client


@pytest.fixture
def memory_service_with_real_json(mock_neo4j_client, real_learning_memory_client):
    """Create MemoryService with real LearningMemoryClient."""
    return MemoryService(
        neo4j_client=mock_neo4j_client,
        learning_memory_client=real_learning_memory_client,
    )


class TestMemoryGraphitiIntegration:
    """Integration tests for Graphiti JSON dual-write."""

    @pytest.mark.asyncio
    async def test_full_flow_agent_to_dual_write(
        self,
        memory_service_with_real_json,
        real_learning_memory_client,
        temp_storage_path,
    ):
        """
        Task 5.1: Test full flow: Agent → memory write → Neo4j + Graphiti JSON dual-write.

        This test simulates the complete flow from an Agent completing analysis
        to the memory being written to both Neo4j and Graphiti JSON storage.
        """
        # Arrange
        await memory_service_with_real_json.initialize()
        await real_learning_memory_client.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            # Simulate Agent completing scoring analysis
            episode_id = await memory_service_with_real_json.record_learning_event(
                user_id="test-user-001",
                canvas_path="数学/线性代数.canvas",
                node_id="node-matrix-001",
                concept="矩阵乘法",
                agent_type="scoring-agent",
                score=85,
                duration_seconds=120,
            )

            # Wait for fire-and-forget task to complete
            await wait_for_condition(
                lambda: (
                    temp_storage_path.exists()
                    and len(json.loads(temp_storage_path.read_text(encoding="utf-8")).get("memories", [])) >= 1
                ),
                timeout=3.0,
                description="JSON file written with at least 1 learning memory",
            )

        # Assert
        assert episode_id is not None
        assert episode_id.startswith("episode-")

        # Verify JSON file was created and contains the memory
        assert temp_storage_path.exists()
        with open(temp_storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data.get("memories", [])) == 1
        memory = data["memories"][0]
        assert memory["canvas_name"] == "数学/线性代数.canvas"
        assert memory["node_id"] == "node-matrix-001"
        assert memory["concept"] == "矩阵乘法"
        assert memory["score"] == 85.0

    @pytest.mark.asyncio
    async def test_learning_memory_client_unavailable_graceful_degradation(
        self, mock_neo4j_client, wait_for_call
    ):
        """
        Task 5.2: Test LearningMemoryClient unavailable scenario (graceful degradation).

        When LearningMemoryClient fails, the main flow should continue without errors.
        """
        # Arrange
        failing_client = AsyncMock()
        failing_client.initialize = AsyncMock(return_value=False)
        failing_client.add_learning_episode = AsyncMock(
            side_effect=Exception("Storage unavailable")
        )

        service = MemoryService(
            neo4j_client=mock_neo4j_client,
            learning_memory_client=failing_client,
        )
        await service.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            # This should NOT raise an exception despite JSON client failing
            episode_id = await service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="basic-decomposition",
            )

            # Wait for fire-and-forget task
            await wait_for_call(failing_client.add_learning_episode)

        # Assert - Main flow should complete successfully
        assert episode_id is not None
        assert episode_id.startswith("episode-")
        # Neo4j should have been called
        mock_neo4j_client.create_learning_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_json_episode_format_matches_learning_memory_schema(
        self,
        memory_service_with_real_json,
        real_learning_memory_client,
        temp_storage_path,
    ):
        """
        Task 5.3: Verify JSON episode format matches LearningMemory schema.

        The stored JSON should contain all fields defined in LearningMemory dataclass.
        """
        # Arrange
        await memory_service_with_real_json.initialize()
        await real_learning_memory_client.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            await memory_service_with_real_json.record_learning_event(
                user_id="test-user",
                canvas_path="物理/力学.canvas",
                node_id="node-newton-001",
                concept="牛顿第三定律",
                agent_type="oral-explanation",
                score=92,
            )

            await wait_for_condition(
                lambda: (
                    temp_storage_path.exists()
                    and len(json.loads(temp_storage_path.read_text(encoding="utf-8")).get("memories", [])) >= 1
                ),
                timeout=3.0,
                description="JSON file written with at least 1 learning memory",
            )

        # Assert - Verify JSON schema compliance
        with open(temp_storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        memory = data["memories"][0]

        # Required fields per LearningMemory schema
        assert "canvas_name" in memory
        assert "node_id" in memory
        assert "concept" in memory

        # Optional fields per LearningMemory schema
        assert "user_understanding" in memory or memory.get("user_understanding") is None
        assert "score" in memory
        assert "agent_feedback" in memory
        assert "timestamp" in memory

        # Verify data types
        assert isinstance(memory["canvas_name"], str)
        assert isinstance(memory["node_id"], str)
        assert isinstance(memory["concept"], str)
        assert isinstance(memory["score"], (int, float))
        assert isinstance(memory["timestamp"], str)

    @pytest.mark.asyncio
    async def test_multiple_episodes_stored_correctly(
        self,
        memory_service_with_real_json,
        real_learning_memory_client,
        temp_storage_path,
    ):
        """
        Test that multiple learning episodes are stored correctly in sequence.
        """
        # Arrange
        await memory_service_with_real_json.initialize()
        await real_learning_memory_client.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            # Record multiple episodes
            episodes = []
            for i in range(3):
                episode_id = await memory_service_with_real_json.record_learning_event(
                    user_id="test-user",
                    canvas_path=f"test-{i}.canvas",
                    node_id=f"node-{i}",
                    concept=f"概念{i}",
                    agent_type="scoring-agent",
                    score=70 + i * 10,
                )
                episodes.append(episode_id)
                # Yield control between episodes
                await yield_to_event_loop()

            # Wait for all fire-and-forget tasks to write 3 memories
            await wait_for_condition(
                lambda: (
                    temp_storage_path.exists()
                    and len(json.loads(temp_storage_path.read_text(encoding="utf-8")).get("memories", [])) >= 3
                ),
                timeout=5.0,
                description="All 3 learning memories written to JSON",
            )

        # Assert
        with open(temp_storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data.get("memories", [])) == 3

        # Verify each episode
        for i, memory in enumerate(data["memories"]):
            assert memory["canvas_name"] == f"test-{i}.canvas"
            assert memory["node_id"] == f"node-{i}"
            assert memory["concept"] == f"概念{i}"
            assert memory["score"] == 70 + i * 10

    @pytest.mark.asyncio
    async def test_temporal_event_dual_write_integration(
        self,
        memory_service_with_real_json,
        real_learning_memory_client,
        temp_storage_path,
    ):
        """
        Test dual-write for temporal events (node_created, node_updated, etc.).
        """
        # Arrange
        await memory_service_with_real_json.initialize()
        await real_learning_memory_client.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            event_id = await memory_service_with_real_json.record_temporal_event(
                event_type="node_created",
                session_id="session-001",
                canvas_path="数学/集合论.canvas",
                node_id="node-set-001",
                metadata={"node_text": "集合的定义与运算"},
            )

            await wait_for_condition(
                lambda: (
                    temp_storage_path.exists()
                    and len(json.loads(temp_storage_path.read_text(encoding="utf-8")).get("memories", [])) >= 1
                ),
                timeout=3.0,
                description="JSON file written with temporal event memory",
            )

        # Assert
        assert event_id is not None
        assert event_id.startswith("event-")

        with open(temp_storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data.get("memories", [])) == 1
        memory = data["memories"][0]
        assert memory["canvas_name"] == "数学/集合论.canvas"
        assert memory["node_id"] == "node-set-001"
        assert memory["concept"] == "集合的定义与运算"

    @pytest.mark.asyncio
    async def test_concurrent_dual_writes(
        self,
        memory_service_with_real_json,
        real_learning_memory_client,
        temp_storage_path,
    ):
        """
        Test that concurrent dual-writes don't interfere with each other.
        """
        # Arrange
        await memory_service_with_real_json.initialize()
        await real_learning_memory_client.initialize()

        # Act - Fire multiple concurrent writes
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            tasks = []
            for i in range(5):
                task = memory_service_with_real_json.record_learning_event(
                    user_id=f"user-{i}",
                    canvas_path=f"concurrent-{i}.canvas",
                    node_id=f"node-{i}",
                    concept=f"并发测试概念{i}",
                    agent_type="scoring-agent",
                    score=80 + i,
                )
                tasks.append(task)

            # Execute all concurrently
            results = await asyncio.gather(*tasks)

            # Wait for all 5 fire-and-forget tasks to complete
            await wait_for_condition(
                lambda: (
                    temp_storage_path.exists()
                    and len(json.loads(temp_storage_path.read_text(encoding="utf-8")).get("memories", [])) >= 5
                ),
                timeout=5.0,
                description="All 5 concurrent learning memories written to JSON",
            )

        # Assert
        assert len(results) == 5
        assert all(r.startswith("episode-") for r in results)

        with open(temp_storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # All 5 episodes should be stored
        assert len(data.get("memories", [])) == 5

    @pytest.mark.asyncio
    async def test_chinese_content_in_dual_write(
        self,
        memory_service_with_real_json,
        real_learning_memory_client,
        temp_storage_path,
    ):
        """
        Test that Chinese content is properly stored in JSON.
        """
        # Arrange
        await memory_service_with_real_json.initialize()
        await real_learning_memory_client.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            await memory_service_with_real_json.record_learning_event(
                user_id="中文用户",
                canvas_path="数学/高等数学.canvas",
                node_id="node-极限-001",
                concept="极限的ε-δ定义",
                agent_type="clarification-path",
                score=88,
            )

            await wait_for_condition(
                lambda: (
                    temp_storage_path.exists()
                    and len(json.loads(temp_storage_path.read_text(encoding="utf-8")).get("memories", [])) >= 1
                ),
                timeout=3.0,
                description="JSON file written with Chinese content",
            )

        # Assert
        with open(temp_storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        memory = data["memories"][0]
        assert memory["canvas_name"] == "数学/高等数学.canvas"
        assert memory["concept"] == "极限的ε-δ定义"
        # Verify Chinese characters are properly preserved
        assert "极限" in memory["concept"]
        assert "ε-δ" in memory["concept"]
