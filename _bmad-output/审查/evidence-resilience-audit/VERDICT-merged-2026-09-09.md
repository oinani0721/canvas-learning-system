# 合并裁定：Neo4j 离线/写失败时学习数据是否会丢

> 复核方式：只读（grep / sed / cat / git show / ls / wc）于 `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`。未跑测试、未启服务、未连 7691/7687。下文每条「实测」= 本次亲自跑过的只读命令；标「二手」= 引自四视角/反驳而本次未复验。

---

## 1. 完整链路（写入 → 暂存 → 重放 → 落库）

学习数据不是一条链，是**五条互不相通的链**。Phase 2 的「取代」只发生在其中一条上。

### 链 A —— 评分 / 学习事件（`record_learning_event`）：**两条分叉，一条断、一条堵**

| 环 | 位置 | 状态 |
|---|---|---|
| 写入 A-1 结构化半边 | `backend/app/services/memory_service.py:576` → `:1198` → `backend/app/clients/neo4j_client.py:1005` | **活** |
| ↳ 落库（在线） | `neo4j_client.py:1019` `MERGE (u:User)-[:LEARNED]->(c:Concept)` | **活** |
| ↳ 降级暂存（离线） | `neo4j_client.py:409/414/419`（初始化失败）与 `:619-621 / :627-629`（中途降级）→ `_run_query_json_fallback` → `:743 _save_json_data` → `backend/data/neo4j_memory.json` | **活（写）** |
| ↳ 该暂存的重放 | — | **从未存在**（见 §2.2） |
| ↳ 前置 fail-closed | `neo4j_client.py:1005-1016`：group_id 解析失败 `return False`，**发生在 `run_query` 之前**，连 JSON 都不落；上游 `memory_service.py:1198` 不检查返回值 | **活（有争议，见 §4.9）** |
| 写入 A-2 语义 episode | `memory_service.py:632` → `_enqueue_episode`（`:442`） | **活** |
| ↳ 就绪闸 | `memory_service.py:459-461` `if not worker.is_ready: logger.debug(...); return False`；`is_ready = _started and _graphiti is not None`（`episode_worker.py:527`） | **活** |
| ↳ 调用方处理 | `:632` **不接返回值**，随后照常 `return episode_id`（`:645`） | **断（零暂存、零告警）** |
| ↳ 暂存 | 队列 `asyncio.Queue(maxsize=100)`（`episode_worker.py:310`），**纯内存、不落盘、启动不读盘** | **活但不耐久** |
| ↳ 队满 / 停机 | `:510-512` 只加计数器；`:486` drain 超时「will be lost」 | **断（不落盘）** |
| ↳ 死信 | `episode_worker.py:225 / 234-260` → 相对路径 `data/dead_letter_episodes.jsonl`；本树**该文件不存在**（实测 `ls`） | **活（写）** |
| ↳ 死信重放 | — | **从未存在**；消费者只有 `traces.py:22-23`（只读）、`census_dead_letter_episodes.py`（自称只读）、`generate_regression_tests.py`（生成测试） |
| ↳ 死信有损 | `episode_worker.py:107` `"episode_body": self.episode_body[:200]`；全文仅 `DEAD_LETTER_STORE_FULL_BODY` 开启才写（`:229-232 / :253-254`） | **默认残片** |

### 链 B —— 结构化知识实体（`record_knowledge_entity`：callout / relation / error）

| 环 | 位置 | 状态 |
|---|---|---|
| 写入 | `memory_service.py:1647` `enqueued = self._enqueue_episode(...)` —— **全仓唯一检查返回值的写点** | **活** |
| 暂存 | `:1662 _record_structured_outbox`（定义 `:499`，落盘 `:513`）→ `backend/data/failed_writes.jsonl`，status 诚实标 `degraded`（`:1657-1677`） | **活** |
| 重放 A | `memory_service.py:2679 recover_failed_writes` | **孤儿**（实测非测试命中仅：定义 + `failed_writes_constants.py:6` 注释 + `:2682` docstring） |
| 重放 B | `fallback_sync_service.py:54 sync_all_fallbacks` / `:657` 工厂 | **孤儿**（实测非测试命中仅定义本身） |
| 真相源旁路 | 同函数 docstring `memory_service.py:506-507` 原文：「callout/relation 的**主要持久化是 frontmatter + 启动回填**（vault md 是真相源, backfill_vault 重建边）, outbox 是非结构化材料/边界场景的兜底」 | **活** |
| 启动回填 | `main.py:392 backfill_vault(..., execute=True)`，源是 vault markdown | **活，但被 `main.py:386` `if _worker_graphiti is not None:` 门住** —— Neo4j 离线时整段跳过（`:404` 只打「跳过」日志） |

