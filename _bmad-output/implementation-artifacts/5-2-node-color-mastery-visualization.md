# Story 5.2: 节点颜色精通度可视化

Status: ready-for-dev

## Story

As a 用户,
I want 白板上的节点颜色反映掌握程度，一眼看出哪些学得好哪些薄弱,
so that 我对学习全貌有直觉感知。

## Acceptance Criteria

1. **AC-1: 5 色精通度映射**
   - **Given** 节点有精通度数据（来自 Story 5.1 BKT+FSRS 系统）
   - **When** 白板渲染节点
   - **Then** 节点颜色按精通度状态映射：
     - **未学习**：Obsidian 默认节点色（无任何交互记录的节点）
     - **学习中（蓝色系）**：有对话但未被考察（`hasInteraction && !hasExamRecord`）
     - **薄弱（红/橙色系）**：考察表现不佳（`effective_proficiency < 0.4`）
     - **掌握（绿色系）**：考察表现好（`effective_proficiency >= 0.7`）
     - **待复习（黄色系）**：FSRS 提醒该复习了（`fsrsNextReview <= now && effective_proficiency >= 0.4`）
   - **And** 中间过渡区间（0.4 <= proficiency < 0.7 且无复习提醒）显示为学习中（蓝色）
   - **And** 待复习状态优先级高于掌握/学习中（当 FSRS 提醒到期时覆盖其他状态）

2. **AC-2: 颜色即时更新**
   - **Given** 节点精通度通过 WebSocket `mastery_update` 事件更新（AutoSCORE 评分完成流）
   - **When** `mastery-state` Store 接收到精通度变更
   - **Then** NodeColorIndicator 组件在 100ms 内反映新颜色（NFR-PERF-06）
   - **And** 颜色变化使用 CSS `transition` 平滑过渡（300ms ease-in-out）
   - **And** 不需要刷新页面或重新打开白板

3. **AC-3: Light/Dark 主题适配**
   - **Given** 用户使用 Obsidian Light 或 Dark 主题
   - **When** 切换主题
   - **Then** 精通度颜色在两种主题下均清晰可辨、对比度足够
   - **And** 使用 `.theme-light` / `.theme-dark` CSS 选择器定义两套颜色值
   - **And** 颜色选择确保色觉障碍用户也能区分状态（不仅依赖色相，辅以亮度差异）

4. **AC-4: Obsidian CSS 变量集成**
   - **Given** 精通度颜色系统作为 Layer 2（Canvas Learning 扩展）CSS 变量
   - **When** 主题或自定义 CSS 变化
   - **Then** 精通度颜色通过自定义 CSS 变量 `--cl-mastery-*` 定义，用户高级场景可覆盖
   - **And** 变量基于 Obsidian 原生 CSS 变量（`--background-primary` 等）构建，保持主题一致性
   - **And** CSS 类名使用 `cl-` 前缀 + Svelte scoped CSS 隔离

5. **AC-5: NodeColorIndicator 组件渲染**
   - **Given** CanvasNode 组件渲染一个节点（Story 1.4 已实现）
   - **When** 节点有精通度状态
   - **Then** NodeColorIndicator 组件包裹或叠加在 CanvasNode 上，渲染对应颜色
   - **And** 颜色应用方式为节点边框颜色 + 左侧色条指示器（不覆盖节点内容区域背景色，保持内容可读性）
   - **And** 未学习状态的节点不显示色条指示器（与现有默认外观一致）
   - **And** 组件在视口裁剪时正确处理（视口外不渲染，与 CanvasView culling 协同）

6. **AC-6: mastery-state Store 集成**
   - **Given** `mastery-state.svelte.ts` Store 管理精通度数据
   - **When** Store 中某节点的精通度数据更新
   - **Then** 通过 Svelte 5 `$state` 响应式机制自动触发对应节点的颜色重新计算
   - **And** 颜色计算为纯函数（`getMasteryColor(nodeState) => MasteryColorClass`），可独立测试
   - **And** 无精通度数据的节点默认为"未学习"状态

## Tasks / Subtasks

