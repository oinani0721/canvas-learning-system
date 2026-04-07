## Why

A10 Phase 0 Hardening #1 (commit `e946043`) fixed `_get_kg_relevance` to bind both `id` and `canvasId` on the primary node `n` in its Cypher MATCH clause, closing a silent cross-canvas collision risk. The fix is in code, a static grep test guards it, and the existing `algo-question` spec already has a "Primary node is bound to canvasId" scenario describing the shape of the query.

What the spec does **not** currently say is that this dual binding is a **long-term architectural commitment** rather than a waypoint. Without an explicit "long-term commitment" clause, a future refactor could legitimately read the existing scenario as "the fix for a specific bug in Phase 0" and decide to "simplify" back to `{id: $node_id}` when `canvas_id` starts feeling like dead weight — the regression guard would still trip, but nobody would know whether the trip is a real violation or a planned change. The spec would not provide any grounds to push back.

User decision 2026-04-07 (A10 Phase 1 plan session 3, Q5) made the commitment explicit: "node_id dual binding `{id, canvasId}` is the permanent rule." This change anchors that user decision into the `algo-question` spec so that future "simplifications" must either respect the commitment or introduce a new MODIFIED Requirement that supersedes it. That is, future changes must be deliberate and reviewed, not drive-by.

This is pure spec hardening with zero code changes. The code already matches what the updated spec will require.

## What Changes

- **MODIFIED Capability** `algo-question`: Extend the existing "kg_relevance Schema Correctness" Requirement to state the dual binding is a long-term commitment and to add two new scenarios that lock the commitment.
- **New scenario** "Dual binding is a long-term architectural commitment, not a migration waypoint": states that removing either `id` or `canvasId` from the primary-node MATCH properties constitutes a breaking spec change and SHALL require a new MODIFIED Requirement that explicitly supersedes this one.
- **New scenario** "Future migration to global node_id namespace requires explicit spec change": captures the valid escape hatch — if the product ever decides node_id IS globally unique, the simplification is allowed, but ONLY after a new OpenSpec change carrying a MODIFIED Requirement is merged.
- The existing 4 scenarios (`kg_relevance finds nodes`, `does not silently return default`, `production data is not uuid-based`, `primary node is bound to canvasId`, `cypher syntax check`) are preserved verbatim — MODIFIED Requirements require full re-statement.

## Capabilities

### Modified Capabilities

- `algo-question`: Extend "kg_relevance Schema Correctness" Requirement with long-term-commitment semantics and 2 new scenarios. No other requirements in the capability are touched.

## Impact

- **Spec**: `openspec/specs/algo-question/spec.md` — will gain ~20 lines of new scenario text when this change is archived. No requirement removed, no scenario removed.
- **Code**: Zero changes. The existing implementation at `backend/app/services/question_generator.py:_get_kg_relevance` already binds both `id` and `canvasId`.
- **Tests**: Zero changes. The existing static grep regression test at `backend/tests/test_kg_relevance_schema.py` (or equivalent; verify during Step 1 of tasks) already enforces the Cypher shape.
- **Observability**: None.
- **Rollback**: Trivial — revert the archive commit. No code depends on the new scenarios being present.
- **Risk**: Minimal. The only way this change can go wrong is if the MODIFIED Requirement block fails to re-state all 5 original scenarios exactly; `openspec validate --strict` catches that class of error.
