审查结论：**不通过，不能按“整改闭合/验收通过”归档。** 当前 HEAD 确为 `f6c1fdaf52664a659a7ed6d444503e513bdaa695`。共在 `/private/tmp` 实跑 119 个历史/新构造 fixture，另跑 C3 平衡矩阵、91 门、旧新 C1/C2 对比及 tmp 副本变异；未写 worktree、未碰 live vault、未联网。

决定性结果有三项：

- 5 条原历史反例仍为 `C4 / 建议删 / confident=true`。
- 用户标题裁决只关闭 C3，没有关闭 C4。
- 信号⑩对典型多行闭合 HTML 注释失效，C3/C4 双出口均可穿透。

## 一、历史反例复核

统一命令：

```sh
P=canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
R=/private/tmp/card-g56c-final-a.wlNu1b

python3 -B "$P" \
  --vault "$R/<group>/vault" \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir "$R/<group>/out" \
  --batch-size 10

jq -r '.items[] |
  [.name,.criterion,.verdict,(.confident|tostring),
   (.exact_duplicate_of//"null")] | @tsv' \
  "$R/<group>/out/inbox-preview-_待处理.json"
```

历史组逐批实测：

| 组 | 覆盖面 | 逐字 stdout 末行 | 判定 |
|---|---|---|---|
| `old-b3-h` | B3、H1、H2、H3、H4 | `本批 10 件 · 拿不准 9 件 · 建议删 1 件` | 9 条安全；1 条是合法 H4 精确重复正向锚 |
| `h1-heading-family` | NBSP、EM/全角/NNBSP/OGHAM、`#keep`、TAB/空格标题 | `本批 9 件 · 拿不准 9 件 · 建议删 0 件` | PASS |
| `h1-round1` | NBSP、GPT4、DOI、长模型、`by:`、词间零宽、重复键、ISBN | `本批 10 件 · 拿不准 10 件 · 建议删 0 件` | PASS |
| `h2-round2-zero` | `by_`/`by__`、词内/词间零宽及四个 C4 出口 | `本批 10 件 · 拿不准 10 件 · 建议删 0 件` | PASS |
| `h2-round2-whitelist` | ISBN、馆藏号、title/aliases/date/tags 唯一值及 C4 | `本批 8 件 · 拿不准 8 件 · 建议删 0 件` | PASS |
| `h3-invis-a/b` | 原六码点、U+2063、200E/200F/061C/034F/FE0F/2062/180E/202E | 共 18 件，全部 `拿不准` | PASS |
| `h3-comments` | 单行闭合注释 URL/DOI/ISBN/generated，含 C3/C4 | `本批 8 件 · 拿不准 8 件 · 建议删 0 件` | PASS |
| `h4-unicode` | Cf/Mn/Cc/Zs/Lo/So | `本批 10 件 · 拿不准 9 件 · 建议删 1 件` | **FAIL** |
| `h4-splitline` | U+000B/000C/001C/0085 | `本批 4 件 · 拿不准 0 件 · 建议删 4 件` | **FAIL** |
| `h4-comments` | 历史多行、嵌套、围栏、空注释 | 8 条 C6；另 1 条合法 fenced C4、1 条空注释 C3 | PASS，但样本没覆盖典型独立关闭行 |
| `h4-visual-c3`、`h4-splitline-c3` | 标题裁决后的 C3 隔离对照 | 6/6 `C6 / 拿不准 / false` | C3 子面 PASS |

历史失败逐字输出：

```text
10-So-U2800-C4.md	C4_exact_duplicate	建议删	true	节点/canon-cf.md
01-Cc-U000B-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
02-Cc-U000C-C4.md	C4_exact_duplicate	建议删	true	节点/canon-2.md
03-Cc-U001C-C4.md	C4_exact_duplicate	建议删	true	节点/canon-3.md
04-Cc-U0085-C4.md	C4_exact_duplicate	建议删	true	节点/canon-4.md
```

Cc 输入字节：

```text
01-Cc-U000B-C4.md	232047656e6572610b746564206279204d4f44454c2d310a
02-Cc-U000C-C4.md	232047656e6572610c746564206279204d4f44454c2d320a
03-Cc-U001C-C4.md	232047656e6572611c746564206279204d4f44454c2d330a
04-Cc-U0085-C4.md	232047656e657261c285746564206279204d4f44454c2d340a
```

根因链：

