# UAT — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 第 2/3 张）

> # ✅ Codex round-9 判定：**本卡新增／遗漏 HIGH 已降为 0**
>
> 代码 `8e3c3fa2` · round-10 终审中 · 未 push · 工作树干净
> Codex **十轮**（远超卡文 5 轮上限，如实登记）。车道两次按 D-15 停车并交主 session，均因流程判定「(n) 未闭环」而继续整改。**主 session 仍可裁定止于任一版本。**
>
> ## r9 的分类计数（本卡现在最关键的一张表）
>
> | 分类（Codex 互斥计数） | r9 条数 | 本轮处置 |
> |---|---|---|
> | **本卡引入或遗漏** | **LOW 1 / HIGH 0** ✅ | LOW 已修（端点补 `pending=-1` 语义说明）|
> | 既有算法，应归**独立重写卡** | HIGH 1 | 移交（缺 timestamp 的旧记录重试取 `now()`，可覆盖新评分）|
> | **既知移交项** | HIGH 1 + MEDIUM 3 | 移交（G2-2 跨 vault / 模块锁跨循环 / 状态失真 / 归属门假绿）|
>
> ⇒ **本卡自己的代码已经收敛。** 剩余 HIGH 全部是「接线照亮的既有算法雷区」。
>
> ## r9 两条修复（`8e3c3fa2`）
>
> | # | 问题 | 修法 |
> |---|---|---|
> | LOW-6 | 上一轮引入 `-1` 表「数不出来」，但端点文案只写 `pending:int` | 端点 `description` + docstring 写明「`-1` = UNKNOWN，不是负一条；该链必带 `error`；聚合方必须**跳过负值**而非求和」|
> | MEDIUM-3 | 几条分支仍会「文件里还有条目却报 `pending=0`」 | 逐条改：清 checkpoint 失败（**这条是车道上一轮新写的**）、三链初读/解析失败、外层 except 兜底 —— 全改 `-1` + `error`；局部日志不再打与 `unknown` 汇总矛盾的数字 |
>
> 保留 `pending=0` 的只剩「文件不存在 / 内容为空 / 解析出空列表」——那是真的没有待回灌。
> **实测**：3 条全成功 + 清游标失败 ⇒ `pending=-1` 且文件仍有 3 条；canvas 解析失败 ⇒ 带 `error`；汇总日志打出 `≥0 (+failed_writes unknown)` 而非负数。
>
> ## ⚠️ 本轮值得记的一条自伤
>
> 我为修「`pending` 报 0 掩盖真实剩余」而引入 `-1` 哨兵，结果它立刻被两处 `sum()` 吃进汇总——**把「未知」变成负数，比原来报 0 更糟**。
> **哨兵值的代价总是出现在聚合处，而聚合处往往离引入处很远**（一处在同文件汇总段，一处在 `main.py`）。引入哨兵必须同时 grep 所有消费点；r9 还指出我当时说的「无第三处消费点」应收窄为「无第三处**数值聚合**」——`traces.py` 是展示/序列化出口，那正是 LOW-6 的由来。
>
> ## 接线目标已达成（不因任何裁定作废）
>
> 孤儿门 **0 → 2** · 真库 7692 端到端门 **6 passed** · **仓里两条 `[P0]` 常红契约测试转绿** · pyright **0 errors** · `tests/unit` diff 恒只有 `<` · 全程 W4 哨兵 **0** · 地盘门 `main.py` 两 hunk 始终在 `:386-404`
>
> ## 请主 session 裁定
>
> | # | 事项 |
> |---|---|
> | 1 | **停车版本**：`8e3c3fa2`（本卡引入/遗漏 HIGH = 0）/ 更早？ |
> | 2 | **是否接受超配额**（卡文上限 5，实走 10 轮）|
> | 3 | **是否接受改动面多一个既有 unit 测试文件**（`test_story_38_8_fallback_sync.py`，仅 fixture 加 `progress_version`）|
> | 4 | **是否采纳「独立排 Story 38.8 重写卡」**（Codex r7 提出、r8/r9 复申）—— 本卡十轮暴露的 HIGH 清单可直接做该卡的验收负控集 |

> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T6-B.md`
> 车道：`card-t6-neo4j`（分支 `card/t6-neo4j`）
> 前卡 T6-A 末 commit = `310eef31` · **最终 HEAD = `ccb1d101`**（5 个 commit）· B14_BASE = `08100483`
> 证据目录：`_bmad-output/审查/evidence-neo4j-replay-wire/`（78 项）

---

## 〇 第 0 分钟（(a)）

| 项 | 实测 |
|---|---|
| `pwd` | `…/.claude/worktrees/card-t6-neo4j` ✅ |
| 分支 | `card/t6-neo4j` ✅ |
| HEAD | `310eef31`（= T6-A 末 commit `docs(t6-a): Neo4j 离线暂存链零代码普查`）✅ |
| `git status --porcelain` | 空 ✅ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均在 ✅（venv 为目录级 symlink → `card-v5-lance/backend/.venv`） |
| pyright 自证 `test -x "$P"` | ok（`card-v5-lance/backend/.venv/bin/pyright`，v1.1.411）✅ |
| `$BASE` 红基线 `grep -vc '^#'` | **64** ✅ |

**§〇 file:line 逐条核 — 零漂移，卡文写的每一行都逐字命中：**

| 卡文声称 | 实测 |
|---|---|
| `sync_all_fallbacks` :53 | :53 ✅（AST） |
| `get_fallback_sync_service` :656 | :656 ✅ |
| `FallbackSyncService.__init__` :50 | :50 ✅ |
| `_sync_failed_writes/_sync_canvas_events/_sync_learning_memories` 113/193/255 | 113/193/255 ✅ |
| `recover_failed_writes` :2687 / docstring :2690 | :2687 / :2690 ✅ |
| `_record_structured_outbox` :502（调用点 :1665） | :502 / :1665 ✅ |
| `load_failed_scores` :2793（调用点 :802） | :2793 / :802 ✅ |
| `main.py` 门 `if _worker_graphiti is not None:` :387 | :387 ✅ |
| `main.py` :380 try / :381-384 import / :386 `_worker_graphiti=` / :403 else / :404 skip-info / :405 except | 全部逐字命中 ✅ |
| `main.py` T5-D :568 security 段 | `openapi_schema["security"] = [{"InternalApiKey": []}]` ✅（与本卡 hunk 相距逾 170 行） |
| `require_internal_api_key` `security.py:64` | :64 ✅ |
| `traces.py` `router = APIRouter()` :15（裸 router 无路由级鉴权） | :15 ✅ ⇒ (d) 必须端点级挂依赖 |
| `failure_counters.EDGE_SYNC_DEAD_LETTER_PATH` :24-26 | :24-26 ✅ |

**手册地盘核**（`grep` 主干树手册，⛔ 未改手册）——抄录命中原文 L122：

> `| **T6** | card-t6-neo4j | **T6-A**（CARD-NEO4J-REPLAY-CENSUS） | T6-A → T6-B → T6-C | T6-A 零代码；T6-B/C 触及 backend/app；main.py 只动 :386-404 段；DD-03 禁 mock，回灌门走 7692 |`

**开工 unit 基线**：`evidence-neo4j-replay-wire/unit-open-20260914T204341.txt` → `36 failed, 5076 passed, 48 skipped, 23 xfailed, 29 errors`，nodeid 口径 **65** 条，比 `$BASE` 的 64 条多 1 条：

- `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`
- **非本卡引入**：T6-A 是零代码 commit ⇒ 开工时代码树 = `08100483`，与 `$BASE` 采样树**逐字节相同**，本卡此刻一行代码都还没写。开工时孤立跑该文件也红（`unit-open-candidate-isolated-20260914T222544.txt`，`1 failed, 13 passed`）。
- ⚠️ **收工复跑时它变绿了** ⇒ 它是**不稳定**测试（环境/时序相关），不是稳定红。此处保留开工观测的原文，更正见 §二.7 末节 —— 两处结论方向一致（都不是本卡引入），但「稳定/不稳定」这个判断以收工实测为准。

---

## 一 完成条件逐条

### (b) 先红（改代码前落档）

| 判据 | 结果 | 证据 |
|---|---|---|
| ① 孤儿门主判据 | **0** ✅ | `orphan-gate-before-20260914T204349.txt` |
| ① 验伪锚 A：去掉 `grep -vF 'Replaced by'` 应恰 +1 | 裸命中 **1**（`memory_service.py:2690` docstring），差值恰 +1 ✅ | 同上 |
| ① 验伪锚 B：pathspec 形态 | `-- 'backend/app/**/*.py'` 对 `_worker_graphiti` **空输出**；`-- backend/app` 命中 `main.py`（该文件内 4 处）✅ ⇒ 必须用目录形态 | 同上 |
| ① `get_fallback_sync_service()` 生产调用 | **0**（裸 grep 命中 :656 `def` 自身，滤掉后 0）✅ | 同上 |
| ② 离线分支不登记 | `sed -n '404p'` 仅「启动回填跳过 (graphiti 未就绪)」一句；「待回灌/pending/backlog」计数 **0**，验伪锚「跳过」计数 **1** ✅ | `offline-branch-before-20260914T222906.txt` |
| ② 只读计数方法改前不存在 | **0** ✅ | 同上 |
| ③ 端到端门接线前必红 | **5 failed, 1 passed** ✅ | `replay-red-20260914T222821.txt` |
| ③ 红的身份 | 承重用例红在 `:305` 的「回灌后图内可查」断言（`assert []`，端点响应 405 Method Not Allowed = 端点尚不存在）；其余四条各红在自己的状态码断言。**非 import/夹具错**——夹具正常连上 7692、清理与播种均执行 ✅ | `replay-red-identity-20260914T222842.txt` |

> 405 而非 404 的原因：`/traces/replay-fallbacks` 被既有 `GET /traces/{request_id}` 匹配到路径但方法不允许。接线后 POST 路由完全匹配，不受注册顺序影响。

### (c)(d)(e) 三处接线

| 处 | 落点 | 说明 |
|---|---|---|
| (c) 启动恢复自动触发 | `main.py` if 分支体末（`@@ -402,0 +403,22 @@` 纯插入） | `backfill_vault(...)` 之后 `await get_fallback_sync_service().sync_all_fallbacks()`；日志「Neo4j 启动已恢复 → 回灌 N 条, M 条待回灌」。新 import 为**分支内 inline**。**自带内层 `try/except`**：否则回灌异常会落进外层 `except` 被记成「启动回填 failed」，把「回灌失败」伪装成「回填出问题」（DD-13 名实不符），而此时回填其实已经成功 |
| (d) 鉴权管理端点 | `traces.py` 新增 `POST /traces/replay-fallbacks` | 端点级 `dependencies=[Depends(require_internal_api_key)]` + `responses={403,503}`（与 `sync.py:64-72` 同形，防 schemathesis `status_code_conformance` 漂红）。body 空，原样返回 stats。⛔ `security.py` 一字未改，只 `import` |
| (e) 离线登记待回灌 | `main.py` else 分支体末（`@@ -404,0 +427,17 @@` 纯插入） | 新增只读 `FallbackSyncService.count_fallback_backlog()`，纯读三文件、不连 Neo4j；日志「Neo4j 离线, N 条待回灌, 恢复后回灌」。⛔ 未做有界/轮转、未往 `/traces` 加积压字段（T6-C 地盘） |

**两个分支各有一行 `from app.services.fallback_sync_service import get_fallback_sync_service` 是刻意的，不是疏忽** —— 卡文 (c) 与 (e) 分别明令「新 import 用**分支内 inline import（≥:386）**，⛔ 不加进 :381-384 既有 import 块」。合并成一个 import 就必须上提到门外或既有 import 块，那恰好是卡文划死的禁区（也是 T5-D 之外唯一会与别卡产生行交集的地方）。

**`count_fallback_backlog` 的一个刻意口径（名实一致）**：`pending_total` **只累加 `failed_writes` 与 `canvas_events`**。这两个文件回灌成功后会被 `_rotate_file` 搬走，所以「文件里还有几条」= 「还有几条没回灌」；而 `learning_memories.json` **刻意不轮转**（`_sync_learning_memories` 结尾 NOTE —— 运行时 `LearningMemoryClient` 还要查它），其条目数是「本地记录总数」而非「待回灌数」，计进 total 会虚报。故单列返回、日志分开陈述。

### (f) 孤儿门 0 → ≥2

| 判据 | 改前 | 改后 |
|---|---|---|
| 主判据（滤 `Replaced by`） | **0** | **2** ✅ — `traces.py::replay_fallbacks` + `main.py` 回填门在线分支（实测 :137 / :416，随整改漂移，以符号为准） |
| 验伪锚（不滤） | 1 | **3**（恰 +1，多出 `memory_service.py:2690` docstring）✅ |
| `get_fallback_sync_service()` | 0 | **3** ✅ |

证据：`orphan-gate-before-20260914T204349.txt` / `orphan-gate-after-20260914T223040.txt`（成对落档）/ **`orphan-gate-final-*.txt`（最终 HEAD `d90f5a67` 重跑）**

三轮整改后在最终 HEAD 重跑，结论不变：主判据仍 **2**（`traces.py:137` + `main.py:416`，行号随整改漂移，符号为 `replay_fallbacks` 与回填门在线分支）、不滤仍 **3**（恰 +1）、工厂调用仍 **3**、pathspec 验伪锚仍成立（glob 形态空输出 / 目录形态命中 `main.py`）。

### (g) 真库 7692 端到端门 — 6 passed

`replay-green-postformat-20260914T223402.txt` → `6 passed`，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`

用例链：

1. `test_gate_never_targets_live_7691` — 环境自证
2. `test_offline_entry_replays_into_graph_via_admin_endpoint`（**承重**）— 写 `failed_writes.jsonl`（tmp 隔离）→ 经鉴权端点触发 → 直接查 7692 断言 `(:User{id:'default_user'})-[:LEARNED]->(:Concept{name:…})`，逐字段核 `score==73`、`timestamp`、`Concept.group_id` 非空且为 `vault__*` 物理格式且 **≠ DEFAULT 污染桶**、`LEARNED.group_id == Concept.group_id`（W1 复合写身份）。**前置自证**：回灌前该 Concept 查询必须为空，否则正向断言恒真
3. `test_second_replay_is_idempotent` — 第二次 `recovered == 0` 且门前缀节点数**逐标签相同**
4. `test_admin_endpoint_rejects_missing_key_403` / `_wrong_key_403` / `_unconfigured_key_503`

