# Canvas Learning System - Story 12.E.1 Tests
# ✅ Verified from pytest documentation
"""
Story 12.E.1 - comparison-table concepts Array Format Tests

Tests for _extract_comparison_concepts() and call_explanation() JSON construction:
- AC 1: comparison-table Agent receives `concepts` array (>=2 elements)
- AC 2: Other Agents still receive `concept` string (backward compatibility)
- AC 3: Unit tests cover _extract_comparison_concepts() logic
- AC 4: Smart topic extraction (skip metadata rows) preserved
- AC 5: Logging records concepts array content

[Source: docs/stories/story-12.E.1-prompt-format-alignment.md#Testing]
[Source: .claude/agents/comparison-table.md:14-21 - Agent expects concepts array]
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestExtractComparisonConcepts:
    """Task 4.2-4.4: Unit tests for _extract_comparison_concepts() method."""

    @pytest.fixture
    def agent_service(self):
        """Create AgentService instance for testing."""
        from app.services.agent_service import AgentService
        return AgentService()

    # ============================================================
    # AC 3 / Task 4.2: Extract concepts from Markdown table
    # ============================================================

    def test_extract_comparison_concepts_from_table(self, agent_service):
        """
        Task 4.2: Test extraction from Markdown table headers.

        Given: Content with a table like | 概念A | 概念B | 概念C |
        When: _extract_comparison_concepts() is called
        Then: Return ["概念A", "概念B", "概念C"]

        [Source: Story 12.E.1 - Task 4.2]
        """
        content = """# 对比分析

| TCP | UDP | SCTP |
|-----|-----|------|
| 可靠传输 | 不可靠传输 | 可靠传输 |
| 面向连接 | 无连接 | 面向连接 |
"""
        topic = "传输协议"
        concepts = agent_service._extract_comparison_concepts(content, topic)

        # Should extract TCP, UDP, SCTP from table header
        assert len(concepts) >= 2, f"Expected at least 2 concepts, got {concepts}"
        assert "TCP" in concepts
        assert "UDP" in concepts

    def test_extract_comparison_concepts_from_table_with_dimension_column(self, agent_service):
        """
        Test extraction skips '对比维度' column header.

        Given: Table with first column as dimension label
        When: _extract_comparison_concepts() is called
        Then: Skip dimension column, return concept columns only

        [Source: Story 12.E.1 - Dev Notes: skip 对比维度/维度/比较 etc.]
        """
        content = """| 对比维度 | 数组 | 链表 |
|----------|------|------|
| 访问时间 | O(1) | O(n) |
| 插入时间 | O(n) | O(1) |
"""
        topic = "数据结构"
        concepts = agent_service._extract_comparison_concepts(content, topic)

        # Should skip "对比维度", extract ["数组", "链表"]
        assert "对比维度" not in concepts
        assert "数组" in concepts
        assert "链表" in concepts

    # ============================================================
    # AC 3 / Task 4.3: Extract concepts from Markdown list
    # ============================================================

    def test_extract_comparison_concepts_from_list(self, agent_service):
        """
        Task 4.3: Test extraction from Markdown bullet list.

        Given: Content with bullet list like - 概念A
        When: _extract_comparison_concepts() is called
        Then: Return concepts from list items

        [Source: Story 12.E.1 - Task 4.3]
        """
        content = """# 比较以下概念

- 函数式编程
- 面向对象编程
- 过程式编程

请生成一个对比表。
"""
        topic = "编程范式"
        concepts = agent_service._extract_comparison_concepts(content, topic)

        assert len(concepts) >= 2
        assert "函数式编程" in concepts
        assert "面向对象编程" in concepts

    def test_extract_comparison_concepts_from_asterisk_list(self, agent_service):
        """
        Test extraction from asterisk-style list (* item).

        [Source: Story 12.E.1 - Dev Notes: r'^[\\-\\*]\\s+(.+)' regex]
        """
        content = """比较：
* React
* Vue
* Angular
"""
        topic = "前端框架"
        concepts = agent_service._extract_comparison_concepts(content, topic)

        assert len(concepts) >= 2
        assert "React" in concepts
        assert "Vue" in concepts

    # ============================================================
    # AC 3 / Task 4.3 (extended): Extract from ## headings
    # ============================================================

    def test_extract_comparison_concepts_from_headings(self, agent_service):
        """
        Test extraction from ## headings when table/list not found.

        Given: Content with ## Heading1, ## Heading2
        When: _extract_comparison_concepts() is called
        Then: Return concepts from headings

        [Source: Story 12.E.1 - Dev Notes: Strategy 3]
        """
        content = """# 对比分析

