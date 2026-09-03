结论：需整改

### 33 条规则逐条判断（第 20/21/33 条已按本轮改动重写，见上）

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | PASS（“8 键”计数措辞不准） | candidate 独立构造，未从 durable payload 复制；环境快照两键被排除：[SKILL.md:1389-1402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1389)、[SKILL.md:1579-1591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1579)。实际比较结构为 4 个外层事实加 7 个 payload 事实，并非字面 8 个 JSON 键。相关行为门包含在 `306 passed` 中。 |
| 2 | PASS | durable `review_time` 先过 validator，再要求整秒、UTC offset=0，只验不改：[SKILL.md:334-361](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:334)、[SKILL.md:1152-1154](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1152)。非 UTC、小数秒行实跑均 `rc=1`。 |
| 3 | FAIL | F1-only 的期望序数只折算 `_applicable` 后继：[SKILL.md:1292-1317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1292)，而 §6.3 行已在 [SKILL.md:1166-1186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1166) 跳过。E1/E2 完成、仅保留 E2 为合法 §6.3 行后，validator `rc=0`，E1 重跑 `rc=1`：`attempt_count 1 != 期望 2`。 |
| 4 | PASS（按本轮收窄范围） | 本写点生成的 durable 行在正常/崩溃恢复两路径均取日志锁定的评分、采用时刻和序数：[SKILL.md:1773-1819](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1773)、[SKILL.md:1821-1899](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1821)。小数秒、offset、已有 W 两例恢复均 `rc=0`、节点 bytes 相同。对辅助输入不承诺整节点相同，这个收窄诚实。 |
| 5 | PASS | `validate_record_full()` 与消费侧 rating/grade 完整性门均在 apply 前：[SKILL.md:1152-1154](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1152)、[SKILL.md:1215-1220](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1215)。缺失、bool、越界和档位不自洽门均通过测试。 |
| 6 | FAIL | 规格没有回写本轮 B②。[schema:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:190) 仍写“无 receipt 时 W 为空、`review_time == scored_at`”；[schema:153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:153) 和 [schema:327](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:327) 仍把已修的 bridge 行为列为待修。 |
| 7 | PASS | 最后非空字节行是否有 LF 的判断在 [SKILL.md:753-805](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:753)。无 LF 坏末行按截断容忍；有 LF 坏末行实跑 `rc=1`。 |
| 8 | PASS | `out_of_order` 只接受布尔 `true`，且要求 `review_time <= W`：[SKILL.md:1196-1208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1196)。伪装为乱序的未来行实跑被拒。 |
| 9 | FAIL（规则文字错，代码与 validator 一致） | 实现并不“剥首行 BOM”，而是在 [SKILL.md:767-770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:767) 直接拒绝；后面的 `utf-8-sig` 分支不可达。validator 同样拒 BOM。应改规则文字，不应放宽实现。 |
| 10 | PASS | 深层对象重复键由 `object_pairs_hook` 拒绝：[SKILL.md:378-384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:378)、[validator:115-127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/scripts/validate_learning_events.py:115)。完整坏末行也不会被误当截断。 |
| 11 | FAIL（规则比现规格更严） | 两条全为 foreign 的 pending 会被依序恢复，而非预先停下：[SKILL.md:1641-1771](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1641)。首轮 `rc=1`，但 stdout 已显示恢复 2 条，W 和节点已发布；[schema:160-162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:160) 本身要求“pending 重放至空”，未写“多个即停”。 |
| 12 | PASS | [六格测试:1255-1319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1255) 单跑 `1 passed`；六个前置状态均真实构成，断言检查 rc、哈希、W、receipt 和行数，不是恒真断言。 |
| 13 | PASS | 顶层非 object、不可用 `node_id`、本节点缺 payload 都在归属跳过前拒绝：[SKILL.md:1111-1144](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1111)。坏 foreign 行不会阻塞本节点，相关双向测试均通过。 |
| 14 | PASS（分支本身） | foreign 未应用事件逐项复放 FSRS、mastery、last_examined、calibration、attempt；本次事件排除 mastery 重放：[SKILL.md:1643-1724](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1643)。格 1 实跑终态账本 2 行、tip=2。其“是否已应用”前提仍受规则 15/21 缺陷影响。 |
| 15 | FAIL | “校准里有它”的语义判定不可靠。`id_form` 反例中 receipt 属于完整 ID `quiz:K`，却被解释为另一个 `quiz:quiz:K` 已应用；writer `rc=0` no-op、attempt 仍 1。判据可以为真而事件事实并未应用。 |
| 16 | FAIL | 全账扫描确实位于早退前：[SKILL.md:1257-1274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1257)，但规则 21 的 full/bare 错绑可把“校准没有该事件”误判为“已有”，从而绕过本门。 |
| 17 | PASS（按规则 28 收窄） | 本次 ID 在 [SKILL.md:211-227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:211) 拒空白；durable 扫描只管本节点：[SKILL.md:814-829](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:814)。本节点空白 ID `rc=1`，foreign §6.3 空白 ID不阻塞。 |
| 18 | PASS | 事件类型、concept/node、vault 绑定在 validator 后再次检查：[SKILL.md:1152-1195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1152)。同键异主/异型定向测试通过。 |
| 19 | PASS | 非法 marker 或无 marker 却带 review 扩展键先被 validator/纵深门拒；真正 §6.3 行跳过：[SKILL.md:1166-1186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1166)。 |
| 20 | FAIL（主体顺序正确，但存在未登记误拒） | `validate_record_full()` 的顺序正确，合法 §6.3 也不会因完整校验误拒；但 validator-valid 的旧/外部 `grade_norm=0.752` 行可被 foreign replay，却在原事件自己重跑时被入口 `.75` candidate 判 envelope 冲突。实跑 validator `rc=0`、恢复成功，原白板重跑 `rc=1`。 |
| 21 | FAIL | marker 约束只在 `_sources` 为空时执行：[SKILL.md:549-580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:549)。来源非空时，标为 full 的裸 token 仍可回落到另一完整 ID。实跑 writer `rc=0` 静默漏算。 |
| 22 | PASS | `ts` 与稳定业务时刻分别经 validator 正则 `fullmatch`，拒而不洗：[SKILL.md:258-285](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:258)。首尾空白/换行/非法日期最终均在 append 前 `rc=1`。 |
| 23 | FAIL（只覆盖 `review/1` 后继） | duplicate/F1 的后继确实用 calibration 而非 W：[SKILL.md:1292-1317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1292)、[SKILL.md:1426-1430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1426)，但完全遗漏 §6.3 后继。 |
| 24 | FAIL（只修了 dup 分支） | dup 分支会利用后继行自身序数/行序证明：[SKILL.md:1433-1494](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1433)；F1-only 没有对应实现。§6.3 后继反例 validator `rc=0`、retry `rc=1`。 |
| 25 | PASS | `_SCORED_AT` 取本次稳定输入，并由 candidate 独立使用，不抄 durable 或本轮执行时刻：[SKILL.md:258-267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:258)、[SKILL.md:1381-1387](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1381)。稳定 10:00、重跑记录时刻变化的恢复例 `rc=0`。 |
| 26 | FAIL | dup 分支能跨 k 条行折算 gap：[SKILL.md:1466-1494](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1466)；F1-only 仍把被排除的历史贡献当 0，未共享这套证明。 |
| 27 | FAIL | 规则要求缺原始稳定时刻即停；实现却告警后回落 `review_time`：[SKILL.md:1221-1236](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1221)、[SKILL.md:1560-1578](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1560)。已实跑形成不同原始时刻静默别名。 |
| 28 | PASS | 无 marker 历史行上的 `out_of_order` 不具契约语义；calibration 使用 `yaml.safe_load`；空白 ID 只阻断本节点：[SKILL.md:410-422](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:410)、[SKILL.md:1473-1487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1473)。尾注释/键顺序变体测试通过。 |
| 29 | PASS | 全文件重复 ID 在消费前拒绝：[SKILL.md:806-832](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:806)；新记录 append 前完整自检：[SKILL.md:1928-1939](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1928)；唯一性证据未注入当前候选。相关门通过。 |
| 30 | FAIL | receipt 字段较以前完整，但 full/bare 来源错绑、缺 `scored_at` 回落和 `exam_board` 类型别名均可打穿“同一次评分”证明。最小 board 反例第二次 `rc=0`、ledger 0 bytes。 |
| 31 | FAIL | 六处归属比较使用 `_nkey` 的部分正确；但 receipt 事实比较在 [SKILL.md:605-612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:605) 使用 Python `!=`，`{"k":1}` 与 `{"k":true}` 被判相等，不是严格 JSON 事实比较。 |
| 32 | FAIL | 有 receipt 的三方绑定、F1-only 的 W 覆盖和写前预演已存在；但无 receipt 的证明只覆盖当前 dup，foreign pending 在 [SKILL.md:1643-1647](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1643) 未先复算 adopted，缺 `scored_at` 时 dup 证明也被跳过。 |
| 33 | FAIL | F1 后继在 [SKILL.md:1301-1303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1301) 手写 exact/bare；foreign guard 在 [SKILL.md:1688-1691](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1688) 又手写一次。所谓唯一实现的静态门只数特定源码字面：[test:3548-3574](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:3548)，因此误报通过。 |

