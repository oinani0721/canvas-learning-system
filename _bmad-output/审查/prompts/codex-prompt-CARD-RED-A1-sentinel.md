# 独立审查请求 — CARD-RED-A1-sentinel（BATCH-2026-09-07-第十三批）

仓库根: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
分支: `card/u10-red-a`

---

## 一 背景

这是一个后端 FastAPI + pytest 的项目。本卡处理 `backend/tests/unit` 目录级跑里的 12 条红，并顺带落地一处 router 级鉴权。

**12 条红的失败身份不是断言，而是一道端口门的哨兵。** `backend/tests/conftest.py:153-172` 装了一个 `pytest_runtest_makereport` wrapper：如果某个用例期间发生过到现网 Neo4j 端口（7691/7687）的连接尝试并被门拦下，就把该用例的 `report.outcome` 改成 `"failed"`，并把哨兵文本拼到 `longrepr` 前面。所以这 12 条的失败正文首行是 `live Neo4j port connect attempted …`，中间没有断言 traceback。

**归属会随收集顺序漂移。** `app/clients/neo4j_client.py:2742-2746` 的 `get_neo4j_client()` 是进程级单例，`app/services/mastery_store.py:544-549` 的 `get_mastery_store()` 也是。单例的惰性初始化只在**第一次**触发时真的去连一次；连失败后 `_fallback_to_json()` 把它切成 JSON 降级态并置 `_initialized=True`，此后不再连。于是「谁先跑谁付账」——按 nodeid 逐条修会变成「换个顺序又红到别人头上」。本卡开工实测：五个文件换一种收集顺序，服务级那条红就从 `test_mock_degradation_transparency.py` 换成 `test_review_mode_support.py`（存档 `five-open-order-a-*.txt` / `five-open-order-b-*.txt`）。

**鉴权那半的依据。** `app/main.py:554-568` 的 OpenAPI securitySchemes 文案（:561）早就写着 `/chat/*, /sync/*, /system/*` 在生产模式受内部 API key 保护，但 `app/api/v1/system.py` 全 router 此前只有 `/config`（:782）与 `/test-llm`（:849）两个端点真的挂了依赖。本卡在 `system.py:28` 的 `APIRouter(...)` 上加 router 级 `dependencies=[Depends(require_internal_api_key)]`（与 `app/api/v1/endpoints/chat.py:48` 同形）+ `responses={403, 503}`，让实现追上文档。

**前置说明**：本卡有一个「通告门」——另一条车道（W4-7）的成果进候选树后本卡要 merge 再复判。**截至本次审查，通告未到，本卡处于阶段一**（未 merge，起点 = U10-C 末 commit `0acea4e3`）。

---

## 二 作者自述，请独立核对

1. **每条红都定位到了真连点，并且打桩打在「会真连的那一层」，未放宽端口门、未改 W4 门文件。**
   - 族 A（9 条端点族）真连点 = `app/api/v1/system.py:53-59` 的 `_check_neo4j`（每请求新建 driver）；打桩 = 在两个测试文件里 patch `app.api.v1.system._check_neo4j`。
   - 族 B（1 条 kg）真连点 = `app/api/v1/endpoints/kg_health.py:39-44`（端点函数体内 local import 的 driver）；打桩 = patch `neo4j.AsyncGraphDatabase.driver`。
   - 族 C（1 条服务级）真连点 = `app/clients/neo4j_client.py:523` 的 `health_check()`；打桩 = patch `Neo4jClient.health_check` 返回 `False`。
   - `backend/tests/conftest.py`、`backend/tests/support/live_port_guard.py`、`guard_plugin.py` 一字未改；`ALLOWED_TEST_PORTS` 未动；7691 未进任何白名单。
2. **换收集顺序两次都绿**：`five-after-order-a-*.txt` 与 `five-after-order-b-*.txt` 的 FAILED 集合都为空，哨兵串计数都为 0。
3. **`system.py` 只改 router 构造一行（现为多行的等价写法），端点函数体零改动**：没有动 `_check_neo4j`，没有动任何 `@router.get/post` 下面的函数体，没有顺手修该文件既有的 7 条 pyright 报错。
4. **调用方清点支持「加鉴权不会打断线上探针」**：容器 healthcheck 打的是 `/api/v1/health`（`docker-compose.yml:228` + `app/api/v1/endpoints/health.py`，无 prefix），不经 `/system` router。
5. **`backend/openapi.json` 由与 pre-commit hook 同一支脚本再生**（`scripts/spec-tools/check-openapi-drift.py --write`），未手改。

---

## 三 请按重要性排序回答的问题

