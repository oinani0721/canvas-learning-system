"""
测试并行命令系统 - Canvas学习系统

测试并行命令解析、执行和集成功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-26
"""

import asyncio
import pytest
import unittest.mock as mock
from datetime import datetime
import json
import os
import sys
import tempfile
import uuid

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parallel_command_parser import (
    ParallelCommandParser, ParallelCommand, CommandType, TaskPriority,
    CommandConfig
)
from command_executor import CommandExecutor, ExecutionStatus, ProgressTracker


class TestParallelCommandParser:
    """测试ParallelCommandParser类"""

    def setup_method(self):
        """测试前准备"""
        self.config = CommandConfig()
        self.parser = ParallelCommandParser(self.config)

    def test_parse_parallel_agents_basic(self):
        """测试基础的parallel-agents命令解析"""
        command_string = "*parallel-agents clarification-path 4"
        command, errors = self.parser.parse_command(command_string)

        assert command is not None
        assert len(errors) == 0
        assert command.command_type == CommandType.PARALLEL_AGENTS
        assert command.agent_type == "clarification-path"
        assert command.node_count == 4

    def test_parse_parallel_agents_with_options(self):
        """测试带选项的parallel-agents命令解析"""
        command_string = "*parallel-agents memory-anchor --max=3 --canvas=test.canvas --dry-run"
        command, errors = self.parser.parse_command(command_string)

        assert command is not None
        assert command.command_type == CommandType.PARALLEL_AGENTS
        assert command.agent_type == "memory-anchor"
        assert command.max_instances == 3
        assert command.canvas_path == "test.canvas"
        assert command.dry_run == True

    def test_parse_parallel_nodes(self):
        """测试parallel-nodes命令解析"""
        command_string = "*parallel-nodes clarification-path --nodes=node1,node2,node3"
        command, errors = self.parser.parse_command(command_string)

        assert command is not None
        assert command.command_type == CommandType.PARALLEL_NODES
        assert command.agent_type == "clarification-path"
        assert command.target_nodes == ["node1", "node2", "node3"]

    def test_parse_parallel_color(self):
        """测试parallel-color命令解析"""
        command_string = "*parallel-color memory-anchor --color=1 --limit=5"
        command, errors = self.parser.parse_command(command_string)

        assert command is not None
        assert command.command_type == CommandType.PARALLEL_COLOR
        assert command.agent_type == "memory-anchor"
        assert command.color_filter == "1"
        assert command.node_count == 5

    def test_parse_parallel_mixed(self):
        """测试parallel-mixed命令解析"""
        command_string = "*parallel-mixed memory-anchor:3,clarification-path:4"
        command, errors = self.parser.parse_command(command_string)

        assert command is not None
        assert command.command_type == CommandType.PARALLEL_MIXED
        assert command.mixed_config == {"memory-anchor": 3, "clarification-path": 4}

    def test_validate_invalid_agent_type(self):
        """测试无效Agent类型验证"""
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_AGENTS,
            agent_type="invalid-agent"
        )
        errors = self.parser.validate_command(command)
        assert len(errors) > 0
        assert any("不支持的Agent类型" in error for error in errors)

    def test_validate_invalid_color(self):
        """测试无效颜色验证"""
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_COLOR,
            agent_type="clarification-path",
            color_filter="9"  # 无效颜色
        )
        errors = self.parser.validate_command(command)
        assert len(errors) > 0
        assert any("不支持的颜色" in error for error in errors)

    def test_validate_too_many_instances(self):
        """测试实例数超限验证"""
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_AGENTS,
            agent_type="clarification-path",
            max_instances=20  # 超过默认限制
        )
        errors = self.parser.validate_command(command)
        assert len(errors) > 0
        assert any("超过系统限制" in error for error in errors)

    def test_suggest_completion_empty(self):
        """测试空输入的补全建议"""
        suggestions = self.parser.suggest_completion("")
        assert len(suggestions) == 4  # 四种命令类型
        assert all(s.startswith("*") for s in suggestions)

    def test_suggest_completion_partial(self):
        """测试部分输入的补全建议"""
        suggestions = self.parser.suggest_completion("*parallel")
        assert len(suggestions) >= 4
        assert all("*parallel-" in s for s in suggestions)

    def test_suggest_completion_agent(self):
        """测试Agent类型补全建议"""
        suggestions = self.parser.suggest_completion("*parallel-agents ")
        assert len(suggestions) >= len(self.config.supported_agents)
        assert any("clarification-path" in s for s in suggestions)

    def test_get_command_help_all(self):
        """测试获取所有命令帮助"""
        help_text = self.parser.get_command_help()
        assert "*parallel-agents" in help_text
        assert "*parallel-nodes" in help_text
        assert "*parallel-color" in help_text
        assert "*parallel-mixed" in help_text

    def test_get_command_help_specific(self):
        """测试获取特定命令帮助"""
        help_text = self.parser.get_command_help(CommandType.PARALLEL_AGENTS)
        assert "Agent类型" in help_text
        assert "[count]" in help_text
        assert "--nodes=" in help_text


