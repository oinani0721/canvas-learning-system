# Test Quality Review: Story 32.10 — Tests Reliability & Isolation Fixes

**Quality Score**: 73/100 (C - Needs Improvement)
**Review Date**: 2026-02-10
**Review Scope**: Story 32.10 related test files (3 files)
**Reviewer**: TEA Agent (Test Architect)

---

Note: This review audits existing tests; it does not generate tests.

## Executive Summary

**Overall Assessment**: Needs Improvement

**Recommendation**: Request Changes

### Key Strengths

- Performance excellent — all tests are lightweight unit/API tests with no I/O bottlenecks (98/100)
- Good class-based organization with descriptive docstrings and AC references
- Effective use of pytest fixtures and parameterized tests
- Mock usage is appropriate — no real external calls in tests

### Key Weaknesses

- 2 HIGH determinism violations: `datetime.now(timezone.utc)` without mocking creates midnight-boundary flakiness
- 2 HIGH isolation violations: yield fixture without `try/finally` + `clear()` instead of `pop()` causes DI override leakage
- Story 32.10 coverage gap: `test_fsrs_state_query.py` has identical yield vulnerability not addressed by the story
- `test_fsrs_manager.py` at 524 lines exceeds the 300-line guideline

### Summary

Story 32.10 correctly identifies 3 real P1 test reliability issues from the EPIC-32 adversarial audit, but the test files have additional quality issues beyond the story scope. The most critical are datetime.now() flakiness (which can cause CI failures at midnight boundaries) and DI override leakage (which can cause cascading test failures when a test raises an exception). The story's coverage is slightly incomplete — it misses the identical yield/cleanup vulnerability in `test_fsrs_state_query.py`. Performance is excellent as all tests are lightweight.

---

## Quality Criteria Assessment

| Criterion | Status | Violations | Notes |
|-----------|--------|-----------|-------|
| Determinism (datetime/random) | :x: FAIL | 4 | 2 HIGH: datetime.now() in assertions, 2 MEDIUM: datetime.now() in test data |
| Isolation (cleanup/shared state) | :x: FAIL | 6 | 2 HIGH: missing try/finally + clear() nukes, 3 MEDIUM, 1 LOW |
| Maintainability (structure/DRY) | :warning: WARN | 12 | 2 HIGH: file size + duplication, 5 MEDIUM, 5 LOW |
| Coverage (AC completeness) | :x: FAIL | 5 | 5 HIGH: all Story 32.10 issues confirmed + 1 missed gap |
| Performance (speed/efficiency) | :white_check_mark: PASS | 1 | 1 LOW: minor fixture scope optimization |
| Test Length (<=300 lines) | :warning: WARN | 2 | 524 lines and 365 lines exceed guideline |
| BDD Format (Given-When-Then) | :warning: WARN | 2 | Complex tests lack BDD comments |
| Fixture Patterns | :x: FAIL | 3 | Missing try/finally on yield fixtures |
| Explicit Assertions | :white_check_mark: PASS | 0 | All tests have clear assertions |

**Total Violations**: 11 Critical (HIGH), 10 High (MEDIUM), 7 Low (LOW)

---

## Quality Score Breakdown

```
Starting Score:          100

Dimension Scores (weighted):
  Determinism (25%):     65 × 0.25 = 16.25
  Isolation (25%):       74 × 0.25 = 18.50
  Maintainability (20%): 72 × 0.20 = 14.40
  Coverage (15%):        58 × 0.15 =  8.70
  Performance (15%):     98 × 0.15 = 14.70
                         --------
Final Score:             72.55 → 73/100
Grade:                   C (Needs Improvement)
```

---

## Critical Issues (Must Fix)

### 1. datetime.now() Flaky Assertion — Midnight Boundary Risk

**Severity**: P0 (Critical)
**Location**: `backend/tests/unit/test_fsrs_manager.py:124`
**Criterion**: Determinism
**Dimension**: determinism

