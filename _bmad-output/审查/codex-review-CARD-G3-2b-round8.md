结论：需整改

### 26 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | FAIL | `SKILL.md:887-899,1027-1038` 的固定键集与身份快照排除本身正确，但缺稳定时刻时 `:898-899` 直接抄 durable 值，candidate 不再独立。实跑同 ID、无 `review_time`、业务时刻从 8 月改到 12 月仍 `rc=0` 幂等跳过，账本仅 1 行。 |
| 2 | PASS | `SKILL.md:290-317,759-761,831-837`。实跑 `.500Z` 与 `+08:00` 行均 `rc=1`；`Z`、`+00:00` 整秒行可消费。没有归一化坏行。 |
| 3 | FAIL | 主干六格期望值正确，但 `SKILL.md:985-994` 把无 marker 历史 payload 的任意 `out_of_order:true` 当“不推进次数”。实跑正确 E1 `attempt_count=1` 被拒，错误值 `2` 反而 `rc=0`。 |
| 4 | FAIL | 辅助字段不在载荷内的收窄表述是诚实的；但日志锁住的业务时刻仍不一致。稳定时刻 10:00、运行时刻 10:05 时，首写 durable `review_time=10:05`；崩溃恢复重跑 `rc=1 envelope 冲突`。 |
| 5 | PASS | `SKILL.md:759-761,816-830`。缺失/非法 `rating`、`grade_norm` 及评分不自洽均在 apply 前 `rc=1`、节点 SHA 不变；与 validator 结论一致。 |
| 6 | PASS | 裁决确已写入 `docs/learning-events-schema-v1.md:184-201,209-217`；五文件 schema 契约测试通过。另有 manifest 升级自相矛盾，见问题清单。 |
| 7 | PASS | `SKILL.md:462-479,507-512`。实跑 `坏行\n   ` 被视为有终止 LF 的完整坏行并 `rc=1`；无 LF 的真正尾部半行被隔离。 |
| 8 | PASS | `SKILL.md:803-815`。晚于 W 的 `true`、`false`、字符串 `"true"` 均拒绝；早于 W 的布尔 `true` 放行且 W 不受该行推进。 |
| 9 | FAIL（表述） | 字节切行与解码语义正确，但“首行剥 BOM”不真实：`SKILL.md:474-477` 在 `utf-8-sig` 解码 `:483` 之前直接拒绝。实跑 writer/validator 都 `rc=1`。应改规则文字，不改当前拒绝行为。 |
| 10 | PASS | `SKILL.md:499-506`。重复 JSON 键实跑 `rc=1`，错误含“重复键”，节点和账本未变。 |
| 11 | FAIL（表述） | `SKILL.md:1066-1187` 与规格 A2/A9 会顺序恢复多个纯 foreign pending。实跑两条 pending：首轮 `rc=1` 但节点已落定到第二条，`attempt_count=2`、账本仍 2 行，并输出“已恢复 2 个未完成事件”。只有 current 与 foreign 混合才停。 |
| 12 | PASS | `test_g3_2_review_ledger.py:1235-1296` 六格前置和终态均真实，独立探针也得到相同结果；没有靠恒真断言冒充行为验证。但六格缺少稳定时刻/A3 维度。 |
| 13 | PASS | `SKILL.md:727-741`。缺失、`null`、数字、空串、纯空白 `node_id` 均 `rc=1`；合法别节点可跳过。 |
| 14 | PASS | `SKILL.md:1068-1140,1161-1187`。foreign 未应用事件实跑后 mastery、`last_examined`、校准、attempt、FSRS 均按 durable payload 复放；本次事件未在该分支重复算。 |
| 15 | FAIL | 规范化生成的 frontmatter 下不会二次 mastery；但 `_fm_has_event()` 的文本判据 `SKILL.md:411-433` 对合法 YAML 注释头产生假阴性。实跑事件已在 `calibration_log` 中却被判断未应用，续跑永久 `rc=1`。 |
| 16 | PASS | `SKILL.md:848-860` 已在所有幂等早退前扫描。实跑 validator 放行的迟到未标行，writer 在 no-op 前 `rc=1`，节点零改。 |
| 17 | FAIL | `SKILL.md:521-530` 比规格更严。§2:26 冻结 parsed-field 字面相等，§3:40 只要求非空。实跑一条别节点、`event_id=' foreign-history-id '` 的合法历史行：validator `rc=0`，writer `rc=1`，整个 vault 后续评分被阻断。 |
| 18 | PASS | `SKILL.md:759-802`。错误事件类型、`concept_id`、`vault_id` 的本节点 review 行均 `rc=1`；合法非评分事件经过校验后跳过。 |
| 19 | PASS | `SKILL.md:773-793`。`schema_ext="review/01"`、非法 marker 或无 marker 却带 validator 认定的扩展键均不能降级成历史行；真正 §6.3 历史行仍可 no-op。 |
| 20 | FAIL（边界） | `validate_record_full()` 调用顺序 `SKILL.md:717-761` 正确；当前 manifest 下合法历史行未被它误拒。但规则 17 的全账门在路由前阻断合法别节点行，违反 `schema:198` 的节点边界。8 处重复检查不是缺陷：规格 `:196` 已明确它们是同结论纵深。带空白时刻也确实先在 full validator 处 `rc=1`，到不了 `_instant_only().strip()`。 |
| 21 | PASS | `SKILL.md:363-408`。实跑完整/裸形态来源可能同时为 `['quiz:K','quiz:quiz:K']` 时 `rc=1`，未猜测归属；完整 ID 正常命中。 |
| 22 | PASS | `SKILL.md:248-258,1287-1290` 对 `p.ts` 做字面校验并原样写 `recorded_at`。带首尾空白输入实跑 `rc=1`、零写。稳定业务时刻的缺陷属于规则 25。 |
| 23 | PASS | `SKILL.md:928-942,1104-1135` 已删除 W 兜底。降级 A 作为 foreign 恢复后，实跑 attempts 为 `[1,2]`，A 的 mastery 未再次吸收。 |
| 24 | FAIL | `SKILL.md:952-1001` 的普通历史回推可工作，但 markerless `out_of_order:true` 被错误跳过，导致日志真实可证的 E1 序数从 1 算成 2。 |
| 25 | FAIL | Step 3/4 已提供稳定值（`SKILL.md:150-174`），candidate 也读取它，但正常首写仍 `_bridge(..., p["ts"])`（`:1237-1242`）。此外 A3 会把稳定原时刻变成 `W+1s`，当前事件没有持久化二者的绑定。 |
| 26 | FAIL | 普通跨 k 行折算测试通过；但 `SKILL.md:988-989` 对无 marker 历史行错误赋予 `out_of_order` 扩展语义，实际会推进的行未计入 gap。 |

