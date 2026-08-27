#!/usr/bin/env python
"""RAG-S2 评测门禁 (RAG-S2-2026-08-09): vault 检索 gold set 回归。

对 tests/regression/vault_gold_set.yaml 的 60 条 query 跑三层评测, 产出排序/
交付指标并与固化基线比较 — 任一指标回退超容差即 fail。阶段 2 每个改动批次
(chunk 策略 / 权重 / dedup / rerank) 完成必跑, 作为强制验收挡板。

三层 (fork 自 run_memory_retrieval_regression.py, 结构与纪律同源):
  Tier R 排序层 — 进程内直调 search_supplementary, 截断参数全关
                  (min_relevance=0 / elbow 关 / hard_cap=top_k), 评未截断排序:
                  hit@10 (教科书 hit rate, 分母=query 数; 曾误名 recall@10,
                  G4-12 正名) / MRR / nDCG@10 / contamination@10 /
                  polluted_query_rate / handwritten_share@10 / duplicate_rate
  Tier D 交付层 — 同函数生产参数 (0.50/0.25/10), 评用户实际看到什么:
                  delivery_rate / delivered_contamination / false_positive_rate
  Tier H hook 冒烟 — 5 条 HTTP probe 守护 enrich-hook 护栏
                  (短句跳过/斜杠跳过/系统词黑名单/exam 前缀), backend 不在线
                  时跳过该层 (不算回退)。

与 memory 金集的关键差异: vault 链无 episode_worker lifespan 依赖 → 直调
服务层评测 (快且免 HTTP 噪声); 但必须手动设 vault ContextVar, 否则
resolve_table_name 落错表 = 假基线。

硬禁断言: config.forbidden (检验白板/exam_board/标记串) 出现在任何结果中
→ 直接 exit 1, 不进百分比 (信息隔离铁律 HARD-ISO)。

用法:
  cd backend && .venv/bin/python scripts/run_vault_retrieval_regression.py
  ... --update-baseline --reason "开工基线"      # 固化基线 (churn 留痕)
  ... --shadow                                    # exploration 集合只报告
  ... --json                                      # 追加机器可读 JSON

exit: 0 = 通过 / 1 = 指标回退或硬禁违规 / 2 = 环境不可用
"""

import argparse
import asyncio
import difflib
import fnmatch
import json
import math
import statistics
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "lib"))

GOLD_SET = BACKEND_DIR / "tests" / "regression" / "vault_gold_set.yaml"
SHADOW_SET = BACKEND_DIR / "tests" / "regression" / "vault_gold_set_shadow.yaml"
BASELINE_FILE = BACKEND_DIR / "tests" / "fixtures" / "regression_baselines" / "vault_retrieval_baseline.json"
LAST_RUN_FILE = BASELINE_FILE.with_name("vault_retrieval_last_run.json")
BASELINE_HISTORY = BASELINE_FILE.with_name("vault_retrieval_baseline_history.jsonl")

# ⚠️ 必须在 backend 容器内执行 (docker exec canvas-learning-system-backend
# python scripts/run_vault_retrieval_regression.py ...) — 生产 LanceDB 在
# named volume (容器内 /lancedb), 宿主进程解析到空的相对路径 data/lancedb,
# 评出来的是假基线 (2026-08-09 首跑实锤: 宿主 tables=[] 全零)。
import os

_BACKEND_URL = os.environ.get("VAULT_EVAL_BACKEND_URL", "http://localhost:8001")
HOOK_ENDPOINT = f"{_BACKEND_URL}/api/v1/chat/rag/enrich-hook"
HEALTH_ENDPOINT = f"{_BACKEND_URL}/api/v1/health"

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

# 指标方向: True = 越高越好, False = 越低越好
METRIC_DIRECTIONS = {
    "hit_at_10": True,
    "mrr": True,
    "ndcg_at_10": True,
    "handwritten_share_at_10": True,
    "contamination_at_10": False,
    "polluted_query_rate": False,
    "duplicate_rate": False,
    "delivery_rate": True,
    "delivered_contamination_rate": False,
    "false_positive_rate": False,
}

