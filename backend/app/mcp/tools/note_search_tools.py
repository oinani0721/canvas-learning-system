# Canvas Learning System - MCP Note Search Tool
# F2: Expose RAG retrieval pipeline as MCP tool for Agent SDK
#
# Enables Claude to autonomously search the user's Vault notes during
# conversation, supporting MVP #10 (笔记精准检索返回) and the core system
# requirement "笔记片段精准检索系统".
#
# Uses the full RAG pipeline (4-source parallel retrieval + fusion + reranking)
# via RAGService.query(), which includes:
#   - LanceDB + BGE-M3 semantic search (vault_notes)
#   - Graphiti knowledge graph search
#   - Multimodal retrieval (images/PDFs)
#   - Quality checking + context compression
#
# [Source: S18-8 F2 decision — MCP note_search tool, fastapi_mcp expose RAG API]
# [Source: MVP #10 — 笔记精准检索返回]

import logging
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Input / Output Models
# ═══════════════════════════════════════════════════════════════════════════════


class NoteSearchInput(BaseModel):
    """Input for the search_notes MCP tool."""

    query: str = Field(
        ...,
        description="Natural language search query. Supports Chinese and English.",
    )
    canvas_file: Optional[str] = Field(
        None,
        description="Canvas file path to scope search. When set, results are filtered to notes related to this canvas.",
    )
    subject_id: Optional[str] = Field(
        None,
        description="Subject ID for multi-subject scope isolation (e.g., 'math', 'physics'). "
        "When set, only searches within the specified subject.",
    )
    max_results: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of results to return.",
    )
    cross_subject: bool = Field(
        False,
        description="When True, expand search to related subjects via tag similarity.",
    )
    fusion_strategy: Optional[Literal["rrf", "weighted", "cascade"]] = Field(
        None,
        description="Override fusion strategy. Default: auto-selected based on query.",
    )


