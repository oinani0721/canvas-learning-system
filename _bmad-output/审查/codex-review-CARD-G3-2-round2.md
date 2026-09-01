结论：需整改。虽然 20 门和指定 production contract test 共 21 项全部通过，但复现出 3 个 BLOCKER、4 个 HIGH、1 个 MEDIUM。

### Findings

[BLOCKER] [quiz-answer/SKILL.md:243-287](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:283) — F1 在 A2 与 canonical envelope 门之前早退，既吞掉冲突事实，也跳过 degraded pending 恢复。  
依据: 契约 [§6.2 A2/A4.5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:160) 要求未推进 frontmatter 时走 A2、异 envelope 必须拒绝。真实主 PYEOF 复现：①先写 `answer_scored`，同 ID 改 `abandoned=True` 仍 `rc=0`、“幂等跳过”；②首次 degraded 后同 ID 重试，仍 `rc=0`，`fsrs_after_retry={}`、账本 1 行。  
建议: 有 durable duplicate 时先执行 envelope 判定与 W/A2 恢复；F1 不能单独证明 FSRS 已推进。

[BLOCKER] [quiz-answer/SKILL.md:417-431](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:417) — restore 的“全 envelope”比较仍从 durable 行自抄三个非时刻字段。  
依据: `_mine` 直接采用 `_dpl` 的 `fsrs_library_version`、`fsrs_params_hash`、`attempt_count`，违反“仅时刻字段采纳 durable，其余差异 fail-closed”。将 library 改成 `tampered-library` 后真实恢复仍 `rc=0`、`ledger=restore`。门⑧只变异 `exam_board/event_version`。  
建议: 保留重放 `_out` 并独立复算算法身份与 attempt_count；全部非时刻字段逐项变异锁门。

[BLOCKER] [quiz-answer/SKILL.md:269-281,374-405](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:379) — A2 不拒绝既存重复 event_id，会确定性重复应用。  
依据: `dup=next(...)` 只取首行，但 pending 循环收纳所有行。预置两条完全相同的 pending 行后，真实入口输出两次“A2 重放已应用”，随后发布节点；违反 [§6.2:187-189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:187) 的 duplicate 绝不二次 apply。  
建议: 重放前对全文件 event_id 唯一性 fail-closed；不得静默去重或选边。

[HIGH] [fsrs_bridge.py:193-200](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/scripts/fsrs_bridge.py:193) — M-1 严格 rating 门可被 abandoned 分支绕过。  
依据: `abandoned` 先无条件置 `used_rating=1`，严格 `isinstance` 只在 `elif` 中执行。pending `answer_abandoned/rating=1.5` 被真实 A2 成功应用，违反 [§6.1:103-105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:103)。门⑰只测了 scored 变体。  
建议: 先验证显式 rating 的类型、范围和 abandoned 自洽，再选择调度 rating。

[HIGH] [test_g3_2_review_ledger.py:207-221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/tests/regression/test_g3_2_review_ledger.py:207) — 门②没有落实卡文要求的“恢复结果与直接应用逐字节相同”。  
依据: [W7.md:49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W7.md:49) 要求字节等值；测试只比 FSRS 子集。复现得到 `byte_equal=false`，SHA 分别为 `5fccc4dc…` 与 `bb351682…`。restore 虽采纳 durable `review_time`，但 [SKILL.md:481,534](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:481) 的 `last_examined/calibration.ts` 仍使用重试 `p["ts"]`。  
建议: 恢复所有副作用使用 durable 原事件时间，并以节点完整 bytes 对拍。

[HIGH] [quiz-answer/SKILL.md:_fm_has_event:249-263](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:249) — 含引号或反斜杠的合法 event_id 会造成 F1 假阴性和重复 frontmatter 副作用。  
依据: 写侧用 `json.dumps`，读侧只剥外引号、不反解转义。用 `board"quote#q1` 重放后节点再次改变，`attempt_count 1→2`、calibration 变 2 条，账本仍 1 行。  
建议: 双引号 scalar 用 `json.loads` 同源反解，并覆盖 quoted、single-quoted、bare 三种持久形态。

[HIGH] [learning_event_log.py:92-113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/backend/app/services/learning_event_log.py:92) — H-2 新 LF 守卫使既存零字节账本无法写入首事件。  
依据: 空文件扫描后执行 `seek(-1, SEEK_END)` 抛 `Errno 22`，函数吞错并返回 `False`；复现结果 `returned=false,size=0`。门⑳仅覆盖非空 partial 尾行。  
建议: 仅在 `path.stat().st_size > 0` 时读取尾字节，并新增空文件首写门。

[MEDIUM] [quiz-answer/SKILL.md:265-266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/canvas-vault/.claude/skills/quiz-answer/SKILL.md:265) — M-2 单写者声明被收窄成“同一节点”，未诚实覆盖同 vault 不同节点共享账本。  
依据: [§6.2:180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:180) 明确账本是 per-vault 共享文件，G3-3 前不同节点 writer 同样缺 per-vault 锁。  
建议: 明示“同一 vault 内任何两个 quiz-answer 均不得并行”。

### Round-1 整改复核

| 项目 | 结论 |
|---|---|
| B-1 | 目标修复 PASS。失败在 `399-403`，早于 append `486-528` 和发布 `565-576`；此前成功重放只改内存。Step 3 已写分并停在 pending，属既定两阶段状态。 |
| B-2 | 原“失败后发布 calibration”路径已修；总体仍 FAIL，见 F1/degraded 与转义 ID findings。 |
| B-3 | FAIL：F1 绕门且三个非时刻字段自证。 |
| H-1 | PASS：真实 partial 尾行跳过留痕，中间坏行拒绝，门⑦有效。 |
| H-2 | PARTIAL：非空 partial 隔离和幂等通过；零字节边界失败。 |
| H-3 | PASS：A7 门在 append/publish 前，门⑱有效。 |
| M-1 | PARTIAL：scored `1.5` 已拒；abandoned 绕过。 |
| M-2 | PARTIAL：`_again` 措辞已修；单写者范围仍过窄。 |
| M-3 / M-4 | PASS：ASCII 键名陷阱可杀旧实现；fixture 对 WT venv 的说明与 `resolve()` 一致。 |
| LOW / inode | PASS：门⑲覆盖 Obsidian 裸词；门⑬绑定 vault 根与节点父目录 inode。 |
| B-4 | PASS：正确编排 worktree 卡文可读。 |

定向命令收集 21 项，结果 `21 passed, 10 warnings`。但语义覆盖上，门②、⑧失败；门①完整幂等、⑫同 ID degraded 恢复、⑰ abandoned rating、⑳空文件均仅部分覆盖。

六项最终结论：

- 真 write-ahead：PASS（单写者正常路径）。
- A2 不重复应用：FAIL。
- 查重正确：FAIL。
- degraded 哨兵成对写出：PASS；非法 pending 的消费门仍不完整。
- G3-3 边界诚实：PARTIAL。
- fixture 同源：PASS。

合法 restore 的 `Z`/`+00:00` canonical 文本冲突仍是 [§6.2:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger/docs/learning-events-schema-v1.md:186) 已登记的保守误拒；本轮未发现超出该已知口径的新误拒，主要问题是错误放行。

验证限制：`graphiti-canvas/search_memory_facts` 本会话不可调用；首次受限沙箱运行因无可写 tempdir 在收集前 ENOENT，获准使用隔离临时 fixture 后复跑全绿，不是产品失败。本轮未运行整仓测试。

VERDICT: 需整改


