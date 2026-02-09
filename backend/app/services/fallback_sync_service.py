# Story 38.8: JSON Fallback → Neo4j Complete Sync Mechanism
#
# When Neo4j is unavailable, three JSON fallback files accumulate data.
# This service syncs them back to Neo4j on startup when it recovers.
#
# Fallback files:
#   1. data/failed_writes.jsonl     (Story 38.6 - scoring failures)
#   2. app/data/canvas_events_fallback.json  (Story 38.5 - Canvas CRUD)
#   3. data/learning_memories.json  (Story 38.4 - dual-write)

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.clients.neo4j_client import Neo4jClient, get_neo4j_client
from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock

logger = logging.getLogger(__name__)

# Directory paths
_BACKEND_DIR = Path(__file__).parent.parent.parent  # backend/
_APP_DATA_DIR = Path(__file__).parent.parent / "data"  # backend/app/data/

CANVAS_EVENTS_FALLBACK_FILE = _APP_DATA_DIR / "canvas_events_fallback.json"
LEARNING_MEMORIES_FILE = _BACKEND_DIR / "data" / "learning_memories.json"
SYNC_CHECKPOINT_FILE = _BACKEND_DIR / "data" / "sync_checkpoint.json"

# Lock for checkpoint file access
_checkpoint_lock = threading.Lock()

# Days before .synced files are cleaned up
_SYNCED_FILE_RETENTION_DAYS = 30

# Checkpoint save interval (entries)
_CHECKPOINT_INTERVAL = 50


