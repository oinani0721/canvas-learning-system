# Design: Fix Question Generator Silent Mastery-Data Bug (A10 Phase 0)

## Context

### Discovery chain

This change is the direct outcome of a chain of three reviews:

1. **A10 original question** (`docs/project-status/fr-exploration/A10.md` line 88, frozen since Apr 5 2026): the user asked 「FSRS 的算法是如何和其他的算法进行融合的，没有理清楚」 — an architectural clarity question, not a bug report.

2. **A10 Phase 1 formalization** (`openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/`): we formalized the 5-signal `MasteryFusionEngine` contract as 4 ADDED Requirements under the `algo-fusion` capability. The change explicitly asserted "compute_fused_mastery returns zero external call sites" and recommended that future implementation work use `MODIFIED Requirements` to wire fusion into verification/recommendation/exam.

3. **ChatGPT Deep Research review of Phase 1** (Apr 7 2026): ChatGPT used GitHub connector to read the actual codebase and corrected our claim. It found that `mastery_engine.py:347-355` already calls `compute_fused_mastery(concept_id)` inside `effective_proficiency()`, and that `mastery_engine.py:563-567` includes the fusion result in `concept_to_response()`. The "zero call sites" claim was wrong.

### Deeper finding from following ChatGPT's hint

Following ChatGPT's correction, deeper exploration of `question_generator.py` revealed a **silent production bug** that the prior A10 analysis missed. The bug pattern:

- `question_generator.py:673-698` (`_get_mastery_data`) was written to consume `effective_proficiency` from `ConceptState`
- The implementation uses `getattr(concept, "effective_proficiency", 0.0)`
- But `backend/app/models/mastery_state.py:68-110` (`@dataclass class ConceptState`) does **not** define `effective_proficiency` as a field
- The class docstring at line 74 says: "Volatile values (retrievability, effective_proficiency) are computed on read and never stored."
- Therefore `getattr(... 0.0)` always returns the default `0.0`
- The same broken pattern affects 4 fields: `effective_proficiency`, `mastery_level`, `mastery_label`, `retrievability`
- The full backend grep `concept\.effective_proficiency\s*=` finds zero setters on `ConceptState` instances anywhere
- The correct call pattern (used at `backend/app/mcp/tools/mastery_tools.py:175`) is `result.effective_proficiency = engine.effective_proficiency(concept)` — calling the method on `MasteryEngine`, not reading an attribute on `ConceptState`

### Production impact

Because `acp.effective_proficiency` is always `0.0`:

| Location | Symptom |
|---|---|
| `question_generator.py:482-489` | Difficulty branch `if acp.effective_proficiency < 0.3` is always true → every question is silently classified as `"easy"`, never `medium-easy/medium-hard/hard` |
| `question_generator.py:493` | Rationale string always reads `effective_proficiency=0.00` |
| `question_generator.py:540` | Gemini prompt template variable `effective_proficiency` always renders `0.00` (LLM is told the learner has zero mastery for every concept) |
| `question_generator.py:551` | Fallback prompt contains `**精通度**: effective_proficiency=0.00` |
| `question_generator.py:620` | Fallback question generator receives `0.0` and always picks the simplest template |

The bug has been latent since Story 6.3 implementation (commit `836d098` only reformatted the code without changing the logic).

### Why "zero hits" was wrong but the broader narrative is right

The previous A10 narrative — "three parallel weighting systems that never read each other's results" — is **not** invalidated by this discovery. Instead, the discovery refines it:

- `MasteryFusionEngine.compute_fused_mastery` IS consumed by `MasteryEngine.effective_proficiency` (correct, not "zero call sites")
- `MasteryEngine.effective_proficiency` IS NOT consumed by `verification_service` (correct, no decoupling change)
- `MasteryEngine.effective_proficiency` IS NOT consumed by `recommendation_service` (correct, no decoupling change)
- `question_generator` **THINKS** it consumes `effective_proficiency` — but the path was broken from day one

