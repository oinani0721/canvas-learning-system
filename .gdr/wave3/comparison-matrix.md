# GDR Wave 3 — Comparison Matrix: Tool Call UI + Observability Closed Loop

> **Agent**: SYNTH (Wave 3)
> **Research Topic**: 前端工具调用UI + 可观测性闭环（参考 Claudian/Claude Code）
> **Generated**: 2026-03-24
> **Input**: Wave 2 Agents W2-A through W2-J (10 agents, key findings summarized)

---

## 1. Comprehensive Comparison Matrix

### 1.1 Tool Call UI Rendering Mode

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Rendering architecture** | Collapsible block + Generative UI hybrid (W2-G: Cursor/Windsurf use structured steps; Claude Code uses collapsible blocks; Vercel uses Generative UI) | XAGen: log visualization + human-in-the-loop + auto error detection (W2-E); A2UI (Google): declarative catalog > HTML injection (W2-C) | No explicit decision on UI rendering mode for tool calls | **NEW FINDING** — Must decide: collapsible block (Claudian/Companion pattern) vs structured steps (Cursor) vs generative UI (Vercel). Recommend: collapsible block + generative UI hybrid per W2-G |
| **Tool-specific renderers** | assistant-ui: `makeAssistantToolUI` registers per-tool renderer + `ToolFallback` collapsible (W2-A); Claudian: `ToolCallRenderer` with 10+ tool-specific renderers (W2-I) | No academic position | stream-json events drive UI — ACTIVE | **VALIDATED** — Community unanimously uses per-tool specialized renderers with a generic fallback. Claudian's 10+ renderers + assistant-ui's `makeAssistantToolUI` confirm this pattern |
| **Dual payload mode** | Pi agent: tool returns `model text` + `UI blocks` separately (W2-C); Vercel AI SDK: `message.parts` dispatched by type (W2-A) | ECD framework: evidence stream separate from presentation (W2-D) | Observer outputs standardized learning event — ACTIVE | **VALIDATED** — Separate model-facing payload from UI-facing payload. Learning events go to Observer; UI blocks go to renderer |
| **Learning-specific differentiation** | No competitor has learning-specific observability (W2-G): "展示'为什么调用'关联学习目标" is unique differentiator | AgentTrace: cognitive layer logs "why" an agent acts (W2-E); OLM literature: make student model visible drives metacognition (W2-D) | No explicit decision | **NEW FINDING** — Unique opportunity: annotate tool calls with learning context ("why was this tool called relative to your learning goal"). No competitor does this. Academic support from AgentTrace cognitive layer + OLM research |

### 1.2 Event Stream Transport Protocol (Sidecar → Frontend)

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Primary transport** | Tauri Channels > Tauri Events for streaming (W2-C); WebSocket on Windows outperforms binary IPC by avoiding 200ms penalty (W2-C, W2-H: KL-10); opcode uses Tauri event emit `claude-output:{session_id}` (W2-A) | AG-UI Protocol: ~16 event types + toolCallId correlation (W2-C) | Tool-UI Bridge real-time needs — ACTIVE; FR-AGENT-01 data flow not described = systemic gap | **CONFLICT** — Existing decision says "stream-json" but W2-C/W2-H show Windows IPC has 200ms penalty for large payloads. WebSocket or Tauri Channel is better. Solo IDE (W2-B) uses identical architecture (Tauri2+Node.js sidecar+React) and is production-proven |
| **Event schema** | AG-UI: `TOOL_CALL_START` / `STATE_DELTA` / `TOOL_CALL_END` (W2-A); SDKMessage has 21 types including `tool_progress`, `tool_use_summary` (W2-I); StreamChunk has 13 variants + `parentToolUseId` for subagent nesting (W2-I) | AgentTrace: three-layer logging (operational/cognitive/contextual) (W2-E) | stream-json contains tool_use/tool_result — ACTIVE | **VALIDATED with EXTENSION** — stream-json does provide tool_use/tool_result (W2-F confirmed this, correcting earlier assumption). But schema should be extended with AG-UI-style toolCallId correlation + AgentTrace cognitive layer for learning context |
| **Streaming parse strategy** | Claudian: skip `input_json_delta` streaming, wait for complete `SDKAssistantMessage` (W2-I); Agent SDK: `content_block_start/delta/stop`, tool_use deltas are partial JSON needing accumulation (W2-B) | No academic position | Claudian mode (spawn CLI + subscribe credits) — ACTIVE | **VALIDATED** — Claudian's "wait for complete message" strategy is simpler and avoids partial JSON pitfalls. Acceptable latency tradeoff for learning context (not real-time coding) |

