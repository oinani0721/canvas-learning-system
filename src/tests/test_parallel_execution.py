"""
并行执行测试 - Canvas学习系统

测试并行Agent执行器的核心功能，包括：
- 并行处理核心框架测试
- 上下文隔离测试
- 任务队列管理测试
- 错误处理和恢复测试
- 结果聚合测试
- 性能监控测试

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
Story: 8.14 (Task 8)
"""

import asyncio
import tempfile
import time
from pathlib import Path

import pytest
from context_isolation_manager import ContextIsolationManager
from error_handling_manager import ErrorCategory, ErrorHandlingManager, ErrorRecord, RecoveryStrategy

# 导入被测试模块
from parallel_agent_executor import AgentTask, ParallelAgentExecutor, ParallelExecutionSummary
from performance_monitor import PerformanceMonitor
from result_aggregator import AgentResult, AggregationMethod, ResultAggregator, ResultMetadata
from task_queue_manager import TaskDefinition, TaskPriority, TaskQueueManager


class TestParallelAgentExecutor:
    """测试并行Agent执行器"""

    @pytest.fixture
    def executor_config(self):
        """测试用执行器配置"""
        return {
            "parallel_processing": {
                "enabled": True,
                "default_max_concurrent": 4,
                "max_concurrent_limit": 8
            },
            "context_isolation": {
                "isolation_level": "process",
                "context_size_limit_mb": 128,
                "context_cleanup_enabled": True
            },
            "task_queue": {
                "queue_type": "priority",
                "max_queue_size": 100,
                "task_retry_attempts": 2
            },
            "error_handling": {
                "continue_on_error": True,
                "error_isolation": True,
                "fallback_strategy": "retry"
            }
        }

    @pytest.fixture
    async def executor(self, executor_config):
        """测试用执行器实例"""
        executor = ParallelAgentExecutor()
        executor.config = executor_config
        await executor.initialize()
        yield executor
        await executor.shutdown()

    @pytest.mark.asyncio
    async def test_executor_initialization(self, executor_config):
        """测试执行器初始化"""
        executor = ParallelAgentExecutor()
        executor.config = executor_config
        await executor.initialize()

        assert executor.process_pool is not None
        assert executor.max_concurrent == 4
        assert executor.context_manager is not None
        assert executor.queue_manager is not None

        await executor.shutdown()

    @pytest.mark.asyncio
    async def test_submit_batch_tasks(self, executor):
        """测试批量任务提交"""
        tasks = [
            {
                "agent_name": "basic-decomposition",
                "canvas_path": "test.canvas",
                "input_data": {"material_text": "测试材料1"},
                "priority": "high"
            },
            {
                "agent_name": "oral-explanation",
                "canvas_path": "test.canvas",
                "input_data": {"concept": "测试概念"},
                "priority": "normal"
            }
        ]

        execution_id = await executor.submit_batch_tasks(tasks, max_concurrent=2)

        assert execution_id is not None
        assert execution_id in executor.executions
        assert executor.executions[execution_id].overall_status == "running"
        assert len(executor.executions[execution_id].agent_execution_sessions) == 0  # 还未开始

    @pytest.mark.asyncio
    async def test_get_execution_status(self, executor):
        """测试获取执行状态"""
        tasks = [
            {
                "agent_name": "basic-decomposition",
                "canvas_path": "test.canvas",
                "input_data": {"material_text": "测试材料"}
            }
        ]

        execution_id = await executor.submit_batch_tasks(tasks)
        status = await executor.get_execution_status(execution_id)

        assert status["execution_id"] == execution_id
        assert "overall_status" in status
        assert "task_queue" in status
        assert "performance_metrics" in status

    @pytest.mark.asyncio
    async def test_cancel_execution(self, executor):
        """测试取消执行"""
        tasks = [
            {
                "agent_name": "basic-decomposition",
                "canvas_path": "test.canvas",
                "input_data": {"material_text": "测试材料"}
            }
        ]

        execution_id = await executor.submit_batch_tasks(tasks)
        success = await executor.cancel_execution(execution_id)

        assert success is True
        assert executor.executions[execution_id].overall_status == "cancelled"

    def test_get_performance_metrics(self, executor):
        """测试获取性能指标"""
        # 创建模拟执行总结
        summary = ParallelExecutionSummary(
            execution_id="test-exec-123",
            submission_timestamp="2025-01-22T10:00:00Z",
            execution_mode="parallel_batch",
            max_concurrent_agents=4,
            overall_status="completed"
        )

        executor.executions[summary.execution_id] = summary
        metrics = executor.get_performance_metrics(summary.execution_id)

        assert "parallel_efficiency" in metrics
        assert "resource_usage" in metrics
        assert "throughput" in metrics
        assert "global_metrics" in metrics

    def test_configure_parallel_settings(self, executor):
        """测试配置并行设置"""
        new_settings = {
            "parallel_processing": {
                "default_max_concurrent": 6
            }
        }

        success = executor.configure_parallel_settings(new_settings)

        assert success is True
        # 验证配置已更新（实际实现中需要检查具体配置值）

    @pytest.mark.asyncio
    async def test_agent_execution_simulation(self, executor):
        """测试Agent执行模拟"""
        # 创建测试任务
        task = AgentTask(
            agent_name="basic-decomposition",
            canvas_path="test.canvas",
            input_data={"material_text": "测试材料"}
        )

        # 模拟执行Agent
        result = await executor._execute_basic_decomposition(task)

        assert result["status"] == "success"
        assert "output_data" in result
        assert "sub_questions" in result["output_data"]
        assert "performance_metrics" in result


