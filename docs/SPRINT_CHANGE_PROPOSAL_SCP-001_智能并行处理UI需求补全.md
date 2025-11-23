# Sprint变更提案 - 智能并行处理UI需求补全

**提案编号**: SCP-001
**创建日期**: 2025-11-12
**提案状态**: ✅ 待用户审批
**影响范围**: PRD v1.1.4 → v1.1.5, Epic 11, Epic 13
**预估时间影响**: +1周

---

## 📋 执行摘要 (Executive Summary)

**问题识别**: Obsidian Plugin UI完全缺少智能并行处理功能暴露，尽管完整的后端实现已存在（Epic 10）。

**推荐路径**: 扩展Epic 13（新增Story 13.8），扩展Epic 11（新增4个API端点），新增功能需求FR2.1。

**核心变更**:
- ✅ 新增PRD需求：FR2.1（智能并行处理UI）
- ✅ 新增Story：Story 13.8（1-2周工作量）
- ✅ 新增API端点：4个RESTful API + 1个WebSocket
- ✅ 时间影响：+1周总时间

---

## 1️⃣ 变更触发和背景 (Trigger & Context)

### 1.1 触发事件

**触发Story**: 无（系统性PRD审计发现的需求缺失）

**发现时间**: 2025-11-12，执行correct-course任务时

**发现方式**: 用户明确指出："关于并行处理也是要在obsidian上提供一个UI按键"

### 1.2 核心问题定义

**问题陈述**:
PRD v1.1.4在Epic 13（Obsidian Plugin）中完全缺少对智能并行处理UI的描述，尽管：
1. ✅ 完整的后端实现已存在（Story 10.2已完成，300+行代码）
2. ✅ CLI命令`/intelligent-parallel`已可用
3. ✅ AsyncExecutionEngine已实现（8倍性能提升）
4. ✅ 智能分组算法已实现（TF-IDF + K-Means）

**问题分类**:
- [x] 是新发现的需求
- [x] 是功能需求和实现不匹配（后端已实现，UI未设计）

### 1.3 影响评估

**直接后果**:
- ❌ 用户无法在Obsidian中使用智能并行处理功能
- ❌ Epic 10的价值无法通过Plugin交付给最终用户
- ❌ FR1的承诺"所有操作均可在Obsidian中完成"未实现

**证据支持**:
1. **代码证据**: `command_handlers/intelligent_parallel_handler.py`（1394行）已完整实现
2. **测试证据**: Epic 10.2的E2E测试全部通过（docs/performance-benchmarks.md）
3. **PRD证据**: Grep搜索结果显示Story 13.4只提到"核心命令（拆解、评分、解释）"，无批量处理相关描述

---

## 2️⃣ Epic影响分析 (Epic Impact Assessment)

### 2.1 当前Epic分析

**Epic 13: Obsidian Plugin开发** - ⚠️ **需要修改**

**现状**: 包含Story 13.1-13.7，聚焦于：
- Canvas工具栏基础按钮（拆解、评分、解释 - 单节点操作）
- 命令面板集成（Ctrl+P）
- 设置面板
- 实时进度推送（针对单Agent执行）

**需要添加**:
- ✅ **新增Story 13.8**: 智能并行处理UI（1-2周工作量）

**理由**:
- 智能并行处理是批量操作，UI复杂度远高于单节点操作
- 需要4个新的UI组件（工具栏按钮、分组预览、进度监控、结果预览）
- 需要与Epic 11的新API端点集成

---

**Epic 11: 后端Python服务** - ⚠️ **需要修改**

**现状**: Story 11.1-11.5已覆盖基础API端点

**需要添加**:
- ✅ **新增Story 11.6**: 智能并行处理API端点（4个REST API + 1个WebSocket）

**API详细规格**:

