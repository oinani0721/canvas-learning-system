"""负控段① —— 只删掉**词法否决**那一个分支（键级探针那一层原样保留）。

只拆这一层：`_lex = re.search(...)` 那一行**保留**（证明红不是语法塌方），
删掉的只有「命中、且解析结果无键 ⇒ 拒写」这一个判断本身。
（round-2 整改后豁免已整段去掉，锚从 `if _lex and not _in_value and (` 变回 `if _lex and (`。）

期望（与段④互为对角线）：
  · `..._lying_parser_is_refused[honest_probes_empty_mapping / honest_probes_list]` 红
    —— 这两格的假模块对两道探针都老实，活得过键级探针，只能靠词法否决拦；
  · `[constant_bare / constant_quoted_key / constant_flow_mapping]` **仍绿**
    —— 它们死在键级探针那一层，与本段拆掉的东西无关；
  · 两个控制组仍绿。
"""
import re

p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

ANCHOR = r"^\s*if _lex and \("
n = len(re.findall(ANCHOR, t, re.M))
assert n == 1, f"锚点应恰 1 处, 实见 {n}"
t2 = re.sub(
    ANCHOR + r".*?\n(?:\s+raise SystemExit\(.*?\)\n)",
    "",
    t,
    count=1,
    flags=re.M | re.S,
)
assert t2 != t, "变异没生效"
assert len(re.findall(r"^\s*_lex = re\.search", t2, re.M)) == 1, "⛔ 把 _lex 赋值也删了 = 拆了两层"
assert "_kprobe = yaml.safe_load(" in t2, "⛔ 键级探针被波及 = 拆了两层"
assert "_kprobe = yaml.safe_load(" in t2, "⛔ 键级探针被波及 = 拆了两层"
assert len(re.findall(ANCHOR, t2, re.M)) == 0, "⛔ 分支没删干净"
open(p, "w", encoding="utf-8").write(t2)
print(f"段① 变异已注入：删 {len(t) - len(t2)} 字符（只删词法否决分支，键级探针原样）")
