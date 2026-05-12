"""Wikilink 4 精度解析器 — Story 2.2+2.9 T2 (2026-05-11).

解析 Obsidian wikilink 文本的 4 种精度:
- file:   ``[[X]]``                → target=X
- heading: ``[[X#Heading]]``       → target=X, heading=Heading (装载只读 heading 段落)
- block:   ``[[X#^block_id]]``     → target=X, block_id=block_id
- alias:   ``[[X|Alias]]``         → target=X, alias=Alias (slug 字段用 alias)

Deny:
- 嵌套 alias ``[[X|Y|Z]]``         → is_valid=False (无效 Obsidian 语法)
- 空 target ``[[]]`` / ``[[ ]]``    → is_valid=False
- 仅 ``#``/``^`` 而无 target        → is_valid=False

本模块为纯函数（无 I/O、无依赖 obsidiantools），单元测试好写。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# 匹配单个 wikilink 内部内容（不含 [[ ]] 包裹）
# 例如对 `[[Eigenvalues#Definition|特征值]]` 提取 inner=`Eigenvalues#Definition|特征值`
# 用 `.*?` 而非 `.+?` 让 `[[]]` 也能命中（之后在 inner.strip() 时识别为 empty_target）
_WIKILINK_INNER_PATTERN = re.compile(r"^\s*\[\[(.*?)\]\]\s*$")

# 匹配 markdown heading 行: `## Heading` 或 `### Sub-Heading`
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class ParsedWikilink:
    """单个 wikilink 解析结果."""

    target: str  # 文件 basename (无 .md, 无 [[ ]])
    heading: Optional[str] = None  # ``#Heading`` 提取（无 #）
    block_id: Optional[str] = None  # ``#^block_id`` 提取（无 #^）
    alias: Optional[str] = None  # ``|Alias`` 提取
    raw: str = ""  # 原始 wikilink 文本（含 [[ ]]）
    is_valid: bool = True
    invalid_reason: Optional[str] = None


def parse_wikilink(text: str) -> ParsedWikilink:
    """解析单个 wikilink 文本（含 ``[[`` ``]]`` 包裹）.

    Args:
        text: 形如 ``[[X]]`` / ``[[X#h]]`` / ``[[X#^id]]`` / ``[[X|Y]]`` 的字符串

    Returns:
        ParsedWikilink. is_valid=False 时 invalid_reason 解释原因.

    Examples:
        >>> parse_wikilink("[[Eigenvalues]]").target
        'Eigenvalues'
        >>> parse_wikilink("[[X#Definition]]").heading
        'Definition'
        >>> parse_wikilink("[[X#^abc123]]").block_id
        'abc123'
        >>> parse_wikilink("[[X|Y]]").alias
        'Y'
        >>> parse_wikilink("[[X|Y|Z]]").is_valid
        False
    """
    raw = text
    match = _WIKILINK_INNER_PATTERN.match(text)
    if not match:
        return ParsedWikilink(
            target="",
            raw=raw,
            is_valid=False,
            invalid_reason="not_wikilink_format",
        )

    inner = match.group(1).strip()
    if not inner:
        return ParsedWikilink(
            target="",
            raw=raw,
            is_valid=False,
            invalid_reason="empty_target",
        )

    # 1. 切 alias: `target#part|alias`
    alias_parts = inner.split("|")
    if len(alias_parts) > 2:
        return ParsedWikilink(
            target="",
            raw=raw,
            is_valid=False,
            invalid_reason="nested_alias",
        )
    target_and_anchor = alias_parts[0].strip()
    alias = alias_parts[1].strip() if len(alias_parts) == 2 else None
    if alias is not None and not alias:
        # `[[X|]]` 视为无效（空 alias）
        return ParsedWikilink(
            target="",
            raw=raw,
            is_valid=False,
            invalid_reason="empty_alias",
        )

    # 2. 切 anchor (heading 或 block_id): `target#anchor`
    anchor_parts = target_and_anchor.split("#", 1)
    target = anchor_parts[0].strip()
    if not target:
        return ParsedWikilink(
            target="",
            raw=raw,
            is_valid=False,
            invalid_reason="empty_target",
        )

    heading: Optional[str] = None
    block_id: Optional[str] = None
    if len(anchor_parts) == 2:
        anchor = anchor_parts[1].strip()
        if not anchor:
            # `[[X#]]` 视为无效（空 anchor）
            return ParsedWikilink(
                target=target,
                alias=alias,
                raw=raw,
                is_valid=False,
                invalid_reason="empty_anchor",
            )
        if anchor.startswith("^"):
            block_id_raw = anchor[1:].strip()
            if not block_id_raw:
                return ParsedWikilink(
                    target=target,
                    alias=alias,
                    raw=raw,
                    is_valid=False,
                    invalid_reason="empty_block_id",
                )
            block_id = block_id_raw
        else:
            heading = anchor

    return ParsedWikilink(
        target=target,
        heading=heading,
        block_id=block_id,
        alias=alias,
        raw=raw,
        is_valid=True,
    )


def extract_heading_section(content: str, heading: str) -> Optional[str]:
    """从 markdown content 提取指定 heading 段落（含 heading 本身到下一个同级或更高级 heading 之前）.

    Args:
        content: 完整 markdown 文本（带 frontmatter 或不带均可，本函数不剥离）
        heading: 目标 heading 文本（无 # 前缀，如 "Definition"）

    Returns:
        段落文本（含 heading 行）；找不到返回 None.

    Behavior:
        - 大小写敏感匹配 heading 文本（与 Obsidian 行为一致）
        - 兼容 CRLF / LF 换行（Phase 1.7 FRONTMATTER_PATTERN 已修同样问题）
        - 提取从匹配的 heading 行开始，到下一个 ``<=`` 同级 heading（或文件末尾）

    Examples:
        >>> content = "## A\\nbody A\\n## B\\nbody B"
        >>> extract_heading_section(content, "A")
        '## A\\nbody A\\n'
    """
    # 规范化换行
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    # 找 heading 行索引 + 级别
    target_idx: Optional[int] = None
    target_level: int = 0
    for idx, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        if title == heading:
            target_idx = idx
            target_level = level
            break

    if target_idx is None:
        return None

    # 找下一个 <= target_level 的 heading（结束位置）
    end_idx: int = len(lines)
    for idx in range(target_idx + 1, len(lines)):
        m = re.match(r"^(#{1,6})\s+", lines[idx])
        if m and len(m.group(1)) <= target_level:
            end_idx = idx
            break

    section_lines = lines[target_idx:end_idx]
    return "\n".join(section_lines) + ("\n" if section_lines else "")


def extract_all_wikilinks(text: str) -> list[ParsedWikilink]:
    """从一段 markdown 文本中提取所有 wikilink（每个都通过 parse_wikilink 解析）.

    Args:
        text: markdown 文本

    Returns:
        解析后的 ParsedWikilink 列表（含 is_valid=False 的，便于审计）.
    """
    # 匹配所有 [[...]] 出现（贪婪但内部无 ]]）
    pattern = re.compile(r"\[\[[^\[\]]+?\]\]")
    return [parse_wikilink(m.group(0)) for m in pattern.finditer(text)]
