#!/usr/bin/env python3
"""跨套「六档处置表」逐档硬比 —— CARD-DEBT-mutkill-R3 MEDIUM③。

⛔ **这不是「读汇总段字段」，是「解析被测套自己印出来的裁决」**。两者差别必须说清：
四套变异 harness 里**只有 `g33`** 有 `--json` 并写结构化的 `verdict_counts`
（`g33_mutation_gates.py` 的 `--json` 选项与 `"verdict_counts": nv` 字段）；
`g32b` / `g32cb` / `g32ccr1` 三套**既无 `--json` 选项也无该字段**（2026-09-14 于
`B14_BASE` 树 `grep -cF 'verdict_counts'` / `grep -cF -- '--json'` 实测皆为 0），
它们的六档只出现在 **stdout 的汇总段**。所以本工具对三套是**按套写正则去解析人读
文本**，正则写错 = 本工具自己红（解析不到任一档即 `SystemExit`），⛔ 不得静默判「一致」。
「给三套补 `--json`/`verdict_counts`」已裁另立第十五批卡，不在本卡地盘。

⛔ **不自证**：本工具**不重新裁决**任何变异，也不统计自己解析出来的裁决结果去和
自己比 —— 那是恒真式。真正承重的独立判据是**分母**：每套「应有多少条变异」由本
工具**自己用 AST 从该套源码现算** `len(MUTATIONS)`，⛔ 不采信存档或 stdout 自称的
`total` / `M`。四个数必须全相等：

    ① reconcile 自己把解析到的六档相加      = sum(six)
    ② 该套**自己印出来**的「六档之和」      = T
    ③ 该套**自称**的分母                    = M
    ④ 本工具从源码 AST 现算的变异条数        = N

  · ①≠② ⇒ 存档里某一档的计数被改过 / 正则吃错了行；
  · ②≠③ ⇒ 有条目跑完没落进任何一档（该套自己的 `_sum_ok` 本该已经报，存档可能被改）；
  · ③≠④ ⇒ **部分跑冒充全量**，或 `MUTATIONS` 漂移 —— 这一条才是跨源独立判据。

只读：本工具只读存档与 tee 文件 + 用 `ast` 解析 harness 源码（⛔ 不 `import` 任何
harness 的 `main()`、不跑门、不改盘、不连任何库）。

用法::

    python3 scripts/mutation_verdict_reconcile.py \\
        --expect g32cb,g32ccr1 \\
        --stdout g32cb=<tee.txt> --stdout g32ccr1=<tee.txt>

`--expect` 是**声明式**的：声明了哪几套，就必须给哪几套的输入。声明了却没给输入 /
文件不存在 / 解析不到六档 ⇒ `SystemExit`（非零 rc）。
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

SCRIPTS = Path(__file__).resolve().parent

#: 六档口径与 `mutation_kill_identity.VERDICTS` 逐字一致。
#: ⛔ 这里**故意写死一份字面量**而不是 `from mutation_kill_identity import VERDICTS`：
#: 本工具是对账方，档名是它的**独立预期**。跟被对账方共用同一个常量，「档名漂了」
#: 这件事就再也对不出来了（两份手抄清单会漂移，但漂移正是这道门要抓的东西）。
VERDICT_NAMES: tuple[str, ...] = (
    "KILLED",
    "KILLED-UNBOUND",
    "SURVIVED",
    "HARNESS-ERROR",
    "ANCHOR-ERROR",
    "SYNTAX-INVALID",
)

#: 三套 stdout 形态里，除 KILLED 外的五档都是 `档名: N`（g32cb/g32ccr1 带两空格缩进）。
_TAIL_FIVE = "KILLED-UNBOUND|SURVIVED|HARNESS-ERROR|ANCHOR-ERROR|SYNTAX-INVALID"


class Parsed(NamedTuple):
    """从一份存档里解析出来的东西（全部来自**被对账方自己的输出**）。"""

    counts: dict[str, int]
    printed_total: int  # 该套自己印的「六档之和」
    declared_m: int  # 该套自称的分母


class Suite(NamedTuple):
    source: str  # harness 源码文件名（AST 现算分母用）
    form: str  # "stdout" | "json"


SUITES: dict[str, Suite] = {
    # ⚠️ g32b 的汇总段**不缩进**，且多印一行「KILLED 合计」——那**不是**六档之一。
    "g32b": Suite("g32b_mutation_gates.py", "stdout"),
    "g32cb": Suite("g32cb_mutation_gates.py", "stdout"),
    "g32ccr1": Suite("g32ccr1_negative_controls.py", "stdout"),
    # ⚠️ 只有 g33 有 `--json` / `verdict_counts`（实测）。
    "g33": Suite("g33_mutation_gates.py", "json"),
}


class ReconcileError(Exception):
    """解析/对账失败。⛔ 一律上抛成非零 rc，不得降级成「一致」。"""


# ── 独立分母：AST 现算 ──────────────────────────────────────────────────────


def ast_mutation_count(source_name: str) -> int:
    """从 harness 源码 AST 现算 `len(MUTATIONS)`。

    ⛔ 用 `ast.parse` 而不是 `import`：import 会执行模块级代码（含路径常量与可能的
    副作用），而本工具的承诺是**只读**。
    """
    path = SCRIPTS / source_name
    if not path.exists():
        raise ReconcileError(f"harness 源码不存在，分母无法独立现算: {path}")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            if any(getattr(t, "id", "") == "MUTATIONS" for t in node.targets):
                return len(node.value.elts)
    raise ReconcileError(f"{source_name} 里找不到模块级 `MUTATIONS = [...]`，分母无法独立现算")


# ── 形态一：g32cb / g32ccr1 的 stdout 汇总段 ────────────────────────────────
#
# 实测形态（g32cb :582-603 / g32ccr1 :462-482），两空格缩进、**计数在档名之前**：
#     «2 空格»9/9 KILLED (绑定: 消息 + 失败位置在门文件内; …)
#     «2 空格»KILLED-UNBOUND: 0 (仅证明指定门红了)
#     …
#     «2 空格»六档之和: 9 (应 = 变异条数 9) ✓

_CB_KILLED = re.compile(r"^ {2}(?P<n>\d+)/(?P<m>\d+) KILLED \(", re.M)
_CB_FIVE = re.compile(rf"^ {{2}}(?P<name>{_TAIL_FIVE}): (?P<n>\d+)", re.M)
_CB_SUM = re.compile(r"^ {2}六档之和: (?P<t>\d+) \(应 = 变异条数 (?P<m>\d+)\)", re.M)

# ── 形态二：g32b 的 stdout 汇总段 ───────────────────────────────────────────
#
# 实测形态（g32b :3019-3041），**不缩进**、计数在冒号之后：
#     KILLED (绑定断言身份: 位置 [+ 消息]): 6/6
#     KILLED-UNBOUND (仅证明指定门红了, 位置与消息都没绑): 0
#     KILLED 合计 (两者之和, **不等于**「全部被指定断言杀死」): 6/6   ⛔ 不是六档之一
#     SURVIVED: 0
#     …
#     六档之和: 6 (应 = 6) ✓            ⛔ 括注里**没有**「变异条数」字样

_B_KILLED = re.compile(r"^KILLED \(绑定断言身份: [^)]*\): (?P<n>\d+)/(?P<m>\d+)\s*$", re.M)
_B_UNBOUND = re.compile(r"^KILLED-UNBOUND \([^)]*\): (?P<n>\d+)\s*$", re.M)
_B_FOUR = re.compile(r"^(?P<name>SURVIVED|HARNESS-ERROR|ANCHOR-ERROR|SYNTAX-INVALID): (?P<n>\d+)", re.M)
_B_SUM = re.compile(r"^六档之和: (?P<t>\d+) \(应 = (?P<m>\d+)\)", re.M)


def _one(rx: re.Pattern[str], text: str, what: str, suite: str) -> re.Match[str]:
    """整份存档里该形态必须**恰好命中一次**。

    ⛔ 0 次 = 正则写错或该套没印出来 ⇒ 报错，不得当「缺省 0」；
    ⛔ >1 次 = 存档里混了两次跑的输出，逐档硬比会拿错一次的数字。
    """
    hits = rx.findall(text)
    if len(hits) != 1:
        raise ReconcileError(f"{suite}: 存档里「{what}」命中 {len(hits)} 次(应为 1) —— 正则 {rx.pattern!r}")
    m = rx.search(text)
    assert m is not None  # findall 命中 1 次 ⇒ search 必命中
    return m


def parse_stdout(suite: str, text: str) -> Parsed:
    """解析三套 stdout 汇总段。⛔ 三套形态互异，按套分支，不共用一套正则。"""
    counts: dict[str, int] = {}
    if suite == "g32b":
        mk = _one(_B_KILLED, text, "KILLED 行", suite)
        counts["KILLED"] = int(mk.group("n"))
        declared_m = int(mk.group("m"))
        counts["KILLED-UNBOUND"] = int(_one(_B_UNBOUND, text, "KILLED-UNBOUND 行", suite).group("n"))
        four = _B_FOUR.finditer(text)
        for m in four:
            counts[m.group("name")] = int(m.group("n"))
        ms = _one(_B_SUM, text, "六档之和行", suite)
    else:
        mk = _one(_CB_KILLED, text, "KILLED 行", suite)
        counts["KILLED"] = int(mk.group("n"))
        declared_m = int(mk.group("m"))
        for m in _CB_FIVE.finditer(text):
            counts[m.group("name")] = int(m.group("n"))
        ms = _one(_CB_SUM, text, "六档之和行", suite)
    missing = [v for v in VERDICT_NAMES if v not in counts]
    if missing:
        raise ReconcileError(f"{suite}: 存档里解析不到这些档 {missing} —— ⛔ 缺档不得当成 0/「一致」")
    # ⚠️ KILLED 行与「六档之和」行各自带一个分母；两者不一致说明存档被改过。
    sum_m = int(ms.group("m"))
    if sum_m != declared_m:
        raise ReconcileError(f"{suite}: 该套自称的分母自相矛盾（KILLED 行 {declared_m} vs 六档之和行 {sum_m}）")
    return Parsed(counts, int(ms.group("t")), declared_m)


def parse_json(suite: str, text: str) -> Parsed:
    """解析 g33 的 `--json` 存档（实测只有 g33 有 `verdict_counts` / `total`）。"""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReconcileError(f"{suite}: JSON 存档解析不了 —— {exc}") from exc
    if not isinstance(data, dict):
        raise ReconcileError(f"{suite}: JSON 存档顶层不是对象")
    raw = data.get("verdict_counts")
    if not isinstance(raw, dict):
        raise ReconcileError(f"{suite}: JSON 存档缺 `verdict_counts` 字段 —— ⛔ 缺字段不得当成「一致」")
    missing = [v for v in VERDICT_NAMES if v not in raw]
    if missing:
        raise ReconcileError(f"{suite}: `verdict_counts` 缺这些档 {missing} —— ⛔ 缺档不得当成 0/「一致」")
    total = data.get("total")
    if not isinstance(total, int):
        raise ReconcileError(f"{suite}: JSON 存档缺 `total`（该套自称的分母）")
    counts = {v: int(raw[v]) for v in VERDICT_NAMES}
    # g33 自己印的「六档之和」在 stdout；JSON 侧它把结论存成布尔 `verdict_sum_matches_total`。
    # ⛔ 不拿这个布尔当「六档之和」用 —— 它是该套**自己的结论**，不是可交叉核对的数字。
    # JSON 形态下「该套自己印出来的和」以 `sum(verdict_counts)` 为准（那是它写进存档的
    # 六个数字本身），独立性由 AST 分母那一维承担。
    declared_sum_ok = data.get("verdict_sum_matches_total")
    if declared_sum_ok is not None and not isinstance(declared_sum_ok, bool):
        raise ReconcileError(f"{suite}: `verdict_sum_matches_total` 形态不对（应为布尔）")
    return Parsed(counts, sum(counts.values()), total)


# ── 对账 ────────────────────────────────────────────────────────────────────


def reconcile_one(suite: str, path: Path) -> list[str]:
    """核一套；返回问题列表（空 = 该套对得上）。"""
    cfg = SUITES[suite]
    if not path.exists():
        raise ReconcileError(f"{suite}: 声明了要核，但输入文件不存在 {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_stdout(suite, text) if cfg.form == "stdout" else parse_json(suite, text)
    ast_n = ast_mutation_count(cfg.source)
    own_sum = sum(parsed.counts.values())
    problems: list[str] = []
    if own_sum != parsed.printed_total:
        problems.append(
            f"{suite}: 逐档相加 {own_sum} ≠ 该套印出来的六档之和 {parsed.printed_total} "
            f"—— 存档里某一档的计数与和行对不上"
        )
    if parsed.printed_total != parsed.declared_m:
        problems.append(
            f"{suite}: 六档之和 {parsed.printed_total} ≠ 该套自称的分母 {parsed.declared_m} —— 有条目跑完没落进任何一档"
        )
    if parsed.declared_m != ast_n:
        problems.append(
            f"{suite}: 该套自称的分母 {parsed.declared_m} ≠ 源码 AST 现算的变异条数 {ast_n} "
            f"—— 部分跑冒充全量, 或 MUTATIONS 已漂移（⛔ 这一条是唯一的跨源独立判据）"
        )
    print(f"── {suite}（{cfg.form} 形态, 存档 {path.name}）")
    for v in VERDICT_NAMES:
        print(f"     {v:15} {parsed.counts[v]}")
    print(
        f"     逐档相加={own_sum} 该套印的六档之和={parsed.printed_total} "
        f"该套自称分母={parsed.declared_m} AST 现算条数={ast_n} "
        f"{'✓' if not problems else '⛔ 对不上'}"
    )
    return problems


def _kv(pairs: list[str], flag: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for raw in pairs:
        if "=" not in raw:
            raise SystemExit(f"⛔ {flag} 须写成 `<套名>=<路径>`，实得 {raw!r}")
        name, _, p = raw.partition("=")
        if name not in SUITES:
            raise SystemExit(f"⛔ {flag} 里的套名 {name!r} 不认识（可选: {', '.join(SUITES)}）")
        if name in out:
            raise SystemExit(f"⛔ {flag} 给了两次 {name!r}")
        out[name] = Path(p)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--expect", required=True, help="本次应核哪几套（逗号分隔）")
    ap.add_argument("--stdout", action="append", default=[], metavar="套名=路径", help="该套 run 的 tee .txt")
    ap.add_argument("--json", action="append", default=[], metavar="套名=路径", help="该套 --json 存档")
    args = ap.parse_args(argv)

    expect = [s.strip() for s in args.expect.split(",") if s.strip()]
    if not expect:
        raise SystemExit("⛔ --expect 不得为空 —— 空声明会让这道门变成恒真")
    unknown = [s for s in expect if s not in SUITES]
    if unknown:
        raise SystemExit(f"⛔ --expect 里的套名不认识: {unknown}（可选: {', '.join(SUITES)}）")

    stdout_in = _kv(args.stdout, "--stdout")
    json_in = _kv(args.json, "--json")
    inputs: dict[str, Path] = {}
    problems: list[str] = []
    for suite in expect:
        want = SUITES[suite].form
        given = stdout_in if want == "stdout" else json_in
        other = json_in if want == "stdout" else stdout_in
        if suite in other:
            # ⛔ 形态喂错必须报错而不是「试着解析看看」：g32b 没有 --json，
            # 拿 stdout 当 JSON 解析失败会被误读成「存档坏了」而不是「口径错了」。
            problems.append(f"{suite}: 该套是 {want} 形态，却用 --{'json' if want == 'stdout' else 'stdout'} 喂入")
            continue
        if suite not in given:
            # ⛔ MEDIUM③ 的核心：声明了却没给输入**不得**静默判「一致」。
            problems.append(f"{suite}: --expect 声明了要核，却没给 --{want} 输入 —— ⛔ 缺席不是「一致」")
            continue
        inputs[suite] = given[suite]

    extra = sorted((set(stdout_in) | set(json_in)) - set(expect))
    if extra:
        problems.append(f"给了输入却没在 --expect 里声明: {extra} —— 声明与输入必须一一对应")

    print(f"== 六档处置表跨套硬比（声明核 {len(expect)} 套: {', '.join(expect)}）==")
    for suite in expect:
        if suite not in inputs:
            continue
        try:
            problems.extend(reconcile_one(suite, inputs[suite]))
        except ReconcileError as exc:
            problems.append(str(exc))

    if problems:
        print("\n⛔ 对账不通过:")
        for p in problems:
            print(f"   · {p}")
        raise SystemExit(1)
    print(f"\n✓ {len(expect)} 套六档逐档硬比一致，且各套自称分母 == 源码 AST 现算条数")
    return 0


if __name__ == "__main__":
    sys.exit(main())
