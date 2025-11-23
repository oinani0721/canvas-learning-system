"""
Integration Tests for Temporal Memory Manager with Neo4j Validation

Tests the complete initialization flow of temporal_memory_manager
with Neo4j connection validation integration.

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-31
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from memory_system.temporal_memory_manager import TemporalMemoryManager
from memory_system.neo4j_validator import (
    Neo4jConnectionError,
    ERROR_CONNECTION_REFUSED,
    ERROR_AUTH_FAILED,
    ERROR_DATABASE_NOT_FOUND
)


class TestTemporalMemoryManagerInitialization:
    """Test temporal memory manager initialization with validation"""

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'false'}, clear=False)
    def test_initialization_success_with_validation(self, mock_validate):
        """Test successful initialization when Neo4j validation passes"""
        # Mock successful validation
        mock_validate.return_value = {
            'available': True,
            'error_type': None,
            'error': '',
            'suggestion': '',
            'estimated_fix_time': ''
        }

        # Create manager with config
        config = {
            'neo4j_uri': 'bolt://localhost:7687',
            'neo4j_username': 'neo4j',
            'neo4j_password': 'testpassword',
            'database_name': 'ultrathink'
        }

        # Should not raise exception
        manager = TemporalMemoryManager(config=config)

        # Verify validation was called with correct parameters
        mock_validate.assert_called_once_with(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='testpassword',
            database='ultrathink'
        )

        # Verify manager was initialized
        assert manager.neo4j_uri == 'bolt://localhost:7687'
        assert manager.neo4j_username == 'neo4j'
        assert manager.database_name == 'ultrathink'

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'false'}, clear=False)
    def test_initialization_failure_connection_refused(self, mock_validate):
        """Test initialization fails when Neo4j connection is refused"""
        # Mock validation failure
        mock_validate.return_value = {
            'available': False,
            'error_type': ERROR_CONNECTION_REFUSED,
            'error': 'Neo4j端口7687不可达',
            'suggestion': '启动Neo4j数据库服务',
            'estimated_fix_time': '30秒'
        }

        config = {
            'neo4j_uri': 'bolt://localhost:7687',
            'neo4j_username': 'neo4j',
            'neo4j_password': 'testpassword',
            'database_name': 'ultrathink'
        }

        # Should raise Neo4jConnectionError
        with pytest.raises(Neo4jConnectionError) as exc_info:
            TemporalMemoryManager(config=config)

        # Verify error contains all required information
        error = exc_info.value
        assert error.error_type == ERROR_CONNECTION_REFUSED
        assert error.error == 'Neo4j端口7687不可达'
        assert error.suggestion == '启动Neo4j数据库服务'
        assert error.estimated_fix_time == '30秒'

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'false'}, clear=False)
    def test_initialization_failure_auth_failed(self, mock_validate):
        """Test initialization fails when Neo4j authentication fails"""
        # Mock authentication failure
        mock_validate.return_value = {
            'available': False,
            'error_type': ERROR_AUTH_FAILED,
            'error': '身份验证失败: 用户名或密码错误',
            'suggestion': '请检查.env文件中的NEO4J_USERNAME和NEO4J_PASSWORD配置',
            'estimated_fix_time': '2分钟'
        }

        config = {
            'neo4j_uri': 'bolt://localhost:7687',
            'neo4j_username': 'neo4j',
            'neo4j_password': 'wrong_password',
            'database_name': 'ultrathink'
        }

        # Should raise Neo4jConnectionError
        with pytest.raises(Neo4jConnectionError) as exc_info:
            TemporalMemoryManager(config=config)

        error = exc_info.value
        assert error.error_type == ERROR_AUTH_FAILED
        assert '身份验证失败' in error.error
        assert 'NEO4J_USERNAME和NEO4J_PASSWORD' in error.suggestion
        assert error.estimated_fix_time == '2分钟'

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'false'}, clear=False)
    def test_initialization_failure_database_not_found(self, mock_validate):
        """Test initialization fails when database doesn't exist"""
        # Mock database not found
        mock_validate.return_value = {
            'available': False,
            'error_type': ERROR_DATABASE_NOT_FOUND,
            'error': '数据库"ultrathink"不存在。可用数据库: neo4j, system',
            'suggestion': '创建数据库"ultrathink"。在Neo4j Browser中执行:\n  CREATE DATABASE ultrathink',
            'estimated_fix_time': '1分钟'
        }

        config = {
            'neo4j_uri': 'bolt://localhost:7687',
            'neo4j_username': 'neo4j',
            'neo4j_password': 'testpassword',
            'database_name': 'ultrathink'
        }

        # Should raise Neo4jConnectionError
        with pytest.raises(Neo4jConnectionError) as exc_info:
            TemporalMemoryManager(config=config)

        error = exc_info.value
        assert error.error_type == ERROR_DATABASE_NOT_FOUND
        assert 'ultrathink' in error.error
        assert 'CREATE DATABASE' in error.suggestion
        assert error.estimated_fix_time == '1分钟'

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'true'}, clear=False)
    def test_initialization_skip_validation_in_test_mode(self, mock_validate):
        """Test that validation is skipped when SKIP_NEO4J_VALIDATION=true"""
        config = {
            'neo4j_uri': 'bolt://localhost:7687',
            'neo4j_username': 'neo4j',
            'neo4j_password': 'testpassword',
            'database_name': 'ultrathink'
        }

        # Should not raise exception even without mocking validation result
        manager = TemporalMemoryManager(config=config)

        # Verify validation was NOT called
        mock_validate.assert_not_called()

        # Manager should still be created
        assert manager.neo4j_uri == 'bolt://localhost:7687'
        assert manager.database_name == 'ultrathink'

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {}, clear=False)
    def test_initialization_with_default_config(self, mock_validate):
        """Test initialization with default configuration from environment"""
        # Remove SKIP_NEO4J_VALIDATION if it exists
        os.environ.pop('SKIP_NEO4J_VALIDATION', None)

        # Mock successful validation
        mock_validate.return_value = {
            'available': True,
            'error_type': None,
            'error': '',
            'suggestion': '',
            'estimated_fix_time': ''
        }

        # Set environment variables
        with patch.dict(os.environ, {
            'NEO4J_URI': 'bolt://testhost:7687',
            'NEO4J_USERNAME': 'testuser',
            'NEO4J_PASSWORD': 'testpass',
            'NEO4J_DATABASE': 'testdb'
        }):
            # Create manager without config (should use env vars)
            manager = TemporalMemoryManager()

            # Verify it used environment variables
            assert manager.neo4j_uri == 'bolt://testhost:7687'
            assert manager.neo4j_username == 'testuser'
            assert manager.neo4j_password == 'testpass'
            assert manager.database_name == 'testdb'

            # Verify validation was called with env vars
            mock_validate.assert_called_once_with(
                uri='bolt://testhost:7687',
                username='testuser',
                password='testpass',
                database='testdb'
            )

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'false'}, clear=False)
    def test_error_message_contains_all_fields(self, mock_validate):
        """Test that error message includes error, suggestion, and estimated_fix_time"""
        # Mock validation failure with all fields
        mock_validate.return_value = {
            'available': False,
            'error_type': ERROR_CONNECTION_REFUSED,
            'error': 'Connection refused on port 7687',
            'suggestion': 'Start Neo4j service using: neo4j.bat console',
            'estimated_fix_time': '30秒'
        }

        config = {
            'neo4j_uri': 'bolt://localhost:7687',
            'neo4j_username': 'neo4j',
            'neo4j_password': 'testpassword',
            'database_name': 'ultrathink'
        }

        with pytest.raises(Neo4jConnectionError) as exc_info:
            TemporalMemoryManager(config=config)

        error_message = str(exc_info.value)

        # Verify all required fields are in the error message
        assert 'Connection refused on port 7687' in error_message
        assert 'Start Neo4j service using: neo4j.bat console' in error_message
        assert '30秒' in error_message
        assert 'deployment\\setup_environment.bat' in error_message

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'false'}, clear=False)
    def test_config_precedence_over_environment(self, mock_validate):
        """Test that config dict takes precedence over environment variables"""
        # Mock successful validation
        mock_validate.return_value = {
            'available': True,
            'error_type': None,
            'error': '',
            'suggestion': '',
            'estimated_fix_time': ''
        }

        # Set environment variables
        with patch.dict(os.environ, {
            'NEO4J_URI': 'bolt://envhost:7687',
            'NEO4J_USERNAME': 'envuser',
            'NEO4J_PASSWORD': 'envpass',
            'NEO4J_DATABASE': 'envdb'
        }):
            # Create manager with explicit config (should override env vars)
            config = {
                'neo4j_uri': 'bolt://confighost:7687',
                'neo4j_username': 'configuser',
                'neo4j_password': 'configpass',
                'database_name': 'configdb'
            }
            manager = TemporalMemoryManager(config=config)

            # Verify it used config, not env vars
            assert manager.neo4j_uri == 'bolt://confighost:7687'
            assert manager.neo4j_username == 'configuser'
            assert manager.neo4j_password == 'configpass'
            assert manager.database_name == 'configdb'

            # Verify validation was called with config values
            mock_validate.assert_called_once_with(
                uri='bolt://confighost:7687',
                username='configuser',
                password='configpass',
                database='configdb'
            )


