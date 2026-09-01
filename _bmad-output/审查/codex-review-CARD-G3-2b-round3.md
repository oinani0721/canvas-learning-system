结论：需整改

以下反例绑定到未变异主程序 SHA-256 `41ef618ba2386e596decd395f2f744369a2b90b552031991115981ffb464c656`。已确认至少两条单进程路径会漏掉评分副作用。

### 13 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | FAIL | [SKILL.md:581–634](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:581) 确实独立构造固定 payload 八键并排除两个 FSRS 身份键。实测 `1`/`1.0`/`"1"`/`true` 分别序列化为不同文本，NFC/NFD 也不同；但 Python 接受并重新输出 `NaN`，两侧 `exam_board=NaN` 可通过 envelope，writer `rc=0`、validator `rc=1`。`effective_at != review_time` 在 duplicate 路径会冲突，但 foreign pending 绕过 envelope 后仍被应用。 |
| 2 | FAIL | [SKILL.md:236–263](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:236) 在正则和解析前调用 `strip()`。持久行 `review_time=" 2026-08-01T10:00:00Z "` 实测 writer `rc=0` 并重放，validator `rc=1`，违反“不归一化”。别节点的小数秒、非 UTC、坏 rating 未卡当前节点，说明按节点缩窄本身正确。 |
| 3 | FAIL | [SKILL.md:598–634](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:598) 仍从 frontmatter 读取 `_att_now`，再减 `_after_applied`。E1/E2 后仅删除当前 `attempt_count`，重跑 E1 得 `rc=1 envelope 冲突`；合法、已计入 frontmatter 的旧格式行夹在 E1/E2 中间也会使 E1 重跑 `rc=1`。合法 `out_of_order` 夹行可 no-op，但不能挽救前两种组合。 |
| 4 | FAIL | [SKILL.md:476–478](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:476)、[SKILL.md:647–711](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:647)。普通单事件恢复在新卡、Review、Learning、A3 `W+1s`、长间隔、弃答下字节一致；但 degraded 已写 EMA 后恢复：新卡 direct `5fccc4dc…`、recover `c93162b5…`；Review+A3 direct `b3e6c261…`、recover `8d2be44…`。更严重的是 A pending 后答 B：直接路径 `mastery=0.61/a=2.6211/b=1.6756/cal=[A,B]`，恢复路径 `0.57/2.1/1.6/cal=[B]`。 |
| 5 | PASS | [fsrs_bridge.py:195–212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/scripts/fsrs_bridge.py:195)。`grade_norm=.75, rating=4` 实测 `rc=1`、节点零写。无 marker 的 §6.3 历史行不进入此门，作为旁行时新评分 `rc=0`、账本两行。合法历史同 ID 被拒是另一处分诊问题，不是 rating 等式造成。 |
| 6 | 部分通过 | [schema §6.2:184–195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:184) 已写入 envelope、排除键、独立 candidate 和整秒消费门；但 [§6.2:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:197) 的“`≤W` 歧义对 exactly-once 无影响”被同秒反例推翻，规格本身需改。 |
| 7 | PASS | [SKILL.md:345–376](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:345)。九案实测符合：坏行无 LF `rc=0` 隔离；带 LF/CRLF `rc=1`；`坏行\n空白无LF` 仍 `rc=1`；唯一坏行无 LF `rc=0`、有 LF `rc=1`。 |
| 8 | PASS | [SKILL.md:536–548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:536)。`false`、`"true"`、`1`、对象均 `rc=1`；布尔 `true` 且时间晚于 W 也 `rc=1`；合法 `review_time≤W` 的补录行放行且不推进 W。 |
| 9 | FAIL | [SKILL.md:345–362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:345) 的确二进制读取并显式 decode；完整行或中间行非 UTF-8 均 `rc=1`。但“唯一非 UTF-8 行且无 LF”被当作多字节截断尾行，实测 `rc=0`。若这是预期截断自愈，须把该例外写入规则9/规格；否则实现应停下。 |
| 10 | PASS | [SKILL.md:265–276](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:265)、[SKILL.md:363–370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:363)。payload 重复 `grade_norm`、顶层重复 `node_id` 均 `rc=1`、节点和账本原样；`object_pairs_hook` 对嵌套对象同样生效。 |
| 11 | FAIL | [SKILL.md:608–622](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:608) 只在“当前事件是 duplicate 且它之前还有 pending”时守卫。预置 A/B 两条 pending 后写新 C，实测 `rc=0`、重放两条、账本 attempts `[1,2,3]`。连续两次在发布前崩溃即可在单进程下产生该状态，并非只可能外部篡改。 |
| 12 | FAIL | [test_g3_2_review_ledger.py:1148–1227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1148) 六格的分支前置条件属实；`_strip_calibration` 独立对拍仅删除 `calibration_log`，`changed_common=[]`。但格1只断言 FSRS/W，漏验 mastery/calibration；格5未对拍完整 bytes。另有测试把缺计数字段的合法重跑 `rc=1` 和同刻双重放锁成正确行为。 |
| 13 | FAIL | [schema:14–16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:14) 要求任何版本缺可用 `node_id` 的读方 fail-closed；实现 [SKILL.md:520–524](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:520) 却直接跳过。缺 `node_id` 行后写新评分：writer `rc=0`、validator `rc=1`。同时把 `node_id` 和 `concept_id` 都写成同一个不存在值时，validator 实测 `rc=0`，所以“写错一定拦下”也表述过宽。 |

