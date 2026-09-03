结论：需整改

已实测确认两条 exactly-once BLOCKER：一条会把同一次评分的 FSRS 调度算两遍；另一条会把不同完整 ID 的新评分静默吞掉。规则 20 未发现误拒合法历史行；“逐字节相同”的收窄表述是诚实的，但不影响本结论。

### 32 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | PASS | `SKILL.md:1278-1291` 独立构造 candidate；额外键/缺键敌对门实跑均 `rc=1`，不再从 durable 自抄。 |
| 2 | PASS | `SKILL.md:308-335` 强制 UTC canonical 整秒。合法非 UTC offset 行实际 validator `0 violations`、writer `rc=1`，是 `schema-v1.md:152,207` 明定的消费侧加严。 |
| 3 | PARTIAL | `SKILL.md:1141-1254,1381-1389` 的序数回推算术在六格内正确；但分支依据只是 receipt ID presence，别名/事实不符时并非“可证”，见规则 14/21/30。 |
| 4 | PASS | `SKILL.md:713-776,1443-1475` 锁定量取日志值；六格第 6 格实测恢复节点 bytes 等于直接应用 golden。辅助输入不在载荷的收窄表述诚实，未掩盖评分 exactly-once 缺陷。 |
| 5 | PASS | `SKILL.md:890-899,954-965` 先过 validator，再复核 rating/grade；缺失、错型、不自洽用例均 `rc=1`。 |
| 6 | PARTIAL | 同口径复核已写入 `schema-v1.md:195-201`；但当前三时刻/envelope 已未同步，`schema-v1.md:184-192` 仍是旧契约。 |
| 7 | PASS | `SKILL.md:506-558` 按最后非空字节行判断 LF；尾部空白和坏末行矩阵实跑结果符合预期。 |
| 8 | PASS | `SKILL.md:941-953` 只接受布尔 `true`，且标记时刻晚于 W 会 `rc=1`。 |
| 9 | FAIL（应改规则文字） | `SKILL.md:520-529` 在解码前直接拒 BOM，所谓“首行剥 BOM”不可达。`test_g3_2_review_ledger.py:1827-1844` 实跑 BOM 为 writer `rc=1`，validator 也拒；当前代码口径正确。 |
| 10 | PASS | `SKILL.md:545-552` 与 `validator.py:115-127` 都拒重复 JSON 键；实跑两侧均失败。 |
| 11 | FAIL（应改规则文字） | `SKILL.md:1320-1414` 只在“本次 dup 与 foreign 混队”时停；两条纯 foreign pending 实跑 settled `rc=0`、ledger `2→3`、attempt `0→3`。`schema-v1.md:160-162` 本来也要求按序重放至空。 |
| 12 | PASS（但非穷尽） | `test_g3_2_review_ledger.py:1255-1319` 的六个前置状态均属实并执行生产块；新增 `L=0,C=1,W=0` 是第七个语义分支，尚未纳入集中门。 |
| 13 | PASS | `SKILL.md:865-878` 在归属前拒不可用 `node_id`。实跑缺 node 行 `rc=1`；别节点缺 payload 不阻塞，writer `rc=0`。 |
| 14 | FAIL | `SKILL.md:1342-1393` 虽能复放各字段，但 receipt 已存在时只查 ID、不比事实。篡改 foreign 行分数后，FSRS 按新分数重放、mastery/receipt 仍保留旧分数。 |
| 15 | PARTIAL | 诚实 degraded 场景下，第 5 格实测 mastery/attempt 不会二次吸收；但 receipt presence 可由别名或不一致事实造成假阳性。 |
| 16 | PARTIAL | `SKILL.md:1002-1014` 对真正“≤W、未标、无 receipt”行会 `rc=1`；但错误别名 receipt 可绕过“无 receipt”前提。 |
| 17 | PASS | `SKILL.md:211-217,577-582`：本次及本笔记行的空白 ID 均拒；别笔记合法空白 ID 不阻塞。 |
| 18 | PASS | `SKILL.md:909-940` 对类型、concept、vault 分别校验；对应坏例均 `rc=1`。 |
| 19 | PASS | `SKILL.md:911-931` 对带扩展特征但 marker 非法的本笔记行 fail-closed，不能冒充历史行。 |
| 20 | PASS | `SKILL.md:855-931` 控制流为归属→版本/payload→`validate_record_full()`→marker。实跑真历史行 validator/writer 均 `0`；别节点坏行 validator `1`、writer `0`；本节点 v2、缺 attempt、非 UTC 分别由 `schema-v1.md:195-201,298-300` 授权加严。未发现合法历史行误拒。 |
| 21 | FAIL | `SKILL.md:381-426` 在来源集合为空时仍返回 true；`SKILL.md:1267` 的 adopted receipt 查找又不复用 compat resolver。实测不同完整 ID 的新评分被零次应用。 |
| 22 | PASS | `SKILL.md:249-276,1598-1609` 字面拒空白/畸形输入，新记录追加前再过 validator；未观察到洗值后落账。 |
| 23 | PARTIAL | `SKILL.md:1151-1165` 确实不用 W 判断次数是否已计入；但 calibration ID presence 不是事实一致性的充分证据。 |
| 24 | PASS | `SKILL.md:1168-1229` 优先从日志 ordinal 回推；遇历史间隙会指名缺失行并 `rc=1`，未发现猜值或误报 envelope。 |
| 25 | PASS | `SKILL.md:249-258,1255-1285` candidate 使用 payload 内稳定时刻；六格续跑时变更运行时 `ts` 仍正常收敛。 |
| 26 | PASS | `SKILL.md:1201-1229` 对跨过的计数贡献逐条折算；不可证历史行会停。 |
| 27 | FAIL | 三时刻首写见 `SKILL.md:1551-1565`，但 foreign replay 不执行 adopted-time 绑定，且 `schema-v1.md:184-192` 仍无 `scored_at`/receipt 契约；实测可二次推进。 |
| 28 | PASS | `SKILL.md:1211-1217,429-457,572-582` 分别实现历史 OO 键无契约语义、YAML 尾注释解析及本笔记限定的 ID 空白门。 |
| 29 | PASS（写回问题归规则 32） | `SKILL.md:559-585` 全局 ID 唯一、`:1603-1609` 新记录自检、`:429-457` 用 PyYAML 读 receipt；同 ID 异主/异型实跑均拒。 |
| 30 | FAIL | `SKILL.md:1043-1070` 不比较 receipt `attempt_count` 与期望序数，`ts` 也只验非空。把 attempt `1→999` 后删除 ledger，同事件重跑仍 `rc=0` 并称“事实一致”。 |
| 31 | FAIL | 六处归属键和 candidate 不自证已修；但 `SKILL.md:419-426` 的空来源放行、`:1043-1070` 的六事实不严仍破坏整体声明。 |
| 32 | FAIL | W 覆盖门本身存在于 `SKILL.md:1073-1084`；但 adopted-time 漏 foreign、漏缺 `ts`、漏历史 bare receipt，且 `SKILL.md:803-843,1570-1579` 的 YAML 预演并非全路径有效。 |

