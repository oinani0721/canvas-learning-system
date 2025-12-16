# Canvas Learning System - Agents Router
# Story 15.2: Routing System and APIRouter Configuration
# Story 21.1: 统一位置信息提取 - 连接真实AgentService
# Story 12.A.2: Agent-RAG Bridge Layer - 5源融合上下文注入
"""
Agent invocation router.

Provides 11 endpoints for AI agent operations (decomposition, scoring, explanation).
[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents]
[Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md - Story 21.1]
[Source: docs/stories/story-12.A.2-agent-rag-bridge.md - RAG Integration]
"""

import asyncio
import logging
from typing import Annotated, Any, AsyncGenerator, Dict, List, Optional, Tuple

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: BackgroundTasks)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.dependencies import AgentServiceDep, CanvasServiceDep, ContextEnrichmentServiceDep, RAGServiceDep
from app.services.memory_service import MemoryService
from app.models import (
    DecomposeRequest,
    DecomposeResponse,
    ErrorResponse,
    ExplainRequest,
    ExplainResponse,
    NodeRead,
    NodeScore,
    QuestionDecomposeRequest,
    QuestionDecomposeResponse,
    ScoreRequest,
    ScoreResponse,
    SubQuestion,
    VerificationQuestion,
    VerificationQuestionRequest,
    VerificationQuestionResponse,
)

logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
# APIRouter(prefix, tags, responses) for modular routing
agents_router = APIRouter(
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Canvas or node not found"},
        500: {"model": ErrorResponse, "description": "Agent service error"},
    }
)


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.A.5: MemoryService 依赖注入 - 学习事件自动记录
# [Source: docs/stories/story-12.A.5-learning-event-recording.md]
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_memory_service_for_agents() -> AsyncGenerator[MemoryService, None]:
    """
    Get MemoryService for agents endpoint.

    Uses yield syntax to support resource cleanup after request completion.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)
    [Source: docs/stories/story-12.A.5-learning-event-recording.md#Dev-Notes]
    """
    service = MemoryService()
    try:
        await service.initialize()
        yield service
    finally:
        await service.cleanup()


MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service_for_agents)]


