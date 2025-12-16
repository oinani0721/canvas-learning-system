# Epic 12.A: Agent-RAG 深度集成 - Brownfield Enhancement

**版本**: 1.0
**创建日期**: 2025-12-15
**状态**: 待实施
**类型**: Brownfield Enhancement (Epic 12 扩展补丁)
**来源**: UltraThink 深度调研报告

---

## 1. Epic 概述

### 1.1 Epic 目标

修复 4 个关键断裂点，让右键菜单 Agent 真正使用 LangGraph 多源融合能力，实现：
- Agent 调用时获取 5 源融合上下文 (Graphiti + LanceDB + 多模态 + 教材 + 跨Canvas)
- Agent 读取当前节点和周边连接节点的完整内容
- Agent 基于用户学习历史进行个性化响应
- 补齐设计中缺失的剖析节点 Agent

### 1.2 问题背景

**UltraThink 深度调研发现**:

| 系统 | 代码完成度 | 集成完成度 | 根本问题 |
|------|-----------|------------|---------|
| LangGraph RAG | 88% | **0%** | 插件右键菜单从未调用 RAG API |
| Agent 端点 | 90% | **50%** | 直接调用 AI，不使用多源融合 |
| 记忆系统 | 85% | **10%** | 存在但未注入 Agent 上下文 |
| 节点上下文 | 80% | **30%** | Canvas 名称格式错误导致读取失败 |

**Bug Log 统计**: 39次 "无法从AI响应中提取有效内容" 错误

### 1.3 成功标准

| 指标 | 当前值 | 目标值 | 验证方法 |
|------|--------|--------|---------|
| Agent 调用成功率 | ~30% | 95%+ | Bug log 错误归零 |
| RAG 上下文注入率 | 0% | 100% | 每次 Agent 调用包含 RAG 结果 |
| 节点上下文完整性 | 0% | 100% | 包含目标节点 + 相邻节点 |
| 学习历史注入率 | 0% | 100% | 每次调用查询记忆系统 |
| 可用 Agent 数量 | 9 | 14 | 右键菜单完整显示 |

---

## 2. 现有系统上下文

### 2.1 技术栈

- **后端**: FastAPI + Python 3.11
- **前端插件**: TypeScript + Obsidian API
- **LangGraph**: StateGraph + 5源并行检索
- **记忆系统**: Graphiti + LanceDB + JSON 存储

### 2.2 关键集成点

```
canvas-progress-tracker/obsidian-plugin/
├── src/api/ApiClient.ts           # HTTP API 客户端
├── src/managers/ContextMenuManager.ts  # 右键菜单管理
└── main.ts                        # 插件入口

backend/app/
├── api/v1/endpoints/agents.py     # Agent API 端点
├── api/v1/endpoints/rag.py        # RAG API 端点
├── services/agent_service.py      # Agent 服务层
├── services/rag_service.py        # RAG 服务层
├── services/canvas_service.py     # Canvas 文件服务
├── services/context_enrichment_service.py  # 上下文增强
└── clients/graphiti_client.py     # 记忆系统客户端
```

### 2.3 当前架构断裂

```
┌─────────────────────────────────────────────────────────────┐
│ 当前架构（断裂状态）                                         │
├─────────────────────────────────────────────────────────────┤
│  右键菜单 → /agents/* → AgentService → 直接调用AI ❌        │
│                         ↓ (独立运行)                       │
│                    不使用LangGraph融合                      │
│                    不读取节点上下文                          │
│                    不注入学习记忆                           │
│                                                            │
│  RAG端点 → /rag/* → RAGService → LangGraph StateGraph ✅   │
│                      ↓ (完整实现但未被调用)                  │
│                 5源并行检索 + 质量控制                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Stories 列表

### Story 12.A.1: Canvas 名称标准化 (P0 BLOCKER)

**问题**: Canvas 名称格式不一致导致 39 次错误

**错误链**:
```
1. 插件传入: "KP13-线性逼近与微分.md" (带.md扩展) ❌
2. CanvasService添加: ".canvas" 扩展
3. 最终路径: "KP13-线性逼近与微分.md.canvas" ❌ 不存在
4. CanvasNotFoundException → Agent 调用失败
```

**修复范围**:
- `ContextMenuManager.ts:974-990` - 传入正确格式
- `canvas_service.py:70-76` - 路径处理逻辑容错
- `ApiClient.ts` - 请求发送前标准化

**验收标准**:
- [ ] Canvas 名称统一为 `Canvas/Math53/Lecture5` 格式（无扩展名）
- [ ] 39 次错误归零
- [ ] 添加单元测试覆盖路径处理

**预估**: 1h

---

### Story 12.A.2: Agent-RAG 桥接层 (P1)

**问题**: Agent 端点不使用 LangGraph 融合

**修复范围**:
- `agents.py` - 在 Agent 调用前触发 RAG 查询
- `agent_service.py` - 接收 RAG 上下文参数

**实现方案**:
```python
# agents.py - 修改 decompose_basic 端点
async def decompose_basic(request: DecomposeRequest):
    # 新增: 先调用 RAG 获取多源上下文
    rag_context = await rag_service.query(
        query=request.content,
        canvas_file=request.canvas_name,
        fusion_strategy="weighted"
    )
    # 将 RAG 结果作为 Agent 上下文
    return await agent_service.decompose_basic(
        ...,
        rag_context=rag_context.results
    )
