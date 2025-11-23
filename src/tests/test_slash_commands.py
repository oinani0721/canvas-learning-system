"""
Canvas学习系统 - 斜杠命令系统测试

测试斜杠命令系统的各种功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# 添加项目根目录到Python路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from slash_command_system import (
    SlashCommandSystem,
    CommandMetadata,
    CommandParameter,
    CommandExecutionContext,
    CommandExecutionResult,
    ArgumentParser,
    CommandRegistry,
    AutoCompletionSystem,
    get_slash_command_system,
    execute_slash_command,
    validate_slash_command
)

class TestArgumentParser:
    """测试参数解析器"""

    def test_parse_string_parameter(self):
        """测试字符串参数解析"""
        parser = ArgumentParser()
        param = CommandParameter(
            name="test",
            type="string",
            required=True
        )

        result = parser.parse_arguments(["--test", "hello"], [param])
        assert result == {"test": "hello"}

    def test_parse_integer_parameter(self):
        """测试整数参数解析"""
        parser = ArgumentParser()
        param = CommandParameter(
            name="number",
            type="integer",
            required=True
        )

        result = parser.parse_arguments(["--number", "42"], [param])
        assert result == {"number": 42}

    def test_parse_boolean_parameter(self):
        """测试布尔参数解析"""
        parser = ArgumentParser()
        param = CommandParameter(
            name="flag",
            type="boolean",
            required=True
        )

        result = parser.parse_arguments(["--flag", "true"], [param])
        assert result == {"flag": True}

        result = parser.parse_arguments(["--flag", "false"], [param])
        assert result == {"flag": False}

    def test_parse_flag_parameter(self):
        """测试标志参数解析"""
        parser = ArgumentParser()
        param = CommandParameter(
            name="verbose",
            type="flag",
            required=False
        )

        result = parser.parse_arguments(["--verbose"], [param])
        assert result == {"verbose": True}

    def test_parse_choice_parameter(self):
        """测试选择参数解析"""
        parser = ArgumentParser()
        param = CommandParameter(
            name="color",
            type="choice",
            required=True,
            choices=["red", "green", "blue"]
        )

        result = parser.parse_arguments(["--color", "red"], [param])
        assert result == {"color": "red"}

        # 测试无效选择
        with pytest.raises(Exception):
            parser.parse_arguments(["--color", "yellow"], [param])

    def test_parse_default_value(self):
        """测试默认值"""
        parser = ArgumentParser()
        param = CommandParameter(
            name="optional",
            type="string",
            required=False,
            default="default_value"
        )

        result = parser.parse_arguments([], [param])
        assert result == {"optional": "default_value"}

    def test_missing_required_parameter(self):
        """测试缺少必需参数"""
        parser = ArgumentParser()
        param = CommandParameter(
            name="required",
            type="string",
            required=True
        )

        with pytest.raises(Exception):
            parser.parse_arguments([], [param])

class TestCommandRegistry:
    """测试命令注册器"""

    def test_register_command(self):
        """测试命令注册"""
        registry = CommandRegistry()
        metadata = CommandMetadata(
            name="test",
            aliases=["t"],
            description="Test command",
            usage="/test",
            examples=["/test"],
            handler="test_handler",
            parameters=[]
        )

        def test_handler(context):
            return {"success": True}

        result = registry.register_command(metadata, test_handler)
        assert result is True
        assert "test" in registry.commands
        assert "t" in registry.alias_map

    def test_get_command_metadata(self):
        """测试获取命令元数据"""
        registry = CommandRegistry()
        metadata = CommandMetadata(
            name="test",
            aliases=["t"],
            description="Test command",
            usage="/test",
            examples=["/test"],
            handler="test_handler",
            parameters=[]
        )

        def test_handler(context):
            return {"success": True}

        registry.register_command(metadata, test_handler)

        # 通过名称获取
        result = registry.get_command_metadata("test")
        assert result is not None
        assert result.name == "test"

        # 通过别名获取
        result = registry.get_command_metadata("t")
        assert result is not None
        assert result.name == "test"

    def test_unregister_command(self):
        """测试命令注销"""
        registry = CommandRegistry()
        metadata = CommandMetadata(
            name="test",
            aliases=["t"],
            description="Test command",
            usage="/test",
            examples=["/test"],
            handler="test_handler",
            parameters=[]
        )

        def test_handler(context):
            return {"success": True}

        registry.register_command(metadata, test_handler)
        result = registry.unregister_command("test")
        assert result is True
        assert "test" not in registry.commands
        assert "t" not in registry.alias_map

class TestAutoCompletionSystem:
    """测试自动补全系统"""

    def test_get_command_suggestions(self):
        """测试命令建议"""
        registry = CommandRegistry()
        metadata = CommandMetadata(
            name="test",
            aliases=["t"],
            description="Test command",
            usage="/test",
            examples=["/test"],
            handler="test_handler",
            parameters=[]
        )

        def test_handler(context):
            return {"success": True}

        registry.register_command(metadata, test_handler)
        completion = AutoCompletionSystem(registry)

        # 测试命令补全
        suggestions = completion.get_suggestions("/te")
        assert len(suggestions) > 0
        assert any(s.command == "/test" for s in suggestions)

    def test_parameter_suggestions(self):
        """测试参数建议"""
        registry = CommandRegistry()
        metadata = CommandMetadata(
            name="test",
            aliases=["t"],
            description="Test command",
            usage="/test --param <value>",
            examples=["/test --param hello"],
            handler="test_handler",
            parameters=[
                CommandParameter(
                    name="param",
                    type="string",
                    required=False,
                    description="Test parameter"
                )
            ]
        )

        def test_handler(context):
            return {"success": True}

        registry.register_command(metadata, test_handler)
        completion = AutoCompletionSystem(registry)

        # 测试参数补全
        suggestions = completion.get_suggestions("/test --")
        assert len(suggestions) > 0
        assert any("--param" in s.command for s in suggestions)

class TestSlashCommandSystem:
    """测试斜杠命令系统"""

    @pytest.fixture
    def system(self):
        """创建测试用的斜杠命令系统"""
        system = SlashCommandSystem()

        # 注册测试命令
        test_metadata = CommandMetadata(
            name="test",
            aliases=["t"],
            description="Test command",
            usage="/test [--name <value>]",
            examples=["/test", "/test --name hello"],
            handler="test_handler",
            parameters=[
                CommandParameter(
                    name="name",
                    type="string",
                    required=False,
                    description="Test parameter"
                )
            ]
        )

        async def test_handler(context):
            return {
                "success": True,
                "parameters": context.parameters,
                "command": context.command_name
            }

        system.register_command(test_metadata, test_handler)
        return system

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, system):
        """测试执行简单命令"""
        result = await system.execute_command("/test")
        assert result.status == "success"
        assert result.output is not None
        assert result.output["success"] is True

    @pytest.mark.asyncio
    async def test_execute_command_with_parameters(self, system):
        """测试执行带参数的命令"""
        result = await system.execute_command("/test --name hello")
        assert result.status == "success"
        assert result.output["parameters"]["name"] == "hello"

    @pytest.mark.asyncio
    async def test_execute_command_with_alias(self, system):
        """测试使用别名执行命令"""
        result = await system.execute_command("/t --name world")
        assert result.status == "success"
        assert result.output["command"] in ["test", "t"]  # 应该解析为实际命令名或别名
        assert result.output["parameters"]["name"] == "world"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_command(self, system):
        """测试执行不存在的命令"""
        result = await system.execute_command("/nonexistent")
        assert result.status == "error"
        assert "command_not_found" in result.error_type

    @pytest.mark.asyncio
    async def test_execute_command_with_invalid_parameters(self, system):
        """测试执行带无效参数的命令"""
        result = await system.execute_command("/test --invalid-param value")
        assert result.status == "error"
        assert "invalid_parameters" in result.error_type

    def test_validate_command(self, system):
        """测试命令验证"""
        # 验证有效命令
        result = system.validate_command("/test --name hello")
        assert result["valid"] is True
        assert result["command"] == "test"
        assert result["parameters"]["name"] == "hello"

        # 验证无效命令
        result = system.validate_command("/nonexistent")
        assert result["valid"] is False
        assert "not found" in result["error"].lower() or "未找到" in result["error"]

    def test_get_command_suggestions(self, system):
        """测试获取命令建议"""
        suggestions = system.get_command_suggestions("/te")
        assert len(suggestions) > 0
        assert any(s.command == "/test" for s in suggestions)

    def test_generate_help_text(self, system):
        """测试生成帮助文本"""
        help_text = system.generate_help_text()
        assert "test" in help_text
        assert "Test command" in help_text

        # 特定命令的帮助
        specific_help = system.generate_help_text("test")
        assert "test" in specific_help
        assert "Test command" in specific_help

class TestCommandExecutionResult:
    """测试命令执行结果"""

    def test_create_successful_result(self):
        """测试创建成功结果"""
        result = CommandExecutionResult(
            execution_id="test-123",
            status="success",
            start_time=None,
            output={"message": "Success"}
        )
        assert result.status == "success"
        assert result.output["message"] == "Success"

    def test_create_error_result(self):
        """测试创建错误结果"""
        result = CommandExecutionResult(
            execution_id="test-123",
            status="error",
            start_time=None,
            error_message="Something went wrong",
            error_type="test_error"
        )
        assert result.status == "error"
        assert result.error_message == "Something went wrong"
        assert result.error_type == "test_error"

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_command_workflow(self):
        """测试完整的命令工作流程"""
        system = SlashCommandSystem()

        # 注册一个复杂的测试命令
        metadata = CommandMetadata(
            name="complex",
            aliases=["c"],
            description="Complex test command",
            usage="/complex [--required <value>] [--optional <value>] [--flag]",
            examples=[
                "/complex --required hello",
                "/complex --required hello --optional world --flag"
            ],
            handler="complex_handler",
            parameters=[
                CommandParameter(
                    name="required",
                    type="string",
                    required=True,
                    description="Required parameter"
                ),
                CommandParameter(
                    name="optional",
                    type="string",
                    required=False,
                    description="Optional parameter",
                    default="default"
                ),
                CommandParameter(
                    name="flag",
                    type="flag",
                    required=False,
                    description="A flag"
                )
            ]
        )

        async def complex_handler(context):
            return {
                "success": True,
                "received_params": context.parameters,
                "execution_id": context.execution_id
            }

        system.register_command(metadata, complex_handler)

        # 测试各种执行场景
        test_cases = [
            ("/complex --required test1", {"required": "test1", "optional": "default"}),
            ("/c --required test2 --optional custom", {"required": "test2", "optional": "custom"}),
            ("/complex --required test3 --flag", {"required": "test3", "optional": "default", "flag": True}),
        ]

        for command, expected_params in test_cases:
            result = await system.execute_command(command)
            assert result.status == "success"
            assert result.output["received_params"] == expected_params

    def test_error_handling_and_recovery(self):
        """测试错误处理和恢复"""
        system = SlashCommandSystem()

        # 注册一个会抛出异常的命令
        metadata = CommandMetadata(
            name="error",
            aliases=[],
            description="Error test command",
            usage="/error",
            examples=["/error"],
            handler="error_handler",
            parameters=[]
        )

        async def error_handler(context):
            raise ValueError("Test error")

        system.register_command(metadata, error_handler)

        # 验证错误被正确处理
        result = asyncio.run(system.execute_command("/error"))
        assert result.status == "error"
        assert "Test error" in result.error_message
        assert result.suggestions is not None

class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_command_execution_performance(self):
        """测试命令执行性能"""
        system = SlashCommandSystem()

        # 注册性能测试命令
        metadata = CommandMetadata(
            name="perf",
            aliases=[],
            description="Performance test command",
            usage="/perf",
            examples=["/perf"],
            handler="perf_handler",
            parameters=[]
        )

        async def perf_handler(context):
            # 模拟一些处理时间
            await asyncio.sleep(0.01)
            return {"success": True}

        system.register_command(metadata, perf_handler)

        # 测试多次执行的性能
        import time
        start_time = time.time()

        for _ in range(10):
            result = await system.execute_command("/perf")
            assert result.status == "success"

        end_time = time.time()
        total_time = end_time - start_time

        # 平均每次执行应该在合理时间内
        avg_time = total_time / 10
        assert avg_time < 1.0  # 每次执行应该少于1秒

if __name__ == "__main__":
    pytest.main([__file__, "-v"])