双向口径复核结果：

- writer 比 validator 严但规格明确授权的情形：非 UTC review time、缺 `attempt_count`、本节点未知版本、本笔记空白 ID、迟到未标且无 receipt。
- writer 放行、validator 拒的别节点坏行，是 `schema-v1.md:196-200` 明定的作用域边界。
- 对本笔记实际消费的 `review/1` 行，未发现绕过 `validate_record_full()` 的日志形状；真正的漏网位于 validator 不负责的 receipt/frontmatter 证明层。
- 八处重复检查不算缺陷。`schema-v1.md:196` 已承认它们是同口径纵深；建议只把标题改成“先过校验器，再做同口径复核与消费侧加严”，不要删代码。
- `_instant_only().strip()` 的“到不了”仅对已完整校验的 ledger 时刻成立。receipt `ts=" 2026-08-01T10:00:00Z "` 实跑可到达并被 strip，同事件重跑 `rc=0`；广义声明不成立。
- 两阶段在正常的早于/等于/晚于三种关系下第二轮收敛；但 foreign 篡改反例会“收敛到错误状态”，合法一空格 YAML 反例则会永久卡住。

### 六种状态

| 状态 | 结论 | 实测依据 |
|---|---|---|
| `L=0,C=0,W=0` | PASS | 目标行/receipt 不存在，`W=None`；先恢复 foreign 时首轮 `rc=1`，第二轮 `rc=0`，最终目标行和 receipt 存在、W 到目标时刻。 |
| `L=0,C=1,W=1` | PASS | 删除目标 ledger 行但保留 receipt/W；重跑 `rc=0`，stdout 含“旧写序/不补录”，节点 SHA 与 ledger 行数不变。 |
| `L=1,C=1,W=1` | PASS | 完整成功态重跑 `rc=0`、“幂等跳过”，节点 SHA 不变、ledger 仍一行。 |
| `L=1,C=0,W=1` | PASS | 删除 calibration 后重跑 `rc=1`，报“缺校准记录/人工核对”，节点与 ledger 行数不变。 |
| `L=1,C=1,W=0` | PASS | degraded 首写后 receipt/attempt 存在但无 W；恢复 `rc=0`，只补 FSRS，mastery 与 attempt 字节未变化。 |
| `L=1,C=0,W=0` | PASS | 保留 ledger、把节点回滚到初态；恢复 `rc=0`，节点 bytes 与直接应用 golden 完全相同。 |

