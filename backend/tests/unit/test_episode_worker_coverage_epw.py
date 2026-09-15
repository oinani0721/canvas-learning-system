"""
GraphitiEpisodeWorker 等价覆盖 — CARD-EPW-COVERAGE（第十四批）。

背景（CARD-RED-C1 / UAT-CARD-RED-C1-2026-09-08 §8.1）
=====================================================
`59586af1` (2026-03-26) 删除了 `MemoryService._write_to_graphiti_json_with_retry`
及常量 `GRAPHITI_JSON_WRITE_TIMEOUT` / `GRAPHITI_RETRY_BACKOFF_BASE`；重试 / 退避 /
死信 / 计数 / 隐私语义整体迁入 `app/services/episode_worker.py`。迁走后，原来的 22 条
用例被 skip 掩盖（`test_memory_service_write_retry` 模块级 18 +
`test_failure_observability::TestMemoryServiceDualWriteFailure` 类级 3 +
`test_qa_38_6_scoring_reliability_extra::TestFullCycleIntegration` 类级 1），而
`test_episode_worker_retry.py` 的 5 条用例**从未**与它们逐条对映。

本文件是那 22 条里 21 条的等价承接方（逐条映射见
`_bmad-output/审查/evidence-epw-coverage/coverage-matrix-*.md`）。第 22 条
（`TestWriteRetryStrictQA::test_record_temporal_event_uses_retry_method`）是**调用方接线**
语义，worker 侧无对应接线点（`get_episode_worker()` 直调为本卡禁止面），登记退役移交。

⚠️ 等价 ≠ 逐字复刻（如实声明的语义收窄 / 反转）
------------------------------------------------
1. **退避**：旧实现是定值 `base * 2**attempt` = 1s/2s/4s；现实现是
   `random.uniform(0, min(2**retry_count, 60))`（full jitter, 60s 封顶,
   `EpisodeTask.backoff_seconds`）。可对齐的不变量是**上界序列**仍为 1/2/4/8，
   故断言写成「上界 + 单调不减 + 封顶」，不对抖动取定值。
2. **每次尝试超时**：旧实现有 per-attempt timeout 常量；现 worker 对
   `add_episode` **不加任何超时包装**（`_process_episode` 直接 `await`，全文件
   `asyncio.wait_for` 只出现在连通性探针与 `stop()` 排空）。该语义**无等价**，
   不在本文件伪造。
3. **超时/异常的日志区分**：旧实现靠 warning 文案后缀 `(timeout)` 区分；现实现
   靠死信记录的 `error_type` 字段区分（重试 warning 只带 `str(error)`，而
   `TimeoutError` 的 `str()` 为空串）。本文件按**现实现**钉 `error_type`。
4. **重试身份**：旧实现每次重试**新建** LearningMemory（新 timestamp）；现实现把
   **同一个** `EpisodeTask` 对象重新入队，`created_at` / `reference_time` 不变，
   只有 `retry_count` 递增。这是语义**反转**，本文件按现实现钉死。
5. **失败计数器**：旧实现递增模块级 `dual_write_failures`；现实现递增 worker 自己的
   `WorkerMetrics.episodes_failed` / `episodes_dead_lettered`。本文件只覆盖后者。

⛔ 隔离纪律（CARD-EPW-COVERAGE 完成条件 (c)/(i)）
------------------------------------------------
`DeadLetterStore.__init__` 与 `GraphitiEpisodeWorker.__init__` 的死信路径默认值都是
**相对路径** `"data/dead_letter_episodes.jsonl"`，而承重裁判一律 `cd backend` 后跑
⇒ 漏传一处就会追加写进 `backend/data/` 这个真死信坟场。因此本文件内：
  - 每一处 `GraphitiEpisodeWorker(...)` 必带 kwarg `dead_letter_path=`（tmp_path 派生）；
  - 每一处 `DeadLetterStore(...)` 必带 kwarg `file_path=`（tmp_path 派生）；
  - `get_episode_worker()` / `cleanup_episode_worker()` 直调 = 0（单例工厂
    `episode_worker.py::get_episode_worker` 无参实例化，恒用默认相对路径，且模块级
    `_worker_instance` 会跨用例残留）。
静态判据见 `_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py`（逐 Call 断言）。
graphiti 客户端全程 `MagicMock`，零真库、零 7691/7687、零 `initialize_graphiti`。
"""

import asyncio
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from graphiti_core.errors import GroupIdValidationError

from app.services.episode_worker import (
    DeadLetterStore,
    EpisodeTask,
    GraphitiEpisodeWorker,
    _redact,
)

