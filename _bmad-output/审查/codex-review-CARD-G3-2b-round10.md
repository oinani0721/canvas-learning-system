结论：需整改

### 30 条规则逐条判断

下表中的实现、规格、校验器和测试分别指 [SKILL.md](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md)、[learning-events-schema-v1.md](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md)、[validate_learning_events.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/scripts/validate_learning_events.py) 和 [test_g3_2_review_ledger.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py)。

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | FAIL | `SKILL.md:1166-1179` 虽独立构造 candidate，却把 `effective_at/review_time` 排除；规格 `:184-192` 仍要求它们进入 envelope。篡改这两个时刻后 validator `rc=0`，同 ID 重跑 `rc=0`，`fsrs_state 1→2`。 |
| 2 | PASS | `SKILL.md:301-328,832-834`。小数秒和 `+08:00` 的 durable `review_time` 均在应用前 `rc=1`；整秒 `Z/+00:00` 正常恢复。 |
| 3 | FAIL | `SKILL.md:1054-1071` 用 `(业务时刻,行号)` 判断后继，而非物理追加序；物理第 2 行时刻早于第 1 行的合法账本，validator `rc=0`、原样重跑第 1 行却 `rc=1 envelope 冲突`。 |
| 4 | PASS（限收窄范围） | 正常/恢复的评分、FSRS、attempt 核心量一致。恢复时改 `question_id/self_confidence` 后节点字节不同，但 diff 仅这三个辅助字段；因此题述收窄是诚实的。 |
| 5 | PASS | `SKILL.md:832-900`。缺失、错型、越界或与评分不自洽的 `rating/grade_norm` 均在 apply 前 `rc=1`、节点未改。 |
| 6 | FAIL | 规格 `:184-192` 仍冻结旧 envelope；对规格全文搜索 `scored_at` 得 0 条，receipt 四事实也未写入规格。 |
| 7 | PASS | `SKILL.md:499-551`。`合法行 + 无 LF 腰斩尾行` 被正确识别为第 2 行截断；首跑输出明确点名该行。 |
| 8 | PASS | `SKILL.md:876-888`。`false/"true"` 及晚于 W 的标记行均 `rc=1`；合法早到 `true` 行放行且不推进 W。 |
| 9 | FAIL（规则文字） | 字节切行、逐行解码正确，但 BOM 并不剥除：`SKILL.md:513-516` 先拒绝，使 `:522` 的 `utf-8-sig` 不可达。BOM 案 writer/validator 均 `rc=1`、双 SHA 不变。应改规则文字，不应改实现去 strip。 |
| 10 | PASS | `SKILL.md:340-351,538-545`。重复 JSON 键实测 `rc=1`、零写。 |
| 11 | FAIL（已知取舍） | `SKILL.md:1208-1316` 会重放多个 foreign pending。实测首轮 `rc=1`，但节点已写入 2 条 receipt、W 已推进，不是“任何写入前停下”。现行规格 `:160,202-206` 未要求零写。 |
| 12 | FAIL（覆盖不完整） | `test:1255-1319` 六个夹具均真实且各自通过，但遗漏可达状态 `dup=None,f1=True,W 未推进`；该状态实测导致永久漏补 FSRS。 |
| 13 | PASS | `SKILL.md:798-814` 在归属分流前拒绝不可用 `node_id`。空白节点路径实测 `rc=1`、账本未创建。 |
| 14 | PARTIAL | `SKILL.md:1251-1281` 的正常 foreign 恢复确实复放 mastery、last time、receipt、attempt，并排除当前事件；但 `_already_` 只看 ID，会对事实不匹配的 receipt 误判“已应用”并跳过。 |
| 15 | PARTIAL | 标准 degraded 案通过：mastery/attempt 不二算，只补 FSRS。但 calibration 命中并不证明 durable 行的时刻/类型就是已应用的那件事实；篡改时刻案仍二次推进 FSRS。 |
| 16 | PARTIAL | `SKILL.md:944-949` 对普通 `≤W、无标记、无 receipt` 行能停下；但 NFC 笔记下的 NFD 同主行在 `:813` 被当 foreign 跳过，门不可达。 |
| 17 | 实现 PASS / 契约 FAIL | `SKILL.md:211-217,570-575` 拒首尾空白；规格 `:40` 和 validator 只要求非空。对应测试中 validator `rc=0`、writer `rc=1`，属于未回写的单边收紧。 |
| 18 | PASS | `SKILL.md:832-875`。本节点错误 event type、concept_id、vault_id 均在消费前 `rc=1`。 |
| 19 | PASS | `SKILL.md:825-866`。带复习扩展却缺失/写错 marker 的本节点行实测 `rc=1`，没有按历史行跳过。 |
| 20 | PARTIAL | 本节点确实先跑 `validate_record_full()`；合法 §6.3 行 validator/writer 均 `rc=0` 且幂等 no-op。问题是 raw Unicode 归属会漏掉同主行，且 `:552-578` 会让完全无关的 foreign duplicate 阻塞本次写入。 |
| 21 | FAIL | `SKILL.md:581-594` 把 candidate `evid` 注入来源集合，账本丢失时形成“自证唯一”；完整 ID `K` 的历史 receipt 可吞掉另一完整 ID `quiz:K`。实测 `rc=0`、账本仍空、attempt 不变。 |
| 22 | PASS | `SKILL.md:249-269,1480-1482`。输入按字面 fullmatch；不存在日期再由完整记录自检拒绝。`2026-02-30...` 实测 `rc=1`、无日志行。 |
| 23 | PASS（狭义） | `SKILL.md:1055-1069,1244-1277` 已删除 W 兜底，后继是否计入 attempt 确由 calibration 判断；其“receipt 证据是否可信”是规则 15/30 的独立失败。 |
| 24 | FAIL | `SKILL.md:1065-1071` 对 review/1 后继仍按时刻序，而注释 `:1091-1103` 自己也承认 ordinal 应按物理行号。反例 validator `rc=0`、writer `rc=1`。 |
| 25 | PASS | `SKILL.md:249-251,1020-1027,1167-1175`。candidate 使用本次稳定输入 `_SCORED_AT`；仅改变重跑 `ts` 的真实续跑实测成功且不增行。 |
| 26 | PASS | `SKILL.md:1105-1130`。测试链中真值 E1 attempt=1 得 `rc=0`，伪值 2 得 `rc=1`，能跨缺值间隙折算。 |
| 27 | FAIL | `SKILL.md:901-916,1163-1166` 对 durable 行缺 `scored_at` 只告警并回落 `review_time`。A3 旧行反例 validator `rc=0`，连续两次续跑均 `rc=1`、W 不变。 |
| 28 | PARTIAL | 无 marker 的 `out_of_order` 不具语义、YAML 尾注释可解析，两项均通过；但“只管本笔记”的 ID 空白过滤仍用 raw `node_id`，NFD 同主形态可绕过。 |
| 29 | PARTIAL | 同键异主/异型、新记录自检、PyYAML 读取均已实现；但全局 duplicate 范围与规则 20 冲突，且合法非空 inline calibration list 会被后续文本插入写成非法 YAML。 |
| 30 | FAIL | `SKILL.md:975-988` 不比较 `attempt_count`，`grade_norm` 缺失/字符串时跳过比较，也不比较 event type/`abandoned` 或 adopted time。仅删 ledger 后把 scored 改为 abandoned，实测仍 `rc=0`、称“事实一致”。 |

