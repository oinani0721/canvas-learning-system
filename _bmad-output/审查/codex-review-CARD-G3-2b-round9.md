结论：需整改

### 28 条规则逐条判断

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | FAIL | `SKILL.md:1052-1073` 的 candidate 确实独立构造，但排除了 `effective_at/review_time`，与规格 `docs/...:184-192` 不符。把 durable 两处采用时刻从 10:00 改为 11:00、保留 `scored_at=10:00` 后，validator `rc=0`；同 ID 重跑 `rc=0`，FSRS `state 1→2`、`W 10:00→11:00`，同一评分被调度两遍。 |
| 2 | PASS | `SKILL.md:301-328,785-787` 在应用前强制整秒、UTC、可解析。小数秒及非 UTC `review_time` 实测 writer 均 `rc=1`、节点不变。 |
| 3 | FAIL | 日志边界回推见 `SKILL.md:938-1051`，期望分支见 `:1143-1170`，算术本身正确；但分支依赖文本正则 F1。把合法 YAML mapping 改为 `- ts:` 后接 `event_id:`，PyYAML 仍读出该 ID，writer 却 `rc=1` 称“缺校准记录”，会误拒合法状态。 |
| 4 | PARTIAL | 同一正常 durable 行的直接应用/崩溃恢复在六态格 6 中逐字节相同。对 `question_id` 等非载荷辅助输入的收窄是诚实的；但 stable=10:00、运行 ts=10:05 时，正常路径产出 `W/due=10:00/10:10`，degraded 后恢复产出 `10:05/10:15`，说明日志锁定的调度量仍因路径不同而分叉，见 `SKILL.md:1279,1292-1305`。 |
| 5 | PASS | `SKILL.md:785-787,842-856` 与 validator `:1363-1433` 均在应用前拒绝缺失、错类型及与分数不自洽的 rating。缺 rating/非法 grade 实测 writer `rc=1`。 |
| 6 | FAIL | 规格没有回写新的三时刻裁决：`docs/...:94-108,184-192` 无 `scored_at`，且仍规定 envelope 包含 `effective_at + payload`；`rg scored_at docs/... validate_learning_events.py` 为零命中。 |
| 7 | PASS | `SKILL.md:493-527` 确实按“最后一个非空行是否有 LF”判断，而非文件最后字节。不过该判据与追加后再次崩溃组合会产生另一个 BLOCKER，见问题清单。 |
| 8 | PASS | `SKILL.md:829-841` 与 validator `:1368-1373` 只接受布尔 `true`，并要求时刻不晚于 W。`false` 与标记后继事件实测均 `rc=1`。 |
| 9 | FAIL | 字节切行和逐行解码已实现于 `SKILL.md:464-527`；但“首行剥 BOM”不实：`:489-492` 在解码前直接拒绝，`:498` 的 `utf-8-sig` 不可达。实测 writer/validator 均 `rc=1`。应改规则措辞为“BOM 拒绝”。 |
| 10 | PASS | `SKILL.md:514-521` 使用 `object_pairs_hook` 拒重复键。重复 `grade_norm` 行实测 writer `rc=1`。 |
| 11 | FAIL | `SKILL.md:1101-1175,1187-1222` 会先重放并发布多个 foreign pending，再以 `rc=1` 要求重跑，并非发现多个即停止。两条同秒 pending 后，日志和 calibration 都是 10:00，节点 W 却被 A3 推到 10:00:01。现有测试 `test...:2027-2051` 还明确锁定“两条都要重放”。 |
| 12 | FAIL | 六态格 2 的 calibration 时刻是 08-02，而重试稳定值实际是默认 08-01，见 `test...:1255-1271` 与 helper `:158-169`；不是声称的同一次评分。canonical helper `:101-121` 还自称与生产同形却没有 `scored_at`。 |
| 13 | PARTIAL | writer 在 `SKILL.md:753-762` 正确执行 §一“不可路由即停”；但 validator `:1513-1514,1611-1619` 和规格 §三 `docs/...:43` 仍接受空 `node_id`。实测空串行 validator `rc=0`、writer `rc=1`。应修规格 §三和 validator，不应删除 writer 门。 |
| 14 | PASS | canonical foreign pending 会在 `SKILL.md:1143-1175` 复放 mastery、last_examined、calibration、attempt；本次 dup 被排除。三种时刻关系实测均第一轮恢复、第二轮收敛。 |
| 15 | FAIL | canonical degraded 重放确实不会重复吃 EMA；但 `_fm_has_event()` `SKILL.md:422-448` 只看 ID，合法 YAML 键序可使“已应用”为假，adopted-time 篡改又可使它为真但该日志事实实际未应用。 |
| 16 | PARTIAL | `SKILL.md:874-886` 实现了“≤W、无标记、无校准即停”；canonical 反例 `rc=1`。但校准判据存在 YAML 假阴性和 ID 别名假阳性，不能完整证明这项语义。 |
| 17 | FAIL | `SKILL.md:541-551` 只拒本节点，范围收窄落实了；但当前真相源 `docs/...:40,300` 允许任意非空字面 ID，历史行永久合法。预置本节点 `event_id=" quiz:old "` 时 validator `rc=0`、writer `rc=1`，属于单边过严。 |
| 18 | PASS | 本节点 `review/1` 行先经 validator，再由 `SKILL.md:797-828` 绑定两种事件类型、concept 和 vault。相应错误值实测均在应用前 `rc=1`。 |
| 19 | FAIL | `_looks_like_review_ext` 来自 validator `:1218-1230`，未包含新字段 `scored_at`。pending 行去掉 marker 和旧扩展键、仅保留 `grade_norm/exam_board/attempt_count/scored_at` 后，validator `rc=0`、writer `rc=0`，被当 §6.3 历史行跳过，W 仍为空。 |
| 20 | FAIL | 普通本节点行的顺序正确：`SKILL.md:744-819` 先路由、再 `validate_record_full()`、后分流；完整 validator 本身没有误拒合法 §6.3 历史行。失败点是全局 duplicate 在 `:560` 先命中别节点同 ID，而该行又在 `:763-767` 被跳过验证，随后 `:898-908` 把本次评分当历史幂等 no-op。实测 writer `rc=0`、W 为空。 |
| 21 | FAIL | `_fm_has_event_compat()` `SKILL.md:374-419` 只用当前仍存在的 ledger IDs 证明唯一，但实现又承认“已应用、日志行缺失”的旧写序。提交 `K` 后删日志，再提交不同完整 ID `quiz:K`，实际 `rc=0`、账本仍空、attempt 仍 1，后一评分消失。 |
| 22 | FAIL | `SKILL.md:264-269` 只做 `_TS_RE.fullmatch`，未调用 validator 的真实日期/A7 检查 `validate...:140-172,1516-1520`。输入 `2026-02-30T10:00:00Z` 时 writer `rc=0` 并原样落账，validator `rc=1`；下一次合法评分也被自产坏行阻塞。 |
| 23 | PARTIAL | `SKILL.md:948-962` 已从 W 改为 calibration 判后续计数，这是正确方向；但使用的 calibration predicate 不是可靠 receipt，合法 YAML 键序和历史别名都能改变结果。 |
| 24 | PASS | `SKILL.md:981-1026` 优先利用日志后继行自身的 attempt 值回推；没有 anchor 时点名缺值行并停。构造 `E1(1)→无 count L2→L3(3)`，正确 E1=1 `rc=0`，错误 E1=2 `rc=1`。 |
| 25 | PASS | candidate 使用 `_SCORED_AT`，见 `SKILL.md:1059-1066`，不抄 durable，也不使用本轮 ts。stable=10:00、recorded=10:05 时，落账 `scored_at=10:00`。 |
| 26 | PASS | gap 折算见 `SKILL.md:998-1023`。跨一条缺 count 的推进事件时正确减量；无后继证明行则 fail-closed。实跑正确值放行、错误值报 envelope 冲突。 |
| 27 | FAIL | durable 侧仍在 `SKILL.md:1055-1059` 回落 `review_time`；foreign 行完全不要求 `scored_at`；degraded 又在 `:1292-1305` 使用运行 ts。A3 后删除 durable `scored_at` 并回滚节点，连续重跑均 `rc=1 envelope 冲突`，W 永远停在旧值。规格和 validator 也都没有该字段。 |
| 28 | PARTIAL | 无 marker 历史行的 `out_of_order` 不参与序数语义已落实于 `SKILL.md:1008-1014`；`calibration_log: # comment` 已可识别；空白 ID 只管本节点也已落实。但空白禁令本身比规格更严，而且 calibration 仍无法处理合法 YAML 键序或 `calibration_log: null`。 |

