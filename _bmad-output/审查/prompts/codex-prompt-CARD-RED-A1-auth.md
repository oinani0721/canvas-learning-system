你是独立代码审查者。请对下面这张卡的改动做对抗性审查。只读，不要修改任何文件。

# 一 背景

仓库: Canvas Learning System（Tauri + React + FastAPI + Neo4j）。树:
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
分支 `card/u10-red-a`。本卡 = CARD-RED-A1-auth，批次 BATCH-2026-09-07-第十三批。
基线 commit = `7004a365`（同车道前一张卡 CARD-RED-E 的末 commit）。

## 要解决的问题

`backend/tests/unit` 里有 37 个用例长期红。根因不在被测业务逻辑，而在测试装置：

1. `app/security.py::require_internal_api_key` 在 commit `c9bb6c9a`(2026-05-13) 之后
   是 fail-closed 的。Branch 2（`:110-142`）原本是「DEBUG=True + 空 INTERNAL_API_KEY
   → 放行」，现在收紧为「还必须 `ALLOW_UNSAFE_DEV_AUTH_BYPASS=true` **且**
   `request.client.host` 属于 `{"127.0.0.1", "::1"}`」。
2. `fastapi.testclient.TestClient` 的 client host 恒为字符串 `"testclient"`，永远不落
   loopback 集合 ⇒ 不带 key 的请求恒得 503。
3. `backend/tests/conftest.py:494-517` 的共享 `client` fixture 本来配了
   `INTERNAL_API_KEY="test-internal-key"`（`:490`），但三个测试文件各自定义了**同名**的
   本地 `client` fixture（裸 `TestClient(app)`），按 pytest 就近覆盖规则遮蔽了共享件。
4. 结果：挂了该依赖的端点（`chat.py:48` router 级、`sync.py:63` 端点级）在这四个文件里
   一次都没执行过业务逻辑，37 条断言全部停在鉴权墙。

## 本卡做了什么

- 新增 `backend/tests/support/authed_client.py`，提供 **opt-in**（必须显式 import）的
  `authed_client` fixture：settings 覆盖 + TestClient 实例级请求头 + `no_lifespan`。
- 四个测试文件改用它。其中三个文件（chat_endpoint / study_question_deep_mode）在自己的
  `client` fixture 里另加两个 patch；sync_exception_classification 另加两个 patch。
- 解开鉴权后重跑，逐条把第二层失败分成三类（vault 409 / W4 端口哨兵 / 真业务断言），
  能在测试侧打桩的打桩，判为契约演进的**登记移交、不改断言**。

## 本卡的硬边界（作者声明遵守，请独立核对是否真的遵守）

- 零 `backend/app` 写面（不改任何生产代码，含 `security.py` / `sync.py` / `chat.py` /
  `vault_scope.py` / `schema_gate.py` / `config.py`）。
- 不进 `backend/tests/conftest.py` 与 `backend/tests/unit/conftest.py`。
- 新 fixture 禁 `autouse`、禁用环境变量注入 key。
- 不改任何被测用例的断言；不用 skip / xfail 求绿。
- 不放宽 W4 端口哨兵（那道门禁止测试进程连 7687 / 7691）。

# 二 作者自述，请独立核对

1. `authed_client` 没有 `autouse`、没有触碰 `os.environ`、没有进任何 conftest；退出时
   **只**还原它自己加的那个 `dependency_overrides` 键（不做无条件 `clear()`）。
2. 开工 37 条红的去向逐条有账：32 条转绿，5 条仍红且已登记移交。
3. 第二层红分类表里判为「移交」的 5 条，确实不是本卡能修的（理由见分类表 §A）。
4. `sync.py:126` 的 `assert_identity` 不必补桩，依据是 `backend/tests/unit/conftest.py:395-418`
   的 autouse fixture `_stub_vault_identity_registry` 已把 `get_vault_identity_registry()`
   换成 no-op。
5. 未改任何断言，未改 `security.py` / `sync.py` / 任何生产文件。

# 三 请按重要性回答这些问题

