"""
Unit Tests for RealServiceLauncher - Story 10.8

Tests the real service launcher for Canvas Learning System's three-level memory:
- Level 1: Graphiti Knowledge Graph (via MCP tools)
- Level 2: MCP Semantic Memory (via UnifiedMemoryInterface)
- Level 3: Learning Behavior Monitoring (via LearningActivityCapture)

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-29
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from learning_system.real_service_launcher import RealServiceLauncher


@pytest.fixture
def launcher():
    """Create a RealServiceLauncher instance for testing"""
    return RealServiceLauncher()


@pytest.fixture
def mock_session():
    """Create a mock LearningSession object"""
    session = Mock()
    session.session_id = 'test_session_123'
    session.user_id = 'test_user'
    session.canvas_path = 'test.canvas'
    return session


@pytest.fixture
def mock_mcp_functions():
    """Create mock MCP tool functions"""
    return {
        'add_memory': AsyncMock(return_value={'success': True}),
        'get_memory': AsyncMock(return_value={
            'key': 'test_key',
            'content': 'test content',
            'metadata': {}
        }),
        'list_memories': AsyncMock(return_value=[])
    }


class TestRealServiceLauncherInit:
    """Test RealServiceLauncher initialization"""

    def test_init_default_state(self, launcher):
        """Test launcher initializes with correct default state"""
        assert launcher.graphiti_client is None
        assert launcher.mcp_client is None
        assert launcher.behavior_monitor is None
        assert launcher.service_health == {
            'graphiti': 'unknown',
            'mcp_semantic': 'unknown',
            'behavior_monitor': 'unknown'
        }
        assert launcher._mcp_add_memory is None
        assert launcher._mcp_get_memory is None
        assert launcher._mcp_list_memories is None

    def test_set_mcp_functions(self, launcher, mock_mcp_functions):
        """Test MCP function injection for testing"""
        launcher.set_mcp_functions(
            add_memory=mock_mcp_functions['add_memory'],
            get_memory=mock_mcp_functions['get_memory'],
            list_memories=mock_mcp_functions['list_memories']
        )

        assert launcher._mcp_add_memory == mock_mcp_functions['add_memory']
        assert launcher._mcp_get_memory == mock_mcp_functions['get_memory']
        assert launcher._mcp_list_memories == mock_mcp_functions['list_memories']


class TestGraphitiStartup:
    """Test Graphiti Knowledge Graph startup"""

    @pytest.mark.asyncio
    async def test_start_graphiti_success(self, launcher, mock_session, mock_mcp_functions):
        """Test successful Graphiti startup with verification"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)
        canvas_path = 'test.canvas'

        # Act
        result = await launcher._start_graphiti_real(canvas_path, mock_session)

        # Assert
        assert result['success'] is True
        assert result['status'] == 'running'
        assert 'session_key' in result
        assert result['session_key'] == f"learning_session_{mock_session.session_id}"
        assert result['verified'] is True
        assert launcher.graphiti_client == result['session_key']

        # Verify MCP functions were called correctly
        mock_mcp_functions['add_memory'].assert_called_once()
        call_args = mock_mcp_functions['add_memory'].call_args
        assert call_args.kwargs['key'] == f"learning_session_{mock_session.session_id}"
        assert canvas_path in call_args.kwargs['content']
        assert call_args.kwargs['metadata']['type'] == 'session_start'

        mock_mcp_functions['get_memory'].assert_called_once()

    @pytest.mark.asyncio
    async def test_start_graphiti_verification_failure(self, launcher, mock_session, mock_mcp_functions):
        """Test Graphiti startup when verification fails"""
        # Arrange
        mock_mcp_functions['get_memory'].return_value = None  # Verification fails
        launcher.set_mcp_functions(**mock_mcp_functions)

        # Act
        result = await launcher._start_graphiti_real('test.canvas', mock_session)

        # Assert
        assert result['success'] is False
        assert result['status'] == 'failed'
        assert 'error' in result
        assert '验证失败' in result['error']

    @pytest.mark.asyncio
    async def test_start_graphiti_mcp_unavailable(self, launcher, mock_session):
        """Test Graphiti startup when MCP tools are unavailable"""
        # Don't set MCP functions - they will be unavailable

        # Act
        result = await launcher._start_graphiti_real('test.canvas', mock_session)

        # Assert
        assert result['success'] is False
        assert result['status'] == 'failed'
        assert 'error' in result


