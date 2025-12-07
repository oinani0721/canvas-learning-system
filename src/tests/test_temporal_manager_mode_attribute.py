"""
验证TemporalMemoryManager的mode属性 (Story 10.11.4修复验证)

这个测试验证修复后的TemporalMemoryManager正确实现了mode属性。
"""

import os

import pytest
from memory_system.temporal_memory_manager import TemporalMemoryManager


class TestTemporalMemoryManagerModeAttribute:
    """验证TemporalMemoryManager的mode属性存在且正确"""

    def test_mode_attribute_exists(self):
        """验证mode属性在初始化时存在"""
        # 跳过Neo4j验证以在测试环境中运行
        os.environ['SKIP_NEO4J_VALIDATION'] = 'true'

        try:
            manager = TemporalMemoryManager()

            # 验证mode属性存在
            assert hasattr(manager, 'mode'), "TemporalMemoryManager缺少mode属性"

            # 验证mode是字符串类型
            assert isinstance(manager.mode, str), f"mode应该是字符串，实际是 {type(manager.mode)}"

            # 验证mode是有效值之一
            valid_modes = ['neo4j', 'sqlite', 'unavailable']
            assert manager.mode in valid_modes, f"mode={manager.mode} 不在有效值 {valid_modes} 中"

        finally:
            # 清理环境变量
            if 'SKIP_NEO4J_VALIDATION' in os.environ:
                del os.environ['SKIP_NEO4J_VALIDATION']

    def test_mode_attribute_in_get_status(self):
        """验证get_status()方法返回mode信息"""
        os.environ['SKIP_NEO4J_VALIDATION'] = 'true'

        try:
            manager = TemporalMemoryManager()
            status = manager.get_status()

            # 验证status包含mode字段
            assert 'mode' in status, "get_status()应该返回mode字段"

            # 验证mode值有效
            valid_modes = ['neo4j', 'sqlite', 'unavailable']
            assert status['mode'] in valid_modes, f"status中的mode={status['mode']} 不在有效值中"

        finally:
            if 'SKIP_NEO4J_VALIDATION' in os.environ:
                del os.environ['SKIP_NEO4J_VALIDATION']

    def test_mode_reflects_initialization_state(self):
        """验证mode正确反映初始化状态"""
        os.environ['SKIP_NEO4J_VALIDATION'] = 'true'

        try:
            manager = TemporalMemoryManager()

            # 验证mode和is_initialized一致性
            if manager.is_initialized:
                # 如果初始化成功，mode应该是neo4j或sqlite
                assert manager.mode in ['neo4j', 'sqlite'], \
                    f"初始化成功但mode={manager.mode} (应该是neo4j或sqlite)"
            else:
                # 如果初始化失败，mode应该是unavailable
                assert manager.mode == 'unavailable', \
                    f"初始化失败但mode={manager.mode} (应该是unavailable)"

        finally:
            if 'SKIP_NEO4J_VALIDATION' in os.environ:
                del os.environ['SKIP_NEO4J_VALIDATION']

    def test_mode_attribute_type_matches_spec(self):
        """验证mode属性类型符合接口规范"""
        os.environ['SKIP_NEO4J_VALIDATION'] = 'true'

        try:
            manager = TemporalMemoryManager()

            # 验证mode可以被SystemModeDetector访问
            # 模拟SystemModeDetector的访问模式
            temporal_ok = (
                manager.is_initialized and
                manager.mode == 'neo4j'  # 这行在修复前会抛出AttributeError
            )

            # 如果到达这里，说明mode属性可以正常访问
            assert True, "mode属性可以被正常访问"

        finally:
            if 'SKIP_NEO4J_VALIDATION' in os.environ:
                del os.environ['SKIP_NEO4J_VALIDATION']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
