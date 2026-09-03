结论：需整改

### 33 条规则逐条判断（第 20/21/33 条已按本轮改动重写，见上）

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | FAIL | `SKILL.md:552-618,1851-1874` 的候选确实独立构造并排除两个环境键，但 canonical 有碰撞。实跑 `exam_board={"k":1}` 与 `{"k":"§dec:1"}`、以及 `10**30` 与 `10**30+1` 均被判相同，重跑 `rc=0`、节点及账本不变。 |
| 2 | PASS | `SKILL.md:358-385,768-779,1323-1325`。本节点行先过 validator，receipt `ts` 先做不带空白检查；因此 `_instant_only().strip()` 对日志/receipt 空白输入确实到不了。非 UTC durable 时刻被消费侧拒绝是规格 A5/A6 明定的有意加严。 |
| 3 | FAIL | `SKILL.md:1529-1573`。F1-only 用“`review_time ≤ receipt.ts` 的最大现存行号”猜缺失行的位置。实跑合法 §6.3 前驱存在时，把 receipt 的真实 `attempt_count=2` 推成期望 `0`，`rc=1`。 |
| 4 | PASS | `SKILL.md:2120-2157,2166-2218`；测试 `test_g3_2_review_ledger.py:1325-1334`。正常路径和崩溃恢复对日志锁定量逐字节一致。收窄后不再声称 `question_id/self_confidence` 一致，与规格 `docs:211` 相符，是诚实表述。 |
| 5 | PARTIAL | `SKILL.md:1391-1414` 与 validator `1417-1433` 对通常的缺失、类型、档位自洽能在 apply 前拒绝；但 `grade_norm=10**400` 会在 validator 的 `float()` 处抛未捕获 `OverflowError`，不是确定性 violation。 |
| 6 | FAIL | 实跑 `rg -n 'fsrs_applied\|adopted_actual' docs/learning-events-schema-v1.md` 为 0；`scored_at` 也未列入 §6.1 必填键。声称“上述裁决已回写 §6.2”不属实。 |
| 7 | PASS | `SKILL.md:901-953`。判据基于最后一个非空字节行是否有终止 LF；完整坏行后再有空白片段不会被伪装成截断。对应回归随 318 个通过项通过。 |
| 8 | PASS | `SKILL.md:1378-1390`。仅接受布尔 `true`，且强制 `review_time ≤ W`；validator 只管形态、消费者补语义门，属于规格登记的有意差异。 |
| 9 | FAIL（规则表述） | 实现并不“首行剥 BOM”：`SKILL.md:915-918` 在解码前直接拒绝 BOM；`924` 的 `utf-8-sig` 分支因而不可达。BOM 用例实际 writer/validator 都拒绝。应改规则清单文字，不应改代码去剥 BOM。 |
| 10 | PASS | `SKILL.md:402-408,940-947`。重复键由独立异常拒绝，不会落入“末行截断”容忍分支；对应回归通过。 |
| 11 | FAIL（规则表述） | `SKILL.md:1924-1955,2081-2090` 只在“本次 pending 与 foreign pending 混合”时停；纯 foreign 多条会依次复放。`test_g3_2_review_ledger.py:4658-4669` 两条同瞬间 pending 实际 `rc=0`。这与“多个 pending 一律停”不符。 |
| 12 | FAIL | 原六格测试本身通过，但新加的 receipt `fsrs_applied` 使格 3、格 5 又分裂出 missing/false/true 子态；测试没有覆盖这些子态，且其中已有反例，见下节。 |
| 13 | PASS | `docs:14-16,203-207`、`SKILL.md:1310-1325`。归属判断早于 payload 跳过，本节点缺可用 `node_id` 停；这是消费侧必要加严。 |
| 14 | PASS | `SKILL.md:2001-2042`。foreign replay 从日志逐项复放 mastery、last_examined、attempt、receipt；当前 dup 由恢复分支处理，不在此处重复吃 EMA。 |
| 15 | PARTIAL | 非歧义 ID 下，degraded 重跑的 mastery/attempt 实测保持不变；但 `_cands_and_sources` 仍可把别的历史 receipt 解释成本事件，因此“校准里有它”尚不是普遍可靠的应用凭据。 |
| 16 | PASS（局部门） | `SKILL.md:1453-1470` 确实在所有早退前扫描 `≤W`、未标乱序且无可验证 receipt 的 foreign 行并停止。其全局可靠性仍依赖规则 21/30 的 receipt 归属修复。 |
| 17 | PASS | `SKILL.md:211-227,962-977`。输入 ID 拒而不 strip，durable 空白 ID 只约束本节点；对应回归通过。 |
| 18 | PASS | `SKILL.md:1323-1414`。事件类型、concept/node、vault 关系均在 apply 前验证；与 validator 结论一致。 |
| 19 | PASS | `SKILL.md:1337-1367` 能阻止带合法/非法 review marker 的本节点行伪装成历史行；但新增的 `scored_at` 判据与当前规格分叉归入规则 20。 |
| 20 | FAIL | `SKILL.md:1323-1325` 的 validator-first 主链正确；8 处重复检查也不是缺陷，规格 `docs:201-202` 已明确承认这是纵深，应保留。但两处边界仍错：markerless `scored_at` 行被 writer 拒而 validator 放行；别节点非法非字符串 ID 又会经全账来源集合反向阻塞本节点。 |
| 21 | FAIL | `SKILL.md:449-512`。带 `id_form: full` 的 exact 分流正确，但无标记 exact token 仍可能同时是另一条多一层 `quiz:` ID 的历史裸 receipt；现独立碰撞判据只做 strip-once 同值，抓不到该关系。实跑发生错误幂等 no-op。 |
| 22 | PASS | `SKILL.md:258-285,2273-2284`。稳定时刻与 recorded_at 都按原字面 fullmatch，新记录追加前再过 validator；空白/非法日期/非有限数均零落账。 |
| 23 | PASS | `SKILL.md:2015-2034,2058-2064`。后续事件是否已经推进 mastery/attempt 取 receipt/calibration，而不是只看 W；degraded 的 EMA 防双吃实跑成立。 |
| 24 | FAIL | 有行时的日志序数与 gap 折算大体存在，但日志目标行丢失后，`SKILL.md:1529-1550` 无法从现存行号及时刻恢复其原 cursor；合法 §6.3 前驱反例失败。 |
| 25 | PASS | `SKILL.md:258-267,1850-1866`。candidate 的业务时刻来自本次输入的稳定 `review_time`，不是 durable 行或本轮当前时间；对应 A3 续跑门通过。 |
| 26 | PARTIAL | `SKILL.md:1553-1572` 的 `_gap_f1` 折算公式存在，证不出时会停；但它依赖错误的 `_base_line_f1`，因此整体证明仍不成立。 |
| 27 | PASS（字段分工） | `SKILL.md:2166-2244` 分开记录 recorded、adopted、scored 三种时刻，envelope 比原始稳定时刻；缺稳定值会停。`adopted_actual` 方案与 A6 的冲突另见规则 32。 |
| 28 | PASS | markerless 历史行不解释 `out_of_order`，receipt 由 PyYAML 解析，尾注释可接受；ID 空白门限定本节点。对应回归通过。 |
| 29 | PASS（主干） | `SKILL.md:954-980,1205-1269,2245-2284`：全文件字符串 ID 查重、新记录 validator 自检、receipt 结构化 YAML 预演均已实现。来源集合对非法 ID 的强转是规则 20/33 的独立缺陷。 |
| 30 | FAIL | receipt 字段数量齐全，但事实绑定可被 Decimal/string canonical 碰撞、无标记 ID 来源借错，以及 YAML 指数数值变字符串破坏；日志丢失时可错误 no-op 或自产自拒。 |
| 31 | FAIL | `_nkey` 的统一归属调用基本完成，但六事实“严格比较”共用的 `_num_norm` 本身不精确且有标签碰撞，因此统一了错误规则。 |
| 32 | FAIL | `SKILL.md:768-779` 有三方时刻绑定，F1-only 也检查 W 覆盖；但 `fsrs_applied` 没贯穿 dup/pending，false 成功复放后不升 true，且 `adopted_actual` 允许 durable 时刻与实际调度/W 分叉。 |
| 33 | PARTIAL | `_cands_and_sources` 确实只有一份实现，两个消费者的严格度也显式声明；但它仍把非法 foreign ID 强转为字符串，并漏掉无标记 exact 的双重来源解释。结构统一，语义未闭合。 |

