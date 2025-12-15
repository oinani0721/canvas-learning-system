"""
错误处理和恢复管理器 - Canvas学习系统

负责并行Agent处理的错误处理、恢复和诊断，包括：
- Agent错误隔离机制
- 智能自动重试和恢复逻辑
- 失败任务处理策略
- 错误报告、分析和诊断

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
Story: 8.14 (Task 4)
"""

import asyncio
import time
import uuid
import traceback
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import re
import random
from collections import defaultdict, Counter
import statistics


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 轻微错误，不影响系统运行
    MEDIUM = "medium"     # 中等错误，影响部分功能
    HIGH = "high"         # 严重错误，影响主要功能
    CRITICAL = "critical" # 致命错误，可能导致系统崩溃


class ErrorCategory(Enum):
    """错误分类"""
    TIMEOUT = "timeout"                 # 超时错误
    NETWORK = "network"                 # 网络错误
    RESOURCE = "resource"               # 资源错误
    AUTHENTICATION = "authentication"   # 认证错误
    PERMISSION = "permission"           # 权限错误
    VALIDATION = "validation"           # 数据验证错误
    RUNTIME = "runtime"                 # 运行时错误
    CONFIGURATION = "configuration"     # 配置错误
    DEPENDENCY = "dependency"           # 依赖错误
    AGENT_ERROR = "agent_error"         # Agent特定错误
    SYSTEM_ERROR = "system_error"       # 系统错误
    UNKNOWN = "unknown"                 # 未知错误


class RecoveryStrategy(Enum):
    """恢复策略"""
    NONE = "none"                       # 不恢复
    RETRY = "retry"                     # 重试
    FALLBACK = "fallback"               # 降级处理
    SKIP = "skip"                       # 跳过任务
    MANUAL = "manual"                   # 手动处理
    ESCALATE = "escalate"               # 升级处理


class ErrorIsolationLevel(Enum):
    """错误隔离级别"""
    TASK = "task"           # 任务级隔离
    AGENT = "agent"         # Agent级隔离
    WORKER = "worker"       # 工作节点级隔离
    SYSTEM = "system"       # 系统级隔离


@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str = field(default_factory=lambda: f"error-{uuid.uuid4().hex[:16]}")
    task_id: str = ""
    execution_id: str = ""
    agent_name: str = ""
    worker_id: str = ""

    # 错误信息
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    error_type: str = ""
    error_message: str = ""
    error_traceback: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM

    # 时间信息
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3

    # 恢复信息
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.NONE
    recovery_successful: bool = False
    recovery_time: Optional[float] = None
    recovery_attempts: int = 0

    # 隔离信息
    isolation_level: ErrorIsolationLevel = ErrorIsolationLevel.TASK
    isolated_components: List[str] = field(default_factory=list)

    # 上下文信息
    context_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data["error_category"] = self.error_category.value
        data["severity"] = self.severity.value
        data["recovery_strategy"] = self.recovery_strategy.value
        data["isolation_level"] = self.isolation_level.value
        data["timestamp_iso"] = datetime.fromtimestamp(self.timestamp).isoformat()
        if self.recovery_time:
            data["recovery_time_iso"] = datetime.fromtimestamp(self.recovery_time).isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorRecord':
        """从字典创建错误记录"""
        # 处理枚举类型
        if "error_category" in data:
            data["error_category"] = ErrorCategory(data["error_category"])
        if "severity" in data:
            data["severity"] = ErrorSeverity(data["severity"])
        if "recovery_strategy" in data:
            data["recovery_strategy"] = RecoveryStrategy(data["recovery_strategy"])
        if "isolation_level" in data:
            data["isolation_level"] = ErrorIsolationLevel(data["isolation_level"])

        return cls(**data)


