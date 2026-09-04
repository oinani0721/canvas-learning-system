裁决：**不通过**。最终态绑定正确；共发现 **0 BLOCKER / 3 HIGH / 3 MEDIUM / 2 LOW**。三条 HIGH 都经真实生产入口复现，且均不属于两项已裁决产品行为。

证据绑定：

```text
$ git rev-parse HEAD
edf737ac31d079963af8fc5317c0c11838c9be9f

$ shasum -a 256 canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py backend/tests/skills/test_g5_6_clear_inbox.py
3a81045e8ec8d150f2b7e2cebda226fba997d9991aabe42cad1d019ca56e0848  canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
512a4c9e94ec15dd19dd614491072be57449ce1e0b43f7b2d490490cafc8a077  backend/tests/skills/test_g5_6_clear_inbox.py
```

限定路径 `git status --short` 无输出；所有复现仅写 `/private/tmp`。

## 一、历史反例

### 1. 历史危险根因重放：PASS_WITH_LIMITS

前九轮原始 105 件 exact bytes 没有完整保留，不能诚实声称逐字重跑 105 件。我重跑了仍在 `/private/tmp/card-g56c-r9-history.KK3488` 的 9 组、84 件重建样本：

```bash
for g in old_regressions r1_r2_fm_c3 r1_r2_fm_c4 r2_metadata_c3 \
  r3_invis_c4 r4_invis_more_c4 r5_r7_comments_c3 \
  r5_r8_comments_c4 r7_r8_struct_keys
do
  python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
    --vault "/private/tmp/card-g56c-r9-history.KK3488/$g/vault" \
    --now 2026-09-01T00:00:00+08:00 \
    --out-dir "/private/tmp/card-g56c-r9-history.KK3488/$g/edf737ac-out" \
    --batch-size 10
done
```

逐组输出：

```text
old_regressions: 共7 / 拿不准7 / 建议删0
r1_r2_fm_c3: 共10 / 拿不准10 / 建议删0
r1_r2_fm_c4: 共10 / 拿不准10 / 建议删0
r2_metadata_c3: 共8 / 拿不准8 / 建议删0
r3_invis_c4: 共10 / 拿不准10 / 建议删0
r4_invis_more_c4: 共9 / 拿不准9 / 建议删0
r5_r7_comments_c3: 共10 / 拿不准10 / 建议删0
r5_r8_comments_c4: 共10 / 拿不准10 / 建议删0
r7_r8_struct_keys: 共10 / 拿不准10 / 建议删0
{'groups': 9, 'total_items': 84, 'c6_false': 84, 'delete_true': 0}
```

覆盖的历史根因包括重复 frontmatter 键、来源值、HTML/YAML 注释、零宽字符、围栏、语义运算符、属性键名信息等。结论是 **84/84 闭合**，限制是它们并非全部原始 105 件。

另有 10 件旧反例仅把独有信息写进 ATX 标题，当前输出：

```text
本批 10 件 · 拿不准 0 件 · 建议删 10 件
Counter({('C4_exact_duplicate', '建议删', True): 10})
```

这正是偏差 18 已裁决的行为，登记为产品决策连带，不计缺陷。

### 2. R9 点名修复复核

R9-H1 点名的 ASCII 语义空白样本已修；NFD/NFC 和标题差异仍被吸收：

```text
hardbreak raw_equal=False dup_equal=False
paragraph raw_equal=False dup_equal=False
fenced-spaces raw_equal=False dup_equal=False
fenced-blank raw_equal=False dup_equal=False
nfd-nfc raw_equal=False dup_equal=True
```

R9-H3 点名样本也已修：

```text
01-hash-content.md	C6_undecided	拿不准	false
02-h7-text.md	C6_undecided	拿不准	false
04-empty-heading.md	C3_empty_or_skeleton	建议删	true
```

其中 `01` 为 `# # #`，`02` 为 `#######`。

R9-H2 的 ISBN/DOI 正面形态随全门通过，但[裁判](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2819)实际只构造 ISBN、DOI 和普通文件名，没有 URL 文件名样本；该遗漏被第二节的新反例打穿。

## 二、新构造

### R10-H1｜HIGH：C4 仍抹掉 Unicode 语义空白及围栏内行分隔符

