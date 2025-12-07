"""
Tests for PDFExtractor (Story 6.5)

Verifies:
- AC 6.5.1: TOC extraction
- AC 6.5.2: Chapter-based text chunking
- AC 6.5.3: Image extraction
- AC 6.5.4: Performance requirements
"""

import asyncio
import base64
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_rag.processors.pdf_extractor import (
    PDFChunk,
    PDFExtractionError,
    PDFExtractor,
    PDFExtractorError,
    PDFImage,
    PDFNotFoundError,
    PDFStructure,
    TOCEntry,
    extract_pdf_structure,
)

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_fitz():
    """Mock PyMuPDF (fitz) module."""
    with patch("agentic_rag.processors.pdf_extractor.fitz") as mock:
        # Setup mock document
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=5)
        mock_doc.__iter__ = MagicMock(return_value=iter([MagicMock() for _ in range(5)]))
        mock_doc.metadata = {
            "title": "Test Document",
            "author": "Test Author",
        }
        mock_doc.get_toc.return_value = [
            [1, "Chapter 1", 1],
            [2, "Section 1.1", 2],
            [1, "Chapter 2", 3],
        ]

        # Setup mock pages
        mock_pages = []
        for i in range(5):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Page {i+1} content"
            mock_page.get_images.return_value = []
            mock_pages.append(mock_page)

        mock_doc.__getitem__ = MagicMock(side_effect=lambda x: mock_pages[x])

        mock.open.return_value = mock_doc
        yield mock


