结论：需整改

### 33 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | FAIL | `SKILL.md:1362-1373` 的 candidate 确实独立构造，但把 `effective_at/review_time` 排除、改比未写入规格的 `scored_at`；规格 `learning-events-schema-v1.md:184-191` 仍要求 envelope 含 `effective_at`。无 receipt 的崩溃窗中篡改采用时刻后，validator `rc=0`、writer `rc=0`、W 被改到篡改值。 |
| 2 | PASS | `SKILL.md:308-335,992-994` 对 durable `review_time` 复用 `_WHOLE_SECOND_RE`，再要求 UTC 偏移为 0；完整测试组相关门均通过。此结论只指调度采用时刻，不把允许小数的 `recorded_at/scored_at` 混进来。 |
| 3 | 部分通过 | `SKILL.md:1233-1346,1481-1487` 的正常分支确实按账本边界和 calibration 分档，不用 `max()`；但 `:1108/:1253-1257` 把不核事实的 receipt presence 当“已应用”，污染反例最终账本 attempts=`[99,2]` 而节点 attempt=`2`，并未真正证明序数边界。 |
| 4 | PASS（限收窄范围） | `SKILL.md:1542-1587,1596-1667`。实跑 direct 与 crash-recovery 使用不同 `question_id/self_confidence`：账本、attempt=`1`、mastery=`0.57`、W 均相同；节点字节差异只在三个未入载荷的辅助字段。收窄表述诚实，不掩盖 exactly-once 缺陷。 |
| 5 | PASS | `SKILL.md:992-994,1049-1060` 在 apply 前先过 validator，再检查 rating/grade；追加前又在 `:1701-1703` 自检完整记录。293-test 组合全绿。 |
| 6 | FAIL | 绑定 commit 没修改规格；`rg scored_at\|receipt docs/learning-events-schema-v1.md` 为 0 命中。规则 25、27、30–32 所依赖的稳定时刻和 receipt 契约没有回写。 |
| 7 | PASS | `SKILL.md:603-630` 用最后一个非空字节行的索引判 LF。相关截断门通过；完整坏行带 LF 会拒，半个 UTF-8 末行且无 LF 才容忍。 |
| 8 | PASS | `SKILL.md:1036-1048` 只接受布尔 `true`，并要求 `review_time≤W`；非法形态或伪装成乱序的后继均 fail-closed。 |
| 9 | FAIL（规则文字错误） | 实现 `SKILL.md:617-620` 明确拒 BOM，validator `validate_learning_events.py:1560-1579` 也拒；并非“首行剥 BOM”。应改规则文字，当前实现方向正确。 |
| 10 | PASS | `SKILL.md:642-649` 使用 `object_pairs_hook` 拦重复键；validator 也用严格解析。相关测试通过。 |
| 11 | FAIL（规则文字过严） | `SKILL.md:1513-1539` 会顺序恢复多个 foreign pending、落盘后 `rc=1` 要求重跑；实跑第一轮 W 到第二条、attempt=`2`，第二轮写入当前事件后 attempts=`[1,2,3]`。只有 current dup 与 foreign 同处 pending 才在 `:1511-1512` 零写停下。 |
| 12 | 部分通过 | `test_g3_2_review_ledger.py:1255-1319` 六个 fixture 的前置均真实且全部通过；但 structured receipt 使 `L=0/F1=1/W未覆盖` 也成为可达第七态，现矩阵未覆盖。 |
| 13 | PASS | `SKILL.md:960-969` 在归属判断前拒不可用 `node_id`；符合规格 `:14-15` 的读方责任。validator 自身仍允许空串，但这是规格明确分给在线消费者的加严。 |
| 14 | PASS（合法事实前提下） | `SKILL.md:1405-1492` 对 foreign 逐项重放 FSRS、mastery、last_examined、calibration、attempt，并排除本次事件；多 foreign 实跑最终 attempts=`[1,2,3]`。receipt 污染判据缺口另见规则 31。 |
| 15 | FAIL | intended degraded 格通过，但“calibration 里有它”不是可靠事实证明：历史裸/full-ID 碰撞可令它为真而新事件未应用；空本地 eid 又会在 `:703` 令它为假而事件实际已应用。 |
| 16 | FAIL | `SKILL.md:1104-1109` 只查 receipt 布尔存在。篡改已过水位线的日志事实后，validator `rc=0`、writer `rc=0`，旧 receipt 被误认作该行已应用。 |
| 17 | FAIL（比规格严） | writer 在 `SKILL.md:216-217,664-679` 拒本节点首尾空白 ID；但规格 `:40` 和 validator `:1498-1500` 只要求非空。实质上是 writer 拒、validator 放的未冻结分叉。 |
| 18 | PASS | `SKILL.md:1004-1035,1190-1193` 对评分类型、concept/node、vault 和同键异主/异型均有门；相关窄门通过。 |
| 19 | PASS | `SKILL.md:1006-1026` 用 validator 同源 `_looks_like_review_ext`，有扩展痕迹但 marker 非法的本节点行不会被伪装成历史行跳过。 |
| 20 | PASS | `SKILL.md:951-1005` 先处理顶层/路由，`validate_record_full()` 在 `:992` 且早于 marker/out-of-order 分流。未发现 §6.3 合法历史行被这次 validator 调用误拒；别节点可归属的坏行不会阻塞。 |
| 21 | FAIL | 完整 ID 优先及非空来源歧义门已实现，但账本丢失时历史裸 receipt 没有 provenance。实跑旧 `quiz:quiz:K→裸 quiz:K` 后提交新完整 `quiz:K`，writer `rc=0`、账本 0 字节、attempt=`1`，新评分被吞。 |
| 22 | PASS | `SKILL.md:256-258,266-276` 对稳定业务时刻和本次 `ts` 都用 `_TS_RE.fullmatch`，拒而不 strip；追加前完整自检。 |
| 23 | FAIL | `SKILL.md:1243-1257` 确实不用 W，但改用的 calibration presence 仍可被 stale/alias receipt 伪造；因此“换了判据”成立，“判据可靠”不成立。 |
| 24 | PASS | `SKILL.md:1267-1323` 优先从后继日志自身的 attempt 回推；证明行不存在时会指名相关行并停止。现有窄门通过。 |
| 25 | 部分通过 | 实现 `SKILL.md:1208-1215,1347-1374` 正确从本次稳定输入构造候选，不抄 durable 或运行时 `ts`；A3 重跑测试通过。但该时刻尚未进入规格，所以契约闭环不成立。 |
| 26 | PASS | `SKILL.md:1293-1318` 对 proof 前的 gap 逐条折算；无后续证明边界则报不可证，不猜。 |
| 27 | FAIL | `SKILL.md:1061-1076,848-851,1361` 对旧行缺 `scored_at` 并非停下，而是回落到 adopted `review_time`。A3 场景实跑 foreign 恢复 `rc=1` 后原白板连续重跑均 `rc=1 envelope 冲突`，永久不收敛。 |
| 28 | 部分通过 | 历史无 marker 行的 `out_of_order` 不具语义、YAML 尾注释可解析均成立（`SKILL.md:526-575,1303-1309`）；“只拒本笔记空白 ID”也按代码实现，但仍受规则 17 的规格分叉影响。 |
| 29 | PASS | 全局重复 ID 门在 `SKILL.md:656-682`，同键异主/异型在 `:1190-1193`，YAML 解析在 `:539-550`，新记录完整自检在 `:1701-1703`；六格结束后 validator `rc=0`。 |
| 30 | FAIL | receipt 确实持久化多项事实（`SKILL.md:854-873`），F1-only 也比 ID/时刻/次数/分数；但历史裸 token 无法证明完整 ID，且漏比 canonical envelope 中的 `exam_board`。 |
| 31 | FAIL | 归属 NFC 统一和“不拿本次 ID 作来源证据”已实现；但 receipt 并非所有消费点都严格核六事实：dup `:1360` 不传 facts，foreign `:1450-1458` 不比 attempt，late/ordinal `:1108/:1253` 只查布尔。 |
| 32 | FAIL | 有 receipt 时三时刻绑定、F1-only 要求 W 覆盖、写回预演均成立（`SKILL.md:466-481,1165-1176,1668-1677`）；但崩溃窗无 receipt 时 resolver 直接返回，采用时刻又被 envelope 排除，篡改后仍 `rc=0` 恢复。 |
| 33 | 部分通过（安全性 FAIL） | `_cands_and_sources()` 在 `SKILL.md:381-408` 确实只有一份，两消费方共用且差异显式；但这个“有意差异”不安全。另 `:1459` 仍手写 exact-or-bare presence 前置，候选语义仍有第三站点。 |

