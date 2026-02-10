# Canvas Learning System - Agents Router
# Story 15.2: Routing System and APIRouter Configuration
# Story 21.1: 统一位置信息提取 - 连接真实AgentService
# Story 12.A.2: Agent-RAG Bridge Layer - 5源融合上下文注入
# Story 12.E.5: Agent 端点多模态集成 - 图片提取和加载
"""
Agent invocation router.

Provides 11 endpoints for AI agent operations (decomposition, scoring, explanation).
[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents]
[Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md - Story 21.1]
[Source: docs/stories/story-12.A.2-agent-rag-bridge.md - RAG Integration]
[Source: docs/stories/story-12.E.5-agent-multimodal-integration.md - Multimodal]
"""

import asyncio
import base64
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, AsyncGenerator, Dict, List, Optional, Tuple

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: BackgroundTasks)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.config import settings
from app.core.exceptions import CanvasNotFoundException
from app.core.request_cache import request_cache
from app.dependencies import AgentServiceDep, CanvasServiceDep, ContextEnrichmentServiceDep, RAGServiceDep
from app.models import (
    # Story 31.3: Recommend Action
    ActionTrend,
    ActionType,
    AlternativeAgent,
    # Story 12.G.3: Agent Health Check
    AgentHealthCheckResponse,
    AgentHealthChecks,
    AgentHealthStatus,
    ApiTestResult,
    DecomposeRequest,
    DecomposeResponse,
    EdgeRead,  # Story 12.M.2: For created_edges in DecomposeResponse
    ErrorResponse,
    ExplainRequest,
    ExplainResponse,
    HistoryContext,
    NodeRead,
    NodeScore,
    PromptTemplateCheck,
    QuestionDecomposeRequest,
    QuestionDecomposeResponse,
    # Story 31.3: Recommend Action
    RecommendActionRequest,
    RecommendActionResponse,
    ScoreRequest,
    ScoreResponse,
    SubQuestion,
    VerificationQuestion,
    VerificationQuestionRequest,
    VerificationQuestionResponse,
)
from app.services.markdown_image_extractor import MarkdownImageExtractor
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.E.5: Multimodal Image Loading Support
# [Source: docs/stories/story-12.E.5-agent-multimodal-integration.md]
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 12.E.5 Technical Details
# MIME types for supported image formats
IMAGE_MIME_TYPES: Dict[str, str] = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
}

# Story 12.E.5 constraints from Gemini API
MAX_IMAGES_PER_REQUEST = 5  # Avoid exceeding token limits
MAX_IMAGE_SIZE_MB = 4.0     # Gemini API limit


async def _load_images_for_agent(
    resolved_refs: List[Dict],
    max_images: int = MAX_IMAGES_PER_REQUEST,
    max_size_mb: float = MAX_IMAGE_SIZE_MB
) -> List[Dict[str, Any]]:
    """加载图片文件并转换为 API 格式 (AC 5.1)

    Story 12.E.5: Agent 端点多模态集成

    ✅ Verified from ADR-011: pathlib 标准化

    Args:
        resolved_refs: resolve_paths() 返回的路径信息列表
            Each dict contains: {"reference": ImageReference, "absolute_path": str|None, "exists": bool}
        max_images: 最大加载图片数量 (default: 5)
        max_size_mb: 单个图片最大尺寸 MB (default: 4.0)

    Returns:
        包含 data (base64) 和 media_type 的字典列表，用于 GeminiClient.call_agent_with_images()
        格式: [{"data": base64_str, "media_type": mime_type, "path": str}, ...]

    [Source: docs/stories/story-12.E.5-agent-multimodal-integration.md#AC-5.1]
    """
    images: List[Dict[str, Any]] = []
    max_size_bytes = int(max_size_mb * 1024 * 1024)

    for ref_info in resolved_refs[:max_images]:
        # AC 5.1: 不存在的图片静默跳过
        if not ref_info.get("exists") or not ref_info.get("absolute_path"):
            continue

        try:
            file_path = Path(ref_info["absolute_path"])
            suffix = file_path.suffix.lower()

            # Check supported format
            mime_type = IMAGE_MIME_TYPES.get(suffix)
            if not mime_type:
                logger.warning(
                    "[Story 12.E.5] Unsupported image format, skipping",
                    extra={"path": str(file_path), "suffix": suffix}
                )
                continue

            # Check file size (AC 5.4: error handling)
            file_size = file_path.stat().st_size
            if file_size > max_size_bytes:
                logger.warning(
                    f"[Story 12.E.5] Image too large ({file_size / (1024*1024):.2f}MB > {max_size_mb}MB), skipping: {file_path}"
                )
                continue

            # Read and encode as base64
            image_data = file_path.read_bytes()
            base64_data = base64.b64encode(image_data).decode('utf-8')

            images.append({
                "data": base64_data,
                "media_type": mime_type,
                "path": str(file_path)
            })

            logger.info(
                f"[Story 12.E.5] Image loaded successfully: {file_path.name} "
                f"({mime_type}, {file_size / 1024:.1f}KB)"
            )

        except PermissionError:
            # AC 5.4: File permission error, skip
            logger.warning(f"[Story 12.E.5] Permission denied reading image: {ref_info.get('absolute_path')}")
            continue
        except OSError as e:
            # AC 5.4: OS-level error (disk, etc.), skip
            logger.warning(f"[Story 12.E.5] OS error reading image: {ref_info.get('absolute_path')}, error: {e}")
            continue
        except Exception as e:
            # AC 5.4: Any other error, log and skip
            logger.error(
                f"[Story 12.E.5] Failed to load image: {ref_info.get('absolute_path')}, error: {e}"
            )
            continue

    return images

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
# Story 12.J.4: UnicodeEncodeError Helper Function
# [Source: docs/stories/story-12.J.4-unicode-exception-handling.md]
# [Source: specs/api/agent-api.openapi.yml#AgentError]
# [Source: ADR-009 - 错误分类体系]
# ═══════════════════════════════════════════════════════════════════════════════


