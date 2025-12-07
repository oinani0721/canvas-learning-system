"""
GLM Rate Limiter Test Suite - Canvas学习系统

测试GLM Coding Plan用量管理系统的各项功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import asyncio
import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from freezegun import freeze_time
from glm_rate_limiter import (
    GLMRateLimiter,
    PlanType,
    RateLimitConfig,
    TokenBucket,
    create_rate_limiter,
    get_global_rate_limiter,
)


class TestTokenBucket:
    """测试令牌桶算法"""

    @pytest.mark.asyncio
    async def test_token_bucket_initialization(self):
        """测试令牌桶初始化"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.refill_rate == 1.0
        assert bucket.tokens == 10

    @pytest.mark.asyncio
    async def test_token_consumption(self):
        """测试令牌消耗"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        # 消耗令牌
        assert await bucket.consume(1) == True
        assert bucket.tokens == 9

        # 消耗多个令牌
        assert await bucket.consume(5) == True
        assert bucket.tokens == 4

        # 令牌不足
        assert await bucket.consume(5) == False
        assert bucket.tokens == 4

    @pytest.mark.asyncio
    async def test_token_refill(self):
        """测试令牌补充"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/sec

        # 消耗所有令牌
        await bucket.consume(10)
        assert bucket.tokens == 0

        # 等待0.1秒，应该补充1个令牌
        await asyncio.sleep(0.11)
        assert 0 < bucket.tokens < 2

        # 等待1秒，应该补充10个令牌（但不超过容量）
        await asyncio.sleep(1)
        assert bucket.tokens == 10

    @pytest.mark.asyncio
    async def test_wait_for_tokens(self):
        """测试等待令牌"""
        bucket = TokenBucket(capacity=5, refill_rate=5.0)

        # 消耗所有令牌
        await bucket.consume(5)

        # 等待令牌
        start_time = datetime.now()
        result = await bucket.wait_for_tokens(3)
        elapsed = (datetime.now() - start_time).total_seconds()

        assert result == True
        assert elapsed >= 0.5  # 至少等待0.6秒 (3 tokens / 5 tokens/sec)


class TestRateLimitConfig:
    """测试速率限制配置"""

    def test_rate_limit_config_creation(self):
        """测试配置创建"""
        config = RateLimitConfig(
            plan_type=PlanType.PRO,
            max_prompts_per_period=600,
            warning_thresholds=[0.8, 0.9, 0.95],
            rate_limit_requests_per_second=2.0,
            enable_smart_throttling=True,
            max_concurrent_requests=4
        )

        assert config.plan_type == PlanType.PRO
        assert config.max_prompts_per_period == 600
        assert config.warning_thresholds == [0.8, 0.9, 0.95]
        assert config.rate_limit_requests_per_second == 2.0
        assert config.enable_smart_throttling == True
        assert config.max_concurrent_requests == 4

    def test_rate_limit_config_to_dict(self):
        """测试配置转换为字典"""
        config = RateLimitConfig(
            plan_type=PlanType.LITE,
            max_prompts_per_period=120
        )

        config_dict = config.to_dict()
        assert config_dict["plan_type"] == "lite"
        assert config_dict["max_prompts_per_period"] == 120


