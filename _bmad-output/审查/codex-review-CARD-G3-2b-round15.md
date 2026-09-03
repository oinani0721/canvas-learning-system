结论：需整改

### 33 条规则逐条判断（第 20/21/33 条已按本轮改动重写，见上）

以下行号均绑定 commit `9371d8a2`。表中的“套件 PASS”指隔离快照实跑的 `311 passed / 1 skipped`。

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | PARTIAL | `SKILL.md:1671-1693` 的 candidate 键集独立构造且排除了两个 FSRS 环境键；但 `.499/rating=2` 合法 durable 以相同原值重跑，validator `rc=0`、writer `rc=1 envelope 冲突`，说明等价面仍未闭合。 |
| 2 | PASS | `SKILL.md:350-377` 对 durable `review_time` 强制整秒、UTC、拒而不洗；`test_r2_non_whole_second...:1052` 在套件中 PASS。 |
| 3 | PARTIAL | dup 分支的账本边界回推在 `SKILL.md:1501-1612` 基本正确；F1-only 在 `:1394-1408` 一见任何 §6.3 行就停。我构造可证后继历史行 `attempt_count=2`，validator `rc=0`、writer `rc=1`。 |
| 4 | FAIL | current-dup 恢复 `SKILL.md:1905-1933` 没把 durable grade 传给 mastery/receipt。实跑 `.752`：首次恢复 `rc=0`，ledger=`.752`、receipt=`.75`；同输入再跑 `rc=1`。 |
| 5 | PASS | `SKILL.md:1265-1290` 及 validator `:1363-1433` 在应用前检查 rating/grade 完整性与自洽；对应 `test_r5...:1153` PASS。 |
| 6 | FAIL | `docs/learning-events-schema-v1.md:94-108` 的 REQUIRED 清单无 `scored_at`，`:190` 仍是旧崩溃窗口径。实跑缺字段行 validator `rc=0`、writer `rc=1`，没有完成规格回写。 |
| 7 | PASS | `SKILL.md:804-856` 用最后非空字节行的 LF 状态区分截断；`test_truncated...:398`、`test_r7...:1176` PASS。 |
| 8 | PASS | `SKILL.md:1252-1264` 只接受布尔 `true` 并要求时刻不晚于 W；round-1 N1 行为门 PASS。 |
| 9 | PARTIAL | 按字节切行、逐行解码和截断容忍正确；但 `SKILL.md:818-827` 是先拒 BOM，绝非“首行剥 BOM”。行为与 validator 一致，应改规则文字。 |
| 10 | PASS | `SKILL.md:394-400,843-850` 拒重复 JSON 键；对应门在套件中 PASS。 |
| 11 | FAIL | `SKILL.md:1743-1856` 会依次重放多条 foreign pending；实跑两条后已写 `attempt=2`、W=`10:00:01Z`，再以恢复信号 `rc=1` 退出，并非多条即零写停下。规格 A2 也要求重放至空。 |
| 12 | PARTIAL | `test_g3_2_review_ledger.py:1271-1335` 六个 fixture 前置均真实且全部 PASS；但 `:3949-3969` 自己又定义了第七个可达状态，且还遗漏了“后继 W 假覆盖旧 degraded 事件”的不可区分世界。 |
| 13 | PASS | `SKILL.md:1174-1200` 在路由前拦顶层非 object、不可用 `node_id` 和本节点坏 payload；相关 parity 门 PASS。 |
| 14 | PASS | foreign replay 在 `SKILL.md:1825-1855` 复放 durable mastery、时间、校准和次数，本次 dup 排除；对应恢复测试 PASS。 |
| 15 | PASS | `SKILL.md:1819-1829,1916-1922` 先判断 receipt，再决定是否重算 mastery；六格 degraded fixture 证明 EMA/attempt 没有二次吸收。 |
| 16 | PASS | `SKILL.md:1334-1344` 对 `review_time≤W`、无乱序标记、无 receipt 的行 fail-closed；相关晚行事实门 PASS。 |
| 17 | PASS | 输入和本节点 durable ID 的空白分别在 `SKILL.md:211-220,865-889` 拒绝；其他节点不越权阻塞。对应门 PASS。 |
| 18 | PASS | `SKILL.md:1220,1248-1251` 及前置完整 validator 校验限制事件类型、concept 和 vault；三个 narrow 门 `:3673-3687` PASS。 |
| 19 | PASS | `SKILL.md:1222-1241` 对非法 marker/已登记扩展键 fail-closed；但 `scored_at` 没登记造成的旁路见规则 20。 |
| 20 | FAIL | `SKILL.md:1201-1210` 确实先调用 validator；但 `validate_learning_events.py:1218-1230` 的扩展键集合漏 `scored_at`。实跑删 marker 和六个旧扩展键、保留 `scored_at` 的真实评分行：validator `rc=0`、writer `rc=0` 跳过，attempts 最终为 `[1,1]`，旧评分永久未应用。 |
| 21 | FAIL | `SKILL.md:441-478` 只在候选侧排除了 full→bare；`:717-723` 的来源反查仍错误解释 exact full。实跑两个合法完整 ID `quiz:K`、`quiz:quiz:K` 后重跑前者，writer `rc=1`，错误来源集合为 `['quiz:quiz:K']`。 |
| 22 | PASS | `SKILL.md:275-285` 对输入时刻按 validator 正则字面校验、不 strip；相关 input literal 门 PASS。 |
| 23 | PASS | `SKILL.md:1819-1824,1845-1851` 以 receipt presence 判次数是否已应用，不以 W 代替；六格 degraded 用例 PASS。 |
| 24 | PARTIAL | dup 路径 `SKILL.md:1542-1588` 能利用后继自身序数；F1-only `:1394-1408` 未复用这套证明，实际把带 `attempt_count=2` 的可证历史后继一律拒绝。 |
| 25 | PASS | `SKILL.md:1474-1480,2013-2027` 的比较时刻取稳定输入 `scored_at`，不是本次运行时刻或 durable adopted 值；round-8 稳定时刻门 PASS。 |
| 26 | PARTIAL | dup 的 gap 折算在 `SKILL.md:1559-1588` 正确；F1-only 对历史行 blanket stop，未完成同口径折算。 |
| 27 | PARTIAL | 三时刻职责已在 `SKILL.md:2013-2027` 分开，缺 raw 时消费端拒绝；但规格未同步，且 adopted 合法集合仍放宽错误。 |
| 28 | PASS | 无 marker 历史行的 `out_of_order` 不参与契约语义见 `SKILL.md:1569-1575`；receipt 走真正 YAML 解析 `:727-735`；对应 YAML/序数门 PASS。 |
| 29 | PASS | 全账 ID 唯一性 `SKILL.md:857-897`、append 前自检 `:2060-2069`、YAML receipt 解析均存在；对应门 PASS。 |
| 30 | PARTIAL | `_FACT_KEYS` 与统一 resolver 在 `SKILL.md:495,562-683` 会检查完整 ID、原始时刻、序数、分数等；但合法 JSON 数值、null/bool 和 F1 水位线假证明均使“逐项严格绑定”不闭合。 |
| 31 | PARTIAL | 六处归属统一与冻结事实清单已实现；但 exact/full 来源反查和 JSON number 比较仍分别误拒合法输入。 |
| 32 | FAIL | 有日志时三方 adopted 绑定在 `SKILL.md:667-682`；无日志时 `:1431-1445` 仅以 `W≥receipt.ts` 假证明完整应用。另 `:314-327,1752-1785` 的 adopted 集合和滚动 W 都错误。 |
| 33 | PASS（结构） | 两个调用方确实共用 `_cands_and_sources()`（`SKILL.md:441-478,579,709`），严格度差异也在 `:712-716` 明示；但共享实现本身仍有规则 21 的来源语义错误。 |

