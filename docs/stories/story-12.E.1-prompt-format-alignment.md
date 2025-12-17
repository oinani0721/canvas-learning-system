# Story 12.E.1: 提示词格式对齐 - comparison-table concepts 数组

## Status

**Done** (2025-12-16)

---

## Story

**As a** Canvas Learning System 用户,
**I want** comparison-table Agent 收到正确格式的 `concepts` 数组输入,
**so that** Agent 能够正确解析并生成包含多个概念的对比表，而不是收到单个 `concept` 字符串导致解析失败。

---

## Acceptance Criteria

1. [x] comparison-table Agent 收到 `concepts` 数组（>=2 元素），格式符合 `.claude/agents/comparison-table.md` 期望
2. [x] 其他 Agent 格式不变（向后兼容），`oral`, `clarification`, `memory`, `four_level`, `example` 仍使用 `concept` 字符串
3. [x] 单元测试覆盖 `_extract_comparison_concepts()` 概念提取逻辑
4. [x] 智能主题提取功能保留（跳过元数据行的 `_extract_topic_from_content()` 逻辑）
5. [x] 日志记录 concepts 数组内容，便于调试

---

## Tasks / Subtasks

- [x] **Task 1: 创建 `_extract_comparison_concepts()` 方法** (AC: #1)
  - [x] 1.1 在 `agent_service.py` 中新增方法，从 content 中提取对比概念列表
  - [x] 1.2 实现概念提取逻辑：从 Markdown 表头/列表/标题中识别概念
  - [x] 1.3 确保返回至少 2 个概念，否则 fallback 到 `[topic]` 单元素数组

- [x] **Task 2: 修改 `call_explanation()` 中的 JSON 构造逻辑** (AC: #1, #2)
  - [x] 2.1 检测 `explanation_type == "comparison"`
  - [x] 2.2 对 comparison 类型使用 `concepts` 数组
  - [x] 2.3 对其他类型保持使用 `concept` 字符串（向后兼容）

- [x] **Task 3: 添加日志追踪** (AC: #5)
  - [x] 3.1 在 JSON prompt 构造后记录 `concepts` 数组内容
  - [x] 3.2 使用 `[Story 12.E.1]` 前缀标记日志

- [x] **Task 4: 编写单元测试** (AC: #3, #4)
  - [x] 4.1 创建 `test_agent_service_comparison.py` 测试文件
  - [x] 4.2 测试从 Markdown 表格提取概念
  - [x] 4.3 测试从 Markdown 列表提取概念
  - [x] 4.4 测试 fallback 逻辑（无法提取时返回 `[topic]`）
  - [x] 4.5 测试向后兼容性（其他 Agent 类型仍使用 `concept`）

- [x] **Task 5: 回归测试** (AC: #2, #4)
  - [x] 5.1 运行现有 Agent 测试确保无回归
  - [x] 5.2 验证 `oral`, `clarification` 等类型仍正常工作

---

## Dev Notes

### 问题诊断

**根因**: `agent_service.py:1409-1414` 发送 `concept` **字符串**，但 `comparison-table.md:14-21` 期望 `concepts` **数组**。

**当前代码** (问题代码):
```python
# agent_service.py:1406-1414
topic = self._extract_topic_from_content(content)
json_prompt = json.dumps({
    "material_content": content,
    "topic": topic,
    "concept": topic,  # ❌ 错误：应该是 concepts 数组！
    "user_understanding": user_understanding
}, ensure_ascii=False, indent=2)
```

**Agent 模板期望** (`comparison-table.md:14-21`):
```json
{
  "concepts": ["概念A", "概念B", "概念C"],  // ✅ 期望数组
  "topic": "主题名称",
  "material_content": "相关材料内容（可选）",
  "user_understanding": "用户的个人理解"
}
```

### 修复方案

**新增方法**: `_extract_comparison_concepts()`

```python
def _extract_comparison_concepts(self, content: str, topic: str) -> List[str]:
    """
    从内容中提取对比概念列表（用于 comparison-table Agent）

    提取策略:
    1. 从 Markdown 表头提取（如 | 概念A | 概念B | 概念C |）
    2. 从 Markdown 列表提取（如 - 概念A）
    3. 从 # 标题提取（如 ## 概念A）
    4. Fallback: 返回 [topic] 单元素数组

    Returns:
        至少包含 1 个元素的概念列表
    """
    concepts = []

    # 策略1: 从表头提取
    # 策略2: 从列表提取
    # 策略3: 从标题提取

    if len(concepts) >= 2:
        return concepts

    # Fallback
    return [topic] if topic else ["Unknown"]
```

**修改 `call_explanation()`**:

```python
# 对 comparison 类型使用 concepts 数组
if agent_type == AgentType.COMPARISON_TABLE:
    concepts = self._extract_comparison_concepts(content, topic)
    json_prompt = json.dumps({
        "material_content": content,
        "topic": topic,
        "concepts": concepts,  # ✅ 使用数组
        "user_understanding": user_understanding
    }, ensure_ascii=False, indent=2)
    logger.info(f"[Story 12.E.1] comparison-table concepts: {concepts}")
else:
    # 其他 Agent 保持原有格式
    json_prompt = json.dumps({
        "material_content": content,
        "topic": topic,
        "concept": topic,
        "user_understanding": user_understanding
    }, ensure_ascii=False, indent=2)
```

### SDD规范参考 (必填)

**API端点** (从OpenAPI specs):
- 端点路径和方法: `POST /agents/{agent_id}/invoke` (异步调用 Agent)
- 规范来源: `[Source: specs/api/agent-api.openapi.yml#paths./agents/{agent_id}/invoke]`
- 请求Schema: `AgentInvokeRequest` (包含 prompt, context, timeout)
- 响应Schema: `AgentInvokeResponse` (包含 task_id, status)

**数据Schema** (从JSON Schema):
- 模型名称: `AgentPrompt` (内部模型，非外部 Schema)
- 相关 Agent: `comparison-table` (Agent ID: 7)
- 期望输入格式: `{"concepts": [...], "topic": "...", "material_content": "...", "user_understanding": "..."}`
- 验证规则: `concepts` 必须是数组，至少 1 个元素

**Agent 模板规范**:
- 来源: `.claude/agents/comparison-table.md:14-21`
- 期望格式: JSON with `concepts` array (2-5 concepts)

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| ADR-0002 | LangGraph Agents | Agent 输入格式由 `.claude/agents/*.md` 模板定义 |

**关键约束** (从ADR Consequences提取):
- 约束1: Agent 输入格式必须与 `.claude/agents/*.md` 模板期望一致
- 约束2: 修改 JSON 构造逻辑时保持向后兼容（其他 Agent 不受影响）

来源引用: `[Source: ADR-0002]`

### 相关源文件

| 文件 | 行号 | 描述 |
|------|------|------|
| `backend/app/services/agent_service.py` | 1395-1435 | `call_explanation()` - JSON prompt 构造 |
| `backend/app/services/agent_service.py` | 1089-1127 | `_extract_topic_from_content()` - 主题提取 |
| `.claude/agents/comparison-table.md` | 14-21 | Agent 输入格式期望 |

### Testing

**测试文件位置**: `backend/tests/unit/test_agent_service_comparison.py`

**测试标准**:
- 框架: pytest
- 覆盖率要求: >= 80%
- 测试类型: 单元测试 + 集成测试

**关键测试用例**:
1. `test_extract_comparison_concepts_from_table()` - 从表格提取概念
2. `test_extract_comparison_concepts_from_list()` - 从列表提取概念
3. `test_extract_comparison_concepts_fallback()` - 无法提取时 fallback
4. `test_comparison_table_receives_concepts_array()` - comparison-table 收到数组
5. `test_other_agents_receive_concept_string()` - 其他 Agent 收到字符串（向后兼容）

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-16 | 0.1 | Story 创建，基于 Epic 12.E 定义 | PO Agent (Sarah) |
| 2025-12-16 | 0.2 | AC#5 (日志记录) 经用户确认保留；修正测试文件位置 | PO Agent (Sarah) |
| 2025-12-16 | 1.0 | **DONE** - 实现完成，15/15 测试通过，37/37 回归测试通过 | Dev Agent (Claude Opus 4.5) |

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- `[Story 12.E.1] comparison-table concepts: [...]` - agent_service.py:1499

### Completion Notes List

1. **Task 1**: 新增 `_extract_comparison_concepts()` 方法 (lines 1129-1201)，支持从 Markdown 表格、列表、标题提取概念
2. **Task 2**: 修改 `call_explanation()` 逻辑 (lines 1489-1507)，comparison 类型使用 `concepts` 数组
3. **Task 3**: 添加日志 `logger.info(f"[Story 12.E.1] comparison-table concepts: {concepts}")` (line 1499)
4. **Task 4**: 创建 15 个单元测试，覆盖概念提取和向后兼容性
5. **Task 5**: 回归测试通过 (37/37 tests: 15 new + 11 user_understanding + 11 memory_injection)

### File List

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/services/agent_service.py` | Modified | 新增 `_extract_comparison_concepts()` + 修改 `call_explanation()` |
| `backend/tests/unit/test_agent_service_comparison.py` | Created | 15 个单元测试 |
| `docs/stories/story-12.E.1-prompt-format-alignment.md` | Modified | 状态更新为 Done |

---

## QA Results

**Reviewed By**: Quinn (Test Architect)
**Review Date**: 2025-12-16
**Gate Decision**: ✅ **PASS**
**Quality Score**: 100/100

### Requirements Traceability

| AC | Test | Given-When-Then | Status |
|----|------|-----------------|--------|
| AC1 | `test_comparison_table_receives_concepts_array` | Given comparison type → When JSON constructed → Then contains `concepts` array | ✅ |
| AC2 | 5 backward compatibility tests | Given non-comparison type → When JSON constructed → Then contains `concept` string | ✅ |
| AC3 | 9 unit tests for `_extract_comparison_concepts()` | Given various content formats → When extracted → Then returns correct concepts | ✅ |
| AC4 | `test_extract_comparison_concepts_fallback` | Given no extractable concepts → When called → Then returns `[topic]` | ✅ |
| AC5 | Code inspection | N/A (logger.info at line 1499) | ✅ |

### Test Summary

| Category | Count | Status |
|----------|-------|--------|
| New Unit Tests | 15 | ✅ All Pass |
| Regression Tests | 37 | ✅ All Pass |
| AC Coverage | 5/5 | ✅ Complete |

### NFR Validation

| NFR | Status | Notes |
|-----|--------|-------|
| Security | ✅ PASS | Internal service method, no external input handling |
| Performance | ✅ PASS | Regex O(n), max 5 concepts |
| Reliability | ✅ PASS | Fallback mechanism ensures always returns ≥1 concept |
| Maintainability | ✅ PASS | Follows existing patterns, clear docstrings |

### ADR Compliance

- **ADR-0002**: ✅ Agent input format matches `.claude/agents/comparison-table.md` template

### Gate File

`docs/qa/gates/12.E.1-prompt-format-alignment.yml`
