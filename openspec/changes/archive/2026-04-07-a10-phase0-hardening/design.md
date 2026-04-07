# Design: A10 Phase 0 Hardening

## Context

### Review chain origin

This change is the direct outcome of a four-step review/execution chain:

1. **A10** (Apr 5): `docs/project-status/fr-exploration/A10.md` line 88 — user asked 「FSRS 的算法是如何和其他的算法进行融合的，没有理清楚」
2. **a10-fsrs-fusion-formalization** (Apr 7, archived): formalized 5-signal fusion contract as the first `algo-fusion` requirements
3. **ChatGPT Deep Research review round 1** (Apr 7): corrected the "zero call sites" claim, pointed out that `mastery_engine.effective_proficiency` already consumes `compute_fused_mastery`. Led to deeper exploration revealing a silent bug in `question_generator._get_mastery_data`
4. **a10-phase0-fix-question-generator-mastery-bug** (Apr 7, commit `ea6b170`, archived): fixed the silent bug by routing volatile mastery field reads through `MasteryEngine` instead of `getattr` on `ConceptState`
5. **ChatGPT Deep Research review round 2** (Apr 7): adversarially reviewed the Phase 0 fix itself. Confirmed the fix is correct but identified **3 residual risks** that this hardening change addresses.

The three residual risks, with source-level evidence gathered via 3 parallel Explore agents before this change was written:

### Risk 1: Phase 0 can silently fail in production (ID mapping contract unverified)

`mastery_store.get_concept(node_id)` queries `EntityNode.mastery_concept_id` with a name-match fallback. The contract that `CanvasNode.id` should equal `EntityNode.mastery_concept_id` is established asynchronously at `event_handlers.py:31` on score events (`get_or_create_concept(concept_id=node_id, name=node_id)`). If that event has not fired for a given canvas node yet, `get_concept` returns `None` and the Phase 0 fix silently lands on a fallback dict with `effective_proficiency=0.0`. From the consumer's perspective (difficulty selector, Gemini prompt), this is **indistinguishable** from the pre-fix bug.

No production logging distinguishes these two states. The only existing log on the fallback path is `logger.debug(...)`, which is not visible at production log levels.

### Risk 2: 3× redundant `effective_proficiency` calls per node

Source reading of `mastery_engine.py` reveals the call graph:

- `_get_mastery_data` line 699: `engine.effective_proficiency(concept)` — **1st call**
- `_get_mastery_data` line 700: `engine.mastery_level(concept)` → line 419: `eff = self.effective_proficiency(concept)` — **2nd call**
- `_get_mastery_data` line 701: `engine.mastery_label(concept)` → line 450: `self.mastery_level(concept)` → line 419: `self.effective_proficiency(concept)` — **3rd call**

Each `effective_proficiency` call internally invokes `_preload_signal_caches(concept)` and `_fusion_engine.compute_fused_mastery(concept.concept_id)`. For an N-node batch in `select_target_node`, this is 3N full fusion computations instead of N.

There is no memoization in the call path. `signal_registry.py` has per-signal value caches but they are populated per concept, not per `effective_proficiency` invocation.

### Risk 3: `_get_kg_relevance` primary node not bound to canvasId

The Cypher at `question_generator.py:755`:

```cypher
MATCH (n:CanvasNode {id: $node_id})-[r:CANVAS_EDGE|RELATES_TO]-(neighbor:CanvasNode)
WHERE neighbor.canvasId = $canvas_id
```

constrains `neighbor.canvasId` but binds the primary `n` only by `id`. This works today because `CanvasNode.id` is globally unique, but the existing `algo-question/spec.md` "kg_relevance Schema Correctness" Requirement states the query "SHALL use Neo4j property names that match the SyncService write schema (`id` as primary key, `canvasId` as canvas reference)" — which is reasonable to read as requiring both properties on the primary node.

If per-canvas ID namespaces are ever introduced (a common request when users duplicate canvases), this Cypher produces cross-canvas contamination with no deprecation signal.

### Risk 4: `select_target_node` batch has no concurrency cap

Lines 166-175 issue a nested `asyncio.gather`:

```python
mastery_results, kg_results = await asyncio.gather(
    asyncio.gather(*(self._get_mastery_data(nid) for nid in node_ids), return_exceptions=True),
    asyncio.gather(*(self._get_kg_relevance(nid, source_canvas_id) for nid in node_ids), return_exceptions=True),
)
```

For an N-node canvas this starts 2N coroutines against a Neo4j connection pool sized for ~50. The project's established pattern for this problem is at `canvas_service.py:598-616`:

```python
semaphore = asyncio.Semaphore(12)
async def sync_single_edge(edge):
    async with semaphore:
        return await self._sync_edge_to_neo4j(...)
results = await asyncio.gather(*(sync_single_edge(e) for e in edges))
```

