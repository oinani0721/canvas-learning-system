"""
动态检验白板生成器 - Story 8.16核心实现

集成所有组件，实现完整的动态检验白板生成和管理功能。

Author: Canvas Learning System Team
Version: 1.0 (Story 8.16)
Created: 2025-01-22
"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 导入所有组件
try:
    from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic, COLOR_CODE_YELLOW, COLOR_CODE_BLUE
    from critical_nodes_extractor import CriticalNodesExtractor, CriticalNode, SourceAnalysis
    from knowledge_graph_integration import KnowledgeGraphIntegration, KnowledgeGraphContext
    from learning_cycle_manager import LearningCycleManager, LearningStep
    from intelligent_question_generator import IntelligentQuestionGenerator, GeneratedQuestion, QuestionGenerationConfig
except ImportError as e:
    print(f"Warning: Failed to import components: {e}")
    # 简化的本地导入
    from critical_nodes_extractor import CriticalNodesExtractor, CriticalNode, SourceAnalysis

# 尝试导入loguru
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


@dataclass
class DynamicReviewCanvas:
    """动态检验白板数据结构"""
    canvas_id: str
    source_canvas: str
    generation_timestamp: str
    iteration_count: int
    learning_cycle_step: str

    source_analysis: SourceAnalysis
    review_questions: List[GeneratedQuestion]
    dynamic_learning_cycle: Dict[str, Any]
    knowledge_network_expansion: Dict[str, Any]
    progress_tracking: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    user_interaction_data: Dict[str, Any]
    ai_analysis_insights: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "canvas_id": self.canvas_id,
            "source_canvas": self.source_canvas,
            "generation_timestamp": self.generation_timestamp,
            "iteration_count": self.iteration_count,
            "learning_cycle_step": self.learning_cycle_step,
            "source_analysis": self._serialize_source_analysis(),
            "review_questions": [self._serialize_question(q) for q in self.review_questions],
            "dynamic_learning_cycle": self.dynamic_learning_cycle,
            "knowledge_network_expansion": self.knowledge_network_expansion,
            "progress_tracking": self.progress_tracking,
            "quality_metrics": self.quality_metrics,
            "user_interaction_data": self.user_interaction_data,
            "ai_analysis_insights": self.ai_analysis_insights
        }

    def _serialize_source_analysis(self) -> Dict[str, Any]:
        """序列化源分析"""
        return {
            "canvas_id": self.source_analysis.canvas_id,
            "extraction_algorithm": self.source_analysis.extraction_algorithm,
            "total_source_nodes": self.source_analysis.total_source_nodes,
            "critical_nodes_extracted": [
                {
                    "node_id": node.node_id,
                    "color": node.color,
                    "concept_name": node.concept_name,
                    "confidence_score": node.confidence_score,
                    "mastery_estimation": node.mastery_estimation,
                    "reason_for_critical": node.reason_for_critical,
                    "text_content": node.text_content
                }
                for node in self.source_analysis.critical_nodes_extracted
            ],
            "knowledge_graph_context": self.source_analysis.knowledge_graph_context
        }

    def _serialize_question(self, question: GeneratedQuestion) -> Dict[str, Any]:
        """序列化问题"""
        # Handle both enum and string cases for question_type and difficulty_level
        question_type_value = question.question_type.value if hasattr(question.question_type, 'value') else question.question_type
        difficulty_value = question.difficulty_level.value if hasattr(question.difficulty_level, 'value') else question.difficulty_level

        return {
            "question_id": question.question_id,
            "source_node_id": question.source_node_id,
            "question_type": question_type_value,
            "difficulty_level": difficulty_value,
            "question_text": question.question_text,
            "expected_answer_type": question.expected_answer_type,
            "estimated_time_minutes": question.estimated_time_minutes,
            "hint_available": question.hint_available,
            "hint_text": question.hint_text,
            "learning_objectives": question.learning_objectives,
            "intelligent_generation": question.intelligent_generation,
            "quality_score": question.quality_score,
            "generation_timestamp": question.generation_timestamp
        }


class DynamicReviewCanvasGenerator:
    """
    动态检验白板生成器

    这是Story 8.16的核心组件，整合了所有子模块：
    1. 智能节点提取 (CriticalNodesExtractor)
    2. 知识图谱分析 (KnowledgeGraphIntegration)
    3. 智能问题生成 (IntelligentQuestionGenerator)
    4. 学习循环管理 (LearningCycleManager)
    5. Canvas布局和生成
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化动态检验白板生成器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)

        # 初始化所有组件
        self.nodes_extractor = CriticalNodesExtractor(self.config.get("node_extraction", {}))
        self.kg_integration = KnowledgeGraphIntegration(self.config.get("knowledge_graph", {}))
        self.question_generator = IntelligentQuestionGenerator(
            config=QuestionGenerationConfig(**self.config.get("question_generation", {})),
            kg_integration=self.kg_integration
        )

        # Canvas布局参数
        self.layout_params = self.config.get("layout", {
            "canvas_width": 2000,
            "canvas_height": 1500,
            "question_spacing_x": 500,
            "question_spacing_y": 400,
            "starting_x": 100,
            "starting_y": 100
        })

        if LOGURU_ENABLED:
            logger.info("DynamicReviewCanvasGenerator initialized")

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置"""
        default_config = {
            "node_extraction": {
                "critical_colors": ["4", "3"],  # 红色和紫色
                "confidence_threshold": 0.7,
                "mastery_threshold": 0.7
            },
            "question_generation": {
                "max_questions_per_node": 3,
                "difficulty_adaptation": True,
                "context_informed_generation": True,
                "include_hints": True,
                "quality_threshold": 0.7
            },
            "knowledge_graph": {
                "enable_mcp": True,
                "context_analysis": True,
                "max_related_concepts": 5,
                "similarity_threshold": 0.3,
                "mcp_timeout": 30
            },
            "learning_cycle": {
                "auto_advance": False,
                "max_iterations": 10,
                "progress_tracking": True
            },
            "layout": {
                "canvas_width": 2000,
                "canvas_height": 1500,
                "question_spacing_x": 500,
                "question_spacing_y": 400,
                "starting_x": 100,
                "starting_y": 100
            },
            "progress_tracking": {
                "green_node_threshold": 80.0,
                "iteration_limit": 10,
                "time_limit_hours": 24
            }
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 合并配置
                default_config.update(user_config)
                if LOGURU_ENABLED:
                    logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.warning(f"Failed to load config from {config_path}: {e}")

        return default_config

    def create_review_canvas(self, source_canvas: str, iteration: int = 1, user_profile: Optional[Dict] = None) -> str:
        """
        创建检验白板 - 主要入口函数

        Args:
            source_canvas: 源Canvas文件路径
            iteration: 迭代次数
            user_profile: 用户学习档案

        Returns:
            str: 创建的检验白板文件路径
        """
        try:
            if LOGURU_ENABLED:
                logger.info(f"Creating review canvas from {source_canvas}, iteration {iteration}")

            # 1. 提取关键节点
            source_analysis = self.nodes_extractor.extract_critical_nodes(source_canvas)

            if not source_analysis.critical_nodes_extracted:
                raise ValueError("No critical nodes found in source canvas")

            # 2. 生成检验问题
            review_questions = self.question_generator.generate_review_questions(
                source_analysis.critical_nodes_extracted, user_profile
            )

            # 3. 分析知识图谱上下文
            concepts = [node.concept_name for node in source_analysis.critical_nodes_extracted]
            canvas_data = CanvasJSONOperator.read_canvas(source_canvas)
            kg_context = self.kg_integration.analyze_concept_context(concepts, canvas_data)

            # 4. 创建动态检验白板对象
            dynamic_canvas = DynamicReviewCanvas(
                canvas_id=f"canvas-{uuid.uuid4().hex[:16]}",
                source_canvas=source_canvas,
                generation_timestamp=datetime.now().isoformat(),
                iteration_count=iteration,
                learning_cycle_step="step_1_understanding",
                source_analysis=source_analysis,
                review_questions=review_questions,
                dynamic_learning_cycle=self._create_learning_cycle_info(),
                knowledge_network_expansion=self._create_network_expansion_info(),
                progress_tracking=self._create_progress_tracking_info(),
                quality_metrics=self._calculate_quality_metrics(review_questions, source_analysis),
                user_interaction_data=self._create_user_interaction_data(),
                ai_analysis_insights=self._generate_ai_insights(source_analysis, kg_context)
            )

            # 5. 生成Canvas文件
            canvas_file_path = self._generate_canvas_file(dynamic_canvas, source_canvas, iteration)

            # 6. 保存元数据
            self._save_canvas_metadata(dynamic_canvas, canvas_file_path)

            if LOGURU_ENABLED:
                logger.info(f"Review canvas created successfully: {canvas_file_path}")

            return canvas_file_path

        except Exception as e:
            error_msg = f"Failed to create review canvas: {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    def process_learning_cycle_step(self, canvas_path: str, step: int, user_input: Dict) -> Dict:
        """
        处理学习循环步骤

        Args:
            canvas_path: Canvas文件路径
            step: 当前步骤
            user_input: 用户输入数据

        Returns:
            Dict: 处理结果
        """
        try:
            # 初始化学习循环管理器
            cycle_manager = LearningCycleManager(canvas_path, self.config.get("learning_cycle", {}))

            # 处理用户输入
            step_result = cycle_manager.process_user_input(user_input)

            # 如果步骤完成，尝试推进到下一步
            if step_result.success and step_result.output_data.get("can_advance", False):
                advance_result = cycle_manager.advance_to_next_step(step_result.output_data)
                step_result.output_data["advance_result"] = advance_result.__dict__

            # 获取当前进度
            progress = cycle_manager.get_cycle_progress()

            return {
                "step_result": step_result.__dict__,
                "cycle_progress": progress,
                "next_instructions": cycle_manager.get_step_instructions()
            }

        except Exception as e:
            error_msg = f"Failed to process learning cycle step: {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg)
            return {"error": error_msg, "success": False}

    def evaluate_progress(self, canvas_path: str) -> Dict:
        """
        评估学习进度

        Args:
            canvas_path: Canvas文件路径

        Returns:
            Dict: 进度评估结果
        """
        try:
            # 读取Canvas文件
            canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

            # 分析节点颜色分布
            nodes = canvas_data.get("nodes", [])
            color_counts = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}
            for node in nodes:
                color = node.get("color")
                if color in color_counts:
                    color_counts[color] += 1

            total_nodes = len(nodes)
            if total_nodes == 0:
                return {"error": "No nodes found in canvas", "success": False}

            # 计算进度指标
            green_nodes = color_counts.get("2", 0)  # 绿色（完全理解）
            yellow_nodes = color_counts.get("6", 0)  # 黄色（用户理解）
            red_nodes = color_counts.get("4", 0)    # 红色（不理解）
            purple_nodes = color_counts.get("3", 0) # 紫色（似懂非懂）

            # 计算完成百分比（绿色+黄色占总数的比例）
            completion_percentage = ((green_nodes + yellow_nodes) / total_nodes) * 100

            # 计算质量指标
            quality_metrics = {
                "node_distribution": color_counts,
                "completion_percentage": completion_percentage,
                "mastery_level": (green_nodes / total_nodes) * 100 if total_nodes > 0 else 0,
                "needs_attention": (red_nodes + purple_nodes) / total_nodes * 100 if total_nodes > 0 else 0
            }

            # 生成评估结果
            progress_result = {
                "overall_progress": {
                    "total_nodes": total_nodes,
                    "green_nodes": green_nodes,
                    "yellow_nodes": yellow_nodes,
                    "red_nodes": red_nodes,
                    "purple_nodes": purple_nodes,
                    "completion_percentage": completion_percentage
                },
                "quality_metrics": quality_metrics,
                "stopping_conditions": self._check_stopping_conditions(quality_metrics),
                "recommendations": self._generate_recommendations(quality_metrics)
            }

            return progress_result

        except Exception as e:
            error_msg = f"Failed to evaluate progress: {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg)
            return {"error": error_msg, "success": False}

    def should_continue_iteration(self, progress_data: Dict) -> Dict:
        """
        判断是否继续迭代

        Args:
            progress_data: 进度数据

        Returns:
            Dict: 继续迭代决策
        """
        try:
            quality_metrics = progress_data.get("quality_metrics", {})
            completion_percentage = quality_metrics.get("completion_percentage", 0)
            mastery_level = quality_metrics.get("mastery_level", 0)

            # 获取停止条件配置
            stopping_config = self.config.get("progress_tracking", {})
            green_threshold = stopping_config.get("green_node_threshold", 80.0)
            iteration_limit = stopping_config.get("iteration_limit", 10)

            # 检查停止条件
            should_stop = False
            stop_reason = ""

            if completion_percentage >= green_threshold:
                should_stop = True
                stop_reason = "达到完成度阈值"
            elif mastery_level >= 90:
                should_stop = True
                stop_reason = "掌握度达到优秀水平"

            # 估算还需要的迭代次数
            estimated_iterations = max(1, int((green_threshold - completion_percentage) / 20))

            decision = {
                "should_continue": not should_stop,
                "recommended_action": "continue_iteration" if not should_stop else "complete_learning",
                "estimated_completion_iterations": estimated_iterations,
                "stop_reason": stop_reason if should_stop else None,
                "confidence_score": min(completion_percentage / green_threshold, 1.0)
            }

            return decision

        except Exception as e:
            error_msg = f"Failed to evaluate continuation: {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg)
            return {"error": error_msg, "should_continue": False}

    def expand_knowledge_network(self, canvas_path: str, user_additions: List[Dict]) -> Dict:
        """
        扩展知识网络

        Args:
            canvas_path: Canvas文件路径
            user_additions: 用户添加的内容

        Returns:
            Dict: 扩展结果
        """
        try:
            # 读取现有Canvas
            canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

            # 记录添加前状态
            original_nodes = len(canvas_data.get("nodes", []))
            original_edges = len(canvas_data.get("edges", []))

            # 处理用户添加
            added_nodes = []
            added_edges = []
            relationships_established = []

            for addition in user_additions:
                if addition.get("type") == "node":
                    # 添加新节点
                    node_id = self._add_user_node(canvas_data, addition)
                    added_nodes.append(node_id)
                elif addition.get("type") == "edge":
                    # 添加新连接
                    edge_id = self._add_user_edge(canvas_data, addition)
                    added_edges.append(edge_id)
                elif addition.get("type") == "relationship":
                    # 建立关系
                    relationships_established.append(addition)

            # 保存更新后的Canvas
            CanvasJSONOperator.write_canvas(canvas_path, canvas_data)

            # 生成扩展结果
            expansion_result = {
                "network_expansion": {
                    "new_nodes_added": len(added_nodes),
                    "new_edges_added": len(added_edges),
                    "relationships_established": len(relationships_established),
                    "total_nodes": len(canvas_data.get("nodes", [])),
                    "total_edges": len(canvas_data.get("edges", []))
                },
                "added_nodes": added_nodes,
                "added_edges": added_edges,
                "relationships": relationships_established,
                "expansion_quality": self._evaluate_expansion_quality(canvas_data, user_additions)
            }

            if LOGURU_ENABLED:
                logger.info(f"Knowledge network expanded: {len(added_nodes)} nodes, {len(added_edges)} edges")

            return expansion_result

        except Exception as e:
            error_msg = f"Failed to expand knowledge network: {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg)
            return {"error": error_msg, "success": False}

    # 私有辅助方法

    def _create_learning_cycle_info(self) -> Dict[str, Any]:
        """创建学习循环信息"""
        return {
            "current_step": "step_1_understanding",
            "step_name": "填写理解",
            "step_description": "用户填写黄色理解节点，表达对概念的理解",
            "step_instructions": "请仔细阅读每个问题，用您自己的话认真回答。",
            "estimated_time_minutes": 15,
            "required_inputs": ["yellow_node_understanding"],
            "success_criteria": [
                "答案内容相关性>80%",
                "回答长度符合要求",
                "逻辑清晰表达"
            ]
        }

    def _create_network_expansion_info(self) -> Dict[str, Any]:
        """创建知识网络扩展信息"""
        return {
            "new_nodes_added_in_iteration": [],
            "relationships_established": [],
            "expansion_timestamp": datetime.now().isoformat()
        }

    def _create_progress_tracking_info(self) -> Dict[str, Any]:
        """创建进度跟踪信息"""
        return {
            "overall_progress": {
                "total_nodes": 0,
                "green_nodes": 0,
                "yellow_nodes": 0,
                "red_nodes": 0,
                "purple_nodes": 0,
                "completion_percentage": 0.0
            },
            "stopping_conditions": {
                "green_node_threshold": self.config["progress_tracking"]["green_node_threshold"],
                "iteration_limit": self.config["progress_tracking"]["iteration_limit"],
                "time_limit_hours": self.config["progress_tracking"]["time_limit_hours"],
                "user_satisfaction_threshold": 8.0
            },
            "current_status": {
                "meets_stopping_conditions": False,
                "recommended_action": "continue_iteration",
                "estimated_completion_iterations": 3
            },
            "learning_trends": {
                "mastery_improvement_rate": 0.15,
                "knowledge_expansion_rate": 0.25,
                "user_engagement_score": 8.5
            }
        }

    def _calculate_quality_metrics(self, questions: List[GeneratedQuestion], analysis: SourceAnalysis) -> Dict[str, float]:
        """计算质量指标"""
        if not questions:
            return {
                "question_relevance": 0.0,
                "difficulty_appropriateness": 0.0,
                "learning_effectiveness": 0.0,
                "user_satisfaction": 0.0,
                "knowledge_retention": 0.0
            }

        # 计算问题质量指标
        question_relevance = sum(q.quality_score for q in questions) / len(questions)
        difficulty_appropriateness = self._calculate_difficulty_appropriateness(questions, analysis)
        learning_effectiveness = self._calculate_learning_effectiveness(questions, analysis)

        # 模拟用户满意度（实际使用时应该从用户反馈收集）
        user_satisfaction = min(question_relevance * 10, 10.0)
        knowledge_retention = learning_effectiveness * 0.9  # 假设留存率略低于效果

        return {
            "question_relevance": round(question_relevance, 2),
            "difficulty_appropriateness": round(difficulty_appropriateness, 2),
            "learning_effectiveness": round(learning_effectiveness, 2),
            "user_satisfaction": round(user_satisfaction, 1),
            "knowledge_retention": round(knowledge_retention, 2)
        }

    def _calculate_difficulty_appropriateness(self, questions: List[GeneratedQuestion], analysis: SourceAnalysis) -> float:
        """计算难度适宜性"""
        if not questions or not analysis.critical_nodes_extracted:
            return 0.0

        # 计算平均掌握度
        avg_mastery = sum(node.mastery_estimation for node in analysis.critical_nodes_extracted) / len(analysis.critical_nodes_extracted)

        # 计算问题难度分布
        difficulty_scores = {"basic": 0.25, "intermediate": 0.5, "advanced": 0.75, "expert": 1.0}
        total_difficulty = 0.0
        for q in questions:
            # Handle both enum and string cases
            if hasattr(q.difficulty_level, 'value'):
                difficulty_value = q.difficulty_level.value
            else:
                difficulty_value = q.difficulty_level
            total_difficulty += difficulty_scores.get(difficulty_value, 0.5)

        avg_difficulty = total_difficulty / len(questions)

        # 理想情况下，问题难度应该略高于平均掌握度
        ideal_difficulty = min(avg_mastery + 0.1, 1.0)
        appropriateness = 1.0 - abs(avg_difficulty - ideal_difficulty)

        return max(0.0, appropriateness)

    def _calculate_learning_effectiveness(self, questions: List[GeneratedQuestion], analysis: SourceAnalysis) -> float:
        """计算学习效果"""
        if not questions:
            return 0.0

        # 基于问题质量、数量和多样性计算
        quality_score = sum(q.quality_score for q in questions) / len(questions)
        quantity_score = min(len(questions) / 10, 1.0)  # 10个问题为满分

        # 计算类型多样性 - handle both enum and string cases
        question_types = set()
        for q in questions:
            if hasattr(q.question_type, 'value'):
                question_types.add(q.question_type.value)
            else:
                question_types.add(q.question_type)

        diversity_score = min(len(question_types) / 5, 1.0)  # 5种类型为满分

        # 加权平均
        effectiveness = (quality_score * 0.5 + quantity_score * 0.2 + diversity_score * 0.3)

        return effectiveness

    def _create_user_interaction_data(self) -> Dict[str, Any]:
        """创建用户交互数据"""
        return {
            "time_spent_minutes": 0,
            "questions_answered": 0,
            "questions_skipped": 0,
            "hints_used": 0,
            "feedback_provided": False,
            "user_rating": 0.0
        }

    def _generate_ai_insights(self, analysis: SourceAnalysis, kg_context: KnowledgeGraphContext) -> Dict[str, Any]:
        """生成AI分析洞察"""
        return {
            "knowledge_gaps_identified": [
                {
                    "concept": node.concept_name,
                    "gap_severity": "high" if node.mastery_estimation < 0.3 else "medium",
                    "recommendation": "需要重点学习和练习"
                }
                for node in analysis.critical_nodes_extracted if node.mastery_estimation < 0.6
            ],
            "learning_pattern_analysis": {
                "preferred_approach": "visual_examples",
                "optimal_difficulty": "gradual_increase",
                "learning_pace": "steady_progress"
            },
            "next_recommendations": [
                "继续完成当前迭代的学习循环",
                "重点关注理解不足的概念",
                "适当增加练习和应用"
            ]
        }

    def _generate_canvas_file(self, dynamic_canvas: DynamicReviewCanvas, source_canvas: str, iteration: int) -> str:
        """生成Canvas文件"""
        # 确定输出路径
        source_path = Path(source_canvas)
        output_dir = source_path.parent / "review_canvases"

        # 处理Windows路径创建问题
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # 如果无法创建子目录，使用当前目录
            output_dir = source_path.parent
            if LOGURU_ENABLED:
                logger.warning(f"Could not create review_canvases directory, using parent: {e}")

        timestamp = datetime.now().strftime("%Y%m%d")
        canvas_filename = f"{source_path.stem}-检验白板-{timestamp}-iteration{iteration}.canvas"
        canvas_file_path = output_dir / canvas_filename

        # 创建Canvas数据结构
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 添加标题节点
        title_node = self._create_title_node(dynamic_canvas, iteration)
        canvas_data["nodes"].append(title_node)

        # 添加问题节点和对应的黄色理解节点
        current_x = self.layout_params["starting_x"]
        current_y = self.layout_params["starting_y"]

        for i, question in enumerate(dynamic_canvas.review_questions):
            # 问题节点
            question_node = self._create_question_node(question, current_x, current_y)
            canvas_data["nodes"].append(question_node)

            # 黄色理解节点（在问题下方）
            yellow_node = self._create_yellow_node(question, current_x, current_y + 180)
            canvas_data["nodes"].append(yellow_node)

            # 连接问题节点和黄色节点
            edge = self._create_edge(question_node["id"], yellow_node["id"])
            canvas_data["edges"].append(edge)

            # 更新位置
            current_x += self.layout_params["question_spacing_x"]
            if (i + 1) % 3 == 0:  # 每3个问题换行
                current_x = self.layout_params["starting_x"]
                current_y += self.layout_params["question_spacing_y"]

        # 保存Canvas文件
        with open(canvas_file_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)

        return str(canvas_file_path)

    def _create_title_node(self, dynamic_canvas: DynamicReviewCanvas, iteration: int) -> Dict[str, Any]:
        """创建标题节点"""
        source_name = Path(dynamic_canvas.source_canvas).stem
        return {
            "id": f"title-{uuid.uuid4().hex[:16]}",
            "type": "text",
            "text": f"# {source_name} - 检验白板 (第{iteration}轮迭代)\n\n"
                   f"生成时间: {dynamic_canvas.generation_timestamp[:19]}\n"
                   f"关键节点数量: {len(dynamic_canvas.review_questions)}\n"
                   f"当前步骤: {dynamic_canvas.learning_cycle_step}",
            "x": self.layout_params["starting_x"],
            "y": 50,
            "width": 600,
            "height": 120,
            "color": "5"  # 蓝色
        }

    def _create_question_node(self, question: GeneratedQuestion, x: int, y: int) -> Dict[str, Any]:
        """创建问题节点"""
        hint_text = f"\n\n💡 提示: {question.hint_text}" if question.hint_available else ""

        # Handle both enum and string cases for question_type and difficulty_level
        question_type_value = question.question_type.value if hasattr(question.question_type, 'value') else question.question_type
        difficulty_value = question.difficulty_level.value if hasattr(question.difficulty_level, 'value') else question.difficulty_level

        return {
            "id": question.question_id,
            "type": "text",
            "text": f"## 问题 {question.question_id[-4:]}\n\n"
                   f"{question.question_text}\n\n"
                   f"**类型**: {question_type_value}\n"
                   f"**难度**: {difficulty_value}\n"
                   f"**预计时间**: {question.estimated_time_minutes}分钟\n"
                   f"**质量分数**: {question.quality_score:.2f}"
                   f"{hint_text}",
            "x": x,
            "y": y,
            "width": 400,
            "height": 160,
            "color": "1"  # 红色（需要重点关注）
        }

    def _create_yellow_node(self, question: GeneratedQuestion, x: int, y: int) -> Dict[str, Any]:
        """创建黄色理解节点"""
        return {
            "id": f"yellow-{question.question_id[-16:]}",
            "type": "text",
            "text": f"## 我的理解\n\n"
                   f"请在此处填写您对上述问题的理解...\n\n"
                   f"**参考要求**:\n"
                   f"- 用自己的话解释\n"
                   f"- 可以举例子说明\n"
                   f"- 注明不确定的地方",
            "x": x + 50,
            "y": y,
            "width": 350,
            "height": 120,
            "color": "6"  # 黄色（用户理解输出区）
        }

    def _create_edge(self, from_node: str, to_node: str) -> Dict[str, Any]:
        """创建连接边"""
        return {
            "id": f"edge-{uuid.uuid4().hex[:16]}",
            "fromNode": from_node,
            "toNode": to_node,
            "fromSide": "bottom",
            "toSide": "top",
            "label": "理解输出"
        }

    def _save_canvas_metadata(self, dynamic_canvas: DynamicReviewCanvas, canvas_file_path: str):
        """保存Canvas元数据"""
        metadata_file = canvas_file_path.replace('.canvas', '_metadata.json')

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(dynamic_canvas.to_dict(), f, ensure_ascii=False, indent=2)

        if LOGURU_ENABLED:
            logger.info(f"Canvas metadata saved to {metadata_file}")

    def _check_stopping_conditions(self, quality_metrics: Dict) -> Dict[str, Any]:
        """检查停止条件"""
        completion_percentage = quality_metrics.get("completion_percentage", 0)
        mastery_level = quality_metrics.get("mastery_level", 0)
        needs_attention = quality_metrics.get("needs_attention", 100)

        threshold = self.config["progress_tracking"]["green_node_threshold"]

        return {
            "meets_threshold": completion_percentage >= threshold,
            "meets_mastery": mastery_level >= 90,
            "minimal_attention_needed": needs_attention <= 10,
            "overall_ready": completion_percentage >= threshold and mastery_level >= 80
        }

    def _generate_recommendations(self, quality_metrics: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        completion_percentage = quality_metrics.get("completion_percentage", 0)
        mastery_level = quality_metrics.get("mastery_level", 0)

        if completion_percentage < 60:
            recommendations.append("建议重点完成黄色理解节点的填写")
        elif completion_percentage < 80:
            recommendations.append("继续完善理解，争取更多节点达到绿色状态")

        if mastery_level < 50:
            recommendations.append("需要重新学习基础概念，建议补充相关解释")
        elif mastery_level < 80:
            recommendations.append("理解基本到位，可以通过练习巩固")

        if not recommendations:
            recommendations.append("学习进展良好，可以继续下一阶段学习")

        return recommendations

    def _add_user_node(self, canvas_data: Dict, addition: Dict) -> str:
        """添加用户节点"""
        node_id = f"user-node-{uuid.uuid4().hex[:16]}"
        node = {
            "id": node_id,
            "type": "text",
            "text": addition.get("content", ""),
            "x": addition.get("x", 100),
            "y": addition.get("y", 100),
            "width": addition.get("width", 400),
            "height": addition.get("height", 300),
            "color": addition.get("color", "6")  # 默认黄色
        }

        canvas_data.setdefault("nodes", []).append(node)
        return node_id

    def _add_user_edge(self, canvas_data: Dict, addition: Dict) -> str:
        """添加用户连接"""
        edge_id = f"user-edge-{uuid.uuid4().hex[:16]}"
        edge = {
            "id": edge_id,
            "fromNode": addition.get("from_node"),
            "toNode": addition.get("to_node"),
            "fromSide": addition.get("from_side", "right"),
            "toSide": addition.get("to_side", "left")
        }

        if addition.get("label"):
            edge["label"] = addition["label"]

        canvas_data.setdefault("edges", []).append(edge)
        return edge_id

    def _evaluate_expansion_quality(self, canvas_data: Dict, user_additions: List[Dict]) -> float:
        """评估扩展质量"""
        # 简化的质量评估
        nodes = canvas_data.get("nodes", [])
        edges = canvas_data.get("edges", [])

        # 计算连接密度
        if len(nodes) > 1:
            density = len(edges) / (len(nodes) * (len(nodes) - 1) / 2)
        else:
            density = 0

        # 计算内容质量（基于节点文本长度）
        avg_content_length = sum(len(node.get("text", "")) for node in nodes) / len(nodes) if nodes else 0
        content_quality = min(avg_content_length / 100, 1.0)

        # 综合质量分数
        quality_score = (density * 0.4 + content_quality * 0.6)

        return round(quality_score, 2)


# 便利函数
def create_dynamic_review_canvas(source_canvas: str, iteration: int = 1, user_profile: Optional[Dict] = None,
                               config_path: Optional[str] = None) -> str:
    """
    便利函数：创建动态检验白板

    Args:
        source_canvas: 源Canvas文件路径
        iteration: 迭代次数
        user_profile: 用户档案
        config_path: 配置文件路径

    Returns:
        str: 创建的检验白板文件路径
    """
    generator = DynamicReviewCanvasGenerator(config_path)
    return generator.create_review_canvas(source_canvas, iteration, user_profile)


if __name__ == "__main__":
    # 简单测试
    import sys
    if len(sys.argv) > 1:
        source_canvas = sys.argv[1]
        if os.path.exists(source_canvas):
            try:
                result = create_dynamic_review_canvas(source_canvas)
                print(f"Review canvas created: {result}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Source canvas not found: {source_canvas}")
    else:
        print("Usage: python dynamic_review_canvas_generator.py <source_canvas>")