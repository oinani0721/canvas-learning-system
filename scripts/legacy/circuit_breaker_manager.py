"""
熔断器管理器 (Circuit Breaker Manager)

该模块负责实现circuit breaker模式，防止级联失败。
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from concurrent.futures import Future
import threading
import weakref
from collections import deque

# 导入类型定义
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# 导入其他模块的类型
from error_isolation_manager import ErrorInfo, ErrorCategory, ErrorSeverity


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 关闭状态（正常）
    OPEN = "open"          # 打开状态（熔断）
    HALF_OPEN = "half_open"  # 半开状态（尝试恢复）


class FailureType(Enum):
    """失败类型"""
    TIMEOUT = "timeout"
    EXCEPTION = "exception"
    ERROR_CODE = "error_code"
    SLOW_RESPONSE = "slow_response"


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5        # 失败阈值
    success_threshold: int = 3        # 成功阈值（半开状态）
    recovery_timeout: float = 60.0    # 恢复超时（秒）
    monitoring_window: int = 300      # 监控窗口（秒）
    timeout: float = 30.0            # 请求超时（秒）
    slow_response_threshold: float = 5.0  # 慢响应阈值（秒）
    auto_reset: bool = True          # 自动重置
    max_requests: int = 1000         # 窗口内最大请求数


@dataclass
class CircuitBreakerMetrics:
    """熔断器指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeouts: int = 0
    slow_responses: int = 0
    average_response_time: float = 0.0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    failure_rate: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class CircuitBreakerEvent:
    """熔断器事件"""
    timestamp: datetime
    event_type: str  # "state_change", "failure", "success", "timeout"
    service_name: str
    old_state: Optional[CircuitState] = None
    new_state: Optional[CircuitState] = None
    error_info: Optional[ErrorInfo] = None
    response_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """
    熔断器实现

    单个服务的熔断器实例。
    """

    def __init__(self, service_name: str, config: CircuitBreakerConfig):
        """
        初始化熔断器

        Args:
            service_name: 服务名称
            config: 熔断器配置
        """
        self.service_name = service_name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker.{service_name}")

        # 状态
        self.state = CircuitState.CLOSED
        self.state_changed_time = datetime.now()
        self.metrics = CircuitBreakerMetrics()
        self.events: List[CircuitBreakerEvent] = []

        # 线程安全
        self._lock = threading.RLock()

        # 失败记录（用于滑动窗口）
        self._failure_record: deque = deque(maxlen=config.max_requests)
        self._success_record: deque = deque(maxlen=config.max_requests)

        # 回调函数
        self._state_change_callbacks: List[Callable[[CircuitState, CircuitState], None]] = []

    def add_state_change_callback(self, callback: Callable[[CircuitState, CircuitState], None]) -> None:
        """
        添加状态变化回调

        Args:
            callback: 回调函数
        """
        self._state_change_callbacks.append(callback)

    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用服务

        Args:
            operation: 要执行的操作
            *args: 操作参数
            **kwargs: 操作关键字参数

        Returns:
            Any: 操作结果

        Raises:
            Exception: 相应的异常
        """
        # 检查熔断器状态
        if not self._can_execute():
            raise CircuitBreakerOpenException(f"熔断器打开，拒绝调用 - 服务: {self.service_name}")

        # 记录请求开始
        start_time = time.time()

        try:
            # 执行操作
            if asyncio.iscoroutinefunction(operation):
                result = await asyncio.wait_for(
                    operation(*args, **kwargs),
                    timeout=self.config.timeout
                )
            else:
                # 在线程池中执行同步函数
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._execute_with_timeout(operation, args, kwargs)
                )

            # 记录成功
            response_time = time.time() - start_time
            self._record_success(response_time)

            # 检查是否是慢响应
            if response_time > self.config.slow_response_threshold:
                self._record_slow_response(response_time)

            return result

        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self._record_timeout(response_time)
            raise CircuitBreakerTimeoutException(f"调用超时 - 服务: {self.service_name}")

        except Exception as e:
            response_time = time.time() - start_time
            self._record_failure(e, response_time)
            raise

    def _execute_with_timeout(self, operation: Callable, args: tuple, kwargs: dict) -> Any:
        """执行同步操作并处理超时"""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Operation timed out")

        # 设置超时信号
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.config.timeout))

        try:
            result = operation(*args, **kwargs)
            signal.alarm(0)  # 取消超时
            return result
        finally:
            signal.signal(signal.SIGALRM, old_handler)  # 恢复原处理器

    def _can_execute(self) -> bool:
        """检查是否可以执行请求"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                # 检查是否可以尝试恢复
                elapsed = (datetime.now() - self.state_changed_time).total_seconds()
                if elapsed >= self.config.recovery_timeout:
                    self._change_state(CircuitState.HALF_OPEN)
                    return True
                return False
            else:  # HALF_OPEN
                return True

    def _record_success(self, response_time: float) -> None:
        """记录成功"""
        with self._lock:
            now = datetime.now()
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = now
            self.metrics.response_times.append(response_time)
            self.metrics.average_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times)

            # 更新成功率记录
            self._success_record.append(now)

            # 清理过期记录
            self._cleanup_old_records()

            # 在半开状态下，成功达到阈值则关闭熔断器
            if self.state == CircuitState.HALF_OPEN:
                recent_successes = len([
                    t for t in self._success_record
                    if (now - t).total_seconds() <= self.config.monitoring_window
                ])
                if recent_successes >= self.config.success_threshold:
                    self._change_state(CircuitState.CLOSED)

            # 记录事件
            self._record_event("success", response_time=response_time)

    def _record_failure(self, error: Exception, response_time: float) -> None:
        """记录失败"""
        with self._lock:
            now = datetime.now()
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = now
            self.metrics.response_times.append(response_time)
            self.metrics.average_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times)

            # 更新失败记录
            self._failure_record.append(now)

            # 清理过期记录
            self._cleanup_old_records()

            # 计算失败率
            self._update_failure_rate()

            # 检查是否需要打开熔断器
            if self.state == CircuitState.CLOSED:
                if self.metrics.failure_rate >= (self.config.failure_threshold / 100):
                    self._change_state(CircuitState.OPEN)
            elif self.state == CircuitState.HALF_OPEN:
                # 半开状态下任何失败都会重新打开熔断器
                self._change_state(CircuitState.OPEN)

            # 创建错误信息
            error_info = ErrorInfo(
                error_id=f"cb_{self.service_name}_{int(now.timestamp())}",
                error_code=type(error).__name__,
                error_message=str(error),
                error_category=self._categorize_error(error),
                severity=ErrorSeverity.MEDIUM
            )

            # 记录事件
            self._record_event("failure", error_info=error_info, response_time=response_time)

    def _record_timeout(self, response_time: float) -> None:
        """记录超时"""
        with self._lock:
            now = datetime.now()
            self.metrics.total_requests += 1
            self.metrics.timeouts += 1
            self.metrics.last_failure_time = now
            self.metrics.response_times.append(response_time)
            self.metrics.average_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times)

            # 更新失败记录
            self._failure_record.append(now)

            # 清理过期记录
            self._cleanup_old_records()

            # 计算失败率
            self._update_failure_rate()

            # 超时视为失败，检查是否需要打开熔断器
            if self.state == CircuitState.CLOSED:
                if self.metrics.failure_rate >= (self.config.failure_threshold / 100):
                    self._change_state(CircuitState.OPEN)
            elif self.state == CircuitState.HALF_OPEN:
                self._change_state(CircuitState.OPEN)

            # 记录事件
            self._record_event("timeout", response_time=response_time)

    def _record_slow_response(self, response_time: float) -> None:
        """记录慢响应"""
        with self._lock:
            self.metrics.slow_responses += 1

            # 记录事件
            self._record_event("slow_response", response_time=response_time)

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """错误分类"""
        error_type = type(error).__name__
        if 'Timeout' in error_type or 'timeout' in str(error).lower():
            return ErrorCategory.TIMEOUT
        elif 'Connection' in error_type or 'Network' in str(error):
            return ErrorCategory.NETWORK
        else:
            return ErrorCategory.SYSTEM

    def _cleanup_old_records(self) -> None:
        """清理过期记录"""
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.config.monitoring_window)

        # 清理失败记录
        while self._failure_record and self._failure_record[0] < cutoff_time:
            self._failure_record.popleft()

        # 清理成功记录
        while self._success_record and self._success_record[0] < cutoff_time:
            self._success_record.popleft()

    def _update_failure_rate(self) -> None:
        """更新失败率"""
        total_requests = len(self._failure_record) + len(self._success_record)
        if total_requests > 0:
            self.metrics.failure_rate = (len(self._failure_record) / total_requests) * 100
        else:
            self.metrics.failure_rate = 0

    def _change_state(self, new_state: CircuitState) -> None:
        """改变熔断器状态"""
        old_state = self.state
        self.state = new_state
        self.state_changed_time = datetime.now()

        # 记录事件
        self._record_event("state_change", old_state=old_state, new_state=new_state)

        # 调用回调
        for callback in self._state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                self.logger.error(f"状态变化回调执行失败: {str(e)}")

        self.logger.info(
            f"熔断器状态变化 - 服务: {self.service_name}, "
            f"状态: {old_state.value} -> {new_state.value}"
        )

    def _record_event(self, event_type: str, **kwargs) -> None:
        """记录事件"""
        event = CircuitBreakerEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            service_name=self.service_name,
            **kwargs
        )
        self.events.append(event)

        # 保留最近的事件
        if len(self.events) > 1000:
            self.events = self.events[-1000:]

    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state

    def get_metrics(self) -> CircuitBreakerMetrics:
        """获取指标"""
        with self._lock:
            # 创建副本以避免并发修改
            return CircuitBreakerMetrics(
                total_requests=self.metrics.total_requests,
                successful_requests=self.metrics.successful_requests,
                failed_requests=self.metrics.failed_requests,
                timeouts=self.metrics.timeouts,
                slow_responses=self.metrics.slow_responses,
                average_response_time=self.metrics.average_response_time,
                last_failure_time=self.metrics.last_failure_time,
                last_success_time=self.metrics.last_success_time,
                failure_rate=self.metrics.failure_rate,
                response_times=deque(self.metrics.response_times)
            )

    def get_events(self, limit: int = 100) -> List[CircuitBreakerEvent]:
        """获取事件列表"""
        return self.events[-limit:]

    def reset(self) -> None:
        """重置熔断器"""
        with self._lock:
            self._change_state(CircuitState.CLOSED)
            self.metrics = CircuitBreakerMetrics()
            self._failure_record.clear()
            self._success_record.clear()
            self.events.clear()

        self.logger.info(f"熔断器已重置 - 服务: {self.service_name}")


