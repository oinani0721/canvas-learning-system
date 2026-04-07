# Proposal: A10 Phase 0 Hardening — Observability, Performance, and Schema Correctness

## Why

This change closes three residual risks in the A10 Phase 0 fix (`ea6b170`, `a10-phase0-fix-question-generator-mastery-bug`) that were identified by a second round of ChatGPT Deep Research adversarial review. The core finding: **Phase 0 restored the mastery-data path in theory, but left it unobservable, inefficient, and vulnerable to schema drift**. Each of the three risks is quantifiable:

1. **Observability gap — Phase 0 can silently fail in production**. `question_generator._get_mastery_data` now correctly routes through `MasteryEngine`, but when `mastery_store.get_concept(node_id)` returns None (e.g., because `CanvasNode.id` does not match any `EntityNode.mastery_concept_id` — a contract established asynchronously by `event_handlers.py:31` on score events), the function silently falls back to a hard-coded default dict. The fallback result (`effective_proficiency=0.0 / mastery_label="Not Assessed"`) is indistinguishable from the pre-fix bug's output. Without a `mastery_degraded` field, production has no way to detect whether Phase 0 actually took effect on a given node or whether the fix is being bypassed by an ID mapping gap.

2. **Performance gap — 3× redundant `effective_proficiency` calls per node**. Source-level analysis of the post-Phase-0 `_get_mastery_data` reveals that `effective_proficiency(concept)` is invoked three times per node: once directly, once internally via `mastery_level(concept)` at `mastery_engine.py:419`, and a third time via `mastery_label(concept) → mastery_level(concept)` at `mastery_engine.py:450`. Each call invokes `compute_fused_mastery` (which iterates 5 signals and may preload caches), so for a batch of N nodes in `select_target_node`, the total cost is N × 3 fusion computations instead of N × 1.

3. **Schema drift risk — `_get_kg_relevance` does not bind `canvasId` on the primary node**. The current Cypher at `question_generator.py:755` reads `MATCH (n:CanvasNode {id: $node_id})-[r:...]-(neighbor:CanvasNode) WHERE neighbor.canvasId = $canvas_id`. It constrains `neighbor.canvasId` but leaves the primary `n` node bound only by `id`. This works today because `CanvasNode.id` is globally unique across canvases, but it violates the spirit of the existing `algo-question/spec.md` "kg_relevance Schema Correctness" Requirement (which requires `id` + `canvasId` as the canonical addressing pattern), and it would produce cross-canvas contamination the moment the project allows non-globally-unique node IDs (e.g., when per-canvas sandboxes are introduced).

4. **Concurrency tail-risk — `select_target_node` has no batch concurrency cap**. The nested `asyncio.gather` at `question_generator.py:166-175` issues 2*N concurrent Neo4j queries (N mastery + N kg_relevance) per batch. On a 500-node canvas, that is 1000+ simultaneous queries against a Neo4j pool sized for ~50. The project already has a proven pattern for this: `canvas_service.py:599` wraps each coroutine in `async with asyncio.Semaphore(12)`. Adopting the same pattern here is a low-risk forward-looking hardening.

All four fixes converge on the same surface (`question_generator.py`, its tests, and the `algo-question` capability spec) and are tightly coupled in review. They fit in a single change.

Source origin: `docs/project-status/fr-exploration/A10.md` (original user question frozen Apr 5) → `a10-fsrs-fusion-formalization` (Phase 1 formalization, archived Apr 7) → `a10-phase0-fix-question-generator-mastery-bug` (Phase 0 silent-bug fix, archived Apr 7) → this change (Phase 0 Hardening, driven by the second ChatGPT review).

## What Changes

