"""
Parallel Command Parser - Canvas学习系统

本模块实现Claude Code斜杠命令并行接口的命令解析功能，
支持多种并行命令类型的解析和参数验证。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-26
"""

import re
import shlex
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

# 配置日志
logger = logging.getLogger(__name__)


class CommandType(Enum):
    """并行命令类型枚举"""
    PARALLEL_AGENTS = "parallel-agents"
    PARALLEL_NODES = "parallel-nodes"
    PARALLEL_COLOR = "parallel-color"
    PARALLEL_MIXED = "parallel-mixed"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ParallelCommand:
    """并行命令数据模型"""
    command_type: CommandType
    agent_type: str  # Agent类型，如"clarification-path"
    target_nodes: List[str] = field(default_factory=list)  # 节点ID列表
    node_count: Optional[int] = None  # 节点数量
    color_filter: Optional[str] = None  # 颜色筛选
    mixed_config: Optional[Dict[str, int]] = None  # 混合配置 {"agent_type": count}
    canvas_path: str = ""  # Canvas文件路径
    dry_run: bool = False  # 试运行模式
    max_instances: Optional[int] = None  # 最大实例数
    priority: TaskPriority = TaskPriority.NORMAL  # 任务优先级

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "command_type": self.command_type.value,
            "agent_type": self.agent_type,
            "target_nodes": self.target_nodes,
            "node_count": self.node_count,
            "color_filter": self.color_filter,
            "mixed_config": self.mixed_config,
            "canvas_path": self.canvas_path,
            "dry_run": self.dry_run,
            "max_instances": self.max_instances,
            "priority": self.priority.value
        }


@dataclass
class CommandResult:
    """命令执行结果"""
    command_id: str
    status: str  # "success", "failed", "cancelled"
    message: str
    processed_nodes: int = 0
    total_instances: int = 0
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "command_id": self.command_id,
            "status": self.status,
            "message": self.message,
            "processed_nodes": self.processed_nodes,
            "total_instances": self.total_instances,
            "execution_time": self.execution_time,
            "errors": self.errors,
            "metrics": self.metrics
        }


@dataclass
class CommandConfig:
    """命令配置"""
    default_agent_type: str = "clarification-path"
    max_concurrent_instances: int = 6
    default_canvas_path: str = ""
    enable_auto_discovery: bool = True
    output_format: str = "readable"  # "readable", "json", "summary"

    # 支持的Agent类型
    supported_agents: List[str] = field(default_factory=lambda: [
        "basic-decomposition",
        "deep-decomposition",
        "question-decomposition",
        "oral-explanation",
        "clarification-path",
        "comparison-table",
        "memory-anchor",
        "four-level-explanation",
        "example-teaching",
        "scoring-agent",
        "verification-question-agent"
    ])

    # 支持的颜色筛选
    supported_colors: List[str] = field(default_factory=lambda: ["1", "2", "3", "6"])


