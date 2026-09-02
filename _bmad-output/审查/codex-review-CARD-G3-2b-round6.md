结论：需整改

### 22 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | PASS | `quiz-answer/SKILL.md:851-860` 独立构造固定 envelope，并排除两个 FSRS 环境键。相同 8 键重试 `rc=0`，修改 envelope 事实字段则 `rc=1 envelope 冲突`。 |
| 2 | PASS | `quiz-answer/SKILL.md:277-304,671-673` 对 durable `review_time` 先用 `_WHOLE_SECOND_RE` 再要求 UTC；小数秒或非零偏移行均在写节点前 `rc=1`。 |
| 3 | FAIL | `quiz-answer/SKILL.md:803-850` 用 `review_time <= W` 判断后续事件是否已计数，漏掉“mastery/attempt/calibration 已落、W 未动”的 degraded 事件。实测 E1→degraded E2 后重跑 E1，`rc=1 envelope 冲突`，但事实本身一致。 |
| 4 | FAIL | `quiz-answer/SKILL.md:586-590,1023-1053` 时刻和分数取 durable 行正确，但 `question_id`、自评和 callout 仍取重试输入。实测直接路径 SHA `d4710ec8…`，恢复路径 SHA `b3d5aeb…`，`byte_equal=false`。 |
| 5 | PASS | `quiz-answer/SKILL.md:734-743` 与 `validate_learning_events.py:1334-1469` 都拒缺失、错误类型、越界或与 grade 不自洽的评分；对应输入均 `rc=1`、节点未改。 |
| 6 | PASS | `learning-events-schema-v1.md:184-202` 已写入 envelope、序数、完整校验及消费侧加严裁决。 |
| 7 | PASS | `quiz-answer/SKILL.md:420-456` 按最后一个非空字节行的位置判断 LF。实测 `坏行\n   ` 被视为完整坏行并 `rc=1`；真正无 LF 的截断末行被隔离后可继续。 |
| 8 | PASS | `quiz-answer/SKILL.md:715-727` 只接受布尔 `true`，并要求其时刻不晚于 W；字符串 `"true"`、`false` 和晚于 W 的伪乱序行均 `rc=1`。 |
| 9 | PARTIAL | `quiz-answer/SKILL.md:409-456` 的逐字节切行、首行 BOM 剥离及末行半字符容忍已实现；但 BOM 账本 writer `rc=0`、validator `rc=1 Unexpected UTF-8 BOM`，与校验器分叉。 |
| 10 | PASS | `quiz-answer/SKILL.md:306-317,438-450` 使用 `object_pairs_hook` 拒重复键；实测重复键行 `rc=1`，未被截断容忍分支吞掉。 |
| 11 | FAIL（按字面） | `quiz-answer/SKILL.md:900-1019` 会重放多个 foreign pending，再非零退出阻止本次追加；`test_g3_2_review_ledger.py:1983-2007` 实测首轮恢复两条、次轮成功，attempts=`[1,2,3]`。若“停下”仅指“恢复后不追加”，行为 PASS，但规则文字必须改写。 |
| 12 | PASS（有盲点） | `test_g3_2_review_ledger.py:1231-1292` 确实逐格构造六态，无恒真或自比较断言；但格 2/3/5 的 F1=True 都依赖裸 ID 兼容回落，未锁定“新校准记录必须存完整 ID”。 |
| 13 | FAIL | `quiz-answer/SKILL.md:642-653` 只检查 `node_id` 是字符串，`""` 和 `"   "`会被当成别节点跳过。两种实测均 writer settled `rc=0`、账本增至 2 行、节点推进，而 validator `rc=1`。违反 `learning-events-schema-v1.md:14-16,201` 的“可用 node_id”读方义务。 |
| 14 | PASS | `quiz-answer/SKILL.md:900-971` 对真正进入 foreign replay 的事件复放 mastery、last_examined、calibration、attempt；固定辅助输入时，正常链与 degraded→恢复链最终字节一致，attempts=`[1,2]`。 |
| 15 | FAIL | `quiz-answer/SKILL.md:340-368,586-600` 的校准判据会被裸/完整 ID 别名污染，能够“为真但其实是另一事件”；`calibration_log: []` 写坏场景又能“为假但副作用已经应用”。基础 degraded 防双吃逻辑本身通过。 |
| 16 | FAIL | `quiz-answer/SKILL.md:891-896` 有门，但调用同一个错误的兼容判据。实测未标乱序、时刻等于 W、实际无自身校准的行被误认已应用，最终账本 attempts=`[1,2,2]`、writer/validator 均 `rc=0`。 |
| 17 | FAIL | 仅本次输入在 `quiz-answer/SKILL.md:208-214` 检查空白；durable 行未检查。预置 `" quiz:same#q1 "` 后重跑 `same#q1`，最终 `rc=0`、两个 ID 并存、attempt=`2`，同一评分被算两遍。当前规格/validator 也只要求“非空”，须同步补规格。 |
| 18 | PASS | `quiz-answer/SKILL.md:671-714` 先过完整校验，再限定两种评分类型及 concept/vault；类型、concept、vault 任一不符均 `rc=1`。 |
| 19 | PASS | `quiz-answer/SKILL.md:664-705` 完整校验先于历史分流；本节点非法 marker 或“无 marker 但带扩展键”均 `rc=1`，没有当历史行跳过。 |
| 20 | FAIL（骨架正确） | `quiz-answer/SKILL.md:642-684` 的归属、版本、payload、完整校验顺序正确，别节点坏行不阻塞也符合分层边界；但 `:769-772` 把 validator `rc=0` 的合法 §6.3 同 ID 历史评分行拒成 `rc=1`。此外 NaN、空行、BOM 仍存在原始解析口径分叉。 |
| 21 | FAIL / BLOCKER | `quiz-answer/SKILL.md:340-368,476-483,586-600` 注释称新写存完整 ID，但正常路径实际 `_e_id=eid`。实测先写输入 `quiz:K`，再写不同输入 `K`：两次都 `rc=0`，第二次被幂等跳过，账本始终只有 `quiz:quiz:K`、attempt=`1`。 |
| 22 | FAIL | `quiz-answer/SKILL.md:243-245` 使用 `_TS_RE.match()`；Python `$` 会在末尾换行前匹配。输入 `ts="2026-08-02T10:00:00Z\n"` 时 writer `rc=0` 并原样写入，随后 validator `rc=1`。 |

