"""负控段⑦ —— 把键级探针的文档改回**单行**（= round-3 之前的状态），验证新门锁住了它。

round-3 复核的 HIGH：单行探针 `harness_tree: <哨兵>` 对一整类**丢文件尾巴**的坏解析器
（缓冲截断 / 流被提前关闭 / 只读前 N 行）没有尾巴可丢 ⇒ 它们照样答对、活过这一层；
配上词法否决只认顶格裸键（`"harness_tree": v` 与 `{harness_tree: v}` 行首都不是它），
两层一起落空 ⇒ 静默回退父树。

⛔ 变异要**同时**改文档与 a/b 校验：只改文档的话，单行文档解析出的 dict 里没有 a/b，
探针会恒失败 ⇒ 所有格都拒 ⇒ 那是「探针恒红」而不是「回到单行探针」，测不到本门。

期望：
  · `..._key_probe_doc_must_be_multiline_with_the_key_last` **红**（结构门，一句话说清）；
  · `..._truncating_parser_is_refused` **三格红**（行为门：截断器重新混过探针层）；
  · `..._truncating_forms_control_group` 三格**仍绿**（真 PyYAML，与探针形态无关）。
"""
p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

OLD_DOC = '_KPROBE_DOC = "a: 1\\nb: 2\\nharness_tree: __quiz_answer_key_probe__\\n"'
NEW_DOC = '_KPROBE_DOC = "harness_tree: __quiz_answer_key_probe__"'
assert t.count(OLD_DOC) == 1, f"探针文档锚应恰 1 处, 实见 {t.count(OLD_DOC)}"
t2 = t.replace(OLD_DOC, NEW_DOC, 1)

OLD_IF = ' and _kprobe.get("a") == 1 and _kprobe.get("b") == 2'
assert t2.count(OLD_IF) == 1, f"a/b 校验锚应恰 1 处, 实见 {t2.count(OLD_IF)}"
t2 = t2.replace(OLD_IF, "", 1)

assert t2 != t, "变异没生效"
assert "_lex = re.search(" in t2, "⛔ 词法否决被波及 = 拆了两层"
assert 'if not (isinstance(_probe, dict) and _probe.get("a") == 1):' in t2, "⛔ 第一道通用探针被波及"
open(p, "w", encoding="utf-8").write(t2)
print(f"段⑦ 变异已注入：键级探针文档改回单行（{len(t) - len(t2)} 字符）")
