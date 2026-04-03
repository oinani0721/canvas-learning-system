# Comprehensive Verification and Analysis of AI-Driven Test-Driven Development (TDD) Workflows and Success Rates

**Executive Summary & Key Findings**
*   **TDAD & Regression Reduction**: Evidence heavily supports the claims made in the TDAD paper (arXiv:2603.17973). The methodology utilizes Abstract Syntax Tree (AST) mapping to provide agents with targeted test context, achieving a 70% reduction in regressions. The GitHub repository `pepealonso95/TDAD` is real, publicly accessible, and demonstrates active usage.
*   **AgentCoder's 96.3% Pass@1**: The 96.3% Pass@1 claim is accurate but highly contextual. It is derived from the paper "AgentCoder: Multi-Agent Code Generation with Effective Testing and Self-optimisation" and applies exclusively to the *HumanEval* benchmark, which consists of isolated, algorithm-level functions rather than real-world, repository-scale codebases.
*   **TDFlow's SWE-Bench Claims**: The CMU paper (arXiv:2510.23761) accurately reports an 88.8% pass rate on SWE-Bench Lite and 94.3% on SWE-Bench Verified. However, these exceptional numbers are strictly conditional on the system being provided with *human-written, ground-truth reproduction tests*, highlighting that test generation remains the primary bottleneck in autonomous engineering.
*   **`obra/superpowers` Framework**: The GitHub repository `obra/superpowers` is a real, highly utilized Claude Code plugin ecosystem, boasting a massive 124.4k stars. While it strictly enforces a Test-Driven Development (TDD) planning cycle, evidence suggests it mitigates messy code rather than mechanically preventing "facade" architectural patterns without human oversight.
*   **Unified Agentic Systems**: While advanced concepts like the Ralph Loop, AgentCoder isolation, mutation testing, and TDAD AST maps are being utilized across the developer ecosystem, research indicates no single, out-of-the-box GitHub repository flawlessly integrates all four components into a unified source-code system. They currently exist as highly modular, sometimes complementary, tools.
*   **BMAD-METHOD Integration Gaps**: GitHub Issue #843 (and subsequent Issue #1784) in the `bmad-code-org/BMAD-METHOD` repository definitively exists. It provides concrete evidence of a critical TDD integration gap where "dev" agents fail to acknowledge tests written by "QA" agents, breaking the red-green-refactor cycle.

The integration of Large Language Models (LLMs) into software engineering has transitioned from simple code completion to autonomous, agentic repository repair. A critical paradigm in this evolution is Test-Driven Agentic Development (TDD). This report provides an exhaustive, academic verification of six specific claims regarding AI TDD workflows, evaluating the empirical evidence, methodologies, and real-world repository data associated with these advancements.

---

## 1. Verification of TDAD (Test-Driven Agentic Development)

### 1.1 The TDAD Paper (arXiv:2603.17973)
The paper titled "TDAD: Test-Driven Agentic Development - Reducing Code Regressions in AI Coding Agents via Graph-Based Impact Analysis" (arXiv:2603.17973) was authored by Pepe Alonso, Sergio Yovine, and Victor A. Braberman [cite: 1, 2]. The core premise of the research addresses a critical vulnerability in modern AI coding agents: while they are adept at resolving real-world software issues, they frequently introduce regressions by breaking previously passing tests [cite: 3, 4].

Current benchmarks, such as standard SWE-bench metrics, focus predominantly on the resolution rate, leaving the regression behavior under-studied [cite: 4, 5]. To combat this, Alonso et al. introduced TDAD, an open-source tool that performs pre-change impact analysis using an Abstract Syntax Tree (AST) derived code-test dependency graph [cite: 2, 6]. 

### 1.2 Claim Verification: 70% Regression Reduction
The claim that TDAD achieves a 70% regression reduction is explicitly verified by the research notes. Evaluated on the SWE-bench Verified dataset using open-weight models running on consumer hardware (specifically Qwen3-Coder 30B on 100 instances and Qwen3.5-35B-A3B on 25 instances), TDAD's GraphRAG workflow successfully reduced test-level regressions by 70%, dropping the regression rate from 6.08% to a mere 1.82% [cite: 2, 7]. 

In raw numbers, this translated to a reduction from 562 Pass-to-Fail (P2P) failures down to 155 [cite: 2, 4]. Furthermore, when TDAD was deployed as an agent skill with a different model and framework, it improved the overall issue-resolution rate from 24% to 32%, and code generation rates from 40% to 68% [cite: 2, 7].