### 六种状态

| 状态 | 结论 | 实际前置与观测 |
|---|---|---|
| 1. `dup=无 / 笔记未记录 / W无` | FAIL | 前置真实，且有一条 foreign pending。writer `rc=0`、账本两行、W 正确；但 pending A 的 mastery/calibration 未恢复。直接 A→B 为 `mastery=0.61`、校准 `[A,B]`，崩溃后恢复为 `0.57`、校准仅 `[B]`。 |
| 2. `dup=无 / 笔记已记录` | PASS | `f1=True、W=08-02`；重跑 `rc=0`，输出“旧写序/不补录”，节点与账本零改。 |
| 3. `dup=有 / 笔记已记录 / 时刻≤W` | PASS | `rc=0` 幂等 no-op；节点 bytes 不变，账本保持一行。 |
| 4. `dup=有 / 笔记未记录 / 时刻≤W` | PASS | `_strip_calibration` 未改 FSRS、attempt、last_examined 或正文；重跑 `rc=1`、要求人工核对、零写。 |
| 5. `dup=有 / 笔记已记录 / W无` | FAIL | degraded 恢复确实只补 FSRS、未二次吸收 EMA；但完整节点 bytes 与直接成功不同：`5fccc4dc… != c93162b5…`，违反规则4。 |
| 6. `dup=有 / 笔记未记录 / W无` | PASS | 标准崩溃窗口全套恢复，账本仍一行；新卡、Review、Learning、弃答、长间隔及 A3 `W+1s` 对拍均 `rc=0` 且节点 SHA 相同。 |

### 问题清单

[BLOCKER] [schema:155–163、197–202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:155) / [SKILL.md:647–652](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:647) — 已到 W 的同秒未标行会被永久漏算。  
依据: 正常写 E1@10:00 得 W=10:00；外部追加同节点 E2@10:00/attempt2，validator `rc=0`；再写 E3，writer `rc=0`、无 E2 重放、账本 attempts=`[1,2,2]`。  
建议: 先改规格 §6.2 的“歧义无影响”结论；对同节点、未标 `out_of_order` 的 review/1 行按物理行序强制业务时刻严格递增，重复/回退时 fail-closed。相应反转测试 `:1402–1412`。

