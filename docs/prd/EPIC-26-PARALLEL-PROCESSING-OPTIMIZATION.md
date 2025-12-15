# Epic 26: 并行处理优化

---
epic_id: EPIC-26
title: "并行处理优化"
status: planned
priority: P3
created: 2025-12-11
estimated_stories: 4
related_bugs: [Bug-6]
dependencies: [EPIC-21]
---

## 1. 问题概述

### 1.1 Bug描述

**Bug 6: 并行处理多节点不工作**

当前系统的并行处理功能存在严重问题，导致：
- 批量处理的结果没有实际保存到Canvas
- 并发数被硬编码为10，忽略配置文件设置
- ProgressMonitorModal只显示进度，不执行保存操作

### 1.2 根因分析

#### 问题1: 硬编码并发限制

```python
# backend/app/services/agent_service.py:103
def __init__(
    self,
    gemini_client: Optional["GeminiClient"] = None,
    memory_client: Optional["LearningMemoryClient"] = None,
    max_concurrent: int = 10,  # ❌ 硬编码为10，忽略配置
    ai_config: Optional[Any] = None
):
```

**问题**: 配置文件中设置的 `MAX_CONCURRENT=100` 被忽略，始终使用默认值10。

#### 问题2: 前端不保存生成内容

```typescript
// ProgressMonitorModal.ts
// Grep: "save|writeCanvas|modify" → No matches found ❌

// 只有进度显示，没有保存逻辑
private callbacks: ProgressMonitorCallbacks;
// callbacks只有 onComplete 和 onCancel，没有 onSaveResults
```

**问题**: `ProgressMonitorModal`在处理完成后只触发回调，但**没有任何代码**将生成的节点和边写入Canvas文件。

#### 问题3: 批量结果丢失

```
用户启动批量处理
    ↓
后端并行调用Agent → 生成结果 ✅
    ↓
WebSocket推送进度更新到前端 ✅
    ↓
前端ProgressMonitorModal显示进度 ✅
    ↓
处理完成，触发onComplete回调 ✅
    ↓
❌ 缺失: 将results写入Canvas文件
    ↓
结果丢失，Canvas未修改
```

### 1.3 现有架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Obsidian)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐    ┌────────────────────────────┐  │
│  │ GroupPreviewModal   │ →  │ ProgressMonitorModal        │  │
│  │ (选择节点分组)       │    │ (显示处理进度)              │  │
│  └─────────────────────┘    │                            │  │
│                              │ - WebSocket连接 ✅         │  │
│                              │ - Polling回退 ✅           │  │
│                              │ - 进度条UI ✅              │  │
│                              │ - 保存到Canvas ❌ 缺失     │  │
│                              └────────────────────────────┘  │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐    ┌────────────────────────────┐  │
│  │ AgentService        │    │ Batch Processing           │  │
│  │                     │    │                            │  │
│  │ max_concurrent=10   │    │ call_agents_batch() ✅     │  │
│  │ (❌ 硬编码)         │    │ asyncio.Semaphore ✅       │  │
│  │                     │    │ 结果合并 ⚠️ 待优化        │  │
│  └─────────────────────┘    └────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 目标架构

### 2.1 完整并行处理流程

```
┌─────────────────────────────────────────────────────────────┐
│                    优化后的并行处理流程                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  用户选择节点 → GroupPreviewModal (分组预览)                  │
│       │                                                      │
│       ▼                                                      │
│  ProgressMonitorModal (进度监控 + 结果保存)                   │
│       │                                                      │
│       ├─────────────────────────────────────────────────────┤
│       │  [实时进度]                                          │
│       │  - WebSocket推送每个节点完成状态                      │
│       │  - 进度条 + 节点状态卡片                             │
│       │                                                      │
│       ├─────────────────────────────────────────────────────┤
│       │  [结果保存] ⭐ NEW                                   │
│       │  - 每个节点完成后立即保存到Canvas                    │
│       │  - 使用CanvasNodeAPI和CanvasEdgeAPI                 │
│       │  - 创建新节点 + 连接Edge                            │
│       │  - 更新节点颜色状态                                  │
│       │                                                      │
│       ├─────────────────────────────────────────────────────┤
│       │  [完成汇总]                                          │
│       │  - 显示成功/失败统计                                 │
│       │  - 提供回滚选项 (如果部分失败)                       │
│       │                                                      │
└───────┴─────────────────────────────────────────────────────┘
```

