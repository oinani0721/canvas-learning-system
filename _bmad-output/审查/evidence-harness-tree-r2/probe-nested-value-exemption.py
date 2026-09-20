"""实测：`_in_value` 豁免对**嵌套结构里的字符串值**是否仍成立（验收单 §五⓪ 的未证明项）。

判据只遍历 `_doc.values()` 的直接层，嵌套一层的值不在其中 —— 本脚本证实/证伪这一点。
"""
import ast, re, sys, tempfile, types
from pathlib import Path

ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w")
TEXT = (ROOT / "canvas-vault/.claude/skills/quiz-answer/SKILL.md").read_text(encoding="utf-8")
CODE = next(b for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", TEXT, re.S)
            if 'P = "/tmp/quiz-answer-payload.json"' in b)
mod = ast.parse(CODE)
fns = [n for n in mod.body if isinstance(n, ast.FunctionDef) and n.name == "_harness_tree"]
ns = {}
for st in mod.body:
    if isinstance(st, (ast.Import, ast.ImportFrom)) and st.lineno < fns[0].lineno:
        exec(compile(ast.Module(body=[st], type_ignores=[]), "<p>", "exec"), ns)
exec(compile(ast.Module(body=fns, type_ignores=[]), "<h>", "exec"), ns)
fn = ns["_harness_tree"]

import yaml as RY

CASES = [
    ("顶层字符串值内（已修，应回退）", 'note: "open\nharness_tree: /a/b"\n'),
    ("嵌套 list 内的字符串值",        'items:\n  - "open\nharness_tree: /a/b"\n'),
    ("嵌套 dict 内的字符串值",        'outer:\n  inner: "open\nharness_tree: /a/b"\n'),
]
print(f"{'形态':32s} {'lex':5s} {'顶层有键':8s} {'结局':6s} 说明")
print("-" * 104)
for name, raw in CASES:
    lex = bool(re.search(r"^harness_tree[ \t]*:", raw, re.M))
    try:
        doc = RY.safe_load(raw); parsed_ok = True
    except Exception as e:
        doc, parsed_ok = None, False
    has = isinstance(doc, dict) and "harness_tree" in doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); vd = root / "canvas-vault"; vd.mkdir()
        (root / "backend" / "scripts").mkdir(parents=True)
        (vd / ".canvas-config.yaml").write_text(raw, encoding="utf-8")
        try:
            got = fn(str(vd))
            verdict = "OK"
            note = "✓ 回退父树（未误拒）" if got == str(root) else got
        except SystemExit as e:
            verdict = "EXIT"
            note = "⚠️ 被拒 —— " + ("解析本就失败, 属既有 fail-closed" if not parsed_ok else "**误拒面**")
    print(f"{name:32s} {str(lex):5s} {str(has):8s} {verdict:6s} {note}")