# G4-12 名实修正 (2026-08-27, 与 run_memory_retrieval_regression.py 同批):
# recall_at_10 是误名 (分母为 query 数 = hit rate), 新键 hit_at_10。
# 旧 baseline 用别名兼容读取, 防 compare_with_baseline 缺键 continue 静默跳过。
LEGACY_METRIC_ALIASES = {
    "hit_at_10": "recall_at_10",
}


def resolve_baseline_metric(base_metrics: dict, name: str):
    """按新键取 baseline 指标, 未迁移的旧 baseline 回落 legacy 别名."""
    if name in base_metrics:
        return base_metrics[name]
    legacy = LEGACY_METRIC_ALIASES.get(name)
    return base_metrics.get(legacy) if legacy else None


K = 10  # 排序层评测深度


def norm_text(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", str(text)).casefold().split())


def material_text(m: dict) -> str:
    return " ".join(str(m.get(f, "")) for f in ("source_path", "heading", "snippet", "wikilink"))


def grade_of(m: dict, expects: list) -> int:
    """结果对 expect_hit 的分级: file+contains 全中→声明 grade;
    仅 file 中→min(grade,2) (段落不确定)。取所有匹配的最高值。"""
    path_n = norm_text(m.get("source_path", ""))
    snip_n = norm_text(material_text(m))
    best = 0
    for e in expects:
        if norm_text(e["file"]) not in path_n:
            continue
        g = int(e.get("grade", 2))
        if e.get("contains") and norm_text(e["contains"]) not in snip_n:
            g = min(g, 2)
        best = max(best, g)
    return best


def is_contaminated(m: dict, cfg_contam: dict) -> bool:
    path = str(m.get("source_path", ""))
    if any(fnmatch.fnmatch(path, g) or path.startswith(g.rstrip("*")) for g in cfg_contam.get("path_globs", [])):
        return True
    return str(m.get("doc_type", "")) in set(cfg_contam.get("doc_types", []))


def forbidden_violations(m: dict, forb: dict) -> list:
    path = str(m.get("source_path", ""))
    out = []
    for g in forb.get("path_globs", []):
        if fnmatch.fnmatch(path, g) or path.startswith(g.rstrip("*")):
            out.append(f"path {path!r} 命中硬禁 glob {g!r}")
    if str(m.get("doc_type", "")) in set(forb.get("doc_types", [])):
        out.append(f"doc_type {m.get('doc_type')!r} 属硬禁类型 (path={path!r})")
    text_n = norm_text(material_text(m))
    for marker in forb.get("markers", []):
        if norm_text(marker) in text_n:
            out.append(f"命中硬禁标记 {marker!r} (path={path!r})")
    return out


def ndcg_at_k(grades: list, declared: list, k: int) -> float:
    """nDCG@k: gain=2^grade-1。IDCG 用金集声明的 grade 降序 (补 0)。"""
    dcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(grades[:k]))
    ideal = sorted((int(e.get("grade", 2)) for e in declared), reverse=True)
    idcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(ideal[:k]))
    return dcg / idcg if idcg > 0 else 0.0


async def _make_client():
    """写侧同款 lightweight 连接 (无 CPU 预载); embedding 走 Ollama。"""
    from agentic_rag.clients.lancedb_client import LanceDBClient
    from agentic_rag.config import LANCEDB_CONFIG

    client = LanceDBClient(db_path=LANCEDB_CONFIG["db_path"])
    if not client.connect_lightweight() or client._db is None:
        raise RuntimeError(f"LanceDB connect failed: {LANCEDB_CONFIG['db_path']}")
    return client


def _set_vault_context(vault_id: str) -> None:
    """⚠️ 直调必设 — 漏设则 resolve_table_name 落错表 = 假基线。"""
    from app.config import sanitize_vault_id
    from app.core.subject_config import build_vault_group_id, set_current_subject_id

    set_current_subject_id(build_vault_group_id(sanitize_vault_id(vault_id)))


