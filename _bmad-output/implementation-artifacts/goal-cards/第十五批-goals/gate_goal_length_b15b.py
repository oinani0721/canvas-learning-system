#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十五批**续跑段**手册 §三 短 goal 长度门（复制前必跑）。
① 块数 = 10；② 每块 len() ≤ 3800（/goal 硬限 4000，留 200 缓冲）；③ 每块含对应卡文绝对路径且文件存在；
④ 每块含批次标记与「不 push」；⑤ 每块以 /goal 开头；⑥ 每块不得出现 gpt-6-astra / gpt-5.6（旧模型串）；
⑦ 每块含「复核第十五批」收尾口令；⑧ 卡文含「本卡未证明什么」与「台账待登记条目」两个必填锚；
⑨ 每块与卡文含 D-15 固定串（GLM 版）；⑩ 触及 backend/app 的卡（APP_CARDS）卡文与短 goal 含「pyright 保持 0」；
⑪ 每块恰 7 行；⑫ 两文件不得含协议 §2 四个禁用词；⑬ 卡文含 unit 红基线路径与「33」；⑭ 卡文与短 goal 引用协议 §2.4。
本门不比什么：不校验短 goal 概要与卡文语义一致；不校验卡文里的 file:line 是否仍在车道成立。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # goal-cards/
MANUAL = ROOT / "2026-09-19-第十五批续跑手册-DeepSeek开发×GLM复核.md"
CARD_DIR = ROOT / "第十五批-goals"
ORDER = ["P1-D", "P2-C", "P3-C", "P5-B", "P5-C", "P6-C", "P6-D", "P7-B", "P7-C", "P10-C"]
BATCH = "BATCH-2026-09-18-第十五批"
D15 = "Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0"
APP_CARDS = {"P1-D", "P5-B"}
FORBIDDEN = ("构造", "可复现片段", "打穿", "绕过")
UNIT_BASE = "unit-red-baseline-9c4e7e82.txt"

ok = True


def fail(msg):
    global ok
    ok = False
    print(f"❌ {msg}")


def main():
    global ok
    if len(ORDER) != 10 or len(set(ORDER)) != 10:
        fail(f"①: ORDER 表应 10 项，实 {len(set(ORDER))}")
        sys.exit(1)
    if not MANUAL.exists():
        fail(f"续跑手册不存在 {MANUAL}")
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
            fail(f"⑪: {key} 不是恰 7 行（{blk.count(chr(10)) + 1} 行）")
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
        for bad in ("gpt-6-astra", "gpt-5.6"):
            if bad in blk:
                fail(f"⑥: {key} 块内出现旧模型串 {bad!r}")
        if "复核第十五批" not in blk:
            fail(f"⑦: {key} 缺「复核第十五批」收尾口令")
        if D15 not in blk:
            fail(f"⑨: {key} 缺 D-15 固定串（GLM 版）")
        if "§2.4" not in blk:
            fail(f"⑭: {key} 块内未引用协议 §2.4")
        if key in APP_CARDS and "pyright 保持 0" not in blk:
            fail(f"⑩: {key} 触及 backend/app 但短 goal 缺「pyright 保持 0」")
        for w in FORBIDDEN:
            if w in blk:
                fail(f"⑫: {key} 块内含禁用词 {w!r}")
        if card.exists():
            ct = card.read_text(encoding="utf-8")
            for anchor in ("本卡未证明什么", "台账待登记条目"):
                if anchor not in ct:
                    fail(f"⑧: {key} 卡文缺「{anchor}」")
            if D15 not in ct:
                fail(f"⑨: {key} 卡文缺 D-15 固定串（GLM 版）")
            if "§2.4" not in ct:
                fail(f"⑭: {key} 卡文未引用协议 §2.4")
            if key in APP_CARDS and "pyright 保持 0" not in ct:
                fail(f"⑩: {key} 触及 backend/app 但卡文缺「pyright 保持 0」")
            for w in FORBIDDEN:
                if w in ct:
                    fail(f"⑫: {key} 卡文含禁用词 {w!r}")
            if UNIT_BASE not in ct or "33" not in ct:
                fail(f"⑬: {key} 卡文缺 unit 红基线 {UNIT_BASE} 或条数 33")
            if "\x00" in ct:
                fail(f"卡文含 NUL 字节 {key}")
    print("GATE:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
