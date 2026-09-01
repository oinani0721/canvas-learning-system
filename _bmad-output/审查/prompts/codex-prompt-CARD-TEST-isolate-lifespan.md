# Codex 审查提示词 — CARD-TEST-isolate-lifespan

[BATCH-2026-09-01-第八批 / CARD-TEST-isolate-lifespan]

> **round ≥ 2 附注**：round-1 裁定 FAIL（1B/11H/7M/1L），全部 1B+11H 与 6 条 MEDIUM 已整改（处置表见验收单「Codex round-1 处置表」），1 条登记不修（test_health 响应时间阈，ATTEMPTS=0 证实与 Neo4j 无关）。本轮请：(a) **核验每条已修 finding 的修复真实有效**（不是表面糊弄）；(b) 对整改引入的**新代码**做与 round-1 同强度的对抗审查（guard 重写 / guard_plugin / 负控重写 / AST 作用域链重写 / sha 门子壳 / conftest 早期装门与别名 patch）；(c) 上一轮已放行的维度如无新证据不必重查。输出格式同前。

你是独立的对抗性审查员。审查对象是 card/w4-micro 分支上 CARD-TEST-isolate-lifespan 的落地改动（`git log` 中带本批次标记的 commit；工作树即审查现场）。请先读本验收单：`_bmad-output/审查/CARD-TEST-isolate-lifespan-验收单.md`。

## 本卡目标（验收的对照物）

给「用 `app.main.app` 起真实 lifespan 的端点测试」补隔离，并加「测试进程运行时零连现网 Neo4j(7691/7687)」硬门。落地物：

1. `backend/tests/support/lifespan.py` — `no_lifespan(app)` / `lifespan_lite(app)` 基元（换 `app.router.lifespan_context`，退出恢复）。
2. `backend/tests/support/live_port_guard.py` — socket.connect/connect_ex 包装门（7691/7687 fail-closed）+ 每用例结账哨兵 + uvloop 自证。
3. `backend/tests/conftest.py`（根）— session 级 autouse 门 fixture + `pytest_runtest_protocol`/`makereport` 接线 + client fixture 默认 lifespan-free + middleware bug_tracker 单例的 log_path 重定向到 session tmp。
4. 13 个测试文件改造：tests/api 3 + tests/unit 8 + 根级 2（`no_lifespan` 包裹 + 请求期连接点打桩：schema_gate×3 处、get_canvas_service/get_memory_service DI 覆盖、chat.get_memory_service 函数级 patch、mastery.get_mastery_store patch）。
5. `backend/scripts/lifespan_isolation_runtime_sha.sh` — 三个运行时文件 sha 门。
6. `backend/scripts/lifespan_isolation_negative_control.py` — 负门（原地摘 no_lifespan → 指定文件全 FAIL 且原因=live port connect + sha 不变 + 逐字节还原）+ 内置 AST 门（scope: tests/api、tests/unit、test_debug.py、test_deep_monitoring.py、conftest.py；期望 0 违规）。

## 重点审查面（按优先级）

1. **socket 门的绕过面**：
   - uvloop：门在 `pytest_configure` 装、session fixture 自证 policy 非 uvloop 且 `sys.modules` 无 uvloop——能否被绕过？（venv 装了 uvloop 0.22.1，全仓零引用）
   - 线程：TestClient 的 anyio portal 线程、`ThreadPoolExecutor`、裸 `threading.Thread` 里发起的 connect 是否都过包装？（类属性 patch 理论上全进程可见，请证伪）
   - 子进程：`subprocess` 起的 python 进程不受门管——门 docstring 已声明为不比什么。除此之外是否还有本进程内的连接路径被漏掉（SSL wrap 时的重连、`socket.create_connection`、`asyncio.open_connection`、httpx/requests 连 7691）？
   - `connect_ex` 抛 RuntimeError 而非返回 errno——是否有调用方靠返回值探活会被这个决定改变行为？
   - 门装的时机（pytest_configure）与卸载（pytest_unconfigure）之间，`_orig_connect` 保存/恢复的幂等性。
2. **no-op lifespan 是否让测试「测了个寂寞」**：13 个文件逐文件核对其被测端点仍走真实 router、断言面没有从「真测」退化成恒真/恒 503/恒空。特别注意：
   - `tests/unit/test_vault_scope_409.py` 的 module 级 client + 409 门语义是否被 no_lifespan/DI 覆盖破坏；
   - `tests/test_deep_monitoring.py` 断言 /metrics 含 resource 指标——resource_monitor 后台采集不再启动后这些断言是否恒真（prometheus 指标族在 import 期注册、有无 sample 是否影响 exposition 文本）；
   - `tests/unit/test_mastery_api.py` 新增的 `get_mastery_store` patch 是否改变了任何断言路径（此前 stub 是死桩、真 store 连库——本卡改为真桩，基线 4 个失败用例因此转绿）。
3. **路径前缀 advisory 是否构成静默旁路**：`tests/integration/`、`tests/e2e/` 按路径豁免只记不拦。检查 `EXEMPT_PATH_PREFIXES` 的匹配逻辑（nodeid 相对化 + 绝对路径兜底）能否被放到别处的文件意外命中，或 integration 文件放错目录后逃过 marker 检查。
4. **根 conftest 改动的影响面**：`client` fixture 默认 lifespan-free 后，靠根 client 的其它文件（test_health/test_cors/test_rollback_*/regression/test_production_bugs 等）是否有测试实际依赖 lifespan 产物；bug_tracker log_path 重定向是否影响任何读取该文件的测试；`isolate_dependency_overrides` autouse fixture 与新的门 fixture 的顺序交互。
5. **负门与 AST 门**：负门变异锚点唯一性检查、junitxml 解析对「红了但原因不对」的判定、EXIT 还原的完备性（KeyboardInterrupt 路径）；AST 门的绑定解析（函数级 import、局部 FastAPI() 赋值、正例文件）是否会把正例误报或漏报。
6. **哨兵的假阴面**：`pytest_runtest_makereport` 只在 `call`/`teardown` 结账——setup 期的拦截（fixture 里的 connect）是否可能漏结账？`fixturedef` 阶段（finalizer 里）发起的 connect 归属谁？

## 已知的、不要重复报告的事（验收单已登记）

- 基线（7692 override）19 failed/374 passed vs 完成后同命令的 passed 数不等——两个环境本质不同（7692 真库 + lifespan vs 零库 + 无 lifespan），验收单以「comm 对账零新增失败 + 逐条解释翻转」为判据，已在验收单给出翻转清单。
- integration/e2e 10 文件只登记不改造是卡文明确裁决。
- `app/main.py`、exam/verification/memory_service、CI 白名单、tests/regression/conftest.py 不在射程，未改。

## 输出格式

逐条 finding：`[BLOCKER|HIGH|MEDIUM|LOW] <file:line> <问题描述> <建议修法>`。没有 finding 的维度也要给出「查过什么、为何放行」。最后给总体裁定：PASS / FAIL（含 BLOCKER 或 HIGH 即 FAIL）。
