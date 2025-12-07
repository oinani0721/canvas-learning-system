"""
Agent性能优化器测试

测试Agent性能优化器的功能和性能提升效果。

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-01-22
"""

import asyncio

# Import the optimizer
import sys
import time
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))
from agent_performance_optimizer import (
    AgentPerformanceOptimizer,
    execute_agents_parallel,
    get_agent_optimizer,
    submit_agent_task,
)


class TestAgentPerformanceOptimizer:
    """Agent性能优化器测试类"""

    def test_basic_task_execution(self):
        """测试基本任务执行"""
        optimizer = AgentPerformanceOptimizer(max_workers=2)

        try:
            # 提交任务
            task_id = optimizer.submit_task(
                agent_type="basic-decomposition",
                input_data={"concept": "机器学习"}
            )

            # 等待任务完成
            result = optimizer.wait_for_task(task_id, timeout=10.0)

            # 验证结果
            assert result.success is True
            assert result.agent_type == "basic-decomposition"
            assert "sub_questions" in result.result
            assert len(result.result["sub_questions"]) >= 1
            assert result.execution_time > 0

        finally:
            optimizer.shutdown()

    def test_parallel_task_execution(self):
        """测试并行任务执行"""
        optimizer = AgentPerformanceOptimizer(max_workers=5)

        try:
            # 准备多个任务
            tasks = [
                {
                    "agent_type": "basic-decomposition",
                    "input_data": {"concept": f"概念{i}"},
                    "priority": i % 3
                }
                for i in range(8)
            ]

            start_time = time.time()

            # 并行执行
            results = optimizer.execute_parallel(tasks)

            execution_time = time.time() - start_time

            # 验证结果
            assert len(results) == 8, "应该执行8个任务"
            assert all(result.success for result in results), "所有任务应该成功"
            assert execution_time < 5.0, "并行执行应该在5秒内完成"

            # 验证性能统计
            stats = optimizer.get_performance_stats()
            assert stats["parallel_executions"] >= 1
            assert stats["completed_tasks"] == 8
            assert stats["success_rate"] == 100.0

        finally:
            optimizer.shutdown()

    def test_caching_functionality(self):
        """测试缓存功能"""
        optimizer = AgentPerformanceOptimizer(max_workers=2, enable_caching=True)

        try:
            # 第一次执行任务
            task_id1 = optimizer.submit_task(
                agent_type="basic-decomposition",
                input_data={"concept": "缓存测试概念"}
            )
            result1 = optimizer.wait_for_task(task_id1)

            # 第二次执行相同任务（应该命中缓存）
            task_id2 = optimizer.submit_task(
                agent_type="basic-decomposition",
                input_data={"concept": "缓存测试概念"}
            )
            result2 = optimizer.wait_for_task(task_id2)

            # 验证缓存效果
            assert result1.success is True
            assert result2.success is True
            assert result1.result == result2.result, "缓存结果应该相同"

            # 验证缓存统计
            stats = optimizer.get_performance_stats()
            assert stats["cache_hits"] >= 1, "应该有缓存命中"

        finally:
            optimizer.shutdown()

    def test_task_priority(self):
        """测试任务优先级"""
        optimizer = AgentPerformanceOptimizer(max_workers=1)

        try:
            # 提交不同优先级的任务
            low_priority_id = optimizer.submit_task(
                agent_type="basic-decomposition",
                input_data={"concept": "低优先级"},
                priority=10
            )

            high_priority_id = optimizer.submit_task(
                agent_type="basic-decomposition",
                input_data={"concept": "高优先级"},
                priority=1
            )

            # 等待任务完成
            low_result = optimizer.wait_for_task(low_priority_id)
            high_result = optimizer.wait_for_task(high_priority_id)

            # 验证高优先级任务先完成（由于工作线程限制，高优先级应该更早开始）
            assert low_result.success is True
            assert high_result.success is True

        finally:
            optimizer.shutdown()

    def test_error_handling_and_retry(self):
        """测试错误处理和重试机制"""
        optimizer = AgentPerformanceOptimizer(max_workers=2)

        try:
            # 提交一个会失败的任务（使用不存在的Agent类型）
            task_id = optimizer.submit_task(
                agent_type="non-existent-agent",
                input_data={"concept": "测试"}
            )

            # 等待任务完成（应该失败）
            result = optimizer.wait_for_task(task_id, timeout=15.0)

            # 验证错误处理
            assert result.success is False
            assert result.error is not None
            assert "未知的Agent类型" in result.error

            # 验证统计
            stats = optimizer.get_performance_stats()
            assert stats["failed_tasks"] >= 1

        finally:
            optimizer.shutdown()

    def test_context_pooling(self):
        """测试上下文池管理"""
        optimizer = AgentPerformanceOptimizer(
            max_workers=3,
            enable_context_pooling=True
        )

        try:
            # 执行多个相同类型的任务
            task_ids = []
            for i in range(5):
                task_id = optimizer.submit_task(
                    agent_type="scoring-agent",
                    input_data={"user_text": f"用户理解 {i}"}
                )
                task_ids.append(task_id)

            # 等待所有任务完成
            results = []
            for task_id in task_ids:
                result = optimizer.wait_for_task(task_id)
                results.append(result)

            # 验证所有任务成功
            assert all(result.success for result in results)

            # 验证上下文池
            stats = optimizer.get_performance_stats()
            assert stats["context_pool_size"] >= 1

        finally:
            optimizer.shutdown()

    def test_performance_monitoring(self):
        """测试性能监控"""
        optimizer = AgentPerformanceOptimizer(max_workers=3)

        try:
            # 执行一些任务
            task_ids = []
            for i in range(6):
                task_id = optimizer.submit_task(
                    agent_type="oral-explanation",
                    input_data={"concept": f"性能测试概念 {i}"}
                )
                task_ids.append(task_id)

            # 等待完成
            for task_id in task_ids:
                optimizer.wait_for_task(task_id)

            # 检查性能统计
            stats = optimizer.get_performance_stats()

            assert stats["total_tasks"] >= 6
            assert stats["completed_tasks"] >= 6
            assert stats["average_execution_time"] > 0
            assert stats["success_rate"] > 0
            assert "cache_hit_rate_percent" in stats
            assert "queue_size" in stats
            assert "worker_threads" in stats

        finally:
            optimizer.shutdown()

    def test_batch_task_submission(self):
        """测试批量任务提交"""
        optimizer = AgentPerformanceOptimizer(max_workers=4)

        try:
            # 准备批量任务
            batch_tasks = [
                {
                    "agent_type": "basic-decomposition",
                    "input_data": {"concept": f"批量概念 {i}"},
                    "priority": i % 2
                }
                for i in range(6)
            ]

            # 批量提交
            task_ids = optimizer.submit_tasks_batch(batch_tasks)

            # 验证提交结果
            assert len(task_ids) == 6
            assert all(task_id.startswith("task-") for task_id in task_ids)

            # 等待完成
            results = []
            for task_id in task_ids:
                result = optimizer.wait_for_task(task_id)
                results.append(result)

            # 验证执行结果
            assert len(results) == 6
            assert all(result.success for result in results)

        finally:
            optimizer.shutdown()

    def test_task_status_tracking(self):
        """测试任务状态跟踪"""
        optimizer = AgentPerformanceOptimizer(max_workers=2)

        try:
            # 提交任务
            task_id = optimizer.submit_task(
                agent_type="clarification-path",
                input_data={"concept": "状态测试"}
            )

            # 检查初始状态
            initial_status = optimizer.get_task_status(task_id)
            assert initial_status in ["running", "completed"]

            # 等待完成
            result = optimizer.wait_for_task(task_id)

            # 检查最终状态
            final_status = optimizer.get_task_status(task_id)
            assert final_status in ["completed", "failed"]

            if result.success:
                assert final_status == "completed"
            else:
                assert final_status == "failed"

        finally:
            optimizer.shutdown()

    def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试全局优化器
        optimizer1 = get_agent_optimizer()
        optimizer2 = get_agent_optimizer()
        assert optimizer1 is optimizer2, "应该返回同一个实例"

        # 测试便捷任务提交
        task_id = submit_agent_task(
            agent_type="basic-decomposition",
            input_data={"concept": "便捷函数测试"}
        )

        # 验证任务ID格式
        assert task_id.startswith("task-")

        # 等待完成
        optimizer1.wait_for_task(task_id)

        # 测试便捷并行执行
        tasks = [
            {
                "agent_type": "basic-decomposition",
                "input_data": {"concept": f"便捷并行测试 {i}"}
            }
            for i in range(3)
        ]

        results = execute_agents_parallel(tasks)
        assert len(results) == 3
        assert all(result.success for result in results)

        # 清理
        optimizer1.shutdown()

    def test_different_agent_types(self):
        """测试不同Agent类型的执行"""
        optimizer = AgentPerformanceOptimizer(max_workers=3)

        try:
            # 测试各种Agent类型
            agent_types = [
                "basic-decomposition",
                "deep-decomposition",
                "scoring-agent",
                "oral-explanation",
                "clarification-path",
                "comparison-table",
                "memory-anchor",
                "four-level-explanation",
                "example-teaching",
                "verification-question"
            ]

            results = []
            for agent_type in agent_types:
                task_id = optimizer.submit_task(
                    agent_type=agent_type,
                    input_data={"concept": f"{agent_type}测试"}
                )
                result = optimizer.wait_for_task(task_id)
                results.append((agent_type, result))

            # 验证所有Agent类型都能执行
            for agent_type, result in results:
                assert result.success is True, f"{agent_type} 执行失败: {result.error}"
                assert result.agent_type == agent_type
                assert result.result is not None

        finally:
            optimizer.shutdown()

    def test_resource_cleanup(self):
        """测试资源清理"""
        optimizer = AgentPerformanceOptimizer(max_workers=2, cache_size=3)

        try:
            # 执行一些任务，填充缓存
            for i in range(5):
                task_id = optimizer.submit_task(
                    agent_type="basic-decomposition",
                    input_data={"concept": f"资源测试 {i}"}
                )
                optimizer.wait_for_task(task_id)

            # 检查资源使用
            stats = optimizer.get_performance_stats()
            assert stats["cache_size"] <= 3, "缓存大小应该被限制"

            # 清空缓存
            optimizer.clear_cache()
            stats = optimizer.get_performance_stats()
            assert stats["cache_size"] == 0, "缓存应该被清空"

        finally:
            optimizer.shutdown()

    def test_async_compatibility(self):
        """测试异步兼容性"""
        async def test_async_operations():
            optimizer = AgentPerformanceOptimizer(max_workers=2)

            try:
                # 在异步环境中提交任务
                task_id = optimizer.submit_task(
                    agent_type="basic-decomposition",
                    input_data={"concept": "异步测试"}
                )

                # 使用异步等待
                result = await asyncio.get_event_loop().run_in_executor(
                    None, optimizer.wait_for_task, task_id
                )

                assert result.success is True

            finally:
                optimizer.shutdown()

        # 运行异步测试
        asyncio.run(test_async_operations())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