### 1.3 The "TDD Prompting Paradox"
A highly significant and counterintuitive finding in this paper is the "TDD Prompting Paradox." The research demonstrated that simply adding procedural TDD instructions (e.g., telling the agent "how" to do TDD) to the agent's prompt *without* providing targeted test context actually increased regressions to 9.94%—a result worse than using a vanilla baseline with no intervention at all [cite: 2, 6]. 

This paradox reveals that smaller models benefit significantly more from contextual information (being told exactly *which* tests to verify) than from procedural workflows [cite: 7, 8]. The TDAD framework resolves this by replacing a bloated 107-line procedural prompt with a lightweight 20-line instruction file and a static test map that the agent can query at runtime using simple tools like `grep` and `pytest` [cite: 6, 9].

### 1.4 Verification of the `pepealonso95/TDAD` Repository
The query questions whether the GitHub repository `pepealonso95/TDAD` is real and possesses actual usage. The research confirms that the repository is unequivocally real. The paper explicitly states that all code, data, logs, and 28 experiment records (EXP-001 through EXP-028) are publicly available at `https://github.com/pepealonso95/TDAD` under an MIT license [cite: 2, 10]. 

Regarding actual usage and infrastructure:
*   **Installation:** The tool is highly accessible and can be installed via the Python package manager using `pip install tdad` [cite: 2, 9].
*   **Dependencies:** It is designed for zero-dependency integration, requiring no external graph databases, MCP (Model Context Protocol) servers, or complex API calls. Its only dependency beyond standard Python libraries is `NetworkX` [cite: 2, 6].
*   **Community Presence:** The repository is referenced across various developer blogs, YouTube analyses, and academic aggregators, confirming its integration into the broader AI engineering discourse [cite: 9, 11, 12]. While exact star counts for the GitHub repository are not explicitly quantified in the provided notes, its active citation in tools and workflows (like the integration discussions on Reddit) confirms its practical application in the developer community [cite: 11, 12].

---

## 2. AgentCoder and the 96.3% Pass@1 Claim

### 2.1 Paper and Benchmark Identification
The claim of a 96.3% Pass@1 success rate originates from the paper "AgentCoder: Multi-Agent Code Generation with Effective Testing and Self-optimisation" (arXiv:2312.13010), authored by Dong Huang, Jie M. Zhang, Michael Luck, Qingwen Bu, Yuhao Qing, and Heming Cui, representing institutions such as the University of Hong Kong, King's College London, and the University of Sussex [cite: 13].

The 96.3% Pass@1 metric is entirely accurate within the context of the study, but it is critical to identify the benchmark: this score was achieved on the **HumanEval** dataset using the GPT-4 model [cite: 13]. 

### 2.2 HumanEval vs. Real Codebases
The user specifically asks whether this applies to HumanEval only or real codebases. The evidence confirms that this staggering success rate is restricted to algorithmic benchmark datasets, specifically HumanEval and MBPP (Mostly Basic Python Problems) [cite: 13, 14]. 

*   **The HumanEval Benchmark:** Introduced by OpenAI in 2021, HumanEval consists of 164 hand-crafted programming challenges. Each challenge includes a function signature, a docstring, a body, and an average of 7.7 unit tests. These challenges assess a model's understanding of basic language syntax, algorithms, and simple mathematics—analogous to entry-level software interview questions [cite: 15]. 
*   **Real Codebases:** HumanEval is *not* a real-world codebase. As noted in the 2024 AI Index Report, while AI is a "runaway success" on simpler tasks like those in HumanEval (scoring 96.3%), performance on complex, repository-scale tasks remains mediocre. On the SWE-bench test, which comprises 2,294 real software engineering problems sourced from actual GitHub issues, top models like Claude 2 initially solved only 4.8% of the problems [cite: 16]. Therefore, while AgentCoder's architecture is highly effective, the 96.3% metric does not translate to enterprise-level repository repair.

### 2.3 The AgentCoder Architecture
AgentCoder achieves its results by moving away from monolithic, single-agent code generation. It employs a multi-agent framework that decouples code creation, test design, and execution [cite: 14]. The system consists of three distinct agents:
1.  **The Programmer Agent:** Generates the initial code based on the prompt [cite: 13, 17].
2.  **The Test Designer Agent:** Generates basic, edge, and large-scale test cases for the generated code. In the study, this agent achieved a test generation accuracy of 89.6% and a line coverage of 91.7% for HumanEval [cite: 13].
3.  **The Test Executor Agent:** Runs the code against the test cases and provides objective, execution-grounded feedback (error diagnostics) back to the programmer agent for iterative refinement [cite: 13, 14].

