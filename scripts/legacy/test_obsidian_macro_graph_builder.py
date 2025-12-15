#!/usr/bin/env python3
"""
Test suite for Obsidian Macro Document Relationship Graph Construction System

This test suite validates all components of the system according to the 
acceptance criteria defined in Story 1.1.

Author: James (Dev Agent)
Model: claude-sonnet-4-20250514
Story: 1.1
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
import yaml
from unittest.mock import patch, mock_open

# Import the main system
from obsidian_macro_graph_builder import (
    InputProcessor,
    ThemeAnalysisEngine, 
    ContentGenerator,
    LinkingSystem,
    OutputManager,
    MacroGraphBuilder,
    DocumentMetadata,
    Theme
)


class TestInputProcessor(unittest.TestCase):
    """Test Task 1: Input Processing System"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.processor = InputProcessor(self.temp_dir, "#我的课堂总结")
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_find_tagged_documents(self):
        """AC1: System only processes documents containing the user-specified tag"""
        # Create test files
        tagged_file = Path(self.temp_dir) / "tagged.md"
        untagged_file = Path(self.temp_dir) / "untagged.md"
        
        tagged_file.write_text("# Test Document\n\nThis has #我的课堂总结 tag.", encoding='utf-8')
        untagged_file.write_text("# Other Document\n\nNo target tag here.", encoding='utf-8')
        
        found_files = self.processor.find_tagged_documents()
        
        self.assertEqual(len(found_files), 1)
        self.assertIn(str(tagged_file), found_files)
        self.assertNotIn(str(untagged_file), found_files)
    
    def test_parse_markdown_with_yaml_frontmatter(self):
        """Test YAML frontmatter parsing support"""
        content = """---
title: Test Document
tags: ["#我的课堂总结", "#测试"]
---

# Main Heading

Content with #inline_tag here.
"""
        
        with patch("builtins.open", mock_open(read_data=content)):
            doc = self.processor.parse_markdown_document("test.md")
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc.title, "Main Heading")
        self.assertIn("#我的课堂总结", doc.tags)
        self.assertIn("#inline_tag", doc.tags)
        self.assertEqual(doc.yaml_frontmatter['title'], "Test Document")
    
    def test_extract_core_concepts(self):
        """Test core concept extraction from documents"""
        content = """# Python Programming

## Variables and Functions

Python is a programming language. Variables store data.
Functions are reusable code blocks. Python Python Python.
"""
        
        concepts = self.processor._extract_core_concepts(content)
        
        self.assertIn("Python Programming", concepts)
        self.assertIn("Variables and Functions", concepts)
        self.assertIn("Python", concepts)  # Should detect frequent important terms
    
    def test_validate_tags(self):
        """Test tag validation"""
        doc_with_tag = DocumentMetadata(
            file_path="test.md",
            title="Test",
            tags={"#我的课堂总结", "#other"},
            yaml_frontmatter={},
            content="test",
            h1_headings=[],
            core_concepts=[]
        )
        
        doc_without_tag = DocumentMetadata(
            file_path="test2.md",
            title="Test2", 
            tags={"#other"},
            yaml_frontmatter={},
            content="test",
            h1_headings=[],
            core_concepts=[]
        )
        
        self.assertTrue(self.processor.validate_tags(doc_with_tag))
        self.assertFalse(self.processor.validate_tags(doc_without_tag))


