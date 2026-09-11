#!/usr/bin/env python3
"""把 `--probe` 观察到的失败位置回填进 `g32b_mutation_gates.py::EXPECT_LOC`。

⚠️ 回填这件事的性质如实说：`EXPECT_LOC` 的值来自「跑一次看它红在哪」，**判据与
被测量同源** —— 今天证不出「这条变异确实打红了它声称的那条断言」。价值在**从今
往后**（门或生产代码一漂移就当场报出来）。与现有 91 条 `EXPECT_MSG` 的来路同型。

分流规则（不进 `EXPECT_LOC` 的一律进 `EXPECT_LOC_EXEMPT` 并写理由，⛔ 不静默丢）：
  · `stmt:<指纹>` 且该指纹在门文件里**恰好命中 1 条语句**  → 进 `EXPECT_LOC`；
  · `stmt:<指纹>` 但命中 >1 条                              → 豁免 ⑥「同一份代码写了
    两遍，位置身份不可证」；
  · `file:<名>`（失败落在门文件之外）                        → 豁免 ⓐ；
  · probe 里 rc != 1 或没有位置行                            → 豁免 ⓑ，并写实测 rc。

用法：`python3 fill_expect_loc.py <probe 输出.txt> [--apply]`（不带 --apply 只打印）。
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

TREE = Path(__file__).resolve().parents[3]
G32B = TREE / "backend" / "scripts" / "g32b_mutation_gates.py"
GATE_FILE = TREE / "backend" / "tests" / "regression" / "test_g3_2_review_ledger.py"

sys.path.insert(0, str(TREE / "backend" / "scripts"))
from mutation_kill_identity import stmt_fingerprints  # noqa: E402

CAND_RE = re.compile(
    r"^EXPECT_LOC_CANDIDATE\t(?P<tag>\S+)\t(?P<loc>[^\t]*)\t(?P<rc>\d+)\t(?P<raw>[^\t]*)$", re.M
)

EXEMPT_REASONS = {
    "dup": "⑥ 该条实际打红的那条语句在门文件里**出现 >1 次**(同一份代码写了两遍), "
           "位置指纹不能证明红在哪一处; 门本体不在本卡范围, 无法给它加身份",
    "outside": "ⓐ 该变异让门在**门文件之外**失败(实见 {loc}), 只能绑到文件级弱身份; "
               "按 check_expect_loc_unique 的纪律必须登记而不是当成与 stmt: 同等强度",
    "noloc": "ⓑ probe 实测 rc={rc}、FAILURES 区里没有可用的位置行 —— 位置绑不出来; "
             "该条的击杀身份仍只能靠 expect_msg(若有)",
}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    probe_txt = Path(sys.argv[1]).read_text(encoding="utf-8")
    apply = "--apply" in sys.argv[2:]

    cands = [(m["tag"], m["loc"], int(m["rc"]), m["raw"]) for m in CAND_RE.finditer(probe_txt)]
    if not cands:
        # ⛔ 抽取为空**不是**「没问题」——先断言抽取本身命中了东西，再谈比对结果。
        print("⛔ probe 输出里一条 EXPECT_LOC_CANDIDATE 都没抽到 —— 抽取器坏了或跑的是旧版 harness")
        return 1
    print(f"抽到候选 {len(cands)} 条")

    fps = stmt_fingerprints(GATE_FILE)
    hits = {k: len(v) for k, v in fps.items()}
    loc_tbl: dict[str, str] = {}
    exempt: dict[str, str] = {}
    for tag, loc, rc, _raw in cands:
        if not loc or rc != 1:
            exempt[tag] = EXEMPT_REASONS["noloc"].format(rc=rc)
        elif loc.startswith("file:"):
            exempt[tag] = EXEMPT_REASONS["outside"].format(loc=loc)
        elif hits.get(loc[5:], 0) != 1:
            exempt[tag] = EXEMPT_REASONS["dup"]
        else:
            loc_tbl[tag] = loc

    dup_locs = {k: v for k, v in Counter(loc_tbl.values()).items() if v > 1}
    print(f"可绑 {len(loc_tbl)} 条 / 豁免 {len(exempt)} 条")
    if dup_locs:
        # 两条不同的变异打红**同一条语句** —— 合法（同一道防线的两个面），但要报出来
        print(f"⚠️ 有 {len(dup_locs)} 个位置被多条变异共用（合法，但登记一下）: {dup_locs}")
    for tag, why in sorted(exempt.items()):
        print(f"  豁免 {tag}: {why[:90]}")

    body_loc = "".join(f"    {tag!r}: {loc!r},\n" for tag, loc in sorted(loc_tbl.items()))
    body_ex = "".join(f"    {tag!r}: {why!r},\n" for tag, why in sorted(exempt.items()))
    src = G32B.read_text(encoding="utf-8")
    new = src.replace(
        "EXPECT_LOC: dict[str, str] = {}",
        "EXPECT_LOC: dict[str, str] = {\n" + body_loc + "}",
        1,
    ).replace(
        "EXPECT_LOC_EXEMPT: dict[str, str] = {}",
        "EXPECT_LOC_EXEMPT: dict[str, str] = {\n" + body_ex + "}",
        1,
    )
    if new == src:
        print("⛔ 没有发生替换 —— 目标表已经被填过了？(不覆盖已有内容，先人工核)")
        return 1
    if apply:
        G32B.write_text(new, encoding="utf-8")
        print(f"已写回 {G32B}")
    else:
        print("（未加 --apply，只做了分流预演）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
