"""
Multimodal content storage interface.

This module provides a unified interface for storing and retrieving
multimodal content using LanceDB (vectors) and Neo4j (relationships).

Verified from Story 6.3:
- AC 6.3.1: LanceDB table with multimodal=True
- AC 6.3.2: Neo4j Schema with Media nodes
- AC 6.3.3: Unified MultimodalContent interface
- AC 6.3.4: Normalized file storage paths
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.multimodal_content import MediaType, MultimodalContent

logger = logging.getLogger(__name__)


class MultimodalStore:
    """
    Unified storage interface for multimodal content.

    Combines LanceDB for vector storage/search and Neo4j for
    relationship management between concepts and media content.

    Verified from Story 6.3 (AC 6.3.3): Unified interface for CRUD operations
    """

    # LanceDB table name for multimodal content
    LANCEDB_TABLE_NAME = "multimodal_content"

    # Neo4j labels and relationship types
    NEO4J_MEDIA_LABEL = "Media"
    NEO4J_CONCEPT_LABEL = "Concept"
    NEO4J_HAS_MEDIA = "HAS_MEDIA"
    NEO4J_ILLUSTRATES = "ILLUSTRATES"
    NEO4J_REFERENCES = "REFERENCES"

    # Default storage base path
    DEFAULT_STORAGE_PATH = ".canvas-learning/multimodal"

    def __init__(
        self,
        lancedb_client=None,
        graphiti_client=None,
        storage_base_path: Optional[str] = None,
        vector_dim: int = 768,
    ):
        """
        Initialize MultimodalStore.

        Args:
            lancedb_client: LanceDB client instance
            graphiti_client: Graphiti client instance
            storage_base_path: Base path for file storage
            vector_dim: Dimension of embedding vectors (default: 768)
        """
        self.lancedb_client = lancedb_client
        self.graphiti_client = graphiti_client
        self.storage_base_path = Path(
            storage_base_path or self.DEFAULT_STORAGE_PATH
        )
        self.vector_dim = vector_dim

        # Ensure storage directories exist
        self._ensure_storage_dirs()

    def _ensure_storage_dirs(self) -> None:
        """Create storage directories if they don't exist."""
        for media_type in MediaType:
            dir_path = self.storage_base_path / media_type.value
            dir_path.mkdir(parents=True, exist_ok=True)
        # Also create thumbnails directory
        (self.storage_base_path / "thumbnails").mkdir(parents=True, exist_ok=True)

    def get_storage_path(self, media_type: MediaType, filename: str) -> Path:
        """
        Get normalized storage path for a media file.

        Verified from Story 6.3 (AC 6.3.4): File storage path normalization

        Args:
            media_type: Type of media content
            filename: Original filename

        Returns:
            Normalized path for file storage
        """
        return self.storage_base_path / media_type.value / filename

    def get_thumbnail_path(self, content_id: str) -> Path:
        """
        Get thumbnail path for a content item.

        Args:
            content_id: Content UUID

        Returns:
            Path for thumbnail storage
        """
        return self.storage_base_path / "thumbnails" / f"{content_id}.jpg"

    async def add(self, content: MultimodalContent) -> str:
        """
        Add multimodal content to storage.

        Creates entries in both LanceDB (for vector search) and
        Neo4j (for relationship management).

        Args:
            content: MultimodalContent instance to store

        Returns:
            Content ID

        Raises:
            ValueError: If content is invalid
        """
        logger.info(f"Adding multimodal content: {content.id} ({content.media_type.value})")

        # Validate content
        if not content.file_path:
            raise ValueError("file_path is required")
        if not content.related_concept_id:
            raise ValueError("related_concept_id is required")

        # Add to LanceDB
        if self.lancedb_client:
            await self._add_to_lancedb(content)

        # Add to Neo4j
        if self.graphiti_client:
            await self._add_to_neo4j(content)

        logger.info(f"Successfully added content: {content.id}")
        return content.id

    async def _add_to_lancedb(self, content: MultimodalContent) -> None:
        """
        Add content to LanceDB table.

        Verified from Story 6.3 (AC 6.3.1): LanceDB table with 768-dim vectors
        """
        record = content.to_lancedb_record()

        # Ensure table exists
        if not await self.lancedb_client.table_exists(self.LANCEDB_TABLE_NAME):
            await self._create_lancedb_table()

        await self.lancedb_client.add_documents(
            table_name=self.LANCEDB_TABLE_NAME,
            documents=[record],
        )

    async def _create_lancedb_table(self) -> None:
        """Create LanceDB table with proper schema."""
        schema = {
            "id": "string",
            "media_type": "string",
            "file_path": "string",
            "related_concept_id": "string",
            "thumbnail_path": "string",
            "extracted_text": "string",
            "description": "string",
            "vector": f"vector[{self.vector_dim}]",
            "source_location": "string",
            "created_at": "string",
            "metadata": "json",
        }

        await self.lancedb_client.create_table(
            table_name=self.LANCEDB_TABLE_NAME,
            schema=schema,
            mode="create",
        )
        logger.info(f"Created LanceDB table: {self.LANCEDB_TABLE_NAME}")

    async def _add_to_neo4j(self, content: MultimodalContent) -> None:
        """
        Add content to Neo4j as Media node with relationship.

        Verified from Story 6.3 (AC 6.3.2): Neo4j Schema with Media nodes
        """
        # Create Media node
        properties = content.to_neo4j_properties()

        # Use graphiti client to create the node and relationship
        await self.graphiti_client.add_memory(
            key=f"media:{content.id}",
            content=f"Media file: {content.file_path}",
            metadata={
                "type": "media",
                "media_type": content.media_type.value,
                **properties,
            },
        )

        # Create HAS_MEDIA relationship to concept
        await self.graphiti_client.add_relationship(
            entity1=content.related_concept_id,
            entity2=content.id,
            relationship_type=self.NEO4J_HAS_MEDIA,
        )

    async def get(self, content_id: str) -> Optional[MultimodalContent]:
        """
        Retrieve content by ID.

        Args:
            content_id: Content UUID

        Returns:
            MultimodalContent if found, None otherwise
        """
        if self.lancedb_client:
            results = await self.lancedb_client.search(
                table_name=self.LANCEDB_TABLE_NAME,
                query_vector=None,
                filter={"id": content_id},
                limit=1,
            )

            if results:
                return MultimodalContent.from_dict(results[0])

        return None

    async def get_by_concept(
        self,
        concept_id: str,
        media_type: Optional[MediaType] = None,
    ) -> list[MultimodalContent]:
        """
        Get all content associated with a concept.

        Args:
            concept_id: Concept node ID
            media_type: Optional filter by media type

        Returns:
            List of MultimodalContent items
        """
        filter_dict = {"related_concept_id": concept_id}

        if media_type:
            filter_dict["media_type"] = media_type.value

        if self.lancedb_client:
            results = await self.lancedb_client.search(
                table_name=self.LANCEDB_TABLE_NAME,
                query_vector=None,
                filter=filter_dict,
                limit=100,
            )

            return [MultimodalContent.from_dict(r) for r in results]

        return []

    async def search(
        self,
        query_vector: list[float],
        media_types: Optional[list[MediaType]] = None,
        top_k: int = 10,
        min_score: float = 0.5,
    ) -> list[tuple[MultimodalContent, float]]:
        """
        Search content by vector similarity.

        Args:
            query_vector: 768-dimensional query vector
            media_types: Optional filter by media types
            top_k: Maximum number of results
            min_score: Minimum similarity score

        Returns:
            List of (content, score) tuples
        """
        if len(query_vector) != self.vector_dim:
            raise ValueError(
                f"Query vector must have {self.vector_dim} dimensions"
            )

        filter_dict = {}
        if media_types:
            filter_dict["media_type"] = {
                "$in": [mt.value for mt in media_types]
            }

        if self.lancedb_client:
            results = await self.lancedb_client.search(
                table_name=self.LANCEDB_TABLE_NAME,
                query_vector=query_vector,
                filter=filter_dict if filter_dict else None,
                limit=top_k,
            )

            # Filter by min_score and convert to MultimodalContent
            output = []
            for r in results:
                score = r.get("_distance", 0)
                if score >= min_score:
                    content = MultimodalContent.from_dict(r)
                    output.append((content, score))

            return output

        return []

    async def update(
        self,
        content_id: str,
        updates: dict,
    ) -> bool:
        """
        Update content fields.

        Args:
            content_id: Content UUID
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        # Get existing content
        content = await self.get(content_id)
        if not content:
            return False

        # Apply updates
        for key, value in updates.items():
            if hasattr(content, key):
                setattr(content, key, value)

        content.updated_at = datetime.now()

        # Re-add to storage (LanceDB doesn't support true updates)
        await self._add_to_lancedb(content)

        logger.info(f"Updated content: {content_id}")
        return True

    async def delete(self, content_id: str) -> bool:
        """
        Delete content from storage.

        Args:
            content_id: Content UUID

        Returns:
            True if deleted, False if not found
        """
        # Delete from LanceDB
        if self.lancedb_client:
            await self.lancedb_client.delete(
                table_name=self.LANCEDB_TABLE_NAME,
                filter={"id": content_id},
            )

        # Delete from Neo4j
        if self.graphiti_client:
            await self.graphiti_client.delete_memory(content_id)

        logger.info(f"Deleted content: {content_id}")
        return True

    async def list_by_type(
        self,
        media_type: MediaType,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MultimodalContent]:
        """
        List content by media type.

        Args:
            media_type: Type of media to list
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of MultimodalContent items
        """
        if self.lancedb_client:
            results = await self.lancedb_client.search(
                table_name=self.LANCEDB_TABLE_NAME,
                query_vector=None,
                filter={"media_type": media_type.value},
                limit=limit,
            )

            return [MultimodalContent.from_dict(r) for r in results]

        return []

    async def count(
        self,
        media_type: Optional[MediaType] = None,
        concept_id: Optional[str] = None,
    ) -> int:
        """
        Count content items.

        Args:
            media_type: Optional filter by media type
            concept_id: Optional filter by concept

        Returns:
            Number of matching items
        """
        filter_dict = {}
        if media_type:
            filter_dict["media_type"] = media_type.value
        if concept_id:
            filter_dict["related_concept_id"] = concept_id

        if self.lancedb_client:
            return await self.lancedb_client.count(
                table_name=self.LANCEDB_TABLE_NAME,
                filter=filter_dict if filter_dict else None,
            )

        return 0

    async def get_related_concepts(
        self,
        content_id: str,
    ) -> list[str]:
        """
        Get concepts related to a content item.

        Uses Neo4j to traverse HAS_MEDIA relationships.

        Args:
            content_id: Content UUID

        Returns:
            List of concept IDs
        """
        if self.graphiti_client:
            # Search for relationships
            results = await self.graphiti_client.search_facts(
                query=f"media:{content_id}"
            )

            # Extract concept IDs from relationships
            concept_ids = []
            for r in results:
                if r.get("relationship_type") == self.NEO4J_HAS_MEDIA:
                    concept_ids.append(r.get("entity1"))

            return concept_ids

        return []

    def normalize_path(self, file_path: str) -> str:
        """
        Normalize file path for storage.

        Verified from Story 6.3 (AC 6.3.4)

        Args:
            file_path: Original file path

        Returns:
            Normalized absolute path
        """
        path = Path(file_path)

        # If relative, make it relative to storage base
        if not path.is_absolute():
            path = self.storage_base_path / path

        return str(path.resolve())

    async def health_check(self) -> dict:
        """
        Check storage health.

        Returns:
            Dictionary with health status
        """
        status = {
            "lancedb": False,
            "neo4j": False,
            "storage_path_exists": self.storage_base_path.exists(),
        }

        if self.lancedb_client:
            try:
                status["lancedb"] = await self.lancedb_client.table_exists(
                    self.LANCEDB_TABLE_NAME
                )
            except Exception as e:
                logger.error(f"LanceDB health check failed: {e}")

        if self.graphiti_client:
            try:
                # Simple connectivity check
                await self.graphiti_client.list_memories()
                status["neo4j"] = True
            except Exception as e:
                logger.error(f"Neo4j health check failed: {e}")

        return status
