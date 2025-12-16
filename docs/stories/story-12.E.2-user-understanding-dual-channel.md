# Story 12.E.2: user_understanding 双通道传递

**Epic**: Epic 12.E - Agent 质量综合修复
**优先级**: P0 Critical
**Story Points**: 2
**工期**: 0.5 天
**依赖**: 无 (可与 12.E.1, 12.E.3 并行)
**Assignee**: Dev Agent (James)
**状态**: Done

---

## User Story

> As a **Canvas 学习系统用户**, I want to **在调用 deep-decomposition 和 question-decomposition Agent 时，接收到我之前填写的个人理解 (黄色节点内容)**, so that **AI 能够基于我的真实理解水平，生成更有针对性的检验问题，准确暴露我的理解盲点**。

---

## 背景

### 问题根因

Epic 12.E 调研发现，用户在黄色节点 (color: "3") 中填写的个人理解未被正确传递给需要 `user_understanding` 的 Agent:

| Agent | `user_understanding` 需求 | 当前状态 |
|-------|---------------------------|----------|
| `deep-decomposition` | **必需** (第33行) | 收到 `null` |
| `question-decomposition` | **必需** (第36行) | 收到 `null` |
| 其他解释类 Agent | 可选 | 收到 `null` |

### 代码追踪

**当前数据流** (问题):
```
用户黄色节点 → find_related_understanding_content() → user_understandings 列表
                                                           ↓
                                           添加到 enhanced_context (✅)
                                                           ↓
                                           call_explanation() 调用
                                                           ↓
                                           user_understanding 参数未传递 (❌)
                                                           ↓
                                           json_prompt["user_understanding"] = null (❌)
```

**期望数据流** (修复后):
```
用户黄色节点 → find_related_understanding_content() → user_understandings 列表
                                                           ↓
                                           添加到 enhanced_context (✅)
                                                           ↓
                                           合并为 user_understanding 字符串
                                                           ↓
                                           call_explanation(user_understanding=...) (✅)
                                                           ↓
                                           json_prompt["user_understanding"] = "..." (✅)
```

### BUG 代码定位

**位置 1**: `agent_service.py:1849-1851`
```python
# 当前代码 - 缺少 user_understanding 参数
result = await self.call_explanation(
    content, explanation_type, context=enhanced_context, images=images
)
```

**位置 2**: `agent_service.py:1409-1414`
```python
# call_explanation 中 JSON 构造 - user_understanding 参数已支持
json_prompt = json.dumps({
    "material_content": content,
    "topic": topic,
    "concept": topic,
    "user_understanding": user_understanding  # 参数来自方法签名第1386行
}, ensure_ascii=False, indent=2)
```

---

## Acceptance Criteria

### AC 2.1: JSON 字段传递

**验收标准**: `deep-decomposition` 和 `question-decomposition` 收到非 null 的 `user_understanding` JSON 字段 (当存在黄色节点时)

**验证步骤**:
- [x] 调用 `/agents/explain/deep` 端点，有黄色节点时
- [x] 验证 Agent 收到的 JSON prompt 中 `user_understanding` 非 null
- [x] 日志输出包含 `user_understanding` 内容

**测试用例**:
```python
async def test_user_understanding_in_json_field():
    """AC 2.1: 验证 user_understanding 出现在 JSON 字段中"""
    # Arrange: 创建包含黄色节点的 Canvas
    canvas_data = create_test_canvas_with_yellow_node(
        yellow_node_content="逆否命题就是把原命题反过来说"
    )

    # Act: 调用 generate_explanation
    result = await agent_service.generate_explanation(
        canvas_name="test.canvas",
        node_id="target_node",
        content="逆否命题的定义...",
        explanation_type="deep"
    )

    # Assert: 验证 JSON prompt 包含 user_understanding
    # (需要 mock call_explanation 来捕获参数)
    assert mock_call_explanation.called
    call_kwargs = mock_call_explanation.call_args.kwargs
    assert call_kwargs.get("user_understanding") is not None
    assert "反过来说" in call_kwargs["user_understanding"]
```

---

### AC 2.2: enhanced_context 同时包含

**验收标准**: `user_understanding` 同时出现在 JSON 字段和 `enhanced_context` 中

**验证步骤**:
- [x] JSON prompt 包含 `user_understanding` 字段
- [x] `enhanced_context` 包含 "## 用户之前的个人理解" 部分
- [x] 两者内容一致

