# A/B Testing AI Coding Workflows in 2026: Methodologies, Metrics, and the BMAD vs. Superpowers Showdown

Research suggests that the era of unstructured "vibe coding" is rapidly giving way to disciplined, agentic workflows. As of early 2026, the software engineering community has largely accepted that autonomous artificial intelligence (AI) agents require strict guardrails to prevent context degradation and ensure code quality. It seems likely that comparing these disparate workflows requires far more than rudimentary code coverage metrics; rather, a synthesis of automated benchmarking, mutation testing, and controlled A/B split testing is necessary. The evidence leans toward methodologies derived from the SWE-bench framework, augmented by stringent verification pipelines like the Early Quality Score (EQS), as the gold standard for evaluating framework efficacy. 

*   **The Paradigm Shift**: Developers are transitioning from reactive code generators to proactive engineering partners driven by structured pipelines.
*   **Framework Divergence**: Solutions like BMAD enforce an agile, multi-persona enterprise simulation, whereas frameworks like Superpowers enforce strict Test-Driven Development (TDD) via subagent orchestration. 
*   **Evaluation Complexity**: Benchmarking AI-generated code quality requires advanced metrics, notably mutation scores, to detect when an AI has optimized for code coverage without actually verifying functional logic.
*   **Standardized Methodologies**: Adapting the SWE-bench methodology—providing isolated environments and real-world GitHub issues—appears to be the most rigorous approach for head-to-head A/B testing of these agentic scaffolds.

## Introduction to the Agentic Workflow Ecosystem

The landscape of AI-assisted software development in 2026 is characterized by a stark departure from simple autocomplete features or ad-hoc conversational prompting—a practice humorously dubbed **vibe coding** by Andrej Karpathy in 2025 [cite: 1]. Vibe coding, defined by developers providing vague prompts and accepting whatever code the AI outputs, inevitably leads to code that works in localized demonstrations but rapidly degrades in complex production environments [cite: 1, 2]. 

To counter this, a robust ecosystem of agentic coding frameworks has emerged. Collectively boasting over 170,000 GitHub stars, five major frameworks—BMAD, Superpowers, SpecKit, OpenSpec, and GSD (Get Stuff Done)—are competing to establish the definitive standard for AI development methodologies [cite: 3]. These frameworks operate on a shared architectural triad: agents (the personas or subroutines), workflows (the sequential pipelines), and skills (the atomic capabilities such as writing tests or generating Product Requirements Documents) [cite: 4]. The fundamental debate in the academic and open-source communities is no longer *whether* AI needs structure, but rather *how much* and *what kind* of structure yields the highest quality software [cite: 3].

This report exhaustively investigates the methodology for A/B testing different AI coding workflows, explicitly addressing head-to-head comparisons of BMAD versus Superpowers, the formulation of controlled tasks, the SWE-bench methodology, and the advanced metrics required to ascertain true AI-generated code quality.

## Review of Major Frameworks: BMAD vs. Superpowers

Before establishing an A/B testing methodology, it is necessary to define the operational paradigms of the frameworks under comparison. While both aim to maximize autonomous coding quality, their architectural philosophies are diametrically opposed.

### The BMAD Method (Breakthrough Method of Agile AI-Driven Development)

The BMAD framework (holding approximately 37,000 GitHub stars) approaches AI coding as a simulation of a traditional enterprise software development team [cite: 5]. It replaces the singular generic AI assistant with a coordinated suite of 12 or more specialized agent personas, including the Analyst, Product Manager, Architect, UX Designer, Scrum Master, Developer, QA Engineer, and Technical Writer [cite: 2, 5]. 

BMAD operates via "Agent-as-Code," defining each persona in structured YAML or Markdown blueprints that dictate their expertise, responsibilities, and expected output formats [cite: 3, 6]. The workflow follows a rigorous four-phase agile cycle:
1.  **Analysis and Planning**: The Analyst and PM agents draft comprehensive Product Requirements Documents (PRDs) and break them into user stories [cite: 3].
2.  **Architecture**: The Architect agent generates system designs based on the PRD [cite: 6].
3.  **Implementation**: The Developer agent writes code [cite: 6].
4.  **Verification**: The QA agent validates the output against the acceptance criteria [cite: 2].

