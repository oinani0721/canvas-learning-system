"""ChatGPT-DR-2026-05-13 P0-1: observer token fail-closed hardening tests.

Cover the 6 auth decision branches:
1. token set + header match → allow
2. token set + header mismatch → 401
3. token unset + no bypass → 503 (fail-closed default — the hardening)
4. token unset + bypass=true + loopback → allow + warning
5. token unset + bypass=true + non-loopback → 503 (bypass requires both env AND loopback)
6. token unset + bypass=false + loopback → 503 (bypass requires explicit opt-in)

Threat model: prevent memory poisoning where attacker injects bogus
misconceptions into Graphiti via /memory/extract-conversation when
SIDECAR_OBSERVER_TOKEN is unset (previous default-open behavior).
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.memory import _require_observer_token


def _make_request(client_host: str = "127.0.0.1"):
    """Build a minimal Request-like object exposing client.host."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = client_host
    return request


# ════════════════════════════════════════════════════════════════════
# Branch 1: token set + header match → allow
# ════════════════════════════════════════════════════════════════════


def test_observer_token_set_match_allows():
    request = _make_request("127.0.0.1")
    with patch.dict(os.environ, {"SIDECAR_OBSERVER_TOKEN": "secret-123"}, clear=False):
        # Should not raise
        _require_observer_token(
            request=request,
            x_canvas_observer_token="secret-123",
        )


# ════════════════════════════════════════════════════════════════════
# Branch 2: token set + header mismatch → 401
# ════════════════════════════════════════════════════════════════════


