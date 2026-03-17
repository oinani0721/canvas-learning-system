"""
Canvas Learning System - Context API Endpoint
Story 3.4: Learning Context Auto-Injection (AC-1, AC-2, Task 5)

GET /api/v1/context/{node_id}

Returns Tier 1 (current node full) + Tier 2 (adjacent node summaries)
learning context data for injection into Claude Code's system prompt.

Data sources:
- Neo4j (via Neo4jClient): node metadata, mastery data, edge reasons, neighbors
- Graphiti: Tips, error records (searched via graphiti_client)

30s cache per node to avoid redundant queries on rapid message sends.

[Source: _bmad-output/implementation-artifacts/3-4-learning-context-auto-injection.md#Task 5]
"""

import logging
import time

from fastapi import APIRouter
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
# Neo4j Client Access (same pattern as profile.py)
# ═══════════════════════════════════════════════════════════════════════════════


def _get_neo4j_client():
    """Get Neo4j client for Cypher queries. Returns None if unavailable."""
    try:
        from app.clients.neo4j_client import get_neo4j_client
        return get_neo4j_client()
    except Exception as e:
        logger.warning("Neo4j client unavailable: %s", e)
        return None


def _get_graphiti():
    """Get Graphiti client for memory search. Returns None if unavailable."""
    try:
        from app.clients.graphiti_client import get_graphiti_client
        return get_graphiti_client()
    except Exception as e:
        logger.warning("Graphiti client unavailable: %s", e)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Cache (30s TTL per node)
# ═══════════════════════════════════════════════════════════════════════════════

_context_cache: dict[str, tuple[float, ContextResponse]] = {}
CACHE_TTL_SECONDS = 30.0


def _get_cached(node_id: str) -> ContextResponse | None:
    """Return cached context if still fresh (within TTL)."""
    entry = _context_cache.get(node_id)
    if entry is None:
        return None
    cached_at, response = entry
    if time.time() - cached_at > CACHE_TTL_SECONDS:
        del _context_cache[node_id]
        return None
    return response


def _set_cache(node_id: str, response: ContextResponse) -> None:
    """Cache a context response."""
    _context_cache[node_id] = (time.time(), response)


# ═══════════════════════════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════════════════════════

context_router = APIRouter()


@context_router.get(
    "/context/{node_id}",
    response_model=ContextResponse,
    summary="Get learning context for a node (Tier 1 + Tier 2)",
    tags=["Context"],
)
async def get_node_context(node_id: str) -> ContextResponse:
    """
    Fetch the learning context for a specific node.

    Returns Tier 1 (full current node data) and Tier 2 (adjacent node summaries).
    Results are cached for 30 seconds per node.

    Story 3.4 AC-1: Data structured for --append-system-prompt injection.
    Story 3.4 AC-2: Tier 1 = full, Tier 2 = summary, Tier 3 = on-demand (not here).
    """
    # Check cache first
    cached = _get_cached(node_id)
    if cached is not None:
        return cached

    # Assemble Tier 1: current node full context
    tier1 = await _assemble_tier1(node_id)

    # Assemble Tier 2: adjacent node summaries
    tier2 = await _assemble_tier2(node_id)

    response = ContextResponse(
        node_id=node_id,
        node_name=tier1.node_name,
        tier1=tier1,
        tier2=tier2,
    )

    _set_cache(node_id, response)
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# Data Assembly
# ═══════════════════════════════════════════════════════════════════════════════