[BLOCKER] [SKILL.md:647–680](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:647) — A2 只恢复 FSRS/attempt，普通崩溃会漏掉该评分的 mastery/calibration。  
依据: A 已落账未发布，下一次答 B；writer `rc=0`。FSRS 六字段、attempt 均与直接 A→B 相同，但直接节点为 `mastery=0.61/a=2.6211/b=1.6756/cal=[A,B]`，恢复节点为 `0.57/2.1/1.6/cal=[B]`。  
建议: review/1 durable payload 必须携带恢复所有节点副作用所需的事实，并在 A2 逐项重放；否则先原子发布 A2 恢复结果，再允许追加 B。新增整节点 bytes 对拍，不只比 FSRS。

[BLOCKER] [SKILL.md:608–652](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:608) — 多 pending 守卫只覆盖一种 duplicate 排列。  
依据: A/B 两 pending 后写新 C，`rc=0`、重放数 2、账本 `[1,2,3]`；正常 A/B/C mastery 为约 `0.64`、校准三条，当前结果 mastery `0.57`、校准仅 C。  
建议: 若坚持规则11，在任何 bridge/apply 前统一检查 `len(pending)>1`；更根本地，A2 重放后先发布并 fsync 恢复状态，再追加新事件。否则就须修改规则11，设计可证明的任意 pending 折叠。

[BLOCKER] [schema §6.1:94–108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:94) / [SKILL.md:549–561、674–679](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:549) — `attempt_count` 缺失/非法仍可消费，且规格、校验器也未把它列为必填。  
依据: current-node pending 删除 `payload.attempt_count` 后，writer `rc=0`、validator `rc=0`；随后账本 attempts=`[null,1]`，两次评分但笔记计数仅 1。任意过大值也可成为后续权威基数。  
建议: §6.1 增加正整数、非 bool 的 `attempt_count` 契约；validator 与消费侧在 apply 前校验，并按账本边界验证其序数，不能静默跳过同步。

[HIGH] [SKILL.md:598–634](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:598) — 序数仍依赖当前 frontmatter，合法历史重跑会被误判冲突。  
依据: E1/E2 均完整应用，仅删除笔记当前 `attempt_count`，重跑 E1 `rc=1`；E1→已计入 frontmatter 的合法 legacy 行→E2 后重跑 E1 同样 `rc=1`。节点零写但用户无法合法重跑。  
建议: 从账本物理边界和所有会占用序数的合法行独立复算；若历史账本不足以证明，则规格必须明确 fail-closed，而不能继续宣称“不取笔记当前值”。

[HIGH] [SKILL.md:518–561](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:518) — 适用集消费前未完成版本与两时刻一致性门。  
依据: `event_version=2` 的行 validator `rc=0 + WARN`，writer 却 `rc=0` 并输出“A2 重放已应用”；`effective_at=11:00、review_time=10:00` 的 v1 行 writer `rc=0`、validator `rc=1`。  
建议: 路由后先判断版本；未知版本只能跳过并冻结/告警，绝不能按 v1 apply。v1 行须在进入 pending 前验证 `effective_at` 与 `review_time` 为同一绝对瞬间及完整必填形状。

[HIGH] [schema:14–16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:14) / [test:1478–1497](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1478) — 缺 `node_id` 被 writer 静默跳过，测试还把该违约锁成正确。  
依据: 缺 `node_id` 行后运行新评分，writer `rc=0`、节点推进、账本两行；validator 才 `rc=1`。这与规格“任何版本不可路由即 fail-closed”直接冲突。  
建议: 账本扫描阶段对缺失、空值、非字符串 `node_id` 全局 fail-closed；修改测试，不得假定 validator 必然先于写点运行。

[MEDIUM] [SKILL.md:476–478、694–711](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:476) — degraded 恢复与直接成功只因 YAML 键顺序而字节不等。  
依据: 两组 direct/recover SHA 分别为 `5fccc4dc…/c93162b5…`、`b3e6c261…/8d2be44…`；业务字段和账本行数相同。  
建议: 用统一 canonical frontmatter renderer，或明确一个固定插入顺序；把 degraded 已应用后恢复纳入整节点 bytes 测试。

