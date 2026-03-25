# 前端组件清单

> 生成时间: 2026-03-24 | 扫描模式: exhaustive
>
> 框架: Tauri 2 + React 19 + TypeScript 5 + ReactFlow + Zustand + Dexie
> 样式: TailwindCSS v4 + Catppuccin Mocha 主题

## 1. 组件清单 (30 个)

### Layout 组件 (5 个)

| 组件 | 文件 | Props | 用途 | 依赖 Store |
|------|------|-------|------|-----------|
| `App` | `App.tsx` | - | 应用入口: ReactFlow 画布 + 面板布局 | canvas, chat, exam, mastery |
| `StatusBar` | `components/StatusBar.tsx` | - | 底部状态栏: 后端状态 + 同步状态 | - |
| `Settings` | `components/Settings.tsx` | - | 全局设置面板 (AI 配置, 服务状态, Docker 管理) | canvas, chat |
| `SyncIndicator` | `components/SyncIndicator.tsx` | - | 同步状态指示器 (pending/syncing/synced) | - |
| `NodeContextMenu` | `components/NodeContextMenu.tsx` | nodeId, position, onClose | 节点右键菜单: 颜色/考试/档案/索引 | canvas, mastery |

### Canvas/Nodes 组件 (3 个)

| 组件 | 文件 | Props | 用途 | 依赖 Store |
|------|------|-------|------|-----------|
| `KnowledgeNode` | `components/nodes/KnowledgeNode.tsx` | data: KnowledgeNodeData | 知识节点: 标题+内容+掌握度色环+索引状态 | mastery |
| `ImageNode` | `components/nodes/ImageNode.tsx` | data: KnowledgeNodeData | 图片节点: 图片预览+OCR 文本 | - |
| `nodeTypes` | `components/nodes/nodeTypes.ts` | - | ReactFlow 节点类型注册表 | - |

### Chat 组件 (13 个)

| 组件 | 文件 | Props | 用途 | 依赖 Store |
|------|------|-------|------|-----------|
| `ChatPanel` | `components/ChatPanel.tsx` | - | 主聊天面板: 消息列表+输入栏+工具调用 | chat, canvas |
| `InputBar` | `components/chat/InputBar.tsx` | onSend, disabled | 消息输入栏 + /命令触发 | chat |
| `MessageBubble` | `components/chat/MessageBubble.tsx` | message, isUser | 消息气泡 (Markdown 渲染) | - |
| `ToolCallCard` | `components/chat/ToolCallCard.tsx` | toolCall | 工具调用展示卡片 | - |
| `ObserverBadge` | `components/chat/ObserverBadge.tsx` | events | Observer 学习行为标记 (misconception/tip) | chat |
| `SkillSelector` | `components/chat/SkillSelector.tsx` | onSelect, filter | /命令技能选择下拉菜单 | - |
| `StreamingIndicator` | `components/chat/StreamingIndicator.tsx` | - | 流式响应加载指示器 | chat |
| `InlineAnnotation` | `components/chat/InlineAnnotation.tsx` | text, nodeId | 内联标注 (选中文本保存为 Tip) | - |
| `EdgeGuideTooltip` | `components/chat/EdgeGuideTooltip.tsx` | edge | 边引导提示 (新建边时的对话建议) | - |
| `EngineStatusIndicator` | `components/chat/EngineStatusIndicator.tsx` | status | 引擎状态指示器 (API Key/Sidecar) | chat |
| `QuotaExhaustedBanner` | `components/chat/QuotaExhaustedBanner.tsx` | - | API 配额耗尽横幅 | chat |
| `RecoveryBanner` | `components/chat/RecoveryBanner.tsx` | - | 崩溃恢复横幅 | chat |
| `SelectionToolbar` | `components/chat/SelectionToolbar.tsx` | selectedText | 选中文本工具栏 (复制/保存Tip) | - |
| `TipsList` | `components/chat/TipsList.tsx` | tips | Tips 列表展示 | - |

### Exam 组件 (6 个)

