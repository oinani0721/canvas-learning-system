"""
BmadOrchestratorState Schema 定义

定义全自动化 SM→PO→Dev→QA 工作流的 State TypedDict，继承自 LangGraph MessagesState。

✅ Verified from LangGraph Skill:
- Pattern: class State(MessagesState)
- MessagesState 自动管理 messages 列表
- Annotated 字段用于自定义 reducer
- Send 模式用于并行执行

核心功能:
- 9 个工作流阶段追踪
- 并行 Dev 结果合并 (Reducer)
- SoT 冲突自动解决记录
- 崩溃恢复支持

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-30
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional

from langgraph.graph import MessagesState
from typing_extensions import TypedDict

# ============================================================================
# Reducer 函数 (并行结果合并)
# ============================================================================

def merge_dev_outcomes(left: Optional[List[Dict]], right: Optional[List[Dict]]) -> List[Dict]:
    """
    合并来自并行 DEV 节点的结果

    ✅ Verified from LangGraph Skill (Pattern: Annotated with reducer)
    用于处理并行 Dev 节点的并发更新。

    Args:
        left: 现有的 Dev 结果列表
        right: 新的 Dev 结果

    Returns:
        合并后的 Dev 结果列表
    """
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


def merge_qa_outcomes(left: Optional[List[Dict]], right: Optional[List[Dict]]) -> List[Dict]:
    """
    合并来自并行 QA 节点的结果

    ✅ Verified from LangGraph Skill (Pattern: Annotated with reducer)
    用于处理并行 QA 节点的并发更新。

    Args:
        left: 现有的 QA 结果列表
        right: 新的 QA 结果

    Returns:
        合并后的 QA 结果列表
    """
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


def merge_blockers(left: Optional[List[Dict]], right: Optional[List[Dict]]) -> List[Dict]:
    """
    合并阻塞问题列表

    Args:
        left: 现有的阻塞问题列表
        right: 新的阻塞问题

    Returns:
        合并后的阻塞问题列表
    """
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


def merge_commit_shas(left: Optional[List[str]], right: Optional[List[str]]) -> List[str]:
    """
    合并 commit SHA 列表

    Args:
        left: 现有的 commit SHA 列表
        right: 新的 commit SHA

    Returns:
        合并后的 commit SHA 列表
    """
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


# ============================================================================
# 辅助 TypedDict 定义
# ============================================================================

class StoryDraft(TypedDict):
    """SM Agent 创建的 Story 草稿

    记录 SM 阶段的输出。
    """
    story_id: str
    story_file: str  # docs/stories/15.1.story.md
    epic_id: str
    title: str
    created_at: str  # ISO timestamp
    sdd_references: List[str]  # OpenAPI/Schema 引用
    adr_references: List[str]  # ADR 引用
    status: Literal["draft", "approved", "rejected"]


class DevOutcome(TypedDict):
    """Dev Agent 开发结果

    记录单个 Story 的开发结果。
    """
    story_id: str
    outcome: Literal["SUCCESS", "DEV_BLOCKED", "TIMEOUT", "ERROR"]
    tests_passed: bool
    test_count: int
    test_coverage: Optional[float]
    files_created: List[str]
    files_modified: List[str]
    duration_seconds: int
    blocking_reason: Optional[str]
    completion_notes: Optional[str]
    agent_model: str  # e.g., "claude-sonnet-4-5"
    timestamp: str  # ISO timestamp


class QAOutcome(TypedDict):
    """QA Agent 审查结果

    记录单个 Story 的 QA 审查结果。
    """
    story_id: str
    qa_gate: Literal["PASS", "CONCERNS", "FAIL", "WAIVED"]
    quality_score: int  # 1-100
    ac_coverage: Dict[str, Dict[str, str]]  # AC -> {status, evidence}
    issues_found: List[Dict[str, str]]  # {severity, description, location}
    recommendations: List[str]
    adr_compliance: bool
    duration_seconds: int
    reviewer_model: str
    timestamp: str  # ISO timestamp


class BlockerInfo(TypedDict):
    """阻塞问题信息

    记录工作流中遇到的阻塞问题。
    """
    story_id: str
    phase: Literal["SM", "PO", "DEV", "QA", "MERGE"]
    blocker_type: Literal[
        "MISSING_PRD",
        "MISSING_SPECS",
        "SOT_CONFLICT",
        "TEST_FAILURE",
        "QA_FAIL",
        "MERGE_CONFLICT",
        "TIMEOUT",
        "ERROR",
    ]
    description: str
    detected_at: str  # ISO timestamp
    retry_count: int
    resolution: Optional[str]


class SessionInfo(TypedDict):
    """Claude 会话信息

    记录运行中的 Claude CLI 会话。
    """
    session_id: str
    story_id: str
    phase: Literal["SM", "PO", "DEV", "QA"]
    pid: int  # 进程 ID
    worktree_path: str
    log_file: str
    started_at: str  # ISO timestamp
    status: Literal["running", "completed", "failed", "timeout"]


class SoTResolution(TypedDict):
    """SoT 冲突自动解决记录

    记录 PO 阶段自动解决的 Source of Truth 冲突。
    """
    story_id: str
    conflict_type: Literal["PRD_VS_OPENAPI", "PRD_VS_SCHEMA", "SCHEMA_VS_OPENAPI", "ADR_CONFLICT"]
    source_a: str  # 例如 "docs/prd/section-2.md#L45"
    source_b: str  # 例如 "specs/api/canvas-api.openapi.yml#L156"
    field_name: str  # 冲突的字段
    value_a: str
    value_b: str
    resolution: str  # 选择的值
    sot_level_applied: Literal["PRD", "Architecture", "Schema", "OpenAPI", "Story", "Code"]
    resolved_at: str  # ISO timestamp


class ExecutionPlan(TypedDict):
    """执行计划

    依赖分析后生成的执行计划。
    """
    mode: Literal["parallel", "linear", "hybrid"]
    parallel_batches: List[List[str]]  # [["15.1", "15.2"], ["15.3", "15.4"]]
    linear_sequence: List[str]  # 必须顺序执行的 Stories
    conflicts: Dict[str, List[str]]  # "15.1-15.3" -> ["src/review.py"]
    estimated_duration_minutes: int


class SDDValidationResult(TypedDict):
    """SDD 验证结果

    记录三层 SDD 验证的结果。
    """
    tier1_coverage: Dict[str, float]  # {"prd_to_openapi": 0.85, "prd_to_schema": 0.92}
    tier1_passed: bool  # ≥80% coverage required
    tier2_source_verified: bool  # x-source-verification metadata present
    tier3_consistency: Dict[str, List[str]]  # {"warnings": [...], "conflicts": [...]}
    tier3_passed: bool  # No critical conflicts
    overall_passed: bool
    validation_timestamp: str  # ISO timestamp
    blocking_issues: List[str]  # Tier1/2 failures that block workflow


# ============================================================================
# 主状态类定义
# ============================================================================

# ✅ Verified from LangGraph Skill:
# When extending MessagesState, use class definition (NOT TypedDict)
# Pattern: class State(MessagesState): field: Annotated[type, reducer]
class BmadOrchestratorState(MessagesState):
    """
    BMad 编排器状态 Schema - 完全自动化 SM→PO→Dev→QA 工作流

    ✅ Verified from LangGraph Skill (Pattern: MessagesState extension)

    继承 MessagesState，自动管理:
    - messages: List[BaseMessage] (自动累加)

    9 个工作流阶段:
    - SM: Story 创建
    - PO: Story 验证 (SoT 自动解决)
    - ANALYSIS: 依赖分析
    - DEV: 开发实现 (并行 Send)
    - MERGE: 合并协调
    - QA: 质量审查
    - COMMIT: Git 提交
    - FIX: CONCERNS 修复
    - HALT: 失败处理

    并行执行支持:
    - dev_outcomes: 使用 merge_dev_outcomes reducer
    - qa_outcomes: 使用 merge_qa_outcomes reducer
    - blockers: 使用 merge_blockers reducer
    - commit_shas: 使用 merge_commit_shas reducer
    """

    # ========================================
    # 会话追踪
    # ========================================
    session_id: Annotated[str, "唯一编排会话ID (epic-{id}-{timestamp})"]
    started_at: Annotated[str, "ISO 时间戳"]
    current_phase: Annotated[
        Literal["SM", "PO", "ANALYSIS", "DEV", "MERGE", "QA", "COMMIT", "FIX", "HALT", "COMPLETE"],
        "当前工作流阶段"
    ]
    re_qa_mode: Annotated[bool, "re-QA 模式 (--skip-dev 触发，跳过 DEV 阶段循环)"]

    # ========================================
    # 输入配置
    # ========================================
    epic_id: Annotated[str, "正在开发的 Epic ID"]
    story_ids: Annotated[List[str], "要处理的 Story IDs"]
    base_path: Annotated[str, "项目根目录路径"]
    worktree_base: Annotated[str, "Worktree 父目录"]
    max_turns: Annotated[int, "每个 Claude 会话的最大轮数"]
    mode_override: Annotated[
        Optional[Literal["parallel", "linear", "hybrid"]],
        "用户指定的执行模式 (覆盖自动检测)"
    ]

    # ========================================
    # SM 阶段
    # ========================================
    story_drafts: Annotated[List[StoryDraft], "SM agent 创建的 Stories"]
    sm_status: Annotated[
        Literal["pending", "in_progress", "completed", "failed"],
        "SM 阶段状态"
    ]
    sm_error: Annotated[Optional[str], "SM 阶段错误信息"]

    # ========================================
    # PO 阶段 (SoT 自动解决)
    # ========================================
    approved_stories: Annotated[List[str], "PO 批准的 Story IDs"]
    rejected_stories: Annotated[
        List[Dict[str, str]],
        "被拒绝的 Stories: [{story_id, reason}]"
    ]
    sot_resolutions: Annotated[List[SoTResolution], "SoT 冲突自动解决记录"]
    po_status: Annotated[
        Literal["pending", "in_progress", "completed", "failed"],
        "PO 阶段状态"
    ]

    # ========================================
    # 分析阶段 (自动检测模式)
    # ========================================
    execution_plan: Annotated[Optional[ExecutionPlan], "执行计划"]
    execution_mode: Annotated[
        Literal["parallel", "linear", "hybrid"],
        "最终执行模式"
    ]
    parallel_batches: Annotated[List[List[str]], "并行批次"]
    conflict_matrix: Annotated[
        Dict[str, List[str]],
        "Story 对 -> 冲突文件列表"
    ]
    current_batch_index: Annotated[int, "当前正在执行的批次索引"]

    # ========================================
    # 开发阶段 (使用 reducer 合并并行结果)
    # ========================================
    dev_outcomes: Annotated[
        List[DevOutcome],
        merge_dev_outcomes,
        "Dev agent 结果 (并行 reducer 合并)"
    ]
    active_sessions: Annotated[List[SessionInfo], "运行中的 Claude 会话"]
    worktree_paths: Annotated[Dict[str, str], "Story ID -> worktree 路径"]
    dev_status: Annotated[
        Literal["pending", "in_progress", "completed", "partially_failed", "failed"],
        "Dev 阶段状态"
    ]

    # ========================================
    # QA 阶段
    # ========================================
    qa_outcomes: Annotated[
        List[QAOutcome],
        merge_qa_outcomes,
        "QA agent 结果 (并行 reducer 合并)"
    ]
    current_qa_gate: Annotated[
        Optional[Literal["PASS", "CONCERNS", "FAIL", "WAIVED"]],
        "当前批次的 QA 门禁结果"
    ]
    fix_attempts: Annotated[int, "CONCERNS 修复尝试次数 (最多 1 次)"]
    qa_status: Annotated[
        Literal["pending", "in_progress", "completed", "partially_failed", "failed"],
        "QA 阶段状态"
    ]

    # ========================================
    # SDD Pre-Validation 阶段 (开发前, v1.1.0)
    # ========================================
    sdd_pre_validation_result: Annotated[
        Optional[Dict[str, Any]],
        "SDD 开发前验证结果 (SDDPreValidationResult)"
    ]
    sdd_pre_status: Annotated[
        Literal["pending", "skipped", "passed", "warnings", "failed"],
        "SDD 开发前验证状态"
    ]

    # ========================================
    # SDD 验证阶段 (QA 后)
    # ========================================
    sdd_validation_result: Annotated[
        Optional[Dict[str, Any]],
        "SDD 三层验证结果 (SDDValidationResult)"
    ]
    sdd_status: Annotated[
        Literal["pending", "skipped", "passed", "warnings", "failed"],
        "SDD 验证状态"
    ]

    # ========================================
    # 合并阶段
    # ========================================
    merge_status: Annotated[
        Literal["pending", "in_progress", "completed", "conflict_detected", "failed"],
        "合并阶段状态"
    ]
    merge_conflicts: Annotated[
        List[Dict[str, str]],
        "合并冲突: [{story_id, conflicting_files, conflict_type}]"
    ]

    # ========================================
    # 最终输出
    # ========================================
    commit_shas: Annotated[
        List[str],
        merge_commit_shas,
        "所有创建的 commits (并行 reducer 合并)"
    ]
    blockers: Annotated[
        List[BlockerInfo],
        merge_blockers,
        "阻塞问题 (并行 reducer 合并)"
    ]
    final_status: Annotated[
        Literal["success", "partial_success", "failed", "halted", "in_progress"],
        "最终状态"
    ]
    completion_summary: Annotated[Optional[str], "完成摘要"]
    cleanup_completed: Annotated[bool, "清理是否完成 (cleanup_node 设置)"]

    # ========================================
    # 恢复/持久化
    # ========================================
    saved_checkpoint_id: Annotated[Optional[str], "SqliteSaver 检查点 ID (renamed from checkpoint_id to avoid LangGraph reserved name)"]
    last_checkpoint_at: Annotated[Optional[str], "最后检查点时间戳"]
    recovery_point: Annotated[
        Optional[Dict[str, Any]],
        "崩溃恢复点: {phase, story_id, step}"
    ]


# ============================================================================
# 状态初始化工厂函数
# ============================================================================

def create_initial_state(
    epic_id: str,
    story_ids: List[str],
    base_path: str,
    worktree_base: Optional[str] = None,
    max_turns: int = 200,
    mode_override: Optional[Literal["parallel", "linear", "hybrid"]] = None,
) -> Dict[str, Any]:
    """
    创建初始状态字典

    用于 graph.invoke() 的初始输入。

    Args:
        epic_id: Epic ID
        story_ids: 要处理的 Story IDs
        base_path: 项目根目录
        worktree_base: Worktree 父目录 (默认: base_path 父目录)
        max_turns: 每个 Claude 会话的最大轮数
        mode_override: 用户指定的执行模式

    Returns:
        初始状态字典
    """
    from pathlib import Path

    if worktree_base is None:
        # FIX: Use resolve() to get absolute path, avoiding Path('.').parent = '.' issue
        worktree_base = str(Path(base_path).resolve().parent)

    session_id = f"epic-{epic_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    return {
        # 会话追踪
        "session_id": session_id,
        "started_at": datetime.now().isoformat(),
        "current_phase": "SM",
        "re_qa_mode": False,  # 默认不是 re-QA 模式

        # 输入配置
        "epic_id": epic_id,
        "story_ids": story_ids,
        "base_path": base_path,
        "worktree_base": worktree_base,
        "max_turns": max_turns,
        "mode_override": mode_override,

        # SM 阶段
        "story_drafts": [],
        "sm_status": "pending",
        "sm_error": None,

        # PO 阶段
        "approved_stories": [],
        "rejected_stories": [],
        "sot_resolutions": [],
        "po_status": "pending",

        # 分析阶段
        "execution_plan": None,
        "execution_mode": mode_override or "linear",  # 默认 linear，分析后更新
        "parallel_batches": [],
        "conflict_matrix": {},
        "current_batch_index": 0,

        # 开发阶段
        "dev_outcomes": [],
        "active_sessions": [],
        "worktree_paths": {},
        "dev_status": "pending",

        # QA 阶段
        "qa_outcomes": [],
        "current_qa_gate": None,
        "fix_attempts": 0,
        "qa_status": "pending",

        # SDD Pre-Validation 阶段 (v1.1.0)
        "sdd_pre_validation_result": None,
        "sdd_pre_status": "pending",

        # SDD 验证阶段
        "sdd_validation_result": None,
        "sdd_status": "pending",

        # 合并阶段
        "merge_status": "pending",
        "merge_conflicts": [],

        # 最终输出
        "commit_shas": [],
        "blockers": [],
        "final_status": "in_progress",
        "completion_summary": None,
        "cleanup_completed": False,

        # 恢复/持久化
        "saved_checkpoint_id": None,
        "last_checkpoint_at": None,
        "recovery_point": None,

        # MessagesState 继承的 messages
        "messages": [],
    }
