"""
Memory System Models for Canvas Learning System API

Provides Pydantic models for 3-layer memory query operations:
- Temporal Memory (LangGraph Checkpointer)
- Semantic Memory (LanceDB vectors)
- Graphiti Memory (Neo4j knowledge graph)

Source: docs/prd/sections/v116-艾宾浩斯系统3层记忆数据整合-2025-11-12-必读.md
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Memory Query Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryQueryRequest(BaseModel):
    """Request model for memory queries."""
    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    entity_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by entity types (for Graphiti queries)"
    )


class TemporalMemoryItem(BaseModel):
    """Single temporal memory item (learning session history)."""
    session_id: str = Field(..., description="Unique session identifier")
    canvas_id: str = Field(..., description="Associated canvas ID")
    timestamp: datetime = Field(..., description="Session timestamp")
    activity_type: str = Field(..., description="Type of learning activity")
    content: str = Field(..., description="Session content/notes")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class SemanticMemoryItem(BaseModel):
    """Single semantic memory item (document vector)."""
    doc_id: str = Field(..., description="Document identifier")
    content: str = Field(..., description="Document content")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    source: str = Field(..., description="Source document path")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class GraphitiMemoryItem(BaseModel):
    """Single Graphiti memory item (knowledge graph entity/fact)."""
    entity_id: str = Field(..., description="Entity or fact identifier")
    entity_type: str = Field(..., description="Type of entity")
    content: str = Field(..., description="Entity content or fact description")
    relationships: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Related entities and relationship types"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class TemporalQueryResponse(BaseModel):
    """Response for temporal memory queries."""
    items: List[TemporalMemoryItem] = Field(default_factory=list)
    total_count: int = Field(..., description="Total matching items")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")


class SemanticQueryResponse(BaseModel):
    """Response for semantic memory queries."""
    items: List[SemanticMemoryItem] = Field(default_factory=list)
    total_count: int = Field(..., description="Total matching items")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")


class GraphitiQueryResponse(BaseModel):
    """Response for Graphiti memory queries."""
    items: List[GraphitiMemoryItem] = Field(default_factory=list)
    total_count: int = Field(..., description="Total matching items")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")


# ═══════════════════════════════════════════════════════════════════════════════
# Memory Status Models
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryLayerStatus(BaseModel):
    """Status of a single memory layer."""
    name: str = Field(..., description="Layer name (temporal/semantic/graphiti)")
    enabled: bool = Field(..., description="Whether the layer is enabled")
    connected: bool = Field(..., description="Whether the layer is connected")
    item_count: int = Field(default=0, description="Number of items in the layer")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if any")


class MemorySystemStatus(BaseModel):
    """Overall 3-layer memory system status."""
    temporal: MemoryLayerStatus = Field(..., description="Temporal memory status")
    semantic: MemoryLayerStatus = Field(..., description="Semantic memory status")
    graphiti: MemoryLayerStatus = Field(..., description="Graphiti memory status")
    overall_health: str = Field(
        ...,
        description="Overall health status: healthy, degraded, or unhealthy"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Memory Store Models
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryStoreRequest(BaseModel):
    """Request to store a memory item."""
    content: str = Field(..., description="Content to store")
    memory_type: str = Field(
        ...,
        description="Memory type: temporal, semantic, or graphiti"
    )
    canvas_id: Optional[str] = Field(default=None, description="Associated canvas ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    entity_type: Optional[str] = Field(
        default=None,
        description="Entity type (for Graphiti storage)"
    )


class MemoryStoreResponse(BaseModel):
    """Response after storing a memory item."""
    success: bool = Field(..., description="Whether the operation succeeded")
    memory_id: Optional[str] = Field(default=None, description="Stored memory ID")
    message: str = Field(..., description="Status message")