async def _record_learning_event(
    memory_service: MemoryService,
    agent_type: str,
    canvas_path: str,
    node_id: str,
    concept: str,
    score: Optional[int] = None
) -> None:
    """
    后台任务：记录学习事件 (Story 12.A.5)

    - 调用 MemoryService.record_learning_event()
    - 异常静默处理，不影响用户响应 (AC: 4)
    - 非阻塞执行 (AC: 3)

    ✅ Verified from memory_service.py:67-76 (Step 8d Conflict Resolution)
    [Source: docs/stories/story-12.A.5-learning-event-recording.md#实现方案]
    """
    try:
        episode_id = await memory_service.record_learning_event(
            user_id="default",        # TODO: 支持多用户
            canvas_path=canvas_path,  # ✅ 必填
            node_id=node_id,          # ✅ 必填
            concept=concept,          # ✅ 必填
            agent_type=agent_type,    # ✅ 必填 (decompose/explain_*/score)
            score=score               # 可选
        )
        logger.info(f"Story 12.A.5: Recorded learning event: {episode_id} for concept: {concept[:50]}...")
    except Exception as e:
        # AC-4: 静默处理，不影响用户 (记录错误但不抛出)
        logger.error(f"Story 12.A.5: Failed to record learning event: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 21.1: 统一位置信息提取函数
# [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-1]
# ═══════════════════════════════════════════════════════════════════════════════

def extract_node_position(node: Dict[str, Any]) -> Tuple[int, int, int, int]:
    """
    统一提取节点位置信息。

    所有Agent端点使用此函数确保位置提取逻辑一致。

    Args:
        node: Canvas节点数据字典

    Returns:
        Tuple[x, y, width, height] - 位置和尺寸信息

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-1]
    """
    x = int(node.get("x", 0))
    y = int(node.get("y", 0))
    width = int(node.get("width", 400))
    height = int(node.get("height", 200))
    return x, y, width, height


async def get_node_from_canvas(
    canvas_service: CanvasServiceDep,
    canvas_name: str,
    node_id: str
) -> Dict[str, Any]:
    """
    从Canvas中获取指定节点。

    Args:
        canvas_service: Canvas服务实例
        canvas_name: Canvas文件名
        node_id: 目标节点ID

    Returns:
        节点数据字典

    Raises:
        HTTPException: Canvas或节点不存在时抛出404

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-1]
    """
    try:
        canvas_data = await canvas_service.read_canvas(canvas_name)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Canvas not found: {canvas_name}"
        ) from err

    nodes = canvas_data.get("nodes", [])
    for node in nodes:
        if node.get("id") == node_id:
            return node

    raise HTTPException(
        status_code=404,
        detail=f"Node not found: {node_id} in canvas {canvas_name}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.A.2: RAG Context Integration Functions
# [Source: docs/stories/story-12.A.2-agent-rag-bridge.md]
# ═══════════════════════════════════════════════════════════════════════════════

RAG_TIMEOUT_SECONDS = 2.0  # AC4: RAG延迟 < 2s


def format_rag_for_agent(rag_results: List[Dict[str, Any]]) -> str:
    """
    Format RAG results into a readable context string for Agent prompts.

    Converts the 5-source fusion results into a structured text format
    that can be injected into Agent prompts.

    Args:
        rag_results: List of RAG result dicts with source, content, score

    Returns:
        Formatted context string for Agent prompts

    [Source: docs/stories/story-12.A.2-agent-rag-bridge.md#Dev-Notes]
    """
    if not rag_results:
        return ""

    sections = []

    # Group results by source type
    source_groups: Dict[str, List[Dict[str, Any]]] = {}
    for result in rag_results:
        source = result.get("source", "unknown")
        if source not in source_groups:
            source_groups[source] = []
        source_groups[source].append(result)

    # Format each source group
    source_labels = {
        "graphiti": "🔗 知识图谱关联",
        "lancedb": "📊 语义相似内容",
        "multimodal": "🖼️ 图表/公式",
        "textbook": "📖 教材参考",
        "cross_canvas": "🗂️ 跨Canvas关联",
    }

    for source, results in source_groups.items():
        label = source_labels.get(source, f"📌 {source}")
        content_lines = []
        for r in results[:3]:  # Limit to 3 results per source
            content = r.get("content", "")
            if content:
                content_lines.append(f"  - {content[:200]}{'...' if len(content) > 200 else ''}")
        if content_lines:
            sections.append(f"{label}:\n" + "\n".join(content_lines))

    if not sections:
        return ""

    return "## 相关上下文（来自RAG检索）\n\n" + "\n\n".join(sections)


async def get_rag_context_with_timeout(
    rag_service: RAGServiceDep,
    query: str,
    canvas_name: str,
    timeout: float = RAG_TIMEOUT_SECONDS
) -> Optional[str]:
    """
    Execute RAG query with timeout and graceful degradation.

    AC4: RAG延迟 < 2s（可接受范围）
    AC5: RAG服务不可用时优雅降级（继续执行但不带上下文）

    Args:
        rag_service: RAG service instance
        query: Query string (node content)
        canvas_name: Canvas file name for context
        timeout: Timeout in seconds (default: 2.0)

    Returns:
        Formatted RAG context string, or None if unavailable/timeout

    [Source: docs/stories/story-12.A.2-agent-rag-bridge.md#Task-3]
    """
    # AC5: Check if RAG service is available
    if not rag_service.is_available:
        logger.warning(f"RAG service not available: {rag_service.import_error}")
        return None

    try:
        # AC4: 2-second timeout
        rag_result = await asyncio.wait_for(
            rag_service.query_with_fallback(
                query=query,
                canvas_file=canvas_name,
                fusion_strategy="weighted"
            ),
            timeout=timeout
        )

        # Extract and format results
        reranked = rag_result.get("reranked_results", [])
        if not reranked:
            # Fallback to fused results if no reranked
            reranked = rag_result.get("fused_results", [])

        if reranked:
            formatted = format_rag_for_agent(reranked)
            logger.info(f"RAG context retrieved: {len(reranked)} results, {len(formatted)} chars")
            return formatted

        logger.debug("RAG query returned no results")
        return None

    except asyncio.TimeoutError:
        # AC4/AC5: Graceful degradation on timeout
        logger.warning(f"RAG query timeout ({timeout}s), continuing without RAG context")
        return None

    except Exception as e:
        # AC5: Graceful degradation on any error
        logger.warning(f"RAG query failed, continuing without context: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Decomposition Endpoints (2)
# [Source: specs/api/fastapi-backend-api.openapi.yml#Agent Endpoints]
# ═══════════════════════════════════════════════════════════════════════════════

@agents_router.post(
    "/decompose/basic",
    response_model=DecomposeResponse,
    summary="Basic concept decomposition",
    operation_id="decompose_basic",
)
async def decompose_basic(
    request: DecomposeRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5: 后台任务支持
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5: 学习事件记录
) -> DecomposeResponse:
    """
    Perform basic concept decomposition on a node.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID to decompose

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1decompose~1basic]
    [Source: specs/data/decompose-request.schema.json]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    try:
        # Story 25.2: Get enriched context (includes textbook references)
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: {request.node_id} in canvas {request.canvas_name}"
        ) from err

    # Story 12.A.2: Get RAG context with timeout (AC4: <2s, AC5: graceful degradation)
    rag_context = await get_rag_context_with_timeout(
        rag_service=rag_service,
        query=enriched.target_content,
        canvas_name=request.canvas_name
    )

    # Story 25.2 AC5: Log textbook context usage + Story 12.A.2: Log RAG context
    logger.info(
        f"decompose_basic: canvas={request.canvas_name}, node={request.node_id}, "
        f"pos=({enriched.x},{enriched.y}), has_textbook_refs={enriched.has_textbook_refs}, "
        f"has_rag_context={rag_context is not None}"
    )

    try:
        # Story 25.2: Pass enriched content with textbook context embedded
        # Story 12.A.2: Pass rag_context to AgentService
        result = await agent_service.decompose_basic(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=f"{enriched.target_content}\n\n{enriched.enriched_context}" if enriched.enriched_context else enriched.target_content,
            source_x=enriched.x,
            source_y=enriched.y,
            rag_context=rag_context,  # Story 12.A.2: RAG context injection
        )

        # Story 12.A.5: 后台记录学习事件 (AC: 1, 3)
        background_tasks.add_task(
            _record_learning_event,
            memory_service=memory_service,
            agent_type="decompose_basic",
            canvas_path=request.canvas_name,
            node_id=request.node_id,
            concept=enriched.target_content[:100]
        )

        # 转换为响应模型
        return DecomposeResponse(
            questions=result.get("questions", []),
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
        )
    except Exception as e:
        logger.error(f"decompose_basic failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


@agents_router.post(
    "/decompose/deep",
    response_model=DecomposeResponse,
    summary="Deep concept decomposition",
    operation_id="decompose_deep",
)
async def decompose_deep(
    request: DecomposeRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5: 后台任务支持
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5: 学习事件记录
) -> DecomposeResponse:
    """
    Perform deep concept decomposition on a node.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID for deep decomposition

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1decompose~1deep]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    try:
        # Story 25.2: Get enriched context (includes textbook references)
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: {request.node_id} in canvas {request.canvas_name}"
        ) from err

    # Story 12.A.2: Get RAG context with timeout (AC4: <2s, AC5: graceful degradation)
    rag_context = await get_rag_context_with_timeout(
        rag_service=rag_service,
        query=enriched.target_content,
        canvas_name=request.canvas_name
    )

    # Story 25.2 AC5: Log textbook context usage + Story 12.A.2: Log RAG context
    logger.info(
        f"decompose_deep: canvas={request.canvas_name}, node={request.node_id}, "
        f"pos=({enriched.x},{enriched.y}), has_textbook_refs={enriched.has_textbook_refs}, "
        f"has_rag_context={rag_context is not None}"
    )

    try:
        # Story 25.2: Pass enriched content with textbook context embedded
        # Story 12.A.2: Pass rag_context to AgentService
        result = await agent_service.decompose_deep(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=f"{enriched.target_content}\n\n{enriched.enriched_context}" if enriched.enriched_context else enriched.target_content,
            source_x=enriched.x,
            source_y=enriched.y,
            rag_context=rag_context,  # Story 12.A.2: RAG context injection
        )

        # Story 12.A.5: 后台记录学习事件 (AC: 1, 3)
        background_tasks.add_task(
            _record_learning_event,
            memory_service=memory_service,
            agent_type="decompose_deep",
            canvas_path=request.canvas_name,
            node_id=request.node_id,
            concept=enriched.target_content[:100]
        )

        return DecomposeResponse(
            questions=result.get("questions", []),
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
        )
    except Exception as e:
        logger.error(f"decompose_deep failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


# ═══════════════════════════════════════════════════════════════════════════════
# Scoring Endpoint (1)
# [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1score]
# ═══════════════════════════════════════════════════════════════════════════════

@agents_router.post(
    "/score",
    response_model=ScoreResponse,
    summary="Score user understanding",
    operation_id="score_understanding",
)
async def score_understanding(
    request: ScoreRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5: 后台任务支持
    agent_service: AgentServiceDep,
    canvas_service: CanvasServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5: 学习事件记录
) -> ScoreResponse:
    """
    Score user's understanding based on their explanations.

    - **canvas_name**: Canvas file name
    - **node_ids**: List of node IDs to score

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1score]
    [Source: specs/data/node-score.schema.json]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    # Story 12.A.2: Get RAG context for first node (for scoring context)
    first_node_id = request.node_ids[0] if request.node_ids else ""
    rag_context = None
    if first_node_id:
        rag_context = await get_rag_context_with_timeout(
            rag_service=rag_service,
            query=first_node_id,
            canvas_name=request.canvas_name
        )

    logger.info(
        f"score_understanding: canvas={request.canvas_name}, nodes={request.node_ids}, "
        f"has_rag_context={rag_context is not None}"
    )

    try:
        result = await agent_service.score_node(
            canvas_name=request.canvas_name,
            node_ids=request.node_ids,
            rag_context=rag_context,  # Story 12.A.2: RAG context injection
        )

        # 转换为响应模型
        scores = []
        for score_data in result.get("scores", []):
            scores.append(NodeScore(
                node_id=score_data.get("node_id", ""),
                accuracy=score_data.get("accuracy", 0.0),
                imagery=score_data.get("imagery", 0.0),
                completeness=score_data.get("completeness", 0.0),
                originality=score_data.get("originality", 0.0),
                total=score_data.get("total", 0.0),
                new_color=score_data.get("new_color", "3"),
            ))

            # Story 12.A.5: 后台记录学习事件 (每个评分节点)
            background_tasks.add_task(
                _record_learning_event,
                memory_service=memory_service,
                agent_type="score",
                canvas_path=request.canvas_name,
                node_id=score_data.get("node_id", first_node_id),
                concept=score_data.get("concept", "understanding"),
                score=int(score_data.get("total", 0))
            )

        return ScoreResponse(scores=scores)
    except Exception as e:
        logger.error(f"score_understanding failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


# ═══════════════════════════════════════════════════════════════════════════════
# Explanation Endpoints (6)
# [Source: specs/api/fastapi-backend-api.openapi.yml#Agent Endpoints]
# ═══════════════════════════════════════════════════════════════════════════════

async def _call_explanation(
    request: ExplainRequest,
    explanation_type: str,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    background_tasks: BackgroundTasks,  # Story 12.A.5: 后台任务支持
    memory_service: MemoryServiceDep,  # Story 12.A.5: 学习事件记录
) -> ExplainResponse:
    """
    统一解释调用辅助函数。

    [Story 21.1: 统一位置信息提取]
    [Story 21.2: 使用ContextEnrichmentService获取邻居上下文]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    # Story 25.2: Get enriched context (includes textbook references)
    try:
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: canvas={request.canvas_name}, node_id={request.node_id}"
        ) from err

    # Story 12.A.2: Get RAG context with timeout (AC4: <2s, AC5: graceful degradation)
    rag_context = await get_rag_context_with_timeout(
        rag_service=rag_service,
        query=enriched.target_content,
        canvas_name=request.canvas_name
    )

    # Story 25.2 AC5: Log textbook context usage + Story 12.A.2: Log RAG context
    logger.info(
        f"explain_{explanation_type}: canvas={request.canvas_name}, node={request.node_id}, "
        f"pos=({enriched.x},{enriched.y},{enriched.width},{enriched.height}), "
        f"has_textbook_refs={enriched.has_textbook_refs}, has_rag_context={rag_context is not None}"
    )

    try:
        # Story 25.2: Pass enriched context to agent (includes textbook refs per AC3)
        result = await agent_service.generate_explanation(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=enriched.target_content,
            adjacent_context=enriched.enriched_context,  # Includes textbook refs per AC3
            explanation_type=explanation_type,
            source_x=enriched.x,
            source_y=enriched.y,
            source_width=enriched.width,
            source_height=enriched.height,
            rag_context=rag_context,  # Story 12.A.2: RAG context injection
        )

        # Story 12.A.5: 后台记录学习事件 (AC: 1, 3)
        background_tasks.add_task(
            _record_learning_event,
            memory_service=memory_service,
            agent_type=f"explain_{explanation_type}",
            canvas_path=request.canvas_name,
            node_id=request.node_id,
            concept=enriched.target_content[:100]
        )

        return ExplainResponse(
            explanation=result.get("explanation", ""),
            created_node_id=result.get("created_node_id", ""),
        )
    except Exception as e:
        logger.error(f"explain_{explanation_type} failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


@agents_router.post(
    "/explain/oral",
    response_model=ExplainResponse,
    summary="Oral-style explanation",
    operation_id="explain_oral",
)
async def explain_oral(
    request: ExplainRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5
) -> ExplainResponse:
    """
    Generate oral-style explanation for a concept.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1oral]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    return await _call_explanation(request, "oral", agent_service, context_service, rag_service, background_tasks, memory_service)


@agents_router.post(
    "/explain/clarification",
    response_model=ExplainResponse,
    summary="Clarification path generation",
    operation_id="explain_clarification",
)
async def explain_clarification(
    request: ExplainRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5
) -> ExplainResponse:
    """
    Generate clarification path for a concept.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1clarification]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    return await _call_explanation(request, "clarification", agent_service, context_service, rag_service, background_tasks, memory_service)


