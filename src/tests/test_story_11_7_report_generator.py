#!/usr/bin/env python3
"""
Unit Tests for Story 11.7: Learning Report Generator

Tests the LearningReportGenerator class and all report types:
- Daily reports (6 sections, < 2s)
- Weekly reports (trends + heatmap, < 5s)
- Canvas analysis reports (timeline + efficiency)

Author: Dev Agent (James)
Date: 2025-01-15
"""

import pytest
import json
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from canvas_progress_tracker.report_generator import (
    LearningReportGenerator,
    ASCIIChartGenerator,
    get_report_generator,
    COLOR_CODE_TO_NAME,
    COLOR_NAME_TO_EMOJI,
    EBBINGHAUS_REVIEW_DAYS
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for reports"""
    output_dir = tmp_path / "test_reports"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_hot_store():
    """Mock HotDataStore"""
    store = Mock()
    store.get_today_stats.return_value = {
        "session_id": "session_2025-01-15",
        "total_events": 42,
        "canvases_modified": ["math.canvas", "physics.canvas"],
        "color_transitions": {
            "red->purple": 5,
            "purple->green": 3
        },
        "start_time": "2025-01-15T09:00:00",
        "last_update": "2025-01-15T18:00:00"
    }
    return store


@pytest.fixture
def mock_cold_store():
    """Mock ColdDataStore"""
    store = Mock()

    # Mock daily_stats
    store.query_daily_stats.return_value = [{
        "stat_date": "2025-01-15",
        "total_events": 50,
        "total_learning_minutes": 180,
        "nodes_modified": 20,
        "nodes_red": 10,
        "nodes_purple": 15,
        "nodes_green": 25,
        "understanding_rate": 75.0
    }]

    # Mock canvas_changes
    store.query_canvas_changes.return_value = [
        {
            "change_id": "c1",
            "canvas_id": "math.canvas",
            "change_type": "node_modified",
            "node_id": "n1",
            "timestamp": "2025-01-15T10:00:00"
        },
        {
            "change_id": "c2",
            "canvas_id": "math.canvas",
            "change_type": "node_added",
            "node_id": "n2",
            "timestamp": "2025-01-15T11:00:00"
        }
    ]

    # Mock learning_events
    store.query_learning_events.return_value = [
        {
            "event_id": "e1",
            "canvas_id": "math.canvas",
            "event_type": "understanding_breakthrough",
            "timestamp": "2025-01-15T10:30:00",
            "description": "理解了特征向量"
        }
    ]

    # Mock color_transitions
    store.query_color_transitions.return_value = [
        {
            "transition_id": "t1",
            "canvas_id": "math.canvas",
            "node_id": "n1",
            "from_color": "1",  # red
            "to_color": "3",    # purple
            "timestamp": "2025-01-15T10:15:00"
        },
        {
            "transition_id": "t2",
            "canvas_id": "math.canvas",
            "node_id": "n2",
            "from_color": "3",  # purple
            "to_color": "2",    # green
            "timestamp": "2025-01-15T11:30:00"
        }
    ]

    # Mock get_stats_summary
    store.get_stats_summary.return_value = {
        "total_changes": 100,
        "total_learning_events": 20,
        "color_distribution": {"red": 10, "purple": 15, "green": 25},
        "understanding_rate_avg": 75.0
    }

    return store


@pytest.fixture
def report_generator(mock_hot_store, mock_cold_store, temp_output_dir):
    """LearningReportGenerator instance with mocked stores"""
    return LearningReportGenerator(
        hot_store=mock_hot_store,
        cold_store=mock_cold_store,
        output_dir=temp_output_dir
    )


# ============================================================================
# Test ASCII Chart Generator
# ============================================================================

class TestASCIIChartGenerator:
    """Test ASCII art chart generation"""

    def test_generate_bar_chart(self):
        """AC1: ASCII bar chart generation"""
        chart_gen = ASCIIChartGenerator()
        data = {"周一": 120, "周二": 100, "周三": 140}

        result = chart_gen.generate_bar_chart(data, max_width=50)

        assert "周一" in result
        assert "120" in result
        assert "█" in result
        assert "周三" in result
        assert "140" in result

    def test_generate_bar_chart_empty_data(self):
        """AC1: Handle empty data"""
        chart_gen = ASCIIChartGenerator()
        result = chart_gen.generate_bar_chart({})
        assert "无数据" in result

    def test_generate_trend_line(self):
        """AC2: ASCII trend line generation"""
        chart_gen = ASCIIChartGenerator()
        values = [10, 20, 15, 30, 25, 35, 40]

        result = chart_gen.generate_trend_line(values, width=60, height=10)

        assert "●" in result  # Data points
        assert "最大值" in result
        assert "最小值" in result
        assert "40" in result  # Max value

    def test_generate_trend_line_insufficient_data(self):
        """AC2: Handle insufficient data"""
        chart_gen = ASCIIChartGenerator()
        result = chart_gen.generate_trend_line([10], width=60, height=10)
        assert "数据不足" in result

    def test_generate_heatmap(self):
        """AC3: ASCII heatmap generation"""
        chart_gen = ASCIIChartGenerator()
        data = [
            [10, 20, 30],
            [15, 25, 35],
            [5, 15, 25]
        ]
        labels_x = ["A", "B", "C"]
        labels_y = ["X", "Y", "Z"]

        result = chart_gen.generate_heatmap(data, labels_x, labels_y)

        assert "A" in result
        assert "X" in result
        assert "░" in result or "▒" in result or "▓" in result or "█" in result


# ============================================================================
# Test Learning Report Generator Initialization
# ============================================================================

class TestLearningReportGeneratorInit:
    """Test LearningReportGenerator initialization"""

    def test_init_with_defaults(self):
        """AC1: Initialize with default parameters"""
        with patch('canvas_progress_tracker.report_generator.get_hot_data_store'), \
             patch('canvas_progress_tracker.report_generator.get_cold_data_store'):
            generator = LearningReportGenerator()

            assert generator.hot_store is not None
            assert generator.cold_store is not None
            assert generator.output_dir == Path(".learning_reports")
            assert isinstance(generator.chart_gen, ASCIIChartGenerator)

    def test_init_with_custom_params(self, mock_hot_store, mock_cold_store, temp_output_dir):
        """AC1: Initialize with custom parameters"""
        generator = LearningReportGenerator(
            hot_store=mock_hot_store,
            cold_store=mock_cold_store,
            output_dir=temp_output_dir
        )

        assert generator.hot_store == mock_hot_store
        assert generator.cold_store == mock_cold_store
        assert generator.output_dir == temp_output_dir

    def test_output_dir_created(self, temp_output_dir):
        """AC1: Output directory is created"""
        output_dir = temp_output_dir / "new_reports"
        with patch('canvas_progress_tracker.report_generator.get_hot_data_store'), \
             patch('canvas_progress_tracker.report_generator.get_cold_data_store'):
            LearningReportGenerator(output_dir=output_dir)

            assert output_dir.exists()


# ============================================================================
# Test Daily Report Generation
# ============================================================================

class TestDailyReportGeneration:
    """Test daily report generation (AC: 6 sections, < 2s)"""

    def test_generate_daily_report_success(self, report_generator):
        """AC1: Generate daily report successfully"""
        target_date = date(2025, 1, 15)

        file_path = report_generator.generate_daily_report(target_date)

        assert file_path is not None
        assert Path(file_path).exists()
        assert "daily_report_2025-01-15.md" in file_path

    def test_daily_report_performance(self, report_generator):
        """AC4: Daily report generation < 2 seconds"""
        start_time = time.time()

        report_generator.generate_daily_report()

        elapsed = time.time() - start_time
        assert elapsed < 2.0, f"Daily report took {elapsed:.2f}s, expected < 2s"

    def test_daily_report_contains_6_sections(self, report_generator):
        """AC1: Daily report contains 6 sections"""
        target_date = date(2025, 1, 15)
        file_path = report_generator.generate_daily_report(target_date)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for 6 sections
        assert "## 1. 📊 学习时长统计" in content
        assert "## 2. 📚 Canvas活动记录" in content
        assert "## 3. 🎨 节点颜色变化" in content
        assert "## 4. 📈 学习指标" in content
        assert "## 5. 🔄 艾宾浩斯复习提醒" in content
        assert "## 6. ✨ 今日亮点" in content

    def test_daily_report_markdown_format(self, report_generator):
        """AC5: Report saved in Markdown format"""
        file_path = report_generator.generate_daily_report()

        assert file_path.endswith(".md")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert content.startswith("# ")  # Markdown header
        assert "**" in content  # Bold text
        assert "##" in content  # Subheadings

    def test_daily_report_data_accuracy(self, report_generator):
        """AC1: Report data is accurate"""
        target_date = date.today()  # Use today to trigger HotDataStore
        file_path = report_generator.generate_daily_report(target_date)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check that data from mocks appears in report
        assert "math.canvas" in content or "Canvas" in content
        # Check color transitions appear
        assert "🔴" in content or "🟢" in content or "🟣" in content


# ============================================================================
# Test Weekly Report Generation
# ============================================================================

class TestWeeklyReportGeneration:
    """Test weekly report generation (AC: trends + heatmap, < 5s)"""

    def test_generate_weekly_report_success(self, report_generator):
        """AC2: Generate weekly report successfully"""
        start_date = date(2025, 1, 9)
        end_date = date(2025, 1, 15)

        file_path = report_generator.generate_weekly_report(start_date, end_date)

        assert file_path is not None
        assert Path(file_path).exists()
        assert "weekly_report" in file_path

    def test_weekly_report_performance(self, report_generator):
        """AC4: Weekly report generation < 5 seconds"""
        start_time = time.time()

        report_generator.generate_weekly_report()

        elapsed = time.time() - start_time
        assert elapsed < 5.0, f"Weekly report took {elapsed:.2f}s, expected < 5s"

    def test_weekly_report_contains_trend_chart(self, report_generator):
        """AC2: Weekly report contains trend chart"""
        file_path = report_generator.generate_weekly_report()

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 1. 📈 学习时长趋势" in content
        assert "```" in content  # Code block for chart
        assert "█" in content or "●" in content  # Chart characters

    def test_weekly_report_contains_heatmap(self, report_generator):
        """AC2: Weekly report contains heatmap"""
        file_path = report_generator.generate_weekly_report()

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 2. 🔥 Canvas活动热力图" in content

    def test_weekly_report_contains_flow_analysis(self, report_generator):
        """AC2: Weekly report contains node flow analysis"""
        file_path = report_generator.generate_weekly_report()

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 3. 🎨 节点流转分析" in content
        assert "红→紫" in content or "紫→绿" in content

    def test_weekly_report_contains_efficiency(self, report_generator):
        """AC2: Weekly report contains efficiency assessment"""
        file_path = report_generator.generate_weekly_report()

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 4. ⚡ 效率评估" in content
        assert "学习效率指数" in content

    def test_weekly_report_contains_recommendations(self, report_generator):
        """AC2: Weekly report contains next week suggestions"""
        file_path = report_generator.generate_weekly_report()

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 5. 💡 下周学习建议" in content


# ============================================================================
# Test Canvas Analysis Report
# ============================================================================

class TestCanvasAnalysisReport:
    """Test Canvas analysis report generation"""

    def test_generate_canvas_report_success(self, report_generator):
        """AC3: Generate Canvas analysis report successfully"""
        canvas_id = "math.canvas"
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 15)

        file_path = report_generator.generate_canvas_report(
            canvas_id, start_date, end_date
        )

        assert file_path is not None
        assert Path(file_path).exists()
        assert "canvas_report_math" in file_path

    def test_canvas_report_contains_timeline(self, report_generator):
        """AC3: Canvas report contains timeline"""
        file_path = report_generator.generate_canvas_report("math.canvas")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 1. 📅 学习时间线" in content

    def test_canvas_report_contains_flow_stats(self, report_generator):
        """AC3: Canvas report contains node flow statistics"""
        file_path = report_generator.generate_canvas_report("math.canvas")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 2. 🎨 节点流转统计" in content
        assert "红色节点" in content
        assert "掌握率" in content

    def test_canvas_report_contains_progress_curve(self, report_generator):
        """AC3: Canvas report contains progress curve"""
        file_path = report_generator.generate_canvas_report("math.canvas")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 3. 📈 理解进步曲线" in content

    def test_canvas_report_contains_efficiency_analysis(self, report_generator):
        """AC3: Canvas report contains efficiency analysis"""
        file_path = report_generator.generate_canvas_report("math.canvas")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 4. ⚡ 效率分析" in content
        assert "学习效率" in content

    def test_canvas_report_contains_blind_spots(self, report_generator):
        """AC3: Canvas report contains blind spot identification"""
        file_path = report_generator.generate_canvas_report("math.canvas")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## 5. 🎯 知识盲区识别" in content


# ============================================================================
# Test Data Collection Methods
# ============================================================================

class TestDataCollection:
    """Test internal data collection methods"""

    def test_collect_daily_data_today(self, report_generator):
        """Test collecting data for today (uses HotDataStore)"""
        target_date = date.today()

        data = report_generator._collect_daily_data(target_date)

        assert 'today_stats' in data
        assert data['today_stats'] is not None
        assert data['today_stats']['total_events'] == 42

    def test_collect_daily_data_historical(self, report_generator):
        """Test collecting historical data (uses ColdDataStore)"""
        target_date = date(2025, 1, 10)

        data = report_generator._collect_daily_data(target_date)

        assert 'daily_stats' in data
        assert 'changes' in data
        assert 'events' in data

    def test_collect_weekly_data(self, report_generator):
        """Test collecting weekly data"""
        start_date = date(2025, 1, 9)
        end_date = date(2025, 1, 15)

        data = report_generator._collect_weekly_data(start_date, end_date)

        assert 'daily_stats' in data
        assert 'summary' in data
        assert 'color_transitions' in data
        assert 'events' in data

    def test_collect_canvas_data(self, report_generator):
        """Test collecting Canvas-specific data"""
        canvas_id = "math.canvas"
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 15)

        data = report_generator._collect_canvas_data(canvas_id, start_date, end_date)

        assert 'changes' in data
        assert 'events' in data
        assert 'color_transitions' in data


# ============================================================================
# Test Analysis Methods
# ============================================================================

class TestAnalysisMethods:
    """Test internal analysis helper methods"""

    def test_calculate_daily_learning_time(self, report_generator):
        """Test learning time calculation"""
        data = {
            'daily_stats': {
                'total_learning_minutes': 120
            }
        }

        minutes = report_generator._calculate_daily_learning_time(data)

        assert minutes == 120

    def test_analyze_canvas_activity(self, report_generator):
        """Test Canvas activity analysis"""
        data = {
            'changes': [
                {'canvas_id': 'math.canvas', 'change_type': 'node_added'},
                {'canvas_id': 'math.canvas', 'change_type': 'node_modified'},
                {'canvas_id': 'physics.canvas', 'change_type': 'node_added'}
            ]
        }

        activity = report_generator._analyze_canvas_activity(data)

        assert 'math.canvas' in activity
        assert activity['math.canvas']['change_count'] == 2
        assert activity['math.canvas']['nodes_added'] == 1

    def test_analyze_color_changes(self, report_generator):
        """Test color change analysis"""
        data = {
            'color_transitions': [
                {'from_color': '1', 'to_color': '3'},  # red -> purple
                {'from_color': '3', 'to_color': '2'},  # purple -> green
                {'from_color': '1', 'to_color': '3'}   # red -> purple
            ]
        }

        changes = report_generator._analyze_color_changes(data)

        assert 'red->purple' in changes
        assert changes['red->purple'] == 2
        assert changes['purple->green'] == 1

    def test_count_progress_transitions(self, report_generator):
        """Test progress transition counting"""
        color_changes = {
            'red->purple': 3,
            'purple->green': 2,
            'red->green': 1,
            'green->red': 1  # This is not progress
        }

        count = report_generator._count_progress_transitions(color_changes)

        assert count == 6  # 3 + 2 + 1


# ============================================================================
# Test Singleton Access
# ============================================================================

class TestSingletonAccess:
    """Test global singleton access function"""

    def test_get_report_generator(self):
        """AC1: Get global singleton instance"""
        with patch('canvas_progress_tracker.report_generator.get_hot_data_store'), \
             patch('canvas_progress_tracker.report_generator.get_cold_data_store'):

            generator1 = get_report_generator()
            generator2 = get_report_generator()

            assert generator1 is generator2  # Same instance


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_data_handling(self, report_generator):
        """Test handling of empty data"""
        # Set mocks to return empty data
        report_generator.cold_store.query_daily_stats.return_value = []
        report_generator.cold_store.query_canvas_changes.return_value = []
        report_generator.cold_store.query_learning_events.return_value = []
        report_generator.cold_store.query_color_transitions.return_value = []

        # Should not crash
        file_path = report_generator.generate_daily_report()
        assert Path(file_path).exists()

    def test_special_characters_in_canvas_id(self, report_generator):
        """Test handling of special characters in canvas_id"""
        canvas_id = "数学/线性代数.canvas"

        file_path = report_generator.generate_canvas_report(canvas_id)

        assert Path(file_path).exists()
        # Special characters should be sanitized
        assert "/" not in Path(file_path).name

    def test_future_date_handling(self, report_generator):
        """Test handling of future dates"""
        future_date = date.today() + timedelta(days=10)

        # Should not crash
        file_path = report_generator.generate_daily_report(future_date)
        assert Path(file_path).exists()


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests with real data stores (IV1, IV2, IV3)"""

    @pytest.mark.integration
    def test_real_data_stores_integration(self, temp_output_dir):
        """IV1: Integration with real HotDataStore and ColdDataStore"""
        from canvas_progress_tracker.data_stores import HotDataStore, ColdDataStore

        hot_store = HotDataStore()
        cold_store = ColdDataStore()
        generator = LearningReportGenerator(
            hot_store=hot_store,
            cold_store=cold_store,
            output_dir=temp_output_dir
        )

        # Should not crash even with empty stores
        file_path = generator.generate_daily_report()
        assert Path(file_path).exists()

    @pytest.mark.integration
    def test_slash_command_compatibility(self, report_generator):
        """IV1: Compatible with /learning-report slash command"""
        # Simulate slash command calling report generator
        file_path = report_generator.generate_weekly_report()

        assert Path(file_path).exists()
        assert file_path.endswith(".md")

    @pytest.mark.integration
    def test_large_dataset_performance(self, report_generator):
        """IV3: Performance with large datasets (30 days)"""
        # Mock large dataset
        large_stats = []
        for i in range(30):
            day = date(2025, 1, 1) + timedelta(days=i)
            large_stats.append({
                "stat_date": day.strftime("%Y-%m-%d"),
                "total_events": 50,
                "total_learning_minutes": 120,
                "nodes_red": 10,
                "nodes_purple": 15,
                "nodes_green": 25
            })

        report_generator.cold_store.query_daily_stats.return_value = large_stats

        start_time = time.time()
        file_path = report_generator.generate_weekly_report(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 30)
        )
        elapsed = time.time() - start_time

        assert elapsed < 5.0
        assert Path(file_path).exists()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
