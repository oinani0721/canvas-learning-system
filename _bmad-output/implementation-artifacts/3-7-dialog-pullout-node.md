# Story 3.7: 对话拉出节点

Status: ready-for-dev

## Story

As a 用户,
I want 选中对话中的精彩解释拖到白板上生成新知识节点,
so that 对话中的见解能成为知识图谱的一部分。

## Acceptance Criteria

1. **AC-1: 选中文字拖拽到白板**
   - **Given** 用户在对话面板中选中一段文字
   - **When** 拖拽选中文字到白板区域
   - **Then** 在白板上鼠标释放位置生成新的文本节点
   - **And** 节点内容为选中的文字
   - **And** 操作与白板原生创建节点体验一致（节点外观、大小、可编辑性）

2. **AC-2: LLM 自动建议关系**
   - **Given** 新节点从对话中拉出
   - **When** 节点创建完成
   - **Then** 系统自动调用 LLM 推荐与原节点的关系类型
   - **And** 以非模态提示展示建议（如"建议与 [原节点] 建立 [是前置知识] 关系"）
   - **And** 用户可接受（自动创建 Edge）或忽略

3. **AC-3: 新节点同步到后端**
   - **Given** 拉出的新节点创建成功
   - **When** 节点同步管道触发
   - **Then** 新节点自动同步到后端 Neo4j（复用 Story 1.5 的 delta sync 管道）
   - **And** 如果用户接受了关系建议，Edge 也同步到后端

4. **AC-4: 来源追溯**
   - **Given** 新节点从对话中拉出
   - **When** 节点创建
   - **Then** 节点 metadata 记录来源信息：`sourceType: 'dialog_pullout'`, `sourceNodeId`, `sourceMessageId`
   - **And** 学习档案面板（Story 5.3）未来可展示"来源对话"链接

## Tasks / Subtasks

- [ ] **Task 1: 拖拽交互实现** (AC: #1)
  - [ ] 1.1 在 `MessageBubble.svelte`（Story 3.3）中启用选中文字的 drag 能力
  - [ ] 1.2 监听 `dragstart` 事件：将选中文字 + 来源 metadata 写入 `dataTransfer`
  - [ ] 1.3 在 `CanvasView.svelte`（Story 1.4）中监听 `drop` 事件
  - [ ] 1.4 `drop` 事件处理：从 `dataTransfer` 读取文字 → 在 drop 位置创建新节点
  - [ ] 1.5 拖拽过程中显示视觉反馈（半透明文字跟随鼠标 + 白板显示落点预览）

- [ ] **Task 2: 节点创建逻辑** (AC: #1, #3, #4)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/services/pullout-service.ts`
  - [ ] 2.2 实现 `createPulloutNode(content, position, sourceInfo)`: 创建节点 + 写入 Store
  - [ ] 2.3 新节点数据模型：`{ id, type: 'text', content, x, y, width, height, metadata: { sourceType, sourceNodeId, sourceMessageId } }`
  - [ ] 2.4 节点创建后触发 delta sync（复用 Story 1.5 的 Outbox 管道）
  - [ ] 2.5 节点大小根据内容长度自适应（短文字小节点，长文字大节点）

- [ ] **Task 3: LLM 关系建议** (AC: #2)
  - [ ] 3.1 创建 `obsidian-canvas-learning/src/services/relation-suggester.ts`
  - [ ] 3.2 实现 `suggestRelation(newNodeContent, sourceNodeContent)`: 调用后端 LLM API
  - [ ] 3.3 后端端点 `POST /api/v1/suggestions/relation`：输入两个节点内容 → LLM 推荐关系类型
  - [ ] 3.4 关系类型范围：是前置知识 / 是应用案例 / 是对比概念 / 是子概念 / 是补充说明
  - [ ] 3.5 前端显示非模态 Toast 提示：用户可 Accept / Dismiss
  - [ ] 3.6 Accept → 自动创建 Edge + 同步到后端 / Dismiss → 仅保留独立节点

- [ ] **Task 4: 后端关系建议端点** (AC: #2)
  - [ ] 4.1 创建 `backend/app/api/v1/suggestions.py`：`POST /api/v1/suggestions/relation`
  - [ ] 4.2 LLM prompt：给定两个概念内容，推荐最合适的关系类型 + 理由
  - [ ] 4.3 使用 LiteLLM 调用（FR-AGENT-03 不锁定厂商）
  - [ ] 4.4 返回格式：`{ relation_type, confidence, reason }`
  - [ ] 4.5 LLM 调用超时 5s → 超时不建议（不阻塞节点创建）

## Dev Notes

### 拖拽数据传输格式

```typescript
// dragstart 事件中设置
event.dataTransfer.setData('application/canvas-pullout', JSON.stringify({
  content: selectedText,
  sourceNodeId: currentNodeId,
  sourceMessageId: messageId,
  timestamp: new Date().toISOString()
}));
event.dataTransfer.setData('text/plain', selectedText); // 兜底
```

### 关系类型定义

| 关系类型 | Edge Label | 方向 |
|---------|-----------|------|
| 是前置知识 | `IS_PREREQUISITE` | 原→新 |
| 是应用案例 | `IS_APPLICATION` | 原→新 |
| 是对比概念 | `CONTRASTS_WITH` | 双向 |
| 是子概念 | `IS_SUBCONCEPT` | 原→新 |
| 是补充说明 | `SUPPLEMENTS` | 原→新 |

### 关键约束

1. **拖拽跨面板**：从右侧对话面板拖到中部白板区域，需要处理不同 DOM 容器间的拖拽
2. **节点创建复用**：新节点的数据结构和同步管道与白板原生创建节点完全一致（Story 1.4/1.5）
3. **关系建议非阻塞**：LLM 推荐是异步的，不阻塞节点创建。建议在节点创建后 1-2s 内弹出
4. **来源追溯只存不展**：metadata 存储来源信息，但展示功能在 Story 5.3 学习档案面板中实现
5. **拖拽视觉反馈**：使用 HTML5 Drag API 的 `dragImage` 或自定义 ghost element

### 不做的事项（防蔓延）

- 不实现从检验白板拖出节点（Story 6.5）
- 不实现 Edge 自动创建后的 Edge 对话触发（Story 4.1）
- 不实现来源对话链接的展示/跳转（Story 5.3）
- 不实现批量拖出多段文字
- 不实现拖拽到已有节点上合并内容

### Project Structure Notes

- 前端新建：`obsidian-canvas-learning/src/services/pullout-service.ts`
- 前端新建：`obsidian-canvas-learning/src/services/relation-suggester.ts`
- 后端新建：`backend/app/api/v1/suggestions.py`
- 扩展：`MessageBubble.svelte`（Story 3.3）添加 drag 能力
- 扩展：白板 CanvasView（Story 1.4）添加 drop 处理

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.7] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — 对话内交互操作层
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — Neo4j Edge 类型命名规范

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
