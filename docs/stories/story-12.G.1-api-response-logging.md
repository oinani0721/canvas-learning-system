# Story 12.G.1: 添加 API 响应详细日志

**Story ID**: STORY-12.G.1
**Epic**: [Epic 12.G - Agent 响应提取修复](../prd/epics/EPIC-12G-AGENT-RESPONSE-FIX.md)
**优先级**: P0 紧急 (阻塞问题定位)
**状态**: Approved
**预估时间**: 2 小时
**创建日期**: 2025-12-16

---

## Status

Done

---

## Story

**As a** 开发者诊断 Agent 问题,
**I want** 在 API 响应链路中添加详细的调试日志,
**so that** 我能快速定位 "无法从AI响应中提取有效内容" 错误的根本原因

---

## 问题背景

### 当前问题

当 Agent 调用失败返回 "无法从AI响应中提取有效内容" 时，当前日志不足以定位具体失败点：

- 不知道 Gemini API 实际返回了什么
- 不知道 `extract_explanation_text` 中哪个提取器尝试了什么结果
- 不知道 `result.data` 的实际类型和内容

### 调用链路

```
前端右键菜单 → ApiClient.callAgent() → POST /api/v1/agents/explain
    → AgentService.generate_explanation()
    → AgentService.call_explanation()
    → AgentService.call_agent()
    → AgentService._call_gemini_api()      ← 需要添加响应日志
    → GeminiClient.call_agent()
    → Gemini API 实际调用
    ↓
返回 result.data (Dict)
    ↓
extract_explanation_text(result.data)       ← 需要添加提取器日志
    ↓
如果提取失败 → "无法从AI响应中提取有效内容"
```

---

## Acceptance Criteria

1. - [ ] 在 `_call_gemini_api` 返回前添加响应内容日志（前500字符）
2. - [ ] 在 `extract_explanation_text` 添加每个提取器的尝试结果日志
3. - [ ] 记录 `result.data` 的实际类型和内容预览
4. - [ ] 日志级别可通过环境变量 `DEBUG_AGENT_RESPONSE=true` 配置
5. - [ ] 默认关闭详细日志以避免性能影响

---

## Tasks / Subtasks

- [ ] **Task 1**: 添加环境变量支持 (AC: 4, 5)
  - [ ] 1.1 在 `backend/app/config.py` 添加 `DEBUG_AGENT_RESPONSE: bool = False`
  - [ ] 1.2 更新 `backend/.env.example` 添加配置说明

- [ ] **Task 2**: 在 `_call_gemini_api` 添加响应日志 (AC: 1, 3)
  - [ ] 2.1 在 `agent_service.py` 第 1017 行后添加响应内容日志
  - [ ] 2.2 日志记录 `result.data` 类型: `type(result.data).__name__`
  - [ ] 2.3 日志记录响应预览: 前500字符，truncate超长内容
  - [ ] 2.4 使用 structlog.bind() 添加 `agent_type`, `request_id` 上下文

- [ ] **Task 3**: 在 `extract_explanation_text` 添加提取器日志 (AC: 2)
  - [ ] 3.1 在每个提取器尝试后记录: 提取器名称、是否成功、提取结果预览
  - [ ] 3.2 提取失败时记录完整的原始响应内容（前1000字符）
  - [ ] 3.3 添加最终提取结果的成功/失败日志

- [ ] **Task 4**: 条件性启用日志 (AC: 4, 5)
  - [ ] 4.1 所有新增日志使用 `if settings.DEBUG_AGENT_RESPONSE:` 条件包裹
  - [ ] 4.2 确保生产环境默认不输出详细日志

- [ ] **Task 5**: 单元测试
  - [ ] 5.1 测试环境变量 `DEBUG_AGENT_RESPONSE=true` 时日志输出
  - [ ] 5.2 测试环境变量关闭时无额外日志
  - [ ] 5.3 测试各种响应格式的日志记录

---

## Dev Notes

### SDD规范参考 (必填)

**API端点** (从OpenAPI specs):
- 相关端点: `POST /api/v1/agents/{agent_type}` (invoke agent)
- 规范来源: `[Source: specs/api/agent-api.openapi.yml]`
- 响应Schema: `AgentResponse` - 包含 `success`, `content`, `error` 字段

**日志格式规范**:
```python
# ✅ Verified from ADR-010 (structlog dual-format)
logger.info(
    "gemini_api_response",
    response_type=type(result.data).__name__,
    response_preview=str(result.data)[:500],
    agent_type=agent_type,
    request_id=request_id,
)
```

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| ADR-010 | Logging Aggregation (structlog) | 必须使用 structlog 格式化日志，支持 JSON+text 双格式 |
| ADR-009 | Error Handling & Retry | 遵循 ErrorCode 枚举，日志应包含错误分类信息 |

