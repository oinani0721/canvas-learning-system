"""
VerificationState Schema定义

Epic 24: Verification Canvas Redesign (智能引导模式)
Story 24.1: Smart Guidance Architecture Design

定义Verification StateGraph的State TypedDict，用于Socratic式引导循环。

✅ Verified from LangGraph Context7 (topic: StateGraph TypedDict state definition):
- Pattern: class State(TypedDict) with typed fields
- Use Annotated for field descriptions
- Use List, Dict, Optional for complex types

✅ Verified from agentic_rag/state.py (项目现有模式):
- 使用Annotated添加字段描述
- 使用Literal限制枚举值
- 分组组织字段 (检索/策略/质量控制/上下文)

Story 24.1 AC:
- ✅ AC 1: 定义 VerificationState TypedDict
- ✅ AC 3: 支持概念队列管理
- ✅ AC 4: 支持进度状态跟踪

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-13
"""

from typing import Annotated, Any, Dict, List, Literal, Optional

from typing_extensions import TypedDict


class AttemptRecord(TypedDict):
    """单次尝试记录

    记录用户每次回答的详细信息，用于分析和改进引导策略。
    """
    attempt_number: int
    user_answer: str
    score: float
    quality: str  # excellent/good/partial/wrong
    hints_provided: List[str]
    agent_used: Optional[str]
    timestamp: str


class ConceptResult(TypedDict):
    """单个概念的验证结果

    记录每个概念的验证过程和最终结果。
    """
    concept_id: str
    concept_text: str
    final_color: str  # green/yellow/purple/red
    final_score: float
    attempts: List[AttemptRecord]
    mastered: bool


