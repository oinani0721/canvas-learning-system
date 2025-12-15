"""
Canvas学习系统 - 斜杠命令系统

本模块实现Claude Code原生斜杠命令系统，支持：
- 命令注册和分发机制
- 参数解析和验证
- 自动补全系统
- 用户友好的错误处理
- 本地化和别名支持
- 命令历史和记录

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import json
import re
import time
import uuid
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import yaml
import os

# ========== 常量定义 ==========

# 默认配置
DEFAULT_CONFIG_PATH = "config/slash_commands.yaml"
DEFAULT_HISTORY_PATH = "data/command_history.json"
DEFAULT_TIMEOUT_SECONDS = 120
MAX_COMMAND_LENGTH = 1000

# 命令执行状态
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_TIMEOUT = "timeout"
STATUS_CANCELLED = "cancelled"

# 错误类型
ERROR_COMMAND_NOT_FOUND = "command_not_found"
ERROR_INVALID_PARAMETERS = "invalid_parameters"
ERROR_HANDLER_NOT_FOUND = "handler_not_found"
ERROR_EXECUTION_FAILED = "execution_failed"
ERROR_TIMEOUT = "timeout"

# ========== 数据模型 ==========

@dataclass
class CommandParameter:
    """命令参数定义"""
    name: str
    type: str  # string, integer, boolean, flag, path, choice
    required: bool = False
    description: str = ""
    default: Any = None
    choices: Optional[List[str]] = None
    validation: Optional[Dict] = None

@dataclass
class CommandMetadata:
    """命令元数据"""
    name: str
    aliases: List[str]
    description: str
    usage: str
    examples: List[str]
    handler: str
    parameters: List[CommandParameter]
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    category: str = "general"
    enabled: bool = True

@dataclass
class CommandExecutionContext:
    """命令执行上下文"""
    execution_id: str
    command_name: str
    raw_command: str
    parameters: Dict[str, Any]
    timestamp: datetime
    user_id: str = "default"
    session_id: str = "default"

@dataclass
class CommandExecutionResult:
    """命令执行结果"""
    execution_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    output: Optional[Dict] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    suggestions: Optional[List[str]] = None

@dataclass
class CommandSuggestion:
    """命令建议"""
    command: str
    description: str
    confidence: float
    category: str = "general"

# ========== 异常类 ==========

class SlashCommandError(Exception):
    """斜杠命令基础异常"""
    pass

class CommandNotFoundError(SlashCommandError):
    """命令未找到异常"""
    pass

class InvalidParametersError(SlashCommandError):
    """无效参数异常"""
    pass

class HandlerNotFoundError(SlashCommandError):
    """处理器未找到异常"""
    pass

class CommandTimeoutError(SlashCommandError):
    """命令执行超时异常"""
    pass

class SecurityError(SlashCommandError):
    """安全相关异常"""
    pass

# ========== 参数解析器 ==========

class ArgumentParser:
    """参数解析器"""

    def __init__(self):
        self.parsers = {
            'string': self._parse_string,
            'integer': self._parse_integer,
            'boolean': self._parse_boolean,
            'flag': self._parse_flag,
            'path': self._parse_path,
            'choice': self._parse_choice
        }

    def parse_arguments(self, args: List[str], parameters: List[CommandParameter]) -> Dict[str, Any]:
        """解析参数列表

        Args:
            args: 参数列表
            parameters: 参数定义列表

        Returns:
            Dict[str, Any]: 解析后的参数字典

        Raises:
            InvalidParametersError: 当参数无效时
            SecurityError: 当检测到潜在安全风险时
        """
        result = {}
        i = 0
        n = len(args)

        # 安全检查：限制参数数量
        if len(args) > 100:  # 防止参数过多攻击
            raise SecurityError("参数数量过多，可能存在安全风险")

        # 处理位置参数和命名参数
        while i < n:
            arg = args[i]

            # 安全检查：验证参数格式
            if not isinstance(arg, str):
                raise InvalidParametersError(f"参数格式无效: {arg}")

            if len(arg) > 1000:  # 防止参数过长攻击
                raise SecurityError(f"参数过长: {arg[:50]}...")

            if arg.startswith('--'):
                # 命名参数
                param_name = arg[2:]
                i += 1

                # 安全检查：验证参数名称
                if not param_name or not self._is_safe_parameter_name(param_name):
                    raise InvalidParametersError(f"无效的参数名: --{param_name}")

                # 查找对应的参数定义
                param_def = self._find_parameter(param_name, parameters)
                if not param_def:
                    raise InvalidParametersError(f"未知参数: --{param_name}")

                # 解析参数值
                if param_def.type == 'flag':
                    result[param_name] = True
                else:
                    if i >= n:
                        raise InvalidParametersError(f"参数 --{param_name} 需要值")

                    value = args[i]
                    i += 1

                    # 安全检查：验证参数值
                    if not isinstance(value, str):
                        raise InvalidParametersError(f"参数值格式无效: --{param_name}")

                    if len(value) > 1000:  # 防止参数值过长攻击
                        raise SecurityError(f"参数值过长: --{param_name}={value[:50]}...")

                    # 检查是否包含潜在危险的字符
                    if self._contains_dangerous_chars(value):
                        raise SecurityError(f"参数值包含危险字符: --{param_name}")

                    # 类型转换
                    parsed_value = self._parse_parameter_value(value, param_def)
                    result[param_name] = parsed_value
            else:
                # 位置参数 - 暂时不支持，因为所有参数都是有名的
                i += 1

        # 检查必需参数
        for param in parameters:
            if param.required and param.name not in result:
                raise InvalidParametersError(f"缺少必需参数: --{param.name}")

            # 设置默认值
            if param.name not in result and param.default is not None:
                result[param.name] = param.default

        return result

    def _find_parameter(self, name: str, parameters: List[CommandParameter]) -> Optional[CommandParameter]:
        """查找参数定义"""
        for param in parameters:
            if param.name == name:
                return param
        return None

    def _parse_parameter_value(self, value: str, param_def: CommandParameter) -> Any:
        """解析参数值"""
        parser = self.parsers.get(param_def.type)
        if not parser:
            raise InvalidParametersError(f"不支持的参数类型: {param_def.type}")

        return parser(value, param_def)

    def _parse_string(self, value: str, param_def: CommandParameter) -> str:
        """解析字符串参数"""
        if param_def.validation:
            self._validate_string(value, param_def.validation)
        return value

    def _parse_integer(self, value: str, param_def: CommandParameter) -> int:
        """解析整数参数"""
        try:
            int_value = int(value)
            if param_def.validation:
                self._validate_integer(int_value, param_def.validation)
            return int_value
        except ValueError:
            raise InvalidParametersError(f"参数 '{param_def.name}' 需要整数，得到: {value}")

    def _parse_boolean(self, value: str, param_def: CommandParameter) -> bool:
        """解析布尔参数"""
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        else:
            raise InvalidParametersError(f"参数 '{param_def.name}' 需要布尔值，得到: {value}")

    def _parse_flag(self, value: str, param_def: CommandParameter) -> bool:
        """解析标志参数"""
        return True

    def _parse_path(self, value: str, param_def: CommandParameter) -> str:
        """解析路径参数"""
        path = Path(value)
        if not path.exists() and param_def.validation and param_def.validation.get('must_exist', False):
            raise InvalidParametersError(f"路径不存在: {value}")
        return str(path.absolute())

    def _parse_choice(self, value: str, param_def: CommandParameter) -> str:
        """解析选择参数"""
        if not param_def.choices:
            raise InvalidParametersError(f"选择参数 '{param_def.name}' 没有定义选项")

        if value not in param_def.choices:
            raise InvalidParametersError(
                f"参数 '{param_def.name}' 的值 '{value}' 不在选项中: {', '.join(param_def.choices)}"
            )
        return value

    def _validate_string(self, value: str, validation: Dict):
        """验证字符串参数"""
        if 'min_length' in validation and len(value) < validation['min_length']:
            raise InvalidParametersError(f"字符串长度不能少于 {validation['min_length']}")

        if 'max_length' in validation and len(value) > validation['max_length']:
            raise InvalidParametersError(f"字符串长度不能超过 {validation['max_length']}")

        if 'pattern' in validation and not re.match(validation['pattern'], value):
            raise InvalidParametersError(f"字符串不匹配模式: {validation['pattern']}")

    def _validate_integer(self, value: int, validation: Dict):
        """验证整数参数"""
        if 'min_value' in validation and value < validation['min_value']:
            raise InvalidParametersError(f"整数不能小于 {validation['min_value']}")

        if 'max_value' in validation and value > validation['max_value']:
            raise InvalidParametersError(f"整数不能大于 {validation['max_value']}")

    def _is_safe_parameter_name(self, param_name: str) -> bool:
        """检查参数名称是否安全"""
        if not isinstance(param_name, str) or not param_name:
            return False

        # 参数名称只允许字母、数字、下划线和连字符
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, param_name))

    def _contains_dangerous_chars(self, value: str) -> bool:
        """检查参数值是否包含危险字符"""
        if not isinstance(value, str):
            return False

        # 检查常见的注入攻击字符
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '"', "'", '\\', '/', '*', '?']
        return any(char in value for char in dangerous_chars)

# ========== 自动补全系统 ==========

class AutoCompletionSystem:
    """自动补全系统"""

    def __init__(self, command_registry: 'CommandRegistry'):
        self.command_registry = command_registry
        self.command_history = []
        self.file_cache = {}

    def get_suggestions(self, partial_input: str, context: Dict = None) -> List[CommandSuggestion]:
        """获取命令建议"""
        suggestions = []

        # 命令补全
        if partial_input.startswith('/'):
            command_part = partial_input[1:].lower()
            for cmd_name, metadata in self.command_registry.commands.items():
                if cmd_name.startswith(command_part):
                    suggestions.append(CommandSuggestion(
                        command=f"/{cmd_name}",
                        description=metadata.description,
                        confidence=1.0,
                        category=metadata.category
                    ))

                # 检查别名
                for alias in metadata.aliases:
                    if alias.startswith(command_part):
                        suggestions.append(CommandSuggestion(
                            command=f"/{alias}",
                            description=metadata.description,
                            confidence=0.9,
                            category=metadata.category
                        ))

        # 参数补全
        if ' ' in partial_input:
            parts = partial_input.split()
            if len(parts) >= 2 and parts[0].startswith('/'):
                command_name = parts[0][1:]
                metadata = self.command_registry.get_command_metadata(command_name)
                if metadata:
                    param_suggestions = self._get_parameter_suggestions(metadata, parts[1:])
                    suggestions.extend(param_suggestions)

        # 文件路径补全
        suggestions.extend(self._get_file_suggestions(partial_input))

        # 历史命令补全
        suggestions.extend(self._get_history_suggestions(partial_input))

        # 按置信度排序
        suggestions.sort(key=lambda x: x.confidence, reverse=True)

        return suggestions[:10]  # 返回前10个建议

    def _get_parameter_suggestions(self, metadata: CommandMetadata, current_params: List[str]) -> List[CommandSuggestion]:
        """获取参数建议"""
        suggestions = []
        used_params = set()

        # 分析已使用的参数
        for param in current_params:
            if param.startswith('--'):
                used_params.add(param[2:])

        # 为未使用的参数提供建议
        for param_def in metadata.parameters:
            if param_def.name not in used_params:
                suggestion = f"--{param_def.name}"
                if param_def.type == 'choice' and param_def.choices:
                    suggestion += f" [{'|'.join(param_def.choices[:3])}...]"

                suggestions.append(CommandSuggestion(
                    command=suggestion,
                    description=param_def.description,
                    confidence=0.8,
                    category="parameter"
                ))

        return suggestions

    def _get_file_suggestions(self, partial_input: str) -> List[CommandSuggestion]:
        """获取文件路径建议"""
        suggestions = []

        # 检查是否是路径参数
        if any(pattern in partial_input for pattern in [' --', '/canvas ', '/generate-review ']):
            # 简化的文件补全
            current_dir = Path('.')
            canvas_files = list(current_dir.glob('**/*.canvas'))

            for canvas_file in canvas_files[:5]:  # 限制数量
                relative_path = canvas_file.relative_to(current_dir)
                suggestions.append(CommandSuggestion(
                    command=str(relative_path),
                    description=f"Canvas文件: {canvas_file.name}",
                    confidence=0.7,
                    category="file"
                ))

        return suggestions

    def _get_history_suggestions(self, partial_input: str) -> List[CommandSuggestion]:
        """获取历史命令建议"""
        suggestions = []

        for cmd in self.command_history[-10:]:  # 最近10个命令
            if cmd.startswith(partial_input):
                suggestions.append(CommandSuggestion(
                    command=cmd,
                    description="历史命令",
                    confidence=0.6,
                    category="history"
                ))

        return suggestions

    def add_to_history(self, command: str):
        """添加命令到历史记录"""
        if command not in self.command_history:
            self.command_history.append(command)
            # 保持历史记录在合理范围内
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]

# ========== 命令注册器 ==========

class CommandRegistry:
    """命令注册器"""

    def __init__(self):
        self.commands: Dict[str, CommandMetadata] = {}
        self.handlers: Dict[str, Callable] = {}
        self.alias_map: Dict[str, str] = {}

    def register_command(self, metadata: CommandMetadata, handler: Callable) -> bool:
        """注册命令

        Args:
            metadata: 命令元数据
            handler: 处理函数

        Returns:
            bool: 注册是否成功

        Raises:
            ValueError: 当命令元数据无效时
            TypeError: 当处理器不可调用时
        """
        # 验证输入参数
        if not isinstance(metadata, CommandMetadata):
            raise ValueError("metadata必须是CommandMetadata类型")

        if not callable(handler):
            raise TypeError("handler必须是可调用对象")

        if not metadata.name or not isinstance(metadata.name, str):
            raise ValueError("命令名称不能为空且必须是字符串")

        if not isinstance(metadata.aliases, list):
            raise ValueError("别名必须是列表类型")

        # 验证命令名称和别名的有效性
        invalid_aliases = [alias for alias in metadata.aliases
                           if not alias or not isinstance(alias, str) or alias == metadata.name]
        if invalid_aliases:
            raise ValueError(f"无效的别名: {invalid_aliases}")

        try:
            # 检查命令是否已存在
            if metadata.name in self.commands:
                # 记录覆盖警告到日志而非直接打印
                self._log_warning(f"命令 '{metadata.name}' 已存在，将被覆盖")

            # 注册命令
            self.commands[metadata.name] = metadata
            self.handlers[metadata.name] = handler

            # 注册别名，检查冲突
            conflicting_aliases = []
            for alias in metadata.aliases:
                existing_command = self.alias_map.get(alias)
                if existing_command and existing_command != metadata.name:
                    conflicting_aliases.append((alias, existing_command))
                self.alias_map[alias] = metadata.name

            # 报告别名冲突
            if conflicting_aliases:
                self._log_warning(f"别名冲突: {conflicting_aliases}")

            self._log_info(f"成功注册命令: {metadata.name} (别名: {', '.join(metadata.aliases) if metadata.aliases else '无'})")
            return True

        except Exception as e:
            self._log_error(f"注册命令失败: {e}")
            return False

    def unregister_command(self, name: str) -> bool:
        """注销命令

        Args:
            name: 要注销的命令名称

        Returns:
            bool: 注销是否成功
        """
        try:
            if name not in self.commands:
                self._log_warning(f"尝试注销不存在的命令: {name}")
                return False

            # 移除别名映射
            metadata = self.commands[name]
            for alias in metadata.aliases:
                self.alias_map.pop(alias, None)

            # 移除命令
            self.commands.pop(name, None)
            self.handlers.pop(name, None)

            self._log_info(f"成功注销命令: {name}")
            return True

        except Exception as e:
            self._log_error(f"注销命令失败: {e}")
            return False

    def _log_info(self, message: str) -> None:
        """记录信息日志"""
        # 在实际实现中，这里应该使用日志库
        # 为了避免依赖，暂时使用print
        print(f"INFO: {message}")

    def _log_warning(self, message: str) -> None:
        """记录警告日志"""
        print(f"WARNING: {message}")

    def _log_error(self, message: str) -> None:
        """记录错误日志"""
        print(f"ERROR: {message}")

    def get_command_metadata(self, name: str) -> Optional[CommandMetadata]:
        """获取命令元数据"""
        # 检查是否是别名
        actual_name = self.alias_map.get(name, name)
        return self.commands.get(actual_name)

    def get_handler(self, name: str) -> Optional[Callable]:
        """获取命令处理器"""
        # 检查是否是别名
        actual_name = self.alias_map.get(name, name)
        return self.handlers.get(actual_name)

    def list_commands(self, category: str = None) -> List[CommandMetadata]:
        """列出命令"""
        commands = list(self.commands.values())

        if category:
            commands = [cmd for cmd in commands if cmd.category == category]

        return sorted(commands, key=lambda x: x.name)

    def load_from_config(self, config_path: str) -> bool:
        """从配置文件加载命令"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 这里只加载配置，实际的handler注册需要在其他地方进行
            print(f"成功加载命令配置: {config_path}")
            return True

        except Exception as e:
            print(f"加载命令配置失败: {e}")
            return False