### 六种状态

| 格 | 前置状态 | 结论 | 依据 |
|---|---|---|---|
| 1 | `dup=None, f1=False` | PASS | foreign pending 先恢复并独立发布，第二轮才追加本次事件；实跑最终 2 行、`W=2026-08-02T10:00:00Z`。 |
| 2 | `dup=None, f1=True` | FAIL | 普通旧写序孤儿用例能 no-op；但加入合法 §6.3 前驱后，F1 行号近似把 receipt 序数 2 算成 0，实际 `rc=1`，合法续跑不收敛。 |
| 3 | `dup=有, f1=True, W 已覆盖` | FAIL | 正常 `receipt.fsrs_applied=true` 子态通过；但 false 或缺键且日志仍在时仍从 `SKILL.md:1897-1901` 直接 `rc=0` 幂等跳过，没有 fail-closed。 |
| 4 | `dup=有, f1=False, W 已覆盖` | PASS | 实跑 `rc=1`，报“FSRS 已应用但缺校准记录”，节点与账本零写。 |
| 5 | `dup=有, f1=True, W 未覆盖` | FAIL | degraded 重跑会补 W 且不双吃 EMA，但 receipt 仍是 `fsrs_applied:false`；随后日志行丢失时固定 `rc=1`，并非“复放写 true”。 |
| 6 | `dup=有, f1=False, W 未覆盖` | PASS（普通事实） | 崩溃窗口全套恢复后与直接应用字节相同，receipt 写 true，validator 通过。不同事实被 Decimal canonical 撞成同一 envelope 的问题归规则 1/30。 |

