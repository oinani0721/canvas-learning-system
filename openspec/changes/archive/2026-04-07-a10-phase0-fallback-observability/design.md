# Design: A10 Phase 0 Fallback Observability

## Context

### Review chain

This is the fifth step in the A10 review/execution chain:

1. **A10** (Apr 5): original user question in `docs/project-status/fr-exploration/A10.md` line 88
2. **`a10-fsrs-fusion-formalization`** (Apr 7, archived, commit `d8484f5`): formalized the 5-signal fusion contract
3. **`a10-phase0-fix-question-generator-mastery-bug`** (Apr 7, archived, commit `ea6b170`): fixed the silent getattr bug in `_get_mastery_data`
4. **`a10-phase0-hardening`** (Apr 7, archived, commits `e946043` + `ed2bf8e`): added `mastery_degraded` cross-layer observability, 1x perf, kg_relevance canvasId binding, Semaphore(20)
5. **This change** `a10-phase0-fallback-observability`: closes the 3 residual gaps from ChatGPT Deep Research round 3

### Three gaps verified by 3 parallel Explore agents

**Gap 1: `FusionResult.is_fallback` spec/impl drift**

Agent 1 confirmed that `compute_fused_mastery` has 3 return statements, all three set `is_fallback=False`. Spec scenario "Zero signals active is fail-safe" requires the zero-signal branch to return `True`. The defensive `weight_sum <= 0` branch should also be `True` per fallback semantics. Only the normal-fusion happy path is correctly `False`.

No existing test in `test_mastery_fusion.py` asserts `is_fallback` — the drift is unprotected.

Only one downstream consumer exists: `mastery_engine.py:615` includes `fusion_result.is_fallback` in the `fusion_details` dict for API response. Because the implementation uniformly emits `False`, the field is useless as an observability signal.

**Gap 2: Cross-layer state loss through `effective_proficiency(concept)`**

Agent 2 traced the full call chain: `MasteryEngine.effective_proficiency(concept) -> float` has a fallback path (`fusion_result.active_signal_count == 0` → `min(p_mastery, R)`) but the return type is plain float, losing the fallback state. `question_generator._get_mastery_data` receives a float and cannot tell whether fusion actually ran.

Agent 2 scored cross-layer observability consistency at 2/5 (Poor).

**Gap 3: MCP `QueryMasteryOutput` schema inconsistency**

Agent 2 checked `backend/app/mcp/tools/mastery_tools.py:39-62`: the Pydantic model lacks `mastery_degraded`, breaking the cross-layer observability contract established by Phase 0 Hardening round 1.

### Test structure

Agent 3 read `test_mastery_fusion.py`: 19 tests across 3 classes. `FakeSignal` helper already exists. Two tests (`test_no_signals_registered` at L157, `test_all_signals_no_data` at L166) exercise the 0-signal case but assert only `fused_mastery` and `active_signal_count`. Zero `is_fallback` references in the whole file. Naming convention: snake_case, no parametrize, each scenario is its own method.

## Goals / Non-Goals

**Goals:**

1. Align `mastery_fusion.py` implementation with the existing `algo-fusion` spec at `:89` and `:100` (`is_fallback=True` in both fallback branches).
2. Add `MasteryEngine.effective_proficiency_with_fallback_info(concept) -> tuple[float, bool]` as a new public method surfacing the fusion fallback state to callers.
3. Refactor `effective_proficiency(concept) -> float` into a thin wrapper that calls the new method and discards the bool (backward compat).
4. Extend `question_generator._get_mastery_data` to use the new method and translate `fusion_fallback=True` into `mastery_degraded="fusion_fallback"`.
5. Add `mastery_degraded: Optional[str] = None` field to `QueryMasteryOutput` in `mastery_tools.py`.
6. Lock `is_fallback` semantic via 5 scenarios in `test_mastery_fusion.py` (update 2 existing, add 3 new).
7. Lock `fusion_fallback` propagation via 1 new scenario in `test_question_generator_mastery_data.py`.
8. Extend `algo-question` capability's "Mastery Data Degraded Observability" Requirement to include `"fusion_fallback"` as a fourth legal value.

**Non-Goals:**

- Modify `openspec/specs/algo-fusion/spec.md` — the spec already requires `is_fallback=True`; we align impl to spec, not the other way around.
- Touch `verification_service`, `recommendation_service`, `signal_registry`, frontend code, or `ConceptState`.
- Fix `mastery_engine.py:603-604` bare except on FSRS deserialization (Agent 2 P1 — Phase 1 scope).
- Fix `verification_service.py:1973-1994` `_extract_lapse_signal` silent BKT exception (Agent 2 P1 — Phase 1 scope).
- Implement any Phase 1+ architectural recommendations (ReviewPriorityEngine, advance_strategy, recommendation mastery factor, reliability weighting, ablation harness).
- Modify the original `A10.md` user question.

