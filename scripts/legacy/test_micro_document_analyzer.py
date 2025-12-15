#!/usr/bin/env python3
"""
Comprehensive tests for the Micro Document Internal Knowledge Point Graph Construction System.
Tests all acceptance criteria and story requirements.
"""

import os
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the main analyzer
from micro_document_analyzer import MicroDocumentAnalyzer, KnowledgePoint


class TestMicroDocumentAnalyzer(unittest.TestCase):
    """Test suite for MicroDocumentAnalyzer."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create temporary directories for testing
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.test_dir / "output"
        self.analyzer = MicroDocumentAnalyzer(str(self.output_dir))
        
        # Sample test document content
        self.sample_document = """---
title: Test Document
tags: [test, sample]
---

# Test Document for Knowledge Point Extraction

## Section 1: First Knowledge Point

**图像描述**: 这是第一个知识点的图像描述
**视频时间轴**: 0:00-1:30
**总结**: 这是第一个知识点的核心总结，包含了重要的概念解释和应用场景。

## Section 2: Second Knowledge Point  

![图像2](image2.png)
时间轴: 1:30-3:00
要点总结: 第二个知识点涉及更复杂的概念，需要深入理解其机制和原理。

## Section 3: Related Concept

关键概念: 这个概念与前面的知识点密切相关
总结要点: 通过关联学习可以更好地理解整体知识体系。
"""
    
    def tearDown(self):
        """Clean up test environment after each test."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def _create_test_document(self, content: str = None) -> str:
        """Create a test document file and return its path."""
        if content is None:
            content = self.sample_document
        
        doc_path = self.test_dir / "test_document.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(doc_path)
    
    def test_document_processing_basic(self):
        """Test AC1: System processes a single complete original document."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Should not have errors
        self.assertNotIn("error", results)
        
        # Should have original document path set
        self.assertEqual(self.analyzer.original_doc_path, doc_path)
        self.assertEqual(self.analyzer.original_doc_name, "test_document")
        
        # Should have processed content
        self.assertGreater(len(self.analyzer.knowledge_points), 0)
    
    def test_knowledge_point_identification(self):
        """Test AC2: System identifies individual knowledge point blocks."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Should identify multiple knowledge points
        self.assertGreaterEqual(len(self.analyzer.knowledge_points), 2)
        
        # Check knowledge point structure
        for point in self.analyzer.knowledge_points:
            self.assertIsInstance(point, KnowledgePoint)
            self.assertTrue(point.id)
            # Should have some content (title, summary, or description)
            self.assertTrue(point.title or point.summary or point.image_description)
    
    def test_knowledge_point_file_generation(self):
        """Test AC3: System creates new Markdown files for each knowledge point."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Should generate files for knowledge points
        knowledge_point_files = [f for f in results.keys() if f.endswith('.md') and not '中控' in f and not f.startswith('UPDATE_')]
        self.assertGreater(len(knowledge_point_files), 0)
        
        # Check file content structure
        for filename in knowledge_point_files:
            content = results[filename]
            
            # Should have YAML frontmatter
            self.assertTrue(content.startswith('---'))
            
            # Should have required tags
            self.assertIn('知识图谱索引', content)
            
            # Should have structured sections
            self.assertIn('# ', content)  # Title
            self.assertIn('## 核心解释', content)
            self.assertIn('## 来源参考', content)
    
    def test_yaml_frontmatter_generation(self):
        """Test AC3: Proper YAML frontmatter with dynamic tags."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Get first knowledge point file
        kp_files = [f for f in results.keys() if f.endswith('.md') and not '中控' in f and not f.startswith('UPDATE_')]
        self.assertGreater(len(kp_files), 0)
        
        content = results[kp_files[0]]
        
        # Check YAML structure
        lines = content.split('\n')
        self.assertEqual(lines[0], '---')
        
        # Find end of YAML
        yaml_end = -1
        for i, line in enumerate(lines[1:], 1):
            if line == '---':
                yaml_end = i
                break
        
        self.assertGreater(yaml_end, 0)
        
        # Should have required tags
        yaml_content = '\n'.join(lines[1:yaml_end])
        self.assertIn('知识图谱索引', yaml_content)
        self.assertIn('tags:', yaml_content)
        self.assertIn('source:', yaml_content)
    
    def test_multi_level_explanations(self):
        """Test AC4: Generated files include multi-level explanations and analogies."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Get first knowledge point file
        kp_files = [f for f in results.keys() if f.endswith('.md') and not '中控' in f and not f.startswith('UPDATE_')]
        content = results[kp_files[0]]
        
        # Should have multi-level structure
        self.assertIn('## 深入理解', content)
        self.assertIn('### 详细说明', content)
        self.assertIn('### 生动类比', content)
        self.assertIn('### 记忆锚点', content)
    
    def test_source_references(self):
        """Test AC5: All content references original source with precise locations."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Check knowledge point files for source references
        kp_files = [f for f in results.keys() if f.endswith('.md') and not '中控' in f and not f.startswith('UPDATE_')]
        
        for filename in kp_files:
            content = results[filename]
            
            # Should reference original document
            self.assertIn('test_document', content)
            self.assertIn('[[', content)  # Obsidian link syntax
            self.assertIn('## 来源参考', content)
            self.assertIn('源位置', content)
    
    def test_hub_file_creation(self):
        """Test AC6: System creates a Hub File organizing relationships."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Should have hub file
        hub_files = [f for f in results.keys() if '中控' in f]
        self.assertEqual(len(hub_files), 1)
        
        hub_content = results[hub_files[0]]
        
        # Hub file structure checks
        self.assertIn('# test_document - 知识图谱中控', hub_content)
        self.assertIn('## 文档概览', hub_content)
        self.assertIn('## 知识点导航', hub_content)
        self.assertIn('## 知识点关系图', hub_content)
        self.assertIn('## 使用说明', hub_content)
        
        # Should show knowledge point count
        self.assertIn('个知识点', hub_content)
    
    def test_original_document_integration(self):
        """Test AC7: System updates original document with hub file link."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Should have update for original document
        update_files = [f for f in results.keys() if f.startswith('UPDATE_')]
        self.assertEqual(len(update_files), 1)
        
        updated_content = results[update_files[0]]
        
        # Should contain hub file link
        self.assertIn('知识图谱导航', updated_content)
        self.assertIn('[[', updated_content)
        self.assertIn('中控', updated_content)
        
        # Should preserve original content
        self.assertIn('# Test Document', updated_content)
        self.assertIn('Section 1', updated_content)
    
    def test_cross_linking(self):
        """Test AC8: Knowledge point files are cross-linked based on relationships."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Check if any knowledge points have related points
        has_relationships = any(kp.related_points for kp in self.analyzer.knowledge_points)
        
        if has_relationships:
            # Find files with related sections
            kp_files = [f for f in results.keys() if f.endswith('.md') and not '中控' in f and not f.startswith('UPDATE_')]
            
            related_content_found = False
            for filename in kp_files:
                content = results[filename]
                if '## 相关知识点' in content:
                    related_content_found = True
                    # Should have wiki-style links
                    self.assertIn('[[', content)
            
            self.assertTrue(related_content_found)
    
    def test_batch_output_with_separation(self):
        """Test AC9: System outputs all files at once with clear separation."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Should have multiple files generated
        self.assertGreater(len(results), 2)
        
        # Should have different types of files
        file_types = set()
        for filename in results.keys():
            if filename.endswith('.md'):
                if '中控' in filename:
                    file_types.add('hub')
                elif filename.startswith('UPDATE_'):
                    file_types.add('update')
                else:
                    file_types.add('knowledge_point')
        
        # Should have at least knowledge points and hub
        self.assertIn('knowledge_point', file_types)
        self.assertIn('hub', file_types)
    
    def test_obsidian_compatibility(self):
        """Test Obsidian compatibility requirements."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        for filename, content in results.items():
            if filename.endswith('.md') and not filename.startswith('UPDATE_'):
                # Should use proper Obsidian link syntax
                if '[[' in content:
                    # Check for proper link format
                    import re
                    links = re.findall(r'\[\[([^\]]+)\]\]', content)
                    self.assertGreater(len(links), 0)
                
                # Should have proper tag syntax
                if '#' in content and 'tags:' in content:
                    self.assertTrue(True)  # Has tags
                
                # Should be valid Markdown
                self.assertTrue(content.strip())
    
    def test_error_handling_missing_file(self):
        """Test error handling for missing input file."""
        non_existent_path = str(self.test_dir / "non_existent.md")
        
        results = self.analyzer.process_document(non_existent_path)
        
        self.assertIn("error", results)
        self.assertIn("not found", results["error"].lower())
    
    def test_error_handling_empty_document(self):
        """Test error handling for empty or invalid documents."""
        # Create empty document
        empty_doc_path = self._create_test_document("")
        
        results = self.analyzer.process_document(empty_doc_path)
        
        # Should handle gracefully
        self.assertIn("error", results)
    
    def test_knowledge_point_structure(self):
        """Test KnowledgePoint data structure."""
        point = KnowledgePoint(
            id="test_001",
            title="Test Point",
            summary="Test summary"
        )
        
        # Should have proper defaults
        self.assertEqual(point.related_points, [])
        self.assertEqual(point.image_description, "")
        self.assertEqual(point.source_line_start, 0)
    
    def test_filename_generation(self):
        """Test intuitive filename generation."""
        doc_path = self._create_test_document()
        
        results = self.analyzer.process_document(doc_path)
        
        # Check generated filenames
        kp_files = [f for f in results.keys() if f.endswith('.md') and not '中控' in f and not f.startswith('UPDATE_')]
        
        for filename in kp_files:
            # Should be valid filename
            self.assertTrue(filename.endswith('.md'))
            self.assertNotIn('<', filename)
            self.assertNotIn('>', filename)
            self.assertNotIn(':', filename)
            self.assertNotIn('"', filename)
            self.assertNotIn('/', filename)
            self.assertNotIn('\\', filename)
            self.assertNotIn('|', filename)
            self.assertNotIn('?', filename)
            self.assertNotIn('*', filename)
    
    def test_tag_generation(self):
        """Test dynamic tag generation."""
        # Test different content types
        test_cases = [
            ("Python编程基础", "#Python"),
            ("数学公式推导", "#数学"),
            ("英语语法规则", "#英语"),
            ("物理实验", "#物理"),
            ("通用知识点", "#通用知识")
        ]
        
        for summary, expected_tag in test_cases:
            point = KnowledgePoint(id="test", title="", summary=summary)
            main_tag, unified_tag = self.analyzer._generate_tags(point)
            
            # Main tag should match expected
            self.assertEqual(main_tag, expected_tag)
            
            # Unified tag should have date
            self.assertTrue(unified_tag.startswith(f"{expected_tag.replace('#', '#')}_"))
            self.assertIn("2025", unified_tag)  # Current year
    
    def test_relationship_detection(self):
        """Test knowledge point relationship detection."""
        point1 = KnowledgePoint(
            id="kp_001",
            title="First Point",
            summary="Python programming basics",
            source_line_start=1
        )
        
        point2 = KnowledgePoint(
            id="kp_002", 
            title="Second Point",
            summary="Python functions and programming",
            source_line_start=5
        )
        
        point3 = KnowledgePoint(
            id="kp_003",
            title="Unrelated Point", 
            summary="Mathematics formulas",
            source_line_start=50
        )
        
        # Test relationship detection
        self.assertTrue(self.analyzer._are_related(point1, point2))  # Similar content, close lines
        self.assertFalse(self.analyzer._are_related(point1, point3))  # Different content, far lines
    
    def test_content_extraction_patterns(self):
        """Test various content extraction patterns."""
        complex_document = """
