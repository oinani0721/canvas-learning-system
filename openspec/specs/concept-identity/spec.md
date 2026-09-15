# concept-identity Specification

## Purpose
TBD - created by archiving change a6-phase0-fsrs-card-state-bucket-preservation. Update Purpose after archive.
## Requirements
### Requirement: FSRS Card State Projection Snapshot Persistence

`ReviewService._save_card_states()` SHALL persist the in-memory card-state container
`self._card_states` as a **full snapshot**, serialized via `_card_states_payload()` (which
returns `_VaultScopedCardStates.to_nested()` — a vault-scoped nested mapping) with
`json.dumps(..., ensure_ascii=False, indent=2)`. The write is not incremental: each successful
call replaces the whole persisted document with the current in-memory contents.

The write MUST be performed as **temp-file-then-atomic-replace**: the serialized text is written
to `_CARD_STATES_FILE.with_suffix(".json.tmp")` and only then moved onto `_CARD_STATES_FILE` via
`Path.replace`; both filesystem steps are dispatched through `asyncio.to_thread`. The method MUST
NOT open the destination path in write mode, so a failure occurring before the replace step leaves
the destination's previous contents unchanged.

All card-state access and I/O — reading the previous value, applying the optional `pending`
mutation, serializing, and both filesystem steps — MUST execute inside the
`async with _card_states_lock:` critical section (a module-level `asyncio.Lock`). Applying the
mutation inside the lock is what binds the return value to *this* call's `card_data`: a mutation
applied outside the lock could be overwritten by a concurrent call, making `True` unable to
testify to this call's data.

When `pending` is supplied and its vault scope cannot be resolved, the method MUST **fail closed**:
`_card_states_try_set()` returns `False`, the concept is recorded in `self._unpersisted_concepts`,
and the method returns `False` **without touching the filesystem at all** — it returns before the
`try:` block, so not even the parent-directory `mkdir` runs. Silently writing into a default bucket
is forbidden, because that would both disguise a broken configuration as a successful write and
place one vault's card into another vault's bucket.

Failures inside the `try:` block MUST be normalized to a `False` return rather than propagating:
`TypeError`/`ValueError` (which covers the `UnicodeEncodeError` raised by a lone-surrogate
`concept_id`) additionally MUST roll the `pending` mutation back out of memory — restoring the
previous value, or removing the key when there was none — so that one poisoned entry cannot keep
failing the full-snapshot write for every other concept; `OSError` MUST retain the in-memory value
and only record the concept as unpersisted. Both paths MUST mark the pending concept dirty.

On a successful replace the method MUST clear `self._unpersisted_concepts` in full, and it does so
**unconditionally** — it does not check whether each cleared entry is actually represented in the
snapshot that just landed. The cleared marker therefore attests only that every concept *currently
held in memory* has been persisted. It does NOT restore a value that never reached memory (the
fail-closed path) or that was rolled back out of it (the serialization-failure path); those values
are absent from the projection and no later snapshot recovers them. Marker clearing is not data
healing, and this spec MUST NOT be read as promising the latter.

This file is a **projection/cache, not the FSRS scheduling truth source** (frontmatter is; CARD-G3-7).
A `True` return therefore attests only that the projection reached disk. Callers MUST report
`persisted` and `truth_source` as separate signals and MUST NOT let the former stand in for the
latter.

#### Scenario: Snapshot is published by atomic replace, never by writing the destination

- **GIVEN** a `ReviewService` whose `self._card_states` holds at least one card state
- **WHEN** `await review_service._save_card_states()` completes successfully
- **THEN** the serialized text was written to the `.json.tmp` sibling path and moved onto
  `_CARD_STATES_FILE` by `Path.replace`
- **AND** `_CARD_STATES_FILE` was never opened in write mode by this method
- **AND** the persisted document is the nested vault-scoped snapshot produced by
  `_card_states_payload(self._card_states)`, not a partial or incremental update

#### Scenario: Unresolvable vault scope fails closed without any filesystem write

- **GIVEN** `pending = (concept_id, card_data)` whose vault scope cannot be resolved
- **WHEN** `await review_service._save_card_states(pending)` is called
- **THEN** `_card_states_try_set()` reports failure and the method returns `False`
- **AND** `concept_id`'s dirty key is present in `self._unpersisted_concepts`
- **AND** no filesystem call is made — the method returns before the `try:` block, so the
  parent-directory `mkdir`, the temp write, and the replace all do not happen

#### Scenario: Serialization failure is normalized to False and the mutation is rolled back

- **GIVEN** `pending` carries a `concept_id` or `card_data` that cannot be serialized
  (for example a lone surrogate, whose `UnicodeEncodeError` is a `ValueError`)
- **WHEN** `await review_service._save_card_states(pending)` is called
- **THEN** the method returns `False` instead of propagating the exception
- **AND** `self._card_states` no longer carries this call's mutation — the previous value is
  restored, or the key is removed when there was none
- **AND** the concept is recorded in `self._unpersisted_concepts`

#### Scenario: A successful snapshot clears every dirty marker without restoring lost values

- **GIVEN** an earlier call rolled a serialization-failing `pending` back out of memory and
  recorded its dirty key, so `self._unpersisted_concepts` is non-empty
- **WHEN** a later `await review_service._save_card_states()` completes successfully for a
  different, serializable concept
- **THEN** the method returns `True`
- **AND** `self._unpersisted_concepts` is empty — including the earlier concept's key
- **AND** the persisted snapshot still does NOT contain the rolled-back value, because it was
  never in memory to be serialized