## Decisions

### Decision 1: New helper method, not a return-signature change

**Choice**: Add `MasteryEngine.effective_proficiency_with_fallback_info(concept) -> tuple[float, bool]` as a new public method. Refactor the existing `effective_proficiency(concept) -> float` to internally call the new method and discard the bool (backward compat wrapper).

**Rationale**:
- Changing `effective_proficiency` return signature to a tuple would break every existing caller.
- The new helper centralizes fallback detection in one place, so internal and external callers get the same answer.
- The naming (`_with_fallback_info`) makes the return shape self-documenting at call sites.

**Alternative rejected**: Use `@contextmanager` or thread-local variable for last-fallback state — would be thread-unsafe in async contexts.

### Decision 2: `fusion_fallback` value semantic excludes "not assessed"

**Choice**: The new helper returns `fusion_fallback=True` only when the `min(p_mastery, R)` fallback path was taken (no fusion engine attached, or `active_signal_count == 0`). It returns `False` when `interaction_count == 0` and the early-exit returns `base = 0.0`.

**Rationale**:
- A not-assessed concept correctly returning 0.0 is expected Story 5.1 behavior, not a degradation.
- Flagging it as a fallback would flood the observability pipeline with false signals for every new concept.
- The "truly not assessed" vs "fusion fell through" distinction is exactly the signal operators need.

**Alternative rejected**: Introduce a `"not_assessed"` value on `mastery_degraded` — would muddle the `None` semantic of the happy path.

### Decision 3: Include MCP schema fix in scope

**Choice**: Add `mastery_degraded: Optional[str] = None` to `QueryMasteryOutput` even though no existing MCP client requires it.

**Rationale**:
- Agent 2 flagged this as a cross-layer consistency gap.
- The fix is trivial (one line of Pydantic) and purely additive.
- Splitting it out would require a separate OpenSpec change.
- External Claude Code sessions can inspect the field in the future without a schema migration.

**Alternative rejected**: Separate `a10-mcp-mastery-degraded` change — unnecessary overhead.

### Decision 4: No `algo-fusion` spec modification

**Choice**: Leave `openspec/specs/algo-fusion/spec.md` untouched. Implementation catches up to the existing (correct) spec.

**Rationale**:
- The spec text already says `is_fallback=True` for the zero-signal scenario.
- Modifying the spec would mask the fact that the implementation was wrong for an extended period.
- Spec is the canonical reference; implementation should catch up to it.

**Alternative rejected**: Add a MODIFIED Requirement to `algo-fusion` — MODIFIED is for behavioral changes, not bug fixes that restore intended behavior.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| New helper could drift from `effective_proficiency` over time | Old method becomes a thin wrapper calling the new one and discarding the bool — divergence is structurally impossible |
| Callers of the old `effective_proficiency` might expect tuple return | Old signature unchanged; type checkers and tests expecting float continue to work |
| New `"fusion_fallback"` value could break enum-checking downstream code | Downstream uses `mastery_degraded` only for observability, not for branching. Additive value is safe |
| `is_fallback` was uniformly False before — some dashboard might rely on the uniform behavior | No existing code checks `is_fallback == True` (grep-verified). Field was purely observability. Fix enables a previously-dormant signal |
| 2 existing tests will fail if impl is fixed but tests not updated | Both tests are updated in the same commit so fix and lock happen together |
| MCP clients might not recognize the new field | Optional field with None default — Pydantic deserialization is permissive |
| `weight_sum <= 0` branch is technically unreachable (all weights ≥ 0 by spec) | We still fix it for defense-in-depth; one-liner that cannot regress |

## Open Questions

None. This change is scoped to the 3 gaps identified by ChatGPT review round 3. ChatGPT's other questions about group_id semantics, concept_id mapping, CI integration, and Neo4j schema commitments are not blockers for this change and remain open for Phase 1+ product decisions.

## Cross-Links

- `docs/project-status/fr-exploration/A10.md`
- `docs/project-status/fr-exploration/A10-resolution-summary.md` (will gain Section 14)
- `openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/`
- `openspec/changes/archive/2026-04-07-a10-phase0-fix-question-generator-mastery-bug/`
- `openspec/changes/archive/2026-04-07-a10-phase0-hardening/`
- `openspec/specs/algo-fusion/spec.md`
- `backend/app/services/mastery_fusion.py:83-121`
- `backend/app/services/mastery_engine.py:332-371`
- `backend/app/services/question_generator.py:673-711`
- `backend/app/mcp/tools/mastery_tools.py:39-62`
- `backend/tests/unit/test_mastery_fusion.py:156-175`
- `backend/tests/unit/test_question_generator_mastery_data.py`
