# Canvas Learning System - Core Module
# Story 12.H.5: Backend Dedup - Request Cache Infrastructure
# Story 30.4: Agent Memory Mapping Configuration
"""
Core infrastructure modules for Canvas Learning System.

This package contains shared infrastructure components:
- request_cache: Request deduplication cache (Story 12.H.5)
- agent_memory_mapping: Agent to memory type mapping (Story 30.4)
"""

from app.core.request_cache import RequestCache, request_cache
from app.core.agent_memory_mapping import (
    AgentMemoryType,
    AGENT_MEMORY_MAPPING,
    ALL_AGENT_NAMES,
    get_memory_type_for_agent,
    is_memory_enabled_agent,
)

__all__ = [
    "RequestCache",
    "request_cache",
    "AgentMemoryType",
    "AGENT_MEMORY_MAPPING",
    "ALL_AGENT_NAMES",
    "get_memory_type_for_agent",
    "is_memory_enabled_agent",
]
