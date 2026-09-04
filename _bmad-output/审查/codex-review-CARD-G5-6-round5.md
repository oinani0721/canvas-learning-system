结论先行：B3 / H1 / H2 / H3 / H4 五条原缺陷均为 `CONFIRMED-CLOSED`。但新回归审查实跑发现两类新的破坏性删除路径：AI 生成声明的大小写/Unicode 空白变体，以及损坏 URL 的 `Source`/`url` 别名，都会落入 `C3 / 建议删 / confident=true`。因此终裁不能清零。

被测原件与隔离副本运行前后 SHA-256 均为 `92ebcf097d1862c0657800ad3ba8716f92e83904e411ba5b81afd51865afe71f`，`cmp=0`。

## 一、五条逐条判定

### B3 围栏关闭长度　CONFIRMED-CLOSED

- 位置：[inbox_preview.py:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:521)，关闭三条件在 [536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:536)，实质正文判断在 [592](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:592)。
- 复现命令：

```sh
python3 -B /private/tmp/card-g5-6b-codex-audit.3XRBIM/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/B3/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/B3/out
```

- 实际输出：

```text
本批 1 件 · 拿不准 1 件 · 建议删 0 件
```

```json
{"name":"四反引号.md","criterion":"C6_undecided","verdict":"拿不准","target_hint":null,"confident":false}
```

- 结论：三反引号没有提前关闭四反引号围栏，`# keep` 被保留为正文。另实跑较长关闭、波浪线关闭、三空格缩进及 ASCII space/tab 尾随，均能正常关闭。

### H1 URL host 非空　CONFIRMED-CLOSED

- 位置：[inbox_preview.py:360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:360)，`urlsplit`/`hostname` 检查在 [363-372](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:363)，C1 调用在 [923](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:923)。
- 复现命令：

```sh
python3 -B /private/tmp/card-g5-6b-codex-audit.3XRBIM/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/H1/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/H1/out
```

- 实际输出：

```text
本批 2 件 · 拿不准 2 件 · 建议删 0 件
```

```json
{"name":"空host端口.md","criterion":"C6_undecided","verdict":"拿不准","nomination_type":null,"target_hint":null,"confident":false}
{"name":"空host用户.md","criterion":"C6_undecided","verdict":"拿不准","nomination_type":null,"target_hint":null,"confident":false}
```

- 结论：`https://:443/x`、`https://user@/x` 均不再伪装成 primary-record，也未翻成删除提名。

### H2 AI 标记边界　CONFIRMED-CLOSED

- 位置：标记表 [inbox_preview.py:246](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:246)，边界实现 [649-669](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:649)，C2 分支 [935](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:935)。
- 复现命令：

```sh
python3 -B /private/tmp/card-g5-6b-codex-audit.3XRBIM/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/H2/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/H2/out
```

- 实际输出：

```json
{"name":"版权话题.md","criterion":"C6_undecided","verdict":"拿不准","target_hint":null,"confident":false}
{"name":"由字版权话题.md","criterion":"C6_undecided","verdict":"拿不准","target_hint":null,"confident":false}
{"name":"评测话题.md","criterion":"C6_undecided","verdict":"拿不准","target_hint":null,"confident":false}
```

- 结论：三个原始话题反例均无确定归档。当前表中已没有 `本文由 AI`、`本报告由 AI`；题述该两项“仍在表中”与当前字节不符。

### H3 裸 URL 被吞为 frontmatter　CONFIRMED-CLOSED

- 位置：两条键正则 [inbox_preview.py:350-352](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:350)，span/map 在 [443-493](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:443)。
- 复现命令：

```sh
python3 -B /private/tmp/card-g5-6b-codex-audit.3XRBIM/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/H3/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/H3/out
```

- 实际输出：

```json
{"name":"裸URL行.md","criterion":"C6_undecided","verdict":"拿不准","basis":"无机械判据可施加","confident":false}
```

- 结论：`http://example.com/path` 保留为正文，没有 C3、删除建议或“其余皆空行”假依据。

### H4 多正本 MD 自相矛盾　CONFIRMED-CLOSED

- 位置：C4 多候选依据 [inbox_preview.py:1054](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1054)，MD §四 [1513-1529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1513)。
- 复现命令：

