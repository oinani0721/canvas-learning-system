"""Unit tests for FallbackSyncService._replay_scoring_entry_to_neo4j
concept_id contract (Phase 7 residual fix to fix-concept-id-identity-unification).

Context:
    Phase 1-6 (commit d569da0) introduced the `is_uuid_v4` contract across
    verification / memory / review services. An adversarial grep by Agent 2
    discovered a 5th leak in `fallback_sync_service.py`: the
    `_replay_scoring_entry_to_neo4j` helper pulled `concept_id` from the
    failed_writes.jsonl entry via `entry.get("concept_id", concept)` — which
    silently used the text `concept` field as the UUID fallback, violating
    the same contract fixed elsewhere.

Expected behavior after fix:
    - Valid UUID v4 concept_id → `record_score_history` is called with it.
    - Missing concept_id on entry → score_history is skipped + structured
      warning is logged.
    - Text concept_id (e.g. "量子力学") → skip + warn.
    - UUID v1 / v5 concept_id → skip + warn (strict v4-only contract).
    - Main MERGE path (`run_query` for the `LEARNED` relationship) is
      unaffected and still returns True — score_history is a
      non-fatal side-effect.

[Source: openspec/changes/fix-concept-id-identity-unification/tasks.md
 — Phase 7 "fallback_sync_service residual fix"]
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import fallback_sync_service as fss_module
from app.services.fallback_sync_service import FallbackSyncService


# ─────────────────────────────────────────────────────────────────────────
# Test fixtures — intentionally duplicated from test_story_38_8_fallback_sync
# to keep this Phase 7 regression file self-contained and movable.
# ─────────────────────────────────────────────────────────────────────────

_VALID_UUID_V4 = "f4d10d8b-1234-4abc-89ab-cdef01234567"
_UUID_V1 = "550e8400-e29b-11d4-a716-446655440000"  # version nibble = 1
_UUID_V5 = "550e8400-e29b-51d4-a716-446655440000"  # version nibble = 5
_TEXT_CONCEPT = "量子力学"
_CANVAS_NAME = "physics/quantum.canvas"
_SCORE = 85
_TIMESTAMP = "2026-04-07T10:00:00"


@pytest.fixture
def mock_neo4j() -> AsyncMock:
    """Healthy Neo4jClient mock — main MERGE returns should_update=True."""
    client = AsyncMock()
    client.is_fallback_mode = False
    client.health_check = AsyncMock(return_value=True)
    client.run_query = AsyncMock(return_value=[{"should_update": True}])
    client.record_score_history = AsyncMock(return_value=True)
    return client


@pytest.fixture
def sync_service(mock_neo4j) -> FallbackSyncService:
    return FallbackSyncService(neo4j_client=mock_neo4j)


@pytest.fixture
def mock_logger():
    """Patch the module-level structlog logger so we can assert on
    .warning() calls directly.

    structlog does NOT integrate with pytest's `caplog` by default
    (structlog emits to its own LoggerFactory, not stdlib logging),
    so patching the module attribute is the portable alternative.
    """
    with patch.object(fss_module, "logger", new=MagicMock()) as m:
        yield m


def _assert_skip_warning_emitted(mock_log: MagicMock) -> None:
    """Helper: assert exactly one warning containing the contract sentinel
    text was emitted."""
    warning_calls = [c for c in mock_log.warning.call_args_list]
    assert len(warning_calls) >= 1, (
        f"expected at least one logger.warning call, got: {warning_calls}"
    )
    # The message is the first positional arg; check it mentions the skip.
    messages = [
        c.args[0] if c.args else ""
        for c in warning_calls
    ]
    assert any("Skipping score_history" in m for m in messages), (
        f"expected a 'Skipping score_history' warning, got: {messages}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 1: Valid UUID v4 concept_id — record_score_history IS called
# ═══════════════════════════════════════════════════════════════════════════


class TestScenarioValidUuidPassThrough:
    """A well-formed entry with UUID v4 concept_id should propagate to
    record_score_history unchanged."""

    @pytest.mark.asyncio
    async def test_valid_uuid_v4_calls_record_score_history(
        self, sync_service, mock_neo4j
    ):
        entry = {
            "concept": _TEXT_CONCEPT,
            "concept_id": _VALID_UUID_V4,
            "canvas_name": _CANVAS_NAME,
            "score": _SCORE,
            "timestamp": _TIMESTAMP,
        }

        result = await sync_service._replay_scoring_entry_to_neo4j(entry)

        assert result is True
        # Main MERGE fired
        assert mock_neo4j.run_query.await_count == 1
        # Score history fired with the actual UUID (not the text concept)
        assert mock_neo4j.record_score_history.await_count == 1
        call_kwargs = mock_neo4j.record_score_history.call_args.kwargs
        assert call_kwargs["concept_id"] == _VALID_UUID_V4
        assert call_kwargs["canvas_name"] == _CANVAS_NAME
        assert call_kwargs["score"] == _SCORE
        assert call_kwargs["timestamp"] == _TIMESTAMP


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 2: Missing concept_id — skip score history + warn
# ═══════════════════════════════════════════════════════════════════════════


class TestScenarioMissingConceptId:
    """Legacy entries that only carry the `concept` text field must not
    silently leak the text into record_score_history."""

    @pytest.mark.asyncio
    async def test_missing_concept_id_skips_score_history_and_warns(
        self, sync_service, mock_neo4j, mock_logger
    ):
        entry = {
            "concept": _TEXT_CONCEPT,
            # NOTE: no concept_id field at all
            "canvas_name": _CANVAS_NAME,
            "score": _SCORE,
            "timestamp": _TIMESTAMP,
        }

        result = await sync_service._replay_scoring_entry_to_neo4j(entry)

        # Main MERGE still succeeds (concept text is a valid Neo4j node key)
        assert result is True
        assert mock_neo4j.run_query.await_count == 1

        # Score history path is skipped
        assert mock_neo4j.record_score_history.await_count == 0

        # A structured warning is emitted citing the skip
        _assert_skip_warning_emitted(mock_logger)
        # The extra payload captures the actual missing id (None)
        warn_call = mock_logger.warning.call_args_list[0]
        assert warn_call.kwargs["extra"]["concept_id_type"] == "NoneType"


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 3: Text concept_id (not UUID at all) — skip + warn
# ═══════════════════════════════════════════════════════════════════════════


class TestScenarioTextConceptId:
    """Some older entries were written with `concept_id: <text>` by mistake.
    This must be rejected by the UUID v4 guard."""

    @pytest.mark.asyncio
    async def test_text_concept_id_skips_score_history_and_warns(
        self, sync_service, mock_neo4j, mock_logger
    ):
        entry = {
            "concept": _TEXT_CONCEPT,
            "concept_id": _TEXT_CONCEPT,  # text masquerading as UUID
            "canvas_name": _CANVAS_NAME,
            "score": _SCORE,
            "timestamp": _TIMESTAMP,
        }

        result = await sync_service._replay_scoring_entry_to_neo4j(entry)

        assert result is True
        assert mock_neo4j.run_query.await_count == 1
        assert mock_neo4j.record_score_history.await_count == 0
        _assert_skip_warning_emitted(mock_logger)
        # The extra payload preserves the offending text for debugging
        warn_call = mock_logger.warning.call_args_list[0]
        assert warn_call.kwargs["extra"]["concept_id_type"] == "str"
        assert warn_call.kwargs["extra"]["concept_id_preview"] == _TEXT_CONCEPT


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 4: UUID v1 / v5 — strict v4-only contract rejects both
# ═══════════════════════════════════════════════════════════════════════════


class TestScenarioNonV4Uuid:
    """is_uuid_v4 is strict: only v4 layout passes. v1/v5 must be rejected
    to prevent legacy-id leaks (see identifier_validators.py docstring)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "bad_uuid",
        [_UUID_V1, _UUID_V5],
        ids=["uuid_v1", "uuid_v5"],
    )
    async def test_non_v4_uuid_skips_score_history_and_warns(
        self, sync_service, mock_neo4j, mock_logger, bad_uuid
    ):
        entry = {
            "concept": _TEXT_CONCEPT,
            "concept_id": bad_uuid,
            "canvas_name": _CANVAS_NAME,
            "score": _SCORE,
            "timestamp": _TIMESTAMP,
        }

        result = await sync_service._replay_scoring_entry_to_neo4j(entry)

        assert result is True
        assert mock_neo4j.run_query.await_count == 1
        assert mock_neo4j.record_score_history.await_count == 0
        _assert_skip_warning_emitted(mock_logger)
        warn_call = mock_logger.warning.call_args_list[0]
        assert warn_call.kwargs["extra"]["concept_id_preview"] == bad_uuid


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 5: Main MERGE still executes when score_history is skipped
# ═══════════════════════════════════════════════════════════════════════════


