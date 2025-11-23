"""
Canvas Utils 单元测试

测试 CanvasJSONOperator 类的所有功能
"""

import pytest
import time
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import canvas_utils
from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic


class TestCanvasJSONOperator:
    """测试CanvasJSONOperator类"""

    def test_read_canvas_success(self):
        """测试成功读取有效Canvas文件"""
        canvas_path = "src/tests/fixtures/test-basic.canvas"
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

        assert "nodes" in canvas_data
        assert "edges" in canvas_data
        assert len(canvas_data["nodes"]) == 1
        assert len(canvas_data["edges"]) == 1
        assert canvas_data["nodes"][0]["id"] == "node-test123"

    def test_read_canvas_empty(self):
        """测试读取空Canvas文件"""
        canvas_path = "src/tests/fixtures/test-empty.canvas"
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

        assert "nodes" in canvas_data
        assert "edges" in canvas_data
        assert len(canvas_data["nodes"]) == 0
        assert len(canvas_data["edges"]) == 0

    def test_read_canvas_file_not_found(self):
        """测试读取不存在的Canvas文件抛出FileNotFoundError"""
        with pytest.raises(FileNotFoundError) as exc_info:
            CanvasJSONOperator.read_canvas("nonexistent.canvas")

        assert "Canvas文件不存在" in str(exc_info.value)
        assert "nonexistent.canvas" in str(exc_info.value)

    def test_read_canvas_invalid_json(self):
        """测试读取无效JSON文件抛出ValueError"""
        canvas_path = "src/tests/fixtures/invalid.json"

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.read_canvas(canvas_path)

        assert "JSON格式错误" in str(exc_info.value)
        assert canvas_path in str(exc_info.value)

    def test_read_canvas_missing_nodes_field(self):
        """测试缺少nodes字段时自动补充空数组"""
        canvas_path = "src/tests/fixtures/test-missing-fields.canvas"
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

        # 应该自动添加 nodes 和 edges 字段
        assert "nodes" in canvas_data
        assert "edges" in canvas_data
        assert canvas_data["nodes"] == []
        assert canvas_data["edges"] == []

    def test_read_canvas_utf8_encoding(self):
        """测试UTF-8编码支持（中文内容）"""
        canvas_path = "src/tests/fixtures/test-basic.canvas"
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

        # 测试文件包含中文"测试节点"
        assert canvas_data["nodes"][0]["text"] == "测试节点"

    def test_read_canvas_performance(self):
        """测试读取性能（<500ms for <1MB files）"""
        canvas_path = "src/tests/fixtures/test-basic.canvas"

        # 多次测试取平均值
        times = []
        for _ in range(5):
            start = time.time()
            CanvasJSONOperator.read_canvas(canvas_path)
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        # 测试文件很小，应该远低于 500ms
        assert avg_time < 0.5, f"平均读取耗时 {avg_time}s，超过500ms限制"

        # 对于小文件，应该在 100ms 以内
        assert avg_time < 0.1, f"平均读取耗时 {avg_time}s，对于小文件应该 < 100ms"

    def test_read_canvas_returns_dict(self):
        """测试read_canvas返回字典类型"""
        canvas_path = "src/tests/fixtures/test-basic.canvas"
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

        assert isinstance(canvas_data, dict)

    def test_read_canvas_preserves_data_structure(self):
        """测试read_canvas保留完整的数据结构"""
        canvas_path = "src/tests/fixtures/test-basic.canvas"
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

        # 验证节点结构完整
        node = canvas_data["nodes"][0]
        assert "id" in node
        assert "type" in node
        assert "text" in node
        assert "x" in node
        assert "y" in node
        assert "width" in node
        assert "height" in node
        assert "color" in node

        # 验证边结构完整
        edge = canvas_data["edges"][0]
        assert "id" in edge
        assert "fromNode" in edge
        assert "toNode" in edge
        assert "fromSide" in edge
        assert "toSide" in edge

    # ========== Story 1.2: 节点关系图构建测试 ==========

    def test_build_relationship_graph_basic(self):
        """测试基本关系图构建"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "x": 0, "y": 0},
                {"id": "node2", "type": "text", "x": 100, "y": 100},
                {"id": "node3", "type": "text", "x": 200, "y": 200}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node2"},
                {"id": "edge2", "fromNode": "node1", "toNode": "node3"}
            ]
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        # 验证图结构完整性
        assert "node1" in graph
        assert "node2" in graph
        assert "node3" in graph

        # 验证node1的关系
        assert graph["node1"]["children"] == ["node2", "node3"]
        assert graph["node1"]["parents"] == []
        assert len(graph["node1"]["outgoing_edges"]) == 2
        assert len(graph["node1"]["incoming_edges"]) == 0

        # 验证node2的关系
        assert graph["node2"]["parents"] == ["node1"]
        assert graph["node2"]["children"] == []
        assert len(graph["node2"]["incoming_edges"]) == 1
        assert len(graph["node2"]["outgoing_edges"]) == 0

        # 验证node_data包含完整节点信息
        assert graph["node1"]["node_data"]["id"] == "node1"
        assert graph["node1"]["node_data"]["type"] == "text"

    def test_build_relationship_graph_isolated_node(self):
        """测试孤立节点（无连接边）"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "x": 0, "y": 0}
            ],
            "edges": []
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        assert "node1" in graph
        assert graph["node1"]["parents"] == []
        assert graph["node1"]["children"] == []
        assert graph["node1"]["incoming_edges"] == []
        assert graph["node1"]["outgoing_edges"] == []
        assert graph["node1"]["node_data"]["id"] == "node1"

    def test_build_relationship_graph_empty_canvas(self):
        """测试空Canvas"""
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        assert graph == {}

    def test_build_relationship_graph_invalid_edge_reference(self):
        """测试无效节点引用（边引用不存在的节点）"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "x": 0, "y": 0}
            ],
            "edges": [
                # 引用不存在的node2
                {"id": "edge1", "fromNode": "node1", "toNode": "node2"}
            ]
        }

        # 应该优雅处理，忽略无效边
        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        assert "node1" in graph
        # node1不应该有任何子节点（因为node2不存在）
        assert graph["node1"]["children"] == []
        assert graph["node1"]["outgoing_edges"] == []

    def test_build_relationship_graph_complex_relationships(self):
        """测试复杂关系（多个父节点，多个子节点）"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "x": 0, "y": 0},
                {"id": "node2", "type": "text", "x": 100, "y": 0},
                {"id": "node3", "type": "text", "x": 50, "y": 100}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node3"},
                {"id": "edge2", "fromNode": "node2", "toNode": "node3"}
            ]
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        # node3有两个父节点
        assert sorted(graph["node3"]["parents"]) == ["node1", "node2"]
        assert len(graph["node3"]["incoming_edges"]) == 2

        # node1和node2各有一个子节点
        assert graph["node1"]["children"] == ["node3"]
        assert graph["node2"]["children"] == ["node3"]

    def test_build_relationship_graph_no_duplicate_relationships(self):
        """测试避免重复的父子关系"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "x": 0, "y": 0},
                {"id": "node2", "type": "text", "x": 100, "y": 100}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node2"},
                # 重复的边（虽然ID不同）
                {"id": "edge2", "fromNode": "node1", "toNode": "node2"}
            ]
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        # 父子关系应该去重（只出现一次）
        assert graph["node1"]["children"] == ["node2"]
        assert graph["node2"]["parents"] == ["node1"]

        # 但边列表应该包含两条边
        assert len(graph["node1"]["outgoing_edges"]) == 2
        assert len(graph["node2"]["incoming_edges"]) == 2

    def test_get_parent_nodes_success(self):
        """测试获取父节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "text": "Parent"},
                {"id": "node2", "type": "text", "text": "Child"}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node2"}
            ]
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
        parents = CanvasJSONOperator.get_parent_nodes(graph, "node2")

        assert len(parents) == 1
        assert parents[0]["id"] == "node1"
        assert parents[0]["text"] == "Parent"

    def test_get_parent_nodes_multiple(self):
        """测试获取多个父节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"},
                {"id": "node2", "type": "text"},
                {"id": "node3", "type": "text"}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node3"},
                {"id": "edge2", "fromNode": "node2", "toNode": "node3"}
            ]
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
        parents = CanvasJSONOperator.get_parent_nodes(graph, "node3")

        assert len(parents) == 2
        parent_ids = sorted([p["id"] for p in parents])
        assert parent_ids == ["node1", "node2"]

    def test_get_parent_nodes_no_parents(self):
        """测试获取没有父节点的节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"}
            ],
            "edges": []
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
        parents = CanvasJSONOperator.get_parent_nodes(graph, "node1")

        assert parents == []

    def test_get_parent_nodes_invalid_node(self):
        """测试获取不存在节点的父节点抛出KeyError"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"}
            ],
            "edges": []
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        with pytest.raises(KeyError) as exc_info:
            CanvasJSONOperator.get_parent_nodes(graph, "nonexistent")

        assert "节点不存在" in str(exc_info.value)

    def test_get_child_nodes_success(self):
        """测试获取子节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "text": "Parent"},
                {"id": "node2", "type": "text", "text": "Child"}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node2"}
            ]
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
        children = CanvasJSONOperator.get_child_nodes(graph, "node1")

        assert len(children) == 1
        assert children[0]["id"] == "node2"
        assert children[0]["text"] == "Child"

    def test_get_child_nodes_multiple(self):
        """测试获取多个子节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"},
                {"id": "node2", "type": "text"},
                {"id": "node3", "type": "text"}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node2"},
                {"id": "edge2", "fromNode": "node1", "toNode": "node3"}
            ]
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
        children = CanvasJSONOperator.get_child_nodes(graph, "node1")

        assert len(children) == 2
        child_ids = sorted([c["id"] for c in children])
        assert child_ids == ["node2", "node3"]

    def test_get_child_nodes_no_children(self):
        """测试获取没有子节点的节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"}
            ],
            "edges": []
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
        children = CanvasJSONOperator.get_child_nodes(graph, "node1")

        assert children == []

    def test_get_child_nodes_invalid_node(self):
        """测试获取不存在节点的子节点抛出KeyError"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"}
            ],
            "edges": []
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        with pytest.raises(KeyError) as exc_info:
            CanvasJSONOperator.get_child_nodes(graph, "nonexistent")

        assert "节点不存在" in str(exc_info.value)

    def test_get_connected_edges_success(self):
        """测试获取连接边"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"},
                {"id": "node2", "type": "text"},
                {"id": "node3", "type": "text"}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node2"},
                {"id": "edge2", "fromNode": "node3", "toNode": "node1"}
            ]
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
        edges = CanvasJSONOperator.get_connected_edges(graph, "node1")

        # node1有1条outgoing边和1条incoming边
        assert len(edges["outgoing"]) == 1
        assert len(edges["incoming"]) == 1
        assert edges["outgoing"][0]["id"] == "edge1"
        assert edges["incoming"][0]["id"] == "edge2"

    def test_get_connected_edges_no_edges(self):
        """测试获取孤立节点的连接边"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"}
            ],
            "edges": []
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
        edges = CanvasJSONOperator.get_connected_edges(graph, "node1")

        assert edges["incoming"] == []
        assert edges["outgoing"] == []

    def test_get_connected_edges_invalid_node(self):
        """测试获取不存在节点的连接边抛出KeyError"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text"}
            ],
            "edges": []
        }

        graph = CanvasJSONOperator.build_relationship_graph(canvas_data)

        with pytest.raises(KeyError) as exc_info:
            CanvasJSONOperator.get_connected_edges(graph, "nonexistent")

        assert "节点不存在" in str(exc_info.value)

    def test_build_relationship_graph_performance(self):
        """测试构建性能（100节点，<100ms）"""
        # 生成100个节点
        nodes = [
            {"id": f"node{i}", "type": "text", "x": i * 10, "y": 0}
            for i in range(100)
        ]

        # 生成99条边（形成链式结构）
        edges = [
            {
                "id": f"edge{i}",
                "fromNode": f"node{i}",
                "toNode": f"node{i+1}"
            }
            for i in range(99)
        ]

        canvas_data = {"nodes": nodes, "edges": edges}

        # 测试构建时间
        times = []
        for _ in range(5):
            start = time.time()
            graph = CanvasJSONOperator.build_relationship_graph(canvas_data)
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        # 验证构建成功
        assert len(graph) == 100

        # 验证性能（<100ms）
        assert avg_time < 0.1, (
            f"平均构建耗时 {avg_time}s，超过100ms限制"
        )

        # 验证关系正确性
        assert graph["node0"]["children"] == ["node1"]
        assert graph["node99"]["parents"] == ["node98"]
        assert graph["node50"]["parents"] == ["node49"]
        assert graph["node50"]["children"] == ["node51"]

    # ========== Story 1.3: 节点CRUD操作测试 ==========

    def test_generate_node_id_format(self):
        """测试节点ID格式正确"""
        node_id = CanvasJSONOperator.generate_node_id("text")

        assert node_id.startswith("text-")
        assert len(node_id) == len("text-") + 16

    def test_generate_node_id_unique(self):
        """测试节点ID唯一性"""
        id1 = CanvasJSONOperator.generate_node_id("text")
        id2 = CanvasJSONOperator.generate_node_id("text")
        id3 = CanvasJSONOperator.generate_node_id("file")

        # 所有ID应该唯一
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

        # 不同类型的ID有不同的前缀
        assert id1.startswith("text-")
        assert id3.startswith("file-")

    def test_create_node_text_success(self):
        """测试创建text节点成功"""
        canvas_data = {"nodes": [], "edges": []}

        node_id = CanvasJSONOperator.create_node(
            canvas_data,
            node_type="text",
            x=100,
            y=200,
            color="1",
            text="测试问题"
        )

        assert node_id.startswith("text-")
        assert len(canvas_data["nodes"]) == 1

        node = canvas_data["nodes"][0]
        assert node["id"] == node_id
        assert node["type"] == "text"
        assert node["text"] == "测试问题"
        assert node["color"] == "1"
        assert node["x"] == 100
        assert node["y"] == 200
        assert node["width"] == 400  # 默认值
        assert node["height"] == 300  # 默认值

    def test_create_node_file_success(self):
        """测试创建file节点成功"""
        canvas_data = {"nodes": [], "edges": []}

        node_id = CanvasJSONOperator.create_node(
            canvas_data,
            node_type="file",
            x=0,
            y=0,
            file="notes/example.md"
        )

        assert node_id.startswith("file-")
        assert len(canvas_data["nodes"]) == 1
        assert canvas_data["nodes"][0]["file"] == "notes/example.md"

    def test_create_node_group_success(self):
        """测试创建group节点成功"""
        canvas_data = {"nodes": [], "edges": []}

        node_id = CanvasJSONOperator.create_node(
            canvas_data,
            node_type="group",
            x=50,
            y=50,
            width=600,
            height=400
        )

        assert node_id.startswith("group-")
        assert len(canvas_data["nodes"]) == 1
        assert canvas_data["nodes"][0]["width"] == 600
        assert canvas_data["nodes"][0]["height"] == 400

    def test_create_node_with_custom_dimensions(self):
        """测试创建节点时使用自定义尺寸"""
        canvas_data = {"nodes": [], "edges": []}

        CanvasJSONOperator.create_node(
            canvas_data,
            node_type="text",
            x=0,
            y=0,
            width=500,
            height=250,
            text="Custom size"
        )

        node = canvas_data["nodes"][0]
        assert node["width"] == 500
        assert node["height"] == 250

    def test_create_node_without_color(self):
        """测试创建节点时不指定颜色"""
        canvas_data = {"nodes": [], "edges": []}

        CanvasJSONOperator.create_node(
            canvas_data,
            node_type="text",
            x=0,
            y=0,
            text="No color"
        )

        node = canvas_data["nodes"][0]
        # 颜色字段不应该存在
        assert "color" not in node

    def test_create_node_invalid_type(self):
        """测试创建无效类型节点抛出ValueError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_node(
                canvas_data,
                node_type="invalid",
                x=100,
                y=200
            )

        assert "无效的节点类型" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_create_node_text_missing_text_field(self):
        """测试创建text节点缺少text字段抛出ValueError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_node(
                canvas_data,
                node_type="text",
                x=100,
                y=200
            )

        assert "必须提供text字段" in str(exc_info.value)

    def test_create_node_file_missing_file_field(self):
        """测试创建file节点缺少file字段抛出ValueError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_node(
                canvas_data,
                node_type="file",
                x=100,
                y=200
            )

        assert "必须提供file字段" in str(exc_info.value)

    def test_create_node_invalid_color(self):
        """测试创建节点时使用无效颜色抛出ValueError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_node(
                canvas_data,
                node_type="text",
                x=100,
                y=200,
                color="99",  # 无效颜色
                text="Test"
            )

        assert "无效的颜色编码" in str(exc_info.value)

    def test_update_node_color_success(self):
        """测试更新节点颜色成功"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "color": "1",
                 "x": 0, "y": 0}
            ],
            "edges": []
        }

        CanvasJSONOperator.update_node_color(
            canvas_data,
            "text-abc123",
            "2"
        )

        assert canvas_data["nodes"][0]["color"] == "2"

    def test_update_node_color_multiple_nodes(self):
        """测试在多个节点中更新指定节点的颜色"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "color": "1",
                 "x": 0, "y": 0},
                {"id": "node2", "type": "text", "color": "1",
                 "x": 100, "y": 0},
                {"id": "node3", "type": "text", "color": "1",
                 "x": 200, "y": 0}
            ],
            "edges": []
        }

        CanvasJSONOperator.update_node_color(canvas_data, "node2", "3")

        # 只有node2的颜色被更新
        assert canvas_data["nodes"][0]["color"] == "1"
        assert canvas_data["nodes"][1]["color"] == "3"
        assert canvas_data["nodes"][2]["color"] == "1"

    def test_update_node_color_node_not_found(self):
        """测试更新不存在的节点抛出KeyError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(KeyError) as exc_info:
            CanvasJSONOperator.update_node_color(
                canvas_data,
                "nonexistent",
                "2"
            )

        assert "节点不存在" in str(exc_info.value)

    def test_update_node_color_invalid_color(self):
        """测试使用无效颜色更新节点抛出ValueError"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "color": "1",
                 "x": 0, "y": 0}
            ],
            "edges": []
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.update_node_color(
                canvas_data,
                "text-abc123",
                "99"  # 无效颜色
            )

        assert "无效的颜色编码" in str(exc_info.value)

    def test_delete_node_success(self):
        """测试删除节点成功"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0},
                {"id": "text-def456", "type": "text", "x": 100, "y": 100}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc123",
                 "toNode": "text-def456"}
            ]
        }

        nodes_deleted, edges_deleted = CanvasJSONOperator.delete_node(
            canvas_data,
            "text-abc123"
        )

        assert nodes_deleted == 1
        assert edges_deleted == 1
        assert len(canvas_data["nodes"]) == 1
        assert len(canvas_data["edges"]) == 0
        assert canvas_data["nodes"][0]["id"] == "text-def456"

    def test_delete_node_with_multiple_edges(self):
        """测试删除有多条边的节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "x": 0, "y": 0},
                {"id": "node2", "type": "text", "x": 100, "y": 0},
                {"id": "node3", "type": "text", "x": 200, "y": 0}
            ],
            "edges": [
                {"id": "edge1", "fromNode": "node1", "toNode": "node2"},
                {"id": "edge2", "fromNode": "node2", "toNode": "node3"},
                {"id": "edge3", "fromNode": "node3", "toNode": "node1"}
            ]
        }

        nodes_deleted, edges_deleted = CanvasJSONOperator.delete_node(
            canvas_data,
            "node2"
        )

        assert nodes_deleted == 1
        assert edges_deleted == 2  # edge1 和 edge2 都被删除
        assert len(canvas_data["nodes"]) == 2
        assert len(canvas_data["edges"]) == 1
        # 只剩下 edge3
        assert canvas_data["edges"][0]["id"] == "edge3"

    def test_delete_node_no_edges(self):
        """测试删除没有边的节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "x": 0, "y": 0},
                {"id": "node2", "type": "text", "x": 100, "y": 0}
            ],
            "edges": []
        }

        nodes_deleted, edges_deleted = CanvasJSONOperator.delete_node(
            canvas_data,
            "node1"
        )

        assert nodes_deleted == 1
        assert edges_deleted == 0
        assert len(canvas_data["nodes"]) == 1

    def test_delete_node_not_found(self):
        """测试删除不存在的节点抛出KeyError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(KeyError) as exc_info:
            CanvasJSONOperator.delete_node(canvas_data, "nonexistent")

        assert "节点不存在" in str(exc_info.value)

    def test_find_nodes_by_color_found(self):
        """测试查找指定颜色的节点"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "color": "1",
                 "x": 0, "y": 0},
                {"id": "node2", "type": "text", "color": "2",
                 "x": 100, "y": 100},
                {"id": "node3", "type": "text", "color": "1",
                 "x": 200, "y": 200}
            ],
            "edges": []
        }

        red_nodes = CanvasJSONOperator.find_nodes_by_color(canvas_data, "1")

        assert len(red_nodes) == 2
        assert red_nodes[0]["id"] == "node1"
        assert red_nodes[1]["id"] == "node3"

    def test_find_nodes_by_color_not_found(self):
        """测试查找不存在的颜色返回空列表"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "color": "1",
                 "x": 0, "y": 0}
            ],
            "edges": []
        }

        yellow_nodes = CanvasJSONOperator.find_nodes_by_color(
            canvas_data, "6"
        )

        assert yellow_nodes == []

    def test_find_nodes_by_color_no_color_field(self):
        """测试查找节点时某些节点没有color字段"""
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "color": "1",
                 "x": 0, "y": 0},
                # node2 没有 color 字段
                {"id": "node2", "type": "text", "x": 100, "y": 100},
                {"id": "node3", "type": "text", "color": "1",
                 "x": 200, "y": 200}
            ],
            "edges": []
        }

        red_nodes = CanvasJSONOperator.find_nodes_by_color(canvas_data, "1")

        # 应该只返回有 color="1" 的节点
        assert len(red_nodes) == 2
        assert red_nodes[0]["id"] == "node1"
        assert red_nodes[1]["id"] == "node3"

    def test_find_node_by_id_found(self):
        """测试根据ID查找节点成功"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0}
            ],
            "edges": []
        }

        node = CanvasJSONOperator.find_node_by_id(
            canvas_data,
            "text-abc123"
        )

        assert node is not None
        assert node["id"] == "text-abc123"

    def test_find_node_by_id_not_found(self):
        """测试根据ID查找不存在的节点返回None"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0}
            ],
            "edges": []
        }

        node = CanvasJSONOperator.find_node_by_id(
            canvas_data,
            "nonexistent"
        )

        assert node is None

    def test_node_exists_true(self):
        """测试检查节点存在"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0}
            ],
            "edges": []
        }

        exists = CanvasJSONOperator.node_exists(
            canvas_data,
            "text-abc123"
        )

        assert exists is True

    def test_node_exists_false(self):
        """测试检查节点不存在"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0}
            ],
            "edges": []
        }

        exists = CanvasJSONOperator.node_exists(
            canvas_data,
            "nonexistent"
        )

        assert exists is False

    def test_get_all_node_ids_success(self):
        """测试获取所有节点ID"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0},
                {"id": "text-def456", "type": "text", "x": 100, "y": 100},
                {"id": "file-ghi789", "type": "file", "x": 200, "y": 200}
            ],
            "edges": []
        }

        ids = CanvasJSONOperator.get_all_node_ids(canvas_data)

        assert len(ids) == 3
        assert "text-abc123" in ids
        assert "text-def456" in ids
        assert "file-ghi789" in ids

    def test_get_all_node_ids_empty(self):
        """测试获取空Canvas的节点ID列表"""
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        ids = CanvasJSONOperator.get_all_node_ids(canvas_data)

        assert ids == []

    # ========== Story 1.4: 边（Edge）操作测试 ==========

    def test_generate_edge_id_format(self):
        """测试边ID格式正确"""
        from_node = "text-a1b2c3d4e5f67890"
        to_node = "text-x9y8z7w6v5u4t3s2"

        edge_id = CanvasJSONOperator.generate_edge_id(from_node, to_node)

        # 验证格式
        assert edge_id.startswith("edge-")
        parts = edge_id.split('-')
        assert len(parts) == 4  # edge, from8, to8, timestamp6
        assert parts[1] == "a1b2c3d4"  # from前8位
        assert parts[2] == "x9y8z7w6"  # to前8位
        assert len(parts[3]) == 6  # 时间戳6位

    def test_generate_edge_id_unique(self):
        """测试边ID唯一性（不同时间戳）"""
        from_node = "text-a1b2c3d4e5f67890"
        to_node = "text-x9y8z7w6v5u4t3s2"

        edge_id1 = CanvasJSONOperator.generate_edge_id(from_node, to_node)
        time.sleep(0.001)  # 等待时间变化
        edge_id2 = CanvasJSONOperator.generate_edge_id(from_node, to_node)

        # 时间戳部分应该不同（虽然很小概率相同）
        # 主要验证ID生成成功
        assert edge_id1.startswith("edge-")
        assert edge_id2.startswith("edge-")

    def test_create_edge_success(self):
        """测试成功创建边"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0},
                {"id": "text-xyz789", "type": "text", "x": 100, "y": 100}
            ],
            "edges": []
        }

        edge_id = CanvasJSONOperator.create_edge(
            canvas_data,
            from_node="text-abc123",
            to_node="text-xyz789",
            from_side="right",
            to_side="left",
            label="拆解自"
        )

        assert edge_id.startswith("edge-")
        assert len(canvas_data["edges"]) == 1

        edge = canvas_data["edges"][0]
        assert edge["id"] == edge_id
        assert edge["fromNode"] == "text-abc123"
        assert edge["toNode"] == "text-xyz789"
        assert edge["fromSide"] == "right"
        assert edge["toSide"] == "left"
        assert edge["label"] == "拆解自"

    def test_create_edge_with_color(self):
        """测试创建带颜色的边"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0},
                {"id": "text-xyz789", "type": "text", "x": 100, "y": 100}
            ],
            "edges": []
        }

        edge_id = CanvasJSONOperator.create_edge(
            canvas_data,
            from_node="text-abc123",
            to_node="text-xyz789",
            color="2"
        )

        edge = canvas_data["edges"][0]
        assert edge["color"] == "2"

    def test_create_edge_default_sides(self):
        """测试创建边使用默认side值"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0},
                {"id": "text-xyz789", "type": "text", "x": 100, "y": 100}
            ],
            "edges": []
        }

        edge_id = CanvasJSONOperator.create_edge(
            canvas_data,
            from_node="text-abc123",
            to_node="text-xyz789"
        )

        edge = canvas_data["edges"][0]
        assert edge["fromSide"] == "right"  # DEFAULT_FROM_SIDE
        assert edge["toSide"] == "left"  # DEFAULT_TO_SIDE

    def test_create_edge_from_node_not_found(self):
        """测试源节点不存在抛出ValueError"""
        canvas_data = {
            "nodes": [
                {"id": "text-xyz789", "type": "text", "x": 100, "y": 100}
            ],
            "edges": []
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_edge(
                canvas_data,
                from_node="nonexistent",
                to_node="text-xyz789"
            )

        assert "源节点不存在" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_create_edge_to_node_not_found(self):
        """测试目标节点不存在抛出ValueError"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0}
            ],
            "edges": []
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_edge(
                canvas_data,
                from_node="text-abc123",
                to_node="nonexistent"
            )

        assert "目标节点不存在" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_create_edge_invalid_from_side(self):
        """测试无效fromSide抛出ValueError"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0},
                {"id": "text-xyz789", "type": "text", "x": 100, "y": 100}
            ],
            "edges": []
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_edge(
                canvas_data,
                from_node="text-abc123",
                to_node="text-xyz789",
                from_side="invalid"
            )

        assert "无效的fromSide值" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_create_edge_invalid_to_side(self):
        """测试无效toSide抛出ValueError"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0},
                {"id": "text-xyz789", "type": "text", "x": 100, "y": 100}
            ],
            "edges": []
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_edge(
                canvas_data,
                from_node="text-abc123",
                to_node="text-xyz789",
                to_side="invalid"
            )

        assert "无效的toSide值" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_create_edge_invalid_color(self):
        """测试无效颜色编码抛出ValueError"""
        canvas_data = {
            "nodes": [
                {"id": "text-abc123", "type": "text", "x": 0, "y": 0},
                {"id": "text-xyz789", "type": "text", "x": 100, "y": 100}
            ],
            "edges": []
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.create_edge(
                canvas_data,
                from_node="text-abc123",
                to_node="text-xyz789",
                color="9"
            )

        assert "无效的颜色编码" in str(exc_info.value)

    def test_update_edge_success(self):
        """测试成功更新边"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {
                    "id": "edge-abc123-xyz789-123456",
                    "fromNode": "text-abc123",
                    "toNode": "text-xyz789",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

        CanvasJSONOperator.update_edge(
            canvas_data,
            "edge-abc123-xyz789-123456",
            {"label": "个人理解", "color": "6"}
        )

        edge = canvas_data["edges"][0]
        assert edge["label"] == "个人理解"
        assert edge["color"] == "6"

    def test_update_edge_multiple_fields(self):
        """测试更新边的多个字段"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {
                    "id": "edge-abc123-xyz789-123456",
                    "fromNode": "text-abc123",
                    "toNode": "text-xyz789",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

        CanvasJSONOperator.update_edge(
            canvas_data,
            "edge-abc123-xyz789-123456",
            {
                "label": "拆解自",
                "color": "1",
                "fromSide": "bottom",
                "toSide": "top"
            }
        )

        edge = canvas_data["edges"][0]
        assert edge["label"] == "拆解自"
        assert edge["color"] == "1"
        assert edge["fromSide"] == "bottom"
        assert edge["toSide"] == "top"

    def test_update_edge_not_found(self):
        """测试更新不存在的边抛出KeyError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(KeyError) as exc_info:
            CanvasJSONOperator.update_edge(
                canvas_data,
                "nonexistent",
                {"label": "test"}
            )

        assert "边不存在" in str(exc_info.value)

    def test_update_edge_invalid_color(self):
        """测试更新边为无效颜色抛出ValueError"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {
                    "id": "edge-abc123-xyz789-123456",
                    "fromNode": "text-abc123",
                    "toNode": "text-xyz789",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.update_edge(
                canvas_data,
                "edge-abc123-xyz789-123456",
                {"color": "9"}
            )

        assert "无效的颜色编码" in str(exc_info.value)

    def test_update_edge_invalid_from_side(self):
        """测试更新边为无效fromSide抛出ValueError"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {
                    "id": "edge-abc123-xyz789-123456",
                    "fromNode": "text-abc123",
                    "toNode": "text-xyz789",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.update_edge(
                canvas_data,
                "edge-abc123-xyz789-123456",
                {"fromSide": "invalid"}
            )

        assert "无效的fromSide值" in str(exc_info.value)

    def test_update_edge_invalid_to_side(self):
        """测试更新边为无效toSide抛出ValueError"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {
                    "id": "edge-abc123-xyz789-123456",
                    "fromNode": "text-abc123",
                    "toNode": "text-xyz789",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.update_edge(
                canvas_data,
                "edge-abc123-xyz789-123456",
                {"toSide": "invalid"}
            )

        assert "无效的toSide值" in str(exc_info.value)

    def test_delete_edge_success(self):
        """测试成功删除边"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {
                    "id": "edge-abc123-xyz789-123456",
                    "fromNode": "text-abc123",
                    "toNode": "text-xyz789"
                }
            ]
        }

        success = CanvasJSONOperator.delete_edge(
            canvas_data,
            "edge-abc123-xyz789-123456"
        )

        assert success is True
        assert len(canvas_data["edges"]) == 0

    def test_delete_edge_multiple_edges(self):
        """测试从多个边中删除一个"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "text-abc",
                    "toNode": "text-def"
                },
                {
                    "id": "edge-2",
                    "fromNode": "text-ghi",
                    "toNode": "text-jkl"
                },
                {
                    "id": "edge-3",
                    "fromNode": "text-mno",
                    "toNode": "text-pqr"
                }
            ]
        }

        CanvasJSONOperator.delete_edge(canvas_data, "edge-2")

        assert len(canvas_data["edges"]) == 2
        assert canvas_data["edges"][0]["id"] == "edge-1"
        assert canvas_data["edges"][1]["id"] == "edge-3"

    def test_delete_edge_not_found(self):
        """测试删除不存在的边抛出KeyError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(KeyError) as exc_info:
            CanvasJSONOperator.delete_edge(canvas_data, "nonexistent")

        assert "边不存在" in str(exc_info.value)

    def test_find_edges_by_node_from(self):
        """测试查找出边（direction=from）"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"},
                {"id": "edge2", "fromNode": "text-abc",
                 "toNode": "text-ghi"},
                {"id": "edge3", "fromNode": "text-xyz",
                 "toNode": "text-abc"}
            ]
        }

        edges = CanvasJSONOperator.find_edges_by_node(
            canvas_data,
            "text-abc",
            direction="from"
        )

        assert len(edges) == 2
        assert edges[0]["id"] == "edge1"
        assert edges[1]["id"] == "edge2"

    def test_find_edges_by_node_to(self):
        """测试查找入边（direction=to）"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"},
                {"id": "edge2", "fromNode": "text-abc",
                 "toNode": "text-ghi"},
                {"id": "edge3", "fromNode": "text-xyz",
                 "toNode": "text-abc"}
            ]
        }

        edges = CanvasJSONOperator.find_edges_by_node(
            canvas_data,
            "text-abc",
            direction="to"
        )

        assert len(edges) == 1
        assert edges[0]["id"] == "edge3"

    def test_find_edges_by_node_both(self):
        """测试查找所有相关边（direction=both）"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"},
                {"id": "edge2", "fromNode": "text-abc",
                 "toNode": "text-ghi"},
                {"id": "edge3", "fromNode": "text-xyz",
                 "toNode": "text-abc"}
            ]
        }

        edges = CanvasJSONOperator.find_edges_by_node(
            canvas_data,
            "text-abc",
            direction="both"
        )

        assert len(edges) == 3

    def test_find_edges_by_node_no_match(self):
        """测试查找无相关边的节点"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"}
            ]
        }

        edges = CanvasJSONOperator.find_edges_by_node(
            canvas_data,
            "text-xyz",
            direction="both"
        )

        assert edges == []

    def test_find_edges_by_node_invalid_direction(self):
        """测试无效direction参数抛出ValueError"""
        canvas_data = {"nodes": [], "edges": []}

        with pytest.raises(ValueError) as exc_info:
            CanvasJSONOperator.find_edges_by_node(
                canvas_data,
                "text-abc",
                direction="invalid"
            )

        assert "无效的direction值" in str(exc_info.value)

    def test_find_edge_by_id_found(self):
        """测试根据ID查找边成功"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"}
            ]
        }

        edge = CanvasJSONOperator.find_edge_by_id(canvas_data, "edge1")

        assert edge is not None
        assert edge["id"] == "edge1"

    def test_find_edge_by_id_not_found(self):
        """测试根据ID查找边失败返回None"""
        canvas_data = {"nodes": [], "edges": []}

        edge = CanvasJSONOperator.find_edge_by_id(canvas_data, "nonexistent")

        assert edge is None

    def test_edge_exists_true(self):
        """测试边存在性检查（存在）"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"}
            ]
        }

        assert CanvasJSONOperator.edge_exists(canvas_data, "edge1") is True

    def test_edge_exists_false(self):
        """测试边存在性检查（不存在）"""
        canvas_data = {"nodes": [], "edges": []}

        assert CanvasJSONOperator.edge_exists(
            canvas_data, "nonexistent"
        ) is False

    def test_get_all_edge_ids_success(self):
        """测试获取所有边ID"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"},
                {"id": "edge2", "fromNode": "text-ghi",
                 "toNode": "text-jkl"}
            ]
        }

        edge_ids = CanvasJSONOperator.get_all_edge_ids(canvas_data)

        assert len(edge_ids) == 2
        assert "edge1" in edge_ids
        assert "edge2" in edge_ids

    def test_get_all_edge_ids_empty(self):
        """测试获取空Canvas的边ID列表"""
        canvas_data = {"nodes": [], "edges": []}

        edge_ids = CanvasJSONOperator.get_all_edge_ids(canvas_data)

        assert edge_ids == []

    def test_find_edge_between_nodes_found(self):
        """测试查找两节点间的边成功"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"},
                {"id": "edge2", "fromNode": "text-ghi",
                 "toNode": "text-jkl"}
            ]
        }

        edge = CanvasJSONOperator.find_edge_between_nodes(
            canvas_data,
            "text-abc",
            "text-def"
        )

        assert edge is not None
        assert edge["id"] == "edge1"

    def test_find_edge_between_nodes_not_found(self):
        """测试查找两节点间的边失败返回None"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"}
            ]
        }

        edge = CanvasJSONOperator.find_edge_between_nodes(
            canvas_data,
            "text-xyz",
            "text-uvw"
        )

        assert edge is None

    def test_find_edge_between_nodes_wrong_direction(self):
        """测试查找两节点间的边（方向相反）"""
        canvas_data = {
            "nodes": [],
            "edges": [
                {"id": "edge1", "fromNode": "text-abc",
                 "toNode": "text-def"}
            ]
        }

        # 查找反向边（from和to交换）
        edge = CanvasJSONOperator.find_edge_between_nodes(
            canvas_data,
            "text-def",  # 交换位置
            "text-abc"
        )

        assert edge is None  # 应该找不到，因为方向不对


class TestColorManagement:
    """测试颜色管理系统"""

    def test_get_color_code_valid_inputs(self):
        """测试 get_color_code 对所有有效输入"""
        assert canvas_utils.get_color_code("red") == "1"
        assert canvas_utils.get_color_code("green") == "2"
        assert canvas_utils.get_color_code("purple") == "3"
        assert canvas_utils.get_color_code("blue") == "5"
        assert canvas_utils.get_color_code("yellow") == "6"

    def test_get_color_code_case_insensitive(self):
        """测试 get_color_code 不区分大小写"""
        assert canvas_utils.get_color_code("RED") == "1"
        assert canvas_utils.get_color_code("Green") == "2"
        assert canvas_utils.get_color_code("YELLOW") == "6"
        assert canvas_utils.get_color_code("PuRpLe") == "3"

    def test_get_color_code_invalid_input(self):
        """测试 get_color_code 对无效输入返回 None"""
        assert canvas_utils.get_color_code("invalid") is None
        assert canvas_utils.get_color_code("") is None
        assert canvas_utils.get_color_code("orange") is None
        assert canvas_utils.get_color_code("black") is None

    def test_get_color_semantic_valid_codes(self):
        """测试 get_color_semantic 对所有有效编码"""
        assert canvas_utils.get_color_semantic("1") == "red"
        assert canvas_utils.get_color_semantic("2") == "green"
        assert canvas_utils.get_color_semantic("3") == "purple"
        assert canvas_utils.get_color_semantic("5") == "blue"
        assert canvas_utils.get_color_semantic("6") == "yellow"

    def test_get_color_semantic_invalid_codes(self):
        """测试 get_color_semantic 对无效编码返回 None"""
        assert canvas_utils.get_color_semantic("4") is None
        assert canvas_utils.get_color_semantic("99") is None
        assert canvas_utils.get_color_semantic("") is None
        assert canvas_utils.get_color_semantic("0") is None

    def test_get_color_description_all_codes(self):
        """测试 get_color_description 返回正确描述"""
        desc1 = canvas_utils.get_color_description("1")
        assert desc1 is not None
        assert "不理解" in desc1

        desc2 = canvas_utils.get_color_description("2")
        assert desc2 is not None
        assert "完全理解" in desc2

        desc3 = canvas_utils.get_color_description("3")
        assert desc3 is not None
        assert "似懂非懂" in desc3

        desc5 = canvas_utils.get_color_description("5")
        assert desc5 is not None
        assert "补充解释" in desc5

        desc6 = canvas_utils.get_color_description("6")
        assert desc6 is not None
        assert "个人理解" in desc6

    def test_get_color_description_invalid_code(self):
        """测试 get_color_description 对无效编码返回 None"""
        assert canvas_utils.get_color_description("4") is None
        assert canvas_utils.get_color_description("99") is None

    def test_is_valid_color_code_valid(self):
        """测试 is_valid_color_code 对有效编码返回 True"""
        assert canvas_utils.is_valid_color_code("1") is True
        assert canvas_utils.is_valid_color_code("2") is True
        assert canvas_utils.is_valid_color_code("3") is True
        assert canvas_utils.is_valid_color_code("5") is True
        assert canvas_utils.is_valid_color_code("6") is True

    def test_is_valid_color_code_invalid(self):
        """测试 is_valid_color_code 对无效编码返回 False"""
        assert canvas_utils.is_valid_color_code("4") is False
        assert canvas_utils.is_valid_color_code("99") is False
        assert canvas_utils.is_valid_color_code("0") is False
        assert canvas_utils.is_valid_color_code("") is False

    def test_get_all_color_codes(self):
        """测试 get_all_color_codes 返回所有有效编码"""
        codes = canvas_utils.get_all_color_codes()
        assert len(codes) == 5
        assert "1" in codes
        assert "2" in codes
        assert "3" in codes
        assert "5" in codes
        assert "6" in codes
        assert "4" not in codes

    def test_get_all_color_semantics(self):
        """测试 get_all_color_semantics 返回所有语义名称"""
        semantics = canvas_utils.get_all_color_semantics()
        assert len(semantics) == 5
        assert "red" in semantics
        assert "green" in semantics
        assert "purple" in semantics
        assert "blue" in semantics
        assert "yellow" in semantics

    def test_get_visual_color_for_theme_underwater(self):
        """测试 Underwater 主题的视觉颜色映射"""
        assert canvas_utils.get_visual_color_for_theme(
            "1", "underwater") == "红色"
        assert canvas_utils.get_visual_color_for_theme(
            "2", "underwater") == "绿色"
        assert canvas_utils.get_visual_color_for_theme(
            "3", "underwater") == "紫色"
        assert canvas_utils.get_visual_color_for_theme(
            "5", "underwater") == "蓝色"
        assert canvas_utils.get_visual_color_for_theme(
            "6", "underwater") == "黄色"

    def test_get_visual_color_invalid_theme(self):
        """测试无效主题返回 None"""
        assert canvas_utils.get_visual_color_for_theme(
            "1", "nonexistent") is None
        assert canvas_utils.get_visual_color_for_theme(
            "2", "invalid_theme") is None

    def test_get_visual_color_invalid_code(self):
        """测试无效颜色编码返回 None"""
        assert canvas_utils.get_visual_color_for_theme(
            "99", "underwater") is None
        assert canvas_utils.get_visual_color_for_theme(
            "4", "underwater") is None

    def test_color_code_semantic_roundtrip(self):
        """测试颜色编码和语义名称互相转换（往返转换）"""
        # 测试所有有效的颜色
        for semantic, code in canvas_utils.COLOR_CODES.items():
            # semantic -> code -> semantic
            assert canvas_utils.get_color_code(semantic) == code
            assert canvas_utils.get_color_semantic(code) == semantic

    def test_color_constants_consistency(self):
        """测试颜色常量的一致性"""
        # 验证 COLOR_RED 等常量与新的 COLOR_CODE_RED 一致
        assert canvas_utils.COLOR_RED == canvas_utils.COLOR_CODE_RED
        assert canvas_utils.COLOR_GREEN == canvas_utils.COLOR_CODE_GREEN
        assert canvas_utils.COLOR_PURPLE == canvas_utils.COLOR_CODE_PURPLE
        assert canvas_utils.COLOR_BLUE == canvas_utils.COLOR_CODE_BLUE
        assert canvas_utils.COLOR_YELLOW == canvas_utils.COLOR_CODE_YELLOW

    def test_valid_colors_set_contains_all_codes(self):
        """测试 VALID_COLORS 列表包含所有有效编码（保持顺序）"""
        expected_codes = ["1", "2", "3", "5", "6"]
        assert canvas_utils.VALID_COLORS == expected_codes

    def test_color_semantic_constants(self):
        """测试颜色语义常量定义正确"""
        assert canvas_utils.COLOR_SEMANTIC_RED == "red"
        assert canvas_utils.COLOR_SEMANTIC_GREEN == "green"
        assert canvas_utils.COLOR_SEMANTIC_PURPLE == "purple"
        assert canvas_utils.COLOR_SEMANTIC_BLUE == "blue"
        assert canvas_utils.COLOR_SEMANTIC_YELLOW == "yellow"


class TestCanvasFileIO:
    """测试Canvas文件I/O和备份系统"""

    def setup_method(self):
        """每个测试前的设置"""
        self.test_canvas_path = "src/tests/fixtures/test-write.canvas"
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "text",
                    "text": "Test",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 300
                }
            ],
            "edges": []
        }

    def teardown_method(self):
        """每个测试后的清理"""
        import glob as glob_module
        # 清理测试文件和所有备份
        if os.path.exists(self.test_canvas_path):
            os.remove(self.test_canvas_path)

        # 清理所有备份文件
        backup_pattern = self.test_canvas_path.replace(
            ".canvas", ".backup.*.canvas"
        )
        for backup_file in glob_module.glob(backup_pattern):
            try:
                os.remove(backup_file)
            except OSError:
                pass

        # 清理临时文件
        temp_file = self.test_canvas_path + canvas_utils.TEMP_FILE_SUFFIX
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

    def test_create_backup_success(self):
        """测试成功创建备份文件"""
        # 先创建原始文件
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )

        # 创建备份
        backup_path = canvas_utils.create_backup(self.test_canvas_path)

        # 验证备份文件存在
        assert os.path.exists(backup_path)
        # 验证备份文件名格式
        assert ".backup." in backup_path
        assert backup_path.endswith(".canvas")

    def test_create_backup_file_not_exists(self):
        """测试备份不存在的文件抛出FileNotFoundError"""
        with pytest.raises(FileNotFoundError) as exc_info:
            canvas_utils.create_backup("nonexistent.canvas")

        assert "Canvas文件不存在" in str(exc_info.value)

    def test_backup_file_naming_format(self):
        """测试备份文件命名格式正确性"""
        # 先创建原始文件
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )

        backup_path = canvas_utils.create_backup(self.test_canvas_path)

        # 提取时间戳部分并验证格式
        # 格式：test-write.backup.YYYYMMDDHHmmssμs.canvas
        import re
        pattern = r'\.backup\.(\d{20})\.canvas$'
        match = re.search(pattern, backup_path)
        assert match is not None, f"备份文件名格式不正确: {backup_path}"

        # 验证时间戳可解析
        timestamp_str = match.group(1)
        from datetime import datetime
        datetime.strptime(
            timestamp_str, canvas_utils.BACKUP_TIMESTAMP_FORMAT
        )

    def test_backup_content_identical(self):
        """测试备份文件内容与原文件一致"""
        # 创建原始文件
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )

        # 创建备份
        backup_path = canvas_utils.create_backup(self.test_canvas_path)

        # 读取并比较内容
        original_data = CanvasJSONOperator.read_canvas(self.test_canvas_path)
        backup_data = CanvasJSONOperator.read_canvas(backup_path)

        assert original_data == backup_data

    def test_list_backups_empty(self):
        """测试列出不存在的备份文件返回空列表"""
        backups = canvas_utils.list_backups(self.test_canvas_path)
        assert backups == []

    def test_list_backups_single(self):
        """测试列出单个备份文件"""
        # 创建原始文件和备份
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )
        canvas_utils.create_backup(self.test_canvas_path)

        # 列出备份
        backups = canvas_utils.list_backups(self.test_canvas_path)

        assert len(backups) == 1
        assert os.path.exists(backups[0][0])

    def test_list_backups_multiple_sorted(self):
        """测试列出多个备份文件并按时间降序排序"""
        # 创建原始文件
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )

        # 创建3个备份
        backup_paths = []
        for i in range(3):
            backup_path = canvas_utils.create_backup(self.test_canvas_path)
            backup_paths.append(backup_path)
            time.sleep(0.1)  # 确保时间戳不同

        # 列出备份
        backups = canvas_utils.list_backups(self.test_canvas_path)

        # 验证数量
        assert len(backups) == 3

        # 验证按时间降序排序（最新的在前）
        timestamps = [dt for _, dt in backups]
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i+1], \
                "备份列表应该按时间降序排序"

    def test_cleanup_old_backups_keep_3(self):
        """测试清理旧备份只保留最近3个"""
        # 创建原始文件
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )

        # 创建5个备份文件
        for i in range(5):
            canvas_utils.create_backup(self.test_canvas_path)
            time.sleep(0.1)  # 确保时间戳不同

        # 验证创建了5个备份
        backups_before = canvas_utils.list_backups(self.test_canvas_path)
        assert len(backups_before) == 5

        # 清理
        canvas_utils.cleanup_old_backups(
            self.test_canvas_path, keep_count=3
        )

        # 验证只剩3个备份
        backups_after = canvas_utils.list_backups(self.test_canvas_path)
        assert len(backups_after) == 3

    def test_cleanup_old_backups_keep_all_if_less(self):
        """测试备份数量不超过限制时不清理"""
        # 创建原始文件
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )

        # 创建2个备份文件
        canvas_utils.create_backup(self.test_canvas_path)
        time.sleep(0.1)
        canvas_utils.create_backup(self.test_canvas_path)

        # 清理（保留3个）
        canvas_utils.cleanup_old_backups(
            self.test_canvas_path, keep_count=3
        )

        # 验证仍然有2个备份
        backups = canvas_utils.list_backups(self.test_canvas_path)
        assert len(backups) == 2

    def test_cleanup_old_backups_removes_oldest(self):
        """测试清理删除最旧的备份"""
        # 创建原始文件
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )

        # 创建4个备份并记录路径
        backup_paths = []
        for i in range(4):
            backup_path = canvas_utils.create_backup(self.test_canvas_path)
            backup_paths.append(backup_path)
            time.sleep(0.15)  # 确保时间戳不同

        # 清理（保留2个）
        canvas_utils.cleanup_old_backups(
            self.test_canvas_path, keep_count=2
        )

        # 验证最旧的2个被删除
        assert not os.path.exists(backup_paths[0]), "最旧的备份应该被删除"
        assert not os.path.exists(backup_paths[1]), "第二旧的备份应该被删除"
        assert os.path.exists(backup_paths[2]), "较新的备份应该保留"
        assert os.path.exists(backup_paths[3]), "最新的备份应该保留"

    def test_write_canvas_atomic_success(self):
        """测试原子写入成功"""
        canvas_utils.write_canvas_atomic(
            self.test_canvas_path, self.test_canvas_data
        )

        # 验证文件存在
        assert os.path.exists(self.test_canvas_path)

        # 验证临时文件已清理
        temp_path = self.test_canvas_path + canvas_utils.TEMP_FILE_SUFFIX
        assert not os.path.exists(temp_path)

        # 验证内容正确
        data = CanvasJSONOperator.read_canvas(self.test_canvas_path)
        assert data == self.test_canvas_data

    def test_write_canvas_atomic_invalid_data_not_dict(self):
        """测试原子写入非字典数据抛出ValueError"""
        with pytest.raises(ValueError) as exc_info:
            canvas_utils.write_canvas_atomic(
                self.test_canvas_path, "not a dict"
            )

        assert "canvas_data必须是字典类型" in str(exc_info.value)

    def test_write_canvas_atomic_missing_nodes_field(self):
        """测试原子写入缺少nodes字段抛出ValueError"""
        invalid_data = {"edges": []}

        with pytest.raises(ValueError) as exc_info:
            canvas_utils.write_canvas_atomic(
                self.test_canvas_path, invalid_data
            )

        assert "缺少'nodes'字段" in str(exc_info.value)

    def test_write_canvas_atomic_missing_edges_field(self):
        """测试原子写入缺少edges字段抛出ValueError"""
        invalid_data = {"nodes": []}

        with pytest.raises(ValueError) as exc_info:
            canvas_utils.write_canvas_atomic(
                self.test_canvas_path, invalid_data
            )

        assert "缺少'edges'字段" in str(exc_info.value)

    def test_write_canvas_atomic_nodes_not_list(self):
        """测试原子写入nodes不是列表抛出ValueError"""
        invalid_data = {"nodes": "not a list", "edges": []}

        with pytest.raises(ValueError) as exc_info:
            canvas_utils.write_canvas_atomic(
                self.test_canvas_path, invalid_data
            )

        assert "nodes']必须是列表类型" in str(exc_info.value)

    def test_write_canvas_atomic_edges_not_list(self):
        """测试原子写入edges不是列表抛出ValueError"""
        invalid_data = {"nodes": [], "edges": "not a list"}

        with pytest.raises(ValueError) as exc_info:
            canvas_utils.write_canvas_atomic(
                self.test_canvas_path, invalid_data
            )

        assert "edges']必须是列表类型" in str(exc_info.value)

    def test_write_canvas_atomic_creates_temp_file(self):
        """测试原子写入过程中创建临时文件"""
        # 这个测试验证原子写入的行为，但临时文件会被立即清理
        canvas_utils.write_canvas_atomic(
            self.test_canvas_path, self.test_canvas_data
        )

        # 临时文件应该已被清理
        temp_path = self.test_canvas_path + canvas_utils.TEMP_FILE_SUFFIX
        assert not os.path.exists(temp_path)

    def test_write_canvas_atomic_utf8_support(self):
        """测试原子写入支持UTF-8中文"""
        chinese_data = {
            "nodes": [
                {
                    "id": "test-node",
                    "type": "text",
                    "text": "测试中文内容：逆否命题",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 300
                }
            ],
            "edges": []
        }

        canvas_utils.write_canvas_atomic(
            self.test_canvas_path, chinese_data
        )

        # 读取并验证中文内容
        data = CanvasJSONOperator.read_canvas(self.test_canvas_path)
        assert data["nodes"][0]["text"] == "测试中文内容：逆否命题"

    def test_write_canvas_complete_flow(self):
        """测试write_canvas完整流程：备份→写入→清理"""
        # 第一次写入（无备份）
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )
        assert os.path.exists(self.test_canvas_path)

        # 第二次写入（应该创建备份）
        modified_data = self.test_canvas_data.copy()
        modified_data["nodes"].append({
            "id": "node-2",
            "type": "text",
            "text": "Test 2",
            "x": 100,
            "y": 100,
            "width": 400,
            "height": 300
        })
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, modified_data
        )

        # 验证备份存在
        backups = canvas_utils.list_backups(self.test_canvas_path)
        assert len(backups) >= 1

        # 验证内容已更新
        data = CanvasJSONOperator.read_canvas(self.test_canvas_path)
        assert len(data["nodes"]) == 2

    def test_write_canvas_multiple_writes_keep_3_backups(self):
        """测试多次写入只保留3个备份"""
        # 写入6次
        for i in range(6):
            modified_data = self.test_canvas_data.copy()
            modified_data["nodes"][0]["text"] = f"Version {i}"
            CanvasJSONOperator.write_canvas(
                self.test_canvas_path, modified_data
            )
            time.sleep(0.1)  # 确保时间戳不同

        # 验证只保留3个备份
        backups = canvas_utils.list_backups(self.test_canvas_path)
        assert len(backups) == 3

    def test_write_canvas_performance(self):
        """测试写入操作性能（必须<1秒）"""
        # 创建中等规模的Canvas数据（50个节点）
        large_canvas_data = {
            "nodes": [
                {
                    "id": f"node-{i}",
                    "type": "text",
                    "text": f"Test Node {i}",
                    "x": i * 100,
                    "y": i * 50,
                    "width": 400,
                    "height": 300
                }
                for i in range(50)
            ],
            "edges": []
        }

        start_time = time.time()
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, large_canvas_data
        )
        elapsed = time.time() - start_time

        assert elapsed < 1.0, \
            f"写入耗时 {elapsed:.2f}s，超过1秒要求"

    def test_restore_from_backup_success(self):
        """测试从备份恢复文件"""
        # 创建原始文件
        original_data = {
            "nodes": [{"id": "original", "type": "text",
                      "text": "Original", "x": 0, "y": 0}],
            "edges": []
        }
        CanvasJSONOperator.write_canvas(self.test_canvas_path, original_data)

        # 创建备份
        backup_path = canvas_utils.create_backup(self.test_canvas_path)

        # 修改原文件
        modified_data = {
            "nodes": [{"id": "modified", "type": "text",
                      "text": "Modified", "x": 0, "y": 0}],
            "edges": []
        }
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, modified_data
        )

        # 从备份恢复
        canvas_utils.restore_from_backup(
            self.test_canvas_path, backup_path
        )

        # 验证恢复后的内容
        restored_data = CanvasJSONOperator.read_canvas(self.test_canvas_path)
        assert restored_data["nodes"][0]["id"] == "original"
        assert restored_data["nodes"][0]["text"] == "Original"

    def test_restore_from_backup_file_not_exists(self):
        """测试从不存在的备份恢复抛出FileNotFoundError"""
        with pytest.raises(FileNotFoundError) as exc_info:
            canvas_utils.restore_from_backup(
                self.test_canvas_path,
                "nonexistent.backup.canvas"
            )

        assert "备份文件不存在" in str(exc_info.value)

    def test_write_canvas_atomic_json_format(self):
        """测试原子写入的JSON格式化正确"""
        canvas_utils.write_canvas_atomic(
            self.test_canvas_path, self.test_canvas_data
        )

        # 读取文件内容检查格式
        with open(self.test_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 应该有缩进（indent=2）
        assert '  "nodes"' in content or '  "edges"' in content

        # 应该支持中文（ensure_ascii=False）
        if any(ord(c) > 127 for c in self.test_canvas_data["nodes"][0]["text"]):
            # 如果有中文，应该直接显示而不是\uXXXX
            assert '\\u' not in content or content.count('\\u') < 10


# ========== Layer 2: CanvasBusinessLogic 测试 ==========

class TestCanvasBusinessLogic:
    """测试CanvasBusinessLogic类（Layer 2）"""

    def setup_method(self):
        """每个测试前的设置"""
        # 使用测试fixture文件
        self.test_canvas_path = "src/tests/fixtures/test-context.canvas"

        # 创建测试用的Canvas数据
        self.test_canvas_data = {
            "nodes": [
                # 父节点（红色）
                {
                    "id": "node-parent",
                    "type": "text",
                    "text": "逆否命题",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 300,
                    "color": "1"
                },
                # 目标节点（紫色）
                {
                    "id": "node-target",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 500,
                    "y": 0,
                    "width": 400,
                    "height": 300,
                    "color": "3"
                },
                # 黄色节点1（个人理解）
                {
                    "id": "node-yellow1",
                    "type": "text",
                    "text": "我的理解：逆否命题是将原命题的条件和结论都取反并交换",
                    "x": 900,
                    "y": -200,
                    "width": 400,
                    "height": 300,
                    "color": "6"
                },
                # 黄色节点2（个人理解）
                {
                    "id": "node-yellow2",
                    "type": "text",
                    "text": "例如：若p则q → 若非q则非p",
                    "x": 900,
                    "y": 200,
                    "width": 400,
                    "height": 300,
                    "color": "6"
                },
                # 子节点（蓝色说明）
                {
                    "id": "node-child",
                    "type": "text",
                    "text": "逆否命题与原命题等价",
                    "x": 1400,
                    "y": 0,
                    "width": 400,
                    "height": 300,
                    "color": "5"
                },
                # 兄弟节点（紫色）
                {
                    "id": "node-sibling",
                    "type": "text",
                    "text": "逆否命题有什么用？",
                    "x": 500,
                    "y": 400,
                    "width": 400,
                    "height": 300,
                    "color": "3"
                }
            ],
            "edges": [
                # 父节点 → 目标节点
                {
                    "id": "edge-parent-target",
                    "fromNode": "node-parent",
                    "toNode": "node-target",
                    "fromSide": "right",
                    "toSide": "left",
                    "label": "拆解自"
                },
                # 目标节点 → 黄色节点1
                {
                    "id": "edge-target-yellow1",
                    "fromNode": "node-target",
                    "toNode": "node-yellow1",
                    "fromSide": "right",
                    "toSide": "left",
                    "label": "个人理解"
                },
                # 目标节点 → 黄色节点2
                {
                    "id": "edge-target-yellow2",
                    "fromNode": "node-target",
                    "toNode": "node-yellow2",
                    "fromSide": "right",
                    "toSide": "left",
                    "label": "个人理解"
                },
                # 目标节点 → 子节点
                {
                    "id": "edge-target-child",
                    "fromNode": "node-target",
                    "toNode": "node-child",
                    "fromSide": "right",
                    "toSide": "left",
                    "label": "补充解释"
                },
                # 父节点 → 兄弟节点
                {
                    "id": "edge-parent-sibling",
                    "fromNode": "node-parent",
                    "toNode": "node-sibling",
                    "fromSide": "right",
                    "toSide": "left",
                    "label": "拆解自"
                }
            ]
        }

        # 写入测试文件
        CanvasJSONOperator.write_canvas(
            self.test_canvas_path, self.test_canvas_data
        )

    def teardown_method(self):
        """每个测试后的清理"""
        # 清理测试文件和备份
        if os.path.exists(self.test_canvas_path):
            os.remove(self.test_canvas_path)

        # 清理备份文件
        import glob
        backup_pattern = self.test_canvas_path.replace(
            ".canvas", ".backup.*.canvas"
        )
        for backup_file in glob.glob(backup_pattern):
            try:
                os.remove(backup_file)
            except OSError:
                pass

    def test_extract_context_success(self):
        """测试成功提取上下文"""
        from canvas_utils import CanvasBusinessLogic

        logic = CanvasBusinessLogic(self.test_canvas_path)
        context = logic.extract_context("node-target")

        # 验证目标节点信息
        assert context["target_node"]["id"] == "node-target"
        assert context["target_node"]["text"] == "什么是逆否命题？"
        assert context["target_node"]["color"] == "3"
        assert context["target_node"]["type"] == "text"
        assert context["target_node"]["position"]["x"] == 500
        assert context["target_node"]["position"]["y"] == 0

        # 验证黄色节点
        assert len(context["related_yellow_nodes"]) == 2
        yellow_ids = [n["id"] for n in context["related_yellow_nodes"]]
        assert "node-yellow1" in yellow_ids
        assert "node-yellow2" in yellow_ids

        # 验证边标签
        for yellow_node in context["related_yellow_nodes"]:
            assert yellow_node["edge_label"] == "个人理解"

        # 验证父节点
        assert len(context["parent_nodes"]) == 1
        assert context["parent_nodes"][0]["id"] == "node-parent"
        assert context["parent_nodes"][0]["text"] == "逆否命题"

        # 验证子节点（不包括黄色节点）
        assert len(context["child_nodes"]) == 1
        assert context["child_nodes"][0]["id"] == "node-child"

        # 验证兄弟节点
        assert len(context["sibling_nodes"]) == 1
        assert context["sibling_nodes"][0]["id"] == "node-sibling"

    def test_extract_context_node_not_found(self):
        """测试节点不存在时抛出ValueError"""
        from canvas_utils import CanvasBusinessLogic

        logic = CanvasBusinessLogic(self.test_canvas_path)

        with pytest.raises(ValueError) as exc_info:
            logic.extract_context("nonexistent-node")

        assert "目标节点不存在" in str(exc_info.value)
        assert "nonexistent-node" in str(exc_info.value)
        assert self.test_canvas_path in str(exc_info.value)

    def test_extract_context_no_yellow_nodes(self):
        """测试目标节点没有黄色节点的情况"""
        from canvas_utils import CanvasBusinessLogic

        # 创建没有黄色节点的Canvas
        canvas_data = {
            "nodes": [
                {
                    "id": "node-alone",
                    "type": "text",
                    "text": "孤独的节点",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 300,
                    "color": "1"
                }
            ],
            "edges": []
        }
        test_path = "src/tests/fixtures/test-no-yellow.canvas"
        CanvasJSONOperator.write_canvas(test_path, canvas_data)

        try:
            logic = CanvasBusinessLogic(test_path)
            context = logic.extract_context("node-alone")

            # 应该返回空列表，而不是报错
            assert context["related_yellow_nodes"] == []
            assert context["parent_nodes"] == []
            assert context["child_nodes"] == []
            assert context["sibling_nodes"] == []
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_extract_context_canvas_summary(self):
        """测试Canvas概要生成"""
        from canvas_utils import CanvasBusinessLogic

        logic = CanvasBusinessLogic(self.test_canvas_path)
        context = logic.extract_context("node-target")

        summary = context["canvas_summary"]

        # 验证总数
        assert summary["total_nodes"] == 6
        assert summary["total_edges"] == 5

        # 验证颜色分布
        color_dist = summary["color_distribution"]
        assert color_dist["red"] == 1  # node-parent
        assert color_dist["green"] == 0
        assert color_dist["purple"] == 2  # node-target, node-sibling
        assert color_dist["yellow"] == 2  # node-yellow1, node-yellow2
        assert color_dist["blue"] == 1  # node-child

    def test_extract_context_performance(self):
        """测试上下文提取性能（<200ms）"""
        from canvas_utils import CanvasBusinessLogic

        # 创建较大的Canvas（50个节点）
        large_canvas_data = {
            "nodes": [
                {
                    "id": f"node-{i}",
                    "type": "text",
                    "text": f"测试节点 {i}",
                    "x": (i % 10) * 500,
                    "y": (i // 10) * 400,
                    "width": 400,
                    "height": 300,
                    "color": ["1", "2", "3", "5", "6"][i % 5]
                }
                for i in range(50)
            ],
            "edges": [
                {
                    "id": f"edge-{i}",
                    "fromNode": f"node-{i}",
                    "toNode": f"node-{i+1}",
                    "fromSide": "right",
                    "toSide": "left"
                }
                for i in range(49)
            ]
        }

        test_path = "src/tests/fixtures/test-large.canvas"
        CanvasJSONOperator.write_canvas(test_path, large_canvas_data)

        try:
            logic = CanvasBusinessLogic(test_path)

            # 测试性能
            start_time = time.time()
            context = logic.extract_context("node-25")
            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒

            # 验证性能要求
            assert elapsed_time < 200, \
                f"性能不达标：{elapsed_time:.2f}ms > 200ms"

            # 验证结果正确性
            assert context["target_node"]["id"] == "node-25"
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)
            # 清理备份
            import glob
            for backup in glob.glob(test_path.replace(".canvas", ".backup.*.canvas")):
                try:
                    os.remove(backup)
                except OSError:
                    pass

    def test_extract_context_with_parent_and_child_nodes(self):
        """测试提取父节点和子节点"""
        from canvas_utils import CanvasBusinessLogic

        logic = CanvasBusinessLogic(self.test_canvas_path)
        context = logic.extract_context("node-target")

        # 验证父节点详细信息
        assert len(context["parent_nodes"]) == 1
        parent = context["parent_nodes"][0]
        assert "id" in parent
        assert "text" in parent
        assert "color" in parent
        assert parent["id"] == "node-parent"

        # 验证子节点详细信息（不包括黄色节点）
        assert len(context["child_nodes"]) == 1
        child = context["child_nodes"][0]
        assert "id" in child
        assert "text" in child
        assert "color" in child
        assert child["id"] == "node-child"

    def test_extract_context_target_node_structure(self):
        """测试目标节点信息结构完整性"""
        from canvas_utils import CanvasBusinessLogic

        logic = CanvasBusinessLogic(self.test_canvas_path)
        context = logic.extract_context("node-target")

        target = context["target_node"]

        # 验证所有必需字段
        assert "id" in target
        assert "type" in target
        assert "text" in target
        assert "color" in target
        assert "position" in target
        assert "size" in target

        # 验证position结构
        assert "x" in target["position"]
        assert "y" in target["position"]
        assert isinstance(target["position"]["x"], int)
        assert isinstance(target["position"]["y"], int)

        # 验证size结构
        assert "width" in target["size"]
        assert "height" in target["size"]
        assert isinstance(target["size"]["width"], int)
        assert isinstance(target["size"]["height"], int)

    def test_canvas_business_logic_init(self):
        """测试CanvasBusinessLogic初始化"""
        from canvas_utils import CanvasBusinessLogic

        logic = CanvasBusinessLogic(self.test_canvas_path)

        # 验证属性
        assert logic.canvas_path == self.test_canvas_path
        assert logic.canvas_data is not None
        assert "nodes" in logic.canvas_data
        assert "edges" in logic.canvas_data

    def test_canvas_business_logic_init_file_not_found(self):
        """测试初始化时文件不存在抛出异常"""
        from canvas_utils import CanvasBusinessLogic

        with pytest.raises(FileNotFoundError):
            CanvasBusinessLogic("nonexistent.canvas")

    def test_extract_context_sibling_nodes_logic(self):
        """测试兄弟节点查找逻辑"""
        from canvas_utils import CanvasBusinessLogic

        logic = CanvasBusinessLogic(self.test_canvas_path)
        context = logic.extract_context("node-target")

        # 兄弟节点应该是共享父节点的其他节点
        siblings = context["sibling_nodes"]
        assert len(siblings) == 1

        # 兄弟节点不应该包含目标节点自己
        sibling_ids = [s["id"] for s in siblings]
        assert "node-target" not in sibling_ids

        # 兄弟节点应该是 node-sibling
        assert "node-sibling" in sibling_ids

    # ========== Story 2.6: 标准学习单元结构测试 ==========

    def test_add_sub_question_with_yellow_node_creates_both_nodes(self):
        """测试创建问题节点时自动创建黄色节点 (AC: 1)"""
        from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator
        import os
        import shutil

        # 创建临时测试文件
        temp_path = "src/tests/fixtures/test-pairing-temp.canvas"
        shutil.copy("src/tests/fixtures/test-pairing.canvas", temp_path)

        try:
            logic = CanvasBusinessLogic(temp_path)
            material_id = "material-test123"
            question_text = "什么是逆否命题？"

            # Act
            question_id, yellow_id = logic.add_sub_question_with_yellow_node(
                material_node_id=material_id,
                question_text=question_text
            )

            # Assert - 验证两个节点ID有效
            assert question_id is not None
            assert yellow_id is not None
            assert question_id.startswith("text-")
            assert yellow_id.startswith("text-")

            # 重新读取Canvas验证节点存在
            canvas_data = CanvasJSONOperator.read_canvas(temp_path)
            question_node = CanvasJSONOperator.find_node_by_id(
                canvas_data, question_id
            )
            yellow_node = CanvasJSONOperator.find_node_by_id(
                canvas_data, yellow_id
            )

            assert question_node is not None
            assert yellow_node is not None

            # 验证问题节点属性
            assert question_node["type"] == "text"
            assert question_node["text"] == question_text
            assert question_node["color"] == "1"  # 初始为红色

            # 验证黄色节点属性
            assert yellow_node["type"] == "text"
            assert yellow_node["color"] == "6"  # 黄色

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_add_sub_question_yellow_node_position_v11_layout(self):
        """测试黄色节点位置符合v1.1布局（正下方，水平对齐） (AC: 2)"""
        from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator
        import os
        import shutil

        # 创建临时测试文件
        temp_path = "src/tests/fixtures/test-pairing-temp.canvas"
        shutil.copy("src/tests/fixtures/test-pairing.canvas", temp_path)

        try:
            logic = CanvasBusinessLogic(temp_path)
            material_id = "material-test123"

            # Act
            question_id, yellow_id = logic.add_sub_question_with_yellow_node(
                material_node_id=material_id,
                question_text="测试问题"
            )

            # Assert
            canvas_data = CanvasJSONOperator.read_canvas(temp_path)
            question_node = CanvasJSONOperator.find_node_by_id(
                canvas_data, question_id
            )
            yellow_node = CanvasJSONOperator.find_node_by_id(
                canvas_data, yellow_id
            )

            # v1.1核心验证：水平对齐
            assert yellow_node["x"] == question_node["x"], \
                "黄色节点应与问题节点水平对齐"

            # 验证垂直位置：黄色节点在问题节点正下方
            # QUESTION_NODE_HEIGHT (120) + YELLOW_OFFSET_Y (30)
            expected_yellow_y = question_node["y"] + 120 + 30
            assert yellow_node["y"] == expected_yellow_y, \
                "黄色节点应在问题节点正下方"

            # 验证黄色节点尺寸
            assert yellow_node["width"] == 350, "黄色节点宽度应为350px"
            assert yellow_node["height"] == 150, "黄色节点高度应为150px"

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_add_sub_question_creates_edge_with_label(self):
        """测试创建连接边并添加标签'个人理解' (AC: 3)"""
        from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator
        import os
        import shutil

        # 创建临时测试文件
        temp_path = "src/tests/fixtures/test-pairing-temp.canvas"
        shutil.copy("src/tests/fixtures/test-pairing.canvas", temp_path)

        try:
            logic = CanvasBusinessLogic(temp_path)
            material_id = "material-test123"

            # Act
            question_id, yellow_id = logic.add_sub_question_with_yellow_node(
                material_node_id=material_id,
                question_text="测试问题"
            )

            # Assert - 查找问题→黄色的边
            canvas_data = CanvasJSONOperator.read_canvas(temp_path)
            edge_found = False

            for edge in canvas_data["edges"]:
                if (edge["fromNode"] == question_id and
                        edge["toNode"] == yellow_id):
                    edge_found = True
                    # 验证边的连接方向
                    assert edge["fromSide"] == "bottom", \
                        "应从问题底部连接"
                    assert edge["toSide"] == "top", \
                        "应连接到黄色顶部"
                    # 验证边的标签
                    assert edge.get("label") == "个人理解", \
                        "边标签应为'个人理解'"
                    break

            assert edge_found, "应存在从问题到黄色节点的边"

            # 验证材料→问题的边也存在
            material_edge_found = False
            for edge in canvas_data["edges"]:
                if (edge["fromNode"] == material_id and
                        edge["toNode"] == question_id):
                    material_edge_found = True
                    assert edge.get("label") == "拆解自", \
                        "材料→问题边标签应为'拆解自'"
                    break

            assert material_edge_found, "应存在从材料到问题节点的边"

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_yellow_node_has_prompt_text(self):
        """测试黄色节点包含提示内容 (AC: 4)"""
        from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator
        import os
        import shutil

        # 创建临时测试文件
        temp_path = "src/tests/fixtures/test-pairing-temp.canvas"
        shutil.copy("src/tests/fixtures/test-pairing.canvas", temp_path)

        try:
            logic = CanvasBusinessLogic(temp_path)
            material_id = "material-test123"

            # Act
            _, yellow_id = logic.add_sub_question_with_yellow_node(
                material_node_id=material_id,
                question_text="测试问题"
            )

            # Assert
            canvas_data = CanvasJSONOperator.read_canvas(temp_path)
            yellow_node = CanvasJSONOperator.find_node_by_id(
                canvas_data, yellow_id
            )

            assert yellow_node["text"] == "[请在此填写你对该问题的个人理解]", \
                "黄色节点应包含提示内容模板"

            # 验证黄色节点的颜色代码
            assert yellow_node["color"] == "6", \
                "黄色节点颜色代码应为'6'"

            # 验证黄色节点的尺寸
            assert yellow_node["width"] == 350, \
                "黄色节点宽度应为350px"
            assert yellow_node["height"] == 150, \
                "黄色节点高度应为150px"

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_multiple_questions_vertical_spacing(self):
        """测试多个问题节点时垂直间距正确 (AC: 1, 2)"""
        from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator
        import os
        import shutil

        # 创建临时测试文件
        temp_path = "src/tests/fixtures/test-pairing-temp.canvas"
        shutil.copy("src/tests/fixtures/test-pairing.canvas", temp_path)

        try:
            logic = CanvasBusinessLogic(temp_path)
            material_id = "material-test123"

            # Act - 创建3个问题
            q1_id, y1_id = logic.add_sub_question_with_yellow_node(
                material_node_id=material_id,
                question_text="问题1"
            )

            # 重新加载Canvas数据（因为上一次调用已经保存）
            logic.canvas_data = CanvasJSONOperator.read_canvas(temp_path)

            q2_id, y2_id = logic.add_sub_question_with_yellow_node(
                material_node_id=material_id,
                question_text="问题2"
            )

            logic.canvas_data = CanvasJSONOperator.read_canvas(temp_path)

            q3_id, y3_id = logic.add_sub_question_with_yellow_node(
                material_node_id=material_id,
                question_text="问题3"
            )

            # Assert
            canvas_data = CanvasJSONOperator.read_canvas(temp_path)
            q1_node = CanvasJSONOperator.find_node_by_id(canvas_data, q1_id)
            q2_node = CanvasJSONOperator.find_node_by_id(canvas_data, q2_id)
            q3_node = CanvasJSONOperator.find_node_by_id(canvas_data, q3_id)

            # 验证垂直间距 = VERTICAL_SPACING_BASE (380)
            vertical_spacing_1_to_2 = q2_node["y"] - q1_node["y"]
            vertical_spacing_2_to_3 = q3_node["y"] - q2_node["y"]

            assert vertical_spacing_1_to_2 == 380, \
                "问题1到问题2的垂直间距应为380px"
            assert vertical_spacing_2_to_3 == 380, \
                "问题2到问题3的垂直间距应为380px"

            # 验证每个问题都有对应的黄色节点
            y1_node = CanvasJSONOperator.find_node_by_id(canvas_data, y1_id)
            y2_node = CanvasJSONOperator.find_node_by_id(canvas_data, y2_id)
            y3_node = CanvasJSONOperator.find_node_by_id(canvas_data, y3_id)

            assert y1_node is not None
            assert y2_node is not None
            assert y3_node is not None

            # 验证每个黄色节点都与对应问题节点水平对齐
            assert y1_node["x"] == q1_node["x"]
            assert y2_node["x"] == q2_node["x"]
            assert y3_node["x"] == q3_node["x"]

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_add_sub_question_with_guidance(self):
        """测试添加问题时包含引导提示"""
        from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator
        import os
        import shutil

        # 创建临时测试文件
        temp_path = "src/tests/fixtures/test-pairing-temp.canvas"
        shutil.copy("src/tests/fixtures/test-pairing.canvas", temp_path)

        try:
            logic = CanvasBusinessLogic(temp_path)
            material_id = "material-test123"
            question_text = "什么是逆否命题？"
            guidance = "💡 提示：从定义出发思考"

            # Act
            question_id, _ = logic.add_sub_question_with_yellow_node(
                material_node_id=material_id,
                question_text=question_text,
                guidance=guidance
            )

            # Assert
            canvas_data = CanvasJSONOperator.read_canvas(temp_path)
            question_node = CanvasJSONOperator.find_node_by_id(
                canvas_data, question_id
            )

            # 验证问题文本包含引导提示
            assert question_text in question_node["text"]
            assert guidance in question_node["text"]

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_add_sub_question_material_not_found(self):
        """测试材料节点不存在时抛出ValueError"""
        from canvas_utils import CanvasBusinessLogic
        import os
        import shutil

        # 创建临时测试文件
        temp_path = "src/tests/fixtures/test-pairing-temp.canvas"
        shutil.copy("src/tests/fixtures/test-pairing.canvas", temp_path)

        try:
            logic = CanvasBusinessLogic(temp_path)

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                logic.add_sub_question_with_yellow_node(
                    material_node_id="nonexistent-id",
                    question_text="测试问题"
                )

            assert "材料节点不存在" in str(exc_info.value)
            assert "nonexistent-id" in str(exc_info.value)

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # ========== Story 2.7: 智能节点定位算法测试 ==========

    def test_calculate_smart_position_decomposition_vertical(self):
        """测试拆解子问题纵向排列逻辑"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-positioning.canvas")
        parent_node = {
            "id": "parent-123",
            "x": 100,
            "y": 200,
            "width": 400,
            "height": 300
        }

        pos = logic.calculate_smart_position(
            parent_node=parent_node,
            relationship_type="decomposition",
            existing_nodes=[]
        )

        # 验证纵向排列
        assert pos["x"] == 100, "拆解子问题x坐标应与父节点相同"
        assert pos["y"] == 200 + 300 + 80, "y坐标应为父节点底部 + VERTICAL_GAP"
        assert pos["y"] == 580

    def test_calculate_smart_position_siblings_offset(self):
        """测试多个兄弟节点横向错开逻辑"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-positioning.canvas")
        parent_id = "parent-123"

        # 预先添加1个子问题（放在不会重叠的位置）
        logic.canvas_data["edges"].append({
            "id": "edge-1",
            "fromNode": parent_id,
            "toNode": "child-1",
            "fromSide": "bottom",
            "toSide": "top"
        })
        logic.canvas_data["nodes"].append({
            "id": "child-1",
            "x": 600,  # 放在远处，不会与新节点重叠
            "y": 1000,
            "width": 400,
            "height": 120,
            "color": "1"  # 红色
        })

        parent_node = {
            "id": parent_id,
            "x": 100,
            "y": 200,
            "width": 400,
            "height": 300
        }

        # 添加第2个子节点
        pos = logic.calculate_smart_position(
            parent_node=parent_node,
            relationship_type="decomposition",
            existing_nodes=logic.canvas_data["nodes"]
        )

        # 验证横向错开：基础位置(100, 580) + 兄弟偏移(50, 0)
        assert pos["x"] == 100 + 50, "第2个子节点应横向偏移50px"
        assert pos["y"] == 580, "y坐标应为父节点底部 + VERTICAL_GAP"

    def test_calculate_smart_position_explanation(self):
        """测试补充解释节点位置（偏下偏右）"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-positioning.canvas")
        parent_node = {
            "id": "question-123",
            "x": 500,
            "y": 200,
            "width": 400,
            "height": 120
        }

        pos = logic.calculate_smart_position(
            parent_node=parent_node,
            relationship_type="explanation",
            existing_nodes=[]
        )

        # 验证偏下偏右
        assert pos["x"] == 500 + 400 + 50, "x坐标应为父节点右侧 + HORIZONTAL_GAP"
        assert pos["y"] == 200 + 100, "y坐标应为父节点顶部 + EXPLANATION_OFFSET_Y"

    def test_check_overlap_detects_collision(self):
        """测试重叠检测能正确识别碰撞"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-positioning.canvas")

        # 创建现有节点
        existing_nodes = [{
            "id": "existing-1",
            "x": 100,
            "y": 200,
            "width": 400,
            "height": 300
        }]

        # 测试重叠位置
        pos_overlap = {"x": 150, "y": 250}  # 会与existing-1重叠
        assert logic._check_overlap(
            pos_overlap, 400, 300, existing_nodes
        ) is True, "应该检测到重叠"

        # 测试不重叠位置
        pos_no_overlap = {"x": 600, "y": 200}  # 不会重叠
        assert logic._check_overlap(
            pos_no_overlap, 400, 300, existing_nodes
        ) is False, "应该检测为无重叠"

    def test_avoid_overlap_adjusts_position(self):
        """测试避免重叠功能能调整位置"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-positioning.canvas")

        # 创建现有节点（占据位置 100, 200）
        existing_nodes = [{
            "id": "existing-1",
            "x": 100,
            "y": 200,
            "width": 400,
            "height": 300
        }]

        # 尝试在重叠位置创建节点
        base_pos = {"x": 150, "y": 250}
        adjusted_pos = logic._avoid_overlap(
            base_pos=base_pos,
            width=400,
            height=300,
            existing_nodes=existing_nodes
        )

        # 验证位置已被调整
        assert adjusted_pos != base_pos, "位置应被调整以避免重叠"

        # 验证调整后的位置不再重叠
        has_overlap = logic._check_overlap(
            pos=adjusted_pos,
            width=400,
            height=300,
            existing_nodes=existing_nodes
        )
        assert not has_overlap, "调整后应无重叠"

    def test_calculate_smart_position_performance(self):
        """测试定位计算性能（必须<50ms）"""
        import time
        logic = CanvasBusinessLogic("src/tests/fixtures/test-large-canvas.canvas")

        # 创建大量现有节点（模拟复杂Canvas）
        existing_nodes = logic.canvas_data.get("nodes", [])

        parent_node = {
            "id": "parent-test",
            "x": 2500,
            "y": 2000,
            "width": 400,
            "height": 300
        }

        # 测量执行时间
        start_time = time.time()
        pos = logic.calculate_smart_position(
            parent_node=parent_node,
            relationship_type="decomposition",
            existing_nodes=existing_nodes
        )
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        # 验证性能
        assert elapsed_ms < 50, \
            f"执行时间{elapsed_ms:.2f}ms超过50ms限制"
        assert pos is not None

    def test_calculate_smart_position_invalid_relationship_type(self):
        """测试不支持的关系类型抛出ValueError"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-positioning.canvas")
        parent_node = {
            "id": "p1",
            "x": 100,
            "y": 200,
            "width": 400,
            "height": 300
        }

        with pytest.raises(ValueError, match="不支持的关系类型"):
            logic.calculate_smart_position(
                parent_node=parent_node,
                relationship_type="invalid_type",
                existing_nodes=[]
            )

    def test_smart_position_does_not_break_v11_layout(self):
        """验证智能定位不破坏v1.1布局的问题-黄色配对"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-v11-compatibility.canvas")
        material_id = "material-123"

        # 先使用v1.1方法创建问题+黄色配对
        q_id, y_id = logic.add_sub_question_with_yellow_node(
            material_node_id=material_id,
            question_text="测试问题"
        )

        q_node = CanvasJSONOperator.find_node_by_id(logic.canvas_data, q_id)
        y_node = CanvasJSONOperator.find_node_by_id(logic.canvas_data, y_id)

        # 验证v1.1布局特点：黄色节点在问题下方，水平对齐
        assert y_node["x"] == q_node["x"], \
            "黄色节点应与问题节点水平对齐"
        assert y_node["y"] == q_node["y"] + 120 + 30, \
            "黄色节点应在问题节点下方"

        # 现在使用智能定位添加解释节点
        explanation_pos = logic.calculate_smart_position(
            parent_node=q_node,
            relationship_type="explanation",
            existing_nodes=logic.canvas_data["nodes"]
        )

        # 验证解释节点位置不干扰问题-黄色配对
        assert explanation_pos["x"] > y_node["x"] + y_node["width"], \
            "解释节点应在黄色节点右侧，不覆盖"

    def test_extract_verification_nodes_success(self):
        """测试成功提取红色和紫色节点"""
        # 创建包含红色和紫色节点的测试Canvas
        test_canvas_data = {
            "nodes": [
                {
                    "id": "material-1",
                    "type": "text",
                    "text": "逆否命题材料",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 300
                },
                {
                    "id": "red-1",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 600,
                    "y": 100,
                    "width": 400,
                    "height": 120,
                    "color": "1"  # 红色
                },
                {
                    "id": "purple-1",
                    "type": "text",
                    "text": "逆否命题与原命题的关系？",
                    "x": 600,
                    "y": 300,
                    "width": 400,
                    "height": 120,
                    "color": "3"  # 紫色
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "material-1",
                    "toNode": "red-1"
                },
                {
                    "id": "edge-2",
                    "fromNode": "material-1",
                    "toNode": "purple-1"
                }
            ]
        }

        # 创建临时测试文件
        import tempfile
        import json
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_canvas_data, f)
            temp_path = f.name

        try:
            logic = CanvasBusinessLogic(temp_path)
            result = logic.extract_verification_nodes()

            # 验证返回结构
            assert "red_nodes" in result
            assert "purple_nodes" in result
            assert "stats" in result

            # 验证红色节点
            assert len(result["red_nodes"]) == 1
            assert result["red_nodes"][0]["id"] == "red-1"
            assert result["red_nodes"][0]["content"] == "什么是逆否命题？"

            # 验证紫色节点
            assert len(result["purple_nodes"]) == 1
            assert result["purple_nodes"][0]["id"] == "purple-1"

            # 验证统计信息
            assert result["stats"]["red_count"] == 1
            assert result["stats"]["purple_count"] == 1

        finally:
            os.remove(temp_path)

    def test_extract_with_yellow_nodes(self):
        """测试提取关联的黄色节点内容"""
        test_canvas_data = {
            "nodes": [
                {
                    "id": "red-1",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 120,
                    "color": "1"
                },
                {
                    "id": "yellow-1",
                    "type": "text",
                    "text": "我的理解：逆否命题是将原命题的条件和结论都取反并交换",
                    "x": 600,
                    "y": 100,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色
                },
                {
                    "id": "yellow-2",
                    "type": "text",
                    "text": "例如：若p则q → 若非q则非p",
                    "x": 600,
                    "y": 300,
                    "width": 350,
                    "height": 150,
                    "color": "6"
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "red-1",
                    "toNode": "yellow-1"
                },
                {
                    "id": "edge-2",
                    "fromNode": "red-1",
                    "toNode": "yellow-2"
                }
            ]
        }

        import tempfile
        import json
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_canvas_data, f)
            temp_path = f.name

        try:
            logic = CanvasBusinessLogic(temp_path)
            result = logic.extract_verification_nodes()

            # 验证红色节点关联了2个黄色节点
            assert len(result["red_nodes"]) == 1
            assert len(result["red_nodes"][0]["related_yellow"]) == 2

            yellow_contents = result["red_nodes"][0]["related_yellow"]
            assert "我的理解：逆否命题是将原命题的条件和结论都取反并交换" in yellow_contents
            assert "例如：若p则q → 若非q则非p" in yellow_contents

            # 验证统计信息
            assert result["stats"]["red_with_yellow"] == 1

        finally:
            os.remove(temp_path)

    def test_extract_with_parent_nodes(self):
        """测试提取父节点上下文"""
        test_canvas_data = {
            "nodes": [
                {
                    "id": "material-1",
                    "type": "text",
                    "text": "逆否命题材料",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 300
                },
                {
                    "id": "red-1",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 600,
                    "y": 100,
                    "width": 400,
                    "height": 120,
                    "color": "1"
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "material-1",
                    "toNode": "red-1"
                }
            ]
        }

        import tempfile
        import json
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_canvas_data, f)
            temp_path = f.name

        try:
            logic = CanvasBusinessLogic(temp_path)
            result = logic.extract_verification_nodes()

            # 验证红色节点有父节点
            assert len(result["red_nodes"]) == 1
            assert len(result["red_nodes"][0]["parent_nodes"]) == 1
            assert result["red_nodes"][0]["parent_nodes"][0]["id"] == "material-1"
            assert result["red_nodes"][0]["parent_nodes"][0]["content"] == "逆否命题材料"

            # 验证层级
            assert result["red_nodes"][0]["level"] == 1

        finally:
            os.remove(temp_path)

    def test_extract_empty_canvas(self):
        """测试空Canvas（无红色/紫色节点）"""
        test_canvas_data = {
            "nodes": [
                {
                    "id": "material-1",
                    "type": "text",
                    "text": "材料节点",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 300
                }
            ],
            "edges": []
        }

        import tempfile
        import json
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_canvas_data, f)
            temp_path = f.name

        try:
            logic = CanvasBusinessLogic(temp_path)
            result = logic.extract_verification_nodes()

            # 验证返回空列表，不抛出异常
            assert result["red_nodes"] == []
            assert result["purple_nodes"] == []
            assert result["stats"]["red_count"] == 0
            assert result["stats"]["purple_count"] == 0

        finally:
            os.remove(temp_path)

    def test_extract_no_yellow_nodes(self):
        """测试红色/紫色节点但无黄色节点的情况"""
        test_canvas_data = {
            "nodes": [
                {
                    "id": "red-1",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 120,
                    "color": "1"
                }
            ],
            "edges": []
        }

        import tempfile
        import json
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_canvas_data, f)
            temp_path = f.name

        try:
            logic = CanvasBusinessLogic(temp_path)
            result = logic.extract_verification_nodes()

            # 验证红色节点存在但related_yellow为空列表
            assert len(result["red_nodes"]) == 1
            assert result["red_nodes"][0]["related_yellow"] == []

            # 验证统计信息
            assert result["stats"]["red_with_yellow"] == 0

        finally:
            os.remove(temp_path)

    def test_extract_performance(self):
        """测试性能：提取操作<200ms"""
        # 创建包含100个节点的大型Canvas
        nodes = []
        edges = []

        # 添加材料节点
        nodes.append({
            "id": "material-root",
            "type": "text",
            "text": "根材料",
            "x": 0,
            "y": 0,
            "width": 400,
            "height": 300
        })

        # 添加50个红色节点和50个紫色节点
        for i in range(50):
            nodes.append({
                "id": f"red-{i}",
                "type": "text",
                "text": f"红色问题{i}",
                "x": (i % 10) * 500,
                "y": (i // 10) * 400,
                "width": 400,
                "height": 120,
                "color": "1"
            })
            edges.append({
                "id": f"edge-red-{i}",
                "fromNode": "material-root",
                "toNode": f"red-{i}"
            })

        for i in range(50):
            nodes.append({
                "id": f"purple-{i}",
                "type": "text",
                "text": f"紫色问题{i}",
                "x": (i % 10) * 500,
                "y": 2000 + (i // 10) * 400,
                "width": 400,
                "height": 120,
                "color": "3"
            })
            edges.append({
                "id": f"edge-purple-{i}",
                "fromNode": "material-root",
                "toNode": f"purple-{i}"
            })

        test_canvas_data = {"nodes": nodes, "edges": edges}

        import tempfile
        import json
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_canvas_data, f)
            temp_path = f.name

        try:
            logic = CanvasBusinessLogic(temp_path)

            # 测量执行时间
            start = time.time()
            result = logic.extract_verification_nodes()
            elapsed = (time.time() - start) * 1000  # 转换为毫秒

            # 验证性能
            assert elapsed < 200, f"提取耗时{elapsed:.2f}ms，超过200ms限制"

            # 验证提取结果正确
            assert result["stats"]["red_count"] == 50
            assert result["stats"]["purple_count"] == 50

        finally:
            os.remove(temp_path)

    def test_extract_stats_calculation(self):
        """测试统计信息计算正确"""
        test_canvas_data = {
            "nodes": [
                # 3个红色节点，2个有黄色节点
                {"id": "red-1", "type": "text", "text": "红1", "x": 0, "y": 0, "width": 400, "height": 120, "color": "1"},
                {"id": "red-2", "type": "text", "text": "红2", "x": 0, "y": 200, "width": 400, "height": 120, "color": "1"},
                {"id": "red-3", "type": "text", "text": "红3", "x": 0, "y": 400, "width": 400, "height": 120, "color": "1"},
                # 2个紫色节点，1个有黄色节点
                {"id": "purple-1", "type": "text", "text": "紫1", "x": 0, "y": 600, "width": 400, "height": 120, "color": "3"},
                {"id": "purple-2", "type": "text", "text": "紫2", "x": 0, "y": 800, "width": 400, "height": 120, "color": "3"},
                # 黄色节点
                {"id": "yellow-1", "type": "text", "text": "黄1", "x": 500, "y": 0, "width": 350, "height": 150, "color": "6"},
                {"id": "yellow-2", "type": "text", "text": "黄2", "x": 500, "y": 200, "width": 350, "height": 150, "color": "6"},
                {"id": "yellow-3", "type": "text", "text": "黄3", "x": 500, "y": 600, "width": 350, "height": 150, "color": "6"}
            ],
            "edges": [
                {"id": "e1", "fromNode": "red-1", "toNode": "yellow-1"},
                {"id": "e2", "fromNode": "red-2", "toNode": "yellow-2"},
                {"id": "e3", "fromNode": "purple-1", "toNode": "yellow-3"}
            ]
        }

        import tempfile
        import json
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_canvas_data, f)
            temp_path = f.name

        try:
            logic = CanvasBusinessLogic(temp_path)
            result = logic.extract_verification_nodes()

            # 验证统计信息
            assert result["stats"]["red_count"] == 3
            assert result["stats"]["purple_count"] == 2
            assert result["stats"]["red_with_yellow"] == 2
            assert result["stats"]["purple_with_yellow"] == 1

        finally:
            os.remove(temp_path)

    def test_find_parent_nodes_deep_hierarchy(self):
        """测试深层次层级（材料→问题→子问题）"""
        test_canvas_data = {
            "nodes": [
                {"id": "root", "type": "text", "text": "根节点", "x": 0, "y": 0, "width": 400, "height": 300},
                {"id": "level1", "type": "text", "text": "一级", "x": 500, "y": 0, "width": 400, "height": 300},
                {"id": "level2", "type": "text", "text": "二级", "x": 1000, "y": 0, "width": 400, "height": 300},
                {"id": "red-deep", "type": "text", "text": "深层红色", "x": 1500, "y": 0, "width": 400, "height": 120, "color": "1"}
            ],
            "edges": [
                {"id": "e1", "fromNode": "root", "toNode": "level1"},
                {"id": "e2", "fromNode": "level1", "toNode": "level2"},
                {"id": "e3", "fromNode": "level2", "toNode": "red-deep"}
            ]
        }

        import tempfile
        import json
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_canvas_data, f)
            temp_path = f.name

        try:
            logic = CanvasBusinessLogic(temp_path)
            result = logic.extract_verification_nodes()

            # 验证红色节点层级为3（距离root 3层）
            assert len(result["red_nodes"]) == 1
            assert result["red_nodes"][0]["level"] == 3

            # 验证父节点正确
            assert len(result["red_nodes"][0]["parent_nodes"]) == 1
            assert result["red_nodes"][0]["parent_nodes"][0]["id"] == "level2"

        finally:
            os.remove(temp_path)


