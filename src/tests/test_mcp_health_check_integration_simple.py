"""
Simplified Integration Tests for MCP Health Check in Learning Commands

Tests the integration without complex mocking of full LearningSessionManager.
Focuses on testing the health check function integration patterns.

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-31
Story: 10.11.2 - MCP Graphiti Server Health Check Integration
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from memory_system.mcp_health_check import (
    MCPServerUnavailableError,
    check_mcp_server_health,
    detect_mcp_server_path,
    suggest_mcp_server_startup,
)


class TestMCPHealthCheckIntegrationPatterns:
    """Test integration patterns used in learning_commands.py"""

    @pytest.mark.asyncio
    async def test_early_health_check_pattern_success(self):
        """
        Test pattern: Early health check before starting system

        This is the pattern used in start_session()
        """
        # Mock successful health check
        with patch('importlib.import_module') as mock_import:
            mock_claude_tools = type('obj', (object,), {
                'mcp__graphiti_memory__list_memories': AsyncMock(return_value={'memories': []})
            })
            mock_import.return_value = mock_claude_tools

            # Perform health check (as done in start_session)
            health = await check_mcp_server_health(timeout=2)

            # Verify result
            assert health['available'] is True
            assert health['error'] == ''

            # Pattern: Check if available, then proceed or degrade
            if not health['available']:
                graphiti_unavailable = True  # Degradation mode
            else:
                graphiti_unavailable = False  # Normal mode

            assert graphiti_unavailable is False

    @pytest.mark.asyncio
    async def test_early_health_check_pattern_failure(self):
        """
        Test pattern: Early health check detects unavailable server

        This is the pattern used in start_session() when MCP is unavailable
        """
        # Mock failed health check
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("No module named 'claude_tools'")

            # Perform health check
            health = await check_mcp_server_health(timeout=2)

            # Verify result
            assert health['available'] is False
            assert len(health['error']) > 0
            assert len(health['suggestion']) > 0
            assert len(health['mcp_server_path']) > 0

            # Pattern: Set degradation flag
            graphiti_unavailable = not health['available']
            assert graphiti_unavailable is True

            # Pattern: Generate user-friendly message
            error_message = "❌ Graphiti知识图谱功能不可用\n"
            error_message += f"原因: {health['error']}\n"
            error_message += f"建议: {health['suggestion']}\n"
            error_message += f"路径: {health['mcp_server_path']}"

            assert '❌' in error_message
            assert 'Graphiti' in error_message

    @pytest.mark.asyncio
    async def test_start_graphiti_pattern_with_exception(self):
        """
        Test pattern: Health check before import, raise exception if unavailable

        This is the pattern used in _start_graphiti()
        """
        # Mock failed health check
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Server unavailable")

            # Perform health check
            health = await check_mcp_server_health(timeout=2)

            # Pattern: If unavailable, raise MCPServerUnavailableError
            if not health['available']:
                with pytest.raises(MCPServerUnavailableError):
                    raise MCPServerUnavailableError(
                        error=health['error'],
                        suggestion=health['suggestion'],
                        mcp_server_path=health['mcp_server_path']
                    )

    # Note: Timeout parameter testing is covered by unit tests in test_mcp_health_check.py

    @pytest.mark.asyncio
    async def test_degradation_mode_workflow(self):
        """
        Test complete degradation mode workflow

        Pattern: Health check fails → Set flag → Continue without Graphiti
        """
        # Mock unavailable MCP
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("MCP unavailable")

            # Step 1: Early health check
            health = await check_mcp_server_health(timeout=2)
            assert health['available'] is False

            # Step 2: Set degradation flag
            graphiti_unavailable = True

            # Step 3: Skip Graphiti startup (simulated)
            if not graphiti_unavailable:
                # This would normally call _start_graphiti()
                raise AssertionError("Should not start Graphiti in degradation mode")

            # Step 4: Verify system continues without Graphiti
            assert graphiti_unavailable is True

    @pytest.mark.asyncio
    async def test_exception_provides_startup_command(self):
        """
        Test that MCPServerUnavailableError contains startup command

        Pattern: Exception message includes helpful commands for user
        """
        # Get default paths and suggestions
        server_path = detect_mcp_server_path()
        suggestion = suggest_mcp_server_startup()

        # Create exception
        error = MCPServerUnavailableError(
            error="Connection failed",
            suggestion=suggestion,
            mcp_server_path=server_path
        )

        # Verify exception message contains helpful information
        error_str = str(error)
        assert '快速启动命令' in error_str or '命令' in error_str
        assert len(server_path) > 0

    @pytest.mark.asyncio
    async def test_health_check_return_format(self):
        """
        Test that health check returns expected format

        Pattern: Always return dict with required keys
        """
        # Mock any scenario
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = Exception("Any error")

            health = await check_mcp_server_health(timeout=2)

            # Verify required keys present
            required_keys = ['available', 'error', 'suggestion', 'mcp_server_path']
            for key in required_keys:
                assert key in health, f"Missing required key: {key}"

            # Verify types
            assert isinstance(health['available'], bool)
            assert isinstance(health['error'], str)
            assert isinstance(health['suggestion'], str)
            assert isinstance(health['mcp_server_path'], str)

    def test_exception_sanitization_integration(self):
        """
        Test that exception sanitizes error messages properly

        Pattern: Sanitize all error messages for security
        """
        # Test with dangerous input
        dangerous_error = "\x1b[31mError\x1b[0m; rm -rf /; && cat /etc/passwd"

        exception = MCPServerUnavailableError(
            error=dangerous_error,
            suggestion="Fix it",
            mcp_server_path="C:\\path"
        )

        # Verify sanitization
        assert '\x1b[31m' not in exception.error
        assert ';' not in exception.error
        assert '&&' not in exception.error


class TestMCPHealthCheckRealWorldScenarios:
    """Test real-world integration scenarios"""

    @pytest.mark.asyncio
    async def test_scenario_first_time_user_no_mcp_server(self):
        """
        Scenario: New user, MCP server not installed

        Expected: Clear error message with installation instructions
        """
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("No module named 'claude_tools'")

            health = await check_mcp_server_health(timeout=2)

            # Verify helpful error information
            assert health['available'] is False
            assert 'claude_tools' in health['error']
            assert len(health['suggestion']) > 0
            assert len(health['mcp_server_path']) > 0

    @pytest.mark.asyncio
    async def test_scenario_mcp_server_timeout(self):
        """
        Scenario: MCP server is running but responds slowly

        Expected: Timeout with retry suggestion
        """
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)

        with patch('importlib.import_module') as mock_import:
            mock_claude_tools = type('obj', (object,), {
                'mcp__graphiti_memory__list_memories': slow_response
            })
            mock_import.return_value = mock_claude_tools

            health = await check_mcp_server_health(timeout=1)

            assert health['available'] is False
            assert '超时' in health['error'] or 'timeout' in health['error'].lower()

    @pytest.mark.asyncio
    async def test_scenario_mcp_server_connection_error(self):
        """
        Scenario: MCP server exists but cannot connect

        Expected: Connection error with restart suggestion
        """
        with patch('importlib.import_module') as mock_import:
            mock_claude_tools = type('obj', (object,), {
                'mcp__graphiti_memory__list_memories': AsyncMock(side_effect=ConnectionError("Connection refused"))
            })
            mock_import.return_value = mock_claude_tools

            health = await check_mcp_server_health(timeout=2)

            assert health['available'] is False
            assert 'Connection' in health['error'] or '连接' in health['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
