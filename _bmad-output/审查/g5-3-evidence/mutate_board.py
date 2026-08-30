#!/usr/bin/env python3
"""G5-3 四态实景演示的确定性变异器（只作用于 scratchpad 里的 vault **副本**，绝不碰 live）。

对一块真实板（或它的种子笔记——CS188 板的候选实际全部来自 `节点/lecture 2.md`，
所以目标文件按候选分布自动选，不写死）施加四种互不重叠的改动：
  1. 行号漂移 —— 往 frontmatter 塞 3 行（期望 unchanged）
  2. 正文微调 —— 在目标小节正文末尾追加一句（期望 changed / reason=content）
  3. 顺序调换 —— 把一个小节整块搬到另一个之前（期望 moved）
  4. 改标题   —— 给一个小节标题加后缀（期望 removed + added）

目标小节从候选里挑**互不嵌套**的四个（贪心取 line_start > 上一个 line_end）——
嵌套会让父子连坐，把演示搅浑。

用法: python3 mutate_board.py <vault根> <preview.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def pick_disjoint(cands: list[dict], n: int) -> list[dict]:
    out: list[dict] = []
    last_end = -1
    for c in cands:
        a = c["source_anchor"]
        if a["line_start"] > last_end:
            out.append(c)
            last_end = a["line_end"]
        if len(out) == n:
            break
    return out


def main() -> int:
    vault, preview_path = Path(sys.argv[1]), Path(sys.argv[2])
    data = json.loads(preview_path.read_text(encoding="utf-8"))

    # 候选最多的来源文件 = 变异目标（CS188 板的候选全在种子笔记里）
    per_file: dict[str, list[dict]] = {}
    for c in data["candidates"]:
        per_file.setdefault(c["source_anchor"]["file"], []).append(c)
    target_rel = max(per_file, key=lambda k: len(per_file[k]))
    cands = per_file[target_rel]

    picks = pick_disjoint(cands, 4)
    if len(picks) < 4:
        raise SystemExit(f"✗ {target_rel} 里互不嵌套的候选不足 4 个（{len(picks)}），无法演示四态")
    edit_c, before_c, move_c, rename_c = picks

    path = vault / target_rel
    lines = path.read_text(encoding="utf-8").splitlines()

    def span(c: dict) -> tuple[int, int]:  # → 0-based [start, end)
        a = c["source_anchor"]
        return a["line_start"] - 1, a["line_end"]

    # 4. 改标题（最靠后，原地替换不改行数）
    rs, _ = span(rename_c)
    lines[rs] = lines[rs].rstrip() + "（修订版）"

    # 3. 顺序调换：move_c 整块搬到 before_c 之前
    ms, me = span(move_c)
    block = lines[ms:me]
    del lines[ms:me]
    bs, _ = span(before_c)
    lines[bs:bs] = block

    # 2. 正文微调：edit_c 末尾追加一句（edit_c 完全在 before_c 之前，调序不影响其行号）
    _, ee = span(edit_c)
    lines.insert(ee, "补一句实景演示用的正文改动，用来触发内容指纹变化。")

    # 1. 行号漂移：frontmatter 塞 3 行（全局位移，不改任何小节内容）
    drift = False
    if lines and lines[0].strip() == "---":
        close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if close is not None:
            lines[close:close] = [f"g53_demo_pad_{i}: x" for i in range(3)]
            drift = True

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"变异目标文件: {target_rel}（候选 {len(cands)}）· frontmatter 行号漂移={'是' if drift else '否(无 frontmatter)'}")
    print(f"  改正文  : {edit_c['resolved_name']}  [{edit_c['stable_id']}]")
    print(f"  调序    : {move_c['resolved_name']} → 移到 {before_c['resolved_name']} 之前  [{move_c['stable_id']}]")
    print(f"  改标题  : {rename_c['resolved_name']}  [{rename_c['stable_id']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
