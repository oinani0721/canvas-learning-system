# Canvas Learning System - EPIC-33 Batch Pipeline E2E Tests
# Story 33.13: EPIC Documentation Sync + E2E Test Coverage
"""
E2E tests for the complete EPIC-33 batch processing pipeline.

Tests cover:
- AC-33.13.4: Full batch flow (analyze → confirm → poll → complete)
- AC-33.13.5: Cancel flow (start → cancel → verify cancelled)

Uses proper patching to inject test settings (bypasses @lru_cache issue)
and mocks external dependencies (_perform_clustering, Neo4j, GeminiClient).
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.config import Settings

# Import shared helpers from conftest (autouse _reset_e2e_singletons applies automatically)
from tests.conftest import simulate_async_delay
from tests.e2e.conftest import mock_perform_clustering, make_lightweight_ensure_deps


# =============================================================================
# Helpers
# =============================================================================

def _make_test_settings(canvas_base_path: str) -> Settings:
    """Create isolated test settings with custom canvas base path."""
    return Settings(
        PROJECT_NAME="Canvas E2E Test",
        VERSION="test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="*",
        CANVAS_BASE_PATH=canvas_base_path,
    )


def _create_canvas(base_dir: Path, name: str, node_count: int) -> Path:
    """Create a test .canvas file with yellow (color '6') text nodes."""
    patterns = [
        "What is concept {i}? Define the core definition.",
        "Compare concept {i} and concept {j}.",
        "How to understand concept {i}? Explain in detail.",
        "Give an example of concept {i} in practice.",
        "How to memorize concept {i}? Any tricks?",
        "Deep analysis of concept {i} principles.",
    ]
    nodes = []
    for i in range(node_count):
        text = patterns[i % len(patterns)].format(i=i, j=(i + 1) % max(node_count, 1))
        nodes.append({
            "id": f"node-{i:03d}",
            "type": "text",
            "color": "6",
            "text": text,
            "x": (i % 5) * 250,
            "y": (i // 5) * 150,
            "width": 220,
            "height": 100,
        })
    canvas_data = {"nodes": nodes, "edges": []}
    canvas_file = base_dir / name
    canvas_file.write_text(json.dumps(canvas_data, ensure_ascii=False), encoding="utf-8")
    return canvas_file


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def canvas_dir(tmp_path):
    """Return a clean directory for canvas files (ASCII-safe path)."""
    d = tmp_path / "canvases"
    d.mkdir()
    return d


# =============================================================================
# AC-33.13.4: Full Batch Pipeline E2E
# =============================================================================

class TestFullBatchPipeline:
    """
    E2E test: POST analyze → POST confirm → GET progress → completed.

    [AC-33.13.4]
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_full_batch_flow_analyze_confirm_poll_complete(self, canvas_dir):
        """
        Complete happy-path flow:
        1. POST /api/v1/canvas/intelligent-parallel  — analyze & group nodes
        2. POST /api/v1/canvas/intelligent-parallel/confirm — start batch
        3. GET  /api/v1/canvas/intelligent-parallel/{session_id} — poll until done
        4. Verify final status is completed and progress reported
        """
        from app.services.agent_service import AgentResult, AgentType

        # Create 10-node canvas
        canvas_file = _create_canvas(canvas_dir, "test10.canvas", 10)
        canvas_relative = canvas_file.name  # "test10.canvas"

        test_settings = _make_test_settings(str(canvas_dir))

        # Fast mock agent that returns AgentResult
        async def fast_agent(*args, **kwargs):
            at_str = kwargs.get("agent_type", args[0] if args else "basic-decomposition")
            await simulate_async_delay(0.005)
            try:
                at = AgentType(at_str)
            except ValueError:
                at = AgentType.BASIC_DECOMPOSITION
            return AgentResult(agent_type=at, success=True,
                               result={"content": f"mock {at_str}"})

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
            patch("app.services.agent_service.AgentService.call_agent",
                  side_effect=fast_agent),
            patch("app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
                  new=make_lightweight_ensure_deps(test_settings, fast_agent)),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # Step 1: Analyze
                resp = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={"canvas_path": canvas_relative, "target_color": "6"},
                )
                assert resp.status_code == 200, f"Analyze failed: {resp.text}"
                data = resp.json()
                assert "groups" in data
                assert data["total_nodes"] > 0
                groups = data["groups"]
                assert len(groups) > 0

                # Verify group structure
                for g in groups:
                    assert "group_id" in g
                    assert "recommended_agent" in g
                    assert "nodes" in g

                # Step 2: Confirm
                groups_config = [
                    {
                        "group_id": g["group_id"],
                        "agent_type": g["recommended_agent"],
                        "node_ids": [n["node_id"] for n in g["nodes"]],
                    }
                    for g in groups
                ]
                resp = await client.post(
                    "/api/v1/canvas/intelligent-parallel/confirm",
                    json={"canvas_path": canvas_relative, "groups": groups_config},
                )
                assert resp.status_code == 202, f"Confirm failed: {resp.text}"
                session_id = resp.json()["session_id"]
                assert session_id

                # Step 3: Poll until complete
                final = None
                for _ in range(200):
                    resp = await client.get(
                        f"/api/v1/canvas/intelligent-parallel/{session_id}"
                    )
                    assert resp.status_code == 200
                    final = resp.json()
                    if final["status"] in ("completed", "partial_failure", "failed"):
                        break
                    await simulate_async_delay(0.05)

                # Step 4: Verify completion
                assert final is not None, "Session did not complete within timeout"
                assert final["status"] in ("completed", "partial_failure"), \
                    f"Expected completed/partial_failure, got {final['status']}"
                assert final["progress_percent"] >= 0

                # Step 5: Verify result files are reported (AC-33.13.4 step 5)
                assert "groups" in final, "Progress response should contain groups"
                total_results = 0
                for group in final.get("groups", []):
                    results = group.get("results", [])
                    total_results += len(results)
                    for result in results:
                        assert "node_id" in result, "Each result should have node_id"
                assert total_results > 0, \
                    f"Should have node results but got {total_results}"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_analyze_returns_correct_structure(self, canvas_dir):
        """Verify /intelligent-parallel analyze response has correct schema."""
        canvas_file = _create_canvas(canvas_dir, "schema_test.canvas", 8)
        test_settings = _make_test_settings(str(canvas_dir))

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={"canvas_path": canvas_file.name, "target_color": "6"},
                )
                assert resp.status_code == 200
                data = resp.json()
                assert "canvas_path" in data
                assert "total_nodes" in data
                assert "groups" in data
                assert isinstance(data["groups"], list)
                # total_nodes matches sum of group nodes
                total = sum(len(g["nodes"]) for g in data["groups"])
                assert data["total_nodes"] == total


