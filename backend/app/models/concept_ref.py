"""
ConceptRef — the lingua franca for concept identity across services.

A `ConceptRef` carries a concept's *machine* identity (`concept_id`,
always a UUID v4 string) alongside its *display* identity
(`concept_name`, the human-readable text shown to users and LLMs).
By keeping these two slots explicit and immutable we make it impossible
for downstream code to mistakenly use one in place of the other — which
was the root cause of the FSRS rerank / difficulty adaptation 100% miss
bugs documented in the fix-concept-id-identity-unification proposal.

Usage:
    from app.models.concept_ref import ConceptRef

    ref = ConceptRef(
        concept_id="f4d10d8b-1234-4abc-89ab-cdef01234567",
        concept_name="万有引力",
        canvas_id="physics_101",
    )

    # Always pass concept_id to Neo4j / FSRS / mastery layers:
    score_history = await memory.get_concept_score_history(
        concept_id=ref.concept_id,
        canvas_name=ref.canvas_id,
    )

    # Always pass concept_name to LLM prompts and user-facing text:
    prompt = f"请解释概念：{ref.concept_name}"

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "ConceptRef Construction Invariant"]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.utils.identifier_validators import is_uuid_v4


@dataclass(frozen=True)
class ConceptRef:
    """Immutable reference to a concept with explicit identity separation.

    Fields:
        concept_id: UUID v4 string — the machine identity used as a
            primary key in Neo4j (`CanvasNode.id`), the FSRS card cache
            (`review_service._card_states`), and the mastery store.
        concept_name: Human-readable text — used in LLM prompts, user
            messages, and Graphiti `concept_name` field. Must be
            non-empty and must not look like a filesystem path
            (filesystem-shaped names usually indicate that a path
            leaked into a slot expecting a concept).
        canvas_id: Optional canvas scope. Reserved for future
            per-canvas isolation (FR-KG-04 follow-ups). Currently
            informational.

    Invariants (enforced in __post_init__, raise ValueError on violation):
        1. `concept_id` is a syntactically valid UUID v4 string.
        2. `concept_name` is a non-empty string.
        3. `concept_name` does not start with `"/"` (path leakage guard).

    Why frozen=True:
        Prevents callers from mutating concept_id after construction —
        the original bug class involved the same dict being passed to
        multiple functions, each of which would set the `concept` key
        to a different thing (sometimes UUID, sometimes text). Freezing
        the dataclass makes such mutation impossible.
    """

    concept_id: str
    concept_name: str
    canvas_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not is_uuid_v4(self.concept_id):
            raise ValueError(f"concept_id must be UUID v4, got: {self.concept_id!r}")
        if not isinstance(self.concept_name, str) or not self.concept_name:
            raise ValueError(
                f"concept_name must be non-empty string, got: {self.concept_name!r}"
            )
        if self.concept_name.startswith("/"):
            raise ValueError(
                f"concept_name must not be a path, got: {self.concept_name!r}"
            )