This collaborative system not only drastically improves accuracy (pushing base GPT-4 from 90.2% to 96.3% on HumanEval) but also reduces token overhead. AgentCoder required an overall token overhead of 56.9K for HumanEval, significantly lower than competing multi-agent frameworks like MetaGPT (138.2K) or ChatDev (183.7K) [cite: 13].

---

## 3. TDFlow by CMU (arXiv:2510.23761)

### 3.1 The Claims and the Methodology
The paper "TDFlow: Agentic Workflows for Test Driven Software Engineering" (arXiv:2510.23761), authored by Kevin Han, Siddharth Maddikayala, Tim Knappe, Om Patel, Austen Liao, and Amir Barati Farimani from Carnegie Mellon University (CMU) and affiliated institutions, introduces a novel test-driven agentic workflow [cite: 18, 19]. 

The paper claims that TDFlow attains an **88.8% pass rate on SWE-Bench Lite** (an absolute improvement of 27.8% over the next best baseline) and a **94.3% pass rate on SWE-Bench Verified** [cite: 18, 19]. 

TDFlow achieves this by framing repository-scale software engineering strictly as a test-resolution task. It forces a decoupling of patch proposing, debugging, patch revision, and optional test generation across separate sub-agents. This modularity reduces the long-context burden on any individual agent and tightly constrains the tools available to them [cite: 18, 19].

### 3.2 The Crucial Caveat: Human-Written Tests
It is imperative to contextualize these massive success rates. The 88.8% and 94.3% figures are achieved **only when the system is provided with human-written, ground-truth reproduction tests** [cite: 18, 19]. 

The researchers explicitly state that when TDFlow is tasked with *generating its own tests*, its performance on SWE-Bench Verified drops to 69.8% [cite: 18]. This leads to a monumental conclusion in the study: the debugging, file localization, and code reasoning capabilities of modern LLMs (like GPT-4.1 and Claude 3.5 Sonnet) are already sufficient for solving complex software engineering issues. The primary bottleneck preventing human-level autonomous software engineering is the *accurate generation of valid reproduction tests* [cite: 18].

### 3.3 Independent Verification
The query asks if these claims have been verified by independent groups. The provided research notes indicate that TDFlow represents a highly rigorous academic study, but they do not explicitly contain data showing that a third-party, independent research group has replicated the exact 88.8% and 94.3% figures on SWE-Bench Lite/Verified. However, the methodology itself is transparent. The researchers conducted a manual inspection of 800 TDFlow runs and found only 7 instances of "test hacking" (where an agent alters the test to pass rather than fixing the underlying code), validating the robustness of the agent's behavior within the study parameters [cite: 18, 19]. The broader ecosystem considers TDFlow a formalized academic validation of the test-driven loop approach [cite: 20].

---

## 4. Analysis of `obra/superpowers`

### 4.1 Verifying the Star Count and Usage
The GitHub repository `obra/superpowers`, created by Jesse Vincent (obra) in October 2025, represents a massively popular agentic skills framework and software development methodology designed primarily as a plugin for Claude Code [cite: 21, 22].

The query questions the 120k star count. According to the extracted GitHub Stargazers API data and Star History metrics from March 2026, the repository has an extraordinary **124.4k stars** [cite: 21]. It ranks as the #59 most starred repository globally [cite: 21]. Its growth was explosive, accumulating 73,000 stars in just its first 5 months [cite: 23]. Furthermore, it boasts 10.1k forks and features active community engagement, confirming it is a highly utilized, legitimate framework [cite: 21].

### 4.2 Does the TDD Skill Prevent "Facade Code"?
To address whether the TDD skill in Superpowers prevents "facade code," we must distinguish between the architectural *Facade Design Pattern* and the colloquial term "facade code" (meaning superficial, messy, or hallucinated AI code dumps).

*   **Facade Design Pattern:** In software engineering, a Facade is a structural design pattern that provides a simplified, front-facing interface to a complex subsystem, hiding its internal complexities to make the system easier to use and maintain [cite: 24, 25, 26]. Nothing in the Superpowers documentation suggests it mechanically *prevents* a developer or agent from utilizing the valid Facade design pattern if architecturally appropriate.
*   **Superficial "Facade" Code:** If "facade code" refers to shallow, unmaintainable code generated hastily by AI, Superpowers actively combats this. The framework explicitly prevents Claude from "skipping straight to writing code" [cite: 27]. It auto-enforces a strict `brainstorm -> plan -> TDD -> code review` pipeline [cite: 27, 28]. It emphasizes true red/green TDD, YAGNI (You Aren't Gonna Need It), and DRY (Don't Repeat Yourself) principles [cite: 29]. By forcing the agent to extract a spec, create an implementation plan, and follow a subagent-driven TDD process, it significantly reduces the generation of messy, superficial code [cite: 27, 29].