@pytest.fixture
def mock_fitz_with_images():
    """Mock fitz with image extraction."""
    with patch("agentic_rag.processors.pdf_extractor.fitz") as mock:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=3)
        mock_doc.metadata = {"title": "Test", "author": ""}
        mock_doc.get_toc.return_value = []

        # Create test image data (must be > MIN_IMAGE_SIZE=100 bytes)
        test_image_data = b"fake_image_data_" + b"x" * 200

        mock_doc.extract_image.return_value = {
            "image": test_image_data,
            "ext": "png",
            "width": 100,
            "height": 100,
        }

        mock_pages = []
        for i in range(3):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Page {i+1}"
            # First page has 2 images, second has 1, third has none
            # Format: (xref, smask, width, height, bpc, colorspace, alt. colorspace, name, filter, referencer)
            if i == 0:
                mock_page.get_images.return_value = [
                    (1, 0, 100, 100, 8, "DeviceRGB", "", "img1", "DCTDecode", 0),
                    (2, 0, 50, 50, 8, "DeviceRGB", "", "img2", "DCTDecode", 0),
                ]
            elif i == 1:
                mock_page.get_images.return_value = [
                    (3, 0, 200, 200, 8, "DeviceRGB", "", "img3", "DCTDecode", 0),
                ]
            else:
                mock_page.get_images.return_value = []
            mock_pages.append(mock_page)

        mock_doc.__getitem__ = MagicMock(side_effect=lambda x: mock_pages[x])
        mock.open.return_value = mock_doc
        yield mock


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a temporary PDF path (file may not exist)."""
    return tmp_path / "test_document.pdf"


@pytest.fixture
def existing_pdf_path(tmp_path):
    """Create an existing (fake) PDF file."""
    pdf_path = tmp_path / "existing.pdf"
    # Write minimal PDF header for validation
    pdf_path.write_bytes(b"%PDF-1.4\nfake content")
    return pdf_path


# =============================================================================
# Test Data Classes
# =============================================================================

class TestTOCEntry:
    """Tests for TOCEntry dataclass."""

    def test_create_toc_entry(self):
        """Test TOCEntry creation."""
        entry = TOCEntry(title="Chapter 1", page=1, level=1)
        assert entry.title == "Chapter 1"
        assert entry.page == 1
        assert entry.level == 1

    def test_to_dict(self):
        """Test TOCEntry to_dict conversion."""
        entry = TOCEntry(title="Section 1.1", page=5, level=2)
        result = entry.to_dict()
        assert result == {"title": "Section 1.1", "page": 5, "level": 2}


class TestPDFImage:
    """Tests for PDFImage dataclass."""

    def test_create_pdf_image(self):
        """Test PDFImage creation."""
        img = PDFImage(
            index=0,
            page_num=1,
            base64_data="abc123",
            extension="png",
            width=100,
            height=200,
        )
        assert img.index == 0
        assert img.page_num == 1
        assert img.extension == "png"

    def test_to_dict(self):
        """Test PDFImage to_dict conversion."""
        img = PDFImage(
            index=1,
            page_num=2,
            base64_data="xyz789",
            extension="jpg",
            width=50,
            height=75,
        )
        result = img.to_dict()
        assert result["index"] == 1
        assert result["page_num"] == 2
        assert result["base64"] == "xyz789"
        assert result["ext"] == "jpg"


class TestPDFChunk:
    """Tests for PDFChunk dataclass."""

    def test_create_chunk(self):
        """Test PDFChunk creation."""
        chunk = PDFChunk(
            page_num=1,
            heading="Introduction",
            level=1,
            content="This is the introduction.",
        )
        assert chunk.page_num == 1
        assert chunk.heading == "Introduction"
        assert chunk.level == 1
        assert chunk.content == "This is the introduction."
        assert chunk.images == []

    def test_chunk_with_images(self):
        """Test PDFChunk with images."""
        img = PDFImage(0, 1, "base64data", "png")
        chunk = PDFChunk(
            page_num=1,
            heading="Chapter 1",
            level=1,
            content="Content",
            images=[img],
        )
        assert len(chunk.images) == 1
        assert chunk.images[0].extension == "png"

    def test_to_dict(self):
        """Test PDFChunk to_dict conversion."""
        chunk = PDFChunk(
            page_num=2,
            heading="Section 1",
            level=2,
            content="Section content",
        )
        result = chunk.to_dict()
        assert result["page_num"] == 2
        assert result["heading"] == "Section 1"
        assert result["images"] == []


class TestPDFStructure:
    """Tests for PDFStructure dataclass."""

    def test_create_structure(self):
        """Test PDFStructure creation."""
        structure = PDFStructure(
            id="abc123",
            file_path="/test/doc.pdf",
            file_name="doc.pdf",
            title="Test Document",
            author="Author",
            page_count=10,
        )
        assert structure.id == "abc123"
        assert structure.page_count == 10
        assert structure.toc == []
        assert structure.chunks == []

    def test_to_dict(self):
        """Test PDFStructure to_dict conversion."""
        structure = PDFStructure(
            id="xyz789",
            file_path="/path/to/doc.pdf",
            file_name="doc.pdf",
            title="My Document",
            author="Me",
            page_count=5,
            total_images=3,
            total_text_length=1000,
        )
        result = structure.to_dict()
        assert result["id"] == "xyz789"
        assert result["title"] == "My Document"
        assert result["total_images"] == 3

    def test_from_dict(self):
        """Test PDFStructure from_dict creation."""
        data = {
            "id": "test123",
            "file_path": "/test.pdf",
            "file_name": "test.pdf",
            "title": "Test",
            "author": "Author",
            "page_count": 3,
            "toc": [{"title": "Ch1", "page": 1, "level": 1}],
            "chunks": [
                {
                    "page_num": 1,
                    "heading": "Ch1",
                    "level": 1,
                    "content": "Content",
                    "images": [],
                }
            ],
            "total_images": 0,
            "total_text_length": 100,
            "processing_time_ms": 500,
            "extracted_at": "2024-01-01T00:00:00",
        }
        structure = PDFStructure.from_dict(data)
        assert structure.id == "test123"
        assert len(structure.toc) == 1
        assert len(structure.chunks) == 1

    def test_get_text_by_page(self):
        """Test get_text_by_page method."""
        structure = PDFStructure(
            id="test",
            file_path="/test.pdf",
            file_name="test.pdf",
            title="Test",
            author="",
            page_count=2,
            chunks=[
                PDFChunk(1, "Ch1", 1, "Page 1 text"),
                PDFChunk(2, "Ch1", 1, "Page 2 text"),
            ],
        )
        assert structure.get_text_by_page(1) == "Page 1 text"
        assert structure.get_text_by_page(2) == "Page 2 text"
        assert structure.get_text_by_page(3) == ""

    def test_get_images_by_page(self):
        """Test get_images_by_page method."""
        img1 = PDFImage(0, 1, "data1", "png")
        img2 = PDFImage(1, 1, "data2", "jpg")
        structure = PDFStructure(
            id="test",
            file_path="/test.pdf",
            file_name="test.pdf",
            title="Test",
            author="",
            page_count=2,
            chunks=[
                PDFChunk(1, None, 0, "Text", images=[img1, img2]),
                PDFChunk(2, None, 0, "Text2", images=[]),
            ],
        )
        images = structure.get_images_by_page(1)
        assert len(images) == 2
        assert structure.get_images_by_page(2) == []

    def test_get_chapter_content(self):
        """Test get_chapter_content method."""
        structure = PDFStructure(
            id="test",
            file_path="/test.pdf",
            file_name="test.pdf",
            title="Test",
            author="",
            page_count=4,
            chunks=[
                PDFChunk(1, "Chapter 1", 1, "Ch1 intro"),
                PDFChunk(2, "Chapter 1", 1, "Ch1 content"),
                PDFChunk(3, "Chapter 2", 1, "Ch2 intro"),
                PDFChunk(4, "Chapter 2", 1, "Ch2 content"),
            ],
        )
        ch1_content = structure.get_chapter_content("Chapter 1")
        assert len(ch1_content) == 2
        assert ch1_content[0].content == "Ch1 intro"


# =============================================================================
# Test PDFExtractor
# =============================================================================

class TestPDFExtractor:
    """Tests for PDFExtractor class."""

    def test_init_default(self):
        """Test default initialization."""
        extractor = PDFExtractor()
        assert extractor.extract_images is True
        assert extractor.preserve_formatting is True

    def test_init_custom(self):
        """Test custom initialization."""
        extractor = PDFExtractor(
            extract_images=False,
            max_image_size_mb=5.0,
            preserve_formatting=False,
        )
        assert extractor.extract_images is False
        assert extractor.max_image_size_mb == 5.0
        assert extractor.preserve_formatting is False

    def test_init_without_fitz(self):
        """Test initialization without PyMuPDF."""
        with patch("agentic_rag.processors.pdf_extractor.fitz", None):
            with pytest.raises(ImportError, match="PyMuPDF"):
                PDFExtractor()


class TestPDFExtractorExtraction:
    """Tests for PDFExtractor extraction methods."""

    @pytest.mark.asyncio
    async def test_extract_structured_file_not_found(self):
        """Test extraction with non-existent file."""
        extractor = PDFExtractor()
        with pytest.raises(PDFNotFoundError):
            await extractor.extract_structured("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_extract_structured_basic(self, existing_pdf_path, mock_fitz):
        """Test basic structured extraction."""
        extractor = PDFExtractor()
        result = await extractor.extract_structured(existing_pdf_path)

        assert isinstance(result, PDFStructure)
        assert result.title == "Test Document"
        assert result.author == "Test Author"
        assert result.page_count == 5
        assert len(result.toc) == 3
        assert len(result.chunks) == 5

    @pytest.mark.asyncio
    async def test_extract_structured_with_progress(self, existing_pdf_path, mock_fitz):
        """Test extraction with progress callback."""
        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        extractor = PDFExtractor()
        await extractor.extract_structured(existing_pdf_path, progress_callback)

        assert len(progress_calls) == 5
        assert progress_calls[0] == (1, 5)
        assert progress_calls[-1] == (5, 5)

    @pytest.mark.asyncio
    async def test_extract_with_images(self, existing_pdf_path, mock_fitz_with_images):
        """Test extraction with images (AC 6.5.3)."""
        extractor = PDFExtractor()
        result = await extractor.extract_structured(existing_pdf_path)

        assert result.total_images == 3
        assert len(result.chunks[0].images) == 2
        assert len(result.chunks[1].images) == 1
        assert len(result.chunks[2].images) == 0

    @pytest.mark.asyncio
    async def test_extract_without_images(self, existing_pdf_path, mock_fitz):
        """Test extraction with images disabled."""
        extractor = PDFExtractor(extract_images=False)
        result = await extractor.extract_structured(existing_pdf_path)

        assert result.total_images == 0
        for chunk in result.chunks:
            assert len(chunk.images) == 0


class TestPDFExtractorTOC:
    """Tests for TOC extraction (AC 6.5.1)."""

    @pytest.mark.asyncio
    async def test_get_toc(self, existing_pdf_path, mock_fitz):
        """Test standalone TOC extraction."""
        extractor = PDFExtractor()
        toc = await extractor.get_toc(existing_pdf_path)

        assert len(toc) == 3
        assert toc[0].title == "Chapter 1"
        assert toc[0].level == 1
        assert toc[1].title == "Section 1.1"
        assert toc[1].level == 2

    @pytest.mark.asyncio
    async def test_toc_file_not_found(self):
        """Test TOC extraction with non-existent file."""
        extractor = PDFExtractor()
        with pytest.raises(PDFNotFoundError):
            await extractor.get_toc("/nonexistent.pdf")

    def test_extract_toc_internal(self, mock_fitz):
        """Test internal _extract_toc method."""
        extractor = PDFExtractor()
        mock_doc = mock_fitz.open.return_value
        toc = extractor._extract_toc(mock_doc)

        assert len(toc) == 3
        assert all(isinstance(entry, TOCEntry) for entry in toc)


class TestPDFExtractorImages:
    """Tests for image extraction (AC 6.5.3)."""

    @pytest.mark.asyncio
    async def test_get_page_images(self, existing_pdf_path, mock_fitz_with_images):
        """Test getting images from specific page."""
        extractor = PDFExtractor()
        images = await extractor.get_page_images(existing_pdf_path, 1)

        assert len(images) == 2
        assert all(isinstance(img, PDFImage) for img in images)

    @pytest.mark.asyncio
    async def test_get_page_images_invalid_page(self, existing_pdf_path, mock_fitz_with_images):
        """Test getting images from invalid page."""
        extractor = PDFExtractor()
        with pytest.raises(PDFExtractionError, match="out of range"):
            await extractor.get_page_images(existing_pdf_path, 100)

    @pytest.mark.asyncio
    async def test_image_extraction_with_base64(self, existing_pdf_path, mock_fitz_with_images):
        """Test image Base64 encoding."""
        extractor = PDFExtractor()
        result = await extractor.extract_structured(existing_pdf_path)

        img = result.chunks[0].images[0]
        # Verify base64 is valid
        decoded = base64.b64decode(img.base64_data)
        # Fixture creates: b"fake_image_data_" + b"x" * 200 (>100 bytes MIN_IMAGE_SIZE)
        expected_data = b"fake_image_data_" + b"x" * 200
        assert decoded == expected_data


class TestPDFExtractorTextExtraction:
    """Tests for text extraction (AC 6.5.2)."""

    @pytest.mark.asyncio
    async def test_extract_text_only(self, existing_pdf_path, mock_fitz):
        """Test text-only extraction."""
        extractor = PDFExtractor()
        text = await extractor.extract_text_only(existing_pdf_path)

        assert "Page 1 content" in text
        assert "Page 5 content" in text

    @pytest.mark.asyncio
    async def test_extract_text_with_page_range(self, existing_pdf_path, mock_fitz):
        """Test text extraction with page range."""
        extractor = PDFExtractor()
        text = await extractor.extract_text_only(existing_pdf_path, page_range="1-3")

        assert "Page 1 content" in text
        assert "Page 3 content" in text

    @pytest.mark.asyncio
    async def test_extract_text_with_progress(self, existing_pdf_path, mock_fitz):
        """Test text extraction with progress callback."""
        progress_calls = []

        def callback(current, total):
            progress_calls.append((current, total))

        extractor = PDFExtractor()
        await extractor.extract_text_only(
            existing_pdf_path,
            page_range="1,3,5",
            progress_callback=callback,
        )

        assert len(progress_calls) == 3

    def test_parse_page_range_all(self):
        """Test page range parsing - all pages."""
        extractor = PDFExtractor()
        pages = extractor._parse_page_range(None, 10)
        assert pages == list(range(1, 11))

    def test_parse_page_range_single(self):
        """Test page range parsing - single pages."""
        extractor = PDFExtractor()
        pages = extractor._parse_page_range("1,3,5", 10)
        assert pages == [1, 3, 5]

    def test_parse_page_range_range(self):
        """Test page range parsing - range."""
        extractor = PDFExtractor()
        pages = extractor._parse_page_range("2-5", 10)
        assert pages == [2, 3, 4, 5]

    def test_parse_page_range_mixed(self):
        """Test page range parsing - mixed."""
        extractor = PDFExtractor()
        pages = extractor._parse_page_range("1,3-5,7", 10)
        assert pages == [1, 3, 4, 5, 7]


class TestPDFExtractorHeadingFinding:
    """Tests for heading finding functionality."""

    def test_find_heading_basic(self):
        """Test basic heading finding."""
        extractor = PDFExtractor()
        toc = [
            TOCEntry("Chapter 1", 1, 1),
            TOCEntry("Section 1.1", 3, 2),
            TOCEntry("Chapter 2", 5, 1),
        ]

        heading, level = extractor._find_heading(toc, 1)
        assert heading == "Chapter 1"
        assert level == 1

        heading, level = extractor._find_heading(toc, 3)
        assert heading == "Section 1.1"
        assert level == 2

        heading, level = extractor._find_heading(toc, 4)
        assert heading == "Section 1.1"
        assert level == 2

        heading, level = extractor._find_heading(toc, 5)
        assert heading == "Chapter 2"
        assert level == 1

    def test_find_heading_empty_toc(self):
        """Test heading finding with empty TOC."""
        extractor = PDFExtractor()
        heading, level = extractor._find_heading([], 1)
        assert heading is None
        assert level == 0


class TestPDFExtractorPerformance:
    """Tests for performance requirements (AC 6.5.4)."""

    @pytest.mark.asyncio
    async def test_processing_time_recorded(self, existing_pdf_path, mock_fitz):
        """Test that processing time is recorded."""
        extractor = PDFExtractor()
        result = await extractor.extract_structured(existing_pdf_path)

        # Processing time may be 0 for mocked fast operations
        # Just verify the field exists and is non-negative
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_async_yields_control(self, existing_pdf_path, mock_fitz):
        """Test that async extraction yields control."""
        # This test verifies the async nature works correctly
        extractor = PDFExtractor()

        async def concurrent_task():
            return "completed"

        # Run extraction and another task concurrently
        result, other = await asyncio.gather(
            extractor.extract_structured(existing_pdf_path),
            concurrent_task(),
        )

        assert isinstance(result, PDFStructure)
        assert other == "completed"


class TestConvenienceFunction:
    """Tests for convenience function."""

    @pytest.mark.asyncio
    async def test_extract_pdf_structure(self, existing_pdf_path, mock_fitz):
        """Test extract_pdf_structure convenience function."""
        result = await extract_pdf_structure(existing_pdf_path)

        assert isinstance(result, PDFStructure)
        assert result.page_count == 5

    @pytest.mark.asyncio
    async def test_extract_pdf_structure_with_kwargs(self, existing_pdf_path, mock_fitz):
        """Test convenience function with custom kwargs."""
        # Configure mock for blocks format
        mock_doc = mock_fitz.open.return_value
        for page in [mock_doc.__getitem__(i) for i in range(5)]:
            # Return proper block format: (x0, y0, x1, y1, "text", block_no, block_type)
            page.get_text.side_effect = lambda fmt="text": (
                [(0, 0, 100, 20, "Block text", 0, 0)] if fmt == "blocks" else "Text content"
            )

        result = await extract_pdf_structure(
            existing_pdf_path,
            extract_images=False,
            preserve_formatting=False,
        )

        assert isinstance(result, PDFStructure)


# =============================================================================
# Integration Tests
# =============================================================================

class TestPDFExtractorIntegration:
    """Integration tests for PDFExtractor."""

    @pytest.mark.asyncio
    async def test_full_extraction_workflow(self, existing_pdf_path, mock_fitz):
        """Test complete extraction workflow."""
        extractor = PDFExtractor()

        # Step 1: Get TOC
        toc = await extractor.get_toc(existing_pdf_path)
        assert len(toc) > 0

        # Step 2: Full extraction
        structure = await extractor.extract_structured(existing_pdf_path)
        assert structure.page_count > 0
        assert len(structure.chunks) == structure.page_count

        # Step 3: Verify serialization
        data = structure.to_dict()
        restored = PDFStructure.from_dict(data)
        assert restored.id == structure.id
        assert restored.page_count == structure.page_count

    @pytest.mark.asyncio
    async def test_chapter_navigation(self, existing_pdf_path, mock_fitz):
        """Test chapter-based navigation."""
        extractor = PDFExtractor()
        structure = await extractor.extract_structured(existing_pdf_path)

        # Find chapter content
        ch1_chunks = structure.get_chapter_content("Chapter 1")
        assert len(ch1_chunks) > 0

        # Get text by page
        page1_text = structure.get_text_by_page(1)
        assert page1_text == "Page 1 content"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestPDFExtractorErrors:
    """Tests for error handling."""

    def test_pdf_extractor_error_hierarchy(self):
        """Test exception hierarchy."""
        assert issubclass(PDFNotFoundError, PDFExtractorError)
        assert issubclass(PDFExtractionError, PDFExtractorError)

    @pytest.mark.asyncio
    async def test_handle_corrupt_pdf(self, existing_pdf_path):
        """Test handling of corrupt PDF."""
        with patch("agentic_rag.processors.pdf_extractor.fitz") as mock:
            mock.open.side_effect = Exception("Cannot open PDF")

            extractor = PDFExtractor()
            with pytest.raises(PDFExtractionError, match="Cannot open PDF"):
                await extractor.extract_structured(existing_pdf_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
