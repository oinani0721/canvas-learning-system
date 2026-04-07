## ADDED Requirements

### Requirement: Episode Cache Per-Group Isolation

The `MemoryService` SHALL maintain its in-memory episode cache as a per-group structure (`Dict[group_id, Deque[episode, maxlen=MAX_EPISODE_CACHE]]`) instead of a single shared list. Each `group_id` SHALL have its own independent FIFO cache with capacity equal to `MAX_EPISODE_CACHE` (default 2000), and episodes belonging to one group SHALL never be evicted by writes from another group.

#### Scenario: Single group writes beyond limit only evicts its own data

- **GIVEN** `group_id="数学:微积分"` has 0 episodes in cache
- **WHEN** the service records 2100 learning events for `group_id="数学:微积分"` in sequence
- **THEN** `len(self._episodes_by_group["数学:微积分"]) == 2000`
- **AND** the 100 oldest episodes (the first 100 written) are no longer in the cache
- **AND** the 2000 most recent episodes are present in FIFO order

#### Scenario: Multiple groups never evict each other

- **GIVEN** `group_id="A"` has 1500 episodes AND `group_id="B"` has 600 episodes (total 2100 across both)
- **WHEN** the service records 1 more episode for `group_id="A"`
- **THEN** `len(self._episodes_by_group["A"]) == 1501`
- **AND** `len(self._episodes_by_group["B"]) == 600` (unchanged)
- **AND** no episode from group B was evicted

#### Scenario: Search consults only the requested group's bucket

- **GIVEN** `group_id="A"` has 100 episodes AND `group_id="B"` has 100 episodes
- **WHEN** `search_episodes(group_id="A", query="...")` is called via the in-memory fallback path
- **THEN** the search iterator only traverses `self._episodes_by_group["A"]`
- **AND** does not access `self._episodes_by_group["B"]`

#### Scenario: Stats endpoint exposes per-group counts

- **GIVEN** the cache contains `{"A": 1500 episodes, "B": 600 episodes, "C": 200 episodes}`
- **WHEN** the service returns `get_stats()`
- **THEN** the response contains `total_episodes=2300` (sum across all buckets)
- **AND** the response contains `groups_count=3`

### Requirement: Episode Cache Group Count Bound

The `MemoryService` SHALL enforce an upper bound `MAX_GROUPS` (default 100) on the number of distinct `group_id` buckets held in memory. When a new write would exceed this bound, idle buckets (no activity in the last 24 hours) SHALL be evicted in least-recently-accessed order until the count drops below `MAX_GROUPS`. Active buckets (touched within the last 24 hours) SHALL be protected from eviction.

#### Scenario: Idle group is evicted when MAX_GROUPS exceeded

- **GIVEN** the cache contains 100 group buckets AND `group_id="X"` was last accessed 25 hours ago
- **WHEN** a new write arrives for `group_id="NEW_101"` (a new bucket that does not yet exist)
- **THEN** `_evict_idle_groups_if_needed()` removes `group_id="X"` from the cache
- **AND** `len(self._episodes_by_group) == 100` after the write
- **AND** a structured log entry `idle_group_evicted` is emitted with `evicted_group="X", last_access=<timestamp>`

#### Scenario: Active groups are protected from eviction

- **GIVEN** the cache contains 100 group buckets and ALL of them were accessed within the last hour
- **WHEN** a new write arrives for `group_id="NEW_101"`
- **THEN** no group is evicted
- **AND** `len(self._episodes_by_group) == 101` (temporary overflow allowed when no idle groups exist)
- **AND** a structured log entry `max_groups_exceeded_no_idle` is emitted

#### Scenario: Last-access timestamp updated on every write

- **GIVEN** `group_id="A"` exists with `last_access = 2026-04-06T10:00:00`
- **WHEN** a new episode is recorded for `group_id="A"` at `2026-04-06T15:00:00`
- **THEN** `self._group_last_access["A"] == 2026-04-06T15:00:00`
- **AND** group A is treated as active in subsequent eviction passes

### Requirement: Episode Recovery From Neo4j Distributes Into Per-Group Buckets

When `MemoryService` recovers episodes from Neo4j on startup or after a connection recovery, the recovered episodes SHALL be distributed into per-group buckets based on each episode's `group_id` field, not appended to a single shared list. The recovery path SHALL respect the `MAX_EPISODE_CACHE` per-group cap and the `MAX_GROUPS` bound.

#### Scenario: Recovery distributes episodes by group_id

- **GIVEN** Neo4j contains 500 episodes with `group_id="A"` and 300 episodes with `group_id="B"`
- **WHEN** `recover_episodes_from_neo4j()` is called on startup
- **THEN** `len(self._episodes_by_group["A"]) == 500`
- **AND** `len(self._episodes_by_group["B"]) == 300`
- **AND** `self._episodes_recovered == True`

#### Scenario: Recovery respects per-group cap

- **GIVEN** Neo4j contains 2500 episodes with `group_id="A"`
- **WHEN** `recover_episodes_from_neo4j()` is called
- **THEN** `len(self._episodes_by_group["A"]) == 2000` (capped to MAX_EPISODE_CACHE)
- **AND** the most recent 2000 episodes (by timestamp) are kept

#### Scenario: Recovery handles missing group_id gracefully

- **GIVEN** Neo4j contains 100 legacy episodes without a `group_id` field (predates per-group isolation)
- **WHEN** `recover_episodes_from_neo4j()` is called
- **THEN** legacy episodes are placed in a fallback bucket with `group_id="__legacy__"`
- **AND** a structured log entry `legacy_episodes_recovered` reports the count

### Requirement: FR-KG-04 Documentation Reflects Real Sync Pipeline

The FR-KG-04 design document at `docs/project-status/fr-exploration/FR-KG-04/FR-KG-04.md` SHALL describe the real backend call chain: `POST /api/v1/sync/batch → SyncService.process_sync_batch() → _upsert_node/_upsert_edge → Neo4j (CANVAS_EDGE)`. References to `canvas_service.add_edge()` as the active path SHALL be removed or marked as historical/deprecated. The relationship label written by sync/batch SHALL be documented as `CANVAS_EDGE` (not `CONNECTS_TO`).

#### Scenario: Backend call chain section uses SyncService path

- **GIVEN** the FR-KG-04.md document, section "后端处理链路详解"
- **WHEN** the section is read
- **THEN** the call chain shows `POST /api/v1/sync/batch → SyncService.process_sync_batch()`
- **AND** the chain does NOT contain `canvas_service.add_edge()`
- **AND** the relationship label is `CANVAS_EDGE`

#### Scenario: Key functions table reflects active code paths

- **GIVEN** the FR-KG-04.md table "后端" key functions
- **WHEN** the table is read
- **THEN** entries for `_sync_edge_to_neo4j` and `sync_all_edges_to_neo4j` are removed or marked `[deprecated]`
- **AND** entries for `SyncService._upsert_node` and `SyncService._upsert_edge` are present

#### Scenario: Difficulty mapping section uses real thresholds

- **GIVEN** the FR-KG-04.md section describing FSRS difficulty mapping
- **WHEN** the section is read
- **THEN** the thresholds are 0.3 / 0.5 / 0.7 based on `effective_proficiency` (not 60 / 80 based on raw score)
- **AND** four difficulty levels are listed (easy, medium-easy, medium-hard, hard)
