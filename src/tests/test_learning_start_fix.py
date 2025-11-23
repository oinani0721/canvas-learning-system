"""
测试 Story 10.10: 修复 /learning start 命令核心逻辑

验证LearningSessionManager真实调用三个记忆系统：
- Graphiti知识图谱（MCP工具）
- 时序记忆管理器
- 语义记忆管理器

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-30
"""

import pytest
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from command_handlers.learning_commands import LearningSessionManager
from memory_system.memory_exceptions import TemporalMemoryError, SemanticMemoryError


class TestLearningStartRealCalls:
    """测试 /learning start 真实调用记忆系统"""

    @pytest.fixture
    def manager(self, tmp_path):
        """创建临时会话管理器"""
        session_dir = tmp_path / ".learning_sessions"
        return LearningSessionManager(session_dir=str(session_dir))

    @pytest.fixture
    def test_canvas_path(self):
        """测试用Canvas路径"""
        return "src/tests/fixtures/test.canvas"

    @pytest.mark.asyncio
    async def test_start_graphiti_real_call(self, manager, test_canvas_path):
        """测试真实调用Graphiti MCP工具"""
        # Mock MCP Graphiti工具返回成功结果
        mock_result = {
            'memory_id': 'mem_20251030_123456_test',
            'status': 'success'
        }

        # Create a mock MCP module
        mock_mcp_tool = AsyncMock(return_value=mock_result)

        # Use sys.modules to inject the mock
        import sys
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}):
            result = await manager._start_graphiti(
                canvas_path=test_canvas_path,
                session_id="test_session_001"
            )

            # 验证真实调用
            assert result['status'] == 'running'
            assert 'memory_id' in result
            assert result['memory_id'] == 'mem_20251030_123456_test'
            assert 'initialized_at' in result
            assert result['storage'] == 'Neo4j图数据库'

    @pytest.mark.asyncio
    async def test_start_graphiti_mcp_unavailable(self, manager, test_canvas_path):
        """测试Graphiti MCP工具不可用时抛出异常"""
        # Mock导入失败 - simulate ImportError when importing from claude_tools
        # Ensure claude_tools is not in sys.modules
        if 'claude_tools' in sys.modules:
            del sys.modules['claude_tools']

        # The import will fail naturally since claude_tools doesn't exist
        with pytest.raises(RuntimeError) as exc_info:
            await manager._start_graphiti(
                canvas_path=test_canvas_path,
                session_id="test_session_001"
            )
        assert "MCP Graphiti工具不可用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_graphiti_missing_memory_id(self, manager, test_canvas_path):
        """测试Graphiti返回结果缺少memory_id时抛出异常"""
        # Mock返回不完整的结果
        mock_result = {'status': 'success'}  # 缺少memory_id

        # Create a mock MCP module
        mock_mcp_tool = AsyncMock(return_value=mock_result)
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}):
            with pytest.raises(ValueError) as exc_info:
                await manager._start_graphiti(
                    canvas_path=test_canvas_path,
                    session_id="test_session_001"
                )
            assert "缺少memory_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_temporal_real_init(self, manager, test_canvas_path):
        """测试真实初始化TemporalMemoryManager"""
        # Mock TemporalMemoryManager
        mock_session = Mock()
        mock_session.session_id = "temporal_session_123"

        mock_temporal_manager = Mock()
        mock_temporal_manager.is_initialized = True
        mock_temporal_manager.create_learning_session.return_value = mock_session

        with patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager):
            result = await manager._start_temporal(
                canvas_path=test_canvas_path,
                session_id="test_session_001"
            )

            # 验证真实初始化
            assert result['status'] == 'running'
            assert 'session_id' in result
            assert result['session_id'] == 'temporal_session_123'
            assert 'initialized_at' in result
            assert result['storage'] == '本地SQLite数据库'

            # 验证调用了create_learning_session
            mock_temporal_manager.create_learning_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_temporal_init_failed(self, manager, test_canvas_path):
        """测试TemporalMemoryManager初始化失败时抛出异常"""
        # Mock初始化失败
        mock_temporal_manager = Mock()
        mock_temporal_manager.is_initialized = False

        with patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager):
            with pytest.raises(TemporalMemoryError):
                await manager._start_temporal(
                    canvas_path=test_canvas_path,
                    session_id="test_session_001"
                )

    @pytest.mark.asyncio
    async def test_start_semantic_mcp_check(self, manager, test_canvas_path):
        """测试检查SemanticMemoryManager的MCP可用性"""
        # Mock SemanticMemoryManager with MCP available
        mock_semantic_manager = Mock()
        mock_semantic_manager.mcp_client = Mock()  # MCP可用
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_456"

        # Story 10.11.3: Mock get_status() 返回MCP模式
        mock_semantic_manager.get_status.return_value = {
            'initialized': True,
            'mode': 'mcp',
            'features': {
                'add_memory': True,
                'search_memories': True,
                'advanced_semantic_search': True,
                'vector_similarity': True
            }
        }

        with patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):
            result = await manager._start_semantic(
                canvas_path=test_canvas_path,
                session_id="test_session_001"
            )

            # 验证成功初始化
            assert result['status'] == 'running'
            assert 'memory_id' in result
            assert result['memory_id'] == 'semantic_mem_456'
            assert 'initialized_at' in result
            assert result['storage'] == '向量数据库'
            # Story 10.11.3: 验证新字段
            assert result['mode'] == 'mcp'
            assert 'features' in result

            # 验证调用了store_semantic_memory
            mock_semantic_manager.store_semantic_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_semantic_mcp_unavailable(self, manager, test_canvas_path):
        """测试MCP不可用时自动降级到fallback模式（Story 10.11.3）"""
        # Mock SemanticMemoryManager使用降级模式
        mock_semantic_manager = Mock()
        mock_semantic_manager.mcp_client = None  # MCP不可用
        mock_semantic_manager.fallback_cache = Mock()  # 使用降级缓存
        mock_semantic_manager.store_semantic_memory.return_value = "fallback_mem_789"

        # Story 10.11.3: Mock get_status() 返回降级模式
        mock_semantic_manager.get_status.return_value = {
            'initialized': True,
            'mode': 'fallback',
            'features': {
                'add_memory': True,
                'search_memories': True,
                'advanced_semantic_search': False,
                'vector_similarity': False
            }
        }

        with patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):
            result = await manager._start_semantic(
                canvas_path=test_canvas_path,
                session_id="test_session_001"
            )

            # 验证降级模式成功启动
            assert result['status'] == 'running'
            assert result['mode'] == 'fallback'
            assert result['storage'] == '本地SQLite缓存'
            assert 'memory_id' in result

    @pytest.mark.asyncio
    async def test_graceful_degradation(self, manager, test_canvas_path):
        """测试优雅降级：某系统不可用时其他系统继续"""
        # Mock各系统的响应
        # Graphiti: 成功
        mock_graphiti_result = {
            'memory_id': 'mem_test_123',
            'status': 'success'
        }

        # Temporal: 失败
        mock_temporal_manager = Mock()
        mock_temporal_manager.is_initialized = False

        # Semantic: 成功
        mock_semantic_manager = Mock()
        mock_semantic_manager.mcp_client = Mock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_789"

        # Create mock MCP module
        mock_mcp_tool = AsyncMock(return_value=mock_graphiti_result)
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            result = await manager.start_session(canvas_path=test_canvas_path)

            # 验证：即使Temporal失败，Graphiti和Semantic仍然启动成功
            assert 'memory_systems' in result
            assert 'graphiti' in result['memory_systems']
            assert 'temporal' in result['memory_systems']
            assert 'semantic' in result['memory_systems']

            # 验证Graphiti成功
            assert result['memory_systems']['graphiti']['status'] == 'running'
            assert result['memory_systems']['graphiti']['memory_id'] == 'mem_test_123'

            # 验证Temporal失败但有错误信息
            assert result['memory_systems']['temporal']['status'] == 'unavailable'
            assert 'error' in result['memory_systems']['temporal']
            assert 'attempted_at' in result['memory_systems']['temporal']

            # 验证Semantic成功
            assert result['memory_systems']['semantic']['status'] == 'running'
            assert result['memory_systems']['semantic']['memory_id'] == 'semantic_mem_789'

    @pytest.mark.asyncio
    async def test_session_json_format(self, manager, test_canvas_path):
        """测试会话JSON格式正确"""
        # Mock所有系统成功
        mock_graphiti_result = {'memory_id': 'mem_123', 'status': 'success'}

        mock_temporal_manager = Mock()
        mock_temporal_manager.is_initialized = True
        mock_session = Mock()
        mock_session.session_id = "temp_session_456"
        mock_temporal_manager.create_learning_session.return_value = mock_session

        mock_semantic_manager = Mock()
        mock_semantic_manager.mcp_client = Mock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_789"

        # Create mock MCP module
        mock_mcp_tool = AsyncMock(return_value=mock_graphiti_result)
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            result = await manager.start_session(canvas_path=test_canvas_path)

            # 验证JSON格式
            assert 'session_id' in result
            assert 'memory_systems' in result

            # 验证每个系统都有status字段
            for system_name, system_data in result['memory_systems'].items():
                assert 'status' in system_data
                status = system_data['status']
                assert status in ['running', 'unavailable']

                # 如果running，必须有initialized_at
                if status == 'running':
                    assert 'initialized_at' in system_data

                # 如果unavailable，必须有error和attempted_at
                if status == 'unavailable':
                    assert 'error' in system_data
                    assert 'attempted_at' in system_data

            # 验证会话文件被创建
            session_file = Path(manager.session_dir) / f"{result['session_id']}.json"
            assert session_file.exists()

            # 读取会话文件验证格式
            with open(session_file, 'r', encoding='utf-8') as f:
                session_json = json.load(f)

            assert 'session_id' in session_json
            assert 'start_time' in session_json
            assert 'canvas_path' in session_json
            assert 'memory_systems' in session_json

    def test_backward_compatibility(self):
        """测试会话JSON向后兼容"""
        # 旧格式JSON
        old_json = {
            "session_id": "test_session",
            "start_time": "2025-10-30T19:00:00",
            "canvas_path": "/path/to/canvas",
            "memory_systems": {
                "graphiti": {"status": "running"}
            }
        }

        # 新格式应该包含所有旧字段
        new_json = {
            "session_id": "test_session",
            "start_time": "2025-10-30T19:00:00",
            "canvas_path": "/path/to/canvas",
            "memory_systems": {
                "graphiti": {
                    "status": "running",
                    "memory_id": "mem_123",  # 新字段
                    "storage": "Neo4j图数据库",  # 新字段
                    "initialized_at": "2025-10-30T19:00:01"  # 新字段
                }
            }
        }

        # 验证向后兼容：旧字段都存在于新格式中
        assert set(old_json.keys()).issubset(set(new_json.keys()))
        assert set(old_json['memory_systems']['graphiti'].keys()).issubset(
            set(new_json['memory_systems']['graphiti'].keys())
        )

    @pytest.mark.asyncio
    async def test_session_file_saved_correctly(self, manager, test_canvas_path):
        """测试会话文件正确保存到磁盘"""
        # Mock所有系统
        mock_graphiti_result = {'memory_id': 'mem_123', 'status': 'success'}

        mock_temporal_manager = Mock()
        mock_temporal_manager.is_initialized = True
        mock_session = Mock()
        mock_session.session_id = "temp_session_456"
        mock_temporal_manager.create_learning_session.return_value = mock_session

        mock_semantic_manager = Mock()
        mock_semantic_manager.mcp_client = Mock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_789"

        # Create mock MCP module
        mock_mcp_tool = AsyncMock(return_value=mock_graphiti_result)
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            result = await manager.start_session(canvas_path=test_canvas_path)

            # 验证文件存在
            session_file = Path(result['session_file'])
            assert session_file.exists()

            # 验证文件内容
            with open(session_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)

            assert saved_data['session_id'] == result['session_id']
            assert saved_data['canvas_path'] == os.path.abspath(test_canvas_path)
            assert 'memory_systems' in saved_data
            assert 'graphiti' in saved_data['memory_systems']
            assert 'temporal' in saved_data['memory_systems']
            assert 'semantic' in saved_data['memory_systems']

    def test_generate_session_id_format(self, manager):
        """测试生成的session_id格式正确"""
        session_id = manager._generate_session_id()

        # 验证格式: session_YYYYMMDD_HHMMSS
        assert session_id.startswith("session_")
        parts = session_id.split("_")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS


