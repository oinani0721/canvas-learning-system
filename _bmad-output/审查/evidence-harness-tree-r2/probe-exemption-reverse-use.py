"""实证：词法否决的「值内豁免」能否被**反向利用**（自查 + workflow ①c 交叉）。

形态：config 顶层**真的写了** harness_tree，而文档里另有一个值含 `harness_tree:` 子串。
豁免条件是「命中串出现在某个值内」⇒ 豁免生效 ⇒ 词法否决不触发 ⇒ 解析器谎报无键时
静默回退父树 = r10 H1 的原结局在豁免面上复活。

对照三格：decoy 在 / decoy 不在 / 真 PyYAML（证明 config 本身没写错）。
"""
import ast, re, sys, tempfile, types
from pathlib import Path

ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w")
TEXT = (ROOT / "canvas-vault/.claude/skills/quiz-answer/SKILL.md").read_text(encoding="utf-8")
CODE = next(b for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", TEXT, re.S)
            if 'P = "/tmp/quiz-answer-payload.json"' in b)
_mod = ast.parse(CODE)
_fns = [n for n in _mod.body if isinstance(n, ast.FunctionDef) and n.name == "_harness_tree"]
_ns = {}
for _st in _mod.body:
    if isinstance(_st, (ast.Import, ast.ImportFrom)) and _st.lineno < _fns[0].lineno:
        exec(compile(ast.Module(body=[_st], type_ignores=[]), "<p>", "exec"), _ns)
exec(compile(ast.Module(body=_fns, type_ignores=[]), "<h>", "exec"), _ns)
fn = _ns["_harness_tree"]

import yaml as RY
KEY_PROBE = "harness_tree: __quiz_answer_key_probe__"


def honest_fake(file_answer):
    """对两道探针都老实、只对用户这份 config 说谎（= 活得过键级探针那一层）。"""
    m = types.ModuleType("yaml")
    def sl(s, *a, **k):
        if s in ("a: 1", KEY_PROBE):
            return RY.safe_load(s)
        return file_answer
    m.safe_load = sl
    return m


CASES = [
    ("A 有 decoy 值含该子串 + 谎报无键", True,  "fake"),
    ("B 无 decoy（对照）+ 谎报无键",     False, "fake"),
    ("C 有 decoy + 真 PyYAML（对照）",   True,  "real"),
]
print(f"{'形态':38s} {'结局':6s} 说明")
print("-" * 104)
for name, with_decoy, parser in CASES:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); vd = root / "canvas-vault"; vd.mkdir()
        (root / "backend" / "scripts").mkdir(parents=True)          # 父树可用 ⇒ 静默回退会「成功」
        tgt = root / "target-tree"; (tgt / "backend" / "scripts").mkdir(parents=True)
        decoy = 'decoy: "见文档 harness_tree: 的说明"\n' if with_decoy else ""
        raw = f"{decoy}harness_tree: {tgt}\n"
        (vd / ".canvas-config.yaml").write_text(raw, encoding="utf-8")

        truth = RY.safe_load(raw)
        assert "harness_tree" in truth, "前提没成立: 顶层没有这个键"

        lie = {"decoy": "见文档 harness_tree: 的说明"} if with_decoy else {}
        saved = sys.modules.get("yaml")
        sys.modules["yaml"] = honest_fake(lie) if parser == "fake" else RY
        try:
            got = ("ok", fn(str(vd)))
        except SystemExit as e:
            got = ("exit", str(e))
        finally:
            if saved is not None:
                sys.modules["yaml"] = saved

        if got[0] == "ok" and str(got[1]) == str(root):
            note = "⚠️⚠️ 未被拦下的输入：静默回退父树（config 指着 target-tree）"
        elif got[0] == "ok" and str(got[1]) == str(tgt.resolve()):
            note = "✓ 采用了 config 指的那棵树"
        elif got[0] == "exit":
            note = "✓ 被拒：" + got[1].split(" — ")[0][:52]
        else:
            note = str(got[1])
        print(f"{name:38s} {got[0]:6s} {note}")
