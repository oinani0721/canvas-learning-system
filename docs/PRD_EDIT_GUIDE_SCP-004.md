# PRD编辑指南 - SCP-004实施

**文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
**目标版本**: v1.1.8
**编辑数量**: 5处
**备份位置**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md.backup_*`

---

## ⚠️ 执行前准备

1. **关闭Obsidian** (如果PRD文件正在被打开)
2. **确认备份已创建** (检查backup文件存在)
3. **使用文本编辑器打开PRD文件** (VS Code, Notepad++等)

---

## 📝 Edit 1: 更新文档版本号 (Line 3-5)

**位置**: 文件开头，Line 3-5

**查找这段文字**:
```markdown
**文档版本**: v1.1.7 (3层记忆技术栈勘误修正版)
**创建日期**: 2025-01-15
**最后更新**: 2025-11-12 (**NEW**: 3层记忆技术栈勘误修正 - 确保100%代码一致性)
```

**替换为**:
```markdown
**文档版本**: v1.1.8 (单节点智能分析UI + PRD文档修正版)
**创建日期**: 2025-01-15
**最后更新**: 2025-11-12 (**NEW**: 单节点智能分析UI + Epic 11/13 Story序列修正)
```

---

## 📝 Edit 2: 新增v1.1.8变更日志节 (在Line 7之前插入)

**位置**: 在`## ⚠️ v1.1.7`这一行之前插入

**插入以下完整内容**:

```markdown

## ⚠️ v1.1.8 单节点智能分析UI + PRD文档修正 (2025-11-12) **必读**

**核心变更**:
1. 新增FR2.2（单节点智能分析UI），基于Story 2.9智能推荐引擎
2. 修正Epic 11和Epic 13的Story序列列表（v1.1.5/v1.1.6更新时的遗漏）

**新增内容**:
1. **FR2.2 单节点智能分析UI**: 右键黄色节点→智能评分→推荐确认→执行Agent
   - 用户场景：检验白板填写理解后，右键触发智能分析
   - 交互流程：自动评分（4维）→展示推荐Agent及理由→用户确认→执行
   - UI组件：右键菜单项 + 推荐确认模态框
2. **Story 11.9 API端点**: POST `/api/analyze-single-node`，集成Story 2.9逻辑
   - 请求：`{node_id, node_content, canvas_path}`
   - 响应：`{score_result, recommendation, reasoning, options}`
   - 响应时间：<2秒
3. **Story 13.9 UI实现**: 4-5天工作量
   - Task 1: 右键菜单扩展（"智能分析"菜单项）
   - Task 2: 推荐确认模态框UI（评分展示、维度分析、推荐理由）
   - Task 3: API集成与Agent执行
   - Task 4: Canvas更新与结果展示
   - Task 5: 错误处理与用户提示
4. **Epic影响**:
   - Epic 11: 8→9 Stories (+Story 11.9)
   - Epic 13: 8→9 Stories (+Story 13.9)
   - 总时间: +0.9-1.4周 (MVP 10.5-13.5周 → 11.4-14.9周)

**文档修正**:
1. **Epic 11 Story序列修正** (Line 3863-3869):
   - Story 11.6: 明确为"智能批量处理API"（v1.1.5定义，但序列未更新）
   - Story 11.8: 原"Docker Compose"重新编号（原11.6）
2. **Epic 13 Story序列修正** (Line 4107-4114):
   - Story 13.8: 补充"智能批量处理UI"（v1.1.5新增，但序列未记录）

**技术基础**:
- Story 2.9智能推荐引擎（已完成，100%测试通过）
- Epic 10异步并发架构（已验证，8倍性能提升）

**优先级**: Must Have - P0（与FR2.1批量处理同级，完整智能决策UI闭环）

**对比FR2.1批量处理**:
| 特性 | FR2.1批量处理 | FR2.2单节点分析 |
|------|--------------|----------------|
| 触发方式 | 工具栏按钮 | 右键单个黄色节点 |
| 处理对象 | 所有黄色节点（批量） | 当前选中的单个节点 |
| 智能推荐 | 基于内容关键词分组 | 基于4维评分结果推荐 |
| 推荐逻辑 | TF-IDF+K-Means聚类 | Story 2.9智能建议引擎 |
| 用户确认 | 分组预览后确认 | 推荐Agent后确认 |

**相关文档**: `docs/SPRINT_CHANGE_PROPOSAL_SCP-004_单节点智能分析UI.md`

---

```

---

