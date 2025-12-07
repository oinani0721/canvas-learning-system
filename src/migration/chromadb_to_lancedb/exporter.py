# ✅ Verified from Story 12.3 AC 3.1 - ChromaDB Data Export
"""
ChromaDB Exporter Module

Exports ChromaDB collection data to JSONL format for migration to LanceDB.
Each line in the output file contains one document with its metadata and embedding.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of ChromaDB export operation."""

    success: bool
    collection_name: str
    output_path: str
    record_count: int
    file_size_bytes: int
    export_time_seconds: float
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "collection_name": self.collection_name,
            "output_path": self.output_path,
            "record_count": self.record_count,
            "file_size_bytes": self.file_size_bytes,
            "export_time_seconds": self.export_time_seconds,
            "errors": self.errors,
        }


class ChromaDBExporter:
    """
    Export ChromaDB collections to JSONL format.

    Each exported document contains:
    - id: Document ID
    - content: Document text content
    - metadata: Document metadata dict
    - embedding: Vector embedding (list of floats)

    Example usage:
        exporter = ChromaDBExporter(chromadb_client)
        result = exporter.export_collection("canvas_explanations", "data/migration/")
    """

    def __init__(self, client: Optional[Any] = None, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB exporter.

        Args:
            client: Existing ChromaDB client instance
            persist_directory: Path to ChromaDB persistence directory (if no client provided)
        """
        self.client = client
        self.persist_directory = persist_directory

        if self.client is None and self.persist_directory:
            self._init_client()

    def _init_client(self) -> None:
        """Initialize ChromaDB client from persist directory."""
        try:
            import chromadb
            from chromadb.config import Settings

            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            logger.info(f"Initialized ChromaDB client from {self.persist_directory}")
        except ImportError:
            logger.warning("chromadb not installed, using mock client")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            self.client = None

    def list_collections(self) -> List[str]:
        """List all available collections in ChromaDB."""
        if self.client is None:
            return []

        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def export_collection(
        self,
        collection_name: str,
        output_dir: str,
        batch_size: int = 1000
    ) -> ExportResult:
        """
        Export a ChromaDB collection to JSONL format.

        Args:
            collection_name: Name of the collection to export
            output_dir: Directory to save the JSONL file
            batch_size: Number of records to fetch per batch

        Returns:
            ExportResult with export statistics
        """
        import time
        start_time = time.time()
        errors: List[str] = []
        record_count = 0

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"chromadb_export_{collection_name}_{timestamp}.jsonl"

        try:
            if self.client is None:
                raise ValueError("ChromaDB client not initialized")

            # Get collection
            collection = self.client.get_collection(collection_name)

            # Get all documents with embeddings and metadata
            # ✅ Verified from ChromaDB docs - get() returns documents, metadatas, embeddings
            results = collection.get(
                include=["documents", "metadatas", "embeddings"]
            )

            ids = results.get("ids", [])
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            embeddings = results.get("embeddings", [])

            # Write to JSONL
            with open(output_file, "w", encoding="utf-8") as f:
                for i, doc_id in enumerate(ids):
                    record = {
                        "id": doc_id,
                        "content": documents[i] if documents else None,
                        "metadata": metadatas[i] if metadatas else {},
                        "embedding": embeddings[i] if embeddings else None,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    record_count += 1

            logger.info(f"Exported {record_count} records from {collection_name}")

        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            # Create empty result on failure
            return ExportResult(
                success=False,
                collection_name=collection_name,
                output_path=str(output_file),
                record_count=0,
                file_size_bytes=0,
                export_time_seconds=time.time() - start_time,
                errors=errors,
            )

        # Calculate file size
        file_size = output_file.stat().st_size if output_file.exists() else 0
        export_time = time.time() - start_time

        return ExportResult(
            success=True,
            collection_name=collection_name,
            output_path=str(output_file),
            record_count=record_count,
            file_size_bytes=file_size,
            export_time_seconds=export_time,
            errors=errors,
        )

    def export_all_collections(
        self,
        output_dir: str,
        collections: Optional[List[str]] = None
    ) -> Dict[str, ExportResult]:
        """
        Export multiple collections to JSONL files.

        Args:
            output_dir: Directory to save JSONL files
            collections: List of collection names (None = all collections)

        Returns:
            Dict mapping collection names to ExportResults
        """
        if collections is None:
            collections = self.list_collections()

        results = {}
        for collection_name in collections:
            logger.info(f"Exporting collection: {collection_name}")
            results[collection_name] = self.export_collection(
                collection_name, output_dir
            )

        return results


def export_collection_to_jsonl(
    collection_name: str,
    output_path: str,
    chromadb_client: Optional[Any] = None,
    persist_directory: Optional[str] = None
) -> ExportResult:
    """
    Convenience function to export a ChromaDB collection to JSONL.

    Args:
        collection_name: Name of collection to export
        output_path: Directory path for output file
        chromadb_client: Optional existing ChromaDB client
        persist_directory: Optional path to ChromaDB persistence directory

    Returns:
        ExportResult with export statistics
    """
    exporter = ChromaDBExporter(
        client=chromadb_client,
        persist_directory=persist_directory
    )
    return exporter.export_collection(collection_name, output_path)
