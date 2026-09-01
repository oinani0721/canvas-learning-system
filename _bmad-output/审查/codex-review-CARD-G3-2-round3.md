结论：**需整改**。指定 25 门虽全部通过，但生产主 PYEOF 块仍复现 **2 BLOCKER + 3 HIGH + 2 MEDIUM**。

### Round-2 整改复核

| 项目 | 结论 | 当前证据 |
|---|---|---|
| B-a | PASS | 已应用判据改为 `W >= durable.review_time`；envelope 位于 no-op/A2/恢复前，见 `SKILL.md:419-470`。 |
| B-b | FAIL | 两个身份键已排除、attempt 已按态计算，但存在历史 attempt 误拒和任意额外 payload 自抄。 |
| B-c | PASS | 全文件 parsed `event_id` 计数并在重放前拒绝，见 `SKILL.md:277-300`、门㉓ `test:779-807`。 |
| H-a | PASS（原项） | 显式 rating 类型/范围及 abandoned≠1 已拒绝，见 `fsrs_bridge.py:193-208`；但 scored 自洽仍有新 HIGH。 |
| H-b | FAIL | calibration/last_examined 已改，正常路径 mastery 仍使用 `p["ts"]`，见 `SKILL.md:584`。 |
| H-c | PASS | 双引号用 `json.loads`，单引号/裸词兼容，见 `SKILL.md:251-270`、门㉔。 |
| H-d | PASS | `st_size > 0` 后才读取尾字节，见 `learning_event_log.py:92-115`、门⑳。 |
| M-a | PASS | 已声明同一 vault 内任何两个 quiz-answer 不得并行，见 `SKILL.md:272-274`。 |

### Findings

[BLOCKER] canvas-vault/.claude/skills/quiz-answer/SKILL.md:450-458,482,507-545 — `_mine_env` 仍从 durable payload 自抄任意额外键，可绕过 envelope 并跳过 FSRS 恢复。  
依据: 临时生产块实测：给崩溃窗口 durable 行加入 `payload.out_of_order=true`，envelope 放行，A2 因 `:482` 排除该行，writer 仍 `rc=0` 并写入 calibration/mastery，但节点 `fsrs_fields={}`、账本仍一行；主体 validator 甚至返回 `rc=0`。这违反 schema §6.2:183-189 的完整 payload envelope 与恢复约束。门⑧只变异被独立覆盖的 `exam_board/event_version`。  
建议: 从本次输入和固定生产键集独立构造 candidate payload；在线重试出现 `out_of_order` 或未知额外键必须冲突，仅排除明确批准的两个身份键。

[BLOCKER] canvas-vault/.claude/skills/quiz-answer/SKILL.md:484-496；canvas-vault/.claude/scripts/fsrs_bridge.py:190,233-241 — A2 会归一并消费带小数秒的 durable `review_time`，导致同一账本行二次推进 FSRS。  
依据: 预置唯一行 `review_time=10:00:00.500Z`。第一次恢复 `rc=0`，W 写为 `10:00:00Z`；第二次同 ID 重跑仍判 pending，再次重放后 W 变为 `10:00:01Z`，账本始终一行。正是 §6.2:192 禁止的 A5 二次 apply。门⑤只覆盖正常新写输入。  
建议: A2 调 bridge 前严格校验 durable 时刻为 tz-aware 整秒；非法 durable 行 fail-closed，禁止消费时顺手规范化。

[HIGH] canvas-vault/.claude/skills/quiz-answer/SKILL.md:433,439-458 — applied 态用当前 tip 的 `attempt_count` 校验历史事件，合法旧事件重放会被误报冲突。  
依据: 实测 E1、E2 均成功，durable attempts 为 `[1,2]`，frontmatter 为 2；随后原样重跑 E1 返回 `rc=1 envelope 冲突`，而 §6.2:187 要求同 canonical envelope no-op。门①只测紧邻重跑。  
建议: 从账本边界独立复算历史 ordinal，不能把当前 tip 当成旧 durable 值；新增 `E1→E2→重跑E1` 门。

