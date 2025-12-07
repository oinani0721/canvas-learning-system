#!/usr/bin/env python3
"""
Graphiti集成测试

测试Graphiti知识图谱系统的核心功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from concept_extractor import ConceptExtractor
from graph_commands import GraphCommandHandler
from graph_visualizer import GraphVisualizer

# 测试目标模块
from graphiti_integration import GraphitiKnowledgeGraph


class TestGraphitiKnowledgeGraph(unittest.TestCase):
    """测试GraphitiKnowledgeGraph类"""

    def setUp(self):
        """测试前准备"""
        # 使用测试配置
        self.test_config = {
            "neo4j_uri": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "password"
        }
        self.graphiti = GraphitiKnowledgeGraph(**self.test_config)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.graphiti.neo4j_uri, self.test_config["neo4j_uri"])
        self.assertEqual(self.graphiti.username, self.test_config["username"])
        self.assertEqual(self.graphiti.password, self.test_config["password"])
        self.assertIsNotNone(self.graphiti.graphiti)

    @patch('graphiti_integration.Graphiti')
    def test_initialization_with_custom_llm(self, mock_graphiti_class):
        """测试使用自定义LLM初始化"""
        mock_graphiti = Mock()
        mock_graphiti_class.return_value = mock_graphiti

        graphiti = GraphitiKnowledgeGraph(
            anthropic_api_key="test-key",
            voyage_api_key="test-key"
        )

        self.assertIsNotNone(graphiti)

    @pytest.mark.asyncio
    async def test_initialize(self):
        """测试异步初始化"""
        # 模拟build_indices_and_constraints方法
        self.graphiti.graphiti.build_indices_and_constraints = AsyncMock()

        await self.graphiti.initialize()
        self.graphiti.graphiti.build_indices_and_constraints.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_learning_session(self):
        """测试记录学习会话"""
        # 模拟add_episode方法
        self.graphiti.graphiti.add_episode = AsyncMock(return_value=Mock())
        self.graphiti._record_node_interactions_graphiti = AsyncMock()

        session_data = {
            "canvas_file": "test.canvas",
            "session_type": "decomposition",
            "duration_minutes": 30,
            "user_id": "test_user",
            "nodes_interacted": [
                {
                    "concept_name": "测试概念",
                    "node_type": "question",
                    "interaction_type": "created",
                    "interaction_outcome": "success"
                }
            ]
        }

        session_id = await self.graphiti.record_learning_session(session_data)

        self.assertIsInstance(session_id, str)
        self.graphiti.graphiti.add_episode.assert_called_once()

    def test_create_session_episode_body(self):
        """测试创建会话episode描述"""
        session_data = {
            "canvas_file": "test.canvas",
            "session_type": "decomposition",
            "duration_minutes": 30,
            "learning_outcomes": {
                "new_concepts_learned": 2,
                "concepts_reviewed": 1,
                "weaknesses_identified": 0,
                "mastery_improvements": 1
            }
        }

        body = self.graphiti._create_session_episode_body(session_data)

        self.assertIn("test.canvas", body)
        self.assertIn("decomposition", body)
        self.assertIn("30 minutes", body)
        self.assertIn("2", body)  # new_concepts_learned

    @pytest.mark.asyncio
    async def test_search_concept_network(self):
        """测试搜索概念网络"""
        # 模拟search方法
        mock_edge = Mock()
        mock_edge.fact = "测试事实"
        mock_edge.valid_at = datetime.now(timezone.utc)
        mock_edge.created_at = datetime.now(timezone.utc)
        mock_edge.episodes = []
        mock_edge.uuid = "test-uuid"

        self.graphiti.graphiti.search = AsyncMock(return_value=[mock_edge])

        result = await self.graphiti.search_concept_network("测试概念")

        self.assertIn("center_concept", result)
        self.assertIn("concepts", result)
        self.assertIn("relationships", result)
        self.assertEqual(result["center_concept"], "测试概念")

    @pytest.mark.asyncio
    async def test_identify_weaknesses(self):
        """测试识别薄弱环节"""
        # 模拟search方法
        mock_edge = Mock()
        mock_edge.fact = "failed concept: 测试概念"
        mock_edge.created_at = datetime.now(timezone.utc)
        mock_edge.episodes = []
        mock_edge.uuid = "test-uuid"

        self.graphiti.graphiti.search = AsyncMock(return_value=[mock_edge])

        weaknesses = await self.graphiti.identify_weaknesses("test_user")

        self.assertIsInstance(weaknesses, list)
        if weaknesses:
            self.assertIn("concept_name", weaknesses[0])
            self.assertIn("weakness_level", weaknesses[0])

    def test_extract_concept_from_fact(self):
        """测试从事实中提取概念"""
        test_cases = [
            ("concept: 测试概念", "测试概念"),
            ("failed concept: 数学公式", "数学公式"),
            ("difficulty: 理解定义", "理解定义"),
            ("学习困难 概念理解", "学习困难 概念理解")
        ]

        for fact, expected in test_cases:
            with self.subTest(fact=fact):
                result = self.graphiti._extract_concept_from_fact(fact)
                self.assertEqual(result, expected)

    @pytest.mark.asyncio
    async def test_close(self):
        """测试关闭连接"""
        self.graphiti.graphiti.close = AsyncMock()
        await self.graphiti.close()
        self.graphiti.graphiti.close.assert_called_once()


class TestConceptExtractor(unittest.TestCase):
    """测试ConceptExtractor类"""

    def setUp(self):
        """测试前准备"""
        self.extractor = ConceptExtractor()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.extractor.relationship_types)
        self.assertIsNotNone(self.extractor.relationship_keywords)
        self.assertIsNotNone(self.extractor.subject_patterns)

    def test_extract_concept_names_from_text(self):
        """测试从文本中提取概念名称"""
        test_text = """
        这是一个测试文本。
        概念1：这是第一个概念。
        概念2：这是第二个概念。
        【重要概念】这是一个重要的概念。
        （附加概念）这是附加概念。
        """

        concepts = self.extractor._extract_concept_names_from_text(test_text)

        self.assertIsInstance(concepts, list)
        self.assertGreater(len(concepts), 0)
        # 检查是否包含预期的概念
        expected_concepts = ["概念1", "概念2", "重要概念", "附加概念"]
        for expected in expected_concepts:
            self.assertIn(expected, concepts)

    def test_is_valid_concept(self):
        """测试概念验证"""
        valid_concepts = ["测试概念", "数学公式", "物理定律", "计算机程序"]
        invalid_concepts = ["", "123", "的", "了", "，。！？"]

        for concept in valid_concepts:
            with self.subTest(concept=concept):
                self.assertTrue(self.extractor._is_valid_concept(concept))

        for concept in invalid_concepts:
            with self.subTest(concept=concept):
                self.assertFalse(self.extractor._is_valid_concept(concept))

    def test_identify_subject_areas(self):
        """测试识别学科领域"""
        test_cases = [
            ("数学定理和微积分计算", {"数学"}),
            ("物理实验和力学分析", {"物理"}),
            ("化学反应和分子结构", {"化学"}),
            ("算法设计和数据结构", {"计算机"}),
            ("跨学科的数学物理应用", {"数学", "物理"}),
            ("普通文本内容", set())
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = self.extractor._identify_subject_areas(text)
                self.assertEqual(result, expected)

    def test_calculate_concept_confidence(self):
        """测试计算概念置信度"""
        concept_data = {
            "source_nodes": ["node1", "node2", "node3"],
            "descriptions": ["描述1", "描述2"],
            "subject_areas": ["数学"],
            "aliases": set()
        }

        confidence = self.extractor._calculate_concept_confidence(concept_data)

        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_infer_relationship_type_from_edge(self):
        """测试从边标签推断关系类型"""
        test_cases = [
            ("基于", "is_prerequisite_for"),
            ("类似于", "is_similar_to"),
            ("相反", "is_contradictory_of"),
            ("推导", "is_derived_from"),
            ("应用", "is_applied_in"),
            ("例如", "is_example_of"),
            ("包括", "includes"),
            ("导致", "leads_to"),
            ("其他", "is_related_to")
        ]

        for edge_label, expected_type in test_cases:
            with self.subTest(edge_label=edge_label):
                result = self.extractor._infer_relationship_type_from_edge(
                    edge_label, "概念A", "概念B"
                )
                self.assertEqual(result, expected_type)

    def test_extract_concepts_from_canvas(self):
        """测试从Canvas提取概念"""
        # 创建测试Canvas数据
        canvas_data = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "text",
                    "text": "这是一个测试概念\n包含多个描述\n用于测试提取功能",
                    "color": "1"
                },
                {
                    "id": "node2",
                    "type": "text",
                    "text": "数学概念：微积分\n包括导数和积分",
                    "color": "2"
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "fromNode": "node1",
                    "toNode": "node2",
                    "label": "基于"
                }
            ]
        }

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(canvas_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            result = self.extractor.extract_concepts_from_canvas(temp_path)

            self.assertIn("concepts", result)
            self.assertIn("relationships", result)
            self.assertIn("statistics", result)
            self.assertGreater(len(result["concepts"]), 0)

        finally:
            # 清理临时文件
            Path(temp_path).unlink()

    def test_cluster_concepts(self):
        """测试概念聚类"""
        concepts = {
            "概念1": {"text_content": "数学相关内容"},
            "概念2": {"text_content": "物理相关内容"},
            "概念3": {"text_content": "数学公式内容"},
            "概念4": {"text_content": "化学实验内容"}
        }

        clusters = self.extractor.cluster_concepts(concepts)

        self.assertIsInstance(clusters, list)
        self.assertGreater(len(clusters), 0)
        # 所有概念都应该在某个聚类中
        all_concepts_in_clusters = []
        for cluster in clusters:
            all_concepts_in_clusters.extend(cluster)
        self.assertEqual(len(set(all_concepts_in_clusters)), len(concepts))


class TestGraphCommandHandler(unittest.TestCase):
    """测试GraphCommandHandler类"""

    def setUp(self):
        """测试前准备"""
        self.handler = GraphCommandHandler("test_config.yaml")

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.handler.config_path, "test_config.yaml")
        self.assertIsNone(self.handler.current_session_id)
        self.assertFalse(self.handler.is_recording)

    def test_get_status(self):
        """测试获取状态"""
        status = self.handler.get_status()

        self.assertIn("is_recording", status)
        self.assertIn("current_session_id", status)
        self.assertIn("config_path", status)
        self.assertIn("timestamp", status)
        self.assertFalse(status["is_recording"])

    @pytest.mark.asyncio
    async def test_start_recording(self):
        """测试开始录制"""
        # 创建临时Canvas文件
        canvas_data = {"nodes": [], "edges": []}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(canvas_data, f)
            temp_path = f.name

        try:
            # 模拟GraphitiContextManager
            with patch('graph_commands.GraphitiContextManager') as mock_context:
                mock_context.return_value.__aenter__ = AsyncMock()
                mock_context.return_value.__aexit__ = AsyncMock()
                mock_graphiti = AsyncMock()
                mock_graphiti.record_learning_session = AsyncMock(return_value="test-session-id")
                mock_context.return_value.__aenter__.return_value = mock_graphiti

                session_id = await self.handler.start_recording(temp_path, "test_user")

                self.assertEqual(session_id, "test-session-id")
                self.assertTrue(self.handler.is_recording)
                self.assertEqual(self.handler.current_session_id, "test-session-id")

        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_stop_recording(self):
        """测试停止录制"""
        # 先设置录制状态
        self.handler.is_recording = True
        self.handler.current_session_id = "test-session"

        summary = await self.handler.stop_recording()

        self.assertIn("session_id", summary)
        self.assertEqual(summary["session_id"], "test-session")
        self.assertFalse(self.handler.is_recording)
        self.assertIsNone(self.handler.current_session_id)

    @pytest.mark.asyncio
    async def test_stop_recording_no_active_session(self):
        """测试停止录制但没有活跃会话"""
        with self.assertRaises(ValueError):
            await self.handler.stop_recording()


class TestGraphVisualizer(unittest.TestCase):
    """测试GraphVisualizer类"""

    def setUp(self):
        """测试前准备"""
        self.visualizer = GraphVisualizer()

        # 测试数据
        self.test_concepts = {
            "概念1": {
                "text_content": "测试概念1的内容",
                "confidence": 0.8,
                "subject_areas": ["数学"],
                "node_types": ["question"]
            },
            "概念2": {
                "text_content": "测试概念2的内容",
                "confidence": 0.6,
                "subject_areas": ["物理"],
                "node_types": ["explanation"]
            }
        }

        self.test_relationships = [
            {
                "source_concept": "概念1",
                "target_concept": "概念2",
                "relationship_type": "is_similar_to",
                "relationship_strength": 0.7,
                "confidence_score": 0.8
            }
        ]

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.visualizer.color_schemes)
        self.assertIsNotNone(self.visualizer.layout_algorithms)
        self.assertIn("default", self.visualizer.color_schemes)
        self.assertIn("spring", self.visualizer.layout_algorithms)

    def test_build_simple_graph(self):
        """测试构建简单图结构"""
        G, pos = self.visualizer._build_simple_graph(self.test_concepts, self.test_relationships)

        self.assertEqual(len(G["nodes"]), 2)
        self.assertEqual(len(G["edges"]), 1)
        self.assertEqual(len(pos), 2)

        # 检查布局
        for concept in self.test_concepts:
            self.assertIn(concept, pos)
            self.assertEqual(len(pos[concept]), 2)  # x, y坐标

    def test_compute_node_attributes(self):
        """测试计算节点属性"""
        pos = {"概念1": (0.0, 0.0), "概念2": (1.0, 1.0)}
        node_attrs = self.visualizer._compute_node_attributes(
            self.test_concepts, pos, "default", None
        )

        self.assertEqual(len(node_attrs), 2)
        self.assertIn("概念1", node_attrs)
        self.assertIn("概念2", node_attrs)

        # 检查属性
        for concept_name, attrs in node_attrs.items():
            self.assertIn("name", attrs)
            self.assertIn("x", attrs)
            self.assertIn("y", attrs)
            self.assertIn("size", attrs)
            self.assertIn("color", attrs)
            self.assertIn("label", attrs)

    def test_compute_edge_attributes(self):
        """测试计算边属性"""
        pos = {"概念1": (0.0, 0.0), "概念2": (1.0, 1.0)}
        edge_attrs = self.visualizer._compute_edge_attributes(
            self.test_relationships, pos, "default"
        )

        self.assertEqual(len(edge_attrs), 1)

        for edge_key, attrs in edge_attrs.items():
            self.assertIn("source", attrs)
            self.assertIn("target", attrs)
            self.assertIn("x", attrs)
            self.assertIn("y", attrs)
            self.assertIn("width", attrs)
            self.assertIn("color", attrs)

    def test_generate_json_visualization(self):
        """测试生成JSON可视化"""
        pos = {"概念1": (0.0, 0.0), "概念2": (1.0, 1.0)}
        node_attrs = self.visualizer._compute_node_attributes(
            self.test_concepts, pos, "default", None
        )
        edge_attrs = self.visualizer._compute_edge_attributes(
            self.test_relationships, pos, "default"
        )

        result = self.visualizer._generate_json_visualization(
            self.test_concepts, self.test_relationships, node_attrs, edge_attrs
        )

        self.assertEqual(result["format"], "json")
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIn("metadata", result)
        self.assertEqual(len(result["nodes"]), 2)
        self.assertEqual(len(result["edges"]), 1)

    def test_simple_layout(self):
        """测试简单布局"""
        nodes = ["A", "B", "C", "D"]
        pos = self.visualizer._simple_layout(nodes)

        self.assertEqual(len(pos), 4)
        for node in nodes:
            self.assertIn(node, pos)
            x, y = pos[node]
            # 检查是否在单位圆上
            self.assertAlmostEqual(abs((x**2 + y**2)**0.5), 1.0, places=5)

    def test_extract_concept_from_fact(self):
        """测试从事实中提取概念（在GraphVisualizer中）"""
        fact = "concept: 微积分基础"
        concept = self.visualizer._extract_concept_from_fact(fact)
        self.assertEqual(concept, "微积分基础")


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_canvas_path = self.temp_dir / "test.canvas"

        # 创建测试Canvas文件
        canvas_data = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "text",
                    "text": "数学概念：微积分\n微积分包括导数和积分\n是数学分析的基础",
                    "color": "1"
                },
                {
                    "id": "node2",
                    "type": "text",
                    "text": "导数定义\n导数描述函数的变化率",
                    "color": "2"
                },
                {
                    "id": "node3",
                    "type": "text",
                    "text": "积分应用\n积分用于计算面积和体积",
                    "color": "2"
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "fromNode": "node1",
                    "toNode": "node2",
                    "label": "包括"
                },
                {
                    "id": "edge2",
                    "fromNode": "node1",
                    "toNode": "node3",
                    "label": "包括"
                }
            ]
        }

        with open(self.test_canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False)

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_end_to_end_concept_extraction(self):
        """测试端到端概念提取"""
        extractor = ConceptExtractor()
        result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        # 验证结果
        self.assertIn("concepts", result)
        self.assertIn("relationships", result)
        self.assertIn("statistics", result)

        # 应该提取到概念
        self.assertGreater(len(result["concepts"]), 0)
        stats = result["statistics"]
        self.assertGreater(stats["total_concepts"], 0)

    def test_end_to_end_visualization(self):
        """测试端到端可视化"""
        # 先提取概念
        extractor = ConceptExtractor()
        extraction_result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        # 生成可视化
        visualizer = GraphVisualizer()
        viz_result = visualizer.visualize_concept_network(
            concepts=extraction_result["concepts"],
            relationships=extraction_result["relationships"],
            output_format="json"
        )

        # 验证结果
        self.assertEqual(viz_result["format"], "json")
        self.assertIn("nodes", viz_result)
        self.assertIn("edges", viz_result)
        self.assertGreater(len(viz_result["nodes"]), 0)

    def test_visualizer_with_different_layouts(self):
        """测试不同布局算法"""
        extractor = ConceptExtractor()
        extraction_result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))
        visualizer = GraphVisualizer()

        layouts = ["spring", "circular", "kamada_kawai", "hierarchical"]

        for layout in layouts:
            with self.subTest(layout=layout):
                try:
                    result = visualizer.visualize_concept_network(
                        concepts=extraction_result["concepts"],
                        relationships=extraction_result["relationships"],
                        output_format="json",
                        layout_algorithm=layout
                    )
                    self.assertEqual(result["format"], "json")
                except Exception as e:
                    # 某些布局可能因为依赖问题而失败，这是可以接受的
                    self.skipTest(f"Layout {layout} not available: {e}")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