# 与 test_episode_worker_retry.py 同一范式：`patch("…episode_worker.asyncio.sleep")`
# 改的是 asyncio 模块的属性（模块单例），会连带影响本文件自己的轮询。导入期存一份
# 未打桩的引用，供 side_effect 与轮询helper 使用，避免递归与误捕。
_ORIGINAL_ASYNCIO_SLEEP = asyncio.sleep

#: 被测 group_id 取 D16 冒号格式；graphiti 侧期望值写**字面量**（`_process_episode`
#: 内 `semantic_group_id(sanitize_group_id_for_graphiti(...))` 落影子分组）。⛔ 不调
#: 同一函数求值——期望值与被测量同源会让断言跟着实现一起退化。
_GROUP_ID = "vault:cs_61b"
_EXPECTED_GRAPHITI_GROUP_ID = "vault__cs_61b__semantic"

_BODY = '{"action":"epw_coverage"}'


# ─── fixtures / helpers ─────────────────────────────────────────────────────


@pytest.fixture
def dead_letter_path(tmp_path):
    """本文件唯一的死信落点来源 —— tmp_path 派生，永不落 backend/data。"""
    return tmp_path / "dead_letter.jsonl"


@pytest.fixture
async def worker(dead_letter_path, monkeypatch):
    """A started GraphitiEpisodeWorker: tmp_path 死信 + MagicMock graphiti。

    `DEAD_LETTER_STORE_FULL_BODY` 显式 delenv —— 隐私断言描述的是**默认**行为，
    继承 shell 里偶然导出的值会得到假红（同 test_episode_worker_retry.py:56 的教训）。
    """
    monkeypatch.delenv("DEAD_LETTER_STORE_FULL_BODY", raising=False)
    w = GraphitiEpisodeWorker(maxsize=16, dead_letter_path=str(dead_letter_path))
    mock_graphiti = MagicMock()
    mock_graphiti.add_episode = AsyncMock(return_value=None)
    w.set_graphiti_client(mock_graphiti)
    await w.start()
    yield w, mock_graphiti, dead_letter_path
    await w.stop(timeout=5.0)


def _make_task(
    name: str = "epw_task",
    *,
    max_retries: int = 3,
    body: str = _BODY,
    request_id: str | None = None,
    metadata: dict | None = None,
    entity_types: dict | None = None,
    edge_types: dict | None = None,
    source: str | None = None,
) -> EpisodeTask:
    return EpisodeTask(
        name=name,
        episode_body=body,
        group_id=_GROUP_ID,
        source_description="test_episode_worker_coverage_epw",
        max_retries=max_retries,
        request_id=request_id,
        metadata=metadata if metadata is not None else {},
        entity_types=entity_types,
        edge_types=edge_types,
        source=source,
    )


async def _wait_until(predicate, *, timeout: float = 3.0, interval: float = 0.02):
    """本地轮询 helper（不跨 conftest）。用未打桩的 sleep，免受 sleep patch 影响。"""
    loop = asyncio.get_running_loop()
    start = loop.time()
    while loop.time() - start < timeout:
        if predicate():
            return
        await _ORIGINAL_ASYNCIO_SLEEP(interval)
    raise TimeoutError(f"Predicate {predicate} not satisfied within {timeout}s")


async def _no_sleep(seconds):
    """退避不真睡 —— 只让出事件循环。"""
    await _ORIGINAL_ASYNCIO_SLEEP(0)


def _read_records(path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").strip().splitlines()]


# ═══════════════════════════════════════════════════════════════════════════
# A 组 — 重试与尝试次数
# 承接: test_memory_service_write_retry::TestWriteToGraphitiJsonWithRetry
#       {first_attempt, after_one_retry, after_two_retries, all_retries_timeout,
#        exception_triggers_retry, all_retries_exception, zero_retries_single_attempt}
#       + TestWriteRetryStrictQA::test_mixed_timeout_then_exception_then_success
# ═══════════════════════════════════════════════════════════════════════════


async def test_first_attempt_success_no_retry(worker):
    """等价于「首次写入成功」：一次 add_episode，零重试、零死信。"""
    w, mock_graphiti, dl = worker
    task = _make_task(name="first_attempt_ok")

    assert w.enqueue(task) is True
    await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    assert mock_graphiti.add_episode.await_count == 1
    assert w.metrics.episodes_enqueued == 1
    assert w.metrics.episodes_processed == 1
    assert w.metrics.episodes_failed == 0
    assert w.metrics.episodes_dead_lettered == 0
    assert task.retry_count == 0, "成功路径不得递增 retry_count"
    assert not dl.exists(), "成功路径不得建死信文件"


async def test_success_after_one_retry(worker):
    """等价于「第一次失败后重试成功」：2 次尝试、1 次退避、最终 processed。"""
    w, mock_graphiti, dl = worker
    attempts = {"n": 0}

    async def fail_once(**kwargs):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise asyncio.TimeoutError()

    mock_graphiti.add_episode = AsyncMock(side_effect=fail_once)
    task = _make_task(name="retry_once")

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep) as slept:
        w.enqueue(task)
        await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    assert attempts["n"] == 2
    assert w.metrics.episodes_failed == 1
    assert w.metrics.episodes_processed == 1
    assert w.metrics.episodes_dead_lettered == 0
    assert slept.await_count == 1, "每次重试前恰好一次退避 sleep"
    assert task.retry_count == 1
    assert not dl.exists()


