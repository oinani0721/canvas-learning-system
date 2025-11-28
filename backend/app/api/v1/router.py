# Canvas Learning System - API v1 Router
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter include_router)
"""
API v1 router that aggregates all endpoint routers.

This module combines all API v1 endpoint routers into a single router
that can be mounted on the main FastAPI application.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#API路由设计]
[Source: specs/api/fastapi-backend-api.openapi.yml]
"""

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
from fastapi import APIRouter

from app.api.v1.endpoints import health

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter include_router)
# Pattern: Create main router and include sub-routers with prefixes/tags
router = APIRouter()

# ═══════════════════════════════════════════════════════════════════════════════
# Health Check Routes
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: include_router tags)
router.include_router(
    health.router,
    tags=["System"],
    responses={
        500: {"description": "Internal server error"}
    }
)

# ═══════════════════════════════════════════════════════════════════════════════
# Future Routes (Story 15.2+)
# ═══════════════════════════════════════════════════════════════════════════════

# Canvas operations (Story 15.2)
# router.include_router(
#     canvas.router,
#     prefix="/canvas",
#     tags=["Canvas"],
#     responses={404: {"description": "Canvas not found"}}
# )

# Agent operations (Story 15.3)
# router.include_router(
#     agent.router,
#     prefix="/agents",
#     tags=["Agents"],
#     responses={500: {"description": "Agent call failed"}}
# )

# Review operations (Story 15.4)
# router.include_router(
#     review.router,
#     prefix="/review",
#     tags=["Review"]
# )
