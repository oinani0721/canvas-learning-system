"""
优雅降级管理器 (Graceful Degradation Manager)

该模块负责实现优雅降级处理，在部分失败时提供部分结果和恢复建议。
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
import threading
from collections import defaultdict

# 导入类型定义
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# 导入其他模块的类型
from error_isolation_manager import ErrorInfo, ErrorCategory, ErrorSeverity
from retry_manager import RetryState


class DegradationLevel(Enum):
    """降级级别"""
    NO_DEGRADATION = "no_degradation"     # 无降级
    MINIMAL = "minimal"                  # 轻微降级
    MODERATE = "moderate"                # 中度降级
    SEVERE = "severe"                    # 严重降级
    CRITICAL = "critical"                # 关键降级


class RecoveryAction(Enum):
    """恢复动作"""
    RETRY = "retry"                      # 重试
    FALLBACK = "fallback"                # 使用备用方案
    SKIP = "skip"                        # 跳过
    PARTIAL = "partial"                  # 部分处理
    ALTERNATIVE = "alternative"          # 使用替代方案
    MANUAL = "manual"                    # 手动干预


@dataclass
class ProcessingTask:
    """处理任务"""
    task_id: str
    task_type: str
    priority: int = 0  # 优先级，数字越大优先级越高
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    data: Dict[str, Any] = field(default_factory=dict)
    required: bool = True  # 是否必须完成
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class PartialResult:
    """部分结果"""
    task_id: str
    result: Any
    success: bool
    error_info: Optional[ErrorInfo] = None
    execution_time: float = 0
    degraded: bool = False
    degradation_level: DegradationLevel = DegradationLevel.NO_DEGRADATION
    fallback_used: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecoveryResult:
    """错误恢复结果"""
    recovery_id: str
    original_error: ErrorInfo
    recovery_strategy: str
    recovery_success: bool
    recovery_time: datetime = field(default_factory=datetime.now)
    recovery_details: Dict[str, Any] = field(default_factory=dict)
    user_notification: Optional[str] = None
    impact_assessment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DegradationStrategy:
    """降级策略"""
    strategy_id: str
    task_type: str
    error_categories: List[ErrorCategory]
    degradation_level: DegradationLevel
    fallback_actions: List[RecoveryAction]
    timeout_extension: Optional[float] = None
    resource_limit: Optional[Dict[str, Any]] = None
    quality_threshold: Optional[float] = None
    user_message: Optional[str] = None


@dataclass
class SessionState:
    """会话状态"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    degraded_tasks: int = 0
    current_degradation_level: DegradationLevel = DegradationLevel.NO_DEGRADATION
    partial_results: List[PartialResult] = field(default_factory=list)
    recovery_actions: List[ErrorRecoveryResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GracefulDegradationManager:
    """
    优雅降级管理器

    负责处理部分失败情况，提供部分结果和恢复建议。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化优雅降级管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 内部状态
        self._session_states: Dict[str, SessionState] = {}
        self._degradation_strategies: Dict[str, DegradationStrategy] = {}
        self._fallback_handlers: Dict[str, Callable] = {}
        self._active_sessions: Set[str] = set()

        # 线程安全锁
        self._lock = threading.RLock()

        # 配置参数
        self.max_partial_results = self.config.get('max_partial_results', 1000)
        self.degradation_threshold = self.config.get('degradation_threshold', 0.1)  # 10%
        self.auto_recovery_enabled = self.config.get('auto_recovery_enabled', True)

        # 初始化默认策略
        self._initialize_default_strategies()

        # 注册清理函数
        import atexit
        atexit.register(self.shutdown)

    def _initialize_default_strategies(self) -> None:
        """初始化默认降级策略"""
        default_strategies = [
            DegradationStrategy(
                strategy_id="network_fallback",
                task_type="api_call",
                error_categories=[ErrorCategory.NETWORK, ErrorCategory.TIMEOUT],
                degradation_level=DegradationLevel.MODERATE,
                fallback_actions=[RecoveryAction.RETRY, RecoveryAction.FALLBACK],
                timeout_extension=30.0,
                user_message="网络连接不稳定，正在使用备用方案"
            ),
            DegradationStrategy(
                strategy_id="api_limit_fallback",
                task_type="api_call",
                error_categories=[ErrorCategory.API_LIMIT],
                degradation_level=DegradationLevel.MINIMAL,
                fallback_actions=[RecoveryAction.RETRY, RecoveryAction.ALTERNATIVE],
                timeout_extension=60.0,
                user_message="API调用受限，正在降低请求频率"
            ),
            DegradationStrategy(
                strategy_id="canvas_corruption_fallback",
                task_type="canvas_processing",
                error_categories=[ErrorCategory.CANVAS_CORRUPTION],
                degradation_level=DegradationLevel.SEVERE,
                fallback_actions=[RecoveryAction.SKIP, RecoveryAction.MANUAL],
                user_message="Canvas文件可能损坏，建议手动检查"
            ),
            DegradationStrategy(
                strategy_id="memory_overflow_fallback",
                task_type="batch_processing",
                error_categories=[ErrorCategory.MEMORY_OVERFLOW],
                degradation_level=DegradationLevel.MODERATE,
                fallback_actions=[RecoveryAction.PARTIAL, RecoveryAction.SKIP],
                resource_limit={"batch_size": 10},
                user_message="内存不足，正在分批处理"
            ),
            DegradationStrategy(
                strategy_id="validation_fallback",
                task_type="data_validation",
                error_categories=[ErrorCategory.VALIDATION],
                degradation_level=DegradationLevel.MINIMAL,
                fallback_actions=[RecoveryAction.SKIP],
                user_message="部分数据验证失败，已跳过无效数据"
            )
        ]

        for strategy in default_strategies:
            self._degradation_strategies[strategy.strategy_id] = strategy

    def register_fallback_handler(self, task_type: str, handler: Callable) -> None:
        """
        注册备用处理器

        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self._fallback_handlers[task_type] = handler
        self.logger.info(f"已注册备用处理器: {task_type}")

    async def handle_partial_failure(self,
                                   session_id: str,
                                   completed_tasks: List[ProcessingTask],
                                   failed_tasks: List[ProcessingTask]) -> ErrorRecoveryResult:
        """
        处理部分失败的情况

        Args:
            session_id: 会话ID
            completed_tasks: 已完成的任务列表
            failed_tasks: 失败的任务列表

        Returns:
            ErrorRecoveryResult: 错误恢复结果
        """
        recovery_id = f"recovery_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # 获取或创建会话状态
            session_state = self._get_or_create_session(session_id)

            # 分析失败原因
            failure_analysis = await self._analyze_failures(failed_tasks)

            # 确定降级级别
            degradation_level = self._calculate_degradation_level(
                len(completed_tasks),
                len(failed_tasks),
                failure_analysis
            )

            # 生成部分结果
            partial_results = await self._generate_partial_results(
                completed_tasks,
                failed_tasks,
                degradation_level
            )

            # 执行恢复动作
            recovery_actions = await self._execute_recovery_actions(
                failed_tasks,
                degradation_level,
                failure_analysis
            )

            # 更新会话状态
            session_state.current_degradation_level = degradation_level
            session_state.partial_results.extend(partial_results)
            session_state.recovery_actions.extend(recovery_actions)

            # 创建恢复结果
            recovery_result = ErrorRecoveryResult(
                recovery_id=recovery_id,
                original_error=failure_analysis.get('primary_error'),
                recovery_strategy=failure_analysis.get('strategy', 'default'),
                recovery_success=len(recovery_actions) > 0,
                recovery_details={
                    'degradation_level': degradation_level.value,
                    'completed_tasks': len(completed_tasks),
                    'failed_tasks': len(failed_tasks),
                    'partial_results_count': len(partial_results),
                    'recovery_actions_count': len(recovery_actions),
                    'failure_analysis': failure_analysis
                },
                user_notification=self._generate_user_notification(
                    degradation_level,
                    len(completed_tasks),
                    len(failed_tasks)
                ),
                impact_assessment=self._assess_impact(
                    session_state,
                    degradation_level
                )
            )

            self.logger.info(
                f"部分失败处理完成 - 会话: {session_id}, "
                f"降级级别: {degradation_level.value}, "
                f"恢复动作: {len(recovery_actions)}"
            )

            return recovery_result

        except Exception as e:
            self.logger.error(f"处理部分失败异常: {str(e)}")
            return ErrorRecoveryResult(
                recovery_id=recovery_id,
                original_error=ErrorInfo(
                    error_id="unknown",
                    error_code="RECOVERY_ERROR",
                    error_message=str(e),
                    error_category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.HIGH
                ),
                recovery_strategy="error",
                recovery_success=False,
                recovery_details={'error': str(e)}
            )

    async def _analyze_failures(self, failed_tasks: List[ProcessingTask]) -> Dict[str, Any]:
        """分析失败原因"""
        error_counts = defaultdict(int)
        error_categories = []

        for task in failed_tasks:
            # 这里应该从任务中获取实际的错误信息
            # 暂时使用模拟的错误分析
            if task.retry_count >= task.max_retries:
                error_counts['timeout'] += 1
                error_categories.append(ErrorCategory.TIMEOUT)
            else:
                error_counts['unknown'] += 1
                error_categories.append(ErrorCategory.SYSTEM)

        # 找出主要的错误类型
        primary_error_type = max(error_counts, key=error_counts.get)
        primary_category = max(set(error_categories), key=error_categories.count)

        return {
            'primary_error': primary_error_type,
            'primary_category': primary_category,
            'error_distribution': dict(error_counts),
            'total_failures': len(failed_tasks),
            'strategy': self._select_strategy(primary_category)
        }

    def _calculate_degradation_level(self,
                                   completed_count: int,
                                   failed_count: int,
                                   failure_analysis: Dict[str, Any]) -> DegradationLevel:
        """计算降级级别"""
        total = completed_count + failed_count
        if total == 0:
            return DegradationLevel.NO_DEGRADATION

        failure_rate = failed_count / total

        # 根据失败率确定降级级别
        if failure_rate <= 0.05:  # 5%以下
            return DegradationLevel.NO_DEGRADATION
        elif failure_rate <= 0.15:  # 15%以下
            return DegradationLevel.MINIMAL
        elif failure_rate <= 0.35:  # 35%以下
            return DegradationLevel.MODERATE
        elif failure_rate <= 0.6:   # 60%以下
            return DegradationLevel.SEVERE
        else:
            return DegradationLevel.CRITICAL

    async def _generate_partial_results(self,
                                       completed_tasks: List[ProcessingTask],
                                       failed_tasks: List[ProcessingTask],
                                       degradation_level: DegradationLevel) -> List[PartialResult]:
        """生成部分结果"""
        partial_results = []

        # 处理已完成的任务
        for task in completed_tasks:
            result = PartialResult(
                task_id=task.task_id,
                result={'status': 'completed'},
                success=True,
                degraded=degradation_level != DegradationLevel.NO_DEGRADATION,
                degradation_level=degradation_level
            )
            partial_results.append(result)

        # 处理失败的任务，标记为部分失败
        for task in failed_tasks:
            result = PartialResult(
                task_id=task.task_id,
                result={'status': 'failed', 'retry_count': task.retry_count},
                success=False,
                degraded=True,
                degradation_level=degradation_level,
                error_info=ErrorInfo(
                    error_id=f"error_{task.task_id}",
                    error_code="TASK_FAILED",
                    error_message=f"任务失败，已重试{task.retry_count}次",
                    error_category=ErrorCategory.INSTANCE_FAILURE,
                    severity=ErrorSeverity.MEDIUM
                )
            )
            partial_results.append(result)

        return partial_results

    async def _execute_recovery_actions(self,
                                       failed_tasks: List[ProcessingTask],
                                       degradation_level: DegradationLevel,
                                       failure_analysis: Dict[str, Any]) -> List[ErrorRecoveryResult]:
        """执行恢复动作"""
        recovery_actions = []

        strategy_id = failure_analysis.get('strategy')
        strategy = self._degradation_strategies.get(strategy_id)

        if not strategy:
            # 使用默认恢复策略
            strategy = self._degradation_strategies.get('network_fallback')

        if strategy:
            for task in failed_tasks:
                for action in strategy.fallback_actions:
                    recovery_result = await self._apply_recovery_action(
                        task,
                        action,
                        strategy
                    )
                    if recovery_result:
                        recovery_actions.append(recovery_result)

        return recovery_actions

    async def _apply_recovery_action(self,
                                    task: ProcessingTask,
                                    action: RecoveryAction,
                                    strategy: DegradationStrategy) -> Optional[ErrorRecoveryResult]:
        """应用恢复动作"""
        try:
            recovery_id = f"recover_{task.task_id}_{action.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            if action == RecoveryAction.RETRY:
                # 重试任务
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    # 这里应该实际执行重试
                    return ErrorRecoveryResult(
                        recovery_id=recovery_id,
                        original_error=ErrorInfo(
                            error_id="retry",
                            error_code="RETRY",
                            error_message="重试任务",
                            error_category=ErrorCategory.SYSTEM,
                            severity=ErrorSeverity.LOW
                        ),
                        recovery_strategy=action.value,
                        recovery_success=True,
                        recovery_details={'retry_count': task.retry_count}
                    )

            elif action == RecoveryAction.FALLBACK:
                # 使用备用方案
                handler = self._fallback_handlers.get(task.task_type)
                if handler:
                    result = await handler(task)
                    return ErrorRecoveryResult(
                        recovery_id=recovery_id,
                        original_error=ErrorInfo(
                            error_id="fallback",
                            error_code="FALLBACK",
                            error_message="使用备用方案",
                            error_category=ErrorCategory.SYSTEM,
                            severity=ErrorSeverity.LOW
                        ),
                        recovery_strategy=action.value,
                        recovery_success=True,
                        recovery_details={'fallback_result': result}
                    )

            elif action == RecoveryAction.SKIP:
                # 跳过任务
                return ErrorRecoveryResult(
                    recovery_id=recovery_id,
                    original_error=ErrorInfo(
                        error_id="skip",
                        error_code="SKIP",
                        error_message="跳过任务",
                        error_category=ErrorCategory.SYSTEM,
                        severity=ErrorSeverity.LOW
                    ),
                    recovery_strategy=action.value,
                    recovery_success=True,
                    recovery_details={'skipped': True}
                )

            # 其他恢复动作的实现...

        except Exception as e:
            self.logger.error(f"应用恢复动作失败: {str(e)}")

        return None

    def _select_strategy(self, error_category: ErrorCategory) -> str:
        """选择恢复策略"""
        # 根据错误类型选择合适的策略
        strategy_map = {
            ErrorCategory.NETWORK: "network_fallback",
            ErrorCategory.TIMEOUT: "network_fallback",
            ErrorCategory.API_LIMIT: "api_limit_fallback",
            ErrorCategory.CANVAS_CORRUPTION: "canvas_corruption_fallback",
            ErrorCategory.MEMORY_OVERFLOW: "memory_overflow_fallback",
            ErrorCategory.VALIDATION: "validation_fallback"
        }
        return strategy_map.get(error_category, "network_fallback")

    def _generate_user_notification(self,
                                   degradation_level: DegradationLevel,
                                   completed_count: int,
                                   failed_count: int) -> str:
        """生成用户通知"""
        if degradation_level == DegradationLevel.NO_DEGRADATION:
            return f"所有任务已完成 ({completed_count}/{completed_count + failed_count})"

        total = completed_count + failed_count
        success_rate = (completed_count / total * 100) if total > 0 else 0

        messages = {
            DegradationLevel.MINIMAL: f"少量任务失败，已完成 {success_rate:.1f}% 的任务",
            DegradationLevel.MODERATE: f"部分任务失败，已完成 {success_rate:.1f}% 的任务，系统正在使用备用方案",
            DegradationLevel.SEVERE: f"大量任务失败，仅完成 {success_rate:.1f}% 的任务，建议检查系统状态",
            DegradationLevel.CRITICAL: f"系统严重降级，仅完成 {success_rate:.1f}% 的任务，需要立即处理"
        }

        return messages.get(degradation_level, "系统出现异常，正在处理中")

    def _assess_impact(self,
                      session_state: SessionState,
                      degradation_level: DegradationLevel) -> Dict[str, Any]:
        """评估影响"""
        total_tasks = session_state.total_tasks
        if total_tasks == 0:
            return {'impact': 'minimal'}

        impact_scores = {
            DegradationLevel.NO_DEGRADATION: 0,
            DegradationLevel.MINIMAL: 0.1,
            DegradationLevel.MODERATE: 0.3,
            DegradationLevel.SEVERE: 0.7,
            DegradationLevel.CRITICAL: 1.0
        }

        impact_score = impact_scores.get(degradation_level, 0)

        return {
            'impact_score': impact_score,
            'impact_level': 'minimal' if impact_score < 0.3 else 'moderate' if impact_score < 0.7 else 'severe',
            'affected_tasks': session_state.failed_tasks + session_state.degraded_tasks,
            'recommendations': self._get_recommendations(degradation_level)
        }

    def _get_recommendations(self, degradation_level: DegradationLevel) -> List[str]:
        """获取恢复建议"""
        recommendations = {
            DegradationLevel.NO_DEGRADATION: [],
            DegradationLevel.MINIMAL: [
                "检查网络连接",
                "稍后重试失败的任务"
            ],
            DegradationLevel.MODERATE: [
                "检查系统资源使用情况",
                "考虑降低并发度",
                "检查API限制"
            ],
            DegradationLevel.SEVERE: [
                "立即检查系统日志",
                "暂停新任务提交",
                "考虑重启服务"
            ],
            DegradationLevel.CRITICAL: [
                "系统需要立即维护",
                "联系技术支持",
                "准备数据恢复方案"
            ]
        }
        return recommendations.get(degradation_level, [])

    def _get_or_create_session(self, session_id: str) -> SessionState:
        """获取或创建会话状态"""
        with self._lock:
            if session_id not in self._session_states:
                self._session_states[session_id] = SessionState(session_id=session_id)
                self._active_sessions.add(session_id)
            return self._session_states[session_id]

    async def generate_partial_results(self, session_id: str) -> Dict[str, Any]:
        """
        生成部分结果

        Args:
            session_id: 会话ID

        Returns:
            Dict[str, Any]: 部分结果
        """
        try:
            session_state = self._session_states.get(session_id)
            if not session_state:
                return {'error': 'Session not found'}

            # 整理部分结果
            results = {
                'session_id': session_id,
                'summary': {
                    'total_tasks': session_state.total_tasks,
                    'completed_tasks': session_state.completed_tasks,
                    'failed_tasks': session_state.failed_tasks,
                    'degraded_tasks': session_state.degraded_tasks,
                    'degradation_level': session_state.current_degradation_level.value,
                    'success_rate': (session_state.completed_tasks / session_state.total_tasks) if session_state.total_tasks > 0 else 0
                },
                'partial_results': [
                    {
                        'task_id': r.task_id,
                        'success': r.success,
                        'degraded': r.degraded,
                        'degradation_level': r.degradation_level.value,
                        'error': r.error_info.error_message if r.error_info else None
                    }
                    for r in session_state.partial_results
                ],
                'recovery_actions': [
                    {
                        'recovery_id': r.recovery_id,
                        'strategy': r.recovery_strategy,
                        'success': r.recovery_success,
                        'details': r.recovery_details
                    }
                    for r in session_state.recovery_actions
                ],
                'generated_at': datetime.now().isoformat()
            }

            return results

        except Exception as e:
            self.logger.error(f"生成部分结果失败: {str(e)}")
            return {'error': str(e)}

    async def suggest_recovery_options(self, failed_tasks: List[ProcessingTask]) -> List[str]:
        """
        建议恢复选项

        Args:
            failed_tasks: 失败的任务列表

        Returns:
            List[str]: 恢复选项列表
        """
        options = []

        if not failed_tasks:
            return options

        # 分析失败模式
        retryable_tasks = [t for t in failed_tasks if t.retry_count < t.max_retries]
        non_retryable_tasks = [t for t in failed_tasks if t.retry_count >= t.max_retries]

        if retryable_tasks:
            options.append(f"重试 {len(retryable_tasks)} 个可重试的任务")

        if non_retryable_tasks:
            options.append(f"使用备用方案处理 {len(non_retryable_tasks)} 个任务")

        # 根据任务类型建议具体操作
        task_types = set(t.task_type for t in failed_tasks)
        for task_type in task_types:
            if task_type == "api_call":
                options.append("检查API配置和网络连接")
            elif task_type == "canvas_processing":
                options.append("验证Canvas文件完整性")
            elif task_type == "batch_processing":
                options.append("减少批处理大小")

        return options

    async def create_failure_report(self, session_id: str) -> Dict[str, Any]:
        """
        创建失败报告

        Args:
            session_id: 会话ID

        Returns:
            Dict[str, Any]: 失败报告
        """
        try:
            session_state = self._session_states.get(session_id)
            if not session_state:
                return {'error': 'Session not found'}

            report = {
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'session_duration': (datetime.now() - session_state.created_at).total_seconds(),
                'task_summary': {
                    'total': session_state.total_tasks,
                    'completed': session_state.completed_tasks,
                    'failed': session_state.failed_tasks,
                    'degraded': session_state.degraded_tasks
                },
                'degradation_summary': {
                    'level': session_state.current_degradation_level.value,
                    'impact': self._assess_impact(session_state, session_state.current_degradation_level),
                    'recovery_actions_taken': len(session_state.recovery_actions)
                },
                'recommendations': self._get_recommendations(session_state.current_degradation_level),
                'detailed_failures': [
                    {
                        'task_id': r.task_id,
                        'error': r.error_info.error_message if r.error_info else 'Unknown error',
                        'error_category': r.error_info.error_category.value if r.error_info else 'unknown',
                        'retry_count': r.metadata.get('retry_count', 0) if r.metadata else 0
                    }
                    for r in session_state.partial_results
                    if not r.success
                ]
            }

            return report

        except Exception as e:
            self.logger.error(f"创建失败报告失败: {str(e)}")
            return {'error': str(e)}

    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """
        获取会话状态

        Args:
            session_id: 会话ID

        Returns:
            Optional[SessionState]: 会话状态
        """
        return self._session_states.get(session_id)

    def cleanup_expired_sessions(self, older_than_hours: int = 24) -> int:
        """
        清理过期会话

        Args:
            older_than_hours: 多少小时前的会话

        Returns:
            int: 清理的会话数
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        expired_sessions = []

        with self._lock:
            for session_id, state in self._session_states.items():
                if state.created_at < cutoff_time:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self._session_states[session_id]
                self._active_sessions.discard(session_id)

        if expired_sessions:
            self.logger.info(f"清理了 {len(expired_sessions)} 个过期会话")

        return len(expired_sessions)

    def shutdown(self) -> None:
        """关闭管理器"""
        try:
            with self._lock:
                self._session_states.clear()
                self._active_sessions.clear()

            self.logger.info("优雅降级管理器已关闭")

        except Exception as e:
            self.logger.error(f"关闭优雅降级管理器时出错: {str(e)}")