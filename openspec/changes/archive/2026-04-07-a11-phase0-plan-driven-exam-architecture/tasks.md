# Phase 0 Tasks — Plan-Driven Exam Architecture

> **Scope**: Pure design. No code changes. Tasks below produce the 4 OpenSpec artifacts (proposal, design, specs/exam-planning/spec, this tasks file). Implementation tasks for Phase 1+ are listed at the bottom under "Phase 1 Entry Points" but are NOT executed in Phase 0.

## 1. Proposal Authoring

- [x] 1.1 Write `## Why` section quoting A11.md user FR + reference 42-commit A11 schema-drift fix chain + reference deep research bundle commit `8f4a3fd`
- [x] 1.2 Write `## What Changes` section enumerating the 4 artifacts and explicitly stating "no code changes"
- [x] 1.3 Write `## Capabilities` section with `### New Capabilities` listing only `exam-planning` (no `### Modified Capabilities` since this Phase 0 modifies no existing spec)
- [x] 1.4 Write `## Impact` section listing affected files (4 markdown), risk=极低, rollback=git revert, and "design-context-only references" subsection mentioning algo-question + algo-rag without spec deltas
- [x] 1.5 Verify proposal.md uses `## Why` (NOT `## What & Why`) per CLAUDE.md hard format constraint

## 2. Design Authoring

- [x] 2.1 Write `## Context` section explaining A11.md vision vs deep research distinction + 5 Phase 1 Deep Explore findings + Constraints
- [x] 2.2 Write `## Goals / Non-Goals` section with explicit Goals (5 items) and Non-Goals (8 items)
- [x] 2.3 Write `## Decisions` section D1: plan-driven vs mastery-based co-existence (Choice + Rationale + 3 alternatives + Trade-offs)
- [x] 2.4 Write `## Decisions` section D2: plan file format (Choice = UX decision pending, marker `[DECISION-UX:a11-phase0/plan-file-format]`)
- [x] 2.5 Write `## Decisions` section D3: plan generation approach (Choice = TECH decision pending, marker `[DECISION-TECH:a11-phase0/plan-generation-approach]`)
- [x] 2.6 Write `## Decisions` section D4: KG relevance role in plan generation (top-down design rationale, defer deep research D2 to Phase 2)
- [x] 2.7 Write `## Decisions` section D5: 3-factor formula three-stage deprecation path (Phase 0 mark legacy → Phase 1 feature flag → Phase 2 demote to fallback-only, never delete)
- [x] 2.8 Write `## Risks / Trade-offs` table with 7 risks + mitigations
- [x] 2.9 Write `## Migration Plan` section (no code migration in Phase 0, just rollback strategy + Phase 1+ migration outline)
- [x] 2.10 Write `## Open Questions` section listing 4 UX decisions + 3 TECH decisions + 3 Phase 1 prereq questions
- [x] 2.11 Write `## Deferred` section listing 5 items out of Phase 0 scope (D1 segment commit, D4 doc drift CI, plan prompt templates, plan executor state machine, feature flag implementation)

## 3. Spec Authoring (specs/exam-planning/spec.md)

- [x] 3.1 Write `# exam-planning Specification` heading and `## Purpose` paragraph explaining high-level orchestration vs algo-question low-level scoring distinction
- [x] 3.2 Write `## ADDED Requirements` header (since this is a NEW capability, not MODIFIED)
- [x] 3.3 Write Requirement 1 "Plan File Generation" + 3 scenarios (multi-node canvas / empty canvas / reproducibility)
- [x] 3.4 Write Requirement 2 "Plan File Schema Stability" + 2 scenarios (version field present / no silent auto-upgrade)
- [x] 3.5 Write Requirement 3 "Plan-Driven Question Selection" + 2 scenarios (next-question reads plan / legacy formula as fallback)
- [x] 3.6 Write Requirement 4 "Progressive Difficulty Within Plan" + 3 scenarios (L1 starts on central node / L2 requires both L1s done / sparse canvas stays L1)
- [x] 3.7 Write Requirement 5 "3-Factor Formula Deprecation Path" + 2 scenarios (legitimate fallback INFO log / unexpected invocation WARN log + regression test)
- [x] 3.8 Verify all scenarios use `#### Scenario:` (4 hashtags, NOT 3) per CLAUDE.md hard format constraint
- [x] 3.9 Verify all requirements use SHALL/MUST language (avoid should/may)
- [x] 3.10 Verify every requirement has at least 2 scenarios

## 4. Tasks Authoring (this file)

- [x] 4.1 Write Phase 0 task groups 1-5 covering proposal, design, spec, this file, and validation
- [x] 4.2 Write narrative "Archive Procedure" section (non-checkbox) documenting commit/lefthook flow
- [x] 4.3 Write narrative "Post-Archive Follow-ups" section (non-checkbox) listing 7 deferred decisions
- [x] 4.4 Write Phase 1 entry points subsection clearly marked "NOT executed in Phase 0"
- [x] 4.5 Write Phase 2+ entry points subsection further deferred

## 5. Validation

