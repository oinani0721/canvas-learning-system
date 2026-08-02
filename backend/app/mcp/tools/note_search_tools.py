# Canvas Learning System - MCP Note Search Tool
# F2: Expose RAG retrieval pipeline as MCP tool for Agent SDK
#
# Enables Claude to autonomously search the user's Vault notes during
# conversation, supporting MVP #10 (笔记精准检索返回) and the core system
# requirement "笔记片段精准检索系统".
#
# RAG-S0-2026-08-02 (阶段 0 止血): the raw LanceDB hybrid search — formerly the
# RAG-P0 v2 emergency fallback — is now the DEFAULT execution path ("fast").
# The LangGraph multi-source pipeline (0/5 channels alive since 2026-05-11) is
# retired from the default chain and kept behind the RAG_EXTENDED_MODE env var
# strictly for stage-4 shadow evaluation. Do NOT delete the extended branch.
#
# [Source: S18-8 F2 decision — MCP note_search tool, fastapi_mcp expose RAG API]
# [Source: MVP #10 — 笔记精准检索返回]
# [Source: RAG-S0-2026-08-02 — 阶段 0 止血: fast path 转正 + 废 quality 假信号]

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Add backend/lib to sys.path for agentic_rag imports (same idiom as
# rag_service.py / mastery_engine.py). The fast path no longer imports
# rag_service, so this module can't rely on rag_service having done it.
_backend_root = Path(__file__).parent.parent.parent.parent  # app/mcp/tools/ -> backend/
_lib_path = str(_backend_root / "lib")
if _lib_path not in sys.path:
    sys.path.insert(0, _lib_path)

# Env gate for the retired LangGraph pipeline (stage-4 shadow evaluation only).
_EXTENDED_MODE_ENV = "RAG_EXTENDED_MODE"
_TRUTHY = ("1", "true", "yes", "on")


def _extended_mode_enabled() -> bool:
    """Whether the retired LangGraph pipeline is explicitly re-enabled."""
    return os.environ.get(_EXTENDED_MODE_ENV, "").strip().lower() in _TRUTHY


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
        description="Canvas file path to scope search. Extended mode only "
        "(RAG_EXTENDED_MODE); ignored on the default fast path.",
    )
    subject_id: Optional[str] = Field(
        None,
        description="Subject ID for multi-subject scope isolation (e.g., 'math', 'physics'). "
        "Extended mode only (RAG_EXTENDED_MODE); ignored on the default fast path.",
    )
    max_results: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of results to return.",
    )
    cross_subject: bool = Field(
        False,
        description="When True, expand search to related subjects via tag similarity. "
        "Extended mode only (RAG_EXTENDED_MODE); ignored on the default fast path.",
    )
    fusion_strategy: Optional[Literal["rrf", "weighted", "cascade"]] = Field(
        None,
        description="Override fusion strategy. Only applies in extended mode "
        "(RAG_EXTENDED_MODE); the default fast path is single-source.",
    )


class NoteResultItem(BaseModel):
    """A single note search result."""

    content: str = Field(..., description="Matching note content segment.")
    file_path: str = Field(default="", description="Source file path.")
    relevance_score: float = Field(default=0.0, description="Relevance score (0-1).")
    source: str = Field(default="unknown", description="Retrieval source (e.g., 'lancedb', 'graphiti').")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NoteSearchOutput(BaseModel):
    """Output from the search_notes MCP tool.

    RAG-S0-2026-08-02: quality_grade removed — it was computed by the dead
    LangGraph pipeline over its own empty results (permanently "low") and
    carried no information. Honest status is now split into execution_mode
    (which path ran) + source_status (what the delivered results actually are).
    """

    query: str = Field(..., description="Original search query.")
    results: List[NoteResultItem] = Field(default_factory=list)
    total_count: int = Field(default=0, description="Number of results returned.")
    execution_mode: Literal["fast", "extended", "fallback"] = Field(
        default="fast",
        description="Which retrieval path produced the results: "
        "'fast' = raw LanceDB hybrid (default); "
        "'extended' = LangGraph pipeline (RAG_EXTENDED_MODE, stage-4 shadow only); "
        "'fallback' = extended pipeline returned empty or failed, raw LanceDB "
        "delivery was attempted.",
    )
    source_status: Literal["ok_nonempty", "ok_empty", "error"] = Field(
        default="ok_empty",
        description="Status of the actually delivered results: "
        "'ok_nonempty' = search succeeded with results; "
        "'ok_empty' = search succeeded, genuinely no matches; "
        "'error' = retrieval infrastructure failed (NOT the same as no matches).",
    )
    status: str = Field(default="ok", description="ok or error.")
    message: str = Field(default="", description="Error message if status=error.")