### 4.3 Success and Failure Reports
Real-world usage reports from GitHub issues and developer blogs highlight both the successes and the constraints of the system:
*   **Successes:** Users report that with Superpowers, "It's not uncommon for Claude to be able to work autonomously for a couple hours at a time without deviating from the plan" [cite: 29]. It is highly praised for projects where "just write it" approaches keep producing messy code [cite: 27]. 
*   **Failures/Limitations:** As an experimental framework, some skills are marked as "Under active refinement" or "May evolve based on usage" [cite: 30]. Furthermore, as noted in discussions of agentic workflows, heavy parallelization of TDD workflows (running multiple sub-agents in git worktrees) can create massive computational overhead, turning laptop performance into a bottleneck and causing agents to wait around during concurrent test suite execution [cite: 31]. While Superpowers successfully orchestrates the loop, the underlying hardware and token costs remain a friction point for developers [cite: 31].

---

## 5. Advanced Combinations: Ralph Loop, AgentCoder, Mutation Testing, and TDAD

The query asks if anyone has combined the **Ralph Loop** (persistent iteration), **AgentCoder isolation** (role-specific sub-agents), **mutation testing**, and **TDAD AST maps** into a single working open-source repository.

### 5.1 Defining the Components
1.  **Ralph Loop:** Named after a bash loop created by Geoffrey Huntley, the "Ralph" technique forces an agent into a deterministic iteration cycle. If the agent fails, the hook catches the exit and feeds the prompt back, forcing the agent to review its git history and try again until a strict completion signal (like a passing test) is met [cite: 11]. It operates on the principle that naive, stubborn iteration with proper feedback often outperforms single-shot architectures [cite: 32].
2.  **AgentCoder Isolation:** The separation of concerns into distinct agents (Programmer, Test Designer, Test Executor) [cite: 13].
3.  **Mutation Testing:** A technique where code is deliberately perturbed (mutated) to ensure the test suite is robust enough to catch regressions.
4.  **TDAD AST Maps:** The use of Abstract Syntax Trees to map code-to-test dependencies, allowing agents to run targeted impact analysis prior to committing [cite: 2].

### 5.2 Evidence of a Unified System
Based on the research notes, there is **no explicit evidence of a single, out-of-the-box GitHub repository** that flawlessly integrates all four of these specific components into one foundational source code. Instead, the ecosystem has moved toward highly modular integrations.

However, we see strong evidence of frameworks mapping closely to this ideal:
*   **TDAID Phase Mapping (2025-2026):** A skill manifest named `oimiragieo-agent-studio-claude-skills-tdd-skill-md` outlines a "Canon TDD for humans and AI agents" that explicitly combines **ralph-loop integration** (Step 1), a **mutation testing gate** (Step 4), and **Test-Driven Prompting (TDP)** where verbatim test output is injected into a developer agent's prompt [cite: 33]. 
*   **TDAD as a Complement:** In community discussions (such as Reddit threads regarding the Ralph Loop), the creator of TDAD specifically mentions that TDAD acts as a complement to Ralph loop workflows. TDAD enforces a "BDD to Test to Fix cycle" and captures a "Golden Packet" (real execution traces, API responses, DOM snapshots), which feeds high-quality data back into the iterative loop [cite: 11, 12]. 

While developers are manually combining these philosophies—using a Ralph loop to iterate over an AgentCoder-style isolated testing agent that utilizes TDAD's AST maps for targeted testing—a monolithic GitHub repository unifying all four native elements was not identified in the provided sources. The current paradigm favors platform-level orchestration (like Windsurf or Claude Code) calling upon specific skills (like TDAD and Superpowers) dynamically [cite: 20, 31].

---

## 6. BMAD-METHOD Issue #843 and the TDD Integration Gap

### 6.1 Verification of Issue #843
The research notes confirm the existence of GitHub Issue #843 in the repository `bmad-code-org/BMAD-METHOD`. The issue is titled: **"How does workflow dev-story adopt the TDD model for development? #843"** and was opened by user `@MidasKylix` on October 30, 2025 [cite: 34].