- [ ] **Task 1: 精通度颜色 CSS 变量体系** (AC: #3, #4)
  - [ ] 1.1 在 `obsidian-canvas-learning/styles.css` 中追加 Layer 2 精通度颜色 CSS 变量：
    - Dark 主题（`.theme-dark`）：定义 `--cl-mastery-{unlearned,learning,weak,mastered,review}-{border,bar}` 共 10 个变量
    - Light 主题（`.theme-light`）：同名变量，使用适合浅色背景的色值
    - 未学习状态 border 映射到 `var(--background-modifier-border)`（Obsidian 原生变量）
    - 过渡动画变量 `--cl-mastery-transition: border-color 300ms ease-in-out, box-shadow 300ms ease-in-out`
  - [ ] 1.2 Dark 主题色值选择：
    - 学习中蓝色 `#5B8DEF`、薄弱红/橙 `#E06356`、掌握绿 `#4CAF50`、待复习黄 `#F5A623`
  - [ ] 1.3 Light 主题色值选择：
    - 学习中蓝色 `#3A6DD8`、薄弱红/橙 `#C4382B`、掌握绿 `#2E7D32`、待复习黄 `#D4880F`
  - [ ] 1.4 颜色选择原则：
    - Dark 主题使用较亮色值（在深色背景上突出）
    - Light 主题使用较深色值（在浅色背景上突出）
    - 蓝/红/绿/黄四色在亮度维度有差异（不仅依赖色相区分）
    - 对比度满足 WCAG AA 标准（与节点背景色对比度 >= 3:1）

- [ ] **Task 2: 精通度状态计算工具函数** (AC: #1, #6)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/utils/mastery-color.ts`：
    - 定义 `MasteryStatus` 类型：`'unlearned' | 'learning' | 'weak' | 'mastered' | 'review'`
    - 定义 `NodeMasteryData` 接口（effectiveProficiency, hasInteraction, hasExamRecord, fsrsNextReview）
    - 实现 `getMasteryStatus(data: NodeMasteryData): MasteryStatus` 纯函数
    - 实现 `getMasteryColorClass(status: MasteryStatus): string` 映射函数（返回 `cl-mastery-{status}`）
  - [ ] 2.2 `getMasteryStatus` 判定逻辑（优先级排序）：
    - 无交互 + 无考察 → `unlearned`
    - FSRS 复习到期 → `review`（覆盖其他状态）
    - 有交互但无考察 → `learning`
    - 考察 proficiency < 0.4 → `weak`
    - 考察 proficiency >= 0.7 → `mastered`
    - 考察 0.4 <= proficiency < 0.7 → `learning`（过渡区间）
    - proficiency 为 null 且有考察 → `weak`
  - [ ] 2.3 为 `getMasteryStatus` 编写单元测试 `obsidian-canvas-learning/src/__tests__/mastery-color.test.ts`：
    - 未交互节点 → `unlearned`
    - 有对话无考察 → `learning`
    - 考察 proficiency=0.2 → `weak`
    - 考察 proficiency=0.5 → `learning`（过渡区间）
    - 考察 proficiency=0.8 → `mastered`
    - 掌握但 FSRS 到期 → `review`（优先级覆盖）
    - proficiency=null 且有考察 → `weak`
    - FSRS 未到期的掌握节点 → `mastered`

- [ ] **Task 3: mastery-state.svelte.ts Store** (AC: #2, #6)
  - [ ] 3.1 创建 `obsidian-canvas-learning/src/stores/mastery-state.svelte.ts`：
    - 定义 `MasteryState` class 使用 Svelte 5 `$state` rune
    - 核心状态：`nodeMasteryMap = $state<Map<string, NodeMasteryData>>(new Map())`
    - `updateNodeMastery(nodeId, data)` 方法：合并更新单节点精通度，创建新 Map 触发响应式
    - `loadBoardMastery(entries)` 方法：批量加载白板精通度（白板打开时调用）
    - `getNodeStatus(nodeId)` 方法：返回 MasteryStatus（供 NodeColorIndicator 消费）
    - `markInteraction(nodeId)` 方法：标记节点有交互（对话开始时调用）
    - 导出 singleton `export const masteryState = new MasteryState()`
  - [ ] 3.2 Store 仅管理前端精通度状态缓存，权威数据在后端 Neo4j（Layer 0 后端算法权威原则）
  - [ ] 3.3 数据流向：后端 EventBus `BKT_UPDATED` → WebSocket `mastery_update` → `masteryState.updateNodeMastery()` → Svelte 响应式 → NodeColorIndicator 重渲染

- [ ] **Task 4: NodeColorIndicator Svelte 组件** (AC: #1, #2, #3, #5)
  - [ ] 4.1 创建 `obsidian-canvas-learning/src/components/canvas/NodeColorIndicator.svelte`：
    - Props：`nodeId: string`
    - 使用 `$derived` 从 masteryState 派生 masteryStatus 和 colorClass
    - 渲染左侧 4px 宽色条指示器（`position: absolute; left: 0; top: 0; bottom: 0`）
    - 未学习状态不渲染指示器（条件渲染 `{#if showIndicator}`）
  - [ ] 4.2 Scoped CSS 样式：
    - `.cl-mastery-indicator` 基础样式：绝对定位、4px 宽、圆角左上下角、transition 过渡
    - `.cl-mastery-learning` 背景色 `var(--cl-mastery-learning-bar)`
    - `.cl-mastery-weak` 背景色 `var(--cl-mastery-weak-bar)`
    - `.cl-mastery-mastered` 背景色 `var(--cl-mastery-mastered-bar)`
    - `.cl-mastery-review` 背景色 `var(--cl-mastery-review-bar)`
    - `pointer-events: none` 确保不影响节点交互
    - `z-index: 1` 确保色条在节点内容之上

- [ ] **Task 5: 集成 NodeColorIndicator 到 CanvasNode** (AC: #5)
  - [ ] 5.1 修改 `obsidian-canvas-learning/src/components/canvas/CanvasNode.svelte`（Story 1.4 已创建）：
    - 导入 NodeColorIndicator 组件和 masteryState/getMasteryColorClass
    - 在节点容器内添加 `<NodeColorIndicator nodeId={node.id} />`
    - 使用 `$derived` 计算 masteryBorderClass 并绑定到节点容器 class
  - [ ] 5.2 在 CanvasNode scoped CSS 中添加精通度边框样式：
    - `.cl-canvas-node.cl-mastery-learning-border` → `border-color: var(--cl-mastery-learning-border)`
    - `.cl-canvas-node.cl-mastery-weak-border` → `border-color: var(--cl-mastery-weak-border)`
    - `.cl-canvas-node.cl-mastery-mastered-border` → `border-color: var(--cl-mastery-mastered-border)`
    - `.cl-canvas-node.cl-mastery-review-border` → `border-color: var(--cl-mastery-review-border)`
  - [ ] 5.3 确保 CanvasNode 容器有 `position: relative`（NodeColorIndicator absolute 定位依赖）
  - [ ] 5.4 确保视口裁剪正常：NodeColorIndicator 在 CanvasNode 内部，随节点一起被 culling

- [ ] **Task 6: WebSocket 精通度更新接收** (AC: #2)
  - [ ] 6.1 在 `obsidian-canvas-learning/src/services/api-client.ts`（Story 1.1 已创建）中追加 WebSocket `mastery_update` 消息处理：
    - 解析 `mastery_update` 类型消息的 payload
    - 执行 snake_case → camelCase 字段转换（API service 层规范）
    - 调用 `masteryState.updateNodeMastery(nodeId, convertedData)`
  - [ ] 6.2 WebSocket 断连时精通度数据保留缓存（不清空），重连后批量同步

- [ ] **Task 7: 白板打开时批量加载精通度** (AC: #1, #6)
  - [ ] 7.1 在 `canvas-state.svelte.ts` 的 `switchBoard()` 方法中追加精通度加载：
    - 调用 `apiClient.getBoardMastery(boardId)` 获取该白板所有节点精通度
    - 调用 `masteryState.loadBoardMastery(data)` 批量写入 Store
    - 加载失败时 console.warn 但不阻塞白板打开（降级：所有节点默认色）
  - [ ] 7.2 在 `api-client.ts` 中追加 `getBoardMastery(boardId)` 方法：
    - `GET /api/v1/mastery/board/{boardId}` → 返回该白板所有节点的精通度数据
    - 后端不可达时返回空数组（降级策略：NFR-REL-02）

## Dev Notes

### 依赖关系

- **Story 5.1（BKT+FSRS 系统）**：提供精通度数据（`effective_proficiency`, FSRS 复习时间）。5.2 的颜色映射消费 5.1 的数据。但 5.2 实现时可以先用开发测试数据验证前端组件，5.1 完成后接入真实数据。
- **Story 1.4（白板节点渲染）**：提供 CanvasNode 组件。5.2 在 CanvasNode 中集成 NodeColorIndicator。1.4 必须先完成。
- **WebSocket 通道**：精通度实时更新依赖 WebSocket 连接。本 Story 追加消息处理逻辑，WebSocket 基础设施由后端提供。

### 精通度状态判定逻辑

```
                            +--------------+
                            | 有交互记录？  |
                            +------+-------+
                                   |
                          No ------+------ Yes
                                   |         |
                         +---------v--+  +---v----------+
                         |  未学习     |  | FSRS到期？    |
                         | (默认色)    |  +---+-----------+
                         +------------+      |
                                    Yes -----+---- No
                                             |       |
                                   +---------v--+  +-v------------+
                                   |  待复习     |  | 有考察记录？  |
                                   | (黄色)      |  +-+-------------+
                                   +------------+    |
                                            No ------+---- Yes
                                                     |       |
                                           +---------v--+  +-v--------------+
                                           |  学习中     |  | proficiency    |
                                           | (蓝色)      |  | 分档判定       |
                                           +------------+  +-+--------------+
                                                             |
                                              +--------------+--------------+
                                              |              |              |
                                         p < 0.4      0.4<=p<0.7      p >= 0.7
                                              |              |              |
                                        +-----v----+  +-----v----+  +-----v----+
                                        |  薄弱     |  |  学习中   |  |  掌握     |
                                        | (红/橙)   |  | (蓝色)    |  | (绿色)    |
                                        +----------+  +----------+  +----------+
```

### 颜色呈现方式

采用**边框颜色 + 左侧色条指示器**双重方式，原因：
1. **不改变节点背景色**：保持内容可读性（用户编辑的文字在默认背景上显示）
2. **左侧色条**：4px 宽的垂直色条，提供快速视觉扫描锚点（参考 VS Code 编辑器装订线指示器模式）
3. **边框颜色**：整个节点边框微妙变色，选中态与精通度色叠加显示
4. **未学习节点不添加任何视觉标记**：与默认外观完全一致，避免噪音

### 数据流完整链路

```
AutoSCORE 评分完成
  -> EventBus: SCORE_SUBMITTED -> mastery_engine: BKT+FSRS 更新
  -> EventBus: BKT_UPDATED -> Neo4j: 更新 pMastery
  -> WebSocket: mastery_update 推送到前端
  -> api-client.ts: handleWebSocketMessage()
  -> masteryState.updateNodeMastery(nodeId, data)
  -> Svelte $state 响应式触发
  -> NodeColorIndicator $derived 重新计算
  -> DOM 更新：色条 + 边框颜色变化（CSS transition 300ms）
```

### 精通度数值规范

- 内部存储/传输：`0.0 ~ 1.0` float
- `effective_proficiency = min(p_mastery, R)`（BKT 掌握概率和 FSRS 记忆保留率取较小值）
- 用户展示：不直接展示数字，用颜色传达（处方性 OLM 原则）
- 阈值 0.4 / 0.7 为 MVP 初始值，后续可通过配置调整

### CSS 隔离策略

- 所有 CSS 类名使用 `cl-mastery-` 前缀
- NodeColorIndicator 使用 Svelte scoped CSS
- 精通度颜色 CSS 变量在 `styles.css` 全局定义（供所有组件使用）
- `.theme-light` / `.theme-dark` 覆盖确保主题适配
- 不使用硬编码颜色值，全部走 CSS 变量

### 命名规范速查（本 Story 涉及）

- Svelte 组件文件：`PascalCase.svelte`（`NodeColorIndicator.svelte`）
- Store 文件：`kebab-case.svelte.ts`（`mastery-state.svelte.ts`）
- 工具函数文件：`kebab-case.ts`（`mastery-color.ts`）
- CSS 类名：`cl-mastery-*`（精通度颜色系统）
- TypeScript 变量/函数：`camelCase`（`effectiveProficiency`, `getMasteryStatus()`）
- CSS 变量：`--cl-mastery-*`（Layer 2 扩展变量）

### 不做的事项（防蔓延 DD-10）

- 不实现后端 BKT/FSRS 算法（Story 5.1）
- 不实现后端 WebSocket 基础设施（后端 Story 提供）
- 不实现后端 `/api/v1/mastery/board/{boardId}` 端点（后端 Story 提供）
- 不实现学习档案面板中的精通度详情展示（Story 5.3）
- 不实现 FSRS 复习提醒列表（Story 5.4）
- 不实现 OLM 三层面板（Phase 2 延后）
- 不实现颜色的用户自定义设置 UI（高级功能，通过 CSS 变量覆盖即可）
- 不实现精通度动画效果（如脉冲、闪烁）——仅 CSS transition 过渡
- 不实现 Calibration 校准相关颜色变化（Story 5.5）
- 不实现 EventBus 或 CircuitBreaker（Story 5.7）

### 共享文件编辑规则

| 文件 | 规则 |
|------|------|
| `styles.css` | 仅追加 `--cl-mastery-*` CSS 变量定义，不修改已有变量 |
| `CanvasNode.svelte` | 追加 NodeColorIndicator 导入和渲染 + 边框样式类。不修改已有拖拽/编辑/选中逻辑 |
| `api-client.ts` | 追加 WebSocket `mastery_update` 消息处理 + `getBoardMastery()` 方法。不修改已有 REST 方法 |
| `canvas-state.svelte.ts` | 在 `switchBoard()` 中追加精通度加载调用。不修改已有 CRUD 方法 |

### 降级策略

| 场景 | 降级行为 |
|------|---------|
| 后端不可达 | 所有节点显示为"未学习"（默认色），白板正常使用 |
| WebSocket 断连 | 精通度缓存保留，不实时更新，重连后批量同步 |
| 精通度 API 返回错误 | 不阻塞白板打开，console.warn 记录，节点默认色 |
| BKT/FSRS 尚未部署（5.1 未完成） | getMasteryStatus 均返回 unlearned，无色条无边框色变化 |

### Project Structure Notes

本 Story 新增/修改的文件清单：

```
obsidian-canvas-learning/
+-- styles.css                                    # [修改] 追加 --cl-mastery-* CSS 变量
+-- src/
    +-- components/
    |   +-- canvas/
    |       +-- CanvasNode.svelte                 # [修改] 集成 NodeColorIndicator + 边框样式
    |       +-- NodeColorIndicator.svelte          # [新建] 精通度色条指示器组件
    +-- stores/
    |   +-- mastery-state.svelte.ts               # [新建] 精通度状态 Store
    +-- services/
    |   +-- api-client.ts                         # [修改] 追加 mastery_update 处理 + getBoardMastery()
    +-- utils/
    |   +-- mastery-color.ts                      # [新建] 精通度状态计算纯函数
    +-- __tests__/
        +-- mastery-color.test.ts                 # [新建] 精通度计算单元测试
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.2] -- Story 需求和 AC（节点颜色映射 5 色 + NodeColorIndicator + Light/Dark 适配）
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] -- 精通度追踪能力域：三通道传达（节点颜色+学习档案面板+FSRS Dashboard）、effective_proficiency=min(p_mastery,R)、精通度仅通过考察更新
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Flow] -- 评分完成流：EventBus SCORE_SUBMITTED -> mastery_engine -> BKT_UPDATED -> WebSocket mastery_update -> mastery-state -> 节点颜色变化
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns] -- 命名规范（CSS cl- 前缀、Store kebab-case.svelte.ts、组件 PascalCase.svelte）
- [Source: _bmad-output/planning-artifacts/architecture.md#Format Patterns] -- 精通度数值 0.0~1.0 float、不直接展示数字用颜色/文字描述、WebSocket 消息格式
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure] -- 前端目录结构（components/canvas/ E 组、stores/mastery-state.svelte.ts）
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Customization Strategy] -- 精通度颜色系统 5 状态定义（未学习/学习中/薄弱/掌握/待复习）
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Design System Foundation] -- Layer 2 Canvas Learning 扩展 CSS 变量用于精通度颜色映射
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] -- E 组白板组件包含 NodeColorIndicator，Phase 2 组件路线图
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Color System] -- 基础色使用 Obsidian CSS 变量，精通度色映射到节点颜色
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Accessibility] -- Light/Dark 自动适配（.theme-light / .theme-dark）
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns] -- Obsidian 主题兼容三层 CSS（Obsidian 变量/自定义 cl-变量/Svelte scoped）
- [Source: _bmad-output/planning-artifacts/prd.md#FR-MAST-03] -- 精通度通过三种方式传达：(1) 白板上节点颜色 (2) 学习档案面板 (3) FSRS 复习提醒

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
