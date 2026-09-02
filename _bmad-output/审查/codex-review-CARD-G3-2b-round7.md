结论：需整改

### 24 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | FAIL | `SKILL.md:844-845,956-962` 从 durable 行取 `_dup_rt` 后复制进 candidate 的 `effective_at/review_time`，违反 `docs/learning-events-schema-v1.md:184-187` 的独立构造要求。实跑首次 `ts=2026-08-01`，回滚节点后同 ID 用 `2026-12-31` 重跑：`rc=0`、ledger 仍 1 行且业务时刻仍为 `2026-08-01`，恢复节点与首次成功产物逐字节相同；不同业务事实被当成重试。 |
| 2 | PASS | `SKILL.md:280-307,732-734`：先过完整校验，再要求 durable `review_time` 为 UTC 整秒。小数秒行实跑 `rc=1`；`+08:00` durable 行实跑 `rc=1`“非 UTC”，均未应用。 |
| 3 | FAIL | `SKILL.md:880-930` 同时存在 W 回退判据和错误的历史序数证明。合法链 `[attempt=1, 缺失, 3]` 经 validator `rc=0`，重跑 E1 却 `rc=1 envelope 冲突`；正确期望是 `3-2=1`，实现算成 `3-1=2`。 |
| 4 | PASS（限收窄范围） | `SKILL.md:1126-1172,1207-1218` 的恢复副作用使用 durable `review_time/grade/attempt`。崩溃回滚后恢复产物与正常产物 `byte_equal=True`。对 `question_id` 等未入载荷的辅助字段收窄是诚实的，不掩盖调度、掌握度、次数差异；但不抵消规则 1 的 candidate 缺陷。 |
| 5 | PASS | `SKILL.md:732-734,795-803`。缺 `rating`、以及 `rating=4/grade_norm=.75` 不自洽两例均 `rc=1`，且在应用前停止。 |
| 6 | PASS（文档面） | `docs/learning-events-schema-v1.md:184-217` 已写入 candidate、UTC、校准、迟到事件等裁决；其中规则 1、16、23、24 的实现未兑现。 |
| 7 | PASS | `SKILL.md:433-485` 按最后一个非空行判断 LF。坏 JSON 末行带 LF：`rc=1`；去掉 LF：`rc=0`，输出“截断尾行”并将新事件隔离成独立行。 |
| 8 | PASS | `SKILL.md:776-788` 只接受布尔 `true`，且要求时刻不晚于 W。新卡上伪造 `out_of_order=true` 的后继行实跑 `rc=1`。 |
| 9 | FAIL（规则文字错误） | `SKILL.md:447-456` 实际在解码前拒 BOM，并没有“首行剥 BOM”；writer 与 validator 实跑均 `rc=1`。实现方向与校验器一致，应把规则改成“BOM fail-closed”。 |
| 10 | PASS | `SKILL.md:309-330,472-473` 使用拒重复键的 loader。重复 `grade_norm` 实跑 `rc=1`，拒因明确含“重复键”。 |
| 11 | FAIL（规则应收窄） | `SKILL.md:1003-1124` 会批量重放多个纯 foreign pending，只在 current+foreign 混合时于 `1090-1097` 停止。两条 foreign 实跑第一轮 `rc=1` 但已恢复两行、W 到第二行；第二轮 `rc=0`，attempts 为 `[1,2,3]`。这符合规格 A9 和现有测试，却不符合“任何多个 pending 都停”的宽泛文字。 |
| 12 | PASS | `test_g3_2_review_ledger.py:1235-1296` 六格前置均真实构造；独立读取账本/frontmatter 后六格均符合声称状态，没有恒真断言。目标文件实跑 `44 passed`。 |
| 13 | FAIL（消费侧 PASS、生产侧 FAIL） | 消费侧 `SKILL.md:698-714` 会拒不可用 `node_id`；但当前事件在 `217,1224-1236` 构造前没有同款门。以节点 `节点/ .md` 实跑：首次 `rc=0`，写出 `node_id=' '`、`concept_id=' '`；回滚节点模拟崩溃后重跑 `rc=1`，ledger 1 行、节点无 W。validator 当前也错误地 `rc=0`，与规格 §一“可用路由信封”不一致。 |
| 14 | PARTIAL | `SKILL.md:1046-1076` 在正常 ID 情况下会复放 foreign 的 mastery、last_examined、calibration、attempt，并排除本次事件；两条 foreign 实跑均被复放。但规则 21 的 alias 假阳性可把未应用 foreign 判成 `_already_=True`，从而跳过这些副作用。 |
| 15 | PARTIAL | 真实 degraded 序列 `E1 normal → E2 degraded → retry E1` 实跑 `rc=0`、节点 SHA 不变，没有二吃 EMA，`SKILL.md:1045-1050,1137-1140` 正确；但规则 21 证明 calibration 判据存在“为真但其实是另一事件”的情况。 |
| 16 | FAIL | 检查在 `SKILL.md:996-1001`，却晚于 `968-972` 的幂等早退。E1/E2 正常应用后外部追加更早、未标乱序、无 calibration 的 LATE 行，validator `rc=0`；重跑 E2 时 writer `rc=0`“幂等跳过”，节点仍没有 LATE 校准。 |
| 17 | FAIL（比规格更严） | `SKILL.md:499-503` 全账本拒首尾空白 ID；但 `docs/...:40` 与 `validate_learning_events.py:1498-1500` 只要求非空，并冻结“字面即身份”。完整合法 review 行 `event_id=' quiz:legal-by-v1 '` 实跑 validator `rc=0 RESULT: PASS`、writer `rc=1`。 |
| 18 | PASS | `SKILL.md:732-775` 先用 validator 检查挂载事件类型，再检查 `concept_id/node_id/vault_id`。对应坏行均 `rc=1`；合法别节点非评分行不阻塞。 |
| 19 | PASS | `validate_learning_events.py:1526-1543` 与 `SKILL.md:746-766` 都拒非法 marker 或无 marker 却带 review 扩展键；合法纯 §6.3 历史行实跑 validator `rc=0`、同 ID writer `rc=0` no-op。 |
| 20 | PASS | `SKILL.md:698-734` 的归属判断与 `validate_record_full()` 顺序正确；合法非评分行在 `735-745` 跳过，合法历史行在 `746-766` 跳过。未发现因调用 validator 本体而误拒合法 §6.3 行。混合历史链的失败来自规则 24，不是规则 20。 |
| 21 | FAIL | `_fm_has_event_compat()` 在 `SKILL.md:367-381` exact-first，绕过 alias 歧义检查。首次提交本地 ID `quiz:K` 后，将其校准模拟成旧形态 `quiz:K`，再提交不同 ID `K`：第二次 `rc=0`，ledger 仍仅 `['quiz:quiz:K']`、attempt 仍 1、校准仍一条，新评分静默漏账。 |
| 22 | PASS | `SKILL.md:238-248` 使用 validator 的 `_TS_RE.fullmatch()` 且不 strip。空白、尾换行、畸形输入均 `rc=1` 且无 ledger；合法 `Z/+08:00` 输入产物通过 validator。 |
| 23 | FAIL | `SKILL.md:880-885` 仍是 `calibration OR review_time<=W`，并非规则声称的“只用 calibration”。删除 E2 校准但保留 `W=t2` 后重跑较早事件，代码仍把 E2 计作已贡献次数。 |
| 24 | FAIL | `SKILL.md:921-930` 跳过缺 count 的中间历史评分后，对更后面的证明行固定减 1。实跑合法链 E1(1)→L2(无 count)→L3(3)：validator `rc=0`、writer `rc=1`；把错误的 E1 次数改成 2 后反而 `rc=0`。 |

