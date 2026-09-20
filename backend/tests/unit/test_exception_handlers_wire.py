"""CARD-EXC-HANDLER-WIRE-REDACT — 异常处理器接线 + 500/200 响应体脱敏的行为门。

[BATCH-2026-09-18-第十五批 / CARD-EXC-HANDLER-WIRE-REDACT]

本文件钉四件事，每条都写明**自己测的是哪一层**（分层指纹），以免绿在别的路径上：

  1. **接线**（`test_production_app_wires_core_and_generic_handlers`）：生产
     `app.main.app` 上真的挂了 `app.core.exceptions.CanvasException` 与
     `Exception` 两个处理器，**且** `HTTPException` / `RequestValidationError`
     两键仍是 FastAPI 自带函数**本体**（身份断言 `is`，不是数键数）——
     后者锁的是「接线没有顺手把 422/`detail` 契约换掉」。
  2. **真实层序**（`test_production_middleware_order_matches_starlette_semantics`）：
     Starlette 1.0.0 `add_middleware` = `user_middleware.insert(0, …)`，
     ⇒ **后 add 的在外层**。`main.py` 依次 add CORSException → Encoding →
     CORS → Metrics，所以运行期外→内是 Metrics → CORS → Encoding →
     CORSException。本条锁的是**事实**（Starlette 语义 + add 顺序），不是本卡
     的修复 —— 本卡落地前它就是绿的，它存在的意义是：main.py 那段层序注释
     将来若再被改回「CORSExceptionMiddleware 最外层」，注释与运行期的矛盾
     会有一条可执行的判据指出来。
  3. **500 体脱敏 + 体大小**（`test_middleware_500_body_is_redacted_and_bounded`）：
     生产 `CORSExceptionMiddleware` 接住的未处理异常，响应体只剩泛化文案 +
     `error_type` + `bug_id`；异常原文（含部署绝对路径）零泄漏，且体有界。
     **同时**读回 `bug_log.jsonl` 断言原文仍在 —— 脱敏是「不给调用方」，
     不是「把诊断信息丢掉」；少了这一条，把 `log_error` 一起删掉也能全绿。
  4. **core 族 → 404**（`test_core_canvas_not_found_is_handled_before_middleware`
     与 `test_default_http_exception_contract_survives_wiring`）：生产真正
     `raise` 的是 `app.core.exceptions` 那套层级（`exception_handlers.py` 原先
     绑的 `app.exceptions.CanvasException` 生产从不 raise）。接上 core 族处理器
     后「canvas 不存在」在 `ExceptionMiddleware`（最内层）就变 404，**先于**
     `CORSExceptionMiddleware` 的 500；排他断言是 `error_type` **不在**体里
     —— 那个键是中间件独有指纹，它在 = 处理器没轮到。
  5. **fsrs-state 200 体脱敏**（`test_fsrs_state_error_reason_is_redacted`）：
     `/review/fsrs-state` 的 `except` 分支返回 200 + `reason`，原本是
     `f"error: {e}"`（原文直出），改后只剩类型名。

**本文件替换了哪些真实现（如实全列）**：

  - `app.main.bug_tracker` / `app.core.exception_handlers.bug_tracker` —— 只换
    **落盘路径**（指向 pytest `tmp_path`），`log_error` 行为一行未改；与
    `tests/conftest.py::_neo4j_live_port_guard` 对 `app.main` 的做法同型。
    换它是为了能读回落盘内容做「诊断不丢」断言，不是为了绕过被测逻辑。
  - `app.api.v1.endpoints.review._get_review_service_singleton` —— 替换的是被测
    端点的**上游依赖**（制造「服务层抛异常」这个前置条件），被测的
    `except` 分支本身是真代码；形态与 `tests/api/v1/endpoints/test_fsrs_state_api.py:52`
    既有夹具一致。
  - `CanvasService` 依赖（DI override，只在生产 app 那条 404 用例里）—— 换成一个抛
    `CanvasNotFoundException` 的 **async** 替身，制造被测前置条件。覆盖键取的是
    `canvas.py` 路由**自己绑定**的那个函数对象（见该用例内注释：别的测试 reload 过
    `app.dependencies`，现取会拿到另一个对象）。
  - `app.services.memory_service.get_memory_service`（模块属性 patch，同一条用例）——
    换成哑对象。理由不是「为了让断言过」，而是 canvas 依赖会在请求期惰性
    `initialize()` 一个真 `MemoryService` 并对 `NEO4J_URI` 跑 driver health_check
    （目录级跑里被 W4 哨兵拦下）。本用例不消费 memory 行为。
    ⚠️ 代价如实写明：这条用例因此**不再覆盖**真实 `MemoryService` 初始化链。

  除这四处外，被测链上的中间件、处理器、端点、`TestClient` 全是真实现（DD-03）。

**不连库**：全部进程内 `TestClient`，不触 7691/7687/7692。
"""

