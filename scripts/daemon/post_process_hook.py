#!/usr/bin/env python3
"""
Post Process Hook - Orchestrator for Dev-QA auto-record pipeline.

Coordinates Story file updates and QA Gate generation after development completion.
Can be called from both linear daemon and parallel workflow.

Usage:
    # As module
    from post_process_hook import PostProcessHook
    hook = PostProcessHook(base_path)
    result = hook.process(story_id, worktree_path, session_id)

    # As CLI
    python post_process_hook.py --story-id 12.5 --worktree-path /path/to/worktree
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from story_file_updater import StoryFileUpdater, UpdateResult
from qa_gate_generator import QAGateGenerator, GateResult


@dataclass
class PostProcessResult:
    """Result of the complete post-processing operation."""
    story_id: str
    session_id: str
    story_updated: bool
    gate_generated: bool
    story_file: Optional[str] = None
    gate_file: Optional[str] = None
    dev_record_complete: bool = False
    qa_record_complete: bool = False
    errors: list = None
    timestamp: str = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def is_success(self) -> bool:
        """Check if all operations completed successfully."""
        return self.story_updated and self.gate_generated and not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PostProcessHook:
    """
    Post-processing orchestrator for Dev-QA auto-record pipeline.

    Workflow:
    1. Read .worktree-result.json
    2. Call StoryFileUpdater to update Story.md
    3. Call QAGateGenerator to create QA Gate YAML
    4. Sync files to main repository
    5. Return combined result
    """

    RESULT_FILE = ".worktree-result.json"
    QA_GATES_DIR = "docs/qa/gates"
    STORIES_DIR = "docs/stories"

    def __init__(self, base_path: Path):
        """
        Initialize the post-process hook.

        Args:
            base_path: Main repository path (e.g., C:\\Users\\ROG\\托福\\Canvas)
        """
        self.base_path = Path(base_path)
        self.story_updater = StoryFileUpdater()
        self.gate_generator = QAGateGenerator()

    def process(
        self,
        story_id: str,
        worktree_path: Path,
        session_id: str = "auto",
    ) -> PostProcessResult:
        """
        Execute the complete post-processing pipeline.

        Args:
            story_id: Story ID (e.g., "12.5")
            worktree_path: Path to the worktree directory
            session_id: Session identifier for tracking

        Returns:
            PostProcessResult with all operation results
        """
        errors = []
        worktree_path = Path(worktree_path)

        # Step 1: Read .worktree-result.json
        result_data = self._read_result_file(worktree_path)
        if not result_data:
            return PostProcessResult(
                story_id=story_id,
                session_id=session_id,
                story_updated=False,
                gate_generated=False,
                errors=["Failed to read .worktree-result.json"],
            )

        # Extract story title for gate filename
        story_title = result_data.get("story_title", f"Story {story_id}")

        # Step 2: Update Story file
        update_result = self._update_story_file(story_id, result_data, worktree_path)
        if update_result.error:
            errors.append(f"Story update: {update_result.error}")

        # Step 3: Generate QA Gate
        gate_result = self._generate_qa_gate(story_id, story_title, result_data)
        if gate_result.error:
            errors.append(f"Gate generation: {gate_result.error}")

        # Step 4: Update .worktree-result.json with post-process status
        self._update_result_file(
            worktree_path,
            result_data,
            update_result,
            gate_result,
        )

        return PostProcessResult(
            story_id=story_id,
            session_id=session_id,
            story_updated=update_result.dev_record_updated or update_result.qa_results_updated,
            gate_generated=gate_result.success,
            story_file=str(update_result.story_file) if update_result.story_file else None,
            gate_file=str(gate_result.gate_file) if gate_result.gate_file else None,
            dev_record_complete=update_result.dev_record_updated,
            qa_record_complete=update_result.qa_results_updated,
            errors=errors if errors else None,
        )

    def _read_result_file(self, worktree_path: Path) -> Optional[Dict[str, Any]]:
        """
        Read and parse .worktree-result.json.

        Args:
            worktree_path: Worktree directory path

        Returns:
            Parsed JSON data or None if failed
        """
        result_file = worktree_path / self.RESULT_FILE

        if not result_file.exists():
            print(f"[PostProcessHook] Warning: {result_file} not found")
            return None

        try:
            with open(result_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PostProcessHook] Error reading result file: {e}")
            return None

    def _update_story_file(
        self,
        story_id: str,
        result_data: Dict[str, Any],
        worktree_path: Path,
    ) -> UpdateResult:
        """
        Update Story file with Dev Agent Record and QA Results.

        Args:
            story_id: Story ID
            result_data: Parsed result data
            worktree_path: Worktree path

        Returns:
            UpdateResult from StoryFileUpdater
        """
        print(f"[PostProcessHook] Updating Story file for {story_id}...")

        result = self.story_updater.update_story_file(
            story_id=story_id,
            result=result_data,
            worktree_path=worktree_path,
            main_repo_path=self.base_path,
        )

        if result.is_complete():
            print(f"[PostProcessHook] Story file updated: {result.story_file}")
        else:
            print(f"[PostProcessHook] Story update incomplete: {result.error}")

        return result

    def _generate_qa_gate(
        self,
        story_id: str,
        story_title: str,
        result_data: Dict[str, Any],
    ) -> GateResult:
        """
        Generate QA Gate YAML file.

        Args:
            story_id: Story ID
            story_title: Story title for filename
            result_data: Parsed result data

        Returns:
            GateResult from QAGateGenerator
        """
        print(f"[PostProcessHook] Generating QA Gate for {story_id}...")

        output_dir = self.base_path / self.QA_GATES_DIR

        result = self.gate_generator.generate_gate(
            story_id=story_id,
            story_title=story_title,
            result=result_data,
            output_dir=output_dir,
        )

        if result.success:
            print(f"[PostProcessHook] QA Gate generated: {result.gate_file}")
        else:
            print(f"[PostProcessHook] Gate generation failed: {result.error}")

        return result

    def _update_result_file(
        self,
        worktree_path: Path,
        result_data: Dict[str, Any],
        update_result: UpdateResult,
        gate_result: GateResult,
    ):
        """
        Update .worktree-result.json with post-processing status.

        Args:
            worktree_path: Worktree path
            result_data: Original result data
            update_result: Story update result
            gate_result: Gate generation result
        """
        result_file = worktree_path / self.RESULT_FILE

        try:
            # Add post-processing info
            result_data["post_process"] = {
                "completed": True,
                "timestamp": datetime.now().isoformat(),
                "story_file_updated": update_result.is_complete(),
                "qa_gate_file": str(gate_result.gate_file) if gate_result.success else None,
                "dev_record_complete": update_result.dev_record_updated,
                "qa_record_complete": update_result.qa_results_updated,
            }

            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            print(f"[PostProcessHook] Updated {result_file}")

        except Exception as e:
            print(f"[PostProcessHook] Warning: Could not update result file: {e}")


def main():
    """CLI entry point for parallel mode support."""
    parser = argparse.ArgumentParser(
        description="Post-process hook for Dev-QA auto-record pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python post_process_hook.py --story-id 12.5 --worktree-path /path/to/worktree
    python post_process_hook.py --story-id 15.1 --worktree-path . --session-id linear-123
        """,
    )

    parser.add_argument(
        "--story-id",
        type=str,
        required=True,
        help="Story ID (e.g., 12.5)",
    )

    parser.add_argument(
        "--worktree-path",
        type=Path,
        required=True,
        help="Path to worktree directory",
    )

    parser.add_argument(
        "--session-id",
        type=str,
        default="cli",
        help="Session identifier for tracking",
    )

    parser.add_argument(
        "--base-path",
        type=Path,
        default=None,
        help="Main repository path (auto-detected if not specified)",
    )

    args = parser.parse_args()

    # Auto-detect base path from script location
    if args.base_path is None:
        # Script is at: Canvas/scripts/daemon/post_process_hook.py
        script_dir = Path(__file__).resolve().parent
        base_path = script_dir.parent.parent  # Canvas directory
    else:
        base_path = args.base_path

    print(f"[PostProcessHook] Starting post-processing...")
    print(f"[PostProcessHook]   Story: {args.story_id}")
    print(f"[PostProcessHook]   Worktree: {args.worktree_path}")
    print(f"[PostProcessHook]   Base Path: {base_path}")
    print(f"[PostProcessHook]   Session: {args.session_id}")

    # Create and run hook
    hook = PostProcessHook(base_path)
    result = hook.process(
        story_id=args.story_id,
        worktree_path=args.worktree_path,
        session_id=args.session_id,
    )

    # Output result
    print("")
    print("=" * 50)
    print("  POST-PROCESSING RESULT")
    print("=" * 50)
    print(f"  Story ID: {result.story_id}")
    print(f"  Story Updated: {result.story_updated}")
    print(f"  Gate Generated: {result.gate_generated}")
    print(f"  Success: {result.is_success()}")

    if result.errors:
        print(f"  Errors:")
        for error in result.errors:
            print(f"    - {error}")

    if result.story_file:
        print(f"  Story File: {result.story_file}")
    if result.gate_file:
        print(f"  Gate File: {result.gate_file}")

    print("=" * 50)

    # Exit code
    sys.exit(0 if result.is_success() else 1)


if __name__ == "__main__":
    main()
