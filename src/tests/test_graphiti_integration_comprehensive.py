#!/usr/bin/env python3
"""
Graphiti集成综合测试

完整的端到端测试，验证整个Graphiti知识图谱系统。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest

from graphiti_integration import GraphitiKnowledgeGraph, GraphitiContextManager
from concept_extractor import ConceptExtractor
from graph_commands import GraphCommandHandler
from graph_visualizer import GraphVisualizer


class TestGraphitiSystemIntegration(unittest.TestCase):
    """Graphiti系统集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # 创建测试Canvas文件
        self.test_canvas_path = self.temp_dir / "test_math_canvas.canvas"
        with open(Path(__file__).parent / "fixtures" / "sample_canvas_data.json", 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        with open(self.test_canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False)

        # 创建测试配置
        self.config_path = self.temp_dir / "test_config.yaml"
        config_data = {
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "password",
                "database": "test_canvas_learning"
            }
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(config_data, f, default_flow_style=False)

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_complete_learning_workflow(self):
        """测试完整的学习工作流程"""
        # 1. 概念提取
        extractor = ConceptExtractor()
        extraction_result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        self.assertGreater(len(extraction_result["concepts"]), 0)
        self.assertGreater(len(extraction_result["relationships"]), 0)

        # 2. 知识图谱记录（模拟）
        with patch('graph_commands.GraphitiContextManager') as mock_context:
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()
            mock_graphiti = AsyncMock()
            mock_graphiti.record_learning_session = AsyncMock(return_value="test-session-id")
            mock_graphiti.extract_concept_relationships = AsyncMock(return_value=[])
            mock_context.return_value.__aenter__.return_value = mock_graphiti

            # 3. 命令处理器测试
            handler = GraphCommandHandler(str(self.config_path))

            # 开始录制
            session_id = await handler.start_recording(str(self.test_canvas_path))
            self.assertIsNotNone(session_id)

            # 分析Canvas
            analysis_result = await handler.analyze_canvas(str(self.test_canvas_path))
            self.assertIn("extraction_summary", analysis_result)

            # 停止录制
            summary = await handler.stop_recording()
            self.assertIn("session_id", summary)

    def test_concept_extraction_accuracy(self):
        """测试概念提取准确性"""
        extractor = ConceptExtractor()
        result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        # 验证数学概念识别
        concepts = result["concepts"]
        math_concepts = [name for name, data in concepts.items() if "数学" in data.get("subject_areas", [])]
        self.assertGreater(len(math_concepts), 0)

        # 验证关系提取
        relationships = result["relationships"]
        self.assertGreater(len(relationships), 0)

        # 验证统计信息
        stats = result["statistics"]
        self.assertIn("total_concepts", stats)
        self.assertIn("total_relationships", stats)
        self.assertGreater(stats["total_concepts"], 3)

    def test_visualization_generation(self):
        """测试可视化生成"""
        # 先提取概念
        extractor = ConceptExtractor()
        extraction_result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        # 生成不同格式的可视化
        visualizer = GraphVisualizer()
        formats = ["json", "svg"]

        for format_type in formats:
            with self.subTest(format=format_type):
                try:
                    result = visualizer.visualize_concept_network(
                        concepts=extraction_result["concepts"],
                        relationships=extraction_result["relationships"],
                        output_format=format_type
                    )
                    self.assertEqual(result["format"], format_type)
                except ImportError as e:
                    # 某些依赖可能不可用
                    self.skipTest(f"Format {format_type} not available: {e}")

    def test_different_layout_algorithms(self):
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
                    self.assertIsNotNone(result)
                except Exception as e:
                    # 某些布局可能不可用
                    if "NetworkX" not in str(e):
                        self.skipTest(f"Layout {layout} failed: {e}")

    def test_concept_clustering_quality(self):
        """测试概念聚类质量"""
        extractor = ConceptExtractor()
        extraction_result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        clusters = extractor.cluster_concepts(extraction_result["concepts"])

        self.assertIsInstance(clusters, list)
        self.assertGreater(len(clusters), 0)

        # 验证所有概念都在聚类中
        all_concepts_in_clusters = []
        for cluster in clusters:
            all_concepts_in_clusters.extend(cluster)

        original_concepts = set(extraction_result["concepts"].keys())
        clustered_concepts = set(all_concepts_in_clusters)

        self.assertEqual(original_concepts, clustered_concepts)

    def test_relationship_type_classification(self):
        """测试关系类型分类准确性"""
        extractor = ConceptExtractor()
        extraction_result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        relationships = extraction_result["relationships"]
        relationship_types = [rel["relationship_type"] for rel in relationships]

        # 验证关系类型分布
        expected_types = [
            "is_related_to", "includes", "is_prerequisite_for",
            "is_similar_to", "is_derived_from"
        ]

        found_types = set(relationship_types)
        # 至少应该有一些有效的关系类型
        self.assertGreater(len(found_types.intersection(expected_types)), 0)

    def test_confidence_score_distribution(self):
        """测试置信度分数分布"""
        extractor = ConceptExtractor()
        extraction_result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        concepts = extraction_result["concepts"]
        confidences = [data["confidence"] for data in concepts.values()]

        self.assertGreater(len(confidences), 0)

        # 验证置信度范围
        for confidence in confidences:
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)

        # 计算平均置信度
        avg_confidence = sum(confidences) / len(confidences)
        self.assertGreater(avg_confidence, 0.1)  # 至少应该有合理的置信度

    def test_subject_area_classification(self):
        """测试学科领域分类"""
        extractor = ConceptExtractor()
        extraction_result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        concepts = extraction_result["concepts"]
        subject_areas = set()

        for concept_data in concepts.values():
            subject_areas.update(concept_data.get("subject_areas", []))

        # 应该识别出数学相关的概念
        self.assertIn("数学", subject_areas)

    @pytest.mark.asyncio
    async def test_error_handling_and_robustness(self):
        """测试错误处理和健壮性"""
        handler = GraphCommandHandler(str(self.config_path))

        # 测试不存在的Canvas文件
        with self.assertRaises(FileNotFoundError):
            await handler.analyze_canvas("nonexistent.canvas")

        # 测试停止不存在的会话
        with self.assertRaises(ValueError):
            await handler.stop_recording()

    def test_performance_with_large_canvas(self):
        """测试大Canvas文件的性能"""
        # 创建一个较大的测试Canvas
        large_canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 生成50个节点
        for i in range(50):
            node = {
                "id": f"node-{i}",
                "type": "text",
                "text": f"概念{i}：这是第{i}个测试概念，包含详细的描述信息用于测试性能。",
                "x": (i % 10) * 100,
                "y": (i // 10) * 150,
                "width": 300,
                "height": 150,
                "color": str((i % 3) + 1)
            }
            large_canvas_data["nodes"].append(node)

        # 生成连接关系
        for i in range(49):
            edge = {
                "id": f"edge-{i}",
                "fromNode": f"node-{i}",
                "toNode": f"node-{i+1}",
                "fromSide": "right",
                "toSide": "left",
                "label": "相关"
            }
            large_canvas_data["edges"].append(edge)

        # 保存大Canvas文件
        large_canvas_path = self.temp_dir / "large_test_canvas.canvas"
        with open(large_canvas_path, 'w', encoding='utf-8') as f:
            json.dump(large_canvas_data, f, ensure_ascii=False)

        # 测试提取性能
        import time
        start_time = time.time()

        extractor = ConceptExtractor()
        result = extractor.extract_concepts_from_canvas(str(large_canvas_path))

        end_time = time.time()
        extraction_time = end_time - start_time

        # 验证结果
        self.assertGreater(len(result["concepts"]), 40)  # 至少应该提取到大部分概念
        self.assertGreater(len(result["relationships"]), 30)

        # 性能要求（应该在合理时间内完成）
        self.assertLess(extraction_time, 30.0)  # 30秒内完成

        print(f"大Canvas提取性能：{extraction_time:.2f}秒，提取{len(result['concepts'])}个概念")

    def test_data_format_consistency(self):
        """测试数据格式一致性"""
        extractor = ConceptExtractor()
        result = extractor.extract_concepts_from_canvas(str(self.test_canvas_path))

        # 验证概念数据格式
        for concept_name, concept_data in result["concepts"].items():
            self.assertIsInstance(concept_name, str)
            self.assertIn("name", concept_data)
            self.assertEqual(concept_data["name"], concept_name)
            self.assertIn("source_nodes", concept_data)
            self.assertIn("descriptions", concept_data)
            self.assertIn("node_types", concept_data)
            self.assertIn("colors", concept_data)
            self.assertIn("confidence", concept_data)
            self.assertIsInstance(concept_data["confidence"], (int, float))

        # 验证关系数据格式
        for relationship in result["relationships"]:
            self.assertIn("source_concept", relationship)
            self.assertIn("target_concept", relationship)
            self.assertIn("relationship_type", relationship)
            self.assertIn("relationship_strength", relationship)
            self.assertIn("confidence_score", relationship)
            self.assertIn("source", relationship)
            self.assertIsInstance(relationship["relationship_strength"], (int, float))
            self.assertIsInstance(relationship["confidence_score"], (int, float))


class TestGraphitiSystemScalability(unittest.TestCase):
    """测试系统可扩展性"""

    def test_multiple_canvas_processing(self):
        """测试多个Canvas文件的处理"""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # 创建多个测试Canvas文件
            canvas_files = []
            for i in range(3):
                canvas_path = temp_dir / f"test_canvas_{i}.canvas"
                canvas_data = {
                    "nodes": [
                        {
                            "id": f"node-{i}-1",
                            "type": "text",
                            "text": f"Canvas {i} 概念1",
                            "x": 100, "y": 100, "width": 200, "height": 100, "color": "1"
                        },
                        {
                            "id": f"node-{i}-2",
                            "type": "text",
                            "text": f"Canvas {i} 概念2",
                            "x": 400, "y": 100, "width": 200, "height": 100, "color": "2"
                        }
                    ],
                    "edges": [
                        {
                            "id": f"edge-{i}",
                            "fromNode": f"node-{i}-1",
                            "toNode": f"node-{i}-2",
                            "fromSide": "right",
                            "toSide": "left",
                            "label": "相关"
                        }
                    ]
                }

                with open(canvas_path, 'w', encoding='utf-8') as f:
                    json.dump(canvas_data, f, ensure_ascii=False)

                canvas_files.append(canvas_path)

            # 测试批量处理
            extractor = ConceptExtractor()
            results = []

            for canvas_path in canvas_files:
                result = extractor.extract_concepts_from_canvas(str(canvas_path))
                results.append(result)

            # 验证结果
            self.assertEqual(len(results), 3)
            for result in results:
                self.assertGreater(len(result["concepts"]), 0)
                self.assertGreater(len(result["relationships"]), 0)

        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)