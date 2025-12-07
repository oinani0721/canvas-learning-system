"""
PDF Processor for Canvas Learning System (Story 6.2)

Provides PDF processing capabilities including:
- Format validation
- First page thumbnail generation
- Metadata extraction (title, author, page count)
- Page range parsing

Dependencies:
- PyMuPDF (fitz): PDF processing library
- Pillow: Image processing for thumbnails
"""

import base64
import hashlib
import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
except ImportError:
    Image = None


@dataclass
class PDFMetadata:
    """PDF metadata and processing results."""

    id: str
    file_path: str
    file_name: str
    file_size: int
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int = 0
    page_range: Optional[str] = None
    selected_pages: list[int] = field(default_factory=list)
    thumbnail_base64: Optional[str] = None
    thumbnail_path: Optional[str] = None
    mime_type: str = "application/pdf"
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
            "keywords": self.keywords,
            "creator": self.creator,
            "producer": self.producer,
            "creation_date": self.creation_date,
            "modification_date": self.modification_date,
            "page_count": self.page_count,
            "page_range": self.page_range,
            "selected_pages": self.selected_pages,
            "thumbnail_base64": self.thumbnail_base64,
            "thumbnail_path": self.thumbnail_path,
            "mime_type": self.mime_type,
            "processed_at": self.processed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PDFMetadata":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class PDFProcessorError(Exception):
    """Base exception for PDF processing errors."""
    pass


class PDFValidationError(PDFProcessorError):
    """Raised when PDF validation fails."""
    pass


class PDFSizeError(PDFProcessorError):
    """Raised when PDF exceeds size limit."""
    pass


class PDFCorruptError(PDFProcessorError):
    """Raised when PDF is corrupted or unreadable."""
    pass


class PageRangeError(PDFProcessorError):
    """Raised when page range is invalid."""
    pass


