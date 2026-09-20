# 对抗性代码复核 — CARD-REPLAY-REWRITE（BATCH-2026-09-18-第十五批 / P2-C）· round-2

## ① 背景与最小读取面（只读这些，不要全仓扫）

本仓是 Tauri + React + FastAPI 的桌面学习系统。改动主题 = **Story 38.8 回灌算法重写**：
`failed_writes.jsonl` 链从「位置游标 + 快照长度比较 + 试过即成功」重写成「稳定记录身份 + 来源 vault
落盘 + 写完读回执才算成功 + 身份日志崩溃恢复幂等 + `.overflow.*` 代际扫回」（裁定书 §1.8 ④ 四件事，G2-2 并入）。

**round-2（本轮）**：r1 给出 B0 / H2 / M2 / L1；整改 commit `47ebbc21` 落地三处修复（HIGH-1 / MEDIUM-1 /
MEDIUM-2），HIGH-2 以「已登记边界 + 单进程部署证据」提请复核重分类 —— **逐条处置见 §⑥**。

审查绑定：`PREV = a05fa643`，`审SHA = 47ebbc21`（= 当前 HEAD；其后无代码改动）。

最小读取面（逐条，不要超出）：

1. `git --no-pager diff --no-color a05fa643 47ebbc21 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动（9 文件，累计）
2. `git --no-pager diff --no-color 3d0c4fce 47ebbc21 -- . ':(exclude)_bmad-output'` —— **r1→r2 的整改 delta（3 文件）**，重点复核对象
3. `backend/app/services/fallback_sync_service.py` 改后全段：`_sync_failed_writes` / `_replay_failed_writes_generation` /
   `_filter_confirmed_lines` / `_resolve_entry_source` / `_load_confirmed_ids` / `_persist_confirmed_ids` /
   `_clear_confirmed_ids` / `_replay_scoring_entry_to_neo4j`（含 `_replay_scoring_entry_with_ts` / `_no_ts`）/
   `_sync_learning_memories` / `_load_checkpoint`–`_clear_checkpoint` / `_build_group_id_from_canvas` /
   `_canonical_entry_json` / `_legacy_record_id`
4. `backend/app/core/failed_writes_constants.py`：`stamp_failed_write_identity` / `serialize_failed_write` /
   `_resolve_stamp_vault_id` / `_stamp_group_id` 与既有 `_replay_in_flight` / `_invalidate_replay_checkpoint` 全段
5. `backend/app/clients/neo4j_client.py`：新增 `record_score_history_by_record_id`；只读对照 `record_score_history`（一字未改，AST 门已证）
6. `backend/app/services/memory_service.py:502-527` 与 `:2863-2953`；`backend/app/services/agent_service.py:102-149`
7. 两份新测试全文：`backend/tests/unit/test_replay_rewrite_identity.py`（13 条）、`backend/tests/integration/test_replay_rewrite_7692.py`（7 条）
8. r1 存档（只读参照）：`_bmad-output/审查/codex-review-CARD-REPLAY-REWRITE.md`
9. 判定上下文：`_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` §1.5 A/B、§1.7、§1.8 ④、§二.3

## ② 作者自述 —— 请独立核对，不要采信

1. **r1 HIGH-1 已修**：缺 `timestamp` 且带 `score` 的条目现在**整条留待**（不写评分历史、不确认、留在文件计 pending）——
   跳过二次写却确认 = 静默丢历史，与裁定书 §1.8④ 冲突。新单测 `test_no_ts_with_score_stays_pending` +
   gate ⑥ 强化（Episode 数 0 / pending==1 / 文件保留）。
2. **r1 MEDIUM-1 已修**：任一代 `remaining<0`（数不出来）或列举/处理中断 ⇒ 顶层 `pending=-1` + `error`
   （未知不再被算术累加）。新单测 `test_overflow_unreadable_propagates_unknown`。
3. **r1 MEDIUM-2 已修**：`score` 不可转 int（含 NaN / inf）在**任何图写入之前**拒掉 —— 整条留待、其余照常，
   不中断整代。新单测 `test_unconvertible_score_stays_pending_without_blocking_others`。
4. **r1 HIGH-2（多进程）**：当前部署 = **单容器单 uvicorn**（`backend/Dockerfile` CMD 无 `--workers`；
   `docker top` 实测恰 1 个 uvicorn 进程）；该边界已在卡文「本卡未证明」#3、P2-B #13/#17 与
   `_sync_all_lock` docstring 登记为「进程内锁，多 worker / 多进程未覆盖」；修法（文件级锁 / 单飞标志）
   不在本卡范围。请复核：在单进程部署模型下是否降为登记边界。
5. **legacy 内容哈希**（r1 LOW）：接受为 **legacy-only 迁移取舍**；v2 写侧 `stamp_failed_write_identity`
   必生成 `record_id`（uuid4），内容哈希不会成为 v2 的正常兜底。
6. 其余自述同 r1（身份日志顺序 / 回执两支 / 默认隔离 / overflow 不复活 / neo4j_client 只新增 /
   `test_story_38_8` 越界 30=30 / `test_neo4j_replay_wire_t6b` seed 对齐 / `_sync_learning_memories` 游标退场 /
   零新增 pyright ignore / `LEFTHOOK_EXCLUDE=python-lint` 且改动行零格式漂移）。

## ③ 按重要性排序的问题（逐项给结论）

- **⓪** 确认日志与文件写回之间任一崩溃点重启是否真幂等（Episode 不重、LEARNED 不丢）？
- **①** `sha256(规范 JSON)` legacy 身份把「内容相同但语义独立」的两条合成一条是否可接受（限 legacy）？
- **②** 缺 `vault_id` 隔离在现网 90 条历史条目上的产品后果（G4-6 迁移前一直留在文件）。
- **③** overflow 代际扫回是否可能重放已被活动文件确认过的同 `record_id`（幂等兜底是否足够）？
- **④** 多进程与 `failed_writes_lock`（进程内锁）的边界 —— 结合 §⑥.2 的部署证据复核定级。
- **⑤** pyright 0 是否靠 `# pyright: ignore` 掩盖？（本卡零新增 ignore）
- **Jev 分诊 r2（urgency 降序，§2.4.3；落 `evidence-replay-rewrite/jev-triage-47ebbc21.json`）**：

  | 文件 | urgency | risk | verdict |
  |---|---|---|---|
  | `fallback_sync_service.py` | 2.99 | error_handling | REVIEW |
  | `test_replay_rewrite_7692.py` | 1.51 | test_or_docs | pass |
  | `test_replay_rewrite_identity.py` | 1.11 | test_or_docs | pass |

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
- 本卡零连库；测试门只连 7692 测试容器（不在本审范围）。
- **不在本卡范围**：`_sync_canvas_events` / `_sync_learning_memories` 两链的算法重写；`_event_fingerprint`
  的内容合并面；G4-6 的现网迁移；`.overflow.*` 的 retention 天数策略；多进程锁的实现（见 §⑥.2 定级问题）。
