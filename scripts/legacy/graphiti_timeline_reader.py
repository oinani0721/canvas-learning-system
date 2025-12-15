#!/usr/bin/env python3
"""
Graphiti时间线数据读取器

从Graphiti知识图谱中读取真实的学习会话、事件和进度数据，
用于仪表板显示真实的学习时间分析。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-19
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# 导入Canvas工具
try:
    from canvas_utils import KnowledgeGraphLayer, CanvasJSONOperatorWithKG
    GRAPHITI_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入Canvas工具: {e}")
    GRAPHITI_AVAILABLE = False

class GraphitiTimelineReader:
    """Graphiti时间线数据读取器"""

    def __init__(self):
        self.kg_layer = None
        self.canvas_kg = None
        self.initialized = False

    async def initialize(self):
        """初始化Graphiti连接"""
        if not GRAPHITI_AVAILABLE:
            return False

        try:
            # 初始化KnowledgeGraphLayer
            self.kg_layer = KnowledgeGraphLayer()
            kg_success = await self.kg_layer.initialize()

            # 初始化CanvasJSONOperatorWithKG（包含get_learning_timeline方法）
            self.canvas_kg = CanvasJSONOperatorWithKG()
            canvas_kg_success = await self.canvas_kg.initialize()

            self.initialized = kg_success and canvas_kg_success

            if self.initialized:
                print("✅ Graphiti时间线读取器初始化成功")
            else:
                print("❌ Graphiti时间线读取器初始化失败")

            return self.initialized

        except Exception as e:
            print(f"❌ Graphiti初始化失败: {e}")
            return False

    async def get_real_timeline_data(self, user_id: str, canvas_id: str,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        从Graphiti获取真实的时间线数据

        Args:
            user_id: 用户ID
            canvas_id: Canvas ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            真实的时间线数据
        """
        if not self.initialized:
            return {"error": "Graphiti读取器未初始化"}

        try:
            # 设置默认时间范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # 尝试从CanvasJSONOperatorWithKG获取时间线数据
            if hasattr(self.canvas_kg, 'get_learning_timeline'):
                timeline_result = await self.canvas_kg.get_learning_timeline(
                    user_id, canvas_id, start_date, end_date
                )

                if timeline_result.get("success"):
                    timeline_data = timeline_result.get("timeline", {})
                    statistics = timeline_result.get("statistics", {})

                    return {
                        "success": True,
                        "timeline": timeline_data,
                        "statistics": statistics,
                        "period": {
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                            "days": (end_date - start_date).days
                        },
                        "data_source": "graphiti_real"
                    }
                else:
                    return {"error": f"获取时间线失败: {timeline_result.get('error', '未知错误')}"}
            else:
                return {"error": "CanvasJSONOperatorWithKG缺少get_learning_timeline方法"}

        except Exception as e:
            return {"error": f"从Graphiti获取时间线数据失败: {e}"}

    async def get_learning_sessions(self, user_id: str, canvas_id: str,
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取学习会话数据"""
        if not self.initialized:
            return []

        try:
            # 获取时间线数据
            timeline_data = await self.get_real_timeline_data(user_id, canvas_id, start_date, end_date)

            if timeline_data.get("success"):
                timeline = timeline_data.get("timeline", {})
                return timeline.get("sessions", [])
            else:
                return []

        except Exception as e:
            print(f"获取学习会话失败: {e}")
            return []

    async def get_learning_events(self, user_id: str, canvas_id: str,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取学习事件数据"""
        if not self.initialized:
            return []

        try:
            # 获取时间线数据
            timeline_data = await self.get_real_timeline_data(user_id, canvas_id, start_date, end_date)

            if timeline_data.get("success"):
                timeline = timeline_data.get("timeline", {})
                return timeline.get("events", [])
            else:
                return []

        except Exception as e:
            print(f"获取学习事件失败: {e}")
            return []

    def generate_dashboard_data_from_graphiti(self, user_id: str, canvas_id: str,
                                            timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从Graphiti时间线数据生成仪表板数据

        Args:
            user_id: 用户ID
            canvas_id: Canvas ID
            timeline_data: 从Graphiti获取的时间线数据

        Returns:
            仪表板数据
        """
        if not timeline_data.get("success"):
            return {"error": "无效的时间线数据"}

        try:
            timeline = timeline_data.get("timeline", {})
            sessions = timeline.get("sessions", [])
            events = timeline.get("events", [])
            statistics = timeline_data.get("statistics", {})

            # 生成时间线图表数据
            timeline_chart = self._create_timeline_chart_from_sessions(sessions)

            # 生成活动热力图
            activity_heatmap = self._create_activity_heatmap_from_sessions(sessions)

            # 计算概览数据
            overview = self._create_overview_from_data(sessions, events, statistics)

            # 生成掌握度分布（基于事件中的颜色变化）
            mastery_distribution = self._create_mastery_distribution_from_events(events)

            # 生成效率分析
            efficiency_analysis = self._create_efficiency_analysis(sessions, events)

            # 生成学习建议
            recommendations = self._generate_recommendations_from_data(sessions, events)

            return {
                "overview": overview,
                "timeline_chart": timeline_chart,
                "mastery_distribution": mastery_distribution,
                "activity_heatmap": activity_heatmap,
                "efficiency_analysis": efficiency_analysis,
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat(),
                "data_source": "graphiti_real",
                "canvas_info": {
                    "filename": canvas_id,
                    "total_sessions": len(sessions),
                    "total_events": len(events),
                    "data_period": timeline_data.get("period", {})
                }
            }

        except Exception as e:
            return {"error": f"从Graphiti生成仪表板数据失败: {e}"}

    def _create_timeline_chart_from_sessions(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从会话数据创建时间线图表"""
        daily_data = {}

        for session in sessions:
            start_time_str = session.get("start_time", "")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    date_str = start_time.strftime("%Y-%m-%d")

                    if date_str not in daily_data:
                        daily_data[date_str] = {
                            "session_count": 0,
                            "total_duration": 0,
                            "mastery_changes": 0
                        }

                    daily_data[date_str]["session_count"] += 1
                    daily_data[date_str]["total_duration"] += session.get("duration", 0)

                except Exception:
                    continue

        # 转换为列表格式
        daily_list = []
        for date, data in sorted(daily_data.items()):
            daily_list.append({
                "date": date,
                "session_count": data["session_count"],
                "total_duration": data["total_duration"],
                "mastery_changes": data["mastery_changes"]
            })

        return {
            "period": f"{len(daily_list)}天",
            "daily_data": daily_list,
            "total_sessions": sum(d["session_count"] for d in daily_list),
            "total_mastery_changes": sum(d["mastery_changes"] for d in daily_list)
        }

    def _create_activity_heatmap_from_sessions(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从会话数据创建活动热力图"""
        heatmap_data = []

        # 初始化7天x24小时的矩阵
        for weekday in range(7):
            for hour in range(24):
                heatmap_data.append({
                    "weekday": weekday,
                    "hour": hour,
                    "activity": 0,
                    "intensity": 0
                })

        # 统计每个时间段的活跃度
        for session in sessions:
            start_time_str = session.get("start_time", "")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    weekday = start_time.weekday()
                    hour = start_time.hour

                    # 找到对应的热力图数据点
                    for data_point in heatmap_data:
                        if data_point["weekday"] == weekday and data_point["hour"] == hour:
                            data_point["activity"] += session.get("duration", 0)
                            break

                except Exception:
                    continue

        # 计算强度
        max_activity = max(d["activity"] for d in heatmap_data) if heatmap_data else 1
        for data_point in heatmap_data:
            data_point["intensity"] = min(10, (data_point["activity"] / max_activity) * 10) if max_activity > 0 else 0

        return {
            "period": "真实学习数据",
            "heatmap_data": heatmap_data,
            "peak_hour": self._find_peak_hour(heatmap_data),
            "peak_weekday": self._find_peak_weekday(heatmap_data)
        }

    def _create_overview_from_data(self, sessions: List[Dict[str, Any]],
                                 events: List[Dict[str, Any]],
                                 statistics: Dict[str, Any]) -> Dict[str, Any]:
        """从数据创建概览"""
        total_sessions = len(sessions)
        total_duration = sum(s.get("duration", 0) for s in sessions)

        # 统计颜色变化（掌握情况）
        color_changes = [e for e in events if e.get("event_type") == "color_changed"]
        mastery_improvements = len([c for c in color_changes if self._is_positive_change(c)])

        return {
            "total_nodes": statistics.get("total_nodes", 0),
            "mastered_nodes": statistics.get("mastered_nodes", mastery_improvements),
            "mastery_rate": (mastery_improvements / max(1, len(color_changes))) * 100 if color_changes else 0,
            "color_distribution": self._count_current_colors(events),
            "recent_sessions": total_sessions,
            "total_study_time": total_duration,
            "last_activity": sessions[-1].get("start_time") if sessions else datetime.now().isoformat()
        }

    def _create_mastery_distribution_from_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从事件创建掌握度分布"""
        current_colors = {}

        # 获取每个节点的最新颜色
        for event in events:
            if event.get("event_type") == "color_changed":
                node_id = event.get("node_id")
                new_color = event.get("new_value")
                if node_id and new_color:
                    current_colors[node_id] = new_color

        # 统计颜色分布
        color_counts = {}
        for color in current_colors.values():
            color_counts[color] = color_counts.get(color, 0) + 1

        total_nodes = sum(color_counts.values())

        colors = []
        color_names = {
            "1": {"name": "不理解", "color": "#ff4444"},
            "2": {"name": "完全理解", "color": "#44ff44"},
            "3": {"name": "似懂非懂", "color": "#ff44ff"},
            "4": {"name": "困难", "color": "#ff6666"},
            "5": {"name": "AI解释", "color": "#4444ff"},
            "6": {"name": "个人理解", "color": "#ffff44"}
        }

        for code, count in color_counts.items():
            if code in color_names:
                colors.append({
                    "code": code,
                    "name": color_names[code]["name"],
                    "color": color_names[code]["color"],
                    "count": count,
                    "percentage": round(count / total_nodes * 100, 1) if total_nodes > 0 else 0
                })

        return {
            "colors": colors,
            "total_nodes": total_nodes,
            "mastered_percentage": next((c["percentage"] for c in colors if c["code"] == "2"), 0)
        }

    def _create_efficiency_analysis(self, sessions: List[Dict[str, Any]],
                                  events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建效率分析"""
        if not sessions:
            return {
                "overall_efficiency": 0,
                "time_efficiency": 0,
                "frequency_efficiency": 0,
                "mastery_efficiency": 0,
                "recommendations": ["暂无学习数据"]
            }

        total_duration = sum(s.get("duration", 0) for s in sessions)
        session_count = len(sessions)

        # 时间效率：平均会话时长
        avg_session_duration = total_duration / session_count if session_count > 0 else 0
        time_efficiency = min(avg_session_duration / 30, 1.0) * 100  # 30分钟为理想时长

        # 频率效率：会话频率
        if len(sessions) > 1:
            first_session = datetime.fromisoformat(sessions[0].get("start_time", "").replace('Z', '+00:00'))
            last_session = datetime.fromisoformat(sessions[-1].get("start_time", "").replace('Z', '+00:00'))
            days_span = max(1, (last_session - first_session).days)
            frequency = session_count / days_span
            frequency_efficiency = min(frequency / 1.0, 1.0) * 100  # 每天1次为理想频率
        else:
            frequency_efficiency = 0

        # 掌握效率：颜色变化比例
        color_changes = [e for e in events if e.get("event_type") == "color_changed"]
        positive_changes = len([c for c in color_changes if self._is_positive_change(c)])
        mastery_efficiency = (positive_changes / max(1, len(color_changes))) * 100 if color_changes else 0

        overall_efficiency = (time_efficiency + frequency_efficiency + mastery_efficiency) / 3

        return {
            "overall_efficiency": round(overall_efficiency, 1),
            "time_efficiency": round(time_efficiency, 1),
            "frequency_efficiency": round(frequency_efficiency, 1),
            "mastery_efficiency": round(mastery_efficiency, 1),
            "recommendations": self._generate_efficiency_recommendations(
                time_efficiency, frequency_efficiency, mastery_efficiency
            )
        }

    def _generate_recommendations_from_data(self, sessions: List[Dict[str, Any]],
                                           events: List[Dict[str, Any]]) -> List[str]:
        """基于真实数据生成学习建议"""
        recommendations = []

        if not sessions:
            return ["开始记录学习会话以获得个性化建议"]

        # 基于会话频率的建议
        if len(sessions) < 5:  # 少于5个会话
            recommendations.append("建议增加学习频率，保持连续性")

        # 基于会话时长的建议
        avg_duration = sum(s.get("duration", 0) for s in sessions) / len(sessions)
        if avg_duration < 15:  # 平均少于15分钟
            recommendations.append("建议延长单次学习时长，目标25-30分钟")
        elif avg_duration > 60:  # 平均超过60分钟
            recommendations.append("学习时间较长，注意适当休息")

        # 基于颜色变化的建议
        color_changes = [e for e in events if e.get("event_type") == "color_changed"]
        if len(color_changes) == 0:
            recommendations.append("积极参与学习活动，记录理解进展")
        else:
            positive_changes = len([c for c in color_changes if self._is_positive_change(c)])
            if positive_changes / len(color_changes) > 0.5:
                recommendations.append("学习进展良好，继续保持")
            else:
                recommendations.append("尝试不同的学习方法，提高理解效果")

        return recommendations if recommendations else ["学习状态良好，继续努力"]

    def _is_positive_change(self, color_change_event: Dict[str, Any]) -> bool:
        """判断颜色变化是否是积极的（向理解方向发展）"""
        old_color = color_change_event.get("old_value", "")
        new_color = color_change_event.get("new_value", "")

        # 颜色重要性映射
        color_importance = {
            "1": 0.2,  # 红色（不理解）
            "2": 1.0,  # 绿色（完全理解）
            "3": 0.6,  # 紫色（似懂非懂）
            "4": 0.2,  # 红色（不理解，备用编码）
            "5": 0.8,  # 蓝色（AI说明）
            "6": 0.4   # 黄色（个人理解）
        }

        old_importance = color_importance.get(old_color, 0.5)
        new_importance = color_importance.get(new_color, 0.5)

        return new_importance > old_importance

    def _count_current_colors(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计当前颜色分布"""
        current_colors = {}

        for event in events:
            if event.get("event_type") == "color_changed":
                node_id = event.get("node_id")
                new_color = event.get("new_value")
                if node_id and new_color:
                    current_colors[node_id] = new_color

        color_counts = {}
        for color in current_colors.values():
            color_counts[color] = color_counts.get(color, 0) + 1

        return color_counts

    def _find_peak_hour(self, heatmap_data: List[Dict[str, Any]]) -> int:
        """找到最活跃的小时"""
        max_activity = 0
        peak_hour = 14  # 默认下午2点

        for data_point in heatmap_data:
            if data_point["activity"] > max_activity:
                max_activity = data_point["activity"]
                peak_hour = data_point["hour"]

        return peak_hour

    def _find_peak_weekday(self, heatmap_data: List[Dict[str, Any]]) -> int:
        """找到最活跃的星期几"""
        max_activity = 0
        peak_weekday = 2  # 默认周二

        for data_point in heatmap_data:
            if data_point["activity"] > max_activity:
                max_activity = data_point["activity"]
                peak_weekday = data_point["weekday"]

        return peak_weekday

    def _generate_efficiency_recommendations(self, time_eff: float, freq_eff: float, mastery_eff: float) -> List[str]:
        """生成效率建议"""
        recommendations = []

        if time_eff < 50:
            recommendations.append("建议增加单次学习时长，目标25-30分钟")

        if freq_eff < 50:
            recommendations.append("建议增加学习频率，每周至少学习5次")

        if mastery_eff < 30:
            recommendations.append("建议复习已掌握内容，加强理解深度")
        elif mastery_eff > 80:
            recommendations.append("掌握度很高，可以学习新内容")

        if time_eff > 80 and freq_eff > 80:
            recommendations.append("学习效率很高，继续保持")

        if not recommendations:
            recommendations.append("学习状态良好，继续努力")

        return recommendations

# 全局实例
graphiti_reader = None

async def get_graphiti_reader() -> GraphitiTimelineReader:
    """获取Graphiti时间线读取器实例"""
    global graphiti_reader
    if graphiti_reader is None:
        graphiti_reader = GraphitiTimelineReader()
        await graphiti_reader.initialize()
    return graphiti_reader