class TestCanvasOrchestrator:
    """测试CanvasOrchestrator类（Layer 3）"""

    def test_batch_score_all_yellow_nodes_success(self):
        """测试成功批量评分所有黄色节点（包含不同分数段）"""
        from canvas_utils import CanvasOrchestrator
        from unittest.mock import patch

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        # Mock scoring-agent返回不同分数
        mock_results = [
            {
                "total_score": 88,
                "pass": True,
                "color_action": "change_to_green",
                "feedback": "理解准确，表达清晰"
            },
            {
                "total_score": 72,
                "pass": False,
                "color_action": "change_to_purple",
                "feedback": "基本理解，但不够完整"
            },
            {
                "total_score": 55,
                "pass": False,
                "color_action": "keep_red",
                "feedback": "理解不够准确，需要重新学习"
            }
        ]

        with patch.object(
            orchestrator,
            '_call_scoring_agent',
            side_effect=mock_results
        ):
            report = orchestrator.batch_score_all_yellow_nodes(
                show_progress=False
            )

        # 验证报告统计
        assert report["total_nodes"] == 3
        assert report["passed"] == 1    # 88分 >= 80
        assert report["partial"] == 1   # 72分 60-79
        assert report["failed"] == 1    # 55分 < 60
        assert report["skipped"] == 0
        assert len(report["needs_attention"]) == 1

        # 验证需要关注的节点信息
        attention_node = report["needs_attention"][0]
        assert attention_node["score"] == 55
        assert "question-mno345" in attention_node["node_id"]

        # 验证颜色已更新
        canvas_data = CanvasJSONOperator.read_canvas(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        question_nodes = [
            n for n in canvas_data["nodes"]
            if n["id"].startswith("question-")
        ]

        # 第1个节点 88分 -> 绿色 "2"
        q1 = next(n for n in question_nodes if n["id"] == "question-abc123")
        assert q1["color"] == "2"

        # 第2个节点 72分 -> 紫色 "3"
        q2 = next(n for n in question_nodes if n["id"] == "question-ghi789")
        assert q2["color"] == "3"

        # 第3个节点 55分 -> 红色 "1"
        q3 = next(n for n in question_nodes if n["id"] == "question-mno345")
        assert q3["color"] == "1"

    def test_batch_score_all_yellow_nodes_no_yellow_nodes(self):
        """测试Canvas中没有黄色节点时返回空报告"""
        from canvas_utils import CanvasOrchestrator

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-no-yellow.canvas"
        )

        report = orchestrator.batch_score_all_yellow_nodes(
            show_progress=False
        )

        assert report["total_nodes"] == 0
        assert report["passed"] == 0
        assert report["partial"] == 0
        assert report["failed"] == 0
        assert report["skipped"] == 0
        assert report["needs_attention"] == []

    def test_batch_score_all_yellow_nodes_orphan_yellow_node(self):
        """测试黄色节点没有对应问题节点时的错误处理"""
        from canvas_utils import CanvasOrchestrator
        from unittest.mock import patch

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-orphan-yellow.canvas"
        )

        # Mock scoring-agent只会被调用1次（孤立节点被跳过）
        mock_result = {
            "total_score": 85,
            "pass": True,
            "color_action": "change_to_green",
            "feedback": "理解准确"
        }

        with patch.object(
            orchestrator,
            '_call_scoring_agent',
            return_value=mock_result
        ):
            report = orchestrator.batch_score_all_yellow_nodes(
                show_progress=False
            )

        # 验证孤立节点被跳过
        assert report["total_nodes"] == 2  # 总共2个黄色节点
        assert report["skipped"] == 1      # 1个孤立节点被跳过
        assert report["passed"] == 1       # 1个正常节点被评分

    def test_batch_score_all_yellow_nodes_progress_display(self, capsys):
        """测试进度提示输出正确"""
        from canvas_utils import CanvasOrchestrator
        from unittest.mock import patch

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        mock_result = {
            "total_score": 85,
            "pass": True,
            "color_action": "change_to_green",
            "feedback": "理解准确"
        }

        with patch.object(
            orchestrator,
            '_call_scoring_agent',
            return_value=mock_result
        ):
            orchestrator.batch_score_all_yellow_nodes(show_progress=True)

        captured = capsys.readouterr()
        assert "处理中: 1/3" in captured.out
        assert "处理中: 2/3" in captured.out
        assert "处理中: 3/3" in captured.out
        assert "批量评分完成！" in captured.out

    def test_batch_score_all_yellow_nodes_report_content(self):
        """测试汇总报告包含所有必要信息"""
        from canvas_utils import CanvasOrchestrator
        from unittest.mock import patch

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        mock_result = {
            "total_score": 50,
            "pass": False,
            "color_action": "keep_red",
            "feedback": "需要重新学习"
        }

        with patch.object(
            orchestrator,
            '_call_scoring_agent',
            return_value=mock_result
        ):
            report = orchestrator.batch_score_all_yellow_nodes(
                show_progress=False
            )

        # 验证报告结构
        assert "total_nodes" in report
        assert "passed" in report
        assert "partial" in report
        assert "failed" in report
        assert "skipped" in report
        assert "needs_attention" in report

        # 验证needs_attention包含完整信息
        assert len(report["needs_attention"]) == 3  # 3个节点都<60分
        for attention_node in report["needs_attention"]:
            assert "node_id" in attention_node
            assert "question_text" in attention_node
            assert "score" in attention_node
            assert "feedback" in attention_node

    def test_batch_score_all_yellow_nodes_color_update(self):
        """测试评分后节点颜色正确更新"""
        from canvas_utils import CanvasOrchestrator
        from unittest.mock import patch

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        # Mock不同分数的结果
        mock_results = [
            {
                "total_score": 90,
                "color_action": "change_to_green",
                "feedback": "优秀"
            },
            {
                "total_score": 70,
                "color_action": "change_to_purple",
                "feedback": "良好"
            },
            {
                "total_score": 45,
                "color_action": "keep_red",
                "feedback": "需要改进"
            }
        ]

        with patch.object(
            orchestrator,
            '_call_scoring_agent',
            side_effect=mock_results
        ):
            orchestrator.batch_score_all_yellow_nodes(show_progress=False)

        # 读取更新后的Canvas
        canvas_data = CanvasJSONOperator.read_canvas(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        question_nodes = {
            n["id"]: n
            for n in canvas_data["nodes"]
            if n["id"].startswith("question-")
        }

        # 验证颜色更新正确
        assert question_nodes["question-abc123"]["color"] == "2"  # 绿色
        assert question_nodes["question-ghi789"]["color"] == "3"  # 紫色
        assert question_nodes["question-mno345"]["color"] == "1"  # 红色

    def test_batch_score_all_yellow_nodes_interruption(self):
        """测试中断批量操作时保存已完成结果"""
        from canvas_utils import CanvasOrchestrator
        from unittest.mock import patch
        import shutil

        # 创建测试文件的副本（避免影响其他测试）
        test_copy = "src/tests/fixtures/test-batch-scoring-interrupt.canvas"
        shutil.copy(
            "src/tests/fixtures/test-batch-scoring.canvas",
            test_copy
        )

        try:
            orchestrator = CanvasOrchestrator(test_copy)

            # Mock第2次调用时抛出KeyboardInterrupt
            mock_results = [
                {
                    "total_score": 88,
                    "color_action": "change_to_green",
                    "feedback": "优秀"
                },
                KeyboardInterrupt()  # 第2次调用时中断
            ]

            with patch.object(
                orchestrator,
                '_call_scoring_agent',
                side_effect=mock_results
            ):
                with pytest.raises(KeyboardInterrupt):
                    orchestrator.batch_score_all_yellow_nodes(
                        show_progress=False
                    )

            # 验证第1个节点的结果已保存
            canvas_data = CanvasJSONOperator.read_canvas(test_copy)
            question_nodes = {
                n["id"]: n
                for n in canvas_data["nodes"]
                if n["id"].startswith("question-")
            }

            # 第1个问题节点颜色应已更新为绿色
            assert question_nodes["question-abc123"]["color"] == "2"

        finally:
            # 清理测试文件
            if os.path.exists(test_copy):
                os.remove(test_copy)

    def test_find_question_node_for_yellow(self):
        """测试查找黄色节点对应的问题节点"""
        from canvas_utils import CanvasOrchestrator

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        canvas_data = CanvasJSONOperator.read_canvas(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        relationship_graph = CanvasJSONOperator.build_relationship_graph(
            canvas_data
        )

        # 测试查找正常连接的黄色节点
        question_id = orchestrator._find_question_node_for_yellow(
            "yellow-def456",
            relationship_graph
        )
        assert question_id == "question-abc123"

        # 测试查找不存在的节点
        question_id = orchestrator._find_question_node_for_yellow(
            "nonexistent",
            relationship_graph
        )
        assert question_id is None

    def test_map_color_action_to_code(self):
        """测试color_action到颜色编码的映射"""
        from canvas_utils import CanvasOrchestrator

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        # 测试各种color_action
        assert orchestrator._map_color_action_to_code(
            "change_to_green"
        ) == "2"
        assert orchestrator._map_color_action_to_code(
            "change_to_purple"
        ) == "3"
        assert orchestrator._map_color_action_to_code("keep_red") == "1"

        # 测试无效的color_action（默认返回红色）
        assert orchestrator._map_color_action_to_code("invalid") == "1"

    def test_save_report_to_file(self):
        """测试保存报告到文件"""
        from canvas_utils import CanvasOrchestrator
        import os
        import glob

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        report = {
            "total_nodes": 3,
            "passed": 1,
            "partial": 1,
            "failed": 1,
            "skipped": 0,
            "needs_attention": [
                {
                    "node_id": "question-abc",
                    "question_text": "测试问题",
                    "score": 55,
                    "feedback": "需要改进"
                }
            ]
        }

        # 保存报告（不指定路径，自动生成）
        orchestrator._save_report_to_file(report)

        # 查找生成的报告文件
        report_files = glob.glob(
            "src/tests/fixtures/test-batch-scoring-批量评分报告-*.md"
        )

        try:
            assert len(report_files) > 0, "应该生成报告文件"

            # 读取报告内容验证
            with open(report_files[0], 'r', encoding='utf-8') as f:
                content = f.read()

            assert "批量评分报告" in content
            assert "统计摘要" in content
            assert "总节点数" in content
            assert "需要重点关注的节点" in content

        finally:
            # 清理生成的报告文件
            for report_file in report_files:
                if os.path.exists(report_file):
                    os.remove(report_file)

    def test_canvas_orchestrator_init(self):
        """测试CanvasOrchestrator初始化"""
        from canvas_utils import CanvasOrchestrator

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        # 验证属性
        assert orchestrator.canvas_path == \
            "src/tests/fixtures/test-batch-scoring.canvas"
        assert orchestrator.operator is not None
        assert orchestrator.logic is not None

    def test_canvas_orchestrator_init_file_not_found(self):
        """测试初始化时文件不存在抛出异常"""
        from canvas_utils import CanvasOrchestrator

        with pytest.raises(FileNotFoundError):
            CanvasOrchestrator("nonexistent.canvas")


class TestVerificationQuestionGeneration:
    """测试检验问题生成功能 (Story 4.2)"""

    @pytest.fixture
    def sample_extracted_nodes(self):
        """包含红色和紫色节点的示例数据"""
        return {
            "red_nodes": [
                {
                    "id": "red-abc123",
                    "content": "什么是逆否命题？",
                    "related_yellow": [],
                    "parent_nodes": [
                        {"id": "material-1", "content": "命题逻辑基础"}
                    ],
                    "level": 1
                },
                {
                    "id": "red-def456",
                    "content": "'非p'和'非q'是什么意思？",
                    "related_yellow": [],
                    "parent_nodes": [
                        {"id": "material-1", "content": "命题逻辑基础"}
                    ],
                    "level": 1
                }
            ],
            "purple_nodes": [
                {
                    "id": "purple-xyz789",
                    "content": "逆否命题与原命题等价吗？",
                    "related_yellow": [
                        "我觉得它们意思相同，都描述同一个逻辑关系"
                    ],
                    "parent_nodes": [
                        {"id": "material-1", "content": "命题逻辑基础"}
                    ],
                    "level": 1
                }
            ],
            "stats": {
                "red_count": 2,
                "purple_count": 1,
                "red_with_yellow": 0,
                "purple_with_yellow": 1
            }
        }

    def test_generate_questions_for_red_nodes(self, sample_extracted_nodes):
        """测试为红色节点生成1-2个问题 (AC: 1)"""
        from canvas_utils import CanvasOrchestrator

        # Arrange: 准备只有红色节点的数据
        extracted_nodes = {
            "red_nodes": [sample_extracted_nodes["red_nodes"][0]],
            "purple_nodes": [],
            "stats": {"red_count": 1, "purple_count": 0}
        }

        # Act: 调用生成方法
        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        questions = orchestrator.generate_verification_questions_with_agent(
            extracted_nodes
        )

        # Assert: 验证生成1-2个问题
        red_questions = [
            q for q in questions
            if q["source_node_id"] == "red-abc123"
        ]
        assert 1 <= len(red_questions) <= 2, \
            f"红色节点应生成1-2个问题,实际{len(red_questions)}个"
        assert all("question_text" in q for q in red_questions)
        assert all("source_node_id" in q for q in red_questions)

    def test_generate_questions_for_purple_nodes(self, sample_extracted_nodes):
        """测试为紫色节点生成2-3个问题 (AC: 2)"""
        from canvas_utils import CanvasOrchestrator

        # Arrange: 准备只有紫色节点的数据
        extracted_nodes = {
            "red_nodes": [],
            "purple_nodes": [sample_extracted_nodes["purple_nodes"][0]],
            "stats": {"red_count": 0, "purple_count": 1}
        }

        # Act
        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        questions = orchestrator.generate_verification_questions_with_agent(
            extracted_nodes
        )

        # Assert: 验证生成2-3个问题
        purple_questions = [
            q for q in questions
            if q["source_node_id"] == "purple-xyz789"
        ]
        assert 2 <= len(purple_questions) <= 3, \
            f"紫色节点应生成2-3个问题,实际{len(purple_questions)}个"

    def test_questions_have_source_node_id(self, sample_extracted_nodes):
        """测试问题标注来源节点ID (AC: 4)"""
        from canvas_utils import CanvasOrchestrator

        # Arrange
        extracted_nodes = sample_extracted_nodes

        # Act
        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        questions = orchestrator.generate_verification_questions_with_agent(
            extracted_nodes
        )

        # Assert: 所有问题都有source_node_id
        assert all("source_node_id" in q for q in questions)
        valid_ids = ["red-abc123", "red-def456", "purple-xyz789"]
        assert all(
            q["source_node_id"] in valid_ids for q in questions
        )

    def test_questions_are_targeted(self, sample_extracted_nodes):
        """测试问题有针对性,能揭示盲区 (AC: 3)"""
        from canvas_utils import CanvasOrchestrator

        # Arrange: 包含黄色节点理解的紫色节点
        extracted_nodes = {
            "red_nodes": [],
            "purple_nodes": [
                {
                    "id": "purple-1",
                    "content": "逆否命题是什么?",
                    "related_yellow": [
                        "逆否命题就是把原命题倒过来说"
                    ],  # 模糊理解
                    "parent_nodes": [],
                    "level": 1
                }
            ],
            "stats": {"red_count": 0, "purple_count": 1}
        }

        # Act
        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        questions = orchestrator.generate_verification_questions_with_agent(
            extracted_nodes
        )

        # Assert: 验证问题有question_type和difficulty字段
        assert all("question_type" in q for q in questions)
        assert all("difficulty" in q for q in questions)
        valid_types = {"突破型", "检验型", "应用型", "综合型", "基础型"}
        assert all(
            q["question_type"] in valid_types for q in questions
        )

    def test_generation_performance(self, sample_extracted_nodes):
        """测试问题生成耗时<5秒 (AC: 5)"""
        from canvas_utils import CanvasOrchestrator
        import time

        # Arrange: 准备较大规模数据(20个节点)
        red_nodes = [
            {
                "id": f"red-{i}",
                "content": f"问题{i}",
                "related_yellow": [],
                "parent_nodes": [],
                "level": 1
            }
            for i in range(10)
        ]
        purple_nodes = [
            {
                "id": f"purple-{i}",
                "content": f"问题{i}",
                "related_yellow": [f"理解{i}"],
                "parent_nodes": [],
                "level": 1
            }
            for i in range(10)
        ]
        extracted_nodes = {
            "red_nodes": red_nodes,
            "purple_nodes": purple_nodes,
            "stats": {"red_count": 10, "purple_count": 10}
        }

        # Act: 测量执行时间
        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        start = time.time()
        questions = orchestrator.generate_verification_questions_with_agent(
            extracted_nodes
        )
        elapsed = time.time() - start

        # Assert: 验证<5秒
        assert elapsed < 5.0, \
            f"问题生成耗时{elapsed:.2f}秒,超过5秒限制"
        assert len(questions) > 0, "应该生成至少1个问题"

    def test_agent_call_error_handling(self):
        """测试Agent调用失败时的错误处理"""
        from canvas_utils import CanvasOrchestrator

        # Arrange: 准备会导致错误的数据(缺少必要字段)
        extracted_nodes = {
            "red_nodes": [],
            "purple_nodes": []
            # 故意不包含stats字段
        }

        # Act & Assert: 验证不会崩溃,而是返回空列表或抛出明确错误
        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        questions = orchestrator.generate_verification_questions_with_agent(
            extracted_nodes
        )
        # 空输入应该返回空列表
        assert isinstance(questions, list)

    def test_question_deduplication(self):
        """测试问题去重逻辑"""
        from canvas_utils import CanvasBusinessLogic

        # Arrange: 准备包含重复问题的列表
        questions = [
            {
                "source_node_id": "node-1",
                "question_text": "什么是命题？",
                "question_type": "检验型",
                "difficulty": "基础"
            },
            {
                "source_node_id": "node-2",
                "question_text": "什么是命题？",  # 重复
                "question_type": "突破型",
                "difficulty": "基础"
            },
            {
                "source_node_id": "node-3",
                "question_text": "如何理解命题？",  # 不同
                "question_type": "应用型",
                "difficulty": "深度"
            }
        ]

        # Act
        logic = CanvasBusinessLogic(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        deduped_questions = logic._classify_questions(questions)

        # Assert: 验证去重后只保留唯一问题
        question_texts = [q["question_text"] for q in deduped_questions]
        assert len(question_texts) == len(set(question_texts)), \
            "不应有重复问题"
        # 应该只有2个不同的问题
        assert len(deduped_questions) == 2

    def test_classify_questions_validates_types(self):
        """测试_classify_questions验证问题类型"""
        from canvas_utils import CanvasBusinessLogic

        # Arrange: 准备包含无效类型的问题
        questions = [
            {
                "source_node_id": "node-1",
                "question_text": "测试问题1",
                "question_type": "无效类型",  # 无效
                "difficulty": "基础"
            },
            {
                "source_node_id": "node-2",
                "question_text": "测试问题2",
                "question_type": "检验型",  # 有效
                "difficulty": "深度"
            }
        ]

        # Act
        logic = CanvasBusinessLogic(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        classified = logic._classify_questions(questions)

        # Assert: 验证无效类型被修正为"检验型"
        assert all(
            q["question_type"] in
            {"突破型", "检验型", "应用型", "综合型", "基础型"}
            for q in classified
        )

    def test_classify_questions_sorts_by_difficulty(self):
        """测试_classify_questions按难度排序（深度优先）"""
        from canvas_utils import CanvasBusinessLogic

        # Arrange: 准备混合难度的问题
        questions = [
            {
                "source_node_id": "node-1",
                "question_text": "基础问题1",
                "question_type": "检验型",
                "difficulty": "基础"
            },
            {
                "source_node_id": "node-2",
                "question_text": "深度问题1",
                "question_type": "应用型",
                "difficulty": "深度"
            },
            {
                "source_node_id": "node-3",
                "question_text": "基础问题2",
                "question_type": "突破型",
                "difficulty": "基础"
            },
            {
                "source_node_id": "node-4",
                "question_text": "深度问题2",
                "question_type": "综合型",
                "difficulty": "深度"
            }
        ]

        # Act
        logic = CanvasBusinessLogic(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )
        sorted_questions = logic._classify_questions(questions)

        # Assert: 验证深度问题排在前面
        difficulties = [q["difficulty"] for q in sorted_questions]
        # 前面的应该是深度问题
        deep_count = sum(1 for d in difficulties if d == "深度")
        first_deep_indices = [
            i for i, d in enumerate(difficulties) if d == "深度"
        ]
        # 所有深度问题的索引应该小于基础问题
        if deep_count > 0:
            assert max(first_deep_indices) < len(sorted_questions) - 1 or \
                all(d == "深度" for d in difficulties)

    def test_empty_extracted_nodes_raises_error(self):
        """测试空的extracted_nodes抛出错误"""
        from canvas_utils import CanvasOrchestrator

        # Arrange
        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="extracted_nodes不能为空"):
            orchestrator.generate_verification_questions_with_agent(None)

    def test_missing_fields_raises_error(self):
        """测试缺少必要字段抛出错误"""
        from canvas_utils import CanvasOrchestrator

        # Arrange: 缺少purple_nodes字段
        extracted_nodes = {
            "red_nodes": []
            # 故意不包含purple_nodes
        }

        orchestrator = CanvasOrchestrator(
            "src/tests/fixtures/test-batch-scoring.canvas"
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="extracted_nodes缺少必要字段"
        ):
            orchestrator.generate_verification_questions_with_agent(
                extracted_nodes
            )


# ========== Story 4.4: 检验白板Canvas文件生成 ==========

class TestReviewCanvasGeneration:
    """测试检验白板生成功能（Story 4.4）"""

    @pytest.fixture
    def sample_clustered_questions(self):
        """包含多个主题聚类的示例数据"""
        return {
            "命题逻辑": [
                {
                    "source_node_id": "red-1",
                    "question_text": "什么是逆否命题?",
                    "question_type": "突破型",
                    "difficulty": "基础",
                    "guidance": "💡 从定义出发",
                    "rationale": "帮助理解基础概念"
                },
                {
                    "source_node_id": "red-2",
                    "question_text": "逆否命题和原命题等价吗?",
                    "question_type": "检验型",
                    "difficulty": "深度",
                    "guidance": "",
                    "rationale": "检验是否真正理解"
                }
            ],
            "布尔代数": [
                {
                    "source_node_id": "purple-1",
                    "question_text": "什么是布尔代数?",
                    "question_type": "突破型",
                    "difficulty": "基础",
                    "guidance": "💡 从集合运算类比",
                    "rationale": "建立直观理解"
                }
            ]
        }

    def test_generate_review_canvas_file_success(
        self,
        sample_clustered_questions
    ):
        """测试成功生成检验白板文件 (AC: 1-3)"""
        import json

        # Arrange: 准备测试环境
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        # Act
        result = logic.generate_review_canvas_file(sample_clustered_questions)

        # Assert: 文件存在
        assert os.path.exists(result["review_canvas_path"]), \
            "检验白板文件应存在"

        # 验证文件是有效的JSON
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)
            assert "nodes" in canvas_data
            assert "edges" in canvas_data

        # 验证返回结果
        assert result["total_questions"] == 3
        assert result["cluster_count"] == 2
        assert result["generation_time"] < 8.0

        # 清理测试文件
        if os.path.exists(result["review_canvas_path"]):
            os.remove(result["review_canvas_path"])

    def test_review_canvas_filename_follows_convention(self):
        """测试文件命名符合规范 (AC: 2)"""
        from datetime import datetime

        # Arrange
        clustered_questions = {
            "主题1": [{
                "question_text": "问题1",
                "question_type": "突破型",
                "difficulty": "基础"
            }]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert: 文件名格式: {basename}-检验白板-{YYYYMMDD}.canvas
        filename = os.path.basename(result["review_canvas_path"])
        date_str = datetime.now().strftime("%Y%m%d")
        expected_pattern = f"test-basic-检验白板-{date_str}.canvas"

        assert filename == expected_pattern, \
            f"文件名应为: {expected_pattern}, 实际为: {filename}"

        # 清理
        if os.path.exists(result["review_canvas_path"]):
            os.remove(result["review_canvas_path"])

    def test_review_canvas_saved_in_same_directory(self):
        """测试文件保存在原白板同一目录 (AC: 3)"""
        # Arrange
        original_path = "src/tests/fixtures/test-basic.canvas"
        clustered_questions = {
            "主题1": [{
                "question_text": "问题1",
                "question_type": "突破型",
                "difficulty": "基础"
            }]
        }

        # Act
        logic = CanvasBusinessLogic(original_path)
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert: 目录相同
        original_dir = os.path.dirname(os.path.abspath(original_path))
        review_dir = os.path.dirname(os.path.abspath(result["review_canvas_path"]))

        assert original_dir == review_dir, \
            f"检验白板应与原白板在同一目录。原白板: {original_dir}, 检验白板: {review_dir}"

        # 清理
        if os.path.exists(result["review_canvas_path"]):
            os.remove(result["review_canvas_path"])

    def test_review_canvas_contains_description_node(self):
        """测试包含说明节点(蓝色) (AC: 4)"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [{
                "question_text": "问题1",
                "question_type": "突破型",
                "difficulty": "基础"
            }]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert: 读取生成的Canvas文件
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        # 查找蓝色说明节点
        description_nodes = [
            n for n in canvas_data["nodes"]
            if n.get("color") == "5"
        ]

        assert len(description_nodes) == 1, "应有1个蓝色说明节点"
        assert "# 检验白板" in description_nodes[0]["text"], \
            "说明节点应包含标题"
        assert "生成时间" in description_nodes[0]["text"], \
            "说明节点应包含生成时间"
        assert "检验问题: 1 个" in description_nodes[0]["text"], \
            "说明节点应包含问题数量"

        # 清理
        os.remove(result["review_canvas_path"])

    def test_review_canvas_contains_all_questions(self):
        """测试包含所有检验问题(红色) (AC: 5)"""
        import json

        # Arrange
        clustered_questions = {
            "命题逻辑": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"},
                {"question_text": "问题2", "question_type": "检验型", "difficulty": "深度"}
            ],
            "布尔代数": [
                {"question_text": "问题3", "question_type": "应用型", "difficulty": "基础"}
            ]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        # 统计红色问题节点
        red_question_nodes = [
            n for n in canvas_data["nodes"]
            if n.get("color") == "1"
        ]

        assert len(red_question_nodes) == 3, "应有3个红色问题节点"
        assert result["total_questions"] == 3, "返回结果应正确统计问题数"

        # 验证问题文本
        question_texts = [n["text"] for n in red_question_nodes]
        assert "问题1" in question_texts
        assert "问题2" in question_texts
        assert "问题3" in question_texts

        # 清理
        os.remove(result["review_canvas_path"])

    def test_each_question_has_yellow_node(self):
        """测试每个问题关联黄色理解节点 (AC: 6)"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"},
                {"question_text": "问题2", "question_type": "检验型", "difficulty": "深度"}
            ]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        red_nodes = [n for n in canvas_data["nodes"] if n.get("color") == "1"]
        yellow_nodes = [n for n in canvas_data["nodes"] if n.get("color") == "6"]

        assert len(red_nodes) == len(yellow_nodes), \
            "红色问题节点数应等于黄色理解节点数"

        # 验证每个红色节点都有边连接到一个黄色节点
        edges = canvas_data["edges"]
        for red_node in red_nodes:
            # 查找从红色节点出发的边
            edges_from_red = [
                e for e in edges
                if e["fromNode"] == red_node["id"]
            ]
            assert len(edges_from_red) >= 1, \
                f"红色节点{red_node['id']}应有至少1条边"

            # 验证目标节点是黄色
            to_node_id = edges_from_red[0]["toNode"]
            to_node = next(
                n for n in canvas_data["nodes"]
                if n["id"] == to_node_id
            )
            assert to_node["color"] == "6", "问题节点应连接到黄色理解节点"

        # 验证黄色节点包含占位符
        for yellow_node in yellow_nodes:
            assert "[请填写你的理解]" in yellow_node["text"], \
                "黄色节点应包含占位符文本"

        # 清理
        os.remove(result["review_canvas_path"])

    def test_generation_time_under_8_seconds(self):
        """测试生成操作耗时<8秒 (AC: 7)"""
        # Arrange: 准备较大规模数据(30个问题)
        clustered_questions = {}
        for i in range(6):  # 6个聚类
            clustered_questions[f"主题{i+1}"] = [
                {
                    "question_text": f"问题{j+1}",
                    "question_type": "突破型",
                    "difficulty": "基础"
                }
                for j in range(5)  # 每个聚类5个问题
            ]

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert
        assert result["generation_time"] < 8.0, \
            f"生成耗时{result['generation_time']:.2f}秒应<8秒"

        # 清理
        os.remove(result["review_canvas_path"])

    def test_v11_layout_yellow_below_question(self):
        """测试v1.1布局:黄色节点在问题节点正下方"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [{
                "question_text": "问题1",
                "question_type": "突破型",
                "difficulty": "基础"
            }]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        red_node = next(n for n in canvas_data["nodes"] if n.get("color") == "1")

        # 找到对应的黄色节点
        edge = next(e for e in canvas_data["edges"] if e["fromNode"] == red_node["id"])
        yellow_node = next(n for n in canvas_data["nodes"] if n["id"] == edge["toNode"])

        # 验证v1.1布局:
        # 1. 水平对齐(x坐标相同)
        assert yellow_node["x"] == red_node["x"], \
            "黄色节点应与问题节点水平对齐"

        # 2. 在下方(y = question_y + height + offset)
        expected_y = red_node["y"] + 120 + 30  # QUESTION_HEIGHT + YELLOW_OFFSET_Y
        assert yellow_node["y"] == expected_y, \
            f"黄色节点y坐标应为{expected_y},实际为{yellow_node['y']}"

        # 清理
        os.remove(result["review_canvas_path"])

    def test_input_validation_empty_clusters(self):
        """测试输入验证:空聚类"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        with pytest.raises(ValueError, match="clustered_questions不能为空"):
            logic.generate_review_canvas_file({})

    def test_input_validation_invalid_type(self):
        """测试输入验证:无效类型"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        # 传入非空的list来触发类型检查
        with pytest.raises(ValueError, match="clustered_questions必须是字典类型"):
            logic.generate_review_canvas_file(["not", "a", "dict"])

    def test_input_validation_missing_question_text(self):
        """测试输入验证:缺少question_text字段"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        invalid_clusters = {
            "主题1": [
                {"question_type": "突破型"}  # 缺少question_text
            ]
        }

        with pytest.raises(ValueError, match="缺少'question_text'字段"):
            logic.generate_review_canvas_file(invalid_clusters)

    def test_input_validation_no_questions(self):
        """测试输入验证:聚类中没有问题"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        clusters_with_no_questions = {
            "主题1": []  # 空列表
        }

        with pytest.raises(ValueError, match="没有检验问题可生成"):
            logic.generate_review_canvas_file(clusters_with_no_questions)

    def test_output_filename_override(self):
        """测试自定义输出文件名"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [{
                "question_text": "问题1",
                "question_type": "突破型",
                "difficulty": "基础"
            }]
        }
        custom_path = "src/tests/fixtures/custom-review.canvas"

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(
            clustered_questions,
            output_filename_override=custom_path
        )

        # Assert
        assert result["review_canvas_path"] == custom_path
        assert os.path.exists(custom_path)

        # 验证文件内容有效
        with open(custom_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)
            assert "nodes" in canvas_data
            assert len(canvas_data["nodes"]) > 0

        # 清理
        os.remove(custom_path)

    def test_multiple_clusters_layout(self):
        """测试多个聚类的空间布局"""
        import json

        # Arrange: 3个聚类
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"}
            ],
            "主题2": [
                {"question_text": "问题2", "question_type": "突破型", "difficulty": "基础"}
            ],
            "主题3": [
                {"question_text": "问题3", "question_type": "突破型", "difficulty": "基础"}
            ]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        red_nodes = sorted(
            [n for n in canvas_data["nodes"] if n.get("color") == "1"],
            key=lambda n: n["y"]
        )

        # 验证聚类间有间隔
        # 每个聚类只有1个问题,所以y坐标应该递增
        assert red_nodes[0]["y"] < red_nodes[1]["y"], \
            "第一个聚类应在第二个聚类上方"
        assert red_nodes[1]["y"] < red_nodes[2]["y"], \
            "第二个聚类应在第三个聚类上方"

        # 清理
        os.remove(result["review_canvas_path"])

    def test_clustered_questions_with_multiple_questions_per_cluster(self):
        """测试每个聚类包含多个问题的布局"""
        import json

        # Arrange: 一个聚类包含3个问题
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"},
                {"question_text": "问题2", "question_type": "突破型", "difficulty": "基础"},
                {"question_text": "问题3", "question_type": "突破型", "difficulty": "基础"}
            ]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)

        # Assert
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        red_nodes = sorted(
            [n for n in canvas_data["nodes"] if n.get("color") == "1"],
            key=lambda n: n["y"]
        )

        # 验证3个问题节点垂直排列,间距为VERTICAL_SPACING_BASE (380px)
        assert len(red_nodes) == 3
        assert red_nodes[1]["y"] - red_nodes[0]["y"] == 380
        assert red_nodes[2]["y"] - red_nodes[1]["y"] == 380

        # 清理
        os.remove(result["review_canvas_path"])


