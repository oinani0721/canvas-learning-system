"""FR-KG-04 Phase 4 Task 4.6: HTTP exception classification at /sync/batch.

Story: openspec change fix-fr-kg-04-schema-drift-and-sync-hardening.

The previous endpoint returned 503 for every exception, masking logic bugs
behind a "Neo4j unavailable" message. This test suite verifies the new
classification:

- ServiceUnavailable / AuthError / ConnectionError → 503
- Neo4jError (non-service) / ValueError / TypeError / anything else → 500

Response bodies must NOT contain raw exception text (no internal paths,
driver state, or stack traces leaked to the client).
"""

from __future__ import annotations

from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from neo4j.exceptions import AuthError, ServiceUnavailable

from app.config import Settings, get_settings
from app.main import app
from tests.support.authed_client import TEST_INTERNAL_API_KEY, authed_client  # noqa: F401


SAMPLE_PAYLOAD = {
    "canvas_id": "test-canvas",
    # P0-SYNC-ISO-2026-08-17: vault_id 必填
    "vault_id": "test_vault",
    "subject_id": "test-subject",
    "operations": [
        {
            "operation_id": "00000000-0000-0000-0000-000000000001",
            "entity_type": "node",
            "entity_id": "node-1",
            "operation": "create",
            "payload": {"title": "t", "content": "c"},
            "timestamp": "2026-04-07T00:00:00Z",
        }
    ],
}


def _dev_settings() -> Settings:
    """Dev-mode settings that let the auth dependency through.

    CARD-RED-A1-auth: 本 helper 原先返回 ``INTERNAL_API_KEY=""``，依据的是
    ``c9bb6c9a`` (2026-05-13) **之前**的「DEBUG=True + 空 key → 放行」矩阵。
    该分支已被收紧为「还要 ``ALLOW_UNSAFE_DEV_AUTH_BYPASS=true`` 且 client.host
    是 loopback」(``security.py:110-124``)，而 ``TestClient`` 的 host 恒为
    ``"testclient"`` ⇒ 空 key 恒 503。所以「让请求过鉴权」现在只能靠**显式配 key**，
    值取 ``authed_client`` 用的同一个 —— 用例仍在自己的第一行装这份 override。
    两份 Settings 只在**鉴权相关字段**上一致（``DEBUG=True`` + 同一个 ``INTERNAL_API_KEY``）；
    ``PROJECT_NAME`` / ``CORS_ORIGINS`` 等其余字段并不相同，不是整份逐字等价
    （Codex round-1 LOW-3 实证）。鉴权路径只读这两个字段，所以断言路径不变。
    """
    return Settings(
        PROJECT_NAME="Test",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
        INTERNAL_API_KEY=TEST_INTERNAL_API_KEY,
    )


@pytest.fixture
def client(authed_client: TestClient) -> Generator[TestClient, None, None]:
    """带 key 的 TestClient + ``/sync/batch`` 在鉴权之后那两道墙的桩。

    CARD-RED-A1-auth: 原本是裸 ``TestClient(app)`` + 零桩。解开鉴权后请求会往下
    撞两处与「异常分类」无关的墙，两个桩都照 ``test_sync_batch_auth.py:98-99``
    的先例：

    - ``sync.py:107`` ``get_canvas_schema_gate().block_reason()`` 每次请求都真连
      ``NEO4J_URI`` 做 SHOW CONSTRAINTS，关掉 lifespan 拦不住请求期这条连接。
      桩的 ``block_reason`` 返回 ``None``，与「未知态放行」的实际行为逐字一致。
    - ``sync.py:114`` ``resolve_vault_group_id`` 在「请求 vault ≠ 进程 active
      vault」时 409 fail-closed。本文件测的是**异常分类矩阵**，不是 vault 隔离；
      不把 ``SAMPLE_PAYLOAD["vault_id"]`` 声明成 active vault，六条断言会全变 409，
      淹没真正要测的 503/500 分流信号。

    ``sync.py:126`` 的 ``assert_identity`` **不必**再打桩：
    ``tests/unit/conftest.py:395-418`` 的 autouse ``_stub_vault_identity_registry``
    已把 ``get_vault_identity_registry()`` 换成 no-op（``_NoopRegistry.assert_identity``
    在 :412-413）。

    ⛔ 不做 ``app.dependency_overrides.clear()``：用例自己装的 override 由
    ``tests/conftest.py:441-452`` 的 autouse ``isolate_dependency_overrides`` 在用例
    边界整份恢复，``authed_client`` 只还原它自己加的那个键。
    """
    gate = MagicMock()
    gate.block_reason = AsyncMock(return_value=None)
    with (
        patch("app.config.get_current_vault_id", return_value=SAMPLE_PAYLOAD["vault_id"]),
        patch("app.services.schema_gate.get_canvas_schema_gate", return_value=gate),
    ):
        yield authed_client


def _override_sync_service_raising(exc: BaseException) -> Any:
    """Return a patch context manager that makes SyncService raise ``exc``."""

    async def raiser(*args: Any, **kwargs: Any) -> None:
        raise exc

    return patch(
        "app.services.sync_service.SyncService.process_sync_batch",
        new=AsyncMock(side_effect=raiser),
    )


# ---------------------------------------------------------------------------
# 503 branch: infrastructure failures
# ---------------------------------------------------------------------------


class TestInfrastructureErrors:
    """ServiceUnavailable, AuthError, ConnectionError → 503."""

    def test_service_unavailable_returns_503(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(ServiceUnavailable("neo4j down")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 503
        body = response.json()
        # Fixed, non-leaky message
        assert body["detail"] == "Neo4j unavailable"
        # Raw exception text must not appear in the response
        assert "neo4j down" not in str(body)

    def test_auth_error_returns_503(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(AuthError("bad creds")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 503
        assert response.json()["detail"] == "Neo4j unavailable"

    def test_connection_error_returns_503(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(ConnectionError("refused")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 503
        assert response.json()["detail"] == "Neo4j unavailable"


# ---------------------------------------------------------------------------
# 500 branch: logic errors
# ---------------------------------------------------------------------------


class TestLogicErrors:
    """Logic bugs (ValueError, TypeError, unexpected exceptions) → 500."""

    def test_value_error_returns_500(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(ValueError("unexpected payload shape")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 500
        body = response.json()
        # Fixed, generic message — no raw exception content
        assert body["detail"] == "Sync batch failed unexpectedly"
        assert "unexpected payload shape" not in str(body)

    def test_type_error_returns_500(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(TypeError("int has no len()")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 500
        assert response.json()["detail"] == "Sync batch failed unexpectedly"

    def test_generic_exception_returns_500(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings

        class UnknownError(Exception):
            """A custom exception never seen before."""

        with _override_sync_service_raising(UnknownError("mystery")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 500
        body = response.json()
        assert body["detail"] == "Sync batch failed unexpectedly"
        assert "mystery" not in str(body)