**Issue Description**:
`datetime.now(timezone.utc)` is captured at test execution time and compared against `due` with a 5-second tolerance. If the test runs at 23:59:58 and the card's `due` calculation happens at 00:00:01, the delta crosses a date boundary, potentially causing the `assert delta < 5` to fail due to the 1-day offset.

**Current Code**:

```python
# backend/tests/unit/test_fsrs_manager.py:116-127
def test_create_card_is_due_immediately(self, fsrs_manager):
    card = fsrs_manager.create_card()
    due = fsrs_manager.get_due_date(card)
    now = datetime.now(timezone.utc)  # Line 124: NON-DETERMINISTIC
    delta = abs((due - now).total_seconds())
    assert delta < 5, f"Card should be due immediately, delta={delta}s"
```

**Recommended Fix**:

```python
# Option A (Recommended): freezegun
from freezegun import freeze_time

@freeze_time("2026-06-15T12:00:00Z")
def test_create_card_is_due_immediately(self, fsrs_manager):
    card = fsrs_manager.create_card()
    due = fsrs_manager.get_due_date(card)
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    delta = abs((due - now).total_seconds())
    assert delta < 5

# Option B: Widen tolerance
def test_create_card_is_due_immediately(self, fsrs_manager):
    card = fsrs_manager.create_card()
    due = fsrs_manager.get_due_date(card)
    now = datetime.now(timezone.utc)
    delta = abs((due - now).total_seconds())
    assert delta < 10, f"Card should be due immediately, delta={delta}s"
```

**Why This Matters**:
CI tests running near midnight will fail intermittently. This is a known class of flaky test that is difficult to reproduce locally but causes CI failures.

---

### 2. datetime.now() Flaky Assertion — Future Date Comparison

**Severity**: P0 (Critical)
**Location**: `backend/tests/unit/test_fsrs_manager.py:234`
**Criterion**: Determinism
**Dimension**: determinism

**Issue Description**:
`now = datetime.now(timezone.utc)` is captured before `review_card()`. If review_card() takes non-trivial time, the `due_date` could be calculated relative to a slightly different clock instant, making `due_date > now` borderline.

**Current Code**:

```python
# backend/tests/unit/test_fsrs_manager.py:231-241
def test_get_due_date_is_in_future_after_review(self, fsrs_manager, new_card):
    now = datetime.now(timezone.utc)  # Line 234: captured BEFORE review
    updated_card, _ = fsrs_manager.review_card(new_card, Rating.Good)
    due_date = fsrs_manager.get_due_date(updated_card)
    assert due_date > now, "Due date should be in the future after review"
```

**Recommended Fix**:

```python
@freeze_time("2026-06-15T12:00:00Z")
def test_get_due_date_is_in_future_after_review(self, fsrs_manager, new_card):
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    updated_card, _ = fsrs_manager.review_card(new_card, Rating.Good)
    due_date = fsrs_manager.get_due_date(updated_card)
    assert due_date > now
```

---

### 3. Yield Fixture Without try/finally — DI Override Leakage

**Severity**: P0 (Critical)
**Location**: `backend/tests/api/v1/endpoints/test_fsrs_state_api.py:37-41`
**Criterion**: Isolation
**Dimension**: isolation

**Issue Description**:
The `override_settings` fixture yields without `try/finally`. If any test using this fixture raises an exception, the cleanup code (`app.dependency_overrides.clear()`) will never execute, causing the DI override to leak into subsequent tests.

**Current Code**:

```python
# backend/tests/api/v1/endpoints/test_fsrs_state_api.py:37-41
@pytest.fixture(autouse=True)
def override_settings():
    app.dependency_overrides[get_settings] = get_settings_override
    yield                                 # If test raises → cleanup skipped!
    app.dependency_overrides.clear()      # ALSO: clear() wipes ALL overrides
```

**Recommended Fix**:

```python
@pytest.fixture(autouse=True)
def override_settings():
    app.dependency_overrides[get_settings] = get_settings_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_settings, None)  # Targeted cleanup
```

