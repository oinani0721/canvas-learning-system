# Tasks: A10 Phase 0 Hardening

## 1. Pre-change Verification

- [ ] 1.1 Re-confirm `mastery_level` at `mastery_engine.py:419` calls `self.effective_proficiency(concept)`
- [ ] 1.2 Re-confirm `mastery_label` at `mastery_engine.py:450` calls `self.mastery_level(concept)` (which recurses into `effective_proficiency`)
- [ ] 1.3 Re-confirm `canvas_service.py:598-616` uses the `Semaphore(12) + inner async gated func` pattern
- [ ] 1.4 Re-confirm `_get_kg_relevance` Cypher at `question_generator.py:755` only binds `n.id` (not `n.canvasId`)

## 2. Add MasteryEngine Public Helpers

- [ ] 2.1 Add `mastery_level_from_proficiency(self, eff: float, concept: ConceptState) -> int` to `MasteryEngine` (mirror the logic at `mastery_engine.py:412-444` but accept `eff` as parameter instead of recomputing)
- [ ] 2.2 Add `mastery_label_from_level(self, level: int) -> str` as a 2-line wrapper around `MASTERY_LABELS.get(level, "Unknown")`
- [ ] 2.3 Add docstrings noting the rationale (1x cost vs the existing 3x methods)

## 3. Extend ACPData and NodePriority Models

- [ ] 3.1 Add `mastery_degraded: Optional[str] = None` to `ACPData` in `backend/app/models/exam_models.py:203-225`
- [ ] 3.2 Add `mastery_degraded: Optional[str] = None` to `NodePriority` in `backend/app/models/exam_models.py:241-260`
- [ ] 3.3 Update both docstrings to list the possible values (`None`, `"concept_not_found"`, `"exception"`)

## 4. Refactor _get_mastery_data for Perf + Observability

- [ ] 4.1 In `backend/app/services/question_generator.py:_get_mastery_data`, compute `eff = engine.effective_proficiency(concept)` exactly once
- [ ] 4.2 Replace `engine.mastery_level(concept)` with `engine.mastery_level_from_proficiency(eff, concept)`
- [ ] 4.3 Replace `engine.mastery_label(concept)` with `engine.mastery_label_from_level(level)` (where `level` is the result of 4.2)
- [ ] 4.4 Add `"mastery_degraded": None` to the happy-path return dict
- [ ] 4.5 Add `"mastery_degraded": "concept_not_found"` to the `if not concept` branch
- [ ] 4.6 Add `"mastery_degraded": "exception"` to the except branch fallback dict
- [ ] 4.7 Update the docstring to describe the degraded contract

## 5. Update assemble_acp to Propagate mastery_degraded

- [ ] 5.1 In `question_generator.py:assemble_acp` at lines 264-271, add `acp.mastery_degraded = mastery.get("mastery_degraded")`
- [ ] 5.2 Verify all other `_get_mastery_data` callers (line 127 target_node_id path) handle the new dict key gracefully

## 6. Update select_target_node for Semaphore + mastery_degraded Propagation

- [ ] 6.1 In `question_generator.py:select_target_node`, create a function-local `semaphore = asyncio.Semaphore(20)` before the batch gather
- [ ] 6.2 Define `async def _gated_mastery(nid)` and `async def _gated_kg(nid)` wrappers using `async with semaphore:`
- [ ] 6.3 Replace the bare `self._get_mastery_data(nid)` in the gather with `_gated_mastery(nid)` (same for kg)
- [ ] 6.4 In the batch result processing loop, propagate `mastery_data.get("mastery_degraded")` into `NodePriority.mastery_degraded`
- [ ] 6.5 Preserve the existing `return_exceptions=True` and per-node degrade logging

## 7. Tighten _get_kg_relevance Cypher