1. **族 C 的打桩是不是只是把那一次连接推迟给了别的用例？** 作者的论证是：patch `health_check` 之后单例照样被建出、照样落进 `_fallback_to_json()` 的降级终态，所以进程终态与打桩前逐项相同，债是「付清」不是「转移」；而 patch 单例 accessor 才会移债。请独立核对这条论证，特别是 `_initialize_neo4j_driver` → `_fallback_to_json` → `_initialize_json_fallback` 这条链上 `_use_json_fallback` / `_initialized` 两个标志的赋值时机（`app/clients/neo4j_client.py:378-470`、`:554`）。
2. **router 级鉴权会不会让装机期端点在还没有 key 的时候不可用？** 特别是 `POST /api/v1/system/setup-wizard`（`system.py:456`）与 `GET /api/v1/system/health` —— 这两个在「用户第一次装好、还没配 key」的场景下会被 403 挡住。这是产品面风险，作者已登记但未处置，请判断登记是否足够、还是应当在本卡处理。
3. **新增的鉴权行为断言在依赖被摘掉时真的会变红吗？** 见 `tests/unit/test_startup_health_check.py` 的 `TestSystemRouterAuth` 三条。请判断它们是否可能在「router 根本没挂依赖」的情况下也绿（例如 fixture 自身的 settings 覆盖导致落到别的分支）。
4. **单例的首触者换人之后，哪些原本绿的用例可能开始红？** 作者的收工全量跑显示对 202 条红基线的 diff 只有 12 条 `<`、零 `>`，但请判断这个判据是否足以支撑「没有把债推给别人」。
5. **`backend/openapi.json` 的 security 段变化是否与插件侧实际发出的请求一致？** 注意：per-operation 的 `security` 引用的方案名是 `APIKeyHeader`，而 `components.securitySchemes` 里定义的名字是 `InternalApiKey` —— 作者实测这个不一致在本卡改动**之前就存在**（`/chat/*`、`/sync/batch`、`/system/config` 三处），本卡只是把同一模式扩大到 `/system/*` 其余端点，按「禁顺手修存量」登记未修。请判断这个处置是否恰当。

---

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- 一句话结论
- `file:line`（用当前树上的真实行号）
- 依据（读到的代码或存档文件里的具体内容）

若某条自述你核对后认为不成立，请直接指出并给出你的判断依据。

---

## 五 边界（请不要评的）

- 不评那道端口门本身的设计（`backend/tests/support/live_port_guard.py` / `backend/tests/conftest.py:153-172`）——那是另一条车道的地盘，本卡只读并依赖它。
- 不评 `backend/tests/support/authed_client.py`、`backend/tests/unit/conftest.py`、`test_system_endpoint_auth.py`、`test_sync_batch_auth.py`、`test_agent_templates_smoke.py`、`app/services/agent_service.py` 的改动——分属别的卡。
- 不评 `app/api/v1/system.py` 既有的 7 条 pyright 报错（属另一张卡的清理面，本卡明令不动）。
- 不评 `_archive/` 与 `_bmad-archive/` 下的任何内容。
- `backend/tests/contract/**` 本卡只跑不改，不评其内容。

---

## 六 最小读取面

- 本卡 diff 全文：`git diff 0acea4e3 -- . ':(exclude)_bmad-output'`
- `backend/app/api/v1/system.py`：`:1..:50`、`:60..:95`、`:260..:285`、`:388..:410`、`:786..:806`、`:855..:870`
- `backend/tests/conftest.py:150..:175`
- `backend/app/clients/neo4j_client.py:378..:470`、`:501..:536`、`:545..:560`、`:2740..:2800`
- `backend/app/api/v1/endpoints/kg_health.py:28..:82`
- `backend/app/security.py:88..:165`
- 六个改动测试文件的 fixture 段
- `_bmad-output/审查/evidence-red-a1-sentinel/*.txt`，重点：
  - `sentinel-triage-20260909.txt`（12 条逐条处置表）
  - `five-open-order-a-*.txt` / `five-open-order-b-*.txt`（漂移证据）
  - `five-after-order-a-*.txt` / `five-after-order-b-*.txt`（收工双序）
  - `unit-open-*.txt` / `unit-after-*.txt` / `red-diff-after-*.txt`
  - `pyright-multiset-diff-p1-*.txt`
  - `contract-full-before-INCOMPLETE.txt` + `contract-sys-before-*.txt` / `contract-sys-after-*.txt`
- 验收单：`_bmad-output/验收单/UAT-CARD-RED-A1-sentinel-2026-09-09.md`
