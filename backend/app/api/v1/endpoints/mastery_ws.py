"""
Mastery WebSocket Endpoint and Connection Manager

Story 5.2: WebSocket real-time mastery updates to the Obsidian frontend.

Endpoint:
  WS /ws - Accept WebSocket connections, broadcast mastery_update messages

Architecture:
  - MasteryConnectionManager maintains a set of active WebSocket connections
  - EventBus UI_MASTERY_PUSH events are forwarded to all connected clients
  - Heartbeat ping every 30 seconds keeps connections alive
  - On disconnect, frontend preserves cached mastery data (NFR-REL-02)

Message format (snake_case, frontend converts to camelCase):
  {
    "type": "mastery_update",
    "node_id": "abc-123",
    "effective_proficiency": 0.75,
    "has_interaction": true,
    "has_exam_record": true,
    "fsrs_next_review": "2026-03-20T00:00:00Z"
  }

[Source: obsidian-canvas-learning/src/services/api-client.ts - connectWebSocket / handleWebSocketMessage]
[Source: _bmad-output/implementation-artifacts/5-2-node-color-mastery-visualization.md]
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.models.canvas_events import LearningEvent, LearningEventType
from app.services.event_bus import get_event_bus

logger = logging.getLogger(__name__)

# Heartbeat interval (seconds)
_HEARTBEAT_INTERVAL_S = 30


class MasteryConnectionManager:
    """Manages WebSocket connections for mastery update broadcasts.

    Unlike the intelligent-parallel ConnectionManager which tracks sessions,
    this manager maintains a simple set of all connected clients. Every
    mastery_update message is broadcast to all connected frontends.
    """

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._subscribed = False

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
            count = len(self._connections)
        logger.info(f"Mastery WS connected (total={count})")

        # Subscribe to EventBus on first connection
        if not self._subscribed:
            self._subscribe_to_event_bus()

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the registry."""
        async with self._lock:
            self._connections.discard(websocket)
            count = len(self._connections)
        logger.info(f"Mastery WS disconnected (total={count})")

    async def broadcast(self, message: dict) -> int:
        """Send a message to all connected clients.

        Returns:
            Number of clients that received the message.
        """
        async with self._lock:
            connections = list(self._connections)

        if not connections:
            return 0

        sent = 0
        failed: list[WebSocket] = []
        payload = json.dumps(message, ensure_ascii=False)

        for ws in connections:
            try:
                await ws.send_text(payload)
                sent += 1
            except (ConnectionError, RuntimeError, OSError) as exc:
                logger.debug(f"Mastery WS broadcast failed for one client: {exc}")
                failed.append(ws)

        # Clean up broken connections
        if failed:
            async with self._lock:
                for ws in failed:
                    self._connections.discard(ws)

        return sent

    def _subscribe_to_event_bus(self) -> None:
        """Subscribe to UI_MASTERY_PUSH events on the EventBus."""
        event_bus = get_event_bus()
        event_bus.subscribe(
            LearningEventType.UI_MASTERY_PUSH,
            self._handle_mastery_push,
            subsystem="mastery_ws",
        )
        self._subscribed = True
        logger.info("MasteryConnectionManager subscribed to UI_MASTERY_PUSH")

    async def _handle_mastery_push(self, event: LearningEvent) -> None:
        """EventBus handler: forward UI_MASTERY_PUSH payload to all WS clients."""
        payload = event.payload
        message = {
            "type": "mastery_update",
            "node_id": payload.get("node_id", ""),
            "effective_proficiency": payload.get("effective_proficiency"),
            "has_interaction": payload.get("has_interaction", False),
            "has_exam_record": payload.get("has_exam_record", False),
            "fsrs_next_review": payload.get("fsrs_next_review"),
        }
        count = await self.broadcast(message)
        if count > 0:
            logger.debug(
                f"Mastery WS push: node={message['node_id']} -> {count} client(s)"
            )


# Global singleton
_mastery_ws_manager: Optional[MasteryConnectionManager] = None


def get_mastery_ws_manager() -> MasteryConnectionManager:
    """Get or create the global MasteryConnectionManager singleton."""
    global _mastery_ws_manager
    if _mastery_ws_manager is None:
        _mastery_ws_manager = MasteryConnectionManager()
    return _mastery_ws_manager


async def websocket_mastery_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint handler for /ws mastery updates.

    Lifecycle:
      1. Accept connection
      2. Start heartbeat task (ping every 30s)
      3. Listen for client messages (keep-alive)
      4. On disconnect, clean up

    [Source: api-client.ts connectWebSocket()]
    """
    manager = get_mastery_ws_manager()
    await manager.connect(websocket)

    # Start heartbeat
    heartbeat_task = asyncio.create_task(_heartbeat_loop(websocket))

    try:
        while True:
            # Wait for client messages to keep connection alive.
            # The frontend does not send meaningful messages on this channel;
            # this loop simply detects disconnection.
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=600.0)
            except asyncio.TimeoutError:
                # 10-minute inactivity timeout
                logger.info("Mastery WS: inactivity timeout, closing")
                break

    except WebSocketDisconnect:
        logger.debug("Mastery WS: client disconnected")

    except Exception as exc:
        logger.warning(f"Mastery WS error: {exc}")

    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        await manager.disconnect(websocket)


async def _heartbeat_loop(websocket: WebSocket) -> None:
    """Send periodic heartbeat pings to keep the connection alive."""
    try:
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL_S)
            try:
                ping_msg = json.dumps(
                    {
                        "type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                await websocket.send_text(ping_msg)
            except (ConnectionError, RuntimeError, OSError):
                break
    except asyncio.CancelledError:
        raise
