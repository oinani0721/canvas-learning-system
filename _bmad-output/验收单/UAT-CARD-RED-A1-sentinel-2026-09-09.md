# UAT — CARD-RED-A1-sentinel

> 批次: `BATCH-2026-09-07-第十三批` · 车道 `card-u10-red-a`（分支 `card/u10-red-a`）
> 卡文: `.../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U10-D.md`
> 起点 `U0` = `0acea4e3`（U10-C `CARD-RED-A1-auth` 末 commit）
> **阶段: 一（通告未到）** —— 截至本单落笔，主 session 的「U7-C W4-7 已进候选树 `<sha>`」通告**未收到**，
> 故 **未 merge 候选树**，`P` / `M` / `$M^2` 四元组中只有 `U0` 有值；判据区间 = 单段 `U0..HEAD`。
> 证据目录: `_bmad-output/审查/evidence-red-a1-sentinel/`

---

## 0 一句话

`tests/unit` 里那 12 条红的失败身份是**端口门哨兵**（不是断言）；本卡按「哪条路径会真连」在**测试侧**打了三处桩，
12 条全消、零新增红；同时把 `system.py:28` 的 router 级鉴权补上，让实现追上 `main.py:561` 早就写下的文案。

---

## 1 完成条件逐条

### (a) 第 0 分钟 + 通告门

| 项 | 实测 | 存档 |
|---|---|---|
| `pwd` | `.../worktrees/card-u10-red-a` ✅ | `minute0-20260909T160008.txt` |
| 分支 | `card/u10-red-a` ✅ | 同上 |
| `HEAD` | `0acea4e3a6a62501319c8144a83b9f58cbf310a2` = U10-C 末 commit ✅ | 同上 |
| `git status --porcelain` | 只有新建的 evidence 目录（未跟踪）✅ | 同上 |
| `backend/.env` | EXISTS ✅ | 同上 |
| `backend/.venv/bin/pytest` | 存在 ✅ | 同上 |
| **通告门** | **未收到 W4-7 通告 ⇒ 阶段一，未 merge，未对 12 条之外的任何红下结论** | 本单 §5 |

**⚠️ 阶段二未执行**：`P` / `M` / `"$M^2"` 三个值本卡**没有**（不是「填了但没写」）。
主 session 抽本卡 diff 面时按**单段** `git log --format=%h --no-merges 0acea4e3..HEAD` 即可，
⛔ 不要按卡文 (k)② 的两段并集口径抽——那是阶段二才成立的写法。

### (b) 开工基线 + 12 条自证

- **① `tests/unit` 目录级开工**：`unit-open-20260909T160022.txt`
  - 汇总行 `= 132 failed, 4795 passed, 48 skipped, 135 warnings, 29 errors in 278.88s (0:04:38) =`；末行 `rc=1`
  - nodeid 口径红 **161** 条；对 202 基线 diff（`red-diff-open-20260909T160022.txt`）：**只有 `<` 行 41 条，零 `>` 行** ✅
  - 41 条 `<` 的归因（如实分两类）：
    - **32 条 = U10-C 消掉的**：`test_chat_endpoint.py` 16 + `test_study_question_deep_mode.py` 8 + `test_sync_exception_classification.py` 6 + `test_enrich_context_vault_isolation.py` 2
    - **9 条 = 环境差异，非 U10-C 亦非本卡**：`test_agent_templates_smoke.py` 全部 9 条（该文件属 U10-B 面，本车道树上绿而 202 基线树上红；本卡**未证明**其成因，登记移交）
- **② 12 条自证**：`card12-presence-open-20260909T160022.txt` —— 卡文 12 条**逐条 PRESENT**；
  且本轮红集里这五个文件的条目**恰好只有这 12 条**（`five-files-red-open-20260909T160022.txt`），无多无少 ⇒ **本轮未漂移**。
- **③ pyright 多重集基线**：`pyright-base-20260909T161545.txt` → **7 errors**（与卡文「存量 7 条」一致）
- **④ `tests/api` 目录级**：见 (f) / §二.9 —— open 与 after 均 `268 passed`
- **⑤ merge 后重跑**：**不适用**（阶段一）

### (c) 鉴权裁决落地

`backend/app/api/v1/system.py:28` 由 `APIRouter(prefix="/system", tags=["System"])` 改为多行等价写法，新增：
- `dependencies=[Depends(require_internal_api_key)]`（与 `endpoints/chat.py:48` 同形；`Depends` 与 `require_internal_api_key` 改前已在 `:19` / `:23` import，**未新增 import**）
- `responses={403: …, 503: …}`（文案抄 `:783-788` 同形）

**端点函数体零改动**，`_check_neo4j` 一字未动，7 条 pyright 存量未修。

**落地前复跑的调用方 census（三个数按卡文口径）**：

| 口径 | 实测 | 说明 |
|---|---|---|
| `grep -rn '/api/v1/system\|/system/' backend/tests/unit` 命中行 | **28** | conftest 1 / auth 13 / startup 10 / health_detailed 3 / config_drift 1 |
| 其中**非调用点** | **6** | `tests/unit/conftest.py:39`（注释）、`test_system_endpoint_auth.py:2/:107/:156`、`test_startup_health_check.py:22/:53`（docstring） |
| 真实 HTTP **调用行** | **22** | auth 10 + startup 8 + health_detailed 3 + config_drift 1 |

> **⚠️ 卡文事实修正 ①**：卡文 §〇 写 `tests/unit/conftest.py:36` 是那条注释，实测在 **`:39`**。三个数（28/6/22）本身实测吻合。

**非测试调用方 census（本卡实测，⚠️ 与卡文不符，如实列全）**：

| # | 位置 | 端点 | 改前是否已受鉴权 | 本卡后 |
|---|---|---|---|---|
| 1 | `frontend/frontend/src/lib/api-client.ts:102` | GET `/system/health` | 否 | **新受影响 → 403** |
| 2 | `frontend/frontend/src/lib/api-client.ts:123` | POST `/system/config` | 是（:782） | 不变 |
| 3 | `frontend/frontend/src/lib/api-client.ts:160` | GET `/system/llm-stats` | 否 | **新受影响 → 403** |
| 4 | `frontend/frontend/src/lib/api-client.ts:180` | POST `/system/test-llm` | 是（:849） | 不变 |
| 5 | `frontend/src/services/api-client.ts:284` | POST `/system/config` | 是 | 不变（该文件 `:182` 会注入 key） |
| 6 | `frontend/src/services/api-client.ts:319` | POST `/system/test-llm` | 是 | 不变 |
| 7 | `frontend/src/services/docker-manager.ts:173` | GET `/system/health` | 否 | **新受影响 → 403**（裸 `fetch`，只带 `Content-Type`） |

> **⚠️ 卡文事实修正 ②**：卡文称非测试调用方「只剩两处淘汰 Tauri 前端」。实测 `/api/v1/system/*` 共 **7 处**调用点，
> 其中**新受影响的是 3 处**（health ×2 + **llm-stats ×1，卡文漏列**）。结论方向不变——**三处全在两个已淘汰 Tauri 前端**
> （`frontend/frontend/` 与 `frontend/src/`），`frontend/obsidian-plugin/src` 与 `canvas-vault/.claude` **零命中**（实测 rc=1）。

**「不会打断线上探针」的依据（实测）**：`docker-compose.yml:228` 的 backend healthcheck 是
`curl -sf http://localhost:8001/api/v1/health`，该路径来自 `app/api/v1/endpoints/health.py` 的无 prefix router
（`router.py:68-72` include），**不经** `/system` router（其 prefix 为 `/system`）⇒ 容器 liveness 不受影响。

### (d) 受影响端点测试改走 `authed_client`

