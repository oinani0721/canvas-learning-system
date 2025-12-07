"""
Worktree Watcher Daemon Module

This module provides automated monitoring of parallel development worktrees
and automatic QA session triggering when dev-complete status is detected.

Components:
- worktree_scanner: Discovers active Git worktrees
- status_watcher: Monitors .worktree-status.yaml files using watchdog
- qa_spawner: Spawns Claude Code QA sessions
- worktree_watcher_daemon: Main daemon orchestrator
"""

__version__ = "1.0.0"
__author__ = "Canvas Learning System"

from .worktree_scanner import WorktreeScanner, WorktreeInfo
from .status_watcher import StatusWatcher, WorktreeStatusHandler
from .qa_spawner import QASessionSpawner, QASession, QASessionState

__all__ = [
    "WorktreeScanner",
    "WorktreeInfo",
    "StatusWatcher",
    "WorktreeStatusHandler",
    "QASessionSpawner",
    "QASession",
    "QASessionState",
]