from __future__ import annotations

import inspect
import uuid
from typing import Any

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# 工具
# ═══════════════════════════════════════════════════════════════════════════


def _marker() -> str:
    """每次调用都不同的哨兵串：用它判「原文有没有进响应体」。

    用随机串而不是固定字面量，是为了让「体里不含它」这条断言不可能因为
    别处恰好存在同名字符串而假绿。
    """
    return "EXCMARK-" + uuid.uuid4().hex


def _register_production_shape(app_: Any) -> None:
    """按**生产口径**注册处理器：`override_fastapi_defaults=False`。

    先显式断言这个开关存在，再调用。这条断言不是多余的样板：本卡落地前
    `register_exception_handlers` 只有一个位置参数，直接调用会以裸 `TypeError`
    炸在夹具里，先红跑就看不出「红在哪条命题上」。写成断言后，红落在与被测
    命题同义的一句话上，改后它恒真（开关是本卡的交付物之一）。
    """
    from app.core import exception_handlers

    params = inspect.signature(exception_handlers.register_exception_handlers).parameters
    assert "override_fastapi_defaults" in params, (
        "register_exception_handlers 缺 override_fastapi_defaults 开关："
        "生产无法在保留 FastAPI 默认 422/detail 契约的前提下接线"
    )
    exception_handlers.register_exception_handlers(app_, override_fastapi_defaults=False)


