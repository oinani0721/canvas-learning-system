"""Unit tests for ReviewService._load_card_states + _get_card_state.

Verifies the dual-bucket compat-read behavior added by
fix-concept-id-identity-unification.

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "Card State Load Is Backward Compatible"]
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services import review_service as rs_module


_VALID_UUID_1 = "f4d10d8b-1234-4abc-89ab-cdef01234567"
_VALID_UUID_2 = "a1b2c3d4-5678-4def-89ab-cdef01234567"
_LEGACY_TEXT_KEY_1 = "万有引力"
_LEGACY_TEXT_KEY_2 = "legacy-string-id"


@pytest.fixture
def mixed_card_states_file(tmp_path: Path):
    """Write a fsrs_card_states.json file with mixed UUID + text keys."""
    file_path = tmp_path / "fsrs_card_states.json"
    payload = {
        _VALID_UUID_1: '{"stability":1.0,"difficulty":5.0}',
        _VALID_UUID_2: '{"stability":2.0,"difficulty":4.0}',
        _LEGACY_TEXT_KEY_1: '{"stability":3.0,"difficulty":6.0}',
        _LEGACY_TEXT_KEY_2: '{"stability":4.0,"difficulty":7.0}',
    }
    file_path.write_text(json.dumps(payload), encoding="utf-8")
    return file_path


@pytest.fixture
def patched_card_states_path(mixed_card_states_file, monkeypatch):
    """Point _CARD_STATES_FILE at our temp file for the duration of the test."""
    monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", mixed_card_states_file)
    return mixed_card_states_file


class TestLoadCardStatesDualBucket:
    """Scenario: Mixed UUID and legacy text keys on disk."""

    def test_mixed_keys_split_into_two_buckets(self, patched_card_states_path):
        merged = rs_module.ReviewService._load_card_states()
        uuid_states, legacy_states = rs_module.ReviewService._split_card_state_buckets(
            merged
        )
        # Two UUID keys land in primary bucket
        assert len(uuid_states) == 2
        assert _VALID_UUID_1 in uuid_states
        assert _VALID_UUID_2 in uuid_states
        # Two text keys land in legacy bucket
        assert len(legacy_states) == 2
        assert _LEGACY_TEXT_KEY_1 in legacy_states
        assert _LEGACY_TEXT_KEY_2 in legacy_states
        # No cross-contamination
        assert _VALID_UUID_1 not in legacy_states
        assert _LEGACY_TEXT_KEY_1 not in uuid_states

    def test_only_uuid_keys_returns_empty_legacy(self, tmp_path, monkeypatch):
        file_path = tmp_path / "fsrs_card_states.json"
        file_path.write_text(
            json.dumps({_VALID_UUID_1: '{"stability":1.0}'}),
            encoding="utf-8",
        )
        monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", file_path)
        merged = rs_module.ReviewService._load_card_states()
        uuid_states, legacy_states = rs_module.ReviewService._split_card_state_buckets(
            merged
        )
        assert _VALID_UUID_1 in uuid_states
        assert legacy_states == {}

    def test_only_legacy_keys_returns_empty_uuid(self, tmp_path, monkeypatch):
        file_path = tmp_path / "fsrs_card_states.json"
        file_path.write_text(
            json.dumps({_LEGACY_TEXT_KEY_1: '{"stability":1.0}'}),
            encoding="utf-8",
        )
        monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", file_path)
        merged = rs_module.ReviewService._load_card_states()
        uuid_states, legacy_states = rs_module.ReviewService._split_card_state_buckets(
            merged
        )
        assert uuid_states == {}
        assert _LEGACY_TEXT_KEY_1 in legacy_states

    def test_missing_file_returns_two_empty_dicts(self, tmp_path, monkeypatch):
        file_path = tmp_path / "does-not-exist.json"
        monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", file_path)
        merged = rs_module.ReviewService._load_card_states()
        uuid_states, legacy_states = rs_module.ReviewService._split_card_state_buckets(
            merged
        )
        assert uuid_states == {}
        assert legacy_states == {}

    def test_corrupt_file_returns_two_empty_dicts(self, tmp_path, monkeypatch):
        file_path = tmp_path / "corrupt.json"
        file_path.write_text("not valid json {{{", encoding="utf-8")
        monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", file_path)
        merged = rs_module.ReviewService._load_card_states()
        uuid_states, legacy_states = rs_module.ReviewService._split_card_state_buckets(
            merged
        )
        assert uuid_states == {}
        assert legacy_states == {}


class TestGetCardStateFallback:
    """Scenario: _get_card_state prefers UUID bucket, falls back to legacy."""

    def _make_service_with_states(self, uuid_dict, legacy_dict):
        """Build a stub ReviewService instance bypassing __init__ for unit
        isolation — we only need the two bucket dicts and the lookup helper.
        """
        svc = rs_module.ReviewService.__new__(rs_module.ReviewService)
        svc._card_states = uuid_dict
        svc._legacy_card_states = legacy_dict
        return svc

    def test_uuid_hit_in_primary_bucket(self):
        svc = self._make_service_with_states(
            {_VALID_UUID_1: "uuid-data"},
            {_LEGACY_TEXT_KEY_1: "legacy-data"},
        )
        assert svc._get_card_state(_VALID_UUID_1) == "uuid-data"

    def test_legacy_hit_via_fallback(self, caplog):
        svc = self._make_service_with_states(
            {_VALID_UUID_1: "uuid-data"},
            {_LEGACY_TEXT_KEY_1: "legacy-data"},
        )
        # Looking up with the legacy text key — UUID lookup misses, legacy hits
        result = svc._get_card_state(_LEGACY_TEXT_KEY_1)
        assert result == "legacy-data"

    def test_complete_miss_returns_none(self):
        svc = self._make_service_with_states(
            {_VALID_UUID_1: "uuid-data"},
            {_LEGACY_TEXT_KEY_1: "legacy-data"},
        )
        assert svc._get_card_state("totally-unknown-key") is None

    def test_uuid_bucket_takes_precedence(self):
        """If somehow the same key exists in both buckets, UUID wins."""
        # NOTE: This shouldn't happen in practice (a key cannot be both
        # UUID-shaped and not-UUID-shaped) but the contract is "UUID first".
        svc = self._make_service_with_states(
            {_VALID_UUID_1: "uuid-version"},
            {_VALID_UUID_1: "legacy-version"},
        )
        assert svc._get_card_state(_VALID_UUID_1) == "uuid-version"
