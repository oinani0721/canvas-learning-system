"""
Unit tests for error_formatters (Story 10.11.4)

Tests the startup report generation and fix suggestion functions.
"""


import pytest
from memory_system.error_formatters import (
    format_startup_report,
    generate_fix_suggestions,
    require_graphiti,
    require_semantic_advanced,
    require_temporal,
)


class TestFormatStartupReport:
    """Test format_startup_report() function"""

    def test_full_mode_report(self):
        """Full mode: all systems available"""
        mode_info = {
            'mode': 'full',
            'available_systems': [
                '时序记忆管理器 [Neo4j模式]',
                'Graphiti知识图谱 [MCP服务器连接]',
                '语义记忆管理器 [MCP完整模式]'
            ],
            'unavailable_systems': [],
            'functionality_impact': '所有功能正常运行'
        }

        report = format_startup_report(mode_info)

        # Verify report structure
        assert '==========' in report  # Banner
        assert 'Canvas Learning System 启动成功' in report
        assert '完整模式' in report
        assert '(3/3系统可用)' in report
        assert '✅ 时序记忆管理器 [Neo4j模式]' in report
        assert '✅ Graphiti知识图谱 [MCP服务器连接]' in report
        assert '✅ 语义记忆管理器 [MCP完整模式]' in report
        assert '影响: 所有功能正常运行' in report
        # No fix suggestions for full mode
        assert '提示:' not in report or report.count('提示:') == 0

    def test_partial_mode_report(self):
        """Partial mode: Graphiti unavailable"""
        mode_info = {
            'mode': 'partial',
            'available_systems': [
                '时序记忆管理器 [Neo4j模式]',
                '语义记忆管理器 [降级模式 - 本地缓存]'
            ],
            'unavailable_systems': [
                'Graphiti知识图谱 [MCP服务器未连接]'
            ],
            'functionality_impact': '知识图谱功能不可用，学习会话记录功能正常'
        }

        report = format_startup_report(mode_info)

        assert '部分模式' in report
        assert '(2/3系统可用)' in report
        assert '✅ 时序记忆管理器 [Neo4j模式]' in report
        assert '❌ Graphiti知识图谱 [MCP服务器未连接]' in report
        assert '影响: 知识图谱功能不可用' in report
        assert '提示:' in report  # Should have fix suggestion
        assert 'start_all_mcp_servers.bat' in report

    def test_basic_mode_report(self):
        """Basic mode: minimal functionality"""
        mode_info = {
            'mode': 'basic',
            'available_systems': [
                '语义记忆管理器 [降级模式 - 本地缓存]'
            ],
            'unavailable_systems': [
                '时序记忆管理器 [Neo4j不可用]',
                'Graphiti知识图谱 [MCP服务器未连接]'
            ],
            'functionality_impact': '仅基础功能可用，时序记忆功能受限'
        }

        report = format_startup_report(mode_info)

        assert '基础模式' in report
        assert '(1/3系统可用)' in report
        assert '❌ 时序记忆管理器 [Neo4j不可用]' in report
        assert '❌ Graphiti知识图谱 [MCP服务器未连接]' in report
        assert '提示:' in report

    def test_report_with_all_unavailable(self):
        """Edge case: All systems unavailable"""
        mode_info = {
            'mode': 'basic',
            'available_systems': [],
            'unavailable_systems': [
                '时序记忆管理器 [Neo4j不可用]',
                'Graphiti知识图谱 [MCP服务器未连接]',
                '语义记忆管理器 [完全不可用]'
            ],
            'functionality_impact': '仅基础功能可用'
        }

        report = format_startup_report(mode_info)

        assert '(0/3系统可用)' in report
        assert report.count('❌') == 3


class TestGenerateFixSuggestions:
    """Test generate_fix_suggestions() function"""

    def test_graphiti_unavailable_suggestion(self):
        """Graphiti unavailable → MCP server startup suggestion"""
        unavailable = ['Graphiti知识图谱 [MCP服务器未连接]']

        suggestion = generate_fix_suggestions(unavailable)

        assert 'start_all_mcp_servers.bat' in suggestion

    def test_neo4j_unavailable_suggestion(self):
        """Neo4j unavailable → Neo4j startup suggestion"""
        unavailable = ['时序记忆管理器 [Neo4j不可用]']

        suggestion = generate_fix_suggestions(unavailable)

        assert 'neo4j.bat console' in suggestion

    def test_semantic_unavailable_suggestion(self):
        """Semantic completely unavailable → MCP client fix suggestion"""
        unavailable = ['语义记忆管理器 [完全不可用]']

        suggestion = generate_fix_suggestions(unavailable)

        assert 'diagnose_mcp_client.py' in suggestion

    def test_multiple_unavailable_suggestions(self):
        """Multiple systems unavailable → combined suggestions"""
        unavailable = [
            'Graphiti知识图谱 [MCP服务器未连接]',
            '时序记忆管理器 [Neo4j不可用]'
        ]

        suggestion = generate_fix_suggestions(unavailable)

        # Should contain both suggestions
        assert 'start_all_mcp_servers.bat' in suggestion or 'neo4j.bat' in suggestion
        assert ' 或 ' in suggestion  # Multiple suggestions combined

    def test_no_unavailable_no_suggestion(self):
        """No unavailable systems → empty suggestion"""
        unavailable = []

        suggestion = generate_fix_suggestions(unavailable)

        assert suggestion == ''

    def test_unknown_system_no_suggestion(self):
        """Unknown system → no suggestion"""
        unavailable = ['Unknown System [Unknown Error]']

        suggestion = generate_fix_suggestions(unavailable)

        # Should return empty string for unknown systems
        assert suggestion == ''


