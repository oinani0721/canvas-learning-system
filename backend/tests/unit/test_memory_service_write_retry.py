# Canvas Learning System - Memory Service Write Retry Tests
# Story 31.A.3: 写入可靠性增强
# AC-31.A.3.4: 单元测试覆盖
# ✅ Verified from docs/stories/31.A.3.story.md#Testing
"""
Unit tests for Graphiti JSON write retry functionality.

Story 31.A.3: 写入可靠性增强
- AC-31.A.3.1: 添加重试机制
- AC-31.A.3.4: 单元测试覆盖

Test scenarios:
- First attempt success
- Success after retry
- All retries failed (timeout)
- Exception triggers retry
- Retry success logging (info level)
- All retries failed logging (warning level)

[Source: docs/stories/31.A.3.story.md#Testing]
"""
import asyncio

import pytest
from unittest.mock import AsyncMock, patch

from app.services.memory_service import MemoryService, GRAPHITI_JSON_WRITE_TIMEOUT


# ✅ 模块级别 fixture（不在类内定义）
# [Source: backend/tests/unit/test_graphiti_json_dual_write.py:30-56]

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


class TestWriteToGraphitiJsonWithRetry:
    """Tests for _write_to_graphiti_json_with_retry method."""

    @pytest.mark.asyncio
    async def test_write_succeeds_first_attempt(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试首次写入成功"""
        await memory_service.initialize()

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-episode-1",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="测试概念",
        )

        assert result is True
        assert mock_learning_memory_client.add_learning_episode.call_count == 1

    @pytest.mark.asyncio
    async def test_write_succeeds_after_one_retry(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试第一次超时后重试成功"""
        await memory_service.initialize()

        # 第一次超时，第二次成功
        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=[asyncio.TimeoutError(), True]
        )

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-episode-2",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="测试概念",
        )

        assert result is True
        assert mock_learning_memory_client.add_learning_episode.call_count == 2

    @pytest.mark.asyncio
    async def test_write_succeeds_after_two_retries(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试两次超时后第三次成功"""
        await memory_service.initialize()

        # 前两次超时，第三次成功
        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=[asyncio.TimeoutError(), asyncio.TimeoutError(), True]
        )

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-episode-3",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="测试概念",
            max_retries=2,
        )

        assert result is True
        assert mock_learning_memory_client.add_learning_episode.call_count == 3

    @pytest.mark.asyncio
    async def test_write_fails_after_all_retries_timeout(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试全部重试失败（超时）"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-episode-timeout",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="测试概念",
            max_retries=2,
        )

        assert result is False
        assert mock_learning_memory_client.add_learning_episode.call_count == 3

    @pytest.mark.asyncio
    async def test_exception_triggers_retry(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试异常（非超时）触发重试"""
        await memory_service.initialize()

        # 第一次异常，第二次成功
        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=[Exception("Network error"), True]
        )

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-episode-exception",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="测试概念",
        )

        assert result is True
        assert mock_learning_memory_client.add_learning_episode.call_count == 2

    @pytest.mark.asyncio
    async def test_write_fails_after_all_retries_exception(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试全部重试失败（异常）"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=Exception("Persistent error")
        )

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-episode-exception-fail",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="测试概念",
            max_retries=2,
        )

        assert result is False
        assert mock_learning_memory_client.add_learning_episode.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_success_logging(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试重试成功后记录 info 日志"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=[asyncio.TimeoutError(), True]
        )

        with patch("app.services.memory_service.logger") as mock_logger:
            result = await memory_service._write_to_graphiti_json_with_retry(
                episode_id="test-episode-log-success",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="测试概念",
            )

        assert result is True
        # Story 38.6: retry logs at warning level (was debug)
        mock_logger.warning.assert_called()
        # 验证成功日志（重试后成功应记录 info）
        mock_logger.info.assert_called()
        log_call_args = str(mock_logger.info.call_args)
        assert "test-episode-log-success" in log_call_args
        assert "2 attempts" in log_call_args

    @pytest.mark.asyncio
    async def test_all_retries_failed_warning_logging(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试全部重试失败后记录 warning 日志"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        with patch("app.services.memory_service.logger") as mock_logger:
            result = await memory_service._write_to_graphiti_json_with_retry(
                episode_id="test-episode-log-fail",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="测试概念",
                max_retries=2,
            )

        assert result is False
        # 验证失败日志使用 warning
        mock_logger.warning.assert_called()
        log_call_args = str(mock_logger.warning.call_args)
        assert "test-episode-log-fail" in log_call_args
        assert "3 attempts" in log_call_args

    @pytest.mark.asyncio
    async def test_first_success_debug_logging(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试首次成功只记录 debug 日志（不是 info）"""
        await memory_service.initialize()

        with patch("app.services.memory_service.logger") as mock_logger:
            result = await memory_service._write_to_graphiti_json_with_retry(
                episode_id="test-episode-first-success",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="测试概念",
            )

        assert result is True
        # 首次成功应记录 debug（不是 info）
        mock_logger.debug.assert_called()
        debug_call_args = str(mock_logger.debug.call_args)
        assert "test-episode-first-success" in debug_call_args
        # info 不应该被调用（首次成功不需要 info）
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_with_all_optional_params(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试所有可选参数都传递"""
        await memory_service.initialize()

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-episode-full-params",
            canvas_name="test.canvas",
            node_id="node-456",
            concept="完整参数测试",
            score=85.5,
            agent_feedback="scoring-agent",
            user_understanding="用户的理解文本",
            max_retries=1,
        )

        assert result is True
        # 验证 add_learning_episode 被调用
        mock_learning_memory_client.add_learning_episode.assert_called_once()
        # 获取传入的 LearningMemory 对象
        call_args = mock_learning_memory_client.add_learning_episode.call_args
        learning_memory = call_args[0][0]
        assert learning_memory.canvas_name == "test.canvas"
        assert learning_memory.node_id == "node-456"
        assert learning_memory.concept == "完整参数测试"
        assert learning_memory.score == 85.5
        assert learning_memory.agent_feedback == "scoring-agent"
        assert learning_memory.user_understanding == "用户的理解文本"

    @pytest.mark.asyncio
    async def test_zero_retries_single_attempt(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.4: 测试 max_retries=0 只尝试一次"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-episode-no-retry",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="测试概念",
            max_retries=0,
        )

        assert result is False
        assert mock_learning_memory_client.add_learning_episode.call_count == 1


class TestWriteRetryStrictQA:
    """QA 补充测试: 严格验证 AC-31.A.3 的边界条件和实现细节。"""

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.1 + Story 38.6: 验证指数退避延迟值 (1.0s, 2.0s)"""
        await memory_service.initialize()

        # 前两次超时，第三次成功
        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=[asyncio.TimeoutError(), asyncio.TimeoutError(), True]
        )

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await memory_service._write_to_graphiti_json_with_retry(
                episode_id="test-backoff",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="退避测试",
                max_retries=2,
            )

        assert result is True
        # 验证 sleep 被调用 2 次（2 次重试前各一次）
        assert mock_sleep.call_count == 2
        # Story 38.6: 指数退避 1.0 * 2^0 = 1.0, 1.0 * 2^1 = 2.0
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays[0] == pytest.approx(1.0)
        assert delays[1] == pytest.approx(2.0)

    @pytest.mark.asyncio
    async def test_exponential_backoff_all_failures(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.1 + Story 38.6: 验证全部失败时指数退避延迟值 (1.0s, 2.0s)"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await memory_service._write_to_graphiti_json_with_retry(
                episode_id="test-backoff-fail",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="退避测试",
                max_retries=2,
            )

        assert result is False
        # 最后一次失败后不 sleep，所以只有 2 次 sleep（重试1和重试2之前）
        assert mock_sleep.call_count == 2
        # Story 38.6: 指数退避 1.0 * 2^0 = 1.0, 1.0 * 2^1 = 2.0
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays[0] == pytest.approx(1.0)
        assert delays[1] == pytest.approx(2.0)

    @pytest.mark.asyncio
    async def test_mixed_timeout_then_exception_then_success(
        self, memory_service, mock_learning_memory_client
    ):
        """QA 补充: 混合异常类型 - Timeout后Exception后成功"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=[asyncio.TimeoutError(), Exception("Network error"), True]
        )

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-mixed",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="混合异常",
            max_retries=2,
        )

        assert result is True
        assert mock_learning_memory_client.add_learning_episode.call_count == 3

    @pytest.mark.asyncio
    async def test_exception_failure_warning_includes_error_message(
        self, memory_service, mock_learning_memory_client
    ):
        """QA 补充: Exception失败的warning日志应包含错误消息（与Timeout日志格式不同）"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=Exception("Custom DB error")
        )

        with patch("app.services.memory_service.logger") as mock_logger:
            result = await memory_service._write_to_graphiti_json_with_retry(
                episode_id="test-exc-log",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="异常日志",
                max_retries=2,
            )

        assert result is False
        mock_logger.warning.assert_called()
        log_msg = str(mock_logger.warning.call_args)
        # Exception 失败日志应包含错误消息
        assert "Custom DB error" in log_msg
        assert "test-exc-log" in log_msg
        # Exception 失败不包含 "(timeout)" 后缀
        assert "(timeout)" not in log_msg

    @pytest.mark.asyncio
    async def test_timeout_failure_warning_includes_timeout_suffix(
        self, memory_service, mock_learning_memory_client
    ):
        """QA 补充: Timeout失败的warning日志应包含'(timeout)'后缀"""
        await memory_service.initialize()

        mock_learning_memory_client.add_learning_episode = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        with patch("app.services.memory_service.logger") as mock_logger:
            result = await memory_service._write_to_graphiti_json_with_retry(
                episode_id="test-timeout-log",
                canvas_name="test.canvas",
                node_id="node-123",
                concept="超时日志",
                max_retries=0,
            )

        assert result is False
        log_msg = str(mock_logger.warning.call_args)
        assert "(timeout)" in log_msg
        assert "test-timeout-log" in log_msg

    @pytest.mark.asyncio
    async def test_record_temporal_event_uses_retry_method(
        self, memory_service, mock_learning_memory_client
    ):
        """AC-31.A.3.2: 验证 record_temporal_event 使用带重试的方法"""
        await memory_service.initialize()

        with patch.object(
            memory_service, "_write_to_graphiti_json_with_retry", new_callable=AsyncMock
        ) as mock_retry_write:
            with patch("app.services.memory_service.settings") as mock_settings:
                mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

                event_id = await memory_service.record_temporal_event(
                    event_type="node_created",
                    session_id="session-qa-test",
                    canvas_path="qa-test.canvas",
                    node_id="node-qa-1",
                    metadata={"node_text": "QA测试节点"},
                )

                await asyncio.sleep(0.1)

        assert event_id is not None
        # 验证调用的是 _write_to_graphiti_json_with_retry 而非旧方法
        mock_retry_write.assert_called_once()
        call_kwargs = mock_retry_write.call_args
        # 验证传入的参数
        assert call_kwargs[1]["canvas_name"] == "qa-test.canvas" or call_kwargs.kwargs.get("canvas_name") == "qa-test.canvas"

    @pytest.mark.asyncio
    async def test_retry_creates_new_timestamp_each_attempt(
        self, memory_service, mock_learning_memory_client
    ):
        """QA 发现: 每次重试创建新的 LearningMemory（不同 timestamp）

        这记录了一个潜在的幂等性问题：如果第一次写入在 timeout 瞬间完成（race condition），
        重试会因为不同的 timestamp 导致不同的 memory_key，从而产生重复记录。
        """
        await memory_service.initialize()

        captured_memories = []

        async def capture_and_fail(memory):
            captured_memories.append(memory)
            if len(captured_memories) < 3:
                raise asyncio.TimeoutError()
            return True

        mock_learning_memory_client.add_learning_episode = capture_and_fail

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="test-timestamp",
            canvas_name="test.canvas",
            node_id="node-123",
            concept="时间戳测试",
            max_retries=2,
        )

        assert result is True
        assert len(captured_memories) == 3
        # 每次重试的 LearningMemory 应该有相同的核心字段
        for m in captured_memories:
            assert m.canvas_name == "test.canvas"
            assert m.node_id == "node-123"
            assert m.concept == "时间戳测试"
        # 记录: 每次重试会有不同的 timestamp (潜在幂等性问题)
        timestamps = [m.timestamp for m in captured_memories]
        # timestamp 可能不同（因为 datetime.now() 在每次循环中调用）
        assert all(t is not None for t in timestamps)
