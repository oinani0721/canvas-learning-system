"""
BMad Workflow Enforcer - 工作流状态机强制执行

确保 Story 严格遵循 BMad 工作流:
Draft → Approved → InProgress → Review → Done

⚠️ 关键特性：
- Epic 1-20 跳过验证 (遗留数据)
- Epic 21+ 强制验证，无法绕过
- Pre-commit Hook 和 Commit Gate G11/G12 双重验证

验证检查项:
- G11: Workflow Status - Story 状态必须 >= Review
- G12: Status Consistency - Story 文件状态 = YAML 状态

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-11
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# ============================================================================
# 状态枚举和转换规则
# ============================================================================


class StoryStatus(Enum):
    """Story 工作流状态"""
    DRAFT = "Draft"
    APPROVED = "Approved"
    IN_PROGRESS = "InProgress"
    REVIEW = "Review"
    DONE = "Done"
    UNKNOWN = "Unknown"

    @classmethod
    def from_string(cls, value: str) -> "StoryStatus":
        """从字符串解析状态"""
        value_lower = value.lower().strip()

        # 映射各种可能的格式
        status_map = {
            "draft": cls.DRAFT,
            "approved": cls.APPROVED,
            "ready for dev": cls.APPROVED,
            "ready": cls.APPROVED,
            "in_progress": cls.IN_PROGRESS,
            "inprogress": cls.IN_PROGRESS,
            "in progress": cls.IN_PROGRESS,
            "dev": cls.IN_PROGRESS,
            "development": cls.IN_PROGRESS,
            "review": cls.REVIEW,
            "qa review": cls.REVIEW,
            "qa": cls.REVIEW,
            "done": cls.DONE,
            "completed": cls.DONE,
            "complete": cls.DONE,
        }

        return status_map.get(value_lower, cls.UNKNOWN)


# 允许的状态转换
ALLOWED_TRANSITIONS: Dict[StoryStatus, List[StoryStatus]] = {
    StoryStatus.DRAFT: [StoryStatus.APPROVED],
    StoryStatus.APPROVED: [StoryStatus.IN_PROGRESS],
    StoryStatus.IN_PROGRESS: [StoryStatus.REVIEW],
    StoryStatus.REVIEW: [StoryStatus.DONE, StoryStatus.IN_PROGRESS],  # 允许退回
    StoryStatus.DONE: [],  # 终态
    StoryStatus.UNKNOWN: list(StoryStatus),  # Unknown 可以转到任何状态
}

# 允许提交的最小状态
COMMIT_READY_STATUSES = {StoryStatus.REVIEW, StoryStatus.DONE}


# ============================================================================
# 数据类
# ============================================================================


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    story_id: str
    current_status: Optional[StoryStatus]
    expected_statuses: List[StoryStatus]
    error_message: str
    details: Dict[str, Any]


@dataclass
class WorkflowPhase:
    """工作流阶段信息"""
    name: str
    completed: bool
    evidence: Optional[str] = None


# ============================================================================
# Audit Logger (工作流专用)
# ============================================================================


class WorkflowAuditLogger:
    """工作流审计日志记录器"""

    def __init__(self, log_path: Optional[Path] = None):
        if log_path is None:
            project_root = Path(__file__).parent.parent.parent
            log_path = project_root / "logs" / "workflow-gate-audit.jsonl"

        self.log_path = log_path
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """确保日志目录存在"""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        event: str,
        story_id: str,
        data: Optional[Dict[str, Any]] = None,
        action: str = "INFO",
    ):
        """记录工作流事件"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "story_id": story_id,
            "action": action,
            "data": data or {},
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[WorkflowAuditLogger] Warning: Failed to write log: {e}")


# ============================================================================
# WorkflowEnforcer 主类
# ============================================================================