class CircuitBreakerOpenException(Exception):
    """熔断器打开异常"""
    pass


class CircuitBreakerTimeoutException(Exception):
    """熔断器超时异常"""
    pass


class CircuitBreakerManager:
    """
    熔断器管理器

    管理所有服务的熔断器实例。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化熔断器管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 内部状态
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._global_config = CircuitBreakerConfig(**self.config.get('global', {}))

        # 线程安全
        self._lock = threading.RLock()

        # 监控任务
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None

        # 注册清理函数
        import atexit
        atexit.register(self.shutdown)

    async def create_circuit_breaker(self,
                                    service_name: str,
                                    config: Optional[Dict[str, Any]] = None) -> bool:
        """
        创建熔断器

        Args:
            service_name: 服务名称
            config: 熔断器配置

        Returns:
            bool: 是否成功创建
        """
        with self._lock:
            if service_name in self._circuit_breakers:
                self.logger.warning(f"熔断器已存在 - 服务: {service_name}")
                return False

            # 合并配置
            if config:
                cb_config = CircuitBreakerConfig(**{**self._global_config.__dict__, **config})
            else:
                cb_config = self._global_config

            # 创建熔断器
            circuit_breaker = CircuitBreaker(service_name, cb_config)
            self._circuit_breakers[service_name] = circuit_breaker

            self.logger.info(f"已创建熔断器 - 服务: {service_name}")
            return True

    async def call_through_circuit_breaker(self,
                                          service_name: str,
                                          operation: Callable,
                                          *args,
                                          **kwargs) -> Any:
        """
        通过熔断器调用服务

        Args:
            service_name: 服务名称
            operation: 要执行的操作
            *args: 操作参数
            **kwargs: 操作关键字参数

        Returns:
            Any: 操作结果
        """
        circuit_breaker = self._get_circuit_breaker(service_name)
        if not circuit_breaker:
            # 如果熔断器不存在，直接执行
            if asyncio.iscoroutinefunction(operation):
                return await operation(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, operation, *args, **kwargs)

        return await circuit_breaker.call(operation, *args, **kwargs)

    def _get_circuit_breaker(self, service_name: str) -> Optional[CircuitBreaker]:
        """获取熔断器"""
        with self._lock:
            return self._circuit_breakers.get(service_name)

    async def get_circuit_state(self, service_name: str) -> Optional[CircuitState]:
        """
        获取熔断器状态

        Args:
            service_name: 服务名称

        Returns:
            Optional[CircuitState]: 熔断器状态
        """
        circuit_breaker = self._get_circuit_breaker(service_name)
        return circuit_breaker.get_state() if circuit_breaker else None

    async def reset_circuit_breaker(self, service_name: str) -> bool:
        """
        重置熔断器状态

        Args:
            service_name: 服务名称

        Returns:
            bool: 是否成功重置
        """
        circuit_breaker = self._get_circuit_breaker(service_name)
        if circuit_breaker:
            circuit_breaker.reset()
            return True
        return False

    async def get_all_circuit_states(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有熔断器状态

        Returns:
            Dict[str, Dict[str, Any]]: 所有熔断器的状态信息
        """
        states = {}
        with self._lock:
            for service_name, circuit_breaker in self._circuit_breakers.items():
                metrics = circuit_breaker.get_metrics()
                states[service_name] = {
                    'state': circuit_breaker.get_state().value,
                    'state_changed_time': circuit_breaker.state_changed_time.isoformat(),
                    'metrics': {
                        'total_requests': metrics.total_requests,
                        'successful_requests': metrics.successful_requests,
                        'failed_requests': metrics.failed_requests,
                        'timeouts': metrics.timeouts,
                        'slow_responses': metrics.slow_responses,
                        'failure_rate': metrics.failure_rate,
                        'average_response_time': metrics.average_response_time
                    }
                }

        return states

    async def start_monitoring(self) -> None:
        """启动监控"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("熔断器监控已启动")

    async def stop_monitoring(self) -> None:
        """停止监控"""
        self._monitoring_active = False
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("熔断器监控已停止")

    async def _monitoring_loop(self) -> None:
        """监控循环"""
        while self._monitoring_active:
            try:
                # 检查所有熔断器状态
                await self._check_circuit_health()

                # 等待下一次检查
                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                self.logger.error(f"熔断器监控错误: {str(e)}")
                await asyncio.sleep(10)

    async def _check_circuit_health(self) -> None:
        """检查熔断器健康状态"""
        with self._lock:
            for service_name, circuit_breaker in self._circuit_breakers.items():
                metrics = circuit_breaker.get_metrics()
                state = circuit_breaker.get_state()

                # 检查异常情况
                if state == CircuitState.OPEN:
                    # 检查是否长时间处于打开状态
                    open_duration = (datetime.now() - circuit_breaker.state_changed_time).total_seconds()
                    if open_duration > self._global_config.recovery_timeout * 2:
                        self.logger.warning(
                            f"熔断器长时间处于打开状态 - 服务: {service_name}, "
                            f"持续时间: {open_duration:.1f}秒"
                        )

                # 检查高失败率
                if metrics.failure_rate > 50:
                    self.logger.warning(
                        f"服务失败率过高 - 服务: {service_name}, "
                        f"失败率: {metrics.failure_rate:.1f}%"
                    )

                # 检查慢响应
                if metrics.slow_responses > metrics.total_requests * 0.3:
                    self.logger.warning(
                        f"服务响应过慢 - 服务: {service_name}, "
                        f"慢响应数: {metrics.slow_responses}, "
                        f"总请求数: {metrics.total_requests}"
                    )

    def get_service_statistics(self) -> Dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            total_circuits = len(self._circuit_breakers)
            open_circuits = sum(
                1 for cb in self._circuit_breakers.values()
                if cb.get_state() == CircuitState.OPEN
            )
            half_open_circuits = sum(
                1 for cb in self._circuit_breakers.values()
                if cb.get_state() == CircuitState.HALF_OPEN
            )
            closed_circuits = total_circuits - open_circuits - half_open_circuits

            # 计算总体指标
            total_requests = sum(
                cb.get_metrics().total_requests
                for cb in self._circuit_breakers.values()
            )
            total_failures = sum(
                cb.get_metrics().failed_requests + cb.get_metrics().timeouts
                for cb in self._circuit_breakers.values()
            )
            overall_failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

            return {
                'total_circuits': total_circuits,
                'circuits_by_state': {
                    'open': open_circuits,
                    'half_open': half_open_circuits,
                    'closed': closed_circuits
                },
                'overall_metrics': {
                    'total_requests': total_requests,
                    'total_failures': total_failures,
                    'failure_rate': overall_failure_rate
                },
                'services': list(self._circuit_breakers.keys()),
                'last_updated': datetime.now().isoformat()
            }

    async def export_metrics(self) -> Dict[str, Any]:
        """
        导出指标数据

        Returns:
            Dict[str, Any]: 指标数据
        """
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }

        with self._lock:
            for service_name, circuit_breaker in self._circuit_breakers.items():
                metrics = circuit_breaker.get_metrics()
                metrics_data['services'][service_name] = {
                    'state': circuit_breaker.get_state().value,
                    'state_changed_time': circuit_breaker.state_changed_time.isoformat(),
                    'total_requests': metrics.total_requests,
                    'successful_requests': metrics.successful_requests,
                    'failed_requests': metrics.failed_requests,
                    'timeouts': metrics.timeouts,
                    'slow_responses': metrics.slow_responses,
                    'failure_rate': metrics.failure_rate,
                    'average_response_time': metrics.average_response_time,
                    'last_failure_time': metrics.last_failure_time.isoformat() if metrics.last_failure_time else None,
                    'last_success_time': metrics.last_success_time.isoformat() if metrics.last_success_time else None
                }

        return metrics_data

    def shutdown(self) -> None:
        """关闭管理器"""
        try:
            # 停止监控
            if self._monitoring_active:
                asyncio.create_task(self.stop_monitoring())

            # 清理熔断器
            with self._lock:
                self._circuit_breakers.clear()

            self.logger.info("熔断器管理器已关闭")

        except Exception as e:
            self.logger.error(f"关闭熔断器管理器时出错: {str(e)}")