- `DEAD_LETTER_STORE_FULL_BODY` 默认值与 live `backend/data/` 真实文件本卡未动。

## ⑥ r1 处置（逐条，请复核整改是否成立、定级是否恰当）

| # | r1 发现 | 处置 | 证据 |
|---|---|---|---|
| 1 | **HIGH** `:923` 缺 ts+score 跳过二次写仍确认（丢历史） | **已修**：整条留待（不写评分历史、不确认、留文件） | 新单测 `test_no_ts_with_score_stays_pending`；gate ⑥ 强化（Episode==0 / pending==1 / 文件保留）；负控段 1b 重跑红在 ⑥ |
| 2 | **HIGH** `:519` 多进程无跨进程互斥（finalize 交错可删新追加） | **提请重分类为登记边界**：单容器单 uvicorn 部署（Dockerfile CMD 无 --workers；docker top 1 进程）；卡文「未证明」#3 + P2-B #13/#17 已登记；修法不在本卡范围 | `backend/Dockerfile:28`；`docker inspect/top` 实测；`_sync_all_lock` docstring |
| 3 | **MEDIUM** `:388` overflow `remaining=-1` 被算术累加（未知伪装成确定值） | **已修**：未知向顶层传播（`pending=-1` + `error`） | 新单测 `test_overflow_unreadable_propagates_unknown` |
| 4 | **MEDIUM** `:930` `int(score)` ValueError 逃逸中断整代 | **已修**：任何图写入前预验 score 可转 int；坏条留待、其余照常 | 新单测 `test_unconvertible_score_stays_pending_without_blocking_others` |
| 5 | **LOW** legacy 哈希合并（不可逆丢历史） | **接受为 legacy-only 取舍**；v2 必带 writer 生成的 `record_id` | `stamp_failed_write_identity`；prompt §②.5 |

承重裁判在 `47ebbc21` 重跑：单测 13 passed / gate 7 passed / 负控 4 段红在指定断言 + RESTORE_VERIFIED /
点名套件 138 passed / t6b 6 passed / pyright `0 errors, 82 warnings` / 改动行零格式漂移 ALL-PASS / 目录级 `tests/regression` 1913 passed rc=0；`tests/unit` 32F/5775P、nodeid 对基线只 `<`、W4 `blocked=0`。
