# Canvas Learning System - Health Check Endpoint
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: path operation decorators)
"""
Health check endpoint for the Canvas Learning System API.

This endpoint provides application status information for monitoring
and load balancer health checks.

[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health]
[Source: specs/data/health-check-response.schema.json]
"""

from datetime import datetime, timezone
import logging

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.models.common import HealthCheckResponse

# Get logger for this module
logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
# Pattern: Create router instance with tags for OpenAPI grouping
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="返回应用状态、名称、版本和时间戳",
    operation_id="health_check",
    responses={
        200: {
            "description": "应用健康",
            "model": HealthCheckResponse
        },
        500: {
            "description": "应用异常"
        }
    }
)
async def health_check(
    settings: Settings = Depends(get_settings)
) -> HealthCheckResponse:
    """
    Check application health status.

    Returns application name, version, and current timestamp to indicate
    the service is running and responsive.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Depends lru_cache settings)
    Pattern: Inject settings using Depends(get_settings)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health]

    Args:
        settings: Application settings injected via dependency.

    Returns:
        HealthCheckResponse: Health status with app info and timestamp.

    Example Response:
        {
            "status": "healthy",
            "app_name": "Canvas Learning System API",
            "version": "1.0.0",
            "timestamp": "2025-11-24T10:30:00Z"
        }
    """
    logger.debug("Health check requested")

    return HealthCheckResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc)
    )
