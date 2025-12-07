"""
Linear Progress - Progress tracking and persistence for linear development daemon.

Manages the state of sequential Story execution with crash recovery support.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ProgressStatus(Enum):
    """Status of the linear development session."""
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    HALTED = "halted"
    COMPLETED = "completed"


class StoryOutcome(Enum):
    """Possible outcomes for a Story execution."""
    SUCCESS = "SUCCESS"
    DEV_BLOCKED = "DEV_BLOCKED"
    QA_BLOCKED = "QA_BLOCKED"
    QA_CONCERNS_UNFIXED = "QA_CONCERNS_UNFIXED"
    COMPACT = "COMPACT"  # Claude session compacted
    CRASH = "CRASH"      # Process crashed without result
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_result_outcome(cls, outcome_str: str) -> 'StoryOutcome':
        """Convert worktree-result.json outcome to StoryOutcome."""
        mapping = {
            "SUCCESS": cls.SUCCESS,
            "DEV_BLOCKED": cls.DEV_BLOCKED,
            "QA_BLOCKED": cls.QA_BLOCKED,
            "QA_CONCERNS_UNFIXED": cls.QA_CONCERNS_UNFIXED,
            "TIMEOUT": cls.TIMEOUT,
            "ERROR": cls.ERROR,
        }
        return mapping.get(outcome_str, cls.UNKNOWN)

    def is_success(self) -> bool:
        """Check if outcome represents success."""
        return self == StoryOutcome.SUCCESS

    def is_blocked(self) -> bool:
        """Check if outcome represents a blocked state (needs retry or halt)."""
        return self in [
            StoryOutcome.DEV_BLOCKED,
            StoryOutcome.QA_BLOCKED,
            StoryOutcome.QA_CONCERNS_UNFIXED,
        ]

    def is_restart_needed(self) -> bool:
        """Check if outcome means we need to restart (compact/crash)."""
        return self in [StoryOutcome.COMPACT, StoryOutcome.CRASH]


@dataclass
class CompletedStory:
    """Record of a completed Story."""
    story_id: str
    outcome: str  # String to allow JSON serialization
    commit_sha: Optional[str] = None
    duration_seconds: float = 0.0
    retry_count: int = 0
    compact_restarts: int = 0
    completed_at: Optional[str] = None

    # Post-processing tracking (Dev-QA Auto-Record Pipeline)
    story_file_updated: bool = False
    qa_gate_file: Optional[str] = None
    dev_record_complete: bool = False
    qa_record_complete: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompletedStory':
        # Handle backward compatibility with older progress files
        valid_fields = {
            'story_id', 'outcome', 'commit_sha', 'duration_seconds',
            'retry_count', 'compact_restarts', 'completed_at',
            'story_file_updated', 'qa_gate_file',
            'dev_record_complete', 'qa_record_complete'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass
class CurrentStory:
    """State of the currently executing Story."""
    story_id: str
    started_at: str
    retry_count: int = 0
    compact_restarts: int = 0
    claude_pid: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CurrentStory':
        return cls(**data)


@dataclass
class Statistics:
    """Aggregate statistics for the session."""
    total_duration_seconds: float = 0.0
    total_retries: int = 0
    total_compact_restarts: int = 0
    stories_succeeded: int = 0
    stories_failed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Statistics':
        return cls(**data)


@dataclass
class LinearProgress:
    """
    Complete progress state for linear development daemon.

    Supports:
    - Crash recovery via JSON persistence
    - Resume from any point
    - Statistics tracking
    """
    version: str = "2.0"
    session_id: str = ""
    daemon_pid: Optional[int] = None
    stories: List[str] = field(default_factory=list)
    current_index: int = 0
    status: str = "idle"
    started_at: Optional[str] = None
    last_updated: Optional[str] = None
    completed_stories: List[CompletedStory] = field(default_factory=list)
    current_story: Optional[CurrentStory] = None
    halted_at: Optional[str] = None
    halt_reason: Optional[str] = None
    statistics: Statistics = field(default_factory=Statistics)

    # Circuit breaker settings
    max_compact_restarts: int = 5
    max_retries: int = 1

    def __post_init__(self):
        """Initialize session if not set."""
        if not self.session_id:
            self.session_id = f"linear-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        self.daemon_pid = os.getpid()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "session_id": self.session_id,
            "daemon_pid": self.daemon_pid,
            "stories": self.stories,
            "current_index": self.current_index,
            "status": self.status,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "completed_stories": [s.to_dict() for s in self.completed_stories],
            "current_story": self.current_story.to_dict() if self.current_story else None,
            "halted_at": self.halted_at,
            "halt_reason": self.halt_reason,
            "statistics": self.statistics.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinearProgress':
        """Create from dictionary (JSON deserialization)."""
        progress = cls(
            version=data.get("version", "2.0"),
            session_id=data.get("session_id", ""),
            daemon_pid=data.get("daemon_pid"),
            stories=data.get("stories", []),
            current_index=data.get("current_index", 0),
            status=data.get("status", "idle"),
            started_at=data.get("started_at"),
            last_updated=data.get("last_updated"),
            halted_at=data.get("halted_at"),
            halt_reason=data.get("halt_reason"),
        )

        # Deserialize completed stories
        completed = data.get("completed_stories", [])
        progress.completed_stories = [CompletedStory.from_dict(s) for s in completed]

        # Deserialize current story
        current = data.get("current_story")
        if current:
            progress.current_story = CurrentStory.from_dict(current)

        # Deserialize statistics
        stats = data.get("statistics", {})
        progress.statistics = Statistics.from_dict(stats)

        return progress

    @classmethod
    def load(cls, path: Path) -> Optional['LinearProgress']:
        """Load progress from JSON file."""
        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"[LinearProgress] Warning: Could not load progress: {e}")
            return None

    def save(self, path: Path):
        """Save progress to JSON file."""
        self.last_updated = datetime.now().isoformat()
        self.daemon_pid = os.getpid()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[LinearProgress] Error saving progress: {e}")

    def get_current_story_id(self) -> Optional[str]:
        """Get the current Story ID to process."""
        if self.current_index < len(self.stories):
            return self.stories[self.current_index]
        return None

    def is_complete(self) -> bool:
        """Check if all stories are complete."""
        return self.current_index >= len(self.stories)

    def is_halted(self) -> bool:
        """Check if execution is halted."""
        return self.status == "halted"

    def start_story(self, story_id: str, claude_pid: Optional[int] = None):
        """Mark a story as started."""
        self.status = "in_progress"
        self.current_story = CurrentStory(
            story_id=story_id,
            started_at=datetime.now().isoformat(),
            retry_count=0,
            compact_restarts=0,
            claude_pid=claude_pid,
        )

    def mark_story_complete(
        self,
        story_id: str,
        outcome: StoryOutcome,
        commit_sha: Optional[str] = None,
        duration_seconds: float = 0.0,
    ):
        """Mark a story as completed and move to next."""
        completed = CompletedStory(
            story_id=story_id,
            outcome=outcome.value,
            commit_sha=commit_sha,
            duration_seconds=duration_seconds,
            retry_count=self.current_story.retry_count if self.current_story else 0,
            compact_restarts=self.current_story.compact_restarts if self.current_story else 0,
            completed_at=datetime.now().isoformat(),
        )
        self.completed_stories.append(completed)

        # Update statistics
        if outcome.is_success():
            self.statistics.stories_succeeded += 1
        else:
            self.statistics.stories_failed += 1

        self.statistics.total_duration_seconds += duration_seconds

        # Move to next story
        self.current_index += 1
        self.current_story = None

        # Check if complete
        if self.is_complete():
            self.status = "completed"

    def increment_retry(self) -> bool:
        """
        Increment retry count for current story.

        Returns:
            True if retry is allowed, False if should halt.
        """
        if self.current_story:
            self.current_story.retry_count += 1
            self.statistics.total_retries += 1
            return self.current_story.retry_count <= self.max_retries
        return False

    def increment_compact_restart(self) -> bool:
        """
        Increment compact restart count for current story.

        Returns:
            True if restart is allowed, False if should halt (circuit breaker).
        """
        if self.current_story:
            self.current_story.compact_restarts += 1
            self.statistics.total_compact_restarts += 1
            return self.current_story.compact_restarts <= self.max_compact_restarts
        return False

    def should_retry(self) -> bool:
        """Check if current story should be retried."""
        if self.current_story:
            return self.current_story.retry_count < self.max_retries
        return False

    def halt(self, reason: str):
        """Halt execution with reason."""
        self.status = "halted"
        self.halted_at = datetime.now().isoformat()
        self.halt_reason = reason

    def resume(self):
        """Resume from halted state."""
        self.status = "in_progress"
        self.halted_at = None
        self.halt_reason = None
        # Re-initialize current story if needed
        story_id = self.get_current_story_id()
        if story_id and not self.current_story:
            self.start_story(story_id)


if __name__ == "__main__":
    # Quick test
    print("LinearProgress module loaded successfully")

    # Create test progress
    progress = LinearProgress(stories=["15.1", "15.2", "15.3"])
    print(f"Session ID: {progress.session_id}")
    print(f"Stories: {progress.stories}")
    print(f"Current: {progress.get_current_story_id()}")

    # Simulate start
    progress.start_story("15.1", claude_pid=12345)
    print(f"Started: {progress.current_story}")

    # Simulate complete
    progress.mark_story_complete("15.1", StoryOutcome.SUCCESS, "abc1234", 1800)
    print(f"Completed: {len(progress.completed_stories)} stories")
    print(f"Next: {progress.get_current_story_id()}")

    # Test serialization
    data = progress.to_dict()
    restored = LinearProgress.from_dict(data)
    print(f"Restored session: {restored.session_id}")
