# CARD-G5-6c 第七轮终审报告（自 stderr 抢救）

> ⛔ 本轮 stdout 为 **0 字节** —— codex 内容过滤器拦下了输出，正文自 stderr 抢救。
> 按卡文「stdout 0 字节…一律不合并」，本轮无论结论如何都不改变「不合并」。
> ⚠️ 抢救时先抓错过一次：stderr 里既有 codex **读入**的历史报告、也有它的输出，
> 第一次 `rfind('# CARD-G5-6c')` 抓到的是 round-3 报告的回显。真正的输出锚点是
> 末尾 ERROR 之前的那段（字节区间 569511–593303），已按此重取。

# 一、历史反例复核

统一复现命令：

```sh
ROOT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox
P="$ROOT/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py"
R=/private/tmp/card-g56c-r7-trackA.41zUUP
CASE=round4-exact

python3 -B "$P" \
  --vault "$R/$CASE/vault" \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir "$R/$CASE/out" \
  --batch-size 10

jq -r '.items[] |
  [.name,.criterion,.verdict,(.confident|tostring),
   (.exact_duplicate_of//"null"),(.uncertain_reason//"null")] | @tsv' \
  "$R/$CASE/out/inbox-preview-_待处理.json"
```

## 1.1 R7-B1：历史 C4 反例仍未闭合

`round4-exact` 逐字输出：

```text
01-Cf-U2064-C3.md	C6_undecided	拿不准	false	null	null
02-Cf-U1BCA0-C4.md	C6_undecided	拿不准	false	节点/canonical.md	文件里有疑似「生成器声明」的 frontmatter 键
03-Cf-UE0001-C3.md	C6_undecided	拿不准	false	null	null
04-Mn-U0301-C3.md	C6_undecided	拿不准	false	null	null
05-Mn-U1AB0-C4.md	C6_undecided	拿不准	false	节点/canonical.md	文件里有疑似「生成器声明」的 frontmatter 键
06-Mn-UE0100-C3.md	C6_undecided	拿不准	false	null	null
07-Cc-U0001-C3.md	C6_undecided	拿不准	false	null	null
08-Zs-U200A-C3.md	C6_undecided	拿不准	false	null	null
09-Lo-U3164-C3.md	C6_undecided	拿不准	false	null	null
10-So-U2800-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md	null
```

失败件与正本的精确字节：

```text
10-So-U2800-C4.md
232047656e657261e2a080746564206279204750542d340a524f554e44342d45584143542d424f44590a

节点/canonical.md
524f554e44342d45584143542d424f44590a
```

换 `CASE=splitline-cc`，逐字输出：

```text
01-Cc-U000B-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md	null
02-Cc-U000C-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md	null
03-Cc-U001C-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md	null
04-Cc-U0085-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md	null
```

输入字节：

```text
U+000B 232047656e6572610b746564206279204d4f44454c0a
U+000C 232047656e6572610c746564206279204d4f44454c0a
U+001C 232047656e6572611c746564206279204d4f44454c0a
U+0085 232047656e657261c285746564206279204d4f44454c0a
正本    746564206279204d4f44454c0a
```

根因是：

- [dup_body()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:731) 在 742–744 行仍无条件丢弃围栏外标题。
- 标题裁决只进入 [has_substantive_content()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:752) 的 C3 路径。
- [head_window()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:821) 先执行 `splitlines()`，换行型控制符在不可见归一前已改变结构。

扩展实测也一致：

```text
01-visible-unique-title.md	C4_exact_duplicate	建议删	true	节点/canonical.md
02-U3164-title.md	C4_exact_duplicate	建议删	true	节点/canonical.md
03-U2800-title.md	C4_exact_duplicate	建议删	true	节点/canonical.md
01-U001D-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md
02-U001E-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md
03-U2028-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md
04-U2029-C4.md	C4_exact_duplicate	建议删	true	节点/canonical.md
```

偏差 18/19 已公开接受这项 C4 风险；但本轮明确规定“任何历史件重新出现 `建议删 + true` 即按 BLOCKER/HIGH 报”，所以不能将其写成“历史反例全部闭合”。

## 1.2 其余历史反例闭合

同一命令分别替换 `CASE`，再执行：