**Why This Matters**:
DI override leakage causes cascading test failures. Test B fails because Test A's exception prevented cleanup, and Test B inherits a stale override. This is extremely difficult to debug because the failing test is not the one with the bug.

---

### 4. clear() Wipes ALL DI Overrides — Cross-Fixture Interference

**Severity**: P0 (Critical)
**Location**: `backend/tests/api/v1/endpoints/test_fsrs_state_api.py:41`
**Criterion**: Isolation
**Dimension**: isolation

**Issue Description**:
`app.dependency_overrides.clear()` removes ALL overrides, not just the one this fixture set. If conftest.py or other fixtures have set additional overrides (e.g., `get_canvas_service`, `get_memory_service`), they will be wiped.

**Current Code**:

```python
app.dependency_overrides.clear()  # NUCLEAR: removes EVERYTHING
```

**Recommended Fix**:

```python
app.dependency_overrides.pop(get_settings, None)  # SURGICAL: only our override
```

**Related**: `test_fsrs_state_query.py:43` already uses the correct `pop()` pattern.

---

### 5. Coverage Gap: test_fsrs_state_query.py Has Same Vulnerability

**Severity**: P1 (High)
**Location**: `backend/tests/unit/test_fsrs_state_query.py:39-43`
**Criterion**: Coverage
**Dimension**: coverage

**Issue Description**:
Story 32.10 identifies the yield/cleanup issues in `test_fsrs_state_api.py` (AC-32.10.2, AC-32.10.3) but does NOT identify the identical `yield` without `try/finally` vulnerability in `test_fsrs_state_query.py`. While this file correctly uses `pop()` (satisfying AC-32.10.3 pattern), it still lacks exception safety.

**Current Code**:

```python
# backend/tests/unit/test_fsrs_state_query.py:39-43
@pytest.fixture(autouse=True)
def override_settings():
    app.dependency_overrides[get_settings] = _test_settings_override
    yield                                           # No try/finally!
    app.dependency_overrides.pop(get_settings, None) # Correct pop(), but unreachable on exception
```

**Recommended Fix**:

```python
@pytest.fixture(autouse=True)
def override_settings():
    app.dependency_overrides[get_settings] = _test_settings_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_settings, None)
```

**Why This Matters**:
Story 32.10 should also include this file in its scope. Otherwise, the same class of bug persists after the story is "completed".

---

## Recommendations (Should Fix)

### 1. Conditional `if FSRS_AVAILABLE` Anti-Pattern

**Severity**: P2 (Medium)
**Location**: `backend/tests/unit/test_fsrs_manager.py:79,86,112,146,...`
**Criterion**: Maintainability
**Dimension**: maintainability

**Issue Description**:
Multiple tests wrap assertions in `if FSRS_AVAILABLE:` blocks. This means tests silently pass without asserting anything when FSRS is not available, hiding potential issues.

**Recommended Improvement**:

```python
# Instead of:
def test_something(self, fsrs_manager):
    if FSRS_AVAILABLE:
        assert something

# Use:
@pytest.mark.skipif(not FSRS_AVAILABLE, reason="FSRS library not installed")
def test_something(self, fsrs_manager):
    assert something
```

### 2. File Size: test_fsrs_manager.py Exceeds 300-Line Guideline

**Severity**: P2 (Medium)
**Location**: `backend/tests/unit/test_fsrs_manager.py`
**Criterion**: Maintainability

**Issue Description**:
524 lines with 10 test classes. While well-organized, the file would benefit from splitting.

**Recommended**: Split into `test_fsrs_manager_core.py` (init, creation, review) and `test_fsrs_manager_serialization.py` (serialization, state conversion, dataclass).

### 3. Duplicate Test Setup in Health Endpoint Tests

**Severity**: P2 (Medium)
**Location**: `backend/tests/api/v1/endpoints/test_fsrs_state_api.py:177-221`
**Criterion**: Maintainability

