"""
BMad Orchestrator StateGraph 构建

构建全自动化 SM→PO→Dev→QA 工作流的 LangGraph StateGraph。

✅ Verified from LangGraph Skill:
- Pattern: StateGraph(State) construction
- add_node() for nodes
- add_edge() for unconditional transitions
- add_conditional_edges() for routing
- set_entry_point() for start node
- compile() with checkpointer for persistence

12个节点工作流 (v1.1.0 - 增加 SDD_PRE 和 CLEANUP):
SM → PO → Analysis → SDD_PRE → DEV → QA → SDD → MERGE → COMMIT → CLEANUP → END
                        ↓                   ↓                           ↑
                      HALT              FIX (CONCERNS循环)               │
                    (覆盖率<80%)           ↓                           │
                                        HALT ─────────────────────────┘

关键改进 (v1.1.0):
- SDD_PRE 节点: 开发前验证 SDD 覆盖率 ≥80%，否则强制阻止
- CLEANUP 节点: 确保工作树总是被清理 (无论成功或失败)
- Fail-Forward 设计: 部分失败时仍继续执行到 COMMIT
- 增强路由: 优先检查实际结果列表，而非状态标志
- 卡住检测: 5分钟无日志活动则终止会话并提取部分结果

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-11-30
Updated: 2025-12-01 - Added cleanup_node, fail-forward design
"""

import asyncio
from pathlib import Path
from typing import List, Literal

# ✅ Verified from Context7: Use MemorySaver for simplicity
# AsyncSqliteSaver requires async context manager which complicates the architecture
# TODO: Implement async context wrapper for persistent checkpointing in future version
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .nodes import (
    analysis_node,
    cleanup_node,
    commit_node,
    dev_node,
    fix_node,
    halt_node,
    merge_node,
    po_node,
    qa_node,
    sdd_pre_validation_node,  # NEW: v1.1.0 - Pre-dev SDD validation
    sdd_validation_node,
    sm_node,
)
from .state import BmadOrchestratorState, create_initial_state

# ============================================================================
# 辅助函数
# ============================================================================

