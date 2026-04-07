## 1. Pre-Change Verification

- [x] 1.1 Read current `openspec/specs/algo-question/spec.md` to confirm the existing "kg_relevance Schema Correctness" Requirement contains exactly 5 scenarios (`kg_relevance finds nodes`, `does not silently return default`, `production data is not uuid-based`, `primary node is bound to canvasId`, `cypher syntax check`) and that the body text already states the dual binding rule
- [x] 1.2 Verify `backend/app/services/question_generator.py::_get_kg_relevance` already uses `MATCH (n:CanvasNode {id: $node_id, canvasId: $canvas_id})` (installed by Phase 0 Hardening #1, commit `e946043`)
- [x] 1.3 Confirm zero code changes are needed for this change (it is pure spec hardening)

## 2. Proposal Authoring

- [x] 2.1 Write `proposal.md` with sections: `Why` / `What Changes` / `Capabilities` / `Impact`
- [x] 2.2 Mark `algo-question` under Modified Capabilities (no new capability is added)
- [x] 2.3 Explicitly cite user decision 2026-04-07 Q5 as the source of the long-term commitment

## 3. Design Authoring

- [x] 3.1 Write `design.md` with Context, Goals, Non-Goals, Key Decisions, Risks, Migration Plan, Rollback Plan
- [x] 3.2 Document Decision 1: MODIFIED vs ADDED Requirement, and why MODIFIED wins
- [x] 3.3 Document Decision 2: two scenarios vs one combined scenario
- [x] 3.4 Document Decision 3: scope is limited to `_get_kg_relevance`, NOT propagated to `SyncService` / frontend

## 4. Spec Delta Authoring

- [x] 4.1 Create `specs/algo-question/spec.md` with header `## MODIFIED Requirements`
- [x] 4.2 Copy the 5 existing scenarios of "kg_relevance Schema Correctness" verbatim into the delta (MODIFIED Requirements require full re-statement)
- [x] 4.3 Extend the Requirement description with an additional paragraph establishing the long-term architectural commitment and citing user decision 2026-04-07
- [x] 4.4 Append new scenario "Dual binding is a long-term architectural commitment, not a migration waypoint"
- [x] 4.5 Append new scenario "Future migration to global node_id namespace requires explicit spec change"
- [x] 4.6 Ensure every scenario header uses exactly 4 hashtags (`#### Scenario:` — 3 hashtags silently fail)

## 5. Validation

- [ ] 5.1 Run `npx openspec validate a10-phase1-lock-canvasnode-dual-binding --strict` — expect 0 errors
- [ ] 5.2 Run `npx openspec status --change a10-phase1-lock-canvasnode-dual-binding` — expect `Progress: 4/4 artifacts complete`
- [ ] 5.3 Diff the pre-change `openspec/specs/algo-question/spec.md` against a mental model of the post-archive result — verify only "kg_relevance Schema Correctness" is touched and no other requirement loses scenarios

## 6. Archive

- [ ] 6.1 Run `npx openspec archive a10-phase1-lock-canvasnode-dual-binding -y`
- [ ] 6.2 Verify `openspec/specs/algo-question/spec.md` now contains the extended description and 7 scenarios under "kg_relevance Schema Correctness"
- [ ] 6.3 Verify all other requirements in the capability remain untouched (use `git diff openspec/specs/algo-question/spec.md` to confirm)

## 7. Commit + Push

- [ ] 7.1 Stage the archive directory and the merged spec with specific file paths (not `git add -A`)
- [ ] 7.2 Write commit message citing user decision 2026-04-07 Q5 and the scope "spec-only hardening, zero code"
- [ ] 7.3 Commit; the lefthook post-commit hook auto-pushes to both `backup` and `origin` remotes
- [ ] 7.4 Verify `git rev-parse HEAD == git rev-parse origin/main`
