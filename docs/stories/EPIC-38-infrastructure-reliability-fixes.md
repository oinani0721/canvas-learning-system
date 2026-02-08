# EPIC 38: Infrastructure Reliability Fixes

> **Origin:** Deep Explore 审计发现 6 个系统性基础设施问题，全部源于 BMad 模板盲区（D1-D6 维度缺失）。
> **Checklist applied:** `_bmad/bmm/checklists/infrastructure-ac-checklist.md` v1.0.0
> **Priority:** P1 — 功能"看起来工作"但数据可能丢失/不完整

---

## Epic Goal

修复 6 个已识别的基础设施可靠性问题，确保数据持久化、错误恢复、输入验证、配置安全、降级透明、端到端集成全部达标。

## Requirements Covered

| FR | Description | Story |
|----|-------------|-------|
| FR-38.1 | LanceDB 自动索引更新 | 38.1 |
| FR-38.2 | 学习历史持久化与恢复 | 38.2 |
| FR-38.3 | FSRS 状态初始化保障 | 38.3 |
| FR-38.4 | Dual-write 默认安全配置 | 38.4 |
| FR-38.5 | Canvas CRUD 降级写入 | 38.5 |
| FR-38.6 | 评分写入可靠性 | 38.6 |
| FR-38.7 | 端到端集成验证 | 38.7 |

---

## Story 38.1: LanceDB 自动索引触发

As a learner,
I want my Canvas node changes to be automatically indexed in LanceDB,
So that RAG context retrieval always has up-to-date content without manual API calls.

### Acceptance Criteria

**AC-1 (D1: Persistence — Write Trigger)**
**Given** a Canvas node is created or updated via the API
**When** the backend processes the CRUD request
**Then** a LanceDB index update is triggered automatically (async, non-blocking)
**And** the index update completes within 5 seconds of the CRUD operation
**And** no manual POST `/metadata/index` call is required

**AC-2 (D2: Resilience — Failure Handling)**
**Given** the automatic LanceDB index update fails (connection error, timeout)
**When** the error occurs
**Then** the CRUD operation still succeeds (index failure must not block CRUD)
**And** the failed index update is queued for retry (max 3 attempts, exponential backoff)
**And** a WARNING log is emitted: `"LanceDB index update failed for node {id}, queued for retry"`

**AC-3 (D1: Persistence — Startup Recovery)**
**Given** the application restarts with pending index updates in the queue
**When** the application starts
**Then** pending updates are retried during startup
**And** a startup log shows: `"LanceDB: {N} pending index updates recovered"`

### Code References

| File | Line | Current Behavior |
|------|------|-----------------|
| `backend/app/api/v1/endpoints/metadata.py` | L253-370 | POST `/metadata/index` — manual only |
| `backend/app/api/v1/endpoints/canvas.py` | L83-220 | Canvas CRUD — no LanceDB trigger |

### Implementation Notes

- Hook into CanvasService CRUD methods (add_node, update_node) to emit index event
- Use `asyncio.create_task()` with error callback (not bare fire-and-forget)
- Consider debouncing rapid updates (e.g., 500ms window)

---

## Story 38.2: Learning History Persistence & Restart Recovery

As a learner,
I want my learning history to survive application restarts,
So that my progress is never lost and AI context always has my full history.

### Acceptance Criteria

**AC-1 (D1: Persistence — Storage Location)**
**Given** a learning event is recorded via `record_episode_to_neo4j()`
**When** the event is appended to `self._episodes`
**Then** the event is also persisted to Neo4j (already done) **AND** the `_episodes` cache is recoverable from Neo4j on restart
**And** storage location: Neo4j (primary), `self._episodes` (runtime cache only)

**AC-2 (D1: Persistence — Restart Recovery)**
**Given** the application restarts
**When** `MemoryService` initializes
**Then** `self._episodes` is populated from Neo4j (query recent episodes, limit 1000)
**And** `get_learning_history()` returns non-empty results if previous sessions exist
**And** a startup log shows: `"MemoryService: recovered {N} episodes from Neo4j"`

**AC-3 (D5: Degradation — Neo4j Unavailable at Startup)**
**Given** Neo4j is unavailable when the application starts
**When** `MemoryService` attempts to recover episodes
**Then** `self._episodes` remains empty (graceful degradation)
**And** a WARNING log is emitted: `"MemoryService: Neo4j unavailable, starting with empty history"`
**And** new episodes recorded during this session are still appended to `self._episodes`
**And** recovery is re-attempted when Neo4j becomes available (lazy recovery on first query)

