# P1 残项 CLOSED / STILL-OPEN 台账（CARD-DEBT-16）

> **卡**: CARD-DEBT-16 · **批次**: BATCH-2026-08-31-第七批 · **车道**: V7
> **裁定来源**: Codex 单轮终裁，原文逐字存档于 `codex-review-CARD-DEBT-16-P1残项单轮终裁.md`
> **裁定基线**: tracked HEAD `9cf0fb85ed839bb7035d023534fca222a24d6968`
> **输入**: `2026-08-20-P1-05d-五轮审查包-给Codex.md`（2026-08-20 备好、从未送审，本卡封存为输入）
>
> ## ⛔ 本台账的效力
>
> **此后任何对 P1-05 / P1-01 / P1-08 / B4 / TOCTOU / P1-03 / P1-04 的「CLOSED」宣称，
> 必须能指认到本台账的对应行。** 本台账未记 CLOSED 的项，任何文档、验收单、卡文里
> 出现的「已闭合 / 已解决 / 已收官」表述一律视为**未经复核的自宣**（计划书 L236 与
> G0 退出门 L241 的原义：收官状态由外部复核裁定，不由施工方自宣）。
>
> 升级路径：owner 卡过门后，由该卡的独立复核出具证据，回到本台账改行——**不允许**
> 在别处新起一份口径。

---

## 一、七项裁定表

| # | ID | 裁定 | owner（STILL-OPEN 项） | 一句话理由 |
|---|---|---|---|---|
| 1 | **P1-05** vault 文件准入边界 | 🔴 **STILL-OPEN**（部分闭合） | **DEBT-17**（需补卡） | 固定态越界读取已关，但 direct full-scan 对**历史已入库行**不收敛 |
| 2 | **P1-01** 快照 generation 不迁移 | 🟢 **CLOSED** | — | 跳写条件已与 generation 解耦，旧版/future/非法 schema 均强制重写自愈 |
| 3 | **P1-08** 锚点文档失实 | 🔴 **STILL-OPEN** | **DEBT-18**（需补卡） | C4 立的纪律没变成可执行门，后续批次已重新落盘通过数 |
| 4 | **B4** payload 准入与快照完整性 | 🔴 **STILL-OPEN** | **G4-8**（现成卡，裁定须拆 A/B） | 无 node_id 准入、无 provenance 持久化、无来源 digest |
| 5 | **TOCTOU** 判定与 open 非原子 | 🔴 **STILL-OPEN** | **INFRA-DEBT-01**（需补卡） | 窗口跨 5 个读取面，非任何 G4 卡范围 |
| 6 | **P1-03** 服务层四态贯穿 | 🔴 **STILL-OPEN**（部分闭合） | **G4-2**（重开 / G4-2R） | 统一四态已落地，但客户端内部吞异常 + 生产兼容入口剥状态 |
| 7 | **P1-04** API/trace/UI 面四态 | 🔴 **STILL-OPEN** | **G4-3**（现成卡，范围准确） | API schema 无 status 字段，前端 `retrieval_status` 零命中 |

**STILL-OPEN 项 owner 映射覆盖率：6/6 = 100%**（3 张现成卡 + 3 张显式登记的补卡需求）。

---

## 二、逐项台账

### 1. P1-05 — vault 文件准入边界 🔴 STILL-OPEN（部分闭合）

**已闭合的半边**（C1 `c154a7f2`，我方独立复核确认）：

- `backend/lib/agentic_rag/clients/lancedb_client.py:507` `_resolves_outside_vault` — realpath containment，`OSError` 分支 `return True` 即 fail-closed。
- `:1657` 全量索引**收集期**即拒（被拒文件不进 `md_files`，不会被 open/嵌入/落库）。
- `:1974` 单文件索引在 `open`（`:1980`）**之前**拒。
- `backend/app/services/vault_index_orchestrator.py:157,194-196` 走同一判定。
- 回归锁：`backend/tests/regression/test_real_entrypoint_admission.py`。

