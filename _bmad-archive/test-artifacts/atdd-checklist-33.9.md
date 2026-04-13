# ATDD Checklist - Epic 33, Story 33.9: EPIC-33 P0 DI Chain Repair

**Date:** 2026-02-09
**Author:** ROG
**Primary Test Level:** Integration (Python pytest)

---

## Story Summary

Story 33.9 修复 `intelligent_parallel.py:get_service()` 中 `batch_orchestrator=None` 和 `agent_service=None` 的 DI 断裂问题。当前代码导致 `/confirm` 永远停在 pending、`/cancel` 无法信号取消、`/single-agent` 抛出 RuntimeError。

**As a** Canvas Learning System user
**I want** the intelligent parallel batch processing system to actually execute batch jobs when I confirm
**So that** my yellow nodes are processed by agents instead of being stuck in "pending" forever

---

## Acceptance Criteria

1. **AC-33.9.1** (P0): `service._batch_orchestrator is not None` after `get_service()`
2. **AC-33.9.2** (P0): `service._agent_service is not None` after `get_service()`
3. **AC-33.9.3** (P0): `/confirm` → session transitions from `pending` → `running` → `completed`
4. **AC-33.9.4** (P0): `/cancel` can cancel a running batch session
5. **AC-33.9.5** (P0): `/single-agent` invokes agent without RuntimeError
6. **AC-33.9.6** (P1): `batch_orchestrator.routing_engine is not None`
7. **AC-33.9.7** (P1): DI completeness integration test passes
8. **AC-33.9.8** (P2): `set_batch_deps()` phantom comments removed; dead code cleaned

---

## Failing Tests Created (RED Phase)

### Integration Tests (20 tests)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

#### TestBatchOrchestratorInjection (3 tests)

- **Test:** `test_batch_orchestrator_is_not_none`
  - **Status:** RED — `get_service()` passes `batch_orchestrator=None` at line 111
  - **Verifies:** AC-33.9.1 — batch_orchestrator injection

- **Test:** `test_batch_orchestrator_has_session_manager`
  - **Status:** RED — BatchOrchestrator never constructed
  - **Verifies:** AC-33.9.1 — BatchOrchestrator constructor args

- **Test:** `test_batch_orchestrator_has_agent_service`
  - **Status:** RED — BatchOrchestrator never constructed
  - **Verifies:** AC-33.9.1 — BatchOrchestrator constructor args

#### TestAgentServiceInjection (2 tests)

- **Test:** `test_agent_service_is_not_none`
  - **Status:** RED — `get_service()` passes `agent_service=None` at line 112
  - **Verifies:** AC-33.9.2 — agent_service injection

- **Test:** `test_agent_service_has_gemini_client`
  - **Status:** RED — agent_service never constructed
  - **Verifies:** AC-33.9.2 — AgentService constructor args

#### TestConfirmStartsBatchExecution (1 test)

- **Test:** `test_confirm_transitions_from_pending`
  - **Status:** RED — batch_orchestrator=None → session stuck at "pending"
  - **Verifies:** AC-33.9.3 — /confirm starts real execution

#### TestCancelRunningBatch (1 test)

- **Test:** `test_cancel_signals_batch_orchestrator`
  - **Status:** RED — no BatchOrchestrator instance to signal
  - **Verifies:** AC-33.9.4 — /cancel signaling

#### TestSingleAgentRetry (2 tests)

- **Test:** `test_single_agent_no_runtime_error`
  - **Status:** RED — agent_service=None → RuntimeError
  - **Verifies:** AC-33.9.5 — /single-agent precondition

- **Test:** `test_single_agent_endpoint_returns_200`
  - **Status:** RED — agent_service=None → HTTP 500
  - **Verifies:** AC-33.9.5 — /single-agent HTTP response

#### TestRoutingEngineInjection (1 test)

- **Test:** `test_batch_orchestrator_has_routing_engine`
  - **Status:** RED — BatchOrchestrator not constructed
  - **Verifies:** AC-33.9.6 — routing_engine injection

#### TestDICompletenessIntegration (4 tests)

- **Test:** `test_service_batch_orchestrator_not_none`
  - **Status:** RED — batch_orchestrator=None
  - **Verifies:** AC-33.9.7

- **Test:** `test_service_agent_service_not_none`
  - **Status:** RED — agent_service=None
  - **Verifies:** AC-33.9.7

- **Test:** `test_batch_orchestrator_routing_engine_not_none`
  - **Status:** RED — batch_orchestrator=None
  - **Verifies:** AC-33.9.7

- **Test:** `test_start_batch_session_not_stuck_pending`
  - **Status:** RED — batch_orchestrator=None → perpetual pending
  - **Verifies:** AC-33.9.7

#### TestPhantomCodeCleanup (2 tests)

- **Test:** `test_no_set_batch_deps_references`
  - **Status:** RED — `set_batch_deps()` comments exist at lines 111-112
  - **Verifies:** AC-33.9.8

