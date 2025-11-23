# Canvas学习系统 - 项目上下文

## 🎯 项目简介
基于Obsidian Canvas的AI辅助学习系统，使用费曼学习法，通过13个专项Sub-agents协作完成：
- 子问题拆解（3个Agent）
- 补充解释（6个Agent）
- 评分和检验（2个Agent）
- Canvas操作（1个Orchestrator + 1个工具Agent）

## 📁 项目结构
```
C:/Users/ROG/托福/
├── .claude/
│   ├── PROJECT.md (本文件) ✅
│   ├── agents/          ✅ 11个Sub-agent已创建
│   └── commands/        ✅ 自定义命令
├── canvas_utils.py      ✅ Python工具库（3层架构，~100KB）
├── requirements.txt     ✅ Python依赖
├── .gitignore           ✅ Git忽略规则
├── docs/
│   ├── project-brief.md ✅
│   ├── prd/             ✅ PRD分片
│   ├── architecture/    ✅ 架构分片（8个文档）
│   └── stories/         ✅ 26个Story文件（Epic 1-3）
├── tests/               ✅ 12个测试文件
└── 笔记库/              ✅ Canvas白板文件（.canvas）
```

## 🤖 Sub-agents架构设计（13个 - 待Dev实现）

系统设计包含13个专项Sub-agents，**架构已完成**，等待Dev阶段实现。

### 设计分类
- **主控Agent**（1个）：canvas-orchestrator
- **拆解系列**（3个）：basic-decomposition, deep-decomposition, problem-decomposition
- **解释系列**（6个）：oral-explanation, clarification-path, comparison-table, memory-anchor, four-level-explanation, example-teaching
- **评分和检验**（2个）：scoring-agent, review-verification
- **工具Agent**（1个）：canvas-operations

### 架构文档位置
完整的Agent设计和模板请查看：
- **docs/architecture/sub-agent-templates.md** - 13个Agent的完整模板
- **docs/architecture/sub-agent-calling-protocol.md** - Agent调用协议

### 实现状态
✅ **当前Agent文件状态：11/13**（已创建11个agent）

**已实现**（11个）：
- canvas-orchestrator.md ✅
- basic-decomposition.md ✅
- deep-decomposition.md ✅
- question-decomposition.md ✅
- oral-explanation.md ✅
- clarification-path.md ✅
- comparison-table.md ✅
- memory-anchor.md ✅
- four-level-explanation.md ✅
- example-teaching.md ✅
- scoring-agent.md ✅

**待实现**（2个）：
- review-verification.md ⏳（待Epic 4实现）
- canvas-operations.md ⏳（待Epic 5实现）

---

## 🎨 Canvas颜色系统
- 🔴 红色（color: "1"）：不理解/未通过
- 🟢 绿色（color: "2"）：完全理解/已通过
- 🟣 紫色（color: "3"）：似懂非懂/待检验
- 🟡 黄色（color: "6"）：个人理解输出区

## 📋 在检验白板上使用Agent

检验白板是带有初始框架的动态学习白板，支持所有Agent操作。

### 工作流示例

**场景**：在检验白板上拆解问题

```
1. 打开检验白板：离散数学-检验白板-20250115.canvas
2. 选择一个红色问题节点
3. 调用basic-decomposition Agent
4. 系统在检验白板上添加子问题节点
5. 继续在黄色节点填写理解
6. 调用scoring-agent评分
7. 根据评分结果决定是否继续拆解或添加解释
8. 重复上述过程，检验白板逐渐复杂化
```

### 检验白板 vs 原白板

| 操作类型 | 原白板 | 检验白板 |
|---------|-------|---------|
| 调用拆解Agent | ✅ | ✅ |
| 调用评分Agent | ✅ | ✅ |
| 调用补充解释Agent | ✅ | ✅ |
| 在Obsidian中编辑 | ✅ | ✅ |
| 添加自定义节点 | ✅ | ✅ |

