"""负控段⑧ —— 只删掉键级探针对 `a` / `b` 两项的校验（round-4 L1 的守卫）。

那两项是唯一拦得住「丢**头**」类损坏（只解析最后 N 行）的判据：对三行探针，丢头的解析器
只读到 `harness_tree: <哨兵>` ⇒ 那个键的校验照样过。

期望：`..._tail_only_parser_is_refused` **红**；其余格（丢尾类 / 契约 / 误拒代价）**全绿**。
"""
p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

OLD = ' and _kprobe.get("a") == 1 and _kprobe.get("b") == 2'
assert t.count(OLD) == 1, f"锚应恰 1 处, 实见 {t.count(OLD)}"
t2 = t.replace(OLD, "", 1)
assert t2 != t, "变异没生效"
assert '_KPROBE_DOC = "a: 1\\nb: 2\\nharness_tree: __quiz_answer_key_probe__\\n"' in t2, "⛔ 探针文档被波及 = 拆了两层"
assert '_kprobe.get("harness_tree") == "__quiz_answer_key_probe__"' in t2, "⛔ 键校验被波及 = 拆了两层"
assert "_lex = re.search(" in t2, "⛔ 词法否决被波及 = 拆了两层"
open(p, "w", encoding="utf-8").write(t2)
print(f"段⑧ 变异已注入：删掉探针的 a/b 两项校验（-{len(t) - len(t2)} 字符）")
