"""
PDF Extractor for Canvas Learning System (Story 6.5)

Provides structured PDF content extraction including:
- TOC (Table of Contents) extraction
- Chapter-based text chunking
- Embedded image extraction with Base64 encoding
- Async processing with progress callbacks

Dependencies:
- PyMuPDF (fitz): PDF processing library

Verified from Story 6.5 (AC 6.5.1-6.5.4):
- AC 6.5.1: 自动识别目录(TOC)，提取章节标题和页码
- AC 6.5.2: 按目录结构分块，每块包含标题和内容
- AC 6.5.3: 自动识别嵌入图片，提取并Base64编码
- AC 6.5.4: 单页处理≤5秒，支持大文件分页处理
"""

import asyncio
import base64
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


@dataclass
class PDFImage:
    """Extracted image from PDF."""

    index: int
    page_num: int
    base64_data: str
    extension: str
    width: int = 0
    height: int = 0
    xref: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "index": self.index,
            "page_num": self.page_num,
            "base64": self.base64_data,
            "ext": self.extension,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class TOCEntry:
    """Table of Contents entry."""

    title: str
    page: int
    level: int

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "page": self.page,
            "level": self.level,
        }


@dataclass
class PDFChunk:
    """PDF text chunk with associated metadata."""

    page_num: int
    heading: Optional[str]
    level: int
    content: str
    images: list[PDFImage] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "page_num": self.page_num,
            "heading": self.heading,
            "level": self.level,
            "content": self.content,
            "images": [img.to_dict() for img in self.images],
        }


@dataclass
class PDFStructure:
    """Complete structured PDF content."""

    id: str
    file_path: str
    file_name: str
    title: str
    author: str
    page_count: int
    toc: list[TOCEntry] = field(default_factory=list)
    chunks: list[PDFChunk] = field(default_factory=list)
    total_images: int = 0
    total_text_length: int = 0
    processing_time_ms: int = 0
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "title": self.title,
            "author": self.author,
            "page_count": self.page_count,
            "toc": [entry.to_dict() for entry in self.toc],
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "total_images": self.total_images,
            "total_text_length": self.total_text_length,
            "processing_time_ms": self.processing_time_ms,
            "extracted_at": self.extracted_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PDFStructure":
        """Create from dictionary."""
        toc = [TOCEntry(**entry) for entry in data.get("toc", [])]
        chunks = []
        for chunk_data in data.get("chunks", []):
            images = [PDFImage(**img) for img in chunk_data.get("images", [])]
            chunk_data["images"] = images
            chunks.append(PDFChunk(**chunk_data))

        return cls(
            id=data["id"],
            file_path=data["file_path"],
            file_name=data["file_name"],
            title=data["title"],
            author=data["author"],
            page_count=data["page_count"],
            toc=toc,
            chunks=chunks,
            total_images=data.get("total_images", 0),
            total_text_length=data.get("total_text_length", 0),
            processing_time_ms=data.get("processing_time_ms", 0),
            extracted_at=data.get("extracted_at", ""),
        )

    def get_text_by_page(self, page_num: int) -> str:
        """Get text content for a specific page."""
        for chunk in self.chunks:
            if chunk.page_num == page_num:
                return chunk.content
        return ""

    def get_images_by_page(self, page_num: int) -> list[PDFImage]:
        """Get images for a specific page."""
        for chunk in self.chunks:
            if chunk.page_num == page_num:
                return chunk.images
        return []

    def get_chapter_content(self, chapter_title: str) -> list[PDFChunk]:
        """Get all chunks belonging to a chapter."""
        result = []
        in_chapter = False
        chapter_level = 0

        for chunk in self.chunks:
            if chunk.heading == chapter_title:
                in_chapter = True
                chapter_level = chunk.level
                result.append(chunk)
            elif in_chapter:
                if chunk.heading and chunk.level <= chapter_level:
                    break
                result.append(chunk)

        return result


class PDFExtractorError(Exception):
    """Base exception for PDF extraction errors."""
    pass


class PDFNotFoundError(PDFExtractorError):
    """Raised when PDF file not found."""
    pass


class PDFExtractionError(PDFExtractorError):
    """Raised when extraction fails."""
    pass