class TestThemeAnalysisEngine(unittest.TestCase):
    """Test Task 2: Theme Analysis Engine"""
    
    def setUp(self):
        # Create sample documents for testing
        self.documents = [
            DocumentMetadata(
                file_path="doc1.md",
                title="Python Basics",
                tags={"#我的课堂总结"},
                yaml_frontmatter={},
                content="Python programming content",
                h1_headings=["Python Basics"],
                core_concepts=["Python", "Programming", "Variables", "Functions"]
            ),
            DocumentMetadata(
                file_path="doc2.md", 
                title="Advanced Python",
                tags={"#我的课堂总结"},
                yaml_frontmatter={},
                content="Advanced Python concepts",
                h1_headings=["Advanced Python"],
                core_concepts=["Python", "Classes", "Objects", "Programming"]
            ),
            DocumentMetadata(
                file_path="doc3.md",
                title="Math Concepts", 
                tags={"#我的课堂总结"},
                yaml_frontmatter={},
                content="Mathematics content",
                h1_headings=["Math Concepts"],
                core_concepts=["Mathematics", "Algebra", "Calculus"]
            )
        ]
        
        self.engine = ThemeAnalysisEngine(self.documents)
    
    def test_identify_core_themes(self):
        """AC2: System identifies independent, important core themes across all tagged documents"""
        themes = self.engine.identify_core_themes()
        
        # Should find Python as a theme (appears in 2 docs)
        theme_names = [theme.name for theme in themes]
        self.assertIn("Python", theme_names)
        self.assertIn("Programming", theme_names)
        
        # Check theme properties
        python_theme = next(theme for theme in themes if theme.name == "Python")
        self.assertEqual(len(python_theme.related_documents), 2)
        self.assertGreater(python_theme.confidence_score, 0)
        self.assertIn("doc1.md", python_theme.related_documents)
        self.assertIn("doc2.md", python_theme.related_documents)
    
    def test_theme_relationships(self):
        """Test cross-document thematic analysis and theme relationships"""
        themes = self.engine.identify_core_themes()
        
        # Find themes that should be related
        python_theme = next((t for t in themes if t.name == "Python"), None)
        programming_theme = next((t for t in themes if t.name == "Programming"), None)
        
        if python_theme and programming_theme:
            # They should be related since they appear in same documents
            self.assertTrue(
                "Programming" in python_theme.related_themes or 
                "Python" in programming_theme.related_themes
            )
    
    def test_theme_prioritization(self):
        """Test theme prioritization and categorization logic"""
        themes = self.engine.identify_core_themes()
        
        # Themes should be sorted by confidence score
        for i in range(len(themes) - 1):
            self.assertGreaterEqual(themes[i].confidence_score, themes[i+1].confidence_score)


class TestContentGenerator(unittest.TestCase):
    """Test Task 3: Content Generation System"""
    
    def setUp(self):
        self.themes = [
            Theme(
                name="Python",
                description="Core theme: Python",
                core_concepts=["Programming", "Variables", "Functions", "Classes"],
                related_documents=["doc1.md", "doc2.md"],
                related_themes={"Programming"},
                confidence_score=0.67
            )
        ]
        
        self.documents = [
            DocumentMetadata(
                file_path="doc1.md",
                title="Python Basics",
                tags={"#我的课堂总结"},
                yaml_frontmatter={},
                content="Python content",
                h1_headings=["Python Basics"],
                core_concepts=["Python", "Programming"]
            )
        ]
        
        self.generator = ContentGenerator(self.themes, self.documents)
    
    def test_generate_intuitive_filename(self):
        """AC3: Intuitive, descriptive filenames using common language concepts"""
        filename = self.generator.generate_intuitive_filename(self.themes[0])
        
        self.assertTrue(filename.endswith(".md"))
        self.assertIn("Python", filename)
        self.assertIn("编程概念", filename)  # Should detect programming context
    
    def test_generate_yaml_frontmatter(self):
        """AC3: Proper YAML frontmatter with dynamic main tags, 知识图谱索引, and unified tags"""
        frontmatter = self.generator.generate_yaml_frontmatter(self.themes[0])
        
        # Check required tags
        tags = frontmatter['tags']
        self.assertIn('#知识图谱索引', tags)
        self.assertTrue(any(tag.startswith('#Python') for tag in tags))  # Main tag
        self.assertTrue(any('_' in tag and tag.endswith('20250801') for tag in tags))  # Unified tag format
        
        # Check other required fields
        self.assertEqual(frontmatter['title'], 'Python')
        self.assertIn('created', frontmatter)
        self.assertEqual(frontmatter['confidence_score'], 0.67)
    
    def test_generate_structured_content(self):
        """AC4: Multi-level explanations, vivid analogies, storytelling, and memory anchors"""
        content = self.generator.generate_theme_content(self.themes[0])
        
        # Check for required sections
        self.assertIn("## 核心洞察", content)
        self.assertIn("## 深度理解", content)
        self.assertIn("### 形象比喻", content)
        self.assertIn("### 记忆锚点", content)
        self.assertIn("## 相关原始文档", content)
        self.assertIn("## 相关主题探索", content)
        self.assertIn("## 快速回顾与内化", content)
        
        # Check for storytelling elements
        self.assertIn("想象成", content)  # Analogy language
        self.assertIn("记住关键词", content)  # Memory anchor
    
    def test_source_document_references(self):
        """AC5: All generated content strictly references and links back to original source documents"""
        content = self.generator.generate_theme_content(self.themes[0])
        
        # Should contain references to source documents
        self.assertIn("[[doc1]]", content)  # Obsidian link format
        self.assertIn("Python Basics", content)  # Document title reference


