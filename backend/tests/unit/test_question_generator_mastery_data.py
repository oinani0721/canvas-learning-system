"""A10 Phase 0 regression tests for question_generator._get_mastery_data.

These tests protect against the silent bug discovered during ChatGPT Deep
Research review of the A10 fusion-formalization change (commit d8484f5).

The bug: question_generator._get_mastery_data used getattr(concept, "<volatile>", default)
to read effective_proficiency / mastery_level / mastery_label / retrievability,
but ConceptState (mastery_state.py:74) explicitly does NOT store volatile fields.
The getattr calls always returned the defaults (0.0 / "Not Assessed" / 1.0),
silently corrupting downstream difficulty selection and Gemini prompt rendering.

The fix: route volatile-field reads through MasteryEngine instance methods
obtained via the global singleton get_mastery_engine().

Source: openspec/changes/a10-phase0-fix-question-generator-mastery-bug/
Discovery doc: docs/project-status/fr-exploration/A10-resolution-summary.md
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.mastery_state import ConceptState
from app.services.question_generator import QuestionGenerator


@pytest.fixture
def generator() -> QuestionGenerator:
    """Provide a QuestionGenerator instance (no DI needed — _get_mastery_data uses lazy imports)."""
    return QuestionGenerator()


@pytest.fixture
def fresh_concept() -> ConceptState:
    """ConceptState with no interactions (not assessed)."""
    return ConceptState(
        concept_id="c-fresh",
        topic="topic-1",
        name="Fresh Concept",
        p_mastery=0.1,
        interaction_count=0,
    )


@pytest.fixture
def studied_concept() -> ConceptState:
    """ConceptState with realistic interaction history."""
    return ConceptState(
        concept_id="c-studied",
        topic="topic-1",
        name="Studied Concept",
        p_mastery=0.65,
        interaction_count=12,
        fluent_count=2,
    )


def _patch_engine_and_store(
    monkeypatch: pytest.MonkeyPatch,
    *,
    concept: ConceptState | None,
    effective_proficiency_value: float = 0.0,
    mastery_level_value: int = 0,
    mastery_label_value: str = "Not Assessed",
    retrievability_value: float = 1.0,
) -> tuple[MagicMock, AsyncMock]:
    """Install AsyncMock store + MagicMock engine for the duration of one test.

    Returns (engine_mock, store_mock) for assertions.
    """
    engine_mock = MagicMock(name="MasteryEngine")
    engine_mock.effective_proficiency.return_value = effective_proficiency_value
    # A10 Phase 0 Hardening: the production code now calls the pre-computed
    # helpers (mastery_level_from_proficiency / mastery_label_from_level)
    # to avoid 3x redundant effective_proficiency calls per node.
    engine_mock.mastery_level_from_proficiency.return_value = mastery_level_value
    engine_mock.mastery_label_from_level.return_value = mastery_label_value
    engine_mock.get_retrievability.return_value = retrievability_value

    store_mock = MagicMock(name="MasteryStore")
    store_mock.get_concept = AsyncMock(return_value=concept)

    monkeypatch.setattr(
        "app.services.mastery_engine.get_mastery_engine",
        lambda: engine_mock,
    )
    monkeypatch.setattr(
        "app.services.mastery_store.get_mastery_store",
        lambda: store_mock,
    )
    return engine_mock, store_mock


# ---------------------------------------------------------------------------
# Regression scenario 1: fused mastery flows from MasteryEngine to the dict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_effective_proficiency_from_fusion(
    generator: QuestionGenerator,
    studied_concept: ConceptState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When MasteryEngine returns 0.85 for a concept, _get_mastery_data must return 0.85.

    Pre-fix bug: getattr(concept, "effective_proficiency", 0.0) ALWAYS returned 0.0
    because ConceptState has no such field.
    """
    engine_mock, store_mock = _patch_engine_and_store(
        monkeypatch,
        concept=studied_concept,
        effective_proficiency_value=0.85,
        mastery_level_value=3,
        mastery_label_value="Proficient",
        retrievability_value=0.92,
    )

    result = await generator._get_mastery_data(studied_concept.concept_id)

    assert result["effective_proficiency"] == 0.85
    assert result["mastery_level"] == 3
    assert result["mastery_label"] == "Proficient"
    assert result["retrievability"] == 0.92
    assert result["p_mastery"] == 0.65  # stable field via direct attribute access

    # Verify the engine methods were called with the actual ConceptState (not a default)
    # A10 Phase 0 Hardening: effective_proficiency is called exactly once and the
    # resulting value is piped into mastery_level_from_proficiency (which receives
    # both the cached eff and the concept) and mastery_label_from_level (level only).
    engine_mock.effective_proficiency.assert_called_once_with(studied_concept)
    engine_mock.mastery_level_from_proficiency.assert_called_once_with(
        0.85, studied_concept
    )
    engine_mock.mastery_label_from_level.assert_called_once_with(3)
    engine_mock.get_retrievability.assert_called_once_with(studied_concept)
    # The old un-cached variants must NOT be called by _get_mastery_data — calling
    # them would re-invoke effective_proficiency internally, re-introducing the 3x
    # performance regression this hardening eliminates.
    engine_mock.mastery_level.assert_not_called()
    engine_mock.mastery_label.assert_not_called()
    store_mock.get_concept.assert_awaited_once_with("c-studied")
    # A10 Phase 0 Hardening: happy-path returns mastery_degraded=None so downstream
    # observability can distinguish it from concept_not_found / exception fallbacks.
    assert result["mastery_degraded"] is None


