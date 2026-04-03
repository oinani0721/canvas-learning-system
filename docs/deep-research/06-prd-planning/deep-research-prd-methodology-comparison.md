# Specification-Driven Development for AI Agents: A Comparative Analysis of BMAD V6, GSD, and the Ralph Loop

**Key Points:**
*   Research suggests that the era of unstructured "vibe coding" with AI agents is transitioning toward Specification-Driven Development (SDD), mitigating issues like context rot and technical debt.
*   The BMAD V6 framework provides a highly structured, metamorphic multi-agent ecosystem that simulates an entire product team to generate deeply detailed, heavily sharded markdown artifacts.
*   Goal-Structured Documentation (GSD) strongly emphasizes "context engineering," utilizing a Discuss-Plan-Execute-Verify loop with isolated 200k-token sub-agent execution to maintain context purity.
*   For deterministic autonomous execution, the Ralph Loop relies on a strict, machine-parseable JSON state file (`prd.json`), prioritizing dependency-ordered, single-iteration tasks over verbose narrative documentation.
*   The evidence leans toward `snarktank/ralph`'s native PRD compiler skill being the most optimized approach for producing `prd.json` files, as it utilizes strict formatting heuristics designed specifically for state-machine loops.
*   Alternative community-validated frameworks like Taskmaster AI, SpecKit, OpenSpec, and Superpowers offer varied philosophies regarding how much structure AI agents need, balancing execution depth with platform breadth.

