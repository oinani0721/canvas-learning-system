"""
BMad Orchestrator - 全自动化 24/7 开发系统

基于 LangGraph StateGraph 实现完全自动化的 SM→PO→Dev→QA 工作流。

主要模块:
- state.py: 状态 Schema 定义
- nodes.py: StateGraph 节点实现
- graph.py: StateGraph 构建和编译
- session_spawner.py: Claude CLI 会话生成器
- dependency_analyzer.py: Story 依赖分析
- cli.py: CLI 入口点

✅ Verified from LangGraph Skill (Pattern: MessagesState extension)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-30
"""

from .dependency_analyzer import (
    AnalysisResult,
    ConflictInfo,
    StoryDependency,
    analyze_dependencies,
    print_analysis_report,
)
from .graph import (
    build_graph,
    compile_graph,
    resume_workflow,
    run_epic_workflow,
)
from .nodes import (
    analysis_node,
    cleanup_node,  # v1.1.0 - Cleanup
    commit_node,
    create_dev_sends,
    create_qa_sends,
    dev_node,
    fix_node,
    halt_node,
    merge_node,
    po_node,
    qa_node,
    sdd_pre_validation_node,  # NEW: v1.1.0 - Pre-dev SDD validation
    sdd_validation_node,  # Post-QA SDD validation
    sm_node,
)
from .session_spawner import (
    DEV_PROMPT_TEMPLATE,
    PO_PROMPT_TEMPLATE,
    QA_PROMPT_TEMPLATE,
    SM_PROMPT_TEMPLATE,
    BmadSessionSpawner,
    DevResult,
    POResult,
    QAResult,
    # v1.1.0: Health monitoring
    SessionHealthMonitor,
    SessionHealthStatus,
    SessionResult,
    SMResult,
    run_single_session,
)
from .state import (
    BlockerInfo,
    BmadOrchestratorState,
    DevOutcome,
    ExecutionPlan,
    QAOutcome,
    SessionInfo,
    SoTResolution,
    StoryDraft,
    create_initial_state,
    merge_blockers,
    merge_commit_shas,
    merge_dev_outcomes,
    merge_qa_outcomes,
)

__all__ = [
    # State
    "BmadOrchestratorState",
    "StoryDraft",
    "DevOutcome",
    "QAOutcome",
    "BlockerInfo",
    "SessionInfo",
    "SoTResolution",
    "ExecutionPlan",
    "create_initial_state",
    # Reducers
    "merge_dev_outcomes",
    "merge_qa_outcomes",
    "merge_blockers",
    "merge_commit_shas",
    # Session Spawner
    "BmadSessionSpawner",
    "SessionResult",
    "SMResult",
    "POResult",
    "DevResult",
    "QAResult",
    "run_single_session",
    # Prompt Templates
    "SM_PROMPT_TEMPLATE",
    "PO_PROMPT_TEMPLATE",
    "DEV_PROMPT_TEMPLATE",
    "QA_PROMPT_TEMPLATE",
    # Health Monitoring (v1.1.0)
    "SessionHealthMonitor",
    "SessionHealthStatus",
    # Nodes
    "sm_node",
    "po_node",
    "analysis_node",
    "sdd_pre_validation_node",  # v1.1.0 - Pre-dev SDD
    "dev_node",
    "qa_node",
    "sdd_validation_node",  # Post-QA SDD
    "merge_node",
    "commit_node",
    "fix_node",
    "halt_node",
    "cleanup_node",  # v1.1.0 - Cleanup
    "create_dev_sends",
    "create_qa_sends",
    # Dependency Analyzer
    "analyze_dependencies",
    "StoryDependency",
    "ConflictInfo",
    "AnalysisResult",
    "print_analysis_report",
    # Graph
    "build_graph",
    "compile_graph",
    "run_epic_workflow",
    "resume_workflow",
]

__version__ = "1.1.0"
