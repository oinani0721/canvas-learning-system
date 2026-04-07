# FR-KG-05 MVP — 设计文档

## 架构决策

### D1: Settings 开关存储方式 → localStorage
沿用 Settings.tsx 现有模式（`SETTINGS_KEY = 'canvas-learning-settings'`），在 `SettingsData` 接口中加 `enableRecommendations: boolean`，默认 `false`。

### D2: 推荐状态管理 → Hook 内部 state
不创建新 Zustand store。用 `useRecommendations` hook 内部的 `useState` 管理推荐列表和忽略列表。理由：推荐数据是临时的、非共享的，不需要全局 store。

### D3: 忽略记录 → 内存暂存（Session 级别）
本次不加 Dexie 表。忽略记录存在 hook 的 `useState` 中，刷新会丢失。这是已知限制，延后到 Pipe#6/7 修复。

### D4: UI 形态 → 底部浮动推荐栏
参考 Story 1.7 规范的 RecommendationBar 设计。固定在 Canvas 底部，可折叠。

## 数据流

```
Settings (localStorage)
  │ enableRecommendations = true?
  ▼
useRecommendations(boardId, nodes, edges)
  │
  ├─ 检查：开关开 && 节点数 ≥ 5 && 有未连线节点
  │
  ├─ 5s debounce 后调用 fetchRecommendations()
  │     ├─ canvasId = boardId
  │     └─ dismissedPairs = 内存中已忽略的对
  │
  ├─ 返回 { recommendations, accept, dismiss, loading }
  │
  ▼
RecommendationBar
  ├─ 显示推荐卡片列表
  ├─ [接受] → canvas-store.addEdge(source, target, label)
  └─ [忽略] → hook 内部加入 dismissedPairs，从列表移除
```

## 组件设计

### useRecommendations hook

```typescript
// 输入
boardId: string | null
nodes: Node[]           // 来自 useBoardNodes
edges: Edge[]           // 来自 useBoardEdges
enabled: boolean        // 来自 Settings

// 输出
recommendations: Recommendation[]
loading: boolean
accept: (rec: Recommendation) => void
dismiss: (rec: Recommendation) => void
```

**触发条件**：
- `enabled === true`
- `boardId` 不为空
- 节点数 ≥ 5
- 存在未连线的节点（通过 edges 计算）

**防抖**：节点/边变化后等 5s 再请求。用 `useEffect` + `setTimeout`。

### RecommendationBar 组件

```
┌─────────────────────────────────────────────────────────┐
│ 💡 发现 2 组概念可能有关联                    [▼ 折叠]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  线性代数 ↔ 矩阵运算   82%  内容相似                    │
│  [✅ 接受连线]  [❌ 忽略]                               │
│                                                         │
│  Python ↔ TensorFlow   67%  共同关联2个概念             │
│  [✅ 接受连线]  [❌ 忽略]                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**状态**：
- `collapsed` / `expanded`（默认 expanded）
- `loading`（请求中显示 spinner）
- `empty`（无推荐时隐藏整个栏）

### Settings.tsx 改动

在现有设置面板中加一个 section：

```
┌─ 功能开关 ──────────────────────────────────┐
│                                              │
│  概念关联推荐  [━━━━○ 关]                    │
│  系统自动分析节点间的潜在关联并给出建议        │
│                                              │
└──────────────────────────────────────────────┘
```

## 复用的现有代码

| 现有代码 | 位置 | 复用方式 |
|---------|------|---------|
| `fetchRecommendations()` | api-client.ts:722 | 直接调用 |
| `Recommendation` 类型 | types.ts:472 | 直接使用 |
| `RecommendationResponse` 类型 | types.ts:484 | 直接使用 |
| `addEdge()` | canvas-store.ts:285 | 接受推荐时调用 |
| `SETTINGS_KEY` + localStorage 模式 | Settings.tsx:57 | 沿用同一 key |
| `useBoardNodes` / `useBoardEdges` | useBoardData.ts | 作为 hook 输入 |