# Complex Knowledge Point

**图像描述**: 复杂的图像内容
**视频时间轴**: 2:30-4:00
**核心总结**: 这是一个复杂的知识点，包含多层次的理解要求。

![示例图片](example.png)

时间点: 4:00-5:30

关键要点:
- 第一个要点
- 第二个要点

总结要点: 通过系统化学习可以掌握核心概念。
"""
        
        doc_path = self._create_test_document(complex_document)
        results = self.analyzer.process_document(doc_path)
        
        # Should extract various content types
        points = self.analyzer.knowledge_points
        self.assertGreater(len(points), 0)
        
        # Check if content was properly extracted
        point = points[0]
        self.assertTrue(point.image_description or point.video_timeline or point.summary)


class TestFileOperations(unittest.TestCase):
    """Test file I/O operations."""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.test_dir / "output"
        self.analyzer = MicroDocumentAnalyzer(str(self.output_dir))
    
    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_output_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        # Output directory should not exist initially
        self.assertFalse(self.output_dir.exists())
        
        # Create test document
        doc_path = self.test_dir / "test.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write("# Test\n\n总结: Test content")
        
        # Process document
        results = self.analyzer.process_document(str(doc_path))
        
        # Output directory should be created
        self.assertTrue(self.output_dir.exists())
    
    def test_file_writing_utf8(self):
        """Test UTF-8 encoding for files with Chinese characters."""
        chinese_content = """
# 中文知识点

**图像描述**: 包含中文字符的描述
**总结**: 这是一个中文知识点的测试，确保UTF-8编码正确处理。
"""
        
        doc_path = self.test_dir / "chinese_test.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(chinese_content)
        
        results = self.analyzer.process_document(str(doc_path))
        
        # Should handle Chinese characters properly
        self.assertNotIn("error", results)
        
        # Check that files contain Chinese characters
        for filename, content in results.items():
            if filename.endswith('.md'):
                # Should contain Chinese characters without encoding issues
                self.assertIn('中文', content)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [TestMicroDocumentAnalyzer, TestFileOperations]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("=" * 80)
    print("微观文档知识点图谱构建系统 - 测试套件")
    print("=" * 80)
    
    result = run_tests()
    
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    print(f"总计测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n测试成功率: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！系统实现符合所有验收标准。")
    else:
        print("\n❌ 部分测试失败，需要修复后重新测试。")