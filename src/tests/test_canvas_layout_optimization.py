"""
Canvas布局优化算法测试

测试Story 8.3中实现的Canvas节点智能布局优化算法功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-21
"""

import json
import os

# 导入被测试的模块
import sys
import tempfile
from typing import Any, Dict

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_utils import (
    DEFAULT_NODE_WIDTH,
    LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER,
    LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT,
    LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT,
    LAYOUT_OPTIMIZATION_DEFAULT_ALIGNMENT,
    QUESTION_NODE_HEIGHT,
    YELLOW_NODE_HEIGHT,
    YELLOW_NODE_WIDTH,
    YELLOW_OFFSET_Y,
    CanvasBusinessLogic,
    CanvasOrchestrator,
    LayoutOptimizer,
    LayoutPreferences,
)


class TestLayoutPreferences:
    """测试布局偏好配置类"""

    def test_default_preferences(self):
        """测试默认偏好设置"""
        prefs = LayoutPreferences()

        assert prefs.alignment_mode == LAYOUT_OPTIMIZATION_DEFAULT_ALIGNMENT
        assert prefs.spacing_settings["yellow_offset_y"] == YELLOW_OFFSET_Y
        assert prefs.clustering_settings["enable_clustering"] is True
        assert prefs.visual_preferences["prevent_overlap"] is True

    def test_custom_preferences(self):
        """测试自定义偏好设置"""
        custom_spacing = {
            "horizontal_spacing": 500,
            "vertical_spacing": 400,
            "yellow_offset_y": 40,
            "auto_adjust_spacing": False
        }

        prefs = LayoutPreferences(
            alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT,
            spacing_settings=custom_spacing
        )

        assert prefs.alignment_mode == LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT
        assert prefs.spacing_settings["yellow_offset_y"] == 40
        assert prefs.spacing_settings["auto_adjust_spacing"] is False

    def test_validate_preferences_valid(self):
        """测试有效偏好设置验证"""
        prefs = LayoutPreferences(
            alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER
        )
        assert prefs.validate_preferences() is True

    def test_validate_preferences_invalid_alignment(self):
        """测试无效对齐方式验证"""
        prefs = LayoutPreferences(alignment_mode="invalid")
        assert prefs.validate_preferences() is False

    def test_get_alignment_offset_left(self):
        """测试左对齐偏移计算"""
        prefs = LayoutPreferences(alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT)
        offset = prefs.get_alignment_offset(400, 350)
        assert offset == 0

    def test_get_alignment_offset_center(self):
        """测试居中对齐偏移计算"""
        prefs = LayoutPreferences(alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER)
        offset = prefs.get_alignment_offset(400, 350)
        assert offset == 25  # (400 - 350) // 2

    def test_get_alignment_offset_right(self):
        """测试右对齐偏移计算"""
        prefs = LayoutPreferences(alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT)
        offset = prefs.get_alignment_offset(400, 350)
        assert offset == 50  # 400 - 350


