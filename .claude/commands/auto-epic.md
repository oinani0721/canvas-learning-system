---
name: auto-epic
description: Read PRD -> Subagent TDD -> mutation testing verification
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Agent
---

# /auto-epic

Automated Epic execution pipeline with mutation testing verification.

## Workflow

1. Read `PRD.md`, find the first Epic NOT marked `COMPLETE`
2. Read `PROGRESS.md` to understand completed progress
3. For each feature in the Epic:
   a. Use `Agent(subagent)` to execute `/tdd-cycle` (test-first development)
   b. PostToolUse Hook automatically runs the Composite Oracle
   c. If mutmut reports surviving mutants -> iterate to fix (strengthen tests or implementation)
   d. If vulture/knip reports dead code -> connect the pipeline or delete
   e. If integrity-auditor reports CRITICAL findings -> feed rejection back to Builder subagent for retry
4. All checks pass -> `git commit` (lefthook pre-commit hooks auto-check)
5. Update `PROGRESS.md` to mark Epic as `COMPLETE`
6. If all Epics complete -> write `ALL_EPICS_COMPLETE` to `PROGRESS.md`

## Key Principles

- **Test first**: Every feature starts with a failing test
- **Mutation-verified**: Tests must catch code mutations (no facade tests)
- **Pipeline integrity**: Every new function must have a caller (vulture enforces)
- **Auditor retry loop**: When integrity-auditor rejects, Builder subagent retries with feedback
