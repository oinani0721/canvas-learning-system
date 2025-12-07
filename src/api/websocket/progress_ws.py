"""
WebSocket Progress Service

Real-time progress updates for verification canvas.

Story 19.4 AC 1-6: WebSocket实时进度推送

✅ Verified from FastAPI WebSocket docs (Context7: /fastapi/fastapi)
✅ Verified from watchdog docs (Context7: /gorakhargosh/watchdog)
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WSMessage:
    """
    WebSocket message structure.

    [Source: docs/stories/19.4.story.md:78-102 - SDD规范参考]

    Attributes:
        type: Message type ('progress_update', 'connection_ack', 'error')
        data: Message payload
        timestamp: ISO format timestamp
    """

    def __init__(
        self,
        msg_type: str,
        data: Dict[str, Any],
        timestamp: Optional[str] = None
    ):
        self.type = msg_type
        self.data = data
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp
        }


class ProgressConnectionManager:
    """
    WebSocket connection manager for progress updates.

    Manages active WebSocket connections per canvas_id and handles
    broadcasting progress updates to connected clients.

    [Source: docs/stories/19.4.story.md:130-148 - 架构设计参考]

    Example:
        >>> manager = ProgressConnectionManager()
        >>> await manager.connect(websocket, "离散数学.canvas")
        >>> await manager.broadcast_progress_update("离散数学.canvas", {...})

    ✅ Verified from FastAPI WebSocket docs (Context7: /fastapi/fastapi)
    """

    def __init__(self):
        # canvas_id -> list of websocket connections
        # ✅ Verified: Dict structure for multi-client support per canvas
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, canvas_id: str) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection object
            canvas_id: Canvas identifier to subscribe to

        [Source: FastAPI WebSocket docs - websocket.accept()]
        """
        # ✅ Verified from Context7: FastAPI WebSocket accept pattern
        await websocket.accept()

        async with self._lock:
            if canvas_id not in self.active_connections:
                self.active_connections[canvas_id] = []
            self.active_connections[canvas_id].append(websocket)

        # Send connection acknowledgment
        # [Source: docs/stories/19.4.story.md:99-102 - ConnectionAckData]
        ack_message = WSMessage(
            msg_type="connection_ack",
            data={"status": "connected", "canvas_id": canvas_id}
        )
        await websocket.send_json(ack_message.to_dict())

        logger.info(f"WebSocket connected for canvas: {canvas_id}")

    async def disconnect(self, websocket: WebSocket, canvas_id: str) -> None:
        """
        Remove a disconnected WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            canvas_id: Canvas identifier

        [Source: FastAPI WebSocket docs - connection cleanup]
        """
        async with self._lock:
            if canvas_id in self.active_connections:
                try:
                    self.active_connections[canvas_id].remove(websocket)
                    if not self.active_connections[canvas_id]:
                        del self.active_connections[canvas_id]
                except ValueError:
                    pass  # Already removed

        logger.info(f"WebSocket disconnected for canvas: {canvas_id}")

    async def broadcast_progress_update(
        self,
        canvas_id: str,
        progress_data: Dict[str, Any],
        changed_node: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Broadcast progress update to all connected clients for a canvas.

        Args:
            canvas_id: Canvas identifier
            progress_data: Progress statistics (total_concepts, passed_count, etc.)
            changed_node: Optional node change information

        Returns:
            Number of clients successfully notified

        [Source: docs/stories/19.4.story.md:86-97 - ProgressUpdateData]
        """
        if canvas_id not in self.active_connections:
            return 0

        # Build message according to SDD spec
        message = WSMessage(
            msg_type="progress_update",
            data={
                "canvas_id": canvas_id,
                **progress_data,
                "changed_node": changed_node
            }
        )

        disconnected: List[WebSocket] = []
        notified = 0

        # ✅ Verified from Context7: send_json pattern
        for connection in self.active_connections.get(canvas_id, []):
            try:
                await connection.send_json(message.to_dict())
                notified += 1
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn, canvas_id)

        return notified

    async def send_error(
        self,
        websocket: WebSocket,
        error_code: str,
        error_message: str
    ) -> None:
        """
        Send an error message to a specific client.

        Args:
            websocket: Target WebSocket connection
            error_code: Error code identifier
            error_message: Human-readable error message
        """
        message = WSMessage(
            msg_type="error",
            data={"code": error_code, "message": error_message}
        )
        try:
            await websocket.send_json(message.to_dict())
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    def get_connection_count(self, canvas_id: str) -> int:
        """Get number of active connections for a canvas."""
        return len(self.active_connections.get(canvas_id, []))

    def get_all_canvas_ids(self) -> List[str]:
        """Get list of all canvas IDs with active connections."""
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ProgressConnectionManager()


async def websocket_progress_endpoint(
    websocket: WebSocket,
    canvas_id: str
) -> None:
    """
    WebSocket endpoint for progress updates.

    Endpoint: WS /ws/progress/{canvas_id}

    Maintains connection and waits for client messages or disconnection.
    Progress updates are pushed via the manager.broadcast_progress_update().

    Args:
        websocket: FastAPI WebSocket connection
        canvas_id: Canvas identifier from URL path

    [Source: docs/stories/19.4.story.md:106 - API端点规范]
    ✅ Verified from Context7: FastAPI WebSocket endpoint pattern
    """
    await manager.connect(websocket, canvas_id)
    try:
        while True:
            # Keep connection alive, wait for client messages
            # Client can send heartbeat or close
            # ✅ Verified from Context7: receive_text pattern
            data = await websocket.receive_text()

            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        # ✅ Verified from Context7: WebSocketDisconnect exception handling
        await manager.disconnect(websocket, canvas_id)
    except Exception as e:
        logger.error(f"WebSocket error for {canvas_id}: {e}")
        await manager.disconnect(websocket, canvas_id)


class CanvasFileWatcher:
    """
    Watches Canvas files for changes and triggers progress updates.

    Uses watchdog library to monitor file system changes on Canvas JSON files.
    When a Canvas file is modified, it parses the changes and broadcasts
    progress updates via WebSocket.

    [Source: docs/stories/19.4.story.md:30-34 - Task 2: Canvas文件监听]

    ✅ Verified from watchdog docs (Context7: /gorakhargosh/watchdog)

    Example:
        >>> watcher = CanvasFileWatcher("/path/to/vault")
        >>> watcher.start()
        >>> # ... later
        >>> watcher.stop()
    """

    def __init__(
        self,
        watch_path: str,
        on_canvas_change: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """
        Initialize the Canvas file watcher.

        Args:
            watch_path: Path to the Obsidian vault to monitor
            on_canvas_change: Callback when canvas changes (canvas_path, canvas_data)
        """
        self.watch_path = Path(watch_path)
        self.on_canvas_change = on_canvas_change
        self._observer = None
        self._running = False
        self._canvas_cache: Dict[str, Dict[str, Any]] = {}

    def _load_canvas(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a canvas JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load canvas {path}: {e}")
            return None

    def _detect_node_changes(
        self,
        old_data: Optional[Dict[str, Any]],
        new_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect which node changed between old and new canvas data.

        Returns:
            Changed node info or None if no relevant change detected
        """
        if old_data is None:
            return None

        old_nodes = {n['id']: n for n in old_data.get('nodes', [])}
        new_nodes = {n['id']: n for n in new_data.get('nodes', [])}

        # Find color changes
        for node_id, new_node in new_nodes.items():
            if node_id in old_nodes:
                old_node = old_nodes[node_id]
                old_color = old_node.get('color', '')
                new_color = new_node.get('color', '')

                if old_color != new_color:
                    return {
                        "node_id": node_id,
                        "source_node_id": new_node.get('sourceNodeId', ''),
                        "old_color": old_color,
                        "new_color": new_color
                    }

        return None

    def _calculate_progress(
        self,
        canvas_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate progress statistics from canvas data.

        [Source: Story 19.2 - ProgressAnalyzer integration]
        """
        nodes = canvas_data.get('nodes', [])

        # Count nodes with sourceNodeId (verification nodes)
        source_nodes = [n for n in nodes if 'sourceNodeId' in n]
        total_concepts = len(source_nodes)

        # Count passed (green = "2")
        passed_count = sum(
            1 for n in source_nodes
            if n.get('color') == '2'
        )

        coverage_rate = passed_count / total_concepts if total_concepts > 0 else 0.0

        return {
            "total_concepts": total_concepts,
            "passed_count": passed_count,
            "coverage_rate": round(coverage_rate, 4)
        }

    async def handle_file_modified(self, file_path: str) -> None:
        """
        Handle a canvas file modification event.

        Args:
            file_path: Path to the modified canvas file
        """
        path = Path(file_path)

        # Only process .canvas files
        if path.suffix != '.canvas':
            return

        canvas_id = path.name
        old_data = self._canvas_cache.get(canvas_id)
        new_data = self._load_canvas(path)

        if new_data is None:
            return

        # Detect changes
        changed_node = self._detect_node_changes(old_data, new_data)

        # Update cache
        self._canvas_cache[canvas_id] = new_data

        # Calculate progress
        progress_data = self._calculate_progress(new_data)

        # Broadcast update
        notified = await manager.broadcast_progress_update(
            canvas_id,
            progress_data,
            changed_node
        )

        if notified > 0:
            logger.info(
                f"Progress update sent for {canvas_id}: "
                f"{progress_data['passed_count']}/{progress_data['total_concepts']}"
            )

        # Call custom callback if provided
        if self.on_canvas_change:
            self.on_canvas_change(str(path), new_data)

    def start(self) -> None:
        """
        Start watching for canvas file changes.

        ✅ Verified from watchdog docs (Context7: /gorakhargosh/watchdog)
        - Observer.schedule() to register path
        - Observer.start() to begin monitoring
        """
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            logger.error("watchdog library not installed. Run: pip install watchdog")
            return

        class CanvasEventHandler(FileSystemEventHandler):
            def __init__(handler_self, watcher: 'CanvasFileWatcher'):
                handler_self.watcher = watcher

            def on_modified(handler_self, event):
                if not event.is_directory and event.src_path.endswith('.canvas'):
                    # Schedule async handler
                    asyncio.create_task(
                        handler_self.watcher.handle_file_modified(event.src_path)
                    )

        # ✅ Verified from Context7: Observer and schedule pattern
        self._observer = Observer()
        event_handler = CanvasEventHandler(self)
        self._observer.schedule(
            event_handler,
            str(self.watch_path),
            recursive=True
        )
        self._observer.start()
        self._running = True

        logger.info(f"Canvas file watcher started for: {self.watch_path}")

    def stop(self) -> None:
        """
        Stop watching for file changes.

        ✅ Verified from watchdog docs: observer.stop() and observer.join()
        """
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._running = False
            logger.info("Canvas file watcher stopped")

    @property
    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._running
