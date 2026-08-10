#!/usr/bin/env python
"""RAG-S2.5 金集验收器: Board Manifest 结构完整性契约 (P=R=1.00 硬门槛)。

与检索金集 (run_vault_retrieval_regression.py, 姿势同源) 的本质差异:
语义检索允许近似 (容差比较), 结构检索是**完整性契约** — official 区全部
走硬禁通道: 集合/字段相等, 差一个即 exit 1, 无 tolerance。

检查组 (tests/regression/board_manifest_gold_set.yaml, T0 签字后封版):
  G1 板成员 ×6 / G2 孤儿 ×1 / G3 dual_source_gap ×3 / G4 字段投影 ×10
  (含 pick_hint 与 vault decay_beta 真相源 1e-9 复算 + exam 白名单键集) /
  G5 exam 历史 ×3 / G6 泄漏禁项 ×8 (禁串 ×5 + 任意深度禁键 + 合成极端节点 ×2)

用法 (以容器内为准, 与检索金集姿势统一; manifest 纯文件读宿主也可跑):
  docker exec canvas-learning-system-backend \\
      python scripts/run_board_manifest_regression.py
  ... --vault /path/to/vault               # 覆盖 CANVAS_BASE_PATH
  ... --update-baseline --reason "封版"    # 固化基线 (churn 留痕)
  ... --shadow                             # shadow 分区只报告不判分
  ... --json                               # 追加机器可读 JSON

exit: 0 = 全绿 / 1 = 任一硬禁违规或金集缩水 / 2 = 环境不可用
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

GOLD_SET = BACKEND_DIR / "tests" / "regression" / "board_manifest_gold_set.yaml"
BASELINE_FILE = BACKEND_DIR / "tests" / "fixtures" / "regression_baselines" / "board_manifest_baseline.json"
LAST_RUN_FILE = BASELINE_FILE.with_name("board_manifest_last_run.json")
BASELINE_HISTORY = BASELINE_FILE.with_name("board_manifest_baseline_history.jsonl")

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def _all_keys(obj) -> set:
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            keys |= _all_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            keys |= _all_keys(item)
    return keys


def _iter_nodes(manifest: dict):
    yield from manifest.get("nodes") or []


class Checker:
    def __init__(self) -> None:
        self.results: list[dict] = []

    def add(self, check_id: str, ok: bool, detail: str = "") -> None:
        self.results.append({"check": check_id, "ok": bool(ok), "detail": detail})
        mark = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        line = f"  {mark} {check_id}"
        if detail and not ok:
            line += f" — {detail}"
        print(line)

    @property
    def failed(self) -> list[dict]:
        return [r for r in self.results if not r["ok"]]


def build_all(vault: Path) -> dict:
    """真 vault 一次扫描 → 各板 study/exam manifest + 列板。"""
    from app.models.board_manifest import project_manifest
    from app.services.board_manifest_service import build_manifest

    listing = build_manifest(vault)
    out = {"listing": listing, "boards": {}}
    for b in listing["boards"]:
        bid = b["board_id"]
        raw = build_manifest(vault, board_id=bid)
        out["boards"][bid] = {
            "raw": raw,
            "study": project_manifest(raw, "study").model_dump(),
            "exam": project_manifest(raw, "exam").model_dump(),
        }
    return out


# ── G1-G5 ──


def check_g1(c: Checker, gold: dict, data: dict) -> None:
    for case in gold["official"]["g1_membership"]:
        bid = case["board_id"]
        board = data["boards"].get(bid)
        if board is None:
            c.add(f"G1[{bid}]", False, "板不存在于 manifest")
            continue
        actual = sorted(n["node_id"] for n in _iter_nodes(board["study"]))
        expected = sorted(case["members"])
        c.add(f"G1[{bid}]", actual == expected, f"expected={expected} actual={actual}")


def check_g2(c: Checker, gold: dict, data: dict) -> None:
    actual = sorted(o["node_id"] for o in data["listing"]["orphans"])
    expected = sorted(gold["official"]["g2_orphans"])
    c.add("G2[orphans]", actual == expected, f"expected={expected} actual={actual}")


def check_g3(c: Checker, gold: dict, data: dict) -> None:
    for case in gold["official"]["g3_gap"]:
        bid = case["board_id"]
        gap = data["boards"][bid]["study"]["dual_source_gap"] or {}
        actual_co = sorted(e["node_id"] for e in gap.get("concepts_only", []))
        actual_fo = sorted(gap.get("frontmatter_only", []))
        ok = actual_co == sorted(case["concepts_only"]) and actual_fo == sorted(case["frontmatter_only"])
        c.add(f"G3[{bid}]", ok, f"concepts_only={actual_co} frontmatter_only={actual_fo}")


def _find_node(data: dict, bid: str, nid: str, view: str = "study") -> dict | None:
    for n in _iter_nodes(data["boards"][bid][view]):
        if n["node_id"] == nid:
            return n
    return None


def check_g4(c: Checker, gold: dict, data: dict, vault: Path) -> None:
    for case in gold["official"]["g4_fields"]:
        cid = f"G4[{case['check']}]"
        if case["check"] == "pick_hint_equivalence":
            _check_pick_equivalence(c, cid, case, data, vault)
            continue
        if case["check"] == "board_name_mismatch":
            ok, details = True, []
            for sub in case["cases"]:
                b = data["boards"][sub["board_id"]]["study"]["board"]
                good = b["board_name"] == sub["board_name"] and b["board_name_mismatch"] == sub["mismatch"]
                ok &= good
                details.append(f"{sub['board_id']}: name={b['board_name']}")
            c.add(cid, ok, "; ".join(details))
            continue
        if case["check"] == "exam_entry_keyset":
            node = _find_node(data, case["board_id"], case["node_id"], view="exam")
            actual = sorted(node.keys()) if node else []
            c.add(cid, actual == sorted(case["keys"]), f"actual={actual}")
            continue
        if case["check"] == "stub_and_limits":
            ok, details = True, []
            for sub in case["is_stub_cases"]:
                node = _find_node(data, sub["board_id"], sub["node_id"])
                good = node is not None and node["is_stub"] == sub["is_stub"]
                ok &= good
                if not good:
                    details.append(f"{sub['node_id']} is_stub≠{sub['is_stub']}")
            for bid, views in data["boards"].items():
                for n in _iter_nodes(views["exam"]):
                    for d in n["past_question_digests"]:
                        if d["digest"] and len(d["digest"]) > case["digest_max"]:
                            ok = False
                            details.append(f"digest 超限 {bid}/{n['node_id']}")
                    rel = n.get("relation") or {}
                    reason = rel.get("derived_reason")
                    if reason and len(reason) > case["derived_reason_max"]:
                        ok = False
                        details.append(f"derived_reason 超限 {bid}/{n['node_id']}")
            c.add(cid, ok, "; ".join(details))
            continue

        # 通用字段断言 (mastery/role/relation/attempt_count/前缀)
        node = _find_node(data, case["board_id"], case["node_id"])
        if node is None:
            c.add(cid, False, f"节点缺失: {case['node_id']}")
            continue
        ok, details = True, []
        if "mastery" in case:
            for k, v in case["mastery"].items():
                actual = node["mastery"].get(k)
                if actual != v and not (
                    isinstance(v, (int, float)) and isinstance(actual, (int, float)) and abs(actual - v) < 1e-9
                ):
                    ok = False
                    details.append(f"mastery.{k}: expected={v} actual={actual}")
        if "role" in case and node["role"] != case["role"]:
            ok = False
            details.append(f"role: expected={case['role']} actual={node['role']}")
        if "relation" in case:
            rel = node.get("relation") or {}
            for k, v in case["relation"].items():
                if rel.get(k) != v:
                    ok = False
                    details.append(f"relation.{k}: expected={v} actual={rel.get(k)}")
        if "derived_at_prefix" in case:
            da = (node.get("relation") or {}).get("derived_at") or ""
            if not da.startswith(case["derived_at_prefix"]):
                ok = False
                details.append(f"derived_at={da}")
        if "attempt_count" in case and node["attempt_count"] != case["attempt_count"]:
            ok = False
            details.append(f"attempt_count={node['attempt_count']}")
        if "last_examined_prefix" in case:
            le = node.get("last_examined") or ""
            if not le.startswith(case["last_examined_prefix"]):
                ok = False
                details.append(f"last_examined={le}")
        c.add(cid, ok, "; ".join(details))


def _check_pick_equivalence(c: Checker, cid: str, case: dict, data: dict, vault: Path) -> None:
    """pick_hint 与 vault decay_beta.py 真相源逐值复算 1e-9 (禁漂移)。"""
    scripts = vault / ".claude" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        import decay_beta as dbeta
    except ImportError as e:
        c.add(cid, False, f"decay_beta 真相源不可 import: {e}")
        return
    finally:
        sys.path.remove(str(scripts))

    node = _find_node(data, case["board_id"], case["node_id"])
    hint = node["pick_hint"]
    m = node["mastery"]
    if m["source"] == "beta":
        a, b = m["a"], m["b"]
    elif m["source"] in ("score_only", "legacy_v2"):
        a, b = dbeta.from_legacy(m["score"])
    else:
        a, b = dbeta.PRIOR_A, dbeta.PRIOR_B
    a_eff, b_eff = dbeta.effective(a, b, hint["days_idle"] or 0.0)
    ok = (
        abs(hint["mu"] - dbeta.mu(a_eff, b_eff)) < 1e-9
        and abs(hint["sigma"] - dbeta.sigma(a_eff, b_eff)) < 1e-9
        and abs(hint["pick_score"] - dbeta.pick_score(a_eff, b_eff)) < 1e-9
    )
    c.add(cid, ok, f"hint={hint}")


def check_g5(c: Checker, gold: dict, data: dict) -> None:
    for case in gold["official"]["g5_exam_history"]:
        bid = case["board_id"]
        actual = sorted(e["exam_board_id"] for e in data["boards"][bid]["study"]["exam_history"])
        expected = sorted(case["exam_board_ids"])
        c.add(f"G5[{bid}]", actual == expected, f"actual={actual}")
    # 正向对照 (Code-Review M8): qid 匹配若静默失效 (digest 全 None), 集合相等
    # 检查照样全绿 — 必须有一条非空断言兜底
    total_digests = sum(
        1
        for v in data["boards"].values()
        for n in _iter_nodes(v["exam"])
        for d in n["past_question_digests"]
        if d["digest"]
    )
    c.add("G5[digest 非空对照]", total_digests > 0, "全 vault 零 digest — qid 匹配可能静默失效")


# ── G6 泄漏禁项 ──


def check_g6(c: Checker, gold: dict, data: dict, vault: Path) -> None:
    cfg = gold["config"]
    # 正向对照 (Code-Review M8): 禁串必须仍存在于 vault 源文件, 否则用户改写
    # 文案后检查会静默腐烂成恒真 (扫描一个不存在的串永绿但零信息)
    vault_corpus = ""
    for sub in ("节点", "原白板", "检验白板"):
        d = vault / sub
        if d.is_dir():
            for p in d.glob("*.md"):
                try:
                    vault_corpus += p.read_text(encoding="utf-8")
                except OSError:
                    pass
    exam_json_all = json.dumps({bid: views["exam"] for bid, views in data["boards"].items()}, ensure_ascii=False)
    for s in cfg["forbidden_strings"]:
        present = s in vault_corpus
        clean = s not in exam_json_all
        detail = "禁串已不在 vault 源文件 (对照失效, 需换串)" if not present else "exam 视图 JSON 命中禁串"
        c.add(f"G6[禁串:{s[:18]}…]", present and clean, detail)
    leaked = _all_keys({bid: v["exam"] for bid, v in data["boards"].items()}) & set(cfg["forbidden_keys"])
    c.add("G6[禁键任意深度]", not leaked, f"泄漏键: {sorted(leaked)}")


def check_g6_synthetic(c: Checker, gold: dict) -> None:
    """合成极端节点: 批注者把定义塞进派生原因/tips → 只允许白名单槽位出现且截断。"""
    from app.models.board_manifest import project_manifest
    from app.services.board_manifest_service import build_manifest

    poison = gold["official"]["g6_leakage"]["synthetic_poison"]
    definition = poison["definition_text"]
    tips_text = poison["tips_text"]
    tmp = Path(tempfile.mkdtemp(prefix="manifest-poison-"))
    try:
        (tmp / "原白板").mkdir()
        (tmp / "节点").mkdir()
        (tmp / "检验白板").mkdir()
        (tmp / "原白板" / "毒板.md").write_text("---\ntype: whiteboard\n---\n# 毒板\n\n## Concepts\n", encoding="utf-8")
        long_reason = (definition * 20)[:600]  # >500, 验证硬截断
        (tmp / "节点" / "毒A.md").write_text(
            "---\n"
            'source_board: "[[原白板/毒板]]"\n'
            "relationships:\n"
            "  - type: extends\n"
            '    target: "[[种子]]"\n'
            f"    description: {long_reason}\n"
            "---\n正文。\n",
            encoding="utf-8",
        )
        (tmp / "节点" / "毒B.md").write_text(
            "---\n"
            'source_board: "[[原白板/毒板]]"\n'
            "tips:\n"
            f"  - text: {tips_text}\n"
            "    tag: question\n"
            "error_candidates:\n"
            f"  - misconception: {definition}\n"
            f"    correction: {definition}\n"
            "---\n正文。\n",
            encoding="utf-8",
        )
        raw = build_manifest(tmp, board_id="毒板")
        exam = project_manifest(raw, "exam").model_dump()
        exam_json = json.dumps(exam, ensure_ascii=False)

        node_a = next(n for n in exam["nodes"] if n["node_id"] == "毒A")
        reason = node_a["relation"]["derived_reason"]
        # Code-Review M7 修复原恒真条件: 断言改为「定义串在 exam JSON 中只允许
        # 出现在 reason 槽位内」— 挖掉该槽位后全 JSON 0 命中 (槽位内重复不限,
        # 因为毒文本本身就是 definition*20 拼接)
        json_without_reason = exam_json.replace(reason, "")
        c.add(
            "G6[合成A:定义只在白名单槽位且截断500]",
            len(reason) == 500 and definition[:30] in reason and definition[:30] not in json_without_reason,
            f"reason_len={len(reason)}",
        )
        c.add(
            "G6[合成B:tips/misconception 0 命中]",
            tips_text not in exam_json and definition not in json_without_reason,
            "毒 tips 或完整定义串出现在 exam JSON",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_g7(c: Checker, gold: dict, data: dict) -> None:
    """pick_rank 板内候选秩 (RAG-S2.6): rank==1 逐板定值 + 占位不入秩 + 秩稠密唯一。"""
    case = gold["official"]["g7_pick_rank"]
    ok, details = True, []

    for sub in case["rank_one"]:
        bid = sub["board_id"]
        winners = [
            n["node_id"]
            for n in _iter_nodes(data["boards"][bid]["exam"])
            if (n["pick_hint"] or {}).get("pick_rank") == 1
        ]
        if winners != [sub["node_id"]]:
            ok = False
            details.append(f"{bid}: rank1 expected=[{sub['node_id']}] actual={winners}")

    for bid, views in data["boards"].items():
        ranks = []
        for n in _iter_nodes(views["exam"]):
            rank = (n["pick_hint"] or {}).get("pick_rank")
            if case.get("stubs_never_ranked") and n["is_stub"] and rank is not None:
                ok = False
                details.append(f"{bid}/{n['node_id']}: 占位节点拿到 rank={rank}")
            if rank is not None:
                ranks.append(rank)
        if case.get("ranks_dense_and_unique") and sorted(ranks) != list(range(1, len(ranks) + 1)):
            ok = False
            details.append(f"{bid}: 秩非稠密唯一 {sorted(ranks)}")

    c.add("G7[pick_rank]", ok, "; ".join(details))


def check_g8(c: Checker, gold: dict, data: dict) -> None:
    """score_scale 量纲申报 (RAG-S2.6): 恒非空 + 推定必标 + 至少 1 条来自写侧真值。"""
    case = gold["official"]["g8_score_scale"]
    ok, details = True, []
    declared = 0
    for bid, views in data["boards"].items():
        for n in _iter_nodes(views["exam"]):
            for d in n["past_question_digests"]:
                scale = d.get("score_scale")
                if case.get("never_null") and not scale:
                    ok = False
                    details.append(f"{bid}/{n['node_id']}/{d['qid']}: 量纲缺失")
                    continue
                if scale == case["declared_value"]:
                    declared += 1
                elif case["inferred_suffix"] not in scale:
                    ok = False
                    details.append(f"{bid}/{n['node_id']}/{d['qid']}: 非真值却未标推定 {scale!r}")
    if declared < case["min_declared_count"]:
        ok = False
        details.append(f"写侧真值量纲仅 {declared} 条 (< {case['min_declared_count']}), 正向对照失效")
    c.add("G8[score_scale]", ok, "; ".join(details) or f"declared={declared}")


def run_shadow(gold: dict, data: dict) -> list[dict]:
    """shadow 分区: 只报告不判分 (观察面)。"""
    reports = []
    for case in gold.get("shadow") or []:
        if case["check"] == "doc_count_drift":
            drift = [
                f"{b['board_id']}: declared={b['doc_count_declared']} actual={b['member_count_actual']}"
                for b in data["listing"]["boards"]
                if b["doc_count_declared"] not in (None, b["member_count_actual"])
            ]
            reports.append({"check": "doc_count_drift", "report": drift})
        elif case["check"] == "stub_census":
            stubs = [
                f"{bid}/{n['node_id']}"
                for bid, v in data["boards"].items()
                for n in _iter_nodes(v["study"])
                if n["is_stub"]
            ]
            reports.append({"check": "stub_census", "report": {"count": len(stubs), "nodes": stubs}})
    return reports


def main() -> int:
    ap = argparse.ArgumentParser(description="Board Manifest 金集验收器")
    ap.add_argument("--vault", help="vault 根目录 (缺省 settings.CANVAS_BASE_PATH)")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--reason", help="--update-baseline 必填的 churn 理由")
    ap.add_argument("--shadow", action="store_true", help="附带 shadow 分区报告")
    ap.add_argument("--json", action="store_true", help="追加机器可读 JSON")
    args = ap.parse_args()

    if args.update_baseline and not args.reason:
        print(f"{RED}--update-baseline 必须带 --reason (churn 留痕纪律){RESET}")
        return 2

    if args.vault:
        vault = Path(args.vault)
    else:
        from app.config import get_settings

        vault = Path(get_settings().CANVAS_BASE_PATH)
    if not (vault / "节点").is_dir() or not (vault / "原白板").is_dir():
        print(f"{RED}环境不可用: vault 结构缺失 {vault}{RESET}")
        return 2

    gold = yaml.safe_load(GOLD_SET.read_text(encoding="utf-8"))
    print(f"Board Manifest 金集 v{gold['version']} — vault: {vault}")
    print(f"origin: {gold['origin']}\n")

    data = build_all(vault)
    c = Checker()
    check_g1(c, gold, data)
    check_g2(c, gold, data)
    check_g3(c, gold, data)
    check_g4(c, gold, data, vault)
    check_g5(c, gold, data)
    check_g6(c, gold, data, vault)
    check_g6_synthetic(c, gold)
    check_g7(c, gold, data)
    check_g8(c, gold, data)

    total, failed = len(c.results), len(c.failed)
    print(f"\n合计: {total - failed}/{total} 硬禁通过")

    shadow_reports = run_shadow(gold, data) if args.shadow else []
    for r in shadow_reports:
        print(f"{YELLOW}[shadow] {r['check']}: {r['report']}{RESET}")

    # 基线三件套: 硬禁通道本身无容差, 基线只防金集静默缩水 + churn 留痕
    now = datetime.now(timezone.utc).isoformat()
    summary = {
        "ts": now,
        "gold_version": gold["version"],
        "checks_total": total,
        "checks_failed": failed,
        "generation": data["listing"]["freshness"]["generation"],
    }
    LAST_RUN_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_RUN_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    baseline = None
    if BASELINE_FILE.exists():
        baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    if args.update_baseline:
        record = {**summary, "reason": args.reason}
        BASELINE_FILE.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        with BASELINE_HISTORY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"{YELLOW}基线已固化: {total} checks (reason: {args.reason}){RESET}")
    elif baseline and total < baseline["checks_total"]:
        print(
            f"{RED}金集缩水: baseline={baseline['checks_total']} 当前={total} — "
            f"需 --update-baseline --reason 显式留痕{RESET}"
        )
        failed += 1

    if args.json:
        print(json.dumps({**summary, "results": c.results, "shadow": shadow_reports}, ensure_ascii=False))

    if failed:
        print(f"{RED}FAIL — {failed} 项硬禁违规 (无容差, 差一个即失败){RESET}")
        return 1
    print(f"{GREEN}PASS — 结构完整性契约全绿 (P=R=1.00){RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
