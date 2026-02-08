# EPIC-31.A: 记忆系统管道修复

## 元数据

| 属性 | 值 |
|------|------|
| EPIC ID | 31.A |
| 标题 | 记忆系统管道修复 |
| 状态 | Draft |
| 优先级 | P0 - Critical |
| 创建日期 | 2026-02-05 |
| 依赖 | EPIC-30 (Story 30.1-30.2) |
| 预计工作量 | 6 Stories, 24 ACs |

---

## 1. 背景与问题陈述

### 1.1 问题发现

通过 4 个并行 Explore Agent 的深度调研（2026-02-05），发现记忆系统存在 **4 个关键断点**：

```
┌─────────────────────────────────────────────────────────────┐
│                    记忆系统数据流断点                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Agent 执行                                                 │
│      ↓                                                      │
│  MemoryService.record_learning_event()                      │
│      ├─ [SYNC] → Neo4j ✅ 工作                              │
│      ├─ [SYNC] → self._episodes ✅ 工作                     │
│      └─ [ASYNC] → Graphiti JSON ⚠️ 断点4: 无重试            │
│                                                             │
│  查询路径                                                    │
│      ↓                                                      │
│  get_learning_history()                                     │
│      └─ 读取 self._episodes ❌ 断点3: 只读内存不读Neo4j      │
│                                                             │
│  VerificationService                                        │
│      └─ search_verification_questions()                     │
│          └─ _graphiti_client = None ❌ 断点1: 未注入         │
│                                                             │
│  前端 ReviewDashboardView                                   │
│      └─ calculatePriority(null) ❌ 断点2: FSRS状态未传递     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 历史问题

| 错误模式 | 出现次数 | 根因 |
|---------|---------|------|
| EPIC 重复定义 | 7 次 | 需求不清晰 |
| Status/Approved 混淆 | 1 次 | Story 30.8 显示 Approved 但 11 AC 未实现 |
| 过度 Mock | 系统性 | 1193 个 Mock，0 个 E2E 测试 |

### 1.3 本 EPIC 目标

**修复 4 个断点，使记忆系统数据能够完整流通**

```
修复后数据流：
Agent 执行 → MemoryService → Neo4j (持久化)
                          ↓
前端查询 ← get_learning_history() ← Neo4j (读取)
                          ↓
VerificationService.search_verification_questions() ← GraphitiTemporalClient
```

---

## 2. Story 清单

| Story | 标题 | 优先级 | 断点 | AC 数量 |
|-------|------|--------|------|---------|
| 31.A.1 | 后端依赖注入修复 | P0 | 断点1 | 4 |
| 31.A.2 | 学习历史读取修复 | P1 | 断点3 | 4 |
| 31.A.3 | 写入可靠性增强 | P1 | 断点4 | 4 |
| 31.A.4 | 前端 FSRS 状态传递修复 | P0 | 断点2 | 4 |
| 31.A.5 | 集成测试补全 | P1 | 测试缺口 | 4 |
| 31.A.6 | TodayReviewListService 完整集成 | P2 | 死代码消除 + UX 优化 | 4 |

---

## 3. 断点详情与修复方案

### 3.1 断点1: 后端依赖注入错误

**问题**：
- `dependencies.py:531-535` 创建 VerificationService 时未传入 `graphiti_client`
- 导致 `verification_service.py:1851` 调用 `search_verification_questions()` 时 AttributeError

**修复**：
```python
# dependencies.py - get_verification_service()
graphiti_client = get_graphiti_temporal_client()
service = VerificationService(
    rag_service=rag_service,
    cross_canvas_service=cross_canvas_service,
    textbook_context_service=textbook_service,
    graphiti_client=graphiti_client  # 添加此行
)
```

**Story**: 31.A.1

---

### 3.2 断点2: 前端 FSRS 状态传递缺失

**问题**：
- `ReviewDashboardView.ts:163-168` 调用 `calculatePriority()` 时 FSRS 参数硬编码为 `null`
- `FSRSStateQueryService` 已完整实现（Story 32.3），但 `main.ts` **从未初始化**该服务
- 导致优先级计算 40% 权重（FSRS 维度）始终返回中立分数 50

**修复**：
```typescript
// main.ts - 添加 FSRSStateQueryService 初始化
this.fsrsStateQueryService = new FSRSStateQueryService(this.app, apiBaseUrl);

