"""负控段④ —— 只删掉**键级探针**那一个判断（词法否决那一层原样保留）。

只拆这一层：`_kprobe = yaml.safe_load(...)` 那一行**保留**（证明红不是 NameError），
删掉的只有「它给不出这个键 ⇒ raise ImportError」这个判断本身。

期望（与段① 互为对角线）：
  · `..._lying_parser_is_refused[constant_quoted_key / constant_flow_mapping]` 红
    —— 这两格正是 round-1 复核抓到的未被拦下的输入，词法正则对它们行首不命中，
      只有键级探针拦得住；
  · `[honest_probes_empty_mapping / honest_probes_list]` **仍绿** —— 它们靠词法否决；
  · `[constant_bare]` **也红，但红在另一条断言上** ——

⚠️ 实测更正（本脚本初版预测它仍绿，按实测改的是预测不是判据）：`constant_bare` 确实
**仍被拦住了**（裸键写法词法正则命中，词法否决接住了它），但拒因从「读不出本写点唯一
关心的那个键」变成了「解析结果与文件内容不符」⇒ 该格的 `want` 断言红，正文写着
「拒因跑到另一层 = 这一格实际测的不是它声称的那道判据」。这正是那条断言的用意。

⇒ 由此得出一条比预测更有信息量的结论：**两层有重叠但不等价** —— 裸键写法两层都拦得住，
而 `"harness_tree": v`（引号键）与 `{harness_tree: v}`（flow mapping）这两种写法
**只有键级探针拦得住**（它们在本段下红在「返回了一棵树」，是真的没拦住）。
"""
import re

p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

#: ⛔ 锚只钉 `if not (isinstance(_kprobe, dict)` 这一段前缀，**不钉整条条件** ——
#: 条件本身会随生产演进（round-3 给它加了 a/b 两项校验），钉整条必然漂。
#: 本卡这条锚漂过一次（round-3 之后注入失败），是脚本自己的 assert 抛出来才发现的。
ANCHOR = r'^\s*if not \(isinstance\(_kprobe, dict\)'
n = len(re.findall(ANCHOR, t, re.M))
assert n == 1, f"锚点应恰 1 处, 实见 {n}"
t2 = re.sub(ANCHOR + r".*?\n(?:\s+raise ImportError\(.*?\)\n)", "", t, count=1, flags=re.M | re.S)
assert t2 != t, "变异没生效"
assert "_kprobe = yaml.safe_load(" in t2, "⛔ 把探针调用也删了 = 拆了两层"
assert len(re.findall(r"^\s*if _lex and \(", t2, re.M)) == 1, "⛔ 词法否决被波及 = 拆了两层"
#: ⚠️ 这条自检的锚在 round-2 整改（豁免整段去掉）后变过一次：`if _lex and not _in_value and (`
#: → `if _lex and (`。当时锚没跟上 ⇒ 变异**没注入** ⇒ 后续 pytest 全绿看起来像「负控通过」，
#: 实际什么都没测。是这条 assert 自己抛出来才被发现 —— 变异脚本的自检不是装饰。
assert 'if not (isinstance(_probe, dict) and _probe.get("a") == 1):' in t2, "⛔ 第一道通用探针被波及"
open(p, "w", encoding="utf-8").write(t2)
print(f"段④ 变异已注入：删 {len(t) - len(t2)} 字符（只删键级探针的判断，词法否决原样）")