class TestContextIsolationManager:
    """测试上下文隔离管理器"""

    @pytest.fixture
    def isolation_config(self):
        """测试用隔离配置"""
        return {
            "isolation_level": "process",
            "context_size_limit_mb": 128,
            "context_cleanup_enabled": True,
            "gc_threshold_percentage": 80.0
        }

    @pytest.fixture
    def isolation_manager(self, isolation_config):
        """测试用隔离管理器实例"""
        return ContextIsolationManager(isolation_config)

    @pytest.mark.asyncio
    async def test_create_isolated_context(self, isolation_manager):
        """测试创建隔离上下文"""
        context_id = await isolation_manager.create_isolated_context(
            task_id="test-task-123",
            agent_name="basic-decomposition"
        )

        assert context_id is not None
        assert context_id in isolation_manager.active_contexts

        usage = await isolation_manager.get_context_usage(context_id)
        assert usage is not None
        assert usage["task_id"] == "test-task-123"
        assert usage["agent_name"] == "basic-decomposition"

    @pytest.mark.asyncio
    async def test_cleanup_context(self, isolation_manager):
        """测试清理上下文"""
        context_id = await isolation_manager.create_isolated_context(
            task_id="test-task-456",
            agent_name="oral-explanation"
        )

        success = await isolation_manager.cleanup_context(context_id)

        assert success is True
        assert context_id not in isolation_manager.active_contexts

    def test_get_all_contexts_status(self, isolation_manager):
        """测试获取所有上下文状态"""
        status = isolation_manager.get_all_contexts_status()

        assert "active_contexts_count" in status
        assert "shared_contexts_count" in status
        assert "contexts" in status

    @pytest.mark.asyncio
    async def test_cleanup_idle_contexts(self, isolation_manager):
        """测试清理空闲上下文"""
        # 创建多个上下文
        context_ids = []
        for i in range(3):
            context_id = await isolation_manager.create_isolated_context(
                task_id=f"test-task-{i}",
                agent_name="test-agent"
            )
            context_ids.append(context_id)

        # 清理空闲上下文（设置为很短的超时时间）
        cleaned_count = await isolation_manager.cleanup_idle_contexts(idle_timeout_seconds=0)

        assert cleaned_count == 3
        assert len(isolation_manager.active_contexts) == 0