### 六种状态

这里的 PASS 只表示测试构造确实处于它声称的状态，不表示整个状态空间已闭合。

1. **PASS — L=0、F1=0**  
   初始只有 foreign pending。本次第一阶段 `rc=1` 并恢复 foreign，第二阶段 `rc=0` 写当前事件；最终 ledger=2、calibration=2、attempt=`2`、W=`TS2`。

2. **PASS — L=0、F1=1、W 已覆盖**  
   当前事件日志行被删、receipt 与 W 保留。实跑 `rc=0`“旧写序”，节点 hash 不变，账本仍只有 foreign 行。

3. **PASS — L=1、F1=1、W 已覆盖**  
   完整成功后的原样重跑，实跑 `rc=0`“幂等跳过”，ledger 仍 1 行、节点字节不变。

4. **PASS — L=1、F1=0、W 已覆盖**  
   删除 calibration 后重跑，实跑 `rc≠0`“缺校准记录”，节点和账本零写。

5. **PASS — L=1、F1=1、W 未覆盖**  
   degraded 落账状态，实跑 `rc=0`，只补 FSRS；mastery/EMA/attempt 均未二次吸收。

6. **PASS — L=1、F1=0、W 未覆盖**  
   append 后、节点发布前崩溃，实跑 `rc=0` 全套恢复；相同辅助输入时与正常路径节点逐字节相同。

