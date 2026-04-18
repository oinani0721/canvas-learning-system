"""Tests for Story 1.11: Config drift detection."""

import tempfile
from pathlib import Path

import pytest


class TestParseEnvFile:
    def test_parses_simple(self, tmp_path):
        from app.services.config_drift_service import _parse_env_file

        f = tmp_path / ".env"
        f.write_text('FOO=bar\nBAZ="hello"\n# comment\n')
        result = _parse_env_file(f)
        assert result["FOO"] == "bar"
        assert result["BAZ"] == "hello"

    def test_missing_file(self):
        from app.services.config_drift_service import _parse_env_file

        assert _parse_env_file("/nonexistent/.env") == {}


class TestMaskSensitive:
    def test_masks_password(self):
        from app.services.config_drift_service import mask_sensitive

        assert mask_sensitive("NEO4J_PASSWORD", "supersecret") == "su*******et"

    def test_non_sensitive_unchanged(self):
        from app.services.config_drift_service import mask_sensitive

        assert mask_sensitive("DEBUG", "true") == "true"

    def test_short_password_unchanged(self):
        from app.services.config_drift_service import mask_sensitive

        assert mask_sensitive("NEO4J_PASSWORD", "ab") == "ab"


class TestDetectConfigDrift:
    def test_no_drift(self, tmp_path):
        from app.services.config_drift_service import detect_config_drift

        root = tmp_path / "root.env"
        backend = tmp_path / "backend.env"
        root.write_text("NEO4J_USER=neo4j\nDEBUG=true\n")
        backend.write_text("NEO4J_USER=neo4j\nDEBUG=true\n")

        result = detect_config_drift(root, backend)
        assert len(result["drifts"]) == 0
        assert "NEO4J_USER" in result["synced"]

    def test_drift_detected(self, tmp_path):
        from app.services.config_drift_service import detect_config_drift

        root = tmp_path / "root.env"
        backend = tmp_path / "backend.env"
        root.write_text("NEO4J_USER=neo4j\nDEBUG=true\n")
        backend.write_text("NEO4J_USER=neo4j\nDEBUG=false\n")

        result = detect_config_drift(root, backend)
        assert len(result["drifts"]) == 1
        assert result["drifts"][0]["key"] == "DEBUG"

    def test_missing_in_backend(self, tmp_path):
        from app.services.config_drift_service import detect_config_drift

        root = tmp_path / "root.env"
        backend = tmp_path / "backend.env"
        root.write_text("ACTIVE_VAULT=cs61b\n")
        backend.write_text("")

        result = detect_config_drift(root, backend)
        assert len(result["missing"]) == 1
        assert result["missing"][0]["present_in"] == "root_only"


class TestConfigCheckEndpoint:
    @pytest.fixture
    def client(self):
        from app.main import app
        from fastapi.testclient import TestClient

        return TestClient(app, raise_server_exceptions=False)

    def test_endpoint_returns_200(self, client):
        resp = client.get("/api/v1/system/config-check")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "drifts" in data
        assert "synced" in data