#### 1. POST `/api/canvas/intelligent-parallel`
**描述**: 触发智能分组分析
**请求体**:
```json
{
  "canvas_path": "笔记库/离散数学/离散数学.canvas",
  "options": {
    "grouping_mode": "intelligent",  // or "manual"
    "max_groups": 6,
    "auto_execute": false
  }
}
```
**响应**:
```json
{
  "session_id": "session-20250112-143022",
  "total_nodes": 12,
  "groups": [
    {
      "group_id": "group-1",
      "agent": "comparison-table",
      "nodes": [{"id": "node-1", "text": "逆否命题 vs 否命题"}],
      "priority": "high",
      "estimated_time": 45
    }
  ],
  "total_estimated_time": 135
}
```

#### 2. POST `/api/canvas/intelligent-parallel/confirm`
**描述**: 用户确认分组后开始执行
**请求体**:
```json
{
  "session_id": "session-20250112-143022",
  "groups": [...]  // 用户可能修改过的分组
}
```
**响应**:
```json
{
  "status": "started",
  "websocket_url": "/ws/intelligent-parallel/session-20250112-143022"
}
```

#### 3. GET `/api/canvas/intelligent-parallel/status/{session_id}`
**描述**: 查询执行状态（轮询备用方案）
**响应**:
```json
{
  "session_id": "session-20250112-143022",
  "status": "running",  // or "completed", "failed"
  "progress": {
    "total": 12,
    "completed": 8,
    "failed": 1,
    "running": 3
  },
  "results": [...]
}
```

#### 4. WebSocket `/ws/intelligent-parallel/{session_id}`
**描述**: 实时进度推送
**推送消息格式**:
```json
{
  "type": "progress_update",
  "timestamp": "2025-01-12T14:32:15Z",
  "data": {
    "group_id": "group-1",
    "node_id": "node-1",
    "status": "completed",
    "output": {
      "file_path": "逆否命题vs否命题-comparison-20250112.md",
      "file_size": 3256
    }
  }
}
```

---

### 2.2 未来Epic分析

**Epic 14+**: 无影响（未来Epic尚未定义）

---

## 3️⃣ 文档冲突分析 (Artifact Conflict Analysis)

### 3.1 PRD冲突

**冲突点1**: FR1承诺 vs 实际能力不匹配

**FR1原文**（Line 216）:
> "所有操作均可在Obsidian原生Canvas编辑器中完成，无需切换到外部工具或CLI"

**实际情况**:
- 智能并行处理功能仅能通过CLI命令`/intelligent-parallel`使用
- Obsidian Plugin完全无此功能

**解决方案**:
- 新增FR2.1，明确智能并行处理UI需求
- 更新FR1的验收标准，增加对批量操作的覆盖检查

---

**冲突点2**: Epic 13范围定义不完整

**当前描述** (Story 13.4):
> "Canvas工具栏支持核心命令（拆解、评分、解释）"

**缺失内容**:
- 无"批量处理"或"智能并行"相关描述
- 仅聚焦于单节点操作

**解决方案**:
- 新增Story 13.8，专门处理智能并行处理UI

---

### 3.2 架构文档冲突

**无冲突** - 架构文档已包含Epic 10的完整技术方案（AsyncExecutionEngine、TF-IDF聚类等），只需在Plugin架构中增加UI层描述。

---

### 3.3 其他文档影响

**需要更新的文档**:
1. ✅ `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md` (v1.1.4 → v1.1.5)
2. ✅ `docs/epic-13-plugin-development-plan.md` (如果存在)
3. ✅ `.claude/commands/intelligent-parallel.md` (更新说明Plugin UI已集成)

---

## 4️⃣ 路径选择和推荐 (Path Forward Evaluation)

### 选项1: 直接扩展Epic 13 ⭐ **推荐**

**描述**: 新增Story 13.8和Story 11.6，扩展现有Epic范围

**优点**:
- ✅ 后端已完整实现，只需UI开发
- ✅ 架构无需变更
- ✅ 时间影响最小（+1周）
- ✅ 不影响已完成的Story

