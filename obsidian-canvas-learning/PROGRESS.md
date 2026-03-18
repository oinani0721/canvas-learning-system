# Canvas Learning Plugin - Progress

## M0: Minimal scaffold [DONE]
- [x] Clone official obsidian-sample-plugin template
- [x] Create src/main.ts + src/settings.ts (pure TypeScript)
- [x] Build succeeds (1.6KB, zero errors)
- [x] Plugin loads in Obsidian (screenshot confirmed)
- [x] Ribbon icon shows, Notice pops up, status bar works

## M1a: ItemView sidebar panel [DONE]
- [x] Create src/canvas-learning-view.ts (ItemView)
- [x] Register view in main.ts, ribbon icon opens it
- [x] Verify: clicking icon opens right sidebar with text
- ~35 lines new file + ~15 lines main.ts changes

## M1b: Read .canvas file and display nodes
- [ ] Parse active .canvas file JSON (nodes/edges)
- [ ] Display node names as list in sidebar
- [ ] Verify: open .canvas file, see node list in sidebar
- ~60 lines new code

## M1c: Node interaction (click to see details)
- [ ] Click a node shows its full text content
- [ ] Verify: click node in list, see content below
- ~50 lines new code

## Story 3.1: Claude Code CLI Per-Node Session [DONE]
- [x] Task 1: DialogEngine interface (dialog-engine.ts) — StreamEvent, EngineError, DialogEngine
- [x] Task 2: ClaudeCodeEngine implementation (claude-code-engine.ts) — spawn, NDJSON parse, auth detect
- [x] Task 3: SessionStore (session-store.ts) — JSON persistence, nodeId->sessionId mapping
- [x] Task 5: MCP config generator (mcp-config.ts) — canvas-mcp.json generation
- [x] TypeScript compiles clean, esbuild production build passes
- Files: src/services/dialog-engine.ts, claude-code-engine.ts, session-store.ts, mcp-config.ts

## M2: Backend API connection
- [ ] Copy api-client.ts from _v1-ref (requestUrl)
- [ ] Health check on plugin load
- [ ] Status bar shows "connected" or "offline"
- ~80 lines (mostly copied)

## M3: AI explain a node (first AI feature)
- [ ] Right-click node -> "Explain this concept"
- [ ] Call POST /api/v1/agents/explain/oral
- [ ] Display AI response in modal
- ~70 lines new code

## Key rules
- Each step verified in Obsidian before next
- No step exceeds 80 lines
- Pure TypeScript + Obsidian API only
- esbuild watch + hot-reload = <1s feedback
