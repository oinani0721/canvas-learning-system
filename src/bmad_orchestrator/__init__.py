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
- audit.py: 执行审计日志模块
- workflow_enforcer.py: 工作流状态机强制执行

✅ Lazy Import Pattern: langgraph-dependent modules loaded on demand
✅ Pre-commit hooks work without langgraph (~100MB savings)

Author: Canvas Learning System Team
Version: 2.1.0
Created: 2025-11-30
Updated: 2025-12-13 (Lazy imports for pre-commit compatibility)
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Lightweight modules - NO langgraph dependency
# These are eagerly imported for backward compatibility
# ═══════════════════════════════════════════════════════════════════════════════

from .audit import (
    AuditEntry,
    ExecutionAuditLog,
    create_audit_log,
)
from .dependency_analyzer import (
    AnalysisResult,
    ConflictInfo,
    StoryDependency,
    analyze_dependencies,
    print_analysis_report,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Lazy imports for langgraph-dependent modules
# These are only loaded when accessed, allowing pre-commit hooks to work
# without installing langgraph in the isolated venv
# ═══════════════════════════════════════════════════════════════════════════════

# Define which names belong to which module for lazy loading
_GRAPH_EXPORTS = frozenset({
    "build_graph",
    "compile_graph",
    "resume_workflow",
    "run_epic_workflow",
})

_NODES_EXPORTS = frozenset({
    "analysis_node",
    "cleanup_node",
    "commit_node",
    "create_dev_sends",
    "create_qa_sends",
    "dev_node",
    "fix_node",
    "halt_node",
    "merge_node",
    "po_node",
    "qa_node",
    "sdd_pre_validation_node",
    "sdd_validation_node",
    "sm_node",
})

_SESSION_SPAWNER_EXPORTS = frozenset({
    "DEV_PROMPT_TEMPLATE",
    "PO_PROMPT_TEMPLATE",
    "QA_PROMPT_TEMPLATE",
    "SM_PROMPT_TEMPLATE",
    "BmadSessionSpawner",
    "DevResult",
    "POResult",
    "QAResult",
    "SessionHealthMonitor",
    "SessionHealthStatus",
    "SessionResult",
    "SMResult",
    "run_single_session",
})

_STATE_EXPORTS = frozenset({
    "BlockerInfo",
    "BmadOrchestratorState",
    "DevOutcome",
    "ExecutionPlan",
    "QAOutcome",
    "SessionInfo",
    "SoTResolution",
    "StoryDraft",
    "create_initial_state",
    "merge_blockers",
    "merge_commit_shas",
    "merge_dev_outcomes",
    "merge_qa_outcomes",
})

# All lazy-loaded exports
_LANGGRAPH_MODULES = _GRAPH_EXPORTS | _NODES_EXPORTS | _SESSION_SPAWNER_EXPORTS | _STATE_EXPORTS


def __getattr__(name: str):
    """
    Lazy import for langgraph-dependent modules.

    This allows scripts that only need lightweight modules (audit, dependency_analyzer)
    to import from bmad_orchestrator without triggering langgraph imports.

    Example:
        # This works without langgraph installed:
        from bmad_orchestrator import AnalysisResult, analyze_dependencies

        # This triggers langgraph import:
        from bmad_orchestrator import build_graph
    """
    if name in _GRAPH_EXPORTS:
        from . import graph
        return getattr(graph, name)
    elif name in _NODES_EXPORTS:
        from . import nodes
        return getattr(nodes, name)
    elif name in _SESSION_SPAWNER_EXPORTS:
        from . import session_spawner
        return getattr(session_spawner, name)
    elif name in _STATE_EXPORTS:
        from . import state
        return getattr(state, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # ──────────────────────────────────────────────────────────────────────────
    # Audit (lightweight - always available)
    # ──────────────────────────────────────────────────────────────────────────
    "AuditEntry",
    "ExecutionAuditLog",
    "create_audit_log",

    # ──────────────────────────────────────────────────────────────────────────
    # Dependency Analyzer (lightweight - always available)
    # ──────────────────────────────────────────────────────────────────────────
    "analyze_dependencies",
    "StoryDependency",
    "ConflictInfo",
    "AnalysisResult",
    "print_analysis_report",

    # ──────────────────────────────────────────────────────────────────────────
    # State (lazy-loaded - requires langgraph)
    # ──────────────────────────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────────────────────
    # Session Spawner (lazy-loaded - requires langgraph)
    # ──────────────────────────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────────────────────
    # Nodes (lazy-loaded - requires langgraph)
    # ──────────────────────────────────────────────────────────────────────────
    "sm_node",
    "po_node",
    "analysis_node",
    "sdd_pre_validation_node",
    "dev_node",
    "qa_node",
    "sdd_validation_node",
    "merge_node",
    "commit_node",
    "fix_node",
    "halt_node",
    "cleanup_node",
    "create_dev_sends",
    "create_qa_sends",

    # ──────────────────────────────────────────────────────────────────────────
    # Graph (lazy-loaded - requires langgraph)
    # ──────────────────────────────────────────────────────────────────────────
    "build_graph",
    "compile_graph",
    "run_epic_workflow",
    "resume_workflow",
]

__version__ = "2.1.0"  # Lazy imports for pre-commit compatibility
