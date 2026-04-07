# Proposal: Fix FSRS Card State Legacy Bucket Overwrite (A6 Phase 0)

## Why

This change fixes a **P0 silent data-loss bug** in `backend/app/services/review_service.py:_save_card_states` discovered during ChatGPT Deep Research review of A6 (`docs/project-status/fr-exploration/A6.md`, User 2 的第 3 问：「FSRS 评分历史究竟会给我使用检验白板的时候会带来什么影响」).

The chain of discovery:

1. The in-flight worktree change [`fix-concept-id-identity-unification`](../../../.worktrees/fix-concept-id-identity-unification/openspec/changes/fix-concept-id-identity-unification/proposal.md) introduced the ConceptRef identity contract and split `ReviewService` card state into two in-memory buckets at load time:
   - `self._card_states` — UUID-keyed (authoritative after migration)
   - `self._legacy_card_states` — text-keyed (pre-migration legacy FSRS data)
   The `_load_card_states` + `_get_card_state` lookup chain correctly consults both buckets (and the worktree's existing Requirement "Card State Load Is Backward Compatible" codifies this).
2. ChatGPT Deep Research reviewed the A6 resolution summary doc against `origin/main` + `fix-concept-id-identity-unification` and flagged a P1 risk: the **write path** `_save_card_states()` (line 406) only serializes `self._card_states`, silently dropping `self._legacy_card_states`. Any `save_card_state()` call after init would persist-overwrite the file with UUID-only entries, **permanently deleting pre-migration FSRS data on the next restart**.
3. Independent verification by 5 parallel Explore agents confirmed the bug and corrected the severity to P0 (not P1):
   - `review_service.py:405-407` reads only `self._card_states` into the serialized JSON
   - The in-flight `backend/data/fsrs_card_states.json` fixture on main contains at least 1 legacy text key (`"node123"`), proving the scenario is not hypothetical
   - The existing test `test_card_states_compat_read.py` only exercises the load path, giving a false sense of safety
4. Deep exploration revealed that ChatGPT's 5 other A6-related claims were false alarms (Neo4j unique constraint already present at `001_canvas_constraints.cypher:22-23`; LLM Router schema validation already present at `llm_router.py:49-51,257`; pip-audit CI job already present at `.github/workflows/test.yml:71-85`; CORS mis-config not applicable under Tauri desktop + `X-CLS-Internal-Key` auth; 4/6 claims wrong). But 3 deeper P0s ChatGPT missed were surfaced: RELATES_TO write-side activation, `fsrs_difficulty` integration into question priority formula, and frontend edge-sync pipeline. These are out of phase-0 scope and tracked in `design.md` as Deferred follow-up changes.

This is an A6 **Phase 0 fix**: it precedes the larger A6 follow-ups because **no FSRS-related improvement is safe to ship until `_save_card_states` preserves the legacy bucket** — any other change merged before this one risks triggering the silent overwrite via some other save path, compounding the data loss.

## What Changes

- **FIXED** `backend/app/services/review_service.py:406` (`_save_card_states`): serialize the union of both buckets via `{**self._legacy_card_states, **self._card_states}` before `json.dumps`. The UUID bucket wins on the defensive (and in practice impossible) chance of a key collision, because `_load_card_states` uses `is_uuid_v4(key)` to partition the buckets into disjoint key spaces.
- **UPDATED** the `logger.debug` line at `review_service.py:411-413` to report `len(combined)` instead of `len(self._card_states)`, so that any future regression where one bucket silently empties is visible in operator logs.
- **NEW** `backend/tests/unit/test_review_service_legacy_bucket_round_trip.py` (~80 lines, 3 pytest-asyncio scenarios):
  - Round-trip preserves both buckets (mixed UUID + legacy text key on disk → save → re-load → both present)
  - Save with empty legacy bucket is byte-equivalent to the UUID-only case (no regression for fully-migrated installs)
  - Save after `save_card_state("<new-uuid>", ...)` preserves the pre-existing legacy bucket
- **NEW** spec requirement under `concept-identity`: codify that `_save_card_states()` MUST serialize both buckets (see `specs/concept-identity/spec.md`).

## Capabilities

### Modified Capabilities

- `concept-identity`: add 1 new ADDED Requirement "FSRS Card State Legacy Bucket Preservation On Save". This capability is being introduced by the sibling worktree change `fix-concept-id-identity-unification`. This phase 0 change is a peer add-on to the same capability and is archive-order-independent — whichever archives first creates `openspec/specs/concept-identity/spec.md`; the second appends its ADDED Requirement(s) via OpenSpec's append-only delta merge.

## Impact

- **Production behavior**: After merging this fix, legacy text-keyed FSRS card states (i.e. any entry whose key is not a UUID v4 — typically pre-migration data from before the ConceptRef refactor) will survive every save operation instead of being silently deleted on the next restart.
- **API**: zero change. No new endpoints, no modified request/response schemas.
- **Schema**: zero change. The on-disk format of `fsrs_card_states.json` is unchanged (still a flat `Dict[str, dict]`). Only the subset of keys that `_save_card_states` emits changes — from "UUID only" to "UUID ∪ legacy text".
- **Test impact**: 1 new test file (~80 lines, 3 scenarios). No existing test file is modified. `test_card_states_compat_read.py` already covers the read path and its assertions remain valid.
- **Risk**: zero. The modification is purely additive — merging two disjoint dicts cannot produce data that was not already in one of the input dicts. If `_legacy_card_states` is empty (fully-migrated install), the merge is a byte-equivalent no-op.
- **Rollback**: `git revert <commit>` is clean — the fix is a 5-line code change plus 1 new test file. The spec delta is append-only.
- **Relationship to the main worktree change**: this phase 0 sits **on top of** the `fix-concept-id-identity-unification` branch and depends on `_legacy_card_states` existing (introduced by that branch). It must land **before** the main worktree change merges to main, otherwise any production save triggered between `concept-identity` merge and this phase 0 merge risks the silent overwrite described above.
