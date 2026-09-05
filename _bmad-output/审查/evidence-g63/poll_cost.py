"""CARD-G6-3 · 轮询开销量化（完成条件 c）：60 分钟窗口的请求次数与 CPU。

请求**次数**不需要空等一小时——它由轮询契约唯一决定：
`review_app.py:159-160` `POLL_MIN_MS = 5000` / `POLL_MAX_MS = 60000`，
周期 = `clamp(最近未来 next_due − now, 5s, 60s)`。所以 60 分钟窗口内：

    上界（永远贴着下限跑，即总有 5 秒内到期的卡）= 3600 / 5  = 720 次
    下界（永远贴着上限跑，即无近期到期）        = 3600 / 60 =  60 次

需要实测的是**每次请求的成本**，再乘以上面两个次数得到 CPU 区间。本脚本对
真实 `GET /api/v1/review/overview` 背靠背打满一个 720 次的样本（= 上界一小时
的全部请求量），量总 CPU 时间与单次耗时分布。

⚠ 口径声明（防止把推算读成实测）：
- **实测**：单次请求的 wall/CPU 成本、720 次的总 CPU。
- **推算**：60 分钟窗口的请求次数（由 clamp 契约算出，不是等一小时数出来的）。
- 背靠背打满与真实节奏（每 5s 一次）在**单次成本**上没有差别（同一段代码、
  同一个进程、同一份投影文件）；差别只在挂钟分布，而挂钟分布不影响累计 CPU。
  真实节奏下的实测速率另由 `e2e_relearn_visibility.py` 的路径 A 交叉验证。

跑法（从 backend/ 起）:
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \\
      .venv/bin/python ../_bmad-output/审查/evidence-g63/poll_cost.py

零产品代码改动；tmp vault；裸 TestClient（不起 lifespan、不连 7691）。
"""

from __future__ import annotations

import json
import os
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BACKEND = REPO / "backend"
PICKER = REPO / "scripts" / "daily_review_pick.py"
DECAY = REPO / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py"