**仍缺的半边**（本轮新裁）：

`lancedb_client.py:1663-1666` 的 `if not md_files: return 0` **早于**指纹 diff（`:1680`）与删除清理循环（`:1697-1701`）。于是：一个文件先合法入库，随后变成越界 symlink（或被黑名单化），再跑一次默认 full scan——它被收集期拒掉，`md_files` 为空，函数在算 `deleted_files_rel` **之前**就返回 0，**旧 row 与旧 fingerprint 原样留在库里**。

- 复现（Codex 给出、我方复核代码路径成立）：临时库先索引合法 `节点/only.md` → 替换为指向 vault 外 `outside.md` 的 symlink → `index_vault_notes(force_rebuild=False)`。观测 `返回 0`，但 row 与 fingerprint 各仍为 1。
- **该 direct 入口在生产被使用**：`backend/app/api/v1/endpoints/metadata.py:590` 直接调 `lancedb_client.index_vault_notes(...)`，不走 orchestrator。经 orchestrator 的 reconcile 路径（`vault_index_orchestrator.py:483-530`）才会归零。
- 绿灯为何不冲突：`test_real_entrypoint_admission.py:72-85` 的 direct 用例**从空库开始**，只证明「被拒文件不新增」，从未覆盖历史行。

**归因（Codex 明确、我方认同）**：空集提前返回由更早提交 `0c4fe286` 引入，**早于** C1。这是 C1 的**不完整修复**，不是 C1 新造缺陷。

**owner → DEBT-17（补卡需求，登记如下）**

| 字段 | 内容 |
|---|---|
| id | `DEBT-17` |
| 标题 | direct full-scan 准入收敛 |
| what | 移除空准入集的 pre-diff `return`，让 fingerprint 删除与无 fingerprint orphan 清理照常执行；覆盖 `metadata.py` 的 direct endpoint |
| 完成判据方向 | 真 LanceDB 覆盖「合法入库 → 目录黑名单 / 文件黑名单 / 外部 symlink / 物理删除」四类；一次默认 full scan 后 rows + fingerprints **均为 0**；先红后绿 |
| 估时 / wave / deps | 3h / wave 1 / 无 |
| 附带 | reconcile 同一路径同时计 deleted+orphan 时报 `enqueued=2` 而实际 pending 唯一键只有 1（低严重度遥测计数错），并入本卡修正 |

### 2. P1-01 — 快照 generation 不迁移 🟢 CLOSED

**闭合证据**（C2 `1683328c`，我方独立复核确认）：

`backend/app/services/board_manifest_service.py:958-985` 的跳写条件已收紧为
`same_generation AND type(prev_version) is int AND prev_version == SNAPSHOT_SCHEMA_VERSION AND _snapshot_passes_v3_validation(prev)`——
四个条件同时成立才 `return False`；否则即便 generation 未变也走强制重写并落 `logger.info` 自愈日志。
`prev` 非 dict、`freshness` 非 dict 两条曾把 live 请求打成 500 / 让坏快照永不自愈的路径都已按「判 generation 不同 → 强制重写」处理。

严格加载在 `:1020-1072`。回归锁：`test_snapshot_schema_migration_contract.py:126-180`（同代 v1 / future version / 根与嵌套错型 / 带垃圾键的 v3）、`test_snapshot_v3_contract.py:262-340`。

**边界声明（不得用来重开本项）**：`mastery_a=mastery_b=1e308` 可让派生 `sigma`/`pick_score` 成 NaN——这个反例真实存在，但重写同一份当前 v3 修不掉它。五轮包 `:39` 已把「同 generation、schema 合法但内容真实性 / 数值语义不足」明确划归 B4。**它使 B4 保持开放，不重开 P1-01 的 generation/schema 迁移义务。**

**P1-01 无追加动作。**

### 3. P1-08 — 锚点文档失实 🔴 STILL-OPEN

