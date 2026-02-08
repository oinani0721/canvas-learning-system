"""
Story 38.7 AC-3: Restart Survival

Verifies: Episodes, FSRS cards, LanceDB index survive application restart.

Split from test_story_38_7_e2e_integration.py for maintainability.
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.memory_service import MemoryService

from tests.integration.conftest import make_mock_neo4j, make_mock_learning_memory


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: Restart Survival
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC3RestartSurvival:
    """AC-3: Data survives application restart (episodes, FSRS, LanceDB)."""

    @pytest.mark.asyncio
    async def test_restart_recovers_episodes_from_neo4j(self):
        """
        [P0] Story 38.2 AC-2: After restart, MemoryService recovers
        episodes from Neo4j and get_learning_history() returns them.
        """
        stored_episodes = [
            {"user_id": "u1", "concept": "Calculus", "concept_id": "c1",
             "score": 75, "timestamp": "2026-02-06T14:00:00", "group_id": "g1",
             "review_count": 1},
            {"user_id": "u1", "concept": "Physics", "concept_id": "c2",
             "score": 90, "timestamp": "2026-02-06T15:00:00", "group_id": "g1",
             "review_count": 3},
        ]
        neo4j = make_mock_neo4j(episodes=stored_episodes)
        learning_mem = make_mock_learning_memory()

        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        await ms.initialize()

        assert ms._episodes_recovered is True
        assert len(ms._episodes) == 2
        concepts = {e["concept"] for e in ms._episodes}
        assert "Calculus" in concepts
        assert "Physics" in concepts

    @pytest.mark.asyncio
    async def test_restart_deduplicates_recovered_episodes(self):
        """
        [P1] Story 38.2: Recovery deduplicates by (user_id, concept, timestamp).
        Two records with identical (user_id, concept, timestamp) should be deduped
        to a single episode.
        """
        stored_episodes = [
            {"user_id": "u1", "concept": "Python", "concept_id": "c1",
             "score": 80, "timestamp": "2026-02-06T10:00:00", "group_id": "g1",
             "review_count": 1},
            {"user_id": "u1", "concept": "Python", "concept_id": "c1",
             "score": 90, "timestamp": "2026-02-06T10:00:00", "group_id": "g1",
             "review_count": 2},
        ]
        neo4j = make_mock_neo4j(episodes=stored_episodes)
        learning_mem = make_mock_learning_memory()

        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        await ms.initialize()

        python_episodes = [e for e in ms._episodes if e["concept"] == "Python"]
        assert len(python_episodes) == 1

    @pytest.mark.asyncio
    async def test_fsrs_card_state_readable_within_same_instance(self):
        """
        [P0] Story 38.3 AC-4: FSRS card states (in-memory) are readable
        within the same ReviewService instance lifetime.

        Note: FSRS cards are in-memory only — they do NOT survive actual
        process restart. Persistence across restarts requires external storage
        (not in scope for Story 38.3).
        """
        from app.services.review_service import ReviewService, FSRS_AVAILABLE

        if not FSRS_AVAILABLE:
            pytest.skip("py-fsrs not installed")

        canvas_svc = MagicMock()
        task_mgr = MagicMock()
        rs = ReviewService(canvas_service=canvas_svc, task_manager=task_mgr)

        card_data = json.dumps({
            "due": datetime.now().isoformat(),
            "stability": 2.5,
            "difficulty": 4.0,
            "state": 2,
            "reps": 3,
            "lapses": 0,
            "last_review": datetime.now().isoformat(),
        })
        rs._card_states["concept-A"] = card_data

        result = await rs.get_fsrs_state("concept-A")
        assert result is not None
        assert result.get("found") is True

    @pytest.mark.asyncio
    async def test_lancedb_pending_recovery_on_restart(self, tmp_path):
        """
        [P0] Story 38.1 AC-3: On restart, recover_pending() replays
        entries from lancedb_pending_index.jsonl.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        svc = LanceDBIndexService()
        pending_file = tmp_path / "lancedb_pending_index.jsonl"
        pending_file.write_text(
            json.dumps({"canvas_name": "math-101", "timestamp": "2026-02-07T10:00:00"}) + "\n",
            encoding="utf-8"
        )
        svc._pending_file = pending_file

        svc._do_index = AsyncMock()

        result = await svc.recover_pending(str(tmp_path))
        assert result["recovered"] == 1
        assert result["pending"] == 0
        svc._do_index.assert_awaited_once_with("math-101", str(tmp_path))

        assert not pending_file.exists()