8 处与校验器完全等价的重复检查本身不是行为缺陷，保留纵深防御比删除更稳妥。应把规格 A8 改成“先过校验器本体；允许同口径纵深复验；再叠加消费侧更严项，且复验不得改变受理集合”，并用差分测试锁住等价性。

`_instant_only().strip()` 当前确实到不了脏时刻：唯一调用在 `quiz-answer/SKILL.md:748`，本节点 v1 行此前已在 `:671-673` 完整校验。实测带空白 `effective_at` 在该调用前 `rc=1`；合法 `18:00+08:00` 与 `10:00Z` 同瞬间时 writer/validator 均 `rc=0`。

### 六种状态

| 状态 | 结论 | 实跑依据 |
|---|---|---|
| 1. `dup=无, F1=F` | PASS | foreign pending 首轮 `rc=1` 并恢复，W=`2026-08-01T10:00:00Z`、账本仍 1 行；自动重跑 `rc=0`，账本 2 行、W 推到本次时刻。 |
| 2. `dup=无, F1=T` | PASS | 旧写序孤儿输入 `rc=0` no-op；节点与账本 bytes 均未变化。 |
| 3. `dup=有, F1=T, applied=T` | PASS | 完整成功后重跑 `rc=0` 幂等跳过；节点和账本 bytes 均未变化。 |
| 4. `dup=有, F1=F, applied=T` | PASS | `rc=1`，提示缺校准、需人工裁定；节点和账本 bytes 均未变化。 |
| 5. `dup=有, F1=T, applied=F` | PASS | degraded 初态无 W；恢复 `rc=0` 后 W=`TS1`，EMA/attempt 不变、calibration `1→1`、账本 bytes 不变。 |
| 6. `dup=有, F1=F, applied=F` | PASS | 崩溃窗口恢复 `rc=0`，节点与固定辅助输入下的 golden bytes 相同，账本仍 1 行。 |

六格前置按程序当前的“compat-F1”语义真实成立，也没有恒真断言。但格 2/3/5 的 calibration 实际保存裸 ID，exact-full F1 均为 false；测试只证明兼容回落能命中，没有证明规则 21 声称的“新数据一律完整 ID”。格 2–5 部分断言只比较账本行数；格 5 也未在测试源码直接断言 calibration/last_examined，不过额外动态观测确认 calibration 未增长。

### 问题清单

