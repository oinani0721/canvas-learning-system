# Test-Driven Agentic Development (TDAD) in 2026: Integrating AST Impact Maps into AI Coding Workflows

**Key Points:**
*   **TDAD drastically reduces agent-introduced regressions**: Research demonstrates that providing AI agents with structural context via an Abstract Syntax Tree (AST) impact map reduces test-level regressions by 70% compared to baseline models [cite: 1, 2].
*   **The TDD Prompting Paradox**: Counterintuitively, giving AI coding agents procedural instructions to follow Test-Driven Development (TDD) *increases* regressions (e.g., from 6.08% to 9.94%). Agents benefit far more from targeted data (which tests to check) than procedural rules (how to do TDD) [cite: 1, 3].
*   **Lightweight Integration**: The primary artifact, `test_map.txt`, combined with a 20-line `SKILL.md`, replaces complex GraphRAG databases, eliminating runtime dependencies and allowing seamless integration into tools like Claude Code via `CLAUDE.md` [cite: 1, 4].
*   **Static vs. Dynamic Analysis**: Unlike traditional tools like `pytest-testmon` or coverage-guided selection, TDAD's static AST graph approach allows agents to understand pre-change impact without requiring a full dynamic test suite execution [cite: 1, 5]. 
*   **Language Extensibility**: While the primary `tdad` pipeline was evaluated on Python (SWE-bench), the underlying methodology of AST parsing is highly adaptable to polyglot environments like Tauri, React, and TypeScript through Tree-sitter extensions, though native multi-language tooling remains an active area of development [cite: 1, 4].

**Executive Summary**
The integration of Artificial Intelligence (AI) coding agents into production software engineering workflows has accelerated dramatically by 2026. However, while agents have become highly proficient at resolving isolated issues, they frequently introduce regressions—breaking previously passing tests [cite: 1]. The TDAD (Test-Driven Agentic Development) methodology, introduced by Alonso, Yovine, and Braberman, addresses this critical flaw through pre-change, graph-based impact analysis [cite: 1]. By constructing an AST-derived dependency map between source code and tests, TDAD surfaces a lightweight text file (`test_map.txt`) that agents query to verify their work before committing [cite: 1]. This report exhaustively details the operational mechanics of the `pepealonso95/TDAD` repository, its integration into modern workflows like Claude Code and the Ralph Loop, multi-agent collaboration strategies, community reception, and comparative advantages over traditional dynamic test selection tools. 

***

## 1. Introduction: The Regression Crisis in AI Software Engineering

As of early 2026, the evaluation of large-language-model (LLM) based coding agents has been heavily skewed toward issue-resolution metrics, predominantly measured by benchmarks like SWE-bench [cite: 1]. State-of-the-art agents demonstrate the capability to resolve over 70% of real-world GitHub issues [cite: 6]. However, this hyper-focus on resolution rate masks a critical operational vulnerability: regression introduction. Recent empirical studies reveal that roughly half of agent-authored patches that pass issue-specific benchmarks would be rejected by human maintainers due to unintended side effects, with CI/CD pipeline failures being the leading cause of rejection for agent-generated pull requests [cite: 1]. 

When treating agents as autonomous contributors, evaluating them solely on whether they fix a target bug is insufficient; their "net contribution" must account for the code they break [cite: 1]. To mitigate this, developers historically leaned on Test-Driven Development (TDD), expecting that enforcing TDD on AI agents would yield similar safety guarantees as it does for human developers. However, empirical findings in 2026 uncovered the **TDD Prompting Paradox**: providing smaller open-weight models (such as Qwen3-Coder 30B) with explicit, procedural TDD instructions actually *increased* regression rates from 6.08% to 9.94%, making the problem 42% worse [cite: 1, 2]. Procedural instructions consume precious context window tokens and push out necessary repository context, leading agents to attempt overly ambitious, poorly localized fixes [cite: 1].

The solution to this paradox lies in prioritizing *information density* over *procedural guidance* [cite: 2]. The Test-Driven Agentic Development (TDAD) framework achieves this by shifting the burden of test discovery from the LLM to a deterministic, AST-based graph analysis pipeline [cite: 1]. Instead of telling the agent *how* to test, TDAD tells the agent *what* to test [cite: 1].

## 2. Mechanics of the TDAD Framework (`pepealonso95/TDAD`)

