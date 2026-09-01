# CARD-G3-2b 对抗性审查 round-1（第九批 W7 · 清除 R1-R7 并闭合 write-ahead 六格状态机）

你是独立对抗审查者，审的是一个**本地单机学习工具**的数据完整性实现：一份 append-only 的学习事件账本（JSONL）与笔记 frontmatter 之间的 write-ahead 一致性。没有网络面、没有多租户、没有凭据；关心的全部是「崩溃/重试/账本被外部工具写坏时，会不会静默丢一次评分或重复推进一次调度」。

被审工作已 commit 在这个 git worktree（**未合并主干、未 push**）：

    WT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger
    分支 card/w7-ledger，最终 commit 91aaa11a（开工基线 02dbc426）

## 前情：本卡要收什么

前身 CARD-G3-2（第八批）经三轮审查到顶停轮。**round-3 报告**（必读：`WT/_bmad-output/审查/codex-review-CARD-G3-2-round3.md`，重点 1-45 行）在 25 门全绿的情况下，用真实生产 PYEOF 入口打穿 **2 BLOCKER + 3 HIGH + 2 MEDIUM**，记为 R1-R7。本卡只收这 7 条 + 六格状态机闭合。

| # | 级别 | round-3 原始发现 | 本卡修法 |
|---|---|---|---|
| R1 | BLOCKER | `_mine_env` 从 durable payload 自抄任意额外键，可绕 envelope 并跳过 FSRS 恢复 | candidate 改为**独立字面构造**成固定生产键集；键集本身进等价面（多一键/少一键/值不同一律冲突），只放行明确排除的两个 fsrs 身份键 |
| R2 | BLOCKER | A2 归一并消费带小数秒的 durable `review_time`，同一行二次推进 FSRS | 新增 `_durable_instant()`，在**适用集构造时逐行**强制 tz-aware + UTC 偏移 0 + 无小数秒，**只验不改** |
| R3 | HIGH | applied 态用当前 tip 的 `attempt_count` 校验历史事件，`E1→E2→重跑E1` 被误报冲突 | 沿账本回推 ordinal：已计入态 `A_now − 其后已应用数`；未计入态 `A_now + 1 + 其前 pending 数` |
| R4 | HIGH | 正常路径 mastery 用 `p["ts"]`、恢复路径用 durable `review_time`，两路径产物字节不等 | 正常路径同样传 `review_time` |
| R5 | HIGH | A2 会应用 scored rating 与 `grade_norm` 不自洽的 pending 行 | bridge 在 apply 前机械复算 `rating_from_grade(grade_norm, abandoned)` 并要求相等 |
| R6 | MEDIUM | 身份键排除策略未同步到冻结 schema | §6.2 回写四条（身份键归属 / candidate 独立构造禁令 / A5 消费侧强制 / A4.5 截断判据） |
| R7 | MEDIUM | 尾行容错丢失 EOF 的 LF 状态，带 LF 的损坏末行被当截断 | 读取时保留 EOF 的 LF 状态；只有「最后一行 **且** 文件不以 LF 结尾」才算截断 |

## 你只读以下文件

1. `WT/canvas-vault/.claude/skills/quiz-answer/SKILL.md` — **主写点**（Step 4c 的主 PYEOF 块，即 `P = "/tmp/quiz-answer-payload.json"` 那个块）
2. `WT/canvas-vault/.claude/scripts/fsrs_bridge.py`
3. `WT/backend/app/services/learning_event_log.py`（本卡**未改**，如实核对是否该改）
4. `WT/backend/tests/regression/test_g3_2_review_ledger.py` — 现 33 门（门㉖-㉝ 为本卡新增）
5. `WT/backend/scripts/g32b_r1r7_counterexamples.py` / `g32b_mutation_gates.py` / `g32b_build_fixture.py`
6. `WT/docs/learning-events-schema-v1.md` §6.1-§6.3（**契约判据唯一真相源**）
7. `WT/_bmad-output/验收单/UAT-CARD-G3-2b-write-ahead六格状态机闭合-2026-09-02.md`
8. 卡文（只读，不在本车道）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第九批-goals/W7.md`

## ⛔ 你必须亲跑生产入口，不得用绿门自述代替

round-3 的价值正在于：**25 门全绿仍被真实入口打穿**。所以：

- **不要**只读测试文件然后相信断言；
- **必须**自己用逐字提取的主 PYEOF 块（`test_g3_2_review_ledger.py` 顶部的 `_MAIN_BLOCKS` 提取法，或直接跑 `g32b_r1r7_counterexamples.py`）在隔离临时目录里构造账本/节点反例，观察真实 `rc`、真实 frontmatter、真实账本行数；
- 特别要试**本卡没想到的形态**：R1-R7 之外的键、时刻、态组合。

**已知环境点**（round-3 踩过）：只读沙箱下 pytest 若无可写 tempdir 会在收集前失败。可设 `TMPDIR` 到一个可写目录，或对 pytest 加 `--basetemp=<可写目录>`；本卡的 `g32b_*.py` 三个脚本默认写 `/private/tmp/card-g3-2b-fixture`。如果你的沙箱**任何**位置都不可写，请**如实写进「验证限制」**，不要用「门是绿的」代替实测结论。

## 建议的验证顺序

```bash
WT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger

