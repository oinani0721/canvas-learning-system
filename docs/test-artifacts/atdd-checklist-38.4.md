# ATDD Checklist - EPIC-38, Story 38.4: Dual-Write Default Configuration Safety

**Date:** 2026-02-06
**Author:** ROG
**Primary Test Level:** Unit

---

## Story Summary

Configuration safety change to make dual-write JSON fallback enabled by default, so fresh installations have Neo4j offline resilience out of the box.

**As an** operator deploying the system
**I want** dual-write to JSON fallback to be enabled by default
**So that** a fresh installation has Neo4j offline resilience out of the box

---

## Acceptance Criteria

1. **AC-1 (Safe Default):** Fresh installation defaults `ENABLE_GRAPHITI_JSON_DUAL_WRITE` to `true`; startup log shows "Dual-write: enabled (default)"
2. **AC-2 (Explicit Disable):** Operator can set to `false`; startup log shows "disabled (explicit configuration)"; WARNING about data loss risk
3. **AC-3 (Missing Env Var):** Absence of env var defaults to `True` (identical to AC-1)

---

## Failing Tests Created (RED Phase)

### Unit Tests (7 tests)

**File:** `backend/tests/unit/test_story_38_4_dual_write_default.py` (195 lines)

#### AC-1: Safe Default

- **Test:** `TestAC1SafeDefault::test_settings_field_default_is_true`
  - **Status:** RED (XFAIL) — config.py has `default=False`, need `default=True`
  - **Priority:** P0
  - **Verifies:** Settings field default value is True

- **Test:** `TestAC1SafeDefault::test_lowercase_alias_returns_true_by_default`
  - **Status:** RED (XFAIL) — lowercase alias reflects False default
  - **Priority:** P0
  - **Verifies:** Property alias at L584-586 also returns True

- **Test:** `TestAC1SafeDefault::test_startup_log_dual_write_enabled_default`
  - **Status:** RED (XFAIL) — no dual-write log in lifespan()
  - **Priority:** P1
  - **Verifies:** Startup log message "Dual-write: enabled (default)"

#### AC-2: Explicit Disable

- **Test:** `TestAC2ExplicitDisable::test_explicit_env_false_disables_dual_write`
  - **Status:** GREEN (PASSED) — env var override already works
  - **Priority:** P0
  - **Verifies:** Setting ENABLE_GRAPHITI_JSON_DUAL_WRITE=false disables it

- **Test:** `TestAC2ExplicitDisable::test_startup_log_dual_write_disabled_explicit`
  - **Status:** RED (XFAIL) — no dual-write disabled log in lifespan()
  - **Priority:** P1
  - **Verifies:** Startup log "Dual-write: disabled (explicit configuration)"

- **Test:** `TestAC2ExplicitDisable::test_warning_log_data_loss_risk_when_disabled`
  - **Status:** RED (XFAIL) — no WARNING log in lifespan()
  - **Priority:** P1
  - **Verifies:** WARNING "JSON fallback is disabled. Neo4j outage will cause data loss."

#### AC-3: Missing Env Var

- **Test:** `TestAC3MissingEnvVar::test_missing_env_var_defaults_to_true`
  - **Status:** RED (XFAIL) — config.py has `default=False`
  - **Priority:** P0
  - **Verifies:** Missing env var defaults to True via Settings instantiation

---

## Data Factories Created

None required — Story 38.4 tests only Settings class and log output.

---

## Fixtures Created

None required — Tests use `unittest.mock.patch` and pytest `caplog` fixture.

---

## Mock Requirements

### Lifespan Dependencies Mock

Tests for startup log behavior mock the following lifespan() dependencies:

| Dependency | Mock Type | Purpose |
|-----------|-----------|---------|
| `app.main.get_default_monitor` | `patch` → `AsyncMock` | Skip resource monitoring |
| `app.main.load_alert_rules_from_yaml` | `patch` → `[]` | Skip alert rule loading |
| `app.main.create_default_dispatcher` | `patch` | Skip notification setup |
| `app.main.AlertManager` | `patch` → `AsyncMock` | Skip alert manager |
| `app.main.get_memory_service` | `AsyncMock` | Skip MemoryService pre-warm |
| `app.main.cleanup_memory_service` | `AsyncMock` | Skip cleanup |
| `app.main.set_alert_manager` | `patch` | Skip alert injection |
| `app.main.set_session_validator` | `patch` | Skip session validation |
| `app.main.settings` | `patch` | Control config values |

---

## Required data-testid Attributes

None — Story 38.4 has no UI components.

---

## Implementation Checklist

### Test: test_settings_field_default_is_true / test_lowercase_alias_returns_true_by_default / test_missing_env_var_defaults_to_true

**File:** `backend/tests/unit/test_story_38_4_dual_write_default.py`

**Tasks to make these tests pass:**

- [ ] Change `default=False` → `default=True` in `backend/app/config.py:L410`
- [ ] Update Field description to reflect new default
- [ ] Run test: `pytest backend/tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault -v`
- [ ] Run test: `pytest backend/tests/unit/test_story_38_4_dual_write_default.py::TestAC3MissingEnvVar -v`
- [ ] All 3 tests pass (green phase)

**Estimated Effort:** 0.1 hours

---

### Test: test_startup_log_dual_write_enabled_default

**File:** `backend/tests/unit/test_story_38_4_dual_write_default.py`