async def create_worktrees_from_main(
    base_path: Path,
    worktree_base: Path,
    story_ids: List[str],
) -> dict:
    """
    为 re-QA 场景从 main 分支创建 worktrees

    当使用 --skip-dev 参数时，代码已在 main 分支上。
    此函数创建 worktrees 以便 QA 可以在独立环境中运行。

    Args:
        base_path: 项目根目录 (main 仓库)
        worktree_base: Worktree 父目录
        story_ids: Story IDs 列表

    Returns:
        worktree_paths: {story_id: worktree_path} 字典
    """
    worktree_paths = {}

    for story_id in story_ids:
        branch_name = f"develop-{story_id}"
        worktree_path = worktree_base / f"Canvas-{branch_name}"

        # 检查 worktree 是否已存在
        if worktree_path.exists():
            print(f"[Worktree] {worktree_path} already exists, reusing")
            worktree_paths[story_id] = str(worktree_path)
            continue

        # 检查分支是否已存在
        check_branch = await asyncio.create_subprocess_exec(
            'git', 'rev-parse', '--verify', branch_name,
            cwd=str(base_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, _ = await check_branch.communicate()
        branch_exists = check_branch.returncode == 0

        if branch_exists:
            # 分支存在，使用现有分支创建 worktree
            proc = await asyncio.create_subprocess_exec(
                'git', 'worktree', 'add', str(worktree_path), branch_name,
                cwd=str(base_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            # 分支不存在，从 main 创建新分支
            proc = await asyncio.create_subprocess_exec(
                'git', 'worktree', 'add', '-b', branch_name, str(worktree_path), 'main',
                cwd=str(base_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            print(f"[Worktree] Created: {worktree_path}")
            worktree_paths[story_id] = str(worktree_path)
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            print(f"[Worktree] [WARN] Failed to create {worktree_path}: {error_msg}")
            # 即使失败也记录路径，让后续流程决定是否继续
            worktree_paths[story_id] = str(worktree_path)

    return worktree_paths


# ============================================================================
# 路由函数
# ============================================================================

def route_after_sm(state: BmadOrchestratorState) -> Literal["po_node", "halt_node"]:
    """
    SM 节点后的路由

    ✅ Verified from LangGraph Skill (Pattern: Conditional routing)

    规则:
    - sm_status == "completed" → PO
    - sm_status == "failed" → HALT
    """
    if state.get("sm_status") == "completed":
        return "po_node"
    return "halt_node"


def route_after_po(state: BmadOrchestratorState) -> Literal["analysis_node", "halt_node"]:
    """
    PO 节点后的路由

    规则:
    - 有 approved_stories → Analysis
    - 无 approved_stories → HALT
    """
    if state.get("approved_stories"):
        return "analysis_node"
    return "halt_node"


def route_after_analysis(state: BmadOrchestratorState) -> Literal["sdd_pre_validation_node"]:
    """
    Analysis 节点后的路由 (v1.1.0)

    总是进入 SDD Pre-Validation 阶段 (开发前验证)
    """
    return "sdd_pre_validation_node"


def route_after_sdd_pre(state: BmadOrchestratorState) -> Literal["dev_node", "halt_node"]:
    """
    SDD Pre-Validation 节点后的路由 (v1.1.0)

    规则:
    - sdd_pre_status == "passed" or "warnings" → DEV
    - sdd_pre_status == "failed" → HALT (强制阻止)
    """
    sdd_pre_status = state.get("sdd_pre_status", "pending")

    if sdd_pre_status in ("passed", "warnings", "skipped"):
        print(f"[Router] SDD_PRE→DEV: sdd_pre_status={sdd_pre_status}")
        return "dev_node"

    # 失败时阻止开发
    print(f"[Router] SDD_PRE→HALT: sdd_pre_status={sdd_pre_status}")
    return "halt_node"


def route_after_dev(state: BmadOrchestratorState) -> Literal["qa_node", "halt_node"]:
    """
    Dev 节点后的路由 - FAIL-FORWARD 设计

    ✅ Enhanced: 检查实际 dev_outcomes 列表，而非仅检查状态标志

    规则:
    - 如果有任何 Story 开发成功 → QA (即使部分失败也继续)
    - 只有当所有 Story 都失败时 → HALT

    这确保即使部分 Story 失败，工作流也能继续到 QA 阶段。
    """
    # 首先检查实际的 dev_outcomes 列表
    dev_outcomes = state.get("dev_outcomes", [])

    if dev_outcomes:
        # 计算成功的 Story 数量
        success_count = sum(
            1 for o in dev_outcomes
            if o.get("outcome") == "SUCCESS"
        )

        if success_count > 0:
            # 至少有一个 Story 成功 - 继续到 QA
            print(f"[Router] DEV→QA: {success_count}/{len(dev_outcomes)} stories succeeded (fail-forward)")
            return "qa_node"

    # 回退到状态标志检查（向后兼容）
    dev_status = state.get("dev_status", "unknown")
    if dev_status in ("completed", "partially_failed"):
        print(f"[Router] DEV→QA: dev_status={dev_status}")
        return "qa_node"

    # 只有当真的没有成功时才 HALT
    print(f"[Router] DEV→HALT: No successful stories (dev_status={dev_status}, outcomes={len(dev_outcomes)})")
    return "halt_node"


def route_after_qa(
    state: BmadOrchestratorState
) -> Literal["sdd_validation_node", "fix_node", "halt_node"]:
    """
    QA 节点后的路由 - FAIL-FORWARD 设计

    优先检查 qa_outcomes 列表的实际结果，而不是仅依赖 current_qa_gate 状态标志。

    Fail-Forward 规则:
    1. 首先检查 qa_outcomes 列表
    2. 如果有任何 PASS/WAIVED 的 Story → 继续到 SDD_VALIDATION
    3. 如果只有 CONCERNS 且未修复 → 尝试 FIX (最多1次)
    4. 只有当全部 FAIL 时才 HALT
    5. 回退到 current_qa_gate 状态标志（向后兼容）
    """
    # 首先检查实际的 qa_outcomes 列表
    qa_outcomes = state.get("qa_outcomes", [])
    fix_attempts = state.get("fix_attempts", 0)

    if qa_outcomes:
        # 统计各种结果
        pass_count = sum(
            1 for o in qa_outcomes
            if o.get("qa_gate") in ("PASS", "WAIVED")
        )
        concerns_count = sum(
            1 for o in qa_outcomes
            if o.get("qa_gate") == "CONCERNS"
        )
        fail_count = sum(
            1 for o in qa_outcomes
            if o.get("qa_gate") == "FAIL"
        )
        total = len(qa_outcomes)

        # Fail-forward: 至少有一个 PASS/WAIVED 就继续
        if pass_count > 0:
            print(f"[Router] QA→SDD: {pass_count}/{total} stories passed (fail-forward)")
            return "sdd_validation_node"

        # 只有 CONCERNS，尝试修复一次
        if concerns_count > 0 and fail_count == 0 and fix_attempts < 1:
            print(f"[Router] QA→FIX: {concerns_count} stories with concerns, attempting fix")
            return "fix_node"

        # 如果有 CONCERNS 但已经尝试修复过，继续到 SDD（fail-forward）
        if concerns_count > 0 and fix_attempts >= 1:
            print(f"[Router] QA→SDD: {concerns_count} concerns after fix attempt (fail-forward)")
            return "sdd_validation_node"

        # 全部 FAIL 才 HALT
        if fail_count == total:
            print(f"[Router] QA→HALT: All {fail_count} stories failed")
            return "halt_node"

    # 回退到状态标志检查（向后兼容）
    qa_gate = state.get("current_qa_gate", "unknown")

    if qa_gate in ("PASS", "WAIVED"):
        print(f"[Router] QA→SDD: qa_gate={qa_gate}")
        return "sdd_validation_node"
    elif qa_gate == "CONCERNS" and fix_attempts < 1:
        print(f"[Router] QA→FIX: qa_gate={qa_gate}, fix_attempts={fix_attempts}")
        return "fix_node"
    elif qa_gate == "CONCERNS" and fix_attempts >= 1:
        # Fail-forward: CONCERNS 修复后继续
        print(f"[Router] QA→SDD: qa_gate={qa_gate} after fix (fail-forward)")
        return "sdd_validation_node"

    # 只有当真的失败时才 HALT
    print(f"[Router] QA→HALT: qa_gate={qa_gate}, outcomes={len(qa_outcomes)}")
    return "halt_node"


def route_after_sdd_validation(
    state: BmadOrchestratorState
) -> Literal["merge_node", "halt_node"]:
    """
    SDD Validation 节点后的路由 - FAIL-FORWARD 设计

    规则:
    - sdd_status in ("passed", "warnings", "skipped") → MERGE
    - sdd_status == "failed" → HALT (但 warnings 仍继续)

    Fail-Forward: 默认为 "skipped"，确保即使 SDD 验证未运行也能继续
    """
    sdd_status = state.get("sdd_status", "skipped")

    if sdd_status in ("passed", "warnings", "skipped"):
        print(f"[Router] SDD→MERGE: sdd_status={sdd_status}")
        return "merge_node"

    # 只有明确失败才 HALT
    print(f"[Router] SDD→HALT: sdd_status={sdd_status}")
    return "halt_node"


def route_after_merge(state: BmadOrchestratorState) -> Literal["commit_node", "halt_node"]:
    """
    Merge 节点后的路由 - FAIL-FORWARD 设计

    规则:
    - merge_status == "conflict_detected" → HALT
    - 其他情况 (包括 "completed", "partial") → COMMIT

    Fail-Forward: 只有明确的冲突才阻止，部分合并也继续
    """
    merge_status = state.get("merge_status", "unknown")

    # 只有明确的冲突才 HALT
    if merge_status == "conflict_detected":
        print(f"[Router] MERGE→HALT: merge_status={merge_status}")
        return "halt_node"

    # Fail-forward: 其他情况继续到 COMMIT
    print(f"[Router] MERGE→COMMIT: merge_status={merge_status}")
    return "commit_node"


def route_after_fix(state: BmadOrchestratorState) -> Literal["qa_node", "commit_node"]:
    """
    Fix 节点后的路由

    规则:
    - fix_attempts == 1 → 重新 QA
    - fix_attempts > 1 → 提交已通过的
    """
    if state.get("fix_attempts", 0) <= 1:
        return "qa_node"
    return "commit_node"


def route_after_commit(state: BmadOrchestratorState) -> Literal["cleanup_node", "dev_node"]:
    """
    Commit 节点后的路由

    规则:
    - re-QA 模式 (skip_dev) → 直接 CLEANUP (不循环回DEV)
    - 还有更多批次 → 返回 DEV
    - 所有批次完成 → CLEANUP (然后到 END)
    """
    # 检查是否为 re-QA 模式 (skip_dev)
    re_qa_mode = state.get("re_qa_mode", False)
    if re_qa_mode:
        print("[Router] COMMIT→CLEANUP: re-QA mode - skip batch checking")
        return "cleanup_node"

    current_batch_index = state.get("current_batch_index", 0)
    parallel_batches = state.get("parallel_batches", [])

    if current_batch_index + 1 < len(parallel_batches):
        # 还有更多批次，更新索引并返回 DEV
        print(f"[Router] COMMIT→DEV: More batches remaining ({current_batch_index + 1}/{len(parallel_batches)})")
        return "dev_node"

    # 所有批次完成，进入清理
    print("[Router] COMMIT→CLEANUP: All batches completed")
    return "cleanup_node"


# ============================================================================
# StateGraph 构建
# ============================================================================

def build_graph(
    checkpointer_path: str = "bmad_orchestrator.db",
    skip_sm: bool = False,
    skip_po: bool = False,
    skip_analysis: bool = False,
    skip_dev: bool = False,
    skip_qa: bool = False,
    skip_sdd: bool = False,
) -> StateGraph:
    """
    构建 BMad Orchestrator StateGraph (支持多阶段跳过)

    ✅ Verified from LangGraph Skill:
    - Pattern: StateGraph(State) construction
    - add_node() for nodes
    - add_conditional_edges() for routing

    Args:
        checkpointer_path: SqliteSaver 数据库路径
        skip_sm: 是否跳过SM阶段
        skip_po: 是否跳过PO阶段
        skip_analysis: 是否跳过Analysis阶段
        skip_dev: 是否跳过DEV阶段 (用于re-QA场景)
        skip_qa: 是否跳过QA阶段
        skip_sdd: 是否跳过SDD阶段

    Returns:
        编译后的 StateGraph
    """
    # 创建 StateGraph
    graph = StateGraph(BmadOrchestratorState)

    # ========================================
    # 添加节点
    # ========================================

    graph.add_node("sm_node", sm_node)
    graph.add_node("po_node", po_node)
    graph.add_node("analysis_node", analysis_node)
    graph.add_node("sdd_pre_validation_node", sdd_pre_validation_node)  # NEW: v1.1.0 - Pre-dev SDD
    graph.add_node("dev_node", dev_node)
    graph.add_node("qa_node", qa_node)
    graph.add_node("sdd_validation_node", sdd_validation_node)  # SDD Validation (post-QA)
    graph.add_node("merge_node", merge_node)
    graph.add_node("commit_node", commit_node)
    graph.add_node("fix_node", fix_node)
    graph.add_node("halt_node", halt_node)
    graph.add_node("cleanup_node", cleanup_node)  # Cleanup (v1.1.0)

    # ========================================
    # 设置入口点 (根据 skip 参数条件设置)
    # ========================================

    if skip_sm and skip_po and skip_analysis and skip_dev:
        graph.set_entry_point("qa_node")
        print("[INFO] Skip SM+PO+Analysis+DEV - starting from QA node (re-QA mode)")
    elif skip_sm and skip_po and skip_analysis:
        graph.set_entry_point("dev_node")
        print("[INFO] Skip SM+PO+Analysis - starting from DEV node")
    elif skip_sm and skip_po:
        graph.set_entry_point("analysis_node")
        print("[INFO] Skip SM+PO - starting from Analysis node")
    elif skip_sm:
        graph.set_entry_point("po_node")
        print("[INFO] Skip SM - starting from PO node")
    else:
        graph.set_entry_point("sm_node")

    # ========================================
    # 添加条件边 (路由)
    # ========================================

    # SM → PO or HALT
    graph.add_conditional_edges(
        "sm_node",
        route_after_sm,
        {
            "po_node": "po_node",
            "halt_node": "halt_node",
        }
    )

    # PO → Analysis or HALT
    graph.add_conditional_edges(
        "po_node",
        route_after_po,
        {
            "analysis_node": "analysis_node",
            "halt_node": "halt_node",
        }
    )

    # Analysis → SDD_PRE (v1.1.0)
    graph.add_conditional_edges(
        "analysis_node",
        route_after_analysis,
        {
            "sdd_pre_validation_node": "sdd_pre_validation_node",
        }
    )

    # SDD_PRE → DEV or HALT (v1.1.0)
    graph.add_conditional_edges(
        "sdd_pre_validation_node",
        route_after_sdd_pre,
        {
            "dev_node": "dev_node",
            "halt_node": "halt_node",
        }
    )

    # DEV → QA or HALT
    graph.add_conditional_edges(
        "dev_node",
        route_after_dev,
        {
            "qa_node": "qa_node",
            "halt_node": "halt_node",
        }
    )

    # QA → SDD_VALIDATION or FIX or HALT
    graph.add_conditional_edges(
        "qa_node",
        route_after_qa,
        {
            "sdd_validation_node": "sdd_validation_node",  # NEW: QA → SDD
            "fix_node": "fix_node",
            "halt_node": "halt_node",
        }
    )

    # SDD_VALIDATION → MERGE or HALT
    graph.add_conditional_edges(
        "sdd_validation_node",
        route_after_sdd_validation,
        {
            "merge_node": "merge_node",
            "halt_node": "halt_node",
        }
    )

    # MERGE → COMMIT or HALT
    graph.add_conditional_edges(
        "merge_node",
        route_after_merge,
        {
            "commit_node": "commit_node",
            "halt_node": "halt_node",
        }
    )

    # FIX → QA or COMMIT
    graph.add_conditional_edges(
        "fix_node",
        route_after_fix,
        {
            "qa_node": "qa_node",
            "commit_node": "commit_node",
        }
    )

    # COMMIT → CLEANUP or DEV (for next batch)
    graph.add_conditional_edges(
        "commit_node",
        route_after_commit,
        {
            "cleanup_node": "cleanup_node",  # Changed: COMMIT → CLEANUP (v1.1.0)
            "dev_node": "dev_node",
        }
    )

    # HALT → CLEANUP (Changed from HALT → END in v1.1.0)
    # Ensures cleanup always happens even on failure
    graph.add_edge("halt_node", "cleanup_node")

    # CLEANUP → END (Always the final step)
    graph.add_edge("cleanup_node", END)

    return graph


def compile_graph(
    checkpointer_path: str = "bmad_orchestrator.db",
    skip_sm: bool = False,
    skip_po: bool = False,
    skip_analysis: bool = False,
    skip_dev: bool = False,
    skip_qa: bool = False,
    skip_sdd: bool = False,
) -> "CompiledGraph":
    """
    编译 StateGraph 并添加 Checkpointer (支持多阶段跳过)

    ✅ Verified from LangGraph Skill:
    - Pattern: graph.compile(checkpointer=SqliteSaver(...))

    Args:
        checkpointer_path: SqliteSaver 数据库路径 (仅在 SqliteSaver 可用时使用)
        skip_sm: 是否跳过SM阶段
        skip_po: 是否跳过PO阶段
        skip_analysis: 是否跳过Analysis阶段
        skip_dev: 是否跳过DEV阶段 (用于re-QA场景)
        skip_qa: 是否跳过QA阶段
        skip_sdd: 是否跳过SDD阶段

    Returns:
        编译后的 Graph (可调用)
    """
    graph = build_graph(
        checkpointer_path,
        skip_sm=skip_sm,
        skip_po=skip_po,
        skip_analysis=skip_analysis,
        skip_dev=skip_dev,
        skip_qa=skip_qa,
        skip_sdd=skip_sdd,
    )

    # ✅ Verified from Context7 (LangGraph persistence.md):
    # Use MemorySaver for async workflows (simple, no external dependencies)
    # Note: State is not persisted across restarts, but workflow runs correctly
    checkpointer = MemorySaver()

    # 编译
    compiled = graph.compile(checkpointer=checkpointer)

    return compiled


# ============================================================================
# 运行入口
# ============================================================================

async def run_epic_workflow(
    epic_id: str,
    story_ids: List[str],
    base_path: str,
    worktree_base: str = None,
    max_turns: int = 200,
    mode_override: Literal["parallel", "linear", "hybrid"] = None,
    checkpointer_path: str = "bmad_orchestrator.db",
    skip_sm: bool = False,
    skip_po: bool = False,
    skip_analysis: bool = False,
    skip_dev: bool = False,
    skip_qa: bool = False,
    skip_sdd: bool = False,
    timeout: int = 3600,
) -> dict:
    """
    运行 Epic 全自动化工作流

    ✅ Verified from LangGraph Skill:
    - Pattern: compiled_graph.ainvoke(initial_state)

    Args:
        epic_id: Epic ID
        story_ids: 要处理的 Story IDs
        base_path: 项目根目录
        worktree_base: Worktree 父目录 (默认: base_path 父目录)
        max_turns: 每个 Claude 会话的最大轮数
        mode_override: 强制执行模式
        checkpointer_path: SqliteSaver 数据库路径
        skip_sm: 是否跳过SM阶段
        skip_po: 是否跳过PO阶段
        skip_analysis: 是否跳过依赖分析阶段
        skip_dev: 是否跳过DEV阶段 (用于re-QA场景)
        skip_qa: 是否跳过QA阶段
        skip_sdd: 是否跳过SDD验证
        timeout: 超时时间(秒)

    Returns:
        最终状态字典
    """
    print("=" * 60)
    print(f"BMad Orchestrator - Epic {epic_id} Workflow")
    print("=" * 60)
    print(f"Stories: {story_ids}")
    print(f"Base Path: {base_path}")
    print(f"Mode Override: {mode_override or 'Auto-detect'}")
    print(f"Max Turns: {max_turns}")
    print(f"Timeout: {timeout}s")
    print("\nPhase Skip Settings:")
    print(f"  Skip SM: {skip_sm}")
    print(f"  Skip PO: {skip_po}")
    print(f"  Skip Analysis: {skip_analysis}")
    print(f"  Skip DEV: {skip_dev}")
    print(f"  Skip QA: {skip_qa}")
    print(f"  Skip SDD: {skip_sdd}")
    if any([skip_sm, skip_po, skip_analysis, skip_dev, skip_qa, skip_sdd]):
        entry_point = "SM"
        if skip_sm:
            entry_point = "PO"
        if skip_sm and skip_po:
            entry_point = "Analysis"
        if skip_sm and skip_po and skip_analysis:
            entry_point = "DEV"
        if skip_sm and skip_po and skip_analysis and skip_dev:
            entry_point = "QA"
        print(f"  ** Entry Point: {entry_point} **")
    print("=" * 60)

    # 创建初始状态
    initial_state = create_initial_state(
        epic_id=epic_id,
        story_ids=story_ids,
        base_path=base_path,
        worktree_base=worktree_base,
        max_turns=max_turns,
        mode_override=mode_override,
    )

    # 添加 timeout 到 state (供 nodes 使用)
    initial_state["timeout"] = timeout

    # 预填充 story_drafts (多个跳过模式都需要)
    base_path_obj = Path(base_path)
    story_drafts = []
    for story_id in story_ids:
        # 尝试找到 Story 文件
        story_file_patterns = [
            f"docs/stories/story-{story_id}.story.md",
            f"docs/stories/{story_id}.story.md",
        ]
        story_file = None
        for pattern in story_file_patterns:
            full_path = base_path_obj / pattern
            if full_path.exists():
                story_file = pattern
                break

        if story_file:
            story_drafts.append({
                "story_id": story_id,
                "story_file": story_file,
                "outcome": "SUCCESS",
                "checklist_passed": True,
            })
        else:
            story_drafts.append({
                "story_id": story_id,
                "story_file": f"docs/stories/story-{story_id}.story.md",
                "outcome": "SUCCESS",
                "checklist_passed": True,
            })

    # ========================================
    # Skip SM 状态预填充
    # ========================================
    if skip_sm:
        initial_state["sm_status"] = "completed"
        initial_state["current_phase"] = "po"
        initial_state["story_drafts"] = story_drafts
        print(f"[INFO] Skip SM - Pre-filled {len(story_drafts)} story drafts")

    # ========================================
    # Skip PO 状态预填充
    # ========================================
    if skip_po:
        initial_state["po_status"] = "completed"
        initial_state["approved_stories"] = story_ids  # 假设全部批准
        initial_state["sot_resolutions"] = []
        if not skip_sm:
            initial_state["story_drafts"] = story_drafts
        initial_state["current_phase"] = "analysis"
        print(f"[INFO] Skip PO - All {len(story_ids)} stories pre-approved")

    # ========================================
    # Skip Analysis 状态预填充
    # ========================================
    if skip_analysis:
        mode = mode_override or "parallel"
        if mode == "linear":
            batches = [[s] for s in story_ids]
        else:
            batches = [story_ids]  # 单批次并行
        initial_state["parallel_batches"] = batches
        initial_state["current_batch_index"] = 0
        initial_state["execution_mode"] = mode
        if not skip_po:
            initial_state["approved_stories"] = story_ids
        initial_state["current_phase"] = "dev"
        print(f"[INFO] Skip Analysis - Using {mode} mode with {len(batches)} batch(es)")

    # ========================================
    # Skip DEV 状态预填充 (re-QA 场景)
    # ========================================
    if skip_dev:
        from datetime import datetime

        # 创建 worktrees 从 main 分支
        worktree_base_path = Path(worktree_base) if worktree_base else base_path_obj.parent
        worktree_paths = await create_worktrees_from_main(base_path_obj, worktree_base_path, story_ids)

        # 构造合成 dev_outcomes (假设所有 Story 开发成功)
        synthetic_dev_outcomes = []
        for story_id in story_ids:
            synthetic_dev_outcomes.append({
                "story_id": story_id,
                "outcome": "SUCCESS",
                "tests_passed": True,
                "test_count": 0,
                "test_coverage": None,
                "files_created": [],
                "files_modified": [],
                "duration_seconds": 0,
                "blocking_reason": None,
                "completion_notes": "Pre-filled for re-QA (--skip-dev)",
                "agent_model": "claude-sonnet-4-5",
                "timestamp": datetime.now().isoformat(),
            })

        initial_state["dev_outcomes"] = synthetic_dev_outcomes
        initial_state["dev_status"] = "completed"
        initial_state["worktree_paths"] = worktree_paths
        initial_state["current_phase"] = "qa"
        initial_state["re_qa_mode"] = True  # 标记为 re-QA 模式，用于路由决策

        # 确保前置状态也正确设置
        if not skip_analysis:
            mode = mode_override or "linear"
            if mode == "linear":
                batches = [[s] for s in story_ids]
            else:
                batches = [story_ids]
            initial_state["parallel_batches"] = batches
            initial_state["current_batch_index"] = 0
            initial_state["execution_mode"] = mode

        print(f"[INFO] Skip DEV - Created {len(worktree_paths)} worktrees from main branch")
        print(f"[INFO] Skip DEV - Pre-filled {len(synthetic_dev_outcomes)} dev_outcomes (re-QA mode)")

    # 编译 Graph (传递所有 skip 参数)
    compiled = compile_graph(
        checkpointer_path,
        skip_sm=skip_sm,
        skip_po=skip_po,
        skip_analysis=skip_analysis,
        skip_dev=skip_dev,
        skip_qa=skip_qa,
        skip_sdd=skip_sdd,
    )

    # 运行
    config = {"configurable": {"thread_id": f"epic-{epic_id}"}}
    final_state = await compiled.ainvoke(initial_state, config)

    # === Status Persistence: Persist workflow results to YAML ===
    try:
        from .status_persister import StatusPersister

        persister = StatusPersister(Path(base_path))
        success = await persister.persist_workflow_result(
            final_state=final_state,
            epic_id=epic_id,
        )

        if success:
            print(f"[Orchestrator] Status persisted to {persister.YAML_PATH}")
        else:
            print("[Orchestrator] [WARN] Failed to persist status (non-blocking)")
    except Exception as e:
        print(f"[Orchestrator] [WARN] Status persistence error: {e} (non-blocking)")
    # === End Status Persistence ===

    print("=" * 60)
    print("Workflow Complete!")
    print(f"Final Status: {final_state.get('final_status', 'unknown')}")
    print(f"Commits: {len(final_state.get('commit_shas', []))}")
    print(f"Blockers: {len(final_state.get('blockers', []))}")
    print("=" * 60)

    return final_state


async def resume_workflow(
    thread_id: str,
    checkpointer_path: str = "bmad_orchestrator.db",
) -> dict:
    """
    恢复中断的工作流

    ✅ Verified from LangGraph Skill:
    - Pattern: Use thread_id to resume from checkpoint

    Args:
        thread_id: 工作流线程 ID (通常是 "epic-{epic_id}")
        checkpointer_path: SqliteSaver 数据库路径

    Returns:
        最终状态字典
    """
    print(f"Resuming workflow: {thread_id}")

    compiled = compile_graph(checkpointer_path)

    config = {"configurable": {"thread_id": thread_id}}

    # 获取当前状态
    state = await compiled.aget_state(config)

    if state.values:
        print(f"Current Phase: {state.values.get('current_phase', 'unknown')}")
        print("Resuming...")

        # 继续执行
        final_state = await compiled.ainvoke(None, config)
        return final_state
    else:
        print(f"No checkpoint found for thread: {thread_id}")
        return {}


# ============================================================================
# CLI 入口
# ============================================================================

if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="BMad Orchestrator - Epic Workflow")
    parser.add_argument("epic_id", help="Epic ID to develop")
    parser.add_argument("--stories", nargs="+", required=True, help="Story IDs")
    parser.add_argument("--base-path", default=".", help="Project base path")
    parser.add_argument("--worktree-base", help="Worktree parent directory")
    parser.add_argument("--max-turns", type=int, default=200, help="Max turns per session")
    parser.add_argument("--mode", choices=["parallel", "linear", "hybrid"], help="Execution mode override")
    parser.add_argument("--resume", help="Resume from thread ID")

    args = parser.parse_args()

    async def main():
        if args.resume:
            result = await resume_workflow(args.resume)
        else:
            result = await run_epic_workflow(
                epic_id=args.epic_id,
                story_ids=args.stories,
                base_path=args.base_path,
                worktree_base=args.worktree_base,
                max_turns=args.max_turns,
                mode_override=args.mode,
            )

        print("\nFinal Result:")
        print(f"  Status: {result.get('final_status', 'unknown')}")
        print(f"  Summary: {result.get('completion_summary', 'N/A')}")

    asyncio.run(main())
