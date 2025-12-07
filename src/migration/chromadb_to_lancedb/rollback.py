# ✅ Verified from Story 12.3 AC 3.5 - Rollback Plan
"""
Rollback Manager Module

Provides backup and restore functionality for ChromaDB data.
Supports rollback in case of migration failure.
"""

import logging
import shutil
import tarfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    """Result of backup operation."""

    success: bool
    backup_path: str
    source_path: str
    file_size_bytes: int
    backup_time_seconds: float
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "backup_path": self.backup_path,
            "source_path": self.source_path,
            "file_size_bytes": self.file_size_bytes,
            "backup_time_seconds": self.backup_time_seconds,
            "errors": self.errors,
        }


@dataclass
class RestoreResult:
    """Result of restore operation."""

    success: bool
    restore_path: str
    backup_path: str
    restore_time_seconds: float
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "restore_path": self.restore_path,
            "backup_path": self.backup_path,
            "restore_time_seconds": self.restore_time_seconds,
            "errors": self.errors,
        }


class RollbackManager:
    """
    Manage backup and rollback for ChromaDB migration.

    Provides:
    - Backup ChromaDB data to tar.gz archive
    - Restore ChromaDB from backup
    - List available backups
    - Cleanup old backups

    Example usage:
        manager = RollbackManager("data/backups")
        backup_result = manager.backup_chromadb("data/memory_db")
        # ... migration ...
        if migration_failed:
            restore_result = manager.restore_chromadb(backup_result.backup_path)
    """

    def __init__(self, backup_dir: str = "data/backups"):
        """
        Initialize rollback manager.

        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_chromadb(
        self,
        chromadb_path: str,
        backup_name: Optional[str] = None
    ) -> BackupResult:
        """
        Backup ChromaDB data directory to tar.gz archive.

        Args:
            chromadb_path: Path to ChromaDB data directory
            backup_name: Optional custom backup name

        Returns:
            BackupResult with backup statistics
        """
        import time
        start_time = time.time()
        errors: List[str] = []

        source_path = Path(chromadb_path)

        if not source_path.exists():
            return BackupResult(
                success=False,
                backup_path="",
                source_path=str(source_path),
                file_size_bytes=0,
                backup_time_seconds=0,
                errors=[f"Source path does not exist: {source_path}"],
            )

        # Generate backup filename
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"chromadb_backup_{timestamp}"

        backup_path = self.backup_dir / f"{backup_name}.tar.gz"

        try:
            # Create tar.gz archive
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(source_path, arcname=source_path.name)

            file_size = backup_path.stat().st_size
            logger.info(f"Created backup: {backup_path} ({file_size} bytes)")

        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            return BackupResult(
                success=False,
                backup_path=str(backup_path),
                source_path=str(source_path),
                file_size_bytes=0,
                backup_time_seconds=time.time() - start_time,
                errors=errors,
            )

        return BackupResult(
            success=True,
            backup_path=str(backup_path),
            source_path=str(source_path),
            file_size_bytes=file_size,
            backup_time_seconds=time.time() - start_time,
            errors=errors,
        )

    def restore_chromadb(
        self,
        backup_path: str,
        restore_path: Optional[str] = None
    ) -> RestoreResult:
        """
        Restore ChromaDB from backup archive.

        Args:
            backup_path: Path to backup tar.gz file
            restore_path: Optional custom restore path (default: original location)

        Returns:
            RestoreResult with restore statistics
        """
        import time
        start_time = time.time()
        errors: List[str] = []

        backup_file = Path(backup_path)

        if not backup_file.exists():
            return RestoreResult(
                success=False,
                restore_path="",
                backup_path=str(backup_file),
                restore_time_seconds=0,
                errors=[f"Backup file not found: {backup_file}"],
            )

        try:
            # Extract to temporary location first
            temp_extract = self.backup_dir / "temp_restore"
            if temp_extract.exists():
                shutil.rmtree(temp_extract)
            temp_extract.mkdir(parents=True)

            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(temp_extract)

            # Get the extracted directory name
            extracted_items = list(temp_extract.iterdir())
            if not extracted_items:
                raise ValueError("Backup archive is empty")

            extracted_dir = extracted_items[0]

            # Determine restore location
            if restore_path is None:
                # Default: restore to parent of backup dir
                restore_path = str(self.backup_dir.parent / extracted_dir.name)

            target_path = Path(restore_path)

            # Backup existing data if present
            if target_path.exists():
                existing_backup = target_path.with_suffix(".pre_restore_backup")
                if existing_backup.exists():
                    shutil.rmtree(existing_backup)
                shutil.move(str(target_path), str(existing_backup))
                logger.info(f"Moved existing data to: {existing_backup}")

            # Move extracted data to target
            shutil.move(str(extracted_dir), str(target_path))

            # Cleanup temp directory
            shutil.rmtree(temp_extract)

            logger.info(f"Restored to: {target_path}")

        except Exception as e:
            error_msg = f"Restore failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            return RestoreResult(
                success=False,
                restore_path=restore_path or "",
                backup_path=str(backup_file),
                restore_time_seconds=time.time() - start_time,
                errors=errors,
            )

        return RestoreResult(
            success=True,
            restore_path=str(target_path),
            backup_path=str(backup_file),
            restore_time_seconds=time.time() - start_time,
            errors=errors,
        )

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.

        Returns:
            List of backup info dicts
        """
        backups = []

        for backup_file in sorted(self.backup_dir.glob("chromadb_backup_*.tar.gz"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "path": str(backup_file),
                "name": backup_file.stem,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        return backups

    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """
        Remove old backups, keeping the most recent ones.

        Args:
            keep_count: Number of recent backups to keep

        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        deleted_count = 0

        if len(backups) <= keep_count:
            return 0

        # Delete older backups (list is already sorted newest first)
        for backup in backups[keep_count:]:
            try:
                Path(backup["path"]).unlink()
                deleted_count += 1
                logger.info(f"Deleted old backup: {backup['path']}")
            except Exception as e:
                logger.error(f"Failed to delete backup {backup['path']}: {e}")

        return deleted_count

    def verify_backup(self, backup_path: str) -> bool:
        """
        Verify backup archive integrity.

        Args:
            backup_path: Path to backup tar.gz file

        Returns:
            True if backup is valid
        """
        backup_file = Path(backup_path)

        if not backup_file.exists():
            return False

        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                # Check if archive can be read
                members = tar.getmembers()
                if not members:
                    return False
                # Verify first few files can be extracted
                for member in members[:5]:
                    tar.getmember(member.name)
            return True
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False


def backup_chromadb(backup_path: str) -> BackupResult:
    """
    Convenience function to backup ChromaDB.

    Args:
        backup_path: Path to ChromaDB data directory

    Returns:
        BackupResult with backup statistics
    """
    manager = RollbackManager()
    return manager.backup_chromadb(backup_path)


def restore_chromadb(backup_path: str) -> RestoreResult:
    """
    Convenience function to restore ChromaDB.

    Args:
        backup_path: Path to backup tar.gz file

    Returns:
        RestoreResult with restore statistics
    """
    manager = RollbackManager()
    return manager.restore_chromadb(backup_path)
