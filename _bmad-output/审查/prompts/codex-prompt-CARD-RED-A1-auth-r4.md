你是独立代码审查者。这是**第四轮**（round-4）。只读，不要修改任何文件。

# 〇 本轮定位

轮次记录：
- r1: BLOCKER=0 HIGH=0 + 2 MEDIUM + 3 LOW → 全部采纳整改
- r2（绑 `7004a365..faeda37f`）: BLOCKER=0 HIGH=0 + 2 MEDIUM + 2 LOW → 全部采纳整改
- r3（绑 `7004a365..bcbe2741`）: BLOCKER=0 HIGH=0 **MEDIUM=0** + 2 LOW → 全部采纳整改

**本轮绑定最终 HEAD `1e326860`**，审查面 = `git diff 7004a365 1e326860`（三个 commit）。
r3 之后没有任何代码改动尚未提交；工作区应当是干净的（若你观察到不一致，请指出）。

r3 两条 LOW 的整改：

1. **LOW-1**（chat 校验用例少算一条）→ `test_chat_endpoint.py` 的 `client` fixture docstring
   现在列全三条：`test_enrich_context_max_hops_validation` /
   `test_enrich_context_rejects_invalid_mode`（两者 Pydantic 422）+
   `test_enrich_context_empty_node_path_rejected`（端点内提前返回 400）。

2. **LOW-2**（行号仍在漂）→ 作者把**本卡内引用同一文件位置的地方一律改成用例名**，
   不再写行号；只对 `security.py` / `chat.py` / `sync.py` / `vault_scope.py` /
   `tests/conftest.py` / `tests/unit/conftest.py` / `test_vault_scope_409.py` /
   `test_sync_batch_auth.py` 这些**外部文件**保留行号（它们不随本卡改动漂移）。
   涉及 `test_chat_endpoint.py` / `test_study_question_deep_mode.py` /
   `test_enrich_context_vault_isolation.py` 三处 docstring 与
   `second-layer-20260909T134842.txt`。

3. 另采纳 r3 的精确化：把「一直绿」收窄为「本卡开工/收工两次目录级存档均通过」，
   并补上正面证据行 `unit-open-20260909T132605.txt:279` /
   `unit-after-20260909T134347.txt:279`。

**本轮请重点核对**：

- 上述三项整改是否落实，有没有**漏改**的位置（仍写着会漂的行号、或仍少算/多算用例）。
- 保留下来的**外部文件行号**是否仍然准确（尤其 `test_vault_scope_409.py:333-343` /
  `:345-373`、`tests/unit/conftest.py:395-418`、`tests/conftest.py:441-452` / `:490` /
  `:494-517`、`test_sync_batch_auth.py:98-99`、`security.py:110-142`）。
- 三份文档（两处 fixture docstring、`second-layer`、验收单）之间是否**互相一致**——
  同一件事有没有在一处说 A、另一处说 B。
- 有没有在这三轮整改中**新引入**的失实说明。

r1/r2/r3 已核过且未被动摇的结论（覆盖不泄漏、实例头覆盖请求路径、17 条 active-vault
桩合理、sync 两桩未替换异常分类路径、37=32+5 闭合、断言未变、未改生产代码与两个
conftest、「另有 409 覆盖」与「同一组桩」属实）**不必重复论证**。

# 二 作者自述（round-1 版，供对照；后续整改见 §〇）

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

- 本卡改动全文：`git diff 7004a365 1e326860`（三个 commit，含新文件）
- 前三轮存档：`_bmad-output/审查/codex-review-CARD-RED-A1-auth-r{1,2,3}.md`
- `backend/tests/unit/test_vault_scope_409.py:325-375`
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
