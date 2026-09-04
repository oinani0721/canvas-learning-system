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
# RAG-S2 T5 (2026-08-10 链统一): the fast path now goes through the SHARED
# post-processing chain (search_supplementary) — hybrid FTS+RRF, weighted
# ordering, taint scan, empty-doc detection, source-file dedup, CE delivery
# gate, retrieval_confidence. MCP search and hook injection are the same chain.
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

from app.services.supplementary_search_service import search_supplementary

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
    # RAG-S2 T5 (2026-08-10): ⛔ server.py 以 response_model=NoteSearchOutput
    # 注册 — 顶层新字段必须在此声明, 否则被 FastAPI 序列化裁掉。
    retrieval_confidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Query-level retrieval confidence from the shared "
        "post-processing chain (RAG-S2 T5): {level: high|medium|low|none, "
        "signals: {...}}. 'none' = empty/degraded delivery. None (absent) = "
        "results came from the extended LangGraph pipeline (no confidence "
        "computed).",
    )


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
            # T5 审查 HIGH-1: enable_fallback=False — LanceDBClient.search()
            # 默认把超时/任何异常吞成 [] (基础设施故障 → 假 ok_empty)。本
            # client 是 MCP 专属 (不与索引端点共享), 关掉吞噬让异常沿
            # _vault_scoped_search → search_supplementary(search_failed, degraded)
            # → _fast_path_search raise → source_status="error" 诚实上报。
            client = LanceDBClient(db_path=resolved_db_path, enable_fallback=False)
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


async def _fast_path_search(query: str, max_results: int) -> Dict[str, Any]:
    """
    Fast path via the shared post-processing chain (RAG-S2 T5 链统一).

    History: RAG-P0 v2 (2026-05-11) 起这里是纯 vector 直查 (tbl.search().where()
    .limit()), 绕过 LanceDBClient.search() — 意味着 MCP 检索享受不到 hook 链
    T2-T4 的全部改进 (hybrid FTS+RRF / source_priority 加权序 / taint 扫描 /
    空文档检测 / 源文件级 dedup / CE 交付门), score 量纲都不同 (1-distance vs
    加权分)。T5 起两条链同源: 统一走 search_supplementary (生产交付参数
    min_relevance=0.50, 与 hook 链一致), score 量纲 = 加权分。

    Raises on infrastructure failure (embedding service down / LanceDB 不可用 /
    超时) so the caller reports source_status="error" instead of a fake empty ok
    — search_supplementary 把基础设施故障吞成 degraded+空, 这里还原为异常。
    """
    helper_client = await _get_fast_client()
    # T5 审查 HIGH-1: embedding 预检 — LanceDBClient.search() 内部把
    # embedding=None 吞成空结果 (连 enable_fallback=False 都拦不住, 它不是
    # 异常路径), 共享链会把它判成 empty_index。恢复旧 fast path 的显式
    # 预检: embedding 服务挂 = 基础设施故障, 必须报 error 而非 ok_empty
    # (阶段 0 契约 3)。代价是每次 MCP 查询多一次 query 向量化 (~几十 ms)。
    query_vector = await helper_client._get_query_vector(query)
    if not query_vector:
        raise RuntimeError("bge-m3 embedding returned None (embedding service unavailable)")
    supp_result = await search_supplementary(
        query=query,
        lancedb_client=helper_client,
        top_k_max=max_results,
        min_relevance=0.50,
        elbow_drop_threshold=0.25,
        hard_cap=max_results,
        include_content=True,
    )
    if supp_result.get("degraded") and not supp_result.get("materials"):
        raise RuntimeError(f"supplementary search degraded: {supp_result.get('reason')}")
    logger.info(
        "[search_notes] fast path (shared chain) returned %s materials",
        len(supp_result.get("materials", [])),
    )
    return supp_result


