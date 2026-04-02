# S01 Research: 代码库清理 + 环境就绪

**Slice:** S01 — 代码库清理 + 环境就绪
**Milestone:** M001 — 核心管道端到端打通
**Researched:** 2026-04-02
**Depth:** Targeted (known tech, moderate cleanup + config work)

---

## Summary

S01 is primarily cleanup and environment setup. The codebase is in better shape than expected:
- **R041 (TS errors) is ALREADY DONE** — `tsc --noEmit` returns 0 errors with strict mode enabled (TS 5.8.3)
- **R042 (garbage files)** — 16 tracked garbage files need `git rm` + 60 deleted-but-tracked unicode snapshot files need cleanup
- **R001 (MCP sidecar)** — Architecture is sound (3-layer: frontend->sidecar->backend MCP), likely failure is transport type or backend not running. Needs live diagnostic.
- **Docker-compose** — Already has staged Mac-focused changes (Ollama->native, paths->Mac, host.docker.internal)
- **Dual-layer Key separation** — Already organic (Anthropic key for sidecar, Google key for backend), needs formal enforcement

## Requirements Mapping

| Requirement | Status | Notes |
|---|---|---|
| R041 — 1730 TS errors | **ALREADY DONE** | 0 errors, strict mode, TS 5.8.3 |
| R042 — Garbage files | Ready to execute | 16 tracked files + 60 deleted snapshots |
| R001 — MCP sidecar fix | Needs live diagnostic | Transport type mismatch most likely |
| R043 — Mac platform | Partially done | docker-compose Mac changes staged |

## Recommendation

Split into 3 tasks:
1. **Garbage file cleanup** (mechanical, no risk) — `git rm` tracked garbage, clean deleted snapshots
2. **Docker/env Mac setup** (low risk) — finalize docker-compose, verify `docker compose up` + `npm run tauri dev`
3. **MCP sidecar diagnostic** (medium risk, needs live system) — start services, diagnose transport, fix

Task 1 is independent. Tasks 2-3 require running services.

---

## Implementation Landscape

### Task 1: Garbage File Cleanup

**Files to `git rm`** (all tracked, confirmed via `git ls-files`):

Root (10 files, ~45KB):
- `R` (32B, single-char garbage)
- `UsersHeishingAppDataLocalTempwrite-pig.js` (12KB)
- `UsersHeishingAppDataLocalTempwrite-story.js` (14B)
- `UsersHeishingAppDataLocalTempwrite-test-event-bus.js` (9.5KB)
- `UsersHeishingAppDataLocalTempwrite-test-fc.js` (6.5KB)
- `UsersHeishingAppDataLocalTempwrite-test-pig.js` (10KB)
- `UsersHeishingAppDataLocalTempwrite-test-qa.js` (5.7KB)
- `UsersHeishingAppDataLocalTempwrite-tests.js` (725B)
- `test-fix-v11-prompt.txt` (50B)
- `test-pipe-prompt.txt` (31B)

Backend (6 files, ~224B):
- `backend/!` (32B)
- `backend/J` (32B)
- `backend/R` (32B)
- `backend/schema_test.canvas` (32B)
- `backend/workflow_test.canvas` (32B)
- `backend/_gen_mastery_tests.py` (130B, one-off script)

**Already-deleted files to `git rm --cached`** (~60 files):
- `backend/.canvas-learning/snapshots/` unicode directories — already deleted locally, need `git rm` to clean tracking
- `backend/` unicode-named files (8 files) — same situation
- Root unicode files — same

**`.gitignore` already covers** `.canvas-learning/`, `*.canvas`, so no new ignore rules needed.

**Verification:** `git status` should show clean after `git rm` + commit.

### Task 2: Docker/Environment Mac Setup