BMAD also features **Scale-Adaptive Intelligence**, allowing developers to select different workflow depths based on task complexity. For instance, a "Quick Flow" bypasses full PRD generation for simple bug fixes, whereas the "Standard" track enforces full architectural planning for greenfield Minimum Viable Products (MVPs) [cite: 2, 7]. 

### The Superpowers Framework

Created by Jesse Vincent and possessing over 7,800 GitHub stars, Superpowers operates as a sophisticated plugin for CLI coding agents like Claude Code or OpenCode [cite: 1, 8]. Unlike BMAD’s enterprise simulation, Superpowers relies on automated, contextually-triggered skills and an unwavering enforcement of Test-Driven Development (TDD) [cite: 1].

Superpowers is defined by the following architectural constraints:
1.  **Mandatory Brainstorming and Design Refinement**: The agent is programmatically forbidden from writing code immediately. It must first interactively elicit a specification and draft a bite-sized implementation plan [cite: 8, 9].
2.  **Iron Law TDD Enforcement**: Superpowers enforces the RED-GREEN-REFACTOR cycle. Crucially, it utilizes a strict "delete-and-rewrite" rule: if the AI writes implementation code before writing a corresponding failing test, the framework intercepts and physically deletes the production code, forcing the agent to restart [cite: 3].
3.  **Subagent-Driven Development**: To prevent context pollution—a phenomenon where models degrade after consuming roughly 50% of their token context window—Superpowers dispatches fresh subagents for localized, 2-to-5-minute tasks [cite: 1, 9].
4.  **Two-Stage Quality Gates**: Each subagent undergoes an automated internal review. The first stage verifies specification compliance; the second stage reviews code quality [cite: 9].

### Head-to-Head and Controlled Comparisons in the Literature

Addressing the query of whether controlled comparisons of BMAD, Superpowers, and custom TDD workflows exist on identical coding tasks: the most prominent analysis in the 2026 literature is provided by software engineering researcher Rick Hightower in his series, *The Great Framework Showdown: Superpowers vs. BMAD vs. SpecKit vs. GSD* [cite: 3, 4].

Hightower's practitioner comparison executes head-to-head evaluations of these frameworks. The analysis concludes that BMAD excels in enterprise-scale compliance, traceability, and managing complex multi-repository projects via context isolation per persona [cite: 1, 10]. However, BMAD can be considered excessive for individual developers or minor features [cite: 1]. Conversely, Superpowers excels in strictly enforcing coding discipline and ensuring logic verification, though its effectiveness is heavily reliant on the availability of robust subagent infrastructure and test environments [cite: 1, 9]. 

Furthermore, community efforts have recognized that these workflows are not mutually exclusive. The community has actively experimented with **hybrid workflows**, such as combining BMAD's persona-based architectural planning with Superpowers' rigorous TDD implementation gates. This combination yields BMAD's detailed traceability while preserving Superpowers' robust code quality guarantees [cite: 3]. Tools like **Bmalph** have even emerged to bridge BMAD's planning outputs directly into automated execution systems, demonstrating the community's drive toward standardized, interoperable pipelines [cite: 11].

## Metrics for Comparing AI-Generated Code Quality

Evaluating the outputs of varying AI frameworks requires moving beyond traditional software metrics. LLMs are highly proficient at optimizing for proxy metrics, leading to the phenomenon of Goodhart's Law: when a measure becomes a target, it ceases to be a good measure [cite: 12]. Therefore, an A/B testing methodology must utilize a composite suite of metrics to evaluate the true efficacy of an AI workflow.