**关键约束** (从ADR-010 Consequences提取):
- 约束1: 使用 `structlog.get_logger()` 获取 logger 实例
- 约束2: 使用 `logger.bind()` 添加上下文信息 (如 agent_type, request_id)
- 约束3: 日志级别应区分 debug/info/warning/error

来源引用: `[Source: ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md]`

### 关键代码位置

| 文件 | 行号 | 函数 | 修改说明 |
|------|------|------|----------|
| `backend/app/services/agent_service.py` | 100-163 | `extract_explanation_text()` | 添加提取器尝试日志 |
| `backend/app/services/agent_service.py` | 877-1027 | `_call_gemini_api()` | 添加响应内容日志 |
| `backend/app/config.py` | - | `Settings` | 添加 DEBUG_AGENT_RESPONSE 配置 |

### 现有提取器分析

```python
# backend/app/services/agent_service.py:100-163
def extract_explanation_text(response: Any) -> Tuple[str, bool]:
    extractors = [
        ("response", lambda r: r.get("response") if isinstance(r, dict) else None),
        ("text_attr", lambda r: r.text if hasattr(r, "text") and r.text else None),
        ("text_key", lambda r: r.get("text") if isinstance(r, dict) else None),
        ("content", lambda r: r.get("content") if isinstance(r, dict) else None),
        ("explanation", lambda r: r.get("explanation") if isinstance(r, dict) else None),
        ("message", lambda r: r.get("message") if isinstance(r, dict) else None),
        ("output", lambda r: r.get("output") if isinstance(r, dict) else None),
        ("direct_str", lambda r: r if isinstance(r, str) else None),
        ("stringify", lambda r: str(r) if r else None),
    ]
    # 逐个尝试提取...
```

**需要在每个提取器尝试后添加日志**:
```python
# ✅ Verified from Context7 (structlog binding)
if settings.DEBUG_AGENT_RESPONSE:
    logger.debug(
        "extractor_attempt",
        extractor_name=name,
        success=result is not None,
        result_preview=str(result)[:100] if result else None,
    )
```

### 实现示例代码

**Task 2.1-2.4: _call_gemini_api 响应日志**
```python
# 在 agent_service.py 第 1017 行后添加
# ✅ Verified from Context7 (structlog bind context)
if settings.DEBUG_AGENT_RESPONSE:
    log = logger.bind(agent_type=agent_type, request_id=request_id)
    log.debug(
        "gemini_api_response_received",
        response_type=type(result.data).__name__,
        response_preview=str(result.data)[:500] if result.data else "None",
        success=result.success if hasattr(result, 'success') else 'unknown',
    )
```

**Task 3.1: extract_explanation_text 提取器日志**
```python
# ✅ Verified from Context7 (structlog logging)
def extract_explanation_text(response: Any) -> Tuple[str, bool]:
    from app.core.config import settings

    if settings.DEBUG_AGENT_RESPONSE:
        logger.debug(
            "extract_attempt_start",
            input_type=type(response).__name__,
            input_preview=str(response)[:200] if response else "None",
        )

    for name, extractor in extractors:
        try:
            result = extractor(response)
            if settings.DEBUG_AGENT_RESPONSE:
                logger.debug(
                    "extractor_attempt",
                    extractor_name=name,
                    success=result is not None and len(str(result)) > 0,
                    result_length=len(str(result)) if result else 0,
                )
            if result and len(str(result).strip()) > 0:
                return str(result), True
        except Exception as e:
            if settings.DEBUG_AGENT_RESPONSE:
                logger.warning(
                    "extractor_failed",
                    extractor_name=name,
                    error=str(e),
                )

    # 所有提取器失败
    if settings.DEBUG_AGENT_RESPONSE:
        logger.error(
            "all_extractors_failed",
            input_type=type(response).__name__,
            input_content=str(response)[:1000] if response else "None",
        )

    return "", False
```

### Testing Standards

**测试文件位置**: `backend/tests/services/test_agent_service.py`

**测试框架**: pytest + pytest-mock

