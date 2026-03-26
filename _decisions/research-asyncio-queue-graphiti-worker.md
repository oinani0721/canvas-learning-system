# Worker Implementation Manual: asyncio.Queue + Graphiti add_episode

> **Research date**: 2026-03-24
> **Python version**: 3.14.3 (Queue.shutdown() available since 3.13)
> **Project**: canvas-learning-system FastAPI backend

---

## 1. FastAPI lifespan 中启动 asyncio.Task 的标准模式

### 标准模式代码

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio
import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ── Startup ──
    worker = GraphitiEpisodeWorker()
    await worker.start()
    app.state.episode_worker = worker
    logger.info("GraphitiEpisodeWorker started")

    yield  # Application runs here

    # ── Shutdown ──
    await worker.stop(timeout=30.0)
    logger.info("GraphitiEpisodeWorker stopped")

app = FastAPI(lifespan=lifespan)
```

### 关键要点

- **必须在 yield 前启动，yield 后停止** -- yield 之间是应用运行期
- **必须保持 task 引用** -- 存到 `app.state` 避免被 GC
- **asyncio.create_task() 必须在 running event loop 中调用** -- lifespan 是 async context，天然满足
- **多 worker 进程（uvicorn --workers N）** -- 每个进程有独立 event loop，各自启动独立 worker

### 已有项目模式参考

项目 `backend/app/main.py` 已经有成熟的 lifespan 模式：`resource_monitor.start_background_collection()`、`alert_manager.start()`、`archive_scheduler.start()` 都遵循相同的 start/yield/stop 范式。新 worker 应遵循同样的模式。

---

## 2. asyncio.Queue maxsize 设置与溢出处理

### 推荐 maxsize

| 场景 | maxsize | 理由 |
|------|---------|------|
| 本项目 (单用户 Obsidian 插件) | **100** | 用户学习事件产生速率低（秒级），add_episode 耗时 5-30s/条，100 条 buffer 足够吸收突发 |
| 高并发 API 服务 | 500-1000 | 需要更大缓冲 |
| 无限制 (maxsize=0) | **禁止** | 内存无上限增长风险 |

### 满队列处理策略

```python
# 策略 A（推荐）: put_nowait + QueueFull 降级
try:
    queue.put_nowait(episode_task)
except asyncio.QueueFull:
    logger.warning(
        f"Episode queue full (size={queue.qsize()}), "
        f"dropping event: {episode_task.name[:50]}"
    )
    # 可选: 写入 JSON fallback 文件
    await _write_to_fallback_file(episode_task)

# 策略 B: await put() 阻塞（不推荐用于 API handler）
# 会阻塞请求处理，导致 HTTP 响应延迟
await queue.put(episode_task)  # blocks until space available

# 策略 C: put with timeout
try:
    await asyncio.wait_for(queue.put(episode_task), timeout=1.0)
except asyncio.TimeoutError:
    logger.warning("Queue put timed out, event dropped")
```

**本项目推荐策略 A**：API handler 中使用 `put_nowait`，满了就降级到 JSON fallback（项目已有 Story 38.4 的 dual-write 机制可复用）。

---

## 3. 优雅关闭（Graceful Shutdown）

### Python 3.13+ Queue.shutdown() 方案（推荐）

```python
async def stop(self, timeout: float = 30.0):
    """Graceful shutdown: drain remaining events then stop."""
    logger.info(f"Shutting down worker, {self._queue.qsize()} events pending...")

    # Step 1: shutdown(immediate=False) -- 停止新 put，允许 get 继续消费
    self._queue.shutdown(immediate=False)

    # Step 2: 等待 worker task 自然结束（消费完剩余 + 收到 QueueShutDown）
    try:
        await asyncio.wait_for(self._worker_task, timeout=timeout)
        logger.info("Worker drained all pending events")
    except asyncio.TimeoutError:
        logger.warning(
            f"Worker drain timed out ({timeout}s), "
            f"{self._queue.qsize()} events lost. Cancelling..."
        )
        self._worker_task.cancel()
        try:
            await self._worker_task
        except asyncio.CancelledError:
            pass

    # Step 3: 记录丢失的事件数（如果有）
    remaining = self._queue.qsize()
    if remaining > 0:
        logger.error(f"Lost {remaining} unprocessed episodes on shutdown")
