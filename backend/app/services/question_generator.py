# Canvas Learning System - Question Generator Service
# PRD Story 4.2: Deep Verification Question Generation
# [Source: docs/prd/FULL-PRD-REFERENCE.md - Story 4.2]
"""
Question Generator Service for Verification Canvas.

Generates three types of questions based on node color:
- Breakthrough (红色节点): Core concept questions for things not understood
- Verification (紫色节点): Deep verification questions for partial understanding
- Application (应用型): Practical application scenarios

[Source: PRD F8 + Story 4.2]
"""

import re
from typing import Dict, List, Literal, Optional

QuestionType = Literal["breakthrough", "verification", "application"]


class QuestionGenerator:
    """
    PRD Story 4.2: Deep Verification Question Generation

    - 突破型问题 (Breakthrough): 针对红色节点的核心疑问
    - 检验型问题 (Verification): 验证紫色节点是否真正理解
    - 应用型问题 (Application): 知识的实际应用场景

    Each node generates 1-2 questions.
    Question generation should complete within <5 seconds.
    """

    # Question templates for different types
    BREAKTHROUGH_TEMPLATES = [
        "请用自己的话解释：{concept}",
        "{concept} 的核心原理是什么？",
        "为什么 {concept}？请从根本原因分析",
        "如果要向初学者解释 {concept}，你会怎么说？",
    ]

    VERIFICATION_TEMPLATES = [
        "请详细描述 {concept} 的工作机制",
        "验证理解：{concept} 与什么概念相关？有何区别？",
        "{concept} 在什么情况下适用？什么情况下不适用？",
        "请举一个具体例子来说明 {concept}",
    ]

    APPLICATION_TEMPLATES = [
        "{concept} 可以应用在哪些实际场景中？",
        "如何使用 {concept} 解决实际问题？",
        "设计一个使用 {concept} 的案例",
    ]

    def __init__(self):
        """Initialize the question generator."""
        self._template_index = 0

    def generate_questions(
        self,
        node: Dict,
        question_type: Optional[QuestionType] = None
    ) -> List[str]:
        """
        Generate 1-2 verification questions for a single node.

        Args:
            node: Canvas node dict with 'text' and 'color' fields
            question_type: Optional override for question type

        Returns:
            List of 1-2 question strings

        PRD Story 4.2 AC:
        - 每个节点生成1-2个问题
        - 问题生成耗时<5秒
        """
        content = node.get("text", "").strip()
        color = node.get("color", "")

        # Skip empty nodes
        if not content:
            return []

        # Extract core concept from content
        concept = self._extract_concept(content)

        # Determine question type based on color if not specified
        # Color codes (Obsidian Canvas actual): "4"=red, "3"=purple, "2"=green, "6"=yellow
        if question_type is None:
            if color == "4":  # Red - not understood (修复: 4才是红色)
                question_type = "breakthrough"
            elif color == "3":  # Purple - partial understanding
                question_type = "verification"
            else:
                question_type = "application"

        # Select templates based on type
        templates = self._get_templates(question_type)

        # Generate questions using templates
        questions = []
        for template in templates[:2]:  # Max 2 questions
            question = template.format(concept=concept)
            questions.append(question)

        return questions

    def _extract_concept(self, content: str) -> str:
        """
        Extract the core concept from node content.

        Handles various content formats:
        - Simple text: use as-is
        - Markdown headers: extract header text
        - Multi-line: use first line
        - Long content: truncate to key phrase
        """
        # Remove markdown formatting
        content = re.sub(r'^#+\s*', '', content)  # Remove headers
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Remove bold
        content = re.sub(r'\*([^*]+)\*', r'\1', content)  # Remove italic

        # Get first line if multi-line
        first_line = content.split('\n')[0].strip()

        # Truncate if too long (keep first 50 chars)
        if len(first_line) > 50:
            # Try to find a natural break point
            break_points = ['. ', '，', '：', '。', ' - ']
            for bp in break_points:
                idx = first_line.find(bp)
                if 10 < idx < 50:
                    return first_line[:idx]
            return first_line[:50] + "..."

        return first_line if first_line else content[:50]

    def _get_templates(self, question_type: QuestionType) -> List[str]:
        """Get question templates for the specified type."""
        if question_type == "breakthrough":
            return self.BREAKTHROUGH_TEMPLATES
        elif question_type == "verification":
            return self.VERIFICATION_TEMPLATES
        else:
            return self.APPLICATION_TEMPLATES

    def generate_for_nodes(
        self,
        nodes: List[Dict]
    ) -> Dict[str, List[str]]:
        """
        Generate questions for multiple nodes.

        Args:
            nodes: List of Canvas nodes

        Returns:
            Dict mapping node_id to list of questions
        """
        result = {}
        for node in nodes:
            node_id = node.get("id", "")
            if node_id:
                questions = self.generate_questions(node)
                result[node_id] = questions
        return result
