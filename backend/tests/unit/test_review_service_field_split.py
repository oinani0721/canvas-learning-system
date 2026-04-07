"""Unit tests for ReviewService.save_card_state field semantics.

Verifies that after fix-concept-id-identity-unification:
  1. concept_id is validated as UUID v4 at entry
  2. memory_data dict contains explicit concept_id / concept_name fields
  3. Legacy `concept` field alias is preserved for backward compat
  4. concept_name is not required (during migration) but is honored when given

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "Card State Save Requires UUID"]
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import review_service as rs_module


_VALID_UUID = "f4d10d8b-1234-4abc-89ab-cdef01234567"


def _make_service():
    """Bypass __init__ — we only need a partially constructed service for
    unit isolation. graphiti_client is wired so the persist branch runs."""
    svc = rs_module.ReviewService.__new__(rs_module.ReviewService)
    svc._card_states = {}
    svc._legacy_card_states = {}
    svc._fsrs_manager = None
    svc.graphiti_client = MagicMock()  # truthy → persist branch executes
    svc._auto_persist_failures = 0
    return svc


class TestUuidValidationAtEntry:
    @pytest.mark.asyncio
    async def test_text_concept_id_rejected(self):
        svc = _make_service()
        result = await svc.save_card_state(
            concept_id="万有引力",
            card_data='{"stability":1.0}',
            canvas_name="phys",
            rating=3,
        )
        assert result is False
        # Cache must remain empty
        assert svc._card_states == {}

    @pytest.mark.asyncio
    async def test_legacy_string_id_rejected(self):
        svc = _make_service()
        result = await svc.save_card_state(
            concept_id="legacy-id",
            card_data='{"stability":1.0}',
            canvas_name="phys",
            rating=3,
        )
        assert result is False
        assert svc._card_states == {}

    @pytest.mark.asyncio
    async def test_v1_uuid_rejected(self):
        svc = _make_service()
        # v1 UUID has '1' as version nibble, not '4'
        result = await svc.save_card_state(
            concept_id="550e8400-e29b-11d4-a716-446655440000",
            card_data='{"stability":1.0}',
            canvas_name="phys",
            rating=3,
        )
        assert result is False
        assert svc._card_states == {}


class TestMemoryDataFieldSplit:
    @pytest.mark.asyncio
    async def test_uuid_save_writes_three_identity_fields(self):
        svc = _make_service()
        # Patch get_learning_memory_client to capture the memory_data dict
        captured = {}
        mock_client = MagicMock()
        mock_client.initialize = AsyncMock()

        async def _capture(memory_data):
            captured.update(memory_data)

        mock_client.add_learning_memory = AsyncMock(side_effect=_capture)

        with patch(
            "app.clients.graphiti_client.get_learning_memory_client",
            return_value=mock_client,
        ):
            result = await svc.save_card_state(
                concept_id=_VALID_UUID,
                card_data='{"stability":1.0}',
                canvas_name="phys",
                rating=4,
                concept_name="万有引力",
            )

        assert result is True
        # All three identity fields populated correctly
        assert captured["concept_id"] == _VALID_UUID
        assert captured["concept_name"] == "万有引力"
        assert captured["concept"] == "万有引力"  # legacy alias
        # And the cache hot path was updated
        assert svc._card_states[_VALID_UUID] == '{"stability":1.0}'

    @pytest.mark.asyncio
    async def test_uuid_save_without_concept_name_falls_back_to_id(self):
        """During migration, callers may not yet pass concept_name. Make sure
        the function still works — concept_name defaults to concept_id."""
        svc = _make_service()
        captured = {}
        mock_client = MagicMock()
        mock_client.initialize = AsyncMock()

        async def _capture(memory_data):
            captured.update(memory_data)

        mock_client.add_learning_memory = AsyncMock(side_effect=_capture)

        with patch(
            "app.clients.graphiti_client.get_learning_memory_client",
            return_value=mock_client,
        ):
            result = await svc.save_card_state(
                concept_id=_VALID_UUID,
                card_data='{"x":1}',
                canvas_name="phys",
                rating=2,
            )

        assert result is True
        assert captured["concept_id"] == _VALID_UUID
        # When concept_name is omitted we fall back to the UUID itself
        assert captured["concept_name"] == _VALID_UUID
        assert captured["concept"] == _VALID_UUID

    @pytest.mark.asyncio
    async def test_no_graphiti_client_still_caches(self):
        """Without graphiti_client wired, the in-memory cache is still updated."""
        svc = _make_service()
        svc.graphiti_client = None  # disable persist branch

        result = await svc.save_card_state(
            concept_id=_VALID_UUID,
            card_data='{"x":1}',
            canvas_name="phys",
            rating=3,
        )

        assert result is True
        assert svc._card_states[_VALID_UUID] == '{"x":1}'
