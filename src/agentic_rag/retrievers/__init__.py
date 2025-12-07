"""
Retriever模块 for Canvas Agentic RAG (Story 6.8)

提供多模态检索功能:
- MultimodalRetriever: 多模态内容检索器
- MultimodalResult: 多模态检索结果

Dependencies:
- Story 6.6 (MultimodalVectorizer)
- Story 6.7 (AssociationEngine)
"""

from .multimodal_retriever import (
    MultimodalResult,
    MultimodalRetrievalTimeout,
    MultimodalRetriever,
    MultimodalRetrieverError,
    multimodal_retrieval_node,  # Story 6.8: LangGraph节点
    retrieve_multimodal,
)

__all__ = [
    "MultimodalRetriever",
    "MultimodalResult",
    "MultimodalRetrieverError",
    "MultimodalRetrievalTimeout",
    "retrieve_multimodal",
    "multimodal_retrieval_node",  # Story 6.8: LangGraph节点
]