**技术上没有区别**：所有Canvas操作对检验白板完全通用。

**使用上的建议**：
- 原白板：随时调用解释Agent，有辅助的学习
- 检验白板：先尝试自己输出，暴露盲区后再调用Agent

**检验白板的核心理念**：
> "检验白板是一张带有初始框架的空白费曼学习画布，用户在这张画布上尝试从头复现知识体系，在复现过程中暴露理解盲区。"

### 持续扩展学习循环

检验白板支持**无限次迭代扩展**，通过8步学习循环，从简单的问题列表逐渐生长为复杂的知识网络。

**8步学习循环**：
1. **填写个人理解** → 在黄色节点输出理解（不看资料）
2. **发现不足** → 识别理解不足的地方
3. **继续拆解** → 对不懂的问题调用拆解Agent
4. **补充解释** → 调用解释Agent获取帮助
5. **评分验证** → 调用scoring-agent检验理解
6. **颜色流转** → 红色→紫色→绿色（根据评分）
7. **添加自己的节点** → 补充原创理解
8. **构建完整知识网络** → 重复循环，白板逐渐复杂化

**常见场景推荐流程**：

| 场景 | 症状 | 推荐Agent | 目标 |
|------|------|----------|------|
| 完全不懂 | 无法输出任何内容 | basic-decomposition | 拆解降难度 |
| 似懂非懂（紫色） | 能说大概但不准确 | clarification-path | 深度理解 |
| 易混淆概念 | 与其他概念混淆 | comparison-table | 结构化对比 |
| 需要记忆 | 理解了但记不住 | memory-anchor | 生动类比 |
| 需要练习 | 缺少实际应用 | example-teaching | 例题巩固 |

**何时停止迭代**：

建议在满足以下**至少3个**条件时停止：
- ✅ 绿色占比 ≥ 80%（80%以上问题已完全理解）
- ✅ 节点数量接近原白板的50-70%
- ✅ 至少生成3个解释文档（file节点）
- ✅ 至少添加2个原创节点（个人理解）
- ✅ 无红色节点（没有完全不懂的问题）

**避免过度迭代**：
- ⚠️ 不追求100%绿色（80-90%即可）
- ⚠️ 不无限添加节点（50-70%原白板复杂度即可）
- ⚠️ 理解>记忆（关注理解深度，不过度完美主义）

**完整指南**: 详见 `docs/review-canvas-iterative-workflow.md`（完整的8步循环、决策树、真实案例）

## 📐 技术架构概览
- **3层Python架构**：CanvasJSONOperator → CanvasBusinessLogic → CanvasOrchestrator
- **v1.1布局算法**：黄色节点在问题正下方（垂直对齐）
- **Sub-agent调用**：使用自然语言调用（非Task()函数）

详见：docs/architecture/

---

## 📚 关键文档位置
- **项目简报**: docs/project-brief.md ✅
- **PRD**: docs/prd/ ✅
- **架构文档**: docs/architecture/ ✅ (8个文档)
- **用户故事**: docs/stories/ (SM将生成)

---

## 🔧 开发工作流（BMad-Method）

**当前阶段：准备移交SM**

完整流程：Analyst ✅ → PM ✅ → Architect ✅ → SM（下一步） → Dev → QA

### 下一步：移交给Scrum Master
```bash
/BMad-create-next-story
```

### 预计时间表
- SM阶段：2-3天
- Dev阶段（Epic 1）：5-7天
- 完整系统：16-22天

---

## 📝 当前状态
- **日期**: 2025-10-15
- **当前阶段**: Dev开发中（Epic 3完成，进行中）
- **已完成Agent数**: 11/13（84.6%完成）
- **已完成Story数**: 26/26 for Epic 1-3
- **文档完整性**: ✅ 100%
- **代码实现进度**: ~85%（核心功能已实现，待Epic 4-5）

---

**状态：Epic 1-3已完成并通过QA审查，Epic 4-5待开发**