### 六种状态

1. PASS — `dup=F, f1=F`。前置确为账本只有一个 foreign pending、W/本次校准均无；两阶段后 `ledger=2`、`attempt_count=2`、`W=2026-08-02T10:00:00Z`。

2. PASS — `dup=F, f1=T`。账本删掉本次事件但保留其校准，W 与 attempt 已推进；实跑 `rc=0`“旧写序，不补录”，节点 SHA 和账本 1 行均不变。

3. PASS — `dup=T, f1=T, applied=T`。W 等于 durable `review_time`，attempt=1；实跑 `rc=0` 幂等 no-op，节点与账本均不变。

4. PASS — `dup=T, f1=F, applied=T`。只删校准、保留 W/attempt；实跑 `rc=1`“缺校准记录、人工核对”，零写。

5. PASS — `dup=T, f1=T, applied=F`。降级首写后 W 不存在，但 attempt/校准已存在；恢复 `rc=0`，只补 W/FSRS，mastery 与 attempt 逐字不变。

6. PASS — `dup=T, f1=F, applied=F`。模拟 append 后节点未发布；恢复 `rc=0`，账本仍 1 行、attempt=1，节点与直接成功产物逐字节相同。

六格测试本身没有恒真行为断言；失败域是六格之外未纳入的“原始稳定时刻、运行时刻、A3 采用时刻”三者关系。

### 问题清单

[BLOCKER] [SKILL.md:887](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:887) — 稳定业务时刻只用于重试 candidate，正常首写仍使用本次运行时刻，崩溃后永久无法恢复。  
依据: 新卡输入 `review_time=10:00`、`ts=10:05`，首跑 `rc=0`，durable `effective_at/payload.review_time=10:05`。回滚节点模拟 append 后崩溃，再以稳定 10:00、`ts=10:06` 重跑，得到 `rc=1 envelope 冲突`；账本保持 1 行，节点仍无 W，第三次重跑仍相同。即使不回滚节点、只模拟白板尚未置 done，也同样永久冲突。  
建议: durable payload 同时保存“原始稳定 scored_at”和“A3 后实际采用的 review_time”，envelope 比较前者、恢复使用后者；同步修改规格、validator 和测试。不能只把 `:1239` 改成 `p.review_time`。

