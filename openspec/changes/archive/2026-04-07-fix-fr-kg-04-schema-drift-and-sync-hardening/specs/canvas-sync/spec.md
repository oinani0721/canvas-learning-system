## ADDED Requirements

### Requirement: Batch Sync Endpoint Authentication

The `/api/v1/sync/batch` endpoint SHALL require a valid internal API key via the `X-CLS-Internal-Key` header for all write operations. The authentication SHALL use a fail-closed policy in production.

#### Scenario: Production request without API key is rejected

- **WHEN** a request to `/api/v1/sync/batch` is made with no `X-CLS-Internal-Key` header AND `DEBUG=False` AND `INTERNAL_API_KEY` is configured
- **THEN** the server responds with HTTP 403 Forbidden and detail "Invalid internal API key"

#### Scenario: Production request with wrong API key is rejected

- **WHEN** a request includes `X-CLS-Internal-Key: wrong-key` AND the configured `INTERNAL_API_KEY` is `"real-key"`
- **THEN** the server responds with HTTP 403 Forbidden

#### Scenario: Production with no API key configured fails closed

- **WHEN** `DEBUG=False` AND `INTERNAL_API_KEY` environment variable is empty
- **THEN** every request to `/api/v1/sync/batch` responds with HTTP 503 Service Unavailable and detail "Internal API key not configured"

#### Scenario: Development mode allows missing key with warning

- **WHEN** `DEBUG=True` AND `INTERNAL_API_KEY` is empty AND a request has no `X-CLS-Internal-Key` header
- **THEN** the request is processed normally AND a structured warning log "INTERNAL_API_KEY is not configured but DEBUG=True; allowing request (dev mode)" is emitted

#### Scenario: Valid key grants access

- **WHEN** the request includes `X-CLS-Internal-Key: test-internal-key` AND `INTERNAL_API_KEY` is configured as `test-internal-key`
- **THEN** the request proceeds to `SyncService.process_sync_batch` normally

### Requirement: Dependency-Aware Segment Commit

The backend SHALL process sync batches as three independent transactional segments ordered by entity dependency (Board → Node → Edge for create/update operations, and the reverse order for delete operations). Segments 1 and 2 (Board and Node) SHALL be fully atomic — any single operation failure inside these segments MUST trigger a rollback of the segment and abort all subsequent segments. Segment 3 (Edge) SHALL tolerate partial failures: independent edge operations MUST NOT block each other, and the segment SHALL commit as long as at least one operation succeeded. When a preceding segment aborts, every operation in the subsequent segments SHALL be returned to the client with `error_class = DEPENDENCY_MISSING`.

#### Scenario: Node segment succeeds, edge segment commits partial failures

- **GIVEN** a sync batch containing 2 node creates and 3 edge creates
- **AND** all 2 nodes succeed in Segment 2
- **AND** 2 of the 3 edges in Segment 3 succeed but 1 edge fails with a transient Neo4j error
- **WHEN** `process_sync_batch` completes
- **THEN** Segment 2's transaction is committed
- **AND** Segment 3's transaction is committed with the 2 successful edges persisted to Neo4j
- **AND** the `SyncBatchResponse` reports `synced_count = 4`, `failed_count = 1`
- **AND** the failed edge's result carries `error_class = TRANSIENT_ERROR`

#### Scenario: Node segment failure aborts edge segment

- **GIVEN** a sync batch containing 2 node creates and 3 edge creates
- **AND** 1 of the 2 nodes raises a validation error in Segment 2
- **WHEN** `process_sync_batch` completes
- **THEN** Segment 2's transaction is rolled back (no nodes persisted)
- **AND** Segment 3 is never executed
- **AND** the `SyncBatchResponse` contains 5 operation results
- **AND** the 3 edge operations all carry `error_class = DEPENDENCY_MISSING` with error message indicating the upstream segment failure

#### Scenario: Delete batch uses reverse segment order

- **GIVEN** a sync batch with `operation = "delete"` containing 1 board delete, 2 node deletes, and 3 edge deletes
- **WHEN** `process_sync_batch` partitions the batch into segments
- **THEN** the segments are executed in order Edge → Node → Board
- **AND** each segment follows the same atomic rule as the create/update path
- **AND** if any edge delete fails, Node and Board segments are still attempted only when the Edge segment committed at least one successful delete

### Requirement: Per-Operation Error Classification

Every `SyncOperationResult` returned by the backend SHALL include an `error_class` field of type `SyncErrorClass` (values: `VALIDATION_ERROR`, `DEPENDENCY_MISSING`, `TRANSIENT_ERROR`) whenever `success = false`. When `success = true`, `error_class` MUST be omitted or null. The frontend SHALL use this field to select a retry strategy without inspecting the human-readable `error` message.

