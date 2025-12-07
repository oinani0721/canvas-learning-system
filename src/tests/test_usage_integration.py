"""
Usage Integration Tests - Canvas学习系统

测试GLM用量管理系统的集成功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append('..')

from enhanced_agent_instance_pool import EnhancedGLMInstancePool, QuotaControlConfig, QuotaExhaustionStrategy
from glm_rate_limiter import GLMRateLimiter, PlanType, RateLimitConfig
from usage_monitor import UsageMonitor


class TestUsageIntegration:
    """用量系统集成测试"""

    @pytest.fixture
    def temp_data_dir(self):
        """临时数据目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def rate_limiter(self, temp_data_dir):
        """创建速率限制器实例"""
        config = RateLimitConfig(
            plan_type=PlanType.PRO,
            max_prompts_per_period=100,  # 使用较小的数量便于测试
            rate_limit_requests_per_second=2.0,
            max_concurrent_requests=2
        )

        # 临时修改数据目录
        from unittest.mock import patch
        with patch('glm_rate_limiter.Path') as mock_path:
            mock_path.return_value = Path(temp_data_dir)
            limiter = GLMRateLimiter(config)
            yield limiter

    @pytest.mark.asyncio
    async def test_limiter_monitor_integration(self, rate_limiter):
        """测试速率限制器与监控器的集成"""
        # 创建监控器
        monitor = UsageMonitor(rate_limiter)

        # 启动系统
        await rate_limiter.start()
        await monitor.start_monitoring()

        try:
            # 消耗一些额度
            await rate_limiter.consume_quota(10)
            await rate_limiter.consume_quota(20)

            # 获取实时指标
            metrics = await monitor.get_real_time_metrics()

            # 验证指标
            assert metrics["current_usage"]["used_prompts"] == 30
            assert metrics["current_usage"]["remaining_prompts"] == 70
            assert metrics["current_usage"]["usage_percentage"] == 0.3

            # 获取套餐信息
            assert metrics["plan_info"]["plan_type"] == "pro"
            assert metrics["plan_info"]["max_prompts_per_period"] == 100

        finally:
            await monitor.stop_monitoring()
            await rate_limiter.stop()

    @pytest.mark.asyncio
    async def test_alert_system_integration(self, rate_limiter):
        """测试预警系统集成"""
        alerts_received = []

        async def alert_handler(alert):
            alerts_received.append(alert)

        # 设置预警回调
        await rate_limiter.set_alert_callback(alert_handler)

        # 创建监控器
        monitor = UsageMonitor(rate_limiter)

        await rate_limiter.start()
        await monitor.start_monitoring()

        try:
            # 消耗到触发预警
            await rate_limiter.consume_quota(85)  # 85%

            # 等待预警处理
            await asyncio.sleep(0.1)

            # 验证预警
            assert len(alerts_received) > 0
            assert alerts_received[0].alert_type == "warning"

        finally:
            await monitor.stop_monitoring()
            await rate_limiter.stop()

    @pytest.mark.asyncio
    async def test_enhanced_pool_integration(self):
        """测试增强版实例池集成"""
        # 创建用量控制配置
        quota_config = QuotaControlConfig(
            enable_quota_control=True,
            quota_exhaustion_strategy=QuotaExhaustionStrategy.QUEUE,
            max_wait_time_seconds=5
        )

        # 创建增强版实例池
        pool = EnhancedGLMInstancePool(
            max_concurrent_instances=2,
            quota_control_config=quota_config
        )

        await pool.start()

        try:
            # 创建实例
            instance_id = await pool.create_instance("clarification-path")
            assert instance_id is not None

            # 提交任务
            task_data = {
                "task_id": "test-001",
                "node_data": {"content": "test"}
            }

            result = await pool.submit_task(instance_id, task_data)
            assert result["status"] in ["completed", "queued"]

            # 获取池状态
            pool_status = await pool.get_pool_status()
            assert pool_status["quota_status"]["quota_control_enabled"] == True

            # 获取用量仪表板
            dashboard = await pool.get_usage_dashboard()
            assert "real_time_metrics" in dashboard

        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_quota_exhaustion_strategies(self):
        """测试用量耗尽策略"""
        strategies = [
            QuotaExhaustionStrategy.REJECT,
            QuotaExhaustionStrategy.QUEUE
        ]

        for strategy in strategies:
            quota_config = QuotaControlConfig(
                enable_quota_control=True,
                quota_exhaustion_strategy=strategy,
                max_wait_time_seconds=1
            )

            pool = EnhancedGLMInstancePool(
                max_concurrent_instances=1,
                quota_control_config=quota_config
            )

            await pool.start()

            try:
                # 消耗所有额度
                pool.rate_limiter.usage_metrics.used_prompts = pool.rate_limiter.config.max_prompts_per_period

                # 创建实例
                instance_id = await pool.create_instance("test-agent")

                # 提交任务
                task_data = {"task_id": "test", "data": {}}
                result = await pool.submit_task(instance_id, task_data)

                # 验证策略
                if strategy == QuotaExhaustionStrategy.REJECT:
                    assert result["status"] == "error"
                elif strategy == QuotaExhaustionStrategy.QUEUE:
                    assert result["status"] == "queued"

            finally:
                await pool.stop()

    @pytest.mark.asyncio
    async def test_usage_history_tracking(self, rate_limiter):
        """测试用量历史记录跟踪"""
        monitor = UsageMonitor(rate_limiter)

        await rate_limiter.start()
        await monitor.start_monitoring()

        try:
            # 模拟一些使用
            for i in range(3):
                await rate_limiter.consume_quota(10)
                await asyncio.sleep(0.1)

            # 获取历史记录
            history = await monitor.get_usage_history(days=1)

            # 验证历史记录结构
            assert isinstance(history, list)

        finally:
            await monitor.stop_monitoring()
            await rate_limiter.stop()

    @pytest.mark.asyncio
    async def test_usage_report_generation(self, rate_limiter):
        """测试用量报告生成"""
        monitor = UsageMonitor(rate_limiter)

        await rate_limiter.start()
        await monitor.start_monitoring()

        try:
            # 模拟使用
            await rate_limiter.consume_quota(50)

            # 生成报告
            report = await monitor.generate_usage_report(days=1)

            # 验证报告结构
            if "error" not in report:
                assert "report_id" in report
                assert "generated_at" in report
                assert "plan_type" in report
                assert "recommendations" in report

        finally:
            await monitor.stop_monitoring()
            await rate_limiter.stop()

    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self, rate_limiter):
        """测试并发请求限制"""
        # 创建多个并发任务
        async def consume_quota():
            return await rate_limiter.consume_quota(1)

        # 启用智能节流
        rate_limiter.config.enable_smart_throttling = True

        # 创建并发任务
        tasks = [consume_quota() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # 验证部分请求被限制
        successful = sum(1 for result in results if result)
        assert successful < 10  # 不是所有请求都应该成功

    @pytest.mark.asyncio
    async def test_plan_type_switching(self):
        """测试套餐类型切换"""
        # 创建不同套餐的限制器
        lite_limiter = GLMRateLimiter(RateLimitConfig(
            plan_type=PlanType.LITE,
            max_prompts_per_period=120
        ))

        pro_limiter = GLMRateLimiter(RateLimitConfig(
            plan_type=PlanType.PRO,
            max_prompts_per_period=600
        ))

        # 验证配置差异
        assert lite_limiter.config.max_prompts_per_period == 120
        assert pro_limiter.config.max_prompts_per_period == 600

        # 验证速率限制差异
        assert lite_limiter.config.rate_limit_requests_per_second == 0.4
        assert pro_limiter.config.rate_limit_requests_per_second == 2.0

    @pytest.mark.asyncio
    async def test_data_export_functionality(self, rate_limiter):
        """测试数据导出功能"""
        monitor = UsageMonitor(rate_limiter)

        await rate_limiter.start()
        await monitor.start_monitoring()

        try:
            # 导出JSON格式
            json_path = await monitor.export_usage_data("json")
            assert json_path.endswith(".json")

            # 导出CSV格式（如果有历史数据）
            # csv_path = await monitor.export_usage_data("csv")
            # assert csv_path.endswith(".csv")

        finally:
            await monitor.stop_monitoring()
            await rate_limiter.stop()

    @pytest.mark.asyncio
    async def test_error_recovery(self, rate_limiter):
        """测试错误恢复机制"""
        # 创建监控器
        monitor = UsageMonitor(rate_limiter)

        await rate_limiter.start()
        await monitor.start_monitoring()

        try:
            # 消耗额度
            await rate_limiter.consume_quota(10)

            # 验证状态正常
            status = await rate_limiter.get_usage_status()
            assert status.used_prompts == 10

            # 模拟错误情况（消耗超额）
            success = await rate_limiter.consume_quota(1000)
            assert not success

            # 验证系统仍然正常
            status = await rate_limiter.get_usage_status()
            assert status.used_prompts == 10

        finally:
            await monitor.stop_monitoring()
            await rate_limiter.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