# 裁判 1（五文件回归；本卡自报 263 collected / 262 passed, 1 skipped）
cd $WT/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest \
  tests/regression/test_learning_events_schema_contract.py \
  tests/regression/test_fsrs_bridge.py \
  tests/regression/test_learning_event_log.py \
  tests/regression/test_g3_2_review_ledger.py \
  tests/regression/test_fsrs_golden_vectors.py -q -p no:cacheprovider

# 裁判 2（R1-R7 生产入口反例；本卡自报 19/19 PASS）
PYTHONDONTWRITEBYTECODE=1 $WT/backend/.venv/bin/python $WT/backend/scripts/g32b_build_fixture.py
PYTHONDONTWRITEBYTECODE=1 $WT/backend/.venv/bin/python $WT/backend/scripts/g32b_r1r7_counterexamples.py

# 裁判 3（validator）
cd $WT/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/validate_learning_events.py /private/tmp/card-g3-2b-fixture/learning_events.jsonl

# 变异（串行，自带逐字节还原；本卡自报 10/10 KILLED）
PYTHONDONTWRITEBYTECODE=1 $WT/backend/.venv/bin/python $WT/backend/scripts/g32b_mutation_gates.py
```

⚠️ 变异脚本会**临时修改**被审源文件后立刻还原（`finally` + 逐字节 sha 比对）。若你不愿让被审文件被临时改动，跳过这一条并在报告里说明；若你跑了，请在报告末尾确认这三个文件的 sha256 与你开始审查时一致。

## 请重点攻击这些面

1. **R1 的等价面是否真的闭合**：candidate 现在是固定 8 键字面构造。durable 行还有什么形态能让 `json.dumps(..., sort_keys=True)` 两侧相等却语义不同？（键顺序、数值类型 `3` vs `3.0`、`true` vs `1`、Unicode 归一化、`ensure_ascii` 差异、`effective_at` 与 `payload.review_time` 不一致……）
2. **R2 的作用域窄化是否漏网**：只对「本节点 + `schema_ext=review/1` + 未标 `out_of_order`」的行强制整秒。标了 `out_of_order` 的行、别的节点的行、`schema_ext` 拼错的行会走哪条路？`_durable_instant` 用 `datetime.fromisoformat` + `replace("Z","+00:00")` 解析，有哪些字面量能骗过它（`+00:00:00`？`-00:00`？`Z` 出现在非结尾？）
3. **R3 的 ordinal 回推是否在所有态自洽**：多个 pending 并存、账本中同节点事件时刻相同（`(rt, line)` 全序）、`attempt_count` 在 frontmatter 缺失（按 0 起算）、`out_of_order` 行插在中间、历史行（无 `review/1` 扩展）夹杂其中——这些组合下 `_att_expect` 会不会算错并造成**误拒**（体验破损）或**误放行**（真冲突被吞）？
4. **R4 的字节等价是否只在门的 fixture 上成立**：换别的 `last_examined` / A3 bump 幅度 / `mastery_a,b` 初值，两路径还字节相同吗？degraded 路径（`fsrs_ok=False`）下 `review_time` 与恢复路径同源吗？
5. **R5 是否引入新的误拒**：`grade_norm` 是浮点，`rating_from_grade` 用 `1.0 + 3.0*gn` 分档。账本里合法写入的 `grade_norm` 与本次复算是否可能因浮点表示或 `round(GN,2)` 的时机差异跨档？历史上由**旧版本**写入的合法行会不会因此永久无法重放？
6. **R7 是否把合法情形误判**：账本以 `\r\n` 结尾、末行是空白行、文件恰好只有一个坏行且无 LF、坏行同时是唯一行——分别走哪条分支？
7. **六格状态机（门㉝）是否真的覆盖六格**：每格的前置态是否真是它宣称的那格（尤其格4 的 `_strip_calibration` 是否真的只删了 calibration 而没顺手改变别的判据）。
8. **本卡新增的三个 `g32b_*.py` 脚本自身**：安全边界断言是否可绕（`FIXTURE_ROOT` 的 resolve/symlink、marker 文件检查）；反例脚本的判据是否有「自证」成分（用被审代码的输出当期望值）。

## 输出格式

严格按下面结构，中文：

```
结论：<通过 | 需整改>

### R1-R7 逐条复核
| 项目 | 结论 | 当前证据（file:line + 你亲跑的观测） |

### 六格状态机
（逐格给 PASS/FAIL 与依据）

### Findings
[BLOCKER|HIGH|MEDIUM|LOW] <file:line> — <一句话>
依据: <你亲自跑出来的最小复现与观测值>
建议: <具体修法>

### 回归与裁判复核
（三个裁判 + 变异脚本的实跑结果；与本卡自报数字不符处必须点名）

### 验证限制
（沙箱可写性、未跑的东西、无法证明的东西）

VERDICT: <通过 | 需整改>
```

判据一律以 `docs/learning-events-schema-v1.md` §6.1-§6.3 为准；实现与契约冲突时，指出是哪一侧该改。**不要**把「本卡未实现并发锁」当作 BLOCKER——那是 G3-3 的移交范围，卡文与 UAT 均已如实声明；但如果你发现**单写者前提下**仍能丢事件或二次 apply，那就是 BLOCKER。
