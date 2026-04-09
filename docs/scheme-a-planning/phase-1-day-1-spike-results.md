---
title: Phase 1 Day 1 Spike Results
subtitle: Real-run L5 Evidence for Plan v23 v5 → Plan v24 feedback
date: 2026-04-09
spike-1-status: COMPLETE-WITH-FINDINGS
spike-2-status: CONFIRMED (matches Plan v23 Stage 1)
spike-3-status: SETUP-COMPLETE-PENDING-REAL-SESSION-TEST
l5-findings-count: 7
recorded-by: Plan v24 Part B execution
feeds-into: Plan v25 (Phase 1 §10.1 task 1-7 kickoff)
---

# Phase 1 Day 1 Spike Results

> **Purpose**: Record real-run output from Spike 1/2/3 as L5 evidence.
> Plan v23 §7.6.5 locked "real-run > recursive review" philosophy.
> This document is the L5 feedback loop deliverable.

## Executive Summary

| Spike | Status | L5 Findings | Key Conclusion |
|---|---|---|---|
| **1 · Canvas backend 13 svc + 15 MCP** | COMPLETE WITH L5 FINDINGS | 5 | Backend boots in degraded mode · **15/15 MCP tools confirmed** · but Graphiti background task exception bypasses lifespan try/except · health check false-positive |
| **2 · canvas_agentic_rag import** | CONFIRMED | 0 new | `LANGGRAPH_AVAILABLE=True ERROR=None` · matches Plan v23 Stage 1 ground truth |
| **3 · UserPromptSubmit hook** | SETUP-COMPLETE · REAL-SESSION TEST PENDING | 1 | Dry-run all 5 edge cases passed · user must verify in new Claude Code session |

**Total L5 findings discovered**: **7** (detailed in Section 4).

**Decision point**: Spikes do NOT block Phase 1 §10.1 task 1-7 (vault init / Claudian / skill set). L5 findings feed into future erratum correction in 14-PRD v6.

---

## Environment Snapshot (Pre-Spike)

| Component | State | Version/Value |
|---|---|---|
| Python | Running | 3.14.3 (uvicorn venv) |
| uvicorn | Installed | 0.42.0 |
| Pydantic | Installed | 2.11 (with V1 compat shim) |
| Ollama | Running natively | PID 38478 on port 11434 |
| Docker daemon | Not running | Docker Desktop closed |
| Neo4j (port 7687) | Not listening | default bolt port empty |
| Neo4j (port 7689) | Not listening | user personal Graphiti (`~/.claude/CLAUDE.md` refers) empty |
| Neo4j (port 7691) | Not listening | Canvas backend target (from `docker-compose.yml` + `backend/.env`) empty |
| Canvas backend | Not running | port 8000 empty |
| `GOOGLE_API_KEY` | Set in `.env` | Both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set (backend defaults to GOOGLE) |

**Strategic choice**: run Spike 1 in **degraded mode** (no Neo4j) rather than starting Docker. This is explicitly the L5 discovery vector — "what happens when the backend can't reach Neo4j on startup?"

---

## Spike 1 · Canvas Backend 13 Services + 15 MCP Tools

### Command

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && \
  nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info \
    > /tmp/canvas-spike1.log 2>&1 &