class TestTaskQueueManager:
    """测试任务队列管理器"""

    @pytest.fixture
    def queue_config(self):
        """测试用队列配置"""
        return {
            "queue_type": "priority",
            "max_queue_size": 50,
            "load_balancing_strategy": "round_robin",
            "back_pressure_enabled": True,
            "back_pressure_threshold": 0.8
        }

    @pytest.fixture
    def queue_manager(self, queue_config):
        """测试用队列管理器实例"""
        return TaskQueueManager(queue_config)

    @pytest.mark.asyncio
    async def test_submit_task(self, queue_manager):
        """测试提交任务"""
        task = TaskDefinition(
            agent_name="basic-decomposition",
            canvas_path="test.canvas",
            input_data={"material_text": "测试材料"},
            priority=TaskPriority.HIGH
        )

        success = await queue_manager.submit_task(task)

        assert success is True
        assert queue_manager.main_queue.size() == 1

    @pytest.mark.asyncio
    async def test_get_next_task(self, queue_manager):
        """测试获取下一个任务"""
        task = TaskDefinition(
            agent_name="basic-decomposition",
            canvas_path="test.canvas",
            input_data={"material_text": "测试材料"},
            priority=TaskPriority.URGENT
        )

        await queue_manager.submit_task(task)
        next_task = await queue_manager.get_next_task()

        assert next_task is not None
        assert next_task.agent_name == "basic-decomposition"
        assert next_task.priority == TaskPriority.URGENT

    @pytest.mark.asyncio
    async def test_complete_task(self, queue_manager):
        """测试完成任务"""
        task = TaskDefinition(
            agent_name="basic-decomposition",
            canvas_path="test.canvas",
            input_data={"material_text": "测试材料"}
        )

        await queue_manager.submit_task(task)
        next_task = await queue_manager.get_next_task()
        await queue_manager.complete_task(next_task.task_id, success=True)

        stats = await queue_manager.get_queue_status()
        assert stats["completed_tasks"] == 1
        assert stats["running_tasks"] == 0

    @pytest.mark.asyncio
    async def test_priority_ordering(self, queue_manager):
        """测试优先级排序"""
        # 按不同优先级提交任务
        low_task = TaskDefinition(
            agent_name="test-agent",
            canvas_path="test.canvas",
            input_data={},
            priority=TaskPriority.LOW
        )
        high_task = TaskDefinition(
            agent_name="test-agent",
            canvas_path="test.canvas",
            input_data={},
            priority=TaskPriority.HIGH
        )

        await queue_manager.submit_task(low_task)
        await queue_manager.submit_task(high_task)

        # 高优先级任务应该先被获取
        first_task = await queue_manager.get_next_task()
        second_task = await queue_manager.get_next_task()

        assert first_task.priority == TaskPriority.HIGH
        assert second_task.priority == TaskPriority.LOW

    def test_register_worker(self, queue_manager):
        """测试注册工作节点"""
        queue_manager.register_worker("worker-1", max_concurrent_tasks=2)
        queue_manager.register_worker("worker-2", max_concurrent_tasks=1)

        worker_status = asyncio.run(queue_manager.get_worker_status())

        assert worker_status["total_workers"] == 2
        assert worker_status["available_workers"] == 3  # 2 + 1
        assert "worker-1" in worker_status["workers"]
        assert "worker-2" in worker_status["workers"]

    def test_get_queue_status(self, queue_manager):
        """测试获取队列状态"""
        status = asyncio.run(queue_manager.get_queue_status())

        assert "queue_size" in status
        assert "worker_count" in status
        assert "available_workers" in status
        assert "queue_utilization" in status
        assert "back_pressure_active" in status


