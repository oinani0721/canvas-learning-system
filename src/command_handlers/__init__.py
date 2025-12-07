"""
Canvas学习系统 - 命令处理器模块

本模块包含所有斜杠命令的处理器实现。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

# 导入所有处理器模块
from .analytics_commands import *
from .canvas_commands import *
from .memory_commands import *
from .system_commands import *
from .utilities_commands import *

# 处理器注册表
HANDLER_REGISTRY = {
    # Canvas命令处理器
    'handle_canvas_command': handle_canvas_command,
    'handle_status_command': handle_status_command,
    'handle_help_command': handle_help_command,
    'handle_batch_explain_command': handle_batch_explain_command,
    'handle_generate_review_command': handle_generate_review_command,
    'handle_optimize_layout_command': handle_optimize_layout_command,

    # 记忆系统命令处理器
    'handle_memory_search_command': handle_memory_search_command,
    'handle_memory_stats_command': handle_memory_stats_command,

    # 分析命令处理器
    'handle_analyze_command': handle_analyze_command,
    'handle_graph_command': handle_graph_command,

    # 实用工具命令处理器
    'handle_validate_command': handle_validate_command,
    'handle_export_command': handle_export_command,
}

def get_all_handlers():
    """获取所有处理器函数"""
    return HANDLER_REGISTRY

def register_handler(name: str, handler_func):
    """注册新的处理器"""
    HANDLER_REGISTRY[name] = handler_func

def get_handler(name: str):
    """获取指定名称的处理器"""
    return HANDLER_REGISTRY.get(name)