```

### Startup Timeline

| Time (UTC) | Event |
|---|---|
| 21:10:33 | uvicorn process started (PID 47449) |
| 21:10:34.166 | Agentic RAG module loaded · **LANGGRAPH_AVAILABLE=True** |
| 21:10:34.415 | `[MCP] Patched fastapi-mcp anyOf+type schema conflict (v0.4.0 bug)` |
| 21:10:34.428 | **`[Story 3.2] Registered 14 MCP tool routes (incl. F2 search_notes)`** — see L5-#3 |
| 21:10:34.711 | `[MCP] Stripped spurious 'type' from 112 anyOf properties across 175 tools` |
| 21:10:34.712 | `MCP SSE server listening at /mcp` |
| 21:10:34.713 | `Starting Canvas Learning System API v1.0.0` (lifespan begins) |
| 21:10:34.722 | Neo4jClient: `mode=NEO4J, uri=bolt://localhost:7691, pool_size=50` |
| 21:10:34.722 | **Neo4j connection failed to `localhost:7691`** (expected — no server) |
| 21:10:34.723 | **`Falling back to JSON storage mode`** — MemoryService graceful degrade |
| 21:10:34.723 | `Loaded 36 relationships from backend/data/neo4j_memory.json` |
| 21:10:34.723 | `MemoryService recovered 36 episodes · initialized successfully` |
| 21:10:34.724 | EventBus registered **8** production handlers (SCORE/BKT/FSRS/MASTERY/CALIBRATION/MEMORY_WRITE/RAG_WEIGHT/UI_MASTERY) |
| 21:10:34.725 | Signal registry initialized with **5** adapters (bkt_mastery, fsrs_retrievability, exam_score_avg, calibration_bias, self_confidence_avg) |
| 21:10:34.726 | `Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY` |
| 21:10:34.766 → 21:12:11 | **Graphiti `build_indices_and_constraints()` background task** infinite retry loop against Neo4j |
| 21:12:11.923 | **`Task exception was never retrieved`** — `ServiceUnavailable` leaked as unhandled asyncio exception |
| (unknown) | lifespan returns · **port 8000 starts LISTENING** |
| 21:12:47 | `/api/v1/health` responds `{"status":"healthy","components":{"neo4j":"ok"}}` — **health lies** |
| 21:13:38 | SIGTERM received · graceful shutdown completed in ~1s |

**Total lifespan time before port 8000 listen**: ~100+ seconds (dominated by Graphiti Neo4j retry backoff).

### 13 Services Status Matrix

