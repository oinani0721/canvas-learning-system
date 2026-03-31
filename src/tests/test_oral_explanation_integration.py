"""
测试口语化解释功能的集成测试

包括：
- 文件命名规范验证
- Canvas节点创建验证
- 边创建验证
- 端到端集成测试
"""

import json
import os
import re

# 假设canvas_utils.py在项目根目录
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from canvas_utils import COLOR_BLUE, CanvasJSONOperator, CanvasOrchestrator


def test_filename_convention():
    """测试文件命名规范：{topic}-口语化解释-{timestamp}.md"""
    topic = "逆否命题"
    timestamp = "20251015143025"
    expected = f"{topic}-口语化解释-{timestamp}.md"

    # 验证命名格式
    pattern = r"^.+-口语化解释-\d{14}\.md$"
    assert re.match(pattern, expected), f"文件名格式不符合规范: {expected}"

    # 验证时间戳格式
    timestamp_pattern = r"\d{14}"
    timestamp_match = re.search(timestamp_pattern, expected)
    assert timestamp_match, "时间戳格式不正确"

    extracted_timestamp = timestamp_match.group()
    assert len(extracted_timestamp) == 14, "时间戳应为14位数字"

    # 验证可以解析为有效日期
    try:
        datetime.strptime(extracted_timestamp, "%Y%m%d%H%M%S")
    except ValueError:
        assert False, f"时间戳无法解析为有效日期: {extracted_timestamp}"

    print("[PASS] 文件命名规范验证通过")


def test_blue_node_creation():
    """测试蓝色说明节点创建（color="5"）"""
    # 创建测试Canvas文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".canvas", delete=False, encoding="utf-8"
    ) as f:
        test_canvas_path = f.name
        test_canvas = {
            "nodes": [
                {
                    "id": "question-test123",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 100,
                    "y": 200,
                    "width": 400,
                    "height": 120,
                    "color": "1",
                }
            ],
            "edges": [],
        }
        json.dump(test_canvas, f, ensure_ascii=False, indent=2)

    try:
        # 创建Orchestrator并调用create_explanation_nodes
        orchestrator = CanvasOrchestrator(test_canvas_path)
        result = orchestrator.create_explanation_nodes(
            question_node_id="question-test123",
            explanation_type="口语化解释",
            file_path="./test-口语化解释-20251015143025.md",
        )

        # 验证返回结果
        assert "blue_node_id" in result, "返回结果应包含blue_node_id"
        assert "file_node_id" in result, "返回结果应包含file_node_id"

        # 读取更新后的Canvas
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 查找蓝色节点
        blue_node = next(
            (n for n in canvas_data["nodes"] if n["id"] == result["blue_node_id"]), None
        )

        assert blue_node is not None, "蓝色节点应被创建"
        assert blue_node["type"] == "text", "蓝色节点类型应为text"
        assert blue_node["color"] == COLOR_BLUE, (
            f"蓝色节点颜色应为{COLOR_BLUE}（字符串）"
        )
        assert "💡 口语化解释" in blue_node["text"], "蓝色节点内容应包含表情符号和说明"
        assert "点击查看详细内容" in blue_node["text"], "蓝色节点应提示用户点击"

        print("[PASS] 蓝色节点创建验证通过")

    finally:
        # 清理测试文件
        if os.path.exists(test_canvas_path):
            os.unlink(test_canvas_path)


def test_file_node_creation():
    """测试file节点创建并正确引用.md文件"""
    # 创建测试Canvas文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".canvas", delete=False, encoding="utf-8"
    ) as f:
        test_canvas_path = f.name
        test_canvas = {
            "nodes": [
                {
                    "id": "question-test123",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 100,
                    "y": 200,
                    "width": 400,
                    "height": 120,
                    "color": "1",
                }
            ],
            "edges": [],
        }
        json.dump(test_canvas, f, ensure_ascii=False, indent=2)

    try:
        # 创建Orchestrator并调用create_explanation_nodes
        orchestrator = CanvasOrchestrator(test_canvas_path)
        file_path = "./逆否命题-口语化解释-20251015143025.md"

        result = orchestrator.create_explanation_nodes(
            question_node_id="question-test123",
            explanation_type="口语化解释",
            file_path=file_path,
        )

        # 读取更新后的Canvas
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 查找file节点
        file_node = next(
            (n for n in canvas_data["nodes"] if n["id"] == result["file_node_id"]), None
        )

        assert file_node is not None, "file节点应被创建"
        assert file_node["type"] == "file", "file节点类型应为file"
        assert file_node["file"] == file_path, "file节点应引用正确的文件路径"
        assert file_node["file"].startswith("./"), "file路径应使用相对路径（以./开头）"

        print("[PASS] file节点创建验证通过")

    finally:
        # 清理测试文件
        if os.path.exists(test_canvas_path):
            os.unlink(test_canvas_path)