**已闭合的半边**：C4 `1b7485b9` 立的三条纪律仍写在 `CURRENT_TASK.md:16`（①不记累计 commit 数 ②不落盘 CI run 号/通过数 ③收官状态由外部复核裁定不由施工方自宣）；CI 状态行 `:22` 本身合规——只记定性事实 + `gh run list --limit 3` 实查命令。

**仍缺的半边（纪律已回退，两条独立发现互相印证）**：

> 我方在送审的同时做了独立取证，与 Codex 的裁定**各自独立地**落到同一行——这条不是单方面转述。

- `CURRENT_TASK.md:7`（**恢复锚点前 15 行内**，由 `270c1716` 即第六批收官写入）：
  `②CI 接线（test.yml +10 行，517 passed）` —— 正是纪律②禁止落盘的通过数。
- `CURRENT_TASK.md:11`：`🔜 本合并（s6-recap…）+ t2-closeout 后…` —— 但 `270c1716`（s6-recap 合并）与 `9cf0fb85`（t2-closeout 合并）**都已在 HEAD**，把已完成的动作写成待办。
- 同型的通过数还散见于 `:55`(`393 passed`) `:70`(`425 passed`) `:78`(`381 passed`) `:126`(`252 passed`)。
- **不算违例的**：`_bmad-output/` 的 goal 总账仍用定性 CI 状态（总账 v2 `:1085`）；历史审查报告里的测试计数属**冻结证据**，不是状态锚点。

**失败场景**：新上下文只读恢复锚点前 15 行 → 读到被禁止的通过数，并被告知去执行 HEAD 里已经完成的「下一步」。同一文件内纪律与锚点自相矛盾。

**归因**：`270c1716` 在 C4 之后重新写入，属**缺少自动纪律门导致的后续回归**，不是 `1b7485b9` 当次改动引入。

**owner → DEBT-18（补卡需求，登记如下）**

| 字段 | 内容 |
|---|---|
| id | `DEBT-18` |
| 标题 | 可执行的锚点纪律门 |
| what | 重建 `CURRENT_TASK.md` 前 15 行（删 CI 通过数、删已完成的「未来动作」）；建 lint **只检查可变状态文档**，冻结的审查证据走显式 allowlist |
| 完成判据方向 | fixture 写入 run 号或 `517 passed` 必须让 lint 变红（先红后绿）；allowlist 内的历史审查报告不得误伤 |
| 估时 / wave / deps | 2h / wave 1 / 无 |

> ⚠️ 这条纪律**在本卡的产出里也必须遵守**：本台账与 DEBT-13 台账均不落盘 CI run 号与通过数；引用的测试计数一律带 commit/文件锚点、标为时点证据。

### 4. B4 — payload 准入与快照完整性 🔴 STILL-OPEN

**现状**（Codex 裁定 + 我方独立取证一致）：

- `backend/app/graphiti/canvas_episode.py:208-247`：`CanvasGraphEpisodeV1` 的 vault/group/canvas/node ID 仍是**裸 `str`**，且**无 provenance 字段**。
- 生产链路 `endpoints/memory.py:547-576` → `memory_service.py:1402-1453` → `graphiti_structured_writer.py:106-142` **未形成统一强制门**。
- `session:` 隔离只做了一半：完整会话原文走 sibling 隔离，但**摘要 / tips / Q&A 仍走普通 group**（`memory.py:749-761`、`conversation_distiller.py:359-407`）。我方补充取证：`memory.py:753` 的 `node_id = f"session:{request.session_id[:16]}"` 是**拼接产生方，不是准入校验方**。
- SnapshotV3 无来源 digest（`snapshot_v3.py:243-251`）；generation 仅绑定路径/mtime/size（`board_manifest_service.py:501-519`）。
- ⚠️ **易混淆点（我方登记）**：仓内 `error_writer.py:83,98` 与 `candidate_callout.py:72` 的 `provenance` 是 `seeded|distilled` 的**测试种子角标**（2026-07-20 裁决），与 B4 要的「episode payload 来源证明」**不是同一个东西**，不得拿来充数。