The open-source repository `pepealonso95/TDAD` provides a zero-dependency (beyond NetworkX) Python package designed for pre-change impact analysis [cite: 1]. It operates independently of complex runtime architectures like Docker or Model Context Protocol (MCP) servers, making it highly portable for local agentic workflows [cite: 1].

### 2.1 Two-Stage Architecture Pipeline

TDAD operates in a strict two-stage pipeline designed to decouple heavy static analysis from the agent's runtime reasoning cycle [cite: 1].

**Stage 1: Indexing and Graph Construction**
The first stage involves parsing the repository's Abstract Syntax Tree (AST) to build an explicit code-test dependency graph [cite: 1]. 
*   **AST Parser & Graph Builder**: The tool parses the source code to identify structural units. It creates a graph where nodes represent specific entities: `File`, `Class`, `Function`, and `Test` [cite: 1, 4].
*   **Test Linker**: Edges are drawn to capture static relationships. The graph schema utilizes specific edge types such as `CALLS`, `IMPORTS`, and `TESTS` to map exactly which implementation logic is exercised by which test suites [cite: 4]. 
*   **NetworkX Backend**: Originally utilizing a Neo4j database running in Docker, the architecture was iteratively refined through an autonomous auto-improvement loop to use a lightweight, in-memory NetworkX backend [cite: 1]. This completely eliminated the Docker dependency, significantly reducing the friction of deploying TDAD in diverse CI/CD and local environments [cite: 1].

**Stage 2: Impact Analysis and Artifact Generation**
Once the graph is indexed, the impact analyzer calculates the blast radius of proposed or anticipated changes. The engine selects the affected tests and exports them into a simple, static artifact: `test_map.txt` [cite: 1, 4]. 

### 2.2 The `test_map.txt` and `SKILL.md` Artifacts

The elegance of TDAD lies in how it surfaces its complex graph analysis to the AI agent. It relies on two fundamental text files [cite: 1, 7]:

1.  **`test_map.txt`**: This file is a highly simplified, grep-able mapping of source files to their relevant test files (one line per mapping) [cite: 1, 7]. It acts as a localized "map" of the codebase tailored specifically to the files the agent is currently modifying [cite: 8].
2.  **`SKILL.md`**: A concise instruction set that teaches the agent how to consume the map. During development, researchers discovered that verbosity actively harmed agent performance. Simplifying `SKILL.md` from 107 lines down to a mere 20 lines quadrupled the agent's issue resolution rate from 12% to 50% [cite: 1]. The optimized 20-line definition provides three simple directives:
    *   (1) Fix the bug.
    *   (2) Use `grep` on `test_map.txt` to find tests related to the modified files.
    *   (3) Run those specific tests and fix any failures before concluding the task [cite: 1, 9].

### 2.3 Command Execution and Agent Consumption

To utilize TDAD, developers simply install it via pip (`pip install tdad`) and run it against their repository to generate the map [cite: 1]. At runtime, the AI agent requires only standard command-line tools—specifically `grep` and a test runner like `pytest` [cite: 1]. 

When the agent decides to modify `src/auth/login.py`, it executes `grep "src/auth/login.py" test_map.txt`. The output instantly provides the paths to the relevant unit and integration tests. The agent then runs `pytest` on those specific paths. If a regression is detected, the agent utilizes the execution traces to self-correct in a tight, localized loop [cite: 1, 2]. This targeted verification prevents the agent from running the entire, potentially hour-long test suite, while ensuring it does not skip verification entirely [cite: 1].

## 3. Integration into Claude Code and Agentic Workflows

By 2026, tools like Anthropic's Claude Code have shifted the paradigm from chat-based AI to terminal-native autonomous agents [cite: 10]. Integrating TDAD into these environments requires aligning the agent's persistent memory and orchestration loops with the static impact maps.

### 3.1 Utilizing `CLAUDE.md` for Context Provisioning

Claude Code relies heavily on a project-root file named `CLAUDE.md` to establish persistent project instructions [cite: 11]. Unlike `settings.json`, which enforces client-level permissions, `CLAUDE.md` provides workflow guidance that Claude reads at the initiation of every session [cite: 11]. 