| 文件 | 调用行数 | 改法 |
|---|---|---|
| `test_startup_health_check.py` | **8** | 本地 `client` fixture 改为 `return authed_client`（显式 import，⛔ 未改 `authed_client.py`） |
| `test_health_detailed.py` | **3** | 同上 |
| `test_config_drift.py` | **1** | 类内 `client` fixture 同上 |
| 合计 | **12** | = §(c) 的 22 调用行 − auth 文件那 10 处 |

`test_system_endpoint_auth.py` **未动**（U10-E 面）；`test_kg_health.py` **不需要** `authed_client`（`kg_health_router` 不落鉴权）。
**断言一行未改。**

> **⚠️ 语义收窄如实记录**：`test_health_detailed.py` / `test_config_drift.py` 原 fixture 是
> `TestClient(app, raise_server_exceptions=False)`，`authed_client` 用的是默认 `True`。
> 这四条用例走的都是端点的正常返回路径（组件异常在 `_probe_with_timeout:350` 就被吞成 ComponentHealth），
> 收工实测全绿；但「服务端异常被转成 500 响应」这一行为本卡**不再覆盖**。

### (e) 12 条逐条处置

完整表见 **`evidence-red-a1-sentinel/sentinel-triage-20260909.txt`**（每行：nodeid | 真连点 file:line | 处置 | 依据）。

三族真连点与打桩层：

| 族 | 条数 | 真连点 | 打桩层 | 为什么是这一层 |
|---|---|---|---|---|
| A 端点·system | 9 | `system.py:53-59` `_check_neo4j`（每请求新建 driver） | patch `app.api.v1.system._check_neo4j` | 调用点 `:258-260` / `:381` 都在**调用时**从模块全局解析该名字；`setup_wizard:478` 内部再调 `startup_health_check` ⇒ 一处覆盖三族用例 |
| B 端点·kg | 1 | `kg_health.py:39-44` 端点函数体内 driver | patch `neo4j.AsyncGraphDatabase.driver` | 该名字是**函数体内 local import**，模块全局里没有 ⇒ 只能 patch 源模块属性 |
| C 服务级 | 2 | `neo4j_client.py:523` `health_check()` | patch `Neo4jClient.health_check` → `False` | 见下 |

**族 C 为什么不 patch 单例 accessor（本卡最关键的一处判断）**：
`get_neo4j_client()` / `get_mastery_store()` 是**进程级单例**。把它们摘掉，本用例期间单例根本不被建出来，
那唯一一次真连不是被消掉、而是被推给进程里**下一个**调用方 —— 哨兵换个 nodeid 照样报出来。
改 patch `health_check` 则是把债**付清**：单例照建，`_initialize_neo4j_driver` 照走
`_fallback_to_json()` ⇒ `_use_json_fallback=True` + `_initialized=True`（`neo4j_client.py:467`），
**决定「还会不会再连」的那两个标志与打桩前完全一致，只少了那一次 socket**
（⚠️ 不是「进程终态逐项相同」—— 真实失败路径 `:534` 会写 `_last_health_check` 时间戳、`AsyncMock` 不会；
该字段不参与再连判定，Codex r1 LOW-3 更正过我这处措辞）。返 `False` 而非抛，因为真实 `health_check:529-535`
本来就把异常吞成 `False`。收工日志可证该路径被走到：`WARNING app.clients.neo4j_client:neo4j_client.py:408 Neo4j health check failed during initialization`。

**归属漂移的实证（开工期，同一份代码只换收集顺序）**：

| 收集顺序 | 服务级红的 nodeid | 另一文件 |
|---|---|---|
| order-a（mock 在前） | `test_mock_degradation_transparency::test_mock_mode_logs_warning` | `test_review_mode_support.py` 全绿 |
| order-b（review 最前） | `test_review_mode_support::test_fresh_mode_parameter_accepted` | `test_mock_degradation_transparency.py` 全绿 |

存档 `five-open-order-a-20260909T160624.txt` / `five-open-order-b-20260909T160917.txt`（两跑都是 `11 failed`，族 A/B 十条不变）。
⇒ 这就是「⛔ 不按 nodeid 逐条修」的实证依据。

**⛔ 未做的事（逐条）**：未放宽哨兵、未把 7691 加进 `ALLOWED_TEST_PORTS`、未改 `tests/conftest.py` /
`live_port_guard.py` / `guard_plugin.py`、未改任何生产降级逻辑、未 skip / 未 xfail。
`app/api/v1/endpoints/kg_health.py` **一字未改**（裁决(甲)）—— 该端点仍无鉴权、真连点仍在，只是单元测试进程不再拨 7691。

### (f) 收工统一裁判

> ⚠️ **本节有两轮存档**：`*-after-*` 是 `ruff format` **之前**跑的，`*-final-*` 是**定稿态**（(i-1) 格式化之后）跑的。
> **以 `*-final-*` 为准**；两轮逐条对照见本节末尾（`same_rc=0`）。

#### 定稿态（`unit-final-20260909T181456.txt` / `five-final-order-a|b-*`）

| 判据 | 实测 |
|---|---|
| `tests/unit` 汇总行 | `= 120 failed, 4810 passed, 48 skipped, 135 warnings, 29 errors in 262.29s =`；末行 `rc=1` |
| 红条数 | **149** |
| 对 202 基线 `>` 行 | **无输出**（`red-diff-final-*.txt`） ✅ |
| 与格式化前收工红集对照 | `diff` **`same_rc=0`** ⇒ 逐条相同 ⇒ 格式化是纯排版，未改行为 ✅ |
| 五文件 order-a | `72 passed`，FAILED **0**，哨兵串计数 **0**，`rc=0` ✅ |
| 五文件 order-b | `72 passed`，FAILED **0**，哨兵串计数 **0**，`rc=0` ✅ |

#### 格式化之前那一轮（保留，作为「格式化未改行为」的左端）

`unit-after-20260909T163206.txt`
- 汇总行 `= 120 failed, 4810 passed, 48 skipped, 135 warnings, 29 errors in 282.20s (0:04:42) =`；末行 `rc=1`
- 对 **202 基线** diff（`red-diff-after-20260909T163206.txt`）：**零 `>` 行** ✅
- 对 **开工** diff（`red-diff-open-vs-after-20260909T163206.txt`）：**`<` 12 行、`>` 0 行**；
  且 `diff` 逐条比对证明消掉的**正是卡文那 12 条，无多无少**（本单 §1(b)② 的 nodeid 清单）
- 计数变化：红 161 → **149**（−12）；passed 4795 → **4810**（+15 = 修好的 12 条 + (g) 新增的 3 条）
- **本卡引入的 `>`（哨兵 / `/tmp` 环境告警 / 新 403）= 0** ✅

`tests/api` 目录级：`api-open-…164338.txt`（268 passed）vs `api-after-…163754.txt`（268 passed）⇒ diff 空（`red-api-diff.txt`，`api_diff_rc=0`）✅

#### (f-补) `tests/contract` —— ⚠️ 那道门对本卡要验的性质是**瞎的**，另补带负控的探针

卡文 §二.8 要求用 `tests/contract/test_openapi_contract.py` 做 before/after，证明「新的 403 没有变成 schema 里未声明的状态码」。**实测这道门做不到这件事**：

| 事实 | 实测 |
|---|---|
| 全量 207 个 operation | 29 分钟只跑完约 8 条（≈3.6 min/op），全量外推 **≈12 小时** ⇒ 未跑完（`contract-full-before-INCOMPLETE.txt`） |
| 定向 4 个 operation 的 **before**（树态还原到 `U0`） | **4 条全红**，用时 34:09（`contract-sys-before-20260909T165510.txt`） |
| before 的**拒因** | 4 条全是 `hypothesis.errors.DeadlineExceeded`（16–19s vs 10s 上限）；`status_code_conformance` 在整份存档里出现 **0 次**；哨兵串出现 418 次 |
| 控制组 | `POST /system/config`（改前**已**受鉴权）同样红 ⇒ 红与本卡无关 |