# ✅ Verified from LangGraph Context7:
# Pattern: class State(TypedDict) for StateGraph state definition
class VerificationState(TypedDict):
    """
    Verification Canvas State Schema (智能引导模式)

    ✅ Verified from LangGraph Context7 (topic: StateGraph TypedDict)

    用于Socratic式问答循环的完整状态定义。

    **源Canvas信息**:
    - source_canvas: 源Canvas文件路径
    - source_nodes: 源Canvas中需要验证的节点列表

    **概念队列**:
    - concept_queue: 待验证概念队列
    - current_concept: 当前正在验证的概念
    - current_concept_idx: 当前概念索引

    **用户回答**:
    - user_answer: 用户当前回答内容
    - answer_quality: 回答质量评级 (excellent/good/partial/wrong)
    - answer_score: 回答评分 (0-100)

    **进度跟踪**:
    - total_concepts: 总概念数
    - completed_concepts: 已完成概念数
    - green_count: 掌握(绿色)数量
    - yellow_count: 部分理解(黄色)数量
    - purple_count: 需复习(紫色)数量
    - red_count: 未掌握(红色)数量

    **引导状态**:
    - hints_given: 当前概念已给出的提示数
    - max_hints: 最大提示次数
    - current_hints: 当前提示内容列表
    - selected_agent: 选中的引导Agent

    **结果Canvas**:
    - verification_canvas: 生成的验证Canvas数据
    - concept_results: 每个概念的验证结果

    **会话控制**:
    - session_id: 验证会话ID
    - is_paused: 是否暂停
    - is_completed: 是否完成
    - user_action: 用户操作 (continue/skip/pause/end)
    """

    # ═══════════════════════════════════════════════════════════════════════════════
    # 源Canvas信息
    # ═══════════════════════════════════════════════════════════════════════════════
    source_canvas: Annotated[str, "源Canvas文件路径"]
    source_nodes: Annotated[List[Dict[str, Any]], "源Canvas中需要验证的节点列表"]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 概念队列
    # ═══════════════════════════════════════════════════════════════════════════════
    concept_queue: Annotated[List[str], "待验证概念队列"]
    current_concept: Annotated[str, "当前正在验证的概念"]
    current_concept_idx: Annotated[int, "当前概念索引"]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 用户回答
    # ═══════════════════════════════════════════════════════════════════════════════
    user_answer: Annotated[str, "用户当前回答内容"]
    answer_quality: Annotated[
        Literal["excellent", "good", "partial", "wrong", "skipped"],
        "回答质量评级"
    ]
    answer_score: Annotated[float, "回答评分 (0-100)"]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 进度跟踪 (Story 24.3 依赖)
    # ═══════════════════════════════════════════════════════════════════════════════
    total_concepts: Annotated[int, "总概念数"]
    completed_concepts: Annotated[int, "已完成概念数"]
    green_count: Annotated[int, "掌握(绿色)数量"]
    yellow_count: Annotated[int, "部分理解(黄色)数量"]
    purple_count: Annotated[int, "需复习(紫色)数量"]
    red_count: Annotated[int, "未掌握(红色)数量"]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 引导状态 (Story 24.4 依赖)
    # ═══════════════════════════════════════════════════════════════════════════════
    hints_given: Annotated[int, "当前概念已给出的提示数"]
    max_hints: Annotated[int, "最大提示次数 (默认3)"]
    current_hints: Annotated[List[str], "当前提示内容列表"]
    selected_agent: Annotated[
        Optional[Literal[
            "memory-anchor",
            "example-teaching",
            "comparison-table",
            "basic-decomposition",
            "clarification-path"
        ]],
        "选中的引导Agent"
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # RAG上下文 (Story 24.5 依赖)
    # ═══════════════════════════════════════════════════════════════════════════════
    rag_context: Annotated[Optional[str], "RAG检索的上下文内容"]
    rag_available: Annotated[bool, "RAG服务是否可用"]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 结果Canvas
    # ═══════════════════════════════════════════════════════════════════════════════
    verification_canvas: Annotated[Dict[str, Any], "生成的验证Canvas数据"]
    concept_results: Annotated[List[ConceptResult], "每个概念的验证结果"]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 会话控制
    # ═══════════════════════════════════════════════════════════════════════════════
    session_id: Annotated[str, "验证会话ID"]
    is_paused: Annotated[bool, "是否暂停"]
    is_completed: Annotated[bool, "是否完成"]
    user_action: Annotated[
        Literal["continue", "skip", "pause", "end", "retry"],
        "用户操作"
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 当前问题 (Story 24.2 依赖)
    # ═══════════════════════════════════════════════════════════════════════════════
    current_question: Annotated[str, "当前生成的引导问题"]
    question_type: Annotated[
        Literal["definition", "application", "comparison", "example", "derivation"],
        "问题类型"
    ]


def create_initial_state(
    source_canvas: str,
    source_nodes: List[Dict[str, Any]],
    session_id: str
) -> VerificationState:
    """
    创建初始VerificationState

    Args:
        source_canvas: 源Canvas文件路径
        source_nodes: 需要验证的节点列表
        session_id: 验证会话ID

    Returns:
        初始化的VerificationState
    """
    # 从节点提取概念文本
    concept_queue = [
        node.get("text", "").strip()
        for node in source_nodes
        if node.get("text", "").strip()
    ]

    return VerificationState(
        # 源Canvas信息
        source_canvas=source_canvas,
        source_nodes=source_nodes,

        # 概念队列
        concept_queue=concept_queue,
        current_concept=concept_queue[0] if concept_queue else "",
        current_concept_idx=0,

        # 用户回答
        user_answer="",
        answer_quality="wrong",
        answer_score=0.0,

        # 进度跟踪
        total_concepts=len(concept_queue),
        completed_concepts=0,
        green_count=0,
        yellow_count=0,
        purple_count=0,
        red_count=0,

        # 引导状态
        hints_given=0,
        max_hints=3,
        current_hints=[],
        selected_agent=None,

        # RAG上下文
        rag_context=None,
        rag_available=True,

        # 结果Canvas
        verification_canvas={"nodes": [], "edges": []},
        concept_results=[],

        # 会话控制
        session_id=session_id,
        is_paused=False,
        is_completed=False,
        user_action="continue",

        # 当前问题
        current_question="",
        question_type="definition",
    )


__all__ = [
    "VerificationState",
    "AttemptRecord",
    "ConceptResult",
    "create_initial_state",
]