### Traditional and Operational Metrics
While not definitive on their own, traditional metrics remain useful for baseline operational assessment:
*   **Time to Completion**: The wall-clock time required for the autonomous agent to traverse the workflow from task ingestion to successful pull request generation [cite: 13, 14]. 
*   **Lines of Code (LoC) / Diff Size**: Useful for detecting "hallucinated bloat," where an AI generates excessively verbose implementations instead of utilizing standard DRY (Don't Repeat Yourself) principles [cite: 8].
*   **Test Pass Rate**: The percentage of standard unit tests that pass post-generation. While necessary, a 100% test pass rate does not guarantee code quality [cite: 15].
*   **Regression Count**: The number of pre-existing, unrelated tests broken by the AI's code injection, serving as a primary indicator of how well the framework's context-management preserves the broader codebase integrity [cite: 15].

### Advanced Verification Metrics: Mutation Score

The most critical metric for evaluating AI-generated code is the **Mutation Score**. Research consistently shows that when AI agents are prompted to write tests (a common step in frameworks like BMAD and Superpowers), they optimize for Code Coverage [cite: 12]. An AI will systematically generate inputs to exercise every code branch, achieving 100% line coverage. However, the assertions generated often merely mirror the implementation rather than verifying the actual business logic [cite: 16]. The tests verify that the code *executes*, but not that the output is correct.

Mutation testing addresses this "facade detection rate." Tools like StrykerJS (JavaScript), mutmut (Python), or PIT (Java) inject deliberate, small semantic faults (mutants) into the source code—such as changing a `>` to a `<` or swapping an arithmetic operator [cite: 16, 17]. The automated test suite is then executed against the mutated code.

*   If the test suite fails, the mutant is "killed" (the test suite successfully detected the bug).
*   If the test suite passes, the mutant "survived" (the test suite possesses a blind spot).

The Mutation Score is defined mathematically as:
\[ \text{Mutation Score} = \left( \frac{\text{Total Killed Mutants}}{\text{Total Valid Mutants}} \right) \times 100\% \]

In the context of A/B testing frameworks, comparing the Mutation Score of a BMAD-generated feature versus a Superpowers-generated feature reveals which workflow instills deeper, more rigorous logical verification [cite: 12]. A high mutation score (typically >80% for critical logic) indicates that the framework's QA or TDD prompt chains are highly effective [cite: 16, 17].

### The Early Quality Score (EQS)

In late 2025, to provide a unified framework for evaluating autonomous test agents, the industry introduced the **Early Quality Score (EQS)** [cite: 15]. EQS is a composite metric that acts as a definitive benchmark for A/B testing AI test quality. It is composed of three dimensions:
1.  **Code Coverage**: The percentage of code executed by tests [cite: 15].
2.  **Mutation Score**: The percentage of mutants caught by tests [cite: 15].
3.  **Method-Scope Coverage**: A structural metric measuring the percentage of public methods that have dedicated, direct tests achieving 100% coverage for that specific method [cite: 15].

By calculating the EQS for the outputs of BMAD and Superpowers, researchers can definitively quantify which framework produces software that is resilient to regression.

| Metric | Definition | AI Evasion Risk | Utility in A/B Testing |
| :--- | :--- | :--- | :--- |
| **Test Pass Rate** | % of generated tests that pass | High (AI writes trivial assertions) | Baseline qualification |
| **Code Coverage** | % of source lines executed by tests | High (AI executes without verifying) | Secondary indicator |
| **Mutation Score** | % of injected faults caught by tests | Low (Requires logical rigor to pass) | Primary quality indicator |
| **EQS** | Composite of Coverage, Mutation, and Scope | Low | Ultimate framework ranking |

## SWE-Bench Methodology: The Gold Standard for Agent Evaluation

To determine how researchers compare different agent setups on identical benchmarks, one must examine the **SWE-bench** methodology. Introduced by Jimenez et al., SWE-bench has become the preeminent standard for evaluating AI coding agents on real-world tasks [cite: 18, 19]. 

### Architectural Setup of SWE-bench

SWE-bench consists of 2,294 historically verified, real-world GitHub issues pulled from popular open-source repositories (primarily Python) [cite: 20]. The methodology for comparing two different setups (e.g., BMAD vs. Superpowers) follows a strict, deterministic sequence:
1.  **Environment Isolation**: For each task, the coding agent is provided with an isolated Docker container containing the exact checkout of the codebase from the commit immediately prior to the issue's historical resolution [cite: 19, 20].
2.  **Agentic Harness Constraints**: To isolate the performance of the *workflow framework* rather than the foundational Large Language Model (LLM), researchers standardize the tools available. The agent is typically given a minimal "bash-tool-only" harness, allowing it to navigate, search, and edit files exactly as a human developer would in a terminal [cite: 19].
3.  **Task Execution**: The agent is provided the text of the GitHub issue and must autonomously generate a `.patch` file (a code diff) designed to resolve the bug or implement the feature [cite: 18, 19].
4.  **Deterministic Evaluation**: The generated patch is applied to the codebase. The system is evaluated by running the *actual historical unit tests* that were written by human maintainers in the pull request that closed the original issue [cite: 18, 20]. If all tests pass, the run is marked successful. 

Metrics reported typically include **pass@1** (success rate on the first attempt) and **pass@3** (success rate within three attempts) [cite: 20].

### The Importance of the Agent Scaffold

SWE-bench explicitly proves that the "scaffolding" around the foundational model—the workflow framework, the prompts, memory management, and context engineering—is just as crucial as the foundational model itself. For instance, the Verdent AI agent demonstrated that different frameworks utilizing the exact same LLM (e.g., Claude Sonnet 4.5) achieve drastically different success rates on SWE-bench due solely to their workflow methodologies [cite: 20]. 

### Limitations and Evolving Methodologies: UTBoost and Mutation

While SWE-bench is rigorous, it is not flawless. Researchers discovered that relying solely on human-written historical unit tests poses a risk. The **UTBoost** study revealed that even expert-verified unit tests (in the subset SWE-bench Verified) missed critical edge cases [cite: 21]. AI agents were generating patches that passed the evaluation tests but introduced bugs elsewhere in the codebase; fixing these test gaps resulted in leaderboard ranking changes for 24% of the evaluated agents [cite: 21].

Furthermore, to prevent AI models from simply memorizing historical GitHub data (overfitting), researchers have begun utilizing **benchmark mutation methodology**, transforming public problem descriptions into novel, internal benchmarks (e.g., SWE-Bench C#) to measure true zero-shot reasoning [cite: 22]. 

## Designing a Controlled Task for Workflow A/B Testing

To perform a head-to-head A/B test of BMAD and Superpowers outside of large-scale SWE-bench evaluations, teams must design controlled, constrained tasks. Based on A/B testing methodologies for standard AI prompts and software testing, a good controlled task must possess the following attributes [cite: 22, 23]:

1.  **Isolated Domain Scope**: The task must be an isolated feature that requires reasoning across multiple files but does not require deep, tribal knowledge of an undocumented proprietary system. 
2.  **Known Correct Answer**: The feature must have a deterministic, mathematical, or rigidly definable end-state. 
3.  **Measurable Success Criteria**: Success must be evaluable via automated, hidden test suites that the AI is not allowed to view during generation.

### Example Task: The "Online Library" Implementation
A practical, community-validated example task used in framework comparisons (such as those by Vishal Mysore) is the creation of a bounded web application, such as an "Online Library" [cite: 10]. 

*   **Requirements**: Browse books by title/author/genre, implement search functionality, and handle pagination.
*   **Workflow A (BMAD)**: The prompt is handed to the BMAD master orchestrator. The workflow executes the PM, Architect, and Developer personas. The output is tracked based on architectural document generation and final code implementation [cite: 10].
*   **Workflow B (Superpowers)**: The prompt is handed to the Superpowers agent. The workflow triggers mandatory brainstorming, generates a spec, creates failing tests for pagination and search, and implements the subagents to fulfill the tests [cite: 9].

By running both frameworks on this identical prompt using the exact same underlying LLM (e.g., Claude 3.5 Sonnet), and tracking trace IDs for variant outputs, researchers can cleanly compare the metrics [cite: 23].

## Community-Validated Methodology for A/B Testing AI Workflows

Synthesizing the concepts of A/B automation, SWE-bench isolation, and mutation scoring, the following is a proposed, rigorously structured methodology for A/B testing AI coding workflows in 2026:

### Phase 1: Environment and Baseline Setup
1.  **Standardize the Foundation Model**: Both frameworks must utilize the exact same LLM API via a unified proxy to eliminate model-level variance.
2.  **Containerize the Workspace**: Utilize isolated Docker environments for each test run to ensure identical starting states and prevent cross-contamination of cache or context [cite: 19, 20].
3.  **Define the Test Suite**: Select a subset of tasks (e.g., 50 randomized problems from SWE-bench Verified or a custom suite of internal feature requests) [cite: 18, 20]. 

### Phase 2: Execution and Traffic Splitting
1.  **Routing**: Utilize an automation engine (e.g., n8n or Make) to randomly split the task prompts 50/50 between the BMAD framework and the Superpowers framework [cite: 23].
2.  **Traceability**: Inject a unique `trace_id` and `variant_label` (Framework_A or Framework_B) into the telemetry of the execution run to track the metadata [cite: 23].
3.  **Resource Constraints**: Apply hard limits on token usage, execution time (e.g., 1 hour per task), and API costs to measure efficiency alongside accuracy.

### Phase 3: Multi-Dimensional Evaluation
Once the patches/features are generated, they must be subjected to an automated CI/CD evaluation pipeline:
1.  **Application**: Apply the generated code patch to the pristine codebase.
2.  **Hidden Test Execution**: Run an exhaustive suite of hidden unit/integration tests that the AI agents were not permitted to view. Calculate the **Test Pass Rate**.
3.  **Mutation Testing**: Execute a mutation testing tool (e.g., StrykerJS) across the files modified by the AI. Calculate the **Mutation Score** to determine if the AI's logic is brittle [cite: 16, 17].
4.  **Static Analysis**: Calculate the Lines of Code (LoC) delta and method-scope coverage to derive the final **Early Quality Score (EQS)** [cite: 15].

### Phase 4: Statistical Significance and Conclusion
Aggregate the metrics across the 50 tasks. A framework is only considered superior if it demonstrates a statistically significant improvement (e.g., 95%+ confidence interval) in EQS and Mutation Score [cite: 23]. 

## Conclusion

The transition from vibe coding to viable, agentic software engineering is the defining narrative of developer tooling in 2026. While frameworks like BMAD provide unparalleled structure through persona simulation and planning [cite: 5, 6], frameworks like Superpowers offer unmatched logic verification through strictly enforced TDD and subagent-driven execution [cite: 1, 9]. 

A/B testing these frameworks requires a departure from trivial evaluation. As AI models become highly adept at passing standard code coverage checks, the industry must pivot toward metrics that measure true verification, notably the Mutation Score and the Early Quality Score (EQS) [cite: 12, 15]. By employing the containerized, deterministic evaluation methodologies pioneered by SWE-bench [cite: 19], enterprise teams can quantitatively determine which scaffold architecture produces the most resilient, production-ready code. Future research will likely continue to explore the hybridization of these frameworks, marrying the comprehensive macro-planning of BMAD with the relentless micro-execution of Superpowers [cite: 3, 11].

**Sources:**
1. [towardsai.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFlA6mbd2x_ft6si5b2-MPF-qIFZrZc4aEBgTx9CoOP7TVB6jRNv7BrtsBwMpnK_wdlQd__GWiDt5qTY1GyEeolzRoGT3Z8Wg8VfBKZEH6nMfViQHxhqemKBADv8clVf9JeyKtKsQpAbgxKQkBvjm-v3Tda8KT5DZyWlbLjaBKNxq24V5eXs-UTEwtXFqMMCU6PmSJdkKKhgTcxyvLRShTl-ZDjqEK7X-30ILmsZxFoC9OmjZBCq8WVQiLh)
2. [reenbit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHerlM3lq_p7esdftF7DjbPC1dVM6jJXi8lmJqZuA1tqz9Z2BhoJmTIbty2FKitt8E1BXDT29UApL2PR6tqh7Oppkk3TU-lntLLoB3JRnvrEtojH2hqTrpTwRtjDtAJPwmNDuQmPMPL5BwwRL0gjpwIyTKTnOiSs3Fgg_NYpPUwSvaaZdr9eDWU2f3YiM6pQaRAlJH5ei84-uOhOv4PmmcqaTSy)
3. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGIkIGH46UtqGncWKxtCrd-HrCF3pnO8lwab3l-3Nf5BRj4m17TXyY6qzqH1yUjHbcLV9CNL6OrImP7pfyy3Gj2n_TVLexhQNAcB9v8LLQA3PnmU6iemLftNgNtb2qhSeRV2EdfO9CS89voPJacal2KjbjZ2Yny5YpR_JEzauhuXv96CIylfYC8Zu2FgN3_Xi7JjKX5EPwrWxZKdZOynZYkmlwTNaC50LAFoA==)
4. [plainenglish.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHyHPRSGphHaWq_1nuHP57KvhmaPXu_isQHJzj8W3BvPCDrYvcsh7xv9eY975ZVP8paILzrsc81uqRuqnRC1LhJLpf4PFsoXk6nKAARRa6mLKvmM84dwk7ByYeU5IG2h_Wb0TL9QjbNzONndy89f5eMQKwsYB2fxgPLVrBKi5OXDIZ9uz5Y_TmLuV0RtgKEL4gAo1-uUTFTOFwDfCPFkv2O)
5. [rywalker.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEcTXIPjPD_xWRjdV8Xlb4_5eyuzNvReFGqnkcn9OSS4dpW7FRxZ1nuGU7_BjgaFBPEmIsSRlvTeglSV13kn_OyAbBOAYc0ff05BW6jGYbS0h_cYtSh5HnWXTCWDN0zWQ==)
6. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF8hCbN_mWGCliwIDghTOwfC0GmsNhs2d_LUc7ZWJDyQnYndJy9o9wbG9zMeeb_1yKAebgTovM4pNqKbksOKhIRu9bRYpvxYl7ai1hC6oeO_QgkXNYWsp4KNKteGqBmhLjaY2BfRLpoTk-1X5H0rvVrRsHI0JKwKLUZTL43bfgk68zSKMwyiYtZtU_1QgDg6BGMR2ou_o8_P503teDZ20AoKo6c6pfEGg==)
7. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFx_F4tEwQhNy8C0gk3BBabUJUtKKVZdk1X79iSQque4UnIf0qKj1fQzkLhKxiRWrMu47CIehtXJeV6oxiNxDh2_IBxFumSFrcWbymjg6l4tnWI8z5BtRDLvG_kh4EETQveOI9roPrbsGVVbUh4U9tjjRwPE7xtF_HULoxNftSYMQjDy923Ua-rotSn3lfDwcgkgkJdRN4d4bNveCy29TfWjOEMIHh4kyLqsKPqQComz9BfBePCYOPtDw==)
8. [mcpmarket.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG05GaJQ7Lc17dpRLWZbycu5RvDcQYhblCmv5QkZtYb83F20zDV2p6KFOO4eZmcmCEhu09aQMYdV1USJxxV71LLsVRF6fdRgP0QLU6dcF7yMvac4oZ49Dqp_01rk7Ej)
9. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF6sXoUhk64jonu5WOYiw_BTlo1bY7KCxegIZVlunpYXvnu9MIt4wWKTxnIzprpNBuz0bD9AGzW1XieBFBy_DAJOuZwuYuCulULPZHAWGeb9YFxhkTUAMi1XfSbIGkRtIvlSHpBHDRjXLGXElgmpsdLo9QOTT3jasK77iHDA4KVeszVdR8=)
10. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFA0x39We_aj5I6mOv7ekePtSz0QYwRteSh7fv-irkP2SpfNxo9auo7DAc0NeUxMDdQAeU8rLd3CuT8LLmNKR1UrumP6mTNnkL1hus_VoQz_VQvK1Z33xljst1HnDHO-jcpoU4y3qwcEvhfnBeC6P6U8BjeN-ODNBaJOVaP_XnYhAsl8nvq6DGRR5Xozh53UQT1rDd4gA==)
11. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFFVMoDydNj8O5Jp4nPrhezFEmUP_DMruB0agcrKWUg1Jmv7uPyUbpXZ4J20zWm22nH1mfhOPZvXsRmzN92unOy7rcg6AMcliCrBD_iGKKT6_nQIIUYOvsDC2lb4-YkqlC4aJIufa8moOk85HlTaZhIQC18rH6mFp1nW0EgyIuowsC7t-OMxMoxyInkzQYSqRBktlKOuay4eA==)
12. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFdXzhlDvqn1hL__udFGUGfJJpHn5V1cTjGjhcWhuvWjP2R6uaAZmFOiyHxqrBBdZzHWhNZnmcPpP-nxxpX1DYsEXcGXazT8BsrahL7YG6IJHdBzy6sZBLVJfap5OWbdx2rM-kUxZy73EwyeiVsq33cAKGsAG1NIjQOihXQ1T2zFqaIqy3rK2YVlFKJEyngVHj8LpUjuAw9G_Xx69HP0w==)
13. [sitespect.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHasXTckUxWHrbtYKe7t5dClfhIL10Y9WNd1p1cL66kudwrhcImctmWDFEhpjVqgaTT__hOmUo42ZZ2jGrerPNOyF44CVJQtZ4Bxl2hA4ZCVldT6Cf0JHsJH5HR0s_zeDWreqP0XCKuw7lo)
14. [pipedrive.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHdlokO77CqcG1qIiZc5l0LnxjZPklus0JsdQcUUiEvwoGmnYgWSa1EYYjo4ZdC6pclv9Qo95seV4l5qOoD7ELCYq67xxXjjxk5bxukJroamK6iQWUqNdsCz5QgFXn-I1ji2HJMvA==)
15. [startearly.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFcaAo1aviwlaK1qNzJNr0FJYX19PEViS4uKCPp2lZtmgWHASR4J5IYs-mghMTa_35kEaJsJ6X1SxgYotWAvexdnNT62VkQVeh5PtI2J-tenTSNjn9TX2oE6jLv-CfvZbAj0ozYLbnwUii10lHpXvirl7bhe-8VgkzTnQ==)
16. [super-productivity.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQENsFjzmks-8kP2lnMnelD0m_mwnOH94XXmV3HfzlxGAJs6l-Qj8UeV5L_wAhgLfR-jfSmSPBibO2G4Dy4iwsW0Cu-0pcqiD0-1BcfBK3Zl1qv4uVx4ciQBNv14wFFUPPo0RNdsNGM3WoEDUPlNMcvarSti)
17. [testrigor.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFXNVlnzocZF19s6wG-2tgqphXCI3SBlENUT7z5OYAtGGSEj7EFD5Y4RSbrSCB4h7NQMjYsC6M-w6Bkf6FGf8wB78Q-O1B_sDSDcPnjiwcDNPmQfWTCi0UJUUdOELq2ti5i7bZRDKtYhH2boVpynn6VXFhNk94rlT81_Ej5aG4P-9QlkdU8dQ==)
18. [cognition.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE_q93QWdymhTXlXIuV4ar0vV273H3x8x4cz267AMDtImQlpjgIxVynhleNVM-_4ofzv79-oImyiq3MWiO4T29EoSzPPNjIV5AazQ2CVHtFs2T1muaFVGTZ--qiJnlycfr2Cj9M79TqRkFU)
19. [vals.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHKFLDSu-d0xSuBfpJMhkub36_zY3-VUjvBLblznTKxCp6m2AhLX9vfeWDxMvjECsC1YMkWfq3MofHlqM1vBNi13JDlHn764U6NqxViDXqR48lqVsnVVrWeQ78LB98=)
20. [verdent.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFmrSsqe5iMErCvOl6k2vHi3a9di5Kf12qJN45mPWC-0DntunkUBy5EZbrxQrYQhdamuRy9pDxF_geV4JENfERppcTBCNgyZQMYajso3xzoTujIuGNqJ3bHGnopBWTFJdgwrRqRpgxuNqaTWwzhUTo9QZ1BUs8=)
21. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEhZWKwLVONAU92-aodHvIzfn1p_JtH54zzv6lujMxRupsLqyqxlgIt3zu9RP0df-mcIO7q-du6x3HP5ZwPVBQGzM9OI8_sQXe7T-qZg6jgtL745Ud782V76tPR1bEV-zXtAP4GHWI1-PttMbo1rP6magXBCgSOZgyl36YxhgPqZOcGwebI7CleVh4wyFC8GX-iEYkLZZaLt0pNWmMm1RHvumDTrxjtXeRFcDphy7Gmiv2cZOzMHagfgQQzZA==)
22. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFXC_dVWEcMbka70QIjN_uS0A5lxpdEPM3bWVutyGmeQeISxNkPPSAGEoiBG6nDcdOjszwzvyG1WVsYQ6CQ7KV6F_D5tcYFR0QJN7yKb6OmfHrB6nikeCoZ5A==)
23. [dev.to](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGBiqHV5OmyJ5oXjEVrNXeE_dDwv6NiRxDVPerYpc2C2w3xxPzu_dL4inja142xPYYP_7vk2Gu2FylV_eW7DKlJUXeVsSZ8Sd6W5DvCtU0-dUJBqiJLBsQ8GSVJySwAaJ_ghwLEghvgirDA1k9CsleBam8g_GFIhXHpZU0BBRdB9rF_rICYYeUSwWDggv1Y0xxO7fPw589foYD9)