class TestProgressTracker:
    """测试ProgressTracker类"""

    def test_initialization(self):
        """测试初始化"""
        tracker = ProgressTracker(10)
        assert tracker.total_tasks == 10
        assert tracker.completed_tasks == 0
        assert tracker.failed_tasks == 0
        assert tracker.get_progress_percentage() == 0

    def test_update_progress(self):
        """测试进度更新"""
        tracker = ProgressTracker(10)
        tracker.update_progress(completed=3, failed=1)
        assert tracker.completed_tasks == 3
        assert tracker.failed_tasks == 1
        assert tracker.get_progress_percentage() == 40.0

    def test_elapsed_time(self):
        """测试已用时间"""
        import time
        tracker = ProgressTracker(5)
        time.sleep(0.1)
        assert tracker.get_elapsed_time() >= 0.1

    def test_eta_calculation(self):
        """测试剩余时间估算"""
        tracker = ProgressTracker(10)
        tracker.update_progress(completed=2)
        eta = tracker.get_eta()
        assert eta is not None
        assert eta > 0


@pytest.mark.asyncio
class TestCommandExecutor:
    """测试CommandExecutor类"""

    def setup_method(self):
        """测试前准备"""
        # Mock the dependencies
        self.mock_instance_pool = mock.AsyncMock()
        self.mock_instance_pool.max_concurrent_instances = 6

        self.executor = CommandExecutor(
            instance_pool=self.mock_instance_pool
        )

    async def test_preview_command(self):
        """测试命令预览"""
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_AGENTS,
            agent_type="clarification-path",
            node_count=5
        )

        with mock.patch('command_executor.CanvasOrchestrator') as mock_orchestrator:
            # Mock canvas data
            mock_orchestrator.return_value.get_all_nodes.return_value = [
                {"id": f"node{i}", "color": "1"} for i in range(10)
            ]

            preview = await self.executor.preview_command(command)

            assert "command_type" in preview
            assert "resource_requirements" in preview
            assert "estimated_duration" in preview
            assert preview["resource_requirements"]["total_instances"] == 5

    async def test_execute_dry_run(self):
        """测试试运行模式"""
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_AGENTS,
            agent_type="clarification-path",
            node_count=3,
            dry_run=True
        )

        with mock.patch('command_executor.CanvasOrchestrator') as mock_orchestrator:
            mock_orchestrator.return_value.get_all_nodes.return_value = [
                {"id": f"node{i}", "color": "1"} for i in range(5)
            ]

            result = await self.executor.execute_command(command)

            assert result.status == "success"
            assert result.processed_nodes == 3
            assert "dry_run" in result.metrics

    async def test_cancel_command(self):
        """测试取消命令"""
        command_id = str(uuid.uuid4())
        # 添加一个活跃命令
        self.executor.active_commands[command_id] = {
            "status": ExecutionStatus.RUNNING,
            "result": None,
            "start_time": datetime.now().timestamp()
        }

        cancelled = await self.executor.cancel_command(command_id)
        assert cancelled == True
        assert self.executor.active_commands[command_id]["status"] == ExecutionStatus.CANCELLED

    def test_get_execution_status(self):
        """测试获取执行状态"""
        command_id = str(uuid.uuid4())
        start_time = datetime.now().timestamp()

        # 添加一个活跃命令
        self.executor.active_commands[command_id] = {
            "status": ExecutionStatus.RUNNING,
            "result": None,
            "start_time": start_time
        }

        status = self.executor.get_execution_status(command_id)
        assert status is not None
        assert status["command_id"] == command_id
        assert status["status"] == ExecutionStatus.RUNNING
        assert status["start_time"] == start_time

    def test_cleanup_completed_commands(self):
        """测试清理完成的命令"""
        # 添加一些命令（包括过期的）
        old_time = datetime.now().timestamp() - 7200  # 2小时前
        self.executor.active_commands.update({
            "cmd1": {
                "status": ExecutionStatus.COMPLETED,
                "start_time": old_time
            },
            "cmd2": {
                "status": ExecutionStatus.RUNNING,
                "start_time": datetime.now().timestamp()
            }
        })

        self.executor.cleanup_completed_commands(max_age=3600)  # 1小时

        # cmd1应该被清理，cmd2应该保留
        assert "cmd1" not in self.executor.active_commands
        assert "cmd2" in self.executor.active_commands