async def test_success_after_two_retries(worker):
    """等价于「两次失败后第三次成功」：3 次尝试、2 次退避。"""
    w, mock_graphiti, dl = worker
    attempts = {"n": 0}

    async def fail_twice(**kwargs):
        attempts["n"] += 1
        if attempts["n"] <= 2:
            raise asyncio.TimeoutError()

    mock_graphiti.add_episode = AsyncMock(side_effect=fail_twice)
    task = _make_task(name="retry_twice")

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep) as slept:
        w.enqueue(task)
        await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    assert attempts["n"] == 3
    assert w.metrics.episodes_failed == 2
    assert w.metrics.episodes_processed == 1
    assert slept.await_count == 2
    assert task.retry_count == 2
    assert not dl.exists()


async def test_all_attempts_timeout_then_dead_letter(worker):
    """等价于「全部重试失败（超时）」：max_retries=3 ⇒ 4 次尝试后落死信。"""
    w, mock_graphiti, dl = worker
    mock_graphiti.add_episode = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep):
        w.enqueue(_make_task(name="always_timeout"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    assert mock_graphiti.add_episode.await_count == 4, "初次 + 3 次重试"
    assert w.metrics.episodes_failed == 4
    assert w.metrics.episodes_dead_lettered == 1
    assert w.metrics.episodes_processed == 0

    records = _read_records(dl)
    assert len(records) == 1
    # 旧实现靠 warning 文案后缀 "(timeout)" 区分超时；现实现靠 error_type 字段。
    assert records[0]["error_type"] == "TimeoutError"
    assert records[0]["retry_count"] == 3


async def test_non_timeout_exception_triggers_retry(worker):
    """等价于「异常（非超时）同样触发重试」：不是只有超时才重试。"""
    w, mock_graphiti, dl = worker
    attempts = {"n": 0}

    async def fail_with_value_error(**kwargs):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ValueError("non-timeout failure")

    mock_graphiti.add_episode = AsyncMock(side_effect=fail_with_value_error)

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep) as slept:
        w.enqueue(_make_task(name="value_error_retry"))
        await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    assert attempts["n"] == 2, "ValueError 必须走重试，而不是直接死信"
    assert slept.await_count == 1
    assert w.metrics.episodes_dead_lettered == 0
    assert not dl.exists()


async def test_all_attempts_exception_then_dead_letter(worker):
    """等价于「全部重试失败（异常）」：非超时异常耗尽后同样落死信。"""
    w, mock_graphiti, dl = worker
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError("always broken"))

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep):
        w.enqueue(_make_task(name="always_exception"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    assert mock_graphiti.add_episode.await_count == 4
    assert w.metrics.episodes_dead_lettered == 1
    records = _read_records(dl)
    assert len(records) == 1
    assert records[0]["error_type"] == "RuntimeError"
    assert records[0]["error"] == "always broken"


async def test_zero_max_retries_single_attempt_then_dead_letter(worker):
    """等价于「max_retries=0 只尝试一次」：can_retry 首次即 False ⇒ 立即死信、零退避。"""
    w, mock_graphiti, dl = worker
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError("one shot"))
    task = _make_task(name="zero_retries", max_retries=0)
    assert task.can_retry is False, "max_retries=0 时 retry_count=0 也不得可重试"

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep) as slept:
        w.enqueue(task)
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    assert mock_graphiti.add_episode.await_count == 1
    assert slept.await_count == 0, "不重试就不得退避"
    assert w.metrics.episodes_failed == 1
    assert w.metrics.episodes_dead_lettered == 1
    assert _read_records(dl)[0]["retry_count"] == 0


