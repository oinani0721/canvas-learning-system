# Story 6.5: 递归考察与新节点同步

Status: ready-for-dev

## Story

As a 用户,
I want 考察中发现新盲区时拉出新节点，新节点可继续被考察，发现的内容实时同步回原白板，
so that 知识盲区不断被发掘并补充到知识图谱中。

## Acceptance Criteria

1. **AC-1: 检验白板中拉出新节点（FR-EXAM-05）**
   - **Given** 用户在检验白板对话中发现新盲区
   - **When** 选中对话文字拖到白板区域
   - **Then** 在检验白板上生成新的文本节点，内容为选中文字
   - **And** 操作体验与原白板 FR-CONV-08 对话拉出节点完全一致
   - **And** 系统自动建议与原考察节点的关系（LLM 推荐关系类型）
   - **And** 新节点在检验白板上可见、可交互

2. **AC-2: 新节点实时同步回原白板（FR-EXAM-05, FR-EXAM-18）**
   - **Given** 用户在检验白板中拉出新节点
   - **When** 新节点创建完成
   - **Then** 新节点及其关系边实时同步回原白板
   - **And** 原白板上立刻出现对应的新节点（用户回到原白板时能看到）
   - **And** 同步通过 exam_service → sync_service → Neo4j + IndexedDB 双写实现
   - **And** 新节点的 sourceExamId 字段记录来源检验白板 ID

3. **AC-3: 检验白板中所有数据变更实时同步（FR-EXAM-18）**
   - **Given** 用户在检验白板中操作
   - **When** 产生以下数据变更
   - **Then** 以下变更实时同步回原白板对应节点：
     - Tips/Tag 标注 → 原白板对应节点的 Graphiti 数据更新
     - 精通度更新 → 原白板对应节点的颜色变化
     - 新 Edge 创建 → 原白板出现对应连线
   - **And** 同步延迟 < 2s（Outbox delta sync 机制）
   - **And** 前端 UI 即时反映变化

4. **AC-4: 递归考察——新节点可继续被考察（FR-EXAM-06）**
   - **Given** 用户在检验白板中确认了新拉出的节点
   - **When** 用户点击新节点
   - **Then** 右侧面板打开该新节点的 AI 对话（ChatPanel 考察模式）
   - **And** Agent 可对该新节点继续深入剖析和考察（与原有节点考察体验一致）
   - **And** Agent 可为新节点出题（generate_question 支持 target_node_id = 新节点 ID）
   - **And** 新节点考察完成后同样触发 AutoSCORE 评分 → BKT/FSRS 更新

5. **AC-5: 用户驱动终止——"不点"= 自然结束（FR-EXAM-06）**
   - **Given** 检验白板中有新拉出的节点
   - **When** 用户选择不点击新节点
   - **Then** 考察自然结束，不强制用户继续
   - **And** 不弹出"是否继续深入？"确认框（用户掌控节奏）
   - **And** 用户可随时回到之前的考察对话，或开始考察其他节点

6. **AC-6: 递归深度无限制但有自然收敛**
   - **Given** 用户持续递归考察（拉出新节点→考察→再拉出→再考察）
   - **When** 递归发生
   - **Then** 系统不设人为递归深度限制
   - **And** 自然收敛机制：越深入的节点越细粒度，出题范围越窄，用户自然觉得"够了"
   - **And** 认知负荷控制（Story 6.7）作为时间维度的收敛保障
   - **And** exam-state 记录 discoveredNodes 列表，追踪递归发现链

7. **AC-7: 新发现节点追踪**
   - **Given** 考察过程中产生新节点
   - **When** exam-state 更新
   - **Then** discoveredNodes 列表记录每个新节点的：
     - nodeId：新节点 ID
     - sourceNodeId：从哪个节点的对话中拉出
     - depth：递归深度（第 1 层 = 从原考察节点拉出，第 2 层 = 从第 1 层新节点拉出...）
     - timestamp：发现时间
   - **And** discoveredNodes 数据用于 Story 6.8 考察记录保存

## Tasks / Subtasks

