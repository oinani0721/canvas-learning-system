"""
处理进度监控系统 - 增强版

提供实时进度跟踪、状态报告、性能分析和异常监控功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
Story: 10.4 - Canvas并行处理集成引擎
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from collections import deque

from parallel_canvas_processor import ProcessingSession, ProcessingTask, TaskStatus

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


class ProgressEventType(Enum):
    """进度事件类型"""
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    PROGRESS_UPDATE = "progress_update"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class ProgressEvent:
    """进度事件"""
    event_type: ProgressEventType
    session_id: str
    task_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressSnapshot:
    """进度快照"""
    session_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    processing_tasks: int
    pending_tasks: int
    progress_percentage: float
    elapsed_time: float
    estimated_remaining_time: Optional[float]
    throughput: float  # 任务/秒
    error_rate: float  # 错误率
    timestamp: datetime = field(default_factory=datetime.now)


class AdvancedProgressMonitor:
    """高级进度监控器

    提供以下功能：
    - 实时进度跟踪
    - 性能指标计算
    - 异常检测和报告
    - 历史数据记录
    - 实时通知
    """

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.event_history: deque = deque(maxlen=max_history)
        self.progress_snapshots: Dict[str, List[ProgressSnapshot]] = {}
        self.active_sessions: Dict[str, ProcessingSession] = {}
        self.event_callbacks: List[Callable] = []
        self.performance_metrics: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False

    async def start_monitoring(self, session: ProcessingSession):
        """开始监控会话"""
        logger.info(f"Starting progress monitoring for session {session.session_id}")

        with self._lock:
            self.active_sessions[session.session_id] = session
            self.progress_snapshots[session.session_id] = []

        # 触发会话开始事件
        await self._emit_event(ProgressEventType.SESSION_STARTED, session.session_id, {
            "total_tasks": len(session.tasks),
            "agent_type": session.tasks[0].agent_type if session.tasks else None,
            "canvas_path": session.canvas_path
        })

        # 启动监控任务
        if not self._is_monitoring:
            self._is_monitoring = True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self, session_id: str):
        """停止监控会话"""
        logger.info(f"Stopping progress monitoring for session {session_id}")

        # 触发会话结束事件
        session = self.active_sessions.get(session_id)
        if session:
            event_type = ProgressEventType.SESSION_COMPLETED if session.status == TaskStatus.COMPLETED else ProgressEventType.SESSION_FAILED
            await self._emit_event(event_type, session_id, {
                "final_status": session.status.value,
                "total_completed": session.completed_nodes,
                "total_failed": session.failed_nodes,
                "total_time": (session.end_time - session.start_time).total_seconds() if session.end_time and session.start_time else 0
            })

        with self._lock:
            self.active_sessions.pop(session_id, None)

        # 如果没有活跃会话，停止监控循环
        if not self.active_sessions and self._monitoring_task:
            self._monitoring_task.cancel()
            self._is_monitoring = False

    async def update_task_status(self, task: ProcessingTask, old_status: TaskStatus):
        """更新任务状态"""
        session_id = task.task_id.split('-')[0]  # 假设task_id包含session_id

        # 触发任务状态事件
        if task.status == TaskStatus.PROCESSING and old_status == TaskStatus.PENDING:
            await self._emit_event(ProgressEventType.TASK_STARTED, session_id, {
                "task_id": task.task_id,
                "node_id": task.node_id,
                "complexity": task.complexity.value
            })
        elif task.status == TaskStatus.COMPLETED:
            await self._emit_event(ProgressEventType.TASK_COMPLETED, session_id, {
                "task_id": task.task_id,
                "processing_time": (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else 0
            })
        elif task.status == TaskStatus.FAILED:
            await self._emit_event(ProgressEventType.TASK_FAILED, session_id, {
                "task_id": task.task_id,
                "error_message": task.error_message
            })

    async def get_progress_snapshot(self, session_id: str) -> Optional[ProgressSnapshot]:
        """获取当前进度快照"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        # 计算任务统计
        total_tasks = len(session.tasks)
        completed_tasks = sum(1 for t in session.tasks if t.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for t in session.tasks if t.status == TaskStatus.FAILED)
        processing_tasks = sum(1 for t in session.tasks if t.status == TaskStatus.PROCESSING)
        pending_tasks = sum(1 for t in session.tasks if t.status == TaskStatus.PENDING)

        # 计算进度百分比
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # 计算经过时间
        elapsed_time = 0
        if session.start_time:
            elapsed_time = (datetime.now() - session.start_time).total_seconds()

        # 估算剩余时间
        estimated_remaining_time = None
        if completed_tasks > 0 and elapsed_time > 0:
            avg_time_per_task = elapsed_time / completed_tasks
            remaining_tasks = total_tasks - completed_tasks
            estimated_remaining_time = avg_time_per_task * remaining_tasks

        # 计算吞吐量
        throughput = completed_tasks / max(elapsed_time, 1)

        # 计算错误率
        error_rate = (failed_tasks / max(completed_tasks + failed_tasks, 1)) * 100

        snapshot = ProgressSnapshot(
            session_id=session_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            processing_tasks=processing_tasks,
            pending_tasks=pending_tasks,
            progress_percentage=progress_percentage,
            elapsed_time=elapsed_time,
            estimated_remaining_time=estimated_remaining_time,
            throughput=throughput,
            error_rate=error_rate
        )

        # 保存快照
        with self._lock:
            self.progress_snapshots[session_id].append(snapshot)
            # 限制快照数量
            if len(self.progress_snapshots[session_id]) > 100:
                self.progress_snapshots[session_id].pop(0)

        return snapshot

    async def get_progress_history(self, session_id: str, limit: int = 50) -> List[ProgressSnapshot]:
        """获取进度历史"""
        with self._lock:
            snapshots = self.progress_snapshots.get(session_id, [])
            return snapshots[-limit:]

    async def get_performance_report(self, session_id: Optional[str] = None) -> Dict:
        """获取性能报告"""
        if session_id:
            # 获取特定会话的报告
            snapshots = self.progress_snapshots.get(session_id, [])
            if not snapshots:
                return {"error": "No progress data found for session"}
            sessions_data = {session_id: snapshots}
        else:
            # 获取所有会话的报告
            sessions_data = self.progress_snapshots

        report = {
            "timestamp": datetime.now().isoformat(),
            "sessions": {}
        }

        for sid, snapshots in sessions_data.items():
            if not snapshots:
                continue

            latest = snapshots[-1]
            session = self.active_sessions.get(sid)

            # 计算性能指标
            avg_throughput = sum(s.throughput for s in snapshots) / len(snapshots)
            peak_throughput = max(s.throughput for s in snapshots)
            avg_error_rate = sum(s.error_rate for s in snapshots) / len(snapshots)

            # 检测性能异常
            anomalies = self._detect_performance_anomalies(snapshots)

            report["sessions"][sid] = {
                "status": session.status.value if session else "unknown",
                "progress": {
                    "percentage": latest.progress_percentage,
                    "completed": latest.completed_tasks,
                    "total": latest.total_tasks,
                    "failed": latest.failed_tasks
                },
                "timing": {
                    "elapsed": latest.elapsed_time,
                    "estimated_remaining": latest.estimated_remaining_time
                },
                "performance": {
                    "throughput": {
                        "current": latest.throughput,
                        "average": avg_throughput,
                        "peak": peak_throughput
                    },
                    "error_rate": {
                        "current": latest.error_rate,
                        "average": avg_error_rate
                    }
                },
                "anomalies": anomalies,
                "recommendations": self._generate_recommendations(latest, anomalies)
            }

        return report

    def _detect_performance_anomalies(self, snapshots: List[ProgressSnapshot]) -> List[str]:
        """检测性能异常"""
        anomalies = []
        if len(snapshots) < 5:
            return anomalies

        recent = snapshots[-5:]
        throughputs = [s.throughput for s in recent]
        error_rates = [s.error_rate for s in recent]

        # 检测吞吐量下降
        if throughputs[-1] < throughputs[0] * 0.5:
            anomalies.append("Throughput has decreased significantly")

        # 检测错误率上升
        if error_rates[-1] > 20 and error_rates[-1] > error_rates[0] * 2:
            anomalies.append("Error rate is increasing")

        # 检测停滞
        if all(s.progress_percentage == recent[0].progress_percentage for s in recent):
            anomalies.append("Progress appears to be stalled")

        return anomalies

    def _generate_recommendations(self, snapshot: ProgressSnapshot, anomalies: List[str]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if snapshot.error_rate > 10:
            recommendations.append("Consider reviewing failed tasks and adjusting parameters")

        if snapshot.throughput < 0.1:
            recommendations.append("Low throughput detected - check system resources")

        if "stalled" in " ".join(anomalies).lower():
            recommendations.append("Progress stalled - check for deadlock or resource contention")

        if snapshot.estimated_remaining_time and snapshot.estimated_remaining_time > 3600:  # 超过1小时
            recommendations.append("Long processing time estimated - consider increasing concurrency")

        return recommendations

    def register_callback(self, callback: Callable[[ProgressEvent], None]):
        """注册进度回调函数"""
        self.event_callbacks.append(callback)

    def unregister_callback(self, callback: Callable):
        """注销回调函数"""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)

    async def _emit_event(self, event_type: ProgressEventType, session_id: str, data: Dict):
        """发出进度事件"""
        event = ProgressEvent(event_type=event_type, session_id=session_id, data=data)

        # 记录事件
        with self._lock:
            self.event_history.append(event)

        # 通知回调
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    async def _monitoring_loop(self):
        """监控循环"""
        while self._is_monitoring and self.active_sessions:
            try:
                # 更新所有活跃会话的进度
                for session_id in list(self.active_sessions.keys()):
                    snapshot = await self.get_progress_snapshot(session_id)
                    if snapshot:
                        await self._emit_event(
                            ProgressEventType.PROGRESS_UPDATE,
                            session_id,
                            asdict(snapshot)
                        )

                # 等待一段时间再更新
                await asyncio.sleep(1)  # 每秒更新一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # 出错时等待更长时间

    async def export_progress_data(self, session_id: str, file_path: str):
        """导出进度数据"""
        snapshots = self.progress_snapshots.get(session_id, [])
        events = [e for e in self.event_history if e.session_id == session_id]

        data = {
            "session_id": session_id,
            "export_timestamp": datetime.now().isoformat(),
            "snapshots": [asdict(s) for s in snapshots],
            "events": [asdict(e) for e in events]
        }

        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Progress data exported to {file_path}")

    def get_real_time_stats(self) -> Dict:
        """获取实时统计信息"""
        with self._lock:
            active_sessions = len(self.active_sessions)
            total_events = len(self.event_history)
            total_snapshots = sum(len(s) for s in self.progress_snapshots.values())

        return {
            "active_sessions": active_sessions,
            "total_events": total_events,
            "total_snapshots": total_snapshots,
            "is_monitoring": self._is_monitoring,
            "registered_callbacks": len(self.event_callbacks)
        }