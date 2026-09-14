#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十四批手册 §三 短 goal 长度门（复制前必跑；主 session 与车道均可跑）。
① 块数 = 43；② 每块 len() ≤ 3800（/goal 硬限 4000 字符，留 200 缓冲——限的是字符数，wc -c 数字节会虚高）；
③ 每块含对应卡文绝对路径且文件存在；④ 每块含批次标记与「不 push」；⑤ 每块以 /goal 开头；
⑥ 每块与卡文都不得出现 gpt-5.6（Codex 复核模型统一 gpt-6-astra）；⑦ 每块含「复核第十四批」收尾口令；
⑧ 卡文含「本卡未证明什么」与「台账待登记条目」两个必填锚；
⑨ 每块与卡文含 D-15 固定串「Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0」（用户 2026-09-07 裁）；
⑩ 触及 backend/app 的卡（APP_CARDS）卡文与短 goal 含「pyright 保持 0」（第十四批：候选树 pyright app = 0 为合入门，语义车道保持 0）；
⑪ 卡文与短 goal 不得含旧口径字面量（第十四批波 0 勘探实测已更正）：`:1281`（U7-A HIGH-1 主干实值 :1512/:1522-1534/:1535）、
   `mutation_kill_identity.py:203`（H1 落点 :211）、`stale-mock`（Y4-D skip reason 无此字面量）、`cd backend && .venv/bin/pyright`（软链无 pyright，rc=0 假绿）。
本门不比什么：不校验短 goal 概要与卡文语义一致；不校验卡文里的 file:line 是否仍在主干成立；⑩ 的 APP_CARDS 名单是排批时人工圈定，不从 diff 推导。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # goal-cards/
MANUAL = ROOT / "2026-09-11-第十四批开跑手册-10车道43卡.md"
CARD_DIR = ROOT / "第十四批-goals"
ORDER = ["T1-A", "T1-B",
         "T2-A", "T2-B", "T2-C", "T2-D", "T2-E",
         "T3-A", "T3-B", "T3-C", "T3-D",
         "T4-A", "T4-B", "T4-C", "T4-D",
         "T5-A", "T5-B", "T5-C", "T5-D", "T5-E",
         "T6-A", "T6-B", "T6-C",
         "T7-A", "T7-B", "T7-C", "T7-D",
         "T8-A", "T8-B", "T8-C", "T8-D", "T8-E", "T8-F", "T8-G",
         "T9-A", "T9-B", "T9-C", "T9-D",
         "T10-A", "T10-B", "T10-C", "T10-D", "T10-E"]
BATCH = "BATCH-2026-09-11-第十四批"
D15 = "Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0"
APP_CARDS = {"T3-A", "T3-B", "T3-C", "T3-D", "T5-A", "T5-B", "T5-C", "T5-D", "T5-E",
             "T6-B", "T6-C", "T7-B", "T8-F", "T10-E"}  # 14 张；T1-A 的 lancedb_client 在 backend/lib，不计
OLD_LITERALS = (":1281", "mutation_kill_identity.py:203", "stale-mock", "cd backend && .venv/bin/pyright")

ok = True


def fail(msg):
    global ok
    ok = False
    print(f"❌ {msg}")


def main():
    global ok
    if len(ORDER) != 43 or len(set(ORDER)) != 43:
        fail(f"①: ORDER 表 {len(ORDER)} 项 / 去重 {len(set(ORDER))}，应为 43")
        sys.exit(1)
    if not MANUAL.exists():
        fail(f"手册不存在 {MANUAL}")
        sys.exit(1)
    lines = MANUAL.read_text(encoding="utf-8").splitlines()
    i3 = next(i for i, l in enumerate(lines) if l.startswith("## 三、"))
    i4 = next(i for i, l in enumerate(lines) if l.startswith("## 四、"))
    fences = [i for i in range(i3, i4) if lines[i].strip() == "```"]
    if len(fences) != 2 * len(ORDER):
        fail(f"①: §三 围栏数 {len(fences)} != {2 * len(ORDER)}")
        sys.exit(1)
    blocks = ["\n".join(lines[a + 1 : b]) for a, b in zip(fences[0::2], fences[1::2])]
    heads = [l for l in lines[i3:i4] if l.startswith("### ")]
    if len(heads) != len(ORDER):
        fail(f"①: §三 标题数 {len(heads)} != {len(ORDER)}")
    for h, key in zip(heads, ORDER):
        if not h.startswith(f"### {key}（"):
            fail(f"①: 标题顺序错：{h[:30]!r} 应为 {key}")
    for key, blk in zip(ORDER, blocks):
        n = len(blk)
        card = CARD_DIR / f"{key}.md"
        if n > 3800:
            fail(f"②: {key} 长度 {n} > 3800")
        else:
            print(f"✅ {key}: {n} 字符（≤3800）")
        if blk.count("\n") != 6:
            fail(f"②: {key} 不是恰 7 行（{blk.count(chr(10)) + 1} 行）")
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
        if "复核第十四批" not in blk:
            fail(f"⑦: {key} 缺「复核第十四批」收尾口令")
        if D15 not in blk:
            fail(f"⑨: {key} 缺 D-15 固定串")
        if key in APP_CARDS and "pyright 保持 0" not in blk:
            fail(f"⑩: {key} 触及 backend/app 但短 goal 缺「pyright 保持 0」")
        for lit in OLD_LITERALS:
            if lit in blk:
                fail(f"⑪: {key} 块内含旧口径字面量 {lit!r}")
        if card.exists():
            ct = card.read_text(encoding="utf-8")
            if "gpt-5.6" in ct:
                fail(f"⑥: {key} 卡文出现 gpt-5.6")
            for anchor in ("本卡未证明什么", "台账待登记条目"):
                if anchor not in ct:
                    fail(f"⑧: {key} 卡文缺「{anchor}」")
            if D15 not in ct:
                fail(f"⑨: {key} 卡文缺 D-15 固定串")
            if key in APP_CARDS and "pyright 保持 0" not in ct:
                fail(f"⑩: {key} 触及 backend/app 但卡文缺「pyright 保持 0」")
            for lit in OLD_LITERALS:
                if lit in ct:
                    fail(f"⑪: {key} 卡文含旧口径字面量 {lit!r}")
            if "\x00" in ct:
                fail(f"卡文含 NUL 字节 {key}")
    print("GATE:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