双向口径对照结果：本节点被消费的 v1 行没有发现“writer 放行、validator 拒绝”的漏网；别节点坏行被 writer 跳过是规则 20 的有意职责分工。相反方向发现规则 17：validator 放行而 writer 拒绝。另有 `node_id=' '` 是规格要求拒、但当前生产端和 validator 都放行的共同缺口。

### 六种状态

1. PASS — `(日志无本次事件, calibration=False)`：预置 foreign pending 后运行本次事件，第一轮只恢复、第二轮 `rc=0`；最终 ledger 2 行，W=`2026-08-02T10:00:00Z`，两条 calibration 都存在。
2. PASS — `(日志无本次事件, calibration=True)`：旧写序遗留；`rc=0` no-op，节点 SHA 不变，ledger 保持 1 行。
3. PASS — `(日志有, calibration=True, W≥事件时刻)`：`rc=0` 幂等跳过，节点 SHA 与 ledger 行数均不变。
4. PASS — `(日志有, calibration=False, W≥事件时刻)`：`rc=1`，报告“FSRS 已应用但缺校准”，节点与 ledger 零写。
5. PASS — `(日志有, calibration=True, W<事件时刻/无 W)`：degraded 恢复 `rc=0`，只补 FSRS；EMA、掌握度、次数四类字段不变。
6. PASS — `(日志有, calibration=False, W<事件时刻/无 W)`：崩溃窗口全套恢复 `rc=0`，与正常成功产物逐字节相同。

