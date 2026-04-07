## ADDED Requirements

### Requirement: Learning Context Read-Time Group Isolation

The `LearningContextService._fetch_neighbor_records` function SHALL accept a `group_id` parameter and apply it as a Cypher filter on both endpoints of the neighbor traversal. The Cypher query SHALL allow nodes whose `group_id` matches the requested value OR whose `group_id` is NULL (backward compatibility for historical demo data). The `get_node_context` function SHALL pass its received `group_id` argument through to `_fetch_neighbor_records`.

#### Scenario: Same node in two different groups returns disjoint neighbors
- **WHEN** Neo4j contains node `贝叶斯定理` with `group_id="physics"` connected to neighbor `条件概率` (also `group_id="physics"`), AND a separate node also named `贝叶斯定理` with `group_id="math"` connected to a different neighbor `贝叶斯网络` (also `group_id="math"`)
- **AND** `get_node_context(node_id="贝叶斯定理", group_id="physics")` is called
- **THEN** the returned `tier2.neighbors` MUST contain `条件概率` AND MUST NOT contain `贝叶斯网络`

#### Scenario: Historical NULL group_id node is still readable
- **WHEN** Neo4j contains a historical seed node with `group_id IS NULL`
- **AND** `get_node_context(node_id="<seed>", group_id="physics")` is called
- **THEN** the seed node IS included in the result (the `OR group_id IS NULL` clause permits orphan nodes)

#### Scenario: New write enforces non-null group_id
- **WHEN** any write through `SyncService` attempts to create an EntityNode without `group_id`
- **THEN** the write is rejected by the existing `1ea43b2` enforcement (no change in this requirement, just verification of the assumption)

---

### Requirement: Context API Cache Key Includes Group ID

The `_context_cache` in `backend/app/api/v1/endpoints/context.py` SHALL key each cached entry by the tuple `(group_id, node_id)`, serialized as the string `f"{group_id or DEFAULT_GROUP_ID}:{node_id}"` where `DEFAULT_GROUP_ID` is imported from `app.config` (currently `"cs188"`). Using the same constant as `LearningContextService.get_node_context`'s fallback prevents the "literal `default`" cache key from desynchronizing with the service-layer group_id the entry was actually computed under. The helper functions `_get_cached` and `_set_cache` SHALL accept this composite key string instead of bare `node_id`. The `get_node_context_endpoint` SHALL construct the composite key from its `node_id` path param and `group_id` query param before calling the helpers.

#### Scenario: Same node in two groups gets independent cache entries
- **WHEN** `GET /api/v1/context/n1?group_id=physics` is called, then `GET /api/v1/context/n1?group_id=math` is called within the 30s TTL
- **THEN** the second call MUST trigger a new `get_node_context()` invocation (the second call's response body is computed from physics-isolated data, not served from the first call's cache)

#### Scenario: Same node same group hits cache
- **WHEN** `GET /api/v1/context/n1?group_id=physics` is called twice within 30 seconds
- **THEN** the second call returns the cached body without invoking `get_node_context()` a second time

#### Scenario: Default group cache key uses DEFAULT_GROUP_ID
- **WHEN** `GET /api/v1/context/n1` is called without `group_id` query param
- **THEN** the cache key is `f"{DEFAULT_GROUP_ID}:n1"` (e.g. `"cs188:n1"` under current config), matching the same `DEFAULT_GROUP_ID` fallback used by `get_node_context` so that a None-group call and an explicit-default call share the same cache entry

#### Scenario: Cache eviction respects new key format
- **WHEN** the cache reaches `CACHE_MAX_SIZE=200` entries
- **THEN** LRU eviction removes the oldest entry by `cached_at` regardless of which composite key it uses

---

### Requirement: Cross Canvas Retriever Fail-Soft on Placeholder Implementation

When `find_related_canvases` returns an empty list (its current placeholder behavior), the `CrossCanvasRetriever` SHALL return an empty result list from `search()` instead of falling back to a `lancedb.search` call without the `canvas_file` filter. The retriever module SHALL log a one-time WARNING (deduplicated via a module-level `_warned_unimplemented` sentinel) explaining that `find_related_canvases` is not implemented.

#### Scenario: Placeholder find_related_canvases returns empty result
- **WHEN** `find_related_canvases` returns an empty list (current placeholder state)
- **AND** `CrossCanvasRetriever.search(query="贝叶斯", canvas_file="A.canvas")` is called
- **THEN** the returned list MUST be empty AND the log MUST contain `cross_canvas disabled` exactly once across the lifetime of the process

#### Scenario: Repeated calls do not spam warning log
- **WHEN** `search()` is called 100 times with empty `find_related_canvases` results
- **THEN** the warning log entry appears exactly once

#### Scenario: When find_related_canvases is implemented future-state
- **WHEN** a future change implements `find_related_canvases` to return `["B.canvas", "C.canvas"]`
- **THEN** `search()` MUST query the canvas_nodes table for B and C only AND MUST NOT trigger the warning log

---

### Requirement: Vault Notes Retriever Group ID Filter Interface

The `VaultNotesService.search` method SHALL accept an optional `group_id` parameter (default `None`). When `group_id` is non-None, the method SHALL filter the LanceDB result list using a "common-note downgrade" rule: a note SURVIVES the filter if its `metadata.subject_id` (or the nested `metadata.metadata_json.subject_id`) either equals the requested `group_id` OR is `None`. Notes with `subject_id == None` are treated as **common / 通用主题 notes** and join every group's result set — this prevents the filter from collapsing to an empty list under the current ingestion paths that do not yet populate `subject_id` consistently. When `group_id` is `None`, the method SHALL return all results unchanged (backward compatibility for the current single-vault assumption). The retriever node function `vault_notes_retrieval_node` is NOT required to pass `group_id` in this requirement.

#### Scenario: group_id None returns unfiltered results
- **WHEN** `VaultNotesService.search(query="...", num_results=10)` is called with no group_id
- **THEN** the result list contains all matching notes regardless of their `subject_id`

#### Scenario: group_id matches subject filters results (strict match plus common)
- **WHEN** LanceDB has 5 notes total, 3 with `metadata_json.subject_id=physics` and 2 with `metadata_json.subject_id=math`
- **AND** `search(query="...", num_results=10, group_id="physics")` is called
- **THEN** the result list contains the 3 physics notes (math notes excluded)

#### Scenario: group_id with no matching non-null subject returns only common notes
- **WHEN** `search(query="...", num_results=10, group_id="biology")` is called and no notes have `subject_id="biology"` but some notes have `subject_id=None`
- **THEN** the result list contains exactly the None-subject (common) notes, while notes with explicit non-matching subject_id are excluded

#### Scenario: Notes missing subject_id are INCLUDED under filter as common notes
- **WHEN** a note has no `metadata.subject_id` AND no `metadata_json.subject_id` field (or the field is explicitly `None`)
- **AND** `search(..., group_id="physics")` is called
- **THEN** that note IS in the result list (treated as a common / 通用主题 note that joins every group). This is intentional: under current ingestion paths subject_id is often unset, and strict exclusion would collapse the filter to zero results