### 6.2 Description of the TDD Integration Gap
The issue perfectly encapsulates the current limitations of multi-agent TDD workflows. The user describes a scenario where they followed the recommended process using a "QA" agent persona named `tea` (Test Engineer Agent). After creating a story, they ran an ATDD (Acceptance Test-Driven Development) command. 

However, the bug report states: 
> *"the agent dev still develops dev stories in the traditional way, seemingly unaware of the work done by agent tea and not following TDD. As a result, I have to tell the dev each time that tea has already done some work and expects them to develop using TDD."* [cite: 34]

This highlights a severe integration gap: the "dev" agent operates in a silo, ignoring the test-first context established by the testing agent. 

### 6.3 Corroboration via Issue #1784
This architectural flaw is further corroborated by a later issue, #1784 (opened February 27, 2026), which directly references the underlying mechanics of the problem [cite: 35].

When the `TEA` module's ATDD workflow runs before the `dev-story` workflow, it correctly creates test files populated with `test.fixme()` (Playwright's skip mechanism) to represent the RED phase of TDD. However, the `dev-story/instructions.xml` is not "ATDD-aware." It instructs the developer agent to "Write FAILING tests first" as if starting from scratch. 

Consequently, the developer agent implements the source code but completely ignores the pre-existing tests generated by the QA agent. It never removes the `test.fixme()` tags, meaning the tests remain permanently skipped. The proposed fix involves updating the workflow XML to force the dev agent to verify that no `test.fixme()` calls remain, thus strictly enforcing the red-green-refactor cycle [cite: 35]. This documentation definitively proves that while multi-agent TDD frameworks (like AgentCoder) show massive potential in controlled academic benchmarks, their implementation in open-source developer tooling faces significant state-management and inter-agent communication hurdles.

---

## 7. Discussion and Academic Implications

The synthesis of these six claims reveals a distinct trajectory in the field of Agentic Software Engineering.

1.  **Context Over Procedure:** The TDAD findings regarding the "TDD Prompting Paradox" fundamentally challenge early prompt engineering paradigms. Forcing an LLM to follow procedural steps ("do TDD") consumes context windows and increases regressions. Instead, providing deterministic, structural data (like AST dependency maps) allows the model's natural reasoning capabilities to shine [cite: 2, 9].
2.  **The Benchmark Illusion:** The massive 96.3% success rate of AgentCoder on HumanEval [cite: 13] versus the struggles of models on SWE-Bench highlights the danger of benchmark saturation. HumanEval tests function-level algorithmic completion, whereas real-world software engineering requires repository-level context, dependency management, and long-term planning [cite: 15, 16].
3.  **The Test Generation Bottleneck:** CMU's TDFlow research provides the most vital insight into the future of AI coding. The fact that LLMs can achieve a 94.3% resolution rate on SWE-Bench Verified *if given human-written tests* proves that the actual coding and debugging capabilities of modern LLMs are already at human parity [cite: 19, 36]. The final frontier is autonomous test generation. If an AI cannot write a valid, unbeatable test, it cannot autonomously navigate a Ralph loop safely [cite: 5, 36].
4.  **Ecosystem Maturity:** The explosive popularity of the `obra/superpowers` framework (124.4k stars) demonstrates massive developer appetite for structured agentic workflows [cite: 21]. However, as evidenced by the BMAD-METHOD issues, the connective tissue between specialized sub-agents remains fragile. Handoffs between QA agents and Dev agents frequently break down without strict, programmatic state enforcement [cite: 34, 35].

## 8. Conclusion

The evaluation of these claims confirms that Test-Driven Agentic Development is shifting from theoretical exploration to practical implementation. Tools like TDAD prove that pre-change impact analysis through AST maps drastically reduces code regressions [cite: 2]. Multi-agent systems like AgentCoder and TDFlow demonstrate that decoupling roles leads to unprecedented success rates, provided the agents are given high-quality, ground-truth tests [cite: 13, 19]. Finally, the widespread adoption of frameworks like `obra/superpowers` and the ongoing debugging of systems like BMAD-METHOD signify that the industry is actively solving the orchestration challenges required to make fully autonomous, repository-scale AI software engineering a reality.

