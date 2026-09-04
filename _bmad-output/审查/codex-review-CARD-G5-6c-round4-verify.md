结论先行：**闭合 HTML 注释的 HIGH 已闭合；不可见字符 BLOCKER 未闭合。** 新实现能处理新的 Cf/Mn/Cc 普通码点，但仍被类别外视觉空白字符打穿；更严重的是，属于已声明类别 Cc 的换行型控制字符会在 `_strip_invisible()` 之前被 `splitlines()` 消耗，4/4 重新进入 C4 `建议删 + confident=true`。因此只能按“到顶不合并、整改验证失败”归档，不能登记为验收闭合。

## 一、两条闭合核验

### 1. 不可见字符：FAIL · BLOCKER

先确认以下码点均未出现在 round-3：

```sh
rg -n '2064|1BCA0|E0001|0301|1AB0|E0100|0001|200A|3164|2800|000B|000C|001C|0085' \
  _bmad-output/审查/codex-review-CARD-G5-6c-round3.md
```

逐字输出：无输出。

新类别内/类别外矩阵：

```text
01-Cf-U2064-C3.md    U+2064   Cf   INVISIBLE PLUS
02-Cf-U1BCA0-C4.md   U+1BCA0  Cf   SHORTHAND FORMAT LETTER OVERLAP
03-Cf-UE0001-C3.md   U+E0001  Cf   LANGUAGE TAG
04-Mn-U0301-C3.md    U+0301   Mn   COMBINING ACUTE ACCENT
05-Mn-U1AB0-C4.md    U+1AB0   Mn   COMBINING DOUBLED CIRCUMFLEX ACCENT
06-Mn-UE0100-C3.md   U+E0100  Mn   VARIATION SELECTOR-17
07-Cc-U0001-C3.md    U+0001   Cc   <unnamed>
08-Zs-U200A-C3.md    U+200A   Zs   HAIR SPACE
09-Lo-U3164-C3.md    U+3164   Lo   HANGUL FILLER
10-So-U2800-C4.md    U+2800   So   BRAILLE PATTERN BLANK
```

复现：

```sh
python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-r4-unicode.x0DWzv/matrix/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-r4-unicode.x0DWzv/matrix/out \
  --batch-size 10
```

逐字输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-r4-unicode.x0DWzv/matrix/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-r4-unicode.x0DWzv/matrix/out/inbox-preview-_待处理.md
  _待处理/ 共 10 件，本批全取（10 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 10 件 · 拿不准 7 件 · 建议删 3 件