- [`dup_body()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:711)仍丢掉所有标题。
- 标题裁决只进入 [`has_substantive_content()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:732)。
- `splitlines()` 在不可见归一前拆掉换行型 Cc，见 [`head_window()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:792)。
- 随后 [`C4`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1494)仍按去标题正文确定删除。

因此“历史反例全部闭合”为 **FAIL · BLOCKER**。

## 二、新构造

统一新构造批次：

```sh
python3 -B "$P" \
  --vault /private/tmp/card-g56c-final-a.wlNu1b/new-probes/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-final-a.wlNu1b/new-probes/out \
  --batch-size 10
```

逐字 stdout：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-final-a.wlNu1b/new-probes/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-final-a.wlNu1b/new-probes/out/inbox-preview-_待处理.md
  _待处理/ 共 10 件，本批全取（10 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 10 件 · 拿不准 0 件 · 建议删 10 件
```

逐字结果：

```text
01-multiline-open-content.md	C3_empty_or_skeleton	建议删	true	null	null
02-multiline-middle-content.md	C3_empty_or_skeleton	建议删	true	null	null
03-multiline-C4.md	C4_exact_duplicate	建议删	true	节点/库内正本.md	null
04-fm-comment-C3.md	C3_empty_or_skeleton	建议删	true	null	null
05-fm-comment-C4.md	C4_exact_duplicate	建议删	true	节点/库内正本.md	null
06-unique-heading-C4.md	C4_exact_duplicate	建议删	true	节点/库内正本.md	null
07-U3164-heading-C4.md	C4_exact_duplicate	建议删	true	节点/库内正本.md	null
08-U2800-heading-C4.md	C4_exact_duplicate	建议删	true	节点/库内正本.md	null
09-key-encoded-info-C3.md	C3_empty_or_skeleton	建议删	true	null	null
10-key-encoded-info-C4.md	C4_exact_duplicate	建议删	true	节点/库内正本.md	null
```

### 1. 多行闭合 HTML 注释：FAIL · HIGH

典型输入：

```markdown
# 

<!--
source: https://new.example/middle
-->
```

或：

```markdown
<!-- source: https://new.example/dup
-->
重复正文
```

生产状态机在未看到 `-->` 的行直接 `break`，没有累积该行的 `rem`；只在关闭符所在行执行 `stripped_comments.append(rem[:i])`，见 [inbox_preview.py:677](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:677)。当 `-->` 独占一行时，最终仅收集空串，信号⑩在 [inbox_preview.py:1378](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1378)完全看不到内容。

纯函数逐字结果：

```text
([('# ', 'text'), ('', 'text'), ('', 'text'), ('', 'text')], False, [''])
```

这直接违反本轮明确判据“被闭合 HTML 注释剥掉的内容（非整行）算未消化”，且同时穿透 C3/C4。

围栏对照：

```text
03-html-outside.md	C6_undecided	拿不准	False
04-html-inside-fence.md	C6_undecided	拿不准	False
05-fence-info-comment.md	C3_empty_or_skeleton	建议删	True
10-unclosed-fence-info.md	C3_empty_or_skeleton	建议删	True
```

围栏内容中的注释按代码正文处理是安全的；真正的 HIGH 是围栏外多行注释内容丢失。含来源文字的 fence info string 被当纯分隔符删除，另登记 MEDIUM 边界。

### 2. frontmatter YAML 注释：FAIL · HIGH

```yaml
---
# source: https://new.example/fm-comment
---
```

以及带重复正文的 DOI 版本分别进入 C3、C4。原因是：

- [`frontmatter_span()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:537)把 YAML 注释当作不作数的空 frontmatter；
- `frontmatter_pairs=[]`；
- [`unparsed_fm`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1245)又显式排除 `#` 开头行。

这与“闭合 HTML 注释中的唯一信息不能丢”同构。

### 3. 标题与 C4 的交互：FAIL · BLOCKER

即使是普通可见标题：

```markdown
# 只有这一份写了母本第37页
重复正文
```

也会因 `dup_body()` 丢标题而进入 C4。U+3164/U+2800 只是让生成声明护栏同时失明：

```text
01-U3164-C4.md	C4_exact_duplicate	建议删	true	节点/canon-lo.md
02-U2800-C4.md	C4_exact_duplicate	建议删	true	节点/canon-so.md
```

因此标题裁决仅关闭“只有标题、无库内重复正文”的 C3 子面。是否全面改变 C4 的标题语义仍属产品裁决，但当前“BLOCKER 已关闭”的声明已经被实测证伪。

### 4. 新 splitlines 同族

```text
01-U001D-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
02-U001E-C4.md	C4_exact_duplicate	建议删	true	节点/canon-2.md
03-U2028-C4.md	C4_exact_duplicate	建议删	true	节点/canon-3.md
04-U2029-C4.md	C4_exact_duplicate	建议删	true	节点/canon-4.md
```

说明问题不是四个历史码点特判，而是“先 `splitlines()`、后不可见归一”的处理顺序。

空键名编码 DOI/ISBN 的两个构造也穿透，但形态较对抗，登记 MEDIUM，暂不单独升 HIGH。

## 三、C3 可达面

实测命令：

```sh
python3 -B "$P" \
  --vault /private/tmp/card-g56c-final.SBE1sr/c3/vault \
  --inbox-dir /private/tmp/card-g56c-final.SBE1sr/c3/vault/_pending \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-final.SBE1sr/c3/out \
  --batch-size 10
```

逐字结果：

```text
01-zero.md	C3_empty_or_skeleton	建议删	True	0 字节空文件
02-blank.md	C3_empty_or_skeleton	建议删	True	剥离 frontmatter / HTML 注释后实质正文 0 字符（6 字节文件：标题 0 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）
03-dividers.md	C3_empty_or_skeleton	建议删	True	剥离 frontmatter / HTML 注释后实质正文 0 字符（12 字节文件：标题 0 行、纯结构行 3 行、代码围栏 0 行、其余皆空行或注释）
04-empty-headings.md	C3_empty_or_skeleton	建议删	True	剥离 frontmatter / HTML 注释后实质正文 0 字符（7 字节文件：标题 2 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）
05-quotes-only.md	C3_empty_or_skeleton	建议删	True	剥离 frontmatter / HTML 注释后实质正文 0 字符（8 字节文件：标题 0 行、纯结构行 3 行、代码围栏 0 行、其余皆空行或注释）
06-empty-checkbox.md	C6_undecided	拿不准	False	无机械判据可施加
07-empty-frontmatter.md	C3_empty_or_skeleton	建议删	True	剥离 frontmatter / HTML 注释后实质正文 0 字符（24 字节文件：标题 1 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）
08-empty-fence.md	C3_empty_or_skeleton	建议删	True	剥离 frontmatter / HTML 注释后实质正文 0 字符（14 字节文件：标题 0 行、纯结构行 0 行、代码围栏 2 行、其余皆空行或注释）
09-punct-heading.md	C6_undecided	拿不准	False	无机械判据可施加
10-empty-table.md	C3_empty_or_skeleton	建议删	True	剥离 frontmatter / HTML 注释后实质正文 0 字符（16 字节文件：标题 0 行、纯结构行 2 行、代码围栏 0 行、其余皆空行或注释）
```

判定：

- 用户点名的五种全部仍可达，C3 **没有判死**。
- 全空 frontmatter、空代码块、空表格也仍可达，所以“只剩五种”不是严格穷举。
- 空任务框 `- [ ]` 与纯标点标题落 C6，是安全方向少删，登记 MEDIUM/LOW。
- 真正的问题不是 C3 召回太窄，而是多行/YAML 注释等带唯一信息的结构仍被错当空骨架。

### C1/C2 与 `969844ef` 对比：PASS

从用户提供的全卡 diff 反向还原旧版：

```sh
sed -n '2039,$p' \
  _bmad-output/审查/CARD-G5-6c-diff-969844ef-to-f6c1fdaf.txt |
  patch -R -p1 -d /private/tmp/g56c-gate-baseline.Ljcssg/oldrepo
```

逐字摘要：

```text
OLD_SHA=4b873b61f588c7aab56b19374a13f183a9e5433f9efdd16ff9be3f0eaafcb7fd
NEW_SHA=a3c6242bb84f8625b8015147a2cc6614c6d5518819d8f4ef2c4ea49834fdde5f
AST_CRITICAL_EQUAL=True mismatches=[]
CONSTANTS_EQUAL=True mismatches=[]
REGEXES_EQUAL=True mismatches=[]
C1_VALUE_MATRIX=328 mismatches=0
FRONTMATTER_MATRIX=124 mismatches=0
C2_FUNCTION_MATRIX=90 mismatches=0
CLI_CASES=39 old_C1=9 new_C1=9 old_C2=18 new_C2=18 consequential_mismatches=0
C1_C2_SURFACE_COMPARISON=PASS
```

护栏加宽没有扩大 C1/C2 的确定提名面。

## 四、门强度

### 1. 91 门：基线绿，但整体门强度 FAIL

```sh
cd backend
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest \
  tests/skills/test_g5_6_clear_inbox.py -q -p no:cacheprovider
```

关键逐字输出：

```text
collected 91 items
tests/skills/test_g5_6_clear_inbox.py .................................. [ 37%]
.........................................................                [100%]
======================= 91 passed, 10 warnings in 6.53s ========================
```

但：

- 标题门 [test_g5_6_clear_inbox.py:2573](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2573)只造无重复正文的 C3 样本。
- 不可见门 [test_g5_6_clear_inbox.py:2511](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2511)端到端只走 U+2063 frontmatter，没有换行型 Cc。
- 闭合注释门 [test_g5_6_clear_inbox.py:2462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2462)全是内容与 `-->` 同行，没有典型独立关闭行。

所以 91 门对门内形态承重，但没有锁住三个真实交互出口。

### 2. 变异 runner：机械判据 PASS，证明强度 PARTIAL

在 `/private/tmp` 副本重跑：

```text
M-NBSP:       2 failed, 89 passed, rc=1
M-CLAIMBOUND: 1 failed, 90 passed, rc=1
M-ZEROWIDTH:  2 failed, 89 passed, rc=1
M-GENSIGNAL:  3 failed, 88 passed, rc=1
M-SRCALIAS:   1 failed, 90 passed, rc=1
M-DOIVAL:     2 failed, 89 passed, rc=1
M-PAIRS:      1 failed, 90 passed, rc=1
M-FALLBACK:   2 failed, 89 passed, rc=1
M-INVISENUM:  1 failed, 90 passed, rc=1
M-COMMENT:    2 failed, 89 passed, rc=1
M-HEADING:    1 failed, 90 passed, rc=1

finally 还原后 sha256 = a3c6242bb84f8625b8015147a2cc6614c6d5518819d8f4ef2c4ea49834fdde5f (与基线逐字节相同)
G56C_NEGATIVE_CONTROL: PASS （11/11 变异的实际失败集合等于预先声明集合）
```

额外 URL/slept/AI 归属变异也准确杀门。故“当前 11 个变异在当前期望集合下满足集合相等、rc=1、源码还原”成立。

但 runner 把同名 `FAILED`/`ERROR` 都压成测试名。逐字模拟：

```text
parsed=['test_invisible_chars_are_detected_by_category_not_enumeration']
expected=['test_invisible_chars_are_detected_by_category_not_enumeration']
rc=1
runner_ok=True
```

因此同名 fixture/teardown ERROR 可冒充“断言被杀”。当前 91 个测试均为顶层非参数化函数，未发现现实假绿；但它只能证明“该测试名以 FAILED/ERROR 出现”，不能证明预期 assertion 确实失败。

### 3. 期望集合不是完全独立 oracle：PARTIAL · MEDIUM

[g56c_mutations.py:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:5)声称修改前推理写死、不从输出反抄；但：

- M-ZEROWIDTH 在首跑少红后改期望：[g56c_mutations.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:78)；
- M-FALLBACK 在首跑多红后扩期望：[g56c_mutations.py:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:147)；
- README 也承认实跑后修改：[README:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:104)、[README:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:163)。

所以它不是运行时动态自抄，但也不能称为完全先验、独立预言。

## 五、措辞

### 生产文件与 MD §七

| 位置 | 判定 |
|---|---|
| [inbox_preview.py:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:24)“当前登记九类” | FAIL；实现已有⑩。 |
| [偏差15:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:127) | PARTIAL/FAIL；漏⑩，也没登记已知 C4 标题/Cc 出口。 |
| [偏差16:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:175) | PASS；非法端口进 C1 但方向为留原地的声明与实测一致。 |
| [偏差17:183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:183) | 窄义 PASS；明确写了同一行/句读/动词边界，不是穷尽证明。 |
| [inbox_preview.py:811](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:811) | FAIL；仍写 U+3164/U+2800 会落 C3、标题不算正文，已被最终裁决改写。 |
| [inbox_preview.py:750](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:750) | FAIL；“顺带关闭 BLOCKER”越过 C4。 |
| [inbox_preview.py:915](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:915)、[922](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:922) | FAIL；“骨架是闭合的/才真的闭合”与偏差17自身边界声明矛盾。 |
| [MD §七:2054](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2054) | FAIL；只列八类，漏⑨任意非空值、⑩闭合注释，也没披露标题只保护 C3。 |

MD §七属于漏写和不完整；“两个出口共用护栏、一律落拿不准”的总括则比多行注释/C4 实证更宽。

### 验收单

| 位置 | 判定 |
|---|---|
| [UAT:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:5) | FAIL；仍写“白名单外”，实际白名单已取消。 |
| [UAT:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:24) | FAIL · HIGH；“3 条 + 5 条同族全部修掉”比证据宽。 |
| [UAT:58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:58)、[95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:95)、[205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:205) | FAIL；9/38、88 门、8/3 条均陈旧，当前是 91 门、11 条。 |
| [UAT:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:124) | FAIL · BLOCKER；“顺带关闭 U+3164/U+2800”被 C4 复现证伪。 |
| [UAT:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:168) | FAIL · HIGH；无条件写“漏判落拿不准”，实际存在漏判后 C4 删除。 |
| [UAT:178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:178) | PARTIAL；简单样本成立，但需补“C1/C2/C4/C5 均未先命中”的前提。 |
| [UAT:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:214) | FAIL；仍写九类/三种，漏⑩及最终标题口径。 |

### evidence README 1—9

| 节 | 判定 |
|---|---|
| §1 | PASS/PARTIAL；三份原样本当前均 C6，但先红输出与前后输入 sha 未独立保存。 |
| §2 | FAIL；仍写“三条各 1 failed, 81 passed、恰好一门”，当前为 11 条、91 门、每条红 1—3 门。 |
| §3 | PASS/PARTIAL；“不证明第四条/真实库存”诚实。 |
| §4 | PARTIAL；旧新对账有价值，但记录的 final sha 已过时，原始递归逐键输出未入包。 |
| §5 | PARTIAL；历史叙述基本诚实，8/8 原始输出已被当前 11/11 文件覆盖。 |
| §6 | PASS/PARTIAL；正确记录 `rc==1`、FAILED/ERROR 并计及 expected 曾实跑后修订。 |
| §7 | PARTIAL；“未经独立复核”是当时真实状态，但 17 样本/90 门原始逐件输出未入包。 |
| [§8:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:208) | **FAIL · BLOCKER**；漏掉其权威来源报告已经发现的四个 splitlines Cc，却写“Cf/Mn/Cc 全闭合”。 |
| [§9:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:262) | **FAIL · BLOCKER**；五个 C3 锚成立，但据此宣布整条 U+3164/U+2800 BLOCKER 关闭，越过 C4。 |

README 章节齐全，但 §8/§9 与独立报告和最终实跑冲突，不能作为“闭合”归档证据。

## 六、登记

- **BLOCKER｜历史反例未全闭合。** U+2800 C4 及四个换行型 Cc 原样仍为 `建议删 + true`。
- **BLOCKER｜标题裁决只保护 C3。** `dup_body()` 仍丢标题；U+3164/U+2800 和普通唯一标题均可在 C4 丢失。
- **HIGH｜信号⑩多行实现不完整。** `-->` 独占行时，前面注释内容未收集，URL/ISBN 在 C3/C4 双出口被确定删除。
- **HIGH｜frontmatter YAML 注释未保护。** YAML 注释中的唯一 URL/DOI 在 C3/C4 双出口被确定删除。
- **PASS｜其余历史家族。** NBSP、模型声明、DOI、长模型名、`by:`/`by_`、词内/词间零宽、重复键、ISBN、原白名单键、U+2063 族及门内单行注释均闭合。
- **PASS｜C1/C2。** 相对 `969844ef` 的确定命中面完全一致。
- **PASS｜C3 基本可达性。** 五个点名锚全部仍在，另有空 frontmatter/围栏/表格正向面；C3 未死亡。
- **MEDIUM｜门强度。** 91 门和 11 个变异对登记样本承重，但未覆盖 C4 标题、splitlines Cc、典型多行注释。
- **MEDIUM｜变异 oracle。** 最终集合固定，但部分期望曾看过首跑结果后改写；不能称完全独立先验。
- **MEDIUM/LOW｜保守少删与边界。** 空任务框/纯标点标题落 C6；fence info string 与空键名承载信息需要后续产品裁决。
- **措辞 FAIL。** 生产注释、MD §七、UAT、README §8/§9 均存在陈旧、漏写或超证据声明。

归档裁定：可以按“`f6c1fdaf` 最终独立审查不通过，BLOCKER/HIGH 仍开”归档；不可按“验收闭合、合并就绪或完成”归档。

BLOCKER/HIGH 清零: 否
