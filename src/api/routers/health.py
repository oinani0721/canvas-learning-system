"""
Health Check Router for Canvas Learning System API

Provides health check endpoint for monitoring application status.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from ..config import get_settings
from ..models import HealthCheckResponse

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="返回应用状态、名称、版本和时间戳",
    operation_id="health_check"
)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns application health status including:
    - status: "healthy" or "unhealthy"
    - app_name: Application name
    - version: Application version
    - timestamp: Current UTC timestamp

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health
    """
    settings = get_settings()
    return HealthCheckResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc)
    )
