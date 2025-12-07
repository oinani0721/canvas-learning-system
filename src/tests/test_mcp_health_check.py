"""
Unit Tests for MCP Server Health Check Module

Tests the MCP server health check functionality including:
- check_mcp_server_health function
- MCPServerUnavailableError exception class
- detect_mcp_server_path function
- suggest_mcp_server_startup function

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-31
Story: 10.11.2 - MCP Graphiti Server Health Check
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from memory_system.mcp_health_check import (
    MCPServerUnavailableError,
    check_mcp_server_health,
    check_mcp_server_health_sync,
    detect_mcp_server_path,
    suggest_mcp_server_startup,
)


class TestCheckMCPServerHealth:
    """Test suite for check_mcp_server_health function"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check when MCP server is available and responding"""
        # Mock successful scenario
        mock_list_memories = AsyncMock(return_value={'memories': [], 'count': 0})

        with patch('importlib.import_module') as mock_import:
            mock_claude_tools = Mock()
            mock_claude_tools.mcp__graphiti_memory__list_memories = mock_list_memories
            mock_import.return_value = mock_claude_tools

            # Execute health check
            result = await check_mcp_server_health(timeout=2)

            # Assertions
            assert result['available'] is True
            assert result['error'] == ''
            assert result['suggestion'] == ''
            assert 'mcp_server_path' in result
            assert mock_list_memories.called

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check when MCP server times out"""
        # Mock timeout scenario
        async def mock_timeout(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow response

        with patch('importlib.import_module') as mock_import:
            mock_claude_tools = Mock()
            mock_claude_tools.mcp__graphiti_memory__list_memories = mock_timeout
            mock_import.return_value = mock_claude_tools

            # Execute health check with short timeout
            result = await check_mcp_server_health(timeout=1)

            # Assertions
            assert result['available'] is False
            assert 'timeout' in result['error'].lower() or '超时' in result['error']
            assert 'suggestion' in result
            assert 'mcp_server_path' in result

    @pytest.mark.asyncio
    async def test_health_check_import_error(self):
        """Test health check when claude_tools module cannot be imported"""
        # Mock import failure
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("No module named 'claude_tools'")

            # Execute health check
            result = await check_mcp_server_health(timeout=2)

            # Assertions
            assert result['available'] is False
            assert 'claude_tools' in result['error']
            assert 'suggestion' in result
            assert 'mcp_server_path' in result

    @pytest.mark.asyncio
    async def test_health_check_missing_function(self):
        """Test health check when list_memories function is missing"""
        # Mock scenario where claude_tools exists but list_memories doesn't
        with patch('importlib.import_module') as mock_import:
            mock_claude_tools = Mock()
            mock_claude_tools.mcp__graphiti_memory__list_memories = None  # Missing function
            mock_import.return_value = mock_claude_tools

            # Execute health check
            result = await check_mcp_server_health(timeout=2)

            # Assertions
            assert result['available'] is False
            assert 'list_memories' in result['error']
            assert 'suggestion' in result

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self):
        """Test health check when MCP server returns connection error"""
        # Mock connection error
        mock_list_memories = AsyncMock(side_effect=ConnectionError("Connection refused"))

        with patch('importlib.import_module') as mock_import:
            mock_claude_tools = Mock()
            mock_claude_tools.mcp__graphiti_memory__list_memories = mock_list_memories
            mock_import.return_value = mock_claude_tools

            # Execute health check
            result = await check_mcp_server_health(timeout=2)

            # Assertions
            assert result['available'] is False
            assert 'Connection' in result['error'] or '连接' in result['error']
            assert 'suggestion' in result
            assert 'mcp_server_path' in result

    @pytest.mark.asyncio
    async def test_health_check_returns_all_required_fields(self):
        """Test that health check result contains all required fields"""
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Test error")

            # Execute health check
            result = await check_mcp_server_health(timeout=2)

            # Verify all required fields present
            required_fields = ['available', 'error', 'suggestion', 'mcp_server_path']
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"


class TestMCPServerUnavailableError:
    """Test suite for MCPServerUnavailableError exception class"""

    def test_exception_initialization(self):
        """Test exception initializes with correct attributes"""
        error = "Test error message"
        suggestion = "Try restarting the server"
        path = "C:\\test\\path"

        exception = MCPServerUnavailableError(
            error=error,
            suggestion=suggestion,
            mcp_server_path=path
        )

        assert exception.error == error
        assert exception.suggestion == suggestion
        assert exception.mcp_server_path == path

    def test_exception_string_format(self):
        """Test exception __str__ returns properly formatted message"""
        exception = MCPServerUnavailableError(
            error="MCP服务器响应超时",
            suggestion="启动MCP服务器",
            mcp_server_path="C:\\test\\path"
        )

        error_str = str(exception)

        # Verify message contains key components
        assert "❌ MCP Graphiti服务器不可用" in error_str
        assert "原因:" in error_str
        assert "解决方案:" in error_str
        assert "快速启动命令:" in error_str
        assert "MCP服务器响应超时" in error_str

    def test_exception_sanitizes_ansi_codes(self):
        """Test exception removes ANSI escape codes from error messages"""
        # Error message with ANSI codes
        error_with_ansi = "\x1b[31mRed error\x1b[0m message"

        exception = MCPServerUnavailableError(
            error=error_with_ansi,
            suggestion="Fix it",
            mcp_server_path="C:\\test\\path"
        )

        # ANSI codes should be removed
        assert "\x1b[31m" not in exception.error
        assert "\x1b[0m" not in exception.error
        assert "Red error message" in exception.error

    def test_exception_truncates_long_messages(self):
        """Test exception truncates messages longer than 500 characters"""
        # Create a very long error message
        long_error = "A" * 600

        exception = MCPServerUnavailableError(
            error=long_error,
            suggestion="Fix it",
            mcp_server_path="C:\\test\\path"
        )

        # Should be truncated to 500 chars (497 + "...")
        assert len(exception.error) <= 500

    def test_exception_filters_injection_characters(self):
        """Test exception filters potential shell injection characters"""
        # Error message with dangerous characters
        error_with_injection = "Error; rm -rf /; && cat /etc/passwd"

        exception = MCPServerUnavailableError(
            error=error_with_injection,
            suggestion="Fix it",
            mcp_server_path="C:\\test\\path"
        )

        # Dangerous characters should be removed
        assert ";" not in exception.error
        assert "&&" not in exception.error
        assert "|" not in exception.error

    def test_exception_sanitizes_path(self):
        """Test exception sanitizes path information"""
        # Path with dangerous characters
        path_with_injection = "C:\\test\\path; rm -rf /"

        exception = MCPServerUnavailableError(
            error="Error",
            suggestion="Fix it",
            mcp_server_path=path_with_injection
        )

        # Dangerous characters should be removed from path
        assert ";" not in exception.mcp_server_path
        assert "|" not in exception.mcp_server_path


class TestDetectMCPServerPath:
    """Test suite for detect_mcp_server_path function"""

    def test_detect_default_path(self):
        """Test returns default path when no environment variable set"""
        with patch.dict('os.environ', {}, clear=True):
            path = detect_mcp_server_path()

            # Should return default path
            assert "graphiti\\mcp_server" in path or "graphiti/mcp_server" in path

    def test_detect_env_path(self):
        """Test returns environment variable path when set"""
        custom_path = "C:\\custom\\mcp\\path"

        with patch.dict('os.environ', {'MCP_SERVER_PATH': custom_path}):
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                path = detect_mcp_server_path()

                # Should return custom path from env var
                assert path == custom_path

    def test_detect_env_path_not_exists(self):
        """Test returns default path when env path doesn't exist"""
        custom_path = "C:\\nonexistent\\path"

        with patch.dict('os.environ', {'MCP_SERVER_PATH': custom_path}):
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = False
                path = detect_mcp_server_path()

                # Should fall back to default path
                assert "graphiti\\mcp_server" in path or "graphiti/mcp_server" in path


