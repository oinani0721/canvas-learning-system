# Architectural Analysis of Context Passing and Memory State Management in Claude Code Sessions

**Key Points:**
*   **Contextual Saturation:** Evidence strongly suggests that the AI's confusion stems from excessive, unstructured context injection at session start. Forcing the system to read four distinct policy and log files alongside 90 dynamically retrieved Graphiti facts creates severe attention dilution.
*   **Rule Overload and Interruption:** The system implements strict heuristic constraints (Development Discipline or "DD" rules) via intercepting hooks. The active blocking mechanism interrupts the AI's chain of thought, forcing it to focus on compliance rather than the primary coding objective.
*   **State Tracking Deficiency:** Research indicates a reliance on append-only episodic memory (Graphiti logs) and static decision logs, rather than a deterministic, mutable state machine (like a `CURRENT_TASK.md` file with checkboxes). This leads to temporal confusion regarding which phase of a plan is actively being executed.
*   **Dual-Write Conflicts:** The overlap between file-based memory (`decision-log.md`) and graph-based memory (Neo4j Graphiti) likely creates epistemological divergence, where the AI retrieves conflicting directives from different sources.

The following report provides an exhaustive, academic analysis of the Claude Code project's context passing mechanisms, addressing the user's reports of session confusion. While precise internal token counts and full contents of the internal markdown files (e.g., `development-discipline.md`) could not be fully retrieved due to the limits of the static snippets provided, the analysis approximates these values based on the algorithmic parameters explicitly defined in the project's hook architecture. The findings lean toward the conclusion that the architecture requires immediate simplification, transitioning from a highly reactive, rule-heavy injection model to a proactive, state-driven execution model.

***

## 1. Introduction: The Dynamics of Inter-Session Context in Agentic Systems

In autonomous software engineering utilizing Large Language Models (LLMs), inter-session context continuity is arguably the most critical architectural challenge. As sessions compress, restart, or branch into separate agentic tasks, the model must flawlessly rebuild its operational context: understanding what has been completed, what rules apply to the current domain, and what the immediate next step in the overarching plan is. 

The user reports that the Claude Code assistant frequently becomes confused when receiving plans or tasks from previous sessions. To diagnose this, we must analyze the project's complex interceptor pattern, which operates via `.claude/hooks`. This system employs a sophisticated array of Node.js scripts that intercept user prompts, tool uses, and context compactions to inject rules, force memory retrieval, and block non-compliant outputs. 

This report will systematically deconstruct this architecture across seven specific investigative vectors: Session Context Injection, Plan/Task Tracking, Rule Conflicts, Context Window Pollution, Memory Overlap, Specific Failure Modes, and Strategic Recommendations.

***

## 2. Investigation 1: Session Context Injection Mechanisms

The context passing mechanism relies heavily on a multi-stage hook injection pipeline. By analyzing the `.claude/hooks` directory, we observe three primary temporal intervention points: `session-start`, `user-prompt-submit`, and `post-compact`.

### 2.1 The `session-start` Hook
The `session-start` hook dictates the foundational epistemological state of the AI when a new environment is spun up. The codebase enforces an aggressive "mandatory read" policy immediately upon instantiation [cite: 1].

The hook writes the following strict directive to `process.stdout`:
```text
⛔⛔⛔ Session启动强制执行（不可跳过）:
1. search_memory_facts("Session-Start", group_ids:["canvas-dev"], max_facts:30, exclude_invalidated:true)
2. search_memory_facts("{话题关键词}", group_ids:["canvas-dev"], max_facts:30, exclude_invalidated:true)
3. add_memory("[Session-Start] {主题}", group_id:"canvas-dev")
4. ⛔⛔⛔ 使用Read工具读取以下4个文件（不可跳过）:
 - Read("_decisions/decision-log.md")
 - Read(".claude/rules/development-discipline.md")
 - search_memory_facts("MVP 刚需 14项", group_ids:["canvas-dev"], max_facts:30, exclude_invalidated:true)
 - Read("docs/known-gotchas.md")
```