// ReviewDashboardView.ts - 使用真实 FSRS 状态
const fsrsState = await this.queryFSRSState(conceptId);
const priorityResult = this.priorityCalculatorService.calculatePriority(
    conceptId,
    fsrsState,  // ✅ 真实 FSRS 数据（非 null）
    memoryResult,
    review.canvasId
);
```

**影响**：
- 优先级计算权重：FSRS 40% + 行为 30% + 网络 20% + 交互 10%
- FSRS=null 时 40% 权重始终返回 50 分，复习建议排序不准确

**Story**: 31.A.4

---

### 3.3 断点3: 学习历史只读内存

**问题**：
- `memory_service.py:320-405` 的 `get_learning_history()` 只读 `self._episodes`
- 重启后内存清空，历史数据丢失
- 对比 `get_review_suggestions()` 正确从 Neo4j 读取

**修复**：
```python
# memory_service.py - get_learning_history()
async def get_learning_history(self, ...):
    # 从 Neo4j 查询（参考 get_review_suggestions 的实现）
    group_id = build_group_id(subject) if subject else None
    episodes = await self.neo4j.get_learning_history(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id
    )
    # 回退到内存（如果 Neo4j 不可用）
    if not episodes:
        episodes = [e for e in self._episodes if e.get("user_id") == user_id]
    # ... 过滤和分页
```

**Story**: 31.A.2

---

### 3.4 断点4: Graphiti 写入可靠性

**问题**：
- `memory_service.py:300-312` 使用 `asyncio.create_task()` fire-and-forget
- 无重试机制，500ms 超时后静默失败
- 数据可能丢失

**修复**：
```python
# memory_service.py - 带重试的写入
async def _write_to_graphiti_json_with_retry(self, ..., max_retries: int = 2):
    for attempt in range(max_retries + 1):
        try:
            await asyncio.wait_for(
                self._learning_memory.add_learning_episode(...),
                timeout=GRAPHITI_JSON_WRITE_TIMEOUT,
            )
            return True
        except (asyncio.TimeoutError, Exception):
            if attempt < max_retries:
                await asyncio.sleep(0.1 * (attempt + 1))  # 指数退避
                continue
            logger.warning(f"Graphiti write failed after {max_retries} retries")
            return False
```

**Story**: 31.A.3

---

## 4. 依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                    Story 依赖关系                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  前置条件（已完成）：                                         │
│  └─ EPIC-30 Story 30.1-30.2 (Neo4j 基础设施)                │
│                                                             │
│  Phase 1（可并行）：                                         │
│  ├─ 31.A.1 后端依赖注入修复                                  │
│  ├─ 31.A.2 学习历史读取修复                                  │
│  ├─ 31.A.3 写入可靠性增强                                    │
│  └─ 31.A.4 前端服务连接修复                                  │
│                                                             │
│  Phase 2（依赖 Phase 1）：                                   │
│  └─ 31.A.5 集成测试补全                                      │
│                                                             │
│  Phase 3（可选优化，依赖 31.A.4）：                            │
│  └─ 31.A.6 TodayReviewListService 完整集成 (P2)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 成功标准

### 5.1 功能验证

- [ ] Agent 执行后，数据写入 Neo4j 成功
- [ ] 重启后，`GET /api/v1/memory/episodes` 返回历史数据
- [ ] VerificationService 能成功调用 `search_verification_questions()`
- [ ] 前端 Dashboard 优先级计算使用真实 FSRS 状态（40% 权重生效）
- [ ] Graphiti 写入失败时有重试，重试后仍失败时记录警告

### 5.2 测试验证

- [ ] 新增集成测试使用真实 Neo4j（非 Mock）
- [ ] 跨会话持久化测试通过
- [ ] 双写一致性测试通过
- [ ] 所有现有测试不回归

### 5.3 文档验证

- [ ] Story 30.8 状态修正为 Pending（11 AC 未实现）
- [ ] Story 30.4 进度修正为 21%（3/14 Agent）

---

## 6. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Neo4jClient 缺少 get_learning_history 方法 | 中 | 断点3 修复时需先检查/实现 |
| GraphitiTemporalClient 单例初始化问题 | 低 | 复用现有 get_graphiti_temporal_client() |
| 前端类型不匹配 | 低 | TypeScript 编译检查 |
| 现有测试依赖 Mock 行为 | 中 | 修复后运行完整测试套件 |

---

## 7. 历史教训整合

基于调研发现的错误模式，本 EPIC 采取以下预防措施：

1. **精确的代码位置** - 每个 AC 都标注文件和行号
2. **明确的验收标准** - 不使用模糊描述
3. **集成测试优先** - Story 31.A.5 专门补充真实集成测试
4. **依赖注入验证** - 不允许 None 依赖静默通过

---

## 8. 参考文档

- 深度调研报告（2026-02-05）
- EPIC-30 记忆系统完整激活
- EPIC-31 验证系统
- `backend/app/dependencies.py`
- `backend/app/services/memory_service.py`
- `canvas-progress-tracker/obsidian-plugin/main.ts`

---

## 版本历史

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0 | 2026-02-05 | PM Agent | 初始创建 |
| 1.1 | 2026-02-05 | PO Agent | 断点2修正：TodayReviewListService → FSRSStateQueryService（基于5并行Agent代码验证） |
| 1.2 | 2026-02-05 | QA Agent | 新增 Story 31.A.6（TodayReviewListService 集成），更新工作量为 6 Stories/24 ACs，补充 Phase 3 依赖关系 |
