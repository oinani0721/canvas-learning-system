#!/usr/bin/env python3
"""
Simple test runner for the Obsidian Macro Graph Builder
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_basic_functionality():
    """Test basic functionality without emojis"""
    print("Testing Obsidian Macro Graph Builder")
    print("=" * 50)
    
    try:
        # Test imports
        from obsidian_macro_graph_builder import (
            InputProcessor, ThemeAnalysisEngine, ContentGenerator,
            LinkingSystem, OutputManager, MacroGraphBuilder
        )
        print("OK All imports successful")
        
        # Test basic instantiation
        temp_path = "C:\\temp"
        processor = InputProcessor(temp_path, "#我的课堂总结")
        print("OK InputProcessor created successfully")
        
        # Test content generation logic
        from obsidian_macro_graph_builder import Theme, DocumentMetadata
        
        test_theme = Theme(
            name="Python",
            description="Python programming concepts",
            core_concepts=["Programming", "Variables"],
            related_documents=["doc1.md"],
            related_themes=set(),
            confidence_score=0.5
        )
        
        test_doc = DocumentMetadata(
            file_path="test.md",
            title="Test",
            tags={"#我的课堂总结"},
            yaml_frontmatter={},
            content="test content",
            h1_headings=["Test"],
            core_concepts=["Test"]
        )
        
        generator = ContentGenerator([test_theme], [test_doc])
        filename = generator.generate_intuitive_filename(test_theme)
        print(f"OK Generated filename: {filename}")
        
        yaml_fm = generator.generate_yaml_frontmatter(test_theme)
        print(f"OK Generated YAML frontmatter with {len(yaml_fm)} fields")
        
        content = generator.generate_theme_content(test_theme)
        print(f"OK Generated content with {len(content)} characters")
        
        # Test linking system
        linking = LinkingSystem([test_theme], [test_doc])
        test_content = "This is about Python programming"
        linked_content = linking.generate_obsidian_links(test_content, "Test")
        print("OK Linking system works")
        
        print("\n" + "=" * 50)
        print("SUCCESS: All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\nSystem is ready for use!")
    else:
        print("\nPlease fix the issues before using the system.")