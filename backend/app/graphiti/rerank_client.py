"""M5 (2026-07-13, 路线图 v2) — llama-server /v1/rerank 适配器。

graphiti_core 自带的 OpenAIRerankerClient 走 chat completions + logprobs
布尔分类协议, 不能对接 bge-reranker-v2-m3: llama-server --rerank 模式只
暴露 /v1/rerank (无 chat 端点), 且 bge-reranker 是 cross-encoder 序列
分类模型而非生成模型。本适配器实现 graphiti CrossEncoderClient 接口,
直连 rerank 协议 — 即路线图 M5 的"30 行适配器"。

宿主启动: scripts/local-llm/start-reranker-graphiti.sh (:18012)。
真机基线 (2026-07-13): query"特征值为零意味着什么" → 正确文档 logit
+4.74, 干扰项 -7.6/-10.9, 语义排序正确。
"""

from __future__ import annotations

import math

import httpx
from graphiti_core.cross_encoder.client import CrossEncoderClient


class LlamaServerRerankerClient(CrossEncoderClient):
    """bge-reranker-v2-m3 @ llama-server --rerank 的 CrossEncoderClient。"""

    def __init__(self, base_url: str, model: str, timeout: float = 15.0):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        if not passages:
            return []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/rerank",
                json={
                    "model": self._model,
                    "query": query,
                    "documents": passages,
                },
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
        # bge 返回原始 logit (可为负); sigmoid 归一到 (0,1), 对齐 graphiti
        # 其他 CrossEncoder 实现的分数量纲 (logprob 概率)。
        scored = [
            (
                passages[r["index"]],
                1.0 / (1.0 + math.exp(-float(r["relevance_score"]))),
            )
            for r in results
            if isinstance(r.get("index"), int) and 0 <= r["index"] < len(passages)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
