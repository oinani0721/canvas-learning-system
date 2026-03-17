# Story 3.6: Tips 标注与错误归档

Status: ready-for-dev

## Story

As a 用户,
I want 选中对话文字后标记为 Tips 或让系统自动归档我的错误,
so that 我的关键知识点和薄弱环节被持久化记录，Agent 将来能精准引用。

## Acceptance Criteria

1. **AC-1: 浮动操作面板**
   - **Given** 用户在对话消息中选中一段文字
   - **When** 选中完成（mouseup / touchend）
   - **Then** 选中文字上方出现浮动操作面板
   - **And** 面板包含"打 Tag"（分类标注）和"写 Tips"（关键笔记）两个按钮
   - **And** 面板不遮挡选中文字，跟随选中位置定位
   - **And** 点击面板外部关闭面板

2. **AC-2: Tips 写入 Graphiti**
   - **Given** 用户点击"写 Tips"按钮
   - **When** 弹出 Tips 编辑迷你表单（标题 + 标签选择）
   - **Then** 用户确认后，Tips 保存到 Graphiti（Agent 自报告通道）
   - **And** Tips 数据包含：内容（选中文字）、标题（用户填写）、标签、来源节点 ID、来源对话时间戳
   - **And** 保存成功后 Notice 提示"Tips 已保存"
   - **And** 新 Tips 立即可在 Story 3.4 的上下文注入中被引用

3. **AC-3: 4 类错误自动分类**
   - **Given** Agent 在对话中检测到用户的理解错误
   - **When** Agent 通过 MCP 工具 `record_error` 上报
   - **Then** 系统自动分类错误为 4 类之一：
     - 破题错误（审题、条件识别失误）
     - 推理谬误（逻辑推导步骤错误）
     - 知识点缺失（缺乏必要前置知识）
     - 似懂非懂（表面理解但无法迁移应用）
   - **And** 分类结果存储到 Graphiti（结构化实体：Misconception）

4. **AC-4: 差异化补救策略映射**
   - **Given** 错误被分类归档
   - **When** 系统记录补救建议
   - **Then** 不同错误类型映射到差异化补救策略：
     - 破题错误 → 同结构新题练习
     - 推理谬误 → 找错练习 + 反例构造
     - 知识点缺失 → 回退到定义题
     - 似懂非懂 → 辨析题 + 迁移应用题
   - **And** 补救策略存储在错误记录中，供后续考察出题消费

5. **AC-5: Tag 分类标注**
   - **Given** 用户点击"打 Tag"按钮
   - **When** 弹出标签选择器
   - **Then** 用户可以给选中文字打上分类标签（重要/困惑/灵感/待复习）
   - **And** 标签颜色区分（如重要=红色/困惑=黄色/灵感=绿色/待复习=蓝色）
   - **And** 标注后该消息气泡显示标签标记

## Tasks / Subtasks