```sh
python3 -B /private/tmp/card-g5-6b-codex-audit.3XRBIM/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/H4/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/H4/out
```

- 实际 JSON：

```json
{"criterion":"C4_exact_duplicate","verdict":"建议删","basis":"库内已有 2 份正文逐字相同的文件：归档/乙本.md、节点/甲本.md。⛔ 哪一份算「正本」不可判（无机械依据），但收件箱这份相对它们是多余的，故仍建议删","exact_duplicate_of":"归档/乙本.md","exact_duplicate_others":["节点/甲本.md"]}
```

- 实际 MD：

```md
- **第三份.md** · 与库内 2 份文件逐字相同：归档/乙本.md、节点/甲本.md —— 哪一份是正本不可判（exact_duplicate_of 仅为字典序代表）
```

- 结论：两个候选全部呈现，字典序项只称“代表”，不再钦定正本。

## 二、新回归

### BLOCKER-1：AI 真声明的大小写/Unicode 空白变体仍会被确定删除

- 根因位置：`AI_MARKERS` 大小写敏感 [inbox_preview.py:246-260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:246)；`raw_ai_marker()` 仍只遍历同一张精确字面量表 [687-696](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:687)；漏掉后进入 C3 [994-1018](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:994)。
- 输入 SHA-256：`984eb596b411c0991bc79b28954880e80f35c6e8377652fd6352ce03bade3699`

```text
---
generator: generated by ai
---
```

- 真实命令：

```sh
python3 -B /private/tmp/card-g5-6b-codex-audit.3XRBIM/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/REG_AI_CASE/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/REG_AI_CASE/out
```

- 实际输出：

```text
本批 2 件 · 拿不准 0 件 · 建议删 2 件
```

```json
{"name":"全小写AI声明.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（35 字节文件：标题 0 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）","confident":true,"uncertain_reason":null}
{"name":"全大写AI声明.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（35 字节文件：标题 0 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）","confident":true,"uncertain_reason":null}
```

`Generated by AI`（内部两个 U+00A0）也得到相同删除结果，输入 SHA-256 为 `d25014363220980c4081ba5eede0a3f2e674250057e936551c3719d54b954495`。

这不是语义否定，也不是话题提及。漏掉 C2 本身可以是字面量方法的上限，但漏掉后产出 `建议删 + confident=true`，违反题述“漏判方向落 C6、方向安全”的限定，故为 BLOCKER。

### BLOCKER-2：损坏 URL 的常见来源键别名仍穿透护栏进入 C3

- 根因位置：C1 只取小写 `source` [inbox_preview.py:923-925](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:923)；别名只有“值已是合法 URL”才成为信号 [950-980](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:950)。裁判自己把 `url`/`URL`/`Source` 称为常见剪藏键，但只测合法值 [test:1573-1604](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:1573)。
- 输入 SHA-256：`08b338d4f63346aad1e3c14164b6056742d883e74fe89c14ddc082583b193f44`

```text
---
Source: https://:443/x
---
```

- 真实命令：

```sh
python3 -B /private/tmp/card-g5-6b-codex-audit.3XRBIM/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/REG_SOURCE_ALIAS/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g5-6b-codex-audit.3XRBIM/cases/REG_SOURCE_ALIAS/out
```

- 实际输出：

```text
本批 1 件 · 拿不准 0 件 · 建议删 1 件
```

```json
{"name":"坏Source别名空.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（31 字节文件：标题 0 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）","confident":true,"uncertain_reason":null}
```

小写 `url: https://:443/x` 也同样删除。它仍携带唯一 provenance；因 URL 损坏便把来源声明当作不存在并确定删除，与小写 `source` 的 fail-closed 护栏不一致，故为 BLOCKER。

### 其余重点连带

- H2 存量正例保持：`本文由 Deep Research 生成` → C2/`deep research 报告/`；`R99_深度调研.md` 内 `由 AI 生成` → C2/`R99/`。`Generated by AI Lab researchers` 及真实断言 `Generated by AI for internal review` 在有正文时均安全落 C6。
- H1 合法值保持：IPv6、大写 scheme、Unicode IDN 均为 `C1 / 留原地 / primary-record / confident=true`。
- H3 两条正则现已同口径。纯函数实跑：

