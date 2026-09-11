"""Tests for Story 1.10: Detailed health endpoint with 3-level status."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.support.authed_client import authed_client  # noqa: F401 — 由 fixture 请求

#: 见 ``test_startup_health_check.py`` 同名常量: 桩件不抄真实异常文案。
_STUB_DETAIL = "stubbed by unit test: live Neo4j is never dialled here (W4 port gate)"


@pytest.fixture(autouse=True)
def stub_neo4j_probe():
    """把 ``_check_neo4j`` 换成不开 socket 的等价件 (真连点 ``system.py:47-74``)。

    ``detailed_health_check`` :381 在调用时从模块全局解析这个名字, 所以 patch
    模块属性即可。返回 "unhealthy" 是为了复刻**今天这个环境的产物**:
    ``_probe_with_timeout`` :328-333 把它映射成 "unavailable", 于是
    ``test_unavailable_core_returns_503`` 的 503 分支照旧被走到 —— 换成 "healthy"
    会让那条断言变成永远走不到的死分支 (假绿)。
    """
    from app.api.v1.system import ComponentStatus

    stub = AsyncMock(return_value=ComponentStatus(name="neo4j", status="unhealthy", message=_STUB_DETAIL))
    with patch("app.api.v1.system._check_neo4j", stub):
        yield stub


@pytest.fixture
def client(authed_client: TestClient) -> TestClient:  # noqa: F811
    """带 ``X-CLS-Internal-Key`` 的 TestClient (``tests/support/authed_client.py``)。

    ⚠️ 语义收窄如实记录: 原件是 ``TestClient(app, raise_server_exceptions=False)``,
    ``authed_client`` 用的是默认的 ``True``。本文件三条用例走的都是
    ``detailed_health_check`` 的正常返回路径 (组件异常在 ``_probe_with_timeout``
    :350 就被吞成 ComponentHealth), 不依赖「服务端异常被转成 500 响应」这一行为。
    """
    return authed_client


class TestDetailedHealthEndpoint:
    def test_returns_components(self, client):
        resp = client.get("/api/v1/system/health/detailed")
        assert resp.status_code in (200, 503)
        data = resp.json()["data"]
        assert "overall_status" in data
        assert "components" in data
        assert len(data["components"]) >= 3
        assert data["overall_status"] in ("ready", "degraded", "unavailable")

    def test_component_has_required_fields(self, client):
        resp = client.get("/api/v1/system/health/detailed")
        for comp in resp.json()["data"]["components"]:
            assert "name" in comp
            assert "status" in comp
            assert comp["status"] in ("ready", "degraded", "unavailable")
            assert "latency_ms" in comp
            assert "fix_hint" in comp

    def test_unavailable_core_returns_503(self, client):
        resp = client.get("/api/v1/system/health/detailed")
        data = resp.json()["data"]
        neo4j = next((c for c in data["components"] if c["name"] == "neo4j"), None)
        assert neo4j is not None
        if neo4j["status"] == "unavailable":
            assert resp.status_code == 503


class TestAggregateStatus:
    def test_all_ready(self):
        from app.api.v1.system import ComponentHealth, _aggregate_status

        components = [
            ComponentHealth(name="neo4j", status="ready"),
            ComponentHealth(name="ollama", status="ready"),
        ]
        assert _aggregate_status(components) == "ready"

    def test_non_core_unavailable_is_degraded(self):
        from app.api.v1.system import ComponentHealth, _aggregate_status

        components = [
            ComponentHealth(name="neo4j", status="ready"),
            ComponentHealth(name="ollama", status="unavailable"),
        ]
        assert _aggregate_status(components) == "degraded"

    def test_core_unavailable_is_unavailable(self):
        from app.api.v1.system import ComponentHealth, _aggregate_status

        components = [
            ComponentHealth(name="neo4j", status="unavailable"),
            ComponentHealth(name="ollama", status="ready"),
        ]
        assert _aggregate_status(components) == "unavailable"
