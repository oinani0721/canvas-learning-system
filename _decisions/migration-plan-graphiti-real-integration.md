# Migration Plan: Graphiti Real Integration

> **Date**: 2026-03-24 | **Status**: PLAN | **Prereq**: _decisions/research-asyncio-queue-graphiti-worker.md

## Architecture

BEFORE: API -> MemoryService -> Neo4j Cypher + JSON file dual-write + Neo4j EntityNode bridge
AFTER:  API -> MemoryService -> Neo4j Cypher (preserved) + GraphitiEpisodeWorker.enqueue() -> Graphiti add_episode

## Confirmed Decisions
- Strategy C: asyncio.Queue + single background Worker
- LLM: Gemini full stack (GeminiClient + GeminiEmbedder + GeminiRerankerClient)
- Neo4j: 7691 (learning, separate from dev-memory 7689)
- .env: NEO4J_URI 7688 -> 7691
- Docker: add GOOGLE_API_KEY env var

## Phase 0: Environment (NO code logic changes)
Entry: Decision confirmed | Exit: Neo4j 7691 connected, health OK | Rollback: revert .env

| Task | File | Details |
|------|------|---------|
| Fix NEO4J_URI | backend/.env | 7688 -> 7691 |
| Fix .env.example | backend/.env.example | 7688 -> 7691 |
| Add GOOGLE_API_KEY | docker-compose.yml | backend env section |
| Verify Neo4j health | manual | docker exec cypher-shell |
| Verify data intact | manual | record count query |

## Phase 1: Delete Dead Code (C5/C6/C7)
Entry: Phase 0 | Exit: Zero dead code, ruff passes | Rollback: git revert

| Task | Details |
|------|---------|
| Identify dead code | Grep for non-existent method calls |
| Delete dead functions | Remove bodies + orphan imports |
| Remove call sites | If any callers exist |
| Run ruff check | Lint clean |

## Phase 2: Build GraphitiEpisodeWorker (NEW file, no callers)
Entry: Phase 1, Neo4j OK, GOOGLE_API_KEY set | Exit: Worker starts/stops, metrics OK, queue=0 | Rollback: Delete file + revert

| Task | File | Details |
|------|------|---------|
| Create episode_worker.py | backend/app/services/episode_worker.py | EpisodeTask, WorkerMetrics, DeadLetterStore, Worker |
| Init Graphiti client | episode_worker.py | graphiti_core.Graphiti + Gemini LLM |
| Wire lifespan startup | backend/app/main.py | await worker.start() |
| Wire lifespan shutdown | backend/app/main.py | await cleanup_episode_worker() |
| Monitoring endpoint | monitoring.py | GET /api/v1/monitoring/episode-worker |
| Config additions | backend/app/config.py | Queue maxsize etc |
| Verify dependency | requirements.txt | graphiti-core>=0.5 |
| Lint + tests | All modified | ruff + pytest |

Risks: Init failure -> try/except degraded mode; Python<3.13 -> sentinel pattern
Parallel: 2.1-2.2 can parallel with 2.3-2.5

## Phase 3: Replace Fake Bridge Layer (critical swap)

### 3A: Add enqueue adapter to MemoryService
- _enqueue_episode() helper: builds EpisodeTask, calls worker.enqueue()
- Inject worker reference via __init__ or lazy singleton

### 3B: Swap record_learning_event() [3 locations]
| Location | Before | After |
|----------|--------|-------|
| memory_service.py:604-629 | asyncio.create_task json+bridge | _enqueue_episode() |
| memory_service.py:1270-1286 | asyncio.create_task bridge | _enqueue_episode() |
| memory_service.py:1545-1553 | asyncio.create_task json retry | _enqueue_episode() |

### 3C: Add enqueue to record_knowledge_entity()
13 callers -> 1 method. Add enqueue to method body. Callers UNCHANGED:
tips.py(1), memory.py(2), event_handlers.py(1), conversation_distiller.py(3),
conversation_archive.py(1), conversation_tools.py(2), error_tools.py(1), memory_tools.py(2)