> **幂等的真实防线（如实声明，与卡文「幂等靠 MERGE」的表述有出入）**：挡住重复的**不是** Cypher MERGE。`neo4j_client.record_score_history` 是 `CREATE (e:Episode {id: randomUUID()})` —— 同一条目真被重放两次**会多出一个 Episode**。真正挡住的是 `_sync_failed_writes` 成功后的 `_rotate_file`（文件搬走 ⇒ 第二轮无输入）。所以「节点数逐标签不变」这条断言验的是**那条**防线。MERGE 只保住 Concept/LEARNED 不重复。
>
> 因此端到端门只播种 `failed_writes`，另两条链指向不存在的 tmp 路径 —— `learning_memories` 不轮转，若播种它则第二次仍会重放，幂等断言无从成立。

**这条设计依据已单独实证，不是推断**（`learning-memories-not-rotated-20260914T224129.txt`，真 7692 + tmp 隔离）：

| | 第一次 | 第二次 |
|---|---|---|
| `learning_memories` stats | `{'recovered': 1, 'pending': 0}` | `{'recovered': 1, 'pending': 0}` |
| 文件是否还在 | `True` | `True` |

⇒ 该链每次回灌都会**全量重放**。**但这不是缺陷**：`_replay_learning_memory_to_neo4j` 的 Cypher 只有 `MERGE` + `SET`（last-write-wins），**零 `CREATE`、且不调 `record_score_history`**（该方法体内 `grep -c 'record_score_history'` = 0）—— 所以重复重放在图上是幂等的，不累积节点。(c) 让它每次启动都跑，代价是**性能**而非正确性：每次启动多执行 N 条 MERGE，而 N 随该文件单调增长（该文件从不轮转、写侧无界 ⇒ 归 T6-C）。已登记为已知代价，见台账条目 ⑪。

**门的输入形态与生产写侧逐字段核对**（防「门在验一个现实中不存在的输入」）：`failed_writes.jsonl` 有**两个非测试写侧**：

| 写侧 | 条目 schema | `sync_all_fallbacks` 能否重放 |
|---|---|---|
| `agent_service.py:118-131`（Story 38.6 评分失败） | `{timestamp, event_type, concept_id, canvas_name, score, error_reason, concept, user_understanding, agent_feedback}` | **能** ✅ |
| `memory_service._record_structured_outbox:502`（A7 结构化写入失败） | `{kind:"knowledge_entity", event_type, content, metadata, group_id, timestamp}` | **不能** ❌ |

本门 seed 的条目字段照抄第一种（主写侧），故门验的是真实存在的输入形态 ✅

> ### ⚠️ 本卡实证发现的一个真实覆盖缺口（如实登记，非假绿）
>
> `_replay_scoring_entry_to_neo4j` 取 `concept = entry.get("concept") or entry.get("concept_id", "")`，而 `knowledge_entity` 条目**两个字段都没有** ⇒ 判「Skipping entry with no concept」→ `return False` → 计 `pending` 写回文件。
>
> **实证**（`schema-gap-knowledge-entity-20260914T224351.txt`，同一文件播种 A/B 两条，真 7692）：
>
> ```
> failed_writes stats = {'recovered': 1, 'pending': 1}
> A 条目 → 图内可查: True
> 回灌后文件剩余条目数 = 1
>   剩余条目 kind='knowledge_entity' 有 concept 字段=False
> ```
>
> **数据不会丢**（条目被原样写回文件），但**永远回灌不了** —— 能处理它的是 `recover_failed_writes`（孤儿②，按 `entry.get("kind") == "knowledge_entity"` 分流走 `record_knowledge_entity`），而那个方法**仍是零调用方**。
>
> 即：本卡把 `failed_writes.jsonl` 的**评分类**条目接通了，`knowledge_entity` 类条目的消费者缺口**依然存在**。这直接抬高了台账条目 ③（`recover_failed_writes` 处置）的优先级 —— 它不是「可疑的死代码」，而是「某类条目的唯一消费者，至今未接通」。本卡范围内未修（接通它属于另一处接线，且需先裁定两个重放器的职责边界）。

DD-03 合规：回灌走真 `Neo4jClient` → 真 7692，sync 路径零打桩。隔离手段仅为「把三条暂存文件与 checkpoint 的路径常量指向 `tmp_path`」+「把服务单例换成指向 7692 的实例」，被测代码一字未改地真实执行。

### (h) pyright 保持 0

`pyright-close-20260914T223914.txt` → **`0 errors, 81 warnings, 0 informations`**（cwd = `backend/`，与 B14_BASE 逐字同）。本卡未新增任何 `# pyright: ignore`。⛔ 未用 `LEFTHOOK_EXCLUDE=python-typecheck`。

### ruff（(o) 新增行自证）

`ruff-close-20260914T223914.txt` → `files=4`（四个改动文件全覆盖），`All checks passed!`，`rc=0`。
**验伪锚**（`ruff-worktree-20260914T223131.txt`）：初版锚用 F401 **没红** —— 诊断发现 `backend/ruff.toml` 的 `select = ["E9","F63","F7","F82"]` 里**没有 F401**，即锚超出了判据的扫描面，说明的不是判据失效。改用扫描面内的 **F821**（未定义名）后 `anchor_rc=1` ✅，证明判据真在抓 lint、非空跑。
`ruff format --check` 四文件全 `already formatted`。

### (i) 既有套件不回退

**名单**（`grep -rl 'fallback_sync|failure_counters|failed_edge_syncs|backfill_vault' backend/tests` + traces 相关）：`test_story_38_8_fallback_sync.py`、`test_failure_observability.py`、`test_vault_backfill.py`、`test_qa_38_6_scoring_reliability_extra.py`、`test_sync_exception_classification.py`、`test_cypher_contract_gate.py`、`test_all_index_entrypoints_hostile_env.py`

`suite-close-20260914T223139.txt` → `1 failed, 181 passed, 5 skipped`，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`
唯一红 `test_qa_38_6_scoring_reliability_extra.py::TestMergedViewEdgeCases::test_merged_view_sort_newest_first` **既有**：同时在 `$BASE:47` 与开工基线 `open.nodeids:48` 命中 ⇒ 本卡引入红 = **0** ✅

`tests/unit` 目录级 diff：见 §二。

### (j) openapi 待主 session 再生（本卡不修）

`openapi-drift-20260914T223237.txt` → `test_committed_snapshot_has_no_drift` **FAILED**（预期）。
`lefthook-spec-sync-skipped-20260914T223317.txt` 给出完整因果链：

- lefthook 的 `spec-sync-flat`（`lefthook.yml:60`）与 `spec-sync-root`（`:71`）会**自动重生成并 `git add backend/openapi.json`** —— 与卡文 (j)「commit 不含 openapi.json」直接冲突，故本卡 commit 时 `LEFTHOOK_EXCLUDE=spec-sync-flat,spec-sync-root`。
- **被跳过 hook 的本体输出已落档**：单独跑 `check-openapi-drift.py --write <scratchpad>/openapi-preview.json` → `generator_rc=0`（`paths=198 schemas=357`），hook 本身没坏，是本卡刻意不落盘。
- **漂移确实来自本卡新端点**：预览快照 `grep -c 'replay-fallbacks'` = **1**，仓内快照 = **0**。
- 仓内 `backend/openapi.json` 全程 `git status` 空 ⇒ 未改动；commit 文件面实测 4 个文件，不含它 ✅
- ⚠️ 被跳过的**不是** `python-typecheck`（那条是本批硬禁），本卡 pyright 实测 0 errors 未绕。

### (k) 负控输入（两段）

**段① 拆掉端点鉴权依赖 → 鉴权用例必红**（`negctl-1-auth-20260914T223707.txt`）

| 项 | 值 |
|---|---|
| 跑前 shasum(`traces.py`) | `6e85d3b41a8b027bf04a5fbdac8eca3aeb546d477bb8c0065227b83130e6a40d` |
| 变异后 shasum | `6659cfa370c72f762e361f9b60453a78d4187723e77cbb60b7dc7a0d750d5ca7`（不同 ⇒ 变异真落上） |
| 变异后该行剩余命中 | **0** |
| 门结果 | `3 failed`，分别红在 `assert 200 == 403` ×2、`assert 200 == 503` ×1 —— 正是指定断言 |
| 还原后 shasum | `6e85d3b41a8b027bf04a5fbdac8eca3aeb546d477bb8c0065227b83130e6a40d` —— 与跑前**逐字同** ✅ |
| 还原方式 | EXIT trap 无条件 `cp`，基准取自 `git show HEAD:<path>`。⛔ 未用 `git stash` / `git checkout HEAD -- <path>` |
| 现网触碰 | `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` ✅ |

> **本段第一次跑时抓出并已修的一个真实弱点**：初版三条鉴权用例不挂 `gate_client`。正常态下鉴权依赖在 handler 之前拒掉请求、端点体不执行，实测零连接；但**负控要拆的正是那层鉴权**，拆掉后未被拦下的输入会落进端点体，`get_fallback_sync_service()` 返回进程默认单例 → 按 `backend/.env` 的 `NEO4J_URI=bolt://localhost:7691` 去连**现网**（首跑响应即 `{"skipped":true,"reason":"Neo4j unhealthy"}`）。已给三条用例挂上 `gate_client`，把单例换成指向 7692 的实例 —— 于是「本门在任何状态下都不指向现网」成为结构性事实，不再依赖「鉴权恰好先拦住」这个前提。修后重跑负控，变异态实测 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`。

**段② 摘掉两处 `sync_all_fallbacks()` 调用 → 「回灌后图内可查」必红**（`negctl-2-replay-20260914T223739.txt`）

| 项 | 值 |
|---|---|
| 跑前 shasum | `traces.py` `6e85d3b4…`、`main.py` `8b50529de1be4098e7cd8598dbb50d326a87e8ba1537017224c0c6756611fd70` |
| 变异后 shasum | `434060d6…` / `790976ff…`（两文件均不同 ⇒ 变异真落上） |
| 变异后孤儿门主判据 | **0**（从 2 回落到 0 ⇒ 变异真摘掉了两处调用） |
| 门结果 | `2 failed` —— 承重用例红在 `:302` 的「回灌后图内可查」断言（`assert []`），幂等用例红在 `assert 0 == 1` |
| 还原后 shasum | `6e85d3b4…` / `8b50529d…` —— 与跑前**逐字同** ✅ |
| 现网触碰 | `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` ✅ |

> **这一段证明了什么**：变异态下管理端点**仍返回 200**、stats 形状**仍然正常**（`{"failed_writes":{"recovered":0,"pending":0}}`），但图里查不到 —— 即本门的绿**不是**由 stats 自述兑现的，而是真绑在「图内内容」上。换言之门没有在验夹具自写的图。
> 变异手法说明：调用行被替换为形状相同但不回灌的返回值，而非整行删除 —— 整行删除会让 `stats`/`replay` 未定义抛 `NameError`，那样红的身份是「端点炸了」，不是「门绑在接线上」。

### (l) 地盘门

`territory-20260914T223812.txt`（Codex 前）/ `mainpy-hunk-20260914T223824.txt` / `territory-final-20260914T224909.txt`（绑 `d9fa0774`）/ **`territory-final-r3-*.txt`（最终 HEAD `d90f5a67`）**

主判据 `git --no-pager diff --stat --no-color 310eef31 HEAD -- . ':(exclude)_bmad-output'`（最终 HEAD `d90f5a67`）：

```
 backend/app/api/v1/endpoints/traces.py             |  70 ++-
 backend/app/main.py                                |  57 +++
 backend/app/services/fallback_sync_service.py      |  86 ++++
 .../integration/test_neo4j_replay_wire_t6b.py      | 476 +++++++++++++++++++++
 4 files changed, 688 insertions(+), 1 deletion(-)
```

三轮整改后逐轮重跑，结论始终不变：同样 4 个文件、⊆ 白名单、禁改文件全空、`main.py` 两 hunk 始终是 `-402,0` 与 `-404,0` 两个**纯插入**、删除行数始终 **0**、`:381-384` import 块始终逐字原样。最终 HEAD 的实测见 `territory-final-r3-*.txt`。

⚠️ round-2 整改引入了对 `backend/tests/support/live_port_guard.py` 的**调用**（`canonical_target_ports` / `ALLOWED_TEST_PORTS`）。该文件已一并纳入禁改文件核，实测**未改动** —— 本卡只 import，不动它一个字。

⊆ 卡文 §一(l) 白名单 ✅（未动 `memory_service.py` / `failure_counters.py` / `failed_writes_constants.py`）
禁改文件核（`security.py` / `system.py` / `openapi.json` / 两个 `conftest.py`）：**全空** ✅

**`main.py` 逐 hunk（`-U0` 形式证据，这是最强的一条）**：

```
@@ -402,0 +403,22 @@   ← 纯插入, 删 0 行, 插在改前 :402 之后 = if 分支体末尾（:403 else 之前）
@@ -404,0 +427,17 @@   ← 纯插入, 删 0 行, 插在改前 :404 之后 = else 分支体末尾（:405 except 之前）
```

`-N,0` 直接证明两个 hunk 都是纯插入、零删除行 ⇒ `:381-384` 既有 import 块与 `:405-406` except 段**一字未动**（改后 `sed -n '381,384p'` 与改前逐字同，已落档）。新 import 均为分支内 inline，位置 ≫ :386 ✅

**AST 结构归属核（`mainpy-ast-structure-20260914T224223.txt`）** —— 行号判据只说明「插在哪两行之间」，AST 才说明「语法上属于哪个分支」：

```
回填门 if 节点: lineno=387
  if-body  行区间: 391..424   else-body 行区间: 426..443
if-body(在线分支):  backfill_vault@[392]  sync_all_fallbacks@[416]  count_fallback_backlog@[]
else-body(离线分支): backfill_vault@[]     sync_all_fallbacks@[]     count_fallback_backlog@[436]
顺序: backfill_vault@392 < sync_all_fallbacks@416 ⇒ True
回灌调用包在内层 Try@415, handler 数=1 ⇒ 不落外层 except
离线分支中 initialize/run_query/health_check 调用数 = 0 (期望 0)
```

