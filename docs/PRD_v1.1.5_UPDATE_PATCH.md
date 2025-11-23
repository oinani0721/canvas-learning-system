# PRD v1.1.5 更新补丁

**目标文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
**当前版本**: v1.1.4
**目标版本**: v1.1.5
**更新日期**: 2025-11-12

---

## 📋 更新说明

由于PRD文件可能被其他进程占用，此补丁文档包含了所有需要应用到PRD的更新内容。请在PRD文件可编辑时手动应用这些更新，或使用此补丁文件作为参考。

---

## ✏️ 更新 1：版本号和最后更新日期（第3-5行）

**原内容**:
```markdown
**文档版本**: v1.1.4 (艾宾浩斯复习系统设计补全版)
**创建日期**: 2025-01-15
**最后更新**: 2025-11-11 (**NEW**: 艾宾浩斯复习系统设计补全 - FR3扩展+Epic 14调整)
```

**替换为**:
```markdown
**文档版本**: v1.1.5 (智能并行处理UI需求补全版)
**创建日期**: 2025-01-15
**最后更新**: 2025-11-12 (**NEW**: 智能并行处理UI需求补全 - FR2.1新增+Epic 11/13扩展)
```

---

## ✏️ 更新 2：新增v1.1.5变更说明（在第8行之前插入）

**插入位置**: 第8行之前（"## ⚠️ v1.1.4 艾宾浩斯复习系统设计补全"之前）

**插入内容**:
```markdown
## ⚠️ v1.1.5 智能并行处理UI需求补全 (2025-11-12) **必读**

**核心变更**: 新增FR2.1（智能并行处理UI），扩展Epic 13（Story 13.8）和Epic 11（Story 11.6），暴露Epic 10后端实现

**新增内容**:
1. **FR2.1 智能并行处理UI**: Canvas工具栏"智能批量处理"按钮，4步交互流程（分组预览→执行→进度监控→结果展示）
2. **Story 13.8 UI实现**: 7天工作量，5个Task（工具栏按钮、分组预览模态框、实时进度、结果预览、错误处理）
3. **Story 11.6 API端点**: 4个REST API + 1个WebSocket，集成AsyncExecutionEngine和智能调度器
4. **Epic影响**: Epic 13 (7→8 Stories), Epic 11 (5→6 Stories), 总时间+1周

**技术基础**: Epic 10的完整后端实现（1400+行代码）已验证，8倍性能提升，TF-IDF+K-Means智能分组

**优先级**: Must Have - P0（后端已实现，只需UI暴露）

**相关文档**: `docs/SPRINT_CHANGE_PROPOSAL_SCP-001_智能并行处理UI需求补全.md`

---
```

---

## ✏️ 更新 3：新增FR2.1需求（在第262-264行之间插入）

**插入位置**: 第262行之后，第264行之前（在"---"和"#### FR3: 艾宾浩斯复习提醒系统"之间）

**插入内容**:

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
│   优先级: High                             │
│                                            │
│ 🔍 Group 2: 复杂概念澄清 (4节点)            │
│   推荐Agent: clarification-path            │
│   优先级: High                             │
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
│    └─ 充分条件 vs 必要条件.md (2.8KB)       │
│                                            │
│ ⏳ Group 2 (clarification-path): 进行中 (2/4)│
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
│                                            │
│ [ 查看错误日志 ] [ 关闭 ]                   │
└────────────────────────────────────────────┘
```

**验收标准**:
- ✅ Canvas工具栏显示"智能批量处理"按钮（图标：⚡）
- ✅ 点击按钮触发智能分组分析（<3秒完成）
- ✅ 分组预览模态框正确显示分组结果
- ✅ 实时进度显示（WebSocket推送，延迟<500ms）
- ✅ 完成结果预览（成功/失败统计）
- ✅ Canvas自动更新（3层结构正确）
- ✅ 错误处理完善（无黄色节点提示、Agent失败不中断其他）

**关联Epic/Story**:
- Epic 11: Story 11.6（4个REST API + 1个WebSocket）
- Epic 13: Story 13.8（UI实现，7天）

**优先级**: Must Have - P0（已有完整后端实现，只缺UI暴露）

**时间估算**: +1周（UI开发 + API集成 + E2E测试）

---
```

---

## ✏️ 更新 4：更新Epic 13 Story列表（找到Epic 13章节）

**查找**: 搜索"Epic 13: Obsidian Plugin开发"章节

**在Story列表中添加**:
```markdown
- **Story 13.8**: 智能并行处理UI实现（7天，8 Points）
  - Canvas工具栏按钮
  - 智能分组预览模态框
  - 实时进度监控模态框
  - 完成结果预览模态框
  - 错误处理和边界情况
```

