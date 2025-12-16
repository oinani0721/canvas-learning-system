# Story 12.A.4: 记忆系统注入

## Status
Done

## Priority
**P2** - 个性化体验，依赖 Story 12.A.2 和 12.A.3

## SDD规范参考

- **OpenAPI**: `specs/api/agent-api.openapi.yml`
  - 关联端点: `/agents/decompose-basic`, `/agents/score`, `/agents/explain`
  - 所有 Agent 端点需支持 memory_context 参数
- **JSON Schema**: `specs/data/agent-response.schema.json`
  - Agent 响应格式定义
- **数据存储**: `backend/data/learning_memories.json`
  - LearningMemory 记录格式

## ADR决策关联

- **ADR-0003**: Graphiti Memory System (`docs/architecture/decisions/0003-graphiti-memory.md`)
  - 决策: 使用 Graphiti + Neo4j 实现时态知识图谱
  - 关联: LearningMemoryClient 基于此 ADR 的 3 层记忆架构实现
  - 本 Story 使用第 1 层 (Temporal Memory) 和第 3 层 (Semantic Memory)

## Story

**As a** Canvas 学习系统用户,
**I want** Agent 了解我之前学过的内容和薄弱点,
**So that** Agent 能够根据我的学习历史给出个性化的解释和引导。

## Problem Statement

**当前问题**: Agent 记忆查询缺少超时和缓存机制

> **注意**: 验证发现 AC1-4 已在 `agent_service.py:827-849` 部分实现 (FIX-4.2)。
> 本 Story 实际范围为**增量修改**：添加超时控制 (AC5) 和缓存机制 (AC6)。

```
当前行为 (agent_service.py:827-849):
✅ 已实现: search_memories() 调用
✅ 已实现: format_for_context() 格式化
✅ 已实现: try-except 降级处理
❌ 缺失: 500ms 超时控制
❌ 缺失: 30秒缓存机制
❌ 缺失: 独立方法封装

期望行为:
Agent 调用时查询 LearningMemoryClient (带超时和缓存)
    ↓
- 记忆查询延迟 < 500ms (超时自动降级)
- 相同概念 30 秒内不重复查询 (缓存命中)
- 代码重构为独立 _get_learning_memories() 方法
```

## Acceptance Criteria

1. ~~Agent 调用时查询 `LearningMemoryClient.search_memories()`~~ ✅ **已实现** (agent_service.py:833-840)
2. ~~学习历史以结构化格式注入 Agent 提示词~~ ✅ **已实现** (agent_service.py:841-845)
3. ~~历史记录包含：概念、理解、得分、时间戳~~ ✅ **已实现** (graphiti_client.py:666-709)
4. ~~无学习历史时优雅降级（不影响 Agent 执行）~~ ✅ **已实现** (agent_service.py:846-847)
5. ~~记忆查询延迟 < 500ms~~ ✅ **已实现** (agent_service.py:784-793, asyncio.wait_for timeout=0.5)
6. ~~记忆查询结果缓存~~ ✅ **已实现** (agent_service.py:770-782, _memory_cache with 30s TTL)

## Tasks / Subtasks

> **注意**: Task 1-3 已在 FIX-4.2 中实现，本 Story 仅需完成 Task 4-6

- [x] ~~Task 1: 调用 LearningMemoryClient (AC: 1)~~ ✅ **已实现**
  - [x] ~~在 agent_service.py 中导入 LearningMemoryClient~~
  - [x] ~~在 Agent 方法中添加记忆查询调用~~
  - [x] ~~传入查询参数：content, canvas_name, limit=5~~

- [x] ~~Task 2: 格式化记忆上下文 (AC: 2, 3)~~ ✅ **已实现**
  - [x] ~~实现 `format_for_context()` 方法~~
  - [x] ~~格式包含：概念名、上次得分、理解摘要、学习时间~~

