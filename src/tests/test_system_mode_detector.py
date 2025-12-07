"""
Unit tests for SystemModeDetector (Story 10.11.4)

Tests the system mode detection logic and helper functions.
"""

import pytest
from memory_system.system_mode_detector import (
    MODE_BASIC,
    MODE_FULL,
    MODE_NAMES,
    MODE_PARTIAL,
    SystemModeDetector,
    _build_available_list,
    _build_unavailable_list,
    _describe_impact,
)


# Mock manager classes for testing
class MockTemporalManager:
    """Mock Temporal Memory Manager for testing"""
    def __init__(self, is_initialized=True, mode='neo4j'):
        self.is_initialized = is_initialized
        self.mode = mode


class MockSemanticManager:
    """Mock Semantic Memory Manager for testing"""
    def __init__(self, is_initialized=True, mode='mcp'):
        self.is_initialized = is_initialized
        self.mode = mode


class TestSystemModeDetector:
    """Test SystemModeDetector.detect_mode() with all scenarios"""

    def test_full_mode_all_systems_available(self):
        """Scenario 1: All systems available + semantic=mcp → mode='full'"""
        temporal = MockTemporalManager(is_initialized=True, mode='neo4j')
        graphiti = True
        semantic = MockSemanticManager(is_initialized=True, mode='mcp')

        result = SystemModeDetector.detect_mode(temporal, graphiti, semantic)

        assert result['mode'] == MODE_FULL
        assert len(result['available_systems']) == 3
        assert len(result['unavailable_systems']) == 0
        assert '所有功能正常运行' in result['functionality_impact']

    def test_partial_mode_graphiti_unavailable(self):
        """Scenario 2: temporal+semantic available, graphiti unavailable → mode='partial'"""
        temporal = MockTemporalManager(is_initialized=True, mode='neo4j')
        graphiti = False
        semantic = MockSemanticManager(is_initialized=True, mode='mcp')

        result = SystemModeDetector.detect_mode(temporal, graphiti, semantic)

        assert result['mode'] == MODE_PARTIAL
        assert len(result['available_systems']) == 2
        assert len(result['unavailable_systems']) == 1
        assert any('Graphiti' in s for s in result['unavailable_systems'])
        assert '知识图谱功能不可用' in result['functionality_impact']

    def test_partial_mode_semantic_fallback(self):
        """Scenario 4: temporal available, semantic fallback → mode='partial'"""
        temporal = MockTemporalManager(is_initialized=True, mode='neo4j')
        graphiti = True
        semantic = MockSemanticManager(is_initialized=True, mode='fallback')

        result = SystemModeDetector.detect_mode(temporal, graphiti, semantic)

        assert result['mode'] == MODE_PARTIAL
        assert len(result['available_systems']) == 3
        # Semantic is available but in fallback mode
        assert any('降级模式' in s for s in result['available_systems'])

    def test_basic_mode_only_semantic_available(self):
        """Scenario 3: Only semantic available → mode='basic'"""
        temporal = MockTemporalManager(is_initialized=False, mode='unavailable')
        graphiti = False
        semantic = MockSemanticManager(is_initialized=True, mode='fallback')

        result = SystemModeDetector.detect_mode(temporal, graphiti, semantic)

        assert result['mode'] == MODE_BASIC
        assert len(result['available_systems']) == 1
        assert len(result['unavailable_systems']) == 2
        assert '仅基础功能可用' in result['functionality_impact']

    def test_basic_mode_all_unavailable(self):
        """Edge case: All systems unavailable"""
        temporal = MockTemporalManager(is_initialized=False, mode='unavailable')
        graphiti = False
        semantic = MockSemanticManager(is_initialized=False, mode='unavailable')

        result = SystemModeDetector.detect_mode(temporal, graphiti, semantic)

        assert result['mode'] == MODE_BASIC
        assert len(result['available_systems']) == 0
        assert len(result['unavailable_systems']) == 3

    def test_partial_mode_temporal_unavailable(self):
        """Scenario: graphiti + semantic(mcp) available, temporal unavailable"""
        temporal = MockTemporalManager(is_initialized=False, mode='unavailable')
        graphiti = True
        semantic = MockSemanticManager(is_initialized=True, mode='mcp')

        result = SystemModeDetector.detect_mode(temporal, graphiti, semantic)

        assert result['mode'] == MODE_PARTIAL
        assert len(result['available_systems']) == 2
        assert any('时序记忆' in s for s in result['unavailable_systems'])

    def test_partial_mode_semantic_unavailable(self):
        """Scenario: temporal + graphiti available, semantic unavailable"""
        temporal = MockTemporalManager(is_initialized=True, mode='neo4j')
        graphiti = True
        semantic = MockSemanticManager(is_initialized=False, mode='unavailable')

        result = SystemModeDetector.detect_mode(temporal, graphiti, semantic)

        assert result['mode'] == MODE_PARTIAL
        assert len(result['available_systems']) == 2
        assert any('语义记忆' in s for s in result['unavailable_systems'])

    def test_basic_mode_only_temporal_available(self):
        """Edge case: Only temporal available"""
        temporal = MockTemporalManager(is_initialized=True, mode='neo4j')
        graphiti = False
        semantic = MockSemanticManager(is_initialized=False, mode='unavailable')

        result = SystemModeDetector.detect_mode(temporal, graphiti, semantic)

        assert result['mode'] == MODE_BASIC
        assert len(result['available_systems']) == 1