| 组件 | 文件 | Props | 用途 | 依赖 Store |
|------|------|-------|------|-----------|
| `ExamCanvas` | `components/exam/ExamCanvas.tsx` | - | 考试画布: 题目展示+作答区 | exam |
| `ExamModeSelector` | `components/exam/ExamModeSelector.tsx` | onSelect | 考试模式选择 (全量/薄弱/随机) | - |
| `ExamSummary` | `components/exam/ExamSummary.tsx` | results | 考试结果摘要 | exam |
| `CognitiveLoadTimer` | `components/exam/CognitiveLoadTimer.tsx` | startTime | 认知负荷计时器 | - |
| `HintButton` | `components/exam/HintButton.tsx` | examId, questionId | 提示按钮 (Chain-of-Hints L1-L4) | exam |
| `SkipButton` | `components/exam/SkipButton.tsx` | examId, questionId | 跳过按钮 | exam |

### Dashboard 组件 (2 个)

| 组件 | 文件 | Props | 用途 | 依赖 Store |
|------|------|-------|------|-----------|
| `ReviewItem` | `components/dashboard/ReviewItem.tsx` | schedule | 复习项卡片 (下次复习时间+掌握度) | mastery |
| `ExamCard` | `components/dashboard/ExamCard.tsx` | exam | 考试卡片 (状态+分数+时间) | - |

### Profile 组件 (1 个)

| 组件 | 文件 | Props | 用途 | 依赖 Store |
|------|------|-------|------|-----------|
| `LearningProfile` | `components/profile/LearningProfile.tsx` | nodeId | 学习档案面板: 摘要+Tips+薄弱点+QA精华 | mastery |

### Markdown 组件 (1 个)

| 组件 | 文件 | Props | 用途 | 依赖 Store |
|------|------|-------|------|-----------|
| `markdown-renderers` | `components/markdown/markdown-renderers.tsx` | - | 自定义 Markdown 渲染器 (代码块/LaTeX/链接) | - |

---

## 2. Zustand Stores (4 个)

### canvas-store (9,593 行)

> 文件: `frontend/src/stores/canvas-store.ts`

| 状态字段 | 类型 | 说明 |
|----------|------|------|
| `boards` | CanvasBoard[] | 画布列表 |
| `currentBoardId` | string \| null | 当前选中画布 ID |
| `view` | 'canvas' \| 'settings' \| 'exam' \| ... | 当前视图路由 |
| `contextMenu` | ContextMenuState \| null | 右键菜单状态 |

| Action | 说明 |
|--------|------|
| `loadBoards()` | 从 Dexie 加载画布列表 |
| `createBoard(name)` | 创建新画布 |
| `addNode(canvasId, data)` | 添加节点 (写 Dexie + sync_outbox) |
| `updateNode(id, data)` | 更新节点 |
| `deleteNode(id)` | 删除节点 |
| `addEdge(canvasId, data)` | 添加边 |
| `deleteEdge(id)` | 删除边 |
| `setView(view)` | 切换视图 |

### chat-store (47,247 行)

> 文件: `frontend/src/stores/chat-store.ts`

| 状态字段 | 类型 | 说明 |
|----------|------|------|
| `messages` | Map<string, Message[]> | 按节点 ID 分组的消息 |
| `isStreaming` | boolean | 是否正在流式响应 |
| `engineType` | 'sidecar' \| 'api-key' \| null | 当前 AI 引擎类型 |
| `engineStatus` | 'disconnected' \| 'connecting' \| 'ready' \| 'error' | 引擎连接状态 |
| `selectedSkill` | string \| null | 当前选中的 /命令 |
| `edgeContext` | EdgeContext \| null | 边上下文 (用于边引导对话) |
| `observerEvents` | ObserverEvent[] | Observer 检测到的学习行为 |

| Action | 说明 |
|--------|------|
| `sendMessage(nodeId, content)` | 发送消息到 AI |
| `initEngine()` | 初始化 AI 引擎 (Sidecar 或 API Key) |
| `setSkill(skill)` | 设置 /命令 |
| `clearMessages(nodeId)` | 清除节点消息 |
| `saveMessage(msg)` | 保存消息到 Dexie |

### exam-store (7,043 行)

> 文件: `frontend/src/stores/exam-store.ts`

| 状态字段 | 类型 | 说明 |
|----------|------|------|
| `currentExam` | ExamSession \| null | 当前考试会话 |
| `questions` | Question[] | 题目队列 |
| `currentQuestionIndex` | number | 当前题号 |
| `results` | ExamResult[] | 评分结果 |
| `mode` | 'idle' \| 'selecting' \| 'examining' \| 'summary' | 考试阶段 |