```

### Worker 侧处理 QueueShutDown

```python
async def _run(self):
    """Worker main loop."""
    while True:
        try:
            task = await self._queue.get()
        except asyncio.QueueShutDown:
            logger.info("Queue shut down, worker exiting")
            break

        try:
            await self._process(task)
        except Exception as e:
            logger.error(f"Episode processing failed: {e}")
            await self._handle_failure(task, e)
        finally:
            self._queue.task_done()
```

### 为什么不用 sentinel 模式

Python 3.13+ 的 `Queue.shutdown()` 是官方推荐的替代方案，比 sentinel (放入 `None` 作为终止信号) 更健壮：
- 自动阻止新的 `put()` 调用
- 正确处理 `join()` 的 unblock
- 不需要约定特殊的 sentinel 值

---

## 4. add_episode 的 sequential await 要求

### graphiti-core 官方文档明确要求

源自 `graphiti_core/graphiti.py` 第 864-867 行的 docstring：

> It is recommended to run this method as a background process, such as in a queue.
> **It's important that each episode is added sequentially and awaited before adding the next one.**
> For web applications, consider using FastAPI's background tasks or a dedicated task queue like Celery for this purpose.

### 为什么必须 sequential

1. **时序图谱一致性** -- add_episode 会查询 `previous_episodes` 做上下文关联，并行会导致前后文关系混乱
2. **实体去重** -- 并行处理同一 group_id 的 episode 会导致重复实体节点
3. **Edge invalidation** -- 时间线上的事实覆盖（如"A的老师是B" -> "A的老师是C"）需要顺序处理才能正确失效旧 edge
4. **Neo4j 事务冲突** -- 并发写入同一子图可能导致 deadlock 或 constraint violation

### graphiti 官方 MCP Server 的实现证据

`getzep/graphiti/mcp_server/src/services/queue_service.py` 使用**每个 group_id 一个独立 asyncio.Queue + 一个 worker task**，确保同一 group_id 内严格顺序：

```python
# 官方实现的核心模式
async def _process_episode_queue(self, group_id: str):
    while True:
        process_func = await self._episode_queues[group_id].get()
        try:
            await process_func()  # 一条条 await，不并行
        except Exception as e:
            logger.error(f"Error processing queued episode for group_id {group_id}: {e}")
        finally:
            self._episode_queues[group_id].task_done()
```

### 本项目的适配

本项目当前只有一个 group_id（`canvas-dev` 或基于 canvas_file），单 worker 即可满足顺序要求。如果未来需要多个 group_id 并行处理（不同 canvas 之间互不影响），可以扩展为 per-group-id worker。

---

## 5. 失败重试策略

### 指数退避 + Dead-Letter 实现

```python
import asyncio
import random
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class EpisodeTask:
    """Queue item wrapping an episode for processing."""
    name: str
    episode_body: str
    group_id: str
    source_description: str
    reference_time: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    @property
    def backoff_seconds(self) -> float:
        """Exponential backoff with full jitter."""
        base = 2 ** self.retry_count  # 1, 2, 4, 8, ...
        cap = min(base, 60)           # cap at 60 seconds
        return random.uniform(0, cap)  # full jitter


class DeadLetterStore:
    """Persistent store for failed episodes that exhausted retries."""

    def __init__(self, file_path: str = "data/dead_letter_episodes.jsonl"):
        self._file_path = file_path

    async def store(self, task: EpisodeTask, error: Exception):
        """Append failed task to JSONL file for later manual inspection."""
        import json, aiofiles

        record = {
            "name": task.name,
            "episode_body": task.episode_body,
            "group_id": task.group_id,
            "source_description": task.source_description,
            "reference_time": task.reference_time.isoformat(),
            "retry_count": task.retry_count,
            "error": str(error),
            "error_type": type(error).__name__,
            "failed_at": datetime.utcnow().isoformat(),
        }

        async with aiofiles.open(self._file_path, mode="a") as f:
            await f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.error(
            f"Dead-lettered episode: name={task.name}, "
            f"retries={task.retry_count}, error={error}"
        )