class NoteResultItem(BaseModel):
    """A single note search result."""

    content: str = Field(..., description="Matching note content segment.")
    file_path: str = Field(default="", description="Source file path.")
    relevance_score: float = Field(default=0.0, description="Relevance score (0-1).")
    source: str = Field(
        default="unknown", description="Retrieval source (e.g., 'lancedb', 'graphiti')."
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NoteSearchOutput(BaseModel):
    """Output from the search_notes MCP tool."""

    query: str = Field(..., description="Original search query.")
    results: List[NoteResultItem] = Field(default_factory=list)
    total_count: int = Field(default=0, description="Number of results returned.")
    quality_grade: str = Field(
        default="unknown",
        description="Quality assessment: high / medium / low.",
    )
    status: str = Field(default="ok", description="ok or error.")
    message: str = Field(default="", description="Error message if status=error.")


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Implementation
# ═══════════════════════════════════════════════════════════════════════════════


async def search_notes(
    query: str,
    canvas_file: Optional[str] = None,
    subject_id: Optional[str] = None,
    max_results: int = 10,
    cross_subject: bool = False,
    fusion_strategy: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search user's Vault notes using the full RAG pipeline.

    Executes the 6-source parallel retrieval pipeline via RAGService.query(),
    including semantic search (BGE-M3), knowledge graph (Graphiti),
    and multimodal sources. Results are fused
    and reranked for optimal relevance.

    Args:
        query: Natural language search query.
        canvas_file: Optional canvas file for scoping.
        subject_id: Optional subject for isolation.
        max_results: Maximum results to return.
        cross_subject: Whether to expand to related subjects.
        fusion_strategy: Override fusion strategy.

    Returns:
        Dict with results, quality_grade, status.
    """
    try:
        from app.services.rag_service import get_rag_service

        rag_service = get_rag_service()

        # Execute full RAG pipeline
        rag_result = await rag_service.query(
            query=query,
            canvas_file=canvas_file,
            subject_id=subject_id,
            cross_subject=cross_subject,
            fusion_strategy=fusion_strategy,
        )

        # Extract and format results
        raw_results = rag_result.get("reranked_results", [])
        if not raw_results:
            raw_results = rag_result.get("results", [])

        # RAG-P0 v2 fallback (2026-05-11): LangGraph 5-channel fusion pipeline
        # has a known `fan_out_retrieval` conditional_edges routing bug causing
        # all 5 channels to silently skip execution (Channel health: 0/5 active).
        # When the pipeline returns 0, fall back to direct LanceDBClient.search()
        # single-path query so Claudian skill never gets empty supplementary.
        # Long-term fix: state_graph.py fan_out_retrieval path_map (P1, deferred).
        if not raw_results:
            # RAG-P0 v2 fallback (2026-05-11): RAGService.query() returned 0 due to
            # known LangGraph fan_out_retrieval routing bug + LanceDBClient.search
            # hybrid path also returns 0 silently. Bypass BOTH layers — go raw
            # LanceDB API. Proven path: tbl.search(vector).where(filter).limit(N).
            try:
                import os
                from agentic_rag.clients import LanceDBClient
                from agentic_rag.config import LANCEDB_CONFIG

                # LANCEDB_CONFIG['db_path'] defaults to 'data/lancedb' (relative!)
                # but actual data is at env LANCEDB_DATA_PATH (=/lancedb in container).
                # Prefer env over config to avoid cwd-dependent empty connection.
                resolved_db_path = os.environ.get(
                    "LANCEDB_DATA_PATH", LANCEDB_CONFIG["db_path"]
                )
                logger.warning(
                    f"[search_notes] RAG pipeline returned 0; bypassing to raw LanceDB "
                    f"API (db_path={resolved_db_path})"
                )

                # Need bge-m3 query vector + already-connected db
                helper_client = LanceDBClient(db_path=resolved_db_path)
                await helper_client.initialize()
                query_vector = await helper_client._get_query_vector(query)
                if not query_vector:
                    logger.error(
                        "[search_notes] fallback failed: bge-m3 embedding returned None"
                    )
                else:
                    # Use helper_client._db (already-connected) instead of new
                    # lancedb.connect() to avoid path resolution mismatch
                    db = helper_client._db
                    if db is None:
                        raise RuntimeError(
                            "helper_client._db is None after initialize()"
                        )
                    # vault_id-prefixed table name
                    table_name = helper_client.resolve_table_name("vault_notes")
                    logger.debug(
                        f"[search_notes] fallback opening table '{table_name}' "
                        f"(available: {list(db.table_names())[:5]})"
                    )
                    tbl = db.open_table(table_name)
                    # Filter out whiteboard, fallback to IS NULL for pre-A1 rows
                    where_clause = (
                        "(doc_type NOT IN ('whiteboard') OR doc_type IS NULL)"
                    )
                    raw_df = (
                        tbl.search(query_vector)
                        .where(where_clause)
                        .limit(max_results)
                        .to_pandas()
                    )
                    raw_results = [
                        {
                            "content": row.get("content", ""),
                            "file_path": row.get("canvas_file", ""),
                            "score": 1.0 - float(row.get("_distance", 0.0))
                            if "_distance" in row
                            else 0.0,
                            "retrieval_source": "lancedb_raw_fallback",
                            "metadata": {
                                "doc_type": row.get("doc_type", ""),
                                "subject": row.get("subject", ""),
                                "category": row.get("category", ""),
                            },
                        }
                        for _, row in raw_df.iterrows()
                    ]
                    logger.info(
                        f"[search_notes] raw LanceDB fallback returned "
                        f"{len(raw_results)} results from {table_name}"
                    )
            except Exception as fb_exc:
                logger.error(
                    f"[search_notes] raw LanceDB fallback failed: {fb_exc}",
                    exc_info=True,
                )

        items: List[NoteResultItem] = []
        for r in raw_results[:max_results]:
            content = r.get("content", r.get("text", ""))
            file_path = r.get("file_path", r.get("path", r.get("source", "")))
            score = r.get("score", r.get("relevance_score", 0.0))
            source = r.get("source_type", r.get("retrieval_source", "unknown"))

            items.append(
                NoteResultItem(
                    content=content,
                    file_path=str(file_path),
                    relevance_score=float(score) if score else 0.0,
                    source=str(source),
                    metadata={
                        k: v
                        for k, v in r.items()
                        if k
                        not in (
                            "content",
                            "text",
                            "file_path",
                            "path",
                            "score",
                            "relevance_score",
                            "source_type",
                            "retrieval_source",
                        )
                    },
                )
            )

        quality = rag_result.get("quality_grade", "unknown")

        logger.info(
            f"[F2] search_notes: query='{query[:50]}' results={len(items)} quality={quality}"
        )

        return NoteSearchOutput(
            query=query,
            results=items,
            total_count=len(items),
            quality_grade=str(quality),
            status="ok",
        ).model_dump()

    except Exception as e:
        logger.error(f"[F2] search_notes failed: {e}")
        return NoteSearchOutput(
            query=query,
            status="error",
            message=str(e),
        ).model_dump()