规则 20 并未因调用 validator 而误拒真正的 §6.3 历史行；实测无 marker、无复习扩展的旧评分行 validator `rc=0`，同 ID writer `rc=0` no-op。实际过严项是首尾空白 ID，以及规则 20 与规则 29 对“完全属于其他节点的重复 ID”范围定义互相冲突。

八处重复字段检查不构成 correctness 缺陷。规格 `:196` 已经写成“先过本体，再做同口径防御性复核及消费侧加严”，保留纵深合理，不建议删除；若还要改，只需把规则清单的简写同步成这句话。

`_instant_only().strip()` 当前确实到不了带空白时刻：唯一调用在 `SKILL.md:925`，此前 `:832-834` 已跑完整校验。实测带空白 `effective_at` 时 writer `rc=1`、节点和账本 SHA 均不变。

校验器双向口径结果：

- writer 拒、validator 放：非 UTC durable 时刻、缺 attempt、当前节点未知版本、伪乱序、`≤W` 且无 receipt。这些已由规格 A8 明示为消费侧加严。
- writer 拒、validator 放且尚未写入规格：当前节点首尾空白 event_id。
- writer 放、validator 拒：归属明确的 foreign 坏 v1 行，以及首次遇到无 LF 截断尾行；前者是 A8 的分工，后者是 §二截断策略。
- BOM 是两边都拒，不是 writer 放行。
- 对真正进入本节点 `validate_record_full()` 的行，未发现 writer 放而 validator 拒的漏网。