### 六种状态

现有六格测试的 fixture 和断言本身都成立：

| 状态 | 结果 | 依据 |
|---|---|---|
| ① `L=0/F1=0` | PASS | `test:1272-1279`：先恢复 foreign，再重跑写新事件；最终 ledger=2、W=`2026-08-02T10:00:00Z`。 |
| ② `L=0/F1=1/W覆盖` | PASS（仅该 fixture） | `test:1281-1290`：真实已应用旧写序孤儿被正确 no-op，节点 SHA 不变。 |
| ③ `L=1/F1=1/W覆盖` | PASS | `test:1292-1299`：完整事件原样重跑，ledger 保持 1 行、节点 SHA 不变。 |
| ④ `L=1/F1=0/W覆盖` | PASS | `test:1301-1307`：缺 receipt 时定向拒绝，节点和 ledger 零写。 |
| ⑤ `L=1/F1=1/W未覆盖` | PASS | `test:1309-1323`：degraded 重试只补 FSRS，EMA/attempt 逐字段不变。 |
| ⑥ `L=1/F1=0/W未覆盖` | PASS（仅两位小数 fixture） | `test:1325-1335`：`.75` 恢复与正常产物逐字节相同；但我的 `.752` 反例首次恢复后 ledger/receipt 已分叉，第二跑 `rc=1`。 |

