# Story 12.A.2: Agent-RAG 桥接层

## Status
Implementation Complete (Pending User Verification)

## Priority
**P1** - 核心集成，依赖 Story 12.A.1

## Story

**As a** Canvas 学习系统用户,
**I want** Agent 拆解/解释时获取多源上下文,
**So that** Agent 响应包含 Graphiti 知识图谱、LanceDB 向量检索、跨 Canvas 关联等丰富信息。

## Problem Statement

**当前问题**: Agent 端点直接调用 AI，不使用 LangGraph 5源融合能力

```
当前流程:
右键菜单 → /agents/decompose/basic → AgentService → 直接调用Claude
                                      ↓
                                 无多源上下文
                                 无质量评估
                                 无融合算法

期望流程:
右键菜单 → /agents/decompose/basic → RAGService → LangGraph StateGraph
                                      ↓
                                 5源并行检索
                                 质量控制循环
                                 → AgentService (带RAG上下文)
```

## Acceptance Criteria

1. Agent 端点在调用 AgentService 前先执行 RAG 查询
2. RAG 结果作为 `rag_context` 参数传递给 Agent
3. Agent 提示词包含 RAG 融合结果
4. RAG 延迟 < 2s（可接受范围）
5. RAG 服务不可用时优雅降级（继续执行但不带上下文）
6. 所有 9 个现有 Agent 端点都使用 RAG 桥接

## Tasks / Subtasks

- [x] Task 0: 创建 RAGServiceDep 依赖注入 (AC: 1) ✅ 2025-12-15
  - [x] 在 `dependencies.py` 中创建 `get_rag_service_dep()` 异步生成器
  - [x] 添加 `RAGServiceDep = Annotated[RAGService, Depends(get_rag_service_dep)]` 类型别名
  - [x] 导出到 `__all__` 列表
  - [x] 验证依赖注入链: Settings → RAGService → Agent端点

- [x] Task 1: 修改 agents.py 端点 (AC: 1, 2) ✅ 2025-12-15
  - [x] 导入 `RAGServiceDep` 依赖
  - [x] 在 `decompose_basic` 端点添加 RAG 查询
  - [x] 在 `decompose_deep` 端点添加 RAG 查询
  - [x] 在所有 `explain_*` 端点添加 RAG 查询
  - [x] 在 `score_understanding` 端点添加 RAG 查询
  - [x] 额外: 13个Agent端点全部集成 (超出AC6要求的9个)

- [x] Task 2: 扩展 AgentService 接口 (AC: 2, 3) ✅ 2025-12-15
  - [x] 修改 `decompose_basic()` 方法签名，添加 `rag_context` 参数
  - [x] 修改所有相关方法接受 RAG 上下文 (6个方法)
  - [x] 在 Agent 提示词模板中添加 RAG 结果段落
  - [x] 格式化 RAG 结果为 Agent 可理解的文本 (`format_rag_for_agent`)

- [x] Task 3: 实现降级机制 (AC: 5) ✅ 2025-12-15
  - [x] 捕获 RAG 服务异常
  - [x] 异常时记录日志但继续执行
  - [x] 返回空上下文而非抛出错误
  - [x] 添加超时处理（2s 超时后降级）
  - [x] 实现 `get_rag_context_with_timeout()` 辅助函数

- [x] Task 4: 性能优化 (AC: 4) ✅ 2025-12-15
  - [N/A] asyncio.gather: 因RAG依赖enriched content，无法并行化
  - [x] 添加 RAG 延迟监控日志 (line 287: logger.info)
  - [N/A] RAG缓存: 作为未来优化项保留

- [x] Task 5: 测试验证 (AC: 6) ✅ 2025-12-15
  - [x] 测试所有13个Agent端点的RAG集成 (验证代码注入)
  - [x] 验证RAG上下文出现在Agent提示词中
  - [x] 测试RAG服务不可用时的降级行为 (is_available检查)
  - [x] 验证延迟在可接受范围内 (2s timeout)

## Dev Notes

### 现状与目标对比 (验证修复 2025-12-15)

| 维度 | 当前实现 | Story 目标 |
|------|---------|-----------|
| **服务** | `ContextEnrichmentService` | `RAGService` |
| **依赖注入** | `ContextEnrichmentServiceDep` | `RAGServiceDep` (需创建) |
| **上下文来源** | 邻居节点 + Textbook (2源) | 5源融合 (Graphiti + LanceDB + Multimodal + Textbook + CrossCanvas) |
| **质量控制** | 无 | 质量评估 + 重写循环 |
| **融合算法** | 简单拼接 | RRF/Weighted 融合 + Reranking |

**注意**: 当前 `agents.py` 已使用 `ContextEnrichmentServiceDep`，本 Story 是升级到完整的 RAG 管道。

