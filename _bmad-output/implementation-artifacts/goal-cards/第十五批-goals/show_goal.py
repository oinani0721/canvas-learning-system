#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取第十五批某张卡的短 goal 粘贴文本（唯一真相源 = 手册 §三，本脚本只读不改，杜绝副本漂移）。

用法：
    python3 show_goal.py P1-A            # 打印到屏幕
    python3 show_goal.py P1-A | pbcopy   # macOS：直接进剪贴板，然后 Cmd+V 粘进 /goal
    python3 show_goal.py                 # 列出全部 33 个块名与字符数
"""
import re
import sys
from pathlib import Path

MANUAL = Path(__file__).resolve().parent.parent / "2026-09-18-第十五批开跑手册-11车道33卡.md"


def blocks():
    lines = MANUAL.read_text(encoding="utf-8").splitlines()
    i3 = next(i for i, l in enumerate(lines) if l.startswith("## 三、"))
    i4 = next(i for i, l in enumerate(lines) if l.startswith("## 四、"))
    out, key = {}, None
    fence, buf = False, []
    for l in lines[i3:i4]:
        m = re.match(r"^### (P\d+b?-[A-G])（(.+)）\s*$", l)
        if m:
            key = m.group(1)
            out[key] = {"card": m.group(2), "text": None}
            continue
        if l.strip() == "```":
            if fence:
                if key and out[key]["text"] is None:
                    out[key]["text"] = "\n".join(buf)
                fence, buf = False, []
            else:
                fence = True
            continue
        if fence:
            buf.append(l)
    return out


def main():
    bs = blocks()
    if len(sys.argv) < 2:
        print(f"# 第十五批 33 个短 goal（源：{MANUAL.name} §三）\n")
        for k, v in bs.items():
            print(f"{k:8s} {v['card']:40s} {len(v['text'] or ''):5d} 字符")
        print("\n用法：python3 show_goal.py <块名> | pbcopy   然后在车道标签页 Cmd+V 粘进 /goal")
        return 0
    key = sys.argv[1].strip()
    key = re.sub(r"^p", "P", key)                                   # p1-a → P1-a
    key = re.sub(r"-([a-g])$", lambda m: "-" + m.group(1).upper(), key)  # P1-a → P1-A（P2b 的 b 保持小写）
    if key not in bs:
        print(f"没有块 {key}；可用：{' '.join(bs)}", file=sys.stderr)
        return 2
    t = bs[key]["text"]
    if not t:
        print(f"块 {key} 解析为空（手册 §三 格式被改过？）", file=sys.stderr)
        return 3
    sys.stdout.write(t + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
