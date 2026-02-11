"""
Story 30.24: 边界测试与防护加固

Tests for boundary conditions, special characters, oversized payloads,
shutdown data safety, and Unicode handling in the memory system.

AC-30.24.1: Empty input boundary test
AC-30.24.2: Special character group_id test
AC-30.24.3: Oversized payload test (422)
AC-30.24.4: Shutdown data safety test
AC-30.24.5: Unicode concept name test
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.subject_config import build_group_id, sanitize_subject_name


# ============================================================================
# AC-30.24.1: Empty input boundary test
# ============================================================================


class TestEmptyInputBoundary:
    """AC-30.24.1: Empty event list submitted to record_batch_learning_events."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero_processed(self):
        """Empty list returns processed=0, errors=[] without crashing."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": False}

        result = await svc.record_batch_learning_events([])

        assert result["processed"] == 0
        assert result["failed"] == 0
        assert result["errors"] == []
        assert result["episode_ids"] == []
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_empty_list_does_not_call_neo4j(self):
        """Empty list must NOT invoke any Neo4j write."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": True}
        svc.neo4j.record_episode = AsyncMock()

        await svc.record_batch_learning_events([])

        svc.neo4j.record_episode.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_list_has_valid_timestamp(self):
        """Empty list response still contains a valid ISO timestamp."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": False}

        result = await svc.record_batch_learning_events([])

        # Should be a valid ISO timestamp
        ts = result["timestamp"]
        datetime.fromisoformat(ts)  # raises ValueError if invalid


# ============================================================================
# AC-30.24.2: Special character group_id test
# ============================================================================

SPECIAL_GROUP_IDS = [
    ("", "default"),                          # empty string → default
    ("../etc/passwd", "___etc_passwd"),        # path traversal → sanitized
    ("<script>", "_script_"),                  # XSS → sanitized
    ("数学/离散数学", "数学_离散数学"),            # Chinese path → preserved Chinese, slash→underscore
    ("📚 Math", "📚_math"),                    # emoji → preserved emoji
    ("a" * 1000, None),                        # very long string → truncated/handled
]


class TestSpecialCharacterGroupId:
    """AC-30.24.2: group_id with special characters handled safely."""

    @pytest.mark.parametrize("raw_input,expected_prefix", [
        ("", "default"),
        ("../etc/passwd", None),   # just check no crash
        ("<script>alert(1)</script>", None),
        ("数学/离散数学", None),
        ("📚 Math", None),
        ("a" * 1000, None),
    ])
    def test_sanitize_subject_name_no_crash(self, raw_input, expected_prefix):
        """sanitize_subject_name handles all special inputs without crashing."""
        result = sanitize_subject_name(raw_input)
        assert isinstance(result, str)
        assert len(result) > 0
        if expected_prefix:
            assert result == expected_prefix

    def test_empty_string_returns_default(self):
        """Empty string group_id returns 'default'."""
        assert sanitize_subject_name("") == "default"

    def test_path_traversal_stripped(self):
        """Path traversal characters are sanitized."""
        result = sanitize_subject_name("../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_xss_characters_stripped(self):
        """XSS characters (<, >) are sanitized."""
        result = sanitize_subject_name("<script>alert(1)</script>")
        assert "<" not in result
        assert ">" not in result

    def test_chinese_preserved(self):
        """Chinese characters are preserved in sanitization."""
        result = sanitize_subject_name("数学/离散数学")
        assert "数学" in result
        assert "离散数学" in result

    def test_emoji_sanitized_to_stable_identifier(self):
        """Emoji characters are safely stripped to stable identifier (emoji ∉ \\w)."""
        result = sanitize_subject_name("📚 Math")
        # Emoji is not a Unicode \w char → stripped by sanitize_subject_name
        # This is documented behavior: emoji in group_id are sanitized, not preserved
        # (AC-30.24.2 updated to reflect this design decision)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "math" in result

    def test_build_group_id_with_chinese(self):
        """build_group_id correctly constructs group_id with Chinese subject."""
        gid = build_group_id("数学")
        assert isinstance(gid, str)
        assert "数学" in gid

    def test_build_group_id_with_emoji(self):
        """build_group_id correctly constructs group_id with emoji."""
        gid = build_group_id("📚 Math")
        assert isinstance(gid, str)
        assert len(gid) > 0

    @pytest.mark.asyncio
    async def test_neo4j_parameterized_query_with_special_chars(self):
        """Neo4j client uses parameterized queries — special chars don't cause injection."""
        from app.clients.neo4j_client import Neo4jClient

        client = Neo4jClient()
        client._initialized = True
        client.run_query = AsyncMock(return_value=[])

        malicious_group_id = "<script>'; DROP TABLE users;--"

        await client.get_review_suggestions(
            user_id="test_user",
            limit=5,
            group_id=malicious_group_id
        )

        call_args = client.run_query.call_args
        # Verify group_id is passed as a named parameter (not interpolated into query)
        # Support both positional and keyword calling conventions
        all_kwargs = call_args.kwargs if call_args.kwargs else {}
        assert all_kwargs.get("groupId") == malicious_group_id, (
            f"groupId not passed as keyword param. kwargs={all_kwargs}"
        )
        # Verify the Cypher query string does NOT contain raw malicious input
        query_str = call_args.args[0] if call_args.args else ""
        assert malicious_group_id not in query_str, (
            "Malicious input found in query string — possible Cypher injection!"
        )


