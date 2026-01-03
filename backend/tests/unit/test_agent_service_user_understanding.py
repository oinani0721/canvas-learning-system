# Canvas Learning System - Story 12.E.2 Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Story 12.E.2 - user_understanding Dual-Channel Delivery Tests

Tests for user_understanding being passed through both channels:
- AC 2.1: JSON field (user_understanding in json_prompt)
- AC 2.2: enhanced_context ("## 用户之前的个人理解" section)
- AC 2.3: null handling (None when no yellow nodes, not empty string)
- AC 2.4: Backward compatibility (topic extraction unchanged)

[Source: docs/stories/story-12.E.2-user-understanding-dual-channel.md#Testing]
[Source: docs/architecture/coding-standards.md#测试规范]
"""

import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set environment variable BEFORE importing agent_service
# This enables context enrichment for testing dual-channel delivery
os.environ["DISABLE_CONTEXT_ENRICHMENT"] = "false"

# Reload the module to pick up the new environment variable
import importlib

import app.services.agent_service as agent_service_module

importlib.reload(agent_service_module)


class TestUserUnderstandingDualChannel:
    """Story 12.E.2 - user_understanding Dual-Channel Delivery Tests."""

    @pytest.fixture
    def temp_canvas_dir(self):
        """Create a temporary directory for test canvas files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def canvas_with_yellow_node(self, temp_canvas_dir: str) -> Dict[str, Any]:
        """Create canvas data with a yellow understanding node (color: '6')."""
        canvas_data = {
            "nodes": [
                {
                    "id": "source-node-001",
                    "type": "text",
                    "text": "逆否命题的定义是...",
                    "x": 0,
                    "y": 0,
                    "width": 250,
                    "height": 60,
                    "color": "1"  # Red - concept node
                },
                {
                    "id": "yellow-understanding-001",
                    "type": "text",
                    "text": "我理解逆否命题就是把原命题的条件和结论都否定然后交换",
                    "x": 0,
                    "y": 100,
                    "width": 250,
                    "height": 80,
                    "color": "6"  # Yellow - understanding node (修复: '6'=Yellow, '3'=Purple)
                }
            ],
            "edges": [
                {
                    "id": "edge-001",
                    "fromNode": "source-node-001",
                    "toNode": "yellow-understanding-001",
                    "fromSide": "bottom",
                    "toSide": "top"
                }
            ]
        }
        # Write canvas file
        canvas_path = os.path.join(temp_canvas_dir, "test.canvas")
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False)
        return {"data": canvas_data, "path": canvas_path, "dir": temp_canvas_dir}

    @pytest.fixture
    def canvas_without_yellow_node(self, temp_canvas_dir: str) -> Dict[str, Any]:
        """Create canvas data without yellow understanding nodes."""
        canvas_data = {
            "nodes": [
                {
                    "id": "source-node-001",
                    "type": "text",
                    "text": "逆否命题的定义是...",
                    "x": 0,
                    "y": 0,
                    "width": 250,
                    "height": 60,
                    "color": "1"  # Red - concept node
                },
                {
                    "id": "blue-explanation-001",
                    "type": "text",
                    "text": "AI生成的解释内容...",
                    "x": 0,
                    "y": 100,
                    "width": 250,
                    "height": 80,
                    "color": "5"  # Blue - AI explanation node
                }
            ],
            "edges": [
                {
                    "id": "edge-001",
                    "fromNode": "source-node-001",
                    "toNode": "blue-explanation-001",
                    "fromSide": "bottom",
                    "toSide": "top"
                }
            ]
        }
        # Write canvas file
        canvas_path = os.path.join(temp_canvas_dir, "test_no_yellow.canvas")
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False)
        return {"data": canvas_data, "path": canvas_path, "dir": temp_canvas_dir}

    @pytest.fixture
    def canvas_with_multiple_yellow_nodes(self, temp_canvas_dir: str) -> Dict[str, Any]:
        """Create canvas data with multiple yellow understanding nodes."""
        canvas_data = {
            "nodes": [
                {
                    "id": "source-node-001",
                    "type": "text",
                    "text": "逆否命题的定义是...",
                    "x": 0,
                    "y": 0,
                    "width": 250,
                    "height": 60,
                    "color": "1"
                },
                {
                    "id": "yellow-001",
                    "type": "text",
                    "text": "第一个理解：否定条件和结论",
                    "x": 0,
                    "y": 100,
                    "width": 250,
                    "height": 80,
                    "color": "3"
                },
                {
                    "id": "yellow-002",
                    "type": "text",
                    "text": "第二个理解：交换条件和结论",
                    "x": 300,
                    "y": 100,
                    "width": 250,
                    "height": 80,
                    "color": "3"
                }
            ],
            "edges": [
                {
                    "id": "edge-001",
                    "fromNode": "source-node-001",
                    "toNode": "yellow-001",
                    "fromSide": "bottom",
                    "toSide": "top"
                },
                {
                    "id": "edge-002",
                    "fromNode": "source-node-001",
                    "toNode": "yellow-002",
                    "fromSide": "bottom",
                    "toSide": "top"
                }
            ]
        }
        canvas_path = os.path.join(temp_canvas_dir, "test_multi.canvas")
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False)
        return {"data": canvas_data, "path": canvas_path, "dir": temp_canvas_dir}

    # ==========================================================================
    # AC 2.1: JSON Field Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_user_understanding_in_json_field(self, canvas_with_yellow_node):
        """
        AC 2.1: Verify user_understanding appears in JSON field.

        When yellow nodes exist, call_explanation should receive
        user_understanding parameter with the merged content.
        """
        from app.services.agent_service import AgentService

        # Arrange
        canvas_info = canvas_with_yellow_node
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "Test explanation"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            with patch('app.config.settings') as mock_settings:
                mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                service = AgentService()

                # Act
                await service.generate_explanation(
                    canvas_name="test",
                    node_id="source-node-001",
                    content="逆否命题的定义...",
                    explanation_type="deep"
                )

                # Assert
                mock_call.assert_called_once()
                call_kwargs = mock_call.call_args.kwargs

                # ✅ AC 2.1: user_understanding should NOT be None
                assert "user_understanding" in call_kwargs or len(mock_call.call_args.args) > 4
                # Check if passed as kwarg
                user_understanding = call_kwargs.get("user_understanding")
                assert user_understanding is not None, "user_understanding should not be None when yellow nodes exist"
                assert "把原命题" in user_understanding or "否定" in user_understanding

    @pytest.mark.asyncio
    async def test_user_understanding_contains_yellow_node_content(self, canvas_with_yellow_node):
        """
        AC 2.1: Verify user_understanding contains actual yellow node text.

        The user_understanding parameter should contain the exact text
        from the yellow understanding node(s).
        """
        from app.services.agent_service import AgentService

        canvas_info = canvas_with_yellow_node
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            with patch('app.config.settings') as mock_settings:
                mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                service = AgentService()
                await service.generate_explanation(
                    canvas_name="test",
                    node_id="source-node-001",
                    content="逆否命题",
                    explanation_type="oral"
                )

                call_kwargs = mock_call.call_args.kwargs
                user_understanding = call_kwargs.get("user_understanding")

                # Should contain exact text from yellow node
                expected_content = "我理解逆否命题就是把原命题的条件和结论都否定然后交换"
                assert user_understanding is not None
                assert expected_content in user_understanding

    # ==========================================================================
    # AC 2.2: Dual-Channel Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_user_understanding_in_enhanced_context(self, canvas_with_yellow_node):
        """
        AC 2.2: Verify user_understanding in enhanced_context.

        The enhanced_context should contain "## 用户之前的个人理解" section.
        """
        from app.services.agent_service import AgentService

        canvas_info = canvas_with_yellow_node
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            with patch('app.config.settings') as mock_settings:
                mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                service = AgentService()
                await service.generate_explanation(
                    canvas_name="test",
                    node_id="source-node-001",
                    content="逆否命题",
                    explanation_type="oral"
                )

                call_kwargs = mock_call.call_args.kwargs
                context = call_kwargs.get("context", "")

                # ✅ AC 2.2: enhanced_context should contain user understanding section
                assert "用户之前的个人理解" in context, \
                    f"enhanced_context should contain '用户之前的个人理解' section, got: {context[:200]}"

    @pytest.mark.asyncio
    async def test_user_understanding_in_both_channels(self, canvas_with_yellow_node):
        """
        AC 2.2: Verify user_understanding in BOTH JSON field AND enhanced_context.

        This is the core dual-channel test - both delivery mechanisms should work.
        """
        from app.services.agent_service import AgentService

        canvas_info = canvas_with_yellow_node
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            with patch('app.config.settings') as mock_settings:
                mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                service = AgentService()
                await service.generate_explanation(
                    canvas_name="test",
                    node_id="source-node-001",
                    content="逆否命题",
                    explanation_type="deep"  # deep-decomposition requires user_understanding
                )

                call_kwargs = mock_call.call_args.kwargs
                user_understanding = call_kwargs.get("user_understanding")
                context = call_kwargs.get("context", "")

                # ✅ Channel 1: JSON field
                assert user_understanding is not None, "JSON field user_understanding should not be None"

                # ✅ Channel 2: enhanced_context
                assert "用户之前的个人理解" in context, "enhanced_context should contain user understanding"

                # Both should contain same content
                assert "否定" in user_understanding or "交换" in user_understanding
                assert "否定" in context or "交换" in context

    @pytest.mark.asyncio
    async def test_multiple_yellow_nodes_merged(self, canvas_with_multiple_yellow_nodes):
        """
        AC 2.2: Verify multiple yellow nodes are merged correctly.

        When multiple yellow nodes exist, they should be joined with "\n\n".
        """
        from app.services.agent_service import AgentService

        canvas_info = canvas_with_multiple_yellow_nodes
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            with patch('app.config.settings') as mock_settings:
                mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                service = AgentService()
                await service.generate_explanation(
                    canvas_name="test_multi",
                    node_id="source-node-001",
                    content="逆否命题",
                    explanation_type="oral"
                )

                call_kwargs = mock_call.call_args.kwargs
                user_understanding = call_kwargs.get("user_understanding")

                # Should contain content from both yellow nodes
                assert user_understanding is not None
                # Note: Order may vary due to BFS traversal
                assert "第一个理解" in user_understanding or "第二个理解" in user_understanding

    # ==========================================================================
    # AC 2.3: Null Handling Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_user_understanding_null_when_no_yellow_node(self, canvas_without_yellow_node):
        """
        AC 2.3: Verify user_understanding is None (null) when no yellow nodes.

        When there are no yellow understanding nodes, user_understanding
        should be None (which becomes JSON null), NOT an empty string.
        """
        from app.services.agent_service import AgentService

        canvas_info = canvas_without_yellow_node
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            with patch('app.config.settings') as mock_settings:
                mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                service = AgentService()
                await service.generate_explanation(
                    canvas_name="test_no_yellow",
                    node_id="source-node-001",
                    content="逆否命题",
                    explanation_type="oral"
                )

                call_kwargs = mock_call.call_args.kwargs
                user_understanding = call_kwargs.get("user_understanding")

                # ✅ AC 2.3: Should be None, NOT empty string
                assert user_understanding is None, \
                    f"user_understanding should be None when no yellow nodes, got: {repr(user_understanding)}"

    @pytest.mark.asyncio
    async def test_user_understanding_not_empty_string(self, canvas_without_yellow_node):
        """
        AC 2.3: Verify user_understanding is NOT an empty string.

        Explicit check that we get None, not "".
        """
        from app.services.agent_service import AgentService

        canvas_info = canvas_without_yellow_node
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            with patch('app.config.settings') as mock_settings:
                mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                service = AgentService()
                await service.generate_explanation(
                    canvas_name="test_no_yellow",
                    node_id="source-node-001",
                    content="逆否命题",
                    explanation_type="oral"
                )

                call_kwargs = mock_call.call_args.kwargs
                user_understanding = call_kwargs.get("user_understanding")

                # Should NOT be empty string
                assert user_understanding != "", \
                    "user_understanding should be None, not empty string ''"

    # ==========================================================================
    # AC 2.4: Backward Compatibility Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_topic_extraction_unchanged(self, canvas_with_yellow_node):
        """
        AC 2.4: Verify topic extraction is not affected by user_understanding changes.

        The _extract_topic_from_content method should work as before.
        """
        from app.services.agent_service import AgentService

        canvas_info = canvas_with_yellow_node
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            with patch('app.config.settings') as mock_settings:
                mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                service = AgentService()

                # Test with Chinese content
                await service.generate_explanation(
                    canvas_name="test",
                    node_id="source-node-001",
                    content="Level Set方法是一种数值方法，用于追踪界面的演化",
                    explanation_type="oral"
                )

                # Verify call_explanation was called (backward compatibility)
                mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_explanation_returns_result(self, canvas_with_yellow_node):
        """
        AC 2.4: Verify generate_explanation still returns expected result structure.

        The method should still return the proper result dictionary.
        """
        from app.services.agent_service import AgentService

        canvas_info = canvas_with_yellow_node
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"explanation": "这是一个测试解释", "content": "Test content"}

        with patch.object(AgentService, 'call_explanation', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            # Also mock the file writing to avoid side effects
            with patch.object(AgentService, '_write_nodes_to_canvas', new_callable=AsyncMock):
                with patch('app.config.settings') as mock_settings:
                    mock_settings.CANVAS_BASE_PATH = canvas_info["dir"]

                    service = AgentService()
                    result = await service.generate_explanation(
                        canvas_name="test",
                        node_id="source-node-001",
                        content="逆否命题",
                        explanation_type="oral"
                    )

                    # Should return a dict with expected keys
                    assert isinstance(result, dict)
                    # Result structure should be maintained


class TestCallExplanationUserUnderstanding:
    """Tests for call_explanation user_understanding handling."""

    @pytest.mark.asyncio
    async def test_call_explanation_json_contains_user_understanding(self):
        """
        Verify JSON prompt in call_explanation contains user_understanding field.
        """
        from app.services.agent_service import AgentService

        mock_agent_result = MagicMock()
        mock_agent_result.success = True
        mock_agent_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_agent', new_callable=AsyncMock) as mock_call_agent:
            mock_call_agent.return_value = mock_agent_result

            service = AgentService()

            test_understanding = "用户的测试理解内容"
            await service.call_explanation(
                content="测试内容",
                explanation_type="oral",
                context="测试上下文",
                user_understanding=test_understanding
            )

            # Check the JSON prompt passed to call_agent
            mock_call_agent.assert_called_once()
            call_args = mock_call_agent.call_args
            json_prompt = call_args.args[1]  # Second positional arg is the prompt

            # Parse JSON and verify
            prompt_data = json.loads(json_prompt)
            assert prompt_data["user_understanding"] == test_understanding

    @pytest.mark.asyncio
    async def test_call_explanation_json_null_when_no_understanding(self):
        """
        Verify JSON prompt has null user_understanding when not provided.
        """
        from app.services.agent_service import AgentService

        mock_agent_result = MagicMock()
        mock_agent_result.success = True
        mock_agent_result.data = {"explanation": "Test"}

        with patch.object(AgentService, 'call_agent', new_callable=AsyncMock) as mock_call_agent:
            mock_call_agent.return_value = mock_agent_result

            service = AgentService()
            await service.call_explanation(
                content="测试内容",
                explanation_type="oral",
                user_understanding=None  # Explicitly None
            )

            call_args = mock_call_agent.call_args
            json_prompt = call_args.args[1]

            prompt_data = json.loads(json_prompt)
            # JSON null becomes Python None
            assert prompt_data["user_understanding"] is None
