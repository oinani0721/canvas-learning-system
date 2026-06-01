"""
GraphitiEpisodeWorker - Async queue-based background worker for graphiti add_episode.

Production-ready implementation with:
- asyncio.Queue for sequential episode processing
- Exponential backoff retry with full jitter
- Dead-letter store for exhausted retries
- Graceful shutdown with drain timeout
- Observable metrics (queue depth, latency, failure rate)

References:
- graphiti-core docstring: "each episode is added sequentially and awaited"
- getzep/graphiti mcp_server/src/services/queue_service.py (official pattern)
- Python 3.13+ asyncio.Queue.shutdown() for graceful termination

Author: Canvas Learning System
"""

import asyncio
import hashlib
import json
import logging
import os
import re

import structlog
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from graphiti_core import Graphiti

logger = structlog.get_logger(__name__)


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
    entity_types: dict[str, Any] | None = field(default=None)
    edge_types: dict[str, Any] | None = field(default=None)
    request_id: str | None = field(default=None)

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    @property
    def backoff_seconds(self) -> float:
        """Exponential backoff with full jitter. Cap at 60s."""
        base = 2**self.retry_count
        cap = min(base, 60)
        return random.uniform(0, cap)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "episode_body": self.episode_body[:200],  # truncate for logging
            "group_id": self.group_id,
            "source_description": self.source_description,
            "reference_time": self.reference_time.isoformat(),
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
        }
        if self.request_id is not None:
            result["request_id"] = self.request_id
        # Log type names only (type references are not JSON-serializable)
        if self.entity_types:
            result["entity_type_names"] = list(self.entity_types.keys())
        if self.edge_types:
            result["edge_type_names"] = list(self.edge_types.keys())
        return result


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

    def record_processing_time(self, seconds: float) -> None:
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


# audit-2026-04-07/p1-1: secret patterns we redact from any string before
# it lands on disk. Defense in depth — even if upstream callers think they're
# sending sanitized data, the dead-letter file is the last stop and a common
# place for forensic exfiltration. CWE-532 (Insertion of Sensitive Information
# into Log File). Patterns mirror common LLM/cloud key formats.
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),  # OpenAI/Anthropic
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),  # Google
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),  # GitHub
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),  # JWT
)


def _redact(text: str) -> str:
    """Replace secret-looking substrings with ***REDACTED***. No-op for non-strings."""
    if not isinstance(text, str):
        return text
    result = text
    for pat in _SECRET_PATTERNS:
        result = pat.sub("***REDACTED***", result)
    return result