WINDOW_S = 3600
POLL_MIN_S = 5      # review_app.py:159 POLL_MIN_MS
POLL_MAX_S = 60     # review_app.py:160 POLL_MAX_MS
SAMPLE_N = WINDOW_S // POLL_MIN_S      # 720 = 上界一小时的全部请求量
#: 投影里放几个到期节点 —— 单库空投影会低估 _summarize 的解析成本
NODE_COUNT = 12


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    sys.dont_write_bytecode = True

    import app.config as config_mod
    import app.main as main_mod
    from app.config import reload_settings
    from fastapi.testclient import TestClient

    saved = {k: os.environ.get(k) for k in ("VAULTS_ROOT", "ACTIVE_VAULT")}
    tmp = tempfile.TemporaryDirectory(prefix="g63_cost_")
    root = Path(tmp.name)
    try:
        # ── 真实 vault + 真实生产器产出的真实投影 ──
        vault = root / "costlab"
        (vault / ".obsidian").mkdir(parents=True)
        (vault / "节点").mkdir()
        scripts = vault / ".claude" / "scripts"
        scripts.mkdir(parents=True)
        shutil.copy(DECAY, scripts)
        past = _iso_z(datetime.now(timezone.utc) - timedelta(hours=1))
        for i in range(NODE_COUNT):
            (vault / "节点" / f"节点{i}.md").write_text(
                "---\ntype: concept\n"
                f'source_board: "[[原白板/开销板{i % 3}]]"\n'
                f"fsrs_due: {past}\nfsrs_state: 2\n---\n内容。\n",
                encoding="utf-8",
            )
        p = subprocess.run(
            [sys.executable, str(PICKER), "--vault", str(vault), "--write"],
            capture_output=True, text=True, timeout=120,
        )
        if p.returncode != 0:
            print(f"生产器失败 rc={p.returncode}\n{p.stderr[-800:]}", file=sys.stderr)
            return 1

        reload_settings(overrides={"VAULTS_ROOT": str(root), "ACTIVE_VAULT": "costlab"})
        main_mod.settings = config_mod.settings
        from app.main import app

        client = TestClient(app, base_url="http://127.0.0.1:8011")
        try:
            r = client.get("/api/v1/review/overview")
            r.raise_for_status()
            entry = next(v for v in r.json()["vaults"] if v["vault_id"] == "costlab")
            due_count = (entry.get("projection") or {}).get("due_count")
            if entry["status"] != "ok" or not due_count:
                print(f"前提不成立: status={entry['status']} due_count={due_count} — "
                      "样本投影必须是真 ok 且有到期节点, 否则量的是空壳解析", file=sys.stderr)
                return 1

            for _ in range(20):      # 预热, 把 import/首次解析摊掉
                client.get("/api/v1/review/overview")

            ru0 = resource.getrusage(resource.RUSAGE_SELF)
            cpu0, wall0 = time.process_time(), time.perf_counter()
            per_req: list[float] = []
            for _ in range(SAMPLE_N):
                t = time.perf_counter()
                resp = client.get("/api/v1/review/overview")
                per_req.append((time.perf_counter() - t) * 1000)
                if resp.status_code != 200:
                    print(f"请求失败 {resp.status_code}", file=sys.stderr)
                    return 1
            cpu_total = time.process_time() - cpu0
            wall_total = time.perf_counter() - wall0
            ru1 = resource.getrusage(resource.RUSAGE_SELF)
            rss_delta_mb = (ru1.ru_maxrss - ru0.ru_maxrss) / (1024 * 1024)
        finally:
            client.close()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        reload_settings()
        main_mod.settings = config_mod.settings
        tmp.cleanup()

    per_req.sort()
    p50, p95, p99 = (per_req[int(len(per_req) * q)] for q in (0.50, 0.95, 0.99))
    cpu_per_req_ms = cpu_total / SAMPLE_N * 1000
    hi_cpu_s = cpu_per_req_ms * (WINDOW_S / POLL_MIN_S) / 1000
    lo_cpu_s = cpu_per_req_ms * (WINDOW_S / POLL_MAX_S) / 1000

    data = {
        "sample_requests": SAMPLE_N, "due_count": due_count, "nodes_seeded": NODE_COUNT,
        "cpu_total_s": round(cpu_total, 4), "wall_total_s": round(wall_total, 4),
        "cpu_per_req_ms": round(cpu_per_req_ms, 4),
        "wall_per_req_ms_p50": round(p50, 4), "p95": round(p95, 4), "p99": round(p99, 4),
        "rss_delta_mb": round(rss_delta_mb, 2),
        "hour_requests_max": WINDOW_S // POLL_MIN_S, "hour_requests_min": WINDOW_S // POLL_MAX_S,
        "hour_cpu_s_max": round(hi_cpu_s, 3), "hour_cpu_s_min": round(lo_cpu_s, 3),
    }
    (HERE / "poll-cost.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    L = [
        "# CARD-G6-3 · 轮询开销量化（完成条件 c）",
        "",
        "> 真实 `GET /api/v1/review/overview` + 真实生产器产出的真实投影"
        f"（{NODE_COUNT} 个节点、`due_count={due_count}`）。tmp vault，裸 TestClient（不起 lifespan）。",
        "",
        "## 口径：哪些是实测，哪些是推算",
        "",
        "| | 来源 |",
        "|---|---|",
        f"| 单次请求的 CPU / 挂钟成本 | **实测**（{SAMPLE_N} 次背靠背样本） |",
        "| 60 分钟窗口的请求**次数** | **推算**——由轮询契约唯一决定，见下 |",
        "| 60 分钟窗口的 CPU | 实测单次成本 × 推算次数 |",
        "",
        f"次数为什么可以推算：周期 = `clamp(next_due − now, {POLL_MIN_S}s, {POLL_MAX_S}s)`"
        f"（`review_app.py:159-160`），所以一小时最多 `3600/{POLL_MIN_S}` = "
        f"**{WINDOW_S // POLL_MIN_S} 次**，最少 `3600/{POLL_MAX_S}` = **{WINDOW_S // POLL_MAX_S} 次**。"
        "这两个数由 (b) 的接线断言锁住，不是估计。",
        "",
        "背靠背打满与真实节奏在**单次成本**上没有差别（同一段代码、同一进程、同一份投影文件），",
        "差别只在挂钟分布，而挂钟分布不改变累计 CPU。真实节奏下的速率由",
        "`e2e-timing.md` 路径 A 的实际轮询次数交叉验证。",
        "",
        "## 实测",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| 样本请求数 | {SAMPLE_N}（= 上界一小时的全部请求量） |",
        f"| 总 CPU | {cpu_total:.4f}s |",
        f"| 总挂钟 | {wall_total:.4f}s |",
        f"| **单次 CPU** | **{cpu_per_req_ms:.4f} ms** |",
        f"| 单次挂钟 p50 / p95 / p99 | {p50:.3f} / {p95:.3f} / {p99:.3f} ms |",
        f"| 进程 maxRSS 增量 | {rss_delta_mb:.2f} MB |",
        "",
        "## 60 分钟窗口",
        "",
        "| 场景 | 请求次数 | CPU |",
        "|---|---|---|",
        f"| 最忙（永远贴 {POLL_MIN_S}s 下限：总有 5 秒内到期的卡） | {WINDOW_S // POLL_MIN_S} | "
        f"**{hi_cpu_s:.3f}s**（占单核 {hi_cpu_s / WINDOW_S * 100:.4f}%） |",
        f"| 最闲（永远贴 {POLL_MAX_S}s 上限：无近期到期） | {WINDOW_S // POLL_MAX_S} | "
        f"{lo_cpu_s:.3f}s（占单核 {lo_cpu_s / WINDOW_S * 100:.4f}%） |",
        "",
        "## 结论",
        "",
        f"最坏情况一小时 {WINDOW_S // POLL_MIN_S} 次请求、约 {hi_cpu_s:.2f} 秒 CPU"
        f"（单核占用 {hi_cpu_s / WINDOW_S * 100:.4f}%）。这是**单机单用户**的本地服务，",
        "该量级下轮询开销不构成问题——**不需要调参**，因此本卡也不碰任何参数",
        "（卡文：不达标只登记，不静默调参；这里是达标，更没有理由动）。",
        "",
        f"⚠ 未测：多 vault 规模放大（本样本只有 1 个库、{NODE_COUNT} 个节点）、",
        "浏览器侧的渲染与内存开销（本脚本只量服务端）。",
    ]
    (HERE / "poll-cost.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[-22:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