```

```sh
jq -r '.items[] |
  [.name,.criterion,.verdict,(.confident|tostring),
   (.exact_duplicate_of//"null")] | @tsv' \
  /private/tmp/card-g56c-r4-unicode.x0DWzv/matrix/out/inbox-preview-_待处理.json
```

逐字输出：

```text
01-Cf-U2064-C3.md	C6_undecided	拿不准	false	null
02-Cf-U1BCA0-C4.md	C6_undecided	拿不准	false	节点/canon-cf.md
03-Cf-UE0001-C3.md	C6_undecided	拿不准	false	null
04-Mn-U0301-C3.md	C6_undecided	拿不准	false	null
05-Mn-U1AB0-C4.md	C6_undecided	拿不准	false	节点/canon-mn.md
06-Mn-UE0100-C3.md	C6_undecided	拿不准	false	null
07-Cc-U0001-C3.md	C6_undecided	拿不准	false	null
08-Zs-U200A-C3.md	C3_empty_or_skeleton	建议删	true	null
09-Lo-U3164-C3.md	C3_empty_or_skeleton	建议删	true	null
10-So-U2800-C4.md	C4_exact_duplicate	建议删	true	节点/canon-so.md
```

失败样本字节：

```text
U+200A: 232047656e657261e2808a746564206279204750542d340a
U+3164: 232047656e657261e385a4746564206279204750542d340a
U+2800: 232047656e657261e2a080746564206279204750542d340a...
```

这证明 `{Cf,Mn,Cc}` 仍是有限类别表，覆盖不了 `HAIR SPACE`、`HANGUL FILLER`、`BRAILLE PATTERN BLANK` 等视觉空白。

更强的集合内反例来自处理顺序：[head_window()` 先 `splitlines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:779)，随后才进入[类别剥离](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:829)。

输入统一为 `# Genera<Cc>ted by MODEL`，库内正本为 `ted by MODEL`：

```text
01-Cc-U000B-C4.md	U+000B	Cc	splitlines=2
02-Cc-U000C-C4.md	U+000C	Cc	splitlines=2
03-Cc-U001C-C4.md	U+001C	Cc	splitlines=2
04-Cc-U0085-C4.md	U+0085	Cc	splitlines=2
```

```sh
python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-r4-unicode.x0DWzv/splitline-cc/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-r4-unicode.x0DWzv/splitline-cc/out \
  --batch-size 10
```

逐字输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-r4-unicode.x0DWzv/splitline-cc/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-r4-unicode.x0DWzv/splitline-cc/out/inbox-preview-_待处理.md
  _待处理/ 共 4 件，本批全取（4 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 4 件 · 拿不准 0 件 · 建议删 4 件
```

```text
01-Cc-U000B-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md	null
02-Cc-U000C-C4.md	C4_exact_duplicate	建议删	true	节点/canon-2.md	null
03-Cc-U001C-C4.md	C4_exact_duplicate	建议删	true	节点/canon-3.md	null
04-Cc-U0085-C4.md	C4_exact_duplicate	建议删	true	节点/canon-4.md	null
```

这与 round-3 BLOCKER 是同一种安全出口复发，故条目 1 不能登记闭合。

### 2. 闭合 HTML 注释：PASS

覆盖多行、嵌套、标题行内、多注释、C3/C4、围栏和空注释：

```sh
python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-comments.UooGZp/comment-matrix/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-comments.UooGZp/comment-matrix/out
```

逐字输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-comments.UooGZp/comment-matrix/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-comments.UooGZp/comment-matrix/out/inbox-preview-_待处理.md
  _待处理/ 共 10 件，本批全取（10 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 10 件 · 拿不准 9 件 · 建议删 1 件
```

```text
01-c3-multiline.md	C6_undecided	拿不准	false	null
02-c3-nested.md	C6_undecided	拿不准	false	null
03-c3-inline-heading.md	C6_undecided	拿不准	false	null
04-c3-multiple.md	C6_undecided	拿不准	false	null
05-c4-inline-adjacent.md	C6_undecided	拿不准	false	节点/canonical.md
06-c4-multiline.md	C6_undecided	拿不准	false	节点/canonical.md
07-c4-nested.md	C6_undecided	拿不准	false	节点/nested-canonical.md
08-fence-unique.md	C6_undecided	拿不准	false	null
09-fence-exact.md	C4_exact_duplicate	建议删	true	节点/fence-canonical.md
10-empty-comment.md	C6_undecided	拿不准	false	null
```

`09-fence-exact.md` 不构成穿透：围栏内 `<!-- -->` 按[生产实现约定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:637)是代码正文；只有与库内同一 fenced literal 逐字相同时才进 C4。

`commented_out` 确在 unknown 兜底之前判定，静态位置为 [1410](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1410) 对 [1417](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1417)。同时带非空 `title` 的实跑逐字结果：

```text
01-c3-comment-before-fallback.md	C6_undecided	拿不准	false	null	文件里有被 HTML 注释包起来的内容（如 '<!-- internal note -->'）...
02-c4-comment-before-fallback.md	C6_undecided	拿不准	false	节点/canonical.md	文件里有被 HTML 注释包起来的内容（如 '<!-- internal note -->'）...
```

所以 round-3 的 HTML 注释 HIGH 已闭合。

## 二、新回归

### 1. C3 三种可达面仍在：PASS

```sh
jq -r '.items[] |
 [.name,.criterion,.verdict,(.confident|tostring),.basis] | @tsv' \
 /private/tmp/card-g56c-comments.UooGZp/c3-reach/out2/inbox-preview-_待处理.json
```

逐字输出：

```text
01-zero-byte.md	C3_empty_or_skeleton	建议删	true	0 字节空文件
02-no-frontmatter-skeleton.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（27 字节文件：标题 2 行、纯结构行 2 行、代码围栏 0 行、其余皆空行或注释）
03-all-empty-frontmatter.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（34 字节文件：标题 1 行、纯结构行 1 行、代码围栏 0 行、其余皆空行或注释）
```

第三件 exact text：

```text
---
title:
tags:
---
# 标题

- 
```

### 2. C1/C2 命中面：PASS

增量 diff 中检索 C1/C2 判据改动：

```sh
rg -n '^[-+].*(_is_primary_source_url|find_ai_marker|C1_source_url|C2_ai_self_declared)' \
  _bmad-output/审查/CARD-G5-6c-diff-813aff35-to-400b2692.txt
```

逐字输出：

```text
<no matches>
```

当前代表矩阵：

```text
01-c1-lower.md	C1_source_url	留原地	true	primary-record	null
02-c1-upper-scheme.md	C1_source_url	留原地	true	primary-record	null
03-c1-quoted-comment.md	C1_source_url	留原地	true	primary-record	null
04-c1-empty-host.md	C6_undecided	拿不准	false	null	null
05-c1-uppercase-key.md	C6_undecided	拿不准	false	null	null
06-c2-cn.md	C2_ai_self_declared	归档	true	secondary-synthesis	deep research 报告/
07-c2-en.md	C2_ai_self_declared	归档	true	secondary-synthesis	deep research 报告/
08-c2-case-tab.md	C2_ai_self_declared	归档	true	secondary-synthesis	deep research 报告/
09-c2-topic.md	C6_undecided	拿不准	false	null	null
10-c2-outside-window.md	C6_undecided	拿不准	false	null	null
```

结合 round-3 已复算的 baseline/final 集合相等证据（[round3:226](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/codex-review-CARD-G5-6c-round3.md:226)），可以传递判定 400b2692 未改变 C1/C2 命中面。

### 3. `Mn`：常规样本未伤，但存在保守编码不一致 · MEDIUM

普通 NFD `Café / résumé / naïve / généré par la main`、C1、C2、C3、C4：

```text
01-zero-byte.md	C3_empty_or_skeleton	建议删	true	null
02-NFD-pure-skeleton.md	C3_empty_or_skeleton	建议删	true	null
03-NFD-empty-frontmatter.md	C3_empty_or_skeleton	建议删	true	null
04-NFD-exact-duplicate.md	C4_exact_duplicate	建议删	true	节点/canon-nfc.md
05-NFD-vs-NFC-not-exact.md	C6_undecided	拿不准	false	null
06-NFD-French-heading.md	C3_empty_or_skeleton	建议删	true	null
07-NFD-C1-source.md	C1_source_url	留原地	true	null
08-NFD-C2-marker.md	C2_ai_self_declared	归档	true	null
```

但规范等价的重音编码产生不同 verdict：

```text
canonically_equal=True
NFD=23204765cc816e657261746564206279204750542d340a
NFC=232047c3a96e657261746564206279204750542d340a
01-NFD.md	C6_undecided	拿不准	false
02-NFC.md	C3_empty_or_skeleton	建议删	true
```

这是因为 NFD 的 U+0301 被当作 Mn 剥掉后，`Génerated` 变成 `Generated`；NFC 的 `é` 属于 Ll，不被剥。方向是多降 C6、少删，不定为 HIGH，但确属新增保守不一致。

### 4. 空注释也阻断 C3/C4 · MEDIUM

```text
01-empty-inline-comment.md	C6_undecided	拿不准	false	节点/canonical.md
02-empty-multiline-comment.md	C6_undecided	拿不准	false	节点/canonical.md
```

`<!---->` 与 `<!--\n\n-->` 没有注释内容，仍被当作未消化信息。这是安全方向的少删，不影响本轮 HIGH 闭合，但扩大了 C3/C4 false negative。

## 三、门强度

完整裁判当前为绿：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
backend/.venv/bin/pytest -c /dev/null -p no:cacheprovider \
backend/tests/skills/test_g5_6_clear_inbox.py -q \
--basetemp=/private/tmp/card-g56c-postr3.1AoFch/pytest-full
```

关键逐字输出：

```text
........................................................................ [ 80%]
..................                                                       [100%]
90 passed, 10 warnings in 6.06s
```

两道门对精确历史回退均承重：

```text
基线两门：
..                                                                       [100%]
2 passed in 0.28s

M-INVISENUM 精确退回六码点：
E AssertionError: U+2063 未被按类别剥掉
FAILED ../../../../../dev::test_invisible_chars_are_detected_by_category_not_enumeration
1 failed in 0.32s

M-COMMENT 清空 commented_out：
E AssertionError: 注释里的URL.md 被确定删除了
FAILED ../../../../../dev::test_source_inside_closed_html_comment_blocks_deletion
1 failed in 0.24s
```

但它们不是结构门：

```text
把实现改成恰好枚举裁判中的 15 个码点：
.                                                                        [100%]
1 passed in 0.40s

把注释实现窄成只认整行单行 <!-- ... -->：
..                                                                       [100%]
2 passed in 0.33s
```

后一窄实现下，多行闭合注释重新变为：

```text
多行注释.md	C3_empty_or_skeleton	建议删	true	null
```

因此：

- M-INVISENUM 只证明“不能退回原六码点”，不能证明“必须按类别”或“不可见字符结构闭合”。
- M-COMMENT 只锁住门内单行案例；多行、嵌套、围栏边界未由新门承重。
- 当前生产实现对这些注释形态实跑是安全的，但门不足以防后续回退。

### 「10/10 失败集合相等」：PARTIAL

生产源与存档基线绑定成立：

```text
15fd3078e310989ae636ec71185245875f5c206c2b59b7b4160a332b9385f720  inbox_preview.py
```

与 [g56c_mutations_output.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations_output.txt:1) 及最终还原 hash 相同；两条新增 exact rollback 也已在 `/private/tmp` 副本独立证明确实产生 assertion failure。

但 runner 仍在 [193–221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:193) 把 `FAILED` 和 `ERROR` 折叠成仅含 test name 的集合。复现其解析逻辑：

```sh
python3 -c 'out="ERROR tests/skills/test_g5_6_clear_inbox.py::test_invisible_chars_are_detected_by_category_not_enumeration - RuntimeError: fixture broke\n"; expected={"test_invisible_chars_are_detected_by_category_not_enumeration"}; failed={ln.split("::")[1].split(" ")[0].strip() for ln in out.splitlines() if (ln.startswith("FAILED ") or ln.startswith("ERROR ")) and "::" in ln}; rc=1; print(f"parsed={sorted(failed)}"); print(f"expected={sorted(expected)}"); print(f"rc={rc}"); print(f"runner_ok={failed == expected and rc == 1}")'
```

逐字输出：

```text
parsed=['test_invisible_chars_are_detected_by_category_not_enumeration']
expected=['test_invisible_chars_are_detected_by_category_not_enumeration']
rc=1
runner_ok=True
```

所以“10/10”在 runner 自身定义下内部一致，但不能解释为“10 个预期断言失败”：

- 同名 fixture/teardown `ERROR` 仍可冒充 `FAILED`；
- 输出只绑定生产源 hash，没有绑定裁判和 runner hash；
- runner 顶部仍写“八条回退变异”；
- 注释又明确记载部分 expected 集合是在实跑出现多红/少红后修订，并非完全独立先验。

遵守本轮禁令，未重跑会原地改源码的 mutation runner。

## 四、措辞

1. [测试名和 docstring](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2506)称“按类别而非枚举”，但 15 码点枚举实现可全绿，声明宽于门的证明能力。

2. [`_strip_invisible` docstring](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:810)称“把不可见字符替换”，实际既会替换可见组合重音 Mn，又漏掉 Zs/Lo/So 视觉空白和被 `splitlines()` 抢先消耗的 Cc，措辞过宽。

3. [源码 1340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1340)称“只收注释里有非空内容的行”，实际检查的是带分隔符的原始整行 `ln.strip()`；`<!---->` 也命中，逐字错误。

4. [裁判 1478](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:1478)残留“闭合注释空骨架仍 C3”，紧接着的注释和实际断言却要求 C6，属 LOW 自相矛盾。

5. [README §7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:171)对状态边界写得准确：明确“无独立复核、未经复核整改、到顶不合并”，没有越权宣称闭合。

6. 但 README 的“17 条原始反例全部端到端 C6”“15 样本经字节核验”没有在包内保存对应逐件命令/输出；“实际失败集合”也掩盖了 FAILED/ERROR 合并。作为历史自报可以登记，不能当独立证明。

## 五、登记

- **BLOCKER｜不可见字符护栏仍可穿透。** 类别外 U+200A/U+3164/U+2800 重现 C3/C4 确定删除；类别内 U+000B/U+000C/U+001C/U+0085 又因 `splitlines()` 先行而 4/4 重现 C4 确定删除。
- **PASS｜闭合 HTML 注释 HIGH。** C3/C4、单行、多行、嵌套、行内及 fallback 次序均闭合；围栏内按代码处理符合既有契约。
- **MEDIUM｜空注释扩大保守少删。**
- **MEDIUM｜Mn 导致 NFC/NFD 规范等价文本 verdict 不一致。**
- **MEDIUM｜两道门只承住精确历史回退，不承住结构能力。**
- **MEDIUM｜mutation runner 仍允许同名 ERROR 冒充 FAILED，且缺裁判/runner 字节绑定。**
- **LOW｜测试、源码注释和取证说明存在上述过宽或陈旧措辞。**

归档裁决建议：可按“3 轮到顶、不合并、round-3 后整改独立验证仍 FAIL”归档；不可按“整改闭合/验收通过”归档。

BLOCKER/HIGH 清零: 否
