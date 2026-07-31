# Canvas Learning System - MCP Server
# Story 3.2: MCP Tool Exposure (AC-1, AC-2)
#
# FastAPI-MCP ASGI integration: exposes backend algorithm tools via MCP protocol.
# Mounted at /mcp on the FastAPI app for JSON-RPC 2.0 communication.
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 1]
# [Source: _decisions/ADR-001-dialogue-engine.md — MCP injection via --mcp-config]
# [Source: architecture.md#6-layer-defense — Layer 0: Backend Algorithm Authority]

import logging
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI

logger = logging.getLogger(__name__)

mcp: Any = None


def _patch_fastapi_mcp_anyof_bug() -> None:
    """
    Monkey-patch fastapi-mcp v0.4.0 to fix the anyOf + type schema conflict.

    ROOT CAUSE (fastapi-mcp issue):
    When a Pydantic model has ``Optional[str]`` fields, Pydantic generates JSON Schema
    with ``anyOf: [{type: "string"}, {type: "null"}]`` and NO top-level ``type`` key.
    fastapi-mcp ``convert_openapi_to_mcp_tools()`` sees the missing ``type`` and adds
    ``type="string"`` (extracted from anyOf via ``get_single_param_type_from_schema``).
    This creates an invalid schema with BOTH anyOf and type at the same level.

    EFFECT:
    The MCP client (Claude Code / Claude Desktop) uses Zod for schema validation.
    Zod sees ``type="string"`` and requires a string value. When the AI omits optional
    fields or sends null, Zod rejects with "expected string, received undefined".

    FIX:
    After the original conversion, strip the spurious ``type`` from any property that
    already has ``anyOf``, ``oneOf``, or ``allOf`` composition keywords.
    """
    try:
        import fastapi_mcp.openapi.convert as convert_module
        import mcp.types as types

        _original = convert_module.convert_openapi_to_mcp_tools

        def _patched_convert(
            openapi_schema: Dict[str, Any],
            describe_all_responses: bool = False,
            describe_full_response_schema: bool = False,
        ) -> Tuple[List[types.Tool], Dict[str, Dict[str, Any]]]:
            """Patched: call original, then strip spurious type from anyOf properties."""
            tools, operation_map = _original(
                openapi_schema,
                describe_all_responses=describe_all_responses,
                describe_full_response_schema=describe_full_response_schema,
            )

            composition_keywords = {"anyOf", "oneOf", "allOf"}
            patched_count = 0

            for tool in tools:
                properties = tool.inputSchema.get("properties", {})
                for _prop_name, prop_schema in properties.items():
                    # If a property has both a composition keyword AND "type",
                    # the "type" was spuriously added by fastapi-mcp. Remove it.
                    if isinstance(prop_schema, dict) and "type" in prop_schema:
                        if any(kw in prop_schema for kw in composition_keywords):
                            del prop_schema["type"]
                            patched_count += 1

            if patched_count > 0:
                logger.info(
                    "[MCP] Stripped spurious 'type' from %d anyOf properties across %d tools",
                    patched_count,
                    len(tools),
                )

            return tools, operation_map

        convert_module.convert_openapi_to_mcp_tools = _patched_convert

        # Also patch the local reference in fastapi_mcp.server, because it uses
        # `from fastapi_mcp.openapi.convert import convert_openapi_to_mcp_tools`
        # which creates a bound local reference that wouldn't see our module-level patch.
        import fastapi_mcp.server as server_module

        server_module.convert_openapi_to_mcp_tools = _patched_convert
        logger.info("[MCP] Patched fastapi-mcp anyOf+type schema conflict (v0.4.0 bug)")

    except Exception as e:
        logger.warning("[MCP] Failed to patch fastapi-mcp anyOf bug: %s", e)