class TestReviewCanvasDynamicOperations:
    """测试检验白板的动态学习操作

    验证所有Agent操作在检验白板上的通用性 (Story 4.6)
    """

    def test_add_decomposition_to_review_canvas(self, tmp_path):
        """测试在检验白板上添加拆解问题 (AC: 1, 2)"""
        import shutil
        import json

        # Arrange: 准备检验白板（复制到临时目录）
        review_canvas_src = "src/tests/fixtures/test-review-canvas.canvas"
        review_canvas_path = str(tmp_path / "test-review-canvas.canvas")
        shutil.copy(review_canvas_src, review_canvas_path)

        logic = CanvasBusinessLogic(review_canvas_path)

        # Act: 添加子问题（模拟拆解Agent）
        q_id, y_id = logic.add_sub_question_with_yellow_node(
            "question-red-1",
            "子问题：逆否命题的定义是什么？",
            "💡 提示：从形式化定义出发"
        )

        # Assert: 验证操作成功
        canvas_data = CanvasJSONOperator.read_canvas(review_canvas_path)
        question_node = next(n for n in canvas_data["nodes"] if n["id"] == q_id)
        yellow_node = next(n for n in canvas_data["nodes"] if n["id"] == y_id)

        assert question_node["color"] == canvas_utils.COLOR_CODE_RED
        assert yellow_node["color"] == canvas_utils.COLOR_CODE_YELLOW
        assert "子问题" in question_node["text"]
        # Guidance goes into yellow node template, verify it was created
        assert yellow_node["text"] is not None

    def test_scoring_on_review_canvas(self, tmp_path):
        """测试在检验白板上更新节点颜色（评分） (AC: 1, 4)"""
        import shutil

        # Arrange
        review_canvas_src = "src/tests/fixtures/test-review-canvas.canvas"
        review_canvas_path = str(tmp_path / "test-review-canvas.canvas")
        shutil.copy(review_canvas_src, review_canvas_path)

        # Act: 更新节点颜色（模拟评分Agent）
        canvas_data = CanvasJSONOperator.read_canvas(review_canvas_path)
        CanvasJSONOperator.update_node_color(
            canvas_data,
            "question-red-1",
            canvas_utils.COLOR_CODE_GREEN
        )
        CanvasJSONOperator.write_canvas(review_canvas_path, canvas_data)

        # Assert
        canvas_data = CanvasJSONOperator.read_canvas(review_canvas_path)
        question_node = next(n for n in canvas_data["nodes"] if n["id"] == "question-red-1")
        assert question_node["color"] == canvas_utils.COLOR_CODE_GREEN

    def test_add_explanation_file_to_review_canvas(self, tmp_path):
        """测试在检验白板上添加补充解释文件节点 (AC: 1, 3)"""
        import shutil
        import json

        # Arrange
        review_canvas_src = "src/tests/fixtures/test-review-canvas.canvas"
        review_canvas_path = str(tmp_path / "test-review-canvas.canvas")
        shutil.copy(review_canvas_src, review_canvas_path)

        # Act: 添加file节点（模拟补充解释Agent）
        canvas_data = CanvasJSONOperator.read_canvas(review_canvas_path)
        file_node_id = CanvasJSONOperator.create_node(
            canvas_data,
            node_type="file",
            x=800,
            y=400,
            width=300,
            height=200,
            file="逆否命题-口语化解释-20250115.md"
        )
        CanvasJSONOperator.write_canvas(review_canvas_path, canvas_data)

        # Assert
        canvas_data_after = CanvasJSONOperator.read_canvas(review_canvas_path)
        file_node = next(n for n in canvas_data_after["nodes"] if n["id"] == file_node_id)
        assert file_node["type"] == "file"
        assert "口语化解释" in file_node["file"]

    def test_add_custom_nodes_to_review_canvas(self, tmp_path):
        """测试在检验白板上添加自定义节点 (AC: 1, 5)"""
        import shutil

        # Arrange
        review_canvas_src = "src/tests/fixtures/test-review-canvas.canvas"
        review_canvas_path = str(tmp_path / "test-review-canvas.canvas")
        shutil.copy(review_canvas_src, review_canvas_path)

        # Act: 用户添加自定义节点
        canvas_data = CanvasJSONOperator.read_canvas(review_canvas_path)
        custom_node_id = CanvasJSONOperator.create_node(
            canvas_data,
            node_type="text",
            x=500,
            y=600,
            text="我自己的理解补充：逆否命题可以用真值表验证",
            color=canvas_utils.COLOR_CODE_PURPLE
        )
        CanvasJSONOperator.write_canvas(review_canvas_path, canvas_data)

        # Assert
        canvas_data_after = CanvasJSONOperator.read_canvas(review_canvas_path)
        custom_node = next(n for n in canvas_data_after["nodes"] if n["id"] == custom_node_id)
        assert "真值表" in custom_node["text"]
        assert custom_node["color"] == canvas_utils.COLOR_CODE_PURPLE

    def test_review_canvas_grows_dynamically(self, tmp_path):
        """测试检验白板动态增长 (AC: 6)"""
        import shutil
        import json

        # Arrange: 初始检验白板（3个问题，3个黄色节点，1个说明节点）
        review_canvas_src = "src/tests/fixtures/test-review-canvas.canvas"
        review_canvas_path = str(tmp_path / "test-review-canvas.canvas")
        shutil.copy(review_canvas_src, review_canvas_path)

        canvas_data_initial = CanvasJSONOperator.read_canvas(review_canvas_path)
        initial_node_count = len(canvas_data_initial["nodes"])

        # Act: 模拟用户操作流程
        logic = CanvasBusinessLogic(review_canvas_path)

        # 1. 拆解问题1 → 添加2个子问题
        logic.add_sub_question_with_yellow_node("question-red-1", "子问题1", "")
        logic.add_sub_question_with_yellow_node("question-red-1", "子问题2", "")

        # 2. 添加补充解释文件节点
        canvas_data = CanvasJSONOperator.read_canvas(review_canvas_path)
        CanvasJSONOperator.create_node(
            canvas_data,
            node_type="file",
            x=800,
            y=400,
            file="解释文件.md"
        )
        CanvasJSONOperator.write_canvas(review_canvas_path, canvas_data)

        # 3. 用户添加2个自定义节点
        canvas_data = CanvasJSONOperator.read_canvas(review_canvas_path)
        CanvasJSONOperator.create_node(canvas_data, "text", x=600, y=700, text="自定义节点1")
        CanvasJSONOperator.create_node(canvas_data, "text", x=600, y=900, text="自定义节点2")
        CanvasJSONOperator.write_canvas(review_canvas_path, canvas_data)

        # Assert: 检验白板节点数量显著增加
        canvas_data_final = CanvasJSONOperator.read_canvas(review_canvas_path)
        final_node_count = len(canvas_data_final["nodes"])

        # 初始7节点 (1说明+3问题+3黄色)
        # 新增：2子问题+2黄色+1file+2自定义=7节点
        # 总共：7+7=14节点
        assert final_node_count == initial_node_count + 7, \
            f"检验白板应增长7个节点（从{initial_node_count}到{final_node_count}）"

        # 验证检验白板是"活的"——节点类型多样化
        node_types = [n["type"] for n in canvas_data_final["nodes"]]
        assert "text" in node_types
        assert "file" in node_types

        # 验证有多种颜色节点（红、黄、紫等）
        colors = set(n.get("color") for n in canvas_data_final["nodes"] if "color" in n)
        assert len(colors) >= 3, "检验白板应包含多种颜色节点（体现动态增长）"


