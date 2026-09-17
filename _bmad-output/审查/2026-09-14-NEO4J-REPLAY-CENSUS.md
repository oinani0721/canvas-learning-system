# CARD-NEO4J-REPLAY-CENSUS — Neo4j 离线暂存链零代码普查

> 批次: `BATCH-2026-09-11-第十四批` · 车道 T6（`card-t6-neo4j` / 分支 `card/t6-neo4j`） · 本车道第 1/3 张
> 绑定: `B14_BASE` = `081004834e37b1b0253cf81dc7b44e784646c934`（`08100483`），census 期间工作树代码零改动
> 定性: **零代码纯只读**（`grep` / `sed` / `nl` / `git grep` / `git show`，不连库、不起 lifespan、不写 live vault）
> 上游: R-09（U11-A 离线韧性审计）· 审计原文 `…/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-resilience-audit/VERDICT-merged-2026-09-09.md`
> 下游: T6-B `CARD-NEO4J-REPLAY-WIRE`（接通面） / T6-C `CARD-NEO4J-REPLAY-BOUND`（有界 + 可观测面）
> 全部证据: `_bmad-output/审查/evidence-neo4j-replay-census/`（34 组判据逐条落盘，`.txt` 后缀）
>
> **版本**: v2（Codex round-1 复核后修订）。v1 的 12 处事实错误由 Codex 指出、本卡逐条独立实测确认，
> 另 11 处由作者自查发现；两类来源在 §九 逐条标注。**修订为纯文档改动，代码零改动**（D-32 不重置轮次）。

---

## §零 第 0 分钟自证与判读口径

| 项 | 实测 |
|---|---|
| `pwd` / 分支 / `HEAD` | `…/worktrees/card-t6-neo4j` / `card/t6-neo4j` / `08100483`（full `081004834e37b1b0253cf81dc7b44e784646c934`） |
| `git status --porcelain \| wc -l` | `0`（开工时） |
| venv / `.env` / pyright | 均在位 |
| 红基线 `grep -vc '^#' $BASE` | **64**（`…/evidence-b14/unit-red-baseline-08100483.txt`） |

存档: `step0-selfcheck-20260914T195007.txt`

### 判读口径声明（全文适用）

1. **rc 与 stdout 分开判读**。形如 `git grep … | grep -v '/tests/'` 的判据，记录的 `rc_gitgrep` 是**管道首段**退出码（表示「全仓有无命中」），**不表示过滤后是否为空**。凡结论为「非测试零命中」，判据一律是 **stdout 为空**。
2. `rc=141` = `128 + SIGPIPE(13)`，由 `| head -n` 提前关管道产生，**不是失败**。
3. 每条 census grep 旁带**同次验伪锚**（先证该 grep 能命中一条已知正例）。
4. grep/git 输出一律 `--no-color`。
5. **⚠️ v1 教训（已改正）**：读函数体不得用固定行数窗口（`sed -n "n,n+42p"`）——v1 判据 16c 的窗口恰好切在 `events.append(event)`，漏掉紧接的三行截留逻辑，导致链 5 有界性结论错误。v2 全部改用 `nl -ba` + 按语义边界定位。

---

## §一 暂存链总表（写侧 / 读侧 / 回灌 / 有界）

> **链数沿革（诚实标注归属）**：卡文 §〇 列 4 条 + 第 5 条；**U11 审计 §2.1–2.6 已列 6 条**（含 `learning_memories.json`）；
> 本卡补第 7 条 `failed_dual_writes.jsonl`；**Codex round-1 指出第 8 条候选** `outbox/events.jsonl`（判据 19 的三种路径拼接形态覆盖不到的变量拼接）。
> ⇒ 当前为 **7 条暂存链 + 1 条已接通对照链**，且**不宣称是全集**（见 §八）。