# =============================================================================
# AC-33.13.5: Cancel Flow E2E
# =============================================================================

class TestCancelFlow:
    """
    E2E test: start batch → cancel → verify cancelled status.

    [AC-33.13.5]
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_cancel_running_session(self, canvas_dir):
        """
        Cancel flow:
        1. Analyze + confirm to start a batch session
        2. POST /cancel/{session_id}
        3. Verify status becomes 'cancelled'
        """
        from app.services.agent_service import AgentResult, AgentType

        canvas_file = _create_canvas(canvas_dir, "cancel_test.canvas", 15)
        test_settings = _make_test_settings(str(canvas_dir))

        # Slow agent to give time for cancellation
        async def slow_agent(*args, **kwargs):
            at_str = kwargs.get("agent_type", args[0] if args else "basic-decomposition")
            await simulate_async_delay(0.5)  # 500ms per node
            try:
                at = AgentType(at_str)
            except ValueError:
                at = AgentType.BASIC_DECOMPOSITION
            return AgentResult(agent_type=at, success=True,
                               result={"content": f"mock {at_str}"})

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
            patch("app.services.agent_service.AgentService.call_agent",
                  side_effect=slow_agent),
            patch("app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
                  new=make_lightweight_ensure_deps(test_settings, slow_agent)),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # Step 1: Analyze + Confirm
                resp = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={"canvas_path": canvas_file.name, "target_color": "6"},
                )
                groups = resp.json()["groups"]
                groups_config = [
                    {
                        "group_id": g["group_id"],
                        "agent_type": g["recommended_agent"],
                        "node_ids": [n["node_id"] for n in g["nodes"]],
                    }
                    for g in groups
                ]
                resp = await client.post(
                    "/api/v1/canvas/intelligent-parallel/confirm",
                    json={"canvas_path": canvas_file.name, "groups": groups_config},
                )
                session_id = resp.json()["session_id"]

                # Step 2: Wait briefly then cancel
                await simulate_async_delay(0.3)
                resp = await client.post(
                    f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
                )
                assert resp.status_code == 200, f"Cancel failed: {resp.text}"
                cancel_data = resp.json()
                assert "completed_count" in cancel_data

                # Step 3: Verify status is cancelled
                resp = await client.get(
                    f"/api/v1/canvas/intelligent-parallel/{session_id}"
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "cancelled"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_session_returns_404(self, canvas_dir):
        """Cancel a session that doesn't exist → 404."""
        test_settings = _make_test_settings(str(canvas_dir))

        with patch("app.dependencies.get_settings", return_value=test_settings):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/canvas/intelligent-parallel/cancel/nonexistent-id"
                )
                assert resp.status_code == 404


# =============================================================================
# Helper: Lightweight _ensure_async_deps replacement
# =============================================================================

def make_lightweight_ensure_deps(settings, agent_mock):
    """
    Factory returning an async function that replaces _ensure_async_deps.

    Injects lightweight mock dependencies (no Neo4j, no real GeminiClient)
    so the batch pipeline can execute end-to-end with mocked agents.
    """

    async def _lightweight_ensure_deps():
        import app.api.v1.endpoints.intelligent_parallel as ep_mod

        if ep_mod._deps_initialized:
            return

        service = ep_mod.get_service()

        from app.services.batch_orchestrator import BatchOrchestrator
        from app.services.agent_service import AgentService
        from app.services.canvas_service import CanvasService
        from app.services.session_manager import SessionManager

        canvas_base = str(settings.canvas_base_path) if settings.canvas_base_path else None
        canvas_service = CanvasService(canvas_base_path=canvas_base)

        # Create AgentService with mocked gemini_client
        agent_service = AgentService(
            gemini_client=MagicMock(),
            canvas_service=canvas_service,
        )
        # Patch call_agent on the instance
        agent_service.call_agent = agent_mock

        session_manager = SessionManager.get_instance()

        batch_orchestrator = BatchOrchestrator(
            session_manager=session_manager,
            agent_service=agent_service,
            canvas_service=canvas_service,
            vault_path=canvas_base,
        )

        service._batch_orchestrator = batch_orchestrator
        service._agent_service = agent_service
        service._canvas_service = canvas_service

        ep_mod._deps_initialized = True

    return _lightweight_ensure_deps
