"""
Unit tests for Neo4j configuration in Settings.

Story 30.1 - AC 2: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE, NEO4J_ENABLED

[Source: docs/stories/30.1.story.md - AC 2]
[Source: backend/app/config.py:324-347]
"""

import os
import pytest
from unittest.mock import patch

from app.config import Settings


class TestNeo4jSettingsDefaults:
    """Test Neo4j settings have correct defaults (AC2)."""

    def test_neo4j_enabled_default_true(self):
        """NEO4J_ENABLED defaults to True."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(
                _env_file=None,
                NEO4J_PASSWORD="test",
            )
            assert settings.NEO4J_ENABLED is True
            assert settings.neo4j_enabled is True

    def test_neo4j_uri_default(self):
        """NEO4J_URI defaults to bolt://localhost:7687."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.NEO4J_URI == "bolt://localhost:7687"
            assert settings.neo4j_uri == "bolt://localhost:7687"

    def test_neo4j_user_default(self):
        """NEO4J_USER defaults to 'neo4j'."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.NEO4J_USER == "neo4j"
            assert settings.neo4j_user == "neo4j"

    def test_neo4j_database_default(self):
        """NEO4J_DATABASE defaults to 'neo4j'."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.NEO4J_DATABASE == "neo4j"
            assert settings.neo4j_database == "neo4j"

    def test_neo4j_password_empty_default(self):
        """NEO4J_PASSWORD defaults to empty string (user must set it)."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.NEO4J_PASSWORD == ""
            assert settings.neo4j_password == ""


class TestNeo4jSettingsFromEnv:
    """Test Neo4j settings load from environment variables (AC2)."""

    def test_neo4j_settings_from_env(self):
        """All 5 Neo4j env vars are correctly loaded."""
        env = {
            "NEO4J_ENABLED": "true",
            "NEO4J_URI": "bolt://custom-host:7688",
            "NEO4J_USER": "admin",
            "NEO4J_PASSWORD": "s3cret_p@ss",
            "NEO4J_DATABASE": "canvas_db",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings(_env_file=None)

            assert settings.neo4j_enabled is True
            assert settings.neo4j_uri == "bolt://custom-host:7688"
            assert settings.neo4j_user == "admin"
            assert settings.neo4j_password == "s3cret_p@ss"
            assert settings.neo4j_database == "canvas_db"

    def test_neo4j_enabled_false_from_env(self):
        """NEO4J_ENABLED=false correctly parsed as bool False."""
        with patch.dict(os.environ, {"NEO4J_ENABLED": "false"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.neo4j_enabled is False

    def test_neo4j_enabled_case_insensitive(self):
        """NEO4J_ENABLED accepts 'False' (case-insensitive)."""
        with patch.dict(os.environ, {"NEO4J_ENABLED": "False"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.neo4j_enabled is False

    def test_neo4j_uri_with_different_port(self):
        """NEO4J_URI accepts non-standard ports."""
        with patch.dict(os.environ, {"NEO4J_URI": "bolt://localhost:7689"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.neo4j_uri == "bolt://localhost:7689"
