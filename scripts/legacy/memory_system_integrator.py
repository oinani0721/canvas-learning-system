"""
记忆系统集成器

本模块实现记忆系统的集成，包括：
- 语义记忆系统集成
- 情景记忆系统集成
- 工作记忆快照功能
- Graphiti和MCP系统集成

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-25
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import hashlib

# 尝试导入loguru用于企业级日志记录
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = True

# 尝试导入MCP和Graphiti记忆系统
try:
    import mcp__graphiti_memory__add_memory
    import mcp__graphiti_memory__search_memories
    import mcp__graphiti_memory__add_relationship
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    logger.warning("Graphiti记忆系统不可用")


@dataclass
class SemanticMemoryEntry:
    """语义记忆条目"""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    concept: str = ""
    semantic_compression: str = ""
    key_insights: List[str] = field(default_factory=list)
    associated_emotions: List[str] = field(default_factory=list)
    retention_score: float = 0.0
    confidence_level: float = 0.0
    creation_timestamp: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    related_concepts: List[str] = field(default_factory=list)


@dataclass
class EpisodicMemoryLink:
    """情景记忆链接"""
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    episode_description: str = ""
    key_events: List[str] = field(default_factory=list)
    emotional_trajectory: List[str] = field(default_factory=list)
    learning_breakthrough_moments: List[str] = field(default_factory=list)
    context_metadata: Dict = field(default_factory=dict)
    episode_start: datetime = field(default_factory=datetime.now)
    episode_end: datetime = field(default_factory=datetime.now)
    importance_score: float = 0.0


@dataclass
class WorkingMemorySnapshot:
    """工作记忆快照"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_timestamp: datetime = field(default_factory=datetime.now)
    active_concepts: List[str] = field(default_factory=list)
    cognitive_load_level: str = ""
    attention_focus: str = ""
    working_capacity_utilization: float = 0.0
    task_context: Dict = field(default_factory=dict)
    interference_factors: List[str] = field(default_factory=list)


