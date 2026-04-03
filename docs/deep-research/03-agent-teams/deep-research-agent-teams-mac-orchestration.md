# Orchestrating Claude Code Native Agent Teams on macOS for TDD Workflows in 2026

**Key Points**
*   **Experimental Status**: Agent Teams, introduced in Claude Code v2.1.32 (Opus 4.6), represent a paradigm shift from sequential to parallel execution, though they remain an experimental feature requiring manual configuration.
*   **macOS & tmux Integration**: Utilizing `teammateMode: "tmux"` provides isolated, observable environments for parallel agent execution. However, research suggests that users must navigate documented bugs involving `pane-base-index` mismatching and `isTTY` evaluation failures.
*   **TDD Enforcement**: Test-Driven Development (TDD) discipline can be rigidly enforced using native lifecycle hooks—specifically `TaskCompleted` and `TeammateIdle`—which act as programmatic quality gates. 
*   **Architectural Limitations**: Evidence indicates that nested teams are architecturally prohibited, limiting the recursive potential of third-party plugins like Superpowers' `subagent-driven-development`.
*   **Computational Cost**: Optimal team sizes lean heavily toward 2-3 agents; exceeding this dramatically inflates API overhead, as seen in Anthropic's $20,000 C-compiler experiment.

**Overview of Agentic Development**
The landscape of AI-assisted software engineering has transitioned from "vibe coding" (interactive, single-agent pair programming) to agentic orchestration. In this new model, a "Lead" agent delegates discrete tasks to specialized "Teammates" operating in distinct context windows.

**Test-Driven Execution**
By applying Test-Driven Development (TDD) principles to multi-agent swarms, engineers can constrain the non-deterministic nature of Large Language Models (LLMs). This report explores the exact configurations, workflows, and limitations of orchestrating these native Agent Teams on macOS in 2026.

---

## 1. Introduction to Claude Code Agent Teams

In early 2026, the release of Claude Opus 4.6 alongside Claude Code v2.1.32 introduced "Agent Teams," marking a transition from single-agent coding assistants to fully orchestrated multi-agent swarms [cite: 1, 2]. Unlike the previous "subagent" architecture—where specialized agents operated in isolated silos and reported exclusively to a parent orchestrator—Agent Teams enable peer-to-peer collaboration, shared task management via explicit file-locking, and dynamic inter-agent messaging [cite: 3, 4]. 

For software engineers on macOS, terminal multiplexers like `tmux` and iTerm2 have become the preferred display backends, as they allow developers to visually monitor the parallel reasoning of up to 16 agents simultaneously [cite: 5, 6]. However, operating at this frontier comes with friction. From token-cost explosions to complex environment bugs specific to macOS and `tmux`, achieving a stable Test-Driven Development (TDD) workflow requires highly specific configurations. This report systematically addresses the architecture, configuration, and practical execution of Claude Code Agent Teams for macOS-based TDD workflows in 2026.

## 2. macOS Configuration: Setting Up Agent Teams with tmux

To achieve true observability in multi-agent workflows, running Claude Code within `tmux` is essential. When properly configured, the `tmux` display mode allows the Team Lead to spawn teammates into separate split panes, providing an isolated execution context and visual stream for each [cite: 3, 7]. 

### 2.1. Exact `settings.json` Configuration

Agent Teams are an experimental feature and are disabled by default. You must explicitly opt in by modifying the global or project-level `.claude/settings.json` file [cite: 3, 7].

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "tmux",
  "disableAllHooks": false
}
```

While the documentation states that `"teammateMode": "tmux"` should auto-detect the multiplexer [cite: 1], a known bug in Claude Code v2.1.32+ on macOS causes the parser to occasionally ignore this setting in non-interactive setups, falling back to `"in-process"` mode [cite: 8, 9]. 

### 2.2. The `tmux.conf` Requirements

A critical configuration requirement pertains to window and pane indexing within `tmux`. Many modern `tmux` configurations (such as those powered by `tmux-sensible` or Catppuccin themes) set `pane-base-index` and `base-index` to `1` for ergonomic keyboard navigation [cite: 5, 10]. 

However, Claude Code's internal spawning mechanism assumes `0`-based pane indexing. When it dispatches its >350-character initialization payload via `tmux send-keys` to spawn a teammate, a `pane-base-index 1` setting causes the payload to target a non-existent pane, leaving the new agent stranded on a welcome screen [cite: 11, 12]. 

To prevent this, your `~/.tmux.conf` must either revert to 0-based indexing or temporarily override it during Claude sessions:

```tmux
# ~/.tmux.conf
# CRITICAL: Claude Code requires 0-based pane indexing for teammate spawning
set -g base-index 0
setw -g pane-base-index 0

