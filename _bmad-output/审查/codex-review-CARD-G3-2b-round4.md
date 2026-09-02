结论：需整改

### 19 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | FAIL | [SKILL.md:678](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:678)、[SKILL.md:713](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:713)：candidate 的 `effective_at/review_time` 直接复制 durable `_dup_rt`，不是真正独立构造。把日志内两处时刻同时从 `t1` 改成 `t9` 后，以原 `t1` payload 重跑仍 `rc=0`、`W=t9`、validator `rc=0`，且节点字节不同。违反 [规格:187](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:187)。 |
| 2 | FAIL | [SKILL.md:251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:251)、[SKILL.md:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:273)：先 `.strip()`，`effective_at` 还只做 `fromisoformat`。带首尾空格的两时刻被消费，settled `rc=0`；validator `rc=1`。这属于静默归一化。 |
| 3 | FAIL | [SKILL.md:690](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:690)、[SKILL.md:805](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:805)：笔记 `attempt_count=99`、pending 载荷为 `1` 时，恢复后仍为 `99`；再写本次评分后最终为 `100`，账本序数为 `[1,100]`。两次评分只增加一次，`max()` 确实掩盖了错误。 |
| 4 | FAIL（声明过强） | [SKILL.md:507](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:507)、[SKILL.md:859](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:859)：业务分数和 durable 时刻在相同环境下能锁定；但重试时改 `callout/question_id/self_confidence/source_board`，恢复仍 `rc=0`，节点 bytes 不等，正文出现新 callout。foreign replay 又明确把部分字段写 `null`，[规格:202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:202) 也承认无法逐字节恢复。 |
| 5 | PASS | [SKILL.md:635](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:635)、[fsrs_bridge.py:195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/scripts/fsrs_bridge.py:195)：形态门后，bridge 在 apply 前复算自洽性。`grade_norm=0,rating=4` 实跑 `rc=1`，未产生 `fsrs_*`/水位线；不是先应用后报错。 |
| 6 | PASS（仅文档事实） | A8/A9 确已写入 [规格:195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:195) 和 [规格:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:199)。但实现没有完整落实，见规则 11、13–16。 |
| 7 | PASS | [SKILL.md:371](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:371)、[测试:1491](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1491)：9 种尾部排列均命中生产块；无 LF 的最后非空坏行被容忍，坏行已有 LF 时 `rc!=0`。 |
| 8 | PASS | [SKILL.md:616](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:616)：非布尔 `true` 或 `review_time>W` 均拒绝；合法 `true` 且 `review_time≤W` 的补录行实跑放行且不推进该旧时刻。 |
| 9 | PARTIAL | [SKILL.md:360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:360)、[测试:1752](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1752)：字节切行、逐行 decode、半个 CJK 尾行容忍、BOM 剥除均工作。但 BOM 行被 writer 重放并 `rc=0`，validator 在 [validate_learning_events.py:1560](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/scripts/validate_learning_events.py:1560) 返回 `rc=1`；空白行也被 writer 跳过而 validator 判违规。 |
| 10 | PASS | [SKILL.md:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:291)、[测试:1331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1331)：重复 `grade_norm` 的行实跑 `rc!=0`，节点和账本写入面未变。 |
| 11 | FAIL | 守卫只统计 current dup 之前的 pending，[SKILL.md:697](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:697)。`current E1@t1` 在前、foreign `E2@t2` 在后时，首轮 `rc=1` 发布 `W=t2` 且 calibration 只有 E2；第二轮仍 `rc=1`，永久报 E1 “FSRS 已应用但缺校准记录”。 |
| 12 | PASS（六格本身） | [测试:1208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1208) 的六个前置三元组均真实，详见下节。但六格只算一个 collected test，未覆盖规则 11 的危险排列。 |
| 13 | FAIL | [SKILL.md:565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:565) 只对 dict 检查 `node_id`。账本首行改成 `[]` 后 writer `rc=0` 并追加新评分，validator `rc=1`；目标行保留 `node_id` 但删除整个 `payload` 也被静默跳过。违反 [规格:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:14)。 |
| 14 | FAIL | 普通 foreign 行确实逐项复放，但 [SKILL.md:788](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:788) 与两阶段发布组合有缺口：规则 11 的反例中 E1 的 FSRS 被发布、其 mastery/calibration 却因“本次事件”跳过，永久漏掉。 |
| 15 | FAIL | [SKILL.md:325](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:325) 没按 YAML 规则把单引号内 `''` 解成 `'`。合法 ID `O'Brien` 被 Obsidian 风格化为 `'O''Brien'` 后，degraded 事件再次重放，mastery `0.57→0.61`，calibration 同事件出现两条；账本 validator 仍 `rc=0`。 |
| 16 | FAIL（语义正确，判据实现不可靠） | [SKILL.md:753](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:753)：普通历史行、合法 `out_of_order` 补录、标准格式已应用行均未误伤；但上述合法 YAML 形态会产生“为假但实际已应用”。另一个已应用的 `quiz:x` 会让损坏的顶层 ID `x` 共享 calibration `x`，产生“为真但该事件未应用”。 |
| 17 | PARTIAL，且比规格严 | [SKILL.md:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:208)、[测试:1809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1809)：当前输入尾空格实跑 `rc!=0`、零写。但 [规格:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:40) 和 validator 只要求非空；`validate_record_full(" quiz:x ")` 无违规。foreign durable ID 也没有同款门。 |
| 18 | PASS | [SKILL.md:606](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:606)、[测试:1784](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1784)：错误 event type/concept/vault 均 `rc!=0`；合法 scored/abandoned 均 settled `rc=0`。 |
| 19 | PASS（字面规则）；规则清单不完整 | [SKILL.md:580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:580)：marker 存在但值非法会停。但 marker 整个删除、扩展键仍在时 writer `rc=0`，calibration 只有随后新事件；validator `rc=1`。这直接违反 [规格:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:91)。 |

