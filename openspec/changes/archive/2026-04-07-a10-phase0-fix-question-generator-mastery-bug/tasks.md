# Tasks: Fix Question Generator Silent Mastery-Data Bug (A10 Phase 0)

## 1. Pre-fix Verification

- [ ] 1.1 Confirm `ConceptState` (mastery_state.py:68-110) has no `effective_proficiency / mastery_level / mastery_label / retrievability` fields
- [ ] 1.2 Confirm `get_mastery_engine()` singleton exists at `mastery_engine.py:677-686` and `set_mastery_engine` is called from `main.py:220-261`
- [ ] 1.3 Confirm `mastery_tools.py:175` uses `engine.effective_proficiency(concept)` as the correct pattern

## 2. Verify Existing Public API (no new code needed)

- [ ] 2.1 Confirm `MasteryEngine.get_retrievability(concept)` exists at `mastery_engine.py:301-307` as a public wrapper around `_get_retrievability` (this was discovered during implementation; the Phase 0 plan initially assumed a wrapper had to be added)

## 3. Fix question_generator._get_mastery_data

- [ ] 3.1 In `backend/app/services/question_generator.py:673-698`, add `from app.services.mastery_engine import get_mastery_engine` as a lazy import inside the function (matching the existing `mastery_store` lazy import pattern)
- [ ] 3.2 Replace the 4 broken `getattr(concept, "<volatile_field>", default)` calls with: `engine.effective_proficiency(concept)`, `engine.mastery_level(concept)`, `engine.mastery_label(concept)`, `engine.get_retrievability(concept)`
- [ ] 3.3 Keep the stable-field reads (`p_mastery`) using direct attribute access (`concept.p_mastery`) — those are real fields on ConceptState
- [ ] 3.4 Verify the function still raises no exceptions when concept is None or when the engine is not yet wired

## 4. New Regression Tests

- [ ] 4.1 Create `backend/tests/unit/test_question_generator_mastery_data.py`
- [ ] 4.2 Test scenario: `test_effective_proficiency_from_fusion` — When `MasteryEngine` returns `effective_proficiency=0.85` for a concept with non-zero interactions, `_get_mastery_data` returns `0.85` (not 0.0)
- [ ] 4.3 Test scenario: `test_difficulty_selector_uses_real_proficiency` — When `acp.effective_proficiency=0.85` (via the fixed flow), the difficulty branch picks `"hard"`
- [ ] 4.4 Test scenario: `test_not_assessed_returns_zero` — When `interaction_count=0`, the returned `effective_proficiency` is `0.0` and `mastery_label` is `"Not Assessed"` (correctly)
- [ ] 4.5 Test scenario: `test_no_getattr_pattern_remains` — A code-grep check that `getattr(concept, "effective_proficiency"` does not appear in the file (regression guard)

## 5. Update Existing Broken e2e Mocks

- [ ] 5.1 Read `backend/tests/e2e/test_a11_kg_relevance_e2e.py` lines 100-130 and 220-250 to find the hard-coded `effective_proficiency=0.0` mocks
- [ ] 5.2 Replace the hard-coded values with realistic deterministic values (e.g., `0.45` for medium-mastery, `0.85` for high-mastery) OR mock `mastery_engine` directly to return controlled values
- [ ] 5.3 Verify the test still asserts what it intended (kg_relevance priority ordering)

## 6. Run Tests

- [ ] 6.1 Run `cd backend && .venv/bin/pytest tests/unit/test_question_generator_mastery_data.py -xvs` for the new tests
- [ ] 6.2 Run `cd backend && .venv/bin/pytest tests/e2e/test_a11_kg_relevance_e2e.py -xvs` for the updated e2e
- [ ] 6.3 Run the A11 regression suite (lefthook pre-push gate equivalent)
- [ ] 6.4 If any test fails, fix and re-run before commit

## 7. Documentation Updates

- [ ] 7.1 Update `docs/project-status/fr-exploration/A10-resolution-summary.md`:
  - Add a new section "## 12. Discovered During ChatGPT Review (2026-04-07)" between Section 11 and the "How to use this document" footer
  - Document: ChatGPT corrected the "zero call sites" claim; we then discovered the silent bug; this Phase 0 change fixes it
  - Add a link to this Phase 0 change archive path
- [ ] 7.2 Update `openspec/specs/algo-fusion/spec.md` Purpose:
  - Replace `TBD - created by archiving change a10-fsrs-fusion-formalization. Update Purpose after archive.` with a real Purpose paragraph describing the 5-signal fusion engine contract

## 8. Validation

- [ ] 8.1 Run `npx openspec validate a10-phase0-fix-question-generator-mastery-bug --strict` and confirm 0 errors
- [ ] 8.2 Run `npx openspec status --change a10-phase0-fix-question-generator-mastery-bug` and confirm `4/4 artifacts complete`

## 9. Archive + Commit + Push

- [ ] 9.1 Run `npx openspec archive a10-phase0-fix-question-generator-mastery-bug -y`
- [ ] 9.2 Verify the new Requirement merged into `openspec/specs/algo-question/spec.md`
- [ ] 9.3 Run `git status` and confirm the expected file set (code fix, new test, modified e2e, modified docs, modified algo-fusion/spec.md Purpose, archive directory, modified algo-question/spec.md)
- [ ] 9.4 Stage with explicit file list
- [ ] 9.5 Commit with conventional message `fix(A10-phase0): question_generator mastery_data silent bug — call MasteryEngine instead of getattr`
- [ ] 9.6 Verify lefthook pre-push backend-smoke passes
- [ ] 9.7 Verify `git rev-parse HEAD == origin/main`