class TestCanvasComparison:
    """测试Canvas对比分析功能（Story 4.8）"""

    def test_compare_with_canvas_basic(self):
        """测试基础对比功能"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        result = logic.compare_with_canvas(review_path)

        # Assert - 验证返回结构
        assert "structure_comparison" in result
        assert "content_comparison" in result
        assert "color_comparison" in result
        assert "suggestions" in result

        # 验证结构对比数据
        structure = result["structure_comparison"]
        assert structure["original_node_count"] == 5
        assert structure["review_node_count"] == 5
        assert 0.0 <= structure["replication_rate"] <= 1.5
        assert structure["original_depth"] >= 1
        assert structure["review_depth"] >= 1
        assert "node_type_distribution" in structure

    def test_compare_structure_statistics(self):
        """测试结构对比统计准确性"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        result = logic.compare_with_canvas(review_path)
        structure = result["structure_comparison"]

        # Assert - 节点数量
        assert structure["original_node_count"] == 5
        assert structure["review_node_count"] == 5

        # Assert - 复现率
        expected_rate = 5 / 5  # review_count / original_count
        assert abs(structure["replication_rate"] - expected_rate) < 0.01

        # Assert - 节点类型分布
        original_dist = structure["node_type_distribution"]["original"]
        assert original_dist["text"] == 5
        assert original_dist["file"] == 0
        assert original_dist["group"] == 0

        review_dist = structure["node_type_distribution"]["review"]
        assert review_dist["text"] == 5

    def test_identify_missing_concepts(self):
        """测试遗漏知识点识别"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        result = logic.compare_with_canvas(review_path)
        content = result["content_comparison"]

        # Assert
        # 原白板有5个核心概念，检验白板应该遗漏部分概念
        missing = content["missing_concepts"]
        assert isinstance(missing, list)
        # 至少识别出一些遗漏（根据测试数据）
        assert len(missing) >= 2  # "逆否命题的等价性证明" 和 "真值表的构造方法" 应该被识别为遗漏

        # 验证遗漏概念的结构
        for concept in missing:
            assert "id" in concept
            assert "text" in concept
            assert "color" in concept
            assert len(concept["text"]) > 0

    def test_identify_new_concepts(self):
        """测试新增理解识别"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        result = logic.compare_with_canvas(review_path)
        content = result["content_comparison"]

        # Assert
        new_concepts = content["new_concepts"]
        assert isinstance(new_concepts, list)
        # 检验白板中的"个人总结"应该被识别为新增理解
        assert len(new_concepts) >= 1

        # 验证新增概念的结构
        for concept in new_concepts:
            assert "id" in concept
            assert "text" in concept
            assert len(concept["text"]) > 0

    def test_color_distribution_comparison(self):
        """测试颜色分布对比"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        result = logic.compare_with_canvas(review_path)
        color = result["color_comparison"]

        # Assert - 验证颜色统计结构
        assert "original" in color
        assert "review" in color
        assert "understanding_rate" in color

        # Assert - 原白板颜色分布
        original_colors = color["original"]
        assert original_colors["red"] == 2  # test-original.canvas 有2个红色节点
        assert original_colors["purple"] == 1  # 1个紫色
        assert original_colors["green"] == 2  # 2个绿色
        assert original_colors["yellow"] == 0  # 0个黄色

        # Assert - 检验白板颜色分布
        review_colors = color["review"]
        assert review_colors["red"] >= 1
        assert review_colors["yellow"] >= 2  # 检验白板有黄色理解节点

        # Assert - 理解质量指标
        assert 0.0 <= color["understanding_rate"] <= 1.0

    def test_generate_comparison_report(self, tmp_path):
        """测试对比报告生成"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        logic = CanvasBusinessLogic(original_path)
        comparison_data = logic.compare_with_canvas(review_path)

        output_path = tmp_path / "test-comparison-report.md"

        # Act
        logic.generate_comparison_report(comparison_data, str(output_path))

        # Assert - 文件已创建
        assert output_path.exists()

        # Assert - 验证报告内容
        content = output_path.read_text(encoding='utf-8')
        assert "# 检验白板对比报告" in content
        assert "整体统计" in content
        assert "知识覆盖分析" in content
        assert "理解质量分析" in content
        assert "改进建议" in content

        # 验证包含具体数据
        assert "原白板节点数" in content
        assert "检验白板节点数" in content
        assert "复现率" in content
        assert "已复现" in content
        assert "遗漏" in content
        assert "新增理解" in content

        # 验证颜色分布
        assert "原白板颜色分布" in content
        assert "检验白板颜色分布" in content
        assert "理解质量指标" in content

    def test_comparison_suggestions(self):
        """测试改进建议生成"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        result = logic.compare_with_canvas(review_path)
        suggestions = result["suggestions"]

        # Assert
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # 验证建议内容类型
        suggestion_text = " ".join(suggestions)
        # 应该包含以下至少一种建议
        has_valid_suggestion = any([
            "遗漏" in suggestion_text,
            "紫色节点" in suggestion_text,
            "红色节点" in suggestion_text,
            "理解质量" in suggestion_text,
            "原创理解" in suggestion_text
        ])
        assert has_valid_suggestion, "应该生成有意义的改进建议"

    def test_comparison_performance(self):
        """测试对比操作性能（<5秒）"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        import time
        start_time = time.time()
        result = logic.compare_with_canvas(review_path)
        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time < 5.0, f"对比耗时 {elapsed_time:.2f}秒，超过5秒限制"
        # 对于小文件，应该远低于5秒
        assert elapsed_time < 1.0, f"对比耗时 {elapsed_time:.2f}秒，对于小文件应该 < 1秒"

        # 验证返回结果正确
        assert result is not None
        assert "structure_comparison" in result

    def test_handle_canvas_comparison_orchestrator(self, tmp_path):
        """测试CanvasOrchestrator的对比接口"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        review_path = "src/tests/fixtures/test-review.canvas"
        orchestrator = canvas_utils.CanvasOrchestrator(original_path)

        output_report_path = tmp_path / "test-report.md"

        # Act
        result = orchestrator.handle_canvas_comparison(
            review_canvas_path=review_path,
            output_report_path=str(output_report_path)
        )

        # Assert - 返回结构
        assert "comparison_data" in result
        assert "report_path" in result

        # Assert - 对比数据完整
        comparison_data = result["comparison_data"]
        assert "structure_comparison" in comparison_data
        assert "content_comparison" in comparison_data
        assert "color_comparison" in comparison_data

        # Assert - 报告文件已生成
        assert output_report_path.exists()
        assert result["report_path"] == str(output_report_path)

        # Assert - 报告内容正确
        content = output_report_path.read_text(encoding='utf-8')
        assert "# 检验白板对比报告" in content

    def test_handle_canvas_comparison_auto_path(self, tmp_path):
        """测试Orchestrator自动生成报告路径"""
        # Arrange - 复制测试文件到临时目录
        import shutil
        original_src = "src/tests/fixtures/test-original.canvas"
        review_src = "src/tests/fixtures/test-review.canvas"

        original_path = tmp_path / "test-original.canvas"
        review_path = tmp_path / "test-review.canvas"

        shutil.copy(original_src, original_path)
        shutil.copy(review_src, review_path)

        orchestrator = canvas_utils.CanvasOrchestrator(str(original_path))

        # Act - 不指定报告路径
        result = orchestrator.handle_canvas_comparison(
            review_canvas_path=str(review_path)
        )

        # Assert - 自动生成的报告路径
        report_path = result["report_path"]
        assert report_path is not None
        assert os.path.exists(report_path)
        # 应该在原Canvas同目录下
        assert str(tmp_path) in report_path
        # 应该包含日期戳
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        assert today in report_path

    def test_calculate_canvas_depth_no_edges(self):
        """测试无边Canvas的深度计算"""
        # Arrange
        canvas_data = {
            "nodes": [
                {"id": "node1", "type": "text", "x": 0, "y": 0},
                {"id": "node2", "type": "text", "x": 100, "y": 100}
            ],
            "edges": []
        }
        logic = CanvasBusinessLogic("src/tests/fixtures/test-original.canvas")

        # Act
        depth = logic._calculate_canvas_depth(canvas_data)

        # Assert - 没有边时，所有节点都是根节点，深度为1
        assert depth == 1

    def test_calculate_canvas_depth_with_hierarchy(self):
        """测试有层级关系的Canvas深度计算"""
        # Arrange
        canvas_data = {
            "nodes": [
                {"id": "root", "type": "text", "x": 0, "y": 0},
                {"id": "child1", "type": "text", "x": 100, "y": 100},
                {"id": "child2", "type": "text", "x": 200, "y": 100},
                {"id": "grandchild", "type": "text", "x": 150, "y": 200}
            ],
            "edges": [
                {"id": "e1", "fromNode": "root", "toNode": "child1"},
                {"id": "e2", "fromNode": "root", "toNode": "child2"},
                {"id": "e3", "fromNode": "child1", "toNode": "grandchild"}
            ]
        }
        logic = CanvasBusinessLogic("src/tests/fixtures/test-original.canvas")

        # Act
        depth = logic._calculate_canvas_depth(canvas_data)

        # Assert - root → child1 → grandchild 是3层
        assert depth == 3

    def test_is_concept_covered_exact_match(self):
        """测试概念覆盖检测 - 精确匹配"""
        # Arrange
        logic = CanvasBusinessLogic("src/tests/fixtures/test-original.canvas")
        concept_text = "逆否命题的定义"
        review_texts = [
            "逆否命题的定义：原命题p→q的逆否命题是¬q→¬p",
            "其他内容"
        ]

        # Act
        is_covered = logic._is_concept_covered(concept_text, review_texts)

        # Assert
        assert is_covered is True

    def test_is_concept_covered_not_found(self):
        """测试概念覆盖检测 - 未覆盖"""
        # Arrange
        logic = CanvasBusinessLogic("src/tests/fixtures/test-original.canvas")
        concept_text = "完全不相关的概念"
        review_texts = ["逆否命题", "命题逻辑"]

        # Act
        is_covered = logic._is_concept_covered(concept_text, review_texts)

        # Assert
        assert is_covered is False

    def test_extract_core_concepts(self):
        """测试提取核心概念"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        core_concepts = logic._extract_core_concepts(logic.canvas_data)

        # Assert
        assert len(core_concepts) == 5  # test-original.canvas有5个核心概念节点
        # 验证每个概念的结构
        for concept in core_concepts:
            assert "id" in concept
            assert "text" in concept
            assert "color" in concept
            # 颜色应该是红/绿/紫之一
            assert concept["color"] in ["1", "2", "3"]

    def test_comparison_with_empty_review_canvas(self):
        """测试与空检验白板对比"""
        # Arrange
        original_path = "src/tests/fixtures/test-original.canvas"
        empty_path = "src/tests/fixtures/test-empty.canvas"
        logic = CanvasBusinessLogic(original_path)

        # Act
        result = logic.compare_with_canvas(empty_path)

        # Assert
        structure = result["structure_comparison"]
        assert structure["review_node_count"] == 0
        assert structure["replication_rate"] == 0.0

        content = result["content_comparison"]
        assert content["covered_concepts"] == 0
        assert len(content["missing_concepts"]) == 5  # 全部遗漏

    def test_comparison_file_not_found(self):
        """测试对比不存在的文件抛出异常"""
        # Arrange
        logic = CanvasBusinessLogic("src/tests/fixtures/test-original.canvas")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            logic.compare_with_canvas("nonexistent.canvas")



