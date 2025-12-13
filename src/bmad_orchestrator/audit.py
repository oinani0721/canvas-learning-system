"""
执行审计日志模块 - BMad Orchestrator

Epic 改进: *epic-develop 命令真正自动化 BMad Agents
Phase 2: 执行审计

提供完整的工作流执行审计能力，追踪每个步骤的执行状态。

核心组件:
- AuditEntry: 单个审计条目
- ExecutionAuditLog: 完整审计日志管理
- AuditReport: 审计报告生成

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-13
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Audit Entry
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AuditEntry:
    """
    单个审计条目

    记录单个节点的执行状态。

    Attributes:
        timestamp: 时间戳
        node_name: 节点名称
        status: 执行状态 ("executed" | "skipped" | "failed")
        reason: 状态原因
        artifacts: 产出的文件路径列表
        duration_ms: 执行时长（毫秒）
        error_message: 错误信息（如果有）
        metadata: 其他元数据
    """
    timestamp: datetime
    node_name: str
    status: str  # "executed" | "skipped" | "failed"
    reason: str
    artifacts: List[str] = field(default_factory=list)
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        """从字典创建"""
        data = data.copy()
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# Execution Audit Log
# ═══════════════════════════════════════════════════════════════════════════════

class ExecutionAuditLog:
    """
    执行审计日志

    管理完整 Epic 开发周期的审计记录。

    主要功能:
    - log_execution(): 记录成功执行
    - log_skip(): 记录跳过
    - log_failure(): 记录失败
    - to_markdown(): 生成 Markdown 报告
    - save(): 保存审计日志
    - load(): 加载审计日志

    使用示例:
    ```python
    audit = ExecutionAuditLog(epic_id="24")
    audit.log_execution("sm_node", ["docs/stories/24.1.story.md"])
    audit.log_execution("po_node", [])
    audit.log_skip("sdd_pre_validation_node", "Fast mode enabled")
    report = audit.to_markdown()
    audit.save(Path("logs/epic-24-audit.json"))
    ```
    """

    # BMad 标准节点顺序
    STANDARD_NODE_ORDER = [
        "sm_node",           # SM: Story 创建
        "po_node",           # PO: Story 验证
        "analysis_node",     # 依赖分析
        "sdd_pre_validation_node",  # SDD 预验证
        "dev_node",          # DEV: 开发
        "qa_node",           # QA: 审查
        "sdd_validation_node",  # SDD 后验证
        "merge_node",        # 合并
        "commit_node",       # 提交
    ]

    def __init__(self, epic_id: str, project_root: Optional[Path] = None):
        """
        初始化审计日志

        Args:
            epic_id: Epic 标识符
            project_root: 项目根目录
        """
        self.epic_id = epic_id
        self.project_root = project_root or Path.cwd()
        self.entries: List[AuditEntry] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.story_ids: List[str] = []
        self.metadata: Dict[str, Any] = {}

        logger.info(f"[AuditLog] 创建 Epic {epic_id} 审计日志")

    def log_execution(
        self,
        node: str,
        artifacts: List[str],
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录成功执行

        Args:
            node: 节点名称
            artifacts: 产出文件列表
            duration_ms: 执行时长
            metadata: 额外元数据
        """
        entry = AuditEntry(
            timestamp=datetime.now(),
            node_name=node,
            status="executed",
            reason="Normal execution",
            artifacts=artifacts,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        logger.info(f"[AuditLog] ✅ 节点执行完成: {node}")

    def log_skip(self, node: str, reason: str) -> None:
        """
        记录跳过

        Args:
            node: 节点名称
            reason: 跳过原因
        """
        entry = AuditEntry(
            timestamp=datetime.now(),
            node_name=node,
            status="skipped",
            reason=reason,
            artifacts=[]
        )
        self.entries.append(entry)
        logger.info(f"[AuditLog] ⏭️ 节点跳过: {node} - {reason}")

    def log_failure(
        self,
        node: str,
        error_message: str,
        reason: str = "Execution failed"
    ) -> None:
        """
        记录失败

        Args:
            node: 节点名称
            error_message: 错误信息
            reason: 失败原因
        """
        entry = AuditEntry(
            timestamp=datetime.now(),
            node_name=node,
            status="failed",
            reason=reason,
            artifacts=[],
            error_message=error_message
        )
        self.entries.append(entry)
        logger.error(f"[AuditLog] ❌ 节点失败: {node} - {error_message}")

    def finalize(self) -> None:
        """完成审计日志"""
        self.end_time = datetime.now()
        logger.info(f"[AuditLog] 审计日志完成，共 {len(self.entries)} 个条目")

    def get_executed_nodes(self) -> List[str]:
        """获取已执行的节点列表"""
        return [e.node_name for e in self.entries if e.status == "executed"]

    def get_skipped_nodes(self) -> List[str]:
        """获取跳过的节点列表"""
        return [e.node_name for e in self.entries if e.status == "skipped"]

    def get_failed_nodes(self) -> List[str]:
        """获取失败的节点列表"""
        return [e.node_name for e in self.entries if e.status == "failed"]

    def check_workflow_compliance(self) -> Dict[str, Any]:
        """
        检查工作流合规性

        验证是否遵循了 BMad 标准流程。

        Returns:
            合规性检查结果
        """
        executed = set(self.get_executed_nodes())
        skipped = set(self.get_skipped_nodes())
        failed = set(self.get_failed_nodes())

        # 必须执行的核心节点
        required_nodes = {"sm_node", "po_node", "dev_node", "qa_node", "commit_node"}
        missing_required = required_nodes - executed - skipped

        # 检查执行顺序
        executed_list = self.get_executed_nodes()
        order_violations = []
        for i, node in enumerate(executed_list):
            if node in self.STANDARD_NODE_ORDER:
                expected_idx = self.STANDARD_NODE_ORDER.index(node)
                for _j, prev_node in enumerate(executed_list[:i]):
                    if prev_node in self.STANDARD_NODE_ORDER:
                        prev_expected_idx = self.STANDARD_NODE_ORDER.index(prev_node)
                        if prev_expected_idx > expected_idx:
                            order_violations.append(
                                f"{prev_node} 应在 {node} 之后执行"
                            )

        compliance = {
            "compliant": len(missing_required) == 0 and len(order_violations) == 0,
            "executed_nodes": list(executed),
            "skipped_nodes": list(skipped),
            "failed_nodes": list(failed),
            "missing_required": list(missing_required),
            "order_violations": order_violations,
            "total_entries": len(self.entries),
        }

        return compliance

    def to_markdown(self) -> str:
        """
        生成 Markdown 审计报告

        Returns:
            Markdown 格式的审计报告
        """
        lines = [
            f"# Epic {self.epic_id} 执行审计报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**开始时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            lines.append(f"**结束时间**: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**总时长**: {duration:.1f} 秒")

        if self.story_ids:
            lines.append(f"**Stories**: {', '.join(self.story_ids)}")

        lines.extend(["", "---", "", "## 执行摘要", ""])

        # 统计
        executed = len([e for e in self.entries if e.status == "executed"])
        skipped = len([e for e in self.entries if e.status == "skipped"])
        failed = len([e for e in self.entries if e.status == "failed"])

        lines.append("| 状态 | 数量 |")
        lines.append("|------|------|")
        lines.append(f"| ✅ 执行 | {executed} |")
        lines.append(f"| ⏭️ 跳过 | {skipped} |")
        lines.append(f"| ❌ 失败 | {failed} |")
        lines.append(f"| **总计** | {len(self.entries)} |")

        # 合规性检查
        compliance = self.check_workflow_compliance()
        lines.extend(["", "## 工作流合规性", ""])

        if compliance["compliant"]:
            lines.append("✅ **工作流完全合规**")
        else:
            lines.append("⚠️ **工作流存在问题**")
            if compliance["missing_required"]:
                lines.append(f"- 缺失必要节点: {', '.join(compliance['missing_required'])}")
            if compliance["order_violations"]:
                lines.append("- 执行顺序问题:")
                for violation in compliance["order_violations"]:
                    lines.append(f"  - {violation}")

        # 详细条目
        lines.extend(["", "## 详细执行记录", ""])

        for entry in self.entries:
            status_emoji = {
                "executed": "✅",
                "skipped": "⏭️",
                "failed": "❌"
            }.get(entry.status, "❓")

            lines.append(f"### {status_emoji} {entry.node_name}")
            lines.append("")
            lines.append(f"- **时间**: {entry.timestamp.strftime('%H:%M:%S')}")
            lines.append(f"- **状态**: {entry.status}")
            lines.append(f"- **原因**: {entry.reason}")

            if entry.duration_ms:
                lines.append(f"- **时长**: {entry.duration_ms} ms")

            if entry.artifacts:
                lines.append("- **产出**:")
                for artifact in entry.artifacts:
                    lines.append(f"  - `{artifact}`")

            if entry.error_message:
                lines.append(f"- **错误**: {entry.error_message}")

            lines.append("")

        # 页脚
        lines.extend([
            "---",
            "",
            "🤖 Generated by BMad Orchestrator Audit System",
        ])

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "epic_id": self.epic_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "story_ids": self.story_ids,
            "metadata": self.metadata,
            "entries": [e.to_dict() for e in self.entries],
            "compliance": self.check_workflow_compliance(),
        }

    def save(self, path: Path) -> None:
        """
        保存审计日志

        Args:
            path: 保存路径
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"[AuditLog] 审计日志已保存: {path}")

    def save_markdown(self, path: Path) -> None:
        """
        保存 Markdown 报告

        Args:
            path: 保存路径
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())
        logger.info(f"[AuditLog] Markdown 报告已保存: {path}")

    @classmethod
    def load(cls, path: Path) -> "ExecutionAuditLog":
        """
        加载审计日志

        Args:
            path: 日志文件路径

        Returns:
            ExecutionAuditLog 实例
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        audit = cls(epic_id=data["epic_id"])
        audit.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            audit.end_time = datetime.fromisoformat(data["end_time"])
        audit.story_ids = data.get("story_ids", [])
        audit.metadata = data.get("metadata", {})
        audit.entries = [AuditEntry.from_dict(e) for e in data.get("entries", [])]

        logger.info(f"[AuditLog] 审计日志已加载: {path}")
        return audit


# ═══════════════════════════════════════════════════════════════════════════════
# Audit Log Factory
# ═══════════════════════════════════════════════════════════════════════════════

def create_audit_log(
    epic_id: str,
    story_ids: Optional[List[str]] = None,
    project_root: Optional[Path] = None
) -> ExecutionAuditLog:
    """
    创建审计日志实例

    Args:
        epic_id: Epic ID
        story_ids: Story ID 列表
        project_root: 项目根目录

    Returns:
        ExecutionAuditLog 实例
    """
    audit = ExecutionAuditLog(epic_id=epic_id, project_root=project_root)
    if story_ids:
        audit.story_ids = story_ids
    return audit


__all__ = [
    "AuditEntry",
    "ExecutionAuditLog",
    "create_audit_log",
]
