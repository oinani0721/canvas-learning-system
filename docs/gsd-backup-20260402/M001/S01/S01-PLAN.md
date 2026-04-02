# S01: 代码库清理 + 环境就绪

**Goal:** Clean codebase baseline (zero garbage files) with working Mac dev environment (docker services healthy, MCP endpoint reachable).
**Demo:** `git status` shows no tracked garbage; `docker compose up -d` starts neo4j+backend on Mac; `curl localhost:8001/api/v1/health` returns 200; `curl localhost:8001/mcp` returns valid MCP response; `tsc --noEmit` still 0 errors.

## Must-Haves

- All 16 tracked garbage files + ~60 deleted-but-tracked snapshot files removed from git tracking (R042)
- `tsc --noEmit` continues to pass with 0 errors (R041 regression guard)
- `docker compose up -d` starts neo4j + backend on Mac without Ollama container (R043)
- Backend health endpoint returns 200
- MCP endpoint at `localhost:8001/mcp` returns valid response (R001 partial)
- MCP transport type matches between frontend config and backend server (R001)

## Proof Level

- This slice proves: operational
- Real runtime required: yes (docker services + MCP endpoint)
- Human/UAT required: no

## Verification

- `git ls-files -- R 'UsersHeishing*' 'test-fix*' 'test-pipe*' 'backend/!' 'backend/J' 'backend/R' 'backend/schema_test.canvas' 'backend/workflow_test.canvas' 'backend/_gen_mastery_tests.py' | wc -l` returns 0
- `git ls-files --deleted | wc -l` returns 0
- `cd frontend && npx tsc --noEmit` exits 0
- `docker compose ps` shows neo4j + backend running/healthy
- `curl -sf http://localhost:8001/api/v1/health` returns 200
- `curl -sf http://localhost:8001/mcp` returns valid MCP handshake or SSE stream

## Observability / Diagnostics

- Runtime signals: `docker compose logs backend | grep -i mcp` for MCP mount status
- Inspection surfaces: `curl localhost:8001/api/v1/health`, `curl localhost:8001/mcp`, `docker compose ps`
- Failure visibility: `"MCP server setup skipped"` in backend logs if fastapi-mcp import fails; container exit codes
- Redaction constraints: `backend/.env` contains API keys — never commit or log

## Integration Closure

- Upstream surfaces consumed: none (S01 is the foundation slice)
- New wiring introduced in this slice: MCP transport type alignment (if fix needed)
- What remains before the milestone is truly usable end-to-end: S02 (Graphiti memory), S03 (RAG pipeline), S04 (exam chain)

## Tasks

- [ ] **T01: Git-remove all tracked garbage files and deleted snapshots** `est:15m`
  - Why: R042 — 16 tracked garbage files + ~60 deleted-but-tracked unicode snapshot files pollute the repo
  - Files: root garbage files (`R`, `UsersHeishing*`, `test-*.txt`), `backend/` garbage (`!`, `J`, `R`, `*.canvas`, `_gen_mastery_tests.py`), `backend/.canvas-learning/snapshots/`
  - Do: (1) `git rm` the 16 tracked garbage files by exact name. (2) `git rm` all 60 deleted-but-tracked files via `git ls-files --deleted | xargs git rm`. (3) Verify `.gitignore` already covers `.canvas-learning/` and `*.canvas`. (4) Commit the cleanup.
  - Verify: `git ls-files -- R 'UsersHeishing*' 'test-fix*' 'test-pipe*' 'backend/!' 'backend/J' 'backend/R' 'backend/schema_test*' 'backend/workflow_test*' 'backend/_gen*' | wc -l` returns 0 AND `git ls-files --deleted | wc -l` returns 0
  - Done when: Zero tracked garbage files, zero deleted-but-tracked files, commit created

- [ ] **T02: Verify Docker Mac environment and start services** `est:20m`
  - Why: R043 — docker-compose.yml already has Mac config (Ollama→profiles:windows, host.docker.internal, Mac vault paths). Need to verify services actually start healthy.
  - Files: `docker-compose.yml`, `backend/.env`
  - Do: (1) Run `docker compose up -d`. (2) Wait for health checks, verify `docker compose ps` shows neo4j+backend healthy. (3) `curl http://localhost:8001/api/v1/health` → 200. (4) Check `ollama list | grep bge-m3` (pull if missing). (5) `cd frontend && npx tsc --noEmit` → 0 errors. (6) If any service fails, diagnose from `docker compose logs` and fix.
  - Verify: `docker compose ps` shows healthy; `curl -sf http://localhost:8001/api/v1/health` returns 200; `npx tsc --noEmit` exits 0
  - Done when: Docker services healthy on Mac, backend health 200, TS zero errors maintained

- [ ] **T03: Diagnose and fix MCP sidecar→backend connection** `est:30m`
  - Why: R001 — MCP tool calls don't trigger. Likely transport type mismatch (SSE vs Streamable HTTP). Needs live backend from T02.
  - Files: `frontend/src/services/claude-engine.ts` (lines 728-733), `backend/app/mcp/server.py`, `frontend/sidecar/sidecar.js` (lines 38-44, 126)
  - Do: (1) `curl http://localhost:8001/mcp` — check response type. (2) `docker compose exec backend pip show fastapi-mcp` — check version. (3) `docker compose logs backend | grep -i mcp` — verify mount. (4) If transport mismatch: change `type: 'sse'` to `type: 'http'` (or vice versa) in `claude-engine.ts:732`. (5) Verify tool names in sidecar `MCP_TOOLS` whitelist match backend's `operation_id` values. (6) If schema monkey-patch targets moved in newer fastapi-mcp, update `server.py`.
  - Verify: `curl -sf http://localhost:8001/mcp` returns non-empty; `docker compose logs backend | grep -i mcp` shows successful mount; no "MCP server setup skipped" in logs
  - Done when: MCP endpoint accessible, transport type aligned, sidecar tool names match backend

## Files Likely Touched

- Root: `R`, `UsersHeishingAppDataLocalTempwrite-*.js`, `test-fix-v11-prompt.txt`, `test-pipe-prompt.txt`
- `backend/!`, `backend/J`, `backend/R`, `backend/schema_test.canvas`, `backend/workflow_test.canvas`, `backend/_gen_mastery_tests.py`
- `backend/.canvas-learning/snapshots/**` (~60 deleted files)
- `docker-compose.yml` (verify, possibly no changes)
- `frontend/src/services/claude-engine.ts` (line 732, if transport fix needed)
- `backend/app/mcp/server.py` (if monkey-patch fix needed)
- `frontend/sidecar/sidecar.js` (if tool name fix needed)
