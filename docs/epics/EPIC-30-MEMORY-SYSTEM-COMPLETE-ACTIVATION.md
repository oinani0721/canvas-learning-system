# Epic 30: Memory System Complete Activation
# 记忆系统完整激活

**Epic ID**: EPIC-30
**类型**: Brownfield Enhancement
**优先级**: P0 (High)
**状态**: 16/24 Stories Done (67%), Gate: FAIL — 3 Deferred (30.17-30.19), 5 Pending (30.20-30.24), P0 覆盖率 80%
**创建日期**: 2026-01-15
**最后审查**: 2026-02-10 (对抗性审查)
**预计工时**: ~105小时 (原60h + 修复45h)
**实施周期**: 6周 (原4周 + 对抗性审查修复2周)

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

> **最后更新**: 2026-02-10 (对抗性审查后同步)

| 组件 | 文件 | 行数 | 状态 |
|------|------|------|------|
| Neo4j客户端 | `backend/app/clients/neo4j_client.py` | ~2011 | ✅ Bolt驱动 + JSON fallback |
| MemoryService | `backend/app/services/memory_service.py` | ~1498 | ✅ 完全实现 (含双写/幂等/批量) |
| Memory API | `backend/app/api/v1/endpoints/memory.py` | ~389 | ✅ 7端点完成 |
| Health API | `backend/app/api/v1/endpoints/health.py` | ~1731 | ✅ Neo4j/Graphiti/LanceDB/Storage |
| Agent映射 | `backend/app/core/agent_memory_mapping.py` | ~98 | ✅ 15个Agent映射 |
| MemoryQueryService | `canvas-progress-tracker/obsidian-plugin/src/services/MemoryQueryService.ts` | 624 | ✅ 已初始化 (main.ts:560) |
| GraphitiAssociationService | `canvas-progress-tracker/obsidian-plugin/src/services/GraphitiAssociationService.ts` | 521 | ✅ 已初始化 (main.ts:582) |
| NodeColorChangeWatcher | `canvas-progress-tracker/obsidian-plugin/src/services/NodeColorChangeWatcher.ts` | ~595 | ✅ 已实现 (Story 30.6/30.9) |

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
- AC-30.4.1: 15个Agent执行完成后自动调用`record_learning_episode()`
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
| hint-generation | 提示生成 | hint_record |
| review-board-agent-selector | 复习选择 | concept_reviewed |
| graphiti-memory-agent | 图谱记忆 | concept_reviewed |

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

### Stories 30.9-30.16: 对抗性审查修复与测试补全

> **来源**: 2026-02-09 对抗性审查发现 Stories 30.1-30.8 的功能缺陷和测试覆盖不足，
> 后续创建 8 个修复/测试 Story 系统性补齐。

#### Story 30.9: NodeColorChangeWatcher 数据完整性修复 [P1] ✅ Done

**来源**: Story 30.6 QA 第二轮审查 (CONCERNS, 60/100) 发现 6 个缺陷
**修复内容**: 启动噪声过滤、概念名称映射修正、颜色移除/节点删除追踪
**预计工时**: 4小时

---

#### Story 30.10: 学习事件写入幂等性修复 [P0] ✅ Done

**来源**: 对抗性审查发现 Graphiti 双写重复、内存列表无去重、episode_id 不确定
**修复内容**: 确定性幂等键生成、内存去重、Graphiti 写入幂等保护
**阻塞**: Story 30.11 依赖此 Story
**预计工时**: 6小时

---

#### Story 30.11: 批量端点真批量改造 [P0] ✅ Done

**来源**: 对抗性审查发现 `record_batch_learning_events()` 是伪批量 (50事件×200ms=10s，远超AC要求<500ms)
**修复内容**: 用 `asyncio.gather()` 实现真并行写入
**依赖**: Story 30.10
**预计工时**: 8小时

---

#### Story 30.12: Agent 触发完整性补齐 [P0] ✅ Done