### 2.2 可配置并发数

```python
# 目标配置架构
class ParallelConfig:
    # 从config.py读取
    max_concurrent: int = settings.PARALLEL_MAX_CONCURRENT or 20

    # 根据节点数量动态调整
    @classmethod
    def get_optimal_concurrent(cls, node_count: int) -> int:
        if node_count <= 5:
            return 5
        elif node_count <= 20:
            return 10
        elif node_count <= 50:
            return 20
        else:
            return cls.max_concurrent  # 用户配置的最大值
```

---

## 3. Stories

### Story 26.1: 可配置并发数支持

**优先级**: P1 (High)
**估计**: 2 Story Points

#### 描述

修复并发数硬编码问题，支持从配置文件读取，并根据任务规模动态调整。

#### 根因

```python
# backend/app/services/agent_service.py:103
max_concurrent: int = 10,  # ❌ 硬编码，忽略配置
```

#### 验收标准 (AC)

- [ ] AC 1: `AgentService.__init__`从`config.py`读取`MAX_CONCURRENT`
- [ ] AC 2: 支持动态并发数调整 (5-50范围)
- [ ] AC 3: 添加`PARALLEL_MAX_CONCURRENT`配置项到`.env`
- [ ] AC 4: 日志记录当前使用的并发数
- [ ] AC 5: 单元测试验证配置读取

#### 技术任务

1. 修改`agent_service.py:__init__`读取配置
2. 在`config.py`添加`PARALLEL_MAX_CONCURRENT`配置
3. 实现`ParallelConfig.get_optimal_concurrent()`动态计算
4. 添加配置验证 (防止过大或过小)
5. 编写单元测试

#### 关键文件

- `backend/app/services/agent_service.py:99-150`
- `backend/app/config.py`
- `backend/.env`

#### 代码变更示例

```python
# config.py
class Settings(BaseSettings):
    # ...existing...

    # Parallel Processing
    PARALLEL_MAX_CONCURRENT: int = Field(
        default=20,
        description="Maximum concurrent agent calls (5-50)"
    )
    PARALLEL_MIN_CONCURRENT: int = 5
    PARALLEL_BATCH_SIZE: int = 10

# agent_service.py
def __init__(
    self,
    gemini_client: Optional["GeminiClient"] = None,
    memory_client: Optional["LearningMemoryClient"] = None,
    max_concurrent: Optional[int] = None,  # ✅ 改为Optional
    ai_config: Optional[Any] = None
):
    # 从配置读取，支持覆盖
    from app.config import get_settings
    settings = get_settings()
    self._max_concurrent = max_concurrent or settings.PARALLEL_MAX_CONCURRENT

    # 验证范围
    self._max_concurrent = max(
        settings.PARALLEL_MIN_CONCURRENT,
        min(self._max_concurrent, 50)
    )
```

---

### Story 26.2: ProgressMonitorModal结果保存

**优先级**: P0 (Critical)
**估计**: 4 Story Points

#### 描述

实现`ProgressMonitorModal`的结果保存逻辑，将批量处理结果实际写入Canvas文件。

#### 根因

```typescript
// ProgressMonitorModal.ts - 只有进度显示，没有保存逻辑
// Grep: "save|writeCanvas|modify" → No matches found ❌
```

#### 验收标准 (AC)

- [ ] AC 1: 每个节点处理完成后立即保存到Canvas
- [ ] AC 2: 使用`CanvasNodeAPI`创建生成的节点
- [ ] AC 3: 使用`CanvasEdgeAPI`创建连接边
- [ ] AC 4: 更新源节点颜色状态
- [ ] AC 5: 失败节点不影响其他节点保存
- [ ] AC 6: 提供回滚机制 (删除本次批量添加的节点)

#### 技术任务