### 六种状态

`L`=账本有本次 event，`F`=calibration 有本次 event，`A`=`W≥T`。

| 状态 | 实测前置 | 结果 | 判断 |
|---|---|---|---|
| 1 | `L=F, F=F`；另有一条 foreign pending | 首轮恢复 `rc=1`，次轮新写 `rc=0`；账本 `1→2`，最终 `W=2026-08-02T10:00:00Z` | PASS |
| 2 | `L=F, F=T` | `rc=0`，旧写序 orphan no-op；节点 hash 不变、账本仍 1 行 | PASS |
| 3 | `L=T, F=T, A=T` | `rc=0` 幂等 no-op；节点 hash 与账本行数均不变 | PASS |
| 4 | `L=T, F=F, A=T` | `rc=1`，命中“缺校准记录/人工核对”；零写 | PASS |
| 5 | `L=T, F=T, A=F`，`W=null` | `rc=0`，只补 `W/FSRS`；测试锁定的 mastery a/b/score、attempt 未变 | PASS |
| 6 | `L=T, F=F, A=F`，`W=null` | `rc=0`，恢复节点 bytes 等于正常路径 golden，validator `rc=0` | PASS |

六格确实调用从 Markdown 原样抽出的生产代码块，只重定向 `P`，依赖链接到真实 validator/bridge。未发现承担行为结论的恒真断言；但格 6 的 golden 来自同一 SUT 正常路径，只能证明两条路径一致，不能排除共同犯错。格 5 没检查 `last_examined` 和 calibration 不重不漏。

### 问题清单

[BLOCKER] [SKILL.md:697](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:697) — current dup 在前、foreign pending 在后时，两阶段发布永久不收敛并漏掉 current 的评分链副作用。  
依据: `E1(current)@t1,E2(foreign)@t2,W=null`；第一轮 `rc=1` 后 `W=t2`、attempt=2、calibration 仅 E2；第二轮仍 `rc=1`，固定报 E1 已有 FSRS 但无 calibration。  
建议: 在调用任何 bridge 前做全局 pending 预检。若规则 11 是最终裁决，`len(pending)>1` 一律零写停下；若要保留多 foreign 重放，至少禁止 current dup 与 foreign 在同一轮折叠/发布。同步修改 §6.2 与互相矛盾的测试。

[BLOCKER] [SKILL.md:325](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:325) — calibration presence 不是可靠的事件应用凭据，会同时产生假阳性和假阴性。  
依据: `O'Brien` 的合法 YAML 单引号表示导致假阴性，mastery `0.57→0.61`、同事件 calibration 两条；已应用 `quiz:x` 与被消费端错误放行的损坏顶层 ID `x` 又都映射成 calibration `x`，后者 mastery/calibration 被漏掉。  
建议: calibration 持久化并比较完整 ledger `event_id`，不要剥 `quiz:`；旧 bare 数据仅在唯一可逆时兼容，否则停下。frontmatter 使用真正的 YAML parser，至少完整实现 YAML 单引号解码；同时强制复习事件 ID 的 `quiz:` 构造规则。

[BLOCKER] [SKILL.md:580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:580) — 删除 `schema_ext` 即可把完整评分伪装成历史行并永久漏算。  
依据: 仅删除 marker、保留 rating/review_time/vault/concept 等字段；writer `rc=0` 并写新事件，最终 calibration 只有新事件，validator `rc=1` 报“含扩展键但缺 schema_ext”。  
建议: 复用 validator 的 `REVIEW_EXT_KEYS/_looks_like_review_ext`；本节点评分行只要出现任一扩展键却无 marker，必须在任何状态计算前零写停下。规格和 validator 已正确，只改实现与测试。