---

## ✏️ 更新 5：更新Epic 11 Story列表（找到Epic 11章节）

**查找**: 搜索"Epic 11: 后端Python服务"章节

**在Story列表中添加**:
```markdown
- **Story 11.6**: 智能并行处理API端点（3天，5 Points）
  - POST /api/canvas/intelligent-parallel（智能分组分析）
  - POST /api/canvas/intelligent-parallel/confirm（任务执行确认）
  - GET /api/canvas/intelligent-parallel/status/{session_id}（状态查询）
  - WebSocket /ws/intelligent-parallel/{session_id}（实时进度推送）
```

---

## ✏️ 更新 6：更新项目统计信息（如果有总体统计章节）

**查找**: "Story总数"或"总时间"相关章节

**更新**:
- Story总数: 55 → 57
- 开发时间: 12周 → 13周
- Epic 11 Story数: 5 → 6
- Epic 13 Story数: 7 → 8
- API端点数: 20 → 25（+4 REST API + 1 WebSocket）

---

## ✏️ 更新 7：Changelog章节（通常在文档末尾）

**查找**: "## 版本历史"或"## Changelog"章节

**在最顶部插入**:
```markdown
### v1.1.5 (2025-11-12)
- 🆕 新增FR2.1: 智能并行处理UI（Must Have - P0）
- 📝 新增Story 13.8: 智能并行处理UI实现（7天，8 Points）
- 📝 新增Story 11.6: 智能并行处理API端点（3天，5 Points）
- ⏱️ 时间线更新: +1周（总计13周）
- 📊 Story总数: 55 → 57
- 🔗 Epic 11 API端点: 20 → 25
- 📋 Epic 13 Story数: 7 → 8
- 📋 Epic 11 Story数: 5 → 6
- 🎯 暴露Epic 10的8倍性能提升到Obsidian Plugin
- 📚 新增Sprint Change Proposal: SCP-001
```

---

## 📚 补充文档

### 新增Story文档

**文件1**: `docs/stories/13.8.story.md` ✅ 已创建
- 完整的Story 13.8文档
- 5个详细Task清单
- 10个验收标准
- E2E测试计划

**文件2**: `docs/stories/11.6.story.md` ✅ 已创建
- Story 11.6简要文档
- 4个API端点规格
- WebSocket消息格式

### 新增提案文档

**文件**: `docs/SPRINT_CHANGE_PROPOSAL_SCP-001_智能并行处理UI需求补全.md` ✅ 已创建
- 完整的Sprint Change Proposal
- 8个章节详细分析
- UI Mockup（ASCII艺术）
- 风险评估和缓解策略

---

## 🔧 应用补丁的推荐步骤

### 方法1：手动复制粘贴（推荐）

1. 打开`docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
2. 按照上述7个更新点逐一应用
3. 保存文件并验证格式正确

### 方法2：使用Git Patch（如果启用Git）

```bash
# 1. 创建Git patch
git apply < PRD_v1.1.5_UPDATE_PATCH.md

# 2. 验证patch
git diff docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md

# 3. 提交
git add docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md
git commit -m "Update PRD to v1.1.5: Add FR2.1 智能并行处理UI"
```

### 方法3：使用文本编辑器的查找替换

1. 在VS Code或其他编辑器中打开PRD文件
2. 使用Ctrl+F查找每个"原内容"
3. 手动替换为"新内容"
4. 保存并验证

---

## ✅ 验证清单

应用补丁后，请验证：

- [ ] 版本号已更新为v1.1.5
- [ ] 最后更新日期为2025-11-12
- [ ] v1.1.5变更说明已插入
- [ ] FR2.1完整内容已插入（约150行）
- [ ] Epic 13 Story列表包含Story 13.8
- [ ] Epic 11 Story列表包含Story 11.6
- [ ] Story总数已更新为57
- [ ] 开发时间已更新为13周
- [ ] Changelog包含v1.1.5条目
- [ ] 所有markdown格式正确（标题层级、代码块、列表）

---

## 📞 联系方式

**补丁创建者**: PM Agent (Sarah)
**创建日期**: 2025-11-12
**相关提案**: SCP-001

如有疑问或需要协助，请参考：
- Sprint Change Proposal: `docs/SPRINT_CHANGE_PROPOSAL_SCP-001_智能并行处理UI需求补全.md`
- Story 13.8: `docs/stories/13.8.story.md`
- Story 11.6: `docs/stories/11.6.story.md`

---

**补丁版本**: v1.0
**补丁状态**: ✅ 已生成，待应用