# Recommended UX settings for monitoring swarms
set -g mouse on
set -g history-limit 100000
set -g renumber-windows on
set -g focus-events on
set -g default-terminal "screen-256color"
```

### 2.3. Startup Sequence and Execution

To bypass the `isTTY` macOS parsing bug that forces agents into `in-process` mode, developers should utilize a specific startup sequence. Explicitly passing the CLI flag `--teammate-mode tmux` or manipulating the `$TMUX` environment variable ensures the split-pane backend engages properly [cite: 7, 9].

**Startup Script (`claude-team.sh`)**:
```bash
#!/bin/bash
# Ensures clean startup of Claude Agent Teams in tmux

# Clear stale locks and task data to prevent ghost-state collisions
rm -rf ~/.claude/teams/* ~/.claude/tasks/*

# Launch inside tmux, forcing the teammate mode
tmux new-session -d -s claude-tdd
tmux send-keys -t claude-tdd "env CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude --teammate-mode tmux" C-m
tmux attach-session -t claude-tdd
```

## 3. Assigning TDD Roles and Managing Permissions

A robust Test-Driven Development (TDD) workflow requires strict separation of concerns: writing tests (Red), writing implementation (Green), and code review (Refactor). Claude Code Agent Teams facilitate this through role-based teammate prompting.

### 3.1. Defining TDD Teammates

The Team Lead operates as the orchestrator. By supplying a comprehensive initial prompt, the Lead utilizes the `TeamCreate` and `Task` tools to spawn specialized teammates [cite: 4, 13].

**Example Orchestration Prompt**:
> "We are implementing a new authentication module using strict TDD. Create a 3-person agent team. 
> 1. Spawn a 'test-writer' teammate responsible ONLY for writing Jest specifications based on the PRD.
> 2. Spawn an 'implementer' teammate responsible for writing the business logic to pass the tests.
> 3. Spawn a 'reviewer' teammate to run static analysis and verify architectural compliance.
> Do not allow the implementer to begin until the test-writer has completed the failing tests."

### 3.2. Permission Scoping and Limitations

A major architectural constraint of Claude Code Agent Teams is that **permissions are inherited at spawn time** [cite: 14, 15]. The documentation explicitly states: "All teammates start with the lead's permission mode. You can change individual teammate modes after spawning, but you can't set per-teammate modes at spawn time" [cite: 1, 15].

Because of this limitation, you cannot programmatically spawn a `test-writer` with write access while simultaneously spawning a `reviewer` in strict read-only mode during the `TeamCreate` phase. The standard workaround is to rely on **Delegate Mode** (`Shift+Tab`) for the Lead, which restricts the Lead to coordination tasks, and explicitly instructing the `reviewer` agent via prompt constraints to avoid executing file-write tools [cite: 14, 16].

## 4. Inter-Agent Communication: The `SendMessage` API

Unlike legacy subagents, which operate as fire-and-forget workers that only return a final summary to the parent [cite: 17, 18], Agent Teams utilize a peer-to-peer mailbox system [cite: 13, 19]. This is foundational for passing test specifications between agents.

### 4.1. The `SendMessage` Protocol

The communication layer is built on the `SendMessage` tool, which supports `message` (direct agent-to-agent), `broadcast` (to all teammates), and `plan_approval_response` [cite: 4, 17]. Messages are serialized to disk in `~/.claude/teams/<team_id>/inbox/` and injected directly into the receiving agent's context window as a `<teammate-message>` XML block [cite: 4].

### 4.2. Workflow for Passing Test Specs

In a TDD workflow, the dependency chain relies on a combination of the Shared Task List (`TaskUpdate`) and the `SendMessage` tool [cite: 4, 13].

1. **Task Locking**: The Lead creates two linked tasks: `Task A` (Write Auth Tests) and `Task B` (Implement Auth Logic). `Task B` is explicitly marked as blocked by `Task A` in the JSON task list [cite: 3, 20].
2. **Test Generation**: The `test-writer` teammate claims `Task A`. It writes `auth.test.js`, executes the test runner to ensure it fails (Red phase), and commits the file.
3. **Peer Notification**: The `test-writer` uses the `SendMessage` tool to directly ping the `implementer`: 
   * *"Payload: Tests for the auth module have been written to src/auth.test.js. The test suite is currently failing with 4 missing implementations. I am marking Task A complete."*
4. **Task Unblocking**: The `test-writer` calls `TaskUpdate` to mark `Task A` complete. `Task B` automatically unblocks [cite: 3, 21].
5. **Implementation**: The `implementer` agent receives the `<teammate-message>`, claims `Task B`, reads `auth.test.js`, and begins writing the source code to achieve a passing state (Green phase) [cite: 17, 21].

## 5. Known Bugs and Workarounds on macOS

Deploying experimental Agent Teams on macOS in 2026 involves navigating several known architectural and display bugs.

### 5.1. The `pane-base-index` Swallowing Bug

As noted in section 2.2, if `tmux` is configured with `pane-base-index 1`, Claude Code fails to properly target the new pane with its initialization prompt. The prompt (>350 characters) is swallowed, and the agent hangs at the welcome screen [cite: 11, 12]. 
* **Workaround**: Temporarily execute `tmux set pane-base-index 0` before initiating the `claude` command, or permanently update `~/.tmux.conf` [cite: 12].

### 5.2. Context Compaction and Memory Loss

A critical divergence exists between `in-process` teammates and `tmux` teammates regarding context compaction. In Claude Code, when an agent nears its 200k+ token context limit, it runs a compaction algorithm to summarize and truncate history. 
* **The Bug**: This compaction pathway is only implemented for full CLI processes. `in-process` teammates lack the compaction loop. If an `in-process` agent hits its context limit, the Node.js subagent runner simply crashes and the agent dies silently without recovery [cite: 9]. 
* **Workaround**: This makes the use of `teammateMode: "tmux"` absolutely mandatory for complex TDD workflows, as `tmux` teammates run as full, independent CLI processes capable of proper context compaction [cite: 9].

### 5.3. iTerm2 Native Split Pane Issues

While `teammateMode: "auto"` or `"tmux"` is supposed to natively support iTerm2 split panes, it frequently falls back to `in-process` mode. 
* **Root Cause**: The integration relies heavily on the iTerm2 Python API [cite: 1, 22]. 
* **Workaround**: Users must install the `it2` CLI (`pip3 install it2`), navigate to iTerm2 Settings → General → Magic, and explicitly enable the "Python API" [cite: 4, 7]. If this fails, running a lightweight `tmux` session inside iTerm2 remains the most reliable fallback.

## 6. Community-Validated Configurations

The developer community has rapidly standardized best practices for Agent Teams. Two primary GitHub repositories stand out as the gold standard for configurations in 2026.

### 6.1. `FlorianBruniaux/claude-code-ultimate-guide`

Maintained with over 200 commits, this repository is highly regarded for its deep architectural dives and production-ready `.claude/settings.json` templates [cite: 23, 24]. The repository validates the necessity of isolated git worktrees for parallel agents to prevent constant merge conflicts [cite: 19, 25]. It also provides comprehensive `CLAUDE.md` templates that dictate rules of engagement for multi-agent swarms [cite: 24, 26].

### 6.2. `disler/claude-code-hooks-mastery`

With over 3,000 stars, this repository specializes in programmatic control over Claude Code via Hooks [cite: 27, 28]. It introduces the "Builder/Validator" pattern, which is the foundational architecture for TDD in Agent Teams. The repository demonstrates how to write `PreToolUse` hooks to block dangerous bash commands (e.g., `rm -rf`) and `PostToolUse` hooks to trigger formatters automatically, ensuring agents do not pollute the codebase [cite: 27, 29].

## 7. Enforcing TDD Discipline via Agent Teams Hooks

To ensure AI agents adhere strictly to TDD (and do not fall into the trap of writing implementation before tests), developers must utilize Claude Code's native Hook system [cite: 30, 31]. Agent Teams introduce two specific hook events: `TeammateIdle` and `TaskCompleted` [cite: 1, 30].

### 7.1. The `TaskCompleted` Quality Gate

The `TaskCompleted` hook fires the moment an agent attempts to mark a task as done. By executing a shell script that runs your test suite, you can deterministically block the AI from moving forward if the code is broken. If the shell script exits with code `2`, the completion is rejected, and the stderr output is fed back to the agent [cite: 30].

**Example `settings.json` Hook Binding**:
```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "type": "command",
        "command": "./.claude/hooks/tdd-gate.sh"
      }
    ]
  }
}
```

**Example `tdd-gate.sh` Implementation**:
```bash
#!/bin/bash
# tdd-gate.sh - Enforces TDD by requiring passing tests before task completion

echo "Running test suite validation..."
npm run test -- --passWithNoTests

if [ $? -ne 0 ]; then
    echo "QUALITY GATE FAILED: Test suite contains failing tests." >&2
    echo "You must fix the implementation so that all tests pass before completing this task." >&2
    exit 2 # Exit code 2 blocks the task completion
fi

echo "QUALITY GATE PASSED."
exit 0
```

### 7.2. The `TeammateIdle` Hook

When an agent runs out of work, the `TeammateIdle` hook triggers [cite: 30]. In a TDD workflow, an implementer might finish its task early. Instead of shutting down, an exit code `2` can automatically redirect the idle agent to run a linter, generate documentation, or review a peer's pending pull request, maximizing resource utilization [cite: 30].

## 8. Combining the Ralph Outer Loop with the Agent Teams Inner Loop

The "Ralph Loop" (popularized by `snarktank/ralph`) is a viral autonomous development pattern. It is essentially an infinite bash loop (`while :; do cat PROMPT.md | claude-code; done`) that continuously respawns a fresh AI session to chip away at a `prd.json` file until all requirements are met [cite: 32, 33].

### 8.1. The Outer vs. Inner Loop Architecture

*   **Outer Loop (Ralph)**: Manages state persistency across macro-iterations. It reads `prd.json`, extracts the next macro-feature, runs the AI, checks for completion, and archives the run [cite: 32]. This solves the "context rot" problem by ensuring every new feature begins with a completely fresh LLM context [cite: 32, 34].
*   **Inner Loop (Agent Teams)**: Parallelizes the immediate execution of a specific feature. When Ralph spawns Claude Code, Claude Code acts as the Team Lead, spinning up a swarm of 3 agents to write tests, frontend, and backend simultaneously [cite: 25, 34].

### 8.2. Has it been combined?

Yes. The community refers to this as Tier 2/Tier 3 orchestration [cite: 25, 34]. When a developer executes `ralph.sh --tool claude`, Ralph feeds a specific slice of the PRD to Claude Code [cite: 32]. If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set, the prompt explicitly instructs Claude: *"Use an Agent Team of 3 to implement this PRD slice."* 

The Team Lead breaks the PRD slice into granular tasks, the teammates execute them in parallel `tmux` panes, the Lead synthesizes the final review, and exits. The Ralph bash script then analyzes the git diff, marks the PRD item as done, clears the context, and loops to the next feature [cite: 34, 35]. This hybrid approach combines the infinite stamina of Ralph with the horizontal speed of Agent Teams.

## 9. Optimal Team Size: Computational Cost vs. Coordination Overhead

A pressing question regarding Agent Teams is scale. While Anthropic successfully demonstrated a 16-agent team, community consensus strongly advises against this for daily use [cite: 6, 36].

### 9.1. The Reality of Token Burn

Every teammate spawned is a distinct, fully-featured Claude Code instance. They all require their own context windows. A single intensive session can consume ~200,000 tokens. A team of 5 agents working simultaneously will burn upwards of 1.2 million tokens per execution loop [cite: 13]. In Anthropic's 16-agent C-compiler experiment, the swarm consumed 2 billion input tokens over two weeks, costing nearly $20,000 [cite: 6, 13].

### 9.2. Community Consensus: 2-3 vs. 4-5 Teammates

*   **2-3 Teammates (The Sweet Spot)**: The community heavily favors 2-3 teammates (plus the Lead) [cite: 5, 25]. This maps perfectly to MVC or TDD patterns (Frontend/Backend/Tests, or Implementer/Reviewer). Coordination overhead is minimal, inter-agent messaging is clean, and API costs remain manageable [cite: 25, 37].
*   **4-5 Teammates**: At 4-5 agents, developers begin to see diminishing returns. The shared task list becomes volatile, agents frequently step on each other's toes causing Git lock contentions, and the "inbox" becomes noisy [cite: 5, 36]. 
*   **Rule of Thumb**: Allocate 5-6 granular tasks per teammate. If you cannot extract 15 distinct, non-overlapping tasks from your prompt, you do not need 3 teammates [cite: 13, 15].

## 10. Superpowers `subagent-driven-development` inside Agent Teams

The `Superpowers` plugin is a popular Claude Code extension offering a `subagent-driven-development` skill. It reads an implementation plan and dispatches fresh subagents for each micro-task, enforcing a two-stage review (spec compliance, then code quality) [cite: 38, 39]. 

### 10.1. Architectural Compatibility

**Can Superpowers run *inside* an Agent Team?** 
Strictly speaking, **no**. The Claude Code v2.1.32 architecture enforces a strict hierarchy: *"No nested teams: teammates cannot spawn their own teams or teammates. Only the lead can manage the team"* [cite: 1, 14, 15]. 

Furthermore, `subagent-driven-development` relies on the legacy `Task` tool (subagents) rather than the peer-to-peer Agent Teams mechanism [cite: 39, 40]. If a spawned Teammate attempts to execute the `subagent-driven-development` skill, the Claude Code binary will block the operation, as subagents/teammates lack the authorization to recursively spawn children [cite: 41].

### 10.2. The Correct Implementation Pattern

To leverage Superpowers alongside Agent Teams, the workflow must be inverted:
1. The human user invokes the `Superpowers` planning skill to generate a structured implementation plan.
2. Instead of using the Superpowers subagent execution skill, the human instructs the **Team Lead** to parallelize the generated plan using the native Agent Teams infrastructure.
3. The Team Lead manually creates the 2-stage review tasks in the Shared Task List, assigning them to native Agent Teammates [cite: 17, 42].

## 11. Real Production Experience Reports

The introduction of Agent Teams has yielded significant, publicly documented production outcomes, shifting the paradigm from hypothetical AI assistance to autonomous engineering operations.

### 11.1. Anthropic's 100,000-Line C Compiler

The most definitive proof of concept was executed by Anthropic researcher Nicholas Carlini. Over two weeks, a swarm of 16 autonomous Claude agents built a 100,000-line C compiler written in Rust [cite: 6, 13]. 
*   **The Oracle Pattern**: The agents were provided with the standard GCC compiler to act as a ground-truth "oracle." The agents continuously ran their output against GCC's test suites; if behavior mismatched, they re-iterated [cite: 43].
*   **The Result**: The AI-generated compiler successfully compiled the bootable Linux 6.9 kernel, QEMU, FFmpeg, and SQLite [cite: 6, 13]. 
*   **The Cost**: The endeavor cost approximately $20,000 in API credits, proving that while autonomous engineering at scale is technically feasible, the financial economics require optimization [cite: 6, 13].

### 11.2. Bootstrapped SaaS Acceleration

Independent developers and "bootstrapped SaaS founders" report utilizing 2-3 agent teams to ship full features overnight [cite: 44, 45]. By isolating frontend, backend, and documentation into parallel `tmux` panes, solo developers act as "Tech Leads," focusing solely on prompt engineering, architectural review, and defining acceptance criteria, while the Agent Team handles the boilerplate generation [cite: 45]. Reports indicate that utilizing cheaper models (like Claude 3.5 Sonnet) for the implementation teammates, while reserving the expensive Opus 4.6 model for the Team Lead, drastically reduces costs while maintaining high architectural fidelity [cite: 13, 30].

## 12. Conclusion

The integration of Claude Code Agent Teams on macOS presents a formidable evolution in software engineering. By mapping traditional TDD roles—test-writer, implementer, and reviewer—to independent, concurrent AI agents communicating via the `SendMessage` API, developers can enforce deterministic quality gates on non-deterministic models. 

While the ecosystem in 2026 demands careful navigation of known macOS `tmux` bugs and strict token-budget management, tools like the Ralph Loop and programmatic Hooks provide the necessary scaffolding to make this a production-ready reality. Ultimately, Agent Teams transform the human developer from a pair-programmer into an orchestrator, scaling individual output to the level of a complete engineering squad.

**Sources:**
1. [claude.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHa-6ddDw3tSOW5PHYLyj6W7gp2ovxlVCgSGnA1S6ZXHphVt2vP6lwMK1HkI1IO5cvSkPu1UQVwSEpC8ZanbdYkK35gk0wiD3THhRa2Y8FknDTNxLFFAQXACUc-v9owAVI=)
2. [turingcollege.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFUUOuSu5DFKd62pe7gDnT_evbjaVjnAP42d6IiqtpndrYhkzTIL_Qrr3OmptAmJ_7c3o75VGXjnLNG0MEdQHE_gxu7TzyyM7obJpEJEoWgRbhItRVWR7C7eip40OoLe2dryPeuh3Uior8QyrZ-cHBRxJXHCA==)
3. [substack.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGqNTYJUUPTO99Cc_EaAqjYo07tZxojjEps9cmCz9iHFaioXbjibWx6rWGhCC5mkdGT34P8m2WTxuK1zBf2tbi69xIAo1jMJBKui4Rqy2R64QL1XjXFLD3yIUevnoChseFGjEQHkJlo4ldiSbi1gO4C6w==)
4. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEESuQRXYfvL8T48s28mR8rTysJ40gwM5Y7OfOBtr_e3X1CD9BPm7qlG_BH5NUPU8H-BTN03IOakKvqPJCL5C8q3Shz66U2MnRGVPv0-BgG52g198EhdiKeEzC62ciYigWHj14j4bnt41Ue4j2ciu6EubODd6paXyNSY8QqsyZDmo2UzLFZzQ6CVOSthOhyEaBuphHuTw==)
5. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHQkJfOMRHypi5mUhaaO6k7ILvu75mHrsH862aT-DVoDqAvNZfME0yu47cI96H3VsQw-i2F6YxBOIHgijDiGQWKVuq49OvmYS1Lx7U51XbnPPw0rk23ynFC_-73ZyIx36gYozuTXOCTk7saSc9UJcxYJGqXxNWSKIL_Lr9uqPN0nA2UVyMJsKPBdR0Lga4hq2UfAzHCmciKvvu5)
6. [faun.dev](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEy0zLdzIoUOWyjQGOckaIlxMfJeyY8QMZI-gUNHhKO1iNF2H4C8eLfKxeCHWOy-3xmt5-XOXpCJFkqOjpfdNRRQzdPmsRpiaKm_AVLMDptZ2Jv6IESVnkhc4h9ZCAKQJ0Rix5d_eBAPQIN-FAYB6ZFr7UL0AkxkNirj_RYPAnH6uALQzlTBNBFKZ4fB0FEvCX5PFfZnYed9HEP63fnPgwM)
7. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG2mNvX4CjRM99fV23V2MR2o2CtwmfVCeX8kH14u876y_WrqcePzirUlwAVP4kjb9dG1PK812fJauqM0gVIX3FniW3hcM1u1aPno_KdxQm84wuToB3c-NhYMKp7Mz2G_pvGvk0fgYPsKNADVHzqxXU04hYV2a4ifzciiVb0D58zEx5QIzyKsHe3au5sb8fC0FM-TggsY2EdINEqPl_I8ZsTd6Djr9nVD0MM)
8. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEJIys599cedbMhPt4B1BZ4ZI9DyuCjotyy705T2TTbyY_S1O1I0ME2M_uW6CDMMxqzZilwxweT4q5UUqtbAtirNrLIT95fVONWXVgzVrCNl2F3Fji-aFQ-CpIipd5lp4jzm_nXMmxTYUMacA==)
9. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF2z0QTf4WfR7SB8TbeSHsS_UpJYsSt_NLD4wvbiYzAWFNMPsQQcRhS7D6V77I6X7ullYUs2fgIkc30p5zhCKs_KYZDEO9qtFGmbARr0xrm01MCQAHZbhJxYrkJubyGDmWQv_DjCPG7Is3wdaRz5UdlEnX3fNENR_OlLllCWMT2L9dIAwGJIEJlrNTZYGkKZkbQl7U5WWDWFTNGhjVT)
10. [go.dev](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGQKaYfRkzJvwhBKJ_EeFN1xgOp_ehRZD4Y0LzUz_Qcgr-9I6J_vIiQTvwz487E89D3Yr7IGjCQZo0ZTh-rArcnJedlmrZC-Gv2B81O5o2o8VsuPKi0yn48FC8XlDBNt5oQyGk=)
11. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFtcYdsm9QjE14NCziHVdWym7YibQgInwNYc5VtO8lESiNZCard-3ixFK-PfP7AaiEBvYKjh8h6anLKhmfRRDN2mMVqN_HgtmNtsgi-KL-gMNryTI4VRTOYoVAL2UmKuO__PCzAHr-9Yu5cyg==)
12. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHk0-oSyxVXbjqiqmugVZGejC4bhtLaOh27CTi9vhH-99jKrO7QIrQ_yMgGeXXuCh-yVQait9B_kE3GSnuGR_BV1oCo4moDdk-Vw7dtN4a3iIsZJGCA39J_RwcolxR23ZbIFg__OOJjsnnD8Q==)
13. [prg.sh](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG2BxEGFCHjB40sTIdTe2nViJS-lWWPolGbIJgqSuKand7prwzexcbXnIYrjmC9XlqA7KHjby7bSyHm9ciIhD3TgdB8vtPzaDVD6PKllKWMkP_Atzx38J6exO7Z5R8JxHnO)
14. [panaversity.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE8fWplFHZednPSYJr_X4zDtlCRnGbaSBkajWSeXQstdyGsR7nugRayW3V2kxJ7dXHWzgd5MXPOy06i1jP9macTu2jMDDdArExGvmmBV64_ml_6NZcY4bgufeCLlATpsLSNyO8NoYO9CMrDGxkHbUttx2qJPPSAd_i9sL4-rL4mRSN_fDgJmz-eYPgGPTXGWIXctq3m)
15. [claudefa.st](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE6_bfEBn6DBXf0Ps0G4WsIO2qN--RlzkYUGxri-ewBlxahvRWbx0O9B6px_6ygX1jOS0G3td21X4ac7st672Zb52_6S2ErGL1Utvv-eOz066tL6lzXbKnNMDMFlZAT-gnqOs08jZL7JBBveLi3rBuiY0EMmaA=)
16. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEU7xiwuEbm8mSuAIJp-18cUwUgmweDklokM4lx1aWKqQncqlV6e-owbIGJkaWnlUhVoINmxSUpMt5VZL3ud1y8tmxl2AJcsyJvyZ2rMv9ZFpLpSHodm_0iNCNP86-8JY2-3ecpI0UkYE7_S3NwLLrqnRxfxpTB9NrOcIaDm2CcClIZVYVP5Wt8nBNFvec04qw8_VVKVMTyMr0g-qxC78hcplin8R0TelxcAQ==)
17. [alexop.dev](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHp2zCTWWLh-iXzSX5jwpbZkgV9InvZo6KHJw6QtwMhz0atLxkoZeNHrPAiDQzx0PL9-VwTqCBudRwG6WhEVsY5pwJcT10pdYqQ7D-S191p0SgK7_WrJo1U44jAnSa4msblqVR1vKMStLQU7j9Ga8Z4VuyQlx4sMsaOrPLRLPI=)
18. [addyosmani.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFgNjXz2DICElFgLN8ouxr4zILT46GXlU5Kqrl1_9O4tpol278XS0Z37jiOPEuBClgW2m6tSEOo3Ml02x58rUy108J82meAxByG-zFrCoo2WIi4kPoHnSAs_Jw6pVEgxr5sMfITaU4UmXs=)
19. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF_9lYm7q3F25jxdR5QKVfStFyCQZN89SQUoYq4WLgi_3K59WZ4SnZvPZV2fBPkjOwkwc9FKbyeb0bx3PZbLVaoBHXwaYItCACkJM558qO5BgUp8vEyXKm5n1erYtyh9mgdmW5dwlXBxeiJF6KLbA3pre7fcQrdm4uo6pz2P-Q2YZ1sStk2GozXPFKeOwsuux4n0-tZgvO3G3PfUA==)
20. [addy.ie](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFW3d9db-R1xo4iws47ThIVmGOD7m0Io-g7U71sagnZN4nl47VAclCcjNrmY7WrQGIDRRIf65wpJjJOqBUhDI73HX7GedQjjzRTBQwEX37lCrkGLY2KOHVxYK-_zeFu-2nvP7fod5s=)
21. [aifreeapi.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG9zFQtfaHluiLPDXWIsY_qDJlly4WWLTdUzIaFiALPE1bwtW6QTb1ebA9AiO7rw5TKaV1GlOIP8Z1R_3zoNucfZq7ylg78_j66vPSBACmM-7mHzKmrSKTachX9gCFn1kemAxFcEZFS8kp_G6fJndM=)
22. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFTsMOVzm2QiO5eQwsX2jp60MInT-ZBGJNFREZFxKxvf6FvLDNBh8G0QNKZu_kyE_hmhu8dbdO8UfSBo5m7kftH_ytJRyUafx4em5Qa4TPR9Aws0Lne-7uhjLnGo_RsaDlmx9B10jzaheuyTw==)
23. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGXLXByGXIVOL95akrCGELdHVW-YrQOkYX5d2i_596FA7afZSSKAIMqK9sL-DFNaCq9-LKqjBnFjNgl1xbg4gIM-EX1SXOGK3uh6iZC6iOlFtJBm4Ms-8fEkZXIRIadD2_LPSFFsSlG2s1uCXTVGWJd8c4=)
24. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHFj8A75NOzMr5foUYT3wEwMPBrVmik_SMhQtC_e99_NfIyG5UF4TmGa_MLE4srQ3wXEnGNq5G8_pQen46QGh88mj9HX85ocShrcauhWoskFl_TC8V5EFOkIgRmj4TujZrCadgVXMax6Mm1WlXusA2cjaUY)
25. [addyosmani.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFiO-OMt9P70dgN-_U_7NzfavKejnzblHiAnk6rkx9T-c6gPw9jhmx2Zh1IX0mhgU2l2j026MoIL9AqzImHBXG3ZR9yhmVSYUs_FVIIp2jIbdCnOSxoXMoMYKoSPeFvkdLaW1pnRUY=)
26. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGDM2ZBzYHxqCw8ciKnab-t0iY-k14WxYZHr_MZ5jpJqOuqCEKuJMhon_MESDNaAVx9m-z-Ib0biJ6y3Gx-iiiP1fSd4sTP_9XpDcevL9JUOjtPqqFRiJjMXW0_uzZH7Zo=)
27. [ksred.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFb83ixm3ej4tgn5D-qOiIrxOSVMSi4YGgv1wqA6ZmnwJt8QLy6TE817syyuj0V3krd5JD6JIA8y7ruygAUbF8Lm-vJo171Z8VIP7agPqdWghuwTDgFHsjtteTQ3AmtfwNtihSNocEOL4NeWpdBcgcqaz755yLGe8CMX4ycuMVrErwf9gpL8VzjMO-evwYtfmAbgOTA)
28. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8SAQ_s09G_WPc9s7MDklJ6qBOz0pIhAR2aE4nXfsZwlT2V8CzfaISdoJqf6pzP36CFLu6KOndbInAUZ4pU2YWNYT1oEEL2lqXBKXtV1kTLCm1U8Z7t484cBLL5Pt6HSRVBrnZOffIuw==)
29. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGwKF1DpEXKORF_AuxQ6_cKlPpQ-zpT3y5zXHjocJgSdi-tZ6ZbVN8O9AW-CcoabTpzkuYORQYdLeZ8YvnrEDXE7I6l_cPZZM9NR0yhDnqoupGRON8twlgsyWUyivA4eFc=)
30. [claudefa.st](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH0H2GaHy9twbo1iyORhTjm69QBuc-CpXDgjUsb1F248a5K0ZH-R1FAgqVXz3JbAJudg9WkGt_lW53d9WTfdlHNOoekYFlXQ8X-IaWbnS6WvI_4GTE-eZ1Xxb-UllV-jC6AQxNvmQKHE9I9CMOIb_g=)
31. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE7N-K1zmGM-uOODqWXEtvFWi_j5dnQrAhtcBh4NKloFbyQJrOQCSgZtyNF_YQ7K5UhvcfGRBKSJamjpLTuk8adXaXGXYM05U1YzjFYAwVld9Pt9vV2aEyiaPPVdKurljs2exOTurI42U_BTeeN_dzzOC0chWOvg9inSokCYzeE)
32. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEbVfWper_qNkzuIZYrF11uKIrERct-eP6MnB1sHRNmk2IUJGGbJyprETk8HvyNqy06NeS5KiiHYWgeZ93yfZ6rZLRzL7JbQoySxiOyakIkrDQFBsuonq4=)
33. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFBKrL4I5h7xjEiM-M33fJ5fiyQYZR-VzHa9cAhTByKrAYZFPHc4WoFqAKnWr0DgI1RQHoBulRi-vkP6IWISRzqx9azboqRks6upKWeryqO3ct9DARuEc-DEpjBSitLVmLAeIIS19CYjK4pYV6SzFz9oNR61D3r6Um4N5DCUKt7FtmUtpJ8GbJc3BPIkG91J_o=)
34. [daviddaniel.tech](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG6hU6P29Xw3SWoaTE_gwGcCSpvwll_jTjdkWD19cTy0fNhw5muOKLp_2BPzBdYm1WmXzZijXyMVjfD0S9p5lOMZRAIZRpvCjIUY0DN2of17k8Gw1AD0OTrtHcAJDZqDJyWXk32Cq-ICoKirRLGou31rFTuLCyCmQ==)
35. [thetoolnerd.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHd_Xh_fAIpgKAEiI4c3-HoTNEukea-mUw40I7iF9TcH-dEQ8fkKstn3P7oeWk-NRrM6AIrrsnAct_I7bHXb6u8ojjDKnkzVI-6YHOBiYJi_PBFUgenJf15byna_k5XefZeCdAnk_S1KEwl9F-0xTA3pI9JlNRSxyU=)
36. [nxcode.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE2YqZ4fK5pXhOl15e7S5mt09LEvb_nR-6u1RHr6kDRGe64_UTBLvJXsUqpsYonhRS-eLkccw5d5-CkhT3v1UwTmMDGM1PwovO4kUyKe9cah-6Gzvnnx6144qDYrc1CMNciVCXfNKKkd6zvAJAf9MtamSoDbOdh4QEsEwotU9biNLkBySIad9So2cti3DeWnQ==)
37. [laozhang.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGcXbD-GYF9d3omkoZsWZ8Tkthj6ToafXON0oWmdalGasGK-l1skeNrIra6kTkz4dAr_Zq2uIV3rLyD4223CM3gB0Id-AHUs80lXtOz8lCpEDk7whCpF2RZ_CsDuDLIgDyogUoGE9BaKo1cbbvQNg==)
38. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEg2KWq5AH14oycJiSQJJWbW1e2D54uFS0h6JPXJHlpxYUqrEO9j_CTY33Zaqa0KuZwlxaIXlB70X9Fesg-xbj_q4cz9_ZjmyBsXE5LbdJ88-_qYmgD2F2nipcKwxb9orbJjs_P-Up2M4a233Z_ThY5-b_jLcV90n7bdaWxqa0SZN8Jbz4Wjac1VNtso-0Y)
39. [devgenius.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHvrdK99nMiXajsKmv66zZHAbuEZ1d6Zfx2u99mAMYHyWE0k848o-fZ9qeQvQy3I1cIjGp1HaWPPtVZXS33ZEdgKu9-V7W2JRxOU88Fe6bENxMukpe6WnhlmvRe23NiVf-aAuO1qRULPa9r6J3aRnEXVg_n0mVDUJXot_gS3nrNSmIDmGz82_4cybiPzGYJRZZ1qviThKlXhDEVev5YdTWyQAITKaEis2Nm4ogl)
40. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHIVXhSZ7Sy8Mnjj0hrKXSUG1zfZNSxX3d6cOghrX0-6C5_vSojLaJvkJYLbiYww-RmXFTe_v1oAbje1OPLJaYWLIrV4-QmBG_GgJU57JqNX0lzpYqi6YMUzI2_UcO9SITDkXQMcM13cHcePAnWLeIr_bxcx76I5DMr-knQHyKZ0-tSGg==)
41. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEr47IEee7v3nZtOyC4K0M1pjg21ETU7_XoIvDpOf7Xy_mfNP5gGeOaEjgIx0I_ZfVtYZgur6IBcOrlegiWM_eGmvH_sjV_-QUiNNoinMJB2Fk1hpsA0Gs2sbrIIoVMFkPCF_2HfWYbLXQK4g-E_rDedYa2p7vuSZdxVxMpIupYuTNeJ2_V4WLd8TMbSod6jtOhQNJ57bAh5YbT6Lts-xvimMXIphgYv-SIzozCmA==)
42. [fsck.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFSU1Wv3kHOvtl6SWrHIvXSHVPVTlKK9jXFcOI7unHDlLPkQpQnr5UqWAU6mqYCsum2INgJ5gpb_MAsmsmz4zQ1GuCflHLfZgQ95NKSrx00sdn3Vz3gMSUAuQQqOpu3XL0wdkxV)
43. [substack.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFqJHQnb5e-ue_kyVQmdVcxavVFu1QIwT-JqL6OL5GRb3eGFe9ighIKKdODvX9vDi60OXlLnEp86-8UbrwwAr4KHoPNw85P4npJNxWmqhBJN4tNEj0DkGe_biNfCAtOKqYu5ob4rN9LjEy4jUYQdfDLe3olWXkeGROUvWE=)
44. [paddo.dev](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7dfMvkftrBFk0D63At-ySC0T_kp_tnS1bTueSv4h-4JlEKZxHQEiuKZyzm5SVaX0WP2UvR3IT_VgBa4hWlIjiPQR0Sc3N9RehU1Dphr-cR9kD60qiWtJfSijoUt3YUIGSLsleXiVSrYK_)
45. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHSN_Ta0Zv2TOt3yw3NkIEX0K7S47zRaICIyIjIT2xRXKkFqwgaQ28Fr99Roc3xq4AWGTw0ImxON8OA9hWs1sZ_Dln_w46hDSS3SMmZ6d2h3CoeQnPPW4CoB7fPLd8ORT4=)