### Code References

| File | Line | Current Behavior |
|------|------|-----------------|
| `backend/app/services/memory_service.py` | L138 | `self._episodes: List[Dict] = []` — always starts empty |
| `backend/app/services/memory_service.py` | L369 | `self._episodes.append(episode)` — memory only |
| `backend/app/services/memory_service.py` | L394-467 | `get_learning_history()` — reads from `self._episodes` only |

### Implementation Notes

- Add `async def _recover_episodes_from_neo4j()` called in `__init__` or first access
- Neo4j query: `MATCH (e:Episode) WHERE e.user_id = $uid RETURN e ORDER BY e.timestamp DESC LIMIT 1000`
- If Neo4j is down at init, set `self._episodes_recovered = False` and retry on first `get_learning_history()` call

---

## Story 38.3: FSRS State Initialization Guarantee

As a learner,
I want the review priority calculation to always use real FSRS data when available,
So that my review schedule is truly personalized, not falling back to a fixed score.

### Acceptance Criteria

**AC-1 (D3: Input Validation — Non-null Guarantee)**
**Given** a review item is requested for the dashboard
**When** the backend queries FSRS state for a concept
**Then** if a valid FSRS card exists, `fsrs_state` is returned with all fields non-null
**And** if no FSRS card exists, the response is `{found: false, reason: "no_card_created"}`
**And** if `_fsrs_manager` is None, the response is `{found: false, reason: "fsrs_not_initialized"}`

**AC-2 (D3: Input Validation — Frontend Contract)**
**Given** the frontend receives a review item with `fsrs_state: null`
**When** `calculatePriority()` is called
**Then** the FSRS dimension uses a default score of 50 (existing behavior — validated as correct)
**And** the UI shows an indicator: "FSRS data unavailable" next to the priority score
**And** the `reason` field from the backend is logged to console for debugging

**AC-3 (D5: Degradation — FSRS Manager Initialization)**
**Given** the application starts
**When** `ReviewService` initializes `_fsrs_manager`
**Then** if initialization succeeds, log: `"FSRS manager initialized successfully"`
**And** if initialization fails, log WARNING: `"FSRS manager failed to initialize: {reason}"`
**And** the `/health` endpoint includes `fsrs: "ok"` or `fsrs: "degraded"`

**AC-4 (D4: Configuration — Auto Card Creation)**
**Given** a concept enters the review system for the first time
**When** no FSRS card exists for this concept
**Then** a default FSRS card is automatically created (stability=1.0, difficulty=5.0, state=New)
**And** subsequent queries for this concept return `{found: true}` with real data

### Code References

| File | Line | Current Behavior |
|------|------|-----------------|
| `backend/app/services/review_service.py` | L1693-1768 | `get_fsrs_state()` — returns `{found: False}` when no card |
| `backend/app/api/v1/endpoints/review.py` | L985-1034 | API endpoint — converts to `fsrs_state=None` |
| `canvas-progress-tracker/.../PriorityCalculatorService.ts` | L282-287 | `if (!state) → score: 50` (default) |
| `canvas-progress-tracker/.../TodayReviewListService.ts` | L714-768 | `queryFSRSStateForPriority()` — returns null on not found |

### Implementation Notes

- AC-4 is the root fix: create default FSRS cards when concepts enter the review system
- AC-1/AC-2 are defense-in-depth for cases where card creation fails
- Consider batch card creation for existing concepts without FSRS cards (migration)

---

## Story 38.4: Dual-Write Default Configuration Safety

As an operator deploying the system,
I want dual-write to JSON fallback to be enabled by default,
So that a fresh installation has Neo4j offline resilience out of the box.

### Acceptance Criteria

**AC-1 (D4: Configuration — Safe Default)**
**Given** a fresh installation with no `.env` file customization
**When** the application starts
**Then** `ENABLE_GRAPHITI_JSON_DUAL_WRITE` defaults to `true`
**And** the startup log shows: `"Dual-write: enabled (default)"`