因此，题目要求的“任一双向差异都算口径分叉”与规格 A8 的“foreign 坏行由离线 validator 负责、在线 writer 不阻塞”不能同时成立；需选定一套表述。

### 六种状态

| 格 | 实际前置 | 结果 |
|---|---|---|
| 1 | 无本次日志、无本次 receipt；有 1 条 foreign pending | PASS：首轮先恢复 foreign 并要求重跑，第二轮追加本次；终态 2 行、attempt=2、W=本次时刻。 |
| 2 | 无本次日志、有本次 receipt、W 已推进到本次时刻 | PASS：`rc=0`，走旧写序 no-op；节点 SHA 与行数不变。 |
| 3 | 有日志、有 receipt、W 已覆盖 | PASS：`rc=0`，幂等 no-op；节点 SHA、行数不变。 |
| 4 | 有日志、无 receipt、W 已覆盖 | PASS：`rc=1`，报“FSRS 已应用但缺校准记录”；节点不变。 |
| 5 | 有日志、有 receipt、W 未推进 | PASS：`rc=0`，只补 FSRS；mastery/attempt 不二算。 |
| 6 | 有日志、无 receipt、W 未推进 | PASS：`rc=0`，全套恢复；在相同辅助输入下与正常路径节点字节一致。 |

六格本身没有恒真断言，夹具状态也与注释一致；但“六格穷尽状态空间”是错的：

- 缺失格：无日志、有 receipt、W 未推进。
- 实测构造：先让 FSRS bridge 降级，使 receipt/attempt 已写而 W 为空；随后模拟外部程序删除 ledger；同 ID、同稳定时刻重跑。
- 结果：writer `rc=0`，输出“已完整应用/旧写序/幂等跳过”，节点 SHA 不变、W 仍为空、ledger 仍为 0 bytes。FSRS 永久不补。

### 问题清单

[BLOCKER] [SKILL.md:1166](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1166) — adopted `review_time/effective_at` 未绑定，同一次评分可二次推进 FSRS。  
依据: 正常写 E1@08-01 后，只把日志的 `effective_at` 与 `payload.review_time` 改成 08-02，保留 `scored_at`；validator `rc=0`。同 ID、原稳定时刻重跑 `rc=0`，`fsrs_state 1→2`、stability `2.3065→7.3153`、W `08-01→08-02`，attempt 仍为 1。  
建议: `scored_at` 继续承担原始评分身份，同时用 receipt 的 `ts` 绑定 durable `effective_at/review_time`；已有 receipt 时三者不同必须零写停下。规格不得用 `scored_at` 简单替换原 A4.5 的 adopted-time 约束。

[BLOCKER] [SKILL.md:969](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:969) — `dup=None,f1=True` 无条件 no-op，遗漏 degraded 后日志丢失这一可达状态。  
依据: 降级首跑 `rc=0`，receipt/attempt=1、W 为空；清空 ledger 后重跑 `rc=0`，日志仍空、W 仍空，stdout 却称“已完整应用”。  
建议: F1-only 不得仅凭 receipt no-op；还要证明 W/FSRS 已覆盖 receipt 的 adopted time。证明不了则停止，或在 receipt 持久化足够调度事实后恢复。

[BLOCKER] [SKILL.md:807](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:807) — NFC/NFD 只在 duplicate owner 检查归一化，适用集路由仍 raw compare，合法 pending 被永久漏算。  
依据: 当前文件名为 NFC `café笔记`，预置 node/concept 为等价 NFD 的 E1，validator `rc=0`；写 E2 得 `rc=0`。终态日志 attempts=`[1,1]`，笔记 attempt=1、receipt 只有 E2、W=E2，E1 未应用。  
建议: 使用同一个 NFC node-key 完成适用集、空白 ID、legacy、concept 和 duplicate ownership 的全部归属比较，不能只修一个分支。