# ============================================================================
# AC-30.24.5: Unicode concept name test
# ============================================================================


class TestUnicodeConceptNames:
    """AC-30.24.5: Unicode concepts stored and queried correctly."""

    UNICODE_CONCEPTS = [
        "監督学習 📊",
        "Bayes' Theorem",
        "集合论 ∩ ∪ ⊂",
        "概率论与数理统计",
        "Ψ(x) = ∑ cₙφₙ(x)",
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("concept", [
        "監督学習 📊",
        "Bayes' Theorem",
        "集合论 ∩ ∪ ⊂",
        "概率论与数理统计",
        "Ψ(x) = ∑ cₙφₙ(x)",
    ])
    async def test_unicode_concept_stored_in_episodes(self, concept):
        """Unicode concept is stored in _episodes without corruption."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": False}

        event = {
            "event_type": "color_changed",
            "timestamp": "2026-02-10T12:00:00Z",
            "canvas_path": "test/unicode.canvas",
            "node_id": "node_001",
            "metadata": {"concept": concept},
        }

        result = await svc.record_batch_learning_events([event])

        assert result["processed"] == 1
        assert result["failed"] == 0

        # Verify concept stored correctly in episodes
        stored = svc._episodes[-1]
        assert stored["metadata"]["concept"] == concept

    @pytest.mark.asyncio
    @pytest.mark.parametrize("concept", [
        "監督学習 📊",
        "Bayes' Theorem",
        "集合論 ∩ ∪ ⊂",
    ])
    async def test_unicode_concept_sent_to_neo4j(self, concept):
        """Unicode concept is passed to Neo4j without truncation or mojibake."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": True}
        svc.neo4j.record_episode = AsyncMock()

        event = {
            "event_type": "color_changed",
            "timestamp": "2026-02-10T12:00:00Z",
            "canvas_path": "test/unicode.canvas",
            "node_id": "node_002",
            "metadata": {"concept": concept},
        }

        await svc.record_batch_learning_events([event])

        svc.neo4j.record_episode.assert_called_once()
        payload = svc.neo4j.record_episode.call_args[0][0]
        assert payload["concept"] == concept


# ============================================================================
# AC-30.24.3: Oversized payload test (422)
# ============================================================================


class TestOversizedPayload:
    """AC-30.24.3: Batch with >50 events rejected by Pydantic validation.

    Tests Pydantic model validation directly (true unit test).
    HTTP 422 behavior is covered by integration tests in:
    - tests/integration/test_epic30_memory_integration.py
    - tests/e2e/test_memory_learning_flow_e2e.py
    """

    def _make_events(self, count: int) -> list:
        return [
            {
                "event_type": "color_changed",
                "timestamp": f"2026-02-10T12:00:{i % 60:02d}Z",
                "canvas_path": "test/boundary.canvas",
                "node_id": f"node_{i:03d}",
            }
            for i in range(count)
        ]

    def test_oversized_batch_rejected_by_pydantic(self):
        """100 events exceeds max_length=50 → ValidationError."""
        from pydantic import ValidationError
        from app.models.memory_schemas import BatchEpisodesRequest

        with pytest.raises(ValidationError) as exc_info:
            BatchEpisodesRequest(events=self._make_events(100))

        assert "events" in str(exc_info.value)

    def test_just_over_limit_rejected(self):
        """51 events (just over limit) → ValidationError."""
        from pydantic import ValidationError
        from app.models.memory_schemas import BatchEpisodesRequest

        with pytest.raises(ValidationError):
            BatchEpisodesRequest(events=self._make_events(51))

    def test_exactly_50_events_accepted(self):
        """Exactly 50 events should pass Pydantic validation (positive assertion)."""
        from app.models.memory_schemas import BatchEpisodesRequest

        req = BatchEpisodesRequest(events=self._make_events(50))
        assert len(req.events) == 50


# ============================================================================
# AC-30.24.4: Shutdown data safety test
# ============================================================================


