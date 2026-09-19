#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取第十五批**续跑段**某张卡的短 goal 粘贴文本（唯一真相源 = 续跑手册 §三；本脚本只读不改）。

用法：
    python3 show_goal_b15b.py P1-D            # 打印到屏幕
    python3 show_goal_b15b.py P1-D | pbcopy   # macOS：直接进剪贴板，然后 Cmd+V 粘成普通消息（无 /goal 前缀）
    python3 show_goal_b15b.py                 # 列出全部 20 个块名与字符数
"""
import re
import sys
from pathlib import Path

MANUAL = Path(__file__).resolve().parent.parent / "2026-09-19-第十五批续跑手册-DeepSeek开发×GLM复核.md"


def blocks():
    lines = MANUAL.read_text(encoding="utf-8").splitlines()
    i3 = next(i for i, l in enumerate(lines) if l.startswith("## 三、"))
    i4 = next(i for i, l in enumerate(lines) if l.startswith("## 四、"))
    out, key = {}, None
    fence, buf = False, []
    for l in lines[i3:i4]:
        m = re.match(r"^### (P\d+b?-[A-G]|补审-[A-Za-z0-9-]+)（(.+)）\s*$", l)
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
        for k, v in bs.items():
            t = v["text"] or ""
            print(f"{k:8s} {len(t):5d} 字符  {v['card']}")
        return
    k = sys.argv[1]
    if k not in bs or bs[k]["text"] is None:
        sys.exit(f"没有块 {k!r}；可选：{', '.join(bs)}")
    print(bs[k]["text"])


if __name__ == "__main__":
    main()