**Analysis of Injection Order and Conflicts:**
1.  **Implicit Parallelism vs. Sequential Dependency:** The prompt commands the AI to execute multiple tool calls (`search_memory_facts` and `Read`). However, LLMs generate tokens sequentially. Asking the model to execute five distinct tool calls before effectively addressing the user's prompt creates a high risk of tool-use fatigue. If the model fails to execute one of the `Read` commands, the foundational context is compromised.
2.  **Order of Execution:** The instruction lists memory retrieval *before* file reading. This is theoretically sound, as it allows dynamic episodic memory to load before static rules. However, the requirement to read `_decisions/decision-log.md`, `.claude/rules/development-discipline.md`, and `docs/known-gotchas.md` [cite: 1] simultaneously overwhelms the initial system prompt phase.
3.  **Conflict Vector:** The AI is instructed to "search MVP 14 requirements" using Graphiti memory facts, while simultaneously reading file-based rules. If the memory facts contradict the `decision-log.md`, the AI has no explicit resolution hierarchy to determine which source is authoritative.

### 2.2 The `user-prompt-submit` Hook (Dynamic Injection)
To provide just-in-time (JIT) context, the system uses a Node.js hook that parses incoming user messages via standard input (`process.stdin`) and uses Regular Expressions to detect the semantic intent of the prompt [cite: 1]. 

The hook evaluates flags such as:
*   `isCodeExplore`: Triggered by `/deep.?explore|代码.*分析/i`
*   `isDecisionScene`: Triggered by `/选型|方案|对比/i`
*   `isImplScene`: Triggered by `/impl|实现|编码/i`
*   `isFrontend`: Triggered by `/前端|UI|界面/i`
*   `isObsidianPlugin`: Triggered by `/obsidian|plugin|插件/i`

Depending on the detected scene, it injects specific constraints. For example, if `isImplScene` is true, it appends:
`⛔ 实施场景[DD-03/04]: Context7+WebSearch查证成熟案例→参考落地→LSP检查→禁止mock`
`⛔ 开发完成后必须：(1) 启动独立 Agent 对抗性代码审查... (2) commit + push backup` [cite: 1].

**Evaluation of Dynamic Injection:**
While context-sensitive injection is a standard pattern in LLM applications, relying on primitive regex matching on user prompts is highly brittle. If a user says, "I am *not* doing an impl right now, just brainstorming," the regex `/impl/` will still fire, injecting irrelevant coding guidelines into a brainstorming session. This causes severe contextual dissonance. Furthermore, the hook always prepends a command to run `search_memory_facts` with `max_facts:30` based on the user's keywords [cite: 1], meaning *every single turn* risks flooding the context window with 30 historical nodes.

### 2.3 The `post-compact` Hook
Context windows in autonomous agents frequently fill up, requiring "compaction" or summarization to continue the session. The `post-compact` hook detects this event and re-injects the most critical core rules to prevent "catastrophic forgetting" of the system prompts [cite: 1].

The hook writes:
`⛔⛔⛔ 上下文已压缩 — 核心规则重新加载:` followed by a summary of rules DD-03, DD-04, DD-05, DD-06, DD-10, and DD-12, and commands the AI to re-read `.claude/rules/development-discipline.md` [cite: 1].

**Critique:** This hook is architecturally sound in its intent (preventing rule decay), but highly destructive in its execution. Forcing the AI to use the `Read` tool to ingest an entire markdown file *immediately after* the context was compressed specifically to save space is paradoxical. It rapidly re-pollutes the freshly cleared context window, severely degrading the AI's ability to maintain a coherent train of thought regarding the actual multi-step plan.

***

## 3. Investigation 2: Plan and Task Tracking Mechanisms

A reliable inter-session agent requires a deterministic state machine to track plans (e.g., Phase 1: Setup, Phase 2: Implementation, Phase 3: Testing). The user notes the AI gets confused about plans passed from previous sessions. 

