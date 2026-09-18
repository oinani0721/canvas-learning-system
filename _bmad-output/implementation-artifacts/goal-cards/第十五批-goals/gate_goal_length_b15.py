#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十五批手册 §三 短 goal 长度门（复制前必跑；主 session 与车道均可跑）。
① 块数 = 33；② 每块 len() ≤ 3800（/goal 硬限 4000 字符，留 200 缓冲——数字符不数字节）；
③ 每块含对应卡文绝对路径且文件存在；④ 每块含批次标记与「不 push」；⑤ 每块以 /goal 开头；
⑥ 每块与卡文都不得出现 gpt-5.6；⑦ 每块含「复核第十五批」收尾口令；
⑧ 卡文含「本卡未证明什么」与「台账待登记条目」两个必填锚；
⑨ 每块与卡文含 D-15 固定串；⑩ 触及 backend/app 的卡（APP_CARDS）卡文与短 goal 含「pyright 保持 0」；
⑪ 卡文与短 goal 不得含旧口径字面量；⑫ 每块恰 7 行；⑬ 两文件不得含协议 §2 四个禁用词；⑭ 卡文含 unit 红基线路径与「33」。
本门不比什么：不校验短 goal 概要与卡文语义一致；不校验卡文里的 file:line 是否仍在主干成立（那是阶段二复核 agent 与车道第 0 分钟的活）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # goal-cards/
MANUAL = ROOT / "2026-09-18-第十五批开跑手册-11车道33卡.md"
CARD_DIR = ROOT / "第十五批-goals"
ORDER = ["P1-A", "P1-B", "P1-C", "P1-D",
         "P2-A", "P2-B", "P2-C",
         "P3-A", "P3-B", "P3-C",
         "P4-A", "P4-B", "P4-C",
         "P5-A", "P5-B", "P5-C",
         "P6-A", "P6-B", "P6-C", "P6-D",
         "P7-A", "P7-B", "P7-C",
         "P8-A", "P8-B", "P8-C",
         "P9-A", "P9-B", "P9-C",
         "P10-A", "P10-B", "P10-C",
         "P2b-A"]
BATCH = "BATCH-2026-09-18-第十五批"
D15 = "Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0"
APP_CARDS = {"P1-A", "P1-B", "P1-C", "P1-D", "P2-A", "P2-B", "P4-A", "P4-B", "P5-A", "P5-B", "P8-A", "P8-B", "P2b-A"}  # 13 张（阶段一 manifest touches_backend_app）
OLD_LITERALS = (":1281", "mutation_kill_identity.py:203", "stale-mock", "cd backend && .venv/bin/pyright", "unit-red-baseline-08100483", "NEW @ 65b2ed65")
FORBIDDEN = ("构造", "可复现片段", "打穿", "绕过")  # 协议 §2：prompt 与卡文禁用（以「负控输入/对照输入/未被拦下的输入/门未覆盖的路径」代替）
UNIT_BASE = "unit-red-baseline-9c4e7e82.txt"

ok = True


def fail(msg):
    global ok
    ok = False
    print(f"❌ {msg}")


def main():
    global ok
    if len(ORDER) != 33 or len(set(ORDER)) != 33:
        fail(f"①: ORDER 表 {len(ORDER)} 项 / 去重 {len(set(ORDER))}，应为 33")
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
            fail(f"⑫: {key} 不是恰 7 行（{blk.count(chr(10)) + 1} 行）")
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
        if "复核第十五批" not in blk:
            fail(f"⑦: {key} 缺「复核第十五批」收尾口令")
        if D15 not in blk:
            fail(f"⑨: {key} 缺 D-15 固定串")
        if key in APP_CARDS and "pyright 保持 0" not in blk:
            fail(f"⑩: {key} 触及 backend/app 但短 goal 缺「pyright 保持 0」")
        for lit in OLD_LITERALS:
            if lit in blk:
                fail(f"⑪: {key} 块内含旧口径字面量 {lit!r}")
        for w in FORBIDDEN:
            if w in blk:
                fail(f"⑬: {key} 块内含禁用词 {w!r}")
        if card.exists():
            ct = card.read_text(encoding="utf-8")
            # 放行判据形态 `grep -c 'gpt-5.6'`（卡文 §二「存档内旧模型名计数 → 0」的检查命令本身含该串，第十四批同款）；其余出现 = 违规
            if "gpt-5.6" in ct.replace("grep -c 'gpt-5.6'", ""):
                fail(f"⑥: {key} 卡文出现 gpt-5.6（非 grep -c 判据形态）")
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
            for w in FORBIDDEN:
                if w in ct:
                    fail(f"⑬: {key} 卡文含禁用词 {w!r}")
            if UNIT_BASE not in ct or "33" not in ct:
                fail(f"⑭: {key} 卡文缺 unit 红基线 {UNIT_BASE} 或条数 33")
            if "\x00" in ct:
                fail(f"卡文含 NUL 字节 {key}")
    print("GATE:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