**四条可复现反例**：① `node_id="../../forged"` 及不匹配的 vault/group/canvas 被请求模型与 episode 模型接受；② 传入 `provenance={...}` 后 `model_dump()` **静默丢字段**；③ 正常 session 全文进 sibling，结构化摘要仍进普通 group；④ 生成 `score=0.4` 的快照后只把落盘 score 改成 `0.99` 并保留 generation，下一次 live 不重写磁盘，删除节点源触发降级后返回伪改的 `0.99`。

**绿灯为何不冲突**：B4 邻接的 48 个测试只验证基础模型 / 路由 / writer 原样传递，**没有让 episode schema 成为 endpoint→queue→writer 的强制门**。

**owner → CARD-G4-8（现成卡，归属恰当，但裁定必须拆）**

| 子卡 | 范围 | 估时 / wave / deps |
|---|---|---|
| **G4-8A** payload 准入与命名空间 | 真实 endpoint→queue→writer 拒绝伪造 ID；持久化 required provenance；**所有** session 结构化产物隔离 | 5–7h / wave 3 / G4-5 + DEBT-11 |
| **G4-8B** 快照数值闭包与来源完整性 | `1e308` 走 HTTP JSON 的边界；canonical-source digest / 等价证明；同代 `0.4→0.99` 改写必须重建或拒绝 | 6–8h / **wave 2** / **不应被 G4-5 / DEBT-11 阻塞** |

拆分理由：G4-8B 与 Graphiti episode 契约无依赖关系，捆在 wave 3 会被无关前置卡拖住；且它承接的正是 P1-01 边界里划给 B4 的那半边。

### 5. TOCTOU — containment 判定与 open 非原子 🔴 STILL-OPEN

**窗口仍在**（我方独立复核确认）：`lancedb_client.py:1973-1981` — 先 containment check，后按**路径**重新 `open`；full 入口同型（`:1655-1660` 检查，`:1681`、`:1718-1728` 分别 hash / read）。

**射程比五轮包登记的更大**（本轮新增事实）：同型窗口还在 backfill、relationship、projection、error rebuild —— 例如 `backend/app/services/vault_backfill.py:195-201`。

**反例**：在检查返回后、正文读取前确定性替换路径对象。single / full 两条真实 Lance 入口均观测：`returned=1`、替换后 marker 出现在索引 row、`row_count=1` —— 说明检查、hash、正文**没有绑定同一文件句柄 / 同一组 bytes**。图写入后的真实 Neo4j 影响标 `UNVERIFIABLE`（本轮只读沙箱不连生产库），但 Lance 持久化反例已足以判开。

**归属裁定（本卡必须给出的产出之一）**：

> **不归 G4-8，也不归任何现有 G4 卡。** G4 族各卡的范围是读作用域（G4-1a/1b）、四态（G4-2/3）、VaultScope（G4-4）、outbox（G4-6）、payload 准入（G4-8）、DLQ（G4-9），**没有一张覆盖文件系统准入的原子性**；而该窗口跨 Lance、backfill、relationship、projection、error rebuild 五个面，塞进任何一张 G4 卡都会让那张卡的范围失真。**裁定为独立 infra-debt 补卡。**

| 字段 | 内容 |
|---|---|
| id | `INFRA-DEBT-01` |
| 标题 | 已验证文件对象贯穿（TOCTOU 收口） |
| what | 统一 `open_admitted_markdown` 或等价抽象，使 containment、regular-file、identity、hash、正文**基于同一 fd / handle / bytes** |
| 完成判据方向 | 所有生产 reader 的确定性交错必须显式拒绝或一致重试，并产生零 hash / 零 index / 零 dry-run / 零 graph-write；macOS 与 Linux 契约一致 |
| 估时 / wave / deps | 10h，wave 1 启动；建议拆 **01A** Lance/orchestrator 5h、**01B** 其余 reader 5h（wave 2，依赖 01A） |

