# 独立复核请求 — CARD-EXC-HANDLER-WIRE-REDACT（8011 暴露面三处异常文本直出边界）

## ① 背景与最小读取面

本次改动把三处「异常文本直出响应边界」一起收口，并把一个从未接线的异常处理器模块接进生产 app。
请只读下面这些位置（**只读，禁写、禁连任何数据库**）：

- `git diff 9c4e7e82 9e034d60 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
- `backend/app/core/exception_handlers.py` 全文
- `backend/app/main.py:700-860`（`CORSExceptionMiddleware` 类体 + 接线 + 四次 `add_middleware` + `include_router`）
- `backend/app/api/v1/endpoints/review.py:1405-1525`（`/fsrs-state/{concept_id}` 端点）
- `backend/app/core/exceptions.py:1-45`（生产真正 raise 的那套层级）
- `backend/app/exceptions/canvas_exceptions.py:20-110`（另一套同名层级）
- `backend/tests/unit/test_exception_handlers_wire.py` 全文（本卡新增的行为门）
- `backend/tests/regression/test_u9c_startup_rejection_eval.py:1-60,215-262,276-442`
- `backend/tests/regression/test_production_bugs.py:1-70`
- `backend/tests/test_middleware.py:30-80,310-325`（依赖 `override_fastapi_defaults=True` 的既有套件）
- `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/starlette/applications.py:57-76,98-101`
- `_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:503-575`（议题 α 的原始评估）

## ①b 本轮新增：round-1 之后做了什么（请一并核对）

round-1（绑 `0707be32`）报 0 BLOCKER / 0 HIGH + 4 MEDIUM + 2 LOW。round-2 绑 `7d3bdc2b`，
两者之间**只有一个 commit，且只改 `backend/tests/unit/test_exception_handlers_wire.py`，
生产代码零改动**（请用 `git diff 0707be32 7d3bdc2b` 独立核对这一点）。

采纳并整改的三条：

- **MEDIUM-3**：新增 `test_core_family_status_mapping_and_500_redaction`，对 core 族六档
  （`CanvasNotFoundException` / `NodeNotFoundException` / core `ValidationError` /
  已登记异常的子类 / core 基类 / 未登记子类）逐档锁状态码，500 档另锁脱敏体、`bug_id`、
  原文零泄漏与落盘仍有原文。
- **MEDIUM-4**：接线门加**绑定身份**断言（`handlers[Exception] is generic_exception_handler`、
  `handlers[CoreCanvasException] is core_canvas_exception_handler`）。
- **LOW-5**：`bug_log.jsonl` 的断言由「两个片段」升为异常消息**全文**。

登记不改的三条（理由如实写在这里，请判断理由是否成立）：

- **MEDIUM-1**（core 4xx 回显调用方传入值）：卡文明示「不给 4xx 业务文案脱敏」，
  该面已登记进「本卡未证明什么」。
- **MEDIUM-2**（`app.exceptions` 族 500 走 `to_dict()` 原文）：卡文明示
  `override_fastapi_defaults=False` 分支**仍注册**该族（`test_middleware.py` 契约）；
  该族在 `backend/app` 的 `raise` 站点实测为 0。
- **LOW-6**（动态生成的类名进 `error_type`）：理论面，生产无此形态。

本轮请**重点核对**：这三条「登记不改」的理由是否站得住；以及新加的那道门是否存在
门未覆盖的路径（本卡已做两段负控：删掉 `NodeNotFoundException → 404` 映射、把 core 500
的 `message` 改回 `str(exc)`，两段都让该门红在指定档上）。

## ①c round-2 之后做了什么（round-3 绑 `8c4a66a8`）

round-2（绑 `7d3bdc2b`）报 0 BLOCKER / 0 HIGH + 3 MEDIUM + 2 LOW，**五条全部登记不改**
（理由见下）。此后只有一个提交 `8c4a66a8`，**仍只改
`backend/tests/unit/test_exception_handlers_wire.py`，生产代码零改动**
（请用 `git diff 7d3bdc2b 8c4a66a8` 独立核对）。

该提交修的是本卡自己引入的一条目录级红：
`test_production_app_maps_core_canvas_not_found_to_404` 的断言全过（404、由 core 处理器产出），
但 `tests/unit` **目录级**跑时被 conftest 的 W4 哨兵判红 —— canvas 端点的 DI 链在请求期惰性
`initialize()` 一个真 `MemoryService`，它对 `NEO4J_URI` 真跑 driver health_check，命中
`('::1', 7691)` 被拦下（`blocked` 由基线 0 变 1）。单文件跑看不到（该单例已被同文件别的用例
初始化过）。修法是把 `get_memory_service` 覆盖成哑对象，并对两个 override **保存并恢复**原值
而不是直接 `pop`。请核对：这个覆盖是否掩盖了本用例本应测到的东西；保存/恢复的写法是否在
异常路径下也成立。

**round-2 五条的处置（请判断理由是否站得住）**：

1. MEDIUM（`app.exceptions` 族 500 走 `to_dict()` 原文）—— 登记不改。你上一轮指出
   「`test_middleware.py` 约束的是默认 `True` 分支」这条反驳**已被接受**，作者不再以该套件为理由；
   保留注册的真实理由是卡文明确指定该分支仍注册该族，且该族在 `backend/app` 的 `raise` 站点
   实测为 0。改注册形态超出本卡 scope。
2. MEDIUM（响应头泄漏的门未覆盖）—— 登记不改，已写进「本卡未证明什么」。
3. MEDIUM（core 4xx `details` 白名单未被门锁）—— 登记不改，已写进「本卡未证明什么」。
4. LOW（动态类名）—— 登记不改。
5. LOW（u9c 三处过期描述）—— 该行段不在本卡允许改动的行区间内，登记移交。

## ①d round-3 之后做了什么（round-4 绑 `9e034d60`）

round-3（绑 `8c4a66a8`）报 0 BLOCKER / 0 HIGH + 3 MEDIUM + 4 LOW。此后有两个提交，
**都只改 `backend/tests/unit/test_exception_handlers_wire.py`，生产代码零改动**
（请用 `git diff 8c4a66a8 9e034d60` 独立核对）：

- `c2789bd2`（**纯 docstring**）：采纳 r3 LOW-4 后半条 —— 文件头替身清单漏列了两个覆盖。
  等价证明：去掉全部 docstring 后 `ast.dump` 逐字符相同 = True。
- `9e034d60`：round-3 那版 W4 修法**无效**，目录级 `blocked` 仍为 1。真正的根因不是
  「少覆盖一个依赖」，而是**覆盖键的对象身份漂移**：`tests/unit/test_cross_canvas_removal.py:39`
  会 `importlib.reload(app.dependencies)`，字母序在本文件之前，于是目录级跑里
  `app.dependencies.get_canvas_service` 已是新对象，而 `canvas.py` 的路由在 import 时绑定的是
  旧对象 —— 拿新对象当键等于覆盖了一个没人要的键，请求照样走真 `CanvasService`
  （它读 `settings.canvas_base_path`，并在依赖里惰性初始化真 `MemoryService` 连 7691）。
  断言仍然全过（真 `CanvasService` 对不存在的白板同样抛 `CanvasNotFoundException`），
  所以只有 W4 哨兵看得见。两层修法：(1) 覆盖键改取 `canvas.py` 路由自己绑定的那个函数对象
  `CanvasServiceDep.__metadata__[0].dependency`；(2) 再用 `monkeypatch` 换掉
  `app.services.memory_service.get_memory_service` 模块属性兜底（`get_canvas_service` 体内是
  运行时 import）。

本卡为此做了一段负控（把键改回「现取」并拆掉第二层兜底）：最小复现组合
（先跑那个 reload 的文件、再跑本文件）下 `blocked` 由 0 变 1 且该用例 FAILED；
还原后 `shasum` 逐字节相同。

**请重点核对**：
1. 这个两层修法是否**掩盖**了本用例本应测到的东西 —— 特别是它现在还能不能证明
   「生产 app 上 core 族落 404」这条命题；
2. `__metadata__[0].dependency` 这个取键方式在 `Annotated` 结构变化时会不会静默取错；
3. r3 的 3 MEDIUM + 3 条未采纳的 LOW 全部**登记不改**（响应头门、`details` 白名单门、
   另两支子类继承门、core 500 完整键集门、动态类名、u9c 越界行段），理由是协议对
   MEDIUM/LOW 是登记不阻断、且其中数条的行段不在本卡允许改动范围内。请判断这些理由是否成立，
   以及是否有哪一条其实是 BLOCKER/HIGH 被错分了级。

## ② 作者自述（请独立核对，不要采信）

1. `app.core.exceptions` 族（生产真正 raise 的那套）新增了处理器 `core_canvas_exception_handler`，
   映射 `CanvasNotFoundException` / `NodeNotFoundException` → 404、core `ValidationError` → 400、
   其余子类与基类 → 500（500 走与 `generic_exception_handler` 逐字同形的脱敏体 + `bug_id`）。
2. `register_exception_handlers` 的开关**默认值是 `True`**（保持既有裸调用套件的契约），
   生产在 `main.py` 显式传 `False`（round-1 已纠正过作者摘要里的措辞）；
   `False` 时跳过 `HTTPException` / `RequestValidationError` 两行，运行期
   `app.main.app.exception_handlers[starlette.exceptions.HTTPException]`
   与 `[RequestValidationError]` 仍是 FastAPI 自带函数**本体**（身份比较）。
3. `CORSExceptionMiddleware` 的 500 体不再含 `safe_message`；原文仍进服务端日志（`[:200]`）
   与 `bug_tracker.log_error`（`bug_log.jsonl` 全文 + 栈）。
4. `main.py` 的中间件层序注释改成与 Starlette 1.0.0 `insert(0, …)` 语义一致
   （外→内 = Metrics → CORS → Encoding → CORSException）。
5. `/review/fsrs-state` 的 `except` 分支 200 体 `reason` 只剩异常类型名。

## ③ 请按重要性回答的问题

0. 脱敏之后，是否仍有**别的通道**把异常原文送进响应？请具体检查 `error_type`（类名本身）、
   `X-Request-ID`、CORS 头、core 族 4xx 体的 `details` 字典、以及 4xx 业务文案里回显的调用方输入。
1. core 族处理器把「canvas 不存在」从 500 变 404，是否会改变**端点自接 `except` 分支之外**的
   既有消费者语义（例如只看状态码分支的插件 / 前端调用点）？
2. `Exception` 处理器接上后，`ServerErrorMiddleware` 在 `TestClient(raise_server_exceptions=True)`
   （默认值）下会把异常再抛一次 —— 是否有既有测试因此从「拿到 500 响应」变成「异常抛进测试」？
3. 两套同名 `CanvasException`（`app.exceptions` 与 `app.core.exceptions`）同时作为键存在于
   `app.exception_handlers` 里，是否存在 MRO / 分派歧义？
4. 提交时用 `LEFTHOOK_EXCLUDE=spec-sync-flat,spec-sync-root` 跳过了 openapi 再生。
   本卡自述「再生 diff 只有 `x-generated-at` 一行」是否成立？有没有本应体现在 schema 里的差异被漏掉？
5. `pyright` 报 0 errors 是否靠 `cast(...)` 掩盖了真实类型问题？
6. u9c 那条口径钉翻转后，是否仍保留了「产出方是中间件」的排他判据？
7. 新增的行为门里，是否存在**门未覆盖的路径** —— 即把生产改回去某种形态后，该门仍然全绿？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line`，并说明**什么输入**会让它出问题（哪条输入未被拦下）。
描述问题时请使用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类措辞。

## ⑤ 边界

只读；不连任何数据库；不评 β（D-38 legacy 兼容重做，本批不排）；
不评 `ErrorHandlerMiddleware`（`app/middleware/error_handler.py`）的去留；
不评 `review.py` 另 7 处 `HTTPException(detail=…str(e))` 的 `detail` 口径（相邻面，已登记移交）。
