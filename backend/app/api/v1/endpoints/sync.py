# Canvas Learning System - Sync API Endpoint
# Story 1.5: Canvas Data Sync to Backend KG (AC-7)
"""
REST endpoint for batch-syncing canvas data from IndexedDB to Neo4j.

POST /api/v1/sync/batch — Receives a batch of create/update/delete
operations and applies them idempotently to Neo4j.

[Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 5]
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable
from pydantic import BaseModel, Field

from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id
from app.models.sync_models import SyncBatchRequest, SyncBatchResponse
from app.security import require_internal_api_key

logger = logging.getLogger(__name__)

sync_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Round-23 Story 8.4 — Relationship sync (frontmatter relationships[] → Graphiti)
# ═══════════════════════════════════════════════════════════════════════════════


class RelationshipSyncResponse(BaseModel):
    """Round-23 Story 8.4 — single-note 同步响应."""

    note_path: str
    synced: int = 0
    skipped: int = 0
    errors: List[str] = Field(default_factory=list)


class VaultRelationshipSyncResponse(BaseModel):
    """Round-23 Story 8.4 — full-vault 扫描响应."""

    files_scanned: int = 0
    total_synced: int = 0
    total_skipped: int = 0
    errors: List[str] = Field(default_factory=list)
    dry_run: bool = True


@sync_router.post(
    "/batch",
    response_model=SyncBatchResponse,
    summary="Batch sync canvas data to Neo4j",
    description=(
        "Receives a batch of canvas sync operations (create/update/delete) "
        "from the frontend Outbox and applies them idempotently to Neo4j. "
        "Individual operation failures are reported without aborting the batch. "
        "Requires the X-CLS-Internal-Key header (FR-KG-04 Phase 2). "
        "(Story 1.5 AC-7)"
    ),
    dependencies=[Depends(require_internal_api_key)],
    responses={
        403: {"description": "Invalid or missing internal API key"},
        500: {"description": "Unexpected logic error in sync pipeline"},
        503: {
            "description": (
                "Neo4j connection unavailable, OR internal API key not "
                "configured in production mode (fail-closed)"
            )
        },
    },
)
async def sync_batch(request: SyncBatchRequest) -> SyncBatchResponse:
    """Process a batch of canvas sync operations.

    FR-KG-04 Phase 4 Task 4.1: exception classification.

    The previous implementation caught every exception and returned 503
    "Neo4j unreachable". This hid logic bugs (ValueError, TypeError,
    KeyError from malformed payloads) behind a "service degraded" veneer.
    The new classification:

    - ``ServiceUnavailable`` / ``AuthError`` / ``ConnectionError`` → 503
      (genuine infrastructure issue — retrying might help)
    - ``Neo4jError`` (non-service) / anything else → 500
      (logic bug; retrying will not help, client should give up)

    Neither response body contains the raw exception text because that
    may leak driver state or internal paths. Only fixed strings like
    "Neo4j unavailable" / "Sync batch failed unexpectedly" are returned.

    [Source: Story 1.5 AC-7 — POST /api/v1/sync/batch]
    [Source: Story 1.5 AC-4 — idempotent Neo4j writes]
    """
    from app.services.sync_service import get_sync_service

    # Wave-5 Stage B 续 — P0 写入路径! 多 vault 串库就在这条 sync 路径出
    # bug. 注入 ContextVar 在调 sync_service 之前.
    resolve_vault_group_id(
        request.vault_id,
        subject_id=request.subject_id,
        legacy_group_id=request.group_id,
    )

    try:
        service = get_sync_service()
        return await service.process_sync_batch(request)
    except (ServiceUnavailable, AuthError, ConnectionError) as e:
        # Infrastructure-level failures → 503
        logger.error(
            "sync_batch_neo4j_unavailable: type=%s detail=%s",
            type(e).__name__,
            str(e)[:200],
        )
        raise HTTPException(
            status_code=503,
            detail="Neo4j unavailable",
        ) from e
    except Exception as e:
        # Everything else (logic bugs, unexpected Neo4jError) → 500
        # Use logger.exception to capture the full traceback for debugging,
        # but return a generic message so no internal state leaks.
        logger.exception(
            "sync_batch_unexpected_error: type=%s",
            type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Sync batch failed unexpectedly",
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# Round-23 Story 8.4 — Relationship sync endpoints (Round-14 残缺 #4 修复)
# ═══════════════════════════════════════════════════════════════════════════════


@sync_router.post(
    "/relationships/by-node",
    response_model=RelationshipSyncResponse,
    summary="Sync single node frontmatter relationships → Graphiti edges",
    dependencies=[Depends(require_internal_api_key)],
)
async def sync_relationships_by_node(
    note_path: str = Query(..., description="vault 相对路径 (如 '节点/A.md')"),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description=(
            "Wave-5 Stage B (Multi-vault P0) — 推荐必填. Plugin "
            "inferVaultId(app.vault.getName()). 空时 fallback 到 deprecated group_id."
        ),
    ),
    subject_id: Optional[str] = Query(
        default=None, description="可选 vault 内学科二级 namespace."
    ),
    group_id: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id.",
    ),
) -> RelationshipSyncResponse:
    """Round-23 Story 8.4 — 单节点 relationships → Graphiti edges 同步.

    Tauri Obsidian plugin 在 file-save 时调本 endpoint, 把 frontmatter
    relationships[] 推到 Graphiti 形成 edge graph.

    Errors:
        404: vault root 不可解析或 note 文件不存在.
    """
    from app.config import settings
    from app.services.relationship_sync_service import sync_relationships_for_note

    vault_root = getattr(settings, "canvas_base_path", None)
    if not vault_root:
        raise HTTPException(
            status_code=404,
            detail="vault root (canvas_base_path) not configured",
        )

    resolved_group_id = resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )

    result = await sync_relationships_for_note(
        note_path=note_path, vault_root=vault_root, group_id=resolved_group_id
    )

    return RelationshipSyncResponse(
        note_path=note_path,
        synced=result["synced"],
        skipped=result["skipped"],
        errors=result["errors"],
    )


@sync_router.post(
    "/relationships/vault",
    response_model=VaultRelationshipSyncResponse,
    summary="Full-vault scan + sync frontmatter relationships → Graphiti",
    dependencies=[Depends(require_internal_api_key)],
)
async def sync_relationships_vault(
    dry_run: bool = Query(default=True, description="True 默认仅扫描计数"),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description=(
            "Wave-5 Stage B (Multi-vault P0) — 推荐必填. Plugin inferVaultId. "
            "空时 fallback 到 deprecated group_id."
        ),
    ),
    subject_id: Optional[str] = Query(
        default=None, description="可选 vault 内学科二级 namespace."
    ),
    group_id: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id.",
    ),
) -> VaultRelationshipSyncResponse:
    """Round-23 Story 8.4 — 全量扫 vault 同步 frontmatter relationships.

    用户场景:
    - 切设备 / 重建 Graphiti 索引 (vault md 保留, Graphiti edge graph 丢)
    - 用户 bulk 编辑后一键 reconcile

    建议: 先 dry_run=True 看会写多少, 再 dry_run=False 实际跑.

    Errors:
        404: vault root 不可解析.
    """
    from app.config import settings
    from app.services.relationship_sync_service import sync_relationships_in_vault

    vault_root = getattr(settings, "canvas_base_path", None)
    if not vault_root:
        raise HTTPException(
            status_code=404,
            detail="vault root (canvas_base_path) not configured",
        )

    resolved_group_id = resolve_vault_group_id(
        vault_id, subject_id=subject_id, legacy_group_id=group_id
    )

    result = await sync_relationships_in_vault(
        vault_root=vault_root, group_id=resolved_group_id, dry_run=dry_run
    )

    return VaultRelationshipSyncResponse(
        files_scanned=result["files_scanned"],
        total_synced=result["total_synced"],
        total_skipped=result["total_skipped"],
        errors=result["errors"],
        dry_run=result["dry_run"],
    )
