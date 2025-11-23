# PRD技术真实性修正清单

**创建日期**: 2025-11-12
**目标文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
**PRD版本**: v1.1.6
**验证依据**: Canvas系统实际代码深度审计

---

## 📋 修正概览

| 修正项 | 位置 | 紧急程度 | 影响范围 |
|--------|------|---------|---------|
| Temporal Memory技术栈 | Lines 12, 420-426 | 🔴 Critical | Epic 11/12/14 |
| Semantic Memory技术栈 | Lines 12, 428-430 | 🔴 Critical | Epic 11/12/14 |
| Py-FSRS算法描述 | Lines 13, 67, 223, 435-447 | 🟡 Medium | Epic 14 |
| 架构层数 | Lines 218, 245, 多处 | 🟢 Low | 文档一致性 |

---

## 🔴 Critical修正 #1: Temporal Memory技术栈

### 位置1: Line 12 (v1.1.6更新说明)

**当前错误文本**:
```
1. **数据源单一问题**: 原系统仅依赖Canvas评分≥60作为唯一数据源 → 整合Temporal/Graphiti/Semantic三层记忆
```

**修正为**:
```
1. **数据源单一问题**: 原系统仅依赖Canvas评分≥60作为唯一数据源 → 整合Temporal(Neo4j/Graphiti)/Graphiti/Semantic(MCP+ChromaDB)三层记忆
```

