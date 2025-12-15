"""
重试管理器 (Retry Manager)

该模块负责实现自动重试机制，支持可配置的重试次数和退避策略。
"""

import asyncio
import logging
import random
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, Type
from concurrent.futures import Future
import threading
import weakref

# 导入类型定义
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# 导入错误处理模块的类型
from error_isolation_manager import ErrorInfo, ErrorCategory, ErrorSeverity


class RetryStrategy(Enum):
    """重试策略"""
    IMMEDIATE = "immediate"       # 立即重试
    FIXED_DELAY = "fixed_delay"   # 固定延迟
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    LINEAR_BACKOFF = "linear_backoff"  # 线性退避
    RANDOM_JITTER = "random_jitter"  # 随机抖动
    CUSTOM = "custom"           # 自定义策略


class RetryDecision(Enum):
    """重试决策"""
    RETRY = "retry"             # 继续重试
    ABORT = "abort"             # 中止重试
    SUCCEED = "succeed"         # 标记为成功


@dataclass
class RetryAttempt:
    """重试尝试记录"""
    attempt_number: int
    timestamp: datetime
    error_info: Optional[ErrorInfo] = None
    delay_seconds: float = 0
    success: bool = False
    execution_time: float = 0  # 执行时间(秒)
    result: Any = None


@dataclass
class RetryState:
    """重试状态数据模型"""
    task_id: str
    max_retries: int
    current_attempt: int = 0
    retry_attempts: List[RetryAttempt] = field(default_factory=list)
    next_retry_time: Optional[datetime] = None
    final_result: Optional[str] = None  # "success", "failed", "cancelled"
    total_execution_time: float = 0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.current_attempt < self.max_retries and self.final_result is None

    @property
    def retry_count(self) -> int:
        """已重试次数"""
        return len([a for a in self.retry_attempts if not a.success])

    @property
    def total_attempts(self) -> int:
        """总尝试次数"""
        return len(self.retry_attempts)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if not self.retry_attempts:
            return 0.0
        successful_attempts = sum(1 for a in self.retry_attempts if a.success)
        return successful_attempts / len(self.retry_attempts)


@dataclass
class RetryPolicy:
    """重试策略配置"""
    policy_id: str
    strategy: RetryStrategy
    max_retries: int = 3
    base_delay: float = 1.0  # 基础延迟(秒)
    max_delay: float = 60.0  # 最大延迟(秒)
    multiplier: float = 2.0  # 退避倍数
    jitter: bool = True       # 是否添加随机抖动
    jitter_range: float = 0.1  # 抖动范围(0-1)
    retryable_errors: List[ErrorCategory] = field(default_factory=list)
    non_retryable_errors: List[ErrorCategory] = field(default_factory=list)
    timeout: Optional[float] = None  # 总超时时间


@dataclass
class RetryConfig:
    """重试配置"""
    enabled: bool = True
    default_policy_id: str = "default"
    policies: Dict[str, RetryPolicy] = field(default_factory=dict)
    global_max_retries: int = 5
    cleanup_interval: int = 3600  # 清理间隔(秒)
    max_retry_states: int = 1000  # 最大重试状态数


class RetryStrategyBase(ABC):
    """重试策略基类"""

    @abstractmethod
    async def calculate_delay(self, attempt: int, base_delay: float, **kwargs) -> float:
        """计算延迟时间"""
        pass

    @abstractmethod
    def should_retry(self, error: Exception, attempt: int, max_retries: int) -> bool:
        """判断是否应该重试"""
        pass


class ImmediateRetryStrategy(RetryStrategyBase):
    """立即重试策略"""

    async def calculate_delay(self, attempt: int, base_delay: float, **kwargs) -> float:
        return 0

    def should_retry(self, error: Exception, attempt: int, max_retries: int) -> bool:
        return attempt < max_retries


class FixedDelayStrategy(RetryStrategyBase):
    """固定延迟策略"""

    async def calculate_delay(self, attempt: int, base_delay: float, **kwargs) -> float:
        return base_delay

    def should_retry(self, error: Exception, attempt: int, max_retries: int) -> bool:
        return attempt < max_retries


