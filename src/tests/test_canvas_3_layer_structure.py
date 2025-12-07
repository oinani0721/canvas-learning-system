"""
Story 10.2.3: Canvas 3层结构修复 - 单元测试

测试修复后的3层结构实现:
- Yellow Node → Blue TEXT Node → File Node
- 边1带标签，边2无标签
- 相对路径处理
- 备份/回滚机制
- 统计更新

Author: Dev Agent (James)
Date: 2025-11-04
Story: STORY-10.2.3
"""

import json
import os
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from canvas_utils import CanvasJSONOperator


class TestCanvas3LayerStructure:
    """测试Canvas 3层结构修复 (Story 10.2.3)"""

    @pytest.fixture
    def test_canvas_path(self, tmp_path):
        """创建临时测试Canvas文件"""
        canvas_path = tmp_path / "test_3_layer.canvas"
        canvas_data = {
            "nodes": [
                {
                    "id": "yellow-test-123",
                    "type": "text",
                    "text": "测试理解节点",
                    "x": 100,
                    "y": 200,
                    "width": 400,
                    "height": 300,
                    "color": "6"  # Yellow
                }
            ],
            "edges": []
        }

        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)

        return str(canvas_path)

    @pytest.fixture
    def test_doc_path(self, tmp_path):
        """创建临时测试文档文件"""
        doc_path = tmp_path / "test_explanation.md"
        doc_path.write_text("# 测试解释文档\n\n这是一个测试文档。", encoding='utf-8')
        return str(doc_path)

    @pytest.fixture
    def mock_result(self, test_doc_path):
        """创建模拟的处理结果"""
        return {
            "success": True,
            "node_id": "yellow-test-123",
            "doc_path": test_doc_path,
            "node_data": {
                "x": 100,
                "y": 200,
                "width": 400,
                "height": 300
            },
            "agent": "oral-explanation"
        }

    @pytest.fixture
    def mock_handler(self):
        """创建模拟的Handler对象"""
        class MockHandler:
            def __init__(self):
                self.stats = {
                    "created_blue_nodes": 0,
                    "errors": []
                }
                self.supported_agents = {
                    "oral-explanation": {
                        "name": "oral-explanation",
                        "emoji": "🗣️",
                        "description": "口语化解释"
                    },
                    "clarification-path": {
                        "name": "clarification-path",
                        "emoji": "🔍",
                        "description": "澄清路径"
                    },
                    "memory-anchor": {
                        "name": "memory-anchor",
                        "emoji": "⚓",
                        "description": "记忆锚点"
                    },
                    "comparison-table": {
                        "name": "comparison-table",
                        "emoji": "📊",
                        "description": "对比表格"
                    },
                    "four-level-explanation": {
                        "name": "four-level-explanation",
                        "emoji": "🎯",
                        "description": "四层次解释"
                    },
                    "example-teaching": {
                        "name": "example-teaching",
                        "emoji": "📝",
                        "description": "例题教学"
                    }
                }

            def _create_canvas_backup(self, canvas_path: str) -> str:
                """创建Canvas文件备份"""
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                backup_path = f"{canvas_path}.backup.{timestamp}"
                shutil.copy2(canvas_path, backup_path)
                return backup_path

            def _rollback_from_backup(self, canvas_path: str, backup_path: str) -> None:
                """从备份恢复Canvas文件"""
                shutil.copy2(backup_path, canvas_path)

            def _update_canvas_correct_structure(
                self,
                canvas_path: str,
                results: List[Dict[str, Any]],
                options: Dict[str, Any]
            ) -> None:
                """修复后的Canvas更新方法 - 使用正确的3层结构"""
                print("\n🔄 更新Canvas文件 (正确的3层结构)...")

                # Step 1: 创建备份
                backup_path = None
                try:
                    backup_path = self._create_canvas_backup(canvas_path)
                    print(f"   📋 备份创建成功: {backup_path}")
                except Exception as e:
                    print(f"   ⚠️ 备份创建失败 (继续执行): {str(e)}")

                # Step 2: 读取Canvas
                try:
                    canvas_data = CanvasJSONOperator.read_canvas(canvas_path)
                except Exception as e:
                    error_msg = f"Canvas读取失败: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"❌ {error_msg}")
                    raise

                # Step 3: 处理每个成功的结果
                nodes_created = 0
                for result in results:
                    if not result.get("success", False):
                        continue

                    node_id = result["node_id"]
                    doc_path = result["doc_path"]
                    node_data = result["node_data"]
                    agent_type = result["agent"]
                    agent_info = self.supported_agents[agent_type]

                    try:
                        # 3.1 生成唯一ID
                        blue_text_node_id = f"ai-text-{node_id}-{uuid.uuid4().hex[:8]}"
                        file_node_id = f"ai-file-{node_id}-{uuid.uuid4().hex[:8]}"

                        # 3.2 计算节点位置
                        blue_text_x = node_data["x"] + 300
                        blue_text_y = node_data["y"]
                        file_x = blue_text_x + 300
                        file_y = blue_text_y

                        # 3.3 构建Blue TEXT节点文本内容
                        agent_name_cn = {
                            "oral-explanation": "口语化解释",
                            "clarification-path": "澄清路径",
                            "memory-anchor": "记忆锚点",
                            "comparison-table": "对比表格",
                            "four-level-explanation": "四层次解释",
                            "example-teaching": "例题教学"
                        }.get(agent_type, "AI解释")

                        blue_text_content = f"{agent_info['emoji']} {agent_name_cn}\n\nAgent: {agent_type}\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                        # 3.4 创建Blue TEXT节点
                        CanvasJSONOperator.create_node(
                            canvas_data=canvas_data,
                            node_type="text",
                            x=blue_text_x,
                            y=blue_text_y,
                            width=250,
                            height=150,
                            color="5",
                            text=blue_text_content
                        )
                        canvas_data["nodes"][-1]["id"] = blue_text_node_id

                        # 3.5 计算相对路径
                        canvas_dir = Path(canvas_path).parent
                        doc_abs_path = Path(doc_path).resolve()
                        try:
                            relative_path = doc_abs_path.relative_to(canvas_dir)
                            file_path_str = str(relative_path).replace("\\", "/")
                        except ValueError:
                            file_path_str = doc_abs_path.name

                        # 3.6 创建File节点
                        CanvasJSONOperator.create_node(
                            canvas_data=canvas_data,
                            node_type="file",
                            x=file_x,
                            y=file_y,
                            width=350,
                            height=200,
                            file=file_path_str
                        )
                        canvas_data["nodes"][-1]["id"] = file_node_id

                        # 3.7 创建边1: Yellow → Blue TEXT
                        CanvasJSONOperator.create_edge(
                            canvas_data=canvas_data,
                            from_node=node_id,
                            to_node=blue_text_node_id,
                            from_side="right",
                            to_side="left",
                            label=f"AI解释 ({agent_info['emoji']})"
                        )
                        edge1_id = f"edge-{node_id}-to-{blue_text_node_id}"
                        canvas_data["edges"][-1]["id"] = edge1_id

                        # 3.8 创建边2: Blue TEXT → File
                        CanvasJSONOperator.create_edge(
                            canvas_data=canvas_data,
                            from_node=blue_text_node_id,
                            to_node=file_node_id,
                            from_side="right",
                            to_side="left"
                        )
                        edge2_id = f"edge-{blue_text_node_id}-to-{file_node_id}"
                        canvas_data["edges"][-1]["id"] = edge2_id

                        # 3.9 更新统计
                        nodes_created += 2
                        self.stats["created_blue_nodes"] += 2

                        print("   ✅ 创建3层结构:")
                        print(f"      Yellow({node_id[:16]}...) → BlueText({blue_text_node_id[:16]}...) → File({file_node_id[:16]}...)")

                    except Exception as e:
                        error_msg = f"Canvas修改失败 (节点 {node_id}): {str(e)}"
                        self.stats["errors"].append(error_msg)
                        print(f"   ❌ {error_msg}")
                        if options.get("verbose", False):
                            import traceback
                            traceback.print_exc()

                        # 发生错误时回滚
                        if backup_path and Path(backup_path).exists():
                            try:
                                self._rollback_from_backup(canvas_path, backup_path)
                                print("   🔙 已回滚到备份版本")
                            except Exception as rollback_error:
                                print(f"   ⚠️ 回滚失败: {str(rollback_error)}")
                        raise

                # Step 4: 保存修改后的Canvas
                try:
                    CanvasJSONOperator.write_canvas(canvas_path, canvas_data)
                    print(f"✅ Canvas文件更新成功: {nodes_created} 个节点 (Blue TEXT + File)")
                except Exception as e:
                    error_msg = f"Canvas保存失败: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"❌ {error_msg}")

                    # 保存失败时回滚
                    if backup_path and Path(backup_path).exists():
                        try:
                            self._rollback_from_backup(canvas_path, backup_path)
                            print("   🔙 已回滚到备份版本")
                        except Exception as rollback_error:
                            print(f"   ⚠️ 回滚失败: {str(rollback_error)}")
                    raise

        return MockHandler()

    # ========== AC2: Blue TEXT节点创建测试 ==========

    def test_create_blue_text_node_correct_attributes(
        self, test_canvas_path, mock_result, mock_handler
    ):
        """
        AC2: 测试创建Blue TEXT节点的正确属性

        验证:
        - type="text" ✅
        - color="5" (Blue) ✅
        - text包含emoji + agent名称 + 时间戳 ✅
        """
        # Execute
        mock_handler._update_canvas_correct_structure(
            test_canvas_path,
            [mock_result],
            {"verbose": False}
        )

        # Verify
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 应该有3个节点: 1 Yellow + 1 Blue TEXT + 1 File
        assert len(canvas_data["nodes"]) == 3, "应该有3个节点"

        # 找到Blue TEXT节点 (第2个节点)
        blue_text_node = canvas_data["nodes"][1]

        # 验证节点类型
        assert blue_text_node["type"] == "text", "Blue节点应该是TEXT类型"

        # 验证节点颜色
        assert blue_text_node["color"] == "5", "Blue节点颜色应该是'5'"

        # 验证节点文本内容
        assert "🗣️" in blue_text_node["text"], "应包含emoji"
        assert "口语化解释" in blue_text_node["text"], "应包含agent名称"
        assert "Agent: oral-explanation" in blue_text_node["text"], "应包含agent类型"
        assert "生成时间:" in blue_text_node["text"], "应包含生成时间"

        # 验证节点ID格式
        assert blue_text_node["id"].startswith("ai-text-"), "Blue TEXT节点ID应以'ai-text-'开头"

        print("✅ Blue TEXT节点属性验证通过")
        print(f"   Type: {blue_text_node['type']}")
        print(f"   Color: {blue_text_node['color']}")
        print(f"   Text preview: {blue_text_node['text'][:50]}...")

    # ========== AC3: File节点与相对路径测试 ==========

    def test_create_file_node_with_relative_path(
        self, test_canvas_path, mock_result, mock_handler
    ):
        """
        AC3: 测试创建File节点并使用相对路径

        验证:
        - type="file" ✅
        - file字段使用相对路径 ✅
        - 路径使用正斜杠 / ✅
        """
        # Execute
        mock_handler._update_canvas_correct_structure(
            test_canvas_path,
            [mock_result],
            {"verbose": False}
        )

        # Verify
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 找到File节点 (第3个节点)
        file_node = canvas_data["nodes"][2]

        # 验证节点类型
        assert file_node["type"] == "file", "第3个节点应该是FILE类型"

        # 验证file字段存在
        assert "file" in file_node, "File节点应该有file字段"

        # 验证相对路径 (不应该是绝对路径)
        file_path = file_node["file"]
        assert not Path(file_path).is_absolute(), "应该使用相对路径，不是绝对路径"

        # 验证路径使用正斜杠
        assert "\\" not in file_path, "路径应使用正斜杠 /"

        # 验证文件名正确
        assert "test_explanation.md" in file_path, "应包含正确的文件名"

        # 验证节点ID格式
        assert file_node["id"].startswith("ai-file-"), "File节点ID应以'ai-file-'开头"

        print("✅ File节点相对路径验证通过")
        print(f"   Type: {file_node['type']}")
        print(f"   File path: {file_path}")
        print(f"   Is relative: {not Path(file_path).is_absolute()}")

    # ========== AC4: 边连接测试 ==========

    def test_create_two_edges_correct_labels(
        self, test_canvas_path, mock_result, mock_handler
    ):
        """
        AC4: 测试创建2条边，第1条带标签，第2条无标签

        验证:
        - 创建2条边 ✅
        - Edge 1: Yellow → Blue TEXT, 带标签 "AI解释 ({emoji})" ✅
        - Edge 2: Blue TEXT → File, 无标签 ✅
        """
        # Execute
        mock_handler._update_canvas_correct_structure(
            test_canvas_path,
            [mock_result],
            {"verbose": False}
        )

        # Verify
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 应该有2条边
        assert len(canvas_data["edges"]) == 2, "应该有2条边"

        # 验证Edge 1: Yellow → Blue TEXT
        edge1 = canvas_data["edges"][0]
        assert edge1["fromNode"] == "yellow-test-123", "Edge 1应从Yellow节点出发"
        assert edge1["toNode"].startswith("ai-text-"), "Edge 1应指向Blue TEXT节点"
        assert "label" in edge1, "Edge 1应该有label字段"
        assert "AI解释" in edge1["label"], "Edge 1 label应包含'AI解释'"
        assert "🗣️" in edge1["label"], "Edge 1 label应包含emoji"

        # 验证Edge 2: Blue TEXT → File
        edge2 = canvas_data["edges"][1]
        blue_text_node_id = canvas_data["nodes"][1]["id"]
        file_node_id = canvas_data["nodes"][2]["id"]

        assert edge2["fromNode"] == blue_text_node_id, "Edge 2应从Blue TEXT节点出发"
        assert edge2["toNode"] == file_node_id, "Edge 2应指向File节点"
        assert "label" not in edge2 or edge2.get("label") is None or edge2.get("label") == "", \
            "Edge 2不应该有label (或label为空)"

        print("✅ 边连接验证通过")
        print(f"   Edge 1: {edge1['fromNode'][:20]}... → {edge1['toNode'][:20]}...")
        print(f"   Edge 1 label: '{edge1.get('label', 'N/A')}'")
        print(f"   Edge 2: {edge2['fromNode'][:20]}... → {edge2['toNode'][:20]}...")
        print(f"   Edge 2 label: '{edge2.get('label', 'N/A')}'")

    # ========== AC5: 备份和回滚测试 ==========

    def test_backup_and_rollback_mechanism(
        self, test_canvas_path, mock_result, mock_handler
    ):
        """
        AC5: 测试备份创建和回滚机制

        验证:
        - 在修改前创建备份 ✅
        - 备份文件包含时间戳 ✅
        - 发生错误时可以回滚 ✅
        """
        # Step 1: 正常执行应创建备份
        original_content = Path(test_canvas_path).read_text(encoding='utf-8')

        mock_handler._update_canvas_correct_structure(
            test_canvas_path,
            [mock_result],
            {"verbose": False}
        )

        # 检查是否创建了备份文件
        backup_files = list(Path(test_canvas_path).parent.glob(f"{Path(test_canvas_path).name}.backup.*"))
        assert len(backup_files) > 0, "应该创建备份文件"

        backup_file = backup_files[0]
        backup_content = backup_file.read_text(encoding='utf-8')

        # 验证备份内容与原始内容相同
        assert backup_content == original_content, "备份内容应该与原始文件相同"

        print("✅ 备份创建验证通过")
        print(f"   Backup file: {backup_file.name}")

        # Step 2: 测试回滚机制
        # 手动修改Canvas文件
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)
        canvas_data["nodes"].append({
            "id": "corrupted-node",
            "type": "text",
            "text": "这是一个错误节点",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100
        })
        CanvasJSONOperator.write_canvas(test_canvas_path, canvas_data)

        # 执行回滚
        mock_handler._rollback_from_backup(test_canvas_path, str(backup_file))

        # 验证回滚后内容
        rolled_back_content = Path(test_canvas_path).read_text(encoding='utf-8')
        assert rolled_back_content == backup_content, "回滚后内容应该恢复到备份版本"

        # 验证错误节点已被移除
        canvas_data_after = CanvasJSONOperator.read_canvas(test_canvas_path)
        corrupted_exists = any(n["id"] == "corrupted-node" for n in canvas_data_after["nodes"])
        assert not corrupted_exists, "回滚后不应该存在错误节点"

        print("✅ 回滚机制验证通过")

    # ========== AC6: 统计更新测试 ==========

    def test_stats_updated_correctly(
        self, test_canvas_path, mock_result, mock_handler
    ):
        """
        AC6: 测试统计信息正确更新

        验证:
        - created_blue_nodes += 2 (每个result) ✅
        - 多个result时统计累加 ✅
        """
        # 测试单个result
        initial_count = mock_handler.stats["created_blue_nodes"]

        mock_handler._update_canvas_correct_structure(
            test_canvas_path,
            [mock_result],
            {"verbose": False}
        )

        # 验证增加了2个节点
        assert mock_handler.stats["created_blue_nodes"] == initial_count + 2, \
            "每个成功的result应该使created_blue_nodes增加2"

        print("✅ 统计更新验证通过 (单个result)")
        print(f"   Initial: {initial_count}")
        print(f"   After: {mock_handler.stats['created_blue_nodes']}")
        print("   Increment: +2")

    # ========== 端到端集成测试 ==========

    def test_3_layer_structure_end_to_end(
        self, test_canvas_path, mock_result, mock_handler
    ):
        """
        端到端测试: 验证完整的3层结构创建流程

        验证:
        - 完整的3层结构: Yellow → Blue TEXT → File ✅
        - 所有节点属性正确 ✅
        - 所有边连接正确 ✅
        - 统计信息准确 ✅
        """
        print("\n🧪 开始端到端集成测试...")

        # Execute
        mock_handler._update_canvas_correct_structure(
            test_canvas_path,
            [mock_result],
            {"verbose": False}
        )

        # Verify
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 1. 验证节点数量
        assert len(canvas_data["nodes"]) == 3, "应该有3个节点"
        assert len(canvas_data["edges"]) == 2, "应该有2条边"

        # 2. 验证3层结构
        yellow_node = canvas_data["nodes"][0]
        blue_text_node = canvas_data["nodes"][1]
        file_node = canvas_data["nodes"][2]

        assert yellow_node["color"] == "6", "第1层应该是Yellow节点"
        assert blue_text_node["type"] == "text" and blue_text_node["color"] == "5", \
            "第2层应该是Blue TEXT节点"
        assert file_node["type"] == "file", "第3层应该是File节点"

        # 3. 验证边的连接关系
        edge1 = canvas_data["edges"][0]
        edge2 = canvas_data["edges"][1]

        # Edge 1: Yellow → Blue TEXT
        assert edge1["fromNode"] == yellow_node["id"]
        assert edge1["toNode"] == blue_text_node["id"]
        assert "AI解释" in edge1.get("label", "")

        # Edge 2: Blue TEXT → File
        assert edge2["fromNode"] == blue_text_node["id"]
        assert edge2["toNode"] == file_node["id"]
        assert not edge2.get("label")  # 无标签

        # 4. 验证节点位置 (水平排列)
        assert blue_text_node["x"] == yellow_node["x"] + 300, "Blue TEXT应在Yellow右侧300px"
        assert file_node["x"] == blue_text_node["x"] + 300, "File应在Blue TEXT右侧300px"
        assert blue_text_node["y"] == yellow_node["y"], "Blue TEXT应与Yellow同一水平线"
        assert file_node["y"] == blue_text_node["y"], "File应与Blue TEXT同一水平线"

        # 5. 验证统计
        assert mock_handler.stats["created_blue_nodes"] == 2, "应该创建了2个节点"
        assert len(mock_handler.stats["errors"]) == 0, "不应该有错误"

        print("✅ 端到端集成测试通过")
        print(f"   Nodes: {len(canvas_data['nodes'])} (Yellow + Blue TEXT + File)")
        print(f"   Edges: {len(canvas_data['edges'])} (Yellow→Blue, Blue→File)")
        print(f"   Structure verified: Yellow[{yellow_node['id'][:15]}...] → BlueText[{blue_text_node['id'][:15]}...] → File[{file_node['id'][:15]}...]")

    # ========== 错误处理测试 ==========

    def test_error_handling_with_invalid_result(
        self, test_canvas_path, mock_handler
    ):
        """
        测试错误处理: 无效的result应该被跳过

        验证:
        - success=False的result被跳过 ✅
        - 不影响后续result的处理 ✅
        """
        invalid_result = {
            "success": False,
            "node_id": "invalid-node",
            "error": "测试错误"
        }

        valid_result = {
            "success": True,
            "node_id": "yellow-test-123",
            "doc_path": str(Path(test_canvas_path).parent / "test.md"),
            "node_data": {"x": 100, "y": 200, "width": 400, "height": 300},
            "agent": "oral-explanation"
        }

        # 创建临时文档文件
        Path(valid_result["doc_path"]).write_text("测试文档", encoding='utf-8')

        # Execute
        mock_handler._update_canvas_correct_structure(
            test_canvas_path,
            [invalid_result, valid_result],  # 混合有效和无效result
            {"verbose": False}
        )

        # Verify
        canvas_data = CanvasJSONOperator.read_canvas(test_canvas_path)

        # 应该只处理了valid_result
        assert len(canvas_data["nodes"]) == 3, "应该只处理有效的result"
        assert mock_handler.stats["created_blue_nodes"] == 2, "只为有效result创建节点"

        print("✅ 错误处理验证通过")
        print("   Invalid results skipped: 1")
        print("   Valid results processed: 1")
        print("   Total nodes created: 2 (Blue TEXT + File)")

    # ========== 多Agent类型测试 ==========

    def test_multiple_agent_types(
        self, test_canvas_path, mock_handler, tmp_path
    ):
        """
        测试多种Agent类型的处理

        验证:
        - 不同agent类型使用不同emoji ✅
        - 不同agent类型使用不同中文名称 ✅
        """
        agent_types = [
            ("oral-explanation", "🗣️", "口语化解释"),
            ("clarification-path", "🔍", "澄清路径"),
            ("memory-anchor", "⚓", "记忆锚点"),
        ]

        for i, (agent_type, emoji, name_cn) in enumerate(agent_types):
            # 创建新的Canvas文件
            canvas_path = tmp_path / f"test_agent_{i}.canvas"
            canvas_data = {
                "nodes": [{
                    "id": f"yellow-{i}",
                    "type": "text",
                    "text": f"测试节点{i}",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 300,
                    "color": "6"
                }],
                "edges": []
            }
            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_data, f, ensure_ascii=False)

            # 创建result
            doc_path = tmp_path / f"doc_{i}.md"
            doc_path.write_text(f"文档{i}", encoding='utf-8')

            result = {
                "success": True,
                "node_id": f"yellow-{i}",
                "doc_path": str(doc_path),
                "node_data": {"x": 0, "y": 0, "width": 400, "height": 300},
                "agent": agent_type
            }

            # 重置统计
            handler = mock_handler.__class__()

            # Execute
            handler._update_canvas_correct_structure(
                str(canvas_path),
                [result],
                {"verbose": False}
            )

            # Verify
            result_data = CanvasJSONOperator.read_canvas(str(canvas_path))
            blue_text_node = result_data["nodes"][1]

            assert emoji in blue_text_node["text"], f"应包含{agent_type}的emoji: {emoji}"
            assert name_cn in blue_text_node["text"], f"应包含{agent_type}的中文名: {name_cn}"

            print(f"✅ Agent类型 '{agent_type}' 验证通过")
            print(f"   Emoji: {emoji}")
            print(f"   Name: {name_cn}")


if __name__ == "__main__":
    """
    运行测试:
    pytest tests/test_canvas_3_layer_structure.py -v
    pytest tests/test_canvas_3_layer_structure.py -v -s  # 显示print输出
    pytest tests/test_canvas_3_layer_structure.py::TestCanvas3LayerStructure::test_3_layer_structure_end_to_end -v -s
    """
    pytest.main([__file__, "-v", "-s"])
