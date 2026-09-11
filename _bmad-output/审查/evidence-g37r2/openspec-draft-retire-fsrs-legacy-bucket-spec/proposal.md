## Why

The `concept-identity` capability's only requirement — "FSRS Card State Legacy Bucket Preservation On Save" — specifies a two-bucket card-state model (`_card_states` + `_legacy_card_states`, partitioned by `is_uuid_v4(key)`) that **has never existed in this branch's implementation or history**. Three independent measurements on `card-u9-mastery` @ `8f7440ef` confirm it: `grep -E '_legacy_card_states|is_uuid_v4' -- backend/app` returns 0 hits; `git log -S'_legacy_card_states' -- backend/app/services/review_service.py` returns nothing; and `_load_card_states` (`review_service.py:545-563`) returns the loaded dict verbatim with no partitioning at all. The requirement is therefore not "out of date" — it is a specification of behavior no code was ever written for, and it is now actively misleading: it names `save_card_state()` with a `concept_name` parameter the current signature does not have, and that method is being retired in the same batch for having zero call sites in `backend/app`.

## What Changes

- **BREAKING (spec only, no runtime behavior)**: Remove the requirement `FSRS Card State Legacy Bucket Preservation On Save` from the `concept-identity` capability, together with its three scenarios. No production code changes accompany this removal, because no production code ever implemented it.
- Record, in the removal's `Reason`/`Migration` fields, the three measurements that establish the requirement was never implemented, so a future reader can tell "deliberately retired" from "accidentally dropped".
- Leave `openspec/changes/archive/2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation/` untouched as the historical record of where the requirement came from.

## Capabilities

### New Capabilities

<!-- None. This change only removes an existing requirement. -->

### Modified Capabilities

- `concept-identity`: the sole requirement `FSRS Card State Legacy Bucket Preservation On Save` is removed. After this change the capability carries no requirements, which is the honest state: nothing in `backend/app` currently implements a concept-identity contract at the spec level.

## Impact

- **Specs**: `openspec/specs/concept-identity/spec.md` — one requirement and three scenarios removed by `openspec archive`. Handled by the CLI; the file is not edited by hand.
- **Production code**: none. The removal is a documentation-truth correction, not a behavior change.
- **Tests**: none. No test asserts the two-bucket contract; the two tests that referenced `save_card_state` by name are re-pointed at the real persistence entry point `_save_card_states` by the accompanying card work, independently of this change.
- **Docs**: `docs/fsrs-truth-source-d0-revision.md` and `docs/known-gotchas.md` reference the retired method by name; both are updated in the same card to say "retired" rather than "kept pending retirement".
- **Rollback**: `git revert` the archive commit. Because the change carries no code, revert restores the spec text and nothing else. The historical archived change directory is not modified and remains available as the source of the original wording.
- **Verification**: `openspec validate --specs --strict` (14 specs, all passing before the change) must remain green after archive, and `git diff -- openspec/specs/concept-identity/spec.md` must show the requirement removed by the CLI rather than by a hand edit.