### 3D: Delete replaced code
- _write_to_graphiti_json() at memory_service.py:305-384
- _write_to_graphiti_json_with_retry() at memory_service.py:386-504
- _bridge_to_claude_graphiti() at memory_service.py:637-674
- graphiti_bridge_service.py (entire file)
- get_graphiti_bridge import at memory_service.py:68
- LearningMemoryClient import at memory_service.py:54-58
- ENABLE_GRAPHITI_JSON_DUAL_WRITE checks in memory_service.py + main.py
- dead-letter/failure-counter imports at memory_service.py:69-73

### 3E: Verify
- ruff check backend/app/
- Grep deleted names -> zero refs
- POST learning event -> returns fast, event queued
- Worker metrics -> episodes_enqueued > 0
- Neo4j direct write still works

Entry: Phase 2 (worker running, empty queue)
Exit: All 18+ sites migrated, worker processing, Neo4j preserved, frontend unchanged
Rollback: git revert
Risks: Rate limit (backoff+dead-letter), 30s latency (maxsize=100), crash (try/except per episode)
Order: 3A -> (3B parallel 3C) -> 3D -> 3E

## Phase 4: Fake Naming Cleanup (42 occurrences)
Entry: Phase 3 stable | Exit: All refs accurate | Rollback: git revert

- Audit all "graphiti" refs in backend/app/
- Rename inaccurate ones (says Graphiti, means Neo4j or JSON)
- Update module docstrings
- Remove ENABLE_GRAPHITI_JSON_DUAL_WRITE from config + .env
- Run ruff + tests

## Phase 5: search_memories Layered Replacement
Entry: Phase 3 stable + enough episodes | Exit: Layered search <2s | Rollback: Revert to in-memory

- Add graphiti search to worker (episode_worker.py)
- Refactor search_memories(): Graphiti -> Neo4j fulltext -> in-memory
- Add Neo4j fulltext index
- Verify 25+ callers (NO signature change)
- Performance test

Callers: memory_tools.py, server.py, conversation_inheritance.py(2),
conversation_archive.py(2), archive_scheduler.py(1), learning_context_service.py(1),
context_enrichment_service.py(1), archive.py(1), tips.py(1), agent_service.py(1)

## Dependency Graph
Phase 0 -> 1 -> 2 -> 3 -> (4 parallel 5)
Within Phase 3: 3A -> (3B || 3C) -> 3D -> 3E

## Global Rollback
Gemini fails: Worker dead-letters events. Neo4j direct write NEVER removed. Fix creds -> replay.
Neo4j fails: Direct Cypher fails (existing). Restart -> replay.

| Phase | Rollback | Data Loss |
|-------|----------|-----------|
| 0 | 1-line .env | None |
| 1 | git revert | None |
| 2 | Delete file + revert | None |
| 3 | git revert | Dead-lettered preserved |
| 4 | git revert | None |
| 5 | Revert search | None |

## Estimated Effort
| Phase | Complexity | Files | Time |
|-------|-----------|-------|------|
| 0 | Trivial | 3 | 15 min |
| 1 | Low | 2-4 | 30 min |
| 2 | Medium | 4 | 2-3 hours |
| 3 | High | 3-5 | 3-4 hours |
| 4 | Low-Med | 5-10 | 1-2 hours |
| 5 | Medium | 3-4 | 2-3 hours |
Total: 9-13 hours

## Key Files
| File | Role |
|------|------|
| backend/.env | NEO4J_URI fix, GOOGLE_API_KEY |
| docker-compose.yml | GOOGLE_API_KEY passthrough |
| backend/app/services/memory_service.py | Primary: swap fire-and-forget -> enqueue |
| backend/app/services/graphiti_bridge_service.py | DELETE in Phase 3D |
| backend/app/services/episode_worker.py | NEW: GraphitiEpisodeWorker |
| backend/app/main.py | Lifespan wiring |
| backend/app/config.py | New config fields |
| backend/app/api/v1/endpoints/monitoring.py | Worker health endpoint |
| backend/app/clients/graphiti_client.py | LearningMemoryClient may be removed |

## Open Questions
1. group_id: Single (canvas-learning) or per-subject (canvas-cs188)? Per-subject matches existing build_group_id().
2. Dead-letter replay on startup? Adds startup latency.
3. LearningMemoryClient: Remove entirely or keep as tertiary fallback?
4. Phase 3D: Same commit as swap or separate? Recommend separate.
