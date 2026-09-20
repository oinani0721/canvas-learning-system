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

The write MUST be performed as **temp-file-then-atomic-replace**: the serialized text is first
encoded to UTF-8 **before any file is opened**; the resulting bytes are written to the
`_CARD_STATES_FILE.with_suffix(".json.tmp")` sibling, flushed and `os.fsync`'d, published onto
`_CARD_STATES_FILE` by `os.replace`, and the parent directory is `os.fsync`'d afterwards. The whole
sequence is dispatched through **one** `asyncio.to_thread` call. Encoding first is what keeps an
unencodable payload from ever creating the temp file; the `os.fsync` on the temp file is what keeps
a successful rename from publishing a name whose data has not yet reached the device. Every failure
path once the temp file exists MUST attempt to remove it. That removal is itself I/O and can fail:
`missing_ok=True` suppresses only `FileNotFoundError`, and a cleanup that fails for another reason
surfaces as an `OSError` and is normalized like any other, rather than being silently ignored. The
guarantee is therefore that every failure path *attempts* the removal — not that a `.json.tmp` can
never survive a call whose cleanup itself failed. The method MUST NOT open the
destination path in write mode, so a failure occurring before the replace step leaves the
destination's previous contents unchanged.

The whole filesystem sequence MUST additionally hold a module-level `threading.Lock`
(`_card_states_file_lock`), so that it is serialized between *threads* and not only between
coroutines. `async with _card_states_lock` releases the lock when a coroutine is cancelled, while
`asyncio.to_thread` cannot cancel a thread that has already started; without the thread lock two
threads can therefore sit on the same deterministic `.json.tmp` path, where the later one's
`open(tmp, "wb")` truncates the very inode the earlier one is still writing through. The temp file
name is deterministic rather than random, so this serialization covers one process only: concurrent
processes or workers are explicitly out of scope here.

Mutual exclusion is not ordering, so each call MUST also take a monotonic sequence number **before**
its thread is dispatched, and the publish MUST be discarded when a snapshot with a greater or equal
sequence number has already landed. Without that check, the still-running thread of a cancelled call
can publish a payload serialized at an earlier moment *after* a newer snapshot has landed and
cleared the dirty markers — a silently lost update. Discarding is correct rather than lossy because
every write is a **full** snapshot of the same in-memory container, so the newer one already
contains everything this call would have written; the call therefore still reports success.

All card-state access and I/O — reading the previous value, applying the optional `pending`
mutation, serializing, and both filesystem steps — MUST execute inside the
`async with _card_states_lock:` critical section (a module-level `asyncio.Lock`). Applying the
mutation inside the lock is what binds the return value to *this* call's `card_data`: a mutation
applied outside the lock could be overwritten by a concurrent call, making `True` unable to
testify to this call's data. That `asyncio.Lock` alone does not cover a cancelled call whose worker
thread is still running, which is why the filesystem sequence also takes `_card_states_file_lock`.

When `pending` is supplied and its vault scope cannot be resolved, the method MUST **fail closed**:
`_card_states_try_set()` returns `False`, the concept is recorded in `self._unpersisted_concepts`,
and the method returns `False` **without touching the filesystem at all** — it returns before the
`try:` block, so not even the parent-directory `mkdir` runs. Silently writing into a default bucket
is forbidden, because that would both disguise a broken configuration as a successful write and
place one vault's card into another vault's bucket.

`TypeError`, `ValueError` and `OSError` raised inside the `try:` block MUST be normalized to a
`False` return rather than propagating. `TypeError`/`ValueError` (which covers the
`UnicodeEncodeError` raised by a lone-surrogate `concept_id`) additionally MUST roll the `pending`
mutation back out of memory — restoring the previous value, or removing the key when there was
none — so that one poisoned entry cannot keep failing the full-snapshot write for every other
concept; `OSError` MUST retain the in-memory value and only record the concept as unpersisted.
Both paths MUST mark the pending concept dirty. Normalization is scoped to **those three exception
families inside that block**: anything else (and anything raised outside it) propagates to the
caller, so this spec MUST NOT be read as promising that the method always returns a `bool`.

