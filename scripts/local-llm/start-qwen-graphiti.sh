#!/usr/bin/env bash
# Graphiti 本地 LLM 宿主启动脚本 (M1 2026-07-13, 路线图 v2)
#
# ⛔ 参数即契约 — `--reasoning off --reasoning-budget 0` 是 canary 通过的
# 前提条件, 不是可调优化项:
#   开思考:  5 跑 2 挂 (content 为空/JSON 截断), avg 107s/p95 171s
#   关思考: 50 跑零失败, avg 1.42s / p95 1.57s  ← 2026-07-13 基线
# 机理: json_schema 语法约束只作用于 content, 思维链不受约束地消耗 token
# 预算, 烧穿即产出空 content (LM Studio #1773 同病理)。改任何 runtime 参数
# 或换模型后必须重跑 canary:
#   docker exec canvas-learning-system-backend python \
#     /app/scripts/graphiti_schema_canary.py \
#     --base-url http://host.docker.internal:12341/v1 \
#     --model qwen3.5-35b-a3b-q4_k_s --runs 50
#
# 模型: Qwen3.5-35B-A3B Q4_K_S (MoE, ~3B 激活参数), 权重缓存于
# ~/.cache/huggingface, 首次运行自动下载 (~20GB)。
set -euo pipefail

PORT="${GRAPHITI_LLM_PORT:-12341}"

if curl -s -m 2 "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1; then
    echo "llama-server 已在 :${PORT} 运行, 无需重复启动"
    exit 0
fi

exec llama-server \
    -hf bartowski/Qwen_Qwen3.5-35B-A3B-GGUF:Q4_K_S \
    --host 127.0.0.1 \
    --port "${PORT}" \
    -ngl 999 \
    -c 16384 \
    --parallel 1 \
    --alias qwen3.5-35b-a3b-q4_k_s \
    --jinja \
    --reasoning off \
    --reasoning-budget 0
