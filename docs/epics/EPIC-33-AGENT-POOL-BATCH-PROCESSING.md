# Epic 33: Agent Pool Batch Processing - Full Activation

> **类型**: Brownfield Enhancement Epic
> **创建日期**: 2026-01-17
> **状态**: Draft - 待审批
> **优先级**: P0 (Critical)

---

## Epic Title

**Agent Pool Batch Processing Full Activation - Brownfield Enhancement**

---

## Epic Goal

启用已完成的Obsidian批处理UI，通过实现缺失的6个后端API端点，允许用户对100+黄色节点进行智能分组和并行Agent执行。实现智能Agent路由和结果合并策略，提供8x加速的最优学习内容生成体验。

---

## Epic Description

### Existing System Context

| 项目 | 内容 |
|------|------|
| **当前功能** | Obsidian UI 100%就绪，后端API 0%实现 |
| **技术栈** | FastAPI + Python 3.11 + LangGraph + Obsidian Plugin (TS) |
| **集成点** | agent_service.py, canvas_utils.py, async_execution_engine.py |

### 当前实现状态

| 组件 | 状态 | 位置 | 说明 |
|------|------|------|------|
| **Obsidian UI** | ✅ 100% | `canvas-progress-tracker/obsidian-plugin/src/modals/` | 3个Modal + CSS完全就绪 |
| **AsyncExecutionEngine** | ✅ 100% | `src/command_handlers/async_execution_engine.py:39-150` | Semaphore=12, 8x加速 |
| **TF-IDF + K-Means** | ✅ 100% | `src/canvas_utils.py:11564-11730` | Auto-K选择, Silhouette Score |
| **LangGraph Send** | ✅ 100% | `src/agentic_rag/parallel_retrieval.py:59-116` | 5源并行检索 |
| **Backend REST API** | ❌ 0% | N/A | **主阻塞 - 6端点不存在** |
| **WebSocket** | ❌ 0% | N/A | **次阻塞** |
| **Session管理** | ❌ 0% | N/A | **次阻塞** |
| **智能路由** | ❌ 0% | N/A | 算法存在但未集成 |
| **结果合并** | ❌ 0% | N/A | 未实现 |

### 根本原因分析

**Obsidian UI调用的6个后端API端点完全不存在**：

| 端点 | 方法 | 调用位置 | 状态 |
|------|------|----------|------|
| `/canvas/intelligent-parallel` | POST | GroupPreviewModal:187 | ❌ MISSING |
| `/canvas/intelligent-parallel/confirm` | POST | main.ts:2325 | ❌ MISSING |
| `/canvas/intelligent-parallel/{sessionId}` | GET | ProgressMonitorModal:579 | ❌ MISSING |
| `/canvas/intelligent-parallel/cancel/{sessionId}` | POST | ProgressMonitorModal:717 | ❌ MISSING |
| `/canvas/single-agent` | POST | ResultSummaryModal:407 | ❌ MISSING |
| `/ws/intelligent-parallel/{sessionId}` | WebSocket | ProgressMonitorModal:341 | ❌ MISSING |

### 关键依赖声明 (2026-01-19 新增)

> **⚠️ EPIC-30 依赖关系**:
>
> 本Epic的部分Stories依赖 **EPIC-30** 已完成的功能：
>
> | 本Epic Story | 依赖 | 依赖说明 |
> |--------------|------|----------|
> | **33.4** 智能分组服务 | EPIC-30 Story 30.8 | 需要 `group_id` 多学科隔离支持，确保批处理结果按学科分组存储 |
> | **33.5** Agent路由引擎 | EPIC-30 Story 30.4 | 复用 14个Agent映射表 (`agent_memory_mapping.py`) |
> | **33.6** 批处理编排器 | EPIC-30 Story 30.4 | 调用 `agent_service.py` 的 fire-and-forget 模式触发记忆写入 |
>
> **架构层级关系**:
> ```
> EPIC-30 (记忆系统基础)
>     ├─ 30.4 Agent触发机制 ← 33.5, 33.6 复用
>     └─ 30.8 group_id隔离 ← 33.4 复用
>           ↓
> EPIC-33 (批处理)
>     ├─ 33.4 智能分组 (依赖30.8)
>     ├─ 33.5 Agent路由 (依赖30.4)
>     └─ 33.6 批处理编排 (依赖30.4)
> ```
>
> **实现要求**:
> - 33.4 必须使用 `group_id` 参数进行学科隔离
> - 33.5-33.6 必须复用 `backend/app/core/agent_memory_mapping.py` 中的Agent映射