The dirty-marker identity MUST be the vault-scoped pair `(vault_id, concept_id)` produced by
`_dirty_key()`, never a bare `concept_id`. The main state carries a vault dimension, so this
derived state must carry the same one: otherwise a failed write for concept `c` in vault A would
make vault B's *same-named* concept `c` report `persisted=False` on a cache hit — a cross-vault
false report. When the vault cannot be resolved, `None` stands in for `vault_id`, which is
faithful because in that case the projection was never advanced anyway.

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
  `_CARD_STATES_FILE` by `os.replace`
- **AND** `_CARD_STATES_FILE` was never opened in write mode by this method
- **AND** the persisted document is the nested vault-scoped snapshot produced by
  `_card_states_payload(self._card_states)`, not a partial or incremental update
- **AND** no `.json.tmp` sibling remains after the call

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
- **AND** no `.json.tmp` sibling was created (encoding happens before any file is opened)

#### Scenario: A successful snapshot clears every dirty marker without restoring lost values

- **GIVEN** an earlier call rolled a serialization-failing `pending` back out of memory and
  recorded its dirty key, so `self._unpersisted_concepts` is non-empty
- **WHEN** a later `await review_service._save_card_states()` completes successfully for a
  different, serializable concept
- **THEN** the method returns `True`
- **AND** `self._unpersisted_concepts` is empty — including the earlier concept's key
- **AND** the persisted snapshot still does NOT contain the rolled-back value, because it was
  never in memory to be serialized

#### Scenario: A dirty marker in one vault does not make a same-named concept in another look unpersisted

- **GIVEN** concept id `c` exists in both vault A and vault B
- **AND** a write for `c` under vault A failed, so `("A", "c")` is in `self._unpersisted_concepts`
- **AND** `("B", "c")` is NOT in `self._unpersisted_concepts` — vault B's own writes all succeeded
- **WHEN** `c` is served from cache while vault B is the active scope and its persisted state is
  queried via `_is_unpersisted()`
- **THEN** `c` is reported as persisted under vault B, because the lookup key is `("B", "c")`
  and that pair is not in the set
- **AND** a bare-`concept_id` marker identity would instead have reported vault B's `c` as
  unpersisted

#### Scenario: A failure after the temp file exists leaves no residue and keeps the destination unchanged

- **GIVEN** `_CARD_STATES_FILE` already holds a previous snapshot
- **AND** `pending = (concept_id, card_data)` is serializable, so the temp file does get created
- **WHEN** `os.replace` raises `OSError` while publishing the temp file onto the destination
- **THEN** `await review_service._save_card_states(pending)` returns `False` instead of propagating
- **AND** `concept_id`'s dirty key is present in `self._unpersisted_concepts`
- **AND** no `.json.tmp` sibling remains — the cleanup runs on every failure path, not only on the
  replace step (a cleanup that itself fails is the one case where a sibling can survive, and it is
  reported as a `False` return like any other `OSError`)
- **AND** `_CARD_STATES_FILE` is byte-for-byte identical to the previous snapshot
- **AND** at least one `os.fsync` happened **before** the `os.replace` attempt, so a rename that
  had succeeded could not have published a name whose data was still only in the page cache

#### Scenario: A stale snapshot never overwrites a newer one that already landed

- **GIVEN** a snapshot carrying sequence number `n` has already been published onto
  `_CARD_STATES_FILE`
- **WHEN** a thread belonging to an earlier, cancelled call tries to publish its own payload, whose
  sequence number is smaller than `n`
- **THEN** that publish is discarded: `_CARD_STATES_FILE` still holds the snapshot for `n`, byte for
  byte, and no `.json.tmp` is left behind
- **AND** a later call whose sequence number is greater than `n` does publish, so the check
  discriminates by sequence rather than refusing every write
