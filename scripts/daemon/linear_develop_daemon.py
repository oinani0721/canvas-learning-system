#!/usr/bin/env python3
"""
Linear Development Daemon - 24/7 unattended sequential Story development.

This daemon manages Claude CLI sessions for sequential Story execution,
automatically handling:
- Session lifecycle (start, monitor, restart)
- Compact detection and automatic restart
- Failure retry (1 attempt)
- Progress persistence and crash recovery
- Circuit breaker for infinite loops

Usage:
    python linear_develop_daemon.py --stories 15.1,15.2,15.3
    python linear_develop_daemon.py --stories 15.1,15.2,15.3 --resume
    python linear_develop_daemon.py --stories 15.1,15.2,15.3 --base-path "C:\\path"

Based on worktree_watcher_daemon.py architecture.
"""

import argparse
import signal
import sys
import time
import io
from pathlib import Path
from datetime import datetime
from typing import Optional

# Fix Windows console encoding for Chinese characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from linear_progress import LinearProgress, StoryOutcome, ProgressStatus
from linear_outcome_parser import OutcomeParser, ParsedOutcome
from linear_session_spawner import LinearSessionSpawner
from post_process_hook import PostProcessHook


class LinearDevelopDaemon:
    """
    Main daemon orchestrating sequential Story development.

    Features:
    - 24/7 unattended operation
    - Automatic compact/crash recovery
    - Single retry on failure
    - Progress persistence
    - Circuit breaker protection
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        stories: list,
        base_path: Path,
        max_turns: int = 200,
        resume: bool = False,
        ultrathink: bool = False,
    ):
        """
        Initialize the daemon.

        Args:
            stories: List of Story IDs to process sequentially
            base_path: Parent directory where worktrees are located
            max_turns: Maximum agentic turns per Claude session
            resume: Whether to resume from existing progress file
            ultrathink: Enable UltraThink extended thinking mode
        """
        self.stories = stories
        self.base_path = Path(base_path)
        self.max_turns = max_turns
        self.resume = resume
        self.ultrathink = ultrathink

        # Progress file location
        # If base_path already ends with 'Canvas', use it directly
        if self.base_path.name == "Canvas":
            self.progress_file = self.base_path / "linear-progress.json"
        else:
            self.progress_file = self.base_path / "Canvas" / "linear-progress.json"

        # Initialize components
        self.spawner = LinearSessionSpawner(max_turns=max_turns, ultrathink=ultrathink)
        self.parser = OutcomeParser()
        self.progress: Optional[LinearProgress] = None

        # Post-processing hook for Dev-QA auto-record pipeline
        # Determine Canvas directory (main repo path)
        if self.base_path.name == "Canvas":
            self.canvas_path = self.base_path
        else:
            self.canvas_path = self.base_path / "Canvas"
        self.post_processor = PostProcessHook(self.canvas_path)

        # Running state
        self._running = False
        self._current_process = None

    def _setup_signal_handlers(self):
        """Setup handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            print(f"\n[Daemon] Received signal {sig}, initiating graceful shutdown...")
            self._running = False

            # Try to terminate current process gracefully
            if self._current_process and self._current_process.poll() is None:
                print("[Daemon] Terminating current Claude session...")
                try:
                    self._current_process.terminate()
                    self._current_process.wait(timeout=10)
                except:
                    self._current_process.kill()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _load_or_create_progress(self):
        """Load existing progress or create new."""
        if self.resume and self.progress_file.exists():
            self.progress = LinearProgress.load(self.progress_file)
            if self.progress:
                print(f"[Daemon] Resumed from session: {self.progress.session_id}")
                print(f"[Daemon] Current index: {self.progress.current_index}/{len(self.progress.stories)}")
                self.progress.resume()
                return

        # Create new progress
        self.progress = LinearProgress(stories=self.stories)
        print(f"[Daemon] Created new session: {self.progress.session_id}")

    def _get_worktree_path(self, story_id: str) -> Path:
        """Get worktree path for a Story."""
        return self.base_path / f"Canvas-develop-{story_id}"

    def _validate_worktrees(self) -> bool:
        """Validate all worktrees exist."""
        missing = []
        for story_id in self.stories:
            path = self._get_worktree_path(story_id)
            if not path.exists():
                missing.append(story_id)

        if missing:
            print(f"[Daemon] ERROR: Missing worktrees for Stories: {', '.join(missing)}")
            print("[Daemon] Run '/parallel *init' to create worktrees first.")
            return False

        return True

    def _process_story(self, story_id: str) -> ParsedOutcome:
        """
        Process a single Story (blocking until complete).

        Args:
            story_id: The Story ID to process

        Returns:
            ParsedOutcome with the result
        """
        worktree_path = self._get_worktree_path(story_id)
        start_time = datetime.now()

        print("")
        print("=" * 70)
        print(f"  Processing Story {story_id}")
        print("=" * 70)
        print(f"  Worktree: {worktree_path}")
        print(f"  Time: {start_time.isoformat()}")
        print(f"  Retry: {self.progress.current_story.retry_count if self.progress.current_story else 0}")
        print(f"  Compact restarts: {self.progress.current_story.compact_restarts if self.progress.current_story else 0}")
        print("=" * 70)
        print("")

        # Clean up old result file
        self.spawner.cleanup_result_file(worktree_path)

        # Spawn Claude session
        try:
            self._current_process = self.spawner.spawn(story_id, worktree_path)

            # Update progress with PID
            if self.progress.current_story:
                self.progress.current_story.claude_pid = self._current_process.pid
            self.progress.save(self.progress_file)

        except Exception as e:
            print(f"[Daemon] ERROR: Failed to spawn session: {e}")
            return ParsedOutcome(
                outcome=StoryOutcome.ERROR,
                blocking_reason=str(e),
            )

        # Wait for process to complete (blocking)
        print(f"[Daemon] Waiting for Story {story_id} to complete...")
        return_code = self._current_process.wait()
        self._current_process = None

        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"[Daemon] Story {story_id} process exited with code {return_code}")
        print(f"[Daemon] Duration: {duration:.1f} seconds")

        # Parse outcome
        outcome = self.parser.parse(worktree_path, return_code)
        outcome.duration_seconds = duration

        return outcome

    def _handle_outcome(self, story_id: str, outcome: ParsedOutcome):
        """
        Handle the outcome of a Story execution.

        Decides whether to:
        - Move to next Story (SUCCESS)
        - Retry (BLOCKED, first attempt)
        - Restart (COMPACT/CRASH)
        - Halt (BLOCKED after retry, circuit breaker)
        """
        print(f"[Daemon] Story {story_id} outcome: {outcome.outcome.value}")

        if outcome.outcome.is_success():
            # Success - move to next
            print(f"[Daemon] SUCCESS: Story {story_id} completed!")
            if outcome.commit_sha:
                print(f"[Daemon]   Commit: {outcome.commit_sha}")

            # Execute post-processing for Dev-QA auto-record pipeline
            print(f"[Daemon] Running post-processing for Story {story_id}...")
            worktree_path = self._get_worktree_path(story_id)
            post_result = self.post_processor.process(
                story_id=story_id,
                worktree_path=worktree_path,
                session_id=self.progress.session_id,
            )

            if post_result.is_success():
                print(f"[Daemon]   Story file updated: {post_result.story_updated}")
                print(f"[Daemon]   QA gate generated: {post_result.gate_generated}")
            else:
                print(f"[Daemon]   Post-processing completed with warnings:")
                for error in (post_result.errors or []):
                    print(f"[Daemon]     - {error}")

            self.progress.mark_story_complete(
                story_id,
                outcome.outcome,
                outcome.commit_sha,
                outcome.duration_seconds,
            )

            # Update the just-completed story with post-processing info
            if self.progress.completed_stories:
                completed = self.progress.completed_stories[-1]
                completed.story_file_updated = post_result.story_updated
                completed.qa_gate_file = post_result.gate_file
                completed.dev_record_complete = post_result.dev_record_complete
                completed.qa_record_complete = post_result.qa_record_complete

        elif outcome.outcome.is_restart_needed():
            # Compact or crash - restart (not counted as retry)
            if outcome.outcome == StoryOutcome.COMPACT:
                print(f"[Daemon] COMPACT detected - will restart session")
            else:
                print(f"[Daemon] CRASH detected - will restart session")

            # Check circuit breaker
            if not self.progress.increment_compact_restart():
                print(f"[Daemon] CIRCUIT BREAKER: Too many compact restarts for Story {story_id}")
                self.progress.halt(f"Circuit breaker: {self.progress.max_compact_restarts}+ compact restarts")
            # Otherwise, continue with same story (current_index unchanged)

        elif outcome.outcome.is_blocked():
            # Blocked - check if we should retry
            if self.progress.should_retry():
                print(f"[Daemon] BLOCKED - attempting retry ({self.progress.current_story.retry_count + 1}/{self.progress.max_retries + 1})")
                self.progress.increment_retry()
                # current_index unchanged, will retry same story
            else:
                # Already retried, halt
                print(f"[Daemon] HALT: Story {story_id} blocked after retry")
                reason = outcome.blocking_reason or outcome.outcome.value
                self.progress.halt(f"Story {story_id} blocked: {reason}")

                # Record as completed (failed)
                self.progress.mark_story_complete(
                    story_id,
                    outcome.outcome,
                    None,
                    outcome.duration_seconds,
                )

        else:
            # Unknown or error
            print(f"[Daemon] WARNING: Unexpected outcome {outcome.outcome.value}")
            if outcome.blocking_reason:
                print(f"[Daemon]   Reason: {outcome.blocking_reason}")

            # Treat as crash - restart
            if not self.progress.increment_compact_restart():
                self.progress.halt(f"Too many unknown outcomes for Story {story_id}")

    def _print_summary(self):
        """Print final summary."""
        print("")
        print("=" * 70)
        print("  LINEAR DEVELOPMENT DAEMON - FINAL SUMMARY")
        print("=" * 70)
        print(f"  Session: {self.progress.session_id}")
        print(f"  Status: {self.progress.status}")
        print(f"  Stories processed: {len(self.progress.completed_stories)}/{len(self.progress.stories)}")
        print(f"  Succeeded: {self.progress.statistics.stories_succeeded}")
        print(f"  Failed: {self.progress.statistics.stories_failed}")
        print(f"  Total retries: {self.progress.statistics.total_retries}")
        print(f"  Total compact restarts: {self.progress.statistics.total_compact_restarts}")
        print(f"  Total duration: {self.progress.statistics.total_duration_seconds:.1f} seconds")

        if self.progress.halt_reason:
            print(f"  Halt reason: {self.progress.halt_reason}")

        print("=" * 70)

        # List completed stories
        if self.progress.completed_stories:
            print("\n  Completed Stories:")
            for story in self.progress.completed_stories:
                status = "✓" if story.outcome == "SUCCESS" else "✗"
                print(f"    {status} {story.story_id}: {story.outcome}")
                if story.commit_sha:
                    print(f"      Commit: {story.commit_sha[:7]}")

        print("")

    def start(self):
        """Start the daemon main loop."""
        print("")
        print("=" * 70)
        print(f"  Linear Development Daemon v{self.VERSION}")
        print("=" * 70)
        print(f"  Stories: {', '.join(self.stories)}")
        print(f"  Base Path: {self.base_path}")
        print(f"  Max Turns: {self.max_turns}")
        print(f"  Resume: {self.resume}")
        print(f"  UltraThink: {self.ultrathink}")
        print(f"  Progress File: {self.progress_file}")
        print("=" * 70)
        print("")

        # Validate worktrees
        if not self._validate_worktrees():
            sys.exit(1)

        # Setup signal handlers
        self._setup_signal_handlers()

        # Load or create progress
        self._load_or_create_progress()

        print("[Daemon] Starting main loop... Press Ctrl+C to stop")
        print("")

        self._running = True

        try:
            while self._running:
                # Check if complete
                if self.progress.is_complete():
                    print("[Daemon] All stories completed!")
                    self.progress.status = "completed"
                    break

                # Check if halted
                if self.progress.is_halted():
                    print(f"[Daemon] Execution halted: {self.progress.halt_reason}")
                    break

                # Get current story
                story_id = self.progress.get_current_story_id()
                if not story_id:
                    print("[Daemon] No more stories to process")
                    break

                # Start story if not already started
                if not self.progress.current_story or self.progress.current_story.story_id != story_id:
                    self.progress.start_story(story_id)

                # Save progress before processing
                self.progress.save(self.progress_file)

                # Process story
                outcome = self._process_story(story_id)

                # Handle outcome
                self._handle_outcome(story_id, outcome)

                # Save progress after processing
                self.progress.save(self.progress_file)

                # Small delay before next iteration
                if self._running and not self.progress.is_complete() and not self.progress.is_halted():
                    time.sleep(2)

        except KeyboardInterrupt:
            print("\n[Daemon] Interrupted by user")

        finally:
            # Save final state
            self.progress.save(self.progress_file)

            # Print summary
            self._print_summary()

            # Exit code based on status
            if self.progress.status == "completed" and self.progress.statistics.stories_failed == 0:
                print("[Daemon] Exiting with success (code 0)")
                sys.exit(0)
            else:
                print("[Daemon] Exiting with failure (code 1)")
                sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Linear Development Daemon - 24/7 unattended sequential Story development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    python linear_develop_daemon.py --stories 15.1,15.2,15.3,15.4,15.5,15.6
    python linear_develop_daemon.py --stories 15.1,15.2,15.3 --resume
    python linear_develop_daemon.py --stories 15.1,15.2 --max-turns 150
        '''
    )

    parser.add_argument(
        '--stories',
        type=str,
        required=True,
        help='Comma-separated list of Story IDs (e.g., "15.1,15.2,15.3")'
    )

    # Auto-detect base path from script location
    # Script is at: Canvas/scripts/daemon/linear_develop_daemon.py
    # Base path is: Canvas's parent directory
    script_dir = Path(__file__).resolve().parent
    canvas_dir = script_dir.parent.parent  # Canvas directory
    default_base_path = canvas_dir.parent  # Parent of Canvas (e.g., C:\Users\ROG\托福)

    parser.add_argument(
        '--base-path',
        type=Path,
        default=default_base_path,
        help='Base path where worktrees are located (auto-detected from script location)'
    )

    parser.add_argument(
        '--max-turns',
        type=int,
        default=200,
        help='Maximum agentic turns per session (default: 200)'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from existing progress file'
    )

    parser.add_argument(
        '--ultrathink',
        action='store_true',
        help='Enable UltraThink extended thinking mode for deep analysis'
    )

    args = parser.parse_args()

    # Parse stories
    stories = [s.strip() for s in args.stories.split(',')]

    # Create and start daemon
    daemon = LinearDevelopDaemon(
        stories=stories,
        base_path=args.base_path,
        max_turns=args.max_turns,
        resume=args.resume,
        ultrathink=args.ultrathink,
    )

    daemon.start()


if __name__ == '__main__':
    main()
