# ✅ Verified from Story 12.3 - ChromaDB → LanceDB Migration Module
"""
ChromaDB to LanceDB Migration Module

This module provides tools for migrating vector data from ChromaDB to LanceDB
with zero data loss, dual-write support, and rollback capabilities.

Components:
- exporter: Export ChromaDB data to JSONL format
- importer: Import JSONL data into LanceDB
- validator: Validate data consistency between databases
- dual_write_adapter: Dual-write adapter for gradual migration
- rollback: Backup and restore functionality
"""

from .dual_write_adapter import DualWriteAdapter, VectorDatabaseAdapter
from .exporter import ChromaDBExporter, ExportResult
from .importer import ImportResult, LanceDBImporter
from .rollback import BackupResult, RestoreResult, RollbackManager
from .validator import MigrationValidator, ValidationResult

__all__ = [
    # Exporter
    "ChromaDBExporter",
    "ExportResult",
    # Importer
    "LanceDBImporter",
    "ImportResult",
    # Validator
    "MigrationValidator",
    "ValidationResult",
    # Dual Write
    "DualWriteAdapter",
    "VectorDatabaseAdapter",
    # Rollback
    "RollbackManager",
    "BackupResult",
    "RestoreResult",
]
