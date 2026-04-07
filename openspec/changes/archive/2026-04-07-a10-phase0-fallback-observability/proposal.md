# Proposal: A10 Phase 0 Fallback Observability

## Why

This change closes a narrow but high-signal gap discovered during ChatGPT Deep Research round-3 adversarial review of A10 (`docs/project-status/fr-exploration/A10.md`). The predecessor changes restored the mastery-data flow (Phase 0 `a10-phase0-fix-question-generator-mastery-bug`, commit `ea6b170`) and added cross-layer observability for the `_get_mastery_data` happy path / not-found / exception paths (Phase 0 Hardening `a10-phase0-hardening`, commit `e946043`). Review round 3 identified three residual risks in the **fusion fallback** path specifically:

1. **Spec/implementation drift on `FusionResult.is_fallback`**: `openspec/specs/algo-fusion/spec.md` scenario "Zero signals active is fail-safe" explicitly requires `is_fallback=True` when `compute_fused_mastery` returns the fallback `FusionResult` with `active_signal_count == 0`. The actual implementation at `backend/app/services/mastery_fusion.py:89` sets `is_fallback=False` on that branch, and `:100` sets the same on the defensive `weight_sum <= 0` branch. Only the normal-fusion return at `:120` is correctly `False`. Source-level verification via an Explore agent confirmed the spec drift at all three return sites, and a grep confirmed `test_mastery_fusion.py` has **zero** assertions of `is_fallback` — so the drift is currently unprotected by tests.

2. **Lost fallback state through `MasteryEngine.effective_proficiency(concept)`**: The method at `backend/app/services/mastery_engine.py:332-371` reads `fusion_result.active_signal_count > 0` to decide whether to use the fused value or fall back to `min(p_mastery, R)`. The function returns a plain `float`, **losing the `is_fallback` information**. Downstream consumers (`question_generator._get_mastery_data`, MCP tools, ACP assembly) receive `0.0` or some degraded value without any indication of whether the fusion was actually consumed. The Phase 0 Hardening `mastery_degraded` field on `ACPData` / `NodePriority` already distinguishes `concept_not_found` / `exception` / `None` — but does not distinguish "fusion actually produced a value" from "fusion fell through to min(p_mastery, R)".

3. **MCP layer missing `mastery_degraded` field**: `backend/app/mcp/tools/mastery_tools.py:QueryMasteryOutput` schema lacks a `mastery_degraded` field, breaking the cross-layer observability contract established by Phase 0 Hardening. External Claude Code sessions using the MCP tool cannot observe whether the returned mastery values came from fusion or a fallback path.

None of these are breaking runtime bugs — the returned values are still numerically valid. But **they are exactly the kind of silent-degradation gaps that the predecessor changes were designed to eliminate**. Leaving them creates the same "looks like Phase 0 worked, might be silently degraded" ambiguity that Phase 0 Hardening Round 1 was meant to close.

Out of scope for this change: ChatGPT's Phase 1+ architectural recommendations (ReviewPriorityEngine, advance_strategy, recommendation mastery factor, reliability weighting, ablation harness). Those require either product decisions (group_id semantics) or data exports (ablation baselines) that this session does not have.

## What Changes

- **FIXED** `backend/app/services/mastery_fusion.py:89` and `:100` — both fallback `FusionResult` constructions now set `is_fallback=True` (matching the spec). The happy-path return at `:120` stays `False`.
- **NEW** public method `MasteryEngine.effective_proficiency_with_fallback_info(concept) -> tuple[float, bool]` at `backend/app/services/mastery_engine.py`. The existing `effective_proficiency(concept) -> float` becomes a thin wrapper that discards the bool (backward compat). Callers that need the fallback info (most notably `_get_mastery_data`) use the new method. The bool is `True` when the `min(p_mastery, R)` fallback path was used (either because no fusion engine is attached, or because fusion returned `active_signal_count == 0`). It is `False` when fusion was actually used OR when the concept is not assessed (`interaction_count == 0` → base = 0.0 is the correct "not assessed" output, not a degradation).
- **MODIFIED** `backend/app/services/question_generator.py:_get_mastery_data`: call the new helper; when `fusion_fallback` is `True` on the happy path (concept exists but fusion fell through), set `mastery_degraded = "fusion_fallback"` in the returned dict. The existing `"concept_not_found"` and `"exception"` values are unchanged.
- **MODIFIED** `backend/app/mcp/tools/mastery_tools.py:QueryMasteryOutput`: add `mastery_degraded: Optional[str] = None` field, mirroring the cross-layer pattern.
- **EXTENDED** `backend/tests/unit/test_mastery_fusion.py`: update 2 existing tests (`test_no_signals_registered`, `test_all_signals_no_data`) to assert `is_fallback=True`; add 3 new scenarios (`test_single_signal_active_is_fallback_false`, `test_five_signals_active_is_fallback_false`, `test_weight_sum_zero_is_fallback_true`).
- **EXTENDED** `backend/tests/unit/test_question_generator_mastery_data.py`: add 1 new scenario `test_fusion_fallback_propagates_to_mastery_degraded` verifying the new "fusion_fallback" value reaches the returned dict.
- **MODIFIED** `openspec/specs/algo-question/spec.md` `Mastery Data Degraded Observability` Requirement: add `"fusion_fallback"` as a fourth legal value alongside `None`, `"concept_not_found"`, `"exception"`.
- **NO CHANGES** to: `openspec/specs/algo-fusion/spec.md` (the scenario text already requires `is_fallback=True` — we are aligning implementation to the existing contract, not modifying the contract), `ConceptState`, `verification_service`, `recommendation_service`, `signal_registry`, frontend code.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities

- `algo-question`: extend the existing "Mastery Data Degraded Observability" Requirement to recognize `"fusion_fallback"` as a legal observable degradation value. No existing Requirement is removed or semantically reversed.

## Impact

- **Production observability**: Any concept whose fusion computation falls through to the `min(p_mastery, R)` path is now visibly marked as `mastery_degraded="fusion_fallback"` in API responses, MCP tool outputs, and the exam priority log stream. Operators can distinguish "fusion is working but this concept has no fusion data" from "fusion is working and produced a confident result".
- **Test coverage**: `is_fallback` becomes the first field on `FusionResult` with positive assertions in `test_mastery_fusion.py` (previously zero assertions). The 5 new/updated scenarios lock down the semantic for all 3 return sites in `compute_fused_mastery`.
- **Backward compatibility**: `effective_proficiency(concept) -> float` signature is unchanged. New helper is purely additive. `QueryMasteryOutput.mastery_degraded` is `Optional[str] = None` — existing MCP clients that do not inspect it are unaffected.
- **Rollback**: `git revert <commit>` cleanly restores the prior behavior. No migration is needed.
- **Out of scope (P1, documented for future)**: `mastery_engine.py:603-604` bare `except: pass` on FSRS card deserialization (Phase 1), `verification_service.py:1973-1994` `_extract_lapse_signal()` silent BKT exception (Phase 1), ChatGPT's ReviewPriorityEngine / advance_strategy / recommendation mastery factor / reliability weighting / ablation harness (Phase 1+).
