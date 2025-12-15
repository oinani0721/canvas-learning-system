#!/usr/bin/env python3
"""
Canvas学习系统 - 斜杠命令注册脚本

用于初始化和注册所有斜杠命令到系统中。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from slash_command_system import (
    SlashCommandSystem,
    CommandMetadata,
    CommandParameter,
    initialize_slash_command_system
)
from command_handlers import HANDLER_REGISTRY

def register_all_commands(system: SlashCommandSystem):
    """注册所有斜杠命令"""

    # ========== Canvas命令 ==========
    system.register_command(CommandMetadata(
        name="canvas",
        aliases=["c", "canvas-system"],
        description="Canvas学习系统主命令",
        usage="/canvas [action]",
        examples=["/canvas", "/canvas status", "/canvas help"],
        handler="handle_canvas_command",
        parameters=[
            CommandParameter(
                name="action",
                type="string",
                required=False,
                description="要执行的操作",
                choices=["status", "help", "version", "reset", "init"],
                default="status"
            )
        ],
        category="system"
    ), HANDLER_REGISTRY["handle_canvas_command"])

    system.register_command(CommandMetadata(
        name="canvas-status",
        aliases=["status", "cs"],
        description="显示Canvas系统状态",
        usage="/canvas-status [--detailed] [--component <component>]",
        examples=["/canvas-status", "/canvas-status detailed"],
        handler="handle_status_command",
        parameters=[
            CommandParameter(
                name="detailed",
                type="flag",
                required=False,
                description="显示详细信息"
            ),
            CommandParameter(
                name="component",
                type="string",
                required=False,
                description="检查特定组件状态",
                choices=["agents", "memory", "files", "performance"]
            )
        ],
        category="system"
    ), HANDLER_REGISTRY["handle_status_command"])

    system.register_command(CommandMetadata(
        name="canvas-help",
        aliases=["help", "ch", "?"],
        description="显示Canvas系统帮助信息",
        usage="/canvas-help [command] [--topic <topic>]",
        examples=["/canvas-help", "/canvas-help batch-explain"],
        handler="handle_help_command",
        parameters=[
            CommandParameter(
                name="command",
                type="string",
                required=False,
                description="要查看帮助的命令名称"
            ),
            CommandParameter(
                name="topic",
                type="string",
                required=False,
                description="帮助主题",
                choices=["basic", "advanced", "agents", "workflow"]
            )
        ],
        category="system"
    ), HANDLER_REGISTRY["handle_help_command"])

    # ========== Canvas操作命令 ==========
    system.register_command(CommandMetadata(
        name="batch-explain",
        aliases=["be", "explain-batch"],
        description="批量解释多个节点",
        usage="/batch-explain <canvas_file> [--agent <agent_type>] [--color_filter <color>]",
        examples=[
            "/batch-explain 离散数学.canvas",
            "/batch-explain 离散数学.canvas --agent oral-explanation"
        ],
        handler="handle_batch_explain_command",
        parameters=[
            CommandParameter(
                name="canvas_file",
                type="path",
                required=True,
                description="Canvas文件路径",
                validation={"must_exist": True, "file_types": [".canvas"]}
            ),
            CommandParameter(
                name="agent",
                type="string",
                required=False,
                description="使用的Agent类型",
                choices=["oral-explanation", "clarification-path", "memory-anchor", "comparison-table", "four-level-explanation", "example-teaching"],
                default="oral-explanation"
            ),
            CommandParameter(
                name="nodes",
                type="string",
                required=False,
                description="指定节点ID，用逗号分隔"
            ),
            CommandParameter(
                name="color_filter",
                type="string",
                required=False,
                description="按颜色筛选节点",
                choices=["red", "purple", "yellow", "blue", "green"]
            )
        ],
        category="canvas",
        timeout=120
    ), HANDLER_REGISTRY["handle_batch_explain_command"])

    system.register_command(CommandMetadata(
        name="generate-review",
        aliases=["gr", "review"],
        description="生成智能复习白板",
        usage="/generate-review <canvas_file> [--focus <focus_type>] [--output_name <name>]",
        examples=[
            "/generate-review 离散数学.canvas",
            "/generate-review 离散数学.canvas --focus weakness-focused"
        ],
        handler="handle_generate_review_command",
        parameters=[
            CommandParameter(
                name="canvas_file",
                type="path",
                required=True,
                description="源Canvas文件路径",
                validation={"must_exist": True, "file_types": [".canvas"]}
            ),
            CommandParameter(
                name="focus",
                type="string",
                required=False,
                description="复习焦点",
                choices=["weakness-focused", "comprehensive", "targeted"],
                default="comprehensive"
            ),
            CommandParameter(
                name="output_name",
                type="string",
                required=False,
                description="输出文件名（不含扩展名）"
            ),
            CommandParameter(
                name="include_explanations",
                type="boolean",
                required=False,
                description="是否包含AI解释节点",
                default=True
            )
        ],
        category="canvas",
        timeout=60
    ), HANDLER_REGISTRY["handle_generate_review_command"])

    system.register_command(CommandMetadata(
        name="optimize-layout",
        aliases=["ol", "optimize"],
        description="优化Canvas布局",
        usage="/optimize-layout <canvas_file> [--algorithm <algorithm>] [--backup <true|false>]",
        examples=["/optimize-layout 离散数学.canvas"],
        handler="handle_optimize_layout_command",
        parameters=[
            CommandParameter(
                name="canvas_file",
                type="path",
                required=True,
                description="Canvas文件路径",
                validation={"must_exist": True, "file_types": [".canvas"]}
            ),
            CommandParameter(
                name="algorithm",
                type="string",
                required=False,
                description="布局算法",
                choices=["v1.1", "hierarchical", "force-directed", "circular"],
                default="v1.1"
            ),
            CommandParameter(
                name="backup",
                type="boolean",
                required=False,
                description="是否创建备份",
                default=True
            )
        ],
        category="canvas",
        timeout=30
    ), HANDLER_REGISTRY["handle_optimize_layout_command"])

    # ========== 记忆系统命令 ==========
    system.register_command(CommandMetadata(
        name="memory-search",
        aliases=["ms", "search-memory"],
        description="搜索语义记忆",
        usage="/memory-search <query> [--limit <number>] [--context <context>] [--export <true|false>]",
        examples=[
            "/memory-search 逆否命题",
            "/memory-search 逻辑推理 --limit 5"
        ],
        handler="handle_memory_search_command",
        parameters=[
            CommandParameter(
                name="query",
                type="string",
                required=True,
                description="搜索关键词",
                validation={"min_length": 2, "max_length": 200}
            ),
            CommandParameter(
                name="limit",
                type="integer",
                required=False,
                description="结果数量限制",
                default=10,
                validation={"min_value": 1, "max_value": 50}
            ),
            CommandParameter(
                name="context",
                type="string",
                required=False,
                description="搜索上下文"
            ),
            CommandParameter(
                name="export",
                type="boolean",
                required=False,
                description="是否导出结果",
                default=False
            )
        ],
        category="memory",
        timeout=30
    ), HANDLER_REGISTRY["handle_memory_search_command"])

    system.register_command(CommandMetadata(
        name="memory-stats",
        aliases=["mstats", "memory-statistics"],
        description="显示记忆统计",
        usage="/memory-stats [--detailed] [--export <true|false>]",
        examples=["/memory-stats", "/memory-stats detailed"],
        handler="handle_memory_stats_command",
        parameters=[
            CommandParameter(
                name="detailed",
                type="flag",
                required=False,
                description="显示详细统计"
            ),
            CommandParameter(
                name="export",
                type="boolean",
                required=False,
                description="是否导出统计报告",
                default=False
            )
        ],
        category="memory",
        timeout=15
    ), HANDLER_REGISTRY["handle_memory_stats_command"])

    # ========== 分析命令 ==========
    system.register_command(CommandMetadata(
        name="analyze",
        aliases=["analysis", "learning-stats"],
        description="学习效果分析",
        usage="/analyze [canvas_file] [--type <analysis_type>] [--time_range <range>] [--export_format <format>]",
        examples=["/analyze", "/analyze 离散数学.canvas --type weakness"],
        handler="handle_analyze_command",
        parameters=[
            CommandParameter(
                name="canvas_file",
                type="path",
                required=False,
                description="要分析的Canvas文件"
            ),
            CommandParameter(
                name="type",
                type="string",
                required=False,
                description="分析类型",
                choices=["progress", "weakness", "efficiency", "comprehensive"],
                default="comprehensive"
            ),
            CommandParameter(
                name="time_range",
                type="string",
                required=False,
                description="时间范围",
                choices=["week", "month", "quarter", "all"],
                default="month"
            ),
            CommandParameter(
                name="export_format",
                type="string",
                required=False,
                description="导出格式",
                choices=["json", "markdown", "html"],
                default="markdown"
            )
        ],
        category="analytics",
        timeout=45
    ), HANDLER_REGISTRY["handle_analyze_command"])

    system.register_command(CommandMetadata(
        name="graph",
        aliases=["knowledge-graph", "kg"],
        description="知识图谱查询",
        usage="/graph [action] [--concept <concept>] [--depth <depth>] [--format <format>]",
        examples=["/graph show", "/graph query --concept 逆否命题"],
        handler="handle_graph_command",
        parameters=[
            CommandParameter(
                name="action",
                type="string",
                required=False,
                description="图谱操作",
                choices=["show", "query", "export", "visualize"],
                default="show"
            ),
            CommandParameter(
                name="concept",
                type="string",
                required=False,
                description="查询的概念"
            ),
            CommandParameter(
                name="depth",
                type="integer",
                required=False,
                description="查询深度",
                default=2,
                validation={"min_value": 1, "max_value": 5}
            ),
            CommandParameter(
                name="format",
                type="string",
                required=False,
                description="输出格式",
                choices=["text", "json", "mermaid"],
                default="text"
            )
        ],
        category="analytics",
        timeout=30
    ), HANDLER_REGISTRY["handle_graph_command"])

    # ========== 实用工具命令 ==========
    system.register_command(CommandMetadata(
        name="validate",
        aliases=["check", "verify"],
        description="验证Canvas文件",
        usage="/validate <canvas_file> [--check_types <types>] [--fix <true|false>]",
        examples=["/validate 离散数学.canvas", "/validate 离散数学.canvas --check_types colors"],
        handler="handle_validate_command",
        parameters=[
            CommandParameter(
                name="canvas_file",
                type="path",
                required=True,
                description="要验证的Canvas文件",
                validation={"must_exist": True, "file_types": [".canvas"]}
            ),
            CommandParameter(
                name="check_types",
                type="string",
                required=False,
                description="验证类型",
                choices=["syntax", "structure", "colors", "links", "all"],
                default="all"
            ),
            CommandParameter(
                name="fix",
                type="boolean",
                required=False,
                description="是否尝试自动修复",
                default=False
            )
        ],
        category="utilities",
        timeout=20
    ), HANDLER_REGISTRY["handle_validate_command"])

    system.register_command(CommandMetadata(
        name="export",
        aliases=["backup", "save"],
        description="导出Canvas数据",
        usage="/export <canvas_file> [--format <format>] [--output_dir <dir>] [--include_metadata <true|false>]",
        examples=["/export 离散数学.canvas", "/export 离散数学.canvas --format markdown"],
        handler="handle_export_command",
        parameters=[
            CommandParameter(
                name="canvas_file",
                type="path",
                required=True,
                description="要导出的Canvas文件",
                validation={"must_exist": True, "file_types": [".canvas"]}
            ),
            CommandParameter(
                name="format",
                type="string",
                required=False,
                description="导出格式",
                choices=["json", "markdown", "html", "pdf"],
                default="json"
            ),
            CommandParameter(
                name="output_dir",
                type="path",
                required=False,
                description="输出目录",
                default="exports"
            ),
            CommandParameter(
                name="include_metadata",
                type="boolean",
                required=False,
                description="是否包含元数据",
                default=True
            )
        ],
        category="utilities",
        timeout=25
    ), HANDLER_REGISTRY["handle_export_command"])

async def test_command_system():
    """测试命令系统"""
    print("正在测试斜杠命令系统...")

    # 初始化系统
    system = initialize_slash_command_system()
    register_all_commands(system)

    print(f"已注册 {len(system.command_registry.commands)} 个命令")

    # 测试一些命令
    test_commands = [
        "/help",
        "/canvas-status",
        "/commands",
        "/canvas version"
    ]

    for cmd in test_commands:
        print(f"\n测试命令: {cmd}")
        try:
            result = await system.execute_command(cmd)
            if result.status == "success":
                print(f"✅ 执行成功")
                if result.output:
                    print(f"   输出: {result.output.get('type', 'unknown')}")
            else:
                print(f"❌ 执行失败: {result.error_message}")
        except Exception as e:
            print(f"❌ 执行异常: {e}")

def main():
    """主函数"""
    print("Canvas学习系统 - 斜杠命令注册器")
    print("=" * 50)

    try:
        # 初始化系统
        system = initialize_slash_command_system()
        register_all_commands(system)

        print(f"✅ 成功注册 {len(system.command_registry.commands)} 个命令")
        print("\n已注册的命令:")

        # 按类别显示命令
        categories = {}
        for name, metadata in system.command_registry.commands.items():
            if metadata.category not in categories:
                categories[metadata.category] = []
            categories[metadata.category].append((name, metadata))

        for category, commands in categories.items():
            print(f"\n📁 {category.title()}:")
            for name, metadata in commands:
                aliases = f" ({', '.join(metadata.aliases)})" if metadata.aliases else ""
                print(f"  /{name}{aliases} - {metadata.description}")

        print(f"\n📊 统计信息:")
        print(f"  总命令数: {len(system.command_registry.commands)}")
        print(f"  类别数: {len(categories)}")
        print(f"  总别名数: {len(system.command_registry.alias_map)}")

        # 询问是否运行测试
        response = input("\n是否运行命令系统测试? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            asyncio.run(test_command_system())

        print(f"\n🎉 斜杠命令系统注册完成!")
        print("现在可以在Claude Code中使用这些斜杠命令了。")

    except Exception as e:
        print(f"❌ 注册失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)