# ========== 斜杠命令系统核心类 ==========

class SlashCommandSystem:
    """斜杠命令系统"""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """初始化斜杠命令系统

        Args:
            config_path: 命令配置文件路径
        """
        self.config_path = config_path
        self.command_registry = CommandRegistry()
        self.argument_parser = ArgumentParser()
        self.auto_completion = AutoCompletionSystem(self.command_registry)
        self.execution_history: List[CommandExecutionResult] = []

        # 创建必要的目录
        self._ensure_directories()

        # 加载配置
        self._load_configuration()

        # 初始化内置命令
        self._register_builtin_commands()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            Path("config"),
            Path("data"),
            Path("logs")
        ]

        for directory in directories:
            directory.mkdir(exist_ok=True)

    def _load_configuration(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            self.command_registry.load_from_config(self.config_path)
        else:
            print(f"配置文件不存在: {self.config_path}，使用默认配置")

    def _register_builtin_commands(self):
        """注册内置命令"""
        # 这些是基础的系统命令，其他的命令需要外部注册
        builtin_commands = [
            (CommandMetadata(
                name="help",
                aliases=["h", "?"],
                description="显示帮助信息",
                usage="/help [command_name]",
                examples=["/help", "/help canvas"],
                handler="handle_help_command",
                parameters=[
                    CommandParameter(
                        name="command_name",
                        type="string",
                        required=False,
                        description="要查看帮助的命令名称"
                    )
                ],
                category="system"
            ), self._handle_help_command),

            (CommandMetadata(
                name="commands",
                aliases=["list", "ls"],
                description="列出所有可用命令",
                usage="/commands [category]",
                examples=["/commands", "/commands system"],
                handler="handle_commands_command",
                parameters=[
                    CommandParameter(
                        name="category",
                        type="string",
                        required=False,
                        description="按类别筛选命令"
                    )
                ],
                category="system"
            ), self._handle_commands_command)
        ]

        for metadata, handler in builtin_commands:
            self.register_command(metadata, handler)

    def register_command(self, metadata: CommandMetadata, handler: Callable) -> bool:
        """注册命令"""
        return self.command_registry.register_command(metadata, handler)

    async def execute_command(self, command_line: str, user_context: Dict = None) -> CommandExecutionResult:
        """执行命令

        Args:
            command_line: 命令行文本
            user_context: 用户上下文

        Returns:
            CommandExecutionResult: 执行结果
        """
        # 创建执行上下文
        execution_id = f"exec-{uuid.uuid4().hex[:16]}"
        start_time = datetime.now()

        try:
            # 解析命令
            command_name, args = self._parse_command_line(command_line)
            if not command_name:
                raise InvalidParametersError("命令行格式错误")

            # 获取命令元数据
            metadata = self.command_registry.get_command_metadata(command_name)
            if not metadata:
                raise CommandNotFoundError(f"命令未找到: {command_name}")

            if not metadata.enabled:
                raise CommandNotFoundError(f"命令已禁用: {command_name}")

            # 解析参数
            parameters = self.argument_parser.parse_arguments(args, metadata.parameters)

            # 创建执行上下文
            context = CommandExecutionContext(
                execution_id=execution_id,
                command_name=command_name,
                raw_command=command_line,
                parameters=parameters,
                timestamp=start_time,
                user_id=user_context.get('user_id', 'default') if user_context else 'default',
                session_id=user_context.get('session_id', 'default') if user_context else 'default'
            )

            # 获取处理器
            handler = self.command_registry.get_handler(command_name)
            if not handler:
                raise HandlerNotFoundError(f"处理器未找到: {command_name}")

            # 执行命令（带超时）
            result = await asyncio.wait_for(
                self._execute_handler(handler, context),
                timeout=metadata.timeout
            )

            # 记录成功结果
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            execution_result = CommandExecutionResult(
                execution_id=execution_id,
                status=STATUS_SUCCESS,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                output=result,
                suggestions=self._generate_suggestions(metadata, result)
            )

            # 添加到历史记录
            self.auto_completion.add_to_history(command_line)
            self.execution_history.append(execution_result)

            return execution_result

        except asyncio.TimeoutError:
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            execution_result = CommandExecutionResult(
                execution_id=execution_id,
                status=STATUS_TIMEOUT,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                error_message="命令执行超时",
                error_type=ERROR_TIMEOUT,
                suggestions=["检查命令是否陷入无限循环", "增加超时时间", "简化命令参数"]
            )

            self.execution_history.append(execution_result)
            return execution_result

        except Exception as e:
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            error_type = self._classify_error(e)
            error_message = str(e)
            suggestions = self._generate_error_suggestions(e, metadata if 'metadata' in locals() else None)

            execution_result = CommandExecutionResult(
                execution_id=execution_id,
                status=STATUS_ERROR,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                error_message=error_message,
                error_type=error_type,
                suggestions=suggestions
            )

            self.execution_history.append(execution_result)
            return execution_result

    def _parse_command_line(self, command_line: str) -> Tuple[str, List[str]]:
        """解析命令行"""
        command_line = command_line.strip()

        if not command_line.startswith('/'):
            raise InvalidParametersError("命令必须以 / 开头")

        parts = command_line[1:].split()
        if not parts:
            raise InvalidParametersError("命令不能为空")

        command_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        return command_name, args

    async def _execute_handler(self, handler: Callable, context: CommandExecutionContext) -> Dict:
        """执行处理器"""
        try:
            # 检查处理器是否是协程函数
            if asyncio.iscoroutinefunction(handler):
                result = await handler(context)
            else:
                result = handler(context)

            return result if isinstance(result, dict) else {"result": result}

        except Exception as e:
            raise SlashCommandError(f"处理器执行失败: {e}")

    def _classify_error(self, error: Exception) -> str:
        """分类错误类型"""
        if isinstance(error, CommandNotFoundError):
            return ERROR_COMMAND_NOT_FOUND
        elif isinstance(error, InvalidParametersError):
            return ERROR_INVALID_PARAMETERS
        elif isinstance(error, HandlerNotFoundError):
            return ERROR_HANDLER_NOT_FOUND
        elif isinstance(error, CommandTimeoutError):
            return ERROR_TIMEOUT
        else:
            return ERROR_EXECUTION_FAILED

    def _generate_error_suggestions(self, error: Exception, metadata: CommandMetadata = None) -> List[str]:
        """生成错误建议"""
        suggestions = []

        if isinstance(error, CommandNotFoundError):
            # 找相似的命令
            if metadata:
                suggestions.append(f"您是否想使用: /{metadata.name}")

            suggestions.extend([
                "使用 /commands 查看所有可用命令",
                "使用 /help 查看命令帮助"
            ])

        elif isinstance(error, InvalidParametersError):
            if metadata:
                suggestions.append(f"正确用法: {metadata.usage}")
                suggestions.append(f"使用 /help {metadata.name} 查看详细帮助")

        elif isinstance(error, HandlerNotFoundError):
            suggestions.append("该命令的处理器未正确注册")
            suggestions.append("请检查系统配置")

        return suggestions

    def _generate_suggestions(self, metadata: CommandMetadata, result: Dict) -> List[str]:
        """生成执行建议"""
        suggestions = []

        # 基于命令类型的建议
        if metadata.category == "canvas":
            suggestions.extend([
                "使用 /canvas-status 检查系统状态",
                "使用 /canvas-help 获取更多帮助"
            ])

        return suggestions

    def get_command_suggestions(self, partial_input: str, context: Dict = None) -> List[CommandSuggestion]:
        """获取命令建议"""
        return self.auto_completion.get_suggestions(partial_input, context)

    def validate_command(self, command_line: str) -> Dict:
        """验证命令"""
        try:
            command_name, args = self._parse_command_line(command_line)
            metadata = self.command_registry.get_command_metadata(command_name)

            if not metadata:
                return {
                    "valid": False,
                    "error": f"命令未找到: {command_name}",
                    "suggestions": self.get_command_suggestions(command_line)
                }

            # 尝试解析参数
            try:
                parameters = self.argument_parser.parse_arguments(args, metadata.parameters)
                return {
                    "valid": True,
                    "command": command_name,
                    "parameters": parameters,
                    "metadata": asdict(metadata)
                }
            except Exception as e:
                return {
                    "valid": False,
                    "error": str(e),
                    "command": command_name,
                    "suggestions": [f"使用 /help {command_name} 查看正确用法"]
                }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "suggestions": ["使用 /help 查看基本用法"]
            }

    def generate_help_text(self, command_name: str = None) -> str:
        """生成帮助文本"""
        if command_name:
            # 特定命令的帮助
            metadata = self.command_registry.get_command_metadata(command_name)
            if not metadata:
                return f"命令未找到: {command_name}\n使用 /commands 查看所有可用命令"

            help_text = f"""
# {metadata.name}

**描述**: {metadata.description}

**用法**: {metadata.usage}

**别名**: {', '.join(metadata.aliases)}

**参数**:
"""

            if metadata.parameters:
                for param in metadata.parameters:
                    required_str = "必需" if param.required else f"可选 (默认: {param.default})"
                    help_text += f"  --{param.name} ({param.type}): {param.description} - {required_str}\n"
            else:
                help_text += "  无参数\n"

            help_text += f"""
**示例**:
"""
            for example in metadata.examples:
                help_text += f"  {example}\n"

            return help_text
        else:
            # 所有命令的帮助
            commands = self.command_registry.list_commands()

            help_text = """
# Canvas学习系统 - 斜杠命令帮助

## 可用命令

"""

            # 按类别分组
            categories = {}
            for cmd in commands:
                if cmd.category not in categories:
                    categories[cmd.category] = []
                categories[cmd.category].append(cmd)

            for category, cmds in categories.items():
                help_text += f"### {category.title()}\n\n"
                for cmd in cmds:
                    aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                    help_text += f"**/{cmd.name}**{aliases}: {cmd.description}\n"
                    help_text += f"  用法: {cmd.usage}\n\n"

            help_text += """
## 使用技巧

1. 输入 `/` 后按 Tab 键可以查看命令补全
2. 使用 `--help` 参数查看命令详细帮助
3. 命令支持别名，可以使用更简短的形式
4. 系统会保存命令历史，可以使用上下键浏览

## 获取帮助

- `/help [command_name]` - 查看特定命令的帮助
- `/commands [category]` - 列出命令
- `/help` - 显示此帮助信息
"""

            return help_text

    # ========== 内置命令处理器 ==========

    async def _handle_help_command(self, context: CommandExecutionContext) -> Dict:
        """处理帮助命令"""
        command_name = context.parameters.get('command_name')

        if command_name:
            help_text = self.generate_help_text(command_name)
        else:
            help_text = self.generate_help_text()

        return {
            "type": "help",
            "content": help_text,
            "format": "markdown"
        }

    async def _handle_commands_command(self, context: CommandExecutionContext) -> Dict:
        """处理命令列表命令"""
        category = context.parameters.get('category')
        commands = self.command_registry.list_commands(category)

        result = {
            "type": "command_list",
            "commands": []
        }

        for cmd in commands:
            result["commands"].append({
                "name": cmd.name,
                "aliases": cmd.aliases,
                "description": cmd.description,
                "usage": cmd.usage,
                "category": cmd.category,
                "enabled": cmd.enabled
            })

        return result

