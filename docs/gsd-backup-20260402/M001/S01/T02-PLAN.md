---
estimated_steps: 5
estimated_files: 3
skills_used: []
---

# T02: Finalize Docker Compose Mac config and verify backend health

**Slice:** S01 — 代码库清理 + 环境就绪
**Milestone:** M001

## Description

The docker-compose.yml already has staged Mac-focused changes (Ollama service → `profiles: ["windows"]` so it won't start on Mac, backend OLLAMA_HOST → `host.docker.internal:11434` to reach native Mac Ollama, volume paths adjusted for Mac). This task verifies those changes work: docker services start, neo4j is reachable, backend health endpoint returns 200, and `tsc --noEmit` still passes as R041 regression guard.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| Docker daemon | Abort — cannot proceed without Docker | N/A | N/A |
| Neo4j container | Check logs, may need port conflict resolution (7691/7478) | Wait up to 30s for startup | N/A |
| Backend container | Check `docker compose logs backend` for import errors | Wait up to 30s | N/A |
| Native Ollama (bge-m3) | `ollama pull bge-m3` if missing — backend embedding may fail without it | N/A | N/A |

## Steps

1. Read `docker-compose.yml` to confirm staged Mac changes are correct (Ollama profiles, host.docker.internal, Mac volume paths).
2. Run `docker compose up -d` and wait for containers to be healthy.
3. Verify: `docker compose ps` shows neo4j + backend running (no ollama). Check `curl -sf http://localhost:8001/api/v1/health` returns 200. Check `curl -sf http://localhost:7478` (Neo4j browser) is reachable.
4. Check native Ollama has bge-m3: `ollama list | grep bge-m3`. If missing, run `ollama pull bge-m3`.
5. Run `cd frontend && npx tsc --noEmit` to verify R041 regression guard (0 TS errors maintained).

## Must-Haves

- [ ] `docker compose up -d` starts neo4j + backend without Ollama container on Mac
- [ ] Backend health endpoint returns 200
- [ ] Neo4j is reachable at configured port
- [ ] `tsc --noEmit` passes with 0 errors (R041 regression guard)

## Verification

- `docker compose ps --format '{{.Service}} {{.State}}'` shows neo4j and backend as "running"
- `curl -sf http://localhost:8001/api/v1/health` returns HTTP 200
- `cd frontend && npx tsc --noEmit` exits with code 0

## Observability Impact

- Signals added/changed: Docker container health status, backend startup logs
- How a future agent inspects this: `docker compose ps`, `docker compose logs backend`, `curl localhost:8001/api/v1/health`
- Failure state exposed: Container exit codes, backend stderr showing import failures or connection errors

## Inputs

- `docker-compose.yml` — staged Mac changes to verify
- `backend/.env` — environment variables for backend (AI_PROVIDER, NEO4J_URI, OLLAMA_HOST)
- `frontend/tsconfig.json` — TypeScript config for regression check

## Expected Output

- `docker-compose.yml` — verified working on Mac (may need minor fixes if staged changes are incomplete)
- `frontend/` — verified tsc --noEmit passes (no changes expected)
