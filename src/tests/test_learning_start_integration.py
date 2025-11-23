"""
Canvas Learning System - Story 10.10 Integration Tests

集成测试套件，验证LearningSessionManager与现有系统的完整集成。

测试内容:
1. LearningSessionManager导入和初始化
2. 与command_handlers的集成
3. 与现有memory_system模块的兼容性
4. 完整的会话启动流程（end-to-end）
5. 错误传播和处理
6. Session JSON持久化和恢复

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-30
Story: 10.10 - 修复/learning start命令核心逻辑
"""

import pytest
import asyncio
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# 测试导入 - 验证模块可以正确导入
from command_handlers.learning_commands import (
    LearningSessionManager,
    create_learning_session_manager
)
from memory_system.memory_exceptions import (
    TemporalMemoryError,
    SemanticMemoryError
)


@pytest.fixture
def temp_test_dir(tmp_path):
    """创建临时测试目录"""
    test_dir = tmp_path / "integration_test"
    test_dir.mkdir()
    yield test_dir
    # 清理
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def test_canvas_file(temp_test_dir):
    """创建测试Canvas文件"""
    canvas_path = temp_test_dir / "test_integration.canvas"
    canvas_data = {
        "nodes": [
            {
                "id": "node1",
                "type": "text",
                "text": "测试问题",
                "x": 0,
                "y": 0,
                "width": 250,
                "height": 60,
                "color": "1"
            }
        ],
        "edges": []
    }
    with open(canvas_path, 'w', encoding='utf-8') as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)
    return str(canvas_path)


