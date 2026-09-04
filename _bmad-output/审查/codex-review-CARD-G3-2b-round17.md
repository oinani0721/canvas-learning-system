结论：需整改

### 33 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| R01 绑定 commit 与唯一入口 | PASS | HEAD=`56bfe9d4316a126c8a713a09f5f5ef8d4078ef7b`；`SKILL.md:190-194` 为唯一含 `P = "/tmp/quiz-answer-payload.json"` 的 Python 块，匹配数 `1`。 |
| R02 JSONL 逐行严格解析 | PASS | `SKILL.md:940-959` 禁重复键、NaN/Infinity，并区分尾截断；相关门随全套测试 `329 passed / 1 skipped, rc=0`。 |
| R03 截断尾行与 LF 守卫 | PASS | `SKILL.md:2533-2539` 追加前检查末字节；带 LF 的损坏行 fail-closed，无 LF 尾截断隔离。 |
| R04 路由信封与未知版本 | PASS | `schema-v1.md:13-16`、消费门对应测试 `test_g3_2_review_ledger.py:2368-2444` 通过；本节点未知版本拒，别节点未知版本可跳过。 |
| R05 字符串 `event_id` 全文件唯一 | PASS | `SKILL.md:960-986`、validator `:1498-1500,1628-1637` 均只把非空字符串登记进唯一性集合。 |
| R06 非字符串 id 的登记面 | PASS | `SKILL.md:989-999,1549-1559`；预置别节点 `event_id: 1` 时 validator=`1`，本节点幂等重跑 writer=`0` 且零写。非字符串值使整行非法，不属于“有效 event_id 唯一性”量化域；不应强转后参与身份碰撞。 |
| R07 `review/1` marker 与挂载点 | PASS | `schema-v1.md:90-94`、`SKILL.md:1450-1468`；缺/坏 marker、错挂 event_type 的消费门通过。 |
| R08 vault/concept/node 身份绑定 | PASS | `schema-v1.md:95-102`、`SKILL.md:1470-1477`；当前节点错误绑定均在 apply 前拒绝。 |
| R09 rating/grade/abandoned 自洽 | PASS | `schema-v1.md:103-105`、`fsrs_bridge.py:195-218`、`SKILL.md:1491-1502`；显式 rating 非真 int、越界或与分数不符均拒。 |
| R10 算法身份与 degraded 哨兵 | PASS（有移交） | 具名版本由 validator manifest 门承担；成对 `degraded:*` 被两侧放行的缺口已经在 `schema-v1.md:217` 明确移交，没有继续冒充已覆盖。 |
| R11 时间语法、整秒、绝对瞬间比较 | PASS | `schema-v1.md:106,141-143,238`；offset 等价、尾空白、非整秒等门均通过。 |
| R12 bridge 的 UTC/A3/A7 | PASS | `fsrs_bridge.py:69-93,172-194,243-268`；真实桥测试通过，offset 转 UTC、naive 拒绝、`≤W` 推 `W+1s`。 |
| R13 水位线三态 | PASS | `schema-v1.md:114-139`；新卡/正常/残缺由共享 validator 分类，六字段非法组合相关门通过。 |
| R14 `out_of_order` 形态与语义 | PASS | `schema-v1.md:240-245`、`SKILL.md:1478-1490`；伪装成乱序的真实后继会在消费前拒绝。 |
| R15 A1 write-ahead | PASS | `SKILL.md:2491-2570`；事件 append+fsync 在 calibration/frontmatter 发布前。 |
| R16 追加完整性 | PASS | `SKILL.md:2556-2569` 单次 `os.write`、校验返回字节数、文件及首次创建父目录 fsync。 |
| R17 frontmatter 原子发布 | PASS | 恢复路径 `SKILL.md:2422-2433`、正常路径 `:2581+` 均为 temp→fsync→replace→父目录 fsync。 |
| R18 A2 pending 准入和顺序 | FAIL | 标量门通过，但 512 层合法 `exam_board` 行 validator=`0`，崩溃窗恢复 writer=`1 RecursionError`、`W=None`、ledger=`1`；A2 无法消费合法 pending。 |
| R19 A3 唯一采用值及本轮反转 | PASS | `SKILL.md:322-343` 现在只接受 `_adopted_from(scored_at, rolling_W)`；同瞬间两行 validator=`0`、writer=`1`，第二行改成 `W+1s` 后 writer=`0`。符合 `schema-v1.md:155-162,188-189`。 |
| R20 rolling baseline 取实际 W | PARTIAL | 合法生产形态下原实现/退役变异实测均 `rc=1, zero-write=true`；但有 receipt 的 foreign pending 会跳过 `SKILL.md:2188-2204` 哨兵及 `:2283-2294` 校准哨兵，M141 只能证明“生产可达域等价”。 |
| R21 A9 两阶段必须收敛 | FAIL | E1 degraded→E2 第一阶段恢复：`rc=1`；E1 的 receipt 仍 `fsrs_applied:false`。E2 第二轮=`0` 后，E1 原样重跑=`1`，两阶段未使原白板落定。 |
| R22 duplicate canonical envelope | PASS | `schema-v1.md:209-223`；事件类型、节点、scored_at、payload 键集和值的比较门通过；身份环境键排除范围已按规格收窄。 |
| R23 “完整应用”早退只能凭严格证据 | FAIL | `SKILL.md:1878-1910,2149-2153` 把 YAML 字符串 `"false"` 经 `bool()` 变成真；实测 writer=`0` 并删除 payload，但 `W=None`。 |
| R24 receipt `id_form` 与历史两种解释 | PASS | 候选解释阶段枚举未标记 exact 的 full/bare 两来源；对应门及 M148 通过，没有再借他人 receipt 吞分。 |
| R25 `fsrs_applied` 全分支生命周期 | FAIL | 当前 dup 的普通布尔 false 可升 true；foreign false 不升，非布尔值不拒，foreign receipt 也只按“是否存在”分流。 |
| R26 F1-only/旧写序孤儿 | PARTIAL | 普通字符串 receipt 可 `rc=0` 零写；合法旧 `exam_board: 1e+300` 形态重跑=`1`，深嵌套 receipt 也会栈溢出。 |
| R27 类型保真 canonical tree | FAIL | 普通 `1/1.0`、bool/int、超大整数及内部标签碰撞门通过；但 `SKILL.md:578-619` 无界递归，500/512 层开始出现首写=`0`、重跑=`1`。 |
| R28 attempt ordinal | FAIL | 一条合法 §6.3 后继同时缺 `review_time`/`attempt_count` 时，篡改 A receipt 的 `attempt_count:1→2` 和 `pred_id→后继`，validator=`0`、writer=`0` 错误 no-op。 |
| R29 `pred_id` 失联时回退 | PASS（声明需改） | 指向别节点、自身、不存在 id 均命中 `0` 条后回到带歧义证明的 cursor；无歧义样本均 writer=`0` 零写，非法类型=`1`。所以实现是“优先证据+安全回退”，不是送审声明的“四类各自 fail-closed”。 |
| R30 `pred_id` 方向自洽 | FAIL | `SKILL.md:1693-1715` 在时刻和序数两种方向证据都缺时仍 `_anchor_ok_f1=True`；§6.3 后继旁路实测成立。 |
| R31 正常与恢复取得同一 `pred_id` | PASS（测试不足） | append-only、唯一 id 前提下，正常路径取当前末行，恢复路径按目标行切开取同一末前驱。额外实测 A→B：`byte_equal=true`、`pred_A_count=1`、ledger=`2`；现有字节一致性门只直接覆盖 `pred_id:null`。 |
| R32 `exam_board` 类型双编码与 legacy | PARTIAL | 新格式的空串/null/bool/`1e300`/3001 位整数/对象/数组均首写、即时重跑、validator=`0`；但无 `board_form` 的旧裸指数浮点 receipt 重跑=`1`。 |
| R33 `exam_board` 字符与深度闭环 | FAIL | U+0085 在追加第二条 receipt 后从码点 `133` 变 `32`；U+007F/U+0080/U+0090/U+009F 使下一评分持续 `rc=1`；512 层崩溃恢复=`1 RecursionError`。 |