| # | 文件 | 写侧 | 读侧 | 回灌 | 有界 |
|---|---|---|---|---|---|
| 1 | `backend/data/neo4j_memory.json` | ✅ `neo4j_client._save_json_data` def `:475`，**六个调用点** `:463/:751/:1778/:1987/:2202/:2341`；降级入口 `_fallback_to_json:421`（初始化失败 `:408/:413/:418`、中途降级 `:628/:636`） | ✅ **有运行时读**：`:447-449` 初始化载入 `_data`、`:915` 降级查询读 `_data`。**无自动回灌 Neo4j** | ❌ **从未存在**（U11 §2.2：`fallback_sync_service` 三文件清单不含它） | ⚠️ 无容量淘汰；但**非严格单调增长**（`:2197-2202` 删除 association 后覆写） |
| 2 | `backend/data/dead_letter_episodes.jsonl`（相对 CWD `data/…`） | ✅ `DeadLetterStore.store:233` 追加；三调用点 `:641/:655/:658`。⛔ **触发前提**见 §二.2 | ❌ **假读侧**：`traces.py:23` 读的是 `backend/app/data/…`，与写路径不同（§二.4）；即使同路径，`request_id` 仅半数通道落盘 | ❌ **从未存在**；且**不可从死信自重放**（默认仅存 `episode_body[:200]`，`:107`） | ❌ 零轮转 |
| 3 | `backend/data/failed_writes.jsonl` | ✅ **三个写者**（§二.3）：`agent_service._record_failed_write` def `:98`/落盘 `:130`；`memory_service._record_structured_outbox` def `:502`/落盘 `:516`/调 `:1665`；`memory_service._flush_pending_failed_writes` def `:2854`/落盘 `:2872`（累积 `:1422`，仅 `cleanup()` `:2845-2846` 刷） | ⚠️ `load_failed_scores` def `:2793`/实调 `:802`，但**UI 实际多半看不见**：entry 无 `user_id`（`agent_service:117-127`），而 `:805-806` 在 `user_id` 非空时按它过滤 | ⚠️ **两个孤儿，且能力不等价**：`recover_failed_writes:2687`（有 `knowledge_entity` 分支 `:2735`）、`_sync_failed_writes:113`（`:146` 统一走评分 helper，`:314/:319-321` 无 `concept` 即 `return False`） | ❌ 清理代码全在孤儿体内 ⇒ 永不执行 |
| 4 | `backend/data/failed_edge_syncs.jsonl` | ✅ `canvas_service.py:508-516` `write_dead_letter(EDGE_SYNC_DEAD_LETTER_PATH, …)`（带 `request_id`）。**实测该文件存在**（车道树 763 B） | ❌ **假读侧**：写 `backend/data/`（`failure_counters:25`，`.parent`×3）vs 读 `backend/app/data/`（`traces.py:17`，`.parent`×4）——**读路径目录实测不存在** | ❌ **零消费者**；且**死信字段不足以重放**（缺 `from_node_id`/`to_node_id`/`edge_label`，§二.6） | ❌ 零轮转 |
| 5 | `backend/app/data/canvas_events_fallback.json` | ⚠️ 六处门 `:266/:363/:443/:460/:989/:998`（形态逐字一致），**写调用在门下一行** `:267/:364/:444/:461/:990/:999` | ❌ 无 UI 读 | ⚠️ 孤儿 `_sync_canvas_events:193` | ✅ **写侧已有条数上限**：`_max_fallback_events = 10000`（`:97`），`:164-166` 每次追加后截留最后 10000 条、`:171` 覆写，**不依赖回灌**。⚠️ 条数有界 **≠ 字节有界**（单条事件大小无限制） |
| 6 | `backend/data/failed_dual_writes.jsonl` | ❌ **当前源码无生产写入接线**（`DUAL_WRITE_DEAD_LETTER_PATH` 非测试仅定义处 `failure_counters:27-29`） | ❌ 无 | ❌ 无 | — 文件当前不产生（**不等于历史上从未产生**，Codex 限定） |
| 7 | `backend/data/learning_memories.json` | ✅ `LearningMemoryClient._save_data:817-823`（全量原子覆写） | ✅ **运行时查询源**：`:794-796` 初始化读文件、`:892`/`:955` 查内存；`dependencies.py:222/:231` 注入、`agent_service.py:4998` 写 / `:2087` 查 | ⚠️ 孤儿 `_sync_learning_memories:255` | ⚠️ **设计上不轮转**（`fallback_sync_service:297-298` 注释声明理由） |
| 8* | `backend/data/outbox/events.jsonl`（**对照组：唯一已接通**） | ✅ `event_bus.py:263`（熔断 OPEN）/ `:303`（重试耗尽）→ `_write_outbox:342`；路径 `:47-49` 变量拼接。**实测存在**（383 B） | ✅ `recover_outbox:368` | ✅ **真实接线** `main.py:216`（`:212-219`） | ❌ 无容量/年龄上限 |

> **第 8 条的限定（Codex MEDIUM-7，本卡采纳）**：已证明生产注册与启动恢复入口存在；**未证明**单纯 Neo4j 断连一定沿活跃 handler 写入该箱（部分下层会降级到其他链）。故登记为**候选 + 对照范式**，不宣称「已证第 8 条离线写活链」。U11 另实测其覆盖缺口：`_dispatch_tier1` 只 `raise` 从不写 outbox，而 `SCORE_SUBMITTED` 是 `TIER_1_CRITICAL` ⇒ 评分事件结构上永不进 outbox。

### §一.1 逐链 U11 审计条目对应（卡文 (b) 要求，引条目名不引行号）

| 本卡链 | U11 条目 |
|---|---|
| 链 1 | §2.2（回灌器从未存在；三文件清单不含它） |
| 链 2 | §2.4（写者活但只在 worker 已就绪后触发 ⇒ 不覆盖「启动时离线」头号场景；残片重放不出原始内容） |
| 链 3 | §2.1 + §4.1（「没人回灌」为真、「没人读」为假） |
| 链 4 | §2.3（零重放；边可由别的路径从 markdown 重建，但不是靠这个文件） |
| 链 5 | §2.5（本机双向断；按 example 部署则写活读死） |
| 链 6 | **U11 未列 ⇒ 本卡新增** |
| 链 7 | §2.6（常态旁路存储，不是失败兜底；回灌器孤儿） |
| 链 8* | §1 链 E（唯一活着的「暂存 ↔ 启动重放」闭环） |
| 启动回填门 | §3 S1（`_worker_graphiti is None` ⇒ 回填被跳过；且无自愈，须重启进程） |

---

## §二 逐链要点

### §二.1 孤儿不是「从未接线」，是「曾接线、被摘除」（判据 25）

`git show 59586af1 -- backend/app/main.py`（2026-03-26 09:30:14，`refactor(phase2): delete fake bridge/JSON dual-write code, replaced by GraphitiEpisodeWorker`）删除行逐字包含：

