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

# CARD-G2-2 (2026-08-28): tips 作用域解析统一走 vault_scope 唯一解析点
from app.core.vault_scope import resolve_vault_group_id

logger = logging.getLogger(__name__)

tips_router = APIRouter()


def _resolve_tips_group_id(vault_id: str | None = None) -> str:
    """B2 修复 (2026-07-12 对抗审查): tips 写读统一落当前 vault 桶。

    CARD-G2-2 (2026-08-28): 私有 helper 改调 vault_scope 唯一解析点。
    语义收紧: 显式 vault_id 与进程 active vault 不一致时 409 fail-closed
    (原实现会静默为他 vault 构组); 缺省回退当前激活 vault 不变。
    写读两侧 (save/search/find_episode) 全部走本函数保持成对。

    ⚠️ 刻意**不接** subject_id (Codex round-1 MEDIUM-12): tips GET 端点
    无 subject 参数, 写侧若落 ``vault:<id>:<subject>`` 子组则读侧只查
    root group、永远回读不到。SaveTipRequest.subject_id 字段保留 (旧
    契约测试依赖) 但不参与构组; 要贯通须读写端点成对改造 = 后续卡。
    """
    return resolve_vault_group_id(vault_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class SaveTipRequest(BaseModel):
    """Request body for saving a tip annotation."""

    vault_id: str = Field(
        ...,
        min_length=1,
        description=(
            "B2 (2026-07-12) + P0-3 (2026-07-31) 改必填: vault 身份。"
            "插件端 inferVaultId(app.vault.getName()) 传。"
            "写侧禁止回退全局 vault — tips 统一落显式 vault 桶。"
        ),
    )

    subject_id: str | None = Field(
        default=None,
        description="可选 vault 内学科二级 (D16 group 规约; CARD-G2-2 加性补齐)",
    )
    content: str = Field(..., min_length=1, description="The selected text content")
    title: str = Field(..., min_length=1, description="User-provided title for the tip")
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags: important, confused, inspiration, review",
    )
    node_id: str = Field(..., description="Source canvas node ID")
    annotation_id: str = Field(
        default="",
        description=(
            "P0 (A+-prime): 稳定批注身份 cb-xxx (前端 wrapSelection 生成)。"
            "后端 write_callout 用它做 identity, 空则回退首行。"
        ),
    )
    source_timestamp: str = Field(..., description="ISO timestamp of the source dialogue message")
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


class SaveRelationRequest(BaseModel):
    """P4 (A+-prime): 派生关系原因实时上报 (Cmd+Shift+D 拉新节点)。

    走 Graphiti-native write_relation_reason (经 record_knowledge_entity), 不走
    sync.py 的 CANVAS_EDGE 投影。让'写下为什么拉出 → 立即读回'不必等重启回填。
    """

    vault_id: str = Field(
        ...,
        min_length=1,
        description=(
            "B2 (2026-07-12) + P0-3 (2026-07-31) 改必填: vault 身份。"
            "插件端 inferVaultId(app.vault.getName()) 传。"
            "写侧禁止回退全局 vault — tips 统一落显式 vault 桶。"
        ),
    )

    source_node_id: str = Field(..., description="持有 relationship 的派生节点 basename")
    target_node_id: str = Field(..., description="源节点 basename")
    relation_type: str = Field(default="related_to", description="prerequisite/refines/extends/...")
    reason: str = Field(default="", description="用户写的'为什么拉出/连接'")
    source_timestamp: str = Field(default="", description="ISO 用户操作时刻")


class SaveRelationResponse(BaseModel):
    saved: bool
    status: str = "written"
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
    content_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hex")
    annotation_id: str = Field(
        default="",
        description="P0 (A+-prime): 稳定批注身份 cb-xxx, 空=历史批注(回退首行)",
    )