```

### Worker 中的重试逻辑

```python
async def _process(self, task: EpisodeTask):
    """Process a single episode with retry."""
    try:
        await self._graphiti.add_episode(
            name=task.name,
            episode_body=task.episode_body,
            group_id=task.group_id,
            source_description=task.source_description,
            reference_time=task.reference_time,
        )
        self._metrics.episodes_processed += 1

    except Exception as e:
        self._metrics.episodes_failed += 1

        if task.can_retry:
            task.retry_count += 1
            backoff = task.backoff_seconds
            logger.warning(
                f"Episode failed (attempt {task.retry_count}/{task.max_retries}), "
                f"retrying in {backoff:.1f}s: {e}"
            )
            await asyncio.sleep(backoff)
            # Re-queue at the front (high priority retry)
            # Note: asyncio.Queue has no priority, so we just put it back
            try:
                self._queue.put_nowait(task)
            except asyncio.QueueFull:
                await self._dead_letter.store(task, e)
        else:
            await self._dead_letter.store(task, e)
```

### 重试策略参数

| 参数 | 值 | 理由 |
|------|-----|------|
| max_retries | 3 | add_episode 涉及 LLM 调用，瞬态错误（rate limit、timeout）通常 3 次内恢复 |
| backoff base | 2^n 秒 | 1s, 2s, 4s -- 不会太激进 |
| backoff cap | 60s | 避免指数爆炸 |
| jitter | full jitter (0, cap) | 防止 thundering herd |
| dead-letter format | JSONL 文件 | 可人工审查，startup 时可重放 |

---

## 6. 监控指标

### 指标定义

```python
from dataclasses import dataclass, field
from datetime import datetime
import time

@dataclass
class WorkerMetrics:
    """Episode worker metrics for monitoring."""
    # Counters
    episodes_enqueued: int = 0
    episodes_processed: int = 0
    episodes_failed: int = 0
    episodes_dead_lettered: int = 0
    episodes_dropped_queue_full: int = 0

    # Gauges
    queue_depth: int = 0            # current items in queue
    worker_running: bool = False

    # Latency tracking
    _processing_times: list[float] = field(default_factory=list)
    _last_process_start: float = 0.0

    def record_processing_time(self, seconds: float):
        self._processing_times.append(seconds)
        # Keep last 100 for rolling average
        if len(self._processing_times) > 100:
            self._processing_times = self._processing_times[-100:]

    @property
    def avg_processing_time_ms(self) -> float:
        if not self._processing_times:
            return 0.0
        return (sum(self._processing_times) / len(self._processing_times)) * 1000

    @property
    def max_processing_time_ms(self) -> float:
        if not self._processing_times:
            return 0.0
        return max(self._processing_times) * 1000

    def to_dict(self) -> dict:
        return {
            "episodes_enqueued": self.episodes_enqueued,
            "episodes_processed": self.episodes_processed,
            "episodes_failed": self.episodes_failed,
            "episodes_dead_lettered": self.episodes_dead_lettered,
            "episodes_dropped_queue_full": self.episodes_dropped_queue_full,
            "queue_depth": self.queue_depth,
            "worker_running": self.worker_running,
            "avg_processing_time_ms": round(self.avg_processing_time_ms, 1),
            "max_processing_time_ms": round(self.max_processing_time_ms, 1),
            "success_rate": (
                self.episodes_processed / max(self.episodes_processed + self.episodes_failed, 1)
            ),
        }
```

### 暴露方式

```python
# FastAPI endpoint
@router.get("/api/v1/monitoring/episode-worker")
async def episode_worker_health(request: Request):
    worker = request.app.state.episode_worker
    return worker.metrics.to_dict()
