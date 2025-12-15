"""
错误隔离管理器 (Error Isolation Manager)

该模块负责实现错误隔离机制，确保单个Agent实例失败时不会影响整体处理任务。
"""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import threading
import weakref

# 导入类型定义
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 轻微错误，不影响主要功能
    MEDIUM = "medium"     # 中等错误，影响部分功能
    HIGH = "high"         # 严重错误，影响核心功能
    CRITICAL = "critical" # 致命错误，系统无法继续


class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "network"           # 网络相关错误
    API_LIMIT = "api_limit"       # API限制错误
    INSTANCE_FAILURE = "instance_failure"  # 实例失败
    CANVAS_CORRUPTION = "canvas_corruption"  # Canvas文件损坏
    MEMORY_OVERFLOW = "memory_overflow"      # 内存溢出
    TIMEOUT = "timeout"           # 超时错误
    VALIDATION = "validation"     # 数据验证错误
    SYSTEM = "system"             # 系统级错误


class IsolationLevel(Enum):
    """隔离级别"""
    NONE = "none"               # 不隔离
    TASK = "task"               # 任务级隔离
    INSTANCE = "instance"       # 实例级隔离
    SESSION = "session"         # 会话级隔离


@dataclass
class ErrorInfo:
    """错误信息数据模型"""
    error_id: str
    error_code: str
    error_message: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    instance_id: Optional[str] = None
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_message: Optional[str] = None


@dataclass
class InstanceInfo:
    """实例信息"""
    instance_id: str
    instance_type: str  # "agent", "worker", "processor"
    status: str  # "active", "quarantined", "terminated"
    created_at: datetime
    last_heartbeat: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    active_tasks: Set[str] = field(default_factory=set)
    error_count: int = 0
    total_tasks_processed: int = 0


@dataclass
class QuarantineRecord:
    """隔离记录"""
    instance_id: str
    quarantine_time: datetime
    reason: str
    policy_id: str
    auto_recovery_time: Optional[datetime] = None
    is_active: bool = True
    recovery_attempts: int = 0


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    instance_id: str
    check_time: datetime
    is_healthy: bool
    response_time: float  # 毫秒
    error_message: Optional[str] = None
    memory_usage: Optional[float] = None  # MB
    cpu_usage: Optional[float] = None     # 百分比
    active_tasks: int = 0
    error_count: int = 0


@dataclass
class FailurePattern:
    """故障模式分析"""
    pattern_id: str
    error_type: ErrorCategory
    frequency: int  # 出现频率
    time_pattern: str  # "random", "periodic", "burst"
    affected_instances: List[str]
    first_occurrence: datetime
    last_occurrence: datetime
    auto_recovery_possible: bool = False
    recommended_action: Optional[str] = None


@dataclass
class IsolationPolicy:
    """隔离策略"""
    policy_id: str
    error_category: ErrorCategory
    isolation_level: IsolationLevel
    max_error_rate: float = 0.1  # 错误率阈值
    quarantine_time: int = 300   # 隔离时间(秒)
    auto_recovery: bool = True
    notification_required: bool = True
    propagation_blocked: bool = True  # 是否阻止错误传播


@dataclass
class ErrorPropagationRule:
    """错误传播规则"""
    rule_id: str
    source_error_category: ErrorCategory
    target_categories: List[ErrorCategory]
    block_propagation: bool = True
    max_propagation_depth: int = 3
    time_window: int = 60  # 时间窗口(秒)


@dataclass
class ErrorPropagationEvent:
    """错误传播事件"""
    event_id: str
    source_error: ErrorInfo
    target_instance_id: Optional[str]
    propagation_time: datetime
    propagation_depth: int
    blocked: bool
    block_reason: Optional[str] = None