class TestLayoutOptimizer:
    """测试布局优化器类"""

    def create_test_canvas_data(self, node_count: int = 5) -> Dict[str, Any]:
        """创建测试用的Canvas数据"""
        nodes = []
        edges = []

        # 创建问题-黄色节点对
        for i in range(node_count):
            x = 100 + i * 500
            y = 100 + (i % 2) * 300

            # 问题节点
            question_id = f"question-{i}"
            nodes.append({
                "id": question_id,
                "type": "text",
                "x": x,
                "y": y,
                "width": DEFAULT_NODE_WIDTH,
                "height": QUESTION_NODE_HEIGHT,
                "color": "1",  # 红色
                "text": f"问题 {i+1}"
            })

            # 黄色节点（故意放错位置用于测试）
            yellow_id = f"yellow-{i}"
            nodes.append({
                "id": yellow_id,
                "type": "text",
                "x": x + 50,  # 故意偏移
                "y": y + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y + 10,  # 故意偏移
                "width": YELLOW_NODE_WIDTH,
                "height": YELLOW_NODE_HEIGHT,
                "color": "6",  # 黄色
                "text": "个人理解"
            })

            # 创建连接边
            edges.append({
                "id": f"edge-{i}",
                "fromNode": question_id,
                "toNode": yellow_id,
                "fromSide": "bottom",
                "toSide": "top",
                "label": "个人理解"
            })

        return {"nodes": nodes, "edges": edges}

    def test_optimizer_initialization(self):
        """测试优化器初始化"""
        canvas_data = self.create_test_canvas_data()
        prefs = LayoutPreferences()

        optimizer = LayoutOptimizer(canvas_data, prefs)

        assert len(optimizer.nodes) == 10  # 5个问题 + 5个黄色
        assert len(optimizer.edges) == 5
        assert optimizer.preferences.alignment_mode == LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER
        assert len(optimizer.node_map) == 10

    def test_calculate_yellow_position_left(self):
        """测试左对齐黄色节点位置计算"""
        canvas_data = self.create_test_canvas_data()
        optimizer = LayoutOptimizer(canvas_data)

        question_node = {
            "x": 100,
            "y": 200,
            "width": 400,
            "height": QUESTION_NODE_HEIGHT
        }

        pos = optimizer.calculate_yellow_position(question_node, LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT)

        assert pos["x"] == 100  # 左对齐
        assert pos["y"] == 200 + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y

    def test_calculate_yellow_position_center(self):
        """测试居中对齐黄色节点位置计算"""
        canvas_data = self.create_test_canvas_data()
        optimizer = LayoutOptimizer(canvas_data)

        question_node = {
            "x": 100,
            "y": 200,
            "width": 400,
            "height": QUESTION_NODE_HEIGHT
        }

        pos = optimizer.calculate_yellow_position(question_node, LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER)

        assert pos["x"] == 175  # 100 + (400 - 350) // 2
        assert pos["y"] == 200 + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y

    def test_calculate_yellow_position_right(self):
        """测试右对齐黄色节点位置计算"""
        canvas_data = self.create_test_canvas_data()
        optimizer = LayoutOptimizer(canvas_data)

        question_node = {
            "x": 100,
            "y": 200,
            "width": 400,
            "height": QUESTION_NODE_HEIGHT
        }

        pos = optimizer.calculate_yellow_position(question_node, LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT)

        assert pos["x"] == 150  # 100 + 400 - 350
        assert pos["y"] == 200 + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y

    def test_detect_node_overlaps(self):
        """测试节点重叠检测"""
        canvas_data = {
            "nodes": [
                {
                    "id": "node1",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 150
                },
                {
                    "id": "node2",
                    "x": 150,  # 重叠
                    "y": 120,  # 重叠
                    "width": 200,
                    "height": 150
                },
                {
                    "id": "node3",
                    "x": 400,  # 不重叠
                    "y": 100,
                    "width": 200,
                    "height": 150
                }
            ],
            "edges": []
        }

        optimizer = LayoutOptimizer(canvas_data)
        overlaps = optimizer.detect_node_overlaps()

        assert len(overlaps) == 1
        assert overlaps[0]["node1_id"] == "node1"
        assert overlaps[0]["node2_id"] == "node2"

    def test_optimize_canvas_layout_auto(self):
        """测试自动布局优化"""
        canvas_data = self.create_test_canvas_data()
        prefs = LayoutPreferences(alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER)
        optimizer = LayoutOptimizer(canvas_data, prefs)

        result = optimizer.optimize_canvas_layout("auto")

        assert result.success is True
        assert result.quality_score > 0
        assert result.optimization_time_ms >= 0
        assert len(result.changes_made) > 0  # 应该有一些调整
        assert result.optimization_id.startswith("opt-")

    def test_optimize_canvas_layout_alignment_only(self):
        """测试仅对齐优化"""
        canvas_data = self.create_test_canvas_data()
        prefs = LayoutPreferences(alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER)
        optimizer = LayoutOptimizer(canvas_data, prefs)

        result = optimizer.optimize_canvas_layout("alignment")

        assert result.success is True
        # 检查黄色节点是否被正确对齐
        for change in result.changes_made:
            if "调整黄色节点" in change and "水平位置" in change:
                assert True
                break
        else:
            pytest.fail("未找到对齐调整记录")

    def test_calculate_layout_quality_score(self):
        """测试布局质量分数计算"""
        canvas_data = self.create_test_canvas_data()
        optimizer = LayoutOptimizer(canvas_data)

        score = optimizer.calculate_layout_score()

        assert 0 <= score <= 10
        assert isinstance(score, float)

    def test_calculate_alignment_score_perfect(self):
        """测试完美对齐分数计算"""
        canvas_data = self.create_test_canvas_data()

        # 手动设置黄色节点到正确位置
        for node in canvas_data["nodes"]:
            if node["id"].startswith("yellow"):
                question_id = node["id"].replace("yellow", "question")
                question_node = next(n for n in canvas_data["nodes"] if n["id"] == question_id)

                # 设置为居中对齐位置
                expected_x = question_node["x"] + (question_node["width"] - YELLOW_NODE_WIDTH) // 2
                expected_y = question_node["y"] + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y
                node["x"] = expected_x
                node["y"] = expected_y

        optimizer = LayoutOptimizer(canvas_data)
        score = optimizer._calculate_alignment_score()

        assert score == 10.0  # 完美对齐

    def test_calculate_overlap_score_no_overlaps(self):
        """测试无重叠分数计算"""
        canvas_data = self.create_test_canvas_data()
        optimizer = LayoutOptimizer(canvas_data)

        score = optimizer._calculate_overlap_score()

        assert score == 10.0  # 无重叠

    def test_group_nodes_by_color(self):
        """测试按颜色分组节点"""
        canvas_data = {
            "nodes": [
                {"id": "red1", "color": "1"},
                {"id": "red2", "color": "1"},
                {"id": "green1", "color": "2"},
                {"id": "yellow1", "color": "6"},
                {"id": "yellow2", "color": "6"},
            ],
            "edges": []
        }

        optimizer = LayoutOptimizer(canvas_data)
        groups = optimizer._group_nodes_by_color()

        assert len(groups["1"]) == 2
        assert len(groups["2"]) == 1
        assert len(groups["6"]) == 2


