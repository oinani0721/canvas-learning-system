"""
Worktree Scanner - Discovers active parallel development worktrees.

This module finds all Git worktrees that follow the Canvas parallel development
naming convention (Canvas-develop-{story_id}).
"""

import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class WorktreeInfo:
    """Information about a development worktree."""
    path: Path
    branch: str
    story_id: str
    status_file: Path
    result_file: Path

    @property
    def exists(self) -> bool:
        """Check if worktree directory exists."""
        return self.path.exists()

    @property
    def has_status_file(self) -> bool:
        """Check if .worktree-status.yaml exists."""
        return self.status_file.exists()

    @property
    def has_result_file(self) -> bool:
        """Check if .worktree-result.json exists."""
        return self.result_file.exists()


class WorktreeScanner:
    """Discovers and tracks active parallel development worktrees."""

    # Naming pattern for development worktrees
    WORKTREE_PREFIX = "Canvas-develop-"

    def __init__(self, base_path: Path, main_repo_path: Optional[Path] = None):
        """
        Initialize the scanner.

        Args:
            base_path: Parent directory where worktrees are located
            main_repo_path: Path to main Canvas repository (for git commands)
        """
        self.base_path = Path(base_path)
        self.main_repo_path = main_repo_path or (self.base_path / "Canvas")

    def scan(self) -> List[WorktreeInfo]:
        """
        Scan for all active development worktrees.

        Returns:
            List of WorktreeInfo objects for each found worktree
        """
        worktrees = []

        # Method 1: Use git worktree list
        git_worktrees = self._scan_git_worktrees()

        # Method 2: Scan filesystem for Canvas-develop-* directories
        fs_worktrees = self._scan_filesystem()

        # Merge results (git list is authoritative, but include FS findings)
        seen_paths = set()
        for wt in git_worktrees:
            worktrees.append(wt)
            seen_paths.add(wt.path)

        for wt in fs_worktrees:
            if wt.path not in seen_paths:
                worktrees.append(wt)

        return worktrees

    def _scan_git_worktrees(self) -> List[WorktreeInfo]:
        """Scan using git worktree list --porcelain."""
        worktrees = []

        try:
            result = subprocess.run(
                ['git', 'worktree', 'list', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=str(self.main_repo_path),
                timeout=10
            )

            if result.returncode != 0:
                return worktrees

            # Parse porcelain output
            current_path = None
            current_branch = None

            for line in result.stdout.strip().split('\n'):
                if line.startswith('worktree '):
                    current_path = Path(line[9:])
                elif line.startswith('branch refs/heads/'):
                    current_branch = line[18:]
                elif line == '' and current_path:
                    # End of worktree block
                    if self._is_dev_worktree(current_path):
                        story_id = self._extract_story_id(current_path.name)
                        worktrees.append(WorktreeInfo(
                            path=current_path,
                            branch=current_branch or "unknown",
                            story_id=story_id,
                            status_file=current_path / '.worktree-status.yaml',
                            result_file=current_path / '.worktree-result.json'
                        ))
                    current_path = None
                    current_branch = None

            # Handle last worktree if no trailing newline
            if current_path and self._is_dev_worktree(current_path):
                story_id = self._extract_story_id(current_path.name)
                worktrees.append(WorktreeInfo(
                    path=current_path,
                    branch=current_branch or "unknown",
                    story_id=story_id,
                    status_file=current_path / '.worktree-status.yaml',
                    result_file=current_path / '.worktree-result.json'
                ))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return worktrees

    def _scan_filesystem(self) -> List[WorktreeInfo]:
        """Scan filesystem for Canvas-develop-* directories."""
        worktrees = []

        try:
            for item in self.base_path.iterdir():
                if item.is_dir() and item.name.startswith(self.WORKTREE_PREFIX):
                    story_id = self._extract_story_id(item.name)
                    status_file = item / '.worktree-status.yaml'

                    # Only include if it has a status file (indicates proper setup)
                    if status_file.exists():
                        worktrees.append(WorktreeInfo(
                            path=item,
                            branch=f"develop-story-{story_id}",
                            story_id=story_id,
                            status_file=status_file,
                            result_file=item / '.worktree-result.json'
                        ))
        except PermissionError:
            pass

        return worktrees

    def _is_dev_worktree(self, path: Path) -> bool:
        """Check if path is a development worktree."""
        return (
            self.WORKTREE_PREFIX in str(path) and
            (path / '.worktree-status.yaml').exists()
        )

    def _extract_story_id(self, name: str) -> str:
        """
        Extract story ID from worktree name.

        Examples:
            'Canvas-develop-13.1' -> '13.1'
            'Canvas-develop-15.2' -> '15.2'
        """
        if name.startswith(self.WORKTREE_PREFIX):
            return name[len(self.WORKTREE_PREFIX):]
        return name.split('-')[-1] if '-' in name else "unknown"

    def get_worktree(self, story_id: str) -> Optional[WorktreeInfo]:
        """Get a specific worktree by story ID."""
        for wt in self.scan():
            if wt.story_id == story_id:
                return wt
        return None


if __name__ == "__main__":
    # Quick test
    import sys

    base_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Users\ROG\托福")
    scanner = WorktreeScanner(base_path)

    print(f"Scanning for worktrees in {base_path}...")
    worktrees = scanner.scan()

    if worktrees:
        print(f"\nFound {len(worktrees)} worktrees:")
        for wt in worktrees:
            status = "✅" if wt.has_status_file else "❌"
            result = "📄" if wt.has_result_file else "⏳"
            print(f"  {status} {result} Story {wt.story_id}: {wt.path}")
    else:
        print("\nNo worktrees found.")
