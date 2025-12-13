"""
Retriever模块 for Canvas Agentic RAG (Story 6.8, Story 23.4)

提供多模态和多源检索功能:
- MultimodalRetriever: 多模态内容检索器 (Story 6.8)
- TextbookContextService: 教材上下文检索器 (Story 23.4)
- CrossCanvasService: 跨Canvas关联检索器 (Story 23.4)

Dependencies:
- Story 6.6 (MultimodalVectorizer)
- Story 6.7 (AssociationEngine)
- LanceDBClient: 向量检索
"""

# Story 23.4: 跨Canvas关联检索
from .cross_canvas_retriever import (
    CrossCanvasRetrievalTimeout,
    CrossCanvasRetrieverConfig,
    CrossCanvasRetrieverError,
    CrossCanvasService,
    cross_canvas_retrieval_node,
)
from .multimodal_retriever import (
    MultimodalResult,
    MultimodalRetrievalTimeout,
    MultimodalRetriever,
    MultimodalRetrieverError,
    multimodal_retrieval_node,  # Story 6.8: LangGraph节点
    retrieve_multimodal,
)

# Story 23.4: 教材上下文检索
from .textbook_retriever import (
    TextbookContextService,
    TextbookRetrievalTimeout,
    TextbookRetrieverConfig,
    TextbookRetrieverError,
    textbook_retrieval_node,
)

__all__ = [
    # Story 6.8: 多模态检索
    "MultimodalRetriever",
    "MultimodalResult",
    "MultimodalRetrieverError",
    "MultimodalRetrievalTimeout",
    "retrieve_multimodal",
    "multimodal_retrieval_node",
    # Story 23.4: 教材上下文检索
    "TextbookContextService",
    "TextbookRetrieverConfig",
    "TextbookRetrieverError",
    "TextbookRetrievalTimeout",
    "textbook_retrieval_node",
    # Story 23.4: 跨Canvas关联检索
    "CrossCanvasService",
    "CrossCanvasRetrieverConfig",
    "CrossCanvasRetrieverError",
    "CrossCanvasRetrievalTimeout",
    "cross_canvas_retrieval_node",
]
