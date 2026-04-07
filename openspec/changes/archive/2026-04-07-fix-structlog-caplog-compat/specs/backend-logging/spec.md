## ADDED Requirements

### Requirement: Structured JSON Logging Output

The backend system SHALL emit all log events in single-line JSON format containing at minimum the fields `level`, `timestamp` (ISO 8601), `event` (or `message`), and `logger` (source module). The final JSON serialization SHALL be performed exactly once per log event — no double-serialization or nested JSON strings.

#### Scenario: Service logs a warning

- **GIVEN** a backend service has initialized `structlog.get_logger(__name__)`
- **WHEN** the service calls `logger.warning("Low clustering quality", silhouette=0.12)`
- **THEN** stdout receives exactly one line of valid JSON parseable by `json.loads`
- **AND** the JSON object contains `"level": "warning"`, `"event": "Low clustering quality"`, `"silhouette": 0.12`, and an ISO timestamp
- **AND** no second or nested JSON appears for the same event

#### Scenario: Third-party library uses stdlib logging

- **GIVEN** a third-party library calls `logging.getLogger("neo4j").info("Connection established")`
- **WHEN** the log event propagates to the root logger
- **THEN** stdout receives the event rendered as JSON with `"logger": "neo4j"` and `"level": "info"`
- **AND** the output format is identical to structlog-origin events (same shape)

### Requirement: Request ID Propagation Across Service Calls

The backend system SHALL propagate a `request_id` value from the incoming HTTP request through all log events emitted during that request's lifecycle, including events from services, repositories, and Neo4j client calls. The `request_id` SHALL be stored in `structlog.contextvars` and automatically merged into every log event without explicit passing.

#### Scenario: Client sends request with X-Request-ID header

- **GIVEN** the backend receives an HTTP request carrying header `X-Request-ID: trace-abc-123`
- **AND** the `LoggingMiddleware` has bound the header value into `structlog.contextvars`
- **WHEN** a downstream service calls `logger.info("Fetching node from Neo4j")`
- **THEN** the emitted JSON log event contains `"request_id": "trace-abc-123"`
- **AND** a subsequent `logger.info` in the same request from a different service also contains `"request_id": "trace-abc-123"`

#### Scenario: Client sends request without X-Request-ID header

- **GIVEN** the backend receives an HTTP request with no `X-Request-ID` header
- **WHEN** the `LoggingMiddleware` processes the request
- **THEN** a UUID is generated and bound into `structlog.contextvars` as `request_id`
- **AND** all log events for this request include the generated UUID as their `request_id` field

### Requirement: pytest caplog Fixture Visibility

The backend test environment SHALL make log events emitted via `structlog.get_logger(...)` visible to pytest's `caplog` fixture. A test MUST be able to assert on the content of `caplog.records` (or `caplog.text`) for any log event emitted during the test body, regardless of whether the emitting module uses stdlib `logging.getLogger` or `structlog.get_logger`.

#### Scenario: Test asserts on structlog warning

- **GIVEN** a pytest test importing a service module that uses `structlog.get_logger(__name__)`
- **AND** the test receives the `caplog` fixture from pytest
- **WHEN** the test triggers a code path that calls `logger.warning("Low clustering quality detected")`
- **THEN** `caplog.records` contains at least one `LogRecord` whose `message` (or `getMessage()`) contains `"Low clustering quality detected"`
- **AND** the `LogRecord.levelname` equals `"WARNING"`

#### Scenario: Test asserts on stdlib logging fallback path

- **GIVEN** a pytest test importing a module that still uses `logging.getLogger(__name__)` (e.g. a third-party library path)
- **WHEN** the test triggers a code path that calls `logger.error("Neo4j connection refused")`
- **THEN** `caplog.records` contains the corresponding `LogRecord` with `levelname="ERROR"` and the matching message
- **AND** the assertion is indistinguishable from a structlog-origin assertion

### Requirement: Idempotent Logging Initialization

The logging configuration entry point `configure_logging()` SHALL be safe to call more than once within the same Python process. Repeated calls SHALL NOT result in duplicate `StreamHandler` instances on the root logger, and SHALL NOT cause log events to appear multiple times on stdout.

#### Scenario: configure_logging called twice at startup

- **GIVEN** the process has not yet configured logging
- **WHEN** `configure_logging()` is called for the first time
- **AND** `configure_logging()` is called a second time (e.g. from a test fixture re-entry)
- **THEN** `logging.getLogger().handlers` contains exactly one handler of type `StreamHandler` wrapping a `structlog.stdlib.ProcessorFormatter`
- **AND** a single `logger.info("once")` call produces exactly one line on stdout

#### Scenario: pytest session re-initializes logging across test modules

- **GIVEN** the session-scoped `_configure_logging_for_tests` fixture has been executed once
- **WHEN** a subsequent test module is loaded and indirectly imports `app.main`
- **THEN** the number of handlers on the root logger remains exactly one
- **AND** the first `logger.info` from the new module still reaches `caplog.records`

### Requirement: Isolated Test Context Variables

The backend test suite SHALL ensure that `structlog.contextvars` bound during one test function does not leak into subsequent test functions. Any `request_id`, `user_id`, or other `contextvars` values set during a test MUST be cleared before the next test begins executing.

#### Scenario: Test A binds request_id, Test B reads contextvars

- **GIVEN** test function `test_a` calls `structlog.contextvars.bind_contextvars(request_id="test-A")`
- **AND** `test_a` completes
- **WHEN** test function `test_b` (running after `test_a`) calls `structlog.contextvars.get_contextvars()`
- **THEN** the returned dict does not contain the key `request_id`
- **AND** `test_b` sees an empty or default contextvars state

### Requirement: Production Log Format Stability

The logging bridge migration SHALL preserve the existing production log output format so that downstream log consumers (file collectors, log viewers, Docker logs) see no behavioral change beyond the addition of caplog-compatible bridging. The set of fields present in production log lines before and after the migration MUST be identical.

#### Scenario: Production log line before and after migration have identical fields

- **GIVEN** a baseline capture of 10 production log lines from the pre-migration backend
- **AND** a post-migration capture of the same 10 request flows
- **WHEN** both sets are parsed as JSON and their key sets are compared
- **THEN** the set of keys present in post-migration lines is a superset of pre-migration keys
- **AND** no previously-present key has been dropped
- **AND** the values for `request_id`, `level`, `timestamp`, and `event` follow the same format (UUID, lowercase level string, ISO 8601, human-readable event)
