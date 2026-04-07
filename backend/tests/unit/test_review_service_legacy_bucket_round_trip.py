"""Unit tests for ReviewService._save_card_states legacy bucket preservation.

Verifies the A6 Phase 0 fix: _save_card_states() must serialize the union of
both UUID and legacy text buckets so that pre-migration FSRS card states are
not silently dropped on save.

[Source: openspec/changes/a6-phase0-fsrs-card-state-bucket-preservation/specs/
 concept-identity/spec.md — Requirement "FSRS Card State Legacy Bucket
 Preservation On Save"]
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import review_service as rs_module

# Use shared isolate_card_states_file fixture from conftest.py — it patches
# _CARD_STATES_FILE to an empty tmp_path file so each test has isolation.
pytestmark = pytest.mark.usefixtures("isolate_card_states_file")


_VALID_UUID_1 = "f4d10d8b-1234-4abc-89ab-cdef01234567"
_VALID_UUID_2 = "a1b2c3d4-5678-4def-89ab-cdef01234567"
_LEGACY_TEXT_KEY_1 = "node123"
_LEGACY_TEXT_KEY_2 = "万有引力"

_UUID_1_PAYLOAD = '{"stability":1.0,"difficulty":5.0}'
_UUID_2_PAYLOAD = '{"stability":2.0,"difficulty":4.0}'
_LEGACY_1_PAYLOAD = '{"stability":3.0,"difficulty":6.0}'
_LEGACY_2_PAYLOAD = '{"stability":4.0,"difficulty":7.0}'


def _make_service(uuid_dict: dict, legacy_dict: dict) -> rs_module.ReviewService:
    """Build a ReviewService instance bypassing __init__ for unit isolation.

    The full __init__ wires up FSRSManager / CanvasService / TaskManager which
    are irrelevant for testing the serialization path. We only need the two
    bucket dicts and the lock attribute.
    """
    svc = rs_module.ReviewService.__new__(rs_module.ReviewService)
    svc._card_states = uuid_dict
    svc._legacy_card_states = legacy_dict
    return svc


def _write_disk_fixture(file_path: Path, payload: dict) -> None:
    """Write a raw fsrs_card_states.json fixture to disk."""
    file_path.write_text(json.dumps(payload), encoding="utf-8")


def _reload_from_disk(file_path: Path) -> tuple[dict, dict]:
    """Simulate a fresh ReviewService init against the patched file.

    Returns (uuid_states, legacy_states) after going through the real
    _load_card_states + _split_card_state_buckets code path.
    """
    merged = rs_module.ReviewService._load_card_states()
    uuid_states, legacy_states = rs_module.ReviewService._split_card_state_buckets(
        merged
    )
    return uuid_states, legacy_states


class TestLegacyBucketPreservationOnSave:
    """Spec Requirement: FSRS Card State Legacy Bucket Preservation On Save."""

    @pytest.mark.asyncio
    async def test_round_trip_preserves_both_buckets(self, isolate_card_states_file):
        """Scenario: Round-trip preserves both buckets.

        GIVEN disk contains 1 UUID entry AND 1 legacy text entry
        AND ReviewService init partitions them into _card_states and _legacy_card_states
        WHEN _save_card_states() is called
        AND a fresh ReviewService is re-initialized against the same file
        THEN both buckets still contain their original entries.
        """
        # Arrange: write mixed-bucket fixture + init via the patched path
        file_path = isolate_card_states_file
        _write_disk_fixture(
            file_path,
            {
                _VALID_UUID_1: _UUID_1_PAYLOAD,
                _LEGACY_TEXT_KEY_1: _LEGACY_1_PAYLOAD,
            },
        )
        initial_uuid, initial_legacy = _reload_from_disk(file_path)
        assert _VALID_UUID_1 in initial_uuid
        assert _LEGACY_TEXT_KEY_1 in initial_legacy

        svc = _make_service(initial_uuid, initial_legacy)

        # Act: save
        await svc._save_card_states()

        # Assert: fresh reload from disk has both buckets
        reloaded_uuid, reloaded_legacy = _reload_from_disk(file_path)
        assert reloaded_uuid == {_VALID_UUID_1: _UUID_1_PAYLOAD}, (
            f"UUID bucket corrupted or lost: {reloaded_uuid}"
        )
        assert reloaded_legacy == {_LEGACY_TEXT_KEY_1: _LEGACY_1_PAYLOAD}, (
            f"Legacy bucket silently dropped: {reloaded_legacy}"
        )

    @pytest.mark.asyncio
    async def test_empty_legacy_bucket_is_byte_equivalent_uuid_only(
        self, isolate_card_states_file
    ):
        """Scenario: Save with empty legacy bucket is byte-equivalent to UUID-only case.

        GIVEN _card_states has entries AND _legacy_card_states is empty
        WHEN _save_card_states() is called
        THEN the serialized JSON equals what json.dumps(self._card_states, ...) would
             have produced under the old (buggy) implementation.
        """
        file_path = isolate_card_states_file
        uuid_only = {
            _VALID_UUID_1: _UUID_1_PAYLOAD,
            _VALID_UUID_2: _UUID_2_PAYLOAD,
        }
        svc = _make_service(uuid_only, {})

        # Act
        await svc._save_card_states()

        # Assert: file bytes match what the old impl would have written
        expected = json.dumps(uuid_only, ensure_ascii=False, indent=2)
        actual = file_path.read_text(encoding="utf-8")
        assert actual == expected, (
            "Empty-legacy save should be byte-equivalent to json.dumps(self._card_states) — "
            f"expected {len(expected)} bytes, got {len(actual)} bytes"
        )

        # Reload sanity check: still 2 UUID entries, 0 legacy
        reloaded_uuid, reloaded_legacy = _reload_from_disk(file_path)
        assert len(reloaded_uuid) == 2
        assert reloaded_legacy == {}

    @pytest.mark.asyncio
    async def test_save_preserves_new_uuid_entries_via_save_card_state(
        self, isolate_card_states_file
    ):
        """Scenario: Save preserves new UUID entries written via save_card_state.

        GIVEN _card_states has {uuid-A} AND _legacy_card_states has {text-B}
        WHEN a new uuid-C is added to _card_states and _save_card_states() fires
        THEN re-loading yields all 3 entries: uuid-A, uuid-C in UUID bucket,
             text-B still in legacy bucket.
        """
        file_path = isolate_card_states_file
        svc = _make_service(
            {_VALID_UUID_1: _UUID_1_PAYLOAD},
            {_LEGACY_TEXT_KEY_2: _LEGACY_2_PAYLOAD},
        )

        # Simulate the mutation that save_card_state would do internally:
        # add a new UUID entry to _card_states then trigger save.
        svc._card_states[_VALID_UUID_2] = _UUID_2_PAYLOAD
        await svc._save_card_states()

        # Assert: reloaded state has all 3 entries in the right buckets
        reloaded_uuid, reloaded_legacy = _reload_from_disk(file_path)
        assert reloaded_uuid == {
            _VALID_UUID_1: _UUID_1_PAYLOAD,
            _VALID_UUID_2: _UUID_2_PAYLOAD,
        }, f"UUID bucket missing entries: {reloaded_uuid}"
        assert reloaded_legacy == {_LEGACY_TEXT_KEY_2: _LEGACY_2_PAYLOAD}, (
            f"Legacy bucket silently dropped: {reloaded_legacy}"
        )

        # Also verify the total on-disk entry count
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        assert len(raw) == 3, f"Expected 3 entries on disk, got {len(raw)}: {raw}"
