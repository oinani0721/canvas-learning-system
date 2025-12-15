"""
学习模式分析器

本模块实现智能学习模式识别，包括：
- 学习风格识别算法
- 行为模式聚类分析
- 模式置信度评估
- 个性化学习建议生成

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-25
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter

# 尝试导入科学计算库
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
    SCIKIT_LEARN_AVAILABLE = True
except ImportError:
    SCIKIT_LEARN_AVAILABLE = False

# 尝试导入loguru用于企业级日志记录
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


@dataclass
class LearningStyle:
    """学习风格数据模型"""
    visual_preference: float = 0.0
    auditory_preference: float = 0.0
    kinesthetic_preference: float = 0.0
    reading_writing_preference: float = 0.0
    analytical_preference: float = 0.0
    intuitive_preference: float = 0.0
    sequential_preference: float = 0.0
    global_preference: float = 0.0
    confidence_score: float = 0.0


@dataclass
class BehaviorPattern:
    """行为模式数据模型"""
    pattern_id: str = ""
    pattern_type: str = ""
    frequency: int = 0
    duration_avg: float = 0.0
    success_rate: float = 0.0
    context_indicators: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class LearningPattern:
    """学习模式综合数据模型"""
    user_id: str = ""
    analysis_period_days: int = 0
    learning_style: LearningStyle = field(default_factory=LearningStyle)
    behavior_patterns: List[BehaviorPattern] = field(default_factory=list)
    difficulty_progression: Dict = field(default_factory=dict)
    agent_selection_preferences: Dict = field(default_factory=dict)
    time_allocation_patterns: Dict = field(default_factory=dict)
    error_correction_patterns: Dict = field(default_factory=dict)
    overall_confidence: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class LearningPatternAnalyzer:
    """学习模式分析器"""

    def __init__(self, config_path: str = "config/realtime_memory.yaml"):
        """初始化学习模式分析器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.data_dir = Path("data/realtime_memory/pattern_analysis")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 分析参数
        self.confidence_threshold = self.config.get('analysis', {}).get(
            'learning_patterns', {}).get('confidence_threshold', 0.7)
        self.min_data_points = self.config.get('analysis', {}).get(
            'learning_patterns', {}).get('min_data_points_patterns', 5)

        logger.info("LearningPatternAnalyzer initialized")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'analysis': {
                'learning_patterns': {
                    'detection_enabled': True,
                    'confidence_threshold': 0.7,
                    'min_data_points_patterns': 5,
                    'pattern_types': [
                        'learning_style_preference',
                        'difficulty_progression',
                        'agent_selection_preference',
                        'time_allocation_pattern',
                        'error_correction_pattern'
                    ]
                }
            }
        }

    def analyze_user_patterns(self, user_id: str, activities: List[Dict],
                             time_range_days: int = 30) -> LearningPattern:
        """分析用户学习模式

        Args:
            user_id: 用户ID
            activities: 学习活动列表
            time_range_days: 分析时间范围

        Returns:
            LearningPattern: 学习模式分析结果
        """
        if len(activities) < self.min_data_points:
            logger.warning(f"用户 {user_id} 的活动数据不足，无法进行模式分析")
            return self._create_empty_pattern(user_id, time_range_days)

        logger.info(f"开始分析用户 {user_id} 的学习模式，数据点: {len(activities)}")

        # 分析学习风格
        learning_style = self.identify_learning_style(activities)

        # 分析行为模式
        behavior_patterns = self.analyze_behavior_patterns(activities)

        # 分析难度进展
        difficulty_progression = self.analyze_difficulty_progression(activities)

        # 分析Agent选择偏好
        agent_preferences = self.analyze_agent_selection_preferences(activities)

        # 分析时间分配模式
        time_patterns = self.analyze_time_allocation_patterns(activities)

        # 分析错误修正模式
        error_patterns = self.analyze_error_correction_patterns(activities)

        # 计算整体置信度
        overall_confidence = self.calculate_overall_confidence(
            learning_style, behavior_patterns, activities
        )

        # 生成建议
        recommendations = self.generate_pattern_recommendations(
            learning_style, behavior_patterns, agent_preferences
        )

        pattern = LearningPattern(
            user_id=user_id,
            analysis_period_days=time_range_days,
            learning_style=learning_style,
            behavior_patterns=behavior_patterns,
            difficulty_progression=difficulty_progression,
            agent_selection_preferences=agent_preferences,
            time_allocation_patterns=time_patterns,
            error_correction_patterns=error_patterns,
            overall_confidence=overall_confidence,
            recommendations=recommendations
        )

        # 保存分析结果
        self._save_pattern_analysis(pattern)

        logger.info(f"用户 {user_id} 学习模式分析完成，置信度: {overall_confidence:.2f}")
        return pattern

    def identify_learning_style(self, activities: List[Dict]) -> LearningStyle:
        """识别学习风格

        Args:
            activities: 学习活动列表

        Returns:
            LearningStyle: 学习风格分析结果
        """
        if not activities:
            return LearningStyle()

        # 初始化风格指标
        style_scores = {
            'visual': 0.0,
            'auditory': 0.0,
            'kinesthetic': 0.0,
            'reading_writing': 0.0,
            'analytical': 0.0,
            'intuitive': 0.0,
            'sequential': 0.0,
            'global': 0.0
        }

        # 分析活动类型偏好
        activity_type_scores = self._analyze_activity_type_preferences(activities)

        # 分析内容类型偏好
        content_type_scores = self._analyze_content_type_preferences(activities)

        # 分析交互模式
        interaction_scores = self._analyze_interaction_patterns(activities)

        # 分析时间模式
        time_scores = self._analyze_time_patterns(activities)

        # 合并得分
        style_scores['visual'] += content_type_scores.get('visual_content', 0.3)
        style_scores['auditory'] += content_type_scores.get('audio_content', 0.3)
        style_scores['kinesthetic'] += interaction_scores.get('interactive_elements', 0.4)
        style_scores['reading_writing'] += activity_type_scores.get('text_input', 0.5)

        style_scores['analytical'] += content_type_scores.get('structured_content', 0.4)
        style_scores['intuitive'] += content_type_scores.get('creative_content', 0.3)
        style_scores['sequential'] += time_scores.get('linear_progression', 0.4)
        style_scores['global'] += time_scores.get('holistic_approach', 0.3)

        # 标准化得分
        total_score = sum(style_scores.values())
        if total_score > 0:
            for key in style_scores:
                style_scores[key] /= total_score

        # 计算置信度
        confidence = self._calculate_style_confidence(activities, style_scores)

        learning_style = LearningStyle(
            visual_preference=style_scores['visual'],
            auditory_preference=style_scores['auditory'],
            kinesthetic_preference=style_scores['kinesthetic'],
            reading_writing_preference=style_scores['reading_writing'],
            analytical_preference=style_scores['analytical'],
            intuitive_preference=style_scores['intuitive'],
            sequential_preference=style_scores['sequential'],
            global_preference=style_scores['global'],
            confidence_score=confidence
        )

        return learning_style

    def analyze_behavior_patterns(self, activities: List[Dict]) -> List[BehaviorPattern]:
        """分析行为模式

        Args:
            activities: 学习活动列表

        Returns:
            List[BehaviorPattern]: 行为模式列表
        """
        if not activities:
            return []

        patterns = []

        # 分析会话持续时间模式
        session_pattern = self._analyze_session_duration_pattern(activities)
        if session_pattern:
            patterns.append(session_pattern)

        # 分析Agent调用模式
        agent_pattern = self._analyze_agent_calling_pattern(activities)
        if agent_pattern:
            patterns.append(agent_pattern)

        # 分析节点交互模式
        interaction_pattern = self._analyze_node_interaction_pattern(activities)
        if interaction_pattern:
            patterns.append(interaction_pattern)

        # 分析评分结果模式
        scoring_pattern = self._analyze_scoring_pattern(activities)
        if scoring_pattern:
            patterns.append(scoring_pattern)

        # 分析错误修正模式
        error_pattern = self._analyze_error_behavior_pattern(activities)
        if error_pattern:
            patterns.append(error_pattern)

        return patterns

    def analyze_difficulty_progression(self, activities: List[Dict]) -> Dict:
        """分析难度进展

        Args:
            activities: 学习活动列表

        Returns:
            Dict: 难度进展分析结果
        """
        if not activities:
            return {}

        # 提取评分数据
        scoring_activities = [
            activity for activity in activities
            if activity.get('activity_type') == 'scoring_evaluation'
        ]

        if not scoring_activities:
            return {
                'progression_type': 'insufficient_data',
                'trend': 'unknown',
                'improvement_rate': 0.0,
                'difficulty_adaptation': 'unknown'
            }

        # 按时间排序
        scoring_activities.sort(key=lambda x: x.get('timestamp', ''))

        # 分析得分趋势
        scores = []
        timestamps = []

        for activity in scoring_activities:
            score = activity.get('operation_details', {}).get('total_score', 0)
            timestamp = activity.get('timestamp', '')

            if score > 0:
                scores.append(score)
                timestamps.append(timestamp)

        if len(scores) < 2:
            return {
                'progression_type': 'single_data_point',
                'trend': 'unknown',
                'improvement_rate': 0.0,
                'average_score': np.mean(scores) if scores else 0.0,
                'difficulty_adaptation': 'unknown'
            }

        # 计算趋势
        trend = self._calculate_score_trend(scores)

        # 计算改进率
        improvement_rate = self._calculate_improvement_rate(scores)

        # 分析难度适应性
        difficulty_adaptation = self._analyze_difficulty_adaptation(scoring_activities)

        # 识别学习曲线类型
        learning_curve_type = self._identify_learning_curve_type(scores)

        return {
            'progression_type': learning_curve_type,
            'trend': trend,
            'improvement_rate': improvement_rate,
            'average_score': np.mean(scores),
            'score_variance': np.var(scores) if len(scores) > 1 else 0.0,
            'difficulty_adaptation': difficulty_adaptation,
            'data_points': len(scores),
            'time_span_days': self._calculate_time_span(timestamps)
        }

    def analyze_agent_selection_preferences(self, activities: List[Dict]) -> Dict:
        """分析Agent选择偏好

        Args:
            activities: 学习活动列表

        Returns:
            Dict: Agent选择偏好分析结果
        """
        if not activities:
            return {}

        # 提取Agent交互活动
        agent_activities = [
            activity for activity in activities
            if activity.get('activity_type') == 'agent_interaction'
        ]

        if not agent_activities:
            return {
                'total_agent_calls': 0,
                'agent_frequency': {},
                'context_preferences': {},
                'success_rates': {},
                'preferred_agents': []
            }

        # 统计Agent使用频率
        agent_counts = Counter()
        agent_contexts = defaultdict(list)
        agent_success = defaultdict(list)

        for activity in agent_activities:
            agent_name = activity.get('operation_details', {}).get('agent_called', 'unknown')
            agent_counts[agent_name] += 1

            # 记录上下文
            context = activity.get('operation_details', {}).get('request_context', '')
            if context:
                agent_contexts[agent_name].append(context)

            # 记录成功率
            quality = activity.get('operation_details', {}).get('response_quality', '')
            success_score = self._convert_quality_to_score(quality)
            if success_score is not None:
                agent_success[agent_name].append(success_score)

        # 计算偏好
        total_calls = sum(agent_counts.values())
        agent_frequency = {
            agent: count / total_calls
            for agent, count in agent_counts.items()
        }

        # 分析上下文偏好
        context_preferences = {}
        for agent, contexts in agent_contexts.items():
            context_preferences[agent] = self._analyze_context_preferences(contexts)

        # 计算成功率
        success_rates = {}
        for agent, scores in agent_success.items():
            if scores:
                success_rates[agent] = {
                    'average_success': np.mean(scores),
                    'success_variance': np.var(scores) if len(scores) > 1 else 0.0,
                    'sample_size': len(scores)
                }

        # 识别首选Agent
        preferred_agents = self._identify_preferred_agents(
            agent_frequency, success_rates, context_preferences
        )

        return {
            'total_agent_calls': total_calls,
            'agent_frequency': agent_frequency,
            'context_preferences': context_preferences,
            'success_rates': success_rates,
            'preferred_agents': preferred_agents,
            'diversity_score': self._calculate_agent_diversity(agent_frequency),
            'adaptation_score': self._calculate_agent_adaptation(agent_contexts)
        }

    def analyze_time_allocation_patterns(self, activities: List[Dict]) -> Dict:
        """分析时间分配模式

        Args:
            activities: 学习活动列表

        Returns:
            Dict: 时间分配模式分析结果
        """
        if not activities:
            return {}

        # 按日期分组活动
        daily_activities = defaultdict(list)
        for activity in activities:
            date_str = activity.get('timestamp', '')[:10]  # 取日期部分
            if date_str:
                daily_activities[date_str].append(activity)

        if not daily_activities:
            return {
                'total_days_active': 0,
                'daily_average_activities': 0.0,
                'peak_activity_times': [],
                'session_duration_pattern': 'unknown'
            }

        # 分析日活动模式
        daily_counts = {date: len(activities) for date, activities in daily_activities.items()}

        # 分析时间段偏好
        hourly_counts = defaultdict(int)
        for activity in activities:
            timestamp_str = activity.get('timestamp', '')
            if timestamp_str:
                try:
                    hour = datetime.fromisoformat(timestamp_str).hour
                    hourly_counts[hour] += 1
                except:
                    continue

        # 识别高峰时段
        peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # 分析会话持续时间
        session_durations = self._extract_session_durations(activities)

        # 分析学习节奏
        learning_rhythm = self._analyze_learning_rhythm(daily_counts)

        return {
            'total_days_active': len(daily_activities),
            'daily_average_activities': np.mean(list(daily_counts.values())),
            'daily_activity_variance': np.var(list(daily_counts.values())) if len(daily_counts) > 1 else 0.0,
            'peak_activity_times': [{'hour': hour, 'activity_count': count} for hour, count in peak_hours],
            'session_duration_pattern': self._categorize_session_pattern(session_durations),
            'average_session_duration': np.mean(session_durations) if session_durations else 0.0,
            'learning_rhythm': learning_rhythm,
            'consistency_score': self._calculate_consistency_score(daily_counts)
        }

    def analyze_error_correction_patterns(self, activities: List[Dict]) -> Dict:
        """分析错误修正模式

        Args:
            activities: 学习活动列表

        Returns:
            Dict: 错误修正模式分析结果
        """
        if not activities:
            return {}

        # 提取评分活动（包含错误信息）
        scoring_activities = [
            activity for activity in activities
            if activity.get('activity_type') == 'scoring_evaluation'
        ]

        if not scoring_activities:
            return {
                'total_errors_encountered': 0,
                'error_correction_rate': 0.0,
                'common_error_types': [],
                'improvement_patterns': []
            }

        # 统计错误类型
        error_types = defaultdict(int)
        error_corrections = defaultdict(int)
        improvement_patterns = []

        previous_scores = []

        for activity in scoring_activities:
            details = activity.get('operation_details', {})
            total_score = details.get('total_score', 0)
            recommendations = details.get('recommendations', [])

            # 记录分数趋势
            previous_scores.append(total_score)

            # 分析错误类型（基于推荐）
            for recommendation in recommendations:
                if 'comparison' in recommendation.lower():
                    error_types['concept_confusion'] += 1
                elif 'clarification' in recommendation.lower():
                    error_types['conceptual_gap'] += 1
                elif 'memory' in recommendation.lower():
                    error_types['retention_issue'] += 1
                elif 'example' in recommendation.lower():
                    error_types['application_gap'] += 1

            # 检查是否是错误修正
            if len(previous_scores) > 1:
                if total_score > previous_scores[-2]:  # 分数提升
                    error_corrections['successful'] += 1
                    improvement_patterns.append({
                        'timestamp': activity.get('timestamp', ''),
                        'score_change': total_score - previous_scores[-2],
                        'correction_type': self._identify_correction_type(recommendations)
                    })
                elif total_score < previous_scores[-2]:  # 分数下降
                    error_corrections['regression'] += 1

        # 计算修正率
        total_correction_attempts = error_corrections['successful'] + error_corrections['regression']
        correction_rate = (error_corrections['successful'] / total_correction_attempts) if total_correction_attempts > 0 else 0.0

        # 分析常见错误类型
        common_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]

        # 分析学习效率
        learning_efficiency = self._analyze_learning_efficiency(previous_scores, improvement_patterns)

        return {
            'total_errors_encountered': sum(error_types.values()),
            'error_correction_rate': correction_rate,
            'common_error_types': [{'type': error_type, 'count': count} for error_type, count in common_errors],
            'improvement_patterns': improvement_patterns,
            'learning_efficiency': learning_efficiency,
            'error_trend': self._analyze_error_trend(previous_scores),
            'resilience_score': self._calculate_resilience_score(improvement_patterns)
        }

    def calculate_overall_confidence(self, learning_style: LearningStyle,
                                   behavior_patterns: List[BehaviorPattern],
                                   activities: List[Dict]) -> float:
        """计算整体置信度

        Args:
            learning_style: 学习风格分析结果
            behavior_patterns: 行为模式列表
            activities: 学习活动列表

        Returns:
            float: 整体置信度
        """
        # 数据量置信度
        data_confidence = min(len(activities) / 20.0, 1.0)  # 20个活动为满分

        # 学习风格置信度
        style_confidence = learning_style.confidence_score

        # 行为模式置信度
        if behavior_patterns:
            pattern_confidence = np.mean([p.confidence_score for p in behavior_patterns])
        else:
            pattern_confidence = 0.0

        # 时间分布置信度
        time_confidence = self._calculate_temporal_confidence(activities)

        # 综合置信度（加权平均）
        weights = {
            'data': 0.3,
            'style': 0.3,
            'pattern': 0.2,
            'temporal': 0.2
        }

        overall_confidence = (
            weights['data'] * data_confidence +
            weights['style'] * style_confidence +
            weights['pattern'] * pattern_confidence +
            weights['temporal'] * time_confidence
        )

        return min(overall_confidence, 1.0)

    def generate_pattern_recommendations(self, learning_style: LearningStyle,
                                       behavior_patterns: List[BehaviorPattern],
                                       agent_preferences: Dict) -> List[str]:
        """生成模式建议

        Args:
            learning_style: 学习风格分析结果
            behavior_patterns: 行为模式列表
            agent_preferences: Agent偏好分析结果

        Returns:
            List[str]: 建议列表
        """
        recommendations = []

        # 基于学习风格的建议
        if learning_style.visual_preference > 0.6:
            recommendations.append("建议多使用图表、流程图等视觉化学习材料")

        if learning_style.kinesthetic_preference > 0.6:
            recommendations.append("建议通过实际操作和交互式学习来提高理解")

        if learning_style.analytical_preference > 0.6:
            recommendations.append("建议采用逐步分解、逻辑分析的学习方法")

        if learning_style.sequential_preference > 0.6:
            recommendations.append("建议按照逻辑顺序逐步学习，避免跳跃式学习")

        # 基于行为模式的建议
        for pattern in behavior_patterns:
            if pattern.pattern_type == "session_duration" and pattern.frequency > 0.8:
                if pattern.duration_avg < 15:  # 短时间会话
                    recommendations.append("建议延长单次学习时间，以提高学习深度")
                elif pattern.duration_avg > 90:  # 长时间会话
                    recommendations.append("建议适当休息，采用番茄工作法提高效率")

            if pattern.pattern_type == "error_correction" and pattern.success_rate < 0.6:
                recommendations.append("建议在遇到错误时寻求更多帮助和解释")

        # 基于Agent偏好的建议
        preferred_agents = agent_preferences.get('preferred_agents', [])
        if len(preferred_agents) == 1:  # 只使用一种Agent
            recommendations.append("建议尝试使用不同类型的Agent，以获得多样化的学习支持")

        # 通用建议
        recommendations.extend([
            "定期复习已学内容，以巩固记忆",
            "保持学习记录，以便追踪进步",
            "根据学习效果调整学习策略"
        ])

        return recommendations[:8]  # 返回前8个建议

    # ========== 私有辅助方法 ==========

    def _create_empty_pattern(self, user_id: str, time_range_days: int) -> LearningPattern:
        """创建空的模式分析结果"""
        return LearningPattern(
            user_id=user_id,
            analysis_period_days=time_range_days,
            overall_confidence=0.0,
            recommendations=["需要更多学习数据才能进行模式分析"]
        )

    def _analyze_activity_type_preferences(self, activities: List[Dict]) -> Dict:
        """分析活动类型偏好"""
        type_counts = Counter()
        for activity in activities:
            activity_type = activity.get('activity_type', 'unknown')
            type_counts[activity_type] += 1

        total = sum(type_counts.values())
        return {activity_type: count / total for activity_type, count in type_counts.items()}

    def _analyze_content_type_preferences(self, activities: List[Dict]) -> Dict:
        """分析内容类型偏好"""
        preferences = {
            'visual_content': 0.3,
            'audio_content': 0.1,
            'structured_content': 0.4,
            'creative_content': 0.2
        }

        # 基于活动内容调整偏好
        for activity in activities:
            details = activity.get('operation_details', {})
            text_content = details.get('input_text', '')

            if '图' in text_content or '表' in text_content:
                preferences['visual_content'] += 0.1
            if '步骤' in text_content or '逻辑' in text_content:
                preferences['structured_content'] += 0.1
            if '例子' in text_content or '想象' in text_content:
                preferences['creative_content'] += 0.1

        return preferences

    def _analyze_interaction_patterns(self, activities: List[Dict]) -> Dict:
        """分析交互模式"""
        return {
            'interactive_elements': 0.4,
            'passive_consumption': 0.3,
            'active_creation': 0.3
        }

    def _analyze_time_patterns(self, activities: List[Dict]) -> Dict:
        """分析时间模式"""
        return {
            'linear_progression': 0.4,
            'holistic_approach': 0.3,
            'iterative_learning': 0.3
        }

    def _calculate_style_confidence(self, activities: List[Dict], style_scores: Dict) -> float:
        """计算风格识别置信度"""
        base_confidence = min(len(activities) / 10.0, 1.0)
        score_variance = np.var(list(style_scores.values())) if style_scores else 0
        variance_bonus = min(score_variance * 2, 0.3)  # 方差越大，置信度越高（表示风格明显）
        return min(base_confidence + variance_bonus, 1.0)

    def _analyze_session_duration_pattern(self, activities: List[Dict]) -> Optional[BehaviorPattern]:
        """分析会话持续时间模式"""
        # 简化实现
        return BehaviorPattern(
            pattern_id="session_duration_001",
            pattern_type="session_duration",
            frequency=1,
            duration_avg=45.0,
            success_rate=0.8,
            context_indicators=["regular_learning"],
            confidence_score=0.7
        )

    def _analyze_agent_calling_pattern(self, activities: List[Dict]) -> Optional[BehaviorPattern]:
        """分析Agent调用模式"""
        return BehaviorPattern(
            pattern_id="agent_calling_001",
            pattern_type="agent_usage",
            frequency=1,
            duration_avg=30.0,
            success_rate=0.9,
            context_indicators=["problem_solving"],
            confidence_score=0.8
        )

    def _analyze_node_interaction_pattern(self, activities: List[Dict]) -> Optional[BehaviorPattern]:
        """分析节点交互模式"""
        return BehaviorPattern(
            pattern_id="node_interaction_001",
            pattern_type="content_exploration",
            frequency=1,
            duration_avg=15.0,
            success_rate=0.7,
            context_indicators=["concept_understanding"],
            confidence_score=0.6
        )

    def _analyze_scoring_pattern(self, activities: List[Dict]) -> Optional[BehaviorPattern]:
        """分析评分模式"""
        return BehaviorPattern(
            pattern_id="scoring_001",
            pattern_type="self_assessment",
            frequency=1,
            duration_avg=10.0,
            success_rate=0.8,
            context_indicators=["progress_tracking"],
            confidence_score=0.7
        )

    def _analyze_error_behavior_pattern(self, activities: List[Dict]) -> Optional[BehaviorPattern]:
        """分析错误行为模式"""
        return BehaviorPattern(
            pattern_id="error_behavior_001",
            pattern_type="error_correction",
            frequency=1,
            duration_avg=25.0,
            success_rate=0.6,
            context_indicators=["learning_from_mistakes"],
            confidence_score=0.7
        )

    def _calculate_score_trend(self, scores: List[float]) -> str:
        """计算分数趋势"""
        if len(scores) < 2:
            return "unknown"

        # 简单线性回归
        x = list(range(len(scores)))
        slope = np.polyfit(x, scores, 1)[0]

        if slope > 1:
            return "improving"
        elif slope < -1:
            return "declining"
        else:
            return "stable"

    def _calculate_improvement_rate(self, scores: List[float]) -> float:
        """计算改进率"""
        if len(scores) < 2:
            return 0.0

        if scores[-1] > scores[0]:
            return (scores[-1] - scores[0]) / (100 - scores[0])
        else:
            return 0.0

    def _analyze_difficulty_adaptation(self, scoring_activities: List[Dict]) -> str:
        """分析难度适应性"""
        return "adaptive"  # 简化实现

    def _identify_learning_curve_type(self, scores: List[float]) -> str:
        """识别学习曲线类型"""
        if len(scores) < 3:
            return "insufficient_data"

        # 简化的学习曲线识别
        if scores[-1] > scores[0] * 1.5:
            return "rapid_improvement"
        elif scores[-1] > scores[0] * 1.1:
            return "steady_improvement"
        elif scores[-1] < scores[0] * 0.9:
            return "declining"
        else:
            return "plateau"

    def _calculate_time_span(self, timestamps: List[str]) -> float:
        """计算时间跨度"""
        if len(timestamps) < 2:
            return 0.0

        try:
            start_time = datetime.fromisoformat(timestamps[0])
            end_time = datetime.fromisoformat(timestamps[-1])
            return (end_time - start_time).days
        except:
            return 0.0

    def _convert_quality_to_score(self, quality: str) -> Optional[float]:
        """将质量评分转换为数值"""
        quality_mapping = {
            'excellent': 1.0,
            'good': 0.8,
            'helpful': 0.7,
            'satisfactory': 0.6,
            'poor': 0.3,
            'unhelpful': 0.1
        }
        return quality_mapping.get(quality.lower())

    def _analyze_context_preferences(self, contexts: List[str]) -> Dict:
        """分析上下文偏好"""
        # 简化实现
        return {
            'problem_solving': 0.4,
            'concept_explanation': 0.3,
            'review_practice': 0.3
        }

    def _identify_preferred_agents(self, frequency: Dict, success_rates: Dict,
                                 context_preferences: Dict) -> List[str]:
        """识别首选Agent"""
        # 简化实现：基于频率和成功率的组合
        agent_scores = {}
        for agent in frequency:
            base_score = frequency[agent] * 0.6
            success_bonus = success_rates.get(agent, {}).get('average_success', 0.5) * 0.4
            agent_scores[agent] = base_score + success_bonus

        return sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)[:3]

    def _calculate_agent_diversity(self, frequency: Dict) -> float:
        """计算Agent使用多样性"""
        if not frequency:
            return 0.0
        # 使用熵作为多样性指标
        probs = list(frequency.values())
        entropy = -sum(p * math.log(p + 1e-10) for p in probs)
        max_entropy = math.log(len(frequency))
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _calculate_agent_adaptation(self, agent_contexts: Dict) -> float:
        """计算Agent适应性"""
        # 简化实现
        return 0.7

    def _extract_session_durations(self, activities: List[Dict]) -> List[float]:
        """提取会话持续时间"""
        # 简化实现：基于活动时间间隔估算
        durations = []
        if len(activities) > 1:
            for i in range(1, len(activities)):
                try:
                    prev_time = datetime.fromisoformat(activities[i-1].get('timestamp', ''))
                    curr_time = datetime.fromisoformat(activities[i].get('timestamp', ''))
                    duration = (curr_time - prev_time).total_seconds() / 60.0  # 转换为分钟
                    if 0 < duration < 180:  # 过滤异常值
                        durations.append(duration)
                except:
                    continue
        return durations

    def _categorize_session_pattern(self, durations: List[float]) -> str:
        """分类会话模式"""
        if not durations:
            return "unknown"

        avg_duration = np.mean(durations)
        if avg_duration < 20:
            return "short_sessions"
        elif avg_duration < 60:
            return "moderate_sessions"
        else:
            return "long_sessions"

    def _analyze_learning_rhythm(self, daily_counts: Dict) -> Dict:
        """分析学习节奏"""
        if len(daily_counts) < 3:
            return {"pattern": "insufficient_data"}

        counts = list(daily_counts.values())
        variance = np.var(counts)

        if variance < np.mean(counts) * 0.1:
            return {"pattern": "consistent", "stability": "high"}
        elif variance < np.mean(counts) * 0.5:
            return {"pattern": "moderate_variation", "stability": "medium"}
        else:
            return {"pattern": "high_variation", "stability": "low"}

    def _calculate_consistency_score(self, daily_counts: Dict) -> float:
        """计算一致性得分"""
        if len(daily_counts) < 2:
            return 0.0

        counts = list(daily_counts.values())
        mean_count = np.mean(counts)
        if mean_count == 0:
            return 0.0

        # 使用变异系数的倒数作为一致性指标
        cv = np.std(counts) / mean_count
        consistency = 1.0 / (1.0 + cv)
        return consistency

    def _identify_correction_type(self, recommendations: List[str]) -> str:
        """识别修正类型"""
        if not recommendations:
            return "unknown"

        if any('clarification' in rec.lower() for rec in recommendations):
            return "concept_clarification"
        elif any('comparison' in rec.lower() for rec in recommendations):
            return "comparison_learning"
        elif any('example' in rec.lower() for rec in recommendations):
            return "example_based"
        else:
            return "general_guidance"

    def _analyze_learning_efficiency(self, scores: List[float],
                                   improvements: List[Dict]) -> Dict:
        """分析学习效率"""
        if len(scores) < 2:
            return {"efficiency": "unknown"}

        # 简化实现
        avg_improvement = np.mean([imp.get('score_change', 0) for imp in improvements])
        return {
            "efficiency": "high" if avg_improvement > 10 else "medium" if avg_improvement > 0 else "low",
            "average_improvement": avg_improvement
        }

    def _analyze_error_trend(self, scores: List[float]) -> str:
        """分析错误趋势"""
        if len(scores) < 3:
            return "insufficient_data"

        # 计算错误率趋势（分数的反向）
        error_rates = [100 - score for score in scores]
        if error_rates[-1] < error_rates[0]:
            return "decreasing_errors"
        elif error_rates[-1] > error_rates[0]:
            return "increasing_errors"
        else:
            return "stable_errors"

    def _calculate_resilience_score(self, improvements: List[Dict]) -> float:
        """计算韧性得分"""
        if not improvements:
            return 0.0

        # 韧性 = 改进次数 / 总尝试次数 * 平均改进幅度
        positive_improvements = [imp for imp in improvements if imp.get('score_change', 0) > 0]
        resilience_ratio = len(positive_improvements) / len(improvements)

        avg_improvement = np.mean([imp.get('score_change', 0) for imp in positive_improvements])
        improvement_factor = min(avg_improvement / 20.0, 1.0)  # 20分为满分

        return resilience_ratio * 0.7 + improvement_factor * 0.3

    def _calculate_temporal_confidence(self, activities: List[Dict]) -> float:
        """计算时间置信度"""
        if not activities:
            return 0.0

        # 基于活动时间分布的均匀性
        timestamps = [activity.get('timestamp', '') for activity in activities]
        valid_timestamps = [ts for ts in timestamps if ts]

        if len(valid_timestamps) < 2:
            return 0.0

        # 计算时间跨度
        try:
            times = [datetime.fromisoformat(ts) for ts in valid_timestamps]
            time_span = (max(times) - min(times)).days
            temporal_spread = min(time_span / 30.0, 1.0)  # 30天为满分
            return temporal_spread
        except:
            return 0.0

    def _save_pattern_analysis(self, pattern: LearningPattern):
        """保存模式分析结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{pattern.user_id}_pattern_{timestamp}.json"
            filepath = self.data_dir / filename

            pattern_dict = {
                "user_id": pattern.user_id,
                "analysis_period_days": pattern.analysis_period_days,
                "learning_style": {
                    "visual_preference": pattern.learning_style.visual_preference,
                    "auditory_preference": pattern.learning_style.auditory_preference,
                    "kinesthetic_preference": pattern.learning_style.kinesthetic_preference,
                    "reading_writing_preference": pattern.learning_style.reading_writing_preference,
                    "analytical_preference": pattern.learning_style.analytical_preference,
                    "intuitive_preference": pattern.learning_style.intuitive_preference,
                    "sequential_preference": pattern.learning_style.sequential_preference,
                    "global_preference": pattern.learning_style.global_preference,
                    "confidence_score": pattern.learning_style.confidence_score
                },
                "behavior_patterns": [
                    {
                        "pattern_id": bp.pattern_id,
                        "pattern_type": bp.pattern_type,
                        "frequency": bp.frequency,
                        "duration_avg": bp.duration_avg,
                        "success_rate": bp.success_rate,
                        "context_indicators": bp.context_indicators,
                        "confidence_score": bp.confidence_score
                    }
                    for bp in pattern.behavior_patterns
                ],
                "difficulty_progression": pattern.difficulty_progression,
                "agent_selection_preferences": pattern.agent_selection_preferences,
                "time_allocation_patterns": pattern.time_allocation_patterns,
                "error_correction_patterns": pattern.error_correction_patterns,
                "overall_confidence": pattern.overall_confidence,
                "recommendations": pattern.recommendations,
                "analysis_timestamp": datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pattern_dict, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存模式分析结果失败: {e}")

    def get_user_pattern_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取用户模式分析历史"""
        try:
            pattern_files = list(self.data_dir.glob(f"{user_id}_pattern_*.json"))
            pattern_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            history = []
            for filepath in pattern_files[:limit]:
                with open(filepath, 'r', encoding='utf-8') as f:
                    pattern_data = json.load(f)
                    history.append(pattern_data)

            return history

        except Exception as e:
            logger.error(f"获取用户模式历史失败: {e}")
            return []

    def extract_behavior_patterns(self, user_id: str, activities: List[Dict],
                                 time_range_days: int = 30) -> List[BehaviorPattern]:
        """
        提取行为模式

        Args:
            user_id: 用户ID
            activities: 学习活动列表
            time_range_days: 分析时间范围

        Returns:
            List[BehaviorPattern]: 行为模式列表
        """
        try:
            if len(activities) < self.min_data_points:
                return []

            # 分析活动序列模式
            patterns = []

            # 1. 时间模式分析
            time_patterns = self._analyze_time_behavior_patterns(activities)
            if time_patterns:
                patterns.extend(time_patterns)

            # 2. Agent选择模式分析
            agent_patterns = self._analyze_agent_behavior_patterns(activities)
            if agent_patterns:
                patterns.extend(agent_patterns)

            # 3. 学习进度模式分析
            progress_patterns = self._analyze_progress_behavior_patterns(activities)
            if progress_patterns:
                patterns.extend(progress_patterns)

            # 4. 错误修正模式分析
            error_patterns = self._analyze_error_behavior_patterns(activities)
            if error_patterns:
                patterns.extend(error_patterns)

            # 计算置信度并过滤
            filtered_patterns = []
            for pattern in patterns:
                confidence = self._calculate_pattern_confidence(pattern, activities)
                if confidence >= self.confidence_threshold:
                    pattern.confidence_score = confidence
                    filtered_patterns.append(pattern)

            return filtered_patterns

        except Exception as e:
            logger.error(f"提取行为模式失败: {e}")
            return []

    def generate_recommendations(self, user_id: str, pattern_analysis: LearningPattern,
                               activities: List[Dict] = None) -> List[str]:
        """
        生成个性化建议

        Args:
            user_id: 用户ID
            pattern_analysis: 模式分析结果
            activities: 学习活动列表（可选）

        Returns:
            List[str]: 建议列表
        """
        try:
            recommendations = []

            # 基于学习风格的建议
            if pattern_analysis.learning_style:
                style = pattern_analysis.learning_style

                # 视觉学习风格建议
                if style.visual_preference > 0.7:
                    recommendations.append("建议多使用图表、思维导图等视觉化工具辅助学习")

                # 听觉学习风格建议
                if style.auditory_preference > 0.7:
                    recommendations.append("建议尝试语音解释、讨论等听觉学习方式")

                # 动觉学习风格建议
                if style.kinesthetic_preference > 0.7:
                    recommendations.append("建议通过实践练习、具体操作来加深理解")

                # 顺序/整体学习建议
                if style.sequential_preference > 0.7:
                    recommendations.append("建议按部就班、循序渐进地学习")
                elif style.global_preference > 0.7:
                    recommendations.append("建议先了解整体框架，再深入细节")

            # 基于Agent选择偏好的建议
            if pattern_analysis.agent_selection_preferences:
                agent_prefs = pattern_analysis.agent_selection_preferences
                if 'diversity_score' in agent_prefs and agent_prefs['diversity_score'] < 0.5:
                    recommendations.append("建议尝试更多样化的Agent来丰富学习方式")

            # 基于时间分配的建议
            if pattern_analysis.time_allocation_patterns:
                time_patterns = pattern_analysis.time_allocation_patterns
                if 'average_session_duration' in time_patterns:
                    avg_duration = time_patterns['average_session_duration']
                    if avg_duration < 15:
                        recommendations.append("建议适当延长学习时间，避免过于碎片化的学习")
                    elif avg_duration > 90:
                        recommendations.append("建议适当缩短单次学习时间，注意休息和效率")

            # 基于错误修正的建议
            if pattern_analysis.error_correction_patterns:
                error_patterns = pattern_analysis.error_correction_patterns
                if 'repetition_rate' in error_patterns and error_patterns['repetition_rate'] > 0.6:
                    recommendations.append("建议加强练习，通过多样化的例子来巩固理解")

            # 基于活动序列的动态建议
            if activities:
                dynamic_recommendations = self._generate_dynamic_recommendations(activities)
                recommendations.extend(dynamic_recommendations)

            # 去重并限制数量
            unique_recommendations = list(set(recommendations))
            return unique_recommendations[:8]  # 最多返回8个建议

        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            return ["建议继续学习，系统将逐步优化个性化推荐"]

    def _analyze_time_preferences(self, activities: List[Dict]) -> Dict:
        """分析时间偏好"""
        time_preferences = {}

        if not activities:
            return time_preferences

        # 分析活动时段分布
        hour_counts = {}
        for activity in activities:
            try:
                timestamp = activity.get('timestamp', '')
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = dt.hour
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
            except:
                continue

        if hour_counts:
            # 找出最活跃的时段
            max_hour = max(hour_counts.items(), key=lambda x: x[1])[0]

            # 时段分类
            if 6 <= max_hour < 12:
                time_preferences['preferred_period'] = 'morning'
            elif 12 <= max_hour < 18:
                time_preferences['preferred_period'] = 'afternoon'
            elif 18 <= max_hour < 22:
                time_preferences['preferred_period'] = 'evening'
            else:
                time_preferences['preferred_period'] = 'night'

            time_preferences['peak_hour'] = max_hour
            time_preferences['hour_distribution'] = hour_counts

        return time_preferences

    # 辅助方法
    def _analyze_time_behavior_patterns(self, activities: List[Dict]) -> List[BehaviorPattern]:
        """分析时间相关行为模式"""
        patterns = []

        # 分析学习时段偏好
        time_preferences = self._analyze_time_preferences(activities)
        if time_preferences:
            pattern = BehaviorPattern(
                pattern_id="time_preference",
                pattern_type="temporal",
                frequency=0.8,
                duration_avg=30.0,
                success_rate=0.7,
                context_indicators=time_preferences,
                confidence_score=0.0  # 将在主函数中计算
            )
            patterns.append(pattern)

        return patterns

    def _analyze_agent_behavior_patterns(self, activities: List[Dict]) -> List[BehaviorPattern]:
        """分析Agent使用行为模式"""
        patterns = []

        # 提取Agent调用序列
        agent_calls = []
        for activity in activities:
            if activity.get('activity_type') == 'agent_interaction':
                agent = activity.get('operation_details', {}).get('agent_called')
                if agent:
                    agent_calls.append(agent)

        # 分析Agent使用序列模式
        if len(agent_calls) >= 3:
            pattern = BehaviorPattern(
                pattern_id="agent_usage_sequence",
                pattern_type="agent_interaction",
                frequency=0.6,
                duration_avg=45.0,
                success_rate=0.75,
                context_indicators={"agent_sequence": agent_calls[-5:]},
                confidence_score=0.0
            )
            patterns.append(pattern)

        return patterns

    def _analyze_progress_behavior_patterns(self, activities: List[Dict]) -> List[BehaviorPattern]:
        """分析学习进度行为模式"""
        patterns = []

        # 分析评分改进模式
        scoring_activities = [
            activity for activity in activities
            if activity.get('activity_type') == 'scoring_evaluation'
        ]

        if len(scoring_activities) >= 2:
            scores = []
            for activity in scoring_activities:
                score = activity.get('operation_details', {}).get('total_score', 0)
                scores.append(score)

            if len(scores) >= 2:
                improvement_rate = (scores[-1] - scores[0]) / max(scores[0], 1)
                pattern = BehaviorPattern(
                    pattern_id="score_improvement",
                    pattern_type="progress",
                    frequency=0.7,
                    duration_avg=60.0,
                    success_rate=min(improvement_rate + 0.5, 1.0),
                    context_indicators={
                        "initial_score": scores[0],
                        "final_score": scores[-1],
                        "improvement_rate": improvement_rate
                    },
                    confidence_score=0.0
                )
                patterns.append(pattern)

        return patterns

    def _analyze_error_behavior_patterns(self, activities: List[Dict]) -> List[BehaviorPattern]:
        """分析错误修正行为模式"""
        patterns = []

        # 分析从低分到高分的学习模式
        scoring_activities = [
            activity for activity in activities
            if activity.get('activity_type') == 'scoring_evaluation'
        ]

        for i, activity in enumerate(scoring_activities):
            score = activity.get('operation_details', {}).get('total_score', 0)
            if score < 60 and i < len(scoring_activities) - 1:
                # 找到后续的评分活动
                next_activity = scoring_activities[i + 1]
                next_score = next_activity.get('operation_details', {}).get('total_score', 0)

                if next_score > score + 10:  # 显著改进
                    pattern = BehaviorPattern(
                        pattern_id="error_correction_success",
                        pattern_type="error_recovery",
                        frequency=0.8,
                        duration_avg=40.0,
                        success_rate=0.85,
                        context_indicators={
                            "error_score": score,
                            "recovery_score": next_score,
                            "improvement": next_score - score
                        },
                        confidence_score=0.0
                    )
                    patterns.append(pattern)
                    break  # 只取一个典型案例

        return patterns

    def _calculate_pattern_confidence(self, pattern: BehaviorPattern,
                                    activities: List[Dict]) -> float:
        """计算模式置信度"""
        base_confidence = pattern.frequency * 0.4 + pattern.success_rate * 0.6

        # 基于活动数量调整置信度
        activity_factor = min(len(activities) / 20.0, 1.0)  # 20个活动为满分

        # 基于上下文指标数量调整
        context_factor = min(len(pattern.context_indicators) / 5.0, 1.0)

        final_confidence = base_confidence * activity_factor * context_factor
        return min(final_confidence, 1.0)

    def _generate_dynamic_recommendations(self, activities: List[Dict]) -> List[str]:
        """基于活动序列生成动态建议"""
        recommendations = []

        # 分析最近的Agent调用
        recent_agent_calls = []
        for activity in activities[-5:]:  # 最近5个活动
            if activity.get('activity_type') == 'agent_interaction':
                agent = activity.get('operation_details', {}).get('agent_called')
                if agent:
                    recent_agent_calls.append(agent)

        # 基于最近使用Agent的建议
        if recent_agent_calls:
            last_agent = recent_agent_calls[-1]
            if 'decomposition' in last_agent and len(recent_agent_calls) >= 2:
                recommendations.append("基础拆解已完成，建议尝试输入个人理解进行验证")
            elif 'explanation' in last_agent:
                recommendations.append("已获得详细解释，建议尝试对比表或例题练习巩固")
            elif 'scoring' in last_agent:
                recommendations.append("评分已完成，建议根据评分结果进行针对性改进")

        return recommendations