- [ ] **Task 1: TipAnnotation 浮动面板组件** (AC: #1)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/components/chat/TipAnnotation.svelte`
  - [ ] 1.2 实现选中文字检测：监听 `mouseup` 事件，获取 `Selection` 对象
  - [ ] 1.3 浮动面板定位：计算选中区域 bounding rect，面板定位在其上方
  - [ ] 1.4 面板内容：两个按钮（"打 Tag" + "写 Tips"）
  - [ ] 1.5 CSS `.cl-chat-annotation-panel`，z-index 高于消息列表
  - [ ] 1.6 点击外部 / 选中取消 → 关闭面板

- [ ] **Task 2: Tips 写入逻辑** (AC: #2)
  - [ ] 2.1 创建 Tips 编辑迷你表单（Modal 或 inline popup）：标题输入 + 标签多选
  - [ ] 2.2 创建 `obsidian-canvas-learning/src/services/tips-service.ts`
  - [ ] 2.3 实现 `saveTip(tip: TipData)`: POST 到后端 `/api/v1/tips` 端点
  - [ ] 2.4 后端端点创建 `backend/app/api/v1/tips.py`：接收 Tip 数据 → 写入 Graphiti
  - [ ] 2.5 Graphiti 实体类型：`LearningTip`（content, title, tags, nodeId, sourceTimestamp）
  - [ ] 2.6 保存成功 → Obsidian `Notice` 提示

- [ ] **Task 3: 错误自动分类系统** (AC: #3, #4)
  - [ ] 3.1 创建 `backend/app/mcp/tools/error_tools.py`：`record_error` MCP 工具
  - [ ] 3.2 实现 4 类错误分类逻辑（基于 Agent 上报的错误描述 + LLM 分类）
  - [ ] 3.3 创建 `backend/app/services/error_classifier.py`：分类器 + 补救策略映射
  - [ ] 3.4 分类结果写入 Graphiti：`Misconception` 实体（errorType, description, remedy, nodeId）
  - [ ] 3.5 补救策略映射表硬编码在 `error_classifier.py` 中

- [ ] **Task 4: Tag 标注功能** (AC: #5)
  - [ ] 4.1 创建标签选择器组件（TipAnnotation 面板的子组件）
  - [ ] 4.2 预定义标签：重要(red) / 困惑(yellow) / 灵感(green) / 待复习(blue)
  - [ ] 4.3 标注后更新消息的 metadata（`tags: string[]`）
  - [ ] 4.4 MessageBubble 渲染时显示标签标记（小色块 badge）
  - [ ] 4.5 标注数据持久化到 SQLite messages 表的 metadata 字段

- [ ] **Task 5: 后端 Graphiti Schema 定义** (AC: #2, #3)
  - [ ] 5.1 创建/扩展 `backend/app/graphiti/entity_types.py`
  - [ ] 5.2 定义 `LearningTip` Pydantic Schema（Graphiti 自定义实体类型）
  - [ ] 5.3 定义 `Misconception` Pydantic Schema（4 类错误 + 补救策略）
  - [ ] 5.4 定义 Edge 类型：`HAS_TIP`, `HAS_MISCONCEPTION`（节点→Tips/错误的关系）

## Dev Notes

### 浮动面板定位算法

```typescript
function positionPanel(selection: Selection): { top: number, left: number } {
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  return {
    top: rect.top - panelHeight - 8, // 选中区域上方 8px
    left: rect.left + (rect.width - panelWidth) / 2 // 水平居中
  };
}
```

### 错误分类与补救策略映射

| 错误类型 | 特征 | 补救策略 |
|---------|------|---------|
| 破题错误 | 审题失误、条件遗漏、问题理解偏差 | 同结构新题（改数字不改结构） |
| 推理谬误 | 逻辑跳步、因果倒置、不当归纳 | 找错练习 + 反例构造 |
| 知识点缺失 | 缺前置知识、概念未学 | 回退到定义题 + 基础概念补充 |
| 似懂非懂 | 能复述不能应用、表面理解 | 辨析题 + 迁移应用（换场景） |

### Graphiti 三通道写入

本 Story 实现"Agent 自报告通道"：
- Tips 由用户手动标注 → 前端 POST → 后端写入 Graphiti
- 错误由 Agent 检测 → MCP `record_error` 工具 → 后端写入 Graphiti

另外两个通道（对话蒸馏、考察提取）在 Story 3.8 和 Story 6.x 中实现。

### 关键约束

1. **浮动面板**：不使用 Obsidian Modal（太重），使用自定义 absolute 定位面板
2. **Graphiti 写入**：需要 Graphiti graphiti_core 实例已初始化（依赖 Story 1.1 的 Neo4j 容器）
3. **分类器**：MVP 阶段使用 LLM 分类（通过 LiteLLM 调用），不实现规则引擎
4. **补救策略**：仅存储策略标识，实际执行在检验白板出题时消费（Story 6.3）

### 不做的事项（防蔓延）

- 不实现对话蒸馏通道（Story 3.8）
- 不实现考察提取通道（Story 6.x）
- 不实现 Tips 在学习档案面板的展示（Story 5.3）
- 不实现错误在"需要加强方向"中的展示（Story 5.3）
- 不实现补救策略的实际执行（Story 6.3 出题时消费）
- 不实现 Tips 编辑/删除功能

### Project Structure Notes

- 前端新建：`obsidian-canvas-learning/src/components/chat/TipAnnotation.svelte`
- 前端新建：`obsidian-canvas-learning/src/services/tips-service.ts`
- 后端新建：`backend/app/api/v1/tips.py`
- 后端新建：`backend/app/mcp/tools/error_tools.py`
- 后端新建：`backend/app/services/error_classifier.py`
- 后端新建/扩展：`backend/app/graphiti/entity_types.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.6] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — 4类错误分类 + 补救策略映射
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — Graphiti 三通道写入

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

### Completion Notes List

- AC-1: TipAnnotation.svelte floating panel with mouseup selection detection, absolute positioning
- AC-2: tips-service.ts + POST /api/v1/tips endpoint -> Graphiti via MemoryService
- AC-3: error_tools.py MCP record_error tool + error_classifier.py with LLM classification
- AC-4: ErrorType enum + ERROR_TYPE_TO_REMEDY mapping in entity_types.py
- AC-5: Tag selector in TipAnnotation.svelte with 4 predefined tags (important/confused/inspiration/review)
- Graphiti entity schemas: LearningTip, Misconception in entity_types.py
- MCP server updated: record_error tool registered (11 total tools)
- Router updated: /api/v1/tips route registered

### File List

- backend/app/graphiti/__init__.py (new)
- backend/app/graphiti/entity_types.py (new)
- backend/app/services/error_classifier.py (new)
- backend/app/mcp/tools/error_tools.py (new)
- backend/app/api/v1/endpoints/tips.py (new)
- backend/app/mcp/server.py (modified - added record_error tool)
- backend/app/mcp/tools/__init__.py (modified - added error_tools)
- backend/app/api/v1/router.py (modified - added tips_router)
- obsidian-canvas-learning/src/components/chat/TipAnnotation.svelte (new)
- obsidian-canvas-learning/src/services/tips-service.ts (new)
