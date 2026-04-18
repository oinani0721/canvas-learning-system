"""Tests for Story 1.6: KG health check + .gitignore generation."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path


class TestGitignoreGeneration:
    def test_creates_gitignore(self, tmp_path):
        from app.services.vault_init_service import VaultInitService

        svc = VaultInitService()
        svc._ensure_gitignore(tmp_path)
        gi = tmp_path / ".gitignore"
        assert gi.exists()
        content = gi.read_text()
        assert "data/lancedb/" in content
        assert "data/neo4j/" in content
        assert ".obsidian/workspace.json" in content

    def test_does_not_overwrite_existing(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("custom content\n")
        from app.services.vault_init_service import VaultInitService

        VaultInitService._ensure_gitignore(tmp_path)
        assert gi.read_text() == "custom content\n"


class TestGitPluginDetection:
    def test_detects_installed(self, tmp_path):
        from app.services.vault_init_service import VaultInitService

        (tmp_path / ".obsidian" / "plugins" / "obsidian-git").mkdir(parents=True)
        assert VaultInitService.has_git_plugin(str(tmp_path)) is True

    def test_not_installed(self, tmp_path):
        from app.services.vault_init_service import VaultInitService

        assert VaultInitService.has_git_plugin(str(tmp_path)) is False


class TestKGHealthEndpoint:
    @pytest.fixture
    def client(self):
        from app.main import app

        return TestClient(app, raise_server_exceptions=False)

    def test_endpoint_returns_200(self, client):
        resp = client.get("/api/v1/kg/health")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_nodes" in data
        assert "neo4j_available" in data