- [ ] 7.1 In `question_generator.py:_get_kg_relevance`, change the Cypher MATCH line 755 from `MATCH (n:CanvasNode {id: $node_id})` to `MATCH (n:CanvasNode {id: $node_id, canvasId: $canvas_id})`
- [ ] 7.2 Keep the existing `WHERE neighbor.canvasId = $canvas_id` clause (belt-and-suspenders)
- [ ] 7.3 Update the function docstring to note the dual binding

## 8. Extend Unit Tests

- [ ] 8.1 In `backend/tests/unit/test_question_generator_mastery_data.py`, add `test_effective_proficiency_called_exactly_once` — use MagicMock to spy on `engine.effective_proficiency` call count
- [ ] 8.2 Add `test_concept_not_found_returns_degraded_marker` — mock `store.get_concept` to return None, assert `result["mastery_degraded"] == "concept_not_found"`
- [ ] 8.3 Add `test_exception_path_returns_degraded_marker` — mock `store.get_concept` to raise ValueError, assert `result["mastery_degraded"] == "exception"`
- [ ] 8.4 Add `test_mastery_level_from_proficiency_matches_mastery_level` — property test: for a pair (eff, concept), both methods produce the same level
- [ ] 8.5 Add `test_happy_path_includes_none_degraded` — regression guard for backward compatibility

## 9. Extend e2e Tests

- [ ] 9.1 In `backend/tests/e2e/test_a11_kg_relevance_e2e.py`, add `test_cross_canvas_node_id_isolation` — seed same node_id under two different canvasIds, verify `_get_kg_relevance` scopes correctly to the requested canvas
- [ ] 9.2 Add `test_semaphore_bounds_concurrent_gather` — use a mock Neo4j client that sleeps 10ms and counts in-flight calls; run `select_target_node` on a 50-node synthetic canvas; assert max concurrent ≤ 20
- [ ] 9.3 Verify the new tests coexist with the existing 11 A11 tests

## 10. Run Test Suites

- [ ] 10.1 Run `.venv/bin/pytest tests/unit/test_question_generator_mastery_data.py -xvs` — all new + existing tests pass
- [ ] 10.2 Run `.venv/bin/pytest tests/ -k "a11_kg_relevance and not (chaos or fuzz)" --tb=short -q` — A11 regression suite green
- [ ] 10.3 Run `.venv/bin/ruff format backend/app/services/question_generator.py backend/app/services/mastery_engine.py backend/app/models/exam_models.py backend/tests/unit/test_question_generator_mastery_data.py backend/tests/e2e/test_a11_kg_relevance_e2e.py`
- [ ] 10.4 If any test fails, fix and re-run before proceeding

## 11. Update A10-resolution-summary.md

- [ ] 11.1 Add a "## 13. Phase 0 Hardening (2026-04-07)" section to `docs/project-status/fr-exploration/A10-resolution-summary.md`
- [ ] 11.2 Document the 4 hardenings (observability / 1x perf / kg schema / Semaphore) with short rationale each
- [ ] 11.3 Link to this change's archive path

## 12. Validation

- [ ] 12.1 Run `npx openspec validate a10-phase0-hardening --strict` — 0 errors
- [ ] 12.2 Run `npx openspec status --change a10-phase0-hardening` — 4/4 artifacts complete

## 13. Archive + Commit + Push

- [ ] 13.1 Run `npx openspec archive a10-phase0-hardening -y` from project root
- [ ] 13.2 Verify the 3 new Requirements + 1 MODIFIED Requirement merged into `openspec/specs/algo-question/spec.md`
- [ ] 13.3 Run `git status` and confirm expected file set
- [ ] 13.4 Stage with explicit file list (no `git add -A`)
- [ ] 13.5 Commit with conventional message `fix(a10-phase0-hardening): observability + 1x perf + kg schema + bounded concurrency`
- [ ] 13.6 Verify lefthook pre-push A11 regression suite passes
- [ ] 13.7 Verify `git rev-parse HEAD == git rev-parse origin/main`
