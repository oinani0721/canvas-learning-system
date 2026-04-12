# Story 5.7: EventBus 三系统联通

Status: ready-for-dev

## Story

As a 系统,
I want FSRS、Graphiti、RAG 三个子系统通过 EventBus 联通，精通度更新时触发检索权重调整和记忆更新,
so that 学习数据能在系统间自动流动，形成闭环。

## Acceptance Criteria

1. **AC-1: EventBus 核心引擎**
   - **Given** 后端 FastAPI 应用启动
   - **When** EventBus 初始化
   - **Then** 自建 asyncio EventBus（约 100 行精简实现）启动运行
   - **And** 支持事件类型注册：每个事件类型关联一组异步处理器（handler）
   - **And** 支持 subscribe(event_type, handler) / unsubscribe(event_type, handler) / publish(event) 三个核心方法
   - **And** 事件处理器按注册顺序执行
   - **And** EventBus 为全局单例，通过 FastAPI dependency injection 注入

2. **AC-2: 三层优先级队列**
   - **Given** EventBus 接收到事件
   - **When** 根据事件的 tier 属性分发
   - **Then** 三层优先级处理：
     - **P0 / Tier1 CRITICAL**: await 同步执行——精通度更新（BKT/FSRS 计算）、AutoSCORE 评分。必须等待完成后才继续，失败则抛异常
     - **P1 / Tier2 IMPORTANT**: fire + retry + JSONL outbox——Graphiti 记忆写入、Neo4j 属性更新。异步执行，失败后重试（指数退避 2s→4s→8s，最多 3 次），仍失败则写入 JSONL outbox 文件供恢复
     - **P2 / Tier3 BEST_EFFORT**: fire-and-forget——WebSocket 推送 UI 更新、RAG 索引权重调整。异步执行，失败仅记录日志，不重试不阻塞
   - **And** Tier 属性在 LearningEvent 中定义，不可由 handler 覆盖

3. **AC-3: 事件类型定义**
   - **Given** EventBus 运行中
   - **When** 追加事件类型
   - **Then** 以下学习事件类型定义在 `models/canvas_events.py` 枚举中（追加式编辑）：
     - `SCORE_SUBMITTED` — AutoSCORE 评分完成（Tier1, payload: node_id, session_id, grade, dimensions）
     - `BKT_UPDATED` — BKT 掌握概率更新（Tier2, payload: node_id, p_mastery, delta）
     - `FSRS_UPDATED` — FSRS 复习调度更新（Tier2, payload: node_id, stability, due_date）
     - `MASTERY_CHANGED` — 融合精通度变化（Tier2, payload: node_id, old_level, new_level, fused_mastery）
     - `CALIBRATION_RECORDED` — 校准记录写入（Tier2, payload: node_id, quadrant, self_confidence, actual_performance）
     - `MEMORY_WRITE_REQUESTED` — 请求 Graphiti 写入记忆（Tier2, payload: node_id, memory_type, content）
     - `RAG_WEIGHT_ADJUST` — 请求 RAG 检索权重调整（Tier3, payload: node_id, mastery_level, boost_factor）
     - `UI_MASTERY_PUSH` — WebSocket 推送精通度变化到前端（Tier3, payload: node_id, mastery_level, color）
   - **And** 所有事件遵循 LearningEvent 格式：event_type, payload（必含 node_id + session_id）, timestamp, source, tier

4. **AC-4: FSRS → Graphiti → RAG 三系统联通**
   - **Given** 用户在检验白板中被考察，AutoSCORE 评分完成
   - **When** SCORE_SUBMITTED 事件发布
   - **Then** 事件级联流：
     1. `SCORE_SUBMITTED` [Tier1] → mastery_engine: BKT + FSRS 更新
     2. `BKT_UPDATED` [Tier2] → graphiti: 写入评分记录 + Neo4j: 更新 pMastery
     3. `FSRS_UPDATED` [Tier2] → graphiti: 写入复习调度
     4. `MASTERY_CHANGED` [Tier2] → graphiti: 更新学习记忆
     5. `RAG_WEIGHT_ADJUST` [Tier3] → RAG: 调整该节点的检索权重（已掌握节点降权，薄弱节点升权）
     6. `UI_MASTERY_PUSH` [Tier3] → WebSocket: 推送到前端 mastery-state → 节点颜色变化
   - **And** 每一步的触发由前一步的 handler 在处理完成后 publish 下一个事件（链式触发）
   - **And** 任一 Tier2/3 步骤失败不阻塞其他步骤

