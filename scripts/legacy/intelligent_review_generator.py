"""
智能复习计划生成器 - Canvas学习系统

本模块实现智能复习计划生成的核心功能，负责：
- 基于学习历史分析和薄弱环节识别生成个性化复习计划
- 实现基于艾宾浩斯算法的复习调度优化
- 支持多种复习策略（薄弱环节导向、全面复习、针对性复习）
- 提供动态调整机制和个性化适配功能

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

# 导入相关模块
try:
    from learning_analyzer import LearningAnalyzer
    from mcp_memory_client import MCPMemoryClient
    from graphiti_integration import GraphitiKnowledgeGraph
    from ebbinghaus_review import EbbinghausReviewScheduler
except ImportError as e:
    print(f"Warning: 无法导入依赖模块 {e}，某些功能可能受限")


@dataclass
class ReviewPlanConfig:
    """复习计划配置"""
    user_id: str = "default"
    target_canvas: str = ""
    plan_type: str = "weakness_focused"  # weakness_focused, comprehensive_review, targeted_review
    difficulty_level: str = "adaptive"  # easy, medium, hard, expert, adaptive
    estimated_duration: int = 45  # 分钟
    max_concepts_per_session: int = 5
    include_explanations: bool = True
    include_examples: bool = True
    adaptive_difficulty: bool = True
    personalize_content: bool = True


@dataclass
class ReviewConcept:
    """复习概念"""
    concept_name: str
    weakness_score: float
    mastery_score: float
    difficulty: str
    urgency_level: str
    recommended_focus_areas: List[str]
    review_questions: List[Dict[str, Any]]
    supporting_materials: List[str]
    estimated_time_minutes: int
    prerequisites: List[str] = None
    related_concepts: List[str] = None


@dataclass
class ReviewSession:
    """复习会话"""
    session_id: str
    concepts: List[ReviewConcept]
    estimated_duration: int
    difficulty_level: str
    learning_objectives: List[str]
    session_type: str
    adaptive_elements: Dict[str, Any]


class IntelligentReviewGenerator:
    """智能复习计划生成器

    负责基于学习历史分析和用户需求生成个性化的复习计划。
    集成多种数据源和算法，提供科学有效的复习建议。
    """

    def __init__(
        self,
        learning_analyzer: Optional[LearningAnalyzer] = None,
        mcp_client: Optional[Any] = None,
        graphiti_client: Optional[Any] = None,
        ebbinghaus_scheduler: Optional[Any] = None
    ):
        """初始化智能复习计划生成器

        Args:
            learning_analyzer: 学习分析器实例
            mcp_client: MCP语义记忆客户端
            graphiti_client: Graphiti知识图谱客户端
            ebbinghaus_scheduler: 艾宾浩斯复习调度器
        """
        self.learning_analyzer = learning_analyzer or LearningAnalyzer(
            mcp_client=mcp_client,
            graphiti_client=graphiti_client,
            ebbinghaus_scheduler=ebbinghaus_scheduler
        )
        self.mcp_client = mcp_client
        self.graphiti_client = graphiti_client
        self.ebbinghaus_scheduler = ebbinghaus_scheduler

        # 复习策略配置
        self.REVIEW_STRATEGIES = {
            "weakness_focused": {
                "primary_goal": "address_identified_weaknesses",
                "concept_selection": "lowest_performing_first",
                "difficulty_progression": "gradual_increase",
                "feedback_frequency": "high",
                "max_concepts": 5,
                "focus_on_recent_weaknesses": True,
            },
            "comprehensive_review": {
                "primary_goal": "full_scope_review",
                "concept_selection": "curriculum_order",
                "difficulty_progression": "mixed_difficulty",
                "feedback_frequency": "moderate",
                "max_concepts": 8,
                "include_mastered_concepts": True,
            },
            "targeted_review": {
                "primary_goal": "specific_topic_mastery",
                "concept_selection": "user_selected+related",
                "difficulty_progression": "adaptive",
                "feedback_frequency": "as_needed",
                "max_concepts": 6,
                "user_driven": True,
            }
        }

        # 难度分级配置
        self.DIFFICULTY_LEVELS = {
            "easy": {
                "question_complexity": "basic",
                "time_per_concept": 8,
                "max_concepts": 8,
                "support_level": "high",
                "focus": "confidence_building",
            },
            "medium": {
                "question_complexity": "intermediate",
                "time_per_concept": 12,
                "max_concepts": 5,
                "support_level": "moderate",
                "focus": "balanced_learning",
            },
            "hard": {
                "question_complexity": "advanced",
                "time_per_concept": 15,
                "max_concepts": 3,
                "support_level": "minimal",
                "focus": "challenge_mastery",
            },
            "expert": {
                "question_complexity": "expert_level",
                "time_per_concept": 20,
                "max_concepts": 2,
                "support_level": "minimal",
                "focus": "mastery_extension",
            },
            "adaptive": {
                "question_complexity": "dynamic",
                "time_per_concept": "dynamic",
                "max_concepts": "dynamic",
                "support_level": "adaptive",
                "focus": "personalized_optimization",
            }
        }

    def generate_review_plan(
        self,
        user_id: str,
        target_canvas: str,
        plan_type: str = "weakness_focused",
        config: Optional[ReviewPlanConfig] = None
    ) -> Dict[str, Any]:
        """生成智能复习计划

        Args:
            user_id: 用户ID
            target_canvas: 目标Canvas文件
            plan_type: 计划类型 ("weakness_focused", "comprehensive_review", "targeted_review")
            config: 复习计划配置

        Returns:
            Dict: 完整的复习计划数据
        """
        if config is None:
            config = ReviewPlanConfig(
                user_id=user_id,
                target_canvas=target_canvas,
                plan_type=plan_type
            )

        try:
            # 1. 分析学习历史
            learning_analysis = self.learning_analyzer.analyze_learning_history(
                user_id=user_id,
                canvas_path=target_canvas
            )

            # 2. 提取薄弱概念
            weak_concepts = learning_analysis.get("identified_weak_concepts", [])

            # 3. 根据策略选择概念
            selected_concepts = self._select_concepts_by_strategy(
                weak_concepts, learning_analysis, config
            )

            # 4. 生成复习内容
            review_concepts = self._generate_review_concepts(selected_concepts, config)

            # 5. 创建复习会话
            review_sessions = self._create_review_sessions(review_concepts, config)

            # 6. 生成个性化元素
            personalization = self._generate_personalization_features(config, learning_analysis)

            # 7. 创建动态调整配置
            dynamic_adjustment = self._create_dynamic_adjustment_config(review_concepts, config)

            # 8. 生成完整计划
            plan_id = f"plan-{uuid.uuid4().hex[:16]}"

            review_plan = {
                "plan_id": plan_id,
                "user_id": user_id,
                "target_canvas": target_canvas,
                "generation_timestamp": datetime.now().isoformat(),
                "plan_type": plan_type,
                "config": asdict(config),
                "learning_analysis_summary": learning_analysis.get("analysis_summary", {}),
                "review_sessions": [asdict(session) for session in review_sessions],
                "personalization_features": personalization,
                "dynamic_adjustment": dynamic_adjustment,
                "success_metrics": self._calculate_success_metrics(review_concepts, learning_analysis),
                "estimated_completion_time": self._estimate_completion_time(review_sessions),
                "next_review_date": self._calculate_next_review_date(config),
            }

            return review_plan

        except Exception as e:
            raise RuntimeError(f"复习计划生成失败: {str(e)}")

    def _select_concepts_by_strategy(
        self,
        weak_concepts: List[Dict[str, Any]],
        learning_analysis: Dict[str, Any],
        config: ReviewPlanConfig
    ) -> List[Dict[str, Any]]:
        """根据策略选择概念

        Args:
            weak_concepts: 薄弱概念列表
            learning_analysis: 学习分析结果
            config: 复习计划配置

        Returns:
            List[Dict]: 选择的概念列表
        """
        strategy = self.REVIEW_STRATEGIES.get(config.plan_type, self.REVIEW_STRATEGIES["weakness_focused"])
        selected_concepts = []

        if config.plan_type == "weakness_focused":
            # 选择薄弱程度最高的概念
            selected_concepts = sorted(
                weak_concepts,
                key=lambda x: x.get("weakness_score", 0),
                reverse=True
            )[:strategy["max_concepts"]]

        elif config.plan_type == "comprehensive_review":
            # 全面复习，包括已掌握和部分掌握的概念
            mastery_analysis = learning_analysis.get("mastery_assessment", {})

            # 按掌握程度分层选择
            not_mastered = [c for c in weak_concepts if c.get("mastery_score", 0) < 8]
            partially_mastered = [c for c in weak_concepts if 5 <= c.get("mastery_score", 0) < 8]

            selected_concepts = not_mastered[:3] + partially_mastered[:strategy["max_concepts"]-3]

        elif config.plan_type == "targeted_review":
            # 针对性复习，可以基于用户指定或特定主题
            # 这里简化实现，优先选择紧急程度高的概念
            selected_concepts = sorted(
                weak_concepts,
                key=lambda x: (x.get("urgency_level", "low") == "high", x.get("weakness_score", 0)),
                reverse=True
            )[:strategy["max_concepts"]]

        # 应用用户偏好过滤
        if config.personalize_content:
            selected_concepts = self._apply_personal_preferences(selected_concepts, config)

        return selected_concepts

    def _generate_review_concepts(
        self,
        selected_concepts: List[Dict[str, Any]],
        config: ReviewPlanConfig
    ) -> List[ReviewConcept]:
        """生成复习概念对象

        Args:
            selected_concepts: 选择的概念列表
            config: 复习计划配置

        Returns:
            List[ReviewConcept]: 复习概念对象列表
        """
        review_concepts = []

        for concept_data in selected_concepts:
            concept_name = concept_data.get("concept_name", "")

            # 生成复习问题
            review_questions = self._generate_review_questions(concept_data, config)

            # 生成支持材料
            supporting_materials = self._generate_supporting_materials(concept_data, config)

            # 估算时间
            estimated_time = self._estimate_concept_review_time(concept_data, config)

            # 确定难度级别
            difficulty = self._determine_concept_difficulty(concept_data, config)

            # 查找相关概念和先决条件
            related_concepts = self._find_related_concepts(concept_name)
            prerequisites = self._find_prerequisites(concept_name)

            review_concept = ReviewConcept(
                concept_name=concept_name,
                weakness_score=concept_data.get("weakness_score", 0),
                mastery_score=concept_data.get("mastery_score", 0),
                difficulty=difficulty,
                urgency_level=concept_data.get("urgency_level", "medium"),
                recommended_focus_areas=concept_data.get("recommended_focus_areas", []),
                review_questions=review_questions,
                supporting_materials=supporting_materials,
                estimated_time_minutes=estimated_time,
                prerequisites=prerequisites,
                related_concepts=related_concepts
            )

            review_concepts.append(review_concept)

        return review_concepts

    def _generate_review_questions(
        self,
        concept_data: Dict[str, Any],
        config: ReviewPlanConfig
    ) -> List[Dict[str, Any]]:
        """生成复习问题

        Args:
            concept_data: 概念数据
            config: 复习计划配置

        Returns:
            List[Dict]: 复习问题列表
        """
        concept_name = concept_data.get("concept_name", "")
        weakness_type = concept_data.get("weakness_type", "general_weakness")
        mastery_score = concept_data.get("mastery_score", 5)

        questions = []

        # 根据薄弱类型生成不同类型的问题
        if weakness_type == "insufficient_exposure":
            questions.append(self._create_basic_understanding_question(concept_name))
        elif weakness_type == "lack_of_practice":
            questions.append(self._create_application_question(concept_name))
        elif weakness_type == "conceptual_misunderstanding":
            questions.append(self._create_concept_clarification_question(concept_name))
        elif weakness_type == "procedural_error":
            questions.append(self._create_procedure_question(concept_name))
        elif weakness_type == "recall_failure":
            questions.append(self._create_recall_question(concept_name))
        else:
            # 通用问题
            questions.append(self._create_general_review_question(concept_name))

        # 根据掌握程度添加额外问题
        if mastery_score < 4:
            questions.append(self._create_basic_question(concept_name))
        elif mastery_score < 7:
            questions.append(self._create_intermediate_question(concept_name))
        else:
            questions.append(self._create_advanced_question(concept_name))

        return questions[:3]  # 最多返回3个问题

    def _create_basic_understanding_question(self, concept_name: str) -> Dict[str, Any]:
        """创建基础理解问题"""
        return {
            "question_text": f"请用自己的话解释什么是{concept_name}？",
            "question_type": "conceptual_understanding",
            "suggested_approach": "从定义和核心特征开始",
            "estimated_time_minutes": 8,
            "difficulty": "basic",
            "evaluation_criteria": ["准确性", "完整性", "清晰度"]
        }

    def _create_application_question(self, concept_name: str) -> Dict[str, Any]:
        """创建应用问题"""
        return {
            "question_text": f"请举一个{concept_name}在实际中应用的例子，并解释为什么这个例子体现了{concept_name}的核心特征。",
            "question_type": "application",
            "suggested_approach": "先想一个具体场景，然后分析其特征",
            "estimated_time_minutes": 12,
            "difficulty": "intermediate",
            "evaluation_criteria": ["相关性", "理解深度", "解释清晰度"]
        }

    def _create_concept_clarification_question(self, concept_name: str) -> Dict[str, Any]:
        """创建概念澄清问题"""
        return {
            "question_text": f"{concept_name}与相似概念的主要区别是什么？请详细说明。",
            "question_type": "comparison",
            "suggested_approach": "列出相关概念，然后逐一比较关键特征",
            "estimated_time_minutes": 10,
            "difficulty": "intermediate",
            "evaluation_criteria": ["对比准确性", "区分清晰度", "深度理解"]
        }

    def _create_procedure_question(self, concept_name: str) -> Dict[str, Any]:
        """创建过程性问题"""
        return {
            "question_text": f"请详细描述应用{concept_name}的步骤或流程。",
            "question_type": "procedure",
            "suggested_approach": "按时间顺序或逻辑顺序列出关键步骤",
            "estimated_time_minutes": 15,
            "difficulty": "advanced",
            "evaluation_criteria": ["步骤完整性", "逻辑性", "实用性"]
        }

    def _create_recall_question(self, concept_name: str) -> Dict[str, Any]:
        """创建回忆性问题"""
        return {
            "question_text": f"不查阅资料的情况下，尽可能多地回忆{concept_name}相关的知识点。",
            "question_type": "recall",
            "suggested_approach": "从最基础的定义开始，逐步展开相关内容",
            "estimated_time_minutes": 8,
            "difficulty": "basic",
            "evaluation_criteria": ["回忆准确性", "知识广度", "组织结构"]
        }

    def _create_general_review_question(self, concept_name: str) -> Dict[str, Any]:
        """创建通用复习问题"""
        return {
            "question_text": f"请总结你对{concept_name}的理解，包括定义、重要性、应用场景等。",
            "question_type": "comprehensive",
            "suggested_approach": "从多个角度全面描述概念",
            "estimated_time_minutes": 12,
            "difficulty": "intermediate",
            "evaluation_criteria": ["全面性", "准确性", "深度"]
        }

    def _create_basic_question(self, concept_name: str) -> Dict[str, Any]:
        """创建基础问题"""
        return {
            "question_text": f"{concept_name}最基本的特点是什么？",
            "question_type": "basic",
            "suggested_approach": "关注核心定义和主要特征",
            "estimated_time_minutes": 5,
            "difficulty": "easy",
            "evaluation_criteria": ["准确性", "简洁性"]
        }

    def _create_intermediate_question(self, concept_name: str) -> Dict[str, Any]:
        """创建中等难度问题"""
        return {
            "question_text": f"解释{concept_name}在相关领域中的作用和意义。",
            "question_type": "contextual",
            "suggested_approach": "结合具体背景和实例进行分析",
            "estimated_time_minutes": 10,
            "difficulty": "medium",
            "evaluation_criteria": ["理解深度", "应用能力", "分析能力"]
        }

    def _create_advanced_question(self, concept_name: str) -> Dict[str, Any]:
        """创建高级问题"""
        return {
            "question_text": f"请分析{concept_name}的局限性或可能的改进方向。",
            "question_type": "critical_analysis",
            "suggested_approach": "批判性思考，提出改进建议",
            "estimated_time_minutes": 15,
            "difficulty": "hard",
            "evaluation_criteria": ["批判思维", "创新性", "分析深度"]
        }

    def _generate_supporting_materials(
        self,
        concept_data: Dict[str, Any],
        config: ReviewPlanConfig
    ) -> List[str]:
        """生成支持材料

        Args:
            concept_data: 概念数据
            config: 复习计划配置

        Returns:
            List[str]: 支持材料列表
        """
        concept_name = concept_data.get("concept_name", "")
        materials = []

        # 基于推荐关注领域生成材料
        focus_areas = concept_data.get("recommended_focus_areas", [])

        if "概念定义复习" in focus_areas:
            materials.append(f"建议重新阅读{concept_name}的基础定义和核心概念")

        if "实例练习加强" in focus_areas:
            materials.append(f"寻找{concept_name}的实际应用案例进行练习")

        if "与其他概念的关系理解" in focus_areas:
            materials.append(f"分析{concept_name}与相关概念的联系和区别")

        if "补充相关知识背景" in focus_areas:
            materials.append(f"了解{concept_name}的历史背景或发展过程")

        # 添加通用支持材料
        if config.include_explanations:
            materials.append("可查看相关AI解释材料加深理解")

        if config.include_examples:
            materials.append("通过具体例题来巩固理解")

        return materials[:5]  # 最多返回5条建议

    def _estimate_concept_review_time(
        self,
        concept_data: Dict[str, Any],
        config: ReviewPlanConfig
    ) -> int:
        """估算概念复习时间

        Args:
            concept_data: 概念数据
            config: 复习计划配置

        Returns:
            int: 估算时间（分钟）
        """
        base_time = 10  # 基础时间

        # 根据薄弱程度调整
        weakness_score = concept_data.get("weakness_score", 0.5)
        time_adjustment = 1 + weakness_score  # 薄弱程度越高，时间越长

        # 根据掌握程度调整
        mastery_score = concept_data.get("mastery_score", 5)
        if mastery_score < 4:
            time_adjustment += 0.5
        elif mastery_score > 8:
            time_adjustment -= 0.3

        # 根据难度级别调整
        difficulty_config = self.DIFFICULTY_LEVELS.get(config.difficulty_level, {})
        if config.difficulty_level != "adaptive":
            base_time = difficulty_config.get("time_per_concept", base_time)

        estimated_time = int(base_time * time_adjustment)
        return max(5, min(30, estimated_time))  # 限制在5-30分钟范围内

    def _determine_concept_difficulty(
        self,
        concept_data: Dict[str, Any],
        config: ReviewPlanConfig
    ) -> str:
        """确定概念难度级别

        Args:
            concept_data: 概念数据
            config: 复习计划配置

        Returns:
            str: 难度级别
        """
        if config.difficulty_level != "adaptive":
            return config.difficulty_level

        # 自适应难度确定
        mastery_score = concept_data.get("mastery_score", 5)
        weakness_score = concept_data.get("weakness_score", 0.5)

        if mastery_score >= 8 and weakness_score < 0.3:
            return "expert"
        elif mastery_score >= 6 and weakness_score < 0.5:
            return "hard"
        elif mastery_score >= 4:
            return "medium"
        else:
            return "easy"

    def _find_related_concepts(self, concept_name: str) -> List[str]:
        """查找相关概念

        Args:
            concept_name: 概念名称

        Returns:
            List[str]: 相关概念列表
        """
        if self.graphiti_client:
            try:
                related = self.graphiti_client.search_related_concepts(concept_name, limit=3)
                return [concept.get("name", "") for concept in related]
            except:
                pass

        # 简化实现，返回空列表
        return []

    def _find_prerequisites(self, concept_name: str) -> List[str]:
        """查找先决条件

        Args:
            concept_name: 概念名称

        Returns:
            List[str]: 先决条件列表
        """
        if self.graphiti_client:
            try:
                prerequisites = self.graphiti_client.get_prerequisites(concept_name, limit=2)
                return [concept.get("name", "") for concept in prerequisites]
            except:
                pass

        # 简化实现，返回空列表
        return []

    def _create_review_sessions(
        self,
        review_concepts: List[ReviewConcept],
        config: ReviewPlanConfig
    ) -> List[ReviewSession]:
        """创建复习会话

        Args:
            review_concepts: 复习概念列表
            config: 复习计划配置

        Returns:
            List[ReviewSession]: 复习会话列表
        """
        sessions = []

        # 根据概念数量和预计时间创建会话
        total_time = sum(concept.estimated_time_minutes for concept in review_concepts)

        if total_time <= config.estimated_duration:
            # 单个会话
            session = self._create_single_session(review_concepts, config)
            sessions.append(session)
        else:
            # 多个会话
            current_session_concepts = []
            current_time = 0
            session_counter = 1

            for concept in review_concepts:
                if current_time + concept.estimated_time_minutes > config.estimated_duration:
                    # 创建当前会话
                    if current_session_concepts:
                        session = self._create_single_session(current_session_concepts, config, session_counter)
                        sessions.append(session)

                    # 开始新会话
                    current_session_concepts = [concept]
                    current_time = concept.estimated_time_minutes
                    session_counter += 1
                else:
                    current_session_concepts.append(concept)
                    current_time += concept.estimated_time_minutes

            # 添加最后一个会话
            if current_session_concepts:
                session = self._create_single_session(current_session_concepts, config, session_counter)
                sessions.append(session)

        return sessions

    def _create_single_session(
        self,
        concepts: List[ReviewConcept],
        config: ReviewPlanConfig,
        session_number: int = 1
    ) -> ReviewSession:
        """创建单个复习会话

        Args:
            concepts: 会话包含的概念
            config: 复习计划配置
            session_number: 会话编号

        Returns:
            ReviewSession: 复习会话对象
        """
        session_id = f"session-{uuid.uuid4().hex[:12]}"
        total_time = sum(concept.estimated_time_minutes for concept in concepts)

        # 确定会话难度级别
        difficulties = [concept.difficulty for concept in concepts]
        session_difficulty = self._determine_session_difficulty(difficulties)

        # 生成学习目标
        learning_objectives = self._generate_learning_objectives(concepts, session_difficulty)

        # 确定会话类型
        session_type = f"{config.plan_type}_session_{session_number}"

        # 自适应元素
        adaptive_elements = self._create_adaptive_elements(concepts, config)

        return ReviewSession(
            session_id=session_id,
            concepts=concepts,
            estimated_duration=total_time,
            difficulty_level=session_difficulty,
            learning_objectives=learning_objectives,
            session_type=session_type,
            adaptive_elements=adaptive_elements
        )

    def _determine_session_difficulty(self, concept_difficulties: List[str]) -> str:
        """确定会话难度级别

        Args:
            concept_difficulties: 概念难度列表

        Returns:
            str: 会话难度级别
        """
        difficulty_weights = {"easy": 1, "medium": 2, "hard": 3, "expert": 4}

        if not concept_difficulties:
            return "medium"

        total_weight = sum(difficulty_weights.get(d, 2) for d in concept_difficulties)
        avg_weight = total_weight / len(concept_difficulties)

        if avg_weight <= 1.5:
            return "easy"
        elif avg_weight <= 2.5:
            return "medium"
        elif avg_weight <= 3.5:
            return "hard"
        else:
            return "expert"

    def _generate_learning_objectives(
        self,
        concepts: List[ReviewConcept],
        difficulty_level: str
    ) -> List[str]:
        """生成学习目标

        Args:
            concepts: 概念列表
            difficulty_level: 难度级别

        Returns:
            List[str]: 学习目标列表
        """
        objectives = []

        # 基础目标
        objectives.append("复习和巩固指定概念的核心知识")

        # 根据难度级别添加特定目标
        if difficulty_level in ["easy", "medium"]:
            objectives.append("提高概念理解的准确性和完整性")
        elif difficulty_level in ["hard", "expert"]:
            objectives.append("深化对概念复杂性和应用的理解")

        # 根据概念特点添加目标
        has_weak_concepts = any(c.weakness_score > 0.7 for c in concepts)
        if has_weak_concepts:
            objectives.append("重点突破薄弱环节，提升掌握程度")

        has_application_questions = any(
            "application" in q.question_type for c in concepts for q in c.review_questions
        )
        if has_application_questions:
            objectives.append("练习概念的实际应用能力")

        return objectives[:4]  # 最多返回4个目标

    def _create_adaptive_elements(
        self,
        concepts: List[ReviewConcept],
        config: ReviewPlanConfig
    ) -> Dict[str, Any]:
        """创建自适应元素

        Args:
            concepts: 概念列表
            config: 复习计划配置

        Returns:
            Dict: 自适应元素配置
        """
        return {
            "difficulty_adjustment": {
                "enabled": config.adaptive_difficulty,
                "triggers": ["performance_below_threshold", "completion_too_fast", "user_request"],
                "adjustment_range": "one_level_up_down",
            },
            "content_adaptation": {
                "enabled": config.personalize_content,
                "learning_style_matching": True,
                "preferred_content_types": ["visual", "textual", "interactive"],
            },
            "time_management": {
                "flexible_duration": True,
                "auto_extend_threshold": 0.8,
                "time_warnings": [0.5, 0.8],
            },
            "feedback_system": {
                "immediate_feedback": True,
                "detailed_explanations": True,
                "progress_tracking": True,
            }
        }

    def _generate_personalization_features(
        self,
        config: ReviewPlanConfig,
        learning_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成个性化特征

        Args:
            config: 复习计划配置
            learning_analysis: 学习分析结果

        Returns:
            Dict: 个性化特征
        """
        # 分析学习趋势
        trends = learning_analysis.get("learning_trends", {})

        # 分析参与模式
        engagement_patterns = trends.get("engagement_patterns", {})

        return {
            "learning_style_adaptation": {
                "preferred_approach": self._determine_preferred_approach(engagement_patterns),
                "complexity_tolerance": "gradual_increase",
                "feedback_preference": "immediate_explanations",
            },
            "time_optimization": {
                "optimal_study_duration": self._calculate_optimal_duration(engagement_patterns),
                "break_intervals": 15,
                "peak_performance_time": self._identify_peak_time(engagement_patterns),
            },
            "motivation_elements": {
                "progress_tracking": True,
                "achievement_milestones": self._generate_achievement_milestones(config),
                "encouraging_messages": True,
                "difficulty_progression": "visible",
            }
        }

    def _determine_preferred_approach(self, engagement_patterns: Dict[str, Any]) -> str:
        """确定偏好的学习方法

        Args:
            engagement_patterns: 参与模式

        Returns:
            str: 偏好的方法
        """
        interaction_types = engagement_patterns.get("interaction_types", {})

        question_freq = interaction_types.get("question_creation", 0)
        understanding_freq = interaction_types.get("understanding_input", 0)
        explanation_freq = interaction_types.get("explanation_access", 0)

        if understanding_freq > 0.5:
            return "self_explanation_focused"
        elif question_freq > 0.3:
            return "inquiry_based"
        elif explanation_freq > 0.4:
            return "guided_learning"
        else:
            return "balanced_approach"

    def _calculate_optimal_duration(self, engagement_patterns: Dict[str, Any]) -> int:
        """计算最佳学习时长

        Args:
            engagement_patterns: 参与模式

        Returns:
            int: 最佳时长（分钟）
        """
        avg_duration = engagement_patterns.get("average_session_duration", 45)
        return max(20, min(90, avg_duration))  # 限制在20-90分钟

    def _identify_peak_time(self, engagement_patterns: Dict[str, Any]) -> str:
        """识别最佳学习时间

        Args:
            engagement_patterns: 参与模式

        Returns:
            str: 最佳时间段
        """
        return engagement_patterns.get("preferred_study_time", "morning")

    def _generate_achievement_milestones(self, config: ReviewPlanConfig) -> List[str]:
        """生成成就里程碑

        Args:
            config: 复习计划配置

        Returns:
            List[str]: 里程碑列表
        """
        milestones = []

        if config.plan_type == "weakness_focused":
            milestones.extend([
                "完成3个薄弱概念的复习",
                "理解程度提升至75%以上",
                "能够独立解释所有概念"
            ])
        elif config.plan_type == "comprehensive_review":
            milestones.extend([
                "复习覆盖所有指定概念",
                "建立概念间的联系",
                "完成综合练习"
            ])
        elif config.plan_type == "targeted_review":
            milestones.extend([
                "掌握目标概念的深度理解",
                "能够解决相关应用问题",
                "形成个人知识体系"
            ])

        return milestones[:3]

    def _create_dynamic_adjustment_config(
        self,
        review_concepts: List[ReviewConcept],
        config: ReviewPlanConfig
    ) -> Dict[str, Any]:
        """创建动态调整配置

        Args:
            review_concepts: 复习概念列表
            config: 复习计划配置

        Returns:
            Dict: 动态调整配置
        """
        return {
            "initial_difficulty_level": config.difficulty_level,
            "adaptation_triggers": [
                "score_below_6_for_consecutive_attempts",
                "completion_time_significantly_faster_than_estimated",
                "user_requests_difficulty_change",
                "concept_mastery_rapidly_improves",
            ],
            "adjustment_strategies": {
                "increase_difficulty": "add_complexity_require_related_concepts",
                "decrease_difficulty": "provide_more_guidance_break_into_steps",
                "change_approach": "switch_to_visual_or_analogical_explanation",
                "adjust_content": "focus_on_weak_areas_or_expand_to_related_topics",
            },
            "performance_thresholds": {
                "mastery_threshold": 8.0,
                "struggle_threshold": 4.0,
                "speed_threshold": 0.5,  # 完成时间比例
            }
        }

    def _calculate_success_metrics(
        self,
        review_concepts: List[ReviewConcept],
        learning_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算成功指标

        Args:
            review_concepts: 复习概念列表
            learning_analysis: 学习分析结果

        Returns:
            Dict: 成功指标
        """
        # 基于当前薄弱程度设定目标
        avg_weakness = sum(c.weakness_score for c in review_concepts) / len(review_concepts) if review_concepts else 0.5

        # 基于历史表现设定目标
        current_mastery = sum(c.mastery_score for c in review_concepts) / len(review_concepts) if review_concepts else 5.0

        return {
            "target_completion_rate": 0.9,
            "target_average_score": min(10.0, current_mastery + (1.0 - avg_weakness) * 3),
            "target_time_efficiency": 0.8,
            "estimated_improvement_confidence": 0.85 if avg_weakness > 0.6 else 0.75,
            "target_mastery_improvement": min(3.0, avg_weakness * 4),
        }

    def _estimate_completion_time(self, review_sessions: List[ReviewSession]) -> Dict[str, Any]:
        """估算完成时间

        Args:
            review_sessions: 复习会话列表

        Returns:
            Dict: 完成时间估算
        """
        total_time = sum(session.estimated_duration for session in review_sessions)
        session_count = len(review_sessions)

        return {
            "total_estimated_minutes": total_time,
            "total_estimated_hours": round(total_time / 60, 1),
            "number_of_sessions": session_count,
            "average_session_duration": total_time // session_count if session_count > 0 else 0,
            "recommended_completion_days": max(1, session_count),
        }

    def _calculate_next_review_date(self, config: ReviewPlanConfig) -> str:
        """计算下次复习日期

        Args:
            config: 复习计划配置

        Returns:
            str: 下次复习日期ISO格式
        """
        # 基于艾宾浩斯算法计算
        if self.ebbinghaus_scheduler:
            try:
                # 简化实现，返回7天后
                next_date = datetime.now() + timedelta(days=7)
                return next_date.isoformat()
            except:
                pass

        # 默认返回7天后
        next_date = datetime.now() + timedelta(days=7)
        return next_date.isoformat()

    def _apply_personal_preferences(
        self,
        concepts: List[Dict[str, Any]],
        config: ReviewPlanConfig
    ) -> List[Dict[str, Any]]:
        """应用个人偏好过滤

        Args:
            concepts: 概念列表
            config: 复习计划配置

        Returns:
            List[Dict]: 过滤后的概念列表
        """
        # 简化实现，返回原列表
        # 在实际应用中可以根据用户历史偏好进行调整
        return concepts

    def adjust_plan_dynamically(
        self,
        plan_id: str,
        user_performance: Dict[str, Any]
    ) -> bool:
        """动态调整复习计划

        Args:
            plan_id: 计划ID
            user_performance: 用户表现数据

        Returns:
            bool: 调整是否成功
        """
        # 实现动态调整逻辑
        # 这里是简化实现
        return True

    def generate_progress_report(
        self,
        plan_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """生成复习进度报告

        Args:
            plan_id: 计划ID
            user_id: 用户ID

        Returns:
            Dict: 进度报告数据
        """
        # 实现进度报告生成逻辑
        # 这里是简化实现
        return {
            "plan_id": plan_id,
            "user_id": user_id,
            "generation_time": datetime.now().isoformat(),
            "overall_progress": 0.0,
            "concept_progress": {},
            "recommendations": [],
        }


# 示例使用
if __name__ == "__main__":
    # 创建智能复习计划生成器
    generator = IntelligentReviewGenerator()

    # 生成复习计划
    try:
        config = ReviewPlanConfig(
            user_id="default",
            target_canvas="离散数学.canvas",
            plan_type="weakness_focused",
            estimated_duration=45
        )

        review_plan = generator.generate_review_plan(
            user_id="default",
            target_canvas="离散数学.canvas",
            plan_type="weakness_focused",
            config=config
        )

        print("智能复习计划生成结果:")
        print(f"计划ID: {review_plan['plan_id']}")
        print(f"计划类型: {review_plan['plan_type']}")
        print(f"复习会话数: {len(review_plan['review_sessions'])}")
        print(f"预计总时长: {review_plan['estimated_completion_time']['total_estimated_minutes']} 分钟")

        # 显示复习会话
        for i, session in enumerate(review_plan['review_sessions'], 1):
            print(f"\n复习会话 {i}:")
            print(f"  难度级别: {session['difficulty_level']}")
            print(f"  预计时长: {session['estimated_duration']} 分钟")
            print(f"  包含概念: {len(session['concepts'])} 个")
            print(f"  学习目标: {session['learning_objectives']}")

    except Exception as e:
        print(f"复习计划生成失败: {e}")