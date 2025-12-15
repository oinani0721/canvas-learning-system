"""
智能问题生成器 - 动态检验白板系统 (Story 8.16)

实现基于用户掌握程度、知识图谱上下文和难度适配的智能问题生成系统。

Author: Canvas Learning System Team
Version: 1.0 (Story 8.16)
Created: 2025-01-22
"""

import json
import os
import uuid
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 尝试导入现有模块
try:
    from canvas_utils import COLOR_CODE_RED, COLOR_CODE_PURPLE, COLOR_CODE_GREEN
    from critical_nodes_extractor import CriticalNode, SourceAnalysis
    from knowledge_graph_integration import KnowledgeGraphContext, KnowledgeGraphIntegration
except ImportError:
    # 本地定义
    COLOR_CODE_RED = "4"
    COLOR_CODE_PURPLE = "3"
    COLOR_CODE_GREEN = "2"

    class CriticalNode:
        def __init__(self, **kwargs):
            self.node_id = kwargs.get("node_id", "")
            self.color = kwargs.get("color", "")
            self.concept_name = kwargs.get("concept_name", "")
            self.confidence_score = kwargs.get("confidence_score", 0.0)
            self.mastery_estimation = kwargs.get("mastery_estimation", 0.0)
            self.reason_for_critical = kwargs.get("reason_for_critical", "")
            self.text_content = kwargs.get("text_content", "")

    class SourceAnalysis:
        def __init__(self, **kwargs):
            self.critical_nodes_extracted = kwargs.get("critical_nodes_extracted", [])
            self.knowledge_graph_context = kwargs.get("knowledge_graph_context", {})

    class KnowledgeGraphIntegration:
        def __init__(self, *args, **kwargs):
            pass

# 尝试导入loguru
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


class QuestionType(Enum):
    """问题类型枚举"""
    CONCEPTUAL_UNDERSTANDING = "conceptual_understanding"      # 概念理解
    APPLICATION_SCENARIO = "application_scenario"              # 应用场景
    COMPARISON_ANALYSIS = "comparison_analysis"                # 对比分析
    PROBLEM_SOLVING = "problem_solving"                        # 问题求解
    EXAMPLE_GENERATION = "example_generation"                  # 例子生成
    CAUSE_EFFECT = "cause_effect"                              # 因果关系
    STEP_BY_STEP = "step_by_step"                              # 步骤说明
    CRITICAL_THINKING = "critical_thinking"                    # 批判思维


class DifficultyLevel(Enum):
    """难度级别枚举"""
    BASIC = "basic"          # 基础
    INTERMEDIATE = "intermediate"  # 中等
    ADVANCED = "advanced"    # 高级
    EXPERT = "expert"        # 专家级


@dataclass
class QuestionTemplate:
    """问题模板"""
    template_id: str
    question_type: QuestionType
    difficulty_level: DifficultyLevel
    template_text: str
    expected_answer_type: str
    context_requirements: List[str]
    generation_rules: Dict[str, Any]


@dataclass
class GeneratedQuestion:
    """生成的问题"""
    question_id: str
    source_node_id: str
    question_type: QuestionType
    difficulty_level: DifficultyLevel
    question_text: str
    expected_answer_type: str
    estimated_time_minutes: int
    hint_available: bool
    hint_text: str = ""
    learning_objectives: List[str] = field(default_factory=list)
    intelligent_generation: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    generation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class QuestionGenerationConfig:
    """问题生成配置"""
    max_questions_per_node: int = 3
    difficulty_adaptation: bool = True
    context_informed_generation: bool = True
    include_hints: bool = True
    quality_threshold: float = 0.7
    enable_adaptive_difficulty: bool = True
    personalize_for_user: bool = True