根因位于 [`dup_body()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:790)：

- `ln.rstrip()` 剥除所有 Unicode 空白；
- `suffix.strip()` 又把两个 NBSP 当作“普通空格后缀”；
- 最终将两个 U+00A0 改写为两个 ASCII 空格。

复现：

```bash
mkdir -p /private/tmp/card-g56c-edf737ac-root.bn1VcA/semws/vault/{_待处理,节点}
printf '%s' $'alpha  \nbeta\n' \
  > /private/tmp/card-g56c-edf737ac-root.bn1VcA/semws/vault/节点/canonical.md
printf '%s' $'alpha\u00a0\u00a0\nbeta\n' \
  > /private/tmp/card-g56c-edf737ac-root.bn1VcA/semws/vault/_待处理/nbsp-tail.md

python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-edf737ac-root.bn1VcA/semws/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-edf737ac-root.bn1VcA/semws/out \
  --batch-size 10
```

逐字输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-edf737ac-root.bn1VcA/semws/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-edf737ac-root.bn1VcA/semws/out/inbox-preview-_待处理.md
  _待处理/ 共 1 件，本批全取（1 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 1 件 · 拿不准 0 件 · 建议删 1 件
canonical.md
616c70686120200a626574610a
nbsp-tail.md
616c706861c2a0c2a00a626574610a
{'name': 'nbsp-tail.md', 'criterion': 'C4_exact_duplicate', 'verdict': '建议删', 'confident': True, 'exact_duplicate_of': '节点/canonical.md', 'basis': '归一化正文与 节点/canonical.md 逐字相等（sha256 相同）', 'uncertain_reason': None}
```

两个文件字节不同、换行语义也不同，却被声明“逐字相等”。

同一证据域还有另一条实现路径：[前置 `splitlines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:630)会在围栏分类前把 U+001D 改造成行界。围栏内仅差 `a<001D>b` 与 `a\nb` 的真实入口输出：

```text
{'name': 'control-in-bare-fence.md', 'criterion': 'C4_exact_duplicate', 'verdict': '建议删', 'confident': True, 'exact_duplicate_of': '节点/canonical-code-bare.md', 'basis': '归一化正文与 节点/canonical-code-bare.md 逐字相等（sha256 相同）', 'uncertain_reason': None}
```

这是标题之外的正文差异，不受偏差 18 覆盖。

### R10-H2｜HIGH：带前缀的 URL 文件名仍穿透来源护栏

[文件名护栏](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1563)对整个 stem 使用锚定 URL 正则。只要 URL 前有 `source_`，四个 probe 都不会以 `https://` 开头。

复现：

```bash
python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-edf737ac-root.bn1VcA/fname/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-edf737ac-root.bn1VcA/fname/out \
  --batch-size 10
```

逐字输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-edf737ac-root.bn1VcA/fname/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-edf737ac-root.bn1VcA/fname/out/inbox-preview-_待处理.md
  _待处理/ 共 2 件，本批全取（2 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 2 件 · 拿不准 1 件 · 建议删 1 件
{'name': 'source_https___example.test_article.md', 'criterion': 'C4_exact_duplicate', 'verdict': '建议删', 'confident': True, 'exact_duplicate_of': '节点/generic.md', 'uncertain_reason': None, 'basis': '归一化正文与 节点/generic.md 逐字相等（sha256 相同）'}
{'name': 'https___example.test_article.md', 'criterion': 'C6_undecided', 'verdict': '拿不准', 'confident': False, 'exact_duplicate_of': '节点/generic.md', 'uncertain_reason': "文件名本身像一条来源标识（'https___example.test.article'）—— 引擎没有消费过文件名里的信息，删掉这份材料，那个标识就没有别的地方留着了；且正文与 节点/generic.md 逐字相同 —— 但「整个文件多余」只有正文证据支撑，上述信号未消化，删不删由你定", 'basis': '无机械判据可施加'}
```

四种 probe 的直接输出：

```text
source_https_example.test.article
  'source_https_example.test.article'	url_match=False
  'source:https:example.test:article'	url_match=False
  'source/https/example.test/article'	url_match=False
  'source:https/example.test/article'	url_match=False
https___example.test.article
  'https___example.test.article'	url_match=False
  'https:::example.test:article'	url_match=False
  'https///example.test/article'	url_match=False
  'https://example.test/article'	url_match=True
```

这是文件名里唯一来源被 `建议删 + confident=true`，与标题裁决无关。

### R10-H3｜HIGH：ATX closing 使用 Unicode 空白，误删有可见标题内容的文件

[`_atx_heading_text()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:458)先用 Unicode `.strip()`，随后用 `\s` 判断 closing。输入 `# <NBSP>#` 中，NBSP 不是 CommonMark closing 的 ASCII space/tab 分隔符，因此末尾 `#` 是标题内容；当前实现却返回空标题。

复现：

```bash
printf '%s' $'# \u00a0#\n' \
  > /private/tmp/card-g56c-edf737ac-root.bn1VcA/atx/vault/_待处理/03-nbsp-before-hash.md

python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-edf737ac-root.bn1VcA/atx/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-edf737ac-root.bn1VcA/atx/out \
  --batch-size 10
```

逐字输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-edf737ac-root.bn1VcA/atx/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-edf737ac-root.bn1VcA/atx/out/inbox-preview-_待处理.md
  _待处理/ 共 4 件，本批全取（4 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 4 件 · 拿不准 2 件 · 建议删 2 件
01-hash-content.md	C6_undecided	拿不准	false	无机械判据可施加
02-h7-text.md	C6_undecided	拿不准	false	无机械判据可施加
03-nbsp-before-hash.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（6 字节文件：标题 1 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）
04-empty-heading.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（3 字节文件：标题 1 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）
2320c2a0230a
```

纯函数交叉核验：

```text
hex=2320c2a0230a
repr='# \xa0#\n'
heading_text=''
substantive=False
```

这违反“标题里写了字算实质正文”，不属于 C3 五种已裁决空面。

## 三、决策忠实度

### 1. C4 不看标题：PARTIAL，核心决策存在，但实际语法范围未如实限定

[`_HEADING_RE`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:442)实际丢弃的是：

- 围栏外；
- 行首 0–3 个 ASCII 空格；
- ATX H1–H6；
- **文件中所有这类 heading 行，包括中间小节标题**。

它不会丢 Setext 标题、blockquote 内标题、HTML 标题、H7 或围栏内 `#`。

纯函数输出：

```text
all_top_level_ATX equal= True a= '正文' b= '正文'
Setext_title equal= False a= '标题A\n===\n正文' b= '标题B\n===\n正文'
blockquote_heading equal= False a= '> # 标题A\n正文' b= '> # 标题B\n正文'
ATX_no_body equal= True a= '' b= ''
```

因此：

- “不看 ATX 标题”这一核心决策实现了；
- **多丢**：不只文件首标题，所有顶层 ATX 小节标题都被丢，独有小节信息可随件删除；
- **少丢**：Setext 等标题仍参与比较，造成安全方向的重复漏识别；
- 这些属于已裁决项连带，不升级 HIGH；但“C4 不看标题”这个泛称比实际证据宽。

### 2. C3 五种面：五种都在，但实现另有空语法面

真实入口对以下五种均输出 `C3 / 建议删 / true`：

```text
01-zero.md	C3_empty_or_skeleton	建议删	true
02-blank.md	C3_empty_or_skeleton	建议删	true
03-dividers.md	C3_empty_or_skeleton	建议删	true
04-empty-headings.md	C3_empty_or_skeleton	建议删	true
05-quotes.md	C3_empty_or_skeleton	建议删	true
```

但还有：

```text
06-empty-fence.md	C3_empty_or_skeleton	建议删	true
07-empty-list.md	C3_empty_or_skeleton	建议删	true
08-empty-frontmatter.md	C3_empty_or_skeleton	建议删	true
09-empty-comment.md	C3_empty_or_skeleton	建议删	true
```

这些额外形式没有实质内容或来源，故不按用户规则升级 B/H；但若“只剩五种”是排他产品规格，则实现忠实度为 **PARTIAL / MEDIUM**。当前代码和 UAT 实际实现、描述的是更宽的性质规则：“剥掉结构后一个字符都没剩”。

第二节 R10-H3 则不同：它把真正的标题字符误判为空，构成 HIGH。

## 四、门强度

### 1. 实际是 96 门，不是 92 门

```bash
rg -c '^def test_' backend/tests/skills/test_g5_6_clear_inbox.py
env TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 LC_ALL=C.UTF-8 \
  backend/.venv/bin/pytest \
  backend/tests/skills/test_g5_6_clear_inbox.py \
  -q -p no:cacheprovider
```

逐字输出：

```text
96
........................................................................ [ 75%]
........................                                                 [100%]
======================= 96 passed, 10 warnings in 6.11s ========================
```

无 skip、xfail、deselect；96 个均为顶层非参数化测试函数。

### 2. 实际是 16 条变异；16/16 当前实跑通过

我在 `/private/tmp` 隔离副本运行，未原地修改生产文件。16 轮均满足：

- 实际失败集合等于预声明集合；
- `rc == 1`；
- 每轮从原始字节独立变异并还原；
- 最终 SHA 与工作树生产文件一致。

关键逐字输出：

```text
源码基线 sha256 = 3a81045e8ec8d150f2b7e2cebda226fba997d9991aabe42cad1d019ca56e0848

M-NBSP       2 failed, 94 passed
M-CLAIMBOUND 1 failed, 95 passed
M-ZEROWIDTH  2 failed, 94 passed
M-GENSIGNAL  3 failed, 93 passed
M-SRCALIAS   1 failed, 95 passed
M-DOIVAL     2 failed, 94 passed
M-PAIRS      1 failed, 95 passed
M-FALLBACK   2 failed, 94 passed
M-INVISENUM  1 failed, 95 passed
M-COMMENT    3 failed, 93 passed
M-HEADING    2 failed, 94 passed
M-STRUCT     2 failed, 94 passed
M-KEYNAME    1 failed, 95 passed
M-ATX        1 failed, 95 passed
M-SEMWS      1 failed, 95 passed
M-FNAME      1 failed, 95 passed

finally 还原后 sha256 = 3a81045e8ec8d150f2b7e2cebda226fba997d9991aabe42cad1d019ca56e0848 (与基线逐字节相同)
======================================================================
G56C_NEGATIVE_CONTROL: PASS （16/16 变异的实际失败集合等于预先声明集合）
```

正面机制见[变异 runner](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:330)。但 16 个 mutant 只点名 **18 个 distinct test nodes**，不能外推成“96 门逐门经变异证明承重”。

### 3. R10-M2｜MEDIUM：M-SEMWS 是多点变异，围栏保真子层可假绿

[M-SEMWS](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:251)同时：

1. 把 `if is_code` 改成 `if False`；
2. 把段落空行的 `parts.append("")` 改成 `continue`。

裁判围栏样本使用两个尾随空格；即使围栏分支失效，普通路径仍把它归一回两个空格。当前 M-SEMWS 的红只由“丢段落空行”贡献。

只退掉围栏分支后，全门逐字输出：

```text
........................................................................ [ 75%]
........................                                                 [100%]
96 passed in 5.30s
```

该变异副本：

```text
inbox_dup= '```\nkey\n```'
canon_dup= '```\nkey\n```'
dup_equal= True
```

真实入口则会对仅差围栏内一个尾随空格的两件给出：

```text
本批 1 件 · 拿不准 0 件 · 建议删 1 件
criterion=C4_exact_duplicate, verdict=建议删, confident=true, exact_duplicate_of=节点/canon.md
```

当前未变异实现对此样本是 `current_dup_equal=False`，所以这是门缺口，不是第四条生产 HIGH。应拆成段落、硬换行、围栏三个独立 mutant，并让围栏样本使用单空格或 TAB。

### 4. R10-L1｜LOW：FAILED/ERROR 并计且 rc==1，但仍有绕过面

[解析器](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:288)确实把 `FAILED`、`ERROR` 并入集合，也强制 `rc == 1`。但它只比较节点名，不锁 collected/passed/skipped/deselected，也不区分 assertion failure 与同节点 setup/teardown error。

模拟输出：

```text
FAILED_rc1: parsed=['test_gate'] rc=1 ok=True
same_node_SETUP_ERROR_rc1: parsed=['test_gate'] rc=1 ok=True
one_failed_95_skipped_rc1: parsed=['test_gate'] rc=1 ok=True
extra_ERROR_rc1: parsed=['test_gate', 'test_other'] rc=1 ok=False
collection_ERROR_rc2: parsed=[] rc=2 ok=False
empty_mutations: allok=True count=0/0
```

当前 16 轮没有利用这些绕过：全部失败数与通过数合计 96，未见 skip/deselect，抽查新增 mutant 均为 assertion `FAILED`。故只记 LOW。

## 五、措辞

复核命令：

```bash
rg -n '九类|逐字保真|rstrip|丢空行|92 门|12 条变异|88 passed|8/8|3 条回退|81 passed|已修：|只剩五种|空围栏' \
  canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  _bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md \
  _bmad-output/审查/evidence-g56c/README-取证说明.md \
  _bmad-output/审查/evidence-g56c/g56c_mutations.py
```

关键逐字输出：

```text
inbox_preview.py:25:                       当前登记九类；数字随轮次增长，此处不再写死）→ 建议删
inbox_preview.py:791:    """**逐字保真**的正文形态 —— C4「精确重复」的唯一比对依据。
inbox_preview.py:793:    只做无语义的归一：丢标题行（围栏外）、行尾空白 rstrip、丢空行、NFC。
UAT...md:95:| 终态 | **88 passed, 0 failed**
UAT...md:99:| 负验证变异（本版 8 条回退） | **8/8 实际失败集合逐个等于事先写死的名单**
UAT...md:147:- **92 门全绿 + 12 条变异的失败集合全部命中 ≠ 全称保证**
UAT...md:214:- 裁判：...（**88 条**）
UAT...md:221:- 变异取证：...（3 条回退变异）
README-取证说明.md:41:实测：三条各 `1 failed, 81 passed`
README-取证说明.md:453:| 92 门是否真承重 | — | **PASS** |
README-取证说明.md:454:| 12 条变异 | — | **PASS** |
g56c_mutations.py:2:"""CARD-G5-6c 负控：八条回退变异
```

结论：

- **生产头 PARTIAL**：偏差 18 的核心代价写到了，但“标题”未限定为“围栏外顶层 ATX H1–H6 的所有 heading 行”，尤其漏报中间小节标题也会被丢。偏差 19 又把已经修复的多行闭合注释和 YAML 注释继续写成“未修”。
- **`dup_body` docstring FAIL**：同一段同时写“逐字保真”和“rstrip、丢空行”；后半是旧实现，前半又被 R10-H1 实证证伪。
- **生成 MD §七 FAIL**：只登记 ①–⑧，漏掉实际的 ⑨非空/未知键名、⑩被剥注释、文件名来源护栏，也完全没有披露偏差 18。
- **UAT FAIL**：88/8/3 与 92/12 多套旧数字并存；实际是 96/16。它还把 C3 写成“一个字都没写的性质族”，与本轮用户锁定的“仅五种”冲突。
- **取证 README FAIL**：[§10.5.1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:516)声明 R9-H1/H2 “已修”，分别被 R10-H1、R10-H2 证伪；早期 81/8、后期 92/12 也都落后于实际 96/16。
- **数字权威源**：[当前变异输出](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations_output.txt:1)确实记录 16/16、每轮总数 96。

## 六、登记

| 编号 | 等级 | 登记 |
|---|---:|---|
| R10-H1 | HIGH | C4 仍通过 Unicode `rstrip/strip` 与前置 `splitlines()` 抹掉标题外正文差异，却输出“逐字相等”并确定删除 |
| R10-H2 | HIGH | 带前缀的 URL 文件名未被来源护栏识别，唯一来源随 C4 件确定删除 |
| R10-H3 | HIGH | ATX closing 使用 Unicode 空白，`# <NBSP>#` 的可见标题内容被误判为空骨架 |
| R10-M1 | MEDIUM | C3 实现的是“无内容性质族”，不止用户锁定的五种语法面 |
| R10-M2 | MEDIUM | M-SEMWS 多点变异掩盖围栏逐字分支，单点退化可在 96 门下假绿 |
| R10-M3 | MEDIUM | 生产头、MD §七、UAT、README 对偏差范围、护栏和修复状态的声明落后或过宽 |
| R10-L1 | LOW | 变异 parser 可由同节点 ERROR、95 skip 或空 mutation 集绕过 |
| R10-L2 | LOW | 92/12、88/8/3、81 等陈旧数字与实际 96/16 冲突 |

C4 的剩余根因已经是**证据域形状**：当前仍是“正文的有损投影相等 ⇒ 整件可删”。继续补 Unicode 字符或文件名模式无法形成封闭保证。若后续重定义，应把用户已授权的损失明确列成封闭白名单——例如 NFC、已裁决的 ATX 标题省略——除此之外保留所有代码点、行边界和围栏内容；文件名/frontmatter 则应进入完整证据域或统一作为未消化字段，而不是继续追加模式。

C3 也必须在“严格五种语法”与“任何无实质字符的性质族”之间统一实现和文档。本轮用户已明确前者，因此当前额外四类应登记为规格漂移；R10-H3 则证明现有简化 Markdown 解析器还会越界吞掉真实内容。

BLOCKER/HIGH 清零: 否

