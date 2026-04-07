# FR-KG-05 MVP — 实施任务

## ~~Task 1: Settings 开关~~ [x]
**文件**: `frontend/src/components/Settings.tsx`
**改动**:
- `SettingsData` 接口加 `enableRecommendations: boolean`
- `DEFAULT_SETTINGS` 加 `enableRecommendations: false`
- UI 加功能开关 section（toggle 样式，参考现有 UI 模式）
**验收**: Settings 面板中可见开关，开关状态保存到 localStorage

## ~~Task 2: useRecommendations hook~~ [x]
**文件**: `frontend/src/hooks/useRecommendations.ts`（新建）
**依赖**: Task 1 完成（需要读取 Settings）
**改动**:
- 读取 localStorage 中 `enableRecommendations` 值
- 接收 boardId、nodes、edges 参数
- 计算未连线节点数，不满足条件时返回空
- 5s debounce 后调用 `apiClient.fetchRecommendations()`
- 管理 recommendations state 和 dismissedPairs state（内存级）
- 暴露 `accept(rec)` 和 `dismiss(rec)` 方法
**验收**:
- Given 开关关闭 When 画布有 10 个节点 Then 不触发 API 请求
- Given 开关打开 When 节点数 < 5 Then 不触发
- Given 开关打开 When 节点数 ≥ 5 且有未连线节点 Then 5s 后触发请求

## ~~Task 3: RecommendationBar 组件~~ [x]
**文件**: `frontend/src/components/RecommendationBar.tsx`（新建）
**依赖**: Task 2 完成（需要 hook 提供数据）
**改动**:
- 固定在 Canvas 底部的浮动栏
- 折叠/展开状态切换
- 每条推荐显示：源节点 ↔ 目标节点、置信度百分比、原因
- [接受] 按钮 → 调用 `canvasStore.addEdge()`
- [忽略] 按钮 → 调用 hook 的 `dismiss()`
- 无推荐时完全隐藏
- loading 状态显示 spinner
**验收**:
- Given 有推荐 When 栏展开 Then 显示推荐卡片列表
- Given 点击接受 When 推荐 "A↔B" Then Canvas 上出现 A→B 的连线
- Given 点击忽略 When 推荐 "A↔B" Then 该卡片从列表消失
- Given 无推荐 Then 推荐栏不显示

## ~~Task 4: 挂载到 App~~ [x]
**文件**: `frontend/src/App.tsx`
**依赖**: Task 2 + Task 3 完成
**改动**:
- 在 Canvas 视图区域内引入 `useRecommendations` hook
- 将 hook 返回值传给 `RecommendationBar` 组件
- RecommendationBar 定位在 ReactFlow 容器底部
**验收**: 完整端到端流程可用（Settings 开关 → 触发 → 显示 → 接受/忽略）

## 实施顺序

```
Task 1 (Settings 开关)
    │
    ▼
Task 2 (useRecommendations hook)
    │
    ▼
Task 3 (RecommendationBar 组件)
    │
    ▼
Task 4 (挂载到 App)
```

## 已知限制（本次不处理）
- 忽略记录刷新即丢失（需 Dexie v6 dismissed_recommendations 表）
- 推荐边和普通边无视觉区分（需自定义 edge 组件）
- 接受推荐时标签为空（需传递 suggestedLabel）
- 忽略记录不跨设备同步（需 Sync Outbox 扩展）