async def run_tiers(gold: dict) -> dict:
    from app.services.supplementary_search_service import search_supplementary

    cfg = gold["config"]
    top_k = int(cfg.get("top_k", 20))
    contam_cfg = cfg.get("contamination", {})
    forb_cfg = cfg.get("forbidden", {})
    dup_ratio = float(cfg.get("duplicate_ratio", 0.92))
    delivery_cfg = cfg.get("delivery", {})

    _set_vault_context(str(cfg.get("vault_id", "canvas_vault")))
    client = await _make_client()

    per_query = []
    latencies = []
    hard_violations = []

    # Tier R 累计
    hit_at_10_hits = hit_at_10_total = 0
    rr_values, ndcg_values = [], []
    contam_hits = contam_slots = 0
    polluted_queries = 0
    handwritten = ranked_total = 0
    dup_items = dup_total = 0
    # Tier D 累计
    delivered_ok = delivery_total = 0
    delivered_contam = delivered_total_items = 0
    fp_returned = fp_capacity = 0
    top1_scores = []

    for q in gold["queries"]:
        qid = q["id"]
        expects = q.get("expect_hit", [])
        not_hits = q.get("expect_not_hit", [])
        empty_expected = bool(q.get("expect_empty"))

        # ── Tier R: 截断全关, 拿排序全表 ──
        t0 = time.perf_counter()
        try:
            r_res = await search_supplementary(
                q["query"],
                client,
                top_k_max=top_k,
                min_relevance=0.0,
                elbow_drop_threshold=1.01,  # >1 = 永不触发
                hard_cap=top_k,
            )
        except Exception as exc:
            print(f"  {RED}⚠ {qid} Tier-R 检索异常: {exc}{RESET}")
            r_res = {"materials": [], "degraded": True, "reason": "exception"}
        latencies.append(time.perf_counter() - t0)
        mats = r_res.get("materials", [])[:top_k]

        for m in mats:
            hard_violations.extend(f"[{qid}] {v}" for v in forbidden_violations(m, forb_cfg))

        entry = {
            "id": qid,
            "query_type": q.get("query_type", ""),
            "returned": len(mats),
        }

        # 近重复
        texts_n = [norm_text(material_text(m)) for m in mats]
        q_dups = 0
        for i, tn in enumerate(texts_n):
            for prev in texts_n[:i]:
                if tn and prev and difflib.SequenceMatcher(None, tn, prev).ratio() >= dup_ratio:
                    q_dups += 1
                    break
        dup_items += q_dups
        dup_total += len(mats)

        # handwritten share (全部 query 的 top-10 汇总)
        top10 = mats[:K]
        handwritten += sum(1 for m in top10 if str(m.get("source_path", "")).startswith("节点/"))
        ranked_total += len(top10)

        if not empty_expected and expects:
            # nDCG 修正 (T2 实测抓获 >1.0): 声明是文件级、结果是 chunk 级 —
            # 同文件多 chunk 重复计 gain 会使 DCG > IDCG。per-expect 去重:
            # 每条 expect 只有首个匹配的结果计 gain, 后续同源命中记 0
            # (hit@10/MRR 用原始逐结果 flags, 不受影响)。
            grades = []
            used_expects: set = set()
            for m in mats:
                path_n = norm_text(m.get("source_path", ""))
                snip_n = norm_text(material_text(m))
                best_g, best_i = 0, None
                for i, e in enumerate(expects):
                    if i in used_expects or norm_text(e["file"]) not in path_n:
                        continue
                    g = int(e.get("grade", 2))
                    if e.get("contains") and norm_text(e["contains"]) not in snip_n:
                        g = min(g, 2)
                    if g > best_g:
                        best_g, best_i = g, i
                if best_i is not None:
                    used_expects.add(best_i)
                grades.append(best_g)
            relevant = [g > 0 for g in grades]
            first = next((i + 1 for i, f in enumerate(relevant) if f), None)
            hit_at_10_total += 1
            if any(relevant[:K]):
                hit_at_10_hits += 1
            rr_values.append(1.0 / first if first else 0.0)
            ndcg_values.append(ndcg_at_k(grades, expects, K))
            entry["first_relevant_rank"] = first
            entry["ndcg"] = round(ndcg_values[-1], 3)
            if first is None:
                entry["top5_paths"] = [m.get("source_path", "") for m in mats[:5]]

        # 配额污染 (expect_not_hit)
        q_polluted = False
        for nh in not_hits:
            glob = nh.get("path_glob", "")
            allowed = int(nh.get("max_in_top_k", 0))
            n_hit = sum(
                1
                for m in top10
                if fnmatch.fnmatch(str(m.get("source_path", "")), glob)
                or str(m.get("source_path", "")).startswith(glob.rstrip("*"))
            )
            contam_slots += len(top10)
            over = max(0, n_hit - allowed)
            contam_hits += over
            if over:
                q_polluted = True
                entry.setdefault("pollution", []).append(f"{glob}: {n_hit}/{allowed}")
        # 全局污染口径 (contamination cfg) 对无显式 not_hit 的 query 也计
        if not not_hits and not empty_expected:
            n_c = sum(1 for m in top10 if is_contaminated(m, contam_cfg))
            # 无显式配额时不计入 contamination 指标 (raw 可能是正解),
            # 但记录供报告观察
            if n_c:
                entry["contam_note"] = n_c
        if q_polluted:
            polluted_queries += 1

        # ── Tier D: 生产参数 ──
        try:
            d_res = await search_supplementary(
                q["query"],
                client,
                top_k_max=int(delivery_cfg.get("hard_cap", 10)) + 5,
                min_relevance=float(delivery_cfg.get("min_relevance", 0.50)),
                elbow_drop_threshold=float(delivery_cfg.get("elbow_drop_threshold", 0.25)),
                hard_cap=int(delivery_cfg.get("hard_cap", 10)),
            )
        except Exception as exc:
            print(f"  {RED}⚠ {qid} Tier-D 检索异常: {exc}{RESET}")
            d_res = {"materials": []}
        d_mats = d_res.get("materials", [])
        for m in d_mats:
            hard_violations.extend(f"[{qid}/D] {v}" for v in forbidden_violations(m, forb_cfg))

        if empty_expected:
            fp_returned += len(d_mats)
            fp_capacity += int(delivery_cfg.get("hard_cap", 10))
            entry["delivered_false_positives"] = len(d_mats)
        else:
            delivery_total += 1
            d_grades = [grade_of(m, expects) for m in d_mats] if expects else []
            if any(g > 0 for g in d_grades):
                delivered_ok += 1
            entry["delivered"] = len(d_mats)
            if d_mats:
                top1_scores.append(float(d_mats[0].get("score", 0.0)))
            delivered_total_items += len(d_mats)
            delivered_contam += sum(1 for m in d_mats if is_contaminated(m, contam_cfg))

        per_query.append(entry)

    metrics = {
        "hit_at_10": round(hit_at_10_hits / hit_at_10_total, 4) if hit_at_10_total else 0.0,
        "mrr": round(statistics.mean(rr_values), 4) if rr_values else 0.0,
        "ndcg_at_10": round(statistics.mean(ndcg_values), 4) if ndcg_values else 0.0,
        "contamination_at_10": round(contam_hits / contam_slots, 4) if contam_slots else 0.0,
        "polluted_query_rate": round(polluted_queries / len(gold["queries"]), 4),
        "handwritten_share_at_10": round(handwritten / ranked_total, 4) if ranked_total else 0.0,
        "duplicate_rate": round(dup_items / dup_total, 4) if dup_total else 0.0,
        "delivery_rate": round(delivered_ok / delivery_total, 4) if delivery_total else 0.0,
        "delivered_contamination_rate": round(delivered_contam / delivered_total_items, 4)
        if delivered_total_items
        else 0.0,
        "false_positive_rate": round(fp_returned / fp_capacity, 4) if fp_capacity else 0.0,
    }
    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "mode": "in-process search_supplementary (Tier R + D)",
        "query_count": len(gold["queries"]),
        "metrics": metrics,
        "top1_score_distribution": {
            "median": round(statistics.median(top1_scores), 3) if top1_scores else None,
            "min": round(min(top1_scores), 3) if top1_scores else None,
        },
        "latency": {
            "median_s": round(statistics.median(latencies), 3),
            "max_s": round(max(latencies), 3),
        },
        "hard_violations": hard_violations,
        "per_query": per_query,
    }


