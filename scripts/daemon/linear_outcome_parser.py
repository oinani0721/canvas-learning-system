"""
Linear Outcome Parser - Parse worktree results and detect compact/crash signals.

Determines the outcome of a Claude session by examining:
1. .worktree-result.json (primary, most reliable)
2. Process exit code
3. Log file content (for compact detection)
"""

import json
import re
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from linear_progress import StoryOutcome


@dataclass
class ParsedOutcome:
    """Result of parsing a story execution."""
    outcome: StoryOutcome
    commit_sha: Optional[str] = None
    blocking_reason: Optional[str] = None
    duration_seconds: float = 0.0
    is_compact: bool = False
    raw_result: Optional[dict] = None


class OutcomeParser:
    """
    Parse .worktree-result.json and log files to determine story outcome.

    Priority:
    1. .worktree-result.json exists → parse outcome from it
    2. Exit code != 0 + compact detected → COMPACT
    3. Exit code != 0 + no result → CRASH
    4. Exit code == 0 + no result → UNKNOWN (unexpected)
    """

    # Patterns to detect compact in log files
    COMPACT_PATTERNS = [
        r"Compacting conversation",
        r"\[compact\]",
        r"Context.*compacting",
        r"conversation.*compact",
    ]

    # Patterns to detect errors that might indicate issues
    ERROR_PATTERNS = [
        r"FATAL ERROR",
        r"Unhandled exception",
        r"Process terminated",
    ]

    def __init__(self, result_filename: str = ".worktree-result.json"):
        self.result_filename = result_filename
        self._compact_regex = re.compile(
            "|".join(self.COMPACT_PATTERNS),
            re.IGNORECASE
        )

    def parse(
        self,
        worktree_path: Path,
        return_code: int
    ) -> ParsedOutcome:
        """
        Parse the outcome of a story execution.

        Args:
            worktree_path: Path to the worktree directory
            return_code: Process exit code from Claude CLI

        Returns:
            ParsedOutcome with determined outcome and details
        """
        result_file = worktree_path / self.result_filename
        log_file = worktree_path / "dev-qa-output.log"

        # Priority 1: Check result file
        if result_file.exists():
            return self._parse_result_file(result_file)

        # Priority 2: No result file, check for compact/crash
        if return_code != 0:
            # Check if it was a compact
            if self._log_contains_compact(log_file):
                return ParsedOutcome(
                    outcome=StoryOutcome.COMPACT,
                    is_compact=True,
                )
            else:
                return ParsedOutcome(
                    outcome=StoryOutcome.CRASH,
                    blocking_reason=f"Process exited with code {return_code}",
                )

        # Priority 3: Exit code 0 but no result file
        # This is unexpected - Claude should always write result
        return ParsedOutcome(
            outcome=StoryOutcome.UNKNOWN,
            blocking_reason="Process exited successfully but no result file found",
        )

    def _parse_result_file(self, result_file: Path) -> ParsedOutcome:
        """Parse the .worktree-result.json file."""
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            outcome_str = data.get("outcome", "UNKNOWN")
            outcome = StoryOutcome.from_result_outcome(outcome_str)

            return ParsedOutcome(
                outcome=outcome,
                commit_sha=data.get("commit_sha"),
                blocking_reason=data.get("blocking_reason"),
                duration_seconds=data.get("duration_seconds", 0.0),
                is_compact=False,
                raw_result=data,
            )

        except json.JSONDecodeError as e:
            return ParsedOutcome(
                outcome=StoryOutcome.ERROR,
                blocking_reason=f"Invalid JSON in result file: {e}",
            )
        except Exception as e:
            return ParsedOutcome(
                outcome=StoryOutcome.ERROR,
                blocking_reason=f"Error reading result file: {e}",
            )

    def _log_contains_compact(self, log_file: Path) -> bool:
        """
        Check if log file contains compact indicators.

        Reads the last 100 lines to check for compact patterns.
        """
        if not log_file.exists():
            return False

        try:
            # Read last portion of log file efficiently
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                # Seek to approximate last 50KB
                try:
                    f.seek(0, 2)  # End of file
                    size = f.tell()
                    if size > 50000:
                        f.seek(size - 50000)
                        f.readline()  # Skip partial line
                    else:
                        f.seek(0)
                except:
                    f.seek(0)

                content = f.read()

            # Check for compact patterns
            return bool(self._compact_regex.search(content))

        except Exception as e:
            print(f"[OutcomeParser] Warning: Could not read log file: {e}")
            return False

    def check_log_for_completion(self, log_file: Path) -> Tuple[bool, Optional[str]]:
        """
        Check log file for completion indicators.

        Returns:
            Tuple of (is_complete, outcome_hint)
        """
        if not log_file.exists():
            return False, None

        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(0, 2)
                size = f.tell()
                if size > 20000:
                    f.seek(size - 20000)
                    f.readline()
                else:
                    f.seek(0)
                content = f.read()

            # Check for success indicators
            if '"outcome": "SUCCESS"' in content or '"outcome":"SUCCESS"' in content:
                return True, "SUCCESS"

            # Check for blocked indicators
            if '"outcome": "DEV_BLOCKED"' in content:
                return True, "DEV_BLOCKED"
            if '"outcome": "QA_BLOCKED"' in content:
                return True, "QA_BLOCKED"

            return False, None

        except Exception:
            return False, None


class LogMonitor:
    """
    Real-time log file monitor for detecting compact during execution.

    Used in background thread to detect compact before process exits.
    """

    def __init__(self, log_file: Path, parser: OutcomeParser):
        self.log_file = log_file
        self.parser = parser
        self._last_position = 0

    def check_new_content(self) -> Tuple[bool, bool]:
        """
        Check for new content in log file.

        Returns:
            Tuple of (has_new_content, compact_detected)
        """
        if not self.log_file.exists():
            return False, False

        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(0, 2)
                current_size = f.tell()

                if current_size <= self._last_position:
                    return False, False

                f.seek(self._last_position)
                new_content = f.read()
                self._last_position = current_size

                # Check for compact in new content
                compact_detected = bool(self.parser._compact_regex.search(new_content))

                return True, compact_detected

        except Exception:
            return False, False

    def reset(self):
        """Reset monitor position."""
        self._last_position = 0


if __name__ == "__main__":
    # Quick test
    print("OutcomeParser module loaded successfully")

    parser = OutcomeParser()

    # Test outcome mapping
    for outcome_str in ["SUCCESS", "DEV_BLOCKED", "QA_BLOCKED", "UNKNOWN"]:
        outcome = StoryOutcome.from_result_outcome(outcome_str)
        print(f"  {outcome_str} -> {outcome.value} (success={outcome.is_success()}, blocked={outcome.is_blocked()})")

    # Test compact patterns
    test_lines = [
        "Compacting conversation...",
        "The context is being compacted",
        "[compact] triggered",
        "Normal log line",
    ]
    for line in test_lines:
        match = parser._compact_regex.search(line)
        print(f"  '{line}' -> compact={bool(match)}")
