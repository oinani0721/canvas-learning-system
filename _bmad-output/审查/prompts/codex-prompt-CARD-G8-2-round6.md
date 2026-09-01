# CARD-G8-2 独立对抗审查（round-6 · 用户授权定向续轮第三轮）

你是独立审查者。round-1/2/3/4/5 存档于 codex-review-CARD-G8-2*.md；round-5 你判
0 BLOCKER + 2 HIGH。本轮只复核这 2 条的整改与其余 MEDIUM 顺带项。工作目录 =
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、round-5 两条 HIGH 的整改声明（证伪优先，不成立标 REGRESSED）

### HIGH-1：closer 必须与 opener **严格等长**（"≥" 是 fenced 规则不是 span 规则）

整改：`_strip_code_spans` 的配对条件由 `runs[j][2] < runs[i][2]`（跳过更短）改为
`runs[j][2] != runs[i][2]`（跳过一切不等长）。你的反例 `` `x``[[A]]` ``（MarkdownIt:
opener/closer 均单反引号、content='x``[[A]]'）下 [[A]] 必须在 span 内被剥、A 报孤儿。
新门 `test_code_span_closer_must_equal_opener`（fixture 逐字取自你的反例）。
变异 M16 恢复（closer 退回 ≥ 语义）指定杀该门——同时回应你 round-5 M1「M16 删除理由不成立」。

### HIGH-2：span 剥除后空串拼接制造伪 wikilink

整改：`_strip_code_spans` 的删除区间改为**空格占位**（`text[prev:s] + " "`）——
「[`x`[A]]」剥 span 后是「[ [A]]」而非「[[A]]」。新门
`test_code_span_removal_leaves_placeholder_not_concatenation`（fixture 逐字取自你的反例）。
变异 M21（占位退回空串拼接）指定杀该门。

### round-5 三条 MEDIUM 顺带整改

- M1（M16 删除理由不成立）：M16 已按上表恢复，与新门配套。
- M2（UAT 终态陈旧）：全文统一 round-6 终态（186 passed / 21 mutant / SHA 0414a573…）；
  历史 round 段落标注「时点快照」；附 C 增补 round-4/5 对照表。
- M3（--help 未同步盲区契约）：epilog raw_derived 行补「或存在扫描盲区 (G8/G10/G11 /
  recap 越界拒读)」；help-full.txt 以当前字节重存。`--help | cmp help-full.txt` 应 rc=0。

## 二、终态裁判（当前字节，MANIFEST 绑定）

- 裁判 1：referee1-pytest-full-round6.txt = **186 passed**（67 本卡 + G8-1 119 零回归）
- 变异：**21/21 KILLED**（M13 并入 M20、M16 恢复为新锚、新增 M19/M20/M21；transcripts/ 全存档）
- live 第六轮取证：sha `a82e3af0…` 前后逐字相同 rc=0（live-window-round6.txt 时间戳）
- 禁改门空；MANIFEST 5 源码/测试 + 全部活跃证据（comm -3 空）

## 三、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
round-5 两条若整改不成立标 REGRESSED；整改引入的新面单列。
最后一行：`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