**缺点**:
- ⚠️ 增加Epic 13的工作量（原计划4周 → 5周）

**时间估算**:
- Story 13.8 UI开发: 1周
- Story 11.6 API开发: 3天（与Story 13.8并行）
- E2E测试和文档: 2天
- **总计**: +1周

**风险评估**: 低风险（后端已验证，只需UI集成）

---

### 选项2: 创建新Epic 15（智能并行处理UI专项）

**描述**: 单独创建一个Epic处理所有批量UI功能

**优点**:
- ✅ Epic 13保持原有范围不变
- ✅ 更清晰的Epic职责划分

**缺点**:
- ❌ 时间影响更大（+2周，需要独立的规划和测试周期）
- ❌ 增加管理复杂度
- ❌ 与Epic 13有重复（都在Obsidian Plugin范畴）

**时间估算**: +2周

**风险评估**: 中风险（Epic间依赖增加）

---

### 选项3: 推迟到v2.0版本

**描述**: 当前版本不实现，列入v2.0 Backlog

**优点**:
- ✅ 不影响当前Sprint进度

**缺点**:
- ❌ Epic 10的价值无法交付（8倍性能提升被浪费）
- ❌ FR1承诺无法兑现
- ❌ 用户仍需使用CLI，体验降级

**时间估算**: 0（当前Sprint）

**风险评估**: 高风险（用户期望不满足，Epic 10投资回报低）

---

### 🎯 推荐路径: **选项1 - 直接扩展Epic 13**

**理由**:
1. 后端实现已完成，只需UI暴露（投资回报比最高）
2. 时间影响最小（+1周）
3. 风险最低（无架构变更）
4. 用户痛点立即解决

---

## 5️⃣ 详细变更提案 (Sprint Change Proposal Components)

### 5.1 新增功能需求：FR2.1

**插入位置**: PRD第264行之前（FR2和FR3之间）

**完整内容**:

