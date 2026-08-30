# CARD-C6 (BATCH-2026-08-25-跨vault与收束) semantic rewrite of the wave-5
# Stage B P0 cross-vault leak guard — then CARD-G2-2 (BATCH-2026-08-28)
# contract REVERSAL, exactly the "deliberate red test" the C6 docstring
# predicted: the write-side resolver moved from "process-level active
# vault, ContextVar ignored" to "per-request VaultScope first".
"""Memory write-side vault isolation regression tests.

CONTRACT — memory 写侧 group_id 解析 = per-request VaultScope 优先
(CARD-G2-2 反转, frozen here):

``_vault_scoped_group_id`` resolves the vault via
``app.core.vault_scope.current_vault_id()``: the per-request scope's
vault segment (the ``_current_subject_id`` ContextVar injected by the
endpoint-boundary ``resolve_vault_scope``) when one is set, falling back
to the process-level active vault (``app.config.get_current_vault_id()``)
when no request scope is active (background tasks / CLI / schedulers).

Why this is safe where the pre-2.5.Y ContextVar preference was not:
CARD-G2-2's 409 fail-closed gate guarantees that on request paths the
injected scope's vault EQUALS the active vault (a mismatch is rejected
at the endpoint boundary before any write).  The only sanctioned
divergence is the chat.py hook cwd derivation (documented legal
exception), where honouring the per-request vault is precisely the
correct isolation behaviour.

Scope of the guarantee (Codex CARD-C6 review, HIGH-2/HIGH-3 rectified;
updated by CARD-G2-2):

* It covers the group_id resolution routed through
  ``_vault_scoped_group_id`` (record_learning_event / batch / episode
  write paths, plus the score-history query path, in memory_service).
  The C6-documented exception is now CLOSED by CARD-G2-2:
  ``record_knowledge_entity`` falls back to
  ``vault_scope.current_group_id()`` (no more DEFAULT_GROUP_ID).
* Isolation holds between processes whose CANONICAL vault_ids differ.
  ``sanitize_vault_id`` is lossy ("CS 61B" and "CS-61B" both canonicalize
  to "cs_61b"), so two vaults with display names that collide after
  sanitization share a namespace — that boundary is pinned by
  ``test_lossy_sanitization_boundary_is_pinned`` below rather than
  papered over.

Patch-target note: ``vault_scope.current_vault_id`` performs a
function-body ``from app.config import get_current_vault_id`` at call
time, so tests MUST patch ``app.config.get_current_vault_id``.  Patching
the ``app.services.memory_service`` namespace has no effect (the name
never enters that module's dict).
"""

from unittest.mock import patch

from app.core.subject_config import (
    DEFAULT_SUBJECT_ID,
    _current_subject_id,
    set_current_subject_id,
)
from app.services.memory_service import _vault_scoped_group_id


class TestVaultScopedGroupId:
    """Freeze the vault:-prefixed, per-request-VaultScope-first write-side
    contract (CARD-G2-2; falls back to the process active vault when no
    request scope is set)."""

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

    def test_conflicting_contextvar_wins(self):
        """CARD-G2-2 contract REVERSAL (the C6-predicted deliberate red
        test, now green under the new contract): a per-request scope
        pointing at a DIFFERENT vault takes precedence over the
        process-level active vault.

        On request paths the 409 gate makes this divergence impossible;
        the case exists for the hook-cwd documented legal exception,
        where writing under the request's vault (not the process vault)
        is the correct isolation behaviour.
        """
        set_current_subject_id("vault:contextvar_vault:algorithms")
        with patch("app.config.get_current_vault_id", return_value="process_vault"):
            gid = _vault_scoped_group_id("algorithms", canvas_name="dijkstra")
        assert gid == "vault:contextvar_vault:dijkstra"
        assert "process_vault" not in gid, (
            f"per-request scope must win over process vault (CARD-G2-2): {gid}"
        )

    def test_unset_contextvar_falls_back_to_active_vault(self):
        """No request scope (ContextVar at its DEFAULT_SUBJECT_ID default,
        as in background tasks / CLI) → process-level active vault, same
        as the pre-G2-2 contract."""
        with patch("app.config.get_current_vault_id", return_value="process_vault"):
            gid = _vault_scoped_group_id("algorithms", canvas_name="dijkstra")
        assert gid == "vault:process_vault:dijkstra"

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
