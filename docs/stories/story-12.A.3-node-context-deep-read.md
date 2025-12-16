# Story 12.A.3: 节点上下文深度读取

## Status
**Done** (2025-12-15 实现完成)

> Story经过反幻觉验证，发现4个冲突已全部解决。
> 实际工作量大幅减少：仅需实现 Graphiti 集成 (AC 4)
> ✅ 2025-12-15: Graphiti MCP 集成已实现，11个测试通过

## Priority
**P1** - 核心功能，依赖 Story 12.A.1

## Story

**As a** Canvas 学习系统用户,
**I want** Agent 理解当前节点及其连接的周边节点,
**So that** Agent 能够基于完整的知识结构给出更精准的解释和拆解。

## Problem Statement

**当前问题**: Agent 不读取当前节点内容和周边连接节点

```
当前行为:
右键点击节点 → Agent 只收到节点文本 → 不知道上下文
                ↓
          - 不知道父节点（前置知识）
          - 不知道子节点（衍生概念）
          - 不知道 Graphiti 中的关联概念

期望行为:
右键点击节点 → 获取完整上下文:
                ├── 目标节点完整内容
                ├── 父节点（入边连接）
                ├── 子节点（出边连接）
                └── Graphiti 关联概念
              → Agent 基于完整上下文响应
```

## Acceptance Criteria (已修正)

> **注意**: AC 1-3, 5-6 已由现有实现满足，本Story聚焦 AC 4 (Graphiti集成)

1. ~~Agent 接收目标节点的完整内容（文本 + 位置 + 颜色）~~ → ✅ **已满足** (现有实现)
2. ~~Agent 接收所有入边连接的父节点内容~~ → ✅ **已满足** (现有实现)
3. ~~Agent 接收所有出边连接的子节点内容~~ → ✅ **已满足** (现有实现)
4. **[核心]** Agent 接收 Graphiti 中与目标节点相关的概念 → ✅ **已实现** (2025-12-15)
5. ~~上下文信息格式化为 Agent 可理解的结构~~ → ✅ **已满足** (现有实现)
6. ~~节点不存在时优雅处理（记录日志，继续执行）~~ → ✅ **已满足** (现有实现)

## Tasks / Subtasks (已修正)

> **注意**: 基于 2025-12-15 PO验证冲突解决，Tasks已更新

- [ ] Task 1: ~~扩展 CanvasService~~ **已有实现，跳过** (AC: 1, 2, 3)
  - [x] ~~实现 `get_node(canvas_name, node_id)` 方法~~ → 现有 `_find_adjacent_nodes()` 内联实现
  - [x] ~~实现 `get_edges_for_node(canvas_name, node_id)` 方法~~ → 现有逻辑已满足
  - [x] 返回入边（父节点）和出边（子节点） → 已实现
  - [x] 处理节点不存在的情况 → 已实现

- [x] Task 2: **增强** ContextEnrichmentService (AC: 1-4) ✅ 2025-12-15
  - [x] ~~实现 `enrich_with_full_context()` 方法~~ → **扩展现有 `enrich_with_adjacent_nodes()`**
  - [x] 获取目标节点内容 → 已实现
  - [x] 获取所有相邻节点 → 已实现
  - [x] **新增**: 集成 Graphiti MCP 工具获取关联概念 → ✅ 已实现 (`_search_graphiti_relations()`)
  - [x] **新增**: 优化上下文格式，增加深度信息 → ✅ 已实现 (`_format_graphiti_context()`)

- [x] Task 3: ~~定义上下文数据结构~~ **复用现有** (AC: 5) ✅ 2025-12-15
  - [x] ~~创建 `EnrichedContext` Pydantic 模型~~ → 复用现有 `AdjacentContext` 返回结构
  - [x] **新增**: 扩展现有结构支持 `graphiti_relations` 字段 → ✅ 已添加
  - [x] ~~实现 `format_for_agent()` 方法~~ → 现有 `_build_enriched_context()`

- [x] Task 4: ~~集成到 Agent 端点~~ **已集成** (AC: 5) ✅ 2025-12-15
  - [x] 在 agents.py 中调用 ContextEnrichmentService → **已实现 (lines 137-141, 197-201, 305-309)**
  - [x] 将格式化的上下文传递给 AgentService → 已实现
  - [x] **可选增强**: 更新 Agent 提示词模板优化深度上下文展示 → 自动包含在enriched_context

- [x] Task 5: 错误处理和测试 (AC: 6) ✅ 2025-12-15
  - [x] 处理 Canvas 文件不存在 → 已实现
  - [x] 处理节点 ID 不存在 → 已实现
  - [x] **新增**: 处理 Graphiti MCP 服务不可用 → ✅ graceful degradation 已实现
  - [x] 添加针对 Graphiti 集成的测试 → ✅ 11个测试用例已添加

## Dev Notes

### ⚠️ 冲突解决记录 (2025-12-15 PO验证)

| # | 冲突 | 用户决策 | 修正措施 |
|---|------|---------|---------|
| 1 | `enrich_with_full_context()` vs 现有 `enrich_with_adjacent_nodes()` | ✅ 接受SoT | **扩展现有方法**而非新建 |
| 2 | CanvasService新增 `get_node()`, `get_edges_for_node()` | ✅ 接受SoT | **复用现有内联逻辑**，不新增方法 |
| 3 | `graphiti_client.search_related()` 不存在 (技术幻觉) | ✅ 接受SoT | **移除引用**，使用MCP工具或标记需新增 |
| 4 | "Agent接收上下文" AC已满足 | ✅ 更新AC | AC改为**增强深度**而非新功能 |

