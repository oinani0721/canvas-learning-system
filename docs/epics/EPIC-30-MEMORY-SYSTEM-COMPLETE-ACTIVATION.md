# Epic 30: Memory System Complete Activation
# 记忆系统完整激活

**Epic ID**: EPIC-30
**类型**: Brownfield Enhancement
**优先级**: P0 (High)
**状态**: Ready for Implementation
**创建日期**: 2026-01-15
**预计工时**: ~60小时
**实施周期**: 4周

---

## Epic Goal

将Canvas Learning System已实现但未连接的3层记忆系统完整启用到生产环境，实现学习历史的持久化存储和智能复习建议功能。

**价值陈述**: 启用记忆系统后，用户的学习历史将被持久化存储到Neo4j知识图谱，支持基于艾宾浩斯遗忘曲线的智能复习建议，预计可提升学习效率25%。

---

## Background & Context

### 合并来源

此Epic由以下7个重叠Epic合并而成：

| 原Epic | 文件 | 状态 |
|--------|------|------|
| Epic 12.M | EPIC-12.M-Memory-System-Activation.md | Deprecated → 合并到30 |
| Epic 15 | EPIC-15-3LAYER-MEMORY-ACTIVATION.md | Deprecated → 合并到30 |
| Epic 20 | EPIC-20-THREE-LAYER-MEMORY-ACTIVATION.md | Deprecated → 合并到30 |
| Epic 22 | EPIC-22-MEMORY-SYSTEM.md | Deprecated → 合并到30 |
| Epic 22-R | EPIC-22-R-GRAPHITI-MEMORY-SYSTEM-DEPLOYMENT.md | Deprecated → 合并到30 |
| Epic 23(多学科) | EPIC-23-MEMORY-SYSTEM-MULTI-SUBJECT.md | Deprecated → 合并到30 |
| Epic 23(完整启用) | EPIC-23-MEMORY-SYSTEM-FULL-ACTIVATION.md | Deprecated → 合并到30 |

### 当前系统状态

| 组件 | 文件 | 行数 | 状态 |
|------|------|------|------|
| Neo4j客户端 | `backend/app/clients/neo4j_client.py` | 498 | JSON模拟 |
| MemoryService | `backend/app/services/memory_service.py` | 380 | 完全实现 |
| Memory API | `backend/app/api/v1/endpoints/memory.py` | 289 | 4端点完成 |
| Graphiti客户端 | `src/agentic_rag/clients/graphiti_temporal_client.py` | 649 | 完全实现 |
| MemoryQueryService | `src/services/MemoryQueryService.ts` | 624 | **未初始化** |
| GraphitiAssociationService | `src/services/GraphitiAssociationService.ts` | 521 | **未初始化** |

### 三层记忆架构

| 层级 | 技术 | 存储 | 用途 |
|------|------|------|------|
| Layer 1 (Temporal) | FSRS-4.5 | SQLite | 艾宾浩斯复习调度 |
| Layer 2 (Graphiti) | Neo4j知识图谱 | Neo4j | 概念关系存储 |
| Layer 3 (Semantic) | LanceDB向量库 | LanceDB | 向量检索 (可选) |

---

## Stories

### Story 30.1: Neo4j Docker环境部署 [P0 BLOCKER]

**目标**: 部署生产级Neo4j Docker容器

