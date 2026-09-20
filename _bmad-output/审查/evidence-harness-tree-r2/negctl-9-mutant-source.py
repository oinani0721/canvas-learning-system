"""负控段⑨ —— 只删掉契约门形状层的 `isinstance(..., re.Pattern)` 两行（round-4 L2 的守卫）。

它是唯一拦得住「不是编译正则、但把 fullmatch 委托给真正则」的包装对象的判据 ——
四条行为探针那种对象全答得对。

期望：`..._harness_contract_refuses_a_non_pattern_wrapper` **红**；
      其余六格契约负控与控制组 `..._accepts_real_tree` **全绿**。
"""
import re

p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

ANCHOR = r'^\s*for _n in \("_TS_RE", "_WHOLE_SECOND_RE"\):\n\s*if not isinstance\(getattr\(_vle, _n\), re\.Pattern\):\n\s*_refuse\("不是编译正则".*?\n'
n = len(re.findall(ANCHOR, t, re.M | re.S))
assert n == 1, f"锚应恰 1 处, 实见 {n}"
t2 = re.sub(ANCHOR, "", t, count=1, flags=re.M | re.S)
assert t2 != t, "变异没生效"
assert 'if not callable(getattr(_vle, _n)):' in t2, "⛔ callable 检查被波及 = 拆了两层"
assert 'if not hasattr(_vle, _n):' in t2, "⛔ hasattr 检查被波及 = 拆了两层"
assert '_vle._TS_RE.fullmatch("2026-08-01T10:00:00Z")' in t2, "⛔ 行为探针被波及 = 拆了两层"
open(p, "w", encoding="utf-8").write(t2)
print(f"段⑨ 变异已注入：删掉形状层的 isinstance(re.Pattern) 两行（-{len(t) - len(t2)} 字符）")
