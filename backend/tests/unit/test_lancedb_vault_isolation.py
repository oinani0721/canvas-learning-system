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
            # Should derive from legacy global config, NOT "default" baked in.
            assert client.active_vault_id == "fallback_vault"
        finally:
            reload_settings(overrides={"ACTIVE_VAULT": original})
            _current_subject_id.reset(token)


# ═══════════════════════════════════════════════════════════════════════════════
# Wave-3 hotfix (ChatGPT v4 verdict #3, 2026-05-12) —
# narrow exception catch + Level-4 fallback warning
#
# active_vault_id used to ``except Exception:`` on both Level-2 (subject_config
# ContextVar) and Level-3 (app.config) lookup, silently dropping to "default"
# table namespace. That hid genuine wiring regressions (ImportError on a
# refactor, AttributeError on an API rename, ...) and risked cross-vault data
# leakage with zero Ops visibility.
#
# The fix narrows both excepts to (ImportError, AttributeError, RuntimeError,
# ValueError) — anything outside this list (BaseException, KeyboardInterrupt,
# SystemExit, asyncio.CancelledError, ...) now propagates — AND emits
# logger.warning whenever the property actually lands on "default".
# ═══════════════════════════════════════════════════════════════════════════════


def _raise_keyboard_interrupt(*args, **kwargs):
    """Helper: simulate a Ctrl-C arriving mid-ContextVar-read.

    Used to verify ``active_vault_id`` does NOT swallow ``BaseException``
    subclasses (which would mask catastrophic signals like KeyboardInterrupt
    or SystemExit). Real ContextVar accessors never raise this, but if a
    user hits Ctrl-C while ``get_current_subject_id()`` runs, that signal
    must propagate.
    """
    raise KeyboardInterrupt("simulated user interrupt during ContextVar read")


def _raise_runtime_subject_config(*args, **kwargs):
    """Helper: simulate a real RuntimeError from subject_config accessor.

    Real production scenario: a misconfigured ContextVar default raises
    ``RuntimeError`` on get(). This is one of the four narrow exceptions
    ``active_vault_id`` legitimately catches.
    """
    raise RuntimeError("subject_config accessor wiring outage")


class TestActiveVaultIdNarrowExceptionAndFallbackWarning:
    """Wave-3 verdict #3 — narrow exception catch + Level-4 warning."""

    def test_active_vault_id_default_fallback_logs_warning(self, monkeypatch, caplog):
        """When BOTH subject_config and app.config raise expected errors,
        active_vault_id must:
          1. yield "default" (preserve wave-2 4-level resolution behavior)
          2. emit logger.warning so Ops can see the cross-vault-leak risk.
        """
        import logging
        import sys
        import types

        from agentic_rag.clients.lancedb_client import LanceDBClient

        # ---- Level-2 outage: subject_config.get_current_subject_id raises
        # AttributeError (one of our narrow-tuple errors) on every attr access.
        class _BrokenSubjectConfigModule(types.ModuleType):
            def __getattr__(self, name):
                raise AttributeError(
                    f"subject_config outage: attr {name!r} unavailable"
                )

        broken_subject_config = _BrokenSubjectConfigModule("app.core.subject_config")
        monkeypatch.setitem(
            sys.modules, "app.core.subject_config", broken_subject_config
        )

        # ---- Level-3 outage: app.config.get_current_vault_id raises RuntimeError
        # (also in narrow tuple) so we drop to Level-4.
        import app.config as app_config_mod

        monkeypatch.setattr(
            app_config_mod,
            "get_current_vault_id",
            _raise_runtime_subject_config,
            raising=False,
        )

        # Bridge loguru → stdlib so pytest caplog captures the warning record.
        # The SUT uses loguru when available; the bridge sink mirrors WARNING+
        # messages onto a stdlib logger that caplog watches.
        sink_id = None
        try:
            from loguru import logger as loguru_logger

            bridge_logger = logging.getLogger("agentic_rag.clients.lancedb_client")
            sink_id = loguru_logger.add(
                lambda msg: bridge_logger.warning(str(msg)),
                level="WARNING",
            )
        except ImportError:
            pass

        try:
            client = LanceDBClient()
            with caplog.at_level(
                logging.WARNING,
                logger="agentic_rag.clients.lancedb_client",
            ):
                result = client.active_vault_id

            assert result == "default", (
                "Level-4 must still yield 'default' (wave-2 contract)"
            )

            captured_text = " ".join(rec.getMessage() for rec in caplog.records)
            assert "fell back to 'default'" in captured_text, (
                "Level-4 fallback must emit logger.warning with sentinel "
                f"\"fell back to 'default'\" — got records: {caplog.records!r}"
            )
        finally:
            if sink_id is not None:
                try:
                    from loguru import logger as loguru_logger

                    loguru_logger.remove(sink_id)
                except (ImportError, ValueError):
                    pass

    def test_active_vault_id_level2_exception_specific_only(self, monkeypatch):
        """Level-2 must propagate BaseException / KeyboardInterrupt / SystemExit
        rather than swallowing them via ``except Exception``. Verifies the
        narrow tuple (ImportError, AttributeError, RuntimeError, ValueError)
        does NOT mask catastrophic signals.
        """
        import sys
        import types

        from agentic_rag.clients.lancedb_client import LanceDBClient

        # Build a minimal subject_config replacement whose
        # get_current_subject_id raises KeyboardInterrupt (a BaseException
        # subclass NOT in our narrow tuple). The DEFAULT_SUBJECT_ID constant
        # is set to a non-default sentinel so the `if ctx_value != DEFAULT`
        # gate doesn't short-circuit before the raise.
        replacement = types.ModuleType("app.core.subject_config")
        replacement.DEFAULT_SUBJECT_ID = "__never_matches__"
        replacement.get_current_subject_id = _raise_keyboard_interrupt
        monkeypatch.setitem(sys.modules, "app.core.subject_config", replacement)

        client = LanceDBClient()
        with pytest.raises(KeyboardInterrupt):
            _ = client.active_vault_id

    def test_active_vault_id_level2_runtime_error_falls_through(self, monkeypatch):
        """RuntimeError in subject_config ContextVar accessor → caught (in
        narrow tuple) → falls through to Level-3 (app.config). Confirms the
        wave-2 fallback chain still works after the narrowing.
        """
        import sys
        import types

        from agentic_rag.clients.lancedb_client import LanceDBClient
        from app.config import get_settings, reload_settings

        replacement = types.ModuleType("app.core.subject_config")
        replacement.DEFAULT_SUBJECT_ID = "__never_matches__"
        replacement.get_current_subject_id = _raise_runtime_subject_config
        monkeypatch.setitem(sys.modules, "app.core.subject_config", replacement)

        original = get_settings().ACTIVE_VAULT
        try:
            reload_settings(overrides={"ACTIVE_VAULT": "level3_target"})
            client = LanceDBClient()
            # Level-2 raises RuntimeError (in narrow tuple) → caught →
            # Level-3 yields global active vault from settings.
            assert client.active_vault_id == "level3_target"
        finally:
            reload_settings(overrides={"ACTIVE_VAULT": original})