class TestLinkingSystem(unittest.TestCase):
    """Test Task 4: Linking and Reference System"""
    
    def setUp(self):
        self.themes = [
            Theme(
                name="Python",
                description="Python programming",
                core_concepts=["Programming"],
                related_documents=["doc1.md"],
                related_themes={"Programming"},
                confidence_score=0.5
            ),
            Theme(
                name="Programming", 
                description="Programming concepts",
                core_concepts=["Code"],
                related_documents=["doc1.md"],
                related_themes={"Python"},
                confidence_score=0.4
            )
        ]
        
        self.documents = []
        self.linking_system = LinkingSystem(self.themes, self.documents)
    
    def test_generate_obsidian_links(self):
        """AC5, AC6: Obsidian-compatible link generation ([[]] syntax)"""
        content = "This is about Python and Programming concepts."
        updated_content = self.linking_system.generate_obsidian_links(content, "Python")
        
        # Should convert theme names to Obsidian links
        self.assertIn("[[Programming]]", updated_content)
        # Should not link to itself
        self.assertNotIn("[[Python]]", updated_content)
    
    def test_create_bidirectional_links(self):
        """AC6: Related theme files are cross-linked to form a navigable knowledge network"""
        generated_files = [
            ("python.md", "Content about Python and Programming", "Python"),
            ("programming.md", "Content about Programming and Python", "Programming")
        ]
        
        updated_files = self.linking_system.create_bidirectional_links(generated_files)
        
        # Check that files have backlinks sections
        python_content = next(content for filename, content, theme in updated_files if theme == "Python")
        self.assertIn("## 反向链接", python_content)
        self.assertIn("[[Programming]]", python_content)


class TestOutputManager(unittest.TestCase):
    """Test Task 5: Output Management System"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_manager = OutputManager(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_validate_markdown_compatibility(self):
        """AC7: Validation for generated Markdown compatibility"""
        valid_content = """---
title: Test
---

# Test Content

Some content here.
"""
        
        invalid_content = "Just some text without proper structure"
        
        self.assertTrue(self.output_manager.validate_markdown_compatibility(valid_content))
        self.assertFalse(self.output_manager.validate_markdown_compatibility(invalid_content))
    
    def test_output_batch_files(self):
        """AC7: System outputs all generated files at once with clear separation markers"""
        files = [
            ("test1.md", "---\ntitle: Test1\n---\n\n# Test1\n\nContent", "Theme1"),
            ("test2.md", "---\ntitle: Test2\n---\n\n# Test2\n\nContent", "Theme2")
        ]
        
        output_paths = self.output_manager.output_batch_files(files)
        
        self.assertEqual(len(output_paths), 2)
        
        # Check files were created
        for path in output_paths:
            self.assertTrue(os.path.exists(path))
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("---", content)
                self.assertIn("# Test", content)
    
    def test_generate_overview(self):
        """Test overview generation for created themes and links"""
        themes = [
            Theme("Python", "Python theme", ["Programming"], ["doc1.md"], {"Programming"}, 0.5),
            Theme("Programming", "Programming theme", ["Code"], ["doc1.md"], {"Python"}, 0.4)
        ]
        
        files = [os.path.join(self.temp_dir, "test1.md")]
        
        overview_path = self.output_manager.generate_overview(files, themes)
        
        self.assertTrue(os.path.exists(overview_path))
        
        with open(overview_path, 'r', encoding='utf-8') as f:
            overview_content = f.read()
            
        self.assertIn("知识图谱主题概览", overview_content)
        self.assertIn("主题数量: 2", overview_content)
        self.assertIn("[[Python]]", overview_content)
        self.assertIn("[[Programming]]", overview_content)


class TestMacroGraphBuilderIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test vault structure
        vault_dir = Path(self.temp_dir) / "vault"
        vault_dir.mkdir()
        
        # Create test documents
        doc1 = vault_dir / "python_basics.md"
        doc1.write_text("""---
