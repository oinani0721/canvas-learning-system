# Canvas Learning System - Batch Canvas Writer
# ✅ Verified from Architecture Doc (performance-monitoring-architecture.md:361-380)
# ✅ Verified from ADR-007 (ADR-007-CACHING-STRATEGY-TIERED.md:130-155)
# [Source: docs/stories/17.4.story.md - Task 2]
"""
Canvas batch write optimization with debouncing and atomic writes.

Features:
- Debounced writes (configurable delay, default 500ms)
- Atomic file operations (write to temp, then rename)
- Batch aggregation for multiple rapid changes
- Rollback support via backup files

[Source: docs/architecture/performance-monitoring-architecture.md:361-380]
[Source: docs/architecture/decisions/ADR-007-CACHING-STRATEGY-TIERED.md:130-155]
"""

import asyncio
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

from .canvas_cache import clear_canvas_cache, write_canvas_json

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Batch Writer Configuration
# [Source: docs/architecture/decisions/ADR-007-CACHING-STRATEGY-TIERED.md:130-155]
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class BatchWriterConfig:
    """Batch writer configuration.

    [Source: docs/architecture/decisions/ADR-007-CACHING-STRATEGY-TIERED.md:130-155]
    """

    # Debounce delay in seconds
    debounce_delay: float = 0.5

    # Maximum pending writes before forced flush
    max_pending: int = 10

    # Enable atomic writes (temp file + rename)
    atomic_writes: bool = True

    # Enable backup before write
    create_backup: bool = True

    # Backup retention count
    backup_count: int = 3

    # Enable batch writer
    enabled: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# Pending Write Entry
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class PendingWrite:
    """Represents a pending write operation."""

    canvas_path: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    callback: Optional[Callable[[bool, Optional[Exception]], None]] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Batch Canvas Writer
# [Source: docs/architecture/performance-monitoring-architecture.md:361-380]
# ═══════════════════════════════════════════════════════════════════════════════


