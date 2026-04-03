# Architectural Analysis and Migration Strategy: Custom TDD Workflows vs. Obra/Superpowers Integration

**Key Points:**
*   **Current Workflow Efficacy:** Research suggests that your current `/tdd-cycle` command employs a highly sophisticated, academically backed AgentCoder paradigm (achieving an estimated 96.3% pass@1 rate) by strictly isolating the `test-writer` and `implementer` sub-agents to prevent context contamination [cite: 1]. 
*   **Superpowers Installation Status:** It appears likely that the `.claude/skills/superpowers/` directory in your project currently houses custom organizational skills (e.g., `gen-test`, `api-doc`) rather than the official `obra/superpowers` marketplace framework [cite: 1]. Consequently, the official `superpowers:test-driven-development` skill does not seem to be actively installed in that specific local directory.
*   **Methodological Overlap:** Both your custom infrastructure and the Superpowers framework share a rigorous commitment to the "Iron Law" of Test-Driven Development (TDD)—specifically, the mandate that no production code is written without a failing test first [cite: 2, 3].
*   **Hook Conflicts:** Evidence leans heavily toward existing regex-based validation hooks in your `.claude/hooks/` directory causing severe context pollution and artificial blocking [cite: 1]. These will likely conflict with Superpowers' fluid, Socratic reasoning phases.
*   **Agent Teams Viability:** Integrating Superpowers with your `TeamCreate` Agent Teams (e.g., independent `Builder` and `Test Writer` teammates) is highly feasible, though it will require explicit skill injection into teammate initialization prompts [cite: 1].
*   **Migration Pathway:** Transitioning to Superpowers as the primary workflow will require deprecating the custom `/tdd-cycle` command, removing aggressive regex hooks, installing the official marketplace plugin, and delegating the Epic automation loop to Superpowers' native `subagent-driven-development` [cite: 4, 5].

---

## 1. Introduction to the TDD Infrastructure Evaluation

The integration of autonomous coding agents into formal software engineering pipelines necessitates strict methodological guardrails. Without these guardrails, Large Language Models (LLMs) are prone to architectural drift, hallucination, and the premature generation of production code before behavioral specifications are formalized. Your project has historically mitigated these risks through a highly customized, robust infrastructure comprising the `/tdd-cycle` command, the `/auto-epic` automation pipeline, and a suite of defensive event hooks. 

Recently, the `obra/superpowers` framework has emerged as a comprehensive, skills-based workflow engine for Claude Code, offering native, systemic enforcement of TDD, systematic debugging, and subagent orchestration [cite: 5, 6]. This report provides an exhaustive, academic analysis of your existing TDD infrastructure, evaluates its compatibility with the `obra/superpowers` ecosystem, and outlines a rigorous blueprint for adopting the Superpowers TDD skill as the primary developmental workflow.

---

## 2. Analysis of the Current TDD Workflow (Q1)

To understand the baseline, we must deeply analyze the current state of your test-driven development infrastructure, governed primarily by `.claude/commands/tdd-cycle.md` and `.claude/commands/auto-epic.md`. Your current workflow is an advanced, multi-agent implementation that heavily leverages context isolation and mutation testing verification.

### 2.1 The `/tdd-cycle` Command Workflow

Your `/tdd-cycle` command implements a strict RED-GREEN-REFACTOR loop by deliberately partitioning tasks across isolated sub-agents. This design is rooted in the academic AgentCoder paradigm, which theorizes that segregating test generation from code implementation prevents the LLM from writing biased tests designed merely to pass an existing, flawed implementation. Research noted in your documentation claims this isolation yields a 96.3% pass@1 rate compared to a 67% rate in single-agent architectures [cite: 1].

The workflow proceeds in three immutable phases:

1.  **Phase 1: RED (Test Generation):** 
    The system first reads `docs/known-gotchas.md` to inject historical context. It then spawns an isolated `test-writer` sub-agent [cite: 1]. This agent is explicitly forbidden from writing implementation logic. Its sole mandate is to write failing behavioral tests using `pytest` and `FastAPI TestClient` for the backend, or `vitest` and `@testing-library/react` for the frontend [cite: 1]. Crucially, the system enforces a hard gate: the process cannot proceed to Phase 2 until all newly written tests are executed and confirmed to fail (red) [cite: 1].
