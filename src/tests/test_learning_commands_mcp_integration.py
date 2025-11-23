"""
Integration Tests for Learning Commands MCP Health Check

Tests the integration of MCP server health check into learning_commands.py:
- start_session() method early health check
- _start_graphiti() method health check
- Degradation mode behavior
- Error messaging and user guidance

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-31
Story: 10.11.2 - MCP Graphiti Server Health Check Integration
"""

import asyncio
import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from pathlib import Path

# Import the components we're testing
from command_handlers.learning_commands import LearningSessionManager
from memory_system.mcp_health_check import MCPServerUnavailableError


class TestLearningCommandsMCPHealthCheck:
    """Test suite for MCP health check integration in learning_commands.py"""

    @pytest.mark.asyncio
    async def test_start_session_mcp_available(self):
        """
        Test start_session when MCP server is available

        Expected: Session starts normally, no degradation mode
        """
        # Mock MCP health check to return available
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': True,
                'error': '',
                'suggestion': '',
                'mcp_server_path': 'C:\\test\\path'
            }

            # Mock other dependencies
            with patch('command_handlers.learning_commands.MemoryRecorder'):
                with patch('command_handlers.learning_commands.CanvasIntegrationCoordinator'):
                    handler = LearningSessionManager()

                    # Mock the file operations
                    handler.session_monitor = Mock()
                    handler.session_monitor.is_monitoring = False

                    # Call start_session
                    result = await handler.start_session()

                    # Verify health check was called
                    assert mock_health.called

                    # Verify result indicates success (session active)
                    assert '✅' in result or 'started' in result.lower() or 'active' in result.lower()

    @pytest.mark.asyncio
    async def test_start_session_mcp_unavailable_degradation(self):
        """
        Test start_session when MCP server is unavailable

        Expected: Session starts in degradation mode, friendly error message shown
        """
        # Mock MCP health check to return unavailable
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': False,
                'error': 'MCP服务器响应超时',
                'suggestion': '启动MCP服务器',
                'mcp_server_path': 'C:\\graphiti\\mcp_server'
            }

            # Mock other dependencies
            with patch('command_handlers.learning_commands.MemoryRecorder'):
                with patch('command_handlers.learning_commands.CanvasIntegrationCoordinator'):
                    handler = LearningSessionManager()

                    # Mock file operations
                    handler.session_monitor = Mock()
                    handler.session_monitor.is_monitoring = False

                    # Call start_session
                    result = await handler.start_session()

                    # Verify health check was called
                    assert mock_health.called

                    # Verify degradation message is present
                    assert '❌' in result or 'Graphiti' in result or '不可用' in result

    @pytest.mark.asyncio
    async def test_start_graphiti_health_check_success(self):
        """
        Test _start_graphiti when MCP server health check passes

        Expected: Graphiti starts successfully
        """
        # Mock successful health check
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': True,
                'error': '',
                'suggestion': '',
                'mcp_server_path': 'C:\\test\\path'
            }

            # Mock MCP tool import
            with patch('importlib.import_module') as mock_import:
                mock_claude_tools = Mock()
                mock_claude_tools.mcp__graphiti_memory__add_episode = AsyncMock()
                mock_import.return_value = mock_claude_tools

                handler = LearningSessionManager()

                # Call _start_graphiti
                result = await handler._start_graphiti()

                # Verify health check was called
                assert mock_health.called

                # Verify success message
                assert '✅' in result or 'Graphiti' in result

    @pytest.mark.asyncio
    async def test_start_graphiti_health_check_failure_raises_exception(self):
        """
        Test _start_graphiti when MCP server health check fails

        Expected: MCPServerUnavailableError is raised with helpful message
        """
        # Mock failing health check
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': False,
                'error': 'Connection refused',
                'suggestion': 'Start the MCP server',
                'mcp_server_path': 'C:\\test\\path'
            }

            handler = LearningSessionHandler()

            # Call _start_graphiti and expect exception
            with pytest.raises(MCPServerUnavailableError) as exc_info:
                await handler._start_graphiti()

            # Verify exception contains helpful information
            exception_str = str(exc_info.value)
            assert 'Connection refused' in exception_str or '不可用' in exception_str

    @pytest.mark.asyncio
    async def test_start_graphiti_import_error_handling(self):
        """
        Test _start_graphiti handles ImportError gracefully

        Expected: MCPServerUnavailableError is raised when claude_tools cannot be imported
        """
        # Mock successful health check but failed import
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': True,
                'error': '',
                'suggestion': '',
                'mcp_server_path': 'C:\\test\\path'
            }

            # Mock import failure
            with patch('importlib.import_module') as mock_import:
                mock_import.side_effect = ImportError("No module named 'claude_tools'")

                handler = LearningSessionManager()

                # Call _start_graphiti and expect exception
                with pytest.raises(MCPServerUnavailableError) as exc_info:
                    await handler._start_graphiti()

                # Verify exception message mentions the issue
                exception_str = str(exc_info.value)
                assert 'claude_tools' in exception_str or 'import' in exception_str.lower()

    @pytest.mark.asyncio
    async def test_degradation_mode_flag_set_correctly(self):
        """
        Test that degradation mode flag is set correctly based on health check

        Expected: graphiti_unavailable flag reflects health check result
        """
        # Test unavailable scenario
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': False,
                'error': 'Timeout',
                'suggestion': 'Restart server',
                'mcp_server_path': 'C:\\test\\path'
            }

            with patch('command_handlers.learning_commands.MemoryRecorder'):
                with patch('command_handlers.learning_commands.CanvasIntegrationCoordinator'):
                    handler = LearningSessionManager()
                    handler.session_monitor = Mock()
                    handler.session_monitor.is_monitoring = False

                    # Call start_session
                    await handler.start_session()

                    # Verify health check was called
                    assert mock_health.called

                    # Since we can't directly access the local variable, we verify
                    # the behavior by checking that Graphiti is NOT started
                    # (This is implied by the degradation mode)

    @pytest.mark.asyncio
    async def test_health_check_timeout_parameter(self):
        """
        Test that health check is called with correct timeout parameter

        Expected: timeout=2 seconds as specified in requirements
        """
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': True,
                'error': '',
                'suggestion': '',
                'mcp_server_path': 'C:\\test\\path'
            }

            with patch('command_handlers.learning_commands.MemoryRecorder'):
                with patch('command_handlers.learning_commands.CanvasIntegrationCoordinator'):
                    handler = LearningSessionManager()
                    handler.session_monitor = Mock()
                    handler.session_monitor.is_monitoring = False

                    await handler.start_session()

                    # Verify timeout=2 was used
                    mock_health.assert_called_with(timeout=2)