六格本身有效，但只覆盖当前事件的三元状态；没有覆盖 alias 碰撞、duplicate 早退前的跨行规则 16、以及多历史行序数回推。

### 问题清单

[BLOCKER] `SKILL.md:367-381,825-829` — 完整 ID 与历史裸 ID 的来源歧义仍能让不同评分静默漏账。  
依据: 首次提交 `event_id='quiz:K'` 得 ledger `quiz:quiz:K`、attempt=1；把 calibration 改成历史形态 `quiz:K`；再提交新 ID `K`。实际第二次 `rc=0`，stdout 称“已完整应用”，ledger/attempt/calibration 均未增加。  
建议: calibration token 必须反查所有可能来源：每个 ledger ID 同时贡献完整 token，带 `quiz:` 的再贡献历史裸 token；命中后的来源集合必须恰为当前完整 ID。即使 exact 命中也不得绕过歧义检查。

[BLOCKER] `SKILL.md:968-972,996-1001` — 幂等早退绕过全账本迟到未校准检查。  
依据: 正常写 E1/E2，再外部追加 `LATE@早于W`、无 `out_of_order`、无 calibration；validator `rc=0`。重跑 E2 得 `rc=0`，ledger 含 LATE，但节点始终无 LATE 校准。  
建议: 将规则 16 的全账扫描移动到所有 duplicate、历史行和 F1 早退之前。

[BLOCKER] `SKILL.md:844-845,956-962` — candidate 从 durable 行复制业务时刻，无法识别同 ID 承载了另一业务时刻。  
依据: 首次 `2026-08-01` 成功后回滚节点，同 ID 用 `2026-12-31` 重跑；实际 `rc=0`，只恢复旧事件，ledger 仍 1 行且时刻仍为 8 月。  
建议: 不要直接改成当前 `ts`，否则真实续跑也会冲突——Step 4a 每次都会重新取时间。应将首次评分的稳定 `review_time` 在 Step 3/检验白板持久化，另设新鲜 `recorded_at`；candidate 从本次 payload 中的稳定业务时刻独立构造。这不要求修改冻结 JSONL schema。

[HIGH] `SKILL.md:217,1224-1236` — 当前事件自身的不可用 `node_id` 可先落账，崩溃后无法自动恢复。  
依据: 节点路径 `节点/ .md` 首跑 `rc=0`，ledger 写出 `node_id=' '`；回滚节点后重跑 `rc=1`，ledger 仍 1 行、节点无 W。validator 对该行也错误返回 0。  
建议: 在调用 bridge 和追加前，对派生的 `node_id` 执行“非空且无首尾空白”门，并在 append 前对构造出的 `rec` 做完整自检；validator 的路由信封口径另卡修正。

[HIGH] `SKILL.md:904-930` — 历史序数证明跨过缺次数字段的评分行却只减 1。  
依据: E1(1)→合法历史 L2(无 count)→合法历史 L3(3)，validator `rc=0`；重跑 E1 得 `rc=1 envelope 冲突`。错误 E1=2 反而被接受。  
建议: 若证明行前共有 `k` 个会贡献 attempt 的评分行，应回推 `witness_count-k`；遇到无法证明是否贡献的间隙或 `out_of_order` 行则明确停止，不能固定 `n-1`。

[MEDIUM] `SKILL.md:880-885` — 规则 23 的 W fallback 修复没有真正落地。  
依据: 源码仍为 calibration 与 W 的逻辑或；删除后继事件校准但保留 W 后，后继仍被算作已贡献 attempt。  
建议: 删除 W 分支；先执行规则 16 扫描，再仅按无歧义的完整 calibration ID 计算 `_after_applied`。

[MEDIUM] `SKILL.md:945-953,1090-1097` — current+foreign 混合 pending 的恢复指引不可执行。  
依据: 重跑 current 得 `rc=1`“请先单独重跑其他白板”；改重跑 foreign 又得 `rc=1`“重跑任何白板都不会恢复”，两次均零写。现有两张检验白板无法按提示收敛。  
建议: 提供只恢复、不追加的 recovery-only 入口；否则明确要求人工恢复，不能提示“单独重跑那些白板”。

