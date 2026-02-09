# Story 38.8: JSON Fallback → Neo4j Complete Sync — Unit Tests
#
# Tests for FallbackSyncService covering all 5 ACs:
#   AC-1: Startup replay (failed_writes, canvas_events, learning_memories)
#   AC-2: Idempotency (MERGE produces no duplicates)
#   AC-3: Checkpoint (resume from last success)
#   AC-4: Conflict resolution (last-write-wins)
#   AC-5: File rotation (rotate synced files, preserve learning_memories)

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.fallback_sync_service import (
    FallbackSyncService,
    SYNC_CHECKPOINT_FILE,
    _SYNCED_FILE_RETENTION_DAYS,
)


# ─────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_neo4j():
    """Create a mock Neo4jClient that is healthy and not in fallback mode."""
    client = AsyncMock()
    client.is_fallback_mode = False
    client.health_check = AsyncMock(return_value=True)
    client.run_query = AsyncMock(return_value=[{"should_update": True}])
    client.create_canvas_node_relationship = AsyncMock(return_value=True)
    client.create_edge_relationship = AsyncMock(return_value=True)
    client.create_learning_relationship = AsyncMock(return_value=True)
    client.record_score_history = AsyncMock(return_value=True)
    return client


@pytest.fixture
def sync_service(mock_neo4j):
    """Create a FallbackSyncService with mocked Neo4j."""
    return FallbackSyncService(neo4j_client=mock_neo4j)


@pytest.fixture
def tmp_failed_writes(tmp_path):
    """Create a temporary failed_writes.jsonl file."""
    f = tmp_path / "failed_writes.jsonl"
    return f


@pytest.fixture
def tmp_canvas_events(tmp_path):
    """Create a temporary canvas_events_fallback.json file."""
    f = tmp_path / "canvas_events_fallback.json"
    return f


@pytest.fixture
def tmp_learning_memories(tmp_path):
    """Create a temporary learning_memories.json file."""
    f = tmp_path / "learning_memories.json"
    return f


@pytest.fixture
def tmp_checkpoint(tmp_path):
    """Create a temporary sync_checkpoint.json file path."""
    return tmp_path / "sync_checkpoint.json"


def _patch_paths(
    tmp_failed_writes, tmp_canvas_events, tmp_learning_memories, tmp_checkpoint
):
    """Return dict of patches for all file paths (attribute names only)."""
    return {
        "FAILED_WRITES_FILE": tmp_failed_writes,
        "CANVAS_EVENTS_FALLBACK_FILE": tmp_canvas_events,
        "LEARNING_MEMORIES_FILE": tmp_learning_memories,
        "SYNC_CHECKPOINT_FILE": tmp_checkpoint,
    }


# Helper to write JSONL entries
def write_jsonl(path: Path, entries: list):
    lines = [json.dumps(e) for e in entries]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# AC-1: Startup Replay
# ═══════════════════════════════════════════════════════════════════════════

