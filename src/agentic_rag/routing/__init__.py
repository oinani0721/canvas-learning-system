"""
Agentic RAG Routing Module

Collection of routing functions for conditional edges in StateGraph.

Story 12.9: Quality-based routing
- route_after_quality_check: Route based on quality grade

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from agentic_rag.routing.quality_router import route_after_quality_check

__all__ = ["route_after_quality_check"]
