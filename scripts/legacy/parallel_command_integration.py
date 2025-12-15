"""
Parallel Command Integration - Canvas学习系统

本模块提供并行命令系统的集成接口，统一管理命令解析和执行。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-26
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Optional, Any, Callable, List
from datetime import datetime
import json

# 导入并行命令模块
from parallel_command_parser import (
    ParallelCommandParser, ParallelCommand, CommandConfig, CommandType
)
from command_executor import CommandExecutor

# 配置日志
logger = logging.getLogger(__name__)


class ParallelCommandSystem:
    """并行命令系统主入口

    整合命令解析和执行功能，提供统一的API接口。
    """

    def __init__(self, config: Optional[CommandConfig] = None):
        """初始化并行命令系统

        Args:
            config: 命令配置，如果为None则使用默认配置
        """
        self.config = config or CommandConfig()
        self.parser = ParallelCommandParser(self.config)
        self.executor = None
        self.execution_history: List[Dict] = []

        # 初始化执行器
        self._initialize_executor()

        logger.info("ParallelCommandSystem initialized")

    def _initialize_executor(self):
        """初始化命令执行器"""
        # 设置进度回调
        progress_callback = self._on_progress_update

        try:
            self.executor = CommandExecutor(
                progress_callback=progress_callback
            )
            logger.info("CommandExecutor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CommandExecutor: {e}")
            self.executor = None

    async def execute_command_string(self, command_string: str) -> Dict:
        """执行命令字符串

        Args:
            command_string: 原始命令字符串

        Returns:
            Dict: 执行结果
        """
        logger.info(f"Executing command string: {command_string}")

        # 解析命令
        command, errors = self.parser.parse_command(command_string)

        if errors and not command:
            return {
                "success": False,
                "message": "命令解析失败",
                "errors": errors
            }

        # 验证命令
        validation_errors = self.parser.validate_command(command)
        if validation_errors:
            return {
                "success": False,
                "message": "命令验证失败",
                "errors": validation_errors
            }

        # 检查执行器是否可用
        if not self.executor:
            return {
                "success": False,
                "message": "命令执行器不可用",
                "errors": ["CommandExecutor not initialized"]
            }

        try:
            # 执行命令
            result = await self.executor.execute_command(command)

            # 记录执行历史
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "command": command_string,
                "result": result.to_dict()
            })

            # 格式化返回结果
            return {
                "success": result.status in ["success", "completed_with_errors"],
                "message": result.message,
                "result": result.to_dict(),
                "errors": result.errors
            }

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "success": False,
                "message": f"命令执行出错: {str(e)}",
                "errors": [str(e)]
            }

    async def preview_command(self, command_string: str) -> Dict:
        """预览命令执行计划

        Args:
            command_string: 命令字符串

        Returns:
            Dict: 预览信息
        """
        # 解析命令
        command, errors = self.parser.parse_command(command_string)

        if errors:
            return {
                "success": False,
                "message": "命令解析失败",
                "errors": errors
            }

        # 检查执行器是否可用
        if not self.executor:
            return {
                "success": False,
                "message": "命令执行器不可用",
                "preview": None
            }

        try:
            preview = await self.executor.preview_command(command)
            return {
                "success": True,
                "message": "预览生成成功",
                "preview": preview
            }
        except Exception as e:
            logger.error(f"Error previewing command: {e}")
            return {
                "success": False,
                "message": f"预览生成失败: {str(e)}",
                "preview": None
            }

    def get_command_suggestions(self, partial_command: str) -> List[str]:
        """获取命令补全建议

        Args:
            partial_command: 部分命令

        Returns:
            List[str]: 补全建议列表
        """
        return self.parser.suggest_completion(partial_command)

    def get_command_help(self, command_type: Optional[str] = None) -> str:
        """获取命令帮助

        Args:
            command_type: 命令类型，如果为None则返回所有命令帮助

        Returns:
            str: 帮助信息
        """
        if command_type:
            # 解析命令类型
            for cmd_type in CommandType:
                if cmd_type.value == command_type:
                    return self.parser.get_command_help(cmd_type)
            return f"未知的命令类型: {command_type}"
        else:
            return self.parser.get_command_help()

    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """获取执行历史

        Args:
            limit: 返回的历史记录数量

        Returns:
            List[Dict]: 执行历史
        """
        if limit > 0:
            return self.execution_history[-limit:]
        return self.execution_history

    def get_system_status(self) -> Dict:
        """获取系统状态

        Returns:
            Dict: 系统状态信息
        """
        status = {
            "parser_available": self.parser is not None,
            "executor_available": self.executor is not None,
            "config": {
                "max_concurrent_instances": self.config.max_concurrent_instances,
                "supported_agents": self.config.supported_agents,
                "supported_colors": self.config.supported_colors
            },
            "execution_count": len(self.execution_history),
            "last_execution": None
        }

        if self.execution_history:
            status["last_execution"] = self.execution_history[-1]["timestamp"]

        return status

    def _on_progress_update(self, progress_info: Dict):
        """进度更新回调

        Args:
            progress_info: 进度信息字典
        """
        # 这里可以实现进度显示逻辑
        # 例如：显示进度条、发送通知等
        percentage = progress_info.get("progress_percentage", 0)
        completed = progress_info.get("completed", 0)
        total = progress_info.get("total", 0)
        current_task = progress_info.get("current_task", "")

        # 生成进度条
        bar_length = 20
        filled_length = int(bar_length * percentage / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        # 输出进度（在实际使用中可能需要更复杂的UI）
        print(f"\r⏳ [{bar}] {percentage:.1f}% ({completed}/{total}) {current_task}", end="", flush=True)

        # 完成时换行
        if percentage >= 100:
            print()  # 换行


# 全局实例
_parallel_system: Optional[ParallelCommandSystem] = None


def get_parallel_system() -> ParallelCommandSystem:
    """获取全局并行命令系统实例

    Returns:
        ParallelCommandSystem: 全局实例
    """
    global _parallel_system
    if _parallel_system is None:
        _parallel_system = ParallelCommandSystem()
    return _parallel_system


async def execute_parallel_command(command_string: str) -> Dict:
    """便捷函数：执行并行命令

    Args:
        command_string: 命令字符串

    Returns:
        Dict: 执行结果
    """
    system = get_parallel_system()
    return await system.execute_command_string(command_string)


def preview_parallel_command(command_string: str) -> Dict:
    """便捷函数：预览并行命令

    Args:
        command_string: 命令字符串

    Returns:
        Dict: 预览信息
    """
    system = get_parallel_system()
    return asyncio.run(system.preview_command(command_string))


# CLI工具函数
def run_cli():
    """运行CLI模式"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Canvas并行命令系统CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # execute命令
    exec_parser = subparsers.add_parser("execute", help="执行并行命令")
    exec_parser.add_argument("command", help="要执行的命令")

    # preview命令
    preview_parser = subparsers.add_parser("preview", help="预览执行计划")
    preview_parser.add_argument("command", help="要预览的命令")

    # help命令
    help_parser = subparsers.add_parser("help", help="获取帮助")
    help_parser.add_argument(
        "command_type",
        nargs="?",
        help="命令类型（可选）"
    )

    # status命令
    subparsers.add_parser("status", help="显示系统状态")

    # history命令
    history_parser = subparsers.add_parser("history", help="显示执行历史")
    history_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="显示的历史记录数量"
    )

    args = parser.parse_args()

    # 执行命令
    if args.command == "execute":
        async def run_execute():
            result = await execute_parallel_command(args.command)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        asyncio.run(run_execute())

    elif args.command == "preview":
        result = preview_parallel_command(args.command)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "help":
        system = get_parallel_system()
        help_text = system.get_command_help(args.command_type)
        print(help_text)

    elif args.command == "status":
        system = get_parallel_system()
        status = system.get_system_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.command == "history":
        system = get_parallel_system()
        history = system.get_execution_history(args.limit)
        print(json.dumps(history, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    # 如果直接运行此文件，启动CLI
    run_cli()