#!/usr/bin/env python3
"""
Obsidian Macro Document Relationship Graph Construction System

This system analyzes tagged Obsidian documents and creates thematic files with cross-links
to build a macro-level knowledge graph.

Author: James (Dev Agent)
Model: claude-sonnet-4-20250514
Story: 1.1
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
import json
from collections import defaultdict


# Configuration constants
MIN_THEME_DOCS = 2  # Minimum documents required for a theme
MAX_CONCEPTS_PER_DOC = 15  # Maximum concepts to extract per document
MIN_WORD_LENGTH = 3  # Minimum word length for concept extraction
MIN_CONCEPT_FREQUENCY = 2  # Minimum frequency for a concept to be important
MAX_FREQUENT_CONCEPTS = 10  # Maximum frequent concepts to consider


@dataclass
class DocumentMetadata:
    """Metadata extracted from a document"""
    file_path: str
    title: str
    tags: Set[str]
    yaml_frontmatter: Dict
    content: str
    h1_headings: List[str]
    core_concepts: List[str]


@dataclass
class Theme:
    """Represents a discovered theme across documents"""
    name: str
    description: str
    core_concepts: List[str]
    related_documents: List[str]
    related_themes: Set[str]
    confidence_score: float


class InputProcessor:
    """Task 1: Input Processing System - handles tag-based document filtering and parsing"""
    
    def __init__(self, vault_path: str, target_tag: str = "#我的课堂总结"):
        if not vault_path or not isinstance(vault_path, str):
            raise ValueError("vault_path must be a non-empty string")
        if not target_tag or not isinstance(target_tag, str):
            raise ValueError("target_tag must be a non-empty string")
        if not target_tag.startswith('#'):
            raise ValueError("target_tag must start with '#'")
            
        self.vault_path = Path(vault_path).resolve()  # Resolve to absolute path
        self.target_tag = target_tag
        self.processed_documents: List[DocumentMetadata] = []
    
    def find_tagged_documents(self) -> List[str]:
        """Find all Markdown documents containing the target tag"""
        tagged_files = []
        
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        
        # Recursively search for .md files
        for md_file in self.vault_path.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Check for tag in content (both YAML frontmatter and inline)
                if self.target_tag in content:
                    tagged_files.append(str(md_file))
            except (IOError, OSError) as e:
                print(f"Warning: Could not read {md_file}: {e}")
                continue
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
                continue
        
        return tagged_files
    
    def parse_markdown_document(self, file_path: str) -> Optional[DocumentMetadata]:
        """Parse a Markdown document and extract metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract YAML frontmatter
            yaml_frontmatter = {}
            yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if yaml_match:
                try:
                    yaml_frontmatter = yaml.safe_load(yaml_match.group(1)) or {}
                    content_without_yaml = content[yaml_match.end():]
                except yaml.YAMLError:
                    content_without_yaml = content
            else:
                content_without_yaml = content
            
            # Extract title (first H1 or filename)
            title_match = re.search(r'^#\s+(.+)$', content_without_yaml, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else Path(file_path).stem
            
            # Extract all tags (from YAML and inline)
            tags = set()
            
            # Tags from YAML frontmatter
            if 'tags' in yaml_frontmatter:
                if isinstance(yaml_frontmatter['tags'], list):
                    tags.update(yaml_frontmatter['tags'])
                elif isinstance(yaml_frontmatter['tags'], str):
                    tags.add(yaml_frontmatter['tags'])
            
            # Inline tags (format: #tag)
            inline_tags = re.findall(r'#([^\s#]+)', content)
            tags.update(f"#{tag}" for tag in inline_tags)
            
            # Extract H1 headings
            h1_headings = re.findall(r'^#\s+(.+)$', content_without_yaml, re.MULTILINE)
            
            # Extract core concepts (simplified - look for important phrases)
            core_concepts = self._extract_core_concepts(content_without_yaml)
            
            return DocumentMetadata(
                file_path=file_path,
                title=title,
                tags=tags,
                yaml_frontmatter=yaml_frontmatter,
                content=content_without_yaml,
                h1_headings=h1_headings,
                core_concepts=core_concepts
            )
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def _extract_core_concepts(self, content: str) -> List[str]:
        """Extract core concepts from document content"""
        # Remove markdown formatting
        clean_content = re.sub(r'[*_`~]', '', content)
        clean_content = re.sub(r'\[([^\]]+)\]', r'\1', clean_content)  # Remove link formatting
        
        # Find emphasized terms (common patterns for important concepts)
        concepts = []
        
        # Terms in headings
        headings = re.findall(r'^#+\s+(.+)$', clean_content, re.MULTILINE)
        concepts.extend(headings)
        
        # Terms in bold/italic (after cleanup, look for repeated important terms)
        # This is a simplified approach - in a real system you'd use NLP
        words = re.findall(r'\b[A-Z][a-zA-Z]+\b', clean_content)
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > MIN_WORD_LENGTH:  # Filter short words
                word_freq[word] += 1
        
        # Get most frequent important-looking terms
        frequent_concepts = [word for word, freq in word_freq.items() if freq >= MIN_CONCEPT_FREQUENCY][:MAX_FREQUENT_CONCEPTS]
        concepts.extend(frequent_concepts)
        
        return list(set(concepts))[:MAX_CONCEPTS_PER_DOC]
    
    def validate_tags(self, document: DocumentMetadata) -> bool:
        """Validate that document contains the required tag"""
        return self.target_tag in document.tags
    
    def process_documents(self) -> List[DocumentMetadata]:
        """Main processing pipeline for Task 1"""
        print(f"🔍 Searching for documents with tag: {self.target_tag}")
        tagged_files = self.find_tagged_documents()
        print(f"📄 Found {len(tagged_files)} files with target tag")
        
        processed_docs = []
        for file_path in tagged_files:
            doc = self.parse_markdown_document(file_path)
            if doc and self.validate_tags(doc):
                processed_docs.append(doc)
                print(f"✅ Processed: {Path(file_path).name}")
            else:
                print(f"❌ Skipped: {Path(file_path).name}")
        
        self.processed_documents = processed_docs
        print(f"📋 Total processed documents: {len(processed_docs)}")
        return processed_docs


class ThemeAnalysisEngine:
    """Task 2: Theme Analysis Engine - identifies core themes across documents"""
    
    def __init__(self, documents: List[DocumentMetadata]):
        self.documents = documents
        self.discovered_themes: List[Theme] = []
    
    def identify_core_themes(self) -> List[Theme]:
        """Identify independent, important core themes across all documents"""
        # Group documents by common concepts
        concept_to_docs = defaultdict(set)
        
        for doc in self.documents:
            for concept in doc.core_concepts:
                concept_to_docs[concept].add(doc.file_path)
        
        # Find concepts that appear in multiple documents (potential themes)
        potential_themes = {}
        for concept, doc_paths in concept_to_docs.items():
            if len(doc_paths) >= MIN_THEME_DOCS:  # Theme must appear in at least minimum documents
                potential_themes[concept] = doc_paths
        
        # Create Theme objects
        themes = []
        for theme_name, related_docs in potential_themes.items():
            # Calculate related concepts
            related_concepts = set()
            for doc in self.documents:
                if doc.file_path in related_docs:
                    related_concepts.update(doc.core_concepts)
            
            theme = Theme(
                name=theme_name,
                description=f"Core theme: {theme_name}",
                core_concepts=list(related_concepts)[:10],
                related_documents=list(related_docs),
                related_themes=set(),
                confidence_score=len(related_docs) / len(self.documents)
            )
            themes.append(theme)
        
        # Find theme relationships
        for i, theme1 in enumerate(themes):
            for j, theme2 in enumerate(themes):
                if i != j:
                    # Check for overlapping documents
                    overlap = set(theme1.related_documents) & set(theme2.related_documents)
                    if len(overlap) >= 1:
                        theme1.related_themes.add(theme2.name)
        
        # Sort by confidence score
        themes.sort(key=lambda t: t.confidence_score, reverse=True)
        
        self.discovered_themes = themes[:20]  # Limit to top 20 themes
        print(f"🎯 Discovered {len(self.discovered_themes)} core themes")
        
        return self.discovered_themes


class ContentGenerator:
    """Task 3: Content Generation System - creates theme files with structured content"""
    
    def __init__(self, themes: List[Theme], documents: List[DocumentMetadata]):
        self.themes = themes
        self.documents = documents
        self.doc_lookup = {doc.file_path: doc for doc in documents}
    
    def generate_intuitive_filename(self, theme: Theme) -> str:
        """Generate intuitive, descriptive filename using common language concepts"""
        # Clean theme name for filename
        clean_name = re.sub(r'[^\w\s-]', '', theme.name)
        clean_name = re.sub(r'\s+', '_', clean_name.strip())
        
        # Add descriptive prefix based on content type
        if any(keyword in theme.name.lower() for keyword in ['python', 'code', 'programming']):
            prefix = "编程概念"
        elif any(keyword in theme.name.lower() for keyword in ['math', '数学', '线性', '微积分']):
            prefix = "数学概念"
        elif any(keyword in theme.name.lower() for keyword in ['语言', 'language', '英语', '日语']):
            prefix = "语言学习"
        else:
            prefix = "知识主题"
        
        return f"{prefix}_{clean_name}.md"
    
    def generate_yaml_frontmatter(self, theme: Theme) -> Dict:
        """Generate YAML frontmatter with proper tag hierarchy"""
        current_date = datetime.now().strftime("%Y%m%d")
        
        # Determine main tag based on theme content
        main_tag = f"#{theme.name}"
        if any(keyword in theme.name.lower() for keyword in ['python', 'code']):
            main_tag = "#Python"
        elif any(keyword in theme.name.lower() for keyword in ['math', '数学']):
            main_tag = "#数学"
        elif any(keyword in theme.name.lower() for keyword in ['语言', 'language']):
            main_tag = "#语言学习"
        
        # Create unified tag
        domain = theme.name.split()[0] if theme.name else "通用"
        unified_tag = f"#{domain}_{current_date}"
        
        return {
            'title': theme.name,
            'tags': [main_tag, '#知识图谱索引', unified_tag],
            'created': datetime.now().isoformat(),
            'theme_type': 'macro_relationship',
            'confidence_score': theme.confidence_score,
            'related_themes': list(theme.related_themes)
        }
    
    def generate_theme_content(self, theme: Theme) -> str:
        """Generate structured content with multi-level explanations and analogies"""
        content_parts = []
        
        # Core insights section
        content_parts.append("## 核心洞察")
        content_parts.append(f"\n{theme.description}")
        content_parts.append(f"\n**主要概念**: {', '.join(theme.core_concepts[:5])}")
        
        # Multi-level explanation with analogy
        content_parts.append("\n## 深度理解")
        content_parts.append("\n### 基础概念")
        content_parts.append(f"这个主题围绕 **{theme.name}** 展开，涉及多个相关概念的有机结合。")
        
        content_parts.append("\n### 形象比喻")
        content_parts.append(f"可以把 {theme.name} 想象成一个知识网络的中心节点，")
        content_parts.append("各个相关概念像是连接到这个中心的分支，共同构成一个完整的知识体系。")
        
        content_parts.append("\n### 记忆锚点")
        content_parts.append(f"记住关键词：**{theme.core_concepts[0] if theme.core_concepts else theme.name}**")
        content_parts.append("当遇到相关问题时，以此为起点展开思考。")
        
        # Related original documents
        content_parts.append("\n## 相关原始文档")
        for doc_path in theme.related_documents:
            if doc_path in self.doc_lookup:
                doc = self.doc_lookup[doc_path]
                doc_name = Path(doc_path).stem
                content_parts.append(f"- [[{doc_name}]] - {doc.title}")
        
        # Related themes exploration
        content_parts.append("\n## 相关主题探索")
        if theme.related_themes:
            for related_theme in list(theme.related_themes)[:5]:
                content_parts.append(f"- [[{related_theme}]] - 探索相关联的概念")
        else:
            content_parts.append("- 暂无直接相关主题，这是一个相对独立的概念领域")
        
        # Quick review section
        content_parts.append("\n## 快速回顾与内化")
        content_parts.append("### 关键问题")
        content_parts.append(f"1. {theme.name} 的核心特征是什么？")
        content_parts.append("2. 它与其他概念有何联系？")
        content_parts.append("3. 在实际应用中如何体现？")
        
        content_parts.append("\n### 实践建议")
        content_parts.append(f"定期回顾相关文档，深化对 {theme.name} 的理解。")
        content_parts.append("尝试将这个概念与新学到的知识建立连接。")
        
        return '\n'.join(content_parts)
    
    def generate_theme_files(self) -> List[Tuple[str, str, str]]:
        """Generate all theme files with content"""
        generated_files = []
        
        for theme in self.themes:
            filename = self.generate_intuitive_filename(theme)
            yaml_frontmatter = self.generate_yaml_frontmatter(theme)
            content = self.generate_theme_content(theme)
            
            # Combine YAML frontmatter with content
            yaml_str = yaml.dump(yaml_frontmatter, default_flow_style=False, allow_unicode=True)
            full_content = f"---\n{yaml_str}---\n\n# {theme.name}\n\n{content}"
            
            generated_files.append((filename, full_content, theme.name))
            
        print(f"📝 Generated {len(generated_files)} theme files")
        return generated_files


class LinkingSystem:
    """Task 4: Linking and Reference System - manages Obsidian-compatible links"""
    
    def __init__(self, themes: List[Theme], documents: List[DocumentMetadata]):
        self.themes = themes
        self.documents = documents
        self.theme_lookup = {theme.name: theme for theme in themes}
    
    def generate_obsidian_links(self, content: str, theme_name: str) -> str:
        """Generate proper Obsidian [[]] links in content"""
        # Link to related themes
        for theme in self.themes:
            if theme.name != theme_name and theme.name in content:
                # Replace theme name with link (avoid double-linking)
                pattern = r'\b' + re.escape(theme.name) + r'\b(?!\]\])'
                content = re.sub(pattern, f'[[{theme.name}]]', content, count=1)
        
        return content
    
    def create_bidirectional_links(self, generated_files: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        """Create bidirectional linking between theme files"""
        updated_files = []
        
        for filename, content, theme_name in generated_files:
            # Add cross-references to related themes
            if theme_name in self.theme_lookup:
                theme = self.theme_lookup[theme_name]
                
                # Update content with proper links
                updated_content = self.generate_obsidian_links(content, theme_name)
                
                # Add backlinks section if there are related themes
                if theme.related_themes:
                    backlinks_section = "\n\n## 反向链接\n"
                    backlinks_section += "以下主题引用了本概念：\n"
                    for related in theme.related_themes:
                        backlinks_section += f"- [[{related}]]\n"
                    updated_content += backlinks_section
                
                updated_files.append((filename, updated_content, theme_name))
            else:
                updated_files.append((filename, content, theme_name))
        
        print(f"🔗 Updated {len(updated_files)} files with bidirectional links")
        return updated_files


class OutputManager:
    """Task 5: Output Management System - handles batch file output and validation"""
    
    def __init__(self, output_directory: str):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def validate_markdown_compatibility(self, content: str) -> bool:
        """Validate generated Markdown compatibility"""
        # Basic validation checks
        checks = [
            content.strip(),  # Not empty
            '---' in content,  # Has frontmatter
            content.count('---') >= 2,  # Proper frontmatter structure
            '# ' in content,  # Has main heading
        ]
        return all(checks)
    
    def output_batch_files(self, files: List[Tuple[str, str, str]]) -> List[str]:
        """Output all generated files with separation markers"""
        output_paths = []
        
        print("\n" + "="*60)
        print("📄 GENERATING THEME FILES")
        print("="*60)
        
        for i, (filename, content, theme_name) in enumerate(files, 1):
            if not self.validate_markdown_compatibility(content):
                print(f"❌ Validation failed for {filename}")
                continue
            
            output_path = self.output_directory / filename
            
            try:
                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(content)
                
                output_paths.append(str(output_path))
                
                print(f"\n{'─'*40}")
                print(f"📝 FILE {i}/{len(files)}: {filename}")
                print(f"🎯 THEME: {theme_name}")
                print(f"📍 PATH: {output_path}")
                print(f"✅ STATUS: Generated successfully")
                
            except (IOError, OSError) as e:
                print(f"❌ Error writing {filename}: {e}")
            except Exception as e:
                print(f"❌ Unexpected error writing {filename}: {e}")
        
        print("\n" + "="*60)
        print(f"✅ BATCH COMPLETE: {len(output_paths)} files generated")
        print("="*60)
        
        return output_paths
    
    def generate_overview(self, files: List[str], themes: List[Theme]) -> str:
        """Generate overview of created themes and links"""
        overview_content = []
        
        overview_content.append("# 知识图谱主题概览")
        overview_content.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        overview_content.append(f"主题数量: {len(themes)}")
        overview_content.append(f"生成文件: {len(files)}")
        
        overview_content.append("\n## 主题列表")
        for theme in themes:
            overview_content.append(f"- [[{theme.name}]] (置信度: {theme.confidence_score:.2f})")
        
        overview_content.append("\n## 主题关系网络")
        for theme in themes:
            if theme.related_themes:
                overview_content.append(f"\n### {theme.name}")
                for related in theme.related_themes:
                    overview_content.append(f"  - → [[{related}]]")
        
        overview_content.append("\n## 生成的文件")
        for file_path in files:
            filename = Path(file_path).name
            overview_content.append(f"- {filename}")
        
        overview_path = self.output_directory / "知识图谱_主题概览.md"
        try:
            overview_path.parent.mkdir(parents=True, exist_ok=True)
            with open(overview_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write('\n'.join(overview_content))
        except Exception as e:
            print(f"❌ Error writing overview file: {e}")
            return None
        
        print(f"📊 Overview generated: {overview_path}")
        return str(overview_path)


class MacroGraphBuilder:
    """Main orchestrator class that coordinates all components"""
    
    def __init__(self, vault_path: str, target_tag: str = "#我的课堂总结", 
                 output_path: str = None):
        self.vault_path = vault_path
        self.target_tag = target_tag
        self.output_path = output_path or os.path.join(vault_path, "generated_themes")
        
        # Initialize components
        self.input_processor = InputProcessor(vault_path, target_tag)
        self.theme_engine = None
        self.content_generator = None
        self.linking_system = None
        self.output_manager = OutputManager(self.output_path)
    
    def build_macro_graph(self) -> Dict:
        """Main execution pipeline - orchestrates all tasks"""
        print("🚀 Starting Macro Document Relationship Graph Construction")
        print(f"📂 Vault Path: {self.vault_path}")
        print(f"🏷️  Target Tag: {self.target_tag}")
        print(f"📤 Output Path: {self.output_path}")
        
        try:
            # Task 1: Input Processing
            print("\n" + "="*50)
            print("📋 TASK 1: INPUT PROCESSING")
            print("="*50)
            documents = self.input_processor.process_documents()
            if not documents:
                raise Exception("No documents found with target tag")
            
            # Task 2: Theme Analysis
            print("\n" + "="*50)
            print("🎯 TASK 2: THEME ANALYSIS")
            print("="*50)
            self.theme_engine = ThemeAnalysisEngine(documents)
            themes = self.theme_engine.identify_core_themes()
            if not themes:
                raise Exception("No themes discovered")
            
            # Task 3: Content Generation
            print("\n" + "="*50)
            print("📝 TASK 3: CONTENT GENERATION")
            print("="*50)
            self.content_generator = ContentGenerator(themes, documents)
            generated_files = self.content_generator.generate_theme_files()
            
            # Task 4: Linking System
            print("\n" + "="*50)
            print("🔗 TASK 4: LINKING SYSTEM")
            print("="*50)
            self.linking_system = LinkingSystem(themes, documents)
            linked_files = self.linking_system.create_bidirectional_links(generated_files)
            
            # Task 5: Output Management
            print("\n" + "="*50)
            print("📤 TASK 5: OUTPUT MANAGEMENT")
            print("="*50)
            output_paths = self.output_manager.output_batch_files(linked_files)
            overview_path = self.output_manager.generate_overview(output_paths, themes)
            
            # Final summary
            result = {
                'success': True,
                'documents_processed': len(documents),
                'themes_discovered': len(themes),
                'files_generated': len(output_paths),
                'output_directory': self.output_path,
                'overview_file': overview_path,
                'generated_files': output_paths
            }
            
            print("\n" + "🎉"*20)
            print("✅ MACRO GRAPH CONSTRUCTION COMPLETE!")
            print("🎉"*20)
            print(f"📄 Documents processed: {result['documents_processed']}")
            print(f"🎯 Themes discovered: {result['themes_discovered']}")
            print(f"📝 Files generated: {result['files_generated']}")
            print(f"📊 Overview file: {Path(overview_path).name}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            return {'success': False, 'error': str(e)}


def main():
    """Main entry point for the system"""
    # Configuration
    VAULT_PATH = r"C:\Users\ROG\托福\笔记库"
    TARGET_TAG = "#我的课堂总结"
    
    # Create and run the builder
    builder = MacroGraphBuilder(
        vault_path=VAULT_PATH,
        target_tag=TARGET_TAG
    )
    
    result = builder.build_macro_graph()
    
    if result['success']:
        print(f"\n🎯 Success! Check your output directory: {result['output_directory']}")
    else:
        print(f"\n❌ Failed: {result['error']}")


if __name__ == "__main__":
    main()