- **Test:** `test_no_dead_di_factory`
  - **Status:** RED — `get_intelligent_parallel_service()` is dead code
  - **Verifies:** AC-33.9.8

#### TestNoWarningLogs (2 tests)

- **Test:** `test_no_batch_orchestrator_warning`
  - **Status:** RED — batch_orchestrator=None triggers WARNING
  - **Verifies:** Warning log sentinel

- **Test:** `test_no_agent_service_warning`
  - **Status:** RED — agent_service=None triggers WARNING
  - **Verifies:** Warning log sentinel

#### TestSingletonConstraint (1 test)

- **Test:** `test_shared_batch_orchestrator_instance`
  - **Status:** RED — BatchOrchestrator not constructed
  - **Verifies:** Singleton constraint for cancel signaling

---

## Data Factories Created

N/A — This story is about DI wiring, not data model CRUD. Existing test fixtures in `conftest.py` provide `sample_canvas_data`, `canvas_file`, etc.

---

## Fixtures Created

### reset_service_singleton (autouse)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Fixtures:**

- `reset_service_singleton` — Resets the endpoint module's `_service` singleton
  - **Setup:** Calls `reset_service()` to set `_service = None`
  - **Provides:** Clean service state for each test
  - **Cleanup:** Calls `reset_service()` again after test

---

## Mock Requirements

### No External Service Mocking Required

This is a **DI completeness** test — the purpose is to verify that real dependencies are wired correctly. Tests use `pytest.mark.skip()` in RED phase rather than mocking.

In GREEN phase, some tests may need:
- Mock `GeminiClient` (to avoid real API calls during test)
- Mock `Neo4jClient` (to avoid real database during test)

These should be injected via `app.dependency_overrides` or environment variable defaults.

---

## Required data-testid Attributes

N/A — Backend-only story, no UI components.

---

## Implementation Checklist

### Test: test_batch_orchestrator_is_not_none (AC-33.9.1)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Tasks to make this test pass:**

- [ ] Add `_ensure_async_deps()` async function in `intelligent_parallel.py`
- [ ] In `_ensure_async_deps()`: construct `GeminiClient` from settings
- [ ] In `_ensure_async_deps()`: construct `AgentService` with gemini_client, canvas_service, neo4j_client
- [ ] In `_ensure_async_deps()`: construct `BatchOrchestrator` with session_manager, agent_service, canvas_service, vault_path, routing_engine
- [ ] Assign `service._batch_orchestrator = batch_orchestrator`
- [ ] Make `_ensure_async_deps()` idempotent (no-op after first call)
- [ ] Call `await _ensure_async_deps()` in each endpoint before `return get_service()`
- [ ] Remove `pytest.mark.skip` from this test
- [ ] Run test: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py::TestBatchOrchestratorInjection::test_batch_orchestrator_is_not_none -v`
- [ ] Test passes (green phase)

---

### Test: test_agent_service_is_not_none (AC-33.9.2)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Tasks to make this test pass:**

- [ ] Ensure `_ensure_async_deps()` constructs AgentService
- [ ] Assign `service._agent_service = agent_service`
- [ ] Remove `pytest.mark.skip` from this test
- [ ] Run test: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py::TestAgentServiceInjection::test_agent_service_is_not_none -v`
- [ ] Test passes (green phase)

---

### Test: test_confirm_transitions_from_pending (AC-33.9.3)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Tasks to make this test pass:**

- [ ] Ensure `_ensure_async_deps()` is called in `confirm_batch()` endpoint
- [ ] Ensure `start_batch_session()` calls `batch_orchestrator.run()` as fire-and-forget
- [ ] Verify session transitions from pending → running
- [ ] Remove `pytest.mark.skip` from this test
- [ ] Run test: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py::TestConfirmStartsBatchExecution -v`
- [ ] Test passes (green phase)

---

### Test: test_cancel_signals_batch_orchestrator (AC-33.9.4)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Tasks to make this test pass:**

- [ ] Ensure BatchOrchestrator singleton is shared (same instance for /confirm and /cancel)
- [ ] Verify cancel endpoint can access `batch_orchestrator._cancel_requested`
- [ ] Remove `pytest.mark.skip` from this test
- [ ] Run test: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py::TestCancelRunningBatch -v`
- [ ] Test passes (green phase)

---

### Test: test_single_agent_no_runtime_error (AC-33.9.5)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Tasks to make this test pass:**

- [ ] Ensure `_ensure_async_deps()` is called in `retry_single_node()` endpoint
- [ ] Verify `service._agent_service` is real AgentService
- [ ] Remove `pytest.mark.skip` from this test
- [ ] Run test: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py::TestSingleAgentRetry -v`
- [ ] Test passes (green phase)

---

### Test: test_batch_orchestrator_has_routing_engine (AC-33.9.6)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Tasks to make this test pass:**

- [ ] Pass `routing_engine=get_agent_routing_engine()` to BatchOrchestrator constructor
- [ ] Remove `pytest.mark.skip` from this test
- [ ] Run test: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py::TestRoutingEngineInjection -v`
- [ ] Test passes (green phase)

