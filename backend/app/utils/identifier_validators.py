"""
Identifier validators for the concept-identity capability.

Provides strict format validators that the verification / memory / review
services use as a hard contract: any function accepting a `concept_id`
parameter MUST validate it is a UUID v4 string before propagating it to
storage layers (Neo4j, FSRS card cache, Graphiti).

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "UUID v4 Format Validation"]
"""

from __future__ import annotations

import re

# RFC 4122 UUID v4 — case-insensitive.
# Layout: 8-4-4-4-12 hex with the version nibble fixed to '4' and the
# variant nibble in {8, 9, a, b}. We deliberately reject v1/v3/v5
# (their version nibble would be 1/3/5) so that legacy IDs cannot leak
# into UUID-only code paths.
_UUID_V4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_uuid_v4(value: object) -> bool:
    """Return True iff value is a syntactically valid UUID v4 string.

    Strict by design — accepts only the v4 layout. v1/v3/v5 return False.
    Non-string inputs (None, int, dict, ...) return False without raising.

    Why a regex instead of `uuid.UUID(value, version=4)`:
      1. `uuid.UUID()` accepts any RFC 4122 version when constructed
         from a string; the `version=` argument is a hint, not a check.
         A v1 string like "550e8400-e29b-11d4-a716-446655440000" would
         pass `uuid.UUID(s, version=4)` without raising.
      2. Frontend uses `crypto.randomUUID()` which is always v4. We want
         a fail-fast contract: if a non-v4 ID shows up in a `concept_id`
         slot, that is itself a bug worth surfacing.
      3. The regex is ~3x faster than `uuid.UUID()` on the hot path
         (each verification session validates dozens of concept ids).

    Examples:
        >>> is_uuid_v4("f4d10d8b-1234-4abc-89ab-cdef01234567")
        True
        >>> is_uuid_v4("F4D10D8B-1234-4ABC-89AB-CDEF01234567")  # uppercase
        True
        >>> is_uuid_v4("550e8400-e29b-11d4-a716-446655440000")  # v1
        False
        >>> is_uuid_v4("not-a-uuid")
        False
        >>> is_uuid_v4(None)
        False
        >>> is_uuid_v4(12345)
        False
    """
    if not isinstance(value, str):
        return False
    return bool(_UUID_V4_PATTERN.match(value))