| Action | 说明 |
|--------|------|
| `startExam(canvasId, mode)` | 开始考试 |
| `submitAnswer(answer)` | 提交答案 |
| `requestHint()` | 请求提示 |
| `skipQuestion()` | 跳过题目 |
| `completeExam()` | 完成考试 |

### mastery-store (5,726 行)

> 文件: `frontend/src/stores/mastery-store.ts`

| 状态字段 | 类型 | 说明 |
|----------|------|------|
| `masteryMap` | Map<string, MasteryState> | 节点 ID -> 掌握度映射 |
| `loading` | boolean | 是否正在加载 |
| `lastFetchedBoardId` | string \| null | 上次获取的画布 ID |

| Action | 说明 |
|--------|------|
| `fetchBoardMastery(boardId)` | 获取画布所有节点掌握度 |
| `fetchBatchMastery(groupId)` | 批量获取掌握度 |
| `getMastery(nodeId)` | 获取单节点掌握度 |

---

## 3. Services (12 个)

> 位置: `frontend/src/services/`

| Service | 文件 | 行数 | 说明 |
|---------|------|------|------|
| `api-client` | `api-client.ts` | 35,111 | 后端 REST API 客户端 (所有 HTTP 请求封装) |
| `claude-engine` | `claude-engine.ts` | 30,022 | Claude Agent SDK 引擎 (Sidecar 模式对话) |
| `api-key-engine` | `api-key-engine.ts` | 15,385 | API Key 直连引擎 (Gemini/OpenAI/Anthropic) |
| `dexie-db` | `dexie-db.ts` | 8,446 | Dexie (IndexedDB) 数据库定义 + 表结构 |
| `sync-engine` | `sync-engine.ts` | 9,115 | Outbox 同步引擎: Dexie -> Backend 批量同步 |
| `backup-manager` | `backup-manager.ts` | 12,764 | 本地备份管理器 |
| `crash-recovery` | `crash-recovery.ts` | 12,641 | 崩溃恢复服务 |
| `docker-manager` | `docker-manager.ts` | 10,351 | Docker 容器管理 (通过 Tauri Shell) |
| `engine-fallback` | `engine-fallback.ts` | 7,540 | AI 引擎降级策略 (Sidecar -> API Key) |
| `indexing-service` | `indexing-service.ts` | 4,048 | 节点索引服务 (触发后端 LanceDB 索引) |
| `mastery-utils` | `mastery-utils.ts` | 4,334 | 掌握度工具函数 (颜色映射/等级转换) |
| `obsidian-link` | `obsidian-link.ts` | 7,936 | Obsidian 链接桥接 (打开 Vault 笔记) |

---

## 4. Hooks (3 个)

> 位置: `frontend/src/hooks/`

| Hook | 文件 | 行数 | 说明 |
|------|------|------|------|
| `useBackendStatus` | `useBackendStatus.ts` | 1,319 | 后端健康状态轮询 (5s 间隔) |
| `useBoardData` | `useBoardData.ts` | 1,638 | 画布数据加载 (Dexie useLiveQuery) |
| `usePullToNode` | `usePullToNode.ts` | 3,064 | 拉拽到节点交互 (边创建引导) |

---

## 5. Sidecar (Agent SDK)

> 文件: `frontend/sidecar/sidecar.js` (468 行)
> 运行时: Node.js (通过 Tauri Shell 启动子进程)

**功能**：作为 Claude Agent SDK 的 JSON-RPC 桥接，连接前端 UI 和后端 MCP 工具。

**通信流程**：
```
React UI -> Tauri Shell -> sidecar.js (Agent SDK) -> Backend /mcp (JSON-RPC)
                                                  -> Backend REST API
```

**核心能力**：
- 初始化 Claude Agent SDK 客户端
- 维护对话上下文
- 调用后端 MCP 工具 (15 个)
- 流式传输 Agent 响应到前端

---

## 6. 设计系统

| 项目 | 说明 |
|------|------|
| CSS 框架 | TailwindCSS v4 (原子化 CSS) |
| 主题 | Catppuccin Mocha (暗色主题) |
| 画布引擎 | @xyflow/react (ReactFlow) v12 |
| Markdown | react-markdown + rehype-katex + remark-math (LaTeX 公式支持) |
| 图标 | 无外部图标库 (使用 Unicode/SVG) |
| 字体 | 系统默认字体栈 |