# ========== 系统初始化 ==========

# 全局斜杠命令系统实例
_slash_command_system: Optional[SlashCommandSystem] = None

def get_slash_command_system() -> SlashCommandSystem:
    """获取全局斜杠命令系统实例"""
    global _slash_command_system
    if _slash_command_system is None:
        _slash_command_system = SlashCommandSystem()
    return _slash_command_system

def initialize_slash_command_system(config_path: str = None) -> SlashCommandSystem:
    """初始化斜杠命令系统"""
    global _slash_command_system
    _slash_command_system = SlashCommandSystem(config_path or DEFAULT_CONFIG_PATH)
    return _slash_command_system

# ========== 便捷函数 ==========

async def execute_slash_command(command_line: str, user_context: Dict = None) -> CommandExecutionResult:
    """执行斜杠命令（便捷函数）"""
    system = get_slash_command_system()
    return await system.execute_command(command_line, user_context)

def get_command_suggestions(partial_input: str, context: Dict = None) -> List[CommandSuggestion]:
    """获取命令建议（便捷函数）"""
    system = get_slash_command_system()
    return system.get_command_suggestions(partial_input, context)

def validate_slash_command(command_line: str) -> Dict:
    """验证斜杠命令（便捷函数）"""
    system = get_slash_command_system()
    return system.validate_command(command_line)