# ═══════════════════════════════════════════════════════════════════════════════
# Fast Path: raw LanceDB search (default since RAG-S0-2026-08-02)
# ═══════════════════════════════════════════════════════════════════════════════


# Process-lifetime client singleton: LanceDBClient.initialize() loads the
# bge-m3 weights in-process (~7.4s measured in-container). Re-initializing per
# request was the hidden fixed cost of the old fallback path. The vault is
# deployment-fixed (P0-3: switching = edit .env + compose up = new process),
# so caching the client for the process lifetime is safe. The table handle is
# NOT cached — open_table() per request keeps freshly indexed rows visible.
_fast_client: Optional[Any] = None
# Lock is created lazily inside the running loop: a module-level Lock binds to
# the first loop that awaits it and breaks under per-test event loops.
_fast_client_lock: Optional[asyncio.Lock] = None


async def _get_fast_client() -> Any:
    """Return the shared initialized LanceDBClient (lazy, one per process).

    A failed init is NOT cached: LanceDBClient.initialize() reports failure by
    returning False (it never raises), so the result must be checked here —
    otherwise a broken client (_db=None) would poison every later request
    until process restart. On failure the next request retries from scratch.
    """
    global _fast_client, _fast_client_lock
    if _fast_client is not None:
        return _fast_client
    if _fast_client_lock is None:
        # No await between check and assignment — atomic under asyncio.
        _fast_client_lock = asyncio.Lock()
    async with _fast_client_lock:
        if _fast_client is None:
            from agentic_rag.clients import LanceDBClient
            from agentic_rag.config import LANCEDB_CONFIG

            # Canonical path resolution lives in agentic_rag.config
            # (LANCEDB_DATA_PATH first, legacy LANCEDB_PATH fallback,
            # conflict -> RuntimeError). Single source of truth — do not
            # re-derive from os.environ here.
            resolved_db_path = LANCEDB_CONFIG["db_path"]
            client = LanceDBClient(db_path=resolved_db_path)
            ok = await client.initialize()  # loads embedding weights — once
            if not ok or client._db is None:
                raise RuntimeError(
                    f"LanceDBClient.initialize() failed (db_path="
                    f"{resolved_db_path}); client not cached — next request "
                    "will retry initialization"
                )
            _fast_client = client
            logger.info(f"[search_notes] fast-path LanceDBClient initialized (db_path={resolved_db_path})")
    return _fast_client