def setup_mcp_server(app: FastAPI) -> None:
    """
    Set up the MCP server and register all tools on the FastAPI app.

    Story 3.2 AC-1: FastAPI-MCP ASGI integration at /mcp endpoint.
    P0-2 (2026-07-31): exposes exactly 5 read-only tools; 14 write-side/zombie
    tools are quarantined as 410 stubs (see QUARANTINED_MCP_TOOLS).

    This function uses fastapi-mcp to mount an MCP server that exposes
    all canvas learning tools via the MCP protocol.

    Args:
        app: The FastAPI application instance.
    """
    global mcp
    try:
        from fastapi_mcp import FastApiMCP

        # Patch fastapi-mcp's schema conversion before creating the MCP server.
        # This fixes the anyOf + type conflict that causes "expected string,
        # received undefined" errors in the MCP client (Zod validation).
        _patch_fastapi_mcp_anyof_bug()

        # Register tool endpoints first so they exist when FastApiMCP scans
        _register_tool_routes(app)

        # Create MCP server instance with tag filter.
        # Only routes tagged "MCP Tools" are exposed as MCP tools. Without this
        # filter, FastApiMCP would expose ALL FastAPI routes (health, config,
        # metrics, etc.) as callable MCP tools — a security and API surface risk.
        # S29 fix: include_operations expects List[str] not a function.
        # Use include_tags instead to filter by FastAPI route tag.
        mcp = FastApiMCP(
            app,
            name="canvas-learning-mcp",
            description="Canvas Learning System read-only retrieval tools: "
            "note search, wikilink graph traversal, note reading, "
            "learning memory search, and backend health check.",
            include_tags=["MCP Tools"],
        )

        # Mount MCP server — this exposes /mcp endpoint
        mcp.mount()

        logger.info("[Story 3.2] MCP server mounted at /mcp with canvas-learning tools")

    except ImportError:
        logger.warning(
            "[Story 3.2] fastapi-mcp not installed. MCP server disabled. Install with: pip install fastapi-mcp"
        )
    except Exception as e:
        logger.error(f"[Story 3.2] MCP server setup failed: {e}")


