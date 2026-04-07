"""FR-KG-04 isolation Phase 4 — VaultNotesService group_id placeholder filter.

Phase 4 adds a ``group_id`` parameter to ``VaultNotesService.search()`` as
a placeholder for the multi-vault future. The semantics are:

- ``group_id=None`` → return results unchanged (backward-compat default,
  covers the current single-vault assumption).
- ``group_id="foo"`` → apply a **common-note downgrade** filter: a row
  SURVIVES if ``subject_id in ("foo", None)``. The ``None`` (unset /
  missing) case is treated as a *common / 通用主题* note that joins every
  group. This prevents the filter from collapsing to an empty list under
  the current ingestion paths that do not yet backfill subject_id
  consistently (F9 decision, 2026-04-07).

Once vault_notes ingestion starts writing subject_id on every document,
the common-note downgrade becomes a minority path and the filter becomes
load-bearing for explicit non-matching rows.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from agentic_rag.retrievers.vault_notes_retriever import (
    VaultNotesRetrieverConfig,
    VaultNotesService,
)


pytestmark = pytest.mark.asyncio


def _make_row(row_id: str, subject_id: str | None = None, nested_json: bool = False):
    """Build a fake LanceDB row. If nested_json=True, subject_id lives
    inside the stringified metadata_json blob (the pre-Phase-4 path)
    instead of being flattened onto metadata.
    """
    metadata: dict = {}
    if nested_json and subject_id is not None:
        metadata["metadata_json"] = json.dumps(
            {"subject_id": subject_id, "file_path": f"{row_id}.md"}
        )
    elif subject_id is not None:
        metadata["subject_id"] = subject_id
    return {
        "id": row_id,
        "score": 0.8,
        "metadata": metadata,
    }


def _make_service_with_results(rows):
    """Build a VaultNotesService whose LanceDB returns the given rows."""
    lancedb_mock = AsyncMock()
    lancedb_mock.search = AsyncMock(return_value=rows)
    return VaultNotesService(lancedb_mock, VaultNotesRetrieverConfig())


# ---------------------------------------------------------------------------
# Scenario A — group_id=None → no filtering (backward compat)
# ---------------------------------------------------------------------------


async def test_group_id_none_returns_all_rows():
    rows = [
        _make_row("r1", subject_id="physics"),
        _make_row("r2", subject_id="math"),
        _make_row("r3"),  # missing subject_id
    ]
    service = _make_service_with_results(rows)
    await service.initialize()

    out = await service.search(query="anything", num_results=10, group_id=None)

    ids = {r["id"] for r in out}
    assert ids == {"r1", "r2", "r3"}


# ---------------------------------------------------------------------------
# Scenario B — group_id="physics" → only physics row survives
# ---------------------------------------------------------------------------


async def test_group_id_physics_filters_to_physics_only():
    rows = [
        _make_row("r_phys", subject_id="physics"),
        _make_row("r_math", subject_id="math"),
    ]
    service = _make_service_with_results(rows)
    await service.initialize()

    out = await service.search(query="anything", num_results=10, group_id="physics")

    assert len(out) == 1
    assert out[0]["id"] == "r_phys"


# ---------------------------------------------------------------------------
# Scenario C — group_id with no matching NON-NULL subjects returns only common
# ---------------------------------------------------------------------------


async def test_group_id_with_no_explicit_match_returns_only_common_notes():
    """Under the common-note downgrade (F9), a row with subject_id=None
    still joins every group as a 'common' note. Explicit non-matching
    subject_ids remain excluded.
    """
    rows = [
        _make_row("r1", subject_id="physics"),
        _make_row("r2", subject_id="math"),
        _make_row("r_common"),  # no subject_id → common note
    ]
    service = _make_service_with_results(rows)
    await service.initialize()

    out = await service.search(query="anything", num_results=10, group_id="biology")

    ids = {r["id"] for r in out}
    # Explicit physics / math are excluded (subject != biology, subject != None)
    # Common note survives because its effective subject_id is None.
    assert ids == {"r_common"}


async def test_group_id_with_no_common_and_no_match_returns_empty():
    """Regression guard: when there are NO common notes AND no explicit
    matches, the filter still collapses to empty (no runaway fallback)."""
    rows = [
        _make_row("r1", subject_id="physics"),
        _make_row("r2", subject_id="math"),
    ]
    service = _make_service_with_results(rows)
    await service.initialize()

    out = await service.search(query="anything", num_results=10, group_id="biology")

    assert out == []


# ---------------------------------------------------------------------------
# Scenario D — rows missing subject_id are INCLUDED under filter as common notes
# ---------------------------------------------------------------------------


async def test_group_id_includes_rows_missing_subject_id_as_common():
    """F9: rows with no subject_id (or explicit None) are treated as
    common / 通用主题 notes that join every group's result set. This is
    the common-note downgrade; it prevents the filter from collapsing to
    zero results under current ingestion paths that do not backfill
    subject_id consistently.
    """
    rows = [
        _make_row("r_known", subject_id="physics"),
        _make_row("r_anon"),  # no subject_id in metadata or metadata_json → common
    ]
    service = _make_service_with_results(rows)
    await service.initialize()

    out = await service.search(query="anything", num_results=10, group_id="physics")

    ids = {r["id"] for r in out}
    # Both the explicit physics match AND the common (None-subject) note survive.
    assert ids == {"r_known", "r_anon"}


# ---------------------------------------------------------------------------
# Scenario E — subject_id only inside nested metadata_json string is still honored
# ---------------------------------------------------------------------------


async def test_group_id_honors_nested_metadata_json_subject():
    """Some ingestion paths only write subject_id into the JSON blob.
    The filter must peek into metadata_json after it's been parsed."""
    rows = [
        _make_row("r_nested", subject_id="physics", nested_json=True),
        _make_row("r_math_nested", subject_id="math", nested_json=True),
    ]
    service = _make_service_with_results(rows)
    await service.initialize()

    out = await service.search(query="anything", num_results=10, group_id="physics")

    assert len(out) == 1
    assert out[0]["id"] == "r_nested"
