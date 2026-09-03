结论：需整改

发现 **2 BLOCKER + 4 HIGH + 1 MEDIUM + 4 LOW**。现有 302 个通过测试没有覆盖这些反例。

### 33 条规则逐条判断（第 20/21/33 条已按本轮改动重写，见上）

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | PASS（信封本体） | `SKILL.md:1478-1491` 的 candidate 独立构造，durable 侧多/少业务键都会冲突，两个算法快照键排除。相关 B②/B③门在行为文件 73/73 中通过；身份闭合另见规则 21。 |
| 2 | PASS | `SKILL.md:317-344,1186-1192` 复用 `_WHOLE_SECOND_RE` 并额外要求 UTC；`validator:1375-1395` 负责基础时刻校验。现有整秒/偏移门均通过。 |
| 3 | FAIL | dup 分支 `SKILL.md:1328-1441` 能从日志边界回推；但 F1-only 在 `1238-1249` 直接拿当前 tip。实跑 E1=1、E2=2 后删 E1 日志，validator `rc=0`，重跑 E1 `rc=1`：`attempt_count 1 != 期望 2`。 |
| 4 | PARTIAL | canonical 输入下 `tests:1111-1134,1309-1319` 的正常/恢复字节对拍通过；但合法 `.731Z` 稳定时刻在崩溃后恢复 `rc=1`，因此不能对全部合法输入成立。收窄到“日志锁定量”这一表述本身诚实。 |
| 5 | PASS | `SKILL.md:1098-1100,1155-1166` 在应用前验证 rating/grade；`validator:1363-1433` 同口径。相关坏档位测试通过。 |
| 6 | FAIL | 判据确已写入 `schema:184-202`，但 `schema:190` 的无-receipt 证明本身错误；小数秒合法反例和已有 W 反例均已实跑。规格与实现都要改。 |
| 7 | PASS | `SKILL.md:699-725,746-751` 用最后一个非空字节行的位置判断 LF。截断末行与完整坏末行门均通过。 |
| 8 | PASS | `SKILL.md:1142-1154` 只收布尔 `true`，且要求时刻不晚于 W；validator 在 `1368-1373` 验形态。相关行为门通过。 |
| 9 | FAIL（规则文字） | 实际 `SKILL.md:713-716` 在 decode 前拒 BOM，`722` 的 `utf-8-sig` 不可达；validator 也拒。BOM 测试通过的是“拒绝”，不是“剥 BOM”。 |
| 10 | PASS | `SKILL.md:361-367,738-745` 的重复键解析器会直接停；行为测试通过。 |
| 11 | FAIL（规则文字） | 实现只在 current 与 foreign 同处 pending 时停，见 `SKILL.md:1636-1644`。实跑两条全-foreign pending：validator `rc=0`，writer 第一阶段 `rc=1`“恢复已落定”，节点 `attempt_count=2`。这符合 `schema:155-162,208-212` 的重放至空；应改规则 11，不应 blanket 改代码。 |
| 12 | PARTIAL | 六格和第七格的窄 fixture 都实际可达，定向 6 项测试全过；但格 1/2/3/5/6 均有未覆盖合法子状态，`closed` 的结论不成立。 |
| 13 | PASS | `SKILL.md:1066-1075` 在归属分流前拒不可用 node_id；本次自身 node_id 在 `237-243` 同样拒。相关门通过。 |
| 14 | PASS（核心路径） | `SKILL.md:1577-1624` 对 foreign 逐项复放 mastery、last_examined、calibration、attempt，并在 `1593` 排除本次事件。实跑两个 ordinary foreign 可恢复；事实构造的不收敛另见规则 31。 |
| 15 | FAIL（身份前提未闭合） | canonical degraded 路径 `1684-1687` 确实不重复吃 EMA；但规则 21 的 bare/full 错绑会让“校准里有它”对另一个事件为真。 |
| 16 | PARTIAL | ordinary `≤W + 未标乱序 + 无 receipt` 在 `1203-1220` 正确停；但 receipt 归属仍受规则 21 的错误别名影响，谓词尚非完备证明。 |
| 17 | PASS（有意分叉） | 输入与本节点日志分别在 `211-227,760-775` 拒空白 ID；validator 仍放行，`schema:40` 已明确登记为移交。 |
| 18 | PASS | `SKILL.md:1079-1141,1275-1288` 校验事件类型、NFC 概念归属、vault 归属及全局同键异主。行为门通过。 |
| 19 | PASS | `SKILL.md:1091-1132` 先完整校验，再处理 marker；带扩展键但 marker 非法不会当历史行跳过。 |
| 20 | PASS | 本节点 v1 行在 marker/type/OOO 分流前调用 `validate_record_full()`，见 `1091-1100`；新记录在 `1828-1839` 自检。实查 §6.3 合法无 marker 行先通过 validator、再于 `1112-1132` 跳过，没有合法历史误拒。 |
| 21 | FAIL | `SKILL.md:408-435,513-525` 没把 `id_form: full` 与实际命中的 exact candidate 绑定。实跑两个不同完整 ID 后，第二次 writer `rc=0`、账本仍 `b''`、attempt 仍 1。 |
| 22 | PASS | `_SCORED_AT` 与 `ts` 在 `258-285` 按 `_TS_RE.fullmatch` 字面校验；新记录保留原输入并在追加前自检。 |
| 23 | PASS | `SKILL.md:1338-1352,1587-1619` 用 receipt 判断后继次数是否已贡献，不再用 W 代替。round-7 序数门通过。 |
| 24 | PASS（dup 路径） | `SKILL.md:1362-1416` 优先利用后继日志行、receipt 与行序证明历史序数；无法证明会停并报明缺口。 |
| 25 | PASS | `SKILL.md:265-267,1478-1485,1723-1729` 的 candidate/首写都取稳定业务时刻，不抄日志，也不取重跑时刻。 |
| 26 | PASS | `SKILL.md:1362-1441` 对跨越的无序数历史行折算 gap；`tests:2890-2923` 真值 1 放行、错值 2 拒绝。 |
| 27 | PASS（字段分工） | `SKILL.md:1779-1799` 正确区分 recorded/adopted/scored；缺稳定时刻在 `258-267` 停。无 receipt 时如何证明 adopted 值仍失败，见规则 6/32。 |
| 28 | PASS | 无 marker 行不解释同名 OOO 键；YAML receipt 在 `622-650` 用 PyYAML；ID 空白只检查本节点。相关 YAML 尾注释门通过。 |
| 29 | PASS | 全局日志 ID 唯一性在 `752-778`；新记录自检在 `1833-1839`；校准读取/写回使用 YAML 解析器。 |
| 30 | FAIL | 五项评分事实确实比对，但“完整 ID”会被规则 21 错绑；F1-only 的历史序数又被当前 tip 错判。动态反例分别得到 `rc=0` 漏记和 `rc=1` 误拒。 |
| 31 | FAIL | 六处 `_nkey` 归属统一、候选未注入唯一性证据均正确；但 `_facts_of_row()` 在 `460-469` 擅自 round/stringify，合法值与 receipt 不同。`.752` 与数字 board 都已复现不收敛。 |
| 32 | PARTIAL | receipt 存在时的三方时刻绑定、日志丢失后的 W 覆盖、结构化写回和落账前预演都成立；但日志存在且无 receipt 的采用时刻仅检查空 W，见 `1459-1477`，未覆盖已有 W，空 W 时又用错字节相等。 |
| 33 | PASS（结构） | `_cands_and_sources()` 仅一份，两个消费者共用，严格度差异显式写在 `500-532,604-618`。不过唯一实现中的规则 21 bug 会同步影响两个消费者。 |

