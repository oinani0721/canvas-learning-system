"""ChatGPT-DR-2026-05-13 P0-2: require_internal_api_key fail-closed hardening tests.

Cover the hardened Branch 2 (DEBUG+empty key) decision matrix:
1. token set + match → allow
2. token set + mismatch → 403
3. token set + missing header → 403
4. DEBUG=False + token unset → 503 (Branch 1, unchanged)
5. DEBUG=True + token unset + no bypass → 503 (P0-2 hardening — was 200 before)
6. DEBUG=True + token unset + bypass=true + loopback → allow + warning
7. DEBUG=True + token unset + bypass=true + non-loopback → 503 (defense in depth)
8. DEBUG=True + token unset + bypass=false + loopback → 503

Unit-level approach using mocked Request objects, complementary to the
integration-level tests in test_sync_batch_auth.py / test_system_endpoint_auth.py
which use FastAPI TestClient (whose client.host="testclient" != loopback).

Threat model: prevent silent fail-open in dev mode that previously let any
LAN/external client through to sensitive write endpoints when DEBUG=True
and INTERNAL_API_KEY was unset.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.security import require_internal_api_key


def _make_request(client_host: str = "127.0.0.1"):
    """Build a minimal Request-like object exposing client.host."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = client_host
    return request


def _make_settings(debug: bool, key: str):
    """Build a Settings-like object with DEBUG and INTERNAL_API_KEY attrs."""
    settings = MagicMock()
    settings.DEBUG = debug
    settings.INTERNAL_API_KEY = key
    return settings


# ════════════════════════════════════════════════════════════════════
# Branch: token set + match → allow
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_token_set_match_allows():
    request = _make_request("127.0.0.1")
    settings = _make_settings(debug=False, key="secret-123")
    await require_internal_api_key(
        request=request,
        provided_key="secret-123",
        settings=settings,
    )