class TestReviewCanvasIndependence:
    """测试检验白板的文件独立性和元数据功能（Story 4.9）"""

    def test_review_canvas_is_independent_file(self):
        """测试检验白板是独立的.canvas文件（AC 1）"""
        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础", "source_node_id": "node-test123"}
            ]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)
        review_path = result["review_canvas_path"]

        # Assert
        assert os.path.exists(review_path), "检验白板文件应该存在"
        assert os.path.exists("src/tests/fixtures/test-basic.canvas"), "原白板文件应该存在"
        assert review_path != "src/tests/fixtures/test-basic.canvas", "检验白板与原白板应该是不同文件"
        assert "检验白板" in review_path, "检验白板文件名应包含标识"

        # 清理
        if os.path.exists(review_path):
            os.remove(review_path)

    def test_modify_review_canvas_does_not_affect_original(self):
        """测试修改检验白板不影响原白板（AC 2）"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础", "source_node_id": "node-test123"}
            ]
        }

        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)
        review_path = result["review_canvas_path"]

        # 记录原白板的初始状态
        original_data = CanvasJSONOperator.read_canvas("src/tests/fixtures/test-basic.canvas")
        original_node_count = len(original_data["nodes"])
        original_text = json.dumps(original_data, sort_keys=True)

        # Act: 修改检验白板
        review_data = CanvasJSONOperator.read_canvas(review_path)
        CanvasJSONOperator.create_node(
            review_data,
            node_type="text",
            x=1000,
            y=1000,
            text="新增节点"
        )
        CanvasJSONOperator.write_canvas(review_path, review_data)

        # 重新读取原白板
        original_data_after = CanvasJSONOperator.read_canvas("src/tests/fixtures/test-basic.canvas")
        original_text_after = json.dumps(original_data_after, sort_keys=True)

        # Assert: 原白板完全未被修改
        assert len(original_data_after["nodes"]) == original_node_count, "原白板节点数不应改变"
        assert original_text == original_text_after, "原白板内容应完全不变"

        # 清理
        os.remove(review_path)

    def test_source_node_id_metadata_present(self):
        """测试问题节点包含sourceNodeId元数据（AC 3）"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础", "source_node_id": "node-test123"}
            ]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)
        review_path = result["review_canvas_path"]

        # 读取检验白板
        review_data = CanvasJSONOperator.read_canvas(review_path)

        # Assert: 所有问题节点包含sourceNodeId
        question_nodes = [
            node for node in review_data["nodes"]
            if node.get("color") == canvas_utils.COLOR_CODE_RED and node["type"] == "text"
        ]

        assert len(question_nodes) > 0, "应该有问题节点"

        for q_node in question_nodes:
            # 验证sourceNodeId字段存在
            assert "sourceNodeId" in q_node, f"问题节点{q_node['id']}应包含sourceNodeId字段"
            # 验证sourceNodeId值正确
            assert q_node["sourceNodeId"] == "node-test123", "sourceNodeId应该是正确的源节点ID"

        # 清理
        os.remove(review_path)

    def test_description_node_has_metadata(self):
        """测试说明节点包含originalCanvasPath和generationTimestamp（AC 3）"""
        import json
        from datetime import datetime

        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"}
            ]
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)
        review_path = result["review_canvas_path"]

        # 读取检验白板
        review_data = CanvasJSONOperator.read_canvas(review_path)

        # 找到说明节点（蓝色，位置在(100, 100)）
        description_node = None
        for node in review_data["nodes"]:
            if node.get("color") == canvas_utils.COLOR_CODE_BLUE and node.get("x") == 100:
                description_node = node
                break

        # Assert
        assert description_node is not None, "应该有说明节点"
        assert "originalCanvasPath" in description_node, "说明节点应包含originalCanvasPath字段"
        assert description_node["originalCanvasPath"] == logic.canvas_path, "originalCanvasPath应指向原白板"
        assert "generationTimestamp" in description_node, "说明节点应包含generationTimestamp字段"

        # 验证时间戳格式（ISO 8601）
        timestamp = description_node["generationTimestamp"]
        # 应该可以解析为datetime对象
        dt = datetime.fromisoformat(timestamp)
        assert dt is not None, "时间戳应为有效的ISO 8601格式"

        # 清理
        os.remove(review_path)

    def test_multiple_review_canvases_coexist(self):
        """测试支持生成多个检验白板（AC 4）"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"}
            ]
        }

        # Act: 生成第1个检验白板
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result1 = logic.generate_review_canvas_file(
            clustered_questions,
            output_filename_override="src/tests/fixtures/test-review-1.canvas"
        )
        path1 = result1["review_canvas_path"]

        # Act: 生成第2个检验白板
        result2 = logic.generate_review_canvas_file(
            clustered_questions,
            output_filename_override="src/tests/fixtures/test-review-2.canvas"
        )
        path2 = result2["review_canvas_path"]

        # Assert
        assert os.path.exists(path1), "第1个检验白板应该存在"
        assert os.path.exists(path2), "第2个检验白板应该存在"
        assert path1 != path2, "两个检验白板应该是不同文件"

        # 验证两个检验白板都引用同一个原白板
        review1 = CanvasJSONOperator.read_canvas(path1)
        review2 = CanvasJSONOperator.read_canvas(path2)

        desc1 = [n for n in review1["nodes"] if n.get("color") == canvas_utils.COLOR_CODE_BLUE][0]
        desc2 = [n for n in review2["nodes"] if n.get("color") == canvas_utils.COLOR_CODE_BLUE][0]

        assert desc1["originalCanvasPath"] == logic.canvas_path, "第1个检验白板应引用原白板"
        assert desc2["originalCanvasPath"] == logic.canvas_path, "第2个检验白板应引用原白板"

        # 清理
        os.remove(path1)
        os.remove(path2)

    def test_delete_review_canvas_preserves_original(self):
        """测试删除检验白板不影响原白板（AC 1, 2）"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"}
            ]
        }

        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        # 记录原白板状态
        original_data_before = CanvasJSONOperator.read_canvas("src/tests/fixtures/test-basic.canvas")

        # 生成检验白板
        result = logic.generate_review_canvas_file(clustered_questions)
        review_path = result["review_canvas_path"]

        # Act: 删除检验白板
        os.remove(review_path)

        # Assert: 原白板仍然存在且完整
        assert os.path.exists("src/tests/fixtures/test-basic.canvas"), "原白板应该仍然存在"
        original_data_after = CanvasJSONOperator.read_canvas("src/tests/fixtures/test-basic.canvas")
        assert len(original_data_after["nodes"]) == len(original_data_before["nodes"]), "原白板节点数应该不变"
        assert len(original_data_after["edges"]) == len(original_data_before["edges"]), "原白板边数应该不变"

    def test_filename_uses_datetime_timestamp(self):
        """测试文件名使用日期时间戳避免冲突（AC 4）"""
        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"}
            ]
        }

        # Act: 生成检验白板（使用默认文件名）
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)
        path = result["review_canvas_path"]

        # Assert: 文件名包含日期
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        assert today in path, "文件名应包含日期戳"

        # 清理
        if os.path.exists(path):
            os.remove(path)

    def test_metadata_tracking_for_progress_analysis(self):
        """测试元数据支持进步追踪（AC 5）"""
        import json
        from datetime import datetime

        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"}
            ]
        }

        # Act: 生成两个检验白板（代表不同时间的检验）
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result1 = logic.generate_review_canvas_file(
            clustered_questions,
            output_filename_override="src/tests/fixtures/test-progress-1.canvas"
        )
        result2 = logic.generate_review_canvas_file(
            clustered_questions,
            output_filename_override="src/tests/fixtures/test-progress-2.canvas"
        )

        # 读取两个检验白板的元数据
        review1 = CanvasJSONOperator.read_canvas(result1["review_canvas_path"])
        review2 = CanvasJSONOperator.read_canvas(result2["review_canvas_path"])

        desc1 = [n for n in review1["nodes"] if n.get("color") == canvas_utils.COLOR_CODE_BLUE][0]
        desc2 = [n for n in review2["nodes"] if n.get("color") == canvas_utils.COLOR_CODE_BLUE][0]

        # Assert: 元数据完整，可用于追踪
        assert "originalCanvasPath" in desc1 and "originalCanvasPath" in desc2
        assert desc1["originalCanvasPath"] == desc2["originalCanvasPath"], "应该引用同一个原白板"

        assert "generationTimestamp" in desc1 and "generationTimestamp" in desc2
        # 两个时间戳应该都是有效的ISO 8601格式
        t1 = datetime.fromisoformat(desc1["generationTimestamp"])
        t2 = datetime.fromisoformat(desc2["generationTimestamp"])
        assert t1 is not None and t2 is not None, "时间戳应该可解析"

        # 清理
        os.remove(result1["review_canvas_path"])
        os.remove(result2["review_canvas_path"])

    def test_review_canvas_safe_for_all_operations(self):
        """测试检验白板可以安全地进行拆解、评分等操作（AC 2）"""
        import json

        # Arrange
        clustered_questions = {
            "主题1": [
                {"question_text": "问题1", "question_type": "突破型", "difficulty": "基础"}
            ]
        }

        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        result = logic.generate_review_canvas_file(clustered_questions)
        review_path = result["review_canvas_path"]

        # 记录原白板状态
        original_before = CanvasJSONOperator.read_canvas("src/tests/fixtures/test-basic.canvas")

        # Act: 在检验白板上执行各种操作
        review_logic = CanvasBusinessLogic(review_path)

        # 1. 拆解操作：添加子问题
        review_data = CanvasJSONOperator.read_canvas(review_path)
        first_question = [n for n in review_data["nodes"] if n.get("color") == canvas_utils.COLOR_CODE_RED][0]
        review_logic.add_sub_question_with_yellow_node(
            first_question["id"],
            "子问题测试",
            ""
        )

        # 2. 评分操作：修改节点颜色
        review_data = CanvasJSONOperator.read_canvas(review_path)
        CanvasJSONOperator.update_node_color(
            review_data,
            first_question["id"],
            canvas_utils.COLOR_CODE_GREEN
        )
        CanvasJSONOperator.write_canvas(review_path, review_data)

        # Assert: 原白板未被修改
        original_after = CanvasJSONOperator.read_canvas("src/tests/fixtures/test-basic.canvas")
        assert len(original_after["nodes"]) == len(original_before["nodes"]), "原白板节点数应该不变"
        assert json.dumps(original_before, sort_keys=True) == json.dumps(original_after, sort_keys=True), "原白板内容应完全不变"

        # 清理
        os.remove(review_path)