**Issue Description**:
3 consecutive health endpoint tests repeat identical setup pattern (import, monkeypatch, get, assert).

**Recommended**: Use `@pytest.mark.parametrize` to consolidate.

### 4. datetime.now() in Test Data Construction

**Severity**: P3 (Low)
**Location**: `backend/tests/unit/test_fsrs_state_query.py:329`
**Criterion**: Determinism

**Issue Description**:
`due=datetime.now(timezone.utc)` used in FSRSStateResponse construction. Lower risk since not in assertion comparison, but introduces non-determinism in test data.

**Recommended**: Replace with fixed timestamp constant.

---

## Best Practices Found

### 1. Parametrized Boundary Tests

**Location**: `backend/tests/unit/test_fsrs_manager.py:364-386`
**Pattern**: pytest.mark.parametrize

**Why This Is Good**:
Rating conversion uses 12 boundary test cases via `@pytest.mark.parametrize`, efficiently covering all score-to-rating mappings in a compact, readable format.

### 2. Correct DI Override Pattern (Reference)

**Location**: `backend/tests/unit/test_fsrs_state_query.py:43`
**Pattern**: Targeted pop() cleanup

**Why This Is Good**:
Uses `app.dependency_overrides.pop(get_settings, None)` instead of `clear()`, demonstrating the correct pattern for DI override cleanup. This should be the standard across all test files.

### 3. AsyncMock Service Injection

**Location**: `backend/tests/api/v1/endpoints/test_fsrs_state_api.py:51-64`
**Pattern**: Fixture-based mock injection

**Why This Is Good**:
`mock_review_singleton` fixture properly patches the singleton import path with `AsyncMock`, enabling controlled testing of async service behavior.

---

## Test File Analysis

### File Metadata

| File | Path | Lines | Tests | Framework |
|------|------|-------|-------|-----------|
| test_fsrs_manager.py | `backend/tests/unit/` | 524 | ~30 | pytest |
| test_fsrs_state_api.py | `backend/tests/api/v1/endpoints/` | 306 | ~15 | pytest + FastAPI TestClient |
| test_fsrs_state_query.py | `backend/tests/unit/` | 365 | ~12 | pytest + FastAPI TestClient |

### Test Structure

| File | Classes | Fixtures | Parametrized |
|------|---------|----------|-------------|
| test_fsrs_manager.py | 10 | 4 (fsrs_manager, fsrs_manager_custom, new_card, reviewed_card) | 1 (12 cases) |
| test_fsrs_state_api.py | 4 | 3 (override_settings, client, mock_review_singleton) | 0 |
| test_fsrs_state_query.py | 5 | 4 (override_settings, mock_canvas_service, mock_task_manager, review_service_factory) | 0 |

---

## Context and Integration

### Related Artifacts

- **Story File**: [32.10.story.md](../../docs/stories/32.10.story.md)
- **Story Status**: Ready (not yet implemented)
- **Acceptance Criteria Mapped**: 4 ACs

### Acceptance Criteria Validation

| Acceptance Criterion | Target File | Status | Notes |
|---------------------|-------------|--------|-------|
| AC-32.10.1: datetime.now() replaced | test_fsrs_manager.py:124,234 | :x: Not Fixed | Story Ready, not implemented |
| AC-32.10.2: yield fixture try/finally | test_fsrs_state_api.py:37-41 | :x: Not Fixed | Story Ready, not implemented |
| AC-32.10.3: clear() replaced with pop() | test_fsrs_state_api.py:41 | :x: Not Fixed | Story Ready, not implemented |
| AC-32.10.4: Regression (188 tests pass) | All EPIC-32 tests | :grey_question: Cannot Verify | Requires implementation first |

**Coverage**: 3/4 ACs have confirmed real issues. 1/4 requires implementation to verify.

### Coverage Gap Identified

| Gap | File | Issue | Story Coverage |
|-----|------|-------|---------------|
| Missing AC | test_fsrs_state_query.py:39-43 | yield without try/finally | :x: Not in Story 32.10 |