To integrate TDAD, developers inject the `SKILL.md` directives directly into `CLAUDE.md` [cite: 11, 12]. An optimized `CLAUDE.md` setup for TDAD includes:
*   A brief description of the architecture.
*   The directive to *always* consult `test_map.txt` before executing code modifications.
*   Instructions on using the `ce:writing-tests` skill or custom testing rules [cite: 13].

For example, the file might dictate: *"Before committing any patch, `grep` the modified file paths in `test_map.txt`. Run the surfaced tests via `pytest`. If tests fail, capture the runtime traces and iterate until green."* [cite: 1, 10]. This ensures that the agent adopts the TDAD philosophy predictably across all sessions [cite: 11].

### 3.2 Hooks and Pre-Commit Enforcement

While `CLAUDE.md` guides behavior, robust integration relies on programmatic hooks to enforce it. In 2026 workflows, developers configure `settings.json` or Git pre-commit hooks to automatically trigger TDAD's impact analysis script whenever a file is staged [cite: 11]. If the agent attempts to finalize a task without executing the tests identified in `test_map.txt`, the hook intercepts the action, fails the commit, and feeds the error trace back into the agent's context window. This creates a hard boundary that prevents untested code from advancing [cite: 14].

### 3.3 The Ralph Loop Paradigm

The "Ralph Loop" (or Ralph Wiggum trick) gained massive popularity in early 2026 as a methodology for interacting with Claude Code [cite: 15, 16]. Conceived as a deterministic bash loop, it embraces the philosophy that LLM actions are inherently non-deterministic, making it better to "fail predictably than succeed unpredictably" [cite: 15]. 

In a Ralph Loop setup, Claude Code is given a task and a completion signal. When the agent believes it is done, it attempts to exit. A bash script catches this exit, evaluates a condition (such as running the tests specified by `test_map.txt`), and if failures exist, feeds the failure trace and the same prompt back into Claude [cite: 15]. 

TDAD synergizes perfectly with the Ralph Loop. Instead of running the entire test suite on every Ralph iteration (which is computationally expensive and slow), the bash loop specifically queries `test_map.txt` for the files modified in the current git tree, runs only those tests, and feeds the localized results back to Claude [cite: 1, 15]. This creates a rapid, highly focused autonomous coding loop that systematically drives the codebase toward a green state without context degradation [cite: 15].

## 4. Multi-Agent Teams and Teammate Interaction

As workflows scaled from single agents to multi-agent architectures (e.g., orchestration agents managing subordinate review and test-writing agents), the distribution of context became a critical bottleneck [cite: 13]. 

### 4.1 Injecting `test_map.txt` into Specialized Contexts

In a multi-agent team, the roles are distinct: a "Generator Agent" writes implementation code, while an "Evaluator/Test-Writer Agent" handles QA [cite: 12]. When the Generator modifies a core utility, passing the entire codebase to the Evaluator is highly inefficient and leads to hallucinated test scenarios [cite: 14]. 

TDAD solves this by acting as the communicative connective tissue between agents. The `test_map.txt` is injected directly into the test-writer teammate's context [cite: 1, 3]. The workflow operates as follows:
1.  **Orchestrator**: Assigns the feature ticket.
2.  **Generator**: Edits `backend/db/query.py`.
3.  **TDAD Pipeline**: Automatically updates `test_map.txt` to highlight that `backend/db/query.py` affects `tests/integration/test_db.py` and `tests/unit/test_query.py`.
4.  **Test-Writer**: The orchestrator triggers the test-writer agent, providing it *only* with the diff of `query.py` and the specific paths from `test_map.txt`. 

This guarantees that the test-writer agent focuses exclusively on the affected test boundary. It ensures the AI writes behavioral tests corresponding to the actual dependencies, rather than generating brittle mock-heavy tests that test implementation details instead of system behavior [cite: 13, 17].

### 4.2 Alleviating Parallel Execution Bottlenecks

A documented issue with multi-agent TDD workflows is the severe hardware load created when multiple sub-agents trigger test suites concurrently [cite: 13]. "Tests kicked off from multiple sub-agents run at the same time, the entire system slows down... heavy parallelization can end up taking longer than serial tasks" [cite: 13]. 

By limiting the scope of tests to only those mapped by TDAD's AST graph, the computational overhead of each agent's verification step is drastically reduced. Furthermore, orchestration tools (like custom CLI load balancers) use the TDAD map to ensure that parallel agents are not colliding by attempting to test overlapping dependencies simultaneously [cite: 13].