### 链 C —— Canvas 事件 / 边

| 环 | 位置 | 状态 |
|---|---|---|
| 写入兜底 | `canvas_service.py:121-172`，6 个调用点 `:267 / :360 / :440 / :457 / :986 / :995`，全部包在 `if getattr(settings,"ENABLE_GRAPHITI_JSON_DUAL_WRITE", True):` | **配置依赖**（见 §4.3） |
| ↳ 开关实况 | `config.py:477-480 default=False`；`backend/.env:85` = `# ENABLE_GRAPHITI_JSON_DUAL_WRITE=true`（注释态）；`backend/.env.example:226` = **未注释的生效赋值 `=true`**（实测三处） | 本机 **关**；按样例部署 **开** |
| 重放 | `fallback_sync_service.py:194 _sync_canvas_events` | **孤儿** |
| 边同步死信 | `failure_counters.py:24-26` → `canvas_service.py:505 write_dead_letter` → `backend/data/failed_edge_syncs.jsonl`（实测 80 行，mtime 2026-09-09 18:08，仍在增长） | **活（写）/ 无重放** |
| 另一条活通道 | 前端 IndexedDB `sync_outbox`（`frontend/src/services/dexie-db.ts:222/:234` + `sync-engine.ts`），后端把 Neo4j 异常归 TRANSIENT → 503 → 前端指数退避重投，跨浏览器重启存活（二手，未复验） | **活**，但载荷只有 node/edge/board 结构，**不含评分/episode** |
| 启动重建 | `main.py:363 canvas_projection_sync.sync(...)`，源是 vault markdown | **活**（不消费任何暂存文件） |

### 链 D —— FSRS 复习调度状态（价值最高的一类）：**完整且不经 Neo4j**

| 环 | 位置 | 状态 |
|---|---|---|
| 真相源 | 节点 `.md` frontmatter（`review_service.py:110-116` 自陈：`fsrs_card_states.json` 是投影/缓存，分歧以 frontmatter 为准） | **活** |
| 写入 | `canvas-vault/.claude/scripts/fsrs_bridge.py`，实测 `grep -c "neo4j\|bolt\|graphiti"` = **0** | **活，与 Neo4j 无关** |
| 账本 | `<vault>/learning_events.jsonl`（`learning_event_log.py:2-4`：「过程可回放、图可重建」） | **活** |
| 重放 | quiz-answer 技能的 A2「追加前重放至空」不变量（`canvas-vault/.claude/skills/quiz-answer/SKILL.md:2327` 实测原文；不变量被破坏时 `SystemExit` fail-closed 拒写） | **活 —— 但方向是账本 → frontmatter，不是 → Neo4j** |
| 触发 | launchd `com.canvas.daily-review`，不经后端 | **活** |

### 链 E —— EventBus outbox：**唯一活着的「暂存 ↔ 启动重放」闭环**

| 环 | 位置 | 状态 |
|---|---|---|
| 写 | `event_bus.py:343 → :360`，仅两个触发点 `:264`（熔断 OPEN）/ `:304`（重试耗尽） | **活** |
| 读 | `event_bus.py:369 recover_outbox` ← `main.py:216` | **活** |
| 覆盖上限 | 实测 `_write_outbox` 全文只出现在 `:264/:304/:343`；`_dispatch_tier1`（`:216-237`）只 `raise`，从不写 outbox。而 `SCORE_SUBMITTED` 是 `TIER_1_CRITICAL`（`canvas_events.py:211`） ⇒ **评分事件结构上永不进 outbox** | **覆盖 = 仅 Tier-2** |
| 实况 | 实测 `backend/data/outbox/` 为**空目录** | 未见行使记录 |