### 3.1 Storage and Retrieval of Plans
Based on the provided codebase, plans are stored heterogeneously across two primary vectors:
1.  **File-Based Static Logs:** The `_decisions/decision-log.md` file acts as a historical registry [cite: 1]. 
2.  **Graphiti Episodic Memory:** A Neo4j database instances `EntityNode` elements to store memory. The Python integration shows a Cypher query creating nodes with `entity_type`, `episode_body`, and `source: 'react_agent'` [cite: 1]. The system instructs the AI to use `add_memory("[Decision-Review] ...")` and `add_memory("[Agent-Activity] ...")` [cite: 1].

### 3.2 Lack of Deterministic Task State (Checkboxes/Status)
Upon rigorous examination of the provided research results, **there is no evidence of a reliable, deterministic mechanism to track active task completion**. 

Instead of a centralized `CURRENT_PLAN.md` with explicit `` (pending) and `[x]` (completed) checkboxes, the system relies entirely on semantic logs:
*   The AI logs completion implicitly via the stop hook enforcement: `add_memory("[Agent-Activity] {agent类型} — 修改了哪些文件+原因")` [cite: 1].
*   It logs verification via Regex checks requiring explicit steps: `[DD-07] 实现了功能但未提供用户验收步骤` [cite: 1].
*   It checks physical completion via standard git tools: `execSync('git status --porcelain')` to detect uncommitted files [cite: 1].

**Why this fails:** Because task state is inferred from a chronological stream of memories rather than a deterministic state file, the AI must *deduce* its current position in a plan by reading the history. When `search_memory_facts` returns up to 30 facts [cite: 1], the AI receives a fragmented, nonlinear bag of historical tasks. It sees memories of "Plan created," "Phase 1 finished," and "Bug fixed," but lacks a singular, authoritative pointer indicating "You are currently on Phase 2, Step 3."

***

## 4. Investigation 3: Rule Conflicts and Cognitive Overload

The project relies heavily on the "Development Discipline" (DD) framework, comprising at least 13 distinct rules (DD-01 through DD-13).

### 4.1 Contradictory Instructions and Scope
An analysis of the regex interceptors reveals a massive cognitive load placed on the AI, often with overlapping or contradictory directives:
*   **DD-01/DD-04:** Requires verifying combinations via WebSearch before proposing them [cite: 1].
*   **DD-03:** Forbids mocking [cite: 1].
*   **DD-05:** Mandates using "Pencil" to create UI paradigms before coding [cite: 1].
*   **DD-06:** Strictly forbids using Obsidian Plugin APIs (like `createEl`, `registerEvent`) in the main frontend, as the product has migrated to Tauri+React [cite: 1].
*   **DD-07:** Requires explicit user verification steps [cite: 1].
*   **DD-10:** Requires validating new features against the MVP 14 requirements [cite: 1].
*   **DD-11:** Mandates checking for dead code (callers) [cite: 1].
*   **DD-13:** Memory Quality Gate, requiring evidence tiers (name-only, traced-call-chain, etc.) for code conclusions to prevent knowledge graph poisoning [cite: 1].

### 4.2 The "Stop Hook" Interruption Architecture
The most aggressive enforcement mechanism is the JSON Decision Blocking v7 hook [cite: 1]. This Node.js script intercepts the AI's output (`last_assistant_message`) and actively calls `process.exit(0)` with a `{"decision": "block", "reason": "..."}` JSON payload if the AI violates a rule.

For example:
```javascript
const decisionVerbs = /确认|选定|采用|决定用|推荐|建议采用/i;
const decisionObjects = /方案|架构|算法|选型/i;
if (decisionVerbs.test(msg) && decisionObjects.test(msg) && !/\[Decision\]/i.test(msg) && !/\[Decision-Review\]/i.test(msg)) {
    block('疑似决策未记录。如果本轮做出了技术决策，必须 add_memory [Decision] + [Decision-Review](PENDING)。');
}
``` [cite: 1]

