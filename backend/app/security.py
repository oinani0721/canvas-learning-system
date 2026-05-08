"""Internal API key authentication for backend sensitive endpoints.

FR-KG-04 Phase 2 of openspec change fix-fr-kg-04-schema-drift-and-sync-hardening.

The `/api/v1/sync/batch` endpoint writes directly to Neo4j and was previously
unauthenticated, allowing any process bound to the loopback interface (e.g.
hostile sidecar, accidental script) to corrupt the canvas graph. This module
implements a device-scoped API key check using `fastapi.security.APIKeyHeader`
following the FastAPI Security documentation pattern.

Fail-closed matrix:

| DEBUG | INTERNAL_API_KEY | header | result                                |
|-------|------------------|--------|---------------------------------------|
| True  | empty            | any    | allow + structured warning (dev mode) |
| True  | configured       | match  | allow                                 |
| True  | configured       | wrong  | 403 Forbidden                         |
| True  | configured       | absent | 403 Forbidden                         |
| False | empty            | any    | 503 Service Unavailable (fail-closed) |
| False | configured       | match  | allow                                 |
| False | configured       | wrong  | 403 Forbidden                         |
| False | configured       | absent | 403 Forbidden                         |

The 503 path in production prevents accidental "naked" deployments where the
operator forgot to set INTERNAL_API_KEY — instead of letting writes through
unauthenticated, every request gets a clear "key not configured" error.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings

# Use stdlib logging here (not structlog) so that pytest caplog can capture
# auth events for the test_sync_batch_auth.py regression suite. The sync.py
# endpoint that mounts this dependency also uses stdlib logging, so the
# styles stay aligned.
logger = logging.getLogger(__name__)

#: Header name used by the frontend api-client to forward the device key.
#: Must match the value sent by `frontend/src/services/api-client.ts`.
INTERNAL_API_KEY_HEADER_NAME = "X-CLS-Internal-Key"

#: FastAPI security scheme. ``auto_error=False`` so we can manage the
#: fail-closed matrix manually instead of letting FastAPI raise 403 by default.
INTERNAL_API_KEY_HEADER = APIKeyHeader(
    name=INTERNAL_API_KEY_HEADER_NAME,
    auto_error=False,
    description=(
        "Device-scoped internal API key. Required for sync/batch and other "
        "sensitive write endpoints. Configured via the INTERNAL_API_KEY "
        "environment variable on the backend and VITE_INTERNAL_API_KEY on "
        "the frontend Tauri build."
    ),
)


async def require_internal_api_key(
    provided_key: Optional[str] = Depends(INTERNAL_API_KEY_HEADER),
    settings: Settings = Depends(get_settings),
) -> None:
    """FastAPI dependency that enforces the internal API key fail-closed matrix.

    Raises ``HTTPException(403)`` when a configured key does not match,
    ``HTTPException(503)`` when no key is configured in production mode.

    Args:
        provided_key: Value of the ``X-CLS-Internal-Key`` request header
            (or ``None`` when the header is absent).
        settings: Application settings (injected so that test overrides
            via ``app.dependency_overrides[get_settings]`` work as expected).

    Returns:
        ``None`` on success — the dependency is used purely for its
        side effects (raising on auth failure).
    """
    configured_key = (settings.INTERNAL_API_KEY or "").strip()
    debug_mode = bool(settings.DEBUG)

    # Branch 1: production + no configured key → fail closed (503)
    # Operator forgot to provision the key; never let writes through.
    if not configured_key and not debug_mode:
        logger.error(
            "INTERNAL_API_KEY env var is empty in production mode "
            "(auth_fail_closed); refusing request — header_present=%s",
            bool(provided_key),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal API key not configured",
        )

    # Branch 2: dev + no configured key → allow with warning
    # Convenience for local development without sacrificing observability.
    if not configured_key and debug_mode:
        logger.warning(
            "INTERNAL_API_KEY is not configured but DEBUG=True; "
            "allowing request (dev mode auth_dev_bypass) — header_present=%s",
            bool(provided_key),
        )
        return None

    # Branch 3: configured key, request missing the header → 403
    if not provided_key:
        logger.warning(
            "X-CLS-Internal-Key header missing (auth_reject); rejecting request"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal API key",
        )

    # Branch 4: configured key, header value does not match → 403
    if provided_key != configured_key:
        logger.warning(
            "Provided X-CLS-Internal-Key does not match configured key "
            "(auth_reject); rejecting request"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal API key",
        )

    # Branch 5: configured key, header matches → allow
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Round-23 Story 7.5 · Patch 5 — WebSocket auth (Round-14 / ChatGPT 残缺补丁)
# ═══════════════════════════════════════════════════════════════════════════════

# WebSocket close codes (RFC 6455 §7.4.1):
#   1008: Policy Violation (auth fail / key mismatch)
#   1011: Server Error (key not configured in production)
WS_CLOSE_POLICY_VIOLATION = 1008
WS_CLOSE_SERVER_ERROR = 1011

#: Query parameter name for WebSocket auth token.
#: Browser WebSocket API doesn't support custom headers, so token goes in query string.
WS_TOKEN_QUERY_NAME = "token"


async def verify_websocket_internal_key(websocket) -> bool:
    """Round-23 Story 7.5 — WebSocket auth using INTERNAL_API_KEY via query string.

    与 REST require_internal_api_key 共享同一 fail-closed matrix:

    | DEBUG | INTERNAL_API_KEY | token | result                          |
    |-------|------------------|-------|---------------------------------|
    | True  | empty            | any   | accept + warn (dev mode)        |
    | True  | configured       | match | accept                          |
    | True  | configured       | wrong | close 1008 Policy Violation     |
    | True  | configured       | absent| close 1008 Policy Violation     |
    | False | empty            | any   | close 1011 Server Error         |
    | False | configured       | match | accept                          |
    | False | configured       | wrong | close 1008 Policy Violation     |
    | False | configured       | absent| close 1008 Policy Violation     |

    Args:
        websocket: FastAPI WebSocket instance (查 query_params 拿 token).

    Returns:
        True 鉴权通过 (caller 应继续 await websocket.accept() + 业务逻辑);
        False 已 close (caller 应直接 return).

    Notes:
        - 不调 websocket.accept() — 校验失败时 close 是预 accept 状态的 reject.
        - dev mode 无 key 仍允许 (与 REST 路径一致).
    """
    settings = get_settings()
    configured_key = (settings.INTERNAL_API_KEY or "").strip()
    debug_mode = bool(settings.DEBUG)
    provided_token = websocket.query_params.get(WS_TOKEN_QUERY_NAME, "")

    # Branch 1: prod + 无 key → close 1011
    if not configured_key and not debug_mode:
        logger.error(
            "WebSocket: INTERNAL_API_KEY env var empty in production "
            "(ws_auth_fail_closed); rejecting connection"
        )
        await websocket.close(
            code=WS_CLOSE_SERVER_ERROR,
            reason="Internal API key not configured",
        )
        return False

    # Branch 2: dev + 无 key → 允许 + warn
    if not configured_key and debug_mode:
        logger.warning(
            "WebSocket: INTERNAL_API_KEY not configured but DEBUG=True; "
            "allowing connection (ws_auth_dev_bypass)"
        )
        return True

    # Branch 3: 已配 key, 客户端无 token → close 1008
    if not provided_token:
        logger.warning(
            "WebSocket: query param '%s' missing (ws_auth_reject)", WS_TOKEN_QUERY_NAME
        )
        await websocket.close(
            code=WS_CLOSE_POLICY_VIOLATION,
            reason="Missing auth token",
        )
        return False

    # Branch 4: 已配 key, token 不匹配 → close 1008
    if provided_token != configured_key:
        logger.warning(
            "WebSocket: provided token does not match configured key (ws_auth_reject)"
        )
        await websocket.close(
            code=WS_CLOSE_POLICY_VIOLATION,
            reason="Invalid auth token",
        )
        return False

    # Branch 5: 通过
    return True
