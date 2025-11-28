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