**AC-2 (D4: Configuration — Explicit Disable)**
**Given** an operator sets `ENABLE_GRAPHITI_JSON_DUAL_WRITE=false` in `.env`
**When** the application starts
**Then** dual-write is disabled as configured
**And** the startup log shows: `"Dual-write: disabled (explicit configuration)"`
**And** a WARNING log is emitted: `"JSON fallback is disabled. Neo4j outage will cause data loss."`

**AC-3 (D4: Configuration — Missing Env Var)**
**Given** the `ENABLE_GRAPHITI_JSON_DUAL_WRITE` environment variable is not set
**When** the Settings class initializes
**Then** the default value is `True` (safe default)
**And** behavior is identical to AC-1

### Code References

| File | Line | Current Behavior |
|------|------|-----------------|
| `backend/app/config.py` | L409-412 | `ENABLE_GRAPHITI_JSON_DUAL_WRITE: bool = Field(default=False)` |
| `backend/app/services/memory_service.py` | L376-386 | `record_learning_event()` checks this flag |
| `backend/app/services/memory_service.py` | L990-1004 | `record_temporal_event()` checks this flag |

### Implementation Notes

- **One-line fix**: Change `default=False` to `default=True` in `config.py:L410`
- Add startup log in `main.py` or `dependencies.py` to announce dual-write status
- Add WARNING when explicitly disabled
- Update `.env.example` to document this flag

---

## Story 38.5: Canvas CRUD Graceful Degradation with JSON Fallback

As a learner,
I want my Canvas editing actions to be recorded even when Neo4j is unavailable,
So that my knowledge graph is eventually complete regardless of infrastructure status.

### Acceptance Criteria

**AC-1 (D5: Degradation — Memory Client None)**
**Given** `CanvasService._memory_client` is None (no memory system configured)
**When** a Canvas CRUD event occurs (create/update/delete node or edge)
**Then** if `ENABLE_GRAPHITI_JSON_DUAL_WRITE` is true, the event is written to JSON fallback
**And** the CRUD operation completes successfully
**And** a WARNING log (not DEBUG) is emitted: `"Memory client unavailable, writing to JSON fallback"`

**AC-2 (D5: Degradation — Neo4j Down but Memory Client Exists)**
**Given** `CanvasService._memory_client` exists but `memory_client.neo4j` is None or Neo4j is unreachable
**When** a Canvas CRUD event occurs
**Then** the event is written to JSON fallback (if dual-write enabled)
**And** the CRUD operation completes successfully
**And** a WARNING log is emitted: `"Neo4j unreachable, event written to JSON fallback"`

**AC-3 (D5: Degradation — Health Visibility)**
**Given** Canvas CRUD is operating in degraded mode (JSON fallback only)
**When** the `/health` endpoint is queried
**Then** the response includes `canvas_events: "degraded"` with `fallback: "json"`

**AC-4 (D2: Resilience — Log Level Upgrade)**
**Given** Canvas CRUD events are being skipped due to missing dependencies
**When** the skip occurs
**Then** the log level is WARNING (not DEBUG)
**And** the log message includes the event type and affected node/edge ID

### Code References

| File | Line | Current Behavior |
|------|------|-----------------|
| `backend/app/services/canvas_service.py` | L173-175 | `if _memory_client is None: return` — silent skip |
| `backend/app/services/canvas_service.py` | L278-286 | `_sync_edge_to_neo4j_with_retry()` — skip if None |

### Implementation Notes

- Refactor `_trigger_memory_event()`: before `return`, check if JSON fallback is enabled
- JSON fallback writes to `backend/data/canvas_events_fallback.json`
- Upgrade `logger.debug` → `logger.warning` for all skip paths
- Add fallback write function that doesn't require memory_client

---

## Story 38.6: Scoring Write Reliability (Timeout vs Retry Fix)

As a learner,
I want my quiz scores to be reliably saved after submission,
So that my learning progress is accurately tracked and not silently lost.

### Acceptance Criteria

**AC-1 (D2: Resilience — Timeout-Retry Alignment)**
**Given** a score is submitted and the memory write is triggered
**When** `_write_with_timeout()` executes
**Then** the timeout is >= 10 seconds (not 2 seconds)
**And** the internal retry mechanism (3 retries, exponential backoff 1s/2s/4s = 7s total) can complete within the timeout
**And** the timeout formula: `timeout >= sum(backoff) + margin` = `7s + 3s = 10s`