**验证发现**:
- `ContextEnrichmentService.enrich_with_adjacent_nodes()` 已实现大部分功能 (lines 136-328)
- `agents.py` 已调用此方法 (lines 137-141, 197-201, 305-309)
- 本Story应聚焦于: **增加Graphiti关联** + **优化上下文格式**

### 关键文件

```
backend/app/services/
├── canvas_service.py                    # Canvas 文件操作
├── context_enrichment_service.py        # 上下文增强（需扩展）
└── agent_service.py                     # Agent 服务

backend/app/clients/
└── graphiti_client.py                   # Graphiti 记忆客户端
```

### Canvas 数据结构

```json
{
  "nodes": [
    {
      "id": "abc123",
      "type": "text",
      "text": "逆否命题\n\n定义: 如果 p → q，则逆否命题是 ¬q → ¬p",
      "x": 100,
      "y": 200,
      "width": 300,
      "height": 150,
      "color": "6"
    }
  ],
  "edges": [
    {
      "id": "edge1",
      "fromNode": "parent_node_id",
      "toNode": "abc123",
      "label": "前置知识"
    },
    {
      "id": "edge2",
      "fromNode": "abc123",
      "toNode": "child_node_id",
      "label": "衍生概念"
    }
  ]
}
```

### 实现方案 (已修正)

> **重要**: 以下代码示例已基于冲突解决更新，移除幻觉API

**~~CanvasService 扩展~~ → 无需修改**:
```python
# ✅ 现有实现已满足需求 (context_enrichment_service.py lines 178-223)
# _find_adjacent_nodes() 已实现节点和边的查找
# 无需在 CanvasService 新增方法
```

**ContextEnrichmentService 增强 (核心变更)**:
```python
# context_enrichment_service.py - 扩展现有 enrich_with_adjacent_nodes()

# ✅ 现有方法签名保持不变
async def enrich_with_adjacent_nodes(
    self,
    canvas_name: str,
    node_id: str,
    include_graphiti: bool = True  # 新增: 可选Graphiti集成
) -> dict:
    """增强版: 获取相邻节点 + Graphiti关联"""

    # 现有逻辑保持不变
    adjacent_context = await self._find_adjacent_nodes(canvas_name, node_id)

    # 新增: Graphiti 关联查询 (使用 MCP 工具)
    if include_graphiti:
        try:
            # 使用 mcp__graphiti-memory__search_memories 工具
            node_text = adjacent_context.get("target_node", {}).get("text", "")
            graphiti_results = await self._search_graphiti_relations(node_text)
            adjacent_context["graphiti_relations"] = graphiti_results
        except Exception as e:
            logger.warning(f"Graphiti查询失败，继续执行: {e}")
            adjacent_context["graphiti_relations"] = []

    return adjacent_context

async def _search_graphiti_relations(self, query: str) -> list[dict]:
    """新增: 通过MCP调用Graphiti记忆搜索"""
    # 实现方案选项:
    # 1. 直接调用 mcp__graphiti-memory__search_memories
    # 2. 通过 GraphitiClient 封装
    pass
```

**可用的 Graphiti MCP 工具**:
```
mcp__graphiti-memory__search_memories  # 搜索记忆
mcp__graphiti-memory__search_nodes     # 搜索节点
mcp__graphiti-memory__search_facts     # 搜索事实
```

### 依赖关系

```
Story 12.A.1 (Canvas名称标准化)
    ↓
Story 12.A.3 (本Story)
    ↓
Story 12.A.4 (记忆系统注入)
```

## Risk Assessment

**风险**: 低
- Canvas 数据结构已稳定
- 读取操作无副作用

**缓解措施**:
- 节点不存在时优雅降级
- Graphiti 不可用时继续执行

**回滚计划**:
- 移除 ContextEnrichmentService 调用

## Dependencies

- Story 12.A.1 (Canvas 名称标准化) - 必须先完成
- CanvasService 现有实现
- GraphitiClient 现有实现

## Estimated Effort
~~2 小时~~ → **0.5-1 小时** (冲突解决后范围大幅缩减)

> 原预估包含大量已实现功能，修正后仅需:
> - Graphiti MCP 集成 (~30分钟)
> - 测试用例 (~30分钟)

## Definition of Done (已修正)

- [x] ~~CanvasService 支持获取节点和边~~ → **已实现**
- [x] ~~ContextEnrichmentService 返回完整上下文~~ → **已实现**
- [x] ~~Agent 提示词包含节点上下文~~ → **已实现**
- [x] ~~父节点和子节点正确识别~~ → **已实现**
- [x] **[核心]** Graphiti 关联概念正确获取 → ✅ **已实现** (2025-12-15)
- [x] ~~错误处理覆盖所有边界情况~~ → ✅ **已实现** (含Graphiti graceful degradation)

## Implementation Summary (2025-12-15)

### 代码修改

| 文件 | 修改内容 |
|------|----------|
| `context_enrichment_service.py` | 添加 `graphiti_service` 参数、`include_graphiti` 参数、`_search_graphiti_relations()` 和 `_format_graphiti_context()` 方法 |
| `EnrichedContext` dataclass | 添加 `graphiti_relations` 和 `has_graphiti_refs` 字段 |
| `test_context_enrichment_service.py` | 添加 11 个 Graphiti 集成测试用例 |

### 测试结果

- **21 个测试全部通过** (含 11 个新增 Graphiti 测试)
- Graceful degradation: Graphiti 服务不可用时自动降级，不影响其他功能
