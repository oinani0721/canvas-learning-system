# Story 38.4: Dual-Write Default Configuration Safety

Status: done

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

- [x] Task 1: Change default value in config.py (AC: #1, #3)
  - [x] 1.1 Change `default=False` → `default=True` at `backend/app/config.py:L409`
  - [x] 1.2 Update Field description to reflect new default
- [x] Task 2: Add startup log announcement (AC: #1, #2)
  - [x] 2.1 In `backend/app/main.py` lifespan(), after MemoryService pre-warm (L119), add dual-write status log
  - [x] 2.2 If disabled explicitly, emit WARNING about data loss risk
- [x] Task 3: Update .env.example (AC: #1)
  - [x] 3.1 Change `ENABLE_GRAPHITI_JSON_DUAL_WRITE=false` → `ENABLE_GRAPHITI_JSON_DUAL_WRITE=true` at `backend/.env.example:L185`
  - [x] 3.2 Update comment to reflect new default: "default: true"
- [x] Task 4: Verify existing tests still pass (AC: #1, #2, #3)
  - [x] 4.1 Run existing dual-write tests: 11/11 passed
  - [x] 4.2 Run Story 38.4 specific tests: 7/7 passed
  - [x] 4.3 No tests hardcoded `default=False` assumption (all use explicit mock)

### Review Follow-ups (AI) — Fixed

- [x] [AI-Review][HIGH] getattr fallback False→True in 6 locations (memory_service.py, canvas_service.py)
- [x] [AI-Review][HIGH] Startup log now distinguishes default vs explicit enable via os.environ check
- [x] [AI-Review][MEDIUM] test_lowercase_alias_returns_true_by_default now tests actual property
- [x] [AI-Review][MEDIUM] Lifespan tests now properly patch os.environ for AC-1/AC-2 scenarios

## Dev Notes

### Scope: XS (Extra Small)
Core change is a single line in `config.py`. Supporting changes are log messages and .env.example update.

### Files to Modify

| # | File | Line(s) | Change |
|---|------|---------|--------|
| 1 | `backend/app/config.py` | L409-412 | `default=False` → `default=True`, updated description |
| 2 | `backend/app/config.py` | L602-605 | Property alias — no change needed (reads from same field) |
| 3 | `backend/app/main.py` | L119-128 | Add dual-write status log with default/explicit distinction |
| 4 | `backend/.env.example` | L182-185 | Update default comment and value |

### Files NOT to Modify (Read-Only Context)

| File | Reason |
|------|--------|
| `backend/app/services/memory_service.py:L454` | `record_learning_event()` — getattr fallback updated False→True |
| `backend/app/services/memory_service.py:L1085` | `record_temporal_event()` — getattr fallback updated False→True |
| `backend/app/services/canvas_service.py:L242,329,388,402` | 4x getattr fallback updated False→True |

### Existing Test Files (Verified)

| File | Tests | Result |
|------|-------|--------|
| `backend/tests/unit/test_story_38_4_dual_write_default.py` | 7 tests | 7/7 PASSED |
| `backend/tests/unit/test_graphiti_json_dual_write.py` | 11 tests | 11/11 PASSED |

### Infrastructure AC Checklist (D4) Verification

- [x] **Default state defined:** ON by default (AC-1)
- [x] **Fresh install behavior:** Dual-write enabled without manual setup (AC-1)
- [x] **Env var missing behavior:** Falls back to `True` (AC-3)
- [x] **Config change impact:** Takes effect on restart (standard Pydantic Settings behavior)
- [x] **getattr defense-in-depth:** All 6 getattr fallbacks aligned to True (safe default)

### Project Structure Notes

- Settings class: Pydantic `BaseSettings` with `SettingsConfigDict(env_file=".env")`
- Lowercase alias `enable_graphiti_json_dual_write` property exists at L602-605
- All consumers use `getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True)` — fallback aligned with safe default

### References

- [Source: docs/stories/EPIC-38-infrastructure-reliability-fixes.md#Story-38.4]
- [Source: _bmad/bmm/checklists/infrastructure-ac-checklist.md#D4]
- [Source: backend/app/config.py:L409-412 — default=True]
- [Source: backend/app/main.py:L119-128 — lifespan dual-write log]
- [Source: backend/.env.example:L182-185 — documentation]

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (Code Review + Auto-fix)

### Debug Log References

- Test run: `pytest tests/unit/test_story_38_4_dual_write_default.py` → 7/7 PASSED
- Regression: `pytest tests/unit/test_graphiti_json_dual_write.py` → 11/11 PASSED

### Completion Notes List

1. Implementation done in commits `a29148c` (config.py, main.py) and `14f0412` (.env.example, tests)
2. Code review found 3 HIGH + 3 MEDIUM issues, all fixed automatically
3. Key fix: 6x `getattr` fallback changed from `False` to `True` for safe-default consistency
4. Key fix: Startup log now distinguishes "enabled (default)" vs "enabled (explicit configuration)"
5. Key fix: Test for lowercase property alias now actually tests the property

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-06 | Story created from EPIC-38 audit | PM (bmad-help) |
| 2026-02-07 | Implementation in commits a29148c, 14f0412 | Dev Agent |
| 2026-02-08 | Code review: 3H+3M issues found and auto-fixed | Reviewer (claude-opus-4-6) |
