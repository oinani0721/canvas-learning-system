"""
Agentic RAG - 混合Reranking策略实现

Story 12.8: 混合Reranking策略
Story 2.2: Phase 0 搜索通道修复 - Reranker激活

- Local Cross-Encoder (bge-reranker-base)
- Cohere Rerank API
- Hybrid自动选择逻辑

Author: Canvas Learning System Team
Version: 2.0.0
Created: 2025-11-29
Updated: 2026-03-16 (Story 2.2 - Phase 0 Reranker激活)
"""

import asyncio
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from agentic_rag.state import SearchResult

logger = logging.getLogger(__name__)

# ========================================
# Dependency availability flags
# ========================================

try:
    import torch
    from sentence_transformers import CrossEncoder

    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Local reranking unavailable.")

try:
    import cohere

    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    logger.info("cohere not installed. Cohere API reranking unavailable.")


# ========================================
# Reranking策略枚举
# ========================================


class RerankStrategy(str, Enum):
    LOCAL = "local"
    COHERE = "cohere"
    HYBRID_AUTO = "hybrid_auto"


# ========================================
# Local Cross-Encoder Reranker
# ========================================


class LocalReranker:
    """
    本地Cross-Encoder Reranker (bge-reranker-base)

    Phase 0: bge-reranker-base (102M, 中文支持)
    Phase 1 Story 2.5: 升级为 bge-reranker-v2-m3 (568M, fp16)
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: Optional[str] = None,
        batch_size: int = 32,
    ):
        if not CROSS_ENCODER_AVAILABLE:
            raise ImportError("sentence-transformers not installed. Install with: pip install sentence-transformers")

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = CrossEncoder(model_name, device=device)

        logger.info(f"LocalReranker initialized: {model_name} on {device} (batch_size={batch_size})")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
        return_documents: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using Cross-Encoder.

        Returns list of dicts: [{index, score, document}, ...]
        sorted by score descending.
        """
        if not documents:
            return _empty_list()

        pairs = [(query, doc) for doc in documents]

        loop = asyncio.get_running_loop()
        scores = await loop.run_in_executor(
            None,
            lambda: self.model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
            ),
        )

        scored_docs = [
            {
                "index": i,
                "score": float(score),
                "document": doc if return_documents else None,
            }
            for i, (doc, score) in enumerate(zip(documents, scores))
        ]
        scored_docs.sort(key=lambda x: x["score"], reverse=True)

        return scored_docs[:top_k]

    async def rerank_search_results(
        self,
        query: str,
        search_results: List[SearchResult],
        top_k: int = 10,
    ) -> List[SearchResult]:
        """Rerank a list of SearchResult, returning updated results with reranker scores."""
        if not search_results:
            return _empty_list()

        documents = [r["content"] for r in search_results]

        reranked = await self.rerank(
            query=query,
            documents=documents,
            top_k=min(top_k, len(documents)),
            return_documents=False,
        )

        result_list = []
        for r in reranked:
            original_result = dict(search_results[r["index"]])
            original_result["rerank_score"] = r["score"]
            original_result["original_score"] = original_result.get("score", 0.0)
            original_result["score"] = r["score"]
            if "metadata" not in original_result:
                original_result["metadata"] = {}
            original_result["metadata"]["reranked"] = True
            result_list.append(original_result)

        return result_list


# ========================================
# Cohere Rerank API Wrapper
# ========================================


class CohereReranker:
    """Cohere Rerank API Wrapper (rerank-multilingual-v3.0)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "rerank-multilingual-v3.0",
    ):
        if not COHERE_AVAILABLE:
            raise ImportError("cohere not installed. Install with: pip install cohere")

        api_key = api_key or os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError(
                "Cohere API key not found. Set COHERE_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.client = cohere.Client(api_key=api_key)

        self.call_count = 0
        self.total_cost = 0.0
        self.cost_per_request = 0.002

        logger.info(f"CohereReranker initialized: {model}")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
        return_documents: bool = True,
    ) -> List[Dict[str, Any]]:
        if not documents:
            return _empty_list()

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.rerank(
                    query=query,
                    documents=documents,
                    top_n=min(top_k, len(documents)),
                    model=self.model,
                ),
            )

            self.call_count += 1
            self.total_cost += self.cost_per_request

            results = []
            for r in response.results:
                results.append(
                    {
                        "index": r.index,
                        "score": r.relevance_score,
                        "document": documents[r.index] if return_documents else None,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            # Graceful degradation: return documents with default scores
            return [
                {
                    "index": i,
                    "score": 0.5,
                    "document": doc if return_documents else None,
                }
                for i, doc in enumerate(documents[:top_k])
            ]

    async def rerank_search_results(
        self,
        query: str,
        search_results: List[SearchResult],
        top_k: int = 10,
    ) -> List[SearchResult]:
        if not search_results:
            return _empty_list()

        documents = [r["content"] for r in search_results]

        reranked = await self.rerank(
            query=query,
            documents=documents,
            top_k=min(top_k, len(documents)),
            return_documents=False,
        )

        result_list = []
        for r in reranked:
            original_result = dict(search_results[r["index"]])
            original_result["rerank_score"] = r["score"]
            original_result["original_score"] = original_result.get("score", 0.0)
            original_result["score"] = r["score"]
            if "metadata" not in original_result:
                original_result["metadata"] = {}
            original_result["metadata"]["reranked"] = True
            result_list.append(original_result)

        return result_list

    def get_cost_stats(self) -> Dict[str, Any]:
        return {
            "call_count": self.call_count,
            "total_cost": self.total_cost,
            "cost_per_request": self.cost_per_request,
        }


def _empty_list() -> list:
    """Return a new empty list. Used as sentinel for empty-input guards."""
    return list()


# ========================================
# Module-level exports
# ========================================

__all__ = [
    "RerankStrategy",
    "LocalReranker",
    "CohereReranker",
    "CROSS_ENCODER_AVAILABLE",
    "COHERE_AVAILABLE",
]