class PDFProcessor:
    """
    PDF processing for Canvas Learning System.

    Features:
    - PDF format validation
    - First page thumbnail generation (150x200px)
    - Metadata extraction
    - Page range parsing and validation

    Usage:
        processor = PDFProcessor()
        metadata = await processor.process("/path/to/document.pdf", page_range="1-10")
    """

    # Configuration
    MAX_SIZE_MB: int = 50
    THUMBNAIL_SIZE: tuple[int, int] = (150, 200)
    SUPPORTED_EXTENSIONS: set[str] = {".pdf"}
    THUMBNAIL_QUALITY: int = 85
    THUMBNAIL_FORMAT: str = "PNG"

    def __init__(
        self,
        max_size_mb: int = None,
        thumbnail_size: tuple[int, int] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize PDF processor.

        Args:
            max_size_mb: Maximum allowed PDF size in MB (default: 50)
            thumbnail_size: Thumbnail dimensions (width, height) (default: 150x200)
            cache_dir: Directory to store thumbnails (optional)
        """
        if fitz is None:
            raise ImportError(
                "PyMuPDF is required for PDF processing. "
                "Install with: pip install PyMuPDF"
            )

        self.max_size_mb = max_size_mb or self.MAX_SIZE_MB
        self.thumbnail_size = thumbnail_size or self.THUMBNAIL_SIZE
        self.cache_dir = Path(cache_dir) if cache_dir else None

        if self.cache_dir and not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def process(
        self,
        pdf_path: str | Path,
        page_range: Optional[str] = None,
        generate_thumbnail: bool = True,
        save_thumbnail: bool = False
    ) -> PDFMetadata:
        """
        Process a PDF file and extract metadata.

        Args:
            pdf_path: Path to PDF file
            page_range: Optional page range (e.g., "1-10", "1,3,5-8")
            generate_thumbnail: Whether to generate thumbnail
            save_thumbnail: Whether to save thumbnail to disk

        Returns:
            PDFMetadata with extracted information

        Raises:
            PDFValidationError: If file is not a valid PDF
            PDFSizeError: If file exceeds size limit
            PDFCorruptError: If PDF is corrupted
            PageRangeError: If page range is invalid
        """
        pdf_path = Path(pdf_path)

        # Validate file
        self._validate_file(pdf_path)

        # Generate unique ID
        pdf_id = self._generate_id(pdf_path)

        # Open and extract metadata
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            raise PDFCorruptError(f"Cannot open PDF: {e}")

        try:
            # Extract metadata
            metadata_dict = doc.metadata or {}
            page_count = len(doc)

            # Parse page range
            selected_pages = []
            if page_range:
                selected_pages = self.parse_page_range(page_range, page_count)

            # Generate thumbnail
            thumbnail_b64 = None
            thumbnail_path = None

            if generate_thumbnail and page_count > 0:
                thumbnail_b64 = await self.generate_thumbnail(doc)

                if save_thumbnail and self.cache_dir and thumbnail_b64:
                    thumbnail_path = self._save_thumbnail(pdf_id, thumbnail_b64)

            # Build metadata
            metadata = PDFMetadata(
                id=pdf_id,
                file_path=str(pdf_path.absolute()),
                file_name=pdf_path.name,
                file_size=pdf_path.stat().st_size,
                title=metadata_dict.get("title") or None,
                author=metadata_dict.get("author") or None,
                subject=metadata_dict.get("subject") or None,
                keywords=metadata_dict.get("keywords") or None,
                creator=metadata_dict.get("creator") or None,
                producer=metadata_dict.get("producer") or None,
                creation_date=metadata_dict.get("creationDate") or None,
                modification_date=metadata_dict.get("modDate") or None,
                page_count=page_count,
                page_range=page_range,
                selected_pages=selected_pages,
                thumbnail_base64=thumbnail_b64,
                thumbnail_path=thumbnail_path,
            )

            return metadata

        finally:
            doc.close()

    async def generate_thumbnail(
        self,
        doc_or_path: "fitz.Document | str | Path",
        page_num: int = 0
    ) -> str:
        """
        Generate thumbnail from PDF first page.

        Args:
            doc_or_path: PyMuPDF document or path to PDF
            page_num: Page number for thumbnail (default: 0 = first page)

        Returns:
            Base64-encoded PNG image
        """
        close_doc = False

        if isinstance(doc_or_path, (str, Path)):
            doc = fitz.open(str(doc_or_path))
            close_doc = True
        else:
            doc = doc_or_path

        try:
            if len(doc) == 0:
                raise PDFCorruptError("PDF has no pages")

            page = doc[page_num]

            # Render page to pixmap
            # Calculate zoom to fit thumbnail size while maintaining aspect ratio
            page_rect = page.rect
            width_ratio = self.thumbnail_size[0] / page_rect.width
            height_ratio = self.thumbnail_size[1] / page_rect.height
            zoom = min(width_ratio, height_ratio) * 2  # 2x for better quality

            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to PIL Image
            if Image is None:
                # Fallback: return raw PNG if Pillow not available
                return base64.b64encode(pix.tobytes("png")).decode("utf-8")

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Resize to thumbnail size
            img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format=self.THUMBNAIL_FORMAT, quality=self.THUMBNAIL_QUALITY)
            buffer.seek(0)

            return base64.b64encode(buffer.getvalue()).decode("utf-8")

        finally:
            if close_doc:
                doc.close()

    def parse_page_range(self, range_str: str, total_pages: int) -> list[int]:
        """
        Parse page range string into list of page numbers.

        Supported formats:
        - Single page: "5"
        - Range: "1-10"
        - Mixed: "1,3,5-8,10"
        - All pages: "" or None

        Args:
            range_str: Page range string
            total_pages: Total number of pages in PDF

        Returns:
            List of page numbers (1-indexed)

        Raises:
            PageRangeError: If range is invalid or out of bounds
        """
        if not range_str or not range_str.strip():
            return list(range(1, total_pages + 1))

        pages = set()
        parts = range_str.replace(" ", "").split(",")

        for part in parts:
            if not part:
                continue

            if "-" in part:
                # Range format: "1-10"
                try:
                    match = re.match(r"^(\d+)-(\d+)$", part)
                    if not match:
                        raise PageRangeError(f"Invalid range format: {part}")

                    start, end = int(match.group(1)), int(match.group(2))

                    if start > end:
                        raise PageRangeError(f"Invalid range: start > end ({start} > {end})")

                    if start < 1 or end > total_pages:
                        raise PageRangeError(
                            f"Page range {start}-{end} out of bounds (1-{total_pages})"
                        )

                    pages.update(range(start, end + 1))

                except ValueError as e:
                    raise PageRangeError(f"Invalid range: {part}") from e
            else:
                # Single page: "5"
                try:
                    page_num = int(part)
                    if page_num < 1 or page_num > total_pages:
                        raise PageRangeError(
                            f"Page {page_num} out of bounds (1-{total_pages})"
                        )
                    pages.add(page_num)
                except ValueError as e:
                    raise PageRangeError(f"Invalid page number: {part}") from e

        return sorted(list(pages))

    def extract_metadata(self, pdf_path: str | Path) -> dict:
        """
        Extract metadata from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with metadata fields
        """
        pdf_path = Path(pdf_path)
        self._validate_file(pdf_path)

        doc = fitz.open(str(pdf_path))
        try:
            metadata = doc.metadata or {}
            return {
                "title": metadata.get("title"),
                "author": metadata.get("author"),
                "subject": metadata.get("subject"),
                "keywords": metadata.get("keywords"),
                "creator": metadata.get("creator"),
                "producer": metadata.get("producer"),
                "creation_date": metadata.get("creationDate"),
                "modification_date": metadata.get("modDate"),
                "page_count": len(doc),
                "format": metadata.get("format"),
                "encryption": metadata.get("encryption"),
            }
        finally:
            doc.close()

    def _validate_file(self, pdf_path: Path) -> None:
        """Validate PDF file exists, is accessible, and within size limit."""
        if not pdf_path.exists():
            raise PDFValidationError(f"File not found: {pdf_path}")

        if not pdf_path.is_file():
            raise PDFValidationError(f"Not a file: {pdf_path}")

        if pdf_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise PDFValidationError(
                f"Unsupported format: {pdf_path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Check file size
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_size_mb:
            raise PDFSizeError(
                f"File too large: {file_size_mb:.1f}MB. "
                f"Maximum allowed: {self.max_size_mb}MB"
            )

        # Check if file is readable (basic PDF header check)
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(8)
                if not header.startswith(b"%PDF"):
                    raise PDFValidationError(
                        "Invalid PDF file: missing PDF header"
                    )
        except IOError as e:
            raise PDFValidationError(f"Cannot read file: {e}")

    def _generate_id(self, pdf_path: Path) -> str:
        """Generate unique ID for PDF based on path and size."""
        stat = pdf_path.stat()
        unique_str = f"{pdf_path.absolute()}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def _save_thumbnail(self, pdf_id: str, thumbnail_b64: str) -> str:
        """Save thumbnail to cache directory."""
        if not self.cache_dir:
            return None

        thumbnail_path = self.cache_dir / f"{pdf_id}_thumb.png"

        with open(thumbnail_path, "wb") as f:
            f.write(base64.b64decode(thumbnail_b64))

        return str(thumbnail_path)


# Convenience function for async usage
async def process_pdf(
    pdf_path: str | Path,
    page_range: Optional[str] = None,
    **kwargs
) -> PDFMetadata:
    """
    Process a PDF file and return metadata.

    Args:
        pdf_path: Path to PDF file
        page_range: Optional page range
        **kwargs: Additional arguments passed to PDFProcessor

    Returns:
        PDFMetadata with extracted information
    """
    processor = PDFProcessor(**kwargs)
    return await processor.process(pdf_path, page_range=page_range)