class FallbackSyncService:
    """Syncs JSON fallback files back to Neo4j when it recovers."""

    def __init__(self, neo4j_client: Neo4jClient):
        self._neo4j = neo4j_client

    async def sync_all_fallbacks(self) -> Dict[str, Any]:
        """
        Sync all three fallback files to Neo4j.

        Checks Neo4j availability first. If unavailable, skips.
        Syncs in priority order: failed_writes → canvas_events → learning_memories.

        Returns:
            Dict with per-file stats or {"skipped": True, "reason": "..."}
        """
        # Check Neo4j availability
        if self._neo4j.is_fallback_mode:
            return {"skipped": True, "reason": "Neo4j in fallback mode"}

        try:
            healthy = await self._neo4j.health_check()
        except Exception as e:
            logger.warning(f"[Story 38.8] Neo4j health check failed: {e}")
            return {"skipped": True, "reason": f"health check failed: {e}"}

        if not healthy:
            return {"skipped": True, "reason": "Neo4j unhealthy"}

        result: Dict[str, Any] = {}

        # Priority 1: failed_writes (scoring failures)
        try:
            result["failed_writes"] = await self._sync_failed_writes()
        except Exception as e:
            logger.warning(f"[Story 38.8] failed_writes sync error: {e}")
            result["failed_writes"] = {"recovered": 0, "pending": 0, "error": str(e)}

        # Priority 2: canvas_events
        try:
            result["canvas_events"] = await self._sync_canvas_events()
        except Exception as e:
            logger.warning(f"[Story 38.8] canvas_events sync error: {e}")
            result["canvas_events"] = {"recovered": 0, "pending": 0, "error": str(e)}

        # Priority 3: learning_memories
        try:
            result["learning_memories"] = await self._sync_learning_memories()
        except Exception as e:
            logger.warning(f"[Story 38.8] learning_memories sync error: {e}")
            result["learning_memories"] = {"recovered": 0, "pending": 0, "error": str(e)}

        total_recovered = sum(
            v.get("recovered", 0) for v in result.values() if isinstance(v, dict)
        )
        total_pending = sum(
            v.get("pending", 0) for v in result.values() if isinstance(v, dict)
        )
        logger.info(
            f"[Story 38.8] Fallback sync complete: "
            f"{total_recovered} replayed, {total_pending} still pending"
        )

        return result

    # ─────────────────────────────────────────────────────────────────────
    # 1. failed_writes.jsonl sync
    # ─────────────────────────────────────────────────────────────────────

    async def _sync_failed_writes(self) -> Dict[str, int]:
        """Replay scoring failures from failed_writes.jsonl to Neo4j."""
        if not FAILED_WRITES_FILE.exists():
            return {"recovered": 0, "pending": 0}

        with failed_writes_lock:
            try:
                raw = FAILED_WRITES_FILE.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.warning(f"[Story 38.8] Cannot read failed_writes: {e}")
                return {"recovered": 0, "pending": 0}

        if not raw:
            return {"recovered": 0, "pending": 0}

        lines = raw.splitlines()
        checkpoint_idx = self._load_checkpoint("failed_writes")
        recovered = 0
        still_pending: List[str] = []

        for i, line in enumerate(lines):
            if i < checkpoint_idx:
                # Already synced in a previous partial run
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("[Story 38.8] Skipping malformed failed_writes entry")
                still_pending.append(line)
                continue

            try:
                success = await self._replay_scoring_entry_to_neo4j(entry)
                if success:
                    recovered += 1
                else:
                    still_pending.append(line)
            except Exception as e:
                logger.warning(f"[Story 38.8] failed_writes replay error: {e}")
                still_pending.append(line)

            # Checkpoint every N entries
            if (i + 1) % _CHECKPOINT_INTERVAL == 0:
                self._save_checkpoint("failed_writes", i + 1)

        # Finalize — re-read under lock to preserve entries appended
        # during the async replay window (race condition fix).
        with failed_writes_lock:
            new_lines: List[str] = []
            try:
                if FAILED_WRITES_FILE.exists():
                    current_raw = (
                        FAILED_WRITES_FILE.read_text(encoding="utf-8").strip()
                    )
                    current_lines = current_raw.splitlines() if current_raw else []
                    # Lines appended after our initial read
                    if len(current_lines) > len(lines):
                        new_lines = current_lines[len(lines):]
                else:
                    current_lines = []
            except Exception:
                current_lines = []

            merged = still_pending + new_lines
            if merged:
                self._atomic_write_file(
                    FAILED_WRITES_FILE,
                    "\n".join(merged) + "\n",
                )
            else:
                self._rotate_file(FAILED_WRITES_FILE)

        self._clear_checkpoint("failed_writes")
        self._cleanup_old_synced_files(
            FAILED_WRITES_FILE.parent, FAILED_WRITES_FILE.stem
        )

        return {"recovered": recovered, "pending": len(still_pending)}

    # ─────────────────────────────────────────────────────────────────────
    # 2. canvas_events_fallback.json sync
    # ─────────────────────────────────────────────────────────────────────

    async def _sync_canvas_events(self) -> Dict[str, int]:
        """Replay Canvas CRUD events to Neo4j."""
        if not CANVAS_EVENTS_FALLBACK_FILE.exists():
            return {"recovered": 0, "pending": 0}

        try:
            raw = CANVAS_EVENTS_FALLBACK_FILE.read_text(encoding="utf-8").strip()
            if not raw:
                return {"recovered": 0, "pending": 0}
            events: List[Dict[str, Any]] = json.loads(raw)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[Story 38.8] Cannot parse canvas_events_fallback: {e}")
            return {"recovered": 0, "pending": 0}

        if not events:
            return {"recovered": 0, "pending": 0}

        # Sort by timestamp for chronological replay
        events.sort(key=lambda e: e.get("timestamp", ""))

        checkpoint_idx = self._load_checkpoint("canvas_events")
        recovered = 0
        still_pending: List[Dict[str, Any]] = []

        for i, event in enumerate(events):
            if i < checkpoint_idx:
                continue

            try:
                success = await self._replay_canvas_event_to_neo4j(event)
                if success:
                    recovered += 1
                else:
                    still_pending.append(event)
            except Exception as e:
                logger.warning(f"[Story 38.8] canvas_event replay error: {e}")
                still_pending.append(event)

            if (i + 1) % _CHECKPOINT_INTERVAL == 0:
                self._save_checkpoint("canvas_events", i + 1)

        # Finalize
        if still_pending:
            self._atomic_write_file(
                CANVAS_EVENTS_FALLBACK_FILE,
                json.dumps(still_pending, ensure_ascii=False, indent=2),
            )
        else:
            self._rotate_file(CANVAS_EVENTS_FALLBACK_FILE)

        self._clear_checkpoint("canvas_events")
        self._cleanup_old_synced_files(
            CANVAS_EVENTS_FALLBACK_FILE.parent,
            CANVAS_EVENTS_FALLBACK_FILE.stem,
        )

        return {"recovered": recovered, "pending": len(still_pending)}

    # ─────────────────────────────────────────────────────────────────────
    # 3. learning_memories.json sync
    # ─────────────────────────────────────────────────────────────────────

    async def _sync_learning_memories(self) -> Dict[str, int]:
        """Replay learning memories to Neo4j using MERGE (idempotent)."""
        if not LEARNING_MEMORIES_FILE.exists():
            return {"recovered": 0, "pending": 0}

        try:
            raw = LEARNING_MEMORIES_FILE.read_text(encoding="utf-8").strip()
            if not raw:
                return {"recovered": 0, "pending": 0}
            data = json.loads(raw)
            memories: List[Dict[str, Any]] = data.get("memories", [])
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[Story 38.8] Cannot parse learning_memories: {e}")
            return {"recovered": 0, "pending": 0}

        if not memories:
            return {"recovered": 0, "pending": 0}

        # Sort by timestamp for chronological replay
        memories.sort(key=lambda m: m.get("timestamp", ""))

        checkpoint_idx = self._load_checkpoint("learning_memories")
        recovered = 0
        failed = 0

        for i, mem in enumerate(memories):
            if i < checkpoint_idx:
                continue

            try:
                success = await self._replay_learning_memory_to_neo4j(mem)
                if success:
                    recovered += 1
                else:
                    failed += 1
            except Exception as e:
                logger.warning(f"[Story 38.8] learning_memory replay error: {e}")
                failed += 1

            if (i + 1) % _CHECKPOINT_INTERVAL == 0:
                self._save_checkpoint("learning_memories", i + 1)

        # NOTE: learning_memories.json is NOT rotated - still needed by
        # LearningMemoryClient for runtime queries.
        self._clear_checkpoint("learning_memories")

        return {"recovered": recovered, "pending": failed}

    # ─────────────────────────────────────────────────────────────────────
    # Replay helpers
    # ─────────────────────────────────────────────────────────────────────

    async def _replay_scoring_entry_to_neo4j(self, entry: Dict[str, Any]) -> bool:
        """
        Replay a single failed scoring entry to Neo4j.

        Uses custom Cypher with last-write-wins conflict resolution:
        if Neo4j already has newer data for this relationship, preserve it.
        """
        concept = entry.get("concept") or entry.get("concept_id", "")
        canvas_name = entry.get("canvas_name", "")
        score = entry.get("score")
        ts = entry.get("timestamp", datetime.now().isoformat())

        if not concept:
            logger.warning("[Story 38.8] Skipping entry with no concept")
            return False

        # Build group_id from canvas_name
        group_id = self._build_group_id_from_canvas(canvas_name)

        # Timestamp-preserving MERGE with last-write-wins
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept})
        SET c.group_id = $groupId
        MERGE (u)-[r:LEARNED]->(c)
        WITH r,
             CASE WHEN r.timestamp IS NULL OR r.timestamp <= datetime($ts)
                  THEN true ELSE false END AS should_update
        SET r.score = CASE WHEN should_update THEN $score ELSE r.score END,
            r.timestamp = CASE WHEN should_update THEN datetime($ts) ELSE r.timestamp END,
            r.group_id = CASE WHEN should_update THEN $groupId ELSE r.group_id END
        RETURN should_update
        """

        try:
            results = await self._neo4j.run_query(
                query,
                userId="default_user",
                concept=concept,
                score=score,
                ts=ts,
                groupId=group_id,
            )
            if results and not results[0].get("should_update", True):
                logger.info(
                    f"[Story 38.8] Conflict: Neo4j has newer data for '{concept}', "
                    f"fallback timestamp={ts}"
                )
        except Exception as e:
            logger.warning(f"[Story 38.8] Neo4j scoring replay failed: {e}")
            return False

        # Also record score history if score present
        if score is not None:
            try:
                concept_id = entry.get("concept_id", concept)
                await self._neo4j.record_score_history(
                    concept_id=concept_id,
                    canvas_name=canvas_name,
                    score=int(score),
                    timestamp=ts,
                )
            except Exception as e:
                logger.warning(
                    f"[Story 38.8] Score history record failed (non-fatal): {e}"
                )

        return True

    async def _replay_canvas_event_to_neo4j(
        self, event: Dict[str, Any]
    ) -> bool:
        """Replay a single canvas event (node or edge) to Neo4j."""
        event_type = event.get("event_type", "")
        canvas_name = event.get("canvas_name", "")
        node_id = event.get("node_id")
        edge_id = event.get("edge_id")

        try:
            if event_type in ("node_created", "node_updated"):
                if not node_id:
                    return False
                return await self._neo4j.create_canvas_node_relationship(
                    canvas_path=canvas_name,
                    node_id=node_id,
                    node_text=None,
                )

            elif event_type == "edge_sync":
                if not edge_id:
                    return False
                from_node = event.get("from_node_id", "")
                to_node = event.get("to_node_id", "")
                if not from_node or not to_node:
                    return False
                return await self._neo4j.create_edge_relationship(
                    canvas_path=canvas_name,
                    edge_id=edge_id,
                    from_node_id=from_node,
                    to_node_id=to_node,
                )

            else:
                logger.debug(
                    f"[Story 38.8] Unknown canvas event type: {event_type}"
                )
                return True  # Don't block on unknown types
        except Exception as e:
            logger.warning(f"[Story 38.8] Canvas event replay failed: {e}")
            return False

    async def _replay_learning_memory_to_neo4j(
        self, mem: Dict[str, Any]
    ) -> bool:
        """Replay a single learning memory entry to Neo4j using MERGE (idempotent).

        Uses last-write-wins conflict resolution: if Neo4j already has newer
        data for this concept, the fallback entry does not overwrite it.
        """
        concept = mem.get("concept", "")
        canvas_name = mem.get("canvas_name", "")
        score = mem.get("score")
        ts = mem.get("timestamp", datetime.now().isoformat())

        if not concept:
            return False

        group_id = self._build_group_id_from_canvas(canvas_name)

        # Last-write-wins MERGE: only update if fallback timestamp is newer
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept})
        SET c.group_id = $groupId
        MERGE (u)-[r:LEARNED]->(c)
        WITH r,
             CASE WHEN r.timestamp IS NULL OR r.timestamp <= datetime($ts)
                  THEN true ELSE false END AS should_update
        SET r.score = CASE WHEN should_update THEN $score ELSE r.score END,
            r.timestamp = CASE WHEN should_update THEN datetime($ts) ELSE r.timestamp END,
            r.group_id = CASE WHEN should_update THEN $groupId ELSE r.group_id END,
            r.next_review = CASE WHEN should_update THEN datetime($ts) + duration('P1D') ELSE r.next_review END
        RETURN should_update
        """

        try:
            results = await self._neo4j.run_query(
                query,
                userId="default_user",
                concept=concept,
                score=int(score) if score is not None else None,
                ts=ts,
                groupId=group_id,
            )
            if results and not results[0].get("should_update", True):
                logger.info(
                    f"[Story 38.8] Conflict: Neo4j has newer data for '{concept}', "
                    f"fallback timestamp={ts}"
                )
        except Exception as e:
            logger.warning(f"[Story 38.8] Learning memory replay failed: {e}")
            return False

        return True

    # ─────────────────────────────────────────────────────────────────────
    # Checkpoint management
    # ─────────────────────────────────────────────────────────────────────

    def _load_checkpoint(self, file_key: str) -> int:
        """Load sync progress checkpoint for a file key."""
        with _checkpoint_lock:
            if not SYNC_CHECKPOINT_FILE.exists():
                return 0
            try:
                data = json.loads(
                    SYNC_CHECKPOINT_FILE.read_text(encoding="utf-8")
                )
                return data.get(file_key, {}).get("index", 0)
            except (json.JSONDecodeError, Exception):
                return 0

    def _save_checkpoint(self, file_key: str, index: int) -> None:
        """Save sync progress checkpoint."""
        with _checkpoint_lock:
            data: Dict[str, Any] = {}
            if SYNC_CHECKPOINT_FILE.exists():
                try:
                    data = json.loads(
                        SYNC_CHECKPOINT_FILE.read_text(encoding="utf-8")
                    )
                except (json.JSONDecodeError, Exception):
                    data = {}

            data[file_key] = {
                "index": index,
                "updated_at": datetime.now().isoformat(),
            }

            SYNC_CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write_file(
                SYNC_CHECKPOINT_FILE,
                json.dumps(data, ensure_ascii=False, indent=2),
            )

    def _clear_checkpoint(self, file_key: str) -> None:
        """Remove checkpoint entry after full sync."""
        with _checkpoint_lock:
            if not SYNC_CHECKPOINT_FILE.exists():
                return
            try:
                data = json.loads(
                    SYNC_CHECKPOINT_FILE.read_text(encoding="utf-8")
                )
                data.pop(file_key, None)
                if data:
                    self._atomic_write_file(
                        SYNC_CHECKPOINT_FILE,
                        json.dumps(data, ensure_ascii=False, indent=2),
                    )
                else:
                    SYNC_CHECKPOINT_FILE.unlink(missing_ok=True)
            except (json.JSONDecodeError, Exception):
                pass

    # ─────────────────────────────────────────────────────────────────────
    # File rotation & cleanup
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _rotate_file(path: Path) -> None:
        """Rename fully-synced file to .synced.YYYY-MM-DD-HHMMSS (Windows-safe)."""
        if not path.exists():
            return
        suffix = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        dest = path.with_suffix(f".synced.{suffix}")
        for attempt in range(3):
            try:
                path.rename(dest)
                logger.info(f"[Story 38.8] Rotated {path.name} → {dest.name}")
                return
            except PermissionError:
                if attempt < 2:
                    time.sleep(0.1)
                else:
                    logger.warning(
                        f"[Story 38.8] Cannot rotate {path.name} (PermissionError)"
                    )

    @staticmethod
    def _cleanup_old_synced_files(directory: Path, base_stem: str) -> None:
        """Delete .synced.* files older than retention period."""
        if not directory.exists():
            return
        cutoff = datetime.now() - timedelta(days=_SYNCED_FILE_RETENTION_DAYS)
        for f in directory.iterdir():
            if not f.name.startswith(base_stem) or ".synced." not in f.name:
                continue
            # Extract date from filename: base.synced.YYYY-MM-DD-HHMMSS or legacy YYYY-MM-DD
            try:
                date_str = f.name.rsplit(".synced.", 1)[1]
                # Try full timestamp first, then date-only (backward compat)
                for fmt in ("%Y-%m-%d-%H%M%S", "%Y-%m-%d"):
                    try:
                        file_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue
                if file_date < cutoff:
                    f.unlink(missing_ok=True)
                    logger.info(f"[Story 38.8] Cleaned up old synced file: {f.name}")
            except (ValueError, IndexError):
                pass

    # ─────────────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _atomic_write_file(path: Path, content: str) -> None:
        """Windows-safe atomic write via tmp + rename with 3 retries."""
        tmp = path.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        for attempt in range(3):
            try:
                tmp.replace(path)
                return
            except PermissionError:
                if attempt < 2:
                    time.sleep(0.1)
                else:
                    raise

    @staticmethod
    def _build_group_id_from_canvas(canvas_name: str) -> Optional[str]:
        """Build group_id from canvas name using subject_config."""
        if not canvas_name:
            return None
        try:
            from app.core.subject_config import (
                build_group_id,
                extract_subject_from_canvas_path,
            )
            subject = extract_subject_from_canvas_path(canvas_name)
            return build_group_id(subject, canvas_name)
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────

_fallback_sync_instance: Optional[FallbackSyncService] = None


def get_fallback_sync_service() -> FallbackSyncService:
    """Get or create FallbackSyncService singleton."""
    global _fallback_sync_instance
    if _fallback_sync_instance is None:
        neo4j = get_neo4j_client()
        _fallback_sync_instance = FallbackSyncService(neo4j_client=neo4j)
    return _fallback_sync_instance
