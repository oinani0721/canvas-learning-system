#!/usr/bin/env python3
"""CARD-G6-13 脱敏: 去绝对路径 (只留文件名/摘要/桶/日期)。用法: sanitize.py <in> <out>"""
import re, sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
t = src.read_text(encoding="utf-8", errors="replace")
t = t.replace("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review", "<tree>")
t = t.replace("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees", "<worktrees>")
t = t.replace("/Users/Heishing/Desktop/canvas/canvas-learning-system", "<repo>")
t = t.replace("/Users/Heishing", "<home>")
t = re.sub(r"/private/var/folders/[^\s\"']+", "<tmp>", t)
t = re.sub(r"/private/tmp/g613\.[A-Za-z0-9]+", "<tmp>", t)
t = re.sub(r"/private/tmp/[A-Za-z0-9._-]*g613[A-Za-z0-9._-]*", "<tmp>", t)
t = re.sub(r"/tmp/g613\.[A-Za-z0-9]+", "<tmp>", t)
t = re.sub(r"/tmp/[A-Za-z0-9._-]*g613[A-Za-z0-9._-]*", "<tmp>", t)
t = re.sub(r"/opt/homebrew/[^\s\"']+", "<python>", t)
dst.write_text(t, encoding="utf-8")
print(f"sanitized {src.name} -> {dst} ({len(t)} chars)")