即：(c) 确实落在**在线分支**且在 `backfill_vault` **之后**；(e) 确实落在**离线分支**；(c) 的回灌调用确实包在**自己的 Try** 里（回灌异常不会被外层 except 记成「启动回填 failed」）；(e) 的离线登记路径上**一条 Neo4j 连接类调用都没有**。

**验伪锚（如实声明未成立的那一次）**：地盘门首跑时「去掉 `':(exclude)_bmad-output'` 应多出 `_bmad-output/` 路径」这条验伪锚**没有成立** —— 输出与主判据完全相同。原因是当时 evidence 与本验收单尚未 commit（untracked），`310eef31..HEAD` 里确实不存在 `_bmad-output` 的已提交改动。这是真实状态，不是判据失效。文档 commit 后已重跑，见 §二 末条。

### (m) 现网只读

- 新测试文件全部连接行已落档（`territory-*.txt` 末段）：唯一 URI 是 `NEO4J_TEST_URI`（默认 `bolt://127.0.0.1:7692`），三条暂存文件 + checkpoint + client storage_path 全部 `tmp_path`，无一指向 live vault。
- 探针对 `:7691` **一律拒绝**（`_test_neo4j_reachable` 首行），并有可执行契约 `test_gate_never_targets_live_7691`。

**skip 行为验证（`skip-behavior-20260914T225225.txt`）** —— 附带一个有价值的发现：

原计划用「改 `NEO4J_TEST_URI` 再跑一次 pytest」来验证「7692 不可达 ⇒ 整文件 skip」，**这个方法行不通**：`backend/tests/conftest.py:100` 的 W4 哨兵在 `pytest_configure` 阶段就调 `live_port_guard.assert_test_uri_not_blocked()`，端口白名单**只有 `[7692]`**，指向 7999 或 7691 都会让整个 pytest 会话 `INTERNALERROR` —— 根本进不到本文件。⇒ **W4 哨兵是比本文件级探针更早、更硬的一道防线**（想把测试指向现网，在 pytest 启动阶段就被拦死）。

改为直接驱动 skipif 的判据函数：

```
当前环境 _test_neo4j_reachable() = True  (7692 在跑)
  不可达端口   bolt://127.0.0.1:7999            → reachable=False ⇒ skipif 触发=True
  现网 7691   bolt://127.0.0.1:7691            → reachable=False ⇒ skipif 触发=True  (短路拒绝, 不发起连接)
  不存在的主机 bolt://no-such-host.invalid:7692 → reachable=False ⇒ skipif 触发=True
```

⚠️ **如实声明这验到了哪一层**：验的是 `skipif` 的**输入**（判据函数对三类失败输入都返回 `False`），`skipif` 本身把整文件标 skip 是 pytest 的机制。「7692 容器真的停掉时整文件 skip」这个端到端表现**未实测**（停共享容器会影响其它在跑车道），已登记进 §五。
- 全部跑门输出的 W4 哨兵均为 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`。
- `grep -rn 'fsrs_bridge|decay_beta' <本卡四个改动文件>` → **0 命中** ✅

---

## ⚠️ 批级环境变更登记（协议 §2.3）

**2026-09-14 22:26 启动 Docker Desktop**（用户当次显式授权后执行）。如实记录实况：

- 开工时 Docker daemon 未运行，`7691 / 7687 / 7692` 三个端口全部 `ConnectionRefused`。
- 启动 daemon 后，`docker-compose.yml` 中 `restart: unless-stopped` 策略把**三个容器一并自动拉起**：`canvas-learning-system-neo4j`（现网 7691）、`canvas-learning-system-neo4j-test`（7692）、`canvas-learning-system-backend`（8011）。
- 我随后跑的 `docker compose --profile test up -d neo4j-test` **因容器名冲突失败、未创建任何容器** —— 7692 是被 restart 策略恢复的，不是我建的。证据 `docker-neo4j-test-up-20260914T222629.txt`。
- 7692 可达性与基线：`neo4j-7692-probe-20260914T222636.txt` → `REACHABLE; node count = 113`。
- 本卡全程未连 7691（全部门的 W4 哨兵计数为 0）。
- ⛔ 按本卡硬边界未改手册 §零 —— 该批级通告需**主 session 代为落手册**并通知其余在跑车道（见台账待登记条目 ⑧）。

---

## 二 裁判输出索引

| # | 裁判 | 证据文件 | 末行/结论 |
|---|---|---|---|
| 1 | 第 0 分钟 | （见 §〇） | 全绿 |
| 2 | 孤儿门 改前/改后 | `orphan-gate-before-20260914T204349.txt` / `orphan-gate-after-20260914T223040.txt` | `rc=0`；0 → 2，验伪锚 +1 |
| 3 | 端到端门 改前红 | `replay-red-20260914T222821.txt` / `replay-red-identity-20260914T222842.txt` | `rc=1`；5 failed 1 passed，红在 `:305` |
| 3 | 端到端门 改后绿 | `replay-green-postformat-20260914T223402.txt` | `rc=0`；6 passed |
| 4 | 负控① | `negctl-1-auth-20260914T223707.txt` | `rc=0`（脚本）/ `gate_rc=1`；3 failed，shasum 前后同 |
| 4 | 负控② | `negctl-2-replay-20260914T223739.txt` | `rc=0`（脚本）/ `gate_rc=1`；2 failed，shasum 前后同 |
| 5 | pyright | `pyright-close-20260914T223914.txt` | `0 errors, 81 warnings`；`rc=0` |
| 6 | ruff（+验伪锚） | **`ruff-final-20260914T225036.txt`（最终 HEAD）** / `ruff-close-*.txt` / `ruff-worktree-*.txt` | `files=4` `All checks passed!` `rc=0`；锚 `anchor_rc=1`；`format --check` 4 files already formatted |
| 10b | 终审绑定 + 验伪锚 | `codex-binding-20260914T224933.txt` | `rc=0`；绑 `d9fa0774` diff 空，锚换 `cd1b5ae9` 非空 |
| 7 | 名单套件 | `suite-close-20260914T223139.txt` | `1 failed, 181 passed`；唯一红为既有 |
| 7 | `tests/unit` 目录级 | `unit-close-20260914T223803.txt` | 见下 |
| 8 | 地盘门 | `territory-20260914T223812.txt` / `mainpy-hunk-20260914T223824.txt` | `rc=0`；⊆ 白名单，`-N,0` 纯插入 |
| 9 | openapi 漂移（不修） | `openapi-drift-20260914T223237.txt` / `lefthook-spec-sync-skipped-20260914T223317.txt` | `rc=1`（预期红）/ `generator_rc=0` |
| 10 | Codex round-1 / round-2 | `codex-review-CARD-NEO4J-REPLAY-WIRE.md` / `-r2.md` | 见 §三 |
| 补 | round-1 整改后重跑（端到端门 / pyright / 名单套件） | `replay-green-r2fix-*.txt` / `pyright-r2fix-*.txt` / `suite-r2fix-*.txt` | `6 passed` / `0 errors, 81 warnings` / 唯一红为既有 |
| 补 | round-1 ④ 修复专项验证 + 验伪锚 | `fix-utf8-verify-20260914T224637.txt` | `rc=0`；修后不抛、各记 warning；锚证明该字节确实触发 `UnicodeDecodeError` |
| 补 | AST 结构归属核 | `mainpy-ast-structure-20260914T224223.txt` | `rc=0`；(c) 在线分支且在 `backfill_vault` 后、包在内层 Try；(e) 离线分支零 Neo4j 调用 |
| 补 | `learning_memories` 不轮转实证 | `learning-memories-not-rotated-20260914T224129.txt` | `rc=0`；两轮 `recovered` 均为 1 |
| 补 | `knowledge_entity` schema 缺口实证 | `schema-gap-knowledge-entity-20260914T224351.txt` | `rc=0`；`{'recovered': 1, 'pending': 1}` |
| 补 | 凭据泄漏扫描（按键名，非猜格式） | `secret-scan-*.txt` | `rc=0`；落盘面命中 0，验伪锚命中 1 |
| 补 | skip 判据函数验证（含 W4 白名单发现） | `skip-behavior-20260914T225225.txt` | `rc=0`；三类失败输入均 `reachable=False` |
| 补 | `exists()` 吞权限错误（自审，带对照组） | `pathlib-exists-swallow-20260914T225326.txt` | `rc=0`；2 → 静默 0 无 warning → 还原 2 |
| 补 | 批级环境变更 | `docker-neo4j-test-up-*.txt` / `neo4j-7692-probe-*.txt` | 见 §「批级环境变更登记」 |

### §二.7 `tests/unit` 目录级收工 diff

逐轮重跑（代码每前进一次就重跑一次）：

| 跑 | 绑定 | 汇总 | nodeid | diff base vs close |
|---|---|---|---|---|
| `unit-open-20260914T204341.txt` | 开工（= `08100483` 代码树） | `36 failed / 5076 passed / 29 errors` | 65 | — |
| `unit-close-20260914T223803.txt` | `cd1b5ae9` | `33 failed / 5079 passed / 29 errors` | **62** | 只有 `<` ✅ |
| `unit-close-final-20260914T230416.txt` | `d90f5a67` | `33 failed / 5079 passed / 29 errors` | **62** | 只有 `<` ✅ |
| `unit-close-7bcbfc1a-*.txt` | `7bcbfc1a` | `33 failed / 5079 passed / 29 errors` | **62** | 只有 `<` ✅ |
| `unit-close-ccb1d101-*.txt` | **`ccb1d101`（最终 HEAD）** | `33 failed / 5079 passed / 29 errors` | **62** | 只有 `<` ✅ |

⇒ **五轮整改全程 `close` 恒为 62，diff 恒只有 `<`、零 `>`** —— 本卡引入 unit 红 = 0，且每一轮都在最终代码上重跑过（`unit-diff-final-*.txt`）。

`base=64` / `open(开工)=65` / `close=62`（两轮整改后不变）

**[卡文判据] `diff base.nodeids close.nodeids` — 只有 `<`，零 `>` ✅**

```
48,49d47
< FAILED tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration::test_fallback_sync_called_in_lifespan
< FAILED tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration::test_main_imports_fallback_sync
```

**[本卡引入判据] `diff open.nodeids close.nodeids`（同代码树的开工态）— 同样只有 `<`，零 `>` ⇒ 本卡引入红 = 0 ✅**

```
33d32
< FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422
48,49d47
< …TestStartupIntegration::test_fallback_sync_called_in_lifespan
< …TestStartupIntegration::test_main_imports_fallback_sync
```

#### 🟢 转绿的两条是本卡价值最强的**独立**证据

这两条**不是本卡写的门**，而是仓里**早就存在、一直红着**的测试：

```python
class TestStartupIntegration:
    """Verify main.py lifespan calls fallback sync (formerly recover_failed_writes)."""

    def test_main_imports_fallback_sync(self):
        """[P0] main.py references fallback sync service."""
        assert "get_fallback_sync_service" in source

    def test_fallback_sync_called_in_lifespan(self):
        """[P0] Fallback sync call exists in lifespan context manager."""
        assert "sync_all_fallbacks" in source
```

即：**「启动 lifespan 应当调用回灌」这条 P0 契约在仓里写着、并且一直未兑现**（两条测试常红，且都在 `$BASE` 红基线里）。本卡的接线把它们转绿 —— 这条证据由本卡之外的人预先写下，不受本卡自证偏差影响。

#### 关于 `test_candidate_service::test_accept_candidate_already_accepted_returns_422` 的更正

开工目录级跑与孤立跑**都红**，收工目录级跑**绿**。故它是**不稳定**（环境/时序相关），而非我先前判断的「稳定红」—— 以收工实测为准更正。无论哪种，它都不在 `close` 里，不影响任何判据方向。

#### 地盘门验伪锚补跑（文档 commit 后）

见本节末「§二.10 终审绑定」——该条的验伪锚一次成立。地盘门自身的 `_bmad-output` 验伪锚在文档 commit 后补跑，见 §七。

### §二.10 终审绑定（`codex-binding-20260914T224933.txt`）

```
round-2 审 SHA = d9fa0774 ; 当前 HEAD = d9fa0774
git --no-pager diff --stat --no-color d9fa0774 HEAD -- . ':(exclude)_bmad-output'
  → 空  ⇒ 仍绑定 ✅
验伪锚: 同命令换 round-1 的 cd1b5ae9 → 4 files changed, 43 insertions(+), 8 deletions(-)
  ⇒ 该判据真能测出失绑（不是恒空的死判据）✅
```

存档内旧复核模型名计数 = **0**（两份存档均 0）✅ · round-1 存档首部 `模型`/`reasoning_effort`/`codex` 三字段齐 ✅

### 关于本卡的验伪锚（如实记录 3 次「锚不成立」及其诊断）

本卡共设 5 处验伪锚，其中 3 处**首次没有成立**，全部经诊断后判明是「锚超出判据范围」而非「判据失效」，并换用有效锚重跑：

| 锚 | 首次结果 | 诊断 | 处置 |
|---|---|---|---|
| ruff 判据 | 用 F401 锚 **没红** | `backend/ruff.toml` 的 `select = ["E9","F63","F7","F82"]` 里**没有 F401** ⇒ 锚超出扫描面 | 换扫描面内的 **F821**，`anchor_rc=1` ✅ |
| 凭据扫描 | 正则锚对 `.env` 本身也 **0 命中** | 正则是按 `sk-` 等格式猜的，而 `.env` 里唯一凭据键 `GOOGLE_API_KEY` 不是那些格式 | 改为**按键名取值本体逐字搜**，锚对 `.env` 命中 1 ✅ |
| 地盘门 `_bmad-output` | 去掉 exclude 后输出**完全相同** | 当时 evidence 与验收单尚未 commit（untracked），`310eef31..HEAD` 里确实没有 `_bmad-output` 的已提交改动 ⇒ 真实状态，非判据失效 | 文档 commit 后补跑，见 §七 |

> 记这一节是因为：验伪锚不红有两种解释 —— 判据失效，或锚超出判据范围。不诊断就记「判据通过」，等于把假绿写进验收单。

---

## 三 Codex 复核

### round-1 — 绑 `cd1b5ae9`

存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE.md`（5733 字节）
Codex 自报计数：**BLOCKER 0 / HIGH 0 / MEDIUM 4 / LOW 1** —— 按 D-15 已达合并门。

