#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十一批手册 §三 短 goal 长度门（复制前必跑；主 session 与车道均可跑）。
① 块数 = 17；② 每块 len() ≤ 3800（/goal 硬限 4000 字符，留 200 缓冲——限的是字符数，wc -c 数字节会虚高）；
③ 每块含对应卡文绝对路径且文件存在；④ 每块含批次标记与「不 push」；⑤ 每块以 /goal 开头；
⑥ 每块与卡文都不得出现 gpt-5.6（Codex 复核模型自 2026-09-05 起统一 gpt-6-astra）。
本门不比什么：不校验短 goal 概要与卡文语义一致；不校验卡文内容。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # goal-cards/
MANUAL = ROOT / "2026-09-05-第十一批开跑手册-7车道17卡.md"
CARD_DIR = ROOT / "第十一批-goals"
ORDER = ["Z1-A", "Z1-B", "Z1-C", "Z1-D", "Z2", "Z3-A", "Z3-B", "Z3-C", "Z4-A", "Z4-B", "Z5",
         "Z6-A", "Z6-B", "Z6-C", "Z7-A", "Z7-B", "Z7-C"]
BATCH = "BATCH-2026-09-05-第十一批"

ok = True


def fail(msg):
    global ok
    ok = False
    print(f"❌ {msg}")


lines = MANUAL.read_text(encoding="utf-8").splitlines()
i3 = next(i for i, l in enumerate(lines) if l.startswith("## 三、"))
i4 = next(i for i, l in enumerate(lines) if l.startswith("## 四、"))
fences = [i for i in range(i3, i4) if lines[i].strip() == "```"]
if len(fences) != 2 * len(ORDER):
    fail(f"①: §三 围栏数 {len(fences)} != {2 * len(ORDER)}")
    sys.exit(1)
blocks = ["\n".join(lines[a + 1 : b]) for a, b in zip(fences[0::2], fences[1::2])]
for key, blk in zip(ORDER, blocks):
    n = len(blk)
    card = CARD_DIR / f"{key}.md"
    if n > 3800:
        fail(f"②: {key} 长度 {n} > 3800")
    else:
        print(f"✅ {key}: {n} 字符（≤3800）")
    if str(card) not in blk:
        fail(f"③: {key} 块内缺卡文绝对路径 {card}")
    if not card.exists():
        fail(f"③: {key} 卡文不存在 {card}")
    if BATCH not in blk:
        fail(f"④: {key} 缺批次标记 {BATCH}")
    if "不 push" not in blk:
        fail(f"④: {key} 缺「不 push」")
    if not blk.startswith("/goal"):
        fail(f"⑤: {key} 不以 /goal 开头")
    if "gpt-5.6" in blk:
        fail(f"⑥: {key} 块内出现 gpt-5.6")
    if card.exists() and "gpt-5.6" in card.read_text(encoding="utf-8"):
        fail(f"⑥: {key} 卡文出现 gpt-5.6")
print("GATE:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