```sh
jq -c '{
  names:[.items[].name],
  nonC6:[.items[]
    | select(.criterion!="C6_undecided")
    | [.name,.criterion,.verdict,.confident]]
}' "$R/$CASE/out/inbox-preview-_待处理.json"
```

逐字结果：

```text
hist-core
{"names":["01-hash-NBSP.md","02-model-generator.md","03-DOI-source.md","04-long-model.md","05-by-colon.md","06-by-underscore.md","07-ISBN-citation.md","08-duplicate-DOI.md","09-duplicate-URL.md","10-title-ISBN.md"],"nonC6":[]}

whitelist-zwsp
{"names":["01-title-unique.md","02-alias-unique.md","03-date-unique.md","04-tags-unique.md","05-C4-whitelist.md","06-zwsp-generated.md","07-zwsp-by.md","08-zwsp-cn.md","09-zwsp-C4-title.md","10-zwsp-C4-alias.md"],"nonC6":[]}

zero-one
{"names":["01-U200B.md","02-U200C.md","03-U200D.md","04-U2060.md","05-UFEFF.md","06-U00AD.md","07-U2063.md","08-U200E.md","09-U200F.md","10-U061C.md"],"nonC6":[]}

zero-two
{"names":["01-U034F.md","02-UFE0F.md","03-U2062.md","04-U180E.md","05-U202E.md"],"nonC6":[]}

round3-u2063-exact
{"names":["01-plain-en.md","02-u2063-en-heading.md","03-u2063-en-comment.md","04-u2063-en-C4.md","05-plain-en-C4.md","06-u2063-cn.md","07-plain-cn.md"],"nonC6":[]}

comments-one
{"names":["01-source-url.md","02-doi.md","03-isbn.md","04-generated-with.md","05-plain-comment-control.md","06-source-url-C4.md","07-doi-C4.md","08-generated-with-C4.md","09-multiline-source.md","10-nested.md"],"nonC6":[]}

comments-two
{"names":["01-inline-heading.md","02-multiple.md","03-C4-inline-adjacent.md","04-C4-multiline.md","05-fence-unique.md","06-fence-exact.md","07-empty-inline-comment.md","08-empty-multiline-comment.md","09-fm-whole-line-comment.md","10-fm-tail-comment.md"],"nonC6":[["06-fence-exact.md","C4_exact_duplicate","建议删",true],["07-empty-inline-comment.md","C3_empty_or_skeleton","建议删",true],["08-empty-multiline-comment.md","C3_empty_or_skeleton","建议删",true]]}

nfd-matrix
{"names":["01-NFD-generated.md","02-NFC-generated.md","03-NFD-French-heading.md","04-NFC-French-heading.md"],"nonC6":[]}
```

`comments-two` 的三个非 C6 件均是正向锚：真实精确重复和两个空注释，不是历史危险反例。跨行 HTML 注释、frontmatter 整行 YAML 注释、frontmatter 行尾 YAML 注释三种“来源被剥”写法均已降 C6。

旧 B3/H1/H2/H3/H4 组：

```text
01-B3-four-backticks.md	C6_undecided	拿不准	false
02-H1-empty-host-port.md	C6_undecided	拿不准	false
03-H1-empty-host-user.md	C6_undecided	拿不准	false
04-H2-copyright-topic.md	C6_undecided	拿不准	false
05-H2-you-topic.md	C6_undecided	拿不准	false
06-H2-eval-topic.md	C6_undecided	拿不准	false
07-H3-bare-url.md	C6_undecided	拿不准	false
08-H4-third-copy.md	C4_exact_duplicate	建议删	true
```

H4 是预期的“三份同正文”正向锚，其报告仍逐字声明正本不可判，不构成回归。

## 1.3 C1/C2 命中面与 969844ef 相等

从给定 diff 的第 2152 行起反向还原生产脚本：

```sh
sed -n '2152,$p' \
  "$ROOT/_bmad-output/审查/CARD-G5-6c-diff-969844ef-to-6ac7e891.txt" |
  (cd "$R/baseline-root" && patch -R -p1)

shasum -a 256 \
  "$R/baseline-root/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py" \
  "$P"
```

逐字有效输出：

