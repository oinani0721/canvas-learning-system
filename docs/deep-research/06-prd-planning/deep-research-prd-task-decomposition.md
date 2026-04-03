# Deep Research: PRD Task Decomposition for AI Agent Execution

> Source: 3 parallel Explore agents analyzing 25 subagent logs + project deep research docs
> Date: 2026-03-31

## 1. Optimal Task Granularity (Evidence-Based)

| Granularity | Files/Feature | Time | Success | Example |
|-------------|--------------|------|---------|---------|
| Optimal | 1-3 | 2-5 min | ~100% | "Add sourceCanvasId to TipItem in api-client.ts" |
| Acceptable | 3-5 | 10-20 min | ~80% | "Create layer3.md + refactor loader" |
| Risky | 5-50 | 50-200 min | ~50% | "Delete service + update all imports" |
| Avoid | 50+ | 200+ min | <30% | "Architectural pruning across codebase" |

Agent stall root cause: plan mode blocking (60-112 min mega-gaps). Fix: bypassPermissions.

## 2. Outer + Inner Loop

Target: stateless bash outer loop (ralph-runner.sh) + TDD inner loop per Feature.
Current gap: outer loop is manual, no mutation testing, no adversarial review.

## 3. Mutation Testing Oracle

Three layers: type checking (tsc+pyright) + E2E (Playwright) + mutation (mutmut).
Currently missing: pyright not installed, no E2E tests, mutation testing not triggered.

## 4. Agent Teams Comparison

Used: Agent tool (22 subagents). Not used: native Agent Teams (unstable on Windows).
Recommendation: continue Agent tool for interactive dev, Ralph Loop for autonomous CI.

## 5. Carlini Lessons

16 agents, 100K lines, $20K. Key: atomic task boundaries + external deterministic oracle.

## 6. PRD Feature Template

Each Feature must have: target files (<=3) + code example + machine-verifiable acceptance criteria + anti-examples.
Deletion tasks: split into 5 subtasks (discover -> clean -> delete -> verify -> commit).
