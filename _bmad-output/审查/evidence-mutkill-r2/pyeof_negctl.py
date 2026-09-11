#!/usr/bin/env python3
"""(i) PYEOF_RE 收紧的等价性 + 负控（只读，不写任何生产文件）。

⚠️ 洞的形态是**实测出来的**，不是照着直觉写的：初稿断言「终止行带尾随空格旧版
匹配不上」，跑出来 FAIL —— 旧写法 `\\nPYEOF` 没有结尾锚，带尾随空格照样匹配。
本脚本保留那一条作**验伪锚**（两版必须一致），只把真的量到的三个洞当负控。

判据两段：
  A) 等价性 —— 对真实 SKILL.md，新旧正则提取到的块**逐块逐字节相同**（收紧不得
     丢覆盖面；丢了的话编译自检会静默变窄 = 假绿）；
  B) 负控   —— 实测到的三种形态上「旧版坏 / 新版对」，外加两条两版必须一致的验伪锚。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend" / "scripts"))
from mutation_kill_identity import PYEOF_RE, syntax_check  # noqa: E402

OLD = re.compile(r"<<'PYEOF'\n(.*?)\nPYEOF", re.DOTALL)
TREE = Path(__file__).resolve().parents[3]
MDS = [
    TREE / "canvas-vault/.claude/skills/quiz-answer/SKILL.md",
    TREE / "canvas-vault/.claude/skills/start-exam-board/SKILL.md",
]

bad = 0
print("── A) 真实 SKILL.md 等价性（收紧不得丢覆盖面）──")
for md in MDS:
    src = md.read_text(encoding="utf-8")
    o, n = OLD.findall(src), PYEOF_RE.findall(src)
    same = o == n
    bad += 0 if same else 1
    print(f"  {md.parent.name}/{md.name}: 旧 {len(o)} 块 / 新 {len(n)} 块 / 逐字节相同={same}")

print("── B) 负控（期望 旧版坏 / 新版对）──")
BAD_SYNTAX = "def f(:\n    pass"


def check(name, text, want_old, want_new):
    global bad
    o, n = OLD.findall(text), PYEOF_RE.findall(text)
    ok = (o == want_old) and (n == want_new)
    bad += 0 if ok else 1
    print(f"  {name}\n      旧={o!r}\n      新={n!r}  ⇒ {'PASS' if ok else '⛔FAIL'}")
    return o, n


# 洞①：块内行首 `PYEOFX` ⇒ 旧版提前截断，坏语法藏在被截掉的后半段里
body1 = "x = 1\nPYEOFX = 2\n" + BAD_SYNTAX
s1 = "cmd <<'PYEOF'\n" + body1 + "\nPYEOF\n"
check("洞① 块内行首 PYEOFX ⇒ 旧版提前截断", s1, ["x = 1"], [body1])

# 洞②：引导行带尾随空白 ⇒ 旧版整块提不到 ⇒ 编译自检恒通过（假绿）
s2 = "cmd <<'PYEOF' \n" + BAD_SYNTAX + "\nPYEOF\n"
check("洞② 引导行 `<<'PYEOF' ` 带尾随空白 ⇒ 旧版整块提不到", s2, [], [BAD_SYNTAX])

# 洞③：CRLF ⇒ 旧版整块提不到（与洞②同一个假绿面）
s3 = "cmd <<'PYEOF'\r\n" + BAD_SYNTAX.replace("\n", "\r\n") + "\r\nPYEOF\r\n"
check("洞③ CRLF 行尾 ⇒ 旧版整块提不到", s3, [], [BAD_SYNTAX.replace("\n", "\r\n")])

print("── 验伪锚（两版必须一致；否则「新版更对」可能只是恒不匹配）──")
check("验伪锚1 普通形态", "cmd <<'PYEOF'\nprint(1)\nPYEOF\n", ["print(1)"], ["print(1)"])
# ⚠️ 这一条是初稿写错的那个断言，保留为验伪锚：实测两版**相同**。
check("验伪锚2 终止行带尾随空格(初稿曾误判为洞)", "cmd <<'PYEOF'\nprint(1)\nPYEOF  \n", ["print(1)"], ["print(1)"])

print("── C) 覆盖面丢失的后果（洞②③ 为什么比洞① 更糟）──")
for nm, s in (("洞②", s2), ("洞③", s3)):
    err_new = syntax_check(Path("x.md"), s)
    n_old = len(OLD.findall(s))
    ok = (err_new is not None) and n_old == 0
    bad += 0 if ok else 1
    print(f"  {nm}: 旧版提取 {n_old} 块 ⇒ 编译自检**恒通过**; 新版报 {err_new!r} ⇒ {'PASS' if ok else '⛔FAIL'}")

print(f"VERDICT: {'PASS' if bad == 0 else f'FAIL({bad})'}")
sys.exit(0 if bad == 0 else 1)
