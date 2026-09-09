# Sprint 1.2 — Phase 2: /sync/batch internal API key authentication
# Story: openspec change fix-fr-kg-04-schema-drift-and-sync-hardening
#
# TDD: tests written FIRST, before implementation.
"""
Tests for the internal API key dependency on POST /api/v1/sync/batch.

Fail-closed matrix:
    DEBUG  INTERNAL_API_KEY  request_key   expected
    True   ""                missing       200 (dev convenience, warning logged)
    True   "tk"              missing       403 (key configured, must match)
    True   "tk"              "tk"          200
    False  ""                missing       503 (fail-closed, no key configured)
    False  "tk"              missing       403
    False  "tk"              "wrong"       403
    False  "tk"              "tk"          200
"""

from __future__ import annotations

import logging
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.models.sync_models import SyncBatchResponse
from tests.support.lifespan import no_lifespan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


SAMPLE_PAYLOAD = {
    "canvas_id": "test_canvas",
    # P0-SYNC-ISO-2026-08-17: vault_id 必填 (缺失 → 422, 在 auth 之外)
    "vault_id": "test_vault",
    "subject_id": "test_subject",
    "operations": [
        {
            "operation_id": "00000000-0000-0000-0000-000000000001",
            "entity_type": "board",
            "entity_id": "test_canvas",
            "operation": "create",
            "payload": {"name": "Test Board"},
            "timestamp": "2026-04-06T00:00:00Z",
        }
    ],
}

# A successful sync response object — used as the canned return value of the
# patched SyncService so the auth tests do not depend on Neo4j being up.
EMPTY_OK_RESPONSE = SyncBatchResponse(results=[], synced_count=0, failed_count=0)


def _settings_factory(*, debug: bool, key: str):
    """Build a get_settings override that returns the requested DEBUG/key combo.

    CARD-RED-A2 (2026-09-09) — 为什么 ``debug=False, key=""`` 这一档要走
    ``model_construct``：

    该档过去建不出 ``Settings``。``app/config.py::validate_security_defaults``
    是个 ``@model_validator(mode="after")``，``is_local`` 要求 ``DEBUG=True``
    且 CORS 含 localhost；``DEBUG=False`` + 空 key 命中 ``raise ValueError(
    "INTERNAL_API_KEY required outside local dev. ...")``。异常抛在这个
    override 闭包里 = **请求处理期**，被 ``app/main.py::CORSExceptionMiddleware``
    兜成 **500** —— 请求根本没走到 ``app/security.py``。于是这一档过去测到的
    是配置层而非它声称要测的鉴权层（失败身份 ``assert 500 == 503``；
    bug_tracker 记的 ``error_type`` 是 ``ValidationError``，不是 HTTPException）。

    ``model_construct`` 跳过 pydantic 校验（含 after-validator）与 ``.env``
    读取，按传入值 + 各字段 Field 默认值直接装配，让请求真正撞到
    ``security.py`` 的 Branch 1（fail-closed 503）。

    ⚠️ 这**不是**放宽 ``validate_security_defaults``：生产代码一字未改，进程
    启动装配 ``Settings()`` 时它照样拦得住空 key。改的只是「测试如何造出
    『运维忘了配 key』的那个非法配置」—— 而那正是 Branch 1 声称要防的现实
    场景。其余档位（``debug=True`` 或已配 key）仍走原来的 ``Settings(...)``。
    """

    fields = dict(
        PROJECT_NAME="Canvas Learning System API (Test)",
        VERSION="1.0.0-test",
        DEBUG=debug,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
        INTERNAL_API_KEY=key,
    )

    def override() -> Settings:
        if not debug and not key:
            settings = Settings.model_construct(**fields)
            # 自检：model_construct 不过校验，必须确认它没把关键字段跳成别的值。
            # ⚠️ NEO4J_PASSWORD 断言的是 Field 默认 ""，它**证明不了**「该档没读
            # .env」—— .env 里不设这个键、只设别的键时它同样是 ""。「不读 .env」
            # 的依据是 model_construct 本身不走 BaseSettings 的取值链（只有真
            # ``Settings(...)`` 才会把 .env 与 init kwargs 合并后再校验）；下面
            # 四条断言只用来确认字段值符合预期，不承担那个证明。
            assert settings.DEBUG is False
            assert settings.INTERNAL_API_KEY == ""
            assert settings.CORS_ORIGINS == "http://localhost:3000"
            assert settings.NEO4J_PASSWORD == ""
            return settings
        return Settings(**fields)

    return override


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    """A TestClient that bypasses the real SyncService so we test auth alone.

    CARD-G2-2 (2026-08-28): 同时把 SAMPLE_PAYLOAD 的 vault 声明为进程
    active vault。409 fail-closed 生效后, 「请求 vault ≠ active vault」
    会在鉴权**之后**被拒 —— 本文件测的是鉴权矩阵, 不是 vault 隔离,
    不激活就会让每条 200 断言变成 409, 淹没真正的鉴权回归信号。

    CARD-TEST-isolate-lifespan: schema_gate 一并打桩 —— /sync/batch 每次
    请求都会真连 NEO4J_URI 做 SHOW CONSTRAINTS（verify 失败按「未知态」
    放行），关掉 lifespan 拦不住这条请求期连接。桩的 block_reason 返回
    None，与被拦时的实际放行行为逐字一致，不改变任何断言路径。
    """
    gate = MagicMock()
    gate.block_reason = AsyncMock(return_value=None)
    with (
        patch(
            "app.services.sync_service.SyncService.process_sync_batch",
            new=AsyncMock(return_value=EMPTY_OK_RESPONSE),
        ),
        patch("app.config.get_current_vault_id", return_value=SAMPLE_PAYLOAD["vault_id"]),
        patch("app.services.schema_gate.get_canvas_schema_gate", return_value=gate),
    ):
        with no_lifespan(app), TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Production (DEBUG=False) — strict fail-closed matrix
