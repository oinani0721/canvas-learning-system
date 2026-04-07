## MODIFIED Requirements

### Requirement: kg_relevance Schema Correctness

The `_get_kg_relevance` Cypher query SHALL use Neo4j property names that match the `SyncService` write schema (`id` as primary key, `canvasId` as canvas reference). The query SHALL NOT use `{uuid: ...}` or `canvas_id` (snake_case), which reference non-existent fields in production data. Additionally, the primary node `n` in the MATCH clause SHALL bind **both** `id` and `canvasId` as map properties (not just `id`), so that the query is immune to future product decisions that allow non-globally-unique `node_id` values across canvases.

This dual binding (`{id, canvasId}` on the primary node) is a **long-term architectural commitment** per user decision dated 2026-04-07 (A10 Phase 1 plan session, Q5). Canvas is the product's unit of isolation and cross-canvas data sharing is a deliberate act, not an ambient property. Removing either map property from the primary-node MATCH clause constitutes a breaking spec change that SHALL require a new MODIFIED Requirement explicitly superseding this one; it SHALL NOT be treated as an implementation-level simplification.

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

#### Scenario: Dual binding is a long-term architectural commitment, not a migration waypoint

- **GIVEN** a future refactor proposal that seeks to "simplify" `_get_kg_relevance` by removing either `id: $node_id` or `canvasId: $canvas_id` from the primary-node map properties, on the grounds that one of the values is "redundant"
- **WHEN** the refactor proposal is reviewed against this spec
- **THEN** the proposal SHALL be rejected unless it is accompanied by a new OpenSpec change whose `specs/algo-question/spec.md` contains a MODIFIED Requirement that explicitly supersedes "kg_relevance Schema Correctness"
- **AND** the reviewer's rejection SHALL cite this scenario as evidence that dual binding is not implementation-level code and is not eligible for in-place simplification
- **AND** the existing static grep regression test continues to fail against the simplified version, providing a mechanical second-layer guard

#### Scenario: Future migration to global node_id namespace requires explicit spec change

- **GIVEN** a hypothetical future product decision that `node_id` should become globally unique across canvases (e.g., to support cross-canvas linking or shared node libraries)
- **WHEN** the implementation of that decision is planned
- **THEN** the plan SHALL include a new OpenSpec change that introduces a MODIFIED Requirement for "kg_relevance Schema Correctness" whose body text removes the dual-binding clause and whose scenarios reflect the new single-binding rule
- **AND** only after that OpenSpec change is archived SHALL the `_get_kg_relevance` Cypher, the static grep regression test, and this spec be updated together
- **AND** this sequencing prevents silent partial migration where code is updated but the spec still promises dual binding (or vice versa)