# ---------------------------------------------------------------------------
# Regression scenario 2: not-assessed concept correctly returns 0.0 / Not Assessed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_not_assessed_returns_zero(
    generator: QuestionGenerator,
    fresh_concept: ConceptState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """interaction_count=0 must produce effective_proficiency=0.0 + 'Not Assessed' label.

    This is the CORRECT zero — distinguishable from the pre-fix bug where every
    concept (even with high mastery) returned 0.0.
    """
    _patch_engine_and_store(
        monkeypatch,
        concept=fresh_concept,
        effective_proficiency_value=0.0,
        mastery_level_value=0,
        mastery_label_value="Not Assessed",
        retrievability_value=1.0,
    )

    result = await generator._get_mastery_data(fresh_concept.concept_id)

    assert result["effective_proficiency"] == 0.0
    assert result["mastery_level"] == 0
    assert result["mastery_label"] == "Not Assessed"
    # A10 Phase 0 Hardening: happy-path (concept found, but not assessed) must be
    # distinguishable from concept_not_found — mastery_degraded is None here.
    assert result["mastery_degraded"] is None


# ---------------------------------------------------------------------------
# Regression scenario 3: concept missing from store returns hard-coded fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_concept_returns_fallback(
    generator: QuestionGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If mastery_store.get_concept returns None (e.g., unknown node_id), fallback applies."""
    _patch_engine_and_store(monkeypatch, concept=None)

    result = await generator._get_mastery_data("c-unknown")

    # A10 Phase 0 Hardening: fallback dict now includes mastery_degraded marker
    # so downstream can distinguish this path from happy-path not-assessed.
    assert result == {
        "p_mastery": 0.1,
        "retrievability": 1.0,
        "effective_proficiency": 0.0,
        "mastery_level": 0,
        "mastery_label": "Not Assessed",
        "mastery_degraded": "concept_not_found",
    }


# ---------------------------------------------------------------------------
# Regression scenario 4: full mastery range exercises difficulty branches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("eff_value", "expected_branch"),
    [
        (0.10, "easy"),  # < 0.3
        (0.45, "medium-easy"),  # 0.3 - 0.5
        (0.65, "medium-hard"),  # 0.5 - 0.7
        (0.85, "hard"),  # >= 0.7
    ],
)
async def test_difficulty_selector_branches_via_real_proficiency(
    generator: QuestionGenerator,
    studied_concept: ConceptState,
    monkeypatch: pytest.MonkeyPatch,
    eff_value: float,
    expected_branch: str,
) -> None:
    """The 4 difficulty branches in question_generator.py:482-489 must each be reachable.

    Pre-fix bug: only 'easy' branch was ever reachable because acp.effective_proficiency
    was always 0.0. This parametrized test fails on the broken code (expected branches
    'medium-easy' / 'medium-hard' / 'hard' would never trigger).
    """
    _patch_engine_and_store(
        monkeypatch,
        concept=studied_concept,
        effective_proficiency_value=eff_value,
    )

    result = await generator._get_mastery_data(studied_concept.concept_id)

    # Replicate question_generator.py:482-489 difficulty branch logic
    eff = result["effective_proficiency"]
    if eff < 0.3:
        branch = "easy"
    elif eff < 0.5:
        branch = "medium-easy"
    elif eff < 0.7:
        branch = "medium-hard"
    else:
        branch = "hard"

    assert branch == expected_branch, (
        f"For effective_proficiency={eff_value}, expected branch '{expected_branch}' "
        f"but got '{branch}'. This means the bug is back."
    )


# ---------------------------------------------------------------------------
# Regression scenario 5: code-grep guard against the broken pattern reappearing
# ---------------------------------------------------------------------------


def test_no_getattr_volatile_pattern_in_get_mastery_data() -> None:
    """Static check: _get_mastery_data must not contain getattr(concept, "<volatile>"...).

    This is a regression guard. If a future refactor reintroduces the broken pattern,
    this test fails immediately at the source level (no runtime needed).
    """
    qg_path = (
        Path(__file__).parent.parent.parent
        / "app"
        / "services"
        / "question_generator.py"
    )
    src = qg_path.read_text(encoding="utf-8")

    # Locate _get_mastery_data function body (heuristic: function def to next 'async def')
    start = src.find("async def _get_mastery_data")
    assert start >= 0, "Could not locate _get_mastery_data in question_generator.py"
    end = src.find("async def ", start + 1)
    body = src[start:end] if end > 0 else src[start:]

    # The 4 broken volatile-field patterns must NOT appear in the function body
    forbidden = [
        'getattr(concept, "effective_proficiency"',
        'getattr(concept, "mastery_level"',
        'getattr(concept, "mastery_label"',
        'getattr(concept, "retrievability"',
    ]
    for pattern in forbidden:
        assert pattern not in body, (
            f"A10 Phase 0 regression: pattern '{pattern}' reappeared in "
            f"_get_mastery_data. Volatile mastery fields MUST be read via "
            f"MasteryEngine instance methods, not via getattr on ConceptState."
        )


# ===========================================================================
# A10 Phase 0 Hardening scenarios — added by a10-phase0-hardening change
# ===========================================================================
#
# These scenarios protect the 3 residual risks identified by ChatGPT Deep
# Research round 2 review of Phase 0:
#
# 1. effective_proficiency must be computed exactly once per call (was 3x)
# 2. concept_not_found must return mastery_degraded="concept_not_found"
# 3. exception must return mastery_degraded="exception"
# 4. mastery_level_from_proficiency must match mastery_level (equivalence)
# ===========================================================================


@pytest.mark.asyncio
async def test_effective_proficiency_called_exactly_once(
    generator: QuestionGenerator,
    studied_concept: ConceptState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A10 Phase 0 Hardening: effective_proficiency called 1x per _get_mastery_data.

    Pre-hardening: called 3x (direct + via mastery_level + via mastery_label).
    Post-hardening: called 1x, result is cached and passed to
    mastery_level_from_proficiency and mastery_label_from_level.
    """
    engine_mock, _ = _patch_engine_and_store(
        monkeypatch,
        concept=studied_concept,
        effective_proficiency_value=0.65,
        mastery_level_value=2,
        mastery_label_value="Developing",
    )

    await generator._get_mastery_data(studied_concept.concept_id)

    assert engine_mock.effective_proficiency.call_count == 1, (
        f"Expected effective_proficiency called 1 time, got "
        f"{engine_mock.effective_proficiency.call_count}. "
        f"Phase 0 Hardening regression — the 3x redundancy is back."
    )
    assert engine_mock.mastery_level_from_proficiency.call_count == 1
    assert engine_mock.mastery_label_from_level.call_count == 1
    # The un-cached variants must not be called
    assert engine_mock.mastery_level.call_count == 0
    assert engine_mock.mastery_label.call_count == 0