```

**验收标准**:
- [ ] Agent 调用时获取 5 源融合上下文
- [ ] Agent 响应质量显著提升
- [ ] RAG 延迟 < 2s (可接受)

**预估**: 2h

---

### Story 12.A.3: 节点上下文深度读取 (P1)

**问题**: Agent 不读取当前节点和周边节点

**修复范围**:
- `context_enrichment_service.py` - 增强 `enrich_with_full_context()`
- `canvas_service.py` - 添加 `get_edges_for_node()` 方法

**实现方案**:
```python
async def enrich_with_full_context(canvas_name, node_id):
    # 1. 获取目标节点内容
    target_node = await canvas_service.get_node(canvas_name, node_id)

    # 2. 获取所有相邻节点 (edges)
    edges = await canvas_service.get_edges_for_node(canvas_name, node_id)
    adjacent_nodes = [
        await canvas_service.get_node(canvas_name, e.to_node)
        for e in edges
    ]

    # 3. 获取 Graphiti 关系上下文
    graphiti_context = await graphiti_client.search_related(target_node.text)

    # 4. 组合完整上下文
    return EnrichedContext(
        target=target_node,
        adjacent=adjacent_nodes,
        graphiti=graphiti_context
    )
```

**验收标准**:
- [ ] Agent 知道当前节点的完整内容
- [ ] Agent 知道 edge 连接的周边节点 (父节点 + 子节点)
- [ ] Agent 知道 Graphiti 中的关联概念

**预估**: 2h

---

### Story 12.A.4: 记忆系统注入 (P2)

**问题**: Agent 不知道用户学习历史

**修复范围**:
- `agent_service.py` - 调用 `LearningMemoryClient`
- Prompt 模板 - 添加学习历史段落

**实现方案**:
```python
async def decompose_basic(content, canvas_name, node_id, rag_context=None):
    # 新增: 查询学习记忆
    memories = await learning_memory_client.search_memories(
        query=content,
        canvas_name=canvas_name,
        limit=5
    )
    memory_context = learning_memory_client.format_for_context(memories)

    # 将记忆注入 Agent 提示词
    prompt = f"""
    {content}

    --- 用户学习历史 ---
    {memory_context}

    --- RAG 多源上下文 ---
    {rag_context}
    """
```

**验收标准**:
- [ ] Agent 提示词包含用户学习历史
- [ ] Agent 响应考虑用户已知/薄弱概念
- [ ] 无学习历史时优雅降级

**预估**: 2h

---

### Story 12.A.5: 学习事件自动记录 (P2)

**问题**: Agent 响应后未记录学习事件

**修复范围**:
- `agents.py` - 响应后调用 `MemoryService`
- `memory_service.py` - 确保 `record_learning_event()` 工作

**实现方案**:
```python
# agents.py - 在返回响应前
async def decompose_basic(request):
    result = await agent_service.decompose_basic(...)

    # 新增: 记录学习事件 (后台任务，不阻塞响应)
    background_tasks.add_task(
        memory_service.record_learning_event,
        user_id="default",
        concept=result.main_concept,
        understanding=result.summary,
        canvas_name=request.canvas_name,
        node_id=request.node_id
    )

    return result