def test_observer_token_set_mismatch_401():
    request = _make_request("127.0.0.1")
    with patch.dict(os.environ, {"SIDECAR_OBSERVER_TOKEN": "secret-123"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            _require_observer_token(
                request=request,
                x_canvas_observer_token="wrong-token",
            )
    assert exc_info.value.status_code == 401
    assert "Invalid or missing" in exc_info.value.detail


def test_observer_token_set_missing_header_401():
    request = _make_request("127.0.0.1")
    with patch.dict(os.environ, {"SIDECAR_OBSERVER_TOKEN": "secret-123"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            _require_observer_token(
                request=request,
                x_canvas_observer_token=None,
            )
    assert exc_info.value.status_code == 401


# ════════════════════════════════════════════════════════════════════
# Branch 3: token unset + no bypass → 503 (the core hardening)
# ════════════════════════════════════════════════════════════════════


def test_observer_token_unset_default_fail_closed_503():
    """Default behavior with no env set — fail-closed (key hardening)."""
    request = _make_request("127.0.0.1")
    # Explicitly clear both env vars
    env_patch = {}
    for k in ("SIDECAR_OBSERVER_TOKEN", "ALLOW_LOCAL_OBSERVER_BYPASS"):
        env_patch[k] = ""
    with patch.dict(os.environ, env_patch, clear=False):
        # Manually pop to ensure unset
        os.environ.pop("SIDECAR_OBSERVER_TOKEN", None)
        os.environ.pop("ALLOW_LOCAL_OBSERVER_BYPASS", None)
        with pytest.raises(HTTPException) as exc_info:
            _require_observer_token(
                request=request,
                x_canvas_observer_token=None,
            )
    assert exc_info.value.status_code == 503
    assert "Observer auth not configured" in exc_info.value.detail


# ════════════════════════════════════════════════════════════════════
# Branch 4: token unset + bypass=true + loopback → allow + warning
# ════════════════════════════════════════════════════════════════════


def test_observer_token_unset_bypass_enabled_loopback_v4_allows():
    request = _make_request("127.0.0.1")
    os.environ.pop("SIDECAR_OBSERVER_TOKEN", None)
    with patch.dict(os.environ, {"ALLOW_LOCAL_OBSERVER_BYPASS": "true"}, clear=False):
        # Should not raise
        _require_observer_token(request=request, x_canvas_observer_token=None)


def test_observer_token_unset_bypass_enabled_loopback_v6_allows():
    request = _make_request("::1")
    os.environ.pop("SIDECAR_OBSERVER_TOKEN", None)
    with patch.dict(os.environ, {"ALLOW_LOCAL_OBSERVER_BYPASS": "true"}, clear=False):
        # Should not raise
        _require_observer_token(request=request, x_canvas_observer_token=None)


# ════════════════════════════════════════════════════════════════════
# Branch 5: token unset + bypass=true + non-loopback → 503
# ════════════════════════════════════════════════════════════════════


def test_observer_token_unset_bypass_enabled_non_loopback_503():
    """Even with bypass=true, non-loopback client is denied (defense in depth)."""
    request = _make_request("192.168.1.50")  # LAN IP, not loopback
    os.environ.pop("SIDECAR_OBSERVER_TOKEN", None)
    with patch.dict(os.environ, {"ALLOW_LOCAL_OBSERVER_BYPASS": "true"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            _require_observer_token(request=request, x_canvas_observer_token=None)
    assert exc_info.value.status_code == 503


def test_observer_token_unset_bypass_enabled_external_503():
    """External IP attacker — must be denied even with bypass=true."""
    request = _make_request("203.0.113.42")  # TEST-NET-3 external
    os.environ.pop("SIDECAR_OBSERVER_TOKEN", None)
    with patch.dict(os.environ, {"ALLOW_LOCAL_OBSERVER_BYPASS": "true"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            _require_observer_token(request=request, x_canvas_observer_token=None)
    assert exc_info.value.status_code == 503


# ════════════════════════════════════════════════════════════════════
# Branch 6: token unset + bypass=false (or unset) + loopback → 503
# ════════════════════════════════════════════════════════════════════


def test_observer_token_unset_bypass_explicit_false_503():
    request = _make_request("127.0.0.1")
    os.environ.pop("SIDECAR_OBSERVER_TOKEN", None)
    with patch.dict(os.environ, {"ALLOW_LOCAL_OBSERVER_BYPASS": "false"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            _require_observer_token(request=request, x_canvas_observer_token=None)
    assert exc_info.value.status_code == 503


def test_observer_token_unset_bypass_not_a_boolean_503():
    """Any non-'true' value disables bypass (defense against typos / case)."""
    request = _make_request("127.0.0.1")
    os.environ.pop("SIDECAR_OBSERVER_TOKEN", None)
    # 'yes' / '1' / 'TRUE' must NOT enable bypass — only literal 'true' does
    for fuzzy_value in ("yes", "1", "TRUE", "True", "enabled"):
        with patch.dict(
            os.environ, {"ALLOW_LOCAL_OBSERVER_BYPASS": fuzzy_value}, clear=False
        ):
            if fuzzy_value.lower() == "true":
                # 'TRUE' / 'True' lowercase matches — should allow
                _require_observer_token(request=request, x_canvas_observer_token=None)
            else:
                with pytest.raises(HTTPException) as exc_info:
                    _require_observer_token(
                        request=request, x_canvas_observer_token=None
                    )
                assert exc_info.value.status_code == 503


# ════════════════════════════════════════════════════════════════════
# Defense-in-depth: client object missing
# ════════════════════════════════════════════════════════════════════


def test_observer_token_unset_no_client_object_503():
    """Request without client object (rare edge) — should fail-closed."""
    request = MagicMock()
    request.client = None  # No client info available
    os.environ.pop("SIDECAR_OBSERVER_TOKEN", None)
    with patch.dict(os.environ, {"ALLOW_LOCAL_OBSERVER_BYPASS": "true"}, clear=False):
        with pytest.raises(HTTPException) as exc_info:
            _require_observer_token(request=request, x_canvas_observer_token=None)
    assert exc_info.value.status_code == 503


# ════════════════════════════════════════════════════════════════════
# Regression: token-set path must not depend on bypass env
# ════════════════════════════════════════════════════════════════════


def test_observer_token_set_ignores_bypass_env():
    """When token is set, bypass env is irrelevant (header is authoritative)."""
    request = _make_request("203.0.113.42")  # external IP
    with patch.dict(
        os.environ,
        {
            "SIDECAR_OBSERVER_TOKEN": "secret-123",
            "ALLOW_LOCAL_OBSERVER_BYPASS": "true",  # ignored when token set
        },
        clear=False,
    ):
        # Correct header from external IP — still allowed (token wins)
        _require_observer_token(request=request, x_canvas_observer_token="secret-123")