[HIGH] canvas-vault/.claude/skills/quiz-answer/SKILL.md:523,581-588；backend/tests/regression/test_g3_2_review_ledger.py:60-61,207-220 — H-b 的逐字节恢复仍未闭合。  
依据: 正常路径 `:584` 传原始 `p["ts"]`，恢复路径 `:523` 传 durable `review_time`。用含 `last_examined` 且触发 A3 的正常卡实测，两次均 `rc=0`，但节点 SHA 分别为 `96205e2a…` 与 `3b469e84…`；`mastery_a` 分别为 `65631885.0457` 与 `65631877.4112`。现门②使用无 `last_examined` 的新卡，无法触发差异。  
建议: 正常路径也传 `review_time`；门②改用含 idle 状态且触发 A3/A5 的整节点 byte 对拍。

[HIGH] canvas-vault/.claude/scripts/fsrs_bridge.py:193-208；canvas-vault/.claude/skills/quiz-answer/SKILL.md:492-496 — A2 仍会应用 scored rating 与 grade_norm 不自洽的 pending 行。  
依据: `answer_scored + grade_norm=0.75 + rating=4` 类型和范围合法但契约应为 rating 3；实测 writer `rc=0`、输出“A2 重放已应用”并追加下一事件，事后 validator 才返回 `rc=1`。门⑰只测 float 与 abandoned 变体。  
建议: 显式 rating 对 scored 同样要求 `rating == rating_from_grade(grade_norm)`，并在 apply 前拒绝。

[MEDIUM] docs/learning-events-schema-v1.md:183；canvas-vault/.claude/skills/quiz-answer/SKILL.md:434-457；backend/tests/regression/test_g3_2_review_ledger.py:829-842 — 门㉕锁定的身份键排除策略尚未同步到冻结 schema。  
依据: §6.2:183 定义 envelope 包含完整 payload，只明确排除 `recorded_at`；实现及门㉕却允许两个身份键不同。  
建议: 若该分层裁决确定生效，正式修订 §6.2；否则实现须服从现有完整 payload 契约。

[MEDIUM] canvas-vault/.claude/skills/quiz-answer/SKILL.md:278-288；backend/tests/regression/test_g3_2_review_ledger.py:284-313 — 尾行解析丢失 EOF 是否有 LF，带 LF 的损坏末行也被当成可容忍截断。  
依据: 预置坏 JSON 且已带终止 LF，实测 writer 仍 `rc=0`、声称“截断尾行”，继续追加并推进节点。门⑦仅覆盖无 LF partial。  
建议: 保留原始 EOF/LF 状态；只有无 LF 的最后坏行可隔离，带 LF 坏行必须 fail-closed。

### 六格状态机

`fsrs_applied` 只在 `dup=有` 时有定义，因此实际是 `2 + 4 = 6` 格。

| 状态 | 当前行为 | 结论 |
|---|---|---|
| `dup=None,f1=F` | A2 后正常 append/apply | PARTIAL：foreign pending 输入门不完整 |
| `dup=None,f1=T` | 旧写序孤儿 no-op | PASS |
| `dup有,f1=T,applied=T` | envelope 后 no-op | FAIL：历史 attempt 误拒 |
| `dup有,f1=F,applied=T` | envelope 后人工裁定 | PASS |
| `dup有,f1=T,applied=F` | A2 后只补 FSRS | FAIL：小数秒可重复推进 |
| `dup有,f1=F,applied=F` | A2 后全套恢复 | FAIL：额外键可跳过 A2，且字节不等 |

即时 degraded/crash 恢复到 applied 后的 attempt 计算局部自洽；一旦 `W` 被后续事件推进到 `W > durable.review_time`，状态切换即失去自洽。

### 回归与六项终审

指定命令结果：`25 passed, 10 warnings in 18.62s`。未运行整仓测试；首次只读沙箱因无可写 tempdir 在收集前失败，使用隔离临时 fixture 后同命令通过。

- 写序：PASS，单写者路径确为 ledger fsync 后再发布 frontmatter。
- A2：FAIL。
- 查重：FAIL；parsed equality 和全文件唯一性已通过，但 canonical envelope 仍可绕过。
- degraded 哨兵：PASS；两键成对、W 冻结未发现问题。
- G3-3 边界：PASS；声明范围已诚实覆盖 per-vault。
- fixture：主 PYEOF 逐字提取 PASS；状态覆盖完备性 FAIL，绿色 25 门不能覆盖上述反例。

验证限制：源码检查限于卡文和指定文件；仅执行指定 25 门及隔离临时反例。`graphiti-canvas/search_memory_facts` 当前工具面不可调用。全程未修改被审文件。

VERDICT: 需整改