5. **AC-5: CircuitBreaker 降级**
   - **Given** 三个子系统（FSRS/Graphiti/RAG）之一出现持续故障
   - **When** 该子系统的 handler 连续失败 5 次
   - **Then** CircuitBreaker 状态：CLOSED → OPEN（停止向该子系统分发事件）
   - **And** OPEN 状态下事件写入 JSONL outbox 暂存
   - **And** 30 秒后进入 HALF_OPEN 状态，尝试发送一个事件
   - **And** HALF_OPEN 成功 → CLOSED（恢复正常），失败 → OPEN（继续熔断）
   - **And** 复用已有 CircuitBreaker 模式（若 backend 已有实现）或新建
   - **And** 健康面板显示各子系统 CircuitBreaker 状态

6. **AC-6: 事件追踪与可观测性**
   - **Given** EventBus 处理事件
   - **When** 每个事件从发布到处理完成
   - **Then** 结构化日志记录：
     - 事件来源（source）
     - 事件类型（event_type）
     - 目标处理器（handler_name）
     - 处理结果（success / failed / retrying / circuit_open）
     - 处理耗时（duration_ms）
   - **And** Tier2 失败重试时记录重试次数和退避时间
   - **And** JSONL outbox 文件记录未成功处理的事件（供手动或自动恢复）
   - **And** 健康面板展示事件处理统计（成功率/失败率/平均耗时）

7. **AC-7: 幂等保障**
   - **Given** 事件可能因重试被重复处理
   - **When** handler 收到重复事件
   - **Then** 幂等保障机制：
     - BKT/FSRS 更新：幂等——相同 grade + 相同 timestamp 产生相同结果
     - Neo4j 写入：MERGE upsert 模式，天然幂等
     - Graphiti 记忆写入：基于 event_id 去重
     - LanceDB 索引调整：重新计算权重，幂等
   - **And** 每个 LearningEvent 有唯一 event_id（UUID），handler 可用于去重

8. **AC-8: 单元测试覆盖**
   - **Given** event_bus.py 模块
   - **When** 运行测试
   - **Then** subscribe/unsubscribe/publish 基础功能测试
   - **And** 三层优先级分发测试（Tier1 await / Tier2 retry / Tier3 fire-and-forget）
   - **And** Tier2 重试逻辑测试（1/2/3 次重试 + JSONL outbox 写入）
   - **And** CircuitBreaker 状态转换测试（CLOSED→OPEN→HALF_OPEN→CLOSED / HALF_OPEN→OPEN）
   - **And** 事件级联流测试（SCORE_SUBMITTED → 级联到 6 个后续事件）
   - **And** 幂等性测试（重复事件不产生副作用）
   - **And** 空 handler / handler 异常不崩溃 EventBus 测试

## Tasks / Subtasks

