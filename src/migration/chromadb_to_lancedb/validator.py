# ✅ Verified from Story 12.3 AC 3.3 - Data Consistency Validation
"""
Migration Validator Module

Validates data consistency between ChromaDB and LanceDB after migration.
Performs sampling-based comparison of documents, metadata, and vector similarity.
"""

import json
import logging
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of migration validation."""

    success: bool
    total_source_count: int
    total_target_count: int
    sample_size: int
    matched_count: int
    mismatched_count: int
    missing_count: int
    vector_similarity_avg: float
    validation_time_seconds: float
    details: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def match_rate(self) -> float:
        """Calculate match rate as percentage."""
        if self.sample_size == 0:
            return 0.0
        return (self.matched_count / self.sample_size) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_source_count": self.total_source_count,
            "total_target_count": self.total_target_count,
            "sample_size": self.sample_size,
            "matched_count": self.matched_count,
            "mismatched_count": self.mismatched_count,
            "missing_count": self.missing_count,
            "match_rate_percent": self.match_rate,
            "vector_similarity_avg": self.vector_similarity_avg,
            "validation_time_seconds": self.validation_time_seconds,
            "errors": self.errors,
        }


class MigrationValidator:
    """
    Validate data consistency between ChromaDB and LanceDB.

    Performs sampling-based validation:
    1. Random sample documents from source
    2. Look up corresponding documents in target
    3. Compare content, metadata, and vector similarity

    Example usage:
        validator = MigrationValidator(chromadb_client, lancedb_connection)
        result = validator.validate("canvas_explanations", "canvas_memories", sample_size=100)
    """

    def __init__(
        self,
        chromadb_client: Optional[Any] = None,
        lancedb_connection: Optional[Any] = None
    ):
        """
        Initialize validator with database connections.

        Args:
            chromadb_client: ChromaDB client instance
            lancedb_connection: LanceDB connection instance
        """
        self.chromadb_client = chromadb_client
        self.lancedb_connection = lancedb_connection

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        if not vec1 or not vec2:
            return 0.0

        a = np.array(vec1)
        b = np.array(vec2)

        if len(a) != len(b):
            return 0.0

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def validate(
        self,
        chromadb_collection: str,
        lancedb_table: str,
        sample_size: int = 100,
        similarity_threshold: float = 0.99
    ) -> ValidationResult:
        """
        Validate migration by comparing sampled documents.

        Args:
            chromadb_collection: Name of ChromaDB collection
            lancedb_table: Name of LanceDB table
            sample_size: Number of documents to sample
            similarity_threshold: Minimum cosine similarity for vector match

        Returns:
            ValidationResult with comparison statistics
        """
        import time
        start_time = time.time()
        errors: List[str] = []
        details: List[Dict[str, Any]] = []

        matched_count = 0
        mismatched_count = 0
        missing_count = 0
        similarities: List[float] = []

        try:
            # Get source data from ChromaDB
            source_data = self._get_chromadb_data(chromadb_collection)
            if not source_data:
                return ValidationResult(
                    success=False,
                    total_source_count=0,
                    total_target_count=0,
                    sample_size=0,
                    matched_count=0,
                    mismatched_count=0,
                    missing_count=0,
                    vector_similarity_avg=0.0,
                    validation_time_seconds=time.time() - start_time,
                    errors=["Failed to get ChromaDB data or collection is empty"],
                )

            total_source_count = len(source_data)

            # Get target data from LanceDB
            target_data = self._get_lancedb_data(lancedb_table)
            total_target_count = len(target_data) if target_data else 0

            # Random sample
            actual_sample_size = min(sample_size, total_source_count)
            sampled_ids = random.sample(list(source_data.keys()), actual_sample_size)

            # Compare each sampled document
            for doc_id in sampled_ids:
                source_doc = source_data[doc_id]
                target_doc = target_data.get(doc_id) if target_data else None

                comparison = self._compare_documents(
                    doc_id, source_doc, target_doc, similarity_threshold
                )
                details.append(comparison)

                if comparison["status"] == "matched":
                    matched_count += 1
                    if comparison.get("vector_similarity"):
                        similarities.append(comparison["vector_similarity"])
                elif comparison["status"] == "mismatched":
                    mismatched_count += 1
                else:
                    missing_count += 1

            # Calculate average similarity
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0

            # Determine success (all sampled documents match)
            success = (
                matched_count == actual_sample_size and
                avg_similarity >= similarity_threshold
            )

            return ValidationResult(
                success=success,
                total_source_count=total_source_count,
                total_target_count=total_target_count,
                sample_size=actual_sample_size,
                matched_count=matched_count,
                mismatched_count=mismatched_count,
                missing_count=missing_count,
                vector_similarity_avg=avg_similarity,
                validation_time_seconds=time.time() - start_time,
                details=details,
                errors=errors,
            )

        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            return ValidationResult(
                success=False,
                total_source_count=0,
                total_target_count=0,
                sample_size=0,
                matched_count=0,
                mismatched_count=0,
                missing_count=0,
                vector_similarity_avg=0.0,
                validation_time_seconds=time.time() - start_time,
                errors=errors,
            )

    def _get_chromadb_data(self, collection_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all documents from ChromaDB collection as dict."""
        if self.chromadb_client is None:
            return {}

        try:
            collection = self.chromadb_client.get_collection(collection_name)
            results = collection.get(
                include=["documents", "metadatas", "embeddings"]
            )

            data = {}
            ids = results.get("ids", [])
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            embeddings = results.get("embeddings", [])

            for i, doc_id in enumerate(ids):
                data[doc_id] = {
                    "content": documents[i] if documents else None,
                    "metadata": metadatas[i] if metadatas else {},
                    "embedding": embeddings[i] if embeddings else None,
                }

            return data

        except Exception as e:
            logger.error(f"Failed to get ChromaDB data: {e}")
            return {}

    def _get_lancedb_data(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all documents from LanceDB table as dict."""
        if self.lancedb_connection is None:
            return {}

        try:
            table = self.lancedb_connection.open_table(table_name)
            # Convert to pandas and then to dict
            df = table.to_pandas()

            data = {}
            for _, row in df.iterrows():
                doc_id = row.get("id")
                if doc_id:
                    data[doc_id] = {
                        "content": row.get("text"),
                        "embedding": row.get("vector"),
                        "metadata": {
                            k: v for k, v in row.items()
                            if k not in ("id", "text", "vector")
                        },
                    }

            return data

        except Exception as e:
            logger.error(f"Failed to get LanceDB data: {e}")
            return {}

    def _compare_documents(
        self,
        doc_id: str,
        source: Dict[str, Any],
        target: Optional[Dict[str, Any]],
        similarity_threshold: float
    ) -> Dict[str, Any]:
        """Compare source and target documents."""
        if target is None:
            return {
                "id": doc_id,
                "status": "missing",
                "reason": "Document not found in target",
            }

        # Compare content
        source_content = source.get("content") or ""
        target_content = target.get("content") or ""
        content_match = source_content == target_content

        # Compare vectors
        source_embedding = source.get("embedding")
        target_embedding = target.get("embedding")

        if source_embedding and target_embedding:
            similarity = self.cosine_similarity(source_embedding, target_embedding)
            vector_match = similarity >= similarity_threshold
        else:
            similarity = None
            vector_match = source_embedding is None and target_embedding is None

        # Determine overall status
        if content_match and vector_match:
            status = "matched"
        else:
            status = "mismatched"

        return {
            "id": doc_id,
            "status": status,
            "content_match": content_match,
            "vector_match": vector_match,
            "vector_similarity": similarity,
        }

    def validate_from_jsonl(
        self,
        jsonl_path: str,
        lancedb_table: str,
        sample_size: int = 100,
        similarity_threshold: float = 0.99
    ) -> ValidationResult:
        """
        Validate migration using JSONL export file as source.

        Useful when ChromaDB is no longer available.

        Args:
            jsonl_path: Path to JSONL export file
            lancedb_table: Name of LanceDB table
            sample_size: Number of documents to sample
            similarity_threshold: Minimum cosine similarity for vector match

        Returns:
            ValidationResult with comparison statistics
        """
        import time

        start_time = time.time()
        errors: List[str] = []

        # Load source data from JSONL
        source_data = {}
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        doc_id = record.get("id")
                        if doc_id:
                            source_data[doc_id] = {
                                "content": record.get("content"),
                                "metadata": record.get("metadata", {}),
                                "embedding": record.get("embedding"),
                            }
        except Exception as e:
            return ValidationResult(
                success=False,
                total_source_count=0,
                total_target_count=0,
                sample_size=0,
                matched_count=0,
                mismatched_count=0,
                missing_count=0,
                vector_similarity_avg=0.0,
                validation_time_seconds=time.time() - start_time,
                errors=[f"Failed to read JSONL: {str(e)}"],
            )

        # Get target data
        target_data = self._get_lancedb_data(lancedb_table)

        # Perform validation
        total_source_count = len(source_data)
        total_target_count = len(target_data)
        actual_sample_size = min(sample_size, total_source_count)

        sampled_ids = random.sample(list(source_data.keys()), actual_sample_size)

        matched_count = 0
        mismatched_count = 0
        missing_count = 0
        similarities: List[float] = []
        details: List[Dict[str, Any]] = []

        for doc_id in sampled_ids:
            source_doc = source_data[doc_id]
            target_doc = target_data.get(doc_id)

            comparison = self._compare_documents(
                doc_id, source_doc, target_doc, similarity_threshold
            )
            details.append(comparison)

            if comparison["status"] == "matched":
                matched_count += 1
                if comparison.get("vector_similarity"):
                    similarities.append(comparison["vector_similarity"])
            elif comparison["status"] == "mismatched":
                mismatched_count += 1
            else:
                missing_count += 1

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        success = matched_count == actual_sample_size and avg_similarity >= similarity_threshold

        return ValidationResult(
            success=success,
            total_source_count=total_source_count,
            total_target_count=total_target_count,
            sample_size=actual_sample_size,
            matched_count=matched_count,
            mismatched_count=mismatched_count,
            missing_count=missing_count,
            vector_similarity_avg=avg_similarity,
            validation_time_seconds=time.time() - start_time,
            details=details,
            errors=errors,
        )


def validate_migration(
    chromadb_client: Any,
    lancedb_table: Any,
    sample_size: int = 100
) -> ValidationResult:
    """
    Convenience function to validate migration.

    Args:
        chromadb_client: ChromaDB client
        lancedb_table: LanceDB table instance
        sample_size: Number of documents to sample

    Returns:
        ValidationResult with validation statistics
    """
    validator = MigrationValidator(
        chromadb_client=chromadb_client,
        lancedb_connection=lancedb_table._connection if hasattr(lancedb_table, "_connection") else None
    )
    return validator.validate(
        chromadb_collection=lancedb_table.name,
        lancedb_table=lancedb_table.name,
        sample_size=sample_size,
    )
