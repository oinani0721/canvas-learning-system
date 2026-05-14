"""ChatGPT-DR-2026-05-13 P0-5: source_description writer/reader contract tests.

Lock in the invariant that question_generator reader queries can actually
match what memory_service writers put into Neo4j. Historical bug:
- Writer wrote 'canvas_learning:misconception' / 'canvas_temporal:misconception'
- Reader queried 'error_record'
- Result: _get_error_history always returned empty, exam board could not
  see user misconceptions.

These tests pin both ends so future drift causes immediate CI failure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.source_descriptions import (
    CONVERSATION_ARCHIVE_SOURCES,
    DEFAULT_CONVERSATION_ARCHIVE_SOURCE,
    DEFAULT_MISCONCEPTION_SOURCE,
    DEFAULT_TIP_SOURCE,
    MISCONCEPTION_SOURCES,
    TIP_SOURCES,
)


# ════════════════════════════════════════════════════════════════════
# Default values are members of their source tuples
# ════════════════════════════════════════════════════════════════════


def test_default_tip_source_is_in_tip_sources():
    assert DEFAULT_TIP_SOURCE in TIP_SOURCES


def test_default_misconception_source_is_in_misconception_sources():
    assert DEFAULT_MISCONCEPTION_SOURCE in MISCONCEPTION_SOURCES


def test_default_conversation_archive_source_is_in_archive_sources():
    assert DEFAULT_CONVERSATION_ARCHIVE_SOURCE in CONVERSATION_ARCHIVE_SOURCES


# ════════════════════════════════════════════════════════════════════
# Legacy reader values stay in the tuples for back-compat
# ════════════════════════════════════════════════════════════════════


def test_legacy_tip_value_preserved():
    """Old reader queried = 'tip' — keep accepting it."""
    assert "tip" in TIP_SOURCES


def test_legacy_error_record_value_preserved():
    """Old reader queried = 'error_record' — keep accepting it."""
    assert "error_record" in MISCONCEPTION_SOURCES


def test_legacy_conversation_archive_value_preserved():
    """Old reader queried = 'conversation_archive' — keep accepting it."""
    assert "conversation_archive" in CONVERSATION_ARCHIVE_SOURCES


# ════════════════════════════════════════════════════════════════════
# Writer-side prefix values (memory_service.py actually writes these)
# ════════════════════════════════════════════════════════════════════


def test_writer_canvas_learning_tip_in_sources():
    """memory_service writes 'canvas_learning:tip' — reader must accept."""
    assert "canvas_learning:tip" in TIP_SOURCES


def test_writer_canvas_temporal_tip_in_sources():
    """memory_service writes 'canvas_temporal:tip' — reader must accept."""
    assert "canvas_temporal:tip" in TIP_SOURCES


def test_writer_canvas_learning_misconception_in_sources():
    """memory_service writes 'canvas_learning:misconception' — reader must accept."""
    assert "canvas_learning:misconception" in MISCONCEPTION_SOURCES


def test_writer_canvas_temporal_misconception_in_sources():
    """memory_service writes 'canvas_temporal:misconception' — reader must accept."""
    assert "canvas_temporal:misconception" in MISCONCEPTION_SOURCES


def test_writer_misconception_record_in_sources():
    """error_writer may write 'misconception-record' — reader must accept."""
    assert "misconception-record" in MISCONCEPTION_SOURCES


# ════════════════════════════════════════════════════════════════════
# question_generator.py grep: ensure IN list, not = string
# ════════════════════════════════════════════════════════════════════


def _read_question_generator_source() -> str:
    qg_path = (
        Path(__file__).parent.parent.parent
        / "app"
        / "services"
        / "question_generator.py"
    )
    return qg_path.read_text(encoding="utf-8")


def test_question_generator_uses_in_list_for_tips():
    """Reader must use IN list, not = 'tip' hardcoded."""
    src = _read_question_generator_source()
    assert "source_description IN $tip_sources" in src
    # Belt-and-braces: ensure the dead string literal is gone
    assert "source_description = 'tip'" not in src


def test_question_generator_uses_in_list_for_misconceptions():
    """Reader must use IN list, not = 'error_record' hardcoded."""
    src = _read_question_generator_source()
    assert "source_description IN $misconception_sources" in src
    assert "source_description = 'error_record'" not in src


def test_question_generator_uses_in_list_for_archive():
    """Reader must use IN list, not = 'conversation_archive' hardcoded."""
    src = _read_question_generator_source()
    assert "source_description IN $archive_sources" in src
    assert "source_description = 'conversation_archive'" not in src


def test_question_generator_imports_typed_constants():
    """question_generator must import from app.core.source_descriptions."""
    src = _read_question_generator_source()
    assert "from app.core.source_descriptions import" in src
    assert "TIP_SOURCES" in src
    assert "MISCONCEPTION_SOURCES" in src
    assert "CONVERSATION_ARCHIVE_SOURCES" in src


# ════════════════════════════════════════════════════════════════════
# Tuples must be non-empty (defense against accidental clear)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "tuple_name,tuple_value",
    [
        ("TIP_SOURCES", TIP_SOURCES),
        ("MISCONCEPTION_SOURCES", MISCONCEPTION_SOURCES),
        ("CONVERSATION_ARCHIVE_SOURCES", CONVERSATION_ARCHIVE_SOURCES),
    ],
)
def test_source_tuples_non_empty(tuple_name, tuple_value):
    assert len(tuple_value) > 0, f"{tuple_name} must not be empty"
