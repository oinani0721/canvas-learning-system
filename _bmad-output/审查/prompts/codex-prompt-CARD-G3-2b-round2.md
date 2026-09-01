# CARD-G3-2b 数据完整性复核 round-2（第九批 W7 · write-ahead 账本一致性）

你是独立复核者。审的是一个**本地单机学习工具**的数据完整性实现：一份 append-only 的学习事件账本（JSONL）与笔记 frontmatter 之间的 write-ahead 一致性。没有网络面、没有多租户、没有凭据处理；关心的全部是「程序中途崩了、用户重试、或账本被别的工具写坏时，会不会静默丢一次评分、或把同一次评分重复计算两遍」。

## ⚠️ round-1 的环境教训（请照做，避免重蹈）

round-1 的报告正文**丢失了**：复核者为了跑 pytest 设了 `DEBUG=true`，仓库的 `Settings` 校验失败并把 `.env` 里某个配置值的前缀打进了报错文本，随后输出被内容策略拦下，正文没能写出来。

**请这样跑 pytest**，避免让配置值出现在任何输出里：

```bash
env PYTHONDONTWRITEBYTECODE=1 INTERNAL_API_KEY=round2-placeholder NEO4J_ENABLED=false \
    TMPDIR=<你的可写目录> .venv/bin/pytest <目标> -q -p no:cacheprovider --tb=short
```

给 `INTERNAL_API_KEY` 一个占位值即可让 `Settings` 通过，不必开 `DEBUG`。如果任何命令的输出里出现了看起来像密钥的长串，请**不要**把它抄进报告。

## 被审对象

```
WT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger
分支 card/w7-ledger，最终 commit <FINAL_COMMIT>（开工基线 02dbc426）
```

未合并主干、未 push。

## 这张卡在收什么

前身 CARD-G3-2 经三轮复核到顶停轮，第三轮用真实生产入口打穿 7 条（记 R1-R7）。本卡清除 R1-R7 + 闭合六格状态机；随后 round-1 的推理线索又暴露 5 条（记 N1-N5），一并修完。

| # | 原始问题 | 修法 |
|---|---|---|
| R1 | 比较用的 candidate 以账本行的 payload 为底 spread，未知额外键被自抄 ⇒ 「自己比自己」 | candidate 独立字面构造成固定生产键集；键集本身进等价面 |
| R2 | A2 消费带小数秒的 `review_time`，同一行被重复推进 | `_durable_instant()` 逐行强制 canonical 整秒 + UTC，**只验不改**；整秒字面判据复用校验器本体的 `_WHOLE_SECOND_RE` |
| R3 | 历史事件的 attempt 用 frontmatter 当前值校验 ⇒ `E1→E2→重跑E1` 误报冲突 | 沿账本回推 ordinal |
| R4 | 正常路径与恢复路径的 mastery 业务时刻不同源 ⇒ 产物字节不等 | 两路径统一用 durable `review_time` |
| R5 | rating 与 `grade_norm` 不自洽的行仍被应用 | apply 前机械复算 `rating_from_grade()` 并要求相等 |
| R6 | 身份键排除裁决未回写冻结契约 | §6.2 回写 |
| R7 | 带终止 LF 的损坏末行被当截断容忍 | 保留 EOF 的 LF 状态，只有「最后一行 且 文件不以 LF 结尾」才算截断 |
| N1 | 标了 `out_of_order` 但 `review_time` 晚于一切适用事件的行被无条件排除 ⇒ 该事件的调度状态永久丢失且 `rc=0` | 写点侧补语义门（`review_time > W` ⇒ fail-closed）+ 形态门（唯一合法值布尔 `true`） |
| N2 | EOF 的 LF 判据落在文本模式上（universal newlines 把裸 `\r` 读成 `\n`） | 二进制读 + 显式 decode，判据落在字节上 |
| N3 | 账本行 JSON 重复键被 `json.loads` 静默取最后一个 | `object_pairs_hook` 检测，抛不继承 `ValueError` 的自定义异常 |
| N4 | 非 UTF-8 字节抛 traceback | 捕获并 clean fail-closed |
| N5 | 多 pending 并存时硬算 attempt 期望值 | 报真因 fail-closed |

## 你只读以下文件

1. `WT/canvas-vault/.claude/skills/quiz-answer/SKILL.md` — 主写点（`P = "/tmp/quiz-answer-payload.json"` 那个 PYEOF 块）
2. `WT/canvas-vault/.claude/scripts/fsrs_bridge.py`
3. `WT/backend/app/services/learning_event_log.py`（本卡未改；请如实核对是否该改）
4. `WT/backend/tests/regression/test_g3_2_review_ledger.py` — 现 34 门（㉖-㉞ 本卡新增）
5. `WT/backend/scripts/g32b_r1r7_counterexamples.py` / `g32b_mutation_gates.py` / `g32b_build_fixture.py`
6. `WT/docs/learning-events-schema-v1.md` §6.1-§6.3（**判据唯一真相源**）
7. `WT/_bmad-output/验收单/UAT-CARD-G3-2b-write-ahead六格状态机闭合-2026-09-02.md`
8. `WT/_bmad-output/审查/codex-review-CARD-G3-2-round3.md`（前身第三轮，R1-R7 的出处）
9. 卡文（只读，不在本车道）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第九批-goals/W7.md`

## ⛔ 请亲自跑生产入口，不要用绿门自述代替

前身第三轮的价值正在于：25 门全绿仍被真实入口打穿。所以请自己用逐字提取的主 PYEOF 块（`test_g3_2_review_ledger.py` 顶部的 `_MAIN_BLOCKS` 提取法，或直接跑 `g32b_r1r7_counterexamples.py`），在隔离临时目录里构造账本/节点反例，观察真实 `rc`、真实 frontmatter、真实账本行数。

```bash
WT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger

