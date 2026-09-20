# Canvas Learning System - Global Exception Handlers
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
"""
Global exception handlers for Canvas Learning System FastAPI application.

This module provides centralized exception handling for all API endpoints,
ensuring consistent error response formatting across the application.

Exception Handler Registry:
- app.exceptions.CanvasException: 带 .code/.to_dict() 的那套层级（生产从不 raise，
  见 CARD-EXC-HANDLER-WIRE-REDACT 的两套层级说明）
- app.core.exceptions.CanvasException: 生产真正 raise 的那套（404/400/500 显式映射）
- HTTPException: Standard FastAPI HTTP exceptions（仅 override_fastapi_defaults=True）
- RequestValidationError: Pydantic validation errors（仅 override_fastapi_defaults=True）
- Exception: Generic fallback handler

[Source: specs/data/error-response.schema.json - Error response format]
[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md - Error handling design]
"""

from typing import Any, Dict, cast

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from app.core.bug_tracker import bug_tracker
from app.core.exceptions import CanvasException as CoreCanvasException
from app.core.exceptions import CanvasNotFoundException, NodeNotFoundException
from app.core.exceptions import ValidationError as CoreValidationError
from app.exceptions import CanvasException

# Get logger instance
logger = structlog.get_logger(__name__)


async def canvas_exception_handler(
    request: Request,
    exc: CanvasException,
) -> JSONResponse:
    """
    Handle CanvasException and its subclasses.

    Converts Canvas-specific exceptions to standardized JSON responses
    following the error-response.schema.json format.

    Args:
        request: The incoming HTTP request
        exc: The CanvasException instance

    Returns:
        JSONResponse with error payload

    Example:
        ```python
        raise CanvasNotFoundError("my_canvas")
        # Returns: {"code": 404, "message": "Canvas 'my_canvas' not found", "details": {...}}
        ```

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
    # Pattern: @app.exception_handler(CustomException)

    [Source: specs/data/error-response.schema.json]
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "canvas_exception",
        request_id=request_id,
        error_type=type(exc).__name__,
        error_code=exc.code,
        error_message=exc.message,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.code,
        content=exc.to_dict(),
        headers={"X-Request-ID": request_id},
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Handle FastAPI HTTPException.

    Converts standard HTTPException to the standardized error response format.

    Args:
        request: The incoming HTTP request
        exc: The HTTPException instance

    Returns:
        JSONResponse with error payload

    Example:
        ```python
        raise HTTPException(status_code=404, detail="Item not found")
        # Returns: {"code": 404, "message": "Item not found"}
        ```

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
    # Pattern: Reusing default handlers with custom preprocessing

    [Source: specs/data/error-response.schema.json]
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "http_exception",
        request_id=request_id,
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url.path),
    )

    # Build response body matching error-response.schema.json
    body: Dict[str, Any] = {
        "code": exc.status_code,
        "message": str(exc.detail) if exc.detail else "HTTP Error",
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers={"X-Request-ID": request_id},
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic RequestValidationError.

    Converts validation errors to a user-friendly error response format
    with detailed field-level error information.

    Args:
        request: The incoming HTTP request
        exc: The RequestValidationError instance

    Returns:
        JSONResponse with error payload including validation details

    Example:
        Request body missing required field 'name':
        # Returns: {"code": 400, "message": "Validation error", "details": {...}}

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
    # Pattern: Custom validation error handling

    [Source: specs/data/error-response.schema.json]
    [Source: specs/data/error-detail.schema.json]
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Extract validation error details
    errors = exc.errors()
    error_details = []

    for error in errors:
        # Format location as dot-separated path
        loc = error.get("loc", [])
        field = ".".join(str(x) for x in loc if x != "body")

        error_details.append(
            {
                "field": field,
                "message": error.get("msg", "Invalid value"),
                "code": error.get("type", "validation_error"),
            }
        )

    logger.warning(
        "validation_exception",
        request_id=request_id,
        error_count=len(errors),
        errors=error_details,
        path=str(request.url.path),
    )

    # Build response body matching error-response.schema.json
    body: Dict[str, Any] = {
        "code": 400,
        "message": "Validation error",
        "details": {
            "errors": error_details,
        },
    }

    return JSONResponse(
        status_code=400,
        content=body,
        headers={"X-Request-ID": request_id},
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle all unhandled exceptions as a fallback.

    This handler catches any exception that wasn't caught by more
    specific handlers, ensuring a consistent error response.

    IMPORTANT: In production, this should NOT expose internal error details.

    Args:
        request: The incoming HTTP request
        exc: The unhandled exception

    Returns:
        JSONResponse with generic error payload including bug_id for tracking

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)

    [Source: specs/data/error-response.schema.json]
    [Source: docs/stories/21.5.3.story.md - AC-1, AC-2]
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # ✅ Story 21.5.3 AC-1: 自动记录500错误到bug_log.jsonl
    # 收集请求参数用于bug追踪
    request_params: Dict[str, Any] = {
        "path": str(request.url.path),
        "method": request.method,
        "query_params": dict(request.query_params),
    }

    # 尝试获取请求体（如果可用）
    try:
        # 注意：request.body()是async的，但此处我们使用state缓存的body
        if hasattr(request.state, "body"):
            request_params["body"] = request.state.body
    except Exception:
        pass  # 忽略body获取失败

    # 记录bug到JSONL文件
    bug_id = bug_tracker.log_error(
        endpoint=str(request.url.path),
        error=exc,
        request_params=request_params,
        request_id=request_id,
    )

    logger.error(
        "unhandled_exception",
        request_id=request_id,
        bug_id=bug_id,
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=str(request.url.path),
        exc_info=True,  # Include stack trace in logs
    )

    # ✅ Story 21.5.3 AC-2: 返回响应包含bug_id
    # Generic error response - don't expose internal details, but include bug_id
    body: Dict[str, Any] = {
        "code": 500,
        "message": "Internal server error",
        "bug_id": bug_id,  # 用于用户反馈和问题追踪
    }

    return JSONResponse(
        status_code=500,
        content=body,
        headers={"X-Request-ID": request_id},
    )


# ═══════════════════════════════════════════════════════════════════════════
# CARD-EXC-HANDLER-WIRE-REDACT — app.core.exceptions 族
# ═══════════════════════════════════════════════════════════════════════════

# 显式状态映射。**不**按类名猜、**不**读异常自带的 code（core 族根本没有
# `.code` 属性），未登记的子类与基类一律落 500 —— 新增一个 core 异常却忘了
# 登记时，用户看到的是脱敏的 500 而不是一个猜出来的 4xx。
_CORE_STATUS_RULES: tuple[tuple[type[CoreCanvasException], int], ...] = (
    (CanvasNotFoundException, 404),
    (NodeNotFoundException, 404),
    (CoreValidationError, 400),
)


def _core_exception_status(exc: CoreCanvasException) -> int:
    """按显式映射取状态码；未登记者 → 500。

    用 `isinstance` 顺序匹配而不是 `type(exc)` 查表：将来若有人给
    `CanvasNotFoundException` 加子类，它应当继承 404，而不是静默掉进 500。
    三条规则的类互不继承，顺序无歧义。
    """
    for exc_type, status in _CORE_STATUS_RULES:
        if isinstance(exc, exc_type):
            return status
    return 500


def _core_exception_details(exc: CoreCanvasException) -> Dict[str, Any]:
    """收集 core 异常自带的定位属性，供 4xx 体的 `details` 使用。

    只取白名单里的三个属性（`app/core/exceptions.py` 的构造函数设的就是这三个），
    **不**做 `__dict__` 全量导出 —— 后者会把将来某个子类塞进去的任何东西
    （可能含服务端路径）一并送出体外。
    """
    details: Dict[str, Any] = {}
    for attr in ("canvas_name", "node_id", "field"):
        value = getattr(exc, attr, None)
        if value is not None:
            details[attr] = value
    return details


async def core_canvas_exception_handler(
    request: Request,
    exc: CoreCanvasException,
) -> JSONResponse:
    """Handle `app.core.exceptions.CanvasException` 族 —— 生产真正 raise 的那一套。

    ⚠️ **两套同名层级**（DD-13 名实一致，CARD-EXC-HANDLER-WIRE-REDACT 实测）：

      - `app.exceptions.CanvasException`（本模块 import 的那个，由
        `canvas_exception_handler` 服务）带 `.code` / `.to_dict()`，但
        `backend/app` 里**没有任何生产代码 raise 它**；
      - `app.core.exceptions.CanvasException`（本处理器服务的这个）是裸
        `Exception` 子类，**无** `.code`、**无** `.to_dict()`；
        `canvas_service` / `canvas.py` / `agents.py` / `review_service` raise 的是它。

    把 core 族交给 `canvas_exception_handler` 会在读 `exc.code` 时
    `AttributeError` —— 所以「接线」必须是新增本处理器，不是把旧的接上去。

    响应口径：
      - 404 / 400：体 `{"code", "message"[, "details"]}`，`message` 是业务文案
        （`Canvas 'x' not found`，回显的是调用方传入的名字，不含服务端路径）；
      - 500（未登记子类 / 基类）：与 `generic_exception_handler` 逐字同形的脱敏体
        `{"code": 500, "message": "Internal server error", "bug_id": ...}`，
        异常原文只进服务端日志与 `bug_log.jsonl`（α 默认脱敏）。
    """
    request_id = getattr(request.state, "request_id", "unknown")
    status_code = _core_exception_status(exc)

    if status_code >= 500:
        request_params: Dict[str, Any] = {
            "path": str(request.url.path),
            "method": request.method,
            "query_params": dict(request.query_params),
        }
        bug_id = bug_tracker.log_error(
            endpoint=str(request.url.path),
            error=exc,
            request_params=request_params,
            request_id=request_id,
        )
        logger.error(
            "core_canvas_exception",
            request_id=request_id,
            bug_id=bug_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            status_code=status_code,
            path=str(request.url.path),
            exc_info=True,
        )
        # 与 generic_exception_handler 同一条脱敏契约：体不带原文，只带 bug_id
        server_body: Dict[str, Any] = {
            "code": 500,
            "message": "Internal server error",
            "bug_id": bug_id,
        }
        return JSONResponse(
            status_code=500,
            content=server_body,
            headers={"X-Request-ID": request_id},
        )

    logger.warning(
        "core_canvas_exception",
        request_id=request_id,
        error_type=type(exc).__name__,
        status_code=status_code,
        path=str(request.url.path),
    )

    body: Dict[str, Any] = {
        "code": status_code,
        "message": str(exc),
    }
    details = _core_exception_details(exc)
    if details:
        body["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=body,
        headers={"X-Request-ID": request_id},
    )


def register_exception_handlers(app: FastAPI, *, override_fastapi_defaults: bool = True) -> None:
    """
    Register all exception handlers with the FastAPI application.

    This function should be called during application startup to
    set up the global exception handling.

    Handler Registration Order (from specific to generic):
    1. app.exceptions.CanvasException - 带 .code/.to_dict() 的层级（生产不 raise）
    2. app.core.exceptions.CanvasException - 生产真正 raise 的层级（404/400/500）
    3. HTTPException - 仅 override_fastapi_defaults=True
    4. RequestValidationError - 仅 override_fastapi_defaults=True
    5. Exception - Generic fallback

    **真实拓扑（Starlette 1.0.0 实测，CARD-EXC-HANDLER-WIRE-REDACT）**：
    `build_middleware_stack` 把 `(500, Exception)` 的处理器交给
    `ServerErrorMiddleware`（**最外层**），其余处理器交给 `ExceptionMiddleware`
    （**最内层**，位于全部 user middleware 之内）。推论有二：

      - `generic_exception_handler` 只在异常逸出**全部** user middleware 时才
        轮得到 —— 生产栈里路由/依赖抛的未处理异常会先被 `main.py` 的
        `CORSExceptionMiddleware.dispatch` 接住，**500 体的脱敏在那里完成**，
        补注册本函数并不改变那条路径的响应；
      - 反过来，core 族处理器在 `ExceptionMiddleware` 就生效，**先于**中间件，
        所以「canvas 不存在」能真正从 500 变成 404。

    Args:
        app: The FastAPI application instance
        override_fastapi_defaults: 是否覆盖 FastAPI 自带的 `HTTPException` /
            `RequestValidationError` 处理器（keyword-only）。

            - `True`（默认）：保持历史行为，四类处理器全挂。`HTTPException`
              的体变成 `{"code","message"}`、`RequestValidationError`
              **422 变 400** 且体变 `{"code","message","details"}`。
              `backend/tests/test_middleware.py` 依赖这套口径。
            - `False`（生产 `main.py` 用）：跳过那两行，保留 FastAPI 默认的
              422 + `{"detail": ...}` —— 它是发布契约（`backend/openapi.json`
              的 422 响应、仓内大量 `== 422` / `["detail"]` 断言都绑在上面）。

    Example:
        ```python
        from fastapi import FastAPI
        from app.core.exception_handlers import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app, override_fastapi_defaults=False)
        ```

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
    # Pattern: @app.exception_handler(ExceptionClass)

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md]
    """
    # Register handlers from most specific to least specific
    # starlette 的 stub 把 handler 形参声明成基类 Exception(逆变), 于是任何
    # 只接受具体异常子类的 handler 都不合签名 —— 这是 stub 与 FastAPI 实际
    # 用法的口径差, 不是本仓代码的错。只做类型层 cast, 行为逐字不变(TAIL T6)。
    app.add_exception_handler(CanvasException, cast(ExceptionHandler, canvas_exception_handler))
    app.add_exception_handler(CoreCanvasException, cast(ExceptionHandler, core_canvas_exception_handler))
    if override_fastapi_defaults:
        app.add_exception_handler(HTTPException, cast(ExceptionHandler, http_exception_handler))
        app.add_exception_handler(RequestValidationError, cast(ExceptionHandler, validation_exception_handler))
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info(
        "exception_handlers_registered",
        override_fastapi_defaults=override_fastapi_defaults,
    )