class BatchSyncRequest(BaseModel):
    """Plugin debounce 触发的整文件 callout batch 同步。"""

    vault_id: str = Field(
        ...,
        min_length=1,
        description=(
            "B2 (2026-07-12) + P0-3 (2026-07-31) 改必填: vault 身份。"
            "插件端 inferVaultId(app.vault.getName()) 传。"
            "写侧禁止回退全局 vault — tips 统一落显式 vault 桶。"
        ),
    )

    node_id: str = Field(..., description="Source canvas node basename (no ext)")
    callouts: List[CalloutBatchItem] = Field(..., description="All callouts parsed from the file")
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
    vault_id: str = "",
) -> Dict[str, Any]:
    """
    Retrieve tips for a canvas node from Graphiti memory.

    Story 3.6: GET endpoint for frontend to read saved tips.

    Args:
        node_id: The canvas node ID to fetch tips for.

    Returns:
        GetTipsResponse with list of tips and total count.
    """
    # CARD-G2-2 Codex round-1 BLOCKER-2 整改: 解析必须在 try 之外 —
    # 原实现让 409 落进下方的宽 except, 被吞成 200 + 空 tips 列表
    # (跨 vault 错配伪装成「这个节点没有批注」)。
    group_id = _resolve_tips_group_id(vault_id)
    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Search for tips related to this node
        # B2 (2026-07-12): 读侧与写侧成对 — 同走 _resolve_tips_group_id
        results = await memory_svc.search_memories(
            query=f"learning_tip node_id:{node_id}",
            group_id=group_id,
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

    # CARD-G2-2 Codex round-1 BLOCKER-2 整改: 解析提到 try 之外, 否则
    # 409 会被下方宽 except 改写成 500 (插件看到的是「服务器错误」而非
    # 「vault 错配」, 且无法据此纠正)。
    group_id = _resolve_tips_group_id(request.vault_id)

    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Build tip content for Graphiti
        tags_str = ", ".join(request.tags) if request.tags else "none"

        # P0-1 (2026-05-13): event_type 由 client 决定 — callout 走 callout_annotation,
        # 侧栏 tip 走 learning_tip。两者都通过 memory_format.py canonical schema 映射。
        # Whitelist 防止任意 event_type 注入（只允许已知的 2 种）。
        allowed_event_types = {"learning_tip", "callout_annotation"}
        effective_event_type = request.event_type if request.event_type in allowed_event_types else "learning_tip"

        result = await memory_svc.record_knowledge_entity(
            event_type=effective_event_type,
            content=(f"Tip: {request.title} | Content: {request.content} | Tags: {tags_str}"),
            metadata={
                "tip_id": tip_id,
                "title": request.title,
                "content": request.content,
                "tags": request.tags,
                "node_id": request.node_id,
                "annotation_id": request.annotation_id,
                "source_timestamp": request.source_timestamp,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            group_id=group_id,
        )

        # A7 (P2): 诚实反映持久化结果 — 不再无条件 saved=True。
        write_status = result.get("status", "written") if isinstance(result, dict) else "written"
        degraded = write_status == "degraded"
        logger.info(
            f"[Story 3.6] Tip saved: id={tip_id} node={request.node_id} "
            f"title={request.title[:50]} status={write_status}"
        )

        return SaveTipResponse(
            tip_id=tip_id,
            saved=not degraded,
            status=write_status,
            message=("记忆服务未就绪，批注已暂存，将在服务就绪后自动入图" if degraded else "Tips saved successfully"),
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 3.6] Failed to save tip: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save tip: {str(e)}",
        ) from e


@tips_router.post(
    "/relation",
    response_model=SaveRelationResponse,
    summary="Save a derivation relation reason to Graphiti (P4)",
    description="派生节点时实时上报'为什么拉出'的关系原因 → Graphiti-native "
    "write_relation_reason。修 X1: 不必等启动回填即可读回。",
)
async def save_relation(request: SaveRelationRequest) -> Dict[str, Any]:
    """P4 (A+-prime): 派生关系原因实时入图。"""
    from app.services.memory_service import get_memory_service

    # CARD-G2-2 BLOCKER-2 整改: 解析在 try 之外 (409 不得被改写成 500)。
    group_id = _resolve_tips_group_id(request.vault_id)

    try:
        memory_svc = await get_memory_service()
        result = await memory_svc.record_knowledge_entity(
            event_type="node_derived",
            content=(request.reason or f"{request.source_node_id} -> {request.target_node_id}"),
            metadata={
                "node_id": request.source_node_id,
                "target_node_id": request.target_node_id,
                "relation_type": request.relation_type,
                "reason": request.reason,
                "source_timestamp": request.source_timestamp,
            },
            group_id=group_id,
        )
        write_status = result.get("status", "written") if isinstance(result, dict) else "written"
        degraded = write_status == "degraded"
        logger.info(
            f"[P4] Relation saved: {request.source_node_id} -> "
            f"{request.target_node_id} ({request.relation_type}) status={write_status}"
        )
        return SaveRelationResponse(
            saved=not degraded,
            status=write_status,
            message=("记忆服务未就绪，关系已暂存，将在服务就绪后自动入图" if degraded else "Relation saved"),
        ).model_dump()
    except Exception as e:
        logger.error(f"[P4] Failed to save relation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save relation: {str(e)}") from e


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
    summary="批注 debounce 批量同步 (RE-ENABLED 2026-06-11)",
    description=(
        "曾于 2026-05-14 废弃 (plan-b postmortem) — 该决策前提是'后端管道 "
        "G-FAKE 断裂, 写了也进不了记忆'。2026-06-10 后端重构为 Graphiti-native "
        "(record_knowledge_entity 结构化路由 → :Entity/RELATES_TO, 图级确定性 "
        "uuid MERGE 真幂等), 前提失效, 复活。调用方: 插件 CalloutSyncDebouncer "
        "(3s debounce, 静默), 收录用户在 callout 内续写的'我的理解'全文。"
    ),
)
async def batch_sync_callouts(request: BatchSyncRequest) -> Dict[str, Any]:
    """Batch sync callouts using SHA256 content_hash for idempotency.

    Story 2.4 Plan B Phase 2 (2026-05-14), re-enabled 2026-06-11.
    """
    # CARD-G2-2 Codex round-1 BLOCKER-2 整改 (三处):
    # (1) 循环外解析恰一次 —— 原实现每 item 解析 2 次 (N×2);
    # (2) 解析在幂等键写入之前 —— 原顺序会让被 409 拒绝的请求先污染
    #     _BATCH_HASH_CACHE, 客户端纠正 vault 后重试被误判「重复」而丢批注;
    # (3) 解析在 try 之外 —— 否则 409 被记成 item failure, 整体仍返回 200。
    group_id = _resolve_tips_group_id(request.vault_id)

    try:
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
                    group_id=group_id,
                )
                if already_exists:
                    skipped += 1
                    continue

                # 创建新 episode（Graphiti 自动生成 valid_at 作时序版本标记）
                # P0-7 (2026-05-14): content_hash 必须内嵌到 content 字段才能持久化
                # 查询 — Graphiti 不存 metadata 到 EpisodicNode。`[hash:xxx]` 后缀
                # 让 find_episode_by_content_hash 能用 CONTAINS 匹配。
                tip_id = str(uuid.uuid4())
                tags_repr = f"tag:{callout.tag},understanding:{callout.understanding or 'none'}"
                hash_marker = f"[hash:{callout.content_hash[:16]}]"
                batch_result = await memory_svc.record_knowledge_entity(
                    event_type="callout_annotation",
                    content=(f"Callout [{callout.tag_label}]: {callout.content} | Tags: {tags_repr} | {hash_marker}"),
                    metadata={
                        "tip_id": tip_id,
                        "title": f"{callout.tag_label} · {request.node_id}",
                        "content": callout.content,
                        "tag": callout.tag,
                        "understanding": callout.understanding,
                        "node_id": request.node_id,
                        "annotation_id": callout.annotation_id,
                        "content_hash": callout.content_hash,
                        "source_timestamp": request.source_timestamp,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "batch_sync": True,
                    },
                    group_id=group_id,
                )
                # A7 (P2): degraded 未入图, 不计入 synced
                if isinstance(batch_result, dict) and batch_result.get("status") == "degraded":
                    failed += 1
                else:
                    new_synced += 1
            except Exception as inner_e:
                logger.warning(f"[Story 2.4 batch] Failed one callout (hash={callout.content_hash[:8]}): {inner_e}")
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