1. 在`ProgressMonitorModal`添加`saveNodeResult()`方法
2. 集成`CanvasNodeAPI`和`CanvasEdgeAPI`
3. 实现增量保存 (每个节点完成后立即保存)
4. 实现事务性回滚机制
5. 添加保存状态指示器到UI
6. 编写集成测试

#### 关键文件

- `canvas-progress-tracker/obsidian-plugin/src/modals/ProgressMonitorModal.ts`
- `canvas-progress-tracker/obsidian-plugin/src/api/CanvasNodeAPI.ts`
- `canvas-progress-tracker/obsidian-plugin/src/api/CanvasEdgeAPI.ts`

#### 代码变更示例

```typescript
// ProgressMonitorModal.ts
import { CanvasNodeAPI } from '../api/CanvasNodeAPI';
import { CanvasEdgeAPI } from '../api/CanvasEdgeAPI';

export class ProgressMonitorModal extends Modal {
    private nodeAPI: CanvasNodeAPI;
    private edgeAPI: CanvasEdgeAPI;
    private createdNodeIds: string[] = [];  // For rollback
    private createdEdgeIds: string[] = [];

    /**
     * Save a single node result to Canvas
     * Called immediately when each node completes
     */
    private async saveNodeResult(result: NodeResult): Promise<void> {
        if (result.status !== 'success' || !result.output) {
            return;
        }

        try {
            // 1. Create generated node
            const newNode = await this.nodeAPI.createNode({
                text: result.output,
                x: this.calculateNodeX(result.node_id),
                y: this.calculateNodeY(result.node_id),
                width: 400,
                height: 200,
                color: '3'  // Yellow for new content
            });
            this.createdNodeIds.push(newNode.id);

            // 2. Create edge from source to new node
            const edge = await this.edgeAPI.createEdge({
                fromNode: result.node_id,
                toNode: newNode.id,
                label: this.getEdgeLabel()
            });
            this.createdEdgeIds.push(edge.id);

            // 3. Update source node color if needed
            await this.updateSourceNodeColor(result.node_id);

            logger.info(`Saved result for node ${result.node_id}`);
        } catch (error) {
            logger.error(`Failed to save result for ${result.node_id}:`, error);
            // Don't throw - continue with other nodes
        }
    }

    /**
     * Rollback all changes made in this session
     */
    async rollback(): Promise<void> {
        // Delete edges first (due to dependencies)
        for (const edgeId of this.createdEdgeIds) {
            await this.edgeAPI.deleteEdge(edgeId);
        }
        // Then delete nodes
        for (const nodeId of this.createdNodeIds) {
            await this.nodeAPI.deleteNode(nodeId);
        }
        new Notice('Rollback completed');
    }
}
```

---

### Story 26.3: 批量处理结果合并优化

**优先级**: P2 (Medium)
**估计**: 3 Story Points

#### 描述

优化后端批量处理的结果合并逻辑，支持部分成功、失败重试、进度追踪。

#### 验收标准 (AC)

- [ ] AC 1: 支持部分成功 (10个节点中5个成功则保存5个)
- [ ] AC 2: 失败节点支持单独重试
- [ ] AC 3: 结果包含详细的处理时间统计
- [ ] AC 4: 支持优先级排序 (红色节点优先)
- [ ] AC 5: WebSocket实时推送每个节点状态

#### 技术任务

1. 扩展`call_agents_batch()`支持部分成功返回
2. 实现失败重试队列
3. 添加处理时间统计到`AgentResult`
4. 实现节点优先级排序
5. 优化WebSocket消息格式

#### 关键文件

- `backend/app/services/agent_service.py:498-533`
- `backend/app/api/v1/endpoints/agents.py` (batch endpoint)
- `backend/app/models/schemas.py`

#### 代码变更示例

