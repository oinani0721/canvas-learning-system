裁决：**不通过**。共发现 **0 BLOCKER / 4 HIGH / 3 MEDIUM / 1 LOW**。两项已裁决产品行为均未因行为本身升级；但当前仍有标题之外的正文、代码内容和来源信息进入 `建议删 + confident=true`。

限定文件绑定：

```text
3560b2ccbe429895cd2a6320532595fa55ae575eb6b7e0e9db032df55c6e58ce  inbox_preview.py
4b9fe84e283b1c514f1bb89c37b2f9c5620243d36c5d1bd0b3d1e50ffa6f37a0  test_g5_6_clear_inbox.py
```

## 一、历史反例

### 1. 前七轮危险根因：PASS_WITH_LIMITS

重跑 14 组、105 件的逐字汇总：

```text
g1_round1             10 / 拿不准10 / 建议删0
g2_round2             10 / 拿不准10 / 建议删0
g3_u2063_family        9 / 拿不准9  / 建议删0
g4_round4_matrix      10 / 拿不准9  / 建议删1
g5_splitlines          8 / 拿不准0  / 建议删8
g6_comments           10 / 拿不准9  / 建议删1
g7_old_regressions     8 / 拿不准7  / 建议删1
g8_heading_spaces      9 / 拿不准9  / 建议删0
g9_c4_history          5 / 拿不准5  / 建议删0
g10_more_invisible    10 / 拿不准10 / 建议删0
g11_more_comments     10 / 拿不准8  / 建议删2
g12_nested_c4          1 / 拿不准1  / 建议删0
g13_u2063_guard        3 / 拿不准3  / 建议删0
g14_visual_cross       2 / 拿不准1  / 建议删1
```

```json
{"groups":14,"total_items":105,"c6_false":91,"delete_true":14}
```

14 个删除件中：

- 10 件是偏差 18 覆盖的 ATX 标题 C4 样本；
- 4 件是空注释或真实精确重复对照；
- 排除两类后，历史危险删除为 0。

另对去掉裁决件/控制件的 9 组 84 件重建样本复跑：

```json
{"groups":9,"total_items":84,"c6_false":84,"delete_true":0}
```

覆盖重复 frontmatter 键、URL/DOI/ISBN、任意非空元数据、零宽/不可见字符、HTML/YAML 注释、fence info、语义运算符及信息型键名。

限制：取证包没有 105 件独立 manifest/exact-bytes 清单；105 件依赖前轮 `/private/tmp` fixture，84 件依报告重建。因此这是 `PASS_WITH_LIMITS`，不能冒充从包内独立复算了原始 105 件。

### 2. R10 三个点名修复：窄修均 PASS

命令：

```bash
backend/.venv/bin/python -B -m pytest -vv -p no:cacheprovider \
  backend/tests/skills/test_g5_6_clear_inbox.py::test_ascii_whitespace_semantics_are_not_unicode \
  backend/tests/skills/test_g5_6_clear_inbox.py::test_prefixed_url_filename_is_a_source_signal \
  backend/tests/skills/test_g5_6_clear_inbox.py::test_atx_heading_text_is_parsed_structurally
```

逐字关键输出：

```text
test_ascii_whitespace_semantics_are_not_unicode PASSED
test_prefixed_url_filename_is_a_source_signal PASSED
test_atx_heading_text_is_parsed_structurally PASSED
======================== 3 passed, 10 warnings in 0.77s ========================
```

真实入口输出：

```text
01-nbsp-tail.md	C6_undecided	拿不准	false
02-nbsp-before-hash.md	C6_undecided	拿不准	false
03-true-hardbreak-dup.md	C4_exact_duplicate	建议删	true
04-source_https_example.test.article.md	C6_undecided	拿不准	false
05-plain-dup.md	C4_exact_duplicate	建议删	true
```

所以：

- `rstrip()` → `rstrip(" \t")`：PASS；
- substring + `_` scheme 还原：点名形态 PASS；
- ATX closing `[ \t]`：PASS。

### 3. R11-H1｜HIGH：R10-H1 的 `splitlines()` 第二路径未闭合

[inbox_preview.py:637](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:637)仍先调用 Unicode `text.splitlines()`。围栏内 U+001D 被改写为行界：