class ParallelCommandParser:
    """并行命令解析器

    负责解析和验证各种并行命令格式，将命令字符串转换为结构化的ParallelCommand对象。
    """

    def __init__(self, config: Optional[CommandConfig] = None):
        """初始化命令解析器

        Args:
            config: 命令配置对象，如果为None则使用默认配置
        """
        self.config = config or CommandConfig()

        # 命令模式正则表达式
        self.command_patterns = {
            CommandType.PARALLEL_AGENTS: r'^\*parallel-agents\s+(\w+)(?:\s+(\d+))?(?:\s+--\w+(?:=\S+)?)?\s*$',
            CommandType.PARALLEL_NODES: r'^\*parallel-nodes\s+(\w+)(?:\s+--nodes=[^,]+(?:,[^,]+)*)?(?:\s+--\w+(?:=\S+)?)?\s*$',
            CommandType.PARALLEL_COLOR: r'^\*parallel-color\s+(\w+)(?:\s+--color=[1-6])(?:\s+--\w+(?:=\S+)?)?\s*$',
            CommandType.PARALLEL_MIXED: r'^\*parallel-mixed\s+(.+?)(?:\s+--\w+(?:=\S+)?)?\s*$'
        }

        logger.info("ParallelCommandParser initialized")

    def parse_command(self, command_string: str) -> Tuple[Optional[ParallelCommand], List[str]]:
        """解析命令字符串，返回命令对象和错误列表

        Args:
            command_string: 原始命令字符串

        Returns:
            Tuple[Optional[ParallelCommand], List[str]]: 命令对象和错误列表
        """
        logger.info(f"Parsing command: {command_string}")

        # 预处理命令字符串
        command_string = command_string.strip()

        # 识别命令类型
        command_type = self._identify_command_type(command_string)
        if not command_type:
            return None, [f"无法识别的命令类型: {command_string}"]

        # 根据命令类型解析
        try:
            if command_type == CommandType.PARALLEL_AGENTS:
                return self._parse_parallel_agents(command_string)
            elif command_type == CommandType.PARALLEL_NODES:
                return self._parse_parallel_nodes(command_string)
            elif command_type == CommandType.PARALLEL_COLOR:
                return self._parse_parallel_color(command_string)
            elif command_type == CommandType.PARALLEL_MIXED:
                return self._parse_parallel_mixed(command_string)
        except Exception as e:
            logger.error(f"Error parsing command: {e}")
            return None, [f"解析命令时出错: {str(e)}"]

        return None, ["未知错误"]

    def _identify_command_type(self, command_string: str) -> Optional[CommandType]:
        """识别命令类型

        Args:
            command_string: 命令字符串

        Returns:
            Optional[CommandType]: 命令类型，如果无法识别则返回None
        """
        if command_string.startswith("*parallel-agents"):
            return CommandType.PARALLEL_AGENTS
        elif command_string.startswith("*parallel-nodes"):
            return CommandType.PARALLEL_NODES
        elif command_string.startswith("*parallel-color"):
            return CommandType.PARALLEL_COLOR
        elif command_string.startswith("*parallel-mixed"):
            return CommandType.PARALLEL_MIXED

        return None

    def _parse_parallel_agents(self, command_string: str) -> Tuple[Optional[ParallelCommand], List[str]]:
        """解析*parallel-agents命令

        格式: *parallel-agents <agent_type> [count] [options]

        示例:
        *parallel-agents clarification-path 4
        *parallel-agents memory-anchor --max=3 --canvas=test.canvas
        *parallel-agents oral-explanation 6 --dry-run
        """
        errors = []

        # 使用shlex分割命令参数
        try:
            parts = shlex.split(command_string)
        except ValueError as e:
            return None, [f"命令参数格式错误: {e}"]

        if len(parts) < 2:
            return None, ["*parallel-agents命令需要至少指定Agent类型"]

        # 解析Agent类型
        agent_type = parts[1]
        self._validate_agent_type(agent_type, errors)

        # 解析节点数量（可选）
        node_count = None
        if len(parts) >= 3 and parts[2].isdigit():
            node_count = int(parts[2])

        # 创建命令对象
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_AGENTS,
            agent_type=agent_type,
            node_count=node_count
        )

        # 解析选项参数
        option_errors = self._parse_options(command, parts[3:] if node_count else parts[2:])
        errors.extend(option_errors)

        return command if not errors or len(errors) == len(option_errors) else None, errors

    def _parse_parallel_nodes(self, command_string: str) -> Tuple[Optional[ParallelCommand], List[str]]:
        """解析*parallel-nodes命令

        格式: *parallel-nodes <agent_type> --nodes=node1,node2,node3 [options]

        示例:
        *parallel-nodes clarification-path --nodes=node1,node2,node3
        *parallel-nodes memory-anchor --nodes=node-abc,node-def --dry-run
        """
        errors = []

        # 使用shlex分割命令参数
        try:
            parts = shlex.split(command_string)
        except ValueError as e:
            return None, [f"命令参数格式错误: {e}"]

        if len(parts) < 2:
            return None, ["*parallel-nodes命令需要至少指定Agent类型"]

        # 解析Agent类型
        agent_type = parts[1]
        self._validate_agent_type(agent_type, errors)

        # 创建命令对象
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_NODES,
            agent_type=agent_type
        )

        # 解析选项参数
        option_errors = self._parse_options(command, parts[2:])
        errors.extend(option_errors)

        # 检查必需的nodes参数
        if not command.target_nodes:
            errors.append("*parallel-nodes命令需要指定--nodes参数")

        return command if not errors or len(errors) == len(option_errors) else None, errors

    def _parse_parallel_color(self, command_string: str) -> Tuple[Optional[ParallelCommand], List[str]]:
        """解析*parallel-color命令

        格式: *parallel-color <agent_type> --color=<color> [options]

        示例:
        *parallel-color clarification-path --color=1
        *parallel-color memory-anchor --color=3 --limit=5
        """
        errors = []

        # 使用shlex分割命令参数
        try:
            parts = shlex.split(command_string)
        except ValueError as e:
            return None, [f"命令参数格式错误: {e}"]

        if len(parts) < 2:
            return None, ["*parallel-color命令需要至少指定Agent类型"]

        # 解析Agent类型
        agent_type = parts[1]
        self._validate_agent_type(agent_type, errors)

        # 创建命令对象
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_COLOR,
            agent_type=agent_type
        )

        # 解析选项参数
        option_errors = self._parse_options(command, parts[2:])
        errors.extend(option_errors)

        # 检查必需的color参数
        if not command.color_filter:
            errors.append("*parallel-color命令需要指定--color参数")
        elif command.color_filter not in self.config.supported_colors:
            errors.append(f"不支持的颜色: {command.color_filter}。支持的颜色: {', '.join(self.config.supported_colors)}")

        return command if not errors or len(errors) == len(option_errors) else None, errors

    def _parse_parallel_mixed(self, command_string: str) -> Tuple[Optional[ParallelCommand], List[str]]:
        """解析*parallel-mixed命令

        格式: *parallel-mixed agent1:count1,agent2:count2 [options]

        示例:
        *parallel-mixed memory-anchor:3,clarification-path:4
        *parallel-mixed oral-explanation:2,example-teaching:3 --max=5
        """
        errors = []

        # 使用shlex分割命令参数
        try:
            parts = shlex.split(command_string)
        except ValueError as e:
            return None, [f"命令参数格式错误: {e}"]

        if len(parts) < 2:
            return None, ["*parallel-mixed命令需要指定混合配置"]

        # 解析混合配置
        mixed_config_str = parts[1]
        mixed_config = {}

        try:
            for item in mixed_config_str.split(','):
                if ':' not in item:
                    errors.append(f"无效的混合配置格式: {item}。应为 agent:count")
                    continue

                agent, count = item.split(':', 1)
                agent = agent.strip()
                count = count.strip()

                if agent not in self.config.supported_agents:
                    errors.append(f"不支持的Agent类型: {agent}")
                    continue

                try:
                    count_num = int(count)
                    if count_num <= 0:
                        errors.append(f"无效的实例数量: {count}。必须大于0")
                        continue
                    mixed_config[agent] = count_num
                except ValueError:
                    errors.append(f"无效的实例数量: {count}。必须是数字")
        except Exception as e:
            errors.append(f"解析混合配置时出错: {e}")

        if not mixed_config:
            return None, errors

        # 创建命令对象
        command = ParallelCommand(
            command_type=CommandType.PARALLEL_MIXED,
            agent_type="mixed",  # 混合模式使用特殊标识
            mixed_config=mixed_config
        )

        # 解析选项参数
        option_errors = self._parse_options(command, parts[2:])
        errors.extend(option_errors)

        return command if not errors or len(errors) == len(option_errors) else None, errors

    def _parse_options(self, command: ParallelCommand, options: List[str]) -> List[str]:
        """解析命令选项参数

        Args:
            command: 命令对象
            options: 选项参数列表

        Returns:
            List[str]: 错误列表
        """
        errors = []

        for option in options:
            option = option.strip()

            if option.startswith('--'):
                # 处理带值的选项
                if '=' in option:
                    key, value = option[2:].split('=', 1)
                    errors.extend(self._parse_option_with_value(command, key, value))
                else:
                    # 处理布尔选项
                    errors.extend(self._parse_option_boolean(command, option[2:]))
            else:
                errors.append(f"无效的选项格式: {option}。选项应以--开头")

        return errors

    def _parse_option_with_value(self, command: ParallelCommand, key: str, value: str) -> List[str]:
        """解析带值的选项

        Args:
            command: 命令对象
            key: 选项键
            value: 选项值

        Returns:
            List[str]: 错误列表
        """
        errors = []

        if key == 'nodes':
            # 解析节点列表
            command.target_nodes = [node.strip() for node in value.split(',')]
            if not command.target_nodes:
                errors.append("--nodes参数不能为空")

        elif key == 'color':
            # 解析颜色筛选
            command.color_filter = value
            if value not in self.config.supported_colors:
                errors.append(f"不支持的颜色: {value}。支持的颜色: {', '.join(self.config.supported_colors)}")

        elif key == 'canvas':
            # 解析Canvas路径
            command.canvas_path = value

        elif key == 'max':
            # 解析最大实例数
            try:
                max_instances = int(value)
                if max_instances <= 0:
                    errors.append("--max参数必须大于0")
                else:
                    command.max_instances = max_instances
            except ValueError:
                errors.append(f"无效的--max参数: {value}。必须是数字")

        elif key == 'limit':
            # 解析节点数量限制
            try:
                limit = int(value)
                if limit <= 0:
                    errors.append("--limit参数必须大于0")
                else:
                    command.node_count = limit
            except ValueError:
                errors.append(f"无效的--limit参数: {value}。必须是数字")

        elif key == 'priority':
            # 解析优先级
            try:
                priority_map = {
                    'low': TaskPriority.LOW,
                    'normal': TaskPriority.NORMAL,
                    'high': TaskPriority.HIGH,
                    'urgent': TaskPriority.URGENT
                }
                priority = priority_map.get(value.lower())
                if priority:
                    command.priority = priority
                else:
                    errors.append(f"无效的优先级: {value}。支持的值: low, normal, high, urgent")
            except Exception:
                errors.append(f"无效的--priority参数: {value}")

        else:
            errors.append(f"未知的选项: --{key}")

        return errors

    def _parse_option_boolean(self, command: ParallelCommand, key: str) -> List[str]:
        """解析布尔选项

        Args:
            command: 命令对象
            key: 选项键

        Returns:
            List[str]: 错误列表
        """
        if key == 'dry-run':
            command.dry_run = True
        else:
            return [f"未知的布尔选项: --{key}"]

        return []

    def _validate_agent_type(self, agent_type: str, errors: List[str]) -> None:
        """验证Agent类型并添加到错误列表

        Args:
            agent_type: 要验证的Agent类型
            errors: 错误列表
        """
        if agent_type not in self.config.supported_agents:
            errors.append(f"不支持的Agent类型: {agent_type}。支持的类型: {', '.join(self.config.supported_agents)}")

    def validate_command(self, command: ParallelCommand) -> List[str]:
        """验证命令参数，返回错误列表

        Args:
            command: 命令对象

        Returns:
            List[str]: 错误列表，如果为空则表示验证通过
        """
        errors = []

        # 验证Agent类型（混合模式除外）
        if command.command_type != CommandType.PARALLEL_MIXED:
            if command.agent_type not in self.config.supported_agents:
                errors.append(f"不支持的Agent类型: {command.agent_type}")

        # 验证节点数量
        if command.node_count is not None and command.node_count <= 0:
            errors.append("节点数量必须大于0")

        # 验证颜色筛选
        if command.color_filter and command.color_filter not in self.config.supported_colors:
            errors.append(f"不支持的颜色: {command.color_filter}。支持的颜色: {', '.join(self.config.supported_colors)}")

        # 验证最大实例数
        if command.max_instances is not None:
            if command.max_instances <= 0:
                errors.append("最大实例数必须大于0")
            elif command.max_instances > self.config.max_concurrent_instances:
                errors.append(f"最大实例数不能超过系统限制: {self.config.max_concurrent_instances}")

        # 验证Canvas路径
        if command.canvas_path and not command.canvas_path.endswith('.canvas'):
            errors.append("Canvas路径必须以.canvas结尾")

        # 验证混合配置
        if command.command_type == CommandType.PARALLEL_MIXED:
            if not command.mixed_config:
                errors.append("混合命令必须指定配置")
            else:
                total_instances = sum(command.mixed_config.values())
                if total_instances > self.config.max_concurrent_instances:
                    errors.append(f"混合配置的总实例数({total_instances})超过系统限制({self.config.max_concurrent_instances})")

        return errors

    def get_command_help(self, command_type: Optional[CommandType] = None) -> str:
        """获取命令帮助信息

        Args:
            command_type: 命令类型，如果为None则返回所有命令的帮助

        Returns:
            str: 帮助信息
        """
        help_text = []

        if command_type is None:
            help_text.append("并行命令帮助")
            help_text.append("=" * 50)
            help_text.append("")
            help_text.append("支持的并行命令类型：")
            help_text.append("")

            for cmd_type in CommandType:
                help_text.append(f"  *{cmd_type.value}")
                help_text.append(f"    {self._get_command_description(cmd_type)}")
                help_text.append("")
        else:
            help_text.append(f"*{command_type.value} 命令帮助")
            help_text.append("=" * 50)
            help_text.append("")
            help_text.append(self._get_command_description(command_type))
            help_text.append("")
            help_text.append("语法格式:")
            help_text.append(self._get_command_syntax(command_type))
            help_text.append("")
            help_text.append("参数说明:")
            help_text.append(self._get_command_parameters(command_type))
            help_text.append("")
            help_text.append("示例:")
            help_text.append(self._get_command_examples(command_type))

        return "\n".join(help_text)

    def _get_command_description(self, command_type: CommandType) -> str:
        """获取命令描述"""
        descriptions = {
            CommandType.PARALLEL_AGENTS: "使用指定类型的Agent并行处理多个节点",
            CommandType.PARALLEL_NODES: "使用指定Agent并行处理特定的节点ID列表",
            CommandType.PARALLEL_COLOR: "使用指定Agent并行处理特定颜色的所有节点",
            CommandType.PARALLEL_MIXED: "使用多种类型的Agent混合并行处理"
        }
        return descriptions.get(command_type, "未知命令类型")

    def _get_command_syntax(self, command_type: CommandType) -> str:
        """获取命令语法格式"""
        syntaxes = {
            CommandType.PARALLEL_AGENTS: "*parallel-agents <agent_type> [count] [options]",
            CommandType.PARALLEL_NODES: "*parallel-nodes <agent_type> --nodes=node1,node2,node3 [options]",
            CommandType.PARALLEL_COLOR: "*parallel-color <agent_type> --color=<color> [options]",
            CommandType.PARALLEL_MIXED: "*parallel-mixed agent1:count1,agent2:count2 [options]"
        }
        return syntaxes.get(command_type, "未知语法格式")

    def _get_command_parameters(self, command_type: CommandType) -> str:
        """获取命令参数说明"""
        params = {
            CommandType.PARALLEL_AGENTS: """
  <agent_type>    Agent类型 (如 clarification-path, memory-anchor)
  [count]        要处理的节点数量 (可选)
  --nodes=<list>  指定节点ID列表 (如 node1,node2,node3)
  --max=<num>     最大并发实例数 (默认6)
  --canvas=<path> Canvas文件路径
  --dry-run       试运行模式，不实际执行
  --priority=<p>  任务优先级 (low/normal/high/urgent)
""",
            CommandType.PARALLEL_NODES: """
  <agent_type>    Agent类型 (如 clarification-path, memory-anchor)
  --nodes=<list>  节点ID列表 (必需，如 node1,node2,node3)
  --max=<num>     最大并发实例数 (默认6)
  --canvas=<path> Canvas文件路径
  --dry-run       试运行模式，不实际执行
  --priority=<p>  任务优先级 (low/normal/high/urgent)
""",
            CommandType.PARALLEL_COLOR: """
  <agent_type>    Agent类型 (如 clarification-path, memory-anchor)
  --color=<c>     节点颜色 (必需: 1=红, 2=绿, 3=紫, 6=黄)
  --limit=<num>   限制处理的节点数量 (可选)
  --max=<num>     最大并发实例数 (默认6)
  --canvas=<path> Canvas文件路径
  --dry-run       试运行模式，不实际执行
  --priority=<p>  任务优先级 (low/normal/high/urgent)
""",
            CommandType.PARALLEL_MIXED: """
  <mixed_config>  混合配置 (如 memory-anchor:3,clarification-path:4)
  --max=<num>     最大并发实例数 (默认6)
  --canvas=<path> Canvas文件路径
  --dry-run       试运行模式，不实际执行
  --priority=<p>  任务优先级 (low/normal/high/urgent)
"""
        }
        return params.get(command_type, "未知参数")

    def _get_command_examples(self, command_type: CommandType) -> str:
        """获取命令示例"""
        examples = {
            CommandType.PARALLEL_AGENTS: """
*parallel-agents clarification-path 4
*parallel-agents memory-anchor --max=3 --canvas=离散数学.canvas
*parallel-agents oral-explanation 6 --dry-run
*parallel-agents comparison-table --nodes=node1,node2,node3 --priority=high
""",
            CommandType.PARALLEL_NODES: """
*parallel-nodes clarification-path --nodes=node-abc,node-def,node-ghi
*parallel-nodes memory-anchor --nodes=node1,node2 --dry-run --canvas=test.canvas
*parallel-nodes scoring-agent --nodes=node-1,node-2,node-3 --max=4
""",
            CommandType.PARALLEL_COLOR: """
*parallel-color clarification-path --color=1
*parallel-color memory-anchor --color=3 --limit=5
*parallel-color oral-explanation --color=6 --max=4 --canvas=example.canvas
""",
            CommandType.PARALLEL_MIXED: """
*parallel-mixed memory-anchor:3,clarification-path:4
*parallel-mixed oral-explanation:2,example-teaching:3 --max=5
*parallel-mixed comparison-table:2,scoring-agent:2 --dry-run
"""
        }
        return examples.get(command_type, "暂无示例")

    def suggest_completion(self, partial_command: str) -> List[str]:
        """提供命令自动补全建议

        Args:
            partial_command: 部分命令字符串

        Returns:
            List[str]: 补全建议列表
        """
        suggestions = []
        partial = partial_command.strip()
        partial_lower = partial.lower()

  
        # 如果输入为空，返回所有命令类型
        if not partial:
            return [f"*{cmd_type.value}" for cmd_type in CommandType]

        # 如果以*开头
        if partial_lower.startswith('*'):
            # 检查是否已经输入了完整的命令类型
            matched_cmd_type = None
            partial_cmd_only = partial.split()[0]  # 只取第一个词作为命令

            for cmd_type in CommandType:
                if partial_cmd_only.lower() == f"*{cmd_type.value}":
                    matched_cmd_type = cmd_type
                    break

            # 如果匹配了命令类型
            if matched_cmd_type:
                # 如果后面有内容（不仅仅是空格），说明是要补全Agent类型
                # 使用原始partial_command而不是partial，这样可以保留末尾的空格
                if len(partial_command) > len(partial_cmd_only):
                    for agent in self.config.supported_agents:
                        suggestions.append(f"{partial_cmd_only} {agent}")

                    # 如果是*parallel-mixed，添加混合配置建议
                    if matched_cmd_type == CommandType.PARALLEL_MIXED:
                        suggestions.append("*parallel-mixed memory-anchor:3,clarification-path:4")
                        suggestions.append("*parallel-mixed oral-explanation:2,example-teaching:3")
            else:
                # 没有匹配完整命令类型，建议可能的命令类型
                for cmd_type in CommandType:
                    if cmd_type.value.startswith(partial_lower[1:]):
                        suggestions.append(f"*{cmd_type.value}")

        # 去重并返回前20个建议（确保能包含所有agent建议）
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        return unique_suggestions[:20]