class TestScenarioMainMergeStillSucceedsOnSkip:
    """The whole point of 'skip + warn' instead of 'raise' is that the
    main LEARNED relationship MERGE has already executed successfully by
    the time we validate concept_id for score_history. Skipping score_history
    must not retroactively undo the main write, and must not cause the
    caller to mark this entry as 'still pending'."""

    @pytest.mark.asyncio
    async def test_main_merge_runs_even_when_concept_id_invalid(
        self, sync_service, mock_neo4j
    ):
        entry = {
            "concept": _TEXT_CONCEPT,
            "concept_id": "clearly-not-a-uuid",
            "canvas_name": _CANVAS_NAME,
            "score": _SCORE,
            "timestamp": _TIMESTAMP,
        }

        result = await sync_service._replay_scoring_entry_to_neo4j(entry)

        # Contract: main MERGE's run_query fired exactly once
        assert mock_neo4j.run_query.await_count == 1
        merge_call = mock_neo4j.run_query.await_args_list[0]
        assert merge_call.kwargs["concept"] == _TEXT_CONCEPT
        assert merge_call.kwargs["score"] == _SCORE

        # Score history was skipped
        assert mock_neo4j.record_score_history.await_count == 0

        # But the caller sees success → entry is removed from pending queue
        assert result is True