规则 20 没有过度收紧合法历史行。writer 拒而 validator 放的主要形态——不可路由 node_id、本节点未知版本、缺 attempt、非 UTC durable review_time、OOO 语义错误、`≤W` 无 receipt——均由 §一/A8 明示为消费侧加严或已登记移交。反方向只有别节点坏行隔离和无 LF 截断尾行容忍，是规格明确的作用域差异。没有发现新的、未解释的同节点 v1 `writer 放 / validator 拒` 漏网。

8 处重复校验不是当前实现缺陷。`schema:202` 已诚实改成“同口径防御性复核及消费侧加严”，建议保留现措辞；可为维护性抽共享 helper，但不应仅为了满足“更严”二字删掉纵深层。

`_instant_only().strip()` 的“到不了”成立：账本时刻此前已过 `validate_record_full()`，receipt `ts` 在调用前显式拒空白，W 又经 `fields_from_frontmatter()` 剥离 YAML 表达层空白。没有路径能靠这里洗白首尾空白日志时刻。

“正常与恢复逐字节相同”收窄到评分、调度、序数等日志锁定量，是诚实的；`question_id`、理解自评、callout 等未持久化辅助量不能承诺整节点字节相同，不构成评分漏算的掩盖。但合法小数稳定时刻当前根本不能恢复，仍需先修 BLOCKER。