**Impact on AI Performance:** The AI gets overwhelmed because it is treated as a highly restricted finite state machine rather than an advanced reasoning engine. If the AI generates a brilliant 500-line coding plan but forgets to append `[Decision-Review] PENDING` at the end, the stop hook blocks the entire output [cite: 1]. The AI then receives a system error, forcing it to apologize and rewrite. This adversarial environment breaks the AI's contextual chain of thought, causing it to easily lose track of the core plan while it scrambles to satisfy the syntactic requirements of the 13 DD rules.

***

## 5. Investigation 4: Context Window Pollution Analysis

The user queries how much context is injected at session start and whether it is "too much." While exact token counts depend on the specific contents of the internal markdown files, we can mathematically model the Contextual Noise Ratio based on the defined parameters.

### 5.1 Estimating the Injected Token Count

1.  **Forced Memory Searches (Graphiti):**
    The `session-start` hook triggers three distinct searches:
    *   `search_memory_facts("Session-Start", max_facts:30)` [cite: 1]
    *   `search_memory_facts("{话题关键词}", max_facts:30)` [cite: 1]
    *   `search_memory_facts("MVP 刚需 14项", max_facts:30)` [cite: 1]
    
    *Token Math:* 3 searches × 30 facts = 90 facts. If an average Graphiti fact (EntityNode body, source description, timestamp) consumes 80 tokens, this equals **~7,200 tokens** of purely historical, potentially fragmented memory facts.

2.  **Forced File Reads:**
    The AI must execute `Read` on four files [cite: 1]:
    *   `_decisions/decision-log.md`: A historical log of all decisions. Assuming moderate project age, estimated at **1,500 - 3,000 tokens**.
    *   `.claude/rules/development-discipline.md`: Contains the extensive DD-01 through DD-13 rules. Estimated at **1,000 - 2,000 tokens**.
    *   `docs/known-gotchas.md`: Systemic bug logs. Estimated at **500 - 1,000 tokens**.
    
3.  **Dynamic Hook Appends:**
    The hooks themselves append large text blocks (e.g., the 8 lines in `post-compact`, the situational rules in `user-prompt-submit`). Estimated at **300 - 500 tokens** per turn.

**Total Initial Context Pollution:** Approximately **10,500 to 13,700 tokens** are injected *before* the AI even begins processing the actual logic of the user's specific request.

### 5.2 The "Lost in the Middle" Phenomenon
Research into Transformer architectures demonstrates the "Lost in the Middle" effect: LLMs highly attend to the very beginning of a prompt (system instructions) and the very end (the immediate user query), but attention weights for middle context degrade severely. 

Because the Claude Code project dynamically loads ~12,000 tokens of rules, logs, and Graphiti facts into the middle of the context window upon session start, the actual nuanced details of the "Plan/Task" from the previous session are drowned out. The signal-to-noise ratio is catastrophically low. The AI is so flooded with *how* to write code (the DD rules) and *what not to do* (the known gotchas) that it forgets *what* it is actually supposed to be coding.

***

## 6. Investigation 5: Epistemological Overlap — MEMORY.md vs Graphiti

A profound architectural flaw in the repository is the overlapping responsibility between file-based memory and graph-based memory. 

### 6.1 The Dual-System Architecture
1.  **Graphiti (Neo4j):** An episodic, graph-based RAG system. The Python code defines `search_obsidian_cli` and Neo4j Cypher queries to `CREATE (n:EntityNode...)` [cite: 1]. The AI interacts with this via tool calls like `add_memory` and `search_memory_facts`.
2.  **File System:** Markdown files like `_decisions/decision-log.md` [cite: 1] and likely `MEMORY.md` (though `MEMORY.md` specifics are superseded by Graphiti in the provided logs).