### 被删除的那一环（历史）

实测 `git show 59586af1 -- backend/app/main.py`（2026-03-26，`refactor(phase2): delete fake bridge/JSON dual-write code, replaced by GraphitiEpisodeWorker`）删除行含：

```
-        logger.warning("JSON fallback is disabled. Neo4j outage will cause data loss.")
-    # ✅ Story 38.8: Sync all JSON fallback files to Neo4j on startup
-        from app.services.fallback_sync_service import get_fallback_sync_service
-            sync_svc.sync_all_fallbacks(), timeout=60.0
```

同日 `daa9fd37` 改 `config.py`（实测 diff）：`default=True` + `"safe default for Neo4j offline resilience"` → `default=False` + `"[DEPRECATED] Legacy JSON dual-write."`

⇒ **写侧关 + 重放摘 + 告警删，三件同一天**。

---

## 2. 「有人写、没人读」的暂存数据

**有，六条。** 逐条给「丢什么 / 何时发生 / 精确到什么程度」：

**2.1 `backend/data/failed_writes.jsonl`（实测 78 行）**
- 写者三个（活）：`agent_service.py:131`（评分记忆写超时/异常）、`memory_service.py:513`（A7，worker 未就绪）、`memory_service.py:2864`（`cleanup()` 时刷 `_pending_failed_writes`，`:1419` 累积 ⇒ **进程被 kill 则内存队列全丢**）。
- 回灌器两个，**都是孤儿**。
- ⚠️ **但它有活读侧**：`load_failed_scores`（`:2785`）被 `get_learning_history` 在 `:799` 实调，把条目并进用户可见历史（`:797` 注释 "so the user never sees a missing score gap"）。
- ⇒ 精确表述：**不是「没人读」，是「没人回灌」**。用户界面照常显示分数，而图里没有 —— 这正是断裂长期不被发现的机制。
- 丢什么：这些评分/知识实体永远不进图 ⇒ 复习推荐、掌握度、检验白板选题拿不到它们。

**2.2 `backend/data/neo4j_memory.json`（实测 8 行，当前近乎空）**
- 写者活：Neo4j 掉线时**自动**接管（初始化失败 `:409/414/419`，或运行中重试耗尽 `:619/:627`），此后所有写落此文件。
- 回灌器：**从未存在**。`fallback_sync_service.py` 覆盖的三文件清单里也不含它。
- 且 `_use_json_fallback` 是**单向闩**：实测 `grep -rn "_use_json_fallback = False" backend/app` = **0 命中**，仅 `:431` 置 True。一旦中途降级，进程内永不切回 Neo4j。
- 丢什么：Neo4j 离线期间的**全部** `User/Concept/LEARNED/score/next_review` 结构化事实。它们在盘上，但恢复后没有任何通道把它们送回图。

**2.3 `backend/data/failed_edge_syncs.jsonl`（实测 80 行，仍在增长）** —— 白板边同步 3 次重试耗尽后落盘，零重放。实害较低（边可由 `main.py:363` 从 markdown 重建，且前端 outbox 另有一层），但重建靠的是别的路径，不是这个文件。

**2.4 `data/dead_letter_episodes.jsonl`** —— 本树**不存在**（相对 CWD 路径）。写者活但只在 worker **已就绪**后才可能触发 ⇒ 恰好**不覆盖**「Neo4j 启动时离线」这个头号场景；零重放；默认只存 200 字符残片 ⇒ 即便将来补重放器，按当前代码写出的死信也**重放不出原始内容**。

**2.5 `backend/app/data/canvas_events_fallback.json`** —— 本机配置下写侧也关（走 else 只打日志），**双向断**；按 `.env.example` 部署的实例则是**写活读死**的无界坟场。

**2.6 `backend/data/learning_memories.json`（实测 6 行）** —— `LearningMemoryClient` 的常态旁路存储（不是失败兜底），DI 注入活、有活读侧（`review_service` / `rag_service`，二手），回灌器 `_sync_learning_memories` 孤儿。

**附：`backend/data/failed_dual_writes.jsonl` —— 零写者**（`_write_to_graphiti_json` 已于 `59586af1` 删除），文件永不产生，而 `docs/stories/36.12.story.md` 仍宣称已实现 ⇒ 监控端 `dual_write_failures` **恒 0**，一个「永远没有失败」的指标。