[BLOCKER] [SKILL.md:581](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:581) — 裸 ID 兼容把 candidate 注入唯一性证据，另一完整 ID 的评分被静默吞掉。  
依据: 先应用完整 ID `K` 并形成 receipt `K`；删除 ledger；再提交本地 ID `K`，其完整 ID 实为 `quiz:K`。writer `rc=0`，账本仍 0 bytes、attempt `1→1`、节点不变。  
建议: 从 `_EARLY_LEDGER_IDS` 删除 candidate 注入；账本缺失时裸形态来源不可证，应停下。若要长期兼容，给新 receipt 增加明确格式版本，区分“完整 ID”与“历史裸 ID”。

[BLOCKER] [SKILL.md:975](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:975) — receipt 比较既没实现所称四事实，四事实本身也不足以表示评分事件。  
依据: 正常首写 `answer_scored/rating=3/abandoned=false` 后只清空 ledger；同完整 ID、同 `scored_at`、同 grade，改为 `abandoned=true` 重跑。实际 `rc=0`、称“receipt 事实一致”，账本仍空、attempt=1、receipt 仍是 `abandoned=false`。另测 receipt attempt=999、grade 为字符串/缺失也被放行。  
建议: 严格验证完整 ID、event type/abandoned、原始时刻、adopted 时刻、ordinal、grade 六类事实；全部要求存在、类型正确且可证明相等。

[HIGH] [SKILL.md:684](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:684) — 读取改成真实 YAML，但写回仍假定 block list，会破坏合法 frontmatter。  
依据: 把既有 calibration 改成等价合法的非空 inline list，再写 E2：首跑 `rc=0`、ledger 2 行，但节点随后被 `yaml.safe_load` 判 `ParserError`；E2 重跑 `rc=1`。indentless list 和 `{}` 也复现。  
建议: 结构化读取并重写 calibration list；非 list/null 在 append 前零写拒绝。应在 durable append 前预生成并重新解析候选 frontmatter，避免先落账后才发现无法发布合法 YAML。

[HIGH] [SKILL.md:901](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:901) — 缺 `scored_at` 的 A3 旧行被宣称可回落，实际无法安全续跑。  
依据: validator `rc=0` 的旧行，原始稳定时刻 08-01、A3 adopted 时刻 12-01+1s；删掉 `scored_at` 后连续两次续跑均 `rc=1 envelope 冲突`，节点和 W 不变。  
建议: 新行需在规格和 validator 中强制 `scored_at`；旧行缺失时在任何应用前明确 fail-closed，并提供迁移/人工裁定，不能告警后猜 `review_time`。

[HIGH] [SKILL.md:499](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:499) — 已登记的截断隔离仍只能成功一次，后续评分永久受阻。  
依据: 合法前缀后加无 LF 的腰斩 UTF-8 尾行。首次评分 `rc=0`，账本 `554→1160 bytes`、attempt=1、W 已写；第二次评分 `rc=1`，报该坏行现为中间非法 UTF-8，节点与账本 SHA/长度均不变。  
建议: 按已登记方案增加 validator 可识别的隔离记录/隔离机制；在闭环完成前不要把 LF guard 描述成可持续“自愈”。

[MEDIUM] [SKILL.md:1054](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1054) — ordinal 对 review/1 后继按业务时刻而非物理写序回推。  
依据: ledger 第 1 行 E1@08-02 attempt=1，第 2 行 E2 的 adopted time=08-01、attempt=2；receipt 和笔记证明 E2 后写且已计数。validator `rc=0`，E1 原样重跑却 `rc=1`。  
建议: FSRS pending 可按业务时刻排序；attempt 因果序必须独立按物理行号计算。

