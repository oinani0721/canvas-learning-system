> **DEPRECATED** - 此Epic已合并到 [Epic 30: Memory System Complete Activation](./EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md)
>
> 合并日期: 2026-01-15 | 请参考Epic 30获取最新实施计划

---
document_type: "Epic"
version: "1.0.0"
created_date: "2026-01-15"
status: "deprecated"
epic_type: "brownfield"
---

# Epic 23: 启用 Graphiti 记忆系统 + 多学科隔离

**Epic ID**: Epic-23
**Epic 类型**: 棕地增强 (Brownfield Enhancement)
**优先级**: P1
**预计工作量**: 14 小时
**状态**: 待实施
**创建日期**: 2026-01-15
**负责 PM**: John (PM Agent)

---

## Epic 目标

启用 Canvas Learning System 的 Graphiti/Neo4j 记忆系统，并实现基于 `group_id` 的多学科数据隔离，使不同学科的学习历史可以独立存储和查询，同时支持跨学科检索。

---

## 现有系统上下文

### 当前相关功能

| 组件 | 文件路径 | 行数 | 当前状态 |
|------|---------|------|---------|
| Memory Service | `backend/app/services/memory_service.py` | 390 | ✅ 已实现，使用 JSON 模拟 |
| Neo4j Client | `backend/app/clients/neo4j_client.py` | 498 | ✅ 已实现，JSON 存储 |
| Graphiti Client | `backend/app/clients/graphiti_client.py` | 754 | ✅ 已实现，边同步功能 |
| Memory API | `backend/app/api/v1/endpoints/memory.py` | 289 | ✅ 4 个 REST 端点 |
| ADR 文档 | `docs/architecture/decisions/0003-graphiti-memory.md` | 263 | ✅ 架构决策已记录 |
| Epic 22 PRD | `docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md` | 700 | ✅ 详细规划已完成 |

### 技术栈

- **后端**: FastAPI (Python 3.11+)
- **数据库**: Neo4j 5.26 (待部署)
- **知识图谱**: Graphiti (Zep AI)
- **前端**: Obsidian 插件 (TypeScript)
- **部署**: Docker Compose

### 集成点

1. **Memory Service** → **Neo4j Client** → **Neo4j Database**
2. **Memory Service** → **Graphiti Client** → **Graphiti MCP Server**
3. **Obsidian Plugin** → **Memory API** → **Memory Service**

---

## 增强详情

### 需要添加/变更的内容

1. **Neo4j Docker 部署**：创建 `docker-compose.yml` 一键启动 Neo4j
2. **真实数据库连接**：替换 JSON 模拟为 Bolt 协议连接
3. **多学科隔离**：使用 Graphiti `group_id` 实现学科命名空间
4. **学科自动推断**：从 Canvas 路径自动提取学科标识

### 集成方式

- 遵循现有 Memory Service 架构模式
- 保持 API 端点向后兼容
- 新增 `subject` 查询参数而非破坏现有接口

### 成功标准

- [ ] Neo4j 服务可通过 `docker compose up -d` 启动
- [ ] 学习事件能够持久化到 Neo4j
- [ ] 不同学科的数据查询时正确隔离
- [ ] 跨学科查询能够返回所有相关数据
- [ ] 性能：单学科查询 < 500ms

---

## Stories

### Story 23.1: Neo4j Docker 环境部署

**Story ID**: Story-23.1
**预计时间**: 3 小时
**优先级**: P0

**用户故事**:
```
作为开发者/用户
我希望能够一键启动 Neo4j 数据库
以便系统能够存储长期学习记忆
```

**验收标准 (AC)**:
- [ ] AC-23.1.1: `docker-compose.yml` 包含 Neo4j 5.26 + APOC 插件配置
- [ ] AC-23.1.2: `backend/.env.example` 包含完整 Neo4j 配置模板
- [ ] AC-23.1.3: 运行 `docker compose up -d neo4j` 后服务在 `localhost:7687` 可访问
- [ ] AC-23.1.4: 提供 Windows PowerShell 启动脚本 `scripts/start-neo4j.ps1`
- [ ] AC-23.1.5: Neo4j Browser 可通过 `localhost:7474` 访问

**关键文件**:
- `docker-compose.yml` (新增)
- `backend/.env.example` (修改)
- `scripts/start-neo4j.ps1` (新增)

**技术规格**:
```yaml
# docker-compose.yml 核心配置
services:
  neo4j:
    image: neo4j:5.26.0
    ports:
      - "7474:7474"  # HTTP Browser
      - "7687:7687"  # Bolt Protocol
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-canvas123}
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
```

---

### Story 23.2: Neo4j 真实连接替换 JSON 模拟

**Story ID**: Story-23.2
**预计时间**: 4 小时
**优先级**: P0
**依赖**: Story 23.1

**用户故事**:
```
作为系统
我希望能够连接到真实的 Neo4j 数据库
以便学习数据能够持久化存储
```

**验收标准 (AC)**:
- [ ] AC-23.2.1: `Neo4jClient` 支持真实 Bolt 协议连接
- [ ] AC-23.2.2: 保留 JSON 模式作为开发 fallback（通过 `NEO4J_MOCK=true` 环境变量）
- [ ] AC-23.2.3: 连接池配置（最大 50 连接，超时 30 秒）
- [ ] AC-23.2.4: 启动时自动创建索引（concept_name, timestamp, user_id）
- [ ] AC-23.2.5: 健康检查 API `/api/v1/health/neo4j` 返回连接状态

**关键文件**:
- `backend/app/clients/neo4j_client.py` (修改)
- `backend/app/config.py` (修改)
- `backend/app/api/v1/endpoints/health.py` (修改)