# 裁判 1（自报 264 collected / 263 passed, 1 skipped）
cd $WT/backend && env PYTHONDONTWRITEBYTECODE=1 INTERNAL_API_KEY=round2-placeholder \
  NEO4J_ENABLED=false .venv/bin/pytest \
  tests/regression/test_learning_events_schema_contract.py \
  tests/regression/test_fsrs_bridge.py tests/regression/test_learning_event_log.py \
  tests/regression/test_g3_2_review_ledger.py tests/regression/test_fsrs_golden_vectors.py \
  -q -p no:cacheprovider

# 裁判 2（自报 29/29 PASS）
env PYTHONDONTWRITEBYTECODE=1 $WT/backend/.venv/bin/python $WT/backend/scripts/g32b_build_fixture.py
env PYTHONDONTWRITEBYTECODE=1 $WT/backend/.venv/bin/python $WT/backend/scripts/g32b_r1r7_counterexamples.py

# 裁判 3
cd $WT/backend && env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/validate_learning_events.py /private/tmp/card-g3-2b-fixture/learning_events.jsonl

# 变异（自报 17/17 KILLED；串行，自带逐字节还原）
env PYTHONDONTWRITEBYTECODE=1 $WT/backend/.venv/bin/python $WT/backend/scripts/g32b_mutation_gates.py
```

⚠️ 变异脚本会**临时修改**被审源文件后立刻还原（`finally` + 逐字节 sha 比对）。若你不愿让被审文件被临时改动，跳过它并在报告里说明；若你跑了，请在末尾确认三个源文件的 sha256 与你开始时一致。

## 请重点核查这些面

1. **等价面是否真闭合**：candidate 现在是固定 8 键字面构造。账本行还有什么形态能让两侧 canonical JSON 相等却语义不同？（数值类型 `3` vs `3.0`、`true` vs `1`、Unicode 归一化、`effective_at` 与 `payload.review_time` 不一致……）
2. **R2/N1 的作用域窄化是否漏网**：整秒门与 `out_of_order` 门只施于「本节点 + `schema_ext=review/1`」的行。`schema_ext` 拼错的行、别的节点的行、`node_id` 缺失的行分别走哪条路？`_WHOLE_SECOND_RE` 加 `utcoffset()==0` 有哪些字面量能穿过？
3. **ordinal 回推是否在所有态自洽**：同节点事件时刻相同（`(review_time, 行序)` 全序）、`attempt_count` 在 frontmatter 缺失（按 0 起算）、`out_of_order` 行插在中间、无 `review/1` 扩展的历史行夹杂其中——这些组合下 `_att_expect` 会不会算错，造成**误拒**（体验破损）或**误放行**（真冲突被吞）？`_att_expect` 可能为负吗？
4. **R4 的字节等价是否只在门的 fixture 上成立**：换别的 `last_examined` / A3 推进幅度 / `mastery_a,b` 初值，两路径还字节相同吗？degraded 路径（`fsrs_ok=False`）下 `review_time` 与恢复路径同源吗？
5. **R5 是否引入新的误拒**：`grade_norm` 是浮点，`rating_from_grade` 用 `1.0 + 3.0*gn` 分档。由**旧版本**写入的合法行会不会因浮点或 `round(GN,2)` 的时机差异跨档，从而永久无法重放？
6. **N2/N3/N4 的边界**：账本以 `\r\n` 结尾、末行是空白行、唯一行且无 LF、坏行同时是唯一行；重复键出现在顶层而非 payload；非 UTF-8 字节出现在第一行——分别走哪条分支？
7. **六格状态机（门㉝）是否真覆盖六格**：每格的前置态是否真是它宣称的那格（尤其格4 的 `_strip_calibration` 是否只删了 calibration 而没顺手改变别的判据）。
8. **三个 `g32b_*.py` 脚本自身**：安全边界断言是否可绕（`FIXTURE_ROOT` 的 resolve/symlink、marker 文件检查）；反例脚本的判据是否有「自证」成分（拿被审代码的输出当期望值）。
9. **UAT 是否过承诺**：`UAT-…-2026-09-02.md` 的每一条「证明了什么/不证明什么」是否与实际证据严格对应。

## 输出格式

严格按下面结构，中文：

```
结论：<通过 | 需整改>

### R1-R7 + N1-N5 逐条复核
| 项目 | 结论 | 当前证据（file:line + 你亲跑的观测） |

### 六格状态机
（逐格给 PASS/FAIL 与依据）

### Findings
[BLOCKER|HIGH|MEDIUM|LOW] <file:line> — <一句话>
依据: <你亲自跑出来的最小复现与观测值>
建议: <具体修法>

### 回归与裁判复核
（三个裁判 + 变异脚本的实跑结果；与自报数字不符处必须点名）

### 验证限制
（沙箱可写性、未跑的东西、无法证明的东西）

VERDICT: <通过 | 需整改>
```

判据一律以 `docs/learning-events-schema-v1.md` §6.1-§6.3 为准；实现与契约冲突时，指出是哪一侧该改。**不要**把「本卡未实现并发锁」当作 BLOCKER——那是 G3-3 的移交范围，卡文与 UAT 均已如实声明；但如果你发现**单写者前提下**仍能丢事件或重复计算，那就是 BLOCKER。
