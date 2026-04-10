---
title: Phase 1 Day 1 Spike Results
subtitle: Real-run L5 Evidence for Plan v23 v5 → Plan v24 feedback
date: 2026-04-09
spike-1-status: COMPLETE-WITH-FINDINGS
spike-2-status: CONFIRMED (matches Plan v23 Stage 1)
spike-3-status: RELOCATED-TO-CS188-VAULT-PENDING-REAL-SESSION-TEST
l5-findings-count: 8
recorded-by: Plan v24 Part B + Part C execution
feeds-into: Plan v25 (Phase 1 §10.1 task 1-7 kickoff · Part C2 spec)
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
| **3 · UserPromptSubmit hook** | RELOCATED TO CS188 VAULT · REAL-SESSION TEST PENDING | 2 | Initially mis-installed to global `~/.claude/` · Part C1 relocated to vault-scoped `CS188/.claude/` per PRD §4.7.4 L4663-4665 · scope-isolation dry-run confirmed |

**Total L5 findings discovered**: **8** (detailed in Section 4).

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

### Relocation Event (Plan v24 Part C1 · 2026-04-09 post-Spike3)

**Why**: User review of Spike 3 setup revealed a critical scope violation — I had installed the UserPromptSubmit hook into **global** `~/.claude/settings.json`, causing it to trigger for **every** Claude Code session across all projects. PRD §4.7.4 Step 5 L4663-4665 clearly specified the hook must live in `<vault_root>/.claude/`.

**What was relocated** (6 atomic actions):

1. **Rolled back global `settings.json`**:
   ```
   cp ~/.claude/settings.json.bak.spike3-2026-04-09 ~/.claude/settings.json
   md5 verified: f4ed678015fe4620c4768b2a4fbbd534 (both identical)
   jq '.hooks.UserPromptSubmit // "absent"' → "absent"
   ```

2. **Created vault hooks directory**:
   ```
   mkdir -p "/Users/Heishing/Desktop/spring course 2026/CS188/.claude/hooks"
   ```

3. **Copied hook script to vault**:
   ```
   cp ~/.claude/user-prompt-hook.sh CS188/.claude/hooks/user-prompt-hook.sh
   chmod +x ...
   ```

4. **Refactored script for vault-scoped logging**:
   - Header comments updated (relocation notice + PRD §4.7.4 reference)
   - Log path changed from `~/.claude/user-prompt-history.log` to `${CLAUDE_PROJECT_DIR:-$HOME}/.claude/user-prompt-history.log`
   - Fallback to `$HOME` ensures script works even if Claude Code doesn't inject `CLAUDE_PROJECT_DIR` (defensive)