def _create_encoding_error_response(
    e: UnicodeEncodeError,
    endpoint_name: str,
    cache_key: str = ""
) -> HTTPException:
    """
    Story 12.J.4: Create standardized HTTP response for encoding errors.

    Uses ASCII-safe diagnostic information to avoid secondary encoding errors
    when logging on Windows GBK console.

    Args:
        e: The UnicodeEncodeError exception
        endpoint_name: Name of the endpoint where error occurred
        cache_key: Optional cache key for request dedup cleanup

    Returns:
        HTTPException with structured ENCODING_ERROR response

    [Source: specs/api/agent-api.openapi.yml#AgentError]
    [Source: ADR-009 - 错误分类体系: ENCODING_ERROR is RETRYABLE]
    """
    # Story 12.H.5: Cancel request to allow retry
    if cache_key:
        cancel_request(cache_key)

    # AC4: Safe diagnostic info (ASCII only to prevent secondary encoding errors)
    safe_diagnostic = f"position {e.start}"
    if hasattr(e, 'object') and e.start < len(e.object):
        try:
            char_code = ord(e.object[e.start])
            safe_diagnostic += f", char U+{char_code:04X}"
        except Exception:
            pass

    # AC2: ASCII-safe logging (no emoji or special Unicode)
    logger.error(
        f"[Story 12.J.4] Encoding error in {endpoint_name}: {safe_diagnostic}"
    )

    # AC1: Structured response (aligned with AgentError schema)
    return HTTPException(
        status_code=500,
        detail={
            "error_type": "ENCODING_ERROR",
            "message": "Text encoding error - please ensure content uses UTF-8",
            "is_retryable": True,
            "diagnostic": safe_diagnostic,
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.G.3: Agent Health Check Endpoint with TTL Cache
# [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md]
# [Source: ADR-007 - 60-second TTL cache for health check]
# ═══════════════════════════════════════════════════════════════════════════════

# Health check cache (TTL: 60 seconds per ADR-007)
_health_check_cache: Dict[str, Any] = {}
_health_check_cache_time: float = 0.0
HEALTH_CHECK_CACHE_TTL: int = 60  # seconds


@agents_router.get(
    "/health",
    response_model=AgentHealthCheckResponse,
    summary="Agent System Health Check",
    description="Check health status of Agent system components including API key, client initialization, and prompt templates.",
    tags=["health"],
    responses={
        200: {
            "description": "Health check successful",
            "model": AgentHealthCheckResponse,
        },
    },
)
async def get_agent_health(
    agent_service: AgentServiceDep,
    include_api_test: bool = False,
) -> AgentHealthCheckResponse:
    """
    Get Agent system health status.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: health check endpoint)
    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md]
    [Source: specs/api/agent-api.openapi.yml#/paths/~1agents~1health]

    Performs the following checks:
    - API Key configuration (without exposing actual key)
    - GeminiClient initialization status
    - Prompt template availability (12 expected templates)
    - Optional: Actual API call test (when include_api_test=true)

    Health Status Logic:
    - **unhealthy**: API key not configured OR GeminiClient not initialized
    - **degraded**: Some prompt templates missing
    - **healthy**: All checks pass

    Cache: Results are cached for 60 seconds (ADR-007) to reduce system load.

    Args:
        agent_service: Injected AgentService dependency
        include_api_test: Whether to perform actual API call test (default: False)

    Returns:
        AgentHealthCheckResponse with status, checks details, cached flag, and timestamp
    """
    global _health_check_cache, _health_check_cache_time

    current_time = time.time()
    cache_key = f"health_{include_api_test}"

    # Check if cached result is still valid (TTL: 60 seconds per ADR-007)
    if (
        cache_key in _health_check_cache
        and (current_time - _health_check_cache_time) < HEALTH_CHECK_CACHE_TTL
    ):
        cached_result = _health_check_cache[cache_key]
        # Return cached result with cached=True flag
        return AgentHealthCheckResponse(
            status=AgentHealthStatus(cached_result["status"]),
            checks=AgentHealthChecks(
                api_key_configured=cached_result["checks"]["api_key_configured"],
                gemini_client_initialized=cached_result["checks"]["gemini_client_initialized"],
                prompt_templates=PromptTemplateCheck(**cached_result["checks"]["prompt_templates"]),
                api_test=ApiTestResult(**cached_result["checks"]["api_test"]) if cached_result["checks"].get("api_test") else None,
            ),
            cached=True,
            timestamp=datetime.fromisoformat(cached_result["timestamp"]),
        )

    # Perform fresh health check
    health_result = await agent_service.health_check(include_api_test=include_api_test)

    # Cache the result
    _health_check_cache[cache_key] = health_result
    _health_check_cache_time = current_time

    # Return fresh result with cached=False flag
    return AgentHealthCheckResponse(
        status=AgentHealthStatus(health_result["status"]),
        checks=AgentHealthChecks(
            api_key_configured=health_result["checks"]["api_key_configured"],
            gemini_client_initialized=health_result["checks"]["gemini_client_initialized"],
            prompt_templates=PromptTemplateCheck(**health_result["checks"]["prompt_templates"]),
            api_test=ApiTestResult(**health_result["checks"]["api_test"]) if health_result["checks"].get("api_test") else None,
        ),
        cached=False,
        timestamp=datetime.fromisoformat(health_result["timestamp"]),
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
    # [Source: Story 12.I.2 - Remove emoji to fix Windows GBK encoding issue]
    source_labels = {
        "graphiti": "[Graph] 知识图谱关联",
        "lancedb": "[Vector] 语义相似内容",
        "multimodal": "[Media] 图表/公式",
        "textbook": "[Book] 教材参考",
        "cross_canvas": "[Canvas] 跨Canvas关联",
    }

    for source, results in source_groups.items():
        label = source_labels.get(source, f"[{source}]")
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
# Story 12.H.5: Request Deduplication Helper
# [Source: docs/stories/story-12.H.5-backend-dedup.md]
# ═══════════════════════════════════════════════════════════════════════════════


def check_duplicate_request(
    canvas_name: str,
    node_id: str,
    agent_type: str
) -> str:
    """
    Check for duplicate request and mark as in-progress.

    Story 12.H.5: Backend-level request deduplication to prevent
    duplicate Agent requests from being processed simultaneously.

    Per ADR-009: Returns NON_RETRYABLE error (409 Conflict) for duplicates.

    Args:
        canvas_name: Canvas file name (e.g., "math.canvas")
        node_id: Target node ID
        agent_type: Agent type (e.g., "oral", "four-level", "decompose_basic")

    Returns:
        Cache key if dedup is enabled, empty string if disabled

    Raises:
        HTTPException: 409 Conflict if duplicate request detected

    [Source: docs/stories/story-12.H.5-backend-dedup.md#集成到-agentspy]
    """
    # AC6: Can be disabled via environment variable for testing
    if not settings.ENABLE_REQUEST_DEDUP:
        return ""

    cache_key = request_cache.get_key(canvas_name, node_id, agent_type)

    if request_cache.is_duplicate(cache_key):
        # AC2, AC4: Return 409 and log duplicate
        logger.warning(
            f"[Story 12.H.5] Duplicate request rejected: "
            f"canvas={canvas_name}, node={node_id}, agent={agent_type}"
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Duplicate request",
                "message": "相同请求正在处理中，请稍候",
                "canvas_name": canvas_name,
                "node_id": node_id,
                "agent_type": agent_type,
                "is_retryable": False  # Per ADR-009: NON_RETRYABLE
            }
        )

    # Mark as in-progress
    request_cache.mark_in_progress(cache_key)
    return cache_key


def complete_request(cache_key: str) -> None:
    """
    Mark a request as completed in the dedup cache.

    Args:
        cache_key: Cache key from check_duplicate_request()

    [Source: docs/stories/story-12.H.5-backend-dedup.md#Task-3.7]
    """
    if cache_key:
        request_cache.mark_completed(cache_key)


def cancel_request(cache_key: str) -> None:
    """
    Remove a request from the dedup cache (on failure/cancellation).

    This allows immediate retry of the same request after failure.

    Args:
        cache_key: Cache key from check_duplicate_request()

    [Source: docs/stories/story-12.H.5-backend-dedup.md#Task-3.7]
    """
    if cache_key:
        request_cache.remove(cache_key)


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
    [Story 12.H.5: Request Deduplication]
    """
    # Story 12.H.5: Check for duplicate request
    cache_key = check_duplicate_request(
        canvas_name=request.canvas_name,
        node_id=request.node_id,
        agent_type="decompose_basic"
    )

    try:
        # Story 25.2: Get enriched context (includes textbook references)
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
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

        # Story 12.H.5: Mark request as completed on success
        complete_request(cache_key)

        # Story 12.M.2: Include created_edges in response
        return DecomposeResponse(
            questions=result.get("questions", []),
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
            created_edges=[EdgeRead(**e) for e in result.get("created_edges", [])],
        )
    except UnicodeEncodeError as e:
        # Story 12.J.4: Explicit encoding error handling
        raise _create_encoding_error_response(e, "decompose_basic", cache_key) from e
    except Exception as e:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
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
    [Story 12.H.5: Request Deduplication]
    """
    # Story 12.H.5: Check for duplicate request
    cache_key = check_duplicate_request(
        canvas_name=request.canvas_name,
        node_id=request.node_id,
        agent_type="decompose_deep"
    )

    try:
        # Story 25.2: Get enriched context (includes textbook references)
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
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

        # Story 12.H.5: Mark request as completed on success
        complete_request(cache_key)

        # Story 12.M.2: Include created_edges in response
        return DecomposeResponse(
            questions=result.get("questions", []),
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
            created_edges=[EdgeRead(**e) for e in result.get("created_edges", [])],
        )
    except UnicodeEncodeError as e:
        # Story 12.J.4: Explicit encoding error handling
        raise _create_encoding_error_response(e, "decompose_deep", cache_key) from e
    except Exception as e:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
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
    [Story 12.H.5: Request Deduplication]
    """
    # Story 12.A.2: Get RAG context for first node (for scoring context)
    first_node_id = request.node_ids[0] if request.node_ids else ""

    # Story 12.H.5: Check for duplicate request (use first node_id for key)
    cache_key = check_duplicate_request(
        canvas_name=request.canvas_name,
        node_id=first_node_id,
        agent_type="score"
    )

    rag_context = None
    if first_node_id:
        rag_context = await get_rag_context_with_timeout(
            rag_service=rag_service,
            query=first_node_id,
            canvas_name=request.canvas_name
        )

    logger.info(
        f"score_understanding: canvas={request.canvas_name}, nodes={request.node_ids}, "
        f"has_rag_context={rag_context is not None}, has_node_content={request.node_content is not None}"
    )

    # Story 2.8: Build node_contents dict if content is provided from plugin
    node_contents = None
    if request.node_content and request.node_ids:
        # Map the first node_id to the provided content
        node_contents = {request.node_ids[0]: request.node_content}
        logger.info(f"[Story 2.8] Using provided node_content ({len(request.node_content)} chars)")

    try:
        result = await agent_service.score_node(
            canvas_name=request.canvas_name,
            node_ids=request.node_ids,
            node_contents=node_contents,  # Story 2.8: Pass content from plugin
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
                feedback=score_data.get("feedback"),  # Story 2.8: Pass feedback to frontend
                color_action=score_data.get("color_action"),  # Story 2.8: Pass color_action
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

        # Story 12.H.5: Mark request as completed on success
        complete_request(cache_key)

        return ScoreResponse(scores=scores)
    except UnicodeEncodeError as e:
        # Story 12.J.4: Explicit encoding error handling
        raise _create_encoding_error_response(e, "score_understanding", cache_key) from e
    except Exception as e:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
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
    [Story 12.B.1: 增强错误处理]
    [Story 12.H.5: Request Deduplication]
    """
    # Story 12.H.5: Check for duplicate request
    cache_key = check_duplicate_request(
        canvas_name=request.canvas_name,
        node_id=request.node_id,
        agent_type=f"explain_{explanation_type}"
    )

    try:
        # Story 12.B.1: 请求开始日志
        # Story 12.B.2: 记录是否有实时节点内容
        has_realtime_content = bool(request.node_content)
        logger.info(
            f"[Story 12.B.1] explain_{explanation_type} START: "
            f"canvas={request.canvas_name}, node_id={request.node_id}, "
            f"has_realtime_content={has_realtime_content}"
        )

        # Story 25.2: Get enriched context (includes textbook references)
        # Story 12.B.1: 增强异常捕获
        try:
            enriched = await context_service.enrich_with_adjacent_nodes(
                canvas_name=request.canvas_name,
                node_id=request.node_id
            )
        except CanvasNotFoundException as err:
            # Story 12.B.1: Canvas文件不存在
            logger.warning(f"Canvas not found: {request.canvas_name}")
            raise HTTPException(
                status_code=404,
                detail=f"Canvas file not found: {request.canvas_name}. Please check the file path."
            ) from err
        except ValueError as err:
            # Story 12.B.1: 节点不存在
            logger.warning(f"Node not found: {request.node_id} in {request.canvas_name}")
            raise HTTPException(
                status_code=404,
                detail=f"Node not found: {request.node_id} in canvas {request.canvas_name}"
            ) from err
        except Exception as err:
            # Story 12.B.1: 意外的上下文获取错误
            logger.error(f"Context enrichment failed unexpectedly: {err}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read canvas context: {str(err)}"
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

        # Story 12.D.3: Log received node content for debugging trace
        logger.info(
            f"[Story 12.D.3] Received node content: "
            f"node_id={request.node_id}, "
            f"canvas_name={request.canvas_name}, "
            f"has_node_content={bool(request.node_content)}, "
            f"node_content_len={len(request.node_content or '')}, "
            f"content_preview={(request.node_content or '')[:80].replace(chr(10), ' ')}"
        )

        # Story 12.B.2: 优先使用实时传入的节点内容，fallback到磁盘读取的内容
        # 这是核心修复：确保Agent使用正确的节点内容
        effective_content = request.node_content if request.node_content else enriched.target_content

        # ═══════════════════════════════════════════════════════════════════════
        # Story 12.E.5: 多模态图片提取和加载 (AC 5.2)
        # [Source: docs/stories/story-12.E.5-agent-multimodal-integration.md]
        # ═══════════════════════════════════════════════════════════════════════
        images: List[Dict[str, Any]] = []
        try:
            # Extract image references from effective_content
            image_extractor = MarkdownImageExtractor()
            image_refs = image_extractor.extract_all(effective_content)

            if image_refs:
                logger.info(
                    f"[Story 12.E.5] Found {len(image_refs)} image references in content, "
                    f"paths={[ref.path for ref in image_refs[:5]]}"  # Log first 5
                )

                # Get vault_path and canvas_dir for path resolution
                # ✅ Verified from context_enrichment_service.py:289
                vault_path = Path(context_service._canvas_service.canvas_base_path)

                # Canvas file directory (for ./ relative paths)
                # Canvas files are stored in vault_path/{canvas_name}.canvas
                canvas_file_path = vault_path / f"{request.canvas_name}.canvas"
                canvas_dir = canvas_file_path.parent if canvas_file_path.exists() else vault_path

                # Story 12.E.5-fix: Get source file directory for MD embedded images
                # When node is a "file" type pointing to an MD, images should resolve relative to MD location
                source_file_dir = None
                if enriched.source_file_path:
                    source_file_dir = Path(enriched.source_file_path).parent

                # Resolve paths to absolute paths
                resolved_refs = await image_extractor.resolve_paths(
                    image_refs,
                    vault_path=vault_path,
                    canvas_dir=canvas_dir,
                    source_file_dir=source_file_dir  # Story 12.E.5-fix: MD file directory
                )

                # Load images for API
                images = await _load_images_for_agent(resolved_refs)

                logger.info(
                    f"[Story 12.E.5] Images loaded for agent: "
                    f"loaded={len(images)}, total_refs={len(image_refs)}"
                )
            else:
                logger.debug("[Story 12.E.5] No image references found in content")

        except Exception as img_err:
            # AC 5.3, 5.4: Graceful degradation - image extraction failure doesn't block agent
            logger.warning(
                f"[Story 12.E.5] Image extraction/loading failed, continuing without images: {img_err}"
            )
            images = []
        # ═══════════════════════════════════════════════════════════════════════

        # Story 25.2: Pass enriched context to agent (includes textbook refs per AC3)
        # Story 12.B.1: 日志记录Agent调用参数
        # Story 12.B.2: 增加内容来源日志
        content_source = "realtime" if request.node_content else "disk"
        logger.debug(
            f"[Story 12.B.1] Calling agent_service.generate_explanation: "
            f"type={explanation_type}, content_source={content_source}, "
            f"content_len={len(effective_content)}, "
            f"has_adjacent_context={bool(enriched.enriched_context)}, "
            f"has_rag_context={bool(rag_context)}, "
            f"has_images={len(images) > 0}"  # Story 12.E.5: Log image count
        )

        # Story 12.B.2: 如果使用实时内容，记录内容差异
        if request.node_content and enriched.target_content != request.node_content:
            logger.info(
                f"[Story 12.B.2] Using realtime content (differs from disk): "
                f"realtime_len={len(request.node_content)}, disk_len={len(enriched.target_content)}"
            )

        result = await agent_service.generate_explanation(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=effective_content,  # Story 12.B.2: 使用有效内容
            adjacent_context=enriched.enriched_context,  # Includes textbook refs per AC3
            explanation_type=explanation_type,
            source_x=enriched.x,
            source_y=enriched.y,
            source_width=enriched.width,
            source_height=enriched.height,
            rag_context=rag_context,  # Story 12.A.2: RAG context injection
            images=images if images else None,  # Story 12.E.5: Multimodal images
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

        # Story 12.B.1: 成功日志
        logger.info(
            f"[Story 12.B.1] explain_{explanation_type} SUCCESS: "
            f"explanation_len={len(result.get('explanation', ''))}"
        )

        # Story 12.H.5: Mark request as completed on success
        complete_request(cache_key)

        return ExplainResponse(
            explanation=result.get("explanation", ""),
            created_node_id=result.get("created_node_id", ""),
        )
    except HTTPException:
        # Story 12.B.1: 已经是HTTPException，直接重新抛出
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
        raise
    except TimeoutError as e:
        # Story 12.B.1: AI服务超时
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
        logger.error(f"Agent service timeout for {explanation_type}: {e}")
        raise HTTPException(
            status_code=504,
            detail=f"AI service timeout: The {explanation_type} explanation took too long to generate."
        ) from e
    except ConnectionError as e:
        # Story 12.B.1: AI服务连接失败
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
        logger.error(f"Agent service connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable: Cannot connect to the AI provider."
        ) from e
    except UnicodeEncodeError as e:
        # Story 12.J.4: Explicit encoding error handling
        raise _create_encoding_error_response(e, f"explain_{explanation_type}", cache_key) from e
    except Exception as e:
        # Story 12.B.1: 其他Agent错误
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
        error_msg = str(e)
        logger.error(f"explain_{explanation_type} failed: {e}", exc_info=True)

        # 提供更具体的错误信息
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="AI service rate limited: Please try again in a few moments."
            ) from e
        elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="AI service configuration error: API key issue."
            ) from e
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Agent service error: {error_msg}"
            ) from e


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
    [Story 12.H.5: Request Deduplication]
    """
    # Story 12.H.5: Check for duplicate request
    cache_key = check_duplicate_request(
        canvas_name=request.canvas_name,
        node_id=request.node_id,
        agent_type="verification_question"
    )

    # AC3a: Get enriched context with adjacent nodes
    try:
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
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

        # Story 12.H.5: Mark request as completed on success
        complete_request(cache_key)

        return VerificationQuestionResponse(
            questions=questions,
            concept=result.get("concept", enriched.target_content[:100]),
            generated_at=datetime.now(),
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
        )
    except UnicodeEncodeError as e:
        # Story 12.J.4: Explicit encoding error handling
        raise _create_encoding_error_response(e, "generate_verification_questions", cache_key) from e
    except Exception as e:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
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
    [Story 12.H.5: Request Deduplication]
    """
    # Story 12.H.5: Check for duplicate request
    cache_key = check_duplicate_request(
        canvas_name=request.canvas_name,
        node_id=request.node_id,
        agent_type="decompose_question"
    )

    # AC3a: Get enriched context with adjacent nodes
    try:
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
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

        # Story 12.H.5: Mark request as completed on success
        complete_request(cache_key)

        return QuestionDecomposeResponse(
            questions=questions,
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
        )
    except UnicodeEncodeError as e:
        # Story 12.J.4: Explicit encoding error handling
        raise _create_encoding_error_response(e, "decompose_question", cache_key) from e
    except Exception as e:
        # Story 12.H.5: Cancel request to allow retry
        cancel_request(cache_key)
        logger.error(f"decompose_question failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


# ═══════════════════════════════════════════════════════════════════════════════
# Story 31.3: Intelligent Action Recommendation Endpoint
# [Source: docs/stories/31.3.story.md]
# [Source: specs/data/recommend-action-request.schema.json]
# [Source: specs/data/recommend-action-response.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════


def _calculate_trend(scores: List[int]) -> ActionTrend:
    """
    Calculate score trend based on recent scores.

    Story 31.3 AC-31.3.4: Score trend calculation

    Args:
        scores: List of recent scores (most recent first, max 5)

    Returns:
        ActionTrend enum value
    """
    # [Code Review M2 fix]: Require at least 3 scores for meaningful trend detection.
    # With only 2 scores, a single outlier dominates — too noisy for reliable trends.
    if len(scores) < 3:
        return ActionTrend.stable

    # Compare first half average with second half average
    mid = len(scores) // 2
    recent_avg = sum(scores[:mid]) / mid
    older_avg = sum(scores[mid:]) / (len(scores) - mid)

    diff = recent_avg - older_avg
    # 5-point threshold for trend detection
    if diff > 5:
        return ActionTrend.improving
    elif diff < -5:
        return ActionTrend.declining
    return ActionTrend.stable


def _recommend_action_from_score(
    score: int,
    history_context: Optional[HistoryContext] = None,
) -> Tuple[ActionType, str, Optional[str], int, bool, List[AlternativeAgent]]:
    """
    Determine recommended action based on score and history.

    Story 31.3 AC-31.3.3: Score-based recommendation logic
    - score < 60: decompose (基础拆解)
    - score 60-79: explain (解释补充)
    - score >= 80: next (继续学习)

    Story 31.3 AC-31.3.4: Consider history trends

    Args:
        score: Current score (0-100)
        history_context: Optional historical score context

    Returns:
        Tuple of (action, reason, agent, priority, review_suggested, alternatives)
    """
    review_suggested = False
    alternatives: List[AlternativeAgent] = []
    priority = 3

    # Check for declining trend or consecutive low scores
    if history_context:
        if history_context.trend == ActionTrend.declining:
            review_suggested = True
            priority = 1
        if history_context.consecutive_low_count and history_context.consecutive_low_count >= 3:
            review_suggested = True
            priority = 1
            # Suggest memory anchor as alternative for persistent low scores
            alternatives.append(AlternativeAgent(
                agent="/agents/explain/memory",
                reason="尝试记忆锚点帮助建立概念关联"
            ))

    # AC-31.3.3: Score-based action determination
    if score < 60:
        action = ActionType.decompose
        agent = "/agents/decompose/basic"
        reason = "概念理解不足，建议进行基础拆解"
        priority = min(priority, 1)
        if history_context and history_context.consecutive_low_count and history_context.consecutive_low_count >= 3:
            reason = "连续多次低分，建议从基础开始重新学习"
    elif score < 80:
        action = ActionType.explain
        agent = "/agents/explain/oral"
        reason = "需要补充解释加深理解"
        priority = min(priority, 2)
    else:
        action = ActionType.next
        agent = None
        reason = "掌握良好，可以继续下一个概念"
        priority = 3
        # [Bug fix] Preserve review_suggested=True if history analysis already set it.
        # AC-31.3.4: historical trends should still surface even with high current score.

    return action, reason, agent, priority, review_suggested, alternatives


@agents_router.post(
    "/recommend-action",
    response_model=RecommendActionResponse,
    summary="Intelligent Action Recommendation",
    description="Recommend next learning action based on scoring results and historical performance.",
    tags=["agents"],
    responses={
        200: {
            "description": "Action recommendation successful",
            "model": RecommendActionResponse,
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse,
        },
    },
)
async def recommend_action(
    request: RecommendActionRequest,
    memory_service: MemoryServiceDep,
) -> RecommendActionResponse:
    """
    Recommend next learning action based on score and history.

    Story 31.3: Agent决策推荐端点

    ✅ Verified from docs/stories/31.3.story.md

    Score-based recommendations (AC-31.3.3):
    - score < 60: decompose (基础拆解)
    - score 60-79: explain (解释补充)
    - score >= 80: next (继续学习)

    Historical analysis (AC-31.3.4):
    - Queries learning history for the concept
    - Calculates score trend (improving/stable/declining)
    - Suggests additional review for declining trends
    - Provides alternative agent recommendations

    Args:
        request: RecommendActionRequest with score, node_id, canvas_name
        memory_service: Memory service for history queries

    Returns:
        RecommendActionResponse with recommended action, agent endpoint, and reasoning

    [Source: docs/stories/31.3.story.md]
    [Source: specs/data/recommend-action-request.schema.json]
    [Source: specs/data/recommend-action-response.schema.json]
    """
    # [Code Review M3 fix]: Add request dedup for consistency with other endpoints
    cache_key = check_duplicate_request(
        canvas_name=request.canvas_name,
        node_id=request.node_id,
        agent_type="recommend_action"
    )

    logger.info(
        f"[Story 31.3] recommend_action: score={request.score}, "
        f"node_id={request.node_id}, canvas_name={request.canvas_name}, "
        f"include_history={request.include_history}"
    )

    history_context: Optional[HistoryContext] = None

    # AC-31.3.4: Query historical scores if requested
    if request.include_history:
        try:
            # [Code Review C1 fix]: Use "default" as user_id to match what
            # _record_learning_event() stores (agents.py:391 uses user_id="default").
            # Previously used request.canvas_name which never matched stored events.
            # [Code Review C3 fix]: Use node_id as concept fallback when frontend
            # doesn't send concept, to avoid mixing scores across concepts.
            concept_query = request.concept or request.node_id
            history_result = await memory_service.get_learning_history(
                user_id="default",
                concept=concept_query,
                page=1,
                page_size=10  # Get more to ensure enough scored items after filtering
            )

            # Extract scores from history items.
            items = history_result.get("items", [])
            valid_items = [
                it for it in items
                if "score" in it and it["score"] is not None
            ]

            # [Review fix SORT-001]: Sort by timestamp if available, otherwise trust source order.
            if valid_items and any("timestamp" in it for it in valid_items):
                valid_items.sort(key=lambda it: it.get("timestamp", ""), reverse=True)

            # [Code Review M1 fix]: Safe int conversion — handle floats and float-strings
            # without crashing. int("75.5") raises ValueError; int(float("75.5")) = 75.
            recent_scores: List[int] = []
            for it in valid_items[:5]:
                try:
                    recent_scores.append(int(float(it["score"])))
                except (ValueError, TypeError):
                    logger.warning(f"[Story 31.3] Skipping non-numeric score: {it.get('score')}")

            if recent_scores:
                # Calculate history context
                avg_score = sum(recent_scores) / len(recent_scores)
                trend = _calculate_trend(recent_scores)
                # Count truly consecutive low scores from most recent
                consecutive_low = 0
                for s in recent_scores:
                    if s < 60:
                        consecutive_low += 1
                    else:
                        break

                history_context = HistoryContext(
                    recent_scores=recent_scores[:5],
                    average_score=round(avg_score, 1),
                    trend=trend,
                    consecutive_low_count=consecutive_low
                )
                logger.info(
                    f"[Story 31.3] History context: avg={avg_score:.1f}, "
                    f"trend={trend.value}, consecutive_low={consecutive_low}"
                )

        except Exception as e:
            # Graceful degradation: continue without history
            logger.warning(f"[Story 31.3] Failed to get learning history: {e}")
            history_context = None

    # Determine recommendation
    action, reason, agent, priority, review_suggested, alternatives = _recommend_action_from_score(
        score=request.score,
        history_context=history_context
    )

    logger.info(
        f"[Story 31.3] Recommendation: action={action.value}, agent={agent}, "
        f"priority={priority}, review_suggested={review_suggested}"
    )

    # [Code Review M3]: Mark request as completed
    complete_request(cache_key)

    return RecommendActionResponse(
        action=action,
        agent=agent,
        reason=reason,
        priority=priority,
        review_suggested=review_suggested,
        history_context=history_context,
        alternative_agents=alternatives
    )