Adopting the same pattern in `select_target_node` with a limit of 20 (modestly higher than 12 because the queries are lighter and the primary and neighbor nodes are already indexed) is a proven hardening.

## Goals / Non-Goals

**Goals:**

1. Make Phase 0's production effectiveness **observable** by adding a `mastery_degraded: Optional[str]` flag that distinguishes happy path, concept-not-found fallback, and exception fallback.
2. Reduce the per-node `effective_proficiency` cost from 3× to 1× by adding pre-computed helpers (`mastery_level_from_proficiency`, `mastery_label_from_level`) to `MasteryEngine` and refactoring `_get_mastery_data` to use them.
3. Tighten the `_get_kg_relevance` Cypher to bind both `id` and `canvasId` on the primary node, eliminating a forward-looking schema drift risk.
4. Bound the `select_target_node` batch Neo4j concurrency at 20 via `asyncio.Semaphore`, mirroring the `canvas_service.py:598-616` pattern.
5. Add a new spec requirement for each of the above in `algo-question` capability so regressions cannot be silently reintroduced.
6. Extend the existing unit and e2e test suites to cover all four hardenings.

**Non-Goals:**

- ❌ Modify `ConceptState` dataclass (volatile-fields design is correct)
- ❌ Modify `event_handlers.py` or the concept creation contract (that is a separate potential fix, out of Phase 0 scope)
- ❌ Modify `mastery_fusion.py`, `signal_registry.py`, `mastery_engine.py` core fusion logic (only add helpers)
- ❌ Touch `verification_service.py`, `recommendation_service.py` (Phase 1+ scope)
- ❌ Implement the 5 ChatGPT-recommended Phase 1+ cases (ReviewPriorityEngine, advance_strategy, etc.)
- ❌ Modify the original `A10.md` user question
- ❌ Change the 4 `algo-fusion` Requirements established by `a10-fsrs-fusion-formalization`

## Decisions

### Decision 1: Public helper naming — `mastery_level_from_proficiency` / `mastery_label_from_level`