2.  **Phase 2: GREEN (Minimal Implementation):**
    A separate `implementer` sub-agent is spawned in a fresh, isolated context [cite: 1]. This agent reads the failing test file to understand the behavioral contract. It is instructed to write the *absolute minimum* code required to make the tests pass, strictly forbidding premature optimization, extra features, or refactoring [cite: 1]. If a test fails, the agent is mandated to alter the implementation, never the test itself. A hard gate prevents progression until all tests pass (green).
3.  **Phase 3: REFACTOR (Code Improvement):**
    The loop returns to the primary conversational context. The agent reviews both the test and implementation files to improve naming conventions, structural elegance, and eliminate duplication [cite: 1]. The tests act as a regression harness; any refactoring that breaks the green state is immediately reverted.
4.  **Lightweight Mode:**
    For trivial modifications estimated to take under 30 minutes, the sub-agent isolation is bypassed, and the loop executes within the primary context to save computational overhead and time [cite: 1].

### 2.2 The `/auto-epic` Automation Pipeline

The `/auto-epic` command serves as the macro-orchestrator, elevating the microscopic `/tdd-cycle` into a fully autonomous, feature-factory pipeline [cite: 1]. 

1.  **Requirements Ingestion:** The agent reads `PRD.md` to identify the next incomplete Epic and reviews `PROGRESS.md` to establish spatial awareness of the project [cite: 1].
2.  **Iterative Feature Development:** For each feature delineated in the Epic, the system delegates execution to the `/tdd-cycle` via `Agent(subagent)` [cite: 1]. 
3.  **Composite Oracle Verification (Mutation Testing):** 
    This is a highly advanced quality assurance gate. Following the completion of the implementation, a `PostToolUse` hook automatically executes a Composite Oracle suite, heavily relying on mutation testing tools (`mutmut` or `Stryker`) [cite: 1]. If mutmut reports "surviving mutants" (meaning the implementation could be altered without a test failing, indicating a facade test), the loop rejects the implementation and iterates to strengthen the tests [cite: 1].
4.  **Pipeline Integrity and Dead Code Analysis:** Tools like `vulture` (Python) and `knip` (TypeScript) are run to ensure no uncalled or "dead" code was generated during the sprint [cite: 1].
5.  **Agent Teams Variant (Ralph Loop):** An alternative configuration of `auto-epic.md` utilizes the `teammateMode: in-process` feature [cite: 1]. It uses `TeamCreate` and `TaskCreate` tools to establish a shared task list. It spawns a `Builder` teammate responsible for `src/` directories and a `Test Writer` teammate responsible for `tests/` directories, enforcing TDD by establishing blocking dependencies between tasks [cite: 1].

---

## 3. Evaluation of the Local Superpowers Installation (Q2)

To determine whether the `superpowers:test-driven-development` skill is already available in your project, we must critically examine the contents of the `.claude/skills/superpowers/` directory as retrieved from the research data.

### 3.1 Contents of the `.claude/skills/superpowers/` Directory

The research data reveals that your `.claude/skills/superpowers/` directory is currently populated with a suite of custom, project-specific skills, rather than the core logic of the official `obra/superpowers` marketplace framework [cite: 1]. The files identified within this directory include:

*   **`project-conventions`**: A background-knowledge skill (user-invocable: false) detailing naming conventions, `Result<T, E>` patterns, and forbidden practices (e.g., `any` types, `console.log`) [cite: 1].
*   **`setup-dev`**: An onboarding script for new contributors that runs prerequisite checks and database setups [cite: 1].
*   **`api-doc`**: A generator that applies an OpenAPI YAML template to specific routes [cite: 1].
*   **`create-migration`**: A database migration generator equipped with validation scripts [cite: 1].
*   **`gen-test`**: A custom test scaffold generator that references examples (`unit-test.ts`, `integration-test.ts`) [cite: 1].
*   **`new-component`**: A React component scaffolder utilizing templates [cite: 1].
*   **`pr-check`**: A pull request reviewer that evaluates diffs against a `checklist.md` [cite: 1].
*   **`release-notes`**: A utility that leverages `git log` to summarize commits [cite: 1].

### 3.2 Is `superpowers:test-driven-development` Available?

**Conclusion:** The official `superpowers:test-driven-development` skill is **not** currently available within the `.claude/skills/superpowers/` directory. 

It appears that the directory name `superpowers` was either manually created to house custom project skills, or an early, partial implementation was attempted. The official `obra/superpowers` framework is deployed via Claude Code's marketplace ecosystem. When installed appropriately (e.g., `/plugin install superpowers@superpowers-marketplace`), the core skills—such as `brainstorming`, `writing-plans`, and `test-driven-development`—are stored dynamically within `.claude/plugins/cache/Superpowers/` and are bootstrapped via a `<session-start-hook>` [cite: 7, 8]. 

