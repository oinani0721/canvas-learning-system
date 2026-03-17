# Story 4.2: Edge 对话——Agent 追问与理由记录

Status: ready-for-dev

## Story

As a 用户,
I want Agent 问我"为什么把这两个概念连在一起"，我回答后理由被结构化记录,
so that 系统记住我对概念关系的理解，将来能在对话和考察中引用。

## Acceptance Criteria

1. **AC-1: Agent 主动追问连线理由**
   - **Given** 用户点击 Edge 图标进入 Edge 对话（ChatPanel mode='edge'）
   - **When** 对话 session 初始化完成
   - **Then** Agent 基于预设 prompt 主动发起第一条消息，询问用户为何连接这两个概念
   - **And** Agent 消息引用两端节点名称和内容摘要（如"你把'贝叶斯定理'和'朴素贝叶斯'连在一起，能告诉我它们的关系吗？"）
   - **And** Agent 追问风格为自然对话，不像做练习（体感为"聊天"而非"作业"）
   - **And** Agent 可进行多轮追问（深入理由、澄清理解），不限于一问一答

2. **AC-2: 理由结构化为 KG-triplet Edge 语义标签**
   - **Given** 用户回答连线理由后
   - **When** Agent 判定用户已充分解释
   - **Then** Agent 通过 MCP 工具调用后端，将理由提取为结构化 KG-triplet 格式：
     - `(source_concept, relation_type, target_concept)`
     - 附带 `rationale_text`（用户原始解释）和 `confidence`（Agent 对理解完整度的评估）
   - **And** KG-triplet 的 relation_type 由 Agent 从用户解释中提取（如"是前提条件"、"是特殊情况"、"相互对比"等）
   - **And** 结构化标签存储在 Edge 的 label 属性中，白板上可见

3. **AC-3: 理由双写——Graphiti 结构化 + LanceDB 向量化**
   - **Given** Agent 提取出 KG-triplet 理由
   - **When** 执行双写
   - **Then** **Graphiti 写入**：通过 graphiti_core 的 Agent 自报告通道写入，entity_type 为自定义 Pydantic Schema（包含 source_concept、target_concept、relation_type、rationale_text、confidence、timestamp）
   - **And** **LanceDB 写入**：rationale_text 通过 bge-m3 向量化后写入 LanceDB（供检索管道和出题 ACP 数据包消费）
   - **And** 双写使用事务语义：任一失败不影响对话体验，写入失败后放入 Outbox 队列重试
   - **And** 双写结果不阻塞对话（异步后台执行）

4. **AC-4: 理由作为下游数据消费**
   - **Given** Edge 理由已双写存储
   - **When** 以下场景触发
   - **Then** 出题时：ACP 数据包第 3 层注入 Edge 理由（供 Agent 精准出题）
   - **And** 节点对话时：上下文注入 Tier2 层包含相邻 Edge 理由摘要
   - **And** 检索时：LanceDB 向量检索可匹配到 Edge 理由内容

5. **AC-5: Edge 理由更新与版本**
   - **Given** 用户再次点击已有理由的 Edge 进入对话
   - **When** 用户修改或补充理由
   - **Then** Agent 更新 KG-triplet（覆盖旧 relation_type 或追加新维度）
   - **And** Graphiti 时序感知：保留历史理由版本（可追溯理解演变）
   - **And** LanceDB 重新向量化更新后的 rationale_text（delete-before-insert 去重）
   - **And** 白板上 Edge 标签更新为最新 relation_type

6. **AC-6: MCP 工具——record_edge_rationale**
   - **Given** 后端 FastAPI 运行，MCP 工具注册
   - **When** Agent 调用 `record_edge_rationale` MCP 工具
   - **Then** 工具接收参数：edge_id, source_node_id, target_node_id, relation_type, rationale_text, confidence
   - **And** 工具执行 Graphiti + LanceDB 双写
   - **And** 工具返回写入结果（success/failure + 存储的 record_id）
   - **And** 工具纳入密码学令牌管道（非跳步调用）

## Tasks / Subtasks

