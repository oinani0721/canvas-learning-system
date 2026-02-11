# Canvas Learning System - Story 30.12 Tests
# Agent 触发完整性补齐
"""
Story 30.12 - Agent Trigger Completion Tests

Tests that all 14 agents in AGENT_MEMORY_MAPPING have corresponding
trigger code or are marked as reserved.

[Source: docs/stories/30.12.agent-trigger-completion.story.md]
"""

import ast
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Task 1: hint-generation trigger
# ============================================================================

class TestHintGenerationTrigger:
    """AC-30.12.1: hint-generation triggers memory write after success."""

    @pytest.fixture
    def mock_agent_service(self):
        svc = MagicMock()
        svc._trigger_memory_write = AsyncMock()
        result = MagicMock()
        result.success = True
        result.data = {"hint_text": "这是一个提示", "hint_level": "basic"}
        svc.call_agent = AsyncMock(return_value=result)
        return svc

    @pytest.fixture
    def verification_service(self, mock_agent_service):
        from app.services.verification_service import VerificationService
        vs = VerificationService.__new__(VerificationService)
        vs._sessions = {}
        vs._progress = {}
        vs._agent_service = mock_agent_service
        vs._canvas_service = None
        vs._context_enrichment_service = None
        vs.RAG_TIMEOUT = 5.0
        vs.VERIFICATION_AI_TIMEOUT = 15.0
        return vs

    @pytest.mark.asyncio
    async def test_hint_generation_triggers_memory_write(self, verification_service, mock_agent_service):
        """After successful hint generation, _trigger_memory_write is called."""
        # Patch internal methods that generate_hint_with_rag calls
        with patch.object(verification_service, '_get_enriched_context',
                          new_callable=AsyncMock, return_value={"rag": None, "graph": None, "fsrs": None}):
            result = await verification_service.generate_hint_with_rag(
                concept="二次方程",
                user_answer="不知道",
                attempt_number=1,
                canvas_name="math.canvas",
            )

        assert result == "这是一个提示"
        mock_agent_service._trigger_memory_write.assert_called_once()
        call_kwargs = mock_agent_service._trigger_memory_write.call_args
        assert call_kwargs[1]["agent_type"] == "hint-generation"
        assert call_kwargs[1]["concept"] == "二次方程"

    @pytest.mark.asyncio
    async def test_hint_memory_write_failure_non_blocking(self, verification_service, mock_agent_service):
        """Memory write failure doesn't block hint generation return."""
        mock_agent_service._trigger_memory_write = AsyncMock(side_effect=Exception("write failed"))

        with patch.object(verification_service, '_get_enriched_context',
                          new_callable=AsyncMock, return_value={"rag": None, "graph": None, "fsrs": None}):
            result = await verification_service.generate_hint_with_rag(
                concept="二次方程",
                user_answer="不知道",
                attempt_number=1,
                canvas_name="math.canvas",
            )

        # Hint should still be returned despite memory write failure
        assert result == "这是一个提示"


# ============================================================================
# Task 2: canvas-orchestrator trigger
# ============================================================================

class TestCanvasOrchestratorTrigger:
    """AC-30.12.2: canvas-orchestrator triggers on session start."""

    def test_canvas_orchestrator_trigger_in_code(self):
        """start_batch_session contains canvas-orchestrator memory write trigger."""
        source_file = Path(__file__).parent.parent.parent / "app" / "services" / "batch_orchestrator.py"
        code = source_file.read_text(encoding="utf-8")
        assert 'agent_type="canvas-orchestrator"' in code, (
            "batch_orchestrator.py should trigger memory write for canvas-orchestrator"
        )

    def test_canvas_orchestrator_trigger_in_start_method(self):
        """The trigger is in start_batch_session, not elsewhere."""
        source_file = Path(__file__).parent.parent.parent / "app" / "services" / "batch_orchestrator.py"
        code = source_file.read_text(encoding="utf-8")
        # Find start_batch_session method and check canvas-orchestrator is within it
        start_idx = code.find("async def start_batch_session")
        # Find next method definition after start_batch_session
        next_def_idx = code.find("\n    async def ", start_idx + 1)
        if next_def_idx == -1:
            next_def_idx = len(code)
        method_code = code[start_idx:next_def_idx]
        assert 'canvas-orchestrator' in method_code, (
            "canvas-orchestrator trigger should be in start_batch_session method"
        )


# ============================================================================
# Task 3: Reserved agents
# ============================================================================

class TestReservedAgents:
    """AC-30.12.3: Reserved agents are annotated."""

    def test_reserved_agents_annotated(self):
        """review-board-agent-selector and graphiti-memory-agent have Reserved comment."""
        mapping_file = Path(__file__).parent.parent.parent / "app" / "core" / "agent_memory_mapping.py"
        content = mapping_file.read_text(encoding="utf-8")
        assert "Reserved: no active call site yet" in content


# ============================================================================
# Task 4: 14/14 Mapping Completeness
# ============================================================================

class TestMappingCompleteness:
    """AC-30.12.4: All 14 agents have trigger code or reserved annotation."""

    def test_all_15_agents_in_mapping(self):
        """AGENT_MEMORY_MAPPING has exactly 15 entries (C1 fix: +hint-generation)."""
        from app.core.agent_memory_mapping import AGENT_MEMORY_MAPPING
        assert len(AGENT_MEMORY_MAPPING) == 15

    def test_trigger_code_or_reserved_for_each_agent(self):
        """Each mapped agent has trigger code in codebase or is marked reserved."""
        from app.core.agent_memory_mapping import AGENT_MEMORY_MAPPING

        services_dir = Path(__file__).parent.parent.parent / "app" / "services"
        core_dir = Path(__file__).parent.parent.parent / "app" / "core"

        # Read all service files
        service_code = ""
        for py_file in services_dir.glob("*.py"):
            service_code += py_file.read_text(encoding="utf-8")

        # Read mapping file for reserved annotations
        mapping_code = (core_dir / "agent_memory_mapping.py").read_text(encoding="utf-8")

        reserved_agents = {"review-board-agent-selector", "graphiti-memory-agent"}

        for agent_name in AGENT_MEMORY_MAPPING:
            if agent_name in reserved_agents:
                assert "Reserved" in mapping_code, f"{agent_name} should be marked as Reserved"
            else:
                # Agent should appear in service code with trigger_memory_write context
                assert agent_name in service_code, (
                    f"Agent '{agent_name}' not found in any service code"
                )
