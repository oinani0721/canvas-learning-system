> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p2-outbox · 卡 CARD-REPLAY-REWRITE round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-REPLAY-REWRITE.md)" > _bmad-output/审查/codex-review-CARD-REPLAY-REWRITE.md 2> _bmad-output/审查/codex-review-CARD-REPLAY-REWRITE.stderr </dev/null`
> 审查绑定: `3d0c4fce`（送审时 HEAD；审后代码零改动，整改 commit 47ebbc21 之后另送 r2）
> 会话头自证（抄 `.stderr`，行号括注；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: glm-5.3`（第 5 行） / `reasoning effort: max`（第 9 行）

---

# 审查结论

**绑定确认**：当前 checkout `HEAD = 3d0c4fceb0f9bcb94ece43b98719caa8546b6c2d`，与指定审 SHA 一致；工作区只有本次审查相关 untracked `_bmad-output/审查/...` 文档，未发现代码 dirty。比较基线为 `a05fa643`。本轮只读，没有修改文件、运行测试、启动服务或连接数据库。

总体判断：**单进程、正常 I/O、带 timestamp 的新 schema 条目主路径基本成立**；身份日志的顺序、finalize 的按身份剔除、活动文件重读、overflow 不复活、legacy 隔离和 Neo4j 旧函数不变性都与实现相符。但 **“缺 timestamp 条目跳过评分历史仍判成功”违反了裁定书 §1.8 ④ 对二次写成功条件的要求**，多进程边界也仍是真实丢数据面。

---

## 发现（按重要性）

```text
[HIGH] backend/app/services/fallback_sync_service.py:923 — 缺 timestamp 且带 score 的条目会在跳过 record_score_history_by_record_id 后被确认并移出队列，评分历史永久丢失。
  复现思路：未被拦下的输入 — 构造 concept/score/vault 均有效但没有 timestamp 与 recorded_at 的条目；no-ts LEARNED 回执通过后，因 “score is not None and ts is not None” 为假直接 return True；删除整段二次写调用后，现有 test_missing_timestamp_does_not_overwrite_newer_score 仍绿，因为它只查 LEARNED 分数，不查 Episode/SCORED，也不查文件是否被轮转。
```

这条与裁定书 §1.8 ④ 的“成功确认条件含 record_score_history 二次写”直接冲突。不能为了补历史而取 `now()`；但当前“确认并删除”同样是不可逆选择。更符合本卡 fail-closed 方向的处理应至少让该输入不确认、留在文件里，或另行明确一个不带事件时间的历史契约。按裁定书描述，现网历史 failed_writes 缺 timestamp 为 0，新写侧又会补 `recorded_at`，所以这不是当前存量主路径；但一旦出现手工/异常写者输入，就是静默丢历史。

```text
[HIGH] backend/app/services/fallback_sync_service.py:519 — 多进程回灌/追加仍没有跨进程互斥，确认日志与 finalize 均可能用旧快照覆盖新追加死信。
  复现思路：未被拦下的输入 — 两个 OS 进程同时 replay 同一 active 文件：进程 B 先重读到 [x]，writer 进程追加 z，进程 A 按确认身份写出 [z]，B 最后用先前快照写出空文件并 rotate；z 被删除；failed_writes_lock、_checkpoint_lock 和固定 .tmp 原子替换都只在本进程内有效，现有测试全部单进程。
```

这不是“确认日志只是可能丢一条无害进度”的边界：两个 finalizer 的 **read → filter → atomic replace** 本身可跨进程交错。并发同一 `record_id` 的 Episode MERGE 也依赖串行执行或外部唯一约束；本卡没有创建约束。若产品明确保证只有一个 FastAPI/backend 进程，这是登记边界；若多 worker、sidecar 与 backend 同时回灌是可能部署，则不能合入为安全结论。

```text
[MEDIUM] backend/app/services/fallback_sync_service.py:388 — overflow 代际读失败返回的 remaining=-1 会被算术累加，active 条数可把“未知”伪装成 pending=0/1。
  复现思路：未被拦下的输入 — 让一个 overflow read/finalize re-read 返回 remaining=-1，同时 active 文件剩 1 条；remaining_total 变成 0，active_error 仍为 None，顶层 pending=0 且无 error；目录列举失败路径更直接把 generations 置空后只报 active。