```json
{"map":{"created":"2026-01-01T00:00:00+08:00","source":"https://quoted.test/x","tags":"","title":"x"},"spans":{"bare_url":0,"space_before":3,"tab":3,"tags":3,"timestamp":3}}
```

- C3 指定护栏均正确：非法小写 source、未解析 frontmatter 行、未闭合注释分别为 `C6 / 拿不准 / confident=false / target=null / type=null`，理由如实；无 source、全解析、注释闭合的纯骨架仍为 C3 建议删。
- C4 护栏也正确：带 `source:https://...` 的重复件为 C6，保留 `exact_duplicate_of` 和冲突；无来源正向对照仍为 C4 建议删。
- H4 含反引号路径时，§四仍完整输出 `A/甲\`一.md、B/乙\`二.md`。

## 三、门强度

### 字节码门确实承重

位置：[被测物:169-191](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:169)、[裁判:692-744](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:692)。

原样隔离副本：

```text
1 passed in 0.23s
```

仅删除 `/tmp` 副本中的 `sys.dont_write_bytecode = True`，同门精确变红：

```text
AssertionError: 运行/导入在副本树落下了字节码缓存:
[PosixPath('board-split/scripts/__pycache__')]
1 failed in 0.23s
```

恢复后副本 SHA 再次为 `92ebcf…e71f`、`cmp=0`。tmp 隔离没有让门失去承重。

### 八门与 M1–M6

| 新门 | 指定变异 |
|---|---|
| fence close | M1 |
| URL hostname | M2 |
| AI 表锁 | M3 |
| AI 边界 | M4 |
| 裸 URL frontmatter | M5 |
| frontmatter span | 无 |
| no-space key → C6 | 无 |
| H4 MD | M6 |

依据：[变异脚本:24-87](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-v6-inbox/55f50368-58ea-4aaa-883f-2c062b2f377a/scratchpad/g56b_mutations.py:24)、[输出:1-6](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-v6-inbox/55f50368-58ea-4aaa-883f-2c062b2f377a/scratchpad/g56b_mutations_output.txt:1)。

两道未被 M1–M6 指定覆盖的门并非空转：

- 单独宽化 `_FM_LOOKS_LIKE_KEY_RE` 后，span 门精确红为 `assert 3 == 0 / 1 failed`。
- 再宽化 `_FM_KEY_RE` 接受无空格值后，no-space 门精确红为 `C1_source_url != C6_undecided / 1 failed`。

但不能把 M5 的指定门输出冒充这两门自己的 kill 证据。

### 当前真实计数与否定断言

- 当前限定裁判不是题述的 69 条，也不是 UAT 的 67 条；字节相同隔离树实跑为：

```text
71 passed in 4.15s
```

- 当前变异输出也已从题述 19 条继续增长为 [22/22 killed](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-v6-inbox/55f50368-58ea-4aaa-883f-2c062b2f377a/scratchpad/g56b_mutations_output.txt:24)。
- 八门的条目定位使用 `item_by_name()`、`items[0]` 或 `next()`；条目缺失会失败，不存在题举的“item 不在清单而 `criterion != C3` 恒真”。
- `test_no_destructive_nomination_without_mechanical_evidence` 已在 [test:667-669](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:667) 增加 `assert items`，旧的空列表真空通过面已闭合。
- LOW/PARTIAL：`test_bare_ai_markers_are_removed_from_table` [test:1300-1308](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:1300) 全是 `not in`；把整个表清空后该门仍绿。带 C2 正例的边界门会交叉抓住，因此是单门不自足，不是八门整体空转。
- MEDIUM：no-space 门 [test:1343-1355](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:1343) 未锁 `confident=false`、target/type 为空和 `uncertain_reason`，可放过“拿不准但附确定去向”的回归。
- 71 门全绿仍放过上述两个 BLOCKER，说明没有覆盖 AI 大小写/内部 Unicode 空白，以及 malformed URL 别名。

## 四、措辞

