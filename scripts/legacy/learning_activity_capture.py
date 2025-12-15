"""
实时Canvas学习活动捕获系统

本模块实现Canvas学习过程中所有用户活动的实时捕获和记录，包括：
- 节点交互行为
- 文本输入行为
- Agent调用记录
- 评分结果记录
- 学习会话总结

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-25
"""

import asyncio
import json
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import yaml


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
class LearningActivity:
    """学习活动数据模型"""
    activity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    activity_type: str = ""
    user_id: str = ""
    canvas_path: str = ""
    operation_details: Dict[str, Any] = field(default_factory=dict)
    user_behavior: Dict[str, Any] = field(default_factory=dict)
    cognitive_indicators: Dict[str, Any] = field(default_factory=dict)
    session_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContext:
    """学习会话上下文"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    canvas_path: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    activities: List[LearningActivity] = field(default_factory=list)
    session_metadata: Dict[str, Any] = field(default_factory=dict)


class LearningActivityCapture:
    """学习活动实时捕获器"""

    def __init__(self, config_path: str = "config/realtime_memory.yaml"):
        """初始化学习活动捕获器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.active_sessions: Dict[str, SessionContext] = {}
        self.activity_buffer: List[LearningActivity] = []
        self.is_capturing = False
        self.capture_thread = None
        self.flush_thread = None
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # 创建数据存储目录
        self.data_dir = Path("data/realtime_memory/learning_activities")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("LearningActivityCapture initialized with config: {}", config_path)

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
                # 提取realtime_memory部分（如果存在）
                if 'realtime_memory' in full_config:
                    return full_config['realtime_memory']
                return full_config
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'capture': {
                'enabled': True,
                'capture_frequency_ms': 100,
                'buffer_size_activities': 1000,
                'auto_flush_interval_seconds': 30,
                'capture_scope': {
                    'node_interactions': True,
                    'text_inputs': True,
                    'agent_calls': True,
                    'scoring_results': True,
                    'canvas_navigation': True,
                    'time_spent': True
                }
            }
        }

    def start_capture(self) -> bool:
        """开始实时捕获"""
        if self.is_capturing:
            logger.warning("捕获已在运行中")
            return False

        if not self.config['capture']['enabled']:
            logger.warning("捕获功能未启用")
            return False

        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)

        self.capture_thread.start()
        self.flush_thread.start()

        logger.info("学习活动实时捕获已启动")
        return True

    def stop_capture(self) -> bool:
        """停止实时捕获"""
        if not self.is_capturing:
            logger.warning("捕获未在运行")
            return False

        self.is_capturing = False

        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        if self.flush_thread and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=5)

        # 最后刷新一次
        self._flush_activities()

        logger.info("学习活动实时捕获已停止")
        return True

    def start_memory_session(self, user_id: str, canvas_path: str) -> str:
        """开始记忆会话

        Args:
            user_id: 用户ID
            canvas_path: Canvas文件路径

        Returns:
            str: 会话ID
        """
        session_id = str(uuid.uuid4())
        session = SessionContext(
            session_id=session_id,
            user_id=user_id,
            canvas_path=canvas_path
        )

        self.active_sessions[session_id] = session

        # 记录会话开始活动
        self._capture_activity(
            activity_type="session_start",
            user_id=user_id,
            canvas_path=canvas_path,
            operation_details={
                "session_id": session_id,
                "session_start_time": session.start_time.isoformat()
            },
            session_context={"session_id": session_id}
        )

        logger.info(f"记忆会话已开始: {session_id} for user {user_id}")
        return session_id

    def end_memory_session(self, session_id: str) -> bool:
        """结束记忆会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功结束
        """
        if session_id not in self.active_sessions:
            logger.warning(f"会话不存在: {session_id}")
            return False

        session = self.active_sessions[session_id]
        end_time = datetime.now()
        duration = (end_time - session.start_time).total_seconds()

        # 记录会话结束活动
        self._capture_activity(
            activity_type="session_end",
            user_id=session.user_id,
            canvas_path=session.canvas_path,
            operation_details={
                "session_id": session_id,
                "session_end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_activities": len(session.activities)
            },
            session_context={"session_id": session_id}
        )

        # 保存会话数据
        self._save_session_data(session)

        # 移除活动会话
        del self.active_sessions[session_id]

        logger.info(f"记忆会话已结束: {session_id}, 持续 {duration:.1f} 秒")
        return True

    def capture_node_interaction(self, user_id: str, canvas_path: str,
                               node_id: str, interaction_type: str,
                               details: Dict) -> str:
        """捕获节点交互

        Args:
            user_id: 用户ID
            canvas_path: Canvas文件路径
            node_id: 节点ID
            interaction_type: 交互类型
            details: 交互详情

        Returns:
            str: 活动ID
        """
        if not self._is_capture_enabled('node_interactions'):
            return ""

        activity_id = self._capture_activity(
            activity_type="node_interaction",
            user_id=user_id,
            canvas_path=canvas_path,
            operation_details={
                "node_id": node_id,
                "interaction_type": interaction_type,
                **details
            },
            user_behavior={
                "reading_pattern": details.get("reading_pattern", "unknown"),
                "hesitation_indicators": details.get("hesitation_indicators", []),
                "comprehension_signals": details.get("comprehension_signals", [])
            }
        )

        return activity_id

    def capture_understanding_input(self, user_id: str, canvas_path: str,
                                  node_id: str, input_text: str,
                                  context: Dict) -> str:
        """捕获理解输入

        Args:
            user_id: 用户ID
            canvas_path: Canvas文件路径
            node_id: 节点ID
            input_text: 输入文本
            context: 上下文信息

        Returns:
            str: 活动ID
        """
        if not self._is_capture_enabled('text_inputs'):
            return ""

        input_start_time = context.get("input_start_time", datetime.now())
        input_duration = (datetime.now() - input_start_time).total_seconds()

        activity_id = self._capture_activity(
            activity_type="understanding_input",
            user_id=user_id,
            canvas_path=canvas_path,
            operation_details={
                "node_id": node_id,
                "input_text": input_text,
                "input_length_chars": len(input_text),
                "input_time_seconds": input_duration,
                "editing_pattern": context.get("editing_pattern", "unknown"),
                "target_yellow_node": context.get("target_yellow_node", "")
            },
            cognitive_indicators={
                "confidence_level": self._estimate_confidence(input_text, context),
                "conceptual_clarity": self._estimate_conceptual_clarity(input_text, context),
                "example_usage_ability": self._estimate_example_usage(input_text, context),
                "critical_thinking_engagement": self._estimate_critical_thinking(input_text, context)
            }
        )

        return activity_id

    def capture_agent_interaction(self, user_id: str, canvas_path: str,
                                agent_name: str, interaction_data: Dict) -> str:
        """捕获Agent交互

        Args:
            user_id: 用户ID
            canvas_path: Canvas文件路径
            agent_name: Agent名称
            interaction_data: 交互数据

        Returns:
            str: 活动ID
        """
        if not self._is_capture_enabled('agent_calls'):
            return ""

        activity_id = self._capture_activity(
            activity_type="agent_interaction",
            user_id=user_id,
            canvas_path=canvas_path,
            operation_details={
                "agent_called": agent_name,
                "request_context": interaction_data.get("request_context", ""),
                "response_quality": interaction_data.get("response_quality", ""),
                "time_spent_seconds": interaction_data.get("time_spent_seconds", 0),
                "input_data": interaction_data.get("input_data", {}),
                "output_summary": interaction_data.get("output_summary", "")
            },
            user_behavior={
                "user_satisfaction": interaction_data.get("user_satisfaction", "unknown"),
                "follow_up_actions": interaction_data.get("follow_up_actions", [])
            }
        )

        return activity_id

    def capture_scoring_result(self, user_id: str, canvas_path: str,
                              scoring_data: Dict) -> str:
        """捕获评分结果

        Args:
            user_id: 用户ID
            canvas_path: Canvas文件路径
            scoring_data: 评分数据

        Returns:
            str: 活动ID
        """
        if not self._is_capture_enabled('scoring_results'):
            return ""

        # 将 impact_analysis 合并到 operation_details 中
        operation_details = {
            "scoring_agent": "scoring-agent",
            "yellow_node_id": scoring_data.get("yellow_node_id", ""),
            "scores": scoring_data.get("scores", {}),
            "total_score": scoring_data.get("total_score", 0),
            "color_transition": scoring_data.get("color_transition", ""),
            "recommendations": scoring_data.get("recommendations", []),
            "understanding_improvement": scoring_data.get("understanding_improvement", False),
            "remaining_gaps": scoring_data.get("remaining_gaps", []),
            "next_learning_priority": scoring_data.get("next_learning_priority", "medium")
        }

        activity_id = self._capture_activity(
            activity_type="scoring_evaluation",
            user_id=user_id,
            canvas_path=canvas_path,
            operation_details=operation_details
        )

        return activity_id

    def capture_learning_session_summary(self, user_id: str, session_data: Dict) -> str:
        """捕获学习会话总结

        Args:
            user_id: 用户ID
            session_data: 会话数据

        Returns:
            str: 活动ID
        """
        activity_id = self._capture_activity(
            activity_type="session_summary",
            user_id=user_id,
            canvas_path=session_data.get("canvas_path", ""),
            operation_details={
                "session_duration_minutes": session_data.get("duration_minutes", 0),
                "total_nodes_interacted": session_data.get("total_nodes_interacted", 0),
                "agents_used": session_data.get("agents_used", []),
                "learning_objectives_met": session_data.get("learning_objectives_met", []),
                "key_insights_gained": session_data.get("key_insights_gained", [])
            },
            session_context=session_data.get("session_context", {})
        )

        return activity_id

    def _capture_activity(self, activity_type: str, user_id: str,
                         canvas_path: str, operation_details: Dict = None,
                         user_behavior: Dict = None, cognitive_indicators: Dict = None,
                         session_context: Dict = None) -> str:
        """捕获学习活动（内部方法）

        Args:
            activity_type: 活动类型
            user_id: 用户ID
            canvas_path: Canvas文件路径
            operation_details: 操作详情
            user_behavior: 用户行为
            cognitive_indicators: 认知指标
            session_context: 会话上下文

        Returns:
            str: 活动ID
        """
        activity = LearningActivity(
            activity_type=activity_type,
            user_id=user_id,
            canvas_path=canvas_path,
            operation_details=operation_details or {},
            user_behavior=user_behavior or {},
            cognitive_indicators=cognitive_indicators or {},
            session_context=session_context or {}
        )

        # 添加到缓冲区
        self.activity_buffer.append(activity)

        # 更新活动会话
        if session_context and "session_id" in session_context:
            session_id = session_context["session_id"]
            if session_id in self.active_sessions:
                self.active_sessions[session_id].activities.append(activity)

        # 检查缓冲区大小
        buffer_size = self.config['capture']['buffer_size_activities']
        if len(self.activity_buffer) >= buffer_size:
            self._flush_activities()

        return activity.activity_id

    def _is_capture_enabled(self, capture_type: str) -> bool:
        """检查特定类型的捕获是否启用"""
        return (
            self.config['capture']['enabled'] and
            self.config['capture']['capture_scope'].get(capture_type, False)
        )

    def _capture_loop(self):
        """捕获循环线程"""
        logger.info("捕获循环已启动")

        while self.is_capturing:
            try:
                # 这里可以添加定期捕获逻辑，比如检查Canvas文件变化等
                time.sleep(self.config['capture']['capture_frequency_ms'] / 1000)
            except Exception as e:
                logger.error(f"捕获循环错误: {e}")
                time.sleep(1)

        logger.info("捕获循环已结束")

    def _flush_loop(self):
        """定期刷新循环线程"""
        flush_interval = self.config['capture']['auto_flush_interval_seconds']
        logger.info(f"刷新循环已启动，间隔: {flush_interval} 秒")

        while self.is_capturing:
            try:
                time.sleep(flush_interval)
                self._flush_activities()
            except Exception as e:
                logger.error(f"刷新循环错误: {e}")

        logger.info("刷新循环已结束")

    def _flush_activities(self):
        """刷新活动缓冲区到磁盘"""
        if not self.activity_buffer:
            return

        try:
            # 按用户和日期分组保存
            activities_by_user = {}
            for activity in self.activity_buffer:
                user_date = f"{activity.user_id}_{activity.timestamp.strftime('%Y%m%d')}"
                if user_date not in activities_by_user:
                    activities_by_user[user_date] = []
                activities_by_user[user_date].append(activity)

            # 保存到文件
            for user_date, activities in activities_by_user.items():
                self._save_activities_to_file(user_date, activities)

            # 清空缓冲区
            flushed_count = len(self.activity_buffer)
            self.activity_buffer.clear()

            logger.debug(f"已刷新 {flushed_count} 个活动到磁盘")

        except Exception as e:
            logger.error(f"刷新活动失败: {e}")

    def _save_activities_to_file(self, user_date: str, activities: List[LearningActivity]):
        """保存活动到文件"""
        filename = f"{user_date}_activities.json"
        filepath = self.data_dir / filename

        try:
            # 转换为可序列化的格式
            serializable_activities = []
            for activity in activities:
                activity_dict = {
                    "activity_id": activity.activity_id,
                    "timestamp": activity.timestamp.isoformat(),
                    "activity_type": activity.activity_type,
                    "user_id": activity.user_id,
                    "canvas_path": activity.canvas_path,
                    "operation_details": activity.operation_details,
                    "user_behavior": activity.user_behavior,
                    "cognitive_indicators": activity.cognitive_indicators,
                    "session_context": activity.session_context
                }
                serializable_activities.append(activity_dict)

            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_activities, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存活动文件失败: {filepath}, 错误: {e}")

    def _save_session_data(self, session: SessionContext):
        """保存会话数据"""
        try:
            session_filename = f"{session.user_id}_{session.session_id}_session.json"
            session_filepath = self.data_dir / session_filename

            # 转换为可序列化的格式
            session_dict = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "canvas_path": session.canvas_path,
                "start_time": session.start_time.isoformat(),
                "session_metadata": session.session_metadata,
                "activities_count": len(session.activities),
                "activities": [
                    {
                        "activity_id": activity.activity_id,
                        "timestamp": activity.timestamp.isoformat(),
                        "activity_type": activity.activity_type,
                        "operation_details": activity.operation_details
                    }
                    for activity in session.activities
                ]
            }

            with open(session_filepath, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存会话数据失败: {e}")

    def _estimate_confidence(self, input_text: str, context: Dict) -> float:
        """估算用户理解置信度"""
        # 改进的启发式方法，基于文本长度调整基础置信度
        if len(input_text) < 10:
            confidence = 0.3  # 非常短的文本，低置信度
        elif len(input_text) < 50:
            confidence = 0.5  # 短文本，中等置信度
        else:
            confidence = 0.6  # 足过基础长度，较高置信度

        # 文本长度影响 (更积极的评分)
        if len(input_text) > 50:
            confidence += 0.05
        if len(input_text) > 100:
            confidence += 0.1
        if len(input_text) > 200:
            confidence += 0.1
        if len(input_text) > 300:
            confidence += 0.05

        # 编辑次数影响
        edit_count = context.get("edit_count", 0)
        if edit_count > 1:
            confidence += 0.05
        if edit_count > 3:
            confidence += 0.05
        if edit_count > 5:
            confidence += 0.05

        # 结构化表达奖励
        structure_keywords = ["首先", "其次", "然后", "最后", "因为", "所以", "例如", "比如"]
        structure_count = sum(1 for keyword in structure_keywords if keyword in input_text)
        if structure_count > 0:
            confidence += min(structure_count * 0.03, 0.1)

        # 概念完整性奖励
        concept_keywords = ["定义", "概念", "意思是", "特征", "特点", "作用", "功能"]
        if any(keyword in input_text for keyword in concept_keywords):
            confidence += 0.1

        # 使用提示词或例子（正面因素，显示主动学习）
        if "提示" in input_text or "例子" in input_text or "例如" in input_text:
            confidence += 0.05  # 改为正面奖励

        # 逻辑推理关键词
        logic_keywords = ["因此", "由此可见", "可以得出", "结论", "推理"]
        if any(keyword in input_text for keyword in logic_keywords):
            confidence += 0.1

        # 确保不超过1.0
        return min(max(confidence, 0.0), 1.0)

    def _estimate_conceptual_clarity(self, input_text: str, context: Dict) -> float:
        """估算概念清晰度"""
        clarity = 0.5

        # 包含定义
        if any(keyword in input_text for keyword in ["定义", "概念", "意思是"]):
            clarity += 0.2

        # 包含例子
        if any(keyword in input_text for keyword in ["例子", "比如", "例如"]):
            clarity += 0.2

        # 结构化表达
        if "首先" in input_text and "其次" in input_text:
            clarity += 0.1

        return min(max(clarity, 0.0), 1.0)

    def _estimate_example_usage(self, input_text: str, context: Dict) -> float:
        """估算例子使用能力"""
        ability = 0.3

        example_keywords = ["例子", "比如", "例如", "举例", "具体"]
        example_count = sum(1 for keyword in example_keywords if keyword in input_text)

        ability += min(example_count * 0.2, 0.5)

        return min(max(ability, 0.0), 1.0)

    def _estimate_critical_thinking(self, input_text: str, context: Dict) -> float:
        """估算批判性思维参与度"""
        thinking = 0.3

        # 对比分析
        if any(keyword in input_text for keyword in ["对比", "区别", "不同", "相同"]):
            thinking += 0.2

        # 原因分析
        if any(keyword in input_text for keyword in ["因为", "所以", "原因", "导致"]):
            thinking += 0.2

        # 推论
        if any(keyword in input_text for keyword in ["可以推出", "得出", "结论"]):
            thinking += 0.2

        return min(max(thinking, 0.0), 1.0)

    def get_active_sessions(self) -> List[str]:
        """获取活动会话列表"""
        return list(self.active_sessions.keys())

    def get_session_activities(self, session_id: str) -> List[LearningActivity]:
        """获取会话活动列表"""
        if session_id not in self.active_sessions:
            return []
        return self.active_sessions[session_id].activities

    def get_buffer_status(self) -> Dict:
        """获取缓冲区状态"""
        return {
            "buffer_size": len(self.activity_buffer),
            "active_sessions": len(self.active_sessions),
            "is_capturing": self.is_capturing,
            "config_enabled": self.config['capture']['enabled']
        }