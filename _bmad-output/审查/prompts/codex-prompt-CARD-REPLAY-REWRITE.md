# 对抗性代码复核 — CARD-REPLAY-REWRITE（BATCH-2026-09-18-第十五批 / P2-C）

## ① 背景与最小读取面（只读这些，不要全仓扫）

本仓是 Tauri + React + FastAPI 的桌面学习系统。本次改动的主题是 **Story 38.8 回灌算法重写**：
`failed_writes.jsonl` 链（Neo4j 离线时攒下的评分失败条目）从「位置游标 + 快照长度比较 +
试过即成功」重写成「稳定记录身份 + 来源 vault 落盘 + 写完读回执才算成功 + 身份日志崩溃恢复
幂等 + `.overflow.*` 代际扫回」。十四批复核裁定书 §1.8 ④ 的四件硬要求全部落地（G2-2 并入）。

审查绑定：`PREV = a05fa643`，`审SHA = 3d0c4fce`（= 当前 HEAD；其后无代码改动）。

最小读取面（逐条，不要超出）：

1. `git --no-pager diff --no-color a05fa643 3d0c4fce -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动（9 文件）
2. `backend/app/services/fallback_sync_service.py` 改后全段：`_sync_failed_writes` / `_replay_failed_writes_generation` /
   `_filter_confirmed_lines` / `_resolve_entry_source` / `_load_confirmed_ids` / `_persist_confirmed_ids` /
   `_clear_confirmed_ids` / `_replay_scoring_entry_to_neo4j`（含 `_replay_scoring_entry_with_ts` / `_no_ts` 两分支）/
   `_sync_learning_memories`（游标退场）/ `_load_checkpoint`–`_clear_checkpoint` / `_build_group_id_from_canvas` /
   `_canonical_entry_json` / `_legacy_record_id`
3. `backend/app/core/failed_writes_constants.py`：新 `stamp_failed_write_identity` / `serialize_failed_write` /
   `_resolve_stamp_vault_id` / `_stamp_group_id`，与既有 `_replay_in_flight` / `_invalidate_replay_checkpoint` /
   `append_failed_writes_bounded` 全段
4. `backend/app/clients/neo4j_client.py`：新增 `record_score_history_by_record_id`（:1808 起）；
   只读对照 `record_score_history` :1722–1806（一字未改，AST 门已证）
5. `backend/app/services/memory_service.py:502-527`（`_record_structured_outbox`）与 `:2863-2953`（`_flush_pending_failed_writes`）
   —— 卡文引 `:502–522 / :2855–2886` 为 P2-B 前行号，实测见左
6. `backend/app/services/agent_service.py:102-149`（`_record_failed_write`）
7. 两份新测试全文：`backend/tests/unit/test_replay_rewrite_identity.py`、`backend/tests/integration/test_replay_rewrite_7692.py`
8. `backend/tests/unit/test_story_38_8_fallback_sync.py` 与 `backend/tests/integration/test_neo4j_replay_wire_t6b.py` 的 diff
   （对齐新契约的测试数据/断言改动）
9. 判定上下文（只读引用）：`_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` §1.5 A/B、§1.7、§1.8 ④、§二.3

## ② 作者自述 —— 请独立核对，不要采信

1. **位置游标退场后不存在「跳过未确认者」路径**：进度载体 = `sync_confirmed_ids.json` 身份日志
   （键 = 代际文件名 → `[record_id…]`），每条确认后**先记日志再进下一条**；finalize 按身份从该代
   文件里剔除已确认者、剩余原子写回、再清该代日志。崩溃在任一点重启只重试未确认者。
2. **回执比对覆盖 `should_update` 两支**：true 支比对 `score_after` / `group_after` / `ts_equal`；
   false 支要求图上 `ts_after_ts` 确实更新（让位成功）；缺 timestamp 条目走 no-ts 查询
   （`r.timestamp IS NULL` 才写、有值一律不覆盖 —— 不取 `now()`）。
3. **legacy 条目（无 vault_id 且无 group_id）默认隔离**：不写图、留在文件、计 `quarantined`；
   仅 `CLS_REPLAY_LEGACY_NOSCOPE_VAULT` 显式点名才按该值归属。
4. **overflow 代际扫回与写侧 `_prune_overflow` 保留上限的交互不丢数据**：代际只读一次快照 +
   写回前加锁复查存在性（被 prune 删除则不复活）；全部确认 ⇒ `.synced.<ts>`（沿 30 天 retention）。
5. **`neo4j_client` 只新增函数**：`record_score_history` / `initialize` / `_initialize_neo4j_driver` /
   `run_query` 四函数 `ast.dump` 与 `9c4e7e82` 版逐字符相同（AST 门 + 验伪锚已落档）。
6. **终态更正与登记（请核，勿作为新发现重复上报）**：
   - `test_story_38_8_fallback_sync.py` 为**越界改动**（不在 P2 地盘）：只改测试数据/断言对齐新契约，
     函数名集合 30→30；`test_neo4j_replay_wire_t6b.py` 的 `_seed_entry` 补 `record_id`/`vault_id` 对齐新契约（越界 #2）。
   - `_sync_learning_memories` 的**位置游标一并退场**（结构判据要求全文件 0 处游标符号）：该链重放幂等
     （MERGE + last-write-wins）、不写回不轮转 ⇒ 每轮全量重放是安全方向；旧注释历史保留在 git。
   - pyright warnings 80 → 82（新增 2 条均为 `reportUnnecessaryIsInstance` 防御式检查，与基线 80 条同型）；
     0 errors 保持不变。
   - 提交用 `LEFTHOOK_EXCLUDE=python-lint`（被拦文件为 B15_BASE 既有 dirty 集；「改动行零格式漂移」
     逐行判据 PASS 已落档）；`python-typecheck` 未用 LEFTHOOK_EXCLUDE 跳过。

## ③ 按重要性排序的问题（逐项给结论）

- **⓪** 确认日志与文件写回之间任一崩溃点重启是否真幂等（Episode 不重、LEARNED 不丢）？
  负控输入：把「先记日志」改成「finalize 才记」后，崩溃用例必红（已实测）。
- **①** `sha256(规范 JSON)` legacy 身份把「内容相同但语义独立」的两条合成一条是否可接受？
  （对照 `_event_fingerprint` 同型问题；对死信回灌最坏后果是少记一次历史 Episode）
- **②** 缺 `vault_id` 隔离在现网 90 条历史条目上的产品后果（G4-6 迁移前这些条目会一直留在文件里）。
- **③** overflow 代际扫回是否可能重放已被活动文件确认过的同 `record_id`？（写侧超时轮转后
  代际文件名变化 ⇒ 日志键不匹配 ⇒ 可能重放；幂等性由 Episode 的 record_id MERGE 兜底）
- **④** 多进程追加与 `failed_writes_lock`（进程内锁）的边界；确认日志跨进程一致性。
- **⑤** pyright 0 是否靠 `# pyright: ignore` 掩盖？（本卡零新增 ignore）
- **Jev 分诊（urgency 降序，§2.4.3；落 `evidence-replay-rewrite/jev-triage-3d0c4fce.json`）**：

  | 文件 | urgency | risk | verdict |
  |---|---|---|---|
  | `fallback_sync_service.py` | 3.41 | concurrency_state | REVIEW |
  | `failed_writes_constants.py` | 2.95 | api_contract | REVIEW |
  | `neo4j_client.py` | 2.90 | logic | REVIEW |
  | `test_story_38_8_fallback_sync.py` | 2.38 | test_or_docs | REVIEW |
  | `test_replay_rewrite_7692.py` | 2.33 | test_or_docs | REVIEW |
  | `test_replay_rewrite_identity.py` | 2.29 | test_or_docs | REVIEW |

  分诊为文件级信号，问题清单排序请以其 urgency 降序为参考、以你自己的复核判断为准。