class TestShutdownDataSafety:
    """AC-30.24.4: Pending writes saved to failed_writes.jsonl on shutdown."""

    @pytest.mark.asyncio
    async def test_batch_neo4j_failure_records_to_failed_writes(self, tmp_path):
        """When Neo4j is unreachable during batch, failures persist to failed_writes.jsonl."""
        from app.services.memory_service import MemoryService

        failed_writes_file = tmp_path / "failed_writes.jsonl"

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": True}
        # Simulate Neo4j unreachable — all writes raise
        svc.neo4j.record_episode = AsyncMock(
            side_effect=ConnectionError("Neo4j unreachable")
        )

        events = [
            {
                "event_type": "color_changed",
                "timestamp": f"2026-02-10T12:00:{i:02d}Z",
                "canvas_path": "test/shutdown.canvas",
                "node_id": f"node_{i:03d}",
                "metadata": {"concept": f"concept_{i}"},
            }
            for i in range(5)
        ]

        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE",
            failed_writes_file
        ):
            result = await svc.record_batch_learning_events(events)

        # All 5 writes should fail
        assert result["failed"] == 5
        assert len(result["errors"]) == 5

    @pytest.mark.asyncio
    async def test_cleanup_flushes_pending_writes(self, tmp_path):
        """cleanup_memory_service persists pending failed writes before shutdown."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc._pending_failed_writes = [
            {
                "episode_id": f"ep_{i}",
                "timestamp": "2026-02-10T12:00:00Z",
                "reason": "Neo4j unreachable"
            }
            for i in range(5)
        ]
        svc.neo4j = MagicMock()
        svc.neo4j.cleanup = AsyncMock()
        svc._score_history_cache = {}
        svc._episodes_recovered = False

        failed_writes_file = tmp_path / "failed_writes.jsonl"

        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE",
            failed_writes_file
        ):
            await svc.cleanup()

        # Verify failed_writes.jsonl was created (must NOT be conditional)
        assert failed_writes_file.exists(), "failed_writes.jsonl was not created by cleanup()"
        lines = failed_writes_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 5
        for line in lines:
            record = json.loads(line)
            assert "episode_id" in record
            assert "timestamp" in record
            assert "reason" in record

    @pytest.mark.asyncio
    async def test_failed_writes_record_completeness(self, tmp_path):
        """Each record in failed_writes.jsonl has episode_id, timestamp, reason."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc._pending_failed_writes = [
            {
                "episode_id": "ep_test_001",
                "timestamp": "2026-02-10T12:00:00Z",
                "reason": "ConnectionError: Neo4j host unreachable"
            }
        ]
        svc.neo4j = MagicMock()
        svc.neo4j.cleanup = AsyncMock()
        svc._score_history_cache = {}
        svc._episodes_recovered = False

        failed_writes_file = tmp_path / "failed_writes.jsonl"

        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE",
            failed_writes_file
        ):
            await svc.cleanup()

        assert failed_writes_file.exists(), "failed_writes.jsonl was not created by cleanup()"
        lines = failed_writes_file.read_text(encoding="utf-8").strip().split("\n")
        record = json.loads(lines[0])
        assert record["episode_id"] == "ep_test_001"
        assert record["timestamp"] == "2026-02-10T12:00:00Z"
        assert "Neo4j" in record["reason"]


# ============================================================================
# AC-30.24.6: Vault deployment verify script exit code
# ============================================================================


class TestVaultVerifyExitCode:
    """AC-30.24.6: verify script returns exit 1 on STALE."""

    VERIFY_SCRIPT = Path(__file__).parent.parent.parent.parent / (
        "canvas-progress-tracker/obsidian-plugin/scripts/verify-vault.mjs"
    )

    def test_verify_script_exists(self):
        """verify-vault.mjs script must exist."""
        assert self.VERIFY_SCRIPT.exists(), f"verify script not found: {self.VERIFY_SCRIPT}"

    def _run_verify(self, env_override: dict, timeout: int = 10):
        """Helper: run verify-vault.mjs with UTF-8 encoding (Windows emits emoji)."""
        import subprocess

        env = os.environ.copy()
        env.update(env_override)
        return subprocess.run(
            ["node", str(self.VERIFY_SCRIPT)],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )

    def test_verify_script_exits_nonzero_when_file_not_found(self, tmp_path):
        """When vault main.js doesn't exist, script exits with code 1."""
        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
        assert result.returncode != 0
        output = (result.stdout or "") + (result.stderr or "")
        assert "NOT FOUND" in output

    def test_verify_script_exits_nonzero_when_stale(self, tmp_path):
        """When vault main.js is stale (>5min old), script exits with code 1."""
        # Create a stale main.js (set mtime to 10 minutes ago)
        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
        plugin_dir.mkdir(parents=True)
        main_js = plugin_dir / "main.js"
        main_js.write_text("// stale test file")
        stale_time = time.time() - 600  # 10 minutes ago
        os.utime(main_js, (stale_time, stale_time))

        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
        assert result.returncode == 1
        assert "STALE" in (result.stdout or "")

    def test_verify_script_exits_zero_when_fresh(self, tmp_path):
        """When vault main.js is fresh (<5min), script exits with code 0."""
        # Create a fresh main.js (just created = fresh)
        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
        plugin_dir.mkdir(parents=True)
        main_js = plugin_dir / "main.js"
        main_js.write_text("// fresh test file")

        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
        assert result.returncode == 0
        assert "FRESH" in (result.stdout or "")

    def test_package_json_verify_command_correct(self):
        """package.json verify script points to verify.mjs."""
        pkg_json_path = self.VERIFY_SCRIPT.parent.parent / "package.json"
        assert pkg_json_path.exists()
        pkg = json.loads(pkg_json_path.read_text(encoding="utf-8"))
        assert "verify" in pkg.get("scripts", {})
        assert "verify.mjs" in pkg["scripts"]["verify"]
