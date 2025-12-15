"""
Harness Progress - Progress tracking and persistence for story harness.

Provides crash recovery support via JSON persistence.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class GateResult:
    """Result of CommitGate check (simplified G3+G4)."""
    passed: bool
    g3_tests: bool = False
    g4_qa: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GateResult':
        return cls(**data)


@dataclass
class StoryProgress:
    """Progress state for a single Story."""
    id: str
    status: str = "pending"  # pending, in_progress, completed, failed
    commit_sha: Optional[str] = None
    gate_result: Optional[str] = None
    duration_seconds: Optional[float] = None
    retry_count: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoryProgress':
        return cls(**data)


@dataclass
class HarnessProgress:
    """
    Complete progress state for story harness.

    Supports:
    - Crash recovery via JSON persistence
    - Resume from any point
    - Statistics tracking
    """
    version: str = "1.0"
    session_id: str = ""
    epic_id: str = ""
    stories: List[StoryProgress] = field(default_factory=list)
    status: str = "idle"  # idle, in_progress, halted, completed
    started_at: Optional[str] = None
    last_updated: Optional[str] = None
    halted_at: Optional[str] = None
    halt_reason: Optional[str] = None

    # Statistics
    total_duration_seconds: float = 0.0
    gate_passes: int = 0
    gate_failures: int = 0
    restarts: int = 0

    # Circuit breaker
    max_retries: int = 1

    def __post_init__(self):
        """Initialize session if not set."""
        if not self.session_id:
            self.session_id = f"harness-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if not self.started_at:
            self.started_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "session_id": self.session_id,
            "epic_id": self.epic_id,
            "stories": [s.to_dict() for s in self.stories],
            "status": self.status,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "halted_at": self.halted_at,
            "halt_reason": self.halt_reason,
            "statistics": {
                "total_duration_seconds": self.total_duration_seconds,
                "gate_passes": self.gate_passes,
                "gate_failures": self.gate_failures,
                "restarts": self.restarts,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HarnessProgress':
        """Create from dictionary (JSON deserialization)."""
        progress = cls(
            version=data.get("version", "1.0"),
            session_id=data.get("session_id", ""),
            epic_id=data.get("epic_id", ""),
            status=data.get("status", "idle"),
            started_at=data.get("started_at"),
            last_updated=data.get("last_updated"),
            halted_at=data.get("halted_at"),
            halt_reason=data.get("halt_reason"),
        )

        # Deserialize stories
        stories = data.get("stories", [])
        progress.stories = [StoryProgress.from_dict(s) for s in stories]

        # Deserialize statistics
        stats = data.get("statistics", {})
        progress.total_duration_seconds = stats.get("total_duration_seconds", 0.0)
        progress.gate_passes = stats.get("gate_passes", 0)
        progress.gate_failures = stats.get("gate_failures", 0)
        progress.restarts = stats.get("restarts", 0)

        return progress

    @classmethod
    def get_progress_file(cls, epic_id: str) -> Path:
        """Get the progress file path for an epic."""
        return Path(f"harness-progress-{epic_id}.json")

    @classmethod
    def load(cls, epic_id: str) -> Optional['HarnessProgress']:
        """Load progress from JSON file."""
        path = cls.get_progress_file(epic_id)
        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"[HarnessProgress] Warning: Could not load progress: {e}")
            return None

    @classmethod
    def load_or_create(cls, epic_id: str, story_ids: List[str] = None) -> 'HarnessProgress':
        """Load existing progress or create new one."""
        existing = cls.load(epic_id)
        if existing:
            existing.restarts += 1
            return existing

        progress = cls(epic_id=epic_id)
        if story_ids:
            progress.stories = [StoryProgress(id=sid) for sid in story_ids]
        return progress

    def save(self):
        """Save progress to JSON file."""
        self.last_updated = datetime.now().isoformat()
        path = self.get_progress_file(self.epic_id)

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[HarnessProgress] Error saving progress: {e}")

    def get_next_pending(self) -> Optional[StoryProgress]:
        """Get the next pending story to process."""
        for story in self.stories:
            if story.status == "pending":
                return story
        return None

    def is_complete(self) -> bool:
        """Check if all stories are complete."""
        return all(s.status in ("completed", "failed") for s in self.stories)

    def is_halted(self) -> bool:
        """Check if execution is halted."""
        return self.status == "halted"

    def start_story(self, story_id: str):
        """Mark a story as started."""
        self.status = "in_progress"
        for story in self.stories:
            if story.id == story_id:
                story.status = "in_progress"
                story.started_at = datetime.now().isoformat()
                break

    def mark_completed(self, story_id: str, commit_sha: str, gate_result: GateResult,
                       duration_seconds: float = 0.0):
        """Mark a story as completed."""
        for story in self.stories:
            if story.id == story_id:
                story.status = "completed"
                story.commit_sha = commit_sha
                story.gate_result = "PASS" if gate_result.passed else "FAIL"
                story.duration_seconds = duration_seconds
                story.completed_at = datetime.now().isoformat()
                break

        self.gate_passes += 1
        self.total_duration_seconds += duration_seconds

        if self.is_complete():
            self.status = "completed"

    def mark_failed(self, story_id: str, gate_result: GateResult, error_message: str = None):
        """Mark a story as failed."""
        for story in self.stories:
            if story.id == story_id:
                story.status = "failed"
                story.gate_result = "FAIL"
                story.error_message = error_message
                story.completed_at = datetime.now().isoformat()
                break

        self.gate_failures += 1

    def should_retry(self, story_id: str) -> bool:
        """Check if a story should be retried."""
        for story in self.stories:
            if story.id == story_id:
                return story.retry_count < self.max_retries
        return False

    def increment_retry(self, story_id: str):
        """Increment retry count for a story."""
        for story in self.stories:
            if story.id == story_id:
                story.retry_count += 1
                story.status = "pending"  # Reset to pending for retry
                break

    def halt(self, reason: str):
        """Halt execution with reason."""
        self.status = "halted"
        self.halted_at = datetime.now().isoformat()
        self.halt_reason = reason

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of progress."""
        completed = sum(1 for s in self.stories if s.status == "completed")
        failed = sum(1 for s in self.stories if s.status == "failed")
        pending = sum(1 for s in self.stories if s.status == "pending")
        in_progress = sum(1 for s in self.stories if s.status == "in_progress")

        return {
            "epic_id": self.epic_id,
            "status": self.status,
            "total": len(self.stories),
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "in_progress": in_progress,
            "gate_passes": self.gate_passes,
            "gate_failures": self.gate_failures,
            "total_duration_seconds": self.total_duration_seconds,
            "restarts": self.restarts,
        }


if __name__ == "__main__":
    # Quick test
    print("HarnessProgress module loaded successfully")

    # Create test progress
    progress = HarnessProgress.load_or_create("test", ["1.1", "1.2", "1.3"])
    print(f"Session ID: {progress.session_id}")
    print(f"Stories: {[s.id for s in progress.stories]}")
    print(f"Next pending: {progress.get_next_pending().id if progress.get_next_pending() else None}")

    # Simulate completion
    progress.start_story("1.1")
    gate = GateResult(passed=True, g3_tests=True, g4_qa=True)
    progress.mark_completed("1.1", "abc123", gate, 1800)
    print(f"Summary: {progress.get_summary()}")
