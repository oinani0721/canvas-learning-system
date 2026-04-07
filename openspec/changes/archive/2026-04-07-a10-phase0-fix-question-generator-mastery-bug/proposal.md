# Proposal: Fix Question Generator Silent Mastery-Data Bug (A10 Phase 0)

## Why

This change fixes a long-standing **silent production bug** in `backend/app/services/question_generator.py:_get_mastery_data` discovered during ChatGPT Deep Research review of A10 (`docs/project-status/fr-exploration/A10.md`, line 88: 「FSRS 的算法是如何和其他的算法进行融合的，没有理清楚」).

The chain of discovery:

1. The previous A10 change [`a10-fsrs-fusion-formalization`](../archive/2026-04-07-a10-fsrs-fusion-formalization/proposal.md) formalized the 5-signal `MasteryFusionEngine` contract and asserted that `compute_fused_mastery()` had **zero external call sites**.
2. ChatGPT Deep Research reviewed that change against the GitHub repository and corrected the assertion: `mastery_engine.effective_proficiency()` (Story 5.6) **does** consume `compute_fused_mastery()` and is wired into the global singleton at startup (`backend/app/main.py:220-261`).
3. Following ChatGPT's hint, deeper exploration revealed that **`question_generator.py:_get_mastery_data` (lines 673-698) attempts to read `effective_proficiency`, `mastery_level`, `mastery_label`, and `retrievability` from a `ConceptState` object using `getattr(concept, ..., default)`** — but `ConceptState` (defined at `backend/app/models/mastery_state.py:68-110`) explicitly stores **none** of these fields. Its docstring at line 74 states: "Volatile values (retrievability, effective_proficiency) are computed on read and never stored."

The result is a silent bug: `getattr(concept, "effective_proficiency", 0.0)` always returns `0.0` (the default), and similar defaults for the other fields. Downstream consequences in `question_generator.py`:

- **Difficulty selection** (lines 482-489): The branch `if acp.effective_proficiency < 0.3` is **always true** because `0.0 < 0.3`. Every generated exam question is silently classified as `"easy"` difficulty regardless of the learner's actual mastery state.
- **Prompt rendering** (lines 540, 551): The Gemini prompt always renders `effective_proficiency=0.00`, telling the LLM the learner has zero mastery for every concept.
- **Difficulty rationale** (line 493): The user-facing rationale string always includes `effective_proficiency=0.00`.
- **Fallback question generation** (line 620): The fallback path receives `0.0` and always picks the simplest template branch.

The infrastructure to fix this is already in place. `backend/app/services/mastery_engine.py:677-686` exposes `get_mastery_engine()` as a global singleton that is fusion-enabled at startup. The correct call pattern exists at `backend/app/mcp/tools/mastery_tools.py:175`: `result.effective_proficiency = engine.effective_proficiency(concept)`. The bug is that `question_generator._get_mastery_data` was never updated to use this pattern — it continues to read fields off `ConceptState` that are by design absent.

This is an A10 **Phase 0 fix**: it precedes the larger architectural decisions (Phase 1 KG-relevance integration, Phase 2 verification ranking, Phase 3 recommendation ranking, Phase 4 ablation, Phase 5 reliability weighting) because **no architectural improvement is possible until question_generator stops feeding the LLM and difficulty selector with hard-coded zeros**.

## What Changes

- **FIXED** `backend/app/services/question_generator.py:_get_mastery_data` (lines 673-698): replace `getattr(concept, ...)` reads with calls to `MasteryEngine` methods (`effective_proficiency`, `mastery_level`, `mastery_label`, `retrievability`) obtained via `get_mastery_engine()` singleton
- **(no change to `mastery_engine.py`)** — the existing public method `MasteryEngine.get_retrievability(concept)` (lines 301-307) already wraps the private `_get_retrievability`, so no new method is needed. The Phase 0 fix simply calls this existing public API.
- **NEW** `backend/tests/unit/test_question_generator_mastery_data.py`: 4 regression scenarios covering fused mastery flow, override blending, not-assessed concepts, and difficulty selection across the full mastery range
- **MODIFIED** `backend/tests/e2e/test_a11_kg_relevance_e2e.py`: existing mocks at lines ~104 and ~236 hard-code `effective_proficiency=0.0` (which currently "matches" the broken behavior). After the fix, these mocks must use realistic non-zero values or mock `mastery_engine` directly
- **NEW** spec requirement under `algo-question`: codify that question_generator MUST use `MasteryEngine` methods for volatile mastery field computation (not `getattr`)
- **MODIFIED** `docs/project-status/fr-exploration/A10-resolution-summary.md`: add a "Discovered During ChatGPT Review (2026-04-07)" section documenting the corrections to the previous change's claims and linking to this Phase 0 fix
- **MODIFIED** `openspec/specs/algo-fusion/spec.md` Purpose: replace the placeholder `TBD - created by archiving change a10-fsrs-fusion-formalization. Update Purpose after archive.` with a real one-paragraph Purpose

## Capabilities

### New Capabilities
(none)

### Modified Capabilities

- `algo-question`: add a new requirement codifying the mastery-data consumption pattern (this requirement does not change any existing 5 requirements about kg_relevance and NodePriority)

## Impact

- **Production behavior**: Every exam question generated by question_generator will now reflect the learner's actual mastery state. Difficulty levels will distribute across `easy / medium-easy / medium-hard / hard` instead of always being `easy`. Gemini prompts will receive accurate proficiency values.
- **Test impact**: 1 e2e test file (`test_a11_kg_relevance_e2e.py`) has mocks that hardcode the bug — they will need to be updated as part of this change. New regression test file (~4 scenarios) protects against future regressions.
- **Spec impact**: One new requirement under `algo-question`. The 4 ADDED Requirements from `a10-fsrs-fusion-formalization` (under `algo-fusion`) remain unchanged.
- **No changes** to: `ConceptState` dataclass (its volatile-fields design is correct), `verification_service`, `recommendation_service`, `mastery_fusion.py`, `signal_registry.py`, frontend code.
- **Risk**: `test_a11_kg_relevance_e2e.py` may have other implicit dependencies on the broken state. The change includes a `pytest -k question_generator` and A11 regression suite run as verification.
- **Rollback**: `git revert <commit>` restores the broken behavior. The new `MasteryEngine.retrievability` method is additive, so revert is clean.
