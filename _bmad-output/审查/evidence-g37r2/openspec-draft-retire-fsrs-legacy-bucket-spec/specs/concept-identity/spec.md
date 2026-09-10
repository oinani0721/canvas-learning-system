## REMOVED Requirements

### Requirement: FSRS Card State Legacy Bucket Preservation On Save

**Reason**: The requirement specifies a two-bucket card-state model that has never existed in this branch's implementation or its history. Three independent measurements on `card-u9-mastery` @ `8f7440ef` (2026-09-08):

1. `grep -E '_legacy_card_states|is_uuid_v4' -- backend/app` → **0 hits**. Neither the second bucket nor the partitioning predicate the requirement names exists anywhere in production code.
2. `git log --oneline -S'_legacy_card_states' -- backend/app/services/review_service.py` → **empty**. The identifier has never appeared in this file in the entire branch history, so this is not a regression that removed a working implementation.
3. `ReviewService._load_card_states` (`backend/app/services/review_service.py:545-563`) returns the loaded dict verbatim (`return loaded` / `return {}`) with **no key partitioning at all**. The single bucket `self._card_states` (`:526`) is the only one that exists.

The requirement is additionally unmoored from the code it names: it specifies `save_card_state(concept_id=..., concept_name=..., card_data=..., canvas_name=..., rating=3)`, but the method's signature at `review_service.py:2364` has no `concept_name` parameter, and that method has zero call sites in `backend/app` and is retired in the same batch.

Keeping the requirement is worse than having no requirement: a reader who trusts it concludes that pre-migration FSRS card data is preserved across saves. It is not preserved, because there is no second bucket and no pre-migration data path to preserve.

**Migration**: None required. No production code, test, or client implements or depends on the two-bucket contract, so there is no behavior to migrate away from and no consumer to notify.

- Code that persists FSRS card state continues to use `ReviewService._save_card_states()`, which serializes the single `self._card_states` dict inside `async with _card_states_lock:` — unchanged by this removal.
- The original wording and its motivation remain readable at `openspec/changes/archive/2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation/`, which this change does not modify.
- Anyone who wants the `concept-identity` capability to specify the single-bucket serialization contract that *does* exist should raise a separate proposal; deliberately writing that requirement is out of scope here, and inventing it as a side effect of this removal would turn today's implementation details into a contract nobody decided to make.
