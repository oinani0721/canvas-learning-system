# algo-question Capability Delta

## ADDED Requirements

### Requirement: Mastery Data Degraded Observability

The `question_generator._get_mastery_data(node_id)` helper SHALL always return a dict that contains a `mastery_degraded: Optional[str]` key. The value SHALL be `None` on the happy path (when `mastery_store.get_concept(node_id)` returns a valid `ConceptState` and all `MasteryEngine` methods succeed). The value SHALL be the string `"concept_not_found"` when `store.get_concept` returns `None` (typical cause: the `CanvasNode.id` has no corresponding `EntityNode.mastery_concept_id` because the score event has not been processed yet, or an ID mapping gap exists). The value SHALL be the string `"exception"` when the function's try/except catches an `ImportError`, `AttributeError`, or `ValueError`.

The `ACPData.mastery_degraded` and `NodePriority.mastery_degraded` fields SHALL expose this value unchanged to downstream observability (log pipelines, prompt rendering decisions, and metrics). This parallels the existing `kg_relevance_degraded` field on `NodePriority` (which distinguishes `"empty_graph"` from `"neo4j_unavailable"` from the happy path).

This requirement exists because the A10 Phase 0 silent-bug fix restored the `MasteryEngine` call path in theory, but a subsequent ChatGPT Deep Research review identified that the fallback dict (`effective_proficiency=0.0`) is indistinguishable from the pre-fix bug's output when `get_concept` returns None. Without observability, a production regression (caused by ID mapping drift or event handler failure) would recur invisibly.

#### Scenario: Happy path returns None degraded flag

- **GIVEN** a `ConceptState` returned from `mastery_store.get_concept(node_id)`
- **AND** all `MasteryEngine` methods (`effective_proficiency`, `mastery_level_from_proficiency`, `get_retrievability`) succeed
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned dict contains `"mastery_degraded": None`
- **AND** downstream `acp.mastery_degraded` is `None`

#### Scenario: Concept not found returns concept_not_found marker

- **GIVEN** a `node_id` for which `mastery_store.get_concept(node_id)` returns `None` (no matching `EntityNode.mastery_concept_id`)
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned dict contains `"mastery_degraded": "concept_not_found"`
- **AND** the other fields use the documented fallback values (`p_mastery=0.1`, `effective_proficiency=0.0`, `mastery_level=0`, `mastery_label="Not Assessed"`, `retrievability=1.0`)
- **AND** the caller can distinguish this path from the happy-path "truly not assessed" result

#### Scenario: Exception returns exception marker

- **GIVEN** any of `get_mastery_store()`, `get_mastery_engine()`, `store.get_concept()`, or the `MasteryEngine` method calls raise `ImportError`, `AttributeError`, or `ValueError`
- **WHEN** `_get_mastery_data(node_id)` catches the exception
- **THEN** the returned dict contains `"mastery_degraded": "exception"`
- **AND** a debug log is emitted with the exception type and message

#### Scenario: NodePriority propagates mastery_degraded from batch path

- **GIVEN** `select_target_node` batch-gathers `_get_mastery_data` for N node_ids
- **AND** one of the results has `mastery_degraded="concept_not_found"`
- **WHEN** the resulting `NodePriority` objects are constructed
- **THEN** the corresponding `NodePriority.mastery_degraded` equals `"concept_not_found"`
- **AND** other node priorities retain their own `mastery_degraded` values (each node is observable independently)

### Requirement: Effective Proficiency Computed Once Per Mastery Query

The `question_generator._get_mastery_data(node_id)` helper SHALL invoke `MasteryEngine.effective_proficiency(concept)` **exactly once** per call, cache the result locally, and pass the cached value into `MasteryEngine.mastery_level_from_proficiency(eff, concept)` and `MasteryEngine.mastery_label_from_level(level)`. It SHALL NOT call `MasteryEngine.mastery_level(concept)` or `MasteryEngine.mastery_label(concept)` directly (these methods re-invoke `effective_proficiency` internally).

This requirement exists because the Phase 0 fix used the three direct methods (`effective_proficiency`, `mastery_level`, `mastery_label`), resulting in 3× redundant fusion computation per node (and 3N× for an N-node batch in `select_target_node`). The post-hardening helpers (`mastery_level_from_proficiency`, `mastery_label_from_level`) accept pre-computed inputs and decouple the call graph so that each `_get_mastery_data` invocation triggers exactly one `compute_fused_mastery` execution.

#### Scenario: Single invocation calls effective_proficiency once

- **GIVEN** a `MasteryEngine` with `effective_proficiency` instrumented (e.g., via mock spy)
- **WHEN** `_get_mastery_data(node_id)` is invoked once on a valid ConceptState
- **THEN** `engine.effective_proficiency` has been called exactly 1 time
- **AND** `engine.mastery_level_from_proficiency` has been called exactly 1 time
- **AND** `engine.mastery_level` (the un-cached variant) has been called 0 times
- **AND** `engine.mastery_label` (the un-cached variant) has been called 0 times