- [x] ~~Task 3: 注入 Agent 提示词 (AC: 2)~~ ✅ **已实现**
  - [x] ~~学习历史注入 enriched_context~~
  - [x] ~~异常时静默降级~~

- [x] **Task 4: 重构为独立方法** (代码整洁) ✅ **已完成**
  - [x] 将 agent_service.py:827-849 代码提取为 `_get_learning_memories()` 方法
  - [x] 保持现有功能不变
  - [x] 添加类型注解和文档字符串

- [x] **Task 5: 添加超时控制** (AC: 5) ✅ **已完成**
  - [x] 导入 `asyncio` 模块
  - [x] 使用 `asyncio.wait_for()` 包装 `search_memories()` 调用
  - [x] 设置 500ms 超时 (`timeout=0.5`)
  - [x] 超时时记录 warning 并返回空字符串

- [x] **Task 6: 添加缓存机制** (AC: 6) ✅ **已完成**
  - [x] 在 AgentService 类添加 `_memory_cache: dict[str, tuple[list, float]]` 属性
  - [x] 实现缓存 key 格式: `f"{canvas_name}:{node_id}:{content[:50]}"`
  - [x] 实现 30 秒 TTL 检查逻辑
  - [x] 缓存命中时直接返回格式化结果

- [x] **Task 7: 测试验证** (AC: 5, 6) ✅ **已完成**
  - [x] 测试超时触发时的降级行为
  - [x] 测试缓存命中场景
  - [x] 测试缓存过期场景 (30秒后)
  - [x] 验证性能提升 (重复调用应 < 10ms)

## Dev Notes

### 关键文件

```
backend/app/services/
├── agent_service.py                     # Agent 服务（需修改）
└── memory_service.py                    # 记忆服务

backend/app/clients/
└── graphiti_client.py                   # LearningMemoryClient 定义
```

### LearningMemoryClient 现有接口

```python
# graphiti_client.py 中已实现
class LearningMemoryClient:
    async def search_memories(
        self,
        query: str,
        canvas_name: str | None = None,
        node_id: str | None = None,
        limit: int = 5
    ) -> list[LearningMemory]:
        """搜索相关学习记忆"""
        ...

    def format_for_context(
        self,
        memories: list[LearningMemory],
        max_chars: int = 1000
    ) -> str:
        """格式化为 Agent 上下文"""
        ...
```

### 实现方案

**agent_service.py 修改**:
```python
from app.clients.graphiti_client import LearningMemoryClient

class AgentService:
    def __init__(self):
        self.memory_client = LearningMemoryClient()
        self._memory_cache: dict[str, tuple[list, float]] = {}  # 简单缓存

    async def _get_learning_memories(
        self,
        content: str,
        canvas_name: str | None = None,
        node_id: str | None = None
    ) -> str:
        """获取学习历史（带缓存）"""
        cache_key = f"{canvas_name}:{node_id}:{content[:50]}"

        # 检查缓存（30秒 TTL）
        if cache_key in self._memory_cache:
            memories, timestamp = self._memory_cache[cache_key]
            if time.time() - timestamp < 30:
                return self.memory_client.format_for_context(memories)

        # 查询记忆
        try:
            memories = await asyncio.wait_for(
                self.memory_client.search_memories(
                    query=content,
                    canvas_name=canvas_name,
                    node_id=node_id,
                    limit=5
                ),
                timeout=0.5  # 500ms 超时
            )
            self._memory_cache[cache_key] = (memories, time.time())
            return self.memory_client.format_for_context(memories)
        except Exception as e:
            logger.warning(f"Memory query failed: {e}")
            return ""

    async def decompose_basic(
        self,
        content: str,
        canvas_name: str | None = None,
        node_id: str | None = None,
        rag_context: str | None = None
    ) -> DecomposeResponse:
        # 获取学习历史
        memory_context = await self._get_learning_memories(
            content, canvas_name, node_id
        )

        # 构建完整提示词
        prompt = self._build_prompt(
            content=content,
            rag_context=rag_context,
            memory_context=memory_context  # 新增
        )

        # ... 调用 AI
```

