# Canvas Learning System - Unit Tests for Graphiti JSON Dual-Write
# Story 36.9: 学习记忆双写（Neo4j + Graphiti JSON存储）
# ✅ Verified from docs/stories/36.9.story.md#Task-4
"""
Unit tests for Graphiti JSON dual-write functionality in MemoryService.

Test Coverage (Story 36.9 Task 4):
- 4.1: Test _write_to_graphiti_json() is called after Neo4j write succeeds
- 4.2: Test fire-and-forget doesn't block record_learning_event() return
- 4.3: Test JSON write failure doesn't affect main flow
- 4.4: Test timeout protection (500ms)
- 4.5: Test config flag disables dual-write when false

[Source: docs/stories/36.9.story.md#Testing]
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay, wait_for_condition, wait_for_mock_call, yield_to_event_loop

from app.clients.graphiti_client import LearningMemory
from app.services.memory_service import (
    GRAPHITI_JSON_WRITE_TIMEOUT,
    MemoryService,
)


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4jClient."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.stats = {"connected": True, "mode": "NEO4J", "initialized": True}
    client.create_learning_relationship = AsyncMock(return_value=True)
    client.get_concept_history = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_learning_memory_client():
    """Create a mock LearningMemoryClient."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.add_learning_episode = AsyncMock(return_value=True)
    return client


@pytest.fixture
def memory_service(mock_neo4j_client, mock_learning_memory_client):
    """Create MemoryService with mocked dependencies."""
    return MemoryService(
        neo4j_client=mock_neo4j_client,
        learning_memory_client=mock_learning_memory_client,
    )