**来源**: 对抗性审查发现 14 个 Agent 映射中仅 11 个有实际触发，3 个缺失
**修复内容**: 补齐 hint-generation、comparison-table、memory-anchor 的触发调用
**预计工时**: 4小时

---

#### Story 30.13: 批量性能 + 幂等性测试补全 [P0] ✅ Done

**类型**: 测试 Story
**覆盖**: 幂等性测试 (重复事件去重)、性能基准 (50事件<500ms)、部分失败恢复
**测试数**: 11 tests
**预计工时**: 4小时

---

#### Story 30.14: 14 个 Agent 触发集成测试 [P0] ✅ Done

**类型**: 测试 Story
**覆盖**: 参数化 Agent 触发验证、失败降级测试、映射完整性静态分析
**测试数**: 19 tests (含 `@pytest.mark.parametrize` 14 agents)
**预计工时**: 6小时

---

#### Story 30.15: 多学科隔离 + DI 完整性测试 [P0] ✅ Done

**类型**: 测试 Story
**覆盖**: group_id 查询隔离验证、dependencies.py 端到端 DI 链验证
**测试数**: ~10 tests
**预计工时**: 5小时

---

#### Story 30.16: 真实 Neo4j 集成 + 弹性恢复测试 [P1] ✅ Done

**类型**: 测试 Story
**覆盖**: Docker Neo4j 集成测试、断连→fallback→重连弹性路径、前端健康检查 E2E
**测试数**: 18 tests
**预计工时**: 8小时

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

Phase 5: 对抗性审查修复 [Week 5] (2026-02-09 追加)
├─ Story 30.9: NodeColorChangeWatcher 数据完整性修复 [P1]
├─ Story 30.10: 幂等性修复 [P0] (阻塞30.11)
├─ Story 30.11: 批量真并行改造 [P0]
└─ Story 30.12: Agent触发补齐 [P0] (可与30.10并行)

Phase 6: 测试补全 [Week 5-6] (2026-02-09 追加)
├─ Story 30.13: 批量性能+幂等性测试 [P0]
├─ Story 30.14: Agent触发集成测试 [P0]
├─ Story 30.15: 多学科隔离+DI完整性测试 [P0]
└─ Story 30.16: 真实Neo4j+弹性恢复测试 [P1]

Phase 7: 对抗性审查修复 [Week 7-8] (2026-02-10 BMad全流程审查追加)
├─ Story 30.20: 核心功能测试补充 (30.6/30.7零覆盖修复) [P0]
├─ Story 30.21: 真实环境集成测试套件 (Mock性能基准替代) [P0]
├─ Story 30.22: Agent触发深度测试 (映射表→行为验证) [P1] (与30.23并行)
├─ Story 30.23: CI流水线激活 + asyncio.sleep替换 [P1] (与30.22并行)
└─ Story 30.24: 边界测试与防护加固 [P2]
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

**回滚方式**: 设置`NEO4J_ENABLED=false`环境变量（JSON fallback模式自动启用）

---

## Definition of Done

- [x] 16/19 Stories 完成 (30.1-30.16)
- [ ] ❌ Gate Decision: FAIL — P0 覆盖率 82% (要求 100%), P1 覆盖率 74% (要求 ≥90%)
- [x] 集成测试全部通过 (97+ tests across Stories 30.9-30.16)
- [x] 性能基准达标 (批量50事件<500ms — Story 30.13 验证, **注意: Mock 环境**)
- [x] 健康检查端点返回3层系统状态 (Story 30.3/30.16 验证)
- [x] Obsidian插件记忆服务已初始化 (main.ts:560-586)
- [ ] 🔵 Deferred: Story 30.17 — Priority 计算记忆降级透明化 (P1, 4h)
- [ ] 🔵 Deferred: Story 30.18 — ApiClient Memory 查询方法补全 (P1, 6h)
- [ ] 🔵 Deferred: Story 30.19 — SubjectMapping 学科映射配置 UI (P2, 6h)
- [ ] ⚠️ 待修复 → Story 30.20: Story 30.6/30.7 零测试覆盖
- [ ] ⚠️ 待修复 → Story 30.21: 性能基准需在真实 Neo4j 环境重新验证
- [ ] ⚠️ 待修复 → Story 30.22: Agent 触发测试从映射表升级为行为验证
- [ ] ⚠️ 待修复 → Story 30.23: CI 流水线提交 + asyncio.sleep 硬等待替换
- [ ] ⚠️ 待修复 → Story 30.24: 边界测试 + shutdown 数据安全 + vault 验证退出码