class TestMCPSemanticStartup:
    """Test MCP Semantic Memory Service startup"""

    @pytest.mark.asyncio
    async def test_start_mcp_semantic_success(self, launcher, mock_session):
        """Test successful MCP semantic service startup"""
        # Arrange
        mock_uif = Mock()
        mock_uif.store_complete_learning_memory.return_value = 'memory_id_123'

        with patch('memory_system.unified_memory_interface.UnifiedMemoryInterface', return_value=mock_uif):
            # Act
            result = await launcher._start_mcp_semantic_real('test.canvas', mock_session)

            # Assert
            assert result['success'] is True
            assert result['status'] == 'running'
            assert result['memory_id'] == 'memory_id_123'
            assert result['verified'] is True
            assert launcher.mcp_client == mock_uif

            # Verify store_complete_learning_memory was called correctly
            mock_uif.store_complete_learning_memory.assert_called_once()
            call_args = mock_uif.store_complete_learning_memory.call_args
            assert call_args.kwargs['canvas_id'] == 'test'
            assert call_args.kwargs['node_id'] == f"session_{mock_session.session_id}"
            assert call_args.kwargs['learning_state'] == 'green'
            assert call_args.kwargs['confidence_score'] == 1.0

    @pytest.mark.asyncio
    async def test_start_mcp_semantic_no_memory_id(self, launcher, mock_session):
        """Test MCP semantic startup when no memory_id is returned"""
        # Arrange
        mock_uif = Mock()
        mock_uif.store_complete_learning_memory.return_value = None

        with patch('memory_system.unified_memory_interface.UnifiedMemoryInterface', return_value=mock_uif):
            # Act
            result = await launcher._start_mcp_semantic_real('test.canvas', mock_session)

            # Assert
            assert result['success'] is False
            assert result['status'] == 'failed'
            assert '未返回memory_id' in result['error']

    @pytest.mark.asyncio
    async def test_start_mcp_semantic_import_error(self, launcher, mock_session):
        """Test MCP semantic startup when UnifiedMemoryInterface cannot be imported"""
        # Arrange
        import sys
        # Temporarily make the import fail
        original_modules = sys.modules.copy()
        if 'memory_system.unified_memory_interface' in sys.modules:
            del sys.modules['memory_system.unified_memory_interface']

        with patch.dict('sys.modules', {'memory_system.unified_memory_interface': None}):
            # Act
            result = await launcher._start_mcp_semantic_real('test.canvas', mock_session)

            # Assert
            assert result['success'] is False
            assert result['status'] == 'failed'

        # Restore modules
        sys.modules.update(original_modules)


class TestBehaviorMonitorStartup:
    """Test Learning Behavior Monitoring Service startup"""

    @pytest.mark.asyncio
    async def test_start_behavior_monitor_success(self, launcher, mock_session):
        """Test successful behavior monitor startup"""
        # Arrange
        mock_lac = Mock()
        mock_lac.start_capture.return_value = True
        mock_lac.start_memory_session.return_value = 'monitor_session_123'
        mock_lac.get_buffer_status.return_value = {
            'is_capturing': True,
            'buffer_size': 0,
            'active_sessions': 1
        }

        with patch('learning_activity_capture.LearningActivityCapture', return_value=mock_lac):
            # Act
            result = await launcher._start_behavior_monitor_real('test.canvas', mock_session)

            # Assert
            assert result['success'] is True
            assert result['status'] == 'running'
            assert result['session_id'] == 'monitor_session_123'
            assert result['buffer_size'] == 0
            assert result['active_sessions'] == 1
            assert result['verified'] is True
            assert launcher.behavior_monitor == mock_lac

            # Verify methods were called
            mock_lac.start_capture.assert_called_once()
            mock_lac.start_memory_session.assert_called_once_with(
                user_id=mock_session.user_id,
                canvas_path='test.canvas'
            )
            mock_lac.get_buffer_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_behavior_monitor_capture_fails(self, launcher, mock_session):
        """Test behavior monitor startup when start_capture fails"""
        # Arrange
        mock_lac = Mock()
        mock_lac.start_capture.return_value = False  # Capture fails

        with patch('learning_activity_capture.LearningActivityCapture', return_value=mock_lac):
            # Act
            result = await launcher._start_behavior_monitor_real('test.canvas', mock_session)

            # Assert
            assert result['success'] is False
            assert result['status'] == 'failed'
            assert '启动实时捕获失败' in result['error']

    @pytest.mark.asyncio
    async def test_start_behavior_monitor_not_capturing(self, launcher, mock_session):
        """Test behavior monitor startup when not in capturing state"""
        # Arrange
        mock_lac = Mock()
        mock_lac.start_capture.return_value = True
        mock_lac.start_memory_session.return_value = 'monitor_session_123'
        mock_lac.get_buffer_status.return_value = {
            'is_capturing': False  # Not capturing!
        }

        with patch('learning_activity_capture.LearningActivityCapture', return_value=mock_lac):
            # Act
            result = await launcher._start_behavior_monitor_real('test.canvas', mock_session)

            # Assert
            assert result['success'] is False
            assert result['status'] == 'failed'
            assert '未处于捕获状态' in result['error']

    @pytest.mark.asyncio
    async def test_start_behavior_monitor_import_error(self, launcher, mock_session):
        """Test behavior monitor startup when LearningActivityCapture cannot be imported"""
        # Arrange
        import sys
        # Temporarily make the import fail
        original_modules = sys.modules.copy()
        if 'learning_activity_capture' in sys.modules:
            del sys.modules['learning_activity_capture']

        with patch.dict('sys.modules', {'learning_activity_capture': None}):
            # Act
            result = await launcher._start_behavior_monitor_real('test.canvas', mock_session)

            # Assert
            assert result['success'] is False
            assert result['status'] == 'failed'

        # Restore modules
        sys.modules.update(original_modules)


