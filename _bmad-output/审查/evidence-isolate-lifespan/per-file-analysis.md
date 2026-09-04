## backend/tests/api/v1/endpoints/test_agents_dedup.py
- conversion: no_lifespan
- deps:
  - lifespan 预热的 MemoryService 单例（main.py lifespan 段落） | breaks=False | app/api/v1/endpoints/agents.py:1430 (memory_service: MemoryServiceDep) → app/api/v1/endpoints/memory.py:75 (Me
  - RAGService 单例（lifespan 侧 LanceDB recover_pending 等） | breaks=False | app/api/v1/endpoints/agents.py:1429 (rag_service: RAGServiceDep) → app/dependencies.py:592-635，惰性兜底在 :628-629 
  - Neo4jClient 单例（lifespan 的 FULLTEXT INDEX DDL / 预热） | breaks=False | app/dependencies.py:649-680 get_neo4j_client_dep() → :676 `return get_neo4j_client()`（app/clients/neo4j_client
  - set_alert_manager 全局 / app.state.alert_manager（main.py:134） | breaks=False | grep -c 'app\.state|get_alert_manager|request\.app' app/api/v1/endpoints/agents.py → 0；app/dependencies.py → 0
  - set_mastery_engine 全局 / app.state.mastery_engine·signal_registry·fusion_engine（main.py:252-254） | breaks=False | grep -c 'get_mastery_engine|app\.state' app/api/v1/endpoints/agents.py → 0；app/dependencies.py → 0
  - resource_monitor 后台采集 / prompt_registry / episode_worker / vault_index_orchestrator / archive_scheduler / schema_gate | breaks=False | 本文件唯一 HTTP 路径 POST /api/v1/agents/explain/oral（app/api/v1/endpoints/agents.py:1418-1452 → _call_explanation :1
- risks: ⛔ 本文件的 lifespan 从来没跑过 —— 只做 A 会假绿。`client` fixture 是死代码（--setup-plan 实测 15/15 测试都没请求它），两个 HTTP 用例走 ASGITransport（httpx/_transports/asgi.py:106-108 只有 http scope，不发 lifespan）。所以『把 lifespan 关掉』对本文件的 7691 连接数改善精确为 0。若本卡验收判据是『测试进程零连 7691』，把这个文件计入『已改造』而只加了 no_lifespan 包装，就是把一个从未存在的问题标记为已修，同时放过真实泄漏。 | ⛔ 真实的 7691 连接在 request-time 解依赖，不在 lifespan。链路：agents.py:1430 MemoryServiceDep → memory.py:75 → memory_service.py:2909-2914 惰性 new+initialize → :278 `await self.neo4j.initialize()` → .env:67 `NEO4J_URI=bolt://localhost:7691`（.env:65 `NEO4J_ENABLED=true`）→ 还会跑 :282 `_recover_episodes_from_neo4j()` 的读 Cy

## backend/tests/api/v1/endpoints/test_fsrs_state_api.py
- conversion: no_lifespan
- deps:
  - review_service 单例（lifespan 并未装配；端点自取） | breaks=False | backend/app/api/v1/endpoints/review.py:1412 (`review_service = await _get_review_service_singleton()`)；导入点 rev
  - FSRS_AVAILABLE / FSRS_RUNTIME_OK 模块级全局（review_service.py） | breaks=False | backend/app/api/v1/endpoints/health.py:105-110（函数体内 `from app.services.review_service import FSRS_AVAILABLE, F
  - neo4j_client 单例（health 端点请求时惰性取，lifespan 会把它预热成 initialized） | breaks=False | backend/app/api/v1/endpoints/health.py:143-175（`get_neo4j_client()` → 读 `neo4j.stats` → 只有 is_real_neo4j 才 `aw
  - intelligent_parallel._deps_initialized（health 端点读的另一个模块级全局） | breaks=False | backend/app/api/v1/endpoints/health.py:116-120；定义 backend/app/api/v1/endpoints/intelligent_parallel.py:73，写侧只有
  - app.state.* 全家桶（alert_manager / mastery_engine / signal_registry / fusion_engine / episode_worker / vault_index_orchestrator）+ set_alert_manager / set_mastery_engine 全局 | breaks=False | 写侧 backend/app/main.py:134（app.state.alert_manager）、:137（set_alert_manager）、:252-254（mastery_engine/signal_reg
  - _resolve_vault_group_id 的 ContextVar 注入（两个 review 端点都会先跑） | breaks=False | backend/app/api/v1/endpoints/review.py:1407（fsrs-state）与 :1062-1066（record）调用；实现 review.py:27-61，内部只 import `a
- risks: 【与提示中点名的三个文件无交织】本文件的 `client` 是**函数级**（:45-48），不是 tests/unit/test_vault_scope_409.py:164-172 那种 module 级，也不与 isolated_episode_worker 交织；本文件不请求 /metrics 或 /metrics/summary（那是 tests/test_deep_monitoring.py 的射程），不涉及 mastery_mod._engine/_store（那是 tests/unit/test_mastery_api.py）。所以本文件是三种改法里风险最低的一档，不需要 409 语义保全、也不需要担心 lifespan 的 set_mastery_engine 覆盖测试预置。 | 【唯一可观测行为差异，未被断言】GET /api/v1/health 的 `components["neo4j"]`：开 lifespan 时单例已 initialized ⇒ 端点真的对 7691 发 `RETURN 1 AS ping`（health.py:157-158）并返回 ok/degraded；关掉后走 `not_initialized`（health.py:171-172）。本文件四个 health 测试只断言 `components["fsrs"]`，无一条覆盖 neo

## backend/tests/test_debug.py
- conversion: no_lifespan
- deps:
  - bug_tracker 单例（本文件唯一真正的被测依赖）— 但它不是 lifespan 产物 | breaks=False | app/api/v1/endpoints/debug.py:20（module 级 import）+ :92 / :144 / :219（调用时读模块全局）；app/core/bug_tracker.py:257 `bu
  - alert_manager（set_alert_manager 全局 + app.state.alert_manager） | breaks=False | app/main.py:134 `app.state.alert_manager = alert_manager` / :137 `set_alert_manager(alert_manager)`；debug.py 全
  - mastery_engine / signal_registry / fusion_engine（set_mastery_engine 全局 + app.state.*） | breaks=False | app/main.py:251-254；本文件请求路径仅 /api/v1/debug/* 与 /api/v1/openapi.json，无 /api/v1/mastery/*
  - resource_monitor 后台采集（start_background_collection） | breaks=False | app/main.py:116-118；本文件不请求 /metrics 或 /metrics/summary（见 endpoints_exercised）
  - MemoryService 预热 / Neo4j FULLTEXT DDL / LanceDB recover_pending / EventBus recover_outbox / episode_worker / wikilink eager build / prompt_registry / cost_tracker / archive_scheduler / vault_index_orchestrator / schema_gate | breaks=False | app/main.py:104-106、:116-131、:141-157、:161-175、:177-191、:193-203、:205-221、:223-254、:284-290、:421、:435；debug.py
  - 路由表 / OpenAPI schema（两个 TestDebugRouterRegistration 测试的被测对象） | breaks=False | app/api/v1/router.py:207-215（include debug.router, prefix="/debug", tags=["Debug"]）+ app/main.py:787（include a
  - 其它 startup/shutdown 钩子（会被 lifespan_context 替换一并禁用的东西） | breaks=False | 全仓 `grep -rn "on_event|add_event_handler" app/` 仅命中 main.py:88 的一句 docstring 与三处同名的 record_interaction_event（m
- risks: **4 个构造点，不是 2 个**：除 :66 / :78 两个 fixture，`TestDebugRouterRegistration` 在 **测试函数体内**又各起了一个 `with TestClient(app) as client`（:278、:293）。只改 fixture 会留下 2 个测试照常跑真 lifespan、照常连 7691，而且这两个测试仍会通过——静默漏改，本卡的『零连 7691』判据必须按 grep `TestClient(app)` 计数验收，不能按 fixture 数。 | **`test_debug_tag_in_openapi`(:291-302) 的断言实际只靠 fallback 分支成立**：实测 `[t['name'] for t in openapi.get('tags', [])] == []`——顶层 tags 恒为空，因为 `_custom_openapi`(main.py:541-570) 调 `get_openapi(...)` 时**没有传 `openapi_tags`**（:547-552 只传 title/version/description/routes）。所以 `assert "Debug" in tags or any(...)` 永远靠右半边的 path 级 tags 过关。这是本卡改造**之前就存在**的形

## backend/tests/unit/test_fsrs_state_query.py
- conversion: no_lifespan
- deps:
  - ReviewService 进程单例 get_review_service()（端点 await 它拿服务对象） | breaks=False | app/api/v1/endpoints/review.py:1412 — `review_service = await _get_review_service_singleton()`（名字由 review.py:1
  - vault 作用域 ContextVar（_resolve_vault_group_id → set_current_subject_id） | breaks=False | app/api/v1/endpoints/review.py:1407 — `_resolve_vault_group_id(vault_id, subject_id=subject_id, legacy_group_i
  - 中间件栈的指标/CORS/编码/异常兜底（MetricsMiddleware 等） | breaks=False | app/middleware/metrics.py:97 `CONCURRENT_REQUESTS.inc()` / :135-141 `REQUEST_COUNT.labels(...).inc()`，读的是 metr
- risks: 【本文件不涉及主控点名的三个坑】本文件的 client 是 function 级、非 autouse、类内私有（:56-60），不是 test_vault_scope_409.py 的 module 级形态；不测 /metrics（与 test_deep_monitoring.py 的 resource_monitor 填充问题无关）；不碰 mastery_mod._engine/_store（与 test_mastery_api.py 的 set_mastery_engine 覆盖问题无关）。可以按 A 方案直改。 | 【最重要，改造验证的假绿面】端点 review.py:1448-1457 把**任何**异常吞成 `200 + found=False + reason="error: ..."`。因此 `test_endpoint_returns_not_found_when_no_card`（:111-134）的四条断言（200 / concept_id / found is False / fsrs_state is None / card_state is None）在「patch 失效、service 抛异常、甚至整条依赖链炸掉」时**同样全绿** —— 它无法为 no_lifespan 改造提供任何证据。`test_endpoint_handles_special_c

## backend/tests/unit/test_fsrs_state_query.py
- conversion: None
- deps: NONE
- risks: 

## backend/tests/unit/test_mastery_api.py
- conversion: no_lifespan
- deps:
  - set_mastery_engine 全局 (_engine_instance) / app.state.mastery_engine | breaks=False | app/services/mastery_engine.py:786-789 (get_mastery_engine: `global _engine_instance; if _engine_instance is N
  - mastery store 单例 (_store_instance) | breaks=False | app/services/mastery_store.py:535 `_store_instance: MasteryStore | None = None`；:544-550 `if _store_instance i
  - app.state.* / alert_manager / resource_monitor / prompt_registry / episode_worker | breaks=False | app/middleware/metrics.py:110 `request.state.request_id = request_id`（唯一 state 写点，是 request.state 不是 app.state
  - vault 作用域解析 (resolve_vault_group_id → ContextVar 注入) | breaks=False | app/api/v1/endpoints/mastery.py:53-55 alias → app/api/v1/endpoints/_vault_id_resolver.py:22 → app/core/vault_s
- risks: ⛔ 最大坑：光换 no_lifespan **达不到本卡「零连 7691」目标**。因为 stub store 注入是死的，请求期真 store 仍会 `await self._client.run_query`（mastery_store.py:123）连库。必须连带修 seam，否则这个文件是「改了但没生效」的假绿。 | ⛔ `engine = MasteryEngine.__new__(MasteryEngine)`（:43）缺 `_fusion_engine` 属性。今天不炸，只因为这个 engine 从没被用过；一旦 seam 接通，`concept_to_response`（mastery_engine.py:665）立刻 AttributeError → 全部 200 断言变 500。这是「fixture 形态 ≠ 生产形态」的同型陷阱：注入修好的那一刻缺陷才第一次暴露。 | 改造会把 3 条此前红/依赖现网数据的断言（:82 len==1、:116 save_concept.assert_called_once、:213 old_p_mastery==0.8）转绿。若有人拿「改造前后 pass 数一致」当验收判据，这个文件会被误判为回归。判据必须是逐用例 outcome 比对，不是总数。 | 反向副作用（正面但需登记）：改造前 15 个参数化写用例（grade×4 

## backend/tests/unit/test_sync_batch_auth.py
- conversion: no_lifespan
- deps:
  - schema_gate 单例的 _verified 预热（main.py:341-343 lifespan 里 await get_canvas_schema_gate().verify()） | breaks=False | app/api/v1/endpoints/sync.py:107 `gate_reason = await get_canvas_schema_gate().block_reason()`（accessor 由 sync
  - vault_identity_registry 单例 / :VaultIdentity 认领 | breaks=False | app/api/v1/endpoints/sync.py:126 `await get_vault_identity_registry().assert_identity(raw_vault_id=..., physic
  - get_sync_service 单例 / SyncService 的 Neo4j driver | breaks=False | app/api/v1/endpoints/sync.py:137-138 `service = get_sync_service(); return await service.process_sync_batch(..
  - vault 作用域解析（409 fail-closed 门） | breaks=False | app/api/v1/endpoints/sync.py:114-118 `resolve_vault_group_id(...)` → app/core/vault_scope.py:162-176 的 409 分支；
  - alert_manager（set_alert_manager 全局 + app.state.alert_manager）/ mastery_engine / prompt_registry / resource_monitor 后台采集 / episode_worker / vault_index_orchestrator | breaks=False | main.py:134 / :252-254 / :284-290 / :435 装配；本文件请求路径 app/api/v1/endpoints/sync.py:74-161 全文**不出现** request.app.
- risks: ⛔ 最大的坑：单关 lifespan 达不成「零连 7691」。sync.py:107 的 schema gate 在 _verified is None 时**请求期**重验（schema_gate.py:102-103），只是把拨号从启动期挪到请求期。我实测 7691 端口 OPEN 且三条约束在位（docker exec cypher-shell SHOW CONSTRAINTS → canvasnode/canvasboard×2 全在），所以 200 用例现在是靠现网库绿的。必须同批 stub gate，否则验收单上「零连」是假声明。 | gate 单例 `_gate`（schema_gate.py:114）是**进程级全局且全仓没有任何 autouse 重置**（grep tests/ 里 schema_gate 只出现在 test_schema_gate.py，且那里是直接 new CanvasSchemaGate()）。这意味着跨文件污染面存在：同一 pytest worker 里若有别的文件先把 _verified 置成 False（现网哪天掉了约束、或某测试注入了缺约束的 fake），本文件两条 200 用例会变成 503（detail="Canvas schema constraints missing..."）。加 stub 顺带把这条隐性耦合掐掉，是净收益

## backend/tests/unit/test_sync_group_isolation.py
- conversion: lifespan_lite
- deps:
  - schema_gate 单例 _verified 预热（main.py:343 `await get_canvas_schema_gate().verify()`） | breaks=False | app/api/v1/endpoints/sync.py:107 `gate_reason = await get_canvas_schema_gate().block_reason()`（→ 503 at :109）
  - vault_identity_registry 单例（**非** lifespan 产物：main.py 全文零引用，纯懒单例） | breaks=False | app/api/v1/endpoints/sync.py:126 `await get_vault_identity_registry().assert_identity(...)`
  - app.state.alert_manager / app.state.mastery_engine / set_mastery_engine 全局 / app.state.episode_worker / resource_monitor 后台采集 / prompt_registry / vault_index_orchestrator | breaks=False | app/api/v1/endpoints/sync.py:96-161（handler 全链零 `request.app.state`、零 `get_*_engine()`）+ app/main.py:757-779（C
  - sync_service 单例（**非** lifespan 产物：main.py 全文 grep 'sync_service' 零命中，lifespan 既不创建也不 cleanup） | breaks=False | app/api/v1/endpoints/sync.py:137 `service = get_sync_service()` → app/services/sync_service.py:681-686 懒单例
- risks: 【首要】纯 A 方案（no_lifespan）达不到本卡「零连 7691」目标。schema_gate 的连库在**请求路径**上，不在 lifespan 上：sync.py:107 `block_reason()` → schema_gate.py:102-103 lazy `verify()` → :48-55 建 driver → :76 `SHOW CONSTRAINTS`。关 lifespan 只是把这次连接从 startup 挪到请求时。必须叠加 lite 装配（预置 `_verified=True`）才真的零连。 | 【今天的绿是借来的】该测试当前拿到 200，是因为现网 7691 上三条 canvas 复合唯一约束**恰好齐全**（我只读实测 `MISSING=[]`）。一旦 Neo4j volume 重建 / migrations/003 未跑，`_verified=False` → sync.py:109 直接 503 → 本测试红，而这跟它想测的「group_id 绑定」毫无关系。stub 掉 gate 后反而更稳、更诚实。 | 【只改本文件不够】同目录另有 3 个文件打 /sync/batch 且**同样没 stub schema_gate**：tests/unit/test_vault_scope_409.py、test_sync_batch_auth.p

## backend/tests/unit/test_system_endpoint_auth.py
- conversion: no_lifespan
- deps:
  - require_internal_api_key 的依赖闭包（本文件唯一真正被断言的逻辑） | breaks=False | backend/app/security.py:64-68
  - app.state.* 全族（alert_manager / mastery_engine / signal_registry / fusion_engine / episode_worker / vault_index_orchestrator / rag_s0_warmup_task） | breaks=False | backend/app/api/v1/system.py:1-1232（grep 'app\.state' 零命中，实测）
  - get_runtime_model_config() 单例（/config 的唯一外部协作者） | breaks=False | backend/app/core/litellm_config.py:176-186
  - register_litellm_callbacks() → litellm.callbacks（llm_call_logger + cost_tracker） | breaks=False | backend/app/main.py:151-155（装配侧） / backend/app/api/v1/system.py:845-852（/test-llm 的消费侧）
  - 中间件链（CORSExceptionMiddleware / EncodingValidationMiddleware / CORSMiddleware / MetricsMiddleware） | breaks=False | backend/app/main.py:757-779（注册） + backend/app/middleware/metrics.py:97,131,135（只用模块级 prometheus Counter/Gauge）
  - fastapi_mcp mount_http()（唯一可能把第三方 lifespan 挂进 app.router.lifespan_context 的嫌疑） | breaks=False | backend/.venv/lib/python3.14/site-packages/fastapi_mcp/server.py:312-365（mount_http 全文，无 lifespan / task_group
- risks: ⛔ 本文件在 HEAD 上**本来就红 2 条**，与 lifespan 无关，别误记成「关 lifespan 弄坏的」：`TestSystemConfigAuth::test_prod_no_key_configured_503`(:110-114) 和 `TestSystemTestLLMAuth::test_prod_no_key_configured_503`(:167-170) 实得 500 而非 503。根因：`_settings_factory(debug=False, key="")`(:52-64) 在请求期构造 `Settings(...)`，被 `app/config.py:274-298` 的 `validate_security_defaults` 直接拒收（`is_local = DEBUG and localhost in CORS` → False ⇒ raise ValueError "INTERNAL_API_KEY required outside local dev"），异常在 handler 之前就抛出、被 CORSExceptionMiddleware 兜成 500。这是 Round-23 Patch 1 的 config fail-closed 与本文件矩阵第 3 行（prod+空 key→503）的**契约撞车**，属另一张卡；W4 

## tests/api/v1/endpoints/test_metadata_subject_mapping.py
- conversion: no_lifespan
- deps:
  - SubjectResolver (get_resolver DI)——5 个端点唯一的依赖对象 | breaks=False | app/api/v1/endpoints/metadata.py:117 / :748 / :767 / :797 / :823 全部为 `resolver: SubjectResolver = Depends(get_
  - app.core.vault_scope.resolve_vault_group_id —— GET /metadata 唯一的非 resolver 副作用调用 | breaks=False | app/api/v1/endpoints/metadata.py:138-143 调用（返回值被丢弃，只为 ContextVar 注入 + 409 fail-closed）；实现 app/core/vault_scope
  - MetricsMiddleware（app.add_middleware，每请求都跑） | breaks=False | app/main.py:779 注册；app/middleware/metrics.py:38-58 REQUEST_COUNT/REQUEST_LATENCY/CONCURRENT_REQUESTS 均为**模块级**
  - CORSExceptionMiddleware / EncodingValidationMiddleware / 四个 exception handler（404、422 断言的产出方） | breaks=False | app/main.py:757/:762 注册；EncodingValidationMiddleware.dispatch app/main.py:600-631；CORSExceptionMiddleware.disp
  - lifespan 装配的全部进程内对象（alert_manager/set_alert_manager、mastery_engine、resource_monitor、prompt_registry、episode_worker、vault_index_orchestrator） | breaks=False | app/main.py:134 `app.state.alert_manager` / :252-254 `app.state.mastery_engine` 等；反向证据：`grep -n "app.state|req
- risks: ⛔ **`test_metadata_group_id_format`(:308-315) 是存量红，别记到本改造头上**。它断言 `data["group_id"] == "math54:线性代数"`，实际产出 `vault:canvas_vault:math54:线性代数`。这是**无条件**失败、与 lifespan 无关：app/services/subject_resolver.py:201-205 `_make_group_id` 恒为 `f"{build_vault_group_id(_vid, subject_id=subject)}:{sanitize_subject_name(canvas_name)}"`，而 app/core/subject_config.py:250-254 里 `base = f"vault:{sanitized_vault}"` 是**唯一**返回路径（vault_id 为空只会 `raise ValueError`，不会返回无前缀值）。所以没有任何运行时状态（含起不起 lifespan、settings.vault_id 取什么值）能让它等于断言值。测试写于 8222daef「test: add 38 test files」批量补测时，用的是 Phase A0.5-N 之前的旧三段格式。改造 PR 里应原样保留这条红，或另立卡改断言为

## tests/test_deep_monitoring.py
- conversion: no_lifespan
- deps:
  - resource_monitor 后台采集（main.py:116-117 get_default_monitor() + start_background_collection(interval_seconds=5.0)） | breaks=False | /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/app/api/v1/endpo
  - prometheus 指标注册（canvas_agent_* / canvas_memory_* / canvas_resource_*） | breaks=False | /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/app/api/v1/endpo
  - MemoryService 预热 / Neo4j 连接（lifespan 连 settings.NEO4J_URI=bolt://localhost:7691 + FULLTEXT INDEX DDL） | breaks=False | /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/app/api/v1/endpo
  - alert_manager（set_alert_manager 全局 + app.state.alert_manager，main.py:125-137）/ mastery_engine / prompt_registry / episode_worker / vault_index_orchestrator | breaks=False | /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/app/api/v1/endpo
- risks: module 级 fixture + 全局单例交叉污染（这是本文件最实的坑，且**不是本文件能单独解决的**）：health.py:142-175 的 Neo4j 探针读的是 `get_neo4j_client()` 进程级单例。本文件单独跑时该单例是新建的 initialized=False，零连 7691；但若同一 pytest 进程里**先**跑了别的（尚未改造的）测试模块把该单例 initialize() 起来了，`is_real_neo4j` 为真，本文件的 test_health_endpoint_still_works 会真的对 7691 发 `RETURN 1 AS ping`（health.py:158）。所以「本文件零连 7691」只在本文件独立/全量改造完成后成立；建议本卡额外加一道会话级连接哨兵，别只靠逐文件改造声明零连。 | fixture 退出用 `app.dependency_overrides.clear()`（:40）而非 pop 自己那把 key——module teardown 时会连带清掉别人的 override。这是**既有**行为、本次不放大，但如果后续把 no_lifespan 的还原逻辑也挂在这里，要保证 no_lifespan 的 __exit__ 在异常路径下也执行（用 contextmanager 的 finally，别用裸赋值

## tests/unit/test_subjects_group_isolation.py
- conversion: no_lifespan
- deps:
  - resource_monitor 后台采集（app/main.py:116-117 get_default_monitor().start_background_collection） | breaks=False | app/api/v1/endpoints/subjects.py:105-153（list_subjects 全函数体：只有 _resolve_read_group_params + get_neo4j_client()
  - alert_manager（app/main.py:134 app.state.alert_manager + :137 set_alert_manager 模块级全局） | breaks=False | app/api/v1/router.py:493-501（subjects_router 的 include_router 无 dependencies=）+ app/api/v1/endpoints/subjects.
  - mastery_engine / signal_registry / fusion_engine（app/main.py:251-254 set_mastery_engine 全局 + app.state.*） | breaks=False | app/api/v1/endpoints/subjects.py:15-30（本模块全部 import：logging/uuid/datetime/typing/fastapi/get_neo4j_client/subj
  - Neo4j 连接 / MemoryService 预热 / FULLTEXT DDL / episode_worker 探活 / LanceDB recover_pending / EventBus recover_outbox / wikilink eager build / prompt_registry(:142-143) / schema_gate.verify(:341-343) | breaks=False | app/api/v1/endpoints/subjects.py:127 `neo4j_client = get_neo4j_client()` —— 该名字在 tests/unit/test_subjects_grou
  - 进程 active vault（409 fail-closed 判据来源） | breaks=False | app/core/vault_scope.py:160 `active_vault = get_current_vault_id()` + :166 `if requested not in active_vault_a
- risks: 【非隐患，但必须知道】本文件唯一的 TestClient 是内联的、函数级的，不存在 module 级 fixture 与 autouse 交织问题（对比卡文点名的 test_vault_scope_409.py）。改造面只有 1 行（:268）。 | 【顺序】`_patch_client(monkeypatch, stub)`（:266）当前在 `with TestClient(app)` 之前。若改成 fixture 形态，patch 会落到 client 之后——本用例安全（subjects.py:127 在函数体内取 client，不是 import 期绑定），但换成任何「模块导入期绑定 client」的端点就会失效，抄这个 fixture 到别的文件前要重验。 | 【exact-count 断言的脆弱面】:272 `len(stub.run_calls) == 1` 是精确等值。当前之所以成立，是因为 patch 打的是 `subjects_module.get_neo4j_client`（:58），而 lifespan 用的是 `app.clients.neo4j_client` 里的真函数——两条路不共享。若将来有人把 patch 提升为全局 patch `app.clients.neo4j_client.get_neo4j_client`，**开着 lifespan

## tests/unit/test_subjects_group_isolation.py
- conversion: None
- deps: NONE
- risks: 

## tests/unit/test_sync_exception_classification.py
- conversion: no_lifespan
- deps:
  - schema_gate.verify()（main.py:341-343 在 lifespan 内调用，缓存 CanvasSchemaGate._verified） | breaks=False | app/api/v1/endpoints/sync.py:107 `gate_reason = await get_canvas_schema_gate().block_reason()`
  - vault_identity_registry（现网注册表；lifespan 未装配，但端点会调） | breaks=False | app/api/v1/endpoints/sync.py:126 `await get_vault_identity_registry().assert_identity(...)`
  - sync_service 单例（lifespan 未装配） | breaks=False | app/api/v1/endpoints/sync.py:137 `service = get_sync_service()`
  - alert_manager / mastery_engine / episode_worker / vault_index_orchestrator / resource_monitor（lifespan 真正装配的那批） | breaks=False | app/main.py:134 `app.state.alert_manager=` / :137 `set_alert_manager()` / :251-254 `set_mastery_engine()`+`app
- risks: ⛔ 最重要 —— **本文件 6 个测试当前全红，且红因与 lifespan 无关**，改造前必须先记录这个基线，否则改完看到 6 failed 会被误判成"关 lifespan 把文件搞坏了"。实测（不跑 lifespan、复刻测试的 app+overrides+payload 直发一次请求）：`STATUS: 503`，`BODY: {"detail":"Internal API key not configured. Set INTERNAL_API_KEY env for production, or ALLOW_UNSAFE_DEV_AUTH_BYPASS=true for loopback dev."}`。根因在 app/security.py:109-142 的 Branch 2 fail-closed：`_dev_settings` 给的是 `INTERNAL_API_KEY=""` + `DEBUG=True`，该分支要求 **同时** `ALLOW_UNSAFE_DEV_AUTH_BYPASS=true`（实测 `os.environ.get(...)` 为 None，且 tests/conftest.py、tests/unit/conftest.py 均无 env 写入、无 pytest-env、无 backend/conftest.py）**且** `req

## tests/unit/test_vault_scope_409.py
- conversion: no_lifespan
- deps:
  - set_mastery_engine 全局 + app.state.mastery_engine / signal_registry / fusion_engine (main.py:236-254) | breaks=False | app/api/v1/endpoints/mastery.py:138-142
  - episode_worker.initialize_graphiti + start() + app.state.episode_worker (main.py:274-291) | breaks=False | app/api/v1/endpoints/tips.py:617,633
  - MemoryService pre-warm 单例 (main.py:161-167) + ensure_fulltext_index DDL (main.py:171-175) | breaks=False | app/api/v1/endpoints/memory.py:75
  - MemoryService pre-warm（chat.py 的**直接调用**面，dependency_overrides 覆盖不到） | breaks=False | app/api/v1/endpoints/chat.py:313
  - wikilink 图 eager build (main.py:299-314，读 live vault) | breaks=False | app/services/wikilink_context_service.py:390-409
  - schema_gate.verify() (main.py:340-345) —— /sync/batch 的前置门 | breaks=False | app/api/v1/endpoints/sync.py:107
  - LanceDB recover_pending / EventBus recover_outbox / cost_tracker / archive_scheduler / resource_monitor / alert_manager / prompt_registry / vault_index_orchestrator | breaks=False | app/api/v1/endpoints/sync.py:107
- risks: 【最高】/sync/batch 的 schema gate 在 resolver 之前跑，只关 lifespan 不够。sync.py:107 → schema_gate.py:102-103 会在请求期 lazy verify()，建 driver 打 7691 跑 SHOW CONSTRAINTS。断言不会变（verify 的 except 把失败吞成 None，只有 _verified is False 才 503），但『测试进程零连 7691』的验收会当场不成立。必须按 sketch 第 (3) 处 stub。 | 【最高】module 级 client + 函数级 patch 的时序错位。今天 lifespan 在 module fixture 建立时跑，处在**任何 `patch("app.config.get_current_vault_id")` 之外**；改造后 no_lifespan 什么都不做，于是所有 vault 解析首次发生在用例内的 patch 作用域里。这对本文件是好事（MemoryService 若在请求期初始化，`_recover_episodes_from_neo4j` 的 `require_read_group(None)`(memory_service.py:370-374) 正好能推导出 vault:active_vault 而不抛），但反