async def _assemble_tier1(node_id: str) -> Tier1Context:
    """
    Assemble Tier 1 context: full data for the current node.

    Sources: Neo4j (node name, mastery, edge reasons) + Graphiti (tips, errors).
    Degrades gracefully: returns empty data if services are unavailable.
    """
    node_name = node_id  # Default fallback
    mastery = MasteryInfo()
    tips: list[TipInfo] = []
    errors: list[ErrorInfo] = []
    edge_reasons: list[EdgeReasonInfo] = []

    # --- Fetch node name + mastery + edges from Neo4j ---
    client = _get_neo4j_client()
    if client is not None:
        try:
            # Get node name and mastery data
            node_query = (
                "MATCH (n:Concept {id: $id}) RETURN n.name AS name, "
                "n.p_mastery AS p_mastery, n.fsrs_stability AS stability, "
                "n.fsrs_next_review AS next_review"
            )
            node_result = await client.execute_query(node_query, {"id": node_id})
            if node_result and len(node_result) > 0:
                record = node_result[0]
                node_name = record.get("name") or node_id
                mastery = MasteryInfo(
                    p_mastery=record.get("p_mastery"),
                    stability=record.get("stability"),
                    next_review=record.get("next_review"),
                )

            # Get edge reasons (relationships from/to this node)
            edge_query = (
                "MATCH (n:Concept {id: $id})-[r]-(m:Concept) "
                "RETURN m.name AS neighbor, r.reason AS reason "
                "LIMIT 10"
            )
            edge_result = await client.execute_query(edge_query, {"id": node_id})
            for rec in (edge_result or []):
                if rec.get("neighbor"):
                    edge_reasons.append(
                        EdgeReasonInfo(
                            neighbor_name=rec["neighbor"],
                            reason=rec.get("reason") or "",
                        )
                    )
        except Exception as e:
            logger.warning(
                "Failed to fetch node data from Neo4j for %s: %s", node_id, e
            )

    # --- Fetch tips and errors from Graphiti ---
    graphiti = _get_graphiti()
    if graphiti is not None:
        try:
            # Search for tips related to this node
            tip_results = await graphiti.search(
                query=f"tips for concept {node_id}",
                num_results=20,
            )
            for fact in (tip_results or []):
                fact_text = getattr(fact, 'fact', None) or getattr(fact, 'content', None)
                if fact_text:
                    tips.append(
                        TipInfo(
                            content=fact_text,
                            category="tip",
                            annotated_at=str(getattr(fact, 'created_at', '')),
                        )
                    )

            # Search for error records
            error_results = await graphiti.search(
                query=f"errors mistakes for concept {node_id}",
                num_results=10,
            )
            for fact in (error_results or []):
                fact_text = getattr(fact, 'fact', None) or getattr(fact, 'content', None)
                if fact_text:
                    errors.append(
                        ErrorInfo(
                            error_type="learning_error",
                            description=fact_text,
                            remedy="",
                        )
                    )
        except Exception as e:
            logger.warning(
                "Failed to fetch Graphiti data for %s: %s", node_id, e
            )

    return Tier1Context(
        node_name=node_name,
        mastery=mastery,
        tips=tips,
        errors=errors,
        edge_reasons=edge_reasons,
    )


async def _assemble_tier2(node_id: str) -> Tier2Context:
    """
    Assemble Tier 2 context: 1-hop neighbor summaries from Neo4j.
    Degrades gracefully: returns empty neighbors if Neo4j is unavailable.
    """
    neighbors: list[NeighborInfo] = []

    client = _get_neo4j_client()
    if client is not None:
        try:
            query = (
                "MATCH (n:Concept {id: $id})-[r]-(m:Concept) "
                "RETURN m.name AS name, m.effective_proficiency AS mastery, "
                "r.reason AS reason "
                "LIMIT 10"
            )
            result = await client.execute_query(query, {"id": node_id})
            for rec in (result or []):
                if rec.get("name"):
                    neighbors.append(
                        NeighborInfo(
                            name=rec["name"],
                            mastery_level=rec.get("mastery"),
                            edge_reason=rec.get("reason") or "",
                        )
                    )
        except Exception as e:
            logger.warning(
                "Failed to fetch neighbors from Neo4j for %s: %s", node_id, e
            )

    return Tier2Context(neighbors=neighbors)
