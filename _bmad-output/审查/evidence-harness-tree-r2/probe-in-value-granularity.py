"""独立验证 workflow 复核的 HIGH：`_in_value` 的粒度错误。

主张：`_in_value` 是**整份文档一个布尔**、且只用 `_lex` 的**第一处**命中文本去匹配。
只要已解析结果里**任意一个字符串**含该串，词法否决就对文件里**每一处**命中一起失效
—— 包括真正的顶层 harness_tree 键。

⛔ 关键在触发条件：workflow 用的是**截断式解析器**（只读前 N 行 = 缓冲/流截断类事故的
形态，**不是敌意模块**），config 是一份**普通的单行自文档**写法。若成立，这条落在
docstring 声称「防得住」的「意外损坏的 yaml」**范围之内**，不是已登记的威胁模型之外。
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


def truncating_yaml(n_lines):
    """**非敌意**的坏解析器：只读前 n 行（缓冲截断 / 流被提前关闭的形态）。
    两道探针都是单行文档 ⇒ 它照样答对，活得过键级探针那一层。"""
    m = types.ModuleType("yaml")
    def sl(s, *a, **k):
        return RY.safe_load("\n".join(str(s).splitlines()[:n_lines]))
    m.safe_load = sl
    return m


def run(label, raw, parser):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); vd = root / "canvas-vault"; vd.mkdir()
        (root / "backend" / "scripts").mkdir(parents=True)     # 父树可用 ⇒ 静默回退会「成功」
        tgt = root / "target-tree"; (tgt / "backend" / "scripts").mkdir(parents=True)
        text = raw.replace("<TGT>", str(tgt))
        (vd / ".canvas-config.yaml").write_text(text, encoding="utf-8")

        truth = RY.safe_load(text)
        has_real_key = isinstance(truth, dict) and "harness_tree" in truth

        saved = sys.modules.get("yaml")
        sys.modules["yaml"] = parser
        try:
            got = ("ok", fn(str(vd)))
        except SystemExit as e:
            got = ("exit", str(e))
        finally:
            if saved is not None:
                sys.modules["yaml"] = saved

        if got[0] == "ok" and str(got[1]) == str(root):
            verdict = "⚠️⚠️ 静默回退父树"
        elif got[0] == "ok" and str(got[1]) == str(tgt.resolve()):
            verdict = "✓ 采用 config 指的树"
        elif got[0] == "exit":
            verdict = "✓ 拒: " + got[1].split(" — ")[0][-46:]
        else:
            verdict = str(got[1])
        print(f"{label:44s} 真键在={str(has_real_key):5s} {verdict}")


# 一份**普通的单行自文档 config** —— 没有跨行标量、没有刻意设计
SELF_DOC = 'vault_id: v\nnote: "改这里的 harness_tree: 就能换树"\nharness_tree: <TGT>\n'
NO_DECOY = 'vault_id: v\nnote: "改这里的那一行就能换树"\nharness_tree: <TGT>\n'

print(f"{'形态':44s} {'':11s} 结局")
print("-" * 104)
print("── 坏环境 = 截断式解析器（只读前 2 行，非敌意） ──")
run("C 自文档 note 含该串 + 截断解析器", SELF_DOC, truncating_yaml(2))
run("D 对照：note 不含该串 + 同一截断解析器", NO_DECOY, truncating_yaml(2))
print("── 健康环境对照（真 PyYAML） ──")
run("E 自文档 note 含该串 + 真 PyYAML", SELF_DOC, RY)
run("F 只有值内那串字、无真键 + 真 PyYAML", 'note: "见 harness_tree: 说明"\n', RY)
print()
print("判读：C 静默回退 ∧ D 被拒 ⇒ 差别只在「那串字在不在某个值里」⇒ 豁免被钉成因。")
print("      E/F 绿 ⇒ 健康环境零影响（既不误拒也不误采）。")
print("      截断式解析器是**意外损坏**的形态，docstring :487-489 把它列在「防得住」里。")