**Tasks to make this test pass:**

- [ ] Add dual-write status log in `backend/app/main.py` lifespan(), after MemoryService pre-warm (~L114)
- [ ] Log format: `logger.info("Dual-write: enabled (default)")` when ENABLE_GRAPHITI_JSON_DUAL_WRITE is True
- [ ] Run test: `pytest backend/tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault::test_startup_log_dual_write_enabled_default -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.1 hours

---

### Test: test_startup_log_dual_write_disabled_explicit / test_warning_log_data_loss_risk_when_disabled

**File:** `backend/tests/unit/test_story_38_4_dual_write_default.py`

**Tasks to make these tests pass:**

- [ ] Add disabled log in `backend/app/main.py` lifespan(): `logger.info("Dual-write: disabled (explicit configuration)")`
- [ ] Add WARNING log: `logger.warning("JSON fallback is disabled. Neo4j outage will cause data loss.")`
- [ ] Run test: `pytest backend/tests/unit/test_story_38_4_dual_write_default.py::TestAC2ExplicitDisable -v`
- [ ] Both tests pass (green phase)

**Estimated Effort:** 0.1 hours

---

## Running Tests

```bash
# Run all ATDD tests for Story 38.4
pytest backend/tests/unit/test_story_38_4_dual_write_default.py -v

# Run specific AC tests
pytest backend/tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault -v
pytest backend/tests/unit/test_story_38_4_dual_write_default.py::TestAC2ExplicitDisable -v
pytest backend/tests/unit/test_story_38_4_dual_write_default.py::TestAC3MissingEnvVar -v

# Run with detailed output
pytest backend/tests/unit/test_story_38_4_dual_write_default.py -v --tb=long

# Run existing dual-write tests (regression check)
pytest backend/tests/unit/test_graphiti_json_dual_write.py -v
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

- [x] All 7 tests written (6 failing + 1 passing)
- [x] Tests assert EXPECTED behavior from Story 38.4 AC
- [x] Mock requirements documented
- [x] Implementation checklist created
- [x] Test execution verified: `1 passed, 6 xfailed in 10.22s`

**Verification:**

- All xfailed tests fail due to missing implementation (not test bugs)
- Failure reasons are clear: `default=False` (should be True) and missing log messages
- One test passes: env var override mechanism already works

---

### GREEN Phase (DEV Agent - Next Steps)

**DEV Agent Responsibilities:**

1. **Task 1 (P0):** Change `default=False` → `default=True` in `config.py:L410`
   → Makes 3 tests pass (AC-1 field default + AC-1 alias + AC-3 missing env)
2. **Task 2 (P1):** Add dual-write status log in `main.py` lifespan()
   → Makes 3 tests pass (AC-1 startup log + AC-2 disabled log + AC-2 warning)
3. **Task 3:** Update `.env.example` (no test, manual verification)
4. **Task 4:** Run all existing dual-write tests for regression

**Key Principles:**
- Implement Task 1 first (3 xfail → 3 pass)
- Then Task 2 (3 more xfail → 3 pass)
- Total: 7/7 pass = GREEN phase complete

---

### REFACTOR Phase

- Remove `@pytest.mark.xfail` decorators from all 6 tests
- Verify all 7 tests pass without xfail
- Run regression: `pytest backend/tests/unit/test_graphiti_json_dual_write.py -v`

---

## Knowledge Base References Applied

- **test-quality.md** — Deterministic, isolated tests with explicit assertions
- **fixture-architecture.md** — pytest `caplog` fixture for log capture (adapted from Playwright)
- **data-factories.md** — Not needed (no data generation required)
- **component-tdd.md** — Not applicable (backend-only story)

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `pytest backend/tests/unit/test_story_38_4_dual_write_default.py -v`

**Results:**

```
tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault::test_settings_field_default_is_true XFAIL
tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault::test_lowercase_alias_returns_true_by_default XFAIL
tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault::test_startup_log_dual_write_enabled_default XFAIL
tests/unit/test_story_38_4_dual_write_default.py::TestAC2ExplicitDisable::test_explicit_env_false_disables_dual_write PASSED
tests/unit/test_story_38_4_dual_write_default.py::TestAC2ExplicitDisable::test_startup_log_dual_write_disabled_explicit XFAIL
tests/unit/test_story_38_4_dual_write_default.py::TestAC2ExplicitDisable::test_warning_log_data_loss_risk_when_disabled XFAIL
tests/unit/test_story_38_4_dual_write_default.py::TestAC3MissingEnvVar::test_missing_env_var_defaults_to_true XFAIL
================== 1 passed, 6 xfailed in 10.22s ==================
```

**Summary:**

- Total tests: 7
- Passing: 1 (existing env override behavior)
- Failing (XFAIL): 6 (expected — feature not implemented)
- Status: RED phase verified

---

## Notes

- Story 38.4 is XS scope — only 3 files to modify (config.py, main.py, .env.example)
- All existing dual-write tests in `test_graphiti_json_dual_write.py` explicitly mock the flag as `True`, so they should be unaffected by the default change
- The `getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", False)` pattern in memory_service.py uses `False` as defense-in-depth fallback, not primary default — no change needed
- Coverage failure (25% < 85%) is a global threshold issue, unrelated to this test file

---

**Generated by BMad TEA Agent (Murat)** - 2026-02-06
