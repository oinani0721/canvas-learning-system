> **DEPRECATED** - 此Epic已合并到 [Epic 30: Memory System Complete Activation](./EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md)
>
> 合并日期: 2026-01-15 | 请参考Epic 30获取最新实施计划

---

# Epic: Memory System Full Activation - 记忆系统完整启用

**Epic ID**: Epic-23 (Brownfield Enhancement)
**创建日期**: 2026-01-15
**状态**: 待审批

---

## Epic 目标

将Canvas Learning System已实现但未连接的3层记忆系统完整启用到生产环境，实现学习历史的持久化存储和智能复习建议功能。

**价值陈述**: 启用记忆系统后，用户的学习历史将被持久化存储到Neo4j知识图谱，支持基于艾宾浩斯遗忘曲线的智能复习建议，预计可提升学习效率25%。

---

## 现有系统上下文

### 当前相关功能

Canvas Learning System已在Epic 12和Epic 22中实现了以下记忆系统组件：

| 层级 | 组件 | 实现文件 | 代码量 | 状态 |
|------|------|---------|--------|------|
| Agentic RAG层 | GraphitiTemporalClient | `src/agentic_rag/clients/graphiti_temporal_client.py` | 649行 | ✅ 完整实现 |
| 后端API层 | Memory API (4端点) | `backend/app/api/v1/endpoints/memory.py` | 289行 | ✅ 完整实现 |
| 服务层 | MemoryService | `backend/app/services/memory_service.py` | 380行 | ✅ 完整实现 |
| 存储层 | Neo4jClient | `backend/app/clients/neo4j_client.py` | 498行 | ⚠️ JSON模拟 |
| FSRS算法 | Temporal Memory | `src/temporal_memory.py` | - | ✅ 完整实现 |
| 插件端 | MemoryQueryService | `obsidian-plugin/src/services/MemoryQueryService.ts` | 623行 | ⚠️ 未初始化 |
| 插件端 | GraphitiAssociationService | `src/services/GraphitiAssociationService.ts` | 200+行 | ⚠️ 未初始化 |

### 技术栈

- **后端**: Python 3.11+, FastAPI, Pydantic
- **存储**: Neo4j 5.x (目标), JSON文件 (当前)
- **前端**: Obsidian插件 (TypeScript)
- **算法**: Graphiti (时序知识图谱), FSRS-4.5 (间隔重复)

### 集成点

- Obsidian Canvas UI → 后端Memory API
- MemoryService → Neo4jClient → Neo4j Database
- MemoryService → GraphitiTemporalClient → Graphiti Episodes
- MemoryQueryService → 3层记忆查询聚合

---

## 增强详情

### 正在添加/更改的内容

1. **Neo4j真实连接**: 将Neo4jClient从JSON文件模拟升级到真实Neo4j异步驱动
2. **后端服务集成**: MemoryService调用GraphitiTemporalClient实现双写
3. **插件服务初始化**: 在main.ts中初始化MemoryQueryService和GraphitiAssociationService
4. **健康检查**: 添加记忆系统健康检查端点和UI状态指示
5. **用户控制**: 提供记忆系统启用/禁用的设置开关

### 集成方式

```
┌─────────────────────────────────────────────────────────────┐
│                   Obsidian Canvas UI                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ 学习事件
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MemoryQueryService (插件端)                     │
│              - 3层记忆查询聚合                               │
│              - 优先级计算                                    │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               POST /api/v1/memory/episodes                  │
│               GET  /api/v1/memory/episodes                  │
│               GET  /api/v1/memory/concepts/{id}/history     │
│               GET  /api/v1/memory/review-suggestions        │
│               GET  /api/v1/memory/health (新增)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    MemoryService                            │
│                    - 学习事件记录                            │
│                    - 历史查询                                │
│                    - 复习建议生成                            │
└─────────┬───────────────────────────────────┬───────────────┘
          │                                   │
          ▼                                   ▼
┌─────────────────────────┐    ┌─────────────────────────────┐
│     Neo4jClient         │    │   GraphitiTemporalClient    │
│   (真实Neo4j驱动)        │    │   (时序知识图谱)            │
│   - User节点            │    │   - Episode存储             │
│   - Concept节点         │    │   - 时间范围查询             │
│   - LEARNED关系         │    │   - 实体类型查询             │
└─────────┬───────────────┘    └─────────────┬───────────────┘
          │                                   │
          ▼                                   ▼
┌─────────────────────────┐    ┌─────────────────────────────┐
│      Neo4j Database     │    │    Graphiti Knowledge Graph │
│   bolt://localhost:7687 │    │    (本地缓存 + 降级模式)     │
└─────────────────────────┘    └─────────────────────────────┘
```