### 1.3 Tool Call State Machine Model

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **State transitions** | Vercel AI SDK: three-state `partial-call → call → result` (W2-A); Claudian ToolCallRenderer: `Running → completed/error/blocked` (W2-I); AG-UI: `TOOL_CALL_START → STATE_DELTA* → TOOL_CALL_END` (W2-A) | No academic position on state machine design | No explicit decision | **NEW FINDING** — Must adopt a state machine. Recommend Claudian's 4-state model (`pending → running → completed/error/blocked`) because it handles the `blocked` state for permission prompts (PreToolUse hook deny/ask) |
| **Pending tools buffer** | Claudian StreamController: `pendingTools` Map buffers tool calls, batch renders to reduce DOM jitter (W2-I) | No academic position | No explicit decision | **NEW FINDING** — Critical for UX: buffer pending tool calls and batch-render. Prevents rapid DOM mutations during multi-tool sequences |
| **Hook integration** | Claudian: Hook system with 17 event types, `PreToolUse` can return `allow/deny/ask` (W2-I); Community consensus: hook-based observability is the standard (W2-B) | No academic position | No explicit decision | **NEW FINDING** — Hook system is essential for permission control AND learning observability. PreToolUse/PostToolUse hooks serve dual purpose: (1) security gating, (2) Observer trigger points for learning event extraction |

### 1.4 Collapsible/Expandable UI Components

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Collapse pattern** | assistant-ui: `ToolGroup` folding groups + `ToolFallback` collapsible (W2-A); Companion: collapsible tool blocks + syntax highlighting = "community gold standard UX" (W2-B); Claude Code: collapsible block mode (W2-G) | XAGen: expandable log visualization for agent transparency (W2-E) | No explicit decision | **NEW FINDING** — Strong consensus on collapsible blocks. Companion's pattern (collapsed by default, expand to see details, syntax highlighting for code) is the gold standard |
| **Default state** | Collapsed by default, expand on click (Companion, Claude Code). Running tools show spinner, completed tools show summary (W2-I) | LLM natural language summaries significantly improve dashboard UX (W2-D) | No explicit decision | **NEW FINDING** — Default collapsed + one-line summary. For learning context: add LLM-generated natural language explanation of what the tool did and why (supported by W2-D empirical evidence) |
| **Nesting for subagents** | StreamChunk `parentToolUseId` supports subagent nesting (W2-I); Cline: `ApiStream → Task → ToolExecutor → ChatView` layered architecture (W2-A) | No academic position | No explicit decision | **NEW FINDING** — Must support nested tool calls (subagent spawns tool). Use `parentToolUseId` from StreamChunk schema |

### 1.5 Observer Trigger Mechanism

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Trigger pattern** | PostToolUse hooks as primary trigger (W2-B community consensus); Claudian: `PreToolUse/PostToolUse` hooks (W2-A, W2-I) | AgentTrace: operational log at every action, cognitive log at decision points, contextual log at environment changes (W2-E); ECD: task completion as evidence trigger (W2-E) | Observer outputs standardized learning event — ACTIVE; prompt mechanism TBD (enumerated vs free text) | **VALIDATED with REFINEMENT** — PostToolUse hook is the right trigger. But Observer should also trigger on: (1) conversation turn completion, (2) tool error/blocked states, (3) user explicit "I don't understand" signals. Aligns with AgentTrace three-layer model |
| **Extraction approach** | fire-and-track with Outbox pattern (W2-C): local SQLite WAL write first → async relay → failure retry | Generate-Retrieve-Rerank pipeline for misconception detection (W2-D, W2-E: Misconception GRR); A-MEM Zettelkasten atomicity for knowledge extraction (W2-D) | Observer write confirmed; fire-and-forget needs upgrade to fire-and-track | **VALIDATED** — fire-and-track with Outbox is the correct pattern. Observer extracts atomic learning events (A-MEM style), writes to local SQLite WAL first, then asynchronously persists to Graphiti |
| **Prompt strategy** | No community consensus on enumerated vs free text for Observer prompts | BEA 2025 Shared Task: 4-dimension annotation (identify/localize/guide/actionable-feedback) provides structured extraction schema (W2-D) | Prompt mechanism TBD | **NEW FINDING** — Use BEA 2025's 4-dimension schema as Observer extraction template: (1) what mistake was made, (2) where in the reasoning, (3) what guidance to give, (4) is the feedback actionable. Structured > free text |