- **NEW** `MasteryEngine.mastery_level_from_proficiency(eff, concept) -> int` public helper at `backend/app/services/mastery_engine.py`: replicates `mastery_level` logic but accepts a pre-computed `effective_proficiency` value instead of recomputing internally. Also add `mastery_label_from_level(level) -> str` for symmetry.
- **MODIFIED** `backend/app/services/question_generator.py:_get_mastery_data` (lines 673-711): compute `effective_proficiency(concept)` exactly once per call, pass the cached value into `mastery_level_from_proficiency` and `mastery_label_from_level`. Return a dict that always contains a `mastery_degraded: Optional[str]` key (`None` on the happy path; `"concept_not_found"` when `store.get_concept` returns None; `"exception"` when the try/except catches an error).
- **MODIFIED** `backend/app/services/question_generator.py:assemble_acp` (lines 264-271): pass `mastery.get("mastery_degraded")` through to `acp.mastery_degraded`.
- **MODIFIED** `backend/app/models/exam_models.py:ACPData`: add `mastery_degraded: Optional[str] = None` field.
- **MODIFIED** `backend/app/models/exam_models.py:NodePriority`: add `mastery_degraded: Optional[str] = None` field (mirror of existing `kg_relevance_degraded`).
- **MODIFIED** `backend/app/services/question_generator.py:select_target_node` (lines 142-175): propagate `mastery_degraded` from each batch result into the `NodePriority` objects; wrap the per-node `_get_mastery_data` and `_get_kg_relevance` calls in an `asyncio.Semaphore(20)` using the pattern from `canvas_service.py:598-616`.
- **MODIFIED** `backend/app/services/question_generator.py:_get_kg_relevance` (line 755): tighten the Cypher MATCH to `MATCH (n:CanvasNode {id: $node_id, canvasId: $canvas_id})-[r:CANVAS_EDGE|RELATES_TO]-(neighbor:CanvasNode)` (both primary and neighbor bound to `canvasId`).
- **NEW** spec requirements under `algo-question`:
  - "Mastery Data Degraded Observability" — codifies the `mastery_degraded` contract
  - "Effective Proficiency Computed Once Per Mastery Query" — codifies the 1x calculation performance contract
  - "Bounded Concurrency for Batch Node Scoring" — codifies the Semaphore-wrapped batch gather
- **MODIFIED** spec requirement under `algo-question`: extend "kg_relevance Schema Correctness" with a new scenario asserting the primary node MATCH binds both `id` and `canvasId`.
- **NEW/EXTENDED** `backend/tests/unit/test_question_generator_mastery_data.py`: add scenarios for `effective_proficiency` called exactly once, `concept_not_found` degraded flag, `exception` degraded flag.
- **NEW** `backend/tests/e2e/test_a11_kg_relevance_e2e.py`: add scenarios for cross-canvas node_id isolation + Semaphore concurrency bound.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities

- `algo-question`: 3 new requirements (observability, perf 1x, bounded concurrency) + 1 extended requirement (kg_relevance schema tightening). No existing Requirement content is removed or semantically reversed — this is purely additive hardening.

## Impact

- **Production observability**: Structured log or metrics pipeline gains a `mastery_degraded` dimension that distinguishes "node is truly not assessed" from "ID mapping missing" from "concept lookup crashed". This is the prerequisite for detecting the kind of silent failure Phase 0 fixed — without it, any regression would recur invisibly.
- **Production performance**: `select_target_node` on a 50-node canvas drops from ~150 `effective_proficiency` calls to ~50 (3x reduction). On a 500-node canvas, from ~1500 calls to ~500. Signal preload caches also see 3x fewer hits.
- **Production concurrency**: Batch Neo4j queries capped at 20 simultaneous regardless of canvas size. Existing `return_exceptions=True` per-node degradation logic is preserved — this change only bounds throughput.
- **Future-proofing**: The `_get_kg_relevance` Cypher tightening immunizes the system against a future product decision to allow per-canvas `node_id` namespaces. No cross-canvas contamination path remains.
- **Test coverage**: 5 new regression scenarios plus the existing 8 tests from Phase 0 plus the 11 A11 e2e tests. Total A10 guard surface: 19+ tests.
- **Rollback**: `git revert <commit>` cleanly restores the prior behavior. The new helpers are purely additive, and the new `mastery_degraded` field is `Optional[str] = None` so existing callers that do not set it are unaffected.
- **No changes** to: `ConceptState` dataclass (design is correct), `mastery_fusion.py`, `signal_registry.py`, `verification_service.py`, `recommendation_service.py`, frontend code, or the original `A10.md` user question.