class TestRequireGraphiti:
    """Test require_graphiti() function"""

    def test_graphiti_available(self):
        """Graphiti available → return True"""
        mode_info = {
            'mode': 'full',
            'unavailable_systems': []
        }

        result = require_graphiti(mode_info)

        assert result is True

    def test_graphiti_unavailable(self, capsys):
        """Graphiti unavailable → return False and print message"""
        mode_info = {
            'mode': 'partial',
            'unavailable_systems': ['Graphiti知识图谱 [MCP服务器未连接]']
        }

        result = require_graphiti(mode_info)

        assert result is False

        # Capture printed message
        captured = capsys.readouterr()
        assert '❌ 此功能需要Graphiti知识图谱' in captured.out
        assert 'start_all_mcp_servers.bat' in captured.out


class TestRequireTemporal:
    """Test require_temporal() function"""

    def test_temporal_available(self):
        """Temporal available → return True"""
        mode_info = {
            'mode': 'full',
            'unavailable_systems': []
        }

        result = require_temporal(mode_info)

        assert result is True

    def test_temporal_unavailable(self, capsys):
        """Temporal unavailable → return False and print message"""
        mode_info = {
            'mode': 'partial',
            'unavailable_systems': ['时序记忆管理器 [Neo4j不可用]']
        }

        result = require_temporal(mode_info)

        assert result is False

        # Capture printed message
        captured = capsys.readouterr()
        assert '❌ 此功能需要时序记忆管理器' in captured.out
        assert 'neo4j.bat console' in captured.out


class TestRequireSemanticAdvanced:
    """Test require_semantic_advanced() function"""

    def test_semantic_mcp_mode_available(self):
        """Semantic in MCP mode → return True"""
        mode_info = {
            'mode': 'full',
            'available_systems': [
                '语义记忆管理器 [MCP完整模式]'
            ]
        }

        result = require_semantic_advanced(mode_info)

        assert result is True

    def test_semantic_fallback_mode_unavailable(self, capsys):
        """Semantic in fallback mode → return False and print message"""
        mode_info = {
            'mode': 'partial',
            'available_systems': [
                '语义记忆管理器 [降级模式 - 本地缓存]'
            ]
        }

        result = require_semantic_advanced(mode_info)

        assert result is False

        # Capture printed message
        captured = capsys.readouterr()
        assert '⚠️ 高级语义搜索不可用' in captured.out
        assert '向量相似度搜索不可用' in captured.out

    def test_semantic_completely_unavailable(self, capsys):
        """Semantic completely unavailable → return False"""
        mode_info = {
            'mode': 'basic',
            'available_systems': []
        }

        result = require_semantic_advanced(mode_info)

        assert result is False


class TestReportFormatting:
    """Test report formatting details"""

    def test_report_has_banner_separators(self):
        """Report has proper banner separators"""
        mode_info = {
            'mode': 'full',
            'available_systems': ['System 1'],
            'unavailable_systems': [],
            'functionality_impact': 'All good'
        }

        report = format_startup_report(mode_info)

        # Should start and end with banner separator
        assert report.startswith('====')
        assert report.endswith('====')

    def test_system_count_accuracy(self):
        """System count is accurate"""
        mode_info = {
            'mode': 'partial',
            'available_systems': ['System 1', 'System 2'],
            'unavailable_systems': ['System 3'],
            'functionality_impact': 'Limited'
        }

        report = format_startup_report(mode_info)

        assert '(2/3系统可用)' in report

    def test_empty_mode_info_handles_gracefully(self):
        """Empty mode_info handles gracefully"""
        mode_info = {}

        # Should not crash
        report = format_startup_report(mode_info)

        assert isinstance(report, str)
        assert len(report) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
