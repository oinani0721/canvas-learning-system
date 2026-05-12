"""Story 2.2+2.9 T2 (2026-05-11) — wikilink_parser 单元测试.

覆盖 AC #3 4 精度 + 嵌套 alias deny + heading 段落抽取.

测试范围:
- parse_wikilink: file / heading / block / alias / heading+alias 组合
- parse_wikilink: 嵌套 alias deny / 空 target deny / 空 anchor deny
- extract_heading_section: 提取 ## section 到下一同级
- extract_all_wikilinks: 段落多 wikilink 抽取
"""

from __future__ import annotations

import pytest

from app.services.wikilink_parser import (
    ParsedWikilink,
    extract_all_wikilinks,
    extract_heading_section,
    parse_wikilink,
)


class TestParseWikilinkFile:
    """[[X]] 文件精度."""

    def test_simple_file(self):
        result = parse_wikilink("[[Eigenvalues]]")
        assert result.is_valid is True
        assert result.target == "Eigenvalues"
        assert result.heading is None
        assert result.block_id is None
        assert result.alias is None

    def test_chinese_target(self):
        result = parse_wikilink("[[特征值]]")
        assert result.is_valid is True
        assert result.target == "特征值"

    def test_spaces_in_target(self):
        result = parse_wikilink("[[CS 61B]]")
        assert result.is_valid is True
        assert result.target == "CS 61B"


class TestParseWikilinkHeading:
    """[[X#Heading]] heading 精度."""

    def test_simple_heading(self):
        result = parse_wikilink("[[X#Definition]]")
        assert result.is_valid is True
        assert result.target == "X"
        assert result.heading == "Definition"
        assert result.block_id is None

    def test_heading_with_spaces(self):
        result = parse_wikilink("[[X#Hub Penalty]]")
        assert result.is_valid is True
        assert result.heading == "Hub Penalty"

    def test_chinese_heading(self):
        result = parse_wikilink("[[X#定义]]")
        assert result.is_valid is True
        assert result.heading == "定义"


class TestParseWikilinkBlock:
    """[[X#^block_id]] block 精度."""

    def test_simple_block(self):
        result = parse_wikilink("[[X#^abc123]]")
        assert result.is_valid is True
        assert result.target == "X"
        assert result.block_id == "abc123"
        assert result.heading is None

    def test_block_distinguished_from_heading(self):
        """`#^id` 是 block_id, `#Heading` 是 heading — 不混淆."""
        block = parse_wikilink("[[X#^xyz]]")
        heading = parse_wikilink("[[X#xyz]]")
        assert block.block_id == "xyz"
        assert block.heading is None
        assert heading.heading == "xyz"
        assert heading.block_id is None


class TestParseWikilinkAlias:
    """[[X|Alias]] alias 精度."""

    def test_simple_alias(self):
        result = parse_wikilink("[[Eigenvalues|特征值]]")
        assert result.is_valid is True
        assert result.target == "Eigenvalues"
        assert result.alias == "特征值"
        assert result.heading is None

    def test_heading_and_alias(self):
        """[[X#h|y]] 组合: target + heading + alias 全提取."""
        result = parse_wikilink("[[X#Definition|定义部分]]")
        assert result.is_valid is True
        assert result.target == "X"
        assert result.heading == "Definition"
        assert result.alias == "定义部分"


class TestParseWikilinkDeny:
    """无效 wikilink 必须标 is_valid=False + 给 reason."""

    def test_nested_alias_deny(self):
        """[[X|Y|Z]] 是无效 Obsidian 语法."""
        result = parse_wikilink("[[X|Y|Z]]")
        assert result.is_valid is False
        assert result.invalid_reason == "nested_alias"

    def test_empty_target_deny(self):
        result = parse_wikilink("[[]]")
        assert result.is_valid is False
        assert result.invalid_reason == "empty_target"

    def test_empty_anchor_deny(self):
        """[[X#]] 空 anchor."""
        result = parse_wikilink("[[X#]]")
        assert result.is_valid is False
        assert result.invalid_reason == "empty_anchor"

    def test_empty_alias_deny(self):
        """[[X|]] 空 alias."""
        result = parse_wikilink("[[X|]]")
        assert result.is_valid is False
        assert result.invalid_reason == "empty_alias"

    def test_empty_block_id_deny(self):
        """[[X#^]] 空 block_id."""
        result = parse_wikilink("[[X#^]]")
        assert result.is_valid is False
        assert result.invalid_reason == "empty_block_id"

    def test_not_wikilink_format(self):
        """普通文本不是 wikilink."""
        result = parse_wikilink("just text")
        assert result.is_valid is False
        assert result.invalid_reason == "not_wikilink_format"


class TestExtractHeadingSection:
    """heading 段落抽取."""

    def test_simple_section(self):
        content = "## A\nbody A\n## B\nbody B\n"
        result = extract_heading_section(content, "A")
        assert result is not None
        assert "## A" in result
        assert "body A" in result
        assert "body B" not in result, "B 段不应被包含"
        assert "## B" not in result

    def test_subsection_included(self):
        """## A 应包含其下的 ### sub（更深级别），到下一 ## 才结束."""
        content = "## A\n### A1\nsub body\n## B\nbody B\n"
        result = extract_heading_section(content, "A")
        assert result is not None
        assert "### A1" in result
        assert "sub body" in result
        assert "body B" not in result

    def test_heading_not_found(self):
        content = "## A\nbody"
        result = extract_heading_section(content, "NotExist")
        assert result is None

    def test_crlf_line_endings(self):
        """兼容 Windows CRLF (Phase 1.7 同问题)."""
        content = "## A\r\nbody\r\n## B\r\nB body"
        result = extract_heading_section(content, "A")
        assert result is not None
        assert "body" in result

    def test_until_end_of_file(self):
        """最后一个 heading 段提取到文件末尾."""
        content = "## A\nbody A\n## B\nbody B"
        result = extract_heading_section(content, "B")
        assert result is not None
        assert "body B" in result


class TestExtractAllWikilinks:
    """从段落抽多个 wikilink."""

    def test_extract_multiple(self):
        text = "see [[X]] and [[Y#h|alias]] also [[Z#^id]]"
        results = extract_all_wikilinks(text)
        assert len(results) == 3
        targets = [r.target for r in results]
        assert targets == ["X", "Y", "Z"]

    def test_extract_with_invalid(self):
        """无效 wikilink 也返回（is_valid=False）便于审计."""
        text = "valid [[X]] but [[A|B|C]] invalid"
        results = extract_all_wikilinks(text)
        assert len(results) == 2
        assert results[0].is_valid is True
        assert results[1].is_valid is False
        assert results[1].invalid_reason == "nested_alias"

    def test_empty_text(self):
        assert extract_all_wikilinks("") == []
        assert extract_all_wikilinks("no wikilinks here") == []
