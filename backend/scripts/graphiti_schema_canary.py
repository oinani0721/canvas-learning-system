#!/usr/bin/env python3
"""M1 (2026-07-13 路线图 v2) — Graphiti schema canary: 本地 LLM 运行时上线前的硬门控。

背景 (ChatGPT DR + 内部调研交叉验证):
  Graphiti add_episode 是 6-12 次链式 structured output 调用, 任何一步
  fail-open 就在 Pydantic 层形成间歇性死信。两个已知实锤:
  - LM Studio #1773: Qwen3.5 reasoning 模型 json_schema 约束跑进
    reasoning_content, final content 为空
  - llama.cpp #21228: 嵌套 $ref/$defs schema 静默退化为无约束
  所以 canary 必须用 graphiti_core **真实嵌套 schema** (含 $defs) 而非
  玩具 schema, 且验收是 6 条硬标准连续 N 次零失败。

用法 (容器内跑, 端点经 host.docker.internal 指向宿主):
  docker exec canvas-learning-system-backend python /app/scripts/graphiti_schema_canary.py \
      --base-url http://host.docker.internal:12341/v1 \
      --model qwen3.5-35b-a3b-q4_k_s \
      --runs 50

退出码: 0 = 全部通过 (decision: enable_worker); 1 = 任一失败 (disable_worker)。
fail-closed 契约: M2 的 llm_factory 在启动时调本脚本 (或复用其 probe 函数),
失败则不启用语义抽取 worker — 结构化直写主链不受影响。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from typing import Any

import httpx

# ── Graphiti 真实嵌套 schema (含 $defs — #21228 的风险形状) ──
try:
    from graphiti_core.prompts.extract_nodes import ExtractedEntities

    REAL_SCHEMA = ExtractedEntities.model_json_schema()
    PYDANTIC_MODEL: Any = ExtractedEntities
except ImportError:  # 宿主裸跑时的后备 (形状等价, 手工含 $defs)
    REAL_SCHEMA = {
        "$defs": {
            "ExtractedEntity": {
                "properties": {
                    "name": {"title": "Name", "type": "string"},
                    "entity_type_id": {"title": "Entity Type Id", "type": "integer"},
                    "episode_indices": {
                        "items": {"type": "integer"},
                        "title": "Episode Indices",
                        "type": "array",
                    },
                },
                "required": ["name", "entity_type_id", "episode_indices"],
                "title": "ExtractedEntity",
                "type": "object",
            }
        },
        "properties": {
            "extracted_entities": {
                "items": {"$ref": "#/$defs/ExtractedEntity"},
                "title": "Extracted Entities",
                "type": "array",
            }
        },
        "required": ["extracted_entities"],
        "title": "ExtractedEntities",
        "type": "object",
    }
    PYDANTIC_MODEL = None

# 中文学习批注真实样例 (轮换使用, 贴近生产语料)
SAMPLE_NOTES = [
    "我总是把逆否命题和否命题混在一起，逆否命题是同时否定并交换前后件，否命题只否定不交换。",
    "特征值 λ 表示矩阵 A 在特征向量 v 方向上的缩放比例，Av = λv，如果 λ=0 说明矩阵不可逆。",
    "动态规划的关键是最优子结构和重叠子问题，斐波那契用记忆化能从指数降到线性。",
    "贝叶斯公式 P(A|B) = P(B|A)P(A)/P(B)，先验概率乘以似然再归一化，我老是忘记分母。",
    "MDP 的价值迭代和策略迭代区别：价值迭代每步都更新 V(s)，策略迭代交替做评估和改进。",
]

SYSTEM_PROMPT = (
    "You are an entity extraction assistant. Extract entities from the given "
    "Chinese learning note. Entity types: 0=Concept, 1=Person, 2=Method. "
    "Return only valid JSON matching the schema."
)

THINK_RE = re.compile(r"<think>|</think>|<thinking>|◁think▷", re.I)
FENCE_RE = re.compile(r"^\s*```")


def check_response(body: dict[str, Any]) -> dict[str, bool]:
    """对单次响应跑 6 条硬标准, 返回逐项结果。"""
    checks = {
        "content_nonempty": False,
        "no_think_leak": False,
        "no_markdown_fence": False,
        "json_parses": False,
        "pydantic_validates": False,
        "not_in_reasoning_field": False,
    }
    msg = (body.get("choices") or [{}])[0].get("message", {})
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""

    checks["content_nonempty"] = bool(content.strip())
    checks["no_think_leak"] = not THINK_RE.search(content)
    checks["no_markdown_fence"] = not FENCE_RE.match(content or "")
    # #1773 症状: 约束输出落在 reasoning_content 而 content 为空
    checks["not_in_reasoning_field"] = not (
        not content.strip() and reasoning.strip().startswith("{")
    )
    try:
        parsed = json.loads(content)
        checks["json_parses"] = True
    except (json.JSONDecodeError, TypeError):
        return checks
    if PYDANTIC_MODEL is not None:
        try:
            PYDANTIC_MODEL.model_validate(parsed)
            checks["pydantic_validates"] = True
        except Exception:
            pass
    else:  # 无 graphiti_core 时的等价结构校验
        ents = parsed.get("extracted_entities")
        checks["pydantic_validates"] = isinstance(ents, list) and all(
            isinstance(e, dict)
            and isinstance(e.get("name"), str)
            and isinstance(e.get("entity_type_id"), int)
            for e in ents
        )
    return checks


async def run_canary(base_url: str, model: str, runs: int, timeout: float) -> int:
    payload_base = {
        "model": model,
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "extracted_entities",
                "strict": True,
                "schema": REAL_SCHEMA,
            },
        },
    }
    tally: dict[str, int] = {}
    failures: list[tuple[int, dict[str, bool]]] = []
    latencies: list[float] = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for i in range(runs):
            note = SAMPLE_NOTES[i % len(SAMPLE_NOTES)]
            payload = {
                **payload_base,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": note},
                ],
            }
            t0 = time.monotonic()
            try:
                resp = await client.post(
                    f"{base_url.rstrip('/')}/chat/completions", json=payload
                )
                resp.raise_for_status()
                body = resp.json()
            except Exception as e:  # noqa: BLE001 — 网络/HTTP 失败也是 canary 失败
                print(f"  run {i + 1}/{runs}: TRANSPORT FAIL ({type(e).__name__}: {e})")
                failures.append((i, {"transport": False}))
                continue
            latencies.append(time.monotonic() - t0)

            checks = check_response(body)
            for k, v in checks.items():
                tally[k] = tally.get(k, 0) + (1 if v else 0)
            if not all(checks.values()):
                failures.append((i, checks))
                bad = [k for k, v in checks.items() if not v]
                print(f"  run {i + 1}/{runs}: FAIL {bad}")
            elif (i + 1) % 10 == 0:
                print(
                    f"  run {i + 1}/{runs}: ok (avg {sum(latencies) / len(latencies):.1f}s)"
                )

    # ── 报告 (对齐 ChatGPT DR 建议的 canary 日志格式) ──
    ok = not failures
    decision = "enable_worker" if ok else "disable_worker"
    report = {
        "graphiti_llm_schema_canary": {
            "base_url": base_url,
            "model": model,
            "runs": runs,
            "passed": runs - len(failures),
            "failed": len(failures),
            "per_check_pass": tally,
            "avg_latency_s": round(sum(latencies) / len(latencies), 2)
            if latencies
            else None,
            "p95_latency_s": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 2)
            if len(latencies) >= 2
            else None,
            "decision": decision,
        }
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", required=True, help="OpenAI 兼容端点 (含 /v1)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--runs", type=int, default=50)
    ap.add_argument("--timeout", type=float, default=120.0)
    args = ap.parse_args()
    sys.exit(
        asyncio.run(run_canary(args.base_url, args.model, args.runs, args.timeout))
    )


if __name__ == "__main__":
    main()