### Enhancement Details

**要添加的内容:**
- 6个Backend API端点（POST/GET/WS）
- 4个核心Service（Session/Grouping/Routing/Orchestrator）
- 2个高级功能（ResultMerger + WebSocket）

**成功标准:**
- 100节点批处理 < 60秒
- 智能Agent路由准确率 > 80%
- 现有功能无回归

---

## Stories

| Story | 标题 | 优先级 | 目标 |
|-------|------|--------|------|
| **33.1** | Backend REST Endpoints | P0 | 实现5个REST端点 |
| **33.2** | WebSocket Real-time Updates | P1 | 实时进度推送 |
| **33.3** | Session Management Service | P1 | 会话生命周期管理 |
| **33.4** | Intelligent Grouping Service | P1 | TF-IDF + K-Means集成 |
| **33.5** | Agent Routing Engine | P1 | 智能Agent选择 |
| **33.6** | Batch Processing Orchestrator | P0 | 并行执行编排 |
| **33.7** | Result Merging Strategies | P2 | 多Agent结果融合 |
| **33.8** | E2E Integration Testing | P2 | 端到端测试 |

---

### Story 33.1: Backend REST Endpoints [P0 BLOCKER]

**目标**: 实现Obsidian UI所需的5个REST端点

**验收标准:**
- [ ] POST `/api/v1/canvas/intelligent-parallel` - 接收节点列表，返回分组预览
- [ ] POST `/api/v1/canvas/intelligent-parallel/confirm` - 启动批处理会话
- [ ] GET `/api/v1/canvas/intelligent-parallel/{sessionId}` - 返回进度状态
- [ ] POST `/api/v1/canvas/intelligent-parallel/cancel/{sessionId}` - 取消运行会话
- [ ] POST `/api/v1/canvas/single-agent` - 重试单个失败节点

**关键文件:**
- `backend/app/api/v1/endpoints/intelligent_parallel.py` (NEW)
- `backend/app/api/v1/router.py` (MODIFY)
- `backend/app/models/intelligent_parallel_models.py` (NEW)

---

### Story 33.2: WebSocket Real-time Updates [P1]

**目标**: 为Obsidian UI启用实时进度更新

**验收标准:**
- [ ] WS `/ws/intelligent-parallel/{sessionId}` - WebSocket端点
- [ ] 事件类型: progress_update, task_completed, task_failed, session_completed, error
- [ ] 支持自动重连
- [ ] WebSocket失败时自动降级到轮询

**关键文件:**
- `backend/app/api/v1/endpoints/websocket.py` (NEW)
- `backend/app/main.py` (MODIFY)

---

### Story 33.3: Session Management Service [P1]

**目标**: 跟踪批处理会话生命周期

**验收标准:**
- [ ] 会话创建（UUID4）
- [ ] 状态机: pending → running → completed/failed/cancelled
- [ ] 进度持久化（内存字典，可选Redis）
- [ ] 会话超时（30分钟）+ 自动清理

**关键文件:**
- `backend/app/services/session_manager.py` (NEW)
- `backend/app/models/session_models.py` (NEW)

---

### Story 33.4: Intelligent Grouping Service [P1]

**依赖**: EPIC-30 Story 30.8 (多学科隔离与group_id支持)

**目标**: 将TF-IDF + K-Means聚类集成到API端点

**验收标准:**
- [ ] 集成 `cluster_canvas_nodes()` from canvas_utils.py
- [ ] 自动确定最优K（3-10个聚类）
- [ ] 使用Silhouette Score评估聚类质量
- [ ] 计算预估处理时间 + 优先级分配
- [ ] **必须使用 `group_id` 参数进行学科隔离** (依赖30.8)

**关键文件:**
- `backend/app/services/intelligent_grouping_service.py` (NEW)
- 复用: `src/canvas_utils.py:11564-11730`
- 复用: `backend/app/core/subject_config.py` (来自30.8)

---

### Story 33.5: Agent Routing Engine [P1]

**依赖**: EPIC-30 Story 30.4 (Agent记忆写入触发机制)

**目标**: 根据节点内容智能选择最合适的Agent

**验收标准:**
- [ ] 内容分析识别问题类型 → 匹配最佳Agent
- [ ] 置信度评分（>0.7才推荐）
- [ ] 支持手动覆盖Agent选择
- [ ] **必须复用 `agent_memory_mapping.py` 中的14个Agent映射表** (依赖30.4)