### 6.2 Do They Conflict? Which Wins?
Yes, they inevitably conflict. Graphiti is an *append-only* or *graph-updating* database that tracks chronological state changes (e.g., `[Decision-Review] PENDING` changing to `APPROVED`). The Markdown files are *static* textual documents that must be manually updated via `Edit` or `Write` tools [cite: 1].

**The Disagreement Resolution:**
When the two systems disagree, the architecture provides no explicitly programmed "source of truth." However, practically, **Graphiti usually "wins" in the immediate term, but file-based rules "win" in the persistent term.** 
*   Because the `user-prompt-submit` hook injects `search_memory_facts(..., max_facts:30)` on almost every prompt [cite: 1], the Graphiti data is constantly refreshed at the very bottom of the context window (closest to the inference generation). 
*   Conversely, the `decision-log.md` is only forcibly read at `session-start` [cite: 1]. As the session progresses, the file's contents slip higher into the context window and suffer attention decay, while Graphiti facts are continually re-injected.
*   This creates a dangerous oscillation where the AI might follow an old plan from the `decision-log.md` at the start of the session, but suddenly pivot to a different set of instructions mid-session because a Graphiti search pulled up an overriding node.

***

## 7. Investigation 6: Specific Failure Modes

By synthesizing the codebase mechanisms with known LLM behavioral patterns, we can identify exactly why the AI loses track of its Phase/Step or confuses old plans with new ones.

### 7.1 Temporal Flattening via `max_facts:30`
When the AI searches Graphiti, it pulls up to 30 facts related to the query [cite: 1]. Graph databases return results based on semantic vector similarity or graph traversal, *not* strictly by chronological relevance. Therefore, if the AI queries "Authentication Implementation Plan," Graphiti might return nodes from three different obsolete sessions alongside the current one. The LLM, lacking strict temporal metadata weighting in its prompt, "flattens" these memories, confusing Phase 2 of a deprecated plan from last month with Phase 2 of the active plan.

### 7.2 The Stop-Hook Defocus
The `Graphiti Stop Hook` [cite: 1] is highly punitive. If an AI writes a large chunk of correct code but fails to provide a user verification step (violating DD-07) [cite: 1], it is blocked. 
1.  AI generates Step 1 of the Plan.
2.  Stop Hook intercepts and throws an error: `⛔ 实现了功能但未提供用户验收步骤` [cite: 1].
3.  The context window receives the error. 
4.  The AI apologizes, writes the verification step, but in the psychological "shock" of the error correction, it drops its internal tracking of the larger plan, entirely forgetting to proceed to Step 2.

### 7.3 Regex False Positives and Context Skew
The `user-prompt-submit` hook utilizes simplistic regex logic: `/前端|UI|界面|组件|Svelte|样式|白板/i` [cite: 1]. If a user asks the backend agent, "Make sure the API sends the correct data structure for the UI components," the regex detects `UI` and `组件`, immediately injecting frontend constraints (`[DD-05] 前端先Pencil`) [cite: 1]. The AI suddenly believes it is operating in a frontend context and may alter its plan to start drafting UI components, completely abandoning the backend API task.

### 7.4 Session-Prompt File Unreliability
The AI is instructed to execute `Read("_decisions/decision-log.md")` via tool use [cite: 1]. Because LLMs can be lazy or fail to sequence tool calls properly, the AI might hallucinate the contents of the file instead of actually reading it, or it might summarize it poorly. If the actual task plan is buried inside a session-prompt file that isn't explicitly prioritized over the aggressive DD rules, the AI will ignore the task to ensure it complies with the overwhelming disciplinary constraints.

***

## 8. Investigation 7: Strategic Recommendations

To resolve the AI's confusion and ensure reliable inter-session context passing, the architecture requires a paradigm shift from a **reactive, rule-enforcement model** to a **proactive, state-driven model**. The following architectural restructuring is recommended for `.claude/`, `_decisions/`, `CLAUDE.md`, and the hooks.