[MEDIUM] [SKILL.md:236–263、363–364](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:236) — canonical/严格 JSON 门仍可放行空白时刻和 `NaN`。  
依据: 空白包裹时间 writer `rc=0`、validator `rc=1`；durable/input 都含 `NaN` 时 envelope 文本相等并恢复，validator `rc=1`。  
建议: 对原字符串直接正则/fullmatch，不调用 `strip()`；`json.loads(..., parse_constant=reject)`，所有 `json.dumps` 使用 `allow_nan=False`，并补字段类型门。

[MEDIUM] [SKILL.md:573–576](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:573) — 同 event_id 的合法无-marker 历史行永远报错。  
依据: validator `rc=0` 的 §6.3 历史行及已含 W/calibration 的节点，原样重跑得到 writer `rc=1`；节点、账本虽零改，但违反“永久合法、视为已应用”。  
建议: 有可靠 `f1`/旧写序证据时 no-op；证据缺失时才 fail-closed，并为历史同 ID 增加字节 fixture。

[LOW] [learning_event_log.py:87–115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/app/services/learning_event_log.py:87) / [schema:26、181、305](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:26) — 规格仍把通用入口描述成子串查重，已与代码事实过时。  
依据: `git diff 02dbc426..HEAD -- learning_event_log.py` 退出码 0，说明本轮没改；该文件在前一轮已采用 parsed equality。预置 payload 文本含 `"target"` 后调用 `event_id="target"`，返回 `True`，最终 IDs=`["other","target"]`。  
建议: 本轮无需改 `learning_event_log.py`，也不应给通用入口套 review/1 envelope/rating 门；只需更新规格现状/债务注记。

### 测试复核

实跑结果与自报数字一致：

- 行为文件：`36 collected / 36 passed / exit 0`，10 条第三方弃用 warning。
- 五文件裁判：`266 collected / 265 passed / 1 skipped / exit 0`，10 条 warning。
- skipped 项是工作树没有 live `learning_events.jsonl` 快照。
- 未设置 `DEBUG=true`。

绿色测试不能支持通过结论：

- [test:1167–1174](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1167) 只检查 foreign pending 的 FSRS/W，漏验 mastery/calibration。
- [test:1386–1400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1386) 把合法旧评分的 `rc=1` 锁成正确。
- [test:1402–1412](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1402) 要求两条同刻 pending 都重放；第二条实际由 bridge 从 durable `10:00:00Z` 推进成 W=`10:00:01Z`，违反 A6 的同一瞬间要求。
- [test:1482–1497](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:1482) 明确期待缺 `node_id` 的行被 writer 放过，与规格路由信封条款冲突。

### 验证限制

- 所有自构造写入位于 `/tmp/card-w7-ledger-audit.TaHQWs`；未改被复核文件，也未清理用户已有 dirty/untracked 状态。
- 本次复核没有运行被禁止的 `backend/scripts/g32b_mutation_gates.py`。但审查期间另一个独立会话确实运行了它并周期性改写源码；其退出后工作树仍含一个 `MUTANT`，主文件哈希继续变化。因此反例统一绑定到我在变异间隙前后核对一致的未变异 SHA `41ef618b…`，没有把残留 mutant 当成生产实现。
- pytest 数字是在后续外部污染前取得；污染后没有再次运行，以免把临时 mutant 的结果冒充最终结果。
- 崩溃窗口通过预置 durable 行/旧节点模拟；没有做真实断电、文件系统缓存丢失或硬件故障实验。
- 按要求未把并发锁缺失列为问题；多 pending 反例使用的是单进程、连续两次崩溃可达路径。
- `node_id` 与 `concept_id` 同时写成不存在值是否应被拒，当前 §6.1 没有“节点必须存在”的契约；只能判定规则13的“写错必拦”表述过宽，不能凭空要求实现做存在性绑定。

VERDICT: 需整改


