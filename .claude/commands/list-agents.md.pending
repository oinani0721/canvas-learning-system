---
name: list-agents
description: List all available Sub-agents in Canvas Learning System
---

# Canvas学习系统 - Sub-agents清单

## 主控Agent（1个）

### canvas-orchestrator
- **文件**: .claude/agents/canvas-orchestrator.md
- **职责**: 解析用户指令，调度Sub-agents，更新Canvas
- **调用**: 用户直接输入自然语言指令

---

## 拆解系列（3个）

### 1. basic-decomposition
- **文件**: .claude/agents/basic-decomposition.md
- **场景**: 难以理解的材料（大脑宕机）
- **输出**: 3-7个基础引导性问题
- **调用示例**: `"Use the basic-decomposition subagent to decompose the material about '逆否命题' into simple questions"`

### 2. deep-decomposition
- **文件**: .claude/agents/deep-decomposition.md
- **场景**: 似懂非懂的材料（需要检验理解）
- **输出**: 3-5个深度检验性问题

### 3. problem-decomposition
- **文件**: .claude/agents/problem-decomposition.md
- **场景**: 解题卡壳或思路跑偏
- **输出**: 针对性突破型问题

---

## 解释系列（6个）

### 4. oral-explanation
- **文件**: .claude/agents/oral-explanation.md
- **场景**: 材料一开始就难以理解
- **输出**: 800-1200字口语化教授讲解（Markdown笔记）

### 5. clarification-path
- **文件**: .claude/agents/clarification-path.md
- **输出**: 4步澄清路径（共约400字）

### 6. comparison-table
- **文件**: .claude/agents/comparison-table.md
- **输出**: 结构化对比表（Markdown表格）

### 7. memory-anchor
- **文件**: .claude/agents/memory-anchor.md
- **输出**: 比喻 + 故事 + 押韵口诀

### 8. four-level-explanation
- **文件**: .claude/agents/four-level-explanation.md
- **输出**: 新手/进阶/专家/创新 四层次解答

### 9. example-teaching
- **文件**: .claude/agents/example-teaching.md
- **场景**: 面对题目完全无思路
- **输出**: 完整例题教学（7个部分）

---

## 评分和检验（2个）

### 10. scoring-agent
- **文件**: .claude/agents/scoring-agent.md
- **职责**: 评估黄色节点的个人理解质量
- **评分标准**: 准确性、形象性、完整性、原创性（各25分）
- **通过标准**: ≥80分 → 节点变绿

### 11. review-verification
- **文件**: .claude/agents/review-verification.md
- **职责**: 无纸化回顾检验
- **输出**: 新的Canvas检验白板文件

---

## 工具Agent（1个）

### 12. canvas-operations
- **文件**: .claude/agents/canvas-operations.md
- **职责**: Canvas底层操作（节点CRUD、颜色修改、边连接）
- **调用**: 其他Agent通过canvas_utils.py间接调用

---

## Agent统计
- 总计: 13个Sub-agents
- 已实现: 0/13（等待Dev阶段实现）
- 架构设计状态: ✅ 完成

## 调用关系图
```
用户输入
  ↓
canvas-orchestrator（主控）
  ↓
  ├→ basic-decomposition / deep-decomposition / problem-decomposition
  ├→ oral-explanation / clarification-path / comparison-table /
  │  memory-anchor / four-level-explanation / example-teaching
  ├→ scoring-agent
  └→ review-verification
      ↓
    canvas-operations (通过canvas_utils.py)
```

---

**查看特定Agent的详细信息**:
```bash
cat .claude/agents/[agent-name].md
```

**检查Agent是否存在**:
```bash
ls .claude/agents/
```
