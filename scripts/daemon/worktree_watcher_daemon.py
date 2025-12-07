#!/usr/bin/env python3
"""
Worktree Watcher Daemon - Auto-trigger QA on dev-complete.

This daemon monitors parallel development worktrees and automatically
spawns QA sessions when dev-complete status is detected.

Usage:
    python worktree_watcher_daemon.py
    python worktree_watcher_daemon.py --base-path "C:\\Users\\ROG\\托福"
    python worktree_watcher_daemon.py --max-concurrent 5
"""

import argparse
import signal
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from daemon.worktree_scanner import WorktreeScanner
from daemon.status_watcher import StatusWatcher
from daemon.qa_spawner import QASessionSpawner


class WorktreeWatcherDaemon:
    """
    Main daemon orchestrating worktree monitoring and QA session spawning.

    This daemon:
    1. Scans for active worktrees periodically
    2. Monitors status files for changes using watchdog
    3. Triggers QA sessions when dev-complete is detected
    4. Manages concurrent QA session limits
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        base_path: Path,
        max_concurrent_qa: int = 3,
        scan_interval: int = 30,
        state_file: Optional[Path] = None
    ):
        """
        Initialize the daemon.

        Args:
            base_path: Parent directory where worktrees are located
            max_concurrent_qa: Maximum concurrent QA sessions
            scan_interval: Seconds between worktree scans
            state_file: Path to persist daemon state
        """
        self.base_path = Path(base_path)
        self.scan_interval = scan_interval
        self.state_file = state_file or (self.base_path / "Canvas" / ".daemon-state.json")

        # Initialize components
        self.scanner = WorktreeScanner(self.base_path)
        self.spawner = QASessionSpawner(max_concurrent=max_concurrent_qa)
        self.watcher: Optional[StatusWatcher] = None

        # Running state
        self._running = False
        self._last_scan_time: Optional[datetime] = None
        self._known_worktrees: set = set()

    def _on_dev_complete(self, story_id: str, worktree_path: Path):
        """Callback when dev-complete status is detected."""
        print("")
        print("=" * 70)
        print(f"DEV-COMPLETE DETECTED")
        print("=" * 70)
        print(f"  Story: {story_id}")
        print(f"  Worktree: {worktree_path}")
        print(f"  Time: {datetime.now().isoformat()}")
        print("=" * 70)
        print("")

        # Update status to qa-reviewing
        self._update_worktree_status(worktree_path, "qa-reviewing")

        # Spawn QA session
        if self.spawner.spawn_qa_session(story_id, worktree_path):
            print(f"[Daemon] QA session triggered for Story {story_id}")
        else:
            print(f"[Daemon] Failed to trigger QA session for Story {story_id}")

        # Save state
        self._save_state()

    def _update_worktree_status(self, worktree_path: Path, new_status: str):
        """Update the status in .worktree-status.yaml."""
        status_file = worktree_path / '.worktree-status.yaml'

        if not status_file.exists():
            return

        try:
            # Read existing content
            with open(status_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Update status line
            updated_lines = []
            for line in lines:
                if line.strip().startswith('status:'):
                    updated_lines.append(f'status: "{new_status}"\n')
                else:
                    updated_lines.append(line)

            # Add qa_started_at if not present
            if new_status == "qa-reviewing":
                updated_lines.append(f'qa_started_at: "{datetime.now().isoformat()}"\n')

            # Write back
            with open(status_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)

            print(f"[Daemon] Updated status to '{new_status}' for {worktree_path.name}")

        except Exception as e:
            print(f"[Daemon] Warning: Could not update status file: {e}")

    def _save_state(self):
        """Save daemon state to file."""
        try:
            state = {
                "version": self.VERSION,
                "timestamp": datetime.now().isoformat(),
                "base_path": str(self.base_path),
                "known_worktrees": list(self._known_worktrees),
                "qa_sessions": self.spawner.get_status_summary()
            }

            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            print(f"[Daemon] Warning: Could not save state: {e}")

    def _check_existing_dev_complete(self, worktrees):
        """Check for existing dev-complete statuses on startup."""
        for wt in worktrees:
            if not wt.has_status_file:
                continue

            try:
                with open(wt.status_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Simple check for dev-complete
                if 'status:' in content and 'dev-complete' in content.lower():
                    # Check if not already being processed
                    session = self.spawner.get_session(wt.story_id)
                    if session is None:
                        print(f"[Daemon] Found existing dev-complete: Story {wt.story_id}")
                        self._on_dev_complete(wt.story_id, wt.path)

            except Exception as e:
                print(f"[Daemon] Error checking {wt.story_id}: {e}")

    def start(self):
        """Start the daemon."""
        print("")
        print("=" * 70)
        print(f"  Worktree Watcher Daemon v{self.VERSION}")
        print("=" * 70)
        print(f"  Base Path: {self.base_path}")
        print(f"  Max Concurrent QA: {self.spawner.max_concurrent}")
        print(f"  Scan Interval: {self.scan_interval}s")
        print(f"  State File: {self.state_file}")
        print("=" * 70)
        print("")

        self._running = True

        # Setup signal handlers
        def signal_handler(sig, frame):
            print("\n[Daemon] Received shutdown signal...")
            self._running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print("[Daemon] Starting worktree monitoring... Press Ctrl+C to stop")
        print("")

        try:
            while self._running:
                self._scan_and_watch()
                self._print_status()

                # Wait for next scan
                for _ in range(self.scan_interval):
                    if not self._running:
                        break
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n[Daemon] Interrupted by user")

        finally:
            self._shutdown()

    def _scan_and_watch(self):
        """Scan for worktrees and setup watchers."""
        self._last_scan_time = datetime.now()

        # Scan for worktrees
        worktrees = self.scanner.scan()
        current_paths = {str(wt.path) for wt in worktrees}

        # Check for new worktrees
        new_worktrees = current_paths - self._known_worktrees
        if new_worktrees:
            print(f"[Daemon] Found {len(new_worktrees)} new worktrees")

        # Update known worktrees
        self._known_worktrees = current_paths

        if not worktrees:
            if self.watcher:
                self.watcher.stop()
                self.watcher = None
            return

        # Setup or update watcher
        if self.watcher:
            self.watcher.stop()

        self.watcher = StatusWatcher(on_dev_complete=self._on_dev_complete)
        if self.watcher.watch_worktrees(worktrees):
            # Check for existing dev-complete
            self._check_existing_dev_complete(worktrees)
        else:
            print("[Daemon] Warning: Could not start file watcher")

    def _print_status(self):
        """Print current status."""
        status = self.spawner.get_status_summary()

        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
              f"Worktrees: {len(self._known_worktrees)} | "
              f"QA Sessions - Running: {status['running']}, "
              f"Pending: {status['pending']}, "
              f"Completed: {status['completed']}, "
              f"Failed: {status['failed']}", end="", flush=True)

    def _shutdown(self):
        """Clean shutdown."""
        print("\n[Daemon] Shutting down...")

        if self.watcher:
            self.watcher.stop()

        self._save_state()
        print("[Daemon] Stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Worktree Watcher Daemon - Auto-trigger QA on dev-complete',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    python worktree_watcher_daemon.py
    python worktree_watcher_daemon.py --base-path "C:\\Users\\ROG\\托福"
    python worktree_watcher_daemon.py --max-concurrent 5 --scan-interval 60
        '''
    )

    parser.add_argument(
        '--base-path',
        type=Path,
        default=Path(r'C:\Users\ROG\托福'),
        help='Base path where worktrees are located'
    )

    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='Maximum concurrent QA sessions (default: 3)'
    )

    parser.add_argument(
        '--scan-interval',
        type=int,
        default=30,
        help='Seconds between worktree scans (default: 30)'
    )

    parser.add_argument(
        '--state-file',
        type=Path,
        default=None,
        help='Path to state file (default: Canvas/.daemon-state.json)'
    )

    args = parser.parse_args()

    # Create and start daemon
    daemon = WorktreeWatcherDaemon(
        base_path=args.base_path,
        max_concurrent_qa=args.max_concurrent,
        scan_interval=args.scan_interval,
        state_file=args.state_file
    )

    daemon.start()


if __name__ == '__main__':
    main()