Codex 独立确认的两件事（对本卡承重主张的外部背书）：

- 「负控输入②足以排除**该管理端点评分路径在验夹具预置图或只验 stats**」
- 「`main.py` 两个 hunk 均为所述纯插入」
- ⑤「新增 diff 没有 `pyright: ignore`；`.get()` 前的 `dict` 判断和 `len()` 前的 `list` 判断正确」—— 不计缺陷
- ⑥「三个拒绝用例都装配了隔离文件和服务实例……正常鉴权复用了原依赖，`security.py` 未改」—— 不计缺陷

**四条被采纳并改码（不是只登记）** —— 其中三条属于「自身注释做了承诺而代码没兑现」，一条是承重判据的真实弱点：

| Codex | 定性 | 处置 |
|---|---|---|
| ① MEDIUM 首轮 Episode 数没锁定 | 幂等判据可被「首轮就重复」蒙混（2→2 也通过） | **改测试**：首轮断言从 `Concept == 1` 改为逐标签绝对值 `{Concept:1, Node:1, Canvas:1, Episode:1}` |
| ② MEDIUM 内层异常处理没识别「以返回值表示失败」 | `sync_all_fallbacks` 把子同步异常吞成 `{"recovered":0,"pending":0,"error":…}`，摘要只求和 ⇒ 三条链全炸也打成「回灌 0 条, 0 条待回灌」，与「本来就没东西要回灌」逐字相同。**正是本卡在 commit message 里声称要消灭的那类伪装** | **改 `main.py`**：先查 `error` 字段，非空走 `logger.error` 点名哪几条链未回灌 |
| ③ MEDIUM 「仅计数、不返回路径」的承诺不成立 | 端点 docstring 原写「no file paths are echoed back」，但 `error`/`reason` 带 `str(e)`，`OSError` 通常内嵌绝对路径 —— **我的注释不实** | 卡文要求「原样返回 stats」故不改返回值；**改 docstring 如实声明**泄漏面 + 「不加脱敏就别放宽受众」，并登记 |
| ④ LOW 非 UTF-8 文件会被误报为回填失败 | `UnicodeDecodeError` 是 `ValueError` 子类、**不是** `OSError`，不在捕获集内 ⇒ docstring 承诺的「格式坏按 0 计并记 warning」当场落空 | **改两个计数 helper** 的捕获集 |

**④ 的修复另有专项验证**（`fix-utf8-verify-20260914T224637.txt`）：

```
UnicodeDecodeError 是 ValueError 子类 = True
UnicodeDecodeError 是 OSError 子类    = False  ← 这就是漏的原因
修后 count_fallback_backlog(两个坏文件): 未抛异常 ✅  返回 = {...'pending_total': 0}
  [T6-B backlog] Cannot read failed_writes.jsonl: 'utf-8' codec can't decode byte 0xff …
  [T6-B backlog] Cannot parse canvas_events.json: 'utf-8' codec can't decode byte 0xff …
验伪锚: 抛了 UnicodeDecodeError ✅ ⇒ 坏字节确实会触发该异常
```

**round-1 ⓪（门未覆盖启动与生产单例装配）未改码**，理由：那是测试覆盖面问题而非缺陷，已逐条登记进 §五「本卡未证明什么」⑥；真跑 lifespan 会连现网 7691 并读 live vault，本卡硬边界明令禁止。该理由已写进 round-2 prompt 请 Codex 判定（车道不自判通过）。

整改 commit：`d9fa0774`（`4 files changed, 43 insertions(+), 8 deletions(-)`）。用**新 commit 而非 amend**，以保留 round-1 绑定 SHA `cd1b5ae9` 的可追溯性。
整改后重跑：端到端门 **6 passed**、pyright **0 errors, 81 warnings**、名单套件唯一红仍为既有那条、lefthook `python-lint` + `python-typecheck` 本次**真跑**（有 staged files）且均过。

### round-2 — 绑 `d9fa0774`（最终 HEAD）

存档：`codex-review-CARD-NEO4J-REPLAY-WIRE-r2.md`（7577 字节）
Codex 自报计数：**BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 2** ⇒ 按 D-15「最后一轮必须 BLOCKER=0 **且 HIGH=0**」，**必须整改重送**，本轮不签署通过。

#### 🔴 HIGH-1 是真缺陷，且打中要害 —— 现网端口保护可被绕过

`test_neo4j_replay_wire_t6b.py` 的 `_test_neo4j_reachable` 与 `test_gate_never_targets_live_7691`（round-2 时 :62/:74/:277） 两处保护都只做字符串子串检查 `":7691" in NEO4J_TEST_URI`。
**未被拦下的输入**：`bolt://127.0.0.1:07691`（前导零）—— 字符串检查放行，而驱动 `Address.parse` 解析后端口就是 **7691**（Codex 用工作树实际安装的 neo4j 6.1.0 解析器确认）。随后 `verify_connectivity()` 会真的连上去，凭证有效时夹具清理还会执行。

**根因归类**：字符串面与驱动面是**两个不同的输入面**。在字符串面上判「这不是现网」，证明不了驱动面上「不会连现网」——这正是工程坑索引里「同一正则作用在不同输入面 ≠ 同口径」那条。

**修法**：不再自己解析，改问驱动本人 —— 复用仓里现成的 `tests/support/live_port_guard.py::canonical_target_ports()`（它复现的正是 `parse_neo4j_uri → urlparse → Address.parse{,_list}` 整条链），并把判据从**反向黑名单**改成**正向白名单**（端口必须 ∈ `ALLOWED_TEST_PORTS`）：黑名单漏一个端口就放行，白名单漏一个只会多 skip 一次。解析失败 fail-closed；routing scheme 的多地址逐个校验。可执行契约 `test_gate_never_targets_live_7691` 同步升级，并在用例内嵌对 `:07691` 的负控自证。

**修复实测对照**（`fix-r2-verify-*.txt`）：

| URI | 旧字符串判据 | 驱动解析端口 | 新判据 |
|---|---|---|---|
| `bolt://127.0.0.1:7692` | 放行 | `(7692,)` | 放行 ✅ |
| `bolt://127.0.0.1:7691` | 拒绝 | `(7691,)` | 拒绝 |
| **`bolt://127.0.0.1:07691`** | **放行** ❌ | `(7691,)` | **拒绝** ✅ |
| **`bolt://127.0.0.1:007691`** | **放行** ❌ | `(7691,)` | **拒绝** ✅ |
| **`bolt://127.0.0.1`**（无端口） | **放行** ❌ | `(7687,)` | **拒绝** ✅ |
| **`bolt://127.0.0.1:0`** | **放行** ❌ | `(7687,)` | **拒绝** ✅ |
| `neo4j://ok:7692 evil:7691`（routing 多地址） | 拒绝 | `(7692, 7691)` | 拒绝 ✅ |

⇒ 旧判据放行了 **4 条**实际指向现网（7691/7691/7687/7687）的输入。

**17 种边界输入自查**（`port-guard-edge-cases-*.txt`，对应 round-3 prompt 问题⓪(b)）—— 摘几条关键的：

| 场景 | URI | 驱动解析 | 新判据 |
|---|---|---|---|
| **主机名含 7691** | `bolt://host7691:7692` | `(7692,)` | **放行** ✅ |
| 端口 `00` | `bolt://127.0.0.1:00` | `(7687,)` | 拒绝 ✅ |
| routing 双地址含现网 | `neo4j://ok:7692 evil:7691` | `(7692, 7691)` | 拒绝 ✅ |
| routing 全测试端口 | `neo4j://a:7692 b:7692` | `(7692, 7692)` | 放行 ✅ |
| 带 userinfo | `bolt://u:p@127.0.0.1:7692` | `None`（驱动拒） | 拒绝 ✅ fail-closed |
| IPv6 现网 | `bolt://[::1]:7691` | `(7691,)` | 拒绝 ✅ |
| 非法 scheme / 空串 / 垃圾 | `http://…` / `""` / `not-a-uri` | `None` | 拒绝 ✅ fail-closed |

> `bolt://host7691:7692` 这条反向说明了旧判据的另一面毛病：它是**字符串**匹配，主机名里出现 `7691` 也会被误拒（假阴性）。新判据按端口判，主机名叫什么都不影响。

**「同一张卡里多处同源、改一处不够」的自检**（`no-residual-string-guard-*.txt`）——该字符串判据在本文件出现于**两处防线**（`skipif` 探针 + 可执行契约断言）。修完逐条核残留：

```
:64  [注释] 说明为何不能用字符串判据           ✅
:309 [注释] 记录原断言形态                     ✅
:326 [代码] assert ":7691" not in "bolt://...:07691"  ✅ 负控自证(断言的正是「旧判据看不见这条输入」这个前提)
真正的防线: :78 (探针) / :314 (契约) —— 均为 canonical_target_ports + ALLOWED_TEST_PORTS
```

⇒ 零残留，两处防线都改到了。

#### 其余四条的处置

| Codex | 定性 | 处置 |
|---|---|---|
| MEDIUM-2 空异常文本仍被误判为成功 | round-1 整改②的**不完整修复** —— `v.get("error")` 取真值，而捕获集里 `RuntimeError()`/`OSError()`/`ConnectionError()`/`TimeoutError()` 无参数时 `str(e) == ""` 是 falsy ⇒ 整条链失败却算成功 | **改码**：`"error" in v`（判键存在，不判真值）。实测四个无参数异常旧判据**全部漏判**，新判据全部识别为失败 |
| MEDIUM-4 清理查询越界删除 | 与本卡**自审结论一致**（见台账 11a，本卡先于 Codex 发现并已登记）。兜底那条无任何门身份约束，会删掉别的门留下的无边 scoring Episode | **改码**：加 `e.group_id IS NOT NULL AND e.group_id ENDS WITH '<本门 canvas 名>'`。用 ENDS WITH 而非 vault 前缀，因 group 解析成 `vault:<active_vault>:<canvas>` 后 vault 段随环境变 |

**MEDIUM-4 整改的双向验证**（`cleanup-anchor-verify-*.txt`）—— 锚既要覆盖本门、又不能越界：

```
本门 canvas 名        = 't6bgate_canvas'
解析出的逻辑 group    = 'vault:canvas_vault:t6bgate_canvas'
物理化后 (实际落库值) = 'vault__canvas_vault__t6bgate_canvas'
ENDS WITH 命中本门 group = True ✅

对照 (别的门的 group 不应被命中):
  vault__canvas_vault__g21gate_a      不命中(安全)   ← cypher_contract_gate 的 group
  vault__canvas_vault__other_canvas   不命中(安全)
  vault__canvas_vault                 不命中(安全)
  vault__other__t6bgate_canvas        命中 ← 同 canvas 名但别的 vault, 属本门语义内
```

⇒ 覆盖侧成立（vault 段随环境变也能命中），越界侧成立（别的门用别的 canvas 名，不会被误删）。
| LOW-5 JSON 计数仍有异常遗漏 | 负控输入 `'[' + '1'*5000 + ']'` 在 Python 3.11+ 整数字符串位数上限下抛**普通** `ValueError`，不在 `(OSError, UnicodeDecodeError, JSONDecodeError)` 内。Codex 实际复现 | **改码**：捕获集收敛为 `(OSError, ValueError)` —— `ValueError` 一次覆盖两个子类 + 那个普通 `ValueError`。**验伪锚**：实测该异常 `isinstance(e, json.JSONDecodeError)` = `False`，证明旧捕获集确实漏它 |
| LOW-6 端点 description 与 learning 链口径冲突 | description 承诺「entries are removed once replayed, second call reports recovered=0」，而 `fallback_sync_service` 明确声明 `learning_memories` 不轮转 —— **我自己的文档自相矛盾** | **改码**：description 改为分链如实陈述 |
| MEDIUM-3（round-1 ⓪ 的验收缺口） | Codex 接受「禁碰现网和 live vault 足以支持不跑 lifespan」这个理由，但坚持「**登记限制不能证明这些路径通过**」 | **未改码，登记不阻断**，见 §五 ⑥ |

Codex 本轮另行确认的几件事（对本卡的外部背书）：
- 整改① 确实挡住了「首轮 `Episode=2`、第二轮仍为 2」的负控输入
- 整改③ 可接受（已如实披露异常文本，`:96` 确实接入原鉴权依赖）
- 整改④ 的非法 UTF-8 负控「已确认 warning 后返回零」
- `pending_total` 排除 learning 链的理由**成立**

整改 commit：`d90f5a67`（`4 files changed, 79 insertions(+), 12 deletions(-)`）。
整改后重跑：端到端门 **6 passed**、pyright **0 errors, 81 warnings**、名单套件 + `test_live_port_guard_contract.py` 共 **332 passed**（唯一红仍为既有那条 —— 额外加跑 live_port_guard 契约测试是为确认复用其解析器没破坏它自己的契约）、lefthook `python-lint`/`python-typecheck` 真跑且过。

### round-3 — 绑 `d90f5a67`（最终 HEAD）

存档：`codex-review-CARD-NEO4J-REPLAY-WIRE-r3.md`
Codex 自报计数：**BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 2** —— Codex 原话「**满足所引 D-15 的 B/H 数量条件**」。

#### ✅ HIGH-1 修复经 Codex 独立验证成立

Codex 原话：「探针 `:78–85` 与契约 `:314–317` 都先拒绝空结果，再要求所有端口属于实际白名单 `{7692}`。**实际调用 helper，并对照 Neo4j 6.1.0 的解析入口**，确认前导零、默认端口、IPv6、大小写／空白及 routing 多地址中的现网端口均被拒绝；非支持 scheme、非空 userinfo 也被拒绝。」

它同时给了两条**更准确的措辞更正**（已接受）：

- helper 是「使用驱动的 `Address.parse/parse_list`，**手动复现** URI 检查与分流」，**没有直接调用完整 `parse_neo4j_uri`」** —— 我先前说「复现整条链」略过头了。
- 证明范围是**初始目标地址**；routing 服务器随后返回的地址属于「此次纯解析复核**未覆盖的路径**」。
- `:326` 那处剩余字符串判断「只是旧判据的负控自证，不是第三处保护判据」——与本卡自查结论一致。

