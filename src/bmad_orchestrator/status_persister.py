"""
Status Persister - Batch update canvas-project-status.yaml after workflow

Persists workflow results to the project YAML status file.
Implements End-of-Workflow Batch Update pattern.

Author: Canvas Learning System Team
Version: 1.0.0

Features:
- Batch update after workflow completion
- Backup mechanism before writes
- Rollback on failure
- Status downgrade protection
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Status type (matches YAML status_definitions)
StoryStatus = str  # pending | draft | in-progress | dev-complete | qa-review | completed | blocked


class StatusPersister:
    """
    Persist workflow state to canvas-project-status.yaml.

    Design: End-of-workflow batch update (not incremental).
    Uses merge strategy to preserve existing data.
    """

    YAML_PATH = ".bmad-core/data/canvas-project-status.yaml"

    # Status priority for downgrade protection (higher = more complete)
    STATUS_PRIORITY = {
        "pending": 0,
        "draft": 1,
        "in-progress": 2,
        "dev-complete": 3,
        "qa-review": 4,
        "completed": 5,
        "blocked": 1,  # blocked can be overwritten by progress
    }

    def __init__(self, base_path: Path):
        """
        Initialize StatusPersister.

        Args:
            base_path: Project root directory path
        """
        self.base_path = Path(base_path)
        self.yaml_file = self.base_path / self.YAML_PATH

    async def persist_workflow_result(
        self,
        final_state: Dict[str, Any],
        epic_id: str,
    ) -> bool:
        """
        Main entry: Persist entire workflow result to YAML.

        Args:
            final_state: Final workflow state (BmadOrchestratorState)
            epic_id: Epic identifier

        Returns:
            True if successful, False otherwise
        """
        # Create backup
        backup_path = self._create_backup()

        try:
            # Load existing YAML
            yaml_data = self._load_yaml()

            # Extract story statuses from workflow results
            story_statuses = self._extract_story_statuses(final_state)

            if not story_statuses:
                print("[StatusPersister] No story statuses to persist")
                return True

            # Update sections (merge, not replace)
            self._update_epic_status(yaml_data, epic_id, story_statuses, final_state)
            self._update_parallel_section(yaml_data, epic_id, story_statuses, final_state)

            # Update timestamp
            if "project" in yaml_data:
                yaml_data["project"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

            # Write back
            self._save_yaml(yaml_data)

            print(f"[StatusPersister] Updated {len(story_statuses)} story statuses for epic-{epic_id}")
            return True

        except Exception as e:
            print(f"[StatusPersister] [ERROR] Failed to persist: {e}")
            if backup_path and backup_path.exists():
                self._restore_backup(backup_path)
                print("[StatusPersister] Restored from backup")
            return False

    def _extract_story_statuses(self, final_state: Dict[str, Any]) -> Dict[str, StoryStatus]:
        """
        Map workflow outcomes to YAML status values.

        Priority (highest wins):
        1. QA outcome (PASS/WAIVED -> completed, CONCERNS -> qa-review, FAIL -> blocked)
        2. DEV outcome (SUCCESS -> dev-complete, BLOCKED/TIMEOUT/ERROR -> blocked)
        3. Story drafts (exists -> draft)
        4. Default: pending

        Args:
            final_state: Workflow final state

        Returns:
            Dict mapping story_id to status
        """
        story_ids = final_state.get("story_ids", [])
        dev_outcomes = final_state.get("dev_outcomes", []) or []
        qa_outcomes = final_state.get("qa_outcomes", []) or []
        story_drafts = final_state.get("story_drafts", []) or []
        approved_stories = final_state.get("approved_stories", []) or []

        # Build lookup dicts
        dev_map = {o["story_id"]: o for o in dev_outcomes if isinstance(o, dict)}
        qa_map = {o["story_id"]: o for o in qa_outcomes if isinstance(o, dict)}
        draft_ids = {d["story_id"] for d in story_drafts if isinstance(d, dict)}

        statuses = {}
        for story_id in story_ids:
            # 1. Check QA first (highest priority)
            qa = qa_map.get(story_id)
            if qa:
                gate = qa.get("qa_gate")
                if gate in ("PASS", "WAIVED"):
                    statuses[story_id] = "completed"
                elif gate == "CONCERNS":
                    statuses[story_id] = "qa-review"
                else:  # FAIL
                    statuses[story_id] = "blocked"
                continue

            # 2. Check DEV
            dev = dev_map.get(story_id)
            if dev:
                outcome = dev.get("outcome")
                if outcome == "SUCCESS":
                    statuses[story_id] = "dev-complete"
                elif outcome in ("DEV_BLOCKED", "ERROR", "TIMEOUT"):
                    statuses[story_id] = "blocked"
                else:
                    statuses[story_id] = "in-progress"
                continue

            # 3. Check if approved by PO
            if story_id in approved_stories:
                statuses[story_id] = "draft"
                continue

            # 4. Check drafts
            if story_id in draft_ids:
                statuses[story_id] = "draft"
                continue

            # 5. Default
            statuses[story_id] = "pending"

        return statuses

    def _update_epic_status(
        self,
        yaml_data: Dict,
        epic_id: str,
        story_statuses: Dict[str, StoryStatus],
        final_state: Dict[str, Any],
    ) -> None:
        """
        Update epic section with workflow results.

        Args:
            yaml_data: Full YAML data
            epic_id: Epic identifier
            story_statuses: Story status mapping
            final_state: Workflow final state
        """
        epics = yaml_data.setdefault("epics", {})
        epic_key = f"epic-{epic_id}"
        epic = epics.setdefault(epic_key, {})

        # Determine overall epic status
        statuses_list = list(story_statuses.values())
        all_completed = all(s == "completed" for s in statuses_list) if statuses_list else False
        any_blocked = any(s == "blocked" for s in statuses_list)
        any_in_progress = any(s in ("in-progress", "dev-complete", "qa-review", "draft")
                              for s in statuses_list)

        if all_completed:
            epic["status"] = "completed"
            epic["completion_date"] = datetime.now().strftime("%Y-%m-%d")
        elif any_blocked:
            epic["status"] = "in_progress"  # Has blockers but not fully blocked
        elif any_in_progress:
            epic["status"] = "in_progress"
        else:
            epic["status"] = "pending"

        # Update story list if not present
        if "stories" not in epic:
            epic["stories"] = list(story_statuses.keys())

        # Update substories with emoji markers
        substories = epic.setdefault("substories", {})
        for story_id, status in story_statuses.items():
            existing = substories.get(story_id, "")

            # Only update if new status is higher priority (prevent downgrade)
            if self._should_update_status(status, existing):
                emoji = self._status_to_emoji(status)
                if isinstance(existing, str):
                    # Strip old emoji and add new
                    clean = self._strip_emoji(existing)
                    substories[story_id] = f"{clean} {emoji}".strip() if clean else emoji
                else:
                    substories[story_id] = emoji

    def _update_parallel_section(
        self,
        yaml_data: Dict,
        epic_id: str,
        story_statuses: Dict[str, StoryStatus],
        final_state: Dict[str, Any],
    ) -> None:
        """
        Update parallel_development section.

        Args:
            yaml_data: Full YAML data
            epic_id: Epic identifier
            story_statuses: Story status mapping
            final_state: Workflow final state
        """
        parallel = yaml_data.setdefault("parallel_development", {})
        current_sprint = parallel.setdefault("current_sprint", {})
        final_status = final_state.get("final_status", "unknown")

        if final_status in ("success", "partial_success"):
            # Workflow completed - reset sprint
            current_sprint["sprint_id"] = None
            current_sprint["phase"] = None
            current_sprint["total_stories"] = 0
            current_sprint["started_at"] = None
        else:
            # Workflow incomplete - preserve for resume
            current_sprint["sprint_id"] = f"epic-{epic_id}"
            current_sprint["phase"] = final_state.get("current_phase", "unknown").lower()
            current_sprint["total_stories"] = len(story_statuses)

        # Update worktrees
        worktrees = parallel.setdefault("worktrees", {})
        worktree_paths = final_state.get("worktree_paths", {}) or {}

        for story_id, status in story_statuses.items():
            if status == "completed":
                # Mark as completed but keep entry for history
                if story_id in worktrees:
                    worktrees[story_id]["status"] = status
                    worktrees[story_id]["completed_at"] = datetime.now().isoformat()
            else:
                # Update or create worktree entry
                wt = worktrees.setdefault(story_id, {})
                wt["status"] = status
                if story_id in worktree_paths:
                    wt["path"] = worktree_paths[story_id]
                wt["branch"] = f"develop-{story_id}"

    def _should_update_status(self, new_status: StoryStatus, existing: str) -> bool:
        """
        Determine if story status should be updated (prevent downgrade).

        Args:
            new_status: New status to set
            existing: Existing status string (may include emoji)

        Returns:
            True if should update, False otherwise
        """
        # Extract status from existing (strip emoji)
        existing_status = self._extract_status_from_emoji(existing)

        new_priority = self.STATUS_PRIORITY.get(new_status, 0)
        existing_priority = self.STATUS_PRIORITY.get(existing_status, 0)

        # Allow update if new status is higher priority
        return new_priority >= existing_priority

    def _status_to_emoji(self, status: StoryStatus) -> str:
        """Convert status to display emoji."""
        return {
            "completed": "\u2705",
            "blocked": "\u274c",
            "in-progress": "\ud83d\udd04",
            "dev-complete": "\ud83d\udd04",
            "qa-review": "\ud83d\udd04",
            "draft": "\u23f3",
            "pending": "\u23f3",
        }.get(status, "\u23f3")

    def _strip_emoji(self, text: str) -> str:
        """Strip emoji markers from text."""
        if not text:
            return ""
        # Remove common status emojis
        for emoji in ["\u2705", "\u274c", "\ud83d\udd04", "\u23f3", " "]:
            text = text.replace(emoji, "")
        return text.strip()

    def _extract_status_from_emoji(self, text: str) -> str:
        """Extract status from emoji-marked text."""
        if not text:
            return "pending"
        if "\u2705" in str(text):
            return "completed"
        if "\u274c" in str(text):
            return "blocked"
        if "\ud83d\udd04" in str(text):
            return "in-progress"
        if "\u23f3" in str(text):
            return "draft"
        return "pending"

    def _load_yaml(self) -> Dict:
        """Load YAML file."""
        if self.yaml_file.exists():
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return self._create_minimal_yaml()

    def _save_yaml(self, data: Dict) -> None:
        """Save YAML file with safe formatting."""
        with open(self.yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def _create_minimal_yaml(self) -> Dict:
        """Create minimal YAML structure."""
        return {
            "project": {
                "name": "Canvas Learning System",
                "version": "v1.3",
                "current_phase": "implementation",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
            },
            "epics": {},
            "parallel_development": {
                "enabled": True,
                "version": "1.0.0",
                "status_definitions": {
                    "pending": "Story not yet started",
                    "draft": "Story being drafted by @sm",
                    "in-progress": "Story being developed by @dev",
                    "dev-complete": "Development done, awaiting QA",
                    "qa-review": "Under QA review",
                    "completed": "Fully completed and merged",
                    "blocked": "Blocked by dependency or issue",
                },
                "current_sprint": {},
                "worktrees": {},
            },
        }

    def _create_backup(self) -> Optional[Path]:
        """Create timestamped backup."""
        if not self.yaml_file.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.yaml_file.with_suffix(f".{timestamp}.bak")
        try:
            shutil.copy2(self.yaml_file, backup_path)
            return backup_path
        except Exception as e:
            print(f"[StatusPersister] [WARN] Failed to create backup: {e}")
            return None

    def _restore_backup(self, backup_path: Path) -> bool:
        """Restore YAML from backup."""
        try:
            shutil.copy2(backup_path, self.yaml_file)
            return True
        except Exception:
            return False