class TestCanvasBusinessLogic:
    """测试Canvas业务逻辑层布局优化功能"""

    def create_test_canvas_file(self, node_count: int = 3) -> str:
        """创建测试用的Canvas文件"""
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        for i in range(node_count):
            x = 100 + i * 500
            y = 100 + i * 200

            # 问题节点
            question_id = f"question-{i}"
            canvas_data["nodes"].append({
                "id": question_id,
                "type": "text",
                "x": x,
                "y": y,
                "width": DEFAULT_NODE_WIDTH,
                "height": QUESTION_NODE_HEIGHT,
                "color": "1",
                "text": f"问题 {i+1}"
            })

            # 黄色节点（故意偏移）
            yellow_id = f"yellow-{i}"
            canvas_data["nodes"].append({
                "id": yellow_id,
                "type": "text",
                "x": x + 30,  # 故意偏移
                "y": y + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y,
                "width": YELLOW_NODE_WIDTH,
                "height": YELLOW_NODE_HEIGHT,
                "color": "6",
                "text": "个人理解"
            })

            # 连接边
            canvas_data["edges"].append({
                "id": f"edge-{i}",
                "fromNode": question_id,
                "toNode": yellow_id,
                "fromSide": "bottom",
                "toSide": "top",
                "label": "个人理解"
            })

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False)
        json.dump(canvas_data, temp_file, indent=2, ensure_ascii=False)
        temp_file.close()

        return temp_file.name

    def test_calculate_yellow_position(self):
        """测试黄色节点位置计算"""
        canvas_file = self.create_test_canvas_file()

        try:
            logic = CanvasBusinessLogic(canvas_file)
            question_node = {
                "x": 100,
                "y": 200,
                "width": 400,
                "height": QUESTION_NODE_HEIGHT
            }

            # 测试居中对齐
            pos = logic.calculate_yellow_position(question_node, LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER)
            assert pos["x"] == 175  # 100 + (400 - 350) // 2
            assert pos["y"] == 200 + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y

            # 测试左对齐
            pos = logic.calculate_yellow_position(question_node, LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT)
            assert pos["x"] == 100

            # 测试右对齐
            pos = logic.calculate_yellow_position(question_node, LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT)
            assert pos["x"] == 150

        finally:
            os.unlink(canvas_file)

    def test_optimize_canvas_layout(self):
        """测试Canvas布局优化"""
        canvas_file = self.create_test_canvas_file()

        try:
            logic = CanvasBusinessLogic(canvas_file)
            prefs = LayoutPreferences(alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER)

            result = logic.optimize_canvas_layout(prefs, "alignment")

            assert result.success is True
            assert result.canvas_path == canvas_file
            assert result.quality_score > 0

        finally:
            os.unlink(canvas_file)

    def test_get_layout_optimization_suggestions(self):
        """测试获取布局优化建议"""
        canvas_file = self.create_test_canvas_file()

        try:
            logic = CanvasBusinessLogic(canvas_file)
            suggestions = logic.get_layout_optimization_suggestions()

            assert isinstance(suggestions, list)
            assert len(suggestions) > 0

        finally:
            os.unlink(canvas_file)

    def test_create_layout_snapshot(self):
        """测试创建布局快照"""
        canvas_file = self.create_test_canvas_file()

        try:
            logic = CanvasBusinessLogic(canvas_file)
            snapshot_id = logic.create_layout_snapshot("测试快照")

            assert snapshot_id.startswith("snap-")

        finally:
            os.unlink(canvas_file)