#### Scenario: Batch of N nodes triggers N fusion computations not 3N

- **GIVEN** `select_target_node` processes a canvas of 10 nodes
- **AND** `MasteryEngine.effective_proficiency` is instrumented
- **WHEN** the batch completes
- **THEN** `effective_proficiency` has been called exactly 10 times (one per node)
- **AND** is not called 30 times (which would indicate the pre-hardening 3x redundancy)

### Requirement: Bounded Concurrency for Batch Node Scoring

The `question_generator.select_target_node` method SHALL bound the per-node concurrent Neo4j queries using `asyncio.Semaphore(20)`, wrapping each `_get_mastery_data` and `_get_kg_relevance` call in an `async with semaphore:` block (matching the established pattern at `canvas_service.py:598-616`). The semaphore SHALL be function-local (fresh per `select_target_node` invocation) to avoid cross-request sharing.

This requirement exists because the existing `asyncio.gather` batch at `question_generator.py:166-175` issues 2*N concurrent Neo4j queries (N mastery + N kg_relevance) per call. On a 500-node canvas that is 1000+ simultaneous queries against a Neo4j pool sized for ~50 connections, risking exhaustion. Bounding the inner coroutines at 20 preserves the existing `return_exceptions=True` per-node degradation behavior while preventing pool saturation.

#### Scenario: Semaphore limits simultaneous in-flight queries

- **GIVEN** a `select_target_node` invocation with 100 node_ids
- **AND** each `_get_mastery_data` / `_get_kg_relevance` is instrumented to track currently in-flight calls
- **WHEN** the batch is processed
- **THEN** the maximum simultaneously in-flight count across both query types stays at or below 20
- **AND** all 100 nodes produce valid `NodePriority` objects (no nodes dropped by the bound)

#### Scenario: Small canvas remains unaffected by semaphore

- **GIVEN** a `select_target_node` invocation with 5 node_ids (well below the 20 limit)
- **WHEN** the batch is processed
- **THEN** the total wall-clock time is equivalent to the un-bounded version (within test tolerance)
- **AND** all 5 nodes produce valid `NodePriority` objects

## MODIFIED Requirements

### Requirement: kg_relevance Schema Correctness

The `_get_kg_relevance` Cypher query SHALL use Neo4j property names that match the `SyncService` write schema (`id` as primary key, `canvasId` as canvas reference). The query SHALL NOT use `{uuid: ...}` or `canvas_id` (snake_case), which reference non-existent fields in production data. Additionally, the primary node `n` in the MATCH clause SHALL bind **both** `id` and `canvasId` as map properties (not just `id`), so that the query is immune to future product decisions that allow non-globally-unique `node_id` values across canvases.

#### Scenario: kg_relevance finds nodes written by SyncService
- **WHEN** `SyncService._upsert_node` has written a `CanvasNode {id: "n1", canvasId: "c1"}` AND `_upsert_node` has written `CanvasNode {id: "n2", canvasId: "c1"}` AND they are connected by a `CANVAS_EDGE` relationship
- **THEN** `_get_kg_relevance(node_id="n1", canvas_id="c1")` returns a non-default value (computed from actual neighbors)

#### Scenario: kg_relevance does not silently return default when query is wrong
- **WHEN** `_get_kg_relevance` is called with a `node_id` that exists but whose Cypher query pattern fails to match
- **THEN** the method returns a tuple `(score, degraded_reason)` where `degraded_reason` identifies the failure mode (e.g., `"empty_graph"`, `"node_not_found"`, `"schema_mismatch"`)

#### Scenario: Production data is not in uuid-based schema
- **WHEN** a test runs `MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL RETURN count(n)` against production Neo4j
- **THEN** the count is 0 (or the test fails, indicating remaining legacy data that needs migration)

#### Scenario: Primary node is bound to canvasId

- **GIVEN** two different canvases `c-alpha` and `c-beta` each containing a `CanvasNode` with the same `id="shared-id"` (a hypothetical future where node IDs are per-canvas rather than global)
- **AND** `c-alpha`'s `shared-id` has 3 `CANVAS_EDGE` neighbors within `c-alpha`
- **AND** `c-beta`'s `shared-id` has 10 `CANVAS_EDGE` neighbors within `c-beta`
- **WHEN** `_get_kg_relevance(node_id="shared-id", canvas_id="c-alpha")` is invoked
- **THEN** the result reflects only the 3 neighbors in `c-alpha`, never the 10 in `c-beta`
- **AND** the Cypher MATCH clause contains both `id: $node_id` and `canvasId: $canvas_id` as map properties on the primary node `n`

#### Scenario: Cypher syntax check

- **GIVEN** the post-hardening `_get_kg_relevance` implementation
- **WHEN** a static grep of the Cypher query string runs
- **THEN** the MATCH clause matches the regex `MATCH\s*\(n:CanvasNode\s*\{id:\s*\$node_id,\s*canvasId:\s*\$canvas_id\}\)`