### 六种状态

| 状态 | 结论 | 依据 |
|---|---|---|
| 1. `dup=无, F1=假` | FAIL | 基准标量路径会先恢复再重跑；但 foreign degraded 恢复没有升 true：第一阶段 `rc=1`，第二阶段本次事件 `rc=0`，原事件再跑仍 `rc=1`，不收敛。 |
| 2. `dup=无, F1=真` | FAIL | target 日志行丢失后，以合法 §6.3 后继作为无方向证据的假锚，writer=`0` 错误认定旧写序孤儿完整、零写。 |
| 3. `dup=有, F1=真, applied=true` | FAIL | 普通值可幂等 no-op；500/512 层自产 receipt 重跑却 `rc=1 RecursionError`，不能完成同事件幂等确认。 |
| 4. `dup=有, F1=假, applied=true` | PASS | 实测非零退出、“FSRS 已应用但缺校准记录”，节点与账本零写；没有猜补 receipt 或二次 apply。 |
| 5. `dup=有, F1=真, applied=false` | FAIL | 普通自产格式可恢复；把同一合法 YAML receipt 重排后，FSRS 恢复 `rc=0`，但正则未把 false 升 true，下一次重跑=`1`。 |
| 6. `dup=有, F1=假, applied=false` | FAIL | 普通崩溃窗恢复与正常路径字节相同；512 层合法行则 ledger=`1`、`W=None`、恢复持续 `rc=1`，一次评分永久未 apply。 |