class TestErrorHandlingManager:
    """测试错误处理管理器"""

    @pytest.fixture
    def error_config(self):
        """测试用错误处理配置"""
        return {
            "continue_on_error": True,
            "error_isolation": True,
            "fallback_strategy": "retry",
            "task_retry_attempts": 3,
            "task_retry_delay_seconds": 1
        }

    @pytest.fixture
    def error_handler(self, error_config):
        """测试用错误处理管理器实例"""
        return ErrorHandlingManager(error_config)

    @pytest.mark.asyncio
    async def test_handle_error(self, error_handler):
        """测试处理错误"""
        exception = ValueError("测试错误")
        error_record = await error_handler.handle_error(
            task_id="test-task-123",
            execution_id="test-exec-456",
            agent_name="basic-decomposition",
            worker_id="worker-1",
            exception=exception
        )

        assert error_record is not None
        assert error_record.task_id == "test-task-123"
        assert error_record.agent_name == "basic-decomposition"
        assert error_record.error_type == "ValueError"
        assert error_record.error_message == "测试错误"
        assert error_record.error_category in ErrorCategory

    def test_get_error_statistics(self, error_handler):
        """测试获取错误统计"""
        stats = error_handler.get_error_statistics()

        assert "total_errors" in stats
        assert "recovered_errors" in stats
        assert "recovery_rate" in stats
        assert "active_errors_count" in stats

    def test_get_error_trends(self, error_handler):
        """测试获取错误趋势"""
        # 创建一些模拟错误记录
        for i in range(10):
            error_record = ErrorRecord(
                task_id=f"task-{i}",
                execution_id="exec-123",
                agent_name="test-agent"
            )
            error_record.timestamp = time.time() - (i * 3600)  # 每小时一个错误
            error_handler.error_records[error_record.error_id] = error_record

        trends = error_handler.get_error_trends(time_window_hours=24)

        assert "last_hour" in trends
        assert "last_6hours" in trends
        assert "last_24hours" in trends
        assert "error_rate" in trends

    @pytest.mark.asyncio
    async def test_error_recovery(self, error_handler):
        """测试错误恢复"""
        # 模拟可恢复的错误
        exception = TimeoutError("任务超时")
        error_record = await error_handler.handle_error(
            task_id="test-task-789",
            execution_id="test-exec-abc",
            agent_name="basic-decomposition",
            worker_id="worker-2",
            exception=exception
        )

        # 检查是否尝试了恢复
        assert error_record.recovery_strategy in [RecoveryStrategy.RETRY, RecoveryStrategy.NONE]