class TestSuggestMCPServerStartup:
    """Test suite for suggest_mcp_server_startup function"""

    def test_suggest_windows_startup(self):
        """Test returns Windows-specific startup command"""
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'Windows'

            suggestion = suggest_mcp_server_startup()

            # Should contain Windows batch file
            assert "start_graphiti_mcp.bat" in suggestion
            assert "cd" in suggestion

    def test_suggest_unix_startup(self):
        """Test returns Unix-specific startup command"""
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'Linux'

            suggestion = suggest_mcp_server_startup()

            # Should contain Unix shell script
            assert "start_graphiti_mcp.sh" in suggestion
            assert "cd" in suggestion


class TestSynchronousWrapper:
    """Test suite for synchronous wrapper function"""

    def test_sync_wrapper(self):
        """Test synchronous wrapper calls async function correctly"""
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Test")

            # Call synchronous wrapper
            result = check_mcp_server_health_sync(timeout=2)

            # Should return same format as async version
            assert isinstance(result, dict)
            assert 'available' in result
            assert 'error' in result
            assert 'suggestion' in result
            assert 'mcp_server_path' in result


# ==================== Integration Tests ====================

class TestHealthCheckIntegration:
    """Integration tests for health check workflow"""

    @pytest.mark.asyncio
    async def test_full_success_workflow(self):
        """Test complete success workflow from health check to MCP call"""
        # Mock successful MCP server
        mock_list_memories = AsyncMock(return_value={'memories': []})

        with patch('importlib.import_module') as mock_import:
            mock_claude_tools = Mock()
            mock_claude_tools.mcp__graphiti_memory__list_memories = mock_list_memories
            mock_import.return_value = mock_claude_tools

            # Step 1: Health check
            health = await check_mcp_server_health(timeout=2)
            assert health['available'] is True

            # Step 2: If available, import should work
            # (In real code, this would proceed to call MCP tools)

    @pytest.mark.asyncio
    async def test_full_failure_workflow(self):
        """Test complete failure workflow with exception raising"""
        # Mock unavailable MCP server
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("MCP not available")

            # Step 1: Health check
            health = await check_mcp_server_health(timeout=2)
            assert health['available'] is False

            # Step 2: Should raise exception
            with pytest.raises(MCPServerUnavailableError) as exc_info:
                raise MCPServerUnavailableError(
                    error=health['error'],
                    suggestion=health['suggestion'],
                    mcp_server_path=health['mcp_server_path']
                )

            # Step 3: Verify exception message is user-friendly
            exception_str = str(exc_info.value)
            assert "快速启动命令" in exception_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