- [ ] **Task 1: Edge 对话预设 Prompt 模板** (AC: #1)
  - [ ] 1.1 创建 `backend/prompts/edge-dialog.md`，包含 Edge 对话系统提示：
    - 角色定义：学习助手，帮用户梳理概念关系
    - 上下文模板：注入两端节点信息
    - 追问策略：先开放式提问 → 根据回答深入追问 → 确认理解
    - 语气要求：自然对话风格，非练习/考试语气
  - [ ] 1.2 创建 `backend/prompts/edge-triplet-extraction.md`，包含 KG-triplet 提取指令：
    - 从用户解释中提取 relation_type
    - 输出格式为结构化 JSON
    - confidence 评估规则

- [ ] **Task 2: MCP 工具 record_edge_rationale** (AC: #6)
  - [ ] 2.1 在 `backend/app/api/v1/endpoints/` 中创建或扩展 edge 相关端点
  - [ ] 2.2 实现 `record_edge_rationale` 接口：接收 edge_id, source_node_id, target_node_id, relation_type, rationale_text, confidence
  - [ ] 2.3 注册为 FastAPI-MCP 工具，配置参数 schema
  - [ ] 2.4 纳入密码学令牌管道

- [ ] **Task 3: Graphiti 写入——Edge 理由结构化存储** (AC: #3)
  - [ ] 3.1 定义 Pydantic Schema：EdgeRationale（source_concept, target_concept, relation_type, rationale_text, confidence, timestamp, edge_id）
  - [ ] 3.2 在 `backend/app/services/graphiti/memory_service.py` 中实现 Edge 理由写入方法
  - [ ] 3.3 使用 Graphiti Agent 自报告通道写入
  - [ ] 3.4 实现时序版本管理：新理由不覆盖旧记录，保留历史

- [ ] **Task 4: LanceDB 写入——Edge 理由向量化** (AC: #3)
  - [ ] 4.1 在 LanceDB 中创建 edge_rationales 表（或复用 chunks 表添加 source_type='edge_rationale' 字段）
  - [ ] 4.2 rationale_text 通过 bge-m3 向量化（1024d Dense）
  - [ ] 4.3 元数据包含 edge_id, source_node_id, target_node_id, relation_type
  - [ ] 4.4 更新时使用 delete-before-insert 模式去重

- [ ] **Task 5: 双写事务与异步执行** (AC: #3)
  - [ ] 5.1 record_edge_rationale 端点内实现 Graphiti + LanceDB 双写
  - [ ] 5.2 双写异步执行（asyncio.gather），不阻塞 Agent 对话
  - [ ] 5.3 任一写入失败时放入 Outbox 队列（复用 SyncEngine Outbox 模式）
  - [ ] 5.4 Outbox 重试策略：指数退避，最多 3 次

- [ ] **Task 6: Agent 上下文组装（Edge 模式）** (AC: #1, #4)
  - [ ] 6.1 在 `src/services/agent-bridge.ts` 扩展 Edge 模式的 system prompt 组装：
    - 注入 edge-dialog.md 预设 prompt
    - 注入两端节点上下文（名称、内容摘要、Tips、错误）
    - 注入已有 Edge 理由（如有）
  - [ ] 6.2 Edge 对话 session 的 MCP 工具列表包含 record_edge_rationale

- [ ] **Task 7: Edge 标签 UI 更新** (AC: #2, #5)
  - [ ] 7.1 record_edge_rationale 成功后，通过 WebSocket 推送 Edge 标签更新事件
  - [ ] 7.2 CanvasEdge 组件接收更新，渲染 relation_type 为 Edge 标签文字
  - [ ] 7.3 IndexedDB 同步更新 Edge label 属性

- [ ] **Task 8: 下游消费验证** (AC: #4)
  - [ ] 8.1 验证 ACP 数据包组装时能从 Graphiti 查询到 Edge 理由
  - [ ] 8.2 验证节点对话上下文注入时 Tier2 包含相邻 Edge 理由
  - [ ] 8.3 验证 LanceDB 检索能匹配 Edge 理由内容

- [ ] **Task 9: 测试** (AC: #1-#6)
  - [ ] 9.1 创建 `backend/tests/unit/test_edge_rationale.py`：
    - record_edge_rationale 端点：正常写入/参数缺失/双写部分失败
    - KG-triplet 格式验证
    - Graphiti 写入 mock 验证
    - LanceDB 写入 mock 验证
  - [ ] 9.2 创建 `__tests__/integration/edge-dialog-flow.test.ts`：
    - Edge 对话完整流程：触发→Agent追问→用户回答→理由记录→标签更新
  - [ ] 9.3 编辑后运行 `ruff check` + `ruff format --check` 确认 lint 通过

## Dev Notes

### Edge 理由双写架构

Edge 对话的核心数据流（[Source: architecture.md#能力域3]）：

```
用户回答理由 → Agent 提取 KG-triplet
  → MCP: record_edge_rationale(edge_id, relation_type, rationale_text, confidence)
  → 后端双写:
    ├→ Graphiti: 结构化 KG-triplet（时序版本，可追溯）
    └→ LanceDB: rationale_text 向量化（检索消费）
  → WebSocket 推送 Edge 标签更新
  → 白板 UI 显示 relation_type
```

### 下游消费路径

Edge 理由双写后的消费场景（[Source: architecture.md#能力域3]）：

| 消费场景 | 数据源 | 用途 |
|---------|--------|------|
| 出题 ACP 数据包 | Graphiti | Prompt 第 3 层注入 Edge 理由，精准出题 |
| 节点对话上下文 | Graphiti | Tier2 相邻节点摘要包含 Edge 理由 |
| 语义检索 | LanceDB | 检索管道可匹配 Edge 理由内容 |

### Graphiti 三通道写入

本 Story 使用 **Agent 自报告通道**（[Source: architecture.md#能力域6]）：Agent 直接通过 MCP 工具调用后端写入 Graphiti。其他两个通道（对话蒸馏、考察提取）不在本 Story 范围。

### 密码学令牌管道

record_edge_rationale MCP 工具纳入密码学令牌管道（[Source: architecture.md#能力域11]）：每步产 token，跳步拒绝。Edge 对话不涉及评分/精通度更新，令牌链较短。

### Brownfield 注意

- `backend/app/services/graphiti/memory_service.py` 可能已有部分实现（需 Code-Review 确认是否为 mock）
- LanceDB 表结构需与已有 indexing 管道兼容（向量维度统一 1024d）

### Project Structure Notes

- `backend/prompts/edge-dialog.md` — 新建，Edge 对话预设 prompt
- `backend/prompts/edge-triplet-extraction.md` — 新建，KG-triplet 提取指令
- `backend/app/api/v1/endpoints/edges.py` — 新建或扩展
- `backend/app/services/graphiti/memory_service.py` — 修改（Edge 理由写入）
- `src/services/agent-bridge.ts` — 修改（Edge 上下文组装）
- `src/components/canvas/CanvasEdge.svelte` — 修改（标签渲染更新）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story4.2] — AC 原文
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域3] — Edge 对话架构：EdgeDialogTrigger + ChatPanel Edge 模式 + 理由双写
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域6] — Graphiti 三通道写入 + 自定义 Pydantic Schema
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域11] — MCP 工具暴露 + 密码学令牌管道
- [Source: _bmad-output/planning-artifacts/architecture.md#前端组件目录] — EdgeDialog.svelte 必须与 ChatPanel Edge 模式同 Story
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#核心交互2] — Edge 连线四步流程
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Effortless Interactions] — Edge 连线体感为"自然对话"非"做练习"

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/prompts/edge-dialog.md` — 新建
- `backend/prompts/edge-triplet-extraction.md` — 新建
- `backend/app/api/v1/endpoints/edges.py` — 新建或扩展
- `backend/app/services/graphiti/memory_service.py` — 修改（Edge 理由写入方法）
- `backend/app/models/edge_rationale.py` — 新建（Pydantic Schema）
- `src/services/agent-bridge.ts` — 修改（Edge 上下文组装）
- `src/components/canvas/CanvasEdge.svelte` — 修改（标签渲染）
- `backend/tests/unit/test_edge_rationale.py` — 新建
- `__tests__/integration/edge-dialog-flow.test.ts` — 新建
