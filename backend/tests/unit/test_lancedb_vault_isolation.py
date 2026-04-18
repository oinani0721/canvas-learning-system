"""Tests for Story 1.9: LanceDB vault_id namespace isolation.

Covers vault_id table naming, cross-vault isolation, and index management.
"""

import pytest


class TestResolveTableName:
    """AC #1: Table names include vault_id prefix."""

    def test_prefixes_with_vault_id(self):
        from agentic_rag.clients.lancedb_client import LanceDBClient

        client = LanceDBClient(vault_id="cs_61b")
        assert client.resolve_table_name("vault_notes") == "cs_61b_vault_notes"
        assert client.resolve_table_name("canvas_nodes") == "cs_61b_canvas_nodes"

    def test_default_vault_no_prefix(self):
        from agentic_rag.clients.lancedb_client import LanceDBClient

        client = LanceDBClient(vault_id="default")
        assert client.resolve_table_name("vault_notes") == "vault_notes"

    def test_no_double_prefix(self):
        from agentic_rag.clients.lancedb_client import LanceDBClient

        client = LanceDBClient(vault_id="cs_61b")
        assert client.resolve_table_name("cs_61b_vault_notes") == "cs_61b_vault_notes"

    def test_empty_vault_id_no_prefix(self):
        from agentic_rag.clients.lancedb_client import LanceDBClient

        client = LanceDBClient(vault_id="")
        assert client.resolve_table_name("vault_notes") == "vault_notes"

    def test_active_vault_id_property(self):
        from agentic_rag.clients.lancedb_client import LanceDBClient

        client = LanceDBClient(vault_id="cs188")
        assert client.active_vault_id == "cs188"


class TestVaultIdFromConfig:
    """AC #3: Post-vault-switch, LanceDB auto-switches to new vault's table space."""

    def test_dynamic_vault_id_follows_config(self):
        from app.config import get_settings, reload_settings
        from agentic_rag.clients.lancedb_client import LanceDBClient

        original = get_settings().ACTIVE_VAULT
        client = LanceDBClient()  # no override → uses config

        reload_settings(overrides={"ACTIVE_VAULT": "CS 61B"})
        assert client.resolve_table_name("vault_notes") == "cs_61b_vault_notes"

        reload_settings(overrides={"ACTIVE_VAULT": original})


class TestSubjectResolverVaultId:
    """AC #6: subject_resolver includes vault_id in group_id."""

    def test_group_id_has_vault_prefix(self):
        from app.config import get_settings, reload_settings
        from app.services.subject_resolver import SubjectResolver

        original = get_settings().ACTIVE_VAULT
        reload_settings(overrides={"ACTIVE_VAULT": "cs61b"})

        resolver = SubjectResolver()
        info = resolver.resolve("test-canvas.canvas", manual_subject="math")
        assert info.group_id.startswith("cs61b:")

        reload_settings(overrides={"ACTIVE_VAULT": original})