### 6. P1-03 — 服务层四态贯穿 🔴 STILL-OPEN（部分闭合）

**已闭合的半边**（CARD-G4-2 `9960b146`，经 `d3dcb16c` 合入主线）：

- 统一四态类型 `backend/app/models/service_status.py:39-139`（`ServiceStatus` 枚举 + degraded/unavailable 必带 reason + `OK` 必须非空 items）。
- 三条 statused 入口 + `CanvasRAGState`（`lib/agentic_rag/state.py:183-202`）+ RAG fallback。
- G4-2 自身经 Codex round-1 判 4 BLOCKER + 6 HIGH 后整改：检测由「异常被抛出」改为「探测后端健康」——因为生产最常见故障**不抛异常**。

**仍缺的半边**（我方逐条复核确认）：

1. **客户端内部吞异常**：`lib/agentic_rag/clients/graphiti_client.py:312-379`、`lancedb_client.py:3061-3077` 内部异常直接降 `[]`，四态拿不到信号。
   反例：真实 Graphiti client 内部查询抛 `ConnectionError` → 观测 `client_search=[]`、`channel_errors={}`、融合结果 `status="empty"`、`reason=null`。
2. **生产兼容入口主动剥状态**：`memory_service.py:1091-1106`（`get_review_suggestions`）与 `:2384-2409`（search）——委托到 statused 方法后 `return result.items`，状态被丢弃。
   > 诚实登记：这是 G4-2 **显式声明的兼容取舍**（「保 list 契约」，约 12 处直接迭代），**不是疏漏**；方法自身 docstring 就写着「空 list 无法区分『没有待复习概念』与『Neo4j 挂了』」。但 P1-03 的义务是「贯穿 MemoryService **全部**读路径」——只要生产调用方还在旧 wrapper 上，义务就没到端。
3. **history 折算与统一规则不一致**：`memory_service.py:795-805` 只要 `retrieval_failure` 就固定判 `DEGRADED`；而统一折算 `service_status.py:172-192` 规定「有失败 且 无结果 且 无健康源 → `unavailable`」。冷启动 + 无内存 episode + Neo4j 主/恢复查询均失败时，观测 `items=[]、status="degraded"`，应为 `unavailable`。

**绿灯为何不冲突**：P1-03 的 81 个定向测试让 getter 在**客户端外层**抛异常，或手工注入 `channel_errors`；没有一条经过客户端内部 `enable_fallback=True → []` 的路径，而且测试还锁定旧 list wrapper。

**owner → CARD-G4-2 重开**（流程不允许重开已收官卡则建 `G4-2R`，owner 链仍属 G4-2）。余量约 **4–6h，wave 1**。范围：修客户端吞异常、五路 RAG 状态覆盖、history unavailable 折算、把生产调用方迁离剥状态 wrapper。

### 7. P1-04 — API / trace / UI 面四态 🔴 STILL-OPEN

**现状**：

- API schema **无 `status` / `degraded_reason`**：`backend/app/models/memory_schemas.py:130-149`、`backend/app/api/v1/endpoints/rag.py:122-142`。
- endpoint 重建响应时**丢状态**：`endpoints/memory.py:201-237`、`rag.py:264-326`。
- 前端对 `retrieval_status` / `retrievalStatus` **零命中**；`frontend/src/components/profile/LearningProfile.tsx:36-96` 把子数据失败折成 `?? []`。
- git 全历史**未找到 CARD-G4-3 提交**。

**我方补充（防混淆）**：仓内确实有一批 `degraded_reason` 字段（`endpoints/chat.py:238,376,523`、`exam_sessions.py:82,210`、`review.py:1125,1822`、`models/schemas.py:1009-1013`、`review_models.py:685`、`board_manifest.py:207`）——但那是 D3 血统的**分散加性字段**，加上 MCP 的 `source_status` 三态与 memory health 三态，全仓是**三套不齐的词汇**，不是统一四态透出。不得据此宣称 P1-04 已闭合。

