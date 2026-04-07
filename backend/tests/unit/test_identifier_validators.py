"""Unit tests for is_uuid_v4 — strict UUID v4 format validation.

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "UUID v4 Format Validation"]
"""

import pytest

from app.utils.identifier_validators import is_uuid_v4


class TestIsUuidV4:
    """is_uuid_v4 must accept v4 (any case) and reject everything else."""

    def test_accepts_lowercase_v4(self):
        """Scenario: Accept lowercase UUID v4."""
        assert is_uuid_v4("f4d10d8b-1234-4abc-89ab-cdef01234567") is True

    def test_accepts_uppercase_v4(self):
        """Scenario: Accept uppercase UUID v4 (frontend may emit either)."""
        assert is_uuid_v4("F4D10D8B-1234-4ABC-89AB-CDEF01234567") is True

    def test_accepts_mixed_case_v4(self):
        """Mixed-case is also valid (re.IGNORECASE)."""
        assert is_uuid_v4("F4d10d8B-1234-4AbC-89Ab-CdEf01234567") is True

    def test_rejects_v1_uuid(self):
        """Scenario: Reject UUID v1 — version nibble is '1', not '4'.

        v1 example from RFC 4122: the third group starts with '1'.
        """
        assert is_uuid_v4("550e8400-e29b-11d4-a716-446655440000") is False

    def test_rejects_v3_uuid(self):
        """Reject UUID v3 — version nibble is '3'."""
        assert is_uuid_v4("a3bb189e-8bf9-3888-9912-ace4e6543002") is False

    def test_rejects_v5_uuid(self):
        """Reject UUID v5 — version nibble is '5'."""
        assert is_uuid_v4("886313e1-3b8a-5372-9b90-0c9aee199e5d") is False

    def test_rejects_invalid_variant_nibble(self):
        """Reject when variant nibble is not in {8,9,a,b}.

        Last group starts with 'c' here — variant must be 10xx (binary)
        which means hex 8/9/a/b.
        """
        assert is_uuid_v4("f4d10d8b-1234-4abc-c9ab-cdef01234567") is False

    def test_rejects_malformed_text(self):
        """Scenario: Reject random text."""
        assert is_uuid_v4("not-a-uuid") is False
        assert is_uuid_v4("万有引力") is False
        assert is_uuid_v4("default_concept") is False
        assert is_uuid_v4("") is False

    def test_rejects_missing_hyphens(self):
        """A UUID without dashes is not v4 format."""
        assert is_uuid_v4("f4d10d8b12344abc89abcdef01234567") is False

    def test_rejects_too_short(self):
        """Truncated UUID."""
        assert is_uuid_v4("f4d10d8b-1234-4abc-89ab") is False

    def test_rejects_too_long(self):
        """Trailing extra characters."""
        assert is_uuid_v4("f4d10d8b-1234-4abc-89ab-cdef01234567-extra") is False

    def test_rejects_none(self):
        """Scenario: Reject non-string input — None."""
        assert is_uuid_v4(None) is False

    def test_rejects_int(self):
        """Scenario: Reject non-string input — int."""
        assert is_uuid_v4(12345) is False

    def test_rejects_dict(self):
        """Reject dict input without raising."""
        assert is_uuid_v4({"id": "f4d10d8b-1234-4abc-89ab-cdef01234567"}) is False

    def test_rejects_list(self):
        """Reject list input without raising."""
        assert is_uuid_v4(["f4d10d8b-1234-4abc-89ab-cdef01234567"]) is False

    def test_does_not_raise_on_unusual_input(self):
        """The function must never raise — it's a predicate, not a parser."""
        try:
            is_uuid_v4(object())
            is_uuid_v4(b"f4d10d8b-1234-4abc-89ab-cdef01234567")
        except Exception as exc:
            pytest.fail(f"is_uuid_v4 raised {type(exc).__name__}: {exc}")
