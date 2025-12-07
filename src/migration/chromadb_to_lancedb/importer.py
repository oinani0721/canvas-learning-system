# ✅ Verified from Story 12.3 AC 3.2 - LanceDB Data Import
# ✅ Verified from Context7 /lancedb/lancedb - create_table, add
"""
LanceDB Importer Module

Imports JSONL data exported from ChromaDB into LanceDB tables.
Supports batch import and schema mapping.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of LanceDB import operation."""

    success: bool
    table_name: str
    source_path: str
    record_count: int
    import_time_seconds: float
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "table_name": self.table_name,
            "source_path": self.source_path,
            "record_count": self.record_count,
            "import_time_seconds": self.import_time_seconds,
            "errors": self.errors,
        }


class LanceDBImporter:
    """
    Import JSONL data into LanceDB tables.

    Reads JSONL files exported by ChromaDBExporter and imports them
    into LanceDB tables with proper schema mapping.

    Example usage:
        importer = LanceDBImporter("~/.lancedb")
        result = importer.import_jsonl("data/migration/export.jsonl", "canvas_memories")
    """

    def __init__(self, db_path: str = "~/.lancedb"):
        """
        Initialize LanceDB importer.

        Args:
            db_path: Path to LanceDB database directory
        """
        self.db_path = Path(db_path).expanduser()
        self.db = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize LanceDB connection."""
        try:
            import lancedb

            self.db = lancedb.connect(str(self.db_path))
            logger.info(f"Connected to LanceDB at {self.db_path}")
        except ImportError:
            logger.warning("lancedb not installed, using mock mode")
            self.db = None
        except Exception as e:
            logger.error(f"Failed to connect to LanceDB: {e}")
            self.db = None

    def list_tables(self) -> List[str]:
        """List all tables in LanceDB."""
        if self.db is None:
            return []

        try:
            return self.db.table_names()
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []

    def import_jsonl(
        self,
        jsonl_path: str,
        table_name: str,
        batch_size: int = 1000,
        overwrite: bool = False
    ) -> ImportResult:
        """
        Import JSONL file into LanceDB table.

        Args:
            jsonl_path: Path to JSONL file to import
            table_name: Name of target LanceDB table
            batch_size: Number of records to import per batch
            overwrite: Whether to overwrite existing table

        Returns:
            ImportResult with import statistics
        """
        import time
        start_time = time.time()
        errors: List[str] = []
        record_count = 0

        source_path = Path(jsonl_path)

        if not source_path.exists():
            return ImportResult(
                success=False,
                table_name=table_name,
                source_path=str(source_path),
                record_count=0,
                import_time_seconds=0,
                errors=[f"Source file not found: {source_path}"],
            )

        try:
            if self.db is None:
                raise ValueError("LanceDB not initialized")

            # Read JSONL and prepare data
            records = []
            with open(source_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        # Map ChromaDB format to LanceDB format
                        lancedb_record = self._map_record(record)
                        if lancedb_record:
                            records.append(lancedb_record)
                            record_count += 1

            if not records:
                return ImportResult(
                    success=False,
                    table_name=table_name,
                    source_path=str(source_path),
                    record_count=0,
                    import_time_seconds=time.time() - start_time,
                    errors=["No valid records found in JSONL file"],
                )

            # Import to LanceDB
            # ✅ Verified from Context7 - create_table with data
            mode = "overwrite" if overwrite else "create"

            # Check if table exists
            existing_tables = self.list_tables()
            if table_name in existing_tables:
                if overwrite:
                    # Drop and recreate
                    self.db.drop_table(table_name)
                    table = self.db.create_table(table_name, data=records)
                else:
                    # Add to existing table
                    table = self.db.open_table(table_name)
                    # ✅ Verified from Context7 - table.add() for appending
                    table.add(records)
            else:
                # Create new table
                table = self.db.create_table(table_name, data=records)

            logger.info(f"Imported {record_count} records to {table_name}")

        except Exception as e:
            error_msg = f"Import failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            return ImportResult(
                success=False,
                table_name=table_name,
                source_path=str(source_path),
                record_count=0,
                import_time_seconds=time.time() - start_time,
                errors=errors,
            )

        return ImportResult(
            success=True,
            table_name=table_name,
            source_path=str(source_path),
            record_count=record_count,
            import_time_seconds=time.time() - start_time,
            errors=errors,
        )

    def _map_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map ChromaDB record format to LanceDB format.

        ChromaDB format:
            {"id": str, "content": str, "metadata": dict, "embedding": list}

        LanceDB format:
            {"id": str, "text": str, "vector": list, **metadata_fields}
        """
        try:
            doc_id = record.get("id")
            content = record.get("content", "")
            metadata = record.get("metadata", {}) or {}
            embedding = record.get("embedding")

            if not doc_id:
                return None

            # Build LanceDB record
            lancedb_record = {
                "id": doc_id,
                "text": content or "",
                "vector": embedding,
            }

            # Flatten metadata into record
            for key, value in metadata.items():
                # Avoid overwriting core fields
                if key not in ("id", "text", "vector"):
                    lancedb_record[key] = value

            return lancedb_record

        except Exception as e:
            logger.warning(f"Failed to map record: {e}")
            return None

    def import_multiple(
        self,
        jsonl_paths: List[str],
        table_prefix: str = ""
    ) -> Dict[str, ImportResult]:
        """
        Import multiple JSONL files into separate tables.

        Args:
            jsonl_paths: List of JSONL file paths
            table_prefix: Prefix for table names

        Returns:
            Dict mapping file paths to ImportResults
        """
        results = {}
        for jsonl_path in jsonl_paths:
            # Derive table name from filename
            filename = Path(jsonl_path).stem
            # Remove chromadb_export_ prefix if present
            table_name = filename.replace("chromadb_export_", "")
            # Remove timestamp suffix (last 15 chars: _YYYYMMDD_HHMMSS)
            if len(table_name) > 15 and table_name[-16] == "_":
                table_name = table_name[:-16]

            if table_prefix:
                table_name = f"{table_prefix}_{table_name}"

            logger.info(f"Importing {jsonl_path} to table {table_name}")
            results[jsonl_path] = self.import_jsonl(jsonl_path, table_name)

        return results


def import_jsonl_to_lancedb(
    jsonl_path: str,
    table_name: str,
    db_path: str = "~/.lancedb",
    overwrite: bool = False
) -> ImportResult:
    """
    Convenience function to import JSONL file to LanceDB.

    Args:
        jsonl_path: Path to JSONL file
        table_name: Target table name
        db_path: LanceDB database path
        overwrite: Whether to overwrite existing table

    Returns:
        ImportResult with import statistics
    """
    importer = LanceDBImporter(db_path)
    return importer.import_jsonl(jsonl_path, table_name, overwrite=overwrite)