**发生场景（三个）**：

- **S1 启动时 Neo4j 离线**（最贴题）：`initialize_graphiti` 预检失败 → `episode_worker.py:377-378` `self._graphiti = None; return False` → `main.py:283 start()` **不执行**（实测 `:282-288` else 分支只打 warning）→ `is_ready` 恒 False。此时：链 A-2 的语义 episode **零落盘、零告警、调用方拿到成功返回**；链 A-1 的结构化半边落 `neo4j_memory.json`（没丢盘、没人捡）；链 B 落 `failed_writes.jsonl`（没人回灌）；链 B 的回填被 `_worker_graphiti is None` 跳过。**且无自愈**：`initialize_graphiti` 全仓只在 `main.py:276` 调一次，`set_graphiti_client` 零生产调用 ⇒ Neo4j 中途恢复也不会自己接上，必须重启进程。
- **S2 运行中掉线**：`neo4j_client` 中途降级并闩住；worker 若已就绪，重试窗 = 3 次退避 `U(0,2)/U(0,4)/U(0,8)`（`episode_worker.py:98-103`），**最坏合计约 14 秒**，之后进残片死信。
- **S3 进程被 kill / drain 超时**：内存队列（≤100）全丢，不进死信；`_pending_failed_writes` 只在 `cleanup()` 刷盘，崩溃即丢。

---

## 3. 「已被 worker 取代」这个前提是否成立

**不成立。** 分四条，每条独立可证：

**(a) 覆盖面不成立。** worker 只接 `add_episode` 这一路语义 episode。Canvas 事件的 6 个写点、边同步死信、`LearningMemoryClient` 的 JSON 库、`neo4j_client` 的降级 JSON —— **四条通道从来不在 worker 的覆盖面内**，被翻掉的那个开关管的恰恰是其中一条（Canvas），两者根本不是同一个面。

**(b) 耐久性不成立（决定性）。** 被取代者的性质是「落本地文件 + 启动重放」，即**跨进程存活**且**与 Neo4j 是独立故障域**。worker 的替代物是纯内存有界队列：不落盘、启动不读盘、队满只加计数、停机超时明示丢弃、失败进死信而死信无重放。更关键的是主路径与兜底路径**终点是同一个 Neo4j**（`memory_service.py:1626-1630` 主路径失败后转 `_enqueue_episode`，二手），Neo4j 一挂两条同时失效 —— 而 JSON 兜底的介质是本地磁盘。**在故障域这一维上，这是降级不是等价。**

**(c) 时间窗不成立。** worker 的韧性窗 ≈ 14 秒；被取代者的窗是「直到下一次成功重放」。真实停机以分钟/小时计（本仓 MEMORY.md 记录过 2026-09-05 复习链停摆整天）。

**(d) 替代承诺里的重放端被同一批改动一并删掉。** 见 §1 末的两个 commit：写侧关、重放摘、告警删，同日完成，且至今没有任何东西补上重放端。`backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:446/:453` 仍在 `assert "get_fallback_sync_service" in source` / `assert "sync_all_fallbacks" in source`（实测两行存在，而 `main.py` 内 grep = 0）⇒ **这两条测试必红**，是「删除未收口」的现成红契约锚，只是没人把红转成结论。

**必须限定的一半（否则结论过强）**：前提在**另一种叙述下部分成立**。系统自己的架构声明是「vault markdown = 真相源，Neo4j = 派生投影」（`memory_service.py:506-507`、`review_service.py:110-116`，均实测原文）。在链 B 和链 D 上，这个替代是**兑现的**：FSRS 状态、批注、错误、原因边都有独立于 Neo4j 的持久层与重放器。所以准确的裁定是：

> 「已被 **worker** 取代」→ **不成立**。
> 「已被 **vault frontmatter + 启动回填** 取代」→ 对链 B / D **成立**，对链 A（评分 episode、概念关系）与链 C（Canvas 事件/边）**不成立**。
> 而翻默认值时写在配置里的理由是前者，不是后者。

---

## 4. 有争议 / 分歧的点（如实并列，不强行统一）