⇒ **before/after 都红在同一个与 schema 无关的原因上，差集为空也证明不了本卡想证的事**（门绿/门红都不锁这条性质）。如实登记，不假装这道门通过了。

**after 实测（`contract-sys-after-20260909T173229.txt`，35:45）**：同样 `4 failed`，nodeid 与 before **逐条相同**
（`red-contract-sys-diff.txt`，`contract_diff_rc=0` ⇒ **diff 为空，零新增红**）；拒因分布也相同
（`DeadlineExceeded` 8 次、`status_code_conformance` **0** 次）。
⇒ 本卡**没有**把 contract 弄红，但这只是「没变坏」，不是「证明了没引入未声明状态码」。

**但这一跑意外给出两条真正有用的旁证**（都是 before/after 逐项可比的）：

| 观测 | before | after | 含义 |
|---|---|---|---|
| 哨兵串里 logger = `app.api.v1.system`（即 `_check_neo4j` 的吞点）的条数 | **2** | **0** | 鉴权依赖**真的**在端点函数体之前拦住了，`/system/*` 在这套 harness 下也不再拨 7691 |
| 端口门总账 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` | **207** | **199**（−8） | 同上，减少量与两个端点各 ×N 次请求吻合 |
| `/system/startup-check` / `/system/config-check` 实际返回码 | `200` | **`503`** | 见下 |
| 其余约 400 条哨兵串的 logger | `app.services.schema_gate:92` / `app.main:291` | 同 | **不是** /system 端点产生的，属别的机制，本卡不动 |

**⚠️ 一条本卡差点判错的事实：在 schemathesis 那套 harness 下，新依赖返回的是 `503` 而不是 `403`。**
原因：contract 测试用的是**真实 `backend/.env`** 的 settings（不是 `authed_settings_override`），
其 `INTERNAL_API_KEY` 为空 + `DEBUG=True` ⇒ 落 `security.py:110-142` **Branch 2**（`TestClient` 的
client host 恒为 `"testclient"`，拿不到 loopback bypass）。
⇒ **这正是卡文要求「必须同批声明 403 **和** 503」的实证**：只声明 403 的话，这四条会因「返回了 schema 里
没声明的 503」被 `status_code_conformance` 打红。
⚠️ **但「该检查出现 0 次」推不出「两个码都声明到位」**（Codex r1 LOW-4② / r2 LOW-5 两次点到）：
存档里没有该检查的结论，只能说明**它没有报告失败**，不能反推它跑过并通过。
「503 已声明」这一点的真正依据在 `backend/openapi.json` 本身（16 个 `/system/*` operation 的
`responses` 都含 `503`，见 §1(f-补) 探针输出的 `declared=` 列），不在这份 contract 存档里。

**补的判据：`status_conformance_probe.py`（本目录，带负控）** — 存档 `status-conformance-after-20260909T173152.txt`
（⚠️ 文件名用本机时区 17:31，存档正文里日志行的 `timestamp` 是 UTC 09:31，同一次跑）

| 项 | 结果 |
|---|---|
| 覆盖面 | `app.openapi()` 里全部 **16** 个 `/api/v1/system/*` operation（不是抽样） |
| 正判 | 不带 key 各发一次请求 ⇒ **16 个全返 403**，且 **16 个全都在自己的 `responses` 里声明了 403** ⇒ 未声明的返回码 **0** 个 |
| **负控 A** | 把 spec **副本**里每个 operation 的 `403` 声明摘掉后重判 ⇒ 摘掉 16 个、**仍判 PASS 的 0 个** ⇒ 判定函数确实在读声明 |
| **负控 B**（r1 后新增，更强） | 在**真实 `app.routes`** 上删掉 403 声明 + 清 `app.openapi_schema` 缓存 + **原样重跑观测** ⇒ 16 个 operation **全部判 FAIL**，且**键集与正判逐条相同**（r2 LOW 后收紧，原先只比条数）⇒ 「真的缺声明时这套探针会红」 |
| **还原自证** | r2 LOW 指出原写法（只问「有没有未声明码」）**对空观测会误报 PASS**（Codex 用受控反例复现）。现改为逐条比对 `(method,path)→(状态码,声明集合)` 完整指纹且要求非空 ⇒ 实测**缺失 0 / 指纹变化 0 / 逐条相同 True** |
| 终判 | `VERDICT=PASS`，`rc=0`（v3: `status-conformance-v3-*.txt`；v2 存档保留作对照） |
| 未连 7691 | 三轮观测（正判 / 负控 B / 还原）共 48 次请求，各耗时 ~3.5ms、全部止步于鉴权层 ⇒ **端点函数体一次都没执行** |

**⚠️ 更正一处我原先的错误声明（Codex r1 LOW）**：初版验收单写「未在真实树态上跑负控，
因为那需要执行端点函数体、会连 7691」——**这句不成立**。负控 B 证明：保留鉴权依赖不动、
只改路由对象上的**声明**，端点体照样不执行，全程不连库。该缺口已补上，不再是缺口。

**⚠️ 这个探针仍然不证明什么**：只覆盖 `/system/*` 这 16 个 operation（另外 190 个未证明）；
只做 status code 这一项（不做 schema / content-type / headers 三项）；
只发**不带 key** 的请求 ⇒ 每个 operation 只观测到一个状态码，未动态验证
「未配置 key ⇒ 503」与「带正确 key ⇒ 业务状态码」两档。

### (g) 鉴权形态门

新增 `tests/unit/test_startup_health_check.py::TestSystemRouterAuth` 三条（**位置**：该文件末尾，紧接 `TestSetupWizardPathValidation`）：

| 用例 | 断言 | 结果 |
|---|---|---|
| `test_system_router_rejects_without_key_403` | 无任何 key 头 GET `/api/v1/system/startup-check` ⇒ `403` **且** `detail == "Invalid internal API key"` | ✅ |
| `test_system_router_accepts_with_key_200` | 同端点带正确 key ⇒ `200`（原状态码） | ✅ |
| `test_wrong_key_also_403` | key 不匹配（Branch 4）⇒ 同码同文案 | ✅ |

**无头档的机制写死为卡文选项 ①**：另起一个**不带默认头**的裸 `TestClient(app)`（配 `no_lifespan`），
settings 复用 `tests.support.authed_client.authed_settings_override`（**只 import，未改 U10-C 的文件**）。
理由：`authed_client` 把 key 挂在 `TestClient(app, headers=…)` 的**实例级默认头**上，在它上面发不出「一个头都不带」的请求，
照字面写会得到名实不符（DD-13）。

**为什么期望码是 403 不是 503（实测分支表）**：两档共用「已配置 key + `DEBUG=True`」⇒ 落 `security.py:144-152` **Branch 3**。
`503` 只来自 Branch 1（`:96-105`，`DEBUG=False` + 空 key）与 Branch 2（`:110-142`），本档一个都不沾。
`detail` 逐字绑定是为了区分 Branch 1/2 的 `Internal API key not configured…`。

**⚠️ 这三条门只锁「已配置 key」那一档**：它们靠 `authed_settings_override` 把 settings 钉成
「已配置 key + `DEBUG=True`」。换成**真实 `backend/.env`**（key 为空 + `DEBUG=True`），同样的请求会走
Branch 2 拿到 **503** —— contract 定向 after 实测就是 503（见 §1(f-补)）。
两种码都在本卡的 `responses` 声明里，**但本卡的行为门只覆盖 403 那档**；503 那档归 U10-E。

**⚠️ 卡文事实修正 ③**：卡文 §二.4 要求 `test_system_endpoint_auth.py` **全绿**。实测该文件在本分支
**开工/收工都是 `2 failed, 8 passed`**，两条红是
`TestSystemConfigAuth::test_prod_no_key_configured_503` 与 `TestSystemTestLLMAuth::test_prod_no_key_configured_503`
（用例体 `_settings_factory(debug=False, key="")` ⇒ 正是卡文 (l)⑩ 判给 **U10-E** 的 503 档）。
两条**都在 202 基线里**，开工/收工**逐条相同** ⇒ 本卡既未新增也未修复。存档 `auth-file-after-20260909T163754.txt`。

### (h) openapi.json

由 `scripts/spec-tools/check-openapi-drift.py --write`（与 pre-commit `spec-sync` hook 同一支脚本）再生，**未手改**。
`openapi-regen-20260909T163110.txt`：`WROTE: backend/openapi.json (paths=194 schemas=354)`，diff `156 insertions(+), 2 deletions(-)`。

diff 分三类（**不是只有 `x-generated-at`**）：
1. **形状变化（本卡引入）**：**14 个** `/system/*` operation 各新增 `403` / `503` 两个 response + 一段 `security` ⇒ 14×(2+1) 块。
   ⚠️ `/system/*` 的 operation 总数实测是 **16**（卡文写「约 14 个端点」）；差的 2 个是 `/system/config` 与 `/system/test-llm` ——
   它们改前已在端点级挂了依赖并声明了 403/503，所以 diff 里不出现。**受 router 级依赖影响的是 16 个，新增声明的是 14 个。**
2. **`x-generated-at`** 由 `2026-09-06T12:36:48` → `2026-09-09T08:31:16`
3. **⚠️ 既有漂移被顺带扫入（非本卡改动）**：`/daily-review` 某端点 description 里 `learning_events.jsonl` → `learning_events` 一处文本差。
   说明：仓里那份快照生成于 2026-09-06，其后有别的卡改了该 docstring 而未再生快照；本卡一再生就把它带上了。
   hook 在 commit 时会做同样的事，**无法只再生自己那部分**。如实登记，见 §6 台账 ⑬。

**快照漂移门（同在 `tests/contract`，但不走 schemathesis ⇒ 秒级，可跑完）**：
`tests/contract/test_openapi_snapshot_drift.py` → **26 passed，`rc=0`**，且该跑
`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`（存档 `openapi-drift-gate-after-*.txt`）。
它的主判据正是「committed 快照与当前 `app.openapi()` 归一化后相等」⇒ 本卡再生的那份**不是陈的**。

**⚠️ 悬空 security 引用：根因既有，但本卡把影响面从 2 扩大到 16（Codex r1 MEDIUM 更正过我的表述）**

per-operation 的 `security` 写的是 `{"APIKeyHeader": []}`，而 `components.securitySchemes` 里
只定义了 `InternalApiKey`（`main.py:554-561` 手工加的）⇒ 该引用**悬空**。

| | U0 | 本卡 HEAD |
|---|---|---|
| 悬空引用的 operation 总数 | **17** | **31** |
| 其中 `/system/*` | **2** | **16** |

⚠️ 我最初写的是「本卡只是把同一模式扩大」——**偏轻**。准确说法（Codex 独立比对得出）：
那 14 个 operation 原先**继承 `main.py:568` 的有效全局 `security`**，现在被一个**无效的局部声明覆盖**。
根因不在本卡地盘（要动 `main.py` 或 `security.py` 的方案名），⛔ 按「禁顺手修存量」不改 ⇒ **带这两个数字移交**（§6 台账 ⑭）。

✅ 另一条独立结论：插件侧 `frontend/obsidian-plugin/src/main.ts:1753` 手工发送的
`X-CLS-Internal-Key` 与后端一致 —— **「插件请求正确」与「OpenAPI 契约正确」是两个结论**，前者成立不掩盖后者。
存档 `openapi-security-before-vs-after.txt` + `codex-review-CARD-RED-A1-sentinel.md`。

### (i) 两道 hook 门与存量

#### (i-1) `python-lint`（ruff）—— ⚠️ 拦下本卡的其实是 **format**，不是卡文预期的 typecheck

首次提交被 `python-lint` 拦下：`ruff check` 全过，但 `ruff format --check` 报 6 个文件 would reformat。
⛔ **不能直接 `ruff format` 那 6 个文件**：它会重排 `system.py` 的 `:74/:93/:101/:112…` 等**存量行**、
`test_mock_degradation_transparency.py` 的 **129** 行 —— 那正是卡文明令禁止的「顺手修存量」。

按 U0 树态实测把责任分开（`ruff-format-baseline-*.txt`，line-length=120）：

| 文件 | U0 时 | 处置 |
|---|---|---|
| `test_health_detailed.py` / `test_kg_health.py` / `test_startup_health_check.py` | **已合格** | 违规是**本卡引入的** ⇒ 跑 `ruff format`，实测 diff **只落在本卡新增的块里**（各 6–8 行），一行存量未动 |
| `system.py` / `test_mock_degradation_transparency.py` / `test_review_mode_support.py` | **本来就不合格** | 存量 ⇒ **不动**。本卡在 `system.py` 的 `responses` 块与既有 `:783-788`、`:849` 两处**逐字同形**（卡文要求「同形」），保持一致优先 |
| `test_config_drift.py` | 已合格 | 仍合格 |

**⚠️ 判据换过一次（Codex r1 LOW 打回）**：初版判据是「format-dirty **文件集合** U0 = 收工」——
**不成立**，文件级粒度看不见「已经脏了的文件里**新增**的违规」，而实测我的新增行确实还不合格
（`system.py:41-43` / `test_mock_degradation_transparency.py:53-55` / `test_review_mode_support.py:45-47`）。

**现判据 = 带符号行内容多重集比较**（`ruff-format-hunk-multiset-*.txt`）：取 `ruff format --diff` 的
`+`/`-` 行内容（去行号）排序后，U0 版本与收工版本比多重集。
⚠️ **它比「文件级集合」细，但仍有盲区**（Codex r2 LOW-4）：多重集丢掉了位置、上下文与 hunk 边界，
所以「把旧位置的一处违规修好、同时在新位置引入一处**内容相同**的违规」两侧仍相等 —— 这类**抵消**看不见。
纯新增（哪怕与存量内容重复）不会漏，因为计数会增加。本卡这次经 Codex 独立核对：
formatter 想改的位置与本卡新增行**无交集**，未发生上述抵消。
同时把上述三处**本卡新增的块**
整理成 ruff 偏好写法（⛔ 存量行仍一行不动）。实测：

| 文件 | U0 hunk 行数 | 收工 hunk 行数 | 结果 |
|---|---|---|---|
| `system.py` | 97 | 97 | ✅ 逐条相同 |
| `test_mock_degradation_transparency.py` | 122 | 122 | ✅ 逐条相同 |
| `test_review_mode_support.py` | 84 | 84 | ✅ 逐条相同 |
| 其余四个 | 0 | 0 | ✅ |

`ruff check` **All checks passed!**
⇒ 提交时 `LEFTHOOK_EXCLUDE` 同时跳过 `python-lint`，依据即本表 + hunk 多重集对照。

⚠️ 代价如实记：`system.py` 那处 `responses` 现在是**单行**，与既有 `:783-788` / `:849` 的多行写法**不同形**
（文案仍逐字一致）。取舍是「新增行必须自己合格」优先于「与存量写法一致」，已在代码注释里写明理由。

⚠️ **格式化改了代码 ⇒ 全部单元裁判已按定稿态重跑**（`unit-final-*` / `five-final-order-a|b-*`），
⛔ 不拿格式化之前那几份存档冒充定稿态结果。

#### (i-2) pyright 门与存量

`pyright-multiset-diff-p1-20260909T162635.txt` 末行 **`NEW=0`** ✅
（BASE = 未改 `system.py` 之时的工作树，即 `U0` 树态；AFTER = 本卡最终代码。归一化去掉 `:行:列` 后逐条相同，
7 条存量的**行号平移 +17** 正是本卡加的注释与参数行数 —— 若按行号比会误判成 7 条全新增。）
⛔ 7 条存量未修（归 U2 阶段 2）。

**是否用过 `LEFTHOOK_EXCLUDE`**：见 §(k)。

### (j) Codex

见 §4。

### (k) 提交

见 §4。

---

## 2 DoD-3

### 4-A 「Claude 已代验」（技术断言，逐条有存档）

| # | 断言 | 存档 · 锚 |
|---|---|---|
| 1 | 开工 `tests/unit` 对 202 基线**零 `>` 行** | `red-diff-open-20260909T160022.txt` |
| 2 | 卡文 12 条逐条在开工红集中，且五文件红集恰好等于这 12 条 | `card12-presence-open-*.txt` / `five-files-red-open-*.txt` |
| 3 | 12 条的失败正文首行都是 `live Neo4j port connect attempted`（哨兵，非断言） | `five-open-order-a-20260909T160624.txt`，哨兵串计数 **33** |
| 4 | 归属漂移实证：换收集顺序，服务级红换人 | `five-open-order-a-*.txt` vs `five-open-order-b-*.txt` |
| 5 | 收工五文件**两种收集顺序**：FAILED 集合都为空，哨兵串计数都为 **0** | `five-after-order-a-20260909T163754.txt` / `five-after-order-b-20260909T163754.txt`（各 `72 passed`，`rc=0`） |
| 6 | 收工 `tests/unit` 对 202 基线**零 `>` 行**；对开工 `<`12 / `>`0，消掉的正是那 12 条 | `red-diff-after-*.txt` / `red-diff-open-vs-after-*.txt` |
| 7 | 汇总行与 `rc=` 行在每份存档里 | 见各文件末两行 |
| 8 | `grep -n 'APIRouter(' system.py` 含 `dependencies=` 与 `responses={403,503}` | 见 §3 |
| 9 | 鉴权形态门三条绿（403 + detail 等值 / 200 / 错 key 403） | `five-after-order-a-*.txt` 的 PASSES 段 |
| 10 | `test_system_endpoint_auth.py` 红集开工=收工（2 条，均在 202 基线内，归 U10-E） | `auth-file-after-20260909T163754.txt` |
| 11 | `tests/api` open/after 各 `268 passed`，diff 空 | `red-api-diff.txt`，`api_diff_rc=0` |
| 12 | pyright 多重集 **`NEW=0`** | `pyright-multiset-diff-p1-*.txt` 末行 |
| 13 | 12 条逐条处置表（真连点/处置/依据） | `sentinel-triage-20260909.txt` |
| 14 | 容器 healthcheck 走 `/api/v1/health`，不经 `/system` router | `docker-compose.yml:228` + `router.py:68-72` |
| 15 | contract 定向 before/after 对照（**并说明该门看不见本卡要验的性质**） | `contract-sys-before-…165510.txt` / `contract-sys-after-*.txt` / `red-contract-sys-diff.txt` |
| 16 | `/system/*` 全部 **16** 个 operation：无 key ⇒ 403，且 403 均已声明；**负控成立**（摘掉声明后 16 个全 FAIL） | `status-conformance-after-20260909T173152.txt`，`VERDICT=PASS`，`rc=0` |
| 17 | 探针 16 次请求各 ~3.5ms 且止步鉴权层 ⇒ 端点函数体未执行 ⇒ 未连 7691 | 同上（`request.completed` 行的 `duration_ms`） |
| 18 | live vault 90 分钟内零改动（硬边界） | `find canvas-vault -newermt '-90 minutes'` 无输出 |
| 19 | contract 定向 after 与 before **nodeid 逐条相同**，diff 空，零新增红 | `red-contract-sys-diff.txt`，`contract_diff_rc=0` |
| 20 | 旁证：contract 里出自 `app.api.v1.system` 的哨兵串 **2 → 0**；端口门总账 **207 → 199** | `contract-sys-before-…165510.txt` vs `contract-sys-after-…173229.txt` |
| 21 | openapi 快照漂移门 **26 passed / rc=0 / 端口连接 0** | `openapi-drift-gate-after-*.txt` |
| 22 | `python-typecheck` 拦截的原始输出 + 「报错不在本卡改动行」（唯一 hunk `@@ -28 +28,18 @@`） | `lefthook-typecheck-blocked-*.txt` |

### 4-B 「你来验」（零技术词）

1. 我打开设置页，点「检查系统状态」 → 我看到 Neo4j / Ollama / LanceDB 等各项状态**一条条列出来**，
   哪一项没起来也写清楚了、还给了修复提示 → 页面**不会卡在转圈**。
   我感觉这台机器的状况是**看得见的**——就算有东西没起来，我也知道是哪一个、该去修什么，而不是对着一个转圈的图标发呆。（felt-sense）
2. 我第一次装好、还没把那把内部密钥填进「设置」里就去点「检查系统状态」 → **我会被挡住**，
   页面上会看到一条「没有权限 / 服务暂时不可用」之类的提示（具体哪一种取决于后端那边有没有配好密钥）。
   ⚠️ **这是本卡新引入的行为，本卡不宣布这一项验收通过**（Codex r1 MEDIUM 也这么判）。请你告诉我：
   你觉得「先填密钥、再检查状态」这个顺序可以接受吗？还是「刚装好时的自检」应该不需要密钥就能用？
   —— 见 §5.5。我这边缺的是「先配后端密钥、再把密钥交给客户端」这条流程的验证。
3. 我在复习白板上点「开始复习」 → 卡片照常出来，**不会因为后台数据库没开而变慢或报错**。

---

## 3 关键命令与输出（可复现锚）

```
$ grep -n 'APIRouter(' backend/app/api/v1/system.py
28:router = APIRouter(
$ git diff --cached --unified=0 --no-color -- backend/app/api/v1/system.py | grep '^@@'
@@ -28 +28,18 @@ logger = logging.getLogger(__name__)      # 唯一一个 hunk：1 行 → 18 行
$ git diff --name-only --no-color 0acea4e3 HEAD -- . ':(exclude)_bmad-output'
（见 §4 提交后的实测输出；⛔ 写法必须是 ':(exclude)…'，':!…' 在 zsh 下 rc=128 且 stdout 空 = 假绿）
```

### 3.1 §二.7 地盘门（阶段一单段 `U0..`，提交前按工作树跑）

```
$ git -c core.quotepath=false diff --name-only --no-color 0acea4e3 -- . ':(exclude)_bmad-output' | sort -u
backend/app/api/v1/system.py
backend/openapi.json
backend/tests/unit/test_config_drift.py
backend/tests/unit/test_health_detailed.py
backend/tests/unit/test_kg_health.py
backend/tests/unit/test_mock_degradation_transparency.py
backend/tests/unit/test_review_mode_support.py
backend/tests/unit/test_startup_health_check.py
$ git diff --stat --no-color 0acea4e3 -- <FORBID 六项>      # 空，forbid_rc=0
```
存档 `scope-worktree.txt`。禁改路径（`tests/conftest.py` / `tests/unit/conftest.py` / `tests/support` /
`endpoints/kg_health.py` / `clients/neo4j_client.py` / `app/services`）**全部为空** ✅

`*.stderr*` 由 `.gitignore:264 _bmad-output/审查/**/*.stderr*` 覆盖（`git check-ignore -v` 实测），
`git status --untracked-files=all | grep stderr` 无命中 ⇒ 不会入库 ✅
`board_manifest_last_run.json` 未被改动 ✅

---

## 4 提交与 Codex

### 4.1 提交记录

| 项 | 值 |
|---|---|
| commit | **`b8017248`** `test(unit): 12 条哨兵红按真连点测试侧打桩 + system router 落鉴权 [BATCH-2026-09-07-第十三批 / CARD-RED-A1-sentinel]` |
| header 长度 | **95** 字符（`wc -m`，≤100 ✅）；body 行最长 **95**（≤100 ✅） |
| 改动统计 | 66 files changed（代码 8 + `_bmad-output` 58） |
| 跳过的 hook | `LEFTHOOK_EXCLUDE=python-lint,python-typecheck` —— 两者都带存档（§1(i-1) / §1(i-2)） |
| 跑过的 hook | `ghost-files` ✅ / `mutant-residue-scan` ✅ / `spec-sync-flat` ✅（再生并 `git add` openapi.json）/ `commitlint` ✅ / `spec-reference` ✅ |
| `*.stderr*` | 未入库（`.gitignore:264` 覆盖，`git status --untracked-files=all \| grep stderr` 无命中） |
| `board_manifest_last_run.json` | 未改动 |
| push | **未 push**（卡文要求） |

### 4.2 提交后地盘门（`scope-postcommit-*.txt`）

```
$ git diff --name-only --no-color 0acea4e3 b8017248 -- . ':(exclude)_bmad-output'
backend/app/api/v1/system.py
backend/openapi.json
backend/tests/unit/test_config_drift.py
backend/tests/unit/test_health_detailed.py
backend/tests/unit/test_kg_health.py
backend/tests/unit/test_mock_degradation_transparency.py
backend/tests/unit/test_review_mode_support.py
backend/tests/unit/test_startup_health_check.py
$ git diff --stat --no-color 0acea4e3 b8017248 -- <FORBID 六项>   → 空, forbid_rc=0
$ for c in $(git log --format=%h --no-merges 0acea4e3..b8017248); do git show --stat --oneline $c -- <FORBID>; done → 全空
$ git log --format='%h %s' --no-merges 0acea4e3..b8017248        → 只有 b8017248 一条
```
提交后复跑 openapi 快照门：**26 passed**，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`
（hook 在提交时又再生了一次 `openapi.json`，故必须复跑）。