class WorkflowEnforcer:
    """
    🔒 BMad 工作流强制执行器

    确保所有 Story 开发严格遵循工作流:
    SM Draft → PO Approve → DEV Develop → QA Review → Merge → Commit

    ⚠️ 关键规则：
    - Epic 1-20: 跳过验证 (遗留数据)
    - Epic 21+: 强制验证，任何情况都不能绕过

    Usage:
    ```python
    enforcer = WorkflowEnforcer(base_path)

    # 验证是否可以提交
    result = enforcer.validate_commit_ready("21.1")
    if not result.passed:
        print(f"BLOCKED: {result.error_message}")
        # 阻止提交
    ```
    """

    # 所有Epic都需要验证 (已移除Legacy Bypass - Epic 20补全修复)
    LEGACY_EPIC_THRESHOLD = 0

    def __init__(self, base_path: Optional[Path] = None):
        """
        Args:
            base_path: 项目根目录，默认自动检测
        """
        if base_path is None:
            # 自动检测项目根目录
            base_path = Path(__file__).parent.parent.parent

        self.base_path = Path(base_path)
        self.audit = WorkflowAuditLogger()

        # 路径配置
        self.stories_dir = self.base_path / "docs" / "stories"
        self.yaml_status_path = self.base_path / ".bmad-core" / "data" / "canvas-project-status.yaml"

    # ========================================================================
    # 公开 API
    # ========================================================================

    def is_legacy_epic(self, story_id: str) -> bool:
        """
        检查是否为遗留 Epic (已禁用 - 所有Epic都需验证)

        Args:
            story_id: Story ID (e.g., "21.1", "5.3")

        Returns:
            True 如果是遗留Epic (当前: 永远返回False，所有Epic都验证)
        """
        try:
            epic_num = int(story_id.split(".")[0])
            return epic_num < self.LEGACY_EPIC_THRESHOLD
        except (ValueError, IndexError):
            # 无法解析时默认为遗留
            return True

    def parse_story_status(self, story_id: str) -> Tuple[StoryStatus, Dict[str, Any]]:
        """
        从 Story markdown 文件解析状态

        Args:
            story_id: Story ID (e.g., "21.1")

        Returns:
            Tuple of (status, metadata)
        """
        # 尝试多种文件名格式
        possible_files = [
            self.stories_dir / f"{story_id}.story.md",
            self.stories_dir / f"story-{story_id}.md",
            self.stories_dir / f"Story-{story_id}.md",
        ]

        story_file = None
        for f in possible_files:
            if f.exists():
                story_file = f
                break

        if story_file is None:
            return StoryStatus.UNKNOWN, {"error": "Story file not found"}

        try:
            content = story_file.read_text(encoding="utf-8")
            return self._parse_story_content(content)
        except Exception as e:
            return StoryStatus.UNKNOWN, {"error": str(e)}

    def get_yaml_status(self, story_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        从 YAML 状态文件获取 Story 状态

        Args:
            story_id: Story ID (e.g., "21.1")

        Returns:
            Tuple of (status_string, metadata)
        """
        if not self.yaml_status_path.exists():
            return "unknown", {"error": "YAML status file not found"}

        try:
            with open(self.yaml_status_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            epic_num = story_id.split(".")[0]
            epic_key = f"epic-{epic_num}"

            if "epics" not in data:
                return "unknown", {"error": "No epics section in YAML"}

            epic_data = data["epics"].get(epic_key, {})
            if not epic_data:
                return "unknown", {"error": f"Epic {epic_num} not found in YAML"}

            # 从 stories 列表中查找状态
            stories = epic_data.get("stories", [])
            story_num = story_id.split(".")[1] if "." in story_id else "1"

            # 查找 story 状态
            for story in stories:
                if isinstance(story, dict):
                    if story.get("id") == story_id or story.get("id") == story_num:
                        return story.get("status", "unknown"), story
                elif isinstance(story, str):
                    # 简单格式: ["21.1", "21.2"]
                    if story == story_id or story == story_num:
                        return epic_data.get("status", "unknown"), {"id": story}

            # 如果没有找到具体 story，返回 epic 状态
            return epic_data.get("status", "unknown"), {"epic_status": True}

        except Exception as e:
            return "unknown", {"error": str(e)}

    def validate_transition(
        self,
        from_status: StoryStatus,
        to_status: StoryStatus,
    ) -> Tuple[bool, str]:
        """
        验证状态转换是否合法

        Args:
            from_status: 当前状态
            to_status: 目标状态

        Returns:
            Tuple of (is_valid, error_message)
        """
        allowed = ALLOWED_TRANSITIONS.get(from_status, [])

        if to_status in allowed:
            return True, ""

        error_msg = (
            f"Invalid transition: {from_status.value} → {to_status.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )
        return False, error_msg

    def validate_commit_ready(self, story_id: str) -> ValidationResult:
        """
        验证 Story 是否可以提交

        ⚠️ 这是 Pre-commit Hook 和 Commit Gate G11/G12 调用的核心方法

        Args:
            story_id: Story ID (e.g., "21.1")

        Returns:
            ValidationResult with pass/fail and details
        """
        # 检查遗留 Epic
        if self.is_legacy_epic(story_id):
            self.audit.log(
                "LEGACY_EPIC_SKIP",
                story_id,
                {"reason": f"Epic {story_id.split('.')[0]} < {self.LEGACY_EPIC_THRESHOLD}"},
                "SKIP",
            )
            return ValidationResult(
                passed=True,
                story_id=story_id,
                current_status=None,
                expected_statuses=[],
                error_message="",
                details={"skipped": True, "reason": "Legacy Epic (1-20)"},
            )

        # 解析 Story 文件状态
        story_status, story_meta = self.parse_story_status(story_id)

        # 获取 YAML 状态
        yaml_status_str, yaml_meta = self.get_yaml_status(story_id)
        yaml_status = StoryStatus.from_string(yaml_status_str)

        # 收集详细信息
        details = {
            "story_file_status": story_status.value,
            "yaml_status": yaml_status_str,
            "story_meta": story_meta,
            "yaml_meta": yaml_meta,
        }

        # G11: 检查状态是否达到 Review 或 Done
        if story_status not in COMMIT_READY_STATUSES:
            error_msg = self._build_workflow_error_message(story_id, story_status)

            self.audit.log(
                "WORKFLOW_GATE_BLOCKED",
                story_id,
                {
                    "current_status": story_status.value,
                    "expected_status": [s.value for s in COMMIT_READY_STATUSES],
                    "error": "Story has not completed QA phase",
                },
                "COMMIT_BLOCKED",
            )

            return ValidationResult(
                passed=False,
                story_id=story_id,
                current_status=story_status,
                expected_statuses=list(COMMIT_READY_STATUSES),
                error_message=error_msg,
                details=details,
            )

        # G12: 检查状态一致性 (Story 文件 vs YAML)
        if story_status != yaml_status and yaml_status != StoryStatus.UNKNOWN:
            error_msg = (
                f"Status inconsistency detected for {story_id}:\n"
                f"  Story file status: {story_status.value}\n"
                f"  YAML status: {yaml_status_str}\n"
                f"Please sync the status before committing."
            )

            self.audit.log(
                "STATUS_INCONSISTENCY",
                story_id,
                {
                    "story_status": story_status.value,
                    "yaml_status": yaml_status_str,
                    "error": "Status mismatch between Story file and YAML",
                },
                "COMMIT_BLOCKED",
            )

            return ValidationResult(
                passed=False,
                story_id=story_id,
                current_status=story_status,
                expected_statuses=list(COMMIT_READY_STATUSES),
                error_message=error_msg,
                details=details,
            )

        # 验证通过
        self.audit.log(
            "WORKFLOW_GATE_PASSED",
            story_id,
            {
                "status": story_status.value,
                "checks": ["G11_STATUS", "G12_CONSISTENCY"],
            },
            "COMMIT_ALLOWED",
        )

        return ValidationResult(
            passed=True,
            story_id=story_id,
            current_status=story_status,
            expected_statuses=list(COMMIT_READY_STATUSES),
            error_message="",
            details=details,
        )

    def get_workflow_phases(self, story_id: str) -> List[WorkflowPhase]:
        """
        获取 Story 的工作流阶段完成情况

        用于生成用户友好的错误信息
        """
        story_status, _ = self.parse_story_status(story_id)

        phases = [
            WorkflowPhase(
                name="SM Draft",
                completed=story_status != StoryStatus.UNKNOWN,
                evidence="Story file exists" if story_status != StoryStatus.UNKNOWN else None,
            ),
            WorkflowPhase(
                name="PO Approve",
                completed=story_status in {
                    StoryStatus.APPROVED,
                    StoryStatus.IN_PROGRESS,
                    StoryStatus.REVIEW,
                    StoryStatus.DONE,
                },
            ),
            WorkflowPhase(
                name="DEV Develop",
                completed=story_status in {
                    StoryStatus.IN_PROGRESS,
                    StoryStatus.REVIEW,
                    StoryStatus.DONE,
                },
            ),
            WorkflowPhase(
                name="QA Review",
                completed=story_status in {StoryStatus.REVIEW, StoryStatus.DONE},
            ),
            WorkflowPhase(
                name="Merge",
                completed=story_status == StoryStatus.DONE,
            ),
        ]

        return phases

    # ========================================================================
    # 内部方法
    # ========================================================================

    def _parse_story_content(self, content: str) -> Tuple[StoryStatus, Dict[str, Any]]:
        """从 Story 内容解析状态"""
        metadata = {}

        # 1. 尝试从 YAML frontmatter 解析
        frontmatter_match = re.search(
            r"^---\s*\n(.*?)\n---",
            content,
            re.DOTALL,
        )
        if frontmatter_match:
            try:
                fm_data = yaml.safe_load(frontmatter_match.group(1))
                if fm_data:
                    metadata["frontmatter"] = fm_data

                    # 检查 status 字段
                    if "status" in fm_data:
                        status = StoryStatus.from_string(str(fm_data["status"]))
                        if status != StoryStatus.UNKNOWN:
                            metadata["source"] = "frontmatter"
                            return status, metadata

                    # 检查 approved 字段
                    if fm_data.get("reviewers"):
                        for reviewer in fm_data.get("reviewers", []):
                            if reviewer.get("approved"):
                                metadata["po_approved"] = True
            except yaml.YAMLError:
                pass

        # 2. 从 ## Status section 解析 checkbox
        status_section = re.search(
            r"##\s*Status\s*\n(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if status_section:
            status_text = status_section.group(1)
            metadata["status_section"] = status_text

            # 检查 checkbox 状态
            # - [x] Done
            # - [x] QA Review
            # - [x] In Progress
            # - [x] Ready for Dev
            # - [x] Draft

            checked_items = re.findall(r"-\s*\[x\]\s*(.+)", status_text, re.IGNORECASE)
            unchecked_items = re.findall(r"-\s*\[\s\]\s*(.+)", status_text, re.IGNORECASE)

            metadata["checked_items"] = checked_items
            metadata["unchecked_items"] = unchecked_items

            # 确定最高完成状态 (从高到低优先级)
            # 遍历优先级列表，找到最高级别的已选中状态
            status_priority = [
                ("done", StoryStatus.DONE),
                ("complete", StoryStatus.DONE),
                ("qa review", StoryStatus.REVIEW),
                ("review", StoryStatus.REVIEW),
                ("in progress", StoryStatus.IN_PROGRESS),
                ("development", StoryStatus.IN_PROGRESS),
                ("ready for dev", StoryStatus.APPROVED),
                ("approved", StoryStatus.APPROVED),
                ("ready", StoryStatus.APPROVED),
                ("draft", StoryStatus.DRAFT),
            ]

            # 将所有已选中的项目转换为小写用于匹配
            checked_lower = [item.lower().strip() for item in checked_items]

            # 按优先级从高到低检查，找到第一个匹配的就是最高状态
            for pattern, status in status_priority:
                for checked_item in checked_lower:
                    if pattern in checked_item:
                        metadata["source"] = "checkbox"
                        return status, metadata

        # 3. 默认返回 Draft (如果文件存在)
        metadata["source"] = "default"
        return StoryStatus.DRAFT, metadata

    def _build_workflow_error_message(
        self,
        story_id: str,
        current_status: StoryStatus,
    ) -> str:
        """构建用户友好的工作流错误消息"""
        phases = self.get_workflow_phases(story_id)

        phase_lines = []
        for phase in phases:
            icon = "[✓]" if phase.completed else "[X]"
            evidence = f" ({phase.evidence})" if phase.evidence else ""
            completion = "COMPLETED" if phase.completed else "NOT COMPLETED"
            phase_lines.append(f"    {icon} {phase.name}: {completion}{evidence}")

        error_msg = f"""
============================================================
[WORKFLOW GATE] BMad Workflow Pre-commit Validation
============================================================

[BLOCKED] Story {story_id}: Workflow status violation
  Current Status: {current_status.value}
  Expected Status: Review (or Done)

  BMad workflow requires ALL phases:

{chr(10).join(phase_lines)}

  SUGGESTION:
  - Run: /sm then *draft {story_id}
  - Run: /po then *approve {story_id}
  - Run: /dev then *develop-story {story_id}
  - Run: /qa then *review {story_id}
  - Then retry commit

============================================================
COMMIT BLOCKED - Complete BMad workflow first
============================================================
"""
        return error_msg.strip()


# ============================================================================
# 便捷函数
# ============================================================================


def validate_story_for_commit(
    story_id: str,
    base_path: Optional[Path] = None,
) -> ValidationResult:
    """
    便捷函数：验证 Story 是否可以提交

    Args:
        story_id: Story ID
        base_path: 项目根目录

    Returns:
        ValidationResult
    """
    enforcer = WorkflowEnforcer(base_path)
    return enforcer.validate_commit_ready(story_id)


def is_legacy_story(story_id: str) -> bool:
    """
    便捷函数：检查是否为遗留 Story

    Args:
        story_id: Story ID

    Returns:
        True if Epic < 21
    """
    try:
        epic_num = int(story_id.split(".")[0])
        return epic_num < WorkflowEnforcer.LEGACY_EPIC_THRESHOLD
    except (ValueError, IndexError):
        return True


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "WorkflowEnforcer",
    "StoryStatus",
    "ValidationResult",
    "WorkflowPhase",
    "WorkflowAuditLogger",
    "ALLOWED_TRANSITIONS",
    "COMMIT_READY_STATUSES",
    "validate_story_for_commit",
    "is_legacy_story",
]