5. **Created vault `settings.json`** (NEW file, separate from existing `settings.local.json`):
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [{
         "hooks": [{
           "type": "command",
           "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/user-prompt-hook.sh",
           "timeout": 5
         }]
       }]
     }
   }
   ```
   - Why separate from `settings.local.json`: PRD §4.7.4 Step 5 L4691-4716 uses `settings.json` (non-local) for hooks · `settings.local.json` already holds user permissions + outputStyle · Claude Code merges both files automatically

6. **Scope-isolation dry-run**:
   ```
   (export CLAUDE_PROJECT_DIR="/Users/Heishing/Desktop/spring course 2026/CS188"; \
    echo '{"session_id":"c1-relocation-test-001","cwd":"...","prompt":"Part C1 relocation dry-run 2026-04-09"}' | \
    bash "$CLAUDE_PROJECT_DIR/.claude/hooks/user-prompt-hook.sh")
   exit=0
   ```
   - Verified: new line in `CS188/.claude/user-prompt-history.log` · session `c1-relocation-test-001`
   - Verified: `~/.claude/user-prompt-history.log` tail is UNCHANGED (still `61a11f9b-...` from pre-rollback period)
   - **Scope isolation confirmed at runtime**

**L5 finding**: registered as L5-#8 (see registry below).

### Real-Session Verification · PENDING USER ACTION (post-relocation)

The current Claude Code session loaded `settings.json` at start — hook edits do not hot-reload. **User must verify in a fresh session with CWD inside the CS188 vault**:

1. **Open a NEW Claude Code session with CWD = CS188 vault** (critical):
   ```
   cd "/Users/Heishing/Desktop/spring course 2026/CS188" && claude
   ```
   (alternatively: open Claudian plugin tab in Obsidian pointed at the CS188 vault)
2. Type any prompt (e.g., `test cs188 hook relocation 2026-04-09`)
3. After prompt submission, run in a terminal:
   ```
   tail -5 "/Users/Heishing/Desktop/spring course 2026/CS188/.claude/user-prompt-history.log"
   ```
4. **Expected** (all must match):
   - New line with current UTC timestamp
   - `session=` is a **real UUID** (not `no-session` · not `c1-relocation-test-*`)
   - `cwd=` contains `/Users/Heishing/Desktop/spring course 2026/CS188`
   - `prompt=` contains `test cs188 hook relocation`
5. **Also verify scope isolation** (critical):
   ```
   tail -1 ~/.claude/user-prompt-history.log
   ```
   Should NOT contain the new session_id (proves vault-scoped hook did NOT pollute global log).

**Failure modes**:
- No new line: run `jq empty CS188/.claude/settings.json` to check JSON format · or Claude Code may not support UserPromptSubmit in current version (record as L5-#9 fallback)
- CWD ≠ CS188: hook will not trigger at all · user must verify CWD before testing (use `pwd` in terminal after `cd`)

### Rollback History + Future Rollback

**Global rollback already completed (Plan v24 Part C1)**:
```bash
# 2026-04-09: Plan v24 Part C1 rolled back global settings.json (scope violation fix)
cp ~/.claude/settings.json.bak.spike3-2026-04-09 ~/.claude/settings.json
# md5 verified: f4ed678015fe4620c4768b2a4fbbd534 (both files identical post-rollback)
# Note: source hook script ~/.claude/user-prompt-hook.sh kept for reference · no longer referenced by any settings.json
```

**Future vault rollback (if CS188 hook misbehaves)**:
```bash
# Delete vault hook files (safe — no global impact on other projects)
mv "/Users/Heishing/Desktop/spring course 2026/CS188/.claude/hooks/user-prompt-hook.sh" /tmp/
mv "/Users/Heishing/Desktop/spring course 2026/CS188/.claude/settings.json" /tmp/
# Note: CS188/.claude/settings.local.json is preserved (user permissions + outputStyle · unaffected)
```

---

## L5 Findings Registry

Collected during Plan v24 Part B execution · 2026-04-09.

### L5-#1 · ✅ FIXED in 990e958 · Graphiti background task exception bypasses lifespan try/except

**Status**: ✅ **FIXED** in commit `990e958` (2026-04-09 · Plan v25 Option C)
**Original severity**: Critical · silent degradation

**Location**: `backend/app/main.py` L266-285 (lifespan Phase 2 block) + graphiti-core `Neo4jDriver.build_indices_and_constraints()`

**Evidence**:
```
{"event": "Task exception was never retrieved\nfuture: <Task finished
name='Task-11' coro=<Neo4jDriver.build_indices_and_constraints() done, ...
exception=ServiceUnavailable(...)>", "logger": "asyncio", "level": "error",
"timestamp": "2026-04-09T21:12:11.923878Z"}
```

**Real root cause** (PRD assumption was wrong — verified by 4 independent agents):

The leak does **NOT** originate from our `episode_worker.initialize_graphiti()`. It originates from **graphiti-core v0.28.2 library internals** at `backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/neo4j_driver.py:91-101`:

```python
def __init__(self, uri, user, password, database='neo4j'):
    self.client = AsyncGraphDatabase.driver(uri=uri, auth=(user or '', password or ''))
    # ...
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(self.build_indices_and_constraints())  # L98 LEAKED
    except RuntimeError:
        pass
