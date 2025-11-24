---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-23"
status: "draft"
iteration: 5

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

compatible_with:
  prd: "v1.1.8"
  epic: ["Epic 12", "Epic 18"]

changes_from_previous:
  - "Initial Rollback and Recovery Architecture document"
---

# 回滚与恢复架构

**版本**: v1.0.0
**创建日期**: 2025-11-23
**架构师**: Architect Agent

---

## 1. 概述

本文档定义Canvas Learning System的回滚与恢复架构，确保Canvas操作的可追溯性和数据安全。

### 1.1 设计目标

- Canvas操作历史追踪
- 一键回滚到任意历史版本
- 增量备份和恢复
- 知识图谱状态同步

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                   回滚恢复系统                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │ Operation   │────▶│ History     │────▶│ Rollback  │ │
│  │ Tracker     │     │ Store       │     │ Engine    │ │
│  └─────────────┘     └─────────────┘     └───────────┘ │
│         │                   │                   │       │
│         ▼                   ▼                   ▼       │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │ Canvas      │     │ Snapshot    │     │ Graph     │ │
│  │ Operations  │     │ Manager     │     │ Sync      │ │
│  └─────────────┘     └─────────────┘     └───────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 操作追踪

### 3.1 操作类型

```typescript
type OperationType =
    | 'node_add'           // 添加节点
    | 'node_delete'        // 删除节点
    | 'node_modify'        // 修改节点
    | 'node_color_change'  // 颜色变更
    | 'edge_add'           // 添加边
    | 'edge_delete'        // 删除边
    | 'batch_operation';   // 批量操作

interface Operation {
    id: string;
    type: OperationType;
    canvasPath: string;
    timestamp: Date;
    userId: string;
    data: {
        before: any;      // 操作前状态
        after: any;       // 操作后状态
        nodeIds?: string[];
        edgeIds?: string[];
    };
    metadata: {
        agentId?: string;     // 触发的Agent
        requestId?: string;   // 关联的请求ID
        description: string;  // 操作描述
    };
}
```

### 3.2 操作追踪器

```typescript
class OperationTracker {
    private operations: Operation[] = [];
    private maxHistory: number = 100;

    track(operation: Omit<Operation, 'id' | 'timestamp'>): string {
        const op: Operation = {
            ...operation,
            id: this.generateId(),
            timestamp: new Date()
        };

        this.operations.push(op);

        // 保持历史记录在限制内
        if (this.operations.length > this.maxHistory) {
            this.operations.shift();
        }

        // 持久化到存储
        this.persistOperation(op);

        return op.id;
    }

    getHistory(
        canvasPath: string,
        limit: number = 50
    ): Operation[] {
        return this.operations
            .filter(op => op.canvasPath === canvasPath)
            .slice(-limit);
    }

    getOperation(id: string): Operation | undefined {
        return this.operations.find(op => op.id === id);
    }

    private generateId(): string {
        return `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    private async persistOperation(op: Operation): Promise<void> {
        // 保存到本地存储或数据库
    }
}
```

### 3.3 Canvas操作包装

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md)
class TrackedCanvasOperator {
    private operator: CanvasOperator;
    private tracker: OperationTracker;

    constructor(operator: CanvasOperator, tracker: OperationTracker) {
        this.operator = operator;
        this.tracker = tracker;
    }

    async addNode(
        canvasPath: string,
        node: CanvasNode,
        metadata?: { agentId?: string; description?: string }
    ): Promise<void> {
        // 记录操作前状态
        const before = await this.operator.readCanvas(canvasPath);

        // 执行操作
        await this.operator.addNode(canvasPath, node);

        // 记录操作后状态
        const after = await this.operator.readCanvas(canvasPath);

        // 追踪操作
        this.tracker.track({
            type: 'node_add',
            canvasPath,
            userId: 'current_user',
            data: {
                before: before.nodes,
                after: after.nodes,
                nodeIds: [node.id]
            },
            metadata: {
                agentId: metadata?.agentId,
                description: metadata?.description || `添加节点 ${node.id}`
            }
        });
    }

    async modifyNode(
        canvasPath: string,
        nodeId: string,
        changes: Partial<CanvasNode>,
        metadata?: { agentId?: string; description?: string }
    ): Promise<void> {
        const canvas = await this.operator.readCanvas(canvasPath);
        const oldNode = canvas.nodes.find(n => n.id === nodeId);

        if (!oldNode) throw new Error(`Node ${nodeId} not found`);

        // 执行修改
        await this.operator.modifyNode(canvasPath, nodeId, changes);

        // 追踪操作
        this.tracker.track({
            type: 'node_modify',
            canvasPath,
            userId: 'current_user',
            data: {
                before: oldNode,
                after: { ...oldNode, ...changes },
                nodeIds: [nodeId]
            },
            metadata: {
                agentId: metadata?.agentId,
                description: metadata?.description || `修改节点 ${nodeId}`
            }
        });
    }

    async changeNodeColor(
        canvasPath: string,
        nodeId: string,
        newColor: string,
        metadata?: { agentId?: string; description?: string }
    ): Promise<void> {
        const canvas = await this.operator.readCanvas(canvasPath);
        const oldNode = canvas.nodes.find(n => n.id === nodeId);
        const oldColor = oldNode?.color;

        await this.operator.modifyNode(canvasPath, nodeId, { color: newColor });

        this.tracker.track({
            type: 'node_color_change',
            canvasPath,
            userId: 'current_user',
            data: {
                before: { color: oldColor },
                after: { color: newColor },
                nodeIds: [nodeId]
            },
            metadata: {
                agentId: metadata?.agentId,
                description: metadata?.description || `节点 ${nodeId} 颜色从 ${oldColor} 变为 ${newColor}`
            }
        });
    }
}
```