### 1.6 Memory Write Reliability (fire-and-forget vs fire-and-track)

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Write pattern** | fire-and-track with Outbox pattern: local SQLite WAL → async relay → retry on failure (W2-C); Observer fire-and-forget is listed as HIGH risk (W2-H) | MemArchitect: explicit memory lifecycle governance with decay, conflict resolution, privacy controls (W2-D) | fire-and-forget needs upgrade — ACTIVE | **VALIDATED** — Unanimous: fire-and-forget is unacceptable. Must upgrade to fire-and-track with Outbox. Local write-ahead log guarantees no data loss even if Graphiti is temporarily unavailable |
| **Retry/reconciliation** | Outbox pattern: periodic sweep of undelivered events, exponential backoff retry (W2-C) | Graphiti bi-temporal model handles late arrivals via ingestion-time tracking (W2-D) | No explicit retry mechanism decided | **NEW FINDING** — Graphiti's bi-temporal model (event time vs ingestion time) naturally handles late-arriving events from Outbox retry. This is a synergistic fit |
| **User feedback on write status** | Graphiti write success/failure user feedback listed as MEDIUM priority gap (context_pack.json gap #5) | OLM: make system state visible to learner (W2-D) | No explicit decision | **NEW FINDING** — Show subtle indicator (toast/badge) when learning memory is saved vs pending. Aligns with OLM transparency principle |

### 1.7 Observability Standard

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Standard** | OpenTelemetry (OTel) GenAI semantic conventions is the community standard for agent observability (W2-B) | OpenTelemetry is becoming THE standard for agent observability (W2-D: 25 papers, 6 cross-themes); AgentTrace explicitly builds on OTel (W2-E); trace-based observability > black-box evaluation (W2-D) | No explicit observability standard decided | **NEW FINDING** — Strong consensus: adopt OTel GenAI semantic conventions. AgentTrace's three-layer model (operational/cognitive/contextual) on top of OTel spans provides the right abstraction |
| **Trace granularity** | Per-tool-call spans with parent session trace (OTel model) | AgentTrace: operational (every action), cognitive (reasoning), contextual (environment) — three layers (W2-E) | No explicit decision | **NEW FINDING** — Three-layer: (1) operational spans = tool call start/end/duration, (2) cognitive spans = why agent chose this tool, (3) contextual spans = current learning state. Map to OTel span attributes |
| **Learning analytics** | No competitor has learning-specific observability (W2-G) | Learning analytics shifting from analytics-centric to learning-centric (W2-D); LLM natural language explanations significantly improve dashboard UX (W2-D, empirical evidence) | No explicit decision | **NEW FINDING** — Unique differentiator: learning-centric observability dashboard. Show not just "what tool was called" but "how this relates to your learning progress". LLM-generated summaries for non-technical learners |

### 1.8 Misconception Detection Method

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Detection pipeline** | No community consensus (domain-specific to education) | Generate-Retrieve-Rerank pipeline (W2-E: arXiv:2602.02414): LLM generates plausible misconceptions → embedding retrieval from misconception bank → reranker selects best match | Observer accuracy target >80% — ACTIVE | **VALIDATED** — GRR pipeline is the SOTA approach. BEA 2025 best results: ~78% F1 for mistake identification. >80% target is at the frontier but feasible for structured domains |
| **Weakness taxonomy** | No community position | 5-type taxonomy NOT grounded in established frameworks (W2-D); Should use Bloom's 4 knowledge types + CDM severity + affective dimension; Multi-level error processing: cognitive + metacognitive + motivational + emotional + behavioral + social (W2-D) | 5 weakness types (concept/reasoning/prerequisite/depth/metacognitive) — ACTIVE | **CONFLICT** — Academic evidence (W2-D) shows the 5-type taxonomy is NOT MECE and misses affective dimensions. Recommend re-derivation from Bloom + CDM + error learning literature |
| **Small model viability** | No community position | Misconception GRR: small model LoRA fine-tuning can exceed large model performance (W2-E) | No decision on model size for Observer | **NEW FINDING** — Small fine-tuned model may outperform GPT-4 for misconception detection. Reduces latency and cost for real-time Observer |

### 1.9 Security (Permission Model)

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Tool permission gating** | Claudian: PreToolUse hook returns `allow/deny/ask` (W2-I); Agent SDK `bypassPermissions` flag is a HIGH risk if misused (W2-H); Hook-based permission is community standard (W2-B) | No academic position on agent permission models | 6-layer defense confirmed (Mode D architecture) | **VALIDATED** — PreToolUse hook permission gating aligns with 6-layer defense. Must NOT use `bypassPermissions` flag |
| **Graphiti injection risk** | graphiti-core CVE-2026-32247: Cypher injection vulnerability, MUST upgrade to >= 0.28.2 (W2-J) | No academic position | Graphiti in use — ACTIVE | **STALE** — CRITICAL security action: upgrade graphiti-core to >= 0.28.2 immediately. Cypher injection is a severe vulnerability for a knowledge graph storing student data |
| **CSP for tool UI** | Tauri 2 built-in CSP with compile-time nonce injection (W2-A); A2UI (Google): declarative catalog > HTML injection for security (W2-C) | No academic position | CSP: dev null, prod targeted allowlist — ACTIVE (DE-5) | **VALIDATED** — Use declarative tool UI catalog (shadcn components) rather than injecting HTML from tool output. CSP remains as configured |

### 1.10 Version/Dependency Risk

| Dimension | Community Consensus | Academic Consensus | Existing Decision | Status |
|-----------|--------------------|--------------------|-------------------|--------|
| **Agent SDK version** | v0.2.68+ silently injects `effort:medium` breaking agentic behavior; MUST set explicit `effort:high` (W2-J) | No academic position | Agent SDK sidecar — ACTIVE | **STALE** — CRITICAL: Pin Agent SDK and set explicit `effort:high` to prevent degraded agent behavior |
| **stream-json stability** | v2.1.79 partially fixes hang bug; manageable risk with timeout + SIGKILL (W2-F) | No academic position | stream-json for UI events — ACTIVE | **VALIDATED with CAUTION** — Hang bug partially fixed. Implement timeout watchdog (3 min per W2-H) + SIGKILL escalation |
| **SDK cold start** | Agent SDK 12s cold start is CRITICAL (W2-H) | No academic position | Agent SDK sidecar — ACTIVE | **CONFLICT** — 12s cold start unacceptable for learning UX. Mitigation: pre-warm sidecar at app launch, keep warm with heartbeat, lazy-connect on first user interaction |
| **Extended thinking** | StreamEvent does NOT emit when extended thinking is enabled (W2-F) | No academic position | No explicit decision | **NEW FINDING** — If using extended thinking (Claude models), stream events stop. Must handle gracefully: show "thinking..." state, fallback to polling, or disable extended thinking for tool-call-heavy interactions |
| **Windows child.kill()** | child.kill() unreliable on Windows (W2-F, W2-H); orphan processes accumulate (W2-H) | No academic position | Tauri Shell Plugin for process management — ACTIVE | **CONFLICT** — Known Windows bug prevents reliable process cleanup. Must implement Rust-side process group killing or use HTTP/WebSocket IPC instead of stdin/stdout |
| **Claudian/Tauri currency** | Claudian v1.3.70 CURRENT; Tauri 2.10.3 CURRENT (W2-J) | No academic position | Versions confirmed | **VALIDATED** — Both dependencies are current. No immediate upgrade needed |
| **graphiti-core CVE** | CVE-2026-32247 Cypher injection, upgrade to >= 0.28.2 (W2-J) | No academic position | graphiti in use | **STALE** — MUST upgrade immediately |

---

## 2. Cross-Cutting Synthesis

### 2.1 Architecture Convergence Points

All 10 Wave 2 agents converge on these architectural principles:

1. **Event-driven tool UI** — Tool calls rendered via typed events (tool_use/tool_result), not polling. AG-UI protocol, Vercel AI SDK, and Claudian all use this pattern.

2. **Hook-based observability** — PreToolUse/PostToolUse hooks serve dual purpose: security gating AND learning event extraction. This is the integration point between tool call UI and Observer.

3. **Collapsible block UX** — Collapsed-by-default tool blocks with expandable details. Companion and Claude Code set the community standard.

4. **fire-and-track with Outbox** — Local SQLite WAL write-ahead → async Graphiti persistence. No data loss even under network/service failures.

5. **OTel-based observability** — OpenTelemetry GenAI semantic conventions as the standard, extended with AgentTrace's three-layer model for learning-specific spans.

### 2.2 Key Conflicts Requiring Resolution

| # | Conflict | Wave 1 Decision | Wave 2 Finding | Resolution Needed |
|---|---------|-----------------|----------------|-------------------|
| C1 | Transport protocol | stream-json | Windows IPC 200ms penalty; WebSocket better on Windows | Decide: stream-json parse → WebSocket relay, or direct WebSocket from sidecar |
| C2 | Weakness taxonomy | 5-type (concept/reasoning/prerequisite/depth/metacognitive) | Not MECE; misses affective dimensions; not grounded in CDM/Bloom | Re-derive taxonomy from Bloom + CDM + error learning literature |
| C3 | SDK cold start | Agent SDK sidecar | 12s cold start CRITICAL | Pre-warm at launch + heartbeat keep-alive |
| C4 | Windows process kill | Tauri Shell Plugin | child.kill() unreliable on Windows | Rust-side process group killing OR WebSocket IPC |
| C5 | Extended thinking | Not addressed | StreamEvent stops emitting | Handle gracefully or disable for tool-heavy flows |

### 2.3 Novel Findings Not in Any Existing Decision

| # | Finding | Source | Impact |
|---|---------|--------|--------|
| N1 | Learning-annotated tool calls (show "why" relative to learning goal) | W2-G + W2-E (AgentTrace cognitive layer) + W2-D (OLM) | Unique differentiator — no competitor does this |
| N2 | BEA 2025 4-dimension Observer extraction schema | W2-D (50+ teams, standardized benchmark) | Structured extraction template for Observer prompts |
| N3 | LLM summaries significantly improve observability UX (empirical) | W2-D (learning analytics research) | Tool call summaries should be LLM-generated natural language, not raw JSON |
| N4 | Small LoRA-finetuned model can exceed GPT-4 for misconception detection | W2-E (Misconception GRR) | Observer may not need large model; reduces latency/cost |
| N5 | pendingTools Map buffering reduces DOM jitter | W2-I (Claudian StreamController) | Critical UX pattern for multi-tool sequences |
| N6 | Graphiti bi-temporal model synergizes with Outbox retry pattern | W2-D (Graphiti paper) + W2-C (Outbox pattern) | Late-arriving events handled naturally via ingestion-time tracking |

---

## 3. Incremental Question Queue

### P0 — Must Confirm Before Write-Back (Blocking)

**P0-1. Transport protocol: stream-json vs WebSocket for sidecar→frontend**

> Wave 2 found that Windows binary IPC has a 200ms penalty for large payloads (W2-H: KL-10), and Tauri Channels/WebSocket perform better for streaming (W2-C). The existing decision uses stream-json for event parsing. Two options:
>
> - **Option A**: Keep stream-json for CLI output parsing, relay parsed events to frontend via Tauri Channel/WebSocket (two-hop)
> - **Option B**: Sidecar exposes WebSocket directly, frontend connects (one-hop, bypasses Tauri IPC penalty)
>
> Solo IDE (W2-B) uses identical architecture (Tauri2 + Node.js sidecar + React) in production with Option A pattern.
>
> **Recommendation**: Option A (stream-json parse in Node.js sidecar → Tauri Channel to React). Proven by Solo IDE. Keeps Tauri as the single IPC surface. The 200ms penalty applies to large binary payloads, not small JSON events.

**P0-2. Tool call state machine: adopt Claudian's 4-state model?**

> Claudian uses `pending → running → completed | error | blocked` (W2-I). The `blocked` state is critical for PreToolUse hook permission prompts. Vercel AI SDK uses a simpler 3-state model without `blocked`.
>
> **Recommendation**: Adopt Claudian's model. The `blocked` state is essential for learning context (user may need to confirm before a tool modifies their learning graph).

**P0-3. Observer trigger: PostToolUse hook as primary extraction point?**

> Community consensus (W2-B) and Claudian implementation (W2-I) both use PostToolUse hooks. Academic support from AgentTrace (W2-E). The Observer would fire on every PostToolUse event, extract learning evidence using BEA 2025 4-dimension schema, and write via fire-and-track Outbox.
>
> **Recommendation**: Yes, PostToolUse is the primary trigger. Supplement with: (a) conversation turn end, (b) error/blocked states, (c) explicit user "I'm confused" signals.

**P0-4. graphiti-core CVE-2026-32247: approve immediate upgrade to >= 0.28.2?**

> Cypher injection vulnerability. Student learning data is stored in Graphiti. This is a security-critical upgrade.
>
> **Recommendation**: Upgrade immediately. No alternative.

### P1 — Should Confirm (Affects Write-Back Quality)

**P1-1. Learning-annotated tool calls: add "why this tool was called" to UI?**

> No competitor does this (W2-G). Academic support from AgentTrace cognitive layer (W2-E) and OLM research (W2-D). Would show learners not just "tool X was called" but "tool X was called because you seem to have a misconception about Y".
>
> **Impact**: Significant UX differentiation. Requires Observer integration with tool call renderer. Adds ~30% complexity to tool call UI.

**P1-2. Weakness taxonomy revision: re-derive from Bloom + CDM?**

> W2-D found the 5-type taxonomy is not grounded in any established CDM/ITS framework, overlaps exist (reasoning error can stem from misconception), and affective dimensions are missing.
>
> **Impact**: Affects Observer extraction schema, memory structure, and OLM display. Not urgent for initial tool call UI but should be resolved before Observer goes to production.

**P1-3. SDK cold start mitigation strategy?**

> 12s cold start (W2-H) for Agent SDK sidecar. Options:
> - **A**: Pre-warm at app launch (12s delay at startup, but instant thereafter)
> - **B**: Lazy warm on first chat open (12s delay on first interaction)
> - **C**: Background warm with progress indicator
>
> **Recommendation**: Option C. Show "Preparing AI assistant..." with progress bar during warm-up. Pre-warm starts at app launch but doesn't block UI.

**P1-4. Collapsible tool block UX: adopt Companion gold standard?**

> Companion pattern (W2-B): collapsed by default, expand on click, syntax highlighting for code blocks, one-line summary when collapsed. Add LLM-generated natural language summary per W2-D empirical evidence.
>
> **Recommendation**: Yes, adopt Companion pattern with LLM summary enhancement.

**P1-5. Agent SDK effort flag: set explicit effort:high?**

> v0.2.68+ silently injects `effort:medium` which degrades agentic behavior (W2-J). Must explicitly override.
>
> **Recommendation**: Always set `effort:high` in SDK configuration. This is a one-line fix with significant behavioral impact.

### P2 — Can Defer (Low Priority)

**P2-1. OTel integration: adopt OpenTelemetry GenAI semantic conventions?**

> Strong community and academic consensus (W2-B, W2-D, W2-E). Not blocking for MVP tool call UI but important for observability dashboard and debugging.

**P2-2. Small model LoRA for Observer: evaluate feasibility?**

> W2-E shows small fine-tuned models can exceed GPT-4 for misconception detection. Could reduce Observer latency from seconds to milliseconds. Requires training data collection first.

**P2-3. Extended thinking handling strategy?**

> StreamEvent stops emitting during extended thinking (W2-F). Need a fallback: show "thinking deeply..." state, use polling, or disable extended thinking for tool-heavy flows.

**P2-4. Windows process group killing implementation?**

> child.kill() unreliable on Windows (W2-F, W2-H). Need Rust-side implementation using Windows Job Objects or `taskkill /T /F` workaround. Not blocking for initial dev (dev mode works), but required for production.

**P2-5. Graphiti write success feedback UX?**

> Show subtle indicator when learning memory is saved vs pending. OLM principle supports transparency. Not blocking but improves learner trust.

---

## 4. Status Summary

| Category | Validated | Conflict | New Finding | Stale |
|----------|-----------|----------|-------------|-------|
| Tool call UI rendering | 2 | 0 | 2 | 0 |
| Event stream transport | 1 | 1 | 0 | 0 |
| State machine model | 0 | 0 | 3 | 0 |
| Collapsible UI | 0 | 0 | 3 | 0 |
| Observer trigger | 1 | 0 | 1 | 0 |
| Memory write reliability | 1 | 0 | 2 | 0 |
| Observability standard | 0 | 0 | 3 | 0 |
| Misconception detection | 1 | 1 | 1 | 0 |
| Security/permissions | 1 | 0 | 0 | 1 |
| Version/dependency | 2 | 2 | 1 | 2 |
| **Total** | **9** | **4** | **16** | **3** |

**Overall**: 9 decisions validated, 4 conflicts requiring resolution, 16 new findings to incorporate, 3 stale items needing immediate action.

---

## 5. Recommended Architecture Sketch (Based on Synthesis)

```
User Interaction (React)
    ↓ chat message
Tauri Shell → spawn Claude CLI sidecar (Node.js)
    ↓ stream-json parse
Node.js sidecar processes SDKMessages (21 types)
    ↓ Tauri Channel (typed events)
React Frontend receives events:
    ├─ content_block → ChatRenderer (markdown/code)
    ├─ tool_use → ToolCallRenderer (state machine: pending→running→completed/error/blocked)
    │   ├─ PreToolUse hook → permission check (allow/deny/ask)
    │   ├─ Tool-specific renderer (10+ types via makeAssistantToolUI pattern)
    │   ├─ Collapsible block (Companion pattern + LLM summary)
    │   └─ Learning annotation ("why" context from Observer)
    ├─ tool_result → PostToolUse hook → Observer fires
    │   ├─ Observer: BEA 4-dim extraction (identify/localize/guide/actionable)
    │   ├─ Atomic learning event (A-MEM Zettelkasten style)
    │   └─ fire-and-track: SQLite WAL → async Graphiti write
    └─ rate_limit / error → status indicators

Observability layer (OTel GenAI spans):
    ├─ Operational: tool call timing, success/failure
    ├─ Cognitive: why agent chose this tool (AgentTrace)
    └─ Contextual: current learning state, mastery level
```

---

## Appendix: Source Cross-Reference

| Agent | Key Contribution to This Matrix |
|-------|-------------------------------|
| W2-A | GitHub production cases: opcode, assistant-ui, Vercel AI SDK, Claudian, Cline, AG-UI |
| W2-B | Community consensus: Solo IDE identical architecture, Companion gold standard UX, hook-based observability, OTel |
| W2-C | Technical blogs: AG-UI protocol, Tauri Channels > Events, fire-and-track Outbox, Pi dual payload, A2UI declarative |
| W2-D | Survey papers: 25 papers/6 themes, OTel standard, LLM summaries improve UX, learning analytics shift |
| W2-E | SOTA papers: AgentTrace 3-layer, XAGen tool UI, Misconception GRR, ECD framework |
| W2-F | Counter-evidence: CLI stream-json DOES provide fine-grained events (corrects assumption), hang bug manageable, extended thinking blocks events |
| W2-G | Competitors: 4 UI modes identified, collapsible+generative hybrid recommended, no competitor has learning observability |
| W2-H | Edge cases: 18 limitations (2 CRITICAL: SDK cold start + Windows kill), sidecar lifecycle gaps |
| W2-I | Implementation details: SDKMessage 21 types, Claudian skip-delta strategy, StreamController pendingTools, ToolCallRenderer 10+, hook 17 events |
| W2-J | Timeliness: graphiti CVE, Agent SDK effort:medium injection, Claudian/Tauri current |
