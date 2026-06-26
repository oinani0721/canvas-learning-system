"""可切换 embedder 工厂 (2026-06-26): 摆脱 Gemini 地理封锁单点依赖。

背景: gemini-embedding-001 对部分区域返回 'User location is not supported' →
Graphiti 写路径 (D8 显式 embedding) 全挂。本工厂用环境变量切后端, 主链不改。

为什么 embedding 适合本地化: 本项目主链 (write_callout/write_relation_reason) 是
D2 确定性写入、零 LLM, 只用 embedder 产向量。embedding 是纯向量、无结构化 JSON
要求, 本地模型做这个很稳 (社区 Graphiti+Ollama 的坑多在 LLM 抽取, 不在 embedder)。

EMBEDDER_PROVIDER 环境变量:
- gemini (默认, 向后兼容): GeminiEmbedder / gemini-embedding-001, 需 GOOGLE_API_KEY
- openai: OpenAIEmbedder / text-embedding-3-small, 需 OPENAI_API_KEY
- local:  OpenAIEmbedder + base_url 指向 Ollama/LM Studio (OpenAI 兼容) / bge-m3,
          不受地理封锁、零云端成本。api_key 用占位符。

⚠️ 维度一致性 (硬约束): graphiti EMBEDDING_DIM 默认 1024。换 provider 前确认存量
向量维度一致, 否则语义检索失效需重嵌:
- gemini-embedding-001 → output_dimensionality=1024
- text-embedding-3-small → 原生 1536, graphiti 切片 [:1024]
- bge-m3 → 原生 1024 (与现有数据匹配, 换过去不用重嵌)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_OLLAMA_DEFAULT_BASE_URL = "http://host.docker.internal:11434/v1"


def get_embedder_provider() -> str:
    """当前 embedder 后端 (gemini|openai|local), 默认 gemini。"""
    return (os.getenv("EMBEDDER_PROVIDER") or "gemini").strip().lower()


def build_embedder(google_api_key: str = "", *, embedding_dim: int = 1024) -> Any:
    """按 EMBEDDER_PROVIDER 构造 graphiti EmbedderClient。

    Args:
        google_api_key: gemini 路径的 key (env GOOGLE_API_KEY 兜底)。
        embedding_dim: 目标维度, 须与存量一致 (默认 1024)。
    """
    provider = get_embedder_provider()

    if provider == "local":
        from graphiti_core.embedder.openai import (
            OpenAIEmbedder,
            OpenAIEmbedderConfig,
        )

        base_url = os.getenv("LOCAL_EMBEDDER_BASE_URL") or _OLLAMA_DEFAULT_BASE_URL
        model = os.getenv("LOCAL_EMBEDDER_MODEL") or "bge-m3"
        logger.info("[Embedder] provider=local model=%s base_url=%s", model, base_url)
        return OpenAIEmbedder(
            config=OpenAIEmbedderConfig(
                api_key=os.getenv("LOCAL_EMBEDDER_API_KEY") or "ollama",
                base_url=base_url,
                embedding_model=model,
                embedding_dim=embedding_dim,
            )
        )

    if provider == "openai":
        from graphiti_core.embedder.openai import (
            OpenAIEmbedder,
            OpenAIEmbedderConfig,
        )

        model = os.getenv("OPENAI_EMBEDDER_MODEL") or "text-embedding-3-small"
        logger.info("[Embedder] provider=openai model=%s", model)
        return OpenAIEmbedder(
            config=OpenAIEmbedderConfig(
                api_key=os.getenv("OPENAI_API_KEY") or "",
                base_url=os.getenv("OPENAI_BASE_URL") or None,
                embedding_model=model,
                embedding_dim=embedding_dim,
            )
        )

    # 默认: gemini (向后兼容)
    from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig

    key = google_api_key or os.getenv("GOOGLE_API_KEY") or ""
    model = os.getenv("GEMINI_EMBEDDER_MODEL") or "gemini-embedding-001"
    logger.info("[Embedder] provider=gemini model=%s", model)
    return GeminiEmbedder(
        config=GeminiEmbedderConfig(api_key=key, embedding_model=model)
    )
