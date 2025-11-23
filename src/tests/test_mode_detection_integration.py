"""
Integration tests for mode detection system (Story 10.11.4)

Tests the full integration of mode detection in learning commands.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from command_handlers.learning_commands import (
    set_mode_info,
    get_mode_info,
    LearningSessionManager
)
from memory_system.system_mode_detector import SystemModeDetector, MODE_FULL, MODE_PARTIAL, MODE_BASIC
from memory_system.error_formatters import (
    require_graphiti,
    require_temporal,
    require_semantic_advanced
)


class TestModeInfoStorage:
    """Test mode info storage and retrieval"""

    def test_set_and_get_mode_info(self):
        """Set and get mode info works correctly"""
        mode_info = {
            'mode': 'full',
            'available_systems': ['System 1', 'System 2'],
            'unavailable_systems': [],
            'functionality_impact': 'All good'
        }

        set_mode_info(mode_info)
        retrieved = get_mode_info()

        assert retrieved == mode_info
        assert retrieved['mode'] == 'full'

    def test_get_mode_info_before_set(self):
        """Get mode info before set returns None"""
        # Reset to None
        set_mode_info(None)

        result = get_mode_info()
        assert result is None

    def test_mode_info_updates(self):
        """Mode info can be updated"""
        mode_info1 = {'mode': 'full'}
        mode_info2 = {'mode': 'partial'}

        set_mode_info(mode_info1)
        assert get_mode_info()['mode'] == 'full'

        set_mode_info(mode_info2)
        assert get_mode_info()['mode'] == 'partial'


class TestLearningCommandIntegration:
    """Test mode detection integration in learning command"""

    @pytest.mark.asyncio
    async def test_mode_detection_in_start_session_full_mode(self):
        """Test mode detection during session start - full mode"""
        manager = LearningSessionManager()

        # Mock all 3 systems as available
        with patch.object(manager, '_start_graphiti') as mock_graphiti, \
             patch.object(manager, '_start_temporal') as mock_temporal, \
             patch.object(manager, '_start_semantic') as mock_semantic, \
             patch('command_handlers.learning_commands.check_mcp_server_health') as mock_mcp_health:

            # Configure mocks
            mock_mcp_health.return_value = {
                'available': True,
                'error': None,
                'services': ['graphiti-memory'],
                'suggestion': None
            }

            mock_graphiti.return_value = {
                'status': 'running',
                'memory_id': 'test_memory_id',
                'storage': 'Neo4j图数据库',
                'initialized_at': '2025-01-01T00:00:00'
            }

            mock_temporal.return_value = {
                'status': 'running',
                'session_id': 'test_session_id',
                'storage': '本地SQLite数据库',
                'initialized_at': '2025-01-01T00:00:00'
            }

            mock_semantic.return_value = {
                'status': 'running',
                'mode': 'mcp',
                'features': {
                    'add_memory': True,
                    'search_memories': True,
                    'advanced_semantic_search': True,
                    'vector_similarity': True
                },
                'memory_id': 'test_memory_id',
                'storage': '向量数据库',
                'initialized_at': '2025-01-01T00:00:00'
            }

            # Create mock managers for mode detection
            manager.temporal_manager = Mock(is_initialized=True, mode='neo4j')
            manager.semantic_manager = Mock(is_initialized=True, mode='mcp')
            manager.graphiti_available = True

            # Start session
            result = await manager.start_session(
                canvas_path="test.canvas",
                allow_partial_start=True,
                interactive=False
            )

            # Verify mode was detected and stored
            mode_info = get_mode_info()
            assert mode_info is not None
            assert mode_info['mode'] == MODE_FULL
            assert len(mode_info['available_systems']) == 3
            assert len(mode_info['unavailable_systems']) == 0

    @pytest.mark.asyncio
    async def test_mode_detection_partial_mode_graphiti_down(self):
        """Test mode detection when Graphiti is unavailable"""
        manager = LearningSessionManager()

        with patch.object(manager, '_start_graphiti') as mock_graphiti, \
             patch.object(manager, '_start_temporal') as mock_temporal, \
             patch.object(manager, '_start_semantic') as mock_semantic, \
             patch('command_handlers.learning_commands.check_mcp_server_health') as mock_mcp_health:

            # Graphiti unavailable
            mock_mcp_health.return_value = {
                'available': False,
                'error': 'MCP server not connected',
                'suggestion': 'Start MCP server',
                'mcp_server_path': 'test/path'
            }

            # Temporal and Semantic available
            mock_temporal.return_value = {
                'status': 'running',
                'session_id': 'test_session',
                'storage': 'SQLite',
                'initialized_at': '2025-01-01T00:00:00'
            }

            mock_semantic.return_value = {
                'status': 'running',
                'mode': 'fallback',
                'features': {'add_memory': True, 'search_memories': True},
                'memory_id': 'test_memory',
                'storage': '本地缓存',
                'initialized_at': '2025-01-01T00:00:00'
            }

            manager.temporal_manager = Mock(is_initialized=True, mode='neo4j')
            manager.semantic_manager = Mock(is_initialized=True, mode='fallback')
            manager.graphiti_available = False

            result = await manager.start_session(
                canvas_path="test.canvas",
                allow_partial_start=True,
                interactive=False
            )

            # Verify partial mode detected
            mode_info = get_mode_info()
            assert mode_info is not None
            assert mode_info['mode'] == MODE_PARTIAL
            assert any('Graphiti' in s for s in mode_info['unavailable_systems'])


class TestFunctionalityRestrictionChecks:
    """Test functionality restriction checks in commands"""

    def test_require_graphiti_when_available(self):
        """require_graphiti returns True when Graphiti is available"""
        mode_info = {
            'mode': MODE_FULL,
            'unavailable_systems': []
        }

        result = require_graphiti(mode_info)
        assert result is True

    def test_require_graphiti_when_unavailable(self, capsys):
        """require_graphiti returns False and shows message when unavailable"""
        mode_info = {
            'mode': MODE_PARTIAL,
            'unavailable_systems': ['Graphiti知识图谱 [MCP服务器未连接]']
        }

        result = require_graphiti(mode_info)
        assert result is False

        captured = capsys.readouterr()
        assert '❌ 此功能需要Graphiti知识图谱' in captured.out

    def test_require_temporal_when_available(self):
        """require_temporal returns True when available"""
        mode_info = {
            'mode': MODE_FULL,
            'unavailable_systems': []
        }

        result = require_temporal(mode_info)
        assert result is True

    def test_require_semantic_advanced_fallback_mode(self, capsys):
        """require_semantic_advanced returns False in fallback mode"""
        mode_info = {
            'mode': MODE_PARTIAL,
            'available_systems': ['语义记忆管理器 [降级模式 - 本地缓存]']
        }

        result = require_semantic_advanced(mode_info)
        assert result is False

        captured = capsys.readouterr()
        assert '⚠️ 高级语义搜索不可用' in captured.out


class TestModeDetectionRobustness:
    """Test mode detection handles edge cases gracefully"""

    @pytest.mark.asyncio
    async def test_mode_detection_does_not_block_startup(self):
        """Mode detection failure doesn't prevent session startup"""
        manager = LearningSessionManager()

        with patch.object(manager, '_start_graphiti') as mock_graphiti, \
             patch.object(manager, '_start_temporal') as mock_temporal, \
             patch.object(manager, '_start_semantic') as mock_semantic, \
             patch('command_handlers.learning_commands.check_mcp_server_health') as mock_mcp_health, \
             patch('command_handlers.learning_commands.SystemModeDetector') as mock_detector:

            # Make mode detection raise an exception
            mock_detector.detect_mode.side_effect = Exception("Mode detection failed")

            mock_mcp_health.return_value = {'available': False, 'error': 'test', 'suggestion': 'test', 'mcp_server_path': 'test'}
            mock_temporal.return_value = {'status': 'running', 'session_id': 'test', 'storage': 'test', 'initialized_at': 'test'}
            mock_semantic.return_value = {'status': 'running', 'mode': 'fallback', 'features': {}, 'memory_id': 'test', 'storage': 'test', 'initialized_at': 'test'}

            # Should still start successfully
            result = await manager.start_session(
                canvas_path="test.canvas",
                allow_partial_start=True,
                interactive=False
            )

            # Verify session started despite mode detection failure
            assert result['success'] is True


