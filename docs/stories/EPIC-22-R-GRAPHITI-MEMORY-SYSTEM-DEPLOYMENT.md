> **DEPRECATED** - 此Epic已合并到 [Epic 30: Memory System Complete Activation](../epics/EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md)
>
> 合并日期: 2026-01-15 | 请参考Epic 30获取最新实施计划

---

# Epic 22-R: Graphiti 记忆系统完整部署 - Brownfield Enhancement

**创建日期**: 2026-01-15
**创建者**: John (PM Agent)
**状态**: Draft
**Epic 类型**: 棕地增强 (Brownfield Enhancement)

---

## Epic 标题

**Graphiti Memory System Complete Deployment** - Brownfield Enhancement

---

## Epic 目标

将 Canvas Learning System 的记忆系统从 JSON 文件存储迁移到真实的 Neo4j + Graphiti 架构，实现节点颜色变化自动触发记忆存储，完成 3 层记忆系统 (Temporal + Graphiti + Semantic) 的协同工作。

**价值**: 让用户的学习进度能够持久化存储在图数据库中，支持跨会话的学习历史追踪和艾宾浩斯复习调度。

---

## Epic 描述

### 现有系统上下文

- **当前相关功能**:
  - 后端 GraphitiClient (`backend/app/clients/graphiti_client.py`) 已实现 `add_episode()`, `add_relationship()` 等方法
  - Neo4jClient (`backend/app/clients/neo4j_client.py`) 使用 JSON 文件模拟 Cypher 查询
  - MemoryService (`backend/app/services/memory_service.py`) 提供 `record_learning_event()` 方法
  - Obsidian 插件已有 MemoryQueryService、GraphitiAssociationService

- **技术栈**:
  - 后端: FastAPI + Python 3.11
  - 数据库: 当前 JSON 文件 → 目标 Neo4j 5.15.0
  - 插件: TypeScript + Obsidian API
  - 图谱: Graphiti MCP Tools

- **集成点**:
  - `backend/data/neo4j_memory.json` → Neo4j Docker
  - Obsidian 插件 `main.ts` → 后端 `/api/v1/memory/episodes`
  - `.claude/settings.local.json` → Graphiti MCP 配置

### 增强详情

- **添加/变更内容**:
  1. 部署 Neo4j Docker 容器作为持久化存储
  2. 重构 Neo4jClient 使用真实 AsyncGraphDatabase 驱动
  3. 在 Obsidian 插件中添加节点颜色变化事件监听器
  4. 实现 MemoryCoordinator 统一 3 层记忆访问

- **集成方式**:
  - Docker Compose 管理 Neo4j 服务
  - 后端通过 Bolt 协议连接 Neo4j (端口 7687)
  - 插件通过 HTTP API 调用后端记忆服务
  - MCP 工具直接操作 Neo4j 图数据库

- **成功标准**:
  - [ ] Neo4j 数据库启动并通过健康检查
  - [ ] 28 个现有概念从 JSON 迁移到 Neo4j
  - [ ] 节点颜色变化 (红→绿/紫) 自动触发学习事件记录
  - [ ] MCP 工具 `add_memory`, `search_memories` 操作 Neo4j

---

## Stories

### Story 22-R.1: Neo4j Docker 部署与配置

**优先级**: P1 | **预估工时**: 8h | **依赖**: 无

**描述**: 部署 Neo4j 数据库 Docker 容器，配置连接参数，创建数据迁移脚本。

**验收标准**:
- [ ] AC-1: `docker-compose.yml` 包含 Neo4j 5.15.0 服务，端口 7474 (HTTP) / 7687 (Bolt)
- [ ] AC-2: `backend/app/config.py` 添加 NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD 配置
- [ ] AC-3: 创建 `backend/scripts/migrate_json_to_neo4j.py` 迁移脚本
- [ ] AC-4: `GET /api/v1/health` 端点返回 Neo4j 连接状态
- [ ] AC-5: 迁移后 Neo4j 中包含 28 个 Concept 节点和相应 LEARNED 关系

---

### Story 22-R.2: 真实 Neo4j 客户端实现

