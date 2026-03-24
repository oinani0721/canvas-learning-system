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
from typing import Any, Dict

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_mcp_server(app: FastAPI) -> None:
    """
    Set up the MCP server and register all tools on the FastAPI app.

    Story 3.2 AC-1: FastAPI-MCP ASGI integration at /mcp endpoint.
    Story 3.2 AC-2: 10+ standardized MCP tools with JSON Schema.

    This function uses fastapi-mcp to mount an MCP server that exposes
    all canvas learning tools via the MCP protocol.

    Args:
        app: The FastAPI application instance.
    """
    try:
        from fastapi_mcp import FastApiMCP

        # Register tool endpoints first so they exist when FastApiMCP scans
        _register_tool_routes(app)

        # Create MCP server instance with route prefix filter.
        # Only /mcp/tools/* routes are exposed as MCP tools. Without this
        # filter, FastApiMCP would expose ALL FastAPI routes (health, config,
        # metrics, etc.) as callable MCP tools — a security and API surface risk.
        def _include_mcp_tools_only(route) -> bool:
            """Only include routes under /mcp/tools/ as MCP tools."""
            path = getattr(route, "path", "")
            return path.startswith("/mcp/tools/")

        mcp = FastApiMCP(
            app,
            name="canvas-learning-mcp",
            description="Canvas Learning System backend tools for mastery tracking, "
            "examination, scoring, memory search, and canvas operations.",
            include_operations=_include_mcp_tools_only,
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
    from app.mcp.tools.conversation_tools import (
        ArchiveConversationInput,
        ArchiveConversationOutput,
        CreateExamNodeInput,
        CreateExamNodeOutput,
        archive_conversation,
        create_exam_node,
    )
    from app.mcp.tools.error_tools import (
        RecordErrorInput,
        RecordErrorOutput,
        record_error,
    )
    from app.mcp.tools.exam_tools import (
        AssembleAcpInput,
        AssembleAcpOutput,
        GenerateQuestionInput,
        GenerateQuestionOutput,
        ScoreAnswerInput,
        ScoreAnswerOutput,
        assemble_acp,
        generate_question,
        score_answer,
    )
    from app.mcp.tools.mastery_tools import (
        QueryMasteryInput,
        QueryMasteryOutput,
        UpdateBktInput,
        UpdateBktOutput,
        UpdateFsrsInput,
        UpdateFsrsOutput,
        query_mastery,
        update_bkt,
        update_fsrs,
    )
    from app.mcp.tools.memory_tools import (
        RecordCalibrationInput,
        RecordCalibrationOutput,
        RecordLearningMemoryInput,
        RecordLearningMemoryOutput,
        SearchMemoriesInput,
        SearchMemoriesOutput,
        record_calibration,
        record_learning_memory,
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
    # Mastery Tools
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post(
        "/mcp/tools/query_mastery",
        response_model=QueryMasteryOutput,
        tags=[MCP_TAG],
        summary="Query node mastery state (BKT + FSRS)",
        description="Query the mastery state for a specific canvas node. "
        "Returns BKT mastery probability, FSRS parameters, and effective proficiency. "
        "No pipeline token required.",
    )
    async def _query_mastery(input: QueryMasteryInput) -> Dict[str, Any]:
        return await query_mastery(node_id=input.node_id)

    @app.post(
        "/mcp/tools/update_fsrs",
        response_model=UpdateFsrsOutput,
        tags=[MCP_TAG],
        summary="Update FSRS spaced repetition parameters",
        description="Update FSRS parameters after scoring. "
        "Requires pipeline_token from score_answer (enforces step ordering). "
        "Grade: 1=Forgot, 2=Struggled, 3=Correct, 4=Fluent.",
    )
    async def _update_fsrs(input: UpdateFsrsInput) -> Dict[str, Any]:
        return await update_fsrs(
            node_id=input.node_id,
            grade=input.grade,
            session_id=input.session_id,
            pipeline_token=input.pipeline_token,
        )

    @app.post(
        "/mcp/tools/update_bkt",
        response_model=UpdateBktOutput,
        tags=[MCP_TAG],
        summary="Update BKT mastery probability",
        description="Update Bayesian Knowledge Tracing mastery probability. "
        "Requires pipeline_token from score_answer (enforces step ordering).",
    )
    async def _update_bkt(input: UpdateBktInput) -> Dict[str, Any]:
        return await update_bkt(
            node_id=input.node_id,
            is_correct=input.is_correct,
            session_id=input.session_id,
            pipeline_token=input.pipeline_token,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Exam Tools
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post(
        "/mcp/tools/generate_question",
        response_model=GenerateQuestionOutput,
        tags=[MCP_TAG],
        summary="Generate a question for a concept node",
        description="Generate a question based on node content and mastery level. "
        "Returns a pipeline_token that must be passed to score_answer. "
        "This is the entry point of the exam pipeline.",
    )
    async def _generate_question(input: GenerateQuestionInput) -> Dict[str, Any]:
        return await generate_question(
            node_id=input.node_id,
            session_id=input.session_id,
            difficulty=input.difficulty,
            question_type=input.question_type,
            exam_id=input.exam_id,
            exam_mode=input.exam_mode,
            source_canvas_id=input.source_canvas_id,
        )

    @app.post(
        "/mcp/tools/score_answer",
        response_model=ScoreAnswerOutput,
        tags=[MCP_TAG],
        summary="Score a student's answer (AutoSCORE)",
        description="Score a student's answer using AutoSCORE evaluation. "
        "Requires pipeline_token from generate_question. "
        "Returns a new pipeline_token for update_fsrs/update_bkt.",
    )
    async def _score_answer(input: ScoreAnswerInput) -> Dict[str, Any]:
        return await score_answer(
            node_id=input.node_id,
            session_id=input.session_id,
            question_id=input.question_id,
            student_answer=input.student_answer,
            pipeline_token=input.pipeline_token,
        )

    @app.post(
        "/mcp/tools/assemble_acp",
        response_model=AssembleAcpOutput,
        tags=[MCP_TAG],
        summary="Assemble Assessment Context Package",
        description="Assemble an ACP data bundle for a node containing concept content, "
        "related concepts, mastery level, and learning history. "
        "No pipeline token required.",
    )
    async def _assemble_acp(input: AssembleAcpInput) -> Dict[str, Any]:
        return await assemble_acp(
            node_id=input.node_id,
            include_related=input.include_related,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Memory Tools
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post(
        "/mcp/tools/search_memories",
        response_model=SearchMemoriesOutput,
        tags=[MCP_TAG],
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

    @app.post(
        "/mcp/tools/record_calibration",
        response_model=RecordCalibrationOutput,
        tags=[MCP_TAG],
        summary="Record calibration data (metacognition)",
        description="Record a calibration data point for metacognitive tracking. "
        "Captures the gap between predicted and actual performance. "
        "No pipeline token required.",
    )
    async def _record_calibration(input: RecordCalibrationInput) -> Dict[str, Any]:
        return await record_calibration(
            node_id=input.node_id,
            session_id=input.session_id,
            predicted_score=input.predicted_score,
            actual_score=input.actual_score,
            question_type=input.question_type,
            difficulty=input.difficulty,
        )

    @app.post(
        "/mcp/tools/record_learning_memory",
        response_model=RecordLearningMemoryOutput,
        tags=[MCP_TAG],
        summary="Record learning memory (Observer write path)",
        description=(
            "Record a student learning event (misconception, problem trap, "
            "logical fallacy, guided thinking) to the Graphiti knowledge graph. "
            "Call when you detect student misunderstanding during dialogue. "
            "No pipeline token required. Max 2 calls per turn."
        ),
    )
    async def _record_learning_memory(input: RecordLearningMemoryInput) -> Dict[str, Any]:
        return await record_learning_memory(
            node_id=input.node_id,
            entity_type=input.entity_type,
            concept=input.concept,
            topic=input.topic,
            details=input.details,
            severity=input.severity,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Conversation Tools
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post(
        "/mcp/tools/archive_conversation",
        response_model=ArchiveConversationOutput,
        tags=[MCP_TAG],
        summary="Archive a completed conversation",
        description="Archive a conversation session to the learning memory system. "
        "Stores summary and key insights for future retrieval. "
        "No pipeline token required.",
    )
    async def _archive_conversation(input: ArchiveConversationInput) -> Dict[str, Any]:
        return await archive_conversation(
            node_id=input.node_id,
            session_id=input.session_id,
            summary=input.summary,
            key_insights=input.key_insights,
            mastery_change=input.mastery_change,
        )

    @app.post(
        "/mcp/tools/create_exam_node",
        response_model=CreateExamNodeOutput,
        tags=[MCP_TAG],
        summary="Create an exam node on the canvas",
        description="Create a new exam/verification node on the canvas "
        "linked to a source concept node via an edge. "
        "No pipeline token required.",
    )
    async def _create_exam_node(input: CreateExamNodeInput) -> Dict[str, Any]:
        return await create_exam_node(
            canvas_id=input.canvas_id,
            source_node_id=input.source_node_id,
            exam_title=input.exam_title,
            position_x=input.position_x,
            position_y=input.position_y,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Error Classification Tools (Story 3.6)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post(
        "/mcp/tools/record_error",
        response_model=RecordErrorOutput,
        tags=[MCP_TAG],
        summary="Record and classify a student error (4-type)",
        description="Record a student understanding error detected during dialogue. "
        "Automatically classifies into 4 types (problem_framing, reasoning_fallacy, "
        "knowledge_gap, superficial) and maps to a differentiated remedy strategy. "
        "No pipeline token required.",
    )
    async def _record_error(input: RecordErrorInput) -> Dict[str, Any]:
        return await record_error(
            node_id=input.node_id,
            session_id=input.session_id,
            error_description=input.error_description,
            context=input.context,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Exam Hint + Skip Tools (Story 6.6)
    # ═══════════════════════════════════════════════════════════════════════════

    from app.models.exam_models import (  # noqa: I001
        HintRequest as HintRequestModel,
        HintResponse as HintResponseModel,
        SkipRequest as SkipRequestModel,
        SkipResponse as SkipResponseModel,
    )

    @app.post(
        "/mcp/tools/request_hint",
        response_model=HintResponseModel,
        tags=[MCP_TAG],
        summary="Request a progressive hint (Chain-of-Hints Level 1-4)",
        description="Generate a hint at the requested level for the current exam question. "
        "Level 1=direction, 2=keyword, 3=framework, 4=scaffolded guide. "
        "Uses LLM with level-specific prompt templates. "
        "Story 6.6 AC-1, AC-3, AC-6.",
    )
    async def _request_hint(input: HintRequestModel) -> Dict[str, Any]:
        from app.services.exam_service import get_exam_service

        svc = get_exam_service()
        result = await svc.generate_hint(input)
        return result.model_dump()

    @app.post(
        "/mcp/tools/skip_question",
        response_model=SkipResponseModel,
        tags=[MCP_TAG],
        summary="Skip current exam question (no BKT/FSRS penalty)",
        description="Skip the current question without penalizing mastery. "
        "BKT p_mastery stays unchanged, FSRS has no rating event. "
        "Story 6.6 AC-4.",
    )
    async def _skip_question(input: SkipRequestModel) -> Dict[str, Any]:
        from app.services.exam_service import get_exam_service

        svc = get_exam_service()
        result = await svc.skip_question(input)
        return result.model_dump()

    # ═══════════════════════════════════════════════════════════════════════════
    # Note Search Tool (F2: MVP #10 笔记精准检索返回)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post(
        "/mcp/tools/search_notes",
        response_model=NoteSearchOutput,
        tags=[MCP_TAG],
        summary="Search Vault notes (6-source RAG pipeline)",
        description="Search the user's Vault markdown notes and related sources using "
        "the full RAG pipeline: semantic search (BGE-M3), knowledge graph (Graphiti), "
        "multimodal, textbook, and cross-canvas retrieval with fusion and reranking. "
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

    logger.info("[Story 3.2] Registered 14 MCP tool routes (incl. F2 search_notes)")