class TestAC1StartupReplay:
    """AC-1: On startup, replay fallback entries to Neo4j."""

    @pytest.mark.asyncio
    async def test_skips_when_neo4j_in_fallback_mode(self, sync_service, mock_neo4j):
        """Sync skips if Neo4j is in fallback mode."""
        mock_neo4j.is_fallback_mode = True
        result = await sync_service.sync_all_fallbacks()
        assert result["skipped"] is True
        assert "fallback mode" in result["reason"]

    @pytest.mark.asyncio
    async def test_skips_when_neo4j_unhealthy(self, sync_service, mock_neo4j):
        """Sync skips if Neo4j health check fails."""
        mock_neo4j.health_check = AsyncMock(return_value=False)
        result = await sync_service.sync_all_fallbacks()
        assert result["skipped"] is True

    @pytest.mark.asyncio
    async def test_replays_failed_writes_to_neo4j(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """failed_writes.jsonl entries are replayed via run_query."""
        entries = [
            {
                "timestamp": "2026-02-07T10:00:00",
                "event_type": "scoring",
                "concept_id": "c1",
                "canvas_name": "math.canvas",
                "score": 85,
                "error_reason": "timeout",
                "concept": "Calculus",
            },
            {
                "timestamp": "2026-02-07T10:01:00",
                "event_type": "scoring",
                "concept_id": "c2",
                "canvas_name": "physics.canvas",
                "score": 70,
                "error_reason": "connection",
                "concept": "Kinematics",
            },
        ]
        write_jsonl(tmp_failed_writes, entries)

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        assert result["failed_writes"]["recovered"] == 2
        assert result["failed_writes"]["pending"] == 0
        assert mock_neo4j.run_query.call_count == 2
        assert mock_neo4j.record_score_history.call_count == 2

    @pytest.mark.asyncio
    async def test_replays_canvas_node_events(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Canvas node events are replayed via create_canvas_node_relationship."""
        events = [
            {
                "event_type": "node_created",
                "canvas_name": "test.canvas",
                "node_id": "n1",
                "edge_id": None,
                "timestamp": "2026-02-07T10:00:00",
                "session_id": "s1",
            },
            {
                "event_type": "node_updated",
                "canvas_name": "test.canvas",
                "node_id": "n2",
                "edge_id": None,
                "timestamp": "2026-02-07T10:01:00",
                "session_id": "s2",
            },
        ]
        tmp_canvas_events.write_text(
            json.dumps(events, ensure_ascii=False), encoding="utf-8"
        )

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        assert result["canvas_events"]["recovered"] == 2
        assert mock_neo4j.create_canvas_node_relationship.call_count == 2

    @pytest.mark.asyncio
    async def test_replays_canvas_edge_events(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Canvas edge_sync events are replayed via create_edge_relationship."""
        events = [
            {
                "event_type": "edge_sync",
                "canvas_name": "test.canvas",
                "node_id": None,
                "edge_id": "e1",
                "timestamp": "2026-02-07T10:00:00",
                "session_id": "s1",
                "from_node_id": "n1",
                "to_node_id": "n2",
            },
        ]
        tmp_canvas_events.write_text(
            json.dumps(events, ensure_ascii=False), encoding="utf-8"
        )

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        assert result["canvas_events"]["recovered"] == 1
        mock_neo4j.create_edge_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_replays_learning_memories(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Learning memories are replayed via run_query (last-write-wins MERGE)."""
        data = {
            "memories": [
                {
                    "key": "math.canvas:n1:2026-02-07",
                    "canvas_name": "math.canvas",
                    "node_id": "n1",
                    "concept": "Algebra",
                    "score": 90,
                    "timestamp": "2026-02-07T10:00:00",
                },
                {
                    "key": "math.canvas:n2:2026-02-07",
                    "canvas_name": "math.canvas",
                    "node_id": "n2",
                    "concept": "Geometry",
                    "score": None,
                    "timestamp": "2026-02-07T10:01:00",
                },
            ],
            "metadata": {},
        }
        tmp_learning_memories.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        assert result["learning_memories"]["recovered"] == 2
        # Now uses run_query with last-write-wins MERGE (not create_learning_relationship)
        # run_query called: 2 for learning_memories (may also have failed_writes calls)
        learning_calls = [
            c for c in mock_neo4j.run_query.call_args_list
            if "LEARNED" in str(c) and "concept" in str(c).lower()
        ]
        assert len(learning_calls) >= 2

    @pytest.mark.asyncio
    async def test_chronological_order(
        self, sync_service, mock_neo4j, tmp_canvas_events,
        tmp_failed_writes, tmp_learning_memories, tmp_path,
    ):
        """Canvas events are sorted by timestamp before replay."""
        events = [
            {
                "event_type": "node_created",
                "canvas_name": "test.canvas",
                "node_id": "n2",
                "edge_id": None,
                "timestamp": "2026-02-07T10:05:00",
                "session_id": "s2",
            },
            {
                "event_type": "node_created",
                "canvas_name": "test.canvas",
                "node_id": "n1",
                "edge_id": None,
                "timestamp": "2026-02-07T10:00:00",
                "session_id": "s1",
            },
        ]
        tmp_canvas_events.write_text(
            json.dumps(events, ensure_ascii=False), encoding="utf-8"
        )

        call_order = []
        original_replay = sync_service._replay_canvas_event_to_neo4j

        async def tracking_replay(event):
            call_order.append(event["node_id"])
            return await original_replay(event)

        sync_service._replay_canvas_event_to_neo4j = tracking_replay

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            await sync_service.sync_all_fallbacks()

        # n1 (earlier timestamp) should be replayed first
        assert call_order == ["n1", "n2"]


# ═══════════════════════════════════════════════════════════════════════════
# AC-2: Idempotency
# ═══════════════════════════════════════════════════════════════════════════

class TestAC2Idempotency:
    """AC-2: MERGE-based replay is idempotent."""

    @pytest.mark.asyncio
    async def test_replay_same_entry_twice_is_safe(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Replaying the same scoring entry twice does not create duplicates."""
        entry = {
            "timestamp": "2026-02-07T10:00:00",
            "event_type": "scoring",
            "concept_id": "c1",
            "canvas_name": "math.canvas",
            "score": 85,
            "error_reason": "timeout",
            "concept": "Calculus",
        }
        # Write same entry twice
        write_jsonl(tmp_failed_writes, [entry, entry])

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        # Both replayed successfully (MERGE handles dedup in Neo4j)
        assert result["failed_writes"]["recovered"] == 2
        assert mock_neo4j.run_query.call_count == 2

    @pytest.mark.asyncio
    async def test_learning_memory_merge_no_duplicates(
        self, sync_service, mock_neo4j,
    ):
        """Learning memory replay uses MERGE (idempotent) with last-write-wins."""
        mem = {
            "canvas_name": "math.canvas",
            "concept": "Algebra",
            "score": 90,
            "timestamp": "2026-02-07T10:00:00",
        }
        # Replay twice — MERGE ensures no duplicates
        await sync_service._replay_learning_memory_to_neo4j(mem)
        await sync_service._replay_learning_memory_to_neo4j(mem)

        # Uses run_query with MERGE (not create_learning_relationship)
        assert mock_neo4j.run_query.call_count == 2


# ═══════════════════════════════════════════════════════════════════════════
# AC-3: Checkpoint
# ═══════════════════════════════════════════════════════════════════════════

class TestAC3Checkpoint:
    """AC-3: Checkpoint saves progress; resumes from last success."""

    @pytest.mark.asyncio
    async def test_checkpoint_created_during_sync(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Checkpoint file is created during sync of large batches."""
        # Create > _CHECKPOINT_INTERVAL entries
        entries = [
            {
                "timestamp": f"2026-02-07T10:{i:02d}:00",
                "event_type": "scoring",
                "concept_id": f"c{i}",
                "canvas_name": "math.canvas",
                "score": 80 + i,
                "error_reason": "timeout",
                "concept": f"Concept{i}",
            }
            for i in range(55)
        ]
        write_jsonl(tmp_failed_writes, entries)

        checkpoint_path = tmp_path / "sync_checkpoint.json"
        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, checkpoint_path,
        )

        checkpoints_saved = []
        original_save = sync_service._save_checkpoint

        def tracking_save(key, idx):
            checkpoints_saved.append((key, idx))
            return original_save(key, idx)

        sync_service._save_checkpoint = tracking_save

        with patch.multiple("app.services.fallback_sync_service", **patches):
            await sync_service.sync_all_fallbacks()

        # Should have saved checkpoint at index 50 (every 50 entries)
        assert ("failed_writes", 50) in checkpoints_saved

    @pytest.mark.asyncio
    async def test_resumes_from_checkpoint(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Sync resumes from checkpoint index, skipping already-synced entries."""
        entries = [
            {
                "timestamp": f"2026-02-07T10:{i:02d}:00",
                "event_type": "scoring",
                "concept_id": f"c{i}",
                "canvas_name": "math.canvas",
                "score": 80,
                "error_reason": "timeout",
                "concept": f"Concept{i}",
            }
            for i in range(5)
        ]
        write_jsonl(tmp_failed_writes, entries)

        # Pre-set checkpoint at index 3 (first 3 already synced)
        checkpoint_path = tmp_path / "sync_checkpoint.json"
        checkpoint_path.write_text(
            json.dumps({"failed_writes": {"index": 3, "updated_at": "2026-02-07"}}),
            encoding="utf-8",
        )

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, checkpoint_path,
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        # Only entries 3, 4 should be replayed (indices 0,1,2 skipped)
        assert result["failed_writes"]["recovered"] == 2
        assert mock_neo4j.run_query.call_count == 2

    @pytest.mark.asyncio
    async def test_checkpoint_cleared_after_full_sync(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Checkpoint entry is removed after successful full sync."""
        entries = [
            {
                "timestamp": "2026-02-07T10:00:00",
                "event_type": "scoring",
                "concept_id": "c1",
                "canvas_name": "math.canvas",
                "score": 85,
                "error_reason": "timeout",
                "concept": "Calculus",
            },
        ]
        write_jsonl(tmp_failed_writes, entries)

        checkpoint_path = tmp_path / "sync_checkpoint.json"
        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, checkpoint_path,
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            await sync_service.sync_all_fallbacks()

        # Checkpoint should be cleared (file deleted since no other keys)
        assert not checkpoint_path.exists()


# ═══════════════════════════════════════════════════════════════════════════
# AC-4: Conflict Resolution
# ═══════════════════════════════════════════════════════════════════════════

class TestAC4ConflictResolution:
    """AC-4: Last-write-wins conflict resolution."""

    @pytest.mark.asyncio
    async def test_newer_fallback_wins(self, sync_service, mock_neo4j):
        """When fallback timestamp is newer, Neo4j data gets updated."""
        mock_neo4j.run_query = AsyncMock(return_value=[{"should_update": True}])

        entry = {
            "timestamp": "2026-02-07T12:00:00",
            "concept_id": "c1",
            "canvas_name": "math.canvas",
            "score": 95,
            "concept": "Calculus",
        }
        result = await sync_service._replay_scoring_entry_to_neo4j(entry)

        assert result is True
        mock_neo4j.run_query.assert_called_once()
        call_kwargs = mock_neo4j.run_query.call_args
        assert call_kwargs.kwargs["score"] == 95

    @pytest.mark.asyncio
    async def test_older_fallback_preserves_neo4j(self, sync_service, mock_neo4j):
        """When Neo4j has newer data, fallback entry doesn't overwrite."""
        mock_neo4j.run_query = AsyncMock(return_value=[{"should_update": False}])

        entry = {
            "timestamp": "2026-02-01T10:00:00",
            "concept_id": "c1",
            "canvas_name": "math.canvas",
            "score": 60,
            "concept": "Calculus",
        }
        result = await sync_service._replay_scoring_entry_to_neo4j(entry)

        # Still returns True (replay succeeded, just didn't overwrite)
        assert result is True

    @pytest.mark.asyncio
    async def test_conflict_logged(self, sync_service, mock_neo4j, caplog):
        """When Neo4j has newer data, a log message is emitted."""
        mock_neo4j.run_query = AsyncMock(return_value=[{"should_update": False}])

        entry = {
            "timestamp": "2026-02-01T10:00:00",
            "concept_id": "c1",
            "canvas_name": "math.canvas",
            "score": 60,
            "concept": "Calculus",
        }
        import logging
        with caplog.at_level(logging.INFO):
            await sync_service._replay_scoring_entry_to_neo4j(entry)

        assert any("Conflict" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_learning_memory_older_fallback_preserves_neo4j(
        self, sync_service, mock_neo4j,
    ):
        """When Neo4j has newer learning memory data, fallback doesn't overwrite."""
        mock_neo4j.run_query = AsyncMock(return_value=[{"should_update": False}])

        mem = {
            "canvas_name": "math.canvas",
            "concept": "Algebra",
            "score": 60,
            "timestamp": "2026-01-01T10:00:00",
        }
        result = await sync_service._replay_learning_memory_to_neo4j(mem)

        # Still returns True (replay succeeded, just didn't overwrite)
        assert result is True

    @pytest.mark.asyncio
    async def test_learning_memory_conflict_logged(
        self, sync_service, mock_neo4j, caplog,
    ):
        """Learning memory conflict with Neo4j emits log message."""
        mock_neo4j.run_query = AsyncMock(return_value=[{"should_update": False}])

        mem = {
            "canvas_name": "math.canvas",
            "concept": "Algebra",
            "score": 60,
            "timestamp": "2026-01-01T10:00:00",
        }
        import logging
        with caplog.at_level(logging.INFO):
            await sync_service._replay_learning_memory_to_neo4j(mem)

        assert any("Conflict" in r.message for r in caplog.records)


# ═══════════════════════════════════════════════════════════════════════════
# AC-5: File Rotation
# ═══════════════════════════════════════════════════════════════════════════

class TestAC5FileRotation:
    """AC-5: Synced files are rotated; learning_memories preserved."""

    @pytest.mark.asyncio
    async def test_failed_writes_rotated_after_full_sync(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """failed_writes.jsonl is renamed to .synced.YYYY-MM-DD after full sync."""
        entries = [
            {
                "timestamp": "2026-02-07T10:00:00",
                "event_type": "scoring",
                "concept_id": "c1",
                "canvas_name": "math.canvas",
                "score": 85,
                "error_reason": "timeout",
                "concept": "Calculus",
            },
        ]
        write_jsonl(tmp_failed_writes, entries)

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            await sync_service.sync_all_fallbacks()

        # Original file should be gone (rotated)
        assert not tmp_failed_writes.exists()
        # .synced file should exist (with timestamp suffix YYYY-MM-DD-HHMMSS)
        synced_files = list(tmp_failed_writes.parent.glob("*.synced.*"))
        assert len(synced_files) >= 1

    @pytest.mark.asyncio
    async def test_canvas_events_rotated_after_full_sync(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """canvas_events_fallback.json is rotated after all events synced."""
        events = [
            {
                "event_type": "node_created",
                "canvas_name": "test.canvas",
                "node_id": "n1",
                "edge_id": None,
                "timestamp": "2026-02-07T10:00:00",
                "session_id": "s1",
            },
        ]
        tmp_canvas_events.write_text(
            json.dumps(events, ensure_ascii=False), encoding="utf-8"
        )

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            await sync_service.sync_all_fallbacks()

        assert not tmp_canvas_events.exists()

    @pytest.mark.asyncio
    async def test_learning_memories_not_rotated(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """learning_memories.json is NOT rotated (still needed at runtime)."""
        data = {
            "memories": [
                {
                    "key": "math.canvas:n1:2026-02-07",
                    "canvas_name": "math.canvas",
                    "node_id": "n1",
                    "concept": "Algebra",
                    "score": 90,
                    "timestamp": "2026-02-07T10:00:00",
                },
            ],
            "metadata": {},
        }
        tmp_learning_memories.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            await sync_service.sync_all_fallbacks()

        # File should still exist (NOT rotated)
        assert tmp_learning_memories.exists()

    def test_old_synced_files_cleaned_up(self, tmp_path):
        """Synced files older than retention period are deleted."""
        # Create old .synced file (new format with HHMMSS)
        old_date = (datetime.now() - timedelta(days=_SYNCED_FILE_RETENTION_DAYS + 5))
        old_synced = tmp_path / f"failed_writes.synced.{old_date.strftime('%Y-%m-%d-%H%M%S')}"
        old_synced.write_text("old data", encoding="utf-8")

        # Create old .synced file (legacy format without HHMMSS)
        old_legacy = tmp_path / f"failed_writes.synced.{old_date.strftime('%Y-%m-%d')}"
        old_legacy.write_text("old legacy data", encoding="utf-8")

        # Create recent .synced file
        recent = tmp_path / f"failed_writes.synced.{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
        recent.write_text("recent data", encoding="utf-8")

        FallbackSyncService._cleanup_old_synced_files(tmp_path, "failed_writes")

        assert not old_synced.exists()
        assert not old_legacy.exists()
        assert recent.exists()

    @pytest.mark.asyncio
    async def test_pending_entries_rewritten(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """When some entries fail, only pending entries are kept in file."""
        # First entry will succeed, second will fail
        entries = [
            {
                "timestamp": "2026-02-07T10:00:00",
                "event_type": "scoring",
                "concept_id": "c1",
                "canvas_name": "math.canvas",
                "score": 85,
                "error_reason": "timeout",
                "concept": "Calculus",
            },
            {
                "timestamp": "2026-02-07T10:01:00",
                "event_type": "scoring",
                "concept_id": "c2",
                "canvas_name": "physics.canvas",
                "score": 70,
                "error_reason": "connection",
                "concept": "Kinematics",
            },
        ]
        write_jsonl(tmp_failed_writes, entries)

        # Make run_query fail on second call
        call_count = {"n": 0}

        async def run_query_side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise Exception("Neo4j connection lost")
            return [{"should_update": True}]

        mock_neo4j.run_query = AsyncMock(side_effect=run_query_side_effect)

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        assert result["failed_writes"]["recovered"] == 1
        assert result["failed_writes"]["pending"] == 1

        # File should still exist with only the pending entry
        assert tmp_failed_writes.exists()
        remaining = tmp_failed_writes.read_text(encoding="utf-8").strip().splitlines()
        assert len(remaining) == 1
        remaining_entry = json.loads(remaining[0])
        assert remaining_entry["concept_id"] == "c2"


# ═══════════════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge cases: empty files, missing files, malformed data."""

    @pytest.mark.asyncio
    async def test_empty_files(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Empty fallback files produce zero-count results."""
        tmp_failed_writes.write_text("", encoding="utf-8")
        tmp_canvas_events.write_text("[]", encoding="utf-8")
        tmp_learning_memories.write_text(
            json.dumps({"memories": [], "metadata": {}}), encoding="utf-8"
        )

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        assert result["failed_writes"]["recovered"] == 0
        assert result["canvas_events"]["recovered"] == 0
        assert result["learning_memories"]["recovered"] == 0

    @pytest.mark.asyncio
    async def test_nonexistent_files(
        self, sync_service, mock_neo4j, tmp_path,
    ):
        """Non-existent fallback files produce zero-count results."""
        patches = _patch_paths(
            tmp_path / "nope.jsonl",
            tmp_path / "nope.json",
            tmp_path / "nope2.json",
            tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        assert result["failed_writes"]["recovered"] == 0
        assert result["canvas_events"]["recovered"] == 0
        assert result["learning_memories"]["recovered"] == 0

    @pytest.mark.asyncio
    async def test_malformed_jsonl_entries_skipped(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Malformed JSONL lines are preserved as pending (not lost)."""
        content = 'NOT VALID JSON\n{"timestamp":"2026-02-07","concept":"X","concept_id":"c1","canvas_name":"test","score":80,"event_type":"scoring","error_reason":"err"}\n'
        tmp_failed_writes.write_text(content, encoding="utf-8")

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        # 1 recovered (valid entry), 1 pending (malformed)
        assert result["failed_writes"]["recovered"] == 1
        assert result["failed_writes"]["pending"] == 1

    @pytest.mark.asyncio
    async def test_malformed_canvas_events_json(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """Malformed canvas events file produces zero-count result."""
        tmp_canvas_events.write_text("NOT JSON", encoding="utf-8")

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        assert result["canvas_events"]["recovered"] == 0

    @pytest.mark.asyncio
    async def test_partial_failure_continues(
        self, sync_service, mock_neo4j, tmp_failed_writes,
        tmp_canvas_events, tmp_learning_memories, tmp_path,
    ):
        """If one file sync errors, other files still sync."""
        # Set up canvas events to error
        tmp_canvas_events.write_text("CORRUPT", encoding="utf-8")

        # Set up learning memories to succeed
        data = {
            "memories": [
                {
                    "canvas_name": "math.canvas",
                    "concept": "Algebra",
                    "score": 90,
                    "timestamp": "2026-02-07T10:00:00",
                },
            ],
            "metadata": {},
        }
        tmp_learning_memories.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

        patches = _patch_paths(
            tmp_failed_writes, tmp_canvas_events,
            tmp_learning_memories, tmp_path / "sync_checkpoint.json",
        )
        with patch.multiple("app.services.fallback_sync_service", **patches):
            result = await sync_service.sync_all_fallbacks()

        # Canvas events failed to parse, but learning memories still synced
        assert result["canvas_events"]["recovered"] == 0
        assert result["learning_memories"]["recovered"] == 1

    @pytest.mark.asyncio
    async def test_entry_without_concept_skipped(self, sync_service, mock_neo4j):
        """Scoring entry with no concept is skipped."""
        entry = {
            "timestamp": "2026-02-07T10:00:00",
            "concept_id": "",
            "concept": "",
            "canvas_name": "test",
            "score": 80,
        }
        result = await sync_service._replay_scoring_entry_to_neo4j(entry)
        assert result is False

    @pytest.mark.asyncio
    async def test_edge_event_without_node_ids_skipped(
        self, sync_service, mock_neo4j,
    ):
        """Edge event missing from/to node IDs is skipped."""
        event = {
            "event_type": "edge_sync",
            "canvas_name": "test",
            "edge_id": "e1",
            "from_node_id": "",
            "to_node_id": "",
        }
        result = await sync_service._replay_canvas_event_to_neo4j(event)
        assert result is False

    @pytest.mark.asyncio
    async def test_learning_memory_without_concept_skipped(
        self, sync_service, mock_neo4j,
    ):
        """Learning memory with empty concept is skipped."""
        mem = {
            "canvas_name": "test",
            "concept": "",
            "score": None,
            "timestamp": "2026-02-07T10:00:00",
        }
        result = await sync_service._replay_learning_memory_to_neo4j(mem)
        assert result is False
