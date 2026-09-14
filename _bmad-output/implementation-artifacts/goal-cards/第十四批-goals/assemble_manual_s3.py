#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 第十四批-goals/_goal/<块名>.txt（每份恰 7 行短 goal）装配进手册 §三（`## 三、` 与 `## 四、` 之间），按 ORDER 顺序。
只读 _goal/*.txt 与手册，重写手册 §三 段落；卡名从卡文第二行的批次标记里取。主 session 排批期与卡文修正后各跑一次；跑完必跑 gate_goal_length_b14.py。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "2026-09-11-第十四批开跑手册-10车道43卡.md"
CARD_DIR = ROOT / "第十四批-goals"
GOAL_DIR = CARD_DIR / "_goal"
sys.path.insert(0, str(CARD_DIR))
from gate_goal_length_b14 import ORDER  # noqa: E402

LANE_OF = lambda k: k.split("-")[0]  # noqa: E731


def card_name(key):
    txt = (CARD_DIR / f"{key}.md").read_text(encoding="utf-8")
    m = re.search(r"\[BATCH-2026-09-11-第十四批 / (CARD-[A-Za-z0-9\-]+)\]", txt)
    if not m:
        raise SystemExit(f"{key}.md 缺批次标记，取不到卡名")
    return m.group(1)


def main():
    text = MANUAL.read_text(encoding="utf-8")
    lines = text.split("\n")
    i3 = next(i for i, l in enumerate(lines) if l.startswith("## 三、"))
    i4 = next(i for i, l in enumerate(lines) if l.startswith("## 四、"))
    out = [lines[i3], ""]
    for key in ORDER:
        g = GOAL_DIR / f"{key}.txt"
        if not g.exists():
            raise SystemExit(f"缺短 goal {g}")
        blk = g.read_text(encoding="utf-8").rstrip("\n")
        name = card_name(key)
        out += [f"### {key}（{name}）", "",
                f"> 📋 复制下面代码块粘进 `{LANE_OF(key)}` 标签页的 /goal；完整卡文 `第十四批-goals/{key}.md`。", "",
                "```", blk, "```", ""]
    new = lines[:i3] + out + lines[i4:]
    MANUAL.write_text("\n".join(new), encoding="utf-8")
    print(f"§三 装配完成：{len(ORDER)} 块")


if __name__ == "__main__":
    main()