#### 本轮两条改码、两条登记

| Codex | 定性 | 处置 |
|---|---|---|
| MEDIUM-1 清理身份仍会跨门匹配 | round-2 的 `ENDS WITH` 范围小了但**仍不是精确身份**：对照输入 `group_id='vault__other__other_t6bgate_canvas'` 同样满足尾缀；前四条的 `STARTS WITH 't6bgate'` 也吃 `t6bgate2_*` | **改码**：Canvas 路径**等值**、Concept/Node 用带分隔段的完整前缀（`t6bgate_concept_` / `t6bgate_cid_`）、Episode 的 group **等值**于 `_gate_group_id()` 运行时算出的真实物理 group（解析不出来整条跳过——宁可漏清不可越界），全部参数化传值。`_gate_node_count` 身份口径同步对齐 |
| LOW-4 U+2028 被当成额外记录 | JSONL 行分隔符只有 `\n`，而 `splitlines()` 还在 U+2028/U+2029/`\x0b`/`\x0c`/`\x1c-\x1e`/U+0085 处断行——这些在 JSON 字符串里是**合法原始字符** | **改码**：三处 `splitlines()` → `split("\n")` |
| MEDIUM-2 启动接线门覆盖缺口 | Codex 补充了一条我没写全的路径：`backfill_vault()` 抛异常时控制流**直接进 except**，回灌根本不执行 | **登记**（跑真 lifespan 会连现网并读 live vault，硬边界禁止），见 §五 ⑥ |
| LOW-3 `exists()` 使读取失败静默变零积压 | 与本卡**自审结论一致**（本卡先于 Codex 发现并已带对照组实证） | **登记**，见 §五 ⑦ |

#### LOW-4 的修复是实打实的行为修复，不只是计数

`fix-u2028-verify-*.txt`（真 7692 + tmp 隔离）：

```
面 1 计数: 文件里 1 条含 U+2028 的记录 → 计数 = 1 ✅（改前实测 = 2）
面 2 回灌: failed_writes stats = {'recovered': 1, 'pending': 0}
          图内可查 = ['t6bu2028_concept tail']
          回灌后文件是否已轮转走 = True
```

> **改前该条目的命运**：被 `splitlines()` 切成两个非法 JSON → 双双 `JSONDecodeError` → 双双走 `still_pending` 写回文件 → 下一轮再切再失败 —— **永远回灌不掉**。这是本卡接通的那条回灌链上的洞，所以既有的 `_sync_failed_writes` 两处也一并修了（它们的行数口径互相比较，只改一半会让 `len(current_lines) > len(lines)` 在含 U+2028 的文件上恒为真）。

整改 commit：`7bcbfc1a`（`2 files changed, 98 insertions(+), 33 deletions(-)`）。
整改后重跑：端到端门 **6 passed**、pyright **0 errors**、名单套件 + `live_port_guard` 契约共 **338 passed**（唯一红仍为既有）。

#### 本轮的两项自查（round-4 prompt 问题①② 的预答）

`crlf-checkpoint-selfcheck-*.txt`：

1. **CRLF —— 我原先给的理由是错的（结论对，理由弱）**。我说「写侧都用 `\n` 拼接故不产生 CRLF」，但真正的保证在**读侧**：`Path.read_text()` 默认 `newline=None` = universal newlines，实测 `b'{"a":1}\r\n'` → `'{"a":1}\n'`。即便存在 Windows 写侧或历史 CRLF 文件也安全。已把更准确的理由写进代码注释（见下方「审查期间的一次失误」）。
2. **checkpoint 语义** —— `checkpoint_idx` 按本函数切法存下标；错位需要三件事同时成立：① 上一轮中途崩溃留下 checkpoint ② 文件恰好含 U+2028 ③ 恰好跨这次版本升级。且成功路径结尾总会 `_clear_checkpoint`。根治要给 checkpoint 带口径版本号，超出本卡地盘 —— **登记**。

#### ⚠️ 审查期间的一次失误（如实记录）

我在 Codex round-4 **正审着工作树**的时候去改了 `fallback_sync_service.py` 的注释（补上面那条更准确的 CRLF 理由）。Codex 读的是**工作树**而非 commit，若它恰好在编辑瞬间读到，会基于一个从未存在过的中间态报问题。发现后立即用 `git show HEAD:<path> > <path>` 还原（⛔ 未用 `git checkout`），实测工作树 shasum 与 HEAD 逐字节相同、`git status` 空。那段注释暂存在 scratchpad，待 round-4 结束后作为**独立的纯注释 commit** 补上（协议 §1：纯注释尾巴逐行核后可判等价）。

### round-4 — 绑 `7bcbfc1a`（最终 HEAD）

存档：`codex-review-CARD-NEO4J-REPLAY-WIRE-r4.md`
Codex 自报计数：**BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 2** ⇒ 按 D-15 必须整改重送。

#### 🔴 HIGH 是 round-3 那次 U+2028 修复引入的回归，而且我自己低估了它

我在 round-3 后的验收单里把 checkpoint 错位登记为「跳过或重复几条」的**窄边界**并选择不修。Codex 用**纯内存实验**算出它真会丢数据：

> 首条合法 JSON 含 U+2028，后接普通记录 1–50；旧版切成 52 片，在完成普通记录 48 后保存 checkpoint=50 并中断。新版切成 51 行，载入旧值 50 后只处理记录 50，**尚未处理的记录 49 被跳过，也不进入 `still_pending`**。纯内存结果：旧版续跑 `[49,50]`，新版 `[50]`。

被跳过的条目不进 `still_pending` ⇒ 随 `_rotate_file` 一起搬走 = **真丢**。这不是「窄边界」，是我该修没修的回归。

#### 修法：第一版过重，被既有测试打回

- **第一版**：checkpoint 缺 `line_split` 标记就一律回退 0 → 打破既有 `test_resumes_from_checkpoint`（`assert 5 == 2`）。
- **那条红指出了判据划太宽**：只有文件**真含** U+2028 时两种切法才不同；不含时旧下标完全安全，回退 0 是白白重放。
- **精准版**：checkpoint 带 `line_split` 标记；标记不匹配时再用 `raw` **实测这个具体文件**在两种口径下行数是否相同 —— 相同则沿用，不同才回退 0 并记 warning。`raw` 只由按行切分的 `failed_writes` 传（另两条链走 `json.loads` 得 list，口径与切行无关）。

**四场景实测**（`fix-checkpoint-verify-*.txt`）：

| 场景 | 结果 |
|---|---|
| A 旧 checkpoint + 含 U+2028（Codex 的负控输入） | **回退 0** ✅ 记录 49 不再被跳过 |
| B 旧 checkpoint + 不含 U+2028（对照） | **沿用 50** ✅ 不做无谓重放 |
| C 新 checkpoint 带标记 | 沿用 50 ✅ |
| D `canvas_events`（不传 raw） | 沿用 7 ✅ 未误伤 |

> 这里值得记一笔：**既有测试红了不是麻烦，是它替我指出判据划得太宽**。第一版拿「类别」（旧格式）当判据，精准版拿「事实」（这个文件是否真的切不同）当判据。

#### 其余四条 —— 本轮**全部改码**，无一登记了事

| Codex | 处置 |
|---|---|
| MEDIUM-2 清理身份仍跨 vault／并行运行（另一 vault 的同名 canvas 仍被 canvas 等值删掉；并行另一轮的 `t6bgate_concept_<另一UUID>` 仍命中前缀） | **改码**：根因是锚是**门级**的而越界发生在**运行级**。每次运行分配一次性 `_GATE_RUN_ID`，`GATE_CANVAS` / 两个前缀全部带上它，清理与计数共用 |
| MEDIUM-3 启动回灌仍依赖回填先成功（`backfill_vault()` 抛异常 → 控制流直接进 except → 回灌根本不执行） | **⚠️ 我以为改好了，其实没有** —— 见下方「MEDIUM-3 的修法是假修复」 |
| LOW-4 清理与计数未逐字对齐（无标签 `MATCH` 靠 `name` 命中会把 Node 错算成 Concept，而清理要求「标签+属性」⇒ 清不掉 ⇒ 首轮绝对值断言持续假红） | **改码**：计数逐条绑「标签 + 属性」组合 |
| LOW-5 `exists()` 绕过 warning | **改码**：直接 `read_text`，`FileNotFoundError` 静默 0、其余记 warning。顺带**更正我上一轮写错的 CRLF 理由** —— 保证在读侧的 universal newlines，不在「写侧都用 `\n`」这个更弱的前提 |

#### 本轮自查：`_GATE_RUN_ID` 的隔离边界

`run-id-isolation-selfcheck-*.txt`：`GATE_PREFIX` 只出现在三个带 run id 的派生常量定义里，**零漏网**（清理 4 条 + 计数 4 处全部用派生锚）。
`run-id-repeat-run-*.txt`：同进程连跑两遍同一文件 **6 passed**；两个独立进程各跑一次 **6 passed / 6 passed**。同进程共用 run id 但每个测试的 fixture 做 setup/teardown 清理、`_seed_entry()` 另带自己的 uuid tag，故不冲突；跨进程 run id 不同，天然隔离。

整改 commit：`ccb1d101`（`3 files changed, 180 insertions(+), 80 deletions(-)`）。
整改后重跑：端到端门 + 既有 `fallback_sync` 套件 **36 passed**、pyright **0 errors**、名单套件 + `live_port_guard` 契约 **338 passed**（唯一红仍为既有）。

#### ⚠️⚠️ MEDIUM-3 的修法是**假修复**（Codex round-5 抓出，自查复核确认）

我把回灌移出回填 `try` 后，用 `_worker_online` 传在线状态，但把 `_worker_online = True` 放在了 `backfill_vault()` **之后**（实测 `main.py:410` 赋值 vs `:398` 回填）。于是：

```
backfill_vault() 抛异常 → 跳到 :413 except → 赋值行 :410 从未执行
                        → _worker_online 仍是 False
                        → 回灌走**离线分支**（只做只读计数，不回灌）
                        → 与修之前的行为**逐字相同**
```

**代码结构变了，行为没变。** 而我当时跑了端到端门、名单套件、pyright，全绿 —— 因为**没有任何一条测试覆盖「回填抛异常」这条路径**，那正是我自己登记为「门未覆盖」的那条（§五 ⑥）。

> 教训：**门未覆盖的路径上，重构等于无人看管**。在那种路径上做结构性改动，全绿不构成任何证据。

#### ⚠️⚠️ 同一处修法还引入了**卡文地盘约束违规**（自查发现，非 Codex 提出，待修）

卡文 §一(l) 硬要求：「`main.py` 的所有新增/修改行必须落在回填门 if/else 体 **:386-404**，⛔ 无一落在 `:381-384` 既有 import 块或 `:405-406` except 段」。

我为修 MEDIUM-3 把回灌**移出**回填 `try/except` 后，`main.py` 变成三个 hunk（`territory-final-r5-*.txt`）：

```
@@ -379,0 +380,6 @@    ← _worker_online = False + 注释, 落在 :380 `try:` **之前**
@@ -402,0 +409,2 @@    ← 门体内 (合规)
@@ -407,0 +416,59 @@   ← 回灌整段, 落在 :405-406 except 段**之后**
```

第一和第三个 hunk 都在 `:386-404` 之外 ⇒ **越界**（虽仍是纯插入、删除行数 0、`:381-384` import 块一字未动）。

**修法（既修 MEDIUM-3 又守住地盘）**：不移出，改为给 `backfill_vault(...)` 那几行**单独包一个内层 `try/except`** —— 回填失败被内层吃掉、不再跳过回灌，而回灌仍留在门体 `:386-404` 内。改动落在 `:392-402` 的缩进 + 新增内层 try，全部在约束区间内。

⚠️ 此修法待 round-5 跑完后实施（现在改会污染正在进行的审查 —— 这是本卡第二次踩「审查对象须冻结」，第一次见下方「审查期间的一次失误」）。**修完将超出 D-15 的 5 轮配额**，届时按规定交主 session 裁定是否需要第 6 轮。

### round-5 — 绑 `ccb1d101`（配额最后一轮）

存档：`codex-review-CARD-NEO4J-REPLAY-WIRE-r5.md`
Codex 自报计数：**BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 0**
Codex 原话：「**本轮发现 HIGH 1：应按 D-15 停下车道，交主 session 人审。**」

## 🛑 车道按 D-15 停车

配额 **5/5 用满**且末轮仍报 HIGH ⇒ 按 D-15「轮次上限 5，第 5 轮仍有 HIGH → 停下交主 session 人审」，**车道不再自行整改**。以下三项连同修法与边界一并移交。

### 待裁 ① HIGH — checkpoint 把「已尝试」当成「已成功」

`fallback_sync_service.py:282`（关联 `:259-261 / :275 / :278 / :660-661`）

**Codex 的定性（重要）**：「这是**本卡新增生产接线暴露的既有算法缺陷，非 r5 新引入**。」
即：`_save_checkpoint(i + 1)` 每 50 条推进一次游标，**无论该条重放成功还是失败**；失败条目只进内存 `still_pending`，尚未写回文件。若此时进程中断，重启后游标已越过它 ⇒ **该条目被永久跳过**。

**负控输入（Codex 纯内存实测）**：51 条合法记录，第 1 条失败、第 2–50 条成功；保存 `index=50` 后在第 51 条的 `await` 期间中断。
结果：`重启尝试=[51]，从未成功却被跳过=[1]`。
**对照输入**：前 50 条全部成功 —— 此时游标才是安全的。

**Codex 给的最小改法与边界**：
> checkpoint 只能推进到**连续成功前缀**，不能越过最早失败或畸形行；仅增加「当前条成功才保存」仍不够。还需增加进度语义版本，处理包括当前 `split-lf` 在内、无法证明前缀成功的历史游标。范围为回灌与 checkpoint 恢复逻辑；**旧游标回退可能重复评分 Episode，须由主 session 裁定迁移取舍**。

⚠️ 这条触及**既有算法**而非本卡新增面，且迁移取舍（回退旧游标 ⇒ 重复 Episode）是产品决策 —— 正是该交主 session 的那类。

### 待裁 ② MEDIUM — `_worker_online` 仍依赖回填成功（r4 MEDIUM-3 未关闭）