### 关键文件

```
backend/app/dependencies.py               # 依赖注入 (需添加 RAGServiceDep)
backend/app/api/v1/endpoints/agents.py    # Agent API 端点
backend/app/services/agent_service.py     # Agent 服务层
backend/app/services/rag_service.py       # RAG 服务层
src/agentic_rag/state_graph.py            # LangGraph StateGraph (5源并行检索)
```

### 实现方案

**agents.py 修改**:
```python
from app.services.rag_service import RAGService

@router.post("/decompose/basic")
async def decompose_basic(
    request: DecomposeBasicRequest,
    agent_service: AgentServiceDep,
    rag_service: RAGServiceDep,  # 新增依赖
):
    # 新增: RAG 查询
    rag_context = None
    try:
        rag_result = await asyncio.wait_for(
            rag_service.query(
                query=request.content,
                canvas_file=request.canvas_name,
                fusion_strategy="weighted"
            ),
            timeout=2.0  # 2秒超时
        )
        rag_context = format_rag_for_agent(rag_result.results)
    except Exception as e:
        logger.warning(f"RAG query failed, continuing without context: {e}")

    # 原有逻辑，增加 rag_context 参数
    return await agent_service.decompose_basic(
        content=request.content,
        canvas_name=request.canvas_name,
        node_id=request.node_id,
        rag_context=rag_context  # 新增
    )
```

**Agent 提示词模板**:
```python
# agent_service.py
def _build_prompt(self, content: str, rag_context: str | None) -> str:
    base_prompt = f"""
请分析以下概念并生成引导问题：

## 概念内容
{content}
"""

    if rag_context:
        base_prompt += f"""

## 相关上下文（来自知识图谱和向量检索）
{rag_context}

请结合上述相关上下文，生成更有针对性的引导问题。
"""

    return base_prompt
```

### 依赖关系

```
Story 12.A.1 (Canvas名称标准化)
    ↓
Story 12.A.2 (本Story)
    ↓
Story 12.A.4 (记忆系统注入)
```

## Risk Assessment

**风险**: 中
- RAG 查询增加延迟
- RAG 服务可能不稳定

**缓解措施**:
- 2秒超时 + 降级机制
- 并行执行减少延迟
- 完善的错误处理

**回滚计划**:
- 移除 RAG 服务调用，恢复原有直接调用

## Dependencies

- Story 12.A.1 (Canvas 名称标准化) - 必须先完成
- RAGService 已注册到 router.py - P0 已完成

## Estimated Effort
2 小时

## Definition of Done

- [x] 所有 9 个 Agent 端点集成 RAG 查询 ✅ (实际集成13个端点)
- [x] RAG 上下文出现在 Agent 提示词中 ✅
- [x] 降级机制工作正常 ✅
- [x] RAG 延迟 < 2s ✅ (2s timeout + graceful degradation)
- [ ] Agent 响应质量提升可感知 (需用户手动验证)

## QA Results

**Gate Decision**: **PASS**
**QA Agent**: Quinn (Test Architect)
**Review Date**: 2025-12-16

### Implementation Verification

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| RAGServiceDep | `dependencies.py` | 89-99 | ✅ Verified |
| RAG Helper | `agents.py` | 200-301 | ✅ Verified |
| Endpoint Integration | `agents.py` | 13 endpoints | ✅ Verified |
| AgentService rag_context | `agent_service.py` | 6 methods | ✅ Verified |

### Acceptance Criteria Status

| AC | Status | Notes |
|----|--------|-------|
| AC1 | ✅ PASS | Agent端点先执行RAG查询 |
| AC2 | ✅ PASS | RAG结果作为rag_context传递 |
| AC3 | ✅ PASS | Agent提示词包含RAG融合结果 |
| AC4 | ✅ PASS | 2s超时机制实现 |
| AC5 | ✅ PASS | 优雅降级实现 |
| AC6 | ✅ PASS | 13个端点集成 (超出9个要求) |

### Key Implementation Details

**Helper Functions (agents.py:200-301)**:
- `format_rag_for_agent()`: 格式化RAG结果为Markdown
- `get_rag_context_with_timeout()`: 2s超时 + 降级

**AgentService Methods Updated**:
1. `call_decomposition()` - 添加context参数
2. `call_scoring()` - 添加context参数
3. `score_node()` - 添加rag_context参数
4. `generate_explanation()` - 添加rag_context参数
5. `generate_verification_questions()` - 添加rag_context参数
6. `decompose_question()` - 添加rag_context参数

## Change Log

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|----------|------|
| 2025-12-15 | 1.0 | 初始创建 | UltraThink |
| 2025-12-16 | 1.1 | 实现完成: 全部6个Task完成, 13个端点集成RAG | Dev Agent (James) |
