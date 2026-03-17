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

from app.api.v1.endpoints import debug, health
from app.api.v1.endpoints.agents import agents_router
from app.api.v1.endpoints.archive import archive_router  # Story 3.8
from app.api.v1.endpoints.canvas import canvas_router
from app.api.v1.endpoints.config import config_router
from app.api.v1.endpoints.context import context_router  # Story 3.4
from app.api.v1.endpoints.edges import edges_router  # Story 4.1-4.4
from app.api.v1.endpoints.exam import exam_router
from app.api.v1.endpoints.exam_sessions import exam_sessions_router
from app.api.v1.endpoints.index_image import index_image_router
from app.api.v1.endpoints.intelligent_parallel import (
    intelligent_parallel_router,
    single_agent_router,
)
from app.api.v1.endpoints.mastery import mastery_router
from app.api.v1.endpoints.memory import memory_router
from app.api.v1.endpoints.metadata import metadata_router  # ✅ Story 38.1
from app.api.v1.endpoints.monitoring import monitoring_router
from app.api.v1.endpoints.multimodal import multimodal_router
from app.api.v1.endpoints.profile import profile_router
from app.api.v1.endpoints.rag import rag_router
from app.api.v1.endpoints.review import review_router
from app.api.v1.endpoints.rollback import rollback_router
from app.api.v1.endpoints.suggestions import suggestions_router  # Story 3.7
from app.api.v1.endpoints.sync import sync_router  # Story 1.5
from app.api.v1.endpoints.textbook import textbook_router
from app.api.v1.endpoints.tips import tips_router  # Story 3.6
from app.api.v1.system import router as system_router  # Story 1.1

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter include_router)
# Pattern: Create main router and include sub-routers with prefixes/tags
router = APIRouter()

# ═══════════════════════════════════════════════════════════════════════════════
# Health Check Routes
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: include_router tags)
router.include_router(health.router, tags=["System"], responses={500: {"description": "Internal server error"}})

# ═══════════════════════════════════════════════════════════════════════════════
# System Infrastructure Health (Story 1.1)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(system_router, responses={500: {"description": "System health check error"}})

# ═══════════════════════════════════════════════════════════════════════════════
# Config Routes (AI Configuration Runtime Override)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    config_router, prefix="/config", tags=["Config"], responses={500: {"description": "Configuration error"}}
)

# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Metadata Routes (Story 38.1)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Story 38.1: Canvas Metadata Management System
# [Source: docs/stories/38.1.story.md]
# NOTE: Using separate prefix /canvas-meta to avoid conflict with canvas_router's /{canvas_name} wildcard
router.include_router(
    metadata_router,
    prefix="/canvas-meta",
    tags=["Canvas Metadata"],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Routes (Story 15.2)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    canvas_router, prefix="/canvas", tags=["Canvas"], responses={404: {"description": "Canvas not found"}}
)

# ═══════════════════════════════════════════════════════════════════════════════
# Agent Routes (Story 15.2)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    agents_router, prefix="/agents", tags=["Agents"], responses={500: {"description": "Agent call failed"}}
)

# ═══════════════════════════════════════════════════════════════════════════════
# Image Index Routes (Story 1.6)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    index_image_router,
    tags=["Index"],
    responses={
        400: {"description": "Invalid image data"},
        503: {"description": "Vision API unavailable"},
    },
)

# ═══════════════════════════════════════════════════════════════════════════════
# Review Routes (Story 15.2)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(review_router, prefix="/review", tags=["Review"])

