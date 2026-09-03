1. HIGH-3 durable 失败反馈 — STILL-OPEN

- round-2 的普通文件反例已修：orchestrator 返回 `persist_failed`、新条目从内存弹回、journal 不存在；Lance `_persist_pending()` 返回 `False` 并累计错误。[vault_index_orchestrator.py:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:283) [vault_index_orchestrator.py:326](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:326) [lancedb_index_service.py:456](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:456)
- coalesced 当前行为正确：失败时返回 `persist_failed`，`delete/force=True` 的内存变更被保留；新条目失败则弹回。旧 durable journal 保持不变。
- 503 当前实现也正确：失败实测返回完整七字段 body、`durable=false`；成功路径仍为 `RefreshChangedResponse`，accepted/coalesced/excluded 计数初始化和返回均正确。[index.py:51](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/api/v1/endpoints/index.py:51) [index.py:155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/api/v1/endpoints/index.py:155) [index.py:172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/api/v1/endpoints/index.py:172)
- 但发现生产级同类 HIGH：`recover_pending()` 在锁外读取并 `await` 重放，最后才持锁 rewrite/unlink；期间 `_persist_pending(new)` 可以成功追加并返回 `True`，随后新条目被旧快照覆盖或 unlink，结果仍报 `persist_failed=0`。[lancedb_index_service.py:231](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:231) [lancedb_index_service.py:257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:257) [lancedb_index_service.py:267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:267) [lancedb_index_service.py:477](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:477)
- `/tmp/card-g25-recover-race-70bm6liu` 实测：append 返回 `True`、当时文件含新条目；recover 最终返回 `{recovered:1,pending:0,persist_failed:0}`，journal 被删除。故 HIGH-3 总体不能关闭。

2. HIGH-4 收敛口径锁 — STILL-OPEN

- 当前三段真实文本本身正确，明确区分“orchestrator 只覆盖当前部署”和“Lance 没有周期反熵”。[vault_state_paths.py:153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:153) [vault_state_paths.py:222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:222)
- e①只做 `hasattr/default/dir()`；把 `_scan_loop` 改成立即返回仍绿。e②只观察约 `0.04s`；加入 `0.20s` 自动重入后原门仍绿，而延长事件循环能实际观察到重放。[test_g25_journal_namespace.py:708](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:708) [test_g25_journal_namespace.py:727](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:727)
- e③ 的 `(?<!有)没有周期反熵` 可被“是否没有周期反熵”“有 没有周期反熵”绕过；60s 窗口会误放“不是偶尔，而是约60秒内必收敛”，并漏掉“一分钟内必收敛”“60秒内必然收敛”。[test_g25_journal_namespace.py:772](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:772)
- 三条既有篡改样本确实全红，但第一条同时缺少两条前置短语；即使删除整个 60s 检查仍会被别的断言杀死。[test_g25_journal_namespace.py:822](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:822)
- `/tmp/card-g25-high4-r3/test_e_gate_bypasses.py` 共 `8 passed`，证明三道门均存在全绿绕过。

回归检查 HIGH-1 — CONFIRMED-CLOSED：`O_EXCL` 唯一占位及失败清理仍成立；Lance `.jsonl.tmp` 与 `.pre-g25.bak[.N]` 不碰撞。实际触发序列化中途失败得到原 journal 逐字节不变、无 tmp 残片；三条恢复后 unlink 断言仍绿。[vault_state_paths.py:115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:115) [lancedb_index_service.py:287](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:287)

回归检查 HIGH-2 — CONFIRMED-CLOSED：两服务 legacy 路径继续由当前 journal parent 派生，隔离 fixture 的 scope 正确；三文件以 orchestrator 外部开关双保险实跑 `102 passed`，未写 `backend/app/data`。[vault_index_orchestrator.py:349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:349) [lancedb_index_service.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:203) [test_vault_scope_409.py:29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_vault_scope_409.py:29)

(d)⑦(e)③ 死门审查：

| 门 | 裁决 | 对抗复现 |
|---|---|---|
| d① | 有效 | M1/M2 均使①②③ `3 failed`：`/private/tmp/card-g25-high3-m1.HMCsEE`、`…-m2.9Ixw5r` |
| d② | 死门 | 失败后回滚既有字段仍 `26 passed`：`/private/tmp/card-g25-high3-d2rollback.GWuxlt` |
| d③ | 死门 | 503 body 删除四个字段仍 `26 passed`：`/private/tmp/card-g25-high3-d3body.GbBUqv` |
| d④ | 有效 | 当前 bytes M3 使④⑤ `2 failed`：`/private/tmp/card-g25-high3-m3current.5fylCE` |
| d⑤ | 有效 | 同上；旧“调用点不判返回值”不能全绿 |
| d⑥ | 死门 | 坏目录 False、好目录假 True 且零写仍 `26 passed`：`/private/tmp/card-g25-high3-d6conditional.acHCSx` |
| d⑦ | 有效 | 真实 orchestrator、真实落盘及 UTF-8 basename `≤255` 均有断言 |
| e① | 死门 | `_scan_loop` 立即返回仍绿：`/tmp/card-g25-high4-r3/test_e_gate_bypasses.py` |
| e② | 死门 | 延迟 0.20s 自动重入逃过 0.04s 窗口；正控确认实际重放 |
| e③ | 死门 | lookbehind、60s 等价措辞、否定词语义关联及删除检查均有全绿绕过 |

503 消费方：`rg` 在 `frontend` 零命中；`backend/app` 只有路由、服务说明和 metadata 的 410 指引，因此“无活消费方”前提成立。不过 [metadata.py:697](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/api/v1/endpoints/metadata.py:697) 仍声称“前端走 refresh-changed”，是过期注释。

证据引用核对 — PARTIAL：

- M1–M6 的结果文字与 [g25-mutations.txt:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/g25-mutations.txt:3) 相符，且记录 restore true；但其 Lance 摘要是 `720feac…`，当前为 `72745d…`，不能 exact-bind 当前 bytes。
- 当前重跑 g25：`26 passed`；六文件：`60 passed + 6` 个相同存量失败。证据中的 `19 failed/267 passed → 19 failed/277 passed` 也相符，但 post-suite 早于当前 Lance 文件修改。
- §8.3 的真实 journal before/after 没有出现在五个指定 evidence 文件中，无法从限定证据独立复算。
- §8.3 称 grep 计数为 `6`，当前同命令为 `18`；仍满足 `≥4`，但数字不相符。

新问题分级：

- BLOCKER：无。
- HIGH：Lance recovery snapshot/commit 竞态，成功 append 的 durable intent 被静默删除。
- MEDIUM：批处理 `persist=False` 的末次写失败后，`durable_write_failures=1`、error 非空，但 `durable_degraded=false`。[vault_index_orchestrator.py:343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:343) [vault_index_orchestrator.py:623](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:623)
- MEDIUM：变异/post-suite evidence 未绑定当前 Lance exact bytes。
- LOW：metadata 过期消费方注释；§8.3 grep 数字错误。

限制：未跑全量 CI。另一个并行只读轨首次建立 `/tmp` 镜像时误将 `backend/app/data` 复制进临时目录，随即在测试/import 前删除且未查看或输出内容；工作区未被写入，本报告结论不依赖该副本。

BLOCKER/HIGH 清零：否


