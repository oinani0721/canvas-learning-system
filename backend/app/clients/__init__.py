# Canvas Learning System - Backend Clients
"""
Client modules for external services.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Edge-Enhancement]
[Source: docs/prd/sprint-change-proposal-20251208.md - Epic 20]
"""

from app.clients.claude_client import (
    ClaudeClient,
    get_claude_client,
    reset_claude_client,
)

# Backward compat aliases (S34 G-FAKE-001)
from app.clients.graphiti_client import (  # noqa: F811
    GraphitiEdgeClient,
    Neo4jEdgeClient,
    get_graphiti_client,
    get_neo4j_edge_client,
)

__all__ = [
    "Neo4jEdgeClient",
    "get_neo4j_edge_client",
    "GraphitiEdgeClient",  # backward compat alias
    "get_graphiti_client",  # backward compat alias
    "ClaudeClient",
    "get_claude_client",
    "reset_claude_client",
]
