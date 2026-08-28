> **存档说明**: codex exec 完成审查后被 cyber 误拦（exit 1，重定向文件空——MEMORY 已录 codex 三坑之一）。本文件由 task stdout 抢救提取，内容为 Codex round-2 原文（自"总裁定"起至结论段止），未作任何改写。

总裁定：**仍阻断 / 不可验收**。`67ccebe1` 确实冻结了交付物，92 条数字也可独立复算；但实际只有 **10/13 CLOSED**，`BLOCKER-1`、`HIGH-1`、`HIGH-3` 仍未闭合。

| 项目 | 裁定 | 复核结果 |
|---|---|---|
| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
| BLOCKER-3 | **CLOSED** | `git show 67ccebe1 --stat` 为 10 个 G4-9 文件、3384 insertions，包含脚本、报告、ledger、证据包、round-1 审查和 UAT。当前 HEAD 为 `e7a480eb`，但全部 G4-9 路径相对 `67ccebe1` diff 为空。关键 blob：script `ea370cb…`、report `ff1f71d…`、ledger `6ce5772…`。 |
| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
| MEDIUM-1 | **CLOSED（原 finding）** | 已读取 `episode_body_full`，不再完全忽略该生产字段；当前 92 条为 0。其长度门问题已计入 HIGH-1。 |
| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
| MEDIUM-3 | **CLOSED（声明性控制）** | ledger [`privacy`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:4)及报告 private-only 声明已落地。它是纪律标签，不是技术性防外发门。 |
| LOW-1 | **CLOSED** | token 已修为 `16948–20831`，截断记录声明长度修为 `205–8036`。 |
| LOW-2 | **CLOSED** | [`stable_key_semantics`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:5)已明确仅为冻结快照内 occurrence key，不再声称三列缺一不可。 |
| LOW-3 | **CLOSED** | 报告同时补齐 `LearningConcept.name` 与 `LearningTip.created_at` 两处修复证据。 |
| LOW-4 | **CLOSED** | [报告 §1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:28)已区分当前实证和未重新复证的历史 mountinfo，不再把历史断言冒充本轮证明。 |

重跑数字核验：

- live DLQ SHA 仍为 `3b37460f…ba590`，与冻结 ledger header 相同。
- 92 行 / 92 records / 0 unparseable。
- inline：`4 full_verified / 88 truncated_prefix / 0 anomaly`。
- recoverability：`4 byte_exact / 88 approximate / 0 unrecoverable`。
- class：`89 budget_400 / 2 schema / 1 group_id / 0 unexpected`。
- duplicate：`6` 簇覆盖 `29` 行，额外 occurrence `23`。
- `reference_time`：92/92 与 raw 对账；所核字段 0 mismatch。

新增低风险问题：

- **LOW**：报告称 full_verified 长度 `131–200`，实际四条为 `131/150/180/142`，范围应为 `131–180`。
- **LOW**：ledger distribution 省略 `unexpected:0`、`anomaly:0`、`unrecoverable:0`，固定 schema 消费者需自行补零。
- **LOW**：header line_count 仅数 LF，而 records 使用 `splitlines()`；bare CR/U+2028 输入可出现 header `1`、records `2`。不影响当前标准 LF 的 92 条。

审查期间未修改仓库或真实数据；破坏性反例只作用于自动清理的临时文件。未读取 transcript 内容。当前会话未提供 `graphiti-canvas`，因此无法执行其 memory search；这不影响上述本地 exact-byte、Git 与真实入口裁定。
