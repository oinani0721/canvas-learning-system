> **DEPRECATED** - 此Epic已合并到 [Epic 30: Memory System Complete Activation](../epics/EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md)
>
> 合并日期: 2026-01-15 | 请参考Epic 30获取最新实施计划

---

# Epic 12.M: 记忆系统激活与Neo4j完整部署 - Brownfield Enhancement

## Epic Goal

激活Canvas Learning System的三层记忆系统，实现Neo4j完整部署，支持全部14个Agent的记忆写入触发，使记忆系统从"架构完整但链路断开"状态转变为"完全运行"状态。

---

## Epic Description

### Existing System Context

- **Current relevant functionality**:
  - 三层记忆架构已设计完成 (Graphiti + LanceDB + Temporal Memory)
  - 查询功能95%完成 (search_nodes, search_memories, get_weak_concepts)
  - LangGraph StateGraph 100%完成 (5路并行检索)
  - JSON模拟存储已工作 (neo4j_memory.json, learning_memories.json)

- **Technology stack**:
  - FastAPI后端 (Python 3.11)
  - LangGraph 0.2.x (StateGraph + Send模式)
  - Graphiti MCP服务 (graphiti-memory)
  - Neo4j 5.x (图数据库)
  - py-fsrs (FSRS-4.5算法)

- **Integration points**:
  - `src/agentic_rag/clients/graphiti_client.py` - MCP客户端
  - `backend/app/services/agent_service.py` - Agent服务层
  - `backend/app/clients/neo4j_client.py` - Neo4j客户端
  - Obsidian插件API调用层

### Enhancement Details

- **What's being added/changed**:
  1. 部署Neo4j图数据库替换JSON模拟
  2. 激活Graphiti MCP服务的写入功能
  3. 为14个Agent添加记忆写入触发机制
  4. 构建概念-学习事件-Canvas关系图

- **How it integrates**:
  - Agent执行完成后异步触发 `record_learning_episode()`
  - 通过MCP工具调用 `mcp__graphiti-memory__add_episode`
  - 写入Neo4j图数据库并建立关系

- **Success criteria**:
  - Neo4j服务运行并通过连接测试
  - 14个Agent全部触发记忆写入
  - 写入延迟 < 200ms (P95)
  - Obsidian插件可查询学习历史
  - 检验白板生成基于真实记忆数据

---

## Stories

### Story 12.M.1: Neo4j数据库部署与配置 [P0 BLOCKER]

**目标**: 部署并配置Neo4j图数据库

**验收标准**:
- [ ] AC1: Neo4j服务运行在 `bolt://localhost:7687`
- [ ] AC2: 创建 `canvas_memory` 数据库
- [ ] AC3: 配置用户认证 (NEO4J_USER, NEO4J_PASSWORD)
- [ ] AC4: 验证连接测试通过

**修改文件**:
- `.env` - 更新NEO4J_PASSWORD
- `scripts/init_neo4j.py` - 新建初始化脚本
- `backend/app/clients/neo4j_client.py` - 激活真实连接

---

### Story 12.M.2: Graphiti MCP服务激活 [P0 BLOCKER]

**目标**: 激活Graphiti MCP服务，替换JSON模拟

**验收标准**:
- [ ] AC1: MCP工具 `mcp__graphiti-memory__*` 可用
- [ ] AC2: `add_memory()` 调用真实MCP
- [ ] AC3: `add_episode()` 调用真实MCP
- [ ] AC4: `add_relationship()` 调用真实MCP
- [ ] AC5: 写入延迟 < 200ms

**关键修改点**:
```python
# src/agentic_rag/clients/graphiti_client.py L654-667
# 修改前: episode_id = f"episode_{datetime.now()...}"  # 模拟
# 修改后: result = await mcp__graphiti_memory__add_episode(content=content)
```

**修改文件**:
- `src/agentic_rag/clients/graphiti_client.py` L625-760 - 激活MCP调用
- `.claude/settings.local.json` - 确认MCP配置

---

### Story 12.M.3: Agent记忆写入触发机制 [P1]

**目标**: 所有14个Agent执行后触发记忆写入

**验收标准**:
- [ ] AC1: scoring-agent 完成后写入评分记录
- [ ] AC2: oral-explanation 完成后写入解释内容
- [ ] AC3: basic-decomposition 完成后写入拆解结果
- [ ] AC4: 其他11个Agent同样触发
- [ ] AC5: 异步非阻塞写入 (不影响响应时间)

**Agent写入映射**:
| Agent类型 | 记忆类型 | 重要性 |
|-----------|----------|--------|
| scoring-agent | 评分记录 | 8 |
| oral-explanation | 解释内容 | 7 |
| basic-decomposition | 拆解问题 | 7 |
| deep-decomposition | 深度拆解 | 8 |
| four-level-explanation | 四层解释 | 7 |
| example-teaching | 例题教学 | 6 |
| comparison-table | 对比表格 | 6 |
| clarification-path | 澄清路径 | 7 |
| memory-anchor | 记忆锚点 | 8 |
| question-decomposition | 问题拆解 | 7 |
| verification-question | 检验问题 | 8 |
| canvas-orchestrator | 编排记录 | 5 |
| graphiti-memory-agent | 记忆操作 | 9 |
| 其他 | 通用记录 | 5 |

**修改文件**:
- `backend/app/services/agent_service.py` - 添加记忆触发逻辑
- `backend/app/models/memory_schemas.py` - 添加AgentEpisode模型

---

### Story 12.M.4: 记忆关系图构建 [P1]

**目标**: 构建概念-学习事件-Canvas之间的关系图