**Agent映射:**

| 问题类型 | 推荐Agent |
|----------|-----------|
| "什么是X" | oral-explanation |
| "A和B区别" | comparison-table |
| "如何理解X" | clarification-path |
| "举例说明X" | example-teaching |
| "记忆X" | memory-anchor |
| "深度剖析X" | deep-decomposition |

**关键文件:**
- `backend/app/services/agent_routing_engine.py` (NEW)
- `backend/app/models/agent_routing_models.py` (NEW)

---

### Story 33.6: Batch Processing Orchestrator [P0]

**依赖**: EPIC-30 Story 30.4 (Agent记忆写入触发机制)

**目标**: 连接AsyncExecutionEngine到API端点

**验收标准:**
- [ ] 接收确认会话 → 启动并行执行
- [ ] 使用Semaphore(12)控制并发
- [ ] 通过WebSocket实时广播进度
- [ ] 错误处理（支持部分成功）
- [ ] 结果聚合和Canvas更新
- [ ] **必须使用 `agent_service.py` 的 fire-and-forget 模式触发记忆写入** (依赖30.4)

**关键文件:**
- `backend/app/services/batch_orchestrator.py` (NEW)
- 集成: `backend/app/services/agent_service.py:call_agents_batch()`
- 复用: `backend/app/core/agent_memory_mapping.py` (来自30.4)

---

### Story 33.7: Result Merging Strategies [P2]

**目标**: 实现多Agent结果的智能融合

**验收标准:**
- [ ] **补充式**: 拼接所有Agent输出（最完整）
- [ ] **层级式**: 按深度排序（入门→进阶→专家）
- [ ] **投票式**: 保留最相关内容（去重）
- [ ] 可配置默认策略
- [ ] 合并结果质量评分

**关键文件:**
- `backend/app/services/result_merger.py` (NEW)
- `backend/app/models/merge_strategy_models.py` (NEW)

---

### Story 33.8: E2E Integration Testing [P2]

**目标**: 验证从UI到后端的完整流程

**验收标准:**
- [ ] 测试: 10节点 → 分组 → 并行执行 → 结果
- [ ] 测试: 中途取消 / 重试失败节点 / WebSocket重连
- [ ] 性能: 100节点 < 60秒

**关键文件:**
- `backend/tests/e2e/test_intelligent_parallel.py` (NEW)
- `backend/tests/integration/test_batch_processing.py` (NEW)

---

### Story 33.9: P0 DI Chain Repair [P0 HOTFIX]

**目标**: 修复 `get_service()` 将 `batch_orchestrator=None, agent_service=None` 传入单例的问题

**验收标准:**
- [x] `_ensure_async_deps()` 在首次请求时注入 BatchOrchestrator 和 AgentService
- [x] asyncio.Lock 保护 `_deps_initialized`，防止并发首次请求竞态条件
- [x] 清理 `dependencies.py` 中的死代码 (`get_intelligent_parallel_service`)
- [x] DI 完整性测试 15/15 通过

**关键文件:**
- `backend/app/api/v1/endpoints/intelligent_parallel.py` (MODIFIED)
- `backend/app/dependencies.py` (MODIFIED - dead code removed)
- `backend/tests/integration/test_epic33_di_completeness.py` (NEW)
- `docs/stories/33.9.story.md`

**Status**: Done

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Obsidian Plugin (100% Ready)                  │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐      │
│  │GroupPreview  │  │ProgressMonitor    │  │ResultSummary     │      │
│  │Modal         │→ │Modal + WebSocket  │→ │Modal + Retry     │      │
│  └──────┬───────┘  └────────┬──────────┘  └────────┬─────────┘      │
└─────────┼───────────────────┼──────────────────────┼────────────────┘
          │                   │                      │
          ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Backend API Layer (Story 33.1)                   │
│  POST /intelligent-parallel  GET /status  WS /ws/...  POST /retry   │
└─────────────────────────────────────────────────────────────────────┘
          │                   │                      │
          ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Service Layer (Stories 33.3-33.7)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │Session      │  │Intelligent  │  │Agent        │  │Result       │ │
