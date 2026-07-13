#!/usr/bin/env bash
# Graphiti 本地 reranker 宿主启动脚本 (M5 2026-07-13, 路线图 v2)
#
# bge-reranker-v2-m3 @ llama-server --rerank 模式: 只暴露 /v1/rerank,
# 无 chat 端点 — 后端经 app/graphiti/rerank_client.py 适配器对接
# (graphiti 自带 OpenAIRerankerClient 走 chat+logprobs 协议, 不兼容)。
# ⛔ 不可换成 Ollama / LM Studio: 两者均无 rerank 端点。
#
# 真机基线 (2026-07-13): "特征值为零意味着什么" → 正确文档 logit +4.74,
# 干扰项 -7.6 / -10.9, 语义排序正确。
set -euo pipefail

PORT="${GRAPHITI_RERANKER_PORT:-18012}"

if curl -s -m 2 "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1; then
    echo "reranker llama-server 已在 :${PORT} 运行, 无需重复启动"
    exit 0
fi

exec llama-server \
    -hf gpustack/bge-reranker-v2-m3-GGUF:Q8_0 \
    --host 127.0.0.1 \
    --port "${PORT}" \
    -ngl 999 \
    --rerank \
    --alias bge-reranker-v2-m3
