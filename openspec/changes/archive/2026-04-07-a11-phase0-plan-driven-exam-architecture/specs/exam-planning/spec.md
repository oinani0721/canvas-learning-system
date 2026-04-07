# exam-planning Specification

## Purpose

Defines the exam planning pipeline that addresses A11.md user vision: Claude (or an algorithm) deep-explores the canvas understanding to produce a structured exam plan file BEFORE the exam starts, then conducts the exam by following that plan with logical progressive difficulty (L1 single-node → L2 dual-node → L3 multi-node synthesis). The capability sits ABOVE `algo-question` (which provides low-level kg/mastery scoring) and orchestrates plan generation, plan execution, and progressive difficulty management. Plan-driven mode is the primary path; the legacy 3-factor formula is retained as a last-resort fallback only.

## ADDED Requirements

### Requirement: Plan File Generation

The exam-planning service SHALL generate a structured plan file before each exam session starts. The plan file MUST be human-readable and contain canvas metadata, node sequence, per-node question type (L1/L2/L3), and progression conditions.

#### Scenario: User starts an exam on a canvas with multiple nodes

- **WHEN** a user clicks "Start Exam" on a canvas containing N user-created nodes (where N >= 3)
- **THEN** the exam-planning service generates a plan file containing metadata fields (`canvas_id`, `generated_at`, `generator_version`)
- **AND** the plan file contains a non-empty node sequence with at least 1 entry
- **AND** every node entry has a question_type field set to one of `L1`, `L2`, or `L3`
- **AND** every transition between consecutive node entries has a progression_condition field

#### Scenario: Plan generation fails for empty canvas

- **WHEN** a user attempts to start an exam on a canvas with 0 user-created nodes
- **THEN** the exam-planning service returns a structured error response (not raising an unhandled exception)
- **AND** the error response includes a human-readable message suggesting the user add nodes first
- **AND** no exam session is created in the backend

#### Scenario: Plan generation is reproducible given same canvas state

- **WHEN** plan generation is invoked twice on the same canvas (with no edits between the two invocations) using the same `generator_version`
- **THEN** the two resulting plans contain identical node sequences modulo timestamp metadata fields
- **AND** the two plans contain identical question_type assignments per node

---

### Requirement: Plan File Schema Stability

The plan file SHALL have a stable, versioned schema. Any breaking change to the schema MUST bump the `generator_version` field, and old plan files MUST remain replayable by the version they were generated with.

#### Scenario: Plan file declares its generator version

- **WHEN** any plan file is read by the exam-planning service
- **THEN** the plan file contains a top-level `generator_version` field with a non-empty value

#### Scenario: Old plan files are not auto-upgraded silently

- **WHEN** a plan file with `generator_version=1` is loaded into a service running `generator_version=2`
- **THEN** the service either replays the plan under v1 semantics OR returns a structured error indicating the version mismatch
- **AND** the service MUST NOT silently coerce the v1 plan into v2 schema

---

### Requirement: Plan-Driven Question Selection

During an exam session, the question selection MUST consult the active plan file as the primary source of truth. The legacy 3-factor formula `select_target_node()` SHALL only be invoked as a last-resort fallback when the plan file is absent, exhausted, or marked as invalid.

#### Scenario: Next-question call follows the active plan

- **WHEN** an exam session has an active plan file AND the user submits an answer to the current question
- **THEN** the next question is selected by reading the next entry in the plan file
- **AND** the next-question call does NOT recompute `select_target_node()` from scratch

#### Scenario: Legacy 3-factor formula is the last-resort fallback

- **WHEN** plan generation has failed AND the exam still proceeds in fallback mode
- **THEN** the service falls back to the legacy `select_target_node()` formula
- **AND** the response payload includes a `degraded_reason` field with value `"plan_generation_failed"`
- **AND** the service emits a structured log entry recording the fallback invocation

---

### Requirement: Progressive Difficulty Within Plan

The plan file SHALL express progressive difficulty as a sequence of L1 (single-node) → L2 (dual-node relationship) → L3 (multi-node synthesis) question types. The plan generator MUST decide the L1→L2 and L2→L3 transition points based on canvas connectivity (KG relevance signals).

#### Scenario: Plan starts with L1 questions on the central node

- **WHEN** the plan generator runs on a canvas with a clear central node (highest kg_relevance) AND multiple peripheral nodes
- **THEN** the plan starts with at least one L1 question targeting the central node
- **AND** the central node's L1 questions appear before any L2 or L3 question in the plan sequence

#### Scenario: Plan introduces L2 questions only after both involved nodes have L1 questions

- **WHEN** the plan generator emits an L2 question for a node pair `(X, Y)`
- **THEN** the plan contains at least one L1 question targeting `X` BEFORE the L2 question
- **AND** the plan contains at least one L1 question targeting `Y` BEFORE the L2 question

#### Scenario: Sparse canvas plan stops at L1

- **WHEN** the canvas has fewer than 3 nodes OR has zero CANVAS_EDGE relationships between nodes
- **THEN** the plan contains only L1 question entries
- **AND** the plan metadata field `progression_max_level` is set to the literal string `"L1"`

---

### Requirement: 3-Factor Formula Deprecation Path

The legacy 3-factor formula in `select_target_node()` MUST remain available as a fallback path but MUST be marked as deprecated in code comments. The formula SHALL emit a structured WARN-level log entry every time it is invoked outside the legitimate fallback context, and a regression test MUST exist to catch unexpected invocations.

#### Scenario: Legacy formula invoked as legitimate fallback emits info-level log

- **WHEN** plan-driven mode falls back to the legacy formula because plan generation failed OR the plan was exhausted
- **THEN** the response payload includes the field `legacy_formula_invoked=True`
- **AND** the service emits a structured log entry with `severity=INFO` AND `reason="plan_unavailable"` OR `reason="plan_exhausted"`

#### Scenario: Legacy formula invoked while plan is still active emits warn-level log

- **WHEN** the legacy 3-factor formula is invoked WHILE plan-driven mode is enabled AND the plan file is valid AND the plan has not been exhausted
- **THEN** the service emits a structured log entry with `severity=WARN` AND `reason="legacy_formula_unexpected_invocation"`
- **AND** a regression test exists that asserts this WARN-level log path is exercised by an intentional regression scenario