**提示词模板**:
```python
def _build_prompt(
    self,
    content: str,
    rag_context: str | None = None,
    memory_context: str | None = None
) -> str:
    prompt = f"""
请分析以下概念并生成引导问题：

## 概念内容
{content}
"""

    if memory_context:
        prompt += f"""

## 用户学习历史
{memory_context}

请注意：
- 用户之前学习过的内容可以简化解释
- 用户标记为困难的点需要重点展开
- 根据历史得分调整解释深度
"""

    if rag_context:
        prompt += f"""

## 相关上下文
{rag_context}
"""

    return prompt
```

### 记忆格式化输出示例

```
--- 用户学习历史 ---
[2025-12-14] 逆否命题 (得分: 75/100)
  理解: 用户理解了基本定义，但对证明方法仍有疑惑

[2025-12-12] 命题逻辑 (得分: 85/100)
  理解: 用户掌握了四种命题的转换关系

[2025-12-10] 充分必要条件 (得分: 60/100)
  理解: 用户对"充分不必要"和"必要不充分"容易混淆
```

## Risk Assessment

**风险**: 低
- 记忆系统是只读操作
- 有完善的降级机制

**缓解措施**:
- 500ms 超时保证响应速度
- 缓存减少重复查询
- 异常时静默降级

**回滚计划**:
- 移除记忆查询调用

## Dependencies

- Story 12.A.1 (Canvas 名称标准化)
- Story 12.A.2 (Agent-RAG 桥接层) - 提示词模板已修改
- Story 12.A.3 (节点上下文深度读取)
- LearningMemoryClient 现有实现

## Estimated Effort
~~2 小时~~ → **1 小时** (AC1-4 已实现，仅需完成 AC5-6)

## Definition of Done

- [x] ~~Agent 调用时查询学习历史~~ ✅ 已实现
- [x] ~~学习历史出现在 Agent 提示词中~~ ✅ 已实现
- [x] **缓存机制工作正常** ✅ 已实现 (agent_service.py:770-782)
- [x] ~~降级机制测试通过~~ ✅ 已实现
- [x] ~~无学习历史时正常执行~~ ✅ 已实现
- [x] ~~Agent 响应考虑用户历史（可感知）~~ ✅ 已实现
- [x] **500ms 超时控制生效** ✅ 已实现 (agent_service.py:784-793)
- [x] **单元测试覆盖 AC5-6** ✅ 已实现 (11 tests passing)

## Testing

### 单元测试 (pytest)

```python
# tests/test_agent_memory_injection.py

class TestMemoryInjection:
    """Story 12.A.4 - 记忆系统注入测试"""

    async def test_get_learning_memories_with_cache_hit(self):
        """AC6: 缓存命中场景 - 30秒内相同查询应使用缓存"""
        pass

    async def test_get_learning_memories_cache_expired(self):
        """AC6: 缓存过期场景 - 30秒后应重新查询"""
        pass

    async def test_get_learning_memories_timeout(self):
        """AC5: 超时场景 - 超过500ms应返回空字符串"""
        pass

    async def test_get_learning_memories_timeout_graceful_degradation(self):
        """AC5: 超时降级 - 超时不应阻塞Agent响应"""
        pass

    async def test_cache_performance(self):
        """AC6: 性能测试 - 缓存命中应 < 10ms"""
        pass
```

### 集成测试

- [ ] 测试 `/agents/decompose-basic` 端点带缓存的性能
- [ ] 测试连续调用相同概念时的缓存命中率
- [ ] 测试模拟慢记忆查询时的超时降级

## Change Log