| # | 争议 | 甲方依据 | 乙方依据 | 本次裁定 |
|---|---|---|---|---|
| 4.1 | `failed_writes.jsonl` 是否「零读侧」 | writers/replayers/startup 三视角：只 grep 了两个重放器名 | 反驳：`load_failed_scores`（`:2785`）被 `:799` 实调 | **乙方成立（实测）**。「没人回灌」为真，「没人读」为假。差别是实质的：UI 看得见反而掩盖断裂 |
| 4.2 | `neo4j_memory.json` 是否「只写不读」 | writers/startup：`grep "neo4j_memory"` 只命中路径常量 | 反驳：`_initialize_json_fallback`（`:436-465`）每次降级都把文件读回 `self._data` | **乙方成立（实测）**。原判是窄 grep 假阴性（读走 `self._storage_path`）。但「**回灌器**不存在」双方一致，仍成立 |
| 4.3 | 开关生产实际取值 | 四视角均判「恒 False」（据 `config.py:477` + `.env:85` 注释） | 反驳：`.env.example:226` 是**未注释生效赋值 `=true`**，README 部署步骤是 `cp .env.example .env` | **有争议，且取决于部署**。实测三处文本均属实。取值不同结论方向不同：关 = 连暂存都没有；开 = 写活读死的无界坟场。**线上真实取值本次无法证**（见 §5.2） |
| 4.4 | `learning_events.jsonl` 有无重放器 | writers/replayers：「无任何生产重放器」 | 反驳：quiz-answer 技能 A2「追加前重放至空」 | **各对一半（实测）**。A2 存在且活，但它重放进 **frontmatter**，不是 Neo4j。原判在 Neo4j 轴上成立；作为整体判断是搜索面只划到 `backend/**/*.py` 造成的假阴性（vault 侧 python 内嵌在 SKILL.md 里） |
| 4.5 | `migrate_neo4j_data.py` 是否人工回灌通道 | writers：「须人工跑脚本回灌」 | 反驳 + replayers：该脚本无 driver/bolt/Cypher，是 JSON→JSON Unicode 清洗 | **乙方成立（二手，两个独立视角一致）**。「须人工跑脚本」是**不成立的安慰** |
| 4.6 | 死信 685 条 / 2026-04-07 | replacement 视角引为实证 | 反驳：该数字来自另一棵树（`feature-obsidian-hybrid-dev`）的快照 | **本树无法核实**（实测该文件不存在）。不进结论数字，只作旁证 |
| 4.7 | `backfill_vault` 该记缺陷还是记正常 | replacement/startup：「恰在需要它的场景里不执行」 | 反驳：「重放器在目标恢复后才跑正是重放器的定义」 | **各对一半**。作为**恢复器**它正常；作为**停机期兜底**它零覆盖 —— 而翻开关所需要的恰是后者。且覆盖面只到写进 md 的东西 |
| 4.8 | 「Neo4j 离线 ⇒ 每一条学习 episode 直接消失」 | writers gap#1 | 反驳：评分的结构化半边仍落 `neo4j_memory.json` | **原判过强（实测确认反驳）**。准确表述：语义 episode 这一份消失（零落盘）；结构化半边落 JSON 但无回灌 |
| 4.9 | `create_learning_relationship` 的 group_id fail-closed 是否算一条独立丢失面 | 反驳提出：`:1005-1016` 在 `run_query` 前 `return False`，连 JSON 都进不去，上游不检查返回值 | 无人反对，但也无人给出触发证据 | **机制成立（实测代码属实）**，但触发条件是 group_id 解析失败、**与 Neo4j 是否在线无关**；真实流量中是否发生过，**证据不足** |
| 4.10 | 前端 IndexedDB outbox 算不算「该能力已有覆盖」 | startup/replayers：判为「同名易混淆项，非后端启动恢复」 | 两条反驳：它正是 Neo4j 掉线时白板写入不丢的实现 | **各对一半**。它确实活着且覆盖链 C 的白板结构写入；但载荷只有 node/edge/board，**不含评分、episode、学习事件** ⇒ 不能计入被审能力的主面 |

---

## 5. 证据不足（含「缺什么」）

