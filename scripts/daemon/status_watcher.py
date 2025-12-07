"""
Status Watcher - Monitors .worktree-status.yaml files for changes.

Uses the watchdog library to efficiently detect file modifications
and trigger callbacks when dev-complete status is detected.
"""

import time
import threading
from pathlib import Path
from typing import Callable, Dict, List, Set, Optional

try:
    import yaml
except ImportError:
    yaml = None

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
except ImportError:
    Observer = None
    FileSystemEventHandler = object
    FileModifiedEvent = None
    FileCreatedEvent = None


class WorktreeStatusHandler(FileSystemEventHandler):
    """
    Handles file modification events for .worktree-status.yaml files.

    When a status file changes to 'dev-complete', triggers the on_dev_complete callback.
    """

    def __init__(
        self,
        status_files: Dict[str, Path],  # story_id -> status_file_path
        on_dev_complete: Callable[[str, Path], None],
        debounce_seconds: float = 2.0
    ):
        """
        Initialize the handler.

        Args:
            status_files: Mapping of story_id to status file path
            on_dev_complete: Callback when dev-complete detected (story_id, worktree_path)
            debounce_seconds: Minimum time between triggers for same story
        """
        super().__init__()
        self.status_files = status_files
        self.on_dev_complete = on_dev_complete
        self.debounce_seconds = debounce_seconds

        # Track state
        self._last_event_time: Dict[str, float] = {}
        self._already_triggered: Set[str] = set()
        self._lock = threading.Lock()

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        self._handle_event(event.src_path)

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        self._handle_event(event.src_path)

    def _handle_event(self, src_path: str):
        """Process a file event."""
        modified_path = Path(src_path)

        # Only process .worktree-status.yaml files
        if modified_path.name != '.worktree-status.yaml':
            return

        story_id = self._find_story_for_path(modified_path)
        if story_id is None:
            return

        # Debounce rapid modifications
        with self._lock:
            now = time.time()
            last_time = self._last_event_time.get(story_id, 0)

            if now - last_time < self.debounce_seconds:
                return

            self._last_event_time[story_id] = now

        self._check_for_dev_complete(story_id, modified_path)

    def _find_story_for_path(self, path: Path) -> Optional[str]:
        """Find the story ID for a given status file path."""
        path_str = str(path.resolve())

        for story_id, status_path in self.status_files.items():
            if str(status_path.resolve()) == path_str:
                return story_id

        # Fallback: extract from path
        # Path format: .../Canvas-develop-13.1/.worktree-status.yaml
        parent_name = path.parent.name
        if 'develop-' in parent_name:
            parts = parent_name.split('-')
            return parts[-1] if parts else None

        return None

    def _check_for_dev_complete(self, story_id: str, status_path: Path):
        """Check if status is dev-complete and trigger callback."""
        try:
            status = self._read_status_file(status_path)

            if status.get('status') == 'dev-complete':
                with self._lock:
                    if story_id in self._already_triggered:
                        return  # Already triggered, skip
                    self._already_triggered.add(story_id)

                # Get worktree path (parent of status file)
                worktree_path = status_path.parent

                # Trigger callback
                print(f"[StatusWatcher] dev-complete detected for Story {story_id}")
                self.on_dev_complete(story_id, worktree_path)

        except Exception as e:
            print(f"[StatusWatcher] Error reading status file {status_path}: {e}")

    def _read_status_file(self, path: Path) -> dict:
        """Read and parse a YAML status file."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Use yaml library if available
        if yaml:
            return yaml.safe_load(content) or {}

        # Simple fallback parser
        result = {}
        for line in content.split('\n'):
            if ':' in line and not line.strip().startswith('#'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                result[key] = value

        return result

    def reset_trigger(self, story_id: str):
        """Reset the trigger state for a story (allows re-triggering)."""
        with self._lock:
            self._already_triggered.discard(story_id)
            self._last_event_time.pop(story_id, None)


class StatusWatcher:
    """
    Watches multiple worktree status files for changes.

    Uses watchdog Observer to monitor filesystem events efficiently.
    """

    def __init__(self, on_dev_complete: Callable[[str, Path], None]):
        """
        Initialize the watcher.

        Args:
            on_dev_complete: Callback when dev-complete detected (story_id, worktree_path)
        """
        self.on_dev_complete = on_dev_complete
        self._observer: Optional[Observer] = None
        self._handler: Optional[WorktreeStatusHandler] = None
        self._watched_paths: Set[str] = set()

    def watch_worktrees(self, worktrees: List) -> bool:
        """
        Start watching the given worktrees.

        Args:
            worktrees: List of WorktreeInfo objects

        Returns:
            True if watching started successfully
        """
        if Observer is None:
            print("[StatusWatcher] watchdog library not available")
            return False

        # Build status file mapping
        status_files = {}
        for wt in worktrees:
            if hasattr(wt, 'story_id') and hasattr(wt, 'status_file'):
                status_files[wt.story_id] = wt.status_file

        if not status_files:
            print("[StatusWatcher] No status files to watch")
            return False

        # Create handler
        self._handler = WorktreeStatusHandler(
            status_files=status_files,
            on_dev_complete=self.on_dev_complete
        )

        # Create and start observer
        self._observer = Observer()

        # Watch each worktree directory
        for wt in worktrees:
            if hasattr(wt, 'path'):
                path_str = str(wt.path)
                if path_str not in self._watched_paths:
                    try:
                        self._observer.schedule(self._handler, path_str, recursive=False)
                        self._watched_paths.add(path_str)
                        print(f"[StatusWatcher] Watching: {path_str}")
                    except Exception as e:
                        print(f"[StatusWatcher] Failed to watch {path_str}: {e}")

        try:
            self._observer.start()
            print(f"[StatusWatcher] Started watching {len(self._watched_paths)} worktrees")
            return True
        except Exception as e:
            print(f"[StatusWatcher] Failed to start observer: {e}")
            return False

    def stop(self):
        """Stop watching."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            self._watched_paths.clear()
            print("[StatusWatcher] Stopped")

    def is_watching(self) -> bool:
        """Check if watcher is active."""
        return self._observer is not None and self._observer.is_alive()


if __name__ == "__main__":
    # Quick test
    import sys

    def on_complete(story_id: str, path: Path):
        print(f"CALLBACK: Story {story_id} is dev-complete at {path}")

    # Simple test without full worktree setup
    print("StatusWatcher module loaded successfully")

    if Observer is None:
        print("WARNING: watchdog library not installed")
        print("Install with: pip install watchdog")
    else:
        print("watchdog library available")

    if yaml is None:
        print("WARNING: pyyaml library not installed (will use fallback parser)")
    else:
        print("pyyaml library available")