**Choice**: Add two new public methods to `MasteryEngine`: `mastery_level_from_proficiency(eff: float, concept: ConceptState) -> int` and `mastery_label_from_level(level: int) -> str`. They complement the existing `mastery_level(concept)` and `mastery_label(concept)` without replacing them. The existing methods are left intact (they still do the internal `effective_proficiency` computation for callers that don't have a pre-computed value).

**Rationale**:
- Public API is consistent with DD-13 (name-behavior consistency): the method name clearly indicates it accepts a pre-computed proficiency as input, not that it computes one internally.
- Not marked private (`_`) because callers in `question_generator.py` are outside the class — a private helper would violate DD-13 in spirit.
- The symmetrical `mastery_label_from_level(level)` is a simple wrapper around the existing `MASTERY_LABELS` lookup but keeps all mastery-related string mapping in the `MasteryEngine` module.

**Alternative considered**: Add memoization to `effective_proficiency` via `@functools.lru_cache`. **Rejected** because `concept` is a mutable dataclass — caching by `concept_id` would produce stale results after `update_on_interaction` mutations within the same request.

### Decision 2: `mastery_degraded` as a dict key, propagated to both ACPData and NodePriority

**Choice**: `_get_mastery_data` returns a dict that always contains `"mastery_degraded": None | "concept_not_found" | "exception"`. `assemble_acp` passes this through to `ACPData.mastery_degraded` (new field). `select_target_node` passes it through to `NodePriority.mastery_degraded` (new field).

**Rationale**:
- The dict-key approach mirrors the existing `kg_relevance_degraded` pattern on `NodePriority` (documented at `exam_models.py:241-260`), which has proven itself during A11 review.
- Propagating to both ACPData and NodePriority ensures observability covers both the assemble_acp prompt path and the batch select_target_node scoring path.
- Using `Optional[str]` with `None` default preserves backward compatibility for every existing caller.

**Alternative considered**: Change `_get_mastery_data` return signature to `tuple[dict, Optional[str]]` like `_get_kg_relevance`. **Rejected** because there are many callers of `_get_mastery_data` (including `target_node_id` branch at line 127) and tuple-unpacking churn would blur this change's intent.

### Decision 3: Semaphore wrapping pattern — mirror canvas_service.py exactly

**Choice**: In `select_target_node`, create a function-local `asyncio.Semaphore(20)`, define inner `async def gated_mastery(nid)` / `async def gated_kg(nid)` wrappers that use `async with semaphore:`, then pass those to `asyncio.gather`. Do not reuse the outer gather's lambda — wrap each coroutine explicitly.

**Rationale**:
- Matches `canvas_service.py:598-616` line-for-line (already code-reviewed and in production).
- Function-local semaphore prevents cross-request sharing (a process-wide semaphore could starve one request if another is processing a large canvas).
- Limit 20 is chosen because: (a) Neo4j default connection pool is 50; (b) `canvas_service` uses 12 for write-heavy edge sync; kg_relevance is read-only and lighter; (c) 20 provides headroom for other concurrent services without saturating the pool.

**Alternative considered**: Global `asyncio.Semaphore(20)` at module scope. **Rejected** because concurrent `select_target_node` calls (e.g., from different users) would contend unnecessarily.

### Decision 4: Cypher MATCH tightening is backward compatible

**Choice**: Change `MATCH (n:CanvasNode {id: $node_id})-[r:...]-(neighbor:CanvasNode)` to `MATCH (n:CanvasNode {id: $node_id, canvasId: $canvas_id})-[r:...]-(neighbor:CanvasNode)`. The `$canvas_id` parameter is already passed to the query — this is a pure constraint addition on an existing parameter.

**Rationale**:
- All existing A11 test data is seeded with `canvasId` explicitly (`test_a11_kg_relevance_e2e.py:120-144`), so no test data migration is needed.
- Existing `neighbor.canvasId = $canvas_id` WHERE clause is kept (belt and suspenders — the WHERE filters any neighbor that might somehow lack the property).
- The existing `algo-question/spec.md` "kg_relevance Schema Correctness" Requirement already implies this tightening; the spec MODIFIED delta just makes it explicit.

**Alternative considered**: Only add the constraint to the test assertions without changing production Cypher. **Rejected** because the point is to prevent future drift, not just to test-cover the current state.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Semaphore(20) may still be too high/low for specific Neo4j deployments | The limit is a single constant; tuning requires a 1-line change and a re-deploy. Future work may promote it to a config field |
| New `mastery_degraded` field could confuse prompt rendering if the LLM sees it | The field is consumed only by the select_target_node observability path and is not added to any Gemini prompt template. Layer3.md prompt rendering is unchanged |
| `mastery_level_from_proficiency` logic could drift from `mastery_level` | A unit test asserts equivalence: for any (eff, concept) pair, `mastery_level_from_proficiency(eff, concept)` == `mastery_level(concept)` when `effective_proficiency(concept)` returns `eff` |
| Cypher tightening could break in edge cases where `n.canvasId` is absent (legacy data) | The post-sync schema has `canvasId` on every CanvasNode (confirmed via `_seed_canvas` in A11 tests). A new scenario explicitly tests cross-canvas isolation |
| 4 hardenings in one change could complicate review | All 4 share the same file (`question_generator.py`) and the same capability (`algo-question`). The design.md groups them logically. Git diff is dominated by the spec delta + test additions |
| Future engineers may miss that `mastery_level(concept)` still does 3x internal calls for OTHER callers | The spec Requirement is scoped to `_get_mastery_data` specifically. `mastery_level(concept)` remains the convenience API for callers that don't have a pre-computed value. Docstrings updated accordingly |
| `mastery_label_from_level` is trivially simple — borderline over-engineered | It's 2 lines but keeps the call pattern symmetric and maintains "all mastery label logic lives in MasteryEngine". The cost is negligible |
| e2e test for 500-node Semaphore limit requires real Neo4j + seeding | Use a synthetic test that instruments the semaphore directly (count current holders) rather than actually seeding 500 nodes. This keeps test runtime under 1 second |

## Open Questions

(none — this change is scoped to the four specific residual risks identified by ChatGPT review round 2. All other open questions from `a10-fsrs-fusion-formalization/design.md` remain open for Phase 1+ work.)

## Cross-Links

- `docs/project-status/fr-exploration/A10.md` — original user question (read-only)
- `docs/project-status/fr-exploration/A10-resolution-summary.md` — ChatGPT review entry doc (will be extended with a Section 13 "Phase 0 Hardening" note as part of this change)
- `openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/` — Phase 1 formalization
- `openspec/changes/archive/2026-04-07-a10-phase0-fix-question-generator-mastery-bug/` — Phase 0 silent-bug fix (direct predecessor)
- `backend/app/services/question_generator.py:110-175` — `select_target_node` batch path (target of Semaphore and mastery_degraded propagation)
- `backend/app/services/question_generator.py:673-711` — `_get_mastery_data` (target of 1x eff caching and mastery_degraded dict key)
- `backend/app/services/question_generator.py:740-769` — `_get_kg_relevance` (target of Cypher tightening)
- `backend/app/services/mastery_engine.py:404-454` — `mastery_level` / `mastery_label` (adjacent to new helpers)
- `backend/app/services/canvas_service.py:598-616` — reference pattern for Semaphore wrapping
- `backend/app/models/exam_models.py:203-260` — `ACPData` and `NodePriority` (targets of `mastery_degraded` field additions)
- `backend/tests/unit/test_question_generator_mastery_data.py` — extended with new scenarios
- `backend/tests/e2e/test_a11_kg_relevance_e2e.py` — extended with cross-canvas + Semaphore scenarios