## 5. Community Experience: Successes, Failures, and Limitations

Since its introduction, TDAD has seen rapid adoption and intense scrutiny from the AI engineering community.

### 5.1 Success Reports

*   **Massive Regression Reduction**: Replicating the paper's findings, developers report that shifting from procedural TDD prompting to TDAD's contextual maps reduces test breakages dramatically [cite: 2]. In the SWE-bench Verified subset, TDAD reduced the test-level regression rate from 6.08% to 1.82%, eliminating hundreds of peer-to-peer (P2P) failures [cite: 1, 18].
*   **Resolution Rate Boost**: Supplying the test map does not just make agents safer; it makes them smarter. Because the AST map provides structural context about the codebase, agents use it to guide their implementation logic, resulting in an 8-percentage-point increase in issue resolution (24% to 32%) [cite: 1, 2].
*   **The Power of Zero Dependencies**: Moving from Docker/Neo4j to an in-memory NetworkX backend was heavily praised [cite: 1]. The ability to simply `pip install tdad` and generate maps locally made it viable for everyday developer workflows and fast CI/CD pipelines [cite: 2].

### 5.2 Failure Reports and Limitations

*   **Context Saturation and Token Leakage**: If a repository is poorly structured and highly coupled, the `test_map.txt` can become excessively large. While designed to be `grep`-able, overly broad searches by the agent can still surface too many tests, overwhelming the agent's context window and triggering "token leakage" or project corruption [cite: 4].
*   **The TDD Prompting Paradox (Misapplication)**: Teams that attempted to combine verbose TDD instructions *with* TDAD often saw performance degrade. The community learned that "treating the AI like a junior human developer actually makes it fail more" [cite: 2]. If developers force the agent to read the map but still bog it down with step-by-step TDD tutorials, the agent becomes confused or hallucinates code to fit brittle tests [cite: 2, 19].
*   **Non-Determinism in Model Outputs**: Even with perfect structural context, open-weight models suffer from non-determinism. In some instances during Phase 2 evaluations, baseline resolutions were lost simply due to the stochastic nature of the LLM generation [cite: 1]. 
*   **Testing Implementation vs. Behavior**: Some developers noted that while TDAD helps find *existing* tests, if agents are tasked with *writing* new tests based on the AST, they tend to write mock-heavy tests that tightly couple to the implementation, making future refactoring difficult [cite: 17].

## 6. AST-Based Impact Analysis vs. Dynamic Coverage Alternatives

A critical question regarding TDAD is how it compares to established test impact analysis tools like `pytest-testmon`, `jest --changedSince`, and standard `coverage.py`. 

### 6.1 The Limitations of Dynamic Analysis (`pytest-testmon`)

Tools like `pytest-testmon` determine file scope changes by hashing files and running a dynamic analysis using coverage trackers (like `coverage.py`) during actual test execution [cite: 5]. `pytest-testmon` automatically selects and re-executes only tests affected by recent changes, relying heavily on a local mapping database generated by a previous test run [cite: 5, 20].

**The Problem for AI Agents:**
Dynamic coverage tools require an execution trace. They only know a test depends on a function if that test *previously ran* and hit that function [cite: 20]. AI agents, however, are highly generative. They write entirely new functions, refactor logic, and create novel code paths. 
*   If an agent creates a new file, dynamic coverage has no historical data connecting it to existing tests [cite: 20].
*   Dynamic analysis is reactive. It requires the agent to write the code, run the suite, and parse the output. 

### 6.2 The Superiority of Static AST Graphs (TDAD)

TDAD utilizes **static analysis** via the Abstract Syntax Tree. It does not need to execute the code or rely on historical coverage databases. It analyzes `CALLS`, `IMPORTS`, and `TESTS` edges directly from the source code structure [cite: 4]. 

**Why AST is Genuinely Better for AI:**
1.  **Pre-Change Knowledge**: TDAD provides the agent with a dependency map *before* the agent writes the patch [cite: 1]. The agent understands the structural blast radius of modifying a module immediately, allowing it to plan its code changes defensively.
2.  **No Execution Overhead**: Generating `test_map.txt` does not require spinning up a heavy test environment to capture traces; it simply parses text into an AST graph [cite: 1].
3.  **Captures Unexecuted Paths**: Static analysis identifies dependencies based on imports and function calls, even if previous coverage was incomplete. This ensures agents don't miss peripheral tests that simply lacked dynamic execution history [cite: 20].