class TestTemporalMemoryManagerValidationIntegration:
    """Test that validation integrates properly into initialization flow"""

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'false'}, clear=False)
    def test_validation_called_before_graphiti_initialization(self, mock_validate):
        """Test that Neo4j validation happens before Graphiti initialization"""
        call_order = []

        def validation_side_effect(*args, **kwargs):
            call_order.append('validation')
            return {
                'available': True,
                'error_type': None,
                'error': '',
                'suggestion': '',
                'estimated_fix_time': ''
            }

        mock_validate.side_effect = validation_side_effect

        # Mock _initialize_graphiti to track when it's called
        original_init = TemporalMemoryManager._initialize_graphiti

        def init_graphiti_wrapper(self):
            call_order.append('graphiti_init')
            # Don't actually initialize Graphiti, just mark it was called
            self.is_initialized = True

        with patch.object(TemporalMemoryManager, '_initialize_graphiti', init_graphiti_wrapper):
            TemporalMemoryManager(config={'neo4j_uri': 'bolt://localhost:7687'})

        # Verify validation was called before Graphiti initialization
        assert call_order == ['validation', 'graphiti_init']

    @patch('memory_system.temporal_memory_manager.validate_neo4j_connection')
    @patch.dict(os.environ, {'SKIP_NEO4J_VALIDATION': 'false'}, clear=False)
    def test_graphiti_not_initialized_when_validation_fails(self, mock_validate):
        """Test that Graphiti initialization is not attempted if validation fails"""
        # Mock validation failure
        mock_validate.return_value = {
            'available': False,
            'error_type': ERROR_CONNECTION_REFUSED,
            'error': 'Connection refused',
            'suggestion': 'Start Neo4j',
            'estimated_fix_time': '30秒'
        }

        graphiti_called = False

        def mock_graphiti_init(self):
            nonlocal graphiti_called
            graphiti_called = True

        with patch.object(TemporalMemoryManager, '_initialize_graphiti', mock_graphiti_init):
            with pytest.raises(Neo4jConnectionError):
                TemporalMemoryManager(config={'neo4j_uri': 'bolt://localhost:7687'})

        # Verify Graphiti initialization was never called
        assert graphiti_called is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
