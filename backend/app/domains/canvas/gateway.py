"""
Canvas Domain Gateway — 画布与同步统一入口

Strangler Fig Pattern: 所有外部调用应通过此 gateway 访问 canvas 领域。

包含: canvas_service, sync_service, fallback_sync_service,
       recommendation_service, markdown_image_extractor
"""

from __future__ import annotations

# ── 画布文件 CRUD ──
from app.services.canvas_service import CanvasService

# ── Neo4j 同步 ──
from app.services.sync_service import SyncService

# ── JSON 回退同步 ──
from app.services.fallback_sync_service import FallbackSyncService

# ── 概念关联推荐 ──
from app.services.recommendation_service import RecommendationService

__all__ = [
    "CanvasService",
    "SyncService",
    "FallbackSyncService",
    "RecommendationService",
]
