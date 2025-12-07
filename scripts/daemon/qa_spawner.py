"""
QA Session Spawner - Manages Claude Code QA sessions.

Spawns and monitors Claude Code sessions for automatic QA review
when dev-complete status is detected.
"""

import subprocess
import threading
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class QASessionState(Enum):
    """States for a QA session."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class QASession:
    """Represents a QA review session."""
    story_id: str
    worktree_path: Path
    state: QASessionState = QASessionState.PENDING
    process: Optional[subprocess.Popen] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    return_code: Optional[int] = None
    log_file: Optional[Path] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "story_id": self.story_id,
            "worktree_path": str(self.worktree_path),
            "state": self.state.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "return_code": self.return_code,
            "log_file": str(self.log_file) if self.log_file else None,
            "error_message": self.error_message
        }


class QASessionSpawner:
    """
    Spawns and manages Claude Code QA sessions.

    Limits concurrent sessions and monitors completion status.
    """

    # QA prompt template for Claude Code
    QA_PROMPT_TEMPLATE = '''Execute QA review for Story {story_id}.

===============================================================================
QA WORKFLOW - Full Sequence
===============================================================================

1. Read .worktree-status.yaml to confirm dev-complete status
2. Read the story file to understand requirements

3. Activate QA Agent: /qa

4. Execute full QA sequence:
   *trace {story_id}        # Requirements coverage
   *nfr-assess {story_id}   # Non-functional requirements
   *review {story_id}       # Comprehensive review
   *gate {story_id}         # Quality gate decision

5. Based on gate result:
   - If PASS/WAIVED: Update status to "ready-to-merge"
   - If CONCERNS: Attempt 1 fix cycle, then re-gate
   - If FAIL: Update status to "qa-blocked"

6. Update .worktree-status.yaml with:
   - status: "ready-to-merge" or "qa-blocked"
   - qa_reviewed: true
   - qa_gate: PASS/CONCERNS/FAIL/WAIVED

7. Write .worktree-result.json with final outcome

===============================================================================
'''

    # Default allowed tools for QA sessions
    DEFAULT_ALLOWED_TOOLS = "Bash,Read,Write,Edit,Grep,Glob,TodoWrite"

    def __init__(
        self,
        max_concurrent: int = 3,
        allowed_tools: Optional[str] = None,
        max_turns: int = 150
    ):
        """
        Initialize the spawner.

        Args:
            max_concurrent: Maximum concurrent QA sessions
            allowed_tools: Comma-separated list of allowed tools
            max_turns: Maximum agentic turns per session
        """
        self.max_concurrent = max_concurrent
        self.allowed_tools = allowed_tools or self.DEFAULT_ALLOWED_TOOLS
        self.max_turns = max_turns

        self._sessions: Dict[str, QASession] = {}
        self._lock = threading.Lock()

    @property
    def active_count(self) -> int:
        """Get number of active (running) sessions."""
        with self._lock:
            return sum(
                1 for s in self._sessions.values()
                if s.state == QASessionState.RUNNING
            )

    @property
    def pending_count(self) -> int:
        """Get number of pending sessions."""
        with self._lock:
            return sum(
                1 for s in self._sessions.values()
                if s.state == QASessionState.PENDING
            )

    def spawn_qa_session(self, story_id: str, worktree_path: Path) -> bool:
        """
        Spawn a new QA session for a story.

        Args:
            story_id: The story ID to review
            worktree_path: Path to the worktree

        Returns:
            True if session was spawned or queued
        """
        with self._lock:
            # Check if already exists
            if story_id in self._sessions:
                existing = self._sessions[story_id]
                if existing.state in [QASessionState.PENDING, QASessionState.RUNNING]:
                    print(f"[QASpawner] Session already exists for Story {story_id}")
                    return False

            # Check capacity
            if self.active_count >= self.max_concurrent:
                # Queue for later
                print(f"[QASpawner] Capacity full, queuing Story {story_id}")
                self._sessions[story_id] = QASession(
                    story_id=story_id,
                    worktree_path=worktree_path,
                    state=QASessionState.PENDING
                )
                return True

        # Spawn immediately
        return self._spawn(story_id, worktree_path)

    def _spawn(self, story_id: str, worktree_path: Path) -> bool:
        """Actually spawn the Claude Code process."""
        log_file = worktree_path / f"qa-session-{story_id}.log"
        prompt = self.QA_PROMPT_TEMPLATE.format(story_id=story_id)

        # Build Claude command
        cmd = [
            'claude',
            '-p', prompt,
            '--dangerously-skip-permissions',
            '--allowedTools', self.allowed_tools,
            '--max-turns', str(self.max_turns)
        ]

        try:
            # Open log file
            log_handle = open(log_file, 'w', encoding='utf-8')

            # Spawn process
            process = subprocess.Popen(
                cmd,
                cwd=str(worktree_path),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
            )

            # Record session
            with self._lock:
                self._sessions[story_id] = QASession(
                    story_id=story_id,
                    worktree_path=worktree_path,
                    state=QASessionState.RUNNING,
                    process=process,
                    started_at=datetime.now(),
                    log_file=log_file
                )

            # Start monitoring thread
            threading.Thread(
                target=self._monitor_session,
                args=(story_id, log_handle),
                daemon=True
            ).start()

            print(f"[QASpawner] Started QA session for Story {story_id}")
            print(f"[QASpawner]   Log: {log_file}")
            return True

        except Exception as e:
            print(f"[QASpawner] Failed to spawn QA session for {story_id}: {e}")
            with self._lock:
                self._sessions[story_id] = QASession(
                    story_id=story_id,
                    worktree_path=worktree_path,
                    state=QASessionState.FAILED,
                    error_message=str(e)
                )
            return False

    def _monitor_session(self, story_id: str, log_handle):
        """Monitor a running session and update state on completion."""
        session = self._sessions.get(story_id)
        if not session or not session.process:
            return

        try:
            # Wait for process to complete
            return_code = session.process.wait()

            with self._lock:
                session.completed_at = datetime.now()
                session.return_code = return_code
                session.state = (
                    QASessionState.COMPLETED if return_code == 0
                    else QASessionState.FAILED
                )

            print(f"[QASpawner] Session completed for Story {story_id} (code: {return_code})")

            # Process pending queue
            self._process_pending_queue()

        except Exception as e:
            print(f"[QASpawner] Error monitoring session {story_id}: {e}")
        finally:
            try:
                log_handle.close()
            except:
                pass

    def _process_pending_queue(self):
        """Process pending sessions if capacity available."""
        with self._lock:
            if self.active_count >= self.max_concurrent:
                return

            # Find pending sessions
            for story_id, session in list(self._sessions.items()):
                if session.state == QASessionState.PENDING:
                    # Remove lock temporarily to spawn
                    break
            else:
                return

        # Spawn outside lock
        if session.state == QASessionState.PENDING:
            self._spawn(story_id, session.worktree_path)

    def get_session(self, story_id: str) -> Optional[QASession]:
        """Get session info for a story."""
        return self._sessions.get(story_id)

    def get_all_sessions(self) -> Dict[str, QASession]:
        """Get all sessions."""
        return dict(self._sessions)

    def get_status_summary(self) -> dict:
        """Get summary of all sessions."""
        with self._lock:
            return {
                "total": len(self._sessions),
                "running": self.active_count,
                "pending": self.pending_count,
                "completed": sum(1 for s in self._sessions.values() if s.state == QASessionState.COMPLETED),
                "failed": sum(1 for s in self._sessions.values() if s.state == QASessionState.FAILED),
                "sessions": {k: v.to_dict() for k, v in self._sessions.items()}
            }


if __name__ == "__main__":
    # Quick test
    print("QASessionSpawner module loaded successfully")
    print(f"Default allowed tools: {QASessionSpawner.DEFAULT_ALLOWED_TOOLS}")

    spawner = QASessionSpawner(max_concurrent=3)
    print(f"Max concurrent sessions: {spawner.max_concurrent}")
    print(f"Active sessions: {spawner.active_count}")
    print(f"Pending sessions: {spawner.pending_count}")
