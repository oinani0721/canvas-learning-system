"""Opt-in ``authed_client`` fixture —— 带内部 API key 的 TestClient。

为什么需要它
------------
``app/security.py::require_internal_api_key`` 自 ``c9bb6c9a`` (2026-05-13) 起
是 fail-closed 的: DEBUG=True + 空 ``INTERNAL_API_KEY`` 仅在
``ALLOW_UNSAFE_DEV_AUTH_BYPASS=true`` **且** ``request.client.host`` 是 loopback
时放行 (:110-124)。``TestClient`` 的 client host 恒为 ``"testclient"``, 永远不落
``{"127.0.0.1", "::1"}`` ⇒ 不带 key 的请求恒 503 (:135-142), 挂了该依赖的端点
(``chat.py:48`` router 级 / ``sync.py:63`` 端点级) 业务逻辑一次都执行不到。

``backend/tests/conftest.py:494-517`` 的共享 ``client`` fixture 本来就配了 key
(:490 ``INTERNAL_API_KEY="test-internal-key"``), 但若干测试文件定义了**同名**的
本地 ``client`` fixture (裸 ``TestClient(app)``), 按 pytest 就近覆盖规则静默遮蔽
了共享件。本模块是给这些文件用的显式替代件。

为什么不放进 conftest
--------------------
理由是**限制可发现范围 + 要求显式导入**, 不是「放进 conftest 就会自动给所有测试
加 key」—— 一个具名的非 ``autouse`` fixture 即使定义在 conftest 里, 也仍要被测试或别的
fixture 显式请求才会执行（Codex round-1 LOW-2 更正了本段原先的机制描述）。真正的风险是
**可发现性**: 放进 conftest 后, 整个目录树下任何测试只要写个同名参数就能悄悄拿到 key,
而「鉴权是否生效」恰恰是 ``test_sync_batch_auth.py`` / ``test_system_endpoint_auth.py``
要靠「自己不带 key」来验的 403/503 矩阵。放在 ``tests/support/`` 里, 谁用它谁就得在自己
文件顶部写一行 import, 这行 import 就是审计入口（``grep -rn authed_client``）。与
``tests/support/__init__.py`` 既有约定同向。⛔ 不得加 ``autouse``, 不得写进
``backend/tests/conftest.py`` 或 ``backend/tests/unit/conftest.py``。

为什么不用 os.environ
--------------------
``os.environ`` 是进程级的: 往里写 key (或写 ``ALLOW_UNSAFE_DEV_AUTH_BYPASS``)
会连带影响同一 pytest worker 里其它测试, 且 ``security.py:111`` 读的正是这个
安全开关。本模块只动 ``app.dependency_overrides`` 这一份 per-app 状态, 退出时
**只还原自己加的那个键**。

谁在用 (2026-09-09, CARD-RED-A1-auth)
-------------------------------------
- ``tests/unit/test_chat_endpoint.py``
- ``tests/unit/test_enrich_context_vault_isolation.py``
- ``tests/unit/test_study_question_deep_mode.py``
- ``tests/unit/test_sync_exception_classification.py``

本模块只解开**鉴权**这一层。端点后面的 409 (``vault_scope.py:171``
``resolve_vault_scope`` / ``sync.py:114`` ``resolve_vault_group_id``) 与
schema gate 真连 (``sync.py:107``) 需要调用方各自打桩 —— 先例见
``tests/unit/test_sync_batch_auth.py:98-99``。
"""

from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.security import INTERNAL_API_KEY_HEADER_NAME
from tests.support.lifespan import no_lifespan

#: 与 ``backend/tests/conftest.py:490`` 同值。两处 fixture 在同一文件里混用时,
#: header 与 settings 里的 key 必须逐字相同, 否则 ``security.py`` Branch 4 判 403。
TEST_INTERNAL_API_KEY = "test-internal-key"

#: 「这个键本来不存在」与「这个键本来是 None」的区分哨兵 —— 退出还原时用。
_ABSENT = object()


def authed_settings_override() -> Settings:
    """构造带 ``INTERNAL_API_KEY`` 的测试 Settings。

    ``DEBUG=True`` + CORS 含 localhost 不是装饰: ``app/config.py:286`` 的
    ``is_local`` 由这两项决定, 而 :295-298 在非 local dev 且 key 为空时直接
    ``raise ValueError`` —— 这里 key 非空, 保留 local 组合是为了与
    ``tests/conftest.py:481-491`` 的既有形态逐项对齐, 免得两条路径的 Settings
    在别的字段上分叉。
    """
    return Settings(
        PROJECT_NAME="Canvas Learning System API (Test)",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000",
        CANVAS_BASE_PATH="./test_canvas",
        INTERNAL_API_KEY=TEST_INTERNAL_API_KEY,
    )


@pytest.fixture
def authed_client() -> Generator[TestClient, None, None]:
    """TestClient: 请求自带 ``X-CLS-Internal-Key``, settings 里配了同一个 key。

    三件套:
      1. ``app.dependency_overrides[get_settings]`` → 带 key 的 Settings
         (``require_internal_api_key`` 通过 ``Depends(get_settings)`` 读它);
      2. ``TestClient(app, headers=...)`` → 每个请求自带 key 头, 用例不必逐条手写
         (header 名从 ``app.security`` import, 不抄字面量, 生产改名即跟随);
      3. ``no_lifespan(app)`` → 不跑 ``app.main`` 的 lifespan, 否则起 client 就会
         预热 NEO4J_URI + 跑 DDL + 读 live vault (``tests/conftest.py:498-501``)。

    退出时**只**还原 ``get_settings`` 这一个键: 本来有值就复原原值, 本来没有就
    删除。⛔ 不做 ``app.dependency_overrides.clear()`` —— 无条件 clear 会连带抹掉
    别的 fixture / 用例装的 override。``tests/conftest.py:441-452`` 的 autouse
    ``isolate_dependency_overrides`` 已在每个用例边界做整份快照恢复, 本 fixture
    只需保证自己不越界。

    Yields:
        TestClient: 已过鉴权墙的测试客户端。
    """
    previous = app.dependency_overrides.get(get_settings, _ABSENT)
    app.dependency_overrides[get_settings] = authed_settings_override
    try:
        with (
            no_lifespan(app),
            TestClient(
                app,
                headers={INTERNAL_API_KEY_HEADER_NAME: TEST_INTERNAL_API_KEY},
            ) as test_client,
        ):
            yield test_client
    finally:
        if previous is _ABSENT:
            app.dependency_overrides.pop(get_settings, None)
        else:
            app.dependency_overrides[get_settings] = previous