```markdown
#### FR2.1: 智能并行处理UI (Must Have - P0)

**背景**: Epic 10智能并行处理系统的完整后端实现已完成（IntelligentParallelCommandHandler + AsyncExecutionEngine + IntelligentParallelScheduler），但缺少Obsidian Plugin的UI暴露。当前仅能通过CLI命令`/intelligent-parallel`使用。

**描述**: 在Obsidian Canvas工具栏添加"智能批量处理"按钮，用户可一键触发对当前Canvas的所有黄色节点进行智能分组和Agent批量调用。

**核心能力**:
- ✅ **智能分组**: TF-IDF向量化 + K-Means聚类，自动将语义相近的黄色节点分组
- ✅ **Agent推荐**: 基于节点内容关键词，自动推荐最合适的6个解释Agent
- ✅ **异步并发**: AsyncExecutionEngine支持最多12个Agent并发执行（Epic 10.2的8倍性能提升）
- ✅ **实时进度**: WebSocket推送任务进度、完成状态和错误信息
- ✅ **3层Canvas结构**: 黄色节点 → 蓝色TEXT节点（说明） → File节点（.md文档）

**UI交互流程**:

**Step 1: 工具栏按钮**
```
┌─────────────────────────────────────────┐
│ Canvas工具栏                             │
│ [🎯 拆解] [📊 评分] [📝 解释] [⚡ 智能批量处理] │
└─────────────────────────────────────────┘
```

**Step 2: 智能分组预览模态框**
```
┌────────────────────────────────────────────┐
│ 智能并行处理 - 分组预览                       │
├────────────────────────────────────────────┤
│ 检测到 12 个黄色节点，智能分组为 4 组:        │
│                                            │
│ 📊 Group 1: 对比类概念 (3节点)              │
│   推荐Agent: comparison-table              │
│   • 逆否命题 vs 否命题                      │
│   • 充分条件 vs 必要条件                    │
│   • 演绎法 vs 归纳法                        │
│   优先级: High                             │
│                                            │
│ 🔍 Group 2: 复杂概念澄清 (4节点)            │
│   推荐Agent: clarification-path            │
│   • 数学归纳法的本质                        │
│   • 反证法的适用条件                        │
│   优先级: High                             │
│                                            │
│ ⚓ Group 3: 记忆类内容 (3节点)               │
│   推荐Agent: memory-anchor                 │
│   • 命题的四种形式                          │
│   优先级: Normal                           │
│                                            │
│ 🎯 Group 4: 渐进式理解 (2节点)              │
│   推荐Agent: four-level-explanation        │
│   • 集合论基础                             │
│   优先级: Normal                           │
│                                            │
│ [ 修改分组 ] [ 取消 ] [ 开始处理 (预计2分钟) ] │
└────────────────────────────────────────────┘
```

**Step 3: 实时进度显示**
```
┌────────────────────────────────────────────┐
│ 智能并行处理 - 执行中                        │
├────────────────────────────────────────────┤
│ 总进度: ████████░░░░░░░░ 8/12 (67%)        │
│                                            │
│ ✅ Group 1 (comparison-table): 已完成       │
│    ├─ 逆否命题 vs 否命题.md (3.2KB)         │
│    ├─ 充分条件 vs 必要条件.md (2.8KB)       │
│    └─ 演绎法 vs 归纳法.md (3.5KB)           │
│                                            │
│ ⏳ Group 2 (clarification-path): 进行中 (2/4)│
│    ├─ ✅ 数学归纳法的本质.md (5.1KB)        │
│    ├─ ✅ 反证法的适用条件.md (4.8KB)        │
│    ├─ ⏳ 处理中...                         │
│    └─ ⏸️ 等待中...                         │
│                                            │
│ ⏸️ Group 3 (memory-anchor): 队列中          │
│ ⏸️ Group 4 (four-level-explanation): 队列中 │
│                                            │
│ [ 暂停 ] [ 取消 ] [ 最小化 ]                │
└────────────────────────────────────────────┘
```

**Step 4: 完成结果预览**
```
┌────────────────────────────────────────────┐
│ 智能并行处理 - 完成                          │
├────────────────────────────────────────────┤
│ ✅ 成功处理 11/12 个节点                     │
│ ❌ 1个节点失败                               │
│ ⏱️ 总耗时: 2分15秒                          │
│                                            │
│ 生成文档:                                   │
│ • 3个对比表 (📊)                            │
│ • 4个澄清路径 (🔍)                          │
│ • 3个记忆锚点 (⚓)                           │
│ • 1个四层次解释 (🎯)                        │
│                                            │
│ ❌ 失败节点:                                │
│ • "集合论基础" - Agent执行超时              │
│   [ 单独重试 ]                             │
│                                            │
│ Canvas已自动更新，添加了11个蓝色说明节点和   │
│ 11个文档节点。                              │
│                                            │
│ [ 查看错误日志 ] [ 关闭 ]                   │
└────────────────────────────────────────────┘
```

**验收标准**:
- ✅ Canvas工具栏显示"智能批量处理"按钮（图标：⚡或🔄）
- ✅ 点击按钮触发智能分组分析（<3秒完成）
- ✅ 分组预览模态框正确显示：
  - 检测到的黄色节点总数
  - 智能分组结果（Group ID + Agent推荐 + 节点列表 + 优先级）
  - 预估处理时间
- ✅ 用户可手动修改分组或Agent推荐（可选功能）
- ✅ 实时进度显示：
  - 总进度条（百分比）
  - 每个Group的执行状态（等待中/进行中/已完成/失败）
  - 已生成文档的文件名和大小
- ✅ 完成结果预览：
  - 成功/失败节点统计
  - 生成文档分类统计
  - 失败节点的错误信息和重试按钮
- ✅ Canvas自动更新：
  - 3层结构正确（黄色→蓝色TEXT→File）
  - 蓝色节点显示Agent类型和生成时间
  - File节点正确链接到生成的.md文件
- ✅ 错误处理：
  - 如果无黄色节点，显示友好提示
  - Agent执行失败时，不中断其他Agent
  - 提供错误日志查看入口

**关联Epic/Story**:
- Epic 11: 需要新增4个REST API端点（详见Story 11.6）
- Epic 13: 需要新增Story 13.8（UI实现，1-2周）

**优先级**: Must Have - P0（已有完整后端实现，只缺UI暴露）

**时间估算**: +1周（UI开发 + API集成 + E2E测试）
```