```text
canonical=6060600a610a620a6060600a
candidate=6060600a611d620a6060600a
```

复现：

```bash
python3 -B canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-ea037cea-bare-fence/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-ea037cea-bare-fence/out \
  --batch-size 10
```

逐字输出：

```text
本批 1 件 · 拿不准 0 件 · 建议删 1 件
{"name":"control-in-bare-fence.md","criterion":"C4_exact_duplicate","verdict":"建议删","confident":true,"exact_duplicate_of":"节点/canonical-code-bare.md","basis":"归一化正文与 节点/canonical-code-bare.md 逐字相等（sha256 相同）","uncertain_reason":null}
```

这是围栏正文 `a<U+001D>b`，不是标题；偏差 18 不覆盖。

## 二、新构造

统一入口均为：

```bash
python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault <tmp>/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir <tmp>/out \
  --batch-size 10
```

### R11-H2｜HIGH：raw HTML block 内的非标题来源行被 C4 丢弃

分类器只维护 fence/comment 状态，[inbox_preview.py:716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:716)没有 raw HTML block 状态；[dup_body():807](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:807)对其中的 `#` 行仍按 ATX 丢弃。

正本：

```text
<pre>
</pre>
alpha
```

收件件：

```text
<pre>
# source: https://only-here.test/p
</pre>
alpha
```

收件件 bytes：

```text
3c7072653e0a2320736f757263653a2068747470733a2f2f6f6e6c792d686572652e746573742f700a3c2f7072653e0a616c7068610a
```

逐字输出：

```text
02-html-raw-source.md	C4_exact_duplicate	建议删	true	节点/canonical-html.md	归一化正文与 节点/canonical-html.md 逐字相等（sha256 相同）
```

`<pre>` 内该行是预格式化正文，不是 ATX 标题；唯一 URL 被删除，故为 HIGH。

### R11-H3｜HIGH：C3 仍以 Unicode/行级口径吞掉真实内容

残留消费者：

- `_LIST_PREFIX_RE` 使用 `\s`：[443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:443)
- `_ONLY_STRUCT_RE` 使用 `\s`：[454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:454)
- Unicode `.strip()`：[490](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:490)、[843](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:843)、[876](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:876)
- 没有 indented-code 状态。

关键输入 bytes：

```text
6060600ac2a00a6060600a  fenced NBSP
c2a02d2d2d0a            leading NBSP + ---
20202020230a            四空格缩进代码 #
092d2d2d0a              TAB 缩进代码 ---
2dc2a0230a              -<NBSP>#
```

真实入口逐字输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-r11-impl.Mi4rfa/c3/out2/inbox-preview-_待处理.json / /private/tmp/card-g56c-r11-impl.Mi4rfa/c3/out2/inbox-preview-_待处理.md
  _待处理/ 共 10 件，本批全取（10 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 10 件 · 拿不准 1 件 · 建议删 9 件
```

```text
01-fenced-NBSP.md	C3_empty_or_skeleton	建议删	true
02-leading-NBSP-divider.md	C3_empty_or_skeleton	建议删	true
03-indented-code-hash.md	C3_empty_or_skeleton	建议删	true
04-tab-code-divider.md	C3_empty_or_skeleton	建议删	true
09-list-NBSP-hash.md	C3_empty_or_skeleton	建议删	true
```

围栏内 NBSP 是字面代码内容；四空格/TAB 行是缩进代码；NBSP 分隔的 `#`/列表不构成对应 CommonMark 结构。均不属于五种已裁决 C3 面。

### R11-H4｜HIGH：URL 文件名护栏仍是有限解码

[inbox_preview.py:1579](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1579)只尝试原字、`_`→`:`/`/` 和一种 scheme 还原。标准 percent-encoded URL 仍穿透：

```text
source_https%3A%2F%2Fexample.test_article.md
```

复现输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-r11.X6fsuz/filename/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-r11.X6fsuz/filename/out/inbox-preview-_待处理.md
  _待处理/ 共 4 件，本批全取（4 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 4 件 · 拿不准 0 件 · 建议删 4 件