# ════════════════════════════════════════════════════════════════════
# Branch: token set + mismatch → 403
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_token_set_mismatch_403():
    request = _make_request("127.0.0.1")
    settings = _make_settings(debug=False, key="secret-123")
    with pytest.raises(HTTPException) as exc_info:
        await require_internal_api_key(
            request=request,
            provided_key="wrong-key",
            settings=settings,
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_token_set_missing_header_403():
    request = _make_request("127.0.0.1")
    settings = _make_settings(debug=False, key="secret-123")
    with pytest.raises(HTTPException) as exc_info:
        await require_internal_api_key(
            request=request,
            provided_key=None,
            settings=settings,
        )
    assert exc_info.value.status_code == 403


# ════════════════════════════════════════════════════════════════════
# Branch 1: DEBUG=False + token unset → 503 (unchanged production fail-closed)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_prod_no_key_503():
    request = _make_request("127.0.0.1")
    settings = _make_settings(debug=False, key="")
    with pytest.raises(HTTPException) as exc_info:
        await require_internal_api_key(
            request=request,
            provided_key=None,
            settings=settings,
        )
    assert exc_info.value.status_code == 503


# ════════════════════════════════════════════════════════════════════
# Branch 2 HARDENED: DEBUG=True + token unset + no bypass → 503
# (the core P0-2 hardening — previously was 200)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dev_no_key_no_bypass_now_503():
    request = _make_request("127.0.0.1")
    settings = _make_settings(debug=True, key="")
    os.environ.pop("ALLOW_UNSAFE_DEV_AUTH_BYPASS", None)
    with pytest.raises(HTTPException) as exc_info:
        await require_internal_api_key(
            request=request,
            provided_key=None,
            settings=settings,
        )
    assert exc_info.value.status_code == 503
    assert "Internal API key not configured" in exc_info.value.detail


@pytest.mark.asyncio
async def test_dev_no_key_bypass_false_503():
    """Bypass explicitly disabled → 503 even on loopback."""
    request = _make_request("127.0.0.1")
    settings = _make_settings(debug=True, key="")
    with patch.dict(os.environ, {"ALLOW_UNSAFE_DEV_AUTH_BYPASS": "false"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            await require_internal_api_key(
                request=request,
                provided_key=None,
                settings=settings,
            )
    assert exc_info.value.status_code == 503


# ════════════════════════════════════════════════════════════════════
# Branch 2 HARDENED allow: DEBUG=True + token unset + bypass=true + loopback
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dev_bypass_enabled_loopback_v4_allows():
    request = _make_request("127.0.0.1")
    settings = _make_settings(debug=True, key="")
    with patch.dict(os.environ, {"ALLOW_UNSAFE_DEV_AUTH_BYPASS": "true"}, clear=False):
        await require_internal_api_key(
            request=request,
            provided_key=None,
            settings=settings,
        )


@pytest.mark.asyncio
async def test_dev_bypass_enabled_loopback_v6_allows():
    request = _make_request("::1")
    settings = _make_settings(debug=True, key="")
    with patch.dict(os.environ, {"ALLOW_UNSAFE_DEV_AUTH_BYPASS": "true"}, clear=False):
        await require_internal_api_key(
            request=request,
            provided_key=None,
            settings=settings,
        )


# ════════════════════════════════════════════════════════════════════
# Branch 2 HARDENED reject: DEBUG=True + bypass=true but non-loopback → 503
# (defense in depth — bypass alone insufficient)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dev_bypass_enabled_lan_503():
    """Bypass=true but LAN IP → 503 (defense in depth)."""
    request = _make_request("192.168.1.100")
    settings = _make_settings(debug=True, key="")
    with patch.dict(os.environ, {"ALLOW_UNSAFE_DEV_AUTH_BYPASS": "true"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            await require_internal_api_key(
                request=request,
                provided_key=None,
                settings=settings,
            )
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_dev_bypass_enabled_external_503():
    """Bypass=true but external IP attacker → 503 (defense in depth)."""
    request = _make_request("203.0.113.42")  # TEST-NET-3
    settings = _make_settings(debug=True, key="")
    with patch.dict(os.environ, {"ALLOW_UNSAFE_DEV_AUTH_BYPASS": "true"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            await require_internal_api_key(
                request=request,
                provided_key=None,
                settings=settings,
            )
    assert exc_info.value.status_code == 503


# ════════════════════════════════════════════════════════════════════
# Defense in depth: client object missing
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dev_no_client_object_503():
    """Request without client object (edge case) → 503 fail-closed."""
    request = MagicMock()
    request.client = None
    settings = _make_settings(debug=True, key="")
    with patch.dict(os.environ, {"ALLOW_UNSAFE_DEV_AUTH_BYPASS": "true"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            await require_internal_api_key(
                request=request,
                provided_key=None,
                settings=settings,
            )
    assert exc_info.value.status_code == 503


# ════════════════════════════════════════════════════════════════════
# Regression: bypass env irrelevant when token configured
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_token_set_ignores_bypass_env():
    """When token is set, bypass env is irrelevant (header is authoritative)."""
    request = _make_request("203.0.113.42")  # external
    settings = _make_settings(debug=True, key="secret-123")
    with patch.dict(os.environ, {"ALLOW_UNSAFE_DEV_AUTH_BYPASS": "true"}, clear=False):
        # Correct header from external IP → still allowed (token wins)
        await require_internal_api_key(
            request=request,
            provided_key="secret-123",
            settings=settings,
        )


# ════════════════════════════════════════════════════════════════════
# Regression: bypass=true with token set + wrong header → 403 (not 200)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_token_set_bypass_env_wrong_header_403():
    """When token is set, bypass=true does NOT downgrade auth strictness."""
    request = _make_request("127.0.0.1")
    settings = _make_settings(debug=True, key="secret-123")
    with patch.dict(os.environ, {"ALLOW_UNSAFE_DEV_AUTH_BYPASS": "true"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            await require_internal_api_key(
                request=request,
                provided_key="wrong",
                settings=settings,
            )
    assert exc_info.value.status_code == 403