@dataclass
class RetryPolicy:
    """重试策略"""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retry_on_exceptions: List[str] = field(default_factory=list)
    stop_on_exceptions: List[str] = field(default_factory=list)

    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟

        Args:
            attempt: 重试次数

        Returns:
            float: 延迟时间（秒）
        """
        delay = self.base_delay_seconds * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay_seconds)

        # 添加抖动
        if self.jitter:
            delay *= (0.5 + random.random() * 0.5)

        return delay

    def should_retry(self, exception_type: str) -> bool:
        """判断是否应该重试

        Args:
            exception_type: 异常类型

        Returns:
            bool: 是否应该重试
        """
        # 检查停止重试的异常
        if exception_type in self.stop_on_exceptions:
            return False

        # 检查重试的异常
        if not self.retry_on_exceptions:
            return True  # 默认重试所有异常

        return exception_type in self.retry_on_exceptions


@dataclass
class FallbackStrategy:
    """降级策略"""
    strategy_name: str
    fallback_agents: List[str] = field(default_factory=list)
    fallback_config: Dict[str, Any] = field(default_factory=dict)
    quality_threshold: float = 0.8
    max_fallback_attempts: int = 2

    def is_applicable(self, agent_name: str, error_record: ErrorRecord) -> bool:
        """判断策略是否适用

        Args:
            agent_name: Agent名称
            error_record: 错误记录

        Returns:
            bool: 是否适用
        """
        return agent_name in self.fallback_agents


class ErrorAnalyzer:
    """错误分析器"""

    def __init__(self):
        """初始化错误分析器"""
        self.error_patterns = {
            ErrorCategory.TIMEOUT: [
                r"timeout",
                r"timed out",
                r"time.*out",
                r"deadline"
            ],
            ErrorCategory.NETWORK: [
                r"connection",
                r"network",
                r"socket",
                r"http.*error",
                r"request.*failed"
            ],
            ErrorCategory.RESOURCE: [
                r"memory",
                r"cpu",
                r"disk",
                r"resource.*limit",
                r"out of"
            ],
            ErrorCategory.AUTHENTICATION: [
                r"auth",
                r"login",
                r"credential",
                r"unauthorized",
                r"forbidden"
            ],
            ErrorCategory.PERMISSION: [
                r"permission",
                r"access denied",
                r"not allowed",
                r"forbidden"
            ],
            ErrorCategory.VALIDATION: [
                r"validation",
                r"invalid.*input",
                r"malformed",
                r"bad.*request"
            ]
        }

    def categorize_error(self, error_message: str, exception_type: str) -> ErrorCategory:
        """对错误进行分类

        Args:
            error_message: 错误消息
            exception_type: 异常类型

        Returns:
            ErrorCategory: 错误分类
        """
        error_text = (error_message + " " + exception_type).lower()

        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_text):
                    return category

        # 基于异常类型的特殊判断
        if "timeout" in exception_type.lower():
            return ErrorCategory.TIMEOUT
        elif "connection" in exception_type.lower():
            return ErrorCategory.NETWORK
        elif "memory" in exception_type.lower():
            return ErrorCategory.RESOURCE

        return ErrorCategory.UNKNOWN

    def determine_severity(self, category: ErrorCategory, exception_type: str) -> ErrorSeverity:
        """确定错误严重程度

        Args:
            category: 错误分类
            exception_type: 异常类型

        Returns:
            ErrorSeverity: 错误严重程度
        """
        high_severity_exceptions = [
            "systemexit", "keyboardinterrupt", "memoryerror",
            "systemerror", "oserror"
        ]

        medium_severity_exceptions = [
            "timeouterror", "connectionerror", "httperror",
            "valueerror", "keyerror"
        ]

        exception_type_lower = exception_type.lower()

        if any(exc in exception_type_lower for exc in high_severity_exceptions):
            return ErrorSeverity.HIGH if category != ErrorCategory.CONFIGURATION else ErrorSeverity.CRITICAL
        elif any(exc in exception_type_lower for exc in medium_severity_exceptions):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def analyze_error_trends(self, error_records: List[ErrorRecord]) -> Dict[str, Any]:
        """分析错误趋势

        Args:
            error_records: 错误记录列表

        Returns:
            Dict: 错误趋势分析
        """
        if not error_records:
            return {}

        # 按时间分组分析
        current_time = time.time()
        time_windows = {
            "last_hour": current_time - 3600,
            "last_6hours": current_time - 21600,
            "last_24hours": current_time - 86400
        }

        trends = {}
        for window_name, window_start in time_windows.items():
            recent_errors = [
                error for error in error_records
                if error.timestamp >= window_start
            ]

            trends[window_name] = {
                "total_errors": len(recent_errors),
                "category_distribution": Counter(e.error_category for e in recent_errors),
                "severity_distribution": Counter(e.severity for e in recent_errors),
                "agent_distribution": Counter(e.agent_name for e in recent_errors),
                "recovery_success_rate": (
                    sum(1 for e in recent_errors if e.recovery_successful) /
                    len(recent_errors) if recent_errors else 0
                )
            }

        # 错误率趋势
        error_times = [error.timestamp for error in error_records]
        if len(error_times) > 1:
            time_span = max(error_times) - min(error_times)
            trends["error_rate"] = len(error_times) / max(time_span, 1)

        # 最常见的错误模式
        error_messages = [error.error_message for error in error_records]
        if error_messages:
            trends["common_error_patterns"] = Counter(
                self._extract_error_pattern(msg) for msg in error_messages
            ).most_common(10)

        return trends

    def _extract_error_pattern(self, error_message: str) -> str:
        """提取错误模式

        Args:
            error_message: 错误消息

        Returns:
            str: 错误模式
        """
        # 移除具体数值、ID等，保留错误模式
        pattern = re.sub(r'\d+', '<NUM>', error_message.lower())
        pattern = re.sub(r'[a-f0-9]{8,}', '<ID>', pattern)
        pattern = re.sub(r'/[^\s]+', '<PATH>', pattern)
        pattern = re.sub(r'["\'][^"\']*["\']', '<STRING>', pattern)
        return pattern.strip()


class ErrorHandlingManager:
    """错误处理管理器主类

    提供完整的并行Agent错误处理和恢复功能，
    包括错误分类、隔离、重试、降级和诊断。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化错误处理管理器

        Args:
            config: 错误处理配置
        """
        self.config = config
        self.continue_on_error = config.get("continue_on_error", True)
        self.error_isolation = config.get("error_isolation", True)
        self.fallback_strategy = config.get("fallback_strategy", "retry")

        # 组件
        self.error_analyzer = ErrorAnalyzer()

        # 错误记录存储
        self.error_records: Dict[str, ErrorRecord] = {}
        self.active_errors: Dict[str, ErrorRecord] = {}

        # 重试策略
        self.default_retry_policy = RetryPolicy(
            max_attempts=config.get("task_retry_attempts", 3),
            base_delay_seconds=config.get("task_retry_delay_seconds", 5),
            backoff_factor=config.get("task_retry_backoff_factor", 2.0)
        )
        self.retry_policies: Dict[str, RetryPolicy] = {}

        # 降级策略
        self.fallback_strategies: Dict[str, FallbackStrategy] = {}

        # 隔离级别配置
        self.isolation_rules: Dict[ErrorCategory, ErrorIsolationLevel] = {
            ErrorCategory.SYSTEM_ERROR: ErrorIsolationLevel.SYSTEM,
            ErrorCategory.RESOURCE: ErrorIsolationLevel.WORKER,
            ErrorCategory.AGENT_ERROR: ErrorIsolationLevel.AGENT,
            ErrorCategory.RUNTIME: ErrorIsolationLevel.TASK,
            ErrorCategory.NETWORK: ErrorIsolationLevel.TASK,
            ErrorCategory.TIMEOUT: ErrorIsolationLevel.TASK
        }

        # 错误统计
        self.error_statistics = {
            "total_errors": 0,
            "recovered_errors": 0,
            "escalated_errors": 0,
            "category_counts": defaultdict(int),
            "severity_counts": defaultdict(int),
            "agent_error_counts": defaultdict(int)
        }

        # 回调函数
        self.error_callbacks: List[Callable[[ErrorRecord], None]] = []
        self.recovery_callbacks: List[Callable[[ErrorRecord], bool]] = []

        # 日志设置
        self._setup_logging()

    def _setup_logging(self) -> None:
        """设置错误日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        self.error_log = logging.getLogger("error_handler")
        self.error_log.setLevel(logging.INFO)

        # 文件处理器
        file_handler = logging.FileHandler(
            log_dir / "error_handler.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        self.error_log.addHandler(file_handler)

    def register_retry_policy(self, agent_name: str, policy: RetryPolicy) -> None:
        """注册Agent的重试策略

        Args:
            agent_name: Agent名称
            policy: 重试策略
        """
        self.retry_policies[agent_name] = policy

    def register_fallback_strategy(self, agent_name: str, strategy: FallbackStrategy) -> None:
        """注册Agent的降级策略

        Args:
            agent_name: Agent名称
            strategy: 降级策略
        """
        self.fallback_strategies[agent_name] = strategy

    def add_error_callback(self, callback: Callable[[ErrorRecord], None]) -> None:
        """添加错误回调函数

        Args:
            callback: 错误回调函数
        """
        self.error_callbacks.append(callback)

    def add_recovery_callback(self, callback: Callable[[ErrorRecord], bool]) -> None:
        """添加恢复回调函数

        Args:
            callback: 恢复回调函数（返回恢复是否成功）
        """
        self.recovery_callbacks.append(callback)

    async def handle_error(self,
                          task_id: str,
                          execution_id: str,
                          agent_name: str,
                          worker_id: str,
                          exception: Exception,
                          context_data: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """处理Agent执行错误

        Args:
            task_id: 任务ID
            execution_id: 执行ID
            agent_name: Agent名称
            worker_id: 工作节点ID
            exception: 异常对象
            context_data: 上下文数据

        Returns:
            ErrorRecord: 错误记录
        """
        # 创建错误记录
        error_record = ErrorRecord(
            task_id=task_id,
            execution_id=execution_id,
            agent_name=agent_name,
            worker_id=worker_id,
            error_type=type(exception).__name__,
            error_message=str(exception),
            error_traceback=traceback.format_exc(),
            context_data=context_data or {}
        )

        # 分析和分类错误
        error_record.error_category = self.error_analyzer.categorize_error(
            error_record.error_message,
            error_record.error_type
        )
        error_record.severity = self.error_analyzer.determine_severity(
            error_record.error_category,
            error_record.error_type
        )

        # 确定隔离级别
        if self.error_isolation:
            error_record.isolation_level = self.isolation_rules.get(
                error_record.error_category,
                ErrorIsolationLevel.TASK
            )

        # 执行错误隔离
        await self._isolate_error(error_record)

        # 记录错误
        self.error_records[error_record.error_id] = error_record
        self.active_errors[error_record.error_id] = error_record

        # 更新统计
        self._update_error_statistics(error_record, "error")

        # 触发错误回调
        for callback in self.error_callbacks:
            try:
                callback(error_record)
            except Exception as e:
                self.error_log.error(f"错误回调执行失败: {e}")

        # 记录日志
        self.error_log.error(
            f"Agent错误 [{agent_name}]: {error_record.error_type} - "
            f"{error_record.error_message} (严重程度: {error_record.severity.value})"
        )

        # 尝试恢复
        recovery_success = await self._attempt_recovery(error_record)
        error_record.recovery_successful = recovery_success
        error_record.recovery_time = time.time()

        # 更新统计
        if recovery_success:
            self._update_error_statistics(error_record, "recovery")

        # 从活跃错误中移除
        if error_record.error_id in self.active_errors:
            del self.active_errors[error_record.error_id]

        return error_record

    async def _isolate_error(self, error_record: ErrorRecord) -> None:
        """执行错误隔离

        Args:
            error_record: 错误记录
        """
        isolation_components = []

        if error_record.isolation_level == ErrorIsolationLevel.TASK:
            isolation_components.append(f"task:{error_record.task_id}")
        elif error_record.isolation_level == ErrorIsolationLevel.AGENT:
            isolation_components.append(f"agent:{error_record.agent_name}")
        elif error_record.isolation_level == ErrorIsolationLevel.WORKER:
            isolation_components.append(f"worker:{error_record.worker_id}")
        elif error_record.isolation_level == ErrorIsolationLevel.SYSTEM:
            isolation_components.append("system:all_workers")

        error_record.isolated_components = isolation_components

        self.error_log.info(
            f"错误隔离 [{error_record.error_id}]: "
            f"级别={error_record.isolation_level.value}, "
            f"组件={isolation_components}"
        )

    async def _attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """尝试错误恢复

        Args:
            error_record: 错误记录

        Returns:
            bool: 恢复是否成功
        """
        # 获取重试策略
        retry_policy = self.retry_policies.get(
            error_record.agent_name,
            self.default_retry_policy
        )

        # 检查是否应该重试
        if (error_record.retry_count < retry_policy.max_attempts and
            retry_policy.should_retry(error_record.error_type)):

            error_record.recovery_strategy = RecoveryStrategy.RETRY

            # 计算重试延迟
            delay = retry_policy.calculate_delay(error_record.retry_count + 1)
            await asyncio.sleep(delay)

            # 更新重试计数
            error_record.retry_count += 1
            error_record.recovery_attempts += 1

            self.error_log.info(
                f"尝试重试 [{error_record.error_id}]: "
                f"第{error_record.retry_count}次重试，延迟{delay:.1f}秒"
            )

            # 触发恢复回调（这里应该实际重试任务）
            recovery_success = True
            for callback in self.recovery_callbacks:
                try:
                    success = callback(error_record)
                    if not success:
                        recovery_success = False
                except Exception as e:
                    self.error_log.error(f"恢复回调执行失败: {e}")
                    recovery_success = False

            return recovery_success

        # 尝试降级策略
        fallback_strategy = self.fallback_strategies.get(error_record.agent_name)
        if fallback_strategy and fallback_strategy.is_applicable(error_record.agent_name, error_record):
            return await self._attempt_fallback(error_record, fallback_strategy)

        # 无法自动恢复
        error_record.recovery_strategy = RecoveryStrategy.MANUAL
        self._update_error_statistics(error_record, "escalation")

        return False

    async def _attempt_fallback(self, error_record: ErrorRecord, fallback: FallbackStrategy) -> bool:
        """尝试降级恢复

        Args:
            error_record: 错误记录
            fallback: 降级策略

        Returns:
            bool: 降级是否成功
        """
        if error_record.recovery_attempts >= fallback.max_fallback_attempts:
            return False

        error_record.recovery_strategy = RecoveryStrategy.FALLBACK
        error_record.recovery_attempts += 1

        self.error_log.info(
            f"尝试降级恢复 [{error_record.error_id}]: "
            f"策略={fallback.strategy_name}, 降级Agent={fallback.fallback_agents}"
        )

        # 这里应该实现实际的降级逻辑
        # 例如：切换到备用Agent，使用简化算法等

        return True  # 简化实现

    def _update_error_statistics(self, error_record: ErrorRecord, action: str) -> None:
        """更新错误统计

        Args:
            error_record: 错误记录
            action: 操作类型
        """
        if action == "error":
            self.error_statistics["total_errors"] += 1
            self.error_statistics["category_counts"][error_record.error_category.value] += 1
            self.error_statistics["severity_counts"][error_record.severity.value] += 1
            self.error_statistics["agent_error_counts"][error_record.agent_name] += 1

        elif action == "recovery":
            self.error_statistics["recovered_errors"] += 1

        elif action == "escalation":
            self.error_statistics["escalated_errors"] += 1

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息

        Returns:
            Dict: 错误统计信息
        """
        total_errors = self.error_statistics["total_errors"]
        recovered_errors = self.error_statistics["recovered_errors"]

        recovery_rate = recovered_errors / total_errors if total_errors > 0 else 0

        return {
            **self.error_statistics,
            "recovery_rate": recovery_rate,
            "active_errors_count": len(self.active_errors),
            "total_error_records": len(self.error_records)
        }

    def get_error_trends(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """获取错误趋势分析

        Args:
            time_window_hours: 时间窗口（小时）

        Returns:
            Dict: 错误趋势分析
        """
        current_time = time.time()
        window_start = current_time - (time_window_hours * 3600)

        recent_errors = [
            error for error in self.error_records.values()
            if error.timestamp >= window_start
        ]

        return self.error_analyzer.analyze_error_trends(recent_errors)

    def get_active_errors(self) -> List[Dict[str, Any]]:
        """获取活跃错误列表

        Returns:
            List[Dict]: 活跃错误列表
        """
        return [error.to_dict() for error in self.active_errors.values()]

    def get_error_details(self, error_id: str) -> Optional[Dict[str, Any]]:
        """获取错误详细信息

        Args:
            error_id: 错误ID

        Returns:
            Optional[Dict]: 错误详细信息
        """
        error_record = self.error_records.get(error_id)
        return error_record.to_dict() if error_record else None

    def generate_error_report(self, include_recommendations: bool = True) -> Dict[str, Any]:
        """生成错误分析报告

        Args:
            include_recommendations: 是否包含改进建议

        Returns:
            Dict: 错误分析报告
        """
        report = {
            "report_id": f"error-report-{int(time.time())}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "statistics": self.get_error_statistics(),
            "trends": self.get_error_trends(),
            "active_errors": self.get_active_errors(),
            "recommendations": []
        }

        if include_recommendations:
            report["recommendations"] = self._generate_error_recommendations()

        return report

    def _generate_error_recommendations(self) -> List[str]:
        """生成错误处理改进建议

        Returns:
            List[str]: 改进建议列表
        """
        recommendations = []
        stats = self.error_statistics

        # 基于错误率的建议
        if stats["total_errors"] > 0:
            recovery_rate = stats["recovered_errors"] / stats["total_errors"]
            if recovery_rate < 0.8:
                recommendations.append(
                    "错误恢复率较低，建议检查重试策略和降级机制的配置"
                )

        # 基于错误分类的建议
        category_counts = stats["category_counts"]
        if category_counts.get("timeout", 0) > stats["total_errors"] * 0.3:
            recommendations.append(
                "超时错误占比较高，建议增加任务超时时间或优化Agent性能"
            )

        if category_counts.get("resource", 0) > stats["total_errors"] * 0.2:
            recommendations.append(
                "资源错误占比较高，建议优化资源分配或增加系统资源"
            )

        # 基于Agent错误分布的建议
        agent_counts = stats["agent_error_counts"]
        if agent_counts:
            erroriest_agent = max(agent_counts.items(), key=lambda x: x[1])
            if erroriest_agent[1] > stats["total_errors"] * 0.4:
                recommendations.append(
                    f"Agent '{erroriest_agent[0]}' 错误率较高，"
                    f"建议检查其配置或实现逻辑"
                )

        # 基于活跃错误的建议
        if len(self.active_errors) > 10:
            recommendations.append(
                "活跃错误数量较多，建议及时处理或增加自动恢复能力"
            )

        return recommendations if recommendations else ["错误处理状态良好，无特殊建议"]

    async def export_error_data(self, file_path: str) -> bool:
        """导出错误数据

        Args:
            file_path: 导出文件路径

        Returns:
            bool: 导出是否成功
        """
        try:
            data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "error_statistics": self.get_error_statistics(),
                "error_records": {
                    error_id: error.to_dict()
                    for error_id, error in self.error_records.items()
                },
                "active_errors": {
                    error_id: error.to_dict()
                    for error_id, error in self.active_errors.items()
                },
                "retry_policies": {
                    agent_name: asdict(policy)
                    for agent_name, policy in self.retry_policies.items()
                },
                "fallback_strategies": {
                    agent_name: asdict(strategy)
                    for agent_name, strategy in self.fallback_strategies.items()
                }
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            self.error_log.error(f"导出错误数据失败: {e}")
            return False

    async def clear_error_history(self, older_than_hours: int = 168) -> int:
        """清理历史错误记录

        Args:
            older_than_hours: 清理多少小时前的记录（默认7天）

        Returns:
            int: 清理的记录数量
        """
        cutoff_time = time.time() - (older_than_hours * 3600)

        old_error_ids = [
            error_id for error_id, error in self.error_records.items()
            if error.timestamp < cutoff_time and error_id not in self.active_errors
        ]

        for error_id in old_error_ids:
            del self.error_records[error_id]

        return len(old_error_ids)