### 4.3 Codex 轮次

| 轮 | 模型 / effort | 审查绑定 | 结论 |
|---|---|---|---|
| r1 | `gpt-6-astra` / `ultra` | `b8017248` | **BLOCKER 0 / HIGH 0**；2 MEDIUM + 3 LOW。存档 `codex-review-CARD-RED-A1-sentinel.md` |
| r2 | `gpt-6-astra` / `ultra` | `e74757c5`（r1 整改后的 HEAD） | **BLOCKER 0 / HIGH 0**；2 MEDIUM（均为「登记未闭合」，判定移交恰当）+ 3 LOW。存档 `codex-review-CARD-RED-A1-sentinel-r2.md` |

**停轮判定**：r2 绑定 `e74757c5` = 当时 HEAD，`BLOCKER=0 / HIGH=0`。r2 之后的整改**只动 `_bmad-output`**
（验收单文案 + 探针加固），**代码零改动** ⇒ 按协议「只改 `_bmad-output` 不算」，r2 即末轮。
末轮绑定自证见 §4.4。

#### r2 逐条处置（三条 LOW 都是「我改了处置表却没把正文里被推翻的说法一起改掉」）

| # | 级别 | Codex r2 指出 | 处置 |
|---|---|---|---|
| 1 | MEDIUM | 悬空 security 引用：新表述准确、移交符合地盘约束，**但缺陷仍未修复，应继续标为未解决**，不能视为仅文案问题 | **接受**。§6 台账 ⑭ 标注为 **OPEN（未解决）**，不是「已说明」 |
| 2 | MEDIUM | 装机档撤回正确，但新描述**仍不是完整配置矩阵**（还差 bypass 档与 `Settings` 建不出来那档） | **接受**，§5.5 补全四档矩阵 |
| 3 | LOW | **还原自证会对空观测误报 PASS**：`restored=[]` 也满足「没有未声明码」；Codex 用受控反例复现（删光 `/system/*` paths 后仍 `VERDICT=PASS`）。负控 B 也只比条数、未绑键集 | **接受并加固探针**（`_bmad-output` 内，不触发新轮次）：还原自证改为**逐条比对完整指纹** `(method,path)→(状态码,声明集合)` 且要求非空；负控 B 从「条数相同」收紧为「**键集与正判逐条相同**」。v3 实测：键集相同 `True`、还原指纹缺失 0 / 变化 0 |
| 4 | LOW | 「新增违规必然出现新内容」**过强**：多重集丢了位置与上下文，「旧位置修好 + 新位置引入同样违规」两侧仍相等（抵消）。**纯新增不会漏**（计数会涨） | **接受**，§1(i-1) 改写为「带符号行内容多重集比较」并写明抵消盲区；Codex 独立核对本卡 formatter 想改的位置与新增行**无交集**，本次未发生抵消 |
| 5 | LOW | 验收单 `:123` / `:200` / `:501` **仍重复着被 r1 否定的说法**（「逐项相同」/「检查 0 次 ⇒ 两码都声明到位」/「现在会 403」）⇒ L3/L4②/M2 的文档整改**未全文完成** | **接受，逐处改正**（本轮已改） |

