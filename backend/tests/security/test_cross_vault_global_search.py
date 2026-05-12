"""Round-23 wave-2 hotfix — cross-vault leakage regression (BE-A scope).

Verifies that POST /api/v1/chat/global-search resolves the LanceDB table
using the **request-scoped** ``vault_id`` (not the stale process-level
active vault). Without this, two browsers / two CLAUDE windows on the
same backend can cross-leak — vault_a's prior request seeds the
process-level state, then vault_b's request resolves to vault_a's table.

This test depends on BE-A's multi-vault hotfix landing. Until then it is
marked ``xfail(strict=False)`` so CI still surfaces it if a future change
accidentally fixes the underlying bug.
"""

from __future__ import annotations

from typing import Any, Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dev_settings_override() -> Settings:
    """DEBUG=True + no key so the auth dependency is transparent."""
    return Settings(
        PROJECT_NAME="Canvas Learning System API (Test)",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
        INTERNAL_API_KEY="",
    )


class _RecordingLanceDBStub:
    """Test double for LanceDBClient that records resolve_table_name calls.

    Not a mock of a real interface — a deliberate recorder so we can assert
    on the vault prefix the resolution mechanism produces under cross-vault
    request flow.
    """

    def __init__(self) -> None:
        self._initialized = True
        self.resolved_tables: list[str] = []

    def resolve_table_name(self, base_name: str) -> str:
        # Read the current request-scoped subject_id at resolution time.
        # If BE-A is correctly forwarding request vault_id, this returns the
        # vault_b-prefixed table; otherwise it returns the stale vault_a one.
        from app.core.subject_config import get_current_subject_id

        active_group = get_current_subject_id() or "unknown"
        resolved = f"{active_group}__{base_name}"
        self.resolved_tables.append(resolved)
        return resolved


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    """TestClient with DEBUG=True so the auth wrapper is transparent."""
    app.dependency_overrides[get_settings] = _dev_settings_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason=(
        "BE-A multi-vault hotfix (P0-2) not yet merged: process-level singleton "
        "currently leaks vault_a's resolved table into vault_b's request. "
        "After BE-A lands, this test should pass."
    ),
    strict=False,
)
def test_global_search_must_follow_request_vault_id(
    auth_client: TestClient,
) -> None:
    """Process-level active vault = vault_a, request body vault_id = vault_b
    → resolve_table_name MUST return a vault_b-prefixed table (no vault_a leak)."""
    from app.core.subject_config import build_vault_group_id, set_current_subject_id

    # 1. Seed process-level active vault to vault_a (simulating a prior request).
    vault_a_group = build_vault_group_id("vault_a", subject_id=None, canvas_path=None)
    set_current_subject_id(vault_a_group)

    # 2. Install the recording stub as the module-level singleton.
    recorder = _RecordingLanceDBStub()

    # 3. Patch search_supplementary to: capture client, call resolve_table_name
    #    (mimicking the real _two_tier_search path), and return empty result.
    captured: dict[str, Any] = {"client": None}

    async def _recording_search_supp(
        *, query: str, lancedb_client: Any, **_kwargs
    ) -> dict[str, Any]:
        captured["client"] = lancedb_client
        if lancedb_client is not None and hasattr(lancedb_client, "resolve_table_name"):
            lancedb_client.resolve_table_name("vault_notes")
        return {
            "materials": [],
            "degraded": False,
            "reason": "empty_index",
        }

    with (
        patch(
            "app.api.v1.endpoints.chat._get_supp_lancedb_client",
            new=AsyncMock(return_value=recorder),
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            new=_recording_search_supp,
        ),
    ):
        response = auth_client.post(
            "/api/v1/chat/global-search",
            json={
                "user_question": "what is value iteration",
                "vault_id": "vault_b",  # ← request says vault_b
                "subject_id": None,
                "top_k_max": 5,
                "hard_cap": 5,
            },
        )

    assert response.status_code == 200, (
        f"global-search returned {response.status_code}: {response.text[:200]}"
    )

    # 4. The resolved table MUST be vault_b-prefixed, NOT vault_a.
    assert recorder.resolved_tables, "resolve_table_name was never called; harness bug"
    last_resolved = recorder.resolved_tables[-1]
    assert "vault_b" in last_resolved, (
        f"Expected vault_b prefix in resolved table, got: {last_resolved}. "
        f"This indicates cross-vault leakage — vault_a's process-level state "
        f"leaked into vault_b's request."
    )
    assert "vault_a" not in last_resolved, (
        f"vault_a leaked into vault_b's resolved table: {last_resolved}"
    )