```
-    # ✅ Story 38.8: Sync all JSON fallback files to Neo4j on startup
-        from app.services.fallback_sync_service import get_fallback_sync_service
-        sync_svc = get_fallback_sync_service()
-            sync_svc.sync_all_fallbacks(), timeout=60.0
-                f"[Story 38.8] Fallback sync skipped: {sync_result.get('reason')}"
-            "[Story 38.8] Fallback sync timed out (60s), will resume next startup"
-        logger.warning(f"[Story 38.8] Fallback sync failed (non-fatal): {e}")
-        logger.warning("JSON fallback is disabled. Neo4j outage will cause data loss.")
```

同日 `daa9fd37`（09:35:00，5 分钟后）改 `config.py`：`default=True` + `"safe default for Neo4j offline resilience"` → `default=False` + `"[DEPRECATED] …"`。

⇒ **写侧默认关 + 重放摘除 + 离线告警删除，同一天 5 分钟内三件齐活**（U11 §1 末判断，本卡逐字复证）。
⇒ 措辞必须区分：`sync_all_fallbacks` / `recover_failed_writes` = **曾接线，2026-03-26 被摘除**；链 1/2/4 的重放 = **从未存在**。
⇒ 对 T6-B：接通是**还原**而非新设计，原始形态含 `timeout=60.0` 与 skipped/timeout/failed 三分支，可作实现基线。

### §二.2 链 2 的死信在「头号场景」里连写都不发生（判据 22，U11 §2.4）

`_handle_failure` 唯一非测试调用点 `episode_worker.py:555`（worker 处理循环内）；`is_ready = self._started and self._graphiti is not None`（`:524-526`）；初始化失败时 `self._graphiti = None`（`:376`/`:434`）。
⇒ 死信只在 **worker 已就绪且处理任务失败**时才写。**「Neo4j 启动时离线」这个头号场景根本走不到死信**（worker 未 start、队列不消费）。
⇒ 链 2 不只是「无回灌」，而是**在最需要它的场景里连暂存都没有**。

`request_id` 来源（判据 15）：`DeadLetterStore.store` 的 kwarg 三个调用点**都不传**；真正来源是 `record = {**task.to_dict(), …}`（`:114-115`）。两个生产创建点：`memory_service.py:470-478` **传** `request_id=_ctx.get("request_id")`；`tips.py:623-633`（callout 直投）**不传**（该文件全文零 `request_id`）。无创建后赋值。

### §二.3 链 3 有三个写者，其中一个根本不落盘（判据 21）

| 写者 | 位置 | 性质 |
|---|---|---|
| 1 | `agent_service._record_failed_write` def `:98` / 落盘 `:130` / 调 `:5084` `:5100` | 评分写失败，立即落盘 |
| 2 | `memory_service._record_structured_outbox` def `:502` / 落盘 `:516` / 调 `:1665` | 结构化 outbox（`kind=knowledge_entity`），立即落盘 |
| 3 | `memory_service._flush_pending_failed_writes` def `:2854` / 落盘 `:2872` | ⛔ **内存队列**（累积 `:1422`，字段 `:273`），**仅 `cleanup()` `:2845-2846` 刷盘 ⇒ 进程被 kill 即全丢** |

⇒ 写者 3 的数据**接通回灌也救不回来**（压根没落盘），属 T6-B/T6-C 之外的**第三类缺口**。

**两个回灌器能力不等价（Codex HIGH-2，实测确认）**：`_sync_failed_writes:146` 把**所有**条目交给 `_replay_scoring_entry_to_neo4j`，而该 helper `:314` 取 `concept/concept_id`、`:319-321` 取不到就 `return False`。写者 2 产出的结构化条目（`event_type`/`content`/`metadata`/`group_id`）**没有这两个字段** ⇒ 被静默跳过、永远 `still_pending`。只有旧 `recover_failed_writes:2735` 有 `if entry.get("kind") == "knowledge_entity"` 分支。
⇒ ⛔ **T6-B 只接 `sync_all_fallbacks` 不足以覆盖链 3**。

**「UI 可见」需限定（Codex HIGH-2 后半）**：`agent_service:117-127` 的 entry 九字段无 `user_id`；`memory_service:805-806` 在查询携带非空 `user_id` 时按该字段过滤 ⇒ 这些条目**被过滤掉**。故 U11 「没人读为假」在本精度下应表述为：**读侧代码存在且被调用，但对携带 user_id 的查询实际不可见**。

### §二.4 `/traces` 与死信写侧路径错位（Codex HIGH-4，实测确认）

| | 路径表达式 | 解析结果 |
|---|---|---|
| 写（链 4） | `failure_counters.py:25` `Path(__file__).parent.parent.parent / "data" / …` | `backend/data/failed_edge_syncs.jsonl`（**实测存在，763 B**） |
| 读（traces） | `traces.py:17` `Path(__file__).parent.parent.parent.parent / "data"` | `backend/app/data/failed_edge_syncs.jsonl`（**实测目录不存在**） |

⇒ `/traces` 对 `failed_edge_syncs` 与 `dead_letter_episodes` 的查询**恒空**，原因是**路径错位**，与 `request_id` 无关。
⇒ 链 2 同样需登记路径条件：`episode_worker.py:306` 是相对 CWD 的 `data/…`，从 `backend/` 启动时 = `backend/data/…`，与 traces 读的 `backend/app/data/…` 仍不一致。

