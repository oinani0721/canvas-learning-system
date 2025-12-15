"""
Usage Monitor Module - Canvas学习系统

本模块提供GLM Coding Plan用量实时监控、仪表板显示、
历史记录分析和报告生成功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64

from glm_rate_limiter import GLMRateLimiter, UsageMetrics, UsageAlert

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UsageHistoryEntry:
    """用量历史记录条目"""
    timestamp: datetime
    period_start: datetime
    period_end: datetime
    plan_type: str
    total_prompts: int
    used_prompts: int
    usage_percentage: float
    alerts_triggered: List[str]

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "plan_type": self.plan_type,
            "total_prompts": self.total_prompts,
            "used_prompts": self.used_prompts,
            "usage_percentage": self.usage_percentage,
            "alerts_triggered": self.alerts_triggered
        }


@dataclass
class UsageReport:
    """用量报告数据模型"""
    report_id: str
    generated_at: datetime
    period_covered: str
    plan_type: str
    total_periods: int
    total_prompts_used: int
    average_usage_percentage: float
    peak_usage_percentage: float
    alerts_summary: Dict[str, int]
    usage_trend: str  # "increasing", "decreasing", "stable"
    recommendations: List[str]

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "period_covered": self.period_covered,
            "plan_type": self.plan_type,
            "total_periods": self.total_periods,
            "total_prompts_used": self.total_prompts_used,
            "average_usage_percentage": self.average_usage_percentage,
            "peak_usage_percentage": self.peak_usage_percentage,
            "alerts_summary": self.alerts_summary,
            "usage_trend": self.usage_trend,
            "recommendations": self.recommendations
        }


class UsageMonitor:
    """用量监控器

    提供实时用量监控、历史记录分析、
    报告生成和可视化功能。
    """

    def __init__(self, rate_limiter: GLMRateLimiter):
        """初始化用量监控器

        Args:
            rate_limiter: GLM速率限制器实例
        """
        self.rate_limiter = rate_limiter
        self.data_dir = Path("data")
        self.usage_history_file = self.data_dir / "usage_history.json"
        self.usage_reports_dir = self.data_dir / "usage_reports"

        # 确保目录存在
        self.usage_reports_dir.mkdir(exist_ok=True)

        # 历史记录缓存
        self._history_cache: List[UsageHistoryEntry] = []
        self._cache_loaded = False

        # 监控状态
        self._monitoring = False
        self._monitor_task = None

    async def start_monitoring(self):
        """启动监控"""
        if self._monitoring:
            logger.warning("Usage monitor is already running")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Usage monitor started")

    async def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Usage monitor stopped")

    async def get_real_time_metrics(self) -> Dict:
        """获取实时用量指标

        Returns:
            Dict: 实时用量指标
        """
        # 获取当前用量状态
        current_usage = await self.rate_limiter.get_usage_status()

        # 获取套餐信息
        plan_info = self.rate_limiter.get_plan_info()

        # 计算剩余时间
        now = datetime.now(timezone.utc)
        remaining_time = current_usage.period_end - now
        remaining_hours = remaining_time.total_seconds() / 3600

        # 获取最近的预警
        recent_alerts = self._get_recent_alerts(hours=1)

        # 计算使用速率
        usage_rate = self._calculate_usage_rate()

        return {
            "current_usage": current_usage.to_dict(),
            "plan_info": plan_info,
            "remaining_time_hours": remaining_hours,
            "recent_alerts": [alert.to_dict() for alert in recent_alerts],
            "usage_rate_per_hour": usage_rate,
            "estimated_completion": self._estimate_completion_time(usage_rate),
            "status": self._get_usage_status_level(current_usage.usage_percentage)
        }

    async def get_usage_history(self, days: int = 7) -> List[Dict]:
        """获取历史用量记录

        Args:
            days: 获取最近多少天的记录

        Returns:
            List[Dict]: 历史用量记录
        """
        if not self._cache_loaded:
            await self._load_history_cache()

        # 过滤指定天数内的记录
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        filtered_history = [
            entry for entry in self._history_cache
            if entry.timestamp >= cutoff_date
        ]

        return [entry.to_dict() for entry in filtered_history]

    async def generate_usage_report(self, days: int = 7) -> Dict:
        """生成用量报告

        Args:
            days: 报告覆盖的天数

        Returns:
            Dict: 用量报告
        """
        # 获取历史记录
        history = await self.get_usage_history(days)

        if not history:
            return {"error": "No history data available"}

        # 分析数据
        total_periods = len(history)
        total_prompts_used = sum(entry["used_prompts"] for entry in history)
        average_usage = sum(entry["usage_percentage"] for entry in history) / total_periods
        peak_usage = max(entry["usage_percentage"] for entry in history)

        # 统计预警
        alerts_summary = defaultdict(int)
        for entry in history:
            for alert_type in entry["alerts_triggered"]:
                alerts_summary[alert_type] += 1

        # 分析趋势
        usage_trend = self._analyze_usage_trend(history)

        # 生成建议
        recommendations = self._generate_recommendations(
            average_usage, peak_usage, alerts_summary, usage_trend
        )

        # 创建报告
        report = UsageReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            period_covered=f"Last {days} days",
            plan_type=history[0]["plan_type"] if history else "unknown",
            total_periods=total_periods,
            total_prompts_used=total_prompts_used,
            average_usage_percentage=average_usage,
            peak_usage_percentage=peak_usage,
            alerts_summary=dict(alerts_summary),
            usage_trend=usage_trend,
            recommendations=recommendations
        )

        # 保存报告
        await self._save_report(report)

        return report.to_dict()

    async def export_usage_data(self, format: str = "json") -> str:
        """导出用量数据

        Args:
            format: 导出格式 ("json", "csv", "yaml")

        Returns:
            str: 导出的数据路径
        """
        # 获取完整历史记录
        history = await self.get_usage_history(days=30)  # 最近30天

        # 准备导出数据
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_records": len(history),
            "data": history
        }

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"usage_export_{timestamp}.{format}"
        filepath = self.data_dir / filename

        # 根据格式导出
        if format.lower() == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

        elif format.lower() == "csv":
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if history:
                    writer = csv.DictWriter(f, fieldnames=history[0].keys())
                    writer.writeheader()
                    writer.writerows(history)

        elif format.lower() == "yaml":
            import yaml
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"Usage data exported to {filepath}")
        return str(filepath)

    async def create_usage_dashboard(self) -> Dict:
        """创建用量仪表板数据

        Returns:
            Dict: 仪表板数据
        """
        # 获取实时指标
        real_time = await self.get_real_time_metrics()

        # 获取历史趋势
        history = await self.get_usage_history(days=7)

        # 生成图表数据
        chart_data = self._generate_chart_data(history)

        # 获取最近报告
        recent_report = await self._get_most_recent_report()

        return {
            "real_time_metrics": real_time,
            "historical_trend": history,
            "charts": chart_data,
            "recent_report": recent_report,
            "summary": {
                "total_alerts_today": len(self._get_recent_alerts(hours=24)),
                "current_usage_level": real_time["status"],
                "usage_efficiency": self._calculate_usage_efficiency(history),
                "predicted_usage": self._predict_next_period_usage(history)
            }
        }

    async def _monitor_loop(self):
        """监控循环"""
        while self._monitoring:
            try:
                # 记录当前用量
                await self._record_current_usage()

                # 每5分钟记录一次
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(60)

    async def _record_current_usage(self):
        """记录当前用量"""
        current_usage = await self.rate_limiter.get_usage_status()

        # 创建历史记录条目
        entry = UsageHistoryEntry(
            timestamp=datetime.now(timezone.utc),
            period_start=current_usage.period_start,
            period_end=current_usage.period_end,
            plan_type=self.rate_limiter.config.plan_type.value,
            total_prompts=current_usage.total_prompts,
            used_prompts=current_usage.used_prompts,
            usage_percentage=current_usage.usage_percentage,
            alerts_triggered=[
                alert.alert_type for alert in
                self.rate_limiter.alert_history[-10:]  # 最近10个预警
            ]
        )

        # 添加到缓存
        self._history_cache.append(entry)

        # 限制缓存大小
        if len(self._history_cache) > 1000:
            self._history_cache = self._history_cache[-1000:]

    async def _load_history_cache(self):
        """加载历史记录缓存"""
        try:
            if self.usage_history_file.exists():
                with open(self.usage_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'history' in data:
                    for entry_data in data['history']:
                        entry = UsageHistoryEntry(
                            timestamp=datetime.fromisoformat(entry_data['timestamp']),
                            period_start=datetime.fromisoformat(entry_data['period_start']),
                            period_end=datetime.fromisoformat(entry_data['period_end']),
                            plan_type=entry_data['plan_type'],
                            total_prompts=entry_data['total_prompts'],
                            used_prompts=entry_data['used_prompts'],
                            usage_percentage=entry_data['usage_percentage'],
                            alerts_triggered=entry_data['alerts_triggered']
                        )
                        self._history_cache.append(entry)

            self._cache_loaded = True
            logger.info(f"Loaded {len(self._history_cache)} history entries")

        except Exception as e:
            logger.error(f"Error loading history cache: {e}")

    def _get_recent_alerts(self, hours: int = 1) -> List[UsageAlert]:
        """获取最近的预警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.rate_limiter.alert_history
            if alert.timestamp >= cutoff_time
        ]

    def _calculate_usage_rate(self) -> float:
        """计算使用速率（次/小时）"""
        current_usage = self.rate_limiter.usage_metrics
        elapsed_hours = (datetime.now(timezone.utc) - current_usage.period_start).total_seconds() / 3600

        if elapsed_hours > 0:
            return current_usage.used_prompts / elapsed_hours
        return 0.0

    def _estimate_completion_time(self, usage_rate: float) -> Optional[str]:
        """估算完成时间"""
        if usage_rate <= 0:
            return None

        current_usage = self.rate_limiter.usage_metrics
        remaining_prompts = current_usage.remaining_prompts
        hours_needed = remaining_prompts / usage_rate

        completion_time = datetime.now(timezone.utc) + timedelta(hours=hours_needed)
        return completion_time.strftime("%Y-%m-%d %H:%M:%S")

    def _get_usage_status_level(self, usage_percentage: float) -> str:
        """获取用量状态级别"""
        if usage_percentage >= 0.95:
            return "critical"
        elif usage_percentage >= 0.9:
            return "high"
        elif usage_percentage >= 0.8:
            return "moderate"
        elif usage_percentage >= 0.5:
            return "normal"
        else:
            return "low"

    def _analyze_usage_trend(self, history: List[Dict]) -> str:
        """分析用量趋势"""
        if len(history) < 2:
            return "insufficient_data"

        # 计算最近3期和之前3期的平均用量
        recent_avg = sum(entry["usage_percentage"] for entry in history[-3:]) / 3
        previous_avg = sum(entry["usage_percentage"] for entry in history[-6:-3]) / 3 if len(history) >= 6 else recent_avg

        # 判断趋势
        if recent_avg > previous_avg * 1.1:
            return "increasing"
        elif recent_avg < previous_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    def _generate_recommendations(self, avg_usage: float, peak_usage: float,
                                alerts: Dict, trend: str) -> List[str]:
        """生成使用建议"""
        recommendations = []

        # 基于平均用量的建议
        if avg_usage > 0.9:
            recommendations.append("Consider upgrading to a higher tier plan to avoid interruptions")
        elif avg_usage < 0.3:
            recommendations.append("Consider downgrading to a more cost-effective plan")

        # 基于峰值用量的建议
        if peak_usage > 0.95:
            recommendations.append("Monitor usage closely to avoid exceeding limits")

        # 基于预警的建议
        if alerts.get("critical", 0) > 0:
            recommendations.append("Implement stricter usage controls or schedule tasks more evenly")

        # 基于趋势的建议
        if trend == "increasing":
            recommendations.append("Usage is trending upward - plan for potential upgrade")
        elif trend == "decreasing":
            recommendations.append("Usage is decreasing - review if current plan is optimal")

        if not recommendations:
            recommendations.append("Usage is within optimal range")

        return recommendations

    async def _save_report(self, report: UsageReport):
        """保存报告"""
        filename = f"{report.report_id}.json"
        filepath = self.usage_reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"Report saved to {filepath}")

    async def _get_most_recent_report(self) -> Optional[Dict]:
        """获取最近的报告"""
        try:
            report_files = list(self.usage_reports_dir.glob("report_*.json"))
            if not report_files:
                return None

            latest_file = max(report_files, key=lambda p: p.stat().st_mtime)

            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error loading recent report: {e}")
            return None

    def _generate_chart_data(self, history: List[Dict]) -> Dict:
        """生成图表数据"""
        if not history:
            return {}

        # 按时间排序
        history_sorted = sorted(history, key=lambda x: x["timestamp"])

        # 提取数据
        timestamps = [entry["timestamp"] for entry in history_sorted]
        usage_percentages = [entry["usage_percentage"] * 100 for entry in history_sorted]

        return {
            "usage_trend": {
                "timestamps": timestamps,
                "percentages": usage_percentages,
                "type": "line"
            },
            "usage_distribution": {
                "low": len([p for p in usage_percentages if p < 50]),
                "normal": len([p for p in usage_percentages if 50 <= p < 80]),
                "moderate": len([p for p in usage_percentages if 80 <= p < 90]),
                "high": len([p for p in usage_percentages if 90 <= p < 95]),
                "critical": len([p for p in usage_percentages if p >= 95]),
                "type": "pie"
            }
        }

    def _calculate_usage_efficiency(self, history: List[Dict]) -> float:
        """计算使用效率"""
        if not history:
            return 0.0

        # 效率 = 平均使用率 / 目标使用率 (目标75%)
        avg_usage = sum(entry["usage_percentage"] for entry in history) / len(history)
        target_usage = 0.75

        efficiency = min(avg_usage / target_usage, 1.0) * 100
        return round(efficiency, 2)

    def _predict_next_period_usage(self, history: List[Dict]) -> Optional[float]:
        """预测下一期用量"""
        if len(history) < 3:
            return None

        # 使用最近3期的平均值作为预测
        recent_usages = [entry["usage_percentage"] for entry in history[-3:]]
        predicted = sum(recent_usages) / 3

        return round(predicted * 100, 2)