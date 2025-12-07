# ✅ Verified from Story 12.3 - Migration Test Suite
"""
Test suite for ChromaDB to LanceDB migration.

Tests all migration components:
- ChromaDB export to JSONL
- LanceDB import from JSONL
- Data consistency validation
- Dual-write adapter
- Rollback functionality
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest


class MockChromaDBCollection:
    """Mock ChromaDB collection for testing."""

    def __init__(self, data: List[Dict[str, Any]] = None):
        self.data = data or []
        self._build_index()

    def _build_index(self):
        self._index = {item["id"]: i for i, item in enumerate(self.data)}

    def get(self, ids=None, include=None):
        if ids:
            indices = [self._index[id] for id in ids if id in self._index]
        else:
            indices = range(len(self.data))

        result = {
            "ids": [self.data[i]["id"] for i in indices],
            "documents": [self.data[i].get("content") for i in indices],
            "metadatas": [self.data[i].get("metadata", {}) for i in indices],
            "embeddings": [self.data[i].get("embedding") for i in indices],
        }
        return result

    def upsert(self, ids, documents, embeddings, metadatas):
        for i, id in enumerate(ids):
            if id in self._index:
                idx = self._index[id]
                self.data[idx] = {
                    "id": id,
                    "content": documents[i],
                    "embedding": embeddings[i],
                    "metadata": metadatas[i],
                }
            else:
                self.data.append({
                    "id": id,
                    "content": documents[i],
                    "embedding": embeddings[i],
                    "metadata": metadatas[i],
                })
                self._build_index()

    def delete(self, ids):
        for id in ids:
            if id in self._index:
                del self.data[self._index[id]]
                self._build_index()


class MockChromaDBClient:
    """Mock ChromaDB client for testing."""

    def __init__(self):
        self.collections = {}

    def get_collection(self, name):
        if name not in self.collections:
            self.collections[name] = MockChromaDBCollection()
        return self.collections[name]

    def get_or_create_collection(self, name):
        return self.get_collection(name)

    def list_collections(self):
        return [MagicMock(name=name) for name in self.collections.keys()]


class TestChromaDBExporter:
    """Tests for ChromaDB exporter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_client = MockChromaDBClient()

        # Add test data
        collection = self.mock_client.get_collection("test_collection")
        collection.data = [
            {
                "id": f"doc_{i}",
                "content": f"Test document {i}",
                "metadata": {"source": "test", "index": i},
                "embedding": [0.1 * i] * 384,
            }
            for i in range(10)
        ]
        collection._build_index()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_collection_success(self):
        """Test successful collection export."""
        from src.migration.chromadb_to_lancedb.exporter import ChromaDBExporter

        exporter = ChromaDBExporter(client=self.mock_client)
        result = exporter.export_collection("test_collection", self.temp_dir)

        assert result.success is True
        assert result.record_count == 10
        assert result.collection_name == "test_collection"
        assert Path(result.output_path).exists()

        # Verify JSONL content
        with open(result.output_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 10

            first_record = json.loads(lines[0])
            assert "id" in first_record
            assert "content" in first_record
            assert "metadata" in first_record
            assert "embedding" in first_record

    def test_export_empty_collection(self):
        """Test exporting empty collection."""
        from src.migration.chromadb_to_lancedb.exporter import ChromaDBExporter

        exporter = ChromaDBExporter(client=self.mock_client)
        result = exporter.export_collection("empty_collection", self.temp_dir)

        assert result.success is True
        assert result.record_count == 0

    def test_list_collections(self):
        """Test listing collections."""
        from src.migration.chromadb_to_lancedb.exporter import ChromaDBExporter

        exporter = ChromaDBExporter(client=self.mock_client)
        collections = exporter.list_collections()

        assert "test_collection" in collections


class TestLanceDBImporter:
    """Tests for LanceDB importer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test JSONL file
        self.jsonl_path = Path(self.temp_dir) / "test_export.jsonl"
        with open(self.jsonl_path, "w") as f:
            for i in range(10):
                record = {
                    "id": f"doc_{i}",
                    "content": f"Test document {i}",
                    "metadata": {"source": "test", "index": i},
                    "embedding": [0.1 * i] * 384,
                }
                f.write(json.dumps(record) + "\n")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import_jsonl_without_lancedb(self):
        """Test import behavior when LanceDB is not available."""
        from src.migration.chromadb_to_lancedb.importer import LanceDBImporter

        # Import should handle missing LanceDB gracefully
        importer = LanceDBImporter(db_path=self.temp_dir)

        # If LanceDB is not installed, db will be None
        if importer.db is None:
            result = importer.import_jsonl(str(self.jsonl_path), "test_table")
            assert result.success is False
            assert "not initialized" in result.errors[0].lower() or len(result.errors) > 0

    def test_import_missing_file(self):
        """Test import with missing source file."""
        from src.migration.chromadb_to_lancedb.importer import LanceDBImporter

        importer = LanceDBImporter(db_path=self.temp_dir)
        result = importer.import_jsonl("nonexistent.jsonl", "test_table")

        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_map_record(self):
        """Test record mapping from ChromaDB to LanceDB format."""
        from src.migration.chromadb_to_lancedb.importer import LanceDBImporter

        importer = LanceDBImporter(db_path=self.temp_dir)

        chromadb_record = {
            "id": "test_id",
            "content": "test content",
            "metadata": {"source": "test"},
            "embedding": [0.1, 0.2, 0.3],
        }

        lancedb_record = importer._map_record(chromadb_record)

        assert lancedb_record["id"] == "test_id"
        assert lancedb_record["text"] == "test content"
        assert lancedb_record["vector"] == [0.1, 0.2, 0.3]
        assert lancedb_record["source"] == "test"


class TestMigrationValidator:
    """Tests for migration validator."""

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        from src.migration.chromadb_to_lancedb.validator import MigrationValidator

        validator = MigrationValidator()

        # Same vector should have similarity 1.0
        vec = [1.0, 0.0, 0.0]
        assert validator.cosine_similarity(vec, vec) == pytest.approx(1.0)

        # Orthogonal vectors should have similarity 0.0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert validator.cosine_similarity(vec1, vec2) == pytest.approx(0.0)

        # Empty vectors
        assert validator.cosine_similarity([], []) == 0.0
        assert validator.cosine_similarity([1.0], []) == 0.0

    def test_compare_documents_matched(self):
        """Test document comparison with matching documents."""
        from src.migration.chromadb_to_lancedb.validator import MigrationValidator

        validator = MigrationValidator()

        source = {"content": "test", "embedding": [1.0, 0.0, 0.0]}
        target = {"content": "test", "embedding": [1.0, 0.0, 0.0]}

        result = validator._compare_documents("doc1", source, target, 0.99)

        assert result["status"] == "matched"
        assert result["content_match"] is True
        assert result["vector_match"] is True

    def test_compare_documents_missing(self):
        """Test document comparison with missing target."""
        from src.migration.chromadb_to_lancedb.validator import MigrationValidator

        validator = MigrationValidator()

        source = {"content": "test", "embedding": [1.0, 0.0, 0.0]}

        result = validator._compare_documents("doc1", source, None, 0.99)

        assert result["status"] == "missing"


class TestDualWriteAdapter:
    """Tests for dual-write adapter."""

    def test_store_memory_both_databases(self):
        """Test storing memory in both databases."""
        from src.migration.chromadb_to_lancedb.dual_write_adapter import (
            DualWriteAdapter,
            VectorDatabaseAdapter,
        )

        # Create mock adapters
        class MockAdapter(VectorDatabaseAdapter):
            def __init__(self):
                self.stored = {}

            def store_memory(self, memory_id, content, embedding, metadata=None):
                self.stored[memory_id] = {
                    "content": content,
                    "embedding": embedding,
                    "metadata": metadata,
                }
                return memory_id

            def search_memory(self, query_embedding, limit=10, filter_dict=None):
                return []

            def delete_memory(self, memory_id):
                if memory_id in self.stored:
                    del self.stored[memory_id]
                    return True
                return False

            def get_memory(self, memory_id):
                return self.stored.get(memory_id)

        primary = MockAdapter()
        secondary = MockAdapter()
        dual = DualWriteAdapter(primary, secondary)

        # Store memory
        dual.store_memory("test_id", "test content", [0.1, 0.2], {"key": "value"})

        # Verify both databases have the data
        assert "test_id" in primary.stored
        assert "test_id" in secondary.stored
        assert primary.stored["test_id"]["content"] == "test content"
        assert secondary.stored["test_id"]["content"] == "test content"

    def test_get_stats(self):
        """Test statistics tracking."""
        from src.migration.chromadb_to_lancedb.dual_write_adapter import (
            DualWriteAdapter,
            VectorDatabaseAdapter,
        )

        class MockAdapter(VectorDatabaseAdapter):
            def store_memory(self, memory_id, content, embedding, metadata=None):
                return memory_id

            def search_memory(self, query_embedding, limit=10, filter_dict=None):
                return []

            def delete_memory(self, memory_id):
                return True

            def get_memory(self, memory_id):
                return None

        primary = MockAdapter()
        secondary = MockAdapter()
        dual = DualWriteAdapter(primary, secondary)

        # Perform some writes
        for i in range(5):
            dual.store_memory(f"id_{i}", f"content_{i}", [0.1], None)

        stats = dual.get_stats()
        assert stats.total_writes == 5
        assert stats.successful_writes == 5
        assert stats.failed_writes == 0


class TestRollbackManager:
    """Tests for rollback manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_dir = Path(self.temp_dir) / "backups"
        self.source_dir = Path(self.temp_dir) / "chromadb_data"

        # Create mock ChromaDB data
        self.source_dir.mkdir(parents=True)
        (self.source_dir / "test_file.txt").write_text("test data")
        (self.source_dir / "subdir").mkdir()
        (self.source_dir / "subdir" / "nested.txt").write_text("nested data")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_backup_chromadb_success(self):
        """Test successful backup creation."""
        from src.migration.chromadb_to_lancedb.rollback import RollbackManager

        manager = RollbackManager(str(self.backup_dir))
        result = manager.backup_chromadb(str(self.source_dir))

        assert result.success is True
        assert result.file_size_bytes > 0
        assert Path(result.backup_path).exists()
        assert result.backup_path.endswith(".tar.gz")

    def test_backup_nonexistent_path(self):
        """Test backup with nonexistent source."""
        from src.migration.chromadb_to_lancedb.rollback import RollbackManager

        manager = RollbackManager(str(self.backup_dir))
        result = manager.backup_chromadb("/nonexistent/path")

        assert result.success is False
        assert "does not exist" in result.errors[0].lower()

    def test_restore_chromadb_success(self):
        """Test successful restore from backup."""
        from src.migration.chromadb_to_lancedb.rollback import RollbackManager

        manager = RollbackManager(str(self.backup_dir))

        # Create backup
        backup_result = manager.backup_chromadb(str(self.source_dir))
        assert backup_result.success

        # Delete original
        shutil.rmtree(self.source_dir)

        # Restore
        restore_path = Path(self.temp_dir) / "restored_data"
        restore_result = manager.restore_chromadb(
            backup_result.backup_path,
            str(restore_path)
        )

        assert restore_result.success is True
        assert restore_path.exists()
        assert (restore_path / "test_file.txt").read_text() == "test data"

    def test_list_backups(self):
        """Test listing available backups."""
        from src.migration.chromadb_to_lancedb.rollback import RollbackManager

        manager = RollbackManager(str(self.backup_dir))

        # Create multiple backups
        manager.backup_chromadb(str(self.source_dir), "backup_1")
        manager.backup_chromadb(str(self.source_dir), "backup_2")

        backups = manager.list_backups()
        assert len(backups) == 2

    def test_verify_backup(self):
        """Test backup verification."""
        from src.migration.chromadb_to_lancedb.rollback import RollbackManager

        manager = RollbackManager(str(self.backup_dir))

        # Create backup
        result = manager.backup_chromadb(str(self.source_dir))

        # Verify valid backup
        assert manager.verify_backup(result.backup_path) is True

        # Verify nonexistent backup
        assert manager.verify_backup("/nonexistent.tar.gz") is False

    def test_cleanup_old_backups(self):
        """Test cleanup of old backups."""
        import time

        from src.migration.chromadb_to_lancedb.rollback import RollbackManager

        manager = RollbackManager(str(self.backup_dir))

        # Create multiple backups
        for i in range(5):
            manager.backup_chromadb(str(self.source_dir), f"backup_{i}")
            time.sleep(0.1)  # Ensure different timestamps

        # Keep only 2 backups
        deleted = manager.cleanup_old_backups(keep_count=2)

        assert deleted == 3
        assert len(manager.list_backups()) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