---

## Dimension Score Details

| Dimension | Score | Grade | Weight | Key Issue |
|-----------|-------|-------|--------|-----------|
| Determinism | 65/100 | C | 25% | datetime.now() without mocking (2 HIGH) |
| Isolation | 74/100 | C | 25% | clear() + no try/finally (2 HIGH) |
| Maintainability | 72/100 | B | 20% | File size + conditional assertions (2 HIGH) |
| Coverage | 58/100 | C | 15% | All ACs confirmed but 1 gap missed (5 HIGH) |
| Performance | 98/100 | A+ | 15% | Excellent — no issues |

---

## Next Steps

### Immediate Actions (Before Implementation)

1. **Update Story 32.10 scope** — Add `test_fsrs_state_query.py:39-43` try/finally fix
   - Priority: P1
   - Estimated Effort: 5 minutes

2. **Implement AC-32.10.1** — Fix datetime.now() in test_fsrs_manager.py
   - Priority: P0
   - Approach: freezegun or tolerance widening
   - Estimated Effort: 30 minutes

3. **Implement AC-32.10.2 + AC-32.10.3** — Fix fixture cleanup
   - Priority: P0
   - Apply to both test_fsrs_state_api.py AND test_fsrs_state_query.py
   - Estimated Effort: 15 minutes

### Follow-up Actions (Future PRs)

1. **Split test_fsrs_manager.py** — Reduce from 524 to ~260 lines each
   - Priority: P3
   - Target: Backlog

2. **Replace `if FSRS_AVAILABLE` with `@pytest.mark.skipif`**
   - Priority: P3
   - Target: Backlog

### Re-Review Needed?

:warning: Re-review after Story 32.10 implementation — verify all 4 ACs are satisfied and the coverage gap is addressed.

---

## Decision

**Recommendation**: Request Changes

**Rationale**:
Test quality scores 73/100 (Grade C) with 11 HIGH severity violations across determinism and isolation dimensions. The datetime.now() flakiness creates real CI reliability risk, and the DI override leakage pattern can cause cascading test failures. Story 32.10 correctly identifies the core issues but has one coverage gap (test_fsrs_state_query.py yield vulnerability). All issues are straightforward to fix and the story's implementation plan is sound. Once fixed and re-reviewed, these tests should score 85+ (Grade B).

---

## Appendix

### Violation Summary by Location

| File | Line | Severity | Dimension | Issue | Fix |
|------|------|----------|-----------|-------|-----|
| test_fsrs_manager.py | 124 | P0 | Determinism | datetime.now() in assertion | freeze_time or tolerance |
| test_fsrs_manager.py | 234 | P0 | Determinism | datetime.now() in assertion | freeze_time |
| test_fsrs_state_api.py | 37 | P0 | Isolation | yield without try/finally | Add try/finally |
| test_fsrs_state_api.py | 41 | P0 | Isolation | clear() wipes all overrides | Use pop() |
| test_fsrs_state_query.py | 39 | P1 | Isolation | yield without try/finally | Add try/finally |
| test_fsrs_state_query.py | 329 | P3 | Determinism | datetime.now() in test data | Fixed timestamp |
| test_fsrs_manager.py | 1-524 | P2 | Maintainability | 524 lines exceeds guideline | Split file |
| test_fsrs_manager.py | 79+ | P2 | Maintainability | if FSRS_AVAILABLE pattern | Use skipif |
| test_fsrs_state_query.py | 1-365 | P2 | Maintainability | 365 lines exceeds guideline | Consolidate |
| test_fsrs_state_api.py | 177-221 | P2 | Maintainability | Duplicate health test setup | Parametrize |

---

## Review Metadata

**Generated By**: BMad TEA Agent (Test Architect)
**Workflow**: testarch-test-review v5.0
**Review ID**: test-review-story-32.10-20260210
**Timestamp**: 2026-02-10
**Version**: 1.0
**Execution Mode**: Parallel (5 quality dimensions)
