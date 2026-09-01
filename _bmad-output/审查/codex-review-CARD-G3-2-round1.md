结论概览：A=PARTIAL，B=FAIL，C=FAIL，D=FAIL，E=FAIL/UNVERIFIABLE，F=PARTIAL。定向 16 门加指定 contract 函数虽为 `17 passed`，但生产故障注入复现了多条未覆盖反例。

### A. 写序 — PARTIAL

[HIGH] [SKILL.md:265-277,485-492](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:265) — 真实 partial-JSON 短写在 LF 守卫前即退出，所谓“截断尾行自愈”不可达。  
依据: §6.2 A4.5 要求下次追加先做 LF 守卫；预置 JSON 前缀且无 LF 后重试，结果 `rc=1`、文件字节不变且仍无 LF。现有测试只覆盖“完整 JSON 缺 LF”，不是真短写。  
建议: 将持久化 LF 守卫移到 parse/查重之前，并补 partial-JSON 故障门。

未发现：正常路径确实在 [SKILL.md:464-507](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:464) 完成账本 `write/fsync/首建父目录 fsync`，随后才在 `541-555` 发布节点 temp。主 PYEOF 内没有先物理写 `NODE` 的路径。Step 3 先写的是检验白板 score/status frontmatter，不是 §6.2 的节点 current state；因此不能笼统声称“任何 frontmatter 都不先写”。

### B. A2 恢复与幂等 — FAIL

[BLOCKER] [SKILL.md:389-456,480-555](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:389) — 既有 pending 重放失败后，仍会追加新的 degraded 事件。  
依据: §6.2:160-162 要求追加前重放至空；代码在重放失败后于 `441-442` 清除错误。故障注入结果为账本 `1→2`、stdout 同时出现“pending 重放失败”和“事件已落日志”、FSRS 仍为空。  
建议: 本轮只要存在 pending 且任一重放失败，必须在 append/发布前 fail-closed。

[BLOCKER] [SKILL.md:403-420,458-555,279-283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:403) — dup restore 重放失败仍发布 calibration，随后同 event_id 永久被 F1 当成完整应用。  
依据: 故障恢复后 `calibration=True`、无 FSRS；bridge 恢复后同 eid 重跑只输出“已完整应用，幂等跳过”，最终仍无 FSRS。它主动破坏了“calibration/EMA/FSRS 同次原子发布”这一已知取舍的前提。  
建议: restore 重放失败必须零发布，尤其不得写 calibration event_id。

[BLOCKER] [SKILL.md:403-412](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:403) — F1=false 的 dup restore 没有比较完整 canonical envelope。  
依据: §6.2:183-189 要比较 `{event_version,event_type,node_id,effective_at,payload}`；实现只比五个局部字段。分别篡改 `exam_board`、`effective_at`、`attempt_count`、`event_version` 后，四种均 `rc=0`、无冲突并发布。  
建议: replay/apply 前完成全 envelope canonical 比较；任何差异均 fail-closed。

[MEDIUM] [fsrs_bridge.py:195-198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/scripts/fsrs_bridge.py:195) — 显式 rating 被先 `int()` 强制转换，非法 pending 可被静默应用。  
依据: `1.5→1`、`3.9→3`、`"1"→1`，违反 §6.1:103 的严格 int 要求；A2 在 SKILL `392-394` 直接传入账本 rating。  
建议: 强制 `type(rating) is int and rating in {1,2,3,4}`，并将 `TypeError` 归入 invalid-input。

### C. 查重 — FAIL

[HIGH] [learning_event_log.py:91-111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/app/services/learning_event_log.py:91) — malformed 无 LF 尾行被静默跳过后直接拼接，新事件不可解析但函数返回成功。  
依据: 预写 `{"event_id":"cut` 后调用 `append_event(...,"fresh")`，得到 `ok=True`，两个 JSON 粘成唯一坏行。  
建议: malformed 行应记录错误并返回失败；只对完整、可解析但缺 LF 的尾行补 LF。