```

数据文件未被改动，方向仍是不丢，但状态报告违反了该文件自己对 `pending=-1` 的“数不出来”语义。未知值不能与已知剩余数相加；overflow 未知应向顶层传播 `error`/`pending=-1`，或至少阻止把汇总伪装成确定值。

```text
[MEDIUM] backend/app/services/fallback_sync_service.py:930 — score 存在但不可 int() 时会抛 ValueError，逃出当前网络异常捕获并中断整代回灌，后续条目永远被同一条挡住。
  复现思路：未被拦下的输入 — 放入 score="bad" 或 NaN 且 timestamp/vault/concept 均有效的条目；LEARNED 查询回执通过后 int(score) 抛 ValueError，_replay_failed_writes_generation 的 except 只接 RuntimeError/ConnectionError/TimeoutError，因此不写回、不清日志，下一轮在同一输入重复失败；对照输入 score=80 仍全绿。
```

这主要是异常/损坏输入的 liveness 问题，不是当前正常 writer 主路径。但它与“坏 JSON 行保留、不阻塞后续”的处理口径不一致：语法坏行保留，语义坏 score 却能阻断整代。至少应把确定性坏条目保留并继续，或把确定 性转换失败作为可观测的 per-entry failure。

```text
[LOW] backend/app/services/fallback_sync_service.py:134 — legacy sha256(canonical JSON) 会把内容完全相同但语义独立的无身份条目合并为一条，只能作为历史格式的已接受取舍，不能扩展到 schema v2。
  复现思路：对照输入 — 同一代放两条逐字相同的 no-record_id/no-timestamp 历史条目和一条不同条目；现有 test_legacy_hash_dedup_within_generation 必须仍绿且只重放两条不同身份；但两条语义独立的事件也走同一结果，少记一次 Episode。