遗漏的是可达状态 **L=0、F1=1、W 未覆盖**：degraded 落账后日志又丢失。实现目前会正确拒绝，但六格测试没有覆盖，故规则 12 只能判“部分通过”。

### 问题清单

[BLOCKER] [SKILL.md:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:381)、[SKILL.md:508](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:508)、[SKILL.md:1129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1129) — 空来源下，历史裸 receipt 与新完整 ID 信息上不可区分，会静默漏掉新评分。  
依据: 先以本地 ID `quiz:K` 正常写出完整 ID `quiz:quiz:K`；把 receipt 改成受支持的历史裸 `quiz:K` 并清空日志；再提交不同本地 ID `K`，其完整 ID 为 `quiz:K`，其余事实相同。实测第二次 `rc=0`、“旧写序幂等跳过”，ledger=0 bytes、attempt=`1`。  
建议: 为 receipt 增加版本/provenance/full-ID 形态标记并迁移旧条目；未迁移且日志来源丢失时 fail-closed。仅增加更多评分事实无法解决两个世界字节完全相同的问题。

[BLOCKER] [SKILL.md:864](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:864)、[SKILL.md:1144](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1144) — F1-only 的“六项事实”遗漏 `exam_board`，同 ID 的不同 envelope 被吞。  
依据: `K#q1/board=A` 正常应用后清空日志；以相同 ID、稳定时刻、分数、abandoned，但 `board=B` 重跑。实测 `rc=0`、“receipt 事实一致”，ledger 仍 0 bytes、节点逐字节不变、receipt 仍为 A。保留日志的控制组会正确 `rc=1 envelope 冲突`。  
建议: 用同一个 envelope/facts builder 生成 dup、F1-only、foreign、late 的比较项；至少纳入 `exam_board`，并为每个固定生产键设独立窄门。

[BLOCKER] [SKILL.md:1104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1104) — 已过水位线扫描只看 receipt ID，不核事实，validator-valid 的日志污染可永久漏算一行。  
依据: 正常应用 E1=`.75@08-02`；把同一日志行改为自洽的 `.0/rating=1@08-01`，旧 receipt 保留 `.75@08-02`，validator `rc=0`；再写 E2。writer `rc=0`，最终 ledger grades=`[0.0,0.5]`、attempts=`[1,2]`，receipt grades=`[0.75,0.5]`，最终 validator 仍 `rc=0`。账本现在声称的 E1 从未应用。  
建议: `≤W` 全账扫描和 `_after_applied` 都必须调用统一 resolver，核完整 ID/provenance、scored/adopted time、attempt、grade、abandoned、board；不得以 presence 作为事实证明。