- [x] 5.1 Run `npx openspec validate a11-phase0-plan-driven-exam-architecture --strict` and confirm zero errors
- [x] 5.2 Run `npx openspec status --change a11-phase0-plan-driven-exam-architecture` and confirm `Progress: 4/4 artifacts complete`
- [x] 5.3 Verify no other Phase 0 change has claimed the `exam-planning` capability name (search `openspec/changes/` and `openspec/specs/`)

---

## Archive Procedure (non-task documentation)

> The actions below are NOT change-internal tasks. They describe the meta-process for landing this Phase 0 change into git history. They are recorded here for traceability of how this change was archived.

- Stage Phase 0 directory: `git add` is gitignored by `.gitignore:186` (`openspec/changes/*/`). The standard convention is `npx openspec archive a11-phase0-plan-driven-exam-architecture -y`, which moves the dir into `openspec/changes/archive/<date>-<name>/` (whitelisted) and merges the `specs/exam-planning/` delta into `openspec/specs/exam-planning/spec.md`.
- Commit message format: `docs(openspec): archive a11-phase0-plan-driven-exam-architecture` (matching the `8328264 docs(openspec): archive a6-phase0-fsrs-card-state-bucket-preservation` precedent). Include `@spec: exam-planning-001` reference and `Co-Authored-By: Claude Opus 4.6 (1M context)`.
- Lefthook chain expected: pre-commit (spec-sync skip / ghost-files / python-lint skip / python-typecheck skip) → commit-msg (commitlint + spec-reference) → post-commit (backup-push + origin-push) → pre-push (frontend-test skip / backend-smoke A11 regression 30 passed).
- Three-way hash match verification: `git rev-parse HEAD == git ls-remote origin <branch> == git ls-remote backup <branch>`.

## Post-Archive Follow-ups (non-task documentation)

> The 7 decisions below are deferred to follow-up sessions. They are recorded here for traceability and are also enumerated in `design.md` Open Questions §1 and §2. They are NOT change-internal tasks.

UX decisions (trigger via AskUserQuestion in next session):

- `[DECISION-UX:a11-phase0/plan-file-format]` — Plan 文件格式选择：Markdown / YAML / JSON tree / Mermaid?
- `[DECISION-UX:a11-phase0/plan-visibility]` — 用户能不能看到 plan 文件：始终展示 / 默认隐藏可展开 / 完全隐藏?
- `[DECISION-UX:a11-phase0/plan-editability]` — 用户能不能编辑 plan：只读 / 内联编辑 / 重新生成?
- `[DECISION-UX:a11-phase0/plan-regeneration-trigger]` — 何时触发 plan 重新生成：每次 exam / 仅 canvas 改动后 / 仅用户明确请求?

TECH decisions (trigger via ChatGPT Deep Research in next session):

- `[DECISION-TECH:a11-phase0/plan-generation-approach]` — Plan 生成方式：纯 LLM / 纯算法 / Hybrid?
- `[DECISION-TECH:a11-phase0/plan-storage]` — Plan 存储位置：文件系统 / Neo4j episode / SQLite / In-memory?
- `[DECISION-TECH:a11-phase0/plan-execution-statefulness]` — Plan 执行模型：服务端状态机 / 客户端 replay / Hybrid?

All 7 decisions must be documented back into design.md as updates BEFORE Phase 1 starts. They are Phase 1 prerequisites.

---

## Phase 1 Entry Points (NOT executed in Phase 0)

> The following tasks are listed for traceability only. They are deferred until Phase 0 is approved by the user AND follow-up UX/TECH decisions in §7 are resolved. **Do NOT touch any backend or frontend code as part of this Phase 0 change.**

- **Phase 1.1**: Implement plan file schema (JSON Schema or Pydantic model based on `[DECISION-UX:a11-phase0/plan-file-format]`)
- **Phase 1.2**: Implement plan generator (LLM call + algorithmic fallback per `[DECISION-TECH:a11-phase0/plan-generation-approach]`)
- **Phase 1.3**: Implement plan executor (replace `select_target_node()` consumers per `[DECISION-TECH:a11-phase0/plan-execution-statefulness]`)
- **Phase 1.4**: Add feature flag to `select_target_node()` (default off, allow opt-in to plan-driven)
- **Phase 1.5**: Write unit tests for plan generation (round-trip schema, sparse canvas, central node detection)
- **Phase 1.6**: Write e2e tests for plan-driven exam flow
- **Phase 1.7**: Update `algo-question` spec.md with reference to `exam-planning` capability (add `## MODIFIED Requirements` if any contract changes)
- **Phase 1.8**: Document plan file schema in user-facing docs (`docs/architecture.md` and `docs/known-gotchas.md` if applicable)

## Phase 2+ Entry Points (further deferred)

- **Phase 2.1**: Implement deep research D2 (canvas 0.7 / semantic 0.3 explicit fusion in `_get_kg_relevance`) — write `algo-rag` spec delta
- **Phase 2.2**: Implement deep research D3 mastery-based strategy as ONE plan generator option (alongside topological / LLM / random / user-curated strategies)
- **Phase 2.3**: Demote 3-factor formula to fallback-only invocation (strict path enforcement)
- **Phase 2.4**: Add WARN log + regression test for unexpected legacy formula invocation (per Requirement 5 Scenario 2)
