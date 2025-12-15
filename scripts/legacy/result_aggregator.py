"""
并行结果聚合系统 - 增强版

负责收集、验证、合并并行处理结果，并安全地更新Canvas文件。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
Story: 10.4 - Canvas并行处理集成引擎
"""

import json
import uuid
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from parallel_canvas_processor import ProcessingSession, ProcessingTask, CanvasUpdateResult, TaskStatus
from transaction_manager import transaction_manager

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


class ConflictResolutionStrategy(Enum):
    """冲突解决策略"""
    KEEP_FIRST = "keep_first"      # 保留第一个结果
    KEEP_LAST = "keep_last"        # 保留最后一个结果
    MERGE = "merge"                # 尝试合并
    MANUAL = "manual"              # 需要手动解决


@dataclass
class ResultConflict:
    """结果冲突"""
    node_id: str
    field_name: str
    value1: Any
    value2: Any
    task_ids: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AdvancedResultAggregator:
    """高级结果聚合器

    提供以下功能：
    - 结果收集和验证
    - 冲突检测和解决
    - 增量更新
    - 事务性文件操作
    - 结果质量评估
    """

    def __init__(self, canvas_utils):
        self.canvas_utils = canvas_utils
        self.aggregation_history: List[Dict] = []
        self.conflict_resolution_cache: Dict[str, Any] = {}

    async def aggregate_and_apply_updates(self, session: ProcessingSession) -> CanvasUpdateResult:
        """聚合结果并应用到Canvas（主要入口）"""
        logger.info(f"Aggregating results for session {session.session_id}")

        update_id = f"update-{session.session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # 1. 收集结果
            collected_results = await self._collect_results(session)
            logger.info(f"Collected {len(collected_results)} results")

            # 2. 验证结果
            validation_result = await self._validate_results(collected_results)
            if not validation_result.is_valid:
                raise Exception(f"Result validation failed: {validation_result.errors}")

            # 3. 检测冲突
            conflicts = await self._detect_conflicts(session.canvas_path, collected_results)
            logger.info(f"Detected {len(conflicts)} conflicts")

            # 4. 解决冲突
            resolved_results = await self._resolve_conflicts(collected_results, conflicts)

            # 5. 应用更新
            update_result = await self._apply_updates(session, resolved_results, update_id)

            # 6. 记录聚合历史
            self._record_aggregation(session, update_result, validation_result, conflicts)

            return update_result

        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            return CanvasUpdateResult(
                update_id=update_id,
                session_id=session.session_id,
                nodes_updated=0,
                nodes_created=0,
                edges_updated=0,
                success=False,
                error_details=[str(e)]
            )

    async def _collect_results(self, session: ProcessingSession) -> List[Dict]:
        """收集所有成功的处理结果"""
        results = []

        for task in session.tasks:
            if task.status == TaskStatus.COMPLETED and task.result:
                # 增强结果数据
                enhanced_result = {
                    **task.result,
                    "_metadata": {
                        "task_id": task.task_id,
                        "node_id": task.node_id,
                        "agent_type": task.agent_type,
                        "complexity": task.complexity.value,
                        "processing_time": (task.completed_at - task.started_at).total_seconds() if task.started_at and task.completed_at else 0,
                        "timestamp": task.completed_at.isoformat() if task.completed_at else datetime.now().isoformat()
                    }
                }
                results.append(enhanced_result)

        return results

    async def _validate_results(self, results: List[Dict]) -> ValidationResult:
        """验证结果的有效性"""
        errors = []
        warnings = []

        for result in results:
            # 验证必需字段
            if "node_id" not in result:
                errors.append(f"Missing node_id in result")
                continue

            # 验证节点ID格式
            node_id = result["node_id"]
            if not isinstance(node_id, str) or not node_id:
                errors.append(f"Invalid node_id: {node_id}")
                continue

            # 验证处理内容
            if "processed_content" not in result:
                warnings.append(f"No processed_content for node {node_id}")

            # 验证Agent类型
            if "_metadata" in result:
                agent_type = result["_metadata"].get("agent_type")
                if agent_type not in [
                    "basic-decomposition", "deep-decomposition", "oral-explanation",
                    "clarification-path", "comparison-table", "memory-anchor",
                    "four-level-explanation", "example-teaching", "scoring-agent",
                    "verification-question-agent"
                ]:
                    warnings.append(f"Unknown agent_type: {agent_type}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def _detect_conflicts(self, canvas_path: str, results: List[Dict]) -> List[ResultConflict]:
        """检测结果冲突"""
        conflicts = []
        node_updates: Dict[str, List[Dict]] = {}

        # 按节点分组结果
        for result in results:
            node_id = result["node_id"]
            if node_id not in node_updates:
                node_updates[node_id] = []
            node_updates[node_id].append(result)

        # 检测每个节点的冲突
        for node_id, updates in node_updates.items():
            if len(updates) > 1:
                # 多个结果更新同一节点，可能存在冲突
                conflict = await self._analyze_node_conflicts(node_id, updates)
                if conflict:
                    conflicts.extend(conflict)

        return conflicts

    async def _analyze_node_conflicts(self, node_id: str, updates: List[Dict]) -> List[ResultConflict]:
        """分析特定节点的冲突"""
        conflicts = []

        # 比较所有更新
        for i in range(len(updates)):
            for j in range(i + 1, len(updates)):
                update1 = updates[i]
                update2 = updates[j]

                # 检查内容冲突
                content1 = update1.get("processed_content", "")
                content2 = update2.get("processed_content", "")

                if content1 != content2:
                    # 内容不同，存在冲突
                    conflicts.append(ResultConflict(
                        node_id=node_id,
                        field_name="processed_content",
                        value1=content1,
                        value2=content2,
                        task_ids=[
                            update1["_metadata"]["task_id"],
                            update2["_metadata"]["task_id"]
                        ]
                    ))

        return conflicts

    async def _resolve_conflicts(self, results: List[Dict], conflicts: List[ResultConflict]) -> List[Dict]:
        """解决冲突"""
        if not conflicts:
            return results

        logger.info(f"Resolving {len(conflicts)} conflicts")

        # 创建节点ID到结果的映射
        node_results: Dict[str, List[Dict]] = {}
        for result in results:
            node_id = result["node_id"]
            if node_id not in node_results:
                node_results[node_id] = []
            node_results[node_id].append(result)

        # 解决每个冲突
        resolved_results = []
        processed_nodes: Set[str] = set()

        for conflict in conflicts:
            node_id = conflict.node_id
            if node_id in processed_nodes:
                continue

            updates = node_results[node_id]
            resolved_update = await self._resolve_single_conflict(node_id, updates, conflict)
            resolved_results.append(resolved_update)
            processed_nodes.add(node_id)

        # 添加没有冲突的结果
        for result in results:
            if result["node_id"] not in processed_nodes:
                resolved_results.append(result)

        return resolved_results

    async def _resolve_single_conflict(self, node_id: str, updates: List[Dict], conflict: ResultConflict) -> Dict:
        """解决单个冲突"""
        # 默认策略：选择最新的结果
        latest_update = max(updates, key=lambda u: u["_metadata"]["timestamp"])

        # 记录冲突解决
        self.conflict_resolution_cache[node_id] = {
            "conflict": conflict.__dict__,
            "resolution": ConflictResolutionStrategy.KEEP_LAST.value,
            "selected_update": latest_update["_metadata"]["task_id"],
            "timestamp": datetime.now().isoformat()
        }

        logger.warning(f"Resolved conflict for node {node_id} by selecting latest result")
        return latest_update

    async def _apply_updates(self, session: ProcessingSession, results: List[Dict], update_id: str) -> CanvasUpdateResult:
        """应用更新到Canvas文件"""
        canvas_path = session.canvas_path

        # 创建备份
        backup_path = transaction_manager.create_backup(canvas_path)

        # 使用事务管理器更新Canvas
        def update_canvas_data(current_data: Dict) -> Dict:
            """更新Canvas数据"""
            updated_data = current_data.copy()

            # 确保必要的结构存在
            if "nodes" not in updated_data:
                updated_data["nodes"] = []
            if "edges" not in updated_data:
                updated_data["edges"] = []

            nodes_map = {node["id"]: node for node in updated_data["nodes"]}

            nodes_updated = 0
            nodes_created = 0
            edges_updated = 0

            # 应用每个结果
            for result in results:
                node_id = result["node_id"]
                metadata = result.get("_metadata", {})
                agent_type = metadata.get("agent_type")

                if node_id in nodes_map:
                    # 更新现有节点
                    node = nodes_map[node_id]
                    nodes_updated += 1

                    # 根据Agent类型更新节点
                    if agent_type == "scoring-agent":
                        # 评分Agent：更新颜色
                        score = result.get("score", 0)
                        if score >= 80:
                            node["color"] = "2"  # 绿色
                        elif score >= 60:
                            node["color"] = "3"  # 紫色
                        else:
                            node["color"] = "1"  # 红色
                    else:
                        # 其他Agent：更新文本内容
                        node["text"] = result.get("processed_content", node["text"])

                else:
                    # 创建新节点
                    new_node = {
                        "id": node_id,
                        "type": "text",
                        "text": result.get("processed_content", ""),
                        "x": 100,
                        "y": 100,
                        "width": 400,
                        "height": 300,
                        "color": "2"  # 默认绿色
                    }
                    updated_data["nodes"].append(new_node)
                    nodes_created += 1

                # 根据结果创建边（如果需要）
                if "related_nodes" in result:
                    for related_id in result["related_nodes"]:
                        if related_id in nodes_map:
                            # 创建连接边
                            edge = {
                                "id": f"edge-{uuid.uuid4().hex[:16]}",
                                "fromNode": node_id,
                                "toNode": related_id,
                                "fromSide": "right",
                                "toSide": "left"
                            }
                            updated_data["edges"].append(edge)
                            edges_updated += 1

            # 更新元数据
            if "metadata" not in updated_data:
                updated_data["metadata"] = {}

            updated_data["metadata"]["last_update"] = {
                "update_id": update_id,
                "session_id": session.session_id,
                "timestamp": datetime.now().isoformat(),
                "nodes_updated": nodes_updated,
                "nodes_created": nodes_created,
                "edges_updated": edges_updated
            }

            return updated_data

        # 执行原子性更新
        transaction_manager.atomic_update_json(canvas_path, update_canvas_data)

        # 验证更新
        if not transaction_manager.verify_file_integrity(canvas_path):
            raise Exception("Canvas file integrity check failed after update")

        # 计算统计信息
        total_updates = len(results)
        nodes_updated = sum(1 for r in results if r["node_id"] in nodes_map)
        nodes_created = total_updates - nodes_updated

        return CanvasUpdateResult(
            update_id=update_id,
            session_id=session.session_id,
            nodes_updated=nodes_updated,
            nodes_created=nodes_created,
            edges_updated=0,  # 根据实际更新计算
            backup_path=backup_path,
            success=True
        )

    def _record_aggregation(self,
                           session: ProcessingSession,
                           update_result: CanvasUpdateResult,
                           validation_result: ValidationResult,
                           conflicts: List[ResultConflict]):
        """记录聚合历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session.session_id,
            "update_id": update_result.update_id,
            "success": update_result.success,
            "total_tasks": len(session.tasks),
            "successful_tasks": sum(1 for t in session.tasks if t.status == TaskStatus.COMPLETED),
            "failed_tasks": sum(1 for t in session.tasks if t.status == TaskStatus.FAILED),
            "validation_errors": len(validation_result.errors),
            "validation_warnings": len(validation_result.warnings),
            "conflicts_detected": len(conflicts),
            "conflicts_resolved": len(self.conflict_resolution_cache),
            "nodes_updated": update_result.nodes_updated,
            "nodes_created": update_result.nodes_created,
            "edges_updated": update_result.edges_updated
        }

        self.aggregation_history.append(record)

        # 保持历史记录不超过1000条
        if len(self.aggregation_history) > 1000:
            self.aggregation_history.pop(0)

    async def get_aggregation_report(self, session_id: Optional[str] = None) -> Dict:
        """获取聚合报告"""
        if session_id:
            # 获取特定会话的报告
            records = [r for r in self.aggregation_history if r["session_id"] == session_id]
        else:
            # 获取所有报告
            records = self.aggregation_history

        if not records:
            return {"message": "No aggregation records found"}

        # 计算统计信息
        total_sessions = len(set(r["session_id"] for r in records))
        total_tasks = sum(r["total_tasks"] for r in records)
        avg_success_rate = sum(r["successful_tasks"] for r in records) / max(1, total_tasks) * 100
        total_conflicts = sum(r["conflicts_detected"] for r in records)

        return {
            "summary": {
                "total_sessions": total_sessions,
                "total_tasks": total_tasks,
                "average_success_rate": f"{avg_success_rate:.2f}%",
                "total_conflicts": total_conflicts,
                "conflict_resolution_rate": f"{sum(r['conflicts_resolved'] for r in records) / max(1, total_conflicts) * 100:.2f}%"
            },
            "recent_records": records[-10:]  # 最近10条记录
        }

    async def rollback_update(self, canvas_path: str, update_id: str) -> bool:
        """回滚更新"""
        try:
            # 查找备份文件
            backup_dir = Path(canvas_path).parent / "backups"
            backup_files = list(backup_dir.glob(f"*{update_id}*.canvas")) if backup_dir.exists() else []

            if not backup_files:
                logger.error(f"No backup found for update {update_id}")
                return False

            # 使用最新的备份
            backup_path = max(backup_files, key=lambda p: p.stat().st_mtime)

            # 恢复
            success = transaction_manager.restore_from_backup(canvas_path, str(backup_path))
            if success:
                logger.info(f"Successfully rolled back update {update_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to rollback update {update_id}: {e}")
            return False