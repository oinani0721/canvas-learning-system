> 批次: BATCH-2026-09-07-第十三批 · 车道 U5(card-u5-lance) · 卡 CARD-HYGIENE-openapi round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HYGIENE-openapi-r2.md)"`
> 审查绑定: `dddfc598` （审 SHA = 当时 HEAD；HEAD 现已前进，见 round-3 的绑定）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `sandbox: read-only`

---

**发现 1 条 HIGH、3 条 MEDIUM。剩余 GET 面仍有请求期写入，不能认定“零写”通过。BLOCKER、LOW：本节无。** 以下为静态调用链结论，未执行请求或测试。

1. **HIGH — FSRS 查询会创建并持久化默认卡。**

   **位置：**[review.py:1430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/app/api/v1/endpoints/review.py:1430)、`backend/app/services/review_service.py:2507`。

   **触发条件：**FSRS manager 可用，查询的 concept 没有已有卡、且不受 frontmatter 管辖时，保留的 `GET /api/v1/review/fsrs-state/{concept_id}` 会写入 `backend/data/fsrs_card_states.json`。

   调用链：`review.py:1429–1430` → `review_service.py:2465–2476` 检查管辖状态及已有卡 → `:2507` `_save_card_states()` → `:600` 创建目录、`:604` 写临时文件、`:605` 替换目标。目标路径定义在 `:116–118`。

   **这属于请求期写入，应追加排除该 GET。** 构造时的 `:526` → `:553–555` 只读取快照，不能把该文件仅归因于启动初始化。

2. **MEDIUM — 统一存储健康检查会间接写盘。**

   **位置：**[health.py:1671](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/app/api/v1/endpoints/health.py:1671)。

   **触发条件：**`GET /api/v1/health/storage` 未命中 30 秒缓存、存储路径可写时，会创建目录并创建、删除探针文件。

   调用链：`health.py:1658` 缓存判断 → `:1671` `_check_json_health()` → `:1444` 默认路径 `./data` → `:1448` `mkdir` → `:1452–1453` 对 `.health_check` 执行 `touch/unlink`。

   **应追加排除该 GET。** 探针正常删除后，结束时的 `find -newer` 也看不到这次写入。

3. **MEDIUM — 多模态健康检查每次请求都会尝试写探针。**

   **位置：**[multimodal.py:251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/app/api/v1/endpoints/multimodal.py:251)、`backend/app/services/multimodal_service.py:1035`。

   **触发条件：**保留的 `GET /api/v1/multimodal/health` 到达服务且目录可写时，会写入并删除 `.health_check`。

   调用链：`multimodal.py:251` → `multimodal_service.py:1019` `get_health_status()` → `:1034–1036` `write_text("test")/unlink()`。

   **应追加排除该 GET。** 此外，该服务构造器 `:205` 和首次初始化 `:332` 均调用 `:210–216` 创建媒体目录；其他多模态 GET 也存在条件性初始化写入，尚不能据此认定它们安全。

4. **MEDIUM — 五项门漏检代码目录内其他子目录中的 vault 骨架。**

   **位置：**[conftest.py:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/contract/conftest.py:38)、`:43`。

   **触发条件：**写方法过滤回归，初始化目标为 `backend/<非五项名称>/` 时，骨架仍写进代码目录，但五项顶层检查全部为空。

   `system.py:466、475` 将请求指定的根传给初始化服务；fixture 只检查五个固定顶层名称。这是**检测边界缺口**，不涉及评价 `vault_path` 校验设计。

   对“vault 根恰好是 `backend/`”的完整初始化，检测充分：`VaultInitService:18–23` 的目录被 `raw/wiki/outputs` 覆盖，`:96–98` 的文件被 `CLAUDE.md` 覆盖。另有 `.gitkeep`、`.gitignore` 产物（`:93–104`），但完整初始化同时产生上述骨架，**不能仅因未单列这两项就判定漏检**。

**问题 1：五类文件的归因结果**

| 文件 | 已确认的调用链与结论 |
|---|---|
| `fsrs_card_states.json` | **已确认请求期 writer**，见 HIGH 发现；静态链不能证明它是那次全跑的唯一 writer。 |
| `vault_index_pending__canvas_vault.jsonl` | 服务存在后台与关闭写入：`vault_index_orchestrator.py:799–804` 周期 reconcile → `:628` 持久化；`:853–864` shutdown 也持久化；最终 `:337–342` 写临时文件并替换。**不是只有启动一次性写这一种机制。** `metadata.py:670–671` 的状态查询调用 getter/freshness，已读 freshness 中没有 journal 写入；尚未核实 lifespan 调用入口。 |
| `memory-system-*.log` | `health.py:849、853、865、883、909` 明确在 GET 请求处理中调用 `memory_logger`，包括连接失败路径。日志文件 handler 的绑定尚未核实，因此**不能把该文件直接归为启动专属写入，也不能宣称落盘链已闭合**。 |
| `llm_call_logs.db` | **未完成归因。** |
| `qa_metrics.db` | **未完成归因。** |

完整归因仍缺 `app/main.py` 的 import/lifespan 段、`system.py` 两个统计 GET，以及相关初始化函数。当前授权只包含 `system.py:430–476`；补读请求尚未收到答复，所以未越界读取。已有 mtime 和 gitignore 证据不能替代调用归因，**不需要重跑 4 小时 55 分的测试来补这个缺口**。

**问题 2：历史配置冲突——本节无。**

本机所审查的 schemathesis 加载链为：

`openapi/loaders.py:216–217` → `SchemathesisConfig.discover()` → [`config/__init__.py:162`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/.venv/lib/python3.14/site-packages/schemathesis/config/__init__.py:162)。

它查找的是 **`schemathesis.toml`**，没有读取 `pyproject.toml` 的 `[tool.schemathesis]`。因此历史块中的 `100 / 5000 / stateful="links"` 对当前入口不起作用。

`generation/hypothesis/builder.py:142–177` 取得并合并用户 `@settings`；本文件的 **10 / 10000 / explicit+generate** 不会被该历史块覆盖。该结论绑定本机源码，未泛化到所有 4.x 版本。

**问题 3：错误排除只读 operation——本节无。**

独立集合复算确认：**206 = 92 + 114**；差集为 POST 96、DELETE 9、PUT 6、PATCH 2、GET 1，无新增 operation。唯一移除的 GET 是 `/api/v1/health/lancedb`，`GET /` 保留。

未确认任何“明确纯读且应当恢复”的被排除条目；没有把 `read_note`、`search_*` 等名称当作完整调用链纯读的证据。

**问题 4：五项检测面——见 MEDIUM 发现。**

它足以发现指定顶层骨架，不能证明代码目录整体零写。六条 `find` 命中均在该门之外；五项检查通过不会使已经失败的 `find` 判据转为通过。

**问题 5：跨 module 连锁失败——本节无。**

`conftest.py:59、68–84` 的行为符合设计：module A 留下骨架，A 的后检失败；module B 开始时现场仍脏，B 的前检继续阻断。**这不是把污染错误归责给 B，而是要求现场清理后才能继续。** `:72` 的“合约测试开始之前”应理解为当前 module 开始之前。