**验证依据**:
- ✅ 文件: `memory_system/temporal_memory_manager.py` (480行)
- ✅ 第41-50行: `class TemporalMemoryManager:` 类定义
- ✅ 第61-64行: 使用Neo4j连接参数 (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`)
- ✅ 第97-107行: 使用 `DirectNeo4jStorage` 而非TimescaleDB
- ❌ 无TimescaleDB相关代码

---

### 位置2: Lines 420-426 (FR3数据流向图)

**当前错误文本**:
```
┌──────────────────────────────────────────────────────────────────┐
│ 数据源 (Data Sources)                                            │
├──────────────────────────────────────────────────────────────────┤
│ 1. Canvas节点评分 (≥60分) → 触发添加概念到复习队列              │
│ 2. Temporal Memory (TimescaleDB) → 学习行为数据                 │
│    - 复习频率、间隔时间、正确率趋势                             │
```

**修正为**:
```
┌──────────────────────────────────────────────────────────────────┐
│ 数据源 (Data Sources)                                            │
├──────────────────────────────────────────────────────────────────┤
│ 1. Canvas节点评分 (≥60分) → 触发添加概念到复习队列              │
│ 2. Temporal Memory (Neo4j/Graphiti) → 学习行为数据              │
│    - 复习频率、间隔时间、正确率趋势                             │
│    - 技术栈: Neo4j图数据库 + Graphiti时序记忆封装               │
```

---

## 🔴 Critical修正 #2: Semantic Memory技术栈

### 位置1: Line 12 (已在修正#1中处理)

### 位置2: Lines 428-430 (FR3数据流向图)

**当前错误文本**:
```
│ 4. Semantic Memory (Qdrant) → 文档交互数据                      │
│    - 查阅频率、停留时间、相关文档访问模式                       │
```

**修正为**:
```
│ 4. Semantic Memory (MCP语义系统+ChromaDB) → 文档交互数据        │
│    - 查阅频率、停留时间、相关文档访问模式                       │
│    - 技术栈: MCP语义记忆服务 + ChromaDB向量数据库               │
│    - 支持模式: mcp完整模式/fallback降级模式/unavailable不可用   │
```

**验证依据**:
- ✅ 文件: `memory_system/semantic_memory_manager.py` (492行)
- ✅ 第1-14行: 类注释说明支持3种模式（mcp/fallback/unavailable）
- ✅ 第68行: 导入 `import mcp_memory_client`
- ✅ 第82-94行: 检测缺失模块（chromadb, sentence_transformers等）
- ❌ 无Qdrant相关代码

---

## 🟡 Medium修正 #3: Py-FSRS算法描述

### 位置1: Line 13 (v1.1.6更新说明)

**当前错误文本**:
```
2. **参数默认值问题**: Py-FSRS使用默认17参数（相当于模拟数据） → 从真实行为数据动态优化参数
```

**修正为**:
```
2. **算法升级计划**: 当前使用经典遗忘曲线 R(t)=e^(-t/S) → 计划升级到Py-FSRS算法（预期准确性提升20-30%）并动态优化参数
```

**验证依据**:
- ✅ 文件: `ebbinghaus_review.py` (869行)
- ✅ 第7行: 核心算法注释 `R(t) = e^(-t/S)`
- ✅ 第71-98行: `calculate_retention_rate()` 方法，使用 `math.exp(-time_elapsed_days / memory_strength)`
- ❌ 文件中无 `from fsrs import` 语句
- ⚠️ `canvas_utils.py` Line 124导入了fsrs，但未在`ebbinghaus_review.py`中使用

---

### 位置2: Line 67 (v1.1.4更新说明)

**当前错误文本**:
```
**算法升级**: 采用**Py-FSRS算法**（相比经典艾宾浩斯遗忘曲线准确性提升20-30%）
```

**修正为**:
```
**算法现状与升级计划**:
- **当前**: 使用经典艾宾浩斯遗忘曲线 R(t) = e^(-t/S)（已实现于ebbinghaus_review.py, 869行）
- **计划**: 升级到Py-FSRS算法（预期准确性提升20-30%）
```

---

### 位置3: Line 223 (Section 1.1 核心资产表)

**当前错误文本**:
```
| EbbinghausReviewSystem | Py-FSRS算法 | ✅ 已实现 | 复习算法 |
```

**修正为**:
```
| EbbinghausReviewSystem | 经典遗忘曲线 R(t)=e^(-t/S) | ✅ 已实现 (计划升级Py-FSRS) | 复习算法 |
```

---

### 位置4: Lines 435-447 (FR3数据流向图 - Py-FSRS描述)

**当前错误文本**:
```
        ┌───────────────────────────────────┐
        │ Py-FSRS算法                       │
        │ - 使用从真实行为优化的17参数      │ ← 新增: 真实参数
        │ - 计算下次复习时间                │
        └───────────────────────────────────┘
```

**修正为**:
```
        ┌───────────────────────────────────┐
        │ 复习算法系统                      │
        │ - 当前: 经典遗忘曲线 R(t)=e^(-t/S)│
        │ - 计划: Py-FSRS (优化17参数)      │ ← 升级计划
        │ - 计算下次复习时间                │
        └───────────────────────────────────┘
```

---

### 位置5: Lines 456-459 (v1.1.6关键变更说明)

**当前错误文本**:
```
**v1.1.6关键变更**:
- ✅ **100%真实数据源**: 所有数据来自实际学习行为，无模拟数据
- ✅ **3层记忆系统整合**: Temporal/Graphiti/Semantic全面接入
- ✅ **动态参数优化**: FSRS 17参数从真实行为数据中计算，非默认值
```

**修正为**:
```
**v1.1.6关键变更**:
- ✅ **100%真实数据源**: 所有数据来自实际学习行为，无模拟数据
- ✅ **3层记忆系统整合**: Temporal(Neo4j/Graphiti)/Graphiti/Semantic(MCP+ChromaDB)全面接入
- ⏳ **算法升级计划**: 从经典遗忘曲线升级到Py-FSRS算法，并实现动态参数优化
```

---

## 🟢 Low修正 #4: 架构层数描述

### 位置1: Line 218 (Section 1.1 现有项目概览)

**搜索**: `3层架构` 或 `3-layer`

**当前错误文本**: (需要搜索PRD全文找到具体位置)
```
canvas_utils.py (~150KB, 3层架构)
```

**修正为**:
```
canvas_utils.py (33,854行, 4层架构)
```

**验证依据**:
- ✅ Layer 1: `CanvasJSONOperator` (Line 6607)
- ✅ Layer 2: `CanvasBusinessLogic` (Line 8403)
- ✅ Layer 3: `CanvasOrchestrator` (Line 12467)
- ✅ Layer 4: `KnowledgeGraphLayer` (Line 14648)

---

### 位置2: 多处架构描述

**全局搜索替换**:
- 将所有 `3层架构` → `4层架构`
- 将所有 `~100KB` 或 `~150KB` → `~34,000行` (更准确的代码量描述)

---

## 📊 修正后的核心资产表 (Line 216-226)

**完整修正后的表格**:

```markdown
| 组件 | 规模 | 状态 | 价值 |
|------|------|------|------|
| canvas_utils.py | 33,854行, 4层架构 | ✅ 稳定 | 核心业务逻辑 |
| 12个Sub-agent | `.claude/agents/*.md` (实际14个) | ✅ 验证可用 | Agent定义 |
| Epic 10.2异步引擎 | 1703行代码, 8倍性能提升 | ✅ 完成 | 性能优势 |
| 测试套件 | 2764个测试函数, 127个测试文件 | ✅ 高质量 | 质量保证 |
| Graphiti集成 | Neo4j + KnowledgeGraphLayer (383行) | ✅ 完成 | 知识图谱基础 |
| Temporal Memory | Neo4j/Graphiti封装 (480行) | ✅ 已实现 | 时序记忆 |
| Semantic Memory | MCP+ChromaDB (492行) | ✅ 已实现 (3模式降级) | 语义记忆 |
| EbbinghausReviewSystem | 经典遗忘曲线 (869行) | ✅ 已实现 (计划升级Py-FSRS) | 复习算法 |
```

---

## ✅ 验证检查清单

修正完成后，请验证：

- [ ] 所有Temporal Memory提到的地方都改为 "Neo4j/Graphiti"
- [ ] 所有Semantic Memory提到的地方都改为 "MCP+ChromaDB"
- [ ] 所有Py-FSRS提到的地方都标注为 "计划升级"
- [ ] 所有3层架构提到的地方都改为 "4层架构"
- [ ] Section 3工具定义中的4个新工具参数与实际代码匹配
- [ ] Epic 11/12/14的Story技术细节与修正后描述一致

---

## 📝 应用修正的方法

### 方法1: 手动修改（推荐）

1. 在编辑器中打开PRD文件
2. 使用Ctrl+F搜索每个"当前错误文本"
3. 替换为"修正为"的内容
4. 保存文件

### 方法2: 自动应用（需关闭其他访问PRD的程序）

1. 关闭所有可能正在访问PRD的程序（IDE、Obsidian等）
2. 告知PM Agent继续执行自动修正
3. PM Agent将使用Edit工具逐一应用修正

---

## 📌 修正依据

所有修正基于以下实际代码审计：

1. ✅ `canvas_utils.py` (33,854行) - 完整代码审计
2. ✅ `memory_system/temporal_memory_manager.py` (480行) - 技术栈验证
3. ✅ `memory_system/semantic_memory_manager.py` (492行) - 技术栈验证
4. ✅ `ebbinghaus_review.py` (869行) - 算法实现验证
5. ✅ `command_handlers/intelligent_parallel_handler.py` (1393行) - Epic 10验证
6. ✅ `.claude/agents/` (14个agent文件) - Agent系统验证
7. ✅ `tests/` (2764个测试函数) - 测试覆盖率验证

**验证日期**: 2025-11-12
**验证人**: PM Agent (John)
**验证方法**: 深度代码审计 + 文件系统探索 + 技术栈追溯
