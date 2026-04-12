# Story 1.5: 白板数据同步到后端 KG

Status: ready-for-dev

## Story

As a 用户,
I want 白板上的节点和连线自动同步到后端 Neo4j 知识图谱,
so that 后端算法（检索、精通度追踪等）能访问我的知识结构。

## Acceptance Criteria

1. **AC-1: Delta Sync 自动触发**
   - **Given** 用户在白板上创建/修改/删除节点或连线
   - **When** 操作完成后 500ms-1s 内
   - **Then** SyncEngine 自动消费 `sync_outbox` 队列中的变更记录
   - **And** 通过 delta sync 将变更批量 POST 到后端 `/api/v1/sync/` 端点
   - **And** 同步延迟 < 1s（从用户操作到后端写入完成）
   - **And** 使用 2s debounce 合并高频操作（如连续拖拽移动），避免过多请求

2. **AC-2: 乐观更新（前端即时生效）**
   - **Given** 用户执行白板操作
   - **When** 操作发生
   - **Then** UI 即时生效（IndexedDB 已在 Story 1.4 中完成写入），不等待后端确认
   - **And** 后端同步在后台异步进行，用户无感知
   - **And** 同步成功后更新 Outbox 条目的 `syncedAt` 字段
   - **And** 同步失败不影响前端操作体验

3. **AC-3: Outbox 队列暂存与指数退避重放**
   - **Given** 后端不可达（Docker 未启动 / Neo4j 宕机 / 网络错误）
   - **When** SyncEngine 尝试同步失败
   - **Then** 变更保留在 `sync_outbox` 队列中不丢失
   - **And** SyncEngine 进入指数退避重试（2s → 4s → 8s → 16s → 32s，最多 5 次）
   - **And** 5 次全部失败后 SyncEngine 状态切换为 OFFLINE，停止重试
   - **And** 后端恢复后（健康检查成功），自动从 OFFLINE 切换为 IDLE，重新消费队列
   - **And** 队列按创建时间顺序重放，保证操作顺序

4. **AC-4: Neo4j 幂等写入**
   - **Given** Outbox 中的变更需要写入 Neo4j
   - **When** 后端 sync API 接收到批量同步请求
   - **Then** 使用 Neo4j `MERGE` 语句实现幂等写入（重复提交不产生重复数据）
   - **And** 每条变更携带幂等 UUID（复用 IndexedDB 中节点/边的 id）
   - **And** 创建操作 → `MERGE (n:CanvasNode {id: $id}) SET n += $props`
   - **And** 删除操作 → `MATCH (n {id: $id}) DETACH DELETE n`
   - **And** 节点删除时级联删除关联的边（DETACH DELETE）

5. **AC-5: IndexedDB 与 Neo4j 最终一致**
   - **Given** 用户操作写入 IndexedDB，SyncEngine 异步同步到 Neo4j
   - **When** 同步完成
   - **Then** Neo4j 中的节点和边数据与 IndexedDB 一致（最终一致性）
   - **And** 已同步的 Outbox 条目标记 `syncedAt` 时间戳
   - **And** 已同步的 Outbox 条目定期清理（保留最近 24h，防止表无限增长）

6. **AC-6: 同步状态可视化**
   - **Given** SyncEngine 处于不同状态（IDLE / SYNCING / OFFLINE）
   - **When** 状态变化
   - **Then** 全局 SyncIndicator 组件显示同步状态
   - **And** IDLE：无显示（默认正常状态）
   - **And** SYNCING：显示同步中指示（如旋转图标）
   - **And** OFFLINE：显示离线警告（红色指示 + "后端不可达"提示文字）
   - **And** 同步失败时通过 Obsidian Notice 提示用户