class TestBuildAvailableList:
    """Test _build_available_list helper function"""

    def test_all_available_neo4j_mcp(self):
        """All systems available in optimal mode"""
        result = _build_available_list(
            temporal_ok=True,
            graphiti_ok=True,
            semantic_ok=True,
            semantic_mode='mcp'
        )

        assert len(result) == 3
        assert any('Neo4j模式' in s for s in result)
        assert any('MCP服务器连接' in s for s in result)
        assert any('MCP完整模式' in s for s in result)

    def test_semantic_fallback_mode(self):
        """Semantic in fallback mode"""
        result = _build_available_list(
            temporal_ok=True,
            graphiti_ok=True,
            semantic_ok=True,
            semantic_mode='fallback'
        )

        assert len(result) == 3
        assert any('降级模式' in s for s in result)

    def test_only_temporal_available(self):
        """Only temporal available"""
        result = _build_available_list(
            temporal_ok=True,
            graphiti_ok=False,
            semantic_ok=False,
            semantic_mode='unavailable'
        )

        assert len(result) == 1
        assert any('时序记忆管理器' in s for s in result)

    def test_none_available(self):
        """No systems available"""
        result = _build_available_list(
            temporal_ok=False,
            graphiti_ok=False,
            semantic_ok=False,
            semantic_mode='unavailable'
        )

        assert len(result) == 0


class TestBuildUnavailableList:
    """Test _build_unavailable_list helper function"""

    def test_all_available(self):
        """All systems available → empty unavailable list"""
        result = _build_unavailable_list(
            temporal_ok=True,
            graphiti_ok=True,
            semantic_ok=True,
            semantic_mode='mcp'
        )

        assert len(result) == 0

    def test_graphiti_unavailable(self):
        """Graphiti unavailable"""
        result = _build_unavailable_list(
            temporal_ok=True,
            graphiti_ok=False,
            semantic_ok=True,
            semantic_mode='mcp'
        )

        assert len(result) == 1
        assert any('Graphiti' in s and 'MCP服务器未连接' in s for s in result)

    def test_temporal_unavailable(self):
        """Temporal unavailable"""
        result = _build_unavailable_list(
            temporal_ok=False,
            graphiti_ok=True,
            semantic_ok=True,
            semantic_mode='mcp'
        )

        assert len(result) == 1
        assert any('时序记忆管理器' in s and 'Neo4j不可用' in s for s in result)

    def test_semantic_completely_unavailable(self):
        """Semantic completely unavailable"""
        result = _build_unavailable_list(
            temporal_ok=True,
            graphiti_ok=True,
            semantic_ok=False,
            semantic_mode='unavailable'
        )

        assert len(result) == 1
        assert any('语义记忆管理器' in s and '完全不可用' in s for s in result)

    def test_all_unavailable(self):
        """All systems unavailable"""
        result = _build_unavailable_list(
            temporal_ok=False,
            graphiti_ok=False,
            semantic_ok=False,
            semantic_mode='unavailable'
        )

        assert len(result) == 3


class TestDescribeImpact:
    """Test _describe_impact helper function"""

    def test_full_mode_impact(self):
        """Full mode: all functions normal"""
        result = _describe_impact(
            mode=MODE_FULL,
            temporal_ok=True,
            graphiti_ok=True,
            semantic_ok=True,
            semantic_mode='mcp'
        )

        assert '所有功能正常运行' in result

    def test_partial_mode_no_graphiti(self):
        """Partial mode: Graphiti unavailable"""
        result = _describe_impact(
            mode=MODE_PARTIAL,
            temporal_ok=True,
            graphiti_ok=False,
            semantic_ok=True,
            semantic_mode='mcp'
        )

        assert '知识图谱功能不可用' in result
        assert '学习会话记录功能正常' in result or '时序记忆功能正常' in result

    def test_partial_mode_semantic_fallback(self):
        """Partial mode: Semantic in fallback mode"""
        result = _describe_impact(
            mode=MODE_PARTIAL,
            temporal_ok=True,
            graphiti_ok=True,
            semantic_ok=True,
            semantic_mode='fallback'
        )

        assert '高级语义搜索不可用' in result
        assert '关键词搜索' in result

    def test_basic_mode_impact(self):
        """Basic mode: minimal functionality"""
        result = _describe_impact(
            mode=MODE_BASIC,
            temporal_ok=False,
            graphiti_ok=False,
            semantic_ok=True,
            semantic_mode='fallback'
        )

        assert '仅基础功能可用' in result


class TestModeNames:
    """Test mode name constants"""

    def test_mode_names_complete(self):
        """All modes have Chinese names"""
        assert MODE_FULL in MODE_NAMES
        assert MODE_PARTIAL in MODE_NAMES
        assert MODE_BASIC in MODE_NAMES

        assert MODE_NAMES[MODE_FULL] == '完整模式'
        assert MODE_NAMES[MODE_PARTIAL] == '部分模式'
        assert MODE_NAMES[MODE_BASIC] == '基础模式'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