口径双向核对结果：

- writer 放行、validator 拒绝：非法日历 `recorded_at`；另有“别节点坏行占用本次 event_id”被 writer 当幂等成功。
- writer 拒绝、validator 放行：本节点空白 `event_id`、空 `node_id`、非 UTC durable 时刻、未标记迟到行、本节点未知版本。其中非 UTC、迟到行和未知版本是 §6.2 明文允许的消费侧加严；空白 ID 没有规格依据；空 node_id 是规格内部与 validator 未同步。
- 8 处重复检查本身不算缺陷。实际规格 `docs/...:195-196` 已明确说明它们是同口径纵深而非“更严”；建议保留，当前不需要删代码，也不需要再改措辞。`_instant_only().strip()` 的空白绕过当前确实到不了：唯一调用 `SKILL.md:862` 之前已在 `:785-787` 经过完整校验。

### 六种状态

| 状态 | 结论 | 实际前置与观测 |
|---|---|---|
| 1. `dup=None, F1=F` | PASS（canonical 行） | 前置 candidate 不在账本、calibration 空、W 空，另有一条 foreign pending。settled `rc=0`，最终账本 2 行、W=08-02、calibration 2 项、attempt=2。但测试所用 foreign helper 缺 `scored_at`，与规则 27 冲突。 |
| 2. `dup=None, F1=T` | FAIL | calibration 实际记 08-02，重试 stable 实际为 08-01；writer 仍 `rc=0` 并 no-op。另以同 ID、12 月时刻、不同分数实测也 `rc=0`，账本仍无该事件，12 月评分静默消失。 |
| 3. `dup=有, F1=T, applied=T` | PASS | W=durable time，calibration 有该 ID；重跑 `rc=0`、幂等跳过、节点 SHA 不变、账本 1 行。 |
| 4. `dup=有, F1=F, applied=T` | PASS | W 已过 durable time、calibration 无该 ID；writer `rc=1`，明确要求人工核对，节点和账本零写。 |
| 5. `dup=有, F1=T, applied=F` | PASS（canonical receipt） | degraded 后 W 空、calibration/attempt 已存在；重跑 `rc=0`，只补 FSRS，EMA 与 attempt 不变。YAML 键序或 ID 别名会破坏这一判定。 |
| 6. `dup=有, F1=F, applied=F` | PASS（canonical 行） | append 后回滚节点；恢复 `rc=0`，最终节点逐字节等于直接成功 golden，W=TS1、attempt=1、账本 1 行。 |