## 📝 Edit 3: 新增FR2.2 (搜索"#### FR3:"，在其之前插入)

**位置**: 搜索`#### FR3: 艾宾浩斯复习提醒系统`，在这一行之前插入

**插入以下完整内容**:

```markdown

#### FR2.2: 单节点智能分析UI (Must Have - P0)

**背景**: Story 2.9智能推荐引擎（4维评分后Agent推荐）已在canvas-orchestrator中实现并通过100%测试，但仅能通过CLI使用。用户在检验白板填写理解后，需要UI化的智能决策流程。

**描述**: 用户右键点击单个黄色节点，触发"智能分析"功能，系统自动评分（4维）并推荐下一步Agent操作，用户确认后执行。

**用户故事**:
```
作为学习者
我希望在检验白板填写理解后，右键点击黄色节点就能看到智能评分和推荐的下一步操作
以便快速决策是继续拆解、补充解释还是进入检验阶段
而不需要切换到CLI手动输入命令
```

**核心能力**:
- ✅ **4维评分**: 准确性(Accuracy)、形象性(Imagery)、完整性(Completeness)、原创性(Originality)
- ✅ **档位分级**:
  - ≥80分: 推荐进入检验阶段或继续深化
  - 60-79分: 维度导向推荐（准确性弱→clarification-path，形象性弱→memory-anchor）
  - <60分: 推荐最详细解释Agent（clarification-path优先）
- ✅ **维度导向推荐**:
  - 准确性低 → clarification-path, oral-explanation
  - 形象性低 → memory-anchor, comparison-table
  - 完整性低 → clarification-path, four-level-explanation
  - 原创性低 → oral-explanation, memory-anchor
- ✅ **推荐确认模式**: 展示评分、维度分析、推荐理由，用户确认后执行

**UI交互流程**:

**Step 1: 右键菜单触发**
```
用户操作: 右键点击黄色节点
┌─────────────────────────────┐
│ Canvas右键菜单               │
├─────────────────────────────┤
│ 🎯 基础拆解                  │
│ 🔍 深度拆解                  │
│ 📊 评分                      │
│ 📝 补充解释                  │
│ ────────────────            │
│ ⚡ 智能分析 ⬅️ 新增          │
│ ────────────────            │
│ 📋 复制                      │
│ 🗑️ 删除                     │
└─────────────────────────────┘
```

**Step 2: 推荐确认模态框**
```
点击"智能分析"后，调用API 11.9，展示推荐确认模态框：

┌────────────────────────────────────────────┐
│ 💡 智能分析结果                             │
├────────────────────────────────────────────┤
│ 您的理解得分: 68分                          │
│ 基本正确但存在盲区                          │
│                                            │
│ 📊 维度分析:                               │
│ • 准确性: 18/25 ⚠️ (最弱)                  │
│ • 形象性: 21/25 ✅                         │
│ • 完整性: 17/25                            │
│ • 原创性: 12/25                            │
│                                            │
│ 🎯 推荐操作:                               │
│ ○ A. 使用 clarification-path Agent         │
│      用详细解释纠正理解偏差                 │
│ ○ B. 继续原计划操作                        │
│ ○ C. 取消操作                              │
│                                            │
│ 💬 推荐理由:                               │
│ 您的准确性得分18/25，用详细解释纠正理解偏差 │
│ 能帮助您提升这个维度。                      │
│                                            │
│ [ 确认执行 ] [ 取消 ]                      │
└────────────────────────────────────────────┘
```

**Step 3: 执行Agent并生成结果**
```
用户点击"确认执行"后：
1. 关闭模态框
2. 调用选中的Agent（例如clarification-path）
3. 生成解释文档（.md文件）
4. Canvas自动更新（3层结构：黄色节点→蓝色TEXT节点→File节点）
5. 显示成功通知："已生成澄清路径文档"
```

**验收标准**:
- ✅ 右键黄色节点显示"智能分析"菜单项（图标：⚡）
- ✅ 点击后自动调用API 11.9进行评分（<2秒响应）
- ✅ 推荐确认模态框正确显示评分和维度分析
- ✅ 推荐Agent符合Story 2.9的档位分级规则
- ✅ 用户确认后正确执行推荐Agent
- ✅ Canvas正确更新（3层结构：黄色→蓝色TEXT→File）
- ✅ 错误处理完善（节点不存在、评分失败、Agent执行失败等）
- ✅ 性能达标：评分<2秒，Agent执行<5秒

**关联Epic/Story**:
- Epic 11: Story 11.9（单节点智能分析API，3-4天）
- Epic 13: Story 13.9（单节点智能分析UI，4-5天）
- 依赖: Story 2.9（智能推荐引擎，已完成）

**优先级**: Must Have - P0（与FR2.1批量处理同级，完整智能决策UI闭环）

**时间估算**: +0.9-1.4周（API 3-4天 + UI 4-5天 + 测试2天）

**技术基础**:
- Story 2.9的`generate_enhanced_intelligent_suggestion()`函数（已验证）
- Epic 10的异步并发架构（已验证，8倍性能提升）
- Story 13.5的右键菜单基础（待实施）

---

```