---

### 5.2 新增Story：Story 13.8

**Epic**: Epic 13 - Obsidian Plugin开发

**Story标题**: Story 13.8 - 智能并行处理UI实现

**Story描述**:
实现智能并行处理功能的完整UI，包括工具栏按钮、智能分组预览、实时进度监控和结果预览，集成Epic 10的后端实现。

**任务清单**:

**Task 1: Canvas工具栏按钮** (1天)
- [ ] 在Canvas工具栏添加"智能批量处理"按钮（图标⚡）
- [ ] 按钮点击触发智能分组API调用
- [ ] 处理无黄色节点情况（显示Toast提示）
- [ ] 添加Loading状态（分组分析中...）

**Task 2: 智能分组预览模态框** (2天)
- [ ] 实现分组预览模态框（Modal组件）
- [ ] 显示分组结果：
  - 每个Group的Agent推荐、节点列表、优先级
  - 使用emoji表示Agent类型（📊🔍⚓🎯）
- [ ] 实现"修改分组"功能（可选）：
  - 用户可手动调整Agent推荐
  - 用户可重新分配节点到不同Group
- [ ] "开始处理"按钮触发确认API
- [ ] 显示预估处理时间

**Task 3: 实时进度显示** (2天)
- [ ] 实现进度监控模态框（可最小化）
- [ ] WebSocket连接到`/ws/intelligent-parallel/{session_id}`
- [ ] 实时更新：
  - 总进度条（百分比）
  - 每个Group的状态（✅完成/⏳进行中/⏸️等待中/❌失败）
  - 已生成文档的文件名和大小
- [ ] 实现"暂停"和"取消"功能（调用对应API）
- [ ] WebSocket断开后回退到轮询模式（GET status API）

**Task 4: 完成结果预览** (1天)
- [ ] 显示执行摘要：
  - 成功/失败节点统计
  - 生成文档分类统计（按Agent类型）
  - 总耗时
- [ ] 显示失败节点列表：
  - 错误信息
  - "单独重试"按钮
- [ ] "查看错误日志"按钮打开详细日志面板
- [ ] 关闭按钮

**Task 5: 错误处理和边界情况** (1天)
- [ ] 处理API调用失败（网络错误、超时）
- [ ] 处理Agent执行超时（显示超时提示，不中断其他Agent）
- [ ] 处理Canvas文件锁定冲突（FileLock机制）
- [ ] 添加友好的错误提示Toast
- [ ] 记录错误到日志系统

**验收标准**:
- ✅ 所有FR2.1的验收标准通过
- ✅ 与4个新API端点集成成功
- ✅ E2E测试通过（至少3个测试场景）
- ✅ UI组件通过Accessibility检查（ARIA标签完整）
- ✅ 性能测试：12节点<3分钟完成

**Story点数**: 8 Points

**预估时间**: 7天（1周）

---

### 5.3 新增Story：Story 11.6

**Epic**: Epic 11 - 后端Python服务

**Story标题**: Story 11.6 - 智能并行处理API端点

**Story描述**:
为Obsidian Plugin提供4个REST API端点和1个WebSocket端点，暴露Epic 10的智能并行处理能力。

**任务清单**:

