# Story 1.7: 概念关联推荐

Status: ready-for-dev

## Story

As a 用户,
I want 系统基于知识图谱分析为我推荐可能的概念关联,
so that 我能发现未注意到的知识关系。

## Acceptance Criteria

1. **AC-1: 触发条件——5+ 未连线节点**
   - **Given** 白板上有 5 个以上未连线的知识节点（即该节点无任何 CANVAS_EDGE 连接）
   - **When** 用户完成节点创建/删除/连线操作后，系统在后台自动分析
   - **Then** 后端 `/api/v1/canvas/recommendations` 返回推荐列表
   - **And** 分析仅在节点/边变更时触发（debounce 5s），不持续轮询
   - **And** 白板节点总数 < 5 时不触发分析，返回空列表

2. **AC-2: 分析策略——内容相似度 + 已有连线模式**
   - **Given** 后端收到推荐分析请求
   - **When** 分析引擎执行
   - **Then** 使用两层分析策略：
     - **L1 文本相似度**：对未连线节点对计算 title+content 的语义相似度（bge-m3 embedding cosine similarity），相似度 > 阈值（默认 0.6）的节点对进入候选
     - **L2 图模式分析**：分析已有连线模式（如 A→B, A→C 且 B/C 内容相似，推荐 B→C），利用 Neo4j 2-hop 邻居共现检测
   - **And** 两层结果合并去重，按置信度降序排列
   - **And** 每次最多返回 5 条推荐（避免信息过载）
   - **And** 已被用户忽略的节点对在 24h 内不再重复推荐

3. **AC-3: 推荐 UI 展示——非模态提示**
   - **Given** 后端返回推荐列表（非空）
   - **When** 前端接收到推荐数据
   - **Then** 在白板底部显示可折叠的推荐面板（RecommendationBar 组件）
   - **And** 面板默认折叠为一行提示："发现 N 条可能的概念关联"，点击展开
   - **And** 展开后每条推荐显示：节点 A 名称 + 节点 B 名称 + 推荐理由简述
   - **And** 推荐面板不遮挡白板操作（底部固定，高度受限）
   - **And** 推荐面板有关闭按钮，关闭后在本次会话中不再弹出（除非新增推荐）

4. **AC-4: 接受推荐——自动创建连线**
   - **Given** 用户查看推荐列表
   - **When** 用户点击某条推荐的"接受"按钮
   - **Then** 系统自动在节点 A 和节点 B 之间创建连线（CANVAS_EDGE）
   - **And** 连线使用推荐算法建议的语义标签（如"相关概念"/"前置知识"等），用户可事后修改
   - **And** 创建的连线走 Story 1.4 的正常 CRUD 流程 + Story 1.5 的 sync 同步到 Neo4j
   - **And** 该条推荐从列表中移除
   - **And** 接受操作触发 Obsidian Notice "已创建连线: A → B"

5. **AC-5: 忽略推荐——标记不再推荐**
   - **Given** 用户查看推荐列表
   - **When** 用户点击某条推荐的"忽略"按钮
   - **Then** 该条推荐从列表中移除
   - **And** 该节点对被记录到 IndexedDB `dismissed_recommendations` 表（带时间戳）
   - **And** 24h 内不再推荐该节点对
   - **And** 忽略操作静默执行，不弹出任何提示

6. **AC-6: 性能与降级**
   - **Given** 后端推荐分析可能耗时
   - **When** 分析执行
   - **Then** 前端不阻塞白板操作（异步请求）
   - **And** 后端分析超时 5s 则返回空列表（不影响其他 API）
   - **And** 后端不可达时静默跳过推荐（不显示错误，推荐是增强功能非核心功能）
   - **And** Neo4j 中节点 < 5 时直接返回空，不执行分析（O(1) 快速退出）

## Tasks / Subtasks