**优先级**: P1 | **预估工时**: 10h | **依赖**: 22-R.1

**描述**: 将 Neo4jClient 从 JSON 文件模拟重构为使用真实 `neo4j.AsyncGraphDatabase` 驱动。

**验收标准**:
- [ ] AC-1: Neo4jClient 使用 `neo4j.AsyncGraphDatabase` 异步驱动
- [ ] AC-2: `create_learning_relationship()` 执行真实 Cypher MERGE 语句
- [ ] AC-3: `get_review_suggestions()` 从 Neo4j 查询待复习概念
- [ ] AC-4: 配置连接池大小 (默认 50)
- [ ] AC-5: Neo4j 不可用时优雅降级到 JSON 存储 (保持现有功能)

---

### Story 22-R.3: Graphiti MCP 真实集成

**优先级**: P1 | **预估工时**: 8h | **依赖**: 22-R.1

**描述**: 连接 Graphiti MCP 工具到真实 Neo4j 后端，使 Claude Code 的记忆工具能持久化数据。

**验收标准**:
- [ ] AC-1: `.claude/settings.local.json` MCP 配置指向 Neo4j 连接
- [ ] AC-2: `mcp__graphiti-memory__add_memory` 工具将数据存储到 Neo4j
- [ ] AC-3: `mcp__graphiti-memory__search_memories` 工具从 Neo4j 查询
- [ ] AC-4: `mcp__graphiti-memory__list_memories` 返回 Neo4j 中的记忆列表
- [ ] AC-5: 创建 `docs/guides/graphiti-mcp-setup.md` 设置文档

---

### Story 22-R.4: 节点颜色变化事件触发器 ⭐

**优先级**: P1 | **预估工时**: 12h | **依赖**: 22-R.2

**描述**: 在 Obsidian 插件中添加 Canvas 文件变化监听器，检测节点颜色变化并自动记录学习进度。

**验收标准**:
- [ ] AC-1: 插件注册 `vault.on('modify')` 监听 `.canvas` 文件变化
- [ ] AC-2: 颜色变化检测比较修改前后的节点颜色状态
- [ ] AC-3: 红→绿 (`#fb464c` → `#a0e2a8`) 触发 MASTERED 学习事件
- [ ] AC-4: 红→紫 (`#fb464c` → `#bba8f6`) 触发 PARTIAL_UNDERSTANDING 事件
- [ ] AC-5: 后端 `POST /api/v1/memory/episodes` 接收并存储学习事件
- [ ] AC-6: 实现 500ms 防抖避免事件风暴

**颜色映射规则**:
| 变化前 | 变化后 | 事件类型 |
|--------|--------|----------|
| #fb464c (红) | #a0e2a8 (绿) | MASTERED |
| #fb464c (红) | #bba8f6 (紫) | PARTIAL_UNDERSTANDING |
| #bba8f6 (紫) | #a0e2a8 (绿) | IMPROVED |

---

### Story 22-R.5: 3层记忆协调服务

**优先级**: P2 | **预估工时**: 10h | **依赖**: 22-R.2, 22-R.3

**描述**: 创建 MemoryCoordinator 统一访问 Temporal、Graphiti、Semantic 三层记忆。

**验收标准**:
- [ ] AC-1: 创建 `backend/app/services/memory_coordinator.py`
- [ ] AC-2: Temporal 层: 从 Neo4j 获取 FSRS 复习调度数据
- [ ] AC-3: Graphiti 层: 查询知识图谱概念关系
- [ ] AC-4: Semantic 层: 向量相似搜索 (Feature Flag 控制，可选)
- [ ] AC-5: Agent 服务使用 MemoryCoordinator 获取增强上下文

---

## 兼容性要求

- [x] 现有 API 保持不变 (所有 `/api/v1/*` 端点兼容)
- [x] 数据库 Schema 变更向后兼容 (JSON → Neo4j 迁移，保留原始 JSON 备份)
- [x] UI 变更遵循现有模式 (无 UI 变更)
- [x] 性能影响最小 (Neo4j 查询目标 < 200ms)

