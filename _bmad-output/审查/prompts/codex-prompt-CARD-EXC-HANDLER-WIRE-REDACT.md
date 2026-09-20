# 独立复核请求 — CARD-EXC-HANDLER-WIRE-REDACT（8011 暴露面三处异常文本直出边界）

## ① 背景与最小读取面

本次改动把三处「异常文本直出响应边界」一起收口，并把一个从未接线的异常处理器模块接进生产 app。
请只读下面这些位置（**只读，禁写、禁连任何数据库**）：

- `git diff 9c4e7e82 0707be32 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
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

## ② 作者自述（请独立核对，不要采信）

1. `app.core.exceptions` 族（生产真正 raise 的那套）新增了处理器 `core_canvas_exception_handler`，
   映射 `CanvasNotFoundException` / `NodeNotFoundException` → 404、core `ValidationError` → 400、
   其余子类与基类 → 500（500 走与 `generic_exception_handler` 逐字同形的脱敏体 + `bug_id`）。
2. `register_exception_handlers(app, *, override_fastapi_defaults=False)` 接进 `main.py`；
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