**Task 1: POST `/api/canvas/intelligent-parallel`** (1天)
- [ ] 实现智能分组分析端点
- [ ] 调用`IntelligentParallelCommandHandler._scan_yellow_nodes()`
- [ ] 调用`IntelligentParallelScheduler.intelligent_grouping()`
- [ ] 生成session_id（UUID格式）
- [ ] 缓存分组结果到Redis（TTL: 10分钟）
- [ ] 返回JSON响应（groups数组 + estimated_time）

**Task 2: POST `/api/canvas/intelligent-parallel/confirm`** (1天)
- [ ] 接收用户确认的分组
- [ ] 启动AsyncExecutionEngine异步任务
- [ ] 将任务状态存储到Redis
- [ ] 返回WebSocket URL
- [ ] 处理invalid session_id错误

**Task 3: GET `/api/canvas/intelligent-parallel/status/{session_id}`** (0.5天)
- [ ] 从Redis查询任务状态
- [ ] 返回progress对象（total/completed/failed/running）
- [ ] 返回results数组（已完成的任务结果）
- [ ] 处理session不存在的情况（404错误）

**Task 4: WebSocket `/ws/intelligent-parallel/{session_id}`** (1.5天)
- [ ] 实现WebSocket连接处理
- [ ] 订阅Redis Pub/Sub频道（`intelligent-parallel:{session_id}`）
- [ ] 推送progress_update消息（JSON格式）
- [ ] 推送task_completed消息
- [ ] 推送task_failed消息
- [ ] 推送session_completed消息
- [ ] 处理客户端断开重连（恢复进度）
- [ ] WebSocket心跳检测（每30秒ping/pong）

**验收标准**:
- ✅ 所有4个API端点符合Swagger规范
- ✅ API集成测试通过（Pytest，至少10个测试用例）
- ✅ WebSocket压力测试通过（50并发连接）
- ✅ Redis缓存正确设置TTL（避免内存泄漏）
- ✅ 错误处理完整（400/404/500错误码）

**Story点数**: 5 Points

**预估时间**: 3天（可与Story 13.8并行开发）

---

### 5.4 PRD版本更新

**变更**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`

**版本**: v1.1.4 → v1.1.5

**变更摘要**:
1. **新增FR2.1**（Line 264之前插入）
2. **更新Epic 13描述**（增加Story 13.8引用）
3. **更新Epic 11描述**（增加Story 11.6引用）
4. **更新Story总数**：从"55个Story"更新为"57个Story"
5. **更新时间线**：总时间从"12周"更新为"13周"

**Changelog**:
```markdown
## 版本历史

### v1.1.5 (2025-11-12)
- 🆕 新增FR2.1: 智能并行处理UI（Must Have - P0）
- 📝 新增Story 13.8: 智能并行处理UI实现（7天）
- 📝 新增Story 11.6: 智能并行处理API端点（3天）
- ⏱️ 时间线更新: +1周（总计13周）
- 📊 Story总数: 55 → 57

### v1.1.4 (Previous)
- [原有Changelog内容]
```

---

### 5.5 其他文档更新

**1. `.claude/commands/intelligent-parallel.md`**

**变更**: 增加Obsidian Plugin UI说明

**新增内容**（文件末尾追加）:
```markdown
## 🎨 Obsidian Plugin集成 (v1.1.5+)

**UI入口**: Canvas工具栏 → "⚡ 智能批量处理"按钮

**使用方式**:
1. 打开任意Canvas白板
2. 点击工具栏的"⚡ 智能批量处理"按钮
3. 系统自动分析所有黄色节点并智能分组
4. 在预览模态框中查看分组结果和Agent推荐
5. 点击"开始处理"，实时监控进度
6. 完成后查看结果摘要

**与CLI命令的关系**:
- CLI命令`/intelligent-parallel`仍然可用（适合开发者和高级用户）
- Obsidian Plugin UI提供更友好的交互体验（推荐普通用户使用）
- 两者共享相同的后端实现（Epic 10）

