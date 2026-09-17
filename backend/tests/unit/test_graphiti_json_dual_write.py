# Canvas Learning System - Unit Tests for the learning-episode enqueue path
# Story 36.9: 学习记忆双写（Neo4j + 时序记忆）
# Phase 2 migration: fix-rag-transform-and-episode-isolation
"""
Unit tests for the learning-episode write path of MemoryService.

Pipeline under test (fix-rag-transform-and-episode-isolation, Phase 2)
=====================================================================
``MemoryService.record_learning_event`` / ``record_temporal_event``
  → ``MemoryService._enqueue_episode`` (memory_service.py::_enqueue_episode)
  → ``GraphitiEpisodeWorker.enqueue`` (episode_worker.py::GraphitiEpisodeWorker)
  → background loop → ``graphiti.add_episode``

The two private JSON-write helpers this module was originally written against
were deleted in that refactor. A module-level skip was then added, which also
switched off several cases that had nothing to do with those helpers.
CARD-Y4-D-TAIL (第十四批, 2026-09-14) removes the skip and re-points the
affected cases at the pipeline above.

Scope boundary
--------------
Retry / backoff / dead-letter / metrics semantics are NOT covered here — they
live in ``backend/tests/unit/test_episode_worker_retry.py`` (5 scenarios).
This file covers the *enqueue contract as seen from MemoryService*: a recorded
learning event reaches the worker queue, and a rejected enqueue never breaks
the caller.

⚠️ Config-flag note (AC-36.9.5)
------------------------------
``settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE`` has no consumer left inside
``memory_service.py`` (2026-09-14 实测: the only mention there is a docstring
line; the live consumers are in ``canvas_service.py``). The two flag-named
cases below are kept for their nodeid history, but they pin *current*
behaviour rather than a working switch.

Test Coverage (Story 36.9 Task 4, re-mapped onto the current pipeline):
- 4.1: learning event is enqueued after the Neo4j write succeeds  [verified]
- 4.3: a rejected enqueue degrades silently  [verified]
- 4.5: with the flag on, the caller enqueues  [verified — True side only]

⚠️ 4.5's flag=False side is NOT verified either (Codex r4 LOW-1): the disables case
asserts against a client the pipeline never calls, so an implementation that skipped
recording when the flag is off would still pass both flag cases.

⚠️ 4.2 / 4.4 are NOT verified by this file (Codex r2 LOW-3). Their cases are kept
for nodeid history and their assertions are untouched, but no case here applies a
real downstream delay: the slow writes are attached to a client the current
pipeline never calls. "Caller is not blocked by a slow downstream" therefore has
no covering test in this repo right now — see the per-case notes below.

[Source: docs/stories/36.9.story.md#Testing]
[Migration: openspec/changes/fix-test-infra-paralysis/specs/test-infrastructure-resilience/spec.md]
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.episode_worker import GraphitiEpisodeWorker
from app.services.memory_service import MemoryService

# Constant was removed from memory_service; define locally for test compatibility
GRAPHITI_JSON_WRITE_TIMEOUT = 0.5

from tests.conftest import (
    simulate_async_delay,
    wait_for_condition,
    yield_to_event_loop,
)


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4jClient."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.stats = {"connected": True, "mode": "NEO4J", "initialized": True}
    client.create_learning_relationship = AsyncMock(return_value=True)
    client.get_concept_history = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_learning_memory_client():
    """Create a mock LearningMemoryClient."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.add_learning_episode = AsyncMock(return_value=True)
    return client


@pytest.fixture
def memory_service(mock_neo4j_client, mock_learning_memory_client):
    """Create MemoryService with mocked dependencies."""
    svc = MemoryService(
        neo4j_client=mock_neo4j_client,
    )
    svc._learning_memory = mock_learning_memory_client
    return svc