# ═══════════════════════════════════════════════════════════════════════════════
# 批次5' (MEM-FLYWHEEL-2026-07-22, 燃料策略对账 §三): 批注过滤直连管道
# ═══════════════════════════════════════════════════════════════════════════════


class CalloutDirectRequest(BaseModel):
    """高价值批注 (question/error) 过滤直连入图的受控请求。

    过滤判据 (ChatGPT 燃料对账 R1): 只有「会改变下次出题/讲解行为」的批注
    直连入图; tip/hint/note/warning/info 留 frontmatter raw lane (蒸馏兜底)。
    """

    callout_id: str = Field(..., min_length=1, description="稳定批注身份 cb-xxx (幂等键)")
    callout_type: str = Field(..., description="仅收 question | error (端点侧再校验)")
    node_id: str = Field(..., min_length=1, description="所属节点 (文件 basename)")
    text: str = Field(..., min_length=1, description="批注原文")
    added_at: datetime = Field(
        ...,
        description=(
            "批注原始时间 (FrontmatterTipsSync 的 added_at)。时间戳守卫: 必填, "
            "禁止后端补『现在』— reference_time 错误会污染 Graphiti 事实失效顺序"
        ),
    )
    vault_id: str = Field(
        ...,
        min_length=1,
        description="vault 身份 (P0-3 改必填, 写侧禁止回退全局 vault)",
    )
    understanding: str = Field(default="", description="批注理解档 (可选)")


class CalloutDirectResponse(BaseModel):
    callout_id: str
    accepted: bool
    lane: str = Field(description="question_episode | error_candidate | rejected_type")
    message: str = ""