**验收标准**:
- AC-30.1.1: Docker Compose配置Neo4j 5.26容器 (bolt://localhost:7687)
- AC-30.1.2: NEO4J_URI/USER/PASSWORD环境变量配置
- AC-30.1.3: 数据迁移脚本清理现有JSON中的Unicode乱码
- AC-30.1.4: 健康检查端点返回Neo4j连接状态
- AC-30.1.5: 容器重启后数据持久化验证

**修改文件**:
- `docker-compose.yml` (新建或修改)
- `.env.example` (添加Neo4j配置)
- `backend/app/core/config.py` (添加Neo4j配置类)

**预计工时**: 4小时

---

### Story 30.2: Neo4jClient真实驱动实现 [P0 BLOCKER]

**目标**: 将Neo4jClient从JSON模拟升级到真实Bolt驱动

**验收标准**:
- AC-30.2.1: 使用`neo4j.AsyncGraphDatabase`替换JSON文件存储
- AC-30.2.2: 连接池配置 (max_pool_size=50, connection_timeout=30s)
- AC-30.2.3: 保留JSON fallback模式 (`NEO4J_MOCK=true`环境变量)
- AC-30.2.4: 单次写入延迟 < 200ms (P95)
- AC-30.2.5: 连接失败自动重试 (3次，指数退避)

**修改文件**:
- `backend/app/clients/neo4j_client.py` (重构~200行)
- `backend/requirements.txt` (确认neo4j>=5.0.0)

**预计工时**: 8小时

---

### Story 30.3: Memory API端点集成验证 [P1]

**目标**: 验证所有Memory API端点与真实Neo4j的集成，并添加缺失的健康检查端点

**验收标准**:
- AC-30.3.1: POST /api/v1/memory/episodes 写入Neo4j成功
- AC-30.3.2: GET /api/v1/memory/episodes 分页查询正确
- AC-30.3.3: GET /api/v1/memory/concepts/{id}/history 返回学习历史
- AC-30.3.4: GET /api/v1/memory/review-suggestions 返回FSRS优先级
- AC-30.3.5: GET /api/v1/memory/health 返回3层系统状态
- AC-30.3.6: **后端添加 `GET /api/v1/health/neo4j` 端点** (插件测试连接依赖)
- AC-30.3.7: **后端添加 `GET /api/v1/health/graphiti` 端点** (插件测试连接依赖)
- AC-30.3.8: **后端添加 `GET /api/v1/health/lancedb` 端点** (插件测试连接依赖)
- AC-30.3.9: **插件状态指示器改为调用真实健康检查API** (修复虚假状态显示)

**修改文件**:
- `backend/app/api/v1/endpoints/memory.py` (添加/health端点)
- `backend/app/api/v1/endpoints/health.py` (添加neo4j/graphiti/lancedb健康检查端点)
- `canvas-progress-tracker/obsidian-plugin/src/components/PluginSettingsTab.ts` (修复状态指示器)
- `backend/tests/integration/test_memory_api.py` (扩展测试)

**背景说明** (2026-01-15 深度调研发现):
> 当前插件设置面板中的"测试连接"按钮调用 `/api/v1/health/neo4j` 和 `/api/v1/health/graphiti`，
> 但这些端点在后端不存在（返回404）。状态指示器仅读取本地settings布尔值，
> 即使服务完全宕机也显示"✅ 已启用"，造成用户误解。

**预计工时**: 8小时 (原6小时 + 2小时修复UI幻觉问题)

---

### Story 30.4: Agent记忆写入触发机制 [P1]

**目标**: 为14个Agent添加自动记忆写入触发

**验收标准**:
- AC-30.4.1: 14个Agent执行完成后自动调用`record_learning_episode()`
- AC-30.4.2: 异步非阻塞写入，不影响Agent响应时间
- AC-30.4.3: 写入失败时静默降级，记录错误日志
- AC-30.4.4: Agent映射表配置化（哪些Agent触发哪种记忆类型）

**Agent触发映射表**:

| Agent类型 | 触发动作 | 记忆类型 |
|-----------|---------|---------|
| scoring-agent | 评分完成 | learning_event |
| four-level-explanation | 解释生成 | concept_explanation |
| verification-question | 问题生成 | verification_record |
| oral-explanation | 口语化解释 | oral_record |
| example-teaching | 示例教学 | example_record |
| deep-decomposition | 深度拆解 | decomposition_record |
| comparison-table | 对比生成 | comparison_record |
| memory-anchor | 记忆锚点 | anchor_record |
| clarification-path | 澄清路径 | clarification_record |
| basic-decomposition | 基础拆解 | basic_decomposition |
| question-decomposition | 问题拆解 | question_record |
| canvas-orchestrator | 编排完成 | orchestration_event |

**修改文件**:
- `backend/app/services/agent_service.py` (添加触发逻辑)
- `backend/app/core/agent_memory_mapping.py` (新建配置文件)

**预计工时**: 10小时

---

### Story 30.5: Canvas CRUD操作触发 [P1]

**目标**: Canvas节点/边操作自动触发学习事件记录

**验收标准**:
- AC-30.5.1: 创建Canvas节点时记录`node_created`事件
- AC-30.5.2: 创建边关系时记录`edge_created`事件
- AC-30.5.3: 节点内容更新时记录`node_updated`事件
- AC-30.5.4: 建立Canvas-Concept-LearningEpisode关系图

**修改文件**:
- `backend/app/services/canvas_service.py` (添加触发hooks)
- `backend/app/models/canvas_events.py` (新建事件模型)

**预计工时**: 8小时

---

### Story 30.6: 节点颜色变化监听 [P1]

**目标**: Obsidian插件监听Canvas节点颜色变化，自动触发记忆

**验收标准**:
- AC-30.6.1: 监听`.canvas`文件变化，检测节点颜色属性
- AC-30.6.2: 颜色映射规则：红→未掌握，黄→学习中，绿→已掌握，紫→待验证
- AC-30.6.3: 颜色变化时POST到`/api/v1/memory/episodes`
- AC-30.6.4: 500ms防抖机制避免事件风暴
- AC-30.6.5: 批量变化时合并为单次API调用

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/services/NodeColorChangeWatcher.ts` (新建~200行)
- `canvas-progress-tracker/obsidian-plugin/main.ts` (添加监听器初始化)

**预计工时**: 10小时

---

### Story 30.7: Obsidian插件记忆服务初始化 [P0 BLOCKER]

**目标**: 在插件main.ts中初始化所有记忆相关服务

**验收标准**:
- AC-30.7.1: `MemoryQueryService`在插件加载时异步初始化
- AC-30.7.2: `GraphitiAssociationService`在插件加载时异步初始化
- AC-30.7.3: `PriorityCalculatorService`接收真实`memoryResult`参数
- AC-30.7.4: 设置面板显示Neo4j连接状态和3层系统健康
- AC-30.7.5: 状态栏显示"记忆系统: ✅ 3/3层就绪"或降级状态
- AC-30.7.6: 提供`neo4jEnabled`总开关配置

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/main.ts` (添加~50行初始化代码)
- `canvas-progress-tracker/obsidian-plugin/src/settings/PluginSettingsTab.ts` (确认displayMemorySettings方法)

**预计工时**: 8小时

---

### Story 30.8: 多学科隔离与group_id支持 [P2]

**目标**: 实现Graphiti group_id多学科数据隔离

**验收标准**:
- AC-30.8.1: 每个学科使用独立的`group_id`命名空间
- AC-30.8.2: 学科自动推断规则：从Canvas路径提取（如`数学/离散数学.canvas` → `数学`）
- AC-30.8.3: API支持`?subject=数学`查询参数过滤
- AC-30.8.4: 手动覆盖：设置面板可配置学科映射

**修改文件**:
- `src/agentic_rag/clients/graphiti_temporal_client.py` (添加group_id参数)
- `backend/app/services/memory_service.py` (添加学科解析逻辑)
- `canvas-progress-tracker/obsidian-plugin/src/types/settings.ts` (添加学科映射配置)

**预计工时**: 6小时

---

## Implementation Phases

```
Phase 1: 基础设施 [Week 1]
├─ Story 30.1: Neo4j Docker部署 [P0]
└─ Story 30.2: Neo4jClient真实驱动 [P0]

Phase 2: 后端集成 [Week 2]
├─ Story 30.3: Memory API验证 [P1]
├─ Story 30.4: Agent记忆触发 [P1] (并行)
└─ Story 30.5: Canvas CRUD触发 [P1] (并行)

Phase 3: 插件集成 [Week 3]
├─ Story 30.7: 插件记忆服务初始化 [P0]
└─ Story 30.6: 节点颜色监听 [P1]

Phase 4: 高级功能 [Week 4]
└─ Story 30.8: 多学科隔离 [P2]
```

---

## Risk Assessment

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| Neo4j Docker启动失败 | 中 | JSON fallback模式，`NEO4J_MOCK=true` |
| Graphiti连接超时 | 中 | 500ms超时 + 本地缓存降级 |
| 插件初始化阻塞UI | 低 | 所有服务异步初始化 |
| 数据迁移丢失 | 低 | 迁移前备份JSON文件 |
| 事件风暴 | 中 | 500ms防抖 + 批量合并 |

**回滚时间**: < 1分钟（设置`NEO4J_ENABLED=false`环境变量）

---

## Definition of Done

- [ ] 所有8个Stories完成
- [ ] 所有AC通过验证
- [ ] 单元测试覆盖率 > 90%
- [ ] 集成测试全部通过
- [ ] 性能基准达标 (写入<200ms, 查询<100ms P95)
- [ ] 健康检查端点返回3层系统状态
- [ ] Obsidian状态栏显示记忆系统状态
- [ ] 部署文档更新

---

## Key File Locations

| 功能模块 | 文件路径 |
|---------|---------|
| Neo4j客户端 | `backend/app/clients/neo4j_client.py` |
| 记忆服务 | `backend/app/services/memory_service.py` |
| Memory API | `backend/app/api/v1/endpoints/memory.py` |
| Graphiti客户端 | `src/agentic_rag/clients/graphiti_temporal_client.py` |
| 插件主文件 | `canvas-progress-tracker/obsidian-plugin/main.ts` |
| 插件记忆服务 | `src/services/MemoryQueryService.ts` |
| 插件关联服务 | `src/services/GraphitiAssociationService.ts` |

---

## Story Manager Handoff

当准备实施时，请按以下顺序执行：

1. **Week 1**: Story 30.1 → Story 30.2 (顺序)
2. **Week 2**: Story 30.3 + 30.4 + 30.5 (并行)
3. **Week 3**: Story 30.7 → Story 30.6 (顺序)
4. **Week 4**: Story 30.8

使用 `/BMad:agents:dev` 或 `*create-brownfield-story` 开始实施具体Story。
