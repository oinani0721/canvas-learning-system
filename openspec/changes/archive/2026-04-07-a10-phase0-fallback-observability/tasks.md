# Tasks: A10 Phase 0 Fallback Observability

## 1. Pre-change Verification

- [ ] 1.1 Re-confirm `mastery_fusion.py:89` and `:100` set `is_fallback=False` (should be `True` per spec)
- [ ] 1.2 Re-confirm `mastery_fusion.py:120` sets `is_fallback=False` on happy path (should stay `False`)
- [ ] 1.3 Re-confirm `mastery_engine.py:332-371` `effective_proficiency` returns only `float` (loses fallback state)
- [ ] 1.4 Re-confirm `mastery_tools.py:39-62` `QueryMasteryOutput` lacks `mastery_degraded` field
- [ ] 1.5 Re-confirm `test_mastery_fusion.py` has zero `is_fallback` assertions (grep)

## 2. Fix mastery_fusion.py is_fallback

- [ ] 2.1 Change `mastery_fusion.py:89` from `is_fallback=False` to `is_fallback=True` in the "no active signals" branch
- [ ] 2.2 Change `mastery_fusion.py:100` from `is_fallback=False` to `is_fallback=True` in the "weight_sum <= 0" defensive branch
- [ ] 2.3 Confirm `mastery_fusion.py:120` (normal fusion) stays `is_fallback=False`
- [ ] 2.4 Add a comment referencing this change and the `algo-fusion` spec scenario

## 3. Add MasteryEngine.effective_proficiency_with_fallback_info

- [ ] 3.1 Add new public method `effective_proficiency_with_fallback_info(self, concept: ConceptState) -> tuple[float, bool]` to `MasteryEngine`
- [ ] 3.2 Move the current `effective_proficiency` body into the new method, tracking `fusion_fallback: bool` across the branches
- [ ] 3.3 In the "interaction_count == 0" early exit, return `(0.0_after_override_decay, False)` (not assessed is not a fallback)
- [ ] 3.4 In the "fusion_engine is None" branch, return `(min(p_mastery, R)_after_decay, True)` (fallback)
- [ ] 3.5 In the "fusion returned active_signal_count > 0" branch, return `(fused_value_after_decay, False)`
- [ ] 3.6 In the "fusion returned active_signal_count == 0" branch, return `(min(p_mastery, R)_after_decay, True)` (fallback)
- [ ] 3.7 Refactor `effective_proficiency(self, concept) -> float` to be a thin wrapper: `eff, _ = self.effective_proficiency_with_fallback_info(concept); return eff`

## 4. Update question_generator._get_mastery_data

- [ ] 4.1 In `_get_mastery_data`, replace `engine.effective_proficiency(concept)` with `eff, fusion_fallback = engine.effective_proficiency_with_fallback_info(concept)`
- [ ] 4.2 When `fusion_fallback` is `True`, set `mastery_degraded = "fusion_fallback"` in the happy-path return dict (the concept was found and the call succeeded, so it's not `concept_not_found` or `exception`)
- [ ] 4.3 When `fusion_fallback` is `False`, keep `mastery_degraded = None`
- [ ] 4.4 Verify the fallback dict for `concept_not_found` and `exception` paths are unchanged

## 5. Update mastery_tools.py QueryMasteryOutput

- [ ] 5.1 Add `mastery_degraded: Optional[str] = None` field to `QueryMasteryOutput` Pydantic model in `backend/app/mcp/tools/mastery_tools.py`
- [ ] 5.2 Add a docstring describing the possible values (mirror of `NodePriority.mastery_degraded`)
- [ ] 5.3 Verify `Optional` is already imported (should be — other fields use it)

## 6. Extend test_mastery_fusion.py

- [ ] 6.1 Update `test_no_signals_registered` (L157-164) to also assert `result.is_fallback == True`
- [ ] 6.2 Update `test_all_signals_no_data` (L166-175) to also assert `result.is_fallback == True`
- [ ] 6.3 Add new test `test_single_signal_active_is_fallback_false` — 1 active signal, assert `is_fallback == False`
- [ ] 6.4 Add new test `test_five_signals_active_is_fallback_false` — 5 active signals, assert `is_fallback == False`
- [ ] 6.5 Add new test `test_weight_sum_zero_is_fallback_true` — construct a FakeSignal with `get_weight() == 0.0`, verify defensive branch produces `is_fallback == True`

## 7. Extend test_question_generator_mastery_data.py

- [ ] 7.1 Add new test `test_fusion_fallback_propagates_to_mastery_degraded` — mock `effective_proficiency_with_fallback_info` to return `(0.3, True)`, assert `result["mastery_degraded"] == "fusion_fallback"`
- [ ] 7.2 Verify existing tests still pass after `_get_mastery_data` uses the new helper (update mock if needed)

## 8. Run Test Suites

- [ ] 8.1 Run `.venv/bin/pytest tests/unit/test_mastery_fusion.py -xvs` — all new + existing tests pass
- [ ] 8.2 Run `.venv/bin/pytest tests/unit/test_question_generator_mastery_data.py -xvs` — all tests pass
- [ ] 8.3 Run `.venv/bin/pytest tests/unit/test_kg_relevance_weighted.py tests/e2e/test_a11_kg_relevance_e2e.py -q` — A11 regression gate passes
- [ ] 8.4 Run `.venv/bin/ruff format` on the 5 modified Python files
- [ ] 8.5 If any test fails, fix and re-run before proceeding

## 9. Update A10-resolution-summary.md

- [ ] 9.1 Add a new section "## 14. Phase 0 Hardening #2: Fallback Observability (2026-04-07)" to `docs/project-status/fr-exploration/A10-resolution-summary.md`
- [ ] 9.2 Summarize the 3 gaps and their fixes
- [ ] 9.3 Link to this change's archive path

## 10. Validation

- [ ] 10.1 Run `npx openspec validate a10-phase0-fallback-observability --strict` — 0 errors
- [ ] 10.2 Run `npx openspec status --change a10-phase0-fallback-observability` — 4/4 artifacts complete

## 11. Archive + Commit + Push

- [ ] 11.1 Run `npx openspec archive a10-phase0-fallback-observability -y` from project root
- [ ] 11.2 Verify the MODIFIED Requirement merged into `openspec/specs/algo-question/spec.md`
- [ ] 11.3 Run `git status` and confirm expected file set
- [ ] 11.4 Stage with explicit file list (no `git add -A`)
- [ ] 11.5 Commit with conventional message `fix(a10-phase0-fallback-observability): is_fallback semantic + cross-layer observability`
- [ ] 11.6 Verify lefthook pre-push A11 regression suite passes
- [ ] 11.7 Verify `git rev-parse HEAD == git rev-parse origin/main`