补充状态 `L=0,C=1,W=0` 未进入上述六格集中门。我独立构造后得到 `rc=1`，stderr 指明 `fsrs_last_review=None` 未覆盖 receipt 时刻，节点与空 ledger 零写；当前行为正确，但需要测试锁定。

六格内没有字面常量 assert 或左右完全相同的自比较，因此未发现真正的恒真断言。不过 `test_g3_2_review_ledger.py:1274,1283,1291,1318` 只比较 ledger 行数而非 bytes；同样行数下篡改内容仍可能通过。

### 问题清单

[BLOCKER] [SKILL.md:1267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1267)、[SKILL.md:1320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1320) — adopted-time/receipt 证明没有覆盖每一条 foreign pending，同一次评分可二次推进 FSRS。  
依据: 正常写入 `E1@08-01` 后为 `state=1, stability=2.3065, W=08-01, attempt=1`；只把 ledger 的 `effective_at/review_time` 改为 `08-02`，保留 `scored_at` 和 receipt，validator `rc=0`。提交 E2 的首轮虽然 `rc=1`，却已发布 E1“恢复”：`state 1→2`、`stability 2.3065→7.3153`、`W 08-01→08-02`。第二轮 `rc=0`、attempts `[1,2]`，表面正常但 E1 已计算两次。删除 exact receipt 的 `ts` 也能得到同样结果。  
建议: 在任何 bridge 调用及 `_already_` 判定前，共用一个 per-row resolver：唯一解析 full/bare receipt，严格校验全部事实，并强制 ledger `effective_at`、`review_time`、receipt `ts` 三方同瞬间；receipt 缺字段必须停。

[BLOCKER] [SKILL.md:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:381)、[SKILL.md:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:419) — ledger 缺失时，历史 bare-ID 来源为空仍被当成唯一，另一完整 ID 的评分会静默漏算。  
依据: 先提交本地 ID `quiz:K`，durable full ID 为 `quiz:quiz:K`；把 receipt 改成历史 bare `quiz:K` 并清空 ledger。再提交不同本地 ID `K`（full ID=`quiz:K`），实际 `rc=0`、stdout 称“事实一致且调度已覆盖”，ledger `0 bytes`、attempt 仍 1、receipt 仍一条；第二次评分零次应用。现场：`/private/tmp/codex-card-w7-r9.Hquw4m/manual/missing-ledger-alias/repo/canvas-vault`。  
建议: compat 成功条件必须是 `_sources == {ev_id}`；集合为空同样不可证，必须停。resolver 应返回实际 receipt 及其唯一来源，不能只返回布尔值。

[HIGH] [SKILL.md:1358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1358) — foreign replay 只看 receipt ID presence，可把篡改后的调度与旧 mastery/receipt 拼成自相矛盾状态。  
依据: E1 以 `grade=.75` degraded 落账后，将 ledger 改为 `grade=0/rating=1`，validator `rc=0`。恢复按 Again 得到 `stability=.212`、due `+1min`，但 mastery 仍 `.57`、receipt 仍 `.75`。  
建议: `_already_` 不得是布尔 presence；必须先证明 receipt 的完整 ID、稳定时刻、序数、分数、弃答状态和 adopted time 均与该 ledger 行一致。

[HIGH] [SKILL.md:803](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:803)、[SKILL.md:1570](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1570) — 落账前 YAML 预演未覆盖所有返回路径，合法 YAML 仍会先增 ledger 后被写坏。  
依据: 合法一空格列表 `calibration_log:\n - ...` 的前态可被 PyYAML 解析为 list；新评分 `rc=0`、ledger `1→2`，节点被写成两空格新条目加一空格旧条目，`yaml.safe_load` 得 `ParserError`；同事件重跑 `rc=1`。另以合法 `"calibration_log": []` 开始，首写 `rc=0` 后节点同时出现 quoted 与 bare 两个语义相同键。  
建议: 只要解析结果是 list，就结构化重建目标段；所有返回路径都要对完整候选 frontmatter 做 duplicate-aware YAML 解析。不要用缩进前缀或只认裸键的正则判断结构。

