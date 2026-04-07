# algo-question Specification

## Purpose
TBD - created by archiving change fix-fr-kg-04-schema-drift-and-sync-hardening. Update Purpose after archive.
## Requirements
### Requirement: kg_relevance Schema Correctness

The `_get_kg_relevance` Cypher query SHALL use Neo4j property names that match the `SyncService` write schema (`id` as primary key, `canvasId` as canvas reference). The query SHALL NOT use `{uuid: ...}` or `canvas_id` (snake_case), which reference non-existent fields in production data.

#### Scenario: kg_relevance finds nodes written by SyncService
- **WHEN** `SyncService._upsert_node` has written a `CanvasNode {id: "n1", canvasId: "c1"}` AND `_upsert_node` has written `CanvasNode {id: "n2", canvasId: "c1"}` AND they are connected by a `CANVAS_EDGE` relationship
- **THEN** `_get_kg_relevance(node_id="n1", canvas_id="c1")` returns a non-default value (computed from actual neighbors)

#### Scenario: kg_relevance does not silently return default when query is wrong
- **WHEN** `_get_kg_relevance` is called with a `node_id` that exists but whose Cypher query pattern fails to match
- **THEN** the method returns a tuple `(score, degraded_reason)` where `degraded_reason` identifies the failure mode (e.g., `"empty_graph"`, `"node_not_found"`, `"schema_mismatch"`)

#### Scenario: Production data is not in uuid-based schema
- **WHEN** a test runs `MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL RETURN count(n)` against production Neo4j
- **THEN** the count is 0 (or the test fails, indicating remaining legacy data that needs migration)

---

### Requirement: kg_relevance Weighted Edge Formula

The `_get_kg_relevance` method SHALL compute relevance as a weighted sum over typed edges, where `CANVAS_EDGE` (user-drawn) weighs higher than `RELATES_TO` (LLM-inferred). The final score SHALL be normalized to `[0, 1]`.

#### Scenario: CANVAS_EDGE neighbors contribute weight 1.0
- **WHEN** a node has 3 `CANVAS_EDGE` neighbors and 0 `RELATES_TO` neighbors
- **THEN** `weighted_degree = 3 * 1.0 = 3.0` AND normalized `kg_relevance = min(1.0, 3.0 / 8.0) = 0.375`

#### Scenario: RELATES_TO neighbors contribute weight 0.7
- **WHEN** a node has 0 `CANVAS_EDGE` neighbors and 4 `RELATES_TO` neighbors
- **THEN** `weighted_degree = 4 * 0.7 = 2.8` AND normalized `kg_relevance = min(1.0, 2.8 / 8.0) = 0.35`

#### Scenario: Mixed neighbors sum weighted contributions
- **WHEN** a node has 2 `CANVAS_EDGE` and 3 `RELATES_TO` neighbors
- **THEN** `weighted_degree = 2 * 1.0 + 3 * 0.7 = 4.1` AND normalized `kg_relevance = min(1.0, 4.1 / 8.0) ≈ 0.5125`

#### Scenario: High-degree node is capped at 1.0
- **WHEN** a node has 10 `CANVAS_EDGE` neighbors
- **THEN** `weighted_degree = 10.0` AND normalized `kg_relevance = min(1.0, 10.0 / 8.0) = 1.0`

#### Scenario: Other edge types are ignored
- **WHEN** a node has 5 `HAS_TIP` and 3 `HAS_MISCONCEPTION` neighbors but no `CANVAS_EDGE` or `RELATES_TO` neighbors
- **THEN** `weighted_degree = 0` AND the method returns `(0.5, degraded_reason="empty_graph")` (default with marker)

---

### Requirement: Degraded Reason Observability

The `_get_kg_relevance` method SHALL return structured degradation information when it cannot compute a meaningful score, instead of silently returning the default 0.5.

#### Scenario: Empty graph returns degraded marker
- **WHEN** `_get_kg_relevance` queries a node with no `CANVAS_EDGE` or `RELATES_TO` neighbors
- **THEN** the method returns `(0.5, degraded_reason="empty_graph")` AND the caller may log/track this signal

#### Scenario: Neo4j connection failure returns degraded marker
- **WHEN** the Cypher query raises `ConnectionError` or `asyncio.TimeoutError`
- **THEN** the method returns `(0.5, degraded_reason="neo4j_unavailable")`

#### Scenario: Valid computation returns no degraded marker
- **WHEN** the query returns a non-empty result set
- **THEN** the method returns `(computed_score, degraded_reason=None)`

---

### Requirement: NodePriority Formula Stability

The exam node priority formula SHALL remain `0.4 * (1 - p_mastery) + 0.3 * (1 - retrievability) + 0.3 * kg_relevance`. The `kg_relevance` fix MUST NOT alter weights or the additive structure.

#### Scenario: Weights remain unchanged
- **WHEN** the `NodePriority.calculate` method is invoked
- **THEN** it uses constants `W_MASTERY = 0.4`, `W_RETRIEVABILITY = 0.3`, `W_KG_RELEVANCE = 0.3`

#### Scenario: Priority reacts to fixed kg_relevance
- **WHEN** three nodes have identical `p_mastery=0.5, retrievability=0.5` but `kg_relevance` values of `0.1`, `0.5`, `0.9`
- **THEN** the priority ranking is `node3 > node2 > node1` (higher kg_relevance yields higher priority)

#### Scenario: Fixing kg_relevance changes downstream behavior
- **WHEN** a regression test compares `select_target_node` output before and after the schema fix (on identical test data)
- **THEN** the post-fix output may differ because kg_relevance now returns meaningful values instead of constant 0.5

---

### Requirement: exam_service_ext Schema Alignment

The `exam_service_ext.py` module SHALL NOT write `CanvasNode` nodes with `{uuid: $node_id}` schema. All CanvasNode writes SHALL use the unified `{id: $node_id}` + `canvasId` schema consistent with `SyncService`.

#### Scenario: No uuid-based writes remain
- **WHEN** a CI linter greps for `MERGE \(n:CanvasNode \{uuid:` in the `backend/app/services/` directory
- **THEN** the search returns no matches (excluding `backend/mutants/` test fixtures)

#### Scenario: exam_service_ext writes match SyncService schema
- **WHEN** `exam_service_ext` creates a CanvasNode (e.g., for exam target seeding)
- **THEN** the Cypher uses `MERGE (n:CanvasNode {id: $node_id})` so that it is findable by queries from `recommendation_service`, `question_generator`, and `verification_service`