| # | Service | PRD §7.6.1 Claim | Real-Run Actual | Delta |
|---|---|---|---|---|
| 1 | RAGService / Agentic RAG | Initialized | `LANGGRAPH_AVAILABLE=True` · 7 prompts loaded | Match |
| 2 | MCP Tool Registry | 15 tools | **15 tools exposed at `/mcp/tools/*`** (log msg says 14 but openapi.json says 15 — see L5-#3) | Match (15) |
| 3 | ResourceMonitor | Initialized (5s interval) | `thresholds` set · background loop started | Match |
| 4 | AlertManager | Initialized (30s interval) | `0 rules loaded` (empty `config/alerts.yaml`) · started | Match |
| 5 | PromptRegistry | Initialized | 7 templates loaded: `autoscore / context_extract / crag_grading / query_optimize / query_rewrite / question_gen / search_intent` | Match |
| 6 | CostTracker + LLM Call Logger | Initialized | SQLite at `backend/data/llm_call_logs.db` · LiteLLM callback registered | Match |
| 7 | MemoryService | Initialized (singleton) | **JSON fallback mode** · Neo4j unavailable · recovered 36 episodes | Degraded but functional |
| 8 | LanceDB Index Service | Initialized | `No pending LanceDB index operations` | Match |
| 9 | Archive Scheduler | Initialized (24h interval) | Started | Match |
| 10 | EventBus + handlers | Initialized | **8 handlers** registered · (PRD §7.6.1 implies 9 · off-by-one · see L5-#4) | Degraded count |
| 11 | Mastery Engine + SignalRegistry + FusionEngine | Initialized | 5 adapters registered | Match |
| 12 | GraphitiEpisodeWorker | Initialized | **Background task exception leaked** · not caught by lifespan try/except | L5-#1 **critical** |
| 13 | (implied) Overall lifespan completion | Health check ok | **`"neo4j":"ok"` is a lie** — health endpoint does not reflect actual Neo4j state | L5-#2 **critical** |

**Services initialized**: 11 full + 1 degraded (MemoryService) + 1 broken (Graphiti) = **13** (matches PRD count, but one is silently broken).

### 15 MCP Tools Verification

**Query**: `curl -s http://localhost:8000/api/v1/openapi.json | jq '.paths | to_entries | map(select(.key | startswith("/mcp/tools/"))) | length'`

**Result**: `15`

**Full list** (alphabetical):
```
archive_conversation  assemble_acp            create_exam_node
generate_question     query_mastery           record_calibration
record_error          record_learning_memory  request_hint
score_answer          search_memories         search_notes
skip_question         update_bkt              update_fsrs
```

**All 15 tools match PRD §7.6.1 expected list**.

### Spike 1 Shutdown

- SIGTERM sent via `kill <PID>` (avoiding `kill -9` blocked by guard-hook)
- Shutdown sequence completed gracefully in ~1s:
  - alert_manager.stopped
  - resource_monitor.stopped
  - LanceDB index service cleaned up
  - LLM Call Logger stopped · CostTracker stopped
  - archive scheduler stopped
  - GraphitiEpisodeWorker stopped
  - MemoryService singleton cleaned up
  - `Application shutdown complete` · port 8000 released

**Log file**: `/tmp/canvas-spike1.log` · 630 lines total.

---

## Spike 2 · canvas_agentic_rag Import Re-Verification

### Command

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && \
  .venv/bin/python -c "from app.services.rag_service import LANGGRAPH_AVAILABLE, _IMPORT_ERROR; \
    print('SPIKE_2_RESULT:', 'LANGGRAPH_AVAILABLE=', LANGGRAPH_AVAILABLE, 'ERROR=', _IMPORT_ERROR)"
```

### Output

```
2026-04-09 14:13:42 [debug    ] RAGService: Added .../backend/lib to sys.path
[langchain_core Pydantic V1/Python 3.14 warning · non-blocking]
[jieba pkg_resources warning · non-blocking]
Building prefix dict from the default dictionary ...
Loading model from cache /var/folders/.../jieba.cache
Loading model cost 0.229 seconds.
Prefix dict has been built successfully.
2026-04-09 14:13:45 [info     ] RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True
SPIKE_2_RESULT: LANGGRAPH_AVAILABLE= True ERROR= None
```

### Conclusion

**Matches Plan v23 Stage 1 ground truth exactly**:
- `LANGGRAPH_AVAILABLE=True`
- `_IMPORT_ERROR=None`
- Pydantic V1 warning persistent but non-blocking
- jieba `pkg_resources` warning persistent but non-blocking
- `sys.path` injection at `backend/lib/` works (Plan v23 L32-37 fix still in place)

**No new L5 findings** · Plan v23 Stage 1 baseline holds.

---

## Spike 3 · UserPromptSubmit Hook Configuration + Test

### Architecture Clarification

**PRD §7.6.5 erratum confirmation**: UserPromptSubmit hook lives in **Claude Code Desktop's `~/.claude/settings.json`** · NOT in Canvas backend / Obsidian plugin / sidecar. This was the L3 architectural misjudgment from earlier PRD iterations.

### Setup Actions

1. **Backup existing settings.json**:
   ```
   cp ~/.claude/settings.json ~/.claude/settings.json.bak.spike3-2026-04-09
   md5: f4ed678015fe4620c4768b2a4fbbd534 (pre-edit)
   ```

2. **Write hook script** at `~/.claude/user-prompt-hook.sh`:
   - Reads JSON from stdin (Claude Code hook protocol)
   - Appends `[TS, session_id, cwd, prompt_preview]` to `~/.claude/user-prompt-history.log`
   - **Never exits non-zero** (every jq call guarded with `|| true`)
   - `chmod +x` applied

3. **Add UserPromptSubmit entry** to `~/.claude/settings.json`:
   ```json
   "UserPromptSubmit": [
     {
       "hooks": [
         {
           "type": "command",
           "command": "bash ~/.claude/user-prompt-hook.sh",
           "timeout": 5
         }
       ]
     }
   ]
   ```

4. **Validate JSON**: `jq empty ~/.claude/settings.json` → OK · 4 hook types now configured: Notification, PreToolUse, Stop, **UserPromptSubmit**.

### Edge Case Dry-Run Tests (within current session)

| # | Test | Expected | Result |
|---|---|---|---|
| 1 | Empty stdin | exit 0 | exit=0 |
| 2 | Malformed JSON (`not json{{{`) | exit 0 | **initially exit=5** → fixed (see L5-#7) → exit=0 |
| 3 | Missing fields `{"unrelated":"value"}` | exit 0 · use defaults | exit=0 |
| 4 | Special chars (quotes, $dollar, backticks) | exit 0 · chars sanitized | exit=0 |
| 5 | Valid full input | exit 0 · log line written | exit=0 |

### Bug Fix: `set -eu` Hazard

**Initial script**: had `set -eu` at top → jq on malformed JSON exited non-zero → `set -e` killed script with exit 5 → **Claude Code would have interpreted as "hook failed, block prompt"** → session broken.

**Fix applied**: Removed `set -eu` · wrapped every jq call with `|| true` · exit 0 guaranteed.

**Lesson for future hooks** (see L5-#7): Never use `set -eu` in Claude Code hook scripts. Silent failures > loud crashes for non-blocking hooks.

### Real-Session Verification · PENDING USER ACTION

The current Claude Code session loaded `settings.json` at start — hook edits do not hot-reload. **User must verify in a fresh session**:

1. **Open a NEW Claude Code session** (Ctrl+N or new window)
2. Type any prompt (e.g., "hello")
3. After prompt submission, run in a terminal:
   ```
   tail -5 ~/.claude/user-prompt-history.log
   ```
4. **Expected**: new line with current UTC timestamp · session_id matching the new session · prompt preview containing "hello"

### Rollback Plan (if hook misbehaves)

```bash
cp ~/.claude/settings.json.bak.spike3-2026-04-09 ~/.claude/settings.json
# (hook script ~/.claude/user-prompt-hook.sh can remain · it only runs if settings.json references it)
```

---

## L5 Findings Registry

Collected during Plan v24 Part B execution · 2026-04-09.

### L5-#1 · CRITICAL · Graphiti background task exception bypasses lifespan try/except

**Severity**: Critical · silent degradation

**Location**: `backend/app/main.py` L266-285 (lifespan Phase 2 block) + graphiti-core `Neo4jDriver.build_indices_and_constraints()`

**Evidence**:
```
{"event": "Task exception was never retrieved\nfuture: <Task finished
name='Task-11' coro=<Neo4jDriver.build_indices_and_constraints() done, ...
exception=ServiceUnavailable(...)>", "logger": "asyncio", "level": "error",
"timestamp": "2026-04-09T21:12:11.923878Z"}
```

**Root cause**: `episode_worker.initialize_graphiti()` schedules `build_indices_and_constraints` as a fire-and-forget async task. The task's `ServiceUnavailable` exception is never awaited · so the lifespan try/except block at L283-285 never sees it · exception leaks as "unhandled asyncio task exception".

**Impact**:
- Backend appears to "start successfully" (port 8000 LISTEN)
- But Graphiti subsystem is completely broken
- Background retry loop **never terminates** · spams log every ~1-3 seconds with Neo4j connection errors
- Each retry consumes CPU + opens TCP connections to non-existent Neo4j

**Fix recommendation** (for Phase 1 §10.1):
- `episode_worker.initialize_graphiti` should await `build_indices_and_constraints` inside the try block
- OR register an `asyncio.Task.add_done_callback` that catches the exception and sets `app.state.episode_worker = None`
- OR add startup timeout with fallback

### L5-#2 · CRITICAL · `/api/v1/health` endpoint false-positive on Neo4j

**Severity**: Critical · operational

**Location**: `backend/app/api/v1/endpoints/health.py` (or equivalent)

**Evidence**: Health endpoint responds with `{"status":"healthy","components":{"neo4j":"ok"}}` at 21:12:47 · but we KNOW from lifespan log that Neo4j connection failed and MemoryService is in JSON fallback mode.

**Root cause** (needs investigation): the health check may be reading `app.state.memory_service` which exists (even if in degraded mode) and reporting ok. OR it is checking `NEO4J_ENABLED` env flag rather than actual connectivity.

**Impact**:
- Monitoring / oncall dashboards will show false-green
- Docker compose healthcheck (`curl -sf http://localhost:8001/api/v1/health`) would say healthy when backend is actually broken
- **Phase 1 pre-verification cannot rely on `/health` as oracle**

**Fix recommendation**: Health endpoint should actively ping Neo4j with a lightweight query (e.g., `RETURN 1`) and emit `neo4j: degraded` if it fails.

### L5-#3 · MEDIUM · MCP tool count log/reality mismatch

**Severity**: Medium · documentation inconsistency

**Location**: `backend/app/mcp/server.py` near the log statement `[Story 3.2] Registered 14 MCP tool routes (incl. F2 search_notes)`

**Evidence**:
- Log says: `14 MCP tool routes`
- openapi.json exposes: `15 paths under /mcp/tools/`
- PRD §7.6.1 expected: `15 tools`

**Root cause** (best guess): literal `14` baked into log message · missed update when `search_notes` (or another tool) was added.

**Impact**: minor · PRD operators comparing log count vs reality will doubt correctness.

**Fix recommendation**: Replace log `f"Registered 14 MCP tool routes"` with dynamic `f"Registered {len(registered_tools)} MCP tool routes"`.

### L5-#4 · MEDIUM · EventBus handler count off-by-one

**Severity**: Medium · documentation drift

**Location**: `backend/app/services/event_handlers.py` near `register_all_handlers`

**Evidence**:
- Log says: `registered 8 production handlers (SCORE_SUBMITTED, BKT_UPDATED, FSRS_UPDATED, MASTERY_CHANGED, CALIBRATION_RECORDED, MEMORY_WRITE_REQUESTED, RAG_WEIGHT_ADJUST, UI_MASTERY_PUSH)`
- PRD / various docs imply **9** handlers (pending · needs triangulation with Story 5.7 archive)

**Root cause**: PRD may have over-counted OR one handler was removed without PRD update.

**Fix recommendation**: Audit event_handlers.py vs PRD §7.6.1 text · align.

### L5-#5 · MEDIUM · 4 "not available" subsystems on startup

**Severity**: Medium · feature gaps

**Evidence from lifespan log**:
```
"cohere not installed. Cohere API reranking unavailable."
"EbbinghausReviewScheduler not available: No module named 'ebbinghaus_review'"
"AgentService not available, canvas uses template questions only"
"src.rollback not available — rollback endpoints respond with 503"
```

**Impact**:
- **Cohere reranking**: Agentic RAG degrades to local reranking only (BGE-M3 or similar)
- **EbbinghausReviewScheduler**: review scheduling may fall back to simple FSRS
- **AgentService**: canvas uses template questions (no AI-generated questions)
- **src.rollback**: `/rollback/*` endpoints respond with 503

**Relevance to Phase 1**: None of these subsystems are required for Phase 1 §10.1 task 1-7 (vault init / Claudian / skill set). Deferred.

### L5-#6 · LOW · Neo4j JSON fallback mode "Unhandled query pattern" for FULLTEXT INDEX

**Severity**: Low · known limitation of fallback mode

**Evidence**:
```
"Unhandled query pattern: CREATE FULLTEXT INDEX episode_content IF NOT EXISTS
 FOR (n:EpisodicNode) ON EACH [n.content]"
```

**Root cause**: The JSON fallback mode (`Neo4jClient` with `mode=JSON`) implements a subset of Cypher · does not support DDL statements like `CREATE FULLTEXT INDEX`.

**Impact**: Without Neo4j running, full-text search over episodic memory is unavailable. Keyword search in `search_memories` MCP tool may yield degraded results.

**Fix recommendation**: Either (a) JSON fallback should silently skip DDL, (b) warning message should be suppressed when intentional DDL is attempted, or (c) document this as expected behavior.

### L5-#7 · MEDIUM · `set -eu` hazard in Claude Code hook scripts

**Severity**: Medium · developer foot-gun

**Discovered during**: Spike 3 hook script development

**Evidence**: Initial hook script with `set -eu` at top exited with code 5 on malformed JSON input (due to jq failure propagating through `set -e`).

**Impact**: Claude Code interprets non-zero hook exit as "hook failed · block prompt" → session broken.

**Fix applied**: Removed `set -eu` · wrapped every jq call with `|| true` · exit 0 guaranteed regardless of input.

**Lesson for future hooks**: Document this in Phase 1 §10.1 `developer-guide.md` when skill set includes hook scripts.

---

## Decision Matrix

| Finding | Blocks Phase 1 §10.1 task 1-7? | Must fix before Phase 1? |
|---|---|---|
| L5-#1 Graphiti exception leak | No (Phase 1 does not start Graphiti subsystem by default) | Deferred to Phase 2 |
| L5-#2 Health false-positive | No | Deferred — note for monitoring setup |
| L5-#3 MCP log count 14 vs 15 | No | Trivial docstring fix |
| L5-#4 EventBus 8 vs 9 | No | PRD update |
| L5-#5 4 degraded subsystems | No | Out of scope |
| L5-#6 JSON fallback DDL warning | No | Suppress warning in future |
| L5-#7 `set -eu` hook hazard | No | Document in developer-guide |

**Verdict**: **Phase 1 §10.1 task 1-7 can proceed without blocking on L5 findings**. Register all 7 findings in 14-PRD v6 (or a dedicated `errata-log.md`) for future correction.

---

## Next Steps

1. **Part A complete** (commit `208c26a` pushed to origin + backup)
2. **Part B Spike 1 complete with findings**
3. **Part B Spike 2 confirmed**
4. **Part B Spike 3 setup complete · awaiting user real-session verification**
5. **Wait for user to verify Spike 3 in new Claude Code session** → report result
6. **Next plan (Plan v25)**: Phase 1 §10.1 task 1-7 (vault init / Claudian / skill set / minimal skill set)

---

## Appendix · Raw Log Pointers

- Full Spike 1 backend log: `/tmp/canvas-spike1.log` (630 lines)
- uvicorn PID tracking: `/tmp/canvas-spike1.pid` (contains `uvicorn_pid=47449`)
- User prompt history (Spike 3 dry-run + future real-session): `~/.claude/user-prompt-history.log`
- settings.json backup: `~/.claude/settings.json.bak.spike3-2026-04-09`
- hook script: `~/.claude/user-prompt-hook.sh`

## Cross-References

- 14-PRD v5 §7.6.1 · 13 services + 15 MCP tools claim (source for comparison)
- 14-PRD v5 §7.6.5 · UserPromptSubmit architectural clarification (confirmed by Spike 3)
- 14-PRD v5 §10.1 · Phase 1 task list (unblocked by this spike)
- 16-triangulated-review-report.md §1.5.9 · L5 inevitability defense (this doc is the L5 evidence)
- `docker-compose.yml` L31 · Neo4j port 7691 vs user's personal 7689 disambiguation
- `backend/.env` L11 · `NEO4J_URI=bolt://localhost:7691` (authoritative)
- `backend/app/main.py` L266-285 · lifespan Phase 2 block (L5-#1 location)
- `lefthook.yml` L123-128 · post-commit auto-push (Part A verified)
