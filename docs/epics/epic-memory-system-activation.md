# Epic: Canvas 三层记忆系统启用

## Epic 元数据

| 字段 | 值 |
|------|-----|
| **Epic ID** | EPIC-MEM-001 |
| **类型** | Brownfield Enhancement |
| **优先级** | High |
| **预估 Stories** | 3 |
| **状态** | Draft |
| **创建日期** | 2026-01-15 |

---

## Epic 目标

正式启用 Canvas Learning System 的三层记忆架构（知识图谱 + 语义记忆 + 时序记忆），实现 Canvas 节点增量索引和学习行为实时记录，为个性化复习和薄弱点识别提供数据支撑。

---

## 背景与动机

### 现状分析

Canvas Learning System 的 Agentic RAG 架构已在 Epic 12 中完成实现：
- ✅ StateGraph 5路并行检索
- ✅ RRF融合算法 (k=60)
- ✅ 混合Reranking (80% BGE + 20% Cohere)
- ✅ 质量控制循环

**但三层记忆系统尚未正式启用**：

| 层级 | 名称 | 代码实现 | 激活状态 | 阻塞原因 |
|------|------|---------|---------|---------|
| Layer 1 | 知识图谱 (Graphiti) | 90% | ⚠️ 未激活 | Neo4j 配置缺失 |
| Layer 2 | 语义记忆 (LanceDB) | 80% | ⚠️ 测试模式 | 需要依赖安装 |
| Layer 3 | 时序记忆 (FSRS) | 95% | ✅ 已激活 | 无 |

### 业务价值

1. **个性化复习**: 基于 FSRS 算法推荐最佳复习时间
2. **薄弱点识别**: 通过知识图谱分析概念掌握程度
3. **增量更新**: 避免全量重建索引，提升用户体验
4. **学习追踪**: 记录学习行为，支持学习分析

---

## 技术方案

### 系统架构

```
Obsidian Canvas
     │
     ▼ (文件变更事件)
┌────────────────────────────────────────────┐
│         Obsidian Plugin (TypeScript)        │
│  ├── MemoryAPI.ts (新增)                    │
│  └── ApiClient.ts (复用)                    │
└─────────────────┬──────────────────────────┘
                  │ REST API
                  ▼
┌────────────────────────────────────────────┐
│           FastAPI Backend                   │
│  ├── config.py (添加 Neo4j/LanceDB 配置)    │
│  ├── memory_service.py                      │
│  └── memory.py (API endpoints)              │
└─────────────────┬──────────────────────────┘
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Neo4j   │ │ LanceDB │ │ SQLite  │
│ Layer 1 │ │ Layer 2 │ │ Layer 3 │
│ 知识图谱│ │ 语义记忆│ │ 时序记忆│
└─────────┘ └─────────┘ └─────────┘
```

### 关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 图数据库 | Neo4j (Docker) | 本地部署，数据隐私 |
| 向量数据库 | LanceDB | 原生混合检索，低延迟 |
| 时序算法 | FSRS-4.5 | 开源，效果优于 SM-2 |
| 增量索引 | Hash 比对 + Upsert | 避免全量重建 |

---

## Stories

### Story 1: 环境配置与依赖

**目标**: 完成 Neo4j 和 LanceDB 的配置，确保三层记忆系统可连接

**验收标准**:
- [ ] AC-1.1: `backend/app/config.py` 添加 Neo4j 配置项
- [ ] AC-1.2: `backend/.env` 模板包含所有必要环境变量
- [ ] AC-1.3: Docker 启动脚本可成功启动 Neo4j 容器
- [ ] AC-1.4: Python 依赖安装无冲突

**关键文件**:
- `backend/app/config.py`
- `backend/.env`
- `docker-compose.memory.yml` (新建)

---

### Story 2: 三层记忆激活验证

**目标**: 验证三层记忆系统可正常初始化和连接

