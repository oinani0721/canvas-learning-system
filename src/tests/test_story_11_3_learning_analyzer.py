"""
Story 11.3测试文件 - 学习分析回调系统测试

测试覆盖：
- AC 1: 正确识别4种颜色流转类型
- AC 2: 每种流转类型写入不同事件
- AC 3: 实时更新学习统计
- AC 4: 分析耗时 < 50ms
- AC 5: 支持批量分析
- AC 6: 边缘情况处理

测试包含：
- 单元测试（颜色流转检测、事件生成、统计计算）
- 性能测试（单次分析、批量分析）
- 边缘情况测试（删除节点、损坏数据、非法颜色）
- 集成测试（端到端、多Canvas并发）
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from canvas_progress_tracker.canvas_monitor_engine import CanvasChange, CanvasChangeType
from canvas_progress_tracker.learning_analyzer import (
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_PURPLE,
    COLOR_RED,
    COLOR_YELLOW,
    LearningAnalyzer,
    LearningEventType,
    get_learning_analyzer,
    learning_analysis_callback,
)

# ==================== Fixtures ====================


@pytest.fixture
def learning_analyzer():
    """LearningAnalyzer实例"""
    return LearningAnalyzer()


@pytest.fixture
def sample_red_to_purple_change():
    """红→紫颜色变化事件"""
    return CanvasChange(
        change_id="test_change_001",
        canvas_id="test.canvas",
        change_type=CanvasChangeType.UPDATE,
        node_id="node_abc123",
        node_type="text",
        old_content={
            "id": "node_abc123",
            "type": "text",
            "color": COLOR_RED,
            "text": "问题",
        },
        new_content={
            "id": "node_abc123",
            "type": "text",
            "color": COLOR_PURPLE,
            "text": "问题",
        },
        timestamp=datetime.now(),
        file_path="/path/to/test.canvas",
    )


@pytest.fixture
def sample_purple_to_green_change():
    """紫→绿颜色变化事件"""
    return CanvasChange(
        change_id="test_change_002",
        canvas_id="test.canvas",
        change_type=CanvasChangeType.UPDATE,
        node_id="node_def456",
        node_type="text",
        old_content={
            "id": "node_def456",
            "type": "text",
            "color": COLOR_PURPLE,
            "text": "问题",
        },
        new_content={
            "id": "node_def456",
            "type": "text",
            "color": COLOR_GREEN,
            "text": "问题",
        },
        timestamp=datetime.now(),
        file_path="/path/to/test.canvas",
    )


@pytest.fixture
def sample_red_to_green_change():
    """红→绿颜色变化事件（突破）"""
    return CanvasChange(
        change_id="test_change_003",
        canvas_id="test.canvas",
        change_type=CanvasChangeType.UPDATE,
        node_id="node_ghi789",
        node_type="text",
        old_content={
            "id": "node_ghi789",
            "type": "text",
            "color": COLOR_RED,
            "text": "问题",
        },
        new_content={
            "id": "node_ghi789",
            "type": "text",
            "color": COLOR_GREEN,
            "text": "问题",
        },
        timestamp=datetime.now(),
        file_path="/path/to/test.canvas",
    )


@pytest.fixture
def sample_green_to_purple_change():
    """绿→紫颜色变化事件（退步）"""
    return CanvasChange(
        change_id="test_change_004",
        canvas_id="test.canvas",
        change_type=CanvasChangeType.UPDATE,
        node_id="node_jkl012",
        node_type="text",
        old_content={
            "id": "node_jkl012",
            "type": "text",
            "color": COLOR_GREEN,
            "text": "问题",
        },
        new_content={
            "id": "node_jkl012",
            "type": "text",
            "color": COLOR_PURPLE,
            "text": "问题",
        },
        timestamp=datetime.now(),
        file_path="/path/to/test.canvas",
    )


@pytest.fixture
def sample_node_create_change():
    """新增红色节点事件"""
    return CanvasChange(
        change_id="test_change_005",
        canvas_id="test.canvas",
        change_type=CanvasChangeType.CREATE,
        node_id="node_new001",
        node_type="text",
        old_content=None,
        new_content={
            "id": "node_new001",
            "type": "text",
            "color": COLOR_RED,
            "text": "新问题",
        },
        timestamp=datetime.now(),
        file_path="/path/to/test.canvas",
    )


@pytest.fixture
def sample_yellow_text_update():
    """黄色节点文本更新事件"""
    return CanvasChange(
        change_id="test_change_006",
        canvas_id="test.canvas",
        change_type=CanvasChangeType.UPDATE,
        node_id="node_yellow001",
        node_type="text",
        old_content={
            "id": "node_yellow001",
            "type": "text",
            "color": COLOR_YELLOW,
            "text": "旧理解",
        },
        new_content={
            "id": "node_yellow001",
            "type": "text",
            "color": COLOR_YELLOW,
            "text": "新理解内容更详细",
        },
        timestamp=datetime.now(),
        file_path="/path/to/test.canvas",
    )


# ==================== AC 1测试: 正确识别4种颜色流转类型 ====================


class TestColorTransitionDetection:
    """测试颜色流转检测功能"""

    def test_detect_red_to_purple_understanding_improving(self, learning_analyzer):
        """测试红→紫 = understanding_improving"""
        event_type = learning_analyzer._detect_color_transition(COLOR_RED, COLOR_PURPLE)
        assert event_type == LearningEventType.UNDERSTANDING_IMPROVING

    def test_detect_purple_to_green_understanding_mastered(self, learning_analyzer):
        """测试紫→绿 = understanding_mastered"""
        event_type = learning_analyzer._detect_color_transition(
            COLOR_PURPLE, COLOR_GREEN
        )
        assert event_type == LearningEventType.UNDERSTANDING_MASTERED

    def test_detect_red_to_green_breakthrough(self, learning_analyzer):
        """测试红→绿 = breakthrough"""
        event_type = learning_analyzer._detect_color_transition(COLOR_RED, COLOR_GREEN)
        assert event_type == LearningEventType.BREAKTHROUGH

    def test_detect_green_to_purple_understanding_regressed(self, learning_analyzer):
        """测试绿→紫 = understanding_regressed"""
        event_type = learning_analyzer._detect_color_transition(
            COLOR_GREEN, COLOR_PURPLE
        )
        assert event_type == LearningEventType.UNDERSTANDING_REGRESSED

    def test_detect_purple_to_red_understanding_regressed(self, learning_analyzer):
        """测试紫→红 = understanding_regressed"""
        event_type = learning_analyzer._detect_color_transition(COLOR_PURPLE, COLOR_RED)
        assert event_type == LearningEventType.UNDERSTANDING_REGRESSED

    def test_detect_no_transition_for_blue_yellow(self, learning_analyzer):
        """测试蓝色和黄色不触发颜色流转"""
        assert learning_analyzer._detect_color_transition(COLOR_RED, COLOR_BLUE) is None
        assert (
            learning_analyzer._detect_color_transition(COLOR_RED, COLOR_YELLOW) is None
        )
        assert (
            learning_analyzer._detect_color_transition(COLOR_BLUE, COLOR_GREEN) is None
        )


# ==================== AC 2测试: 每种流转类型写入不同事件 ====================


class TestLearningEventGeneration:
    """测试学习事件生成功能"""

    def test_generate_understanding_improving_event(
        self, learning_analyzer, sample_red_to_purple_change
    ):
        """测试生成understanding_improving事件"""
        event = learning_analyzer.analyze_change(sample_red_to_purple_change)

        assert event is not None
        assert event.event_type == LearningEventType.UNDERSTANDING_IMPROVING
        assert event.canvas_id == "test.canvas"
        assert event.node_id == "node_abc123"
        assert event.details["old_color"] == COLOR_RED
        assert event.details["new_color"] == COLOR_PURPLE
        assert event.details["progress_type"] == "understanding_improving"

    def test_generate_understanding_mastered_event(
        self, learning_analyzer, sample_purple_to_green_change
    ):
        """测试生成understanding_mastered事件"""
        event = learning_analyzer.analyze_change(sample_purple_to_green_change)

        assert event is not None
        assert event.event_type == LearningEventType.UNDERSTANDING_MASTERED
        assert event.details["old_color"] == COLOR_PURPLE
        assert event.details["new_color"] == COLOR_GREEN

    def test_generate_breakthrough_event(
        self, learning_analyzer, sample_red_to_green_change
    ):
        """测试生成breakthrough事件"""
        event = learning_analyzer.analyze_change(sample_red_to_green_change)

        assert event is not None
        assert event.event_type == LearningEventType.BREAKTHROUGH
        assert event.details["old_color"] == COLOR_RED
        assert event.details["new_color"] == COLOR_GREEN

    def test_generate_understanding_regressed_event(
        self, learning_analyzer, sample_green_to_purple_change
    ):
        """测试生成understanding_regressed事件"""
        event = learning_analyzer.analyze_change(sample_green_to_purple_change)

        assert event is not None
        assert event.event_type == LearningEventType.UNDERSTANDING_REGRESSED
        assert event.details["old_color"] == COLOR_GREEN
        assert event.details["new_color"] == COLOR_PURPLE

    def test_generate_knowledge_node_added_event(
        self, learning_analyzer, sample_node_create_change
    ):
        """测试生成knowledge_node_added事件"""
        event = learning_analyzer.analyze_change(sample_node_create_change)

        assert event is not None
        assert event.event_type == LearningEventType.KNOWLEDGE_NODE_ADDED
        assert event.details["new_color"] == COLOR_RED
        assert "old_color" not in event.details

    def test_generate_personal_understanding_updated_event(
        self, learning_analyzer, sample_yellow_text_update
    ):
        """测试生成personal_understanding_updated事件"""
        event = learning_analyzer.analyze_change(sample_yellow_text_update)

        assert event is not None
        assert event.event_type == LearningEventType.PERSONAL_UNDERSTANDING_UPDATED
        assert event.details["old_text_length"] == 3  # "旧理解" (3 characters)
        assert (
            event.details["new_text_length"] == 8
        )  # "新理解内容更详细" (8 characters)
        assert event.details["text_delta"] == 5

    def test_event_id_format(self, learning_analyzer, sample_red_to_purple_change):
        """测试事件ID格式"""
        event = learning_analyzer.analyze_change(sample_red_to_purple_change)

        assert event is not None
        assert event.event_id.startswith("evt_")
        assert len(event.event_id.split("_")) == 3  # evt_{timestamp}_{uuid}


# ==================== AC 3测试: 实时更新学习统计 ====================


class TestLearningStatistics:
    """测试学习统计功能"""

    def test_update_stats_after_single_event(
        self, learning_analyzer, sample_red_to_purple_change
    ):
        """测试单个事件后统计更新"""
        learning_analyzer.analyze_change(sample_red_to_purple_change)

        stats = learning_analyzer.get_learning_stats("test.canvas")
        assert stats["total_events"] == 1
        assert "first_change_time" in stats
        assert "last_change_time" in stats

    def test_update_transition_counts(self, learning_analyzer):
        """测试流转计数正确更新"""
        # 创建3个正向流转和1个负向流转
        changes = [
            CanvasChange(
                change_id=f"change_{i}",
                canvas_id="test.canvas",
                change_type=CanvasChangeType.UPDATE,
                node_id=f"node_{i}",
                node_type="text",
                old_content={"id": f"node_{i}", "color": COLOR_RED, "text": "问题"},
                new_content={"id": f"node_{i}", "color": COLOR_PURPLE, "text": "问题"},
                timestamp=datetime.now(),
                file_path="/path/to/test.canvas",
            )
            for i in range(3)
        ]

        # 添加1个负向流转
        changes.append(
            CanvasChange(
                change_id="change_regress",
                canvas_id="test.canvas",
                change_type=CanvasChangeType.UPDATE,
                node_id="node_regress",
                node_type="text",
                old_content={
                    "id": "node_regress",
                    "color": COLOR_GREEN,
                    "text": "问题",
                },
                new_content={
                    "id": "node_regress",
                    "color": COLOR_PURPLE,
                    "text": "问题",
                },
                timestamp=datetime.now(),
                file_path="/path/to/test.canvas",
            )
        )

        for change in changes:
            learning_analyzer.analyze_change(change)

        stats = learning_analyzer.get_learning_stats("test.canvas")
        assert stats["positive_transitions"] == 3
        assert stats["negative_transitions"] == 1
        assert stats["understanding_rate"] == 0.75  # 3/4

    def test_learning_duration_calculation(self, learning_analyzer):
        """测试学习时长计算"""
        # 创建两个时间间隔的事件
        from datetime import timedelta

        time1 = datetime.now()
        time2 = time1 + timedelta(seconds=60)

        change1 = CanvasChange(
            change_id="change_1",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_1",
            node_type="text",
            old_content={"id": "node_1", "color": COLOR_RED, "text": "问题"},
            new_content={"id": "node_1", "color": COLOR_PURPLE, "text": "问题"},
            timestamp=time1,
            file_path="/path/to/test.canvas",
        )

        change2 = CanvasChange(
            change_id="change_2",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_2",
            node_type="text",
            old_content={"id": "node_2", "color": COLOR_PURPLE, "text": "问题"},
            new_content={"id": "node_2", "color": COLOR_GREEN, "text": "问题"},
            timestamp=time2,
            file_path="/path/to/test.canvas",
        )

        learning_analyzer.analyze_change(change1)
        learning_analyzer.analyze_change(change2)

        stats = learning_analyzer.get_learning_stats("test.canvas")
        assert stats["learning_duration_seconds"] == 60.0

    def test_stats_per_canvas_isolation(self, learning_analyzer):
        """测试不同Canvas的统计相互隔离"""
        change1 = CanvasChange(
            change_id="change_canvas1",
            canvas_id="canvas1.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_1",
            node_type="text",
            old_content={"id": "node_1", "color": COLOR_RED, "text": "问题"},
            new_content={"id": "node_1", "color": COLOR_PURPLE, "text": "问题"},
            timestamp=datetime.now(),
            file_path="/path/to/canvas1.canvas",
        )

        change2 = CanvasChange(
            change_id="change_canvas2",
            canvas_id="canvas2.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_2",
            node_type="text",
            old_content={"id": "node_2", "color": COLOR_RED, "text": "问题"},
            new_content={"id": "node_2", "color": COLOR_GREEN, "text": "问题"},
            timestamp=datetime.now(),
            file_path="/path/to/canvas2.canvas",
        )

        learning_analyzer.analyze_change(change1)
        learning_analyzer.analyze_change(change2)

        stats1 = learning_analyzer.get_learning_stats("canvas1.canvas")
        stats2 = learning_analyzer.get_learning_stats("canvas2.canvas")

        assert stats1["total_events"] == 1
        assert stats2["total_events"] == 1
        assert stats1["positive_transitions"] == 1
        assert stats2["positive_transitions"] == 1


# ==================== AC 4测试: 分析耗时 < 50ms ====================


class TestPerformance:
    """测试性能指标"""

    def test_single_analysis_performance(
        self, learning_analyzer, sample_red_to_purple_change
    ):
        """测试单次分析耗时 < 50ms"""
        times = []

        for _ in range(10):
            start_time = time.perf_counter()
            learning_analyzer.analyze_change(sample_red_to_purple_change)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 50, f"平均分析耗时 {avg_time:.2f}ms 超过50ms"
        assert max_time < 100, f"最大分析耗时 {max_time:.2f}ms 过长"

    def test_complex_event_performance(self, learning_analyzer):
        """测试复杂事件分析性能"""
        # 创建包含大量文本的黄色节点更新
        long_text = "测试内容" * 1000  # 8000字符

        change = CanvasChange(
            change_id="change_complex",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_complex",
            node_type="text",
            old_content={"id": "node_complex", "color": COLOR_YELLOW, "text": "旧内容"},
            new_content={
                "id": "node_complex",
                "color": COLOR_YELLOW,
                "text": long_text,
            },
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        start_time = time.perf_counter()
        learning_analyzer.analyze_change(change)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 50, f"复杂事件分析耗时 {elapsed_ms:.2f}ms 超过50ms"


# ==================== AC 5测试: 支持批量分析 ====================


class TestBatchAnalysis:
    """测试批量分析功能"""

    def test_batch_analysis_basic(self, learning_analyzer):
        """测试基本批量分析"""
        changes = [
            CanvasChange(
                change_id=f"change_{i}",
                canvas_id="test.canvas",
                change_type=CanvasChangeType.UPDATE,
                node_id=f"node_{i}",
                node_type="text",
                old_content={"id": f"node_{i}", "color": COLOR_RED, "text": "问题"},
                new_content={"id": f"node_{i}", "color": COLOR_PURPLE, "text": "问题"},
                timestamp=datetime.now(),
                file_path="/path/to/test.canvas",
            )
            for i in range(10)
        ]

        results = learning_analyzer.analyze_batch(changes)

        assert results["total_events"] == 10
        assert results["canvases_affected"] == 1
        assert results["learning_events_detected"] == 10
        assert "test.canvas" in results["canvases"]

    def test_batch_analysis_performance(self, learning_analyzer):
        """测试批量分析性能（100个变更 < 1秒）"""
        changes = [
            CanvasChange(
                change_id=f"change_{i}",
                canvas_id="test.canvas",
                change_type=CanvasChangeType.UPDATE,
                node_id=f"node_{i}",
                node_type="text",
                old_content={"id": f"node_{i}", "color": COLOR_RED, "text": "问题"},
                new_content={"id": f"node_{i}", "color": COLOR_PURPLE, "text": "问题"},
                timestamp=datetime.now(),
                file_path="/path/to/test.canvas",
            )
            for i in range(100)
        ]

        start_time = time.perf_counter()
        results = learning_analyzer.analyze_batch(changes)
        elapsed = time.perf_counter() - start_time

        assert elapsed < 1.0, f"批量分析耗时 {elapsed:.2f}秒 超过1秒"
        assert results["learning_events_detected"] == 100

    def test_batch_analysis_multiple_canvases(self, learning_analyzer):
        """测试多Canvas批量分析"""
        changes = []

        for canvas_num in range(3):
            for i in range(10):
                changes.append(
                    CanvasChange(
                        change_id=f"change_{canvas_num}_{i}",
                        canvas_id=f"canvas{canvas_num}.canvas",
                        change_type=CanvasChangeType.UPDATE,
                        node_id=f"node_{i}",
                        node_type="text",
                        old_content={
                            "id": f"node_{i}",
                            "color": COLOR_RED,
                            "text": "问题",
                        },
                        new_content={
                            "id": f"node_{i}",
                            "color": COLOR_PURPLE,
                            "text": "问题",
                        },
                        timestamp=datetime.now(),
                        file_path=f"/path/to/canvas{canvas_num}.canvas",
                    )
                )

        results = learning_analyzer.analyze_batch(changes)

        assert results["total_events"] == 30
        assert results["canvases_affected"] == 3
        assert "canvas0.canvas" in results["canvases"]
        assert "canvas1.canvas" in results["canvases"]
        assert "canvas2.canvas" in results["canvases"]


# ==================== AC 6测试: 边缘情况处理 ====================


class TestEdgeCases:
    """测试边缘情况处理"""

    def test_handle_node_deletion(self, learning_analyzer):
        """测试节点删除事件（不触发分析）"""
        delete_change = CanvasChange(
            change_id="change_delete",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.DELETE,
            node_id="node_deleted",
            node_type="text",
            old_content={"id": "node_deleted", "color": COLOR_RED, "text": "问题"},
            new_content=None,
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        event = learning_analyzer.analyze_change(delete_change)
        assert event is None

    def test_handle_position_change_no_color_change(self, learning_analyzer):
        """测试位置变化无颜色变化（跳过分析）"""
        position_change = CanvasChange(
            change_id="change_position",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_moved",
            node_type="text",
            old_content={
                "id": "node_moved",
                "color": COLOR_RED,
                "text": "问题",
                "x": 0,
                "y": 0,
            },
            new_content={
                "id": "node_moved",
                "color": COLOR_RED,
                "text": "问题",
                "x": 100,
                "y": 100,
            },
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        event = learning_analyzer.analyze_change(position_change)
        assert event is None

    def test_handle_missing_old_content(self, learning_analyzer):
        """测试缺失old_content（记录警告，跳过）"""
        invalid_change = CanvasChange(
            change_id="change_invalid",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_invalid",
            node_type="text",
            old_content=None,
            new_content={"id": "node_invalid", "color": COLOR_RED, "text": "问题"},
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        event = learning_analyzer.analyze_change(invalid_change)
        assert event is None

    def test_handle_missing_color_field(self, learning_analyzer):
        """测试缺失color字段（跳过分析）"""
        no_color_change = CanvasChange(
            change_id="change_no_color",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_no_color",
            node_type="text",
            old_content={"id": "node_no_color", "text": "问题"},  # 无color字段
            new_content={"id": "node_no_color", "text": "问题更新"},
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        event = learning_analyzer.analyze_change(no_color_change)
        assert event is None

    def test_handle_invalid_color_value(self, learning_analyzer):
        """测试非法颜色值（记录错误，跳过）"""
        invalid_color_change = CanvasChange(
            change_id="change_invalid_color",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_invalid_color",
            node_type="text",
            old_content={"id": "node_invalid_color", "color": "99", "text": "问题"},
            new_content={"id": "node_invalid_color", "color": "88", "text": "问题"},
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        event = learning_analyzer.analyze_change(invalid_color_change)
        assert event is None

    def test_handle_multiple_rapid_changes_same_node(self, learning_analyzer):
        """测试同一节点短时间内多次颜色变化（保留所有记录）"""
        color_transitions = [
            (COLOR_RED, COLOR_PURPLE),
            (COLOR_PURPLE, COLOR_GREEN),
            (COLOR_GREEN, COLOR_PURPLE),
        ]

        changes = [
            CanvasChange(
                change_id=f"change_{i}",
                canvas_id="test.canvas",
                change_type=CanvasChangeType.UPDATE,
                node_id="node_rapid",
                node_type="text",
                old_content={"id": "node_rapid", "color": colors[0], "text": "问题"},
                new_content={"id": "node_rapid", "color": colors[1], "text": "问题"},
                timestamp=datetime.now(),
                file_path="/path/to/test.canvas",
            )
            for i, colors in enumerate(color_transitions)
        ]

        events = [learning_analyzer.analyze_change(change) for change in changes]
        valid_events = [e for e in events if e is not None]

        assert len(valid_events) == 3
        assert valid_events[0].event_type == LearningEventType.UNDERSTANDING_IMPROVING
        assert valid_events[1].event_type == LearningEventType.UNDERSTANDING_MASTERED
        assert valid_events[2].event_type == LearningEventType.UNDERSTANDING_REGRESSED

    def test_handle_yellow_node_same_text_update(self, learning_analyzer):
        """测试黄色节点文本相同（不触发事件）"""
        same_text_change = CanvasChange(
            change_id="change_same_text",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_yellow_same",
            node_type="text",
            old_content={
                "id": "node_yellow_same",
                "color": COLOR_YELLOW,
                "text": "理解内容",
            },
            new_content={
                "id": "node_yellow_same",
                "color": COLOR_YELLOW,
                "text": "理解内容",
            },
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        event = learning_analyzer.analyze_change(same_text_change)
        assert event is None


# ==================== 集成测试 (IV1, IV2, IV3) ====================


class TestIntegration:
    """集成验证测试"""

    def test_callback_function_integration(self, sample_red_to_purple_change):
        """IV1: 端到端测试 - Canvas变更 → 监控检测 → 学习分析 → 事件写入"""
        with patch(
            "canvas_progress_tracker.data_stores.get_hot_data_store"
        ) as mock_store:
            mock_hot_store = MagicMock()
            mock_store.return_value = mock_hot_store

            # 调用回调函数
            learning_analysis_callback(sample_red_to_purple_change)

            # 验证hot_data_store.append_event被调用
            mock_hot_store.append_event.assert_called_once()

            # 验证事件格式
            call_args = mock_hot_store.append_event.call_args[0][0]
            assert "event_id" in call_args
            assert "timestamp" in call_args
            assert "canvas_id" in call_args
            assert call_args["event_type"] == "understanding_improving"
            assert call_args["details"]["old_color"] == COLOR_RED
            assert call_args["details"]["new_color"] == COLOR_PURPLE

    def test_color_system_compatibility(self, learning_analyzer):
        """IV2: 颜色系统兼容性测试 - 验证5种颜色代码正确识别"""
        colors = [COLOR_RED, COLOR_GREEN, COLOR_PURPLE, COLOR_BLUE, COLOR_YELLOW]

        for old_color in colors:
            for new_color in colors:
                if old_color == new_color:
                    continue

                change = CanvasChange(
                    change_id=f"change_{old_color}_{new_color}",
                    canvas_id="test.canvas",
                    change_type=CanvasChangeType.UPDATE,
                    node_id="node_test",
                    node_type="text",
                    old_content={"id": "node_test", "color": old_color, "text": "问题"},
                    new_content={"id": "node_test", "color": new_color, "text": "问题"},
                    timestamp=datetime.now(),
                    file_path="/path/to/test.canvas",
                )

                # 不应该抛出异常
                try:
                    event = learning_analyzer.analyze_change(change)
                    # 有些颜色组合不产生学习事件（例如红→蓝），这是正常的
                except Exception as e:
                    pytest.fail(f"颜色组合 {old_color}→{new_color} 导致异常: {e}")

    def test_agent_operations_no_interference(self, learning_analyzer):
        """IV3: Agent操作不干扰测试 - AI Agent添加蓝色节点时不影响学习分析"""
        # 模拟AI Agent添加蓝色节点
        blue_node_create = CanvasChange(
            change_id="change_ai_blue",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.CREATE,
            node_id="node_ai_blue",
            node_type="text",
            old_content=None,
            new_content={
                "id": "node_ai_blue",
                "color": COLOR_BLUE,
                "text": "🗣️ Oral Explanation: ...",
            },
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        # 不应该生成学习事件（蓝色节点是AI补充）
        event = learning_analyzer.analyze_change(blue_node_create)
        assert event is None

        # 但学生的理解节点应该正常分析
        student_change = CanvasChange(
            change_id="change_student",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_student",
            node_type="text",
            old_content={"id": "node_student", "color": COLOR_RED, "text": "问题"},
            new_content={"id": "node_student", "color": COLOR_PURPLE, "text": "问题"},
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        event = learning_analyzer.analyze_change(student_change)
        assert event is not None
        assert event.event_type == LearningEventType.UNDERSTANDING_IMPROVING

    def test_multiple_canvas_concurrent_analysis(self, learning_analyzer):
        """IV4: 多Canvas并发测试 - 同时修改3个Canvas，验证分析准确性"""
        changes = []

        # 创建3个Canvas的变更事件
        for canvas_num in range(3):
            for transition_type in [
                (COLOR_RED, COLOR_PURPLE, LearningEventType.UNDERSTANDING_IMPROVING),
                (COLOR_PURPLE, COLOR_GREEN, LearningEventType.UNDERSTANDING_MASTERED),
                (COLOR_RED, COLOR_GREEN, LearningEventType.BREAKTHROUGH),
            ]:
                old_color, new_color, expected_type = transition_type
                changes.append(
                    CanvasChange(
                        change_id=f"change_{canvas_num}_{old_color}_{new_color}",
                        canvas_id=f"canvas{canvas_num}.canvas",
                        change_type=CanvasChangeType.UPDATE,
                        node_id=f"node_{old_color}_{new_color}",
                        node_type="text",
                        old_content={
                            "id": f"node_{old_color}_{new_color}",
                            "color": old_color,
                            "text": "问题",
                        },
                        new_content={
                            "id": f"node_{old_color}_{new_color}",
                            "color": new_color,
                            "text": "问题",
                        },
                        timestamp=datetime.now(),
                        file_path=f"/path/to/canvas{canvas_num}.canvas",
                    )
                )

        # 批量分析
        results = learning_analyzer.analyze_batch(changes)

        # 验证准确性
        assert results["total_events"] == 9  # 3个Canvas × 3种流转
        assert results["canvases_affected"] == 3
        assert results["learning_events_detected"] == 9

        # 验证每个Canvas的统计独立
        for canvas_num in range(3):
            canvas_id = f"canvas{canvas_num}.canvas"
            stats = learning_analyzer.get_learning_stats(canvas_id)
            assert stats["total_events"] == 3
            assert stats["positive_transitions"] == 3
            assert stats["understanding_rate"] == 1.0


# ==================== 全局单例测试 ====================


class TestGlobalSingleton:
    """测试全局单例功能"""

    def test_get_learning_analyzer_singleton(self):
        """测试get_learning_analyzer返回同一实例"""
        analyzer1 = get_learning_analyzer()
        analyzer2 = get_learning_analyzer()

        assert analyzer1 is analyzer2

    def test_singleton_state_persistence(self):
        """测试单例状态持久化"""
        analyzer1 = get_learning_analyzer()

        change = CanvasChange(
            change_id="change_singleton_test",
            canvas_id="test.canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="node_singleton",
            node_type="text",
            old_content={"id": "node_singleton", "color": COLOR_RED, "text": "问题"},
            new_content={"id": "node_singleton", "color": COLOR_PURPLE, "text": "问题"},
            timestamp=datetime.now(),
            file_path="/path/to/test.canvas",
        )

        analyzer1.analyze_change(change)

        # 通过get_learning_analyzer获取的实例应该有相同的统计
        analyzer2 = get_learning_analyzer()
        stats = analyzer2.get_learning_stats("test.canvas")

        assert stats["total_events"] >= 1  # 至少有我们刚添加的事件


# ==================== 回调函数错误处理测试 ====================


class TestCallbackErrorHandling:
    """测试回调函数错误处理"""

    def test_callback_handles_analysis_error(self, sample_red_to_purple_change):
        """测试回调函数处理分析错误"""
        with patch(
            "canvas_progress_tracker.learning_analyzer.get_learning_analyzer"
        ) as mock_analyzer:
            # 模拟分析失败
            mock_instance = MagicMock()
            mock_instance.analyze_change.side_effect = Exception("分析失败")
            mock_analyzer.return_value = mock_instance

            # 回调应该捕获异常并重新抛出
            with pytest.raises(Exception):
                learning_analysis_callback(sample_red_to_purple_change)

    def test_callback_performance_logging(self, sample_red_to_purple_change):
        """测试回调函数性能日志"""
        with patch(
            "canvas_progress_tracker.data_stores.get_hot_data_store"
        ) as mock_store:
            mock_hot_store = MagicMock()
            mock_store.return_value = mock_hot_store

            start_time = time.perf_counter()
            learning_analysis_callback(sample_red_to_purple_change)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # 回调总耗时应该 < 50ms
            assert elapsed_ms < 50, f"回调耗时 {elapsed_ms:.2f}ms 超过50ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