[BLOCKER] [fsrs_bridge.py:243](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/scripts/fsrs_bridge.py:243) — A3 会改变业务采用时刻，但当前没有可供重试证明原始时刻与采用时刻关系的 durable 信息。  
依据: 初始 `W=10:00`，首跑 `ts=review_time=10:00` 得 `rc=0`，durable `review_time=10:00:01`；同一稳定评分以新运行时刻续跑即 `rc=1 envelope 冲突`。回滚节点模拟崩溃后也无法恢复。  
建议: 将 raw scored time 与 adopted review time 分成两个有明确契约的字段。若 schema 不允许增加该字段，就必须把最终 adopted 值在 append 前持久绑定到可恢复的白板状态；仅凭当前 durable adopted 值无法识别“同一原始评分”与“另一评分”。

[BLOCKER] [SKILL.md:894](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:894) — 缺稳定时刻时回抄 durable 的兼容兜底，使上一轮修复实际失效。  
依据: 第一次无 `review_time`、`ts=2026-08-01` 得 `rc=0`；同 ID、同分数、仍无稳定值但 `ts=2026-12-31` 再跑也得 `rc=0`“已完整应用，幂等跳过”。账本仍 1 行、attempt 仍 1、durable 时刻仍为 8 月。  
建议: 新流程缺稳定值必须 fail-closed。旧白板只能走显式迁移/人工确认的兼容通道，不能以 durable 值替代 candidate 输入。

[HIGH] [SKILL.md:985](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:985) — 无 marker 历史行的未知 `out_of_order` 键被错误赋予 review/1 语义，序数判据正反颠倒。  
依据: 构造 E1(1) → 历史 L2 无 count、payload 含 `out_of_order:true` → 历史 L3(3)。validator `rc=0`。正确 E1 count=1 重跑 `rc=1`；把 E1 错改成 count=2 后反而 `rc=0` 幂等跳过。  
建议: 只有 `schema_ext=="review/1" && out_of_order is True` 才能按不推进 attempt 处理。规格还需明确 `out_of_order` 是否属于“无 marker 即违规”的扩展键，并让 `REVIEW_EXT_KEYS` 与该裁决一致。

[HIGH] [SKILL.md:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:411) — 合法 YAML 注释形态使校准凭据产生假阴性，两阶段续跑永久停住。  
依据: 初始 `calibration_log: # keep this comment` 是合法 YAML。首跑 `rc=0`，解析后列表确实含本事件；同 ID 重跑却 `rc=1`“FSRS 已应用但缺校准记录”，账本仍 1 行且节点不再变化。`calibration_log: [] # comment` 还会被写成非法 YAML，随后同样无法收敛。  
建议: 用结构化 YAML 读取校准记录；写入层至少同时支持带尾注释的 block header 与 inline 空列表，并增加解析后 YAML 有效性验收。

[HIGH] [SKILL.md:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:521) — event_id 空白门单边收紧规格，并让一个合法的别节点历史行阻塞整个 vault。  
依据: 预置别节点合法 §6.3 行，`event_id=' foreign-history-id '`。validator `rc=0`、`RESULT: PASS`；writer `rc=1`，明确报首尾空白，节点与账本 SHA 均不变。规格 §2:26 定义的是字面相等，§3:40 只要求非空。  
建议: 现规格下删除或限缩全账 `_ws_ids` 门。若产品决定禁止空白，先同步升级规格、validator 和全部写点，不能由单个消费者把两个字面 ID 推断成同一事实。

[MEDIUM] [validate_learning_events.py:1435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/scripts/validate_learning_events.py:1435) — “合法库升级不冲突”与“所有旧行必须等于当前单一 manifest”自相矛盾。  
依据: 当前产生的行配当前 manifest 得 `violations=[]`；仅把真值源换成合法形状的新版本 `99.0.0` 与新 hash，同一旧行立刻得到 2 条身份不一致 violation。`SKILL.md:759` 会在 envelope 比较前停止，因此 `schema:186` 排除身份键并不能支持升级。  
建议: 选择其一：明确 manifest 永久不可升级并删除“合法升级”理由；或维护版本化 manifest registry，使历史事件按产生时身份验证。

