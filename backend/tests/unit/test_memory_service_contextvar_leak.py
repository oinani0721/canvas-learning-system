# CARD-C6 (BATCH-2026-08-25-跨vault与收束) semantic rewrite of the wave-5
# Stage B P0 cross-vault leak guard.  The original file asserted that
# `_resolve_memory_group_id` honoured the per-request ContextVar
# (`_current_subject_id`).  That resolver was removed in the Story 2.5.Y
# group_id migration; mechanical renaming is impossible because the new
# resolver has the OPPOSITE contract (see module docstring below).
"""Memory write-side vault isolation regression tests.

CONTRACT — memory 写侧 group_id 解析 = 进程级单 active vault (frozen here):

``_vault_scoped_group_id`` resolves the vault via
``app.config.get_current_vault_id()`` (= ``get_settings().vault_id``,
derived from ``.canvas-config.yaml`` / ``ACTIVE_VAULT``).  It deliberately
IGNORES the per-request ContextVar
(``app.core.subject_config._current_subject_id``) that the pre-2.5.Y
``_resolve_memory_group_id`` honoured — asserted below with a CONFLICTING
ContextVar, not just an unset one.

Scope of the guarantee (Codex CARD-C6 review, HIGH-2/HIGH-3 rectified):

* It covers exactly the group_id resolution routed through
  ``_vault_scoped_group_id`` (record_learning_event / batch / episode
  write paths, plus the score-history query path, in memory_service).
  Known pre-existing exception OUTSIDE this resolver,
  documented here and NOT fixed by this card: ``record_knowledge_entity``
  forwards a caller-supplied ``group_id or DEFAULT_GROUP_ID`` verbatim
  (e.g. verification_service passes bare canvas names) — closing that gap
  belongs to a future memory write-side card, not this regression guard.
* Isolation holds between processes whose CANONICAL vault_ids differ.
  ``sanitize_vault_id`` is lossy ("CS 61B" and "CS-61B" both canonicalize
  to "cs_61b"), so two vaults with display names that collide after
  sanitization share a namespace — that boundary is pinned by
  ``test_lossy_sanitization_boundary_is_pinned`` below rather than
  papered over.

Coupling with future multi-vault work: a single backend process serving
several vaults at once (长期计划 D1-B 形态; the cross-vault Web UI 刚需链
consumes per-vault projections and does not by itself require it) cannot
reuse this resolver as-is — it would need per-request vault scoping again.
These tests freeze today's single-active-vault contract explicitly so that
such a change surfaces as a deliberate red test, not silent drift.

Patch-target note: ``_vault_scoped_group_id`` performs a function-body
``from app.config import get_current_vault_id`` at call time, so tests
MUST patch ``app.config.get_current_vault_id``.  Patching the
``app.services.memory_service`` namespace has no effect (the name never
enters that module's dict).
"""

from unittest.mock import patch

from app.core.subject_config import (
    DEFAULT_SUBJECT_ID,
    _current_subject_id,
    set_current_subject_id,
)
from app.services.memory_service import _vault_scoped_group_id