**测试用例**:
```python
async def test_user_understanding_in_both_channels():
    """AC 2.2: 验证双通道传递"""
    # Arrange
    understanding = "我理解逆否命题是..."

    # Act & Assert
    # 1. JSON 字段包含
    assert json_prompt["user_understanding"] == understanding

    # 2. enhanced_context 包含
    assert "## 用户之前的个人理解" in enhanced_context
    assert understanding in enhanced_context
```

---

### AC 2.3: 无黄色节点时正确处理

**验收标准**: 无黄色节点时 `user_understanding` 为 `null` (不是空字符串)

**验证步骤**:
- [x] 无关联黄色节点时调用 Agent
- [x] 验证 `user_understanding` 为 `null`
- [x] 不是空字符串 `""`

**测试用例**:
```python
async def test_user_understanding_null_when_no_yellow_node():
    """AC 2.3: 验证无黄色节点时为 null"""
    # Arrange: Canvas 无黄色节点

    # Act
    result = await agent_service.generate_explanation(...)

    # Assert
    assert call_kwargs.get("user_understanding") is None
    # 而非 ""
```

---

### AC 2.4: 文件名 topic 提取保留 (向后兼容)

**验收标准**: 此 Story 不影响原有 topic 提取功能

**验证步骤**:
- [x] FILE 类型节点仍使用文件名提取 topic
- [x] TEXT 类型节点仍使用内容智能提取

**测试用例**:
```python
async def test_topic_extraction_unchanged():
    """AC 2.4: 验证向后兼容"""
    # Arrange: FILE 类型节点

    # Act
    result = await agent_service.generate_explanation(
        file_path="KP01-Level-Set定义.md",
        ...
    )

    # Assert: topic 仍然正确提取
    assert "Level Set" in extracted_topic
```

---

## Tasks / Subtasks

- [x] **Task 1: 修改 `generate_explanation()` 方法** (AC: 2.1, 2.2)
  - [x] 1.1 在 `find_related_understanding_content()` 调用后，合并 `user_understandings` 为单一字符串
  - [x] 1.2 传递 `user_understanding` 参数到 `call_explanation()`
  - [x] 1.3 保持 `enhanced_context` 中也包含用户理解 (双通道)
  - [x] 1.4 添加调试日志

- [x] **Task 2: 修改 `call_explanation()` 签名文档** (AC: 2.1)
  - [x] 2.1 更新 docstring 说明 `user_understanding` 用途
  - [x] 2.2 添加类型注解确认 `Optional[str]`

- [x] **Task 3: 确保 null vs 空字符串处理** (AC: 2.3)
  - [x] 3.1 无黄色节点时，`user_understanding = None` (非 `""`)
  - [x] 3.2 `call_explanation` 中保持 `None` 不转换为空字符串

- [x] **Task 4: 单元测试** (AC: 2.1-2.4)
  - [x] 4.1 创建 `test_agent_service_user_understanding.py`
  - [x] 4.2 测试 JSON 字段包含 user_understanding
  - [x] 4.3 测试 enhanced_context 包含 user_understanding
  - [x] 4.4 测试无黄色节点时为 null
  - [x] 4.5 测试向后兼容

- [x] **Task 5: 回归测试** (AC: 2.4)
  - [x] 5.1 现有 `generate_explanation` 测试通过
  - [x] 5.2 现有 `call_explanation` 测试通过

---

## Technical Details

### 核心实现代码

#### 1. 修改 `generate_explanation()` (agent_service.py:1798-1860)

```python
async def generate_explanation(
    self,
    canvas_name: str,
    node_id: str,
    content: str,
    explanation_type: str = "oral",
    adjacent_context: Optional[str] = None,
    images: Optional[List[Dict[str, Any]]] = None,
    source_x: float = 0,
    source_y: float = 0,
    source_width: float = 400,
    source_height: float = 200,
    rag_context: Optional[str] = None,
    file_path: Optional[str] = None  # Story 12.E.2: 支持文件名 topic
) -> Dict[str, Any]:
    """Generate an explanation with user understanding dual-channel support."""

    # ... 现有代码: 读取黄色节点 ...

    # ✅ Story 12.E.2: 构建 user_understanding 字符串用于 JSON 字段
    user_understanding: Optional[str] = None
    if user_understandings:
        user_understanding = "\n\n".join(user_understandings)
        logger.info(f"[Story 12.E.2] user_understanding prepared: {len(user_understanding)} chars")

    # ... 现有代码: 构建 enhanced_context (保留双通道) ...

    # ✅ Story 12.E.2: 传递 user_understanding 到 call_explanation
    result = await self.call_explanation(
        content,
        explanation_type,
        context=enhanced_context,
        images=images,
        user_understanding=user_understanding  # 新增参数
    )

    # ... 后续处理 ...
```