class BatchCanvasWriter:
    """Batch Canvas writer with debouncing and atomic writes.

    This class optimizes Canvas file writes by:
    - Debouncing rapid successive writes to the same file
    - Using atomic writes (temp file + rename) for data safety
    - Creating backups before writes for rollback support
    - Aggregating multiple writes into batches

    [Source: docs/architecture/performance-monitoring-architecture.md:361-380]

    Example:
        >>> writer = BatchCanvasWriter()
        >>> await writer.start()
        >>> await writer.write("/path/to/canvas.canvas", {"nodes": [], "edges": []})
        >>> await writer.stop()
    """

    def __init__(self, config: Optional[BatchWriterConfig] = None):
        """Initialize batch writer.

        Args:
            config: Optional configuration, uses defaults if not provided
        """
        self.config = config or BatchWriterConfig()
        self._pending: Dict[str, PendingWrite] = {}
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
        self._stats = {
            "writes": 0,
            "batched": 0,
            "errors": 0,
            "backups_created": 0,
        }

    async def start(self):
        """Start the batch writer background task."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("batch_writer.started")

    async def stop(self):
        """Stop the batch writer and flush pending writes."""
        if not self._running:
            return

        self._running = False

        # Flush remaining writes
        await self._flush_all()

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        logger.info("batch_writer.stopped", stats=self._stats)

    async def write(
        self,
        canvas_path: str,
        data: Dict[str, Any],
        callback: Optional[Callable[[bool, Optional[Exception]], None]] = None,
    ):
        """Queue a Canvas write operation.

        Multiple writes to the same file within the debounce window
        will be batched, with only the latest data being written.

        Args:
            canvas_path: Path to Canvas file
            data: Canvas data dictionary
            callback: Optional callback(success, exception) after write completes
        """
        if not self.config.enabled:
            # Optimization disabled, write immediately
            await self._write_immediate(canvas_path, data, callback)
            return

        async with self._lock:
            # Check if we already have a pending write for this file
            if canvas_path in self._pending:
                self._stats["batched"] += 1
                logger.debug(
                    "batch_writer.batched",
                    path=canvas_path,
                    batched_count=self._stats["batched"],
                )

            # Update or create pending write
            self._pending[canvas_path] = PendingWrite(
                canvas_path=canvas_path,
                data=data,
                callback=callback,
            )

            # Check if we need to force flush
            if len(self._pending) >= self.config.max_pending:
                logger.debug("batch_writer.force_flush", pending=len(self._pending))
                await self._flush_all()

    async def _flush_loop(self):
        """Background loop that flushes pending writes after debounce delay."""
        while self._running:
            await asyncio.sleep(self.config.debounce_delay)
            await self._flush_all()

    async def _flush_all(self):
        """Flush all pending writes."""
        async with self._lock:
            if not self._pending:
                return

            pending_copy = dict(self._pending)
            self._pending.clear()

        # Write all pending files
        for canvas_path, pending in pending_copy.items():
            await self._execute_write(pending)

    async def _execute_write(self, pending: PendingWrite):
        """Execute a single write operation.

        Args:
            pending: Pending write entry
        """
        canvas_path = pending.canvas_path
        data = pending.data
        callback = pending.callback

        try:
            # Create backup if enabled
            if self.config.create_backup and os.path.exists(canvas_path):
                await self._create_backup(canvas_path)

            # Write using atomic or direct method
            if self.config.atomic_writes:
                await self._write_atomic(canvas_path, data)
            else:
                write_canvas_json(canvas_path, data)

            self._stats["writes"] += 1
            logger.debug("batch_writer.write_complete", path=canvas_path)

            if callback:
                callback(True, None)

        except Exception as e:
            self._stats["errors"] += 1
            logger.error("batch_writer.write_error", path=canvas_path, error=str(e))

            if callback:
                callback(False, e)

    async def _write_atomic(self, canvas_path: str, data: Dict[str, Any]):
        """Write to temp file then rename for atomic operation.

        Args:
            canvas_path: Target file path
            data: Canvas data
        """
        # Get directory and create temp file in same directory
        dir_path = os.path.dirname(canvas_path) or "."
        fd, temp_path = tempfile.mkstemp(
            suffix=".canvas.tmp",
            dir=dir_path,
        )

        try:
            # Close the file descriptor (we'll write via write_canvas_json)
            os.close(fd)

            # Write to temp file
            write_canvas_json(temp_path, data)

            # Atomic rename
            shutil.move(temp_path, canvas_path)

            # Clear cache for this file
            clear_canvas_cache()

        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    async def _create_backup(self, canvas_path: str):
        """Create backup of existing Canvas file.

        Args:
            canvas_path: Path to Canvas file
        """
        if not os.path.exists(canvas_path):
            return

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(canvas_path).parent / ".canvas_backups"
        backup_dir.mkdir(exist_ok=True)

        backup_name = f"{Path(canvas_path).stem}_{timestamp}.canvas.bak"
        backup_path = backup_dir / backup_name

        # Copy file to backup
        shutil.copy2(canvas_path, backup_path)
        self._stats["backups_created"] += 1

        # Rotate old backups
        await self._rotate_backups(backup_dir, Path(canvas_path).stem)

        logger.debug("batch_writer.backup_created", backup=str(backup_path))

    async def _rotate_backups(self, backup_dir: Path, stem: str):
        """Remove old backups beyond retention count.

        Args:
            backup_dir: Directory containing backups
            stem: Original file stem to match
        """
        # Find all backups for this file
        pattern = f"{stem}_*.canvas.bak"
        backups = sorted(backup_dir.glob(pattern), reverse=True)

        # Remove excess backups
        for old_backup in backups[self.config.backup_count :]:
            old_backup.unlink()
            logger.debug("batch_writer.backup_rotated", removed=str(old_backup))

    async def _write_immediate(
        self,
        canvas_path: str,
        data: Dict[str, Any],
        callback: Optional[Callable[[bool, Optional[Exception]], None]] = None,
    ):
        """Write immediately without batching (when disabled).

        Args:
            canvas_path: Path to Canvas file
            data: Canvas data
            callback: Optional completion callback
        """
        try:
            write_canvas_json(canvas_path, data)
            self._stats["writes"] += 1
            if callback:
                callback(True, None)
        except Exception as e:
            self._stats["errors"] += 1
            if callback:
                callback(False, e)

    def get_stats(self) -> Dict[str, Any]:
        """Get writer statistics.

        Returns:
            dict: Statistics including writes, batched, errors, backups
        """
        return {
            **self._stats,
            "pending": len(self._pending),
            "config": {
                "debounce_delay": self.config.debounce_delay,
                "max_pending": self.config.max_pending,
                "atomic_writes": self.config.atomic_writes,
                "enabled": self.config.enabled,
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Rollback Support
# ═══════════════════════════════════════════════════════════════════════════════


async def restore_from_backup(canvas_path: str, backup_index: int = 0) -> bool:
    """Restore Canvas file from backup.

    Args:
        canvas_path: Path to Canvas file to restore
        backup_index: Which backup to use (0 = most recent)

    Returns:
        bool: True if restore succeeded, False otherwise
    """
    backup_dir = Path(canvas_path).parent / ".canvas_backups"
    stem = Path(canvas_path).stem
    pattern = f"{stem}_*.canvas.bak"

    backups = sorted(backup_dir.glob(pattern), reverse=True)

    if not backups or backup_index >= len(backups):
        logger.warning("batch_writer.no_backup", path=canvas_path)
        return False

    backup_path = backups[backup_index]

    try:
        shutil.copy2(backup_path, canvas_path)
        clear_canvas_cache()
        logger.info("batch_writer.restored", from_backup=str(backup_path))
        return True
    except Exception as e:
        logger.error("batch_writer.restore_error", error=str(e))
        return False


def list_backups(canvas_path: str) -> List[Dict[str, Any]]:
    """List available backups for a Canvas file.

    Args:
        canvas_path: Path to Canvas file

    Returns:
        list: List of backup info dicts with path and timestamp
    """
    backup_dir = Path(canvas_path).parent / ".canvas_backups"
    stem = Path(canvas_path).stem
    pattern = f"{stem}_*.canvas.bak"

    if not backup_dir.exists():
        return []

    backups = []
    for backup_path in sorted(backup_dir.glob(pattern), reverse=True):
        stat = backup_path.stat()
        backups.append({
            "path": str(backup_path),
            "name": backup_path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })

    return backups
