## 1. Establish the evidence

- [x] 1.1 Measure `grep -E '_legacy_card_states|is_uuid_v4' -- backend/app` and record the hit count (expected: 0)
- [x] 1.2 Measure `git log --oneline -S'_legacy_card_states' -- backend/app/services/review_service.py` and record whether the identifier ever existed (expected: empty)
- [x] 1.3 Read `review_service.py:545-563` and record whether `_load_card_states` partitions keys (expected: no partitioning)
- [x] 1.4 Compare the requirement's `save_card_state(...)` call signature against `review_service.py:2364` and record the mismatch

## 2. Author the change

- [x] 2.1 Write `proposal.md` with `## Why` / `## What Changes` / `## Capabilities` / `## Impact`, listing `concept-identity` under Modified Capabilities
- [x] 2.2 Write `design.md` recording why `REMOVED` was chosen over `MODIFIED`, and why the capability is left with no requirements rather than given an invented replacement
- [x] 2.3 Write `specs/concept-identity/spec.md` with a `## REMOVED Requirements` delta carrying the exact requirement header, plus `**Reason**` (the four measurements) and `**Migration**` (none required, with justification)

## 3. Validate and archive

- [ ] 3.1 Run `openspec validate retire-fsrs-legacy-bucket-spec --strict` and confirm it passes
- [ ] 3.2 Run `openspec status --change retire-fsrs-legacy-bucket-spec` and confirm `Progress: 4/4 artifacts complete`
- [ ] 3.3 Run `openspec archive retire-fsrs-legacy-bucket-spec` so the CLI — not a hand edit — merges the delta into `openspec/specs/concept-identity/spec.md`
- [ ] 3.4 Confirm via `git diff --no-color -- openspec/specs/concept-identity/spec.md` that the requirement and its three scenarios were removed by the archive step
- [ ] 3.5 Re-run `openspec validate --specs --strict` and compare against the pre-change baseline of 14 specs passing; report the result as measured rather than adjusting the change to make it green
