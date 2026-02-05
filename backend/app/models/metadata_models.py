# Canvas Learning System - Canvas Metadata Models
# Story 38.1: Canvas Metadata Management System
"""
Canvas metadata Pydantic models for request/response validation.

Models for:
- Canvas metadata query (subject, category, group_id)
- LanceDB index status
- Subject mapping configuration

[Source: Design doc - Canvas 元数据管理系统设计]
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums
# =============================================================================

class MetadataSource(str, Enum):
    """Source of metadata resolution."""
    CONFIG = "config"       # From subject_mapping.yaml
    INFERRED = "inferred"   # Auto-inferred from path
    DEFAULT = "default"     # Fallback to defaults
    MANUAL = "manual"       # Manually specified in request


# =============================================================================
# Canvas Metadata Models
# =============================================================================

class CanvasMetadataResponse(BaseModel):
    """
    Canvas metadata response model.

    Returns subject, category, and group_id for a Canvas file.

    [Source: Design doc - Phase 1.1]
    """
    canvas_path: str = Field(..., description="Canvas file path")
    subject: str = Field(..., description="Subject identifier (e.g., 'math54')")
    category: str = Field(..., description="Category identifier (e.g., 'math')")
    group_id: str = Field(..., description="Graphiti group_id (e.g., 'math54:离散数学')")
    source: MetadataSource = Field(
        ...,
        description="How the metadata was resolved"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "canvas_path": "Math 54/离散数学.canvas",
                "subject": "math54",
                "category": "math",
                "group_id": "math54:离散数学",
                "source": "config"
            }
        }
    )


# =============================================================================
# LanceDB Index Status Models
# =============================================================================

class CanvasIndexStatusResponse(BaseModel):
    """
    LanceDB index status response model.

    Shows whether a Canvas has been indexed and relevant statistics.

    [Source: Design doc - Phase 1.2]
    """
    canvas_path: str = Field(..., description="Canvas file path")
    indexed: bool = Field(..., description="Whether the Canvas is indexed")
    node_count: int = Field(
        default=0,
        description="Number of indexed nodes",
        ge=0
    )
    last_indexed: Optional[datetime] = Field(
        None,
        description="Last indexing timestamp"
    )
    subject: Optional[str] = Field(
        None,
        description="Subject used during indexing"
    )
    table_name: str = Field(
        default="canvas_nodes",
        description="LanceDB table name"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "canvas_path": "Math 54/离散数学.canvas",
                "indexed": True,
                "node_count": 42,
                "last_indexed": "2026-02-04T12:30:00",
                "subject": "math54",
                "table_name": "canvas_nodes"
            }
        }
    )


class CanvasIndexRequest(BaseModel):
    """
    Canvas index request model.

    Triggers indexing of a Canvas to LanceDB.

    [Source: Design doc - Phase 1.3]
    """
    canvas_path: str = Field(..., description="Canvas file path")
    subject: Optional[str] = Field(
        None,
        description="Override subject (optional)"
    )
    category: Optional[str] = Field(
        None,
        description="Override category (optional)"
    )
    force: bool = Field(
        default=False,
        description="Force re-index even if already indexed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "canvas_path": "Math 54/离散数学.canvas",
                "subject": "math54",
                "category": "math",
                "force": False
            }
        }
    )


class CanvasIndexResponse(BaseModel):
    """
    Canvas index response model.

    Result of a Canvas indexing operation.
    """
    canvas_path: str = Field(..., description="Canvas file path")
    success: bool = Field(..., description="Whether indexing succeeded")
    node_count: int = Field(
        default=0,
        description="Number of nodes indexed",
        ge=0
    )
    subject: str = Field(..., description="Subject used for indexing")
    category: str = Field(..., description="Category used for indexing")
    group_id: str = Field(..., description="Group ID used for indexing")
    duration_ms: float = Field(
        default=0.0,
        description="Indexing duration in milliseconds",
        ge=0
    )
    message: Optional[str] = Field(
        None,
        description="Additional message or error details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "canvas_path": "Math 54/离散数学.canvas",
                "success": True,
                "node_count": 42,
                "subject": "math54",
                "category": "math",
                "group_id": "math54:离散数学",
                "duration_ms": 1250.5,
                "message": None
            }
        }
    )


# =============================================================================
# Subject Mapping Configuration Models
# =============================================================================

class SubjectMappingRule(BaseModel):
    """
    Single subject mapping rule.

    Maps a folder pattern to subject and category.
    """
    pattern: str = Field(
        ...,
        description="Folder pattern (glob-style, e.g., 'Math 54/**')"
    )
    subject: str = Field(..., description="Subject identifier")
    category: str = Field(..., description="Category identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pattern": "Math 54/**",
                "subject": "math54",
                "category": "math"
            }
        }
    )


class CategoryRule(BaseModel):
    """
    Category inference rule.

    Maps patterns to a category when no explicit mapping exists.
    """
    category: str = Field(..., description="Category identifier")
    patterns: List[str] = Field(
        ...,
        description="List of patterns that map to this category"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "math",
                "patterns": ["math*", "数学*", "线性代数*"]
            }
        }
    )


class SubjectMappingConfig(BaseModel):
    """
    Complete subject mapping configuration.

    Used for GET/PUT /api/v1/config/subject-mapping

    [Source: Design doc - Phase 2.1]
    """
    mappings: List[SubjectMappingRule] = Field(
        default_factory=list,
        description="Explicit folder → subject/category mappings"
    )
    category_rules: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Category inference rules (category → patterns)"
    )
    defaults: Dict[str, str] = Field(
        default_factory=lambda: {"subject": "general", "category": "general"},
        description="Default subject/category when no rule matches"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mappings": [
                    {"pattern": "Math 54/**", "subject": "math54", "category": "math"},
                    {"pattern": "Physics 7A/**", "subject": "physics7a", "category": "physics"}
                ],
                "category_rules": {
                    "math": ["math*", "数学*"],
                    "physics": ["physics*", "物理*"]
                },
                "defaults": {
                    "subject": "general",
                    "category": "general"
                }
            }
        }
    )


class SubjectInfo(BaseModel):
    """
    Resolved subject information.

    Internal model returned by SubjectResolver.
    """
    subject: str
    category: str
    group_id: str
    source: MetadataSource

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subject": "math54",
                "category": "math",
                "group_id": "math54:离散数学",
                "source": "config"
            }
        }
    )


# =============================================================================
# Batch Operations
# =============================================================================

class BatchIndexRequest(BaseModel):
    """
    Batch Canvas index request.

    Index multiple Canvas files at once.
    """
    canvas_paths: List[str] = Field(
        ...,
        description="List of Canvas file paths to index",
        min_length=1,
        max_length=50
    )
    force: bool = Field(
        default=False,
        description="Force re-index even if already indexed"
    )


class BatchIndexResponse(BaseModel):
    """
    Batch Canvas index response.
    """
    total: int = Field(..., description="Total Canvas files requested")
    success_count: int = Field(
        default=0,
        description="Number of successfully indexed files"
    )
    failed_count: int = Field(
        default=0,
        description="Number of failed files"
    )
    results: List[CanvasIndexResponse] = Field(
        default_factory=list,
        description="Individual results for each Canvas"
    )
    total_duration_ms: float = Field(
        default=0.0,
        description="Total operation duration in milliseconds"
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "MetadataSource",
    # Metadata
    "CanvasMetadataResponse",
    # Index Status
    "CanvasIndexStatusResponse",
    "CanvasIndexRequest",
    "CanvasIndexResponse",
    # Subject Mapping
    "SubjectMappingRule",
    "CategoryRule",
    "SubjectMappingConfig",
    "SubjectInfo",
    # Batch Operations
    "BatchIndexRequest",
    "BatchIndexResponse",
]
