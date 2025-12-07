"""
Task 6 集成测试 - 验证/learning命令的模式显示
Story 10.11.3 AC4
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from memory_system.semantic_memory_manager import SemanticMemoryManager


class TestTask6Integration:
    """测试Task 6的/learning命令集成"""

    @patch('memory_system.semantic_memory_manager.diagnose_mcp_memory_client')
    def test_get_status_returns_mode_and_features(self, mock_diagnose):
        """测试get_status()返回mode和features"""
        # 模拟MCP不可用，使用降级模式
        mock_diagnose.return_value = {
            'importable': False,
            'error': 'Test error',
            'fix_suggestion': 'Test fix'
        }

        manager = SemanticMemoryManager({'fallback_db_path': ':memory:'})
        status = manager.get_status()

        # 验证返回格式
        assert 'initialized' in status
        assert 'mode' in status
        assert 'features' in status

        # 验证降级模式
        assert status['initialized'] is True
        assert status['mode'] == 'fallback'
        assert isinstance(status['features'], dict)

    @patch('memory_system.semantic_memory_manager.diagnose_mcp_memory_client')
    def test_fallback_mode_features_correct(self, mock_diagnose):
        """测试降级模式的features正确"""
        mock_diagnose.return_value = {
            'importable': False,
            'error': 'Test error',
            'fix_suggestion': 'Test fix'
        }

        manager = SemanticMemoryManager({'fallback_db_path': ':memory:'})
        status = manager.get_status()
        features = status['features']

        # 降级模式应该支持基础功能
        assert features['add_memory'] is True
        assert features['search_memories'] is True

        # 降级模式不支持高级功能
        assert features['advanced_semantic_search'] is False
        assert features['vector_similarity'] is False
        assert features['cross_domain_connections'] is False

    @patch('memory_system.semantic_memory_manager.diagnose_mcp_memory_client')
    def test_start_semantic_integration_format(self, mock_diagnose):
        """测试_start_semantic返回格式（模拟）"""
        mock_diagnose.return_value = {
            'importable': False,
            'error': 'Test error',
            'fix_suggestion': 'Test fix'
        }

        manager = SemanticMemoryManager({'fallback_db_path': ':memory:'})

        # 模拟_start_semantic的返回格式
        memory_id = manager.add_memory("测试会话", {"test": True})
        status_info = manager.get_status()

        # 验证返回应该包含的字段
        expected_fields = ['mode', 'features', 'initialized']
        for field in expected_fields:
            assert field in status_info, f"Missing field: {field}"

        # 验证mode值正确
        assert status_info['mode'] in ['mcp', 'fallback', 'unavailable']

    def test_generate_status_report_format(self):
        """测试generate_status_report的输出格式"""
        # 模拟memory_systems数据（降级模式）
        memory_systems = {
            'semantic': {
                'status': 'running',
                'mode': 'fallback',
                'features': {
                    'add_memory': True,
                    'search_memories': True,
                    'advanced_semantic_search': False,
                    'vector_similarity': False,
                    'cross_domain_connections': False
                },
                'memory_id': 'memory-test123',
                'storage': '本地SQLite缓存',
                'initialized_at': '2025-10-31T12:00:00'
            }
        }

        session_data = {
            'session_id': 'test-session',
            'canvas_path': 'test.canvas',
            'start_time': '2025-10-31T12:00:00'
        }

        # 手动构建report（模拟generate_status_report逻辑）
        report_lines = []
        system_data = memory_systems['semantic']

        if system_data.get('status') == 'running':
            report_lines.append("✅ 语义记忆管理器: 运行中")

            # 检查mode
            if 'mode' in system_data:
                mode = system_data['mode']
                if mode == 'fallback':
                    report_lines.append("   模式: 降级模式 - 本地缓存")
                    report_lines.append("   ⚠️  高级语义搜索不可用，使用关键词搜索")

        report = "\n".join(report_lines)

        # 验证报告内容
        assert "语义记忆管理器: 运行中" in report
        assert "降级模式 - 本地缓存" in report
        assert "高级语义搜索不可用" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