**AC-2 (D2: Resilience — Task Failure Tracking)**
**Given** a memory write task fails after all retries
**When** the final failure occurs
**Then** the failed write is recorded to a local fallback file: `data/failed_writes.jsonl`
**And** each entry includes: `{timestamp, event_type, concept_id, score, error_reason}`
**And** a WARNING log is emitted: `"Score write failed after 3 retries, saved to fallback: {concept_id}"`

**AC-3 (D2: Resilience — Fallback Recovery)**
**Given** failed writes exist in `data/failed_writes.jsonl`
**When** the application starts (or a recovery endpoint is called)
**Then** the system attempts to replay failed writes
**And** successfully replayed entries are removed from the fallback file
**And** a startup log shows: `"Recovered {N} failed writes, {M} still pending"`

**AC-4 (D6: Integration — User Feedback)**
**Given** a score write fails silently in the background
**When** the user checks their learning history
**Then** scores from the fallback file are included in the query results (merged view)
**And** the user never sees a "missing score" gap

### Code References

| File | Line | Current Behavior |
|------|------|-----------------|
| `backend/app/services/agent_service.py` | L3047-3059 | `asyncio.wait_for(timeout=2.0)` — too short for retry |
| `backend/app/services/agent_service.py` | L3066-3072 | `asyncio.create_task()` — no failure tracking |
| `backend/app/services/memory_service.py` | `_write_to_neo4j_with_retry()` | 3 retries, exponential backoff |

### Implementation Notes

- **Quick fix**: Change `timeout=2.0` → `timeout=10.0` in `agent_service.py:L3051`
- **Full fix**: Add `failed_writes.jsonl` fallback and startup recovery
- Consider adding a metric counter for failed writes (observable via /health)

---

## Story 38.7: End-to-End Integration Verification

As a developer,
I want to verify all Stories in this EPIC work together end-to-end,
So that the infrastructure reliability fixes are truly complete.

### Acceptance Criteria

**AC-1 (D6: Integration — Fresh Environment)**
**Given** a fresh environment with default configuration (no `.env` overrides)
**When** the application starts
**Then** dual-write is enabled (Story 38.4)
**And** FSRS manager is initialized (Story 38.3)
**And** startup log confirms: episodes recovered, dual-write enabled, FSRS ok

**AC-2 (D6: Integration — Full Learning Flow)**
**Given** the application is running
**When** a complete learning flow is executed:
  1. Create a Canvas node
  2. Start a learning session on that node
  3. Submit a quiz answer and receive a score
  4. Check the review dashboard for priority
**Then** the Canvas node is auto-indexed in LanceDB (Story 38.1)
**And** the learning event is in `get_learning_history()` (Story 38.2)
**And** the score is persisted (Story 38.6)
**And** the review priority uses real FSRS data (Story 38.3)

**AC-3 (D6: Integration — Restart Survival)**
**Given** the learning flow from AC-2 has completed
**When** the application is restarted
**Then** `get_learning_history()` returns the previously recorded events (Story 38.2)
**And** FSRS cards are still queryable (Story 38.3)
**And** LanceDB index is still valid (Story 38.1)

**AC-4 (D6: Integration — Degraded Mode)**
**Given** Neo4j is stopped (simulating infrastructure failure)
**When** the same learning flow is attempted
**Then** Canvas CRUD events go to JSON fallback (Story 38.5)
**And** learning events go to JSON fallback via dual-write (Story 38.4)
**And** scoring writes go to `failed_writes.jsonl` if all retries fail (Story 38.6)
**And** the `/health` endpoint shows degraded status for Neo4j-dependent features

**AC-5 (D6: Integration — Recovery)**
**Given** Neo4j is restarted after a degraded period
**When** the application detects Neo4j is back
**Then** failed writes from `failed_writes.jsonl` are replayed (Story 38.6)
**And** JSON fallback events are eventually synced to Neo4j (if sync mechanism exists)
**And** the `/health` endpoint returns to normal status

### Infrastructure Verification Checklist

- [ ] Deploy to clean environment (no pre-existing data)
- [ ] Exercise core learning flow end-to-end
- [ ] Kill and restart application, verify data survives
- [ ] Stop Neo4j, verify degradation behavior
- [ ] Restart Neo4j, verify recovery
- [ ] Send null/invalid inputs to review API, verify rejection
- [ ] Check logs for silent failures or swallowed errors
- [ ] Verify `/health` endpoint reflects actual system state