@agents_router.post(
    "/explain/comparison",
    response_model=ExplainResponse,
    summary="Comparison table generation",
    operation_id="explain_comparison",
)
async def explain_comparison(
    request: ExplainRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5
) -> ExplainResponse:
    """
    Generate comparison table for a concept.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1comparison]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    return await _call_explanation(request, "comparison", agent_service, context_service, rag_service, background_tasks, memory_service)


@agents_router.post(
    "/explain/memory",
    response_model=ExplainResponse,
    summary="Memory anchor generation",
    operation_id="explain_memory",
)
async def explain_memory(
    request: ExplainRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5
) -> ExplainResponse:
    """
    Generate memory anchor for a concept.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1memory]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    return await _call_explanation(request, "memory", agent_service, context_service, rag_service, background_tasks, memory_service)


@agents_router.post(
    "/explain/four-level",
    response_model=ExplainResponse,
    summary="Four-level explanation",
    operation_id="explain_four_level",
)
async def explain_four_level(
    request: ExplainRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5
) -> ExplainResponse:
    """
    Generate four-level progressive explanation.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1four-level]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    return await _call_explanation(request, "four-level", agent_service, context_service, rag_service, background_tasks, memory_service)


@agents_router.post(
    "/explain/example",
    response_model=ExplainResponse,
    summary="Example-based teaching",
    operation_id="explain_example",
)
async def explain_example(
    request: ExplainRequest,
    background_tasks: BackgroundTasks,  # Story 12.A.5
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
    memory_service: MemoryServiceDep,  # Story 12.A.5
) -> ExplainResponse:
    """
    Generate example-based teaching content.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1example]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    [Story 12.A.5: 学习事件自动记录]
    """
    return await _call_explanation(request, "example", agent_service, context_service, rag_service, background_tasks, memory_service)


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.A.6: verification-question and question-decomposition Agents
# [Source: docs/stories/story-12.A.6-complete-agents.md]
# ═══════════════════════════════════════════════════════════════════════════════

@agents_router.post(
    "/verification/question",
    response_model=VerificationQuestionResponse,
    summary="Generate verification questions",
    operation_id="generate_verification_questions",
)
async def generate_verification_questions(
    request: VerificationQuestionRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
) -> VerificationQuestionResponse:
    """
    Generate verification questions for a concept node.

    Creates 2-4 verification questions based on the node content,
    suitable for testing understanding of red/purple nodes.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID (typically red or purple)

    [Source: docs/stories/story-12.A.6-complete-agents.md#AC1]
    [Source: .claude/agents/verification-question-agent.md]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    """
    # AC3a: Get enriched context with adjacent nodes
    try:
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: canvas={request.canvas_name}, node_id={request.node_id}"
        ) from err

    # Story 12.A.2: Get RAG context with timeout (AC4: <2s, AC5: graceful degradation)
    rag_context = await get_rag_context_with_timeout(
        rag_service=rag_service,
        query=enriched.target_content,
        canvas_name=request.canvas_name
    )

    logger.info(
        f"generate_verification_questions: canvas={request.canvas_name}, node={request.node_id}, "
        f"pos=({enriched.x},{enriched.y},{enriched.width},{enriched.height}), "
        f"has_rag_context={rag_context is not None}"
    )

    try:
        # AC3: Call agent service with context enrichment
        # Story 12.A.2: Pass rag_context to AgentService
        result = await agent_service.generate_verification_questions(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=enriched.target_content,
            node_type=enriched.color or "red",
            adjacent_context=enriched.enriched_context,
            source_x=enriched.x,
            source_y=enriched.y,
            source_width=enriched.width,
            source_height=enriched.height,
            rag_context=rag_context,  # Story 12.A.2: RAG context injection
        )

        # Convert to response model
        from datetime import datetime
        questions = [
            VerificationQuestion(
                source_node_id=q.get("source_node_id", request.node_id),
                question_text=q.get("question_text", ""),
                question_type=q.get("question_type", "检验型"),
                difficulty=q.get("difficulty", "基础"),
                guidance=q.get("guidance"),
                rationale=q.get("rationale", ""),
            )
            for q in result.get("questions", [])
        ]

        return VerificationQuestionResponse(
            questions=questions,
            concept=result.get("concept", enriched.target_content[:100]),
            generated_at=datetime.now(),
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
        )
    except Exception as e:
        logger.error(f"generate_verification_questions failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


@agents_router.post(
    "/decompose/question",
    response_model=QuestionDecomposeResponse,
    summary="Decompose question into sub-questions",
    operation_id="decompose_question",
)
async def decompose_question(
    request: QuestionDecomposeRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
    rag_service: RAGServiceDep,  # Story 12.A.2: RAG integration
) -> QuestionDecomposeResponse:
    """
    Decompose a verification question into 2-5 sub-questions.

    Takes a purple node (verification question) and creates smaller,
    more focused sub-questions to guide understanding.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID (purple verification question)

    [Source: docs/stories/story-12.A.6-complete-agents.md#AC2]
    [Source: .claude/agents/question-decomposition.md]
    [Story 12.A.2: Agent-RAG Bridge Layer]
    """
    # AC3a: Get enriched context with adjacent nodes
    try:
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: canvas={request.canvas_name}, node_id={request.node_id}"
        ) from err

    # Story 12.A.2: Get RAG context with timeout (AC4: <2s, AC5: graceful degradation)
    rag_context = await get_rag_context_with_timeout(
        rag_service=rag_service,
        query=enriched.target_content,
        canvas_name=request.canvas_name
    )

    logger.info(
        f"decompose_question: canvas={request.canvas_name}, node={request.node_id}, "
        f"pos=({enriched.x},{enriched.y},{enriched.width},{enriched.height}), "
        f"has_rag_context={rag_context is not None}"
    )

    try:
        # AC3: Call agent service with context enrichment
        # Story 12.A.2: Pass rag_context to AgentService
        result = await agent_service.decompose_question(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=enriched.target_content,
            user_understanding="",  # Will be enriched from adjacent yellow nodes
            adjacent_context=enriched.enriched_context,
            source_x=enriched.x,
            source_y=enriched.y,
            source_width=enriched.width,
            source_height=enriched.height,
            rag_context=rag_context,  # Story 12.A.2: RAG context injection
        )

        # Convert to response model
        questions = [
            SubQuestion(
                text=q.get("text", ""),
                type=q.get("type", "检验型"),
                guidance=q.get("guidance", ""),
            )
            for q in result.get("questions", [])
        ]

        return QuestionDecomposeResponse(
            questions=questions,
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
        )
    except Exception as e:
        logger.error(f"decompose_question failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e
