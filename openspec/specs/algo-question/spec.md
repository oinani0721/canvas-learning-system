# algo-question Specification

## Purpose
TBD - created by archiving change fix-fr-kg-04-schema-drift-and-sync-hardening. Update Purpose after archive.
## Requirements
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

### Requirement: Mastery Data Flows Through MasteryEngine

The `question_generator._get_mastery_data(node_id)` helper SHALL obtain volatile mastery fields (`effective_proficiency`, `mastery_level`, `mastery_label`, `retrievability`) by calling `MasteryEngine` instance methods on a `ConceptState` returned from `mastery_store.get_concept(node_id)`. The helper SHALL NOT use `getattr(concept, "<volatile_field>", default)` to read these fields, because `ConceptState` (defined at `backend/app/models/mastery_state.py`) is documented as storing only stable fields and explicitly never persists volatile values. Reading volatile fields via `getattr` silently returns the default value (e.g., `0.0`), which corrupts downstream difficulty selection and Gemini prompt rendering.

This requirement exists because of a long-standing silent bug discovered during ChatGPT Deep Research review of the previous A10 change `a10-fsrs-fusion-formalization`. The fix wires `question_generator` into the existing `get_mastery_engine()` global singleton (initialized at `backend/app/main.py:220-261` with fusion engine attached), restoring the intended Story 5.6 multi-signal fusion consumption path.

#### Scenario: Volatile fields are computed via MasteryEngine

- **GIVEN** a `ConceptState` instance returned by `mastery_store.get_concept(node_id)`
- **AND** the global `MasteryEngine` singleton is fusion-enabled (initialized at startup)
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned dict contains `effective_proficiency = mastery_engine.effective_proficiency(concept)`
- **AND** the returned dict contains `mastery_level = mastery_engine.mastery_level(concept)`
- **AND** the returned dict contains `mastery_label = mastery_engine.mastery_label(concept)`
- **AND** the returned dict contains `retrievability = mastery_engine.get_retrievability(concept)`

#### Scenario: Non-zero fused mastery propagates to ACP

- **GIVEN** a `ConceptState` whose 5 signals fuse to `fused_mastery = 0.85`
- **AND** the concept has no override and no self-assess decay
- **WHEN** `_get_mastery_data(node_id)` is invoked and the result populates an `ACPData` object via `acp.effective_proficiency = mastery.get("effective_proficiency", 0.0)`
- **THEN** `acp.effective_proficiency == 0.85` (within float tolerance), not `0.0`

#### Scenario: Difficulty selector reflects real proficiency

- **GIVEN** an `ACPData` with `effective_proficiency = 0.85` populated by the fixed `_get_mastery_data`
- **WHEN** the question_generator difficulty branch evaluates `acp.effective_proficiency` against the thresholds at lines 482-489
- **THEN** the chosen `difficulty_level` is `"hard"` (the branch `else` after `0.7`), not `"easy"`

#### Scenario: Not-assessed concepts return zero proficiency

- **GIVEN** a `ConceptState` with `interaction_count == 0` (never assessed)
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned `effective_proficiency` is `0.0` (per `MasteryEngine.effective_proficiency` line 344-346 contract)
- **AND** `mastery_label` is `"Not Assessed"`
- **AND** the difficulty selector still picks `"easy"` (correctly, because the learner has no demonstrated mastery)

#### Scenario: getattr fallback path is removed

- **GIVEN** a code review of `question_generator.py:_get_mastery_data` after this change
- **WHEN** searching for the pattern `getattr(concept, "effective_proficiency"` or `getattr(concept, "mastery_level"` or `getattr(concept, "mastery_label"` or `getattr(concept, "retrievability"`
- **THEN** no matches are found
- **AND** the function instead imports `from app.services.mastery_engine import get_mastery_engine` and uses `engine.effective_proficiency(concept)` etc.

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

