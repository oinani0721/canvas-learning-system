#!/usr/bin/env python
"""G0 评测门禁 (MEM-FLYWHEEL-2026-07-22): 记忆检索 gold set 回归。

对 tests/regression/memory_gold_set.yaml 的 25 条 query 批跑生产检索链 —
打运行中 backend 的真接口 POST /mcp/tools/search_memories (与 Claudian MCP
工具、2026-07-22 对抗审查 12 query 实测完全同链), 产出 5 指标并与固化基线
比较 — 任一指标回退超容差即 fail。
此后每批 (批次1'/2'/3'/4') 完成必跑, 作为检索/清污/收敛改动的强制验收挡板。

为什么打 HTTP 而不直调服务层: Tier 1 (Graphiti 语义搜索, 主信号源) 依赖
episode_worker, 它只在 FastAPI lifespan 里启动 — 独立进程直调服务层时
worker.is_ready=False, Tier 1 恒空手, 评出来的是假基线。

5 指标:
  recall@5   — 非 expect_empty query 中 top5 含 ≥1 相关结果的比例 (↑ 越高越好)
  MRR        — 首个相关结果排名倒数的平均 (↑)
  重复率     — top10 内近重复条目占比, normalized difflib ratio ≥ 阈值 (↓ 越低越好)
  假阳性率   — expect_empty query 的返回条目占满编比例 (↓)
  泄漏率     — 全部结果中命中 leak_markers 的条目占比 (↓)

用法:
  cd backend && .venv/bin/python scripts/run_memory_retrieval_regression.py            # 跑评测+门禁比较
  .venv/bin/python scripts/run_memory_retrieval_regression.py --update-baseline        # 固化/更新基线
  .venv/bin/python scripts/run_memory_retrieval_regression.py --json                   # 额外输出机器可读 JSON

exit code: 0 = 通过 / 1 = 指标回退 / 2 = 环境不可用 (backend 未起, 不算回退)
"""

import argparse
import difflib
import json
import statistics
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
BACKEND_URL = "http://localhost:8011"
SEARCH_ENDPOINT = f"{BACKEND_URL}/mcp/tools/search_memories"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/v1/health"

GOLD_SET = BACKEND_DIR / "tests" / "regression" / "memory_gold_set.yaml"
SHADOW_SET = BACKEND_DIR / "tests" / "regression" / "memory_gold_set_shadow.yaml"
BASELINE_FILE = BACKEND_DIR / "tests" / "fixtures" / "regression_baselines" / "memory_retrieval_baseline.json"
LAST_RUN_FILE = BASELINE_FILE.with_name("memory_retrieval_last_run.json")
# P1 (终验对账裁决 2): 基线版本化 — 每次重固化归档旧基线 + 原因, churn 可审计
BASELINE_HISTORY = BASELINE_FILE.with_name("memory_retrieval_baseline_history.jsonl")
JUDGE_REVIEW = BASELINE_FILE.with_name("memory_retrieval_judge_review.jsonl")
QWEN_URL = "http://127.0.0.1:12341/v1/chat/completions"

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

# 指标方向: True = 越高越好 (回退=下降), False = 越低越好 (回退=上升)
METRIC_DIRECTIONS = {
    "recall_at_5": True,
    "mrr": True,
    "duplicate_rate": False,
    "false_positive_rate": False,
    "leak_rate": False,
}


def norm_text(text: str) -> str:
    """NFKC 归一 + casefold + 去空白 — 近重复与子串匹配共用。"""
    return "".join(unicodedata.normalize("NFKC", text).casefold().split())


def result_text(result: dict) -> str:
    """拼接结果对象的可检字段 (接口当前回 fact/source/timestamp, 兜住未来字段)。"""
    fields = (
        "fact",
        "content",
        "name",
        "summary",
        "concept",
        "episode_type",
        "node_id",
    )
    return " ".join(str(result.get(f, "")) for f in fields if result.get(f))


def is_relevant(text_norm: str, expect_any: list) -> bool:
    return any(norm_text(e) in text_norm for e in expect_any)


