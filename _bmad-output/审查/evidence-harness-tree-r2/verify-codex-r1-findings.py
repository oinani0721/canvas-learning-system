"""独立验证 Codex round-1 在 stderr 里留下的三个实测发现（不采信，自己跑一遍）。

三条待验：
  A. `"harness_tree": <target>`（引号键）    + 恒返 {"a":1} 的假模块 ⇒ 声称「静默回退父树」
  B. `{harness_tree: <target>}`（flow）      + 同上                  ⇒ 声称「静默回退父树」
  C. `note: "open\nharness_tree: /a/b"`      + **真 PyYAML**         ⇒ 声称「误拒」

夹具与本卡测试同法：AST 从 SKILL.md 逐字抽 `_harness_tree`，tmp_path 派生，零 live。
"""

import ast
import re
import sys
import tempfile
import types
from pathlib import Path

WT = Path(__file__).resolve()
ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w")
SKILL = ROOT / "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
TEXT = SKILL.read_text(encoding="utf-8")
BLOCKS = re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", TEXT, re.S)
CODE = next(b for b in BLOCKS if 'P = "/tmp/quiz-answer-payload.json"' in b)


def extract():
    mod = ast.parse(CODE)
    fns = [n for n in mod.body if isinstance(n, ast.FunctionDef) and n.name == "_harness_tree"]
    assert len(fns) == 1
    cut = fns[0].lineno
    ns: dict = {}
    for st in mod.body:
        if isinstance(st, (ast.Import, ast.ImportFrom)) and st.lineno < cut:
            exec(compile(ast.Module(body=[st], type_ignores=[]), "<p>", "exec"), ns)
    exec(compile(ast.Module(body=fns, type_ignores=[]), "<h>", "exec"), ns)
    return ns["_harness_tree"]


def fake_constant_a1():
    m = types.ModuleType("yaml")
    m.safe_load = lambda _s, *a, **k: {"a": 1}
    return m


import yaml as REAL_YAML  # noqa: E402

CASES = [
    ("A 引号键 + 恒返{'a':1}", '"harness_tree": {target}\n', "fake"),
    ("B flow mapping + 恒返{'a':1}", "{{harness_tree: {target}}}\n", "fake"),
    ("C 值内跨行文本 + 真 PyYAML", 'note: "open\nharness_tree: /a/b"\n', "real"),
    ("D 裸键 + 恒返{'a':1}（对照：应被拒）", "harness_tree: {target}\n", "fake"),
    ("E 引号键 + 真 PyYAML（对照：应采用）", '"harness_tree": {target}\n', "real"),
    ("F flow + 真 PyYAML（对照：应采用）", "{{harness_tree: {target}}}\n", "real"),
]

fn = extract()
print(f"{'形态':38s} {'结局':6s} 值 / 拒因首段")
print("-" * 118)
for name, tmpl, parser in CASES:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vd = root / "canvas-vault"
        vd.mkdir()
        (root / "backend" / "scripts").mkdir(parents=True)          # 父树可用 ⇒ 静默回退会「成功」
        target = root / "target-tree"
        (target / "backend" / "scripts").mkdir(parents=True)
        raw = tmpl.format(target=target) if "{target}" in tmpl else tmpl
        (vd / ".canvas-config.yaml").write_text(raw, encoding="utf-8")

        saved = sys.modules.get("yaml")
        sys.modules["yaml"] = fake_constant_a1() if parser == "fake" else REAL_YAML
        try:
            got = fn(str(vd))
            if got == str(root):
                verdict, detail = "OK", f"⛔ 回退父树（config 指着 {target.name}）"
            elif got == str(target):
                verdict, detail = "OK", "✓ 采用了 config 指的那棵树"
            else:
                verdict, detail = "OK", got
        except SystemExit as e:
            verdict, detail = "EXIT", str(e).split(" — ")[0][:78]
        finally:
            if saved is not None:
                sys.modules["yaml"] = saved
        print(f"{name:38s} {verdict:6s} {detail}")