**docker-compose.yml** — already has good staged changes:
- Ollama service -> `profiles: ["windows"]` (won't start on Mac)
- Backend OLLAMA_HOST -> `host.docker.internal:11434` (reach native Mac Ollama)
- Volume paths -> Mac paths (`/Users/Heishing/...`)
- Removed `ollama` dependency from backend service

**Still needed:**
- Verify `docker compose up -d` starts neo4j + backend successfully
- Verify backend health endpoint: `curl http://localhost:8001/api/v1/health`
- Verify Neo4j reachable: `curl http://localhost:7478`
- Verify native Ollama has bge-m3 model: `ollama list | grep bge-m3`
- Verify `npm run tauri dev` starts frontend (Vite 5173 + Tauri window)

**Key env vars** (in `backend/.env`, already gitignored):
- `AI_PROVIDER=google`, `AI_API_KEY` (Gemini)
- `GOOGLE_API_KEY` (same Gemini key, for graphiti-core)
- `NEO4J_URI=bolt://localhost:7691`
- `OLLAMA_HOST=http://localhost:11434`
- `LANCEDB_PATH=data/lancedb`

**Dual-layer key separation** is already organic:
- Outer (sidecar): `ANTHROPIC_API_KEY` from host env (Claude subscription)
- Inner (backend): `GOOGLE_API_KEY` from `backend/.env` (Gemini)
- No cross-contamination observed

### Task 3: MCP Sidecar Diagnostic

**Architecture (3-layer chain):**
1. **Frontend** (`claude-engine.ts:731-733`): Injects `mcpServers: { canvas: { type: 'sse', url: 'http://localhost:8001/mcp' } }`
2. **Sidecar** (`sidecar.js`): Passes `mcpServers` to Agent SDK `query()`. Has 14-tool whitelist in `MCP_TOOLS` Set.
3. **Backend** (`mcp/server.py`): `fastapi-mcp>=0.1.0` converts 14 FastAPI routes (tag "MCP Tools") to MCP tools. Mounted at `/mcp`.

**Known fixes already applied:**
- G-API-001: `fastapi-mcp` anyOf+type schema monkey-patch (S29)
- G-API-002: All 15 routes have explicit `operation_id` (S29)

**Likely failure points (ranked):**

1. **Transport type mismatch** — `claude-engine.ts` sends `type: 'sse'`, but `fastapi-mcp` version may have shifted to Streamable HTTP. Comment on line 729-730 explicitly flags this risk.
2. **Backend not running** — If `fastapi-mcp` import fails, `except ImportError` silently skips MCP setup. Look for `"MCP server setup skipped"` in logs.
3. **Tool name namespacing** — SDK may prefix tools as `mcp__canvas__query_mastery` vs bare `query_mastery` in whitelist. The `canUseTool` has `mcp__` fallback (line 126) but could still mismatch.
4. **Schema validation** — Monkey-patch targets specific `fastapi-mcp` v0.4.0 code paths that may have moved if upgraded.

**Diagnostic steps:**
1. Start backend: `docker compose up -d`
2. Test MCP endpoint: `curl http://localhost:8001/mcp` — should return SSE stream or handshake
3. Check backend logs: `docker compose logs backend | grep -i mcp`
4. Check `fastapi-mcp` version in container: `docker compose exec backend pip show fastapi-mcp`
5. If MCP endpoint works, test sidecar manually via NDJSON stdin
6. If transport mismatch: change `type: 'sse'` to `type: 'http'` or vice versa in `claude-engine.ts`

**Key files to modify (if fix needed):**
- `frontend/src/services/claude-engine.ts` (line 731-733) — MCP server config
- `backend/app/mcp/server.py` — MCP mount and monkey-patch
- `frontend/sidecar/sidecar.js` (line 38-44, 126) — tool whitelist and permission

### Deprecated Code for S01 Scope

**LearningMemoryClient** (JSON legacy, 10 files) — this is **S02 scope** (R010), not S01. Leave untouched.

**Naming residuals (G-FAUX legacy)** — API model names + config attributes retained for API compatibility. S02 scope (R011).

---

## Constraints and Risks

| Risk | Severity | Mitigation |
|---|---|---|
| MCP transport mismatch needs live diagnosis | Medium | Cannot fix blind — need running services. Diagnostic steps above. |
| Docker volumes reference Mac-specific paths | Low | Already staged. Vault paths exist on this machine. |
| `fastapi-mcp>=0.1.0` is loose version pin | Low | Check actual installed version in Docker image |
| Native Ollama must have bge-m3 loaded | Low | `ollama pull bge-m3` if missing |

## What NOT to Do in S01

- Do NOT touch LearningMemoryClient (S02 R010)
- Do NOT touch naming residuals (S02 R011)
- Do NOT refactor MCP architecture — just fix the connection
- Do NOT modify backend services — only config/setup files
- Do NOT attempt TS error fixes (already at 0)

---

## Verification Criteria

1. `git status` clean (no tracked garbage files)
2. `docker compose up -d` -> neo4j + backend healthy (no ollama on Mac)
3. `curl http://localhost:8001/api/v1/health` -> 200
4. `curl http://localhost:8001/mcp` -> valid MCP reply
5. `npm run tauri dev` -> Vite dev server + Tauri window opens
6. `tsc --noEmit` -> 0 errors (already passing, regression guard)

## Skill Discovery

No external skills needed. This slice uses:
- Docker Compose (standard, well-known)
- Tauri 2 (already in codebase)
- fastapi-mcp (already in codebase, version check needed)
- @anthropic-ai/claude-agent-sdk (already in sidecar)

No `npx skills find` recommendations.