class TestStartAllServices:
    """Test starting all services together"""

    @pytest.mark.asyncio
    async def test_start_all_services_success(self, launcher, mock_session, mock_mcp_functions):
        """Test successful startup of all three services"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)

        mock_uif = Mock()
        mock_uif.store_complete_learning_memory.return_value = 'memory_id_123'

        mock_lac = Mock()
        mock_lac.start_capture.return_value = True
        mock_lac.start_memory_session.return_value = 'monitor_session_123'
        mock_lac.get_buffer_status.return_value = {
            'is_capturing': True,
            'buffer_size': 0,
            'active_sessions': 1
        }

        with patch('memory_system.unified_memory_interface.UnifiedMemoryInterface', return_value=mock_uif), \
             patch('learning_activity_capture.LearningActivityCapture', return_value=mock_lac):

            # Act
            results = await launcher.start_all_services('test.canvas', mock_session)

            # Assert
            assert 'graphiti' in results
            assert 'mcp_semantic' in results
            assert 'behavior_monitor' in results

            assert results['graphiti']['success'] is True
            assert results['mcp_semantic']['success'] is True
            assert results['behavior_monitor']['success'] is True

    @pytest.mark.asyncio
    async def test_start_all_services_partial_failure(self, launcher, mock_session, mock_mcp_functions):
        """Test that partial service failure doesn't stop other services"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)

        # MCP semantic will fail
        mock_uif = Mock()
        mock_uif.store_complete_learning_memory.side_effect = Exception("Database connection failed")

        # Behavior monitor will succeed
        mock_lac = Mock()
        mock_lac.start_capture.return_value = True
        mock_lac.start_memory_session.return_value = 'monitor_session_123'
        mock_lac.get_buffer_status.return_value = {
            'is_capturing': True,
            'buffer_size': 0,
            'active_sessions': 1
        }

        with patch('memory_system.unified_memory_interface.UnifiedMemoryInterface', return_value=mock_uif), \
             patch('learning_activity_capture.LearningActivityCapture', return_value=mock_lac):

            # Act
            results = await launcher.start_all_services('test.canvas', mock_session)

            # Assert
            assert results['graphiti']['success'] is True  # Should succeed
            assert results['mcp_semantic']['success'] is False  # Should fail
            assert results['behavior_monitor']['success'] is True  # Should succeed

    @pytest.mark.asyncio
    async def test_start_all_services_timeout(self, launcher, mock_session, mock_mcp_functions):
        """Test service startup timeout handling"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)

        # Create a service that times out
        async def slow_service(canvas_path, session):
            await asyncio.sleep(10)  # Exceeds 5 second timeout
            return {'success': True}

        with patch.object(launcher, '_start_mcp_semantic_real', side_effect=slow_service):
            # Act
            results = await launcher.start_all_services(
                'test.canvas',
                mock_session,
                enable_graphiti=False,
                enable_semantic=True,
                enable_behavior=False
            )

            # Assert
            assert results['mcp_semantic']['success'] is False
            assert results['mcp_semantic']['error'] == 'Startup timeout'

    @pytest.mark.asyncio
    async def test_start_all_services_selective(self, launcher, mock_session, mock_mcp_functions):
        """Test selective service startup"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)

        # Act - only start Graphiti
        results = await launcher.start_all_services(
            'test.canvas',
            mock_session,
            enable_graphiti=True,
            enable_semantic=False,
            enable_behavior=False
        )

        # Assert
        assert 'graphiti' in results
        assert 'mcp_semantic' not in results
        assert 'behavior_monitor' not in results