| 位置 | 判定 | 审查结论 |
|---|---|---|
| 文件头“全部声明/无未声明项” [39-40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:39) | FAIL | 有限定门与定点变异无法证明穷尽；本轮两个新破坏路径直接反证。 |
| 偏差 4 [50-58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:50) | FAIL | 有限标点及语义否定说明诚实；但“漏判无正文由护栏落 C6”只覆盖仍含现有 marker 裸子串、因右边界被拒的形态，大小写/空白/同义字面量反例会 C3 删除。AI 信号编号也已从④漂为⑤。 |
| 偏差 11 [74-81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:74) | PASS/PARTIAL | 已正确限定“命中 C4 的分支”，普通及反引号路径的 §四候选完整。门只构造两候选；任意 N 的完整性主要由循环静态实现支持。且§二表格 basis 中反引号仍未转义，故“人读 MD 做反引号转义”若按全局理解仍说宽。 |
| 偏差 12 [82-90](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:82) | PASS/PARTIAL | 已有“若其余判据均不命中”前提。首行 `source:https://x` 实际因 `frontmatter_span=0` 而留作正文，不是由偏差 15 护栏兜住；仅排在合法键后的形态才走 `unparsed_fm` 护栏。 |
| MD §七重复句 [1586-1588](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1586) | PARTIAL | 宜收窄成“在重复判据中，只有正文逐字相等才建议删”，避免脱离语境读成 C3 不会建议删。 |
| MD §七护栏句 [1591-1594](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1591) | STALE | 自称“如实声明”却漏列当前实现已有的“任意键合法 URL”与 `slept_at` 两类信号；同时没有覆盖本轮 malformed URL 别名。 |
| MD §七 AI 漏判句 [1597-1601](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1597) | FAIL | “其余判据不命中时落拿不准”未说明仅适用于现表裸子串；本轮正向英文声明反例实际落 C3 删除。 |
| 验收单 | MEDIUM/STALE | [UAT:3-37](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:3) 仍说 round-4 两 BLOCKER 未修且“不做 round-5”；当前源码/裁判/变异已含 round-5 F2/F3、71 门和 M22。它安全地低估状态、没有错误授权合并，但不能作为当前字节的终态验收单。 |
| UAT 用户承诺 | FAIL/PARTIAL | [173-174](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:173) 泛称能分清“讨论 AI”和“AI 写的”，比已声明原理上限宽；[210](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:210) 的“Markdown 通行规范”比实际 CommonMark 子集宽；[214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:214) 的“必须有域名”也比实现的“hostname 非空”宽，IPv6/localhost 不要求 DNS 域名。 |
| UAT 已有五条/字节码结论 | PASS | 五条原缺陷确已闭合；[85、100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:85) 的 tmp 字节码门承重结论本轮再次得到负验证。 |

## 五、MEDIUM / LOW 登记（不续轮，仅记录）

- MEDIUM：C4 有库内正本且批内也重复时，最终确实建议删，但 `duplicate_within_batch` 冲突文字仍说“故不产出建议删”。实际 JSON 同时出现 `verdict=C4/建议删` 与该冲突，位置在 [inbox_preview.py:881-887](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:881) 和 [1021-1023](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1021)，解释自相矛盾。
- MEDIUM：UAT 当前状态、门数、变异数均与被测字节脱节；虽然 fail-closed，但证据链不可作为当前接受依据。
- MEDIUM：no-space 门未锁完整 C6 安全字段；未闭合注释门同样未完整锁定 confident/target/type/reason。
- LOW：H4 §四已转义反引号，但§二表格 basis 仍输出原始反引号；JSON 与§四保真，因此不重开 H4。
- LOW/已知上限：带正文的 `Generated by AI for…` 漏为 C6，是安全召回损失；不按 BLOCKER/HIGH 记。
- 取证边界：生产 CLI 硬依赖的 `split_preview.py` 仅作不透明字节复制，未打开分析。Graphiti/Sequential Thinking 工具本轮未挂载。checkout 中被测物、裁判和 vault 均未修改。
- 纪律披露：一个已废弃的委派轨曾因漏传 `rg` 文件参数意外做过一次全仓只读搜索；该输出全部弃用。以上所有引用结论均由主审在明确文件参数和 `/private/tmp` 字节副本上重新取证，但不能声称整个过程严格满足“从未扫仓”的纪律要求。

BLOCKER/HIGH 清零: 否