B② 的实现语义核对结果是 PASS，但不是“代码级逐字同源”：主块 [SKILL.md:297-311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:297) 与 bridge [fsrs_bridge.py:192-251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/scripts/fsrs_bridge.py:192) 分别实现了同一序列。可达输入均先保证 aware，因此 bridge 的 `.strip()`、naive 拒绝等差异不会出现：

- 新卡 `18:00:00.731+08:00` → adopted/W `10:00:00Z`。
- 已有 `W=10:00:00Z` 时，同一输入 → adopted `10:00:01Z`。
- 两例崩溃恢复均 `rc=0`、节点 bytes 与直接成功相同。

HIGH① 的 `adopted > 当前 W` 收窄对 dup 分支本身正确：已应用且无 receipt 的行最终在 [SKILL.md:1619-1622](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1619) 停下，不会静默恢复。新的缺口是 foreign pending 未做同款证明，以及缺 `scored_at` 会跳过证明。

八处与 validator 重合的检查不是当前实现缺陷。[schema:201-202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:201) 实际已经明确称其为“同口径防御性复核及消费侧加严”。无需为了措辞删除；若要降低维护风险，应抽共享 helper。`_instant_only().strip()` 当前也确实不可被带空白值到达：账本行先过 validator，receipt `ts` 在调用前按字面拒绝。