“六格闭合”的总体判断仍为 FAIL：

- 状态②把两个字节上可达、业务含义相反的世界混在一起：真正已应用的旧写序孤儿，以及“degraded E1 → 删 E1 日志 → E2 抬高 W”。后者被错误 no-op。
- 测试本身另有第七格 `L=0/F1=1/W未覆盖`（`test:3949-3969`），所以“状态空间只有六格”的注释已过期。
- 82 个行为测试共有 760 个 `assert`，无字面 `assert True/False`。但 `test:2461-2465` 仍是弱门：任意非零退出均可通过，没有约束拒因和零写。

### 问题清单

[BLOCKER] `backend/scripts/validate_learning_events.py:1218-1230` / `canvas-vault/.claude/skills/quiz-answer/SKILL.md:1222-1242` — `scored_at` 未纳入扩展行识别，损坏行可伪装成 §6.3 历史行并永久漏算。  
依据: 从合法 pending E1 删除 `schema_ext/vault_id/concept_id/rating/review_time/fsrs_library_version/fsrs_params_hash`，保留 `scored_at/grade_norm/exam_board/attempt_count`；validator `rc=0`。随后写 E2 得 writer `rc=0`，ledger attempts=`[1,1]`、W 只等于 E2、receipt 只有 E2；E1 从未应用。同 ID 重跑还会在 `SKILL.md:1460-1469` 作为历史行 no-op。  
建议: 把 `scored_at` 同时加入规格 §6.1 REQUIRED、validator `REVIEW_EXT_KEYS` 和类型校验；配套正式旧账迁移。它是新写点独有键，不应继续被当成历史自由字段。