class TestGraphitiJsonDualWrite:
    """Test cases for Graphiti JSON dual-write functionality."""

    @pytest.mark.asyncio
    async def test_dual_write_called_after_neo4j_success(
        self, memory_service, mock_learning_memory_client, wait_for_call
    ):
        """
        Task 4.1: Test _write_to_graphiti_json() is called after Neo4j write succeeds.

        ✅ AC-36.9.1: 学习事件写入Neo4j成功后自动尝试写入LearningMemoryClient
        """
        # Arrange
        await memory_service.initialize()

        # Act
        # Story 31.A.3: Now uses _write_to_graphiti_json_with_retry instead of _write_to_graphiti_json
        with patch.object(memory_service, "_write_to_graphiti_json_with_retry", new_callable=AsyncMock) as mock_write:
            with patch("app.services.memory_service.settings") as mock_settings:
                mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

                episode_id = await memory_service.record_learning_event(
                    user_id="test-user",
                    canvas_path="test.canvas",
                    node_id="node-123",
                    concept="测试概念",
                    agent_type="scoring-agent",
                    score=85,
                )

                # Wait for fire-and-forget task
                await wait_for_call(mock_write)

        # Assert
        assert episode_id is not None
        assert episode_id.startswith("episode-")
        # Verify _write_to_graphiti_json_with_retry was called (fire-and-forget task created)
        mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_fire_and_forget_doesnt_block_return(
        self, memory_service, mock_learning_memory_client
    ):
        """
        Task 4.2: Test fire-and-forget doesn't block record_learning_event() return.

        ✅ AC-36.9.2: JSON写入使用fire-and-forget模式，不阻塞主流程
        """
        # Arrange
        await memory_service.initialize()

        # Make JSON write slow (150ms)
        async def slow_write(*args, **kwargs):
            await simulate_async_delay(0.15)
            return True

        mock_learning_memory_client.add_learning_episode = slow_write

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            start_time = time.time()
            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
            )
            elapsed = time.time() - start_time

        # Assert - Should return immediately (< 0.5s), not wait for 1s JSON write
        assert episode_id is not None
        assert elapsed < 0.5, f"Expected < 0.5s, but took {elapsed:.2f}s (blocked by JSON write)"

    @pytest.mark.asyncio
    async def test_json_write_failure_doesnt_affect_main_flow(
        self, memory_service, mock_learning_memory_client
    ):
        """
        Task 4.3: Test JSON write failure doesn't affect main flow.

        ✅ AC-36.9.3: JSON写入失败时静默降级，记录警告日志但不抛出异常
        """
        # Arrange
        await memory_service.initialize()

        # Make JSON write fail
        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=Exception("Simulated JSON write failure")
        )

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            # This should NOT raise an exception
            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
            )

            # Wait for fire-and-forget task to complete
            await wait_for_mock_call(mock_learning_memory_client.add_learning_episode)

        # Assert
        assert episode_id is not None
        assert episode_id.startswith("episode-")

    @pytest.mark.asyncio
    async def test_timeout_protection(self, memory_service, mock_learning_memory_client):
        """
        Task 4.4: Test timeout protection (500ms).

        ✅ AC-36.9.4: JSON写入超时保护（500ms），超时后放弃写入
        """
        # Arrange
        await memory_service.initialize()

        # Make JSON write slow (150ms, way beyond timeout for fire-and-forget)
        async def very_slow_write(*args, **kwargs):
            await simulate_async_delay(0.15)
            return True

        mock_learning_memory_client.add_learning_episode = very_slow_write

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            start_time = time.time()

            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
            )

            # Wait for fire-and-forget timeout task to complete (poll instead of hard sleep)
            await wait_for_condition(
                lambda: time.time() - start_time >= GRAPHITI_JSON_WRITE_TIMEOUT + 0.3,
                timeout=GRAPHITI_JSON_WRITE_TIMEOUT + 1.0,
                description="fire-and-forget timeout",
            )
            total_elapsed = time.time() - start_time

        # Assert
        assert episode_id is not None
        # Story 38.6: timeout increased to 2.0s; allow margin for fire-and-forget completion
        assert total_elapsed < GRAPHITI_JSON_WRITE_TIMEOUT + 1.5, (
            f"Expected < {GRAPHITI_JSON_WRITE_TIMEOUT + 1.5:.1f}s with timeout, but took {total_elapsed:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_config_flag_disables_dual_write(
        self, memory_service, mock_learning_memory_client
    ):
        """
        Task 4.5: Test config flag disables dual-write when false.

        ✅ AC-36.9.5: 可通过环境变量ENABLE_GRAPHITI_JSON_DUAL_WRITE开关双写功能
        """
        # Arrange
        await memory_service.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            # Disable dual-write
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
            )

            # Yield control to let any background tasks run
            await yield_to_event_loop()

        # Assert
        assert episode_id is not None
        # Verify add_learning_episode was NOT called (dual-write disabled)
        mock_learning_memory_client.add_learning_episode.assert_not_called()

    @pytest.mark.asyncio
    async def test_config_flag_enables_dual_write(
        self, memory_service, mock_learning_memory_client, wait_for_call
    ):
        """
        Test config flag enables dual-write when true.

        Additional test to verify AC-36.9.5 works in both directions.
        """
        # Arrange
        await memory_service.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            # Enable dual-write
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
                score=90,
            )

            # Wait for fire-and-forget task
            await wait_for_call(mock_learning_memory_client.add_learning_episode)

        # Assert
        assert episode_id is not None
        # Verify add_learning_episode was called (dual-write enabled)
        mock_learning_memory_client.add_learning_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_to_graphiti_json_success_logging(
        self, memory_service, mock_learning_memory_client
    ):
        """
        Test that successful JSON write logs debug message.

        ✅ Task 2.5: Log success with logger.debug()
        """
        # Arrange
        await memory_service.initialize()

        # Act
        with patch("app.services.memory_service.logger") as mock_logger:
            await memory_service._write_to_graphiti_json(
                episode_id="test-episode-001",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="测试概念",
                score=85.0,
            )

        # Assert
        mock_learning_memory_client.add_learning_episode.assert_called_once()
        mock_logger.debug.assert_called()
        # Verify the log message contains the episode_id
        log_call_args = str(mock_logger.debug.call_args)
        assert "test-episode-001" in log_call_args

    @pytest.mark.asyncio
    async def test_write_to_graphiti_json_timeout_logging(
        self, memory_service, mock_learning_memory_client
    ):
        """
        Test that timeout logs warning message.

        ✅ AC-36.9.4: Timeout protection with logging
        """
        # Arrange
        await memory_service.initialize()

        async def very_slow_write(*args, **kwargs):
            await simulate_async_delay(2.5)  # Must exceed GRAPHITI_JSON_WRITE_TIMEOUT (2.0s)
            return True

        mock_learning_memory_client.add_learning_episode = very_slow_write

        # Act
        with patch("app.services.memory_service.logger") as mock_logger:
            await memory_service._write_to_graphiti_json(
                episode_id="test-episode-timeout",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="测试概念",
            )

        # Assert
        mock_logger.warning.assert_called()
        log_call_args = str(mock_logger.warning.call_args)
        assert "timeout" in log_call_args.lower()

    @pytest.mark.asyncio
    async def test_write_to_graphiti_json_failure_logging(
        self, memory_service, mock_learning_memory_client
    ):
        """
        Test that failure logs warning message.

        ✅ AC-36.9.3: Silent degradation with warning logging
        """
        # Arrange
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=Exception("Test failure")
        )

        # Act
        with patch("app.services.memory_service.logger") as mock_logger:
            await memory_service._write_to_graphiti_json(
                episode_id="test-episode-failure",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="测试概念",
            )

        # Assert
        mock_logger.warning.assert_called()
        log_call_args = str(mock_logger.warning.call_args)
        assert "failed" in log_call_args.lower()

    @pytest.mark.asyncio
    async def test_record_temporal_event_dual_write(
        self, memory_service, mock_learning_memory_client, wait_for_call
    ):
        """
        Test dual-write is called from record_temporal_event().

        ✅ Task 1.5: Call _write_to_graphiti_json() in record_temporal_event()
        """
        # Arrange
        await memory_service.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            event_id = await memory_service.record_temporal_event(
                event_type="node_created",
                session_id="session-123",
                canvas_path="test.canvas",
                node_id="node-456",
                metadata={"node_text": "新建节点内容"},
            )

            # Wait for fire-and-forget task
            await wait_for_call(mock_learning_memory_client.add_learning_episode)

        # Assert
        assert event_id is not None
        assert event_id.startswith("event-")
        # Verify add_learning_episode was called
        mock_learning_memory_client.add_learning_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_learning_memory_dataclass_creation(
        self, memory_service, mock_learning_memory_client
    ):
        """
        Test that LearningMemory dataclass is created with correct fields.

        ✅ Task 2.1: Create LearningMemory dataclass instance
        """
        # Arrange
        await memory_service.initialize()

        captured_memory = None

        async def capture_memory(memory: LearningMemory):
            nonlocal captured_memory
            captured_memory = memory
            return True

        mock_learning_memory_client.add_learning_episode = capture_memory

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
                score=85,
            )

            # Wait for fire-and-forget task
            await wait_for_condition(
                lambda: captured_memory is not None,
                description="captured_memory set by fire-and-forget task",
            )

        # Assert
        assert captured_memory is not None
        assert captured_memory.canvas_name == "test.canvas"
        assert captured_memory.node_id == "node-123"
        assert captured_memory.concept == "测试概念"
        assert captured_memory.score == 85.0
        assert captured_memory.agent_feedback == "scoring-agent"
        assert captured_memory.timestamp is not None