#### r2 独立复核确认的几条（不是我的自述）

- 两个 fixture 的新 docstring **通过复核**；`431/467/534/554` 行号仍准确（`554` 是判定、实际调用在 `555`）。
- 冷首触候选 `test_verification_service_activation.py:221` **确实成立**，Codex 动态验证到 driver 初始化入口即停（未拨号）；该路径在 `U0..HEAD` **无改动** ⇒ 属**既有隔离边界**，无依据要求本卡越界修复。
- 存档数字独立重算一致：unit `120 failed / 4810 passed / 48 skipped / 29 errors`；对 202 基线 **减 53 / 增 0**，对开工 **减 12 / 增 0**；双序各 72 passed 零哨兵；api 268 passed 端口 0。
- 负控 B 的还原**本次没有失败**：路由声明内容、字典与内层对象身份、键顺序、完整 OpenAPI 内容、依赖覆盖、lifespan 均已恢复，连接尝试 0。

#### r1 逐条处置（⛔ 三条是「把推断当事实写进 docstring/验收单」，属名实不符，必须改正）

| # | 级别 | Codex 指出 | 处置 |
|---|---|---|---|
| 1 | MEDIUM | **悬空 security 引用被本卡扩大**：`APIKeyHeader` 在 `components.securitySchemes` 里未定义，独立比对 U0→HEAD 悬空 operation **17→31**，其中 `/system/*` **2→16**。这 14 个原先继承 `main.py:568` 的**有效**全局声明，现被**无效**的局部声明覆盖 | **接受并改写结论**。原文说「同一模式扩大」偏轻，实况是「把 14 个从有效声明换成了无效声明」。修法在本卡地盘外（要动 `main.py` / `security.py` 的方案名），⛔ 按「禁顺手修存量」不改 ⇒ **带精确数字移交**（§6 台账 ⑭）。Codex 同时确认插件侧 `main.ts:1753` 手工发的 `X-CLS-Internal-Key` **是对的** —— 「插件请求正确」与「OpenAPI 契约正确」是两个结论 |
| 2 | MEDIUM | **装机档不能宣布验收通过**，且「没有 key 就 403」不准确（未配置 key 时通常是 503） | **接受**。4-B 第 2 条已改写为按后端配置分档；§5.5 保留为未证明项，并明确「本卡不宣布该项验收通过」 |
| 3 | LOW | **「进程终态逐项相同」不成立**：真实失败路径 `:534` 会写 `_last_health_check` 时间戳，`AsyncMock` 不会。但「同一实例不移债」的结论**成立** | **接受并改 docstring**：两个 fixture 的措辞改为「**连接控制状态**相同」，并写明差异项与「它不参与是否再连的判定」。code 改动 ⇒ 触发 r2 |
| 4 | LOW | 探针负控有效，但两处解释不成立：① 「真实声明变异必然连库」是错的；② 「还没走到 schema 校验就超时」依据不足（Hypothesis 先执行函数体、后判耗时） | **接受，并把①从「登记缺口」升级为「直接做掉」**：探针加了**负控 B** —— 在真实 `app.routes` 上删 403 声明 + 清 `app.openapi_schema` 缓存 + **原样重跑观测**，实测 16/16 变红，还原后再次全绿，全程不连库。②改写为「只能确证最终判定被 DeadlineExceeded 占据，存档里没有任何 status_code_conformance 结论」 |
| 5 | LOW | **「format-dirty 文件集合相同 ⇒ 零新增违规」不成立**（文件级粒度看不见已脏文件里的新增违规），且本卡新增行确实仍不合格 | **接受，换判据 + 改代码**：判据升级为 **hunk 内容多重集**对照（U0 vs 收工，逐 hunk 比），并把 `system.py` / 两个 fixture 里**本卡新增的块**整理为 ruff 偏好写法（⛔ 存量行仍不动）。新判据实测 7 个文件 hunk 逐条相同（97/122/84/0/0/0/0） |