The decoupling is real, just deeper than originally diagnosed. The fix in this change closes one of the four gaps; verification/recommendation/exam-priority remain as Phase 1+ work.

## Goals / Non-Goals

**Goals:**

1. Restore `question_generator._get_mastery_data` to actually read volatile mastery fields from `MasteryEngine`, not from non-existent `ConceptState` attributes.
2. Use the existing public `MasteryEngine.get_retrievability(concept)` method (lines 301-307) for retrievability — no new method needed (this corrects an early planning assumption that a wrapper had to be added).
3. Add regression tests covering the `effective_proficiency / mastery_level / mastery_label / retrievability` flow under fused-mastery-non-zero, override-blended, and not-assessed scenarios.
4. Update the e2e test mocks that hard-coded `effective_proficiency=0.0` (which currently "match" the broken behavior — they would have caught the bug if they used realistic values).
5. Codify the fix as a new Requirement under `algo-question` so future refactors cannot reintroduce the bug silently.
6. Update the A10-resolution-summary.md to document the discovery + correction.
7. Replace the placeholder `Purpose: TBD` in `openspec/specs/algo-fusion/spec.md` with a real Purpose.

**Non-Goals:**

- ❌ Modify `ConceptState` dataclass — its volatile-fields design is correct (Neo4j stores only stable state).
- ❌ Touch `verification_service`, `recommendation_service`, or `mastery_fusion.py` — those are Phase 1+ scope.
- ❌ Implement any of the 5 ChatGPT-recommended cases (ReviewPriorityEngine, advance_strategy, recommendation mastery factor, reliability weighting, ablation harness).
- ❌ Modify the original A10.md (88 lines preserved as the historical user question).
- ❌ Modify `openspec/specs/algo-fusion/spec.md` Requirements (only the Purpose paragraph).
- ❌ Archive `a10-phase0-fix-question-generator-mastery-bug` immediately and run follow-up changes — this change is self-contained and SHOULD be archived in the same commit because it includes both spec and code.

## Decisions

### Decision 1: Use existing `MasteryEngine.get_retrievability(concept)` public method

**Choice**: Discovery during implementation revealed `MasteryEngine.get_retrievability(concept)` already exists at lines 301-307 as a public wrapper around `_get_retrievability`. The Phase 0 fix calls this existing method instead of introducing a new one.

**Rationale**:
- The existing `freshness(concept)` method returns a `str` ("fresh"/"stale"/"due"), not a `[0,1]` float — so `freshness` is not the right method for `_get_mastery_data` to call.
- The existing `get_retrievability(concept)` method returns the `[0,1]` float we need, with a docstring explicitly stating "Used by signal adapters (FSRSRetrievabilitySignal) to avoid accessing private methods."
- This is a "no-op" architectural decision in retrospect: the public API was already there. The Phase 0 plan initially assumed a wrapper had to be added; reading the file revealed the wrapper already existed. We documented this as a Decision (not a Risk) so future readers see the corrected assumption.

**Alternative considered**: Add a redundant alias `retrievability(concept)` matching the noun form. **Rejected** as unnecessary code duplication.

### Decision 2: Use `get_mastery_engine()` lazy import inside `_get_mastery_data`

**Choice**: In the fixed `_get_mastery_data`, import `get_mastery_engine` lazily inside the function body (matching the existing lazy import pattern for `get_mastery_store`).

**Rationale**:
- `question_generator.py` currently uses lazy imports for `mastery_store` (line 676) to avoid circular imports and to keep the module top-level lightweight.
- Following the same pattern keeps the change minimal and consistent with the file's existing style.

**Alternative considered**: Top-level import. **Rejected** because it changes the file's import style and could introduce circular import risks (mastery_engine depends on mastery_store and signals which depend on store).

### Decision 3: Update broken e2e mocks rather than skip the test

**Choice**: `test_a11_kg_relevance_e2e.py` lines ~104 and ~236 currently mock `_get_mastery_data` to return `{"effective_proficiency": 0.0, ...}`. After the fix, these mocks must use realistic non-zero values (or mock `mastery_engine` directly).

