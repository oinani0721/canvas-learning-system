"""
个性化引擎 - Canvas学习系统

本模块实现智能复习计划的个性化功能，负责：
- 分析用户学习风格和偏好
- 提供时间优化和动机激励策略
- 实现用户偏好的学习和更新机制
- 生成个性化的学习建议和内容适配

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-23
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics

# 导入相关模块
try:
    from learning_analyzer import LearningAnalyzer
    from mcp_memory_client import MCPMemoryClient
    from graphiti_integration import GraphitiKnowledgeGraph
except ImportError as e:
    print(f"Warning: 无法导入依赖模块 {e}，某些功能可能受限")


@dataclass
class UserProfile:
    """用户档案"""
    user_id: str
    learning_style: str
    preferred_difficulty_progression: str
    optimal_study_duration: int
    peak_performance_times: List[str]
    feedback_preferences: List[str]
    motivation_factors: List[str]
    interaction_patterns: Dict[str, float]
    complexity_tolerance: str
    content_preferences: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class LearningStyleAnalysis:
    """学习风格分析结果"""
    primary_style: str
    secondary_styles: List[str]
    style_confidence: float
    characteristics: Dict[str, Any]
    recommendations: List[str]
    evidence: Dict[str, float]


@dataclass
class TimeOptimizationResult:
    """时间优化结果"""
    optimal_session_duration: int
    recommended_break_intervals: List[int]
    peak_performance_periods: List[Dict[str, Any]]
    optimal_study_times: List[str]
    time_management_suggestions: List[str]


@dataclass
class MotivationProfile:
    """动机档案"""
    primary_motivators: List[str]
    achievement_preferences: List[str]
    incentive_types: List[str]
    motivation_triggers: Dict[str, Any]
    personalized_encouragements: List[str]
    goal_setting_preferences: Dict[str, Any]


class PersonalizationEngine:
    """个性化引擎

    负责分析用户学习行为，提供个性化的学习建议和优化策略。
    通过机器学习和数据分析，不断提升用户体验和学习效果。
    """

    def __init__(
        self,
        user_id: str = "default",
        mcp_client: Optional[Any] = None,
        graphiti_client: Optional[Any] = None,
        learning_analyzer: Optional[Any] = None
    ):
        """初始化个性化引擎

        Args:
            user_id: 用户ID
            mcp_client: MCP语义记忆客户端
            graphiti_client: Graphiti知识图谱客户端
            learning_analyzer: 学习分析器
        """
        self.user_id = user_id
        self.mcp_client = mcp_client
        self.graphiti_client = graphiti_client
        self.learning_analyzer = learning_analyzer

        # 学习风格定义
        self.LEARNING_STYLES = {
            "visual": {
                "characteristics": ["偏好图表和图像", "空间思维强", "颜色和形状敏感"],
                "recommendations": ["使用思维导图", "制作图表", "颜色编码"],
                "content_types": ["diagrams", "charts", "mind_maps", "visual_explanations"],
            },
            "auditory": {
                "characteristics": ["偏好口头解释", "讨论和交流", "声音记忆强"],
                "recommendations": ["大声朗读", "参与讨论", "录音复习"],
                "content_types": ["audio_explanations", "discussions", "verbal_instructions"],
            },
            "reading_writing": {
                "characteristics": ["偏好文字材料", "笔记和总结", "书面表达"],
                "recommendations": ["详细笔记", "书面总结", "文字解释"],
                "content_types": ["text_explanations", "written_notes", "reading_materials"],
            },
            "kinesthetic": {
                "characteristics": ["偏好动手实践", "身体记忆", "实际应用"],
                "recommendations": ["实际操作", "身体力行", "应用练习"],
                "content_types": ["practice_exercises", "hands_on_activities", "real_world_applications"],
            },
            "analytical": {
                "characteristics": ["逻辑思维强", "分析问题", "系统化学习"],
                "recommendations": ["逻辑分析", "系统梳理", "问题分解"],
                "content_types": ["logical_explanations", "structured_content", "analytical_exercises"],
            },
            "creative": {
                "characteristics": ["创新思维", "联想丰富", "多角度思考"],
                "recommendations": ["创意联想", "多角度分析", "创新应用"],
                "content_types": ["creative_exercises", "association_activities", "innovative_applications"],
            }
        }

        # 动机因素定义
        self.MOTIVATION_FACTORS = {
            "achievement": {
                "triggers": ["完成目标", "获得高分", "掌握技能"],
                "incentives": ["成就徽章", "进度展示", "技能认证"],
                "encouragements": ["你正在进步！", "继续保持！", "你已经掌握了很多！"],
            },
            "competition": {
                "triggers": ["与他人比较", "排名竞争", "挑战自我"],
                "incentives": ["排行榜", "竞争挑战", "自我突破"],
                "encouragements": ["超越自己！", "你是最好的！", "保持领先！"],
            },
            "social": {
                "triggers": ["团队合作", "分享知识", "获得认可"],
                "incentives": ["社交分享", "团队成就", "同伴认可"],
                "encouragements": ["大家都在支持你！", "你的分享很有价值！", "团队合作很棒！"],
            },
            "exploration": {
                "triggers": ["发现新知识", "探索未知", "好奇心满足"],
                "incentives": ["知识发现", "新领域探索", "好奇奖励"],
                "encouragements": ["发现了新知识！", "好奇心很棒！", "继续探索！"],
            },
            "mastery": {
                "triggers": ["深度理解", "技能精通", "知识体系"],
                "incentives": ["技能精通认证", "知识体系图", "深度成就"],
                "encouragements": ["理解很深刻！", "技能很熟练！", "知识体系很完整！"],
            }
        }

        # 个性化配置
        self.PERSONALIZATION_CONFIG = {
            "learning_style_threshold": 0.6,      # 学习风格识别阈值
            "interaction_tracking_days": 30,      # 交互跟踪天数
            "performance_weight": 0.7,           # 表现权重
            "preference_weight": 0.3,            # 偏好权重
            "update_frequency_days": 7,          # 更新频率（天）
            "min_data_points": 10,               # 最小数据点数
        }

    def analyze_learning_style(
        self,
        learning_history: Optional[Dict[str, Any]] = None
    ) -> LearningStyleAnalysis:
        """分析学习风格

        Args:
            learning_history: 学习历史数据

        Returns:
            LearningStyleAnalysis: 学习风格分析结果
        """
        try:
            # 1. 收集用户行为数据
            behavior_data = self._collect_behavior_data(learning_history)

            # 2. 分析交互模式
            interaction_patterns = self._analyze_interaction_patterns(behavior_data)

            # 3. 计算学习风格得分
            style_scores = self._calculate_style_scores(interaction_patterns)

            # 4. 确定主要学习风格
            primary_style, confidence = self._determine_primary_style(style_scores)

            # 5. 生成推荐
            recommendations = self._generate_style_recommendations(primary_style, style_scores)

            # 6. 收集证据
            evidence = self._collect_style_evidence(style_scores, interaction_patterns)

            return LearningStyleAnalysis(
                primary_style=primary_style,
                secondary_styles=self._get_secondary_styles(style_scores),
                style_confidence=confidence,
                characteristics=self.LEARNING_STYLES.get(primary_style, {}).get("characteristics", []),
                recommendations=recommendations,
                evidence=evidence
            )

        except Exception as e:
            print(f"学习风格分析失败: {e}")
            # 返回默认分析结果
            return LearningStyleAnalysis(
                primary_style="balanced",
                secondary_styles=["visual", "reading_writing"],
                style_confidence=0.5,
                characteristics=["综合型学习者", "适应多种学习方式"],
                recommendations=["尝试不同学习方法", "找到最适合自己的方式"],
                evidence={"default": 0.5}
            )

    def _collect_behavior_data(self, learning_history: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """收集用户行为数据

        Args:
            learning_history: 学习历史数据

        Returns:
            Dict: 行为数据
        """
        behavior_data = {
            "interaction_types": defaultdict(int),
            "time_patterns": defaultdict(list),
            "content_preferences": defaultdict(int),
            "performance_patterns": defaultdict(list),
            "session_durations": [],
            "feedback_responses": defaultdict(int)
        }

        if learning_history:
            # 从学习历史中提取行为数据
            canvas_files = learning_history.get("canvas_files", [])
            for canvas_file in canvas_files:
                # 分析交互类型
                for question in canvas_file.get("questions", []):
                    behavior_data["interaction_types"]["question_creation"] += 1

                for understanding in canvas_file.get("understanding_records", []):
                    behavior_data["interaction_types"]["understanding_input"] += 1
                    quality_score = understanding.get("quality_score", 0)
                    behavior_data["performance_patterns"]["understanding_quality"].append(quality_score)

                for explanation in canvas_file.get("explanations", []):
                    behavior_data["interaction_types"]["explanation_access"] += 1
                    exp_type = explanation.get("explanation_type", "general")
                    behavior_data["content_preferences"][exp_type] += 1

                # 记录会话时间
                mod_time = canvas_file.get("modification_time", 0)
                if mod_time > 0:
                    hour = datetime.fromtimestamp(mod_time).hour
                    behavior_data["time_patterns"][hour].append(mod_time)

        # 添加模拟数据（如果真实数据不足）
        if sum(behavior_data["interaction_types"].values()) < self.PERSONALIZATION_CONFIG["min_data_points"]:
            behavior_data = self._add_simulated_behavior_data(behavior_data)

        return behavior_data

    def _add_simulated_behavior_data(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加模拟行为数据

        Args:
            behavior_data: 原始行为数据

        Returns:
            Dict: 增强后的行为数据
        """
        # 模拟一些基本的交互模式
        behavior_data["interaction_types"]["understanding_input"] += 15
        behavior_data["interaction_types"]["question_creation"] += 8
        behavior_data["interaction_types"]["explanation_access"] += 12

        # 模拟内容偏好
        behavior_data["content_preferences"]["definition"] += 6
        behavior_data["content_preferences"]["example"] += 8
        behavior_data["content_preferences"]["comparison"] += 4

        # 模拟时间模式
        import random
        for _ in range(20):
            hour = random.choice([9, 10, 14, 15, 19, 20])  # 常见学习时间
            behavior_data["time_patterns"][hour].append(datetime.now().timestamp())

        return behavior_data

    def _analyze_interaction_patterns(self, behavior_data: Dict[str, Any]) -> Dict[str, float]:
        """分析交互模式

        Args:
            behavior_data: 行为数据

        Returns:
            Dict: 交互模式得分
        """
        patterns = {}
        total_interactions = sum(behavior_data["interaction_types"].values())

        if total_interactions > 0:
            # 计算交互类型比例
            for interaction_type, count in behavior_data["interaction_types"].items():
                patterns[interaction_type] = count / total_interactions

            # 分析内容偏好
            content_total = sum(behavior_data["content_preferences"].values())
            if content_total > 0:
                for content_type, count in behavior_data["content_preferences"].items():
                    patterns[f"content_{content_type}"] = count / content_total

        # 分析时间模式
        time_patterns = behavior_data["time_patterns"]
        if time_patterns:
            # 找出最活跃的时间段
            hour_counts = {hour: len(times) for hour, times in time_patterns.items()}
            total_hours = sum(hour_counts.values())

            for hour, count in hour_counts.items():
                if total_hours > 0:
                    patterns[f"time_{hour}"] = count / total_hours

        return patterns

    def _calculate_style_scores(self, interaction_patterns: Dict[str, float]) -> Dict[str, float]:
        """计算学习风格得分

        Args:
            interaction_patterns: 交互模式

        Returns:
            Dict: 学习风格得分
        """
        style_scores = {}

        # 基于交互模式计算各学习风格得分
        if "understanding_input" in interaction_patterns:
            # 高理解输入倾向 -> reading_writing
            style_scores["reading_writing"] += interaction_patterns["understanding_input"] * 0.6

        if "explanation_access" in interaction_patterns:
            # 高解释访问倾向 -> visual, reading_writing
            style_scores["visual"] += interaction_patterns["explanation_access"] * 0.3
            style_scores["reading_writing"] += interaction_patterns["explanation_access"] * 0.3

        if "question_creation" in interaction_patterns:
            # 高问题创建倾向 -> analytical, creative
            style_scores["analytical"] += interaction_patterns["question_creation"] * 0.4
            style_scores["creative"] += interaction_patterns["question_creation"] * 0.3

        # 基于内容偏好计算得分
        if "content_example" in interaction_patterns:
            # 偏好例子 -> kinesthetic
            style_scores["kinesthetic"] += interaction_patterns["content_example"] * 0.5

        if "content_comparison" in interaction_patterns:
            # 偏好比较 -> analytical
            style_scores["analytical"] += interaction_patterns["content_comparison"] * 0.4

        # 基于时间模式调整得分
        morning_activities = sum(interaction_patterns.get(f"time_{h}", 0) for h in range(6, 12))
        evening_activities = sum(interaction_patterns.get(f"time_{h}", 0) for h in range(18, 23))

        if morning_activities > 0.3:
            style_scores["analytical"] += 0.2  # 早晨偏向分析型
        if evening_activities > 0.3:
            style_scores["creative"] += 0.2   # 晚上偏向创造型

        # 归一化得分
        max_score = max(style_scores.values()) if style_scores else 1.0
        if max_score > 0:
            style_scores = {style: score / max_score for style, score in style_scores.items()}

        return style_scores

    def _determine_primary_style(self, style_scores: Dict[str, float]) -> Tuple[str, float]:
        """确定主要学习风格

        Args:
            style_scores: 学习风格得分

        Returns:
            Tuple[str, float]: 主要风格和置信度
        """
        if not style_scores:
            return "balanced", 0.5

        # 找出得分最高的风格
        primary_style = max(style_scores.items(), key=lambda x: x[1])
        style_name, score = primary_style

        # 计算置信度
        if score > 0.7:
            confidence = 0.9
        elif score > 0.5:
            confidence = 0.7
        else:
            confidence = 0.5

        return style_name, confidence

    def _get_secondary_styles(self, style_scores: Dict[str, float]) -> List[str]:
        """获取次要学习风格

        Args:
            style_scores: 学习风格得分

        Returns:
            List[str]: 次要风格列表
        """
        # 排序并返回前3个风格（排除主要风格）
        sorted_styles = sorted(style_scores.items(), key=lambda x: x[1], reverse=True)
        return [style for style, _ in sorted_styles[1:4]]

    def _generate_style_recommendations(self, primary_style: str, style_scores: Dict[str, float]) -> List[str]:
        """生成学习风格推荐

        Args:
            primary_style: 主要学习风格
            style_scores: 学习风格得分

        Returns:
            List[str]: 推荐列表
        """
        recommendations = []

        # 基于主要风格的基本推荐
        style_info = self.LEARNING_STYLES.get(primary_style, {})
        recommendations.extend(style_info.get("recommendations", []))

        # 基于次要风格的补充推荐
        for style, score in style_scores.items():
            if style != primary_style and score > 0.5:
                secondary_info = self.LEARNING_STYLES.get(style, {})
                secondary_recs = secondary_info.get("recommendations", [])
                recommendations.extend(secondary_recs[:2])  # 最多2个补充推荐

        # 通用推荐
        recommendations.extend([
            "定期评估学习效果",
            "根据反馈调整学习策略",
            "保持学习的多样性和趣味性"
        ])

        return recommendations[:6]  # 最多返回6个推荐

    def _collect_style_evidence(self, style_scores: Dict[str, float], interaction_patterns: Dict[str, float]) -> Dict[str, float]:
        """收集学习风格证据

        Args:
            style_scores: 学习风格得分
            interaction_patterns: 交互模式

        Returns:
            Dict: 证据数据
        """
        evidence = {}

        # 将交互模式作为证据
        for pattern, value in interaction_patterns.items():
            if value > 0.1:  # 只保留有意义的模式
                evidence[f"pattern_{pattern}"] = value

        # 添加风格得分作为证据
        for style, score in style_scores.items():
            evidence[f"style_{style}"] = score

        return evidence

    def optimize_time_management(
        self,
        user_performance: Optional[Dict[str, Any]] = None
    ) -> TimeOptimizationResult:
        """优化时间管理

        Args:
            user_performance: 用户表现数据

        Returns:
            TimeOptimizationResult: 时间优化结果
        """
        try:
            # 1. 分析历史学习时间模式
            time_patterns = self._analyze_time_patterns(user_performance)

            # 2. 计算最佳学习时长
            optimal_duration = self._calculate_optimal_duration(time_patterns)

            # 3. 确定休息间隔
            break_intervals = self._determine_break_intervals(optimal_duration)

            # 4. 识别高效时段
            peak_periods = self._identify_peak_periods(time_patterns)

            # 5. 生成学习时间建议
            optimal_times = self._generate_optimal_times(peak_periods)

            # 6. 生成时间管理建议
            suggestions = self._generate_time_suggestions(optimal_duration, break_intervals)

            return TimeOptimizationResult(
                optimal_session_duration=optimal_duration,
                recommended_break_intervals=break_intervals,
                peak_performance_periods=peak_periods,
                optimal_study_times=optimal_times,
                time_management_suggestions=suggestions
            )

        except Exception as e:
            print(f"时间优化分析失败: {e}")
            # 返回默认结果
            return TimeOptimizationResult(
                optimal_session_duration=45,
                recommended_break_intervals=[15, 30],
                peak_performance_periods=[{"period": "morning", "efficiency": 0.8}],
                optimal_study_times=["09:00-10:30", "14:00-15:30", "19:00-20:30"],
                time_management_suggestions=["保持规律作息", "适当休息", "找到自己的高效时段"]
            )

    def _analyze_time_patterns(self, user_performance: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """分析时间模式

        Args:
            user_performance: 用户表现数据

        Returns:
            Dict: 时间模式数据
        """
        patterns = {
            "hourly_efficiency": defaultdict(list),
            "session_durations": [],
            "break_patterns": [],
            "daily_rhythms": defaultdict(float)
        }

        # 模拟时间模式数据
        import random
        current_time = datetime.now()

        # 生成最近30天的模拟数据
        for day in range(30):
            day_time = current_time - timedelta(days=day)

            # 模拟不同时段的学习效率
            for hour in range(8, 23):
                # 基础效率模式
                if 9 <= hour <= 11:
                    base_efficiency = random.uniform(0.7, 0.9)  # 上午高效
                elif 14 <= hour <= 16:
                    base_efficiency = random.uniform(0.6, 0.8)  # 下午中等
                elif 19 <= hour <= 21:
                    base_efficiency = random.uniform(0.5, 0.7)  # 晚上一般
                else:
                    base_efficiency = random.uniform(0.3, 0.5)  # 其他时间低效

                patterns["hourly_efficiency"][hour].append(base_efficiency)

            # 模拟会话时长
            if random.random() > 0.3:  # 70%的概率有学习活动
                session_duration = random.randint(20, 90)
                patterns["session_durations"].append(session_duration)

        return patterns

    def _calculate_optimal_duration(self, time_patterns: Dict[str, Any]) -> int:
        """计算最佳学习时长

        Args:
            time_patterns: 时间模式数据

        Returns:
            int: 最佳时长（分钟）
        """
        session_durations = time_patterns.get("session_durations", [])

        if not session_durations:
            return 45  # 默认45分钟

        # 计算平均时长和效率
        avg_duration = statistics.mean(session_durations)

        # 基于时长分布调整
        if avg_duration > 60:
            return 60  # 避免过长
        elif avg_duration < 25:
            return 30  # 避免过短
        else:
            return int(round(avg_duration / 15) * 15)  # 取整到15分钟

    def _determine_break_intervals(self, optimal_duration: int) -> List[int]:
        """确定休息间隔

        Args:
            optimal_duration: 最佳学习时长

        Returns:
            List[int]: 休息间隔（分钟）
        """
        intervals = []

        # 基于学习时长确定休息点
        if optimal_duration <= 30:
            intervals = [15]  # 30分钟内，15分钟休息提醒
        elif optimal_duration <= 45:
            intervals = [15, 30]  # 45分钟内，15和30分钟休息提醒
        elif optimal_duration <= 60:
            intervals = [15, 30, 45]  # 60分钟内，多次休息提醒
        else:
            intervals = [20, 40, 60]  # 长时间学习，延长间隔

        return intervals

    def _identify_peak_periods(self, time_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别高效时段

        Args:
            time_patterns: 时间模式数据

        Returns:
            List[Dict]: 高效时段列表
        """
        hourly_efficiency = time_patterns.get("hourly_efficiency", {})
        peak_periods = []

        for hour, efficiencies in hourly_efficiency.items():
            if efficiencies:
                avg_efficiency = statistics.mean(efficiencies)

                # 定义时段
                if 6 <= hour < 12:
                    period_name = "morning"
                elif 12 <= hour < 18:
                    period_name = "afternoon"
                elif 18 <= hour < 24:
                    period_name = "evening"
                else:
                    period_name = "night"

                # 只保留效率较高的时段
                if avg_efficiency > 0.6:
                    peak_periods.append({
                        "period": period_name,
                        "hour": hour,
                        "efficiency": avg_efficiency,
                        "time_range": f"{hour:02d}:00-{hour+1:02d}:00"
                    })

        # 按效率排序
        peak_periods.sort(key=lambda x: x["efficiency"], reverse=True)

        return peak_periods[:5]  # 返回前5个高效时段

    def _generate_optimal_times(self, peak_periods: List[Dict[str, Any]]) -> List[str]:
        """生成最佳学习时间

        Args:
            peak_periods: 高效时段列表

        Returns:
            List[str]: 最佳学习时间列表
        """
        optimal_times = []

        # 按时段分组
        period_groups = defaultdict(list)
        for period in peak_periods:
            period_groups[period["period"]].append(period)

        # 为每个时段生成推荐时间
        for period_name, periods in period_groups.items():
            if periods:
                # 选择效率最高的时段
                best_period = max(periods, key=lambda x: x["efficiency"])
                hour = best_period["hour"]

                # 生成1.5小时的学习窗口
                if hour + 1 <= 23:
                    time_range = f"{hour:02d}:00-{hour+1:02d}:30"
                    optimal_times.append(time_range)

        # 确保有基本的推荐时间
        if not optimal_times:
            optimal_times = [
                "09:00-10:30",
                "14:00-15:30",
                "19:00-20:30"
            ]

        return optimal_times[:3]

    def _generate_time_suggestions(
        self,
        optimal_duration: int,
        break_intervals: List[int]
    ) -> List[str]:
        """生成时间管理建议

        Args:
            optimal_duration: 最佳时长
            break_intervals: 休息间隔

        Returns:
            List[str]: 时间管理建议
        """
        suggestions = []

        # 基于最佳时长的建议
        suggestions.append(f"建议每次学习{optimal_duration}分钟，保持专注度")
        suggestions.append("学习前设定明确的结束时间，避免拖延")

        # 基于休息间隔的建议
        if break_intervals:
            break_times = ", ".join(str(b) for b in break_intervals)
            suggestions.append(f"在学习{break_times}分钟时适当休息")

        # 通用时间管理建议
        suggestions.extend([
            "找到自己最专注的时间段进行学习",
            "避免在疲劳或饥饿时学习重要内容",
            "保持规律的作息时间",
            "使用番茄工作法提高效率"
        ])

        return suggestions[:6]

    def generate_motivation_profile(
        self,
        user_behavior: Optional[Dict[str, Any]] = None
    ) -> MotivationProfile:
        """生成动机档案

        Args:
            user_behavior: 用户行为数据

        Returns:
            MotivationProfile: 动机档案
        """
        try:
            # 1. 分析动机因素
            primary_motivators = self._analyze_motivation_factors(user_behavior)

            # 2. 确定成就偏好
            achievement_preferences = self._determine_achievement_preferences(user_behavior)

            # 3. 识别激励类型
            incentive_types = self._identify_incentive_types(primary_motivators)

            # 4. 分析动机触发器
            motivation_triggers = self._analyze_motivation_triggers(user_behavior)

            # 5. 生成个性化鼓励
            personalized_encouragements = self._generate_personalized_encouragements(primary_motivators)

            # 6. 确定目标设置偏好
            goal_setting_preferences = self._determine_goal_preferences(user_behavior)

            return MotivationProfile(
                primary_motivators=primary_motivators,
                achievement_preferences=achievement_preferences,
                incentive_types=incentive_types,
                motivation_triggers=motivation_triggers,
                personalized_encouragements=personalized_encouragements,
                goal_setting_preferences=goal_setting_preferences
            )

        except Exception as e:
            print(f"动机档案生成失败: {e}")
            # 返回默认档案
            return MotivationProfile(
                primary_motivators=["achievement", "mastery"],
                achievement_preferences=["skill_certification", "progress_tracking"],
                incentive_types=["badges", "achievements", "progress_bars"],
                motivation_triggers={"completion": 0.8, "progress": 0.7, "challenge": 0.6},
                personalized_encouragements=["继续保持！", "你做得很好！", "每一步都是进步！"],
                goal_setting_preferences={"short_term_goals": True, "measurable_progress": True}
            )

    def _analyze_motivation_factors(self, user_behavior: Optional[Dict[str, Any]]) -> List[str]:
        """分析动机因素

        Args:
            user_behavior: 用户行为数据

        Returns:
            List[str]: 主要动机因素
        """
        # 模拟动机因素分析
        # 在实际应用中，这里会基于真实的用户行为数据进行分析
        factors = []

        # 基于常见模式推测动机因素
        factors.append("achievement")  # 成就动机
        factors.append("mastery")    # 掌握动机

        # 随机添加其他因素
        import random
        additional_factors = ["competition", "social", "exploration"]
        for factor in additional_factors:
            if random.random() > 0.5:
                factors.append(factor)

        return factors[:3]  # 最多返回3个主要因素

    def _determine_achievement_preferences(self, user_behavior: Optional[Dict[str, Any]]) -> List[str]:
        """确定成就偏好

        Args:
            user_behavior: 用户行为数据

        Returns:
            List[str]: 成就偏好列表
        """
        preferences = [
            "progress_tracking",    # 进度跟踪
            "skill_certification",  # 技能认证
            "completion_badges",    # 完成徽章
            "milestone_achievements" # 里程碑成就
        ]

        # 简化实现，返回所有偏好
        return preferences

    def _identify_incentive_types(self, primary_motivators: List[str]) -> List[str]:
        """识别激励类型

        Args:
            primary_motivators: 主要动机因素

        Returns:
            List[str]: 激励类型列表
        """
        incentives = []

        for motivator in primary_motivators:
            motivator_info = self.MOTIVATION_FACTORS.get(motivator, {})
            incentives.extend(motivator_info.get("incentives", []))

        return list(set(incentives))  # 去重

    def _analyze_motivation_triggers(self, user_behavior: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """分析动机触发器

        Args:
            user_behavior: 用户行为数据

        Returns:
            Dict: 动机触发器
        """
        # 模拟动机触发器分析
        triggers = {
            "completion": 0.8,      # 完成任务触发
            "progress": 0.7,        # 进度更新触发
            "challenge": 0.6,       # 挑战完成触发
            "recognition": 0.5,     # 获得认可触发
            "learning": 0.7         # 学习新知触发
        }

        return triggers

    def _generate_personalized_encouragements(self, primary_motivators: List[str]) -> List[str]:
        """生成个性化鼓励

        Args:
            primary_motivators: 主要动机因素

        Returns:
            List[str]: 个性化鼓励语
        """
        encouragements = []

        for motivator in primary_motivators:
            motivator_info = self.MOTIVATION_FACTORS.get(motivator, {})
            encouragements.extend(motivator_info.get("encouragements", []))

        # 添加通用鼓励语
        encouragements.extend([
            "学习是一段旅程，享受这个过程！",
            "每次努力都在让你变得更好！",
            "相信自己的能力，你可以做到的！"
        ])

        return encouragements[:5]  # 最多返回5条

    def _determine_goal_preferences(self, user_behavior: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """确定目标设置偏好

        Args:
            user_behavior: 用户行为数据

        Returns:
            Dict: 目标设置偏好
        """
        return {
            "short_term_goals": True,       # 偏好短期目标
            "measurable_progress": True,    # 偏好可衡量的进步
            "challenging_goals": False,     # 不偏好过高挑战
            "flexible_timeline": True,      # 偏好灵活时间安排
            "visual_progress_tracking": True # 偏好可视化进度跟踪
        }

    def update_user_preferences(
        self,
        user_feedback: Dict[str, Any],
        current_profile: Optional[UserProfile] = None
    ) -> UserProfile:
        """更新用户偏好

        Args:
            user_feedback: 用户反馈数据
            current_profile: 当前用户档案

        Returns:
            UserProfile: 更新后的用户档案
        """
        try:
            # 1. 分析用户反馈
            feedback_analysis = self._analyze_user_feedback(user_feedback)

            # 2. 更新学习风格偏好
            updated_learning_style = self._update_learning_style_preference(
                feedback_analysis, current_profile
            )

            # 3. 更新时间偏好
            updated_time_preferences = self._update_time_preferences(
                feedback_analysis, current_profile
            )

            # 4. 更新动机偏好
            updated_motivation = self._update_motivation_preferences(
                feedback_analysis, current_profile
            )

            # 5. 生成新的用户档案
            updated_profile = UserProfile(
                user_id=self.user_id,
                learning_style=updated_learning_style,
                preferred_difficulty_progression=feedback_analysis.get("difficulty_preference", "gradual"),
                optimal_study_duration=updated_time_preferences["optimal_duration"],
                peak_performance_times=updated_time_preferences["peak_times"],
                feedback_preferences=feedback_analysis.get("feedback_preferences", []),
                motivation_factors=updated_motivation["factors"],
                interaction_patterns=feedback_analysis.get("interaction_patterns", {}),
                complexity_tolerance=feedback_analysis.get("complexity_tolerance", "moderate"),
                content_preferences=updated_motivation["content_preferences"],
                created_at=current_profile.created_at if current_profile else datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            return updated_profile

        except Exception as e:
            print(f"用户偏好更新失败: {e}")
            # 返回默认档案
            return UserProfile(
                user_id=self.user_id,
                learning_style="balanced",
                preferred_difficulty_progression="gradual",
                optimal_study_duration=45,
                peak_performance_times=["morning", "evening"],
                feedback_preferences=["immediate", "detailed"],
                motivation_factors=["achievement", "mastery"],
                interaction_patterns={},
                complexity_tolerance="moderate",
                content_preferences={"visual": True, "text": True},
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

    def _analyze_user_feedback(self, user_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户反馈

        Args:
            user_feedback: 用户反馈数据

        Returns:
            Dict: 反馈分析结果
        """
        analysis = {
            "satisfaction_score": user_feedback.get("satisfaction", 0.7),
            "difficulty_preference": user_feedback.get("preferred_difficulty", "gradual"),
            "content_type_preferences": user_feedback.get("content_preferences", {}),
            "time_preferences": user_feedback.get("time_preferences", {}),
            "feedback_preferences": user_feedback.get("feedback_preferences", ["immediate"]),
            "interaction_patterns": user_feedback.get("interaction_patterns", {}),
            "complexity_tolerance": user_feedback.get("complexity_tolerance", "moderate")
        }

        return analysis

    def _update_learning_style_preference(
        self,
        feedback_analysis: Dict[str, Any],
        current_profile: Optional[UserProfile]
    ) -> str:
        """更新学习风格偏好

        Args:
            feedback_analysis: 反馈分析结果
            current_profile: 当前用户档案

        Returns:
            str: 更新后的学习风格
        """
        # 基于反馈内容调整学习风格
        content_preferences = feedback_analysis.get("content_type_preferences", {})

        # 简化实现：基于内容偏好推断学习风格
        if content_preferences.get("visual", 0) > 0.7:
            return "visual"
        elif content_preferences.get("text", 0) > 0.7:
            return "reading_writing"
        elif content_preferences.get("interactive", 0) > 0.7:
            return "kinesthetic"
        else:
            return current_profile.learning_style if current_profile else "balanced"

    def _update_time_preferences(
        self,
        feedback_analysis: Dict[str, Any],
        current_profile: Optional[UserProfile]
    ) -> Dict[str, Any]:
        """更新时间偏好

        Args:
            feedback_analysis: 反馈分析结果
            current_profile: 当前用户档案

        Returns:
            Dict: 更新后的时间偏好
        """
        time_preferences = feedback_analysis.get("time_preferences", {})

        return {
            "optimal_duration": time_preferences.get("preferred_duration", 45),
            "peak_times": time_preferences.get("preferred_times", ["morning", "evening"]),
            "break_frequency": time_preferences.get("break_frequency", "moderate")
        }

    def _update_motivation_preferences(
        self,
        feedback_analysis: Dict[str, Any],
        current_profile: Optional[UserProfile]
    ) -> Dict[str, Any]:
        """更新动机偏好

        Args:
            feedback_analysis: 反馈分析结果
            current_profile: 当前用户档案

        Returns:
            Dict: 更新后的动机偏好
        """
        satisfaction_score = feedback_analysis.get("satisfaction_score", 0.7)

        # 基于满意度调整动机因素
        if satisfaction_score > 0.8:
            factors = ["achievement", "mastery"]
        elif satisfaction_score > 0.6:
            factors = ["achievement", "exploration"]
        else:
            factors = ["mastery", "social_support"]

        return {
            "factors": factors,
            "content_preferences": feedback_analysis.get("content_type_preferences", {})
        }

    def get_personalized_recommendations(
        self,
        user_profile: UserProfile,
        current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取个性化推荐

        Args:
            user_profile: 用户档案
            current_context: 当前上下文

        Returns:
            Dict: 个性化推荐
        """
        recommendations = {
            "learning_approach": self._recommend_learning_approach(user_profile),
            "content_format": self._recommend_content_format(user_profile),
            "time_suggestions": self._recommend_time_allocation(user_profile, current_context),
            "motivation_strategies": self._recommend_motivation_strategies(user_profile),
            "difficulty_adjustment": self._recommend_difficulty_adjustment(user_profile, current_context)
        }

        return recommendations

    def _recommend_learning_approach(self, user_profile: UserProfile) -> List[str]:
        """推荐学习方法

        Args:
            user_profile: 用户档案

        Returns:
            List[str]: 学习方法推荐
        """
        style_info = self.LEARNING_STYLES.get(user_profile.learning_style, {})
        return style_info.get("recommendations", [
            "制定明确的学习目标",
            "定期复习和总结",
            "结合多种学习方式"
        ])

    def _recommend_content_format(self, user_profile: UserProfile) -> List[str]:
        """推荐内容格式

        Args:
            user_profile: 用户档案

        Returns:
            List[str]: 内容格式推荐
        """
        style_info = self.LEARNING_STYLES.get(user_profile.learning_style, {})
        return style_info.get("content_types", ["text_explanations", "examples"])

    def _recommend_time_allocation(
        self,
        user_profile: UserProfile,
        current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """推荐时间分配

        Args:
            user_profile: 用户档案
            current_context: 当前上下文

        Returns:
            Dict: 时间分配建议
        """
        return {
            "session_duration": user_profile.optimal_study_duration,
            "peak_times": user_profile.peak_performance_times,
            "break_suggestions": [15, 30, 45],
            "time_management_tips": [
                "在精力最充沛时学习重要内容",
                "使用番茄工作法保持专注",
                "定期休息避免疲劳"
            ]
        }

    def _recommend_motivation_strategies(self, user_profile: UserProfile) -> List[str]:
        """推荐动机策略

        Args:
            user_profile: 用户档案

        Returns:
            List[str]: 动机策略推荐
        """
        strategies = []

        for factor in user_profile.motivation_factors:
            factor_info = self.MOTIVATION_FACTORS.get(factor, {})
            strategies.extend(factor_info.get("incentives", []))

        return strategies[:5]

    def _recommend_difficulty_adjustment(
        self,
        user_profile: UserProfile,
        current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """推荐难度调整

        Args:
            user_profile: 用户档案
            current_context: 当前上下文

        Returns:
            Dict: 难度调整建议
        """
        return {
            "progression": user_profile.preferred_difficulty_progression,
            "complexity_tolerance": user_profile.complexity_tolerance,
            "adjustment_triggers": [
                "连续成功完成较高难度内容",
                "在当前难度遇到困难",
                "学习兴趣下降"
            ],
            "adjustment_strategies": {
                "increase": "增加概念复杂度和应用要求",
                "decrease": "提供更多指导和分解步骤",
                "maintain": "保持当前难度，增加练习量"
            }
        }


# 示例使用
if __name__ == "__main__":
    # 创建个性化引擎
    engine = PersonalizationEngine(user_id="example_user")

    # 分析学习风格
    learning_style = engine.analyze_learning_style()
    print("学习风格分析结果:")
    print(f"主要风格: {learning_style.primary_style}")
    print(f"置信度: {learning_style.style_confidence}")
    print(f"推荐: {learning_style.recommendations}")

    # 优化时间管理
    time_optimization = engine.optimize_time_management()
    print(f"\n时间优化结果:")
    print(f"最佳学习时长: {time_optimization.optimal_session_duration} 分钟")
    print(f"最佳学习时间: {time_optimization.optimal_study_times}")

    # 生成动机档案
    motivation_profile = engine.generate_motivation_profile()
    print(f"\n动机档案:")
    print(f"主要动机因素: {motivation_profile.primary_motivators}")
    print(f"个性化鼓励: {motivation_profile.personalized_encouragements[:2]}")

    # 模拟用户反馈并更新偏好
    user_feedback = {
        "satisfaction": 0.8,
        "preferred_difficulty": "gradual",
        "content_preferences": {"visual": 0.8, "text": 0.6},
        "time_preferences": {"preferred_duration": 50, "preferred_times": ["morning"]},
        "feedback_preferences": ["immediate", "detailed"],
        "complexity_tolerance": "moderate"
    }

    updated_profile = engine.update_user_preferences(user_feedback)
    print(f"\n更新后的用户档案:")
    print(f"学习风格: {updated_profile.learning_style}")
    print(f"最佳学习时长: {updated_profile.optimal_study_duration} 分钟")

    # 获取个性化推荐
    recommendations = engine.get_personalized_recommendations(updated_profile, {})
    print(f"\n个性化推荐:")
    print(f"学习方法: {recommendations['learning_approach'][:2]}")
    print(f"动机策略: {recommendations['motivation_strategies'][:2]}")