[BLOCKER] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:340-368,476-483,586-600` — 正常新写仍存裸校准 ID，兼容查询又在歧义证明前直接命中，导致一次正常串行评分静默漏算。  
依据: `/tmp/codex-g32-primary-alias-normal-1ruojt2q` 中先提交 `event_id="quiz:K"`，账本得到 `quiz:quiz:K`、校准却为 `quiz:K`；再提交不同事件 `K`，第二次 `rc=0` 并输出“已完整应用…账本无对应行”，节点/账本 SHA 不变，attempt=`1`，预期的 `quiz:K` 账本行不存在。  
建议: 正常路径保存 `evid`；兼容查询不能在 exact scalar 命中时直接返回，必须同时枚举该 scalar 作为“完整 ID”和“历史裸 ID”可能对应的账本身份，不能唯一证明就停。若业务禁止输入已带 `quiz:`，也须在入口明确拒绝并写入规格。

[BLOCKER] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:208-214,409-483` — durable `event_id` 首尾空白未检查，同一次评分可被两个字面 ID 重放两遍。  
依据: `/tmp/codex-g32-primary-wsid-vmom2y3r` 预置 `" quiz:same#q1 "`，再重跑 canonical `same#q1`；settled `rc=0`，账本 IDs 为 `[" quiz:same#q1 ","quiz:same#q1"]`，attempt `1→2`、校准两条、W 再推进；validator 也 `rc=0`。  
建议: 若采纳规则 17，先在 `learning-events-schema-v1.md` 明确 event_id 禁止首尾空白，再同步收紧 validator 和 writer 的全账本扫描；不得只检查本次输入。

[BLOCKER] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:642-653` — 空串或纯空白 `node_id` 被当作别节点跳过，无法路由的真实评分可能永久漏算。  
依据: `/tmp/codex-g32-primary-route-pb7idrcd` 分别预置 `node_id=""`、`"   "` 且 payload 指向当前概念；两次 writer settled 都 `rc=0`、账本增至 2 行、W 推进至 `2026-08-02T10:00:00Z`，而 validator `rc=1`。  
建议: 在归属比较前要求 `node_id` 是非空且 `node_id.strip()==node_id` 的字符串；同时澄清规格 §三“通用事件可为空”和 §一/A8“消费侧必须可用”的优先关系。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:803-850` — 序数回推把 W 当成所有后续评分副作用的应用证明，误拒含后续 degraded 事件的合法历史重试。  
依据: `/tmp/codex-g32-primary-ordinal-wb__duxn` 中 E1 正常后，E2 degraded：attempt=`2`、calibration 含 E2，但 W 仍为 E1；账本 validator `rc=0`。重跑 E1 得 `rc=1 envelope 冲突`，节点/账本零写。  
建议: 修复 ID 判据后，逐个用其 calibration 证据判断后续事件是否已贡献 attempt，而不是仅用 `review_time <= W`。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:243-245` — 输入时刻正则用 `match`，末尾换行可穿透并由程序自己产出非法日志。  
依据: `/tmp/codex-g32-primary-ts-z1124n3u` 输入末尾 `\n`，writer `rc=0`，解析后的 `recorded_at` 确实含换行；validator `rc=1 recorded_at 非法日期时间`。  
建议: 使用 `_TS_RE.fullmatch()`，并调用校验器的完整时间语义解析，避免只做词法匹配。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:438-444,1119-1145` — writer 读写均允许 NaN/Infinity，与严格校验器分叉。  
依据: `/tmp/codex-g32-primary-naninput-ygdocdt8` 以 `exam_board=NaN` 正常输入，writer `rc=0` 并写出字面 `NaN`，validator `rc=1 非标准 JSON 常量`；`/tmp/codex-g32-primary-lex-2z6_9m5q` 的加性 `payload.note: NaN` 也被 writer 重放并推进 attempt。  
建议: 所有输入及账本读取使用拒绝 `parse_constant` 的 strict loader；输出使用 `json.dumps(..., allow_nan=False)`，并在写前递归拒绝非有限浮点数。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:769-772` — 合法 §6.3 同 ID 历史评分行被无条件当成损坏，违反规格 A4.5 的幂等跳过。  
依据: `/tmp/codex-g32-primary-hist-b_584z25` 将已应用事件转成合法历史 payload 后，validator `rc=0`；原样重跑 writer `rc=1`：“账本已有…但缺 review/1 扩展”，节点/账本零改。  
建议: 非 `review/1` 同 ID 行按 `learning-events-schema-v1.md:188,300` 做幂等 no-op；若产品确实要拒，必须修改这两处规格，而不能只改 writer。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:372-393,613-621` — 合法初始 YAML `calibration_log: []` 会被写成非法 YAML，并使两阶段流程永久不收敛。  
依据: `/tmp/codex-g32-primary-inlinecal-jb44utn0` 首次评分 `rc=0`，产物为 `calibration_log: []` 后紧接缩进列表；attempt/W/账本已推进。相同事件重跑 `rc=1`“FSRS 已应用但缺校准记录”，SHA 不变。  
建议: 对 inline 空列表先原子改写成 block list 再插入；其他 inline 形态应可靠解析或在追加账本前 fail-closed。