---

## 风险缓解

| 主要风险 | 缓解措施 |
|---------|---------|
| Neo4j Docker 在 Windows 11 失败 | 提供 WSL2 备选部署方案 |
| 数据迁移损坏现有 JSON | 迁移前自动备份 `neo4j_memory.json` |
| Obsidian 事件监听导致性能问题 | 500ms 防抖 + 仅监听 .canvas 文件 |
| MCP 版本不兼容 | 锁定 graphiti-core==0.6.0 |

**回滚计划**:
1. 保留 `neo4j_memory.json` 备份文件
2. Neo4jClient 保留 JSON 降级代码路径
3. 插件事件监听可通过设置禁用
4. docker-compose down 即可停止 Neo4j

---

## 完成定义 (Definition of Done)

- [ ] 所有 5 个 Story 完成并通过验收标准
- [ ] 现有功能通过回归测试验证
- [ ] 集成点正常工作 (插件→后端→Neo4j)
- [ ] 文档更新 (MCP 设置指南、部署说明)
- [ ] 无现有功能回归

---

## 验证清单

```powershell
# 1. 启动 Neo4j
docker-compose up -d neo4j

# 2. 验证健康
curl http://localhost:8000/api/v1/health

# 3. 运行迁移
python backend/scripts/migrate_json_to_neo4j.py

# 4. 验证 Neo4j 数据 (浏览器打开 http://localhost:7474)
# 执行 Cypher: MATCH (n:Concept) RETURN count(n)  -- 应返回 28

# 5. 运行集成测试
cd backend && python -m pytest tests/integration/test_neo4j_client.py -v

# 6. 构建部署插件
cd canvas-progress-tracker/obsidian-plugin && npm run build
Copy-Item main.js "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\" -Force

# 7. 手动测试颜色变化
# 在 Obsidian 中打开 Canvas，将红色节点改为绿色
# 检查后端日志: POST /api/v1/memory/episodes 应有记录
```

---

## Story Manager 交接

**Story Manager Handoff:**

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing system running **FastAPI + TypeScript Obsidian Plugin**
- Integration points:
  - `backend/app/clients/neo4j_client.py` → Neo4j Docker
  - `canvas-progress-tracker/obsidian-plugin/main.ts` → Backend API
  - `.claude/settings.local.json` → Graphiti MCP
- Existing patterns to follow:
  - AsyncClient pattern in `backend/app/clients/`
  - Service layer pattern in `backend/app/services/`
  - Obsidian Plugin event registration in `main.ts onload()`
- Critical compatibility requirements:
  - Neo4j 不可用时降级到 JSON 存储
  - 现有 API 端点保持兼容
- Each story must include verification that existing functionality remains intact

The epic should maintain system integrity while delivering **完整的 Graphiti 记忆系统部署**."

---

## 附录: 关键文件清单

| 文件路径 | 操作类型 | Story |
|---------|---------|-------|
| `docker-compose.yml` | 新建/修改 | 22-R.1 |
| `backend/app/config.py` | 修改 (添加 5 配置) | 22-R.1 |
| `backend/.env.example` | 修改 | 22-R.1 |
| `backend/scripts/migrate_json_to_neo4j.py` | 新建 | 22-R.1 |
| `backend/app/clients/neo4j_client.py` | 重构 (~200 行) | 22-R.2 |
| `backend/tests/integration/test_neo4j_client.py` | 新建 | 22-R.2 |
| `.claude/settings.local.json` | 验证/修改 | 22-R.3 |
| `docs/guides/graphiti-mcp-setup.md` | 新建 | 22-R.3 |
| `canvas-progress-tracker/obsidian-plugin/main.ts` | 修改 (~50 行) | 22-R.4 |
| `canvas-progress-tracker/obsidian-plugin/src/services/NodeColorChangeWatcher.ts` | 新建 (~200 行) | 22-R.4 |
| `backend/app/services/memory_coordinator.py` | 新建 (~250 行) | 22-R.5 |
| `backend/app/services/context_enrichment_service.py` | 修改 | 22-R.5 |
