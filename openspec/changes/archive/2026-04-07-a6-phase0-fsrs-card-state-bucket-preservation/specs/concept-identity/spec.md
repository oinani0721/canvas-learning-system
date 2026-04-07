## ADDED Requirements

### Requirement: FSRS Card State Legacy Bucket Preservation On Save

The `ReviewService._save_card_states()` method SHALL serialize the union of both in-memory card-state buckets — `self._card_states` (UUID-v4-keyed, authoritative post-migration) and `self._legacy_card_states` (text-keyed pre-migration legacy FSRS data) — to the persistent `fsrs_card_states.json` file. It MUST NOT silently drop the legacy bucket.

The merge MUST be computed as `{**self._legacy_card_states, **self._card_states}` so that on the defensively-handled (though impossible by construction) chance of a key collision, the UUID bucket value takes precedence. The UUID bucket is the authoritative source for any concept that has been re-keyed to its Canvas node UUID, and the text-bucket key space is disjoint from the UUID bucket key space because `_load_card_states` partitions keys via `is_uuid_v4(key)`.

The debug log line emitted by this method MUST report the size of the merged dictionary (not the size of `_card_states` alone), so that any future regression where one bucket silently empties is visible in operator logs.

The merge and serialization MUST happen inside the existing `async with _card_states_lock:` critical section to prevent a concurrent `save_card_state()` mutation from corrupting the serialized JSON.

#### Scenario: Round-trip preserves both buckets

- **GIVEN** `fsrs_card_states.json` exists on disk containing 1 UUID-v4 key (`"f4d10d8b-1234-4abc-89ab-cdef01234567"`) AND 1 legacy text key (`"node123"`)
- **AND** a `ReviewService` instance is initialized — after `_load_card_states` runs, `_card_states` contains the UUID entry and `_legacy_card_states` contains the text entry
- **WHEN** `await review_service._save_card_states()` is called (with no other mutations in between)
- **AND** the file is re-read from disk and a fresh `ReviewService` instance is initialized against the same file path
- **THEN** the fresh instance's `_card_states` still contains exactly the UUID entry
- **AND** the fresh instance's `_legacy_card_states` still contains exactly the text entry
- **AND** no warning about lost legacy keys is emitted during the save

#### Scenario: Save with empty legacy bucket is byte-equivalent to UUID-only case

- **GIVEN** `fsrs_card_states.json` contains only UUID-v4 keyed entries (a fully-migrated install with no pre-migration data)
- **AND** a `ReviewService` instance is initialized — `_card_states` contains all entries, `_legacy_card_states` is an empty dict `{}`
- **WHEN** `await review_service._save_card_states()` is called
- **THEN** the serialized JSON on disk is byte-equivalent to what `json.dumps(self._card_states, ensure_ascii=False, indent=2)` would have produced
- **AND** no error is raised
- **AND** the debug log line reports `len(combined) == len(self._card_states)`

#### Scenario: Save preserves new UUID entries written via save_card_state

- **GIVEN** `_card_states = {"<uuid-A>": {...}}` (1 UUID entry from init)
- **AND** `_legacy_card_states = {"text-B": {...}}` (1 legacy text entry from init)
- **WHEN** `await review_service.save_card_state(concept_id="<uuid-C>", concept_name="foo", card_data=..., canvas_name=..., rating=3)` is called, which internally triggers `_save_card_states()`
- **AND** the file is re-read from disk and a fresh `ReviewService` instance is initialized against the same file path
- **THEN** the fresh instance's `_card_states` contains both `<uuid-A>` and `<uuid-C>`
- **AND** the fresh instance's `_legacy_card_states` still contains exactly `text-B`
- **AND** the total number of entries in the serialized JSON is exactly 3