**Sources:**
1. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGVj8OQAZCizeYVd_CMxo8hnufD01oaQz_w6JdVn--OD5vV2DsTAtUxyJ826JmGIRf4OmaMTNF8B3xNsGO8SgWW62USZUPmjxgpu4JamYjvv7KG7CxFD_dbktpFIfMjHBdjk8aCFS8zpB3qACRaZ0NU)
2. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFW6mmeylrq27k_AlfhF5J7-bgiZcrfB2--sH1LVu0YqaVhTN_ZtDCsQV-FdbcGiF9khk3LrBpLXUH3Y9rSgaluq1PwklKjrOhPpDZuSqntZUxC4g_f5NwQgg==)
3. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGf02xXVurszxaxs-6kdT4Xd3mRG4eJN4Vcuji9Z542oj3S_Fz5UCbkgbn-gRLBAcLvy9CYgqjHPxNj3wlXzQyXSK_UNzJXH5mxqA-IN26v_s7DHYNqBQ==)
4. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFpD516Ba34maskvig5e6baBMOb6BUoxpHBiKLCyfYL_Rk2W8Zg3Ylp-pXUBAw0QGD-NokyZTI2h8zfNd6F8VZvWfQZfn1BMTG2pQaVYK7Tockvq5FexSdJIFLTdaPOsT-VwIgWrOvABKtt8H1pFH7RTUhN1kfV3ZwvKM7-N4oG_wz-P2Y9IIg=)
5. [thelgtm.dev](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGJEi6aawf50Na5tIoIXzCnXyFFiT67jcwilfVr5sve6crn6qbzE0b-94CNcNVz1M6nCVL3nodQK6Dy5Y17RM3MKURvIdk5aZ9fbK78_pnGI17kOtJ1MY86YjMglZJgEgSMjHBv)
6. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBjPH0BI3Sei7VUTLMPxHNEBJ1pCifFKI-3VJNf7abyIGWeb0bqkR5STSxfYCmxTj1GJcZjYkSkvWoFZxRkYcEYe7c6sCjoxWUnvsWLpDUK6B8av-Jnzu4ww==)
7. [catalyzex.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGd8NH4WWr2jcb-yw9zwJOfVya6I2xDvyHsveJyohw3QxN63t2nA6daSu0XzHZfeCUoZH4n69wN3TrnzLwyE7re-LOW5JGCq5rDVCPjdqez6jHXh28G9XTJyGxH_MYG3idO9pfnsM-fObyjaSQfScRFxYubIZToiGHjZKeHZqsCfhiOEw==)
8. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEHM_L7uHQUgtI-0BXvQIi_QBIt3eGBD0s_V6mfBKPba2hWt2RlgNBFky61MKUPfX2th0DhMki35oBR72Pk6hLiTvmB5-0zytMDyWbx9iplF6J_bFkBGAnyALrX8f_V3WY8YeOZ-ZjtAkav3XrYyR02xYQmSrLwpPq-0fXs_-zceOUbGCXgxqPbDdQHtXSK8bDvGiDhKGUrrNSmdQtEFlhwhc4zdH8jsHxfKt6fvTVwr04HFWSf4TGwSCPSdcEQZddfeGAgHBYHVQ==)
9. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHxf8yrM4Koz4EHCpydBgmfEmavNP3qV8m2UtgNLIHBTfrK86lgK03kJTMouVac_6l1HPijeWgZlH2_zSYJF4I9z-jto_Cou-osvR8uf82h4_I4A_3ZeEIrbYVBQFmfRdLB)
10. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFfCzgHeu5Xk3-HqCMHw2xP9_CoZfvRL-0_9Mn66g9VklqjmAoB-YqTUVItME7BrERVLELgg47FVRSSJeUFaXopE8bwkN8mwaQHTPomLBP12M0tVU4zxQ==)
11. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHEu3yQ2qC7Bf7zCV1Cmf3mmFoIs0c2G5rfmDE-dPpj14bgOzw1-8Hb_G4Q3vRCpr8lxIwwZ7dU_KnkLW3Bf9KDfZOJIvAzVbZ4iM5881N8Papm27q4z6J56axzbmIIw5quL3WwBJnfqGSpxR2HchsagnBj3hMBAZzlsn5BBq2aRoZffssWOGNNl2QnG8jghVPKtVVo8B38)
12. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFU-fMLEIodm9KX5yjuh4kvsnI5IHF1fE8jGzLFF9R1uIxj27v90oZIX1l05OEFtXQpgKfFBjySUX5xZ2nstkLv0Oo7Ko0atTOQTxWoNMaxoexomHawpfoyMCx5fVP_oFOJuubjBZ-Asp7O7xg_EBfbYOM6euycRC6Dhqj_faChdt_g_RI-xJK_ckc1aBaJfxwrJkKJZ2uU5lH2Tw==)
13. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEGkCreprkFDkivI11TymajrU-C2fZCD5JKFzNGIFB6AJxMb-SyWut94sOLWCR33rMCGZtj_CJUeQqMkktkstr-Z-9qQaWTJoxPrY2YVs7WMss-f8SnNPSjLQ==)
14. [emergentmind.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEnvUbJuHKSpg8djwk0YDGAMKKyQ1JCcyNXpA-kg3kTT9cMlHU2tiS86WAUYscL5bIdHGAshyBifeKwKxaGOGPeP1ZUUuwk8qYXdrkT54o7Q-cHM_HKwq9AD8Z7rbQAnXEfG2hy)
15. [klu.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGqzlqvJ1Zba2UJtTiYirFaUuRr42T1DWt9H1sQTWhuHy06qWNEN4Sw42J44YLp0R-IM1LFOVSxZkzplZihL-xQOd3BZOOwey7BM9vvaYgCycC9JcOuS9eMyOGamJEj-mxE)
16. [gtlaw.com.au](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHuX-pU_Qhxn4kOjah1B026i4tN0Ou6_xUqPIiUsuVgt-_AS65_SCM_cb9ZEn5dh7nLgTohiZcDfozPBO6Cn6TKHBdabYvc_0Tm-FlcPIQWRj7VJ9e-s0hTRmOjeYz8Jmj5IegiS9ZEjgtyHok0aHImlA02K_UvwNzL43w=)
17. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFYqV-nypLt9zAncJl31QhLzM4nkoAHd9TNZpOfK2v560m-q4u2nnA4MbS3EXkv1Rub9xe5I7Epx-xghkLQjE7_SMPpz43Kc6odxMivKxg5G_1Ub-KAiwiC0xK7ze5T9WngnaclSZCw55vxIVRD04whwHENK0i6Eo46ne0S-KbWOYllkpUL)
18. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF8SnADHXKIPp_dv3Mg0CC_KmMK11eX1oGYS0XwPZnjBvDxyx8l3rxAhuWxQbeWwIJ6BcNu875CdOSXfJWhNqk7kZEziNsS6TMtd4fpl7FcaWftAgG46gBdmg==)
19. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-RoG6asu9mG1hK6KZh-VbjsV_Psl2jZrD6aOuok9k2fvInPitdrkzEL5pXpsfm84-sn3Gcde4zm5oCgKTIWmjfmtWUfkPostrmCDtKhWEG5zT4-kb7Q==)
20. [vibehackers.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEkTch3trNzInLzzSPPzIxysTpXU54HpX86M8wHftlTyP7WFKeSfhkzGPfEKhGdzUAaFOmgnRKgmfLwt-VUqAATgwHYLBjuwatoPDfa_CxsvWlRgr1AM9kfT8vxFm_o-JeumgI=)
21. [star-history.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHcbGgm9lPmr8c4PdEXQT3w0Nsxd0HBxO-ghYbfeT2KIxntkC8hKJc9EtEo5WPiUo2DB0rDacY0bgRkuqFbsvMAa8q-chB5lvR-SeTt4EPe0LYWfkE4wPn4oyO2qfcsLntUSDA=)
22. [pawgrammer.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEqGBTK7iA948yb6OvOeCQRlmAZO3VlWjSeLWWyhE6hI9xpxl2G2FUjUcLLTSLDi17yRFT2U9Jttq_JfNhhPd8byu7VCJRGAYSm9fmSIG0k7PSpqx1xbfC7UnmbazjUy_S07KKmAIVfCklSjr8Bhw9-W-AsJ5Q=)
23. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHGuxD2bA2zzoNI8rYdk9c05z-AeckQEF3J_DhKNqF60lIfTSbpwVH8VnAgQVl0iEXw3x1hIE4Xr27lZA17EfXCkc-mdRu7AlS2ExJ4TpQVbAS_9BCVrtlaIydKpynMRFA=)
24. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH9xw3wX6X-B5sNCqfSD79iYBbrxPOmquT-cPx4ZlOt8JkrFEd-IO58KUF7C6R6DVdIiGz9G1GcdBwJ8-0ylxPWvQzO0dGQMwFlf2yxhfV9Cyq6fhzkHkWolJIH8bZwFYHSUE235Nr-yVLJkOWR7FcyGYu1Avhdu5J3GsbX6qWUWDfpSin9VtA=)
25. [learncsdesign.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEW60GzWJ768tw6LtMcn0qxtJbi0fNbojPJYQCzmN3PQ5XG-WyScHO3q6p-sotjI9lyPbHoV0X1u-FUa4l4WUMtNFf4cM7OOIjUuzuPhwD1ZWzVnMcIY74399KvyAwsR3kXh61Sg_bJ1_P46ZxN_EDzpvXpEA==)
26. [bitsrc.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEUPPM13U-h9Y2CICWpsHbjU4DKDzIg5SkXieOV8qK-8H1E6muOzy_6taakL7YuUAGTKqakLTXd2Llwqt4y23WgG_s1pvMl_OITvNmeCyOkFMKt34N6wMySpG3C1lMDKIk2IscdhLraBaSijeHbqsmkRreHXNWz3kGfIR4hC_xdF5JFBYM7L6DS8Zluj0-FTmzkj7z0zm75pEWb)
27. [generativeai.pub](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGW0QqLYNgo-BM4j9zL_iiQCRR1lDD6ega5CYQaup-JrKZSee3fXNqaGSfoOWbTFXTFjQK_1RiiPFMdE1FbsVywjmKUFYCWOoOJNnbt7CVcVz9MrFctKT3pE2KG3-0H2ITz8BMZFVGSRq-3jXCvIIjJoeTLBaV8KAHo5IljEMJVATZsB1AcH6sN_CyDWEnA)
28. [fsck.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGsRYOTKayyT7-PQYJS6Z-WDejNGu1cj0F_q85LNUFgY5g9d3-yfBYAuAo4ykYg4Bp8JeFuMib0CfW46TB7ZIgKY5PQ_gL4I0GRtgXAkpEcTUGhuOFGDm8yT-kcMVKVFgZLTcY=)
29. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEt7O4prdSEzE4C-pibyzHYt1y3ecFWgjWFhlh_ArD1Ol16SZKa9tW4OO6TziO4xTmliJO5a5jwQEfEA558MzEHBb2Xeb__o5iwLSpLtHmU4ASAnqbVd-X47w==)
30. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEREL6QdHbo-phd-csmqVmYR8TBOmtnYV-gJ0XkXbGOjzcajhXkeAX_xZNUWS_hdWurjF7F1LOoAMAvKPsnRFFvnOAghRD3_BXdWMMOT86lt-AmVuyJWLLFP1k2wdw=)
31. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFlBHVQFBsc_XHhPOmFL-1yNH_SKDZUaxruSP3GggUMftTNmXwpRVUrhVQppOCpg8Hex8ZR2Gb-Lkg54L7k5__86Cw4JVOPvKUC91RjQDx7EGInEiR4DTl6wY6oVAy_myxgzErgPHPT0ZjIXxn9WPW2vlDPHE_bh6IlT6qpRrRoDyS2XcceM6OKowWsHgJeRSZJM_U3kpbgWqE=)
32. [trukhin.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQERAESum2LNagmJgzENHCc66Nj0kwtri2iYaGO5D59zl2f3zYaHkB2PIp5pKmnVM9fvhRGZHGTeJU17UwgJTZunNTQ7SnnstE2svdA_j-hDrvRrmU6T3bM2ltd3JGROg1FtdBm9w26v3AbPmv3X4cusotbUE1qpeH9J4Fr_8XvNq09GlOEuJ_3ml7eJHUtYujHDXmrZo5p30dwerA-YDnOWhqp8zWS5AOhGXA==)
33. [skillsmp.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFVAzXB56wtlK8KAqWwxUD0fCtA9_yZQ-Z-48ISKoI0Jfr3BoWU8Jpg3x0KDtefg6O5kMAXtQnqO200smXA6CHLuhWdgWBlF-5S-IQQP3NGcCk_Ot75Fc46P3r7V60W03aXZYHshf28-nKdzbyV-rja1MibXM4HFQ5hJwcknaXG1_byBhw=)
34. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEcqYkyd693xE6b5W4Ba-QtBmQJRtdulaFaySxjkHGPJLK1qOe3jIqkRqxywDffg2waN4zwOL-O4ILNZeENY0ZzzG2Ykp0rbU8rdFEx4s6qDoTc6VlmsVfMgb_bUdHSf-nTh_zqigxfPFmdAkYB)
35. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHfKReIRGvBiGe9c7QgNdvPBlU4rR21ttqdXe6y2MZ6pz81TxDMbmihzOMllcH0NVIp6x1ZCPw0kAeC4CgRYoluWng__FpL6pWNgmQKtg3MacpbwSui1Ou9PQYJD4NkHDLFGBg7ELMcZv-ztHiT-g==)
36. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHHy82XTQWMDKgmmCRuSbK1V_p_GtyxZoW9kd8GfpByo50A2j-IWZ0nYjVWlNz5ButgVrlsnMQ1kGG46401Piuy_P4t9ygAoy04jgX8MNom50EDzuto3w==)
