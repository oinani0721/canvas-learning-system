# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
"""
Canvas Service - Business logic for Canvas operations.

This service provides async methods for Canvas file operations,
wrapping the core canvas_utils.py functionality with async support.

Story 30.5: Canvas CRUD Operations Memory Trigger
- AC-30.5.1: node_created event on node creation
- AC-30.5.2: edge_created event on edge creation
- AC-30.5.3: node_updated event on node update

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
[Source: docs/stories/30.5.story.md]
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.core.exceptions import (
    CanvasNotFoundException,
    NodeNotFoundException,
    ValidationError,
)
from app.models.canvas_events import CanvasEventContext, CanvasEventType

if TYPE_CHECKING:
    from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class CanvasService:
    """
    Canvas business logic service.

    Provides async methods for Canvas CRUD operations and node/edge management.
    Uses asyncio.to_thread for I/O operations to maintain async compatibility.

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    """

    def __init__(
        self,
        canvas_base_path: str = None,
        memory_client: Optional[MemoryService] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize CanvasService.

        Args:
            canvas_base_path: Base path for Canvas files (positional or keyword)
            memory_client: Optional MemoryService for temporal event storage (Story 30.5)
            session_id: Optional session ID for event tracking (defaults to generated UUID)

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        [Source: docs/stories/30.5.story.md#Task-2.1]
        """
        self.canvas_base_path = canvas_base_path or "./"
        self._initialized = True
        # Story 12.H.1: Concurrency locks for write operations
        # Per-canvas locks prevent race conditions during concurrent writes
        self._write_locks: Dict[str, asyncio.Lock] = {}
        self._locks_lock = asyncio.Lock()  # Protects _write_locks dictionary

        # Story 30.5: Memory client for temporal event triggers
        self._memory_client: Optional[MemoryService] = memory_client
        self._session_id = session_id or str(uuid.uuid4())

        # Story 38.5: JSON fallback for Canvas events when memory system unavailable
        self._fallback_file_path: Path = Path(__file__).parent.parent / "data" / "canvas_events_fallback.json"
        self._max_fallback_events: int = 10000
        # [Review H1/M1] Initialize count from existing fallback file for cross-restart persistence
        self._fallback_count: int = self._read_existing_fallback_count()

        logger.debug(f"CanvasService initialized with base_path: {canvas_base_path}")

    @property
    def is_fallback_active(self) -> bool:
        """Story 38.5 AC-3: Track whether Canvas events are in degraded (fallback) mode."""
        return self._fallback_count > 0

    def _read_existing_fallback_count(self) -> int:
        """[Review M1] Read existing fallback event count for cross-restart persistence."""
        try:
            if self._fallback_file_path.exists():
                content = self._fallback_file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                events = data if isinstance(data, list) else data.get("events", [])
                return len(events)
        except (json.JSONDecodeError, OSError):
            pass
        return 0

    def _write_canvas_event_fallback(
        self,
        event_type: str,
        canvas_name: str,
        node_id: Optional[str] = None,
        edge_id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Write Canvas event to JSON fallback file.

        Story 38.5 AC-1/AC-2: When memory system is unavailable, persist events
        to a local JSON file for later recovery.

        Args:
            event_type: Event type string (e.g., "node_created", "edge_sync")
            canvas_name: Canvas name or path
            node_id: Node ID (for node events)
            edge_id: Edge ID (for edge events)
            **kwargs: Additional event metadata (from_node_id, to_node_id, etc.)
        """
        try:
            event = {
                "event_type": event_type,
                "canvas_name": canvas_name,
                "node_id": node_id,
                "edge_id": edge_id,
                "timestamp": datetime.now().isoformat(),
                "session_id": self._session_id,
                **kwargs
            }

            # Read existing events or create new list
            events: List[Dict[str, Any]] = []
            if self._fallback_file_path.exists():
                try:
                    content = self._fallback_file_path.read_text(encoding="utf-8")
                    data = json.loads(content)
                    events = data if isinstance(data, list) else data.get("events", [])
                except (json.JSONDecodeError, KeyError):
                    events = []

            events.append(event)

            # [Review M2] Truncate oldest events when exceeding max limit
            if len(events) > self._max_fallback_events:
                events = events[-self._max_fallback_events:]

            # Ensure parent directory exists
            self._fallback_file_path.parent.mkdir(parents=True, exist_ok=True)

            self._fallback_file_path.write_text(
                json.dumps(events, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            self._fallback_count += 1

        except Exception as e:
            logger.error(f"Failed to write canvas event fallback: {e}")

    def _validate_canvas_name(self, canvas_name: str) -> None:
        """
        Validate canvas name to prevent path traversal attacks.
        Allows subdirectory paths (/) but blocks dangerous patterns.

        Args:
            canvas_name: Canvas name to validate (can include subdirectories like "笔记库/子目录/test")

        Raises:
            ValidationError: If canvas name contains dangerous path traversal patterns
        """
        # Block absolute paths
        if canvas_name.startswith('/'):
            raise ValidationError(f"Absolute path not allowed: {canvas_name}")

        # Block dangerous patterns
        dangerous_patterns = ['..', '\\', '\0', '//', '/./']
        for pattern in dangerous_patterns:
            if pattern in canvas_name:
                raise ValidationError(f"Invalid canvas path: {canvas_name}")

    def _get_canvas_path(self, canvas_name: str) -> Path:
        """Get full path to canvas file.

        Normalizes canvas_name by removing common extensions (.canvas, .md)
        to prevent path construction errors like "file.md.canvas".

        [Source: Story 12.A.1 - AC 3: CanvasService 路径处理支持多种输入格式]
        """
        self._validate_canvas_name(canvas_name)
        # ✅ FIX Story 12.A.1: Normalize canvas_name by removing .canvas OR .md extension
        # This handles:
        #   - "Canvas/Math53/Lecture5" (standard format)
        #   - "Canvas/Math53/Lecture5.canvas" (with .canvas extension)
        #   - "KP13-线性逼近与微分.md" (incorrect .md extension from Obsidian)
        normalized_name = canvas_name.removesuffix('.canvas').removesuffix('.md')
        logger.debug(f"Canvas path normalized: '{canvas_name}' -> '{normalized_name}'")
        return Path(self.canvas_base_path) / f"{normalized_name}.canvas"

    async def _get_lock(self, canvas_name: str) -> asyncio.Lock:
        """
        Get write lock for a specific Canvas file (thread-safe).

        Story 12.H.1: Per-canvas locking prevents race conditions.
        Uses a secondary lock (_locks_lock) to protect the locks dictionary.

        Args:
            canvas_name: Canvas file name to get lock for

        Returns:
            asyncio.Lock for the specified canvas

        [Source: Python asyncio.Lock documentation - async context manager]
        """
        async with self._locks_lock:
            if canvas_name not in self._write_locks:
                self._write_locks[canvas_name] = asyncio.Lock()
                logger.debug(f"Created new write lock for canvas: {canvas_name}")
            return self._write_locks[canvas_name]

    async def _trigger_memory_event(
        self,
        event_type: CanvasEventType,
        canvas_name: str,
        node_id: Optional[str] = None,
        edge_id: Optional[str] = None,
        node_data: Optional[Dict[str, Any]] = None,
        edge_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Trigger memory event asynchronously (fire-and-forget).

        Story 30.5: Non-blocking memory write pattern.
        Uses asyncio.create_task() for fire-and-forget execution.
        Does NOT block the CRUD operation waiting for memory write.

        Args:
            event_type: Canvas event type (node_created, node_updated, edge_created)
            canvas_name: Canvas name (without .canvas extension)
            node_id: Node ID (for node events)
            edge_id: Edge ID (for edge events)
            node_data: Node data dictionary (for metadata extraction)
            edge_data: Edge data dictionary (for metadata extraction)

        [Source: ADR-0004 - asyncio.create_task for fire-and-forget]
        [Source: docs/stories/30.5.story.md#Task-2.2]
        """
        if self._memory_client is None:
            # Story 38.5 AC-1/AC-4: Upgrade to WARNING + JSON fallback
            if getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True):
                self._write_canvas_event_fallback(
                    event_type.value, canvas_name, node_id=node_id, edge_id=edge_id
                )
                logger.warning("Memory client unavailable, writing to JSON fallback")
            else:
                logger.warning("Memory client unavailable, skipping event trigger")
            return

        try:
            # Build context for metadata extraction
            context = CanvasEventContext(
                canvas_name=canvas_name,
                node_id=node_id,
                edge_id=edge_id,
                node_data=node_data,
                edge_data=edge_data
            )

            # [Review H1] Fire-and-forget with timeout + fallback on timeout/error
            asyncio.create_task(
                self._safe_write_memory_event(event_type, context)
            )
            logger.debug(f"Triggered memory event: {event_type.value} for {canvas_name}")

        except Exception as e:
            # Task 4: Silent degradation - log but don't raise
            logger.error(
                f"Memory event trigger failed: {event_type.value} "
                f"for {canvas_name}: {e}"
            )
            # Don't re-raise - CRUD operation should succeed

    async def _safe_write_memory_event(
        self,
        event_type: CanvasEventType,
        context: CanvasEventContext
    ) -> None:
        """
        [Review H1] Wrapper that catches TimeoutError at the wait_for level.

        Without this wrapper, wait_for timeout cancels the inner coroutine
        (CancelledError, not caught by except Exception) and raises TimeoutError
        at the task level — unhandled. This wrapper ensures fallback is triggered.
        """
        try:
            await asyncio.wait_for(
                self._write_memory_event(event_type, context),
                timeout=0.5  # 500ms timeout per ADR-0003
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Memory write timed out for {event_type.value}: {context.canvas_name}"
            )
            self._try_fallback_write(event_type, context)
        except asyncio.CancelledError:
            logger.warning(
                f"Memory write cancelled for {event_type.value}: {context.canvas_name}"
            )
            self._try_fallback_write(event_type, context)
        except Exception as e:
            logger.warning(
                f"Memory write failed for {event_type.value}: "
                f"{context.canvas_name}: {e}"
            )
            self._try_fallback_write(event_type, context)

    async def _write_memory_event(
        self,
        event_type: CanvasEventType,
        context: CanvasEventContext
    ) -> None:
        """
        Write memory event to MemoryService (called by fire-and-forget task).

        Story 30.5: Actual memory write operation.

        Args:
            event_type: Canvas event type
            context: Event context with canvas/node/edge info

        [Source: docs/stories/30.5.story.md#Task-3.1]
        """
        try:
            # Build canvas path for storage
            canvas_path = f"{context.canvas_name}.canvas"

            # Extract metadata from context
            metadata = context.to_metadata()

            # Call MemoryService to record the temporal event
            await self._memory_client.record_temporal_event(
                event_type=event_type.value,
                session_id=self._session_id,
                canvas_path=canvas_path,
                node_id=context.node_id,
                edge_id=context.edge_id,
                metadata=metadata
            )

        except asyncio.TimeoutError:
            logger.warning(
                f"Memory write timed out for {event_type.value}: {context.canvas_name}"
            )
            # Story 38.5 AC-2: Fallback on timeout
            self._try_fallback_write(event_type, context)
        except Exception as e:
            # Story 38.5 AC-2: Fallback on error (upgraded from silent degradation)
            logger.warning(
                f"Memory write failed for {event_type.value}: "
                f"{context.canvas_name}: {e}"
            )
            self._try_fallback_write(event_type, context)

    def _try_fallback_write(
        self, event_type: "CanvasEventType", context: "CanvasEventContext"
    ) -> None:
        """Story 38.5 AC-2: Try writing to JSON fallback after Neo4j failure."""
        if getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True):
            self._write_canvas_event_fallback(
                event_type.value, context.canvas_name,
                node_id=context.node_id, edge_id=context.edge_id
            )
            logger.warning(
                f"Event {event_type.value} written to JSON fallback for {context.canvas_name}"
            )

    def _trigger_lancedb_index(
        self, canvas_name: str, node_id: str | None = None
    ) -> None:
        """
        Story 38.1 AC-1: Trigger LanceDB index update (fire-and-forget with debounce).

        Non-blocking. Uses lazy import to avoid circular dependency.
        Index failure does NOT affect CRUD operation result (AC-2).

        Args:
            canvas_name: Canvas name (without .canvas extension)
            node_id: Node ID that triggered this index (for AC-2 logging)
        """
        try:
            from app.services.lancedb_index_service import get_lancedb_index_service

            svc = get_lancedb_index_service()
            if svc is not None:
                svc.schedule_index(
                    canvas_name, self.canvas_base_path, trigger_node_id=node_id
                )
        except Exception as e:
            logger.warning(
                f"[Story 38.1] Failed to schedule LanceDB index for {canvas_name}: {e}"
            )

    async def _sync_edge_to_neo4j(
        self,
        canvas_path: str,
        edge_id: str,
        from_node_id: str,
        to_node_id: str,
        edge_label: Optional[str] = None
    ) -> Optional[bool]:
        """
        Sync edge to Neo4j with retry mechanism (fire-and-forget).

        Story 36.3: Canvas Edge automatic sync to Neo4j.
        - AC-1: Triggered after add_edge() completes successfully
        - AC-2: Fire-and-forget pattern - Canvas operation returns immediately
        - AC-3: Retry mechanism with 3 attempts, exponential backoff (1s, 2s, 4s)
        - AC-5: Creates CONNECTS_TO relationship in Neo4j with edge metadata

        Args:
            canvas_path: Canvas file path (e.g., "笔记库/离散数学.canvas")
            edge_id: Edge unique identifier
            from_node_id: Source node ID
            to_node_id: Target node ID
            edge_label: Optional edge label

        Returns:
            True if sync successful, False if skipped, None if failed after retries

        [Source: docs/stories/36.3.story.md#Task-1]
        [Source: ADR-009 - tenacity retry with exponential backoff]
        """
        if self._memory_client is None:
            # Story 38.5 AC-1/AC-4: Upgrade to WARNING + JSON fallback
            if getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True):
                self._write_canvas_event_fallback(
                    "edge_sync", canvas_path, edge_id=edge_id,
                    from_node_id=from_node_id, to_node_id=to_node_id
                )
                logger.warning("Memory client unavailable, writing edge to JSON fallback")
            else:
                logger.warning("Memory client not configured, skipping edge sync to Neo4j")
            return False

        # Access Neo4jClient through MemoryService
        neo4j = self._memory_client.neo4j
        if neo4j is None:
            # Story 38.5 AC-2/AC-4: Upgrade to WARNING + JSON fallback
            if getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True):
                self._write_canvas_event_fallback(
                    "edge_sync", canvas_path, edge_id=edge_id,
                    from_node_id=from_node_id, to_node_id=to_node_id
                )
                logger.warning("Neo4j unreachable, event written to JSON fallback")
            else:
                logger.warning("Neo4j client not available in memory_client")
            return False

        # Inner function with retry decorator
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type(Exception),
            reraise=True  # We catch RetryError at outer level
        )
        async def _do_sync() -> bool:
            result = await neo4j.create_edge_relationship(
                canvas_path=canvas_path,
                edge_id=edge_id,
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                edge_label=edge_label
            )
            if not result:
                raise Exception("Neo4j returned False")
            return result

        try:
            result = await _do_sync()
            logger.debug(
                f"Edge synced to Neo4j: {edge_id} "
                f"({from_node_id} -> {to_node_id})"
            )
            return result
        except Exception as e:
            # AC-4: Silent degradation after all retries exhausted
            logger.warning(
                f"Edge sync to Neo4j failed after retries: {edge_id}, "
                f"error: {type(e).__name__}: {e}"
            )
            return None  # Fire-and-forget: don't raise

    async def sync_all_edges_to_neo4j(
        self,
        canvas_name: str
    ) -> Dict[str, Any]:
        """
        Sync all Canvas edges to Neo4j (idempotent operation).

        Story 36.4: Canvas打开时全量Edge同步
        - AC-1: POST /api/v1/canvas/{canvas_path}/sync-edges endpoint
        - AC-2: Reads all edges from Canvas and syncs each to Neo4j
        - AC-3: Idempotent - MERGE semantics, no duplicates on repeated calls
        - AC-4: Returns summary with total, synced, failed counts
        - AC-5: Async processing - concurrent edge syncs
        - AC-6: Partial failure handling - single edge failure doesn't block batch
        - AC-7: Response time < 5s for up to 100 edges

        Args:
            canvas_name: Canvas file name (without .canvas extension)

        Returns:
            Dict containing:
                - canvas_path: str
                - total_edges: int
                - synced_count: int
                - failed_count: int
                - skipped_count: int
                - sync_time_ms: float

        [Source: docs/stories/36.4.story.md]
        [Source: ADR-0003 - MERGE idempotency]
        [Source: ADR-0004 - asyncio.gather with Semaphore]
        """
        start_time = time.time()

        # Read Canvas data using existing method
        canvas_data = await self.read_canvas(canvas_name)
        edges = canvas_data.get("edges", [])
        total_edges = len(edges)

        # Early return for empty Canvas
        if total_edges == 0:
            return {
                "canvas_path": canvas_name,
                "total_edges": 0,
                "synced_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "sync_time_ms": 0.0
            }

        # ADR-0004: Semaphore limits concurrent Neo4j connections
        semaphore = asyncio.Semaphore(12)

        async def sync_single_edge(edge: Dict[str, Any]) -> Optional[bool]:
            """Sync single edge with concurrency control."""
            async with semaphore:
                try:
                    return await self._sync_edge_to_neo4j(
                        canvas_path=f"{canvas_name}.canvas",
                        edge_id=edge["id"],
                        from_node_id=edge["fromNode"],
                        to_node_id=edge["toNode"],
                        edge_label=edge.get("label")
                    )
                except Exception as e:
                    logger.warning(
                        f"Edge sync failed in batch: {edge.get('id')}, error: {e}"
                    )
                    return None

        # ADR-009: return_exceptions=True for partial failure handling
        results = await asyncio.gather(
            *[sync_single_edge(edge) for edge in edges],
            return_exceptions=True
        )

        # Calculate statistics
        synced_count = sum(1 for r in results if r is True)
        failed_count = sum(
            1 for r in results
            if r is None or isinstance(r, Exception)
        )
        skipped_count = sum(1 for r in results if r is False)

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Edge bulk sync completed for {canvas_name}: "
            f"total={total_edges}, synced={synced_count}, "
            f"failed={failed_count}, skipped={skipped_count}, "
            f"time={elapsed_ms:.1f}ms"
        )

        return {
            "canvas_path": canvas_name,
            "total_edges": total_edges,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "sync_time_ms": elapsed_ms
        }

    async def read_canvas(self, canvas_name: str) -> Dict[str, Any]:
        """
        Read a Canvas file asynchronously.

        Args:
            canvas_name: Canvas file name (without .canvas extension)

        Returns:
            Canvas data dict

        Raises:
            CanvasNotFoundException: If canvas file doesn't exist
            ValidationError: If canvas name contains path traversal

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        canvas_path = self._get_canvas_path(canvas_name)
        logger.debug(f"Reading canvas: {canvas_path}")

        def _read_file() -> Dict[str, Any]:
            if not canvas_path.exists():
                raise CanvasNotFoundException(f"Canvas not found: {canvas_name}")
            with open(canvas_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        data = await asyncio.to_thread(_read_file)
        data['name'] = canvas_name
        return data

    async def write_canvas(self, canvas_name: str, canvas_data: Dict[str, Any]) -> bool:
        """
        Write canvas data to file (with concurrency lock).

        Story 12.H.1: Uses per-canvas lock to prevent race conditions
        during concurrent write operations.

        Args:
            canvas_name: Canvas file name (without .canvas extension)
            canvas_data: Canvas data to write

        Returns:
            True if successful

        Raises:
            ValidationError: If canvas name contains path traversal

        [Source: Python asyncio.Lock - async context manager for mutual exclusion]
        """
        canvas_path = self._get_canvas_path(canvas_name)
        logger.debug(f"Writing canvas: {canvas_path}")

        # Story 12.H.1: Acquire per-canvas lock before write
        lock = await self._get_lock(canvas_name)
        async with lock:
            logger.debug(f"Acquired write lock for canvas: {canvas_name}")

            def _write_file() -> bool:
                canvas_path.parent.mkdir(parents=True, exist_ok=True)
                with open(canvas_path, 'w', encoding='utf-8') as f:
                    json.dump(canvas_data, f, indent=2, ensure_ascii=False)
                return True

            result = await asyncio.to_thread(_write_file)
            logger.debug(f"Released write lock for canvas: {canvas_name}")
            return result

    async def canvas_exists(self, canvas_name: str) -> bool:
        """
        Check if a canvas file exists.

        Args:
            canvas_name: Canvas file name

        Returns:
            True if canvas exists
        """
        try:
            canvas_path = self._get_canvas_path(canvas_name)
            return await asyncio.to_thread(canvas_path.exists)
        except ValidationError:
            return False

    async def list_canvases(self) -> List[str]:
        """
        List all available Canvas files.

        Returns:
            List of canvas names

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Listing canvases in: {self.canvas_base_path}")

        def _list_files() -> List[str]:
            base_path = Path(self.canvas_base_path)
            if not base_path.exists():
                return []
            return [f.stem for f in base_path.glob("*.canvas")]

        return await asyncio.to_thread(_list_files)

    async def add_node(
        self,
        canvas_name: str,
        node_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a node to a Canvas.

        Args:
            canvas_name: Target canvas name
            node_data: Node data to add

        Returns:
            Added node data with generated ID

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: docs/stories/30.5.story.md#AC-30.5.1]
        """
        logger.debug(f"Adding node to {canvas_name}: {node_data}")

        canvas_data = await self.read_canvas(canvas_name)

        # Generate node ID if not provided
        node_id = node_data.get("id") or str(uuid.uuid4())[:8]
        new_node = {"id": node_id, **node_data}

        # Add default dimensions if not provided
        new_node.setdefault("width", 250)
        new_node.setdefault("height", 60)

        canvas_data["nodes"].append(new_node)
        await self.write_canvas(canvas_name, canvas_data)

        # Story 30.5 AC-30.5.1: Trigger node_created memory event (fire-and-forget)
        await self._trigger_memory_event(
            event_type=CanvasEventType.NODE_CREATED,
            canvas_name=canvas_name,
            node_id=new_node["id"],
            node_data=new_node
        )

        # Story 38.1 AC-1: Trigger LanceDB auto-index (fire-and-forget, debounced)
        self._trigger_lancedb_index(canvas_name, node_id=new_node["id"])

        return new_node

    async def update_node(
        self,
        canvas_name: str,
        node_id: str,
        node_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a node in a Canvas.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to update
            node_data: New node data (partial update)

        Returns:
            Updated node data

        Raises:
            NodeNotFoundException: If node doesn't exist

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: docs/stories/30.5.story.md#AC-30.5.3]
        """
        logger.debug(f"Updating node {node_id} in {canvas_name}")

        canvas_data = await self.read_canvas(canvas_name)

        # Find and update node
        for i, node in enumerate(canvas_data["nodes"]):
            if node.get("id") == node_id:
                # Merge updates, preserving existing data
                updated_node = {**node, **node_data, "id": node_id}
                canvas_data["nodes"][i] = updated_node
                await self.write_canvas(canvas_name, canvas_data)

                # Story 30.5 AC-30.5.3: Trigger node_updated memory event (fire-and-forget)
                await self._trigger_memory_event(
                    event_type=CanvasEventType.NODE_UPDATED,
                    canvas_name=canvas_name,
                    node_id=node_id,
                    node_data=updated_node
                )

                # Story 38.1 AC-1: Trigger LanceDB auto-index (fire-and-forget, debounced)
                self._trigger_lancedb_index(canvas_name, node_id=node_id)

                return updated_node

        raise NodeNotFoundException(f"Node not found: {node_id}")

    async def delete_node(self, canvas_name: str, node_id: str) -> bool:
        """
        Delete a node from a Canvas.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to delete

        Returns:
            True if deleted, False if not found

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Deleting node {node_id} from {canvas_name}")

        canvas_data = await self.read_canvas(canvas_name)

        # Find and remove node
        original_count = len(canvas_data["nodes"])
        canvas_data["nodes"] = [n for n in canvas_data["nodes"] if n.get("id") != node_id]

        if len(canvas_data["nodes"]) == original_count:
            return False

        # Also remove related edges
        canvas_data["edges"] = [
            e for e in canvas_data.get("edges", [])
            if e.get("fromNode") != node_id and e.get("toNode") != node_id
        ]

        await self.write_canvas(canvas_name, canvas_data)

        # [Review M4] Trigger LanceDB re-index on delete to remove stale entries
        self._trigger_lancedb_index(canvas_name, node_id=node_id)

        return True

    async def get_nodes_by_color(
        self,
        canvas_name: str,
        color: str
    ) -> List[Dict[str, Any]]:
        """
        Get all nodes with a specific color.

        Args:
            canvas_name: Target canvas name
            color: Color code to filter by (e.g., "4" for red, "2" for green, "3" for purple)

        Returns:
            List of matching nodes
        """
        canvas_data = await self.read_canvas(canvas_name)
        return [
            node for node in canvas_data.get("nodes", [])
            if node.get("color") == color
        ]

    async def add_edge(
        self,
        canvas_name: str,
        edge_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add an edge between two nodes.

        Args:
            canvas_name: Target canvas name
            edge_data: Edge data with fromNode and toNode

        Returns:
            Added edge data with generated ID

        [Source: docs/stories/30.5.story.md#AC-30.5.2]
        """
        logger.debug(f"Adding edge to {canvas_name}: {edge_data}")

        canvas_data = await self.read_canvas(canvas_name)

        # Generate edge ID if not provided
        edge_id = edge_data.get("id") or str(uuid.uuid4())[:8]
        new_edge = {"id": edge_id, **edge_data}

        if "edges" not in canvas_data:
            canvas_data["edges"] = []
        canvas_data["edges"].append(new_edge)

        await self.write_canvas(canvas_name, canvas_data)

        # Story 30.5 AC-30.5.2: Trigger edge_created memory event (fire-and-forget)
        await self._trigger_memory_event(
            event_type=CanvasEventType.EDGE_CREATED,
            canvas_name=canvas_name,
            edge_id=new_edge["id"],
            edge_data=new_edge
        )

        # Story 36.3: Fire-and-forget Neo4j edge sync
        # AC-2: Canvas operation returns immediately without waiting
        # AC-4: Sync failure does not affect Canvas operation result
        try:
            asyncio.create_task(
                self._sync_edge_to_neo4j(
                    canvas_path=f"{canvas_name}.canvas",
                    edge_id=new_edge["id"],
                    from_node_id=new_edge["fromNode"],
                    to_node_id=new_edge["toNode"],
                    edge_label=new_edge.get("label")
                )
            )
            logger.debug(f"Scheduled edge sync to Neo4j: {new_edge['id']}")
        except Exception as e:
            # AC-4: Silent degradation - log but don't raise
            logger.warning(f"Failed to schedule edge sync to Neo4j: {e}")

        return new_edge

    async def delete_edge(self, canvas_name: str, edge_id: str) -> bool:
        """
        Delete an edge from a Canvas.

        Args:
            canvas_name: Target canvas name
            edge_id: ID of edge to delete

        Returns:
            True if deleted
        """
        logger.debug(f"Deleting edge {edge_id} from {canvas_name}")

        canvas_data = await self.read_canvas(canvas_name)

        original_count = len(canvas_data.get("edges", []))
        canvas_data["edges"] = [
            e for e in canvas_data.get("edges", [])
            if e.get("id") != edge_id
        ]

        if len(canvas_data.get("edges", [])) == original_count:
            return False

        await self.write_canvas(canvas_name, canvas_data)
        return True

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        Called by dependency injection when using yield syntax.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self._initialized = False
        logger.debug("CanvasService cleanup completed")