```

结论：**对 legacy 可接受，但这是损失历史的不可逆合并**。其合理边界来自“旧格式没有稳定身份，无法区分重复写盘与两次独立事件”。新 schema 的身份必须是 writer 生成的 `record_id`；不应把内容哈希继续当成 v2 缺 ID 时的正常兜底来扩大使用。

---

## 对指定问题的逐项结论

### ⓪ 确认日志与文件写回之间的崩溃幂等

**单进程主路径：PASS。**

- 图写入和回执通过后，先把 `record_id` 写入 `sync_confirmed_ids.json`，再处理下一条。
- 图侧Episode 用 `(record_id, group_id)` MERGE；即使确认日志丢失或未写成功，重启后的重复 replay 也不会在串行执行下生成第二个 Episode。
- crash 在“图成功、日志未写”→ 重试，安全；crash 在“日志已写、finalize 未写”→ 重启跳过已确认者；crash 在“部分 finalize”→ 原子替换前旧文件仍在，替换后新文件已剔除已确认者。
- 活动文件重放期间追加的新行不会被初始快照覆盖：finalize 会重新读当前文件，再按身份过滤。

**但两个限定**：

1. 多进程不成立，见 HIGH 第二条。
2. “不会重放已确认者”在 active 被写侧超时轮转时不严格成立，见 ③；不过串行 replay 有 Episode MERGE 兜底。

### ① legacy 内容哈希合并

**有条件接受：只接受为 legacy 迁移期取舍。**

`sort_keys + compact JSON` 使键序不同但内容相同的行得到同一身份，符合实现意图。最坏后果是两条语义独立的完全相同历史事件只记一次 Episode。因为旧格式没有可辨别的请求/事件身份，无法完全修复；不应据此影响新 v2 条目。新 writer 正常总会生成 UUID `record_id`。

### ② 无 vault 历史条目的产品后果

**行为与作者描述一致：默认隔离，不写错 vault。**

`_resolve_entry_source()` 在无 `group_id`、无有效 `vault_id`、未设置 `CLS_REPLAY_LEGACY_NOSCOPE_VAULT` 时返回 `quarantined`，条目保留并计入 pending。按裁定书上下文，存量无 scope 条目会一直留在文件中，直到显式 env 归属或后续迁移；不会因本卡被猜测写入当前 active vault。

需要区分：有 `vault_id` 但无 canvas/path 的条目是 `unresolvable`，不计 `quarantined`；其中 knowledge_entity/no-concept 条目本来就有裁定书 §1.9 登记的永久 pending 问题，本卡没有使其变好或变坏，我不作为新发现重复上报。

### ③ overflow 扫回与 active 轮转/保留上限交互

**处理期间被 prune：PASS，不复活。** overflow finalize 前在 `failed_writes_lock` 下复查文件存在性；被删除则直接清该代日志，不把旧快照写回。

**active 超时轮转：可能重放已确认者，但串行安全性 PASS。** 时序是：

1. replay 以 `failed_writes.jsonl` 为 generation 记录确认日志；
2. 写侧超过 replay window 后把旧 active 轮转为新的 `.overflow.*.jsonl`；
3. replay finalize 看到的是新 active，最后清掉 `failed_writes.jsonl` 这个日志键；
4. 下一轮以新的 overflow 文件名扫描，会再次 replay 旧确认条目。

这不满足字面上的“绝不重放已确认者”，但 LEARNED 是 MERGE，Episode 也按 `record_id` MERGE，因此串行结果是幂等的。多进程下仍受前述并发 MERGE/finalize 风险影响。

保留上限本身仍可能在回灌前删除未回灌 overflow，这是既有 bounded-retention 取舍，不是本卡新增因果链；本卡只是开始扫描仍存在的 overflow，方向上没有变差。

### ④ 多进程与进程内锁边界

**单进程：PASS。** writer/replay 共用 `failed_writes_lock` 做 active 初读与 finalize，`_sync_all_lock` 防同进程并发整次回灌；重读后按身份过滤也能保留追加项。

**多进程：FAIL/未覆盖。** `threading.Lock`、`asyncio.Lock`、固定 `.tmp` 和确认日志 read-modify-write 都没有 OS-level file lock 或唯一临时名。两个 finalizer 可交错覆盖新追加死信；确认日志也可能互相丢失，虽然图侧 idempotence 可降低后果。该边界必须显式登记为 unsupported，或补跨进程锁。

### ⑤ pyright 是否靠 ignore 掩盖

**本卡改动面未发现新增 ignore。** 静态检查显示：

- `neo4j_client.py` 当前与 PREV 均为 0 个 `# pyright: ignore`。
- `fallback_sync_service.py`、`failed_writes_constants.py`、`agent_service.py`、两份新测试均为 0。
- `memory_service.py` 有既有 `# pyright: ignore[reportAttributeAccessIssue]` 两处，但不在本卡 diff。

我没有运行 pyright，因此不重新证明 “0 errors / 80→82 warnings”；只能确认作者声称的“零新增 ignore”与 diff 一致。

---

## 作者自述核对

| 自述 | 结论 |
|---|---|
| failed_writes 位置游标退场，不跳过未确认者 | 单进程 PASS；active 轮转可能冗余 replay，多进程不安全 |
| true/false 回执两支覆盖 | timestamp 主路径 PASS；no-ts 分支漏二次历史并确认，HIGH |
| legacy 无 scope 默认隔离 | PASS |
| overflow 代际扫回、prune 后不复活 | PASS；但 unknown remaining 聚合失真，MEDIUM |
| Neo4j 只新增函数，四个旧函数 AST 不变 | PASS；我用 `ast.dump` 比较 `record_score_history` / `initialize` / `_initialize_neo4j_driver` / `run_query`，均与 `a05fa643` 相同 |
| `test_story_38_8_fallback_sync.py` 越界但函数集合不变 | PASS；AST 统计 test 函数 30 → 30，集合相同 |
| `_sync_learning_memories` 游标退场 | PASS；该链不再调用 `_load_checkpoint`/`_save_checkpoint`，结束时清旧 checkpoint。文件里仍有 canvas 链自己的 `still_pending`，但那是另一链算法，不按本卡评 |
| 本卡零新增 pyright ignore | PASS |

**总裁定建议**：不认为单进程正常路径需要整体推翻，但 **no-ts 二次写缺口应先修或明确改裁**；多进程若非明确 unsupported，也应先加跨进程互斥。其余两条 MEDIUM 可作为后续整改而不是阻塞当前主路径。