def _material_to_item(m: Dict[str, Any]) -> NoteResultItem:
    """search_supplementary material → NoteResultItem (RAG-S2 T5).

    taint 防护与 hook 链 XML 面同口径 (format_supplementary_xml): review /
    quarantine 时正文与 title/wikilink/source_path 一律 placeholder — 否则
    MCP 面成为 prompt injection 的绕行通道。ce_score/raw_score 等内部量纲
    走 per-result metadata 搭车 (MCP 是工具面不是 prompt 面, 无 XML 契约)。
    """
    taint = m.get("taint", "clean")
    injection_risk = float(m.get("injection_risk", 0.0) or 0.0)
    if taint == "quarantine":
        content = (
            "[QUARANTINED — content blocked due to suspected prompt injection. "
            "Use Read tool on source_path to verify if needed.]"
        )
        title = f"[QUARANTINED: tainted title (risk={injection_risk:.2f})]"
        wikilink = "[QUARANTINED]"
        file_path = "[QUARANTINED]"
    elif taint == "review":
        content = f"[REDACTED: suspicious content (risk={injection_risk:.2f}); open source_path manually to verify]"
        title = f"[REDACTED: tainted title (risk={injection_risk:.2f})]"
        wikilink = "[REDACTED]"
        file_path = "[REDACTED]"
    else:
        content = str(m.get("content") or m.get("snippet") or "")
        title = str(m.get("title", ""))
        wikilink = str(m.get("wikilink", ""))
        file_path = str(m.get("source_path", ""))

    # T5 审查 MEDIUM-3: 非 clean 材料的 metadata 只保留数值/布尔信号 —
    # doc_type/source_type 来自 frontmatter 自由文本 (仅 lower/strip 无枚举
    # 校验), 攻击者可把 payload 埋 `type:` 字段, 遮蔽只盖 content/title/
    # wikilink/file_path 时 metadata 成漏网面。
    if taint != "clean":
        signal_keys = (
            "raw_score",
            "fts_confirmed",
            "ce_score",
            "injection_risk",
            "is_link_list_chunk",
        )
    else:
        signal_keys = (
            "raw_score",
            "doc_type",
            "fts_confirmed",
            "ce_score",
            "injection_risk",
            "source_type",
            "is_link_list_chunk",
        )
    metadata: Dict[str, Any] = {k: m[k] for k in signal_keys if m.get(k) is not None}
    metadata["taint"] = taint
    metadata["title"] = title
    metadata["wikilink"] = wikilink

    return NoteResultItem(
        content=content,
        file_path=file_path,
        relevance_score=float(m.get("score") or 0.0),
        source="lancedb_fast",
        metadata=metadata,
    )


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
        items: List[NoteResultItem] = []
        confidence: Optional[Dict[str, Any]] = None

        if extended_mode:
            # Stage-4 shadow evaluation only — retired from the default chain
            # (RAG-S0-2026-08-02). Known-dead as of retirement: 0/5 channels.
            from app.services.rag_service import get_rag_service

            rag_service = get_rag_service()
            raw_results: List[Dict[str, Any]] = []
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

            if raw_results:
                items = [_legacy_row_to_item(r) for r in raw_results[:max_results]]
            else:
                logger.warning("[search_notes] extended pipeline returned 0; falling back to shared fast path")
                # Declare BEFORE the await: if the fast path itself fails
                # here, the error must be attributed to "fallback", not to
                # the pipeline — stage-4 shadow evaluation depends on this.
                execution_mode = "fallback"
                supp_result = await _fast_path_search(query, max_results)
                items = [_material_to_item(m) for m in supp_result.get("materials", [])]
                confidence = supp_result.get("confidence")
        else:
            supp_result = await _fast_path_search(query, max_results)
            items = [_material_to_item(m) for m in supp_result.get("materials", [])]
            confidence = supp_result.get("confidence")

        source_status = "ok_nonempty" if items else "ok_empty"

        logger.info(
            f"[F2] search_notes: query='{query[:50]}' results={len(items)} "
            f"mode={execution_mode} source_status={source_status} "
            f"confidence={(confidence or {}).get('level')}"
        )

        return NoteSearchOutput(
            query=query,
            results=items,
            total_count=len(items),
            execution_mode=execution_mode,
            source_status=source_status,
            status="ok",
            retrieval_confidence=confidence,
        ).model_dump()

    except Exception as e:
        logger.error(f"[F2] search_notes failed: {e}", exc_info=True)
        return NoteSearchOutput(
            query=query,
            execution_mode=execution_mode,
            source_status="error",
            status="error",
            message=str(e),
            # T5: 基础设施故障也给诚实档位 — Claude 不必解析 message 才知道
            # 这不是"真没有相关材料"。
            retrieval_confidence={
                "level": "none",
                "signals": {"degraded_reason": str(e)[:160]},
            },
        ).model_dump()


def _legacy_row_to_item(r: Dict[str, Any]) -> NoteResultItem:
    """Extended (LangGraph) pipeline row → NoteResultItem — 原 search_notes
    归一化循环原样抽出 (行为不变), 仅供 extended 分支消费。"""
    content = r.get("content", r.get("text", ""))
    file_path = r.get("file_path", r.get("path", r.get("source", "")))
    score = r.get("score", r.get("relevance_score", 0.0))
    source = r.get("source_type", r.get("retrieval_source", "unknown"))

    return NoteResultItem(
        content=content,
        file_path=str(file_path),
        relevance_score=float(score) if score else 0.0,
        source=str(source),
        # Merge a row's own "metadata" dict with remaining extra
        # keys — without this rows nest as metadata={"metadata": {...}}.
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