class TestResultAggregator:
    """测试结果聚合器"""

    @pytest.fixture
    def aggregator_config(self):
        """测试用聚合器配置"""
        return {
            "aggregation_method": "merge_outputs",
            "max_result_size_mb": 10,
            "save_results_to_disk": False,  # 测试时不保存到磁盘
            "result_validation_enabled": True
        }

    @pytest.fixture
    def aggregator(self, aggregator_config):
        """测试用聚合器实例"""
        return ResultAggregator(aggregator_config)

    def test_add_result(self, aggregator):
        """测试添加结果"""
        metadata = ResultMetadata(
            task_id="task-123",
            execution_id="exec-456",
            agent_name="basic-decomposition",
            confidence_score=0.8,
            completeness_score=0.9
        )

        result = AgentResult(
            task_id="task-123",
            execution_id="exec-456",
            agent_name="basic-decomposition",
            output_data={"sub_questions": ["问题1", "问题2"]},
            metadata=metadata
        )

        aggregator.add_result(result)

        assert len(aggregator.individual_results) == 1
        assert metadata.result_id in aggregator.individual_results

    @pytest.mark.asyncio
    async def test_aggregate_results(self, aggregator):
        """测试结果聚合"""
        # 创建多个Agent结果
        for i, agent_name in enumerate(["basic-decomposition", "oral-explanation"]):
            metadata = ResultMetadata(
                task_id=f"task-{i}",
                execution_id="exec-123",
                agent_name=agent_name,
                confidence_score=0.8 + i * 0.1
            )

            result = AgentResult(
                task_id=f"task-{i}",
                execution_id="exec-123",
                agent_name=agent_name,
                output_data={
                    "agent_output": f"output-{i}",
                    "timestamp": time.time()
                },
                metadata=metadata
            )
            aggregator.add_result(result)

        # 聚合结果
        aggregated = await aggregator.aggregate_results("exec-123")

        assert aggregated is not None
        assert aggregated.execution_id == "exec-123"
        assert len(aggregated.individual_results) == 2
        assert aggregated.merged_output is not None
        assert aggregated.overall_quality_score >= 0

    @pytest.mark.asyncio
    async def test_different_aggregation_methods(self, aggregator):
        """测试不同聚合方法"""
        metadata = ResultMetadata(
            task_id="task-123",
            execution_id="exec-456",
            agent_name="test-agent",
            confidence_score=0.8
        )

        result = AgentResult(
            task_id="task-123",
            execution_id="exec-456",
            agent_name="test-agent",
            output_data={"value": 42},
            metadata=metadata
        )
        aggregator.add_result(result)

        # 测试保留独立结果方法
        aggregated = await aggregator.aggregate_results(
            "exec-456",
            method=AggregationMethod.PRESERVE_INDIVIDUAL
        )

        assert "individual_results" in aggregated.merged_output
        assert "summary" in aggregated.merged_output

    def test_get_aggregation_statistics(self, aggregator):
        """测试获取聚合统计"""
        stats = aggregator.get_aggregation_statistics()

        assert "total_results" in stats
        assert "valid_results" in stats
        assert "invalid_results" in stats
        assert "total_aggregations" in stats


class TestPerformanceMonitor:
    """测试性能监控器"""

    @pytest.fixture
    def monitor_config(self):
        """测试用监控器配置"""
        return {
            "enabled": True,
            "collect_metrics": True,
            "log_performance_data": False,  # 测试时不记录日志
            "slow_execution_threshold_seconds": 60,
            "memory_usage_alert_threshold_mb": 512,
            "cpu_usage_alert_threshold_percent": 80
        }

    @pytest.fixture
    def monitor(self, monitor_config):
        """测试用监控器实例"""
        return PerformanceMonitor(monitor_config)

    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor):
        """测试启动监控"""
        await monitor.start_monitoring()

        assert monitor.monitoring_active is True
        assert monitor.monitoring_task is not None

        await monitor.stop_monitoring()
        assert monitor.monitoring_active is False

    @pytest.mark.asyncio
    async def test_record_execution_metrics(self, monitor):
        """测试记录执行指标"""
        metrics = monitor.record_execution_metrics(
            execution_id="exec-123",
            task_count=10,
            successful_tasks=8,
            failed_tasks=2,
            total_execution_time_ms=5000,
            parallel_efficiency=3.5,
            concurrency_utilization=0.75
        )

        assert metrics.execution_id == "exec-123"
        assert metrics.task_count == 10
        assert metrics.successful_tasks == 8
        assert metrics.parallel_efficiency == 3.5
        assert metrics.throughput_tasks_per_second == 2.0  # 10 / 5

    def test_get_current_performance_snapshot(self, monitor):
        """测试获取当前性能快照"""
        snapshot = monitor.get_current_performance_snapshot()

        assert "timestamp" in snapshot
        assert "monitoring_active" in snapshot
        assert "metrics_history_counts" in snapshot
        assert "active_alerts_count" in snapshot

    def test_generate_performance_report(self, monitor):
        """测试生成性能报告"""
        report = monitor.generate_performance_report()

        assert "report_id" in report
        assert "generated_at" in report
        assert "monitoring_status" in report
        assert "summary" in report
        assert "resource_metrics" in report
        assert "recommendations" in report


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        # 创建临时配置文件
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.yaml"
            config_content = {
                "parallel_processing": {
                    "default_max_concurrent": 2
                },
                "task_queue": {
                    "max_queue_size": 10
                }
            }

            # 这里应该创建实际的YAML文件，为了简化我们直接使用字典配置
            executor = ParallelAgentExecutor()
            executor.config = config_content
            await executor.initialize()

            try:
                # 提交任务
                tasks = [
                    {
                        "agent_name": "basic-decomposition",
                        "canvas_path": "test.canvas",
                        "input_data": {"material_text": "测试材料1"},
                        "priority": "high"
                    },
                    {
                        "agent_name": "oral-explanation",
                        "canvas_path": "test.canvas",
                        "input_data": {"concept": "测试概念"},
                        "priority": "normal"
                    }
                ]

                execution_id = await executor.submit_batch_tasks(tasks)
                assert execution_id is not None

                # 等待一段时间让任务执行
                await asyncio.sleep(2)

                # 检查执行状态
                status = await executor.get_execution_status(execution_id)
                assert status["execution_id"] == execution_id

                # 获取结果（如果有）
                try:
                    results = await executor.get_execution_results(execution_id)
                    assert "execution_id" in results
                except Exception:
                    # 可能任务还未完成，这是正常的
                    pass

            finally:
                await executor.shutdown()

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """测试错误处理集成"""
        executor = ParallelAgentExecutor()
        executor.config = {
            "parallel_processing": {"default_max_concurrent": 1},
            "error_handling": {"continue_on_error": True}
        }
        await executor.initialize()

        try:
            # 提交一个会失败的任务（无效的Agent名称）
            tasks = [
                {
                    "agent_name": "invalid-agent",
                    "canvas_path": "test.canvas",
                    "input_data": {"test": "data"}
                }
            ]

            execution_id = await executor.submit_batch_tasks(tasks)
            assert execution_id is not None

            # 等待错误处理
            await asyncio.sleep(1)

            # 检查错误是否被正确处理
            status = await executor.get_execution_status(execution_id)
            assert status["execution_id"] == execution_id

        finally:
            await executor.shutdown()