async def test_mixed_timeout_then_exception_then_success(worker):
    """等价于「混合异常类型：超时 → 异常 → 成功」：错误类型切换不打断重试链。"""
    w, mock_graphiti, dl = worker
    attempts = {"n": 0}

    async def mixed(**kwargs):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise asyncio.TimeoutError()
        if attempts["n"] == 2:
            raise RuntimeError("second failure is a different type")

    mock_graphiti.add_episode = AsyncMock(side_effect=mixed)

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep) as slept:
        w.enqueue(_make_task(name="mixed_errors"))
        await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    assert attempts["n"] == 3
    assert slept.await_count == 2
    assert w.metrics.episodes_failed == 2
    assert w.metrics.episodes_processed == 1
    assert w.metrics.episodes_dead_lettered == 0
    assert not dl.exists()


# ═══════════════════════════════════════════════════════════════════════════
# B 组 — 退避（上界 / 单调 / 封顶）
# 承接: TestWriteRetryStrictQA::{test_exponential_backoff_delays,
#       test_exponential_backoff_all_failures}（旧定值 1.0s/2.0s → 现上界 1/2/4）
# ═══════════════════════════════════════════════════════════════════════════


def test_backoff_upper_bound_series_is_1_2_4():
    """旧「1s/2s/4s 定值序列」的等价物 = full jitter 的**上界**序列 1/2/4。

    把 `random.uniform` 换成「返回上界」的桩，退避值就等于 `min(2**retry_count, 60)`，
    于是可以对公式做确定性断言（而不是对抖动采样猜区间）。
    """
    observed_bounds = []

    def fake_uniform(low, high):
        observed_bounds.append((low, high))
        return high

    with patch("app.services.episode_worker.random.uniform", side_effect=fake_uniform):
        delays = [
            EpisodeTask(
                name=f"b{i}",
                episode_body=_BODY,
                group_id=_GROUP_ID,
                source_description="backoff",
                retry_count=i,
            ).backoff_seconds
            for i in range(3)
        ]

    assert observed_bounds == [(0, 1), (0, 2), (0, 4)], "退避区间必须是 [0, 2**retry_count]"
    assert delays == [1.0, 2.0, 4.0], "上界序列与旧实现的 1s/2s/4s 定值序列一致"


def test_backoff_upper_bound_is_monotonic_and_capped_at_60():
    """上界单调不减且封顶 60s —— 旧实现没有封顶，这是本次迁移新增的保护。"""
    bounds = []

    def fake_uniform(low, high):
        bounds.append(high)
        return high

    with patch("app.services.episode_worker.random.uniform", side_effect=fake_uniform):
        for i in range(0, 12):
            EpisodeTask(
                name=f"cap{i}",
                episode_body=_BODY,
                group_id=_GROUP_ID,
                source_description="backoff_cap",
                retry_count=i,
            ).backoff_seconds

    assert bounds == sorted(bounds), f"上界必须单调不减: {bounds}"
    assert max(bounds) == 60, "上界必须封顶在 60s"
    assert bounds[:7] == [1, 2, 4, 8, 16, 32, 60], "2**i 直到触顶后恒为 60"

    # 不打桩的真实抖动：落在 [0, 上界] 内（本条不依赖上面的桩）。
    live = EpisodeTask(
        name="live_jitter",
        episode_body=_BODY,
        group_id=_GROUP_ID,
        source_description="backoff_cap",
        retry_count=10,
    )
    for _ in range(50):
        assert 0.0 <= live.backoff_seconds <= 60.0


# ═══════════════════════════════════════════════════════════════════════════
# C 组 — 死信落盘 / 计数 / 可重放
# 承接: test_failure_observability::TestMemoryServiceDualWriteFailure::
#       test_dual_write_retry_failure_writes_dead_letter
#       + test_qa_38_6_extra::TestFullCycleIntegration::
#         test_full_cycle_fail_record_recover_merge（失败记账半程）
# ═══════════════════════════════════════════════════════════════════════════