[BLOCKER] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:1431-1445` — `W ≥ receipt.ts` 不能证明特定事件已经进入 FSRS，后继事件可以制造假覆盖。  
依据: E1 走 degraded 后删除其日志行；E2 正常落账；重跑 E1 得 `rc=0`、“已完整应用，幂等跳过”，且 FSRS 字段完全不变。损坏链最终为 `state=1, stability=2.3065`；正常 E1→E2 对照为 `state=2, stability=7.3153`。E1 的调度贡献永久漏了一次。  
建议: receipt 增加与 frontmatter 原子发布绑定的事件级 `fsrs_applied`/post-state lineage；degraded 写 false、成功恢复原子改 true。旧 receipt 没有该证明时应 fail-closed 或从完整事件链重建，不能用全局 W 猜。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:314-327,1752-1785` — adopted 合法集合太宽，滚动基线也没有跟随 bridge 的真实采用时刻。  
依据: 两条 foreign pending 均记 `scored_at=review_time=T`。validator `rc=0`；恢复阶段消费两条后 W=`T+1s`，但两行 ledger 和两条 receipt 的采用时刻仍全为 `T`。这违反规格 `docs/...:152,160-164` 的 A3/A6。  
建议: 合法值只有 `_adopted_from(scored_at, rolling_W)`，不存在第三值；当 plain 与 pushed 不同时，plain 不合法。bridge 后断言 `_out["review_time"]` 与 durable 值一致，并以 `_out["fsrs_last_review"]` 滚动。`test:4390-4404` 的“未实施 A3 的外部合法行”oracle 应改掉。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:1156-1159,1676-1693,1922-1933` — 多位小数版本规则只替换了 candidate grade，没有贯穿 rating、mastery、receipt 和 F1-only。  
依据: `.499/rating=2` durable：validator `rc=0`，同原值重跑却因 candidate rating=3 得 writer `rc=1`。`.752` current-dup：首次恢复 `rc=0`，但 receipt 写 `.75`；第二跑 `rc=1 grade_norm 0.75 != 0.752`。  
建议: 先确定唯一 `chosen_grade`，再由它计算 rating，并把它显式传入 mastery、receipt、F1 facts 和 envelope；不要任何分支回落全局 `GN2`。条件本身没有“用户随便给个原值即可别名”的漏洞，因为原值仍须精确等于 durable 且其他事实全部绑定。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:441-478,717-723` — B① 只修了候选解释，来源反查仍把 exact full receipt 当成其他 ID 的历史 bare 来源。  
依据: 正常写本地 `K`，删其 ledger；再正常写不同本地 ID `quiz:K`；最后原样重跑 `K`。前两次均 `rc=0`，receipts 分别为 `quiz:K/full`、`quiz:quiz:K/full`；第三次 `rc=1`，错误来源集合 `['quiz:quiz:K']`。  
建议: 候选不能只返回字符串；应携带 `exact`/`legacy-bare` 解释类型。`exact + id_form:full` 只能贡献自身 exact source。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:513-524,1693` — Python `json.dumps` 不是满足当前合法输入域的 JSON number canonical 比较。  
依据: 我把已应用事件的 ledger/receipt 同步改成合法数值整数 `1`，validator `rc=0`；以同 ID、`grade_norm=1.0` 重跑，writer `rc=1 envelope 冲突`。`0.75/0.750` 解析后相同，字典键序因 `sort_keys` 相同；bool/number 可以区分；但 `1/1.0`、`-0.0/0` 会误拒。  
建议: 同步修改规格 `docs/...:184` 与实现：bool 单独分型，有限 JSON number 用无损十进制数值语义比较。不要递归 `float()`，否则 `9007199254740992` 与 `9007199254740993` 会塌成同值。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:500-528,656-665,2030` — writer 能自产合法 `exam_board:null/true`，下一次却拒绝自己的产物。  
依据: 对 null 与 true，首次写均 `rc=0`、validator `rc=0`；相同输入重跑均 `rc=1`，分别报 receipt 类型非法 `None`/`True`。  
建议: 按当前未冻结类型的规格，保留显式 null，missing 才使用 sentinel，并对所有 JSON 类型做无损 canonical 比较；若产品决定只准字符串，则必须在规格、validator 和首次 append 前同时收紧，不能先写后拒。

[HIGH] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:1394-1408` — 上轮 HIGH① 未闭合：F1-only 看见任何 §6.3 行就停，不尝试利用其可证序数。  
依据: 先完整应用 E1/E2，再保留合法历史 E2（`attempt_count=2`）并删除 E1 日志；目标 receipt 显示 E1 attempt=1，E2 时刻更晚且自身序数可证。validator `rc=0`，writer 仍 `rc=1` 称贡献不可证。  
建议: F1-only 复用 dup 分支 `SKILL.md:1542-1588` 的“最近后继证明行 + gap 折算”；只有确有无序数间隙时才停。

[MEDIUM] `docs/learning-events-schema-v1.md:25,94-108,184-190` / `canvas-vault/.claude/skills/quiz-answer/SKILL.md:1297-1305` — 缺 `scored_at` fail-closed 的安全取舍可以成立，但当前范围过宽且没有规格/迁移闭环。  
依据: 已完整应用的 E1 只删除 ledger `scored_at`，validator `rc=0`；提交无关 E2 时 writer `rc=1`、节点零写。错误信息要求直接修改 append-only JSONL，与规格“只追加不改写”冲突。  
建议: pending/current-dup 等真正需要原始时刻的行缺字段必须拒，这个反转正确；已 settled 且与当前无关的旧行不必一刀切。若产品坚持“全库先迁移”，必须先写入规格，并提供备份、哈希和审计留痕的一次性迁移例外，而不是指导手改历史行。

[MEDIUM] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:195-203` — 非有限评分输入会被静默洗成另一档评分。  
依据: 分别输入字符串 `NaN/Infinity/-Infinity`，三次均 `rc=0`；落账值依次为 `1.0/1.0/0.0`，rating=`4/4/1`。账本字面 NaN/Infinity 会被拒，问题发生在入口钳制之前。  
建议: 在 `float()` 后、clamp 前用 `math.isfinite()` 明拒；同时拒 bool 和非约定输入类型。