### 成功标准

1. **Neo4j连接稳定**: 连接成功率 > 99.9%
2. **API响应时间**: P95 < 200ms
3. **数据一致性**: Neo4j和Graphiti数据同步成功率 > 99%
4. **用户体验**: 状态栏正确显示"记忆系统: ✅ 3/3层就绪"
5. **降级可靠**: Neo4j不可用时自动切换到JSON存储

---

## Stories

### Story 1: Neo4j生产环境配置与客户端升级

**目标**: 将Neo4jClient从JSON模拟升级到真实Neo4j连接

**修改文件**:
- `backend/app/clients/neo4j_client.py` - 添加真实Neo4j异步驱动
- `backend/app/core/config.py` - 添加Neo4j配置项
- `backend/requirements.txt` - 添加neo4j依赖
- `.env.example` - 添加Neo4j环境变量模板

**验收标准**:
- AC-1.1: Neo4j连接配置通过环境变量管理 (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
- AC-1.2: 支持连接池 (max_connection_pool_size=50) 和超时配置 (connection_timeout=30s)
- AC-1.3: 保留JSON降级模式 - 当Neo4j不可用时自动切换到JSON存储
- AC-1.4: 健康检查端点 `GET /api/v1/memory/health` 返回Neo4j连接状态
- AC-1.5: 单元测试覆盖连接、查询、降级三种场景

---

### Story 2: 后端记忆服务集成

**目标**: 连接MemoryService与GraphitiTemporalClient，实现学习事件双写

**修改文件**:
- `backend/app/services/memory_service.py` - 导入并调用GraphitiTemporalClient
- `backend/app/api/v1/endpoints/memory.py` - 添加健康检查端点
- `src/agentic_rag/clients/graphiti_temporal_client.py` - 可能的适配调整

**验收标准**:
- AC-2.1: `record_learning_event()` 同时写入Neo4j和Graphiti
- AC-2.2: 查询API聚合两个数据源的结果
- AC-2.3: `GET /api/v1/memory/health` 返回所有层的健康状态
- AC-2.4: Graphiti超时 (500ms) 时降级到仅Neo4j查询
- AC-2.5: 集成测试验证双写一致性

---

### Story 3: Obsidian插件记忆系统初始化

**目标**: 在插件主文件中初始化并连接所有记忆服务

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/main.ts` - `initializeManagers()` 添加服务初始化
- `canvas-progress-tracker/obsidian-plugin/src/components/PluginSettingsTab.ts` - 添加Neo4j设置UI
- `canvas-progress-tracker/obsidian-plugin/src/types/settings.ts` - 设置默认值调整

**验收标准**:
- AC-3.1: MemoryQueryService在插件加载时异步初始化
- AC-3.2: GraphitiAssociationService在插件加载时异步初始化
- AC-3.3: 设置面板显示Neo4j连接状态 (✅ 已连接 / ❌ 未连接)
- AC-3.4: 状态栏显示"记忆系统: ✅ 3/3层就绪"或具体错误信息
- AC-3.5: PriorityCalculatorService接收真实的memoryResult参数
- AC-3.6: 提供`neo4jEnabled`总开关控制功能启用/禁用

---

## 兼容性要求

- [x] 现有API端点签名保持不变
- [x] 数据库schema向后兼容 - JSON数据可迁移到Neo4j
- [x] UI变更遵循现有Obsidian插件设计语言
- [x] 性能影响最小 - 异步操作，不阻塞主线程

---

## 风险评估与缓解

| 风险 | 级别 | 概率 | 影响 | 缓解措施 |
|------|------|------|------|---------|
| Neo4j连接失败 | 中 | 15% | 高 | 保留JSON降级模式，自动切换 |
| Graphiti超时 | 中 | 20% | 中 | 500ms超时 + 本地缓存降级 |
| 数据迁移丢失 | 低 | 5% | 高 | 提供迁移脚本，先备份JSON数据 |
| 插件性能下降 | 低 | 10% | 中 | 异步初始化，不阻塞Obsidian UI |
| 配置错误 | 低 | 10% | 低 | 健康检查端点 + 明确错误提示 |

**主要风险**: Neo4j服务不稳定
**缓解策略**: 实现双模式存储架构 - Neo4j为主，JSON为备

---

## 回滚计划

1. **设置开关**: 在`settings.ts`中添加`memorySystemEnabled`总开关
2. **快速禁用**: 开关关闭时，跳过所有记忆服务初始化
3. **数据保留**: JSON存储作为备份数据源持续运行
4. **一键回滚**: 如需回滚，只需设置`neo4jEnabled: false`并重启插件

回滚预估时间: < 1分钟

---

## Definition of Done

- [ ] Story 1: Neo4j真实连接在生产环境稳定运行 (24小时无错误)
- [ ] Story 2: MemoryService双写功能验证通过
- [ ] Story 3: Obsidian插件正确初始化所有记忆服务
- [ ] 所有验收标准 (AC) 通过
- [ ] 现有功能回归测试通过 (无Breaking Changes)
- [ ] 健康检查端点 `GET /api/v1/memory/health` 返回正确状态
- [ ] Obsidian状态栏显示记忆系统运行状态
- [ ] 部署文档更新 (Neo4j配置指南)
- [ ] 无新增P0/P1级别Bug

---

## Story Manager 交接

请为此Brownfield Epic开发详细的用户故事。关键考虑事项：

- 这是对现有Canvas Learning System的增强，运行于 **Python 3.11+ / TypeScript** 技术栈
- 集成点: Obsidian插件 → FastAPI后端 → Neo4j/Graphiti
- 需要遵循的现有模式:
  - 后端服务依赖注入 (`get_neo4j_client()`, `get_memory_service()`)
  - 插件服务初始化在 `initializeManagers()` 方法中
  - 设置存储在 `settings.ts` 的 `CanvasReviewSettings` 接口
- 关键兼容性要求:
  - Neo4j不可用时自动降级到JSON存储
  - 所有异步操作有超时保护
- 每个Story必须包含验证现有功能不受影响的测试

Epic应在保持系统完整性的同时交付**3层记忆系统的完整启用**。

---

## 附录: 关键代码位置

### 后端代码

| 文件 | 行数 | 功能 |
|------|------|------|
| `backend/app/clients/neo4j_client.py` | 1-498 | Neo4j客户端 (需升级) |
| `backend/app/services/memory_service.py` | 1-380 | 记忆服务 (需集成) |
| `backend/app/api/v1/endpoints/memory.py` | 1-289 | Memory API端点 |
| `backend/app/core/config.py` | - | 配置管理 (需添加Neo4j) |
| `src/agentic_rag/clients/graphiti_temporal_client.py` | 1-649 | Graphiti时序客户端 |

### 插件代码

| 文件 | 行数 | 功能 |
|------|------|------|
| `obsidian-plugin/main.ts` | 332-429 | 服务初始化 (需修改) |
| `obsidian-plugin/src/services/MemoryQueryService.ts` | 1-623 | 记忆查询服务 |
| `obsidian-plugin/src/services/GraphitiAssociationService.ts` | 1-200+ | Graphiti关联服务 |
| `obsidian-plugin/src/types/settings.ts` | 307-351 | 记忆系统设置定义 |
| `obsidian-plugin/src/components/PluginSettingsTab.ts` | - | 设置UI (需添加Neo4j) |

### 数据文件

| 文件 | 功能 |
|------|------|
| `backend/data/neo4j_memory.json` | 当前JSON存储 (用于降级) |
| `backend/data/graphiti_edges.json` | Graphiti边数据 |
| `backend/data/learning_memories.json` | 学习记忆数据 |