因此六种结构并非全部被有效覆盖：格 2 的夹具语义错误，且格 1 使用了缺 `scored_at` 的所谓 canonical 行。

### 问题清单

[BLOCKER] `SKILL.md:1052-1073,1101-1113` — adopted `review_time/effective_at` 未被身份或 receipt 绑定，同一次评分可再次推进 FSRS。  
依据: 正常写 E1@10:00 后，仅把 durable 两处采用时刻改为 11:00，保留 `scored_at=10:00`；validator `rc=0`，同 ID 重跑 `rc=0`。节点从 `state=1,W=10:00,due=10:10` 变为 `state=2,W=11:00,due=08-03 11:00`，账本、attempt、calibration 仍各 1。  
建议: 按当前规格保留 adopted time 的约束；将 calibration 改为结构化 receipt，至少绑定完整 ID、adopted time、grade/attempt。恢复时从稳定时刻与可证明的前置 W 复算 A3，并与 durable 值核对，不能无条件排除采用时刻。

[BLOCKER] `SKILL.md:1055-1059,799-819` / `validate_learning_events.py:1218-1230` — `scored_at` 没有形成规格、校验器、消费侧闭环。  
依据: A3 产生 `review_time=10:00:01` 后删除 durable `scored_at` 并回滚节点，validator `rc=0`；相同 stable=10:00 连续重跑均 `rc=1 envelope 冲突`，W 卡在 10:00。另把 pending payload 降级成只剩 `grade_norm/exam_board/attempt_count/scored_at`，validator/writer 均 `rc=0`，writer 当历史行跳过，W 为空。  
建议: 先在 §6.1/§6.2 冻结 `scored_at` 必填、身份语义和旧行迁移策略；同步 validator 的 REQUIRED/marker-downgrade 键集；所有本节点待消费行缺它立即停；删除 `review_time` fallback。

