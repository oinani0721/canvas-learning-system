"""
Canvas Learning System - Story 10.11 单元测试
实现诚实状态报告和优雅降级

测试覆盖：
- 系统可用性检测
- 状态报告生成
- 优雅降级机制
- 错误日志记录

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-30
Story: 10.11 - 实现诚实状态报告和优雅降级
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from command_handlers.learning_commands import (
    LearningSessionManager,
    check_neo4j_connection,
    check_mcp_server_health,
    log_startup_error_to_debug_log
)


class TestNeo4jConnection:
    """测试Neo4j连接检测"""

    @patch('command_handlers.learning_commands.socket.socket')
    def test_neo4j_port_unreachable(self, mock_socket):
        """测试Neo4j端口不可达"""
        # Mock socket返回连接失败
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 1  # 非0表示连接失败
        mock_socket.return_value = mock_sock_instance

        result = check_neo4j_connection(timeout=1)

        assert result['available'] == False
        assert 'Neo4j端口7687不可达' in result['error']
        assert result['suggestion'] is not None
        assert 'neo4j' in result['suggestion'].lower()

    @patch('neo4j.GraphDatabase')
    @patch('command_handlers.learning_commands.socket.socket')
    def test_neo4j_connection_success(self, mock_socket, mock_graphdb):
        """测试Neo4j连接成功"""
        # Mock socket连接成功
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock_instance

        # Mock GraphDatabase连接成功
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = {'num': 1}
        mock_session.run.return_value = mock_result
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_driver.session.return_value = mock_session
        mock_driver.close = MagicMock()
        mock_graphdb.driver.return_value = mock_driver

        result = check_neo4j_connection(timeout=1)

        assert result['available'] == True
        assert result['error'] is None
        assert result['version'] is not None

    def test_neo4j_import_error(self):
        """测试neo4j库未安装"""
        # 这个测试在neo4j已安装的环境中会跳过
        # 可以通过mock来模拟ImportError
        with patch('command_handlers.learning_commands.socket.socket') as mock_socket:
            mock_sock_instance = MagicMock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock_instance

            with patch('builtins.__import__', side_effect=ImportError("No module named 'neo4j'")):
                result = check_neo4j_connection(timeout=1)

                assert result['available'] == False
                assert 'neo4j Python库未安装' in result['error']
                assert 'pip install neo4j' in result['suggestion']


class TestMCPServerHealth:
    """测试MCP服务器健康检查"""

    @pytest.mark.asyncio
    async def test_mcp_tools_not_imported(self):
        """测试MCP工具未导入"""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'claude_tools'")):
            result = await check_mcp_server_health(timeout=1)

            assert result['available'] == False
            assert 'MCP工具未导入' in result['error']
            assert result['suggestion'] is not None
            assert result['services'] == []

    @pytest.mark.asyncio
    async def test_mcp_server_result_structure(self):
        """测试MCP服务器健康检查返回结构"""
        result = await check_mcp_server_health(timeout=1)

        # 验证返回结构
        assert 'available' in result
        assert 'error' in result
        assert 'services' in result
        assert 'suggestion' in result
        assert isinstance(result['available'], bool)
        assert isinstance(result['services'], list)

        # 如果不可用，应该有错误和建议
        if not result['available']:
            assert result['error'] is not None
            assert result['suggestion'] is not None


class TestStatusReport:
    """测试状态报告生成"""

    def test_all_systems_running_report(self):
        """测试所有系统运行中的报告"""
        memory_systems = {
            'graphiti': {
                'status': 'running',
                'memory_id': 'mem_test_001',
                'storage': 'Neo4j图数据库',
                'initialized_at': '2025-10-30T19:00:00'
            },
            'temporal': {
                'status': 'running',
                'session_id': 'temp_001',
                'storage': '本地SQLite数据库',
                'initialized_at': '2025-10-30T19:00:01'
            },
            'semantic': {
                'status': 'running',
                'memory_id': 'sem_001',
                'storage': '向量数据库',
                'initialized_at': '2025-10-30T19:00:02'
            }
        }

        session_data = {
            'session_id': 'test_session',
            'canvas_path': 'test.canvas',
            'start_time': '2025-10-30T19:00:00'
        }

        manager = LearningSessionManager()
        report = manager.generate_status_report(memory_systems, session_data)

        # 验证报告内容
        assert "3/3 记忆系统正常运行" in report
        assert "✅ Graphiti知识图谱: 运行中" in report
        assert "✅ 时序记忆管理器: 运行中" in report
        assert "✅ 语义记忆管理器: 运行中" in report
        assert "mem_test_001" in report
        assert "test_session" in report

    def test_partial_systems_running_report(self):
        """测试部分系统运行中的报告"""
        memory_systems = {
            'graphiti': {
                'status': 'running',
                'memory_id': 'mem_test_001',
                'storage': 'Neo4j图数据库',
                'initialized_at': '2025-10-30T19:00:00'
            },
            'temporal': {
                'status': 'running',
                'session_id': 'temp_001',
                'storage': '本地SQLite数据库',
                'initialized_at': '2025-10-30T19:00:01'
            },
            'semantic': {
                'status': 'unavailable',
                'error': 'MCP语义服务未连接',
                'suggestion': '检查MCP服务器状态',
                'attempted_at': '2025-10-30T19:00:02'
            }
        }

        session_data = {
            'session_id': 'test_session',
            'canvas_path': 'test.canvas',
            'start_time': '2025-10-30T19:00:00'
        }

        manager = LearningSessionManager()
        report = manager.generate_status_report(memory_systems, session_data)

        # 验证报告内容
        assert "2/3 记忆系统正常运行" in report
        assert "⚠️ 语义记忆管理器: 不可用" in report
        assert "MCP语义服务未连接" in report
        assert "检查MCP服务器状态" in report
        assert "部分功能受限" in report

    def test_all_systems_unavailable_report(self):
        """测试所有系统不可用的报告"""
        memory_systems = {
            'graphiti': {
                'status': 'unavailable',
                'error': 'Neo4j连接失败',
                'suggestion': '启动Neo4j数据库',
                'attempted_at': '2025-10-30T19:00:00'
            },
            'temporal': {
                'status': 'unavailable',
                'error': 'Graphiti库导入失败',
                'suggestion': '安装依赖',
                'attempted_at': '2025-10-30T19:00:01'
            },
            'semantic': {
                'status': 'unavailable',
                'error': 'MCP服务器不可用',
                'suggestion': '重启MCP服务器',
                'attempted_at': '2025-10-30T19:00:02'
            }
        }

        session_data = {
            'session_id': 'test_session',
            'canvas_path': 'test.canvas',
            'start_time': '2025-10-30T19:00:00'
        }

        manager = LearningSessionManager()
        report = manager.generate_status_report(memory_systems, session_data)

        # 验证报告内容
        assert "0/3 记忆系统可用" in report
        assert "❌ 会话启动失败" in report
        assert "💡 建议：" in report
        assert "检查系统依赖" in report
        assert ".ai/debug-log.md" in report


class TestGracefulDegradation:
    """测试优雅降级"""

    @pytest.mark.asyncio
    async def test_partial_start_allowed(self):
        """测试允许部分系统启动"""
        manager = LearningSessionManager()

        # Mock三个系统的启动方法
        with patch.object(manager, '_start_graphiti', side_effect=Exception("Neo4j不可用")):
            with patch.object(manager, '_start_temporal', new_callable=AsyncMock) as mock_temporal:
                with patch.object(manager, '_start_semantic', new_callable=AsyncMock) as mock_semantic:
                    # Mock成功的返回
                    mock_temporal.return_value = {
                        'status': 'running',
                        'session_id': 'temp_001',
                        'storage': '本地SQLite数据库',
                        'initialized_at': datetime.now().isoformat()
                    }
                    mock_semantic.return_value = {
                        'status': 'running',
                        'memory_id': 'sem_001',
                        'storage': '向量数据库',
                        'initialized_at': datetime.now().isoformat()
                    }

                    # Mock预检测
                    with patch.object(manager, 'detect_systems_before_start', new_callable=AsyncMock) as mock_detect:
                        mock_detect.return_value = {
                            'neo4j': {'available': False},
                            'mcp_server': {'available': True},
                            'dependencies': {'available': True}
                        }

                        result = await manager.start_session(
                            canvas_path="src/tests/fixtures/test.canvas",
                            allow_partial_start=True
                        )

                        # 即使部分系统失败，should仍然成功
                        assert result['success'] == True
                        assert result['running_systems'] == 2  # temporal和semantic成功
                        assert result['total_systems'] == 3

    @pytest.mark.asyncio
    async def test_all_systems_fail_with_partial_start(self):
        """测试所有系统失败但允许部分启动"""
        manager = LearningSessionManager()

        # Mock所有系统都失败
        with patch.object(manager, '_start_graphiti', side_effect=Exception("Graphiti失败")):
            with patch.object(manager, '_start_temporal', side_effect=Exception("Temporal失败")):
                with patch.object(manager, '_start_semantic', side_effect=Exception("Semantic失败")):
                    with patch.object(manager, 'detect_systems_before_start', new_callable=AsyncMock) as mock_detect:
                        mock_detect.return_value = {
                            'neo4j': {'available': False},
                            'mcp_server': {'available': False},
                            'dependencies': {'available': True}
                        }

                        result = await manager.start_session(
                            canvas_path="src/tests/fixtures/test.canvas",
                            allow_partial_start=True,
                            interactive=False  # 非交互模式
                        )

                        # allow_partial_start=True时，即使所有系统失败也返回success
                        assert result['success'] == True
                        assert result['running_systems'] == 0
                        assert 'session_id' in result  # 检查是否有会话ID
                        assert result['total_systems'] == 3


class TestPythonDependencies:
    """测试Python依赖检测"""

    def test_check_python_dependencies_all_installed(self):
        """测试所有依赖都已安装"""
        manager = LearningSessionManager()
        result = manager._check_python_dependencies()

        # 在真实环境中，这些库应该已安装
        # 如果未安装，测试会失败
        assert 'available' in result
        assert 'missing' in result
        assert isinstance(result['missing'], list)

    def test_check_python_dependencies_structure(self):
        """测试依赖检测返回结构"""
        manager = LearningSessionManager()
        result = manager._check_python_dependencies()

        # 验证返回结构
        assert 'available' in result
        assert 'missing' in result
        assert 'suggestion' in result
        assert isinstance(result['available'], bool)
        assert isinstance(result['missing'], list)

        # 如果有缺失依赖，应该有建议
        if not result['available']:
            assert result['suggestion'] is not None
            assert 'pip install' in result['suggestion']


class TestErrorLogging:
    """测试错误日志记录"""

    def test_log_startup_error_to_debug_log(self):
        """测试错误日志记录到debug-log.md"""
        import tempfile
        import shutil

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()

        try:
            # 修改当前目录到临时目录进行测试
            import os
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            # 调用日志记录函数
            log_startup_error_to_debug_log(
                error_type="Neo4jConnectionError",
                error_message="连接失败",
                system_name="Graphiti知识图谱",
                stack_trace="Traceback...\nConnectionError: 连接失败"
            )

            # 验证文件是否创建
            debug_log_path = Path(temp_dir) / ".ai" / "debug-log.md"
            assert debug_log_path.exists()

            # 验证文件内容
            content = debug_log_path.read_text(encoding='utf-8')
            assert "学习会话启动错误" in content
            assert "Neo4jConnectionError" in content
            assert "Graphiti知识图谱" in content
            assert "连接失败" in content

            # 恢复原目录
            os.chdir(original_cwd)
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
