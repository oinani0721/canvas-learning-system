#!/usr/bin/env python3
"""
Micro Document Internal Knowledge Point Graph Construction System
Story 2.1 Implementation

This system analyzes a single document and creates micro-level knowledge point files
with relationships between them for Obsidian vault integration.
"""

import os
import re
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class KnowledgePoint:
    """Represents a single knowledge point extracted from the document."""
    id: str
    title: str
    summary: str
    image_description: str = ""
    video_timeline: str = ""
    source_section: str = ""
    source_line_start: int = 0
    source_line_end: int = 0
    related_points: List[str] = None
    main_tag: str = ""
    unified_tag: str = ""
    
    def __post_init__(self):
        if self.related_points is None:
            self.related_points = []


class MicroDocumentAnalyzer:
    """Main class for micro document analysis and knowledge point extraction."""
    
    def __init__(self, output_dir: str = r"C:\Users\ROG\托福\笔记库"):
        self.output_dir = Path(output_dir)
        self.knowledge_points: List[KnowledgePoint] = []
        self.original_doc_path: str = ""
        self.original_doc_name: str = ""
        self.hub_file_name: str = ""
        
    def process_document(self, document_path: str) -> Dict[str, str]:
        """
        Process a single document and extract knowledge points.
        
        Task 1: Single Document Processing System
        - Implement single document input processing with content validation
        - Parse complete Markdown document structure including metadata
        - Validate document format and extract core content sections
        """
        try:
            # Validate input document
            doc_path = Path(document_path)
            if not doc_path.exists():
                raise FileNotFoundError(f"Document not found: {document_path}")
            
            self.original_doc_path = str(doc_path)
            self.original_doc_name = doc_path.stem
            
            # Read document content
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse document structure
            lines = content.split('\n')
            
            # Extract YAML frontmatter if present
            frontmatter = self._extract_frontmatter(lines)
            
            # Identify knowledge point blocks
            self.knowledge_points = self._identify_knowledge_points(lines)
            
            if not self.knowledge_points:
                raise ValueError("No knowledge points found in document")
            
            # Generate relationships between knowledge points
            self._generate_relationships()
            
            # Generate all output files
            return self._generate_all_files()
            
        except Exception as e:
            return {"error": f"Document processing failed: {str(e)}"}
    
    def _extract_frontmatter(self, lines: List[str]) -> Dict:
        """Extract YAML frontmatter from document if present."""
        frontmatter = {}
        if lines and lines[0].strip() == '---':
            # Find end of frontmatter
            end_index = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    end_index = i
                    break
            
            if end_index > 0:
                frontmatter_text = '\n'.join(lines[1:end_index])
                try:
                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                except yaml.YAMLError:
                    pass
        
        return frontmatter
    
    def _identify_knowledge_points(self, lines: List[str]) -> List[KnowledgePoint]:
        """
        Task 2: Knowledge Point Identification Engine
        - Develop knowledge point block detection algorithm for "image+timeline+summary" patterns
        - Implement summary-centric knowledge point extraction logic
        - Create knowledge point prioritization and categorization system
        """
        knowledge_points = []
        current_point = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for potential knowledge point patterns
            if self._is_knowledge_point_start(line, lines, i):
                # Save previous point if exists
                if current_point and current_point.summary:
                    knowledge_points.append(current_point)
                
                # Start new knowledge point
                current_point = KnowledgePoint(
                    id=f"kp_{len(knowledge_points) + 1:03d}",
                    title="",
                    summary="",
                    source_line_start=i + 1
                )
            
            # Extract content based on patterns
            if current_point:
                self._extract_content_to_point(current_point, line, lines, i)
            
            i += 1
        
        # Add final point
        if current_point and current_point.summary:
            current_point.source_line_end = len(lines)
            knowledge_points.append(current_point)
        
        return knowledge_points
    
    def _is_knowledge_point_start(self, line: str, lines: List[str], index: int) -> bool:
        """Detect if current line starts a new knowledge point block."""
        # Look for patterns that indicate knowledge point starts
        patterns = [
            r'^#{1,3}\s+',  # Headers
            r'^\*\*.*图.*\*\*',  # Image descriptions
            r'^\*\*.*视频.*\*\*',  # Video descriptions
            r'^\d+\.\s+',  # Numbered items
            r'^-\s+.*图.*',  # Bulleted image items
            r'^!\[.*\]',  # Image markdown
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        
        # Check for "image + timeline + summary" pattern in next few lines
        if index < len(lines) - 3:
            next_lines = [lines[i].lower() for i in range(index, min(index + 5, len(lines)))]
            has_image = any('图' in line or 'image' in line for line in next_lines)
            has_timeline = any('时间' in line or 'timeline' in line or ':' in line for line in next_lines)
            has_summary = any('总结' in line or 'summary' in line or '要点' in line for line in next_lines)
            
            if has_image and (has_timeline or has_summary):
                return True
        
        return False
    
    def _extract_content_to_point(self, point: KnowledgePoint, line: str, lines: List[str], index: int):
        """Extract content into appropriate fields of knowledge point."""
        line_lower = line.lower()
        
        # Extract title from headers
        if re.match(r'^#{1,3}\s+', line) and not point.title:
            point.title = re.sub(r'^#{1,3}\s+', '', line).strip()
        
        # Extract image descriptions
        if ('图' in line_lower or 'image' in line_lower) and not point.image_description:
            point.image_description = line.strip()
        
        # Extract video timeline
        if ('时间' in line_lower or 'timeline' in line_lower or re.search(r'\d+:\d+', line)) and not point.video_timeline:
            point.video_timeline = line.strip()
        
        # Extract summary (prioritize content with summary keywords)
        if ('总结' in line_lower or 'summary' in line_lower or '要点' in line_lower or 
            '关键' in line_lower or 'key' in line_lower):
            if not point.summary:
                point.summary = line.strip()
            else:
                point.summary += " " + line.strip()
        
        # If no explicit summary found, accumulate meaningful content
        elif not point.summary and line.strip() and not self._is_structural_element(line):
            if len(line.strip()) > 10:  # Only meaningful content
                point.summary = line.strip()
        
        # Update source section info
        point.source_line_end = index + 1
        if not point.source_section and point.title:
            point.source_section = point.title
    
    def _is_structural_element(self, line: str) -> bool:
        """Check if line is a structural element (not content)."""
        structural_patterns = [
            r'^---+$',  # Horizontal rules
            r'^\s*$',   # Empty lines
            r'^\[.*\]:',  # Link definitions
            r'^```',    # Code blocks
        ]
        
        for pattern in structural_patterns:
            if re.match(pattern, line.strip()):
                return True
        return False
    
    def _generate_relationships(self):
        """
        Task 4: Source Reference and Linking System (partial)
        - Build knowledge point relationship mapping within document context
        - Create bidirectional linking between related knowledge point files
        """
        # Simple relationship detection based on content similarity and proximity
        for i, point1 in enumerate(self.knowledge_points):
            for j, point2 in enumerate(self.knowledge_points):
                if i != j and self._are_related(point1, point2):
                    if point2.id not in point1.related_points:
                        point1.related_points.append(point2.id)
    
    def _are_related(self, point1: KnowledgePoint, point2: KnowledgePoint) -> bool:
        """Determine if two knowledge points are related."""
        # Check proximity (within 10 source lines)
        if abs(point1.source_line_start - point2.source_line_start) <= 10:
            return True
        
        # Check content similarity (simple keyword matching)
        words1 = set(re.findall(r'\w+', point1.summary.lower()))
        words2 = set(re.findall(r'\w+', point2.summary.lower()))
        
        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1.intersection(words2))
            similarity = overlap / min(len(words1), len(words2))
            return similarity > 0.3
        
        return False
    
    def _generate_all_files(self) -> Dict[str, str]:
        """
        Task 7: Batch Output Management System
        - Implement coordinated file output with separation markers
        - Create overview generation for all created knowledge points and hub
        - Add validation for generated Markdown compatibility and link integrity
        """
        results = {}
        
        try:
            # Generate knowledge point files
            for point in self.knowledge_points:
                filename, content = self._generate_knowledge_point_file(point)
                results[filename] = content
            
            # Generate hub file
            hub_filename, hub_content = self._generate_hub_file()
            results[hub_filename] = hub_content
            self.hub_file_name = hub_filename
            
            # Update original document
            original_update = self._generate_original_document_update()
            results[f"UPDATE_{self.original_doc_name}.md"] = original_update
            
            # Write all files to output directory
            self._write_files_to_disk(results)
            
            return results
            
        except Exception as e:
            return {"error": f"File generation failed: {str(e)}"}
    
    def _generate_knowledge_point_file(self, point: KnowledgePoint) -> Tuple[str, str]:
        """
        Task 3: Knowledge Point File Generation System
        - Implement intuitive file naming generator based on summary content
        - Build structured knowledge point content template system
        - Create YAML frontmatter generator with proper tag management
        - Develop multi-level explanation and analogy generation focused on summary content
        """
        # Generate intuitive filename
        filename = self._generate_filename(point)
        
        # Generate tags
        main_tag, unified_tag = self._generate_tags(point)
        point.main_tag = main_tag
        point.unified_tag = unified_tag
        
        # Generate content with multi-level explanations
        content = self._generate_knowledge_point_content(point)
        
        return filename, content
    
    def _generate_filename(self, point: KnowledgePoint) -> str:
        """Generate intuitive filename based on summary content."""
        # Extract key concepts from summary
        summary_text = point.summary if point.summary else point.title
        
        # Clean and extract meaningful words
        words = re.findall(r'\w+', summary_text)
        meaningful_words = [w for w in words if len(w) > 2 and w.lower() not in ['的', '和', '与', '是', '有', '在', '了', 'the', 'and', 'of', 'to', 'in', 'is', 'it']]
        
        # Take first 3-4 meaningful words
        key_words = meaningful_words[:4] if len(meaningful_words) >= 4 else meaningful_words
        
        if not key_words:
            key_words = [f"知识点_{point.id}"]
        
        filename = "_".join(key_words) + ".md"
        
        # Ensure filename is valid
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        return filename
    
    def _generate_tags(self, point: KnowledgePoint) -> Tuple[str, str]:
        """Generate main tag and unified tag for knowledge point."""
        # Determine main tag based on content analysis
        summary_lower = point.summary.lower() if point.summary else ""
        
        if any(word in summary_lower for word in ['python', '编程', 'program']):
            main_tag = "#Python"
        elif any(word in summary_lower for word in ['数学', 'math', '公式']):
            main_tag = "#数学"
        elif any(word in summary_lower for word in ['英语', 'english', '语法']):
            main_tag = "#英语"
        elif any(word in summary_lower for word in ['物理', 'physics']):
            main_tag = "#物理"
        else:
            main_tag = "#通用知识"
        
        # Generate unified tag
        today = datetime.now().strftime("%Y%m%d")
        domain = main_tag.replace("#", "")
        unified_tag = f"#{domain}_{today}"
        
        return main_tag, unified_tag
    
    def _generate_knowledge_point_content(self, point: KnowledgePoint) -> str:
        """Generate structured content for knowledge point file."""
        content_parts = []
        
        # YAML frontmatter
        frontmatter = {
            "tags": [point.main_tag.replace("#", ""), "知识图谱索引", point.unified_tag.replace("#", "")],
            "source": f"[[{self.original_doc_name}#{point.source_section}]]",
            "created": datetime.now().isoformat(),
            "knowledge_point_id": point.id
        }
        
        content_parts.append("---")
        content_parts.append(yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False))
        content_parts.append("---")
        content_parts.append("")
        
        # Main title
        title = point.title if point.title else f"知识点 {point.id}"
        content_parts.append(f"# {title}")
        content_parts.append("")
        
        # Core explanation section
        content_parts.append("## 核心解释")
        content_parts.append("")
        if point.summary:
            content_parts.append(point.summary)
        content_parts.append("")
        
        # Multi-level explanations and analogies
        content_parts.append("## 深入理解")
        content_parts.append("")
        content_parts.append("### 详细说明")
        content_parts.append(self._generate_detailed_explanation(point))
        content_parts.append("")
        
        content_parts.append("### 生动类比")
        content_parts.append(self._generate_analogy(point))
        content_parts.append("")
        
        content_parts.append("### 记忆锚点")
        content_parts.append(self._generate_memory_anchor(point))
        content_parts.append("")
        
        # Source references
        content_parts.append("## 来源参考")
        content_parts.append("")
        content_parts.append(f"- **原文档**: [[{self.original_doc_name}#{point.source_section}]]")
        if point.image_description:
            content_parts.append(f"- **图像描述**: {point.image_description}")
        if point.video_timeline:
            content_parts.append(f"- **视频时间轴**: {point.video_timeline}")
        content_parts.append(f"- **源位置**: 第{point.source_line_start}-{point.source_line_end}行")
        content_parts.append("")
        
        # Related knowledge points
        if point.related_points:
            content_parts.append("## 相关知识点")
            content_parts.append("")
            for related_id in point.related_points:
                related_point = next((kp for kp in self.knowledge_points if kp.id == related_id), None)
                if related_point:
                    related_filename = self._generate_filename(related_point)
                    content_parts.append(f"- [[{related_filename.replace('.md', '')}]]")
            content_parts.append("")
        
        return "\n".join(content_parts)
    
    def _generate_detailed_explanation(self, point: KnowledgePoint) -> str:
        """Generate detailed explanation based on summary content."""
        if not point.summary:
            return "需要根据具体内容进行详细解释。"
        
        # Simple expansion of the summary
        base_text = point.summary
        expansion = f"""
{base_text}

这个知识点的核心在于理解其基本概念和应用场景。通过深入分析，我们可以看到它在整体知识体系中的重要位置。

关键要素包括：
- 基本定义和概念框架
- 实际应用和案例分析  
- 与其他知识点的关联性
- 掌握的方法和技巧
"""
        return expansion.strip()
    
    def _generate_analogy(self, point: KnowledgePoint) -> str:
        """Generate vivid analogy for the knowledge point."""
        return f"""
就像搭建积木一样，{point.title or '这个知识点'}是整个知识体系中的一个重要组件。

想象一下：
- 如果把整个学科比作一座大厦，那么这个知识点就是其中一块重要的基石
- 它与其他知识点相互连接，形成了稳固的知识网络
- 掌握了这个要点，就像掌握了一把钥匙，能够开启更深层次的理解之门

这种理解方式帮助我们将抽象概念具象化，更容易记忆和应用。
"""
    
    def _generate_memory_anchor(self, point: KnowledgePoint) -> str:
        """Generate memory anchor for better retention."""
        return f"""
**记忆口诀**: 围绕"{point.title or '核心概念'}"构建记忆网络

**记忆技巧**:
1. **关键词联想**: 抓住核心关键词进行联想记忆
2. **情境记忆**: 将知识点与具体应用场景结合
3. **反复回顾**: 定期回顾相关内容，强化记忆路径
4. **关联记忆**: 与已掌握的知识点建立联系

**快速回忆提示**: {point.summary[:50] if point.summary else '参考核心解释部分'}...
"""
    
    def _generate_hub_file(self) -> Tuple[str, str]:
        """
        Task 5: Hub File Creation System
        - Implement central hub file generator with relationship visualization
        - Build knowledge point relationship mapping in text format
        - Create navigable overview with clear relationship descriptions
        - Generate intuitive relationship categories and groupings
        """
        hub_filename = f"{self.original_doc_name}_知识图谱中控.md"
        
        content_parts = []
        
        # YAML frontmatter for hub
        frontmatter = {
            "tags": ["知识图谱索引", "中控文件"],
            "source_document": f"[[{self.original_doc_name}]]",
            "created": datetime.now().isoformat(),
            "knowledge_point_count": len(self.knowledge_points)
        }
        
        content_parts.append("---")
        content_parts.append(yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False))
        content_parts.append("---")
        content_parts.append("")
        
        # Hub title
        content_parts.append(f"# {self.original_doc_name} - 知识图谱中控")
        content_parts.append("")
        
        # Overview section
        content_parts.append("## 文档概览")
        content_parts.append("")
        content_parts.append(f"本文档包含 **{len(self.knowledge_points)}** 个知识点，基于原文档 [[{self.original_doc_name}]] 分析生成。")
        content_parts.append("")
        
        # Knowledge points list
        content_parts.append("## 知识点导航")
        content_parts.append("")
        
        for i, point in enumerate(self.knowledge_points, 1):
            filename = self._generate_filename(point)
            title = point.title if point.title else f"知识点 {point.id}"
            summary_preview = point.summary[:80] + "..." if point.summary and len(point.summary) > 80 else point.summary
            
            content_parts.append(f"### {i}. [[{filename.replace('.md', '')}|{title}]]")
            if summary_preview:
                content_parts.append(f"   *{summary_preview}*")
            content_parts.append("")
        
        # Relationship mapping
        content_parts.append("## 知识点关系图")
        content_parts.append("")
        content_parts.append("### 关系概览")
        
        # Group by relationships
        relationship_groups = self._create_relationship_groups()
        
        for group_name, points in relationship_groups.items():
            content_parts.append(f"#### {group_name}")
            content_parts.append("")
            for point in points:
                filename = self._generate_filename(point)
                content_parts.append(f"- [[{filename.replace('.md', '')}]]")
                if point.related_points:
                    content_parts.append("  - 相关: ")
                    for related_id in point.related_points:
                        related_point = next((kp for kp in self.knowledge_points if kp.id == related_id), None)
                        if related_point:
                            related_filename = self._generate_filename(related_point)
                            content_parts.append(f"    - [[{related_filename.replace('.md', '')}]]")
            content_parts.append("")
        
        # Navigation instructions
        content_parts.append("## 使用说明")
        content_parts.append("")
        content_parts.append("1. **快速浏览**: 通过上方的知识点导航快速定位感兴趣的内容")
        content_parts.append("2. **深入学习**: 点击任意知识点标题进入详细页面")
        content_parts.append("3. **关联学习**: 利用关系图发现知识点间的内在联系")
        content_parts.append("4. **源文档参考**: 每个知识点都包含回到原文档的精确链接")
        content_parts.append("")
        
        return hub_filename, "\n".join(content_parts)
    
    def _create_relationship_groups(self) -> Dict[str, List[KnowledgePoint]]:
        """Create intuitive groupings of knowledge points based on relationships."""
        groups = {
            "核心概念群": [],
            "应用实践群": [],  
            "相关概念群": [],
            "独立概念": []
        }
        
        # Simple grouping based on content and relationships
        for point in self.knowledge_points:
            if len(point.related_points) >= 2:
                groups["核心概念群"].append(point)
            elif len(point.related_points) == 1:
                groups["相关概念群"].append(point)
            elif any(word in point.summary.lower() for word in ['应用', '实践', '例子', '案例']):
                groups["应用实践群"].append(point)
            else:
                groups["独立概念"].append(point)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _generate_original_document_update(self) -> str:
        """
        Task 6: Original Document Integration
        - Implement minimal modification system for original documents
        - Add hub file reference link at document top/bottom
        - Preserve original document structure and content integrity
        """
        try:
            # Read original document
            with open(self.original_doc_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Add hub file link at the top (after frontmatter if exists)
            lines = original_content.split('\n')
            
            # Find insertion point (after frontmatter or at beginning)
            insert_index = 0
            if lines and lines[0].strip() == '---':
                # Skip frontmatter
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == '---':
                        insert_index = i + 1
                        break
            
            # Insert hub file link
            hub_link = f"\n> **知识图谱导航**: [[{self.hub_file_name.replace('.md', '')}]] - 查看本文档的详细知识图谱\n"
            
            lines.insert(insert_index, hub_link)
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"Error updating original document: {str(e)}"
    
    def _write_files_to_disk(self, files: Dict[str, str]):
        """Write all generated files to the output directory."""
        try:
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            for filename, content in files.items():
                if filename.startswith("UPDATE_"):
                    # Handle original document update separately
                    original_path = Path(self.original_doc_path)
                    backup_path = original_path.with_suffix('.backup.md')
                    
                    # Create backup
                    if original_path.exists():
                        import shutil
                        shutil.copy2(original_path, backup_path)
                    
                    # Write updated content
                    with open(original_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                else:
                    # Write knowledge point and hub files
                    file_path = self.output_dir / filename
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
        except Exception as e:
            print(f"Warning: Could not write files to disk: {str(e)}")


def main():
    """Main function for command-line usage."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python micro_document_analyzer.py <document_path>")
        sys.exit(1)
    
    document_path = sys.argv[1]
    
    analyzer = MicroDocumentAnalyzer()
    results = analyzer.process_document(document_path)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        sys.exit(1)
    
    print("=" * 60)
    print("微观文档知识点图谱构建系统 - 处理完成")
    print("=" * 60)
    print(f"原文档: {document_path}")
    print(f"输出目录: {analyzer.output_dir}")
    print(f"生成文件数: {len(results)}")
    print(f"知识点数量: {len(analyzer.knowledge_points)}")
    print()
    
    print("生成的文件:")
    for filename in sorted(results.keys()):
        if not filename.startswith("UPDATE_"):
            print(f"  ✓ {filename}")
    
    print()
    print("知识点概览:")
    for i, point in enumerate(analyzer.knowledge_points, 1):
        title = point.title if point.title else f"知识点 {point.id}"
        print(f"  {i}. {title}")
        if point.summary:
            preview = point.summary[:60] + "..." if len(point.summary) > 60 else point.summary
            print(f"     {preview}")
    
    print()
    print("=" * 60)
    print("系统处理完成！请在Obsidian中查看生成的文件。")
    print("=" * 60)


if __name__ == "__main__":
    main()