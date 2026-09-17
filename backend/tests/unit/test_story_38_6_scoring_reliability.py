"""
Story 38.6: Scoring Write Reliability — Unit Tests

Tests:
- AC-1: Timeout-retry alignment (outer >= inner total)
- AC-2: Failed write tracking to data/failed_writes.jsonl
- AC-3: Startup recovery from fallback file
- AC-4: Merged view — failed scores in learning history
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.failed_writes_constants import (
    FAILED_WRITES_FILE,
)
from app.services.agent_service import (
    MEMORY_WRITE_TIMEOUT,
    _record_failed_write,
)
from app.services.episode_worker import EpisodeTask, GraphitiEpisodeWorker
from app.services.memory_service import MemoryService

# Constants removed from memory_service; define locally for test compatibility
GRAPHITI_JSON_WRITE_TIMEOUT = 0.5
GRAPHITI_RETRY_BACKOFF_BASE = 0.1


class TestAC1TimeoutRetryAlignment:
    """AC-1: Outer timeout must be >= sum of inner retries + margin.

    第十四批 T10-D (2026-09-15): CARD-RED-C1 给本类三条用例打了
    `xfail(strict=True)`，reason 写死了承接卡的 ID —— 它们断言的是本文件模块级**本地桩**
    (`GRAPHITI_JSON_WRITE_TIMEOUT` / `GRAPHITI_RETRY_BACKOFF_BASE`)，而 `59586af1`
    (2026-03-26) 已把这两个常量连同 `MemoryService._write_to_graphiti_json_with_retry`
    一起删除（`backend/app` 下两符号 0 命中），故永远不会自然 XPASS。本卡按测试侧
    决策程序去标（⛔ 全程不改 `backend/app`）：

      - `test_retry_backoff_base_is_1_second` / `test_backoff_progression`
        → **改写对齐真 worker**（`EpisodeTask.backoff_seconds`）。旧「定值 1s/2s/4s」
        的等价不变量是 full jitter 的**上界**序列 1/2/4，名实一致，去标后 PASS。
      - `test_inner_per_attempt_timeout_increased`
        → **删除**。现 worker 对 `add_episode` 不加任何超时包装
        （`_process_episode` 直接 await；全文件 `asyncio.wait_for` 只用于连通性探针与
        `stop()` 排空），该语义**无等价**，不在测试侧伪造一个出来。退役登记见
        `_bmad-output/审查/evidence-epw-coverage/coverage-matrix-*.md` 附录 A。

    重试 / 退避 / 死信 / 计数 / 隐私的完整等价覆盖在
    `backend/tests/unit/test_episode_worker_coverage_epw.py`。
    """

    def test_outer_timeout_is_at_least_10_seconds(self):
        """[P0] MEMORY_WRITE_TIMEOUT must be >= 10s per AC-1."""
        assert MEMORY_WRITE_TIMEOUT >= 10.0

    def test_retry_backoff_base_is_1_second(self):
        """[P0] 退避基数 1.0s —— 现实现的等价物是 full jitter 的**上界基数**。

        `EpisodeTask.backoff_seconds` = `random.uniform(0, min(2**retry_count, 60))`，
        `retry_count == 0` 时区间为 [0, 1]：基数仍是 1 秒，只是由定值变成上界。把
        `random.uniform` 换成「返回上界」的桩即可对公式做确定性断言，而不是对抖动采样猜区间。

        ⚠️ 本条钉的是**属性本身**在 `retry_count == 0` 上的取值，**不是**「第一次实际重试」的退避：
        `_handle_failure` 先 `retry_count += 1` 再取 `backoff_seconds`，所以第一次实际重试的区间是
        [0, 2]。实际重试链路的退避实参由
        `test_episode_worker_coverage_epw.py::test_retry_actually_sleeps_backoff_seconds_series_2_4_8`
        钉住（Codex r1 HIGH-1 更正）。
        """
        seen: list[tuple[float, float]] = []

        def capture(low, high):
            seen.append((low, high))
            return high

        with patch("app.services.episode_worker.random.uniform", side_effect=capture):
            delay = EpisodeTask(
                name="backoff_base",
                episode_body="{}",
                group_id="vault:cs_61b",
                source_description="test_story_38_6",
                retry_count=0,
            ).backoff_seconds

        assert seen == [(0, 1)], f"retry_count=0 时退避区间必须是 [0, 1]，实测 {seen}"
        assert delay == 1.0

    def test_outer_timeout_covers_inner_total(self):
        """
        [P0] Verify: outer timeout >= 3 × per_attempt_timeout + sum(backoffs) + margin.

        Inner total = 3 × 2.0s + (1.0 + 2.0 + 4.0) = 13.0s
        Outer timeout must be >= 13.0s (we use 15.0s).
        """
        max_retries = 2  # 3 attempts total
        inner_total = (max_retries + 1) * GRAPHITI_JSON_WRITE_TIMEOUT + sum(
            GRAPHITI_RETRY_BACKOFF_BASE * (2**i) for i in range(max_retries)
        )
        assert MEMORY_WRITE_TIMEOUT >= inner_total, (
            f"Outer timeout ({MEMORY_WRITE_TIMEOUT}s) < inner total ({inner_total}s)"
        )

    def test_backoff_progression(self):
        """[P1] 退避序列 1s/2s/4s —— 现实现的等价物是**上界**序列，并新增 60s 封顶。

        旧实现 `base * 2**attempt` 是定值；现实现每次抽 `[0, min(2**retry_count, 60)]`，
        上界随 `retry_count` 走 1/2/4，但超过 2**6 后恒为 60（旧实现没有封顶，这是迁移新增的保护）。

        ⚠️ 同上：这里的 1/2/4 是**属性**在 `retry_count = 0/1/2` 上的上界。**实际**三次重试因为
        `_handle_failure` 先递增计数，走的是 2/4/8——由
        `test_episode_worker_coverage_epw.py::test_retry_actually_sleeps_backoff_seconds_series_2_4_8` 钉住。
        """
        bounds: list[float] = []

        def capture(low, high):
            bounds.append(high)
            return high

        def _task(retry_count: int) -> EpisodeTask:
            return EpisodeTask(
                name=f"backoff_{retry_count}",
                episode_body="{}",
                group_id="vault:cs_61b",
                source_description="test_story_38_6",
                retry_count=retry_count,
            )

        with patch("app.services.episode_worker.random.uniform", side_effect=capture):
            for attempt in range(3):
                _task(attempt).backoff_seconds
            _task(10).backoff_seconds

        assert bounds[:3] == [1, 2, 4], f"上界序列必须是 1/2/4，实测 {bounds[:3]}"
        assert bounds[3] == 60, "2**10 = 1024 必须被封顶到 60s"


class TestAC2FailedWriteTracking:
    """AC-2: Failed writes must be recorded to data/failed_writes.jsonl."""

    def test_record_failed_write_creates_file(self, tmp_path):
        """[P0] _record_failed_write creates JSONL entry with correct fields."""
        fallback_file = tmp_path / "data" / "failed_writes.jsonl"

        with (
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
            patch("app.services.agent_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
        ):
            _record_failed_write(
                event_type="scoring-agent",
                concept_id="node_abc",
                canvas_name="test.canvas",
                score=35.0,
                error_reason="timeout after 15.0s",
            )

        assert fallback_file.exists()
        lines = fallback_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["event_type"] == "scoring-agent"
        assert entry["concept_id"] == "node_abc"
        assert entry["canvas_name"] == "test.canvas"
        assert entry["score"] == 35.0
        assert entry["error_reason"] == "timeout after 15.0s"
        assert "timestamp" in entry

    def test_record_failed_write_appends(self, tmp_path):
        """[P0] Multiple failures append to the same file."""
        fallback_file = tmp_path / "data" / "failed_writes.jsonl"

        with (
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
            patch("app.services.agent_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
        ):
            _record_failed_write("a", "n1", "c1", 10.0, "err1")
            _record_failed_write("b", "n2", "c2", 20.0, "err2")

        lines = fallback_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_record_failed_write_with_none_score(self, tmp_path):
        """[P1] Score can be None (not all writes have scores)."""
        fallback_file = tmp_path / "data" / "failed_writes.jsonl"

        with (
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
            patch("app.services.agent_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
        ):
            _record_failed_write("hint-generation", "n1", "c1", None, "err")

        entry = json.loads(fallback_file.read_text(encoding="utf-8").strip())
        assert entry["score"] is None


class TestAC3StartupRecovery:
    """AC-3: Application startup replays failed writes.

    CARD-Y4-D-TAIL (第十四批, 2026-09-14): this class was switched off by a
    class-level skip because one case monkeypatched a private retry helper that
    fix-rag-transform-and-episode-isolation had deleted. Replay now runs through
    ``MemoryService._enqueue_episode`` → ``GraphitiEpisodeWorker.enqueue``
    (memory_service.py::recover_failed_writes), so the replay cases below drive a
    real worker instead. ``test_recover_no_file`` needs no worker — it exercises
    the early-return branch before any replay happens.
    """

    @pytest.fixture
    def memory_service(self):
        """Create a MemoryService with mocked dependencies."""
        ms = MemoryService.__new__(MemoryService)
        ms.neo4j = MagicMock()
        ms._learning_memory = AsyncMock()
        ms._learning_memory.add_learning_episode = AsyncMock(return_value=True)
        ms._initialized = True
        ms._episodes = []
        ms._score_history_cache = {}
        return ms

    @pytest.fixture
    async def ready_worker(self, tmp_path, monkeypatch):
        """A started GraphitiEpisodeWorker wired into ``memory_service.get_episode_worker``.

        A real worker, not a stub. ⚠️ Codex r3 LOW-2 更正：一个同时提供 ``is_ready``
        与 ``enqueue`` 的 stub **并不会**让 ``_enqueue_episode`` 的 readiness 分支与
        ``EpisodeTask`` 创建失去覆盖（那些是生产代码，stub 之下照样执行）。stub 真正
        拿掉的是 **worker 自身实现**的覆盖：队列计数与 ``is_ready`` 的真实语义
        （``_started and _graphiti is not None``）。只 mock 最外层 graphiti 客户端。
        ⚠️ Codex r4 LOW-2 更正：**不要**把「队列满/已关闭时 ``enqueue`` 返回 False」也算
        进来——``test_recover_partial_failure`` 的失败侧是直接替换 ``enqueue`` 返回值模拟的，
        没有触发真实拒绝分支，真实 ``QueueFull`` / shutdown 处理的回归本类发现不了。
        """
        w = GraphitiEpisodeWorker(maxsize=64, dead_letter_path=str(tmp_path / "dead_letter.jsonl"))
        mock_graphiti = MagicMock()
        mock_graphiti.add_episode = AsyncMock(return_value=None)
        w.set_graphiti_client(mock_graphiti)
        await w.start()
        monkeypatch.setattr("app.services.memory_service.get_episode_worker", lambda: w)
        yield w
        await w.stop(timeout=5.0)

    @pytest.mark.asyncio
    async def test_recover_no_file(self, memory_service):
        """[P0] No fallback file → returns zeros, no crash."""
        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE",
            Path("/nonexistent/failed_writes.jsonl"),
        ):
            result = await memory_service.recover_failed_writes()

        assert result == {"recovered": 0, "pending": 0}

    @pytest.mark.asyncio
    async def test_recover_successful_replay(self, memory_service, tmp_path, ready_worker):
        """[P0] Entries are replayed and removed from file on success.

        CARD-Y4-D-TAIL: replay succeeds only when the worker accepts the episode,
        so this case now needs a started worker. (It never patched the deleted
        retry helper itself — only ``test_recover_partial_failure`` did; this case
        was switched off because the class-level skip covered the whole class.)
        """
        fallback_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-06T10:00:00",
            "event_type": "scoring-agent",
            "concept_id": "node_1",
            "canvas_name": "test.canvas",
            "score": 35.0,
            "error_reason": "timeout",
        }
        fallback_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with (
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
        ):
            result = await memory_service.recover_failed_writes()

        assert result["recovered"] == 1
        assert result["pending"] == 0
        # File should be deleted after full recovery
        assert not fallback_file.exists()

    @pytest.mark.asyncio
    async def test_recover_partial_failure(self, memory_service, tmp_path, ready_worker):
        """[P0] If replay fails, entry stays in file.

        CARD-Y4-D-TAIL: the original case monkeypatched a now-deleted private retry
        helper so that the first replay returned True and the second False. The
        equivalent boundary under the current pipeline is ``worker.enqueue``, which
        returns False when the queue is full or shut down. Only that final call is
        substituted — ``_enqueue_episode`` still runs its ``is_ready`` check and
        builds a real ``EpisodeTask`` for both entries.
        """
        fallback_file = tmp_path / "failed_writes.jsonl"
        entries = [
            {
                "timestamp": "t1",
                "event_type": "a",
                "concept_id": "n1",
                "canvas_name": "c1",
                "score": 10.0,
                "error_reason": "e1",
            },
            {
                "timestamp": "t2",
                "event_type": "b",
                "concept_id": "n2",
                "canvas_name": "c2",
                "score": 20.0,
                "error_reason": "e2",
            },
        ]
        fallback_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")

        # First enqueue succeeds, second is rejected (queue full / shut down)
        call_count = 0

        def flaky_enqueue(task):
            nonlocal call_count
            call_count += 1
            return call_count == 1  # First succeeds, second fails

        ready_worker.enqueue = flaky_enqueue

        with (
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
        ):
            result = await memory_service.recover_failed_writes()

        assert result["recovered"] == 1
        assert result["pending"] == 1
        # Both entries must have reached the enqueue boundary, otherwise the
        # 1/1 split above could also come from the replay never running at all.
        assert call_count == 2, f"expected 2 enqueue attempts, got {call_count}"
        # File should contain only the still-pending entry — and it must be the
        # one that failed (n2), not the one that succeeded. Counting lines alone
        # would also pass if recovery kept the wrong entry (Codex r4 LOW-3).
        remaining = fallback_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(remaining) == 1
        assert json.loads(remaining[0])["concept_id"] == "n2"

    @pytest.mark.asyncio
    async def test_recover_malformed_entries_preserved(self, memory_service, tmp_path, ready_worker):
        """[P1] Malformed JSON lines are preserved in pending to avoid data loss.

        CARD-Y4-D-TAIL: the valid entry must actually replay for ``recovered == 1``
        to mean anything, so a started worker is required.
        """
        fallback_file = tmp_path / "failed_writes.jsonl"
        fallback_file.write_text(
            "not valid json\n"
            + json.dumps(
                {
                    "timestamp": "t",
                    "concept_id": "n",
                    "canvas_name": "c",
                    "score": 5.0,
                    "error_reason": "e",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        with (
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
        ):
            result = await memory_service.recover_failed_writes()

        # Valid entry recovered, malformed preserved as pending (#9 fix)
        assert result["recovered"] == 1
        assert result["pending"] == 1
        # The point of this case is no data loss: the unparseable line must still
        # be on disk. A 1/1 count alone would also pass if it were dropped and
        # something else were counted as pending (Codex r4 LOW-3).
        remaining = fallback_file.read_text(encoding="utf-8").strip().splitlines()
        assert remaining == ["not valid json"]


class TestAC4MergedView:
    """AC-4: Failed scores are merged into learning history results."""

    @pytest.fixture
    def memory_service(self):
        ms = MemoryService.__new__(MemoryService)
        ms.neo4j = AsyncMock()
        ms.neo4j.get_learning_history = AsyncMock(return_value=[])
        ms._learning_memory = AsyncMock()
        ms._initialized = True
        ms._episodes = []
        ms._episodes_recovered = True  # [Code Review C2]: skip recovery in tests
        ms._score_history_cache = {}
        return ms

    def test_load_failed_scores_empty(self, memory_service):
        """[P0] No fallback file → empty list."""
        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE",
            Path("/nonexistent"),
        ):
            result = memory_service.load_failed_scores()
        assert result == []

    def test_load_failed_scores_with_entries(self, memory_service, tmp_path):
        """[P0] Returns structured entries from JSONL."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-06T10:00:00",
            "event_type": "scoring-agent",
            "concept_id": "node_1",
            "canvas_name": "test.canvas",
            "score": 35.0,
            "error_reason": "timeout",
        }
        fallback_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with (
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
        ):
            results = memory_service.load_failed_scores()

        assert len(results) == 1
        assert results[0]["source"] == "fallback"
        assert results[0]["score"] == 35.0
        assert results[0]["node_id"] == "node_1"

    @pytest.mark.asyncio
    async def test_get_learning_history_merges_failed_scores(self, memory_service, tmp_path):
        """[P0] get_learning_history() includes fallback entries in results."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-06T10:00:00",
            "event_type": "scoring-agent",
            "concept_id": "node_1",
            "canvas_name": "test.canvas",
            "score": 35.0,
            "error_reason": "timeout",
        }
        fallback_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        # Neo4j returns one episode
        neo4j_episode = {
            "timestamp": "2026-02-06T09:00:00",
            "node_id": "node_2",
            "concept": "concept_2",
            "score": 40.0,
        }
        memory_service.neo4j.get_learning_history = AsyncMock(return_value=[neo4j_episode])

        with (
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
        ):
            result = await memory_service.get_learning_history(user_id="test")

        # Both Neo4j episode and fallback entry should appear
        assert result["total"] == 2
        sources = [item.get("source") for item in result["items"]]
        assert "fallback" in sources

    @pytest.mark.asyncio
    async def test_get_learning_history_deduplicates(self, memory_service, tmp_path):
        """[P1] Fallback entries with same node_id+timestamp as Neo4j entries are excluded."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-06T10:00:00",
            "event_type": "scoring-agent",
            "concept_id": "node_1",
            "canvas_name": "test.canvas",
            "score": 35.0,
            "error_reason": "timeout",
        }
        fallback_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        # Neo4j already has the same entry (recovered between request)
        neo4j_episode = {
            "timestamp": "2026-02-06T10:00:00",
            "node_id": "node_1",
            "concept": "node_1",
            "score": 35.0,
        }
        memory_service.neo4j.get_learning_history = AsyncMock(return_value=[neo4j_episode])

        with (
            patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file),
            patch("app.core.failed_writes_constants.FAILED_WRITES_FILE", fallback_file),
        ):
            result = await memory_service.get_learning_history(user_id="test")

        # Should not duplicate — only 1 entry
        assert result["total"] == 1


class TestRegressionSafety:
    """Verify changes don't break existing functionality."""

    def test_failed_writes_file_path_in_data_dir(self):
        """[P0] Shared constant has correct name and path."""
        assert FAILED_WRITES_FILE.name == "failed_writes.jsonl"
        assert "data" in str(FAILED_WRITES_FILE)
        # Both modules now import from the same shared constant (#4, #11)
        from app.services.agent_service import FAILED_WRITES_FILE as AS_FW
        from app.services.memory_service import FAILED_WRITES_FILE as MS_FW

        assert AS_FW == MS_FW == FAILED_WRITES_FILE

    def test_constants_are_consistent(self):
        """[P0] Memory write timeout covers inner retry budget."""
        # 3 attempts × 2.0s timeout + backoff sum (1+2=3s) = 9s
        # Outer must be > 9s
        max_inner = 3 * GRAPHITI_JSON_WRITE_TIMEOUT + 3.0  # 3s backoff for 2 retries
        assert MEMORY_WRITE_TIMEOUT > max_inner