def run_hook_smoke() -> dict:
    """Tier H: 5 条 HTTP probe 守护 hook 护栏 (2026-08-09 F-1 误判教训:
    黑名单词/斜杠/短句的跳过行为若被误改, 用户测试会集体误判)。"""
    import httpx

    probes = [
        ("normal", "特征值的定义是什么", "may_inject"),
        ("too_short", "嗯", "must_skip"),
        ("blacklist_word", "刚才那轮 hook 注入了什么材料", "must_skip"),
        ("slash_prefix", "/chat-with-context 特征值", "must_skip"),
        ("exam_prefix", "/start-exam-board from 特征值与特征向量", "must_skip"),
    ]
    results = {}
    headers = {}
    internal_key = os.environ.get("INTERNAL_API_KEY", "")
    if internal_key:
        headers["X-CLS-Internal-Key"] = internal_key
    try:
        with httpx.Client(timeout=15, trust_env=False, headers=headers) as client:
            for name, prompt, expect in probes:
                resp = client.post(
                    HOOK_ENDPOINT,
                    json={"prompt": prompt, "cwd": str(BACKEND_DIR.parent / "canvas-vault")},
                )
                ctx = ""
                if resp.status_code == 200:
                    ctx = (resp.json().get("hookSpecificOutput") or {}).get("additionalContext", "") or ""
                injected = "supplementary_materials" in ctx
                ok = (not injected) if expect == "must_skip" else resp.status_code == 200
                results[name] = {"status": resp.status_code, "injected": injected, "ok": ok}
    except httpx.HTTPError as exc:
        return {"skipped": True, "reason": f"backend 不可达: {exc}"}
    return results


