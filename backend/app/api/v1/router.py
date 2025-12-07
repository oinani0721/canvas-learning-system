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
from app.api.v1.endpoints.agents import agents_router
from app.api.v1.endpoints.canvas import canvas_router
from app.api.v1.endpoints.monitoring import monitoring_router
from app.api.v1.endpoints.review import review_router
from app.api.v1.endpoints.rollback import rollback_router

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
# Canvas Routes (Story 15.2)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    canvas_router,
    prefix="/canvas",
    tags=["Canvas"],
    responses={404: {"description": "Canvas not found"}}
)

# ═══════════════════════════════════════════════════════════════════════════════
# Agent Routes (Story 15.2)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    agents_router,
    prefix="/agents",
    tags=["Agents"],
    responses={500: {"description": "Agent call failed"}}
)

# ═══════════════════════════════════════════════════════════════════════════════
# Review Routes (Story 15.2)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    review_router,
    prefix="/review",
    tags=["Review"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# Monitoring Routes (Story 17.3)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 17.3 - Alert System & Dashboard
# [Source: docs/stories/17.3.story.md - AC 3-4]
router.include_router(
    monitoring_router,
    prefix="/metrics",
    tags=["Monitoring"],
    responses={500: {"description": "Monitoring service error"}}
)

# ═══════════════════════════════════════════════════════════════════════════════
# Rollback Routes (Story 18.1)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 18.1 - Operation Tracker
# [Source: docs/stories/18.1.story.md - AC 6]
# [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
router.include_router(
    rollback_router,
    prefix="/rollback",
    tags=["Rollback"],
    responses={
        404: {"description": "Operation/snapshot not found"},
        500: {"description": "Rollback service error"}
    }
)
