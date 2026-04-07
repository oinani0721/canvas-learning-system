## 1. Core Fix (review_service.py _save_card_states)

- [x] 1.1 Read the full `_save_card_states` function body (~lines 397-415) in `.worktrees/fix-concept-id-identity-unification/backend/app/services/review_service.py` and confirm line 406 is the `json.dumps(self._card_states, ...)` target
- [x] 1.2 Replace the serialization payload: introduce `combined = {**self._legacy_card_states, **self._card_states}` before the `json.dumps` call and use `combined` as the first argument to `json.dumps`
- [x] 1.3 Update the existing `logger.debug` line below `json.dumps` to report `len(combined)` instead of `len(self._card_states)`, so that future regressions where one bucket silently empties are visible in operator logs

## 2. Round-Trip Regression Test

- [x] 2.1 Create `.worktrees/fix-concept-id-identity-unification/backend/tests/unit/test_review_service_legacy_bucket_round_trip.py` with 3 async pytest scenarios matching `specs/concept-identity/spec.md`: round-trip preserves both buckets, empty-legacy case, and save-card-state preservation
- [x] 2.2 Use `tmp_path` pytest fixture + monkey-patching of `_CARD_STATES_FILE` to give each scenario its own isolated JSON file (no cross-test pollution)
- [x] 2.3 Import `is_uuid_v4` and `ReviewService` via the same paths already used by `test_card_states_compat_read.py` for consistency

## 3. Verification

- [x] 3.1 Run `cd .worktrees/fix-concept-id-identity-unification && .venv/bin/pytest backend/tests/unit/test_review_service_legacy_bucket_round_trip.py -x -v` and confirm all 3 scenarios pass
- [x] 3.2 Run `cd .worktrees/fix-concept-id-identity-unification && .venv/bin/pytest backend/tests/unit/test_card_states_compat_read.py backend/tests/unit/test_card_state_concurrent_write.py -x -v` to confirm the read-path and concurrent-write tests are not regressed
- [x] 3.3 From the main repo root, run `npx openspec validate a6-phase0-fsrs-card-state-bucket-preservation --strict` and confirm zero errors
- [x] 3.4 From the main repo root, run `npx openspec status --change a6-phase0-fsrs-card-state-bucket-preservation` and confirm `Progress: 4/4 artifacts complete`