[MEDIUM] [SKILL.md:552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:552) — 两条完全属于其他节点的 duplicate 会冻结当前节点，与 A8 隔离条款冲突。  
依据: 两条 usable foreign 行重复同一 ID，validator `rc=1`、当前 writer 也 `rc=1`，本次评分未写。  
建议: 保留 validator 的全文件唯一检查；在线 writer 只因 collision 涉及当前 `evid`、当前节点或不可路由行而停。同步把规则 29 缩成这一范围；若产品选择全局冻结，则应反向修改 A8。

[MEDIUM] [learning-events-schema-v1.md:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:184) — 新的稳定时刻/receipt 裁决没有回写真相源，当前实现与规格是两套身份定义。  
依据: 规格全文没有 `scored_at`；仍明确写 envelope 包含 `effective_at` 和 payload。实际 time-tamper 反例证明不能只改文案删除 adopted time。  
建议: 将“原始评分身份”和“已提交调度副作用”分层冻结：前者包含 `scored_at`，后者绑定 adopted time、event type、ordinal 与 grade；同步实现、规格和 validator。

[MEDIUM] [SKILL.md:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:211) — event_id 首尾空白属于未写入规格/validator 的单边收紧。  
依据: 相同带空白 ID，validator `rc=0`、本节点 writer `rc=1`。  
建议: 若产品要禁止空白，更新规格并在 validator/所有写点统一执行；否则不能声称两侧同口径。

[LOW] [SKILL.md:496](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:496) — BOM 注释和规则 9 仍声称会剥除，但实际及测试均明确拒绝。  
依据: BOM+合法行 writer `rc=1`、validator `rc=1`；`SKILL.md:513-516` 的拒绝先于 `utf-8-sig` 解码。  
建议: 把规则 9 和旧注释改成“BOM fail-closed”，保留当前拒绝逻辑。

[LOW] [SKILL.md:602](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:602) — 仓内注释仍无条件声称正常/恢复“逐字节相同”。  
依据: 只改变恢复时的三个辅助输入，两个合法终态的节点 bytes 不同；核心评分/调度/序数相同。  
建议: 将 `:602-604,703-704,1333-1335,1420-1426` 及对应测试说明同步改为题述的收窄表述。

### 测试复核

按指定环境实跑五个相关测试文件：

```text
281 collected / 280 passed / 1 skipped
exit code: 0
10 warnings
62.64s
```

单跑 `test_g3_2_review_ledger.py`：

```text
51 passed
exit code: 0
58.83s
```

因此自报的 `281 collected / 280 passed / 1 skipped` 属实。唯一 skip 位于 `test_learning_events_schema_contract.py:1104-1111`，原因是该 worktree 没有 live `learning_events.jsonl`。

测试质量复核：

- 六格的前置条件和主要分支断言都真实，没有发现无论实现如何都恒真的断言。
- `test:1274,1283,1291,1307` 等零写断言只比较节点 SHA 和 ledger 行数；同样行数下改写 ledger bytes 会漏检，建议统一使用现成的 `_write_face()`。
- 格 6 用同一实现正常路径作 golden，可抓正常/恢复分叉，但抓不到两条路径共同遗漏的事实。
- 缺少 `dup=None,f1=True,W 未推进`。
- 缺少 adopted-time 篡改、NFC/NFD 不同 ID pending、账本丢失下裸/完整 ID、receipt event type/ordinal/错型 grade、非空 inline YAML、物理行序与业务时刻逆序等反例。
- 没有运行 `backend/scripts/g32b_mutation_gates.py`。

### 验证限制

- 工作树全程只读；所有构造输入位于隔离 `/tmp`/`/private/tmp`。
- 未测试并发，也未把缺锁列为问题，结论全部成立于单进程串行前提。
- 崩溃通过保留 ledger、回滚节点或删除 ledger 模拟；没有在每一个 syscall 上做注入。截断尾行做了真实两次运行验证。
- 当前 HEAD 为 `fa545dca6de71bd3470683a648e76a74065ed042`。
- 开始复核时工作树已存在用户改动：`fsrs_bridge.py` 末尾多一段不可达的第二个 `__main__`，以及若干 `_bmad-output/审查` 未跟踪文件；均未改动或清理。第二个入口因前一处 `sys.exit(main())` 不可达，不影响本次测试结果。
- 临时复现目录属于易失性证据；关键退出码和文件终态已在上文逐项记录。

VERDICT: 需整改
