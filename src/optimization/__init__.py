# Canvas Learning System - Optimization Module
# ✅ Verified from Architecture Doc (performance-monitoring-architecture.md:336-398)
# [Source: docs/stories/17.4.story.md - Story 17.4 Performance Optimization]
"""
Performance optimization components for Canvas Learning System.

Components:
- canvas_cache: Canvas file read optimization (orjson + lru_cache)
- batch_writer: Canvas batch write optimization
- resource_aware_scheduler: Resource-aware parallel scheduling

[Source: docs/architecture/performance-monitoring-architecture.md:336-398]
"""

from .batch_writer import BatchCanvasWriter
from .canvas_cache import (
    CacheConfig,
    clear_canvas_cache,
    get_cache_stats,
    read_canvas,
    read_canvas_cached,
)
from .resource_aware_scheduler import ResourceAwareScheduler

__all__ = [
    "read_canvas_cached",
    "read_canvas",
    "clear_canvas_cache",
    "get_cache_stats",
    "CacheConfig",
    "BatchCanvasWriter",
    "ResourceAwareScheduler",
]