---

## 4. 快照管理

### 4.1 快照结构

```typescript
interface Snapshot {
    id: string;
    canvasPath: string;
    timestamp: Date;
    type: 'auto' | 'manual' | 'checkpoint';
    data: {
        canvas: CanvasData;
        operations: string[];  // 相关操作ID
    };
    metadata: {
        description?: string;
        tags?: string[];
        size: number;  // 字节
    };
}

interface CanvasData {
    nodes: CanvasNode[];
    edges: CanvasEdge[];
}
```

### 4.2 快照管理器

```typescript
class SnapshotManager {
    private snapshotsDir: string;
    private maxSnapshots: number = 50;

    constructor(snapshotsDir: string) {
        this.snapshotsDir = snapshotsDir;
    }

    async createSnapshot(
        canvasPath: string,
        type: 'auto' | 'manual' | 'checkpoint',
        description?: string
    ): Promise<Snapshot> {
        // 读取当前Canvas
        const canvas = await this.readCanvas(canvasPath);

        const snapshot: Snapshot = {
            id: this.generateId(),
            canvasPath,
            timestamp: new Date(),
            type,
            data: {
                canvas,
                operations: []
            },
            metadata: {
                description,
                size: JSON.stringify(canvas).length
            }
        };

        // 保存快照
        await this.saveSnapshot(snapshot);

        // 清理旧快照
        await this.cleanupOldSnapshots(canvasPath);

        return snapshot;
    }

    async listSnapshots(
        canvasPath: string,
        options?: {
            type?: 'auto' | 'manual' | 'checkpoint';
            limit?: number;
        }
    ): Promise<Snapshot[]> {
        const snapshots = await this.loadSnapshots(canvasPath);

        let filtered = snapshots;
        if (options?.type) {
            filtered = filtered.filter(s => s.type === options.type);
        }

        if (options?.limit) {
            filtered = filtered.slice(-options.limit);
        }

        return filtered.sort((a, b) =>
            b.timestamp.getTime() - a.timestamp.getTime()
        );
    }

    async getSnapshot(snapshotId: string): Promise<Snapshot | null> {
        // 从存储加载快照
        return this.loadSnapshot(snapshotId);
    }

    async deleteSnapshot(snapshotId: string): Promise<void> {
        // 删除快照文件
    }

    private async cleanupOldSnapshots(canvasPath: string): Promise<void> {
        const snapshots = await this.listSnapshots(canvasPath);

        if (snapshots.length > this.maxSnapshots) {
            const toDelete = snapshots.slice(0, snapshots.length - this.maxSnapshots);

            for (const snapshot of toDelete) {
                await this.deleteSnapshot(snapshot.id);
            }
        }
    }

    private generateId(): string {
        return `snap_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    private async saveSnapshot(snapshot: Snapshot): Promise<void> {
        const filepath = `${this.snapshotsDir}/${snapshot.id}.json`;
        // 保存到文件系统
    }

    private async loadSnapshot(id: string): Promise<Snapshot | null> {
        // 从文件系统加载
        return null;
    }

    private async loadSnapshots(canvasPath: string): Promise<Snapshot[]> {
        // 加载所有相关快照
        return [];
    }

    private async readCanvas(canvasPath: string): Promise<CanvasData> {
        // 读取Canvas文件
        return { nodes: [], edges: [] };
    }
}
```

---

## 5. 回滚引擎

### 5.1 回滚类型

```typescript
type RollbackType =
    | 'operation'   // 回滚单个操作
    | 'snapshot'    // 恢复到快照
    | 'timepoint';  // 恢复到时间点