title: Python Basics
tags: ["#我的课堂总结"]
---

# Python Programming Fundamentals

## Variables
Python variables store data values.

## Functions  
Functions are reusable blocks of code.
""", encoding='utf-8')
        
        doc2 = vault_dir / "advanced_python.md"
        doc2.write_text("""# Advanced Python Concepts

This document covers #我的课堂总结 advanced topics.

## Classes and Objects
Python supports object-oriented programming.

## Modules
Modules help organize Python code.
""", encoding='utf-8')
        
        self.vault_path = str(vault_dir)
        self.builder = MacroGraphBuilder(self.vault_path, "#我的课堂总结")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_complete_pipeline(self):
        """Test the complete macro graph building pipeline"""
        result = self.builder.build_macro_graph()
        
        # Check success
        self.assertTrue(result['success'])
        self.assertGreater(result['documents_processed'], 0)
        self.assertGreater(result['themes_discovered'], 0)
        self.assertGreater(result['files_generated'], 0)
        
        # Check output directory exists
        self.assertTrue(os.path.exists(result['output_directory']))
        
        # Check overview file was created
        self.assertTrue(os.path.exists(result['overview_file']))
        
        # Check that some generated files exist
        for file_path in result['generated_files']:
            self.assertTrue(os.path.exists(file_path))
            
            # Verify file contents
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("---", content)  # Has YAML frontmatter
                self.assertIn("#知识图谱索引", content)  # Has required tag


class TestAcceptanceCriteria(unittest.TestCase):
    """Comprehensive tests for all acceptance criteria"""
    
    def test_ac1_tag_based_processing(self):
        """AC1: System only processes documents containing the user-specified tag"""
        # This is covered in TestInputProcessor.test_find_tagged_documents
        pass
    
    def test_ac2_theme_identification(self):
        """AC2: System identifies independent, important core themes across all tagged documents"""
        # This is covered in TestThemeAnalysisEngine.test_identify_core_themes
        pass
    
    def test_ac3_structured_content_generation(self):
        """AC3: System creates new Markdown files for each identified theme with proper structure"""
        # This is covered in TestContentGenerator tests
        pass
    
    def test_ac4_multi_level_explanations(self):
        """AC4: Generated files include multi-level explanations, vivid analogies, storytelling, and memory anchors"""
        # This is covered in TestContentGenerator.test_generate_structured_content
        pass
    
    def test_ac5_source_document_references(self):
        """AC5: All generated content strictly references and links back to original source documents"""
        # This is covered in TestContentGenerator.test_source_document_references
        pass
    
    def test_ac6_cross_linking(self):
        """AC6: Related theme files are cross-linked to form a navigable knowledge network"""
        # This is covered in TestLinkingSystem.test_create_bidirectional_links
        pass
    
    def test_ac7_batch_output(self):
        """AC7: System outputs all generated files at once with clear separation markers"""
        # This is covered in TestOutputManager.test_output_batch_files
        pass


def run_tests():
    """Run all tests and report results"""
    print("🧪 Running Obsidian Macro Graph Builder Test Suite")
    print("="*60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestInputProcessor,
        TestThemeAnalysisEngine,
        TestContentGenerator,
        TestLinkingSystem,
        TestOutputManager,
        TestMacroGraphBuilderIntegration,
        TestAcceptanceCriteria
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Report summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED. Please review and fix issues.")
        
        if result.failures:
            print("\n📋 FAILURES:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\n🚨 ERRORS:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
        
        return False


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)