[BLOCKER] `SKILL.md:560-570,763-767,898-908` — 别节点行可以占用本次全局幂等键并让本次评分零次应用。  
依据: 预置一条别节点、同 `event_id` 的合法 §6.3 历史行，validator `rc=0`；提交本节点评分时 writer `rc=0`，输出“历史行幂等跳过”，账本仍 1 行、W 为空。坏 foreign 行版本同样被吞。  
建议: 任何 `event_id == evid` 的行都进入当前身份冲突域，不受“别节点坏行不阻塞”豁免；node/type 不同须 fail-closed。

[BLOCKER] `SKILL.md:374-419,892-896` — `dup=None,F1=true` 无条件旧写序 no-op，无法证明是同一次评分。  
依据: 8 月 grade=.75 应用后删除其日志行，再用同 ID、12 月、grade=.11 提交；writer `rc=0`、删除输入 payload，账本仍无该事件，W/calibration 仍为 8 月、attempt=1。`K` 与 `quiz:K` 的历史别名也可产生相同漏账。  
建议: F1-only 状态必须结构化读取 receipt 并比较仍可持久化的事实；receipt 不足以绑定 stable time/grade 时停下。现存 ledger IDs 不能证明已丢失日志来源不存在。

[BLOCKER] `SKILL.md:493-527,1354-1360` — 截断尾行被隔离后，若 append 与节点发布之间崩溃，新事件永久不可恢复。  
依据: 预置无 LF 半行；首跑 `rc=0`，程序补 LF 并追加有效事件。回滚节点模拟 append 后崩溃，再跑 `rc=1`：“第 1 行损坏（中间行）”；有效事件仍在第 2 行，W 为空。  
建议: `docs/...:30,182-183` 需先消除自相矛盾。可使用可持久验证的截断隔离记录，使后续读方能证明并跳过该特定坏行；否则首次发现半行就必须停止，不能继续追加。

[HIGH] `SKILL.md:422-448,660-731` — calibration 判定不是 YAML 语义解析，会误判已应用状态并导致不收敛。  
依据: 仅将合法 mapping 重排为 `- ts:` 后接 `event_id:`，PyYAML 仍解析出正确 ID；同 ID 重跑 writer `rc=1`，以后持续称“缺校准记录”。`calibration_log: null` 首次评分还会被写成非法 YAML。  
建议: 用支持重复键拒绝的结构化 YAML 解析读取 calibration receipt；明确处理 `null`、空列表、尾注释和任意合法 mapping 键序。

[HIGH] `SKILL.md:1279,1292-1305` — degraded 路径仍用运行时 ts 代替稳定业务时刻。  
依据: stable=10:00、ts=10:05；正常路径最终 `review_time/W/due=10:00/10:00/10:10`，强制 degraded 后恢复为 `10:05/10:05/10:15`，节点字节不同。  
建议: degraded 分支同样从 `_SCORED_AT` 解析、整秒化并执行 A3；`p["ts"]` 只允许写 `recorded_at`。

[HIGH] `SKILL.md:1101-1222` — 多 pending 并未在应用前停止。  
依据: 两条 foreign pending 时首轮 `rc=1`，但节点已经发布两条恢复结果。两条均为 10:00 时，最终 W=10:00:01，而两条 durable/calibration 时刻仍为 10:00；validator 前后均 `rc=0`。  
建议: 若规则 11 的确要求“多个即停”，在任何 bridge/mastery/发布之前检查数量并零写退出；若只想禁止追加本次事件，必须改规则措辞并另行解决同秒采用时刻无法回写日志的问题。