```

The task reference is never stored, no done-callback is attached, no exception handler wraps it. Our own `await self._graphiti.build_indices_and_constraints()` at episode_worker.py L338 is actually the **second** call — the leaked task already fired the moment `Graphiti(...)` returned.

**Impact (pre-fix)**:
- Backend appears to "start successfully" (port 8000 LISTEN)
- Graphiti subsystem completely broken
- Background retry loop never terminates · spams stderr every 1-3 seconds with `ServiceUnavailable`
- Each retry consumes CPU + opens TCP connections to non-existent Neo4j

**Fix applied** (commit `990e958`):

Pre-flight Neo4j connectivity probe with a bare `neo4j.AsyncGraphDatabase.driver` **before** instantiating `Graphiti(...)`. If the probe fails, we never construct Graphiti — so the leaked task at L98 is never scheduled. Code change: ~70 lines added at the head of `GraphitiEpisodeWorker.initialize_graphiti` in `backend/app/services/episode_worker.py`.

**Why other approaches were rejected**:
- Awaiting `build_indices_and_constraints` inside our try block → too late, task already fired
- `asyncio.set_exception_handler` → fragile, only suppresses, doesn't fix
- Patching graphiti-core → pinned 0.28.2, not in our source tree

**Tests**: `backend/tests/test_episode_worker_preflight.py` (2 cases · ServiceUnavailable + Timeout · monkeypatch self-contained · 5.39s wall clock)

### L5-#2 · ✅ FIXED in 1f170a6 · `/api/v1/health` endpoint false-positive on Neo4j

**Status**: ✅ **FIXED** in commit `1f170a6` (2026-04-09 · Plan v25 Option C)
**Original severity**: Critical · operational
**Location**: `backend/app/api/v1/endpoints/health.py:133-156` (pre-fix) · `L133-168` (post-fix, 4-way mode-aware)

**Evidence**: Health endpoint responded with `{"status":"healthy","components":{"neo4j":"ok"}}` at 21:12:47 · but lifespan log showed Neo4j connection failed and MemoryService was in JSON fallback mode.

**Real root cause** (PRD assumption was wrong — verified by 4 independent agents):

The endpoint **already had** a `RETURN 1 AS ping` check (not missing). The bug was that the ping dispatched through `Neo4jClient.run_query` which auto-fell-back to `_run_query_json_fallback` (backend/app/clients/neo4j_client.py:450-452). The JSON fallback parser **no-ops silently** on simple queries instead of raising, so `ping` "succeeded" and the endpoint reported `"ok"`.

**False-positive chain**:
1. `Neo4jClient` initializes with `use_json_fallback=False`, retries 3x, fails
2. Auto-fallback triggers → `_use_json_fallback = True`, `stats.mode = "JSON_FALLBACK"`, but `initialized` stays `True`
3. Health endpoint checks `stats["initialized"]` only (not `mode`) → enters ping branch
4. `run_query("RETURN 1 AS ping")` → dispatched to `_run_query_json_fallback` → returns empty list (no raise)
5. `components["neo4j"] = "ok"` ← false-positive

**Fix applied** (commit `1f170a6`):

Mirror the production 4-way classification from `backend/app/services/memory_service.py:969-987` (Story 30.3 fix). Now treats `stats["mode"] == "NEO4J" AND health_status == True` as real-healthy; `JSON_FALLBACK` is reported as `"json_fallback"` (operational, not error); otherwise `"degraded"` or `"not_initialized"`. HTTP stays 200 at top level because the Tauri desktop sidecar should still operate in JSON fallback.

**Why other approaches were rejected**:
- Let fallback raise on simple queries → breaks "silent degrade" contract for 6+ consumers
- Let fallback set `initialized=False` → breaks 6 invariants in memory_service.py and health.py (L223/1113/1250/1546/1742/996)
- K8s readiness/liveness split → Canvas is Tauri desktop, not K8s

**Tests**: `backend/tests/test_health.py::TestHealthCheckNeo4jFallback` (4 cases · NEO4J ok / NEO4J ping-fail / JSON_FALLBACK / not_initialized · monkeypatch self-contained)

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

### L5-#8 · CRITICAL · Spike 3 UserPromptSubmit hook scope misplacement (global vs vault)

**Severity**: Critical · architectural scope violation

**Discovered during**: User review of Spike 3 setup (2026-04-09) · fixed in Plan v24 Part C1 same day

**Evidence**:
- During Spike 3 Setup Actions, I wrote the UserPromptSubmit hook to `~/.claude/settings.json` (global · all projects · all sessions)
- PRD §4.7.4 Step 5 L4663-4665 explicitly states: `# Hook 配置在 vault 根目录 / cd /path/to/your/canvas-vault / ls -la .claude/`
- Correct location: `<vault_root>/.claude/settings.json` · where `vault_root = CANVAS_BASE_PATH` env var `= /Users/Heishing/Desktop/spring course 2026/CS188` (confirmed from `backend/.env` L? and `docker-compose.yml` L162-163)
- Impact: hook would have triggered in **every** Claude Code session across all projects (cs61b, canvas-learning-system dev, any future vault) · not just Canvas Learning System CS188 vault sessions · polluting `~/.claude/user-prompt-history.log` with non-Canvas prompts

