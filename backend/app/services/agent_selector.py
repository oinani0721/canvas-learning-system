"""
Agent Selector Service - 动态Agent选择器

Epic 24: Verification Canvas Redesign (智能引导模式)
Story 24.4: Dynamic Agent Selection

根据用户回答质量和概念类型，动态选择最合适的引导Agent。

✅ Verified from backend/app/services/agent_service.py (项目现有模式):
- 使用Enum定义AgentType
- 异步方法设计
- 单例模式获取服务

Selection Matrix:
| Answer Quality      | Concept Type | Selected Agent      |
|---------------------|--------------|---------------------|
| Partially Correct   | Any          | memory-anchor       |
| Wrong               | Abstract     | example-teaching    |
| Confused            | Similar      | comparison-table    |
| No Idea             | Complex      | basic-decomposition |
| Reasoning Error     | Proof        | clarification-path  |

Story 24.4 AC:
- ✅ AC 1: 创建 AgentSelector 类
- ✅ AC 2: 实现选择矩阵
- ✅ AC 3: 支持5种Agent类型

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-13
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AnswerQuality(str, Enum):
    """回答质量等级"""
    EXCELLENT = "excellent"       # 完全正确，深刻理解
    GOOD = "good"                 # 基本正确，理解到位
    PARTIAL = "partial"           # 部分正确，有遗漏
    WRONG = "wrong"               # 完全错误
    CONFUSED = "confused"         # 概念混淆
    NO_IDEA = "no_idea"           # 完全不知道
    REASONING_ERROR = "reasoning_error"  # 推理错误
    SKIPPED = "skipped"           # 跳过


class ConceptType(str, Enum):
    """概念类型"""
    DEFINITION = "definition"     # 定义类概念
    ABSTRACT = "abstract"         # 抽象概念
    SIMILAR = "similar"           # 易混淆概念
    COMPLEX = "complex"           # 复杂概念
    PROOF = "proof"               # 证明/推导
    APPLICATION = "application"   # 应用类概念
    COMPARISON = "comparison"     # 对比类概念


class GuidanceAgent(str, Enum):
    """引导Agent类型

    ✅ Verified from project agents:
    - memory-anchor: 记忆锚点，生成类比和故事
    - example-teaching: 例题教学，完整解题过程
    - comparison-table: 对比表格，区分易混概念
    - basic-decomposition: 基础拆解，分解难点
    - clarification-path: 澄清路径，系统性解释
    """
    MEMORY_ANCHOR = "memory-anchor"
    EXAMPLE_TEACHING = "example-teaching"
    COMPARISON_TABLE = "comparison-table"
    BASIC_DECOMPOSITION = "basic-decomposition"
    CLARIFICATION_PATH = "clarification-path"


@dataclass
class SelectionContext:
    """选择上下文

    包含做出Agent选择所需的所有信息。
    """
    answer_quality: AnswerQuality
    answer_score: float
    concept_text: str
    concept_type: Optional[ConceptType] = None
    hints_given: int = 0
    previous_agents: List[str] = None
    rag_context: Optional[str] = None

    def __post_init__(self):
        if self.previous_agents is None:
            self.previous_agents = []


@dataclass
class SelectionResult:
    """选择结果

    包含选中的Agent及选择原因。
    """
    agent: GuidanceAgent
    reason: str
    confidence: float  # 0.0 - 1.0
    fallback_agent: Optional[GuidanceAgent] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent": self.agent.value,
            "reason": self.reason,
            "confidence": round(self.confidence, 2),
            "fallback_agent": self.fallback_agent.value if self.fallback_agent else None,
        }


class AgentSelector:
    """
    动态Agent选择器

    根据用户回答质量和概念类型，选择最合适的引导Agent。

    主要方法:
    - select_agent(): 选择最佳Agent
    - get_selection_reason(): 获取选择理由
    - analyze_concept_type(): 分析概念类型

    使用示例:
    ```python
    selector = get_agent_selector()
    context = SelectionContext(
        answer_quality=AnswerQuality.PARTIAL,
        answer_score=55.0,
        concept_text="逆否命题"
    )
    result = await selector.select_agent(context)
    print(f"Selected: {result.agent}, Reason: {result.reason}")
    ```
    """

    # ═══════════════════════════════════════════════════════════════════════════════
    # 选择规则矩阵
    # ═══════════════════════════════════════════════════════════════════════════════

    # 基于回答质量的默认选择
    QUALITY_DEFAULT_MAP: Dict[AnswerQuality, GuidanceAgent] = {
        AnswerQuality.EXCELLENT: GuidanceAgent.MEMORY_ANCHOR,  # 加深记忆
        AnswerQuality.GOOD: GuidanceAgent.EXAMPLE_TEACHING,    # 巩固练习
        AnswerQuality.PARTIAL: GuidanceAgent.MEMORY_ANCHOR,    # 补充理解
        AnswerQuality.WRONG: GuidanceAgent.EXAMPLE_TEACHING,   # 重新学习
        AnswerQuality.CONFUSED: GuidanceAgent.COMPARISON_TABLE,  # 区分概念
        AnswerQuality.NO_IDEA: GuidanceAgent.BASIC_DECOMPOSITION,  # 从头拆解
        AnswerQuality.REASONING_ERROR: GuidanceAgent.CLARIFICATION_PATH,  # 澄清思路
        AnswerQuality.SKIPPED: GuidanceAgent.BASIC_DECOMPOSITION,  # 基础开始
    }

    # 基于(质量, 概念类型)的精确选择
    QUALITY_CONCEPT_MAP: Dict[Tuple[AnswerQuality, ConceptType], GuidanceAgent] = {
        # 部分正确场景
        (AnswerQuality.PARTIAL, ConceptType.DEFINITION): GuidanceAgent.MEMORY_ANCHOR,
        (AnswerQuality.PARTIAL, ConceptType.ABSTRACT): GuidanceAgent.MEMORY_ANCHOR,
        (AnswerQuality.PARTIAL, ConceptType.COMPLEX): GuidanceAgent.BASIC_DECOMPOSITION,

        # 错误场景
        (AnswerQuality.WRONG, ConceptType.ABSTRACT): GuidanceAgent.EXAMPLE_TEACHING,
        (AnswerQuality.WRONG, ConceptType.DEFINITION): GuidanceAgent.CLARIFICATION_PATH,
        (AnswerQuality.WRONG, ConceptType.APPLICATION): GuidanceAgent.EXAMPLE_TEACHING,

        # 混淆场景
        (AnswerQuality.CONFUSED, ConceptType.SIMILAR): GuidanceAgent.COMPARISON_TABLE,
        (AnswerQuality.CONFUSED, ConceptType.COMPARISON): GuidanceAgent.COMPARISON_TABLE,
        (AnswerQuality.CONFUSED, ConceptType.DEFINITION): GuidanceAgent.COMPARISON_TABLE,

        # 完全不知场景
        (AnswerQuality.NO_IDEA, ConceptType.COMPLEX): GuidanceAgent.BASIC_DECOMPOSITION,
        (AnswerQuality.NO_IDEA, ConceptType.ABSTRACT): GuidanceAgent.BASIC_DECOMPOSITION,
        (AnswerQuality.NO_IDEA, ConceptType.PROOF): GuidanceAgent.BASIC_DECOMPOSITION,

        # 推理错误场景
        (AnswerQuality.REASONING_ERROR, ConceptType.PROOF): GuidanceAgent.CLARIFICATION_PATH,
        (AnswerQuality.REASONING_ERROR, ConceptType.APPLICATION): GuidanceAgent.EXAMPLE_TEACHING,
        (AnswerQuality.REASONING_ERROR, ConceptType.COMPLEX): GuidanceAgent.CLARIFICATION_PATH,
    }

    def __init__(self):
        """初始化选择器"""
        logger.info("AgentSelector initialized")

    async def select_agent(self, context: SelectionContext) -> SelectionResult:
        """
        选择最合适的引导Agent

        Args:
            context: 选择上下文

        Returns:
            SelectionResult: 包含选中Agent和选择理由
        """
        logger.debug(f"Selecting agent for quality={context.answer_quality}, "
                    f"concept_type={context.concept_type}")

        # 1. 尝试精确匹配 (质量 + 概念类型)
        if context.concept_type:
            key = (context.answer_quality, context.concept_type)
            if key in self.QUALITY_CONCEPT_MAP:
                agent = self.QUALITY_CONCEPT_MAP[key]
                return SelectionResult(
                    agent=agent,
                    reason=f"基于回答质量({context.answer_quality.value})和概念类型({context.concept_type.value})精确匹配",
                    confidence=0.95,
                    fallback_agent=self._get_fallback(agent, context),
                )

        # 2. 基于回答质量的默认选择
        if context.answer_quality in self.QUALITY_DEFAULT_MAP:
            agent = self.QUALITY_DEFAULT_MAP[context.answer_quality]
            return SelectionResult(
                agent=agent,
                reason=f"基于回答质量({context.answer_quality.value})的默认选择",
                confidence=0.75,
                fallback_agent=self._get_fallback(agent, context),
            )

        # 3. 兜底选择
        return SelectionResult(
            agent=GuidanceAgent.BASIC_DECOMPOSITION,
            reason="默认兜底选择",
            confidence=0.5,
            fallback_agent=GuidanceAgent.CLARIFICATION_PATH,
        )

    def _get_fallback(
        self,
        primary: GuidanceAgent,
        context: SelectionContext
    ) -> Optional[GuidanceAgent]:
        """获取备选Agent"""
        # 排除主选和已使用的Agent
        used = set(context.previous_agents) | {primary.value}

        # 优先级顺序
        priority = [
            GuidanceAgent.MEMORY_ANCHOR,
            GuidanceAgent.EXAMPLE_TEACHING,
            GuidanceAgent.COMPARISON_TABLE,
            GuidanceAgent.BASIC_DECOMPOSITION,
            GuidanceAgent.CLARIFICATION_PATH,
        ]

        for agent in priority:
            if agent.value not in used:
                return agent

        return None

    async def analyze_concept_type(
        self,
        concept_text: str,
        rag_context: Optional[str] = None
    ) -> ConceptType:
        """
        分析概念类型

        TODO: Story 24.5 将使用RAG上下文增强分析

        Args:
            concept_text: 概念文本
            rag_context: RAG上下文（可选）

        Returns:
            ConceptType: 推断的概念类型
        """
        text_lower = concept_text.lower()

        # 关键词匹配
        if any(kw in text_lower for kw in ["定义", "是什么", "概念"]):
            return ConceptType.DEFINITION

        if any(kw in text_lower for kw in ["证明", "推导", "证", "导"]):
            return ConceptType.PROOF

        if any(kw in text_lower for kw in ["区别", "对比", "异同", "vs"]):
            return ConceptType.COMPARISON

        if any(kw in text_lower for kw in ["应用", "例子", "场景", "使用"]):
            return ConceptType.APPLICATION

        if any(kw in text_lower for kw in ["复杂", "多步", "组合"]):
            return ConceptType.COMPLEX

        if any(kw in text_lower for kw in ["类似", "相似", "易混"]):
            return ConceptType.SIMILAR

        # 默认为抽象概念
        return ConceptType.ABSTRACT

    async def infer_quality_from_score(
        self,
        score: float,
        hints_given: int = 0
    ) -> AnswerQuality:
        """
        从评分推断回答质量

        Args:
            score: 回答评分 (0-100)
            hints_given: 已给出的提示数

        Returns:
            AnswerQuality: 推断的回答质量
        """
        # 如果给了很多提示还是低分，可能是完全不懂
        if hints_given >= 2 and score < 30:
            return AnswerQuality.NO_IDEA

        if score >= 85:
            return AnswerQuality.EXCELLENT
        elif score >= 70:
            return AnswerQuality.GOOD
        elif score >= 50:
            return AnswerQuality.PARTIAL
        elif score >= 30:
            return AnswerQuality.WRONG
        else:
            return AnswerQuality.NO_IDEA

    def get_agent_description(self, agent: GuidanceAgent) -> str:
        """获取Agent描述"""
        descriptions = {
            GuidanceAgent.MEMORY_ANCHOR: "记忆锚点 - 通过生动类比、故事和助记法帮助长期记忆",
            GuidanceAgent.EXAMPLE_TEACHING: "例题教学 - 通过完整例题和详细解答巩固理解",
            GuidanceAgent.COMPARISON_TABLE: "对比表格 - 通过结构化对比区分易混淆概念",
            GuidanceAgent.BASIC_DECOMPOSITION: "基础拆解 - 将复杂概念分解为引导问题",
            GuidanceAgent.CLARIFICATION_PATH: "澄清路径 - 系统性1500+字深度解释",
        }
        return descriptions.get(agent, "未知Agent")


# 单例实例
_agent_selector: Optional[AgentSelector] = None


def get_agent_selector() -> AgentSelector:
    """获取AgentSelector单例"""
    global _agent_selector
    if _agent_selector is None:
        _agent_selector = AgentSelector()
    return _agent_selector


__all__ = [
    "AgentSelector",
    "AnswerQuality",
    "ConceptType",
    "GuidanceAgent",
    "SelectionContext",
    "SelectionResult",
    "get_agent_selector",
]