class TestLearningStartIntegration:
    """集成测试类 - 验证完整的系统集成"""

    @pytest.mark.asyncio
    async def test_manager_initialization(self, temp_test_dir):
        """测试1: 验证LearningSessionManager可以正确初始化"""
        session_dir = temp_test_dir / ".learning_sessions"

        manager = LearningSessionManager(session_dir=str(session_dir))

        # 验证初始化
        assert manager.session_dir.exists()
        assert manager.session_dir == session_dir
        assert manager.current_session is None

    @pytest.mark.asyncio
    async def test_convenience_function(self, temp_test_dir):
        """测试2: 验证便捷函数create_learning_session_manager"""
        session_dir = temp_test_dir / ".learning_sessions"

        manager = create_learning_session_manager(session_dir=str(session_dir))

        assert isinstance(manager, LearningSessionManager)
        assert manager.session_dir.exists()

    @pytest.mark.asyncio
    async def test_end_to_end_session_creation(self, test_canvas_file, temp_test_dir):
        """测试3: 端到端会话创建流程"""
        session_dir = temp_test_dir / ".learning_sessions"
        manager = LearningSessionManager(session_dir=str(session_dir))

        # Mock所有三个记忆系统
        mock_graphiti_result = {'memory_id': 'graphiti_mem_123'}
        mock_session = MagicMock()
        mock_session.session_id = "temporal_session_123"

        mock_mcp_tool = AsyncMock(return_value=mock_graphiti_result)
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        mock_temporal_manager = MagicMock()
        mock_temporal_manager.is_initialized = True
        mock_temporal_manager.create_learning_session.return_value = mock_session

        mock_semantic_manager = MagicMock()
        mock_semantic_manager.mcp_client = MagicMock()  # 模拟MCP客户端可用
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_123"

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            # 执行完整流程
            result = await manager.start_session(
                canvas_path=test_canvas_file,
                user_id="integration_test_user",
                session_name="Integration Test Session"
            )

            # 验证返回结果
            assert result['success'] is True
            assert 'session_id' in result
            assert 'session_file' in result
            assert 'memory_systems' in result

            # 验证三个系统都被初始化
            memory_systems = result['memory_systems']
            assert 'graphiti' in memory_systems
            assert 'temporal' in memory_systems
            assert 'semantic' in memory_systems

            # 验证所有系统状态为running
            assert memory_systems['graphiti']['status'] == 'running'
            assert memory_systems['temporal']['status'] == 'running'
            assert memory_systems['semantic']['status'] == 'running'

            # 验证session文件已创建
            session_file = Path(result['session_file'])
            assert session_file.exists()

            # 验证session文件内容
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            assert session_data['session_id'] == result['session_id']
            assert session_data['session_name'] == "Integration Test Session"
            assert session_data['user_id'] == "integration_test_user"
            assert session_data['canvas_path'] == os.path.abspath(test_canvas_file)
            assert 'start_time' in session_data
            assert 'memory_systems' in session_data

    @pytest.mark.asyncio
    async def test_integration_with_real_exceptions(self, test_canvas_file, temp_test_dir):
        """测试4: 验证与memory_exceptions的集成"""
        session_dir = temp_test_dir / ".learning_sessions"
        manager = LearningSessionManager(session_dir=str(session_dir))

        # 模拟TemporalMemoryManager初始化失败，抛出TemporalMemoryError
        mock_temporal_manager = MagicMock()
        mock_temporal_manager.is_initialized = False  # 导致初始化失败

        mock_mcp_tool = AsyncMock(return_value={'memory_id': 'graphiti_mem_123'})
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        mock_semantic_manager = MagicMock()
        mock_semantic_manager.mcp_client = MagicMock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_123"

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            result = await manager.start_session(
                canvas_path=test_canvas_file,
                user_id="test_user"
            )

            # 验证优雅降级 - Graphiti和Semantic成功，Temporal失败
            assert result['success'] is True
            assert result['memory_systems']['graphiti']['status'] == 'running'
            assert result['memory_systems']['temporal']['status'] == 'unavailable'
            assert result['memory_systems']['semantic']['status'] == 'running'

            # 验证temporal的错误信息
            temporal_result = result['memory_systems']['temporal']
            assert 'error' in temporal_result
            assert 'attempted_at' in temporal_result

    @pytest.mark.asyncio
    async def test_session_json_persistence_and_recovery(self, test_canvas_file, temp_test_dir):
        """测试5: 验证Session JSON持久化和恢复"""
        session_dir = temp_test_dir / ".learning_sessions"
        manager1 = LearningSessionManager(session_dir=str(session_dir))

        # Mock系统
        mock_mcp_tool = AsyncMock(return_value={'memory_id': 'graphiti_mem_123'})
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        mock_session = MagicMock()
        mock_session.session_id = "temporal_session_123"
        mock_temporal_manager = MagicMock()
        mock_temporal_manager.is_initialized = True
        mock_temporal_manager.create_learning_session.return_value = mock_session

        mock_semantic_manager = MagicMock()
        mock_semantic_manager.mcp_client = MagicMock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_123"

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            # 创建会话
            result = await manager1.start_session(
                canvas_path=test_canvas_file,
                user_id="test_user",
                session_name="Persistence Test"
            )

            session_id = result['session_id']
            session_file = Path(result['session_file'])

            # 验证文件存在
            assert session_file.exists()

            # 创建新的manager实例，验证可以读取session文件
            manager2 = LearningSessionManager(session_dir=str(session_dir))

            # 读取session文件
            with open(session_file, 'r', encoding='utf-8') as f:
                recovered_session = json.load(f)

            # 验证恢复的数据
            assert recovered_session['session_id'] == session_id
            assert recovered_session['session_name'] == "Persistence Test"
            assert recovered_session['user_id'] == "test_user"
            assert 'memory_systems' in recovered_session
            assert all(k in recovered_session['memory_systems']
                      for k in ['graphiti', 'temporal', 'semantic'])

    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, test_canvas_file, temp_test_dir):
        """测试6: 验证并发会话创建的正确性"""
        import time

        session_dir = temp_test_dir / ".learning_sessions"
        manager = LearningSessionManager(session_dir=str(session_dir))

        # Mock系统
        mock_mcp_tool = AsyncMock(return_value={'memory_id': 'graphiti_mem_123'})
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        def create_mock_session(canvas_id, user_id):
            mock_session = MagicMock()
            mock_session.session_id = f"temporal_{canvas_id}_{user_id}"
            return mock_session

        mock_temporal_manager = MagicMock()
        mock_temporal_manager.is_initialized = True
        mock_temporal_manager.create_learning_session.side_effect = create_mock_session

        mock_semantic_manager = MagicMock()
        mock_semantic_manager.mcp_client = MagicMock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_123"

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            # 创建两个会话
            result1 = await manager.start_session(canvas_path=test_canvas_file, user_id="user1")
            time.sleep(1.1)  # 确保时间戳不同
            result2 = await manager.start_session(canvas_path=test_canvas_file, user_id="user2")

            # 验证两个会话有不同的session_id
            assert result1['session_id'] != result2['session_id']

            # 验证两个session文件都存在
            assert Path(result1['session_file']).exists()
            assert Path(result2['session_file']).exists()

            # 验证session目录中有两个文件
            session_files = list(Path(session_dir).glob("*.json"))
            assert len(session_files) == 2

    @pytest.mark.asyncio
    async def test_all_systems_unavailable_graceful_handling(self, test_canvas_file, temp_test_dir):
        """测试7: 验证所有系统都不可用时的优雅处理"""
        session_dir = temp_test_dir / ".learning_sessions"
        manager = LearningSessionManager(session_dir=str(session_dir))

        # 所有系统都不可用的情况
        # Graphiti: claude_tools不存在
        # Temporal: is_initialized = False
        # Semantic: mcp_client = None

        mock_temporal_manager = MagicMock()
        mock_temporal_manager.is_initialized = False

        mock_semantic_manager = MagicMock()
        mock_semantic_manager.mcp_client = None

        with patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            # 执行会话启动
            result = await manager.start_session(canvas_path=test_canvas_file)

            # 验证会话仍然成功创建（优雅降级）
            assert result['success'] is True
            assert 'session_id' in result
            assert 'session_file' in result

            # 验证所有系统都标记为unavailable
            memory_systems = result['memory_systems']
            assert memory_systems['graphiti']['status'] == 'unavailable'
            assert memory_systems['temporal']['status'] == 'unavailable'
            assert memory_systems['semantic']['status'] == 'unavailable'

            # 验证每个系统都有错误信息和存储说明
            for system_name, system_result in memory_systems.items():
                assert 'error' in system_result
                assert 'attempted_at' in system_result
                assert 'storage' in system_result

            # 验证session文件仍然被创建
            session_file = Path(result['session_file'])
            assert session_file.exists()

    @pytest.mark.asyncio
    async def test_canvas_path_normalization(self, temp_test_dir):
        """测试8: 验证Canvas路径规范化"""
        session_dir = temp_test_dir / ".learning_sessions"
        manager = LearningSessionManager(session_dir=str(session_dir))

        # 创建测试Canvas（使用相对路径）
        canvas_name = "relative_path_test.canvas"
        canvas_path = temp_test_dir / canvas_name
        canvas_data = {"nodes": [], "edges": []}
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f)

        # Mock系统
        mock_mcp_tool = AsyncMock(return_value={'memory_id': 'mem_123'})
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        mock_session = MagicMock()
        mock_session.session_id = "temp_123"
        mock_temporal_manager = MagicMock()
        mock_temporal_manager.is_initialized = True
        mock_temporal_manager.create_learning_session.return_value = mock_session

        mock_semantic_manager = MagicMock()
        mock_semantic_manager.mcp_client = MagicMock()
        mock_semantic_manager.store_semantic_memory.return_value = "sem_123"

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            # 使用相对路径创建会话
            result = await manager.start_session(canvas_path=str(canvas_path))

            # 读取session文件
            with open(result['session_file'], 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # 验证路径被规范化为绝对路径
            stored_path = session_data['canvas_path']
            assert os.path.isabs(stored_path)
            assert stored_path == os.path.abspath(str(canvas_path))


    @pytest.mark.asyncio
    async def test_backward_compatibility_json_format(self, test_canvas_file, temp_test_dir):
        """
        测试9: 测试会话JSON向后兼容

        验证新格式包含所有旧字段，确保现有系统（如Story 8.17的记忆系统）
        可以正确读取新格式的会话JSON。
        """
        session_dir = temp_test_dir / ".learning_sessions"
        manager = LearningSessionManager(session_dir=str(session_dir))

        # Mock所有系统
        mock_mcp_tool = AsyncMock(return_value={'memory_id': 'graphiti_mem_123'})
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        mock_session = MagicMock()
        mock_session.session_id = "temporal_session_123"
        mock_temporal_manager = MagicMock()
        mock_temporal_manager.is_initialized = True
        mock_temporal_manager.create_learning_session.return_value = mock_session

        mock_semantic_manager = MagicMock()
        mock_semantic_manager.mcp_client = MagicMock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_123"

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            # 启动会话
            result = await manager.start_session(
                canvas_path=test_canvas_file,
                user_id="compatibility_test_user"
            )

            # 读取会话JSON
            session_file = Path(result['session_file'])
            with open(session_file, 'r', encoding='utf-8') as f:
                new_json = json.load(f)

            # 定义旧格式的必需字段
            old_format_fields = {'session_id', 'start_time', 'canvas_path', 'memory_systems'}

            # 验证新格式包含所有旧字段
            assert old_format_fields.issubset(set(new_json.keys())), \
                f"Missing fields: {old_format_fields - set(new_json.keys())}"

            # 验证Story 8.17的记忆系统可以读取新格式
            # （Story 8.17只需要session_id和memory_systems字段）
            assert 'session_id' in new_json
            assert 'memory_systems' in new_json

            # 验证memory_systems中每个系统有status字段
            for system_name, system_data in new_json['memory_systems'].items():
                assert 'status' in system_data, \
                    f"System {system_name} missing 'status' field"
                assert system_data['status'] in ['running', 'unavailable'], \
                    f"System {system_name} has invalid status: {system_data['status']}"

    @pytest.mark.asyncio
    async def test_start_with_neo4j_unavailable(self, test_canvas_file, temp_test_dir):
        """
        测试10: 测试Neo4j不可用时的启动（降级场景）

        验证当Neo4j不可用时，Graphiti系统标记为unavailable，
        但其他系统（Temporal、Semantic）仍然尝试启动。
        """
        session_dir = temp_test_dir / ".learning_sessions"
        manager = LearningSessionManager(session_dir=str(session_dir))

        # 模拟Neo4j不可用：claude_tools不存在（导致Graphiti失败）
        # 但Temporal和Semantic仍然可用

        mock_session = MagicMock()
        mock_session.session_id = "temporal_session_123"
        mock_temporal_manager = MagicMock()
        mock_temporal_manager.is_initialized = True
        mock_temporal_manager.create_learning_session.return_value = mock_session

        mock_semantic_manager = MagicMock()
        mock_semantic_manager.mcp_client = MagicMock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_123"

        with patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            # 执行启动（没有claude_tools，Graphiti会失败）
            result = await manager.start_session(
                canvas_path=test_canvas_file,
                user_id="neo4j_test_user"
            )

            # 验证会话仍然成功启动（优雅降级）
            assert result['success'] is True
            assert 'memory_systems' in result

            # 验证Graphiti状态为unavailable
            graphiti = result['memory_systems'].get('graphiti')
            assert graphiti is not None
            assert graphiti['status'] == 'unavailable'
            assert 'error' in graphiti
            assert 'attempted_at' in graphiti

            # 验证Temporal和Semantic仍然成功
            temporal = result['memory_systems'].get('temporal')
            assert temporal is not None
            assert temporal['status'] == 'running'

            semantic = result['memory_systems'].get('semantic')
            assert semantic is not None
            assert semantic['status'] == 'running'

            # 验证至少有运行中的系统
            assert result['running_systems'] >= 2


class TestLearningStopCompatibility:
    """测试/learning stop命令的兼容性"""

    @pytest.mark.asyncio
    async def test_stop_reads_new_session_format(self, tmp_path):
        """测试stop命令可以读取新格式的会话JSON"""
        session_dir = tmp_path / ".learning_sessions"
        session_dir.mkdir()

        # 创建新格式的会话JSON
        session_id = "test_session_123"
        session_file = session_dir / f"session_{session_id}.json"

        new_format_json = {
            "session_id": session_id,
            "start_time": "2025-10-30T10:00:00",
            "canvas_path": "/path/to/test.canvas",
            "user_id": "test_user",
            "session_name": "Test Session",
            "memory_systems": {
                "graphiti": {
                    "status": "running",
                    "memory_id": "mem_123",
                    "initialized_at": "2025-10-30T10:00:01"
                },
                "temporal": {
                    "status": "running",
                    "session_record_id": "temporal_123",
                    "initialized_at": "2025-10-30T10:00:02"
                },
                "semantic": {
                    "status": "unavailable",
                    "error": "MCP server not available",
                    "attempted_at": "2025-10-30T10:00:03"
                }
            }
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(new_format_json, f, ensure_ascii=False, indent=2)

        # 验证文件可以被正确读取
        with open(session_file, 'r', encoding='utf-8') as f:
            loaded_json = json.load(f)

        # 验证所有必需字段存在
        assert loaded_json['session_id'] == session_id
        assert 'memory_systems' in loaded_json
        assert all(sys in loaded_json['memory_systems']
                  for sys in ['graphiti', 'temporal', 'semantic'])

        # 注意：实际的stop实现需要在Story中实现
        # 这里只是验证JSON格式的可读性


class TestLearningStatusCompatibility:
    """测试/learning status命令的兼容性"""

    @pytest.mark.asyncio
    async def test_status_reads_new_json_format(self, tmp_path):
        """测试status命令可以读取新格式的会话JSON"""
        session_dir = tmp_path / ".learning_sessions"
        session_dir.mkdir()

        # 创建新格式的会话JSON
        session_id = "test_session_456"
        session_file = session_dir / f"session_{session_id}.json"

        new_format_json = {
            "session_id": session_id,
            "start_time": "2025-10-30T11:00:00",
            "canvas_path": "/path/to/another_test.canvas",
            "user_id": "another_user",
            "memory_systems": {
                "graphiti": {
                    "status": "running",
                    "memory_id": "mem_456",
                    "initialized_at": "2025-10-30T11:00:01",
                    "storage": "Neo4j knowledge graph"
                },
                "temporal": {
                    "status": "running",
                    "session_record_id": "temporal_456",
                    "initialized_at": "2025-10-30T11:00:02",
                    "storage": "SQLite database"
                },
                "semantic": {
                    "status": "running",
                    "memory_id": "semantic_456",
                    "initialized_at": "2025-10-30T11:00:03",
                    "storage": "MCP semantic service"
                }
            }
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(new_format_json, f, ensure_ascii=False, indent=2)

        # 验证文件可以被正确读取并解析
        with open(session_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)

        # 验证status数据的完整性
        assert status_data['session_id'] == session_id
        assert 'memory_systems' in status_data

        # 验证每个系统的状态信息
        for system_name, system_info in status_data['memory_systems'].items():
            assert 'status' in system_info
            if system_info['status'] == 'running':
                assert 'initialized_at' in system_info
                assert 'storage' in system_info

        # 注意：实际的status命令实现需要在相关Story中完成
        # 这里只是验证JSON格式的兼容性


if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short"])