```python
# agent_service.py
async def call_agents_batch(
    self,
    requests: List[Dict[str, Any]],
    return_exceptions: bool = True,  # 默认返回异常而不是抛出
    priority_sort: bool = True,      # 按优先级排序
    retry_failed: int = 1,           # 失败重试次数
) -> BatchResult:
    """
    Call multiple agents concurrently with enhanced features.

    Returns:
        BatchResult with successful/failed results and statistics
    """
    # Sort by priority if enabled
    if priority_sort:
        requests = self._sort_by_priority(requests)

    # Process with semaphore
    results = []
    failed_requests = []

    for batch in self._chunk(requests, self._max_concurrent):
        batch_results = await asyncio.gather(
            *[self._process_single(req) for req in batch],
            return_exceptions=True
        )

        for req, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                failed_requests.append(req)
            else:
                results.append(result)

    # Retry failed requests
    for _ in range(retry_failed):
        if not failed_requests:
            break
        retry_results = await asyncio.gather(
            *[self._process_single(req) for req in failed_requests],
            return_exceptions=True
        )
        # ... process retry results

    return BatchResult(
        successful=results,
        failed=failed_requests,
        total_time_seconds=elapsed,
        avg_time_per_node=elapsed / len(requests)
    )
```

---

### Story 26.4: 并行处理UI增强

**优先级**: P3 (Low)
**估计**: 2 Story Points

#### 描述

增强`ProgressMonitorModal`的UI体验，添加更多可视化反馈。

#### 验收标准 (AC)

- [ ] AC 1: 显示每个节点的预计剩余时间
- [ ] AC 2: 支持暂停/恢复批量处理
- [ ] AC 3: 显示并发数和队列长度
- [ ] AC 4: 失败节点提供详细错误信息
- [ ] AC 5: 支持最小化到通知区域

#### 技术任务

1. 添加ETA计算逻辑
2. 实现暂停/恢复按钮
3. 添加队列可视化
4. 优化错误展示UI
5. 实现最小化功能

#### 关键文件

- `canvas-progress-tracker/obsidian-plugin/src/modals/ProgressMonitorModal.ts`
- `canvas-progress-tracker/obsidian-plugin/styles.css`

---

## 4. 依赖关系

### 4.1 Epic依赖

```
Epic 21 (Agent流程) ──→ Epic 26 (并行处理)
    │                     │
    │  确保单节点流程正确   │  批量处理依赖单节点逻辑
    │                     │
    └─────────────────────┘
```

### 4.2 Story依赖

```
Story 26.1 ──→ Story 26.3 ──→ Story 26.4
(可配置并发)   (结果合并)     (UI增强)
     │
     └──────→ Story 26.2
              (结果保存) ⭐ 核心
```

**关键路径**: Story 26.2 (结果保存) 是核心，应最先实现。

---

## 5. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| Canvas文件并发写入冲突 | 高 | 高 | 使用文件锁 + 队列写入 |
| 大量节点导致OOM | 中 | 高 | 分批处理 + 内存监控 |
| WebSocket断连丢失进度 | 中 | 中 | Polling回退 + 服务端状态持久化 |
| 用户关闭Modal导致数据丢失 | 中 | 中 | 自动保存 + 恢复机制 |

---

## 6. 测试策略

### 6.1 单元测试

- `test_agent_service_concurrent.py` - 并发数配置测试
- `test_batch_result.py` - 批量结果合并测试

### 6.2 集成测试

- `test_progress_monitor_save.py` - 前端保存逻辑测试
- `test_parallel_e2e.py` - 端到端并行处理测试

### 6.3 性能测试

- 10节点并行: < 30秒
- 50节点并行: < 120秒
- 内存使用: < 500MB (50节点)

---

## 7. 完成标准

- [ ] 所有4个Stories完成
- [ ] 并发数可配置 (5-50)
- [ ] 批量处理结果实际保存到Canvas
- [ ] 支持部分成功和失败重试
- [ ] UI显示实时进度和预计时间
- [ ] 测试覆盖率 > 80%

---

## 8. 参考资料

- [Epic 21](./EPIC-21-AGENT-E2E-FLOW-FIX.md) - Agent端到端流程 (依赖)
- [ProgressMonitorModal源码](../../canvas-progress-tracker/obsidian-plugin/src/modals/ProgressMonitorModal.ts)
- [AgentService源码](../../backend/app/services/agent_service.py)
- [obsidian-canvas Skill](/.claude/skills/obsidian-canvas/SKILL.md) - Canvas API参考
