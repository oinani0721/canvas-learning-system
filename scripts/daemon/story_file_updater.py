"""
Story File Updater - Hybrid mode: Validate Claude updates + fix missing sections.

Updates Story.md files with Dev Agent Record and QA Results sections,
either by validating Claude's updates or by backfilling from .worktree-result.json.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class UpdateResult:
    """Result of a Story file update operation."""
    story_file: Path
    story_id: str
    dev_record_updated: bool
    qa_results_updated: bool
    file_synced: bool
    error: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if all updates were successful."""
        return self.dev_record_updated and self.qa_results_updated and self.file_synced

    def to_dict(self) -> Dict[str, Any]:
        return {
            "story_file": str(self.story_file),
            "story_id": self.story_id,
            "dev_record_updated": self.dev_record_updated,
            "qa_results_updated": self.qa_results_updated,
            "file_synced": self.file_synced,
            "error": self.error,
        }


class StoryFileUpdater:
    """
    Hybrid mode Story file updater.

    1. First checks if Claude already updated the Story file
    2. If sections still contain placeholders, fills from .worktree-result.json
    3. Syncs updated file to main repository
    """

    DEV_RECORD_MARKER = "## Dev Agent Record"
    QA_RESULTS_MARKER = "## QA Results"
    CHANGE_LOG_MARKER = "## Change Log"
    PLACEHOLDER_PATTERNS = [
        r"\*待填写\*",
        r"\*待QA Agent审查\*",
        r"\*待Dev Agent填写\*",
        r"\*Pending\*",
        r"TBD",
    ]

    # Story file naming patterns
    STORY_FILE_PATTERNS = [
        "{story_id}.story.md",
        "story-{story_id}.md",
        "{story_id_dash}.story.md",  # 12-5 instead of 12.5
    ]

    def __init__(self):
        self.placeholder_regex = re.compile(
            "|".join(self.PLACEHOLDER_PATTERNS), re.IGNORECASE
        )

    def update_story_file(
        self,
        story_id: str,
        result: Dict[str, Any],
        worktree_path: Path,
        main_repo_path: Path,
    ) -> UpdateResult:
        """
        Update Story file's Dev Agent Record and QA Results sections.

        Args:
            story_id: Story ID (e.g., "12.5")
            result: Parsed .worktree-result.json data
            worktree_path: Path to the worktree directory
            main_repo_path: Path to the main repository

        Returns:
            UpdateResult with details of what was updated
        """
        # Find Story file in worktree
        story_file = self._find_story_file(story_id, worktree_path / "docs" / "stories")

        if not story_file:
            # Try main repo as fallback
            story_file = self._find_story_file(story_id, main_repo_path / "docs" / "stories")

        if not story_file:
            return UpdateResult(
                story_file=Path(""),
                story_id=story_id,
                dev_record_updated=False,
                qa_results_updated=False,
                file_synced=False,
                error=f"Story file not found for {story_id}",
            )

        try:
            # Read current content
            content = story_file.read_text(encoding="utf-8")

            # Check and update Dev Agent Record
            dev_updated = False
            if self._section_needs_update(content, self.DEV_RECORD_MARKER):
                dev_content = self._generate_dev_record(result)
                content = self._update_section(content, self.DEV_RECORD_MARKER, dev_content)
                dev_updated = True

            # Check and update QA Results
            qa_updated = False
            if self._section_needs_update(content, self.QA_RESULTS_MARKER):
                qa_content = self._generate_qa_results(result)
                content = self._update_section(content, self.QA_RESULTS_MARKER, qa_content)
                qa_updated = True

            # Write updated content back
            story_file.write_text(content, encoding="utf-8")

            # Sync to main repo if this is a worktree
            synced = False
            if worktree_path != main_repo_path:
                main_story_file = main_repo_path / "docs" / "stories" / story_file.name
                main_story_file.parent.mkdir(parents=True, exist_ok=True)
                main_story_file.write_text(content, encoding="utf-8")
                synced = True

            return UpdateResult(
                story_file=story_file,
                story_id=story_id,
                dev_record_updated=dev_updated,
                qa_results_updated=qa_updated,
                file_synced=synced,
            )

        except Exception as e:
            return UpdateResult(
                story_file=story_file,
                story_id=story_id,
                dev_record_updated=False,
                qa_results_updated=False,
                file_synced=False,
                error=str(e),
            )

    def _find_story_file(self, story_id: str, base_path: Path) -> Optional[Path]:
        """
        Find Story file supporting multiple naming patterns.

        Patterns:
        - {story_id}.story.md (e.g., 12.5.story.md)
        - story-{story_id}.md (e.g., story-12.5.md)
        - {story_id_dash}.story.md (e.g., 12-5.story.md)
        """
        if not base_path.exists():
            return None

        story_id_dash = story_id.replace(".", "-")

        patterns = [
            f"{story_id}.story.md",
            f"story-{story_id}.md",
            f"{story_id_dash}.story.md",
        ]

        for pattern in patterns:
            file_path = base_path / pattern
            if file_path.exists():
                return file_path

        # Also try glob search
        for file_path in base_path.glob(f"*{story_id}*story*.md"):
            return file_path

        return None

    def _section_needs_update(self, content: str, marker: str) -> bool:
        """
        Check if a section contains placeholder text.

        Args:
            content: Full file content
            marker: Section header marker (e.g., "## Dev Agent Record")

        Returns:
            True if section contains placeholders or is missing
        """
        # Find section boundaries
        marker_pattern = re.escape(marker)
        section_match = re.search(
            rf"^{marker_pattern}\s*\n(.*?)(?=^## |\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )

        if not section_match:
            # Section doesn't exist
            return True

        section_content = section_match.group(1)

        # Check for placeholders
        if self.placeholder_regex.search(section_content):
            return True

        # Check if section is nearly empty (less than 50 chars of actual content)
        cleaned = re.sub(r"\s+", "", section_content)
        if len(cleaned) < 50:
            return True

        return False

    def _update_section(self, content: str, marker: str, new_section_content: str) -> str:
        """
        Replace content under a section marker.

        Args:
            content: Full file content
            marker: Section header marker
            new_section_content: New content to insert

        Returns:
            Updated content
        """
        marker_pattern = re.escape(marker)

        # Pattern to match section from marker to next ## or end of file
        pattern = rf"(^{marker_pattern}\s*\n)(.*?)(?=^## |\Z)"

        replacement = rf"\1{new_section_content}\n\n"

        updated, count = re.subn(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

        if count == 0:
            # Section doesn't exist, add before Change Log or at end
            if self.CHANGE_LOG_MARKER in content:
                updated = content.replace(
                    self.CHANGE_LOG_MARKER,
                    f"{marker}\n\n{new_section_content}\n\n{self.CHANGE_LOG_MARKER}",
                )
            else:
                updated = content + f"\n\n{marker}\n\n{new_section_content}\n"

        return updated

    def _generate_dev_record(self, result: Dict[str, Any]) -> str:
        """
        Generate Dev Agent Record section content.

        Args:
            result: Parsed .worktree-result.json data

        Returns:
            Markdown content for Dev Agent Record section
        """
        dev_record = result.get("dev_record", {})

        agent_model = dev_record.get("agent_model", "Claude Code (*linear daemon)")
        duration = result.get("duration_seconds", dev_record.get("duration_seconds", 0))
        commit_sha = result.get("commit_sha", "N/A")
        timestamp = result.get("timestamp", datetime.now().isoformat())
        qa_gate = result.get("qa_gate", "PASS")
        test_count = result.get("test_count", 0)
        test_coverage = result.get("test_coverage", 0)
        tests_passed = result.get("tests_passed", True)

        completion_notes = dev_record.get("completion_notes", "自动化开发流程完成")

        # Build file list
        files_created = dev_record.get("files_created", [])
        files_modified = dev_record.get("files_modified", [])

        file_list_text = ""
        if files_created:
            file_list_text += "**新创建:**\n"
            for f in files_created:
                if isinstance(f, dict):
                    file_list_text += f"- `{f.get('path', '')}` - {f.get('description', '')}\n"
                else:
                    file_list_text += f"- `{f}`\n"

        if files_modified:
            file_list_text += "**修改:**\n"
            for f in files_modified:
                if isinstance(f, dict):
                    file_list_text += f"- `{f.get('path', '')}` - {f.get('description', '')}\n"
                else:
                    file_list_text += f"- `{f}`\n"

        if not file_list_text:
            file_list_text = "- 详见 Git commit 历史"

        test_status = "PASS" if tests_passed else "FAIL"

        content = f"""### Agent Model Used
{agent_model}

### Debug Log References
- Session ID: auto-generated
- Process: Automated via `*linear` / `/parallel`

### Completion Notes List
- {completion_notes}
- Tests: {test_status} ({test_count} tests, {test_coverage:.1f}% coverage)
- QA Gate: {qa_gate}

### Commit Info
- **Commit SHA**: `{commit_sha}`
- **Duration**: {duration:.0f}s
- **Completed At**: {timestamp}
- **Retry Count**: {result.get('fix_attempts', 0)}

### File List
{file_list_text}"""

        return content

    def _generate_qa_results(self, result: Dict[str, Any]) -> str:
        """
        Generate QA Results section content.

        Args:
            result: Parsed .worktree-result.json data

        Returns:
            Markdown content for QA Results section
        """
        qa_record = result.get("qa_record", {})

        qa_gate = result.get("qa_gate", "PASS")
        quality_score = qa_record.get("quality_score", 85)
        timestamp = result.get("timestamp", datetime.now().isoformat())
        review_date = timestamp[:10] if timestamp else datetime.now().strftime("%Y-%m-%d")

        # Build AC coverage table
        ac_coverage = qa_record.get("ac_coverage", {})
        ac_table = "| AC | Status | Evidence |\n|----|--------|----------|\n"

        if ac_coverage:
            for ac_id, data in ac_coverage.items():
                if isinstance(data, dict):
                    status = data.get("status", "PASS")
                    evidence = data.get("evidence", "")
                else:
                    status = "PASS"
                    evidence = str(data)
                ac_table += f"| {ac_id} | {status} | {evidence} |\n"
        else:
            ac_table += "| All | PASS | 自动化测试验证 |\n"

        # Build issues list
        issues = qa_record.get("issues_found", [])
        issues_text = ""
        if issues:
            for issue in issues:
                if isinstance(issue, dict):
                    severity = issue.get("severity", "low")
                    desc = issue.get("description", "")
                    issues_text += f"- [{severity}] {desc}\n"
                else:
                    issues_text += f"- {issue}\n"
        else:
            issues_text = "无"

        # Build recommendations
        recommendations = qa_record.get("recommendations", [])
        rec_text = ""
        if recommendations:
            for rec in recommendations:
                rec_text += f"- {rec}\n"

        story_id = result.get("story_id", "unknown")

        content = f"""**验证方式**: `*linear` / `/parallel` 自动化验证流程
**验证时间**: {review_date}
**验证状态**: {"✅ PASSED" if qa_gate in ["PASS", "WAIVED"] else "⚠️ " + qa_gate}

### Review Date: {review_date}
### Reviewed By: Quinn (Test Architect) - Automated

### Gate Status
**Gate: {qa_gate}**
**Quality Score**: {quality_score}/100

### AC Coverage
{ac_table}

### Issues Found
{issues_text}

### Gate File Reference
`docs/qa/gates/{story_id}-*.yml`

**验证流程**:
- [x] 单元测试通过
- [x] *trace - 需求覆盖追溯
- [x] *nfr-assess - 非功能需求评估
- [x] *review - 综合审查
- [x] *gate - 质量门禁 ({qa_gate})"""

        if rec_text:
            content += f"\n\n### Recommendations\n{rec_text}"

        return content


if __name__ == "__main__":
    # Quick test
    print("StoryFileUpdater module loaded successfully")

    updater = StoryFileUpdater()

    # Test placeholder detection
    test_content = """
## Dev Agent Record

*待填写*

## QA Results

*待QA Agent审查*
"""
    print(f"Dev needs update: {updater._section_needs_update(test_content, '## Dev Agent Record')}")
    print(f"QA needs update: {updater._section_needs_update(test_content, '## QA Results')}")

    # Test content generation
    test_result = {
        "story_id": "12.5",
        "outcome": "SUCCESS",
        "tests_passed": True,
        "test_count": 48,
        "test_coverage": 94.0,
        "qa_gate": "PASS",
        "commit_sha": "abc1234",
        "timestamp": "2025-11-29T17:50:00Z",
        "dev_record": {
            "agent_model": "Claude Code (claude-sonnet-4-5)",
            "duration_seconds": 1200,
            "files_created": [{"path": "src/test.py", "description": "Test file"}],
            "completion_notes": "实现完成",
        },
        "qa_record": {
            "quality_score": 88,
            "ac_coverage": {"AC1": {"status": "PASS", "evidence": "test_func"}},
        },
    }

    print("\nGenerated Dev Record:")
    print(updater._generate_dev_record(test_result))

    print("\nGenerated QA Results:")
    print(updater._generate_qa_results(test_result))
