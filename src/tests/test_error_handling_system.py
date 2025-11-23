"""
错误处理和故障恢复系统测试

测试错误隔离、重试机制、优雅降级、错误日志和熔断器功能。
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# 导入要测试的模块
from error_isolation_manager import (
    ErrorIsolationManager, ErrorInfo, ErrorCategory, ErrorSeverity,
    InstanceInfo, IsolationLevel
)
from retry_manager import (
    RetryManager, RetryPolicy, RetryStrategy, RetryState
)
from graceful_degradation_manager import (
    GracefulDegradationManager, ProcessingTask, DegradationLevel
)
from error_logger import ErrorLogger, DiagnosticCollector, LogLevel, DiagnosticLevel
from circuit_breaker_manager import (
    CircuitBreakerManager, CircuitBreakerConfig, CircuitState
)


@pytest.fixture
def temp_dir():
    """临时目录"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def error_isolation_config():
    """错误隔离配置"""
    return {
        'monitoring_interval': 1,
        'heartbeat_timeout': 5,
        'error_rate_threshold': 0.1,
        'max_recovery_attempts': 2
    }


@pytest.fixture
def retry_config():
    """重试配置"""
    return {
        'enabled': True,
        'default_policy_id': 'test',
        'global_max_retries': 3,
        'cleanup_interval': 1
    }


@pytest.fixture
def logger_config(temp_dir):
    """日志配置"""
    return {
        'log_dir': str(temp_dir / 'logs' / 'errors'),
        'diagnostic_dir': str(temp_dir / 'logs' / 'diagnostics'),
        'max_log_size': 1024 * 1024,  # 1MB
        'async_logging': False  # 测试时禁用异步
    }


class TestErrorIsolationManager:
    """测试错误隔离管理器"""

    @pytest.fixture
    def manager(self, error_isolation_config):
        return ErrorIsolationManager(error_isolation_config)

    def test_initialization(self, manager):
        """测试初始化"""
        assert manager is not None
        assert len(manager._isolation_policies) > 0
        assert len(manager._propagation_rules) > 0

    def test_register_instance(self, manager):
        """测试注册实例"""
        instance = InstanceInfo(
            instance_id="test-instance-1",
            instance_type="agent",
            status="active",
            created_at=datetime.now(),
            last_heartbeat=datetime.now()
        )
        result = manager.register_instance(instance)
        assert result is True
        assert "test-instance-1" in manager._registered_instances

    def test_quarantine_instance(self, manager):
        """测试隔离实例"""
        # 先注册实例
        instance = InstanceInfo(
            instance_id="test-instance-2",
            instance_type="agent",
            status="active",
            created_at=datetime.now(),
            last_heartbeat=datetime.now()
        )
        manager.register_instance(instance)

        # 隔离实例
        result = asyncio.run(manager.quarantine_instance(
            "test-instance-2",
            "测试隔离"
        ))
        assert result is True
        assert "test-instance-2" in manager._quarantined_instances

    def test_error_propagation_control(self, manager):
        """测试错误传播控制"""
        error_info = ErrorInfo(
            error_id="test-error-1",
            error_code="TEST_ERROR",
            error_message="测试错误",
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            instance_id="test-instance-1"
        )

        # 测试阻止传播
        result = asyncio.run(manager.check_error_propagation(
            error_info,
            "target-instance"
        ))
        # 根据默认规则，网络错误可能被允许传播
        assert isinstance(result, bool)

    def test_fault_detection(self, manager):
        """测试故障检测"""
        # 注册一个实例
        instance = InstanceInfo(
            instance_id="test-instance-3",
            instance_type="agent",
            status="active",
            created_at=datetime.now(),
            last_heartbeat=datetime.now() - timedelta(minutes=5)  # 模拟心跳超时
        )
        manager.register_instance(instance)

        # 检测故障实例
        fault_instances = asyncio.run(manager.detect_fault_instances())
        # 心跳超时的实例应该被检测到
        assert "test-instance-3" in fault_instances

    def test_get_error_statistics(self, manager):
        """测试获取错误统计"""
        stats = manager.get_error_statistics()
        assert 'total_instances' in stats
        assert 'quarantined_instances' in stats
        assert 'error_distribution' in stats