### 问题清单

[BLOCKER] [SKILL.md:1878](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1878) — 非布尔 `fsrs_applied` 会被 truthiness 当作“已应用”，静默漏掉一次 FSRS。

依据: 先强制 bridge 降级写 E1，得到 `rc=0`、ledger=`1`、receipt 为布尔 false、`W=None`；把它改成合法 YAML 字符串 `fsrs_applied: "false"` 后原样重跑。实际 `rc=0`，stdout 含“已完整应用，幂等跳过”，节点 SHA 未变，`W=None`，ledger 仍 `1`，payload 被删除。根因是 `bool(_rc_dup_applied)`。

建议: receipt 存在时统一执行 `type(v) is bool`；不能写 `v in (True, False)`，因为 `1 == True`。缺失或任何非 bool 一律 fail-closed，并补 `"false"`、`"true"`、`0`、`1` 门。

[BLOCKER] [SKILL.md:1332](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1332) — 新 `q_` 只保护新条目，重建旧 receipt 时重新破坏字符，可在日志行丢失后把同一次评分再算一遍。

依据: A 的 `event_id`/板名含 U+0085，A 首写=`0`；普通 B 首写=`0`。第二次追加后，A receipt 的字符从 U+0085 变为空格。删除 A 的账本行并原样重跑 A，实际 writer=`0`，`attempt_count` 从 `2→3`，最终 ledger IDs 为 `["quiz:B#q1","quiz:A\u0085X#q1"]`：A 已经在 frontmatter 生效过，却再次被当成新评分。根因是 `:1337` 仍用 `json.dumps(... ensure_ascii=False)`，且 `:1343-1347` 只验列表类型和长度。

建议: 重建已有条目时所有键和值都走同一个验证式 YAML emitter；发布前类型敏感地比较 `_reparsed["calibration_log"][:-1]` 与原 `_cur` 全部内容。增加 “A hostile→B→重跑 A” 以及“再删 A 日志行重跑”的门。

[BLOCKER] [SKILL.md:578](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:578) — 合法深层 JSON 首写成功，write-ahead 崩溃后却永远无法恢复。

依据: `exam_board` 为 512 层数组时首写=`0`、validator=`0`。保留已追加行、把节点恢复成 append 前版本以模拟精确崩溃窗，重跑=`1`，未捕获 `RecursionError`，`W=None`、ledger=`1`。32–384 层为 `0/0`；512、640、768 层均为首写 `0`、重跑 `1`。这满足题目给出的单进程“日志有一次、文件零次且重跑无法补”的 BLOCKER 定义。该递归器不是本 commit 新增，但本轮点名的双编码合法值域仍被它打穿。

建议: 把 `_canon_tree` 改为显式栈的迭代实现。若产品要设深度上限，必须先在规格、validator 和首次 append 前冻结同一上限，不能首写后才拒。

[HIGH] [SKILL.md:2277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2277) — foreign degraded 恢复不提升事件级凭据，两阶段不能使原白板收敛。

依据: E1 degraded 首写=`0`；提交 E2 的第一阶段恢复 E1=`1` 并输出“恢复已落定”，节点 W 已到 E1 时刻，但 E1 receipt 仍为 false。E2 第二轮=`0`、W 到 E2 时刻；再跑 E1=`1`，报 `false + W 已覆盖`。提升代码只在当前 dup 的 `:2381-2403`，foreign 路径 `:2283-2294` 因 `_already_` 为真既不重写 receipt，也不检查提升成功。

