#!/usr/bin/env python3
"""
概念提取器专门测试

专门测试ConceptExtractor类的各种功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import unittest

from concept_extractor import ConceptExtractor


class TestConceptExtractionMethods(unittest.TestCase):
    """测试概念提取的各种方法"""

    def setUp(self):
        self.extractor = ConceptExtractor()

    def test_chinese_text_segmentation(self):
        """测试中文文本分词"""
        test_texts = [
            "微积分是数学分析的基础",
            "函数的导数描述变化率",
            "积分计算曲线下面积",
            "极限是微积分的核心概念"
        ]

        for text in test_texts:
            with self.subTest(text=text):
                concepts = self.extractor._extract_concept_names_from_text(text)
                self.assertIsInstance(concepts, list)
                # 应该至少提取出一个概念
                self.assertGreater(len(concepts), 0)

    def test_mathematical_concept_patterns(self):
        """测试数学概念模式识别"""
        math_texts = [
            "泰勒级数展开公式",
            "傅里叶变换应用",
            "拉格朗日中值定理",
            "牛顿-莱布尼茨公式"
        ]

        for text in math_texts:
            with self.subTest(text=text):
                subject_areas = self.extractor._identify_subject_areas(text)
                self.assertIn("数学", subject_areas)

    def test_physics_concept_patterns(self):
        """测试物理概念模式识别"""
        physics_texts = [
            "牛顿第二定律F=ma",
            "电磁感应现象",
            "波动方程推导",
            "热力学第一定律"
        ]

        for text in physics_texts:
            with self.subTest(text=text):
                subject_areas = self.extractor._identify_subject_areas(text)
                self.assertIn("物理", subject_areas)

    def test_relationship_keyword_detection(self):
        """测试关系关键词检测"""
        test_cases = [
            ("A是B的前提", "is_prerequisite_for"),
            ("A类似于B", "is_similar_to"),
            ("A与B相反", "is_contradictory_of"),
            ("A从B推导", "is_derived_from"),
            ("A应用于B", "is_applied_in"),
            ("A是B的例子", "is_example_of"),
            ("A包括B", "includes"),
            ("A导致B", "leads_to")
        ]

        for text, expected_type in test_cases:
            with self.subTest(text=text):
                result = self.extractor._infer_relationship_type_from_edge(text, "A", "B")
                self.assertEqual(result, expected_type)

    def test_concept_confidence_calculation(self):
        """测试概念置信度计算"""
        test_cases = [
            {
                "concept": {
                    "source_nodes": ["node1"],
                    "descriptions": ["简短描述"],
                    "subject_areas": [],
                    "aliases": set()
                },
                "expected_min": 0.1,
                "expected_max": 0.4
            },
            {
                "concept": {
                    "source_nodes": ["node1", "node2", "node3"],
                    "descriptions": ["详细描述1", "详细描述2", "详细描述3"],
                    "subject_areas": ["数学"],
                    "aliases": set()
                },
                "expected_min": 0.5,
                "expected_max": 1.0
            }
        ]

        for case in test_cases:
            with self.subTest(concept=case["concept"]):
                confidence = self.extractor._calculate_concept_confidence(case["concept"])
                self.assertGreaterEqual(confidence, case["expected_min"])
                self.assertLessEqual(confidence, case["expected_max"])

    def test_ngram_generation(self):
        """测试n-gram生成"""
        words = ["微", "积", "分", "是", "数", "学", "分", "析", "的", "基", "础"]

        ngrams = self.extractor._generate_ngrams(words, 2, 4)

        self.assertIsInstance(ngrams, list)
        self.assertGreater(len(ngrams), 0)

        # 检查是否包含预期的n-gram
        expected_ngrams = ["微分", "积分", "数学", "分析", "数学分析"]
        for expected in expected_ngrams:
            if self.extractor._is_valid_concept(expected):
                self.assertIn(expected, ngrams)

    def test_concept_validation_edge_cases(self):
        """测试概念验证边界情况"""
        edge_cases = [
            ("", False),
            ("   ", False),
            ("a", True),
            ("这是一个非常长的概念名称，超过了五十个字符的限制，应该被过滤掉", False),
            ("123", False),
            ("的", False),
            ("正常概念名称", True),
            ("概念123", True),
            ("数学公式", True)
        ]

        for concept, expected in edge_cases:
            with self.subTest(concept=concept):
                result = self.extractor._is_valid_concept(concept)
                self.assertEqual(result, expected)

    def test_canvas_node_to_concept_mapping(self):
        """测试Canvas节点到概念的映射"""
        node_data = {
            "source_nodes": ["node1", "node2"],
            "descriptions": [
                "这是第一个描述",
                "这是第二个更长的描述，包含更多详细信息"
            ],
            "node_types": ["text", "question"],
            "colors": ["1", "2"],
            "subject_areas": ["数学", "物理"],
            "aliases": set(["别名1", "别名2"]),
            "confidence": 0.0,
            "text_content": "合并的文本内容"
        }

        # 测试属性计算
        confidence = self.extractor._calculate_concept_confidence(node_data)

        self.assertGreater(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

        # 节点数量应该增加置信度
        self.assertGreaterEqual(confidence, len(node_data["source_nodes"]) * 0.2)


if __name__ == '__main__':
    unittest.main()