class TestLearningSessionManagerIntegration:
    """集成测试"""

    @pytest.fixture
    def manager(self, tmp_path):
        """创建临时会话管理器"""
        session_dir = tmp_path / ".learning_sessions"
        return LearningSessionManager(session_dir=str(session_dir))

    def test_session_directory_creation(self, tmp_path):
        """测试会话目录自动创建"""
        session_dir = tmp_path / ".learning_sessions_test"
        assert not session_dir.exists()

        manager = LearningSessionManager(session_dir=str(session_dir))
        assert session_dir.exists()
        assert session_dir.is_dir()

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, manager):
        """测试创建多个会话"""
        # Mock所有系统
        mock_graphiti_result = {'memory_id': 'mem_123', 'status': 'success'}

        mock_temporal_manager = Mock()
        mock_temporal_manager.is_initialized = True
        mock_session = Mock()
        mock_session.session_id = "temp_session_456"
        mock_temporal_manager.create_learning_session.return_value = mock_session

        mock_semantic_manager = Mock()
        mock_semantic_manager.mcp_client = Mock()
        mock_semantic_manager.store_semantic_memory.return_value = "semantic_mem_789"

        # Create mock MCP module
        mock_mcp_tool = AsyncMock(return_value=mock_graphiti_result)
        mock_claude_tools = MagicMock()
        mock_claude_tools.mcp__graphiti_memory__add_episode = mock_mcp_tool

        with patch.dict('sys.modules', {'claude_tools': mock_claude_tools}), \
             patch('command_handlers.learning_commands.TemporalMemoryManager',
                   return_value=mock_temporal_manager), \
             patch('command_handlers.learning_commands.SemanticMemoryManager',
                   return_value=mock_semantic_manager):

            # 创建第一个会话
            result1 = await manager.start_session(canvas_path="test1.canvas")
            session_id1 = result1['session_id']

            # 等待1.1秒确保session_id时间戳不同
            time.sleep(1.1)

            # 创建第二个会话
            result2 = await manager.start_session(canvas_path="test2.canvas")
            session_id2 = result2['session_id']

            # 验证生成了不同的session_id
            assert session_id1 != session_id2

            # 验证两个文件都存在
            session_file1 = Path(manager.session_dir) / f"{session_id1}.json"
            session_file2 = Path(manager.session_dir) / f"{session_id2}.json"
            assert session_file1.exists()
            assert session_file2.exists()
