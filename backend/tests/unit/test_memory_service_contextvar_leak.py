# wave-5 Stage B P0 (2026-05-11): regression guard for the cross-vault leak
# fix in memory_service.  ChatGPT v4 Agent C identified that the legacy
# Story 1.9 build_group_id(subject, canvas_name=...) collapses every vault's
# subject:canvas pair onto the same Neo4j namespace, leaking memories across
# vaults.  The fix routes every call through _resolve_memory_group_id which
# prefers ContextVar (vault: prefix) and falls back to build_vault_group_id
# under the vault:default bucket.
"""Memory service multi-vault leak regression tests."""

from app.core.subject_config import (
    DEFAULT_SUBJECT_ID,
    _current_subject_id,
    set_current_subject_id,
)
from app.services.memory_service import _resolve_memory_group_id


class TestResolveMemoryGroupId:
    """Verify _resolve_memory_group_id obeys ContextVar > fallback priority."""

    def setup_method(self):
        # Reset ContextVar between tests.
        _current_subject_id.set(DEFAULT_SUBJECT_ID)

    def teardown_method(self):
        _current_subject_id.set(DEFAULT_SUBJECT_ID)

    def test_memory_service_uses_build_vault_group_id_from_contextvar(self):
        """ContextVar set to a vault:<id> prefix string is trusted and returned
        verbatim — the writes go to that exact vault group_id.

        Regression guard for the ChatGPT v4 Agent C P0 leak: previously every
        call landed in build_group_id(subject, canvas_name=...) regardless of
        the per-request vault, collapsing vault:cs_61b and vault:数学 into the
        same Neo4j namespace.
        """
        set_current_subject_id("vault:cs_61b:algorithms")
        gid = _resolve_memory_group_id("algorithms", canvas_name="dijkstra")
        assert gid == "vault:cs_61b:algorithms", f"ContextVar not respected; got {gid}"

    def test_non_vault_contextvar_is_canonicalized(self):
        """A deprecated bare subject in ContextVar must be canonicalized into
        the vault: namespace so legacy callers still get isolation.
        """
        set_current_subject_id("cs188")  # deprecated
        gid = _resolve_memory_group_id("cs188", canvas_name="lecture-1")
        assert gid.startswith("vault:"), (
            f"deprecated ContextVar not canonicalized: {gid}"
        )

    def test_fallback_when_no_contextvar_uses_vault_default(self):
        """No ContextVar set → fall back to vault:default bucket so we never
        accidentally write to the legacy 'subject:canvas' namespace.
        """
        # ContextVar reset to DEFAULT_SUBJECT_ID
        gid = _resolve_memory_group_id("physics", canvas_name="kinematics")
        assert gid.startswith("vault:"), f"fallback must use vault: prefix, got {gid}"
        assert "default" in gid or "physics" in gid

    def test_two_vaults_do_not_collide(self):
        """The exact leak symptom: vault A's record under {subject, canvas}
        must produce a DIFFERENT group_id than vault B's record under the
        same {subject, canvas}.
        """
        set_current_subject_id("vault:vault_a:algorithms")
        gid_a = _resolve_memory_group_id("algorithms", canvas_name="dijkstra")

        set_current_subject_id("vault:vault_b:algorithms")
        gid_b = _resolve_memory_group_id("algorithms", canvas_name="dijkstra")

        assert gid_a != gid_b, (
            "Two different vaults must produce different group_ids "
            f"(got {gid_a} == {gid_b})"
        )
