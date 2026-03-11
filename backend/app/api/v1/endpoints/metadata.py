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

from app.dependencies import SettingsDep
from app.models import ErrorResponse
from app.models.metadata_models import (
    BatchIndexRequest,
    BatchIndexResponse,
    CanvasIndexRequest,
    CanvasIndexResponse,
    CanvasIndexStatusResponse,
    CanvasMetadataResponse,
    MetadataSource,
    SubjectMappingConfig,
)
from app.services.subject_resolver import SubjectResolver, get_subject_resolver

logger = logging.getLogger(__name__)


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
        from agentic_rag.clients.lancedb_client import LanceDBClient
        import os

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
        example="Math 54/离散数学.canvas"
    ),
    resolver: SubjectResolver = Depends(get_resolver)
) -> CanvasMetadataResponse:
    """
    Get metadata for a Canvas file.

    Returns:
    - **subject**: Subject identifier (e.g., "math54")
    - **category**: Category identifier (e.g., "math")
    - **group_id**: Graphiti group_id (e.g., "math54:离散数学")
    - **source**: How the metadata was resolved

    Resolution priority:
    1. Configuration file mapping
    2. Path-based auto-inference
    3. Default values

    [Source: Design doc - Phase 1.1 Canvas Metadata Query API]
    """
    try:
        info = resolver.resolve(canvas_path)

        return CanvasMetadataResponse(
            canvas_path=canvas_path,
            subject=info.subject,
            category=info.category,
            group_id=info.group_id,
            source=info.source
        )

    except Exception as e:
        logger.error(f"Failed to resolve metadata for {canvas_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve metadata: {str(e)}"
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
    canvas_path: str = Query(
        ...,
        description="Canvas file path",
        example="Math 54/离散数学.canvas"
    ),
    table_name: str = Query(
        default="canvas_nodes",
        description="LanceDB table name"
    ),
    resolver: SubjectResolver = Depends(get_resolver)
) -> CanvasIndexStatusResponse:
    """
    Get LanceDB index status for a Canvas file.

    Returns:
    - **indexed**: Whether the Canvas is indexed
    - **node_count**: Number of indexed nodes
    - **last_indexed**: Last indexing timestamp
    - **subject**: Subject used during indexing

    [Source: Design doc - Phase 1.2 LanceDB Index Status API]
    """
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
                table_name=table_name
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
                table_name=table_name
            )

        # ✅ Story 38.1 Fix: 使用 count_documents_by_canvas 替代空查询向量搜索
        # 问题：之前使用 search(query="") 导致向量化失败，始终返回空结果
        # 解决：使用 pandas WHERE 子句直接查询，不依赖向量搜索
        try:
            doc_info = await lancedb_client.count_documents_by_canvas(
                canvas_path=canvas_path,
                table_name=table_name
            )

            if doc_info["count"] > 0:
                return CanvasIndexStatusResponse(
                    canvas_path=canvas_path,
                    indexed=True,
                    node_count=doc_info["count"],
                    last_indexed=doc_info.get("last_indexed"),
                    subject=doc_info.get("subject"),
                    table_name=table_name
                )
            else:
                return CanvasIndexStatusResponse(
                    canvas_path=canvas_path,
                    indexed=False,
                    node_count=0,
                    last_indexed=None,
                    subject=None,
                    table_name=table_name
                )

        except Exception as e:
            logger.debug(f"Error querying index status: {e}")
            return CanvasIndexStatusResponse(
                canvas_path=canvas_path,
                indexed=False,
                node_count=0,
                last_indexed=None,
                subject=None,
                table_name=table_name
            )

    except Exception as e:
        logger.error(f"Failed to get index status for {canvas_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get index status: {str(e)}"
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
    resolver: SubjectResolver = Depends(get_resolver)
) -> CanvasIndexResponse:
    """
    Index a Canvas file to LanceDB.

    This endpoint:
    1. Resolves subject/category for the Canvas
    2. Reads Canvas nodes
    3. Vectorizes text content
    4. Stores in LanceDB with metadata

    [Source: Design doc - Phase 1.3 Manual Index Trigger API]
    """
    start_time = time.perf_counter()

    try:
        # Resolve metadata
        info = resolver.resolve(
            request.canvas_path,
            manual_subject=request.subject,
            manual_category=request.category
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
                message="LanceDB client not available"
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
                message=f"Canvas file not found: {full_path}"
            )

        # Index Canvas
        # ✅ Story 38.1 Fix: 读取节点后传递相对路径用于存储
        # 问题：之前传递 full_path 导致存储绝对路径，查询时用相对路径无法匹配
        import json
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)
            nodes = canvas_data.get("nodes", [])
        except Exception as e:
            logger.error(f"Failed to read canvas file: {e}")
            nodes = None

        node_count = await lancedb_client.index_canvas(
            canvas_path=request.canvas_path,  # ✅ 使用相对路径存储
            nodes=nodes,  # ✅ 传递已读取的节点
            table_name="canvas_nodes",
            subject=info.subject
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Indexed Canvas {request.canvas_path}: "
            f"{node_count} nodes, {duration_ms:.2f}ms"
        )

        return CanvasIndexResponse(
            canvas_path=request.canvas_path,
            success=True,
            node_count=node_count,
            subject=info.subject,
            category=info.category,
            group_id=info.group_id,
            duration_ms=duration_ms,
            message=None
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
            message=str(e)
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
    resolver: SubjectResolver = Depends(get_resolver)
) -> BatchIndexResponse:
    """
    Index multiple Canvas files to LanceDB.

    Limited to 50 files per request.

    [Source: Design doc - Batch Operations]
    """
    start_time = time.perf_counter()
    results = []
    success_count = 0
    failed_count = 0

    for canvas_path in request.canvas_paths:
        try:
            # Create individual request
            individual_request = CanvasIndexRequest(
                canvas_path=canvas_path,
                force=request.force
            )

            # Index
            result = await index_canvas(
                request=individual_request,
                settings=settings,
                resolver=resolver
            )

            results.append(result)

            if result.success:
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error(f"Batch index error for {canvas_path}: {e}")
            failed_count += 1
            results.append(CanvasIndexResponse(
                canvas_path=canvas_path,
                success=False,
                node_count=0,
                subject="unknown",
                category="unknown",
                group_id="unknown",
                duration_ms=0,
                message=str(e)
            ))

    return BatchIndexResponse(
        total=len(request.canvas_paths),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
        total_duration_ms=(time.perf_counter() - start_time) * 1000
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
):
    """
    Scan all .md files in the vault and index them to LanceDB vault_notes table.

    This enables RAG retrieval to reference vault markdown notes
    when generating AI explanations.
    """
    start_time = time.perf_counter()

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

        vault_path = settings.canvas_base_path
        skip_dirs_str = getattr(settings, 'VAULT_INDEX_SKIP_DIRS', '.obsidian,.git,.trash,node_modules')
        skip_dirs = [d.strip() for d in skip_dirs_str.split(",")]
        chunk_size = getattr(settings, 'VAULT_INDEX_CHUNK_SIZE', 500)
        chunk_overlap = getattr(settings, 'VAULT_INDEX_OVERLAP', 50)

        chunk_count = await lancedb_client.index_vault_notes(
            vault_path=vault_path,
            skip_dirs=skip_dirs,
            table_name="vault_notes",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            subject="cs188"
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"Vault indexing complete: {chunk_count} chunks, {duration_ms:.2f}ms")

        return {
            "success": True,
            "chunk_count": chunk_count,
            "vault_path": vault_path,
            "duration_ms": round(duration_ms, 2),
            "message": f"Indexed {chunk_count} chunks from vault .md files"
        }

    except Exception as e:
        logger.error(f"Vault indexing failed: {e}")
        return {
            "success": False,
            "chunk_count": 0,
            "duration_ms": (time.perf_counter() - start_time) * 1000,
            "message": str(e)
        }


