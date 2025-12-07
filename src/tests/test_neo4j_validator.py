"""
Unit Tests for Neo4j Validator Module

Tests all validation functions with mocked Neo4j connections
to ensure fail-fast behavior and proper error reporting.

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-31
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from memory_system.neo4j_validator import (
    ERROR_AUTH_FAILED,
    ERROR_CONNECTION_REFUSED,
    ERROR_DATABASE_NOT_FOUND,
    Neo4jConnectionError,
    check_database_exists,
    check_neo4j_authentication,
    check_socket_connection,
    parse_neo4j_uri,
    validate_neo4j_connection,
)


class TestParseNeo4jUri:
    """Test URI parsing functionality"""

    def test_parse_valid_bolt_uri(self):
        """Test parsing valid bolt:// URI"""
        host, port = parse_neo4j_uri("bolt://localhost:7687")
        assert host == "localhost"
        assert port == 7687

    def test_parse_valid_neo4j_uri(self):
        """Test parsing valid neo4j:// URI"""
        host, port = parse_neo4j_uri("neo4j://example.com:7474")
        assert host == "example.com"
        assert port == 7474

    def test_parse_secure_bolt_uri(self):
        """Test parsing bolt+s:// URI"""
        host, port = parse_neo4j_uri("bolt+s://secure.host.com:7687")
        assert host == "secure.host.com"
        assert port == 7687

    def test_parse_invalid_uri_missing_port(self):
        """Test parsing URI without port raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            parse_neo4j_uri("bolt://localhost")
        assert "Invalid Neo4j URI format" in str(exc_info.value)

    def test_parse_invalid_uri_wrong_scheme(self):
        """Test parsing URI with wrong scheme raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            parse_neo4j_uri("http://localhost:7687")
        assert "Invalid Neo4j URI format" in str(exc_info.value)

    def test_parse_invalid_uri_no_scheme(self):
        """Test parsing URI without scheme raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            parse_neo4j_uri("localhost:7687")
        assert "Invalid Neo4j URI format" in str(exc_info.value)


class TestSocketConnection:
    """Test socket connectivity functionality"""

    @patch('socket.socket')
    def test_socket_connection_success(self, mock_socket):
        """Test successful socket connection"""
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock_instance

        result = check_socket_connection("localhost", 7687, timeout=2)

        assert result['success'] is True
        assert result['error'] == ''
        mock_sock_instance.settimeout.assert_called_once_with(2)
        mock_sock_instance.connect_ex.assert_called_once_with(("localhost", 7687))
        mock_sock_instance.close.assert_called_once()

    @patch('socket.socket')
    def test_socket_connection_failure(self, mock_socket):
        """Test failed socket connection (port unreachable)"""
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 111  # Connection refused
        mock_socket.return_value = mock_sock_instance

        result = check_socket_connection("localhost", 7687, timeout=2)

        assert result['success'] is False
        assert '端口7687不可达' in result['error']
        assert '111' in result['error']

    @patch('socket.socket')
    def test_socket_connection_timeout(self, mock_socket):
        """Test socket connection timeout"""
        import socket
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.side_effect = socket.timeout("Connection timeout")
        mock_socket.return_value = mock_sock_instance

        result = check_socket_connection("localhost", 7687, timeout=2)

        assert result['success'] is False
        assert '连接超时' in result['error']

    @patch('socket.socket')
    def test_socket_connection_hostname_resolution_failure(self, mock_socket):
        """Test hostname resolution failure"""
        import socket
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.side_effect = socket.gaierror(-2, "Name or service not known")
        mock_socket.return_value = mock_sock_instance

        result = check_socket_connection("invalid.host.name", 7687, timeout=2)

        assert result['success'] is False
        assert '主机名解析失败' in result['error']

    def test_socket_connection_timeout_value(self):
        """Test that timeout is properly set (verify 2 second timeout)"""
        with patch('socket.socket') as mock_socket:
            mock_sock_instance = MagicMock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock_instance

            check_socket_connection("localhost", 7687, timeout=2)

            # Verify timeout was set to 2 seconds
            mock_sock_instance.settimeout.assert_called_once_with(2)


class TestNeo4jAuthentication:
    """Test Neo4j authentication functionality"""

    @patch('memory_system.neo4j_validator.GraphDatabase.driver')
    def test_authentication_success(self, mock_driver):
        """Test successful Neo4j authentication"""
        # Mock successful driver and session
        mock_driver_instance = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = {'test': 1}
        mock_session.run.return_value = mock_result
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance

        result = check_neo4j_authentication(
            "bolt://localhost:7687",
            "neo4j",
            "password",
            timeout=2
        )

        assert result['success'] is True
        assert result['error'] == ''
        assert result['error_type'] is None
        mock_driver_instance.close.assert_called_once()

    @patch('memory_system.neo4j_validator.GraphDatabase.driver')
    def test_authentication_failure_wrong_credentials(self, mock_driver):
        """Test authentication failure with wrong credentials"""
        from neo4j.exceptions import AuthError

        # Mock AuthError
        mock_driver.side_effect = AuthError("Authentication failed")

        result = check_neo4j_authentication(
            "bolt://localhost:7687",
            "neo4j",
            "wrong_password",
            timeout=2
        )

        assert result['success'] is False
        assert '身份验证失败' in result['error']
        assert result['error_type'] == ERROR_AUTH_FAILED

    @patch('memory_system.neo4j_validator.GraphDatabase.driver')
    def test_authentication_service_unavailable(self, mock_driver):
        """Test authentication failure when service is unavailable"""
        from neo4j.exceptions import ServiceUnavailable

        # Mock ServiceUnavailable exception
        mock_driver.side_effect = ServiceUnavailable("Connection refused")

        result = check_neo4j_authentication(
            "bolt://localhost:7687",
            "neo4j",
            "password",
            timeout=2
        )

        assert result['success'] is False
        assert 'Neo4j服务不可用' in result['error']
        assert result['error_type'] == ERROR_CONNECTION_REFUSED

    @patch('memory_system.neo4j_validator.GraphDatabase.driver')
    def test_authentication_timeout(self, mock_driver):
        """Test authentication timeout scenario"""
        # Mock connection timeout
        mock_driver.side_effect = Exception("Connection timeout")

        result = check_neo4j_authentication(
            "bolt://localhost:7687",
            "neo4j",
            "password",
            timeout=2
        )

        assert result['success'] is False
        assert '认证测试失败' in result['error']
        assert result['error_type'] == ERROR_AUTH_FAILED


class TestDatabaseExists:
    """Test database existence verification"""

    def test_database_exists_success(self):
        """Test database exists verification - database found"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = [
            {'name': 'neo4j'},
            {'name': 'system'},
            {'name': 'ultrathink'}
        ]
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session

        result = check_database_exists(mock_driver, "ultrathink")

        assert result['exists'] is True
        assert 'ultrathink' in result['available_databases']
        assert result['error'] == ''

    def test_database_not_exists(self):
        """Test database exists verification - database not found"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = [
            {'name': 'neo4j'},
            {'name': 'system'}
        ]
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session

        result = check_database_exists(mock_driver, "ultrathink")

        assert result['exists'] is False
        assert 'ultrathink' not in result['available_databases']
        assert result['error'] == ''

    def test_database_exists_fallback_success(self):
        """Test database verification fallback when SHOW DATABASES fails"""
        mock_driver = MagicMock()

        # First call to session (system database) fails
        mock_system_session = MagicMock()
        mock_system_session.run.side_effect = Exception("Access denied")

        # Second call to session (target database) succeeds
        mock_target_session = MagicMock()
        mock_target_session.run.return_value = None  # Successful connection

        mock_driver.session.return_value.__enter__.side_effect = [
            mock_system_session,
            mock_target_session
        ]

        result = check_database_exists(mock_driver, "ultrathink")

        assert result['exists'] is True
        assert 'ultrathink' in result['available_databases']

    def test_database_exists_fallback_failure(self):
        """Test database verification fallback when both attempts fail"""
        mock_driver = MagicMock()

        # Both calls fail
        mock_session = MagicMock()
        mock_session.run.side_effect = Exception("Database not found")
        mock_driver.session.return_value.__enter__.return_value = mock_session

        result = check_database_exists(mock_driver, "ultrathink")

        assert result['exists'] is False
        assert result['available_databases'] == []
        assert '无法验证数据库存在性' in result['error']


class TestValidateNeo4jConnection:
    """Test complete validation workflow"""

    @patch('memory_system.neo4j_validator.GraphDatabase.driver')
    @patch('memory_system.neo4j_validator.check_neo4j_authentication')
    @patch('memory_system.neo4j_validator.check_socket_connection')
    def test_validate_connection_success(
        self,
        mock_socket,
        mock_auth,
        mock_driver
    ):
        """Test complete validation succeeds when all checks pass"""
        # Mock all validations to succeed
        mock_socket.return_value = {'success': True, 'error': ''}
        mock_auth.return_value = {
            'success': True,
            'error': '',
            'error_type': None
        }

        mock_driver_instance = MagicMock()
        mock_session = MagicMock()
        mock_result = [
            {'name': 'neo4j'},
            {'name': 'system'},
            {'name': 'ultrathink'}
        ]
        mock_session.run.return_value = mock_result
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance

        result = validate_neo4j_connection(
            "bolt://localhost:7687",
            "neo4j",
            "password",
            "ultrathink"
        )

        assert result['available'] is True
        assert result['error_type'] is None
        assert result['error'] == ''
        assert result['suggestion'] == ''
        assert result['estimated_fix_time'] == ''

    @patch('memory_system.neo4j_validator.check_socket_connection')
    def test_validate_connection_socket_failure(self, mock_socket):
        """Test validation fails at socket test (fail-fast)"""
        mock_socket.return_value = {
            'success': False,
            'error': '端口7687不可达'
        }

        result = validate_neo4j_connection(
            "bolt://localhost:7687",
            "neo4j",
            "password",
            "ultrathink"
        )

        assert result['available'] is False
        assert result['error_type'] == ERROR_CONNECTION_REFUSED
        assert '端口7687不可达' in result['error']
        assert '启动Neo4j数据库服务' in result['suggestion']
        assert result['estimated_fix_time'] == '30秒'

    @patch('memory_system.neo4j_validator.check_neo4j_authentication')
    @patch('memory_system.neo4j_validator.check_socket_connection')
    def test_validate_connection_auth_failure(self, mock_socket, mock_auth):
        """Test validation fails at authentication test"""
        mock_socket.return_value = {'success': True, 'error': ''}
        mock_auth.return_value = {
            'success': False,
            'error': '身份验证失败: 用户名或密码错误',
            'error_type': ERROR_AUTH_FAILED
        }

        result = validate_neo4j_connection(
            "bolt://localhost:7687",
            "neo4j",
            "wrong_password",
            "ultrathink"
        )

        assert result['available'] is False
        assert result['error_type'] == ERROR_AUTH_FAILED
        assert '身份验证失败' in result['error']
        assert 'NEO4J_USERNAME和NEO4J_PASSWORD' in result['suggestion']
        assert result['estimated_fix_time'] == '2分钟'

    @patch('memory_system.neo4j_validator.GraphDatabase.driver')
    @patch('memory_system.neo4j_validator.check_neo4j_authentication')
    @patch('memory_system.neo4j_validator.check_socket_connection')
    def test_validate_connection_database_not_found(
        self,
        mock_socket,
        mock_auth,
        mock_driver
    ):
        """Test validation fails when database doesn't exist"""
        mock_socket.return_value = {'success': True, 'error': ''}
        mock_auth.return_value = {
            'success': True,
            'error': '',
            'error_type': None
        }

        # Mock database not existing
        mock_driver_instance = MagicMock()
        mock_session = MagicMock()
        mock_result = [
            {'name': 'neo4j'},
            {'name': 'system'}
        ]
        mock_session.run.return_value = mock_result
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance

        result = validate_neo4j_connection(
            "bolt://localhost:7687",
            "neo4j",
            "password",
            "ultrathink"
        )

        assert result['available'] is False
        assert result['error_type'] == ERROR_DATABASE_NOT_FOUND
        assert '数据库"ultrathink"不存在' in result['error']
        assert 'CREATE DATABASE ultrathink' in result['suggestion']
        assert result['estimated_fix_time'] == '1分钟'

    def test_validate_connection_invalid_uri(self):
        """Test validation fails with invalid URI format"""
        result = validate_neo4j_connection(
            "invalid://localhost",
            "neo4j",
            "password",
            "ultrathink"
        )

        assert result['available'] is False
        assert result['error_type'] == ERROR_CONNECTION_REFUSED
        assert 'URI格式错误' in result['error']
        assert 'bolt://hostname:port' in result['suggestion']
        assert result['estimated_fix_time'] == '1分钟'

    @patch('memory_system.neo4j_validator.GraphDatabase.driver')
    @patch('memory_system.neo4j_validator.check_neo4j_authentication')
    @patch('memory_system.neo4j_validator.check_socket_connection')
    def test_validate_connection_performance(
        self,
        mock_socket,
        mock_auth,
        mock_driver
    ):
        """Test that validation completes within 2 seconds"""
        # Mock all validations to succeed quickly
        mock_socket.return_value = {'success': True, 'error': ''}
        mock_auth.return_value = {
            'success': True,
            'error': '',
            'error_type': None
        }

        mock_driver_instance = MagicMock()
        mock_session = MagicMock()
        mock_result = [{'name': 'ultrathink'}]
        mock_session.run.return_value = mock_result
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance

        # Measure execution time
        start_time = time.time()
        validate_neo4j_connection(
            "bolt://localhost:7687",
            "neo4j",
            "password",
            "ultrathink"
        )
        elapsed_time = time.time() - start_time

        # Verify completes within 2 seconds
        assert elapsed_time < 2.0, f"Validation took {elapsed_time:.2f}s, expected < 2s"