Therefore, to utilize the true `superpowers:test-driven-development` skill, you must formally install the plugin via the marketplace rather than relying on the custom scripts currently housed in `.claude/skills/superpowers/`.

---

## 4. Comparative Analysis: Custom `tdd-cycle` vs. Superpowers TDD (Q3)

Transitioning to a new developmental methodology requires a rigorous comparative analysis to identify methodological overlaps, architectural gaps, and systemic conflicts.

### 4.1 Methodological Overlaps

Both your custom `/tdd-cycle` and the Superpowers `test-driven-development` skill are firmly rooted in the fundamental tenets of test-first engineering. 

1.  **The Iron Law of TDD:** Both systems vehemently prohibit the generation of production code prior to the establishment of a failing test suite. Superpowers explicitly dictates: "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST" [cite: 2, 3]. Similarly, your `/tdd-cycle` strictly enforces Phase 1 (RED) before allowing Phase 2 (GREEN) to commence [cite: 1].
2.  **Verification of Failure:** Both methodologies mandate the critical step of *watching the test fail*. Superpowers emphasizes that if an agent does not observe a test failing, it has no empirical proof that the test is actually measuring the intended behavior (preventing false positives) [cite: 2, 3]. Your workflow accomplishes this via an explicit `test-writer` prompt requiring a FAIL output [cite: 1].
3.  **Minimalist Implementation:** Both systems champion the YAGNI (You Aren't Gonna Need It) principle. Superpowers requires "minimal code to pass" [cite: 2, 3], mirroring your `implementer` agent's rule to "not write extra features, do not optimize, do not refactor" until Phase 3 [cite: 1].

### 4.2 Architectural Gaps and Divergences

While philosophically aligned, the operational mechanics of the two workflows diverge significantly.

*   **Context Isolation vs. Sequential Prompting:** 
    Your `/tdd-cycle` utilizes the **AgentCoder paradigm**, spinning up entirely separate, ephemeral sub-agents (`test-writer` and `implementer`) to physically isolate the LLM's context window. This guarantees that the implementation agent cannot be biased by the prompts used to generate the test [cite: 1]. Conversely, the Superpowers TDD skill operates predominantly within a continuous conversational loop or via a single dispatched sub-agent tasked with executing a step-by-step plan [cite: 4, 5]. Superpowers guides the agent sequentially (Write test $\rightarrow$ Run test $\rightarrow$ Write code $\rightarrow$ Run tests $\rightarrow$ Refactor), relying on cognitive prompting rather than physical context sandboxing [cite: 2, 4].
*   **Knowledge Base Injection:** 
    Your custom command automatically reads `docs/known-gotchas.md` and explicitly injects it into the prompt variables of the sub-agents [cite: 1]. The Superpowers skill is generalized and does not inherently know about your local `known-gotchas.md` file, relying instead on its overarching `project-conventions` or the agent's general memory retrieval.
*   **Pre-Implementation Design (The Socratic Flow):**
    Superpowers operates as a holistic pipeline. It precedes TDD with `brainstorming` (Socratic questioning to refine design) and `writing-plans` (breaking work into 2-5 minute tasks) [cite: 6, 8]. Your `/tdd-cycle` is a microscopic execution command, assuming the design and planning have already been finalized by `/auto-epic` [cite: 1].

### 4.3 Potential Conflicts

*   **Automation Disruption:** If you invoke Superpowers' TDD skill from within your highly rigid `/auto-epic` loop, the differing orchestration engines may collide. `/auto-epic` expects to manually dictate the sub-agent's behavior via a custom prompt [cite: 1]. If the sub-agent is initialized with Superpowers, the Superpowers `SessionStart` hook will force the sub-agent to follow the Superpowers TDD skill mandates [cite: 7, 9], potentially confusing the agent regarding which master prompt takes precedence.
*   **Granularity of Tasks:** Your `/auto-epic` feeds an entire "feature" to the `/tdd-cycle` [cite: 1]. Superpowers dictates that tasks must be broken down into micro-increments of 2-5 minutes [cite: 4, 8]. Passing a massive, epic-level feature directly to the Superpowers TDD skill will likely cause context bloat and violate its core design principles.

---

## 5. Hook Compatibility Evaluation (Q4)

Hooks are background scripts executed by Claude Code at specific lifecycle events (e.g., `PreToolUse`, `PostToolUse`). We must evaluate your existing `.claude/hooks/` ecosystem for compatibility with the Superpowers framework.

### 5.1 The Current `.claude/hooks/` Ecosystem

Research indicates that your current hook infrastructure is highly aggressive and interventionist. 

1.  **Regex-Based Context Pollution:** Your project currently employs probabilistic, regex-based interceptor hooks (e.g., the Graphiti Stop Hook, semantic intent blockers) designed to parse AI outputs and generate "soft warnings" via `stderr` when undesired behavior is detected [cite: 1]. The research explicitly identifies this as causing "severe context pollution" [cite: 1]. When the AI receives these warnings, it is forced to consume prompt tokens processing them, creating a distraction loop where the AI attempts to appease the regex hook rather than focusing on software engineering [cite: 1].
2.  **Mutation Testing Overload:** Your `PostToolUse` hooks are configured to trigger complex external pipelines, such as the `mutmut` Composite Oracle verification [cite: 1]. 

### 5.2 Superpowers Hook Requirements and Conflicts

The Superpowers framework is injected into the Claude Code environment via a `SessionStart` hook:
`<session-start-hook><EXTREMELY_IMPORTANT> You have Superpowers... RIGHT NOW, go read: @/.../SKILL.md</EXTREMELY_IMPORTANT></session-start-hook>` [cite: 7].

**Compatibility Verdict:** Your current hooks are **highly incompatible** with the smooth operation of Superpowers. 

1.  **Workflow Interruption:** Superpowers relies on the agent establishing a natural, uninhibited chain-of-thought to move seamlessly between writing a test, watching it fail, and writing the implementation [cite: 2, 4]. If a probabilistic regex hook intercepts the agent's Bash or Edit commands and throws a false-positive warning into `stderr`, it will derail the Superpowers workflow [cite: 1]. The agent will abandon the RED-GREEN-REFACTOR loop to apologize and troubleshoot the hook warning.
2.  **Timeout Hazards:** By default, command hooks in Claude Code have a 60-second timeout [cite: 1]. If your `PostToolUse` hook attempts to run a full `mutmut` mutation testing suite [cite: 1] synchronously after the agent writes code, it will likely exceed the 60-second limit, causing the hook to fail, terminating the agent's operation abruptly, and breaking the Superpowers completion cycle.

### 5.3 Resolution Strategy

To utilize Superpowers effectively, your hook environment must be sanitized. The aggressive regex-based `PreToolUse` and `PostToolUse` validation hooks must be deleted or severely simplified [cite: 1]. Mutation testing should be decoupled from the synchronous `PostToolUse` hook and moved into an asynchronous continuous integration pipeline, or explicitly orchestrated by an independent auditing sub-agent, rather than blindly blocking the main agent's tool invocations.

---

## 6. Integration with Agent Teams (Q5)

Agent Teams represent a paradigm shift in autonomous development, allowing multiple specialized sub-agents to collaborate on a shared task list. Your `/auto-epic` configuration demonstrates a pioneering use of `TeamCreate` and `teammateMode: in-process`, spawning distinct `Builder` and `Test Writer` teammates [cite: 1]. 

### 6.1 Can Superpowers TDD Work with Agent Teams?

**Yes, but with critical architectural adjustments.**

The core philosophy of Superpowers is actually highly aligned with multi-agent orchestration; indeed, the framework natively ships with a `subagent-driven-development` skill that dispatches fresh subagents per task [cite: 4, 6]. However, integrating Superpowers specifically with *your* custom `TeamCreate` teammates presents a unique challenge: **Skill Propagation**.

When you spawn a new teammate using the `teammateMode: in-process` configuration [cite: 1], that teammate initializes with a fresh context window. For the `Builder` or `Test Writer` teammate to adhere to the Superpowers TDD mandates, they must be made explicitly aware of those rules.

### 6.2 Harmonizing the Integration

If a `Test Writer` teammate attempts to write tests, and a `Builder` teammate implements them, they are effectively executing your custom `/tdd-cycle` manually. To imbue these teammates with "Superpowers," the global automation prompt (`/auto-epic`) must explicitly instruct the teammates to read and adopt the Superpowers framework.

Instead of writing custom instructional prompts for the teammates [cite: 1], you would formulate the `TaskCreate` prompt as follows:

*"Spawn a `Test Writer` teammate. As your first action, you must read and adhere to `~/.claude/plugins/cache/Superpowers/skills/test-driven-development/SKILL.md`. Execute the RED phase for Task 1."*

Furthermore, Superpowers naturally prefers to handle its own sub-agent orchestration via the `executing-plans` or `subagent-driven-development` skills [cite: 4, 6]. If you adopt Superpowers, you may find that manually defining `TeamCreate` logic in `/auto-epic` is redundant. You could simply provide Superpowers with the `PRD.md`, allow it to invoke the `writing-plans` skill to generate a task list, and then instruct it to invoke the `subagent-driven-development` skill to automatically dispatch, monitor, and review independent TDD subagents [cite: 4, 5, 6].

---

## 7. Migration Strategy: Adopting Superpowers TDD (Q6)

Transitioning your project from the bespoke `/tdd-cycle` infrastructure to the standard `obra/superpowers` ecosystem requires a calculated, phased migration. This ensures that the rigorous quality gates (like mutation testing) are preserved while adopting the superior planning and orchestration capabilities of Superpowers.

### Phase 1: Environment Sanitization and Installation

1.  **Purge Interfering Hooks:** 
    Navigate to `.claude/hooks/` and `.claude/hooks.json`. Systematically remove all probabilistic, regex-based validation hooks (e.g., Graphiti Stop Hooks, semantic intent blockers) [cite: 1]. Remove synchronous mutation testing from `PostToolUse` hooks to prevent 60-second timeouts [cite: 1].
2.  **Install the Official Plugin:**
    Since your local `.claude/skills/superpowers/` directory only contains custom files [cite: 1], you must install the official marketplace plugin. Execute the following in Claude Code:
    ```bash
    /plugin marketplace add obra/superpowers-marketplace
    /plugin install superpowers@superpowers-marketplace
    ```
    Restart Claude Code. You should observe the `<session-start-hook>` bootstrapping the Superpowers framework [cite: 7].
3.  **Migrate Custom Skills:**
    Move your highly valuable custom skills (e.g., `gen-test`, `project-conventions`, `api-doc` [cite: 1]) out of the `.claude/skills/superpowers/` namespace to avoid naming collisions. Place them in standard project directories like `.claude/skills/project-conventions/SKILL.md` [cite: 1].

### Phase 2: Deprecating `/tdd-cycle`

The physical isolation provided by the AgentCoder paradigm in your `/tdd-cycle` [cite: 1] will be replaced by Superpowers' `subagent-driven-development` skill [cite: 4, 6]. 

1.  **Archive the Command:** Remove `.claude/commands/tdd-cycle.md` to prevent confusion [cite: 1].
2.  **Integrate `known-gotchas.md`:** Your custom loop brilliantly injected `docs/known-gotchas.md` [cite: 1]. To preserve this, modify your `project-conventions` skill [cite: 1] to explicitly mandate: *"Before executing any implementation plan, you must silently read `docs/known-gotchas.md` and adhere to its strictures."*

### Phase 3: Re-architecting `/auto-epic`

Your epic automation pipeline [cite: 1] must be refactored to act as a trigger for Superpowers, rather than micromanaging the sub-agents itself.

**Revised `.claude/commands/auto-epic.md` Draft:**
```markdown
---
name: auto-epic
description: Initializes Epic execution using the Superpowers workflow framework.
tools: Bash, Read, Write
---
# Autonomous Epic Execution via Superpowers

1. Read `PRD.md` and identify the first Epic not marked as COMPLETE.
2. Read `PROGRESS.md` to establish spatial context.
3. INITIATE SUPERPOWERS WORKFLOW:
   a. Invoke the `brainstorming` skill to refine the feature requirements.
   b. Invoke the `writing-plans` skill to break the feature into 2-5 minute tasks.
   c. Invoke the `subagent-driven-development` skill. Instruct the orchestration agent to ensure all subagents strictly apply the `test-driven-development` skill (RED-GREEN-REFACTOR) for every task.
4. QUALITY ASSURANCE (Post-Implementation):
   a. Run the mutation testing suite (`mutmut` or `Stryker`) via Bash. If surviving mutants exist, trigger the `requesting-code-review` skill to analyze and eliminate the facade tests.
   b. Run dead-code analysis (`vulture`/`knip`). Delete unconnected nodes.
5. Upon successful QA verification, execute `git commit`.
6. Update `PROGRESS.md` to mark the Epic as COMPLETE.
```

### Phase 4: Validating the TDD Iron Law

Once integrated, observe the workflow. The Superpowers agent will now:
1.  Read the plan.
2.  Execute the RED phase (write failing test).
3.  Execute a test command (e.g., `pytest tests/ -x -v`) and verify the output is red.
4.  Execute the GREEN phase (write minimal code).
5.  Verify the output is green.
6.  Refactor and proceed.

By moving your mutation testing (`mutmut`) out of a blocking `PostToolUse` hook [cite: 1] and into an explicit QA step within the `/auto-epic` loop, you prevent hook timeouts [cite: 1] while maintaining the exact same level of mathematical rigor against facade tests.

---

## 8. Conclusion

Your current, custom TDD infrastructure represents an exceptional, academically rigorous approach to LLM-driven software engineering [cite: 1]. However, maintaining bespoke multi-agent routing, aggressive regex hooks [cite: 1], and custom lifecycle interceptors incurs substantial technical debt and risks severe context pollution.

By formally adopting the `obra/superpowers` framework [cite: 4, 5], you standardize this behavior. The Superpowers TDD skill fully encapsulates your RED-GREEN-REFACTOR philosophy [cite: 2, 3]. By sanitizing your hook environment, relocating your custom skills, and refactoring `/auto-epic` to leverage Superpowers' native planning and subagent orchestration mechanisms, you will achieve a more resilient, fluent, and highly scalable autonomous coding environment.

**Sources:**
1. .claude/commands/tdd-cycle.md (fileSearchStores/persistentcanvaslearningsys-z2njevmxp7md)
2. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGURj3QBK3pfT9cf8R8QO-lZbkUv22Q8K9AUiijvsT-hJpChkM55vOFTR59Q6DcyIWXzHsA37bktzQNJkXbNGd5XPmwgUgQjFg6EtVHyeFJ3k5ha4I1vJPi07DkK6KcvkCRpKorOPIQdme6qcriSUOJE78xvYe4vinXXGbiq6FJP62JC_rBhTRd2VEH0X4TcIVZ7GFXquIKGcL3ClFQ7_I_8xOsdIs=)
3. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFWx4aJXGjh1pely328OD1lH5gh1BxStDPTNSW97_2igLWW2aYi9H80Rd4d7rCXbYwWRZTf6EMpQoKB5o8u3oFEq9GLfExlMQ4hGYPlIbstLSGOEgW6oa0YAiJDhilEdGdT7ZhdGbOuMSpYQGIp1P3CnWUpHTvOYfWwe6UZ6nOuKI_NjrBKJpMc6XNI)
4. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFAtstavvzUGKZiSdJTDaZbEKxFm_CIpeHNRrwWxvlk8YnkeloFxBWvQ4BL1unjk2zWEtgwOw7i8rT-UiJLITvdD1hxBR04dlgf1iTY7JvQBWecuPhjfTwLUg==)
5. [lobehub.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGe8kPrkp6hVpeDQZu-sgnwDIgQJwxS1U1Plk2thneK4CWaBEvepDBdsE5zdX6Zni22yNKmnwUr69pE4Ivwc7LYgV-iccoP3vsWZUu_tnv-oTswOAi0uFOSGynh0X3ffMTbdwT_CpzcAl3SJz5udFwUbGGSvtM0J0lOkTn5Wzk1DvgEeQU-Bv7vVuPnVztK)
6. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHUmGkOJzORae50lFTiUVrZ0HsIeHB-iNwzGUuFuEs8tkCjhVY8JVDT0PSIyZPpCzxIfn9w4wZrya_JQXuPXl1mGJzRGsVjpwRroy82_tKhUUywWcD-b43w6rX3uCnelAadC9R2ogT4xYPlfdk=)
7. [fsck.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFFe-Gc4RJhhrqGoQYEW4fdsl8R8L0QRu5ZP1opwlRtOZP7-zYfjHR8AyqCxrHSu-EFCasmcftY9OkZDSyNuO0NrMXWmqscNiG976ga4p9nKHEDszNrSDjK-bsXxSUulSFFSWQ=)
8. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGzx_32oQhNdxocGy8uzXL5dIYTs15L_f6yPI-_Prq_Mk1DOmHJYeMBnPn4xnyq4u08l2TGdi2V8xWSCgZRRPG9OTEPEwcB8zTb4RhGAO9nUV4887UrQx7R0H__gmCO8x3ZbU7YZmg=)
9. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEnGn2RTfjdcQzY0HKydSBTC0whTVXc7POXypukQYamTL2VgHCnA7x-gkysnoe02-rIwfMS6R1KxZbCYtq99VuH5vJTF5Ce-wiiAuOs2NGyjktF0g0Owp-a1xnizU0=)
