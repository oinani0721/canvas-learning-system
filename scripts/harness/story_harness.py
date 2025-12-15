"""
Story Harness - Anthropic-style long-running agent harness for BMad workflow.

Based on Anthropic's official harness pattern:
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

Usage:
    # Mock mode (no Claude API calls)
    python -m scripts.harness.story_harness --epic 24 --stories "24.1,24.2" --mock

    # Real mode
    python -m scripts.harness.story_harness --epic 24 --stories "24.1,24.2"

    # Resume interrupted session
    python -m scripts.harness.story_harness --epic 24 --resume
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.harness.harness_progress import HarnessProgress, StoryProgress, GateResult
from scripts.daemon.linear_session_spawner import LinearSessionSpawner


class StoryHarness:
    """
    Anthropic-style harness for sequential Story development.

    Implements the "Coding Agent Loop" pattern:
    1. Read progress file
    2. Get next pending story
    3. Run Dev+QA session (via LinearSessionSpawner)
    4. Run simplified CommitGate (G3+G4)
    5. Update progress
    6. Git commit (if gate passed)
    7. Repeat
    """

    # Default cooldown between stories (seconds)
    DEFAULT_COOLDOWN = 30

    def __init__(
        self,
        epic_id: str,
        stories: List[str],
        mock_mode: bool = False,
        worktree_path: Optional[Path] = None,
    ):
        """
        Initialize the story harness.

        Args:
            epic_id: The Epic ID (e.g., "24")
            stories: List of Story IDs to process (e.g., ["24.1", "24.2"])
            mock_mode: If True, simulate without Claude API calls
            worktree_path: Path to worktree (default: current directory)
        """
        self.epic_id = epic_id
        self.stories = stories
        self.mock_mode = mock_mode
        self.worktree_path = worktree_path or Path.cwd()

        # Load or create progress
        self.progress = HarnessProgress.load_or_create(epic_id, stories)

        # Initialize session spawner (reuse existing infrastructure)
        self.spawner = LinearSessionSpawner(max_turns=200, ultrathink=True)

        # Track failed stories for retry decisions
        self._failed_stories: Dict[str, int] = {}

    def run(self):
        """
        Main 24/7 loop.

        Processes stories sequentially, handling failures gracefully.
        """
        print(f"\n{'=' * 60}")
        print(f"[StoryHarness] Starting Epic {self.epic_id}")
        print(f"{'=' * 60}")
        print(f"Stories: {self.stories}")
        print(f"Mock Mode: {self.mock_mode}")
        print(f"Worktree: {self.worktree_path}")
        print(f"Session ID: {self.progress.session_id}")
        print(f"{'=' * 60}\n")

        # Save initial state
        self.progress.save()

        while not self.progress.is_complete():
            story = self.progress.get_next_pending()
            if not story:
                break

            print(f"\n{'=' * 60}")
            print(f"[StoryHarness] Processing Story {story.id}")
            print(f"{'=' * 60}")

            start_time = time.time()

            # Step 1: Mark as in progress
            self.progress.start_story(story.id)
            self.progress.save()

            # Step 2: Run Dev+QA session
            if self.mock_mode:
                result = self._mock_session(story.id)
            else:
                result = self._run_session(story.id)

            duration = time.time() - start_time

            # Step 3: Run CommitGate (simplified G3+G4)
            gate_result = self._run_gate(story.id, result)

            print(f"[StoryHarness] Gate Result: {'PASS' if gate_result.passed else 'FAIL'}")
            print(f"[StoryHarness]   G3 (Tests): {'[PASS]' if gate_result.g3_tests else '[FAIL]'}")
            print(f"[StoryHarness]   G4 (QA): {'[PASS]' if gate_result.g4_qa else '[FAIL]'}")

            # Step 4: Update progress and commit
            if gate_result.passed:
                commit_sha = self._git_commit(story.id, result)
                self.progress.mark_completed(story.id, commit_sha, gate_result, duration)
                print(f"[StoryHarness] [OK] Story {story.id} completed (commit: {commit_sha})")
            else:
                # Check if should retry
                if self.progress.should_retry(story.id):
                    print(f"[StoryHarness] [!] Story {story.id} failed, will retry")
                    self.progress.increment_retry(story.id)
                else:
                    self.progress.mark_failed(
                        story.id,
                        gate_result,
                        error_message=result.get("blocking_reason", "Gate failed")
                    )
                    print(f"[StoryHarness] [X] Story {story.id} failed after max retries, halting")
                    self.progress.halt(f"Story {story.id} failed after max retries")
                    break

            # Step 5: Save progress
            self.progress.save()

            # Step 6: Cooldown before next story
            if not self.progress.is_complete():
                print(f"[StoryHarness] Cooling down for {self.DEFAULT_COOLDOWN}s...")
                time.sleep(self.DEFAULT_COOLDOWN)

        self._print_summary()

    def _mock_session(self, story_id: str) -> Dict[str, Any]:
        """
        Mock a Dev+QA session (for testing without API calls).

        Args:
            story_id: The Story ID

        Returns:
            Mock result dictionary
        """
        print(f"[StoryHarness] Running MOCK session for Story {story_id}")
        time.sleep(2)  # Simulate work

        # Default to success, can be overridden by --fail-story flag
        return {
            "story_id": story_id,
            "outcome": "SUCCESS",
            "tests_passed": True,
            "test_count": 10,
            "test_coverage": 85.0,
            "qa_gate": "PASS",
            "commit_sha": f"mock-sha-{story_id}",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": 2.0,
        }

    def _run_session(self, story_id: str) -> Dict[str, Any]:
        """
        Run a real Dev+QA session via Claude CLI.

        Args:
            story_id: The Story ID

        Returns:
            Result dictionary from .worktree-result.json
        """
        print(f"[StoryHarness] Spawning Claude session for Story {story_id}")

        # Clean up previous result file
        self.spawner.cleanup_result_file(self.worktree_path)

        # Spawn Claude session
        process = self.spawner.spawn(
            story_id=story_id,
            worktree_path=self.worktree_path,
        )

        # Wait for completion
        print(f"[StoryHarness] Waiting for Claude session (PID: {process.pid})...")
        return_code = process.wait()

        print(f"[StoryHarness] Claude session exited with code: {return_code}")

        # Read result file
        result_file = self.worktree_path / ".worktree-result.json"
        if result_file.exists():
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[StoryHarness] Error reading result file: {e}")

        # Default result if no file found
        return {
            "story_id": story_id,
            "outcome": "ERROR",
            "tests_passed": False,
            "qa_gate": None,
            "blocking_reason": "No result file generated",
        }

    def _run_gate(self, story_id: str, result: Dict[str, Any]) -> GateResult:
        """
        Run simplified CommitGate (G3+G4 only).

        G3: Tests passed
        G4: QA Gate passed

        Args:
            story_id: The Story ID
            result: Result from session

        Returns:
            GateResult with pass/fail status
        """
        g3_passed = result.get("tests_passed", False)
        g4_passed = result.get("qa_gate") in ("PASS", "WAIVED")

        return GateResult(
            passed=g3_passed and g4_passed,
            g3_tests=g3_passed,
            g4_qa=g4_passed,
            details=result,
        )

    def _git_commit(self, story_id: str, result: Dict[str, Any]) -> str:
        """
        Create git commit for completed story.

        Args:
            story_id: The Story ID
            result: Result from session

        Returns:
            Commit SHA (or mock SHA in mock mode)
        """
        if self.mock_mode:
            return result.get("commit_sha", f"mock-{story_id}")

        # In real mode, Claude session should have already committed
        # Just return the SHA from result
        return result.get("commit_sha", "no-commit")

    def _print_summary(self):
        """Print final execution summary."""
        summary = self.progress.get_summary()

        print(f"\n{'=' * 60}")
        print(f"[StoryHarness] Execution Summary")
        print(f"{'=' * 60}")
        print(f"Epic: {summary['epic_id']}")
        print(f"Status: {summary['status']}")
        print(f"Total Stories: {summary['total']}")
        print(f"  [OK] Completed: {summary['completed']}")
        print(f"  [X]  Failed: {summary['failed']}")
        print(f"  [.] Pending: {summary['pending']}")
        print(f"Gate Results:")
        print(f"  Passes: {summary['gate_passes']}")
        print(f"  Failures: {summary['gate_failures']}")
        print(f"Total Duration: {summary['total_duration_seconds']:.1f}s")
        print(f"Restarts: {summary['restarts']}")
        print(f"{'=' * 60}")

        # List story details
        print("\nStory Details:")
        for story in self.progress.stories:
            status_icon = {
                "completed": "[OK]",
                "failed": "[X]",
                "pending": "[.]",
                "in_progress": "[>]",
            }.get(story.status, "[?]")
            commit = f" (commit: {story.commit_sha})" if story.commit_sha else ""
            print(f"  {status_icon} {story.id}: {story.status}{commit}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Story Harness - Anthropic-style long-running agent for BMad workflow"
    )
    parser.add_argument(
        "--epic",
        required=True,
        help="Epic ID (e.g., '24')"
    )
    parser.add_argument(
        "--stories",
        help="Comma-separated Story IDs (e.g., '24.1,24.2,24.3')"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode (no Claude API calls)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing progress file"
    )
    parser.add_argument(
        "--worktree",
        type=Path,
        help="Path to worktree (default: current directory)"
    )

    args = parser.parse_args()

    # Parse stories
    if args.resume:
        # Load existing progress to get stories
        existing = HarnessProgress.load(args.epic)
        if not existing:
            print(f"[StoryHarness] Error: No existing progress file for Epic {args.epic}")
            sys.exit(1)
        stories = [s.id for s in existing.stories]
        print(f"[StoryHarness] Resuming Epic {args.epic} with stories: {stories}")
    elif args.stories:
        stories = [s.strip() for s in args.stories.split(",")]
    else:
        print("[StoryHarness] Error: --stories required (or use --resume)")
        sys.exit(1)

    # Create and run harness
    harness = StoryHarness(
        epic_id=args.epic,
        stories=stories,
        mock_mode=args.mock,
        worktree_path=args.worktree,
    )

    try:
        harness.run()
    except KeyboardInterrupt:
        print("\n[StoryHarness] Interrupted by user")
        harness.progress.halt("User interrupted")
        harness.progress.save()
        harness._print_summary()
        sys.exit(130)


if __name__ == "__main__":
    main()
