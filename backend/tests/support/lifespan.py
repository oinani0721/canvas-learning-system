"""lifespan 隔离基元 —— 端点测试走真实 router，但不跑 ``app.main`` 的启动副作用。

[BATCH-2026-09-01-第八批 / CARD-TEST-isolate-lifespan]

## 问题

``with TestClient(app)``（app 来自 ``app.main``）会触发 Starlette 的 lifespan，
即 ``backend/app/main.py`` 的 :func:`~app.main.lifespan`。那条链会：

* 连 ``settings.NEO4J_URI`` 预热 MemoryService —— ``backend/.env`` 里是
  ``bolt://localhost:7691``，**现网库**；
* 对现网库执行 ``CREATE FULLTEXT INDEX episode_content IF NOT EXISTS``
  （幂等 DDL 也是对现网的 DDL）；
* LanceDB ``recover_pending`` / EventBus ``recover_outbox``（写
  ``backend/data/outbox/events.jsonl``）；
* ``episode_worker.initialize_graphiti`` 裸 driver 探活；
* 按 ``settings.canvas_base_path`` eager-build wikilink 图 —— 读 **live vault**。

也就是说：跑一次单元测试 = 连一次生产数据库 + 动一次生产库的 schema + 读一遍
用户的真实笔记库。

## 解法

Starlette 把 lifespan 存在 ``app.router.lifespan_context``
（``starlette/routing.py`` 的 ``Router.__init__``）。把它临时换成一个 no-op
异步上下文，``TestClient.__enter__`` 照常建起 portal、路由表照常是真的，
只是启动副作用整条不跑。

**被测端点仍然走真实 router**：``no_lifespan`` 不碰 ``app.routes``、不碰
``app.dependency_overrides``、不碰任何端点函数。请求路径、依赖注入、中间件、
响应模型全部原样。它只关掉「启动时做什么」。

## 用法

    from tests.support.lifespan import no_lifespan

    @pytest.fixture
    def client():
        from app.main import app

        with no_lifespan(app), TestClient(app) as c:
            yield c

⚠️ ``no_lifespan`` 必须包住整个 ``with TestClient(...)`` 块，而不只是构造：
lifespan 的 startup 在 ``__enter__``、shutdown 在 ``__exit__``，两头都在块内。
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:  # pragma: no cover - 仅供类型检查
    from fastapi import FastAPI


@contextlib.asynccontextmanager
async def _noop_lifespan(app: Any):
    """什么都不做的 lifespan：yield 进去，yield 出来。"""
    yield


@contextlib.contextmanager
def no_lifespan(app: "FastAPI") -> Iterator["FastAPI"]:
    """临时把 ``app.router.lifespan_context`` 换成 no-op，退出时恢复原值。

    保存/恢复而不是永久替换，因为 ``app.main.app`` 是**进程级单例**：同一次
    pytest 会话里，别的测试（尤其 integration/e2e）可能确实要跑真实 lifespan。
    嵌套使用是安全的（各自存各自的原值，后进先出）。

    Args:
        app: FastAPI 应用实例。通常是 ``app.main.app``。

    Yields:
        同一个 app 实例（方便 ``with no_lifespan(app) as a:`` 的写法）。
    """
    router = app.router
    original = router.lifespan_context
    router.lifespan_context = _noop_lifespan
    try:
        yield app
    finally:
        router.lifespan_context = original


@contextlib.contextmanager
def lifespan_lite(app: "FastAPI") -> Iterator["FastAPI"]:
    """no_lifespan + 只装配 **进程内** 的 mastery 融合对象。

    对应 ``app/main.py`` 里 Story 5.6 那一段（``MasteryEngine`` + ``SignalRegistry``
    + ``MasteryFusionEngine`` + ``set_mastery_engine`` + 三个 ``app.state`` 字段）。
    **不连库、不建图、不做任何 recover**。

    给谁用：某个端点测试确实依赖「fusion engine 已挂上」这个启动后状态，而
    ``get_mastery_engine()`` 的惰性兜底（``mastery_engine.py`` 的
    ``if _engine_instance is None: _engine_instance = MasteryEngine(...)``）
    造出来的是**没有 fusion engine** 的裸引擎，两者行为不同。

    退出时把全局单例与 ``app.state`` 恢复原状 —— ``set_mastery_engine`` 写的是模块级
    全局，不恢复就会漏给同会话后面的测试。
    """
    from app.services import mastery_engine as mastery_module
    from app.services.mastery_engine import MasteryEngine
    from app.services.mastery_fusion import MasteryFusionEngine
    from app.services.signal_registry import (
        BKTMasterySignal,
        CalibrationBiasSignal,
        ExamScoreSignal,
        FSRSRetrievabilitySignal,
        SelfConfidenceSignal,
        SignalRegistry,
    )

    _UNSET = object()
    prev_global = mastery_module._engine_instance
    prev_state = {
        name: getattr(app.state, name, _UNSET) for name in ("mastery_engine", "signal_registry", "fusion_engine")
    }

    engine = MasteryEngine()
    registry = SignalRegistry()
    registry.register(BKTMasterySignal(engine, None))
    registry.register(FSRSRetrievabilitySignal(engine))
    registry.register(ExamScoreSignal())
    registry.register(CalibrationBiasSignal())
    registry.register(SelfConfidenceSignal())
    fusion = MasteryFusionEngine(registry)
    engine.set_fusion_engine(fusion)

    mastery_module.set_mastery_engine(engine)
    app.state.mastery_engine = engine
    app.state.signal_registry = registry
    app.state.fusion_engine = fusion

    try:
        with no_lifespan(app):
            yield app
    finally:
        mastery_module._engine_instance = prev_global
        for name, value in prev_state.items():
            if value is _UNSET:
                if hasattr(app.state, name):
                    delattr(app.state, name)
            else:
                setattr(app.state, name, value)
