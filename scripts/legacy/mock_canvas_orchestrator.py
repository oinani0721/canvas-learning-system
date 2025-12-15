"""
Canvas Orchestrator Mock - Story 8.14测试用
用于解决canvas_utils.py依赖问题，使并行Agent处理系统能够独立测试
"""

import asyncio
from typing import Dict, List, Any, Optional


class MockCanvasOrchestrator:
    """模拟Canvas Orchestrator - 专门用于Story 8.14并行处理测试"""

    def __init__(self):
        """初始化模拟Orchestrator"""
        self.agent_registry = {
            "basic-decomposition": self._mock_basic_decomposition,
            "oral-explanation": self._mock_oral_explanation,
            "scoring-agent": self._mock_scoring_agent,
            "deep-decomposition": self._mock_deep_decomposition,
            "clarification-path": self._mock_clarification_path,
            "comparison-table": self._mock_comparison_table,
            "memory-anchor": self._mock_memory_anchor,
            "four-level-explanation": self._mock_four_level_explanation,
            "example-teaching": self._mock_example_teaching,
            "verification-question-agent": self._mock_verification_questions
        }

    async def execute_agent_task(self, agent_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行Agent任务的统一接口"""
        if agent_name not in self.agent_registry:
            return {
                "success": False,
                "error": f"未知Agent类型: {agent_name}",
                "result": None
            }

        try:
            # 模拟Agent执行时间
            await asyncio.sleep(0.1 + len(str(task_data)) * 0.001)  # 根据任务复杂度模拟不同执行时间

            result = await self.agent_registry[agent_name](task_data)
            return {
                "success": True,
                "result": result,
                "execution_time": 0.1 + len(str(task_data)) * 0.001,
                "agent_name": agent_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    async def _mock_basic_decomposition(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟基础拆解Agent"""
        material = task_data.get("material_text", "默认材料")
        return {
            "sub_questions": [
                {"text": f"关于'{material}'的基本定义是什么？", "type": "definition_type"},
                {"text": f"能否举一个'{material}'的具体例子？", "type": "example_type"},
                {"text": f"'{material}'与其他相关概念有什么区别？", "type": "comparison_type"}
            ],
            "total_count": 3,
            "has_guidance": True
        }

    async def _mock_oral_explanation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟口语化解释Agent"""
        concept = task_data.get("concept", "默认概念")
        return {
            "explanation": f"大家好，今天我们来讲解'{concept}'这个概念。这是一个非常重要的知识点...",
            "word_count": 1200,
            "style": "oral_professor"
        }

    async def _mock_scoring_agent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟评分Agent"""
        understanding = task_data.get("user_understanding", "用户理解")
        return {
            "accuracy_score": 85,
            "imagery_score": 78,
            "completeness_score": 82,
            "originality_score": 88,
            "total_score": 83,
            "color_transition": "green",
            "feedback": f"对'{understanding}'的理解总体良好，建议在具象化方面进一步提升"
        }

    async def _mock_deep_decomposition(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟深度拆解Agent"""
        concept = task_data.get("concept", "默认概念")
        return {
            "deep_questions": [
                {"text": f"'{concept}'的本质特征是什么？", "type": "essential_type"},
                {"text": f"'{concept}'在不同情境下如何变化？", "type": "contextual_type"},
                {"text": f"如何将'{concept}'应用到实际问题中？", "type": "application_type"}
            ],
            "difficulty_level": "advanced",
            "cognitive_depth": "high"
        }

    async def _mock_clarification_path(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟澄清路径Agent"""
        concept = task_data.get("concept", "默认概念")
        return {
            "clarification_steps": [
                {"step": 1, "content": f"首先明确'{concept}'的基本含义"},
                {"step": 2, "content": f"然后分析'{concept}'的关键特征"},
                {"step": 3, "content": f"最后探讨'{concept}'的实际应用"}
            ],
            "total_words": 1500
        }

    async def _mock_comparison_table(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟对比表Agent"""
        concepts = task_data.get("concepts", ["概念A", "概念B"])
        return {
            "comparison_table": {
                "定义": [f"{concepts[0]}的定义", f"{concepts[1]}的定义"],
                "特征": [f"{concepts[0]}的特征", f"{concepts[1]}的特征"],
                "应用场景": [f"{concepts[0]}的应用", f"{concepts[1]}的应用"]
            }
        }

    async def _mock_memory_anchor(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟记忆锚点Agent"""
        concept = task_data.get("concept", "默认概念")
        return {
            "memory_anchor": f"想象'{concept}'就像一座灯塔，为你的学习指引方向...",
            "anchor_type": "visual_metaphor",
            "memorability_score": 90
        }

    async def _mock_four_level_explanation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟四层次解释Agent"""
        concept = task_data.get("concept", "默认概念")
        return {
            "levels": {
                "新手": f"'{concept}'是最基础的概念...",
                "进阶": f"深入理解'{concept}'需要掌握...",
                "专家": f"从专业角度看，'{concept}'涉及...",
                "创新": f"基于'{concept}'，我们可以发展出..."
            },
            "total_words": 1400
        }

    async def _mock_example_teaching(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟例题教学Agent"""
        concept = task_data.get("concept", "默认概念")
        return {
            "example_problem": f"关于'{concept}'的经典例题",
            "solution_steps": [
                "第一步：分析题目要求",
                "第二步：应用相关原理",
                "第三步：详细计算过程",
                "第四步：验证结果"
            ],
            "difficulty": "medium"
        }

    async def _mock_verification_questions(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟检验问题生成Agent"""
        concept = task_data.get("concept", "默认概念")
        return {
            "verification_questions": [
                {"text": f"请用自己的话解释什么是'{concept}'？", "type": "understanding_check"},
                {"text": f"如何判断你真正理解了'{concept}'？", "type": "meta_cognition"}
            ],
            "question_count": 2
        }


# 创建全局实例
mock_orchestrator = MockCanvasOrchestrator()