@pytest.fixture
async def ready_worker(tmp_path, monkeypatch):
    """A started GraphitiEpisodeWorker wired into ``memory_service.get_episode_worker``.

    Deliberately a *real* worker instance. ⚠️ Codex r3 LOW-2 更正：一个同时提供
    ``is_ready`` 与 ``enqueue`` 的 stub **并不会**让 ``_enqueue_episode`` 的 readiness
    分支与 ``EpisodeTask`` 创建失去覆盖——那些是生产代码，stub 之下照样执行。stub
    真正拿掉的是 **worker 自身实现**的覆盖：队列计数（``episodes_enqueued``，本文件
    的接纳断言正是读它）与 ``is_ready`` 的真实语义（``_started and _graphiti is not None``）。
    只 mock 最外层 graphiti 客户端，这两样保持真实。
    ⚠️ Codex r4 LOW-2 更正：**不要**把「队列满/已关闭时 ``enqueue`` 返回 False」也算进来——
    本文件没有任何用例触发那条真实分支（拒绝场景是直接替换 ``enqueue`` 的返回值模拟的），
    真实 ``QueueFull`` / shutdown 处理若发生回归，本文件发现不了。
    """
    w = GraphitiEpisodeWorker(maxsize=64, dead_letter_path=str(tmp_path / "dead_letter.jsonl"))
    mock_graphiti = MagicMock()
    mock_graphiti.add_episode = AsyncMock(return_value=None)
    w.set_graphiti_client(mock_graphiti)
    await w.start()
    monkeypatch.setattr("app.services.memory_service.get_episode_worker", lambda: w)
    yield w
    await w.stop(timeout=5.0)