[HIGH] `SKILL.md:264-269,1336` — 输入 ts 只过正则，程序可自产 validator 拒绝的日志。  
依据: `ts=2026-02-30T10:00:00Z`、稳定业务时刻合法时 writer `rc=0`，日志原样写入；validator `rc=1`，下一次合法评分也被该行阻塞。  
建议: append 前对新构造的完整 `rec` 调 `validate_record_full()`，或至少复用 `_parse_ts()` 的日期与 A7 校验；仍保持字面值不归一化。

[MEDIUM] `SKILL.md:541-551` — 本节点空白 event_id 的拒绝比当前规格更严。  
依据: 本节点合法 §6.3 行 `event_id=" quiz:old "` 时 validator `rc=0`、writer `rc=1`；`docs/...:40,300` 只要求非空并冻结字面身份。  
建议: 若产品要全面禁空白，先改规格、validator、所有写点并提供迁移；在此之前不应单边阻塞所有本节点历史行。

[MEDIUM] `test_g3_2_review_ledger.py:1255-1271,2904-2957` — 新六态和稳定时刻测试没有证明其声称的行为。  
依据: 格 2 的 calibration/stable 分别为 08-02/08-01；B3 在 `_fresh()` 后只删除 candidate 值，没有 durable fallback 可测。将 pending duplicate 恢复替换为直接成功 no-op 的内存变异后，整个 `test_round8_stable_scored_at` 仍 PASS。  
建议: 格 2 显式传原 stable；B1/B2 对拍节点字节、W、attempt、calibration；B3 建立含 durable 行再删除其 `scored_at`；更新 `_review_row()` 为真实生产键集。

[MEDIUM] `docs/learning-events-schema-v1.md:14-16,43` / `validate_learning_events.py:1513-1514` — `node_id` 契约内部及 validator 口径不一致。  
依据: `node_id=""` 的历史 v1 行 validator `rc=0`、writer `rc=1`。§一说不可路由必须停，§三却说可为空。  
建议: 以优先条款 §一为准，修改 §三和 validator；保留 writer 的 fail-closed。

[LOW] `SKILL.md:489-498` — 规则 9 和注释仍声称剥 BOM，但实际路径拒绝。  
依据: BOM 文件 writer `rc=1`、validator `rc=1`；`utf-8-sig` 分支不可达。  
建议: 将规则改为“首行 BOM 拒绝”，并删除误导性的死分支/旧注释。

### 测试复核

使用实际存在的 `backend/.venv/bin/pytest`，并按要求设置 `PYTHONDONTWRITEBYTECODE=1`、`INTERNAL_API_KEY=review-placeholder`、`NEO4J_ENABLED=false`、独立 TMPDIR，未设置 `DEBUG`：

- `test_g3_2_review_ledger.py`：`48 collected / 48 passed / 10 warnings`，exit 0，57.65s。
- 五个目标文件合跑：`278 collected / 277 passed / 1 skipped / 10 warnings`，exit 0，61.06s。
- 自报的 `278 / 277 / 1` 数字属实。
- skipped 项为 `test_learning_events_schema_contract.py:1104-1111::test_repo_vault_ledger_schema_v1`，原因是该 worktree 没有 `canvas-vault/learning_events.jsonl`。
- 这 278 项不是整个 regression/整仓测试。
- 未发现裸 `assert True`；但有两个静态契约测试，且上述 B1/B2 断言对“恢复变成 no-op”的变异没有鉴别力。

### 验证限制

- 审计 checkout：`card/w7-ledger@be703e0df64f9736aabd4ee1d5f36b6ba330e235`。
- 根目录没有 `.venv`；照字面运行会 exit 127，因此改用实际的 `backend/.venv`。
- 工作区为只读；最小 vault 均建在 `/private/tmp` 隔离目录，没有修改被复核文件。
- 测试自身在 `test_g3_2_review_ledger.py:1736-1770` 硬编码写删 `/private/tmp/g32b-gate-toctou-*`，所以即使设置 TMPDIR，也并非所有写入都受该目录约束。
- 未运行明确禁止的 `backend/scripts/g32b_mutation_gates.py`。
- 未验证并发；按请求不把缺锁列为问题。
- worktree 原有若干 `_bmad-output/审查/...` 未跟踪文件；本次未触碰。

VERDICT: 需整改


