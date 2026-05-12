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


# ═══════════════════════════════════════════════════════════════════════════════
# Wave-2 P0-2 (2026-05-12) — active_vault_id reads subject_config ContextVar
# ═══════════════════════════════════════════════════════════════════════════════


class TestActiveVaultIdReadsSubjectContextVar:
    """Wave-2 P0-2 vault wiring fix — ``LanceDBClient.active_vault_id`` must
    derive from ``app.core.subject_config.get_current_subject_id()`` (the
    ContextVar that endpoints actually write via ``set_current_subject_id``)
    so that the per-request vault scope reaches LanceDB table resolution
    without an explicit ``_vault_id_override`` ctor arg.
    """

    def test_active_vault_id_reads_subject_contextvar(self):
        """ContextVar set → active_vault_id derives first segment after 'vault:' prefix."""
        from agentic_rag.clients.lancedb_client import LanceDBClient
        from app.core.subject_config import (
            DEFAULT_SUBJECT_ID,
            _current_subject_id,
            set_current_subject_id,
        )

        # Snapshot for restore — ContextVar set() returns a Token we use to reset.
        token = _current_subject_id.set("vault:cs_61b")
        try:
            client = LanceDBClient()  # no override
            assert client.active_vault_id == "cs_61b"
        finally:
            _current_subject_id.reset(token)

    def test_active_vault_id_strips_subject_suffix(self):
        """vault:cs_61b:algorithms → cs_61b (first segment only)."""
        from agentic_rag.clients.lancedb_client import LanceDBClient
        from app.core.subject_config import _current_subject_id

        token = _current_subject_id.set("vault:cs_61b:algorithms")
        try:
            client = LanceDBClient()
            assert client.active_vault_id == "cs_61b"
        finally:
            _current_subject_id.reset(token)

    def test_active_vault_id_resolve_table_name_uses_contextvar(self):
        """End-to-end: ContextVar value flows into resolve_table_name prefix."""
        from agentic_rag.clients.lancedb_client import LanceDBClient
        from app.core.subject_config import _current_subject_id

        token = _current_subject_id.set("vault:数学")
        try:
            client = LanceDBClient()
            assert client.resolve_table_name("vault_notes") == "数学_vault_notes"
        finally:
            _current_subject_id.reset(token)

    def test_active_vault_id_override_wins_over_contextvar(self):
        """Explicit constructor vault_id still takes priority (legacy POC tests)."""
        from agentic_rag.clients.lancedb_client import LanceDBClient
        from app.core.subject_config import _current_subject_id

        token = _current_subject_id.set("vault:cs_61b")
        try:
            client = LanceDBClient(vault_id="explicit_override")
            assert client.active_vault_id == "explicit_override"
        finally:
            _current_subject_id.reset(token)


class TestActiveVaultIdFallbackWhenNoContextVar:
    """Wave-2 P0-2 — fall back to legacy app.config.get_current_vault_id()
    when ContextVar is at DEFAULT_SUBJECT_ID (背景任务/CLI 未调过
    set_current_subject_id 的场景), 保 backward-compat 老 caller 不破裂."""

    def test_active_vault_id_fallback_when_no_contextvar(self):
        """ContextVar at DEFAULT → falls back to app.config global active vault."""
        from agentic_rag.clients.lancedb_client import LanceDBClient
        from app.config import get_settings, reload_settings
        from app.core.subject_config import (
            DEFAULT_SUBJECT_ID,
            _current_subject_id,
        )

        # Force ContextVar to DEFAULT to simulate no-request-scope.
        token = _current_subject_id.set(DEFAULT_SUBJECT_ID)
        original = get_settings().ACTIVE_VAULT
        try:
            reload_settings(overrides={"ACTIVE_VAULT": "fallback_vault"})
            client = LanceDBClient()
            # Should derive from legacy global config, NOT "default" hardcoded.
            assert client.active_vault_id == "fallback_vault"
        finally:
            reload_settings(overrides={"ACTIVE_VAULT": original})
            _current_subject_id.reset(token)
