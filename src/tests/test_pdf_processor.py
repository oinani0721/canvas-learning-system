"""
Test suite for PDFProcessor (Story 6.2)

Tests cover:
- AC 6.2.1: Canvas节点可附加PDF文件
- AC 6.2.2: 显示PDF首页缩略图
- AC 6.2.3: 支持指定页码范围
- AC 6.2.4: PDF元数据存储到Neo4j
"""

import base64
import tempfile
from pathlib import Path

import pytest

# Skip all tests if PyMuPDF not installed
pytest.importorskip("fitz", reason="PyMuPDF required for PDF tests")

from src.agentic_rag.processors.pdf_processor import (
    PageRangeError,
    PDFCorruptError,
    PDFMetadata,
    PDFProcessor,
    PDFProcessorError,
    PDFSizeError,
    PDFValidationError,
    process_pdf,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def processor():
    """Create PDFProcessor instance."""
    return PDFProcessor()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_pdf(temp_dir):
    """Create a minimal valid PDF file."""
    import fitz

    pdf_path = temp_dir / "test_document.pdf"
    doc = fitz.open()

    # Add 3 pages
    for i in range(3):
        page = doc.new_page(width=612, height=792)  # Letter size
        text_point = fitz.Point(72, 72)
        page.insert_text(text_point, f"Page {i + 1} content", fontsize=12)

    # Set metadata
    doc.set_metadata({
        "title": "Test Document",
        "author": "Test Author",
        "subject": "Testing",
        "keywords": "test, pdf, canvas",
    })

    doc.save(str(pdf_path))
    doc.close()

    return pdf_path


@pytest.fixture
def large_pdf(temp_dir):
    """Create a PDF that exceeds size limit."""
    pdf_path = temp_dir / "large_document.pdf"

    # Create file larger than 50MB by writing dummy content
    with open(pdf_path, "wb") as f:
        # Write PDF header
        f.write(b"%PDF-1.4\n")
        # Write enough data to exceed 50MB
        chunk = b"0" * (1024 * 1024)  # 1MB chunk
        for _ in range(51):
            f.write(chunk)

    return pdf_path


@pytest.fixture
def invalid_file(temp_dir):
    """Create an invalid (non-PDF) file."""
    invalid_path = temp_dir / "not_a_pdf.pdf"
    with open(invalid_path, "wb") as f:
        f.write(b"This is not a PDF file")
    return invalid_path


@pytest.fixture
def text_file(temp_dir):
    """Create a text file with .txt extension."""
    text_path = temp_dir / "document.txt"
    with open(text_path, "w") as f:
        f.write("This is a text file")
    return text_path


# ============================================================
# AC 6.2.1: Canvas节点可附加PDF文件
# ============================================================


class TestPDFValidation:
    """Tests for PDF format validation (AC 6.2.1)."""

    @pytest.mark.asyncio
    async def test_valid_pdf_accepted(self, processor, sample_pdf):
        """Test that valid PDF files are accepted."""
        metadata = await processor.process(sample_pdf)

        assert metadata is not None
        assert metadata.file_name == "test_document.pdf"
        assert metadata.page_count == 3
        assert metadata.mime_type == "application/pdf"

    @pytest.mark.asyncio
    async def test_pdf_extension_required(self, processor, text_file):
        """Test that non-PDF extensions are rejected."""
        with pytest.raises(PDFValidationError) as exc_info:
            await processor.process(text_file)

        assert "Unsupported format" in str(exc_info.value)
        assert ".txt" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_pdf_content_rejected(self, processor, invalid_file):
        """Test that files with invalid PDF content are rejected."""
        with pytest.raises(PDFValidationError) as exc_info:
            await processor.process(invalid_file)

        assert "Invalid PDF file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, processor, temp_dir):
        """Test error when file doesn't exist."""
        nonexistent = temp_dir / "nonexistent.pdf"

        with pytest.raises(PDFValidationError) as exc_info:
            await processor.process(nonexistent)

        assert "File not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_file_size_limit_enforced(self, processor, large_pdf):
        """Test that files exceeding 50MB are rejected."""
        with pytest.raises(PDFSizeError) as exc_info:
            await processor.process(large_pdf)

        assert "File too large" in str(exc_info.value)
        assert "50MB" in str(exc_info.value)

    def test_custom_size_limit(self, temp_dir):
        """Test custom max size configuration."""
        processor = PDFProcessor(max_size_mb=10)
        assert processor.max_size_mb == 10


# ============================================================
# AC 6.2.2: 显示PDF首页缩略图
# ============================================================


class TestPDFThumbnail:
    """Tests for PDF thumbnail generation (AC 6.2.2)."""

    @pytest.mark.asyncio
    async def test_thumbnail_generated_by_default(self, processor, sample_pdf):
        """Test thumbnail is generated by default."""
        metadata = await processor.process(sample_pdf)

        assert metadata.thumbnail_base64 is not None
        assert len(metadata.thumbnail_base64) > 0

        # Verify it's valid base64
        decoded = base64.b64decode(metadata.thumbnail_base64)
        assert len(decoded) > 0

    @pytest.mark.asyncio
    async def test_thumbnail_is_valid_png(self, processor, sample_pdf):
        """Test thumbnail is valid PNG image."""
        metadata = await processor.process(sample_pdf)

        decoded = base64.b64decode(metadata.thumbnail_base64)

        # PNG magic bytes
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n'

    @pytest.mark.asyncio
    async def test_thumbnail_size_constraint(self, processor, sample_pdf):
        """Test thumbnail respects 150x200 size limit."""
        import io

        from PIL import Image

        metadata = await processor.process(sample_pdf)
        decoded = base64.b64decode(metadata.thumbnail_base64)

        img = Image.open(io.BytesIO(decoded))

        # Should fit within 150x200
        assert img.width <= 150
        assert img.height <= 200

    @pytest.mark.asyncio
    async def test_thumbnail_generation_can_be_disabled(self, processor, sample_pdf):
        """Test thumbnail generation can be disabled."""
        metadata = await processor.process(sample_pdf, generate_thumbnail=False)

        assert metadata.thumbnail_base64 is None

    @pytest.mark.asyncio
    async def test_thumbnail_saved_to_cache(self, temp_dir, sample_pdf):
        """Test thumbnail can be saved to cache directory."""
        cache_dir = temp_dir / "cache"
        processor = PDFProcessor(cache_dir=str(cache_dir))

        metadata = await processor.process(
            sample_pdf,
            generate_thumbnail=True,
            save_thumbnail=True
        )

        assert metadata.thumbnail_path is not None
        assert Path(metadata.thumbnail_path).exists()

    def test_custom_thumbnail_size(self, temp_dir):
        """Test custom thumbnail size configuration."""
        processor = PDFProcessor(thumbnail_size=(200, 300))
        assert processor.thumbnail_size == (200, 300)

    @pytest.mark.asyncio
    async def test_generate_thumbnail_directly(self, processor, sample_pdf):
        """Test generate_thumbnail method directly."""
        thumbnail_b64 = await processor.generate_thumbnail(sample_pdf)

        assert thumbnail_b64 is not None
        decoded = base64.b64decode(thumbnail_b64)
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n'


# ============================================================
# AC 6.2.3: 支持指定页码范围
# ============================================================


class TestPageRangeParsing:
    """Tests for page range parsing (AC 6.2.3)."""

    def test_single_page(self, processor):
        """Test parsing single page number."""
        pages = processor.parse_page_range("5", 10)
        assert pages == [5]

    def test_page_range(self, processor):
        """Test parsing page range format."""
        pages = processor.parse_page_range("1-5", 10)
        assert pages == [1, 2, 3, 4, 5]

    def test_mixed_format(self, processor):
        """Test parsing mixed format: '1,3,5-8'."""
        pages = processor.parse_page_range("1,3,5-8", 10)
        assert pages == [1, 3, 5, 6, 7, 8]

    def test_all_pages_when_empty(self, processor):
        """Test empty range returns all pages."""
        pages = processor.parse_page_range("", 5)
        assert pages == [1, 2, 3, 4, 5]

    def test_all_pages_when_none(self, processor):
        """Test None returns all pages."""
        pages = processor.parse_page_range(None, 3)
        assert pages == [1, 2, 3]

    def test_spaces_ignored(self, processor):
        """Test spaces in range are ignored."""
        pages = processor.parse_page_range("1, 3, 5 - 7", 10)
        assert pages == [1, 3, 5, 6, 7]

    def test_duplicate_pages_removed(self, processor):
        """Test duplicate pages are removed."""
        pages = processor.parse_page_range("1,1,2,2-4", 10)
        assert pages == [1, 2, 3, 4]

    def test_invalid_range_format(self, processor):
        """Test invalid range format raises error."""
        with pytest.raises(PageRangeError):
            processor.parse_page_range("1--5", 10)

    def test_start_greater_than_end(self, processor):
        """Test start > end raises error."""
        with pytest.raises(PageRangeError) as exc_info:
            processor.parse_page_range("10-5", 15)

        assert "start > end" in str(exc_info.value)

    def test_page_out_of_bounds(self, processor):
        """Test page out of bounds raises error."""
        with pytest.raises(PageRangeError) as exc_info:
            processor.parse_page_range("15", 10)

        assert "out of bounds" in str(exc_info.value)

    def test_range_out_of_bounds(self, processor):
        """Test range out of bounds raises error."""
        with pytest.raises(PageRangeError) as exc_info:
            processor.parse_page_range("5-15", 10)

        assert "out of bounds" in str(exc_info.value)

    def test_invalid_page_number(self, processor):
        """Test invalid page number format."""
        with pytest.raises(PageRangeError):
            processor.parse_page_range("abc", 10)

    def test_zero_page_rejected(self, processor):
        """Test page 0 is rejected (1-indexed)."""
        with pytest.raises(PageRangeError):
            processor.parse_page_range("0", 10)

    @pytest.mark.asyncio
    async def test_page_range_in_process(self, processor, sample_pdf):
        """Test page range is stored in metadata."""
        metadata = await processor.process(sample_pdf, page_range="1-2")

        assert metadata.page_range == "1-2"
        assert metadata.selected_pages == [1, 2]


# ============================================================
# AC 6.2.4: PDF元数据存储到Neo4j
# ============================================================


class TestPDFMetadataExtraction:
    """Tests for PDF metadata extraction (AC 6.2.4)."""

    @pytest.mark.asyncio
    async def test_title_extracted(self, processor, sample_pdf):
        """Test PDF title is extracted."""
        metadata = await processor.process(sample_pdf)
        assert metadata.title == "Test Document"

    @pytest.mark.asyncio
    async def test_author_extracted(self, processor, sample_pdf):
        """Test PDF author is extracted."""
        metadata = await processor.process(sample_pdf)
        assert metadata.author == "Test Author"

    @pytest.mark.asyncio
    async def test_page_count_extracted(self, processor, sample_pdf):
        """Test page count is extracted."""
        metadata = await processor.process(sample_pdf)
        assert metadata.page_count == 3

    @pytest.mark.asyncio
    async def test_file_path_stored(self, processor, sample_pdf):
        """Test file path is stored."""
        metadata = await processor.process(sample_pdf)

        assert metadata.file_path is not None
        assert "test_document.pdf" in metadata.file_path

    @pytest.mark.asyncio
    async def test_file_size_stored(self, processor, sample_pdf):
        """Test file size is stored."""
        metadata = await processor.process(sample_pdf)

        assert metadata.file_size > 0
        assert metadata.file_size == sample_pdf.stat().st_size

    @pytest.mark.asyncio
    async def test_unique_id_generated(self, processor, sample_pdf):
        """Test unique ID is generated."""
        metadata = await processor.process(sample_pdf)

        assert metadata.id is not None
        assert len(metadata.id) == 16  # SHA256 truncated

    @pytest.mark.asyncio
    async def test_processed_at_timestamp(self, processor, sample_pdf):
        """Test processed_at timestamp is set."""
        metadata = await processor.process(sample_pdf)

        assert metadata.processed_at is not None
        # Should be ISO format
        from datetime import datetime
        datetime.fromisoformat(metadata.processed_at)

    def test_extract_metadata_method(self, processor, sample_pdf):
        """Test extract_metadata method directly."""
        metadata = processor.extract_metadata(sample_pdf)

        assert metadata["title"] == "Test Document"
        assert metadata["author"] == "Test Author"
        assert metadata["page_count"] == 3


# ============================================================
# PDFMetadata Serialization
# ============================================================


class TestPDFMetadataSerialization:
    """Tests for PDFMetadata to_dict and from_dict."""

    def test_to_dict(self):
        """Test PDFMetadata serialization."""
        metadata = PDFMetadata(
            id="test123",
            file_path="/path/to/test.pdf",
            file_name="test.pdf",
            file_size=1024,
            title="Test",
            page_count=5,
        )

        data = metadata.to_dict()

        assert data["id"] == "test123"
        assert data["file_path"] == "/path/to/test.pdf"
        assert data["page_count"] == 5

    def test_from_dict(self):
        """Test PDFMetadata deserialization."""
        data = {
            "id": "test456",
            "file_path": "/path/to/doc.pdf",
            "file_name": "doc.pdf",
            "file_size": 2048,
            "title": "Document",
            "page_count": 10,
        }

        metadata = PDFMetadata.from_dict(data)

        assert metadata.id == "test456"
        assert metadata.title == "Document"
        assert metadata.page_count == 10

    def test_roundtrip(self):
        """Test serialization roundtrip."""
        original = PDFMetadata(
            id="roundtrip",
            file_path="/test.pdf",
            file_name="test.pdf",
            file_size=512,
            title="Roundtrip Test",
            author="Tester",
            page_count=3,
            page_range="1-2",
            selected_pages=[1, 2],
        )

        restored = PDFMetadata.from_dict(original.to_dict())

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.page_range == original.page_range
        assert restored.selected_pages == original.selected_pages


# ============================================================
# Convenience Function
# ============================================================


class TestProcessPdfFunction:
    """Tests for process_pdf convenience function."""

    @pytest.mark.asyncio
    async def test_process_pdf_function(self, sample_pdf):
        """Test process_pdf convenience function."""
        metadata = await process_pdf(sample_pdf)

        assert metadata is not None
        assert metadata.page_count == 3

    @pytest.mark.asyncio
    async def test_process_pdf_with_page_range(self, sample_pdf):
        """Test process_pdf with page range."""
        metadata = await process_pdf(sample_pdf, page_range="1-2")

        assert metadata.selected_pages == [1, 2]


# ============================================================
# Error Handling
# ============================================================


class TestPDFErrorHandling:
    """Tests for error handling scenarios."""

    def test_error_hierarchy(self):
        """Test exception class hierarchy."""
        assert issubclass(PDFValidationError, PDFProcessorError)
        assert issubclass(PDFSizeError, PDFProcessorError)
        assert issubclass(PDFCorruptError, PDFProcessorError)
        assert issubclass(PageRangeError, PDFProcessorError)

    @pytest.mark.asyncio
    async def test_corrupt_pdf_error(self, processor, temp_dir):
        """Test handling of corrupt PDF."""
        corrupt_pdf = temp_dir / "corrupt.pdf"
        with open(corrupt_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n")  # Valid header but no content

        with pytest.raises((PDFCorruptError, PDFProcessorError)):
            await processor.process(corrupt_pdf)


# ============================================================
# Integration Tests
# ============================================================


class TestPDFIntegration:
    """Integration tests for PDF processing."""

    @pytest.mark.asyncio
    async def test_full_processing_workflow(self, temp_dir):
        """Test complete PDF processing workflow."""
        import fitz

        # Create PDF with multiple pages and metadata
        pdf_path = temp_dir / "integration_test.pdf"
        doc = fitz.open()

        for i in range(5):
            page = doc.new_page()
            page.insert_text((72, 72), f"Integration Test Page {i + 1}")

        doc.set_metadata({
            "title": "Integration Test",
            "author": "Test Suite",
        })
        doc.save(str(pdf_path))
        doc.close()

        # Process with cache
        cache_dir = temp_dir / "cache"
        processor = PDFProcessor(cache_dir=str(cache_dir))

        metadata = await processor.process(
            pdf_path,
            page_range="1-3",
            generate_thumbnail=True,
            save_thumbnail=True
        )

        # Verify all aspects
        assert metadata.title == "Integration Test"
        assert metadata.author == "Test Suite"
        assert metadata.page_count == 5
        assert metadata.selected_pages == [1, 2, 3]
        assert metadata.thumbnail_base64 is not None
        assert metadata.thumbnail_path is not None
        assert Path(metadata.thumbnail_path).exists()

        # Verify serialization
        data = metadata.to_dict()
        restored = PDFMetadata.from_dict(data)
        assert restored.title == metadata.title


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