## Python
Python 是一种解释型语言。

## Java
Java 是一种编译型语言。

## Go
Go 是一种静态类型语言。
"""
        topic = "编程语言"
        concepts = agent_service._extract_comparison_concepts(content, topic)

        assert len(concepts) >= 2
        assert "Python" in concepts
        assert "Java" in concepts

    # ============================================================
    # AC 3 / Task 4.4: Fallback logic
    # ============================================================

    def test_extract_comparison_concepts_fallback(self, agent_service):
        """
        Task 4.4: Test fallback when no concepts can be extracted.

        Given: Content without tables, lists, or headings
        When: _extract_comparison_concepts() is called
        Then: Return [topic] as single-element array

        [Source: Story 12.E.1 - Task 4.4]
        """
        content = "这是一段普通文本，没有明显的概念结构。"
        topic = "某个主题"
        concepts = agent_service._extract_comparison_concepts(content, topic)

        # Fallback should return [topic]
        assert len(concepts) >= 1
        assert concepts[0] == topic or concepts[0] == "某个主题"

    def test_extract_comparison_concepts_empty_content(self, agent_service):
        """
        Test fallback with empty content.

        [Source: Story 12.E.1 - edge case handling]
        """
        content = ""
        topic = "默认主题"
        concepts = agent_service._extract_comparison_concepts(content, topic)

        assert len(concepts) >= 1
        # Should fallback to topic
        assert "默认主题" in concepts or "Unknown" in concepts

    def test_extract_comparison_concepts_none_topic_fallback(self, agent_service):
        """
        Test fallback when both content and topic are problematic.

        [Source: Story 12.E.1 - edge case: fallback to ["Unknown"]]
        """
        content = "短文本"
        topic = ""
        concepts = agent_service._extract_comparison_concepts(content, topic)

        # Should have at least 1 element
        assert len(concepts) >= 1

    # ============================================================
    # AC 4: Smart topic extraction preserved
    # ============================================================

    def test_extract_comparison_concepts_deduplication(self, agent_service):
        """
        Test that duplicate concepts are removed.

        [Source: Story 12.E.1 - Dev Notes: 去重逻辑]
        """
        content = """- TCP