def compare_with_baseline(report: dict, baseline: dict, tolerance: float) -> list:
    regressions = []
    base = baseline.get("metrics", {})
    for name, higher in METRIC_DIRECTIONS.items():
        # G4-12: 旧 baseline (recall_* 键) 走别名解析, 防缺键静默跳过
        cur, b = report["metrics"].get(name), resolve_baseline_metric(base, name)
        if cur is None or b is None:
            continue
        delta = cur - b
        if higher and delta < -tolerance:
            regressions.append(f"{name}: {b} → {cur} (回退 {delta:+.4f})")
        elif not higher and delta > tolerance:
            regressions.append(f"{name}: {b} → {cur} (恶化 {delta:+.4f})")
    return regressions


def print_report(report: dict, hook: dict) -> None:
    m = report["metrics"]
    print("═" * 66)
    print(f"vault 检索回归 — {report['query_count']} query · {report['mode']}")
    print(f"  [R] hit@10             = {m['hit_at_10']:.2%}")
    print(f"  [R] MRR                = {m['mrr']:.4f}")
    print(f"  [R] nDCG@10            = {m['ndcg_at_10']:.4f}")
    print(f"  [R] 污染@10 (配额超额) = {m['contamination_at_10']:.2%}")
    print(f"  [R] 被污染 query 率    = {m['polluted_query_rate']:.2%}")
    print(f"  [R] 手写占比@10        = {m['handwritten_share_at_10']:.2%}")
    print(f"  [R] 近重复率           = {m['duplicate_rate']:.2%}")
    print(f"  [D] 交付命中率         = {m['delivery_rate']:.2%}")
    print(f"  [D] 交付污染率         = {m['delivered_contamination_rate']:.2%}")
    print(f"  [D] 假阳性率           = {m['false_positive_rate']:.2%}")
    print(f"  top1 score 中位 = {report['top1_score_distribution']['median']}")
    print(f"  延迟 中位 {report['latency']['median_s']}s / 最大 {report['latency']['max_s']}s")
    if isinstance(hook, dict) and hook.get("skipped"):
        print(f"  [H] hook 冒烟: {YELLOW}跳过 ({hook['reason']}){RESET}")
    elif hook:
        bad = [k for k, v in hook.items() if not v.get("ok")]
        state = f"{GREEN}5/5 护栏正常{RESET}" if not bad else f"{RED}护栏异常: {bad}{RESET}"
        print(f"  [H] hook 冒烟: {state}")
    misses = [e for e in report["per_query"] if e.get("first_relevant_rank") is None and "ndcg" in e]
    if misses:
        print(f"  top{K} 无相关的 query ({len(misses)}):")
        for e in misses:
            print(f"    {e['id']} [{e['query_type']}] top5={e.get('top5_paths', [])[:3]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="vault 检索 gold set 回归门禁 (RAG-S2)")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--reason", default="")
    parser.add_argument("--shadow", action="store_true")
    parser.add_argument("--no-hook", action="store_true", help="跳过 Tier H HTTP 冒烟")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.update_baseline and not args.reason:
        print(f"{RED}⛔ --update-baseline 必须带 --reason{RESET}")
        return 2

    gold_path = SHADOW_SET if args.shadow else GOLD_SET
    gold = yaml.safe_load(gold_path.read_text(encoding="utf-8"))
    tolerance = float(gold["config"].get("tolerance", 0.02))
    if args.shadow and not gold.get("queries"):
        print("shadow 集合为空 — 直接通过")
        return 0

    try:
        report = asyncio.run(run_tiers(gold))
    except Exception as exc:
        print(f"{RED}⛔ 评测环境异常 (非指标回退): {exc}{RESET}")
        return 2

    # 空索引哨兵: 全部 query 零返回 = 环境错误 (多半是在宿主跑, 摸不到
    # named volume), 绝不能作为基线/回退判定
    if all(e.get("returned", 0) == 0 for e in report["per_query"]):
        print(
            f"{RED}⛔ 全部 query 零返回 — 索引不可见。请在 backend 容器内运行:\n"
            f"  docker exec canvas-learning-system-backend python "
            f"scripts/run_vault_retrieval_regression.py{RESET}"
        )
        return 2
    report["gold_set_version"] = gold["config"].get("version", 0)

    hook = {} if args.no_hook else run_hook_smoke()
    report["hook_smoke"] = hook
    print_report(report, hook)

    if report["hard_violations"]:
        print(f"{RED}⛔ 硬禁违规 (信息隔离铁律) {len(report['hard_violations'])} 条:{RESET}")
        for v in report["hard_violations"][:10]:
            print(f"  {RED}{v}{RESET}")
        return 1
    if (
        isinstance(hook, dict)
        and not hook.get("skipped")
        and any(not v.get("ok") for v in hook.values() if isinstance(v, dict))
    ):
        print(f"{RED}⛔ hook 护栏异常{RESET}")
        return 1

    if args.shadow:
        print("(shadow 模式 — 只报告)")
        return 0

    LAST_RUN_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_RUN_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps({"metrics": report["metrics"]}, ensure_ascii=False))

    if args.update_baseline or not BASELINE_FILE.exists():
        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
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
        print(f"{YELLOW}📌 基线已固化 (原因: {args.reason or 'initial'}){RESET}")
        return 0

    baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    regressions = compare_with_baseline(report, baseline, tolerance)
    if regressions:
        print(f"{RED}❌ 门禁不通过 — {len(regressions)} 项回退:{RESET}")
        for r in regressions:
            print(f"  {RED}{r}{RESET}")
        return 1
    print(f"{GREEN}✅ 门禁通过 (基线 {baseline.get('run_at', '?')}){RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
