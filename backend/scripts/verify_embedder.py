#!/usr/bin/env python
"""可切换 embedder 验证脚本 (2026-06-26)。

验证 EMBEDDER_PROVIDER 选的后端能对中文样本产出 1024 维向量 (主链 D8 就绪),
不连 Neo4j、不写图 — 纯验 embedder 本身。

用法 (容器内):
  # 本地 bge-m3 (推荐, 不受地理封锁):
  docker exec -e EMBEDDER_PROVIDER=local \\
    -e LOCAL_EMBEDDER_BASE_URL=http://host.docker.internal:11434/v1 \\
    canvas-learning-system-backend python scripts/verify_embedder.py
  # 云端 gemini / openai:
  docker exec -e EMBEDDER_PROVIDER=gemini canvas-learning-system-backend python scripts/verify_embedder.py

前置 (local): 宿主机 `ollama serve` + `ollama pull bge-m3`。
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"
EXPECTED_DIM = 1024
SAMPLES = [
    "一个代理 (Agent) 是能够感知环境并采取行动的实体",  # 中文 — 验多语言
    "Maximize expected utility",  # 英文
]


async def main() -> int:
    from app.config import settings
    from app.graphiti.embedder_factory import build_embedder, get_embedder_provider

    provider = get_embedder_provider()
    print(f"EMBEDDER_PROVIDER = {provider}")
    if provider == "local":
        print(
            f"  base_url = {os.getenv('LOCAL_EMBEDDER_BASE_URL') or 'host.docker.internal:11434/v1 (默认)'}"
        )
        print(f"  model    = {os.getenv('LOCAL_EMBEDDER_MODEL') or 'bge-m3 (默认)'}")

    google_key = os.getenv("GOOGLE_API_KEY") or getattr(settings, "GOOGLE_API_KEY", "")
    try:
        embedder = build_embedder(google_key)
    except Exception as e:  # noqa: BLE001
        print(f"{RED}❌ embedder 构造失败: {e}{RESET}")
        return 1

    try:
        for s in SAMPLES:
            vec = await embedder.create(s)
            dim = len(vec)
            ok = dim == EXPECTED_DIM
            mark = f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"
            print(f"  {mark} dim={dim} (期望 {EXPECTED_DIM}) | {s[:22]}")
            if not ok:
                print(
                    f"{YELLOW}⚠️ 维度 {dim}≠{EXPECTED_DIM} → 与存量向量不一致, 语义检索会"
                    f"失效。需重嵌全量或调 EMBEDDING_DIM 环境变量。{RESET}"
                )
                return 1
    except Exception as e:  # noqa: BLE001
        print(f"{RED}❌ embedding 调用失败: {e}{RESET}")
        msg = str(e).lower()
        if "location is not supported" in msg or "failed_precondition" in msg:
            print("   → Gemini 地理封锁: 换 EMBEDDER_PROVIDER=local (bge-m3) 或开 VPN")
        elif "connection" in msg or "refused" in msg or "connect" in msg:
            print(
                "   → 本地端点连不上: 确认宿主机 `ollama serve` 在跑 + "
                "`ollama pull bge-m3` 已下载 + base_url 用 host.docker.internal"
            )
        elif "401" in msg or "unauthorized" in msg:
            print("   → 鉴权失败: 检查 api_key")
        return 1

    print(
        f"{GREEN}✅ embedder ({provider}) 可用 · {EXPECTED_DIM} 维 · 主链 D8 就绪{RESET}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
