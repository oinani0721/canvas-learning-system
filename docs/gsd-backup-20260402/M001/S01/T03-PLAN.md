---
estimated_steps: 5
estimated_files: 3
skills_used: []
---

# T03: Diagnose and fix MCP sidecar→backend connection

**Slice:** S01 — 代码库清理 + 环境就绪
**Milestone:** M001

## Description

R001 — The sidecar streaming conversation works, but MCP tool calls don't trigger. The most likely cause (per research) is a transport type mismatch: `claude-engine.ts:731` sends `type: 'sse'` but `fastapi-mcp` may have shifted to Streamable HTTP. Secondary suspects: backend not mounting MCP (silent ImportError), tool name namespace mismatch (`mcp__canvas__` prefix vs bare names in whitelist).

This task requires running services (T02 must complete first). It's diagnostic-first: probe the actual MCP endpoint, check the fastapi-mcp version, then apply the minimal fix.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| Backend MCP endpoint | Check if `fastapi-mcp` import failed silently — look for "MCP server setup skipped" in logs | Backend may not have started — fall back to T02 | Check monkey-patch compatibility with installed fastapi-mcp version |
| fastapi-mcp library | Version mismatch may break monkey-patch in `server.py` — check actual version vs expected | N/A | N/A |
| Sidecar Agent SDK | Tool name resolution may fail — check `canUseTool` and `mcp__` prefix fallback | N/A | N/A |

## Steps

1. **Probe MCP endpoint**: With backend running (from T02), run `curl -v http://localhost:8001/mcp` to determine the actual transport type (SSE event-stream vs JSON). Check `docker compose logs backend | grep -i mcp` for mount/setup messages.
2. **Check fastapi-mcp version**: Run `docker compose exec backend pip show fastapi-mcp` to get installed version. Compare with the monkey-patch code in `backend/app/mcp/server.py` which targets specific v0.4.0 code paths.
3. **Diagnose transport mismatch**: Read `frontend/src/services/claude-engine.ts` lines 725-740 to confirm current MCP config (`type: 'sse'`). Compare with what the actual endpoint serves. If mismatch, determine correct type.
4. **Apply fix**: If transport type mismatch → change `type` in `claude-engine.ts`. If backend MCP not mounted → fix import or version. If tool name mismatch → align sidecar whitelist in `sidecar.js` with actual MCP tool names.
5. **Verify end-to-end**: Confirm MCP endpoint responds correctly with the fixed transport type. Check sidecar can list available tools (if testable without full Tauri app).

## Must-Haves

- [ ] MCP endpoint at `localhost:8001/mcp` returns valid response (not 404 or connection error)
- [ ] Transport type in `claude-engine.ts` matches what `fastapi-mcp` actually serves
- [ ] Backend logs confirm MCP server is mounted (no "MCP server setup skipped")
- [ ] Sidecar tool whitelist names align with backend MCP tool names

## Verification

- `curl -sf http://localhost:8001/mcp` returns a valid response (not empty, not 404)
- `docker compose logs backend 2>&1 | grep -i mcp` shows successful mount, no "skipped" message
- `grep -n "type:" frontend/src/services/claude-engine.ts | grep mcp` shows correct transport type matching backend

## Observability Impact

- Signals added/changed: MCP connection diagnostic log messages
- How a future agent inspects this: `curl localhost:8001/mcp`, `docker compose logs backend | grep mcp`, check `claude-engine.ts` MCP config
- Failure state exposed: Transport type mismatch error, fastapi-mcp import failure, tool name resolution failure

## Inputs

- `frontend/src/services/claude-engine.ts` — MCP server config (line 731, `type: 'sse'`)
- `backend/app/mcp/server.py` — MCP mount and monkey-patch code
- `frontend/sidecar/sidecar.js` — MCP_TOOLS whitelist and canUseTool permission

## Expected Output

- `frontend/src/services/claude-engine.ts` — transport type corrected if mismatched
- `backend/app/mcp/server.py` — fixed if MCP mount is failing
- `frontend/sidecar/sidecar.js` — tool names aligned if namespace mismatch found