def _register_tool_routes(app: FastAPI) -> None:
    """
    Register MCP tool endpoints as FastAPI routes.

    FastAPI-MCP automatically converts these routes to MCP tools.
    Each route becomes a callable MCP tool with JSON Schema parameters.

    Args:
        app: The FastAPI application instance.
    """
    from app.mcp.tools.memory_tools import (
        SearchMemoriesInput,
        SearchMemoriesOutput,
        search_memories,
    )
    from app.mcp.tools.note_search_tools import (
        NoteSearchInput,
        NoteSearchOutput,
        search_notes,
    )

    # Tag for grouping in OpenAPI docs
    MCP_TAG = "MCP Tools"

    # ═══════════════════════════════════════════════════════════════════════════
    # Memory Tools
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post(
        "/mcp/tools/search_memories",
        response_model=SearchMemoriesOutput,
        tags=[MCP_TAG],
        operation_id="search_memories",
        summary="Search learning memories (Graphiti KG)",
        description="Search the Graphiti learning memory knowledge graph. "
        "Returns relevant learning memories matching the query. "
        "No pipeline token required.",
    )
    async def _search_memories(input: SearchMemoriesInput) -> Dict[str, Any]:
        return await search_memories(
            query=input.query,
            node_id=input.node_id,
            group_id=input.group_id,
            max_results=input.max_results,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Note Search Tool (F2: MVP #10 笔记精准检索返回)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post(
        "/mcp/tools/search_notes",
        response_model=NoteSearchOutput,
        tags=[MCP_TAG],
        operation_id="search_notes",
        summary="Search Vault notes (6-source RAG pipeline)",
        description="Search the user's Vault markdown notes and related sources using "
        "the full RAG pipeline: semantic search (BGE-M3), knowledge graph (Graphiti), "
        "multimodal, and cross-canvas retrieval with fusion and reranking. "
        "Claude should use this tool when it needs to find relevant notes, "
        "examples, or study materials from the user's knowledge base.",
    )
    async def _search_notes(input: NoteSearchInput) -> Dict[str, Any]:
        return await search_notes(
            query=input.query,
            canvas_file=input.canvas_file,
            subject_id=input.subject_id,
            max_results=input.max_results,
            cross_subject=input.cross_subject,
            fusion_strategy=input.fusion_strategy,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Wikilink Tools (Story 1.3: Wikilink MCP 工具注册)
    # ═══════════════════════════════════════════════════════════════════════════

    from app.mcp.tools.wikilink_tools import (
        GetNeighborsInput,
        GetNeighborsOutput,
        ReadNoteInput,
        ReadNoteOutput,
        get_neighbors,
        read_note,
    )

    @app.post(
        "/mcp/tools/get_neighbors",
        response_model=GetNeighborsOutput,
        tags=[MCP_TAG],
        operation_id="get_neighbors",
        summary="Query wikilink neighbors of a note",
        description="Find notes related to a given note via wikilink graph traversal. "
        "Returns N-hop neighbors with title, path, distance, and frontmatter. "
        "Use this when you need to discover related concepts in the vault.",
    )
    async def _get_neighbors(input: GetNeighborsInput) -> Dict[str, Any]:
        return await get_neighbors(input)

    @app.post(
        "/mcp/tools/read_note",
        response_model=ReadNoteOutput,
        tags=[MCP_TAG],
        operation_id="read_note",
        summary="Read a vault note's content",
        description="Read the full markdown content of a specific note in the vault. "
        "Use this after get_neighbors to read the content of related notes.",
    )
    async def _read_note(input: ReadNoteInput) -> Dict[str, Any]:
        return await read_note(input)

    # ═══════════════════════════════════════════════════════════════════════════
    # Infrastructure Tools (Story 1.12: DEPLOYMENT_TOOLS tier)
    # ═══════════════════════════════════════════════════════════════════════════

    from app.mcp.tools.infra_tools import (
        CheckHealthInput,
        CheckHealthOutput,
        check_backend_health,
    )

    @app.post(
        "/mcp/tools/check_backend_health",
        response_model=CheckHealthOutput,
        tags=[MCP_TAG],
        operation_id="check_backend_health",
        summary="Check backend health (DEPLOYMENT_TOOLS)",
        description="Returns detailed health status of all backend components. "
        "Requires user confirmation. Use when diagnosing backend issues.",
    )
    async def _check_health(
        input: CheckHealthInput | None = None,
    ) -> Dict[str, Any]:
        # P16 (轨道 B 2026-07-20): MCP 桥对空 schema 不发 body, 必填 body
        # 导致调用必 422 — body 改可选, 空 body 构造空模型。
        return await check_backend_health(input or CheckHealthInput())

    _register_quarantined_routes(app)

    logger.info(
        "[P0-2] Registered 5 read-only MCP tool routes + %d quarantined (410) stubs",
        len(QUARANTINED_MCP_TOOLS),
    )


# P0-2 MCP 写侧隔离 (2026-07-31 二轮对抗审查, quarantine-first-delete-second):
# 这些工具无任何 vault skill/hook/插件调用方, 且多为无鉴权写侧
# (record_error 绕 2.5.X D15 候选区门禁直写; switch_vault 改全局 vault 指向;
# update_fsrs/update_bkt 写 D0 决策明令只读的后端真相源)。
# 摘除 "MCP Tools" tag + include_in_schema=False → 不再出现在 MCP 工具列表/OpenAPI。
# 遥测范围: 410 + warning 日志只覆盖直接 POST /mcp/tools/* 的裸 HTTP 调用方;
# MCP JSON-RPC 层调用方走 fastapi-mcp "Unknown tool" 路径, 不经此 stub —— 但
# 它们因 tools/list 已无这些工具而天然无法发起调用。观察期内 HTTP 侧
# 零命中 + 多个真实学习 session 无异常后, 方可物理删除实现代码 (Tier B 批次)。
QUARANTINED_MCP_TOOLS = [
    "query_mastery",
    "update_fsrs",
    "update_bkt",
    "generate_question",
    "score_answer",
    "assemble_acp",
    "record_calibration",
    "record_learning_memory",
    "archive_conversation",
    "create_exam_node",
    "record_error",
    "request_hint",
    "skip_question",
    "switch_vault",
]


def _register_quarantined_routes(app: FastAPI) -> None:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    def _make_handler(tool_name: str):
        async def _quarantined(request: Request) -> JSONResponse:
            client = request.client.host if request.client else "unknown"
            logger.warning(
                "[MCP-QUARANTINE] blocked call to quarantined tool '%s' from %s "
                "(P0-2 write-side isolation; see 2026-07-31 审查吸收文档)",
                tool_name,
                client,
            )
            return JSONResponse(
                status_code=410,
                content={
                    "error": "gone",
                    "detail": (
                        f"MCP tool '{tool_name}' is quarantined "
                        "(P0-2 write-side isolation, 2026-07-31). "
                        "Read-only tools remain: search_notes, get_neighbors, "
                        "read_note, search_memories, check_backend_health."
                    ),
                },
            )

        return _quarantined

    for tool_name in QUARANTINED_MCP_TOOLS:
        app.add_api_route(
            f"/mcp/tools/{tool_name}",
            _make_handler(tool_name),
            methods=["POST"],
            include_in_schema=False,
        )