#### r1 顺带纠正的一处**我自己在 prompt 里写错的数字**

送审 prompt 的问题 4 写成「对 202 条红基线的 diff 只有 12 条 `<`」—— **混用了基线**。正确是：
- 202 基线 → 定稿 149：**减 53、增 0**
- 开工 161 → 定稿 149：**减 12、增 0**（这 12 条才是卡文那 12 条）

本验收单 §1(b)/(f) 两处一直是分开写的，未受影响；错的是 prompt 那一句，记此备查。

命令（协议 §2 原样，`-rN` 逐轮递增）：
```
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-A1-sentinel[-r2].md)" \
  > _bmad-output/审查/codex-review-CARD-RED-A1-sentinel[-r2].md \
  2> _bmad-output/审查/codex-review-CARD-RED-A1-sentinel[-r2].stderr </dev/null
```
两份存档首部均按协议 §2.1 补齐（模型 / reasoning_effort / codex 版本 / 审查绑定 / 会话头自证）。
⚠️ 会话头那条如实写明：字面「前三行」是 stdin 提示 + `codex_models_manager` 刷新超时 ERROR，**不含 model 行**，
故抄的是真正的会话头四行（`OpenAI Codex v0.153.3` / `model:` / `reasoning effort:` / `session id:`）。
`*.stderr` 未入库。`grep -c 'gpt-5'` 两份均为 **0**。

