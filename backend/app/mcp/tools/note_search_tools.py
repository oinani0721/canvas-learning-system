# Canvas Learning System - MCP Note Search Tool
# F2: Expose RAG retrieval pipeline as MCP tool for Agent SDK
#
# Enables Claude to autonomously search the user's Vault notes during
# conversation, supporting MVP #10 (笔记精准检索返回) and the core system
# requirement "笔记片段精准检索系统".
#
# Uses the full RAG pipeline (6-source parallel retrieval + fusion + reranking)
# via RAGService.query(), which includes:
#   - LanceDB + BGE-M3 semantic search (vault_notes)
#   - Graphiti knowledge graph search
#   - Multimodal retrieval (images/PDFs)
#   - Cross-canvas retrieval
#   - Textbook retrieval
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
    relevance_score: float = Field(
        default=0.0, description="Relevance score (0-1)."
    )
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
    multimodal, textbook, and cross-canvas sources. Results are fused
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
                        if k not in ("content", "text", "file_path", "path", "score", "relevance_score", "source_type", "retrieval_source")
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