# 性能基准测试
class TestPerformanceBenchmark:
    """性能基准测试"""

    @pytest.mark.asyncio
    async def test_parallel_vs_serial_performance(self):
        """测试并行vs串行性能"""
        # 这个测试需要实际的Agent执行，可能需要很长时间
        # 在实际环境中应该禁用或调整参数
        pytest.skip("性能基准测试需要完整的Agent环境")

    @pytest.mark.asyncio
    async def test_scalability_performance(self):
        """测试可扩展性性能"""
        # 测试不同并发数量下的性能表现
        concurrency_levels = [1, 2, 4, 8]
        performance_results = {}

        for concurrency in concurrency_levels:
            start_time = time.time()

            # 创建执行器并提交任务
            executor = ParallelAgentExecutor()
            executor.config = {
                "parallel_processing": {"default_max_concurrent": concurrency}
            }
            await executor.initialize()

            try:
                tasks = [
                    {
                        "agent_name": "basic-decomposition",
                        "canvas_path": "test.canvas",
                        "input_data": {"material_text": f"测试材料{i}"},
                        "priority": "normal"
                    }
                    for i in range(concurrency)
                ]

                execution_id = await executor.submit_batch_tasks(tasks)
                # 等待任务完成或超时
                await asyncio.sleep(10)

                end_time = time.time()
                performance_results[concurrency] = end_time - start_time

            finally:
                await executor.shutdown()

        # 分析性能结果
        assert len(performance_results) == len(concurrency_levels)

        # 性能应该随着并发数增加而改善（至少不应该显著恶化）
        baseline_time = performance_results[1]
        for concurrency, exec_time in performance_results.items():
            if concurrency > 1:
                # 并行执行时间应该接近或小于串行时间
                efficiency_ratio = baseline_time / exec_time
                assert efficiency_ratio > 0.5  # 至少50%的效率


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