class MemorySystemIntegrator:
    """记忆系统集成器"""

    def __init__(self, config_path: str = "config/realtime_memory.yaml"):
        """初始化记忆系统集成器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.data_dir = Path("data/realtime_memory/personal_insights")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 记忆存储
        self.semantic_memory: Dict[str, SemanticMemoryEntry] = {}
        self.episodic_memory: Dict[str, EpisodicMemoryLink] = {}
        self.working_memory_snapshots: Dict[str, WorkingMemorySnapshot] = {}

        # 配置参数
        self.semantic_enabled = self.config.get('memory_integration', {}).get(
            'semantic_memory', {}).get('enabled', True)
        self.episodic_enabled = self.config.get('memory_integration', {}).get(
            'episodic_memory', {}).get('enabled', True)
        self.working_enabled = self.config.get('memory_integration', {}).get(
            'working_memory', {}).get('enabled', True)

        logger.info("MemorySystemIntegrator initialized")

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
            'memory_integration': {
                'semantic_memory': {
                    'enabled': True,
                    'compression_level': 'medium',
                    'association_threshold': 0.6,
                    'emotional_tagging': True
                },
                'episodic_memory': {
                    'enabled': True,
                    'episode_duration_minutes': 60,
                    'key_event_detection': True,
                    'breakthrough_moment_detection': True
                },
                'working_memory': {
                    'enabled': True,
                    'snapshot_interval_seconds': 30,
                    'cognitive_load_estimation': True,
                    'attention_tracking': True
                }
            }
        }

    def integrate_with_memory_systems(self, session_data: Dict) -> Dict:
        """集成记忆系统

        Args:
            session_data: 会话数据

        Returns:
            Dict: 记忆系统集成结果
        """
        integration_result = {
            "semantic_memory_entries": [],
            "episodic_memory_links": [],
            "working_memory_snapshots": [],
            "integration_quality_score": 0.0
        }

        try:
            # 语义记忆集成
            if self.semantic_enabled:
                semantic_entries = self._integrate_semantic_memory(session_data)
                integration_result["semantic_memory_entries"] = [
                    self._semantic_entry_to_dict(entry) for entry in semantic_entries
                ]

            # 情景记忆集成
            if self.episodic_enabled:
                episodic_links = self._integrate_episodic_memory(session_data)
                integration_result["episodic_memory_links"] = [
                    self._episodic_link_to_dict(link) for link in episodic_links
                ]

            # 工作记忆集成
            if self.working_enabled:
                working_snapshots = self._integrate_working_memory(session_data)
                integration_result["working_memory_snapshots"] = [
                    self._working_snapshot_to_dict(snapshot) for snapshot in working_snapshots
                ]

            # 计算集成质量得分
            integration_result["integration_quality_score"] = self._assess_integration_quality(
                len(integration_result["semantic_memory_entries"]),
                len(integration_result["episodic_memory_links"]),
                len(integration_result["working_memory_snapshots"])
            )

            logger.info("记忆系统集成完成")

        except Exception as e:
            logger.error(f"记忆系统集成失败: {e}")

        return integration_result

    def _integrate_semantic_memory(self, session_data: Dict) -> List[SemanticMemoryEntry]:
        """集成语义记忆系统"""
        entries = []

        try:
            activities = session_data.get('learning_activities', [])
            learning_trajectory = session_data.get('learning_trajectory_analysis', {})

            # 从学习活动中提取概念
            concepts_extracted = self._extract_concepts_from_activities(activities)

            # 为每个概念创建语义记忆条目
            for concept_data in concepts_extracted:
                concept = concept_data.get('concept', '')
                if not concept or concept in [entry.concept for entry in entries]:
                    continue

                # 生成语义压缩
                semantic_compression = self._generate_semantic_compression(
                    concept, concept_data, learning_trajectory
                )

                # 提取关键洞察
                key_insights = self._extract_key_insights(concept_data, activities)

                # 分析相关情感
                associated_emotions = self._analyze_associated_emotions(concept_data)

                # 计算保留得分
                retention_score = self._calculate_retention_score(concept_data)

                # 计算置信度
                confidence_level = self._calculate_semantic_confidence(concept_data)

                entry = SemanticMemoryEntry(
                    concept=concept,
                    semantic_compression=semantic_compression,
                    key_insights=key_insights,
                    associated_emotions=associated_emotions,
                    retention_score=retention_score,
                    confidence_level=confidence_level,
                    related_concepts=concept_data.get('related_concepts', [])
                )

                entries.append(entry)
                self.semantic_memory[entry.entry_id] = entry

                # 集成到Graphiti记忆系统（如果可用）
                if GRAPHITI_AVAILABLE:
                    self._add_to_graphiti_memory(entry)

            logger.info(f"语义记忆集成完成，创建了 {len(entries)} 个条目")

        except Exception as e:
            logger.error(f"语义记忆集成失败: {e}")

        return entries

    def _integrate_episodic_memory(self, session_data: Dict) -> List[EpisodicMemoryLink]:
        """集成情景记忆系统"""
        links = []

        try:
            session_info = {
                'session_id': session_data.get('memory_session_id', ''),
                'canvas_path': session_data.get('canvas_file_path', ''),
                'start_time': session_data.get('session_start_timestamp', ''),
                'duration': session_data.get('session_duration_minutes', 0)
            }

            activities = session_data.get('learning_activities', [])

            # 分析会话的关键事件
            key_events = self._identify_key_events(activities)

            # 分析情感轨迹
            emotional_trajectory = self._analyze_emotional_trajectory(activities)

            # 识别学习突破时刻
            breakthrough_moments = self._identify_breakthrough_moments(activities)

            if key_events or breakthrough_moments:
                episode_link = EpisodicMemoryLink(
                    episode_description=self._generate_episode_description(session_info, activities),
                    key_events=key_events,
                    emotional_trajectory=emotional_trajectory,
                    learning_breakthrough_moments=breakthrough_moments,
                    context_metadata=session_info,
                    episode_start=datetime.fromisoformat(session_info['start_time']) if session_info['start_time'] else datetime.now(),
                    episode_end=datetime.fromisoformat(session_info['start_time']) + timedelta(minutes=session_info['duration']) if session_info['start_time'] else datetime.now(),
                    importance_score=self._calculate_episode_importance(key_events, breakthrough_moments)
                )

                links.append(episode_link)
                self.episodic_memory[episode_link.episode_id] = episode_link

                # 集成到Graphiti记忆系统（如果可用）
                if GRAPHITI_AVAILABLE:
                    self._add_episode_to_graphiti(episode_link)

            logger.info(f"情景记忆集成完成，创建了 {len(links)} 个链接")

        except Exception as e:
            logger.error(f"情景记忆集成失败: {e}")

        return links

    def _integrate_working_memory(self, session_data: Dict) -> List[WorkingMemorySnapshot]:
        """集成工作记忆系统"""
        snapshots = []

        try:
            activities = session_data.get('learning_activities', [])
            session_start = datetime.fromisoformat(
                session_data.get('session_start_timestamp', datetime.now().isoformat())
            )

            # 根据活动时间戳生成工作记忆快照
            snapshot_intervals = self._calculate_snapshot_intervals(activities)

            for i, timestamp in enumerate(snapshot_intervals):
                # 获取该时间点附近的活动
                nearby_activities = self._get_nearby_activities(activities, timestamp, 5)  # 5分钟窗口

                # 分析活跃概念
                active_concepts = self._extract_active_concepts(nearby_activities)

                # 估算认知负荷
                cognitive_load = self._estimate_cognitive_load(nearby_activities)

                # 分析注意力焦点
                attention_focus = self._analyze_attention_focus(nearby_activities)

                # 计算工作记忆容量利用率
                capacity_utilization = self._calculate_capacity_utilization(
                    active_concepts, cognitive_load
                )

                # 识别干扰因素
                interference_factors = self._identify_interference_factors(nearby_activities)

                snapshot = WorkingMemorySnapshot(
                    snapshot_timestamp=timestamp,
                    active_concepts=active_concepts,
                    cognitive_load_level=cognitive_load,
                    attention_focus=attention_focus,
                    working_capacity_utilization=capacity_utilization,
                    task_context={
                        'session_progress': i / len(snapshot_intervals) if snapshot_intervals else 0,
                        'recent_activities': len(nearby_activities)
                    },
                    interference_factors=interference_factors
                )

                snapshots.append(snapshot)
                self.working_memory_snapshots[snapshot.snapshot_id] = snapshot

            logger.info(f"工作记忆集成完成，创建了 {len(snapshots)} 个快照")

        except Exception as e:
            logger.error(f"工作记忆集成失败: {e}")

        return snapshots

    def _extract_concepts_from_activities(self, activities: List[Dict]) -> List[Dict]:
        """从活动中提取概念"""
        concepts = []

        for activity in activities:
            activity_type = activity.get('activity_type', '')

            if activity_type == 'understanding_input':
                details = activity.get('operation_details', {})
                input_text = details.get('input_text', '')

                # 简单的概念提取（基于关键词和长度）
                if len(input_text) > 20:  # 只处理有意义的输入
                    concept_data = {
                        'concept': self._extract_main_concept(input_text),
                        'source_activity': activity_type,
                        'input_text': input_text,
                        'cognitive_indicators': activity.get('cognitive_indicators', {}),
                        'timestamp': activity.get('timestamp', '')
                    }
                    concepts.append(concept_data)

            elif activity_type == 'agent_interaction':
                details = activity.get('operation_details', {})
                request_context = details.get('request_context', '')

                if request_context:
                    concept_data = {
                        'concept': self._extract_concept_from_context(request_context),
                        'source_activity': activity_type,
                        'context': request_context,
                        'agent_name': details.get('agent_called', ''),
                        'timestamp': activity.get('timestamp', '')
                    }
                    concepts.append(concept_data)

        return concepts

    def _extract_main_concept(self, text: str) -> str:
        """提取主要概念"""
        # 简化实现：基于文本长度和关键词提取
        if len(text) <= 50:
            return text[:20] + "..." if len(text) > 20 else text
        else:
            # 提取前50个字符作为概念摘要
            return text[:50] + "..."

    def _extract_concept_from_context(self, context: str) -> str:
        """从上下文中提取概念"""
        # 简化实现
        return context[:30] + "..." if len(context) > 30 else context

    def _generate_semantic_compression(self, concept: str, concept_data: Dict,
                                     learning_trajectory: Dict) -> str:
        """生成语义压缩"""
        # 简化实现：基于概念和学习轨迹生成压缩描述
        source_activity = concept_data.get('source_activity', '')
        timestamp = concept_data.get('timestamp', '')

        if source_activity == 'understanding_input':
            return f"用户通过理解输入掌握了'{concept}'的概念"
        elif source_activity == 'agent_interaction':
            agent_name = concept_data.get('agent_name', '')
            return f"用户通过{agent_name}的辅助学习了'{concept}'"
        else:
            return f"用户学习了'{concept}'"

    def _extract_key_insights(self, concept_data: Dict, activities: List[Dict]) -> List[str]:
        """提取关键洞察"""
        insights = []

        concept = concept_data.get('concept', '')
        source_activity = concept_data.get('source_activity', '')

        # 基于活动类型生成洞察
        if source_activity == 'understanding_input':
            cognitive_indicators = concept_data.get('cognitive_indicators', {})
            confidence = cognitive_indicators.get('confidence_level', 0)

            if confidence > 0.8:
                insights.append(f"对'{concept}'有高度的理解和信心")
            elif confidence > 0.6:
                insights.append(f"对'{concept}'有基本的理解")
            else:
                insights.append(f"对'{concept}'的理解还需要加强")

        elif source_activity == 'agent_interaction':
            agent_name = concept_data.get('agent_name', '')
            insights.append(f"通过{agent_name}的帮助获得了'{concept}'的深入理解")

        return insights

    def _analyze_associated_emotions(self, concept_data: Dict) -> List[str]:
        """分析相关情感"""
        emotions = []

        source_activity = concept_data.get('source_activity', '')

        # 基于活动类型推断情感
        if source_activity == 'understanding_input':
            cognitive_indicators = concept_data.get('cognitive_indicators', {})
            confidence = cognitive_indicators.get('confidence_level', 0)

            if confidence > 0.8:
                emotions.append("accomplishment")
                emotions.append("confidence")
            elif confidence > 0.6:
                emotions.append("clarity")
                emotions.append("satisfaction")
            else:
                emotions.append("confusion")
                emotions.append("uncertainty")

        elif source_activity == 'agent_interaction':
            emotions.append("curiosity")
            emotions.append("engagement")

        return emotions

    def _calculate_retention_score(self, concept_data: Dict) -> float:
        """计算保留得分"""
        # 基于概念复杂度和用户参与度计算
        source_activity = concept_data.get('source_activity', '')

        base_score = 0.5

        if source_activity == 'understanding_input':
            cognitive_indicators = concept_data.get('cognitive_indicators', {})
            confidence = cognitive_indicators.get('confidence_level', 0)
            clarity = cognitive_indicators.get('conceptual_clarity', 0)

            base_score = (confidence + clarity) / 2

        elif source_activity == 'agent_interaction':
            # Agent辅助的学习通常有更好的保留
            base_score = 0.7

        return min(base_score, 1.0)

    def _calculate_semantic_confidence(self, concept_data: Dict) -> float:
        """计算语义置信度"""
        # 基于数据质量和完整性计算
        source_activity = concept_data.get('source_activity', '')

        if source_activity == 'understanding_input':
            cognitive_indicators = concept_data.get('cognitive_indicators', {})
            if cognitive_indicators:
                return 0.8
            else:
                return 0.6
        elif source_activity == 'agent_interaction':
            return 0.9
        else:
            return 0.5

    def _identify_key_events(self, activities: List[Dict]) -> List[str]:
        """识别关键事件"""
        key_events = []

        for activity in activities:
            activity_type = activity.get('activity_type', '')

            if activity_type == 'agent_interaction':
                agent_name = activity.get('operation_details', {}).get('agent_called', '')
                key_events.append(f"调用了{agent_name}进行学习辅助")

            elif activity_type == 'scoring_evaluation':
                details = activity.get('operation_details', {})
                total_score = details.get('total_score', 0)
                color_transition = details.get('color_transition', '')

                if total_score >= 80:
                    key_events.append(f"获得了高分({total_score}分)，完全理解了概念")
                elif color_transition:
                    key_events.append(f"理解水平发生了转变：{color_transition}")

            elif activity_type == 'understanding_input':
                details = activity.get('operation_details', {})
                input_length = details.get('input_length_chars', 0)

                if input_length > 200:
                    key_events.append("进行了详细的理解输入和思考")

        return key_events

    def _analyze_emotional_trajectory(self, activities: List[Dict]) -> List[str]:
        """分析情感轨迹"""
        emotions = []

        for activity in activities:
            activity_type = activity.get('activity_type', '')

            if activity_type == 'understanding_input':
                cognitive_indicators = activity.get('cognitive_indicators', {})
                confidence = cognitive_indicators.get('confidence_level', 0)

                if confidence > 0.8:
                    emotions.append("confidence")
                elif confidence > 0.6:
                    emotions.append("clarity")
                else:
                    emotions.append("confusion")

            elif activity_type == 'scoring_evaluation':
                details = activity.get('operation_details', {})
                total_score = details.get('total_score', 0)

                if total_score >= 80:
                    emotions.append("accomplishment")
                elif total_score < 60:
                    emotions.append("frustration")
                else:
                    emotions.append("determination")

        return emotions

    def _identify_breakthrough_moments(self, activities: List[Dict]) -> List[str]:
        """识别学习突破时刻"""
        breakthroughs = []

        for activity in activities:
            activity_type = activity.get('activity_type', '')

            if activity_type == 'scoring_evaluation':
                details = activity.get('operation_details', {})
                color_transition = details.get('color_transition', '')

                if color_transition in ['red_to_purple', 'purple_to_green']:
                    breakthroughs.append(f"理解水平实现突破：{color_transition}")

                impact_analysis = activity.get('impact_analysis', {})
                if impact_analysis.get('understanding_improvement'):
                    breakthroughs.append("实现了理解的显著提升")

        return breakthroughs

    def _generate_episode_description(self, session_info: Dict, activities: List[Dict]) -> str:
        """生成情景描述"""
        canvas_name = Path(session_info.get('canvas_path', '')).stem
        duration = session_info.get('duration', 0)

        # 统计活动类型
        activity_counts = {}
        for activity in activities:
            activity_type = activity.get('activity_type', '')
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1

        description_parts = [
            f"在'{canvas_name}'上进行的学习会话",
            f"持续{duration:.0f}分钟"
        ]

        if activity_counts:
            most_common = max(activity_counts.items(), key=lambda x: x[1])
            description_parts.append(f"主要活动类型：{most_common[0]}({most_common[1]}次)")

        return "，".join(description_parts)

    def _calculate_episode_importance(self, key_events: List[str],
                                    breakthrough_moments: List[str]) -> float:
        """计算情景重要性"""
        base_score = 0.3

        # 基于关键事件数量
        event_score = min(len(key_events) * 0.1, 0.4)

        # 基于突破时刻数量
        breakthrough_score = min(len(breakthrough_moments) * 0.3, 0.3)

        total_score = base_score + event_score + breakthrough_score
        return min(total_score, 1.0)

    def _calculate_snapshot_intervals(self, activities: List[Dict]) -> List[datetime]:
        """计算快照时间间隔"""
        if not activities:
            return []

        # 提取有效的时间戳
        timestamps = []
        for activity in activities:
            timestamp_str = activity.get('timestamp', '')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    timestamps.append(timestamp)
                except:
                    continue

        if not timestamps:
            return []

        # 按时间排序
        timestamps.sort()

        # 计算快照时间点（每30秒或每5个活动）
        snapshot_interval = timedelta(seconds=30)
        snapshots = []

        current_time = timestamps[0]
        end_time = timestamps[-1]

        while current_time <= end_time:
            snapshots.append(current_time)
            current_time += snapshot_interval

        return snapshots

    def _get_nearby_activities(self, activities: List[Dict], timestamp: datetime,
                             window_minutes: int) -> List[Dict]:
        """获取时间点附近的活动"""
        window = timedelta(minutes=window_minutes)
        nearby = []

        for activity in activities:
            timestamp_str = activity.get('timestamp', '')
            if timestamp_str:
                try:
                    activity_time = datetime.fromisoformat(timestamp_str)
                    if abs(activity_time - timestamp) <= window:
                        nearby.append(activity)
                except:
                    continue

        return nearby

    def _extract_active_concepts(self, activities: List[Dict]) -> List[str]:
        """提取活跃概念"""
        concepts = []

        for activity in activities:
            activity_type = activity.get('activity_type', '')

            if activity_type == 'understanding_input':
                details = activity.get('operation_details', {})
                input_text = details.get('input_text', '')
                if input_text and len(input_text) > 20:
                    concepts.append(self._extract_main_concept(input_text))

            elif activity_type == 'agent_interaction':
                details = activity.get('operation_details', {})
                context = details.get('request_context', '')
                if context:
                    concepts.append(self._extract_concept_from_context(context))

        return concepts

    def _estimate_cognitive_load(self, activities: List[Dict]) -> str:
        """估算认知负荷"""
        if not activities:
            return "low"

        # 基于活动复杂度和数量估算
        complexity_score = 0

        for activity in activities:
            activity_type = activity.get('activity_type', '')

            if activity_type == 'agent_interaction':
                complexity_score += 2
            elif activity_type == 'understanding_input':
                details = activity.get('operation_details', {})
                input_length = details.get('input_length_chars', 0)
                complexity_score += min(input_length / 100, 3)
            elif activity_type == 'scoring_evaluation':
                complexity_score += 1

        if complexity_score < 3:
            return "low"
        elif complexity_score < 8:
            return "moderate"
        else:
            return "high"

    def _analyze_attention_focus(self, activities: List[Dict]) -> str:
        """分析注意力焦点"""
        if not activities:
            return "unfocused"

        # 统计活动类型分布
        activity_types = [activity.get('activity_type', '') for activity in activities]

        if 'understanding_input' in activity_types:
            return "concept_understanding"
        elif 'agent_interaction' in activity_types:
            return "problem_solving"
        elif 'scoring_evaluation' in activity_types:
            return "self_assessment"
        else:
            return "general_exploration"

    def _calculate_capacity_utilization(self, concepts: List[str], cognitive_load: str) -> float:
        """计算工作记忆容量利用率"""
        # 基于概念数量和认知负荷估算
        concept_load = len(concepts) * 0.1

        load_mapping = {
            'low': 0.2,
            'moderate': 0.5,
            'high': 0.8
        }

        cognitive_load_score = load_mapping.get(cognitive_load, 0.3)

        total_utilization = concept_load + cognitive_load_score
        return min(total_utilization, 1.0)

    def _identify_interference_factors(self, activities: List[Dict]) -> List[str]:
        """识别干扰因素"""
        factors = []

        # 简化实现：基于活动模式识别潜在干扰
        rapid_switches = 0
        prev_type = None

        for activity in activities:
            activity_type = activity.get('activity_type', '')
            if prev_type and activity_type != prev_type:
                rapid_switches += 1
            prev_type = activity_type

        if rapid_switches > len(activities) * 0.7:
            factors.append("频繁的任务切换")

        # 可以添加更多干扰因素的识别逻辑

        return factors

    def _assess_integration_quality(self, semantic_count: int, episodic_count: int,
                                 working_count: int) -> float:
        """评估集成质量"""
        # 基于各类型记忆的数量和平衡性评估质量
        total_count = semantic_count + episodic_count + working_count

        if total_count == 0:
            return 0.0

        # 平衡性得分
        if total_count >= 3:
            expected_each = total_count / 3
            balance_score = 1.0 - (
                abs(semantic_count - expected_each) +
                abs(episodic_count - expected_each) +
                abs(working_count - expected_each)
            ) / total_count
        else:
            # 数据量少时，只要有一种类型就给基础分
            balance_score = 0.5 if total_count > 0 else 0.0

        # 数量得分（数量越多质量越高，但有上限）
        quantity_score = min(total_count / 10.0, 1.0)

        # 综合得分
        quality_score = (balance_score * 0.6 + quantity_score * 0.4)
        return min(quality_score, 1.0)

    def _semantic_entry_to_dict(self, entry: SemanticMemoryEntry) -> Dict:
        """语义记忆条目转字典"""
        return {
            "entry_id": entry.entry_id,
            "concept": entry.concept,
            "semantic_compression": entry.semantic_compression,
            "key_insights": entry.key_insights,
            "associated_emotions": entry.associated_emotions,
            "retention_score": entry.retention_score,
            "confidence_level": entry.confidence_level,
            "creation_timestamp": entry.creation_timestamp.isoformat(),
            "last_accessed": entry.last_accessed.isoformat(),
            "related_concepts": entry.related_concepts
        }

    def _episodic_link_to_dict(self, link: EpisodicMemoryLink) -> Dict:
        """情景记忆链接转字典"""
        return {
            "episode_id": link.episode_id,
            "episode_description": link.episode_description,
            "key_events": link.key_events,
            "emotional_trajectory": link.emotional_trajectory,
            "learning_breakthrough_moments": link.learning_breakthrough_moments,
            "context_metadata": link.context_metadata,
            "episode_start": link.episode_start.isoformat(),
            "episode_end": link.episode_end.isoformat(),
            "importance_score": link.importance_score
        }

    def _working_snapshot_to_dict(self, snapshot: WorkingMemorySnapshot) -> Dict:
        """工作记忆快照转字典"""
        return {
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_timestamp": snapshot.snapshot_timestamp.isoformat(),
            "active_concepts": snapshot.active_concepts,
            "cognitive_load_level": snapshot.cognitive_load_level,
            "attention_focus": snapshot.attention_focus,
            "working_capacity_utilization": snapshot.working_capacity_utilization,
            "task_context": snapshot.task_context,
            "interference_factors": snapshot.interference_factors
        }

    def _add_to_graphiti_memory(self, entry: SemanticMemoryEntry):
        """添加到Graphiti记忆系统"""
        if not GRAPHITI_AVAILABLE:
            return

        try:
            # 创建语义记忆条目
            content = f"概念: {entry.concept}\n语义压缩: {entry.semantic_compression}\n关键洞察: {', '.join(entry.key_insights)}"

            mcp__graphiti_memory__add_memory.add_memory(
                key=f"semantic_{entry.entry_id}",
                content=content,
                metadata={
                    "type": "semantic_memory",
                    "concept": entry.concept,
                    "confidence": entry.confidence_level,
                    "retention_score": entry.retention_score,
                    "emotions": entry.associated_emotions
                }
            )

        except Exception as e:
            logger.error(f"添加到Graphiti记忆失败: {e}")

    def _add_episode_to_graphiti(self, episode: EpisodicMemoryLink):
        """添加情景到Graphiti记忆系统"""
        if not GRAPHITI_AVAILABLE:
            return

        try:
            # 创建情景记忆条目
            content = f"情景: {episode.episode_description}\n关键事件: {', '.join(episode.key_events)}"

            mcp__graphiti_memory__add_memory.add_memory(
                key=f"episodic_{episode.episode_id}",
                content=content,
                metadata={
                    "type": "episodic_memory",
                    "importance": episode.importance_score,
                    "breakthrough_moments": episode.learning_breakthrough_moments,
                    "emotions": episode.emotional_trajectory
                }
            )

        except Exception as e:
            logger.error(f"添加情景到Graphiti记忆失败: {e}")

    def get_memory_statistics(self) -> Dict:
        """获取记忆统计信息"""
        return {
            "semantic_memory_count": len(self.semantic_memory),
            "episodic_memory_count": len(self.episodic_memory),
            "working_memory_snapshots_count": len(self.working_memory_snapshots),
            "graphiti_integration": GRAPHITI_AVAILABLE,
            "last_integration_time": datetime.now().isoformat()
        }

    def search_memories(self, query: str, memory_type: str = "all") -> List[Dict]:
        """搜索记忆"""
        results = []

        if memory_type in ["all", "semantic"]:
            for entry in self.semantic_memory.values():
                if query.lower() in entry.concept.lower() or query.lower() in entry.semantic_compression.lower():
                    results.append({
                        "type": "semantic",
                        "data": self._semantic_entry_to_dict(entry)
                    })

        if memory_type in ["all", "episodic"]:
            for link in self.episodic_memory.values():
                if query.lower() in link.episode_description.lower() or any(query.lower() in event.lower() for event in link.key_events):
                    results.append({
                        "type": "episodic",
                        "data": self._episodic_link_to_dict(link)
                    })

        return results