#### 2. 关键日志追踪

```python
# 添加到 generate_explanation()
logger.info(
    f"[Story 12.E.2] Dual-channel user_understanding:\n"
    f"  - JSON field: {'set' if user_understanding else 'null'}\n"
    f"  - enhanced_context: {'contains' if '用户之前的个人理解' in enhanced_context else 'empty'}\n"
    f"  - content length: {len(user_understanding) if user_understanding else 0}"
)
```

---

## Dev Notes (技术验证引用)

### SDD 规范参考 (必填)

**API 端点**: 此 Story 不涉及 API 签名变更，仅修改内部服务层逻辑。

**相关代码文件**:

| 文件 | 行号 | 修改内容 |
|------|------|---------|
| `backend/app/services/agent_service.py` | 1751-1860 | `generate_explanation()` 方法 |
| `backend/app/services/agent_service.py` | 1370-1438 | `call_explanation()` 方法 (已支持参数) |
| `backend/app/services/agent_service.py` | 1698-1749 | `find_related_understanding_content()` (无需修改) |

**JSON 字段要求** (从 Agent 模板):

| Agent | 字段 | 必需性 | 来源 |
|-------|------|--------|------|
| `deep-decomposition` | `user_understanding` | **必需** | `.claude/agents/deep-decomposition.md:33` |
| `question-decomposition` | `user_understanding` | **必需** | `.claude/agents/question-decomposition.md:36` |
| 其他解释类 Agent | `user_understanding` | 可选 | 各 Agent 模板 |

### ADR 决策关联 (必填)

| ADR 编号 | 决策标题 | 对 Story 的影响 |
|----------|----------|----------------|
| N/A | 无直接相关 ADR | 此为 Bug 修复，遵循现有模式 |

**关键约束**:
- `user_understanding` 为 `Optional[str]`，无值时为 `None` (非空字符串)
- 保持双通道传递 (JSON 字段 + enhanced_context)
- 不修改 Agent 模板

### Testing

**测试文件位置**: `backend/tests/services/test_agent_service_user_understanding.py`

**测试标准**:
- pytest + pytest-asyncio
- Mock `call_explanation` 验证参数
- 覆盖率要求: >= 80%

**测试用例清单**:
1. `test_user_understanding_in_json_field()` - AC 2.1
2. `test_user_understanding_in_enhanced_context()` - AC 2.2
3. `test_user_understanding_in_both_channels()` - AC 2.2
4. `test_user_understanding_null_when_no_yellow_node()` - AC 2.3
5. `test_user_understanding_not_empty_string()` - AC 2.3
6. `test_topic_extraction_unchanged()` - AC 2.4

---

## Dependencies

### 外部依赖
- 无新增依赖

### Story 依赖
- 无 (可与 12.E.1, 12.E.3 并行开发)

### 被依赖
- **Story 12.E.6**: 集成测试 (依赖此 Story)

---

## Risks

### R1: 黄色节点内容过长

**风险描述**: 用户在多个黄色节点中填写大量内容，合并后可能过长

**可能性**: 低 (20%)

**缓解策略**:
- 保持现有的截断机制 (如有)
- 日志警告超长内容
- 不阻塞功能，仅记录

### R2: 向后兼容风险

**风险描述**: 修改 `generate_explanation()` 可能影响现有调用

**可能性**: 低 (10%)

**缓解策略**:
- `user_understanding` 为可选参数，默认 `None`
- 运行所有现有测试确保无回归

---

## DoD (Definition of Done)

### 代码完成
- [x] `generate_explanation()` 传递 `user_understanding` 参数
- [x] `user_understanding` 同时出现在 JSON 和 context
- [x] 无黄色节点时正确返回 `None`
- [x] 添加调试日志 `[Story 12.E.2]`