#### Scenario: Invalid payload maps to VALIDATION_ERROR

- **GIVEN** an operation whose payload fails Pydantic validation (e.g. missing required field, oversized content)
- **WHEN** `_execute_operation` dispatches the payload and Pydantic raises `ValidationError`
- **THEN** the resulting `SyncOperationResult` has `success = false` and `error_class = VALIDATION_ERROR`
- **AND** the `error` field contains a sanitized, human-readable reason that does not leak internal details

#### Scenario: Missing edge endpoint maps to DEPENDENCY_MISSING

- **GIVEN** an edge upsert operation whose `sourceNodeId` or `targetNodeId` does not match any existing `CanvasNode` in Neo4j
- **WHEN** `_upsert_edge` runs the OPTIONAL MATCH + status query
- **THEN** a `SyncDependencyError` is raised
- **AND** the resulting `SyncOperationResult` has `success = false` and `error_class = DEPENDENCY_MISSING`

#### Scenario: Neo4j transient failure maps to TRANSIENT_ERROR

- **GIVEN** a Neo4j driver raising `ServiceUnavailable` or `ConnectionError` mid-operation
- **WHEN** the exception reaches the segment error handler
- **THEN** the resulting `SyncOperationResult` has `success = false` and `error_class = TRANSIENT_ERROR`
- **AND** the `error` field contains a fixed string `"Neo4j transient error"` (no internal state leaked)

### Requirement: Edge Endpoint Fail Fast Validation

The `_upsert_edge` method SHALL validate the presence of both `sourceNodeId` and `targetNodeId` in the payload before running any Cypher query. Missing or empty endpoint identifiers MUST raise `SyncDependencyError` immediately, without reaching Neo4j. The underlying Cypher MUST use `OPTIONAL MATCH` with an explicit status return so that even legitimate missing-node cases (e.g. stale outbox entries) are surfaced as `DEPENDENCY_MISSING` rather than silent no-ops.

#### Scenario: Empty endpoint id raises SyncDependencyError before Neo4j call

- **GIVEN** a sync operation with `entity_type = "edge"` whose payload has `sourceNodeId = ""` and `targetNodeId = "node_42"`
- **WHEN** `_upsert_edge` is invoked
- **THEN** a `SyncDependencyError` is raised before any Cypher query executes
- **AND** the error message identifies which field was missing
- **AND** the Neo4j driver records no query activity for this operation

#### Scenario: Valid endpoints persist CANVAS_EDGE relationship

- **GIVEN** nodes `node_A` and `node_B` already exist in Neo4j with matching canvasId
- **AND** an edge upsert operation with valid `sourceNodeId = "node_A"`, `targetNodeId = "node_B"`, `canvasId = "board_1"`, `label = "explains"`
- **WHEN** `_upsert_edge` runs
- **THEN** exactly one `CANVAS_EDGE` relationship is created between `node_A` and `node_B`
- **AND** the relationship carries `label = "explains"` and the correct timestamps
- **AND** the operation result has `success = true`

### Requirement: Operation ID Deduplication Within Batch

The backend SHALL deduplicate operations sharing the same `operation_id` within a single batch. When duplicates are detected, only the first occurrence SHALL be executed; every subsequent occurrence SHALL be returned with `success = false` and a distinguishing error message `"duplicate_operation_id_skipped"`. This guarantees that retries which accidentally include already-processed entries do not cause double writes.

#### Scenario: Duplicate operation_id in same batch is skipped

- **GIVEN** a sync batch containing two operations with identical `operation_id = "op-123"`
- **WHEN** `process_sync_batch` runs the deduplication step
- **THEN** the first operation is executed normally and its result reports the actual outcome
- **AND** the second operation is skipped with `success = false` and `error = "duplicate_operation_id_skipped"`
- **AND** no Neo4j query is issued for the second occurrence

### Requirement: Sync Payload Input Validation

The `SyncOperation` and `SyncBatchRequest` Pydantic models SHALL enforce the following constraints via `model_validator`: (1) edge `create` and `update` operations MUST carry both `source_node_id`/`sourceNodeId` and `target_node_id`/`targetNodeId` (supporting both snake_case and camelCase for frontend compatibility); (2) node `content` MUST NOT exceed 20000 characters; (3) edge `label` MUST NOT exceed 2000 characters; (4) `operations` array length MUST NOT exceed 500. Any constraint violation SHALL raise `pydantic.ValidationError` before the batch reaches `process_sync_batch`.

#### Scenario: Edge create missing sourceNodeId raises ValidationError

- **GIVEN** an HTTP POST to `/api/v1/sync/batch` with an edge create operation that omits `sourceNodeId`
- **WHEN** FastAPI parses the request body into `SyncBatchRequest`
- **THEN** Pydantic raises `ValidationError` with a message identifying the missing field
- **AND** the endpoint returns HTTP 400 (not 503)
- **AND** `process_sync_batch` is never invoked