### §二.5 链 5 的有界性：写侧本来就有（Codex HIGH-1，推翻 v1 结论）

`canvas_service.py:97` `self._max_fallback_events: int = 10000`；`:164-166`：

```python
# [Review M2] Truncate oldest events when exceeding max limit
if len(events) > self._max_fallback_events:
    events = events[-self._max_fallback_events :]
```

⇒ **条数有界，且不依赖回灌**。v1 说「有界机制全部在孤儿体内」**错误**，根因是判据窗口切在 `:162 events.append(event)`。
⚠️ 仍存在的问题：**条数有界 ≠ 字节有界**（单条事件大小无上限）；写侧是 **read-all → append → truncate → write-all** 全量重写，随事件数增长有写放大。
孤儿 `_sync_canvas_events:193-249` 内另有 checkpoint / `_rotate_file:545` / `_cleanup_old_synced_files:563`（保留 30 天）——这层是**回灌后清理**，与写侧上限是两回事。

### §二.6 链 4 的死信不足以重放（Codex HIGH-6，实测确认）

真实同步调用 `canvas_service.py:481-487` 需要 `canvas_path` / `edge_id` / **`from_node_id`** / **`to_node_id`** / **`edge_label`**；
落盘 `:508-516` 只写 `edge_id` / `canvas_name` / `retry_count` / `request_id`。
⇒ 缺三个必需字段；且源 Canvas 若已修改或删除，也无法回源重建原失败操作。

### §二.7 链 2 的「回源重生成」不适用于全部死信（Codex HIGH-5，实测确认）

`memory_service.enqueue_conversation_archive:481-500` 投递 `conversation_text`（会话正文，来源 `endpoints/memory.py` 的请求消息，**不在 vault markdown 里**）；死信仅留前 200 字（`episode_worker.py:107`）。
`vault_backfill.py:195-213` 只遍历现存 `*.md` 的 `callouts` + `relationships`，`if not callouts and not rels: continue`。
⇒ 启动回填**恢复不了会话全文类 episode**。链 2 的处置不能统一断言「可回源」。

### §二.8 链 6 是死代码

`DUAL_WRITE_DEAD_LETTER_PATH` 非测试命中仅定义处；唯一「集成测试」`test_failure_observability.py::TestMemoryServiceDualWriteFailure`（`:267`）整类被 `@pytest.mark.skip`（`:263`），reason 自述所测的 `MemoryService._write_to_graphiti_json[_with_retry]` 两方法**均已删除**（判据 13c 非测试 stdout 为空）——这解释了它为何不在 64 条红基线里。该类里 `patch("app.services.memory_service.DUAL_WRITE_DEAD_LETTER_PATH", …)` 的目标在 `memory_service.py` 中全缺席，即便解开 skip 也会 AttributeError。
**限定**：结论限于当前源码，**不能据此证明历史上从未产生过该文件**。

### §二.9 链 7 不可轮转（Codex LOW-12 修正表述）

`fallback_sync_service.py:297-298` 注释原文：

```
# NOTE: learning_memories.json is NOT rotated - still needed by
# LearningMemoryClient for runtime queries.
```

准确机制：`neo4j_edge_client.py:794-796` **初始化时**读文件入内存，`:892`/`:955` 查的是内存。
⇒ 轮转**不会立即清空已初始化实例**；但重新初始化时文件缺席，`:800-808` 会创建空存储，**旧记录就此退出运行时查询**。
⇒ ⛔ 对链 7 施加轮转 = 下次重启后运行时数据消失。
（`format_for_context:966-968` 只格式化**传入的 list**，不读文件——v1 把它列为读侧不准确。）

---

## §三 两孤儿重放器：零非测试调用方实证

判据采用**调用形态枚举 + 全命中逐条归类 + 验伪锚**，不用计数。

### §三.1 `recover_failed_writes`（`memory_service.py:2687`）

| 枚举 | 结果（非测试） |
|---|---|
| `(await \|\.)recover_failed_writes\(` | **stdout 空** |
| 裸 `recover_failed_writes(` | 仅 def `:2687` |
| `getattr\([^)]*recover_failed_writes` | stdout 空 |
| `['"]recover_failed_writes['"]` | 仅测试 2 处 |

**全命中归类（非测试 3 行）**：`failed_writes_constants.py:6`（注释）/ `memory_service.py:506`（注释）/ `:2687`（def）。无一是 call。测试侧有 13 处真实 call。
**验伪锚**：`_record_structured_outbox` 命中 `memory_service.py:1665` ⇒ 枚举非恒空。
（⛔ 未用 `load_failed_scores` 当锚：`:802` 是 `to_thread(self.load_failed_scores)`，名字后是 `)` 不是 `(`。）

### §三.2 `sync_all_fallbacks`（`fallback_sync_service.py:53`）与工厂（`:656`）

| 枚举 | 结果（非测试） |
|---|---|
| `(await \|\.)sync_all_fallbacks\(` | 仅 `memory_service.py:2690`（docstring） |
| 裸 `sync_all_fallbacks(` | 仅 def `:53` + 上述 docstring |
| `get_fallback_sync_service\(` | 仅 def `:656` |
| `FallbackSyncService\(` | 仅 `:661`——**工厂自身内部**，而工厂零 call |