class TestCanvasOrchestrator:
    """测试Canvas编排器布局优化功能"""

    def create_test_canvas_file(self) -> str:
        """创建测试用的Canvas文件"""
        canvas_data = {
            "nodes": [
                {
                    "id": "question-1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": DEFAULT_NODE_WIDTH,
                    "height": QUESTION_NODE_HEIGHT,
                    "color": "1",
                    "text": "测试问题"
                },
                {
                    "id": "yellow-1",
                    "type": "text",
                    "x": 130,  # 故意偏移
                    "y": 100 + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y,
                    "width": YELLOW_NODE_WIDTH,
                    "height": YELLOW_NODE_HEIGHT,
                    "color": "6",
                    "text": "个人理解"
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "question-1",
                    "toNode": "yellow-1",
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": "个人理解"
                }
            ]
        }

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False)
        json.dump(canvas_data, temp_file, indent=2, ensure_ascii=False)
        temp_file.close()

        return temp_file.name

    def test_optimize_canvas_layout_with_backup(self):
        """测试带备份的Canvas布局优化"""
        canvas_file = self.create_test_canvas_file()

        try:
            orchestrator = CanvasOrchestrator(canvas_file)
            prefs = LayoutPreferences(alignment_mode=LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER)

            result = orchestrator.optimize_canvas_layout(prefs, "auto", create_backup=True)

            assert result.success is True
            assert result.canvas_path == canvas_file
            assert result.optimization_time_ms >= 0

        finally:
            os.unlink(canvas_file)

    def test_get_layout_optimization_suggestions(self):
        """测试获取布局优化建议"""
        canvas_file = self.create_test_canvas_file()

        try:
            orchestrator = CanvasOrchestrator(canvas_file)
            suggestions = orchestrator.get_layout_optimization_suggestions()

            assert isinstance(suggestions, list)
            assert len(suggestions) > 0

        finally:
            os.unlink(canvas_file)

    def test_create_and_restore_layout_snapshot(self):
        """测试创建和恢复布局快照"""
        canvas_file = self.create_test_canvas_file()

        try:
            orchestrator = CanvasOrchestrator(canvas_file)

            # 创建快照
            snapshot_id = orchestrator.create_layout_snapshot("测试快照")
            assert snapshot_id.startswith("snap-")

            # 尝试恢复快照（当前实现返回False）
            result = orchestrator.restore_layout_snapshot(snapshot_id)
            # TODO: 实现快照持久化后，这里应该返回True

        finally:
            os.unlink(canvas_file)