**验收标准**:
- [ ] AC1: Canvas节点 ← CONTAINS → 概念
- [ ] AC2: 概念 ← RELATED_TO → 概念
- [ ] AC3: 学习事件 ← ABOUT → 概念
- [ ] AC4: 学习事件 ← OCCURRED_IN → Canvas
- [ ] AC5: 关系可通过Cypher查询

**Neo4j Schema**:
```cypher
// 节点类型
(:Canvas {name, path, created_at})
(:Concept {name, canvas, node_id})
(:LearningEpisode {id, agent_type, timestamp, content})

// 关系类型
(Canvas)-[:CONTAINS]->(Concept)
(Concept)-[:RELATED_TO]->(Concept)
(LearningEpisode)-[:ABOUT]->(Concept)
(LearningEpisode)-[:OCCURRED_IN]->(Canvas)
```

**修改文件**:
- `backend/app/clients/neo4j_client.py` - 添加关系创建方法
- `scripts/neo4j_schema.cypher` - 新建Schema定义

---

### Story 12.M.5: Obsidian插件集成验证 [P2]

**目标**: 验证插件能正确调用记忆API

**验收标准**:
- [ ] AC1: 插件可查询学习历史
- [ ] AC2: 插件可获取薄弱概念
- [ ] AC3: 检验白板生成正常工作
- [ ] AC4: WebSocket实时更新

**测试场景**:
1. 在Canvas中选择节点 → 调用scoring-agent → 验证记忆写入
2. 查询学习历史 → 验证返回正确记录
3. 生成检验白板 → 验证薄弱概念识别

---

### Story 12.M.6: 性能优化与监控 [P2]

**目标**: 确保记忆系统性能达标

**验收标准**:
- [ ] AC1: 单次写入 < 200ms (P95)
- [ ] AC2: 批量写入支持 (10条/秒)
- [ ] AC3: 查询延迟 < 100ms
- [ ] AC4: 添加Prometheus指标

**优化策略**:
1. 后台任务队列 (FastAPI BackgroundTasks)
2. 批量写入合并
3. 连接池管理
4. 写入失败重试

---

## Compatibility Requirements

- [x] Existing APIs remain unchanged (只添加新的记忆写入逻辑)
- [x] Database schema changes are backward compatible (新增Neo4j，不影响现有JSON)
- [x] UI changes follow existing patterns (Obsidian插件已有API调用框架)
- [x] Performance impact is minimal (异步非阻塞写入)

---

## Risk Mitigation

- **Primary Risk**: Neo4j连接失败导致记忆系统不可用
- **Mitigation**: 保留JSON fallback模式，当Neo4j不可用时自动降级
- **Rollback Plan**:
  1. 设置环境变量 `USE_JSON_FALLBACK=true` 回退到JSON模式
  2. 所有写入方法都有try-except包装，失败不影响主流程

---

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Existing functionality verified through testing
- [ ] Integration points working correctly
- [ ] Documentation updated appropriately
- [ ] No regression in existing features

### 具体验证清单

- [ ] Neo4j服务运行并通过连接测试
- [ ] 14个Agent全部触发记忆写入
- [ ] 写入延迟 < 200ms (P95)
- [ ] Obsidian插件可查询学习历史
- [ ] 检验白板生成基于真实记忆数据
- [ ] 所有集成测试通过
- [ ] 性能基准测试通过

---

## Story Manager Handoff

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing system running **FastAPI + LangGraph + Obsidian + Neo4j**
- Integration points:
  - `graphiti_client.py` MCP客户端
  - `agent_service.py` Agent服务层
  - `neo4j_client.py` Neo4j客户端
- Existing patterns to follow:
  - 异步非阻塞写入 (async/await)
  - 超时机制 (200ms timeout)
  - Fallback降级模式
- Critical compatibility requirements:
  - 保留JSON fallback
  - 不影响现有Agent响应时间
  - 兼容现有Obsidian插件API
- Each story must include verification that existing functionality remains intact

The epic should maintain system integrity while delivering **完整的记忆系统读写循环**."

---

## Appendix: Deep Investigation Summary

### 当前实现状态

| 组件 | 完成度 | 关键问题 |
|------|--------|----------|
| **Graphiti记忆系统** | 55% | 写入接口是骨架，MCP未部署 |
| **LangGraph集成** | 82% | 核心功能完整，写入链路待验证 |
| **三层记忆架构** | 70-75% | Layer 2 (LanceDB)最弱 |
| **Obsidian插件集成** | 50-60% | 框架完成，集成待验证 |

### 核心问题代码位置

1. **`_add_episode_via_mcp()` 骨架实现**
   - 文件: `src/agentic_rag/clients/graphiti_client.py` L625-677
   - 问题: 返回模拟ID，不调用真实MCP

2. **`add_memory()` 无实际写入**
   - 文件: `src/agentic_rag/clients/graphiti_client.py` L679-722
   - 问题: 只return True，没有MCP调用

3. **MCP可用性检测失败**
   - `self._mcp_available` 始终为 False
   - graphiti-core导入失败

### 文件修改清单

| 文件 | 行号 | 修改内容 |
|------|------|----------|
| `src/agentic_rag/clients/graphiti_client.py` | L625-760 | 激活MCP调用 |
| `backend/app/services/agent_service.py` | L300+ | 添加记忆触发 |
| `backend/app/clients/neo4j_client.py` | 全文 | 激活真实Neo4j |
| `.env` | NEO4J_PASSWORD | 配置密码 |
| `scripts/init_neo4j.py` | 新建 | Neo4j初始化脚本 |
| `scripts/neo4j_schema.cypher` | 新建 | Schema定义 |