### 六种状态

以下分别判断 fixture 是否真实，以及该格是否已被证明闭合。

| 状态 | 判断 | 依据 |
|---|---|---|
| 格1：L0/F0 | fixture PASS；闭包 FAIL | `tests:1255-1263` 确实先恢复 foreign，再重跑写当前事件，最终 `rc=0`、账本 2 行、W=`2026-08-02T10:00:00Z`。但同格换成 validator 合法的 `.752` foreign 后，第二阶段永久 `rc=1`。 |
| 格2：L0/F1/W覆盖 | fixture PASS；闭包 FAIL | `1265-1274` 删除的是当前 tip 行，receipt attempt 与当前 tip 都是 2，`rc=0` 且零写。若删除较早 E1、保留已应用 E2，实跑 E1 重试 `rc=1`，故该格未闭合。 |
| 格3：L1/F1/W覆盖 | fixture PASS；闭包 FAIL | canonical 行在 `1276-1283` 重跑 `rc=0`、节点与账本不变；但本写点自行产出的 `exam_board=123` 首跑 `rc=0`，紧接重跑 `rc=1`。 |
| 格4：L1/F0/W覆盖 | PASS | `1285-1291` 真正删除 calibration、保留 W；writer `rc!=0`，明确报缺校准且整面零写。该状态没有机械安全恢复依据，停下正确。 |
| 格5：L1/F1/W未覆盖 | fixture PASS；闭包 FAIL | `1293-1307` 通过真实 degraded 路径构造，恢复只补 FSRS，EMA/attempt 不变。非字符串 board 会在进入该恢复前被事实类型门误拒。 |
| 格6：L1/F0/W未覆盖 | fixture PASS；闭包 FAIL | `1309-1319` 的 canonical、W 空样本恢复成功并与正常路径字节相同；合法 `.731Z` 样本恢复 `rc=1`，已有 W 的篡改样本则错误地 `rc=0`。 |

第七状态 L0/F1/W未覆盖的布尔前置真实，`tests:3921-3941` 得到 `rc!=0` 且零写；不过 fixture 是正常应用后手工回退 W，不是注释所说的真实 degraded 产物。另用 `FSRS_BRIDGE_REEXEC` 构造真实 degraded 状态后，删除日志再跑同样得到 `rc=1`，所以可达性成立；测试仍应锁定具体“W 未覆盖”拒因。

六格的最终行为断言没有“无论实现怎么变都通过”的恒真项。`tests:2911` 在真值分支确实是有意的空操作前置，但最终行为由 `2920-2923` 约束；`n1 == 1` 也已明确降为前置检查。两处上轮 oracle 修法正确：

- 一空格合法 YAML 现在强制 `rc=0`、日志和校准都增长；
- 空来源幂等路径现在检查实际账本字节、attempt 和完整节点写面，不再靠旧的 `n1`。

### 问题清单

[BLOCKER] [SKILL.md:408](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:408) — `id_form: full` 被当成任意候选的通行证，两个不同完整 ID 会别名成同一次评分。  
依据: 首先提交本地 ID `K`，生成 receipt `quiz:K,id_form:full`；清空日志后提交不同本地 ID `quiz:K`，其完整 ID 是 `quiz:quiz:K`。实际 `rc=0`、日志仍为 0 字节、节点 SHA 和 `attempt_count=1` 不变，第二次评分零次入账。  
建议: 候选结果必须携带 `exact/bare` 形态；`id_form:full` 只能证明 `token == ev_id` 的 exact 命中，绝不能证明 bare fallback。无标记条目只允许在历史 bare 来源唯一时回落。无需把原始 event_id 粗暴塞回通用评分事实表。