**相关文档**:
- PRD FR2.1: 智能并行处理UI需求
- Story 13.8: UI实现文档
- Story 11.6: API端点文档
```

---

**2. `docs/epic-13-plugin-development-plan.md`** （如果存在）

**变更**: 增加Story 13.8

**插入位置**: Story 13.7之后

**内容**: （参考5.2节的Story 13.8详细描述）

---

## 6️⃣ 风险评估和缓解策略 (Risk Assessment)

### 风险1: UI复杂度超出预期 ⚠️ **中风险**

**描述**: 实时进度监控和WebSocket集成可能遇到技术挑战

**影响**: 开发时间延长0.5-1周

**缓解策略**:
1. ✅ 使用成熟的React组件库（如Ant Design的Progress组件）
2. ✅ WebSocket断开时回退到轮询模式（已有GET status API）
3. ✅ 先实现核心功能（分组预览+执行），进度监控可在后续迭代优化

**概率**: 30%

---

### 风险2: API性能瓶颈 ⚠️ **低风险**

**描述**: 多个用户同时触发智能并行处理可能导致服务器负载过高

**影响**: API响应变慢（>5秒），用户体验下降

**缓解策略**:
1. ✅ 使用Redis任务队列限制并发数（最多3个session同时执行）
2. ✅ 添加任务排队提示（"当前有2个任务在您之前，预计等待3分钟"）
3. ✅ Epic 10的AsyncExecutionEngine已优化性能（8倍提升）

**概率**: 15%

---

### 风险3: 用户不理解智能分组结果 ⚠️ **中风险**

**描述**: 用户可能不明白为什么系统推荐特定Agent或分组方式

**影响**: 用户不信任系统推荐，手动修改分组（增加操作成本）

**缓解策略**:
1. ✅ 在分组预览中添加"为什么选择此Agent"的Tooltip提示
2. ✅ 提供"查看分组算法说明"链接（指向帮助文档）
3. ✅ 允许用户手动修改分组（Task 2已包含此功能）
4. ✅ 在用户手册中增加智能分组原理的通俗解释

**概率**: 40%

---

### 风险4: Canvas文件锁定冲突 ⚠️ **低风险**

**描述**: 用户在智能并行处理执行期间手动编辑Canvas，导致冲突

**影响**: Canvas修改失败，部分节点未正确添加

**缓解策略**:
1. ✅ 使用FileLock机制（`canvas_utils.py`已实现）
2. ✅ 在执行期间显示"Canvas已锁定，请勿手动编辑"提示
3. ✅ 提供冲突解决UI（"保留手动修改"或"使用Agent生成结果"）
4. ✅ 自动备份Canvas文件（执行前创建`.backup`文件）

**概率**: 10%

---

## 7️⃣ 验收标准 (Acceptance Criteria)

### 7.1 功能验收

**FR2.1验收**:
- ✅ 所有FR2.1定义的验收标准通过（共15项）
- ✅ UI交互流程4个步骤全部实现
- ✅ 错误处理覆盖所有已知边界情况

**Story 13.8验收**:
- ✅ 5个Task全部完成并通过Code Review
- ✅ E2E测试通过（至少3个场景）
- ✅ UI组件通过Accessibility审查

**Story 11.6验收**:
- ✅ 4个API端点符合Swagger规范
- ✅ 集成测试通过（至少10个测试用例）
- ✅ WebSocket压力测试通过（50并发）

---

### 7.2 文档验收

**PRD更新**:
- ✅ v1.1.5 Changelog正确记录所有变更
- ✅ FR2.1内容完整（包含UI Mockup和验收标准）
- ✅ Epic 13和Epic 11的Story列表更新

**Story文档**:
- ✅ Story 13.8和Story 11.6有完整的任务清单
- ✅ 验收标准明确且可测量
- ✅ 技术实现方案清晰（包含代码示例）

**帮助文档**:
- ✅ 用户手册增加"智能批量处理"章节
- ✅ `.claude/commands/intelligent-parallel.md`更新Obsidian Plugin说明

---

### 7.3 交付物检查清单

**必须交付**:
- ✅ PRD v1.1.5（包含FR2.1）
- ✅ Story 13.8完整文档
- ✅ Story 11.6完整文档
- ✅ 4个新API端点的Swagger规范
- ✅ UI Mockup（ASCII艺术或Figma链接）

**推荐交付**:
- ✅ 智能分组算法原理说明文档（面向用户）
- ✅ WebSocket集成技术文档（面向开发者）
- ✅ E2E测试用例文档

---

## 8️⃣ 下一步行动 (Recommended Actions)

### 阶段1: 文档批准和更新 ⏱️ 1天

**任务**:
1. ✅ 用户审批本Sprint Change Proposal（SCP-001）
2. ✅ 更新PRD到v1.1.5（插入FR2.1）
3. ✅ 创建Story 13.8和Story 11.6详细文档
4. ✅ 更新Epic 13和Epic 11的Story列表

**负责人**: PM Agent (Sarah)

---

### 阶段2: 技术POC验证 ⏱️ 2天 (可选但推荐)

**任务**:
1. ✅ 开发最简化的UI Mockup（HTML+CSS）
2. ✅ 验证WebSocket集成可行性
3. ✅ 测试Redis任务队列性能
4. ✅ 验证Canvas文件锁定机制

**负责人**: Architect Agent (Morgan) + Dev Agent (James)

**目标**: 识别潜在技术风险，避免开发过程中出现阻塞

---

### 阶段3: Sprint规划 ⏱️ 0.5天

**任务**:
1. ✅ 将Story 13.8和Story 11.6加入下一个Sprint
2. ✅ 分配开发资源（FE Dev + BE Dev）
3. ✅ 确定Sprint目标和验收标准
4. ✅ 创建Jira/GitHub Issues

**负责人**: SM Agent (Bob)

---

### 阶段4: 开发和测试 ⏱️ 7天

**任务**:
1. ✅ 并行开发Story 13.8（UI）和Story 11.6（API）
2. ✅ 每日Scrum跟踪进度
3. ✅ Code Review和集成测试
4. ✅ E2E测试和性能测试

**负责人**: Dev Agent (James) + QA Agent (Quinn)

---

### 阶段5: 发布和回顾 ⏱️ 1天

**任务**:
1. ✅ 发布v1.1.5到Production
2. ✅ 更新用户文档和帮助中心
3. ✅ Sprint回顾会议（总结经验教训）
4. ✅ 收集用户反馈（第一周）

**负责人**: PO Agent + SM Agent (Bob)

---

## 📞 提案联系人

**提案作者**: PM Agent (Sarah)
**审批人**: 用户
**技术顾问**: Architect Agent (Morgan)
**执行负责人**: SM Agent (Bob)

---

## 📚 参考文档

1. **PRD当前版本**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md` (v1.1.4)
2. **Epic 10实现文档**: `docs/HONEST_STATUS_REPORT_EPIC10.md`
3. **性能基准**: `docs/performance-benchmarks.md`
4. **智能并行处理Handler**: `command_handlers/intelligent_parallel_handler.py` (1394行)
5. **异步执行引擎**: `command_handlers/async_execution_engine.py` (311行)
6. **智能调度器**: `schedulers/intelligent_parallel_scheduler.py` (330行)
7. **CLI命令定义**: `.claude/commands/intelligent-parallel.md`

---

## ✅ 提案状态

**当前状态**: ✅ 待用户审批

**下一步**: 等待用户反馈和确认

**审批选项**:
1. ✅ **批准** - 立即进入阶段1（文档更新）
2. ⚠️ **修改后批准** - 用户提出修改意见，PM调整后重新提交
3. ❌ **拒绝** - 说明理由，PM重新评估其他路径（如选项2或选项3）

---

**文档生成时间**: 2025-11-12
**文档版本**: SCP-001-v1.0
**BMad™ Core版本**: 兼容
