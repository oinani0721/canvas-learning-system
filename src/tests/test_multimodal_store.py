"""
Tests for Multimodal Content Storage (Story 6.3).

Verified from Story 6.3 acceptance criteria:
- AC 6.3.1: LanceDB table with 768-dim vectors
- AC 6.3.2: Neo4j Schema with Media nodes
- AC 6.3.3: Unified MultimodalContent interface
- AC 6.3.4: File storage path normalization
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from src.agentic_rag.models.multimodal_content import (
    MediaType,
    MultimodalContent,
    MultimodalMetadata,
)
from src.agentic_rag.storage.multimodal_store import MultimodalStore


class TestMediaType:
    """Tests for MediaType enum."""

    def test_media_type_values(self):
        """Test MediaType enum values."""
        assert MediaType.IMAGE.value == "image"
        assert MediaType.PDF.value == "pdf"
        assert MediaType.AUDIO.value == "audio"
        assert MediaType.VIDEO.value == "video"

    def test_from_extension_image(self):
        """Test MediaType detection for images."""
        assert MediaType.from_extension("jpg") == MediaType.IMAGE
        assert MediaType.from_extension(".jpeg") == MediaType.IMAGE
        assert MediaType.from_extension("PNG") == MediaType.IMAGE
        assert MediaType.from_extension(".gif") == MediaType.IMAGE
        assert MediaType.from_extension("webp") == MediaType.IMAGE

    def test_from_extension_pdf(self):
        """Test MediaType detection for PDF."""
        assert MediaType.from_extension("pdf") == MediaType.PDF
        assert MediaType.from_extension(".PDF") == MediaType.PDF

    def test_from_extension_audio(self):
        """Test MediaType detection for audio."""
        assert MediaType.from_extension("mp3") == MediaType.AUDIO
        assert MediaType.from_extension(".wav") == MediaType.AUDIO
        assert MediaType.from_extension("ogg") == MediaType.AUDIO
        assert MediaType.from_extension("m4a") == MediaType.AUDIO

    def test_from_extension_video(self):
        """Test MediaType detection for video."""
        assert MediaType.from_extension("mp4") == MediaType.VIDEO
        assert MediaType.from_extension(".webm") == MediaType.VIDEO
        assert MediaType.from_extension("mkv") == MediaType.VIDEO

    def test_from_extension_unsupported(self):
        """Test MediaType raises for unsupported extension."""
        with pytest.raises(ValueError, match="Unsupported file extension"):
            MediaType.from_extension("xyz")

    def test_get_supported_extensions(self):
        """Test getting supported extensions for each type."""
        image_exts = MediaType.get_supported_extensions(MediaType.IMAGE)
        assert "jpg" in image_exts
        assert "png" in image_exts

        pdf_exts = MediaType.get_supported_extensions(MediaType.PDF)
        assert "pdf" in pdf_exts


class TestMultimodalMetadata:
    """Tests for MultimodalMetadata dataclass."""

    def test_default_metadata(self):
        """Test default metadata values."""
        metadata = MultimodalMetadata()
        assert metadata.file_size is None
        assert metadata.width is None
        assert metadata.height is None

    def test_metadata_with_values(self):
        """Test metadata with specified values."""
        metadata = MultimodalMetadata(
            file_size=12345,
            width=1920,
            height=1080,
            mime_type="image/png",
        )
        assert metadata.file_size == 12345
        assert metadata.width == 1920
        assert metadata.height == 1080

    def test_to_dict(self):
        """Test metadata to dictionary conversion."""
        metadata = MultimodalMetadata(
            file_size=100,
            width=800,
        )
        d = metadata.to_dict()
        assert d["file_size"] == 100
        assert d["width"] == 800
        assert "height" not in d  # None values excluded

    def test_from_dict(self):
        """Test metadata from dictionary."""
        d = {"file_size": 200, "mime_type": "image/jpeg"}
        metadata = MultimodalMetadata.from_dict(d)
        assert metadata.file_size == 200
        assert metadata.mime_type == "image/jpeg"
        assert metadata.width is None


class TestMultimodalContent:
    """Tests for MultimodalContent dataclass."""

    def test_create_content_minimal(self):
        """Test creating content with minimal required fields."""
        content = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            related_concept_id="concept-123",
        )
        assert content.id is not None
        assert content.media_type == MediaType.IMAGE
        assert content.file_path == "/path/to/image.png"
        assert content.related_concept_id == "concept-123"
        assert content.created_at is not None

    def test_create_content_full(self):
        """Test creating content with all fields."""
        vector = [0.1] * 768
        content = MultimodalContent(
            id="custom-id",
            media_type=MediaType.PDF,
            file_path="/path/to/doc.pdf",
            related_concept_id="concept-456",
            thumbnail_path="/path/to/thumb.jpg",
            extracted_text="Sample text",
            description="A sample PDF",
            vector=vector,
            source_location="page 5",
            metadata=MultimodalMetadata(page_count=10),
        )
        assert content.id == "custom-id"
        assert content.thumbnail_path == "/path/to/thumb.jpg"
        assert content.extracted_text == "Sample text"
        assert len(content.vector) == 768
        assert content.metadata.page_count == 10

    def test_media_type_string_conversion(self):
        """Test that string media_type is converted to enum."""
        content = MultimodalContent(
            media_type="image",  # type: ignore
            file_path="/path/to/file.png",
            related_concept_id="concept-789",
        )
        assert content.media_type == MediaType.IMAGE

    def test_vector_validation_wrong_dimension(self):
        """Test that wrong vector dimension raises error."""
        with pytest.raises(ValueError, match="768 dimensions"):
            MultimodalContent(
                media_type=MediaType.IMAGE,
                file_path="/path/to/file.png",
                related_concept_id="concept-123",
                vector=[0.1] * 100,  # Wrong dimension
            )

    def test_to_dict(self):
        """Test content to dictionary conversion."""
        content = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            related_concept_id="concept-123",
        )
        d = content.to_dict()
        assert d["media_type"] == "image"
        assert d["file_path"] == "/path/to/image.png"
        assert "id" in d
        assert "created_at" in d

    def test_from_dict(self):
        """Test content from dictionary."""
        d = {
            "id": "test-id",
            "media_type": "pdf",
            "file_path": "/path/to/doc.pdf",
            "related_concept_id": "concept-456",
            "created_at": "2025-01-01T12:00:00",
        }
        content = MultimodalContent.from_dict(d)
        assert content.id == "test-id"
        assert content.media_type == MediaType.PDF
        assert content.file_path == "/path/to/doc.pdf"

    def test_to_lancedb_record(self):
        """Test conversion to LanceDB record format."""
        content = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            related_concept_id="concept-123",
        )
        record = content.to_lancedb_record()
        assert "id" in record
        assert record["media_type"] == "image"
        assert len(record["vector"]) == 768  # Default zero vector

    def test_to_neo4j_properties(self):
        """Test conversion to Neo4j properties."""
        content = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            related_concept_id="concept-123",
            description="A test image",
        )
        props = content.to_neo4j_properties()
        assert props["media_type"] == "image"
        assert props["description"] == "A test image"
        assert "id" in props

    def test_has_vector_property(self):
        """Test has_vector property."""
        content_no_vector = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            related_concept_id="concept-123",
        )
        assert not content_no_vector.has_vector

        content_with_vector = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            related_concept_id="concept-123",
            vector=[0.1] * 768,
        )
        assert content_with_vector.has_vector


class TestMultimodalStore:
    """Tests for MultimodalStore class."""

    @pytest.fixture
    def mock_lancedb_client(self):
        """Create mock LanceDB client."""
        client = AsyncMock()
        client.table_exists = AsyncMock(return_value=True)
        client.add_documents = AsyncMock()
        client.search = AsyncMock(return_value=[])
        client.delete = AsyncMock()
        client.count = AsyncMock(return_value=0)
        return client

    @pytest.fixture
    def mock_graphiti_client(self):
        """Create mock Graphiti client."""
        client = AsyncMock()
        client.add_memory = AsyncMock()
        client.add_relationship = AsyncMock()
        client.delete_memory = AsyncMock()
        client.list_memories = AsyncMock(return_value=[])
        client.search_facts = AsyncMock(return_value=[])
        return client

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def store(self, mock_lancedb_client, mock_graphiti_client, temp_storage_path):
        """Create MultimodalStore instance with mocks."""
        return MultimodalStore(
            lancedb_client=mock_lancedb_client,
            graphiti_client=mock_graphiti_client,
            storage_base_path=temp_storage_path,
        )

    def test_init_creates_directories(self, store, temp_storage_path):
        """Test that initialization creates storage directories."""
        base = Path(temp_storage_path)
        assert (base / "image").exists()
        assert (base / "pdf").exists()
        assert (base / "audio").exists()
        assert (base / "video").exists()
        assert (base / "thumbnails").exists()

    def test_get_storage_path(self, store, temp_storage_path):
        """Test storage path generation."""
        path = store.get_storage_path(MediaType.IMAGE, "test.png")
        # Cross-platform path check
        assert path.name == "test.png"
        assert path.parent.name == "image"

    def test_get_thumbnail_path(self, store, temp_storage_path):
        """Test thumbnail path generation."""
        path = store.get_thumbnail_path("content-123")
        # Cross-platform path check
        assert path.name == "content-123.jpg"
        assert path.parent.name == "thumbnails"

    @pytest.mark.asyncio
    async def test_add_content(self, store, mock_lancedb_client, mock_graphiti_client):
        """Test adding content to storage."""
        content = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            related_concept_id="concept-123",
        )

        result = await store.add(content)

        assert result == content.id
        mock_lancedb_client.add_documents.assert_called_once()
        mock_graphiti_client.add_memory.assert_called_once()
        mock_graphiti_client.add_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_content_missing_path(self, store):
        """Test adding content without file_path raises error."""
        content = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="",
            related_concept_id="concept-123",
        )

        with pytest.raises(ValueError, match="file_path is required"):
            await store.add(content)

    @pytest.mark.asyncio
    async def test_add_content_missing_concept(self, store):
        """Test adding content without related_concept_id raises error."""
        content = MultimodalContent(
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            related_concept_id="",
        )

        with pytest.raises(ValueError, match="related_concept_id is required"):
            await store.add(content)

    @pytest.mark.asyncio
    async def test_get_content(self, store, mock_lancedb_client):
        """Test retrieving content by ID."""
        mock_lancedb_client.search.return_value = [{
            "id": "content-123",
            "media_type": "image",
            "file_path": "/path/to/image.png",
            "related_concept_id": "concept-456",
            "created_at": "2025-01-01T12:00:00",
        }]

        result = await store.get("content-123")

        assert result is not None
        assert result.id == "content-123"
        assert result.media_type == MediaType.IMAGE

    @pytest.mark.asyncio
    async def test_get_content_not_found(self, store, mock_lancedb_client):
        """Test retrieving non-existent content returns None."""
        mock_lancedb_client.search.return_value = []

        result = await store.get("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_concept(self, store, mock_lancedb_client):
        """Test retrieving content by concept ID."""
        mock_lancedb_client.search.return_value = [
            {
                "id": "content-1",
                "media_type": "image",
                "file_path": "/path/to/1.png",
                "related_concept_id": "concept-123",
                "created_at": "2025-01-01T12:00:00",
            },
            {
                "id": "content-2",
                "media_type": "pdf",
                "file_path": "/path/to/2.pdf",
                "related_concept_id": "concept-123",
                "created_at": "2025-01-01T13:00:00",
            },
        ]

        results = await store.get_by_concept("concept-123")

        assert len(results) == 2
        assert results[0].id == "content-1"
        assert results[1].id == "content-2"

    @pytest.mark.asyncio
    async def test_search(self, store, mock_lancedb_client):
        """Test vector similarity search."""
        query_vector = [0.1] * 768
        mock_lancedb_client.search.return_value = [
            {
                "id": "content-1",
                "media_type": "image",
                "file_path": "/path/to/1.png",
                "related_concept_id": "concept-123",
                "created_at": "2025-01-01T12:00:00",
                "_distance": 0.95,
            },
        ]

        results = await store.search(query_vector, top_k=10)

        assert len(results) == 1
        content, score = results[0]
        assert content.id == "content-1"
        assert score == 0.95

    @pytest.mark.asyncio
    async def test_search_wrong_vector_dimension(self, store):
        """Test search with wrong vector dimension raises error."""
        query_vector = [0.1] * 100  # Wrong dimension

        with pytest.raises(ValueError, match="768 dimensions"):
            await store.search(query_vector)

    @pytest.mark.asyncio
    async def test_delete(self, store, mock_lancedb_client, mock_graphiti_client):
        """Test deleting content."""
        result = await store.delete("content-123")

        assert result is True
        mock_lancedb_client.delete.assert_called_once()
        mock_graphiti_client.delete_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_by_type(self, store, mock_lancedb_client):
        """Test listing content by type."""
        mock_lancedb_client.search.return_value = [
            {
                "id": "content-1",
                "media_type": "image",
                "file_path": "/path/to/1.png",
                "related_concept_id": "concept-123",
                "created_at": "2025-01-01T12:00:00",
            },
        ]

        results = await store.list_by_type(MediaType.IMAGE)

        assert len(results) == 1
        assert results[0].media_type == MediaType.IMAGE

    @pytest.mark.asyncio
    async def test_count(self, store, mock_lancedb_client):
        """Test counting content items."""
        mock_lancedb_client.count.return_value = 42

        result = await store.count(media_type=MediaType.IMAGE)

        assert result == 42
        mock_lancedb_client.count.assert_called_once()

    def test_normalize_path_absolute(self, store):
        """Test normalizing absolute path."""
        path = store.normalize_path("/absolute/path/to/file.png")
        assert Path(path).is_absolute()

    def test_normalize_path_relative(self, store, temp_storage_path):
        """Test normalizing relative path."""
        path = store.normalize_path("relative/file.png")
        assert Path(path).is_absolute()
        assert temp_storage_path in path

    @pytest.mark.asyncio
    async def test_health_check(self, store, mock_lancedb_client, mock_graphiti_client):
        """Test health check."""
        mock_lancedb_client.table_exists.return_value = True

        status = await store.health_check()

        assert status["lancedb"] is True
        assert status["neo4j"] is True
        assert status["storage_path_exists"] is True


class TestMultimodalStoreIntegration:
    """Integration tests for MultimodalStore (AC 6.3.1-6.3.4)."""

    @pytest.fixture
    def content_samples(self):
        """Create sample content for testing."""
        return [
            MultimodalContent(
                id="img-001",
                media_type=MediaType.IMAGE,
                file_path="/path/to/image1.png",
                related_concept_id="concept-001",
                description="Sample image 1",
                vector=[0.1] * 768,
            ),
            MultimodalContent(
                id="pdf-001",
                media_type=MediaType.PDF,
                file_path="/path/to/doc1.pdf",
                related_concept_id="concept-001",
                source_location="page 5",
                extracted_text="Sample text from PDF",
                metadata=MultimodalMetadata(page_count=10),
            ),
            MultimodalContent(
                id="audio-001",
                media_type=MediaType.AUDIO,
                file_path="/path/to/audio1.mp3",
                related_concept_id="concept-002",
                metadata=MultimodalMetadata(duration=120.5),
            ),
        ]

    def test_ac_6_3_1_lancedb_vector_dimension(self, content_samples):
        """AC 6.3.1: LanceDB table supports 768-dim vectors."""
        # Verify vector dimension in records
        for content in content_samples:
            record = content.to_lancedb_record()
            assert len(record["vector"]) == 768

    def test_ac_6_3_2_neo4j_properties(self, content_samples):
        """AC 6.3.2: Neo4j properties are correctly formatted."""
        for content in content_samples:
            props = content.to_neo4j_properties()
            assert "id" in props
            assert "media_type" in props
            assert "file_path" in props
            assert props["media_type"] in ["image", "pdf", "audio", "video"]

    def test_ac_6_3_3_unified_interface(self, content_samples):
        """AC 6.3.3: All media types use unified interface."""
        for content in content_samples:
            # All types should have same base methods
            assert hasattr(content, "to_dict")
            assert hasattr(content, "to_lancedb_record")
            assert hasattr(content, "to_neo4j_properties")
            assert hasattr(content, "has_vector")

            # All types should serialize/deserialize correctly
            d = content.to_dict()
            restored = MultimodalContent.from_dict(d)
            assert restored.id == content.id
            assert restored.media_type == content.media_type

    def test_ac_6_3_4_path_normalization(self):
        """AC 6.3.4: File paths are normalized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MultimodalStore(storage_base_path=tmpdir)

            # Test relative path normalization
            relative_path = "image/test.png"
            normalized = store.normalize_path(relative_path)
            assert Path(normalized).is_absolute()

            # Test absolute path preservation
            absolute_path = "/absolute/path/to/file.png"
            normalized = store.normalize_path(absolute_path)
            assert Path(normalized).is_absolute()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
