"""ChatGPT-DR-2026-05-13 P0-5: Episode source_description typed tuples.

Reader and writer string sets were disjoint:
- Reader queried 'tip' / 'error_record' / 'conversation_archive'
- Writer wrote 'canvas_learning:misconception' / 'canvas_temporal:tip' etc.

This module defines canonical tuples used by reader Cypher IN list queries.
"""

from __future__ import annotations


TIP_SOURCES = (
    "tip",
    "canvas_learning:tip",
    "canvas_temporal:tip",
    "canvas_batch:tip",
)


MISCONCEPTION_SOURCES = (
    "error_record",
    "misconception-record",
    "canvas_learning:misconception",
    "canvas_temporal:misconception",
    "canvas_batch:misconception",
    "canvas_learning:error",
    "canvas_temporal:error",
)


CONVERSATION_ARCHIVE_SOURCES = (
    "conversation_archive",
    "canvas_learning:conversation",
    "canvas_temporal:conversation",
)


EXAM_SESSION_SOURCES = ("exam_session",)
EXAM_RECORD_SOURCES = ("exam_record",)
DISCOVERED_NODE_SOURCES = ("discovered_node",)


MASTERY_OVERRIDE_SOURCES = ("mastery-override",)
SELF_ASSESSMENT_SOURCES = ("self-assessment",)


DEFAULT_TIP_SOURCE = "canvas_learning:tip"
DEFAULT_MISCONCEPTION_SOURCE = "canvas_learning:misconception"
DEFAULT_CONVERSATION_ARCHIVE_SOURCE = "canvas_learning:conversation"