[MEDIUM] [test_g3_2_review_ledger.py:138](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:138) — 测试数据系统性绕开稳定时刻与 A3 组合，导致 BLOCKER 全绿。  
依据: AST 统计 181 次 `_payload(...)` 调用，只有 11 次显式传 `review_time`；所有首写都令 `review_time==ts`。唯一不同值是 `:2823` 的重试，首写是新卡且两值相等。`:1091-1111` 的 A3 测试又省略稳定值，正好走错误的 durable fallback。  
建议: 增加 fresh `review_time != ts`、append 后崩溃、节点已发布但白板未 done、以及 `review_time==ts<=W` 触发 A3 的组合测试；断言第二轮收敛而非只断言首写。

[LOW] [SKILL.md:474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:474) — 规则 9 和前置注释仍写“首行剥 BOM”，实际行为是拒绝。  
依据: BOM 账本 writer/validator 均 `rc=1`；`:483` 的 `utf-8-sig` 对 BOM 不可达。  
建议: 把规则和 `:457-459` 注释改为“首行 BOM fail-closed”；保留当前实现。

[LOW] [SKILL.md:1152](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1152) — 规则 11 把“current+foreign 混合停止”误写成“多个 pending 一律停止”。  
依据: 两个纯 foreign pending 实跑会全部恢复并落盘；现有 `test_g3_2_review_ledger.py:2007-2031` 也明确要求该行为。  
建议: 改规则文字为“纯 foreign 可按证明序批量恢复；本次事件与 foreign 同处 pending 时停止”。

### 测试复核

按当前 worktree 实际虚拟环境路径运行五个目标：

```text
collected 276 items
275 passed, 1 skipped, 10 warnings in 59.33s
exit code 0
```

与自报的 `276 collected / 275 passed / 1 skipped` 一致。

单独行为文件结果：

```text
collected 46 items
46 passed, 10 warnings in 50.06s
exit code 0
```

唯一 skip 是 `test_learning_events_schema_contract.py:1100-1107::test_repo_vault_ledger_schema_v1`，原因是 worktree 的 `canvas-vault/learning_events.jsonl` 不存在。

六格断言不是恒真；但测试存在明显遮蔽：

- 170/181 个 payload 没有稳定 `review_time`。
- A3 字节一致测试走了错误 fallback。
- round-7 真实续跑测试首写令 `review_time==ts`，且新卡不触发 A3。
- 上一轮四项重点修复中，完整 ID 歧义门与提前全局扫描通过；稳定时刻修复只改了一半；序数 gap 修复对 markerless `out_of_order` 引入了新错误。

两侧口径实测：

- 未发现本节点、真正进入消费路径的 v1 行出现未解释的 writer 放行 / validator 拒绝；`validate_record_full()` 前置有效。
- validator 放行 / writer 拒绝中，缺 attempt、非 UTC、迟到未校准等是规格明确的消费侧加严。
- 非预期分叉是：合法空白 event_id、markerless 历史 `out_of_order` 的序数解释，以及未来 manifest 升级。
- 8 处重复字段检查结论与 validator 一致，不构成实现缺陷；规格 `§6.2 A8` 已诚实写成“功能重合的纵深”。不建议仅为措辞删掉；长期可抽取共享纯函数以降低漂移风险。
- `_instant_only().strip()` 当前确实到不了：本节点带空白时刻先在 `validate_record_full()` 得 `rc=1`；别节点不会调用它。

### 验证限制

- worktree 根没有 `.venv/bin/pytest`，照字面运行得到 `rc=127`；改用实际的 `backend/.venv/bin/pytest`。
- 仓库保持只读；所有反例在 `/private/tmp` 的隔离最小 vault 中运行，没有改真实 vault 或现有脏文件。
- 没有设置 `DEBUG=true`，没有运行被禁止的 `g32b_mutation_gates.py`。
- 未测试并发；结论仅针对规格指定的单进程串行前提。
- 未连接 Neo4j、网络或真实 Obsidian UI。白板保持 pending 的判断依据是生产块退出码、payload 保留行为和 Step 4d 控制流。
- manifest 升级项是对真实校验函数注入“未来合法 manifest”的确定性实验，不代表当前仓库已经升级。

VERDICT: 需整改