[BLOCKER] [SKILL.md:805](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:805) — `max(durable,current)` 把非法低序数伪装成“单调不减”，导致已考次数漏加一次。  
依据: 初始 99、pending 序数 1；两次评分完成后 frontmatter 仅 100，账本 `[1,100]`。  
建议: 按重放前边界逐项要求 `durable_attempt == current_attempt + 1`；不相等即不可证、fail-closed。不要以 `max()` 修复事实。

[HIGH] [SKILL.md:713](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:713) — candidate 时刻自抄 durable，且“任意参数下逐字节相同”无法成立。  
依据: 同时篡改 durable 两时刻后仍 `rc=0`；改变 callout/question/self-confidence 后恢复 bytes 不等。库版本或参数升级时恢复还会调用当前 bridge，而日志只保存 identity 字符串。  
建议: candidate 的事实值必须从持久化重试输入独立构造；把所有影响产物的字段及可重放 FSRS 输入/结果入账，或把规格承诺收窄为“相同 bridge 身份与相同非日志参数下，核心状态字段一致”。

[HIGH] [SKILL.md:565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:565) — 消费侧没有完整执行 v1 准入，合法 JSON 损坏行可被静默跳过或应用。  
依据: 顶层 `[]`、目标行缺 payload 均被跳过并允许新写；`event_version:true` 因 `True == 1` 被应用。三者 writer settled `rc=0`，validator 均 `rc=1`。  
建议: 任意非 object 行先停；目标 v1 行消费前复用 `validate_record_full`，再叠加 A8 在线侧更严规则；版本比较显式排除 bool。

[MEDIUM] [SKILL.md:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:273) — writer 与 validator 的词法接收集仍分叉。  
依据: 时刻首尾空白 writer `rc=0`/validator `rc=1`；BOM 与空白行 writer 放行/validator 拒；本次 event ID 尾空格 writer 拒而 validator 放行。  
建议: 时刻与 JSON 行禁止 `.strip()` 洗值；空白行、控制字符统一拒绝；BOM 是双方统一接受还是统一拒绝须写进规格。若保留 event ID 空白门，应同步更新规格和 validator。

[MEDIUM] [test_g3_2_review_ledger.py:1208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1208) — 测试覆盖未锁住本次最危险排列，且有陈旧注释/不可达 fixture 分支。  
依据: [测试:1351](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1351) 只测 foreign 在 current 前时停止；[测试:1446](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1446) 又要求两个 foreign 全重放；[测试:2099](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:2099) 声称 validator 放行 missing marker，但当前 validator 明确拒绝，且 `bad_marker=None` 分支没有任何参数命中。  
建议: 六格参数化并显式断言前置；新增 current-before-foreign、missing-marker、YAML apostrophe、attempt=99、非 object/缺 payload、时刻双篡改；零写断言比较完整 hash，格 5 比较除 FSRS 外的完整 frontmatter。

### 测试复核

按目标集合实跑：

```text
backend/tests/regression/test_g3_2_review_ledger.py
backend/tests/regression/test_learning_events_schema_contract.py
backend/tests/regression/test_fsrs_bridge.py
backend/tests/regression/test_learning_event_log.py
backend/tests/regression/test_decay_beta_convergence.py
```

结果：

- `268 collected`
- `267 passed`
- `1 skipped`
- `10 warnings`
- 用时 `45.90s`

与自报数字完全一致。单独行为测试文件结果为 `38 passed, 10 warnings in 37.68s`。

[learning_event_log.py:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/app/services/learning_event_log.py:61) 本批确实没改：当前无 diff，最后一次修改该文件的是 `02dbc426 feat(g3-2)`。本次 BLOCKER 都在 quiz consumer，且规格 [§6.2:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:188) 明确通用 `append_event()` 不应全局套 review envelope，因此不应为这些修复强行改它。若以后让它直接写 `review/1`，则必须另接同一严格 review 校验入口。

### 验证限制

- 审查锚点：branch `card/w7-ledger`，HEAD `860b88d89bbcc4163015ac50d4fb32a19d157632`。
- 工作树只读；临时 vault 位于 `/private/tmp/codex-card-w7-ledger.pI3Db3`。未修改源码，也未碰既有未跟踪审查文件。
- 仓库根不存在 `.venv/bin/pytest`，原样命令会 `rc=127`；改用实际存在的 `backend/.venv/bin/pytest`，其余环境变量和 pytest 参数不变。
- 未设置 `DEBUG=true`；未运行被禁止的 `g32b_mutation_gates.py`。
- 未模拟真实断电、磁盘控制器缓存故障或并发写；并发按题意不在结论范围。
- 没有实际安装另一版 py-fsrs/参数做跨版本恢复；相关“算法升级后字节不可复现”是代码路径证明。非日志参数变化导致 bytes 不等则已动态复现。

VERDICT: 需整改