六格的原始前置按旧三轴确实构造出来了，没有“无论实现怎样都成立”的恒真断言；问题是新增事件级凭据后，旧六格已不是完整状态空间。尤其 `test_g3_2_review_ledger.py:1309-1323` 只断言 W、EMA、attempt 和行数，从未断言 receipt 由 false 升为 true。

### 问题清单

[BLOCKER] [SKILL.md:1599-1614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1599) — `fsrs_applied` 只在 F1-only 分支生效，dup、pending 和 `≤W` 裁决仍能绕过事件级凭据，既可永久漏掉一次调度，也可重复推进一次。

依据: E1 先 degraded，receipt 为 false、无 W；删 E1 日志行；正常写 E2 把 W 推到 11:00；再把 E1 行恢复到 E2 前并重跑 E1。实际 `rc=0`、输出“已完整应用，幂等跳过”，E1 receipt 仍 false；损坏链为 `fsrs_state=1/due=11:10`，正常 E1→E2 对照为 `state=2/due=2026-08-03T11:00:00Z`。另把正常 receipt 的 `fsrs_applied` 键删掉但保留日志，重跑同样 `rc=0`，并非“旧 receipt 一律 fail-closed”。成功补 FSRS 后再删日志，则因 receipt 仍 false 固定 `rc=1`。

建议: 把事件级凭据纳入所有状态分支：`false + pending` 才允许 bridge，成功后在同一次 frontmatter 原子替换里把原条目结构化升级为 true；`true + pending` 属状态矛盾，必须停，不能再次 bridge；`missing/false + W 覆盖` 仍停；`true + W 覆盖` 才 no-op。旧 receipt 缺键的保守拒绝本身合理，但必须始终一致，并在规格写明迁移路径、false→true 生命周期和原子性。

[BLOCKER] [SKILL.md:552-618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:552) — `Decimal` 修法仍会把两份不同事实压成同一 canonical。

依据: 默认 `decimal` context 精度为 28，`Decimal(10**30).normalize()` 与 `Decimal(10**30+1).normalize()` 实际都得到 `1E+30`。端到端首次 `exam_board=10**30`、同 ID 改成 `10**30+1` 重跑，实际 `rc=0` 幂等跳过；`{"k":1}` 与用户字符串 `{"k":"§dec:1"}` 也因 `default="§dec:..."` 碰撞而 `rc=0`。两种比较点——逐字段 receipt 与整体 envelope——均复现。`1/1.0`、`-0.0/0`、bool/number 分型和 2^53 邻近整数抽样正确；但超过 28 位即失效。NaN/Inf 的新追加会 `rc=1` 且不落账，不过入口 `json.load` 仍接受它们，`nf:nan` 等普通字符串标签在比较域内仍可碰撞。

建议: 不要把内部类型标签序列化进用户字符串域；构造对所有 JSON 类型都打标签的内部树，例如 number/string/bool/null/array/object 各有独立节点类型。数值用 `Decimal.as_tuple()` 或不受 context 舍入影响的精确尾零规范化，显式统一 `1/1.0` 与正负零；P 文件也用 `parse_constant` 拒绝非标准常量。

[BLOCKER] [SKILL.md:449-512](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:449) — 无 `id_form` 的 exact receipt 仍有两种合法历史解释，可以借用另一事件的 receipt 并静默吞掉当前评分。

依据: 先写本地 ID `quiz:K`，完整日志 ID 为 `quiz:quiz:K`；把 receipt 变成受支持的 legacy token `quiz:K` 并去掉 `id_form`，删除旧日志行，再放入一条 validator 合法的新事件 `event_id=quiz:K`。重跑本地 `K` 时实际 `rc=0`、“已完整应用，幂等跳过”，新行未应用。现判据把 exact token 只解释成自身来源，漏掉它也可能是 `quiz:quiz:K` 的历史裸形态。