**Understanding Specification-Driven Development (Layman's Summary)**
For the everyday user or developer, working with AI coding tools like Claude Code often starts feeling like magic. You ask for a feature, and it writes the code. However, as projects grow, the AI's "memory" (known as its context window) fills up with past chats, failed attempts, and outdated instructions. It begins to forget what it was supposed to build, a phenomenon developers call "context rot." Specification-Driven Development (SDD) solves this by forcing the AI to write down its plan into permanent files (like a Product Requirements Document or PRD) before it writes any code. When the AI needs to code, it reads these fresh, clean files instead of relying on a messy chat history. 

This report examines different "operating systems" for these AI agents. BMAD V6 acts like a corporate team, hiring different AI "personas" (like an Analyst and a Product Manager) to write massive, structured documents. GSD (Get Shit Done) acts more like an assembly line, breaking work into tiny, verifiable steps with distinct "research" and "verify" phases. Finally, the Ralph Loop is a minimalist robot that strictly reads a to-do list in a JSON file, doing exactly one task at a time until the list is finished. Choosing the right methodology depends on whether you are building a quick prototype or a massive enterprise architecture.

***

## 1. Introduction: The Paradigm Shift to Specification-Driven Development

The rapid proliferation of large language model (LLM) powered autonomous coding agents has fundamentally altered the software engineering landscape. Initially, the dominant paradigm was colloquially termed **vibe coding**—a process where developers provide unstructured natural language prompts, relying on the LLM to intuit architectural intent and system constraints [cite: 1, 2]. While effective for rapid prototyping, vibe coding quickly degrades in complex projects. As the agent's context window fills with conversation history, debugging attempts, and divergent requirements, it suffers from **context rot** [cite: 3]. The model forgets earlier instructions, hallucinates dependencies, and produces inconsistent, unmaintainable code that generates significant technical debt [cite: 2].

In response to these limitations, the developer community has rapidly gravitated toward **Specification-Driven Development (SDD)** frameworks. These frameworks share a core philosophical premise: project state and architectural intent belong in durable file artifacts, not in ephemeral chat transcripts [cite: 3]. By formalizing the planning phase and generating explicit Product Requirements Documents (PRDs), architectural specs, and granular user stories, these systems orchestrate AI agents deterministically [cite: 4, 5].

This report provides an exhaustive comparative analysis of three dominant SDD methodologies optimized for AI agent development: **BMAD V6**, **GSD (Goal-Structured Documentation)**, and the **Ralph Loop** pattern. It specifically investigates their PRD generation workflows, artifact structuring, machine-parseability, and integration with autonomous state-machine execution environments. Furthermore, the report explores alternative community-validated frameworks—including SpecKit, OpenSpec, and Taskmaster AI—to contextualize the broader ecosystem of agentic orchestration.

## 2. BMAD V6: The Metamorphic Multi-Agent Framework

BMAD (Breakthrough Method for Agile AI-Driven Development) V6 is a highly structured, enterprise-grade framework designed to simulate a complete cross-functional software development team using specialized AI agents [cite: 2, 6]. The framework treats AI as a disciplined participant governed by strict version control and agile ceremonies rather than an ad-hoc assistant [cite: 6].

### 2.1 The Metamorphic Architecture and Scale-Adaptive Intelligence
A defining characteristic of BMAD V6 is its **Scale-Adaptive Intelligence**. The framework dynamically adjusts its planning depth based on the defined scope of the project [cite: 7]. 

The framework operates across three distinct tracks:
1.  **Quick Flow (Level 0-1):** Designed for bug fixes or simple features. It bypasses formal PRD generation, creating only a technical specification and 1-2 user stories. Target resolution time is approximately two hours [cite: 2].
2.  **BMad Method (Level 2-3):** Utilized for new products and platforms. It mandates the creation of a full PRD, Architecture document, UX Design, and Epic breakdown into 10-50 granular stories [cite: 2].
3.  **Enterprise Method (Level 4):** Reserved for multi-tenant systems and large-scale migrations. It includes all Level 2-3 artifacts plus strict Security Architecture, DevOps Strategies, and Test Strategies [cite: 2].

Furthermore, BMAD V6 is project-type adaptive. If a user defines the project as a standard web application, it generates a standard PRD. However, if the project is defined as a video game, the system intelligently substitutes the PRD workflow for a Game Development Design Document (GDD) workflow, altering its questioning to cover game mechanics and art assets [cite: 7, 8].

### 2.2 The `create-prd` Workflow and Artifact Generation
The BMAD V6 PRD generation process is a highly structured, multi-phase sequence that enforces the **Fresh Context Principle**. The framework dictates that distinct tasks (PRD creation, Architecture design, Story implementation) must be executed in entirely new chat sessions to prevent context bloat [cite: 2].

The workflow for creating a PRD unfolds through sequential agent personas:
1.  **The Analyst (Ideation):** Before the PRD is written, an Analyst agent is invoked to refine the business idea, conduct brainstorming, and expose logical flaws in the concept. This results in a "Project Brief" acting as the preliminary source of truth [cite: 6, 7].
2.  **The Product Manager (Specification):** The user initiates the `/bmad-bmm-create-prd` command (or its equivalent in the CLI) [cite: 9]. The Product Manager agent takes the Project Brief and initiates an adaptive interview process [cite: 10].

**PRD Formatting and Templates:**
The resulting PRD is not a simple text file but a heavily structured artifact. In BMAD V6, the PRD includes explicitly required sections:
*   **Vision and Differentiators:** High-level product positioning [cite: 11].
*   **Executive Summary:** A concise overview of the problem and proposed solution [cite: 11].
*   **Measurable Non-Functional Requirements (NFRs):** Strict performance, security, and scalability metrics [cite: 6].
*   **Epics and User Stories:** High-level functional breakdowns prior to technical solutioning [cite: 7].

**Context Engineering via Document Sharding:**
To accommodate the token limitations of foundational models, BMAD V6 utilizes **Document Sharding** [cite: 7]. Instead of producing a monolithic 100-page PRD, the framework splits the requirements into smaller, high-context fragments (e.g., separating `epics.md` from the main PRD, storing artifacts in a dedicated `_bmad-output/planning-artifacts/` subfolder) [cite: 11]. AI agents load only the specific shards necessary for their immediate task [cite: 2, 7].

Following the PRD, the **Architect** agent creates the technical stack, database schema, and directory structure, ensuring downstream coding agents remain "on the rails" [cite: 7].

## 3. GSD (Goal-Structured Documentation): Context Isolation and Execution

While BMAD V6 focuses on generating comprehensive, human-readable agile artifacts, **GSD (Get Shit Done)** positions itself as a low-ceremony, high-performance execution engine [cite: 1, 5]. The methodology is designed specifically to defeat context rot by treating project state purely as a system of isolated files [cite: 3].

### 3.1 Combating Context Rot via `.planning/` Architecture
The core insight of GSD is that traditional long-running AI sessions degrade because every message consumes limited context window tokens. As the window fills, the model "forgets" earlier architectural constraints [cite: 3]. 

GSD circumvents this by externalizing project state into a durable `.planning/` directory [cite: 3]. When a new task is initiated, GSD does not rely on chat history. Instead, the orchestrator script reads the structured files from `.planning/` and initializes a completely fresh sub-agent with a pristine 200k-token context window containing only the precise requirements for that exact task [cite: 1, 12]. 

### 3.2 The Discuss-Plan-Execute-Verify Loop
GSD utilizes a rigid four-phase lifecycle for every project milestone: Discuss, Plan, Execute, and Verify [cite: 3, 13].

1.  **Discuss Phase (`/gsd:discuss-phase`):** The user inputs preferences, UI layouts, and domain constraints. This acts as the boundary setting [cite: 3, 14].
2.  **Plan Phase (`/gsd:plan-phase`):** This is where GSD diverges from traditional PRD writing. GSD spawns specialized parallel agents. **Researchers** investigate the domain (e.g., researching JWT libraries if authentication is required). A **Planner** agent then creates a highly structured, atomic task plan formatted in XML (`PLAN.md`). A **Plan Checker** agent then rigorously reviews the plan against the project goals; if the plan is deficient, the Planner must revise it before execution is allowed [cite: 3, 15].
3.  **Execute Phase (`/gsd:execute-phase`):** GSD orchestrates wave-based parallel execution. Independent tasks are run simultaneously by isolated sub-agents, while dependent tasks are queued. Crucially, each executor agent is restricted to implementing a maximum of three tasks per plan, ensuring surgical, atomic git commits that can be easily reverted [cite: 1, 5].
4.  **Verify Phase (`/gsd:verify-work`):** The system relies on "backpressure" via automated testing. If code fails type-checking or tests, a debugger agent is spawned in a fresh context to find the root cause, create a fix plan, and re-execute [cite: 1, 12].

GSD's output is not a traditional narrative PRD, but rather an executable state machine defined by XML prompts, `CONTEXT.md`, and `PLAN.md` files [cite: 3, 15].

## 4. The Ralph Loop: Autonomous Iterative Execution

The Ralph Loop (frequently implemented via the `snarktank/ralph` repository) represents the most minimalist, execution-focused SDD approach. Coined by Geoffrey Huntley and popularized by Ryan Carson, it abandons heavy architectural documentation in favor of a brutally simple bash loop and a strictly formatted JSON state file [cite: 16, 17].

### 4.1 Architecture of the Ralph Pattern
The Ralph pattern operates on the philosophy that AI agents are not smart in single, long-running shots, but become highly effective through isolated repetition with immediate feedback [cite: 18]. The orchestrator is literally a `while` loop that continuously pipes a prompt to an AI CLI tool (like Claude Code or Amp) [cite: 16, 19].

The mental model of the Ralph Loop is: **Spec → Loop → Feedback → State** [cite: 16].
*   **Declarative Spec:** A machine-readable definition of "done" (`prd.json`) [cite: 16].
*   **Fresh Context:** Every single iteration spawns a brand new AI instance. The AI possesses zero memory of previous iterations except for what is explicitly written in `git history`, `progress.txt`, and `prd.json` [cite: 20].
*   **Feedback Loops:** Quality gates (type-checking, linting, unit tests) are enforced as mandatory backpressure. Code is only committed if it passes these programmatic gates [cite: 16, 21].

### 4.2 The `prd.json` State File
Unlike BMAD and GSD, which utilize Markdown or XML, the Ralph Loop is driven entirely by `prd.json`. This file acts as the project manager, task tracker, and context provider [cite: 22, 23]. 

The loop operates by scanning the `prd.json` file for the highest-priority user story where the key `"passes": false` [cite: 22]. The agent attempts to implement the code. If the quality checks execute successfully, the agent flips the boolean to `"passes": true` and the bash loop cycles to the next task [cite: 22].

### 4.3 `snarktank/ralph` PRD Compiler Skill Approach
Because the Ralph Loop requires strict JSON, human-written PRDs or output from standard AI workflows (like BMAD) cannot be natively executed. To bridge this gap, the `snarktank/ralph` repository includes a dedicated **PRD Compiler Skill** [cite: 16, 20].

**The Theory and Prompting Logic:**
The PRD compiler operates on the premise of "boring, strict output rules." The system prompt explicitly commands the AI to output *only* valid JSON, stripping away all conversational markdown or commentary [cite: 16]. 

Furthermore, the compiler enforces the **Number One Rule: Story Sizing**. Every generated story must be completable within a single context window (one Ralph iteration). If a feature is described as "Add authentication," the compiler is instructed to break it down into micro-stories: schema creation, middleware, login UI, etc. [cite: 24]. The compiler also enforces strict dependency ordering (e.g., schema migrations must be prioritized before UI components) [cite: 24].

**Template and Schema:**
Based on the `prd.json.example` source code from the repository, the compiler forces the AI to map requirements into the following exact schema [cite: 24, 25]:

```json
{
  "project": "[Project Name]",
  "branchName": "ralph/[feature-name-kebab-case]",
  "description": "[Feature description]",
  "userStories": [
    {
      "id": "US-001",
      "title": "Add priority field to database",
      "description": "As a developer, I need to store task priority so it persists across sessions.",
      "acceptanceCriteria": [
        "Add priority column to tasks table: 'high' | 'medium' | 'low'",
        "Generate and run migration successfully",
        "Typecheck passes"
      ],
      "priority": 1,
      "passes": false,
      "notes": ""
    }
  ]
}
```
A critical inclusion mandated by the compiler skill is the programmatic verification in the `acceptanceCriteria`. The compiler is instructed to automatically inject criteria such as `"Typecheck passes"` or, for frontend tasks, `"Verify in browser using dev-browser skill"` to ensure the bash loop has a deterministic way to evaluate success [cite: 20, 24].

## 5. Comparative Analysis: Machine-Parseable PRDs for Ralph Loop

A critical question for developers orchestrating autonomous pipelines is: **Which methodology produces better machine-parseable PRDs that can be directly compiled to `prd.json` for Ralph Loop execution?**

The comparison between BMAD V6, GSD, and the native Ralph Compiler reveals significant differences in optimization for machine-parseability.

### Table 1: Artifact Parseability and Execution Alignment

| Feature/Requirement | BMAD V6 | GSD | Ralph Compiler (`snarktank/ralph`) |
| :--- | :--- | :--- | :--- |
| **Primary Output Format** | Sharded Markdown (`.md`) | XML/Markdown hybrids (`PLAN.md`) | Strict JSON (`prd.json`) |
| **Audience Optimization** | Human stakeholders & PMs | Orchestrator scripts & Sub-agents | Bash scripts & State Machines |
| **Story Sizing Enforcement** | Epic-based, variable size | Task-based (Max 3 per plan) | Strict micro-stories (1 per context window) |
| **Dependency Awareness** | Documented in architecture | Wave-based parallelism map | Strict integer prioritization (`"priority": 1`) |
| **Compilation to JSON** | Requires heavy LLM extraction | Requires LLM/Regex extraction | **Native / Direct output** |

**Analysis:**
1.  **BMAD V6:** While BMAD produces the most comprehensive architectural plans, its PRDs are inherently narrative. It relies on document sharding to manage context, resulting in scattered `.md` files (`epics.md`, `brief.md`, `architecture.md`) [cite: 11]. To compile BMAD output into `prd.json`, a secondary LLM processing step is required to synthesize these documents, filter out business jargon, and forcefully reduce epic-sized requirements into single-iteration Ralph tasks. It is excellent for planning, but poor for direct machine parsing.
2.  **GSD:** GSD improves upon this by inherently understanding atomic execution. Its `PLAN.md` files are highly structured and use XML tags to delimit requirements [cite: 1, 3]. However, GSD is an entire orchestrator unto itself; its artifacts are designed to be consumed by its own python/typescript orchestration layer, not a simple bash `while` loop. 
3.  **Ralph PRD Compiler:** The native `snarktank/ralph` PRD skill is unquestionably the superior approach for generating `prd.json`. It is specifically engineered to bridge the gap between human markdown and deterministic execution [cite: 24, 26]. By actively filtering out non-executable narrative and injecting programmatic `acceptanceCriteria` (e.g., `"php artisan test passes"`), it outputs a pristine state-file that a bash script can parse using tools like `jq` without any intermediary translation [cite: 22, 23].

## 6. Other Community-Validated Methodologies

The broader ecosystem of Claude Code and AI agent orchestration features several other prominent, community-validated SDD methodologies. As of early 2026, these frameworks collectively hold over 170,000 GitHub stars, each representing a distinct philosophy on agent governance [cite: 5, 27].

### 6.1 Taskmaster AI
Taskmaster AI (over 24,000 GitHub stars) operates as a persistent memory and task management layer [cite: 28, 29]. Unlike the bash-driven Ralph loop, Taskmaster AI behaves as a sophisticated project manager using a multi-model architecture. It utilizes a primary model for reasoning, a research model for live web context, and a cheaper fallback model [cite: 5]. 
*   **Differentiator:** Taskmaster excels in building deeply integrated dependency graphs. When a new task is extracted from a PRD, it automatically maps how that feature will impact existing areas of the codebase, routing tasks to editors like Cursor or Windsurf via the Model Context Protocol (MCP) [cite: 5, 28].

### 6.2 SpecKit
SpecKit (over 55,000 GitHub stars) represents GitHub's highly opinionated, heavyweight approach to SDD [cite: 28, 29]. It features over 18 specialized agents and relies on a gated specification process [cite: 5, 27].
*   **Workflow:** SpecKit enforces a rigid cascade of artifacts: `spec.md` → `plan.md` → `research.md`. Execution cannot begin until the specification artifacts pass programmatic gates [cite: 5]. Unlike GSD's parallel executors, SpecKit manages orchestration purely at the specification layer, using detailed specs to guide standard AI tools [cite: 5].

### 6.3 OpenSpec
OpenSpec positions itself as the "Lightweight Standard" [cite: 28]. It aggressively rejects "enterprise theater" in favor of a simplistic, folder-based workflow [cite: 28].
*   **Workflow:** OpenSpec utilizes a strict three-step lifecycle for every codebase alteration: Propose, Apply, Archive [cite: 28]. By placing each proposed change in a completely isolated folder, it naturally prevents cross-change context pollution [cite: 5]. It is highly tool-agnostic, providing CLI slash commands that interface seamlessly with various IDEs and agents [cite: 5].

### 6.4 Superpowers
Superpowers is characterized as the "Disciplined Engineer." It connects atomic agentic capabilities into automated pipelines [cite: 27].
*   **Workflow:** Superpowers is heavily focused on Test-Driven Development (TDD). It enforces a strict discipline system where the agent is required to write failing tests based on the PRD, execute them, write the implementation, and run the tests again, refusing to commit until the CI pipeline turns green [cite: 27].

### 6.5 Agent OS and SwissArmyHammer
Other notable models include **Agent OS**, which acts as a full operating system providing isolated workspaces, permission management, and conflict resolution protocols for multiple simultaneous agents [cite: 28]. Conversely, **SwissArmyHammer** explicitly rejects the rigid pipeline workflows of GSD and SpecKit, utilizing a shared Kanban board as state and allowing developers to trigger independent lifecycle tools (discuss, plan, verify) in any ad-hoc order required by the reality of software development [cite: 30].

## 7. Deep Dive: The `snarktank/ralph` PRD Skill Implementation

To fully understand why the Ralph approach excels at autonomous execution, it is necessary to examine the actual methodology and source code parameters defined in the `snarktank/ralph` repository's skills directory.

### 7.1 The Two-Stage Generation Process
The Ralph workflow does not expect the AI to write a perfect JSON file from a blank prompt. It relies on a two-step pipeline [cite: 20]:
1.  **Generation Phase (`/prd`):** The user invokes the PRD generation skill (`create a prd for [feature]`). The system prompts the agent to ask clarifying, multiple-choice questions to define scope and boundaries [cite: 31, 32]. It generates a human-readable Markdown PRD containing User Stories, Non-goals, and Success Criteria, saved to `tasks/prd-[feature-name].md` [cite: 20, 32].
2.  **Conversion Phase (`/ralph`):** The user then explicitly invokes the compilation skill (`convert this prd to prd.json`) [cite: 20]. The AI is swapped to a strict JSON compilation persona. 

### 7.2 Strict Compilation Heuristics
The Ralph PRD Converter relies on strict heuristics that constrain the AI's natural tendency to group tasks [cite: 16, 24]. 
*   **Dependency Sequencing:** The skill instructs the AI to sequence tasks logically: Database migrations/Schema first, Backend server actions second, and Frontend UI components last. A UI component cannot be prioritized above the schema it relies upon [cite: 24].
*   **The "Passes" Check:** Every single JSON object *must* initiate with `"passes": false`. This is the core binary switch that the `ralph.sh` bash script uses to track state [cite: 22, 24].
*   **Mandatory Quality Gates:** The skill forces the AI to append verifiable bash commands into the `acceptanceCriteria` array (e.g., `npm run typecheck`, `php artisan test`) so the bash loop can autonomously execute a check rather than relying on LLM self-evaluation [cite: 22, 24].

### 7.3 Progress and Memory Management (`progress.txt`)
Because the Ralph iteration spawns a clean agent, `prd.json` handles task state, while a secondary file, `progress.txt`, handles codebase memory. At the end of every successful loop, the agent is instructed to append learnings to `progress.txt` [cite: 18, 33]. 

The prompt specifically asks the agent to consolidate patterns under a `## Codebase Patterns` header, formatted as:
```markdown
## Codebase Patterns
- Drizzle: Use `sql<number>` template for aggregations
- React: Use `useRef<NodeJS.Timeout | null>(null)` for debounce timers
```
When the next iteration begins, the fresh agent reads `prd.json` to see what to build, and reads `progress.txt` to learn *how* the specific codebase expects it to be built, effectively solving context rot while retaining codebase knowledge [cite: 33].

## 8. Conclusion

The evolution from unstructured conversational prompting to Specification-Driven Development marks a maturation in the application of AI coding agents. 

**BMAD V6** serves as an exceptional tool for enterprise planning, utilizing specialized personas and document sharding to produce comprehensive architectural blueprints that keep complex, multi-service projects aligned. However, its narrative, heavily fragmented markdown artifacts require significant post-processing to be machine-executable.

**GSD** strikes a balance between planning and execution. By formalizing the Discuss-Plan-Execute-Verify loop and isolating execution within fresh 200k-token sub-agents, it effectively eliminates context rot. Its XML-based `PLAN.md` files are highly structured but are ultimately designed for GSD's specific multi-agent orchestration layer.

For developers seeking pure, deterministic autonomous execution via a simple state-machine loop, the **Ralph Loop** remains unparalleled. Its reliance on the `snarktank/ralph` PRD Compiler Skill to translate human requirements into strict, dependency-ordered, micro-scoped JSON (`prd.json`) ensures that coding agents execute tasks surgically, with absolute programmatic verification and zero context pollution. 

Ultimately, the choice of methodology dictates the development experience: BMAD provides the architecture, GSD provides the assembly line, and Ralph provides the relentless, automated execution engine.

**Sources:**
1. [pasqualepillitteri.it](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHiPE9FL0SyJZCAT2j8jgspFEzkcc2hzvSqfTXif4Emna6BLTt4yHUTO7TfYo1F2epntLQmhWBkO7N0V6bMSXRX_XvR2tiZ_E4oBT4Ify7Mh655RYXDgBQnQyjYa0YdI1x0SxI2yGozSMbEEsPFCRuJ0qF8_U8N1-lA0jnNYxjk3nmi7eTFOqYwdU7KzrOAn065fyJyrLJU8nurqyw_)
2. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHmI4CCef8Xt_kpvRQkThyZDaMQSZavrp9B66zF7njh9oskUaSQ34SjvY0EEprZsmuJoFyVPkA_JBXg21-_pWrIKv9cMiNEYhZj0ILJMvsMBn-2FaSvkGFh2EYZj2Uj1CCiErb3a1MBSXpouxQ-wi9N0ocxal4BRDJD8EIU9UQAiB7wJMtN4nZ8Dj_i_5g03U47iI4D8bN_-Lw-2tEHC_3Pumvlija2es8Cpzpzx_0WwAFlzPko8e1S)
3. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGEM4P2yEK0uCLwbYg1VMWws1quhQsXcEdv_Mre6bvl_qINMxRGg8Y68SyX7TIS348OX50gezRHlGGr80bdhawNcqhhmxndH3FkaYlCEjsUfzNz-P2dkPLzGOSTqLUxA_PaNm528exGLsRxTofKkGPuggrbsGkl-vhB1VJqIBfjwdACzgPIa-bq3nNZIJCT-l6xvLMYBD8-3FoFGRv1qcg=)
4. [github.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFn87k3rxcMoA_ySrz1TDXoAzd7neaBq1OMMlKYaSR57dWVlHvP46OPZkhs-WOJFac8WjYXigb-OBNkOF74wfLgLRWsCoHYEOvZaM79uzXaGBjP4OfVFC3f-6ugL2xYG8FOQjUIqA2nKXgXxEPdWUmqSaPRZw==)
5. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHuKZCircJzZTyWY6Bc2sugtPQN0V5cR0RxqcdzqBD4fxC6bjzJ--XysELt_ibI44vWnyISLfCYGAOPQnWP6Fo8eDSx3o4I9mFxaWzfEuchWElDVSw-XU3JitjRd69DuPxtDeE93Ic-nnQfABUau-lnOeq1Ai6MzcKE-sUpnOgi3BS3vdIC_aUwBrvKwfmVfV_VQ9faY120cuD8XNgHf6bIC2BNjqB23-xBa-4RpHpBsO2kawRyZc975iOJ)
6. [angelhack.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGqhYslLyoOikBBfUkAuhEpTdozQNajMKmxPtTt9vn7UCvJE_3SIU3l26ByDL7iFU64C_mEy17z5wwrRbJAWdxDZbdxkFF-cS4mAm5qaojbNnOXkB2ndX5L4V8fkYyf-AdPXnuf)
7. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHCGU4aRozZUBZHgfQraLX9pyLQWu8OwNyIYs5g9l7aOPkaQekwXma46rH1tqVp5PUz8cVeO0OCfuiGgU51oQl8TCP__GR0lEy-eqtlrvwmc1-h0SRcGJoqF-YIrORcpS8YXQ4hUck2YXHeWGYdamn3IAgEhdlJmI6qDLnY-24t18pXVAVppzzcNKY=)
8. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHMNiCKeFm84o7__SYIUJRrOt5T3vEX0UXHTZkKLWNPaHb2jVFOuSa6vqXm7qKM5u0aK7mgtGgTeoo4lbjIdHJha4yW-IUOZOMCM4ceMg5UBuSHE4RgtU4L57EzaPN0IjBK3uv9MTgXfZHrGFYRXTzBCJmAPd3umjLwHYTDH_LTiwHUq8Awf632Q7CqMKwCArx9oNWPdw__4hSFbeIp)
9. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGR2OhOmfLt91CoLOUtQz2TvpvkfR8tqLe5sntRQ1JoO_4AA7q4oq5z3QTPjXDVfnVNZeeICh1LOvwT6D799zBs0xqGLjFghm7zXgl2GBs94I051KN0MhASS_FgjaweWH4B2V7EG2VvLmjbhSaI)
10. [mcpmarket.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHGe9AovSOMQdVFMwIApLd0e93vNHjrQN1LF_u4Vb9KI3jb8IMXr9NWk-HziawulFNnYxeW369xbWW4qPJGgVEU8Q2ICopdYSXylurl5btlADstHIh5JECtYhwjMw-lr9UttQ==)
11. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGOIoyhu9KVex5KIMFW2HWT821KxnSmJ-y42GERmZ54GrJclWwPl9etLdLHnaSWe-9tCzTuhoa5q6z3bQr0puNoNr6jZKiPGxAYONYTA4iMGY5Jp1hzckyfSr-s36tDnT0qZRQynP1q3JV7ys2hS5iZU6nn2mHPnoA=)
12. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7-QhYl0aB-5KPjvs9E0g1jx3qwrdWu0NRddUSW9c9HuIaQBZ04qyp31H2CyYmRH8pcEPr9oCjal8RcIYeMHKQgPReYGeugzHnItbtOKSV-pgUXnLaP3Wq-Q1FJQiFgBGh-gjZSy8nMkKWsiJcNOLIkPas2gZc3SCl6gLv5eYEG2ic4De6R8oU41_FCX9RIe82)
13. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZkBhxkFDb3T5AMbPNg2lT-i9YBlt7idiOD4n1DIVyCuaGneVpxvugZ_bItj7iW-L9cYeA9p7E4I3eVK-CpCvG51eUWFsCJXn8vRvMALc8l-oOIKKuxePsvHfVqihEH_kCJMjiV9NtYyFh1JLDingiIaETLx_zrV3xFiRT2kzLkMRZtHavhOfPa9D61iUu2Ra7dhTfGw==)
14. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGAAQ-tlwtxOCUOyomtyXUTMdA-GpaOkzXLUgi1T7LUpzNN69vU16taJVCU2nbSNhAXwkP_TgyxdRrE8tvKPtqwxNwK45A94BLSWJwHb_qgfWR6so2yMIABRgHOByHUnJhriV_gQOpD2eD51uZ_BVvihvCBmc_d9cAiQ0p7aFiFK98cHbKddngWHOaF5UpK2w8z1lM=)
15. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFWS5jCV3dgKWyTfyS_mhnpoTO2-i2joyJvLPMWuF5ccbs0Uvd9X_UsMi4glfUmwp7VW7i99bknTLISqpyUEHikCvtZmS6TPFAv064c0ArNnZcX2QcGa-Ne547SkLEhQICKZd7eGP2RHAppp7Tdps91stVqRRxvlzqx)
16. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFt5NML7HwGkkAUUbHq2ti3IjfkgdPyiNb3aozFX0TgmYwyA7s77fyyVPyrtwzgWtjcL_QVjti-Shp6JXvUkcGPnyXfEHm8Ck5df2RKhP6PQlyLgGZVGjbAXWzyr9ah3GicRtbRWCgViRhnIbK_1ICAb1leTZ3tESEcdyc7kj-QvlpAQbYiXZq9eMsW73kj2Isj9AqbMAW6xjeBXNQGMgywBQ==)
17. [addyosmani.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH023EF3VchZr-ZtcuN1rdrCxXU2JOhxejlLxZZoPaNrk1SCNkOpJ77CA45R23F2-7fcAq2fDAcEjm3BNV6v8pTFzf2-GJkr3xlhxeTk0clCckOQ0e9iFl9gyRSY9oR3Msuxn6MMnI=)
18. [thetoolnerd.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHiS2fTBZguuI7GwyvraOw73Z9vHU4BJRVOEP8lPN9zI2oiz7Ky_gQc-IH-5TE-h--KDJOAAHTAQH1ra1GJotlftnOdziAfhkCWtzWJlmjzU8UPZzGMIqdjCP7jqSibkyO82fBVOauuWeeq3sCiikjyja2_UUFoD4o=)
19. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEbOk6Kra155JUTGzmZokPDsGEEob4BYbAU8E-giSkBYGD-HDCyUyaK9wNgkiEtDCH-A8V66Y1y41gOPV-VhPnkVFquptbtL-4Zi8UiMqXGXf3OXJGU0FnFVuM7eTLjeYzsiZh_CQ==)
20. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGzWyhTIo3GsITHiYJ59u-XjZdY6iG7Lb9-Ub7M1sxmo8CV3M6PL2l58JWzTObHx_VyU_2cqjlVCVdSzjfRWQ3MsvReCgLufe3ZMF48gJQ-Gxhs-TBlUQ8=)
21. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGjv7gnUGXJVXA6lIC_4NU-Kp4sklCpHxNE6qNeb7QeDlMoRlE7f0g4H7pQjmEnTCUM19fza44_o9j-C1qBkd2twJrnZLonvc2ILNlLCG9kFRihMzZuLpAAvYLNuys=)
22. [geocod.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG_PjJ3Vy8QgWJF1UUU6hGwSTkC9jvhlcbYOW-WbaNkw3nH3TTPSpyuW2PRooRZ213xqAh0wbufhuCdeD2ULz65DiG8Edr714r03zj3n-ul_Af72OtpdT9i7jnfoObBDrpPvjMXQzkMZJfylAuvzbTWDBVXK8L59Q==)
23. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF4j0U0Arx6fKx-p8OwG3JDzlFukq58XcmZ1Di6-8IMdztcwOoeJaTNa0LP87fs6n6Xo8Us9pERjACQFZBqnQ3by3hQcjhvBUZ2Z-ZWHbTnakaFmw9O1G1viUZkYvplFLsZT3cd8B9Jb2x5yiri84IMyeUKjuhR)
24. [smithery.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEETtgP1E8qvnQx2HCxiX9b4CH8LFS4zBVRHVukY3lOIj_zG0kx8wrpiAN8Gp7beShC6CMUrVHpHfyc8CiAeM6nqcCG9cN1IUs1R1r8SjwkQrvNxyT9xuE7RdoNMksK4gQQjSj9)
25. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEhSOBaUnSsRIBuE__52I-ljEuTkf0Bz4o5KSkxGXFJi3xic16i-Bd82B_GO0a-qrgdj-MFqMvbS5AocIG2ao8NqZLiqPVaALzEs8_JiVKCATyykCnMX9cLl3JkxdmKquSWUzZgDFfCTb6Kwy5WLMVMhQ4=)
26. [lobehub.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHNCEz2JqADI03JdN9I43pWJnYKRzj-ZgiMmYtwPsCSfpqLWbrweUvbQblCty8gXCh7hm-FNTXTYxORMPa-T-m7vabCHk9_5n_NkzlzOtV_Mh4CuZLEpSGUxaptyptxlYqh2SLuqfZLSpVxWQS6s7Gr62LSL1pbVhh1)
27. [plainenglish.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEQ5GEvEkZw_ezyyRqpTFxHXaSP64NLINYoXubtXlZIVC6Ba4QgNnEg6kDquK_jhDKZVfOdZd72u-lJ537tfNWydWAAqeaRQU_baqTfWRRwi8eUgKqQMVgCw4H-lJdHC58wub7kOyknV_39_0VFQm9gKpuPbLrjmI7rxL4lVtH6rgL2a5L9FkFpvBvmRwN-tGzR1TkJN7gsm34a-pisVXk=)
28. [github.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEiCcw_d_NzuqjRxI-LSUGazVuqKiYF8H2rzgwvi3KHXsstEZrYcN7lOVKbjQO_DIDWbtNV9qaxKZcECH6GGKDODUM9yeZvk-f_JNN9-x1BKROp1rOSWqmyLpJwtFqQ0i6um4AIHC94NDosOkodynKIxEFEVy4pOAINMtI=)
29. [jpuncompiled.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF93t9ADMeBPiNzOJiZZwMAVflRBL1n89mL1MNOP8Bx8W2uEEkDcXd6mFq41fLHjqyLWpQ-tn1vUuLWId8D_4G9JbtGmlIWW0uS7l6zV9_YN3-3N3d8VA==)
30. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFwz01ThGspsWVue6rPi2LZk3_DOyiN30XGnYkevj3civfdHqqqa0uhaf2HPwxLG91D5IAzDFCduGoInzOpgIVGxs4STpeHanOlX89bPhIp3wvRKp1Kfthmjo73_YJ6lbw=)
31. [lobehub.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGSPIw6x2P6Fszd_RDVkETt6ThZr7b9JfiwW-b-b8JfLF5lCDu7UOQWxUF2fdNDE8930Rc5bgYzwT3M5YJR25Zus19KS8h36pLsJ91QBYstPck5XUyEyOViRl_8_FgXTtof5KFFUjf_2WoqxbFIqq0=)
32. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEgP8vsppTEqq5l074wzDOONbkA5qhn2ey16G2poXYf6AHTy1OEPrfWigSbZxCURKGOCX_PBdHYP2bmuUFnFIJk9LY-uH8mJ7FjY2t1qYx5BrCg0e7u6Mk3_mx78EKT-OtQE5OBV659mG0EtSwGtAOGX6jdBDY=)
33. [ampcode.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEcKYjvx5q63xe9WKWiHX3SyJPJd7y4EMHW5oO7z9NEbUbBZxCcvchUw8Ed967PQTiclYKlohzzb_SpKqLnqF4lmYLk6txLFxfd4bYARaP5DQY2AUxgEEVCWf4j9K3sNzl4Ne59JJKQv1f83eZzB54MATZHw9pevA==)