class TestServiceHealthCheck:
    """Test service health checking"""

    @pytest.mark.asyncio
    async def test_verify_services_health_all_healthy(self, launcher, mock_mcp_functions):
        """Test health check when all services are healthy"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)

        mock_uif = Mock()
        mock_uif.is_available.return_value = True
        launcher.mcp_client = mock_uif

        mock_lac = Mock()
        mock_lac.get_buffer_status.return_value = {
            'is_capturing': True,
            'config_enabled': True
        }
        launcher.behavior_monitor = mock_lac

        # Act
        health = await launcher._verify_services_health()

        # Assert
        assert health['graphiti'] == 'healthy'
        assert health['mcp_semantic'] == 'healthy'
        assert health['behavior_monitor'] == 'healthy'
        assert launcher.service_health == health

    @pytest.mark.asyncio
    async def test_verify_services_health_graphiti_unhealthy(self, launcher, mock_mcp_functions):
        """Test health check when Graphiti is unhealthy"""
        # Arrange
        mock_mcp_functions['list_memories'].side_effect = Exception("Neo4j connection failed")
        launcher.set_mcp_functions(**mock_mcp_functions)

        # Act
        health = await launcher._verify_services_health()

        # Assert
        assert health['graphiti'] == 'unhealthy'

    @pytest.mark.asyncio
    async def test_verify_services_health_not_started(self, launcher):
        """Test health check when services are not started"""
        # Act
        health = await launcher._verify_services_health()

        # Assert - services not started should show 'not_started'
        assert health['mcp_semantic'] == 'not_started'
        assert health['behavior_monitor'] == 'not_started'

    @pytest.mark.asyncio
    async def test_get_services_status(self, launcher, mock_mcp_functions):
        """Test getting service status"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)
        launcher.graphiti_client = 'test_session_key'

        mock_uif = Mock()
        mock_uif.is_available.return_value = True
        launcher.mcp_client = mock_uif

        mock_lac = Mock()
        mock_lac.get_buffer_status.return_value = {
            'is_capturing': True,
            'config_enabled': True
        }
        launcher.behavior_monitor = mock_lac

        # Act
        status = await launcher.get_services_status()

        # Assert
        assert status['graphiti']['status'] == 'running'
        assert status['graphiti']['health'] == 'healthy'
        assert status['mcp_semantic']['status'] == 'running'
        assert status['mcp_semantic']['health'] == 'healthy'
        assert status['behavior_monitor']['status'] == 'running'
        assert status['behavior_monitor']['health'] == 'healthy'


class TestStopAllServices:
    """Test stopping all services"""

    @pytest.mark.asyncio
    async def test_stop_all_services_success(self, launcher):
        """Test successful shutdown of all services"""
        # Arrange
        launcher.graphiti_client = 'test_session_key'

        mock_uif = Mock()
        mock_uif.cleanup = Mock()
        launcher.mcp_client = mock_uif

        mock_lac = Mock()
        mock_lac.get_active_sessions.return_value = ['session1', 'session2']
        mock_lac.end_memory_session = Mock()
        mock_lac.stop_capture = Mock()
        launcher.behavior_monitor = mock_lac

        # Act
        results = await launcher.stop_all_services()

        # Assert
        assert results['graphiti']['success'] is True
        assert results['mcp_semantic']['success'] is True
        assert results['behavior_monitor']['success'] is True

        # Verify cleanup was called
        mock_uif.cleanup.assert_called_once()
        assert mock_lac.end_memory_session.call_count == 2
        mock_lac.stop_capture.assert_called_once()

        # Verify clients are cleared
        assert launcher.graphiti_client is None
        assert launcher.mcp_client is None
        assert launcher.behavior_monitor is None

    @pytest.mark.asyncio
    async def test_stop_all_services_no_services(self, launcher):
        """Test stopping when no services are running"""
        # Act
        results = await launcher.stop_all_services()

        # Assert - should return empty dict
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_stop_all_services_error_handling(self, launcher):
        """Test error handling during service shutdown"""
        # Arrange
        mock_uif = Mock()
        mock_uif.cleanup.side_effect = Exception("Cleanup failed")
        launcher.mcp_client = mock_uif

        # Act
        results = await launcher.stop_all_services()

        # Assert
        assert results['mcp_semantic']['success'] is False
        assert 'error' in results['mcp_semantic']