class PDFExtractor:
    """
    PDF Structured Extractor for Canvas Learning System.

    Features:
    - TOC extraction with multi-level support
    - Chapter-based text chunking
    - Embedded image extraction with Base64 encoding
    - Async processing with progress callbacks
    - Performance optimization (<5s/page)

    Usage:
        extractor = PDFExtractor()
        structure = await extractor.extract_structured("/path/to/document.pdf")
    """

    # Configuration
    MAX_IMAGE_SIZE_MB: float = 10.0
    MIN_IMAGE_SIZE: int = 100  # Skip images smaller than 100 bytes

    def __init__(
        self,
        extract_images: bool = True,
        max_image_size_mb: float = None,
        preserve_formatting: bool = True
    ):
        """
        Initialize PDF Extractor.

        Args:
            extract_images: Whether to extract embedded images
            max_image_size_mb: Maximum image size to extract (MB)
            preserve_formatting: Whether to preserve text formatting
        """
        if fitz is None:
            raise ImportError(
                "PyMuPDF is required for PDF extraction. "
                "Install with: pip install PyMuPDF"
            )

        self.extract_images = extract_images
        self.max_image_size_mb = max_image_size_mb or self.MAX_IMAGE_SIZE_MB
        self.preserve_formatting = preserve_formatting

    async def extract_structured(
        self,
        pdf_path: str | Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> PDFStructure:
        """
        Extract structured content from PDF.

        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback(current_page, total_pages)

        Returns:
            PDFStructure with TOC, chunks, and images

        Raises:
            PDFNotFoundError: If file not found
            PDFExtractionError: If extraction fails
        """
        import time
        start_time = time.time()

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise PDFNotFoundError(f"PDF not found: {pdf_path}")

        # Generate unique ID
        pdf_id = self._generate_id(pdf_path)

        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            raise PDFExtractionError(f"Cannot open PDF: {e}")

        try:
            # Extract metadata
            metadata = doc.metadata or {}
            page_count = len(doc)

            # Extract TOC (AC 6.5.1)
            toc = self._extract_toc(doc)

            # Extract chunks with text and images (AC 6.5.2, 6.5.3)
            chunks = []
            total_images = 0
            total_text_length = 0

            for page_num in range(page_count):
                if progress_callback:
                    progress_callback(page_num + 1, page_count)

                page = doc[page_num]

                # Extract text
                text = self._extract_page_text(page)
                total_text_length += len(text)

                # Extract images (AC 6.5.3)
                images = []
                if self.extract_images:
                    images = self._extract_page_images(doc, page, page_num)
                    total_images += len(images)

                # Find heading for this page
                heading, level = self._find_heading(toc, page_num + 1)

                chunks.append(PDFChunk(
                    page_num=page_num + 1,
                    heading=heading,
                    level=level,
                    content=text,
                    images=images
                ))

                # Yield control for async (AC 6.5.4 - performance)
                if page_num % 10 == 0:
                    await asyncio.sleep(0)

            processing_time = int((time.time() - start_time) * 1000)

            return PDFStructure(
                id=pdf_id,
                file_path=str(pdf_path.absolute()),
                file_name=pdf_path.name,
                title=metadata.get("title", "") or pdf_path.stem,
                author=metadata.get("author", "") or "",
                page_count=page_count,
                toc=toc,
                chunks=chunks,
                total_images=total_images,
                total_text_length=total_text_length,
                processing_time_ms=processing_time,
            )

        finally:
            doc.close()

    def _extract_toc(self, doc: "fitz.Document") -> list[TOCEntry]:
        """
        Extract Table of Contents from PDF.

        AC 6.5.1: 自动识别目录(TOC)，提取章节标题和页码，支持多级目录结构

        Args:
            doc: PyMuPDF document

        Returns:
            List of TOCEntry objects
        """
        toc_data = doc.get_toc()
        return [
            TOCEntry(
                title=item[1],
                page=item[2],
                level=item[0]
            )
            for item in toc_data
        ]

    def _extract_page_text(self, page: "fitz.Page") -> str:
        """
        Extract text from a single page.

        AC 6.5.2: 按目录结构分块，每块包含标题和内容，保留段落格式

        Args:
            page: PyMuPDF page

        Returns:
            Extracted text content
        """
        if self.preserve_formatting:
            # Use "text" option for better formatting
            return page.get_text("text")
        else:
            # Use "blocks" for plain text
            blocks = page.get_text("blocks")
            texts = []
            for block in blocks:
                # Block format: (x0, y0, x1, y1, "text", block_no, block_type)
                # block_type 0 = text, 1 = image
                if isinstance(block, (list, tuple)) and len(block) >= 7:
                    if block[6] == 0:  # text block
                        texts.append(str(block[4]))
                elif isinstance(block, str):
                    texts.append(block)
            return "\n".join(texts)

    def _extract_page_images(
        self,
        doc: "fitz.Document",
        page: "fitz.Page",
        page_num: int
    ) -> list[PDFImage]:
        """
        Extract images from a single page.

        AC 6.5.3: 自动识别嵌入图片，提取图片并Base64编码，关联图片所在页码

        Args:
            doc: PyMuPDF document
            page: PyMuPDF page
            page_num: Page number (0-indexed)

        Returns:
            List of PDFImage objects
        """
        images = []

        try:
            image_list = page.get_images(full=True)
        except Exception:
            return images

        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]

                # Extract image data
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                image_data = base_image.get("image")
                if not image_data:
                    continue

                # Skip tiny images
                if len(image_data) < self.MIN_IMAGE_SIZE:
                    continue

                # Skip large images
                if len(image_data) > self.max_image_size_mb * 1024 * 1024:
                    continue

                images.append(PDFImage(
                    index=img_index,
                    page_num=page_num + 1,
                    base64_data=base64.b64encode(image_data).decode("utf-8"),
                    extension=base_image.get("ext", "png"),
                    width=base_image.get("width", 0),
                    height=base_image.get("height", 0),
                    xref=xref,
                ))

            except Exception:
                # Skip problematic images
                continue

        return images

    def _find_heading(
        self,
        toc: list[TOCEntry],
        page_num: int
    ) -> tuple[Optional[str], int]:
        """
        Find the current chapter heading for a page.

        Args:
            toc: Table of Contents entries
            page_num: Page number (1-indexed)

        Returns:
            Tuple of (heading_title, heading_level)
        """
        current_heading = None
        current_level = 0

        for entry in toc:
            if entry.page <= page_num:
                current_heading = entry.title
                current_level = entry.level
            else:
                break

        return current_heading, current_level

    def _generate_id(self, pdf_path: Path) -> str:
        """Generate unique ID for PDF."""
        stat = pdf_path.stat()
        unique_str = f"{pdf_path.absolute()}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    async def extract_text_only(
        self,
        pdf_path: str | Path,
        page_range: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Extract text only (faster, no images).

        Args:
            pdf_path: Path to PDF file
            page_range: Optional page range (e.g., "1-10", "1,3,5")
            progress_callback: Optional callback(current, total)

        Returns:
            Combined text from all pages
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise PDFNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))

        try:
            page_count = len(doc)
            pages_to_extract = self._parse_page_range(page_range, page_count)

            texts = []
            for i, page_num in enumerate(pages_to_extract):
                if progress_callback:
                    progress_callback(i + 1, len(pages_to_extract))

                page = doc[page_num - 1]  # 0-indexed
                texts.append(self._extract_page_text(page))

                # Yield control
                if i % 10 == 0:
                    await asyncio.sleep(0)

            return "\n\n".join(texts)

        finally:
            doc.close()

    def _parse_page_range(
        self,
        range_str: Optional[str],
        total_pages: int
    ) -> list[int]:
        """Parse page range string into list of page numbers."""
        if not range_str:
            return list(range(1, total_pages + 1))

        pages = set()
        parts = range_str.replace(" ", "").split(",")

        for part in parts:
            if "-" in part:
                start, end = map(int, part.split("-"))
                pages.update(range(start, min(end + 1, total_pages + 1)))
            else:
                page = int(part)
                if 1 <= page <= total_pages:
                    pages.add(page)

        return sorted(list(pages))

    async def get_toc(self, pdf_path: str | Path) -> list[TOCEntry]:
        """
        Extract only TOC from PDF (fast).

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of TOCEntry objects
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise PDFNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        try:
            return self._extract_toc(doc)
        finally:
            doc.close()

    async def get_page_images(
        self,
        pdf_path: str | Path,
        page_num: int
    ) -> list[PDFImage]:
        """
        Extract images from a specific page.

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)

        Returns:
            List of PDFImage objects
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise PDFNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        try:
            if page_num < 1 or page_num > len(doc):
                raise PDFExtractionError(
                    f"Page {page_num} out of range (1-{len(doc)})"
                )

            page = doc[page_num - 1]
            return self._extract_page_images(doc, page, page_num - 1)
        finally:
            doc.close()


# Convenience function
async def extract_pdf_structure(
    pdf_path: str | Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    **kwargs
) -> PDFStructure:
    """
    Extract structured content from PDF.

    Args:
        pdf_path: Path to PDF file
        progress_callback: Optional callback(current, total)
        **kwargs: Additional arguments for PDFExtractor

    Returns:
        PDFStructure with TOC, chunks, and images
    """
    extractor = PDFExtractor(**kwargs)
    return await extractor.extract_structured(pdf_path, progress_callback)
