你是独立代码审查者。这是**第二轮**（round-2）。只读，不要修改任何文件。

# 〇 本轮定位

round-1 你给出 BLOCKER=0 / HIGH=0 + 2 MEDIUM + 3 LOW。作者**全部采纳并整改**，
因此按批次协议必须再送一轮。本轮请：

1. **优先核对 5 条整改是否真的落实、且没有引入新的失实说明**：
   - MEDIUM-1（移交理由过强）→ 改在 `_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt` §A：
     不再声称「断言已过期 / 必须重写 / 本卡修不了」，改为「前提未适配 + 分工移交」，
     并明写「为正向用例配匹配的 active vault 不等于关掉隔离，`vault_scope.py:162-176` 仍真实执行」。
   - MEDIUM-2（把不存在的 409 覆盖写成已有保障）→ 改在 `backend/tests/unit/test_chat_endpoint.py`
     与 `backend/tests/unit/test_study_question_deep_mode.py` 的 `client` fixture docstring：
     删除「vault 一致性判定本身由 test_enrich_context_vault_isolation.py 负责」，
     改为明写「本桩不证明什么」+ 登记「全仓当前没有任何测试对 enrich-context 断言 409」这个缺口。
   - LOW-1（请求路径分类不实）→ 同一份 second-layer 表：按请求实际走到哪里重分三类。
   - LOW-2（conftest 机制描述错）→ `backend/tests/support/authed_client.py` 模块 docstring
     「为什么不放进 conftest」段：改为「限制可发现范围 + 要求显式导入」。
   - LOW-3（Settings 逐字等价不实）→ `backend/tests/unit/test_sync_exception_classification.py`
     的 `_dev_settings` docstring：改为「只在鉴权相关字段上一致」。

2. **本轮绑定的是已提交的 HEAD**（不再是工作区）：`faeda37f`，父 commit `7004a365`。
   审查面 = `git diff 7004a365 faeda37f`。

3. round-1 已核过且未变的结论（覆盖不泄漏、实例头覆盖全部请求路径、17 条 active-vault 桩合理、
   sync 两桩没有替换异常分类路径、37=32+5 闭合）**不必重复论证**，除非整改动摇了它们。

4. 请特别检查：整改后的新说法本身是否**仍然过宽或过窄**。作者这一轮写了不少
   「本桩不证明什么」的自我限定，请核对这些限定是否与代码一致、有没有反过来低估或高估了覆盖面。

# 二 作者自述（round-1 版，供对照；整改点见 §〇）

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

- 本卡改动全文：`git diff 7004a365 faeda37f`（已提交，含新文件）
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