class TestSessionDataInclusion:
    """Test that mode info is included in session data"""

    @pytest.mark.asyncio
    async def test_mode_info_saved_in_session_data(self):
        """Mode info is saved in session data"""
        manager = LearningSessionManager()

        with patch.object(manager, '_start_graphiti') as mock_graphiti, \
             patch.object(manager, '_start_temporal') as mock_temporal, \
             patch.object(manager, '_start_semantic') as mock_semantic, \
             patch('command_handlers.learning_commands.check_mcp_server_health') as mock_mcp_health:

            mock_mcp_health.return_value = {'available': True, 'error': None, 'services': [], 'suggestion': None}
            mock_graphiti.return_value = {'status': 'running', 'memory_id': 'test', 'storage': 'test', 'initialized_at': 'test'}
            mock_temporal.return_value = {'status': 'running', 'session_id': 'test', 'storage': 'test', 'initialized_at': 'test'}
            mock_semantic.return_value = {'status': 'running', 'mode': 'mcp', 'features': {}, 'memory_id': 'test', 'storage': 'test', 'initialized_at': 'test'}

            manager.temporal_manager = Mock(is_initialized=True, mode='neo4j')
            manager.semantic_manager = Mock(is_initialized=True, mode='mcp')
            manager.graphiti_available = True

            result = await manager.start_session(
                canvas_path="test.canvas",
                allow_partial_start=True,
                interactive=False
            )

            # Read session file and verify mode info is saved
            import json
            from pathlib import Path

            session_file = Path(result['session_file'])
            assert session_file.exists()

            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            assert 'system_mode' in session_data
            assert session_data['system_mode']['mode'] in [MODE_FULL, MODE_PARTIAL, MODE_BASIC]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
