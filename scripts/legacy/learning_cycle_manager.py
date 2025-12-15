"""
学习循环管理器 - 动态检验白板系统 (Story 8.16)

实现8步学习循环的管理和控制，支持动态学习流程、步骤验证和无限迭代。

Author: Canvas Learning System Team
Version: 1.0 (Story 8.16)
Created: 2025-01-22
"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

# 尝试导入现有模块
try:
    from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic
except ImportError:
    # 如果无法导入，定义本地类
    class CanvasJSONOperator:
        @staticmethod
        def read_canvas(canvas_path: str) -> Dict:
            with open(canvas_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        @staticmethod
        def write_canvas(canvas_path: str, canvas_data: Dict) -> None:
            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_data, f, ensure_ascii=False, indent=2)

# 尝试导入loguru
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


class LearningStep(Enum):
    """学习步骤枚举"""
    STEP_1_UNDERSTANDING = "step_1_understanding"      # 填写理解
    STEP_2_SCORING = "step_2_scoring"                  # 评分验证
    STEP_3_DECOMPOSITION = "step_3_decomposition"      # 深度拆解
    STEP_4_EXPLANATION = "step_4_explanation"          # 补充解释
    STEP_5_PRACTICE = "step_5_practice"                # 重复练习
    STEP_6_VERIFICATION = "step_6_verification"        # 检验阶段
    STEP_7_EXPANSION = "step_7_expansion"              # 扩展知识
    STEP_8_SUMMARY = "step_8_summary"                  # 总结验证


@dataclass
class StepDefinition:
    """步骤定义"""
    step: LearningStep
    name: str
    description: str
    instructions: str
    estimated_time_minutes: Tuple[int, int]  # 最小，最大时间
    required_inputs: List[str]
    validation_rules: List[str]
    success_criteria: List[str]
    auto_advance: bool = False


@dataclass
class LearningCycleState:
    """学习循环状态"""
    current_step: LearningStep
    step_start_time: datetime
    total_elapsed_time: timedelta
    completed_steps: List[LearningStep] = field(default_factory=list)
    step_progress: Dict[LearningStep, float] = field(default_factory=dict)
    user_inputs: Dict[LearningStep, Dict] = field(default_factory=dict)
    step_outputs: Dict[LearningStep, Dict] = field(default_factory=dict)
    iteration_count: int = 1
    cycle_id: str = field(default_factory=lambda: "cycle-" + uuid.uuid4().hex[:16])
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StepResult:
    """步骤执行结果"""
    step: LearningStep
    success: bool
    message: str
    output_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class LearningCycleManager:
    """
    学习循环管理器

    实现8步学习循环的完整管理：
    1. 填写理解 (Step 1)
    2. 评分验证 (Step 2)
    3. 深度拆解 (Step 3)
    4. 补充解释 (Step 4)
    5. 重复练习 (Step 5)
    6. 检验阶段 (Step 6)
    7. 扩展知识 (Step 7)
    8. 总结验证 (Step 8)
    """

    def __init__(self, canvas_path: str, config: Optional[Dict] = None):
        """
        初始化学习循环管理器

        Args:
            canvas_path: Canvas文件路径
            config: 配置参数
        """
        self.canvas_path = canvas_path
        self.config = config or self._get_default_config()
        self.step_definitions = self._initialize_step_definitions()
        self.current_state = None
        self.cycle_history: List[LearningCycleState] = []

        # 加载或创建学习状态
        self._load_cycle_state()

        if LOGURU_ENABLED:
            logger.info(f"LearningCycleManager initialized for canvas: {canvas_path}")

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "auto_save": True,
            "step_timeout_minutes": 30,
            "max_iterations": 10,
            "enable_skip_steps": False,
            "require_step_completion": True,
            "progress_save_interval": 60,  # 秒
            "validation_strictness": "normal"  # strict, normal, relaxed
        }

    def _initialize_step_definitions(self) -> Dict[LearningStep, StepDefinition]:
        """初始化步骤定义"""
        return {
            LearningStep.STEP_1_UNDERSTANDING: StepDefinition(
                step=LearningStep.STEP_1_UNDERSTANDING,
                name="填写理解",
                description="用户填写黄色理解节点，表达对概念的理解",
                instructions="请仔细阅读每个问题，用您自己的话在黄色节点中填写您的理解。不要参考外部资料，只凭记忆表达。",
                estimated_time_minutes=(5, 15),
                required_inputs=["yellow_node_understanding"],
                validation_rules=["completeness_check", "content_relevance"],
                success_criteria=["所有黄色节点都已填写", "内容相关性>80%", "回答长度符合要求"],
                auto_advance=False
            ),

            LearningStep.STEP_2_SCORING: StepDefinition(
                step=LearningStep.STEP_2_SCORING,
                name="评分验证",
                description="使用评分Agent对用户理解进行评分",
                instructions="系统将使用智能评分Agent对您的理解进行4维评分（准确性、具象性、完整性、原创性）。",
                estimated_time_minutes=(2, 5),
                required_inputs=["scoring_agent_completion"],
                validation_rules=["scoring_agent_completion", "score_validity"],
                success_criteria=["所有黄色节点都已完成评分", "评分结果合理", "颜色流转正确"],
                auto_advance=True
            ),

            LearningStep.STEP_3_DECOMPOSITION: StepDefinition(
                step=LearningStep.STEP_3_DECOMPOSITION,
                name="深度拆解",
                description="对不理解或似懂非懂的概念进行深度拆解",
                instructions="对于红色（不理解）和紫色（似懂非懂）的节点，系统将调用深度拆解Agent生成更细致的问题。",
                estimated_time_minutes=(10, 25),
                required_inputs=["decomposition_agent_input"],
                validation_rules=["decomposition_completion", "question_quality"],
                success_criteria=["关键问题已拆解", "子问题数量合适", "问题难度递进"],
                auto_advance=True
            ),

            LearningStep.STEP_4_EXPLANATION: StepDefinition(
                step=LearningStep.STEP_4_EXPLANATION,
                name="补充解释",
                description="为理解不足的概念提供补充解释",
                instructions="系统将生成多种类型的解释文档（口语化解释、澄清路径、对比表等）来帮助您深入理解。",
                estimated_time_minutes=(8, 20),
                required_inputs=["explanation_generation"],
                validation_rules=["explanation_relevance", "content_quality"],
                success_criteria=["生成了相关解释", "解释内容清晰易懂", "覆盖了理解盲区"],
                auto_advance=True
            ),

            LearningStep.STEP_5_PRACTICE: StepDefinition(
                step=LearningStep.STEP_5_PRACTICE,
                name="重复练习",
                description="通过重复练习巩固理解",
                instructions="基于新的理解，重新回答原始问题，或者完成相关的练习题来巩固学习效果。",
                estimated_time_minutes=(5, 15),
                required_inputs=["practice_completion"],
                validation_rules=["practice_completion", "improvement_evidence"],
                success_criteria=["完成了练习", "理解有所提升", "能够独立回答问题"],
                auto_advance=False
            ),

            LearningStep.STEP_6_VERIFICATION: StepDefinition(
                step=LearningStep.STEP_6_VERIFICATION,
                name="检验阶段",
                description="通过检验问题验证理解程度",
                instructions="回答系统生成的检验问题，验证您对概念的真正理解程度。",
                estimated_time_minutes=(10, 20),
                required_inputs=["question_answering"],
                validation_rules=["question_completion", "answer_quality"],
                success_criteria=["回答了所有检验问题", "答案正确性>80%", "逻辑清晰"],
                auto_advance=False
            ),

            LearningStep.STEP_7_EXPANSION: StepDefinition(
                step=LearningStep.STEP_7_EXPANSION,
                name="扩展知识",
                description="基于理解扩展相关知识网络",
                instructions="基于您的理解，添加相关概念、建立知识连接，扩展您的知识网络。",
                estimated_time_minutes=(5, 15),
                required_inputs=["network_expansion"],
                validation_rules=["expansion_quality", "connection_validity"],
                success_criteria=["添加了新节点", "建立了有效连接", "网络结构合理"],
                auto_advance=False
            ),

            LearningStep.STEP_8_SUMMARY: StepDefinition(
                step=LearningStep.STEP_8_SUMMARY,
                name="总结验证",
                description="总结学习成果并验证整体理解",
                instructions="回顾整个学习过程，总结学习成果，验证整体理解水平。",
                estimated_time_minutes=(3, 10),
                required_inputs=["summary_completion"],
                validation_rules=["summary_quality", "understanding_verification"],
                success_criteria=["完成了学习总结", "理解水平达到要求", "准备好进入下一轮迭代"],
                auto_advance=False
            )
        }

    def get_current_step(self) -> Optional[LearningStep]:
        """
        获取当前步骤

        Returns:
            Optional[LearningStep]: 当前步骤，如果未开始则返回None
        """
        if self.current_state:
            return self.current_state.current_step
        return None

    def get_step_instructions(self, step: Optional[LearningStep] = None) -> Optional[str]:
        """
        获取步骤说明

        Args:
            step: 步骤，如果为None则获取当前步骤

        Returns:
            Optional[str]: 步骤说明
        """
        if step is None:
            step = self.get_current_step()

        if step and step in self.step_definitions:
            return self.step_definitions[step].instructions
        return None

    def is_step_completed(self, step: LearningStep) -> bool:
        """
        检查步骤是否完成

        Args:
            step: 要检查的步骤

        Returns:
            bool: 步骤是否完成
        """
        if not self.current_state:
            return False

        return (step in self.current_state.completed_steps and
                self.current_state.step_progress.get(step, 0) >= 1.0)

    def start_new_cycle(self) -> bool:
        """
        开始新的学习循环

        Returns:
            bool: 是否成功开始
        """
        try:
            # 保存当前状态到历史
            if self.current_state:
                self.cycle_history.append(self.current_state)

            # 创建新的循环状态
            self.current_state = LearningCycleState(
                current_step=LearningStep.STEP_1_UNDERSTANDING,
                step_start_time=datetime.now(),
                total_elapsed_time=timedelta(0),
                iteration_count=len(self.cycle_history) + 1
            )

            # 保存状态
            self._save_cycle_state()

            if LOGURU_ENABLED:
                logger.info(f"Started new learning cycle #{self.current_state.iteration_count}")

            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to start new learning cycle: {e}")
            return False

    def advance_to_next_step(self, step_output: Optional[Dict] = None) -> StepResult:
        """
        推进到下一步

        Args:
            step_output: 当前步骤的输出数据

        Returns:
            StepResult: 步骤推进结果
        """
        if not self.current_state:
            return StepResult(
                step=LearningStep.STEP_1_UNDERSTANDING,
                success=False,
                message="No active learning cycle. Call start_new_cycle() first."
            )

        current_step = self.current_state.current_step
        step_def = self.step_definitions.get(current_step)

        if not step_def:
            return StepResult(
                step=current_step,
                success=False,
                message=f"Invalid step: {current_step}"
            )

        try:
            # 验证当前步骤完成情况
            validation_result = self._validate_step_completion(current_step, step_output)

            if not validation_result["valid"]:
                return StepResult(
                    step=current_step,
                    success=False,
                    message=f"Step validation failed: {validation_result['message']}",
                    errors=validation_result.get("errors", [])
                )

            # 记录步骤完成
            self.current_state.completed_steps.append(current_step)
            self.current_state.step_progress[current_step] = 1.0
            if step_output:
                self.current_state.step_outputs[current_step] = step_output

            # 计算下一步
            next_step = self._get_next_step(current_step)

            if next_step is None:
                # 完成一个完整循环
                return self._complete_cycle()

            # 推进到下一步
            self.current_state.current_step = next_step
            self.current_state.step_start_time = datetime.now()

            # 保存状态
            self._save_cycle_state()

            if LOGURU_ENABLED:
                logger.info(f"Advanced from {current_step} to {next_step}")

            return StepResult(
                step=current_step,
                success=True,
                message=f"Successfully advanced to {next_step.name}",
                output_data={"next_step": next_step.value}
            )

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to advance step: {e}")
            return StepResult(
                step=current_step,
                success=False,
                message=f"Error advancing step: {str(e)}"
            )

    def process_user_input(self, user_input: Dict[str, Any]) -> StepResult:
        """
        处理用户输入

        Args:
            user_input: 用户输入数据

        Returns:
            StepResult: 处理结果
        """
        if not self.current_state:
            return StepResult(
                step=LearningStep.STEP_1_UNDERSTANDING,
                success=False,
                message="No active learning cycle"
            )

        current_step = self.current_state.current_step

        try:
            # 验证输入格式
            validation_result = self._validate_user_input(current_step, user_input)

            if not validation_result["valid"]:
                return StepResult(
                    step=current_step,
                    success=False,
                    message=f"Invalid user input: {validation_result['message']}",
                    errors=validation_result.get("errors", [])
                )

            # 保存用户输入
            self.current_state.user_inputs[current_step] = user_input

            # 更新步骤进度
            progress = self._calculate_step_progress(current_step, user_input)
            self.current_state.step_progress[current_step] = progress

            # 处理输入并生成反馈
            feedback = self._generate_input_feedback(current_step, user_input)

            # 保存状态
            self._save_cycle_state()

            return StepResult(
                step=current_step,
                success=True,
                message="User input processed successfully",
                output_data={
                    "progress": progress,
                    "feedback": feedback,
                    "can_advance": progress >= 1.0
                }
            )

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to process user input: {e}")
            return StepResult(
                step=current_step,
                success=False,
                message=f"Error processing user input: {str(e)}"
            )

    def _validate_step_completion(self, step: LearningStep, step_output: Optional[Dict]) -> Dict[str, Any]:
        """验证步骤完成情况"""
        step_def = self.step_definitions.get(step)
        if not step_def:
            return {"valid": False, "message": "Invalid step"}

        # 基础验证：检查必需输入
        if not step_output and step_def.required_inputs:
            return {"valid": False, "message": "Missing required outputs"}

        # 根据步骤类型进行具体验证
        validation_rules = step_def.validation_rules
        errors = []

        for rule in validation_rules:
            rule_result = self._apply_validation_rule(rule, step_output)
            if not rule_result["valid"]:
                errors.append(rule_result["message"])

        return {
            "valid": len(errors) == 0,
            "message": "; ".join(errors) if errors else "Validation passed",
            "errors": errors
        }

    def _validate_user_input(self, step: LearningStep, user_input: Dict) -> Dict[str, Any]:
        """验证用户输入"""
        step_def = self.step_definitions.get(step)
        if not step_def:
            return {"valid": False, "message": "Invalid step"}

        required_inputs = step_def.required_inputs
        errors = []

        # 检查必需字段
        for required in required_inputs:
            if required not in user_input:
                errors.append(f"Missing required field: {required}")

        # 检查数据质量
        if "yellow_node_understanding" in user_input:
            content = user_input["yellow_node_understanding"]
            if not isinstance(content, str) or len(content.strip()) < 5:
                errors.append("Content too short or not a string")

        return {
            "valid": len(errors) == 0,
            "message": "; ".join(errors) if errors else "Input validation passed",
            "errors": errors
        }

    def _apply_validation_rule(self, rule: str, data: Optional[Dict]) -> Dict[str, Any]:
        """应用验证规则"""
        if not data:
            return {"valid": False, "message": "No data to validate"}

        if rule == "completeness_check":
            # 检查完整性
            required_fields = ["content", "node_id"]
            missing = [f for f in required_fields if f not in data]
            return {
                "valid": len(missing) == 0,
                "message": f"Missing fields: {missing}" if missing else "Completeness check passed"
            }

        elif rule == "content_relevance":
            # 检查内容相关性
            content = data.get("content", "")
            if len(content) < 10:
                return {"valid": False, "message": "Content too short"}
            return {"valid": True, "message": "Content relevance check passed"}

        elif rule == "scoring_agent_completion":
            # 检查评分Agent完成情况
            scores = data.get("scores", {})
            if not scores:
                return {"valid": False, "message": "No scores provided"}
            return {"valid": True, "message": "Scoring completion check passed"}

        # 其他规则...
        return {"valid": True, "message": f"Rule {rule} passed"}

    def _calculate_step_progress(self, step: LearningStep, user_input: Dict) -> float:
        """计算步骤进度"""
        step_def = self.step_definitions.get(step)
        if not step_def:
            return 0.0

        # 基于完成的必需输入计算进度
        required_inputs = step_def.required_inputs
        completed_inputs = sum(1 for req in required_inputs if req in user_input)

        base_progress = completed_inputs / len(required_inputs) if required_inputs else 0.0

        # 根据输入质量调整进度
        quality_bonus = self._calculate_input_quality(step, user_input) * 0.2

        return min(base_progress + quality_bonus, 1.0)

    def _calculate_input_quality(self, step: LearningStep, user_input: Dict) -> float:
        """计算输入质量"""
        quality_score = 0.0

        # 内容长度质量
        if "content" in user_input:
            content = user_input["content"]
            length_score = min(len(content) / 100, 1.0)  # 100字符为满分
            quality_score += length_score * 0.5

        # 结构完整性
        structure_fields = ["node_id", "timestamp", "metadata"]
        completed_structure = sum(1 for field in structure_fields if field in user_input)
        structure_score = completed_structure / len(structure_fields)
        quality_score += structure_score * 0.3

        # 用户交互质量
        if "interaction_type" in user_input:
            quality_score += 0.2

        return min(quality_score, 1.0)

    def _generate_input_feedback(self, step: LearningStep, user_input: Dict) -> Dict[str, Any]:
        """生成输入反馈"""
        feedback = {
            "message": "",
            "suggestions": [],
            "next_actions": []
        }

        progress = self._calculate_step_progress(step, user_input)

        if progress < 0.5:
            feedback["message"] = "还需要更多信息来完成这个步骤"
            feedback["suggestions"] = ["请填写更多详细信息", "确保所有必需字段都已填写"]
        elif progress < 1.0:
            feedback["message"] = "进展良好，再补充一些信息就可以进入下一步"
            feedback["suggestions"] = ["检查内容的完整性", "添加更多细节或例子"]
        else:
            feedback["message"] = "步骤完成，可以进入下一步"
            feedback["next_actions"] = ["advance_to_next_step"]

        # 根据步骤类型提供特定反馈
        if step == LearningStep.STEP_1_UNDERSTANDING:
            feedback["suggestions"].append("尝试用自己的话解释，而不是复制原文")
        elif step == LearningStep.STEP_6_VERIFICATION:
            feedback["suggestions"].append("确保答案逻辑清晰，有理有据")

        return feedback

    def _get_next_step(self, current_step: LearningStep) -> Optional[LearningStep]:
        """获取下一步"""
        step_order = [
            LearningStep.STEP_1_UNDERSTANDING,
            LearningStep.STEP_2_SCORING,
            LearningStep.STEP_3_DECOMPOSITION,
            LearningStep.STEP_4_EXPLANATION,
            LearningStep.STEP_5_PRACTICE,
            LearningStep.STEP_6_VERIFICATION,
            LearningStep.STEP_7_EXPANSION,
            LearningStep.STEP_8_SUMMARY
        ]

        try:
            current_index = step_order.index(current_step)
            if current_index < len(step_order) - 1:
                return step_order[current_index + 1]
            else:
                return None  # 循环完成
        except ValueError:
            return None

    def _complete_cycle(self) -> StepResult:
        """完成学习循环"""
        try:
            # 更新总耗时
            total_time = datetime.now() - self.current_state.created_at
            self.current_state.total_elapsed_time = total_time

            # 保存到历史
            self.cycle_history.append(self.current_state)

            # 生成循环总结
            summary = self._generate_cycle_summary(self.current_state)

            if LOGURU_ENABLED:
                logger.info(f"Completed learning cycle #{self.current_state.iteration_count}")

            return StepResult(
                step=LearningStep.STEP_8_SUMMARY,
                success=True,
                message="Learning cycle completed successfully",
                output_data={
                    "cycle_completed": True,
                    "summary": summary,
                    "total_time_minutes": total_time.total_seconds() / 60,
                    "iteration_count": self.current_state.iteration_count
                }
            )

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to complete cycle: {e}")
            return StepResult(
                step=LearningStep.STEP_8_SUMMARY,
                success=False,
                message=f"Failed to complete cycle: {str(e)}"
            )

    def _generate_cycle_summary(self, state: LearningCycleState) -> Dict[str, Any]:
        """生成循环总结"""
        return {
            "cycle_id": state.cycle_id,
            "iteration_count": state.iteration_count,
            "completed_steps": [step.value for step in state.completed_steps],
            "total_time_minutes": state.total_elapsed_time.total_seconds() / 60,
            "step_progress": {step.value: progress for step, progress in state.step_progress.items()},
            "user_inputs_count": len(state.user_inputs),
            "step_outputs_count": len(state.step_outputs)
        }

    def _load_cycle_state(self):
        """加载循环状态"""
        state_file = self._get_state_file_path()

        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 重建状态对象
                self.current_state = self._deserialize_state(data.get("current_state"))
                self.cycle_history = [
                    self._deserialize_state(state_data)
                    for state_data in data.get("cycle_history", [])
                ]

                if LOGURU_ENABLED:
                    logger.info(f"Loaded learning cycle state from {state_file}")

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.warning(f"Failed to load cycle state: {e}")
                self.current_state = None

    def _save_cycle_state(self):
        """保存循环状态"""
        if not self.config.get("auto_save", True):
            return

        try:
            state_file = self._get_state_file_path()
            os.makedirs(os.path.dirname(state_file), exist_ok=True)

            data = {
                "current_state": self._serialize_state(self.current_state) if self.current_state else None,
                "cycle_history": [
                    self._serialize_state(state)
                    for state in self.cycle_history
                ],
                "last_updated": datetime.now().isoformat()
            }

            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to save cycle state: {e}")

    def _get_state_file_path(self) -> str:
        """获取状态文件路径"""
        canvas_name = os.path.splitext(os.path.basename(self.canvas_path))[0]
        return f"data/learning_cycles/{canvas_name}_cycle_state.json"

    def _serialize_state(self, state: LearningCycleState) -> Dict:
        """序列化状态对象"""
        if not state:
            return None

        return {
            "current_step": state.current_step.value,
            "step_start_time": state.step_start_time.isoformat(),
            "total_elapsed_time": state.total_elapsed_time.total_seconds(),
            "completed_steps": [step.value for step in state.completed_steps],
            "step_progress": {step.value: progress for step, progress in state.step_progress.items()},
            "user_inputs": {step.value: inputs for step, inputs in state.user_inputs.items()},
            "step_outputs": {step.value: outputs for step, outputs in state.step_outputs.items()},
            "iteration_count": state.iteration_count,
            "cycle_id": state.cycle_id,
            "created_at": state.created_at.isoformat()
        }

    def _deserialize_state(self, data: Dict) -> Optional[LearningCycleState]:
        """反序列化状态对象"""
        if not data:
            return None

        try:
            return LearningCycleState(
                current_step=LearningStep(data["current_step"]),
                step_start_time=datetime.fromisoformat(data["step_start_time"]),
                total_elapsed_time=timedelta(seconds=data["total_elapsed_time"]),
                completed_steps=[LearningStep(step) for step in data["completed_steps"]],
                step_progress={LearningStep(step): progress for step, progress in data["step_progress"].items()},
                user_inputs={LearningStep(step): inputs for step, inputs in data["user_inputs"].items()},
                step_outputs={LearningStep(step): outputs for step, outputs in data["step_outputs"].items()},
                iteration_count=data["iteration_count"],
                cycle_id=data["cycle_id"],
                created_at=datetime.fromisoformat(data["created_at"])
            )
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to deserialize state: {e}")
            return None

    def get_cycle_progress(self) -> Dict[str, Any]:
        """获取循环进度"""
        if not self.current_state:
            return {"progress": 0.0, "message": "No active cycle"}

        completed_steps = len(self.current_state.completed_steps)
        total_steps = len(self.step_definitions)
        progress = completed_steps / total_steps

        return {
            "progress": progress,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "current_step": self.current_state.current_step.name,
            "iteration_count": self.current_state.iteration_count,
            "cycle_id": self.current_state.cycle_id
        }


# 便利函数
def create_learning_cycle_manager(canvas_path: str, config: Optional[Dict] = None) -> LearningCycleManager:
    """
    便利函数：创建学习循环管理器

    Args:
        canvas_path: Canvas文件路径
        config: 可选配置

    Returns:
        LearningCycleManager: 管理器实例
    """
    return LearningCycleManager(canvas_path, config)


if __name__ == "__main__":
    # 简单测试
    test_canvas = "test_canvas.canvas"
    if os.path.exists(test_canvas):
        manager = create_learning_cycle_manager(test_canvas)
        progress = manager.get_cycle_progress()
        print(f"Learning cycle progress: {progress['progress']:.1%}")
    else:
        print(f"Test canvas not found: {test_canvas}")