```text
patching file 'canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py'
4b873b61f588c7aab56b19374a13f183a9e5433f9efdd16ff9be3f0eaafcb7fd  baseline inbox_preview.py
f2a4d21925fd1095527018e32c0d1a208674cc1eb444307ec71b7337f9f3b44e  current inbox_preview.py
```

两版矩阵输出：

```text
[c1-matrix]
out-baseline ["01-lower.md","02-upper-scheme.md","03-quoted-comment.md","06-first-valid.md"]
out ["01-lower.md","02-upper-scheme.md","03-quoted-comment.md","06-first-valid.md"]

[c2-matrix]
out-baseline ["01-deep-cn.md","02-deep-en.md","03-ai-cn.md","04-ai-en.md","05-case-tab.md","06-punct.md"]
out ["01-deep-cn.md","02-deep-en.md","03-ai-cn.md","04-ai-en.md","05-case-tab.md","06-punct.md"]
```

结论：**C1/C2 确定命中集合完全相等，PASS。** `outside-window` 的最终总判决由旧 C3 变成现 C6，是标题裁决的预期影响，不是 C2 扩面。

# 二、新构造

## 2.1 R7-H1：合法 fence info string 被静默丢弃

输入：

```text
01-source-in-info.md
~~~ {source=https://fence.example/p}
~~~

02-comment-in-info.md
~~~ <!-- source: https://comment-in-info.example/p -->
~~~

03-cell-id-in-info.md
~~~ {.python #cell-37}
~~~
```

命令：

```sh
R2=/private/tmp/card-g56c-r7.o7v1JT/fence-info-matrix

python3 -B "$P" \
  --vault "$R2/vault" \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir "$R2/out" \
  --batch-size 10

jq -c '.items[] |
  {name,criterion,verdict,confident,basis,uncertain_reason}' \
  "$R2/out/inbox-preview-_待处理.json"
```

逐字 CLI 摘要：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-r7.o7v1JT/fence-info-matrix/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-r7.o7v1JT/fence-info-matrix/out/inbox-preview-_待处理.md
  _待处理/ 共 5 件，本批全取（5 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 5 件 · 拿不准 2 件 · 建议删 3 件
```

关键逐字 JSON：

```json
{"name":"01-source-in-info.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（41 字节文件：标题 0 行、纯结构行 0 行、代码围栏 2 行、其余皆空行或注释）","uncertain_reason":null}
{"name":"02-comment-in-info.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（59 字节文件：标题 0 行、纯结构行 0 行、代码围栏 2 行、其余皆空行或注释）","uncertain_reason":null}
{"name":"03-cell-id-in-info.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（27 字节文件：标题 0 行、纯结构行 0 行、代码围栏 2 行、其余皆空行或注释）","uncertain_reason":null}
{"name":"04-source-outside.md","criterion":"C6_undecided","verdict":"拿不准","confident":false,"basis":"无机械判据可施加","uncertain_reason":"文件里有被 HTML 注释包起来的内容（如 'source: https://outside.example/p'），引擎把注释整段剥掉了、没有消费它 —— 注释里可能写着这份材料的来源或说明，删掉就一起没了，文件又没有实质正文 —— 是空骨架还是「信号还没被读懂的文件」拿不准，不敢建议删"}
{"name":"05-source-as-code.md","criterion":"C6_undecided","verdict":"拿不准","confident":false,"basis":"无机械判据可施加","uncertain_reason":"六判据全不命中：无 source URL、文头无可确定的 AI 自述、有实质正文、与库内无逐字相同正本、文件名无 R{n}_ 轮次标记"}
```

根因链：

- [_classify_lines_typed()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:659) 在 667–670 行把完整 opener 记为 `fence` 后立即 `continue`。
- [has_substantive_content()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:762) 在 767–768 行无条件跳过所有 `fence` 行。
- 信号⑩只接 `stripped_comments` 和 frontmatter 注释，见 [1425–1429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1425)。
- 裁判只锁了“空围栏→C3”和“围栏内有内容→非 C3”，见 [测试 1168–1190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:1168)，没有锁“非空 info string + 空围栏”。

## 2.2 R7-H2：有语义运算符被当纯结构

输入分别是 `:=\n`、`=>\n`、`||\n`。

命令：

```sh
R3=/private/tmp/card-g56c-r7.o7v1JT/new-matrix
python3 -B "$P" \
  --vault "$R3/vault" \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir "$R3/out" \
  --batch-size 10