While `jest --changedSince` uses Git diffs to identify which test files are related to changed source files, it relies on static file-level heuristics rather than deep structural graph awareness. TDAD's AST approach understands that a change in `utils.py` affects `test_integration.py` because of a chain of function calls, providing a much higher resolution of impact [cite: 1, 4].

## 7. Cross-Language Applicability: TypeScript, React, and Tauri

The user query specifies a project stack comprising Tauri, React, and FastAPI, requiring both Python and TypeScript coverage.

### 7.1 TDAD's Current Language Constraints

The original TDAD pipeline, as evaluated in the March 2026 paper, was specifically indexed against Python repositories (SWE-bench) [cite: 1]. Its native AST parser was optimized for Python structural units [cite: 1]. Therefore, for the FastAPI backend of the user's project, the `pepealonso95/TDAD` tool works out of the box natively, utilizing standard Python AST parsing to generate the `test_map.txt` [cite: 1].

### 7.2 Extending to TypeScript and React

The authors explicitly stated in their conclusion that "future work includes extending TDAD to multiple languages via Tree-sitter" [cite: 1]. Tree-sitter is a parser generator tool and an incremental parsing library that builds concrete syntax trees for virtually any programming language, making it the ideal engine for multi-language AST graphing [cite: 1].

For a Tauri + React (TypeScript) + FastAPI stack in 2026, developers must employ a polyglot approach to achieve full TDAD compliance:
1.  **Backend (Python)**: Use the native `tdad` pip package to map the FastAPI codebase [cite: 1].
2.  **Frontend (TypeScript/React)**: Because standard TDAD may lack native TS support, developers leverage Tree-sitter wrappers or parallel tools like `semgrep` (which uses AST pattern matching) [cite: 21] to generate a parallel TypeScript graph. 
3.  **Unified `test_map.txt`**: The outputs of both the Python and TypeScript AST analyzers are concatenated into a single `test_map.txt`. 
4.  **Tauri Integration**: Tauri acts as the bridge between the Rust core and the React frontend. Structural edges (`CALLS`, `IMPORTS`) crossing the IPC (Inter-Process Communication) boundary are notoriously difficult to map statically. Advanced teams define custom manual edges in their GraphRAG or rely on the unified `test_map.txt` for intra-language dependencies, instructing the agent via `CLAUDE.md` to run cross-stack integration tests whenever IPC bindings are altered.

While TDAD's core tool is Python-centric, the *methodology* of feeding static test maps rather than procedural TDD instructions is universally applicable and highly recommended for React and TypeScript agents [cite: 2, 3].

## 8. Conclusion

By 2026, the AI software engineering community recognized a fundamental truth: AI agents are not junior human developers [cite: 2]. Prescribing human-centric procedural workflows—like verbose step-by-step TDD instructions—overwhelms model context windows and actively damages their output, increasing regression rates [cite: 1, 2]. 

The TDAD framework shifts the paradigm by utilizing pre-change, AST-based impact analysis. By distilling complex repository structures into a simple, static `test_map.txt`, TDAD provides agents with the exact, localized data they need to verify their code [cite: 1]. Whether integrated into a standard CLI workflow, managed via `CLAUDE.md` rules, enforced by a Ralph Loop, or distributed across a multi-agent team, this structural knowledge reduces code regressions by 70% while actively boosting the agent's ability to resolve complex issues [cite: 1, 2]. 

For modern, polyglot environments like a Tauri/React/FastAPI stack, while the parsing technology must bridge languages via tools like Tree-sitter, the underlying principle remains absolute: to achieve autonomous software development safely, systems must provide agents with structural context, not procedural dogma [cite: 1, 3, 15].