class ErrorIsolationManager:
    """
    错误隔离管理器

    负责实现Agent实例级别的错误隔离，确保单个失败不影响其他实例。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化错误隔离管理器

        Args:
            config: 配置字典，包含隔离策略、监控参数等
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 内部状态
        self._quarantined_instances: Set[str] = set()
        self._instance_health: Dict[str, HealthCheckResult] = {}
        self._error_history: List[ErrorInfo] = []
        self._failure_patterns: Dict[str, FailurePattern] = {}
        self._isolation_policies: Dict[str, IsolationPolicy] = {}
        self._registered_instances: Dict[str, InstanceInfo] = {}
        self._quarantine_records: Dict[str, QuarantineRecord] = {}
        self._propagation_rules: Dict[str, ErrorPropagationRule] = {}
        self._propagation_events: List[ErrorPropagationEvent] = []
        self._active_propagations: Dict[str, List[str]] = {}  # 错误ID -> 受影响的实例列表

        # 线程安全锁
        self._lock = threading.RLock()

        # 监控和清理线程
        self._monitoring_active = False
        self._cleanup_thread: Optional[threading.Thread] = None
        self._monitoring_interval = config.get('monitoring_interval', 60)

        # 健康检查配置
        self.health_check_timeout = config.get('health_check_timeout', 5.0)
        self.max_health_checks = config.get('max_health_checks', 10)

        # 初始化默认策略
        self._initialize_default_policies()
        # 初始化传播规则
        self._initialize_propagation_rules()

        # 注册清理函数
        import atexit
        atexit.register(self.shutdown)

    def _initialize_default_policies(self) -> None:
        """初始化默认隔离策略"""
        default_policies = [
            IsolationPolicy(
                policy_id="instance_failure_policy",
                error_category=ErrorCategory.INSTANCE_FAILURE,
                isolation_level=IsolationLevel.INSTANCE,
                max_error_rate=0.05,
                quarantine_time=600,
                auto_recovery=True
            ),
            IsolationPolicy(
                policy_id="api_limit_policy",
                error_category=ErrorCategory.API_LIMIT,
                isolation_level=IsolationLevel.TASK,
                max_error_rate=0.2,
                quarantine_time=60,
                auto_recovery=True
            ),
            IsolationPolicy(
                policy_id="canvas_corruption_policy",
                error_category=ErrorCategory.CANVAS_CORRUPTION,
                isolation_level=IsolationLevel.SESSION,
                max_error_rate=0.01,
                quarantine_time=1800,
                auto_recovery=False
            ),
            IsolationPolicy(
                policy_id="timeout_policy",
                error_category=ErrorCategory.TIMEOUT,
                isolation_level=IsolationLevel.TASK,
                max_error_rate=0.1,
                quarantine_time=300,
                auto_recovery=True
            )
        ]

        for policy in default_policies:
            self._isolation_policies[policy.policy_id] = policy

    def _initialize_propagation_rules(self) -> None:
        """初始化错误传播规则"""
        default_rules = [
            ErrorPropagationRule(
                rule_id="block_critical_propagation",
                source_error_category=ErrorCategory.SYSTEM,
                target_categories=[
                    ErrorCategory.INSTANCE_FAILURE,
                    ErrorCategory.MEMORY_OVERFLOW,
                    ErrorCategory.CANVAS_CORRUPTION
                ],
                block_propagation=True,
                max_propagation_depth=1,
                time_window=300
            ),
            ErrorPropagationRule(
                rule_id="limit_network_propagation",
                source_error_category=ErrorCategory.NETWORK,
                target_categories=[ErrorCategory.TIMEOUT],
                block_propagation=False,
                max_propagation_depth=2,
                time_window=60
            ),
            ErrorPropagationRule(
                rule_id="block_api_limit_cascade",
                source_error_category=ErrorCategory.API_LIMIT,
                target_categories=[ErrorCategory.NETWORK],
                block_propagation=True,
                max_propagation_depth=1,
                time_window=120
            ),
            ErrorPropagationRule(
                rule_id="allow_validation_propagation",
                source_error_category=ErrorCategory.VALIDATION,
                target_categories=[],
                block_propagation=False,
                max_propagation_depth=0,
                time_window=30
            )
        ]

        for rule in default_rules:
            self._propagation_rules[rule.rule_id] = rule

    async def detect_fault_instances(self) -> List[str]:
        """
        检测故障实例

        Returns:
            List[str]: 故障实例ID列表
        """
        fault_instances = []
        current_time = datetime.now()

        with self._lock:
            for instance_id, instance_info in self._registered_instances.items():
                # 检查心跳超时
                if self._is_heartbeat_timeout(instance_info, current_time):
                    fault_instances.append(instance_id)
                    continue

                # 检查错误率
                if self._is_error_rate_high(instance_id):
                    fault_instances.append(instance_id)
                    continue

                # 检查资源使用
                if self._is_resource_usage_abnormal(instance_id):
                    fault_instances.append(instance_id)
                    continue

                # 检查任务执行异常
                if self._is_task_execution_abnormal(instance_id):
                    fault_instances.append(instance_id)
                    continue

        return fault_instances

    def _is_heartbeat_timeout(self, instance_info: InstanceInfo, current_time: datetime) -> bool:
        """检查心跳超时"""
        heartbeat_timeout = self.config.get('heartbeat_timeout', 120)  # 默认2分钟
        time_diff = (current_time - instance_info.last_heartbeat).total_seconds()
        return time_diff > heartbeat_timeout

    def _is_error_rate_high(self, instance_id: str) -> bool:
        """检查错误率是否过高"""
        recent_errors = self._get_recent_errors_for_instance(instance_id, 300)  # 5分钟内
        error_rate_threshold = self.config.get('error_rate_threshold', 0.1)  # 10%
        error_rate = len(recent_errors) / 300
        return error_rate > error_rate_threshold

    def _is_resource_usage_abnormal(self, instance_id: str) -> bool:
        """检查资源使用是否异常"""
        health_result = self._instance_health.get(instance_id)
        if not health_result:
            return False

        # 检查内存使用
        memory_threshold = self.config.get('memory_threshold', 1024)  # MB
        if health_result.memory_usage and health_result.memory_usage > memory_threshold:
            return True

        # 检查CPU使用
        cpu_threshold = self.config.get('cpu_threshold', 90)  # 百分比
        if health_result.cpu_usage and health_result.cpu_usage > cpu_threshold:
            return True

        return False

    def _is_task_execution_abnormal(self, instance_id: str) -> bool:
        """检查任务执行是否异常"""
        instance_info = self._registered_instances.get(instance_id)
        if not instance_info:
            return False

        # 检查是否有长时间活跃的任务
        max_task_duration = self.config.get('max_task_duration', 600)  # 10分钟
        current_time = datetime.now()

        # 这里需要实际的任务开始时间记录，暂时跳过
        # 实际实现中应该记录每个任务的开始时间

        # 检查任务失败率
        if instance_info.total_tasks_processed > 0:
            failure_rate = instance_info.error_count / instance_info.total_tasks_processed
            failure_threshold = self.config.get('task_failure_threshold', 0.2)  # 20%
            if failure_rate > failure_threshold:
                return True

        return False

    async def isolate_fault_instances(self, fault_instances: List[str]) -> Dict[str, bool]:
        """
        隔离故障实例

        Args:
            fault_instances: 故障实例ID列表

        Returns:
            Dict[str, bool]: 每个实例的隔离结果
        """
        results = {}

        for instance_id in fault_instances:
            try:
                # 分析故障原因
                fault_reason = await self._analyze_fault_cause(instance_id)

                # 执行隔离
                success = await self.quarantine_instance(
                    instance_id,
                    f"自动检测到故障: {fault_reason}"
                )

                results[instance_id] = success

                if success:
                    self.logger.warning(f"故障实例已自动隔离 - ID: {instance_id}, 原因: {fault_reason}")
                else:
                    self.logger.error(f"故障实例隔离失败 - ID: {instance_id}")

            except Exception as e:
                self.logger.error(f"隔离故障实例异常 - ID: {instance_id}: {str(e)}")
                results[instance_id] = False

        return results

    async def _analyze_fault_cause(self, instance_id: str) -> str:
        """
        分析故障原因

        Args:
            instance_id: 实例ID

        Returns:
            str: 故障原因描述
        """
        try:
            # 获取最近的错误
            recent_errors = self._get_recent_errors_for_instance(instance_id, 3600)
            if not recent_errors:
                return "心跳超时"

            # 分析主要错误类型
            error_categories = {}
            for error in recent_errors:
                category = error.error_category.value
                error_categories[category] = error_categories.get(category, 0) + 1

            # 找出最常见的错误类型
            most_common_category = max(error_categories, key=error_categories.get)
            count = error_categories[most_common_category]

            # 根据错误类型生成原因描述
            cause_descriptions = {
                "network": f"网络错误频繁({count}次)",
                "api_limit": f"API调用受限({count}次)",
                "instance_failure": f"实例内部故障({count}次)",
                "canvas_corruption": f"Canvas文件损坏({count}次)",
                "memory_overflow": f"内存溢出({count}次)",
                "timeout": f"任务超时({count}次)",
                "validation": f"数据验证失败({count}次)",
                "system": f"系统级错误({count}次)"
            }

            return cause_descriptions.get(most_common_category, f"未知错误({count}次)")

        except Exception as e:
            self.logger.error(f"分析故障原因失败 - ID: {instance_id}: {str(e)}")
            return "原因分析失败"

    async def auto_isolation_check(self) -> Dict[str, Any]:
        """
        执行自动隔离检查

        Returns:
            Dict[str, Any]: 检查结果
        """
        try:
            # 检测故障实例
            fault_instances = await self.detect_fault_instances()

            if not fault_instances:
                return {
                    'checked_at': datetime.now().isoformat(),
                    'fault_instances': [],
                    'isolated_instances': [],
                    'isolation_results': {},
                    'summary': '未发现故障实例'
                }

            # 隔离故障实例
            isolation_results = await self.isolate_fault_instances(fault_instances)

            # 统计成功的隔离
            isolated_instances = [
                instance_id for instance_id, success in isolation_results.items()
                if success
            ]

            return {
                'checked_at': datetime.now().isoformat(),
                'fault_instances': fault_instances,
                'isolated_instances': isolated_instances,
                'isolation_results': isolation_results,
                'summary': f'检测到{len(fault_instances)}个故障实例，成功隔离{len(isolated_instances)}个'
            }

        except Exception as e:
            self.logger.error(f"自动隔离检查失败: {str(e)}")
            return {
                'checked_at': datetime.now().isoformat(),
                'error': str(e),
                'summary': '自动隔离检查失败'
            }

    def get_fault_detection_metrics(self) -> Dict[str, Any]:
        """
        获取故障检测指标

        Returns:
            Dict[str, Any]: 故障检测指标
        """
        with self._lock:
            total_instances = len(self._registered_instances)
            quarantined_instances = len(self._quarantined_instances)
            unhealthy_instances = sum(
                1 for health in self._instance_health.values()
                if not health.is_healthy
            )

            # 按错误类型统计
            error_by_category = {}
            for error in self._error_history:
                category = error.error_category.value
                error_by_category[category] = error_by_category.get(category, 0) + 1

            # 计算隔离率
            isolation_rate = (quarantined_instances / total_instances) if total_instances > 0 else 0

            return {
                'total_instances': total_instances,
                'active_instances': total_instances - quarantined_instances,
                'quarantined_instances': quarantined_instances,
                'unhealthy_instances': unhealthy_instances,
                'isolation_rate': isolation_rate,
                'error_distribution': error_by_category,
                'last_check_time': datetime.now().isoformat()
            }

    async def start_monitoring(self) -> None:
        """启动监控线程"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._cleanup_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="ErrorIsolationMonitor"
        )
        self._cleanup_thread.start()
        self.logger.info("错误隔离监控已启动")

    async def stop_monitoring(self) -> None:
        """停止监控线程"""
        self._monitoring_active = False
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        self.logger.info("错误隔离监控已停止")

    def _monitoring_loop(self) -> None:
        """监控循环，定期执行健康检查和清理"""
        while self._monitoring_active:
            try:
                # 执行健康检查
                self._perform_health_checks()

                # 执行自动故障检测
                asyncio.run(self._auto_fault_detection())

                # 清理过期的隔离实例
                self._cleanup_expired_quarantines()

                # 分析错误模式
                self._analyze_error_patterns()

                # 清理传播历史
                self.clear_propagation_history(older_than_seconds=3600)

                # 等待下一次检查
                time.sleep(self._monitoring_interval)

            except Exception as e:
                self.logger.error(f"监控循环错误: {str(e)}")
                time.sleep(10)  # 错误后短暂等待

    async def _auto_fault_detection(self) -> None:
        """自动故障检测"""
        try:
            # 执行自动隔离检查
            check_result = await self.auto_isolation_check()

            # 记录检测结果
            if check_result.get('fault_instances'):
                self.logger.info(
                    f"自动故障检测完成: {check_result.get('summary', '')}"
                )

                # 如果有实例被隔离，触发通知
                if check_result.get('isolated_instances'):
                    await self._send_auto_isolation_notification(check_result)

        except Exception as e:
            self.logger.error(f"自动故障检测失败: {str(e)}")

    async def _send_auto_isolation_notification(self, check_result: Dict[str, Any]) -> None:
        """发送自动隔离通知"""
        try:
            message = f"自动隔离通知:\n"
            message += f"检测时间: {check_result.get('checked_at', 'N/A')}\n"
            message += f"故障实例: {', '.join(check_result.get('fault_instances', []))}\n"
            message += f"隔离实例: {', '.join(check_result.get('isolated_instances', []))}\n"
            message += f"总结: {check_result.get('summary', '')}"

            self.logger.warning(message)

            # 这里可以添加其他通知方式，如邮件、短信、webhook等

        except Exception as e:
            self.logger.error(f"发送自动隔离通知失败: {str(e)}")

    def _perform_health_checks(self) -> None:
        """执行健康检查"""
        with self._lock:
            instances_to_check = list(self._instance_health.keys())

        # 使用线程池并行执行健康检查
        with ThreadPoolExecutor(max_workers=min(10, len(instances_to_check))) as executor:
            futures = {
                executor.submit(self._check_instance_health, instance_id): instance_id
                for instance_id in instances_to_check
            }

            for future in futures:
                try:
                    result = future.result(timeout=self.health_check_timeout)
                    self._update_instance_health(result)
                except Exception as e:
                    instance_id = futures[future]
                    self.logger.error(f"健康检查失败 - 实例 {instance_id}: {str(e)}")

    def _check_instance_health(self, instance_id: str) -> HealthCheckResult:
        """检查单个实例的健康状态"""
        start_time = time.time()

        try:
            # 这里应该实现实际的健康检查逻辑
            # 例如：检查实例是否响应、内存使用情况等

            # 模拟健康检查
            response_time = (time.time() - start_time) * 1000

            # 获取错误统计
            recent_errors = self._get_recent_errors_for_instance(instance_id, 300)  # 5分钟内

            # 判断健康状态
            error_rate = len(recent_errors) / 300  # 每秒错误数
            is_healthy = error_rate < 0.1 and response_time < 5000

            return HealthCheckResult(
                instance_id=instance_id,
                check_time=datetime.now(),
                is_healthy=is_healthy,
                response_time=response_time,
                memory_usage=self._get_memory_usage(instance_id),
                cpu_usage=self._get_cpu_usage(instance_id),
                active_tasks=self._get_active_task_count(instance_id),
                error_count=len(recent_errors)
            )

        except Exception as e:
            return HealthCheckResult(
                instance_id=instance_id,
                check_time=datetime.now(),
                is_healthy=False,
                response_time=(time.time() - start_time) * 1000,
                error_message=str(e),
                error_count=1
            )

    def _update_instance_health(self, result: HealthCheckResult) -> None:
        """更新实例健康状态"""
        with self._lock:
            self._instance_health[result.instance_id] = result

            # 如果实例不健康且未被隔离，触发隔离
            if not result.is_healthy and result.instance_id not in self._quarantined_instances:
                asyncio.create_task(
                    self.quarantine_instance(
                        result.instance_id,
                        f"健康检查失败: {result.error_message or '响应超时'}"
                    )
                )

    def _get_recent_errors_for_instance(self, instance_id: str, seconds: int) -> List[ErrorInfo]:
        """获取指定实例最近的错误"""
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        with self._lock:
            return [
                error for error in self._error_history
                if error.instance_id == instance_id and error.timestamp > cutoff_time
            ]

    def _get_memory_usage(self, instance_id: str) -> Optional[float]:
        """获取实例内存使用量"""
        # 这里应该实现实际的内存监控逻辑
        # 返回MB为单位的内存使用量
        return None

    def _get_cpu_usage(self, instance_id: str) -> Optional[float]:
        """获取实例CPU使用率"""
        # 这里应该实现实际的CPU监控逻辑
        # 返回百分比
        return None

    def _get_active_task_count(self, instance_id: str) -> int:
        """获取实例活跃任务数"""
        # 这里应该实现实际的任务计数逻辑
        return 0

    def _cleanup_expired_quarantines(self) -> None:
        """清理过期的隔离实例"""
        current_time = datetime.now()
        expired_instances = []

        with self._lock:
            for instance_id, record in self._quarantine_records.items():
                if not record.is_active:
                    continue

                # 检查是否到了自动恢复时间
                if record.auto_recovery_time and current_time >= record.auto_recovery_time:
                    expired_instances.append(instance_id)

        # 尝试恢复过期的实例
        for instance_id in expired_instances:
            asyncio.create_task(self._attempt_instance_recovery(instance_id))

    async def _attempt_instance_recovery(self, instance_id: str) -> bool:
        """尝试恢复实例"""
        try:
            with self._lock:
                record = self._quarantine_records.get(instance_id)
                if not record or not record.is_active:
                    return False

                record.recovery_attempts += 1

                # 检查恢复次数限制
                max_recovery_attempts = self.config.get('max_recovery_attempts', 3)
                if record.recovery_attempts > max_recovery_attempts:
                    self.logger.error(f"实例恢复尝试次数超限 - ID: {instance_id}")
                    return False

            # 执行健康检查
            health_result = await self.check_instance_health(instance_id)

            if health_result.is_healthy:
                # 恢复成功，解除隔离
                await self.release_quarantine(instance_id)
                self.logger.info(f"实例自动恢复成功 - ID: {instance_id}")
                return True
            else:
                # 恢复失败，设置下一次恢复时间
                next_recovery_time = datetime.now() + timedelta(seconds=300 * record.recovery_attempts)
                with self._lock:
                    record.auto_recovery_time = next_recovery_time
                self.logger.warning(f"实例恢复失败，将在下次尝试 - ID: {instance_id}")
                return False

        except Exception as e:
            self.logger.error(f"实例恢复异常 - ID: {instance_id}: {str(e)}")
            return False

    def _analyze_error_patterns(self) -> None:
        """分析错误模式"""
        with self._lock:
            recent_errors = [
                error for error in self._error_history
                if error.timestamp > datetime.now() - timedelta(hours=1)
            ]

        # 按错误类型分组
        error_groups = {}
        for error in recent_errors:
            category = error.error_category
            if category not in error_groups:
                error_groups[category] = []
            error_groups[category].append(error)

        # 分析每种错误类型的模式
        for category, errors in error_groups.items():
            if len(errors) >= 3:  # 只分析出现3次以上的错误
                pattern_id = f"{category.value}_pattern"

                # 判断时间模式
                time_pattern = self._determine_time_pattern(errors)

                # 获取受影响的实例
                affected_instances = list(set(e.instance_id for e in errors if e.instance_id))

                pattern = FailurePattern(
                    pattern_id=pattern_id,
                    error_type=category,
                    frequency=len(errors),
                    time_pattern=time_pattern,
                    affected_instances=affected_instances,
                    first_occurrence=min(e.timestamp for e in errors),
                    last_occurrence=max(e.timestamp for e in errors),
                    auto_recovery=self._can_auto_recover(category),
                    recommended_action=self._get_recommended_action(category)
                )

                with self._lock:
                    self._failure_patterns[pattern_id] = pattern

    def _determine_time_pattern(self, errors: List[ErrorInfo]) -> str:
        """判断错误的时间模式"""
        if len(errors) < 3:
            return "random"

        # 计算错误间隔
        intervals = []
        for i in range(1, len(errors)):
            interval = (errors[i].timestamp - errors[i-1].timestamp).total_seconds()
            intervals.append(interval)

        # 判断模式
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)

        if variance < avg_interval * 0.1:  # 方差很小，周期性
            return "periodic"
        elif avg_interval < 10:  # 平均间隔很短，突发
            return "burst"
        else:
            return "random"

    def _can_auto_recover(self, category: ErrorCategory) -> bool:
        """判断错误类型是否可以自动恢复"""
        auto_recoverable = {
            ErrorCategory.NETWORK,
            ErrorCategory.API_LIMIT,
            ErrorCategory.TIMEOUT
        }
        return category in auto_recoverable

    def _get_recommended_action(self, category: ErrorCategory) -> Optional[str]:
        """获取针对错误类型的推荐操作"""
        actions = {
            ErrorCategory.NETWORK: "检查网络连接，考虑增加重试",
            ErrorCategory.API_LIMIT: "等待API限制恢复，考虑降低请求频率",
            ErrorCategory.INSTANCE_FAILURE: "重启实例，检查系统资源",
            ErrorCategory.CANVAS_CORRUPTION: "修复Canvas文件，手动恢复",
            ErrorCategory.MEMORY_OVERFLOW: "释放内存，考虑分批处理",
            ErrorCategory.TIMEOUT: "增加超时时间，优化处理逻辑",
            ErrorCategory.VALIDATION: "检查输入数据格式",
            ErrorCategory.SYSTEM: "检查系统配置和权限"
        }
        return actions.get(category)

    async def isolate_error(self, error_info: ErrorInfo) -> bool:
        """
        隔离错误，防止传播

        Args:
            error_info: 错误信息

        Returns:
            bool: 是否成功隔离
        """
        try:
            # 记录错误
            with self._lock:
                self._error_history.append(error_info)

            # 获取对应的隔离策略
            policy = self._get_isolation_policy(error_info.error_category)

            if not policy:
                self.logger.warning(f"未找到错误类型的隔离策略: {error_info.error_category}")
                return False

            # 根据策略执行隔离
            if policy.isolation_level == IsolationLevel.INSTANCE and error_info.instance_id:
                # 隔离整个实例
                await self.quarantine_instance(
                    error_info.instance_id,
                    f"错误隔离: {error_info.error_message}"
                )

            elif policy.isolation_level == IsolationLevel.TASK and error_info.task_id:
                # 隔离单个任务
                self._isolate_task(error_info.task_id)

            elif policy.isolation_level == IsolationLevel.SESSION and error_info.session_id:
                # 隔离整个会话
                self._isolate_session(error_info.session_id)

            # 发送通知（如果需要）
            if policy.notification_required:
                await self._send_isolation_notification(error_info, policy)

            self.logger.info(f"错误已隔离 - ID: {error_info.error_id}, 级别: {policy.isolation_level.value}")
            return True

        except Exception as e:
            self.logger.error(f"错误隔离失败: {str(e)}")
            return False

    def _get_isolation_policy(self, category: ErrorCategory) -> Optional[IsolationPolicy]:
        """根据错误类型获取隔离策略"""
        for policy in self._isolation_policies.values():
            if policy.error_category == category:
                return policy
        return None

    async def quarantine_instance(self, instance_id: str, reason: str,
                               policy_id: Optional[str] = None) -> bool:
        """
        隔离不健康实例

        Args:
            instance_id: 实例ID
            reason: 隔离原因
            policy_id: 隔离策略ID

        Returns:
            bool: 是否成功隔离
        """
        try:
            with self._lock:
                # 检查实例是否已被隔离
                if instance_id in self._quarantined_instances:
                    self.logger.warning(f"实例已被隔离 - ID: {instance_id}")
                    return False

                # 获取实例信息
                instance_info = self._registered_instances.get(instance_id)
                if not instance_info:
                    self.logger.error(f"未找到实例 - ID: {instance_id}")
                    return False

                # 添加到隔离列表
                self._quarantined_instances.add(instance_id)
                instance_info.status = "quarantined"

                # 获取隔离策略
                if not policy_id:
                    policy = self._get_isolation_policy_for_instance(instance_id)
                    policy_id = policy.policy_id if policy else "default_policy"

                # 创建隔离记录
                policy_config = self._isolation_policies.get(policy_id)
                quarantine_time = policy_config.quarantine_time if policy_config else 300
                auto_recovery_time = datetime.now() + timedelta(seconds=quarantine_time)

                record = QuarantineRecord(
                    instance_id=instance_id,
                    quarantine_time=datetime.now(),
                    reason=reason,
                    policy_id=policy_id,
                    auto_recovery_time=auto_recovery_time if policy_config and policy_config.auto_recovery else None
                )
                self._quarantine_records[instance_id] = record

            self.logger.warning(f"实例已隔离 - ID: {instance_id}, 原因: {reason}, 策略: {policy_id}")

            # 执行实际的隔离操作
            await self._execute_instance_isolation(instance_id, instance_info)

            # 暂停实例的活跃任务
            await self._pause_instance_tasks(instance_id)

            return True

        except Exception as e:
            self.logger.error(f"实例隔离失败 - ID: {instance_id}: {str(e)}")
            return False

    def _get_isolation_policy_for_instance(self, instance_id: str) -> Optional[IsolationPolicy]:
        """根据实例最近的错误获取隔离策略"""
        recent_errors = self._get_recent_errors_for_instance(instance_id, 3600)
        if recent_errors:
            # 使用最近的错误类型获取策略
            return self._get_isolation_policy(recent_errors[-1].error_category)
        return None

    async def _execute_instance_isolation(self, instance_id: str, instance_info: InstanceInfo) -> None:
        """执行实例隔离操作"""
        try:
            # 根据实例类型执行不同的隔离策略
            if instance_info.instance_type == "agent":
                # 停止接收新任务
                await self._stop_agent_task_reception(instance_id)
            elif instance_info.instance_type == "worker":
                # 暂停工作进程
                await self._pause_worker_processes(instance_id)
            elif instance_info.instance_type == "processor":
                # 停止处理器
                await self._stop_processor(instance_id)

        except Exception as e:
            self.logger.error(f"执行实例隔离失败 - ID: {instance_id}: {str(e)}")

    async def _stop_agent_task_reception(self, instance_id: str) -> None:
        """停止Agent接收新任务"""
        # 这里应该实现停止Agent接收任务的逻辑
        self.logger.info(f"已停止Agent接收新任务 - ID: {instance_id}")

    async def _pause_worker_processes(self, instance_id: str) -> None:
        """暂停工作进程"""
        # 这里应该实现暂停工作进程的逻辑
        self.logger.info(f"已暂停工作进程 - ID: {instance_id}")

    async def _stop_processor(self, instance_id: str) -> None:
        """停止处理器"""
        # 这里应该实现停止处理器的逻辑
        self.logger.info(f"已停止处理器 - ID: {instance_id}")

    async def _pause_instance_tasks(self, instance_id: str) -> None:
        """暂停实例的活跃任务"""
        try:
            with self._lock:
                instance_info = self._registered_instances.get(instance_id)
                if not instance_info:
                    return

                active_tasks = list(instance_info.active_tasks)

            # 暂停每个活跃任务
            for task_id in active_tasks:
                await self._pause_task(task_id, instance_id)

        except Exception as e:
            self.logger.error(f"暂停实例任务失败 - ID: {instance_id}: {str(e)}")

    async def _pause_task(self, task_id: str, instance_id: str) -> None:
        """暂停单个任务"""
        # 这里应该实现暂停任务的逻辑
        self.logger.info(f"已暂停任务 - ID: {task_id}, 实例: {instance_id}")

    def register_instance(self, instance_info: InstanceInfo) -> bool:
        """
        注册实例

        Args:
            instance_info: 实例信息

        Returns:
            bool: 是否成功注册
        """
        try:
            with self._lock:
                self._registered_instances[instance_info.instance_id] = instance_info

            self.logger.info(f"实例已注册 - ID: {instance_info.instance_id}, 类型: {instance_info.instance_type}")
            return True

        except Exception as e:
            self.logger.error(f"实例注册失败 - ID: {instance_info.instance_id}: {str(e)}")
            return False

    def unregister_instance(self, instance_id: str) -> bool:
        """
        注销实例

        Args:
            instance_id: 实例ID

        Returns:
            bool: 是否成功注销
        """
        try:
            with self._lock:
                # 先解除隔离
                if instance_id in self._quarantined_instances:
                    self._quarantined_instances.remove(instance_id)

                # 删除注册信息
                self._registered_instances.pop(instance_id, None)
                self._instance_health.pop(instance_id, None)
                self._quarantine_records.pop(instance_id, None)

            self.logger.info(f"实例已注销 - ID: {instance_id}")
            return True

        except Exception as e:
            self.logger.error(f"实例注销失败 - ID: {instance_id}: {str(e)}")
            return False

    def update_instance_heartbeat(self, instance_id: str) -> bool:
        """
        更新实例心跳

        Args:
            instance_id: 实例ID

        Returns:
            bool: 是否成功更新
        """
        try:
            with self._lock:
                instance_info = self._registered_instances.get(instance_id)
                if instance_info:
                    instance_info.last_heartbeat = datetime.now()
                    return True
            return False

        except Exception as e:
            self.logger.error(f"更新实例心跳失败 - ID: {instance_id}: {str(e)}")
            return False

    def add_task_to_instance(self, instance_id: str, task_id: str) -> bool:
        """
        将任务分配给实例

        Args:
            instance_id: 实例ID
            task_id: 任务ID

        Returns:
            bool: 是否成功分配
        """
        try:
            with self._lock:
                # 检查实例是否被隔离
                if instance_id in self._quarantined_instances:
                    self.logger.warning(f"实例被隔离，无法分配任务 - ID: {instance_id}")
                    return False

                instance_info = self._registered_instances.get(instance_id)
                if instance_info:
                    instance_info.active_tasks.add(task_id)
                    return True

            return False

        except Exception as e:
            self.logger.error(f"分配任务失败 - 实例: {instance_id}, 任务: {task_id}: {str(e)}")
            return False

    def remove_task_from_instance(self, instance_id: str, task_id: str) -> bool:
        """
        从实例中移除任务

        Args:
            instance_id: 实例ID
            task_id: 任务ID

        Returns:
            bool: 是否成功移除
        """
        try:
            with self._lock:
                instance_info = self._registered_instances.get(instance_id)
                if instance_info and task_id in instance_info.active_tasks:
                    instance_info.active_tasks.remove(task_id)
                    instance_info.total_tasks_processed += 1
                    return True

            return False

        except Exception as e:
            self.logger.error(f"移除任务失败 - 实例: {instance_id}, 任务: {task_id}: {str(e)}")
            return False

    def _isolate_task(self, task_id: str) -> bool:
        """隔离单个任务"""
        # 这里应该实现任务隔离逻辑
        self.logger.info(f"任务已隔离 - ID: {task_id}")
        return True

    def _isolate_session(self, session_id: str) -> bool:
        """隔离整个会话"""
        # 这里应该实现会话隔离逻辑
        self.logger.info(f"会话已隔离 - ID: {session_id}")
        return True

    async def _send_isolation_notification(self, error_info: ErrorInfo, policy: IsolationPolicy) -> None:
        """发送隔离通知"""
        # 这里应该实现通知逻辑
        message = f"错误隔离通知:\n"
        message += f"错误类型: {error_info.error_category.value}\n"
        message += f"隔离级别: {policy.isolation_level.value}\n"
        message += f"错误消息: {error_info.error_message}\n"

        if error_info.instance_id:
            message += f"实例ID: {error_info.instance_id}\n"
        if error_info.task_id:
            message += f"任务ID: {error_info.task_id}\n"

        self.logger.info(message)

    async def check_instance_health(self, instance_id: str) -> HealthCheckResult:
        """
        检查实例健康状态

        Args:
            instance_id: 实例ID

        Returns:
            HealthCheckResult: 健康检查结果
        """
        return self._check_instance_health(instance_id)

    async def release_quarantine(self, instance_id: str) -> bool:
        """
        解除实例隔离

        Args:
            instance_id: 实例ID

        Returns:
            bool: 是否成功解除
        """
        try:
            with self._lock:
                # 检查实例是否被隔离
                if instance_id not in self._quarantined_instances:
                    self.logger.warning(f"实例未被隔离 - ID: {instance_id}")
                    return False

                # 获取实例和隔离记录
                instance_info = self._registered_instances.get(instance_id)
                quarantine_record = self._quarantine_records.get(instance_id)

                if not instance_info or not quarantine_record:
                    self.logger.error(f"未找到实例或隔离记录 - ID: {instance_id}")
                    return False

                # 更新状态
                self._quarantined_instances.remove(instance_id)
                instance_info.status = "active"
                quarantine_record.is_active = False

            self.logger.info(f"实例已解除隔离 - ID: {instance_id}")

            # 执行恢复操作
            await self._execute_instance_recovery(instance_id, instance_info)

            # 恢复暂停的任务
            await self._resume_instance_tasks(instance_id)

            return True

        except Exception as e:
            self.logger.error(f"解除隔离失败 - ID: {instance_id}: {str(e)}")
            return False

    async def _execute_instance_recovery(self, instance_id: str, instance_info: InstanceInfo) -> None:
        """执行实例恢复操作"""
        try:
            # 根据实例类型执行不同的恢复策略
            if instance_info.instance_type == "agent":
                # 恢复接收新任务
                await self._resume_agent_task_reception(instance_id)
            elif instance_info.instance_type == "worker":
                # 恢复工作进程
                await self._resume_worker_processes(instance_id)
            elif instance_info.instance_type == "processor":
                # 恢复处理器
                await self._resume_processor(instance_id)

        except Exception as e:
            self.logger.error(f"执行实例恢复失败 - ID: {instance_id}: {str(e)}")

    async def _resume_agent_task_reception(self, instance_id: str) -> None:
        """恢复Agent接收新任务"""
        # 这里应该实现恢复Agent接收任务的逻辑
        self.logger.info(f"已恢复Agent接收新任务 - ID: {instance_id}")

    async def _resume_worker_processes(self, instance_id: str) -> None:
        """恢复工作进程"""
        # 这里应该实现恢复工作进程的逻辑
        self.logger.info(f"已恢复工作进程 - ID: {instance_id}")

    async def _resume_processor(self, instance_id: str) -> None:
        """恢复处理器"""
        # 这里应该实现恢复处理器的逻辑
        self.logger.info(f"已恢复处理器 - ID: {instance_id}")

    async def _resume_instance_tasks(self, instance_id: str) -> None:
        """恢复实例的暂停任务"""
        try:
            with self._lock:
                instance_info = self._registered_instances.get(instance_id)
                if not instance_info:
                    return

                # 获取暂停的任务（这里需要一个记录暂停任务的机制）
                paused_tasks = []  # 实际实现中应该从某个地方获取暂停的任务列表

            # 恢复每个暂停的任务
            for task_id in paused_tasks:
                await self._resume_task(task_id, instance_id)

        except Exception as e:
            self.logger.error(f"恢复实例任务失败 - ID: {instance_id}: {str(e)}")

    async def _resume_task(self, task_id: str, instance_id: str) -> None:
        """恢复单个任务"""
        # 这里应该实现恢复任务的逻辑
        self.logger.info(f"已恢复任务 - ID: {task_id}, 实例: {instance_id}")

    async def get_quarantined_instances(self) -> List[str]:
        """
        获取被隔离的实例列表

        Returns:
            List[str]: 被隔离的实例ID列表
        """
        with self._lock:
            return list(self._quarantined_instances)

    async def analyze_error_patterns(self) -> List[FailurePattern]:
        """
        分析错误模式

        Returns:
            List[FailurePattern]: 故障模式列表
        """
        with self._lock:
            return list(self._failure_patterns.values())

    def get_instance_health_status(self, instance_id: str) -> Optional[HealthCheckResult]:
        """
        获取实例健康状态

        Args:
            instance_id: 实例ID

        Returns:
            Optional[HealthCheckResult]: 健康状态，如果不存在则返回None
        """
        with self._lock:
            return self._instance_health.get(instance_id)

    def get_error_statistics(self, instance_id: Optional[str] = None,
                           time_window: Optional[int] = None) -> Dict[str, Any]:
        """
        获取错误统计信息

        Args:
            instance_id: 实例ID，如果为None则统计所有实例
            time_window: 时间窗口（秒），如果为None则统计所有历史

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            errors = self._error_history

            # 过滤实例
            if instance_id:
                errors = [e for e in errors if e.instance_id == instance_id]

            # 过滤时间
            if time_window:
                cutoff_time = datetime.now() - timedelta(seconds=time_window)
                errors = [e for e in errors if e.timestamp > cutoff_time]

            # 统计
            total_errors = len(errors)
            error_by_category = {}
            error_by_severity = {}

            for error in errors:
                # 按类型统计
                category = error.error_category.value
                error_by_category[category] = error_by_category.get(category, 0) + 1

                # 按严重程度统计
                severity = error.severity.value
                error_by_severity[severity] = error_by_severity.get(severity, 0) + 1

            # 计算错误率
            if time_window:
                error_rate = total_errors / time_window
            else:
                error_rate = 0

            return {
                'total_instances': len(self._registered_instances),
                'total_errors': total_errors,
                'error_rate': error_rate,
                'error_by_category': error_by_category,
                'error_by_severity': error_by_severity,
                'quarantined_instances': len(self._quarantined_instances),
                'unhealthy_instances': sum(
                    1 for health in self._instance_health.values()
                    if not health.is_healthy
                )
            }

    def shutdown(self) -> None:
        """关闭管理器，清理资源"""
        try:
            # 停止监控
            if hasattr(self, '_monitoring_active'):
                self._monitoring_active = False

            # 等待清理线程结束
            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._cleanup_thread.join(timeout=2)

            # 清理资源
            with self._lock:
                self._quarantined_instances.clear()
                self._instance_health.clear()
                self._error_history.clear()
                self._failure_patterns.clear()

            self.logger.info("错误隔离管理器已关闭")

        except Exception as e:
            self.logger.error(f"关闭错误隔离管理器时出错: {str(e)}")

    async def check_error_propagation(self, error_info: ErrorInfo,
                                     target_instance_id: Optional[str] = None) -> bool:
        """
        检查错误是否可以传播

        Args:
            error_info: 错误信息
            target_instance_id: 目标实例ID

        Returns:
            bool: True表示允许传播，False表示阻止传播
        """
        try:
            # 检查是否在传播时间窗口内
            if not self._is_in_propagation_window(error_info):
                self.logger.info(f"错误超出传播时间窗口 - ID: {error_info.error_id}")
                return False

            # 检查传播深度
            current_depth = self._get_propagation_depth(error_info)
            if current_depth >= self._get_max_propagation_depth(error_info.error_category):
                self.logger.warning(f"错误传播深度超限 - ID: {error_info.error_id}, 当前深度: {current_depth}")
                return False

            # 检查传播规则
            for rule in self._propagation_rules.values():
                if rule.source_error_category == error_info.error_category:
                    if rule.block_propagation:
                        # 记录被阻止的传播事件
                        await self._record_propagation_event(
                            error_info, target_instance_id, current_depth, True,
                            f"被规则 {rule.rule_id} 阻止"
                        )
                        self.logger.info(f"错误传播被阻止 - ID: {error_info.error_id}, 规则: {rule.rule_id}")
                        return False

            # 检查目标实例是否已被隔离
            if target_instance_id and target_instance_id in self._quarantined_instances:
                self.logger.info(f"目标实例已被隔离，阻止传播 - ID: {error_info.error_id}, 实例: {target_instance_id}")
                return False

            # 记录允许的传播事件
            await self._record_propagation_event(
                error_info, target_instance_id, current_depth, False
            )

            return True

        except Exception as e:
            self.logger.error(f"检查错误传播失败: {str(e)}")
            return False

    def _is_in_propagation_window(self, error_info: ErrorInfo) -> bool:
        """检查错误是否在传播时间窗口内"""
        for rule in self._propagation_rules.values():
            if rule.source_error_category == error_info.error_category:
                time_diff = (datetime.now() - error_info.timestamp).total_seconds()
                return time_diff <= rule.time_window
        return True

    def _get_propagation_depth(self, error_info: ErrorInfo) -> int:
        """获取错误的传播深度"""
        # 检查是否有父错误
        if hasattr(error_info, 'context') and 'parent_error_id' in error_info.context:
            parent_error_id = error_info.context['parent_error_id']
            # 递归查找父错误的传播深度
            for error in self._error_history:
                if error.error_id == parent_error_id:
                    return self._get_propagation_depth(error) + 1
        return 0

    def _get_max_propagation_depth(self, error_category: ErrorCategory) -> int:
        """获取错误类型的最大传播深度"""
        for rule in self._propagation_rules.values():
            if rule.source_error_category == error_category:
                return rule.max_propagation_depth
        return 3  # 默认最大深度

    async def _record_propagation_event(self, error_info: ErrorInfo,
                                       target_instance_id: Optional[str],
                                       depth: int, blocked: bool,
                                       block_reason: Optional[str] = None) -> None:
        """记录错误传播事件"""
        event = ErrorPropagationEvent(
            event_id=f"prop_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self._propagation_events)}",
            source_error=error_info,
            target_instance_id=target_instance_id,
            propagation_time=datetime.now(),
            propagation_depth=depth,
            blocked=blocked,
            block_reason=block_reason
        )

        with self._lock:
            self._propagation_events.append(event)

            # 更新活跃传播记录
            if not blocked:
                if error_info.error_id not in self._active_propagations:
                    self._active_propagations[error_info.error_id] = []
                if target_instance_id:
                    self._active_propagations[error_info.error_id].append(target_instance_id)

    async def propagate_error(self, error_info: ErrorInfo,
                             target_instances: List[str]) -> Dict[str, bool]:
        """
        向目标实例传播错误

        Args:
            error_info: 错误信息
            target_instances: 目标实例列表

        Returns:
            Dict[str, bool]: 每个实例的传播结果
        """
        results = {}

        for instance_id in target_instances:
            # 检查是否可以传播
            can_propagate = await self.check_error_propagation(error_info, instance_id)

            if can_propagate:
                try:
                    # 创建新的错误信息（作为传播的错误）
                    propagated_error = ErrorInfo(
                        error_id=f"prop_{error_info.error_id}_{instance_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        error_code=error_info.error_code,
                        error_message=f"传播错误: {error_info.error_message}",
                        error_category=error_info.error_category,
                        severity=error_info.severity,
                        instance_id=instance_id,
                        task_id=error_info.task_id,
                        session_id=error_info.session_id,
                        context={
                            **error_info.context,
                            'parent_error_id': error_info.error_id,
                            'source_instance_id': error_info.instance_id,
                            'propagated_at': datetime.now().isoformat()
                        },
                        stack_trace=error_info.stack_trace
                    )

                    # 处理传播的错误
                    success = await self.isolate_error(propagated_error)
                    results[instance_id] = success

                    if success:
                        self.logger.info(f"错误已传播到实例 - ID: {instance_id}, 源错误: {error_info.error_id}")
                    else:
                        self.logger.error(f"错误传播失败 - ID: {instance_id}, 源错误: {error_info.error_id}")

                except Exception as e:
                    self.logger.error(f"传播错误到实例失败 - ID: {instance_id}: {str(e)}")
                    results[instance_id] = False
            else:
                results[instance_id] = False
                self.logger.info(f"错误传播被阻止 - ID: {instance_id}, 源错误: {error_info.error_id}")

        return results

    def get_propagation_events(self, error_id: Optional[str] = None,
                             instance_id: Optional[str] = None,
                             time_window: Optional[int] = None) -> List[ErrorPropagationEvent]:
        """
        获取错误传播事件

        Args:
            error_id: 错误ID过滤
            instance_id: 实例ID过滤
            time_window: 时间窗口（秒）

        Returns:
            List[ErrorPropagationEvent]: 传播事件列表
        """
        with self._lock:
            events = self._propagation_events

        # 应用过滤条件
        if error_id:
            events = [e for e in events if e.source_error.error_id == error_id]

        if instance_id:
            events = [e for e in events if e.target_instance_id == instance_id]

        if time_window:
            cutoff_time = datetime.now() - timedelta(seconds=time_window)
            events = [e for e in events if e.propagation_time > cutoff_time]

        return events

    def get_active_propagations(self) -> Dict[str, List[str]]:
        """
        获取活跃的错误传播

        Returns:
            Dict[str, List[str]]: 错误ID到受影响实例列表的映射
        """
        with self._lock:
            return self._active_propagations.copy()

    def clear_propagation_history(self, older_than_seconds: int = 3600) -> int:
        """
        清理传播历史记录

        Args:
            older_than_seconds: 清理多少秒前的记录

        Returns:
            int: 清理的记录数
        """
        cutoff_time = datetime.now() - timedelta(seconds=older_than_seconds)
        removed_count = 0

        with self._lock:
            # 清理传播事件
            original_count = len(self._propagation_events)
            self._propagation_events = [
                e for e in self._propagation_events
                if e.propagation_time > cutoff_time
            ]
            removed_count += original_count - len(self._propagation_events)

            # 清理活跃传播记录
            active_to_remove = []
            for error_id, instances in self._active_propagations.items():
                # 检查源错误是否过期
                source_error = next(
                    (e for e in self._error_history if e.error_id == error_id),
                    None
                )
                if source_error and source_error.timestamp < cutoff_time:
                    active_to_remove.append(error_id)

            for error_id in active_to_remove:
                del self._active_propagations[error_id]
                removed_count += 1

        if removed_count > 0:
            self.logger.info(f"已清理 {removed_count} 条传播历史记录")

        return removed_count