1. **无任何运行期观测。** 全部结论来自静态只读追踪。核心那条链（离线 → worker 不就绪 → episode 静默丢）是三点串成的**代码可达性**（`episode_worker.py:377-378` + `main.py:282-288` + `:527`），**没有一条真实离线启动的日志**。缺：一次断网启动 + 日志中 `[Phase 2] GraphitiEpisodeWorker in degraded mode` 与 `Episode worker not ready, skipping enqueue` 的实际出现记录，以及同期 `dead_letter` / `failed_writes` 是否新增。
2. **线上 `backend/.env` 的开关实际取值未知**（gitignored，本次只读了本 worktree）。缺：线上部署树该行的实测。这直接决定 §4.3 的方向。
3. **`backend/data` 现存 78 / 80 行的来源。** 与 MEMORY.md 记录的「TestClient lifespan 污染真 data」形态一致（`Simulated Neo4j failure`、`partial.canvas` 等）。⇒ 它们证明「写者有效 + 无人回灌」，**不证明生产已丢 78 条**。缺：生产日志的 `episodes_dropped_queue_full` / drain timeout 计数，才能给出真实丢失量。
4. **死信实际落盘位置。** 相对 CWD（`episode_worker.py:225`）。Docker 下可从 `WORKDIR /app` 推出；宿主机直跑 uvicorn 时取决于启动目录，未实跑验证。同一 CWD 依赖也影响 `SettingsConfigDict(env_file=".env")` 的加载（二手）。
5. **`DEAD_LETTER_STORE_FULL_BODY` 是否被外部注入。** 只能证明它不在 `.env` / `.env.example` / `docker-compose.yml`，无法证明 shell / launchd 层没有设。
6. **canvas-vault 侧其余写者未穷举**（`start-exam-board` / `ai-linked-doc` 等技能是否各有独立暂存/重试文件）。
7. **A2 重放器「线上就是这一版」未证。** `daily-review-wrapper.sh` 的逐字节 `cmp` 门只覆盖 `fsrs_bridge.py` / `decay_beta.py`，**不覆盖 SKILL.md**（二手）。
8. **`FallbackSyncService` 三个 `_sync_*` 的正确性未验。** 它零调用，验它不影响本裁定；但若要把它挂回启动流程，必须先审两个已知坑：(i) `recover_failed_writes` 是**先删后确认** —— `memory_service.py:2746-2755` 里 `_enqueue_episode` 返 True（仅进内存队列）即从持久文件删除该行，`:2760-2778` 重写文件（二手，机制描述与我读到的 `:2746` 调用点一致）；(ii) 其兜底 `except` 只收 `(RuntimeError, ConnectionError, TimeoutError)`，不覆盖 neo4j 驱动真抛的 `ServiceUnavailable` 与 tenacity `RetryError`（**二手**，引自本树 `_bmad-output/审查/evidence-red-c2/familyD-tail-evidence.json:133`，本次未复验）。⇒ **「自然修法」本身不安全，不能直接接回。**

---

## 6. 给非技术负责人的白话结论

有没有东西在悄悄丢：有，但不是全部。每天的复习进度、错题和批注写在笔记文件里，图数据库停了也照样能用，这部分是安全的。会丢的是「这次学习发生了什么」的那份摘要——图数据库一停，它连草稿都不留，系统还照常回报「已保存」。另外几份写在硬盘上的失败记录，眼下只进不出：写的人还在写，但当初负责把它们送回数据库的那个搬运工，今年三月连同一句「关掉兜底会丢数据」的提醒一起被删掉了，至今没人补。

什么时候能被发现：几乎发现不了。查历史时，界面会把硬盘上那份失败记录一并显示出来，看着分数都在；只有依赖图谱的功能——复习推荐、掌握度、出题选材——会悄悄少料。硬盘上那两份记录现在各有七八十条，仍在增加，但里面不少是测试留下的，真实用户到底丢了多少，现在查不出来。

建议你做两个决定：第一，把那个搬运工重新接回开机流程，但接之前必须先修它「还没送到就先把底稿删掉」的毛病，否则修完更糟。第二，先在测试机上断开图数据库启动一次，用日志把真实丢失量测出来，再决定要不要把那个默认开关改回去——现在两边都只有推理，没有实测。