@tips_router.post(
    "/callout-direct",
    response_model=CalloutDirectResponse,
    summary="高价值批注过滤直连入图 (批次5')",
    description=(
        "question → json episode 经 worker 队列入语义影子图 (分钟级可检索); "
        "error → 错误候选区 (candidate_only 用户主权, 不直接入图)。"
        "低价值类型直接拒绝 — raw lane (frontmatter) 已有数据, 蒸馏兜底。"
    ),
)
async def callout_direct(request: CalloutDirectRequest) -> Dict[str, Any]:
    from app.services.learning_event_log import append_event

    # CARD-G2-2 Codex round-1 BLOCKER-2 整改: 解析必须先于任何早返与
    # 幂等事件落账 —— 原顺序下跨 vault 请求会先写 callout_ingested
    # (以 callout_id 为幂等键), 客户端纠正 vault 后重试被判「duplicate」,
    # 批注永久丢失。现在错配请求在写任何状态前就 409。
    group_id = _resolve_tips_group_id(request.vault_id)

    if request.callout_type not in ("question", "error"):
        return CalloutDirectResponse(
            callout_id=request.callout_id,
            accepted=False,
            lane="rejected_type",
            message="仅 question/error 直连; 其余类型走 frontmatter raw lane",
        ).model_dump()

    # 幂等: callout_ingested 事件以 callout_id 为键, 已记录过 = 已入过管道
    event_recorded = append_event(
        "callout_ingested",
        event_id=f"callout:{request.callout_id}",
        node_id=request.node_id,
        payload={"callout_type": request.callout_type, "text": request.text[:200]},
        effective_at=request.added_at.isoformat(),
    )
    if not event_recorded:
        return CalloutDirectResponse(
            callout_id=request.callout_id,
            accepted=False,
            lane="question_episode" if request.callout_type == "question" else "error_candidate",
            message="duplicate callout_id, 幂等跳过",
        ).model_dump()

    if request.callout_type == "question":
        # 陈述句化 episode → worker 队列 (背压/死信/免重试全复用),
        # reference_time = 批注原始时间 (时间戳守卫)。
        # e2e 实测修正 (2026-07-24): 纯 json episode 对疑问批注只抽出实体、
        # 0 关系边 (疑问句没有 fact 可抽), 而检索链以边为主 → 改为陈述句
        # 模板 (「用户提出疑问」本身是可抽取的事实), 结构化字段留 metadata。
        from app.services.episode_worker import EpisodeTask, get_episode_worker

        understanding_part = f"(理解自评: {request.understanding})" if request.understanding else ""
        body = f"用户在学习概念「{request.node_id}」时提出了疑问{understanding_part}: {request.text}"
        task = EpisodeTask(
            name=f"callout:{request.node_id}:{request.callout_id}",
            episode_body=body,
            group_id=group_id,
            source_description="obsidian.callout.direct",
            reference_time=request.added_at,
            metadata={
                "event_type": "callout_annotation",
                "node_id": request.node_id,
                "callout_id": request.callout_id,
            },
        )
        enqueued = get_episode_worker().enqueue(task)
        return CalloutDirectResponse(
            callout_id=request.callout_id,
            accepted=enqueued,
            lane="question_episode",
            message="enqueued" if enqueued else "worker queue unavailable (蒸馏兜底)",
        ).model_dump()

    # error → 候选区 (candidate_only 铁律: AI 只提名, 用户 accept 才入图)。
    # 分类走本地 LLM (~秒级), 后台执行不阻塞 plugin 静默 POST。
    import asyncio as _asyncio

    async def _nominate_error_candidate() -> None:
        try:
            from app.services.error_classifier import get_error_classifier
            from app.services.error_writer import write_error_dual
            from app.services.frontmatter_signals import _node_md_path

            node_path = _node_md_path(request.node_id)
            if node_path is None:
                logger.warning(f"[批次5'] error callout 无处落候选: node={request.node_id}")
                return
            classified = await get_error_classifier().classify_with_pedagogy(
                error_description=request.text,
                node_id=request.node_id,
                context="(user error callout, direct pipeline)",
            )
            await write_error_dual(
                file_path=node_path,
                error=classified,
                node_id=request.node_id,
                session_id="callout-direct",
                mode="candidate_only",
                group_id=group_id,
                ai_reason="用户手标错误批注 (Cmd+Shift+A), 过滤直连提名",
            )
        except Exception as e:  # noqa: BLE001 — 后台提名失败不影响批注本体
            logger.warning(f"[批次5'] error 候选提名失败 (frontmatter 仍有原文): {e}")

    _asyncio.get_event_loop().create_task(_nominate_error_candidate())
    return CalloutDirectResponse(
        callout_id=request.callout_id,
        accepted=True,
        lane="error_candidate",
        message="candidate nomination scheduled",
    ).model_dump()
