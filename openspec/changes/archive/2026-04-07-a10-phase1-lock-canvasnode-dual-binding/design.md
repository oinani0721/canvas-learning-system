## Context

### What exists today

`_get_kg_relevance(node_id, canvas_id)` in `backend/app/services/question_generator.py` computes a weighted-degree relevance score for a Canvas node's neighborhood in the knowledge graph. A10 Phase 0 Hardening #1 (commit `e946043`) updated its Cypher MATCH clause to bind **both** `id` and `canvasId` as map properties on the primary node `n`:

```cypher
MATCH (n:CanvasNode {id: $node_id, canvasId: $canvas_id})-[r:CANVAS_EDGE|RELATES_TO]-(m:CanvasNode)
RETURN r.type, count(r) as cnt
```

The corresponding spec addition (archived with `fix-fr-kg-04-schema-drift-and-sync-hardening`) added the **"Primary node is bound to canvasId"** scenario to the "kg_relevance Schema Correctness" Requirement. That scenario describes the shape of the Cypher but frames it as "a hypothetical future where node IDs are per-canvas rather than global" — i.e. the scenario protects against a speculative future, not an acknowledged permanent rule.

### What the user decided (2026-04-07 Q5)

The plan session presented the user with the question: "Should `{id, canvasId}` dual binding be the permanent rule, or is it a temporary safeguard until we decide whether node_id is globally unique?"

The user answered: **permanent rule.** The rationale (as recorded in the plan document):

1. Canvas is the product's unit of isolation — users think in canvases, and cross-canvas data sharing is a deliberate act (export, import, linking), not an ambient property.
2. Global node_id namespace adds accidental coupling between canvases and makes "rename / split canvas" operations dangerous.
3. Keeping the dual binding costs nothing (one extra map property in MATCH); removing it risks silent cross-canvas collisions that only manifest under specific data patterns.

### What this change does

Extend the existing "kg_relevance Schema Correctness" Requirement to make the long-term commitment explicit **at the spec level**. Two new scenarios lock the commitment:

1. **"Dual binding is a long-term architectural commitment, not a migration waypoint"** — states that removing `id` or `canvasId` from the map properties is a breaking spec change requiring a new MODIFIED Requirement.
2. **"Future migration to global node_id namespace requires explicit spec change"** — describes the valid escape hatch: product can decide to globalize node_id, but only via a new OpenSpec change.

Together these scenarios shift the protection from "regression guard in one test file" to "spec-level social contract." A future developer who wants to "simplify" the MATCH clause must now write a new OpenSpec change and argue for the shift in `design.md`, rather than just deleting the extra property and watching one test fail.

## Goals

- Make the dual binding commitment **discoverable** at the spec level (grep-friendly, permanent record).
- Prevent **silent regressions** by requiring explicit spec change for simplification.
- Preserve the **valid escape hatch** — this is not "never change, ever," it is "change through the proper channel."
- **Zero code risk** — no production code is modified.

## Non-Goals

- Not introducing any new runtime behavior.
- Not modifying the weighted-degree formula, the degraded-reason observability, or any other aspect of `_get_kg_relevance`.
- Not touching `exam_service_ext`, `SyncService`, `canvas_service`, or any other file that writes or reads `CanvasNode`.
- Not creating a new capability — this is strictly a MODIFIED Requirement inside the existing `algo-question` capability.
- Not pre-committing to what the "new MODIFIED Requirement" would look like IF the product one day decides to globalize node_id. That is a future change's problem.

## Key Decisions

### Decision 1: MODIFIED Requirement, not new Requirement

**Options considered:**

- **(A) ADD a new Requirement** called "kg_relevance Dual Binding Commitment" alongside the existing "kg_relevance Schema Correctness" Requirement.
- **(B) MODIFY the existing** "kg_relevance Schema Correctness" Requirement to extend its description and add 2 scenarios.

**Decision: (B) MODIFY.**

**Rationale:**

- The dual binding is already part of the existing Requirement's body text: `"Additionally, the primary node n in the MATCH clause SHALL bind both id and canvasId as map properties..."` Splitting it across two Requirements would leave the existing Requirement describing half the rule and the new Requirement describing the other half, which is strictly worse for readability.
- OpenSpec MODIFIED Requirements produce an archive delta that cleanly merges back into the main spec without creating orphaned requirement slots.
- The existing scenario "Primary node is bound to canvasId" already concerns dual binding; grouping the new scenarios next to it preserves proximity and readability.

**Trade-off accepted:** MODIFIED Requirements require full re-statement of all scenarios in the delta file. That is 5 existing scenarios + 2 new = 7 scenarios re-typed. This is OpenSpec tooling's design; the cost is low (one-time copy+paste) and the benefit (single source of truth when archived) is high.

### Decision 2: Two scenarios, not one

**Options considered:**

- **(A) One scenario** titled "Dual binding is a long-term commitment" covering both "no silent simplification" and "escape hatch exists."
- **(B) Two scenarios** — one for the commitment assertion, one for the explicit escape hatch path.

**Decision: (B) two scenarios.**

**Rationale:**

- A scenario is supposed to test one observable contract. Conflating "don't remove the binding" with "here's how to remove it legitimately" dilutes both.
- Future readers searching for "how do I globalize node_id if we ever want to?" will grep for "migration" or "global" — they should find a scenario dedicated to that answer, not a sub-bullet inside a commitment scenario.
- The cost of the second scenario is ~8 lines of text; the readability win is substantial.

### Decision 3: No cross-file references to `frontend/` or `sync_service`

The user's Q5 decision only concerns the Cypher in `_get_kg_relevance`. It does not (yet) propagate any new invariant into the frontend node-rendering pipeline or the `SyncService` write path. Those layers already use `canvasId` in their own ways (sync writes `canvasId`, frontend tracks canvas scope via the ReactFlow viewport). Introducing new cross-file requirements here would exceed the user's decision scope and create phantom obligations.

If Phase 2 or later finds a silent cross-canvas bug in sync or in frontend, that will be a **new** OpenSpec change with its own requirements. Not this one.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The MODIFIED delta fails to re-state all 5 original scenarios verbatim (typo, skipped scenario, reworded WHEN clause) | Medium | High — archive would mis-merge and silently drop a scenario | `openspec validate --strict` before archive; manual diff review of the pre-archive and post-archive `spec.md` |
| Future developer reads "long-term commitment" as "immutable" and abandons a legitimate simplification | Low | Medium | The second new scenario explicitly describes the escape hatch path |
| Static grep regression test drifts out of alignment with the new scenario wording | Low | Low | Grep test already exists and is already verified by the Phase 0 Hardening archive; this change does not alter the regex |
| OpenSpec CLI rejects the delta because the MODIFIED Requirement body text changes too much | Low | Medium | Keep the description change additive (append new sentence, don't reword existing); verify with `openspec validate --strict` |
| Archive merges the delta but the result is grammatically awkward | Low | Low | Design the new description addition as a standalone final sentence that reads cleanly after the existing body |

## Migration Plan

No migration. Zero code, zero data. Archive merges the delta and the next session's reads of `openspec/specs/algo-question/spec.md` see the extended Requirement.

## Rollback Plan

If the archive produces a mis-merged spec, revert the archive commit. All prior scenarios return to their pre-archive state. No code or data depends on the new scenarios.
