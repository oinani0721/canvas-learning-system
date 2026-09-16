# 复核请求 — CARD-U9C-EVAL（评估卡，零生产改动）

你在只读沙箱内复核一张**评估卡**的交付物。请按下面五节阅读并给出 finding。

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`
分支 `card/t4-g3`，本卡起点 commit `9400ba26b816e8cad605b2a81e5fdf14e396541e`，
当前 HEAD `b0abea797aa1edce1c1250949a751151428ff428`（本卡两个 commit）。

---

## ① 本卡范围

这张卡**不改任何生产代码**。`backend/app/**` 全程只读。改动面只有两类：

1. 新增一个回归测试文件 `backend/tests/regression/test_u9c_startup_rejection_eval.py`
   （**5 条**用例：实例化层 3 条 + HTTP 层 2 条）；
2. 新增一份评估文档 `_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md`
   及其证据目录 `_bmad-output/审查/evidence-u9c-eval/`；
3. **审查辅助材料**（round-2 补记，此前申报遗漏）：本 prompt 文件
   `_bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md` 与历轮存档
   `_bmad-output/审查/codex-review-CARD-U9C-EVAL-r*.md`。无生产影响。

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

**声明 B（round-1 后已反向重写）— 消息**会**进响应体**：
`VaultScopeUnresolved` 是裸 `Exception` 子类（`vault_scope.py:359`），无专用处理器。
`register_exception_handlers` **生产从未被调用**（运行时 `app.main.app.exception_handlers`
的键只有 `HTTPException` / `RequestValidationError` / `WebSocketRequestValidationError`），
故 `generic_exception_handler` 在此路径上是死代码；真正接住路由异常的是
`CORSExceptionMiddleware`（`main.py:634` 定义、`:757` 注册），它的
`safe_message`（`:709-715`）就是 `str(e)`、无脱敏，取前 500 字符放进
`:738-741` 的 `message`。
⇒ 设计稿「请求 500 **带 CARD-G3-5 消息**」在生产栈上**成立**；
本卡初稿的「屏蔽」结论已撤回。

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
   - HTTP 层**两条**用例是否各自证明了自己测的是哪一层（分层指纹 `error_type`
     的在 / 不在），是否存在某种情形让它们在没有真正区分开的情况下仍然通过；
   - 「仅 handler ⇒ 屏蔽」与「加中间件 ⇒ 不屏蔽」两条断言方向相反，
     是否确实只由中间件挂没挂这一个变量决定。
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
`git diff 9400ba26b816e8cad605b2a81e5fdf14e396541e b0abea797aa1edce1c1250949a751151428ff428`

---

## ⑤ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级列 finding，每条含：

- 一句话结论；
- 依据（文件 + 行号 + 你读到的原文要点）；
- 若判定某条声明不成立，请给出让它不成立的**具体情形**（输入、状态、执行顺序），
  以及该情形是否在本卡声明的覆盖面之内。

若某级别为零，请显式写 `BLOCKER: 0` / `HIGH: 0`，不要省略。
最后给一句总体判断：本卡交付物是否如实、覆盖边界是否被诚实声明。


---

## ⑥ round-2 补充：上一轮的处置

round-1 给出 BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 2，**全部采纳，无驳回**。
本轮请重点核「整改本身是否正确、是否引入新问题」：

- **H1**：已确认成立，并在本卡实测中得到**更强**的结论 ——
  不只是「最小 app 不代表生产」，而是 `register_exception_handlers`
  **生产从未被调用**（运行时打印 `app.main.app.exception_handlers` 的键，
  只有 `HTTPException` / `RequestValidationError` /
  `WebSocketRequestValidationError`，没有 `Exception`）。
  评估文档 ③ 整节已反向重写；新增用例
  `test_production_stack_exposes_message_in_500_body` 挂真
  `CORSExceptionMiddleware`，断言消息原文进 500 体。
  两条 HTTP 用例现各自断言 `error_type` 的在/不在作分层指纹。
  请核：这个更强的结论是否成立？两条用例是否真能区分它们各自声称的那一层？
- **M1**：已改写为「后果取决于端点是否把工厂调用包进 `try` + 解析到哪个 vault」，
  并把 `/review/fsrs-state` 用 HTTP 200 返回带原文 `reason` 这一条作为**新发现**登记。
  请核该表述是否仍有过强之处。
- **M2**：负控 docstring 已按「覆盖什么 / 不覆盖什么 / 未覆盖的由谁接住」逐条改写。
  请核那两条「接住者」的指认是否正确。
- **M3**：已改为「依赖为 singleton，重入不重建」。
- **L1**：地盘核存档已入库。
- **L2**：`unit-20260916T144844.txt` 末行 `rc=0` 与正文矛盾，根因是第二条 `echo`
  重新计算了 `$pipestatus`。**历史存档保持原样不改**（事后改它等于伪造），
  更正与正确写法写在评估文档 §6.5。请核这个处置是否恰当。

另有一处本卡自报的问题请一并核：`backend/data/bug_log.jsonl` 现存 1 条记录，
来自本卡在 pytest **之外**运行的 scratchpad 探针（该处 `tests/conftest.py`
对 `app.main.bug_tracker` 的重定向不在场）。pytest 路径零写已用跑前/跑后
`sha256` + `mtime` 对照加验伪锚证明（存档
`evidence-u9c-eval/zero-write-proof-20260916T190821.txt`）。
该文件被 gitignore、未入库，登记在评估文档 §7.4 交主 session 处置。
请核这个零写证明是否充分、处置是否恰当。