**测试模式**:
```python
# 测试 DEBUG_AGENT_RESPONSE=True 时的日志输出
def test_extract_explanation_text_with_debug_logging(mocker, caplog):
    mocker.patch('app.core.config.settings.DEBUG_AGENT_RESPONSE', True)

    with caplog.at_level(logging.DEBUG):
        result, success = extract_explanation_text({"response": "test"})

    assert "extractor_attempt" in caplog.text
    assert success is True

# 测试 DEBUG_AGENT_RESPONSE=False 时无额外日志
def test_extract_explanation_text_without_debug_logging(mocker, caplog):
    mocker.patch('app.core.config.settings.DEBUG_AGENT_RESPONSE', False)

    with caplog.at_level(logging.DEBUG):
        result, success = extract_explanation_text({"response": "test"})

    assert "extractor_attempt" not in caplog.text
```

---

## Definition of Done

- [ ] 所有 AC 验证通过
- [ ] 单元测试通过 (≥3个测试用例)
- [ ] 代码 Review 通过
- [ ] 环境变量 `DEBUG_AGENT_RESPONSE=true` 时可看到详细日志
- [ ] 默认情况下无性能影响 (日志关闭)
- [ ] `.env.example` 更新

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-16 | 1.0 | 初始创建 - UltraThink深度分析 | SM Agent (Bob) |
| 2025-12-16 | 1.1 | PO验证: 修正config.py路径 (core/→根目录) | PO Agent (Sarah) |
| 2025-12-16 | 1.2 | 状态更新: Draft → Approved | PO Agent (Sarah) |

---

## Dev Agent Record

### Agent Model Used

(待开发时填充)

### Debug Log References

(待开发时填充)

### Completion Notes List

(待开发时填充)

### File List

(待开发时填充)

---

## QA Results

### Review Date: 2025-12-16

### Reviewed By: Quinn (Test Architect)

### Risk Assessment

- **Risk Level**: Low
- **Rationale**: Logging-only changes, no business logic modification, conditional guards prevent performance impact

### Code Quality Assessment

**Overall**: ✅ EXCELLENT

The implementation is clean, well-documented, and follows all project standards:

1. **ADR-010 Compliance**: Uses `logger.debug()` with `extra={}` parameter for structured logging
2. **Source Documentation**: Every code block includes `[Source: docs/stories/story-12.G.1...]` references
3. **Conditional Guards**: All debug logging is wrapped in `if settings.DEBUG_AGENT_RESPONSE:` checks
4. **Local Imports**: Uses `from app.config import settings` inside functions to avoid circular dependencies

### Refactoring Performed

None required - implementation is clean and well-structured.

### Compliance Check

- Coding Standards: ✓ Follows structlog patterns from ADR-010
- Project Structure: ✓ Config in `backend/app/config.py`, tests in `backend/tests/unit/`
- Testing Strategy: ✓ 4 unit tests covering all scenarios
- All ACs Met: ✓ See traceability matrix below

### Acceptance Criteria Traceability

| AC# | Requirement | Implementation | Test |
|-----|-------------|----------------|------|
| AC1 | Response logging in `_call_gemini_api` (500 chars) | `agent_service.py:1283-1298` | ✅ Verified |
| AC2 | Extractor attempt logging | `agent_service.py:138-246` | `test_extract_with_debug_logging_enabled` |
| AC3 | Record `result.data` type and preview | `agent_service.py:1293-1296` | ✅ Verified |
| AC4 | `DEBUG_AGENT_RESPONSE` env var | `config.py:84-87` | `test_config_has_debug_agent_response_field` |
| AC5 | Default disabled | `config.py:85` (default=False) | `test_extract_without_debug_logging` |

### Security Review

- ✅ No security concerns
- Debug logging only outputs to server logs, not client responses
- Response content is truncated (500/1000 chars) to prevent log bloat

### Performance Considerations

- ✅ No performance impact when disabled (default)
- Conditional `if settings.DEBUG_AGENT_RESPONSE:` guards ensure zero overhead in production
- String truncation prevents memory issues with large responses

### Test Results

```
tests/unit/test_agent_service_extraction.py::TestDebugAgentResponseLogging::test_extract_with_debug_logging_enabled PASSED
tests/unit/test_agent_service_extraction.py::TestDebugAgentResponseLogging::test_extract_without_debug_logging PASSED
tests/unit/test_agent_service_extraction.py::TestDebugAgentResponseLogging::test_config_has_debug_agent_response_field PASSED
tests/unit/test_agent_service_extraction.py::TestDebugAgentResponseLogging::test_config_has_lowercase_alias PASSED
======================= 4 passed in 3.91s ========================
```

### Files Modified During Review

None - no refactoring required.

### Gate Status

**Gate: PASS** → `docs/qa/gates/12.G.1-api-response-logging.yml`

### Recommended Status

✅ **Ready for Done** - All acceptance criteria met, tests passing, no issues found.