**验收标准**:
- [ ] AC-2.1: GraphitiClient 成功连接 Neo4j (`bolt://localhost:7687`)
- [ ] AC-2.2: LanceDB 表结构初始化完成 (`canvas_explanations`, `canvas_concepts`, `canvas_nodes`)
- [ ] AC-2.3: FSRS 时序记忆验证通过 (`learning_behavior.db`)
- [ ] AC-2.4: 健康检查端点 `/health/memory` 返回三层状态

**关键文件**:
- `backend/app/clients/neo4j_client.py`
- `src/agentic_rag/clients/lancedb_client.py`
- `src/temporal_memory.py`
- `backend/app/api/v1/endpoints/health.py`

---

### Story 3: 增量索引与插件集成

**目标**: 实现 Canvas 节点增量索引，集成到 Obsidian 插件

**验收标准**:
- [ ] AC-3.1: `upsert_canvas_nodes()` 方法实现增量更新
- [ ] AC-3.2: 增量索引延迟 < 1s/节点
- [ ] AC-3.3: Obsidian 插件 `MemoryAPI.ts` 可调用后端记忆服务
- [ ] AC-3.4: Canvas 文件变更自动触发增量索引 (防抖 500ms)

**关键文件**:
- `src/agentic_rag/clients/lancedb_client.py`
- `canvas-progress-tracker/obsidian-plugin/src/api/MemoryAPI.ts` (新建)
- `canvas-progress-tracker/obsidian-plugin/main.ts`

---

## 兼容性要求

- [x] 现有 APIs 保持不变 (仅添加新端点)
- [x] 数据库 schema 变更向后兼容 (新增表，不修改现有表)
- [x] UI 变更遵循现有模式 (复用 ApiClient 基础设施)
- [x] 性能影响最小 (增量操作，非全量重建)

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 | 回滚方案 |
|------|------|------|---------|---------|
| Neo4j 连接失败 | 中 | 高 | 提供详细错误日志 | 降级到 JSON 文件存储 |
| LanceDB 性能问题 | 低 | 中 | 减少批量大小 | 禁用语义检索 |
| 插件兼容性 | 低 | 中 | 保留旧版备份 | 回退到备份版本 |

---

## 性能指标

| 指标 | 目标值 | 验证方法 |
|------|--------|---------|
| Graphiti 查询延迟 | < 200ms | `time curl /api/v1/memory/search` |
| LanceDB P95 延迟 | < 400ms | 性能测试脚本 |
| 增量索引延迟 | < 1s/节点 | Canvas 变更触发测试 |
| 总 RAG 延迟 | < 10s | 端到端检验白板生成 |

---

## Definition of Done

- [ ] 所有 Stories 完成，验收标准满足
- [ ] 单元测试通过 (`pytest backend/tests/unit/test_memory_service.py`)
- [ ] E2E 测试通过 (`pytest tests/bdd/test_three_layer_memory_agentic_rag.py`)
- [ ] 现有功能无回归
- [ ] 文档更新完成
- [ ] Code Review 通过

---

## Story Manager 交接

> **Story Manager Handoff:**
>
> "请为此棕地 Epic 开发详细的用户故事。关键考虑：
>
> - 这是对现有运行系统的增强，技术栈为 **FastAPI + LangGraph + Neo4j + LanceDB + FSRS**
> - 集成点: `config.py` (配置)、`backend/app/clients/` (客户端)、`obsidian-plugin/src/api/` (插件)
> - 需要遵循的现有模式: Pydantic Settings、ApiClient 封装、健康检查端点
> - 关键兼容性要求: 不修改现有 API 接口，仅添加新端点
> - 每个 Story 必须包含验证，确保现有功能完整性
>
> Epic 目标: 在保持系统完整性的同时，正式启用三层记忆系统并实现增量索引功能。"

---

## 参考资料

- [三层记忆系统设计文档](../architecture/three-layer-memory-system.md)
- [Agentic RAG StateGraph 实现](../../src/agentic_rag/state_graph.py)
- [FSRS 算法说明](https://github.com/open-spaced-repetition/fsrs4anki)
- [LanceDB 文档](https://lancedb.github.io/lancedb/)
