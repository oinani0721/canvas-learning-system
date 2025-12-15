"""
GLM Coding Plan Rate Limiter Module - Canvas学习系统

本模块实现GLM Coding Plan智能用量管理，支持120/600/2400次/5小时的用量限制，
实时监控预警，智能速率控制，确保并行处理不会超出GLM用量限制。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Optional, List, Callable, Any
from pathlib import Path
import logging
import yaml
from collections import deque

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlanType(Enum):
    """GLM Coding Plan套餐类型"""
    LITE = "lite"     # 120 prompts/5h
    PRO = "pro"       # 600 prompts/5h
    MAX = "max"       # 2400 prompts/5h


class AlertType(Enum):
    """预警类型"""
    WARNING = "warning"      # 警告 (80%)
    CRITICAL = "critical"    # 严重 (90%)
    EXCEEDED = "exceeded"    # 超额 (95%+)


@dataclass
class UsageMetrics:
    """用量指标数据模型"""
    total_prompts: int = 0
    used_prompts: int = 0
    remaining_prompts: int = 0
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=5))
    usage_percentage: float = 0.0

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "total_prompts": self.total_prompts,
            "used_prompts": self.used_prompts,
            "remaining_prompts": self.remaining_prompts,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "usage_percentage": self.usage_percentage
        }


@dataclass
class UsageAlert:
    """用量预警数据模型"""
    alert_id: str
    alert_type: str  # "warning", "critical", "exceeded"
    message: str
    percentage: float
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "message": self.message,
            "percentage": self.percentage,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged
        }


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    plan_type: PlanType
    max_prompts_per_period: int
    warning_thresholds: List[float] = field(default_factory=lambda: [0.8, 0.9, 0.95])
    rate_limit_requests_per_second: float = 0.4  # 基于套餐计算的安全速率
    enable_smart_throttling: bool = True
    max_concurrent_requests: int = 4  # 避免并发超额错误

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "plan_type": self.plan_type.value,
            "max_prompts_per_period": self.max_prompts_per_period,
            "warning_thresholds": self.warning_thresholds,
            "rate_limit_requests_per_second": self.rate_limit_requests_per_second,
            "enable_smart_throttling": self.enable_smart_throttling,
            "max_concurrent_requests": self.max_concurrent_requests
        }


class TokenBucket:
    """令牌桶算法实现速率控制"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶

        Args:
            capacity: 桶容量 (最大令牌数)
            refill_rate: 令牌补充速率 (令牌/秒)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        消耗令牌

        Args:
            tokens: 要消耗的令牌数

        Returns:
            bool: 是否成功消耗令牌
        """
        async with self._lock:
            # 补充令牌
            now = time.time()
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.refill_rate

            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

            # 检查是否有足够的令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def wait_for_tokens(self, tokens: int = 1, timeout: float = 60.0) -> bool:
        """
        等待直到有足够的令牌

        Args:
            tokens: 需要的令牌数
            timeout: 最大等待时间（秒）

        Returns:
            bool: 是否成功获得令牌
        """
        start_time = time.time()
        while not await self.consume(tokens):
            if time.time() - start_time > timeout:
                return False
            await asyncio.sleep(0.1)
        return True


class GLMRateLimiter:
    """GLM Coding Plan用量速率限制器

    支持120/600/2400次/5小时的用量管理，实时监控预警，
    智能速率控制，避免触发1302/1303并发超额错误。
    """

    # 套餐配置映射
    PLAN_CONFIGS = {
        PlanType.LITE: {
            "max_prompts": 120,
            "rate_limit_rps": 0.4,  # 120/5h = 0.4 req/s
            "max_concurrent": 2
        },
        PlanType.PRO: {
            "max_prompts": 600,
            "rate_limit_rps": 2.0,  # 600/5h = 2 req/s
            "max_concurrent": 4
        },
        PlanType.MAX: {
            "max_prompts": 2400,
            "rate_limit_rps": 8.0,  # 2400/5h = 8 req/s
            "max_concurrent": 6
        }
    }

    def __init__(self, config: RateLimitConfig):
        """初始化速率限制器

        Args:
            config: 速率限制配置
        """
        self.config = config
        self.usage_metrics = UsageMetrics(
            total_prompts=config.max_prompts_per_period,
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc) + timedelta(hours=5)
        )

        # 令牌桶用于速率控制
        plan_config = self.PLAN_CONFIGS[config.plan_type]
        self.token_bucket = TokenBucket(
            capacity=int(config.rate_limit_requests_per_second * 10),  # 10秒的缓冲
            refill_rate=config.rate_limit_requests_per_second
        )

        # 初始化用量指标
        self.usage_metrics.remaining_prompts = self.usage_metrics.total_prompts - self.usage_metrics.used_prompts

        # 预警回调函数
        self.alert_callback: Optional[Callable] = None

        # 预警历史记录
        self.alert_history: List[UsageAlert] = []

        # 请求队列（用于智能节流）
        self.request_queue = asyncio.Queue()
        self.concurrent_requests = 0

        # 数据持久化路径
        self.data_dir = Path("data")
        self.usage_history_file = self.data_dir / "usage_history.json"

        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)

        # 加载历史数据
        self._load_usage_history()

        # 启动后台任务
        self._monitor_task = None
        self._is_running = False

        logger.info(f"GLMRateLimiter initialized with plan {config.plan_type.value}")

    async def start(self):
        """启动速率限制器"""
        if self._is_running:
            logger.warning("GLMRateLimiter is already running")
            return

        self._is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_usage())
        logger.info("GLMRateLimiter started")

    async def stop(self):
        """停止速率限制器"""
        self._is_running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # 保存历史数据
        self._save_usage_history()
        logger.info("GLMRateLimiter stopped")

    async def check_availability(self, requested_prompts: int = 1) -> bool:
        """检查是否有足够的可用额度

        Args:
            requested_prompts: 需要的prompt数量

        Returns:
            bool: 是否有足够的额度
        """
        # 检查周期是否需要重置
        await self._check_period_reset()

        # 检查剩余额度
        if self.usage_metrics.remaining_prompts >= requested_prompts:
            return True

        return False

    async def consume_quota(self, prompts_used: int) -> bool:
        """消耗用量额度

        Args:
            prompts_used: 使用的prompt数量

        Returns:
            bool: 消耗是否成功
        """
        # 检查周期是否需要重置
        await self._check_period_reset()

        # 检查可用额度
        if not await self.check_availability(prompts_used):
            logger.warning(f"Insufficient quota: requested {prompts_used}, available {self.usage_metrics.remaining_prompts}")
            return False

        # 应用速率限制
        if self.config.enable_smart_throttling:
            if not await self.token_bucket.consume(prompts_used):
                logger.warning(f"Rate limit exceeded for {prompts_used} prompts")
                return False

        # 更新用量统计
        self.usage_metrics.used_prompts += prompts_used
        self.usage_metrics.remaining_prompts = self.usage_metrics.total_prompts - self.usage_metrics.used_prompts
        self.usage_metrics.usage_percentage = self.usage_metrics.used_prompts / self.usage_metrics.total_prompts

        # 检查预警阈值
        await self._check_alert_thresholds()

        logger.info(f"Consumed {prompts_used} prompts, usage: {self.usage_metrics.used_prompts}/{self.usage_metrics.total_prompts}")
        return True

    async def get_usage_status(self) -> UsageMetrics:
        """获取当前用量状态

        Returns:
            UsageMetrics: 当前用量指标
        """
        await self._check_period_reset()
        return self.usage_metrics

    async def wait_for_quota(self, required_prompts: int) -> bool:
        """等待额度恢复

        Args:
            required_prompts: 需要的prompt数量

        Returns:
            bool: 是否成功获得额度
        """
        # 如果当前有足够的额度，直接返回
        if await self.check_availability(required_prompts):
            return True

        # 计算下一个周期的时间
        now = datetime.now(timezone.utc)
        if now >= self.usage_metrics.period_end:
            await self._check_period_reset()
            return await self.check_availability(required_prompts)

        # 等待周期重置
        wait_time = (self.usage_metrics.period_end - now).total_seconds()
        logger.info(f"Waiting for period reset in {wait_time:.2f} seconds")

        await asyncio.sleep(wait_time)
        await self._check_period_reset()

        return await self.check_availability(required_prompts)

    async def set_alert_callback(self, callback: Callable):
        """设置用量预警回调函数

        Args:
            callback: 预警回调函数
        """
        self.alert_callback = callback

    def get_plan_info(self) -> Dict:
        """获取套餐信息

        Returns:
            Dict: 套餐信息
        """
        return {
            "plan_type": self.config.plan_type.value,
            "max_prompts_per_period": self.config.max_prompts_per_period,
            "period_hours": 5,
            "rate_limit_rps": self.config.rate_limit_requests_per_second,
            "max_concurrent_requests": self.config.max_concurrent_requests,
            "current_usage": self.usage_metrics.to_dict()
        }

    async def _check_period_reset(self):
        """检查并执行周期重置"""
        now = datetime.now(timezone.utc)

        if now >= self.usage_metrics.period_end:
            # 保存当前周期的历史数据
            await self._save_period_to_history()

            # 重置用量指标
            self.usage_metrics = UsageMetrics(
                total_prompts=self.config.max_prompts_per_period,
                period_start=now,
                period_end=now + timedelta(hours=5)
            )

            logger.info("Usage period reset")

    async def _check_alert_thresholds(self):
        """检查预警阈值并触发预警"""
        usage_pct = self.usage_metrics.usage_percentage

        for threshold in self.config.warning_thresholds:
            if usage_pct >= threshold:
                # 确定预警类型
                if usage_pct >= 0.95:
                    alert_type = AlertType.EXCEEDED.value
                elif usage_pct >= 0.9:
                    alert_type = AlertType.CRITICAL.value
                else:
                    alert_type = AlertType.WARNING.value

                # 检查是否已经发送过相同类型的预警
                recent_alerts = [
                    alert for alert in self.alert_history
                    if alert.alert_type == alert_type and
                    (datetime.now() - alert.timestamp).total_seconds() < 300  # 5分钟内不重复
                ]

                if not recent_alerts:
                    # 创建预警
                    alert = UsageAlert(
                        alert_id=str(uuid.uuid4()),
                        alert_type=alert_type,
                        message=f"GLM Coding Plan usage {usage_pct:.1%} - {alert_type.upper()}",
                        percentage=usage_pct
                    )

                    self.alert_history.append(alert)

                    # 调用预警回调
                    if self.alert_callback:
                        try:
                            await self.alert_callback(alert)
                        except Exception as e:
                            logger.error(f"Error in alert callback: {e}")

                    logger.warning(f"Usage alert: {alert.message}")

    async def _monitor_usage(self):
        """监控用量的后台任务"""
        while self._is_running:
            try:
                # 检查周期重置
                await self._check_period_reset()

                # 保存历史数据（每分钟一次）
                self._save_usage_history()

                await asyncio.sleep(60)  # 每分钟检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in usage monitor: {e}")
                await asyncio.sleep(60)

    def _load_usage_history(self):
        """加载用量历史数据"""
        try:
            if self.usage_history_file.exists():
                with open(self.usage_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 加载历史记录
                if 'alerts' in data:
                    for alert_data in data['alerts']:
                        alert = UsageAlert(
                            alert_id=alert_data['alert_id'],
                            alert_type=alert_data['alert_type'],
                            message=alert_data['message'],
                            percentage=alert_data['percentage'],
                            timestamp=datetime.fromisoformat(alert_data['timestamp']),
                            acknowledged=alert_data['acknowledged']
                        )
                        self.alert_history.append(alert)

                logger.info("Loaded usage history from file")
        except Exception as e:
            logger.error(f"Error loading usage history: {e}")

    def _save_usage_history(self):
        """保存用量历史数据"""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'alerts': [alert.to_dict() for alert in self.alert_history[-100:]]  # 只保留最近100条
            }

            with open(self.usage_history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage history: {e}")

    async def _save_period_to_history(self):
        """保存当前周期数据到历史记录"""
        # 这里可以扩展为保存到数据库或详细的历史文件
        logger.info(f"Period completed: {self.usage_metrics.used_prompts} prompts used")


# 工厂函数
def create_rate_limiter(plan_type: str = "pro") -> GLMRateLimiter:
    """创建速率限制器实例

    Args:
        plan_type: 套餐类型 ("lite", "pro", "max")

    Returns:
        GLMRateLimiter: 速率限制器实例
    """
    plan_enum = PlanType(plan_type.lower())
    plan_config = GLMRateLimiter.PLAN_CONFIGS[plan_enum]

    config = RateLimitConfig(
        plan_type=plan_enum,
        max_prompts_per_period=plan_config["max_prompts"],
        rate_limit_requests_per_second=plan_config["rate_limit_rps"],
        max_concurrent_requests=plan_config["max_concurrent"]
    )

    return GLMRateLimiter(config)


# 全局速率限制器实例
_global_rate_limiter: Optional[GLMRateLimiter] = None


def get_global_rate_limiter() -> GLMRateLimiter:
    """获取全局速率限制器实例（单例模式）"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = create_rate_limiter("pro")  # 默认pro套餐
    return _global_rate_limiter


async def start_global_rate_limiter():
    """启动全局速率限制器"""
    limiter = get_global_rate_limiter()
    await limiter.start()


async def stop_global_rate_limiter():
    """停止全局速率限制器"""
    global _global_rate_limiter
    if _global_rate_limiter:
        await _global_rate_limiter.stop()