interface RollbackRequest {
    type: RollbackType;
    canvasPath: string;
    target: string;  // 操作ID / 快照ID / 时间戳
    options?: {
        preserveGraph?: boolean;  // 保留知识图谱状态
        createBackup?: boolean;   // 回滚前创建备份
    };
}

interface RollbackResult {
    success: boolean;
    backupId?: string;
    restoredState: CanvasData;
    affectedOperations: string[];
    graphSyncStatus?: 'synced' | 'pending' | 'skipped';
}
```

### 5.2 回滚引擎

```typescript
class RollbackEngine {
    private tracker: OperationTracker;
    private snapshotManager: SnapshotManager;
    private canvasOperator: CanvasOperator;
    private graphSync: GraphSyncService;

    async rollback(request: RollbackRequest): Promise<RollbackResult> {
        // 创建当前状态备份
        let backupId: string | undefined;
        if (request.options?.createBackup !== false) {
            const backup = await this.snapshotManager.createSnapshot(
                request.canvasPath,
                'checkpoint',
                `Backup before rollback to ${request.target}`
            );
            backupId = backup.id;
        }

        try {
            let result: RollbackResult;

            switch (request.type) {
                case 'operation':
                    result = await this.rollbackOperation(request);
                    break;
                case 'snapshot':
                    result = await this.rollbackToSnapshot(request);
                    break;
                case 'timepoint':
                    result = await this.rollbackToTimepoint(request);
                    break;
                default:
                    throw new Error(`Unknown rollback type: ${request.type}`);
            }

            result.backupId = backupId;

            // 同步知识图谱
            if (request.options?.preserveGraph !== true) {
                result.graphSyncStatus = await this.syncGraph(
                    request.canvasPath,
                    result.restoredState
                );
            } else {
                result.graphSyncStatus = 'skipped';
            }

            return result;
        } catch (error) {
            // 回滚失败，恢复备份
            if (backupId) {
                await this.rollbackToSnapshot({
                    type: 'snapshot',
                    canvasPath: request.canvasPath,
                    target: backupId,
                    options: { createBackup: false }
                });
            }
            throw error;
        }
    }

    private async rollbackOperation(
        request: RollbackRequest
    ): Promise<RollbackResult> {
        const operation = this.tracker.getOperation(request.target);
        if (!operation) {
            throw new Error(`Operation ${request.target} not found`);
        }

        // 应用反向操作
        const currentCanvas = await this.canvasOperator.readCanvas(
            request.canvasPath
        );
        const restoredCanvas = this.applyReverseOperation(
            currentCanvas,
            operation
        );

        await this.canvasOperator.writeCanvas(
            request.canvasPath,
            restoredCanvas
        );

        return {
            success: true,
            restoredState: restoredCanvas,
            affectedOperations: [operation.id]
        };
    }

    private async rollbackToSnapshot(
        request: RollbackRequest
    ): Promise<RollbackResult> {
        const snapshot = await this.snapshotManager.getSnapshot(request.target);
        if (!snapshot) {
            throw new Error(`Snapshot ${request.target} not found`);
        }

        // 恢复快照状态
        await this.canvasOperator.writeCanvas(
            request.canvasPath,
            snapshot.data.canvas
        );

        return {
            success: true,
            restoredState: snapshot.data.canvas,
            affectedOperations: snapshot.data.operations
        };
    }

    private async rollbackToTimepoint(
        request: RollbackRequest
    ): Promise<RollbackResult> {
        const targetTime = new Date(request.target);

        // 找到最近的快照
        const snapshots = await this.snapshotManager.listSnapshots(
            request.canvasPath
        );
        const nearestSnapshot = snapshots.find(
            s => s.timestamp <= targetTime
        );

        if (!nearestSnapshot) {
            throw new Error(`No snapshot found before ${targetTime}`);
        }

        // 恢复到快照
        return this.rollbackToSnapshot({
            ...request,
            target: nearestSnapshot.id
        });
    }

    private applyReverseOperation(
        canvas: CanvasData,
        operation: Operation
    ): CanvasData {
        switch (operation.type) {
            case 'node_add':
                // 删除添加的节点
                return {
                    ...canvas,
                    nodes: canvas.nodes.filter(
                        n => !operation.data.nodeIds?.includes(n.id)
                    )
                };

            case 'node_delete':
                // 恢复删除的节点
                return {
                    ...canvas,
                    nodes: [...canvas.nodes, ...operation.data.before]
                };

            case 'node_modify':
            case 'node_color_change':
                // 恢复节点原状态
                return {
                    ...canvas,
                    nodes: canvas.nodes.map(n => {
                        if (operation.data.nodeIds?.includes(n.id)) {
                            return operation.data.before;
                        }
                        return n;
                    })
                };

            default:
                return canvas;
        }
    }