[BLOCKER] [SKILL.md:1459](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1459) — “W 空 ⇒ adopted 与 scored 字节相等”的崩溃窗证明会误拒合法评分并永久不恢复。  
依据: 输入稳定时刻 `2026-08-01T10:00:00.731Z`，首跑 `rc=0`；日志为 `review_time=...00Z`、`scored_at=...00.731Z`，validator `rc=0`。恢复初始节点模拟 append 后崩溃，再跑得到 `rc=1`“采用时刻被改过”，节点保持未应用。合法 `+08:00` 输入同理。[fsrs_bridge.py:192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/scripts/fsrs_bridge.py:192) 会先 UTC 化并截整秒。  
建议: 从 `scored_at` 和崩溃前 W 复算唯一 adopted 值：先 UTC 化、截整秒；若结果 `≤W`，取 `W+1s`。比较复算结果与 durable `effective_at/review_time`，不要比较原字符串；同步修订 `schema:190`。

[HIGH] [SKILL.md:1469](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1469) — 已有 W 的无-receipt 崩溃窗完全跳过 adopted-time 证明。  
依据: E0 已应用后，E1 append，恢复节点至 E0；把 E1 的 effective/review 同步改到 `2026-12-01T10:00:00Z`。validator `rc=0`，重跑 writer `rc=0`，`fsrs_last_review` 实际恢复成 12 月。  
建议: 对所有“dup 存在、receipt 不存在、durable review_time>当前 W”的状态执行同一纯函数复算；现有 `W_inst is None` 条件应移除。规格也不能再把“无 receipt”推导成“W 必为空”。

[HIGH] [SKILL.md:460](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:460) — `_facts_of_row()` 舍入合法日志分数，但 receipt 保存原值，导致两阶段永久不收敛。  
依据: foreign 行 `grade_norm=0.752,rating=3`，validator `rc=0`；第一轮 `rc=1` 且恢复落定、receipt 写 `0.752`；第二轮 `rc=1`：`0.752 != 期望 0.75`，当前评分始终未追加。  
建议: row facts 必须保留 durable 原值；如果产品要强制两位小数，应同时修改 schema、validator 和所有生产者，不能只在消费比较侧 round。

[HIGH] [SKILL.md:457](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:457) — `exam_board` 的 `str()` 与 string-only receipt 门会拒绝 writer 自己产出的 validator-valid 状态。  
依据: 直接给生产入口 `exam_board=123`，首跑 `rc=0`，日志和 receipt 均保存整数 123；紧接相同输入重跑 `rc=1`：`receipt 的 exam_board 类型非法 (123)`。foreign 版本同样第一阶段恢复、第二阶段永久失败。  
建议: 按当前 schema 比较原始 JSON/YAML 值；若该字段必须是路径字符串，先同步冻结 schema 类型、validator 和入口门，再拒旧形态。

[HIGH] [SKILL.md:1238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1238) — F1-only 用当前 tip 校验历史 receipt 序数，合法非-tip 续跑被永久误拒。  
依据: E1/E2 正常完成，当前 attempt=2；只删除 E1 日志行，E1 receipt attempt=1 保留。validator `rc=0`，重跑 E1 `rc=1`、节点零写，报 `attempt_count 1 != 期望 2`。  
建议: 将 dup 分支的边界/后继证明推广到 F1-only：目标 receipt 序数加上可证明的后继贡献应等于当前 tip；存在无法证明的缺口再 fail-closed。

[MEDIUM] [test_g3_2_review_ledger.py:356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:356) — 关键测试只覆盖源码形状或窄代表值，无法证明六状态闭包。  
依据: “小数秒输入”只修改 `ts`，而 `_payload()` 在同 ID 续跑时把稳定 `review_time` 留为 TS1，因此根本没把 `.731Z` 送进 bridge；HIGH②门只测 W 空；facts-list 门 `3779-3798` 只数调用和源码字符串；provenance 门未测 `full marker + bare 命中`。这些测试全绿时，上述 2 BLOCKER + 4 HIGH 均可复现。  
建议: 增加四个生产入口门：fractional/offset 稳定时刻崩溃、已有 W 无 receipt 篡改、full marker 反向 bare 命中、E1 行丢失且 E2 已应用；另参数化 `.752` 和非字符串 board。