class TestRetryManager:
    """测试重试管理器"""

    @pytest.fixture
    def manager(self, retry_config):
        return RetryManager(retry_config)

    def test_initialization(self, manager):
        """测试初始化"""
        assert manager is not None
        assert len(manager._policies) > 0
        assert len(manager._strategies) > 0

    def test_add_policy(self, manager):
        """测试添加重试策略"""
        policy = RetryPolicy(
            policy_id="test-policy",
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=5,
            base_delay=0.5
        )
        manager.add_policy(policy)
        assert "test-policy" in manager._policies

    def test_successful_operation(self, manager):
        """测试成功操作（不需要重试）"""
        async def successful_operation():
            return "success"

        result = asyncio.run(manager.execute_with_retry(
            "test-task-1",
            successful_operation,
            policy_id="default"
        ))
        assert result == "success"

    def test_retry_on_failure(self, manager):
        """测试失败重试"""
        call_count = 0

        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("测试失败")
            return "success after retry"

        result = asyncio.run(manager.execute_with_retry(
            "test-task-2",
            failing_operation,
            policy_id="default"
        ))
        assert result == "success after retry"
        assert call_count == 3

    def test_max_retries_exceeded(self, manager):
        """测试超过最大重试次数"""
        async def always_failing_operation():
            raise ValueError("总是失败")

        with pytest.raises(ValueError):
            asyncio.run(manager.execute_with_retry(
                "test-task-3",
                always_failing_operation,
                policy_id="default"
            ))

    def test_get_retry_statistics(self, manager):
        """测试获取重试统计"""
        stats = manager.get_retry_statistics()
        assert 'total_tasks' in stats
        assert 'active_retries' in stats
        assert 'success_rate' in stats


class TestGracefulDegradationManager:
    """测试优雅降级管理器"""

    @pytest.fixture
    def manager(self):
        return GracefulDegradationManager()

    def test_initialization(self, manager):
        """测试初始化"""
        assert manager is not None
        assert len(manager._degradation_strategies) > 0

    def test_handle_partial_failure(self, manager):
        """测试处理部分失败"""
        completed_tasks = [
            ProcessingTask(
                task_id="task-1",
                task_type="api_call",
                required=True
            ),
            ProcessingTask(
                task_id="task-2",
                task_type="api_call",
                required=False
            )
        ]
        failed_tasks = [
            ProcessingTask(
                task_id="task-3",
                task_type="api_call",
                required=False,
                retry_count=3
            )
        ]

        result = asyncio.run(manager.handle_partial_failure(
            "test-session",
            completed_tasks,
            failed_tasks
        ))
        assert result is not None
        assert result.recovery_success
        assert result.user_notification is not None

    def test_generate_partial_results(self, manager):
        """测试生成部分结果"""
        # 创建会话状态
        session = manager._get_or_create_session("test-session-2")
        session.total_tasks = 5
        session.completed_tasks = 3
        session.failed_tasks = 2

        results = asyncio.run(manager.generate_partial_results("test-session-2"))
        assert results is not None
        assert 'session_id' in results
        assert 'summary' in results

    def test_suggest_recovery_options(self, manager):
        """测试建议恢复选项"""
        failed_tasks = [
            ProcessingTask(
                task_id="task-1",
                task_type="api_call",
                retry_count=0,
                max_retries=3
            ),
            ProcessingTask(
                task_id="task-2",
                task_type="canvas_processing",
                retry_count=3,
                max_retries=3
            )
        ]

        options = asyncio.run(manager.suggest_recovery_options(failed_tasks))
        assert isinstance(options, list)
        assert len(options) > 0

    def test_create_failure_report(self, manager):
        """测试创建失败报告"""
        # 创建会话状态
        session = manager._get_or_create_session("test-session-3")
        session.total_tasks = 10
        session.completed_tasks = 7
        session.failed_tasks = 3

        report = asyncio.run(manager.create_failure_report("test-session-3"))
        assert report is not None
        assert 'session_id' in report
        assert 'task_summary' in report
        assert 'recommendations' in report


