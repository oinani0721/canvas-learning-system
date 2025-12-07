"""
多模态检索器 for Canvas Agentic RAG (Story 6.8)

提供多模态内容检索功能，集成到Agentic RAG流程中:
- AC 6.8.1: 扩展检索节点支持多模态
- AC 6.8.2: 多模态结果融合 (通过rrf_fusion扩展)
- AC 6.8.3: 结果格式化 (缩略图URL, 页码, 章节)
- AC 6.8.4: 检索延迟<2秒

Dependencies:
- Story 6.6 (MultimodalVectorizer) - 向量化
- Story 6.7 (AssociationEngine) - 关联关系

✅ Verified from LangGraph Skill:
- Pattern: Async retrieval nodes
- Pattern: Send for parallel execution

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-04
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, TypedDict

# ============================================================
# Exceptions
# ============================================================

class MultimodalRetrieverError(Exception):
    """Base exception for MultimodalRetriever errors."""
    pass


class MultimodalRetrievalTimeout(MultimodalRetrieverError):
    """Raised when retrieval times out."""
    pass


class VectorizationError(MultimodalRetrieverError):
    """Raised when query vectorization fails."""
    pass


class SearchError(MultimodalRetrieverError):
    """Raised when vector search fails."""
    pass


# ============================================================
# Data Types
# ============================================================

class MediaType(str, Enum):
    """多模态内容类型"""
    IMAGE = "image"
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"


@dataclass
class MultimodalResult:
    """
    多模态检索结果

    AC 6.8.3: 结果格式化
    - 图片结果包含缩略图URL
    - PDF结果包含页码和章节
    - 支持预览链接

    Attributes:
        id: 唯一标识符
        media_type: 媒体类型 (image, pdf, audio, video)
        file_path: 文件路径
        content_preview: 内容预览 (缩略图URL或文本摘要)
        source_location: 来源位置 (页码/时间戳)
        relevance_score: 相关度分数 (0-1)
        related_concepts: 相关概念列表
        metadata: 额外元数据
        retrieved_at: 检索时间戳
    """
    id: str
    media_type: MediaType
    file_path: str
    content_preview: str
    source_location: Optional[str] = None
    relevance_score: float = 0.0
    related_concepts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieved_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "id": self.id,
            "media_type": self.media_type.value if isinstance(self.media_type, MediaType) else self.media_type,
            "file_path": self.file_path,
            "content_preview": self.content_preview,
            "source_location": self.source_location,
            "relevance_score": self.relevance_score,
            "related_concepts": self.related_concepts,
            "metadata": self.metadata,
            "retrieved_at": self.retrieved_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultimodalResult":
        """Create from dictionary."""
        media_type = data.get("media_type", "unknown")
        if isinstance(media_type, str):
            try:
                media_type = MediaType(media_type)
            except ValueError:
                media_type = MediaType.UNKNOWN

        return cls(
            id=data.get("id", ""),
            media_type=media_type,
            file_path=data.get("file_path", ""),
            content_preview=data.get("content_preview", ""),
            source_location=data.get("source_location"),
            relevance_score=data.get("relevance_score", 0.0),
            related_concepts=data.get("related_concepts", []),
            metadata=data.get("metadata", {}),
            retrieved_at=data.get("retrieved_at", datetime.now().isoformat()),
        )


class MultimodalSearchResult(TypedDict):
    """LanceDB search result type hint"""
    id: str
    media_type: str
    file_path: str
    content: str
    description: str
    thumbnail_path: Optional[str]
    page_number: Optional[int]
    chapter: Optional[str]
    related_concepts: List[str]
    _distance: float


# ============================================================
# Protocol for dependency injection
# ============================================================

class LanceDBClientProtocol(Protocol):
    """Protocol for LanceDB client dependency injection."""

    async def similarity_search(
        self,
        table_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        ...


class VectorizerProtocol(Protocol):
    """Protocol for vectorizer dependency injection."""

    async def vectorize_text(self, text: str) -> List[float]:
        """Vectorize text to embedding."""
        ...


# ============================================================
# Configuration
# ============================================================

@dataclass
class MultimodalRetrieverConfig:
    """
    MultimodalRetriever配置

    Attributes:
        top_k: 返回结果数量 (默认5)
        min_score: 最小相关度阈值 (默认0.5)
        timeout_seconds: 检索超时秒数 (默认2.0, AC 6.8.4)
        enable_cache: 是否启用缓存 (默认True)
        cache_ttl_seconds: 缓存TTL (默认300秒)
        default_media_types: 默认搜索的媒体类型
        multimodal_table: LanceDB表名
    """
    top_k: int = 5
    min_score: float = 0.5
    timeout_seconds: float = 2.0
    enable_cache: bool = True
    cache_ttl_seconds: int = 300
    default_media_types: List[MediaType] = field(
        default_factory=lambda: [MediaType.IMAGE, MediaType.PDF]
    )
    multimodal_table: str = "multimodal_content"


# ============================================================
# Cache Implementation
# ============================================================

class RetrievalCache:
    """Simple in-memory cache for retrieval results."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self._cache: Dict[str, tuple[List[MultimodalResult], float]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def _make_key(self, query_vector: List[float], media_types: Optional[List[str]]) -> str:
        """Create cache key from query parameters."""
        # Use first 8 dims + length as signature
        vec_sig = str(query_vector[:8]) + str(len(query_vector))
        types_sig = str(sorted(media_types or []))
        return hashlib.md5(f"{vec_sig}:{types_sig}".encode()).hexdigest()

    def get(
        self,
        query_vector: List[float],
        media_types: Optional[List[str]] = None
    ) -> Optional[List[MultimodalResult]]:
        """Get cached results if available and not expired."""
        key = self._make_key(query_vector, media_types)
        if key in self._cache:
            results, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return results
            else:
                del self._cache[key]
        return None

    def set(
        self,
        query_vector: List[float],
        media_types: Optional[List[str]],
        results: List[MultimodalResult]
    ) -> None:
        """Cache results."""
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        key = self._make_key(query_vector, media_types)
        self._cache[key] = (results, time.time())

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Current cache size."""
        return len(self._cache)


# ============================================================
# MultimodalRetriever
# ============================================================

class MultimodalRetriever:
    """
    多模态检索器

    提供多模态内容检索功能，集成到Agentic RAG流程中。

    Features:
    - AC 6.8.1: 向量相似度搜索 (LanceDB multimodal_content表)
    - AC 6.8.3: 结果格式化 (缩略图URL, 页码, 章节)
    - AC 6.8.4: 并行检索 + 超时降级

    Usage:
        retriever = MultimodalRetriever(lancedb_client)
        results = await retriever.retrieve(query_vector)

        # With filters
        results = await retriever.retrieve(
            query_vector,
            media_types=[MediaType.IMAGE, MediaType.PDF]
        )
    """

    def __init__(
        self,
        lancedb_client: LanceDBClientProtocol,
        vectorizer: Optional[VectorizerProtocol] = None,
        config: Optional[MultimodalRetrieverConfig] = None
    ):
        """
        Initialize MultimodalRetriever.

        Args:
            lancedb_client: LanceDB client for vector search
            vectorizer: Optional vectorizer for text-to-vector conversion
            config: Configuration options
        """
        self.lancedb = lancedb_client
        self.vectorizer = vectorizer
        self.config = config or MultimodalRetrieverConfig()

        # Initialize cache if enabled
        self._cache: Optional[RetrievalCache] = None
        if self.config.enable_cache:
            self._cache = RetrievalCache(
                max_size=100,
                ttl_seconds=self.config.cache_ttl_seconds
            )

    async def retrieve(
        self,
        query_vector: List[float],
        media_types: Optional[List[MediaType]] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None
    ) -> List[MultimodalResult]:
        """
        检索多模态内容

        AC 6.8.1: 向量相似度搜索
        AC 6.8.4: 超时降级 (≤2秒)

        Args:
            query_vector: 查询向量 (768维)
            media_types: 过滤的媒体类型 (默认: image, pdf)
            top_k: 返回数量 (默认: config.top_k)
            min_score: 最小相关度 (默认: config.min_score)

        Returns:
            List[MultimodalResult]: 检索结果列表

        Raises:
            MultimodalRetrievalTimeout: 检索超时
            SearchError: 搜索失败
        """
        start_time = time.time()

        # Use defaults from config
        top_k = top_k or self.config.top_k
        min_score = min_score or self.config.min_score
        media_types = media_types or self.config.default_media_types

        # Convert MediaType enum to string list for filtering
        type_strs = [
            mt.value if isinstance(mt, MediaType) else mt
            for mt in media_types
        ]

        # Check cache first
        if self._cache:
            cached = self._cache.get(query_vector, type_strs)
            if cached is not None:
                return cached[:top_k]

        # Build filter
        search_filter = None
        if type_strs:
            search_filter = {"media_type": {"$in": type_strs}}

        try:
            # Execute search with timeout
            results = await asyncio.wait_for(
                self._execute_search(query_vector, top_k * 2, search_filter),  # Fetch extra for filtering
                timeout=self.config.timeout_seconds
            )

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            raise MultimodalRetrievalTimeout(
                f"Multimodal retrieval timed out after {elapsed:.2f}s "
                f"(limit: {self.config.timeout_seconds}s)"
            )

        except Exception as e:
            raise SearchError(f"Vector search failed: {e}") from e

        # Format results
        formatted = self._format_results(results, min_score)

        # Limit to top_k
        formatted = formatted[:top_k]

        # Cache results
        if self._cache and formatted:
            self._cache.set(query_vector, type_strs, formatted)

        return formatted

    async def retrieve_by_text(
        self,
        query_text: str,
        media_types: Optional[List[MediaType]] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None
    ) -> List[MultimodalResult]:
        """
        通过文本查询检索多模态内容

        Args:
            query_text: 查询文本
            media_types: 过滤的媒体类型
            top_k: 返回数量
            min_score: 最小相关度

        Returns:
            List[MultimodalResult]: 检索结果列表

        Raises:
            VectorizationError: 文本向量化失败
        """
        if not self.vectorizer:
            raise VectorizationError(
                "Vectorizer not configured. Pass vectorizer to constructor "
                "or use retrieve() with pre-computed vectors."
            )

        try:
            query_vector = await self.vectorizer.vectorize_text(query_text)
        except Exception as e:
            raise VectorizationError(f"Failed to vectorize query: {e}") from e

        return await self.retrieve(
            query_vector=query_vector,
            media_types=media_types,
            top_k=top_k,
            min_score=min_score
        )

    async def batch_retrieve(
        self,
        query_vectors: List[List[float]],
        media_types: Optional[List[MediaType]] = None,
        top_k: Optional[int] = None,
        max_concurrent: int = 5
    ) -> List[List[MultimodalResult]]:
        """
        批量检索多模态内容

        Args:
            query_vectors: 查询向量列表
            media_types: 过滤的媒体类型
            top_k: 每个查询返回数量
            max_concurrent: 最大并发数

        Returns:
            List[List[MultimodalResult]]: 每个查询的结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def retrieve_with_semaphore(qv: List[float]) -> List[MultimodalResult]:
            async with semaphore:
                try:
                    return await self.retrieve(
                        query_vector=qv,
                        media_types=media_types,
                        top_k=top_k
                    )
                except Exception:
                    return []

        tasks = [retrieve_with_semaphore(qv) for qv in query_vectors]
        return await asyncio.gather(*tasks)

    async def _execute_search(
        self,
        query_vector: List[float],
        top_k: int,
        filter: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute vector similarity search."""
        return await self.lancedb.similarity_search(
            table_name=self.config.multimodal_table,
            query_vector=query_vector,
            top_k=top_k,
            filter=filter
        )

    def _format_results(
        self,
        raw_results: List[Dict[str, Any]],
        min_score: float
    ) -> List[MultimodalResult]:
        """
        格式化检索结果

        AC 6.8.3: 结果格式化
        - 图片结果包含缩略图URL
        - PDF结果包含页码和章节
        """
        formatted = []

        for r in raw_results:
            # Convert distance to score (0-1, higher is better)
            distance = r.get("_distance", r.get("distance", 1.0))
            score = self._distance_to_score(distance)

            # Filter by min_score
            if score < min_score:
                continue

            # Determine media type
            media_type_str = r.get("media_type", "unknown")
            try:
                media_type = MediaType(media_type_str)
            except ValueError:
                media_type = MediaType.UNKNOWN

            # Get preview based on media type
            content_preview = self._get_preview(r, media_type)

            # Get source location based on media type
            source_location = self._get_source_location(r, media_type)

            result = MultimodalResult(
                id=r.get("id", r.get("doc_id", "")),
                media_type=media_type,
                file_path=r.get("file_path", ""),
                content_preview=content_preview,
                source_location=source_location,
                relevance_score=score,
                related_concepts=r.get("related_concepts", []),
                metadata={
                    k: v for k, v in r.items()
                    if k not in {
                        "id", "doc_id", "media_type", "file_path",
                        "_distance", "distance", "related_concepts",
                        "content", "description", "thumbnail_path",
                        "page_number", "chapter"
                    }
                }
            )

            formatted.append(result)

        # Sort by score descending
        formatted.sort(key=lambda x: x.relevance_score, reverse=True)

        return formatted

    def _distance_to_score(self, distance: float) -> float:
        """
        Convert vector distance to relevance score (0-1).

        Uses: score = 1 / (1 + distance)
        - distance=0 → score=1.0
        - distance=1 → score=0.5
        - distance→∞ → score→0
        """
        if distance < 0:
            distance = 0
        return 1.0 / (1.0 + distance)

    def _get_preview(self, result: Dict[str, Any], media_type: MediaType) -> str:
        """
        获取内容预览

        AC 6.8.3:
        - 图片: 缩略图URL
        - PDF: 章节标题 + 描述摘要
        - 其他: 描述文本
        """
        if media_type == MediaType.IMAGE:
            # Return thumbnail path for images
            thumbnail = result.get("thumbnail_path", "")
            if thumbnail:
                return thumbnail
            # Fallback to description
            return result.get("description", "")[:200]

        elif media_type == MediaType.PDF:
            # Combine chapter and description for PDF
            chapter = result.get("chapter", "")
            description = result.get("description", result.get("content", ""))[:200]
            if chapter:
                return f"[{chapter}] {description}"
            return description

        else:
            # Default: description or content
            return result.get("description", result.get("content", ""))[:200]

    def _get_source_location(
        self,
        result: Dict[str, Any],
        media_type: MediaType
    ) -> Optional[str]:
        """
        获取来源位置

        AC 6.8.3:
        - PDF: 页码 (e.g., "Page 15")
        - Audio/Video: 时间戳 (e.g., "00:05:30")
        - Image: None
        """
        if media_type == MediaType.PDF:
            page = result.get("page_number")
            if page is not None:
                return f"Page {page}"
            return None

        elif media_type in (MediaType.AUDIO, MediaType.VIDEO):
            timestamp = result.get("timestamp")
            if timestamp is not None:
                # Format seconds to HH:MM:SS
                mins, secs = divmod(int(timestamp), 60)
                hours, mins = divmod(mins, 60)
                return f"{hours:02d}:{mins:02d}:{secs:02d}"
            return None

        return None

    def clear_cache(self) -> None:
        """Clear retrieval cache."""
        if self._cache:
            self._cache.clear()

    @property
    def cache_size(self) -> int:
        """Current cache size."""
        return self._cache.size if self._cache else 0


# ============================================================
# Convenience Function
# ============================================================

async def retrieve_multimodal(
    lancedb_client: LanceDBClientProtocol,
    query_vector: List[float],
    media_types: Optional[List[MediaType]] = None,
    top_k: int = 5,
    min_score: float = 0.5,
    timeout_seconds: float = 2.0
) -> List[MultimodalResult]:
    """
    便捷函数: 检索多模态内容

    Args:
        lancedb_client: LanceDB client
        query_vector: 查询向量
        media_types: 媒体类型过滤
        top_k: 返回数量
        min_score: 最小相关度
        timeout_seconds: 超时秒数

    Returns:
        List[MultimodalResult]: 检索结果

    Example:
        >>> results = await retrieve_multimodal(
        ...     lancedb_client,
        ...     query_vector=[0.1, 0.2, ...],
        ...     media_types=[MediaType.IMAGE, MediaType.PDF]
        ... )
    """
    config = MultimodalRetrieverConfig(
        top_k=top_k,
        min_score=min_score,
        timeout_seconds=timeout_seconds,
        enable_cache=False  # No cache for one-off retrievals
    )

    retriever = MultimodalRetriever(lancedb_client, config=config)
    return await retriever.retrieve(
        query_vector=query_vector,
        media_types=media_types
    )


# ============================================================
# LangGraph Node Function
# ============================================================

async def multimodal_retrieval_node(
    state: Dict[str, Any],
    lancedb_client: Optional[LanceDBClientProtocol] = None
) -> Dict[str, Any]:
    """
    LangGraph多模态检索节点

    ✅ Verified from LangGraph Skill (Pattern: Node function signature):
    - Takes state dict
    - Returns partial state update dict

    AC 6.8.1: 添加到StateGraph的多模态检索节点

    Args:
        state: Current graph state containing:
            - query_vector: List[float] - Query embedding
            - messages: List[BaseMessage] - (optional) for text query
        lancedb_client: LanceDB client (injected or from context)

    Returns:
        State update with:
            - multimodal_results: List[MultimodalResult]
            - multimodal_latency_ms: float

    Usage in StateGraph:
        >>> from functools import partial
        >>> from agentic_rag.retrievers import multimodal_retrieval_node
        >>>
        >>> node_fn = partial(multimodal_retrieval_node, lancedb_client=client)
        >>> builder.add_node("multimodal_retrieval", node_fn)
    """
    import time
    start_time = time.time()

    # Get query vector from state
    query_vector = state.get("query_vector")

    if query_vector is None:
        # Try to extract from messages and vectorize
        # This is a fallback - normally query_vector should be pre-computed
        return {
            "multimodal_results": [],
            "multimodal_latency_ms": 0.0,
        }

    if lancedb_client is None:
        # Return empty if no client configured
        return {
            "multimodal_results": [],
            "multimodal_latency_ms": 0.0,
        }

    try:
        retriever = MultimodalRetriever(lancedb_client)
        results = await retriever.retrieve(query_vector)

        latency_ms = (time.time() - start_time) * 1000

        return {
            "multimodal_results": [r.to_dict() for r in results],
            "multimodal_latency_ms": latency_ms,
        }

    except MultimodalRetrievalTimeout:
        # Timeout degradation - return empty results
        latency_ms = (time.time() - start_time) * 1000
        return {
            "multimodal_results": [],
            "multimodal_latency_ms": latency_ms,
        }

    except Exception:
        # Error handling - return empty results
        latency_ms = (time.time() - start_time) * 1000
        return {
            "multimodal_results": [],
            "multimodal_latency_ms": latency_ms,
        }
