# src/rollback/tracked_operator.py
"""
Tracked Canvas Operator

Wraps existing CanvasService to automatically track all operations.

[Source: docs/architecture/rollback-recovery-architecture.md:122-180]
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import Operation, OperationData, OperationMetadata, OperationType
from .operation_tracker import OperationTracker


class TrackedCanvasOperator:
    """带操作追踪的Canvas操作器

    包装现有CanvasService，自动追踪所有操作。

    [Source: docs/architecture/rollback-recovery-architecture.md:122-180]

    Attributes:
        canvas_service: 被包装的CanvasService实例
        tracker: 操作追踪器
        user_id: 当前用户ID
    """

    def __init__(
        self,
        canvas_service: Any,
        tracker: OperationTracker,
        user_id: str = "system",
    ):
        """初始化TrackedCanvasOperator

        Args:
            canvas_service: 被包装的CanvasService实例
            tracker: 操作追踪器
            user_id: 当前用户ID，默认为"system"
        """
        self.canvas_service = canvas_service
        self.tracker = tracker
        self.user_id = user_id

    def _create_and_track_operation(
        self,
        operation_type: OperationType,
        canvas_path: str,
        before: Optional[Any] = None,
        after: Optional[Any] = None,
        node_ids: Optional[List[str]] = None,
        edge_ids: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
        description: str = "",
    ) -> str:
        """创建并追踪一个操作

        Args:
            operation_type: 操作类型
            canvas_path: Canvas文件路径
            before: 操作前状态
            after: 操作后状态
            node_ids: 影响的节点ID列表
            edge_ids: 影响的边ID列表
            agent_id: 执行Agent ID
            request_id: 请求追踪ID
            description: 操作描述

        Returns:
            操作ID
        """
        operation = Operation(
            id=str(uuid.uuid4()),
            type=operation_type,
            canvas_path=canvas_path,
            timestamp=datetime.now(timezone.utc),
            user_id=self.user_id,
            data=OperationData(
                before=before,
                after=after,
                node_ids=node_ids,
                edge_ids=edge_ids,
            ),
            metadata=OperationMetadata(
                agent_id=agent_id,
                request_id=request_id,
                description=description,
            ),
        )
        return self.tracker.track_operation(operation)

    # ========== Node Operations ==========

    def add_node(
        self,
        canvas_path: str,
        node_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """添加节点并追踪操作

        [Source: docs/architecture/rollback-recovery-architecture.md:130-145]

        Args:
            canvas_path: Canvas文件路径
            node_data: 节点数据
            agent_id: 执行Agent ID
            request_id: 请求追踪ID

        Returns:
            创建的节点数据 (包含生成的ID)
        """
        # 执行实际操作
        result = self.canvas_service.add_node(canvas_path, node_data)

        # 追踪操作
        node_id = result.get("id") or node_data.get("id")
        self._create_and_track_operation(
            operation_type=OperationType.NODE_ADD,
            canvas_path=canvas_path,
            before=None,
            after=result,
            node_ids=[node_id] if node_id else None,
            agent_id=agent_id,
            request_id=request_id,
            description=f"Add node: {node_data.get('text', '')[:50]}",
        )

        return result

    def delete_node(
        self,
        canvas_path: str,
        node_id: str,
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """删除节点并追踪操作

        [Source: docs/architecture/rollback-recovery-architecture.md:147-160]

        Args:
            canvas_path: Canvas文件路径
            node_id: 要删除的节点ID
            agent_id: 执行Agent ID
            request_id: 请求追踪ID

        Returns:
            是否删除成功
        """
        # 获取删除前的节点数据
        before_data = self.canvas_service.get_node(canvas_path, node_id)

        # 执行实际操作
        result = self.canvas_service.delete_node(canvas_path, node_id)

        if result:
            # 追踪操作
            self._create_and_track_operation(
                operation_type=OperationType.NODE_DELETE,
                canvas_path=canvas_path,
                before=before_data,
                after=None,
                node_ids=[node_id],
                agent_id=agent_id,
                request_id=request_id,
                description=f"Delete node: {node_id}",
            )

        return result

    def modify_node(
        self,
        canvas_path: str,
        node_id: str,
        updates: Dict[str, Any],
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """修改节点并追踪操作

        [Source: docs/architecture/rollback-recovery-architecture.md:162-175]

        Args:
            canvas_path: Canvas文件路径
            node_id: 要修改的节点ID
            updates: 更新数据
            agent_id: 执行Agent ID
            request_id: 请求追踪ID

        Returns:
            更新后的节点数据
        """
        # 获取修改前的节点数据
        before_data = self.canvas_service.get_node(canvas_path, node_id)

        # 执行实际操作
        result = self.canvas_service.update_node(canvas_path, node_id, updates)

        # 追踪操作
        self._create_and_track_operation(
            operation_type=OperationType.NODE_MODIFY,
            canvas_path=canvas_path,
            before=before_data,
            after=result,
            node_ids=[node_id],
            agent_id=agent_id,
            request_id=request_id,
            description=f"Modify node: {node_id}",
        )

        return result

    def change_node_color(
        self,
        canvas_path: str,
        node_id: str,
        new_color: str,
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """修改节点颜色并追踪操作

        [Source: docs/architecture/rollback-recovery-architecture.md:177-190]

        Args:
            canvas_path: Canvas文件路径
            node_id: 要修改的节点ID
            new_color: 新颜色值
            agent_id: 执行Agent ID
            request_id: 请求追踪ID

        Returns:
            更新后的节点数据
        """
        # 获取修改前的节点数据
        before_data = self.canvas_service.get_node(canvas_path, node_id)
        old_color = before_data.get("color") if before_data else None

        # 执行实际操作
        result = self.canvas_service.update_node(
            canvas_path, node_id, {"color": new_color}
        )

        # 追踪操作 (使用专门的颜色变更类型)
        self._create_and_track_operation(
            operation_type=OperationType.NODE_COLOR_CHANGE,
            canvas_path=canvas_path,
            before={"color": old_color},
            after={"color": new_color},
            node_ids=[node_id],
            agent_id=agent_id,
            request_id=request_id,
            description=f"Change node color: {old_color} → {new_color}",
        )

        return result

    # ========== Edge Operations ==========

    def add_edge(
        self,
        canvas_path: str,
        edge_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """添加边并追踪操作

        [Source: docs/architecture/rollback-recovery-architecture.md:192-205]

        Args:
            canvas_path: Canvas文件路径
            edge_data: 边数据
            agent_id: 执行Agent ID
            request_id: 请求追踪ID

        Returns:
            创建的边数据
        """
        # 执行实际操作
        result = self.canvas_service.add_edge(canvas_path, edge_data)

        # 追踪操作
        edge_id = result.get("id") or edge_data.get("id")
        self._create_and_track_operation(
            operation_type=OperationType.EDGE_ADD,
            canvas_path=canvas_path,
            before=None,
            after=result,
            edge_ids=[edge_id] if edge_id else None,
            agent_id=agent_id,
            request_id=request_id,
            description=f"Add edge: {edge_data.get('fromNode', '')} → {edge_data.get('toNode', '')}",
        )

        return result

    def delete_edge(
        self,
        canvas_path: str,
        edge_id: str,
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """删除边并追踪操作

        [Source: docs/architecture/rollback-recovery-architecture.md:207-220]

        Args:
            canvas_path: Canvas文件路径
            edge_id: 要删除的边ID
            agent_id: 执行Agent ID
            request_id: 请求追踪ID

        Returns:
            是否删除成功
        """
        # 获取删除前的边数据
        before_data = self.canvas_service.get_edge(canvas_path, edge_id)

        # 执行实际操作
        result = self.canvas_service.delete_edge(canvas_path, edge_id)

        if result:
            # 追踪操作
            self._create_and_track_operation(
                operation_type=OperationType.EDGE_DELETE,
                canvas_path=canvas_path,
                before=before_data,
                after=None,
                edge_ids=[edge_id],
                agent_id=agent_id,
                request_id=request_id,
                description=f"Delete edge: {edge_id}",
            )

        return result

    # ========== Batch Operations ==========

    def batch_operation(
        self,
        canvas_path: str,
        operations: List[Dict[str, Any]],
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行批量操作并追踪

        [Source: docs/architecture/rollback-recovery-architecture.md:222-250]

        Args:
            canvas_path: Canvas文件路径
            operations: 操作列表，每个操作包含 type, data 等字段
            agent_id: 执行Agent ID
            request_id: 请求追踪ID

        Returns:
            批量操作结果
        """
        # 获取操作前的Canvas状态 (用于回滚)
        before_state = self.canvas_service.get_canvas_data(canvas_path)

        # 执行实际批量操作
        result = self.canvas_service.batch_update(canvas_path, operations)

        # 获取操作后的Canvas状态
        after_state = self.canvas_service.get_canvas_data(canvas_path)

        # 收集所有影响的节点和边ID
        affected_node_ids = []
        affected_edge_ids = []
        for op in operations:
            if op.get("node_id"):
                affected_node_ids.append(op["node_id"])
            if op.get("edge_id"):
                affected_edge_ids.append(op["edge_id"])

        # 追踪批量操作
        self._create_and_track_operation(
            operation_type=OperationType.BATCH_OPERATION,
            canvas_path=canvas_path,
            before=before_state,
            after=after_state,
            node_ids=affected_node_ids if affected_node_ids else None,
            edge_ids=affected_edge_ids if affected_edge_ids else None,
            agent_id=agent_id,
            request_id=request_id,
            description=f"Batch operation: {len(operations)} operations",
        )

        return result

    # ========== Passthrough Methods ==========

    def get_node(self, canvas_path: str, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点数据 (不追踪，只读操作)"""
        return self.canvas_service.get_node(canvas_path, node_id)

    def get_edge(self, canvas_path: str, edge_id: str) -> Optional[Dict[str, Any]]:
        """获取边数据 (不追踪，只读操作)"""
        return self.canvas_service.get_edge(canvas_path, edge_id)

    def get_canvas_data(self, canvas_path: str) -> Dict[str, Any]:
        """获取完整Canvas数据 (不追踪，只读操作)"""
        return self.canvas_service.get_canvas_data(canvas_path)

    def list_nodes(self, canvas_path: str) -> List[Dict[str, Any]]:
        """列出所有节点 (不追踪，只读操作)"""
        return self.canvas_service.list_nodes(canvas_path)

    def list_edges(self, canvas_path: str) -> List[Dict[str, Any]]:
        """列出所有边 (不追踪，只读操作)"""
        return self.canvas_service.list_edges(canvas_path)
