# 🎯 Section 1: 项目分析

### 1.1 现有项目概览

#### 系统架构 (当前)

```
用户在Obsidian中打开Canvas
    ↓
切换到Claude Code窗口
    ↓
手动输入命令: "@离散数学.canvas 基础拆解'逆否命题'"
    ↓
Claude Code调用Task tool → 调用12个Sub-agent
    ↓
Sub-agent返回JSON结果
    ↓
canvas_utils.py写入Canvas文件
    ↓
用户切回Obsidian查看结果
```

**痛点**:
- ❌ 需要频繁切换窗口 (Obsidian ↔ Claude Code)
- ❌ 命令行输入门槛高,需要记忆语法
- ❌ 无法实时看到Agent执行进度
- ❌ 缺少今日复习提醒功能
- ❌ 检验白板无法追踪原白板节点还原进度
- ❌ 跨Canvas学习需手动记忆关联关系

#### 核心资产

| 组件 | 规模 | 状态 | 价值 |
|------|------|------|------|
| canvas_utils.py | ~150KB, 3层架构 | ✅ 稳定 | 核心业务逻辑 |
| 12个Sub-agent | `.claude/agents/*.md` | ✅ 验证可用 | Agent定义 |
| Epic 10.2异步引擎 | 8倍性能提升 | ✅ 完成 | 性能优势 |
| 测试套件 | 360+测试, 99.2%通过率 | ✅ 高质量 | 质量保证 |
| Graphiti集成 | Neo4j + KnowledgeGraphLayer | ✅ 完成 | 知识图谱基础 |
| EbbinghausReviewSystem | Py-FSRS算法 | ✅ 已实现 | 复习算法 |

**保留策略**: 所有核心资产100%保留,仅迁移接口层

---

### 1.2 迁移范围评估

#### 需要迁移的部分

```
❌ CLI命令接口               → ✅ Obsidian Plugin命令
❌ Claude Code Task调用      → ✅ LangGraph Supervisor调度
❌ 手动切换窗口              → ✅ Obsidian内原生操作
```

#### 需要保留的部分

```
✅ canvas_utils.py (3层架构)    → FastAPI后端继续使用
✅ 12个Agent定义               → LangGraph节点封装
✅ Epic 10.2异步执行引擎       → 性能优势保留
✅ Graphiti知识图谱            → 跨Canvas关联基础
✅ EbbinghausReviewSystem      → 复习系统核心
```

#### 需要新增的功能

```
🆕 艾宾浩斯复习面板            → 今日复习提醒
🆕 检验白板进度追踪            → 原白板节点还原状态
🆕 跨Canvas关联UI              → 手动配置教材-习题关联
🆕 实时进度显示                → WebSocket推送Agent状态
```

---