```

**验收标准**:
- [ ] 每次 Agent 调用自动记录到 learning_memories.json
- [ ] 后续调用可检索历史记录
- [ ] 记录不阻塞 Agent 响应

**预估**: 1h

---

### Story 12.A.6: 补齐剖析节点 Agent (P1)

**问题**: 缺失关键 Agent 类型 (9个 vs 设计14个)

**需要实现的 Agent**:
| Agent | 用途 | 优先级 |
|-------|------|--------|
| `verification-question` | 生成检验问题 | P1 |
| `question-decomposition` | 问题拆解 | P1 |
| `canvas-orchestrator` | Canvas 编排器 | P2 |
| `iteration-validator` | 迭代验证器 | P3 |
| `graphiti-memory-agent` | 记忆图谱 Agent | P3 |

**修复范围**:
- `agent_service.py` - 添加新 Agent 方法
- `agents.py` - 添加新端点
- `ApiClient.ts` - 添加前端调用方法
- `ContextMenuManager.ts` - 添加右键菜单项

**验收标准**:
- [ ] 右键菜单显示所有 14 个 Agent 选项
- [ ] 每个 Agent 都能正常工作
- [ ] 新 Agent 也使用 RAG 桥接层

**预估**: 3h

---

## 4. 实施优先级

| 优先级 | Story | 依赖 | 预估 | 风险 |
|--------|-------|------|------|------|
| **P0** | 12.A.1 Canvas 名称标准化 | 无 | 1h | 低 |
| **P1** | 12.A.2 Agent-RAG 桥接层 | 12.A.1 | 2h | 中 |
| **P1** | 12.A.3 节点上下文深度读取 | 12.A.1 | 2h | 低 |
| **P1** | 12.A.6 补齐剖析节点 Agent | 12.A.1 | 3h | 低 |
| **P2** | 12.A.4 记忆系统注入 | 12.A.2, 12.A.3 | 2h | 低 |
| **P2** | 12.A.5 学习事件自动记录 | 12.A.4 | 1h | 低 |

**总预估**: 11h (分 2-3 个 Sprint)

---

## 5. 兼容性要求

- [x] 现有 Agent API 端点保持不变 (增量添加参数)
- [x] 现有 RAG API 端点保持不变
- [x] 数据库 schema 无变更
- [x] UI 右键菜单向后兼容
- [x] 性能影响可控 (RAG 延迟 < 2s)

---

## 6. 风险缓解

### 主要风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| RAG 调用增加延迟 | 用户体验下降 | 并行执行 RAG 和上下文获取 |
| 记忆系统数据污染 | 错误的学习历史 | 添加数据验证层 |
| Agent 响应格式不一致 | 前端解析失败 | 统一响应 schema |

### 回滚计划

1. **Feature Flag**: 添加 `USE_RAG_BRIDGE` 环境变量
2. **分步发布**: 先发布 12.A.1，验证后再发布其他 Stories
3. **数据备份**: 修改前备份 learning_memories.json

---

## 7. 关键文件清单

### 需要修改的文件

| 文件 | 修改内容 | Story |
|------|---------|-------|
| `ContextMenuManager.ts:974-990` | Canvas 名称格式 | 12.A.1 |
| `canvas_service.py:70-76` | 路径处理容错 | 12.A.1 |
| `ApiClient.ts` | 名称标准化 + 新方法 | 12.A.1, 12.A.6 |
| `agents.py` | RAG 桥接 + 新端点 | 12.A.2, 12.A.5, 12.A.6 |
| `agent_service.py` | 记忆注入 + 新方法 | 12.A.4, 12.A.6 |
| `context_enrichment_service.py` | 完整上下文获取 | 12.A.3 |

### 新增文件

| 文件 | 用途 | Story |
|------|------|-------|
| `tests/test_canvas_name_normalize.py` | 名称标准化测试 | 12.A.1 |
| `agents/verification_question.py` | 新 Agent | 12.A.6 |
| `agents/question_decomposition.py` | 新 Agent | 12.A.6 |

---

## 8. Definition of Done

- [ ] 所有 6 个 Stories 完成，验收标准满足
- [ ] Bug log 中 "无法从AI响应中提取有效内容" 错误归零
- [ ] 右键菜单所有 Agent 选项可用
- [ ] Agent 响应包含多源上下文
- [ ] 学习事件自动记录到记忆系统
- [ ] 单元测试覆盖关键路径
- [ ] 插件重新构建并部署到正确 vault

---

## 9. Story Manager 交接

**请为此 Brownfield Epic 开发详细用户故事。关键考虑点**:

- 这是对现有系统的增强，运行 FastAPI + TypeScript 技术栈
- 集成点: Agent API → RAG Service → LangGraph StateGraph
- 现有模式: 异步服务调用、依赖注入、TypeScript 类型安全
- 关键兼容性要求: 现有 API 端点保持不变

Epic 目标是在保持系统完整性的同时，让 Agent 真正使用 LangGraph 5源融合能力。

---

*Epic 12.A 创建完成 - 2025-12-15*
*基于 UltraThink 深度调研报告*