class TestIntegration:
    """集成测试"""

    def test_parser_to_executor_flow(self):
        """测试从解析器到执行器的完整流程"""
        config = CommandConfig()
        parser = ParallelCommandParser(config)

        # 解析命令
        command_string = "*parallel-agents clarification-path 4 --dry-run"
        command, errors = parser.parse_command(command_string)

        assert command is not None
        assert len(errors) == 0

        # 验证命令对象
        assert command.agent_type == "clarification-path"
        assert command.node_count == 4
        assert command.dry_run == True

    def test_command_serialization(self):
        """测试命令序列化"""
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_MIXED,
            agent_type="mixed",
            mixed_config={"clarification-path": 3, "memory-anchor": 2},
            max_instances=5
        )

        # 转换为字典
        cmd_dict = command.to_dict()
        assert isinstance(cmd_dict, dict)
        assert cmd_dict["command_type"] == "parallel-mixed"
        assert cmd_dict["mixed_config"] == {"clarification-path": 3, "memory-anchor": 2}

        # 从字典重建（在实际使用中可能需要）
        new_command = ParallelCommand(
            command_type=CommandType(cmd_dict["command_type"]),
            agent_type=cmd_dict["agent_type"],
            mixed_config=cmd_dict["mixed_config"],
            max_instances=cmd_dict["max_instances"]
        )

        assert new_command.command_type == command.command_type
        assert new_command.mixed_config == command.mixed_config

    def test_error_handling_invalid_command(self):
        """测试无效命令的错误处理"""
        parser = ParallelCommandParser()

        # 测试空命令
        command, errors = parser.parse_command("")
        assert command is None
        assert len(errors) > 0

        # 测试无效命令类型
        command, errors = parser.parse_command("*invalid-command test")
        assert command is None
        assert len(errors) > 0

        # 测试缺少参数 - *parallel-agents 需要至少Agent类型
        command, errors = parser.parse_command("*parallel-agents")
        assert command is None  # 命令无效
        assert len(errors) > 0  # 应该有错误
        assert any("需要至少指定Agent类型" in error for error in errors)

    def test_edge_cases(self):
        """测试边界情况"""
        config = CommandConfig()
        parser = ParallelCommandParser(config)

        # 测试零实例数
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_AGENTS,
            agent_type="clarification-path",
            node_count=0
        )
        errors = parser.validate_command(command)
        assert len(errors) > 0

        # 测试空节点列表
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_NODES,
            agent_type="clarification-path",
            target_nodes=[]
        )
        errors = parser.validate_command(command)
        # 应该提示需要nodes参数

        # 测试空的混合配置
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_MIXED,
            agent_type="mixed",
            mixed_config={}
        )
        errors = parser.validate_command(command)
        assert len(errors) > 0


# 运行测试的便捷函数
def run_all_tests():
    """运行所有测试"""
    import subprocess

    # 运行pytest
    result = subprocess.run([
        "python", "-m", "pytest",
        "tests/test_parallel_commands.py",
        "-v",
        "--tb=short"
    ], capture_output=True, text=True)

    print("测试结果:")
    print(result.stdout)
    if result.stderr:
        print("错误信息:")
        print(result.stderr)

    return result.returncode == 0


if __name__ == "__main__":
    # 如果直接运行此文件，执行所有测试
    success = run_all_tests()
    sys.exit(0 if success else 1)