[HIGH] [SKILL.md:1360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1360)、[SKILL.md:1450](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1450) — “统一 resolver”只统一了函数，没有统一各调用点的事实清单。  
依据: 正常应用 `.75` 后，把 ledger 同 ID 行改成 validator-valid 的 `.0/rating=1`，再以 `.0` 重跑；实测 `rc=0`“幂等跳过”，ledger 为 `.0`、节点与 receipt 仍为 `.75`。另将 foreign receipt attempt 改成 `999` 后触发恢复，`rc=1` 但属于正常“恢复已落定”，坏值 999 被保留。  
建议: resolver 不应接受调用方随意传缺项 facts；改为由 row/current candidate 内部构建完整事实集，所有判断“已应用”的站点强制走同一入口。

[HIGH] [schema:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:184)、[SKILL.md:1362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1362) — 规格仍要求 envelope 含 `effective_at`，实现却排除了 adopted time。  
依据: 模拟 append 后崩溃、frontmatter 尚无 receipt；把 durable `effective_at/review_time` 从 08-01 同步改到 12-01，保留 `scored_at=08-01`。validator `rc=0`、writer `rc=0`，W 被恢复为 12-01。  
建议: 正确侧是补写规格，正式定义三个时刻和 receipt；同时实现无 receipt 崩溃窗的 adopted-time 证明。不能仅把实现退回“比较 effective_at”，否则 A3 合法续跑会误冲突。

[HIGH] [SKILL.md:848](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:848)、[SKILL.md:1061](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1061)、[SKILL.md:1350](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1350) — 合法旧行缺 `scored_at` 且发生过 A3 时，两阶段恢复永久不收敛。  
依据: 当前 writer 先生成原始时刻 10:00、采用时刻 10:00:01 的行，仅删除旧版不存在的 `scored_at`；validator `rc=0`。别板触发恢复 `rc=1`，receipt 错把 10:00:01 写成 scored_at；原板稳定输入仍为 10:00，此后连续重跑均 `rc=1 envelope 冲突`。  
建议: 消费前从白板保存的稳定输入可靠迁移，或明确 fail-closed 要求人工迁移；不得拿 adopted `review_time` 冒充原始评分时刻。

[HIGH] [SKILL.md:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:211)、[SKILL.md:703](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:703) — 空本地 eid 首次可写，但后续永远无法被 F1 识别。  
依据: `event_id=""` 首跑 `rc=0`，产生合法完整 ID `quiz:`、attempt=`1`、validator `rc=0`；同一输入第二跑 `rc=1`“FSRS 已应用但缺校准记录”，receipt 实际存在。  
建议: 要么入口在任何写入前明确拒空本地 eid，要么移除 `bool(eid)`，始终按完整 `evid` 查询；并新增首跑→重跑收敛门。

[MEDIUM] [SKILL.md:216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:216)、[validator:1498](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/scripts/validate_learning_events.py:1498) — 本节点 event_id 空白禁令未进入规格/validator，形成 writer 拒、validator 放。  
依据: 规格只要求非空；writer 对本节点带首尾空白的行 `rc=1`，validator 对同形态可 `rc=0`。  
建议: 若该安全策略保留，先同步升级 schema 与 validator；否则 writer 不应单边把冻结 v1 的合法字面判非法。

[MEDIUM] [test:3487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:3487)、[test:3559](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:3559) — 两个关键测试 oracle 没有证明声称的行为。  
依据: `:3563` 断言的是删日志前保存的 `n1==1`，实现即使重新追加/再 apply 也能通过；`:3492-3495` 对合法一空格 YAML 即使 writer 错误拒绝也接受。六格主体前置真实，但缺第七个可达状态。  
建议: 前者断言重跑后 `LED.read_bytes()==b""`、节点 hash/attempt 不变；后者必须断言 `rc=0`、ledger/calibration 都增加到 2；补 `L=0/F1=1/W未覆盖` 窄门。

[LOW] [schema:196](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:196) — 八处与 validator 重合的检查目前不是受理口径缺陷，但属于已产生实际分叉的维护风险。  
依据: 当前规格已经如实写成“同口径防御性复核及消费侧加严”，不是只称“更严”；相关坏数据两侧均拒，完整测试通过。此次真正的问题正是各调用点 facts 清单再次分叉。  
建议: 不必再改规格措辞；优先删除完全重复的手写层，只保留明确的消费侧加严，并把 receipt/envelope 事实构造集中为一个不可缺项的实现。