**Sources:**
1. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEDued8B2VLbKgDol6VP5pZvR_PtJdnXXceENEMV1d0UNk3E0kEQvGDiLJGFMzIlvq2t3nwQEakejc081eyQWNLJXYne0AGgtruUMyfxPK8PvHIFk1QEIH2lU_dEU0ppotB49e9LCJzAB87DDBu1-buVr2v5_jcbvJCN6hfhSQALVMu86u0wNU=)
2. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE3D4n8DF0eBZlIA1vAfehhAaXKa5aN9MmAneeHJQFkbQskY6wk3RjYlYDO5ohDRz6LhBAaxeMcLPtnraBRNId3iC21UAQKedeyGHBRxnU084mk7D2Y2oM8w5brrlRO7UF2)
3. [thelgtm.dev](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGzm6wOuUVGepjjvNaZ-qgQwH7_FWWyebj3v8Xl-bykjTUVNe3ziHVLOGTOBKsC4LS-yorOO63jrD0rnyeziz-lJmJ6mGHXLuaqsRvjVkPk0CYUHwLF0pgVYi59qpnplR4SpTsh)
4. [yutori.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHZh1znIWzmLB21rhveEX_x02NT2d_ldIqyu9_C75SahC5AC4kyqbFvI-Pk7r_xEYYkU4ZMvyN6b20qs7w7UGn7RYIdBZpORCfYc9M2Rt9I8R1yVtxhzTbQ9RxPiJBWO2d5YpG8ZHPQWIRZGmfWEDNZx_GSVA==)
5. [readthedocs.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGtW0l7dB6MWTUdeD48ypX4nd5_hN8zEDNmtzXMdGkr12ArV3iw0dS7nAhqIBuaGLzl58DPXfSPzb3N8djLGwWMSCmHQfv1jsL-waoNzQ_UpOsqJRAHOkDuhaQVTKHD-AC9p6kll5wqJvbmguiR1MThHlk=)
6. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH9TzAo1KSRlN_Tb48OqNL8djiygvj524txwylfGQu5F1TCHUtAUne0Wfy8HrbDmYMfRCSvhBVaLjglrSEw1CuxPTYB01D1VAArlE5ENB9ULGsCcb-CY3rcaw==)
7. [alphaxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEr3exXiyyo2zlUg6qG3bwtiQ4OH1rWFhO6ClyQPOQ4Q7QJrhjFWsTmtIm_T2c-EcTi6a8ZRDfBQUBeciv3bVHXeaqiQEqZtlleVc4qApkUS82ZAt80s38XdGGGqn61P85D8Oo83CW-)
8. [alphaxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8U0V-ayIJBQLrROgOjIeN58lwA2EW0yQKKf0uM-jnaHs9S4-3xynG0NK25Yvqksv5MDHHrIcRvH9TzyC2T_qOrjUciPszTQAZiPWKKJdkWGBc9Tm0Qas7txBrlh-7YpzVwHWKSs5z)
9. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHQ3scF6Cd77CIVKOal6RKSvwazY8g7xHQX14tAoeLKU6jDF2hD_b-HB-ehE3cuzvaFOy56xwyI_64GtxZ5Hw2htN8W0fT6iPffRTTO6cjxl23SDqxL3pmscw==)
10. [adventureppc.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGCqH_kCu6iusXzJPAf2dxlRSDiBEodBOQsFpPmuyKFTIFQWjagDePnj0TKXtpEq5Gd1gzIHDb8Xly4-VBXiTvhznbKYe2rIGYkd_Jsf56t9SOVnhTjNj5u5RPbv9ZGWoIxJl1QAxpIGTc81shaooZdZt7Nj8LB2VQsSm0Alp-5dCBEX7-l1uKHQdKY6izG3r6jqXO70tSmrBbVZ6tb9RdYv6ipEffsGQ3-9gk39-Vj)
11. [jdhodges.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG2SPeEssxnV_8RvI-_qKUUbfrmeBVolV4LF2VOAS4RI2ydw8hZSHa6NQiTaTjNzkZQMtd1Gdz0SA0LbmcRFpCR75jl-n6d3yY0pZ8X8QbK7R_0p6jCIQ9D5KUg0DR1x4vEJvANb6XM2LUqIU6AuzWI2ZSXlwk0ZaSOh6EuVXA=)
12. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEIcsC5n_F9v2DRfJqnS8PsVXWX5lwEVGS7pw9kEHEzo0ME6am98y6JBbHeppd1k6ftzRdjRlAtEOwukp_BHjq_NUYoZA1p2BJSW-XWe_KPgXLz_iIKGPB1o5yUr3EVuaaoOhoY28RQCKHM_5PEIIe2vGd1Gp4=)
13. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE-a_V-M1CL0FqcfSe8sgRJ3TJYxb23BvtDxG8XehYw0a5hus4p-GyXicQkfEg31oZFcX30T8elIiIF3zKeXbf8pusiduIJBNWiLIQonHC8DGLR0_8rjqof5Uz_MFn_bV5I3NPpTZftMZQ24MV6Uta4Vzy1eIQ0czWsQYeGBVpU-BHVoJ92i1Iw8OGqIXLmb6UC-MPG_DuGYUg=)
14. [trukhin.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBBIG8ZSHqvb15yq3kfInzE5VWaKD2YdFp2ntnR8ITiLbyUcqtQOYvvXxwnYWh9Mw49hQuU8R1GKSCIlFPE2abWCq33scUTF47nHgiItiu113VFx2EjuBJQKqS530lOqxrEvkEuGOmbSlqd5N0TiUAeukoHKvtd79bpkhlkpRDYMab91McoEb1nGpC2esqu4LFmqtgs-_TAvQ31dcOmn9em2oQMP8FT7MJDQ==)
15. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHTKfaa3Nop-UljRmndEVxIfTxCsIFGE6mtlRKGUx8EcnYtRPNsIOIyUynoZaAwhsVh9hcbuegMQds_qYkblL4eVf5lxKDVPSgjwEAJ0Yewg_f9ruuOpFjCnJ_HOF3UBwrLH7D8JTTrIZ6cQQD0srSKnNkJ7XO7IawUmNN87CzGhswxNfo-uD7j0p3qrPGz_NE4RQgbZn7J)
16. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHfFbJ7J_I2m3BLuT4W548fCE8ohn9hh4L0Fj-C-ENR9hNYTHHAhJKMB9Wb1ynwCOC03qMUUGjK0N_IzvpVjAzzYj0cA2YSPJSTpa1XuhPBvTKEdnZvfiRlszmjQKsGfruVsV3juQQmN5S-Nf8zLGuXLuCboeF-5POHcMBnHIXIv-_oDn5HVXv5Q835JGlGPb1-fGkK80oV407Z)
17. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH3rUj5cmsHK_eFZkP2ORWD0JkoTpWVTDrWqEi3jAxySzXUTOeX-m02ewTJvorvZFl3qwlI3bjZDifctOca1F-Cfz7p8_Hf80ZGaetU7uRm9Fl0n51WGsLkP-_GDrDkppkDwf4sN6vgEN5yB9sxPZ407zXPXq5qyJka11eStYzLn1yvnzFlintJyE8=)
18. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEsR1q7zS0p72NGu6yxf3Xeq4zgPciAv-0Z6WqNUUWTAIel0HbW6ovawgm9aOORODWxQP5K1jxcU_Ui85Wvz6-F9rsgmVboC48mivrUC4NTPHzij41STA==)
19. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH4aO-9NMEUT8piiEwQf_AcWgYbinP6r5-1HHxiYYcb4FNMO2VWJuV-NAITWVCEdJfkB8ejA2VPQjtUPdWGXxsR5HnA_el4WsFHj9J5d59EATIQV8ds0tmzs127raTUKNIDLBY1EckfPe0EPDAugusbG2-Af_bTUpq1HDYzDkkG9crL7RUQO09Rhsr_JPJh55MzmX-nThPG4meYkNJJpAxTag==)
20. [itea4.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE2AZJv_KZPBFOpJB9g0yH4c1XMbaElVEicd5DmPjLgOGfdpnfRpsgWx08QqACX6O4N0k9-xiQ5ofh9bJ2ddFO0TPHOT-fQ-vZXRy-WYhPIeQ9Bm0U18vshILBy6uCpCPIWVFWLAVytsxsH73MEHZGeKTPmyR9isKOUejJ8G_JomeV26LOXD-B55cJ0MSukMTKniyuLaZj8YvWwlVoci-IvQNAdUlQ_Mm0IGbaic_xYkSNxGq04Kfs5)
21. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE6ExTGZRmpfiULB-TnAjCHNpsynsop9ey4UGm7PgK8hY7RTxKy2fz3_uO7fnzTLQfnCBtSoyKwcTXiSSoARehWvAPy8wWeP8yXuV7bCqW77L_ige2PsfnaM1EM-gFJaR9b--kjKqHZ5UXQdQUHi4BaESE=)