class TestErrorLogger:
    """测试错误日志系统"""

    @pytest.fixture
    def logger(self, logger_config):
        return ErrorLogger(logger_config)

    def test_initialization(self, logger):
        """测试初始化"""
        assert logger is not None
        assert logger.log_dir.exists()
        assert logger.diagnostic_dir.exists()

    def test_log_error(self, logger):
        """测试记录错误"""
        error_info = ErrorInfo(
            error_id="test-log-error",
            error_code="LOG_TEST",
            error_message="测试日志错误",
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM
        )

        entry_id = logger.log_error(
            error_info,
            level=LogLevel.ERROR,
            source="test-source",
            tags=["test", "network"]
        )
        assert entry_id is not None
        assert len(entry_id) == 16  # MD5 hash length

    def test_log_entry_persistence(self, logger, temp_dir):
        """测试日志条目持久化"""
        error_info = ErrorInfo(
            error_id="test-persist",
            error_code="PERSIST_TEST",
            error_message="测试持久化",
            error_category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH
        )

        logger.log_error(error_info, source="test-persist")

        # 检查文件是否创建
        log_files = list(logger.log_dir.glob("*.log"))
        assert len(log_files) > 0

        # 检查文件内容
        with open(log_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
            assert "PERSIST_TEST" in content


class TestDiagnosticCollector:
    """测试诊断收集器"""

    @pytest.fixture
    def collector(self, logger_config):
        collector = DiagnosticCollector({
            'diagnostic_dir': logger_config['diagnostic_dir']
        })
        # 设置错误日志记录器
        collector.error_logger = ErrorLogger(logger_config)
        return collector

    def test_initialization(self, collector):
        """测试初始化"""
        assert collector is not None
        assert collector.diagnostic_dir.exists()

    def test_generate_diagnostic_report(self, collector):
        """测试生成诊断报告"""
        # 先添加一些错误日志
        error_info = ErrorInfo(
            error_id="test-diag",
            error_code="DIAG_TEST",
            error_message="测试诊断",
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM
        )
        collector.error_logger.log_error(error_info, source="test-diag")

        # 生成诊断报告
        report = asyncio.run(collector.generate_diagnostic_report(
            diagnostic_level=DiagnosticLevel.BASIC
        ))
        assert report is not None
        assert report.report_id is not None
        assert report.diagnostic_level == DiagnosticLevel.BASIC

    def test_list_diagnostic_reports(self, collector):
        """测试列出诊断报告"""
        # 生成一个报告
        asyncio.run(collector.generate_diagnostic_report())

        # 列出报告
        reports = collector.list_diagnostic_reports()
        assert isinstance(reports, list)
        assert len(reports) > 0


class TestCircuitBreakerManager:
    """测试熔断器管理器"""

    @pytest.fixture
    def manager(self):
        return CircuitBreakerManager()

    def test_initialization(self, manager):
        """测试初始化"""
        assert manager is not None
        assert manager._global_config is not None

    def test_create_circuit_breaker(self, manager):
        """测试创建熔断器"""
        result = asyncio.run(manager.create_circuit_breaker(
            "test-service",
            {
                'failure_threshold': 3,
                'recovery_timeout': 30.0
            }
        ))
        assert result is True
        assert "test-service" in manager._circuit_breakers

    def test_successful_call_through_circuit_breaker(self, manager):
        """测试通过熔断器的成功调用"""
        # 创建熔断器
        asyncio.run(manager.create_circuit_breaker("test-service-2"))

        async def successful_operation():
            return "success"

        result = asyncio.run(manager.call_through_circuit_breaker(
            "test-service-2",
            successful_operation
        ))
        assert result == "success"

    def test_circuit_breaker_open_on_failures(self, manager):
        """测试失败时熔断器打开"""
        # 创建熔断器，设置较低的失败阈值
        asyncio.run(manager.create_circuit_breaker(
            "test-service-3",
            {
                'failure_threshold': 2,
                'recovery_timeout': 1.0
            }
        ))

        async def failing_operation():
            raise ValueError("服务失败")

        # 触发失败
        for _ in range(3):
            try:
                asyncio.run(manager.call_through_circuit_breaker(
                    "test-service-3",
                    failing_operation
                ))
            except ValueError:
                pass

        # 检查熔断器状态
        state = asyncio.run(manager.get_circuit_state("test-service-3"))
        assert state == CircuitState.OPEN

    def test_get_all_circuit_states(self, manager):
        """测试获取所有熔断器状态"""
        # 创建多个熔断器
        asyncio.run(manager.create_circuit_breaker("service-1"))
        asyncio.run(manager.create_circuit_breaker("service-2"))

        states = asyncio.run(manager.get_all_circuit_states())
        assert isinstance(states, dict)
        assert "service-1" in states
        assert "service-2" in states

    def test_get_service_statistics(self, manager):
        """测试获取服务统计"""
        # 创建熔断器
        asyncio.run(manager.create_circuit_breaker("stats-service"))

        stats = manager.get_service_statistics()
        assert 'total_circuits' in stats
        assert 'circuits_by_state' in stats
        assert 'overall_metrics' in stats
        assert stats['total_circuits'] >= 1


class TestIntegration:
    """集成测试"""

    def test_error_handling_workflow(self, temp_dir):
        """测试完整的错误处理工作流"""
        # 创建配置
        config = {
            'log_dir': str(temp_dir / 'integration' / 'logs'),
            'diagnostic_dir': str(temp_dir / 'integration' / 'diagnostics')
        }

        # 初始化组件
        error_logger = ErrorLogger(config)
        diagnostic_collector = DiagnosticCollector(config)
        diagnostic_collector.set_error_logger(error_logger)

        retry_manager = RetryManager({'enabled': True})
        isolation_manager = ErrorIsolationManager({})
        degradation_manager = GracefulDegradationManager()
        circuit_manager = CircuitBreakerManager()

        # 模拟错误场景
        error_info = ErrorInfo(
            error_id="integration-test",
            error_code="INTEGRATION_ERROR",
            error_message="集成测试错误",
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            instance_id="test-instance"
        )

        # 1. 记录错误
        entry_id = error_logger.log_error(error_info)
        assert entry_id is not None

        # 2. 错误隔离
        result = asyncio.run(isolation_manager.isolate_error(error_info))
        assert result is True

        # 3. 生成诊断报告
        report = asyncio.run(diagnostic_collector.generate_diagnostic_report())
        assert report is not None

        # 4. 清理
        error_logger.shutdown()
        diagnostic_collector.shutdown()
        retry_manager.shutdown()
        isolation_manager.shutdown()
        degradation_manager.shutdown()
        circuit_manager.shutdown()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])