- [ ] **Task 1: 后端推荐分析服务** (AC: #1, #2)
  - [ ] 1.1 创建 `backend/app/services/recommendation_service.py`
  - [ ] 1.2 实现 `get_unconnected_nodes(canvas_id: str) -> list[CanvasNode]`：
    - Cypher 查询白板中没有任何 CANVAS_EDGE 的 CanvasNode
    ```cypher
    MATCH (n:CanvasNode {canvasId: $canvas_id})
    WHERE NOT (n)-[:CANVAS_EDGE]-() AND NOT (n)<-[:CANVAS_EDGE]-()
    RETURN n
    ```
  - [ ] 1.3 实现 `compute_text_similarity(nodes: list[CanvasNode]) -> list[RecommendationCandidate]`：
    - 对未连线节点构建 title+content 文本
    - 调用 bge-m3 embedding（复用 LanceDB 管道的 embedding 能力）
    - 计算节点对之间的 cosine similarity
    - 过滤 similarity > 阈值（默认 0.6，可配置）的节点对
  - [ ] 1.4 实现 `detect_graph_patterns(canvas_id: str, unconnected_ids: list[str]) -> list[RecommendationCandidate]`：
    - Cypher 检测 2-hop 邻居共现：
    ```cypher
    MATCH (a:CanvasNode {canvasId: $canvas_id})-[:CANVAS_EDGE*1..2]-(shared)-[:CANVAS_EDGE*1..2]-(b:CanvasNode {canvasId: $canvas_id})
    WHERE a.id IN $unconnected_ids AND b.id IN $unconnected_ids
      AND a.id < b.id
      AND NOT (a)-[:CANVAS_EDGE]-(b)
    RETURN a.id AS source_id, b.id AS target_id, count(shared) AS shared_neighbors
    ORDER BY shared_neighbors DESC
    ```
  - [ ] 1.5 实现 `generate_recommendations(canvas_id: str, dismissed_pairs: list[tuple]) -> list[Recommendation]`：
    - 快速退出：节点 < 5 返回空列表
    - L1 文本相似度 + L2 图模式分析
    - 合并去重（同一节点对只保留最高置信度来源）
    - 过滤已忽略的节点对（dismissed_pairs）
    - 按置信度降序排列，截取 top-5
    - 生成推荐理由简述（基于来源：相似度→"内容相似"/图模式→"共同关联 N 个概念"）
    - 整体超时 5s，超时返回空列表
  - [ ] 1.6 实现推荐标签建议逻辑：
    - 基于节点内容和已有连线的标签分布，建议语义标签
    - 默认标签候选列表：`["相关概念", "前置知识", "应用关系", "对比关系", "包含关系"]`
    - 选择策略：如果白板已有连线标签，优先使用已有标签中出现频率最高的；否则使用"相关概念"

- [ ] **Task 2: 后端推荐 Pydantic Models** (AC: #2, #4)
  - [ ] 2.1 创建 `backend/app/models/recommendation_models.py`：
    ```python
    class RecommendationCandidate(BaseModel):
        source_node_id: str
        target_node_id: str
        confidence: float        # 0.0 ~ 1.0
        source_type: Literal['text_similarity', 'graph_pattern']
        reason: str              # 推荐理由简述

    class Recommendation(BaseModel):
        id: str                  # UUID
        source_node_id: str
        source_node_title: str
        target_node_id: str
        target_node_title: str
        confidence: float
        reason: str
        suggested_label: str     # 建议的连线语义标签

    class RecommendationResponse(BaseModel):
        recommendations: list[Recommendation]
        canvas_id: str
        analyzed_at: datetime
    ```

- [ ] **Task 3: 后端推荐 API 端点** (AC: #1, #6)
  - [ ] 3.1 修改 `backend/app/api/v1/canvas.py`，追加推荐端点：
    - `POST /api/v1/canvas/{canvas_id}/recommendations`
    - 请求体：`DismissedPairsRequest(dismissed_pairs: list[DismissedPair])`
    - 响应：`RecommendationResponse`
    - 超时控制：asyncio.wait_for 5s
    - Neo4j 不可用时返回空列表 + 200（非 503）
  - [ ] 3.2 在 `backend/app/main.py` 中确认 canvas router 已注册（Story 1.5 已注册）

- [ ] **Task 4: 前端推荐 Store** (AC: #1, #3, #5)
  - [ ] 4.1 修改 `obsidian-canvas-learning/src/stores/canvas-state.svelte.ts`，追加推荐相关状态：
    - `recommendations: Recommendation[] = $state([])`
    - `recommendationBarVisible: boolean = $state(false)`
    - `recommendationBarExpanded: boolean = $state(false)`
    - `dismissedSessionClosed: boolean = $state(false)` — 本次会话是否关闭了面板
  - [ ] 4.2 追加方法：
    - `async fetchRecommendations(canvasId: string): Promise<void>` — 调用 API 获取推荐
    - `acceptRecommendation(recId: string): void` — 创建连线 + 移除该推荐
    - `dismissRecommendation(recId: string): void` — 记录忽略 + 移除
    - `closeRecommendationBar(): void` — 关闭面板
  - [ ] 4.3 实现 5s debounce 触发机制：
    - 监听节点/边的增删改操作
    - 操作后 5s debounce 调用 `fetchRecommendations`
    - 只在白板当前节点总数 >= 5 时触发

- [ ] **Task 5: IndexedDB dismissed_recommendations 表** (AC: #5)
  - [ ] 5.1 修改 `obsidian-canvas-learning/src/services/dexie-db.ts`：
    - Schema 版本升级（v2），新增 `dismissed_recommendations` 表
    ```typescript
    dismissed_recommendations: '++id, pairKey, dismissedAt'
    // pairKey = `${nodeId_A}_${nodeId_B}`（排序后拼接，确保唯一）
    ```
  - [ ] 5.2 实现辅助方法：
    - `dismissPair(nodeIdA: string, nodeIdB: string): Promise<void>`
    - `getDismissedPairs(canvasId: string): Promise<DismissedPair[]>` — 过滤 24h 内的
    - `cleanExpiredDismissals(): Promise<void>` — 清理超过 24h 的记录

- [ ] **Task 6: RecommendationBar 前端组件** (AC: #3, #4, #5)
  - [ ] 6.1 创建 `obsidian-canvas-learning/src/components/canvas/RecommendationBar.svelte`
  - [ ] 6.2 实现折叠态：
    ```html
    <div class="cl-canvas-recommendation-bar cl-canvas-recommendation-bar--collapsed">
      <span class="cl-canvas-recommendation-badge">{count}</span>
      <span>发现 {count} 条可能的概念关联</span>
      <button onclick={expand}>展开</button>
      <button onclick={close} title="关闭">×</button>
    </div>
    ```
  - [ ] 6.3 实现展开态：
    ```html
    <div class="cl-canvas-recommendation-bar cl-canvas-recommendation-bar--expanded">
      <div class="cl-canvas-recommendation-header">
        <span>概念关联推荐</span>
        <button onclick={collapse}>收起</button>
        <button onclick={close} title="关闭">×</button>
      </div>
      {#each recommendations as rec}
        <div class="cl-canvas-recommendation-item">
          <span class="cl-canvas-recommendation-nodes">
            {rec.sourceNodeTitle} ↔ {rec.targetNodeTitle}
          </span>
          <span class="cl-canvas-recommendation-reason">{rec.reason}</span>
          <button class="cl-canvas-recommendation-accept" onclick={() => accept(rec.id)}>
            接受
          </button>
          <button class="cl-canvas-recommendation-dismiss" onclick={() => dismiss(rec.id)}>
            忽略
          </button>
        </div>
      {/each}
    </div>
    ```
  - [ ] 6.4 CSS 样式：
    - 底部固定定位，`position: absolute; bottom: 0; left: 0; right: 0;`
    - 展开态最大高度 200px，超出滚动
    - 使用 Obsidian CSS 变量：`var(--background-secondary)`, `var(--text-normal)`, `var(--interactive-accent)`
    - 适配 Light/Dark 主题
    - 关闭/收起按钮不遮挡白板
  - [ ] 6.5 在 `CanvasView.svelte` 底部挂载 RecommendationBar（仅当 `recommendationBarVisible && !dismissedSessionClosed` 时渲染）

- [ ] **Task 7: API Client 扩展** (AC: #1)
  - [ ] 7.1 修改 `obsidian-canvas-learning/src/services/api-client.ts`：
    - 追加 `fetchRecommendations(canvasId: string, dismissedPairs: DismissedPair[]): Promise<RecommendationResponse>`
    - 错误处理：网络错误 / 超时 → 返回空推荐列表（静默降级）
  - [ ] 7.2 追加前端类型定义到 `obsidian-canvas-learning/src/types/canvas.d.ts`：
    - `Recommendation`、`RecommendationResponse`、`DismissedPair`

- [ ] **Task 8: 集成与端到端验证** (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 8.1 端到端验证场景——推荐触发：
    - 创建 6 个内容相关的节点（如"线性代数"、"矩阵"、"向量空间"、"特征值"、"行列式"、"线性变换"）
    - 不创建任何连线
    - 等待 5s debounce → 确认推荐面板出现
    - 验证推荐内容合理（如"矩阵 ↔ 行列式"）
  - [ ] 8.2 端到端验证场景——接受推荐：
    - 点击"接受" → 确认连线自动创建
    - 确认连线同步到 Neo4j（Story 1.5 sync）
    - 确认该推荐从列表移除
  - [ ] 8.3 端到端验证场景——忽略推荐：
    - 点击"忽略" → 确认推荐移除
    - 刷新/重新触发推荐 → 确认该对 24h 内不再出现
  - [ ] 8.4 端到端验证场景——降级：
    - 停止后端 → 执行白板操作 → 确认无错误弹出，推荐面板不显示
  - [ ] 8.5 端到端验证场景——关闭面板：
    - 关闭推荐面板 → 确认本次会话不再弹出
    - 新增节点后有新推荐 → 面板重新出现（dismissedSessionClosed 重置）

## Dev Notes

### Brownfield 上下文

Story 1.5 已实现白板数据同步到后端 Neo4j，包含：
- `sync-engine.ts`：Outbox 消费与 SyncEngine 状态机
- `sync_service.py`：Neo4j MERGE 幂等写入
- `dexie-db.ts`：IndexedDB Schema v1（`canvas_boards`、`canvas_nodes`、`canvas_edges`、`sync_outbox` 四张表）
- `canvas-state.svelte.ts`：白板状态 Store，CRUD 方法和 Outbox 写入

Story 1.4 已实现白板 CRUD 核心功能，包含：
- `CanvasView.svelte`：自建 HTML+SVG 混合渲染画布
- `CanvasNode.svelte` / `CanvasEdge.svelte`：节点和连线组件
- 节点/连线的创建/编辑/删除完整流程

本 Story 在此基础上新增概念关联推荐功能，作为增强功能（非核心功能），降级策略简单——不可用时静默跳过。

### 架构决策说明

**概念关联推荐标注为"MVP 可延后"**（见 Architecture Deferred Decisions），但仍是 Epic 1 的 Story 且对应 FR-KG-05。本 Story 的实现策略是：
- **轻量级实现**：不引入复杂的图神经网络或深度学习模型
- **复用现有基础设施**：bge-m3 embedding（Ollama 容器已有）+ Neo4j Cypher 查询
- **非阻塞设计**：推荐功能完全异步，不影响白板核心操作

### 推荐分析流程

```
用户操作节点/连线 → canvasState 事件触发
  → 5s debounce（避免频繁分析）
  → 检查节点总数 >= 5（否则跳过）
  → 从 IndexedDB 读取 dismissed_recommendations（24h 内）
  → POST /api/v1/canvas/{canvas_id}/recommendations
  → 后端分析：
      → 查询未连线节点（Cypher）
      → L1: bge-m3 文本相似度（cosine > 0.6）
      → L2: 2-hop 邻居共现检测（Cypher）
      → 合并去重 + 过滤已忽略 + top-5
      → 生成推荐理由 + 建议标签
  → 前端接收 → 更新 Store → 显示 RecommendationBar
```

### 推荐置信度计算

| 来源 | 置信度计算 | 说明 |
|------|-----------|------|
| L1 文本相似度 | cosine_similarity 直接作为置信度 | 范围 0.6~1.0 |
| L2 图模式分析 | min(shared_neighbors / 3, 1.0) | 共享 3+ 邻居则满置信度 |
| 合并 | max(L1_confidence, L2_confidence) | 同一对取最高 |

### 不做的事项（防蔓延 DD-10）

- 不实现基于 LLM 的深度关系推理（成本高、延迟大，远期 Phase 2+）
- 不实现推荐理由的详细解释对话（保持轻量，点击接受即创建连线）
- 不实现推荐的用户反馈学习（不根据用户接受/忽略历史调整模型）
- 不实现跨白板推荐（仅白板内推荐）
- 不实现推荐的 WebSocket 实时推送（用 REST 轮询 + debounce 即可）
- 不修改 `CanvasNode.svelte` 或 `CanvasEdge.svelte`（推荐通过 Store 方法创建连线，复用现有流程）
- 不修改 `sync-engine.ts`（接受推荐创建的连线走正常 Outbox 同步）

### 共享文件编辑规则

| 文件 | 规则 |
|------|------|
| `canvas-state.svelte.ts` | 追加 recommendations/recommendationBar 相关状态和方法；保持 Story 1.4/1.5 的节点/连线/Outbox 逻辑 |
| `dexie-db.ts` | Schema 升级到 v2，新增 `dismissed_recommendations` 表；保持 Story 1.4 的四张表 |
| `api-client.ts` | 追加 `fetchRecommendations()` 方法；保持 Story 1.1/1.5 的现有方法 |
| `types/canvas.d.ts` | 追加 Recommendation 相关类型定义；保持 Story 1.4 的节点/边类型 |
| `CanvasView.svelte` | 底部追加 RecommendationBar 组件挂载；保持 Story 1.4 的画布渲染逻辑 |
| `canvas.py`（后端） | 追加推荐 API 端点；保持 Story 1.5 的 CRUD/sync 端点 |
| `main.py`（后端） | 确认 canvas router 已注册即可；无需修改 |

### Project Structure Notes

本 Story 新增/修改的文件清单：

```
obsidian-canvas-learning/
├── src/
│   ├── components/
│   │   └── canvas/
│   │       └── RecommendationBar.svelte           # [新建] 推荐面板组件
│   ├── stores/
│   │   └── canvas-state.svelte.ts                 # [修改] 追加推荐相关状态和方法
│   ├── services/
│   │   ├── dexie-db.ts                            # [修改] Schema v2 新增 dismissed_recommendations
│   │   └── api-client.ts                          # [修改] 追加 fetchRecommendations 方法
│   └── types/
│       └── canvas.d.ts                            # [修改] 追加 Recommendation 类型定义

backend/
├── app/
│   ├── api/v1/
│   │   └── canvas.py                              # [修改] 追加推荐 API 端点
│   ├── services/
│   │   └── recommendation_service.py              # [新建] 推荐分析服务
│   └── models/
│       └── recommendation_models.py               # [新建] 推荐 Pydantic Models
```

### 命名规范速查（本 Story 涉及）

- 前端组件文件：`PascalCase.svelte`（如 `RecommendationBar.svelte`）
- 后端 Service 文件：`snake_case.py`（如 `recommendation_service.py`）
- 后端 Model 文件：`snake_case.py`（如 `recommendation_models.py`）
- CSS 类名：`cl-canvas-recommendation-*`（E 组白板 UI）
- API 端点路径：`/api/v1/canvas/{canvas_id}/recommendations`
- Neo4j 标签：`CanvasNode`（复用 Story 1.5）
- Neo4j 关系类型：`CANVAS_EDGE`（复用 Story 1.5）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.7] — AC 和 Story 需求（5+ 未连线节点、分析内容+连线模式、接受/忽略、非模态提示）
- [Source: _bmad-output/planning-artifacts/prd.md#FR-KG-05] — "系统可以为用户推荐可能的概念关联（基于知识图谱分析）"
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — 概念关联推荐（图分析，MVP可延后）
- [Source: _bmad-output/planning-artifacts/architecture.md#Deferred Decisions] — 概念关联推荐图分析（MVP 可延后）
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture] — Neo4j 5.x + Graphiti（graphiti_core 内嵌方案 C）
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns] — 命名规范（Neo4j PascalCase 标签/UPPER_SNAKE 关系/camelCase 属性）
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — 前端 components/canvas/ 目录、后端 services/ 和 models/ 目录
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries] — `/api/v1/canvas/` 白板数据端点前缀
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns] — 错误处理分层、加载状态规范
- [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines] — Svelte cl- 前缀 CSS、禁止组件直接操作 IndexedDB
- [Source: _bmad-output/implementation-artifacts/1-4-canvas-core-crud-mini-dashboard.md] — Story 1.4 白板 CRUD 上下文（CanvasView、节点/边组件、dexie-db Schema v1）
- [Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md] — Story 1.5 数据同步上下文（SyncEngine、Neo4j 数据模型、sync Outbox）
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Obsidian Components] — Notice 类用于轻量通知

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