- [ ] **Task 1: LearningEvent 模型与事件类型定义** (AC: #3)
  - [ ] 1.1 在 `backend/app/models/canvas_events.py` 中追加 LearningEventType 枚举（SCORE_SUBMITTED / BKT_UPDATED / FSRS_UPDATED / MASTERY_CHANGED / CALIBRATION_RECORDED / MEMORY_WRITE_REQUESTED / RAG_WEIGHT_ADJUST / UI_MASTERY_PUSH）
  - [ ] 1.2 在 `backend/app/models/canvas_events.py` 中追加 EventTier 枚举（TIER_1_CRITICAL / TIER_2_IMPORTANT / TIER_3_BEST_EFFORT）
  - [ ] 1.3 在 `backend/app/models/canvas_events.py` 中追加 LearningEvent 数据类（event_id, event_type, payload, timestamp, source, tier）
  - [ ] 1.4 编辑后运行 `ruff check`

- [ ] **Task 2: EventBus 核心引擎实现** (AC: #1, #2)
  - [ ] 2.1 创建 `backend/app/services/event_bus.py`
  - [ ] 2.2 实现 EventBus 类：subscribe / unsubscribe / publish
  - [ ] 2.3 实现 Tier1 处理逻辑：await handler(event)，失败抛异常
  - [ ] 2.4 实现 Tier2 处理逻辑：asyncio.create_task + 指数退避重试（2s→4s→8s，3 次）+ JSONL outbox 写入
  - [ ] 2.5 实现 Tier3 处理逻辑：asyncio.create_task，失败仅 logger.warning
  - [ ] 2.6 实现全局单例模式 + FastAPI dependency injection
  - [ ] 2.7 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 3: CircuitBreaker 实现** (AC: #5)
  - [ ] 3.1 检查 backend 是否已有 CircuitBreaker 实现（grep fallback_sync / circuit_breaker）
  - [ ] 3.2 若已有则复用并适配 EventBus 接口；若无则新建 `backend/app/services/circuit_breaker.py`
  - [ ] 3.3 实现三状态转换：CLOSED → OPEN（5 次连续失败）→ HALF_OPEN（30s 后）→ CLOSED/OPEN
  - [ ] 3.4 集成到 EventBus Tier2 处理器的重试逻辑中
  - [ ] 3.5 编辑后运行 `ruff check`

- [ ] **Task 4: JSONL Outbox 实现** (AC: #2, #6)
  - [ ] 4.1 实现 JSONL outbox 写入：Tier2 最终失败的事件序列化为 JSON 追加到 `data/outbox/events.jsonl`
  - [ ] 4.2 实现 outbox 恢复：启动时读取 outbox 文件，重新 publish 未处理的事件
  - [ ] 4.3 实现 outbox 清理：成功处理后从 outbox 中标记已完成
  - [ ] 4.4 编辑后运行 `ruff check`

- [ ] **Task 5: 事件处理器注册** (AC: #4)
  - [ ] 5.1 实现 SCORE_SUBMITTED handler → 调用 mastery_engine.record_grade() → publish BKT_UPDATED + FSRS_UPDATED
  - [ ] 5.2 实现 BKT_UPDATED handler → 调用 graphiti 写入 + Neo4j 更新 → publish MASTERY_CHANGED
  - [ ] 5.3 实现 FSRS_UPDATED handler → 调用 graphiti 写入复习调度
  - [ ] 5.4 实现 MASTERY_CHANGED handler → publish RAG_WEIGHT_ADJUST + UI_MASTERY_PUSH
  - [ ] 5.5 实现 RAG_WEIGHT_ADJUST handler → 调整 LanceDB 检索权重（预留接口，MVP 可为 logging placeholder 标注 TODO-Phase2）
  - [ ] 5.6 实现 UI_MASTERY_PUSH handler → WebSocket 推送到前端（预留接口，依赖 WebSocket 层就绪）
  - [ ] 5.7 在 FastAPI app startup 事件中注册所有 handler
  - [ ] 5.8 编辑后运行 `ruff check`

- [ ] **Task 6: 事件追踪与日志** (AC: #6)
  - [ ] 6.1 在 EventBus.publish 中添加结构化日志（事件发布时）
  - [ ] 6.2 在每个 handler 包装器中添加结构化日志（处理结果 + 耗时）
  - [ ] 6.3 Tier2 重试时记录重试次数和退避时间
  - [ ] 6.4 编辑后运行 `ruff check`

- [ ] **Task 7: 幂等保障** (AC: #7)
  - [ ] 7.1 在 EventBus 中维护已处理事件 ID 集合（内存 set，容量上限 10000，LRU 淘汰）
  - [ ] 7.2 handler 执行前检查 event_id 是否已处理
  - [ ] 7.3 验证 mastery_engine / mastery_store 的幂等性（MERGE upsert）
  - [ ] 7.4 编辑后运行 `ruff check`

- [ ] **Task 8: 单元测试** (AC: #8)
  - [ ] 8.1 创建 `backend/tests/unit/test_event_bus.py`：
    - subscribe / unsubscribe / publish 基础功能
    - Tier1 await 执行 + 失败抛异常
    - Tier2 重试逻辑（模拟 1/2/3 次失败 + outbox 写入）
    - Tier3 fire-and-forget + 失败不阻塞
    - 事件级联测试（publish SCORE_SUBMITTED → 验证 6 个后续事件触发）
    - 空 handler / handler 异常隔离
  - [ ] 8.2 创建 `backend/tests/unit/test_circuit_breaker.py`：
    - CLOSED → OPEN（5 次失败）
    - OPEN → HALF_OPEN（30s 超时模拟）
    - HALF_OPEN → CLOSED（成功恢复）
    - HALF_OPEN → OPEN（再次失败）
  - [ ] 8.3 创建 `backend/tests/unit/test_event_idempotency.py`：
    - 重复 event_id 不重复处理
    - LRU 淘汰后旧事件可重新处理
  - [ ] 8.4 运行全部测试确认通过

- [ ] **Task 9: 集成验证** (AC: #4, #5, #6)
  - [ ] 9.1 端到端测试：publish SCORE_SUBMITTED → 验证 mastery_engine 更新 → 验证 Graphiti 写入 → 验证 WebSocket 推送
  - [ ] 9.2 端到端测试：模拟 Graphiti 不可用 → 验证 CircuitBreaker 熔断 → 事件写入 outbox → 恢复后自动重放
  - [ ] 9.3 端到端测试：验证 BKT+FSRS 更新的 Tier1 同步语义（publish 返回时更新已完成）
  - [ ] 9.4 运行 `ruff check backend/app/services/event_bus.py backend/app/models/canvas_events.py` 确认 lint 通过

## Dev Notes

### EventBus 架构设计

**来源**: [Source: architecture.md#Cross-Cutting Concerns #10] — 自建 asyncio EventBus(~100 行) 连接 FSRS/Graphiti/LanceDB/UI 级联写入

```
EventBus 三层优先级:

  ┌─────────────────────────────────────────────────────────────────┐
  │ Tier1 (P0) CRITICAL — await 同步执行                            │
  │   SCORE_SUBMITTED → mastery_engine.record_grade()               │
  │   失败 → 抛异常，调用方感知                                       │
  ├─────────────────────────────────────────────────────────────────┤
  │ Tier2 (P1) IMPORTANT — fire + retry + JSONL outbox              │
  │   BKT_UPDATED → graphiti.write() + neo4j.update()               │
  │   FSRS_UPDATED → graphiti.write_schedule()                       │
  │   失败 → 指数退避重试 2s→4s→8s (max 3) → JSONL outbox           │
  ├─────────────────────────────────────────────────────────────────┤
  │ Tier3 (P2) BEST_EFFORT — fire-and-forget                        │
  │   UI_MASTERY_PUSH → WebSocket 推送                               │
  │   RAG_WEIGHT_ADJUST → LanceDB 检索权重                           │
  │   失败 → 仅 logger.warning，不重试不阻塞                          │
  └─────────────────────────────────────────────────────────────────┘
```

### 事件级联流（评分完成）

```
Agent 调用 MCP tool: score_answer(token) → autoscore.py
  → EventBus: SCORE_SUBMITTED [Tier1, await]
  → mastery_engine: BKT + FSRS 更新
  → EventBus: BKT_UPDATED [Tier2, fire+retry]
  → graphiti: 写入评分记录 + Neo4j: 更新 pMastery
  → EventBus: MASTERY_CHANGED [Tier2, fire+retry]
  → EventBus: RAG_WEIGHT_ADJUST [Tier3, fire-and-forget]
  → EventBus: UI_MASTERY_PUSH [Tier3, fire-and-forget]
  → WebSocket: mastery_update → mastery-state → 节点颜色变化
```

### CircuitBreaker 状态机

```
                   连续 5 次失败
  CLOSED ──────────────────────────→ OPEN
    ↑                                  │
    │ 探测成功                         │ 30s 超时
    │                                  ↓
    └──────────── HALF_OPEN ←──────────┘
                    │
                    │ 探测失败
                    └──────→ OPEN
```

**参考**: [Source: architecture.md#重试与降级策略] — Neo4j 写入 CircuitBreaker: CLOSED → OPEN(5 次失败) → HALF_OPEN(30s 后)

### LearningEvent 格式规范

```python
class LearningEvent:
    event_id: str              # UUID，幂等去重键
    event_type: LearningEventType  # UPPER_SNAKE 枚举
    payload: dict              # 必须包含 node_id + session_id
    timestamp: datetime        # 自动生成
    source: str                # 发送方标识 "autoscore" / "mastery_engine" / "user_action"
    tier: EventTier            # TIER_1_CRITICAL / TIER_2_IMPORTANT / TIER_3_BEST_EFFORT
```

### 后端内部通信规则

**来源**: [Source: architecture.md#Service Boundaries]

```
Service → Service 通信规则:
  ✅ 跨 service 走 EventBus
  ❌ 禁止 service 之间反向 import
  ❌ 禁止 service 直接调用另一个 service

示例:
  ✅ autoscore → EventBus.publish(SCORE_SUBMITTED) → mastery_engine handler
  ❌ autoscore → import mastery_engine → mastery_engine.record_grade()
```

### Brownfield 上下文

- `event_bus.py` 在架构文档目录结构中列出但**尚未创建**。本 Story 为 greenfield 实现
- `canvas_events.py` 已存在，包含 CanvasEventType 枚举（NODE_CREATED 等），需**追加**学习事件类型
- 需检查 backend 是否已有 CircuitBreaker / FallbackSyncService 实现可复用
- WebSocket 层（`backend/app/api/websocket.py`）可能已有或需新建——本 Story 仅注册 handler，不负责 WebSocket 层建设
- RAG 检索权重调整为预留接口（MVP 阶段 handler 内部仅记录日志，待检索管道就绪后实现真实逻辑）

### 与其他 Story 的依赖关系

| 依赖 | 方向 | 说明 |
|------|------|------|
| Story 5.1 (BKT+FSRS) | 前置依赖 | SCORE_SUBMITTED handler 调用 mastery_engine |
| Story 5.5 (Calibration) | 协作 | CALIBRATION_RECORDED 事件由校准模块发布 |
| Story 5.6 (多信号融合) | 协作 | MASTERY_CHANGED 事件携带融合后的精通度 |
| Story 5.2 (节点颜色) | 后续消费 | UI_MASTERY_PUSH 触发前端节点颜色更新 |
| Story 6.4 (AutoSCORE) | 前置依赖 | autoscore 完成后 publish SCORE_SUBMITTED |
| Story 3.2 (MCP 工具) | 协作 | MCP tool score_answer 调用链触发 EventBus |
| Epic 2 (检索管道) | 后续消费 | RAG_WEIGHT_ADJUST 供检索管道消费 |

### 性能约束

- Tier1 处理耗时 < 100ms（BKT+FSRS 计算本身 O(1)）
- Tier2 异步不阻塞主线程，重试延迟由退避策略控制
- Tier3 fire-and-forget，零延迟开销
- EventBus 本身开销极小（asyncio 事件分发约 < 1ms）

### Project Structure Notes

- `event_bus.py` 位于 `backend/app/services/`，符合架构文档目录结构
- 事件类型追加到 `backend/app/models/canvas_events.py`（追加式编辑，不修改现有枚举）
- CircuitBreaker 可选位置：`backend/app/services/circuit_breaker.py` 或复用已有
- JSONL outbox 文件位置：`backend/data/outbox/events.jsonl`（需确保目录存在）
- EventBus 事件必须定义在 `models/canvas_events.py` 的枚举中（[Source: architecture.md#Enforcement Guidelines]）

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns #10] — 自建 asyncio EventBus ~100 行，三层优先级，幂等保障，复用 CircuitBreaker
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns] — LearningEvent 格式规范
- [Source: _bmad-output/planning-artifacts/architecture.md#评分完成流] — SCORE_SUBMITTED → BKT_UPDATED 事件级联
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Boundaries] — 跨 service 走 EventBus 禁止反向 import
- [Source: _bmad-output/planning-artifacts/architecture.md#重试与降级策略] — CircuitBreaker CLOSED→OPEN(5次)→HALF_OPEN(30s)
- [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines #5] — EventBus 事件必须定义在 canvas_events.py
- [Source: _bmad-output/planning-artifacts/architecture.md#后端目录结构] — event_bus.py 在 services/ 目录
- [Source: _bmad-output/planning-artifacts/epics.md#Story5.7] — AC 原文：三系统联通 + P0/P1/P2 + CircuitBreaker + 事件追踪
- [Source: _bmad-output/planning-artifacts/prd.md#可靠性] — NFR-REL-03 Neo4j 异常降级

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/event_bus.py` — 新建（EventBus 核心引擎 + 三层优先级 + JSONL outbox）
- `backend/app/services/circuit_breaker.py` — 新建或复用（CircuitBreaker 三状态机）
- `backend/app/models/canvas_events.py` — 追加 LearningEventType + EventTier + LearningEvent
- `backend/tests/unit/test_event_bus.py` — 新建
- `backend/tests/unit/test_circuit_breaker.py` — 新建
- `backend/tests/unit/test_event_idempotency.py` — 新建