建议: 对每个 foreign receipt 先解析严格状态：无 receipt=崩溃窗全套恢复；bool false=仅补 FSRS并在同次原子发布中升 true；true 但仍 pending=矛盾拒绝；缺键/非法类型=拒绝。用结构化唯一条目更新并断言恰好修改一项，避免原始文本正则。

[MEDIUM] [SKILL.md:1663](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1663) — `pred_id` 命中但方向不可证明时仍被信任。

依据: 正常自产 A/B/C，删 A 日志；把 B 变为 validator=`0` 的 §6.3 行并删除 `review_time`/`attempt_count`；把 A receipt 的 pred 改指后继 B、attempt `1→2`。A 重跑实际 writer=`0`、零写并声称完整。恢复正确 pred/去掉 pred 后同态 writer=`1`、推导期望为 `1`。别节点/自身/不存在 id 在无歧义样本中均安全回退并 `rc=0`，只有非法类型=`1`，所以“四类各自 fail-closed”声明也不准确。

建议: 只有得到肯定的时间或严格 ordinal 证据后才能设置 `_anchor_ok_f1=True`；两者都没有时按锚不可用走歧义回退。`pred_id:null` 也应证明本次确为该节点首事件。

[MEDIUM] [SKILL.md:450](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:450) — 无 `board_form` 的旧 receipt 兼容门只覆盖字符串，旧写点可产的指数浮点被误拒。

依据: 当前 `exam_board=1e300` 首写/重跑/validator 均=`0`；把 receipt 恢复为旧版本真实形态——删除 `board_form`，写裸 `exam_board: 1e+300`——账本不变且 validator=`0`，同一评分重跑=`1`，错误为 `exam_board '1e+300' != 期望 1e+300`。现有 legacy 门 `test:5090-5114` 只用普通字符串。

建议: 为 markerless receipt 定义并实现与旧写点词法一致的迁移解析；若存在 YAML/JSON 不可判歧义，应显式迁移并 fail-closed，而不是宣称整个旧值域兼容。

[MEDIUM] [g32b_mutation_gates.py:727](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/scripts/g32b_mutation_gates.py:727) — `138/138` 中有两条语法错误假杀，另有一条不忠实历史变异。

依据: 对 138 个变异结果做 AST 编译，实际 `syntax_invalid=2`：M64 在抽取程序第 2363 行报 `"'(' was never closed"`；M87 在第 928 行报 `invalid syntax`。把 M87 改成语法有效的“只删 null/~ 分支”后，绑定门实际 `rc=0 SURVIVED`。M151 `:1613-1620` 只把 marker 改成 `legacy`，却保留新式双编码，产生没有任何正式版本写过的混合 receipt。

建议: 每个 mutant 运行测试前先 AST 编译；语法错误应判 harness failure，不得计 KILLED。修正 M64；M87 退役或重绑实际结构化路径；M151 应同时恢复旧裸值编码并移除 marker，或拆成两个忠实变异。

[MEDIUM] [g32b_mutation_gates.py:1468](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/scripts/g32b_mutation_gates.py:1468) — M141 只能证明“生产可达域等价”，不能无条件称等价变异。

依据: 新说明正确推翻了旧的“所有路径必经哨兵”伪证，但逐路径复核结果是：无 receipt 的 foreign 行会在 bridge 前经过 `_adopted_ok`；有 receipt 的 foreign 行会跳过该门，且 `_already_` 使 `_append_calibration` 也不执行；当前 true dup 在 A2 前早退，合法 false dup 两值相等；current+foreign 混合虽执行内存计算，但 `:2340-2341` 在发布前拒绝。因此合法自产状态上两支等价，损坏的 receipt-bearing pending 上并不等价。题目明确包含“被别的程序写坏”的输入域。

建议: 改名为“schema-valid producer-domain equivalent”，并保留 corrupt-ledger fail-closed 门；等严格 receipt 状态门补齐后，再证明损坏态也不可达或不可观察。

[LOW] [test_g3_2_review_ledger.py:1235](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1235) — 仍有同类全文短语碰撞门。