7. **AC-7: 后端 Sync API 端点**
   - **Given** 前端 SyncEngine 发送批量同步请求
   - **When** `POST /api/v1/sync/batch` 接收请求
   - **Then** 后端解析 SyncBatchRequest（包含多条 SyncOperation）
   - **And** 按操作类型（create/update/delete）和实体类型（node/edge/board）分发到 Neo4j
   - **And** 返回每条操作的处理结果（成功/失败+原因）
   - **And** 单条失败不影响其他条目处理（部分成功）
   - **And** 所有写入在同一 Neo4j 事务中执行（原子性）

8. **AC-8: 多学科隔离预留**
   - **Given** 白板数据同步到 Neo4j
   - **When** 创建节点/边
   - **Then** Neo4j 节点携带 `subjectId` 属性（Story 1.9 将使用）
   - **And** Neo4j 节点携带 `canvasId` 属性用于白板级别隔离
   - **And** 查询时支持按 `subjectId` 和 `canvasId` 过滤

## Tasks / Subtasks

- [ ] **Task 1: SyncEngine 核心——Outbox 消费与状态机** (AC: #1, #2, #3)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/services/sync-engine.ts`
  - [ ] 1.2 实现 SyncEngine 状态机：
    ```typescript
    type SyncState = 'IDLE' | 'SYNCING' | 'OFFLINE';
    ```
    - IDLE → SYNCING：Outbox 有未同步条目时触发
    - SYNCING → IDLE：批量同步成功
    - SYNCING → OFFLINE：连续 5 次同步失败
    - OFFLINE → IDLE：健康检查恢复成功
  - [ ] 1.3 实现 Outbox 轮询消费：
    - 使用 `setInterval` 或 Dexie liveQuery 监听 `sync_outbox` 表
    - 2s debounce：收到新条目后等待 2s，合并期间的所有新条目为一批
    - 按 `createdAt` 升序读取未同步条目（`syncedAt IS NULL`）
    - 每批最多 50 条操作
  - [ ] 1.4 实现批量同步请求：
    - 将 Outbox 条目转换为 `SyncBatchRequest` 格式
    - 调用 `apiClient.post('/api/v1/sync/batch', request)`
    - 响应处理：成功条目更新 `syncedAt`，失败条目保留重试
  - [ ] 1.5 实现指数退避重试：
    - 失败后延迟重试：2s → 4s → 8s → 16s → 32s
    - 5 次全部失败 → 状态切换为 OFFLINE
    - 记录每次失败的错误信息到日志
  - [ ] 1.6 实现 OFFLINE 恢复检测：
    - OFFLINE 状态下每 30s 调用 `apiClient.get('/api/v1/system/health')` 检查后端状态
    - 健康检查成功 → 切换为 IDLE → 自动重新消费 Outbox
    - 健康检查失败 → 保持 OFFLINE，继续等待
  - [ ] 1.7 导出 singleton `export const syncEngine = new SyncEngine()`
  - [ ] 1.8 在 Plugin `onload` 中调用 `syncEngine.start()`，`onunload` 中调用 `syncEngine.stop()`

- [ ] **Task 2: Outbox 清理与数据维护** (AC: #5)
  - [ ] 2.1 实现已同步条目清理：
    - 定期（每 1 小时）清理 `syncedAt` 超过 24 小时的 Outbox 条目
    - 使用 Dexie `where('syncedAt').below(cutoff).delete()`
  - [ ] 2.2 实现 Outbox 统计：
    - 提供方法 `getPendingCount(): Promise<number>` 供 UI 查询待同步数量
    - 提供方法 `getOldestPending(): Promise<Date | null>` 供 UI 显示最早未同步时间

- [ ] **Task 3: 同步状态 Store 更新** (AC: #6)
  - [ ] 3.1 修改 `obsidian-canvas-learning/src/stores/system-state.svelte.ts`（Story 1.1 已创建骨架）：
    - 追加 `syncState: SyncState = $state<SyncState>('IDLE')`
    - 追加 `pendingSyncCount: number = $state(0)`
    - 追加 `lastSyncError: string | null = $state(null)`
    - 追加 `lastSuccessfulSync: Date | null = $state(null)`
  - [ ] 3.2 SyncEngine 状态变化时同步更新 system-state：
    - `syncEngine.onStateChange(state => systemState.syncState = state)`
    - 同步成功时 `systemState.lastSuccessfulSync = new Date()`
    - 同步失败时 `systemState.lastSyncError = error.message`

- [ ] **Task 4: SyncIndicator 全局 UI 组件** (AC: #6)
  - [ ] 4.1 创建 `obsidian-canvas-learning/src/components/global/SyncIndicator.svelte`
  - [ ] 4.2 实现三态显示：
    ```html
    <div class="cl-global-sync-indicator">
      {#if syncState === 'SYNCING'}
        <span class="cl-global-sync-spinning" title="正在同步...">⟳</span>
      {:else if syncState === 'OFFLINE'}
        <span class="cl-global-sync-offline" title="后端不可达">
          <span class="cl-global-sync-dot cl-global-sync-dot--red"></span>
          后端离线
        </span>
      {/if}
      <!-- IDLE 状态不显示任何内容 -->
    </div>
    ```
  - [ ] 4.3 同步失败时调用 `new Notice('同步失败: ' + error, 5000)`（Obsidian 原生通知）
  - [ ] 4.4 在 App.svelte 底部固定位置挂载 SyncIndicator（全局可见）
  - [ ] 4.5 CSS 使用 Obsidian 变量：
    - 同步中旋转动画：`@keyframes cl-spin`
    - 离线红点：`background: var(--text-error)`
    - 适配 Light/Dark 主题

- [ ] **Task 5: 后端 Sync API 端点** (AC: #7, #4, #8)
  - [ ] 5.1 创建 `backend/app/models/sync_models.py`：
    ```python
    class SyncOperation(BaseModel):
        operation_id: str          # 幂等 UUID
        entity_type: Literal['node', 'edge', 'board']
        entity_id: str             # 实体 UUID
        operation: Literal['create', 'update', 'delete']
        payload: dict[str, Any]    # 实体属性（create/update 时携带）
        timestamp: datetime        # 前端操作时间戳

    class SyncBatchRequest(BaseModel):
        canvas_id: str
        subject_id: str | None = None
        operations: list[SyncOperation]

    class SyncOperationResult(BaseModel):
        operation_id: str
        success: bool
        error: str | None = None

    class SyncBatchResponse(BaseModel):
        results: list[SyncOperationResult]
        synced_count: int
        failed_count: int
    ```
  - [ ] 5.2 创建 `backend/app/api/v1/sync.py`：
    - `POST /api/v1/sync/batch` → 接收 SyncBatchRequest → 调用 sync_service → 返回 SyncBatchResponse
    - 请求验证：operations 非空，每条 operation 格式合法
    - 错误处理：Neo4j 连接失败 → 503 Service Unavailable
  - [ ] 5.3 在 `backend/app/main.py` 的 FastAPI router 中注册 sync API

- [ ] **Task 6: 后端 Sync Service——Neo4j 幂等写入** (AC: #4, #8)
  - [ ] 6.1 创建 `backend/app/services/sync_service.py`
  - [ ] 6.2 实现 `process_sync_batch(request: SyncBatchRequest) -> SyncBatchResponse`：
    - 在单个 Neo4j 事务中处理所有操作（原子性）
    - 按操作类型分发到对应 Cypher 语句
  - [ ] 6.3 实现 Node 同步 Cypher：
    - **create/update**:
      ```cypher
      MERGE (n:CanvasNode {id: $entity_id})
      SET n.title = $title,
          n.content = $content,
          n.x = $x, n.y = $y,
          n.width = $width, n.height = $height,
          n.canvasId = $canvas_id,
          n.subjectId = $subject_id,
          n.type = $type,
          n.updatedAt = $timestamp
      ON CREATE SET n.createdAt = $timestamp
      ```
    - **delete**:
      ```cypher
      MATCH (n:CanvasNode {id: $entity_id})
      DETACH DELETE n
      ```
  - [ ] 6.4 实现 Edge 同步 Cypher：
    - **create/update**:
      ```cypher
      MATCH (source:CanvasNode {id: $source_node_id})
      MATCH (target:CanvasNode {id: $target_node_id})
      MERGE (source)-[e:CANVAS_EDGE {id: $entity_id}]->(target)
      SET e.label = $label,
          e.canvasId = $canvas_id,
          e.updatedAt = $timestamp
      ON CREATE SET e.createdAt = $timestamp
      ```
    - **delete**:
      ```cypher
      MATCH ()-[e:CANVAS_EDGE {id: $entity_id}]->()
      DELETE e
      ```
  - [ ] 6.5 实现 Board 同步 Cypher：
    - **create/update**:
      ```cypher
      MERGE (b:CanvasBoard {id: $entity_id})
      SET b.name = $name,
          b.subjectId = $subject_id,
          b.updatedAt = $timestamp
      ON CREATE SET b.createdAt = $timestamp
      ```
    - **delete**:
      ```cypher
      MATCH (b:CanvasBoard {id: $entity_id})
      OPTIONAL MATCH (n:CanvasNode {canvasId: $entity_id})
      DETACH DELETE b, n
      ```
  - [ ] 6.6 错误处理：
    - 单条操作异常捕获，记录错误到 SyncOperationResult，不中断其他操作
    - Neo4j 连接异常 → 整个事务回滚 → 返回所有操作失败
    - 日志记录每次同步的操作数量、耗时、成功/失败数

- [ ] **Task 7: API Client 扩展** (AC: #1, #3)
  - [ ] 7.1 修改 `obsidian-canvas-learning/src/services/api-client.ts`（Story 1.1 已创建）：
    - 追加 `syncBatch(request: SyncBatchRequest): Promise<SyncBatchResponse>` 方法
    - 追加错误分类：网络错误 → `SyncNetworkError`，服务端错误 → `SyncServerError`
  - [ ] 7.2 追加前端类型定义到 `obsidian-canvas-learning/src/types/api.d.ts`：
    - `SyncBatchRequest`、`SyncBatchResponse`、`SyncOperation`、`SyncOperationResult`
    - 字段名使用 camelCase（前端规范），api-client 内部处理 snake_case 转换

- [ ] **Task 8: 集成与端到端验证** (AC: #1, #2, #3, #4, #5)
  - [ ] 8.1 修改 `main.ts`：Plugin `onload` 中启动 SyncEngine，`onunload` 中停止
  - [ ] 8.2 端到端验证场景：
    - 创建节点 → 等待 2s → 检查 Neo4j 中存在对应节点
    - 修改节点 → 等待 2s → 检查 Neo4j 节点属性更新
    - 删除节点 → 等待 2s → 检查 Neo4j 节点已删除 + 关联边已删除
    - 创建/删除边 → 验证 Neo4j 关系正确
  - [ ] 8.3 离线恢复场景：
    - 停止后端 → 执行白板操作 → 确认 Outbox 累积 → 启动后端 → 确认自动重放 → 验证 Neo4j 数据
  - [ ] 8.4 幂等性验证：
    - 同一批操作重复提交 2 次 → 确认 Neo4j 数据正确无重复

## Dev Notes

### Brownfield 上下文

Story 1.4 已创建白板 CRUD 核心功能，包含：
- `dexie-db.ts`：IndexedDB Schema v1（`canvas_boards`、`canvas_nodes`、`canvas_edges`、`sync_outbox` 四张表）
- `canvas-state.svelte.ts`：白板状态 Store，每个写操作同步写入 `sync_outbox` 表
- `api-client.ts`：基础 REST 封装（Story 1.1 创建）
- `system-state.svelte.ts`：全局系统状态骨架（Story 1.1 创建）

本 Story 消费 Story 1.4 预留的 `sync_outbox` 表，实现 SyncEngine 自动同步到后端 Neo4j。

### 同步架构（Outbox 模式）

```
用户操作白板节点 → CanvasView 捕获事件
  → canvasState.addNode() → Dexie 写入 IndexedDB + sync_outbox（Story 1.4 已完成）
  → SyncEngine 轮询 sync_outbox（本 Story 实现）
  → 2s debounce 合并批量操作
  → POST /api/v1/sync/batch
  → sync_service.py → Neo4j MERGE 幂等写入
  → WebSocket: sync_status → system-state → SyncIndicator 更新
```

**关键设计决策（来自 Architecture 文档）：**
- **乐观更新**：前端操作即时生效（IndexedDB），后端同步异步进行
- **Outbox 模式**：2s debounce → 批量 POST → 幂等 UUID → 指数退避
- **单用户不需要 CRDT**：last-write-wins 冲突策略
- **SyncEngine 状态机**：IDLE → SYNCING → OFFLINE，三态切换

### SyncEngine 状态机

```
                     ┌─────────┐
                     │  IDLE   │
                     └───┬─────┘
                         │ Outbox 有待同步条目
                         ▼
                     ┌─────────┐
              ┌──────│ SYNCING │──────┐
              │      └─────────┘      │
         同步成功                 连续5次失败
              │                       │
              ▼                       ▼
         ┌─────────┐           ┌──────────┐
         │  IDLE   │           │ OFFLINE  │
         └─────────┘           └────┬─────┘
                                    │ 健康检查恢复
                                    ▼
                               ┌─────────┐
                               │  IDLE   │
                               └─────────┘
```

### 重试策略

| 场景 | 策略 | 参数 |
|------|------|------|
| 后端 sync | 指数退避 | 2s → 4s → 8s → 16s → 32s，最多 5 次 |
| OFFLINE 健康检查 | 定时轮询 | 每 30s 调用 `/api/v1/system/health` |
| Outbox 清理 | 定时任务 | 每 1h 清理 syncedAt > 24h 的条目 |

### Neo4j 数据模型

```
(:CanvasBoard {id, name, subjectId, createdAt, updatedAt})

(:CanvasNode {id, canvasId, subjectId, type, title, content, x, y, width, height, createdAt, updatedAt})

(:CanvasNode)-[:CANVAS_EDGE {id, canvasId, label, createdAt, updatedAt}]->(:CanvasNode)
```

- 节点标签：`CanvasBoard`、`CanvasNode`（PascalCase，Neo4j 规范）
- 关系类型：`CANVAS_EDGE`（UPPER_SNAKE_CASE，Neo4j 规范）
- 属性名：camelCase（与前端一致，简化映射）
- `subjectId` 和 `canvasId` 预留多学科和白板级隔离

### 命名规范速查（本 Story 涉及）

- 前端 Service 文件：`kebab-case.ts`（如 `sync-engine.ts`）
- 前端组件文件：`PascalCase.svelte`（如 `SyncIndicator.svelte`）
- 后端 API 文件：`snake_case.py`（如 `sync.py`）
- 后端 Service 文件：`snake_case.py`（如 `sync_service.py`）
- 后端 Model 文件：`snake_case.py`（如 `sync_models.py`）
- CSS 类名：`cl-global-sync-*`（G 组全局 UI）
- API 端点路径：`/api/v1/sync/`（RESTful snake_case）
- Neo4j 标签：`PascalCase`（`CanvasNode`）
- Neo4j 关系类型：`UPPER_SNAKE_CASE`（`CANVAS_EDGE`）

### 不做的事项（防蔓延 DD-10）

- 不实现 WebSocket 实时推送同步状态（远期 Story，本 Story 用 Store 更新）
- 不实现 Neo4j → IndexedDB 反向同步（单用户单设备，无此需求）
- 不实现冲突检测与合并（单用户 last-write-wins 足够）
- 不实现 LanceDB 索引触发（Story 2.x 检索管道负责）
- 不实现 Graphiti 写入（Story 3.x 对话系统负责三通道写入）
- 不实现 Board 删除的级联清理 LanceDB 索引（后续 Story）
- 不修改 `dexie-db.ts` Schema（复用 Story 1.4 的 Schema v1）
- 不修改 `canvas-state.svelte.ts` 的 Outbox 写入逻辑（复用 Story 1.4 已实现的写入）

### 共享文件编辑规则

| 文件 | 规则 |
|------|------|
| `api-client.ts` | 追加 `syncBatch()` 方法和错误类型；保持 Story 1.1 的健康检查逻辑 |
| `types/api.d.ts` | 追加 Sync 相关类型定义；保持 Story 1.1 的 HealthResponse |
| `system-state.svelte.ts` | 追加 syncState/pendingSyncCount/lastSyncError 字段；保持已有字段 |
| `main.ts` | 追加 SyncEngine start/stop 调用；保持 Story 1.1/1.4 的初始化逻辑 |
| `App.svelte` | 追加 SyncIndicator 组件挂载；保持 Story 1.4 的路由逻辑 |

### Project Structure Notes

本 Story 新增/修改的文件清单：

```
obsidian-canvas-learning/
├── main.ts                                    # [修改] 追加 SyncEngine start/stop
├── src/
│   ├── App.svelte                             # [修改] 追加 SyncIndicator 挂载
│   ├── components/
│   │   └── global/
│   │       └── SyncIndicator.svelte           # [新建] 同步状态指示器
│   ├── stores/
│   │   └── system-state.svelte.ts             # [修改] 追加 sync 相关状态字段
│   ├── services/
│   │   ├── sync-engine.ts                     # [新建] SyncEngine 核心
│   │   └── api-client.ts                      # [修改] 追加 syncBatch 方法
│   └── types/
│       └── api.d.ts                           # [修改] 追加 Sync 类型定义

backend/
├── app/
│   ├── api/v1/
│   │   └── sync.py                            # [新建] Sync API 端点
│   ├── services/
│   │   └── sync_service.py                    # [新建] Neo4j 幂等写入服务
│   ├── models/
│   │   └── sync_models.py                     # [新建] Sync Pydantic Models
│   └── main.py                                # [修改] 注册 sync router
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions] — Frontend-first IndexedDB local-first + Outbox delta sync
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies] — Outbox 模式 delta sync (2s debounce → 批量 POST → 幂等 UUID → 指数退避)，SyncEngine 状态机 (IDLE→SYNCING→OFFLINE)
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture] — 同步架构 Outbox 模式 → Neo4j/SQLite/LanceDB 三端，last-write-wins
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns] — 后端 sync Outbox 指数退避 2s→4s→8s→16s→32s 最多 5 次，Neo4j CircuitBreaker CLOSED→OPEN(5次失败)→HALF_OPEN(30s)
- [Source: _bmad-output/planning-artifacts/architecture.md#Integration Points] — 白板操作流：canvasState.addNode() → Dexie → Outbox → sync-engine(2s debounce) → POST /api/v1/sync/ → Neo4j MERGE
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries] — 数据同步 REST `/api/v1/sync/` 批量幂等同步
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns] — 命名规范（Neo4j PascalCase 标签/UPPER_SNAKE 关系/camelCase 属性），sync-engine.ts 工具命名
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure] — sync-engine.ts 在 services/ 目录，sync.py 在 api/v1/ 目录，sync_service.py 在 services/ 目录
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns] — 数据同步一致性（Outbox 模式 + 乐观更新 + last-write-wins），离线降级（Neo4j 异常 → 队列暂存）
- [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines] — 禁止组件直接操作 IndexedDB，通过 Store 方法
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5] — AC 和 Story 需求
- [Source: _bmad-output/planning-artifacts/epics.md#NFR] — NFR-PERF-02 节点 CRUD 同步 < 500ms，NFR-REL-01 数据零丢失，NFR-REL-03 Neo4j 异常降级
- [Source: _bmad-output/implementation-artifacts/1-4-canvas-core-crud-mini-dashboard.md] — Story 1.4 Outbox 预留上下文（sync_outbox 表已创建，canvasState 每个写操作写 Outbox）

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
