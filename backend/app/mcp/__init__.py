# Canvas Learning System - MCP Server Package
# Story 3.2: MCP Tool Exposure (AC-1 ~ AC-5)
#
# Provides MCP protocol integration for exposing backend algorithm tools
# to Claude Code CLI via FastAPI-MCP ASGI direct connection.
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md]
# [Source: _decisions/ADR-001-dialogue-engine.md]

from app.mcp.server import setup_mcp_server

__all__ = ["setup_mcp_server"]