def test_edge_creation():
    """测试连接边创建：问题→蓝色节点→file节点"""
    # 创建测试Canvas文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".canvas", delete=False, encoding="utf-8"
    ) as f:
        test_canvas_path = f.name
        test_canvas = {
            "nodes": [
                {
                    "id": "question-test123",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 100,
                    "y": 200,
                    "width": 400,
                    "height": 120,
                    "color": "1",
                }
            ],
            "edges": [],
        }
        json.dump(test_canvas, f, ensure_ascii=False, indent=2)

    try:
        # 创建Orchestrator并调用create_explanation_nodes
        orchestrator = CanvasOrchestrator(test_canvas_path)
        result = orchestrator.create_explanation_nodes(
            question_node_id="question-test123",
            explanation_type="口语化解释",
            file_path="./test-口语化解释-20251015143025.md",
        )

        # 读取更新后的Canvas
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 验证边1：问题 → 蓝色说明节点
        edge1 = next(
            (
                e
                for e in canvas_data["edges"]
                if e["fromNode"] == "question-test123"
                and e["toNode"] == result["blue_node_id"]
            ),
            None,
        )

        assert edge1 is not None, "应创建从问题到蓝色节点的连接边"
        assert edge1["label"] == "补充解释", "边1标签应为'补充解释'"

        # 验证边2：蓝色说明节点 → file节点
        edge2 = next(
            (
                e
                for e in canvas_data["edges"]
                if e["fromNode"] == result["blue_node_id"]
                and e["toNode"] == result["file_node_id"]
            ),
            None,
        )

        assert edge2 is not None, "应创建从蓝色节点到file节点的连接边"
        assert edge2["label"] == "详细内容", "边2标签应为'详细内容'"

        print("[PASS] 连接边创建验证通过")

    finally:
        # 清理测试文件
        if os.path.exists(test_canvas_path):
            os.unlink(test_canvas_path)


def test_node_positioning():
    """测试节点定位：蓝色节点在问题右侧偏下，file节点在蓝色节点右侧"""
    # 创建测试Canvas文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".canvas", delete=False, encoding="utf-8"
    ) as f:
        test_canvas_path = f.name
        test_canvas = {
            "nodes": [
                {
                    "id": "question-test123",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 100,
                    "y": 200,
                    "width": 400,
                    "height": 120,
                    "color": "1",
                }
            ],
            "edges": [],
        }
        json.dump(test_canvas, f, ensure_ascii=False, indent=2)

    try:
        # 创建Orchestrator并调用create_explanation_nodes
        orchestrator = CanvasOrchestrator(test_canvas_path)
        result = orchestrator.create_explanation_nodes(
            question_node_id="question-test123",
            explanation_type="口语化解释",
            file_path="./test-口语化解释-20251015143025.md",
        )

        # 读取更新后的Canvas
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 获取节点
        question_node = next(
            n for n in canvas_data["nodes"] if n["id"] == "question-test123"
        )
        blue_node = next(
            n for n in canvas_data["nodes"] if n["id"] == result["blue_node_id"]
        )
        file_node = next(
            n for n in canvas_data["nodes"] if n["id"] == result["file_node_id"]
        )

        # 验证蓝色节点在问题右侧
        assert blue_node["x"] > question_node["x"], "蓝色节点应在问题节点右侧"

        # 验证蓝色节点稍微向下偏移
        assert blue_node["y"] >= question_node["y"], (
            "蓝色节点应在问题节点同一高度或稍低"
        )

        # 验证file节点在蓝色节点右侧
        assert file_node["x"] > blue_node["x"], "file节点应在蓝色节点右侧"

        print("[PASS] 节点定位验证通过")

    finally:
        # 清理测试文件
        if os.path.exists(test_canvas_path):
            os.unlink(test_canvas_path)


def test_error_handling_invalid_question_node():
    """测试错误处理：问题节点不存在"""
    # 创建测试Canvas文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".canvas", delete=False, encoding="utf-8"
    ) as f:
        test_canvas_path = f.name
        test_canvas = {"nodes": [], "edges": []}
        json.dump(test_canvas, f, ensure_ascii=False, indent=2)

    try:
        orchestrator = CanvasOrchestrator(test_canvas_path)

        # 尝试使用不存在的节点ID
        try:
            orchestrator.create_explanation_nodes(
                question_node_id="nonexistent-node",
                explanation_type="口语化解释",
                file_path="./test.md",
            )
            assert False, "应该抛出ValueError"
        except ValueError as e:
            assert "不存在" in str(e), "错误消息应包含'不存在'"
            print(f"[PASS] 错误处理验证通过: {e}")

    finally:
        # 清理测试文件
        if os.path.exists(test_canvas_path):
            os.unlink(test_canvas_path)


if __name__ == "__main__":
    print("开始验证口语化解释集成功能...\n")

    try:
        test_filename_convention()
        test_blue_node_creation()
        test_file_node_creation()
        test_edge_creation()
        test_node_positioning()
        test_error_handling_invalid_question_node()

        print("\n" + "=" * 50)
        print("SUCCESS: 所有集成测试通过！")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        raise