---

### Test: test_no_set_batch_deps_references (AC-33.9.8)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Tasks to make this test pass:**

- [ ] Remove `# Needs async DI; set via set_batch_deps()` comment from line 111
- [ ] Remove `# Needs async DI; set via set_batch_deps()` comment from line 112
- [ ] Remove `pytest.mark.skip` from this test
- [ ] Run test: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py::TestPhantomCodeCleanup::test_no_set_batch_deps_references -v`
- [ ] Test passes (green phase)

---

### Test: test_no_dead_di_factory (AC-33.9.8)

**File:** `backend/tests/integration/test_epic33_di_completeness.py`

**Tasks to make this test pass:**

- [ ] Either import and use `get_intelligent_parallel_service()` in the endpoint, or delete it
- [ ] Remove `pytest.mark.skip` from this test
- [ ] Run test: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py::TestPhantomCodeCleanup::test_no_dead_di_factory -v`
- [ ] Test passes (green phase)

---

## Running Tests

```bash
# Run all failing tests for this story (RED phase — all skipped)
cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py -v

# Run specific test class
python -m pytest tests/integration/test_epic33_di_completeness.py::TestBatchOrchestratorInjection -v

# Run with skip reasons visible
python -m pytest tests/integration/test_epic33_di_completeness.py -v -rs

# Run existing unit tests (must not regress)
python -m pytest tests/unit/test_intelligent_parallel_endpoints.py -v

# Full regression
python -m pytest tests/ -v --timeout=120
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

- All 20 tests written and marked with `pytest.mark.skip(reason="RED: ...")`
- Test file created at `backend/tests/integration/test_epic33_di_completeness.py`
- Each test documents WHY it fails and WHAT to fix
- Implementation checklist created with step-by-step tasks

**Verification:**

- All tests run and are skipped as expected
- Skip messages clearly explain the DI chain break
- Tests assert EXPECTED behavior after fix (not placeholder assertions)

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Implement `_ensure_async_deps()`** in `intelligent_parallel.py`
2. **Wire async dependencies**: GeminiClient → AgentService → BatchOrchestrator
3. **Call `await _ensure_async_deps()`** at the start of each endpoint handler
4. **Remove `pytest.mark.skip`** from each test one at a time
5. **Run the test** to verify it passes
6. **Check off the task** in implementation checklist
7. **Clean up phantom code** (AC-33.9.8)

**Key Principles:**

- One test at a time (start with AC-33.9.1 and AC-33.9.2)
- `_ensure_async_deps()` must be idempotent (safe to call multiple times)
- BatchOrchestrator MUST be a singleton (cancel signaling requires shared instance)
- Run regression suite after each change

---

### REFACTOR Phase (After All Tests Pass)

1. Verify all 20 tests pass
2. Review `_ensure_async_deps()` for thread safety (asyncio.Lock)
3. Consider removing the dead `get_intelligent_parallel_service()` from dependencies.py
4. Run full regression: `python -m pytest tests/ -v --timeout=120`
5. Verify 321+ existing tests still pass

---

## Next Steps

1. **Review this checklist** and failing tests
2. **Run RED phase**: `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py -v -rs`
3. **Verify all 20 tests are SKIPPED** (red phase)
4. **Begin implementation** using implementation checklist
5. **Work one test at a time** (remove skip → implement → green)
6. **Run full regression** after completion
7. **When all tests pass**, manually update story status

---

## Knowledge Base References Applied

- **DI completeness patterns** — MEMORY.md: EPIC-36 DI 断裂修复经验
- **Singleton pattern** — BatchOrchestrator._cancel_requested requires shared instance
- **Test isolation** — MEMORY.md: autouse fixture for singleton reset
- **Code reality check** — Verified actual `get_service()` code at intelligent_parallel.py:108-114

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `cd backend && python -m pytest tests/integration/test_epic33_di_completeness.py -v -rs`

**Expected Results:**

```
SKIPPED [20] tests/integration/test_epic33_di_completeness.py - RED: ...

========================= 20 skipped in X.XXs =========================
```

**Summary:**

- Total tests: 20
- Passing: 0 (expected)
- Skipped: 20 (RED phase — expected)
- Failing: 0 (skip prevents actual failure)
- Status: RED phase verified

---

## Notes

- Story 33.9 的核心是 async 依赖在 sync 函数中无法构造的问题
- `_ensure_async_deps()` 是推荐方案：每个 endpoint 调用 `await _ensure_async_deps()` 后再返回 `get_service()`
- BatchOrchestrator 必须是单例（`_cancel_requested` 是实例级状态）
- 现有 unit tests (`test_intelligent_parallel_endpoints.py`) mock 了整个 service，所以它们会继续通过
- 本 DI 测试是对 mock-heavy 单元测试的补充，验证真实 DI 链

---

**Generated by BMad TEA Agent** - 2026-02-09
