"""
GraphitiEpisodeWorker behavior baseline (fix-test-infra-paralysis Phase 2).

These 5 scenarios cover the retry / backoff / dead-letter / metrics / request_id
semantics that were previously tested via MemoryService._write_to_graphiti_json_with_retry
(now deleted). The retry logic moved to backend/app/services/episode_worker.py:
GraphitiEpisodeWorker._handle_failure during the fix-rag-transform-and-episode-isolation
refactor; this test file is the new home for those assertions.

Spec source: openspec/changes/fix-test-infra-paralysis/specs/test-infrastructure-resilience/spec.md
  - "Test verifies enqueue behavior via EpisodeWorker"
  - "Test asserts exponential backoff series"
  - "Tests MUST NOT mock deprecated retry symbols"

The 5 scenarios:
  1. test_basic_enqueue_and_process — happy path: task enqueued, worker drains, metrics increment
  2. test_exponential_backoff_sleep_series — failure → retry → assert sleep[i] ∈ [0, 2**i), cap 60s
  3. test_dead_letter_on_retries_exhausted — 4 failures → dead-letter file written + metrics counter
  4. test_worker_metrics_completeness — all 6 counter fields update correctly
  5. test_request_id_propagation_through_episode_task — request_id flows through EpisodeTask → dead-letter JSONL
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.episode_worker import (
    EpisodeTask,
    GraphitiEpisodeWorker,
)


# Save a reference to the unpatched asyncio.sleep at import time. The
# `patch("app.services.episode_worker.asyncio.sleep", ...)` calls below patch
# the asyncio module's sleep attribute module-wide, so any code that does
# `import asyncio; await asyncio.sleep(0)` after the patch is active will
# hit the mock. Using this saved reference inside our side_effect functions
# avoids both infinite recursion and unintended sleep capture.
_ORIGINAL_ASYNCIO_SLEEP = asyncio.sleep


# ─── Test fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
async def worker(tmp_path):
    """A fresh GraphitiEpisodeWorker with a temp dead-letter path and a MagicMock graphiti client."""
    dead_letter = tmp_path / "dead_letter.jsonl"
    w = GraphitiEpisodeWorker(maxsize=10, dead_letter_path=str(dead_letter))
    mock_graphiti = MagicMock()
    mock_graphiti.add_episode = AsyncMock(return_value=None)
    w.set_graphiti_client(mock_graphiti)
    await w.start()
    yield w, mock_graphiti, dead_letter
    await w.stop(timeout=5.0)


def _make_task(name: str = "test_episode", request_id: str | None = None) -> EpisodeTask:
    return EpisodeTask(
        name=name,
        episode_body='{"action":"test"}',
        group_id="canvas-test",
        source_description="test_episode_worker_retry",
        max_retries=3,
        request_id=request_id,
    )


async def _wait_until(predicate, *, timeout: float = 2.0, interval: float = 0.02):
    """Tiny local poll helper to avoid pulling cross-conftest dependencies.

    Uses _ORIGINAL_ASYNCIO_SLEEP so that polling is not affected by
    `patch("app.services.episode_worker.asyncio.sleep", ...)` at the call site.
    """
    loop = asyncio.get_running_loop()
    start = loop.time()
    while loop.time() - start < timeout:
        if predicate():
            return
        await _ORIGINAL_ASYNCIO_SLEEP(interval)
    raise TimeoutError(f"Predicate {predicate} not satisfied within {timeout}s")


# ─── Scenario 1: basic enqueue + process success ────────────────────────────


@pytest.mark.asyncio
async def test_basic_enqueue_and_process(worker):
    """Spec scenario: 'Test verifies enqueue behavior via EpisodeWorker' (success path)."""
    w, mock_graphiti, dead_letter = worker

    task = _make_task(name="happy_path")
    enqueued = w.enqueue(task)

    assert enqueued is True, "enqueue should succeed when queue has capacity and is not shut down"

    # Wait for the worker loop to drain it
    await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    assert w.metrics.episodes_enqueued == 1
    assert w.metrics.episodes_processed == 1
    assert w.metrics.episodes_failed == 0
    assert w.metrics.episodes_dead_lettered == 0
    assert mock_graphiti.add_episode.await_count == 1

    # Inspect kwargs forwarded to graphiti.add_episode
    call_kwargs = mock_graphiti.add_episode.await_args.kwargs
    assert call_kwargs["name"] == "happy_path"
    assert call_kwargs["group_id"] == "canvas-test"
    assert call_kwargs["episode_body"] == '{"action":"test"}'

    # Dead-letter file should not exist (no failures)
    assert not dead_letter.exists()


# ─── Scenario 2: exponential backoff sleep series ───────────────────────────


@pytest.mark.asyncio
async def test_exponential_backoff_sleep_series(worker):
    """Spec scenario: 'Test asserts exponential backoff series'.

    Asserts that for retry_count i ∈ {0,1,2,3}, the sleep is in [0, min(2**i, 60)).
    Verifies the formula in EpisodeTask.backoff_seconds (full jitter, 60s cap).
    """
    w, mock_graphiti, dead_letter = worker

    # Capture sleep durations BUT don't actually sleep — wrap with passthrough.
    # NOTE: patching `app.services.episode_worker.asyncio.sleep` patches the
    # asyncio module's sleep attribute, which is module-wide (asyncio is a
    # singleton). So this patch also affects this test's own _wait_until poll
    # loop. We filter sleep values to only collect ones from `_handle_failure`
    # (i.e. those passed by the worker's retry loop, which are the
    # `task.backoff_seconds` jitter values, never the test's 0.02s polls).
    backoff_durations: list[float] = []

    async def recording_sleep(seconds):
        backoff_durations.append(seconds)
        await _ORIGINAL_ASYNCIO_SLEEP(0)  # yield without delaying

    # Make add_episode fail 3 times then succeed on the 4th attempt
    call_count = {"n": 0}

    async def flaky_add_episode(**kwargs):
        call_count["n"] += 1
        if call_count["n"] <= 3:
            raise RuntimeError(f"transient failure #{call_count['n']}")

    mock_graphiti.add_episode = AsyncMock(side_effect=flaky_add_episode)

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=recording_sleep):
        w.enqueue(_make_task(name="backoff_test"))

        # Wait for either a final processed event (3 retries → 4th succeeds → processed)
        # or 4+ failures (which would dead-letter — should not happen here)
        await _wait_until(
            lambda: w.metrics.episodes_processed >= 1 or w.metrics.episodes_dead_lettered >= 1,
            timeout=3.0,
        )

    assert call_count["n"] == 4, f"expected 4 add_episode attempts (3 fail + 1 success), got {call_count['n']}"
    assert w.metrics.episodes_processed == 1, "task should ultimately succeed on 4th attempt"
    assert w.metrics.episodes_dead_lettered == 0
    assert len(backoff_durations) == 3, (
        f"expected 3 backoff sleeps (one per retry), got {len(backoff_durations)}: {backoff_durations}"
    )

    # The formula: backoff_seconds = random.uniform(0, min(2**retry_count, 60))
    # On the i-th retry (i=1,2,3), sleep ∈ [0, min(2**i, 60))
    # = [0, 2), [0, 4), [0, 8) for the first three retries
    # We can't assert exact values (jitter) but we CAN assert each is in range and < 60
    assert 0.0 <= backoff_durations[0] < 2.0, f"retry 1 sleep {backoff_durations[0]} not in [0, 2)"
    assert 0.0 <= backoff_durations[1] < 4.0, f"retry 2 sleep {backoff_durations[1]} not in [0, 4)"
    assert 0.0 <= backoff_durations[2] < 8.0, f"retry 3 sleep {backoff_durations[2]} not in [0, 8)"

    # Cap verification — direct property test (no need to drive worker through 60s)
    capped_task = EpisodeTask(
        name="cap_test",
        episode_body="{}",
        group_id="g",
        source_description="t",
        retry_count=10,  # 2**10 = 1024
    )
    assert capped_task.backoff_seconds <= 60.0, "backoff must be capped at 60s for retry_count >= 6"


# ─── Scenario 3: dead-letter on retries exhausted ───────────────────────────


@pytest.mark.asyncio
async def test_dead_letter_on_retries_exhausted(worker):
    """Spec scenario: dead-letter is written + metrics counter increments after retries exhausted."""
    w, mock_graphiti, dead_letter = worker

    # Make add_episode always fail
    mock_graphiti.add_episode = AsyncMock(
        side_effect=RuntimeError("permanent failure for dead-letter test")
    )

    # Speed up the test by patching asyncio.sleep to no-op
    async def no_sleep(seconds):
        await _ORIGINAL_ASYNCIO_SLEEP(0)

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=no_sleep):
        w.enqueue(_make_task(name="will_fail_forever"))

        # Wait for dead-letter
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1, timeout=3.0)

    # max_retries=3 means 4 total attempts (initial + 3 retries) before dead-letter
    assert mock_graphiti.add_episode.await_count == 4
    assert w.metrics.episodes_failed == 4
    assert w.metrics.episodes_dead_lettered == 1
    assert w.metrics.episodes_processed == 0

    # Dead-letter file should now exist
    assert dead_letter.exists()
    lines = dead_letter.read_text().strip().splitlines()
    assert len(lines) == 1, f"expected 1 dead-letter entry, got {len(lines)}"

    record = json.loads(lines[0])
    assert record["name"] == "will_fail_forever"
    assert record["group_id"] == "canvas-test"
    assert record["error"] == "permanent failure for dead-letter test"
    assert record["error_type"] == "RuntimeError"
    assert record["retry_count"] == 3  # 3 retries attempted before dead-letter
    assert "failed_at" in record
    assert "episode_body_full" in record


# ─── Scenario 4: WorkerMetrics counter completeness ────────────────────────


@pytest.mark.asyncio
async def test_worker_metrics_completeness(worker):
    """Spec scenario: verify all metric fields update correctly across enqueue/process/fail/drop."""
    w, mock_graphiti, dead_letter = worker

    # 1 task that succeeds
    w.enqueue(_make_task(name="metric_pass"))
    await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    # 1 task that fails permanently → dead-letter
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError("metric_fail"))

    async def no_sleep(seconds):
        await _ORIGINAL_ASYNCIO_SLEEP(0)

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=no_sleep):
        w.enqueue(_make_task(name="metric_fail"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1, timeout=3.0)

    m = w.metrics.to_dict()
    # All fields present
    expected_keys = {
        "episodes_enqueued",
        "episodes_processed",
        "episodes_failed",
        "episodes_dead_lettered",
        "episodes_dropped_queue_full",
        "queue_depth",
        "worker_running",
        "avg_processing_time_ms",
        "max_processing_time_ms",
        "success_rate",
    }
    assert set(m.keys()) == expected_keys, f"metrics dict missing keys: {expected_keys - set(m.keys())}"

    # Sanity values
    assert m["episodes_enqueued"] == 2
    assert m["episodes_processed"] == 1
    assert m["episodes_failed"] >= 4  # 4 attempts failed before dead-letter
    assert m["episodes_dead_lettered"] == 1
    assert m["episodes_dropped_queue_full"] == 0
    assert m["worker_running"] is True
    assert 0.0 <= m["success_rate"] <= 1.0


# ─── Scenario 5: request_id propagation through EpisodeTask ────────────────


@pytest.mark.asyncio
async def test_request_id_propagation_through_episode_task(worker):
    """Spec scenario: request_id captured at enqueue time → flows into EpisodeTask → dead-letter JSONL."""
    w, mock_graphiti, dead_letter = worker

    # Make add_episode fail so the task gets dead-lettered (where we can read JSONL)
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError("force_dead_letter"))

    async def no_sleep(seconds):
        await _ORIGINAL_ASYNCIO_SLEEP(0)

    request_id = "trace-request-id-12345"
    task = _make_task(name="rid_test", request_id=request_id)

    # Sanity: EpisodeTask carries request_id
    assert task.request_id == request_id
    task_dict = task.to_dict()
    assert task_dict.get("request_id") == request_id

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=no_sleep):
        w.enqueue(task)
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1, timeout=3.0)

    # Inspect dead-letter JSONL
    assert dead_letter.exists()
    record = json.loads(dead_letter.read_text().strip().splitlines()[0])
    assert record.get("request_id") == request_id, (
        f"dead-letter record missing request_id; got: {record.keys()}"
    )
