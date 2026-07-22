"""M2 (2026-07-13, 路线图 v2) — 可切换 Graphiti LLM / reranker 工厂。

镜像 embedder_factory 模式 (2026-06-26 已验证)。背景: episode_worker 此前
硬接 GeminiClient + GeminiRerankerClient; 用户拍板 Graphiti 语义通道换本地
模型 (M5 Max, ChatGPT DR + 内部调研交叉验证定稿多服务分工拓扑)。

GRAPHITI_LLM_PROVIDER 环境变量:
- gemini (默认, 向后兼容): GeminiClient / gemini-2.5-flash, 需 GOOGLE_API_KEY
- local: OpenAIGenericClient + base_url 指向宿主 llama-server / LM Studio
  (OpenAI 兼容)。⛔ fail-closed 契约: local 分支上线前必须通过
  scripts/graphiti_schema_canary.py (6 条硬标准 × 50 次零失败) —— 两个已知
  实锤: LM Studio #1773 (reasoning 模型 json_schema 输出跑进
  reasoning_content), llama.cpp #21228 (嵌套 $defs schema 静默 fail-open)。
  canary 未通过就启用 = 语义抽取链间歇性死信。

GRAPHITI_RERANKER_PROVIDER 环境变量:
- gemini (默认): GeminiRerankerClient
- local: OpenAIRerankerClient 指向宿主 llama-server /v1/rerank
  (bge-reranker-v2-m3, --pooling rank --rerank)。⛔ 不可指向 Ollama
  (无 rerank 端点) 或 LM Studio (无 rerank 端点, 会错误映射到 embeddings);
  实测 Ollama /v1 的 logprobs 返回 None 会让 OpenAIRerankerClient 崩溃。

并发: 本地 35B 场景 compose 侧 SEMAPHORE_LIMIT=1 + max_coroutines 用
get_graphiti_max_coroutines() (默认云 3 / local 1)。
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_LOCAL_LLM_DEFAULT_BASE_URL = "http://host.docker.internal:12341/v1"
_LOCAL_RERANK_DEFAULT_BASE_URL = "http://host.docker.internal:18012/v1"


def get_llm_provider() -> str:
    """当前 Graphiti LLM 后端 (gemini|local), 默认 gemini。"""
    return (os.getenv("GRAPHITI_LLM_PROVIDER") or "gemini").strip().lower()


def get_reranker_provider() -> str:
    """当前 Graphiti reranker 后端 (gemini|local), 默认 gemini。"""
    return (os.getenv("GRAPHITI_RERANKER_PROVIDER") or "gemini").strip().lower()


def get_graphiti_max_coroutines() -> int:
    """Graphiti 内部并发: local 默认 1 (35B 本地推理), 云默认 3。"""
    explicit = os.getenv("GRAPHITI_MAX_COROUTINES")
    if explicit:
        return max(1, int(explicit))
    return 1 if get_llm_provider() == "local" else 3


async def check_local_providers_health() -> list[str]:
    """local provider 宿主进程可达性自检 (MEM-FLYWHEEL-2026-07-22 批次0 0-1)。

    返回不可达项的人话描述列表 (空 = 全部健康或未启用 local)。
    宿主 llama-server 进程死亡时 add_episode/rerank 会静默失败且无
    fallback (provider 为 env 静态选择) — 此处在启动时点名告警,
    替代「用户几天后才发现语义记忆没入图」。
    """
    import httpx

    probes: list[tuple[str, str, str]] = []
    if get_llm_provider() == "local":
        base = os.getenv("GRAPHITI_LLM_BASE_URL") or _LOCAL_LLM_DEFAULT_BASE_URL
        probes.append(
            (
                "语义抽取 LLM (Qwen@12341)",
                f"{base.rstrip('/')}/models",
                "scripts/local-llm/start-qwen-graphiti.sh",
            )
        )
    if get_reranker_provider() == "local":
        base = os.getenv("GRAPHITI_RERANKER_BASE_URL") or _LOCAL_RERANK_DEFAULT_BASE_URL
        probes.append(
            (
                "检索精排 reranker (@18012)",
                f"{base.rstrip('/')}/models",
                "scripts/local-llm/start-reranker-graphiti.sh",
            )
        )

    unreachable: list[str] = []
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url, fix in probes:
            try:
                await client.get(url)
            except Exception:
                unreachable.append(f"{name} 不可达 ({url}) — 修复: 宿主机运行 {fix}")
    return unreachable


def build_llm_client(google_api_key: str = "", llm_model: str = "") -> Any:
    """按 GRAPHITI_LLM_PROVIDER 构造 graphiti LLMClient。

    local 分支使用 OpenAIGenericClient (graphiti 官方对 OpenAI 兼容本地端点
    的推荐 client, 自带 2 次带错误反馈的重试)。
    """
    from graphiti_core.llm_client.config import LLMConfig

    provider = get_llm_provider()

    if provider == "local":
        from graphiti_core.llm_client.openai_generic_client import (
            OpenAIGenericClient,
        )

        base_url = os.getenv("GRAPHITI_LLM_BASE_URL") or _LOCAL_LLM_DEFAULT_BASE_URL
        model = os.getenv("GRAPHITI_LLM_MODEL") or "qwen3.5-35b-a3b-q4_k_s"
        logger.info(
            "[Graphiti-LLM] provider=local model=%s base_url=%s "
            "(⛔ 须已通过 schema canary — fail-closed 契约)",
            model,
            base_url,
        )
        return OpenAIGenericClient(
            config=LLMConfig(
                api_key=os.getenv("GRAPHITI_LLM_API_KEY") or "local",
                base_url=base_url,
                model=model,
            )
        )

    # 默认: gemini (向后兼容)
    from graphiti_core.llm_client.gemini_client import GeminiClient

    key = google_api_key or os.getenv("GOOGLE_API_KEY") or ""
    model = llm_model or os.getenv("GRAPHITI_LLM_MODEL") or "gemini-2.5-flash"
    logger.info("[Graphiti-LLM] provider=gemini model=%s", model)
    return GeminiClient(config=LLMConfig(api_key=key, model=model))


def build_cross_encoder(google_api_key: str = "", llm_model: str = "") -> Any:
    """按 GRAPHITI_RERANKER_PROVIDER 构造 graphiti CrossEncoderClient。

    ⚠️ 不能传 None 给 Graphiti(cross_encoder=...) — graphiti 默认会构造
    需要 OPENAI_API_KEY 的 OpenAIRerankerClient (启动即炸)。
    """
    from graphiti_core.llm_client.config import LLMConfig

    provider = get_reranker_provider()

    if provider == "local":
        # M5 (2026-07-13): 不能用 graphiti 的 OpenAIRerankerClient —
        # 它走 chat+logprobs 布尔分类协议, 而 llama-server --rerank 只
        # 暴露 /v1/rerank 端点。用自研适配器直连 rerank 协议。
        from app.graphiti.rerank_client import LlamaServerRerankerClient

        base_url = (
            os.getenv("GRAPHITI_RERANKER_BASE_URL") or _LOCAL_RERANK_DEFAULT_BASE_URL
        )
        model = os.getenv("GRAPHITI_RERANKER_MODEL") or "bge-reranker-v2-m3"
        logger.info(
            "[Graphiti-Reranker] provider=local model=%s base_url=%s "
            "(llama-server --rerank, /v1/rerank 协议适配器)",
            model,
            base_url,
        )
        return LlamaServerRerankerClient(base_url=base_url, model=model)

    # 默认: gemini (向后兼容; 当前 cross_encoder recipe 无调用方, 占位为主)
    from graphiti_core.cross_encoder.gemini_reranker_client import (
        GeminiRerankerClient,
    )

    key = google_api_key or os.getenv("GOOGLE_API_KEY") or ""
    model = llm_model or "gemini-2.5-flash"
    logger.info("[Graphiti-Reranker] provider=gemini model=%s", model)
    return GeminiRerankerClient(config=LLMConfig(api_key=key, model=model))