### 4.4 末轮绑定自证（D-15 停轮条件）

| 条件 | 实测 |
|---|---|
| 末轮 = r2，绑定 `e74757c5` | ✅ |
| 该轮 `BLOCKER = 0` 且 `HIGH = 0` | ✅（r2 正文首句） |
| 审后**代码**零改动 —— `git diff --stat e74757c5 HEAD -- . ':(exclude)_bmad-output'` | **空**，`bind_rc=0` ✅ |
| 工作树未提交的代码面 | **空**，`wt_rc=0` ✅ |
| r2 之后只改了 `_bmad-output`（验收单文案 + 探针加固） | ⇒ 协议「只改 `_bmad-output` 不算」⇒ **r2 即末轮**，不需要 r3 |
| 轮次上限 5 | 用了 2 轮 |

⛔ 写法自查：`':(exclude)…'` 而非 `':!…'`（后者在 zsh 下 rc=128 且 stdout 空 = 假绿）。

---

## 5 本卡未证明什么

1. **未证明哨兵归属漂移已根治**。本卡按路径打桩，只覆盖这 6 个测试文件；异步任务 / 后台线程的越界连接仍可能记到别的 nodeid 上。
2. **未证明 `/system/health` 没有本树之外的无 key 探针依赖**。census 只覆盖本仓 + `docker-compose.yml`，未查用户机上的外部监控 / 浏览器书签 / 手工脚本。
3. **未证明 `get_neo4j_client()` 单例在别的目录级套件里的首触者是谁**（`tests/api` 该跑里 268 条全绿、无哨兵红，但那不等于证明了首触者身份）。
4. **未证明 `kg_health.py` 的生产真连点在别处不会红**。本卡只在**单元测试进程**里打桩；生产端点仍无鉴权、仍会真连。
5. **未证明 router 级鉴权对「首次装机时还没有 key」的场景无害**。`POST /system/setup-wizard` 与 `GET /system/health` 现在都受鉴权 —— **产品面风险，本卡只登记不处置，明确不宣布该项验收通过**（见 4-B 第 2 条，需用户裁决）。
   ⚠️ **不要简写成「现在会 403」**（Codex r1 M2 / r2 M2 两次点到）。完整配置矩阵是：
   - 后端**已配置** key + 请求缺头 ⇒ `403`（`security.py:144`）
   - 后端 key **为空** ⇒ 通常 `503`（`security.py:96` / `:110`）
   - `DEBUG=True` + `ALLOW_UNSAFE_DEV_AUTH_BYPASS=true` + loopback 三者同时成立 ⇒ **放行**
   - 非本地配置且 key 为空 ⇒ `config.py:295` 在 `Settings` 校验期就 raise，**根本没有 HTTP 响应**
   本卡未验证「实际页面表现」与「先配后端 key、再把 key 交给客户端」这条流程。
6. **未跑 `tests/integration` / `tests/e2e`**。
7. **未证明 openapi.json 的 security 段变化与插件侧实际请求头一致**；且 `APIKeyHeader` / `InternalApiKey` 名字不一致是**既有**缺陷，本卡未修（§1(h)）。
8. **未证明 `tests/contract` 全量面**，且**那道门本身看不见本卡要验的性质**（见 §1(f-补)）：定向 4 条的 before 全红，拒因是 `DeadlineExceeded`，`status_code_conformance` 出现 0 次 ⇒ 差集为空不构成证据。本卡改用自带负控的 `status_conformance_probe.py` 覆盖 `/system/*` 全部 16 个 operation；其余 190 个 operation、以及 schema / content-type / headers 三项一致性，**本卡未证明**。
8b. ~~负控只做到 spec 侧变异~~ —— **已补**（Codex r1 后新增负控 B：真实 `app.routes` 变异 + 重跑观测 + 还原自证，16/16 变红）。仍未做的是**磁盘树态**变异（改源码再跑），本卡用的是进程内路由对象变异。
10b. **未证明「任意收集顺序」都不移债**（Codex r1 Q4）：只证明了已采样的两种顺序 + 全量默认顺序。Codex 独立指出一个仍可能冷首触的候选：`tests/unit/test_verification_service_activation.py:221` 可经真实 `VerificationService` 走到 `verification_service.py:1931` 的 `get_mastery_store()`，且**未安装本卡的 health-check 桩** —— 若它被提前收集，可能承担首拨。这是**既有隔离边界**，不是本卡新增的移债，但本卡未覆盖。
10c. **全量跑里族 C 两条都红的重置者已有线索但本卡未验证**：Codex 指出 `tests/unit/test_neo4j_client.py:653` 在每条单例测试前后 reset 单例，且位于默认收集顺序中两个族 C 文件**之间** —— 能解释「全量两条都红、五文件单跑只红一条」。本卡未独立复现该链路。
9. **未证明开工 `<` 行里那 9 条 `test_agent_templates_smoke.py` 的成因**（本车道树上绿、202 基线树上红）。只证明了它们不是本卡改的（本卡未碰该文件）。
10. **未证明全量跑里族 C 两条都红的机制**。五文件单跑只红一条（谁先跑谁付账），全量跑两条都红 ⇒ 两者之间该单例被重置过至少一次，**重置者本卡未定位**。本卡对两个文件都打了桩，与重置次数无关。
11. **未证明 `raise_server_exceptions=False` 的丢失无害**（§1(d) 语义收窄）。只证明了这四条用例在收工时绿。
12. **阶段二整体未执行**：未 merge 候选树 ⇒ 未证明本卡改动与候选树里别的卡**语义**相容。
13. **未证明真实部署档（`.env` 里 key 为空 + `DEBUG=True`）下 `/system/*` 的产品行为可接受**：那一档返回 **503** 而不是 403（contract after 实测）。本卡的行为门只钉了「已配置 key ⇒ 403」这一档。
14. **未证明 contract 那 8 次 `DeadlineExceeded` 的成因**。before/after 次数相同（8/8），且 after 的 `/system/*` 请求已快到 3.5ms 量级仍超时 ⇒ 慢因大概率在 hypothesis 侧而非 HTTP 调用，但本卡**没有实测证明**这一点，只如实记录「before/after 同数、与本卡改动无关」。