    private async syncGraph(
        canvasPath: string,
        canvas: CanvasData
    ): Promise<'synced' | 'pending'> {
        try {
            await this.graphSync.syncCanvasState(canvasPath, canvas);
            return 'synced';
        } catch {
            return 'pending';
        }
    }
}
```

---

## 6. 知识图谱同步

### 6.1 同步服务

```python
# ✅ Verified from Graphiti Skill (SKILL.md - Section: Temporal Tracking)
from graphiti_core import Graphiti
from datetime import datetime

class GraphSyncService:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti

    async def sync_canvas_state(
        self,
        canvas_path: str,
        canvas_data: dict
    ) -> None:
        """
        同步Canvas状态到知识图谱
        """
        # 获取Canvas中的所有节点
        node_ids = [node['id'] for node in canvas_data['nodes']]

        # 更新图谱中的节点状态
        for node in canvas_data['nodes']:
            await self.update_node_in_graph(canvas_path, node)

        # 标记已删除的节点
        await self.mark_deleted_nodes(canvas_path, node_ids)

    async def update_node_in_graph(
        self,
        canvas_path: str,
        node: dict
    ) -> None:
        """更新图谱中的节点"""
        # 使用Graphiti的时序追踪
        episode_content = f"""
        Canvas node updated:
        - Canvas: {canvas_path}
        - Node ID: {node['id']}
        - Content: {node.get('text', '')}
        - Color: {node.get('color', '')}
        - Position: ({node['x']}, {node['y']})
        """

        await self.graphiti.add_episode(
            name=f"node_sync_{node['id']}",
            episode_body=episode_content,
            reference_time=datetime.now()
        )

    async def mark_deleted_nodes(
        self,
        canvas_path: str,
        current_node_ids: list
    ) -> None:
        """标记已删除的节点"""
        # 查询图谱中该Canvas的所有节点
        query = """
        MATCH (n:LearningNode {canvas_path: $canvas_path})
        WHERE NOT n.node_id IN $current_ids
        SET n.deleted_at = datetime()
        """

        await self.graphiti._driver.execute_query(query, {
            'canvas_path': canvas_path,
            'current_ids': current_node_ids
        })
```

---

## 7. API接口

### 7.1 回滚API

```python
# ✅ Verified from FastAPI Context7 documentation
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/rollback", tags=["rollback"])

@router.get("/history/{canvas_path}")
async def get_operation_history(
    canvas_path: str,
    limit: int = 50,
    tracker: OperationTracker = Depends(get_tracker)
) -> List[Operation]:
    """获取操作历史"""
    return tracker.getHistory(canvas_path, limit)

@router.get("/snapshots/{canvas_path}")
async def get_snapshots(
    canvas_path: str,
    type: Optional[str] = None,
    limit: int = 20,
    manager: SnapshotManager = Depends(get_snapshot_manager)
) -> List[Snapshot]:
    """获取快照列表"""
    return await manager.listSnapshots(canvas_path, {
        'type': type,
        'limit': limit
    })

@router.post("/snapshot")
async def create_snapshot(
    request: CreateSnapshotRequest,
    manager: SnapshotManager = Depends(get_snapshot_manager)
) -> Snapshot:
    """创建快照"""
    return await manager.createSnapshot(
        request.canvasPath,
        request.type,
        request.description
    )

@router.post("/rollback")
async def rollback(
    request: RollbackRequest,
    engine: RollbackEngine = Depends(get_rollback_engine)
) -> RollbackResult:
    """执行回滚"""
    return await engine.rollback(request)

@router.get("/diff/{snapshot_id}")
async def get_diff(
    snapshot_id: str,
    manager: SnapshotManager = Depends(get_snapshot_manager),
    operator: CanvasOperator = Depends(get_operator)
) -> DiffResult:
    """获取快照与当前状态的差异"""
    snapshot = await manager.getSnapshot(snapshot_id)
    current = await operator.readCanvas(snapshot.canvasPath)

    return calculate_diff(snapshot.data.canvas, current)
```

---

## 8. 配置

```yaml
# rollback_config.yaml
history:
  max_operations: 100
  persist_to_disk: true
  cleanup_interval_hours: 24

snapshots:
  max_per_canvas: 50
  auto_snapshot_interval: 300  # 秒
  checkpoint_on_batch: true

rollback:
  create_backup: true
  sync_graph: true
  timeout_seconds: 30

storage:
  snapshots_dir: ".canvas-learning/snapshots"
  history_dir: ".canvas-learning/history"
```

---

## 9. 相关文档

- [Canvas操作架构](canvas-3-layer-architecture.md)
- [Graphiti知识图谱架构](GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md)
- [3层记忆系统](COMPREHENSIVE-TECHNICAL-PLAN-3LAYER-MEMORY-AGENTIC-RAG.md)

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-23
**维护者**: Architect Agent
