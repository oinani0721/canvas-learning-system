# 把 scripts/local_tz.py 的共享段(模块 docstring 之后的全部)同步到 display_tz.py。
# 用法: sync_copies.py check | apply
# 两份文件的唯一合法差异 = 模块 docstring(首个三引号块)。
import sys, hashlib
from pathlib import Path

ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review")
SRC = ROOT / "scripts/local_tz.py"
DST = ROOT / "backend/app/core/display_tz.py"
Q = chr(34) * 3

def split_doc(text):
    assert text.startswith(Q), "file must start with a module docstring"
    end = text.index(Q, 3) + 3
    while end < len(text) and text[end] == "\n":
        end += 1
    return text[:end], text[end:]

src_doc, src_body = split_doc(SRC.read_text(encoding="utf-8"))
dst_doc, dst_body = split_doc(DST.read_text(encoding="utf-8"))

if sys.argv[1:2] == ["apply"]:
    DST.write_text(dst_doc + src_body, encoding="utf-8")
    print(f"applied: display_tz.py body <- local_tz.py body ({len(src_body)} bytes)")
    dst_doc, dst_body = split_doc(DST.read_text(encoding="utf-8"))

same = src_body == dst_body
print(f"bodies identical: {same}")
print(f"  src body sha256 {hashlib.sha256(src_body.encode()).hexdigest()[:16]}  {len(src_body)} bytes")
print(f"  dst body sha256 {hashlib.sha256(dst_body.encode()).hexdigest()[:16]}  {len(dst_body)} bytes")
if not same:
    import difflib
    for i, ln in enumerate(difflib.unified_diff(src_body.splitlines(), dst_body.splitlines(), "local_tz", "display_tz", lineterm="")):
        print(ln)
        if i > 30:
            print("...")
            break
    sys.exit(1)