class IntelligentQuestionGenerator:
    """
    智能问题生成器

    实现多维度、自适应的问题生成：
    1. 基于用户掌握程度的难度适配
    2. 知识图谱上下文感知生成
    3. 多样化问题类型和模板
    4. 质量评估和优化
    5. 智能提示和指导
    """

    def __init__(self, config: Optional[QuestionGenerationConfig] = None, kg_integration: Optional[KnowledgeGraphIntegration] = None):
        """
        初始化智能问题生成器

        Args:
            config: 生成配置
            kg_integration: 知识图谱集成器
        """
        self.config = config or QuestionGenerationConfig()
        self.kg_integration = kg_integration or KnowledgeGraphIntegration()
        self.question_templates = self._initialize_question_templates()
        self.difficulty_adapter = DifficultyAdapter()
        self.quality_evaluator = QuestionQualityEvaluator()
        self.hint_generator = HintGenerator()

        if LOGURU_ENABLED:
            logger.info("IntelligentQuestionGenerator initialized")

    def _initialize_question_templates(self) -> Dict[QuestionType, List[QuestionTemplate]]:
        """初始化问题模板"""
        templates = {
            QuestionType.CONCEPTUAL_UNDERSTANDING: [
                QuestionTemplate(
                    template_id="concept_def_1",
                    question_type=QuestionType.CONCEPTUAL_UNDERSTANDING,
                    difficulty_level=DifficultyLevel.BASIC,
                    template_text="请用自己的话解释什么是{concept}，并说明它的核心特征。",
                    expected_answer_type="explanation_with_examples",
                    context_requirements=["definition", "characteristics"],
                    generation_rules={"min_length": 50, "require_examples": True}
                ),
                QuestionTemplate(
                    template_id="concept_def_2",
                    question_type=QuestionType.CONCEPTUAL_UNDERSTANDING,
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    template_text="{concept}与{related_concept}有什么区别和联系？请详细分析。",
                    expected_answer_type="comparative_analysis",
                    context_requirements=["related_concepts"],
                    generation_rules={"require_comparison": True, "min_points": 3}
                ),
                QuestionTemplate(
                    template_id="concept_def_3",
                    question_type=QuestionType.CONCEPTUAL_UNDERSTANDING,
                    difficulty_level=DifficultyLevel.ADVANCED,
                    template_text="从{perspective}的角度分析{concept}的本质，并探讨它在{domain}中的意义。",
                    expected_answer_type="deep_analysis",
                    context_requirements=["perspectives", "applications"],
                    generation_rules={"require_deep_analysis": True, "multiple_perspectives": True}
                )
            ],

            QuestionType.APPLICATION_SCENARIO: [
                QuestionTemplate(
                    template_id="app_scenario_1",
                    question_type=QuestionType.APPLICATION_SCENARIO,
                    difficulty_level=DifficultyLevel.BASIC,
                    template_text="请举一个{concept}在{scenario}中的应用实例。",
                    expected_answer_type="real_world_example",
                    context_requirements=["applications"],
                    generation_rules={"require_real_example": True}
                ),
                QuestionTemplate(
                    template_id="app_scenario_2",
                    question_type=QuestionType.APPLICATION_SCENARIO,
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    template_text="假设你遇到{problem}，如何运用{concept}来解决这个问题？",
                    expected_answer_type="problem_solution",
                    context_requirements=["problem_solving"],
                    generation_rules={"require_step_by_step": True}
                ),
                QuestionTemplate(
                    template_id="app_scenario_3",
                    question_type=QuestionType.APPLICATION_SCENARIO,
                    difficulty_level=DifficultyLevel.ADVANCED,
                    template_text="分析{concept}在{complex_scenario}中的综合应用，考虑{constraints}等限制因素。",
                    expected_answer_type="comprehensive_application",
                    context_requirements=["complex_applications"],
                    generation_rules={"require_constraint_analysis": True}
                )
            ],

            QuestionType.COMPARISON_ANALYSIS: [
                QuestionTemplate(
                    template_id="compare_1",
                    question_type=QuestionType.COMPARISON_ANALYSIS,
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    template_text="比较{concept}和{comparison_target}的异同点，可以从{comparison_dimensions}等角度分析。",
                    expected_answer_type="structured_comparison",
                    context_requirements=["comparable_concepts"],
                    generation_rules={"require_multiple_dimensions": True}
                )
            ],

            QuestionType.PROBLEM_SOLVING: [
                QuestionTemplate(
                    template_id="problem_1",
                    question_type=QuestionType.PROBLEM_SOLVING,
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    template_text="运用{concept}解决以下问题：{problem_description}",
                    expected_answer_type="step_by_step_solution",
                    context_requirements=["problem_types"],
                    generation_rules={"require_solution_steps": True}
                )
            ],

            QuestionType.EXAMPLE_GENERATION: [
                QuestionTemplate(
                    template_id="example_1",
                    question_type=QuestionType.EXAMPLE_GENERATION,
                    difficulty_level=DifficultyLevel.BASIC,
                    template_text="请创建一个关于{concept}的{example_type}例子，并解释为什么这是一个好例子。",
                    expected_answer_type="original_example",
                    context_requirements=["example_patterns"],
                    generation_rules={"require_originality": True}
                )
            ]
        }

        return templates

    def generate_review_questions(self, critical_nodes: List[CriticalNode], user_profile: Optional[Dict] = None) -> List[GeneratedQuestion]:
        """
        生成检验问题 - 主要入口函数

        Args:
            critical_nodes: 关键节点列表
            user_profile: 用户学习档案

        Returns:
            List[GeneratedQuestion]: 生成的问题列表
        """
        questions = []

        for node in critical_nodes:
            try:
                # 为每个节点生成问题
                node_questions = self._generate_questions_for_node(node, user_profile)

                # 限制每个节点的问题数量
                node_questions = node_questions[:self.config.max_questions_per_node]
                questions.extend(node_questions)

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.warning(f"Failed to generate questions for node {node.node_id}: {e}")
                continue

        # 质量过滤和排序
        filtered_questions = self._filter_and_rank_questions(questions)

        if LOGURU_ENABLED:
            logger.info(f"Generated {len(filtered_questions)} questions from {len(critical_nodes)} nodes")

        return filtered_questions

    def _generate_questions_for_node(self, node: CriticalNode, user_profile: Optional[Dict] = None) -> List[GeneratedQuestion]:
        """为单个节点生成问题"""
        questions = []

        # 确定基础难度级别
        base_difficulty = self._determine_base_difficulty(node, user_profile)

        # 选择合适的问题类型
        suitable_types = self._select_suitable_question_types(node, base_difficulty)

        for question_type in suitable_types:
            try:
                # 获取模板
                templates = self.question_templates.get(question_type, [])
                if not templates:
                    continue

                # 选择合适的模板
                template = self._select_template(templates, base_difficulty)

                # 适配难度
                adapted_difficulty = self.difficulty_adapter.adapt_difficulty(
                    base_difficulty, node.mastery_estimation, user_profile
                )

                # 生成问题
                question = self._generate_question_from_template(template, node, adapted_difficulty)

                # 质量评估
                quality_score = self.quality_evaluator.evaluate_question(question, node, user_profile)
                question.quality_score = quality_score

                # 生成提示
                if self.config.include_hints:
                    hint = self.hint_generator.generate_hint(question, node)
                    question.hint_text = hint
                    question.hint_available = True

                questions.append(question)

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.warning(f"Failed to generate {question_type} question: {e}")
                continue

        return questions

    def _determine_base_difficulty(self, node: CriticalNode, user_profile: Optional[Dict]) -> DifficultyLevel:
        """确定基础难度级别"""
        mastery = node.mastery_estimation

        # 基于掌握度确定难度
        if mastery < 0.3:
            return DifficultyLevel.BASIC
        elif mastery < 0.6:
            return DifficultyLevel.INTERMEDIATE
        elif mastery < 0.8:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.EXPERT

    def _select_suitable_question_types(self, node: CriticalNode, difficulty: DifficultyLevel) -> List[QuestionType]:
        """选择合适的问题类型"""
        suitable_types = []

        # 基于节点颜色选择类型
        if node.color == COLOR_CODE_RED:
            # 红色节点：基础理解和应用
            suitable_types.extend([
                QuestionType.CONCEPTUAL_UNDERSTANDING,
                QuestionType.APPLICATION_SCENARIO,
                QuestionType.EXAMPLE_GENERATION
            ])
        elif node.color == COLOR_CODE_PURPLE:
            # 紫色节点：对比分析、问题解决
            suitable_types.extend([
                QuestionType.COMPARISON_ANALYSIS,
                QuestionType.PROBLEM_SOLVING,
                QuestionType.CRITICAL_THINKING
            ])

        # 基于难度调整类型
        if difficulty == DifficultyLevel.BASIC:
            suitable_types = [t for t in suitable_types if t in [
                QuestionType.CONCEPTUAL_UNDERSTANDING,
                QuestionType.EXAMPLE_GENERATION
            ]]
        elif difficulty in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
            suitable_types.extend([
                QuestionType.CRITICAL_THINKING,
                QuestionType.STEP_BY_STEP
            ])

        return suitable_types[:3]  # 限制类型数量

    def _select_template(self, templates: List[QuestionTemplate], difficulty: DifficultyLevel) -> QuestionTemplate:
        """选择合适的模板"""
        # 筛选匹配难度的模板
        matching_templates = [t for t in templates if t.difficulty_level == difficulty]

        # 如果没有完全匹配的，选择相近难度的
        if not matching_templates:
            difficulty_order = [DifficultyLevel.BASIC, DifficultyLevel.INTERMEDIATE,
                              DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]

            for diff in difficulty_order:
                matching_templates = [t for t in templates if t.difficulty_level == diff]
                if matching_templates:
                    break

        # 随机选择一个模板
        return random.choice(matching_templates) if matching_templates else templates[0]

    def _generate_question_from_template(self, template: QuestionTemplate, node: CriticalNode, difficulty: DifficultyLevel) -> GeneratedQuestion:
        """从模板生成问题"""
        # 准备替换变量
        variables = self._prepare_template_variables(node, difficulty)

        # 替换模板变量
        question_text = template.template_text
        for key, value in variables.items():
            question_text = question_text.replace(f"{{{key}}}", value)

        # 生成学习目标
        learning_objectives = self._generate_learning_objectives(template, node)

        # 智能生成元数据
        intelligent_generation = {
            "generation_method": "template_based",
            "adapted_from_user_performance": self.config.enable_adaptive_difficulty,
            "knowledge_graph_informed": self.config.context_informed_generation,
            "template_id": template.template_id,
            "difficulty_adapted": difficulty.value != template.difficulty_level.value
        }

        return GeneratedQuestion(
            question_id=f"q-{uuid.uuid4().hex[:16]}",
            source_node_id=node.node_id,
            question_type=template.question_type,
            difficulty_level=difficulty,
            question_text=question_text,
            expected_answer_type=template.expected_answer_type,
            estimated_time_minutes=self._estimate_time(difficulty, template.question_type),
            hint_available=self.config.include_hints,
            learning_objectives=learning_objectives,
            intelligent_generation=intelligent_generation
        )

    def _prepare_template_variables(self, node: CriticalNode, difficulty: DifficultyLevel) -> Dict[str, str]:
        """准备模板变量"""
        concept_name = node.concept_name or node.text_content[:50]

        variables = {
            "concept": concept_name,
            "difficulty": difficulty.value,
            "mastery_level": f"{node.mastery_estimation:.1%}"
        }

        # 根据节点内容添加更多变量
        if "定义" in node.text_content or "definition" in node.text_content.lower():
            variables["definition"] = "定义和基本概念"

        if "应用" in node.text_content or "application" in node.text_content.lower():
            variables["applications"] = "实际应用场景"

        # 添加相关的上下文变量
        context_variables = self._extract_context_variables(node)
        variables.update(context_variables)

        return variables

    def _extract_context_variables(self, node: CriticalNode) -> Dict[str, str]:
        """提取上下文变量"""
        variables = {}

        # 基于概念名称推断相关概念
        concept_lower = node.concept_name.lower()

        if "逻辑" in concept_lower:
            variables.update({
                "related_concept": "命题、推理、证明",
                "scenario": "数学证明或日常推理",
                "domain": "数理逻辑"
            })
        elif "集合" in concept_lower:
            variables.update({
                "related_concept": "元素、子集、并集、交集",
                "scenario": "数据分类或群体分析",
                "domain": "集合论"
            })
        elif "函数" in concept_lower:
            variables.update({
                "related_concept": "定义域、值域、映射",
                "scenario": "数学建模或程序设计",
                "domain": "数学分析"
            })

        # 添加通用的教学变量
        variables.update({
            "perspective": "理论和实践",
            "example_type": "生活化",
            "comparison_dimensions": "定义、性质、应用",
            "problem_description": "一个需要分析的具体情况",
            "constraints": "实际条件和限制因素"
        })

        return variables

    def _generate_learning_objectives(self, template: QuestionTemplate, node: CriticalNode) -> List[str]:
        """生成学习目标"""
        objectives = []

        concept_name = node.concept_name or "这个概念"

        if template.question_type == QuestionType.CONCEPTUAL_UNDERSTANDING:
            objectives = [
                f"理解{concept_name}的基本定义",
                f"掌握{concept_name}的核心特征",
                "能够用自己话解释概念"
            ]
        elif template.question_type == QuestionType.APPLICATION_SCENARIO:
            objectives = [
                f"了解{concept_name}的实际应用",
                "能够在具体场景中运用概念",
                "培养解决问题的能力"
            ]
        elif template.question_type == QuestionType.COMPARISON_ANALYSIS:
            objectives = [
                "培养对比分析能力",
                "理解概念间的联系和区别",
                "发展系统性思维"
            ]
        else:
            objectives = [
                f"深化对{concept_name}的理解",
                "提高分析思考能力",
                "建立知识间的联系"
            ]

        return objectives[:3]  # 限制目标数量

    def _estimate_time(self, difficulty: DifficultyLevel, question_type: QuestionType) -> int:
        """估算答题时间（分钟）"""
        base_times = {
            DifficultyLevel.BASIC: 5,
            DifficultyLevel.INTERMEDIATE: 10,
            DifficultyLevel.ADVANCED: 15,
            DifficultyLevel.EXPERT: 20
        }

        type_multipliers = {
            QuestionType.CONCEPTUAL_UNDERSTANDING: 1.0,
            QuestionType.APPLICATION_SCENARIO: 1.2,
            QuestionType.COMPARISON_ANALYSIS: 1.3,
            QuestionType.PROBLEM_SOLVING: 1.5,
            QuestionType.EXAMPLE_GENERATION: 1.1,
            QuestionType.CRITICAL_THINKING: 1.6
        }

        base_time = base_times.get(difficulty, 10)
        multiplier = type_multipliers.get(question_type, 1.0)

        return int(base_time * multiplier)

    def _filter_and_rank_questions(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """过滤和排序问题"""
        # 质量过滤
        filtered = [q for q in questions if q.quality_score >= self.config.quality_threshold]

        # 按质量分数排序
        filtered.sort(key=lambda q: q.quality_score, reverse=True)

        # 平衡问题类型分布
        balanced_questions = self._balance_question_types(filtered)

        return balanced_questions

    def _balance_question_types(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """平衡问题类型分布"""
        # 统计各类型数量
        type_counts = {}
        for q in questions:
            qtype = q.question_type
            type_counts[qtype] = type_counts.get(qtype, 0) + 1

        # 如果某种类型过多，进行限制
        max_per_type = max(len(questions) // 3, 2)  # 每种类型最多占总数的1/3，但至少2个
        balanced = []

        for q in questions:
            qtype = q.question_type
            if type_counts.get(qtype, 0) <= max_per_type:
                balanced.append(q)
            else:
                type_counts[qtype] -= 1  # 跳过这个问题

        return balanced


class DifficultyAdapter:
    """难度适配器"""

    def adapt_difficulty(self, base_difficulty: DifficultyLevel, mastery_estimation: float, user_profile: Optional[Dict]) -> DifficultyLevel:
        """适配难度级别"""
        if not user_profile:
            return base_difficulty

        # 基于用户表现调整难度
        user_performance = user_profile.get("performance_score", 0.5)
        learning_preference = user_profile.get("learning_preference", "balanced")

        # 计算调整因子
        mastery_factor = 1.0 - mastery_estimation  # 掌握度越低，难度越低
        performance_factor = user_performance

        adjustment_factor = (mastery_factor + performance_factor) / 2

        # 根据学习偏好调整
        if learning_preference == "challenge":
            adjustment_factor += 0.1
        elif learning_preference == "supportive":
            adjustment_factor -= 0.1

        # 确定最终难度
        if adjustment_factor < 0.3:
            return DifficultyLevel.BASIC
        elif adjustment_factor < 0.6:
            return DifficultyLevel.INTERMEDIATE
        elif adjustment_factor < 0.8:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.EXPERT


class QuestionQualityEvaluator:
    """问题质量评估器"""

    def evaluate_question(self, question: GeneratedQuestion, node: CriticalNode, user_profile: Optional[Dict]) -> float:
        """评估问题质量"""
        scores = []

        # 清晰度评分 (0-1)
        clarity_score = self._evaluate_clarity(question)
        scores.append(clarity_score)

        # 相关性评分 (0-1)
        relevance_score = self._evaluate_relevance(question, node)
        scores.append(relevance_score)

        # 难度适宜性评分 (0-1)
        difficulty_score = self._evaluate_difficulty_appropriateness(question, node, user_profile)
        scores.append(difficulty_score)

        # 完整性评分 (0-1)
        completeness_score = self._evaluate_completeness(question)
        scores.append(completeness_score)

        # 加权平均
        weights = [0.3, 0.3, 0.25, 0.15]  # 清晰度、相关性、难度、完整性
        total_score = sum(score * weight for score, weight in zip(scores, weights))

        return round(total_score, 2)

    def _evaluate_clarity(self, question: GeneratedQuestion) -> float:
        """评估问题清晰度"""
        text = question.question_text

        # 检查长度适中
        if len(text) < 20 or len(text) > 200:
            return 0.5

        # 检查是否有明确的任务词
        task_words = ["请", "解释", "分析", "比较", "举例", "解决", "说明"]
        has_task_word = any(word in text for word in task_words)

        if not has_task_word:
            return 0.6

        # 检查语法结构
        if "？" in text or "请" in text:
            return 0.9
        else:
            return 0.7

    def _evaluate_relevance(self, question: GeneratedQuestion, node: CriticalNode) -> float:
        """评估问题相关性"""
        concept_name = node.concept_name.lower()
        question_text = question.question_text.lower()

        # 检查概念名称是否在问题中
        if concept_name in question_text:
            base_score = 0.8
        else:
            base_score = 0.4

        # 检查相关关键词
        related_keywords = ["定义", "应用", "例子", "分析", "比较"]
        keyword_matches = sum(1 for kw in related_keywords if kw in question_text)
        keyword_bonus = min(keyword_matches * 0.1, 0.2)

        return min(base_score + keyword_bonus, 1.0)

    def _evaluate_difficulty_appropriateness(self, question: GeneratedQuestion, node: CriticalNode, user_profile: Optional[Dict]) -> float:
        """评估难度适宜性"""
        mastery = node.mastery_estimation
        difficulty_map = {
            DifficultyLevel.BASIC: 0.2,
            DifficultyLevel.INTERMEDIATE: 0.5,
            DifficultyLevel.ADVANCED: 0.8,
            DifficultyLevel.EXPERT: 0.9
        }

        question_difficulty = difficulty_map.get(question.difficulty_level, 0.5)

        # 理想情况：问题难度略高于当前掌握度
        ideal_difficulty = min(mastery + 0.1, 1.0)

        # 计算适宜性分数
        difference = abs(question_difficulty - ideal_difficulty)
        appropriateness = max(0, 1 - difference * 2)  # 差异越小，分数越高

        return appropriateness

    def _evaluate_completeness(self, question: GeneratedQuestion) -> float:
        """评估问题完整性"""
        score = 0.0

        # 有明确的问题类型
        if question.question_type:
            score += 0.3

        # 有预期答案类型
        if question.expected_answer_type:
            score += 0.2

        # 有学习目标
        if question.learning_objectives:
            score += 0.2

        # 有时间估算
        if question.estimated_time_minutes > 0:
            score += 0.1

        # 有智能生成元数据
        if question.intelligent_generation:
            score += 0.2

        return score


class HintGenerator:
    """提示生成器"""

    def generate_hint(self, question: GeneratedQuestion, node: CriticalNode) -> str:
        """生成问题提示"""
        hint_templates = {
            QuestionType.CONCEPTUAL_UNDERSTANDING: [
                "💡 提示：从{concept}的基本定义开始思考，它的核心特征是什么？",
                "💡 提示：想想{concept}在现实生活中有哪些例子？",
                "💡 提示：试着用简单的话向一个初学者解释{concept}。"
            ],
            QuestionType.APPLICATION_SCENARIO: [
                "💡 提示：先回忆{concept}的定义，然后思考它如何应用到具体情况。",
                "💡 提示：考虑{concept}的使用条件和前提。",
                "💡 提示：分析问题场景，找出可以运用{concept}的关键点。"
            ],
            QuestionType.COMPARISON_ANALYSIS: [
                "💡 提示：从定义、性质、应用等方面进行对比。",
                "💡 提示：既要找出相同点，也要分析不同点。",
                "💡 提示：思考它们之间的关系和联系。"
            ]
        }

        templates = hint_templates.get(question.question_type, [
            "💡 提示：仔细阅读问题，思考相关的概念和例子。"
        ])

        # 选择模板并替换变量
        template = random.choice(templates)
        hint = template.replace("{concept}", node.concept_name or "这个概念")

        return hint


# 便利函数
def generate_intelligent_questions(critical_nodes: List[CriticalNode], user_profile: Optional[Dict] = None,
                                 config: Optional[QuestionGenerationConfig] = None) -> List[GeneratedQuestion]:
    """
    便利函数：生成智能问题

    Args:
        critical_nodes: 关键节点列表
        user_profile: 用户档案
        config: 生成配置

    Returns:
        List[GeneratedQuestion]: 生成的问题列表
    """
    generator = IntelligentQuestionGenerator(config)
    return generator.generate_review_questions(critical_nodes, user_profile)


if __name__ == "__main__":
    # 简单测试
    test_node = CriticalNode(
        node_id="test-001",
        color=COLOR_CODE_RED,
        concept_name="逻辑等价性",
        confidence_score=0.8,
        mastery_estimation=0.3,
        reason_for_critical="测试",
        text_content="逻辑等价性是命题逻辑中的重要概念"
    )

    questions = generate_intelligent_questions([test_node])
    print(f"Generated {len(questions)} questions for test node")
    for q in questions:
        print(f"- {q.question_text} (Difficulty: {q.difficulty_level.value}, Quality: {q.quality_score})")