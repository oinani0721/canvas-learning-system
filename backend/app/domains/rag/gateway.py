"""
RAG Domain Gateway — 检索增强统一入口

Strangler Fig Pattern: 所有外部调用应通过此 gateway 访问 rag 领域。

包含: rag_service, lancedb_index_service, subject_resolver,
       cross_subject_bridge, multimodal_service
"""

from __future__ import annotations

# ── Agentic RAG 编排 ──
from app.services.rag_service import (
    RAGService,
    get_rag_service,
    LANGGRAPH_AVAILABLE,
)

# ── LanceDB 索引服务 ──
from app.services.lancedb_index_service import get_lancedb_index_service

# ── 学科解析 ──
from app.services.subject_resolver import SubjectResolver, get_subject_resolver

# ── 跨学科桥接 ──
from app.services.cross_subject_bridge import compute_tag_jaccard

# ── 多模态内容管理 ──
from app.services.multimodal_service import MultimodalService

__all__ = [
    "RAGService",
    "get_rag_service",
    "LANGGRAPH_AVAILABLE",
    "get_lancedb_index_service",
    "SubjectResolver",
    "get_subject_resolver",
    "compute_tag_jaccard",
    "MultimodalService",
]