**Root cause**:
- During Spike 3, I read PRD §7.6.5 ("UserPromptSubmit hook is a Desktop-layer mechanism, not backend/sidecar") and concluded "Desktop-layer means install globally to `~/.claude/settings.json`"
- I did NOT cross-reference PRD §4.7.4 Step 5 which scopes "Desktop-layer" to mean "vault-scoped Desktop settings" (the `.claude/` directory *inside* the vault root, which Claude Code Desktop reads when CWD matches)
- **Reading §7.6.5 alone gave the wrong scope conclusion** · §7.6.5 + §4.7.4 must be read together

**Fix applied (Plan v24 Part C1 · 2026-04-09)**:
1. Rolled back `~/.claude/settings.json` from `settings.json.bak.spike3-2026-04-09` (md5 verified identical post-rollback)
2. Created `CS188/.claude/hooks/user-prompt-hook.sh` (copy of source script · log path refactored to `${CLAUDE_PROJECT_DIR:-$HOME}/.claude/user-prompt-history.log`)
3. Created `CS188/.claude/settings.json` with only the `hooks.UserPromptSubmit` block · kept separate from pre-existing `settings.local.json` (which holds user permissions + `outputStyle: "Learning"`) · both files merged by Claude Code
4. Dry-run verified scope isolation: log written to `CS188/.claude/user-prompt-history.log` (c1-relocation-test-001) · `~/.claude/user-prompt-history.log` remains UNPOLLUTED

**Lesson for future PRD-faithful implementation**:
- Never act on a single PRD section in isolation — cross-reference with neighboring sections that might modify scope
- When PRD mentions "Desktop level" or "global level", hunt for qualifiers in adjacent sections (`§4.7.4 Step 5` was the qualifier for `§7.6.5`)
- For config changes that could affect "all projects", default-deny and demand explicit PRD quote confirming global scope
- **Meta-lesson**: This L5 is itself evidence for PRD §1.5.9's four-layer nested errata pattern — L5 is "real-run discovery" · and Spike 3's own execution *created* a new L5 that couldn't have been caught by recursive review alone (only by user review of the setup actions)

---

## Decision Matrix

| Finding | Blocks Phase 1 §10.1 task 1-7? | Must fix before Phase 1? |
|---|---|---|
| L5-#1 Graphiti exception leak | No (Phase 1 does not start Graphiti subsystem by default) | ✅ **FIXED** in `990e958` (Plan v25 Option C) |
| L5-#2 Health false-positive | No | ✅ **FIXED** in `1f170a6` (Plan v25 Option C) |
| L5-#3 MCP log count 14 vs 15 | No | Trivial docstring fix |
| L5-#4 EventBus 8 vs 9 | No | PRD update |
| L5-#5 4 degraded subsystems | No | Out of scope |
| L5-#6 JSON fallback DDL warning | No | Suppress warning in future |
| L5-#7 `set -eu` hook hazard | No | Document in developer-guide |
| L5-#8 Hook scope misplacement (global vs vault) | **No (fixed in Part C1)** | **Already fixed** · add to errata-log for future reviewers |

**Verdict**: **Phase 1 §10.1 task 1-7 can proceed without blocking on L5 findings**. Register all 8 findings in 14-PRD v6 (or a dedicated `errata-log.md`) for future correction. L5-#1, L5-#2, and L5-#8 are now **all resolved** (L5-#1/#2 via Plan v25 Option C commits `1f170a6` + `990e958`). Remaining: L5-#3/#4/#5/#6/#7 documentation-only fixes.

---

## Next Steps