建议: 仅 `id_form: full` 才允许 exact-only。无标记 exact 必须同时枚举“自身完整 ID”和“另一个多一层 `quiz:` ID 的历史裸形态”；无法唯一证明时停下或先迁移 receipt。独立碰撞判据还应覆盖 `a == strip_once(b)` 的单向关系，而不只是两边 strip 后相等。

[HIGH] [SKILL.md:1529-1573](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1529) — F1-only 在目标日志行已经丢失后，不能靠 receipt 时刻与现存最大行号恢复目标的原写序。

依据: 节点先有 attempt 1，账本含一条 validator 合法的 §6.3 历史前驱 L；正常写 E 得 attempt 2；只删除 E 行后原样重跑。实际 `rc=1`，错误为 receipt `attempt_count=2` 与推导期望 `0` 不符，节点保持 attempt 2。另有同瞬间后继时，最大 `≤ts` 行号会把后写行吞进基线，真实 receipt 1 被推成期望 2。

建议: 新 receipt 持久化可验证的写序锚，例如 predecessor ID/账本前缀摘要，而不是事后按时刻猜 cursor。旧 receipt 若遇到无 `review_time` 历史行或等时行且没有锚，应明确报“顺序不可证明”，不能计算一个错误期望值。

[HIGH] [SKILL.md:322-335](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:322) — 选项③ `adopted_actual` 不符合当前规格 A3/A6，告警不能把 durable 调度时刻与实际 W 的分叉变成合法状态。

依据: 两条外部同瞬间行可通过单行 validator；复放第二条后 durable `review_time/effective_at/receipt.ts` 仍是 `10:00:00Z`，实际 bridge/W 为 `10:00:01Z`，仅 receipt 增加 `adopted_actual`。这直接违反 `docs:152` 的“三者同一瞬间”和 `docs:163-164` 的“写前推进再落账”。测试 `:4641-4673` 反而锁定了该分叉。另 `actual_ts != ts_str` 用字符串比较，`+00:00` 与 `Z` 同一瞬间也会误记 adopted_actual。

建议: 按当前规格收紧到 A3 唯一值不会误拒合法数据：外部在线写入方也必须在 append 前把第二行写成 `W+1s`，原始同瞬间保存在 `scored_at`；迟到数据走 out_of_order。若产品确要接受已经落盘的同瞬间序列，应先修改规格并设计账本内的可持久化 correction/applied-time 语义，让 proof、F1、排序统一使用它；只在可变 receipt 里记一个审计字段不够。

[HIGH] [SKILL.md:1188-1199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1188) — 任意类型的 `exam_board` 用 JSON 字面裸嵌 YAML，不是类型保真编码，能够自产自拒。

依据: 首次 `exam_board=1e300` 实际 `rc=0`，receipt 写成 `exam_board: 1e+300`；PyYAML 读回为字符串，完全相同输入立即重跑 `rc=1`，报 `exam_board '1e+300' != 期望 1e+300`。嵌套同类数值同样漂移。

建议: receipt 中把该值存成明确版本化的 canonical JSON 字符串并在读侧 `json.loads`，或用能保证 JSON 类型往返的结构化编码；预演必须执行“写出→YAML 读回→事实比较”闭环。

[HIGH] [SKILL.md:983-985](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:983) — 全账来源集合把别节点非法非字符串 `event_id` 强转为字符串，违反“别节点坏行不得阻塞本节点”。

依据: 先正常写本地 `event_id="1"`（完整 ID `quiz:1`），再追加别节点非法 `event_id: 1` 整数。validator 会拒该行；本节点原样重跑实际 `rc=1`，来源歧义被报成 `['1','quiz:1']`，节点和日志零写。

建议: `_EARLY_LEDGER_IDS` 与 `_ALL_LEDGER_IDS` 只登记 schema 定义的非空字符串 ID，与 validator `seen_ids` 的 `isinstance(str)` 口径一致；其他节点的非法 ID 留给离线校验器，不得参与本节点来源证明。

[MEDIUM] [SKILL.md:1355-1367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1355) — `scored_at` 消费门尚未写进真相规格和 validator，当前属于 writer 单边收紧。

依据: 构造无 marker、payload 仅含 `grade_norm/exam_board/attempt_count/scored_at` 的评分行，validator CLI 实际 `rc=0 RESULT: PASS`；writer 实际 `rc=1`、零写。当前 `docs:304-306` 仍称所有无 marker 历史评分行永久合法，validator `REVIEW_EXT_KEYS` 的 `1218-1230` 也不含 scored_at。

