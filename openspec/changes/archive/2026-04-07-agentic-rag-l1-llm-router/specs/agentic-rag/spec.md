## ADDED Requirements

### Requirement: L1 Router LLM-based Channel Selection

The `fan_out_retrieval(state)` conditional edge in `backend/lib/agentic_rag/state_graph.py` SHALL determine which retrieval channels to activate via an LLM-based router (Gemini Flash) when `l1_router_strategy` is set to `"llm"` or `"hybrid"`. The LLM router SHALL receive the user query and a system prompt describing the 5 available retrieval channels, and SHALL return a JSON object `{"activate": [...], "reason": "..."}`. The router SHALL operate within a configurable timeout (default 3.0 seconds) and SHALL fall back to rule-based routing in `"hybrid"` mode when the LLM call fails for any reason. The function SHALL ALWAYS return a non-empty `list[Send]` regardless of any failure mode.

#### Scenario: hybrid strategy uses LLM for keyword-free knowledge query

- **GIVEN** the user submits the query `"万有引力的计算公式"`
- **AND** the runtime config has `l1_router_strategy="hybrid"`
- **AND** the LLM router successfully returns `{"activate": ["lancedb", "vault_notes"], "reason": "知识点定义"}` within timeout
- **WHEN** `fan_out_retrieval(state)` is called
- **THEN** the resulting Send list contains exactly the channels mapped from the LLM intent
- **AND** the structured log entry `[l1_router] route_decision` records `strategy="hybrid"`, `fallback_used=False`, `llm_success=True`

#### Scenario: hybrid strategy falls back to rule when LLM times out

- **GIVEN** the user submits any query
- **AND** the runtime config has `l1_router_strategy="hybrid"` and `l1_router_timeout_seconds=1.0`
- **AND** the LLM call exceeds the timeout (mocked with `asyncio.sleep(5)`)
- **WHEN** `fan_out_retrieval(state)` is called
- **THEN** the function executes `classify_query_intent(query)` as fallback
- **AND** the resulting Send list is built from the rule-based intent
- **AND** the structured log entry records `fallback_used=True`, `fallback_reason="TimeoutError"`
- **AND** the function still returns a non-empty `list[Send]`

#### Scenario: hybrid strategy falls back to rule when LLM returns invalid JSON

- **GIVEN** the user submits any query
- **AND** the runtime config has `l1_router_strategy="hybrid"`
- **AND** the LLM returns `"this is not valid json"` instead of a JSON object
- **WHEN** `fan_out_retrieval(state)` is called
- **THEN** the function falls back to `classify_query_intent` and returns its result
- **AND** the structured log records `fallback_reason="JSONParseError"`

#### Scenario: rule strategy completely skips LLM call

- **GIVEN** the runtime config has `l1_router_strategy="rule"`
- **WHEN** `fan_out_retrieval(state)` is called for any query
- **THEN** `llm_router.route()` is NOT invoked (verified via mock spy assertion)
- **AND** the result is built only from `classify_query_intent`
- **AND** no LLM API call is recorded in metrics

#### Scenario: llm strategy without rule fallback uses 5-channel safe degradation on failure

- **GIVEN** the runtime config has `l1_router_strategy="llm"`
- **AND** the LLM call fails with an exception
- **WHEN** `fan_out_retrieval(state)` is called
- **THEN** the result contains all 5 retrieval channels (graphiti / lancedb / multimodal / cross_canvas / vault_notes)
- **AND** the function does NOT call `classify_query_intent` (rule fallback only applies in hybrid mode)
- **AND** the structured log records `strategy="llm"`, `fallback_used=True`, `fallback_reason="<exception_type>"`

#### Scenario: multi-query rewrite shares a single LLM routing decision

- **GIVEN** the state contains `multi_queries=["导数的定义", "什么是导数", "导数 vs 微分"]` (3 rewritten variants)
- **AND** the runtime config has `l1_router_strategy="hybrid"`
- **WHEN** `fan_out_retrieval(state)` is called
- **THEN** `llm_router.route()` is invoked exactly 1 time (NOT 3 times — shared decision)
- **AND** the resulting Send list contains 3 × N entries where N is the number of channels for the shared intent

### Requirement: L1 Router Configuration Schema

The `CanvasRAGConfig` TypedDict in `backend/lib/agentic_rag/config.py` SHALL include three new optional fields for L1 routing control: `l1_router_strategy`, `l1_router_llm_model`, and `l1_router_timeout_seconds`. The `validate_config()` function SHALL enforce these fields' types and value ranges, replacing invalid values with defaults plus a WARNING log. The `DEFAULT_CONFIG` SHALL set safe defaults that match production-ready behavior.

#### Scenario: default config uses hybrid strategy

- **GIVEN** a fresh `DEFAULT_CONFIG` instance from `backend/lib/agentic_rag/config.py`
- **WHEN** the `l1_router_strategy` field is read
- **THEN** the value is `"hybrid"`
- **AND** `l1_router_llm_model` is `"gemini/gemini-2.0-flash"`
- **AND** `l1_router_timeout_seconds` is `3.0`

#### Scenario: validate_config rejects invalid strategy enum

- **GIVEN** a config dict with `l1_router_strategy="aggressive"` (not in allowed set)
- **WHEN** `validate_config(config)` is called
- **THEN** the result has `l1_router_strategy="hybrid"` (replaced with default)
- **AND** a WARNING log entry mentions `Invalid value for l1_router_strategy`

#### Scenario: validate_config clamps timeout to allowed range

- **GIVEN** a config dict with `l1_router_timeout_seconds=0.1` (below min=0.5)
- **WHEN** `validate_config(config)` is called
- **THEN** the result has `l1_router_timeout_seconds=3.0` (replaced with default)

#### Scenario: validate_config rejects empty string model name

- **GIVEN** a config dict with `l1_router_llm_model=""`
- **WHEN** `validate_config(config)` is called
- **THEN** the result has `l1_router_llm_model="gemini/gemini-2.0-flash"` (default)

### Requirement: L1 Router Observability

The `llm_router.route()` function and `fan_out_retrieval()` SHALL emit structured log entries for every routing decision, including both successful and failed paths. Each log entry SHALL include the fields `query` (truncated to 100 chars), `strategy`, `llm_called`, `llm_latency_ms`, `llm_success`, `fallback_used`, `fallback_reason`, `intent`, `activated_channels`, and `channel_count`.

#### Scenario: successful routing emits info log with all fields

- **GIVEN** the LLM router successfully resolves a query
- **WHEN** the routing decision is finalized
- **THEN** a `[l1_router] route_decision` info log is emitted
- **AND** the log contains all 10 required fields with non-null values

#### Scenario: failed routing emits warning log with error reason

- **GIVEN** the LLM router fails (timeout, JSON error, or API exception)
- **WHEN** the failure is handled
- **THEN** a `[l1_router] llm_failed_fallback_to_rule` warning log is emitted
- **AND** the log contains `fallback_reason` with the exception type name
- **AND** the log contains `llm_latency_ms` with the elapsed time before failure