async def _raw_lancedb_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Direct LanceDB vector search over vault_notes — the fast path.

    Proven path since RAG-P0 v2 (2026-05-11): tbl.search(vector).where(filter)
    .limit(N). Bypasses both RAGService and LanceDBClient.search() wrappers.

    Raises on infrastructure failure (embedding service down, table missing)
    so the caller reports source_status="error" instead of a fake empty ok.
    """
    helper_client = await _get_fast_client()
    query_vector = await helper_client._get_query_vector(query)
    if not query_vector:
        raise RuntimeError("bge-m3 embedding returned None (embedding service unavailable)")

    # Use helper_client._db (already-connected) instead of a fresh
    # lancedb.connect() to avoid path resolution mismatch.
    db = helper_client._db
    if db is None:
        raise RuntimeError("helper_client._db is None after initialize()")

    # vault_id-prefixed table name
    table_name = helper_client.resolve_table_name("vault_notes")
    if logger.isEnabledFor(logging.DEBUG):
        # table_names() scans the DB dir — keep it off the hot path
        logger.debug(
            "[search_notes] fast path opening table '%s' (available: %s)",
            table_name,
            list(db.table_names())[:5],
        )
    tbl = db.open_table(table_name)
    # Filter out whiteboard, fallback to IS NULL for pre-A1 rows
    where_clause = "(doc_type NOT IN ('whiteboard') OR doc_type IS NULL)"
    raw_df = tbl.search(query_vector).where(where_clause).limit(max_results).to_pandas()
    results = [
        {
            "content": row.get("content", ""),
            "file_path": row.get("canvas_file", ""),
            "score": 1.0 - float(row.get("_distance", 0.0)) if "_distance" in row else 0.0,
            "retrieval_source": "lancedb_fast",
            "metadata": {
                "doc_type": row.get("doc_type", ""),
                "subject": row.get("subject", ""),
                "category": row.get("category", ""),
            },
        }
        for _, row in raw_df.iterrows()
    ]
    logger.info(f"[search_notes] fast path returned {len(results)} results from {table_name}")
    return results


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
    Search user's Vault notes.

    Default ("fast"): direct LanceDB + BGE-M3 vector search over vault_notes.
    This is the path that has actually served every result since 2026-05-11.

    Extended (RAG_EXTENDED_MODE env, stage-4 shadow evaluation only): the full
    LangGraph multi-source pipeline. If it returns empty, the fast path still
    delivers and execution_mode is reported as "fallback".

    Args:
        query: Natural language search query.
        canvas_file: Optional canvas file for scoping (extended mode only).
        subject_id: Optional subject for isolation (extended mode only).
        max_results: Maximum results to return.
        cross_subject: Whether to expand to related subjects (extended mode only).
        fusion_strategy: Override fusion strategy (extended mode only).

    Returns:
        Dict with results, execution_mode, source_status, status.
    """
    extended_mode = _extended_mode_enabled()
    execution_mode = "extended" if extended_mode else "fast"
    try:
        raw_results: List[Dict[str, Any]] = []

        if extended_mode:
            # Stage-4 shadow evaluation only — retired from the default chain
            # (RAG-S0-2026-08-02). Known-dead as of retirement: 0/5 channels.
            from app.services.rag_service import get_rag_service

            rag_service = get_rag_service()
            try:
                rag_result = await rag_service.query(
                    query=query,
                    canvas_file=canvas_file,
                    subject_id=subject_id,
                    cross_subject=cross_subject,
                    fusion_strategy=fusion_strategy,
                )
                raw_results = rag_result.get("reranked_results") or rag_result.get("results") or []
            except Exception as pipeline_exc:
                logger.error(
                    f"[search_notes] extended pipeline failed: {pipeline_exc}",
                    exc_info=True,
                )
                raw_results = []

            if not raw_results:
                logger.warning("[search_notes] extended pipeline returned 0; falling back to raw LanceDB fast path")
                # Declare BEFORE the await: if the fast path itself fails
                # here, the error must be attributed to "fallback", not to
                # the pipeline — stage-4 shadow evaluation depends on this.
                execution_mode = "fallback"
                raw_results = await _raw_lancedb_search(query, max_results)
        else:
            raw_results = await _raw_lancedb_search(query, max_results)

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
                    # Merge a row's own "metadata" dict with remaining extra
                    # keys — without this the fast-path rows nest as
                    # metadata={"metadata": {...}}.
                    metadata={
                        **(r["metadata"] if isinstance(r.get("metadata"), dict) else {}),
                        **{
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
                                "metadata",
                            )
                        },
                    },
                )
            )

        source_status = "ok_nonempty" if items else "ok_empty"

        logger.info(
            f"[F2] search_notes: query='{query[:50]}' results={len(items)} "
            f"mode={execution_mode} source_status={source_status}"
        )

        return NoteSearchOutput(
            query=query,
            results=items,
            total_count=len(items),
            execution_mode=execution_mode,
            source_status=source_status,
            status="ok",
        ).model_dump()

    except Exception as e:
        logger.error(f"[F2] search_notes failed: {e}", exc_info=True)
        return NoteSearchOutput(
            query=query,
            execution_mode=execution_mode,
            source_status="error",
            status="error",
            message=str(e),
        ).model_dump()