- [ ] **Task 1: 检验白板中拉出节点功能** (AC: #1)
  - [ ] 1.1 复用原白板的"对话拉出节点"交互逻辑（Story 3.7 SelectionToolbar + 拖拽）
  - [ ] 1.2 在 ExamCanvas 中启用拉出节点交互
  - [ ] 1.3 新节点创建时记录 sourceExamId + sourceNodeId 元数据
  - [ ] 1.4 LLM 推荐新节点与原考察节点的关系类型

- [ ] **Task 2: 新节点实时同步回原白板** (AC: #2, #3)
  - [ ] 2.1 在 exam_service 中实现 sync_node_to_source_canvas() 方法
  - [ ] 2.2 新节点双写：检验白板 IndexedDB + 原白板 IndexedDB + Neo4j
  - [ ] 2.3 新 Edge 双写：检验白板 + 原白板
  - [ ] 2.4 Tips/Tag 标注同步：通过 Graphiti node_id 自然关联（不需要额外同步）
  - [ ] 2.5 精通度更新同步：mastery_engine 使用 node_id 全局唯一，自动关联

- [ ] **Task 3: 递归考察支持** (AC: #4, #5, #6)
  - [ ] 3.1 新节点点击后 ChatPanel 正常打开考察模式对话
  - [ ] 3.2 generate_question MCP 工具支持 target_node_id = 新节点 ID
  - [ ] 3.3 AutoSCORE 对新节点正常工作
  - [ ] 3.4 不设递归深度限制，依赖用户自主决策和认知负荷提醒

- [ ] **Task 4: 新发现节点追踪** (AC: #7)
  - [ ] 4.1 exam-state 中维护 discoveredNodes 列表
  - [ ] 4.2 每次拉出新节点时追加记录（nodeId, sourceNodeId, depth, timestamp）
  - [ ] 4.3 同步更新后端 exam_session 的 discovered_nodes 字段

- [ ] **Task 5: 端到端验证** (AC: #1-#7)
  - [ ] 5.1 测试：检验白板中拉出节点 → 原白板出现该节点
  - [ ] 5.2 测试：点击新节点 → 打开考察对话 → Agent 可出题
  - [ ] 5.3 测试：新节点被考察 → AutoSCORE → 颜色变化
  - [ ] 5.4 测试：连续递归 3 层 → 所有节点均同步到原白板
  - [ ] 5.5 测试：不点击新节点 → 考察自然结束，不弹框

## Dev Notes

### 架构定位

本 Story 实现检验白板的核心创新功能——递归考察。这是全球零竞品的功能，Layer 3 创新级别。回退策略：退化为单轮考察（无递归，无新节点同步）。

### 依赖关系

- **依赖 Story 3.7**：对话拉出节点（SelectionToolbar + 拖拽交互）
- **依赖 Story 6.1**：ExamCanvas 基础框架
- **依赖 Story 6.3**：generate_question 支持任意 node_id
- **依赖 Story 6.4**：AutoSCORE 对新节点的评分
- **被 Story 6.8 依赖**：discoveredNodes 数据纳入考察记录

### 递归考察数据流

```
用户选中文字 → 拖到检验白板 → 新节点创建（检验白板 + 原白板双写）
  → 用户点击新节点 → ChatPanel 考察模式
  → Agent 对新节点出题 → 用户回答
  → AutoSCORE 评分 → BKT/FSRS 更新 → 颜色变化
  → 对话中又发现新盲区 → 再拉出新节点（递归）
```

### 同步策略

检验白板的数据同步有两个方向：
1. **检验白板 → 原白板**：新节点、新 Edge、Tips/Tag 实时同步
2. **原白板 → 检验白板**：精通度变化自动反映（mastery_engine 全局统一）

同步机制复用 Story 1.5 的 Outbox delta sync，不需要新建同步通道。

### 回退策略

- **Level 1**：递归正常工作
- **Level 2**：递归失败 → 新节点可拉出但不可继续考察（退化为笔记功能）
- **Level 3**：同步失败 → 新节点仅在检验白板可见，不同步到原白板（本地暂存，后续重试）

### Project Structure Notes

- 复用 Story 3.7 的 SelectionToolbar 交互组件
- exam_service 新增 sync_node_to_source_canvas 方法
- exam-state 新增 discoveredNodes 管理

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.5] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#能力域4] — FR-EXAM-05/06/18
- [Source: _bmad-output/planning-artifacts/prd.md#Layer3创新] — 检验白板递归考察回退策略
- [Source: _bmad-output/planning-artifacts/architecture.md#考察启动流] — 考察数据流
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#旅程2] — 递归考察步骤 7-8
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#体验原则] — "考察即发现"+"用户掌控节奏"

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/exam_service.py` — 修改（添加 sync_node_to_source_canvas）
- `src/stores/exam-state.svelte.ts` — 修改（添加 discoveredNodes 管理）
- `src/components/exam/ExamCanvas.svelte` — 修改（启用拉出节点交互）
- `backend/app/models/exam_models.py` — 修改（添加 DiscoveredNode 模型）