### 测试完成
- [x] AC 2.1 测试通过 (JSON 字段)
- [x] AC 2.2 测试通过 (双通道)
- [x] AC 2.3 测试通过 (null 处理)
- [x] AC 2.4 测试通过 (向后兼容)
- [x] 现有测试无回归 (129 tests passed)
- [x] 单元测试覆盖率 >= 80% (11 dedicated tests created)

### 文档完成
- [x] 方法 docstring 更新
- [x] 代码注释包含 Story 编号

### 集成完成
- [x] 无语法错误
- [x] 日志可追踪双通道传递

---

## QA Results

**审核人**: QA Agent (Quinn)
**审核日期**: 2025-12-16
**审核状态**: PASS

### Requirements Traceability Matrix

| AC | 验证方法 | 状态 | 证据 |
|----|----------|------|------|
| AC 2.1: JSON 字段传递 | 单元测试 + 代码审查 | ✅ PASS | `test_user_understanding_in_json_field`, `test_call_explanation_json_contains_user_understanding` 通过；`agent_service.py:1502-1507` JSON 构造正确 |
| AC 2.2: enhanced_context 同时包含 | 单元测试 + 代码审查 | ✅ PASS | `test_user_understanding_in_both_channels`, `test_user_understanding_in_enhanced_context` 通过；`agent_service.py:1935-1939` 构建 "用户之前的个人理解" 部分 |
| AC 2.3: 无黄色节点时正确处理 | 单元测试 + 代码审查 | ✅ PASS | `test_user_understanding_null_when_no_yellow_node`, `test_user_understanding_not_empty_string` 通过；`agent_service.py:1915` 初始化为 `None` |
| AC 2.4: 向后兼容 | 单元测试 + 代码审查 | ✅ PASS | `test_topic_extraction_unchanged`, `test_generate_explanation_returns_result` 通过；topic 提取逻辑未被修改 |

### Test Results Summary

| 测试文件 | 测试数量 | 通过 | 失败 |
|---------|---------|------|------|
| `test_agent_service_user_understanding.py` | 11 | 11 | 0 |

### Code Quality Assessment

| 维度 | 评分 | 说明 |
|------|------|------|
| 代码可读性 | ⭐⭐⭐⭐⭐ | 清晰的注释标注 Story 编号 (`[Story 12.E.2]`)，变量命名准确 |
| 错误处理 | ⭐⭐⭐⭐⭐ | try-except 包裹 canvas 文件读取，降级处理完善 |
| 日志追踪 | ⭐⭐⭐⭐⭐ | 双通道状态日志 `[Story 12.E.2] Dual-channel user_understanding:...` |
| 向后兼容 | ⭐⭐⭐⭐⭐ | `user_understanding` 参数默认为 `None`，不影响现有调用 |
| 测试覆盖 | ⭐⭐⭐⭐⭐ | 11 个专用测试覆盖所有 AC，包含边界情况 |

### NFR Compliance

| NFR | 状态 | 说明 |
|-----|------|------|
| 性能 | ✅ | 无新增 I/O 操作，仅在现有流程中添加字符串拼接 |
| 安全性 | ✅ | 无用户输入直接执行，内容通过 JSON 序列化 |
| 可维护性 | ✅ | 代码注释完整，Story 编号可追踪 |

### Issues Found

无

### Recommendations

1. 考虑为 `user_understanding` 添加长度限制，防止超长内容影响 AI 响应质量
2. 未来可考虑在日志中添加 `user_understanding` 内容摘要（前 100 字符）用于调试

### Gate Decision

**PASS** - 所有 AC 验证通过，代码质量符合标准，测试覆盖完整

---

## Change Log

| 版本 | 日期 | 作者 | 变更描述 |
|------|------|------|---------|
| 1.0 | 2025-12-16 | PO Agent (Sarah) | 初始版本，基于验证报告和代码分析创建 |
| 1.1 | 2025-12-16 | Dev Agent (James) | 实现完成：修改 agent_service.py 支持双通道传递，添加 11 个单元测试 |
| 1.2 | 2025-12-16 | QA Agent (Quinn) | QA 审核通过：所有 AC 验证通过，代码质量 5/5，创建 gate 文件 |

---

**Story 创建者**: PO Agent (Sarah)
**创建日期**: 2025-12-16
**最后更新**: 2025-12-16
**创建方式**: validate-next-story 验证后创建