[MEDIUM] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:586-590,1036-1053` — “正常与恢复逐字节相同”只覆盖账本中的核心评分字段，重试辅助输入仍会改变节点字节。  
依据: `/tmp/codex-g32-primary-bytes-hwa0ofst` 保留 durable 行并回滚节点后，用不同 question/confidence/callout 恢复；账本仍 1 行且 `rc=0`，但节点 `byte_equal=false`，恢复产物出现 q9/.99/重试 callout。  
建议: 要求完整字节等价就把这些辅助字段持久化到 durable payload/envelope；否则把规则 4 收窄为仅保证评分、调度和序数副作用一致。

[MEDIUM] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:815-825` — 历史序数分支不读取已有 `payload.attempt_count`，给出的人工处置也无法通过现有输入表达。  
依据: `/tmp/codex-g32-primary-legacyord-5znev32b` 的后续历史行已含 `attempt_count:2` 且 validator `rc=0`；重跑两次仍同样 `rc=1` 并声称“无 attempt_count”，提示“确认后重跑”但重跑没有确认通道。  
建议: 对合法且可证的历史 `attempt_count` 纳入回推；不可证时提供真正存在的迁移命令、显式确认参数或准确的手工字段清单。

[MEDIUM] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:417-444` — 空行和 BOM 与 `validate_learning_events.py:1560-1579` 的严格文件语法不一致。  
依据: `/tmp/codex-g32-primary-lex-2z6_9m5q` 中物理空行被 writer 忽略并保留，settled `rc=0`，validator `rc=1 LINE 2: 空行`；BOM 首行同样 writer `rc=0`、validator `rc=1`。  
建议: 空行由 writer 拒绝；BOM 若坚持规则 9 的兼容策略，则同步修改规格和 validator 只允许文件字节 0 的单个 BOM，否则删除 writer 的 BOM 特例。

[LOW] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:900-1019` — 规则 11 的“多个 pending 时停下”与实际的“全部恢复、发布、再停下”含义不一致。  
依据: `test_g3_2_review_ledger.py:1983-2007` 实跑第一轮复放两条并非零退出，第二轮 `rc=0`，最终 attempts=`[1,2,3]`；这是可收敛行为。  
建议: 保留实现，规则改成“可证的多个 foreign pending 按序恢复并独立发布，本轮不得追加；本次事件与 foreign pending 混合时才拒绝”。

### 测试复核

在 `backend/` 下按指定环境实际运行：

```text
env PYTHONDONTWRITEBYTECODE=1 INTERNAL_API_KEY=review-placeholder \
NEO4J_ENABLED=false TMPDIR=/tmp/codex-g32-full-20260902 \
.venv/bin/pytest \
tests/regression/test_learning_events_schema_contract.py \
tests/regression/test_fsrs_bridge.py \
tests/regression/test_learning_event_log.py \
tests/regression/test_g3_2_review_ledger.py \
tests/regression/test_fsrs_golden_vectors.py \
-q -p no:cacheprovider --tb=short
```

结果：

```text
collected 272 items
271 passed, 1 skipped, 10 warnings in 47.47s
```

自报的 `272 collected / 271 passed / 1 skipped` 完全一致。

单跑行为文件：

```text
backend/tests/regression/test_g3_2_review_ledger.py
42 passed, 0 skipped, 10 warnings in 45.32s
```

测试全绿没有覆盖上述反例，尤其是：正常新写校准值必须为完整 ID、嵌套 `quiz:` 输入、durable ID 空白、不可用字符串 node_id、末尾换行时间、加性字段 NaN、inline `calibration_log: []`、后续 degraded 序数回推及不同辅助输入的恢复字节等价。

### 验证限制

- 工作树只读；生产代码块原样抽取后仅在 `/tmp` 搭建最小 vault，未修改被复核文件。
- 未运行 `backend/scripts/g32b_mutation_gates.py`，未设置 `DEBUG=true`。
- 未做并发测试，也未把缺锁列为问题；所有 BLOCKER 反例均在单进程串行条件下成立。
- 没有模拟真实断电或内核短写；崩溃窗口通过“保留 durable 行、回滚节点”构造。
- 未跑整个仓库的全部测试，只跑了用户所述 272 项目标组合及 42 项行为文件。
- 未进入真实 Obsidian GUI；验证的是指定 Markdown 中唯一生产 Python 块及真实 `fsrs_bridge`/validator。
- 工作树原有 1 个 modified 和若干 untracked 审查文件，复核前后状态一致，未触碰。
- 当前未暴露 Graphiti 连接器，因此无法执行仓库说明中的 Graphiti 查询；这不影响本地代码、规格和动态反例结论。

VERDICT: 需整改


