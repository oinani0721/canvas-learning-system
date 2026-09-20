"""负控段⑥ —— 只删掉预检块的 `sys.dont_write_bytecode = True`，验证 `__pycache__` 门真能抓到。

round-2 复核的 MEDIUM-4：预检声称「纯读零写」，但 `_harness_contract` 会 import validator，
真实用户环境里没有 `PYTHONDONTWRITEBYTECODE` ⇒ Python 往选中的 harness 树落 `__pycache__`。
整改把保证放进预检块自己，并把门改成按真实用户环境跑。本段删掉那一行，期望门红。

期望：`..._preflight_passes_on_a_good_vault`（控制组，一路走到 import validator，最会落盘）
      与 `..._preflight_refuses_before_step3[contract_broken]`（也会 import）**红在
      `_pycache_dirs(...) == []` 那条断言**。

⚠️ 实测更正（初版预测 `[no_pyyaml]` 仍绿，错了）：它**也红**，落点是
   `['no-yaml/__pycache__']` —— 那一格用 `PYTHONPATH` 前置一个「导入即抛」的 `yaml.py`，
   Python 在尝试导入它的过程中就把字节码写进了那个 stub 目录。所以落盘面比
   「走到 import validator」更宽：**只要 import 过任何东西**就可能落。
   `[bad_tree]` 与 env 缺失那格仍绿（它们在任何 import 之前就拒了）。
"""
p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

ANCHOR = "sys.dont_write_bytecode = True\n"
assert t.count(ANCHOR) == 1, f"锚点应恰 1 处, 实见 {t.count(ANCHOR)}"
t2 = t.replace(ANCHOR, "", 1)
assert t2 != t, "变异没生效"
assert 'NODE = os.environ.get("QUIZ_ANSWER_NODE", "")' in t2, "⛔ 把别的行也删了 = 拆了两层"
assert "_kprobe = yaml.safe_load(" in t2, "⛔ 键级探针被波及 = 拆了两层"
open(p, "w", encoding="utf-8").write(t2)
print(f"段⑥ 变异已注入：删掉预检块的 sys.dont_write_bytecode（-{len(t) - len(t2)} 字符）")