class TestVaultScopedGroupId:
    """Freeze the vault:-prefixed, process-level-vault write-side contract."""

    def setup_method(self):
        # Token-based restore: teardown reset() puts back the OUTER value
        # (whatever surrounding fixtures had set), not a hardcoded default.
        self._cv_token = _current_subject_id.set(DEFAULT_SUBJECT_ID)

    def teardown_method(self):
        _current_subject_id.reset(self._cv_token)

    def test_canvas_write_is_always_vault_prefixed(self):
        """A canvas-scoped write must land under vault:<id>:<canvas>."""
        with patch("app.config.get_current_vault_id", return_value="cs_61b"):
            gid = _vault_scoped_group_id("algorithms", canvas_name="dijkstra")
        assert gid.startswith("vault:"), f"write-side must use vault: prefix, got {gid}"
        assert gid == "vault:cs_61b:dijkstra"

    def test_bare_write_is_always_vault_prefixed(self):
        """Even with neither subject nor canvas, writes stay in the vault bucket
        (never the legacy bare-subject namespace)."""
        with patch("app.config.get_current_vault_id", return_value="数学"):
            gid = _vault_scoped_group_id()
        assert gid.startswith("vault:"), f"write-side must use vault: prefix, got {gid}"
        assert gid == "vault:数学"

    def test_conflicting_contextvar_is_ignored(self):
        """The core inversion of the wave-5-era contract, frozen EXPLICITLY:
        a per-request ContextVar pointing at a DIFFERENT vault must not
        influence the resolver — the process-level active vault wins.

        Guards against a regression that re-introduces "prefer ContextVar
        when it looks like vault:*" (which the pre-2.5.Y resolver did):
        such a hybrid would pass every other test in this file but fail
        this one.
        """
        set_current_subject_id("vault:contextvar_vault:algorithms")
        with patch("app.config.get_current_vault_id", return_value="process_vault"):
            gid = _vault_scoped_group_id("algorithms", canvas_name="dijkstra")
        assert gid == "vault:process_vault:dijkstra"
        assert "contextvar_vault" not in gid, f"per-request ContextVar leaked into write-side group_id: {gid}"

    def test_canvas_name_takes_priority_over_subject(self):
        """D16 规约: 二级隔离优先 canvas 名 — when both are supplied the
        canvas wins and the subject is dropped entirely.

        Note the resolver inverts ``build_vault_group_id``'s own
        subject>canvas ordering by never forwarding subject alongside
        canvas_name — this test pins the memory_service-layer ordering.
        """
        with patch("app.config.get_current_vault_id", return_value="cs_61b"):
            gid = _vault_scoped_group_id("algorithms", canvas_name="admissibility")
        assert gid == "vault:cs_61b:admissibility"
        assert "algorithms" not in gid

    def test_two_active_vaults_do_not_collide(self):
        """The wave-5 leak symptom, restated for the new contract: the SAME
        {subject, canvas} pair written from two processes whose canonical
        vault_ids differ must produce DIFFERENT group_ids.

        Scope note: this patches the already-canonical getter return value,
        so it proves isolation at the canonical-id layer only — the lossy
        sanitization boundary above that layer is pinned separately below.
        """
        with patch("app.config.get_current_vault_id", return_value="vault_a"):
            gid_a = _vault_scoped_group_id("algorithms", canvas_name="dijkstra")
        with patch("app.config.get_current_vault_id", return_value="vault_b"):
            gid_b = _vault_scoped_group_id("algorithms", canvas_name="dijkstra")
        assert gid_a != gid_b, f"two active vaults must not collide (got {gid_a} == {gid_b})"
        assert gid_a == "vault:vault_a:dijkstra"
        assert gid_b == "vault:vault_b:dijkstra"

    def test_lossy_sanitization_boundary_is_pinned(self):
        """Known boundary, NOT an isolation guarantee: ``sanitize_vault_id``
        is lossy, so DISPLAY names that differ only in separators/case
        canonicalize to the same vault_id and therefore share a write-side
        namespace.  Pinned so the module docstring's "canonical ids differ"
        scoping stays honest; if sanitization ever becomes injective this
        test flags the (welcome, contract-changing) improvement.
        """
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("CS 61B") == sanitize_vault_id("CS-61B") == "cs_61b"

    def test_deprecated_bare_subject_still_lands_in_vault_bucket(self):
        """Legacy callers passing a deprecated bare subject (e.g. 'cs188')
        must still be canonicalized under the active vault's namespace —
        never written to the legacy flat subject namespace.
        """
        with patch("app.config.get_current_vault_id", return_value="cs_61b"):
            gid = _vault_scoped_group_id("cs188")
        assert gid.startswith("vault:"), f"deprecated subject not canonicalized: {gid}"
        assert gid == "vault:cs_61b:cs188"
