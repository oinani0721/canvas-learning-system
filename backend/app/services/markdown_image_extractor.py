"""
Markdown Image Extractor Service

Story: 12.E.4 - Markdown 图片引用提取器
Epic: 12.E - Agent 质量综合修复

Purpose: Extract image references from Markdown content (Obsidian and standard syntax)
and resolve relative paths to absolute paths for multimodal AI processing.

Author: Dev Agent (James)
Created: 2025-12-16
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ImageReference:
    """Markdown 图片引用数据类

    Story 12.E.4 - AC 4.1-4.4

    Attributes:
        path: 图片路径 (原始提取的路径)
        alt_text: 替代文本 / caption
        format: "obsidian" | "markdown" - 标识语法类型
        original_syntax: 原始语法字符串 (用于调试)
    """
    path: str
    alt_text: str = ""
    format: str = ""  # "obsidian" | "markdown"
    original_syntax: str = ""


class MarkdownImageExtractor:
    """从 Markdown 内容中提取图片引用

    Story 12.E.4 - Markdown 图片引用提取器

    Supported syntaxes:
    - Obsidian: ![[image.png]] or ![[image.png|caption]]
    - Markdown: ![alt](path)

    Features:
    - Skip URL images (http://, https://, data:)
    - Resolve relative paths to absolute paths
    - Support vault-relative and canvas-relative paths

    Example:
        >>> extractor = MarkdownImageExtractor()
        >>> content = "Look at this: ![[formula.png]]"
        >>> refs = extractor.extract_all(content)
        >>> print(refs[0].path)
        'formula.png'

    ADR Reference:
        ✅ Verified from ADR-011: pathlib 标准化
    """

    # ✅ Verified from Story 12.E.4 Technical Details
    # Obsidian: ![[path]] or ![[path|caption]]
    # - Group 1: path (required)
    # - Group 2: caption after | (optional)
    OBSIDIAN_PATTERN = re.compile(r'!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]')

    # ✅ Verified from Story 12.E.4 Technical Details
    # Markdown: ![alt](path)
    # - Group 1: alt text (can be empty)
    # - Group 2: path (required)
    MARKDOWN_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    # Supported image extensions for validation (optional filtering)
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}

    def extract_all(self, content: str) -> List[ImageReference]:
        """提取所有图片引用 (AC 4.1, 4.2, 4.3)

        Args:
            content: Markdown 文本内容

        Returns:
            ImageReference 列表，按出现顺序排列

        Example:
            >>> extractor = MarkdownImageExtractor()
            >>> content = '''
            ... # Math Notes
            ... ![[formula.png]]
            ... ![graph](./images/graph.png)
            ... '''
            >>> refs = extractor.extract_all(content)
            >>> len(refs)
            2
        """
        if not content:
            return []

        refs: List[ImageReference] = []

        # ✅ AC 4.1: Extract Obsidian format ![[path]] or ![[path|caption]]
        for match in self.OBSIDIAN_PATTERN.finditer(content):
            path = match.group(1).strip()
            caption = match.group(2).strip() if match.group(2) else ""

            # ✅ AC 4.3: Skip URL images
            if self._is_url(path):
                continue

            refs.append(ImageReference(
                path=path,
                alt_text=caption,
                format="obsidian",
                original_syntax=match.group(0)
            ))

        # ✅ AC 4.2: Extract Markdown format ![alt](path)
        for match in self.MARKDOWN_PATTERN.finditer(content):
            alt_text = match.group(1).strip()
            path = match.group(2).strip()

            # ✅ AC 4.3: Skip URL images
            if self._is_url(path):
                continue

            refs.append(ImageReference(
                path=path,
                alt_text=alt_text,
                format="markdown",
                original_syntax=match.group(0)
            ))

        return refs

    def _is_url(self, path: str) -> bool:
        """检查是否为 URL 图片 (AC 4.3)

        Args:
            path: 图片路径字符串

        Returns:
            True if path is a URL, False otherwise

        Example:
            >>> extractor = MarkdownImageExtractor()
            >>> extractor._is_url("https://example.com/img.png")
            True
            >>> extractor._is_url("./local.png")
            False
        """
        return path.startswith(('http://', 'https://', 'data:'))

    async def resolve_paths(
        self,
        refs: List[ImageReference],
        vault_path: Path,
        canvas_dir: Optional[Path] = None
    ) -> List[Dict]:
        """解析相对路径为绝对路径 (AC 4.4)

        ✅ Verified from ADR-011: pathlib 标准化

        Args:
            refs: 图片引用列表
            vault_path: Obsidian vault 根目录
            canvas_dir: Canvas 文件所在目录 (用于 ./ 相对路径)

        Returns:
            包含绝对路径和存在性的字典列表:
            [
                {
                    "reference": ImageReference,
                    "absolute_path": str | None,
                    "exists": bool
                },
                ...
            ]

        Example:
            >>> extractor = MarkdownImageExtractor()
            >>> refs = [ImageReference(path="images/formula.png")]
            >>> vault_path = Path("/path/to/vault")
            >>> resolved = await extractor.resolve_paths(refs, vault_path)
        """
        resolved: List[Dict] = []

        for ref in refs:
            result: Dict = {
                "reference": ref,
                "absolute_path": None,
                "exists": False
            }

            # Build candidate paths to check
            # ✅ Verified from ADR-011: Use pathlib for path operations
            candidates: List[Path] = []

            # 1. Relative to vault root (Obsidian default)
            candidates.append(vault_path / ref.path)

            # 2. Relative to canvas file directory (for ./ and ../ paths)
            if canvas_dir:
                if ref.path.startswith(('./', '../')):
                    # Explicit relative path
                    candidates.append(canvas_dir / ref.path)
                else:
                    # Also try canvas directory for non-prefixed paths
                    candidates.append(canvas_dir / ref.path)

            # Check each candidate path
            for candidate in candidates:
                try:
                    # ✅ Verified from ADR-011: Use resolve() for path normalization
                    resolved_path = candidate.resolve()

                    if resolved_path.exists() and resolved_path.is_file():
                        result["absolute_path"] = str(resolved_path)
                        result["exists"] = True
                        break
                except (OSError, ValueError):
                    # Skip invalid paths (e.g., permission denied, invalid characters)
                    continue

            resolved.append(result)

        return resolved

    def extract_obsidian(self, content: str) -> List[ImageReference]:
        """仅提取 Obsidian 格式图片引用

        Convenience method for extracting only Obsidian syntax images.

        Args:
            content: Markdown content

        Returns:
            List of ImageReference with format="obsidian"
        """
        if not content:
            return []

        refs: List[ImageReference] = []

        for match in self.OBSIDIAN_PATTERN.finditer(content):
            path = match.group(1).strip()
            caption = match.group(2).strip() if match.group(2) else ""

            if self._is_url(path):
                continue

            refs.append(ImageReference(
                path=path,
                alt_text=caption,
                format="obsidian",
                original_syntax=match.group(0)
            ))

        return refs

    def extract_markdown(self, content: str) -> List[ImageReference]:
        """仅提取 Markdown 格式图片引用

        Convenience method for extracting only standard Markdown syntax images.

        Args:
            content: Markdown content

        Returns:
            List of ImageReference with format="markdown"
        """
        if not content:
            return []

        refs: List[ImageReference] = []

        for match in self.MARKDOWN_PATTERN.finditer(content):
            alt_text = match.group(1).strip()
            path = match.group(2).strip()

            if self._is_url(path):
                continue

            refs.append(ImageReference(
                path=path,
                alt_text=alt_text,
                format="markdown",
                original_syntax=match.group(0)
            ))

        return refs

    def filter_by_extension(
        self,
        refs: List[ImageReference],
        extensions: Optional[set] = None
    ) -> List[ImageReference]:
        """按文件扩展名过滤图片引用

        Args:
            refs: 图片引用列表
            extensions: 允许的扩展名集合 (默认使用 SUPPORTED_EXTENSIONS)

        Returns:
            过滤后的图片引用列表
        """
        if extensions is None:
            extensions = self.SUPPORTED_EXTENSIONS

        filtered: List[ImageReference] = []

        for ref in refs:
            # ✅ Verified from ADR-011: Use pathlib for extension extraction
            path = Path(ref.path)
            if path.suffix.lower() in extensions:
                filtered.append(ref)

        return filtered