`gateway.py` 不构成调用路径：`domains/canvas/gateway.py` 全文 29 行纯 re-export（`:19` import + `:27` `__all__`），且**零 import 者**（`-e` 多模式实测 rc=1；验伪锚 `from app.services.memory_service` 命中多处）。
> ⚠️ 该判据首次误用 `'a\|b'` BRE 交替（本机不保证解释为交替 ⇒ 假阴性），已改 `-e` 多模式重跑，本文采信重跑结果。

**Codex 独立核对结论（round-1）**：「两个指定重放器及工厂在当前生产源码没有调用或方法引用」**核对通过**（其做法为全标识符归类 + 只解析不导入的 AST 检查）。同时限定：`(await |\.)<name>\(` 正则**不具通用完备性**（会漏裸调用、保存方法后经别名调用、括号包装及部分动态拼接）；当前未发现这些目标函数的漏网调用。

### §三.3 独立佐证：两条常驻红测试（U11 已指出，本卡复测并量化）

`tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration`（`:438`）两条用例读 `main.py` 源码做字符串断言（`:440` / `:447`）。实测 `main.py` 中 `get_fallback_sync_service` / `sync_all_fallbacks` / `recover_failed_writes` **三名全缺席**（验伪锚 `backfill_vault` 命中 `:384/:392`）。

> **归属**：U11 审计 §1 已指出这两条「**必红**，是『删除未收口』的现成红契约锚，只是没人把红转成结论」。
> **本卡贡献**：在 `B14_BASE` 复测确认 + 定位到红基线**第 51/52 行** + 给出量化验收锚。

⇒ **T6-B 的现成验收锚**：接通 lifespan 后这两条应自动转绿，`tests/unit` 红基线 **64 → 62**，无需另造门。

---

## §四 启动回填门（本卡只登记，不改 `main.py`）

| 锚 | 实测 |
|---|---|
| `_worker_graphiti = getattr(get_episode_worker(), "_graphiti", None)` | `:386` |
| `if _worker_graphiti is not None:` | **`:387`**（勘探/设计稿写 `:386` ⇒ 定位更正） |
| `bf = await backfill_vault(` | `:392`（`execute=True`） |
| `else: logger.info("[Graphiti-native] 启动回填跳过 (graphiti 未就绪)")` | `:404` |
| `except Exception as e:` | `:405-406`（整个回填块的异常处理） |

**语义**：Neo4j 离线 ⇒ `_graphiti` 为 None ⇒ `:387-404` 整段跳过 ⇒ 源在 vault markdown 的回填也不发生，`:404` 只打一行跳过日志，不留待办痕迹。

> ⚠️ **口径澄清（Codex MEDIUM-9，v1 表述错误）**：「门在 `:387`」是**定位事实**，**不等于** T6-B 的可改范围就是 `:387-404`。
> `:386` 的取值被 `:394-395` 使用，`:405-406` 是整块的 `except`。本卡证据**既不能断言**这些外围行必须改，**也不能排除**它们。
> ⇒ 移交主 session：设计稿 §3 的地盘声明应按**实际 hunk** 核定，而非据本条更正机械收窄。

---

## §五 双写开关二态（只读；⛔ 未读现网 live vault 的 `.env`）

| 位置 | 原文 | 态 |
|---|---|---|
| `backend/app/config.py:477-479` | `ENABLE_GRAPHITI_JSON_DUAL_WRITE: bool = Field(` / `default=False,` / `description="[DEPRECATED] …"` | 字段默认 **False** |
| `backend/.env:85` | `# ENABLE_GRAPHITI_JSON_DUAL_WRITE=true` | **注释态** |
| `backend/.env.example:226` | `ENABLE_GRAPHITI_JSON_DUAL_WRITE=true` | **生效赋值** |
| `backend/app/config.py:943` | `SettingsConfigDict(env_file=".env", …, case_sensitive=True, extra="ignore")` | 装载口径 |

**结论（二态，方向相反）**

- **态 1 — 本机（用 `backend/.env`）= 关**：走字段 default `False` ⇒ `canvas_service` 六处门走 `else` 只打日志 ⇒ 链 5 连暂存都不写（离线期数据直接丢）。
- **态 2 — 按 `.env.example` 部署 = 开**：`True` ⇒ 链 5 写活，回灌在孤儿身上 ⇒ 写活读死（但写侧有 10000 条上限，见 §二.5）。

> ⚠️ **前提限定（Codex MEDIUM-8）**：以上从「`.env` 该行被注释」推出「进程变量未设」是**推论不是实测**。
> `config.py:943` 的 `env_file=".env"` 是**相对 CWD**；`:1066-1072` 的 `reload_settings` overrides 会写进程环境；
> pydantic-settings 的来源优先级是「构造参数 → 进程环境 → dotenv」。
> ⇒ 结论须附条件：**「在实际装载了该 `.env` 且无更高优先级覆盖的前提下」**。

### §五.1 第三态排查：运行时**无第三态**，但有三项衍生隐患（登记，不修）

