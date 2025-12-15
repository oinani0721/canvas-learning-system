#!/usr/bin/env python3
"""
BMad Workflow Gate Pre-commit Hook

Validates that Story files follow the complete BMad workflow before commit:
- SM Draft → PO Approve → DEV Develop → QA Review → Merge → Commit

⚠️ IMPORTANT:
- Epic 1-20: Skipped (legacy data)
- Epic 21+: MUST pass all workflow phases

Usage (as pre-commit hook):
    python scripts/validate-workflow-gate.py

Exit codes:
    0: All validations passed
    1: Validation failed, commit blocked

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-11
"""

import re
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from bmad_orchestrator.workflow_enforcer import (
    WorkflowEnforcer,
    ValidationResult,
)


# ============================================================================
# Constants
# ============================================================================

# ANSI colors for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


# ============================================================================
# Helper Functions
# ============================================================================


def get_staged_files() -> list[str]:
    """Get list of staged files using git diff --cached"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def extract_story_id(file_path: str) -> str | None:
    """
    Extract story ID from file path.

    Examples:
        docs/stories/21.1.story.md → "21.1"
        docs/stories/story-21.1.md → "21.1"
    """
    filename = Path(file_path).stem

    # Pattern 1: 21.1.story → 21.1
    match = re.match(r"^(\d+\.\d+)\.story$", filename)
    if match:
        return match.group(1)

    # Pattern 2: story-21.1 → 21.1
    match = re.match(r"^story-(\d+\.\d+)$", filename)
    if match:
        return match.group(1)

    # Pattern 3: Story-21.1 → 21.1
    match = re.match(r"^Story-(\d+\.\d+)$", filename, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def is_story_file(file_path: str) -> bool:
    """Check if file is a story file"""
    path = Path(file_path)
    return (
        "stories" in str(path) and
        path.suffix == ".md" and
        (
            ".story.md" in str(path) or
            "story-" in path.stem.lower()
        )
    )


def print_header():
    """Print validation header"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}[WORKFLOW GATE] BMad Workflow Pre-commit Validation{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print()


def print_result(result: ValidationResult):
    """Print validation result"""
    if result.passed:
        if result.details.get("skipped"):
            print(f"  {YELLOW}[SKIP]{RESET} Story {result.story_id}: {result.details.get('reason', 'Legacy Epic')}")
        else:
            print(f"  {GREEN}[PASS]{RESET} Story {result.story_id}: Status = {result.current_status.value if result.current_status else 'N/A'}")
    else:
        print(f"  {RED}[BLOCKED]{RESET} Story {result.story_id}")
        print(f"\n{result.error_message}\n")


def print_summary(passed: int, failed: int, skipped: int):
    """Print summary"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Summary: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET}, {YELLOW}{skipped} skipped{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> int:
    """
    Main entry point for pre-commit hook.

    Returns:
        0 if all validations passed
        1 if any validation failed (blocks commit)
    """
    print_header()

    # Get staged files
    staged_files = get_staged_files()

    # Filter story files
    story_files = [f for f in staged_files if is_story_file(f)]

    if not story_files:
        print(f"  {GREEN}No story files staged for commit{RESET}")
        print()
        return 0

    print(f"  Found {len(story_files)} story file(s) to validate:")
    for f in story_files:
        print(f"    - {f}")
    print()

    # Initialize enforcer
    enforcer = WorkflowEnforcer(project_root)

    # Track results
    passed = 0
    failed = 0
    skipped = 0
    failed_stories: list[ValidationResult] = []

    # Validate each story
    for story_file in story_files:
        story_id = extract_story_id(story_file)

        if story_id is None:
            print(f"  {YELLOW}[WARN]{RESET} Could not extract story ID from: {story_file}")
            skipped += 1
            continue

        # Validate
        result = enforcer.validate_commit_ready(story_id)
        print_result(result)

        if result.passed:
            if result.details.get("skipped"):
                skipped += 1
            else:
                passed += 1
        else:
            failed += 1
            failed_stories.append(result)

    # Print summary
    print()
    print_summary(passed, failed, skipped)

    # Return exit code
    if failed > 0:
        print()
        print(f"{RED}{BOLD}COMMIT BLOCKED{RESET} - Complete BMad workflow for failed stories first")
        print()
        return 1

    print()
    print(f"{GREEN}All validations passed - commit allowed{RESET}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
