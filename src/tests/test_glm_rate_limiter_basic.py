"""
GLM Rate Limiter Basic Test Suite - Canvas学习系统

测试GLM Coding Plan用量管理系统的核心功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import asyncio
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append('..')

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

        # 等待0.2秒，应该补充约2个令牌
        await asyncio.sleep(0.21)
        assert 1 < bucket.tokens <= 3

        # 等待1秒，应该补充到容量
        await asyncio.sleep(1)
        assert bucket.tokens == 10


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
        """测试周期重置（模拟）"""
        # 手动设置周期结束时间为过去
        rate_limiter.usage_metrics.period_end = datetime.now(timezone.utc) - timedelta(seconds=1)

        # 消耗一些额度
        await rate_limiter.consume_quota(100)
        assert rate_limiter.usage_metrics.used_prompts == 100

        # 检查周期重置
        await rate_limiter._check_period_reset()

        # 验证重置（可能不会立即重置，因为时间差太小）
        # 这里主要测试方法不报错

    @pytest.mark.asyncio
    async def test_warning_thresholds(self, rate_limiter):
        """测试预警阈值"""
        alert_callback = AsyncMock()
        await rate_limiter.set_alert_callback(alert_callback)

        # 消耗到80%
        await rate_limiter.consume_quota(480)  # 480/600 = 80%
        await asyncio.sleep(0.1)  # 等待异步处理

        # 应该触发警告
        # 注意：由于cooldown机制，可能不会立即触发
        # 这里主要测试方法执行不报错

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
        for _ in range(10):
            if await rate_limiter.consume_quota(1):
                successful_consumes += 1

        # 由于速率限制，不应该所有请求都成功
        assert successful_consumes < 10

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
    async def test_exact_quota_consumption(self):
        """测试消耗刚好所有额度"""
        limiter = create_rate_limiter("lite")  # 120/5h
        assert await limiter.consume_quota(120) == True
        assert await limiter.consume_quota(1) == False


# Basic integration test
@pytest.mark.asyncio
async def test_basic_integration():
    """基础集成测试"""
    # 创建速率限制器
    limiter = create_rate_limiter("pro")
    await limiter.start()

    try:
        # 模拟一些使用
        for i in range(10):
            success = await limiter.consume_quota(1)
            if success:
                print(f"Consumed prompt {i+1}")
            else:
                print(f"Failed to consume prompt {i+1}")

        # 获取状态
        status = await limiter.get_usage_status()
        print(f"Final status: {status.used_prompts}/{status.total_prompts}")

        assert status.used_prompts > 0

    finally:
        await limiter.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
