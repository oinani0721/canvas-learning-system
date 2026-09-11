#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十三批手册 §三 短 goal 长度门（复制前必跑；主 session 与车道均可跑）。
① 块数 = 32；② 每块 len() ≤ 3800（/goal 硬限 4000 字符，留 200 缓冲——限的是字符数，wc -c 数字节会虚高）；
③ 每块含对应卡文绝对路径且文件存在；④ 每块含批次标记与「不 push」；⑤ 每块以 /goal 开头；
⑥ 每块与卡文都不得出现 gpt-5.6（Codex 复核模型统一 gpt-6-astra）；⑦ 每块含「复核第十三批」收尾口令；
⑧ 卡文含「本卡未证明什么」与「台账待登记条目」两个必填锚；
⑨ 每块含 D-15 固定串「Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0」（用户 2026-09-07 裁）；
⑩ 触及 backend/app 的卡（APP_CARDS）卡文含「禁顺手修存量」（D-16 甲两车道口径：pyright 存量归 U1/U2）。
本门不比什么：不校验短 goal 概要与卡文语义一致；不校验卡文里的 file:line 是否仍在主干成立；⑩ 的 APP_CARDS 名单是排批时人工圈定，不从 diff 推导。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # goal-cards/
MANUAL = ROOT / "2026-09-07-第十三批开跑手册-11车道32卡.md"
CARD_DIR = ROOT / "第十三批-goals"
ORDER = ["U1-A", "U2-A", "U2-B", "U3-A", "U3-B", "U3-C", "U4-A", "U4-B",
         "U5-A", "U5-B", "U5-C", "U5-D", "U6-A", "U6-B", "U6-C",
         "U7-A", "U7-B", "U7-C", "U8-A", "U8-B", "U8-C", "U9-A", "U9-B", "U9-C",
         "U10-A", "U10-B", "U10-C", "U10-D", "U10-E", "U11-A", "U11-B", "U11-C"]
BATCH = "BATCH-2026-09-07-第十三批"
D15 = "Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0"
APP_CARDS = {"U1-A", "U2-A", "U6-A", "U6-B", "U6-C", "U9-B", "U9-C",  # U5-A 的 lancedb_client 在 backend/lib，不计
             "U10-B", "U10-C", "U10-D", "U10-E", "U11-A", "U11-B", "U11-C"}

ok = True


def fail(msg):
    global ok
    ok = False
    print(f"❌ {msg}")


if len(ORDER) != 32 or len(set(ORDER)) != 32:
    fail(f"①: ORDER 表 {len(ORDER)} 项 / 去重 {len(set(ORDER))}，应为 32")
    sys.exit(1)
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
    if "复核第十三批" not in blk:
        fail(f"⑦: {key} 缺「复核第十三批」收尾口令")
    if D15 not in blk:
        fail(f"⑨: {key} 缺 D-15 固定串")
    if card.exists():
        ct = card.read_text(encoding="utf-8")
        if "gpt-5.6" in ct:
            fail(f"⑥: {key} 卡文出现 gpt-5.6")
        for anchor in ("本卡未证明什么", "台账待登记条目"):
            if anchor not in ct:
                fail(f"⑧: {key} 卡文缺「{anchor}」")
        if D15 not in ct:
            fail(f"⑨: {key} 卡文缺 D-15 固定串")
        if key in APP_CARDS and "禁顺手修存量" not in ct:
            fail(f"⑩: {key} 触及 backend/app 但卡文缺「禁顺手修存量」")
print("GATE:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
