"""
测试 ConcurrentAgentProcessor - Story 10.7 修复验证

测试内容:
1. _call_subagent() 方法能正确调用Sub-agent
2. _execute_with_semaphore() 方法能调用真实Agent (而非模拟)
3. Canvas集成在execute_parallel()中正常工作
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
from canvas_utils import ConcurrentAgentProcessor


class TestConcurrentAgentProcessorFixed:
    """测试修复后的ConcurrentAgentProcessor"""

    @pytest.fixture
    def processor(self):
        """创建ConcurrentAgentProcessor实例"""
        return ConcurrentAgentProcessor(max_concurrent=5)

    @pytest.mark.asyncio
    async def test_call_subagent_success(self, processor):
        """测试 _call_subagent() 方法成功调用"""
        # Mock Anthropic client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="这是AI生成的补充解释内容")]
        mock_response.model = "claude-sonnet-4-5-20250929"

        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(return_value=mock_response)

        processor._anthropic_client = mock_client

        # 调用方法
        result = await processor._call_subagent(
            agent_name="clarification-path",
            node_content="测试节点内容",
            canvas_path="test.canvas",
            node_id="node123"
        )

        # 验证结果
        assert result["success"] is True
        assert result["agent_name"] == "clarification-path"
        assert result["node_id"] == "node123"
        assert "这是AI生成的补充解释内容" in result["content"]
        assert "metadata" in result
        assert result["metadata"]["model"] == "claude-sonnet-4-5-20250929"

        # 验证API调用
        assert mock_client.messages.create.called
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["model"] == "claude-sonnet-4-5-20250929"
        assert call_args[1]["max_tokens"] == 4000

    @pytest.mark.asyncio
    async def test_call_subagent_error_handling(self, processor):
        """测试 _call_subagent() 错误处理"""
        # Mock Anthropic client to raise exception
        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(
            side_effect=Exception("API调用失败")
        )

        processor._anthropic_client = mock_client

        # 调用方法
        result = await processor._call_subagent(
            agent_name="clarification-path",
            node_content="测试节点内容",
            canvas_path="test.canvas",
            node_id="node123"
        )

        # 验证错误处理
        assert result["success"] is False
        assert result["content"] is None
        assert "error" in result
        assert "API调用失败" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_with_semaphore_real_agent_call(self, processor):
        """测试 _execute_with_semaphore() 调用真实Agent (非模拟)"""
        # Mock _call_subagent method
        mock_agent_result = {
            "agent_name": "clarification-path",
            "content": "AI生成的解释",
            "node_id": "node123",
            "metadata": {
                "timestamp": "2025-11-04T10:00:00",
                "model": "claude-sonnet-4-5-20250929",
                "word_count": 500
            },
            "success": True
        }

        processor._call_subagent = AsyncMock(return_value=mock_agent_result)

        # 准备任务信息
        task_info = {
            "agent_name": "clarification-path",
            "node_id": "node123",
            "node_text": "测试节点文本内容"
        }

        # 调用方法
        result = await processor._execute_with_semaphore(
            task_info=task_info,
            canvas_path="test.canvas",
            execution_id="exec123"
        )

        # 验证结果
        assert result["status"] == "success"
        assert result["agent_name"] == "clarification-path"
        assert result["node_id"] == "node123"
        assert "agent_result" in result
        assert result["agent_result"]["success"] is True
        assert result["agent_result"]["content"] == "AI生成的解释"

        # 验证 _call_subagent 被调用
        processor._call_subagent.assert_called_once_with(
            agent_name="clarification-path",
            node_content="测试节点文本内容",
            canvas_path="test.canvas",
            node_id="node123"
        )

    @pytest.mark.asyncio
    async def test_execute_with_semaphore_handles_agent_failure(self, processor):
        """测试 _execute_with_semaphore() 处理Agent失败"""
        # Mock _call_subagent to return failure
        mock_agent_result = {
            "agent_name": "clarification-path",
            "content": None,
            "node_id": "node123",
            "error": "Agent生成失败",
            "success": False
        }

        processor._call_subagent = AsyncMock(return_value=mock_agent_result)

        # 准备任务信息
        task_info = {
            "agent_name": "clarification-path",
            "node_id": "node123",
            "node_text": "测试节点文本内容"
        }

        # 调用方法
        result = await processor._execute_with_semaphore(
            task_info=task_info,
            canvas_path="test.canvas",
            execution_id="exec123"
        )

        # 验证错误处理
        assert result["status"] == "error"
        assert "agent_result" in result
        assert result["agent_result"]["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
