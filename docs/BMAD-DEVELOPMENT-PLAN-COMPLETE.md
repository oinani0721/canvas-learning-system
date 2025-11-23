# Canvas Learning System - BMad 4.0 严格合规完整开发计划

**生成日期**: 2025-11-21
**开发范围**: Epic 11-14 (FastAPI → 三层记忆 → UI → 艾宾浩斯)
**预计总时长**: 12-16周
**基于**: README-BMAD-WORKFLOW.md, core-config.yaml, 交付文件清单

---

## 目录

1. [Phase状态总览](#phase状态总览)
2. [阶段一：Phase 3补全](#阶段一phase-3-solutioning-补全-1周)
3. [阶段二：Epic 11 FastAPI后端](#阶段二epic-11---fastapi后端-2周)
4. [阶段三：Epic 12 三层记忆](#阶段三epic-12---三层记忆agentic-rag-4-5周)
5. [阶段四：Epic 13 Obsidian Plugin](#阶段四epic-13---obsidian-plugin-ui-2-3周)
6. [阶段五：Epic 14 艾宾浩斯系统](#阶段五epic-14---艾宾浩斯复习系统-3-4周)
7. [完整里程碑时间线](#完整里程碑时间线)
8. [通用Story开发流程](#通用story开发流程-smdevqa循环)
9. [变更处理流程](#变更处理流程)
10. [验收检查清单](#验收检查清单)

---

## Phase状态总览

| Phase | 当前状态 | 行动 |
|-------|---------|------|
| Phase 1: Analysis | ✅ 完成 | - |
| Phase 2: Planning | ✅ 完成 | - |
| **Phase 3: Solutioning** | ⚠️ 70% | **需先补全** |
| Phase 4: Implementation | ⏳ 待开始 | 完成Phase 3后启动 |

---

## 阶段一：Phase 3 Solutioning 补全 (1周)

### 1.1 交付文件清单

| 文件 | 类型 | 负责Agent | BMad指令 |
|------|------|----------|----------|
| `specs/api/agent-api.openapi.yml` | OpenAPI | Architect | 自然语言请求 |
| `specs/data/canvas-edge.schema.json` | JSON Schema | Architect | 自然语言请求 |
| `specs/data/agent-response.schema.json` | JSON Schema | Architect | 自然语言请求 |
| `docs/architecture/neo4j-review-history-schema.md` | 架构文档 | Architect | `*research` |
| 验证现有OpenAPI规范完整性 | 验证 | Architect | `*execute-checklist` |

### 1.2 指令序列

```bash
# ═══════════════════════════════════════════════════════════════
# Step 1: 激活Architect Agent
# ═══════════════════════════════════════════════════════════════
/architect

# ═══════════════════════════════════════════════════════════════
# Step 2: 研究并创建缺失的OpenAPI规范
# ═══════════════════════════════════════════════════════════════
*research "FastAPI OpenAPI 3.0 specification best practices"

# 创建Agent API规范
"请基于Epic 11-14的API endpoints创建完整的agent-api.openapi.yml，包含：
- 9个Agent调用endpoints
- 复习系统endpoints
- 请求/响应Schema"
*doc-out

# ═══════════════════════════════════════════════════════════════
# Step 3: 创建JSON Schemas
# ═══════════════════════════════════════════════════════════════
"请为Canvas边和Agent响应创建JSON Schema：
- canvas-edge.schema.json
- agent-response.schema.json"
*doc-out

# ═══════════════════════════════════════════════════════════════
# Step 4: 创建Neo4j Schema设计文档
# ═══════════════════════════════════════════════════════════════
*research "Neo4j schema design for review history"
"请创建neo4j-review-history-schema.md，包含：
- ReviewCanvas节点
- GENERATED_FROM关系
- 索引设计"
*doc-out

# ═══════════════════════════════════════════════════════════════
# Step 5: 验证现有规范
# ═══════════════════════════════════════════════════════════════
*execute-checklist architecture-validation
*exit

# ═══════════════════════════════════════════════════════════════
# Step 6: PO验证
# ═══════════════════════════════════════════════════════════════
/po
*execute-checklist-po
*exit
```

### 1.3 验收标准

- [ ] OpenAPI规范覆盖所有28个endpoints (19+9)
- [ ] JSON Schema定义完整且符合规范
- [ ] Neo4j Schema设计文档完成
- [ ] PO验证通过

---

## 阶段二：Epic 11 - FastAPI后端 (2周)

### 2.1 Story依赖分析

```
Story 11.1 (初始化) → Story 11.2 (路由) → Story 11.3 (依赖注入)
                                            ↓
Story 11.4 (中间件) ← Story 11.5 (异步) ← Story 11.6 (文档测试)
```

**并行可行性**:
- Phase 1: 11.1必须先完成
- Phase 2: 11.2, 11.3可并行
- Phase 3: 11.4, 11.5, 11.6可并行

### 2.2 交付文件矩阵

| Story ID | Story名称 | 交付文件 | 预计时间 |
|----------|----------|----------|---------|
| 11.1 | FastAPI应用初始化 | `backend/app/main.py`<br>`backend/app/config.py`<br>`backend/app/dependencies.py` | 4-6h |
| 11.2 | 路由系统配置 | `backend/app/api/v1/endpoints/canvas.py`<br>`backend/app/api/v1/endpoints/agents.py`<br>`backend/app/api/v1/endpoints/review.py` | 5-7h |
| 11.3 | 依赖注入系统 | `backend/app/dependencies/canvas.py`<br>`backend/app/dependencies/agents.py`<br>DI系统设计 | 6-8h |
| 11.4 | 中间件和错误处理 | `backend/app/middleware/logging.py`<br>`backend/app/middleware/error_handler.py`<br>`backend/app/middleware/cors.py` | 5-7h |
| 11.5 | 异步操作 | 异步服务层<br>`asyncio`集成<br>后台任务 | 6-9h |
| 11.6 | API文档和测试 | Swagger文档配置<br>`tests/test_canvas.py`<br>`tests/test_agents.py`<br>pytest配置 | 4-6h |

### 2.3 完整指令序列

```bash
# ═══════════════════════════════════════════════════════════════
# Phase 1: Story 11.1 (必须先完成)
# ═══════════════════════════════════════════════════════════════

# SM创建Story
/sm
*draft
*story-checklist

# Dev实现 (需查询Context7)
/dev
# 查询FastAPI文档
# 使用Context7: resolve-library-id "fastapi" → get-library-docs
*develop-story story-11.1
*run-tests

# QA审查
/qa
*risk-profile story-11.1
*review story-11.1
*gate story-11.1

# ═══════════════════════════════════════════════════════════════
# Phase 2: 并行开发 Story 11.2 + 11.3
# ═══════════════════════════════════════════════════════════════

# 激活并行协调器
/parallel

# 分析依赖
*analyze "11.2, 11.3"

# 创建worktrees
*init "11.2, 11.3"

# 在各worktree中执行 (需要2个Claude Code窗口):
# ─────────────────────────────────────────
# Window 1 (Story 11.2):
/sm
*draft
/dev
*develop-story story-11.2
*run-tests

# Window 2 (Story 11.3):
/sm
*draft
/dev
*develop-story story-11.3
*run-tests
# ─────────────────────────────────────────

# 回到主窗口监控进度
*status

# 合并
*merge --all
*cleanup

# QA审查两个Story
/qa
*review story-11.2
*gate story-11.2
*review story-11.3
*gate story-11.3

# ═══════════════════════════════════════════════════════════════
# Phase 3: 并行开发 Story 11.4 + 11.5 + 11.6
# ═══════════════════════════════════════════════════════════════

/parallel
*analyze "11.4, 11.5, 11.6"
*init "11.4, 11.5, 11.6"

# 在各worktree中执行 (需要3个Claude Code窗口):
# Window 1: Story 11.4
# Window 2: Story 11.5
# Window 3: Story 11.6

*status
*merge --all
*cleanup

/qa
*review story-11.4
*gate story-11.4
*review story-11.5
*gate story-11.5
*review story-11.6
*gate story-11.6
```

### 2.4 技术验证要求

**强制文档来源**: Context7 `/websites/fastapi_tiangolo`

每个API调用必须有文档标注：

```python
# ✅ Verified from Context7 (FastAPI - Dependency Injection)
from fastapi import Depends

# ✅ Verified from Context7 (FastAPI - APIRouter)
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/canvas", tags=["canvas"])
```

### 2.5 验收标准

- [ ] 19个API endpoints全部可调用
- [ ] pytest覆盖率 ≥ 85%
- [ ] Swagger文档可访问 (`/docs`)
- [ ] 异步操作无阻塞
- [ ] 中间件正确处理请求/响应
- [ ] 错误处理覆盖400/404/500

---

## 阶段三：Epic 12 - 三层记忆+Agentic RAG (4-5周)

### 3.1 Story列表 (16个)

| Story ID | Story名称 | 交付文件 | 关键技术 | 预计时间 |
|----------|----------|----------|----------|---------|
| 12.1 | LanceDB集成 | `src/memory/lancedb_client.py` | LanceDB向量存储 | 2-3天 |
| 12.2 | 数据迁移工具 | `scripts/migrate_to_lancedb.py` | 迁移脚本 | 1-2天 |
| 12.3 | Graphiti增强 | `src/memory/graphiti_enhanced.py` | 混合搜索 | 2-3天 |
| 12.4 | Neo4j优化 | Neo4j索引配置 | 性能优化 | 1-2天 |
| 12.5 | LangGraph StateGraph | `src/agents/langgraph_stategraph.py` | 状态图 | 3-4天 |
| 12.6 | 并行检索节点 | 并行检索实现 | Temporal+Semantic+Graphiti | 2-3天 |
| 12.7 | RRF融合算法 | `src/memory/fusion_algorithms.py` | RRF | 2天 |
| 12.8 | Weighted融合 | 融合算法扩展 | 权重融合 | 1-2天 |
| 12.9 | Cascade融合 | 融合算法扩展 | 级联融合 | 2天 |
| 12.10 | 混合Reranking | `src/memory/reranking.py` | 重排序 | 2-3天 |
| 12.11 | Query重写循环 | 查询优化 | 迭代优化 | 2天 |
| 12.12 | Canvas集成 | 完整流程集成 | E2E | 3-4天 |
| 12.13 | 性能监控 | 监控仪表板 | Prometheus | 2天 |
| 12.14 | 成本追踪 | 成本追踪系统 | API统计 | 1-2天 |
| 12.15 | 集成测试 | `tests/integration/` | E2E测试 | 2-3天 |
| 12.16 | 多模态扩展 | 多模态支持 | 图片/PDF (P2) | 3-4天 |

### 3.2 并行策略

```
Batch 1 (Week 4-5): 12.1, 12.2, 12.3, 12.4  [可并行]
          ↓
Batch 2 (Week 5-6): 12.5, 12.6              [依赖Batch 1]
          ↓
Batch 3 (Week 6):   12.7, 12.8, 12.9        [可并行]
          ↓
Batch 4 (Week 7):   12.10, 12.11            [依赖Batch 3]
          ↓
Batch 5 (Week 7-8): 12.12, 12.13, 12.14, 12.15, 12.16 [可并行]
```

### 3.3 Batch 1指令序列示例

```bash
# ═══════════════════════════════════════════════════════════════
# Batch 1: 并行开发 12.1, 12.2, 12.3, 12.4
# ═══════════════════════════════════════════════════════════════

/parallel
*analyze "12.1, 12.2, 12.3, 12.4"
*init "12.1, 12.2, 12.3, 12.4"

# 4个worktree并行开发
# ─────────────────────────────────────────
# Window 1 (Story 12.1 - LanceDB):
/sm
*draft
/dev
# 查询Context7: resolve-library-id "lancedb"
*develop-story story-12.1
*run-tests

# Window 2 (Story 12.2 - Migration):
/sm
*draft
/dev
*develop-story story-12.2
*run-tests

# Window 3 (Story 12.3 - Graphiti):
/sm
*draft
/dev
# 使用Skill: @graphiti
*develop-story story-12.3
*run-tests

# Window 4 (Story 12.4 - Neo4j):
/sm
*draft
/dev
# 查询Context7: resolve-library-id "neo4j"
*develop-story story-12.4
*run-tests
# ─────────────────────────────────────────

# 合并和QA
*merge --all
*cleanup

/qa
*review story-12.1
*gate story-12.1
# ... 重复其他Story
```

### 3.4 技术验证要求

**强制文档来源**:
- LangGraph: `@langgraph` Skill
- Graphiti: `@graphiti` Skill
- LanceDB: Context7 `/lancedb/lancedb`
- Neo4j: Context7

代码标注示例：

```python
# ✅ Verified from LangGraph Skill (SKILL.md - Pattern: StateGraph)
from langgraph.graph import StateGraph

state_graph = StateGraph(AgentState)
state_graph.add_node("retrieve", retrieve_node)
state_graph.add_edge("retrieve", "fuse")

# ✅ Verified from Graphiti Skill (references/hybrid-search.md)
from graphiti_core import Graphiti
results = await graphiti.hybrid_search(query, limit=10)

# ✅ Verified from Context7 (/lancedb/lancedb - Vector Search)
import lancedb
db = lancedb.connect("./data/lancedb")
table = db.create_table("vectors", data)
```

### 3.5 验收标准

- [ ] Agentic RAG检索准确率 ≥ 85%
- [ ] 三层记忆系统完整集成
- [ ] 融合算法可切换 (RRF/Weighted/Cascade)
- [ ] Query重写最多3次迭代
- [ ] 性能监控仪表板可访问
- [ ] 成本追踪准确

---

## 阶段四：Epic 13 - Obsidian Plugin UI (2-3周)

### 4.1 Story列表 (9个)

| Story ID | Story名称 | 交付文件 | 预计时间 |
|----------|----------|----------|---------|
| 13.1 | Plugin项目初始化 | `obsidian-plugin/`项目结构<br>TypeScript配置<br>构建脚本 | 1-2天 |
| 13.2 | Canvas API集成 | Canvas文件读写封装<br>节点/边操作API | 2-3天 |
| 13.3 | API客户端实现 | FastAPI HTTP客户端<br>类型定义<br>错误处理 | 1-2天 |
| 13.4 | 核心命令 | 拆解/评分/解释命令<br>命令注册系统 | 2-3天 |
| 13.5 | 右键菜单和快捷键 | Canvas节点右键菜单<br>快捷键配置 | 1-2天 |
| 13.6 | 设置面板 | Plugin设置页面<br>后端URL配置 | 1天 |
| 13.7 | 错误处理 | 全局错误捕获<br>用户友好提示 | 1天 |
| 13.8 | 智能并行处理UI | 并行处理面板<br>进度显示 | 2天 |
| 13.9 | 单节点智能分析UI | 单节点分析面板<br>结果显示 | 2天 |

### 4.2 技术验证要求

**强制使用**: `@obsidian-canvas` Skill

```bash
# SM编写Story时必须查询Skill
/sm
"@obsidian-canvas 查询Canvas API节点操作方法"
*draft
```

代码标注示例：

```typescript
// ✅ Verified from obsidian-canvas Skill (references/canvas-api.md)
import { Canvas, CanvasNode, CanvasEdge } from 'obsidian';

// 读取Canvas文件
const canvasData = await this.app.vault.read(canvasFile);
const canvas = JSON.parse(canvasData);

// 创建节点
const newNode: CanvasNode = {
    id: generateId(),
    type: 'text',
    text: content,
    x: 0, y: 0,
    width: 400, height: 200,
    color: '1' // 红色
};
```

### 4.3 指令序列

```bash
# ═══════════════════════════════════════════════════════════════
# 串行开发 (Story间依赖较强)
# ═══════════════════════════════════════════════════════════════

# Story 13.1-13.7 按顺序开发
for story_id in 13.1 13.2 13.3 13.4 13.5 13.6 13.7; do
    /sm
    "@obsidian-canvas 查询相关API"
    *draft
    *story-checklist

    /dev
    *develop-story story-${story_id}
    *run-tests

    /qa
    *review story-${story_id}
    *gate story-${story_id}
done

# ═══════════════════════════════════════════════════════════════
# 并行开发 Story 13.8 + 13.9
# ═══════════════════════════════════════════════════════════════

/parallel
*analyze "13.8, 13.9"
*init "13.8, 13.9"

# 2个worktree并行开发
# Window 1: Story 13.8
# Window 2: Story 13.9

*merge --all
*cleanup
```

### 4.4 验收标准

- [ ] Plugin可在Obsidian中安装
- [ ] 所有核心命令可用
- [ ] 右键菜单正常显示
- [ ] 设置面板可配置后端URL
- [ ] 错误提示用户友好
- [ ] Canvas文件读写正确

---

## 阶段五：Epic 14 - 艾宾浩斯复习系统 (3-4周)

### 5.1 Story列表 (15个)

| Story ID | Story名称 | 交付文件 | 关键功能 | 预计时间 |
|----------|----------|----------|----------|---------|
| 14.1 | Py-FSRS算法迁移 | `src/review/fsrs_algorithm.py`<br>数据库扩展 | 从经典公式升级 | 2-3天 |
| 14.2 | FastAPI接口封装 | `backend/app/api/v1/endpoints/review.py` | REST API | 1-2天 |
| 14.3 | 复习面板视图 | Obsidian侧边栏View | UI组件 | 3-4天 |
| 14.4 | 今日复习列表与交互 | 按钮/右键菜单 | 用户交互 | 2-3天 |
| 14.5 | 一键生成检验白板 | `generate_review_canvas_file()` | fresh/targeted模式 | 1.5天 |
| 14.6 | 复习历史+趋势分析 | 图表组件 | 可视化 | 1.5-2.5天 |
| 14.7 | 复习提醒通知 | Obsidian Notice | 通知系统 | 1天 |
| 14.8 | 复习统计图表 | Chart.js集成 | 数据可视化 | 2天 |
| 14.9 | 3层记忆查询工具 | 4个新查询工具 | 记忆系统集成 | 2-3天 |
| 14.10 | 行为监控触发机制 | 定时任务调度器 | 触发点4 | 3-4天 |
| 14.11 | 多维度优先级计算 | 优先级算法 | 4维度综合评分 | 2天 |
| 14.12 | FSRS参数优化 | 梯度下降优化 | 参数调优 | 3-4天 |
| 14.13 | 检验历史存储 | Graphiti关系 | 关系持久化 | 2天 |
| 14.14 | 针对性复习算法 | 权重计算 | 智能权重 | 3天 |
| 14.15 | 复习模式选择UI | Settings+Modal | UI组件 | 1.5天 |

### 5.2 依赖关系

```
Phase 1 (Week 12-13): 14.1, 14.2, 14.3, 14.4, 14.5  [基础功能]
          ↓
Phase 2 (Week 13-14): 14.6, 14.7, 14.8              [UI增强]
          ↓
Phase 3 (Week 14-15): 14.9, 14.10, 14.11, 14.12     [3层记忆整合，依赖Epic 12]
          ↓
Phase 4 (Week 15):    14.13, 14.14, 14.15           [检验历史关联]
```

### 5.3 关键算法

#### 多维度优先级计算 (Story 14.11)

```python
def calculate_multidimensional_priority(concept_id: str) -> float:
    """
    计算概念的综合复习优先级

    维度1: FSRS紧迫性 (40%) - 基于遗忘曲线
    维度2: 行为权重 (30%) - 从Temporal Memory
    维度3: 网络中心性 (20%) - 从Graphiti
    维度4: 交互权重 (10%) - 从Semantic Memory
    """
    # 维度1: FSRS紧迫性
    fsrs_urgency = calculate_fsrs_urgency(concept_id)

    # 维度2: 行为权重
    behavior_weight = query_temporal_learning_behavior(concept_id)

    # 维度3: 网络中心性
    network_centrality = query_graphiti_concept_network(concept_id)

    # 维度4: 交互权重
    interaction_weight = query_semantic_document_interactions(concept_id)

    return (
        fsrs_urgency * 0.4 +
        behavior_weight * 0.3 +
        network_centrality * 0.2 +
        interaction_weight * 0.1
    )
```

#### 针对性复习权重 (Story 14.14)

```python
def calculate_targeted_review_weights(
    weak_concepts: List[str],
    mastered_concepts: List[str],
    config: Dict = None
) -> List[Tuple[str, float]]:
    """
    计算针对性复习的概念权重

    默认配置: {"weak_ratio": 0.7, "mastered_ratio": 0.3}
    - 70%薄弱概念（最近失败的权重最高）
    - 30%已掌握概念（防止遗忘）
    """
    config = config or {"weak_ratio": 0.7, "mastered_ratio": 0.3}
    # ... 实现
```

### 5.4 验收标准

- [ ] Py-FSRS算法准确率提升20-30%
- [ ] 复习面板显示正确
- [ ] 今日复习列表交互流畅
- [ ] 检验白板生成支持两种模式
- [ ] 历史趋势图表显示正确
- [ ] 3层记忆查询工具可用
- [ ] 触发点4定时任务正常运行
- [ ] 多维度优先级计算准确

---

## 完整里程碑时间线

| 里程碑 | 内容 | 预计时间 | 主要交付物 |
|--------|------|---------|-----------|
| **M0** | Phase 3补全 | Week 1 | OpenAPI specs<br>JSON Schemas<br>Neo4j Schema设计 |
| **M1** | Epic 11完成 | Week 2-3 | FastAPI后端可运行<br>19个API endpoints<br>Swagger文档 |
| **M2** | Epic 12 Batch 1-2 | Week 4-5 | LanceDB集成<br>Graphiti增强<br>LangGraph StateGraph |
| **M3** | Epic 12 Batch 3-5 | Week 6-8 | 完整Agentic RAG<br>融合算法<br>性能监控 |
| **M4** | Epic 13完成 | Week 9-11 | Obsidian Plugin可安装<br>所有命令可用<br>设置面板 |
| **M5** | Epic 14完成 | Week 12-15 | 艾宾浩斯系统可用<br>复习面板<br>3层记忆整合 |
| **M6** | 集成测试+优化 | Week 16 | 全系统验收<br>性能优化<br>文档完善 |

### 甘特图视图

```
Week:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16
      ─┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───
M0    [█]
M1        [███████]
M2                    [███████]
M3                            [███████████]
M4                                        [███████████]
M5                                                    [███████████]
M6                                                                [█]
```

---

## 通用Story开发流程 (SM→Dev→QA循环)

每个Story严格执行以下流程：

```bash
# ═══════════════════════════════════════════════════════════════
# Step 1: SM创建Story Draft
# ═══════════════════════════════════════════════════════════════
/sm
*draft                    # SM自动读取Epic文档，生成Story
*story-checklist          # 验证Story完整性

# Story文件会生成在: docs/stories/story-{epic}.{story}.md
# 包含完整的Dev Notes（技术上下文、API规范等）

# ═══════════════════════════════════════════════════════════════
# Step 2: Dev实现
# ═══════════════════════════════════════════════════════════════
/dev
# Dev Agent自动加载devLoadAlwaysFiles (编码标准、SDD规范等)

# 查询技术文档 (零幻觉原则)
# - Skills: @langgraph, @graphiti, @obsidian-canvas
# - Context7: resolve-library-id → get-library-docs

*develop-story {story-id} # Dev只读Story文件，实现代码
*run-tests                # 执行测试

# 所有API调用必须有文档标注:
# ✅ Verified from [来源] ([具体位置])

# ═══════════════════════════════════════════════════════════════
# Step 3: QA审查
# ═══════════════════════════════════════════════════════════════
/qa
*risk-profile {story-id}  # 风险评估 (识别潜在问题)
*trace {story-id}         # 需求追溯 (Given-When-Then)
*nfr-assess {story-id}    # 非功能需求检查
*review {story-id}        # 综合审查
*gate {story-id}          # 质量门禁决策

# 门禁决策:
# - PASS: 继续下一个Story
# - CONCERNS: 团队评审后可继续
# - FAIL: 必须修复 → /dev *review-qa → 重新/qa *gate
# - WAIVED: 记录原因，接受风险

# ═══════════════════════════════════════════════════════════════
# Step 4: 循环继续
# ═══════════════════════════════════════════════════════════════
# 返回Step 1处理下一个Story
```

### 并行开发流程

```bash
# ═══════════════════════════════════════════════════════════════
# 使用Parallel Dev Coordinator
# ═══════════════════════════════════════════════════════════════

# Step 1: 激活协调器
/parallel

# Step 2: 分析依赖
*analyze "story-1, story-2, story-3"
# 输出: 哪些可并行，哪些有冲突

# Step 3: 创建worktrees
*init "story-1, story-2"
# 创建Git worktrees: Canvas-develop-story-1, Canvas-develop-story-2

# Step 4: 在各worktree中开发 (单独的Claude Code窗口)
# Window 1: cd Canvas-develop-story-1 && /dev *develop-story story-1
# Window 2: cd Canvas-develop-story-2 && /dev *develop-story story-2

# Step 5: 监控进度
*status

# Step 6: 合并
*merge --all
# 自动处理合并冲突

# Step 7: 清理
*cleanup
# 删除已合并的worktrees
```

---

## 变更处理流程

### Phase 2变更 (Planning迭代)

当需要修改PRD/Architecture时：

```bash
# Step 1: 初始化迭代
/planning
*init "变更描述"

# Step 2: 进行变更分析
/pm
*correct-course "变更内容"
# 输出: sprint-change-proposal-{date}.md

# Step 3: 验证变更
/planning
*validate
# 检查: breaking changes, API兼容性, Schema兼容性

# Step 4: 完成迭代
*finalize
# 创建Git tag: planning-vN
```

### Phase 4变更 (Sprint中)

当开发过程中发现需要变更时：

```bash
/sm
*correct-course "变更内容"
# 输出: sprint-change-proposal-{date}.md
# 包含: 影响的Stories, 估算影响, 建议
```

### Breaking Changes处理

```bash
# 如果检测到breaking changes
/planning
*validate
# ❌ Breaking Changes Detected!

# 选项A: 修复问题后重试
# 选项B: 接受breaking changes
*finalize --accept-breaking
# 版本号: v1.x.x → v2.0.0

# 必须执行的后续行动:
# 1. 更新CHANGELOG.md
# 2. 通知相关方
# 3. 更新消费者应用
```

---

## 验收检查清单

### 功能验收

#### Epic 11: FastAPI后端
- [ ] 19个API endpoints全部可调用
- [ ] Canvas操作: GET/POST/PUT/DELETE正常
- [ ] Agent调用: 9个Agent endpoint正常
- [ ] Review操作: 生成/进度/同步正常
- [ ] 健康检查: `/api/v1/health`返回200

#### Epic 12: 三层记忆+Agentic RAG
- [ ] LanceDB向量存储正常
- [ ] Graphiti混合搜索可用
- [ ] LangGraph StateGraph流程完整
- [ ] Agentic RAG检索准确率 ≥ 85%
- [ ] 融合算法可切换
- [ ] Query重写最多3次迭代
- [ ] 性能监控仪表板可访问

#### Epic 13: Obsidian Plugin
- [ ] Plugin可在Obsidian中安装
- [ ] 基础拆解命令可用
- [ ] 深度拆解命令可用
- [ ] 评分命令可用
- [ ] 各类解释命令可用
- [ ] 右键菜单正常显示
- [ ] 设置面板可配置

#### Epic 14: 艾宾浩斯复习系统
- [ ] 复习面板显示正确
- [ ] 今日复习列表可交互
- [ ] 一键生成检验白板可用
- [ ] 复习历史趋势图表显示
- [ ] 3层记忆查询工具可用
- [ ] 触发点4定时任务正常
- [ ] 多维度优先级计算准确

### 技术验收

- [ ] 所有API调用有Context7/Skills文档标注
- [ ] pytest覆盖率 ≥ 85%
- [ ] 无安全漏洞 (OWASP Top 10)
- [ ] 异步操作无阻塞
- [ ] 性能指标达标:
  - API响应时间 < 500ms
  - Canvas文件读取 < 200ms
  - Agent调用 < 5秒

### 文档验收

- [ ] Swagger/OpenAPI文档完整
- [ ] 所有技术决策有ADR记录
- [ ] CHANGELOG.md更新
- [ ] README.md更新
- [ ] 用户指南完成

### 集成验收

- [ ] FastAPI ↔ LangGraph集成正常
- [ ] Obsidian Plugin ↔ FastAPI通信正常
- [ ] 艾宾浩斯系统 ↔ 3层记忆集成正常
- [ ] 全系统E2E测试通过

---

## 附录A: 技术栈快速参考

| 技术 | 文档来源 | 查询方式 |
|------|---------|---------|
| FastAPI | Context7 | `resolve-library-id "fastapi"` |
| LangGraph | Skill | `@langgraph` |
| Graphiti | Skill | `@graphiti` |
| Obsidian Canvas | Skill | `@obsidian-canvas` |
| LanceDB | Context7 | `resolve-library-id "lancedb"` |
| Neo4j | Context7 | `resolve-library-id "neo4j"` |
| Py-FSRS | Context7 | `resolve-library-id "py-fsrs"` |
| Pydantic | Context7 | `resolve-library-id "pydantic"` |

---

## 附录B: BMad Agent命令速查

| Agent | 常用命令 | 用途 |
|-------|---------|------|
| PM | `*create-prd`, `*correct-course` | PRD创建/变更 |
| Architect | `*research`, `*doc-out` | 架构设计 |
| SM | `*draft`, `*story-checklist` | Story创建 |
| Dev | `*develop-story`, `*run-tests` | 代码实现 |
| QA | `*review`, `*gate` | 质量审查 |
| PO | `*execute-checklist-po` | 验证 |
| Planning | `*init`, `*validate`, `*finalize` | 迭代管理 |
| Parallel | `*analyze`, `*init`, `*merge` | 并行开发 |

---

**文档结束**

**生成日期**: 2025-11-21
**适用版本**: PRD v1.1.8
**维护者**: Canvas Learning System Team