| 候选 | 判定 | 依据 |
|---|---|---|
| 六处 `getattr(settings, …, True)` 的 `True` 回落 | **不构成第三态** | 字段已定义（`:477`）⇒ 属性恒存在；`:961` 始终构造 `Settings()`，`reload_settings` 仍走该路径，`extra="ignore"` 不删除已声明字段（Codex 核对通过）。**隐患**：与 default=False 方向相反，字段若被删会静默翻 True |
| 小写 alias property `:928-930` | **不构成第三态** | 同值。**隐患**：`case_sensitive=True` + `extra="ignore"` ⇒ 按 alias 名写小写 env **既不报错也不生效** |
| 测试契约分裂 | **非运行时态，但误导** | `tests/e2e/test_epic36_integration.py:316` 断言 `is True`（注释引旧行号 `config.py:419`）；`tests/unit/test_story_38_4_dual_write_default.py:46` 断言 `default is False`。两者不可能同真；unit 绿、e2e 不在门下 |
| **热重载引用残留**（Codex 补充） | **登记** | `canvas_service.py:37` 持有旧 settings 实例，重绑 `config.settings` 不自动更新它 |

---

## §六 处置表（接通 / 退役）— 交 T6-B / T6-C

> **决策项声明**：接通 vs 退役由 T6-B / T6-C 落地，**本卡只出清单与依据**，不做产品裁定、不改任何代码。

| # | 链 | 建议处置 | 依据 / 前置风险 |
|---|---|---|---|
| 3 | `failed_writes.jsonl` | **接通，但只接 `sync_all_fallbacks` 不够** | 写侧在产生数据；⛔ 新回灌器会跳过写者 2 的结构化条目（§二.3），须同时接 `recover_failed_writes` 或给新回灌器补 `knowledge_entity` 分支；⛔ 写者 3 根本不落盘，回灌救不回 |
| 5 | `canvas_events_fallback.json` | **接通**（仅态 2 有数据） | 写侧已有条数上限；回灌后清理在孤儿体内 |
| 7 | `learning_memories.json` | **接通回灌，⛔ 绝不轮转** | 双职能：轮转后下次重启运行时数据消失（§二.9） |
| 2 | `dead_letter_episodes.jsonl` | **不从死信自重放**；观测 + 有界为主 | 默认仅 200 字残片；⛔ 回源重生成**仅适用于 markdown 来源**，会话归档类不适用（§二.7）；⛔ 头号场景连写都不发生（§二.2） |
| 4 | `failed_edge_syncs.jsonl` | **不宜按现状接回灌**（决策项） | ⛔ 死信缺 `from/to/label` 三字段，不足以重放（§二.6）；要接须先补写侧字段 |
| 1 | `neo4j_memory.json` | **保留为镜像，不接自动回灌**（决策项） | 是镜像存储 + 运行时读源，非事件队列；已有手动迁移工具 |
| 6 | `failed_dual_writes.jsonl` | **退役 或 明确接线**，二选一 | 当前零写侧接线 + 唯一测试被 skip 且所测方法已删 |
| 8* | `outbox/events.jsonl` | **不动**（对照范式） | 唯一已接通闭环，T6-B 可照抄 `main.py:212-219` 形态 |

### §六.1 ⛔ 给 T6-B / T6-C 的四条硬前置

**P1 —「接通」不等于「有界」，且有界不能只靠回灌。**
`sync_all_fallbacks:64-65 / :70-71 / :73-74` 三处早退：`is_fallback_mode` → `skipped`；health check 异常 → `skipped`；`not healthy` → `skipped`。
⇒ **Neo4j 不可用时一行都不清理**，而离线期正是坟场增长期。链 5 的写侧上限（`:97` / `:164-166`）是目前**唯一**在离线期仍生效的有界机制——其余链需比照它在写侧实现，而非依赖回灌后 `_rotate_file`。

**P2 — ⛔ 跨 vault 归属风险（接通即触发）。**
`fallback_sync_service.py:623-625` 代码自陈：

```
⛔ 移交 G2-2 (VaultScope 统一): 跨 vault 切换后重放旧 vault 的
待恢复条目仍会归到新 active vault — 条目本身不带 vault 维度,
根治需 VaultScope + 落盘条目补 vault 字段, 不在本卡范围。
```

三处回灌（`:324` / `:392` / `:441`）同用 `_build_group_id_from_canvas`，其 `:638-644` 取 ContextVar 或 **当前 active vault**，而非原记录的 vault。
⇒ T6-B 接通后，若用户曾切换 vault，**旧 vault 的待恢复条目会被写进新 active vault** = 跨 vault 污染。须在接通前决定：补 vault 字段、或按 vault 过滤、或接受并告知。

**P3 — `/traces` 暴露面缺口 + 路径错位。**
`traces.py:20-25` 的 `LOG_FILES` 仅 4 key；未暴露 `failed_writes` / `canvas_events_fallback` / `neo4j_memory` / `failed_dual_writes`。
⛔ 更根本的是 §二.4 的**路径错位**：已暴露的两条也读不到实际文件。T6-C 修暴露面前须先统一路径。

**P4 — 按 `request_id` 查是错的口径。**
`_search_jsonl` 按 `request_id` 等值匹配，而链 3 的 entry 九字段**无 `request_id`**，链 2 有半数通道不传。
⇒「积压数 + 最老时间」本就不是 request_id 口径，T6-C 应走聚合面而非逐条 trace。

---

## §七 口径更正登记

### §七.1 卡文 §〇 六条更正 — 复测结果

