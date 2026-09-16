# 复核请求 — CARD-U9C-EVAL（评估卡，零生产改动）

你在只读沙箱内复核一张**评估卡**的交付物。请按下面五节阅读并给出 finding。

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`
分支 `card/t4-g3`，本卡起点 commit `9400ba26b816e8cad605b2a81e5fdf14e396541e`，
当前 HEAD `463fe762593db1f3d7f27aa76a2df0ad4b8b3379`（本卡只有这一个 commit）。

---

## ① 本卡范围

这张卡**不改任何生产代码**。`backend/app/**` 全程只读。改动面只有两类：

1. 新增一个回归测试文件 `backend/tests/regression/test_u9c_startup_rejection_eval.py`（4 条用例）；
2. 新增一份评估文档 `_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md`
   及其证据目录 `_bmad-output/审查/evidence-u9c-eval/`。

上游议题（U9-C）原本设想的是「legacy 兼容重做」，用户裁定把它降级为**评估卡**：
先把事实口径搞准、钉成回归测试，设计级改动另行排期。

---

## ② 本卡的声明（请逐条核这些声明是否被证据支持）

**声明 A — 前提更正**：U9-C 原立面写「CLI / 后台脚本在没有 vault 上下文时
实例化 `ReviewService` ⇒ 服务拒启」。本卡实测认为**不成立**：
`scripts/` 与 `backend/scripts/` 对 `ReviewService(` 零命中；
全仓非测试代码里 `ReviewService(` 只有一处，即 `backend/app/services/review_service.py:2996`
（**唯一生产实例化点**，位于工厂 `get_review_service` `:2939` 的双检锁内）；
`backend/app/main.py` 的 lifespan **不预先实例化** `ReviewService`。
⇒ 真正的拒启面是「后端启动之后，首个命中 `get_review_service()` 的 HTTP 请求」，
进程启动本身不受影响。

**声明 B — 消息不进响应体**：`VaultScopeUnresolved` 是裸 `Exception` 子类
（`backend/app/core/vault_scope.py:359`），没有专用处理器，逸出后落到
`generic_exception_handler`（`backend/app/core/exception_handlers.py:200` 定义、
`:312` 以 `Exception` 注册）。该处理器返回
`{"code": 500, "message": "Internal server error", "bug_id": ...}`（`:262-266`），
`CARD-G3-5` 指引原文只进 `logger.error(... error_message=str(exc) ...)`（`:250`）
与 `bug_tracker.log_error(...)`（`:243`，落 `data/bug_log.jsonl`）。
⇒ 设计稿「请求 500 **带 CARD-G3-5 消息**」只有一半成立：500 成立、进日志成立、
**进 HTTP 响应体不成立**。

**声明 C — 三层覆盖，无被测层被替身顶替**：
实例化层用真 `_VaultScopedCardStates.from_persisted`；
HTTP 层用真 `register_exception_handlers` 注册的真处理器；
工厂中段（`get_review_service` 先建 memory / canvas / graphiti 依赖，再到 `:2996`）
**本卡不执行** —— 跑它会连真 Neo4j / LanceDB，本卡硬边界禁止，
该段只以只读证据覆盖，并在验收单如实登记为「本卡未证明」。
测试里唯一被替换的是 `bug_tracker` 的**落盘路径**（重定向到 pytest 临时目录），
替换的是文件落点、不是行为。

**声明 D — 判据口径更正**：卡文原判据写「`grep -c 'blocked=' <pytest 输出>` 期望 0」，
理由是「哨兵只在出事时才打印该行」。本卡实测认为这个理由不成立：
`backend/tests/conftest.py:226-227` 的 `pytest_terminal_summary` **无条件**
写出 `live_port_guard.STATE.summary_line()`，而 `summary_line()`
（`backend/tests/support/live_port_guard.py:454-460`）恒含 `blocked=` 字面量。
故改判为「摘要行存在且三项计数全 0」+「`BLOCK_REASON` 那行不出现」。

---

## ③ 请复核项

1. **声明 A~D 是否成立**，尤其是否有反例让其中任一条站不住。
2. **测试是否真的钉住了它声称钉住的东西**：
   - 两条 fail-fast 分支（`review_service.py:570` 与 `:593`）是否都被覆盖到，
     断言的消息片段是否真在对应分支的消息里；
   - HTTP 层那条用例里，「异常侧含消息」与「响应体不含消息」两侧是否都被断言，
     是否存在某种情形让它在**没有真正验证到屏蔽**的情况下仍然通过；
   - 那条排他性断言（`code == 500` 且存在 `bug_id`）是否足以区分
     「这个 500 来自 `generic_exception_handler`」与「来自别处的 500」。
3. **负控（对照输入）是否真能判定**：`test_no_legacy_does_not_raise` 跑在与
   正例完全相同的作用域解析失败环境里。若断言被误写成「无条件抛出」，
   这条对照用例是否一定会失败？若它其实也能通过，请指出。
4. **评估文档的每条结论是否都有本卡实测证据**，而不是从上游勘探文档转抄；
   文档里引用的行号与存档文件路径是否与本树实际一致。
5. **是否误动了不该动的文件**：`backend/app/**` 是否一行未改；
   改动面是否超出 ① 列的两类。
6. 测试是否可能**误连**真实服务（Neo4j 7691/7687、LanceDB），
   或写入车道树里不该被写的文件。

---

## ④ 最小读取面

- `backend/tests/regression/test_u9c_startup_rejection_eval.py`（本卡新增，重点）
- `_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md`（本卡新增，重点）
- `_bmad-output/审查/evidence-u9c-eval/`（本卡裁判存档）
- 只读锚点（本卡未改，仅供核对声明）：
  - `backend/app/services/review_service.py` 的 `:348-600` 与 `:2939-3010`
  - `backend/app/core/exception_handlers.py` 的 `:200-315`
  - `backend/app/core/vault_scope.py:359`
  - `backend/tests/conftest.py:100-135` 与 `:216-228`
  - `backend/tests/support/live_port_guard.py:200-210` 与 `:450-462`
  - 既有同族测试 `backend/tests/regression/test_g3_5_vault_keyed_card_states.py`
    （本卡新测试与它同源，请核是否重复覆盖或口径冲突）

差异面可直接看：
`git diff 9400ba26b816e8cad605b2a81e5fdf14e396541e 463fe762593db1f3d7f27aa76a2df0ad4b8b3379`

---

## ⑤ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级列 finding，每条含：

- 一句话结论；
- 依据（文件 + 行号 + 你读到的原文要点）；
- 若判定某条声明不成立，请给出让它不成立的**具体情形**（输入、状态、执行顺序），
  以及该情形是否在本卡声明的覆盖面之内。

若某级别为零，请显式写 `BLOCKER: 0` / `HIGH: 0`，不要省略。
最后给一句总体判断：本卡交付物是否如实、覆盖边界是否被诚实声明。