### 六种状态

| 状态 | 结果 | 实际前置与观测 |
|---|---|---|
| 1. `dup=F, F1=F` | PASS | W=None，预置一条 foreign pending；`run_settled rc=0`，首阶段确有“恢复已落定”，终态账本 2 行、W=08-02。 |
| 2. `dup=F, F1=T` | PASS | 当前事件日志行删除，但 receipt、W=08-02、attempt=2 保留；重跑 `rc=0`，旧写序 no-op，节点 SHA 不变、账本 1 行。 |
| 3. `dup=T, F1=T, applied=T` | PASS | W 覆盖 durable 时刻；重跑 `rc=0`，“幂等跳过”，节点 SHA 不变、账本 1 行。 |
| 4. `dup=T, F1=F, applied=T` | PASS | 删除 calibration，W 仍覆盖；`rc=1`，报“缺校准记录/人工核对”，节点及账本零写。 |
| 5. `dup=T, F1=T, applied=F` | PASS | degraded 首写后 receipt/attempt 已有、W=None；恢复 `rc=0`，只补 FSRS，W=TS1，mastery/attempt 各行逐字不变。 |
| 6. `dup=T, F1=F, applied=F` | PASS | 模拟 append 后发布前崩溃；恢复 `rc=0`，W=TS1，节点 bytes 与直接成功完全相同、账本仍 1 行。 |

六格测试构造真实，未发现恒真结果断言；但它没有覆盖 full-marker/非空来源错绑、§6.3 F1 后继、三位小数原白板落定、board null/bool 或 foreign adopted 篡改。

### 问题清单

[BLOCKER] [SKILL.md:425-452,549-586](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:425) — `id_form: full` 在来源集合非空时仍可被解释为另一 ID 的裸形态。  
依据: 正常写本地 `K`，得到 receipt `quiz:K, id_form:full`、attempt=1；外部仅把 ledger ID 改为 `quiz:quiz:K`，validator `rc=0`；提交新本地 ID `quiz:K` 后 writer `rc=0`，输出“已完整应用，幂等跳过”，ledger 仍仅 `["quiz:quiz:K"]`、receipt 仍 `quiz:K`、attempt 仍 1、节点/账本零改。  
建议: marker 必须在候选解释阶段生效：标为 full 的 token 只能满足 `token == ev_id`；只有无 marker 的 legacy token 才允许 bare 回落，之后再做来源唯一性证明。

