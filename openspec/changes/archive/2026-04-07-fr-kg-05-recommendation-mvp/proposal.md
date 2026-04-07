# FR-KG-05 概念关联推荐 — MVP 前端接入

## Why

FR-KG-05（系统推荐概念关联）后端已完整实现（L1 bge-m3 余弦相似度 + L2 Neo4j 2-hop），但前端存在 **8 条断裂管道**，导致用户在 Canvas 上完全看不到推荐功能。

详见探索报告：`docs/project-status/fr-exploration/FR-KG-05.md`

目标是用最小改动接通前端管道，让用户能：
1. 在 Settings 中控制推荐功能的开关（默认关闭）
2. 开启后，在 Canvas 上看到系统推荐的概念关联
3. 接受或忽略推荐

## What Changes

### 范围
**做**：
- Settings 开关（Pipe#3 前置条件）
- `useRecommendations` hook 调用 API（Pipe#3）
- RecommendationBar 组件（Pipe#4）
- 5s 防抖触发机制（Pipe#8）

**不做（延后）**：
- Pipe#5：推荐边虚线样式
- Pipe#6/7：Dexie dismissed_recommendations 表（本次用内存 state 暂存）
- Pipe#9：标签建议传递
- Pipe#10：Sync Outbox 扩展

### 影响文件

| 文件 | 改动 |
|------|------|
| `frontend/src/components/Settings.tsx` | 加 `enableRecommendations` 开关 |
| `frontend/src/hooks/useRecommendations.ts` | **新建** — 调用 API + 防抖 + 状态管理 |
| `frontend/src/components/RecommendationBar.tsx` | **新建** — 底部推荐栏 UI |
| `frontend/src/App.tsx` | 挂载 RecommendationBar |
| `frontend/src/stores/canvas-store.ts` | addEdge 接受推荐时调用 |

### 验证方式
1. 启动前端 → Settings → 打开"概念关联推荐"
2. 打开一个有 ≥ 5 个节点的白板，其中至少 2 个未连线
3. 等待 5 秒 → 底部出现推荐栏
4. 点"接受" → 两个节点间出现连线
5. 点"忽略" → 该推荐从列表消失（刷新会重现，这是已知限制）

### 回滚方式
Settings 开关默认关闭，回滚只需：删除新建的 2 个文件 + 还原 Settings.tsx / App.tsx 的改动。
