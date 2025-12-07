"""
Common Pydantic Models for Canvas Learning System API

Provides shared response models and error handling schemas.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Pydantic models)
Models match specs/api/fastapi-backend-api.openapi.yml
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """
    Health check response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/HealthCheckResponse
    """
    status: str = Field(
        ...,
        description="Application health status",
        examples=["healthy", "unhealthy"]
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
        description="Health check timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "app_name": "Canvas Learning System",
                "version": "1.0.0",
                "timestamp": "2025-11-24T10:30:00Z"
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Standard error response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ErrorResponse
    """
    code: int = Field(
        ...,
        description="Error code"
    )
    message: str = Field(
        ...,
        description="Error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": 404,
                "message": "Canvas not found",
                "details": {"canvas_name": "test-canvas"}
            }
        }
    }
