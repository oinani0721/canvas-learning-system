"""负控段⑤ —— 把 round-1 那个「值内豁免」**加回去**（v2 形态），验证新门确实锁住了它。

round-2 复核抓到的 HIGH 就是这个豁免：它是**整份文档一个布尔**，一处命中落在某个值内
就让整份文件的否决失效。本段把它原样注入回去，期望：

  · `..._truncating_parser_cannot_disarm_the_veto` **红** —— 它正是为钉住这个 HIGH 而立的门；
  · `..._truncating_parser_control_group` **仍绿** —— 对照组的 note 不含那串字，豁免不触发；
  · `..._lexical_veto_false_refusal_cost_is_accepted` 三格**翻绿→红**（期望是「被拒」，
    加回豁免后它们不再被拒）—— 这三格钉的是「已知代价」，豁免回来代价就没了，所以红；
  · `constant_*` 三格与两个控制组**仍绿** —— 它们靠键级探针/真 PyYAML，与豁免无关。
"""
import re

p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

ANCHOR = '        if _lex and (not isinstance(_doc, dict) or "harness_tree" not in _doc):\n'
assert t.count(ANCHOR) == 1, f"锚点应恰 1 处, 实见 {t.count(ANCHOR)}"

EXEMPTION = '''        _in_value = False
        if _lex:
            _needle, _stack, _seen = _lex.group(0), [_doc], set()
            while _stack:
                _node = _stack.pop()
                if id(_node) in _seen:
                    continue
                _seen.add(id(_node))
                if isinstance(_node, str):
                    if _needle in _node:
                        _in_value = True
                        break
                elif isinstance(_node, dict):
                    _stack.extend(_node.keys())
                    _stack.extend(_node.values())
                elif isinstance(_node, (list, tuple, set)):
                    _stack.extend(_node)
'''
NEW_IF = '        if _lex and not _in_value and (not isinstance(_doc, dict) or "harness_tree" not in _doc):\n'
t2 = t.replace(ANCHOR, EXEMPTION + NEW_IF, 1)
assert t2 != t, "变异没生效"
assert "_kprobe = yaml.safe_load(" in t2, "⛔ 键级探针被波及 = 拆了两层"
assert t2.count("_in_value = False") == 1, "⛔ 豁免没注入干净"
open(p, "w", encoding="utf-8").write(t2)
print(f"段⑤ 变异已注入：把 round-1 的值内豁免加回去（+{len(t2) - len(t)} 字符）")