│  │Manager      │  │Grouping     │  │Routing      │  │Merger       │ │
│  │(33.3)       │  │(33.4)       │  │(33.5)       │  │(33.7)       │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │                │        │
│         └────────────────┴────────┬───────┴────────────────┘        │
│                                   ▼                                  │
│                    ┌──────────────────────────┐                      │
│                    │  Batch Orchestrator      │                      │
│                    │  (Story 33.6)            │                      │
│                    │  - Semaphore(12)         │                      │
│                    │  - Progress Broadcasting │                      │
│                    └────────────┬─────────────┘                      │
└─────────────────────────────────┼───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Existing Infrastructure (Reuse)                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │AsyncExecution   │  │TF-IDF+K-Means   │  │LangGraph Send       │  │
│  │Engine (Epic 10) │  │(canvas_utils)   │  │(parallel_retrieval) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Changes Summary

| 操作 | 文件路径 | Story |
|------|----------|-------|
| CREATE | `backend/app/api/v1/endpoints/intelligent_parallel.py` | 33.1 |
| CREATE | `backend/app/api/v1/endpoints/websocket.py` | 33.2 |
| CREATE | `backend/app/services/session_manager.py` | 33.3 |
| CREATE | `backend/app/services/intelligent_grouping_service.py` | 33.4 |
| CREATE | `backend/app/services/agent_routing_engine.py` | 33.5 |
| CREATE | `backend/app/services/batch_orchestrator.py` | 33.6 |
| CREATE | `backend/app/services/result_merger.py` | 33.7 |
| CREATE | `backend/app/models/intelligent_parallel_models.py` | 33.1 |
| CREATE | `backend/app/models/session_models.py` | 33.3 |
| CREATE | `backend/app/models/agent_routing_models.py` | 33.5 |
| CREATE | `backend/app/models/merge_strategy_models.py` | 33.7 |
| CREATE | `backend/tests/e2e/test_intelligent_parallel.py` | 33.8 |
| CREATE | `backend/tests/integration/test_batch_processing.py` | 33.8 |
| MODIFY | `backend/app/api/v1/router.py` | 33.1 |
| MODIFY | `backend/app/main.py` | 33.2 |

**统计**: 13个新文件 + 2个修改文件

---

## Story Dependency Graph

```
33.1 (REST API) ─────┬──────────────────────────────────┐
                     │                                  │
33.3 (Session) ──────┼──→ 33.6 (Orchestrator) ──→ 33.8 (E2E Test)
                     │           ↑
33.4 (Grouping) ─────┤           │
                     │           │
33.5 (Routing) ──────┼───────────┤
                     │           │
33.2 (WebSocket) ────┘           │
                                 │
33.7 (Merger) ───────────────────┘
```

**建议实施顺序 (Waves):**
1. **Wave 1**: 33.1 + 33.3 (基础设施)
2. **Wave 2**: 33.2 + 33.4 (通信 + 分组)
3. **Wave 3**: 33.5 + 33.6 (路由 + 编排)
4. **Wave 4**: 33.7 + 33.8 (合并 + 测试)

---

## Compatibility Requirements

- [x] 现有Canvas CRUD API保持不变
- [x] Obsidian UI无需任何修改（100%后端工作）
- [x] 与现有agent_service.py向后兼容
- [x] Database schema changes are backward compatible (无数据库变更)

---

## Risk Mitigation

| 风险 | 缓解措施 | 回滚计划 |
|------|----------|----------|
| WebSocket稳定性 | UI已有轮询fallback | 禁用WS端点 |
| 并行超时 | Semaphore(12)限流 | 降低并发数 |
| 功能回归 | E2E测试覆盖 | 移除新路由 |

---

## Definition of Done

- [ ] 8个Stories全部完成
- [ ] Obsidian UI成功连接所有端点
- [ ] 100节点批处理 < 60秒
- [ ] 智能路由准确率 > 80%
- [ ] 结果合并无重复冗余
- [ ] 无功能回归

---

## Verification Plan

| 测试类型 | 覆盖范围 |
|----------|----------|
| **单元测试** | 每个新Service文件 >90%覆盖率 |
| **集成测试** | API端点 → Service → Agent调用链 |
| **E2E测试** | Obsidian UI → Backend → Canvas更新 |
| **性能测试** | 100节点批处理 < 60秒 |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-17 | 0.1 | Initial draft - Deep dive analysis + 8 Stories | PM Agent (John) |
| 2026-01-19 | 0.2 | **添加EPIC-30依赖声明**: 33.4依赖30.8(group_id), 33.5-33.6依赖30.4(Agent触发机制)；更新验收标准 | PM Agent (John) |

---

*Epic created by PM Agent (John) following brownfield-create-epic task*
*Date: 2026-01-17*