依据: 本轮 M7 收紧到 `**golden manifest 绑定门**承担` 足够：完整短语计数=`1`，原短语计数=`2`。但 `:1235` 在全文分别查“可容忍的截断 vs 完整损坏”和“不以 LF 结尾”；后者在 schema `:208`、`:320` 各出现一次。删掉 `:208` 真正 LF 条款里的后半短语，仍可由 proof 条款喂饱。

建议: 像 A8 门一样先截取 A4.5/LF 段，再检查完整句或结构化条款，不要跨全文拼两个独立 substring。

[LOW] [SKILL.md:322](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:322) — H④ 行为已正确反转，但旧选项③注释仍与代码和规格相反。

依据: 执行代码 `:343` 只认 A3 唯一值，`adopted_actual` 字段已删除；但 `:325-330` 仍说“两值都合法”，`:2214-2241`、`:2287-2294` 仍说选③并记录 `adopted_actual`。实际门为 validator=`0`/writer=`1` 拒同瞬间违规，修正后 writer=`0`。

建议: 删除旧决策叙述或明确标成已废弃历史，避免后续维护者按注释重新引入违规分支。

[LOW] [SKILL.md:2552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2552) — 孤立代理与超大整数存在写入端更严的容量分叉，且代理错误被误报成 NaN。

依据: 合法代理对 `\ud83d\ude00` 解为 emoji，writer/retry/validator=`0`；孤立 `\ud800` writer=`1`、无写，而手工 ASCII 转义日志 validator=`0`。5001 位原始 JSON 整数在输入解析处 `rc=1`，报 Python 4300-digit 限制；3001 位整数全链=`0`。两者均为首次 append 前拒绝，不是自产自拒。

建议: 单独捕获并报告 `UnicodeEncodeError`；规格若允许所有 JSON 字符串/整数，应统一支持或在规格与 validator 同步冻结容量边界。

### 测试复核

`pytest` 实跑与自报数字一致：

```text
329 passed, 1 skipped, 10 warnings in 100.37s
exit code: 0
```

范围正是五个指定文件：

```text
test_learning_events_schema_contract.py
test_fsrs_bridge.py
test_learning_event_log.py
test_g3_2_review_ledger.py
test_fsrs_golden_vectors.py
```

其中账本行为文件单跑为：

```text
100 passed, 10 warnings in 95.97s
exit code: 0
```

变异工具在 `git archive 56bfe9d4` 的 `/tmp` 隔离副本运行，实际：

```text
tool report: 138/138 KILLED
layered controls: 26 passed
exit code: 0
real/user/sys: 331.22 / 277.57 / 47.86 s
```

跑前/跑后 SHA 一致，未污染共享树。但 AST 复核得到 `136` 条语法有效、`2` 条语法无效，因此不能把工具标题解释成“138 个语义变异全部被测试杀死”。

测试承重缺口很具体：

- `fsrs_applied` 门只枚举缺键、bool false、bool true，没有非 bool。
- false→true 门只走当前 dup，没有 foreign degraded。
- hostile-char 门只做“A 首写→立即重跑 A”，没有触发“A→B”时的旧列表重建。
- 没有合法深层 `exam_board`。
- successor-anchor 门只覆盖有 `review_time`/attempt 证据的后继。
- legacy `board_form` 门只覆盖字符串。
- 非 null `pred_id` 的正常/恢复字节一致性尚无直接门。

`exam_board` 实测矩阵：

| 值 | 观测 |
|---|---|
| 空串、null、false、true、3001 位整数、普通对象/数组、emoji、C0 转义 | 首写、validator、即时重跑、第二条追加、重建后重跑均 `0`。 |
| `1e300` | 新双编码全链 `0`；旧 markerless 裸 `1e+300` 重跑 `1`。 |
| NaN、±Infinity | writer=`1`，ledger=`0`、节点不变；符合 RFC JSON 非有限数禁令。 |
| U+0085 | A/B 均可写，但 A receipt 被折为空格；随后 A=`1`，删 A 日志后会重算一次。 |
| U+007F/U+0080/U+0090/U+009F | A 首写/即时重跑=`0`；写 B=`1` 且重复 B 仍=`1`，ledger 留在 A。 |
| U+2028/U+2029 | 在 Python 3.14.4 / PyYAML 6.0.3 下第二条重建后仍全部=`0`。 |
| 合法代理对 | 解析成 emoji，全链=`0`。 |
| 孤立代理 | writer=`1`、无写；手工日志 validator=`0`。 |
| 500/512 层数组 | 首写/validator=`0`，重跑或崩溃恢复=`1 RecursionError`。 |