class TestGraphitiJsonDualWrite:
    """Test cases for Graphiti JSON dual-write functionality."""

    @pytest.mark.asyncio
    async def test_dual_write_called_after_neo4j_success(self, memory_service, ready_worker):
        """
        Task 4.1: the learning event is enqueued after the Neo4j write succeeds.

        ✅ AC-36.9.1: 学习事件写入 Neo4j 成功后自动尝试写入时序记忆

        CARD-Y4-D-TAIL: the private retry helper this case used to patch was
        deleted by fix-rag-transform-and-episode-isolation. The equivalent entry
        point is ``_enqueue_episode`` → ``GraphitiEpisodeWorker.enqueue``, so the
        assertion now inspects the task that actually reaches the worker queue.
        ``enqueue`` is wrapped rather than replaced, so the real queue still runs.
        """
        # Arrange
        await memory_service.initialize()
        enqueued = []
        real_enqueue = ready_worker.enqueue

        def spy_enqueue(task):
            enqueued.append(task)
            return real_enqueue(task)

        # Act
        with patch.object(ready_worker, "enqueue", side_effect=spy_enqueue):
            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
                score=85,
            )

        # Assert
        assert episode_id is not None
        assert episode_id.startswith("episode-")
        # Exactly one episode reached the worker (not >= 0 — a silent no-op must fail here)
        assert len(enqueued) == 1, f"expected 1 enqueued episode, got {len(enqueued)}"
        task = enqueued[0]
        # Literals below come from memory_service.record_learning_event, not from
        # the task itself — an expectation read back off the subject proves nothing.
        assert task.name == "learning:测试概念"
        assert task.source_description.startswith("canvas_learning:")
        assert "测试概念" in task.episode_body
        assert "node-123" in task.episode_body
        assert "score: 85/100" in task.episode_body
        # group_id is derived from the active vault (ContextVar), so only its
        # shape is stable across environments. ⚠️ This is a shape check only — a
        # wrong-but-non-empty group would still pass (Codex r1).
        assert isinstance(task.group_id, str) and task.group_id
        # The spy records before delegating, so len(enqueued) alone only proves an
        # attempt. The worker's own counter proves the queue actually accepted it.
        assert ready_worker.metrics.episodes_enqueued == 1

    @pytest.mark.asyncio
    async def test_fire_and_forget_doesnt_block_return(self, memory_service, mock_learning_memory_client):
        """
        Task 4.2: Test fire-and-forget doesn't block record_learning_event() return.

        ✅ AC-36.9.2: 记忆写入使用 fire-and-forget 模式，不阻塞主流程

        ⚠️ 覆盖边界（CARD-Y4-D-TAIL 2026-09-14 实测，断言保持原样）：本用例把
        ``slow_write`` 挂在 ``mock_learning_memory_client.add_learning_episode``
        上，而现行 ``record_learning_event`` 不再调用该客户端（改走
        ``_enqueue_episode``）⇒ ``slow_write`` 永不执行，下面的 ``elapsed < 0.5``
        并非由「fire-and-forget 生效」保证，当前只证明调用方自身不阻塞。断言之所
        以保持原样，是为了证明本用例在模块级 skip 之前就是绿的（净覆盖损失的证
        据）。⚠️ Codex r1 MEDIUM 更正：此处原写「真实语义见 X」不成立——本仓当前
        **没有**任何用例对调用方施加真实的下游延迟来验证非阻塞；入队路径的用例
        （test_dual_write_called_after_neo4j_success）证明的是「确实入了队」，
        不是「慢下游不会拖住调用方」。该覆盖缺口已登记移交。
        """
        # Arrange
        await memory_service.initialize()

        # Make JSON write slow (150ms)
        async def slow_write(*args, **kwargs):
            await simulate_async_delay(0.15)
            return True

        mock_learning_memory_client.add_learning_episode = slow_write

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            start_time = time.time()
            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
            )
            elapsed = time.time() - start_time

        # Assert - Should return immediately (< 0.5s), not wait for 1s JSON write
        assert episode_id is not None
        assert elapsed < 0.5, f"Expected < 0.5s, but took {elapsed:.2f}s (blocked by JSON write)"

    @pytest.mark.asyncio
    async def test_json_write_failure_doesnt_affect_main_flow(self, memory_service, ready_worker):
        """
        Task 4.3: a rejected enqueue degrades silently.

        ✅ AC-36.9.3: 时序记忆写入失败时静默降级，不抛出异常

        CARD-Y4-D-TAIL: the downstream failure is now modelled at the queue
        boundary — ``enqueue`` returns False when the queue is full or shut down
        (episode_worker.py::GraphitiEpisodeWorker.enqueue). The caller must still
        return a usable episode_id.
        """
        # Arrange
        await memory_service.initialize()

        # Act — downstream rejects the episode
        with patch.object(ready_worker, "enqueue", return_value=False) as rejecting_enqueue:
            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
            )

        # Assert
        assert episode_id is not None
        assert episode_id.startswith("episode-")
        # The rejection must have been reached, otherwise this proves nothing
        rejecting_enqueue.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_protection(self, memory_service, mock_learning_memory_client):
        """
        Task 4.4: Test timeout protection (500ms).

        ✅ AC-36.9.4: 记忆写入超时保护，超时后放弃写入

        ⚠️ 覆盖边界（CARD-Y4-D-TAIL 2026-09-14 实测，断言保持原样）：现行管线没有
        per-write 超时——下游超时/失败由 GraphitiEpisodeWorker 的重试与 dead-letter
        承担（test_episode_worker_retry.py scenario 2/3）。本用例的 slow write 挂在
        从不被调用的客户端上，且等待时长由 ``wait_for_condition`` 自行控制。
        ⚠️ Codex r2 LOW-3 更正：因此它连「调用方不被下游拖住」都**证明不了**——
        本用例运行期间根本不存在下游延迟。它当前只证明调用方会返回一个 episode_id。
        断言保持原样以证明本用例在模块级 skip 之前就是绿的。
        """
        # Arrange
        await memory_service.initialize()

        # Make JSON write slow (150ms, way beyond timeout for fire-and-forget)
        async def very_slow_write(*args, **kwargs):
            await simulate_async_delay(0.15)
            return True

        mock_learning_memory_client.add_learning_episode = very_slow_write

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

            start_time = time.time()

            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
            )

            # Wait for fire-and-forget timeout task to complete (poll instead of hard sleep)
            await wait_for_condition(
                lambda: time.time() - start_time >= GRAPHITI_JSON_WRITE_TIMEOUT + 0.3,
                timeout=GRAPHITI_JSON_WRITE_TIMEOUT + 1.0,
                description="fire-and-forget timeout",
            )
            total_elapsed = time.time() - start_time

        # Assert
        assert episode_id is not None
        # Story 38.6: timeout increased to 2.0s; allow margin for fire-and-forget completion
        assert total_elapsed < GRAPHITI_JSON_WRITE_TIMEOUT + 1.5, (
            f"Expected < {GRAPHITI_JSON_WRITE_TIMEOUT + 1.5:.1f}s with timeout, but took {total_elapsed:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_config_flag_disables_dual_write(self, memory_service, mock_learning_memory_client):
        """
        Task 4.5: Test config flag disables dual-write when false.

        ✅ AC-36.9.5: 可通过环境变量 ENABLE_GRAPHITI_JSON_DUAL_WRITE 开关双写功能

        ⚠️ 覆盖边界（CARD-Y4-D-TAIL 2026-09-14 实测，断言保持原样）：该 flag 在
        ``memory_service.py`` 内已无消费点（live consumers 在 canvas_service.py），
        且 ``record_learning_event`` 不再调用 ``add_learning_episode`` ⇒ 下面的
        ``assert_not_called()`` 与 flag 取值无关，当前恒成立。断言保持原样以证明
        本用例在模块级 skip 之前就是绿的；flag 开关语义的真实覆盖缺口已登记移交。
        """
        # Arrange
        await memory_service.initialize()

        # Act
        with patch("app.services.memory_service.settings") as mock_settings:
            # Disable dual-write
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            episode_id = await memory_service.record_learning_event(
                user_id="test-user",
                canvas_path="test.canvas",
                node_id="node-123",
                concept="测试概念",
                agent_type="scoring-agent",
            )

            # Yield control to let any background tasks run
            await yield_to_event_loop()

        # Assert
        assert episode_id is not None
        # Verify add_learning_episode was NOT called (dual-write disabled)
        mock_learning_memory_client.add_learning_episode.assert_not_called()

    @pytest.mark.asyncio
    async def test_config_flag_enables_dual_write(self, memory_service, ready_worker):
        """
        With the flag on, the learning event reaches the worker queue.

        ⚠️ CARD-Y4-D-TAIL: ``ENABLE_GRAPHITI_JSON_DUAL_WRITE`` has no consumer in
        ``memory_service.py``, so this case can no longer verify a switch. It pins
        current behaviour **for the flag=True side only**: recording enqueues.
        ⚠️ Codex r3 LOW-1 更正：不要读成「无论 flag 如何都入队」——本用例没有测
        flag=False 那一侧，而 test_config_flag_disables_dual_write 的断言也已与 flag
        脱钩（见其注脚）。⇒ 若日后有人让 flag 重新生效、在 False 时跳过入队，
        **这两条都发现不了**。该缺口已登记移交。
        The nodeid is kept so the history of AC-36.9.5 stays traceable.
        """
        # Arrange
        await memory_service.initialize()

        # Act
        with patch.object(ready_worker, "enqueue", wraps=ready_worker.enqueue) as spy_enqueue:
            with patch("app.services.memory_service.settings") as mock_settings:
                mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

                episode_id = await memory_service.record_learning_event(
                    user_id="test-user",
                    canvas_path="test.canvas",
                    node_id="node-123",
                    concept="测试概念",
                    agent_type="scoring-agent",
                    score=90,
                )

        # Assert
        assert episode_id is not None
        spy_enqueue.assert_called_once()
        # The real queue actually accepted it (metrics come from the worker, not the spy).
        assert ready_worker.metrics.episodes_enqueued == 1

    # ── 已删除：3 条私有 JSON-write 助手的 logging 用例（CARD-Y4-D-TAIL）──────
    #
    # 三条名为 ..._success_logging / ..._timeout_logging / ..._failure_logging 的
    # 用例（名字里带那个已删私有助手）直接调用了
    # fix-rag-transform-and-episode-isolation 删除的私有助手，移除模块级 skip 后
    # 恒 AttributeError。这三条断言的语义（成功写入 / 超时 / 失败 各自的可观测性）
    # 现由 GraphitiEpisodeWorker 承担。归属逐条如下——⚠️ 先读本段末尾的定性：
    # 这是**邻近场景归属，不是等价覆盖**（Codex r2 LOW-2：此处原写「等价覆盖」
    # 与末段定性自相矛盾）：
    #
    #   success_logging → test_episode_worker_retry.py::test_basic_enqueue_and_process
    #       （成功路径：metrics.episodes_processed == 1 + add_episode.await_count == 1）
    #   timeout_logging → test_episode_worker_retry.py::test_exponential_backoff_sleep_series
    #       + ::test_dead_letter_on_retries_exhausted（失败 → 退避 → 耗尽落 dead-letter）
    #   failure_logging → test_episode_worker_retry.py::test_dead_letter_on_retries_exhausted
    #       （dead-letter 记录含 error / error_type / retry_count）
    #       + ::test_worker_metrics_completeness（metrics.episodes_failed）
    #
    # ⚠️ 归属定性：**邻近场景，非等价覆盖**（Codex r1 MEDIUM 更正——此处原写
    # 「比原断言更强」不成立）。逐条列出**未被接替**的观测点：
    #   - success：`logger.debug` 被调用、且日志文案含该次 episode_id —— 无接替；
    #   - failure：`logger.warning` 文案含 "failed" —— 无接替（新归属处断言的是
    #     dead-letter 记录字段与 metrics 计数，不读日志）；
    #   - timeout：原用例施加的是**慢下游**输入（下游久不返回），而 scenario 2/3
    #     的下游是**立即抛 RuntimeError** —— 输入形态不同，慢下游这一路现无覆盖。
    # 即：日志可观测性与慢下游输入在本仓当前无专门用例覆盖（已登记移交）。

    @pytest.mark.asyncio
    async def test_record_temporal_event_dual_write(self, memory_service, ready_worker):
        """
        Test the temporal-event path also reaches the worker queue.

        ✅ Task 1.5 现行等价: ``record_temporal_event`` → ``_enqueue_episode``
        (memory_service.py::record_temporal_event 末段)。
        """
        # Arrange
        await memory_service.initialize()
        enqueued = []
        real_enqueue = ready_worker.enqueue

        def spy_enqueue(task):
            enqueued.append(task)
            return real_enqueue(task)

        # Act
        with patch.object(ready_worker, "enqueue", side_effect=spy_enqueue):
            event_id = await memory_service.record_temporal_event(
                event_type="node_created",
                session_id="session-123",
                canvas_path="test.canvas",
                node_id="node-456",
                metadata={"node_text": "新建节点内容"},
            )

        # Assert
        assert event_id is not None
        assert event_id.startswith("event-")
        assert len(enqueued) == 1, f"expected 1 enqueued episode, got {len(enqueued)}"
        task = enqueued[0]
        # Literals from memory_service.record_temporal_event, not read back off the task.
        assert task.name == "temporal:node_created:新建节点内容"
        assert task.source_description == "canvas_temporal:node_created"
        assert "node-456" in task.episode_body
        # Same reason as in test_dual_write_called_after_neo4j_success: the spy
        # records before delegating, so the worker's own counter is what proves
        # the queue accepted the task rather than rejecting it (Codex r2 LOW-1).
        assert ready_worker.metrics.episodes_enqueued == 1

    # ── 已删除：test_learning_memory_dataclass_creation（CARD-Y4-D-TAIL）───────
    #
    # 该用例断言 ``record_learning_event`` 会构造 ``LearningMemory`` dataclass 并
    # 交给 ``LearningMemoryClient.add_learning_episode``。移除模块级 skip 后它以
    # TimeoutError 变红：现行 ``record_learning_event`` 不再走该客户端，被等待的
    # 回调永不触发（它不引用已删私有助手，所以此前未被列为断裂点）。
    #
    # 现行管线的等价载体是 ``EpisodeTask``，其字段已由本文件
    # test_dual_write_called_after_neo4j_success / test_record_temporal_event_dual_write
    # 断言（name / source_description / episode_body），worker 侧的转发字段由
    # test_episode_worker_retry.py::test_basic_enqueue_and_process 断言。
    #
    # ⚠️ 覆盖损失如实登记（非等价覆盖）：``LearningMemory`` dataclass 本身仍是活
    # 代码（clients/neo4j_edge_client.py 定义，services/agent_service.py 调用
    # ``add_learning_episode``），但那条路径不经过 MemoryService，不在本文件的覆盖
    # 对象内。本卡删除后，该 dataclass 的字段构造在本文件不再有任何覆盖；是否另
    # 立用例覆盖 agent_service 侧路径，已登记移交。
