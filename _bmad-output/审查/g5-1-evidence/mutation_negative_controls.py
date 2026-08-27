#!/usr/bin/env python3
"""G5-1 — check_skill_trigger_matrix.py 变异负控（「校验器能红」的可复跑证明）。

15 类蓄意腐烂逐一注入断言表副本, 逐类断言校验器判红且红在预期检查项上
(v2 追加 10 类: 归属锚缺失/伪造、快照 sha 篡改、行号出界、文档-YAML 单边漂移 ×2、
构造顶替真实配额、空白注水、改写行号乱标、话语查重);
最后一类对照组证明 10−1=9 条负例仍 ≥8 判绿是正确行为（不是漏抓）。

用法: backend/.venv/bin/python3 _bmad-output/审查/g5-1-evidence/mutation_negative_controls.py
退出码: 0 = 5 类全被抓 + 对照组行为正确 / 1 = 有漏抓
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
SRC = REPO / "backend" / "scripts" / "check_skill_trigger_matrix.py"
YAML_PATH = REPO / "backend" / "tests" / "regression" / "skill_trigger_matrix.yaml"
VAULT = REPO / "canvas-vault"


def run_mutated(name: str, mutate, workdir: Path) -> tuple[int, list[str]]:
    import yaml

    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    mutate(data)
    p = workdir / f"{name}.yaml"
    p.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"cstm_{name}", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.MATRIX_YAML = p
    sys.argv = ["x", "--vault", str(VAULT)]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main()
    red = [ln.split()[1] for ln in buf.getvalue().splitlines() if "✗" in ln]
    return rc, red


def m_fake_verbatim(d):  # 冒充原话: 篡改 A1 措辞但仍标 verbatim
    for e in d["entries"]:
        if e["id"] == "A1":
            e["utterance"] = "我对规划代理完全理解了，想单独讨论"


def m_flip_trigger(d):  # trigger_today 撒谎: B1 斜杠形却标 false
    for e in d["entries"]:
        if e["id"] == "B1":
            e["trigger_today"] = False


def m_neg_live_prefix(d):  # 负例踩 live 斜杠前缀 (按约定必触发, 自相矛盾)
    for e in d["entries"]:
        if e["id"] == "N3":
            e["utterance"] = "/board-recap 回顾一下我们刚才聊了什么"


def m_planned_as_live(d):  # 未上线 skill 冒充 live
    for e in d["entries"]:
        if e["id"] == "D2":
            e["skill_status"] = "live"


def m_seven_negatives(d):  # 负例砍到 7 条 (< 8)
    d["entries"] = [e for e in d["entries"] if e["id"] not in ("N8", "N9", "N10")]


def m_control_nine(d):  # 对照组: 砍 1 条剩 9 条 — 数量门 T2 必须不红 (9 ≥ 8),
    # 但 v2 行级同步下「YAML 删了文档行还在」必须被 T8 抓 (单边删除即漂移)
    d["entries"] = [e for e in d["entries"] if e["id"] != "N10"]


# ── v2 追加 (Codex 一轮 HIGH-1/2/4 与 BLOCKER-1 对应的腐烂面) ──


def m_no_attribution(d):  # 逐字条目抹掉引语归属锚
    for e in d["entries"]:
        if e["id"] == "A1":
            e["source"].pop("attribution", None)


def m_fake_attribution(d):  # 归属锚指向窗口里不存在的短语
    for e in d["entries"]:
        if e["id"] == "A1":
            e["source"]["attribution"] = "用户亲笔签名"


def m_snapshot_tamper(d):  # 语料快照 sha 登记被改 (等价于快照内容被动过)
    d["meta"]["corpus"]["report"]["sha256"] = "0" * 64


def m_line_out_of_range(d):  # 行号乱标出界
    for e in d["entries"]:
        if e["id"] == "A1":
            e["source"]["line"] = 99999


def m_doc_trigger_flip(d):  # YAML 单边翻转 B1 触发判定 (文档行仍是 **是**)
    for e in d["entries"]:
        if e["id"] == "B1":
            e["trigger_today"] = False


def m_yaml_delete_keep_doc(d):  # 从 YAML 删 A4 但文档表格行还在
    d["entries"] = [e for e in d["entries"] if e["id"] != "A4"]


def m_constructed_fills_real(d):  # 构造顶替真实配额 (把拆分收集的逐字全改构造)
    for e in d["entries"]:
        if e["id"] in ("A1", "A2", "A5"):
            e["source"] = {"type": "constructed"}


def m_whitespace_padding(d):  # 「导 出 思 维 导 图」式注水 (含空白须原文精确匹配)
    for e in d["entries"]:
        if e["id"] == "A2":
            e["utterance"] = " ".join(e["utterance"])


def m_paraphrase_wrong_line(d):  # 改写条目行号乱标到无语义重叠的位置
    for e in d["entries"]:
        if e["id"] == "B3":
            e["source"]["line"] = 134


def m_duplicate_utterance(d):  # 同话语两条断言 (回归集合注水)
    for e in d["entries"]:
        if e["id"] == "N3":
            e["utterance"] = "把 lecture 2 的要点总结成一页笔记给我看看"


# ── v3 追加 (Codex 二轮新发现对应) ──


def m_floor_self_lower(d):  # real_floor 单边自降级 (YAML 把门槛调成全 0)
    d["meta"]["real_floor"] = {k: 0 for k in d["meta"]["real_floor"]}


def m_docdemo_as_verbatim(
    d,
):  # 文档演示冒充用户逐字 (D1 换 verbatim, 归属锚仍是作者标记)
    for e in d["entries"]:
        if e["id"] == "D1":
            e["source"]["type"] = "verbatim"


CASES = [
    ("fake_verbatim", m_fake_verbatim, True, {"T7", "T8"}),
    ("flip_trigger", m_flip_trigger, True, {"T5"}),
    ("neg_live_prefix", m_neg_live_prefix, True, {"T6", "T8"}),
    ("planned_as_live", m_planned_as_live, True, {"T3", "T5"}),
    ("seven_negatives", m_seven_negatives, True, {"T2"}),
    ("no_attribution", m_no_attribution, True, {"T7"}),
    ("fake_attribution", m_fake_attribution, True, {"T7"}),
    ("snapshot_tamper", m_snapshot_tamper, True, {"T7"}),
    ("line_out_of_range", m_line_out_of_range, True, {"T7"}),
    ("doc_trigger_flip", m_doc_trigger_flip, True, {"T5", "T8"}),
    ("yaml_delete_keep_doc", m_yaml_delete_keep_doc, True, {"T8"}),
    ("constructed_fills_real", m_constructed_fills_real, True, {"T1"}),
    ("whitespace_padding", m_whitespace_padding, True, {"T7"}),  # T8 空白归一按设计不红
    ("paraphrase_wrong_line", m_paraphrase_wrong_line, True, {"T7"}),
    ("duplicate_utterance", m_duplicate_utterance, True, {"T0"}),
    ("floor_self_lower", m_floor_self_lower, True, {"T0"}),
    ("docdemo_as_verbatim", m_docdemo_as_verbatim, True, {"T7"}),
    # 对照组: 数量门 9≥8 不触 T2, 但单边删除必被 T8 行级同步抓 — 断言"红得准"
    ("control_nine_negs", m_control_nine, True, {"T8"}),
]

#: 对照组额外断言: 这些检查项在该变异下**不许**红 (红了 = 数量门误伤)
FORBIDDEN_RED = {"control_nine_negs": {"T2"}}


def main() -> int:
    all_ok = True
    with tempfile.TemporaryDirectory() as td:
        for name, mut, want_red, want_checks in CASES:
            rc, red = run_mutated(name, mut, Path(td))
            red_prefixes = {r.split("[")[0] for r in red}
            forbidden = FORBIDDEN_RED.get(name, set())
            if want_red:
                ok = (
                    rc == 1
                    and want_checks <= red_prefixes
                    and not (forbidden & red_prefixes)
                )
                verdict = "✓ 被抓" if ok else "✗ 漏抓或误伤!"
            else:
                ok = rc == 0
                verdict = "✓ 对照组正确判绿" if ok else "✗ 对照组误判红!"
            print(f"[{name}] rc={rc} 红项={sorted(red_prefixes) or '无'} → {verdict}")
            all_ok &= ok
    n_mut = sum(1 for _, _, want_red, _ in CASES if want_red)
    print(
        f"PASS — {n_mut} 类变异全被抓, 对照组行为正确"
        if all_ok
        else "FAIL — 校验器有漏抓面"
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
