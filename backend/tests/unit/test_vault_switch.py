"""Tests for Story 1.8: Vault Switch Runtime API.

Covers AC #1 (switch), #2 (validation), #3 (current), #4 (cache clear).
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def _obsidian_vault(tmp_path):
    """Create a temporary directory that looks like an Obsidian vault."""
    vault = tmp_path / "test-vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    return vault


@pytest.fixture
def _second_vault(tmp_path):
    vault = tmp_path / "second-vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    return vault


@pytest.fixture
def _non_vault(tmp_path):
    """Directory without .obsidian/ — should fail validation."""
    d = tmp_path / "not-a-vault"
    d.mkdir()
    return d


class TestSanitizeVaultId:
    def test_simple_name(self):
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("canvas-vault") == "canvas_vault"

    def test_spaces_and_caps(self):
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("CS 61B") == "cs_61b"

    def test_special_chars(self):
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("my.vault (2026)") == "my_vault_2026"

    def test_empty_string(self):
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("") == "default"

    def test_chinese_chars(self):
        from app.config import sanitize_vault_id

        result = sanitize_vault_id("笔记库")
        assert result == "default"  # all non-ascii stripped → falls back to "default"


class TestReloadSettings:
    def test_cache_clear_picks_up_new_value(self):
        from app.config import get_settings, reload_settings

        original = get_settings().ACTIVE_VAULT

        reload_settings(overrides={"ACTIVE_VAULT": "new-vault"})
        assert get_settings().ACTIVE_VAULT == "new-vault"

        # Restore
        reload_settings(overrides={"ACTIVE_VAULT": original})

    def test_vault_id_changes_after_reload(self):
        from app.config import get_current_vault_id, get_settings, reload_settings

        original = get_settings().ACTIVE_VAULT

        reload_settings(overrides={"ACTIVE_VAULT": "CS 61B"})
        assert get_current_vault_id() == "cs_61b"

        reload_settings(overrides={"ACTIVE_VAULT": original})


class TestVaultSwitchEndpoint:
    """Test POST /api/v1/vault/switch and GET /api/v1/vault/current."""

    @pytest.fixture(autouse=True)
    def _restore_settings(self):
        from app.config import get_settings, reload_settings

        original_path = get_settings().CANVAS_BASE_PATH
        original_vault = get_settings().ACTIVE_VAULT
        yield
        reload_settings(
            overrides={
                "CANVAS_BASE_PATH": original_path,
                "ACTIVE_VAULT": original_vault,
            }
        )

    @pytest.fixture
    def client(self):
        from app.main import app

        return TestClient(app, raise_server_exceptions=False)

    def test_switch_valid_vault(self, client, _obsidian_vault):
        resp = client.post(
            "/api/v1/vault/switch", json={"vault_path": str(_obsidian_vault)}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vault_name"] == "test-vault"
        assert data["vault_id"] == "test_vault"
        assert data["vault_path"] == str(_obsidian_vault)

    def test_switch_nonexistent_path(self, client, tmp_path):
        resp = client.post(
            "/api/v1/vault/switch", json={"vault_path": str(tmp_path / "nope")}
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"] == "vault_not_found"

    def test_switch_non_vault_dir(self, client, _non_vault):
        resp = client.post("/api/v1/vault/switch", json={"vault_path": str(_non_vault)})
        assert resp.status_code == 400
        assert "missing .obsidian" in resp.json()["detail"]["message"]

    def test_get_current(self, client):
        resp = client.get("/api/v1/vault/current")
        assert resp.status_code == 200
        data = resp.json()
        assert "vault_path" in data
        assert "vault_id" in data

    def test_switch_then_current_reflects_new(self, client, _obsidian_vault):
        client.post("/api/v1/vault/switch", json={"vault_path": str(_obsidian_vault)})
        resp = client.get("/api/v1/vault/current")
        assert resp.json()["vault_name"] == "test-vault"