```

不需要 Prometheus -- 项目已有 `/api/v1/monitoring/metrics` 端点和 `MetricsMiddleware`，直接复用 JSON 指标暴露模式。

---

## 7. BackgroundTasks vs asyncio.Queue 对比

| 维度 | FastAPI BackgroundTasks | asyncio.Queue + Worker |
|------|------------------------|----------------------|
| **执行模型** | 每个请求独立 fire-and-forget | 单 worker 顺序消费 |
| **顺序保证** | 无。多请求的 task 可能并行 | 严格 FIFO |
| **背压控制** | 无。无限制产生 task | maxsize 限制 + 降级策略 |
| **失败重试** | 无内置机制 | 可实现指数退避 + dead-letter |
| **监控** | 不可观测 | queue depth、latency、fail rate 全可观测 |
| **优雅关闭** | 无。进程退出时直接丢弃 | drain + timeout + 剩余记录 |
| **内存控制** | task 对象无上限堆积 | maxsize 控制上限 |
| **graphiti 兼容** | **不兼容** -- 无法保证 sequential await | **兼容** -- 天然满足顺序要求 |

### 为什么本项目必须选 asyncio.Queue

1. **graphiti-core 的硬性要求**：`add_episode` 文档明确要求 "each episode is added sequentially and awaited before adding the next one"。`BackgroundTasks` 无法满足此约束，因为多个请求的 background task 会并发执行。

2. **graphiti 官方自己也用 Queue**：`getzep/graphiti/mcp_server` 使用 `asyncio.Queue` + per-group-id worker，而不是 BackgroundTasks。

3. **已知 bug 佐证**：Issue #450 和 #566 中，background processing 导致 100% CPU hang 和 episode 未持久化，根因之一是并发写入冲突。

---

## 8. 完整代码骨架

```python
"""
GraphitiEpisodeWorker - Async queue-based background worker for graphiti add_episode.

Production-ready implementation with:
- asyncio.Queue for sequential episode processing
- Exponential backoff retry with full jitter
- Dead-letter store for exhausted retries
- Graceful shutdown with drain timeout
- Observable metrics (queue depth, latency, failure rate)
- JSON fallback on queue full

References:
- graphiti-core docstring: "each episode is added sequentially and awaited"
- getzep/graphiti mcp_server/src/services/queue_service.py (official pattern)
- Python 3.13+ asyncio.Queue.shutdown() for graceful termination

Author: Canvas Learning System
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EpisodeTask:
    """A unit of work for the episode processing queue."""
    name: str
    episode_body: str
    group_id: str
    source_description: str
    reference_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    @property
    def backoff_seconds(self) -> float:
        """Exponential backoff with full jitter. Cap at 60s."""
        base = 2 ** self.retry_count
        cap = min(base, 60)
        return random.uniform(0, cap)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "episode_body": self.episode_body[:200],  # truncate for logging
            "group_id": self.group_id,
            "source_description": self.source_description,
            "reference_time": self.reference_time.isoformat(),
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class WorkerMetrics:
    """Observable metrics for the episode worker."""
    episodes_enqueued: int = 0
    episodes_processed: int = 0
    episodes_failed: int = 0
    episodes_dead_lettered: int = 0
    episodes_dropped_queue_full: int = 0
    queue_depth: int = 0
    worker_running: bool = False
    _processing_times: list[float] = field(default_factory=list)

    def record_processing_time(self, seconds: float):
        self._processing_times.append(seconds)
        if len(self._processing_times) > 100:
            self._processing_times = self._processing_times[-100:]

    @property
    def avg_processing_time_ms(self) -> float:
        if not self._processing_times:
            return 0.0
        return (sum(self._processing_times) / len(self._processing_times)) * 1000

    @property
    def max_processing_time_ms(self) -> float:
        if not self._processing_times:
            return 0.0
        return max(self._processing_times) * 1000

    def to_dict(self) -> dict[str, Any]:
        total = self.episodes_processed + self.episodes_failed
        return {
            "episodes_enqueued": self.episodes_enqueued,
            "episodes_processed": self.episodes_processed,
            "episodes_failed": self.episodes_failed,
            "episodes_dead_lettered": self.episodes_dead_lettered,
            "episodes_dropped_queue_full": self.episodes_dropped_queue_full,
            "queue_depth": self.queue_depth,
            "worker_running": self.worker_running,
            "avg_processing_time_ms": round(self.avg_processing_time_ms, 1),
            "max_processing_time_ms": round(self.max_processing_time_ms, 1),
            "success_rate": round(self.episodes_processed / max(total, 1), 3),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Dead Letter Store
# ═══════════════════════════════════════════════════════════════════════════════

class DeadLetterStore:
    """Persists failed episodes to JSONL for manual inspection and replay."""

    def __init__(self, file_path: str = "data/dead_letter_episodes.jsonl"):
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    async def store(self, task: EpisodeTask, error: Exception):
        record = {
            **task.to_dict(),
            "episode_body_full": task.episode_body,  # full content for replay
            "error": str(error),
            "error_type": type(error).__name__,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        # Synchronous file write (tiny payload, acceptable)
        with open(self._file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.error(
            f"Dead-lettered episode: name={task.name}, "
            f"retries={task.retry_count}/{task.max_retries}, error={error}"
        )

    def count(self) -> int:
        if not self._file_path.exists():
            return 0
        with open(self._file_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)


# ═══════════════════════════════════════════════════════════════════════════════
# GraphitiEpisodeWorker
# ═══════════════════════════════════════════════════════════════════════════════

class GraphitiEpisodeWorker:
    """
    Async background worker for sequential graphiti add_episode processing.

    Architecture:
        API handler --put_nowait--> asyncio.Queue --get--> Worker --await--> graphiti.add_episode()
                                     (maxsize=100)       (single task)      (sequential, 5-30s each)

    Usage in FastAPI lifespan:
        worker = GraphitiEpisodeWorker(graphiti_instance)
        await worker.start()
        app.state.episode_worker = worker
        ...
        await worker.stop(timeout=30.0)

    Usage in API handler:
        worker = request.app.state.episode_worker
        worker.enqueue(EpisodeTask(name=..., episode_body=..., group_id=...))
    """

    def __init__(
        self,
        graphiti_client: Any = None,
        maxsize: int = 100,
        dead_letter_path: str = "data/dead_letter_episodes.jsonl",
    ):
        self._graphiti = graphiti_client
        self._queue: asyncio.Queue[EpisodeTask] = asyncio.Queue(maxsize=maxsize)
        self._worker_task: Optional[asyncio.Task] = None
        self._dead_letter = DeadLetterStore(dead_letter_path)
        self._metrics = WorkerMetrics()
        self._started = False

    # ── Public API ──

    def set_graphiti_client(self, client: Any):
        """Set or replace the graphiti client (useful for lazy initialization)."""
        self._graphiti = client

    async def start(self):
        """Start the background worker task."""
        if self._started:
            logger.warning("GraphitiEpisodeWorker already started")
            return

        self._worker_task = asyncio.create_task(
            self._run(), name="graphiti-episode-worker"
        )
        self._started = True
        self._metrics.worker_running = True
        logger.info(f"GraphitiEpisodeWorker started (maxsize={self._queue.maxsize})")

    async def stop(self, timeout: float = 30.0):
        """
        Graceful shutdown: drain remaining events, then stop.

        Uses Python 3.13+ Queue.shutdown() for clean termination.
        """
        if not self._started:
            return

        pending = self._queue.qsize()
        logger.info(f"Stopping GraphitiEpisodeWorker, {pending} events pending...")

        # Step 1: Signal queue shutdown (no more puts, gets continue)
        self._queue.shutdown(immediate=False)

        # Step 2: Wait for worker to drain and exit
        if self._worker_task is not None:
            try:
                await asyncio.wait_for(self._worker_task, timeout=timeout)
                logger.info("GraphitiEpisodeWorker drained and stopped cleanly")
            except asyncio.TimeoutError:
                remaining = self._queue.qsize()
                logger.warning(
                    f"Worker drain timed out ({timeout}s), "
                    f"{remaining} events will be lost. Force cancelling..."
                )
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass

        self._started = False
        self._metrics.worker_running = False

    def enqueue(self, task: EpisodeTask) -> bool:
        """
        Enqueue an episode for background processing.

        Non-blocking. Returns False if queue is full (event dropped).
        Caller should handle the False return (e.g., log, fallback).
        """
        try:
            self._queue.put_nowait(task)
            self._metrics.episodes_enqueued += 1
            self._metrics.queue_depth = self._queue.qsize()
            logger.debug(
                f"Enqueued episode: name={task.name[:50]}, "
                f"queue_depth={self._queue.qsize()}"
            )
            return True
        except asyncio.QueueFull:
            self._metrics.episodes_dropped_queue_full += 1
            logger.warning(
                f"Episode queue full (maxsize={self._queue.maxsize}), "
                f"dropping: {task.name[:50]}"
            )
            return False
        except asyncio.QueueShutDown:
            logger.warning(
                f"Episode queue shut down, cannot enqueue: {task.name[:50]}"
            )
            return False

    @property
    def metrics(self) -> WorkerMetrics:
        """Current worker metrics (read-only snapshot)."""
        self._metrics.queue_depth = self._queue.qsize()
        return self._metrics

    # ── Internal ──

    async def _run(self):
        """Worker main loop: sequential episode processing."""
        logger.info("Worker loop started")

        while True:
            try:
                task = await self._queue.get()
            except asyncio.QueueShutDown:
                logger.info("Queue shut down signal received, worker exiting")
                break

            start = time.perf_counter()
            try:
                await self._process_episode(task)
                elapsed = time.perf_counter() - start
                self._metrics.episodes_processed += 1
                self._metrics.record_processing_time(elapsed)
                logger.info(
                    f"Episode processed: name={task.name[:50]}, "
                    f"took={elapsed*1000:.0f}ms"
                )
            except Exception as e:
                elapsed = time.perf_counter() - start
                self._metrics.episodes_failed += 1
                self._metrics.record_processing_time(elapsed)
                await self._handle_failure(task, e)
            finally:
                self._queue.task_done()
                self._metrics.queue_depth = self._queue.qsize()

        logger.info("Worker loop exited")

    async def _process_episode(self, task: EpisodeTask):
        """Call graphiti add_episode for a single task."""
        if self._graphiti is None:
            raise RuntimeError("Graphiti client not initialized")

        await self._graphiti.add_episode(
            name=task.name,
            episode_body=task.episode_body,
            group_id=task.group_id,
            source_description=task.source_description,
            reference_time=task.reference_time,
        )

    async def _handle_failure(self, task: EpisodeTask, error: Exception):
        """Handle a failed episode: retry with backoff or dead-letter."""
        if task.can_retry:
            task.retry_count += 1
            backoff = task.backoff_seconds
            logger.warning(
                f"Episode failed (attempt {task.retry_count}/{task.max_retries}), "
                f"retrying in {backoff:.1f}s: {error}"
            )
            await asyncio.sleep(backoff)
            try:
                self._queue.put_nowait(task)
            except (asyncio.QueueFull, asyncio.QueueShutDown):
                # Cannot re-queue: dead-letter it
                self._metrics.episodes_dead_lettered += 1
                await self._dead_letter.store(task, error)
        else:
            self._metrics.episodes_dead_lettered += 1
            await self._dead_letter.store(task, error)


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton accessor (consistent with project pattern)
# ═══════════════════════════════════════════════════════════════════════════════

_worker_instance: Optional[GraphitiEpisodeWorker] = None


def get_episode_worker() -> GraphitiEpisodeWorker:
    """Get or create the singleton GraphitiEpisodeWorker instance."""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = GraphitiEpisodeWorker()
    return _worker_instance


async def cleanup_episode_worker():
    """Cleanup the singleton worker instance (for shutdown)."""
    global _worker_instance
    if _worker_instance is not None:
        await _worker_instance.stop(timeout=30.0)
        _worker_instance = None
```

### FastAPI lifespan 集成点

```python
# 在 backend/app/main.py 的 lifespan 函数中添加:

# ── Startup (在 yield 之前) ──
from app.services.episode_worker import get_episode_worker, cleanup_episode_worker

episode_worker = get_episode_worker()
# 延迟设置 graphiti client（因为 graphiti 可能还没初始化）
try:
    from app.services.memory_service import get_memory_service
    memory_svc = await get_memory_service()
    if hasattr(memory_svc, '_graphiti_instance'):
        episode_worker.set_graphiti_client(memory_svc._graphiti_instance)
except Exception as e:
    logger.warning(f"Episode worker graphiti client not available yet: {e}")

await episode_worker.start()
app.state.episode_worker = episode_worker
logger.info("GraphitiEpisodeWorker started")

# ── Shutdown (在 yield 之后) ──
await cleanup_episode_worker()
logger.info("GraphitiEpisodeWorker stopped")
```

### API Handler 使用示例

```python
from fastapi import APIRouter, Request
from app.services.episode_worker import EpisodeTask

router = APIRouter()

@router.post("/api/v1/learning/events")
async def record_learning_event(request: Request, event: LearningEventInput):
    worker: GraphitiEpisodeWorker = request.app.state.episode_worker

    task = EpisodeTask(
        name=f"learning:{event.event_type}",
        episode_body=event.to_episode_body(),
        group_id=event.canvas_file or "default",
        source_description=f"canvas_learning:{event.canvas_file}",
    )

    success = worker.enqueue(task)
    if not success:
        # Queue full: write to JSON fallback (Story 38.4 dual-write)
        logger.warning("Episode queue full, using fallback")

    return {
        "status": "accepted",
        "queued": success,
        "queue_depth": worker.metrics.queue_depth,
    }


@router.get("/api/v1/monitoring/episode-worker")
async def episode_worker_health(request: Request):
    worker: GraphitiEpisodeWorker = request.app.state.episode_worker
    return worker.metrics.to_dict()
```

---

## 生产级参考项目

| 项目 | 模式 | URL |
|------|------|-----|
| getzep/graphiti mcp_server | per-group-id asyncio.Queue + worker task | [queue_service.py](https://github.com/getzep/graphiti/blob/main/mcp_server/src/services/queue_service.py) |
| greed2411/fastapi_ws_producer_consumer | asyncio.Queue producer-consumer with WebSocket | [GitHub](https://github.com/greed2411/fastapi_ws_producer_consumer) |
| GoodManWEN/fastapi-queue | Redis-backed task queue for peak shaving | [GitHub](https://github.com/GoodManWEN/fastapi-queue) |
| Saeed Hajebi's Graphiti wrapper | Decoupled FastAPI service wrapping graphiti for stability | [Medium article](https://medium.com/@saeedhajebi/a-production-ready-api-for-graphitis-powerful-but-flawed-memory-15f17a9c1b41) |

---

## Sources

- [FastAPI Background Tasks docs](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI lifespan events](https://dev.turmansolutions.ai/2025/09/27/understanding-fastapis-lifespan-events-proper-initialization-and-shutdown/)
- [John Sturgeon: FastAPI FIFO Queue with asyncio.Queue](https://johnsturgeon.me/2022/12/10/fastapi-writing-a-fifo-queue-with-asyncioqueue/)
- [Python asyncio.Queue docs](https://docs.python.org/3/library/asyncio-queue.html)
- [Graceful Shutdowns with asyncio (roguelynn)](https://roguelynn.com/words/asyncio-graceful-shutdowns/)
- [graphiti-core PyPI](https://pypi.org/project/graphiti-core/)
- [graphiti Issue #450: 100% CPU hang on add_episode](https://github.com/getzep/graphiti/issues/450)
- [graphiti Issue #566: 202 but no persistence](https://github.com/getzep/graphiti/issues/566)
- [graphiti Issue #787: Rate limit even with SEMAPHORE_LIMIT=1](https://github.com/getzep/graphiti/issues/787)
- [graphiti DeepWiki: Core Client](https://deepwiki.com/getzep/graphiti/4.1-graphiti-core)
- [Saeed Hajebi: Production-Ready API for Graphiti](https://medium.com/@saeedhajebi/a-production-ready-api-for-graphitis-powerful-but-flawed-memory-15f17a9c1b41)
- [FastAPI Discussion #10743: Alternative to BackgroundTasks](https://github.com/fastapi/fastapi/discussions/10743)
- [Queue-Based Exponential Backoff pattern](https://dev.to/andreparis/queue-based-exponential-backoff-a-resilient-retry-pattern-for-distributed-systems-37f3)
- [Tenacity retry library](https://tenacity.readthedocs.io/)
- [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