[MEDIUM] `SKILL.md:499-503` — 首尾空白 event ID 的全局拒绝未写入冻结规格，误拒合法存量。  
依据: `event_id=' quiz:legal-by-v1 '` 行 validator `rc=0`，writer `rc=1`。  
建议: 以当前真相源应删除消费侧全局拒绝；若产品决定禁止空白，先同步修改 schema、validator，并给既有行设计迁移，不应仅在 writer 单方面加严。

[LOW] `SKILL.md:1003-1124` — 规则 11 的文字比实际设计更宽。  
依据: 两个纯 foreign pending 第一轮均被应用并发布，第二轮正常收敛；现有测试 `test_g3_2_review_ledger.py:2007-2031` 明确锁定该行为。  
建议: 将规则收窄为“本次 duplicate 与 foreign pending 同处队列时停止”；若坚持任何多个都停，则需改实现、规格和现有测试。

[LOW] `SKILL.md:447-456` — 规则 9 把“拒 BOM”写成了“剥 BOM”。  
依据: writer/validator 均 `rc=1`。  
建议: 只改规则表述为“BOM 拒收”。

[LOW] `docs/learning-events-schema-v1.md:195-201` — “再叠加更严的”不能准确描述八处同口径重复检查。  
依据: `test_g3_2_review_ledger.py:2322-2327` 已承认单删重复手写门的变异会存活；当前两层对同一坏数据结论一致，没有产生受理差异。  
建议: 这不是当前 exactly-once 实现缺陷。既然有意保留纵深，建议把规格改为“先过校验器本体，再做同口径防御性复核及消费侧加严”，并继续做差分/变异门；无需为了措辞删除重复层。

`_instant_only().strip()` 当前确实到不了带首尾空白的时刻：唯一调用在 `SKILL.md:809`，此前 `732-734` 已执行 `validate_record_full()`；validator 在 `validate_learning_events.py:1375-1395,1516-1520` 按字面拒绝。它目前只是潜在漂移味道，不是穿透缺陷。

### 测试复核

实际五文件集合结果：

```text
collected 274 items
273 passed, 1 skipped, 10 warnings in 50.25s
exit 0
```

目标文件单跑：

```text
collected 44 items
44 passed, 10 warnings in 46.44s
exit 0
```

自报的 `274 collected / 273 passed / 1 skipped` 准确。唯一 skip 是 `test_learning_events_schema_contract.py:1104` 的仓内 live ledger 检查，当前 worktree 没有该账本。

测试鉴别力结论：

- 没发现行为门里的恒真断言；六格前置真实。
- `test_g3_2_review_ledger.py:274-285` 把改变 `ts` 称作“仅 recorded_at 变化”，但正常路径的 `ts` 同时决定业务时刻，实际锁定了规则 1 的偏离。
- 规则 16 现有测试只用新 E3 触发，没测 duplicate 早退。
- ID 测试没覆盖 `quiz:quiz:K` 的旧 alias 与 `quiz:K` 完整 ID 碰撞。
- 序数测试只覆盖一个紧邻历史行，没覆盖“缺 count 后又出现 witness”的链。
- `test_g3_2_review_ledger.py:2724` 的 validator 只读 JSONL，不能证明手工回拨后的节点是“真实 degraded 产物”；不过我另跑真实 degraded 序列，当前该分支确实 PASS。
- `test_g3_2_review_ledger.py:473-480` 声称正文“逐字节不变”却用 `read_text`；CRLF 反例运行后原始字节变为 LF，`raw_equal=False`，该测试仍通过。
- `test_g3_2_review_ledger.py:1716-1750` 使用固定 `/private/tmp` 路径，并对既存同名目录执行 `rm -rf`；应改用 pytest `tmp_path`。
- settled helper 每轮重写 payload，未直接证明 retained payload 原样续跑；独立使用同一 payload 文件重跑已确认当前实现第二轮 `rc=0`。

### 验证限制

- 工作树为只读；所有反例仅写入 `/tmp/card-w7-audit.jkPVqp` 或隔离的 `/private/tmp` 目录，未修改被复核文件。工作树原有未跟踪审查文件未触碰。
- 按要求未运行 `backend/scripts/g32b_mutation_gates.py`，未设 `DEBUG=true`。
- 44 项主要由 backend venv 的 `sys.executable` 执行；补跑系统 `python3` 基线成功，但没有用系统解释器重跑全部 44 项。
- 未做真实断电、文件系统缓存丢失或物理 fsync 耐久实验。
- 测试未执行检验白板 Step 4d，因此只能证明 Python 写点收敛，不能动态证明白板最终 `status: done`。
- 未测试并发；这是按题目与规格明确排除的范围。

VERDICT: 需整改