`main.py:410`（关联 `:398 / :427 / :464`）。**本卡自查已先于 Codex 确认**（见上方「MEDIUM-3 的修法是假修复」）。

**Codex 给的最小改法**：「在确认 `_worker_graphiti is not None` 后、**构造回填参数和执行回填之前**设置状态。取到 worker 之前失败时保留默认 `False`，可作为保守策略。」

**车道另备一个更彻底的修法（同时解决待裁 ③）**：不用状态变量，改为给 `backfill_vault(...)` **单独包内层 `try/except`** —— 回填失败被内层吃掉、回灌照常执行，全程没有「在哪一行赋值」这个隐式前提。且回灌可留在门体 `:386-404` 内，一并消除地盘违规。

### 待裁 ③ 卡文地盘约束违规（车道自查发现，非 Codex 提出）

见上方「同一处修法还引入了卡文地盘约束违规」：`main.py` 现有两个 hunk 落在 `:386-404` 之外（`:380` 前的 `_worker_online` 声明、`:405-406` except 之后的回灌整段）。待裁 ② 的「内层 try」修法可一并消除。

### 待裁 ④ MEDIUM — 门只验 group 格式，错误 vault 仍可假绿

`test_neo4j_replay_wire_t6b.py:429`（关联 `:430-435 / :325-345`）

**对照输入**：Concept 与 LEARNED 都落入错误的非默认组 `vault__other__wrong`，评分、时间戳、节点数全部正确 ⇒ **当前所有归属断言仍通过**。
Codex 的提醒很到位：「直接复用被测 `_build_group_id_from_canvas()` 计算期望值，**仍可能同错同绿**」—— 这正是本卡一直在避免的循环论证。最小改法是明确测试 vault 并用**独立**预期值核验。
Codex 同时声明：「这证明门存在缺口，**不代表已证实生产跨 vault 写错**。」

### round-5 关闭的项（Codex 独立确认）

- **⓪(a) 分行长度判据可靠**：`read_text()` 统一 CR、随后 `strip()` 去尾，此后 `splitlines()` 只能增加 LF 之外的切点。Codex **纯内存枚举 4,714 组等长输入，切片不同为零**；r4 的 U+2028 负控回退 0、普通对照保留 50。
- **⓪(b) 无新增同事件循环竞态**：loader 用同一不可变 `raw`，初读到加载 checkpoint 之间无 `await`。（不扩大为跨线程/跨进程保证。）
- **① 异常覆盖与顺序无新增回归**：新 `try` 覆盖 import、工厂调用、回灌与统计。
- **② run ID 整改有效**：未发现清理或计数遗漏旧固定身份；独立进程／xdist worker 各自生成 ID；同进程重复执行有逐用例清理 + 独立 seed UUID。**r4 的两条 LOW（标签绑定、读取失败 warning）已关闭**。

### 车道的自我评价（如实）

五轮里有**两条 HIGH 是我自审多遍没看见的**（字符串假防线、checkpoint 口径回归），**一条 MEDIUM 是我把修法做成了假修复**（结构变了行为没变，因为那条路径无测试覆盖），**一条地盘违规是我修 Codex 意见时引入的**。这些都已逐条写进本单，不做淡化。

---

### round-6 — 绑 `962d86c6`（⚠️ 已对最终 HEAD 失绑，参考用）

**BLOCKER 0 / HIGH 3 / MEDIUM 1 / LOW 0** —— 三条**数据丢失路径**，Codex 均定性为「本卡生产接线暴露的既有缺陷」。

⚠️ **失绑原因（车道之过）**：我在它审 `962d86c6` 期间提交了 `c667b1eb`（自查发现 `canvas_events` 同型缺陷后直接动手）。**本卡第三次**踩「审查对象须冻结」，代价是这一轮对最终 HEAD 失绑。

| Codex | 问题 | 暴露源 | 处置 |
|---|---|---|---|
| HIGH-2 | **并发回灌用旧快照覆盖新追加**：A/B 都初读 `[x,y]`，A 写回 `[y]`，期间追加 z 成 `[y,z]`，B 仍用旧快照、两边长度同为 2 ⇒ 判「无新追加」写回 `[y]`，**z 从未重放却被删** | ✅ **本卡造成** —— 接线前零调用方、不存在并发 | 改码：模块级 `asyncio.Lock` 串行化整次回灌 |
| HIGH-3 | **finalize 重读失败仍继续覆盖**：`except OSError: current_lines = []` 吞掉异常照常写回 | 既有 | 改码：记 error 并**直接返回**，保留原文件 + 保留 checkpoint |
| HIGH-1 | **文件代际错配**：`_clear_checkpoint` 在改写**之后**，中间崩一次就留下指向上一代文件的游标 | 既有 | 改码：先清游标再改写；`_clear_checkpoint` 不再吞 `OSError`；清不掉则放弃改写 |

三条各有行为级实测（`fix-r6-three-highs-*.txt`）：并发序列 `['enter','exit']` 未交叠 / 注入 `OSError` 后文件逐字节原封不动 / 清游标早于改写且清不掉就不动文件。

**另一条自查修复**（`c667b1eb`，非 Codex 提出）：r5 的「连续成功前缀」只施加在 `failed_writes`，而 `canvas_events` **逐字同构、同样会丢**（它的 `still_pending` 也写回文件），一并改；`learning_memories` 后果不同（不写回不轮转、跳过不会丢）但口径统一。
> 这条呼应一个通则：**修完一处要立刻扫同型第二处** —— 审查意见只指出它踩到的那一处。

### round-7 — 绑 `1028bea7`（最终 HEAD，审查始末 HEAD 未变）

**BLOCKER 0 / HIGH 5（含既知 G2-2 移交项 1）/ MEDIUM 3 / LOW 0**

#### r7 对 r6 三条修复的独立核验 —— 全部确认关闭

| r6 修复 | r7 原话 |
|---|---|
| 整次回灌互斥 | 「**同一事件循环内原路径关闭。** 多循环见第 6 项，跨进程仍未覆盖。」 |
| 重读失败提前返回 | 「**原 `failed_writes` 数据删除路径关闭。** 保留 checkpoint 合理；跳过旧归档 cleanup 只延后清理。」 |
| 先清游标再改写 | 「**原 `failed_writes` 换代窗口关闭。** 清成功、替换失败时，实测原文件保留且游标已清，下轮从零重放；代价是可能重复 Episode，**数据保留方向比原先更安全**。」 |

#### r7 新报的 5 HIGH —— 全部落在既有算法上

1. **`canvas_events` 位置游标未绑快照**（`:416`）。两条负控：① 压缩后旧 `index=50` 仍被接受，实测不尝试任何记录直接轮转唯一失败条目；② 保存前缀 50 后中断、追加**时间戳更早**的 z，重启先排序 ⇒ z 被移到游标之前，未重放却随 finalize 出队。**第二条不需要旧版本也不需要压缩**。Codex：「仅前移 `_clear_checkpoint` 或检查下标范围不够。」
2. **canvas 旧「已尝试」游标带当前版本标记被接受**（`:57`）。`962d86c6` 时 canvas 仍按 `i+1` 保存，却共用了已更新的 `_PROGRESS_VERSION` 标记 ⇒ 升级后被当成可信游标。与第 1 项分属**历史语义迁移**与**当前快照身份**两个面。
3. **canvas finalize 完全不重读**（`:449`）。初读 `[x,y]`，期间追加 z，x 成功 y 失败 ⇒ 实测只写回 `[y]`，**z 被删**。「甚至无需注入读取异常」。且**不能照搬** failed_writes 的按长度截取追加后缀 —— 该链会排序。
4. **`record_score_history` 失败仍返回 `True`**（`:604`）。LEARNED 写入成功、`record_score_history()` 抛 `ConnectionError`，控制流仍返回 `True` ⇒ 调用方据此移除/轮转记录，**缺失的评分历史不再自动重试**。
5. **〔既知 G2-2 移交项〕重放用当前 vault**（`:907`）。vault A 留下条目、切到 B 后触发回灌 ⇒ 写进 B。源码已明确承认并移交。Codex 声明：「登记的是源码路径，**未声称观察到实际数据库污染**。」

#### r7 的 3 MEDIUM

- **模块级 `asyncio.Lock` 跨事件循环**（`:74`）：同进程先在 loop A 竞争、再在 loop B 竞争，纯内存实测抛 `bound to a different event loop`。Codex 明确「**不能据此宣称通常单 ASGI worker 会死锁**」，也警告「不能每个循环各建一把锁，否则恢复原来的并发覆盖路径」。
- **finalize 提前返回缺少错误状态**（`:360`）：51 条全成功、期间追加第 52 条、finalize 重读抛 `OSError` ⇒ 实测返回 `{"recovered":51,"pending":0}`，**没有 `error` 键**，于是 `main.py` 的启动汇总进入「正常完成」分支。⚠️ 这正是本卡 r1 整改②要消灭的那类伪装，在新的提前返回路径上**重新出现**了。
- **错误 vault 归属门仍可假绿**（测试 `:429`）：r5/r6/r7 连续三轮指出，本卡始终未改，作为开放项移交。

#### Codex 的结论性建议（本卡采纳为停车依据）

> **建议独立排 Story 38.8 回灌算法重写卡。** ……独立卡应明确**稳定记录身份、来源 vault、成功确认条件和崩溃恢复协议**；本接线卡由主 session 裁定止血范围与停车版本。现有门不运行 lifespan，也未覆盖上述故障路径，**不能据正常输入通过推定整体安全**。

另附 r7 的两条澄清（对后续卡有用）：`_clear_checkpoint` 读取失败时会尝试删除**整份** checkpoint，删除成功可能让其他链也重新重放；`learning_memories` 不写回、不轮转，**没有 canvas 的同型 finalize 删除路径**，旧游标/排序可能导致某轮漏重放，但文件仍保留。

## 四 DoD-3 双段

### 4-A Claude 已代验（技术侧）

| 承诺 | 兑现证据 |
|---|---|
| 孤儿重放器接进真实路径 | 孤儿门 **0 → 2**（`main.py` 回填门在线分支的启动恢复 + `traces.py::replay_fallbacks` 管理端点），验伪锚 +1 |
| 回灌真的把数据写回图 | 7692 端到端门 6 passed，按 `Concept.name` 点查后逐字段断言 `score` / `timestamp` / `group_id`（非空、`vault__*` 物理格式、≠ DEFAULT 桶、边与点同组） |
| 门不是假绿 | 负控② 摘掉调用后端点仍 200、stats 仍正常，但图查询断言红 ⇒ 门绑在图内容而非 stats 自述；负控① 拆鉴权后三条鉴权用例红在指定状态码断言 |
| 重复回灌不产生重复数据 | 第二次 `recovered == 0` 且门前缀节点数逐标签相同；已声明真实防线是 `_rotate_file` 而非 MERGE |
| 鉴权与 `/system/*` 同口径 | 403（缺 header / key 不匹配）、503（生产态未配置）三条用例绿；`security.py` 一字未改 |
| 离线不再静默丢弃 | 离线分支新增只读积压登记，`pending_total` 口径已按「是否会被轮转」如实收窄 |
| 类型/风格不回退 | pyright `0 errors, 81 warnings`（同基线）；ruff 四文件全过 + 验伪锚 `rc=1` |
| 没碰不该碰的 | 地盘门 ⊆ 白名单；`security.py`/`system.py`/`openapi.json`/`conftest` 全空；`main.py` 两 hunk 均 `-N,0` 纯插入；`fsrs_bridge`/`decay_beta` 0 命中；全程 W4 哨兵 0 |
| 既有套件不回退 | 名单套件本卡引入红 0；`tests/unit` 目录级 `base=64 → close=62`，diff **只有 `<`、零 `>`** |
| **仓里早就写着的 P0 契约被兑现** | `TestStartupIntegration::test_main_imports_fallback_sync` 与 `::test_fallback_sync_called_in_lifespan` 两条**既有**常红测试转绿 —— 「启动 lifespan 应当调用回灌」这条契约此前一直未兑现。该证据由本卡之外的人预先写下 |

### 4-B 用户视角（零技术词）

> 后端连不上知识库的时候，攒下的学习记录不再永远躺在文件里没人管——等它恢复了会自动补回去，我也能手动点一下让它立刻补回。而且就算它一直连不上，系统现在也会明明白白告诉我「有多少条在排队等着补」，而不是一声不吭地跳过去。我感觉数据终于不会悄悄丢了。

**felt-sense**：以前那种「它是不是在后台偷偷弄丢我的东西」的隐隐不安，变成了「就算出问题，我也看得见它欠我多少、什么时候还」。

#### DoD-3 双段自检（`dod3-selfcheck-*.txt`）

```
[D3-A] 段 4-B 禁词命中        = 0
[D3-A 强验伪锚] 同正则对全文  = 50   ⇒ 正则确实能命中这些词, 段 4-B 的 0 是真 0
[D3-E] 段 4-B felt-sense 命中 = 2（「感觉」「不安」）
[D3-C] 段 4-A 让用户自己跑    = 0（全部 Claude 自跑并贴证据）
```

禁词集：`curl|docker|HTTP|JSON|.env|endpoint|pytest|schema|容器|daemon|requestUrl|vault.create|obsidiantools|DevTools|终端|命令行`

---

## 五 本卡未证明什么（≥4）

1. **未证明现网已积压的暂存文件回灌后无冲突** —— 全部验证只在 7692 测试容器 + `tmp_path` 上做，现网 7691 与其 `backend/data/` 下的真实暂存文件全程只读未碰。现网条目的 `canvas_name` 分布、group 解析结果、与图中既有数据的时间戳冲突（last-write-wins 分支）都未实测。
2b. **未证明 `failed_writes.jsonl` 里的 `knowledge_entity` 条目能被回灌** —— 实证结论相反：它们**不能**（见 §一(g) 的覆盖缺口一节）。本卡只接通了同一文件里的评分类条目。数据不丢（写回文件）但持续积压。