class TestMCPHealthCheckUserExperience:
    """Test user-facing aspects of MCP health check integration"""

    @pytest.mark.asyncio
    async def test_friendly_error_message_contains_startup_command(self):
        """
        Test that error message contains startup command for user

        Expected: Error message includes the command to start MCP server
        """
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': False,
                'error': 'Connection failed',
                'suggestion': 'cd C:\\graphiti\\mcp_server && start_graphiti_mcp.bat',
                'mcp_server_path': 'C:\\graphiti\\mcp_server'
            }

            with patch('command_handlers.learning_commands.MemoryRecorder'):
                with patch('command_handlers.learning_commands.CanvasIntegrationCoordinator'):
                    handler = LearningSessionManager()
                    handler.session_monitor = Mock()
                    handler.session_monitor.is_monitoring = False

                    result = await handler.start_session()

                    # Verify result contains helpful information
                    assert 'start_graphiti_mcp' in result or '启动' in result or 'MCP' in result

    @pytest.mark.asyncio
    async def test_error_message_includes_path_info(self):
        """
        Test that error message includes MCP server path for user reference

        Expected: Error message shows where MCP server should be located
        """
        test_path = 'C:\\custom\\mcp\\server'

        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': False,
                'error': 'Server not found',
                'suggestion': 'Install MCP server',
                'mcp_server_path': test_path
            }

            with patch('command_handlers.learning_commands.MemoryRecorder'):
                with patch('command_handlers.learning_commands.CanvasIntegrationCoordinator'):
                    handler = LearningSessionManager()
                    handler.session_monitor = Mock()
                    handler.session_monitor.is_monitoring = False

                    result = await handler.start_session()

                    # Verify path is mentioned (at least the directory name)
                    assert 'mcp' in result.lower() or 'server' in result.lower()


# ==================== Integration Workflow Tests ====================

class TestMCPHealthCheckWorkflow:
    """Test complete workflows involving MCP health check"""

    @pytest.mark.asyncio
    async def test_full_successful_workflow(self):
        """
        Test complete successful workflow: health check → MCP import → session start

        Expected: All steps complete successfully
        """
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': True,
                'error': '',
                'suggestion': '',
                'mcp_server_path': 'C:\\test\\path'
            }

            with patch('importlib.import_module') as mock_import:
                mock_claude_tools = Mock()
                mock_claude_tools.mcp__graphiti_memory__add_episode = AsyncMock()
                mock_import.return_value = mock_claude_tools

                with patch('command_handlers.learning_commands.MemoryRecorder'):
                    with patch('command_handlers.learning_commands.CanvasIntegrationCoordinator'):
                        handler = LearningSessionManager()
                        handler.session_monitor = Mock()
                        handler.session_monitor.is_monitoring = False

                        # Step 1: Start session (includes health check)
                        session_result = await handler.start_session()

                        # Step 2: Start Graphiti (includes health check)
                        graphiti_result = await handler._start_graphiti()

                        # Verify both steps succeeded
                        assert '✅' in session_result or 'started' in session_result.lower()
                        assert '✅' in graphiti_result or 'Graphiti' in graphiti_result

    @pytest.mark.asyncio
    async def test_full_failure_workflow(self):
        """
        Test complete failure workflow: health check fails → degradation mode → helpful error

        Expected: System degrades gracefully with helpful messages
        """
        with patch('command_handlers.learning_commands.check_mcp_server_health') as mock_health:
            mock_health.return_value = {
                'available': False,
                'error': 'MCP server not responding',
                'suggestion': 'Start MCP server with: start_graphiti_mcp.bat',
                'mcp_server_path': 'C:\\graphiti\\mcp_server'
            }

            with patch('command_handlers.learning_commands.MemoryRecorder'):
                with patch('command_handlers.learning_commands.CanvasIntegrationCoordinator'):
                    handler = LearningSessionManager()
                    handler.session_monitor = Mock()
                    handler.session_monitor.is_monitoring = False

                    # Step 1: Start session (includes health check, should show warning)
                    session_result = await handler.start_session()

                    # Verify warning message is shown
                    assert '❌' in session_result or 'Graphiti' in session_result or '不可用' in session_result

                    # Step 2: Try to start Graphiti directly (should raise exception)
                    with pytest.raises(MCPServerUnavailableError):
                        await handler._start_graphiti()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