| # | 更正内容 | 复测 |
|---|---|---|
| 1 | config 在 `backend/app/config.py`（非 `core/`），`:477` default=False | ✅ |
| 2 | U1 波 0 services 行号漂移（`sync_all_fallbacks :54→:53` 等 6 项） | ✅ 全部一致 |
| 3 | U2 波 0 core 行号漂移（`failure_counters` 4 项） | ✅ 全部一致 |
| 4 | 启动门 `:386→:387` | ✅（但见 §四 口径澄清） |
| 5 | `failed_edge_syncs` census 5 → **9 行** | ✅ 实测 9 / 非测试 5 |
| 6 | 孤儿判据改「枚举形态 + 全命中归类 + 验伪锚」 | ✅ 已执行 |

### §七.2 本卡新增更正（供 T6-B/T6-C 直接引用）

| # | 内容 |
|---|---|
| 7 | 链数：卡文 5 → U11 已列 6 → 本卡补链 6 → Codex 指出链 8 候选 |
| 8 | `sync_all_fallbacks` 同步**三个**文件；另有 `SYNC_CHECKPOINT_FILE`（`:35`）为状态文件 |
| 9 | 链 2 写侧锚：`DeadLetterStore.__init__:224` 外，`EpisodeWorker.__init__:306` 亦有默认参数，实例化 `:311` |
| 10 | 链 4 真实写入点是 `canvas_service.py:508`（通用写函数 `failure_counters.py:73`），非仅路径常量 `:25` |
| 11 | 链 7 有**两个常量名**指向同一文件：`neo4j_edge_client.py:43` `LEARNING_MEMORY_PATH` / `fallback_sync_service.py:34` `LEARNING_MEMORIES_FILE` |
| 12 | `_sync_failed_writes` def 在 **`:113`**（`:129` 是体内 `_load_checkpoint`） |
| 13 | 链 5 六处是**门行号**，写调用在下一行 `:267/:364/:444/:461/:990/:999` |
| 14 | 链 1 `_save_json_data` 有**六个**调用点；降级入口 `_fallback_to_json:421` |

---

## §八 本卡未证明什么（10 条）

1. **未证明现网实例的 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 真实取值** —— 只读车道树 `.env` / `.env.example`，⛔ 未读现网 live vault 的 `.env`。
2. **未证明七条暂存文件在现网已积压多少 / 最老多久** —— 只对现网目录做了 `ls` 与 `-newer` 计数，未读文件内容。
3. **未证明孤儿接通后的回灌幂等性与正确性** —— T6-B 的 7692 端到端门面（D-39）。
4. **未证明处置表的「接通」优于「退役」** —— 产品决策由 T6-B/C 落地。
5. **未证明 `getattr(…, True)` 在某配置路径下真会让有效默认变 True** —— 未穷举所有 `Settings` 装载路径。
6. **未证明 `DEAD_LETTER_STORE_FULL_BODY` 开启后全文落盘的隐私面** —— 只 census 开关位置。
7. **未证明这 7(+1) 条是全集** —— 判据 19 覆盖三种路径拼接形态；Codex 已用第 8 条（变量拼接）证伪「三形态足够」这一前提。仍不覆盖更复杂的动态拼接 / 配置注入路径。
8. **未证明第 8 条候选在单纯 Neo4j 断连时一定被写入** —— 已证生产注册与恢复入口存在，未证写入路径必经它。
9. **未证明 `_pending_failed_writes` 内存队列的实际丢失规模** —— 只证「仅 `cleanup()` 刷盘」这一代码事实。
10. **未证明链 6 历史上从未产生过文件** —— 结论限于当前源码。

---

## §九 修正记录（v1 → v2，两类来源分列）

### 来源 A — Codex round-1 指出（12 条，本卡逐条独立实测确认，零误报）

| # | 级别 | 修正 | 落点 |
|---|---|---|---|
| 1 | HIGH | 链 5 写侧已有 10000 条上限，v1「有界机制全在孤儿体内」错误 | §一 链5 / §二.5 / §六.1 P1 |
| 2 | HIGH | 链 3 漏两个写者；新回灌器跳过结构化条目；「UI 可见」过强 | §一 链3 / §二.3 / §六 |
| 3 | HIGH | 跨 vault 归属风险未登记 | §六.1 P2 |
| 4 | HIGH | `/traces` 读路径与死信写路径错位 | §一 链2/链4 / §二.4 / §六.1 P3 |
| 5 | HIGH | 链 2 死信来源不限 markdown，回源不可统一断言 | §二.7 / §六 |
| 6 | HIGH | 链 4 死信缺 `from/to/label`，不足以重放 | §二.6 / §六 |
| 7 | MEDIUM | 判据 19 漏第 8 条 outbox 候选（变量拼接） | §一 链8* / §八.7-8 |
| 8 | MEDIUM | 二态缺「实际装载且无更高优先级覆盖」前提 | §五 |
| 9 | MEDIUM | `:387` 是定位更正，不等于可改范围收窄 | §四 |
| 10 | MEDIUM | 链 1 有运行时读侧、非严格单调增长 | §一 链1 |
| 11 | LOW | `_sync_failed_writes` def 在 `:113` | §一 链3 / §七.2 #12 |
| 12 | LOW | 链 7 读取方式与丢失时机表述不准 | §二.9 |

Codex 同时给出 7 项**核对通过**：两孤儿及工厂零调用（AST 交叉验证）、正则不完备但未发现漏网、无缺字段第三态、启动三定位点、链 7 运行时存储职责、离线早退跳过全部清理、链 6 当前无写入接线。

### 来源 B — 作者自查发现（11 条，对照 U11 审计原文 + 追加判据 21-26）