建议: 这个安全门有必要，不建议删除；应在规格把 `scored_at` 登记为 review/1 扩展键/必填事实，并在允许修改 validator 的卡中同步 `_looks_like_review_ext`。在两侧同步前，不能宣称规则 6/20 已完成。

[MEDIUM] [validate_learning_events.py:1417-1420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/scripts/validate_learning_events.py:1417) — validator 对超大整数先 `float()`，会以 traceback 中断而非按行报告 violation。

依据: 对 `grade_norm=10**400` 调 `validate_record_full`，实际退出 1 并抛 `OverflowError: int too large to convert to float`，栈落在 1419；`validate_file/main` 在记录校验阶段也未捕该异常。写点调用同一本体时同样零写但带 traceback。

建议: int 直接用整数范围比较；float 单独做 `math.isfinite()` 和区间检查。只在值已证明为 0/1 或有限 float 后才传给评分函数，或至少把 `OverflowError` 转成确定性 violation。

[MEDIUM] [learning-events-schema-v1.md:192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:192) — “排除算法环境键以支持合法库升级”的声明与先用当前单一 golden manifest 淘汰历史行相矛盾。

依据: 用旧行 `library_version=1.0/hash=a…`，把当前 manifest 参数设为 `2.0/hash=b…` 调 `validate_record_full`，实际得到两个真值不匹配 violation；消费侧 `SKILL.md:1323` 在 envelope 前就会停止，因此排除环境键并不能支持升级后的历史重放。

建议: 若合法升级是要求，validator 应按事件声明的版本匹配一个版本化、追加式的已知 manifest 集；否则删除“升级兼容”声明，明确当前契约禁止升级后消费旧行。

### 测试复核

按要求未设 `DEBUG=true`，使用隔离 TMPDIR 实跑：

```bash
env PYTHONDONTWRITEBYTECODE=1 INTERNAL_API_KEY=review-placeholder \
  NEO4J_ENABLED=false TMPDIR=/tmp/codex-g32-review-0ab79fbb \
  backend/.venv/bin/pytest \
  backend/tests/regression/test_learning_events_schema_contract.py \
  backend/tests/regression/test_fsrs_bridge.py \
  backend/tests/regression/test_learning_event_log.py \
  backend/tests/regression/test_g3_2_review_ledger.py \
  backend/tests/regression/test_fsrs_golden_vectors.py \
  -q -p no:cacheprovider --tb=short
```

实际结果：`exit 0`，`319 items`，**318 passed / 1 skipped / 10 warnings，95.09s**。因此卡文自报的 **317 passed / 1 skipped 不符，少报 1 个 passed**。

分文件计数：

- schema contract：194 passed / 1 skipped
- fsrs bridge：10 passed
- learning event log：6 passed
- G3-2 ledger：89 passed
- FSRS golden vectors：19 passed

唯一 skip 位于 `test_learning_events_schema_contract.py:1104-1108`，原因是 worktree 没有 live ledger。round-15 实际新增了 7 个测试函数（行 4453、4504、4537、4576、4590、4613、4641），不是 6 个，可能是自报少 1 的来源。

测试没有恒真断言，但有明确覆盖缺口：

- 数值门只测 `1/1.0` 与 bool，未测大于 28 位整数及 `§dec:` 标签碰撞。
- 事件级凭据门只测“日志已丢失的 F1-only”，未测日志恢复/仍存在时 false、missing、true 三态，也未断言成功复放后 false→true。
- 来源分流只测带 `id_form: full` 的 exact，未测无标记 exact 的双重解释。
- F1 序数只测部分后继，不测合法 §6.3 前驱和同瞬间后继。
- adopted 测试把当前规格不允许的 durable/actual 分叉锁成了预期行为。

### 验证限制

- 绑定对象已核验为 branch `card/w7-ledger`、HEAD `0ab79fbb1e3411f9f70ec6fdf776794e2a97a20d`。
- 工作树只读；所有构造数据均在 `/tmp/codex-g32-review-0ab79fbb` 或独立临时目录，未改任何 tracked 文件。原有未跟踪审查产物保持不动。
- 按用户要求未运行 `backend/scripts/g32b_mutation_gates.py`。
- 只跑了指定五文件，不代表整个仓库 CI；没有接触 live vault。
- 未做真实断电注入；崩溃窗口通过保留日志/回滚节点/删除或恢复单行模拟，并结合 `fsync/replace` 源码审查。
- 未测试并发；并发明确不在本次范围，也未把缺锁列为问题。

VERDICT: 需整改