两处“判据本身修错后再修”的处置均到位：

- `yaml.safe_load("v: " + lit)` 现在检查映射及其 `["v"]`；中文、空串、null、bool、1000 位整数和数组实测都能正确往返。
- 对含 U+0085 的一条 JSON 文本，`str.splitlines()` 实测分成 `2` 段，而按 `b"\n"` 分仍是 `1` 行；测试 helper 改成字节 LF 口径是正确修复。

H④ 反转判断：正确。A3 是所有 `review/1` 写入方的规格义务；validator 不检查是 validator 缺口，不是许可。§6.3 的无 marker 历史行不参与 pending，因此不会因该反转被误拒。删除原先锁定 `adopted_actual` 违规放行的门不是掩盖：它已经由 `test_round16_same_instant_rows_rejected_per_a3:4665-4706` 和 M149 的正反约束替代。

`pred_id` 字节一致性声明是“有前提的代码证明 + 本轮额外实测”，不是现有测试已完整证明。append-only、唯一 id、同一启动快照下，正常路径目标尚不存在，恢复路径按目标行切开，两者取得相同前驱；额外非 null 前驱样本得到 `byte_equal=true`。应把该样本正式落成回归门。

恒真断言方面，AST 扫描了 `100` 个测试函数、`873` 个 `assert`，未发现 literal `assert True` 或左右完全相同的自比较；发现的是上述“被别段文字喂饱”的语义弱门，以及两个语法错误假杀。

预置真实性方面：

- round-17 markerless legacy receipt 是旧写点真实形态。
- anchor-miss 是真实写三次后删行，属于题设的损坏范围。
- `test:4780-4802` 的 `true + W 未覆盖` 是先正常写再手工只回退 W，当前 writer 自己无法经原子发布产出；它测的是损坏态防御，不能作为生产可达分支的证据。
- M151 的“`board_form: legacy` + 新双编码”没有正式版本产出，确实不忠实。

写入端与 validator 的双向分叉：

| 方向 | 实测形态 | 判断 |
|---|---|---|
| validator 放、writer 拒 | 同瞬间两条 review：`0/1` | writer 按 A3 正确，validator 为已登记缺口。 |
| validator 放、writer 拒 | 无 marker 但带 scored_at、缺 attempt_count：`0/1` | writer 按规格正确，validator 为已登记移交。 |
| validator 放、writer 拒 | 深层 board：`0/1` | 本次真实缺陷。 |
| validator 放、writer 拒 | 手工转义孤代理：`0/1` | 未同步的输入域分叉。 |
| writer 放、validator 拒 | 别节点非法行、别节点非字符串 id：`0/1` | A8 刻意只阻断本节点消费；属于约定分工。 |
| 两侧都放 | 成对伪造 `degraded:*` 身份键：`0/0` | 已在规格中如实登记为 validator 禁改面的移交缺口。 |

### 验证限制

- 仓库全程只读；所有 fixture、崩溃窗和变异副本都在 `/tmp`。未修改 validator 或任何送审文件。
- 没有读取或触碰 `_bmad-output/`；该目录已有的用户改动保持原样。
- 首次无提权测试因沙箱没有可用临时目录而在收集前 `FileNotFoundError`；允许写 `/tmp` 后完整测试通过。
- 崩溃窗口通过“保留 durable 行、恢复节点为旧字节”模拟，没有实施真实断电，因此没有证明存储设备层面的 fsync 行为。
- 按题设没有审并发锁，也未把缺跨进程锁计为问题。
- `_canon_tree` 本体不在 `56bfe9d4^..56bfe9d4` 的新增 diff 中；但它由本轮明确要求的深层 `exam_board` 检查触发，并使绑定快照的 write-ahead 恢复失败，故仍作为阻断项报告。
- 上轮已移交的 validator 超大整数 `float()`/`OverflowError`、`scored_at`、跨算法版本和 degraded identity 缺口未擅自修改。
- 本次复核流程参考了已存的 canvas 对抗审计工作法，具体用于证据先行、分轨复算、真实入口运行和 `/tmp` 隔离反例；最终判断仍以当前 commit 和本轮实测为准。

VERDICT: 需整改


