# Canvas Learning System - Tips API Endpoint
# Story 3.6: Tips Writing to Graphiti (AC-2)
#
# POST /api/v1/tips - Save a user-annotated tip to Graphiti
#
# The tip contains selected text from dialogue, a user-provided title,
# and classification tags. It is written to Graphiti via the
# Agent self-report channel for future context injection (Story 3.4).
#
# [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 2.4]

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

tips_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class SaveTipRequest(BaseModel):
    """Request body for saving a tip annotation."""

    content: str = Field(..., min_length=1, description="The selected text content")
    title: str = Field(..., min_length=1, description="User-provided title for the tip")
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags: important, confused, inspiration, review",
    )
    node_id: str = Field(..., description="Source canvas node ID")
    source_timestamp: str = Field(
        ..., description="ISO timestamp of the source dialogue message"
    )
    event_type: str = Field(
        default="learning_tip",
        description=(
            "Entity type for memory_format canonical schema. "
            "Use 'learning_tip' for sidebar dialogue tips (Story 3.6) or "
            "'callout_annotation' for whiteboard Cmd+Shift+A callout (Story 1.16, P0-1)."
        ),
    )


class SaveTipResponse(BaseModel):
    """Response after saving a tip."""

    tip_id: str
    saved: bool
    status: str = "ok"
    message: str = ""


# ─── Story 2.4 Plan B Phase 2 (2026-05-14): Batch sync schema ───
# 用户在 callout 内继续输入"我的理解"后，plugin debounce 500ms 触发 batch sync。
# Backend 用 content_hash 做幂等去重 — 同 hash 跳过，不同 hash 创建 v2 EpisodicNode。


class CalloutBatchItem(BaseModel):
    """Single callout entry in batch sync."""

    tag: str = Field(..., description="tips | error | question | keypoint")
    tag_label: str = Field(default="", description="Display label e.g. '💡 Tips'")
    understanding: str = Field(
        default="",
        description="understood | fuzzy | not-understood | '' (无 checkbox)",
    )
    content: str = Field(..., min_length=1, description="Callout body content")
    content_hash: str = Field(
        ..., min_length=64, max_length=64, description="SHA256 hex"
    )


class BatchSyncRequest(BaseModel):
    """Plugin debounce 触发的整文件 callout batch 同步。"""

    node_id: str = Field(..., description="Source canvas node basename (no ext)")
    callouts: List[CalloutBatchItem] = Field(
        ..., description="All callouts parsed from the file"
    )
    source_timestamp: str = Field(..., description="ISO timestamp")


class BatchSyncResponse(BaseModel):
    """Aggregate result of batch sync."""

    total_received: int
    new_synced: int  # 新创建 episode 数
    skipped_duplicate: int  # content_hash 已存在跳过
    failed: int
    status: str = "ok"


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


class TipItem(BaseModel):
    """A single tip in the GET response."""

    tip_id: str
    content: str
    title: str
    tags: List[str] = Field(default_factory=list)
    node_id: str
    created_at: str = ""


class GetTipsResponse(BaseModel):
    """Response from GET /tips endpoint."""

    tips: List[TipItem]
    total: int


@tips_router.get(
    "",
    response_model=GetTipsResponse,
    summary="Get tips for a node from Graphiti",
    description="Retrieve all tip annotations for a given canvas node.",
)
async def get_tips(
    node_id: str,
) -> Dict[str, Any]:
    """
    Retrieve tips for a canvas node from Graphiti memory.

    Story 3.6: GET endpoint for frontend to read saved tips.

    Args:
        node_id: The canvas node ID to fetch tips for.

    Returns:
        GetTipsResponse with list of tips and total count.
    """
    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Search for tips related to this node
        results = await memory_svc.search_memories(
            query=f"learning_tip node_id:{node_id}",
            group_id=DEFAULT_GROUP_ID,
            limit=50,
        )

        tips: List[Dict[str, Any]] = []
        seen_tip_ids: set = set()
        for item in results:
            metadata = item.get("metadata", {})
            tip_id = metadata.get("tip_id")
            if metadata.get("node_id") == node_id and tip_id:
                # Deduplicate by tip_id to avoid repeated content
                if tip_id in seen_tip_ids:
                    continue
                seen_tip_ids.add(tip_id)
                tips.append(
                    TipItem(
                        tip_id=tip_id,
                        content=metadata.get("content", ""),
                        title=metadata.get("title", "Untitled"),
                        tags=metadata.get("tags", []),
                        node_id=node_id,
                        created_at=metadata.get("created_at", ""),
                    ).model_dump()
                )

        return GetTipsResponse(
            tips=tips,
            total=len(tips),
        ).model_dump()

    except Exception as e:
        logger.warning(f"[Story 3.6] Failed to get tips for node {node_id}: {e}")
        return GetTipsResponse(tips=[], total=0).model_dump()


