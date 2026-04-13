# Story 1.4: 白板核心——节点与连线 CRUD + 最小化 Dashboard

Status: ready-for-dev

## Story

As a 用户,
I want 在画布上创建文本节点（双击空白处）、编辑节点内容、删除节点（Delete 键）、通过拖拽创建连线，自由拖拽节点、缩放和平移画布，并有一个最小化 Dashboard 作为白板入口,
so that 我能构建可视化知识图谱，并能浏览和打开已有白板。

## Acceptance Criteria

1. **AC-1: 创建文本节点**
   - **Given** 用户打开一个白板视图
   - **When** 用户双击白板空白处
   - **Then** 在点击位置创建一个新的文本节点，光标自动聚焦到节点内容区域可立即编辑
   - **And** 节点包含 header 区域（用于拖拽移动）和 body 区域（用于编辑内容/选取文字）
   - **And** 节点创建后立即写入 IndexedDB（Dexie.js）

2. **AC-2: 编辑节点内容**
   - **Given** 白板上已有文本节点
   - **When** 用户点击节点 body 区域
   - **Then** 进入编辑模式，可修改节点标题和内容
   - **And** 编辑结果实时保存到 IndexedDB（debounce 300ms）
   - **And** 节点 body 区域支持文字选取（与节点拖拽共存：header 拖拽 / body 文字选取）

3. **AC-3: 删除节点和连线**
   - **Given** 用户选中一个或多个节点/连线
   - **When** 按下 Delete 或 Backspace 键
   - **Then** 选中的节点和连线被删除
   - **And** 删除节点时，与该节点关联的所有连线同步删除
   - **And** 删除操作写入 IndexedDB

4. **AC-4: 拖拽创建连线（Edge）**
   - **Given** 白板上有两个或以上节点
   - **When** 用户从节点边缘拖出连线到另一个节点
   - **Then** 创建一条有向 Edge 连接两个节点
   - **And** 拖拽过程中显示临时连线跟随鼠标
   - **And** 释放在空白区域时取消连线创建
   - **And** 用户可为连线添加语义标签（双击连线弹出输入框）
   - **And** Edge 数据写入 IndexedDB

5. **AC-5: 画布操作（拖拽/缩放/平移）**
   - **Given** 用户在白板视图中
   - **When** 用户左键点击节点 header 区域拖拽
   - **Then** 节点跟随鼠标移动，位置实时更新
   - **And** 右键按住拖拽 / 中键按住拖拽 → 平移画布
   - **And** 鼠标滚轮 → 缩放画布（以鼠标位置为中心缩放）
   - **And** Ctrl+左键 / 框选 → 多选节点
   - **And** 所有操作响应 < 16ms（60fps，NFR-PERF-01）
   - **And** 操作逻辑与 Obsidian Canvas 保持一致（零学习成本）

6. **AC-6: IndexedDB 本地存储（Dexie.js）**
   - **Given** 用户执行任何白板操作（创建/编辑/移动/删除）
   - **When** 操作完成
   - **Then** 数据立即写入 IndexedDB（通过 Dexie.js）
   - **And** Dexie liveQuery 驱动 Svelte Store 实现响应式 UI 更新
   - **And** 白板数据在 Obsidian 重启后完整保留
   - **And** IndexedDB schema 包含 `canvas_boards`、`canvas_nodes`、`canvas_edges`、`sync_outbox` 表

7. **AC-7: 最小化 Dashboard**
   - **Given** 用户点击 Ribbon 图标或通过命令面板打开 Canvas Learning System
   - **When** 右侧面板打开
   - **Then** 显示 DashboardView：列出所有已有白板（名称 + 创建时间 + 节点数量）
   - **And** 点击白板卡片 → 切换到该白板的 CanvasView
   - **And** 提供"新建白板"按钮，点击创建空白白板并进入
   - **And** 无白板时显示空状态引导文字 + 新建按钮

8. **AC-8: 性能要求**
   - **Given** 白板上有 100 个节点和 200 条连线
   - **When** 用户执行拖拽/缩放/平移操作
   - **Then** 操作响应 < 16ms（60fps）
   - **And** 使用 CSS `contain: layout style paint` 限制重绘范围
   - **And** 视口外节点不渲染（视口裁剪 culling）

## Tasks / Subtasks

