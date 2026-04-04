"""
Memory Domain Gateway — 学习记忆统一入口

Strangler Fig Pattern: 所有外部调用应通过此 gateway 访问 memory 领域。

包含: memory_service, episode_worker, learning_context_service
"""

from __future__ import annotations

# ── 学习历史 CRUD ──
from app.services.memory_service import (
    MemoryService,
    get_memory_service,
    cleanup_memory_service,
)

# ── Graphiti episode 后台队列 ──
from app.services.episode_worker import (
    GraphitiEpisodeWorker,
    EpisodeTask,
    get_episode_worker,
)

# ── 三层上下文组装（Tier 1/2/3） ──
from app.services.learning_context_service import (
    get_node_context,
    assemble_tier1,
    assemble_tier2,
    format_as_markdown,
)

__all__ = [
    "MemoryService",
    "get_memory_service",
    "cleanup_memory_service",
    "GraphitiEpisodeWorker",
    "EpisodeTask",
    "get_episode_worker",
    "get_node_context",
    "assemble_tier1",
    "assemble_tier2",
    "format_as_markdown",
]