1. **Part A complete** (commit `208c26a` pushed to origin + backup)
2. **Part B Spike 1 complete with findings** (7 initial L5 findings)
3. **Part B Spike 2 confirmed** (matches Plan v23 Stage 1 ground truth)
4. **Part B Spike 3 initial setup → MISPLACED GLOBALLY** (discovered by user · see L5-#8)
5. **Part C1 complete** (rollback global + vault-scoped install + scope-isolation dry-run verified)
6. **Part C2 complete** (Obsidian deploy plugin spec written to `docs/scheme-a-planning/obsidian-deploy-plugin-spec.md`)
7. **Wait for user to verify Spike 3 in new Claude Code session with `CWD=CS188` vault** → report result
8. **Next plan (Plan v25)**: Phase 1 §10.1 task 1-7 (vault init / Claudian / skill set / minimal skill set) · will leverage Part C2 spec as the implementation target for the Obsidian deploy plugin

---

## Appendix · Raw Log Pointers

**Spike 1 artifacts**:
- Full Spike 1 backend log: `/tmp/canvas-spike1.log` (630 lines)
- uvicorn PID tracking: `/tmp/canvas-spike1.pid` (contains `uvicorn_pid=47449`)

**Spike 3 artifacts (pre-Part C1 · frozen)**:
- Pre-relocation hook log (dry-run only · frozen after Part C1): `~/.claude/user-prompt-history.log`
- Global settings.json backup (pre-Spike 3): `~/.claude/settings.json.bak.spike3-2026-04-09`
- Source hook script (kept for reference · no longer referenced): `~/.claude/user-prompt-hook.sh`

**Spike 3 artifacts (post-Part C1 · active)**:
- **Active hook script**: `/Users/Heishing/Desktop/spring course 2026/CS188/.claude/hooks/user-prompt-hook.sh`
- **Active vault settings.json**: `/Users/Heishing/Desktop/spring course 2026/CS188/.claude/settings.json`
- **Active hook log**: `/Users/Heishing/Desktop/spring course 2026/CS188/.claude/user-prompt-history.log`
- Pre-existing vault `.claude/settings.local.json` (user permissions + `outputStyle: "Learning"`): untouched by Part C1

## Cross-References

- 14-PRD v5 §7.6.1 · 13 services + 15 MCP tools claim (source for comparison)
- 14-PRD v5 §7.6.5 · UserPromptSubmit architectural clarification (confirmed by Spike 3)
- 14-PRD v5 §10.1 · Phase 1 task list (unblocked by this spike)
- 16-triangulated-review-report.md §1.5.9 · L5 inevitability defense (this doc is the L5 evidence)
- `docker-compose.yml` L31 · Neo4j port 7691 vs user's personal 7689 disambiguation
- `backend/.env` L11 · `NEO4J_URI=bolt://localhost:7691` (authoritative)
- `backend/app/main.py` L266-285 · lifespan Phase 2 block (L5-#1 location)
- `lefthook.yml` L123-128 · post-commit auto-push (Part A verified)
- **14-PRD v5 §4.7.4 Step 5 L4663-4665** · vault-root hook location — the PRD quote that proves L5-#8 scope violation
- **14-PRD v5 §4.7.4 Step 5 L4691-4716** · `settings.json` (non-local) naming convention · justifies Part C1 file separation from `settings.local.json`
- **`backend/.env` `CANVAS_BASE_PATH=/Users/Heishing/Desktop/spring course 2026/CS188`** · authoritative source proving CS188 is the active vault (Part C1 target)
- **`docker-compose.yml` L162-163** · `CANVAS_BASE_PATH` env passthrough to container · secondary confirmation
- **14-PRD v5 §1.5.9** · four-layer nested errata theory · Part C1 is a real-world L5 case that validates the theory (Spike 3 created its own L5 during execution · only user review + real-run could detect it)
- **`docs/scheme-a-planning/obsidian-deploy-plugin-spec.md`** (Part C2) · the spec document that will be implemented in Plan v25 to prevent future manual scope violations
- **Plan v25 Option C** (L5-#1 + L5-#2 fix) · commits `1f170a6` (health mode-aware) + `990e958` (episode_worker pre-flight) · 2026-04-09 · completes the remediation of both Critical findings discovered during Spike 1
- **`backend/app/services/memory_service.py:969-987`** · production pattern source for health.py 4-way Neo4j mode classification (Story 30.3 fix)
- **`backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/neo4j_driver.py:91-101`** · real root cause of L5-#1 fire-and-forget task leak (library internal, not our code)