def is_leaked(result: dict, text_norm: str, leak_markers: list, group_id: str) -> bool:
    if any(norm_text(m) in text_norm for m in leak_markers):
        return True
    # group_id 越界: 接口当前不回传 group_id (对抗审查标尺#8 已记账); 回传后此分支自动生效
    rg = str(result.get("group_id", "") or "")
    if rg and group_id and rg.replace("__", ":") != group_id.replace("__", ":"):
        return True
    return False


def check_backend_alive() -> bool:
    try:
        # trust_env=False: 本地回环不走系统代理 (代理劫持 localhost 会误报环境不可用)
        resp = httpx.get(HEALTH_ENDPOINT, timeout=5, trust_env=False)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


def run_queries(gold: dict) -> dict:
    cfg = gold["config"]
    group_id = cfg.get("group_id")  # null = 服务端 default_vault_group_id() 推导 (与生产一致)
    max_results = int(cfg.get("max_results", 10))
    leak_markers = cfg.get("leak_markers", [])
    dup_ratio = float(cfg.get("duplicate_ratio", 0.92))

    per_query = []
    latencies = []
    total_items = leaked_items = dup_items = 0
    fp_returned = fp_capacity = 0
    recall_hits = recall_total = 0
    rr_values = []

    with httpx.Client(timeout=60, trust_env=False) as client:
        for q in gold["queries"]:
            payload = {"query": q["query"], "max_results": max_results}
            if group_id:
                payload["group_id"] = group_id
            t0 = time.perf_counter()
            try:
                resp = client.post(SEARCH_ENDPOINT, json=payload)
                resp.raise_for_status()
                results = resp.json().get("results", [])
            except (
                httpx.HTTPError,
                ValueError,
            ) as exc:  # 单条失败不炸全场, 计 0 分并入报告
                results = []
                print(f"  {RED}⚠ {q['id']} 检索异常: {exc}{RESET}")
            dt = time.perf_counter() - t0
            latencies.append(dt)

            texts_norm = [norm_text(result_text(r)) for r in results]
            total_items += len(results)

            # 泄漏 (全部 query 参与)
            q_leaks = sum(1 for r, tn in zip(results, texts_norm) if is_leaked(r, tn, leak_markers, group_id or ""))
            leaked_items += q_leaks

            # 近重复 (与更早条目 ratio ≥ 阈值)
            q_dups = 0
            for i, tn in enumerate(texts_norm):
                for prev in texts_norm[:i]:
                    if tn and prev and difflib.SequenceMatcher(None, tn, prev).ratio() >= dup_ratio:
                        q_dups += 1
                        break
            dup_items += q_dups

            entry = {
                "id": q["id"],
                "query": q["query"],
                "category": q.get("category", ""),
                "returned": len(results),
                "latency_s": round(dt, 3),
                "leaked": q_leaks,
                "duplicates": q_dups,
            }

            if q.get("expect_empty"):
                # 假阳性: 库内不存在的主题, 返回条目全算假阳性
                # (当前无相关度地板, R2 落地后可升级为分数判定)
                fp_returned += len(results)
                fp_capacity += max_results
                entry["false_positives"] = len(results)
            else:
                relevant_flags = [is_relevant(tn, q["expect_any"]) for tn in texts_norm]
                first_rank = next((i + 1 for i, f in enumerate(relevant_flags) if f), None)
                recall_total += 1
                if any(relevant_flags[:5]):
                    recall_hits += 1
                else:
                    # P1 LLM-judge 备料: 词面 miss 的 top5 原文带出, 供二段判分
                    entry["top5_texts"] = [result_text(r)[:300] for r in results[:5]]
                rr_values.append(1.0 / first_rank if first_rank else 0.0)
                entry["relevant_in_top5"] = sum(relevant_flags[:5])
                entry["first_relevant_rank"] = first_rank

            per_query.append(entry)

    metrics = {
        "recall_at_5": round(recall_hits / recall_total, 4) if recall_total else 0.0,
        "mrr": round(statistics.mean(rr_values), 4) if rr_values else 0.0,
        "duplicate_rate": round(dup_items / total_items, 4) if total_items else 0.0,
        "false_positive_rate": round(fp_returned / fp_capacity, 4) if fp_capacity else 0.0,
        "leak_rate": round(leaked_items / total_items, 4) if total_items else 0.0,
    }
    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": SEARCH_ENDPOINT,
        "group_id": group_id or "(server default: vault:canvas_vault)",
        "query_count": len(gold["queries"]),
        "metrics": metrics,
        "latency": {
            "median_s": round(statistics.median(latencies), 3),
            "max_s": round(max(latencies), 3),
        },
        "per_query": per_query,
    }