2. **`failed_edge_syncs.jsonl` 与 `dead_letter_episodes.jsonl` 两条链本卡未接通** —— `sync_all_fallbacks` 只覆盖 `failed_writes` / `canvas_events` / `learning_memories` 三个文件。前者仍只有写侧计数器 + 只读 UI，后者 `DeadLetterStore` 默认只存 `episode_body[:200]` 残片（本身就不足以完整重放）。两条链的接通/退役归 T6-C 或后续卡。
2d. **幂等断言的「节点数相同」只在一个受限查询范围内成立（Codex round-2 指出，本卡未改码）** —— `_gate_node_count` 只数「`name`/`id`/`path` 以门前缀开头的节点」+「经 `SCORED` 连到门前缀 `Node` 的 Episode」。**门未覆盖的路径**：游离 Episode（没连上任何 Node 的）、连错 Node 的 Episode、不带门前缀的节点、以及重复的**关系**（只数节点不数边）。此外 `labels(n)[0]` 只取第一个标签，`count(e)` 没有去重。
    ⇒ 「两次计数相同」只能证明**这个查询范围内**没有新增，不能证明全图没有重复。
    未改码的理由：该查询已挡住 round-2 点名的那个负控输入（首轮 `Episode=2` / 第二轮仍 2），且 round-1 整改后首轮已钉成绝对值 `{Concept:1,Node:1,Canvas:1,Episode:1}`；把计数面扩到全图需要另一套身份锚（7692 是共享容器，全图计数会被别的门污染）。已在 round-3 prompt 问题⑤ 请 Codex 判定这个不改的决定是否可接受。

2c. **未证明「7692 容器真的停掉时整文件 skip」的端到端表现** —— 只验到 `skipif` 的判据函数对三类失败输入返回 `False`（见 §一(m)）。真停容器会影响同机其它在跑车道，故未做；且改 `NEO4J_TEST_URI` 的替代方法被 W4 哨兵在 `pytest_configure` 阶段拦死（端口白名单只有 `[7692]`）。

3. **未证明「Neo4j 启动时在线、运行中掉线再恢复」的中途恢复场景会自动回灌** —— (c) 的触发点在启动 lifespan 内，只覆盖「启动时即已恢复」。mid-run 恢复目前只能靠 (d) 的管理端点手动补；自动探测触发未实现，已移交。
4. **未证明 `recover_failed_writes`（`memory_service.py:2687`，孤儿②）应退役还是保留** —— 本卡只接了 `sync_all_fallbacks`。该方法仍是零非测试调用方，其 docstring 自述已被 `sync_all_fallbacks` 取代，但本卡未删除、未验证删除是否安全。
5. **未证明积压登记的只读计数在超大文件下的性能** —— `_count_jsonl_lines` 用 `read_text()` 整体读入后 `splitlines()`。暂存文件在长期离线下可无界增长（写侧有界是 T6-C 的面），本卡未测百 MB 级文件下的启动耗时与内存。
5b. **`checkpoint_idx` 的下标口径在本卡换切法后存在跨版本错位的窄边界（自查 + round-4 预答，未修）** —— `_sync_failed_writes` 的 `checkpoint_idx` 是按该函数的切法存的下标。本卡把 `splitlines()` 换成 `split("\n")` 后，若**上一轮中途崩溃**留下了用旧口径写的 checkpoint、且文件恰好含 U+2028，下标含义会错位；被跳过的条目不进 `still_pending`，会随 `_rotate_file` 一起搬走（即真的丢）。三件事须同时成立，且成功路径结尾总会 `_clear_checkpoint`。根治要给 checkpoint 带口径版本号，超出本卡地盘。

6. **未证明启动恢复触发在真实 lifespan 中「跑起来是对的」**，且 **Codex round-3 补了一条我没写全的路径**：`backfill_vault()`（`main.py:392`）抛异常时控制流**直接进外层 except**，(c) 的回灌根本不执行 —— 即「回填失败」会连带吃掉「回灌」，而现门检不出。
    —— 端到端门走 `ASGITransport`（刻意不跑 lifespan，否则会连现网并读 live vault）。(c) 那条路径现有三层证据，但**都不是行为测试**：① 既有 `TestStartupIntegration` 两条 —— 只做**源码字符串包含**断言（`"sync_all_fallbacks" in source`），不执行 lifespan；② 本卡的 AST 结构核 —— 证明语法归属与调用顺序，同样不执行；③ 端到端门验的是**同一个** `sync_all_fallbacks` 经管理端点这条路径。**没有任何测试真正启动过 lifespan 并观察回灌发生**。具体未覆盖的：`_worker_graphiti` 为真但 Neo4j 随后不可用时的分支、内层 `except` 的实际触发、以及启动期回灌与首批请求的并发。
7. **`count_fallback_backlog` 的「坏文件计 0」有一个角落连 warning 都不会留（自审发现，本卡未改码）** —— docstring 承诺「读文件失败（不存在 / 权限 / 非 UTF-8 / JSON 坏）按 0 计**并记一条 warning**」，但两个 helper 的第一步是 `if not path.exists(): return 0`，而 `pathlib.Path.exists()` 对权限类 `OSError` 是**返回 False 而不是抛出** —— 即「问不出来」被压成「不存在」，直接 `return 0`，**没有 warning**。于是「目录不可读」与「真的没有积压」在日志里也不可分（这正是工程坑索引里 `pathlib 谓词把「问不出来」压成「不存在」` 那条）。
    **已实证，带对照组**（`pathlib-exists-swallow-20260914T225326.txt`）：

    ```
    对照: 权限正常时 _count_jsonl_lines = 2  (文件真有 2 行)
    父目录 chmod 000 后 exists() = False   ← 没抛异常, 直接报 False
    --- 此处若有 [T6-B backlog] warning 则说明走到了 except ---
    --- (以上无 warning 行) ---
    _count_jsonl_lines = 0   ← 静默 0, 与「真的没有积压」逐字相同
    [还原] 权限恢复后 _count_jsonl_lines = 2
    ```

    未改码的原因：代码已 commit 且 Codex round-2 正在审该 SHA，此时改码会让审查对象在审查期间变动；且该分支只影响日志可观测性，不影响数据安全（离线登记本就只是一条日志）。建议 T6-C 顺手改成 `try: ... except OSError` 包住整段，或显式 `os.stat` 区分三态。
    另：坏文件与真空在**返回值**上不可区分是刻意取舍（见 `_count_json_list` docstring）；那条 warning 是否会被生产日志级别过滤掉，未验。
8. **未证明并发安全** —— 启动回灌与管理端点可能同时触发（启动窗口内收到 POST）。`_sync_failed_writes` 有 `failed_writes_lock`，但 `_sync_canvas_events` / `_sync_learning_memories` 没有对应文件锁；本卡未做并发触发测试。

---

## 六 台账待登记条目（≥4）

0a. **⛔⛔ 建议独立排「Story 38.8 回灌算法重写卡」（Codex round-7 结论性建议，本卡采纳为停车依据）** —— 该文件的问题已涉及**可变快照 / 位置游标 / 排序 / 并发追加 / 数据库部分成功 / 确认删除**六个交织面，继续逐处补丁**难以建立统一的数据保留保证**。独立卡须明确四件事：**稳定记录身份**（不再用位置游标）、**来源 vault**（条目落盘时持久化，不靠重放时的 active vault）、**成功确认条件**（含 `record_score_history` 这类二次写入）、**崩溃恢复协议**（游标与文件代际同生共死）。
    本卡七轮暴露的 HIGH 清单可直接作为该卡的验收负控集：r5 游标语义 / r6 并发覆盖·finalize 覆盖·文件代际 / r7 canvas 三条 + `record_score_history` 返 True + G2-2 跨 vault。

0b. **⚠️ r7 遗留 5 HIGH + 3 MEDIUM 全部未修，逐条见 §三 round-7 段** —— 其中「finalize 提前返回缺少错误状态」值得单独提醒：本卡 r1 整改②好不容易消灭的那类伪装（「三条链全炸也打成回灌 0 条」），在 r6 新增的提前返回路径上**重新出现**了。这正说明为什么该独立排卡：每加一条返回路径就要重新审一遍所有汇总口径。

0. **🛑 本卡停车，四项待裁** — 见 §三 round-5 段与文首横幅。主 session 接手时**第一步**应先裁这四项（尤其 ① 的迁移取舍：回退旧游标会重复评分 Episode），再决定本卡是否入合并队列。车道最终 HEAD `ccb1d101`，5 个 commit，squash 顺序见 §七。

1. **`sync_all_fallbacks` 接通** — 修复 commit `cd1b5ae9`；孤儿门证据 `orphan-gate-{before,after}-*.txt`（0 → 2，验伪锚 +1）；端到端门 nodeid `tests/integration/test_neo4j_replay_wire_t6b.py::test_offline_entry_replays_into_graph_via_admin_endpoint`（及同文件另 5 条）。
2. **openapi 待主 session 集成期再生** — 新增 `POST /api/v1/traces/replay-fallbacks`，本卡 commit 不含 `backend/openapi.json`，`tests/contract/test_openapi_snapshot_drift.py::test_committed_snapshot_has_no_drift` 漂红为预期。commit 时用了 `LEFTHOOK_EXCLUDE=spec-sync-flat,spec-sync-root`（理由与 hook 本体输出已落档；被跳过的不是 `python-typecheck`）。
3. **⚠️ `recover_failed_writes`（`memory_service.py:2687`）仍为孤儿，且它是 `knowledge_entity` 条目的唯一消费者** — 本卡实证（`schema-gap-knowledge-entity-20260914T224351.txt`）：`failed_writes.jsonl` 里由 `memory_service._record_structured_outbox:502` 落盘的 `{"kind":"knowledge_entity", …}` 条目**没有 `concept`/`concept_id` 字段**，被本卡接通的 `_replay_scoring_entry_to_neo4j` 判「no concept」→ 计 pending 写回文件、永不回灌。能按 `kind` 分流处理它的只有 `recover_failed_writes`，而那个方法零非测试调用方。⇒ 其处置**不是**「删不删死代码」的问题，而是「这一类条目要不要回灌」的问题，需与「两个重放器的职责边界」一并裁定。建议排进 T6-C 或紧邻的后续卡。
4. **`failed_edge_syncs.jsonl` / `dead_letter_episodes.jsonl` 两链未接通** — 接通/退役 + 写侧有界归 T6-C。
5. **中途（mid-run）Neo4j 恢复的自动探测触发未实现** — 目前只有启动触发 + 手动端点，移交。
6. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数** — 见 §三「Codex 轮次汇总」表。四轮存档 `codex-review-CARD-NEO4J-REPLAY-WIRE{,-r2,-r3,-r4}.md`，绑定依次 `cd1b5ae9` / `d9fa0774` / `d90f5a67` / `7bcbfc1a`。

6b. **⚠️ `_sync_failed_writes` 的 U+2028 修复改了既有代码（非本卡新增面），请主 session 知悉** — 本卡地盘含 `fallback_sync_service.py`，但 `:227` / `:266` 两处 `splitlines()` → `split("\n")` 改的是**既有** `_sync_failed_writes` 的行为（不是本卡新增的 `count_fallback_backlog`）。理由：该缺陷正落在本卡接通的回灌链上（含 U+2028 的条目永远回灌不掉），不修则「接通了回灌」这个主张对该类条目不成立。既有套件 `test_story_38_8_fallback_sync.py` 全绿未回归。若主 session 认为应拆成独立卡，本条可 revert（两行 + 注释）。

6c. **`checkpoint_idx` 的跨版本口径错位（本卡引入的窄边界）** — 见 §五 5b。根治要给 checkpoint 带口径版本号，建议随 T6-C 的写侧有界一并处理（那时本来就要动这个文件）。
7. **`tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422` 是不稳定测试** — 本卡三次观测：开工目录级跑**红**、开工孤立跑**红**、收工目录级跑**绿**（代码树在这三次之间对该文件无任何改动）。它不在 `evidence-b14/unit-red-baseline-08100483.txt` 里，`$BASE` 与本机开工基线因此差 1 条。⇒ 不是「基线漏了一条稳定红」，而是「这条本身时红时绿」，两边采样撞上了不同的那一面。建议主 session 把它登进不稳定测试清单（而非红基线），否则每批都会有人花时间重新判一次它是不是本卡引入。
8. **⚠️ 批级环境变更需主 session 补手册 §零** — 2026-09-14 22:26 启动 Docker Desktop（用户授权），`restart: unless-stopped` 连带恢复了现网 neo4j(7691)、neo4j-test(7692)、backend(8011) 三个容器。按本卡硬边界我未改手册，需主 session 代为通告其余在跑车道。
9. **`record_score_history` 的 Episode 非幂等** — `CREATE (e:Episode {id: randomUUID()})`（`neo4j_client.py`，`record_score_history` Cypher 段）。任何未来让同一暂存条目被重放两次的改动（例如给 `_sync_failed_writes` 加重试而不轮转）都会产生重复 Episode。卡文「幂等靠 MERGE」的表述对 Concept/LEARNED 成立、对 score-history Episode 不成立，建议在 T6-C 或写契约文档中更正。
10b. **⚠️ 离线登记日志的措辞对一部分条目名实不符（DD-13 边界，本卡未改码）** — (e) 的日志按卡文指定措辞写「Neo4j 离线, N 条待回灌, 恢复后回灌」，而 `count_fallback_backlog` 的 `failed_writes` 计数是**整文件非空行数**，其中的 `knowledge_entity` 条目恢复后**不会**被回灌（见条目 ③）。即该句对主写侧的评分类条目准确、对这一类不准确。
    **为何本卡不改**：① 卡文明确指定了这句措辞；② 要让计数区分「可回灌/不可回灌」就得逐行解析 JSON 并按 `kind` 分流，超出卡文给 (e) 划的「一条日志 + 一个只读计数」边界，且给启动路径增加与文件大小成正比的解析开销（写侧无界 ⇒ T6-C）；③ 代码已 commit 且 Codex 正在审该 SHA，此时改码会让审查对象在审查期间变动。建议 T6-C 连同写侧有界一并处理（那时本来就要逐行处理该文件）。
