# Canvas Learning System - PRD核心文档

**版本**: 1.0 (从PRD v1.1.8提取)
**创建日期**: 2025-11-21
**内容**: Section 1 (项目分析) + Section 5-8 (风险/成功/交付/验收)

---

## 🎯 Section 1: 项目分析

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

## 🔍 Section 1.X: 技术验证协议 (Mandatory Technical Verification Protocol)

### 1.X.1 核心原则

#### "Zero Hallucination Policy - 零幻觉政策"

本项目对技术实现采用**学术论文级别的引用标准**。任何技术细节（API调用、参数、返回值、配置项）都必须可追溯到官方文档，禁止基于"常识"或"经验"进行假设性实现。

**违反此协议的Story将被标记为FAILED，必须重做。**

#### 质量目标

| 质量维度 | 目标 | 衡量方式 | 负责人 |
|---------|------|---------|--------|
| **Bug率（API误用）** | ↓50% | Epic 11-16 Bug追踪 | QA Agent |
| **返工率（技术假设错误）** | ↓70% | Story重做次数统计 | PM Agent |
| **Code Review效率** | ↑30% | Review时间对比 | SM Agent |
| **代码可维护性** | ↑40% | 文档引用注释覆盖率 | Dev Agent |

---

### 1.X.2 技术栈文档访问矩阵

| 技术栈 | 访问方式 | Library ID / Skill Path | 代码片段数 | Epic依赖 |
|--------|---------|------------------------|-----------|---------|
| **FastAPI** | Context7 MCP | `/websites/fastapi_tiangolo` | 22,734 | Epic 11 |
| **Neo4j Cypher** | Context7 MCP | `/websites/neo4j_cypher-manual_25` | 2,032 | Epic 15-16 |
| **Neo4j Operations** | Context7 MCP | `/websites/neo4j_operations-manual-current` | 4,940 | Epic 15-16 |
| **LangGraph** | Local Skill | `@langgraph` | 952页完整文档 | Epic 12 |
| **Graphiti** | Local Skill | `@graphiti` | 完整框架文档 | Epic 12 |
| **Obsidian Canvas** | Local Skill | `@obsidian-canvas` | Canvas API文档 | Epic 13 |

---

### 1.X.3 强制性查询触发点

#### 🔴 Level 1: SM Agent编写Story时 (CRITICAL)

**触发条件**: 编写任何包含技术实现细节的Story

**强制操作**:
1. **识别技术栈**: 列出Story涉及的所有技术
2. **查询官方文档**: 使用Context7查询或激活本地Skill
3. **在Story中引用**: 添加"技术验证"section

#### 🔴 Level 2: Dev Agent开发实现时 (CRITICAL)

**触发条件**: 编写任何包含框架API调用的代码

**UltraThink检查点**:
```
🤔 UltraThink检查点：
1. 我是否100%确定这个API的用法？
2. 参数名称、类型、默认值是否正确？
3. 返回值类型是否符合框架要求？
4. 是否有更好的官方推荐写法？
5. 这个写法是"创新"还是"标准"？
```

**强制暂停点**: 如果任何一个问题的答案是"不确定"，**必须立即停止编码，先查询文档**。

#### 🟡 Level 3: Code Review时 (IMPORTANT)

**Code Review检查清单**:
- [ ] Story包含"技术验证"section且记录完整
- [ ] 代码中所有框架API调用均与官方文档一致
- [ ] 关键代码行包含文档来源注释
- [ ] 无明显的"凭经验"或"创新"写法
- [ ] 参数类型、默认值、返回值均正确

---

### 1.X.4 Definition of Done (DoD) 更新

**所有技术Story的DoD新增以下条目**:

```markdown
## Definition of Done (Enhanced)

### 技术验证要求 (MANDATORY) ⚠️
- [ ] **文档查询记录完整**: Story包含完整的"技术验证"section
- [ ] **API调用已验证**: 所有框架API调用均通过Context7/Skill确认
- [ ] **参数类型正确**: 所有函数参数、返回值类型与官方文档一致
- [ ] **配置项已确认**: 所有配置项符合官方推荐
- [ ] **代码注释包含引用**: 关键代码行包含文档来源注释

### 传统DoD (保留)
- [ ] 代码通过所有单元测试
- [ ] 代码通过集成测试
- [ ] 代码符合项目编码规范
- [ ] PR已通过Code Review
- [ ] 文档已更新
- [ ] 无已知的Critical/High severity bugs
```

---

### 1.X.5 违反协议的处理流程

| 违规类型 | 严重程度 | 处理措施 |
|---------|---------|---------|
| **Story缺少"技术验证"section** | 🔴 Critical | Story标记为BLOCKED |
| **代码中API调用与官方文档不符** | 🔴 Critical | PR被拒绝 |
| **使用了未经验证的"创新"写法** | 🟡 High | 必须提供文档支持 |
| **文档查询记录不完整** | 🟡 Medium | 要求补充记录 |
| **代码注释缺少文档引用** | 🟢 Low | Code Review时补充 |