class ExponentialBackoffStrategy(RetryStrategyBase):
    """指数退避策略"""

    def __init__(self, multiplier: float = 2.0, max_delay: float = 60.0, jitter: bool = True):
        self.multiplier = multiplier
        self.max_delay = max_delay
        self.jitter = jitter

    async def calculate_delay(self, attempt: int, base_delay: float, **kwargs) -> float:
        delay = base_delay * (self.multiplier ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            # 添加随机抖动，避免重试风暴
            jitter_range = kwargs.get('jitter_range', 0.1)
            jitter_amount = delay * jitter_range * (random.random() * 2 - 1)
            delay = max(0, delay + jitter_amount)

        return delay

    def should_retry(self, error: Exception, attempt: int, max_retries: int) -> bool:
        return attempt < max_retries


class LinearBackoffStrategy(RetryStrategyBase):
    """线性退避策略"""

    async def calculate_delay(self, attempt: int, base_delay: float, **kwargs) -> float:
        delay = base_delay * attempt
        max_delay = kwargs.get('max_delay', 60.0)
        return min(delay, max_delay)

    def should_retry(self, error: Exception, attempt: int, max_retries: int) -> bool:
        return attempt < max_retries


class RandomJitterStrategy(RetryStrategyBase):
    """随机抖动策略"""

    async def calculate_delay(self, attempt: int, base_delay: float, **kwargs) -> float:
        min_delay = kwargs.get('min_delay', 0.1)
        max_delay = kwargs.get('max_delay', base_delay * 2)
        return random.uniform(min_delay, max_delay)

    def should_retry(self, error: Exception, attempt: int, max_retries: int) -> bool:
        return attempt < max_retries


class RetryManager:
    """
    重试管理器

    负责管理任务的自动重试，支持多种重试策略和配置。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化重试管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 重试配置
        self.retry_config = RetryConfig(
            enabled=self.config.get('enabled', True),
            default_policy_id=self.config.get('default_policy_id', 'default'),
            global_max_retries=self.config.get('global_max_retries', 5),
            cleanup_interval=self.config.get('cleanup_interval', 3600),
            max_retry_states=self.config.get('max_retry_states', 1000)
        )

        # 内部状态
        self._retry_states: Dict[str, RetryState] = {}
        self._policies: Dict[str, RetryPolicy] = {}
        self._strategies: Dict[RetryStrategy, RetryStrategyBase] = {}
        self._active_retries: Dict[str, Future] = {}
        self._retry_callbacks: Dict[str, List[Callable]] = {}

        # 线程安全锁
        self._lock = threading.RLock()

        # 初始化默认策略
        self._initialize_default_policies()

        # 初始化策略实例
        self._initialize_strategies()

        # 启动清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_active = False

        # 注册清理函数
        import atexit
        atexit.register(self.shutdown)

    def _initialize_default_policies(self) -> None:
        """初始化默认重试策略"""
        default_policies = [
            RetryPolicy(
                policy_id="default",
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=3,
                base_delay=1.0,
                max_delay=60.0,
                multiplier=2.0,
                jitter=True,
                retryable_errors=[
                    ErrorCategory.NETWORK,
                    ErrorCategory.API_LIMIT,
                    ErrorCategory.TIMEOUT
                ]
            ),
            RetryPolicy(
                policy_id="aggressive",
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=5,
                base_delay=0.5,
                max_delay=30.0,
                multiplier=1.5,
                jitter=True
            ),
            RetryPolicy(
                policy_id="conservative",
                strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retries=2,
                base_delay=5.0,
                max_delay=60.0,
                jitter=False,
                retryable_errors=[ErrorCategory.NETWORK]
            ),
            RetryPolicy(
                policy_id="immediate",
                strategy=RetryStrategy.IMMEDIATE,
                max_retries=3,
                base_delay=0,
                jitter=False
            ),
            RetryPolicy(
                policy_id="no_retry",
                strategy=RetryStrategy.FIXED_DELAY,
                max_retries=0,
                base_delay=0,
                jitter=False
            )
        ]

        for policy in default_policies:
            self._policies[policy.policy_id] = policy

    def _initialize_strategies(self) -> None:
        """初始化策略实例"""
        self._strategies = {
            RetryStrategy.IMMEDIATE: ImmediateRetryStrategy(),
            RetryStrategy.FIXED_DELAY: FixedDelayStrategy(),
            RetryStrategy.EXPONENTIAL_BACKOFF: ExponentialBackoffStrategy(),
            RetryStrategy.LINEAR_BACKOFF: LinearBackoffStrategy(),
            RetryStrategy.RANDOM_JITTER: RandomJitterStrategy()
        }

    async def start_cleanup_task(self) -> None:
        """启动清理任务"""
        if self._cleanup_active:
            return

        self._cleanup_active = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("重试管理器清理任务已启动")

    async def stop_cleanup_task(self) -> None:
        """停止清理任务"""
        self._cleanup_active = False
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("重试管理器清理任务已停止")

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while self._cleanup_active:
            try:
                await self._cleanup_expired_states()
                await asyncio.sleep(self.retry_config.cleanup_interval)
            except Exception as e:
                self.logger.error(f"清理循环错误: {str(e)}")
                await asyncio.sleep(60)

    async def _cleanup_expired_states(self) -> None:
        """清理过期的重试状态"""
        current_time = datetime.now()
        expired_threshold = timedelta(hours=24)  # 24小时前的状态
        expired_states = []

        with self._lock:
            for task_id, state in self._retry_states.items():
                # 清理已完成且超过24小时的状态
                if (state.final_result and
                    current_time - state.created_at > expired_threshold):
                    expired_states.append(task_id)

                # 清理数量超限的状态
                elif len(self._retry_states) > self.retry_config.max_retry_states:
                    # 保留最近的状态
                    if state not in sorted(
                        self._retry_states.values(),
                        key=lambda s: s.created_at,
                        reverse=True
                    )[:self.retry_config.max_retry_states]:
                        expired_states.append(task_id)

        # 删除过期状态
        for task_id in expired_states:
            with self._lock:
                self._retry_states.pop(task_id, None)
                self._active_retries.pop(task_id, None)
                self._retry_callbacks.pop(task_id, None)

        if expired_states:
            self.logger.info(f"清理了 {len(expired_states)} 个过期重试状态")

    def add_policy(self, policy: RetryPolicy) -> None:
        """
        添加重试策略

        Args:
            policy: 重试策略
        """
        with self._lock:
            self._policies[policy.policy_id] = policy
        self.logger.info(f"已添加重试策略: {policy.policy_id}")

    def get_policy(self, policy_id: str) -> Optional[RetryPolicy]:
        """
        获取重试策略

        Args:
            policy_id: 策略ID

        Returns:
            Optional[RetryPolicy]: 重试策略
        """
        return self._policies.get(policy_id)

    async def execute_with_retry(self,
                                task_id: str,
                                operation: Callable,
                                *args,
                                policy_id: Optional[str] = None,
                                **kwargs) -> Any:
        """
        执行带重试的操作

        Args:
            task_id: 任务ID
            operation: 要执行的操作
            *args: 操作参数
            policy_id: 重试策略ID
            **kwargs: 操作关键字参数

        Returns:
            Any: 操作结果

        Raises:
            Exception: 最后一次执行的异常
        """
        if not self.retry_config.enabled:
            # 如果重试被禁用，直接执行
            return await self._execute_operation(operation, *args, **kwargs)

        # 获取重试策略
        policy_id = policy_id or self.retry_config.default_policy_id
        policy = self._policies.get(policy_id)
        if not policy:
            raise ValueError(f"未找到重试策略: {policy_id}")

        # 创建重试状态
        retry_state = RetryState(
            task_id=task_id,
            max_retries=min(policy.max_retries, self.retry_config.global_max_retries),
            strategy=policy.strategy
        )

        with self._lock:
            self._retry_states[task_id] = retry_state

        try:
            # 执行重试循环
            result = await self._retry_loop(retry_state, operation, policy, *args, **kwargs)

            # 标记成功
            retry_state.final_result = "success"

            # 调用成功回调
            await self._call_callbacks(task_id, "success", result)

            return result

        except Exception as e:
            # 标记失败
            retry_state.final_result = "failed"

            # 调用失败回调
            await self._call_callbacks(task_id, "failed", e)

            raise

        finally:
            # 清理活跃重试
            with self._lock:
                self._active_retries.pop(task_id, None)

    async def _retry_loop(self,
                          retry_state: RetryState,
                          operation: Callable,
                          policy: RetryPolicy,
                          *args,
                          **kwargs) -> Any:
        """重试循环"""
        last_error = None

        while retry_state.can_retry:
            retry_state.current_attempt += 1
            attempt_start = time.time()

            try:
                # 执行操作
                result = await self._execute_operation(operation, *args, **kwargs)

                # 记录成功的尝试
                attempt = RetryAttempt(
                    attempt_number=retry_state.current_attempt,
                    timestamp=datetime.now(),
                    success=True,
                    execution_time=time.time() - attempt_start,
                    result=result
                )
                retry_state.retry_attempts.append(attempt)

                self.logger.info(
                    f"操作成功 - 任务: {retry_state.task_id}, "
                    f"尝试: {retry_state.current_attempt}, "
                    f"耗时: {attempt.execution_time:.2f}秒"
                )

                return result

            except Exception as e:
                execution_time = time.time() - attempt_start
                last_error = e

                # 创建错误信息
                error_info = self._create_error_info(e, retry_state.task_id)

                # 记录失败的尝试
                attempt = RetryAttempt(
                    attempt_number=retry_state.current_attempt,
                    timestamp=datetime.now(),
                    error_info=error_info,
                    success=False,
                    execution_time=execution_time
                )
                retry_state.retry_attempts.append(attempt)

                # 判断是否应该重试
                should_retry = await self._should_retry(error_info, retry_state, policy)

                if not should_retry or not retry_state.can_retry:
                    self.logger.error(
                        f"操作失败，停止重试 - 任务: {retry_state.task_id}, "
                        f"尝试: {retry_state.current_attempt}, "
                        f"错误: {str(e)}"
                    )
                    break

                # 计算延迟时间
                strategy = self._strategies.get(policy.strategy)
                if strategy:
                    delay = await strategy.calculate_delay(
                        retry_state.current_attempt,
                        policy.base_delay,
                        max_delay=policy.max_delay,
                        jitter_range=policy.jitter_range
                    )
                else:
                    delay = policy.base_delay

                retry_state.next_retry_time = datetime.now() + timedelta(seconds=delay)

                self.logger.warning(
                    f"操作失败，准备重试 - 任务: {retry_state.task_id}, "
                    f"尝试: {retry_state.current_attempt}, "
                    f"延迟: {delay:.2f}秒, "
                    f"错误: {str(e)}"
                )

                # 等待延迟
                if delay > 0:
                    await asyncio.sleep(delay)

        # 重试次数用尽，抛出最后一个错误
        raise last_error if last_error else Exception("重试失败")

    async def _execute_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """执行操作"""
        if asyncio.iscoroutinefunction(operation):
            return await operation(*args, **kwargs)
        else:
            # 在线程池中执行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, operation, *args, **kwargs)

    def _create_error_info(self, error: Exception, task_id: str) -> ErrorInfo:
        """创建错误信息"""
        error_type = type(error).__name__
        error_category = self._categorize_error(error)

        return ErrorInfo(
            error_id=f"retry_{task_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            error_code=error_type,
            error_message=str(error),
            error_category=error_category,
            severity=self._get_error_severity(error),
            task_id=task_id,
            stack_trace=traceback.format_exc() if hasattr(error, '__traceback__') else None
        )

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """错误分类"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        if 'timeout' in error_type.lower() or 'timeout' in error_message:
            return ErrorCategory.TIMEOUT
        elif 'connection' in error_type.lower() or 'network' in error_message:
            return ErrorCategory.NETWORK
        elif 'api' in error_message or 'rate' in error_message or 'limit' in error_message:
            return ErrorCategory.API_LIMIT
        elif 'memory' in error_message or 'overflow' in error_message:
            return ErrorCategory.MEMORY_OVERFLOW
        elif 'validation' in error_type.lower() or 'invalid' in error_message:
            return ErrorCategory.VALIDATION
        else:
            return ErrorCategory.SYSTEM

    def _get_error_severity(self, error: Exception) -> ErrorSeverity:
        """获取错误严重程度"""
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.HIGH

    async def _should_retry(self,
                           error_info: ErrorInfo,
                           retry_state: RetryState,
                           policy: RetryPolicy) -> bool:
        """判断是否应该重试"""
        # 检查是否在不可重试的错误列表中
        if error_info.error_category in policy.non_retryable_errors:
            return False

        # 如果有可重试错误列表，检查是否在其中
        if policy.retryable_errors:
            if error_info.error_category not in policy.retryable_errors:
                return False

        # 使用策略判断
        strategy = self._strategies.get(policy.strategy)
        if strategy:
            return strategy.should_retry(
                Exception(error_info.error_message),
                retry_state.retry_count,
                retry_state.max_retries
            )

        return retry_state.can_retry

    def add_retry_callback(self, task_id: str, callback: Callable) -> None:
        """
        添加重试回调

        Args:
            task_id: 任务ID
            callback: 回调函数
        """
        with self._lock:
            if task_id not in self._retry_callbacks:
                self._retry_callbacks[task_id] = []
            self._retry_callbacks[task_id].append(callback)

    async def _call_callbacks(self, task_id: str, event: str, data: Any) -> None:
        """调用回调函数"""
        callbacks = self._retry_callbacks.get(task_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_id, event, data)
                else:
                    callback(task_id, event, data)
            except Exception as e:
                self.logger.error(f"重试回调执行失败: {str(e)}")

    async def should_retry(self, error_info: ErrorInfo, retry_state: RetryState) -> bool:
        """
        判断是否应该重试（外部接口）

        Args:
            error_info: 错误信息
            retry_state: 重试状态

        Returns:
            bool: 是否应该重试
        """
        policy = self._policies.get(self.retry_config.default_policy_id)
        if not policy:
            return False

        return await self._should_retry(error_info, retry_state, policy)

    async def calculate_backoff_delay(self, attempt: int, base_delay: float = 1.0) -> float:
        """
        计算退避延迟时间

        Args:
            attempt: 尝试次数
            base_delay: 基础延迟

        Returns:
            float: 延迟时间（秒）
        """
        policy = self._policies.get(self.retry_config.default_policy_id)
        if not policy:
            return base_delay

        strategy = self._strategies.get(policy.strategy)
        if strategy:
            return await strategy.calculate_delay(attempt, base_delay)

        return base_delay

    async def get_retry_status(self, task_id: str) -> Optional[RetryState]:
        """
        获取重试状态

        Args:
            task_id: 任务ID

        Returns:
            Optional[RetryState]: 重试状态
        """
        with self._lock:
            return self._retry_states.get(task_id)

    async def cancel_retry(self, task_id: str) -> bool:
        """
        取消重试

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        try:
            with self._lock:
                retry_state = self._retry_states.get(task_id)
                if retry_state:
                    retry_state.final_result = "cancelled"

                # 取消活跃的重试任务
                future = self._active_retries.get(task_id)
                if future and not future.done():
                    future.cancel()

            self.logger.info(f"已取消重试 - 任务: {task_id}")
            return True

        except Exception as e:
            self.logger.error(f"取消重试失败 - 任务: {task_id}: {str(e)}")
            return False

    def get_retry_statistics(self) -> Dict[str, Any]:
        """
        获取重试统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            total_states = len(self._retry_states)
            active_retries = len([
                s for s in self._retry_states.values()
                if s.final_result is None
            ])
            successful_retries = len([
                s for s in self._retry_states.values()
                if s.final_result == "success"
            ])
            failed_retries = len([
                s for s in self._retry_states.values()
                if s.final_result == "failed"
            ])

            # 计算平均重试次数
            retry_counts = [
                s.retry_count for s in self._retry_states.values()
                if s.retry_count > 0
            ]
            avg_retries = sum(retry_counts) / len(retry_counts) if retry_counts else 0

            # 按策略统计
            strategy_stats = {}
            for state in self._retry_states.values():
                strategy = state.strategy.value
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        'total': 0,
                        'success': 0,
                        'failed': 0
                    }
                strategy_stats[strategy]['total'] += 1
                if state.final_result == "success":
                    strategy_stats[strategy]['success'] += 1
                elif state.final_result == "failed":
                    strategy_stats[strategy]['failed'] += 1

            return {
                'total_tasks': total_states,
                'active_retries': active_retries,
                'successful_retries': successful_retries,
                'failed_retries': failed_retries,
                'success_rate': successful_retries / total_states if total_states > 0 else 0,
                'average_retries': avg_retries,
                'strategy_statistics': strategy_stats,
                'policies_count': len(self._policies),
                'last_updated': datetime.now().isoformat()
            }

    def shutdown(self) -> None:
        """关闭重试管理器"""
        try:
            # 停止清理任务
            if self._cleanup_active:
                asyncio.create_task(self.stop_cleanup_task())

            # 取消所有活跃的重试
            with self._lock:
                for future in self._active_retries.values():
                    if not future.done():
                        future.cancel()
                self._active_retries.clear()

            # 清理状态
            self._retry_states.clear()
            self._retry_callbacks.clear()

            self.logger.info("重试管理器已关闭")

        except Exception as e:
            self.logger.error(f"关闭重试管理器时出错: {str(e)}")


