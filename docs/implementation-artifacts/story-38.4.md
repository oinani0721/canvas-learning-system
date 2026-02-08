# Story 38.4: Dual-Write Default Configuration Safety

Status: ready-for-dev

## Story

As an operator deploying the system,
I want dual-write to JSON fallback to be enabled by default,
so that a fresh installation has Neo4j offline resilience out of the box.

## Acceptance Criteria

### AC-1: Safe Default (D4: Configuration)
**Given** a fresh installation with no `.env` file customization
**When** the application starts
**Then** `ENABLE_GRAPHITI_JSON_DUAL_WRITE` defaults to `true`
**And** the startup log shows: `"Dual-write: enabled (default)"`

### AC-2: Explicit Disable (D4: Configuration)
**Given** an operator sets `ENABLE_GRAPHITI_JSON_DUAL_WRITE=false` in `.env`
**When** the application starts
**Then** dual-write is disabled as configured
**And** the startup log shows: `"Dual-write: disabled (explicit configuration)"`
**And** a WARNING log is emitted: `"JSON fallback is disabled. Neo4j outage will cause data loss."`

### AC-3: Missing Env Var (D4: Configuration)
**Given** the `ENABLE_GRAPHITI_JSON_DUAL_WRITE` environment variable is not set
**When** the Settings class initializes
**Then** the default value is `True` (safe default)
**And** behavior is identical to AC-1

## Tasks / Subtasks

- [ ] Task 1: Change default value in config.py (AC: #1, #3)
  - [ ] 1.1 Change `default=False` → `default=True` at `backend/app/config.py:L410`
  - [ ] 1.2 Update Field description to reflect new default
- [ ] Task 2: Add startup log announcement (AC: #1, #2)
  - [ ] 2.1 In `backend/app/main.py` lifespan(), after MemoryService pre-warm (~L114), add dual-write status log
  - [ ] 2.2 If disabled explicitly, emit WARNING about data loss risk
- [ ] Task 3: Update .env.example (AC: #1)
  - [ ] 3.1 Change `ENABLE_GRAPHITI_JSON_DUAL_WRITE=false` → `ENABLE_GRAPHITI_JSON_DUAL_WRITE=true` at `backend/.env.example:L184`
  - [ ] 3.2 Update comment to reflect new default: "default: true"
- [ ] Task 4: Verify existing tests still pass (AC: #1, #2, #3)
  - [ ] 4.1 Run existing dual-write tests: `pytest backend/tests/unit/test_graphiti_json_dual_write.py`
  - [ ] 4.2 Run integration tests: `pytest backend/tests/integration/test_dual_write_consistency.py`
  - [ ] 4.3 Fix any tests that hardcode `default=False` assumption

## Dev Notes

### Scope: XS (Extra Small)
Core change is a single line in `config.py`. Supporting changes are log messages and .env.example update.

### Files to Modify

| # | File | Line(s) | Change |
|---|------|---------|--------|
| 1 | `backend/app/config.py` | L409-412 | `default=False` → `default=True` |
| 2 | `backend/app/config.py` | L584-586 | Property alias — no change needed (reads from same field) |
| 3 | `backend/app/main.py` | ~L114 (after MemoryService pre-warm) | Add dual-write status log |
| 4 | `backend/.env.example` | L182-184 | Update default comment and value |

### Files NOT to Modify (Read-Only Context)

| File | Reason |
|------|--------|
| `backend/app/services/memory_service.py:L376` | `record_learning_event()` — reads flag via `getattr(settings, ...)`, no change needed |
| `backend/app/services/memory_service.py:L990` | `record_temporal_event()` — same pattern, no change needed |

### Existing Test Files (May Need Updates)

| File | Tests | Concern |
|------|-------|---------|
| `backend/tests/unit/test_graphiti_json_dual_write.py` | 7+ tests | All mock `ENABLE_GRAPHITI_JSON_DUAL_WRITE = True` explicitly — should still pass |
| `backend/tests/integration/test_dual_write_consistency.py` | 1+ test | Same mock pattern — should still pass |
| `backend/tests/integration/test_memory_graphiti_integration.py` | 8+ tests | Same mock pattern — should still pass |

### Infrastructure AC Checklist (D4) Verification

- [x] **Default state defined:** ON by default (AC-1)
- [x] **Fresh install behavior:** Dual-write enabled without manual setup (AC-1)
- [x] **Env var missing behavior:** Falls back to `True` (AC-3)
- [x] **Config change impact:** Takes effect on restart (standard Pydantic Settings behavior)

### Project Structure Notes

- Settings class: Pydantic `BaseSettings` with `SettingsConfigDict(env_file=".env")`
- Lowercase alias `enable_graphiti_json_dual_write` property exists at L584-586
- All consumers use `getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", False)` — the `False` fallback in getattr is defense-in-depth, not the primary default

### References

- [Source: docs/stories/EPIC-38-infrastructure-reliability-fixes.md#Story-38.4]
- [Source: _bmad/bmm/checklists/infrastructure-ac-checklist.md#D4]
- [Source: backend/app/config.py:L409-412 — current default=False]
- [Source: backend/app/main.py:L62-134 — lifespan startup sequence]
- [Source: backend/.env.example:L182-184 — current documentation]

## Dev Agent Record

### Agent Model Used

(to be filled by Dev Agent)

### Debug Log References

### Completion Notes List

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-06 | Story created from EPIC-38 audit | PM (bmad-help) |