jq -c '.items[0:3][] |
  {name,criterion,verdict,confident,basis}' \
  "$R3/out/inbox-preview-_待处理.json"
```

逐字输出：

```json
{"name":"01-body-define-symbol.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（3 字节文件：标题 0 行、纯结构行 1 行、代码围栏 0 行、其余皆空行或注释）"}
{"name":"02-body-arrow-symbol.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（3 字节文件：标题 0 行、纯结构行 1 行、代码围栏 0 行、其余皆空行或注释）"}
{"name":"03-body-logical-or.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（3 字节文件：标题 0 行、纯结构行 1 行、代码围栏 0 行、其余皆空行或注释）"}
```

`:=`、`=>` 是常见定义/推导符号，不能统一证明为 Markdown 空骨架。根因是 `_ONLY_STRUCT_RE` 加 [793–795 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:793) 把这类纯标点正文全部忽略。

## 2.3 其他边界

本轮构造未找到新的标题绕过：

```json
{"name":"08-format-only-heading.md","criterion":"C6_undecided","verdict":"拿不准","confident":false}
```

围栏外闭合来源注释和围栏内容中的注释均安全：

```json
{"name":"09-comment-outside-fence.md","criterion":"C6_undecided","verdict":"拿不准","confident":false}
{"name":"10-comment-inside-fence.md","criterion":"C6_undecided","verdict":"拿不准","confident":false}
```

frontmatter 的 flow map、顶层 sequence、嵌套行、Unicode 键、点号键也均落 C6。已有偏差 19 的空键名反例仍在：

```json
{"name":"09-isbn-in-key.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（35 字节文件：标题 1 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）"}
```

它是已登记残余，不另计新根因。

# 三、C3 可达面

命令：

```sh
CASE=c3-reach
python3 -B "$P" \
  --vault "$R/$CASE/vault" \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir "$R/$CASE/out" \
  --batch-size 10

jq -c '.items[] |
  {name,criterion,verdict,confident,basis}' \
  "$R/$CASE/out/inbox-preview-_待处理.json"
