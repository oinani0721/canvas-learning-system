# Canvas Learning System - Subject Models
# Story 1.9: Multi-Subject Knowledge Graph Isolation (Task 8)
"""
Pydantic models for the Subject CRUD API.

Subjects are user-managed entities stored as :Subject nodes in Neo4j.
Each subject provides a namespace (subjectId) for knowledge graph
isolation.

[Source: _bmad-output/implementation-artifacts/1-9-multi-subject-kg-isolation.md#Task 8]
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    """Request body for creating a new subject."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable subject name (e.g. '离散数学', 'Physics 7A')",
    )
    color: Optional[str] = Field(
        None,
        max_length=20,
        description="Optional display color (e.g. '#4A90D9')",
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "离散数学", "color": "#4A90D9"}}
    )


class SubjectUpdate(BaseModel):
    """Request body for updating a subject."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="New subject name",
    )
    color: Optional[str] = Field(
        None,
        max_length=20,
        description="New display color",
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "离散数学 (进阶)", "color": "#D94A4A"}}
    )


class SubjectResponse(BaseModel):
    """Single subject in API responses."""

    id: str = Field(..., description="Subject unique identifier")
    name: str = Field(..., description="Human-readable subject name")
    color: Optional[str] = Field(None, description="Display color")
    created_at: str = Field(..., description="ISO-8601 creation timestamp")
    node_count: int = Field(
        0, description="Number of CanvasNode entries in this subject"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "subj_a1b2c3",
                "name": "离散数学",
                "color": "#4A90D9",
                "created_at": "2026-03-18T10:00:00Z",
                "node_count": 42,
            }
        }
    )


class SubjectListResponse(BaseModel):
    """Response for GET /subjects/."""

    subjects: list[SubjectResponse] = Field(
        default_factory=list, description="All subjects"
    )
    total: int = Field(0, description="Total number of subjects")