[BLOCKER] [SKILL.md:1221-1236,1560-1578](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1221) — 缺 `scored_at` 时回落 adopted time，可把两个不同原始时刻别名为同一次评分。  
依据: E0@10:00 成功；E1 原始也是 10:00，A3 adopted=10:00:01；删除 E1 的 `payload.scored_at` 并把节点回滚到 E0，validator `rc=0`；以同 ID、原始时刻 10:00:01 重跑，writer `rc=0`，账本仍 2 行、attempt=2，新的评分事实未入账。  
建议: 消费任何 `review/1` 行缺 `scored_at` 一律停；旧行走明确迁移。同步把该要求写入 §6.1/A8；若未来允许改 validator，再加入必填门。

[BLOCKER] [SKILL.md:474-485,605-612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:474) — `exam_board` 使用 Python 相等语义，可把不同 JSON 事实当作同一次评分。  
依据: 首次 `exam_board={"k":1}` 得 `rc=0`；清空 ledger 后，以相同 ID/time/grade、`exam_board={"k":true}` 重跑，writer `rc=0` 幂等 no-op，ledger 0 bytes、attempt 仍 1、receipt 仍 `{"k":1}`。此外 `None/True/False` 都是 writer 可产、validator `rc=0` 的值，但同输入重跑均 `rc=1`。  
建议: 以类型敏感的 canonical JSON 比较事实，用 sentinel 区分键缺失与显式 null；或者在 schema、validator、producer 三处统一冻结为 string。不能只改 `_ok_board` 一处。

[HIGH] [SKILL.md:1292-1317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1292) — F1-only 后继折算漏掉真实会推进 attempt 的 §6.3 行。  
依据: 用真实旧写点产生 E2 历史行后，只删除 E1 ledger 行；E2 无 `schema_ext`，validator `rc=0`，tip=2；当前 writer 原样重跑 E1 得 `rc=1`，报 `attempt_count 1 != 期望 2`，节点/账本零写。无 `attempt_count` 的 §6.3 变体同样失败。  
建议: 抽共享 ordinal-proof helper，按 append 行序纳入全部同节点评分后继；有 receipt/序数时折算，无证据时指明具体历史行和缺口后停，不能按贡献 0 计算。

[HIGH] [SKILL.md:196-203,1578-1591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:196) — 三位小数旧/外部行能被恢复，却不能由原白板重跑落定。  
依据: durable E1 改为 validator-valid `grade_norm=0.752`；E2 首阶段成功恢复 E1，receipt 保留 `0.752`、attempt=1、W=10:00；随后原 E1 以输入 `0.752` 重跑得 `rc=1`、`canonical envelope` 冲突，节点和账本零写。现有 [M121 测试:4098-4131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:4098) 明确绕开 dup，只证明 foreign replay。  
建议: 为“当前 writer 两位小数”与“旧/外部原精度”定义显式、类型安全的版本化身份规则；例如对不可由当前 writer 产出的多位 durable 值要求原始输入精确匹配，再使用该输入构造 legacy candidate。若业务只允许两位，则须先收紧 schema/validator并提供迁移，不能仅入口舍入。

[HIGH] [SKILL.md:1537-1577,1643-1647](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1537) — 无 receipt 的 adopted-time 证明只覆盖当前 dup，foreign pending 可携带任意采用时刻被重放。  
依据: 新节点放一条 foreign pending：`scored_at=08-01`，但 `review_time/effective_at=12-01`；validator `rc=0`。提交 08-02 当前事件后 `run_settled rc=0`，attempts=`[1,2]`，W 被推进至 `2026-12-01T10:00:01Z`。  
建议: 每条 pending 在调用 bridge 前，以当时内存 frontmatter 的 W 和该行 `scored_at` 复算 adopted time并比较；顺序重放时每应用一行后更新下一行的基线。缺 `scored_at` 停下迁移。

[MEDIUM] [schema:153,190,327](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:190) — B② 与 bridge 的规格描述仍是旧结论。  
依据: 实现及实跑均证明 W 非空崩溃窗必须复算，offset/小数秒也合法收敛；规格仍要求 W 空和字面相等。  
建议: 规格改成“原始时刻 UTC 化→截整秒→若 `<= 当时W` 则 `W+1s`，按瞬间比较”，并删除已完成的 bridge 移交描述；不要回退正确实现。