class TestGLMRateLimiter:
    """测试GLM速率限制器"""

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
            max_prompts_per_period=600,
            rate_limit_requests_per_second=2.0,
            max_concurrent_requests=4
        )

        # 临时修改数据目录
        with patch('glm_rate_limiter.Path') as mock_path:
            mock_path.return_value = Path(temp_dir)
            limiter = GLMRateLimiter(config)
            yield limiter

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self, rate_limiter):
        """测试速率限制器初始化"""
        assert rate_limiter.config.plan_type == PlanType.PRO
        assert rate_limiter.config.max_prompts_per_period == 600
        assert rate_limiter.usage_metrics.total_prompts == 600
        assert rate_limiter.usage_metrics.used_prompts == 0
        assert rate_limiter.usage_metrics.remaining_prompts == 600
        assert rate_limiter.usage_metrics.usage_percentage == 0.0

    @pytest.mark.asyncio
    async def test_check_availability(self, rate_limiter):
        """检查可用额度"""
        # 初始状态应该有足够额度
        assert await rate_limiter.check_availability(1) == True
        assert await rate_limiter.check_availability(100) == True
        assert await rate_limiter.check_availability(600) == True
        assert await rate_limiter.check_availability(601) == False

    @pytest.mark.asyncio
    async def test_consume_quota(self, rate_limiter):
        """测试消耗额度"""
        # 消耗额度
        assert await rate_limiter.consume_quota(10) == True
        assert rate_limiter.usage_metrics.used_prompts == 10
        assert rate_limiter.usage_metrics.remaining_prompts == 590
        assert rate_limiter.usage_metrics.usage_percentage == 10 / 600

        # 继续消耗
        assert await rate_limiter.consume_quota(90) == True
        assert rate_limiter.usage_metrics.used_prompts == 100
        assert rate_limiter.usage_metrics.remaining_prompts == 500

        # 尝试消耗超额
        assert await rate_limiter.consume_quota(501) == False

    @pytest.mark.asyncio
    async def test_period_reset(self, rate_limiter):
        """测试周期重置"""
        with freeze_time("2025-01-24 12:00:00") as frozen_time:
            # 消耗一些额度
            await rate_limiter.consume_quota(100)
            assert rate_limiter.usage_metrics.used_prompts == 100

            # 跳转到5小时后
            frozen_time.tick(delta=timedelta(hours=5, seconds=1))
            await rate_limiter._check_period_reset()

            # 验证重置
            assert rate_limiter.usage_metrics.used_prompts == 0
            assert rate_limiter.usage_metrics.remaining_prompts == 600

    @pytest.mark.asyncio
    async def test_warning_thresholds(self, rate_limiter):
        """测试预警阈值"""
        alert_callback = AsyncMock()
        rate_limiter.set_alert_callback(alert_callback)

        # 消耗到80%
        await rate_limiter.consume_quota(480)  # 480/600 = 80%
        await asyncio.sleep(0.1)  # 等待异步处理

        # 应该触发警告
        assert alert_callback.call_count > 0
        alert_call = alert_callback.call_args_list[0]
        alert = alert_call[0][0]
        assert alert.alert_type == "warning"
        assert 0.8 <= alert.percentage < 0.85

    @pytest.mark.asyncio
    async def test_critical_threshold(self, rate_limiter):
        """测试严重预警阈值"""
        alert_callback = AsyncMock()
        rate_limiter.set_alert_callback(alert_callback)

        # 消耗到90%
        await rate_limiter.consume_quota(540)  # 540/600 = 90%
        await asyncio.sleep(0.1)

        # 应该触发严重预警
        assert alert_callback.call_count > 0
        alert_call = alert_args_list[-1]
        alert = alert_call[0][0]
        assert alert.alert_type == "critical"

    @pytest.mark.asyncio
    async def test_wait_for_quota(self, rate_limiter):
        """测试等待额度恢复"""
        # 消耗所有额度
        await rate_limiter.consume_quota(600)

        # 等待新周期
        with freeze_time("2025-01-24 12:00:00") as frozen_time:
            # 在同一时期内，应该无法获得额度
            assert await rate_limiter.wait_for_quota(1) == False

            # 跳转到5小时后
            frozen_time.tick(delta=timedelta(hours=5, seconds=1))
            assert await rate_limiter.wait_for_quota(1) == True

    @pytest.mark.asyncio
    async def test_plan_configurations(self):
        """测试不同套餐配置"""
        # Lite套餐
        lite_config = RateLimitConfig(
            plan_type=PlanType.LITE,
            max_prompts_per_period=120,
            rate_limit_requests_per_second=0.4
        )
        lite_limiter = GLMRateLimiter(lite_config)
        assert lite_limiter.config.max_prompts_per_period == 120
        assert lite_limiter.config.rate_limit_requests_per_second == 0.4

        # Pro套餐
        pro_config = RateLimitConfig(
            plan_type=PlanType.PRO,
            max_prompts_per_period=600,
            rate_limit_requests_per_second=2.0
        )
        pro_limiter = GLMRateLimiter(pro_config)
        assert pro_limiter.config.max_prompts_per_period == 600
        assert pro_limiter.config.rate_limit_requests_per_second == 2.0

        # Max套餐
        max_config = RateLimitConfig(
            plan_type=PlanType.MAX,
            max_prompts_per_period=2400,
            rate_limit_requests_per_second=8.0
        )
        max_limiter = GLMRateLimiter(max_config)
        assert max_limiter.config.max_prompts_per_period == 2400
        assert max_limiter.config.rate_limit_requests_per_second == 8.0

    @pytest.mark.asyncio
    async def test_smart_throttling(self, rate_limiter):
        """测试智能节流"""
        # 启用智能节流
        rate_limiter.config.enable_smart_throttling = True

        # 快速消耗应该被限制
        successful_consumes = 0
        for _ in range(20):
            if await rate_limiter.consume_quota(1):
                successful_consumes += 1

        # 由于速率限制，不应该所有请求都成功
        assert successful_consumes < 20

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter):
        """测试并发请求控制"""
        # 模拟并发请求
        async def consume_prompts():
            return await rate_limiter.consume_quota(10)

        # 创建多个并发任务
        tasks = [consume_prompts() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证结果
        successful = sum(1 for result in results if result is True)
        assert successful <= rate_limiter.config.max_concurrent_requests

    @pytest.mark.asyncio
    async def test_usage_status(self, rate_limiter):
        """测试获取用量状态"""
        # 消耗一些额度
        await rate_limiter.consume_quota(150)

        # 获取状态
        status = await rate_limiter.get_usage_status()

        assert status.used_prompts == 150
        assert status.remaining_prompts == 450
        assert status.usage_percentage == 0.25

    @pytest.mark.asyncio
    async def test_plan_info(self, rate_limiter):
        """测试获取套餐信息"""
        plan_info = rate_limiter.get_plan_info()

        assert plan_info["plan_type"] == "pro"
        assert plan_info["max_prompts_per_period"] == 600
        assert plan_info["period_hours"] == 5
        assert plan_info["rate_limit_rps"] == 2.0
        assert plan_info["max_concurrent_requests"] == 4
        assert "current_usage" in plan_info

    @pytest.mark.asyncio
    async def test_start_stop(self, rate_limiter):
        """测试启动和停止"""
        # 启动
        await rate_limiter.start()
        assert rate_limiter._is_running == True
        assert rate_limiter._monitor_task != None

        # 停止
        await rate_limiter.stop()
        assert rate_limiter._is_running == False

    @pytest.mark.asyncio
    async def test_history_persistence(self, rate_limiter, temp_data_dir):
        """测试历史记录持久化"""
        # 创建一些预警
        alert_callback = AsyncMock()
        rate_limiter.set_alert_callback(alert_callback)

        # 触发预警
        await rate_limiter.consume_quota(480)
        await asyncio.sleep(0.1)

        # 保存历史
        rate_limiter._save_usage_history()

        # 验证文件存在
        history_file = Path(temp_data_dir) / "usage_history.json"
        assert history_file.exists()

        # 验证内容
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert 'alerts' in data
            assert len(data['alerts']) > 0


class TestRateLimiterFactory:
    """测试速率限制器工厂函数"""

    def test_create_rate_limiter(self):
        """测试创建速率限制器"""
        limiter = create_rate_limiter("lite")
        assert limiter.config.plan_type == PlanType.LITE
        assert limiter.config.max_prompts_per_period == 120

        limiter = create_rate_limiter("pro")
        assert limiter.config.plan_type == PlanType.PRO
        assert limiter.config.max_prompts_per_period == 600

        limiter = create_rate_limiter("max")
        assert limiter.config.plan_type == PlanType.MAX
        assert limiter.config.max_prompts_per_period == 2400

    def test_global_rate_limiter(self):
        """测试全局速率限制器"""
        # 获取全局实例
        limiter1 = get_global_rate_limiter()
        limiter2 = get_global_rate_limiter()

        # 应该是同一个实例
        assert limiter1 is limiter2
        assert limiter1.config.plan_type == PlanType.PRO  # 默认pro套餐


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_zero_quota_consumption(self):
        """测试消耗0额度"""
        limiter = create_rate_limiter("pro")
        assert await limiter.consume_quota(0) == True

    @pytest.mark.asyncio
    async def test_negative_quota_consumption(self):
        """测试消耗负数额度"""
        limiter = create_rate_limiter("pro")
        with pytest.raises(ValueError):
            await limiter.consume_quota(-1)

    @pytest.mark.asyncio
    async def test_exact_quota_consumption(self):
        """测试消耗刚好所有额度"""
        limiter = create_rate_limiter("lite")  # 120/5h
        assert await limiter.consume_quota(120) == True
        assert await limiter.consume_quota(1) == False

    @pytest.mark.asyncio
    async def test_multiple_period_cycles(self):
        """测试多个周期循环"""
        limiter = create_rate_limiter("pro")

        with freeze_time("2025-01-24 12:00:00") as frozen_time:
            # 第一期
            await limiter.consume_quota(600)
            assert limiter.usage_metrics.used_prompts == 600

            # 第二期
            frozen_time.tick(delta=timedelta(hours=5, seconds=1))
            await limiter._check_period_reset()
            assert limiter.usage_metrics.used_prompts == 0

            await limiter.consume_quota(300)
            assert limiter.usage_metrics.used_prompts == 300

            # 第三期
            frozen_time.tick(delta=timedelta(hours=5, seconds=1))
            await limiter._check_period_reset()
            assert limiter.usage_metrics.used_prompts == 0

    @pytest.mark.asyncio
    async def test_alert_cooldown(self):
        """测试预警冷却时间"""
        limiter = create_rate_limiter("pro")
        alert_callback = AsyncMock()
        limiter.set_alert_callback(alert_callback)

        # 触发80%预警
        await limiter.consume_quota(480)
        await asyncio.sleep(0.1)

        first_alert_count = alert_callback.call_count

        # 再次消耗，但不应该触发新的预警（冷却时间）
        await limiter.consume_quota(1)
        await asyncio.sleep(0.1)

        # 预警次数不应该增加
        assert alert_callback.call_count == first_alert_count


# 集成测试
@pytest.mark.asyncio
async def test_integration_with_agent_pool():
    """测试与Agent实例池的集成"""
    from agent_instance_pool import AgentTask, GLMInstancePool, TaskPriority

    # 创建速率限制器
    limiter = create_rate_limiter("pro")
    await limiter.start()

    # 创建实例池
    pool = GLMInstancePool(max_concurrent_instances=2)
    await pool.start()

    try:
        # 模拟Agent任务
        task = AgentTask(
            task_id="test-001",
            agent_type="clarification-path",
            node_data={"content": "test"},
            priority=TaskPriority.NORMAL
        )

        # 创建实例前检查用量
        assert await limiter.check_availability(1) == True

        # 创建实例
        instance_id = await pool.create_instance("clarification-path")
        assert instance_id is not None

        # 模拟任务执行
        result = await pool.submit_task(instance_id, task)
        assert result == True

        # 消耗用量
        await limiter.consume_quota(1)
        assert limiter.usage_metrics.used_prompts == 1

    finally:
        await pool.stop()
        await limiter.stop()


# 性能测试
@pytest.mark.asyncio
async def test_performance_large_requests():
    """测试大量请求的性能"""
    limiter = create_rate_limiter("max")  # 使用最大套餐

    start_time = datetime.now()

    # 模拟1000个请求
    successful = 0
    for i in range(1000):
        if await limiter.consume_quota(1):
            successful += 1

    elapsed = (datetime.now() - start_time).total_seconds()

    # 验证性能
    assert elapsed < 10  # 应该在10秒内完成
    assert successful > 0  # 至少有一些请求成功

    # 验证速率限制生效
    assert successful < 1000  # 不应该所有请求都成功（受速率限制）


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