**失败场景**：MemoryService 返回 `items=[]、status=unavailable、reason="neo4j down"`，调真实 endpoint 后响应只有 items 与分页字段；RAG 返回 unavailable 后仍是 200 空结果且无状态。**消费者看到的 bytes 与健康真空完全相同。**

**owner → CARD-G4-3**（现成卡，原卡范围准确，**无需拆**）。总账估时 6h，wave 2，依赖 G4-2R。
本批（BATCH-2026-08-31-第七批）V4 车道正在做此卡——本台账的裁定可直接作为其验收输入。

---

## 三、最小收官清单（Codex 判词：三判词中两项仍开，清单封闭）

针对 **P1-05 / P1-01 / P1-08** 三判词，收官只需两张卡：

1. **DEBT-17** — 四类「先合法入库、后被拒/删除」fixture 经 direct endpoint **一次**调用后，rows 与 fingerprints 全清。
2. **DEBT-18** — `CURRENT_TASK.md` 前 15 行修正；可变状态文档 lint 对 run 号、通过数、已完成的未来动作全部先红后绿。

**P1-01 无追加动作。** 其余四项（B4 / TOCTOU / P1-03 / P1-04）的全部后续义务已封闭映射到
G4-2R、G4-3、G4-8A、G4-8B、INFRA-DEBT-01，**不存在未指派残项**。

---

## 四、本轮的 UNVERIFIABLE（如实登记，不猜）

| 项 | 为什么无法在本轮证实 | 需要什么才能证实 |
|---|---|---|
| 真实存量 Neo4j episode / 快照的不合规数量 | 本轮只读沙箱只用合成临时 vault 与 LanceDB，未连接生产 7691 | 获用户批准的**只读**生产 census |
| TOCTOU 交错后对图写入的实际影响 | 同上（Lance 持久化反例已足以判开，图侧未验） | 同上 |

这两条**不影响**本轮任何代码路径裁定。

---

## 五、回填 G8-9 统一验收门底账

本台账按 CARD-G8-9 §4「DEBT-16（P1 残项单轮终裁）…完成判据中『回填 G8-9 底账』条款的落点即本文件对应行」执行，落点为
`_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md` **§2.3 故障诚实** 的
「服务层（Memory/RAG）四态贯穿」判据行。

**只引用不重定义**：本台账不改 G8-9 的 `source_criterion`、不改其三态判定纪律、不新增维度；
按 append 补 evidence 与 note，**不重排任何行**。

已执行的改动（§2.3 表行 + §3 YAML 同行 + §5 残余登记指针，三处一致）：

- `coverage`：`none` → `partial`（G4-2 已落地，但三条反例在案）
- `evidence`：追加 G4-2 实现锚点与本台账指针
- `owners`：`G4-2, G4-3, G4-6` → 追加 `G4-2R`
- `outcome`：**维持 `not_yet` 不动**——G8-9 §1「缺 outcome 或存在未闭合反例时 fail-closed」

**owner 引用的边界（按 G8-9 §1「owner 只引用未完成的正式卡」）**：本轮新登记的
`DEBT-17` / `DEBT-18` / `INFRA-DEBT-01` / `G4-8A` / `G4-8B` **尚未落进总账 v2 的 `#### <id>` 档案节**，
因此**不写进 G8-9 的 owners 数组**，只在本台账登记为补卡需求。唯一进 owners 的是 `G4-2R`——
它是既有 G4-2 owner 链的延续，不是新命名空间。**正式落账动作归主 session 排卡，不在本卡范围。**

**未改的部分（显式声明）**：

- 不新增维度、不改任何 `source_criterion`、不改判定纪律、**不重排任何行**。
- §2.1 数据安全的「0 静默删除/覆盖」虽与 P1-05 / TOCTOU 沾边，但那两项是「越界准入 / 读取原子性」，
  与该维 source_criterion 的「0 静默删除/覆盖」**不同义**——本次**不改数据安全维任何行**，
  只在 §5 留指针，避免越界改判。