[MEDIUM] [SKILL.md:1736-1771](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1736) — 规则 11、现有 N5 测试标题与真实覆盖不一致。  
依据: 两条全 foreign pending 会先全部发布，首轮虽 `rc=1` 但已改变节点；N5 只测试“当前事件 + foreign”的混合队列：[test:1404-1424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1404)。  
建议: 以当前规格为准，应删除“多个一律停”的规则并修正测试说明；若产品确实选择更保守策略，则必须先改规格，再在任何 bridge 调用前零写拒绝 `len(pending)>1`。

[MEDIUM] [SKILL.md:1301-1303,1688-1691](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1301) — 规则 33 声称的单一 resolver 并不存在，静态门欠判。  
依据: helper 外仍有两份 exact/bare 选择；现有静态门只匹配 `_cands.append(_bare)` 等特定字面，77 tests 全绿也未发现。  
建议: F1 probe 由统一 resolver 返回实际命中 token/receipt；foreign 路径无条件调用 resolver。静态门禁止 helper 外出现前缀切片或双 `_receipt_of` 探测。

[LOW] [SKILL.md:767-776](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:767) — 规则 9 声称剥 BOM，但实现和 validator 都拒 BOM，且留下不可达 `utf-8-sig` 分支。  
依据: BOM 文件实跑 writer/validator 均 `rc=1`。  
建议: 把规则改为“首行 BOM 拒绝”，删除死分支。

[LOW] [SKILL.md:1626-1629](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1626) — 注释仍称“只复算 FSRS、mastery 无载荷”，与后续真实复放和 [schema:208-212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:208) 相反。  
依据: 格 1 实际复放 mastery/calibration/attempt；行为正确，仅注释陈旧。  
建议: 更新注释，避免下一轮据此再次做错裁决。

### 测试复核

按指定环境实跑五文件：

```text
collected 307 items
306 passed, 1 skipped, 10 warnings in 81.43s
exit 0
```

自报数字一致。skip 是 [test_repo_vault_ledger_schema_v1:1104-1111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_learning_events_schema_contract.py:1104)，原因是该 worktree 不存在 `canvas-vault/learning_events.jsonl`；不是 FSRS 降级测试。

`test_g3_2_review_ledger.py` 确有 77 个顶层测试，无参数化；AST 检查未发现字面 `assert True` 或直接 `x == x`。但存在以下有效性缺口：

- M121 新预置确实构造出 `grade_norm=0.752`、validator `rc=0`，不是不存在的场景；它只验证 foreign recovery，没有验证原事件白板第二轮能否落定。
- M122 只覆盖整数 `123`，没有覆盖 writer 可产的 `None/True/False`，也没有覆盖嵌套 JSON 的类型别名。
- HIGH④ 门只覆盖 `review/1` 后继，没有覆盖 §6.3 后继。
- B① 门只覆盖来源集合为空，没有覆盖“来源非空但 marker 与 bare 解释冲突”。
- N5 只覆盖 current+foreign，没有覆盖两条全 foreign。
- 规则 33 的门只做源码字面计数，未覆盖等价的手写候选选择。

未发现其他 round-13 门把“声称由正常入口产生”的前置状态构造成入口不可能产生的形态；剩余问题主要是覆盖少了一阶段或少了一类历史/损坏状态。

### 验证限制

- 复核绑定 HEAD 为 `ce6772f0d2c0098f39c05f92c4537fae64ee9128`，分支 `card/w7-ledger`；五个被复核文件相对该 commit 无 diff。
- checkout 原先已有一份 tracked UAT 文档修改和多份 untracked 审查产物；均未修改、清理或纳入结论。
- 隔离探针写在 `/private/tmp`，未触碰真实 vault。
- 按要求未运行 `backend/scripts/g32b_mutation_gates.py`，未设置 `DEBUG=true`。
- 未做真实断电/文件系统缓存故障注入；验证的是单进程状态机、字节产物和 fsync 调用结构。
- 未评并发锁，符合本卡明确排除范围。
- 当前环境没有暴露项目 AGENTS.md 所称的 Graphiti/Sequential Thinking MCP；因此未调用，全部结论来自现场源码、pytest 与隔离运行。
- 记忆仅用于遵循独立交叉核验及保护既有 dirty state 的流程偏好；所有结论均在本次 checkout 重新验证。

VERDICT: 需整改