#### Scenario: Oversized node content raises ValidationError

- **GIVEN** a node create operation with `content` field of 25000 characters
- **WHEN** FastAPI parses the request body
- **THEN** Pydantic raises `ValidationError` indicating the content length exceeds 20000
- **AND** the endpoint returns HTTP 400

#### Scenario: Batch exceeding 500 operations raises ValidationError

- **GIVEN** a sync batch containing 501 operations of any type
- **WHEN** FastAPI parses the request body
- **THEN** Pydantic raises `ValidationError` with `max_length` violation
- **AND** the endpoint returns HTTP 400 without processing any operation

### Requirement: HTTP Error Classification at Sync Endpoint

The `/api/v1/sync/batch` endpoint SHALL translate exceptions into distinct HTTP status codes: `pydantic.ValidationError` and `ValueError` → 400; `neo4j.exceptions.ServiceUnavailable` / `AuthError` / `ConnectionError` → 503; `neo4j.exceptions.Neo4jError` (non-service errors) → 500; any other `Exception` → 500. The response body for 500 and 503 responses MUST NOT include raw exception messages or internal state; only fixed strings like `"Neo4j unavailable"` or `"Internal server error"` are permitted.

#### Scenario: Validation failure returns 400 with sanitized detail

- **GIVEN** a sync batch with a payload that fails Pydantic validation
- **WHEN** the request is handled
- **THEN** the HTTP response status is 400
- **AND** the response body identifies which field failed validation
- **AND** the response does not contain stack traces or internal paths

#### Scenario: Neo4j unavailable returns 503 without leaking detail

- **GIVEN** the Neo4j service is not reachable on the configured port
- **WHEN** `process_sync_batch` attempts `session.begin_transaction`
- **AND** the driver raises `ServiceUnavailable`
- **THEN** the HTTP response status is 503
- **AND** the response body is exactly `{"detail": "Neo4j unavailable"}`
- **AND** no raw exception message or driver state appears in the response

#### Scenario: Normal batch returns 200 with per-operation results

- **GIVEN** a valid sync batch of 5 operations, all succeeding
- **WHEN** the request is handled
- **THEN** the HTTP response status is 200
- **AND** the response body contains a `SyncBatchResponse` with `synced_count = 5` and `failed_count = 0`

### Requirement: Frontend Error-Class-Driven Retry Strategy

The frontend `sync-engine.ts` SHALL consume the `error_class` field on each `SyncOperationResult` and select the outbox entry's fate deterministically: `VALIDATION_ERROR` → mark entry `permanentlyFailed = true` (never retried); `DEPENDENCY_MISSING` → mark entry with `retryPriority = 1` so the next poll sends it before ordinary entries; `TRANSIENT_ERROR` → schedule next retry using exponential backoff based on the existing `retryCount`. If the backend returns `undefined` or `null` for `error_class`, the frontend SHALL degrade to the current TRANSIENT behavior (exponential backoff) so forward-deployed clients remain compatible with older backends.

#### Scenario: VALIDATION_ERROR marks outbox entry permanently failed

- **GIVEN** an outbox entry with `retryCount = 0` and a pending edge create
- **WHEN** the backend responds with `success = false`, `error_class = "VALIDATION_ERROR"` for that entry
- **THEN** the `sync_outbox` record for that entry is updated with `permanentlyFailed = true` and `failureClass = "VALIDATION_ERROR"`
- **AND** subsequent `poll()` invocations skip the entry and do not include it in any batch

#### Scenario: DEPENDENCY_MISSING prioritises entry on next poll

- **GIVEN** an outbox entry for an edge create whose endpoint node is not yet synced
- **WHEN** the backend responds with `error_class = "DEPENDENCY_MISSING"` for that entry
- **THEN** the `sync_outbox` record is updated with `retryPriority = 1` and `failureClass = "DEPENDENCY_MISSING"`
- **AND** the next `poll()` cycle orders entries by `retryPriority DESC` before sending the batch
- **AND** the prioritised entry appears in the first outbound batch alongside any pending Node operations

#### Scenario: TRANSIENT_ERROR schedules exponential backoff

- **GIVEN** an outbox entry with `retryCount = 2`
- **WHEN** the backend responds with `error_class = "TRANSIENT_ERROR"` for that entry
- **THEN** the `sync_outbox` record is updated with `nextRetryAt = now + backoff(retryCount=2)` and `failureClass = "TRANSIENT_ERROR"`
- **AND** `retryCount` is incremented to 3

#### Scenario: Missing error_class falls back to TRANSIENT behavior