### 测试复核

实跑命令：

```bash
env PYTHONDONTWRITEBYTECODE=1 \
  INTERNAL_API_KEY=review-placeholder \
  NEO4J_ENABLED=false \
  TMPDIR=/tmp \
  backend/.venv/bin/pytest \
  backend/tests/regression/test_learning_events_schema_contract.py \
  backend/tests/regression/test_fsrs_bridge.py \
  backend/tests/regression/test_learning_event_log.py \
  backend/tests/regression/test_g3_2_review_ledger.py \
  backend/tests/regression/test_fsrs_golden_vectors.py \
  -q -p no:cacheprovider --tb=short
```

结果：`293 passed, 1 skipped, 10 warnings in 72.87s`。自报数字吻合；`test_g3_2_review_ledger.py` 为 64 tests。

对甲乙丙的直接结论：

- 甲：**不安全**。`_cands_and_sources()` 虽只剩一份，但空来源的 provenance 不可恢复，而且 F1-only facts 漏 `exam_board`；不存在所称的完整“六项事实兜底”。
- 乙：**“require_source=True 且来源为空不可达”成立**。两个默认严格调用点的 ID 都直接来自现存 ledger row，`_ALL_LEDGER_IDS` 必含它；空来源只发生在显式 `require_source=False` 的 F1-only。那行守卫确实不承重，但这不代表 B② 已安全修复。
- 丙：**等价变异体退役成立，但只能限定在 `SKILL.md:1460` 且前置 resolver 保留的程序点**。候选空时两者都假；候选存在且 resolver 返回时两者都真；歧义/坏事实会先抛出。不能推广成 resolver 与 compat 两个 API 在任意输入上等价。
- `_instant_only().strip()`：未发现可达洗白路径。ledger 时间先过 `validate_record_full()`；receipt `ts` 先过字面门；W 经 bridge 字段解析。带首尾空白的日志/receipt 时刻在到达这里前已拒。
- 正常/恢复逐字节相同的收窄：**诚实**。不同辅助输入只会改变未进入事件载荷的 receipt 辅助字段；评分、调度、序数副作用一致。
- 变异归因：按要求未运行 `g32b_mutation_gates.py`，所以不能独立证明“101 全 KILLED”及“17 条假杀→0”的运行数字；只静态核对了空变异对照设计与 M101 的局部等价性。

口径双向检查结果：

- writer 比 validator 严且已由规格明确授权：消费侧 UTC-only、attempt_count 正整数、本节点未知版本、未标记迟到行、out-of-order 语义门。
- writer 比 validator 严但未冻结：本节点 event_id 首尾空白禁令。
- writer 看似比 validator 松但规格明确授权：无 LF 的截断尾行容忍、可归属的别节点坏行不阻塞当前写入。
- 本节点 `review/1` 行因为先调用 validator，未发现新的“writer 放、validator 拒”路径；本轮 BLOCKER 恰恰都是 validator-valid 的事实一致性污染。

### 验证限制

- 绑定对象确认是 `d8dbb2e97e3650627d74a8241ea06d90c28b4362`、分支 `card/w7-ledger`。
- `git diff HEAD`、`git diff --check HEAD` 及五个指定文件的 diff 均为空；没有 tracked 源码污染。
- `fsrs_bridge.py` 工作树与 HEAD 的 SHA-256 均为 `80679678ebf56d53bcbf5f6b5b2b0dbc51e66ea7f8c66977ff2f8d8e7615b35d`，末尾只有一个正常 `if __name__ == "__main__": sys.exit(main())`；丁所述探针已清除。
- `git status` 仍有 **19 个 untracked** 审查产物，均在 `_bmad-output/审查/` 及其 `prompts/` 下。因此不能称工作树完全 pristine，但未发现它们进入生产代码；我没有删除用户已有文件。
- 隔离复现写在 `/tmp` 和 `/private/tmp`，未修改仓库；未设 `DEBUG=true`。
- 按要求未运行会临时修改实现的 mutation gate；未复核并发锁，因为本轮明确排除并发。

VERDICT: 需整改
