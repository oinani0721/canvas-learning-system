# Canvas Learning System - Metadata API Endpoints
# Story 38.1: Canvas Metadata Management System
"""
Canvas Metadata API endpoints.

Provides endpoints for:
- Querying Canvas metadata (subject, category, group_id)
- Checking LanceDB index status
- Triggering Canvas indexing
- Managing subject mapping configuration

[Source: Design doc - Phase 1 Backend API]
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.dependencies import SettingsDep
from app.models import ErrorResponse
from app.models.metadata_models import (
    BatchIndexRequest,
    BatchIndexResponse,
    CanvasIndexRequest,
    CanvasIndexResponse,
    CanvasIndexStatusResponse,
    CanvasMetadataResponse,
    SubjectMappingConfig,
)
from app.services.subject_resolver import SubjectResolver, get_subject_resolver

logger = logging.getLogger(__name__)


# CARD-G2-2 (2026-08-28): 本地克隆删除, 统一走 app.core.vault_scope 唯一
# 解析点。本文件此前的双缺失姿势 (G-DEFAULT 根治 2026-07-10: 回退 active
# vault + 二级透传) 已并入 vault_scope 统一契约。
from app.core.vault_scope import resolve_vault_group_id as _resolve_vault_group_id


# =============================================================================
# Router Setup
# =============================================================================

metadata_router = APIRouter(
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)


# =============================================================================
# Dependencies
# =============================================================================


def get_resolver() -> SubjectResolver:
    """Get SubjectResolver dependency."""
    return get_subject_resolver()


def get_lancedb_client():
    """
    Get LanceDB client dependency.

    Lazy import to avoid circular dependencies.

    ✅ Story 38.1 Fix: 使用实际存储数据的路径
    """
    try:
        import os

        from agentic_rag.clients.lancedb_client import LanceDBClient

        # 直接使用默认相对路径 - LanceDBClient 默认使用 'backend/data/lancedb'
        # 当从 backend/ 目录运行时，实际路径是 backend/backend/data/lancedb
        # 我们保持默认行为，确保索引和查询使用同一路径
        client = LanceDBClient()

        logger.debug(f"LanceDB client created with default path")

        return client
    except ImportError as e:
        logger.warning(f"LanceDB client not available: {e}")
        return None


# =============================================================================
# Canvas Metadata Endpoints
# =============================================================================


@metadata_router.get(
    "/metadata",
    response_model=CanvasMetadataResponse,
    summary="Get Canvas metadata",
    operation_id="get_canvas_metadata",
)
async def get_canvas_metadata(
    canvas_path: str = Query(
        ...,
        description="Canvas file path (relative to vault)",
        example="Math 54/离散数学.canvas",
    ),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 防跨 vault 元数据混淆.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(default=None, deprecated=True, description="Deprecated — 改用 vault_id."),
    resolver: SubjectResolver = Depends(get_resolver),
) -> CanvasMetadataResponse:
    """
    Get metadata for a Canvas file.

    Returns:
    - **subject**: Subject identifier (e.g., "math54")
    - **category**: Category identifier (e.g., "math")
    - **group_id**: Graphiti group_id — D16 规定 vault: 前缀
      (vault:<vault_id>[:<subject_id>]); SubjectResolver 在其上再拼 canvas 段,
      产出四段组合形态。示例 "vault:cs_61b:math54:离散数学" 中的 vault 段是
      **部署期变量占位符** (取自 get_current_vault_id()), 实际值随部署而变 — 勿硬编码
    - **source**: How the metadata was resolved

    Resolution priority:
    1. Configuration file mapping
    2. Path-based auto-inference
    3. Default values

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填, 注入 ContextVar 防跨 vault 元数据混淆.

    [Source: Design doc - Phase 1.1 Canvas Metadata Query API]
    """
    _resolve_vault_group_id(
        vault_id,
        subject_id=subject_id,
        canvas_path=canvas_path,
        legacy_group_id=group_id,
    )

    try:
        info = resolver.resolve(canvas_path)

        return CanvasMetadataResponse(
            canvas_path=canvas_path,
            subject=info.subject,
            category=info.category,
            group_id=info.group_id,
            source=info.source,
        )

    except Exception as e:
        logger.error(f"Failed to resolve metadata for {canvas_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve metadata: {str(e)}",
        )


# =============================================================================
# LanceDB Index Status Endpoints
# =============================================================================


@metadata_router.get(
    "/index-status",
    response_model=CanvasIndexStatusResponse,
    summary="Get Canvas index status",
    operation_id="get_canvas_index_status",
)
async def get_canvas_index_status(
    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),
    table_name: str = Query(default="canvas_nodes", description="LanceDB table name"),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 防 LanceDB 索引串库.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(default=None, deprecated=True, description="Deprecated — 改用 vault_id."),
    resolver: SubjectResolver = Depends(get_resolver),
) -> CanvasIndexStatusResponse:
    """
    Get LanceDB index status for a Canvas file.

    Returns:
    - **indexed**: Whether the Canvas is indexed
    - **node_count**: Number of indexed nodes
    - **last_indexed**: Last indexing timestamp
    - **subject**: Subject used during indexing

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填, 注入 ContextVar 防 LanceDB 索引串库.

    [Source: Design doc - Phase 1.2 LanceDB Index Status API]
    """
    _resolve_vault_group_id(
        vault_id,
        subject_id=subject_id,
        canvas_path=canvas_path,
        legacy_group_id=group_id,
    )

    try:
        # Get LanceDB client
        lancedb_client = get_lancedb_client()

        if lancedb_client is None:
            return CanvasIndexStatusResponse(
                canvas_path=canvas_path,
                indexed=False,
                node_count=0,
                last_indexed=None,
                subject=None,
                table_name=table_name,
            )

        # Initialize client if needed
        if not lancedb_client._initialized:
            await lancedb_client.initialize()

        # Check if table exists and query for canvas
        stats = lancedb_client.get_stats()

        if table_name not in stats.get("tables", []):
            return CanvasIndexStatusResponse(
                canvas_path=canvas_path,
                indexed=False,
                node_count=0,
                last_indexed=None,
                subject=None,
                table_name=table_name,
            )

        # ✅ Story 38.1 Fix: 使用 count_documents_by_canvas 替代空查询向量搜索
        # 问题：之前使用 search(query="") 导致向量化失败，始终返回空结果
        # 解决：使用 pandas WHERE 子句直接查询，不依赖向量搜索
        try:
            doc_info = await lancedb_client.count_documents_by_canvas(canvas_path=canvas_path, table_name=table_name)

            if doc_info["count"] > 0:
                return CanvasIndexStatusResponse(
                    canvas_path=canvas_path,
                    indexed=True,
                    node_count=doc_info["count"],
                    last_indexed=doc_info.get("last_indexed"),
                    subject=doc_info.get("subject"),
                    table_name=table_name,
                )
            else:
                return CanvasIndexStatusResponse(
                    canvas_path=canvas_path,
                    indexed=False,
                    node_count=0,
                    last_indexed=None,
                    subject=None,
                    table_name=table_name,
                )

        except (RuntimeError, ConnectionError, OSError) as e:
            logger.debug(f"Error querying index status: {e}")
            return CanvasIndexStatusResponse(
                canvas_path=canvas_path,
                indexed=False,
                node_count=0,
                last_indexed=None,
                subject=None,
                table_name=table_name,
            )

    except Exception as e:
        logger.error(f"Failed to get index status for {canvas_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get index status: {str(e)}",
        )


# =============================================================================
# Canvas Indexing Endpoints
# =============================================================================


@metadata_router.post(
    "/index",
    response_model=CanvasIndexResponse,
    summary="Index Canvas to LanceDB",
    operation_id="index_canvas",
)
async def index_canvas(
    request: CanvasIndexRequest,
    settings: SettingsDep,
    resolver: SubjectResolver = Depends(get_resolver),
) -> CanvasIndexResponse:
    """
    Index a Canvas file to LanceDB.

    This endpoint:
    1. Resolves subject/category for the Canvas
    2. Reads Canvas nodes
    3. Vectorizes text content
    4. Stores in LanceDB with metadata

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - request.vault_id 推荐必填, 注入 ContextVar 防 LanceDB 索引串库.

    [Source: Design doc - Phase 1.3 Manual Index Trigger API]
    """
    # Wave-5 Stage B — vault_id ContextVar 注入
    # CARD-G2-2 Codex round-1 HIGH-11 整改: HTTP handler 解析恰一次, 索引
    # 本体下沉 _index_canvas_impl —— batch 端点改调 impl, 总解析次数从
    # 1+N 降回每请求 1 次 (硬边界3「每请求只解析一次 VaultScope」)。
    _resolve_vault_group_id(
        request.vault_id,
        subject_id=request.subject_id,
        canvas_path=request.canvas_path,
    )
    return await _index_canvas_impl(request, settings, resolver)


async def _index_canvas_impl(
    request: CanvasIndexRequest,
    settings: SettingsDep,
    resolver: SubjectResolver,
) -> CanvasIndexResponse:
    """索引本体 (不解析 vault scope — 调用方必须已解析恰一次)。"""
    start_time = time.perf_counter()

    try:
        # Resolve metadata
        info = resolver.resolve(
            request.canvas_path,
            manual_subject=request.subject,
            manual_category=request.category,
        )

        # Get LanceDB client
        lancedb_client = get_lancedb_client()

        if lancedb_client is None:
            return CanvasIndexResponse(
                canvas_path=request.canvas_path,
                success=False,
                node_count=0,
                subject=info.subject,
                category=info.category,
                group_id=info.group_id,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                message="LanceDB client not available",
            )

        # Initialize client
        if not lancedb_client._initialized:
            await lancedb_client.initialize()

        # Build full path
        canvas_base_path = settings.canvas_base_path
        full_path = f"{canvas_base_path}/{request.canvas_path}"

        # Check if file exists
        import os

        if not os.path.exists(full_path):
            return CanvasIndexResponse(
                canvas_path=request.canvas_path,
                success=False,
                node_count=0,
                subject=info.subject,
                category=info.category,
                group_id=info.group_id,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Canvas file not found: {full_path}",
            )

        # Index Canvas
        # ✅ Story 38.1 Fix: 读取节点后传递相对路径用于存储
        # 问题：之前传递 full_path 导致存储绝对路径，查询时用相对路径无法匹配
        import json

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                canvas_data = json.load(f)
            nodes = canvas_data.get("nodes", [])
        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.error(f"Failed to read canvas file: {e}")
            nodes = None

        node_count = await lancedb_client.index_canvas(
            canvas_path=request.canvas_path,  # ✅ 使用相对路径存储
            nodes=nodes,  # ✅ 传递已读取的节点
            table_name="canvas_nodes",
            subject=info.subject,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"Indexed Canvas {request.canvas_path}: {node_count} nodes, {duration_ms:.2f}ms")

        return CanvasIndexResponse(
            canvas_path=request.canvas_path,
            success=True,
            node_count=node_count,
            subject=info.subject,
            category=info.category,
            group_id=info.group_id,
            duration_ms=duration_ms,
            message=None,
        )

    except Exception as e:
        logger.error(f"Failed to index Canvas {request.canvas_path}: {e}")
        return CanvasIndexResponse(
            canvas_path=request.canvas_path,
            success=False,
            node_count=0,
            subject=request.subject or "unknown",
            category=request.category or "unknown",
            group_id="unknown",
            duration_ms=(time.perf_counter() - start_time) * 1000,
            message=str(e),
        )


@metadata_router.post(
    "/index/batch",
    response_model=BatchIndexResponse,
    summary="Batch index multiple Canvas files",
    operation_id="batch_index_canvas",
)
async def batch_index_canvas(
    request: BatchIndexRequest,
    settings: SettingsDep,
    resolver: SubjectResolver = Depends(get_resolver),
) -> BatchIndexResponse:
    """
    Index multiple Canvas files to LanceDB.

    Limited to 50 files per request.

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - request.vault_id 推荐必填, 注入 ContextVar 让批量索引 vault scoped.

    [Source: Design doc - Batch Operations]
    """
    start_time = time.perf_counter()

    # Wave-5 Stage B — vault_id ContextVar 注入
    _resolve_vault_group_id(
        request.vault_id,
        subject_id=request.subject_id,
    )

    results = []
    success_count = 0
    failed_count = 0

    for canvas_path in request.canvas_paths:
        try:
            # Create individual request — 透传 vault_id 让 index_canvas 也注入
            individual_request = CanvasIndexRequest(
                canvas_path=canvas_path,
                force=request.force,
                vault_id=request.vault_id,
                subject_id=request.subject_id,
            )

            # Index — 调 impl 而非 HTTP handler (scope 已在循环外解析一次)
            result = await _index_canvas_impl(individual_request, settings, resolver)

            results.append(result)

            if result.success:
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error(f"Batch index error for {canvas_path}: {e}")
            failed_count += 1
            results.append(
                CanvasIndexResponse(
                    canvas_path=canvas_path,
                    success=False,
                    node_count=0,
                    subject="unknown",
                    category="unknown",
                    group_id="unknown",
                    duration_ms=0,
                    message=str(e),
                )
            )

    return BatchIndexResponse(
        total=len(request.canvas_paths),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
        total_duration_ms=(time.perf_counter() - start_time) * 1000,
    )


# =============================================================================
# Vault-wide Note Indexing Endpoints
# =============================================================================


@metadata_router.post(
    "/index/vault",
    summary="Index all .md files in the vault to LanceDB",
    operation_id="index_vault_notes",
)
async def index_vault_notes(
    settings: SettingsDep,
    force_rebuild: bool = False,
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 让 vault notes 索引 vault scoped.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(default=None, deprecated=True, description="Deprecated — 改用 vault_id."),
):
    """
    Scan all .md files in the vault and index them to LanceDB vault_notes table.

    This enables RAG retrieval to reference vault markdown notes
    when generating AI explanations.

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填, 注入 ContextVar 让 vault_notes 表 vault scoped.

    Args:
        force_rebuild: When True, treat all files as new and re-index everything.
            Use after RAG-P0 schema changes (e.g. adding doc_type column) to
            wipe legacy chunks and rebuild with the new metadata. The
            _check_and_fix_dimension_mismatch path will auto-drop the table
            if the schema is incompatible.
    """
    start_time = time.perf_counter()

    # Wave-5 Stage B — vault_id ContextVar 注入(缺省回退当前激活 vault,见 _resolve_vault_group_id)
    effective_group_id = _resolve_vault_group_id(vault_id, subject_id=subject_id, legacy_group_id=group_id)

    try:
        lancedb_client = get_lancedb_client()

        if lancedb_client is None:
            return {
                "success": False,
                "message": "LanceDB client not available",
                "chunk_count": 0,
                "duration_ms": 0,
            }

        if not lancedb_client._initialized:
            await lancedb_client.initialize()

        if force_rebuild:
            # Sprint-1 (2026-07-10): 真 drop-and-rebuild —— 此前 force_rebuild 只把所有
            # 文件当新文件重扫,不清旧行,导致跨 vault/跨时代残留(实测 3534 行旧数据被
            # 检索命中)。先删本 vault 的前缀表再重建。
            try:
                stale_table = lancedb_client.resolve_table_name("vault_notes")
                lancedb_client._db.drop_table(stale_table, ignore_missing=True)
                # ⛔ 必须同步失效表句柄缓存(照抄 rebuild_index/drop_vault_tables 姿势)——
                # 只 drop 不清缓存会让后续写入落在已删表的幽灵句柄上,产出损坏 manifest
                # (2026-07-10 实测: count_rows=50 但数据文件 Not found)。
                lancedb_client._tables_cache.pop(stale_table, None)
                logger.info(
                    "force_rebuild: dropped stale table '%s' before reindex",
                    stale_table,
                )
            except Exception as drop_err:
                logger.warning("force_rebuild: drop stale table failed (continuing): %s", drop_err)

        vault_path = settings.canvas_base_path
        # RAG-S1 (2026-08-03): settings.VAULT_INDEX_SKIP_DIRS 是黑名单唯一权威源
        # (config.py)。此前 getattr 的第三参数是一份永远不会被使用的死拷贝
        # (pydantic 字段总存在)——三份拷贝漂移风险, 已删。
        # P1-02 (Codex 审查 2026-08-19): 改走 effective_vault_skip_dirs() ——
        # 直接 split 会让 env 覆盖撤掉信息隔离铁律 (检验白板/验收单)。
        skip_dirs = settings.effective_vault_skip_dirs()
        chunk_size = getattr(settings, "VAULT_INDEX_CHUNK_SIZE", 500)
        chunk_overlap = getattr(settings, "VAULT_INDEX_OVERLAP", 50)

        chunk_count = await lancedb_client.index_vault_notes(
            vault_path=vault_path,
            skip_dirs=skip_dirs,
            table_name="vault_notes",
            max_tokens=chunk_size,
            overlap_tokens=chunk_overlap,
            # G-DEFAULT 根治 (2026-07-10): 行级 subject 用派生的 vault: 前缀 group,
            # 不再写死 DEFAULT_GROUP_ID(cs188)——违反 C-3 且多 vault 下检索泄漏。
            subject=effective_group_id,
            force_rebuild=force_rebuild,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"Vault indexing complete: {chunk_count} chunks, {duration_ms:.2f}ms")

        return {
            "success": True,
            "chunk_count": chunk_count,
            "vault_path": vault_path,
            "duration_ms": round(duration_ms, 2),
            "message": f"Indexed {chunk_count} chunks from vault .md files",
        }

    except Exception as e:
        logger.error(f"Vault indexing failed: {e}")
        return {
            "success": False,
            "chunk_count": 0,
            "duration_ms": (time.perf_counter() - start_time) * 1000,
            "message": str(e),
        }


@metadata_router.get(
    "/index/vault/status",
    summary="Get vault note indexing status",
    operation_id="vault_index_status",
)
async def vault_index_status(
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 让 status 查询 vault scoped.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(default=None, deprecated=True, description="Deprecated — 改用 vault_id."),
):
    """Check the status of vault note indexing in LanceDB.

    Wave-5 Stage B (2026-05-12) — vault_id 推荐必填.
    RAG-S1 (2026-08-03):
    - 修复裸表名 bug: 此前查 _tables_cache["vault_notes"] (裸 key + 缓存句柄),
      对前缀表 vault (canvas_vault_vault_notes, 3604 行) 永远报 indexed:false。
      改走 resolve_table_name + 每次 open_table (T3 stale-handle 纪律)。
    - 新增 freshness 遥测: last_index_at / pending_depth / lag_seconds / stale
      (orchestrator 关闭时如实报 freshness=None, 不伪造)。
    """
    # Wave-5 Stage B — vault_id ContextVar 注入
    _resolve_vault_group_id(vault_id, subject_id=subject_id, legacy_group_id=group_id)

    try:
        lancedb_client = get_lancedb_client()

        if lancedb_client is None:
            return {"indexed": False, "message": "LanceDB client not available"}

        if not lancedb_client._initialized:
            # RAG-S1: read-only status query — connect only. Full initialize()
            # loads CPU embedding weights (~9.5s measured PER REQUEST since
            # get_lancedb_client() builds a fresh instance every call).
            lancedb_client.connect_lightweight()

        from app.services.vault_index_orchestrator import (
            get_vault_index_orchestrator,
        )

        orch = get_vault_index_orchestrator()
        freshness = orch.freshness() if orch is not None else None

        resolved_table = lancedb_client.resolve_table_name("vault_notes")
        existing_tables = lancedb_client._db.table_names() if lancedb_client._db is not None else []
        if resolved_table in existing_tables:
            table = lancedb_client._db.open_table(resolved_table)
            count = table.count_rows()
            return {
                "indexed": True,
                "chunk_count": count,
                "table_name": resolved_table,
                "freshness": freshness,
                "orchestrator_enabled": orch is not None,
            }
        return {
            "indexed": False,
            "chunk_count": 0,
            "table_name": resolved_table,
            "freshness": freshness,
            "orchestrator_enabled": orch is not None,
            "message": f"table '{resolved_table}' not found. Call POST /index/vault first.",
        }

    except Exception as e:
        return {"indexed": False, "message": str(e)}


# RAG-S2 T5 M6 quarantine (2026-08-10): incremental 端点退役 — 与 orchestrator
# worker 是两个并发写者 (delete-before-insert 交错可产双份 chunk), 且曾是考题
# 入库旁路 (lancedb_client.index_single_file 直写)。全仓无活调用方 (2026-09-01
# CARD-G2-5 round-3 复核实查: frontend 无 refresh-changed 命中, 该注释旧句
# "前端走 refresh-changed" 不实, 已更正; 无产线消费方)。
# 姿势照抄 vault.py P0-3 410 隔离先例; 实现机器 (index_single_file) 保留未删。
@metadata_router.post(
    "/index/vault/incremental",
    deprecated=True,
    summary="QUARANTINED (410) — use POST /api/v1/index/refresh-changed",
    operation_id="index_vault_incremental",
    description=(
        "RAG-S2 T5 quarantine (2026-08-10): this endpoint raced the "
        "orchestrator worker (two concurrent writers; interleaved "
        "delete-before-insert can duplicate chunks) and once bypassed the "
        "exam-question indexing blacklist. Incremental indexing goes through "
        "POST /api/v1/index/refresh-changed (enqueued into the serial "
        "orchestrator worker)."
    ),
)
async def index_vault_incremental(request: dict):
    """410 Gone — 增量索引统一走 orchestrator 串行 worker (M6 收编=退役)。"""
    logger.warning(
        "[M6-INCREMENTAL-QUARANTINE] blocked direct incremental index "
        "(RAG-S2 T5; concurrent-writer + exam-bypass risk) files=%s",
        len(request.get("file_paths", []) or []),
    )
    return JSONResponse(
        status_code=410,
        content={
            "error": "gone",
            "detail": (
                "Incremental vault indexing via this endpoint is quarantined "
                "(RAG-S2 T5, 2026-08-10): it raced the orchestrator worker "
                "(duplicate chunks) and bypassed exam isolation. Use "
                "POST /api/v1/index/refresh-changed instead — it enqueues "
                "into the serial orchestrator worker."
            ),
        },
    )


# =============================================================================
# Subject Mapping Configuration Endpoints
# =============================================================================


@metadata_router.get(
    "/config/subject-mapping",
    response_model=SubjectMappingConfig,
    summary="Get subject mapping configuration",
    operation_id="get_subject_mapping",
)
async def get_subject_mapping(
    resolver: SubjectResolver = Depends(get_resolver),
) -> SubjectMappingConfig:
    """
    Get the current subject mapping configuration.

    Returns the configuration used to resolve Canvas metadata.

    [Source: Design doc - Phase 2 Configuration System]
    """
    return resolver.get_config()


@metadata_router.put(
    "/config/subject-mapping",
    response_model=SubjectMappingConfig,
    summary="Update subject mapping configuration",
    operation_id="update_subject_mapping",
)
async def update_subject_mapping(
    config: SubjectMappingConfig, resolver: SubjectResolver = Depends(get_resolver)
) -> SubjectMappingConfig:
    """
    Update the subject mapping configuration.

    Saves to subject_mapping.yaml and reloads.

    [Source: Design doc - Phase 2 Configuration System]
    """
    success = resolver.update_config(config)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save configuration",
        )

    return resolver.get_config()


@metadata_router.post(
    "/config/subject-mapping/add",
    response_model=SubjectMappingConfig,
    summary="Add a subject mapping rule",
    operation_id="add_subject_mapping_rule",
)
async def add_subject_mapping_rule(
    pattern: str = Query(..., description="Folder pattern"),
    subject: str = Query(..., description="Subject identifier"),
    category: str = Query(..., description="Category identifier"),
    resolver: SubjectResolver = Depends(get_resolver),
) -> SubjectMappingConfig:
    """
    Add or update a subject mapping rule.

    If a rule with the same pattern exists, it will be updated.
    """
    success = resolver.add_mapping(pattern, subject, category)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add mapping",
        )

    return resolver.get_config()


@metadata_router.delete(
    "/config/subject-mapping/remove",
    response_model=SubjectMappingConfig,
    summary="Remove a subject mapping rule",
    operation_id="remove_subject_mapping_rule",
)
async def remove_subject_mapping_rule(
    pattern: str = Query(..., description="Pattern to remove"),
    resolver: SubjectResolver = Depends(get_resolver),
) -> SubjectMappingConfig:
    """
    Remove a subject mapping rule by pattern.
    """
    success = resolver.remove_mapping(pattern)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping with pattern '{pattern}' not found",
        )

    return resolver.get_config()


# =============================================================================
# Export
# =============================================================================

__all__ = ["metadata_router"]