**配置规格**:
```python
# backend/app/config.py 新增
NEO4J_URI: str = Field(default="bolt://localhost:7687")
NEO4J_USERNAME: str = Field(default="neo4j")
NEO4J_PASSWORD: str = Field(default="")
NEO4J_DATABASE: str = Field(default="neo4j")
NEO4J_MAX_POOL_SIZE: int = Field(default=50)
NEO4J_MOCK: bool = Field(default=False)  # 开发模式 fallback
```

---

### Story 23.3: Graphiti `group_id` 多学科支持

**Story ID**: Story-23.3
**预计时间**: 5 小时
**优先级**: P1
**依赖**: Story 23.2

**用户故事**:
```
作为学习者
我希望不同学科的学习记录能够隔离存储
以便我可以针对特定学科查询学习历史
```

**验收标准 (AC)**:
- [ ] AC-23.3.1: `GraphitiClient` 所有操作支持 `group_id` 参数
- [ ] AC-23.3.2: 自动推断逻辑：`数学/离散数学.canvas` → `group_id="数学"`
- [ ] AC-23.3.3: 支持手动覆盖：`.canvas-subject.json` 配置文件
- [ ] AC-23.3.4: 搜索时支持多 `group_id`：`search(group_ids=["数学", "物理"])`
- [ ] AC-23.3.5: Memory API 端点支持 `subject` 查询参数

**关键文件**:
- `backend/app/clients/graphiti_client.py` (修改)
- `backend/app/services/memory_service.py` (修改)
- `backend/app/api/v1/endpoints/memory.py` (修改)
- `backend/app/utils/subject_inference.py` (新增)

**学科推断规则**:
| Canvas 路径 | 推断的 group_id |
|------------|-----------------|
| `数学/离散数学.canvas` | `数学` |
| `物理/力学/牛顿定律.canvas` | `物理` |
| `托福/阅读/passage1.canvas` | `托福` |
| `test.canvas` (根目录) | `default` |

**API 变更**:
```
# 现有 API (保持兼容)
GET /api/v1/memory/episodes

# 新增查询参数
GET /api/v1/memory/episodes?subject=数学
GET /api/v1/memory/episodes?subject=数学,物理  # 多学科
```

---

### Story 23.4: 端到端验证测试

**Story ID**: Story-23.4
**预计时间**: 2 小时
**优先级**: P1
**依赖**: Story 23.3

**用户故事**:
```
作为开发者
我希望有完整的集成测试
以便确保记忆系统正常工作
```

**验收标准 (AC)**:
- [ ] AC-23.4.1: 集成测试：不同学科数据隔离正确
- [ ] AC-23.4.2: 性能测试：单学科查询 < 500ms
- [ ] AC-23.4.3: API 测试：POST/GET `/api/v1/memory/episodes` 正常
- [ ] AC-23.4.4: 文档更新：启用记忆系统指南

**关键文件**:
- `backend/tests/integration/test_memory_multi_subject.py` (新增)
- `docs/guides/memory-system-setup.md` (新增)

**测试场景**:
1. 存储"数学"学科的学习事件 → 验证存储成功
2. 存储"物理"学科的学习事件 → 验证存储成功
3. 查询"数学"学科 → 验证只返回数学相关数据
4. 查询所有学科 → 验证返回全部数据
5. 跨学科关联查询 → 验证 `group_ids` 参数工作

---

## 兼容性要求

- [x] 现有 Memory API 保持向后兼容
- [x] 新增 `subject` 参数为可选，不影响现有调用
- [x] JSON 模拟模式保留，支持无 Neo4j 环境开发
- [x] Obsidian 插件现有功能不受影响

---

## 风险缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| Neo4j Docker 启动失败 | 低 | 高 | 提供详细错误日志，保留 JSON fallback |
| 学科推断不准确 | 中 | 低 | 支持手动覆盖配置 |
| 性能不达标 | 低 | 中 | 预建索引，使用连接池 |
| 数据迁移丢失 | 中 | 高 | 现有 JSON 数据自动导入脚本 |

**回滚计划**:
1. 设置 `NEO4J_MOCK=true` 即可回退到 JSON 模式
2. 所有变更都是增量添加，不删除现有代码
3. Docker 容器可随时停止，不影响其他服务

---

## Definition of Done

- [ ] 所有 Stories 完成，验收标准全部通过
- [ ] 现有功能通过回归测试
- [ ] 集成点正常工作
- [ ] 文档更新完成
- [ ] 无现有功能退化

---

## Story Manager 移交说明

> **移交给 Story Manager**:
>
> "请为此棕地 Epic 开发详细的用户故事。关键考虑：
>
> - 这是对现有系统的增强，运行于 FastAPI + Obsidian TypeScript 技术栈
> - 集成点：Neo4j Client → Memory Service → Memory API
> - 现有模式遵循：Service + Client 分层架构，依赖注入
> - 关键兼容性要求：保持现有 API 向后兼容
> - 每个 Story 必须包含验证现有功能完整性的测试
>
> Epic 目标是在保持系统完整性的同时，交付完整的记忆系统启用功能。"

---

## 参考资料

- [Graphiti Graph Namespacing](https://help.getzep.com/graphiti/core-concepts/graph-namespacing)
- [Neo4j Multi-Tenancy](https://neo4j.com/developer/multi-tenancy-worked-example/)
- [ADR-0003: Graphiti Memory](docs/architecture/decisions/0003-graphiti-memory.md)
- [Epic 22 PRD](docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md)

---

## 变更历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|---------|
| 1.0.0 | 2026-01-15 | PM Agent (John) | 初始创建 |
