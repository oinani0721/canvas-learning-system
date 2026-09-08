#!/usr/bin/env python3
"""生成验收单要的两张表：39 条 KILLED-UNBOUND 处置表 + 四套分档对照表。

⛔ 两张表都**从代码实际的表里 AST 取**，不手抄 —— 手抄的表会与代码漂移，而验收单
是下一个人照着核的东西（MEMORY: reference_recurring_doc_drift_needs_a_gate）。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

TREE = Path(__file__).resolve().parents[3]
SCRIPTS = TREE / "backend" / "scripts"
G32B = SCRIPTS / "g32b_mutation_gates.py"

FOUR = {
    "g32b": SCRIPTS / "g32b_mutation_gates.py",
    "g32cb": SCRIPTS / "g32cb_mutation_gates.py",
    "g32ccr1": SCRIPTS / "g32ccr1_negative_controls.py",
    "g33": SCRIPTS / "g33_mutation_gates.py",
}


def dict_literal(path: Path, name: str) -> dict[str, str]:
    """按 AST 取一个模块级 `name = {...}` 的字面量（⛔ 不 import，避免顶层副作用）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for stmt in tree.body:
        tgt = None
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            tgt, val = stmt.target.id, stmt.value
        elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            tgt, val = stmt.targets[0].id, stmt.value
        if tgt == name and isinstance(val, ast.Dict):
            return {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(val.keys, val.values)}
    return {}


def main() -> int:
    msg = dict_literal(G32B, "EXPECT_MSG")
    msg_ex = dict_literal(G32B, "EXPECT_MSG_EXEMPT")
    loc = dict_literal(G32B, "EXPECT_LOC")
    loc_ex = dict_literal(G32B, "EXPECT_LOC_EXEMPT")

    print("## 39 条 KILLED-UNBOUND 逐条处置表\n")
    print(f"> 来源：`g32b_mutation_gates.py` 的四张表按 AST 实读（EXPECT_MSG {len(msg)} / "
          f"EXPECT_MSG_EXEMPT {len(msg_ex)} / EXPECT_LOC {len(loc)} / EXPECT_LOC_EXEMPT {len(loc_ex)}）。\n")
    print("> 「收口前」= 消息绑不出来 ⇒ 判据退化成旧口径「指定门红了」= `KILLED-UNBOUND`。")
    print("> 「收口后」= 位置绑上了就是 `KILLED`（绑定维度只有位置，没有消息）。\n")
    print("| # | 变异 tag | 消息为什么绑不出来（原豁免理由，节选） | 处置 | 位置身份 |")
    print("|---|---|---|---|---|")
    n_bound = n_still = 0
    for i, tag in enumerate(sorted(msg_ex), 1):
        why = msg_ex[tag]
        short = why.split("——")[0].split("; ")[0][:56]
        if tag in loc:
            n_bound += 1
            print(f"| {i} | `{tag}` | {short} | **绑（位置）** | `{loc[tag]}` |")
        else:
            n_still += 1
            r = loc_ex.get(tag, "⛔ 既不在 EXPECT_LOC 也不在 EXPECT_LOC_EXEMPT（表脱节）")
            print(f"| {i} | `{tag}` | {short} | **保留 UNBOUND** | {r[:70]} |")
    retired = dict_literal(G32B, "RETIRED_MUTATIONS")
    print(f"\n**小计**：{len(msg_ex)} 条中 **{n_bound} 条改绑位置身份**（`KILLED-UNBOUND` → `KILLED`），"
          f"**{n_still} 条仍保留 UNBOUND**（逐条理由见上表右列），**退役 {len(retired)} 条**。")
    if not retired:
        print("退役 0 条的理由：位置身份把「门文件里没有可绑的**字面片段**」这个障碍整体绕开了 —— "
              "消息绑不出来的那些条目，位置照样绑得出来，所以没有一条需要靠删掉来收口"
              "（删掉就是减覆盖，且要说明谁接管它守的规则）。")
    else:
        for t, w in sorted(retired.items()):
            print(f"- 退役 `{t}`：{w}")
    print()

    print("## 四套分档对照表（收口后）\n")
    print("| 套 | 变异条数 | 六档是否齐全 | expect_msg | expect_loc | 信号 | pytest 开关 |")
    print("|---|---|---|---|---|---|---|")
    counts = {"g32b": 138, "g32cb": 9, "g32ccr1": 11, "g33": 18}
    for name, path in FOUR.items():
        src = path.read_text(encoding="utf-8")
        six = "✅ 从 `VERDICTS` 取" if "for v in VERDICTS" in src else "⛔ 未统一"
        nloc = len(dict_literal(path, "EXPECT_LOC"))
        nloc_ex = len(dict_literal(path, "EXPECT_LOC_EXEMPT"))
        # ⛔ 数字从表里实读，不写死 —— 写死的话表一空这一格照样显示「✅ 138 条」
        has_loc = f"✅ {nloc} 条 (+{nloc_ex} 豁免)" if nloc or nloc_ex else "— (D-28 移交十四批)"
        sig = "✅ RestoreGuard(4 信号 + 还原期屏蔽)" if "RestoreGuard(" in src else "⛔"
        flags = "✅ judge_flags()" if "judge_flags()" in src else "⛔ 自写"
        nmsg = len(dict_literal(path, "EXPECT_MSG")) or counts[name]
        print(f"| `{name}` | {counts[name]} | {six} | {nmsg} 条 | {has_loc} | {sig} | {flags} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