```

```json
{"name":"source_https%3A%2F%2Fexample.test_article.md","criterion":"C4_exact_duplicate","verdict":"建议删","confident":true,"exact_duplicate_of":"节点/generic.md","basis":"归一化正文与 节点/generic.md 逐字相等（sha256 相同）","uncertain_reason":null}
```

R10-H2 的点名 `_` 形态修好了，但来源文件名的开放编码面仍未闭合。

## 三、决策忠实度

### C4 不看标题：PARTIAL；已裁决连带不升级

实际丢弃范围是：

- 围栏外；
- line-local 匹配的 ATX H1–H6；
- 文件内所有这类行，包括任意中间小节标题。

不会丢 Setext、blockquote/list 内标题或围栏内 `#`。

纯函数逐字输出：

```text
ATX_all_equal= True
ATX_projection= '共同正文\n共同段落'
Setext_equal= False
Setext_A= '标题A\n===\n共同正文'
```

因此：

- 核心 ATX 省略行为存在；
- “多丢所有 ATX 小节标题”属于已裁决连带，只登记；
- Setext 等“少丢”是安全方向的重复漏识别；
- raw HTML 内假 ATX 行则不是标题，已按 R11-H2 升 HIGH。

### C3 五种面：五种均在，但实现不止五种

真实入口：

```text
01-zero.md	C3_empty_or_skeleton	建议删	true
02-blank.md	C3_empty_or_skeleton	建议删	true
03-dividers.md	C3_empty_or_skeleton	建议删	true
04-empty-headings.md	C3_empty_or_skeleton	建议删	true
05-quotes.md	C3_empty_or_skeleton	建议删	true
06-empty-fence.md	C3_empty_or_skeleton	建议删	true
07-empty-list.md	C3_empty_or_skeleton	建议删	true
08-empty-frontmatter.md	C3_empty_or_skeleton	建议删	true
09-empty-comment.md	C3_empty_or_skeleton	建议删	true
```

前五种全部可达；后四种没有内容或来源，故不升 B/H，但与本轮锁定的排他“五种”规格不一致，记 `R11-M1 / MEDIUM`。真正有内容的额外误伤已归 R11-H3。

## 四、门强度

### 1. 终态是 98 门，不是 92 门

命令：

```bash
env PYTHONDONTWRITEBYTECODE=1 LC_ALL=C.UTF-8 \
  backend/.venv/bin/pytest \
  backend/tests/skills/test_g5_6_clear_inbox.py \
  -q -p no:cacheprovider
```

逐字关键输出：

```text
collected 98 items
backend/tests/skills/test_g5_6_clear_inbox.py .......................... [ 26%]
........................................................................ [100%]
======================= 98 passed, 10 warnings in 6.56s ========================
```

排除最后新增六门后，旧 92 门仍可回放：

```text
collected 98 items / 6 deselected / 92 selected
92 passed, 6 deselected, 10 warnings in 6.08s
```

所以“92 门 PASS”是历史快照，不能称 ea037cea 终态。

### 2. 终态是 19 条变异，不是 12 条

我把裁判、被测脚本和只读依赖放进 `/private/tmp` 隔离副本运行，未执行原地改 worktree 的 runner：

```bash
python3 -B _bmad-output/审查/evidence-g56c/g56c_mutations.py \
  /private/tmp/card-g56c-r11.X6fsuz/mutroot
```

逐字收尾：

```text
finally 还原后 sha256 = 3560b2ccbe429895cd2a6320532595fa55ae575eb6b7e0e9db032df55c6e58ce (与基线逐字节相同)

======================================================================
G56C_NEGATIVE_CONTROL: PASS （19/19 变异的实际失败集合等于预先声明集合）
```

原 12 条是当前 19 条的前 12 条；19 轮均满足：

- 实际失败集合等于预声明集合；
- `rc == 1`；
- 还原 SHA 一致。

`FAILED/ERROR` 并计与 `rc==1` 实现正确，见 [mutation runner:335](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:335) 和 [runner:387](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:387)。

### 3. R11-M2｜MEDIUM：M-SEMWS 仍是多点变异，可掩盖单层退化

[M-SEMWS](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:255)同时撤销围栏保真和段落空行保真。

只在 `/private/tmp` 单独把 `if is_code` 退成 `if False` 后：

```text
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 4.99s
```

而该副本已经错误合并围栏内单个尾随空格：

```text
mutated_candidate= '```\nkey\n```'
mutated_canonical= '```\nkey\n```'
mutated_equal= True
```