async def test_dead_letter_written_on_retry_exhaustion(worker):
    """等价于「重试耗尽 → 写死信」：文件、计数器、记录字段三者同时成立。"""
    w, mock_graphiti, dl = worker
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError("exhausted"))

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep):
        w.enqueue(_make_task(name="exhaust_me", request_id="req-epw-001"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    assert dl.exists()
    records = _read_records(dl)
    assert len(records) == 1
    record = records[0]
    assert record["name"] == "exhaust_me"
    assert record["group_id"] == _GROUP_ID, "死信留的是业务 group_id，不是 graphiti 影子分组"
    assert record["request_id"] == "req-epw-001"
    assert record["error_type"] == "RuntimeError"
    assert "failed_at" in record


async def test_dead_letter_record_is_replayable_without_full_body(worker):
    """等价于「失败 → 记账 → 可恢复」的记账半程：记录自带重放所需的校验信息。

    ⚠️ 语义收窄（如实声明）：旧用例的「恢复 → 合并视图」半程属 MemoryService
    (`recover_failed_writes` / `load_failed_scores`) 面，不在 worker 内，本文件不覆盖。
    """
    w, mock_graphiti, dl = worker
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError("replay me"))

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep):
        w.enqueue(_make_task(name="replayable"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    record = _read_records(dl)[0]
    # 期望值独立于被测量：直接对字面 body 求 sha256，不从 record 反取。
    assert record["episode_body_sha256"] == hashlib.sha256(_BODY.encode("utf-8")).hexdigest()
    assert record["episode_body_length"] == len(_BODY)
    assert record["source_description"] == "test_episode_worker_coverage_epw"
    assert record["reference_time"], "重放需要原始 reference_time"
    # 真实行为锚点：`to_dict()` 落的是截断到 200 字符的正文（存量行为，非隐私开关）。
    assert record["episode_body"] == _BODY[:200]


def test_dead_letter_store_count_matches_appended_lines(dead_letter_path):
    """`DeadLetterStore.count()` 语义：文件不存在 = 0；每次 store 追加一行。"""
    store = DeadLetterStore(file_path=str(dead_letter_path))
    assert store.count() == 0, "文件未建时 count 必须是 0 而不是报错"
    assert not dead_letter_path.exists(), "__init__ 只建目录，不得预创建文件"

    store.store(_make_task(name="c1"), RuntimeError("e1"))
    assert store.count() == 1
    store.store(_make_task(name="c2"), RuntimeError("e2"))
    assert store.count() == 2
    assert len(_read_records(dead_letter_path)) == 2, "append 模式，不得覆盖既有条目"


# ═══════════════════════════════════════════════════════════════════════════
# D 组 — 确定性校验错误跳过重试（episode_worker.py::_handle_failure 首个分支）
# ═══════════════════════════════════════════════════════════════════════════


async def test_deterministic_validation_error_skips_retry_and_dead_letters(worker):
    """确定性校验错（graphiti group_id 校验）重试必然复现 ⇒ 直接死信，不空转队列。"""
    w, mock_graphiti, dl = worker
    mock_graphiti.add_episode = AsyncMock(side_effect=GroupIdValidationError("bad:group"))

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep) as slept:
        w.enqueue(_make_task(name="deterministic_error"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    assert mock_graphiti.add_episode.await_count == 1, "确定性错误不得重试"
    assert slept.await_count == 0, "确定性错误不得退避"
    assert w.metrics.episodes_failed == 1
    assert w.metrics.episodes_dead_lettered == 1
    record = _read_records(dl)[0]
    assert record["error_type"] == "GroupIdValidationError"
    assert record["retry_count"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# E 组 — 死信隐私（默认不落全文 / opt-in 落且脱敏 / 错误串脱敏截断）
# ═══════════════════════════════════════════════════════════════════════════


def test_dead_letter_omits_full_body_by_default(dead_letter_path, monkeypatch):
    """默认配置（未设 DEAD_LETTER_STORE_FULL_BODY）不得落未截断的 episode 全文。"""
    monkeypatch.delenv("DEAD_LETTER_STORE_FULL_BODY", raising=False)
    long_body = "学生原文" * 200  # 800 字符，远超 to_dict 的 200 截断
    store = DeadLetterStore(file_path=str(dead_letter_path))
    store.store(_make_task(name="privacy_default", body=long_body), RuntimeError("boom"))

    record = _read_records(dead_letter_path)[0]
    assert "episode_body_full" not in record
    assert record["episode_body"] == long_body[:200]
    assert record["episode_body_length"] == len(long_body)
    assert len(record["episode_body"]) == 200, "截断字段本身不得携带全文"


@pytest.mark.parametrize("flag", ["true", "1", "yes", "on", "TRUE", " Yes "])
def test_dead_letter_stores_redacted_full_body_when_flag_enabled(dead_letter_path, monkeypatch, flag):
    """opt-in 打开后才落全文，且落盘前必须过 _redact。"""
    monkeypatch.setenv("DEAD_LETTER_STORE_FULL_BODY", flag)
    secret = "sk-" + "A" * 30
    body = f"prefix {secret} suffix"
    store = DeadLetterStore(file_path=str(dead_letter_path))
    store.store(_make_task(name="privacy_optin", body=body), RuntimeError("boom"))

    record = _read_records(dead_letter_path)[0]
    assert "episode_body_full" in record, f"flag={flag!r} 应被识别为开启"
    assert record["episode_body_full"] == "prefix ***REDACTED*** suffix"
    assert secret not in record["episode_body_full"]


@pytest.mark.parametrize("flag", ["false", "0", "no", "off", "", "maybe"])
def test_dead_letter_full_body_flag_rejects_non_truthy_values(dead_letter_path, monkeypatch, flag):
    """非真值一律按关闭处理 —— 隐私默认值不得被含糊的环境变量撬开。"""
    monkeypatch.setenv("DEAD_LETTER_STORE_FULL_BODY", flag)
    store = DeadLetterStore(file_path=str(dead_letter_path))
    store.store(_make_task(name="privacy_off", body="x" * 500), RuntimeError("boom"))

    assert "episode_body_full" not in _read_records(dead_letter_path)[0]


def test_dead_letter_error_message_is_redacted_and_truncated(dead_letter_path, monkeypatch):
    """错误串落盘前脱敏并截断到 200 字符（CWE-532：死信是取证外泄的常见落点）。"""
    monkeypatch.delenv("DEAD_LETTER_STORE_FULL_BODY", raising=False)
    secret = "sk-" + "B" * 30
    error = RuntimeError(f"{secret} " + "x" * 300)
    store = DeadLetterStore(file_path=str(dead_letter_path))
    store.store(_make_task(name="err_redact"), error)

    record = _read_records(dead_letter_path)[0]
    # 期望值独立于被测量：手写脱敏后的字面量再截断，不调用 _redact 求值。
    assert record["error"] == ("***REDACTED*** " + "x" * 300)[:200]
    assert len(record["error"]) == 200
    assert secret not in record["error"]


@pytest.mark.parametrize(
    "raw",
    [
        "sk-" + "A" * 25,
        "AIza" + "B" * 25,
        "ghp_" + "C" * 25,
        "Bearer " + "D" * 25,
        "eyJ" + "a" * 20 + "." + "b" * 20 + "." + "c" * 12,
    ],
)
def test_redact_scrubs_known_secret_patterns(raw):
    """_redact 覆盖 OpenAI/Google/GitHub/Bearer/JWT 五类形态。"""
    scrubbed = _redact(f"head {raw} tail")
    assert raw not in scrubbed
    assert "***REDACTED***" in scrubbed
    assert scrubbed.startswith("head ") and scrubbed.endswith(" tail")


def test_redact_is_noop_for_non_strings_and_clean_text():
    """非字符串原样返回；不含密钥形态的文本不得被误伤。"""
    assert _redact(42) == 42
    assert _redact(None) is None
    clean = "退避上界 1/2/4 秒，sk-short 不足 20 位"
    assert _redact(clean) == clean


# ═══════════════════════════════════════════════════════════════════════════
# F 组 — 计数器（承接 TestMemoryServiceDualWriteFailure 的 timeout/exception 计数）
# ═══════════════════════════════════════════════════════════════════════════


async def test_timeout_failures_increment_failure_counter_per_attempt(worker):
    """等价于「dual-write 超时 → 失败计数器递增」：每次失败尝试各记一次。

    ⚠️ 语义迁移（如实声明）：旧实现递增模块级 `dual_write_failures`；现实现递增
    worker 自己的 `WorkerMetrics.episodes_failed`。
    """
    w, mock_graphiti, dl = worker
    mock_graphiti.add_episode = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep):
        w.enqueue(_make_task(name="timeout_counter"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    assert w.metrics.episodes_failed == 4, "4 次尝试全失败，计数器按尝试记"
    assert w.metrics.episodes_dead_lettered == 1, "死信只记一次"
    assert w.metrics.episodes_processed == 0


async def test_exception_failures_increment_failure_counter_per_attempt(worker):
    """等价于「dual-write 异常 → 失败计数器递增」：异常与超时走同一计数口径。"""
    w, mock_graphiti, dl = worker
    attempts = {"n": 0}

    async def fail_then_ok(**kwargs):
        attempts["n"] += 1
        if attempts["n"] <= 2:
            raise RuntimeError("counted failure")

    mock_graphiti.add_episode = AsyncMock(side_effect=fail_then_ok)

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep):
        w.enqueue(_make_task(name="exception_counter"))
        await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    assert w.metrics.episodes_failed == 2
    assert w.metrics.episodes_processed == 1
    assert w.metrics.episodes_dead_lettered == 0


async def test_metrics_snapshot_covers_all_counters(worker):
    """`WorkerMetrics.to_dict()` 的十个字段在一次成功 + 一次死信后各自取到真值。"""
    w, mock_graphiti, dl = worker

    w.enqueue(_make_task(name="metrics_ok"))
    await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError("metrics_fail"))
    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep):
        w.enqueue(_make_task(name="metrics_fail"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    snapshot = w.metrics.to_dict()
    assert set(snapshot) == {
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
    assert snapshot["episodes_enqueued"] == 2
    assert snapshot["episodes_processed"] == 1
    assert snapshot["episodes_failed"] == 4
    assert snapshot["episodes_dead_lettered"] == 1
    assert snapshot["episodes_dropped_queue_full"] == 0
    assert snapshot["worker_running"] is True
    # success_rate = processed / (processed + failed) = 1/5
    assert snapshot["success_rate"] == 0.2


async def test_queue_full_drops_and_counts(dead_letter_path):
    """队列满 ⇒ enqueue 返回 False 且 episodes_dropped_queue_full 递增（不入死信）。"""
    w = GraphitiEpisodeWorker(maxsize=1, dead_letter_path=str(dead_letter_path))

    assert w.enqueue(_make_task(name="fits")) is True
    assert w.enqueue(_make_task(name="overflow")) is False

    assert w.metrics.episodes_enqueued == 1, "被丢弃的不得计入 enqueued"
    assert w.metrics.episodes_dropped_queue_full == 1
    assert w.metrics.queue_depth == 1
    assert not dead_letter_path.exists(), "队列满是丢弃不是死信"


async def test_enqueue_after_stop_returns_false(dead_letter_path):
    """关停后入队被拒（返回 False 而非抛异常），计数不变。"""
    w = GraphitiEpisodeWorker(maxsize=4, dead_letter_path=str(dead_letter_path))
    mock_graphiti = MagicMock()
    mock_graphiti.add_episode = AsyncMock(return_value=None)
    w.set_graphiti_client(mock_graphiti)
    assert w.is_ready is False, "未 start 时 is_ready 必须为 False"
    await w.start()
    assert w.is_ready is True
    await w.stop(timeout=5.0)

    assert w.enqueue(_make_task(name="after_stop")) is False
    assert w.metrics.episodes_enqueued == 0
    assert w.metrics.worker_running is False


# ═══════════════════════════════════════════════════════════════════════════
# G 组 — 日志分级（承接 retry_success / all_retries_failed / first_success_debug
#        / exception_warning_includes_error_message / timeout_suffix 五条）
# ═══════════════════════════════════════════════════════════════════════════


async def test_retry_warning_includes_attempt_number_and_error_message(worker):
    """等价于「失败 warning 含错误消息」：重试 warning 带 attempt i/N 与 str(error)。"""
    w, mock_graphiti, dl = worker
    marker = "epw-error-marker-9f3a"
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError(marker))

    with (
        patch("app.services.episode_worker.logger") as log,
        patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep),
    ):
        w.enqueue(_make_task(name="warn_msg"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)
        warnings = [c.args[0] for c in log.warning.call_args_list]

    assert len(warnings) == 3, f"3 次重试各一条 warning, got {warnings}"
    assert all(marker in m for m in warnings), "warning 必须带错误消息本身"
    assert "attempt 1/3" in warnings[0]
    assert "attempt 3/3" in warnings[2]


async def test_dead_letter_log_carries_error_type_not_error_message(worker):
    """死信 error 日志只带 error_type，不插值原始错误串（CWE-532 防线）。

    这是旧「timeout 后缀」语义的现实现等价物：区分能力从文案后缀迁到 error_type。
    """
    w, mock_graphiti, dl = worker
    secret = "sk-" + "E" * 30
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError(f"leaky {secret}"))

    with (
        patch("app.services.episode_worker.logger") as log,
        patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep),
    ):
        w.enqueue(_make_task(name="log_privacy"))
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)
        errors = [c.args[0] for c in log.error.call_args_list]

    assert len(errors) == 1
    assert "error_type=RuntimeError" in errors[0]
    assert secret not in errors[0], "原始密钥串不得进结构化日志流"
    assert "retries=3/3" in errors[0]


async def test_enqueue_logs_debug_while_success_logs_info(worker):
    """等价于「首次成功只记 debug 不记 info」的现实现口径：入队 debug、处理成功 info。

    ⚠️ 语义收窄（如实声明）：旧口径是「首次成功 vs 重试成功」的分级差异；现 worker
    对两者用同一条 info（`Episode processed`），可区分的分级变成「入队 debug /
    处理完成 info」。本断言按现实现钉。
    """
    w, mock_graphiti, dl = worker

    with patch("app.services.episode_worker.logger") as log:
        w.enqueue(_make_task(name="log_levels"))
        await _wait_until(lambda: w.metrics.episodes_processed >= 1)
        debugs = [c.args[0] for c in log.debug.call_args_list]
        infos = [c.args[0] for c in log.info.call_args_list]

    assert any("Enqueued episode" in m for m in debugs)
    assert not any("Enqueued episode" in m for m in infos), "入队不得升级到 info"
    assert any("Episode processed" in m for m in infos)
    assert log.warning.call_args_list == [], "成功路径不得产生 warning"


# ═══════════════════════════════════════════════════════════════════════════
# H 组 — 可选参数透传（承接 test_with_all_optional_params）
# ═══════════════════════════════════════════════════════════════════════════


async def test_all_optional_params_forwarded_to_add_episode(worker):
    """等价于「所有可选参数都传递」：entity_types / edge_types / source=json 逐项透传。"""
    w, mock_graphiti, dl = worker
    entity_types = {"Concept": object}
    edge_types = {"LEARNED": object}
    task = _make_task(
        name="optional_params",
        entity_types=entity_types,
        edge_types=edge_types,
        source="json",
    )

    w.enqueue(task)
    await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    kwargs = mock_graphiti.add_episode.await_args.kwargs
    assert kwargs["name"] == "optional_params"
    assert kwargs["episode_body"] == _BODY
    assert kwargs["source_description"] == "test_episode_worker_coverage_epw"
    assert kwargs["reference_time"] == task.reference_time
    assert kwargs["entity_types"] is entity_types
    assert kwargs["edge_types"] is edge_types
    # source="json" ⇒ worker 换成 graphiti 的 EpisodeType.json（受控 schema 入图）
    from graphiti_core.nodes import EpisodeType

    assert kwargs["source"] is EpisodeType.json
    # graphiti 侧落影子分组（字面量期望值，不调 semantic_group_id 求值）
    assert kwargs["group_id"] == _EXPECTED_GRAPHITI_GROUP_ID
    assert task.group_id == _GROUP_ID, "影子分组只作用于 graphiti 调用面，不改写 task 归属"


async def test_optional_params_omitted_when_unset(worker):
    """未设置的可选参数不得以 None 形态传给 add_episode（会覆盖 graphiti 默认值）。"""
    w, mock_graphiti, dl = worker

    w.enqueue(_make_task(name="no_optional"))
    await _wait_until(lambda: w.metrics.episodes_processed >= 1)

    kwargs = mock_graphiti.add_episode.await_args.kwargs
    assert "entity_types" not in kwargs
    assert "edge_types" not in kwargs
    assert "source" not in kwargs


# ═══════════════════════════════════════════════════════════════════════════
# I 组 — 重试身份（承接 test_retry_creates_new_timestamp_each_attempt，语义反转）
# ═══════════════════════════════════════════════════════════════════════════


async def test_retry_reuses_same_task_and_preserves_timestamps(worker):
    """⚠️ 语义**反转**（如实声明）。

    旧实现每次重试新建 LearningMemory ⇒ 每次尝试一个新 timestamp；现实现把**同一个**
    `EpisodeTask` 对象重新入队 ⇒ `created_at` / `reference_time` 全程不变，只有
    `retry_count` 递增。死信记录里的 `created_at` 因此是**首次**入队时刻，可用于算端到端
    滞留时长。本用例按现实现钉死，免得后人照旧描述改坏。
    """
    w, mock_graphiti, dl = worker
    mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError("identity"))
    task = _make_task(name="same_object")
    original_created_at = task.created_at
    original_reference_time = task.reference_time

    with patch("app.services.episode_worker.asyncio.sleep", side_effect=_no_sleep):
        w.enqueue(task)
        await _wait_until(lambda: w.metrics.episodes_dead_lettered >= 1)

    assert task.retry_count == 3, "重试次数写在同一个对象上"
    assert task.created_at == original_created_at, "重试不得刷新 created_at"
    assert task.reference_time == original_reference_time, "重试不得刷新 reference_time"

    record = _read_records(dl)[0]
    assert record["created_at"] == original_created_at.isoformat()
    assert record["reference_time"] == original_reference_time.isoformat()
    assert record["retry_count"] == 3