# ---------------------------------------------------------------------------


class TestProductionFailClosed:
    """When DEBUG=False, missing or wrong keys MUST be rejected."""

    def test_no_key_configured_fails_closed_503(
        self, auth_client: TestClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(debug=False, key="")
        with caplog.at_level(logging.ERROR, logger="app.security"):
            caplog.clear()
            response = auth_client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 503, (
            "DEBUG=False with empty INTERNAL_API_KEY must fail closed (503), not silently allow"
        )
        assert "not configured" in response.json()["detail"].lower()
        # CARD-RED-A2: 上面两条断不出「被哪一层拒的」—— security.py 的 Branch 1
        # (prod + 空 key) 与 Branch 2 (dev + 空 key + 无 bypass) 都返回 503，而且
        # Branch 2 的 detail **以 Branch 1 的整句为前缀**（它是那句后面接
        # "... Set INTERNAL_API_KEY env for production, or
        # ALLOW_UNSAFE_DEV_AUTH_BYPASS=true for loopback dev." 的长文案）——
        # 所以任何 `in` 形式的 detail 断言都分辨不了层，只有 `==` 可以。
        # 下面两条把判据绑到 Branch 1 的身份上：
        #   ① detail 精确等值；
        #   ② 发出 Branch 1 那条 logger.error 的**函数** + 带括号的完整标记。
        #      ⚠️ 不能用裸 token 子串匹配 caplog.text：security.py 的 WebSocket
        #      侧分支用同一个 logger、同样是 ERROR 级别，其标记以 "ws_" 打头
        #      因而**包含**那个裸 token，裸子串判据会把它误判成命中。
        #      security.py 刻意用 stdlib logging 而非 structlog（见其模块注释）
        #      正是为了让 caplog 捕得到这条记录。
        assert response.json()["detail"] == "Internal API key not configured"
        assert any(
            r.name == "app.security"
            and r.levelno == logging.ERROR
            and r.funcName == "require_internal_api_key"
            and "(auth_fail_closed)" in r.getMessage()
            for r in caplog.records
        ), "expected the Branch 1 fail-closed record emitted by require_internal_api_key"

    def test_missing_header_returns_403(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(debug=False, key="real-key")
        response = auth_client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 403
        assert "invalid" in response.json()["detail"].lower()

    def test_wrong_key_returns_403(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(debug=False, key="real-key")
        response = auth_client.post(
            "/api/v1/sync/batch",
            json=SAMPLE_PAYLOAD,
            headers={"X-CLS-Internal-Key": "wrong-key"},
        )
        assert response.status_code == 403

    def test_correct_key_grants_access(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(debug=False, key="real-key")
        response = auth_client.post(
            "/api/v1/sync/batch",
            json=SAMPLE_PAYLOAD,
            headers={"X-CLS-Internal-Key": "real-key"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["synced_count"] == 0
        assert body["failed_count"] == 0


# ---------------------------------------------------------------------------
# Development (DEBUG=True) — convenience: allow missing key with warning
# ---------------------------------------------------------------------------


class TestDevelopmentConvenience:
    """When DEBUG=True, missing INTERNAL_API_KEY is allowed (with warning)."""

    def test_dev_mode_no_key_now_fails_closed_503_p0_2(self, auth_client: TestClient) -> None:
        """ChatGPT-DR-2026-05-13 P0-2: DEBUG=True + empty key now fails closed (503).

        Previous contract (pre-P0-2): DEBUG+empty=200 (silent fail-open dev bypass).
        New contract (P0-2 hardening): DEBUG+empty=503 unless explicit env opt-in
        ALLOW_UNSAFE_DEV_AUTH_BYPASS=true AND client.host is loopback.

        TestClient client.host defaults to "testclient" (not loopback), so even
        with the env set, this test still returns 503 — confirming defense in
        depth. The bypass + loopback path is covered by unit-level test in
        test_internal_api_key_p0_2_hardening.py using mocked Request objects.
        """
        app.dependency_overrides[get_settings] = _settings_factory(debug=True, key="")
        response = auth_client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)

        assert response.status_code == 503
        assert "Internal API key not configured" in response.json().get("detail", "")

    def test_dev_mode_with_key_still_enforces(self, auth_client: TestClient) -> None:
        """Even in DEBUG mode, if a key IS configured, it must match."""
        app.dependency_overrides[get_settings] = _settings_factory(debug=True, key="dev-key")
        # Missing key → 403 (key was configured, so it must match)
        response = auth_client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------


class TestHeaderParsing:
    """The header name MUST be exactly X-CLS-Internal-Key (case-insensitive)."""

    def test_canonical_header_name(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(debug=False, key="abc")
        response = auth_client.post(
            "/api/v1/sync/batch",
            json=SAMPLE_PAYLOAD,
            headers={"X-CLS-Internal-Key": "abc"},
        )
        assert response.status_code == 200