class DeadLetterStore:
    """Persists failed episodes to JSONL for manual inspection and replay.

    audit-2026-04-07/p1-1: privacy-by-default rewrite.

    Previously this stored the full ``episode_body`` plaintext on every failure,
    which means all content the LLM saw — including potentially PII, student
    answers, system prompts containing instructions, and the rare leaked
    credential — was permanently archived in ``data/dead_letter_episodes.jsonl``.
    Combined with the file being committed to git in some failure modes, this
    is a CWE-532 vector.

    New default behavior:
      - Always store ``episode_body_sha256`` (16-byte hex prefix) so replays can
        verify content matches without revealing it.
      - Only store ``episode_body_full`` when env ``DEAD_LETTER_STORE_FULL_BODY``
        is set to ``true`` / ``1`` / ``yes`` (opt-in for debugging).
      - When stored, the full body is run through ``_redact`` to scrub obvious
        secret patterns (OpenAI/Google/GitHub/Bearer/JWT).
      - Error messages are truncated to 200 chars and redacted.
      - Logger.error no longer interpolates the raw error string — only the
        type name — so accidentally-leaked secrets in exception messages don't
        end up in the structured log stream either.
    """

    def __init__(self, file_path: str = "data/dead_letter_episodes.jsonl") -> None:
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _store_full_body_enabled() -> bool:
        flag = (os.environ.get("DEAD_LETTER_STORE_FULL_BODY") or "").strip().lower()
        return flag in ("1", "true", "yes", "on")

    def store(
        self, task: EpisodeTask, error: Exception, *, request_id: str | None = None
    ) -> None:
        """Append failed task to JSONL file synchronously (tiny payload, acceptable).

        Privacy: episode_body_full is omitted unless DEAD_LETTER_STORE_FULL_BODY=true.
        """
        # Always: hash + minimal metadata (safe to keep forever)
        body_bytes = task.episode_body.encode("utf-8", errors="replace")
        body_hash = hashlib.sha256(body_bytes).hexdigest()

        record = {
            **task.to_dict(),
            "episode_body_sha256": body_hash,
            "episode_body_length": len(task.episode_body),
            "error": _redact(str(error))[:200],
            "error_type": type(error).__name__,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Opt-in: full body (still redacted for known secret patterns)
        if self._store_full_body_enabled():
            record["episode_body_full"] = _redact(task.episode_body)

        if request_id is not None:
            record["request_id"] = request_id

        with open(self._file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # audit-2026-04-07/p1-1: scrub error from logger interpolation. Type
        # name only — full message is in the JSONL record (already redacted).
        logger.error(
            f"Dead-lettered episode: name={task.name}, "
            f"retries={task.retry_count}/{task.max_retries}, "
            f"error_type={type(error).__name__}, "
            f"sha256={body_hash[:16]}"
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
        worker = GraphitiEpisodeWorker()
        await worker.initialize_graphiti(neo4j_uri, neo4j_user, neo4j_password, google_api_key)
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
        maxsize: int = 100,
        dead_letter_path: str = "data/dead_letter_episodes.jsonl",
    ) -> None:
        self._graphiti: Optional[Graphiti] = None
        self._queue: asyncio.Queue[EpisodeTask] = asyncio.Queue(maxsize=maxsize)
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._dead_letter = DeadLetterStore(dead_letter_path)
        self._metrics = WorkerMetrics()
        self._started = False

    # ── Initialization ──

    async def initialize_graphiti(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        google_api_key: str,
        llm_model: str = "gemini-2.5-flash",
    ) -> bool:
        """
        Create Graphiti instance with GeminiClient + GeminiEmbedder and build indices.

        Sets os.environ GOOGLE_API_KEY so the Gemini SDK can find it.
        Returns True on success, False if degraded (worker runs but skips episodes).

        ⚠️ CRITICAL: Pre-flight Neo4j connectivity probe MUST run BEFORE Graphiti(...)
        instantiation. graphiti-core v0.28.2's Neo4jDriver.__init__ contains a
        fire-and-forget asyncio task that triggers an unawaited
        build_indices_and_constraints() coroutine on construction:

            # graphiti_core/driver/neo4j_driver.py:91-101
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.build_indices_and_constraints())  # L98 - LEAKED
            except RuntimeError:
                pass

        The created task reference is never stored, no done-callback is attached,
        and no exception handler wraps it. If Neo4j is unreachable, the task raises
        ServiceUnavailable inside the loop and Python emits
        "Task exception was never retrieved" warnings. We cannot patch graphiti-core
        (pinned 0.28.2). The only safe approach is: probe connectivity with a bare
        neo4j AsyncDriver first, and only instantiate Graphiti(...) after the probe
        succeeds. If the probe fails we never construct Graphiti, so the leaked task
        never starts.
        """
        # Pre-flight: bare-driver Neo4j reachability probe (no graphiti-core involved).
        # ✅ Verified pattern: neo4j-python-driver verify_connectivity() probe.
        # Reference: graphiti_core/driver/neo4j_driver.py:98 (fire-and-forget bug)
        from neo4j import (
            AsyncGraphDatabase,
        )  # local import: avoid module-load side effects
        from neo4j.exceptions import AuthError, ServiceUnavailable

        temp_driver = None
        try:
            temp_driver = AsyncGraphDatabase.driver(
                uri=neo4j_uri,
                auth=(neo4j_user or "", neo4j_password or ""),
            )
            await asyncio.wait_for(temp_driver.verify_connectivity(), timeout=5.0)
            logger.info(
                "GraphitiEpisodeWorker: Neo4j pre-flight ok "
                f"(uri={neo4j_uri}, db=neo4j)"
            )
        except (ServiceUnavailable, AuthError, asyncio.TimeoutError, OSError) as e:
            logger.error(
                "GraphitiEpisodeWorker: Neo4j pre-flight failed "
                f"({type(e).__name__}: {e}). "
                "Skipping Graphiti instantiation to avoid graphiti-core "
                "fire-and-forget task leak (neo4j_driver.py:98). "
                "Worker will run in degraded mode."
            )
            self._graphiti = None
            return False
        finally:
            if temp_driver is not None:
                try:
                    await temp_driver.close()
                except Exception as close_err:  # noqa: BLE001
                    logger.debug(f"temp_driver.close() best-effort: {close_err}")

        # Pre-flight passed → safe to instantiate Graphiti (existing logic below)
        try:
            # Make API key available to Gemini SDK
            os.environ.setdefault("GOOGLE_API_KEY", google_api_key)
            # Control graphiti-core internal concurrency (some operations use global env)
            os.environ["SEMAPHORE_LIMIT"] = "3"

            from graphiti_core.cross_encoder.gemini_reranker_client import (
                GeminiRerankerClient,
            )
            from graphiti_core.embedder.gemini import (
                GeminiEmbedder,
                GeminiEmbedderConfig,
            )
            from graphiti_core.llm_client.config import LLMConfig
            from graphiti_core.llm_client.gemini_client import GeminiClient

            llm_config = LLMConfig(api_key=google_api_key, model=llm_model)

            llm_client = GeminiClient(config=llm_config)
            embedder = GeminiEmbedder(
                config=GeminiEmbedderConfig(
                    api_key=google_api_key,
                    embedding_model="gemini-embedding-001",
                )
            )
            cross_encoder = GeminiRerankerClient(config=llm_config)

            # Safe: pre-flight passed, Neo4j is reachable. graphiti-core's L98
            # leaked task will still fire, but build_indices_and_constraints will
            # succeed instead of raising, so no "Task exception never retrieved".
            self._graphiti = Graphiti(
                uri=neo4j_uri,
                user=neo4j_user,
                password=neo4j_password,
                llm_client=llm_client,
                embedder=embedder,
                cross_encoder=cross_encoder,
                max_coroutines=3,
            )

            await self._graphiti.build_indices_and_constraints()
            logger.info(
                f"GraphitiEpisodeWorker: Graphiti initialized "
                f"(neo4j={neo4j_uri}, model={llm_model})"
            )
            return True

        except Exception as e:
            logger.error(
                f"GraphitiEpisodeWorker: Failed to initialize Graphiti client: {e}. "
                f"Worker will run in degraded mode (episodes will be dead-lettered)."
            )
            self._graphiti = None
            return False

    # ── Public API ──

    def set_graphiti_client(self, client: Graphiti) -> None:
        """Set or replace the graphiti client (useful for lazy initialization)."""
        self._graphiti = client

    async def start(self) -> None:
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

    async def stop(self, timeout: float = 30.0) -> None:
        """
        Graceful shutdown: drain remaining events, then stop.

        Uses Python 3.13+ Queue.shutdown() for clean termination.
        """
        if not self._started:
            return

        pending = self._queue.qsize()
        logger.info(f"Stopping GraphitiEpisodeWorker, {pending} events pending...")

        # Step 1: Signal queue shutdown (no more puts, gets continue until empty)
        self._queue.shutdown(immediate=False)

        # Step 2: Wait for worker to drain and exit naturally
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

        Non-blocking. Returns False if queue is full or shut down (event dropped).
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
            logger.warning(f"Episode queue shut down, cannot enqueue: {task.name[:50]}")
            return False

    @property
    def metrics(self) -> WorkerMetrics:
        """Current worker metrics (read-only snapshot with updated queue_depth)."""
        self._metrics.queue_depth = self._queue.qsize()
        return self._metrics

    @property
    def is_ready(self) -> bool:
        """True if worker is started AND graphiti client is initialized."""
        return self._started and self._graphiti is not None

    # ── Internal ──

    async def _run(self) -> None:
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
                    f"took={elapsed * 1000:.0f}ms"
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

    async def _process_episode(self, task: EpisodeTask) -> None:
        """Call graphiti add_episode for a single task."""
        if self._graphiti is None:
            raise RuntimeError("Graphiti client not initialized")

        # P0-5 (2026-05-14): Canvas D16 group_id 用冒号分隔 (vault:cs_61b:subj),
        # 但 Graphiti 上游 validator 拒绝冒号。在 Graphiti 边界 sanitize 为
        # 双下划线分隔形式 (vault__cs_61b__subj)，Canvas 业务逻辑保持 D16 不变。
        from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti

        kwargs: dict[str, Any] = {
            "name": task.name,
            "episode_body": task.episode_body,
            "group_id": sanitize_group_id_for_graphiti(task.group_id),
            "source_description": task.source_description,
            "reference_time": task.reference_time,
        }
        if task.entity_types is not None:
            kwargs["entity_types"] = task.entity_types
        if task.edge_types is not None:
            kwargs["edge_types"] = task.edge_types

        await self._graphiti.add_episode(**kwargs)

    async def _handle_failure(self, task: EpisodeTask, error: Exception) -> None:
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
                self._dead_letter.store(task, error)
        else:
            self._metrics.episodes_dead_lettered += 1
            self._dead_letter.store(task, error)


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


async def cleanup_episode_worker() -> None:
    """Cleanup the singleton worker instance (for shutdown)."""
    global _worker_instance
    if _worker_instance is not None:
        await _worker_instance.stop(timeout=30.0)
        _worker_instance = None