class TestNeo4jConnectionError:
    """Test Neo4jConnectionError exception class"""

    def test_error_initialization(self):
        """Test error object initialization"""
        error = Neo4jConnectionError(
            error_type=ERROR_CONNECTION_REFUSED,
            error="Neo4j端口7687不可达",
            suggestion="启动Neo4j数据库服务",
            estimated_fix_time="30秒"
        )

        assert error.error_type == ERROR_CONNECTION_REFUSED
        assert error.error == "Neo4j端口7687不可达"
        assert error.suggestion == "启动Neo4j数据库服务"
        assert error.estimated_fix_time == "30秒"

    def test_error_message_format(self):
        """Test formatted error message contains all required fields"""
        error = Neo4jConnectionError(
            error_type=ERROR_AUTH_FAILED,
            error="身份验证失败",
            suggestion="检查.env文件中的密码",
            estimated_fix_time="2分钟"
        )

        message = str(error)

        assert "❌ Neo4j数据库连接失败" in message
        assert f"错误类型: {ERROR_AUTH_FAILED}" in message
        assert "原因: 身份验证失败" in message
        assert "解决方案: 检查.env文件中的密码" in message
        assert "预计时间: 2分钟" in message
        assert "deployment\\setup_environment.bat" in message

    def test_error_password_sanitization(self):
        """Test that passwords are sanitized in error messages"""
        error = Neo4jConnectionError(
            error_type=ERROR_AUTH_FAILED,
            error="Authentication failed with password=secret123",
            suggestion="Check your password=mypassword in config",
            estimated_fix_time="2分钟"
        )

        message = str(error)

        # Verify passwords are replaced with ***
        assert "password=***" in message
        assert "secret123" not in message
        assert "mypassword" not in message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