---

## 📝 Edit 4: 修正Epic 11 Story序列 (Line 3863-3869区域)

**位置**: 搜索`### Epic 11: FastAPI后端基础架构搭建`

**查找这段文字**:
```markdown
### Epic 11: FastAPI后端基础架构搭建

**Story序列**:
- Story 11.1: FastAPI项目初始化和基础配置
- Story 11.2: canvas_utils.py集成到FastAPI
- Story 11.3: 核心API endpoints (拆解、评分、解释)
- Story 11.4: 艾宾浩斯复习系统API
- Story 11.5: 跨Canvas关联API
- Story 11.6: Docker Compose环境配置
```

**替换为**:
```markdown
### Epic 11: FastAPI后端基础架构搭建

**Story序列**:
- Story 11.1: FastAPI项目初始化和基础配置
- Story 11.2: canvas_utils.py集成到FastAPI
- Story 11.3: 核心API endpoints (拆解、评分、解释)
- Story 11.4: 艾宾浩斯复习系统API
- Story 11.5: 跨Canvas关联API
- Story 11.6: 智能批量处理API (v1.1.5新增 - 4个REST API + 1个WebSocket)
- Story 11.7: 3层记忆查询API (v1.1.6新增)
- Story 11.8: Docker Compose环境配置 (原Story 11.6重新编号)
- Story 11.9: 单节点智能分析API (v1.1.8新增 - 本次SCP-004)
```

---

## 📝 Edit 5: 修正Epic 13 Story序列 (Line 4107-4114区域)

**位置**: 搜索`### Epic 13: Obsidian Plugin核心功能`

**查找这段文字**:
```markdown
### Epic 13: Obsidian Plugin核心功能

**Story序列**:
- Story 13.1: Plugin项目初始化
- Story 13.2: Canvas API集成
- Story 13.3: API客户端实现
- Story 13.4: 核心命令 (拆解、评分、解释)
- Story 13.5: 右键菜单和快捷键
- Story 13.6: 设置面板
- Story 13.7: 错误处理
```

**替换为**:
```markdown
### Epic 13: Obsidian Plugin核心功能

**Story序列**:
- Story 13.1: Plugin项目初始化
- Story 13.2: Canvas API集成
- Story 13.3: API客户端实现
- Story 13.4: 核心命令 (拆解、评分、解释)
- Story 13.5: 右键菜单和快捷键
- Story 13.6: 设置面板
- Story 13.7: 错误处理
- Story 13.8: 智能批量处理UI (v1.1.5新增 - 7天)
- Story 13.9: 单节点智能分析UI (v1.1.8新增 - 4-5天，本次SCP-004)
```

---

## ✅ 验证清单

完成所有编辑后，请验证：

- [ ] **Edit 1**: 文档版本号已更新为v1.1.8
- [ ] **Edit 2**: v1.1.8变更日志节已添加（在v1.1.7之前）
- [ ] **Edit 3**: FR2.2已添加（在FR3之前）
- [ ] **Edit 4**: Epic 11 Story序列已修正（包含Story 11.6-11.9）
- [ ] **Edit 5**: Epic 13 Story序列已修正（包含Story 13.8-13.9）
- [ ] 文件保存成功
- [ ] 在Obsidian中重新打开PRD，检查格式正确

---

## 🔄 如果编辑失败

如果手动编辑过程中遇到问题：

1. **恢复备份**:
   ```bash
   cp docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md.backup_* docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md
   ```

2. **重新开始**: 从Edit 1重新执行

3. **寻求帮助**: 查看`docs/SPRINT_CHANGE_PROPOSAL_SCP-004_单节点智能分析UI.md`获取详细信息

---

**编辑指南创建时间**: 2025-11-12
**SCP编号**: SCP-004
**状态**: Ready for Manual Execution