1. `authed_client` 对 `app.dependency_overrides[get_settings]` 的覆盖会不会泄漏到同一
   pytest worker 里的其它测试？`backend/tests/conftest.py:441-452` 的 autouse
   `isolate_dependency_overrides` 是否真的兜得住？本 fixture 的 `finally` 还原逻辑在
   「用例自己又覆盖了同一个键」的情况下行为是否正确？
2. 请求头挂在 `TestClient` 实例上（初始化参数 `headers=`），是否覆盖到全部用例路径——
   包括用例自行发起的请求、以及带自定义 headers 的请求（会不会被逐请求 headers 覆盖掉）？
3. 第二层红里被判「409 打桩即可」的条目（chat_endpoint 10 条 + study_question_deep_mode
   7 条），这个桩是否掩盖了真的跨 vault 缺陷？判断依据是「这两个文件的 payload vault_id
   恒为同一个常量，且它们测的不是 vault 语义」——这个依据成立吗？
4. `test_sync_exception_classification.py` 新补的两个桩（`app.config.get_current_vault_id`
   与 `app.services.schema_gate.get_canvas_schema_gate`）是否让「异常分类」这件被测的事
   本身失真？该文件的六条断言验的是 `SyncService.process_sync_batch` 抛不同异常时端点
   返回 503 还是 500——两个桩是否让本该被覆盖的路径不再被覆盖？
5. 有没有哪条 nodeid 是靠「请求根本没走到业务层」才变绿的？特别请检查
   `chat_endpoint` 里 patch 掉 `get_memory_service` 之后，是否有断言实际上已经不再验证
   它原本想验证的东西。
6. `authed_client.py` 与四个测试文件的 docstring 里有大量事实性声明（行号、机制、
   「与生产降级行为逐字一致」之类）。请抽查这些声明是否与代码实际一致——写错的说明
   会被后人当模板照抄。

# 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级列出。每条给出：
- `file:line`
- 你的判断依据（引用具体代码或存档内容，不要只给结论）
- 建议的处置

若某一级没有问题，明确写「无」。最后给一段总评，说明这套改动是否达成了它声称的目标
（让 37 条业务断言真正跑到业务层），以及有没有把问题从一处挪到另一处。

# 五 边界（这些不在本次审查范围）

- 不评 W4 端口哨兵本身的设计（`backend/tests/support/live_port_guard.py` /
  `guard_plugin.py`）——它是别的卡的地盘。
- 不评 `backend/tests/unit/conftest.py` 的内容——那是同批另一张卡的地盘。
- 不评仓库既有的 pyright 存量问题。
- 不评 `_archive/` 下的任何内容。
- 不评那 5 条被判「移交」的用例应该怎么重写——只需判断「移交」这个决定本身是否成立。

# 六 最小读取面（请只读这些）

- 本卡改动全文：`git diff 7004a365 -- . ':(exclude)_bmad-output'`
  （另有一个未跟踪的新文件，见下）
- 新文件全文：`backend/tests/support/authed_client.py`
- `backend/app/security.py` 第 88-166 行
- `backend/app/api/v1/endpoints/chat.py` 第 38-52 行、第 283-330 行
- `backend/app/api/v1/endpoints/sync.py` 第 100-140 行
- `backend/tests/conftest.py` 第 441-452 行、第 470-520 行
- `backend/tests/unit/conftest.py` 第 393-420 行
- `backend/tests/unit/test_sync_batch_auth.py` 第 55-125 行（本卡打桩的先例，只读不改）
- `backend/app/core/vault_scope.py` 第 100-185 行
- 证据目录：`_bmad-output/审查/evidence-red-a1-auth/*.txt`
  其中 `second-layer-*.txt` 是第二层红三分类表，
  `closure-37-*.txt` 是 37 条去向的闭合校验，
  `gate-fixture-constraints-*.txt` 与 `gate-bare-testclient-*.txt` 是两道结构判据，
  `ruff-format-drift-proof-*.txt` 是格式漂移归属的证明。
