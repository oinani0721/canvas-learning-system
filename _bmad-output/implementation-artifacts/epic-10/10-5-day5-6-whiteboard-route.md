---
story_id: "10.5"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 24
depends_on: ["10.4"]
blocks: ["10.6"]
trace: ["FR-DEEP-05", "S4", "M9", "M12", "UX-3"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 5-6"
target_date: "2026-05-11 ~ 2026-05-12"
solution: "方案 Y (Agent 2.5 推荐)"
graph_lib: "ReactFlow (cp Canvas 代码)"
uat_sheet: "_bmad-output/验收单/Story-10.5-day5-6-whiteboard-route.md"
---

# Story 10.5: Day 5-6 Whiteboard 路由 + ReactFlow（方案 Y）

**Status**: ready-for-dev (target Day 5-6, 2026-05-11 ~ 2026-05-12)

## Story（用户故事）

As a 学习者, I want a `/whiteboard` route in DeepTutor where I can see my entire vault knowledge graph as an interactive whiteboard — click nodes to see details, drag to rearrange, with mastery-colored nodes — so that "原白板作为 index 呈现各节点关系" 的 Canvas 范式完整承载。

> **映射对**: M9（拆分点 + 双链 → Graphiti）+ M12（5 大核心总结）+ UX-3（跨概念学习路径）
> **方案选择**: Agent 2.5 方案 Y（中等改造，18-24h，与 10 天 MVP 契合）

## 通俗化解释（给学习者）

> **一句话说**: 在 DeepTutor 加一个"白板视图"页面，全 vault 节点画在一张图上，可以点击、拖拽、缩放，节点颜色显示你的掌握度。

**你会遇到的场景**:
- 进入 DeepTutor 左侧菜单点 "Whiteboard"
- 看到全 vault 节点关系图（不是 Mermaid 静态图）
- 点节点 → 右侧 chat panel 打开该节点详情
- 节点颜色：绿（高掌握度）/ 黄 / 红（低）

**这个功能帮你**:
- 全局学习地图（不限于单个 book 的 ConceptGraph）
- 可交互（不是 Mermaid 那种"看图玩物"）
- 跨概念学习路径（学新概念时看到旧概念关联，UX-3 痛点）

**用个比喻**: 🗺️ 就像 Google Maps 的"我的地点"——所有去过的地方都标在一张地图上，颜色表示喜欢程度，可以点开看详情。

## Acceptance Criteria

### AC #1: Whiteboard 后端 3 endpoint

- **Given** fork backend 加新 router
- **When** 启动 fork
- **Then** 新增 3 个 endpoint:
  - `POST /api/v1/whiteboard/` 创建白板（payload: `{title, vault_id?}`）
  - `GET /api/v1/whiteboard/:id/graph` 返回 `{nodes: [{id, label, mastery, chapter}], edges: [{src, dst, relation, weight}]}`
  - `POST /api/v1/whiteboard/:id/pull-node` 通过 AI 拉新节点
- **And** 后端代理到 Canvas Neo4j 查 nodes + edges + mastery

### AC #2: Whiteboard 前端 ReactFlow UI

- **Given** fork 加 reactflow npm package
- **When** 用户访问 `/whiteboard/:id` 路由
- **Then** ReactFlow canvas 渲染节点 + 边
- **And** 节点按 mastery 着色（绿/黄/红 3 级）
- **And** 边按 relation 类型样式（depends_on 实线、extends 虚线、related 点划线）
- **And** 节点可拖、可缩放、可平移

### AC #3: 节点点击 → ChatPanel sidebar

- **Given** Whiteboard 已加载
- **When** 用户点击某个节点（如 "recursion"）
- **Then** 右侧 ChatPanel 打开
- **And** 显示节点详情（title, chapter, mastery%, last_review）
- **And** 可在 ChatPanel 直接对话该节点（context = 节点 metadata）

### AC #4: 验证场景 S4 通过

- **Given** Day 4 已注入 vault 为 book + Whiteboard 后端可用
- **When** 用户访问 `/whiteboard/<book_id>`
- **Then** 渲染 ≥ 10 节点 + 边
- **And** 节点拖拽流畅（不卡）
- **And** 点节点跳到 ChatPanel ✓

## Tasks / Subtasks

### Backend (Day 5 上午, 6h)

- [ ] Task 1: whiteboard router (AC: #1)
  - [ ] 1.1: 新建 `deeptutor/api/routers/whiteboard.py`
  - [ ] 1.2: 实现 3 个 endpoint
  - [ ] 1.3: register 到 main.py（参考 Story 10.2 wikilink_proxy 模式）

- [ ] Task 2: Canvas backend graph query
  - [ ] 2.1: CanvasClient 加 `get_whiteboard_graph(book_id)` 方法
  - [ ] 2.2: 调 Canvas `/api/v1/wikilink/build` 取节点 + 边
  - [ ] 2.3: 调 Canvas `/api/v1/mastery/batch` 取每个节点的 mastery

### Frontend (Day 5 下午 + Day 6, 12h)

- [ ] Task 3: 安装 ReactFlow + 路由 (AC: #2)
  - [ ] 3.1: `cd ~/Desktop/canvas/deeptutor-fork/web && npm install reactflow`
  - [ ] 3.2: 新建 `web/app/(workspace)/whiteboard/[id]/page.tsx`
  - [ ] 3.3: 路由：`/whiteboard/:id`

- [ ] Task 4: WhiteboardCanvas 组件 (AC: #2)
  - [ ] 4.1: 新建 `web/app/(workspace)/whiteboard/components/WhiteboardCanvas.tsx`
  - [ ] 4.2: import ReactFlow + Controls + Background
  - [ ] 4.3: 节点 fetch: `GET /api/v1/whiteboard/:id/graph`
  - [ ] 4.4: 自定义节点组件 (mastery 着色) + 自定义边组件 (relation 样式)

- [ ] Task 5: NodeContextMenu + ChatPanel sidebar (AC: #3)
  - [ ] 5.1: 新建 `web/app/(workspace)/whiteboard/components/NodeDetailPanel.tsx`
  - [ ] 5.2: 节点 onClick → setSelectedNode(node) → 打开侧栏
  - [ ] 5.3: 侧栏显示 metadata + ChatPanel（cp 现有 chat 组件）

- [ ] Task 6: WorkspaceSidebar 加 Whiteboard tab
  - [ ] 6.1: Edit `web/components/Workspace/WorkspaceSidebar.tsx`
  - [ ] 6.2: 加 "Whiteboard" tab 按钮 → navigate `/whiteboard/default`

### Test + Integration (Day 6 下午, 4-6h)

- [ ] Task 7: Backend test
  - [ ] 7.1: `tests/whiteboard/test_router.py` 验证 3 endpoint
  - [ ] 7.2: Mock Canvas 响应 → assert nodes + edges 转换正确

- [ ] Task 8: E2E (AC: #4)
  - [ ] 8.1: 创建 vault 含 ≥10 节点的测试数据
  - [ ] 8.2: Day 4 注入 → Day 5-6 在 Whiteboard 可见
  - [ ] 8.3: 点节点 → ChatPanel 弹出 ✓
  - [ ] 8.4: 性能：10/50/100 节点拖拽流畅度

## Dev Notes

### 为什么 ReactFlow 而非 Cytoscape

- Cytoscape v3.33.1 已装在 fork package.json 但**未用**（Agent 2.1 发现）
- ReactFlow 已在 Canvas 验证（cp Canvas `App.tsx` ReactFlow 实现节省时间）
- npm install reactflow 1 min，对比 Cytoscape 重写交互 = 1 day 多
- **决策**: Day 5 选 ReactFlow，Cytoscape 闲置（production 阶段再决定）

### 方案 Y vs X vs Z（Agent 2.5）
- **方案 X 轻**: 复用 ConceptGraphBlock 加全屏路由（4-6h）— 仍是单 book 内
- **方案 Y 中（选）**: 新建 `/whiteboard` 路由 + ReactFlow + 后端 Neo4j（18-24h）— 跨 book 全景
- **方案 Z 重**: 重构 Space 主页（40-50h）— 超时不可行

### 与 ConceptGraphBlock 的差异
- ConceptGraphBlock: 单 book 内嵌 Mermaid 静态
- Whiteboard: 全 vault 跨 book ReactFlow 可交互

### 风险
- **R6 性能**: 1000+ 节点 ReactFlow 可能卡 UI → 缓解：2-hop 限制、虚拟滚动
- **node 过多 viewport**: ReactFlow 默认 fitView 自动缩放

## UAT 验收

详见 `_bmad-output/验收单/Story-10.5-day5-6-whiteboard-route.md`

## References

- Deep Explore §2.5 原白板模式 vs DeepTutor UX 改造方案
- Deep Explore §3.3 Day 5-6 路线
- Canvas worktree `frontend/src/App.tsx` ReactFlow 实现（Story 1.x）

## 下一步

→ Story 10.6 Day 7 MasteryDashboard Block（节点掌握度数据落地）