def _redirect_bug_log(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Any:
    """把中间件与处理器两条路径的 bug_log 落点都指向 tmp_path，返回该文件路径。

    换的是**别名指向的实例**（落盘位置），不是 `log_error` 的行为；
    `app.core.bug_tracker.bug_tracker` 单例本身不动（它的默认路径契约另有测试在锁）。
    """
    import app.main as main_mod
    from app.core import exception_handlers
    from app.core.bug_tracker import BugTracker

    log_path = tmp_path / "bug_log.jsonl"
    tracker = BugTracker(log_path=str(log_path))
    monkeypatch.setattr(main_mod, "bug_tracker", tracker)
    monkeypatch.setattr(exception_handlers, "bug_tracker", tracker)
    return log_path


# ═══════════════════════════════════════════════════════════════════════════
# 1. 接线锁
# ═══════════════════════════════════════════════════════════════════════════


def test_production_app_wires_core_and_generic_handlers() -> None:
    """生产 app 挂上了 core 族与 `Exception` 处理器，且没动 FastAPI 默认两键。

    分层指纹：用 `is` 比函数**身份**，不是比键的数量 —— 数量判据挡不住
    「键还在但换了实现」这种等长替换（那正是覆盖 422/`detail` 契约的形态）。

    ⚠️ 键的身份实测（2026-09-18 于 `9c4e7e82`）：FastAPI 装默认处理器时用的是
    **`starlette.exceptions.HTTPException`**，不是 `fastapi.HTTPException`
    （后者是前者的子类）。拿 `fastapi.HTTPException` 当键查会 `KeyError`。
    两个键各锁一件事：starlette 那个必须仍是 FastAPI 默认函数本体；
    `fastapi.HTTPException` 必须**不在**表里 —— 它一旦出现，就说明
    `exception_handlers.py` 的 `http_exception_handler`（返回 `{"code","message"}`）
    被挂上了，`detail` 契约即被改写。
    """
    import fastapi.exception_handlers as fastapi_defaults
    from fastapi import HTTPException as FastAPIHTTPException
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    import app.main as main_mod
    from app.core import exception_handlers
    from app.core.exceptions import CanvasException as CoreCanvasException

    handlers = main_mod.app.exception_handlers

    assert CoreCanvasException in handlers, (
        "生产 app 未注册 app.core.exceptions.CanvasException 处理器：生产真正 raise 的就是这一套层级"
    )
    assert Exception in handlers, "生产 app 未注册 Exception 兜底处理器"

    # 绑定身份（Codex r1 MEDIUM-4）：只断言「键存在」挡不住把键错绑到别的处理器
    # —— 例如把 Exception 绑到 canvas_exception_handler（它会去读 core 族没有的
    # `exc.code`，在真正需要兜底的那一刻二次失败）。两条行为用例都到不了 generic
    # 处理器（一条落 core 404、一条落端点自捕获的 200），所以这里必须比函数本体。
    assert handlers[CoreCanvasException] is exception_handlers.core_canvas_exception_handler
    assert handlers[Exception] is exception_handlers.generic_exception_handler

    assert handlers[StarletteHTTPException] is fastapi_defaults.http_exception_handler, (
        "HTTPException 处理器被覆盖 —— FastAPI 默认 detail 契约已被改写"
    )
    assert handlers[RequestValidationError] is fastapi_defaults.request_validation_exception_handler, (
        "RequestValidationError 处理器被覆盖 —— 422 契约已被改写成 400"
    )
    assert FastAPIHTTPException not in handlers, (
        "fastapi.HTTPException 被单独挂了处理器 —— 该路径会把 detail 体换成 code/message"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 2. 真实层序锁（本卡落地前就绿：它锁事实，不锁修复）
# ═══════════════════════════════════════════════════════════════════════════


def test_production_middleware_order_matches_starlette_semantics() -> None:
    """运行期 user_middleware 外→内 = Metrics → CORS → Encoding → CORSException。

    `starlette/applications.py` 的 `add_middleware` 做的是 `insert(0, …)`，
    所以 `user_middleware[0]` 是**最外层**、最后 add 的那个。main.py 的 add
    顺序是 CORSException → Encoding → CORS → Metrics ⇒ 下面这个列表。

    ⚠️ 本条在本卡落地前后都绿。它不证明本卡改了什么，它把「注释说的层序」
    与「运行期真实层序」之间的口径差变成一条可执行判据。
    """
    import app.main as main_mod

    assert [mw.cls.__name__ for mw in main_mod.app.user_middleware] == [
        "MetricsMiddleware",
        "CORSMiddleware",
        "EncodingValidationMiddleware",
        "CORSExceptionMiddleware",
    ]


# ═══════════════════════════════════════════════════════════════════════════
# 3. 500 体脱敏 + 体大小 + 诊断不丢
# ═══════════════════════════════════════════════════════════════════════════


def test_middleware_500_body_is_redacted_and_bounded(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """真 `CORSExceptionMiddleware` 接住的 500：体内零原文、有界，落盘仍全文。

    被测层是生产中间件本体（`from app.main import CORSExceptionMiddleware`），
    异常由一条 probe 路由真抛 —— 注入点在被测层的**上游**，中间件自身没有替身。

    异常消息里塞了三样东西，各锁一个泄漏面：
      - `marker`：随机串，代表任何「异常原文」；
      - `str(tmp_path)`：真实绝对路径，代表部署路径泄漏（T4-D 实测的那一类）；
      - 6000 个 'x'：代表超长消息，用来把「体有界」与「原文被截断后仍进体」区分开
        —— 旧口径 `safe_message[:500]` 下体会涨到 500 字符以上，本条会红。
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.main import CORSExceptionMiddleware

    log_path = _redirect_bug_log(monkeypatch, tmp_path)

    marker = _marker()
    secret_path = str(tmp_path)
    boom_message = f"{marker} {secret_path} " + "x" * 6000

    probe_app = FastAPI()
    probe_app.add_middleware(CORSExceptionMiddleware)

    @probe_app.get("/_boom")
    def _boom() -> dict:
        raise RuntimeError(boom_message)

    client = TestClient(probe_app, raise_server_exceptions=False)
    resp = client.get("/_boom", headers={"origin": "app://obsidian.md"})

    assert resp.status_code == 500
    body = resp.json()

    # 产出方指纹：`error_type` 是中间件独有键，它在 ⇒ 确实是中间件产出的这个 500
    assert body["error_type"] == "RuntimeError"
    assert set(body) == {"code", "message", "error_type", "bug_id"}
    assert body["code"] == 500
    assert body["message"] == "Internal server error"
    assert body["bug_id"]

    # 零泄漏 + 有界
    assert marker not in resp.text
    assert secret_path not in resp.text
    assert "x" * 200 not in resp.text
    assert len(resp.content) < 512

    # CORS 头仍在（本中间件存在的理由，别在脱敏时顺手弄丢）
    assert "access-control-allow-origin" in resp.headers

    # 脱敏 != 丢诊断：服务端落盘仍有原文
    logged = log_path.read_text(encoding="utf-8")
    # 断言**全文**而不是两个片段（Codex r1 LOW-5）：只查 marker 与路径的话，
    # 把 `error=e` 换成 `error=RuntimeError(safe_message[:500])` 照样全绿 ——
    # 6000 字符的尾部已经丢了，门却看不见。
    assert boom_message in logged, "bug_log.jsonl 未落异常消息全文 —— 脱敏把诊断一起丢了"


# ═══════════════════════════════════════════════════════════════════════════
# 4. core 族 → 404（处理器先于中间件） + 默认 422/detail 契约存活
# ═══════════════════════════════════════════════════════════════════════════


def _build_core_family_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Any:
    """最小 app：生产口径接线 + 真 `CORSExceptionMiddleware` + 两条 probe 路由。"""
    from fastapi import FastAPI, HTTPException

    from app.core.exceptions import CanvasNotFoundException
    from app.main import CORSExceptionMiddleware

    _redirect_bug_log(monkeypatch, tmp_path)

    app_ = FastAPI()
    _register_production_shape(app_)
    app_.add_middleware(CORSExceptionMiddleware)

    @app_.get("/_canvas_missing")
    def _canvas_missing() -> dict:
        raise CanvasNotFoundException("nope")

    @app_.get("/_http_422")
    def _http_422() -> dict:
        raise HTTPException(status_code=422, detail="x")

    return app_


def test_core_canvas_not_found_is_handled_before_middleware(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """`CanvasNotFoundException` → 404，且产出方是处理器而不是中间件。

    `ExceptionMiddleware` 位于全部 user middleware 之内，所以注册在 app 上的
    core 族处理器**先于** `CORSExceptionMiddleware.dispatch` 的 `except` 生效。
    排他断言：`error_type` 不在体里 —— 它在就说明这个 404/500 是中间件产出的。
    """
    from fastapi.testclient import TestClient

    app_ = _build_core_family_app(monkeypatch, tmp_path)
    client = TestClient(app_, raise_server_exceptions=False)

    resp = client.get("/_canvas_missing")

    assert resp.status_code == 404, "core 族 CanvasNotFoundException 未被映射成 404"
    body = resp.json()
    assert body["code"] == 404
    assert "nope" in body["message"]
    assert "error_type" not in body, "响应体带中间件指纹 ⇒ core 族处理器没轮到"


def test_default_http_exception_contract_survives_wiring(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """同一个接线过的 app 上，`HTTPException` 仍走 FastAPI 默认 `detail` 契约。

    这条与上一条共用 app：它证明「接上 core 族」和「保住 422/detail」不是
    二选一 —— `override_fastapi_defaults=False` 正是为此存在的开关。
    """
    from fastapi.testclient import TestClient

    app_ = _build_core_family_app(monkeypatch, tmp_path)
    client = TestClient(app_, raise_server_exceptions=False)

    resp = client.get("/_http_422")

    assert resp.status_code == 422
    assert resp.json() == {"detail": "x"}


def test_production_app_maps_core_canvas_not_found_to_404(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """**生产 app**（真路由 + 真接线 + 真中间件）上，core 族异常落 404 而不是 500。

    上面两条用的是最小 app，证明的是「处理器 + 开关」这套组合的行为；本条证明
    `app.main.app` 这个**实际被 uvicorn 跑的对象**上接线确实生效。
    注入点是端点的上游 DI 依赖 `get_canvas_service`（制造「白板不存在」这个前置
    条件），被测的接线 / 处理器 / 中间件 / 路由全是真的。

    ⚠️ **为什么不靠 `tests/regression/test_production_bugs.py::test_bug_bug_1cbf9ae9`**
    （本卡实测，已登记）：那条用例的 autouse fixture 把 `get_canvas_service` 覆盖成
    **同步** `MagicMock`，请求在 `await canvas_service.sync_all_edges_to_neo4j(...)`
    处先抛 `TypeError: 'MagicMock' object can't be awaited` —— 它走不到
    `CanvasNotFoundException`，因此既证不了旧 bug 还在、也证不了 404 化生效。
    本条用一个 **async** 替身把那条链真正走通。

    **两个 DI 覆盖，各自的理由（DD-03 如实列全）**：
      - `get_canvas_service` → 抛 `CanvasNotFoundException` 的 async 替身：制造
        「白板不存在」这个被测前置条件；
      - `get_memory_service` → `MagicMock`：canvas 端点的 DI 链会在**请求期**惰性
        `initialize()` 一个真 `MemoryService`，它对 `NEO4J_URI` 真跑 driver
        health_check（本卡实测：只在 `tests/unit` **目录级**跑里触发，单文件跑时该单例
        已被别的用例初始化过，所以单跑绿、目录级红 —— 被 `conftest` 的 W4 哨兵抓住，
        `blocked=1`）。本用例不消费 memory 行为，覆盖成哑对象；形态与
        `tests/regression/test_production_bugs.py::stub_lazy_service_dependencies` 一致。
        两个 override 都**保存并恢复**原值，不用 `pop` —— 直接 pop 会把别的测试事先设好的
        覆盖一起删掉。
    """
    from unittest.mock import MagicMock

    from fastapi.testclient import TestClient

    import app.services.memory_service as memory_module
    from app.api.v1.endpoints import canvas as canvas_endpoints
    from app.core.exceptions import CanvasNotFoundException
    from app.main import app as production_app
    from tests.support.lifespan import no_lifespan

    _redirect_bug_log(monkeypatch, tmp_path)

    # 命中记录：没有它，本用例分不清 404 是替身产出的还是真 `CanvasService` 产出的
    # —— 真服务对一个不存在的白板**抛的是同一个异常**，响应一模一样（Codex r4 LOW-1）。
    substitute_calls: list[str] = []

    class _MissingCanvasService:
        async def sync_all_edges_to_neo4j(self, canvas_name: str) -> dict:
            substitute_calls.append(canvas_name)
            raise CanvasNotFoundException(canvas_name)

    # ⚠️ 覆盖键必须取**路由自己绑定的那个函数对象**，不能 `from app.dependencies import
    # get_canvas_service` 现取（本卡实测）：`tests/unit/test_cross_canvas_removal.py:39`
    # 会 `importlib.reload(app.dependencies)`，字母序在本文件之前 ⇒ 目录级跑里
    # `app.dependencies.get_canvas_service` 已是**新**对象，而 `canvas.py` 的路由在 import
    # 时就绑定了旧对象。拿新对象当键 = 覆盖一个没人要的键，请求照样走真 `CanvasService`
    # （它会读 `settings.canvas_base_path`，并在依赖里惰性初始化真 `MemoryService` 连 7691）。
    # 单文件跑时两者同一个对象，所以这条只在目录级跑里暴露 —— 也正是 W4 哨兵抓到它的原因。
    canvas_dep_key = canvas_endpoints.CanvasServiceDep.__metadata__[0].dependency

    # 第二层：`get_canvas_service` 体内是**运行时** import + `await get_memory_service()`，
    # 所以换掉模块属性即可，且这一层对上面那种对象身份漂移免疫。
    async def _dummy_memory_service() -> Any:
        return MagicMock()

    monkeypatch.setattr(memory_module, "get_memory_service", _dummy_memory_service)

    overrides = production_app.dependency_overrides
    saved = {canvas_dep_key: overrides.get(canvas_dep_key)}
    overrides[canvas_dep_key] = _MissingCanvasService
    try:
        with no_lifespan(production_app), TestClient(production_app) as client:
            resp = client.post("/api/v1/canvas/exc-wire-missing/sync-edges", json={})
    finally:
        for dep, original in saved.items():
            if original is None:
                overrides.pop(dep, None)
            else:
                overrides[dep] = original

    # 排他断言先行：证明这次请求确实走的是本用例注入的替身，而不是真 `CanvasService`
    # （后者读 `settings.canvas_base_path`，并会在依赖里惰性初始化真 `MemoryService`）。
    assert substitute_calls == ["exc-wire-missing"], (
        "DI 替身没被调用 —— 覆盖键失配了，这个 404 是真 CanvasService 产出的，"
        f"本用例证明不了接线（实际调用记录：{substitute_calls}）"
    )

    assert resp.status_code == 404, (
        f"生产 app 未把 CanvasNotFoundException 映射成 404，实得 {resp.status_code}: {resp.text[:200]}"
    )
    body = resp.json()
    assert body["code"] == 404
    assert "exc-wire-missing" in body["message"]
    # 排他断言：`error_type` 是中间件独有指纹，它在 ⇒ 这个响应不是处理器产出的
    assert "error_type" not in body


# ═══════════════════════════════════════════════════════════════════════════
# 4b. core 族状态映射全覆盖 + core 500 脱敏（Codex r1 MEDIUM-3）
# ═══════════════════════════════════════════════════════════════════════════


def _core_probe_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Any, exc: BaseException) -> Any:
    """最小 app：生产口径接线 + 真 `CORSExceptionMiddleware` + 一条抛 `exc` 的路由。"""
    from fastapi import FastAPI

    from app.main import CORSExceptionMiddleware

    app_ = FastAPI()
    _register_production_shape(app_)
    app_.add_middleware(CORSExceptionMiddleware)

    @app_.get("/_raise")
    def _raise() -> dict:
        raise exc

    return app_


def test_core_family_status_mapping_and_500_redaction(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """core 族**每一档**都按显式映射落状态码，且 500 档同样脱敏。

    上面那两条 core 用例只制造了 `CanvasNotFoundException`，于是「删掉
    `NodeNotFoundException → 404`」「删掉 `ValidationError → 400`」「把 core 500 的
    `message` 改回 `str(exc)`」「让已登记异常的子类掉进 500」这四种对照输入
    **都不会让门变红**（Codex r1 MEDIUM-3）。本条把这四档一次锁住。

    500 档还多锁一件事：core 基类与未登记子类走的是与 `generic_exception_handler`
    逐字同形的脱敏体 —— 体里没有 `error_type`（那是中间件指纹，它在就说明
    处理器没轮到），也没有异常原文。
    """
    from fastapi.testclient import TestClient

    from app.core.exceptions import (
        CanvasException as CoreCanvasException,
    )
    from app.core.exceptions import (
        CanvasNotFoundException,
        NodeNotFoundException,
    )
    from app.core.exceptions import (
        ValidationError as CoreValidationError,
    )

    class _UnregisteredCanvasError(CoreCanvasException):
        """core 基类的子类，但**没有**登记进状态映射 —— 应落 500。"""

    class _NotFoundSubclass(CanvasNotFoundException):
        """已登记异常的子类 —— 应**继承** 404，而不是掉进 500。"""

    log_path = _redirect_bug_log(monkeypatch, tmp_path)
    secret = _marker()

    cases = [
        (CanvasNotFoundException(f"board-{secret}"), 404, False),
        (NodeNotFoundException(f"node-{secret}", f"board-{secret}"), 404, False),
        (CoreValidationError(f"bad-{secret}", field="color"), 400, False),
        (_NotFoundSubclass(f"sub-{secret}"), 404, False),
        (CoreCanvasException(f"base-{secret}"), 500, True),
        (_UnregisteredCanvasError(f"unmapped-{secret}"), 500, True),
    ]

    for exc, expected_status, expect_redacted in cases:
        app_ = _core_probe_app(monkeypatch, tmp_path, exc)
        client = TestClient(app_, raise_server_exceptions=False)
        resp = client.get("/_raise")
        label = type(exc).__name__

        assert resp.status_code == expected_status, (
            f"{label}: 期望 {expected_status}，实得 {resp.status_code} — {resp.text[:200]}"
        )
        body = resp.json()
        assert body["code"] == expected_status, label
        # 排他断言：`error_type` 是中间件独有键，它在 ⇒ 产出方不是 core 族处理器
        assert "error_type" not in body, f"{label}: 响应体带中间件指纹，处理器没轮到"

        if expect_redacted:
            assert body["message"] == "Internal server error", f"{label}: core 500 未脱敏"
            assert body["bug_id"], f"{label}: core 500 体缺 bug_id"
            assert secret not in resp.text, f"{label}: core 500 体带异常原文"
        else:
            # 4xx 档回显的是**调用方传入的**值（业务文案），这是本卡有意保留的口径
            assert secret in body["message"], f"{label}: 4xx 业务文案丢了调用方输入"
            assert "bug_id" not in body, f"{label}: 4xx 不该记 bug"

    # 两条 500 档的原文仍进服务端落盘（脱敏 != 丢诊断）
    logged = log_path.read_text(encoding="utf-8")
    assert f"base-{secret}" in logged
    assert f"unmapped-{secret}" in logged


# ═══════════════════════════════════════════════════════════════════════════
# 5. /review/fsrs-state 200 体脱敏
# ═══════════════════════════════════════════════════════════════════════════


def test_fsrs_state_error_reason_is_redacted(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """`/review/fsrs-state` 的 `except` 分支：200 + `reason` 只剩异常类型名。

    注入点是端点的上游依赖 `_get_review_service_singleton`（制造「服务层抛」
    这个前置条件），被测的 `except` 分支是真代码，走的是真生产 app。
    """
    from fastapi.testclient import TestClient

    import app.api.v1.endpoints.review as review_mod
    from app.main import app as production_app
    from tests.support.lifespan import no_lifespan

    marker = _marker()
    secret_path = str(tmp_path)

    class _BoomReviewService:
        async def get_fsrs_state(self, concept_id: str) -> dict:
            raise RuntimeError(f"{marker} {secret_path}")

    async def _boom_singleton() -> Any:
        return _BoomReviewService()

    monkeypatch.setattr(review_mod, "_get_review_service_singleton", _boom_singleton)

    with no_lifespan(production_app), TestClient(production_app) as client:
        resp = client.get("/api/v1/review/fsrs-state/exc-wire-probe")

    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is False
    assert data["reason"] == "error: RuntimeError", "fsrs-state 的 reason 仍带异常原文（或类型名口径不符）"
    assert marker not in resp.text
    assert secret_path not in resp.text
