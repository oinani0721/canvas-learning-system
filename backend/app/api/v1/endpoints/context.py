"""
Canvas Learning System - Context API Endpoint
Story 3.4: Learning Context Auto-Injection (AC-1, AC-2, AC-4, Task 5)

GET /api/v1/context/{node_id}
GET /api/v1/context/{node_id}?format=markdown

Returns Tier 1 (current node full) + Tier 2 (adjacent node summaries)
learning context data for injection into Claude Code's --append-system-prompt.

Data sources (via LearningContextService):
- MasteryStore (Neo4j EntityNode): p_mastery, fsrs_stability, next_review
- MemoryService (in-memory episodes): tips, error records
- LearningMemoryClient: supplementary learning memories
- Neo4jClient (Cypher): edge reasons, 1-hop neighbor summaries

30s cache per node to avoid redundant queries on rapid message sends.
Supports ?format=markdown for direct --append-system-prompt injection.

[Source: _bmad-output/implementation-artifacts/3-4-learning-context-auto-injection.md#Task 5]
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class MasteryInfo(BaseModel):
    p_mastery: float | None = None
    stability: float | None = None
    next_review: str | None = None


class TipInfo(BaseModel):
    content: str
    category: str = "general"
    annotated_at: str = ""


class ErrorInfo(BaseModel):
    error_type: str
    description: str
    remedy: str = ""


class EdgeReasonInfo(BaseModel):
    neighbor_name: str
    reason: str


class Tier1Context(BaseModel):
    node_name: str
    mastery: MasteryInfo
    tips: list[TipInfo]
    errors: list[ErrorInfo]
    edge_reasons: list[EdgeReasonInfo]


class NeighborInfo(BaseModel):
    name: str
    mastery_level: float | None = None
    edge_reason: str = ""


class Tier2Context(BaseModel):
    neighbors: list[NeighborInfo]


class ContextResponse(BaseModel):
    node_id: str
    node_name: str
    tier1: Tier1Context
    tier2: Tier2Context


# ═══════════════════════════════════════════════════════════════════════════════
# Cache (30s TTL per node — AC-4 dynamic update)
# ═══════════════════════════════════════════════════════════════════════════════

# Maximum number of cached node contexts to prevent unbounded memory growth.
# With 30s TTL and typical usage, 200 nodes is more than sufficient.
CACHE_MAX_SIZE = 200
CACHE_TTL_SECONDS = 30.0

_context_cache: dict[str, tuple[float, dict]] = {}


def _get_cached(node_id: str) -> dict | None:
    """Return cached context dict if still fresh (within TTL)."""
    entry = _context_cache.get(node_id)
    if entry is None:
        return None
    cached_at, response = entry
    if time.time() - cached_at > CACHE_TTL_SECONDS:
        del _context_cache[node_id]
        return None
    return response


def _set_cache(node_id: str, response: dict) -> None:
    """Cache a context response dict with LRU eviction at CACHE_MAX_SIZE."""
    # Evict oldest entries if cache exceeds max size
    if len(_context_cache) >= CACHE_MAX_SIZE and node_id not in _context_cache:
        # Remove the oldest entry by cached_at timestamp
        oldest_key = min(_context_cache, key=lambda k: _context_cache[k][0])
        del _context_cache[oldest_key]
    _context_cache[node_id] = (time.time(), response)


# ═══════════════════════════════════════════════════════════════════════════════
# Dict -> Pydantic conversion
# ═══════════════════════════════════════════════════════════════════════════════


def _dict_to_response(ctx: dict) -> ContextResponse:
    """Convert raw dict from LearningContextService to Pydantic response model."""
    tier1_raw = ctx.get("tier1", {})
    tier2_raw = ctx.get("tier2", {})

    tier1 = Tier1Context(
        node_name=tier1_raw.get("node_name", ctx.get("node_id", "")),
        mastery=MasteryInfo(**(tier1_raw.get("mastery", {}))),
        tips=[TipInfo(**t) for t in tier1_raw.get("tips", [])],
        errors=[ErrorInfo(**e) for e in tier1_raw.get("errors", [])],
        edge_reasons=[EdgeReasonInfo(**er) for er in tier1_raw.get("edge_reasons", [])],
    )

    tier2 = Tier2Context(
        neighbors=[NeighborInfo(**nb) for nb in tier2_raw.get("neighbors", [])],
    )

    return ContextResponse(
        node_id=ctx.get("node_id", ""),
        node_name=ctx.get("node_name", ""),
        tier1=tier1,
        tier2=tier2,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════════════════════════

context_router = APIRouter()


@context_router.get(
    "/context/{node_id}",
    response_model=ContextResponse,
    summary="Get learning context for a node (Tier 1 + Tier 2)",
    tags=["Context"],
    responses={
        200: {
            "description": "Learning context (JSON or Markdown)",
            "content": {
                "application/json": {},
                "text/plain": {"example": "## 当前节点：贝叶斯定理\n### 精通度\n- BKT掌握概率: 0.45"},
            },
        }
    },
)
async def get_node_context_endpoint(
    node_id: str,
    format: Optional[str] = Query(
        default=None,
        description='Response format: omit for JSON, "markdown" for plain-text Markdown '
        "(ready for --append-system-prompt).",
    ),
    group_id: Optional[str] = Query(
        default=None,
        description="Subject isolation namespace. Defaults to app-level DEFAULT_GROUP_ID.",
    ),
):
    """
    Fetch the learning context for a specific node.

    Returns Tier 1 (full current node data) and Tier 2 (adjacent node summaries).
    Results are cached for 30 seconds per node.

    Story 3.4 AC-1: Data structured for --append-system-prompt injection.
    Story 3.4 AC-2: Tier 1 = full, Tier 2 = summary, Tier 3 = on-demand (not here).
    Story 3.4 AC-4: Each call re-assembles context (cache TTL 30s ensures freshness).

    Query params:
        format: "markdown" returns plain-text Markdown; default returns JSON.
        group_id: override subject namespace for multi-subject isolation.
    """
    from app.services.learning_context_service import (
        format_as_markdown,
        get_node_context,
    )

    # Check cache first
    cached = _get_cached(node_id)
    if cached is None:
        cached = await get_node_context(node_id=node_id, group_id=group_id)
        _set_cache(node_id, cached)

    # Return Markdown if requested
    if format and format.lower() == "markdown":
        md_text = format_as_markdown(cached)
        return PlainTextResponse(content=md_text, media_type="text/plain; charset=utf-8")

    # Default: return JSON via Pydantic model
    return _dict_to_response(cached)