## ④ 输出格式

逐条给：

```
[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话结论>
  复现思路：<一句，用下列措辞>
```

措辞请用：**负控输入**（把某处改回旧写法后哪条门会红）、**对照输入**（同族里必须仍绿的那条）、
**未被拦下的输入**（某个取值/顺序/时序没有被现有判据挡住）、**门未覆盖的路径**（代码里没有任何门经过的分支）。

## ⑤ 边界

- **只读**。不要修改任何文件，不要提出需要运行服务或连接数据库的验证步骤。
- 本卡零连库：不要评估任何 Neo4j / LanceDB 连接面；测试门只连 7692 测试容器（不在本审范围）。
- **不在本卡范围，请不要作为发现提出**：`_sync_canvas_events` / `_sync_learning_memories` 两链的算法重写
  （另两链，本卡只做游标退场）；`_event_fingerprint` 的内容合并面；G4-6 的现网迁移（outbox 幂等 ID /
  vault 命名空间 / 90 条历史条目迁移）；`.overflow.*` 的 retention 天数策略。若你认为本卡改动**让这些变得更糟**，
  那属于本卡范围，请明确说出因果链。
- `DEAD_LETTER_STORE_FULL_BODY` 默认值与 live `backend/data/` 真实文件本卡未动（按用户裁定）。
- 前轮（若存在）已处置的发现不必重复；除非你发现终态与所述不符。