[MEDIUM] `backend/scripts/g32b_mutation_gates.py:1577-1629` — 空变异对照脚本不能证明“假杀 0”。  
依据: 静态计数确为 119 个唯一变异、24 条带层；但脚本只把 `rc==1 && 1 failed` 当红，`rc=2/3/4/5` 会在 `:1621-1622` 被打印成“对照绿”。depth 层单独已红时，只要首个失败断言不同也算通过。  
建议: 所有“绿”必须严格要求 `rc==0`；要宣称非层贡献，layer-only 必须独立为绿，或把粗门拆成单场景门。

关于另外三个点：

- 八处重复字段检查不是实现缺陷。规格 `docs/...:201-202` 已明确它们是与 validator 同结论的纵深复核；保留比删除更合理，必要时只抽共享 helper。
- `_instant_only().strip()` 对 durable ledger 时刻确实到不了：`validate_record_full()` 更早按字面拒空白；receipt `ts` 在 `SKILL.md:671-673` 另有显式空白门。未发现洗值穿透。
- “正常与恢复逐字节相同”缩窄到日志锁定量，关于 `question_id` 等辅助输入的表述是诚实的；但 `.752` 反例证明当前实现连日志锁住的分数都没有贯穿恢复，因此该承诺现在仍不成立。

### 测试复核

在 `/tmp/codex-g32-r13.lvZ5Ww/repo` 的 `9371d8a2` 归档快照中实跑：

```bash
env PYTHONDONTWRITEBYTECODE=1 INTERNAL_API_KEY=review-placeholder \
  NEO4J_ENABLED=false TMPDIR=/tmp/codex-g32-r13.lvZ5Ww/pytest-tmp \
  ./backend/.venv/bin/pytest \
  backend/tests/regression/test_learning_events_schema_contract.py \
  backend/tests/regression/test_fsrs_bridge.py \
  backend/tests/regression/test_learning_event_log.py \
  backend/tests/regression/test_g3_2_review_ledger.py \
  backend/tests/regression/test_fsrs_golden_vectors.py \
  -q -p no:cacheprovider --tb=short
```

实际结果：`311 passed, 1 skipped, 10 warnings in 85.98s`，exit `0`。与自报数字一致。唯一 skip 是 `test_learning_events_schema_contract.py:1104-1111`，原因是 worktree 无仓内 live ledger。

测试缺口：

- `test:4390-4404` 把违反 A2/A3 的同秒第二条 pending 当成“外部合法行”，oracle 错。
- `test:4415-4426` 只同步修改已应用 ledger/receipt，没有测试真实 `.752` current-dup 恢复和第二次扫描。
- `test:4218-4251` 验证第二个完整 ID 能写入，却没有再回头重跑第一个 ID，漏掉来源反查误拒。
- 第七状态门只测 W 未覆盖；没有测 degraded 行删除后被后继 W 假覆盖。
- 未运行 mutation gate；因此不确认“119/119 KILLED、假杀 0、24 空对照”执行结果。静态结构计数匹配，但当前判定逻辑不足以证明该声明。

### 验证限制

- 复核期间共享工作树被另一会话改动了 `SKILL.md`、行为测试和 mutation 脚本；这些改动不是我产生的。所有结论和行号均来自 `git archive 9371d8a2` 的隔离快照，不混入未提交修改。
- 自定义 fixture 只写 `/tmp/codex-g32-r13.lvZ5Ww`，未修改被复核提交。
- 按要求未运行 `g32b_mutation_gates.py`，未设 `DEBUG=true`。
- 未测试并发；并发明确不在本卡范围，也没有把“缺锁”列为问题。
- 无网络、无 Neo4j、无真实 Obsidian UI；验证范围是唯一生产代码块、bridge、validator、规格及指定测试。
- 当前环境没有可调用的 `graphiti-canvas` MCP，因此无法执行仓规中的 Graphiti 查询；不影响上述本地提交级证据。

VERDICT: 需整改