---

## Key File Locations

| 功能模块 | 文件路径 |
|---------|---------|
| Neo4j客户端 | `backend/app/clients/neo4j_client.py` |
| 记忆服务 | `backend/app/services/memory_service.py` |
| Memory API | `backend/app/api/v1/endpoints/memory.py` |
| Health API | `backend/app/api/v1/endpoints/health.py` |
| Agent映射配置 | `backend/app/core/agent_memory_mapping.py` |
| 依赖注入 | `backend/app/dependencies.py` |
| 插件主文件 | `canvas-progress-tracker/obsidian-plugin/main.ts` |
| 插件记忆查询 | `canvas-progress-tracker/obsidian-plugin/src/services/MemoryQueryService.ts` |
| 插件关联服务 | `canvas-progress-tracker/obsidian-plugin/src/services/GraphitiAssociationService.ts` |
| 插件颜色监听 | `canvas-progress-tracker/obsidian-plugin/src/services/NodeColorChangeWatcher.ts` |
| 插件优先级计算 | `canvas-progress-tracker/obsidian-plugin/src/services/PriorityCalculatorService.ts` |
| 插件API客户端 | `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts` |

---

## Story Manager Handoff

### 已完成 (Phase 1-6)

1. **Week 1**: Story 30.1 → 30.2 (顺序) ✅
2. **Week 2**: Story 30.3 + 30.4 + 30.5 (并行) ✅
3. **Week 3**: Story 30.7 → 30.6 (顺序) ✅
4. **Week 4**: Story 30.8 ✅
5. **Week 5**: Story 30.9 + 30.10 → 30.11 + 30.12 (对抗性审查修复) ✅
6. **Week 5-6**: Story 30.13 + 30.14 + 30.15 + 30.16 (测试补全) ✅

### 待实施 (Phase 7 — 对抗性审查 2026-02-10 BMad全流程审查)

7. **Week 7**: Story 30.20 (核心测试补充 P0) → Story 30.21 (真实集成测试 P0)
8. **Week 7-8**: Story 30.22 (Agent深度测试 P1) + 30.23 (CI流水线 P1) (并行)
9. **Week 8**: Story 30.24 (边界测试 P2)

### 已延迟 (Deferred)

10. **待排期**: Story 30.17 (PriorityCalculatorService FSRS集成) + 30.18 (ApiClient补全) + 30.19 (SubjectMapping UI)

---

## 对抗性审查记录

| 日期 | 审查类型 | 发现数 | 关键发现 | 后续行动 |
|------|---------|--------|---------|---------|
| 2026-02-09 | 代码对抗性审查 | 8 | 幂等性bug、伪批量性能、Agent触发不完整 | Stories 30.9-30.16 修复 |
| 2026-02-10 | EPIC 文档对抗性审查 | 13 | 文档严重过时(8→16 Stories)、FSRS硬编码、ApiClient不完整 | Phase 0 文档修复 + Stories 30.17-30.19 计划 |
| 2026-02-10 | BMad 全流程对抗性审查 | 17 | 完成率虚假(16/16→16/19)、Gate FAIL矛盾、Mock性能基准、已删除测试引用、零覆盖Story | Phase 0 文档修复(D1-D5) + Stories 30.20-30.24 规划 |

## Relations