def _llm_judge_relevant(query: str, texts: list) -> bool:
    """P1 三段式判分第二段: 本地 Qwen 二值相关性判定 (ARES 思路: judge 辅助,
    翻案落 review 文件供人工抽检, 不直接替代词面口径的门禁真值)。"""
    prompt = (
        f"问题：{query}\n候选材料：\n"
        + "\n".join(f"- {t}" for t in texts)
        + "\n\n以上材料中是否至少有一条与问题直接相关？只答 yes 或 no。"
    )
    resp = httpx.post(
        QWEN_URL,
        json={
            "model": "qwen",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8,
            "temperature": 0,
        },
        timeout=30,
        trust_env=False,
    )
    resp.raise_for_status()
    answer = resp.json()["choices"][0]["message"]["content"].strip().lower()
    return answer.startswith("y")


def judge_misses(report: dict) -> None:
    """对词面 miss 的 query 跑 LLM-judge, 产出 recall_at_5_judged 参考指标。

    参考指标不进门禁 (METRIC_DIRECTIONS 不含) — judge 提供「词面口径低估了
    多少」的透明度; 翻案明细追加 judge_review.jsonl 供人工抽检校准。
    12341 不可达 → 整段跳过, recall_at_5_judged = None。
    """
    misses = [e for e in report["per_query"] if e.get("first_relevant_rank") is None and e.get("top5_texts")]
    lexical_hits = sum(
        1 for e in report["per_query"] if "first_relevant_rank" in e and e.get("relevant_in_top5", 0) > 0
    )
    total = sum(1 for e in report["per_query"] if "first_relevant_rank" in e)
    flips = []
    try:
        for e in misses:
            if _llm_judge_relevant(e["query"], e["top5_texts"]):
                flips.append({"id": e["id"], "query": e["query"], "top5": e["top5_texts"]})
    except httpx.HTTPError:
        report["metrics"]["recall_at_5_judged"] = None
        print(f"{YELLOW}⚠ LLM-judge 跳过 (12341 不可达){RESET}")
        return
    report["metrics"]["recall_at_5_judged"] = round((lexical_hits + len(flips)) / total, 4) if total else 0.0
    report["judge_flips"] = [f["id"] for f in flips]
    if flips:
        with open(JUDGE_REVIEW, "a", encoding="utf-8") as f:
            for flip in flips:
                f.write(
                    json.dumps(
                        {"reviewed": False, "run_at": report["run_at"], **flip},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        print(
            f"{YELLOW}ℹ judge 翻案 {len(flips)} 条 (词面 miss 但 judge 判相关) — "
            f"已落 {JUDGE_REVIEW.name} 供人工抽检{RESET}"
        )


def compare_with_baseline(report: dict, baseline: dict, tolerance: float) -> list:
    regressions = []
    base_metrics = baseline.get("metrics", {})
    for name, higher_is_better in METRIC_DIRECTIONS.items():
        cur = report["metrics"].get(name)
        base = base_metrics.get(name)
        if cur is None or base is None:
            continue
        delta = cur - base
        if higher_is_better and delta < -tolerance:
            regressions.append(f"{name}: {base} → {cur} (回退 {delta:+.4f}, 容差 -{tolerance})")
        elif not higher_is_better and delta > tolerance:
            regressions.append(f"{name}: {base} → {cur} (恶化 {delta:+.4f}, 容差 +{tolerance})")
    return regressions


def print_report(report: dict) -> None:
    m = report["metrics"]
    print("═" * 64)
    print(f"记忆检索回归 — {report['query_count']} query @ {report['group_id']}")
    print(f"  recall@5      = {m['recall_at_5']:.2%}")
    print(f"  MRR           = {m['mrr']:.4f}")
    print(f"  重复率        = {m['duplicate_rate']:.2%}")
    print(f"  假阳性率      = {m['false_positive_rate']:.2%}")
    print(f"  泄漏率        = {m['leak_rate']:.2%}")
    if m.get("recall_at_5_judged") is not None:
        print(f"  recall@5(judge参考) = {m['recall_at_5_judged']:.2%}  ← 词面+judge翻案, 不进门禁")
    print(f"  延迟          = 中位 {report['latency']['median_s']}s / 最大 {report['latency']['max_s']}s")
    misses = [e for e in report["per_query"] if "first_relevant_rank" in e and e["first_relevant_rank"] is None]
    if misses:
        print(f"  top10 无相关的 query ({len(misses)}):")
        for e in misses:
            print(f"    {e['id']} [{e['category']}] {e['query']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="记忆检索 gold set 回归门禁")
    parser.add_argument("--update-baseline", action="store_true", help="固化当前指标为基线")
    parser.add_argument(
        "--reason",
        default="",
        help="P1: 重固化基线的原因 (与 --update-baseline 连用时必填, 落 history 留痕)",
    )
    parser.add_argument(
        "--shadow",
        action="store_true",
        help="P1: 跑 exploration shadow 集合 (只报告不门禁不动基线)",
    )
    parser.add_argument("--no-judge", action="store_true", help="跳过 LLM-judge 二段判分")
    parser.add_argument("--json", action="store_true", help="stdout 追加机器可读 JSON")
    args = parser.parse_args()

    if args.update_baseline and not args.reason:
        print(f"{RED}⛔ --update-baseline 必须带 --reason (基线 churn 可审计){RESET}")
        return 2

    if not check_backend_alive():
        print(
            f"{RED}⛔ backend 不可达 ({HEALTH_ENDPOINT}) — 先起 backend 再跑门禁。"
            f"环境不可用 ≠ 指标回退, exit 2。{RESET}"
        )
        return 2

    gold_path = SHADOW_SET if args.shadow else GOLD_SET
    gold = yaml.safe_load(gold_path.read_text(encoding="utf-8"))
    tolerance = float(gold["config"].get("tolerance", 0.02))
    if args.shadow and not gold.get("queries"):
        print("shadow 集合为空 — 无失败案例待探索, 直接通过")
        return 0

    report = run_queries(gold)
    report["gold_set_version"] = gold["config"].get("version", 0)
    if not args.no_judge:
        judge_misses(report)
    print_report(report)

    if args.shadow:
        print("(shadow 模式 — 只报告, 不门禁不动基线)")
        return 0

    LAST_RUN_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_RUN_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(
            json.dumps(
                {"metrics": report["metrics"], "latency": report["latency"]},
                ensure_ascii=False,
            )
        )

    if args.update_baseline or not BASELINE_FILE.exists():
        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # P1 (终验对账裁决 2): 重固化归档旧基线 — churn 可审计, 不许静默挪门柱
        if BASELINE_FILE.exists():
            old = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
            with open(BASELINE_HISTORY, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "archived_at": report["run_at"],
                            "reason": args.reason or "(initial)",
                            "gold_set_version": report.get("gold_set_version"),
                            "old_metrics": old.get("metrics"),
                            "new_metrics": report["metrics"],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        BASELINE_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"{YELLOW}📌 基线已固化 → {BASELINE_FILE.relative_to(BACKEND_DIR)}"
            f" (原因: {args.reason or 'initial'}, 旧基线已归档 history){RESET}"
        )
        return 0

    baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    regressions = compare_with_baseline(report, baseline, tolerance)
    if regressions:
        print(f"{RED}❌ 门禁不通过 — {len(regressions)} 项指标回退:{RESET}")
        for r in regressions:
            print(f"  {RED}{r}{RESET}")
        return 1
    print(f"{GREEN}✅ 门禁通过 — 5 指标均未回退 (基线 {baseline.get('run_at', '?')}){RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