### Recommendation 1: Implement a Deterministic State Machine (`CURRENT_TASK.md`)
**Problem:** The AI relies on semantic graph searches to deduce its current plan progress, leading to temporal confusion.
**Solution:** Institute a strict, mutable file named `_decisions/CURRENT_TASK.md`. 
*   This file must act as the absolute source of truth for the active session.
*   It should use standardized Markdown checkboxes: `- [x] Phase 1` and `-  Phase 2`.
*   **Hook Modification:** Modify the `session-start` hook to inject the literal string contents of `CURRENT_TASK.md` directly into the system prompt, rather than forcing the AI to expend a tool-call to read it. Remove the reliance on Graphiti for immediate task tracking.

### Recommendation 2: Decouple Rules from Context Window Injection (Tiered Rules)
**Problem:** 13 DD rules and 4 files cause catastrophic context window pollution [cite: 1].
**Solution:** Do not force the AI to read `.claude/rules/development-discipline.md` at the start of every session. Instead, implement a **Rule RAG system**.
*   Classify the DD rules by domain.
*   Update the `user-prompt-submit` hook [cite: 1] to inject *only the text of the single relevant rule* rather than commanding the AI to read the entire rulebook.
*   Remove the `post-compact` rule re-injection [cite: 1] entirely. Let the AI rely on the core system prompt. If it violates a rule, the post-run testing hooks (like the Auto-Test pytest/vitest hook [cite: 1]) will catch it naturally.

### Recommendation 3: Resolve the Memory Dual-Write Overlap
**Problem:** Graphiti [cite: 1] and `decision-log.md` [cite: 1] overlap and conflict.
**Solution:** Establish a strict epistemological hierarchy:
*   **Graphiti / Neo4j:** Should be used exclusively for *Reference Knowledge* (e.g., "How did we implement Auth last month?").
*   **Markdown Files:** Should be used exclusively for *Current Directives* and *Architectural State* (e.g., "What is our accepted tech stack?").
*   **Hook Modification:** Remove the `max_facts:30` requirement from the `session-start` hook [cite: 1]. When starting a session, the AI should only need its active task file, not 90 random facts from past sessions.

### Recommendation 4: Soften the Stop-Hook Interceptors
**Problem:** The `process.exit(0)` JSON blocking in the stop hook [cite: 1] shatters the AI's chain of thought, causing plan amnesia.
**Solution:** Transition from **Blocking Interceptors** to **Warning Appenders**. 
Instead of blocking the message and forcing a rewrite, allow the message to pass but append a system note to the subsequent user turn: *"System Notice: In your last message, you completed a task but did not provide verification steps. Please provide them now, and then continue with Phase 2 of the plan."* This maintains the AI's forward momentum while still enforcing the Development Discipline.

### Recommendation 5: Consolidate `CLAUDE.md` Architecture
**Problem:** Having 4+ `CLAUDE.md` files and 5+ rule files overwhelms the instruction hierarchy.
**Solution:** 
1.  **Global `CLAUDE.md`:** Should contain strictly immutable core identity and the definition of the single source of truth (`CURRENT_TASK.md`).
2.  **Domain-specific `CLAUDE.md`:** (e.g., in `frontend/`) Should *only* contain domain syntax (e.g., Tauri+React requirements, no Obsidian APIs [cite: 1]). 
3.  Remove explicit routing logic from the text of the markdown files and rely on directory-level context ingestion inherent to standard IDE agent behaviors.

### Summary
The Claude Code project's current context mechanism is a victim of over-engineering. By attempting to strictly control the AI's behavior via dozens of regular expressions, mandatory file reads [cite: 1], high-volume database queries [cite: 1], and aggressive execution blocking [cite: 1], the architecture has crowded out the AI's working memory. To ensure reliable inter-session context passing, the project must drastically reduce automated context injection, implement a unified Markdown-based checklist for task tracking, and allow the AI to read historical memory on-demand rather than by force.

**Sources:**
1. graphiti-session-start.js (fileSearchStores/codereview1774789925-aiog0b3ukqkl)