@tips_router.post(
    "",
    response_model=SaveTipResponse,
    summary="Save a tip annotation to Graphiti",
    description="Save a user-annotated tip (selected dialogue text) to the "
    "Graphiti learning memory. The tip becomes available for future "
    "context injection (Story 3.4).",
)
async def save_tip(request: SaveTipRequest) -> Dict[str, Any]:
    """
    Save a tip annotation to Graphiti.

    Story 3.6 AC-2: User clicks "Write Tips" -> tip saved to Graphiti.
    The tip data includes: content (selected text), title (user input),
    tags, source node ID, and source dialogue timestamp.

    Args:
        request: The tip data to save.

    Returns:
        SaveTipResponse with tip_id and status.
    """
    tip_id = str(uuid.uuid4())

    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Build tip content for Graphiti
        tags_str = ", ".join(request.tags) if request.tags else "none"

        # P0-1 (2026-05-13): event_type 由 client 决定 — callout 走 callout_annotation,
        # 侧栏 tip 走 learning_tip。两者都通过 memory_format.py canonical schema 映射。
        # Whitelist 防止任意 event_type 注入（只允许已知的 2 种）。
        allowed_event_types = {"learning_tip", "callout_annotation"}
        effective_event_type = (
            request.event_type
            if request.event_type in allowed_event_types
            else "learning_tip"
        )

        await memory_svc.record_knowledge_entity(
            event_type=effective_event_type,
            content=(
                f"Tip: {request.title} | Content: {request.content} | Tags: {tags_str}"
            ),
            metadata={
                "tip_id": tip_id,
                "title": request.title,
                "content": request.content,
                "tags": request.tags,
                "node_id": request.node_id,
                "source_timestamp": request.source_timestamp,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            group_id=DEFAULT_GROUP_ID,
        )

        logger.info(
            f"[Story 3.6] Tip saved: id={tip_id} node={request.node_id} "
            f"title={request.title[:50]}"
        )

        return SaveTipResponse(
            tip_id=tip_id,
            saved=True,
            status="ok",
            message="Tips saved successfully",
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 3.6] Failed to save tip: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save tip: {str(e)}",
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# Story 2.4 Plan B Phase 2 (2026-05-14): Batch sync endpoint
# ═══════════════════════════════════════════════════════════════════════════════

# P0-8 (2026-05-14): in-memory cache for hash dedup race condition.
# Graphiti add_episode 是异步（~20-30s LLM extraction），Neo4j 查询可能 lag。
# In-memory cache 同步检查，杜绝同一 batch 处理窗口内重复 enqueue。
# 简单 LRU：> 1000 条时保留最新 800 条。多进程部署会丢一致性，但开发期单进程 OK。
_BATCH_HASH_CACHE: set[str] = set()
_BATCH_HASH_CACHE_MAX = 1000
_BATCH_HASH_CACHE_KEEP = 800


def _hash_cache_check_or_add(hash_marker: str) -> bool:
    """Return True if hash already seen (skip), False if new (proceed + add)."""
    if hash_marker in _BATCH_HASH_CACHE:
        return True
    _BATCH_HASH_CACHE.add(hash_marker)
    if len(_BATCH_HASH_CACHE) > _BATCH_HASH_CACHE_MAX:
        # Simple eviction: keep most recently added (rough — set has no order
        # but for in-process dedup this is acceptable)
        keep = list(_BATCH_HASH_CACHE)[-_BATCH_HASH_CACHE_KEEP:]
        _BATCH_HASH_CACHE.clear()
        _BATCH_HASH_CACHE.update(keep)
    return False


@tips_router.post(
    "/batch",
    response_model=BatchSyncResponse,
    summary="[DEPRECATED 2026-05-14] Plan B batch sync — DISABLED",
    description=(
        "DEPRECATED: 4 方对抗审查 (Canvas/Claude/ChatGPT-1/ChatGPT-2) 一致回退 "
        "Plan A. 此 endpoint 保留作 archive, 不再被 plugin 调用. 任何调用方将"
        "收到 410 Gone. 详见 _bmad-output/research/2026-05-14-plan-b-postmortem.md"
    ),
    deprecated=True,
)
async def batch_sync_callouts(request: BatchSyncRequest) -> Dict[str, Any]:
    # Plan B disable 2026-05-14 — 显式拒绝, 即使 plugin 误调也不写入 Graphiti
    raise HTTPException(
        status_code=410,
        detail=(
            "Plan B batch sync deprecated 2026-05-14. Plan A frontmatter "
            "tips[] is now the source of truth. See plan-b-postmortem.md."
        ),
    )
    # 下面是原 Plan B 实现, 保留代码作 archive 但不可达 (raise 之后):
    """Batch sync callouts using SHA256 content_hash for idempotency.

    Story 2.4 Plan B Phase 2 (2026-05-14).
    """
    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        new_synced = 0
        skipped = 0
        failed = 0

        for callout in request.callouts:
            try:
                # 双层幂等：(1) in-memory cache 杜绝异步 race，(2) Neo4j 持久去重
                hash_marker_for_cache = f"{request.node_id}|{callout.content_hash}"
                if _hash_cache_check_or_add(hash_marker_for_cache):
                    skipped += 1
                    continue
                already_exists = await memory_svc.find_episode_by_content_hash(
                    node_id=request.node_id,
                    content_hash=callout.content_hash,
                    group_id=DEFAULT_GROUP_ID,
                )
                if already_exists:
                    skipped += 1
                    continue

                # 创建新 episode（Graphiti 自动生成 valid_at 作时序版本标记）
                # P0-7 (2026-05-14): content_hash 必须内嵌到 content 字段才能持久化
                # 查询 — Graphiti 不存 metadata 到 EpisodicNode。`[hash:xxx]` 后缀
                # 让 find_episode_by_content_hash 能用 CONTAINS 匹配。
                tip_id = str(uuid.uuid4())
                tags_repr = (
                    f"tag:{callout.tag},understanding:{callout.understanding or 'none'}"
                )
                hash_marker = f"[hash:{callout.content_hash[:16]}]"
                await memory_svc.record_knowledge_entity(
                    event_type="callout_annotation",
                    content=(
                        f"Callout [{callout.tag_label}]: {callout.content} | "
                        f"Tags: {tags_repr} | {hash_marker}"
                    ),
                    metadata={
                        "tip_id": tip_id,
                        "title": f"{callout.tag_label} · {request.node_id}",
                        "content": callout.content,
                        "tag": callout.tag,
                        "understanding": callout.understanding,
                        "node_id": request.node_id,
                        "content_hash": callout.content_hash,
                        "source_timestamp": request.source_timestamp,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "batch_sync": True,
                    },
                    group_id=DEFAULT_GROUP_ID,
                )
                new_synced += 1
            except Exception as inner_e:
                logger.warning(
                    f"[Story 2.4 batch] Failed one callout (hash={callout.content_hash[:8]}): {inner_e}"
                )
                failed += 1

        logger.info(
            f"[Story 2.4 batch] node={request.node_id} "
            f"received={len(request.callouts)} new={new_synced} "
            f"skipped={skipped} failed={failed}"
        )

        return BatchSyncResponse(
            total_received=len(request.callouts),
            new_synced=new_synced,
            skipped_duplicate=skipped,
            failed=failed,
            status="ok",
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 2.4 batch] Batch sync failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch sync failed: {str(e)}",
        ) from e