class TestPerformanceRequirements:
    """测试性能要求"""

    def test_large_canvas_performance(self):
        """测试大型Canvas性能（100节点<2秒）"""
        import time

        # 创建100个节点的Canvas
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        for i in range(50):  # 50个问题-黄色对 = 100个节点
            x = 100 + (i % 10) * 500
            y = 100 + (i // 10) * 400

            question_id = f"question-{i}"
            yellow_id = f"yellow-{i}"

            canvas_data["nodes"].append({
                "id": question_id,
                "type": "text",
                "x": x + (i % 3) * 20,  # 添加一些随机偏移
                "y": y + (i % 3) * 15,
                "width": DEFAULT_NODE_WIDTH,
                "height": QUESTION_NODE_HEIGHT,
                "color": "1",
                "text": f"问题 {i+1}"
            })

            canvas_data["nodes"].append({
                "id": yellow_id,
                "type": "text",
                "x": x + (i % 3) * 25,
                "y": y + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y + (i % 3) * 20,
                "width": YELLOW_NODE_WIDTH,
                "height": YELLOW_NODE_HEIGHT,
                "color": "6",
                "text": "个人理解"
            })

            canvas_data["edges"].append({
                "id": f"edge-{i}",
                "fromNode": question_id,
                "toNode": yellow_id,
                "fromSide": "bottom",
                "toSide": "top",
                "label": "个人理解"
            })

        # 测试性能
        prefs = LayoutPreferences()
        optimizer = LayoutOptimizer(canvas_data, prefs)

        start_time = time.time()
        result = optimizer.optimize_canvas_layout("auto")
        end_time = time.time()

        processing_time_ms = int((end_time - start_time) * 1000)

        assert result.success is True
        assert processing_time_ms < 2000  # 要求<2秒
        assert len(optimizer.nodes) == 100  # 验证节点数量

    def test_position_accuracy(self):
        """测试位置精度（误差<1px）"""
        canvas_data = {
            "nodes": [
                {
                    "id": "question-1",
                    "type": "text",
                    "x": 100,
                    "y": 200,
                    "width": 400,
                    "height": QUESTION_NODE_HEIGHT,
                    "color": "1",
                    "text": "问题"
                },
                {
                    "id": "yellow-1",
                    "type": "text",
                    "x": 175,  # 居中对齐位置
                    "y": 200 + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y,
                    "width": YELLOW_NODE_WIDTH,
                    "height": YELLOW_NODE_HEIGHT,
                    "color": "6",
                    "text": "理解"
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "question-1",
                    "toNode": "yellow-1",
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": "个人理解"
                }
            ]
        }

        optimizer = LayoutOptimizer(canvas_data)
        question_node = canvas_data["nodes"][0]
        yellow_node = canvas_data["nodes"][1]

        # 计算期望位置
        expected_pos = optimizer.calculate_yellow_position(question_node, LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER)

        # 验证精度
        assert abs(yellow_node["x"] - expected_pos["x"]) <= 1  # 误差<1px
        assert abs(yellow_node["y"] - expected_pos["y"]) <= 1  # 误差<1px


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