未发现：SKILL `273-277` 与 `learning_event_log.py:94-99` 都是 `json.loads` 后比较顶层 `event_id`；payload 文本包含目标串不会被生产实现误判 duplicate。

### D. degraded 与 bridge — FAIL

[HIGH] [SKILL.md:438-456](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:438) — degraded 本地 A3 推进缺少 A7 排他上界，会制造非法且永久孤立的事件。  
依据: 合法 `W=8999-12-31T23:59:59Z`、`ts=W`、FSRS unavailable 时，写出非法 `review_time=9000-01-01T00:00:00Z`，同时发布 Beta/calibration；恢复后同 eid 被 F1 no-op，校验仍失败。  
建议: degraded 路径复用 bridge 的 review-domain 门；推进达到上界时 append 前零写退出。

未发现：bridge 的 aware→UTC、naive 拒绝、入口整秒、`review_time/rating/version/hash` 加性输出正确；普通 degraded 路径也能做到同因非空双哨兵、Beta-only 和 W 不推进。

### E. G3-3 边界 — FAIL / UNVERIFIABLE

[BLOCKER] `_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W7.md:<文件缺失>` — 指定卡文及验收单在当前 WT 返回 `ENOENT`。  
依据: 精确路径及其 `第八批-goals` 父目录均不存在，无法核验卡文是否诚实登记单写者、G3-3 边界及已知取舍。  
建议: 补齐卡文或提供正确唯一路径后重新审查。

[MEDIUM] [SKILL.md:265-277,480-483,541-550](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:265) — 生产块依赖单写者但未明示，“并发/重放”日志还暗示了不存在的并发防护。  
依据: `_rows` 只扫描一次；`_mode=="append"` 已意味着该快照中无 dup，因此 `_again` 查询同一旧快照的并发分支不可达；固定 `.quiz-tmp` 也依赖串行。只有测试文件 `:1,487-489` 写明单写者。  
建议: 不在本卡加锁，但须在 SKILL/验收单明确“G3-3 前不并发安全”，并删除误导性的“并发”措辞。

### F. fixture 同源性 — PARTIAL

[MEDIUM] [test_g3_2_review_ledger.py:538-555](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:538) — 第 16 门没有真正杀死旧子串查重实现。  
依据: 对当前中文 EID 和转义 note 实算，旧谓词 `json.dumps(evid) in line == False`；恢复旧实现该门仍可绿。  
建议: 改用 ASCII event_id，并让 payload 某字段值直接等于该 event_id。

[MEDIUM] [test_g3_2_review_ledger.py:vault 99-113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:99) — bridge 的真实 re-exec 可达，但没有经过 fixture 声称的 tmp `backend/.venv` candidate。  
依据: bridge 是指向 WT 的 symlink，而 `_venv_python()` 对 `__file__` 调用 `resolve()`，实际命中 WT 的 venv；tmp 目录 symlink 未参与。  
建议: 修正注释并断言实际解释器；若要证明 tmp candidate，使用不会 resolve 回 WT 的布局。

[LOW] [test_g3_2_review_ledger.py:59-76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:59) — “逐字仿 live”证据不完整。  
依据: 两个预置节点都没有既存 `calibration_log`；重跑只验证 writer 自产格式，不能验证真实 Obsidian 规范化后的既存日志形态。  
建议: 增加预置 live 风格 calibration 条目的 fixture。

验证限制：耐久 spy 的 `dir_count >= 2` 没绑定两个父目录 inode或各自时序；实际源代码顺序正确，但该门不足以独立证明完整目录耐久序列。逐字提取 PYEOF、仅替换 P 常量，以及 `_vault_id_of` 与校验器同实现三项未发现偏差。

定向结果为 `17 passed`，但这不是全仓 CI、掉电存活或并发安全证明；上述生产反例足以否决交付。

VERDICT: 需整改