```

五个指定面逐字输出：

```json
{"name":"01-zero-byte.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"0 字节空文件"}
{"name":"02-blank-lines.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（4 字节文件：标题 0 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）"}
{"name":"03-divider-only.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（4 字节文件：标题 0 行、纯结构行 1 行、代码围栏 0 行、其余皆空行或注释）"}
{"name":"04-empty-heading.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（3 字节文件：标题 1 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）"}
{"name":"05-quote-only.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（2 字节文件：标题 0 行、纯结构行 1 行、代码围栏 0 行、其余皆空行或注释）"}
```

因此 **C3 没有判死，五面全部仍可达**。

但“五种”不是穷尽语法描述，以下也进入 C3：

```json
{"name":"06-empty-frontmatter.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true}
{"name":"07-empty-fence.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true}
{"name":"08-empty-inline-comment.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true}
```

少删方向的保守形态：

```text
aliases: []       → C6 / 拿不准 / false
tags: {}          → C6 / 拿不准 / false
title: null       → C6 / 拿不准 / false
title: ~          → C6 / 拿不准 / false
published: false  → C6 / 拿不准 / false
- [ ]             → C6 / 拿不准 / false
> [!note]         → C6 / 拿不准 / false
```

这部分是安全方向的漏删，可接受为保守偏差；真正不可接受的是二、所示非空 info string、来源元数据和运算符内容仍被 `C3 + true` 删除。

# 四、门强度

## 4.1 当前 91 门真实全绿

命令：

```sh
cd "$ROOT/backend"
env PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/pytest \
  tests/skills/test_g5_6_clear_inbox.py \
  -q -p no:cacheprovider \
  --basetemp /private/tmp/g56c-gate.aIWLTv/pytest-basetemp
```

逐字输出：

```text
collected 91 items
tests/skills/test_g5_6_clear_inbox.py .................................. [ 37%]
.........................................................                [100%]
======================= 91 passed, 10 warnings in 6.42s ========================
```

AST 入口统计：

```text
top_level_test_defs= 91
run_cli_tests= 82
load_module_tests= 14
load_split_module_tests= 2
neither_cli_nor_import= 1
NEITHER:
705:test_no_bytecode_cache_written_into_vault_skills
```

82 个真实 CLI 门与 14 个生产模块 import 门重叠 6 个，覆盖 90 个；余下一门先逐字节比对生产脚本与临时副本，再运行该副本。91 门均有断言。就“是否测到当前生产字节”而言，PASS。

但相关两门定点运行仍全绿：

```sh
.venv/bin/pytest \
  tests/skills/test_g5_6_clear_inbox.py::test_invisible_chars_are_detected_by_category_not_enumeration \
  tests/skills/test_g5_6_clear_inbox.py::test_heading_with_text_counts_as_substantive_content \
  -q -p no:cacheprovider
```

```text
2 passed, 10 warnings in 0.31s
```

原因是：

- [不可见字符门 2571–2579](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2571) 主动把端到端样本换成 frontmatter。
- [标题门 2595–2647](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2595) 只锁无重复正本的 C3；其 2603–2604 行“关闭 U+3164/U+2800 BLOCKER”的表述没有覆盖 C4。

## 4.2 11 条变异

在 `/private/tmp` 同哈希副本执行：

```sh
python3 -B \
  /private/tmp/g56c-gate.aIWLTv/g56c_mutations.py \
  /private/tmp/g56c-gate.aIWLTv/root
```

逐字摘要：

```text
✅ M-NBSP        rc=1 | 2 failed, 89 passed | 还原 sha 一致
✅ M-CLAIMBOUND  rc=1 | 1 failed, 90 passed | 还原 sha 一致
✅ M-ZEROWIDTH   rc=1 | 2 failed, 89 passed | 还原 sha 一致
✅ M-GENSIGNAL   rc=1 | 3 failed, 88 passed | 还原 sha 一致
✅ M-SRCALIAS    rc=1 | 1 failed, 90 passed | 还原 sha 一致
✅ M-DOIVAL      rc=1 | 2 failed, 89 passed | 还原 sha 一致
✅ M-PAIRS       rc=1 | 1 failed, 90 passed | 还原 sha 一致
✅ M-FALLBACK    rc=1 | 2 failed, 89 passed | 还原 sha 一致
✅ M-INVISENUM   rc=1 | 1 failed, 90 passed | 还原 sha 一致
✅ M-COMMENT     rc=1 | 2 failed, 89 passed | 还原 sha 一致
✅ M-HEADING     rc=1 | 1 failed, 90 passed | 还原 sha 一致

finally 还原后 sha256 = f2a4d21925fd1095527018e32c0d1a208674cc1eb444307ec71b7337f9f3b44e (与基线逐字节相同)

G56C_NEGATIVE_CONTROL: PASS （11/11 变异的实际失败集合等于预先声明集合）
```

当前 11 个变异只涉及 13 个 distinct tests：

```text
mutations=11 distinct_expected_tests=13 total_test_defs=91
```

所以准确结论是“91 门真实执行；11 个指定回退被相关 13 门杀灭”，不能写成“91 门逐门均经变异证明承重”。

## 4.3 FAILED/ERROR、rc 与归属断言

runner 在 [224–228 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:224) 合并 `FAILED`/`ERROR`，在 [273–276 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:273) 强制 `rc == 1` 和集合精确相等。

合成输出测试：

```text
ERROR_rc1: rc=1 failed=['test_err'] ok=True
ERROR_rc2: rc=2 failed=['test_err'] ok=False
collection_ERROR_rc2: rc=2 failed=[] ok=False
FAILED_extra_rc1: rc=1 failed=['test_err', 'test_extra'] ok=False
```

判定：

- rc 2、collection error、额外失败均 fail closed。
- 但同名测试节点若因 fixture/setup `ERROR` 且整体 rc=1，会被视作预期 kill。按本卡“FAILED/ERROR 并计”的明示规则这是 PASS；它只能证明预期节点变红，不能单独证明目标断言因果，记 MEDIUM 证据边界。

额外关闭专用信号，归属断言逐字结果：

```text
raw_ai_marker 关闭：
FAILED test_zero_width_split_marker_still_reads_as_ai_suspect
1 failed, 90 passed in 4.73s

任意键 URL 信号关闭：
FAILED test_duplicate_frontmatter_key_does_not_mask_source
1 failed, 90 passed in 4.60s

独立 AI 词信号关闭：
FAILED test_natural_ai_word_is_undigested_signal
FAILED test_cjk_adjacent_ai_is_undigested_signal
2 failed, 89 passed in 4.73s

slept_at 专用信号关闭：
FAILED test_slept_at_is_undigested_signal
1 failed in 0.26s
```

信号归属门确实承重。

## 4.4 期望集合不是纯独立 oracle

[g56c_mutations.py 78–84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:78) 明载 M-ZEROWIDTH 首次实跑“少红”后更正期望；[149–152 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:149) 明载 M-FALLBACK 首次“多红”后补入测试。

因此当前 literal 集合不是运行时自抄，仍有回归价值；但准确称谓应为“实测后冻结的失败集合”，不是纯 a priori 独立预言。另 [脚本第 2 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:2) 仍写“八条”，实际为 11 条。

# 五、措辞

静态核对命令：

```sh
nl -ba "$P" | sed -n \
  '20,25p;127,219p;840,858p;936,952p;2101,2133p'

rg -n '88|8/8|五种|九类|多行|YAML|偏差' \
  "$ROOT/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md" \
  "$ROOT/_bmad-output/审查/evidence-g56c/README-取证说明.md"
```

## 5.1 生产文件头与内部说明

- [24–25 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:24)：写“当前登记九类”，实现已有⑩。**FAIL，陈旧。**

- [偏差 15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:127)：只列①–⑨，漏⑩；165、171 行仍使用已取消的“白名单”叙述；170 行“对结构没有把握就不建议删”被 fence info 与运算符反例直接证伪。**FAIL，比证据宽。**

- [偏差 16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:175)：非法端口仍按一手来源、方向为留原地，范围和影响均准确。**PASS。**

- [偏差 17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:183)：句式边界基本准确，但 187、199–201 行仍把⑨称为“白名单兜底”。**PARTIAL。**

- [偏差 18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:207)：准确披露 C4 丢标题风险。**PASS 作为风险登记；不能据此声称历史反例闭合。**

- [偏差 19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:214)：多行 HTML/YAML 注释“仍会被删”已经失实；splitlines 与空键名残余仍属实。**PARTIAL/陈旧。**

- [851–858 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:851) 仍称 U+3164 标题会落 C3、标题不算内容；已被新标题裁决改写。**FAIL。**

- [944、951 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:944) 仍写“断言骨架是闭合的”“才真的闭合”。当前文头自己又承认跨行、换动词等边界。**FAIL，过宽。**

## 5.2 生成 MD §七

[2113–2123 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2113) 只列八条，漏⑨“任意非空 frontmatter 值”和⑩“被剥注释内容”。**FAIL。**

“一律落拿不准”只有在“原本要走 C3/C4”这一隐含前提下才成立。带同类信号但有正文的轮次文件实跑：

```json
{"name":"R1_comment_signal.md","criterion":"C5_round_filename","verdict":"归档","confident":true,"target_hint":"R1/","basis":"文件名带 R1_ → 归轮次目录；子模式未命中 → 类型留空（去向确定，类型拿不准，不硬填）","uncertain_reason":null}
{"name":"R2_fm_value_signal.md","criterion":"C5_round_filename","verdict":"归档","confident":true,"target_hint":"R2/","basis":"文件名带 R2_ → 归轮次目录；子模式未命中 → 类型留空（去向确定，类型拿不准，不硬填）","uncertain_reason":null}
```

应改成“仅当文件原本将进入 C3/C4 时降 C6”。现措辞判 **PARTIAL/过宽**。

## 5.3 验收单

[UAT 验收单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:62) 存在多处非终态：

- 62、95、145、206 行写 `88` 门；当前是 `91`。
- 99 行写 `8/8` 变异，213 行又写 `3` 条；当前是 `11/11`。
- 125 行“可确定删除面只剩五种”被空围栏、非空 info string、空 frontmatter 证伪。
- 215 行写 17 条偏差；当前文件头已有 19。
- 217–235 行写九类，漏⑩。
- 244–245 行仍称多行 HTML/YAML 注释来源会被删，已不符合最终实现。

逐字现态锚：

```text
collected 91 items
======================= 91 passed, 10 warnings in 6.42s ========================
G56C_NEGATIVE_CONTROL: PASS （11/11 变异的实际失败集合等于预先声明集合）
```

结论：**UAT 不能作为当前最终态归档验收单。**

## 5.4 取证 README

[README-取证说明.md](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:35)：

- 35–42 行的“三条、81 passed”和 56–57 行旧 SHA 是历史快照，但没有清楚绑定提交，不能替代最终态证据。
- 192–193 行“任何带非空闭合注释的骨架件都不再确定删除”被 fence opener info string 中的闭合注释序列击穿。**过宽。**
- 280–289 行“五种”不是穷尽描述。**过宽。**
- 344–349 行写多行/YAML 注释未修，358–382 行又写已修；虽可按时间顺序理解，但归档阅读状态不自洽。**PARTIAL。**
- 378–382 行列出的三种写法确已同口径；但“保护面不该取决于来源写在哪里”作为全称说法仍不成立，来源放进合法 fence info string 后仍是 C3。**枚举结论 PASS，全称口号 FAIL。**

# 六、登记

## 6.1 当前字节绑定

命令：

```sh
rg -n '^diff --git|^index ' \
  "$ROOT/_bmad-output/审查/CARD-G5-6c-diff-969844ef-to-6ac7e891.txt"

git hash-object "$P"
git hash-object "$ROOT/backend/tests/skills/test_g5_6_clear_inbox.py"
git hash-object "$ROOT/_bmad-output/审查/evidence-g56c/README-取证说明.md"
git hash-object "$ROOT/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md"
```

逐字有效输出：

```text
diff target script: a7a5f0b7
current script:     a7a5f0b75f5811634578c4ac378972b3f153699d

diff target tests: 8554beba
current tests:     8554beba02157f680bc1163257c576e28945b1b2

diff target README: 6a2a97fb
current README:     6a2a97fbbd5a37421d7934586916673cdb1a8f13

diff target UAT: 1073a8fb
current UAT:     1073a8fba7bf0bcb67306e57db1e1285e1c45871
```

SHA256：

```text
f2a4d21925fd1095527018e32c0d1a208674cc1eb444307ec71b7337f9f3b44e  inbox_preview.py
1b10429354e62273a367b2054f2b21f0f0c16f59d7ce5d37f2063e2c874b72a7  test_g5_6_clear_inbox.py
6b3de2e4ecc6fcce5540136e1242f57abbeff2c0b9d55856d61fca60b88a06a0  CARD-G5-6c-diff-969844ef-to-6ac7e891.txt
```

当前文件逐字匹配给定 diff 的目标 blobs。受限定读取范围约束，本轮没有读取 `.git` 提交对象，因此只证明“当前字节 = diff 目标字节”，不额外声称独立验证了 `57712c59`/`6ac7e891` 提交标签绑定。

## 6.2 最终登记

| 登记项 | 状态 |
|---|---|
| R7-B1 历史 U+2800/Cc C4 复现 | OPEN / BLOCKER |
| R7-H1 fence info string 静默丢弃 | OPEN / HIGH |
| R7-H2 有语义运算符误判结构 | OPEN / HIGH |
| C1/C2 命中面相对 969844ef | PASS |
| C3 五个指定面可达 | PASS |
| C3 是否判死 | 否 |
| 91 门是否运行当前生产字节 | PASS |
| 11 条现有变异 | PASS_WITH_LIMITS |
| 期望集合独立性 | PARTIAL / MEDIUM |
| UAT/README/生产措辞终态一致性 | FAIL |

审查仅读取用户列出的文件；所有 fixture、pytest 临时目录和安全副本都在 `/private/tmp`。未联网、未碰 live vault、未写 worktree、未原地运行变异 runner，也未执行全仓 CI。既有对抗审查流程只用于拆分证据轨、锁定真实生产入口和明确证据边界，不改变上述实测裁定。

可归档的是本报告的 **FAIL 结论**；不可将 CARD-G5-6c 当前状态归档为验收通过或 BLOCKER/HIGH 已清零。

BLOCKER/HIGH 清零: 否