11. **(c) 每次启动会全量重放 `learning_memories`（已知代价，非缺陷）** — 该文件从不轮转（`_sync_learning_memories` 结尾 NOTE），实测第二次 `recovered` 仍 = 1。图上幂等（纯 MERGE + SET，零 CREATE，不调 `record_score_history`），但每次启动的 MERGE 条数 = 该文件条目数，而该数随时间单调增长（写侧无界 ⇒ T6-C）。若 T6-C 给它加上限/轮转，需同时考虑「轮转后运行时 `LearningMemoryClient` 还要不要查得到」这个约束。
10c. **`canvas_events_fallback.json` 的写侧**已经**有界（供 T6-C，避免重做）** — `canvas_service.py:97` `_max_fallback_events = 10000`，`:165-166` 超限即 `events = events[-max:]` 截最新。该链另有两点实测：写侧 `:169` 有 `mkdir(parents=True, exist_ok=True)`（故 `backend/app/data` 目录当前不存在只表示「还没发生过降级写入」，不是断链）；写侧**始终写 list**（`json.dumps(events)`），与 `_sync_canvas_events` 和本卡计数方法的 shape 口径一致。
    ⚠️ **其余三条链本卡未下结论**：对 `agent_service` / `failure_counters` / `neo4j_edge_client` 我只跑了 `grep -cE 'max|truncat|\[-[0-9]|rotate'` 这类**启发式**判据（命中 5 / 0 / 1），它既会误匹配也会漏，**不足以断言「有界/无界」**。唯一可直接读出的是 `memory_service._record_structured_outbox`：纯 `open(..., "a")` 追加，未见任何上限逻辑。T6-C 请自行逐条核，勿引用本条的 grep 计数当结论。

11a. **⚠️ 本门末条清理查询的范围比 `test_cypher_contract_gate.py` 的同类清理更宽（自审，未改码）** — 本门 `_CLEANUP_QUERIES` 末条（round-2 时 :112） 是 `MATCH (e:Episode) WHERE e.type = 'scoring' AND NOT (e)--() DETACH DELETE e`，而 `test_cypher_contract_gate.py:109` 的同类清理多一个 `e.group_id IS NULL` 限定。⇒ 本门会**多删**「有 group_id 的孤儿 scoring Episode」，那可能是别的门播种的数据。
    **实测差集 = 0**（当前 7692 容器里两种口径各 0 个），但那是**一次快照、不是不变量** —— 只要将来某个门播种一个带 group_id 的孤立 scoring Episode 并断言它存在，本门的清理就会破坏它（表现为那个门随执行顺序时红时绿）。
    未改码原因同上（Codex round-2 正在审该 SHA）。建议收窄到与 cypher gate 同口径，或直接加门前缀限定。
11c. **⚠️⚠️ 给 T6-C 的路由顺序陷阱（本卡实证，不修但必须传达）** — T6-C 计划新增 **GET** `/traces/dead-letter-backlog`。既有 `GET /traces/{request_id}` 是一个吃掉任意单段的路径参数路由且注册在前，Starlette 按注册顺序匹配 ⇒ **若把新 GET 注册在它之后，请求会先命中 `{request_id}` 那条**。
    **实证**（`t6c-route-order-warning-*.txt`，当前 HEAD 实跑）：

    ```
    当前 /traces 路由表: ['GET'] /api/v1/traces/{request_id} ; ['POST'] /api/v1/traces/replay-fallbacks
    实证: GET /api/v1/traces/dead-letter-backlog → 200
          响应: {"request_id":"dead-letter-backlog","total_events":0,"timeline":[]}
    ```

    ⇒ **不是 404，而是 200 + 空 timeline** —— 路由被吃掉了却看起来像「查到了但没数据」，没有人会发现。
    处置：把新的 GET 静态路径的 `@router.get` 写在 `get_trace` **上方**。
    本卡新增的是 **POST**，方法不同故无此问题（已实证，见上表）。

11d. **「用字符串判断一个会被别的解析器消费的值」是本卡最贵的一课（跨卡）** — Codex round-2 HIGH-1：`":7691" in uri` 放行了 `bolt://127.0.0.1:07691`，而驱动解析后连的就是现网。同类问题在本卡另有两处同源：`skipif` 探针与可执行契约断言各一处。**通用处置**：凡「判断某个值安不安全」，判据必须作用在**消费它的那一层**解析出的结果上，而不是它的文本形态；且判据用**正向白名单**而非反向黑名单（黑名单漏一个就放行，白名单漏一个只会多拒一次）。仓里已有现成的驱动口径解析器 `tests/support/live_port_guard.py::canonical_target_ports`，后续任何卡要判 Neo4j URI 安全性都应直接复用它，不要自己写第二个解析器。

11b. **W4 哨兵的测试端口白名单只有 `[7692]`（跨卡可复用的实测事实）** — `backend/tests/conftest.py:100` 在 `pytest_configure` 阶段调 `tests/support/live_port_guard.py:1265` 的 `assert_test_uri_not_blocked()`，把 `NEO4J_TEST_URI` 指向白名单外任何端口（实测 7999 / 7691）都会让**整个 pytest 会话 `INTERNALERROR`**，而不是跳过或报错某个文件。后续卡若想用「改 `NEO4J_TEST_URI`」做对照实验，会撞上这条；它同时也意味着「把测试指向现网」在 pytest 启动阶段就被拦死，比任何文件级探针都早。
12. **`traces.py` 的 `DATA_DIR` 指错目录 —— 本卡实证确认（不是转述 T6-C 卡文）** — 实测解析结果：

    ```
    traces.py DATA_DIR → backend/app/data      存在: False   ← 该目录根本不存在
    死信实际写入        → backend/data/failed_edge_syncs.jsonl   文件存在: True
    相同: False
    ```

    ⇒ `GET /traces/{request_id}` 对 `failed_edge_syncs` 与 `dead_letter_episodes` 两个来源**恒查不到**（`_search_jsonl` 的 `if not file_path.exists(): return results` 直接返回空），这是 DD-13 名实不符的活样本。
    本卡只**新增** POST 端点、未动既有 GET 端点与 `DATA_DIR`，故未触及；T6-C 卡文已把它列入修复面。此处记实证是为了让 T6-C 不必再验一遍，也避免这条以「转述」形态在台账里流转。

---

## 七 提交

- 代码 commit ①：`cd1b5ae9` — `feat(t6-b): 孤儿重放器接进真实路径 [BATCH-2026-09-11-第十四批 / CARD-NEO4J-REPLAY-WIRE]`
  - header `wc -m` = **73**（≤100）✅；body 全部行 ≤100 ✅；文件面 4 个，不含 `openapi.json` ✅
- 代码 commit ②：`d9fa0774` — `fix(t6-b): 按 Codex round-1 整改四处 […]`
  - header `wc -m` = **81** ✅；body 全部行 ≤100 ✅；`4 files changed, 43 insertions(+), 8 deletions(-)`
- 代码 commit ③：`d90f5a67` — `fix(t6-b): 按 Codex round-2 整改 HIGH-1 等五处 […]`
  - header `wc -m` = **90** ✅；body 全部行 ≤100 ✅；`4 files changed, 79 insertions(+), 12 deletions(-)`
- 代码 commit ④：`7bcbfc1a` — `fix(t6-b): 按 Codex round-3 整改清理身份与 U+2028 […]`
  - header `wc -m` = **91** ✅；body 全部行 ≤100 ✅；`2 files changed, 98 insertions(+), 33 deletions(-)`
- 代码 commit ⑤：`ccb1d101` — `fix(t6-b): 按 Codex round-4 整改 checkpoint 口径等五处 […]`
  - header `wc -m` = **96** ✅；body 全部行 ≤100 ✅；`3 files changed, 180 insertions(+), 80 deletions(-)`
  - **为何五个 commit 而非 amend**：amend 会让各轮的绑定 SHA 变成悬空对象、「那一轮审的到底是什么」不可复查 —— 这在本卡尤其要紧，因为 **r3 的整改在 r4 被查出引入回归**，没有独立 commit 就无法定位是哪一次改动带进来的。协议允许单卡多 commit（主 session 用 `cherry-pick --no-commit <range>` squash）。
  - **squash 顺序 = `cd1b5ae9` → `d9fa0774` → `d90f5a67` → `7bcbfc1a` → `ccb1d101`**

### Codex 轮次汇总

| 轮 | 绑定 SHA | B/H/M/L | 改码 | 登记 | 本轮要害 |
|---|---|---|---|---|---|
| r1 | `cd1b5ae9` | 0/0/4/1 | 4 | 0 | 三条是自身注释做了承诺而代码没兑现 |
| r2 | `d9fa0774` | 0/**1**/3/2 | 5 | 1 | **HIGH**：`":7691" in uri` 字符串假防线，`:07691` 绕过 |
| r3 | `d90f5a67` | 0/0/2/2 | 2 | 2 | U+2028 让条目永远回灌不掉（LOW 但是真行为缺陷） |
| r4 | `7bcbfc1a` | 0/**1**/2/2 | 5 | 0 | **HIGH**：r3 的 U+2028 修复引入 checkpoint 口径回归，会丢记录 |
| r5 | `ccb1d101` | 0/**1**/2/0 | 0 | 4 待裁 | **HIGH**：checkpoint 把「已尝试」当「已成功」，中断重启永久跳过失败条目 |

⇒ 五轮共 **23 条意见，改码 16 条**。

**D-15 的 B/H=0 在 r3 曾满足，但 r3 的整改本身在 r4 被查出引入回归；r4 的整改又在 r5 被查出是假修复** —— 这正是「审后改代码必再送一轮」这条规则要防的事，它连续两轮都抓到了。

## 🛑 配额 5/5 用满且末轮仍有 HIGH ⇒ 按 D-15 **停车，交主 session 人审**

Codex round-5 首句即为此结论。车道不再自行整改，四项待裁见 §三 round-5 段。
- 文档 commit：只动 `_bmad-output/`（不破坏 Codex 终审绑定 —— 终审判据 `git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 排除该目录）
- `*.stderr*` 未入库（`.gitignore` 覆盖）✅ · **未 push** ✅ · 未改台账 ✅ · 批中未装/升任何包 ✅

---

## 附录 — evidence 清单（60 项，全部带 rc 末行，0 个 `.log`）

| 文件 | 末行 |
|---|---|
| `cleanup-anchor-verify-20260914T230459.txt` | `rc=0` |
| `codex-binding-20260914T224933.txt` | `rc=0` |
| `codex-binding-r3-20260914T230314.txt` | `rc=0` |
| `docker-neo4j-test-up-20260914T222629.txt` | `rc=0` |
| `dod3-selfcheck-20260914T225641.txt` | `rc=1` |
| `dod3-selfcheck-20260914T225654.txt` | `rc=0  # 全部判据为计数式, 无非零退出` |
| `final-state-snapshot-20260914T230435.txt` | `rc=0` |
| `fix-r2-verify-20260914T225901.txt` | `rc=0` |
| `fix-utf8-verify-20260914T224637.txt` | `rc=0` |
| `four-chains-bound-status-20260914T225543.txt` | `rc=0` |
| `learning-memories-not-rotated-20260914T224129.txt` | `rc=0` |
| `lefthook-precommit-20260914T223650.txt` | ` 4 files changed, 586 insertions(+), 1 d` |
| `lefthook-spec-sync-skipped-20260914T223317.txt` | `rc=0` |
| `mainpy-ast-structure-20260914T224223.txt` | `rc=0` |
| `mainpy-hunk-20260914T223824.txt` | `rc=0` |
| `negctl-1-auth-20260914T223516.txt` | `rc=0` |
| `negctl-1-auth-20260914T223707.txt` | `rc=0` |
| `negctl-2-replay-20260914T223739.txt` | `rc=0` |
| `neo4j-7692-probe-20260914T222636.txt` | `rc=0` |
| `no-mutant-residue-20260914T225351.txt` | `rc=0` |
| `no-residual-string-guard-20260914T230257.txt` | `rc=0` |
| `offline-branch-before-20260914T222906.txt` | `rc=0` |
| `openapi-drift-20260914T223237.txt` | `rc=1` |
| `orphan-gate-after-20260914T223040.txt` | `rc=0` |
| `orphan-gate-before-20260914T204349.txt` | `rc=0` |
| `orphan-gate-final-20260914T230400.txt` | `rc=0` |
| `pathlib-exists-swallow-20260914T225314.txt` | `rc=1` |
| `pathlib-exists-swallow-20260914T225326.txt` | `rc=0` |
| `port-guard-edge-cases-20260914T230537.txt` | `rc=0` |
| `pyright-close-20260914T223045.txt` | `rc=0` |
| `pyright-close-20260914T223914.txt` | `rc=0` |
| `pyright-r2fix-20260914T224659.txt` | `rc=0` |
| `pyright-r3fix-20260914T225918.txt` | `rc=0` |
| `replay-green-20260914T223015.txt` | `rc=0` |
| `replay-green-postformat-20260914T223402.txt` | `rc=0` |
| `replay-green-r2fix-20260914T224607.txt` | `rc=0` |
| `replay-green-r3fix-20260914T225838.txt` | `rc=0` |
| `replay-red-20260914T222821.txt` | `rc=1` |
| `replay-red-identity-20260914T222842.txt` | `rc=1` |
| `ruff-close-20260914T223914.txt` | `rc=0` |
| `ruff-final-20260914T225036.txt` | `rc=0` |
| `ruff-worktree-20260914T223106.txt` | `anchor_rc=0` |
| `ruff-worktree-20260914T223131.txt` | `anchor_rc=1` |
| `schema-gap-knowledge-entity-20260914T224351.txt` | `rc=0` |
| `secret-scan-20260914T224257.txt` | `rc=0` |
| `skip-behavior-20260914T225104.txt` | `rc=0` |
| `skip-behavior-20260914T225225.txt` | `rc=0` |
| `suite-close-20260914T223139.txt` | `rc=1` |
| `suite-r2fix-20260914T224659.txt` | `rc=1` |
| `suite-r3fix-20260914T225918.txt` | `rc=1` |
| `t6c-route-order-warning-20260914T225717.txt` | `rc=0` |
| `territory-20260914T223812.txt` | `rc=0` |
| `territory-final-20260914T224909.txt` | `rc=0` |
| `territory-final-r3-20260914T230129.txt` | `rc=0` |
| `traces-datadir-mismatch-20260914T225509.txt` | `rc=0` |
| `unit-close-20260914T223803.txt` | `rc=1` |
| `unit-close-final-20260914T230416.txt` | `..................................` |
| `unit-diff-20260914T224439.txt` | `diff_open_rc=1` |
| `unit-open-20260914T204341.txt` | `rc=1` |
| `unit-open-candidate-isolated-20260914T222544.txt` | `rc=1` |
