# Canvas Learning System - Common Response Models
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: response model)
"""
Common Pydantic models for API responses.

These models define the structure of responses for health checks,
errors, and other common API patterns.

[Source: specs/data/health-check-response.schema.json]
[Source: specs/data/error-response.schema.json]
"""

from datetime import datetime
from typing import Any, Optional

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: pydantic models)
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """
    Health check response model.

    ✅ Verified from specs/data/health-check-response.schema.json
    Schema fields: status, app_name, version, timestamp (all required)

    Attributes:
        status: Application health status ("healthy" or "unhealthy")
        app_name: Application name
        version: Application version
        timestamp: ISO 8601 timestamp of the health check
    """

    status: str = Field(
        ...,
        description="Application health status",
        json_schema_extra={"enum": ["healthy", "unhealthy"]}
    )
    app_name: str = Field(
        ...,
        description="Application name"
    )
    version: str = Field(
        ...,
        description="Application version"
    )
    timestamp: datetime = Field(
        ...,
        description="Health check timestamp (ISO 8601 format)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "app_name": "Canvas Learning System",
                    "version": "1.0.0",
                    "timestamp": "2025-11-24T10:30:00Z"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """
    Error response model.

    ✅ Verified from specs/data/error-response.schema.json
    Schema fields: code (required), message (required), details (optional)

    Attributes:
        code: HTTP status code or custom error code
        message: Human-readable error message
        details: Additional error details (optional)
    """

    code: int = Field(
        ...,
        description="Error code"
    )
    message: str = Field(
        ...,
        description="Error message"
    )
    details: Optional[Any] = Field(
        default=None,
        description="Additional error details"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": 404,
                    "message": "Canvas not found"
                },
                {
                    "code": 400,
                    "message": "Validation error",
                    "details": {
                        "field": "node_id",
                        "reason": "Invalid format"
                    }
                }
            ]
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Summary Models (Story 17.2)
# [Source: specs/api/canvas-api.openapi.yml:987-1060]
# ═══════════════════════════════════════════════════════════════════════════════

class AgentTypeStats(BaseModel):
    """Statistics for a single agent type."""
    count: int = Field(..., description="Total invocations")
    success_count: int = Field(default=0, description="Successful invocations")
    error_count: int = Field(default=0, description="Failed invocations")
    avg_time_s: float = Field(default=0.0, description="Average execution time in seconds")


class AgentMetricsSummary(BaseModel):
    """
    Agent metrics summary.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]
    """
    invocations_total: int = Field(..., description="Total agent invocations")
    avg_execution_time_s: float = Field(..., description="Average execution time in seconds")
    by_type: dict[str, AgentTypeStats] = Field(
        default_factory=dict,
        description="Statistics by agent type"
    )


class MemoryTypeStats(BaseModel):
    """Statistics for a single memory system type."""
    query_count: int = Field(default=0, description="Total queries")
    success_count: int = Field(default=0, description="Successful queries")
    error_count: int = Field(default=0, description="Failed queries")
    avg_latency_s: float = Field(default=0.0, description="Average latency in seconds")
    by_operation: dict[str, int] = Field(
        default_factory=dict,
        description="Query counts by operation type"
    )


class MemoryMetricsSummary(BaseModel):
    """
    Memory system metrics summary.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]
    """
    queries_total: int = Field(..., description="Total memory queries")
    avg_latency_s: float = Field(..., description="Average query latency in seconds")
    by_type: dict[str, MemoryTypeStats] = Field(
        default_factory=dict,
        description="Statistics by memory type (graphiti, lancedb, temporal, sqlite)"
    )


class ResourceMetricsSummary(BaseModel):
    """
    System resource metrics summary.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]
    """
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    memory_available_bytes: int = Field(default=0, description="Available memory in bytes")
    memory_total_bytes: int = Field(default=0, description="Total memory in bytes")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")
    disk_free_bytes: int = Field(default=0, description="Free disk space in bytes")


class MetricsSummary(BaseModel):
    """
    Complete metrics summary response for /metrics/summary endpoint.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]
    [Source: Story 17.2 AC-6]
    """
    agents: AgentMetricsSummary = Field(..., description="Agent execution metrics")
    memory_system: MemoryMetricsSummary = Field(..., description="Memory system metrics")
    resources: ResourceMetricsSummary = Field(..., description="System resource metrics")
    timestamp: datetime = Field(..., description="Metrics collection timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "agents": {
                        "invocations_total": 150,
                        "avg_execution_time_s": 2.5,
                        "by_type": {
                            "scoring-agent": {
                                "count": 50,
                                "success_count": 48,
                                "error_count": 2,
                                "avg_time_s": 3.2
                            }
                        }
                    },
                    "memory_system": {
                        "queries_total": 300,
                        "avg_latency_s": 0.15,
                        "by_type": {
                            "graphiti": {
                                "query_count": 100,
                                "success_count": 99,
                                "error_count": 1,
                                "avg_latency_s": 0.2,
                                "by_operation": {"search": 80, "write": 20}
                            }
                        }
                    },
                    "resources": {
                        "cpu_usage_percent": 45.2,
                        "memory_usage_percent": 62.5,
                        "memory_available_bytes": 8589934592,
                        "memory_total_bytes": 17179869184,
                        "disk_usage_percent": 55.0,
                        "disk_free_bytes": 107374182400
                    },
                    "timestamp": "2025-12-03T10:30:00Z"
                }
            ]
        }
    }