**Rationale**:
- The current mocks "accidentally pass" because they match the broken production behavior. If we leave them as-is, the regression test loses its intended A11 kg_relevance coverage (the test was designed to verify priority ordering, which depends on non-zero effective_proficiency).
- Updating the mocks is part of the fix scope; otherwise the e2e test silently degrades.

**Alternative considered**: Mark e2e tests as skipped pending follow-up. **Rejected** because A11 is regression-protected by lefthook pre-push (see `lefthook.yml` and `.claude/rules` references) and skipping them defeats the gate.

### Decision 4: Archive in the same session

**Choice**: Unlike the previous A10 Phase 1 change (which was archived to escape the `.gitignore` rule for `openspec/changes/*/`), this Phase 0 change should also archive in the same session — but for a different reason.

**Rationale**:
- This change includes actual code fixes + spec deltas + tests. It is a self-contained, reviewable unit.
- Archiving immediately merges the new `algo-question` Requirement into `openspec/specs/algo-question/spec.md` and produces a clean git commit.
- The previous Phase 1 change's "RFC pending review" framing does not apply here — this Phase 0 fix is the result of that review.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| The fix exposes other latent bugs that depended on `acp.effective_proficiency == 0.0` | Run full test suite (unit + e2e + A11 regression) before commit; the change includes new regression tests for the 4 mastery fields |
| Adding `MasteryEngine.retrievability` could conflict with future renames | The method is a 3-line wrapper; if future work renames `_get_retrievability`, the wrapper can be inlined or deleted with no spec impact |
| `get_mastery_engine()` returns a non-fusion engine if called before startup (e.g., from a test fixture) | The engine still computes `min(p_mastery, R)` as a fallback, which is the documented Story 5.1 behavior; tests that need fusion should explicitly attach a fusion engine via `set_fusion_engine` |
| The new spec Requirement under `algo-question` could be misread as forbidding all `getattr` usage | The Requirement explicitly says "for `effective_proficiency / mastery_level / mastery_label / retrievability`" — other `getattr` usage in the file (e.g., `getattr(concept, "p_mastery", 0.1)` for stable fields) is unaffected and remains correct |
| Updating `test_a11_kg_relevance_e2e.py` mocks could introduce flakiness | New mocks use deterministic values; we run the test locally before commit |
| ChatGPT's "Discovered During ChatGPT Review" section in A10-resolution-summary.md could be misread as "ChatGPT found the silent bug" | We document the discovery chain explicitly: ChatGPT found the call-site claim error; we (Claude Code) found the silent bug while following up on ChatGPT's hint |

## Open Questions

(none — this Phase 0 change is intentionally narrow. The 7 Open Questions from `a10-fsrs-fusion-formalization/design.md` Section "Open Questions for ChatGPT Deep Research Review" remain open and will be addressed by Phase 1+ changes after the user reviews ChatGPT's full response.)

## Cross-Links

- `docs/project-status/fr-exploration/A10.md` — original 88-line user question (read-only, never modified)
- `docs/project-status/fr-exploration/A10-resolution-summary.md` — ChatGPT review entry; this change adds a "Discovered During ChatGPT Review (2026-04-07)" section
- `openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/proposal.md` — predecessor change that this Phase 0 fix corrects
- `openspec/specs/algo-fusion/spec.md` — Phase 1 baseline (this change updates only the Purpose, not Requirements)
- `openspec/specs/algo-question/spec.md` — destination of the new ADDED Requirement after archive
- `backend/app/services/mastery_engine.py:677-686` — `get_mastery_engine()` singleton entry point
- `backend/app/main.py:220-261` — startup wiring for fusion-enabled mastery engine
- `backend/app/services/question_generator.py:673-698` — buggy `_get_mastery_data` (target of the fix)
- `backend/app/mcp/tools/mastery_tools.py:175` — reference for the correct call pattern
- `backend/app/models/mastery_state.py:68-110` — `ConceptState` dataclass with explicit volatile-fields docstring