class TestRetryMechanism:
    """Test service startup retry mechanism"""

    @pytest.mark.asyncio
    async def test_start_service_with_retry_success_first_try(self, launcher):
        """Test service starts successfully on first try"""
        # Arrange
        mock_service = AsyncMock(return_value={'success': True, 'status': 'running'})

        # Act
        result = await launcher._start_service_with_retry(mock_service, 'TestService')

        # Assert
        assert result['success'] is True
        assert mock_service.call_count == 1

    @pytest.mark.asyncio
    async def test_start_service_with_retry_success_after_retries(self, launcher):
        """Test service starts successfully after retries"""
        # Arrange
        mock_service = AsyncMock()
        mock_service.side_effect = [
            {'success': False, 'error': 'First attempt failed'},
            {'success': False, 'error': 'Second attempt failed'},
            {'success': True, 'status': 'running'}  # Third attempt succeeds
        ]

        # Act
        result = await launcher._start_service_with_retry(mock_service, 'TestService')

        # Assert
        assert result['success'] is True
        assert mock_service.call_count == 3

    @pytest.mark.asyncio
    async def test_start_service_with_retry_max_retries_exceeded(self, launcher):
        """Test service fails after max retries"""
        # Arrange
        mock_service = AsyncMock()
        mock_service.side_effect = [
            {'success': False, 'error': 'Attempt 1 failed'},
            {'success': False, 'error': 'Attempt 2 failed'},
            {'success': False, 'error': 'Attempt 3 failed'}
        ]

        # Act
        result = await launcher._start_service_with_retry(mock_service, 'TestService', max_retries=3)

        # Assert
        assert result['success'] is False
        assert mock_service.call_count == 3

    @pytest.mark.asyncio
    async def test_start_service_with_retry_exception_handling(self, launcher):
        """Test retry mechanism handles exceptions"""
        # Arrange
        mock_service = AsyncMock()
        mock_service.side_effect = [
            Exception("First attempt exception"),
            Exception("Second attempt exception"),
            {'success': True, 'status': 'running'}  # Third attempt succeeds
        ]

        # Act
        result = await launcher._start_service_with_retry(mock_service, 'TestService')

        # Assert
        assert result['success'] is True
        assert mock_service.call_count == 3


class TestGetMCPFunction:
    """Test MCP function retrieval"""

    def test_get_mcp_function_from_injected(self, launcher, mock_mcp_functions):
        """Test getting MCP function from injected functions"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)

        # Act
        func = launcher._get_mcp_function('add_memory')

        # Assert
        assert func == mock_mcp_functions['add_memory']

    def test_get_mcp_function_unavailable(self, launcher):
        """Test getting MCP function when unavailable"""
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            launcher._get_mcp_function('add_memory')

        assert 'mcp__graphiti_memory__add_memory不可用' in str(exc_info.value)

    def test_get_mcp_function_invalid_type(self, launcher):
        """Test getting MCP function with invalid type"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            launcher._get_mcp_function('invalid_type')

        assert 'Unknown MCP function type' in str(exc_info.value)


# Performance and integration tests

class TestPerformance:
    """Test performance requirements"""

    @pytest.mark.asyncio
    async def test_startup_time_under_5_seconds(self, launcher, mock_session, mock_mcp_functions):
        """Test that all services start in under 5 seconds (Story AC requirement)"""
        # Arrange
        launcher.set_mcp_functions(**mock_mcp_functions)

        mock_uif = Mock()
        mock_uif.store_complete_learning_memory.return_value = 'memory_id_123'

        mock_lac = Mock()
        mock_lac.start_capture.return_value = True
        mock_lac.start_memory_session.return_value = 'monitor_session_123'
        mock_lac.get_buffer_status.return_value = {
            'is_capturing': True,
            'buffer_size': 0,
            'active_sessions': 1
        }

        with patch('memory_system.unified_memory_interface.UnifiedMemoryInterface', return_value=mock_uif), \
             patch('learning_activity_capture.LearningActivityCapture', return_value=mock_lac):

            # Act
            start_time = datetime.now()
            await launcher.start_all_services('test.canvas', mock_session)
            elapsed = (datetime.now() - start_time).total_seconds()

            # Assert
            assert elapsed < 5.0, f"Startup took {elapsed}s, should be < 5s"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=learning_system.real_service_launcher', '--cov-report=term-missing'])