@metadata_router.get(
    "/index/vault/status",
    summary="Get vault note indexing status",
    operation_id="vault_index_status",
)
async def vault_index_status():
    """Check the status of vault note indexing in LanceDB."""
    try:
        lancedb_client = get_lancedb_client()

        if lancedb_client is None:
            return {"indexed": False, "message": "LanceDB client not available"}

        if not lancedb_client._initialized:
            await lancedb_client.initialize()

        # Check if vault_notes table exists and get count
        if "vault_notes" in lancedb_client._tables_cache:
            table = lancedb_client._tables_cache["vault_notes"]
            count = len(table.to_pandas()) if hasattr(table, 'to_pandas') else 0
            return {
                "indexed": True,
                "chunk_count": count,
                "table_name": "vault_notes",
            }
        else:
            return {
                "indexed": False,
                "chunk_count": 0,
                "message": "vault_notes table not found. Call POST /index/vault first."
            }

    except Exception as e:
        return {"indexed": False, "message": str(e)}


@metadata_router.post(
    "/index/vault/incremental",
    summary="Incrementally index specific .md files to LanceDB",
    operation_id="index_vault_incremental",
)
async def index_vault_incremental(
    request: dict,
    settings: SettingsDep,
):
    """
    Incrementally index a list of .md files into the existing vault_notes table.

    Much faster than full rebuild — only processes the specified files.
    Designed to be called by the Obsidian plugin when files are modified.

    Request body: { "file_paths": ["path/to/note.md", ...] }
    file_paths are relative to the vault root.
    """
    start_time = time.perf_counter()
    file_paths = request.get("file_paths", [])

    if not file_paths:
        return {
            "success": False,
            "message": "No file_paths provided",
            "chunks_indexed": 0,
            "files_processed": 0,
            "duration_ms": 0,
        }

    try:
        lancedb_client = get_lancedb_client()
        if lancedb_client is None:
            return {
                "success": False,
                "message": "LanceDB client not available",
                "chunks_indexed": 0,
                "files_processed": 0,
                "duration_ms": 0,
            }

        if not lancedb_client._initialized:
            await lancedb_client.initialize()

        vault_path = settings.canvas_base_path
        total_chunks = 0
        files_ok = 0

        for rel_path in file_paths:
            import os
            abs_path = os.path.join(vault_path, rel_path)
            if not os.path.isfile(abs_path):
                logger.warning(f"Incremental index: file not found: {abs_path}")
                continue
            count = await lancedb_client.index_single_file(
                file_path=abs_path,
                table_name="vault_notes",
            )
            total_chunks += count
            files_ok += 1

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Incremental vault index: {files_ok}/{len(file_paths)} files, "
            f"{total_chunks} chunks, {duration_ms:.2f}ms"
        )

        return {
            "success": True,
            "chunks_indexed": total_chunks,
            "files_processed": files_ok,
            "files_requested": len(file_paths),
            "duration_ms": round(duration_ms, 2),
            "message": f"Indexed {total_chunks} chunks from {files_ok} files",
        }

    except Exception as e:
        logger.error(f"Incremental vault indexing failed: {e}")
        return {
            "success": False,
            "chunks_indexed": 0,
            "files_processed": 0,
            "duration_ms": (time.perf_counter() - start_time) * 1000,
            "message": str(e),
        }


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
    resolver: SubjectResolver = Depends(get_resolver)
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
    config: SubjectMappingConfig,
    resolver: SubjectResolver = Depends(get_resolver)
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
            detail="Failed to save configuration"
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
    resolver: SubjectResolver = Depends(get_resolver)
) -> SubjectMappingConfig:
    """
    Add or update a subject mapping rule.

    If a rule with the same pattern exists, it will be updated.
    """
    success = resolver.add_mapping(pattern, subject, category)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add mapping"
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
    resolver: SubjectResolver = Depends(get_resolver)
) -> SubjectMappingConfig:
    """
    Remove a subject mapping rule by pattern.
    """
    success = resolver.remove_mapping(pattern)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping with pattern '{pattern}' not found"
        )

    return resolver.get_config()


# =============================================================================
# Export
# =============================================================================

__all__ = ["metadata_router"]