- UDP
- TCP
- QUIC
"""
        topic = "协议"
        concepts = agent_service._extract_comparison_concepts(content, topic)

        # Should deduplicate
        assert concepts.count("TCP") == 1


class TestCallExplanationComparisonFormat:
    """
    Task 4.5: Integration tests for call_explanation() JSON format.
    AC 1: comparison-table receives concepts array
    AC 2: Other agents receive concept string (backward compatibility)
    """

    @pytest.fixture
    def mock_agent_service(self):
        """Create mocked AgentService for JSON inspection."""
        from app.services.agent_service import AgentService
        service = AgentService()
        return service

    @pytest.mark.asyncio
    async def test_comparison_table_receives_concepts_array(self, mock_agent_service):
        """
        Task 4.5 (AC 1): Test comparison-table Agent receives concepts array.

        Given: call_explanation(content, explanation_type="comparison")
        When: JSON prompt is constructed
        Then: JSON contains "concepts" array, not "concept" string

        [Source: Story 12.E.1 - AC #1]
        [Source: .claude/agents/comparison-table.md:14-21]
        """
        content = """比较以下概念:
| TCP | UDP |
|-----|-----|
| 可靠 | 快速 |
"""
        # Capture the JSON prompt sent to call_agent
        captured_json = {}

        async def mock_call_agent(agent_type, prompt, context=None):
            captured_json['prompt'] = prompt
            captured_json['type'] = str(agent_type)
            return MagicMock(content="mock response", success=True)

        with patch.object(mock_agent_service, 'call_agent', side_effect=mock_call_agent):
            await mock_agent_service.call_explanation(
                content=content,
                explanation_type="comparison",
                context=None,
                user_understanding="用户理解"
            )

        # Verify JSON format
        json_prompt = json.loads(captured_json['prompt'])
        assert "concepts" in json_prompt, "comparison-table should receive 'concepts' array"
        assert isinstance(json_prompt["concepts"], list), "concepts should be a list"
        assert len(json_prompt["concepts"]) >= 1
        # Should NOT have "concept" key
        assert "concept" not in json_prompt, "comparison-table should NOT have 'concept' string"

    @pytest.mark.asyncio
    async def test_oral_agent_receives_concept_string(self, mock_agent_service):
        """
        Task 4.5 (AC 2): Test oral Agent still receives concept string.

        Given: call_explanation(content, explanation_type="oral")
        When: JSON prompt is constructed
        Then: JSON contains "concept" string (backward compatibility)

        [Source: Story 12.E.1 - AC #2 backward compatibility]
        """
        content = "逆否命题的定义..."
        captured_json = {}

        async def mock_call_agent(agent_type, prompt, context=None):
            captured_json['prompt'] = prompt
            return MagicMock(content="mock response", success=True)

        with patch.object(mock_agent_service, 'call_agent', side_effect=mock_call_agent):
            await mock_agent_service.call_explanation(
                content=content,
                explanation_type="oral",  # Not comparison
                context=None
            )

        json_prompt = json.loads(captured_json['prompt'])
        # oral agent should use 'concept' string
        assert "concept" in json_prompt, "oral agent should receive 'concept' string"
        assert isinstance(json_prompt["concept"], str)
        # Should NOT have "concepts" array
        assert "concepts" not in json_prompt

    @pytest.mark.asyncio
    async def test_clarification_agent_receives_concept_string(self, mock_agent_service):
        """
        Test clarification Agent backward compatibility.

        [Source: Story 12.E.1 - AC #2]
        """
        content = "测试内容"
        captured_json = {}

        async def mock_call_agent(agent_type, prompt, context=None):
            captured_json['prompt'] = prompt
            return MagicMock(content="mock response", success=True)

        with patch.object(mock_agent_service, 'call_agent', side_effect=mock_call_agent):
            await mock_agent_service.call_explanation(
                content=content,
                explanation_type="clarification",
                context=None
            )

        json_prompt = json.loads(captured_json['prompt'])
        assert "concept" in json_prompt
        assert "concepts" not in json_prompt

    @pytest.mark.asyncio
    async def test_memory_agent_receives_concept_string(self, mock_agent_service):
        """
        Test memory Agent backward compatibility.

        [Source: Story 12.E.1 - AC #2]
        """
        content = "测试内容"
        captured_json = {}

        async def mock_call_agent(agent_type, prompt, context=None):
            captured_json['prompt'] = prompt
            return MagicMock(content="mock response", success=True)

        with patch.object(mock_agent_service, 'call_agent', side_effect=mock_call_agent):
            await mock_agent_service.call_explanation(
                content=content,
                explanation_type="memory",
                context=None
            )

        json_prompt = json.loads(captured_json['prompt'])
        assert "concept" in json_prompt
        assert "concepts" not in json_prompt

    @pytest.mark.asyncio
    async def test_four_level_agent_receives_concept_string(self, mock_agent_service):
        """
        Test four_level Agent backward compatibility.

        [Source: Story 12.E.1 - AC #2]
        """
        content = "测试内容"
        captured_json = {}

        async def mock_call_agent(agent_type, prompt, context=None):
            captured_json['prompt'] = prompt
            return MagicMock(content="mock response", success=True)

        with patch.object(mock_agent_service, 'call_agent', side_effect=mock_call_agent):
            await mock_agent_service.call_explanation(
                content=content,
                explanation_type="four_level",
                context=None
            )

        json_prompt = json.loads(captured_json['prompt'])
        assert "concept" in json_prompt
        assert "concepts" not in json_prompt

    @pytest.mark.asyncio
    async def test_example_agent_receives_concept_string(self, mock_agent_service):
        """
        Test example Agent backward compatibility.

        [Source: Story 12.E.1 - AC #2]
        """
        content = "测试内容"
        captured_json = {}

        async def mock_call_agent(agent_type, prompt, context=None):
            captured_json['prompt'] = prompt
            return MagicMock(content="mock response", success=True)

        with patch.object(mock_agent_service, 'call_agent', side_effect=mock_call_agent):
            await mock_agent_service.call_explanation(
                content=content,
                explanation_type="example",
                context=None
            )

        json_prompt = json.loads(captured_json['prompt'])
        assert "concept" in json_prompt
        assert "concepts" not in json_prompt