---

### 1.X.6 质量监控与持续改进

#### 监控指标

| 指标 | 目标值 | 监控周期 | 责任人 |
|------|--------|---------|--------|
| **Story技术验证完整率** | 100% | 每个Story | SM Agent |
| **API误用Bug数** | <2/Epic | Epic结束时 | QA Agent |
| **文档引用覆盖率** | >80% | Code Review时 | Dev Agent |
| **返工Story数** | <1/Epic | Epic结束时 | PM Agent |

---

## ⚠️ Section 5: 风险评估

### 技术风险

| 风险 | 影响 | 可能性 | 缓解策略 |
|------|------|--------|---------|
| LangGraph性能不如直接调用 | 高 | 中 | 性能基准测试,保留Epic 10.2优化 |
| Obsidian API限制 | 高 | 低 | POC验证,备用Vault文件操作 |
| Docker配置复杂 | 中 | 中 | 详细文档,自动化脚本 |
| 跨平台兼容性 | 中 | 中 | CI/CD多平台测试 |

### 迁移风险

| 风险 | 影响 | 可能性 | 缓解策略 |
|------|------|--------|---------|
| 用户数据丢失 | 极高 | 低 | Epic 18备份机制,双系统验证 |
| 功能回退 | 高 | 中 | 完整测试,保留CLI fallback |
| 用户学习成本高 | 中 | 高 | 详细文档,视频教程 |

### 回滚计划

**触发条件**:
- 数据丢失或损坏
- 严重性能退化 (>50%)
- 关键功能失效

**回滚步骤**:
1. 停止FastAPI和Neo4j服务
2. 恢复备份数据
3. 切换回CLI命令
4. 通知用户

---

## 📈 Section 6: 成功指标

### 关键指标 (KPI)

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| 功能迁移完整性 | 100% (12个Agent全部可用) | 功能清单验证 |
| 性能不退化 | ≥现有系统 | 性能基准测试 |
| 用户满意度 | ≥80% | 用户调研 |
| 窗口切换次数 | 0 (完全在Obsidian内操作) | 用户观察 |
| 数据零丢失 | 100% | 迁移验证 |

---

## 📅 Section 7: 交付计划

### Phase 1: MVP (8-11周)

**交付内容**:
- ✅ Epic 11: FastAPI后端
- ✅ Epic 12: LangGraph编排 + 三层记忆 + Agentic RAG
- ✅ Epic 13: Plugin核心功能
- ✅ Story 14.1-14.3: 复习面板核心

**验收标准**:
- 用户可在Obsidian内完成所有12个Agent操作
- 性能不低于现有系统
- 今日复习功能可用

### Phase 2: 完整功能 (18-22周)

**交付内容**:
- ✅ Epic 14: 艾宾浩斯复习系统完整功能
- ✅ Epic 15: 进度追踪
- ✅ Epic 16: 跨Canvas关联
- ✅ Epic 18: 数据迁移

---

## ✅ Section 8: 验收标准

### 最终验收清单

- [ ] 所有12个Agent功能100%可用
- [ ] Epic 10.2性能优势保留 (8倍提升)
- [ ] 艾宾浩斯复习面板正常工作
- [ ] 检验白板进度追踪准确显示
- [ ] 跨Canvas关联UI可配置
- [ ] 测试覆盖率 ≥85%
- [ ] 文档完整性 100%
- [ ] 用户满意度 ≥80%
- [ ] 数据迁移零丢失
- [ ] 回滚机制验证通过

---

## 📚 附录

### A. 参考文档

- Canvas Learning System CLAUDE.md
- Epic 10.2 Completion Report
- Story 4.9 (sourceNodeId元数据)
- Story 6.1 (Graphiti知识图谱)
- LangGraph官方文档 (Context7)

### B. 术语表

- **LangGraph**: LangChain的图编排框架,用于构建多Agent系统
- **Supervisor Pattern**: 中央路由器模式,一个Supervisor调度多个Worker Agent
- **Graphiti**: 时间感知知识图谱框架
- **Py-FSRS**: Python实现的FSRS间隔重复算法
- **FileLock**: 跨平台文件锁机制,防止并发写入冲突
- **create_react_agent**: LangGraph的工具配备Agent创建函数
- **Tool-Equipped Agent**: 配备工具的Agent,可直接调用函数完成任务
- **WriteHistory**: 写入历史记录系统,支持回滚操作

### C. 相关文档

- **完整PRD**: `CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
- **Epic 12统一规划**: `epics/EPIC-12-Unified.md`
- **ADR决策记录**: `../architecture/decisions/`

---

**文档结束**

**提取来源**: PRD v1.1.8
**提取日期**: 2025-11-21