[MEDIUM] [SKILL.md:1043](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1043)、[SKILL.md:287](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:287) — “六类事实存在、类型正确、相等”声明宽于实现。  
依据: 删除 ledger 并把 receipt attempt `1→999` 后，同事件重跑仍 `rc=0` 并称“事实一致”；receipt `ts` 带首尾空白也能到 `_instant_only()` 并被 strip 后 `rc=0`。  
建议: `attempt_count` 必须与可证明序数相等；无法证明就停。receipt `ts` 应使用 canonical 字面门并拒空白，不得依赖 `.strip()`。

[MEDIUM] [schema-v1.md:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:184)、[SKILL.md:1255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1255) — authoritative schema 仍冻结旧 envelope，与三时刻/receipt 实现不一致。  
依据: 规格仍把 `effective_at` 和 payload 纳入 canonical envelope，只排除两个 FSRS 快照；实现排除 adopted time、改比 `scored_at` 并依赖 receipt。规格全文没有完整的 `scored_at`/adopted receipt 契约。  
建议: 改规格侧，明确 stable/adopted/recorded 三时刻、固定键集、compat resolver 及 receipt 缺失时的 fail-closed。不要简单把实现退回旧 envelope，否则 A3 推时后的合法续跑会再次冲突。

[LOW] [test_g3_2_review_ledger.py:1229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1229)、[test_g3_2_review_ledger.py:3309](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:3309) — 六格门和 adopted-time 门没有覆盖本轮真正失效的分支。  
依据: 集中门缺 `L=0,C=1,W=0`；adopted receipt 仅测试“本次 dup + full ID + ts 存在”，没有 foreign、缺 ts、历史 bare 变体。  
建议: 增加上述四类生产入口回归，并用 `_write_face()` 同时比较节点 SHA 与 ledger SHA，不只比行数。

[LOW] `SKILL.md:520-529,1406-1414` — 规则 9、11 的自报文字与实际/规格相反。  
依据: BOM 实跑 writer/validator 都拒；两条纯 foreign pending settled `rc=0` 并恢复到 attempt 3。  
建议: 规则 9 改为“BOM fail-closed”；规则 11 改为“本次 dup 与任一 foreign pending 混队时停”，不应为迎合旧清单而改代码。

### 测试复核

实际结果：

```text
backend/tests/regression/test_g3_2_review_ledger.py
collected 52 items
52 passed, 10 warnings
```

五文件裁判组合：

```text
collected 282 items
281 passed, 1 skipped, 10 warnings in 70.00s
```

自报的 `282 collected / 281 passed / 1 skipped` 完全吻合。唯一 skip 是 `test_repo_vault_ledger_schema_v1`，原因是该 worktree 没有 `canvas-vault/learning_events.jsonl`。

用户给出的字面路径 `.venv/bin/pytest` 在 worktree 根不存在，首次实际 `exit 127`；随后使用真实环境 `backend/.venv/bin/pytest`，其余环境变量按要求设置，未设置 `DEBUG=true`。

绿门不推翻反例：52 个行为测试没有覆盖 foreign adopted-time、receipt 缺 `ts`、历史 bare adopted resolver，以及来源集合为空的 full-ID 冲突。

### 验证限制

- 审计锚：branch `card/w7-ledger`，HEAD `df7ad35694b6d26969df2deef82a891139d9caab`。
- 工作开始时 `canvas-vault/.claude/scripts/fsrs_bridge.py` 已有用户侧未提交修改：原主入口之后附加了两个不可达的 `exit(9)` 块；本次未修改或清理。
- 生产块从 `SKILL.md` 精确抽取，反例均在 `/private/tmp`/系统临时目录搭最小 vault，以真实 validator 和 bridge 子进程运行，没有 mock。
- 未运行用户禁止的 `g32b_mutation_gates.py`，未修改任何被复核文件。
- 未模拟物理断电，只构造了对应的 durable 文件状态和进程退出窗口。
- 未检查并发；本结论仅针对用户要求的单进程串行前提。

VERDICT: 需整改