当前生产实现正确：

```text
current_equal= False
```

所以 19/19 不能证明 M-SEMWS 的两个子层各自承重。

### 4. R11-L1｜LOW：runner 仍有证据边界

当前 19 轮没有利用这些绕过，但仍存在：

- 只保留函数名，不保留完整 nodeid；未来参数化/同名测试会被集合折叠；
- runner 内不先跑 baseline-green，本轮由独立 98/98 补足；
- 存档只绑定生产源码 SHA，不绑定 test/runner SHA；
- 空变异清单仍可真空通过：

```text
empty_mutations_allok=True count=0/0
```

## 五、措辞

复核结论为 `FAIL / R11-M3`。

- **生产文件头**：[偏差 18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:207)写到了核心代价，但未限定“所有围栏外 line-local ATX H1–H6”；[偏差 19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:214)仍把已经修复的多行 HTML/YAML 注释和空键名路径写成“未修”，却只剩 `splitlines()` 确实仍开着。[dup_body docstring](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:795)的“逐字保真”被 R11-H1 证伪。

- **生成 MD §四/§七**：[§四生成点](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2234)仍输出“逐字相同”；[§七](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2289)没有披露偏差 18，且只列八条护栏，漏⑨、⑩、键名和文件名信号。raw HTML 反例的人读输出是：

```text
## 四、重复线索

- **pre-source.md** · 逐字相同 → 正本 `节点/canonical-pre.md`
```

- **UAT**：[第 125 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:125)和[第 240 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:240)明确采用“空代码块/空列表也删”的性质口径，与本轮 exact 五种冲突；第 5/95/99/147/214/221 行同时保留 `92/12`、`88/8`、`3 条`等多套“终态”数字。

- **取证 README**：[373–374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:373)声称 `splitlines()` 路径已由“C4 不看标题”覆盖，被围栏 U+001D 直接证伪；[465–468](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:465)又否定 exact 五种；[522–533](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:522)称 R9-H1/H2 已修，但没有披露 splitlines 与 percent-encoded URL；[453–454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:453)仍写 92/12。runner 文件头也仍称“八条回退变异”。

当前诚实终态只能写：`98 passed / 19 mutations / 4 HIGH OPEN`。

## 六、登记

| ID | 等级 | 状态 | 登记 |
|---|---:|---|---|
| R11-H1 | HIGH | OPEN | `splitlines()` 抹掉围栏正文行分隔符，C4 假称逐字相同 |
| R11-H2 | HIGH | OPEN | raw HTML block 内唯一来源行被当 ATX 标题丢弃 |
| R11-H3 | HIGH | OPEN | C3 的 Unicode/行级结构判断删除 NBSP、缩进代码等真实内容 |
| R11-H4 | HIGH | OPEN | percent-encoded URL 文件名不进来源护栏，重复正文时确定删除 |
| R11-M1 | MEDIUM | OPEN | C3 五个指定面均在，但空围栏/列表/frontmatter/注释构成额外规格面 |
| R11-M2 | MEDIUM | OPEN | M-SEMWS 多点变异掩盖围栏保真单层假绿 |
| R11-M3 | MEDIUM | OPEN | 生产头、MD、UAT、README 的决策范围、终态数字及“已修”声明互相冲突 |
| R11-L1 | LOW | OPEN | mutation nodeid/provenance、baseline 与 0/0 真空通过边界 |
| R11-P1 | PASS_WITH_LIMITS | CLOSED | 历史非裁决危险根因重建样本闭合；缺原始 exact-byte manifest |
| R11-P2 | PASS | CLOSED | R10 三个点名窄修均按指定形态通过 |
| R11-P3 | PASS | CLOSED | 98 门全绿；19 个已登记 mutant 均满足集合相等、rc=1、恢复 SHA |

判据形状已经明确：

- C3 既然产品规格锁定排他的五种，就应改成五种正面、封闭的 recognizer；当前“不断剥结构、看剩余是否为空”的开放性质判定必然继续吞掉新上下文。
- C4 应保留原始代码点、行界和块级上下文，只省略经标准块解析确认、且获用户授权的 ATX heading source spans。当前 `splitlines()` 后逐行套正则的有损投影，无法让“逐字相等”成为诚实证据。

BLOCKER/HIGH 清零: 否
