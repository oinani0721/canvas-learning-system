# CARD-G8-2 独立对抗审查（round-5 · 用户授权定向续轮第二轮）

你是独立审查者。round-1/2/3/4 存档于 codex-review-CARD-G8-2*.md；round-4 你判
0 BLOCKER + 2 HIGH。本轮复核这 2 条的整改。工作目录 =
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、round-4 两条 HIGH 的整改声明（证伪优先，不成立标 REGRESSED）

### HIGH-1：G8/G10/G11 盲区不计入 raw_derived 状态

整改：`vault_lint.py` check_raw_derived 的状态改为
`WARN if (findings or recap_blind or blind) else OK`（blind = cvr 的 G8/G10/G11 集合）。
新门 `test_raw_derived_g8_blind_forces_warn`：`节点/sub -> vault 外` fixture 断言
CheckResult WARN + blind_spots ≥1 + **CLI JSON** checks[0].status=warn / details.blind_spots ≥1 /
rc=2（同时闭合你 round-4 的 M18-2「只查内部 CheckResult 不够」）。
变异 M19（状态判定去掉 blind）指定杀该门。

### HIGH-2：`(\\`+)[^\\`]*\\1` 不保证 maximal delimiter run

整改：删除该正则，新增 `_strip_code_spans(text)`——按 CommonMark 算法扫描 **maximal**
backtick run（`re.finditer(r"`+")` 不可分割），opener 之后的第一个长度 ≥ opener 的 run 为
closer，两者同时消费。你的反例 `` ``[[A]] ` foo`` ``（MarkdownIt 判整体一个 code_inline）下
[[A]] 必须被剥、A 报孤儿。新门 `test_code_span_commonmark_maximal_run`（fixture 逐字取自你的
round-4 反例）。变异 M20（退回旧正则）指定杀该门。旧 M13/M16 变异已删除（其锚指向的正则行
不复存在，语义被 M20 更强覆盖——删除原因写进 harness 注释）。

### round-4 两条 MEDIUM 顺带整改

- M17（越界守卫顺序）：新门 `test_projection_outside_guard_precedes_read` 用
  monkeypatch `_read_text` 为「读取即炸」锁守卫先于读取（「先读再返回 corrupt」变异必红）。
- M18-2（CLI JSON 契约）：并入 `test_raw_derived_g8_blind_forces_warn`（见上）。
- UAT 终态陈旧：全文统一 round-5 终态数字（184 passed / 19 mutant / 现行 SHA
  vault_lint.py=a8234c15…）；历史 round 段落标注「时点快照」。

## 二、终态裁判（当前字节，MANIFEST 绑定）

- 裁判 1：referee1-pytest-full-round5.txt = **184 passed**（65 本卡 + G8-1 119 零回归）
- 变异：**19/19 KILLED**（M13/M16 删除后共 19 个，transcripts/ 全存档；M19/M20 为新防线）
- live 第五轮取证：sha `a82e3af0…` 前后逐字相同，rc=0，与 JSON summary 一致
- 禁改门空；MANIFEST 全覆盖（5 源码/测试 + 全部活跃证据含 19 份 transcript）

## 三、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
round-4 两条若整改不成立标 REGRESSED；若发现整改引入的新面请单列。
最后一行：`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