- [ ] **Task 1: IndexedDB Schema 与 Dexie.js 配置** (AC: #6)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/services/dexie-db.ts`：定义 Dexie 数据库 class `CanvasLearningDB extends Dexie`
  - [ ] 1.2 定义 IndexedDB Schema（version 1）：
    - `canvas_boards`：`id, name, subjectId, createdAt, updatedAt`
    - `canvas_nodes`：`id, canvasId, type, title, content, x, y, width, height, createdAt, updatedAt`
    - `canvas_edges`：`id, canvasId, sourceNodeId, targetNodeId, label, createdAt, updatedAt`
    - `sync_outbox`：`++id, entityType, entityId, operation, payload, createdAt, syncedAt`
  - [ ] 1.3 定义 TypeScript 接口（`obsidian-canvas-learning/src/types/canvas.d.ts`）：
    - `CanvasBoard`：`{ id: string; name: string; subjectId?: string; createdAt: string; updatedAt: string }`
    - `CanvasNodeData`：`{ id: string; canvasId: string; type: 'text' | 'image'; title: string; content: string; x: number; y: number; width: number; height: number; createdAt: string; updatedAt: string }`
    - `CanvasEdgeData`：`{ id: string; canvasId: string; sourceNodeId: string; targetNodeId: string; label: string; createdAt: string; updatedAt: string }`
    - `SyncOutboxEntry`：`{ id?: number; entityType: 'node' | 'edge' | 'board'; entityId: string; operation: 'create' | 'update' | 'delete'; payload: Record<string, unknown>; createdAt: string; syncedAt?: string }`
  - [ ] 1.4 导出 singleton `db` 实例。确保仅 `stores/` 目录可 import `db`（架构边界规则）
  - [ ] 1.5 实现 UUID 生成工具函数（`crypto.randomUUID()`，Electron 环境可用）

- [ ] **Task 2: Svelte Store — canvas-state.svelte.ts** (AC: #1, #2, #3, #4, #6)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/stores/canvas-state.svelte.ts`：使用 Svelte 5 `$state` rune
  - [ ] 2.2 定义 `CanvasState` class，核心状态字段：
    - `boards: CanvasBoard[]` — 所有白板列表
    - `currentBoardId: string | null` — 当前活动白板
    - `nodes: CanvasNodeData[]` — 当前白板的节点（liveQuery 绑定）
    - `edges: CanvasEdgeData[]` — 当前白板的连线（liveQuery 绑定）
    - `selectedNodeIds: Set<string>` — 当前选中的节点 ID
    - `selectedEdgeIds: Set<string>` — 当前选中的连线 ID
    - `viewport: { x: number; y: number; zoom: number }` — 视口状态
  - [ ] 2.3 实现 CRUD 方法（每个方法内部写 IndexedDB + 写 Outbox）：
    - `createBoard(name: string): Promise<CanvasBoard>`
    - `deleteBoard(id: string): Promise<void>`
    - `switchBoard(id: string): Promise<void>` — 切换白板，重新绑定 liveQuery
    - `addNode(node: Partial<CanvasNodeData>): Promise<CanvasNodeData>` — 自动生成 id/timestamps
    - `updateNode(id: string, changes: Partial<CanvasNodeData>): Promise<void>` — debounce 写入
    - `deleteNode(id: string): Promise<void>` — 同时删除关联 edges
    - `addEdge(edge: Partial<CanvasEdgeData>): Promise<CanvasEdgeData>`
    - `updateEdge(id: string, changes: Partial<CanvasEdgeData>): Promise<void>`
    - `deleteEdge(id: string): Promise<void>`
    - `deleteSelected(): Promise<void>` — 批量删除选中项
  - [ ] 2.4 使用 Dexie liveQuery 绑定 nodes 和 edges 到 Svelte Store（响应式）：
    - 当 `currentBoardId` 变化时，重新订阅 `db.canvas_nodes.where('canvasId').equals(boardId)` 的 liveQuery
    - liveQuery 结果自动更新 `nodes` 和 `edges`，驱动 UI 重渲染
  - [ ] 2.5 Outbox 写入：每个写操作同步写入 `sync_outbox` 表（为 Story 1.5 的 delta sync 预留）
  - [ ] 2.6 导出 singleton `export const canvasState = new CanvasState()`

- [ ] **Task 3: CanvasView 组件——HTML+SVG 混合渲染** (AC: #1, #4, #5, #8)
  - [ ] 3.1 创建 `obsidian-canvas-learning/src/components/canvas/CanvasView.svelte`
  - [ ] 3.2 实现渲染架构：
    ```
    <div class="cl-canvas-viewport" style="contain: layout style paint">
      <!-- SVG 层：连线渲染 -->
      <svg class="cl-canvas-edges-layer">
        {#each visibleEdges as edge}
          <CanvasEdge {edge} />
        {/each}
        <!-- 拖拽中的临时连线 -->
        {#if dragEdge}
          <line class="cl-canvas-temp-edge" ... />
        {/if}
      </svg>
      <!-- HTML 层：节点渲染 -->
      <div class="cl-canvas-nodes-layer" style="transform: translate({vp.x}px, {vp.y}px) scale({vp.zoom})">
        {#each visibleNodes as node}
          <CanvasNode {node} />
        {/each}
      </div>
      <!-- 框选层 -->
      {#if selectionBox}
        <div class="cl-canvas-selection-box" ... />
      {/if}
    </div>
    ```
  - [ ] 3.3 实现视口变换管理：
    - 维护 `viewport = $state({ x: 0, y: 0, zoom: 1 })`
    - CSS transform 应用到节点层和边层：`transform: translate(x, y) scale(zoom)`
    - 鼠标滚轮缩放（以鼠标位置为锚点计算新的 translate 偏移）
    - 缩放范围限制：min 0.1 ~ max 5.0
  - [ ] 3.4 实现画布平移：
    - 右键 mousedown → 记录起始点 → mousemove 计算 delta → 更新 viewport.x/y → mouseup 结束
    - 中键同理
    - 阻止右键默认菜单（`contextmenu` preventDefault）
  - [ ] 3.5 实现双击创建节点：
    - `dblclick` 事件 → 计算画布坐标（屏幕坐标 → 逆 viewport 变换） → `canvasState.addNode({ x, y, ... })`
    - 创建后自动聚焦到新节点的编辑区域
  - [ ] 3.6 实现框选多选：
    - 空白区域左键拖拽 → 绘制半透明选择框 → 计算框内节点 → 更新 selectedNodeIds
    - Ctrl+左键单击节点 → 切换选中状态（toggle）
  - [ ] 3.7 实现视口裁剪（culling）：
    - 根据 viewport 计算可见区域边界
    - `visibleNodes = nodes.filter(n => isInViewport(n, viewport))`
    - `visibleEdges = edges.filter(e => isEdgeVisible(e, viewport, nodesMap))`
    - 每帧只渲染可见元素，确保 100+ 节点仍 60fps
  - [ ] 3.8 实现键盘事件处理：
    - Delete / Backspace → `canvasState.deleteSelected()`
    - Ctrl+A → 全选当前白板所有节点
    - Escape → 取消选择

- [ ] **Task 4: CanvasNode 组件** (AC: #1, #2, #3, #5)
  - [ ] 4.1 创建 `obsidian-canvas-learning/src/components/canvas/CanvasNode.svelte`
  - [ ] 4.2 实现节点结构：
    ```html
    <div class="cl-canvas-node"
         class:cl-canvas-node--selected={isSelected}
         style="left: {node.x}px; top: {node.y}px; width: {node.width}px">
      <!-- Header 区域：拖拽手柄 -->
      <div class="cl-canvas-node-header"
           onmousedown={startDrag}>
        {node.title || '未命名节点'}
      </div>
      <!-- Body 区域：内容编辑 + 文字选取 -->
      <div class="cl-canvas-node-body"
           contenteditable={isEditing}
           oninput={handleInput}>
        {node.content}
      </div>
      <!-- 连线端口（四边） -->
      <div class="cl-canvas-node-port cl-canvas-node-port--right"
           onmousedown={startEdgeDrag} />
      <!-- 同理 top/bottom/left -->
    </div>
    ```
  - [ ] 4.3 实现节点拖拽移动：
    - Header 区域 mousedown → 记录初始位置 → document mousemove 更新 `node.x/y` → mouseup 写入 IndexedDB
    - 多选时拖拽一个节点 → 所有选中节点同步移动（计算 delta 分发给每个选中节点）
    - 使用 `requestAnimationFrame` 限制更新频率保证 60fps
  - [ ] 4.4 实现节点内容编辑：
    - 点击 body 区域 → 进入编辑模式（`contenteditable=true`）
    - `input` 事件 → debounce 300ms → `canvasState.updateNode(id, { content })`
    - 点击节点外部 → 退出编辑模式
    - 编辑模式下阻止 Delete 键触发节点删除
  - [ ] 4.5 实现连线端口拖拽：
    - 节点边缘的小圆点（port）mousedown → 开始 edge 创建模式
    - 鼠标移动到另一个节点上方时高亮该节点（可连接提示）
    - 在另一个节点上 mouseup → `canvasState.addEdge({ sourceNodeId, targetNodeId })`
    - 在空白区域 mouseup → 取消
  - [ ] 4.6 实现选中状态：
    - 左键单击节点 → 设为唯一选中项（清除其他选中）
    - Ctrl+左键 → toggle 选中状态
    - 选中节点显示边框高亮 + 调整手柄

- [ ] **Task 5: CanvasEdge 组件** (AC: #4)
  - [ ] 5.1 创建 `obsidian-canvas-learning/src/components/canvas/CanvasEdge.svelte`
  - [ ] 5.2 实现 SVG 连线渲染：
    ```svg
    <g class="cl-canvas-edge" class:cl-canvas-edge--selected={isSelected}>
      <!-- 贝塞尔曲线连线 -->
      <path d={calculateBezierPath(sourcePos, targetPos)}
            stroke="var(--text-muted)"
            fill="none"
            stroke-width="2" />
      <!-- 箭头 -->
      <polygon points={arrowPoints} fill="var(--text-muted)" />
      <!-- 可点击的透明宽线条（增大点击区域） -->
      <path d={calculateBezierPath(sourcePos, targetPos)}
            stroke="transparent"
            fill="none"
            stroke-width="12"
            onclick={handleClick} />
      <!-- 标签 -->
      {#if edge.label}
        <text x={midX} y={midY} class="cl-canvas-edge-label">
          {edge.label}
        </text>
      {/if}
    </g>
    ```
  - [ ] 5.3 实现贝塞尔曲线路径计算：
    - 根据 source 节点和 target 节点的位置计算控制点
    - 连线从 source 节点的最近边缘出发到 target 节点的最近边缘
    - 自适应控制点距离（短连线用直线，长连线用曲线）
  - [ ] 5.4 实现连线选中：
    - 点击连线 → 选中连线（高亮显示）
    - 选中状态：`stroke-width: 3` + 颜色变为 `--interactive-accent`
  - [ ] 5.5 实现语义标签编辑：
    - 双击连线 → 在连线中点位置弹出小输入框
    - 输入标签后回车/点击外部 → `canvasState.updateEdge(id, { label })`
    - 标签显示在连线中点位置（SVG `<text>`）

- [ ] **Task 6: DashboardView 最小化 Dashboard** (AC: #7)
  - [ ] 6.1 创建 `obsidian-canvas-learning/src/components/dashboard/DashboardView.svelte`
  - [ ] 6.2 实现白板列表展示：
    ```html
    <div class="cl-dash-container">
      <div class="cl-dash-header">
        <h3>我的白板</h3>
        <button class="cl-dash-new-btn" onclick={createNewBoard}>+ 新建白板</button>
      </div>
      {#if boards.length === 0}
        <div class="cl-dash-empty">
          <p>还没有白板，创建第一个开始学习吧！</p>
          <button onclick={createNewBoard}>创建白板</button>
        </div>
      {:else}
        <div class="cl-dash-board-list">
          {#each boards as board}
            <CanvasCard {board} onselect={() => openBoard(board.id)} />
          {/each}
        </div>
      {/if}
    </div>
    ```
  - [ ] 6.3 实现新建白板：
    - 点击按钮 → 弹出 Obsidian `Modal` 输入白板名称
    - 确认 → `canvasState.createBoard(name)` → 自动进入新白板
  - [ ] 6.4 实现白板切换：
    - 点击白板卡片 → `canvasState.switchBoard(id)` → 右侧面板从 Dashboard 切换为 CanvasView
    - 切换机制通过 `main-view.ts` 的视图路由状态管理

- [ ] **Task 7: CanvasCard 组件** (AC: #7)
  - [ ] 7.1 创建 `obsidian-canvas-learning/src/components/dashboard/CanvasCard.svelte`
  - [ ] 7.2 实现卡片展示：白板名称 + 创建时间 + 节点数量
  - [ ] 7.3 实现点击事件：`onclick` → 触发 `onselect` prop 回调

- [ ] **Task 8: MainView 视图路由** (AC: #7)
  - [ ] 8.1 修改 `obsidian-canvas-learning/src/views/main-view.ts`（Story 1.1 已创建）：
    - 增加视图路由状态：`'dashboard' | 'canvas'`
    - Dashboard 模式渲染 `DashboardView`
    - Canvas 模式渲染 `CanvasView`
  - [ ] 8.2 创建顶层 App 组件 `obsidian-canvas-learning/src/App.svelte`：
    - 根据路由状态切换 DashboardView / CanvasView
    - 提供返回 Dashboard 的导航按钮（当在 CanvasView 时）
  - [ ] 8.3 修改 `main.ts`（Story 1.1 已创建）：
    - 在 `onload` 中初始化 Dexie 数据库
    - 确保 Dexie 在所有组件 mount 前就绪

- [ ] **Task 9: CSS 样式** (AC: #1, #4, #5, #7, #8)
  - [ ] 9.1 在各 Svelte 组件中使用 scoped CSS + Obsidian CSS 变量
  - [ ] 9.2 节点样式 (`cl-canvas-node-*`)：
    - 背景色 `var(--background-secondary)`，边框 `var(--background-modifier-border)`
    - 选中态边框 `var(--interactive-accent)`
    - Header 区域 cursor: grab（拖拽时 grabbing）
    - Body 区域 cursor: text
    - 圆角 `var(--radius-s)`
  - [ ] 9.3 连线样式 (`cl-canvas-edge-*`)：
    - 默认颜色 `var(--text-muted)`，选中 `var(--interactive-accent)`
    - 标签字体 `var(--font-text-theme)`
  - [ ] 9.4 视口样式 (`cl-canvas-viewport`)：
    - `overflow: hidden`，`position: relative`，`width: 100%`，`height: 100%`
    - `contain: layout style paint`（性能隔离）
    - 背景网格（可选，使用 CSS 背景图案）
  - [ ] 9.5 Dashboard 样式 (`cl-dash-*`)：
    - 使用 Obsidian 变量保持风格一致
    - 卡片间距 `var(--size-4-2)`
  - [ ] 9.6 适配 Light/Dark 主题：全部使用 Obsidian CSS 变量，无硬编码颜色
  - [ ] 9.7 连线端口样式 (`cl-canvas-node-port`)：
    - 默认隐藏，hover 节点时显示
    - 小圆点 6px 半径，`var(--interactive-accent)` 颜色

- [ ] **Task 10: 性能优化** (AC: #8)
  - [ ] 10.1 视口裁剪实现：计算可视区域，过滤只渲染 viewport 内的节点/边
  - [ ] 10.2 CSS containment：viewport 容器添加 `contain: layout style paint`
  - [ ] 10.3 拖拽节流：使用 `requestAnimationFrame` 限制 mousemove 处理频率
  - [ ] 10.4 编辑 debounce：节点内容编辑 300ms debounce 才写 IndexedDB
  - [ ] 10.5 liveQuery 效率：按 canvasId 索引查询，避免全表扫描
  - [ ] 10.6 SVG 路径缓存：连线端点未变化时复用上次计算的 path 字符串

## Dev Notes

### Brownfield 上下文

Story 1.1 已创建前端插件骨架 `obsidian-canvas-learning/`，包含：
- `main.ts`（Plugin 入口 + Ribbon icon + MainView 注册）
- `src/views/main-view.ts`（ItemView 子类，Svelte 5 mount/unmount）
- `src/services/api-client.ts`（基础 REST 封装）
- `src/types/api.d.ts`（HealthResponse 类型）
- 7 个组件子目录结构（chat/exam/dashboard/profile/canvas/system/global）
- esbuild + esbuild-svelte + TypeScript 构建配置

本 Story 在此基础上新增 E 组白板核心组件、C 组 Dashboard 组件、Dexie 数据库、canvas-state Store。

### 自建 Svelte Canvas 架构

**渲染模式：HTML 节点 + SVG 边混合渲染**（参考 Svelte Flow / tldraw 验证）

```
CanvasView (容器，含视口变换)
├── SVG Layer — CanvasEdge 组件（贝塞尔曲线连线 + 箭头 + 标签）
├── HTML Layer — CanvasNode 组件（DOM 节点，支持 contenteditable 编辑）
└── Overlay Layer — 框选矩形、拖拽临时连线
```

优势：
- HTML 节点可直接使用 `contenteditable` 实现富文本编辑
- SVG 连线渲染平滑，支持贝塞尔曲线和箭头
- 与 tldraw、Excalidraw、Svelte Flow 同架构模式
- CSS `contain` 隔离重绘，保证 60fps

### IndexedDB Schema 设计

```typescript
// Dexie Schema Version 1
const schema = {
  canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
  canvas_nodes: 'id, canvasId, type, title, x, y, createdAt, updatedAt',
  canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
  sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt'
};
```

- 表名 snake_case 复数，字段名 camelCase（架构规范）
- `sync_outbox` 为 Story 1.5 delta sync 预留，本 Story 仅写入不消费
- ID 使用 `crypto.randomUUID()` 生成（Electron 环境可用）
- `subjectId` 为 Story 1.9 多学科隔离预留，MVP 暂不使用

### Dexie liveQuery → Svelte Store 绑定

```typescript
// canvas-state.svelte.ts 中的 liveQuery 绑定模式
import { liveQuery } from 'dexie';
import { db } from '../services/dexie-db';

class CanvasState {
  nodes = $state<CanvasNodeData[]>([]);
  private subscription: { unsubscribe(): void } | null = null;

  async switchBoard(boardId: string) {
    // 取消旧订阅
    this.subscription?.unsubscribe();
    // 建立新订阅
    const observable = liveQuery(() =>
      db.canvas_nodes.where('canvasId').equals(boardId).toArray()
    );
    this.subscription = observable.subscribe(result => {
      this.nodes = result;
    });
  }
}
```

liveQuery 在 IndexedDB 数据变更时自动触发回调，Svelte 5 `$state` 自动驱动 UI 更新，实现完整的响应式链路。

### 视口变换坐标系

```
屏幕坐标 (screenX, screenY)
  ↓ 逆 viewport 变换
画布坐标 (canvasX, canvasY) = ((screenX - vp.x) / vp.zoom, (screenY - vp.y) / vp.zoom)
```

节点的 `x, y` 存储画布坐标，渲染时通过 CSS `transform` 应用 viewport 变换。

### 白板操作交互表（与 Obsidian Canvas 保持一致）

| 操作 | 交互方式 | 实现位置 |
|------|---------|---------|
| 移动节点 | 左键点击节点 header 拖拽 | CanvasNode.svelte |
| 移动白板 | 右键/中键按住拖拽 | CanvasView.svelte |
| 缩放白板 | 鼠标滚轮 | CanvasView.svelte |
| 选中节点 | 左键点击节点 | CanvasNode.svelte |
| 多选节点 | Ctrl+左键 / 框选 | CanvasView.svelte |
| 创建连线 | 从节点边缘拖出到另一节点 | CanvasNode.svelte + CanvasView.svelte |
| 创建节点 | 双击白板空白处 | CanvasView.svelte |
| 删除节点/连线 | 选中 + Delete/Backspace | CanvasView.svelte |
| 选中文字（节点内） | 左键在节点 body 区域拖选 | CanvasNode.svelte |

### 命名规范速查（本 Story 涉及）

- Svelte 组件文件：`PascalCase.svelte`（如 `CanvasView.svelte`）
- Store 文件：`kebab-case.svelte.ts`（如 `canvas-state.svelte.ts`）
- Service 文件：`kebab-case.ts`（如 `dexie-db.ts`）
- CSS 类名：`cl-canvas-*`（E 组白板）、`cl-dash-*`（C 组 Dashboard）
- TypeScript 变量/函数：`camelCase`
- TypeScript 类名：`PascalCase`
- IndexedDB 表名：`snake_case` 复数
- IndexedDB 字段名：`camelCase`

### 不做的事项（防蔓延 DD-10）

- 不实现后端 API 同步（Story 1.5）
- 不实现 sync-engine 消费 outbox 队列（Story 1.5）
- 不实现节点颜色精通度映射（Story 5.2）
- 不实现 EdgeDialogTrigger 连线对话图标（Story 4.1）
- 不实现 ChatPanel 对话面板（Story 3.3）
- 不实现 ImageNode 图片节点（Story 1.6）
- 不实现 FSRS 复习列表（Story 5.4）
- 不实现考察入口/模式选择（Story 5.4, 6.2）
- 不实现 WebSocket 实时推送（后续 Story）
- 不实现 NodeContextMenu 右键菜单（后续 Story，本 Story 仅阻止默认右键菜单用于平移）
- 不实现 ViewportCuller 独立组件（本 Story 内置在 CanvasView 中作为计算逻辑）
- 不实现 Settings Tab / 模型配置（Story 1.3）
- DashboardView 仅列出白板和打开白板，完整 Dashboard 功能（FSRS 复习/检验白板历史/Token 成本）留 Epic 5

### 共享文件编辑规则

| 文件 | 规则 |
|------|------|
| `dexie-db.ts` | 本 Story 创建 Schema v1；后续 Schema 变更必须独立 Story |
| `types/canvas.d.ts` | 本 Story 创建基础类型；后续新增字段只能追加 |
| `main-view.ts` | 修改已有文件添加视图路由；保持 Story 1.1 的 Svelte mount/unmount 逻辑 |
| `main.ts` | 修改已有文件添加 Dexie 初始化；保持 Story 1.1 的 Ribbon icon 和 View 注册 |
| `styles.css` | 本 Story 仅追加 cl-canvas-* 和 cl-dash-* 基础变量映射（如有需要） |

### 60fps 性能保证策略

1. **CSS `contain: layout style paint`** — 限制节点重绘不波及容器
2. **视口裁剪 (culling)** — 视口外节点/边不渲染，减少 DOM 节点数
3. **`requestAnimationFrame`** — 拖拽/缩放操作通过 rAF 节流
4. **Dexie 写入 debounce** — 编辑内容 300ms debounce，拖拽结束才写位置
5. **CSS `transform`** — 视口平移/缩放用 GPU 加速的 transform，不重排布局
6. **SVG 路径缓存** — 端点未变时复用贝塞尔曲线 path 字符串

### Project Structure Notes

本 Story 新增/修改的文件清单：

```
obsidian-canvas-learning/
├── main.ts                                    # [修改] 添加 Dexie 初始化
├── src/
│   ├── App.svelte                             # [新建] 顶层路由组件
│   ├── components/
│   │   ├── canvas/
│   │   │   ├── CanvasView.svelte              # [新建] 白板主视图
│   │   │   ├── CanvasNode.svelte              # [新建] 节点组件
│   │   │   └── CanvasEdge.svelte              # [新建] 连线组件
│   │   └── dashboard/
│   │       ├── DashboardView.svelte           # [新建] 最小化 Dashboard
│   │       └── CanvasCard.svelte              # [新建] 白板卡片
│   ├── stores/
│   │   └── canvas-state.svelte.ts             # [新建] 白板状态 Store
│   ├── services/
│   │   └── dexie-db.ts                        # [新建] IndexedDB Schema + Dexie
│   ├── views/
│   │   └── main-view.ts                       # [修改] 添加视图路由
│   ├── types/
│   │   └── canvas.d.ts                        # [新建] 白板类型定义
│   └── utils/
│       └── canvas-math.ts                     # [新建] 视口变换 + 贝塞尔曲线计算
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions] — 自建 Svelte Canvas HTML+SVG 混合渲染，Frontend-first IndexedDB local-first + Dexie.js liveQuery
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies] — 视口裁剪+CSS containment 保证 60fps，Outbox 模式 delta sync
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns] — 命名规范（IndexedDB 表名 snake_case 复数，字段名 camelCase），CSS cl- 前缀
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries] — 前端目录结构，dexie-db.ts 仅 stores/ 可 import，组件禁止直接操作 IndexedDB
- [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines] — 共享文件加法编辑规则，Store 访问控制
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#白板操作交互] — 操作交互表（拖拽/缩放/平移/连线/多选/创建/删除），与 Obsidian Canvas 保持一致
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — E 组白板组件（CanvasView/CanvasNode/CanvasEdge）、C 组 Dashboard 组件（DashboardView/CanvasCard）
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#CSS 隔离策略] — Svelte scoped CSS + cl- 前缀 + Obsidian CSS 变量
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#面板切换模式] — 右侧面板永远只显示一个视图，切换即替换不叠加
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/epics.md#NFR] — NFR-PERF-01 白板操作 < 16ms 60fps
- [Source: _bmad-output/implementation-artifacts/1-1-project-scaffold-docker-setup.md] — Story 1.1 项目结构上下文

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