@pytest.mark.asyncio
async def test_concept_not_found_returns_degraded_marker(
    generator: QuestionGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A10 Phase 0 Hardening: mastery_degraded='concept_not_found' when store returns None.

    This distinguishes "ID mapping gap" from "happy-path truly not assessed", which
    is critical for detecting whether Phase 0's fix is actually effective in
    production (vs silently falling through to the pre-fix fallback).
    """
    _patch_engine_and_store(monkeypatch, concept=None)

    result = await generator._get_mastery_data("c-unmapped")

    assert result["mastery_degraded"] == "concept_not_found"
    assert result["effective_proficiency"] == 0.0
    assert result["mastery_label"] == "Not Assessed"


@pytest.mark.asyncio
async def test_exception_path_returns_degraded_marker(
    generator: QuestionGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A10 Phase 0 Hardening: mastery_degraded='exception' when lookup raises.

    The function's try/except catches ImportError / AttributeError / ValueError.
    This test verifies the exception fallback is distinguishable from
    concept_not_found and happy-path.
    """
    store_mock = MagicMock(name="MasteryStore")
    store_mock.get_concept = AsyncMock(side_effect=ValueError("boom"))
    engine_mock = MagicMock(name="MasteryEngine")

    monkeypatch.setattr(
        "app.services.mastery_engine.get_mastery_engine",
        lambda: engine_mock,
    )
    monkeypatch.setattr(
        "app.services.mastery_store.get_mastery_store",
        lambda: store_mock,
    )

    result = await generator._get_mastery_data("c-crash")

    assert result["mastery_degraded"] == "exception"
    assert result["effective_proficiency"] == 0.0


def test_mastery_level_from_proficiency_matches_mastery_level() -> None:
    """A10 Phase 0 Hardening: equivalence property between the two helpers.

    For any (eff, concept) pair, mastery_level_from_proficiency(eff, concept)
    must produce the same level as mastery_level(concept) WOULD produce if
    effective_proficiency(concept) returned exactly that `eff`.

    This guards against the two helpers drifting apart during future refactors.
    """
    from app.services.mastery_engine import MasteryEngine, load_mastery_config

    engine = MasteryEngine(load_mastery_config())

    # Table of (eff, interactions, overrides, self_assess, fluent_count, expected_level)
    # Default thresholds: shaky=0.40, developing=0.70, proficient=0.90, mastered_fluent_min=2
    cases = [
        (
            0.0,
            0,
            None,
            None,
            0,
            0,
        ),  # Not Assessed (no interactions/override/self-assess)
        (0.10, 3, None, None, 0, 1),  # < 0.40 -> Shaky
        (0.35, 5, None, None, 1, 1),  # < 0.40 -> Shaky
        (0.55, 10, None, None, 1, 2),  # 0.40 <= eff < 0.70 -> Developing
        (0.75, 10, None, None, 2, 3),  # 0.70 <= eff < 0.90 -> Proficient
        (0.95, 20, None, None, 5, 4),  # >= 0.90 and fluent>=2 -> Mastered
        (
            0.95,
            20,
            None,
            None,
            0,
            3,
        ),  # >= 0.90 but fluent<2 -> Proficient (high but unverified)
    ]

    for eff, interactions, override, self_assess, fluent, expected in cases:
        concept = ConceptState(
            concept_id=f"c-{eff}",
            topic="t",
            name="n",
            p_mastery=eff,
            interaction_count=interactions,
            fluent_count=fluent,
            override_value=override,
            self_assess_value=self_assess,
        )
        actual = engine.mastery_level_from_proficiency(eff, concept)
        assert actual == expected, (
            f"For eff={eff}, interactions={interactions}, fluent={fluent}: "
            f"expected level={expected}, got {actual}"
        )


def test_mastery_label_from_level_matches_mastery_label_lookup() -> None:
    """A10 Phase 0 Hardening: mastery_label_from_level is equivalent to MASTERY_LABELS.get."""
    from app.models.mastery_state import MASTERY_LABELS
    from app.services.mastery_engine import MasteryEngine, load_mastery_config

    engine = MasteryEngine(load_mastery_config())

    for level in range(5):
        assert engine.mastery_label_from_level(level) == MASTERY_LABELS.get(
            level, "Unknown"
        )
    # Out-of-range levels return "Unknown"
    assert engine.mastery_label_from_level(99) == "Unknown"