# ═══════════════════════════════════════════════════════════════════════════════
# Monitoring Routes (Story 17.3)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 17.3 - Alert System & Dashboard
# [Source: docs/stories/17.3.story.md - AC 3-4]
router.include_router(
    monitoring_router,
    prefix="/metrics",
    tags=["Monitoring"],
    responses={500: {"description": "Monitoring service error"}},
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
    responses={404: {"description": "Operation/snapshot not found"}, 500: {"description": "Rollback service error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Memory Routes (Story 22.4)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 22.4 - 学习历史存储与查询API
# [Source: docs/stories/22.4.story.md - AC 1-6]
# [Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
router.include_router(
    memory_router,
    prefix="/memory",
    tags=["Memory"],
    responses={404: {"description": "Episode/concept not found"}, 500: {"description": "Memory service error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Debug Routes (Story 21.5.3)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 21.5.3 - Bug追踪日志系统
# [Source: docs/stories/21.5.3.story.md - AC 3-5]
# [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-3]
router.include_router(
    debug.router,
    prefix="/debug",
    tags=["Debug"],
    responses={404: {"description": "Bug not found"}, 500: {"description": "Debug service error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# RAG Routes (Story 12.4 - P0 BLOCKER FIX)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Story 12.4: Register RAG endpoint (was missing - Epic 12 invisible to users!)
# [Source: UltraThink深度调研报告 v2.0 - Section 10.1]
# [Source: backend/app/api/v1/endpoints/rag.py - 完整实现312行]
router.include_router(
    rag_router,
    prefix="/rag",
    tags=["RAG"],
    responses={503: {"description": "RAG service unavailable"}, 500: {"description": "RAG query failed"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Textbook Routes (方案A: 前端同步到后端)
# ═══════════════════════════════════════════════════════════════════════════════

# [Source: 计划文件 - 关键架构缺陷修复]
# Bridges frontend localStorage to backend .canvas-links.json
router.include_router(
    textbook_router,
    prefix="/textbook",
    tags=["Textbook"],
    responses={404: {"description": "Textbook not found"}, 500: {"description": "Textbook sync failed"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Multimodal Routes (Story 35.1)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 35.1 - Multimodal Upload/Management API
# [Source: docs/stories/35.1.story.md - AC 1-5]
router.include_router(
    multimodal_router,
    prefix="/multimodal",
    tags=["Multimodal"],
    responses={
        413: {"description": "File too large (max 50MB)"},
        415: {"description": "Unsupported media type"},
        500: {"description": "Multimodal service error"},
    },
)

# ═══════════════════════════════════════════════════════════════════════════════
# Intelligent Parallel Processing Routes (Story 33.1)
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 33.1 - Backend REST Endpoints
# [Source: docs/stories/33.1.story.md - AC 1-4]
# [Source: specs/api/parallel-api.openapi.yml]
router.include_router(
    intelligent_parallel_router,
    prefix="/canvas/intelligent-parallel",
    tags=["Intelligent Parallel"],
    responses={
        400: {"description": "Invalid request"},
        404: {"description": "Resource not found"},
        409: {"description": "Conflict - session already completed"},
        500: {"description": "Parallel processing error"},
    },
)

# ✅ Verified from Story 33.1 - Single Agent Retry Endpoint
# [Source: docs/stories/33.1.story.md - AC 5]
router.include_router(
    single_agent_router,
    prefix="/canvas",
    tags=["Intelligent Parallel"],
    responses={404: {"description": "Node or canvas not found"}, 500: {"description": "Agent execution error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Mastery Proficiency Routes (BKT + FSRS Hybrid)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    mastery_router,
    tags=["Mastery"],
    responses={
        400: {"description": "Invalid grade or level"},
        404: {"description": "Concept not found"},
        500: {"description": "Mastery engine error"},
    },
)

# ═══════════════════════════════════════════════════════════════════════════════
# Profile Routes (Story 5.3 - Learning Profile Panel)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    profile_router,
    tags=["Profile"],
    responses={404: {"description": "Node not found"}, 500: {"description": "Profile query error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Exam Session Routes (Story 5.4 - FSRS Review Dashboard)
# ═══════════════════════════════════════════════════════════════════════════════

router.include_router(
    exam_sessions_router, tags=["Exam Sessions"], responses={500: {"description": "Exam sessions query error"}}
)

# ═══════════════════════════════════════════════════════════════════════════════
# Exam CRUD Routes (Story 6.1-6.4: Exam Board Core Flow)
# ═══════════════════════════════════════════════════════════════════════════════

# Story 6.1: Exam session lifecycle (start/get/list/status)
# Story 6.2: Canvas content analysis + mode recommendation
# [Source: _bmad-output/implementation-artifacts/6-1-exam-board-generation.md]
router.include_router(
    exam_router,
    tags=["Exam"],
    responses={
        400: {"description": "Nesting prohibited or invalid request"},
        404: {"description": "Exam session not found"},
        500: {"description": "Exam service error"},
    },
)

# ═══════════════════════════════════════════════════════════════════════════════
# Context Routes (Story 3.4 - Learning Context Auto-Injection)
# ═══════════════════════════════════════════════════════════════════════════════

# Story 3.4: Tier 1 + Tier 2 learning context for --append-system-prompt
# [Source: _bmad-output/implementation-artifacts/3-4-learning-context-auto-injection.md#Task 5]
router.include_router(
    context_router,
    tags=["Context"],
    responses={500: {"description": "Context assembly error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Sync Routes (Story 1.5)
# ═══════════════════════════════════════════════════════════════════════════════

# Story 1.5: Canvas data sync from IndexedDB Outbox to Neo4j
# [Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md]
router.include_router(
    sync_router,
    prefix="/sync",
    tags=["Sync"],
    responses={503: {"description": "Neo4j connection unavailable"}, 500: {"description": "Sync processing error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Tips Routes (Story 3.6)
# ═══════════════════════════════════════════════════════════════════════════════

# Story 3.6: Tips annotation - user-selected dialogue text saved to Graphiti
# [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md]
router.include_router(
    tips_router,
    prefix="/tips",
    tags=["Tips"],
    responses={500: {"description": "Tips save error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Suggestions Routes (Story 3.7)
# ═══════════════════════════════════════════════════════════════════════════════

# Story 3.7: LLM relation suggestion for pullout nodes
# [Source: _bmad-output/implementation-artifacts/3-7-dialog-pullout-node.md]
router.include_router(
    suggestions_router,
    prefix="/suggestions",
    tags=["Suggestions"],
    responses={500: {"description": "Suggestion service error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Archive Routes (Story 3.8)
# ═══════════════════════════════════════════════════════════════════════════════

# Story 3.8: Conversation archive management (Hot-Warm-Cold)
# [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md]
router.include_router(
    archive_router,
    prefix="/archive",
    tags=["Archive"],
    responses={500: {"description": "Archive service error"}},
)

# ═══════════════════════════════════════════════════════════════════════════════
# Edge Rationale Routes (Story 4.1-4.4)
# ═══════════════════════════════════════════════════════════════════════════════

# Story 4.2: Edge dialog — Agent follow-up & rationale recording
# Story 4.4: Fallback — partial failure handling (207 Multi-Status)
# [Source: _bmad-output/implementation-artifacts/4-2-edge-dialog-agent-reasoning.md#Task 2]
router.include_router(
    edges_router,
    prefix="/edges",
    tags=["Edges"],
    responses={
        207: {"description": "Partial success — one write succeeded"},
        500: {"description": "Both writes failed"},
    },
)