| # | 修正 | 落点 |
|---|---|---|
| B1 | 链数归属：U11 已列 6 条，不得表述为本卡新增 | §一 题注 |
| B2 | `_sync_failed_writes:129` → `:113`（与 Codex LOW-11 重合） | §七.2 #12 |
| B3 | 链 3 三个写者（写者 3 仅 `cleanup()` 刷盘） | §二.3 |
| B4 | 链 2 触发前提：头号场景连写都不发生 | §二.2 |
| B5 | 两条红测试归属 U11，本卡仅复测量化 | §三.3 |
| B6 | 链 1 六个调用点 + 降级入口 | §一 链1 / §七.2 #14 |
| B7 | 链 5 门行号 vs 写调用行号 | §七.2 #13 |
| B8 | 增补「未证明」条目 | §八.9 |
| B9 | **孤儿是被摘除的，不是从未接线**（`59586af1` / `daa9fd37` 逐字复证） | §二.1 |
| B10 | 第 8 条对照链 EventBus outbox 为 T6-B 可照抄范式 | §一 链8* / §六 |
| B11 | 逐链 U11 条目对应表 | §一.1 |

---

## §十 判据与 evidence 对照（34 组）

| 判据 | 内容 | evidence |
|---|---|---|
| 0 | 第 0 分钟自证 | `step0-selfcheck-*.txt` |
| 1 | 孤儿 `recover_failed_writes` + 验伪锚 | `judge1-*.txt` |
| 2 | 孤儿 `sync_all_fallbacks` + 工厂 + 验伪锚 | `judge2-*.txt` |
| 2x | 宽枚举补漏（裸/实例化/反射/字符串） | `judge2x-*.txt` |
| 2y | `gateway` import 面 + 两条红测试断言对象缺席 | `judge2y-*.txt` |
| 3/4/5 | `failed_edge_syncs` 9 行 + 启动门三锚 + 双写二态 | `judge3-4-5-*.txt` |
| 5x/6 | 第三态排查 + 五链写读锚 | `judge5x-6-*.txt` |
| 7/8/9 | 第六条链 + `/traces` 暴露面 + 契约分裂 | `judge7-8-9-*.txt` |
| 10 | 写侧接线 + `request_id` + `DeadLetterStore` 实例化 | `judge10-writeside-*.txt` |
| 11/12 | traces 恒空核查 + skip patch 目标 + 基线跑法 | `judge11-12-*.txt` |
| 13/14 | skip 归属 + `EpisodeTask.request_id` 来源 | `judge13-14-*.txt` |
| 15 | `EpisodeTask` 两创建点完整参数 | `judge15-*.txt` |
| 16 | 六链有界性机制（⚠️ 窗口截断，结论已由判据 27 更正） | `judge16-*.txt` |
| 17 | 链 3 清理归属 + 链 1 写入方式 + `sync_all_fallbacks` 早退原文 | `judge17-*.txt` |
| 18/19 | 第七条链 + 全域 `data/` 三形态总扫 + 验伪锚 | `judge18-19-*.txt` |
| 20 | 链 7 写侧 + checkpoint + 轮转实现 | `judge20-*.txt` |
| 21/22 | 链 3 三个写者 + 链 2 触发前提 | `judge21-22-*.txt` |
| 23 | 链 1 写侧完整路径 | `judge23-*.txt` |
| 24 | 链 5 六处门形态一致性 | `judge24-*.txt` |
| 25/26 | 孤儿历史（`59586af1`/`daa9fd37`）+ 链 E 活范式 | `judge25-26-*.txt` |
| 27/28 | **复核 Codex HIGH-1 / HIGH-4** | `judge27-28-*.txt` |
| 29/30 | **复核 Codex HIGH-2 / HIGH-3** | `judge29-30-*.txt` |
| 31 | **复核 Codex HIGH-5/6 + MEDIUM-7/9/10 + LOW-12** | `judge31-*.txt` |
| 32 | **Codex 12 条逐条复核结论汇总** | `judge32-*.txt` |
| 7'(地盘) | 非 `_bmad-output` 改动 = 0 + 禁改六文件 = 0 + 验伪锚 | `judge7-territory-gate-*.txt` |
| 7''(commit 后) | **commit 后**地盘门（此前两侧同一 commit 恒空、不成立）：`diff 08100483 HEAD -- . ':(exclude)_bmad-output'` = 0 行；36 个变更文件 **全部**在 `_bmad-output`；禁改六文件逐个 = 0；并实证 `':!_bmad-output'` 在本机报 `Unimplemented pathspec magic` | `judge7pp-post-commit-territory-gate-*.txt` |
| 33 | 存档卫生（**口径更正**：`*.stderr*` 模式而非 `stderr` 子串）：入库 `*.stderr*` = 0；验伪锚 = 工作区确有 1 个 `.stderr`（355 KB）被 `.gitignore:264` 拦下 ⇒ 非空洞通过 | `judge33-stderr-hygiene-correct-scope-*.txt` |
| 8'(单测) | `tests/unit` nodeid diff 与基线完全一致（64/64，新增红 0） | `judge8-unit-diff-*.txt` + `unit-close-*.txt` |
| 9'(pyright) | `pyright app` = `0 errors` | `judge9-*.txt` |
| 10'(只读) | 现网三处 `-newer sentinel` = 0 + 验伪锚 20 | `judge10-readonly-gate-*.txt` |