[LOW] [SKILL.md:1501](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1501) — HIGH③ 的新指引仍把“缺 receipt 后一定转到另一问题”说得过满。  
依据: E0 已建立 W，E1 经 A3 推到 `W+1s` 后模拟 append 崩溃并删 `scored_at`；首次 `rc=1` 且消息含“另一个问题”，补回 `scored_at` 后实际直接恢复 `rc=0`，没有转到缺校准指引。  
建议: 改为“若 W 已覆盖该事件且校准缺失，才会转到缺校准指引；若 W 未覆盖，补齐后可能直接恢复”。

[LOW] [SKILL.md:696](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:696) — 规则 9 和旧注释仍称首行剥 BOM，与实际双边拒绝相反。  
依据: `713-716` 实际提前 `rc=1`；validator 也拒，BOM 行为门全绿。  
建议: 规则 9 改为“BOM fail-closed”，删除旧剥 BOM 注释，并把不可达的 `utf-8-sig` 改成普通 `utf-8` 以免误导。

[LOW] [learning-events-schema-v1.md:155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:155) — 规则 11 的“多个 pending 一律停”与 A2/A9 及当前安全实现冲突。  
依据: 两条全-foreign pending 实跑可按序恢复，attempt=2；只有 current 与 foreign 混合时实现才拒。  
建议: 把规则 11 改为“本次事件与一个或多个 foreign 同处 pending 时停；全-foreign 且逐项可证时按 A2 重放至空”。

[LOW] [test_g3_2_review_ledger.py:3032](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:3032) — 测试仍把 foreign 空白 event_id 称为“现行规格合法”。  
依据: `schema:40` 本轮已全局禁止空白 ID；validator 当前 `rc=0` 只是已登记、尚未同步的移交缺口。  
建议: 保留“foreign 坏行不得阻塞本节点”的作用域测试，但把文字改成“已知 validator 缺口的别节点行”，不要继续称为合法。

### 测试复核

绑定 HEAD 已核为 `23851cb7b5b21bc6b37604eef5b8057d53cc2d36`，分支 `card/w7-ledger`。

按指定环境运行五个目标文件，因仓库根没有 `.venv`，使用实际存在的 `backend/.venv/bin/pytest`：

```text
302 passed, 1 skipped, 10 warnings in 83.41s
```

与卡文自报的 **302 passed / 1 skipped 完全一致**。

另行结果：

- `test_g3_2_review_ledger.py --collect-only`：73 tests collected。
- 行为文件完整运行：73 passed，10 warnings，78.16s。
- 六格、序数和第七状态等 6 项定向测试：6 passed，10 warnings，14.05s。
- 两处上轮 oracle 改写有效：合法一空格 YAML 现在必须成功并增长；空来源恢复现在验证真实节点/日志结果。
- 没有发现最终行为 oracle 恒真；但 facts-list 是源码形状门，第七状态只断言任意失败，小数秒门没有传小数稳定时刻，证明力仍不足。
- `test_round12_high2_adopted_time_in_crash_window` 的 A3 控制组已有 receipt，不是“已有 W 且无 receipt”的关键崩溃窗。

### 验证限制

- 工作区按只读复核；所有动态 fixture 只写入 `/private/tmp/codex-card-w7-ledger-r11-root` 和独立子目录。未修改任何仓库文件。
- 没有读取或修改现有未跟踪审查报告。
- 按要求没有运行 `g32b_mutation_gates.py`，因此不对变异侧 6 个重锚/3 个退役作独立运行背书。
- 崩溃用“保留 durable 日志、恢复节点到 append 前字节”精确构造，没有执行真实断电；对本状态机而言文件前置状态等价。
- 未测试并发，亦未将“没有并发锁”列为问题。
- 只运行了用户指定的五文件测试范围；没有声称全仓 CI 通过。
- 校验器、真实 PYEOF 入口和真实 FSRS bridge 均被调用；无网络、Neo4j 或 live vault 操作。

VERDICT: 需整改