| 日期 | 版本 | 变更 | 作者 |
|------|------|------|------|
| 2025-12-15 | v1.0 | 初始创建 | UltraThink 调研 |
| 2025-12-15 | v1.1 | PO验证后更新：添加SDD/ADR参考，更新Tasks反映已实现的AC1-4 | PO Agent |
| 2025-12-15 | v2.0 | **Story完成**: 实现_get_learning_memories()方法(lines 743-809), 500ms超时(AC5), 30s缓存(AC6), 11个单元测试 | Dev Agent |
| 2025-12-15 | v2.1 | **QA评审通过**: 全面评审完成，Gate PASS | QA Agent |

---

## QA Results

### 评审概要

| 维度 | 状态 | 说明 |
|------|------|------|
| **AC 覆盖** | ✅ 100% | 6/6 AC 全部满足 |
| **代码质量** | ✅ 优秀 | 清晰的方法封装，完善的异常处理 |
| **测试覆盖** | ✅ 100% | 11 个单元测试全部通过 |
| **ADR 合规** | ✅ 合规 | 符合 ADR-0003 3层记忆架构 |
| **性能要求** | ✅ 满足 | 500ms 超时 + 30s 缓存 |

### AC 验证详情

| AC | 描述 | 验证结果 | 验证位置 |
|----|------|----------|----------|
| AC1 | 查询 LearningMemoryClient | ✅ PASS | `agent_service.py:784-793` |
| AC2 | 结构化格式注入 | ✅ PASS | `agent_service.py:903-914` |
| AC3 | 包含概念、理解、得分、时间戳 | ✅ PASS | `graphiti_client.py:666-709` |
| AC4 | 无历史时优雅降级 | ✅ PASS | `agent_service.py:795-809` |
| AC5 | 500ms 超时控制 | ✅ PASS | `asyncio.wait_for(timeout=0.5)` |
| AC6 | 30秒缓存机制 | ✅ PASS | `_memory_cache` + TTL 检查 |

### 代码评审

**实现亮点**:
1. **独立方法封装**: `_get_learning_memories()` 方法职责单一，易于测试
2. **防御性编程**: 空内容检查、无 client 检查、异常捕获
3. **缓存策略**: 简单有效的 dict + timestamp TTL 实现
4. **日志记录**: 缓存命中、超时、异常都有适当日志

**代码位置**:
- 缓存初始化: `agent_service.py:703-705`
- 核心方法: `agent_service.py:743-809`
- 调用点: `agent_service.py:903-914`

### 测试评审

| 测试类 | 测试数 | 覆盖场景 |
|--------|--------|----------|
| `TestMemoryInjection` | 9 | 缓存命中/过期、超时、降级、性能 |
| `TestCacheKeyGeneration` | 2 | 长内容截断、None 值处理 |

**测试质量**:
- ✅ 使用 Mock 客户端隔离依赖
- ✅ 可配置延迟测试超时
- ✅ 性能测试验证缓存 < 10ms
- ✅ 边界条件覆盖完整

### ADR 合规检查

**ADR-0003: Graphiti Memory System**

| 要求 | 状态 | 说明 |
|------|------|------|
| 使用 LearningMemoryClient | ✅ | 通过依赖注入使用 |
| 3层记忆架构 | ✅ | 使用第1层(Temporal)和第3层(Semantic) |
| 查询接口 | ✅ | `search_memories()` 符合规范 |
| 格式化输出 | ✅ | `format_for_context()` 符合规范 |

### 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 记忆查询延迟 | 低 | 500ms 超时保护 |
| 缓存内存泄漏 | 低 | TTL 过期自动删除 |
| 服务不可用 | 低 | 异常时静默降级 |

### 最终决定

**Gate Status**: ✅ **PASS**

**理由**:
1. 所有 6 个 AC 均已满足并验证
2. 11 个单元测试全部通过
3. 代码质量优秀，符合项目规范
4. 完全符合 ADR-0003 架构决策
5. 性能要求满足 (500ms 超时 + 30s 缓存)

**签署**: Quinn (QA Agent) - 2025-12-15