---

## 6 台账待登记条目（主 session 落 `未合卡追踪台账.md`）

1. **12 条逐条处置表**：`_bmad-output/审查/evidence-red-a1-sentinel/sentinel-triage-20260909.txt`（真连点 / 处置 / 依据三列齐）。
2. **`system.py:28` 落 router 级鉴权 = 产品面变更**。新受影响的非测试调用点 **3 处**（不是卡文说的 2 处，见 §1(c) 表），全在两个已淘汰 Tauri 前端；容器 healthcheck 走 `/api/v1/health` 不受影响（实测依据同表）。
3. **`main.py:561` 文档声称 `/system/*` 受鉴权、实现此前只 2 个端点** —— 本卡让实现追上文档。
4. **卡文草案「哨兵文案指 lifespan」与实测吞点不符**：真实吞点是 `system.py:72-74` / `kg_health.py:72-77` / `neo4j_client.py:529-535`；`tests/conftest.py:155` 的 docstring 待改（**U7 地盘，移交**）。
5. **`app/api/v1/endpoints/system.py` 是 4 行纯注释空壳**（真 router 在 `app/api/v1/system.py`）—— 登记。
6. **`system.py` 7 条 pyright 存量未修**（归 U2 阶段 2）；多重集 `NEW=0`；**是否用过 `LEFTHOOK_EXCLUDE` 见 §4 提交记录**。
7. **W4-7 通告未到 ⇒ 本卡停在阶段一**。`P` / `M` / `"$M^2"` 无值；主 session 抽本卡 diff 面用**单段** `0acea4e3..HEAD`（⛔ 不要用卡文 (k)② 的两段并集）。
8. **Codex 轮次与每轮绑定 SHA** —— 见 §4。
9. **与 U5-D 的交集**：本卡改 `openapi.json` 的 `/system/*` 响应形状，而 `tests/contract/test_openapi_contract.py`（U5-D 地盘）用 schemathesis 对全端点跑 `status_code_conformance` ⇒ 两卡在**同一份 `openapi.json`** 上有交集。本卡只跑不改 contract。
10. **403/503 分工**：本卡只落「已配置 key + 缺 header ⇒ 403（Branch 3）」的形态门；「`DEBUG=False` + 空 key ⇒ 503（Branch 1）」那档归 **U10-E**，且 `test_system_endpoint_auth.py` 里那 2 条 `test_prod_no_key_configured_503` 开工/收工都红（既有，非本卡）。
11. **kg_health 地盘裁决 (甲) 已执行**：`backend/tests/unit/test_kg_health.py` 做了测试侧打桩（该条**已消红**，不是「登记不豁免留红」）；生产 `app/api/v1/endpoints/kg_health.py` 一字未改 ⇒ 该端点仍无鉴权、真连点仍在。
12. **`tests/api` 目录级对照**：`api-open-…164338.txt` / `api-after-…163754.txt`，各 `268 passed`，diff 空。
13. **⚠️ openapi.json 顺带扫入一处既有漂移**（`learning_events.jsonl` → `learning_events` 的 description 文本），来自 2026-09-06 之后别的卡改了 docstring 而未再生快照。hook 在 commit 时会做同样的事，无法只再生本卡那部分 —— 合并期需知晓。
14. **⚠️ OPEN（未解决）— 悬空 security 引用：根因既有，但本卡把面从 2 扩到 16（带数字移交）**：per-op 用 `APIKeyHeader`，`securitySchemes` 只定义 `InternalApiKey`。悬空 operation 总数 **U0 17 → HEAD 31**，其中 `/system/*` **2 → 16**。那 14 个原先继承 `main.py:568` 的**有效**全局声明，现被**无效**的局部声明覆盖。修法要动 `main.py` / `security.py` 的方案名（本卡地盘外）⇒ **移交**，建议与 U5-D 的 contract 面一起处置。插件侧 `main.ts:1753` 的请求头本身是对的，不受影响。
15. **⚠️ `tests/contract` 有两个跨卡的工程事实**（不只影响本卡，建议单独立卡）：
    - **跑不完**：≈3.6 min/operation × 207 ⇒ 外推 ≈12 小时；
    - **⛔ 它对「状态码是否被声明」这条性质是瞎的**：4 条定向 before 全红，拒因全是 `hypothesis.errors.DeadlineExceeded`（W4 端口门让每次真实请求 16–19s，超过 `@settings(deadline=10000)`），`status_code_conformance` 在整份存档里出现 **0 次**。
      ⇒ 只要端口门还在，这道门的 before/after 差集**对 schema 一致性不构成证据**。本卡用 `evidence-red-a1-sentinel/status_conformance_probe.py`（自带负控）补了 `/system/*` 那一格，但全量面仍缺判据。
16. **⚠️ 两处判据写法坑（值得进工程坑索引）**：
    - schemathesis 生成的用例**按 nodeid 点选选不中**（`ERROR: not found: …::test_api_contract`，参数段被丢），只能用 `-k` 子串；
    - `-k "'substr' or 'substr'"`（带单引号）**静默匹配全部**（207 collected / 0 deselected），无引号的 `-k "system"` 才真过滤（16 selected / 191 deselected）。
      **带引号那种写法会把「只跑了 4 条」伪装成「跑了全部」——是典型的假绿面。**
17. **开工 `<` 行里 9 条 `test_agent_templates_smoke.py`** 在本车道树上绿、在 202 基线树上红，成因未定位（属 U10-B 面），登记。

---

## 7 收官状态（如实，含两处不完美）

| 项 | 实测 |
|---|---|
| 分支 / HEAD | `card/u10-red-a` / `b422e9dc` |
| 本卡 commit | 3 个（`b8017248` 落地 → `e74757c5` r1 整改 → `b422e9dc` r2 整改，末者仅 `_bmad-output`） |
| 代码改动面 | 恰好 8 个文件（`system.py` + `openapi.json` + 6 个 `tests/unit/test_*.py`） |
| 禁改路径 | 空（`forbid_rc=0`）；逐 commit 佐证全空（`own_rc=0`） |
| `*.stderr*` 入库 | **本卡零**（三个 commit 都没有添加过名字含 `stderr` 的文件）。⚠️ `git ls-files` 里确有一个 `_bmad-output/审查/G4-9-evidence/census-stderr.txt`，实测由 `4c125f19`（CARD-G4-9，第五批）引入，**非本卡**；它也不匹配 `.gitignore` 的 `*.stderr*`（是 `-stderr.` 不是 `.stderr`） |
| push | **未 push**；本地无 `origin/card/u10-red-a` 追踪分支 |
| openapi 快照门（收官复跑） | `26 passed`，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` |

**⚠️ 两处不完美，如实登记而不粉饰：**

1. **工作树不是完全干净**：evidence 目录里留了 5 个未跟踪的 `.ts-*` 临时标记文件
   （各一行 `TS=...`，是跑裁判时记时间戳用的）。本 session 的 guard hook 拦下了 `rm`
   （破坏性操作需用户确认），所以**没删**。它们不影响任何 commit、不在任何判据面内；
   主 session 若介意可自行删除。
2. **`tests/contract` 全量面本卡未证明**（≈12 小时跑不完，且那道门对本卡要验的性质没有给出结论）。
   已用自带双重负控的探针补了 `/system/*` 那一格，其余 190 个 operation 仍缺判据 —— 见 §5.8。