- **GIVEN** a response from an older backend that omits `error_class`
- **WHEN** `sync-engine.ts` processes the failed result
- **THEN** the outbox entry is scheduled as if `error_class = "TRANSIENT_ERROR"` was received
- **AND** no exception is raised by the frontend

### Requirement: Outbox Schema Extension for Failure Tracking

The Dexie database's `sync_outbox` store SHALL be extended with the following optional fields: `permanentlyFailed: boolean` (default `false`), `failureClass?: string`, `retryPriority?: number` (default `0`), `nextRetryAt?: string` (ISO 8601), `lastError?: string`. A Dexie version bump SHALL ship an `upgrade` callback that initializes defaults on all existing rows so pre-upgrade outbox entries remain processable after the migration.

#### Scenario: Existing outbox entries migrate with correct defaults

- **GIVEN** a Dexie database containing 10 `sync_outbox` entries written before the schema upgrade
- **WHEN** the application starts up with the new Dexie version
- **THEN** Dexie runs the `upgrade` callback
- **AND** all 10 existing entries have `permanentlyFailed = false` and `retryPriority = 0`
- **AND** `failureClass`, `nextRetryAt`, `lastError` remain `undefined` on the existing entries
- **AND** `poll()` continues to process those entries as if no upgrade had occurred

#### Scenario: New outbox entry writes accept the extended fields

- **GIVEN** the new schema is active
- **WHEN** `sync-engine.ts` writes an outbox entry with `failureClass = "DEPENDENCY_MISSING"` and `retryPriority = 1`
- **THEN** the Dexie store persists all fields without type errors
- **AND** a subsequent read returns the same field values

### Requirement: Outbox Entry CanvasId Enforcement

The frontend `sync-engine.ts` SHALL require every outbox entry to carry a non-empty `canvasId` (either on the entry itself or inside its payload). When an entry lacks a resolvable `canvasId`, the sync engine MUST NOT fall back to a literal `'default'` canvas identifier. Instead the entry SHALL remain in the outbox (skipped for this round) and a structured warning log SHALL be emitted so the missing context can be diagnosed.

#### Scenario: Entry with missing canvasId is skipped not defaulted

- **GIVEN** an outbox entry whose `payload.canvasId` and top-level `canvasId` fields are both `undefined`
- **WHEN** `sendBatch` groups entries by canvas
- **THEN** the entry is NOT added to any canvas group
- **AND** the entry is NOT sent to `/api/v1/sync/batch`
- **AND** the entry remains in `sync_outbox` with `syncedAt` unchanged
- **AND** a warning log is emitted identifying the entry `id` and the missing field

#### Scenario: Entry with valid canvasId is grouped normally

- **GIVEN** an outbox entry whose `payload.canvasId = "board_42"`
- **WHEN** `sendBatch` groups entries by canvas
- **THEN** the entry is added to the `"board_42"` group
- **AND** the resulting `SyncBatchRequest.canvasId` is `"board_42"`

### Requirement: CanvasNode Unified Schema

All writes to Neo4j CanvasNode nodes SHALL use `{id: $entity_id}` as the primary identifier and `canvasId` (camelCase) as the canvas reference. The legacy `{uuid}` and `canvas_id` (snake_case) schemas SHALL NOT be introduced by any new code path.

#### Scenario: SyncService writes canonical schema

- **WHEN** `_upsert_node` is called with any payload
- **THEN** the Cypher uses `MERGE (n:CanvasNode {id: $entity_id}) SET n.canvasId = $canvas_id`

#### Scenario: Query services use canonical schema

- **WHEN** any service queries CanvasNode to find nodes written by SyncService
- **THEN** the query uses `MATCH (n:CanvasNode {id: ...})` or `WHERE n.canvasId = ...` (NOT `{uuid}` or `canvas_id`)

### Requirement: Neo4j Constraints and Indexes

The system SHALL enforce Neo4j constraints to prevent duplicate canvas nodes and board naming collisions within the same subject.

#### Scenario: CanvasNode id is unique

- **WHEN** two sync operations attempt to create `CanvasNode` with the same `id`
- **THEN** the second MERGE idempotently updates the existing node (no duplicate created)

#### Scenario: CanvasBoard (subjectId, name) is unique

- **WHEN** a create operation attempts to insert `CanvasBoard {subjectId: "math", name: "linear-algebra"}` AND a board with the same `(subjectId, name)` already exists
- **THEN** the Neo4j constraint raises a violation error AND the operation is marked failed in the batch response

#### Scenario: CanvasNode canvasId is indexed

- **WHEN** any query filters `WHERE n.canvasId = $canvas_id`
- **THEN** Neo4j uses the `canvasnode_canvasid` index (verified by `EXPLAIN` showing `NodeIndexSeek`)
