# Canvas Learning System - Backend Clients
"""
Client modules for external services.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Edge-Enhancement]
[Source: docs/prd/sprint-change-proposal-20251208.md - Epic 20]
"""

from app.clients.claude_client import ClaudeClient, get_claude_client, reset_claude_client
from app.clients.graphiti_client import GraphitiEdgeClient, get_graphiti_client

__all__ = [
    "GraphitiEdgeClient",
    "get_graphiti_client",
    "ClaudeClient",
    "get_claude_client",
    "reset_claude_client",
]
