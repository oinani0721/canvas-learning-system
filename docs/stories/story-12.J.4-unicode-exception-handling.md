# Story 12.J.4: UnicodeEncodeError 显式异常处理

**Epic**: 12.J - Windows 编码架构修复
**优先级**: P0
**状态**: Complete
**预估**: 30 分钟
**完成时间**: 2025-12-17

---

## Story

**As a** Agent 端点,
**I want** 能显式捕获 UnicodeEncodeError,
**so that** 返回结构化的错误响应，而不是让异常传播导致 HTTP 500。

---

## 背景

当前所有 Agent 端点的异常处理使用通用的 `except Exception`。
当 UnicodeEncodeError 发生时，`logger.error(f"...{e}")` 可能再次触发编码错误，
导致级联失败。

**当前代码模式** (`backend/app/api/v1/endpoints/agents.py:714-718`):
```python
except Exception as e:
    cancel_request(cache_key)
    logger.error(f"decompose_basic failed: {e}", exc_info=True)  # 可能触发二次编码错误
    raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e
```

**问题**: Windows GBK 控制台无法编码 emoji/特殊 Unicode 字符，导致 `logger.error()` 抛出二次异常。

---

## 验收标准

- **AC1**: UnicodeEncodeError 返回结构化错误响应 (使用 `ENCODING_ERROR` 类型)
- **AC2**: 错误日志不触发二次编码错误 (使用 ASCII-safe 诊断信息)
- **AC3**: 所有 11 个 Agent 端点都有显式处理
- **AC4**: 编码错误包含安全诊断信息 (hex position, char code)

---

## Tasks / Subtasks

- [x] **Task 1**: 创建编码错误处理辅助函数 (AC: 1, 2, 4)
  - [x] 1.1 在 `agents.py` 顶部添加 `_create_encoding_error_response()` 函数
  - [x] 1.2 实现安全的 ASCII 诊断信息生成 (position + hex char code)
  - [x] 1.3 确保日志使用 ASCII 安全格式

- [x] **Task 2**: 为 Decomposition 端点添加 UnicodeEncodeError 处理 (AC: 3)
  - [x] 2.1 `POST /decompose/basic` - 添加 `except UnicodeEncodeError` 块
  - [x] 2.2 `POST /decompose/deep` - 添加 `except UnicodeEncodeError` 块
  - [x] 2.3 `POST /decompose/question` - 添加 `except UnicodeEncodeError` 块

- [x] **Task 3**: 为 Explanation 端点添加 UnicodeEncodeError 处理 (AC: 3)
  - [x] 3.1 更新 `_call_explanation()` 辅助函数 - 添加 `except UnicodeEncodeError` 块
  - [x] 3.2 验证覆盖 6 个 explain 端点: oral, clarification, comparison, memory, four-level, example

- [x] **Task 4**: 为其他 Agent 端点添加 UnicodeEncodeError 处理 (AC: 3)
  - [x] 4.1 `POST /score` - 添加 `except UnicodeEncodeError` 块
  - [x] 4.2 `POST /verification/question` - 添加 `except UnicodeEncodeError` 块

- [x] **Task 5**: 单元测试 (AC: 1, 2, 3, 4)
  - [x] 5.1 创建 `test_agents_encoding.py` 测试文件
  - [x] 5.2 测试 UnicodeEncodeError 返回结构化响应
  - [x] 5.3 测试诊断信息包含正确的 hex position

---

## Dev Notes

### SDD规范参考 (必填)

**API端点** (从 OpenAPI specs):
- 规范来源: `[Source: specs/api/agent-api.openapi.yml#L779-793]`
- 错误类型枚举: `AgentErrorType` - 包含 `ENCODING_ERROR` (Story 12.J.4 添加)
- 错误响应Schema: `AgentError` (包含 `error_type`, `message`, `is_retryable`, `diagnostic`)

```yaml
# specs/api/agent-api.openapi.yml - AgentErrorType
AgentErrorType:
  enum:
    - CONFIG_MISSING
    - LLM_TIMEOUT
    - LLM_INVALID_RESPONSE
    - NETWORK_TIMEOUT
    - FILE_NOT_FOUND
    - LLM_RATE_LIMIT
    - ENCODING_ERROR      # Story 12.J.4 新增
    - UNKNOWN
```

**数据Schema** (从 JSON Schema):
- 模型名称: `AgentError`
- Schema来源: `[Source: specs/api/agent-api.openapi.yml#L795-822]`
- 必填字段: `error_type`, `message`
- 可选字段: `is_retryable`, `diagnostic`, `details`, `bug_id`

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| ADR-009 | 错误处理与重试策略 | 编码错误属于 RETRYABLE 类别 (用户可换内容重试) |

**关键约束** (从 ADR-009 Consequences 提取):
- **约束1**: 错误必须包含 `is_retryable` 字段指示可重试性
- **约束2**: 错误日志必须使用 UTF-8 编码 (配合 Story 12.J.1)
- **约束3**: Agent 相关错误码使用 5xxx 范围

来源引用: `[Source: ADR-009 - 错误分类体系]`

### 受影响的端点 (11个 - 已验证)

**Decomposition 端点 (3个)**:
| # | 端点路径 | 代码位置 |
|---|----------|----------|
| 1 | `POST /api/v1/agents/decompose/basic` | `agents.py:621-719` |
| 2 | `POST /api/v1/agents/decompose/deep` | `agents.py:721-817` |
| 3 | `POST /api/v1/agents/decompose/question` | `agents.py:1455-1553` |

**Explanation 端点 (6个 - 通过 `_call_explanation` 统一处理)**:
| # | 端点路径 | 代码位置 |
|---|----------|----------|
| 4 | `POST /api/v1/agents/explain/oral` | `agents.py:1170-1197` |
| 5 | `POST /api/v1/agents/explain/clarification` | `agents.py:1199-1226` |
| 6 | `POST /api/v1/agents/explain/comparison` | `agents.py:1228-1255` |
| 7 | `POST /api/v1/agents/explain/memory` | `agents.py:1257-1284` |
| 8 | `POST /api/v1/agents/explain/four-level` | `agents.py:1286-1313` |
| 9 | `POST /api/v1/agents/explain/example` | `agents.py:1315-1342` |

**Other 端点 (2个)**:
| # | 端点路径 | 代码位置 |
|---|----------|----------|
| 10 | `POST /api/v1/agents/score` | `agents.py:824-914` |
| 11 | `POST /api/v1/agents/verification/question` | `agents.py:1349-1453` |

### 代码变更模式

**辅助函数** (添加在 `agents.py` 顶部，约 Line 175 后):
```python
def _create_encoding_error_response(
    e: UnicodeEncodeError,
    endpoint_name: str,
    cache_key: str = ""
) -> HTTPException:
    """
    Story 12.J.4: 创建编码错误的标准化 HTTP 响应.

    使用 ASCII-safe 诊断信息避免二次编码错误。

    [Source: specs/api/agent-api.openapi.yml#AgentError]
    [Source: ADR-009 - 错误分类体系]
    """
    if cache_key:
        cancel_request(cache_key)

    # AC4: 安全诊断信息 (ASCII only)
    safe_diagnostic = f"position {e.start}"
    if hasattr(e, 'object') and e.start < len(e.object):
        try:
            char_code = ord(e.object[e.start])
            safe_diagnostic += f", char U+{char_code:04X}"
        except Exception:
            pass

    # AC2: ASCII-safe 日志
    logger.error(
        f"[Story 12.J.4] Encoding error in {endpoint_name}: {safe_diagnostic}"
    )

    # AC1: 结构化响应 (对齐 AgentError schema)
    return HTTPException(
        status_code=500,
        detail={
            "error_type": "ENCODING_ERROR",
            "message": "Text encoding error - please ensure content uses UTF-8",
            "is_retryable": True,
            "diagnostic": safe_diagnostic,
        }
    )
```

**端点修改模式** (在每个端点的 `except Exception` 之前添加):
```python
except UnicodeEncodeError as e:
    raise _create_encoding_error_response(e, "decompose_basic", cache_key) from e
except Exception as e:
    # 现有通用处理器...
```

### Testing

**测试文件位置**: `backend/tests/api/v1/endpoints/test_agents_encoding.py`

**测试框架**: pytest + pytest-asyncio

**测试用例**:
```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_unicode_encode_error_returns_encoding_error_type(client):
    """AC1: UnicodeEncodeError 返回 ENCODING_ERROR 类型."""
    with patch(
        "app.services.agent_service.AgentService.decompose_basic",
        side_effect=UnicodeEncodeError('gbk', 'test\U0001F525emoji', 4, 5, 'illegal')
    ):
        response = await client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": "test.canvas", "node_id": "node123"}
        )

    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["error_type"] == "ENCODING_ERROR"
    assert data["detail"]["is_retryable"] is True
    assert "diagnostic" in data["detail"]


@pytest.mark.asyncio
async def test_encoding_error_diagnostic_contains_hex_position(client):
    """AC4: 诊断信息包含 hex position."""
    with patch(
        "app.services.agent_service.AgentService.decompose_basic",
        side_effect=UnicodeEncodeError('gbk', 'abc\U0001F525', 3, 4, 'illegal')
    ):
        response = await client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": "test.canvas", "node_id": "node123"}
        )

    diagnostic = response.json()["detail"]["diagnostic"]
    assert "position 3" in diagnostic
    assert "U+1F525" in diagnostic  # Fire emoji
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 修改范围 (11个端点) | 中 | 使用统一辅助函数，减少重复代码 |
| 遗漏端点 | 中 | 使用 grep 验证: `grep -n "except Exception" agents.py` |
| 测试覆盖不足 | 低 | 参数化测试覆盖多个端点 |

---

## Definition of Done

- [x] 辅助函数 `_create_encoding_error_response()` 已添加
- [x] 所有 11 个 Agent 端点添加 `except UnicodeEncodeError` 处理
- [x] 错误日志使用 ASCII-safe 格式 (无 emoji/Unicode)
- [x] 返回结构化 `ENCODING_ERROR` 响应 (对齐 OpenAPI schema)
- [x] 单元测试通过 (pytest) - 16 tests passed
- [x] OpenAPI spec 已更新 (已完成: `ENCODING_ERROR` 已添加到 `AgentErrorType`)

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-17 | 1.0 | 初始创建 | PO Agent |
| 2025-12-17 | 2.0 | 验证修复: 端点数量11个, 路径校正, 添加必填sections | PO Agent (Sarah) |

---

## QA Results

### Review Date: 2025-12-17

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall: EXCELLENT** ✅

Story 12.J.4 demonstrates exemplary implementation with comprehensive coverage across all 11 Agent endpoints. The `_create_encoding_error_response()` helper function (agents.py:183-232) follows best practices:

1. **Centralized Error Handling**: Single helper function eliminates code duplication across 11 endpoints
2. **ASCII-Safe Diagnostics**: Position and hex char code (U+XXXX) format prevents secondary encoding errors on Windows GBK console
3. **Structured Responses**: Aligns with AgentError schema (OpenAPI spec lines 796-822)
4. **ADR-009 Compliance**: ENCODING_ERROR correctly marked as RETRYABLE (users can retry with different content)

### Acceptance Criteria Verification

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC1 | UnicodeEncodeError returns structured ENCODING_ERROR | ✅ PASS | agents.py:224-232 - HTTPException with error_type, message, is_retryable, diagnostic |
| AC2 | Error logs don't trigger secondary errors | ✅ PASS | agents.py:219-221 - ASCII-only log format `[Story 12.J.4] Encoding error in {endpoint}: {safe_diagnostic}` |
| AC3 | All 11 Agent endpoints have explicit handling | ✅ PASS | Verified at lines 774, 875, 1214, 975, 1520, 1623 |
| AC4 | Encoding error includes safe diagnostic info | ✅ PASS | agents.py:209-216 - `position {n}, char U+{XXXX}` format |

### Endpoint Coverage Matrix (AC3 Verification)

| # | Endpoint | Handler Location | Status |
|---|----------|-----------------|--------|
| 1 | POST /decompose/basic | agents.py:774-776 | ✅ |
| 2 | POST /decompose/deep | agents.py:875-877 | ✅ |
| 3 | POST /decompose/question | agents.py:1623-1625 | ✅ |
| 4-9 | POST /explain/* (6 endpoints) | _call_explanation:1214-1216 | ✅ |
| 10 | POST /score | agents.py:975-977 | ✅ |
| 11 | POST /verification/question | agents.py:1520-1522 | ✅ |

### Test Coverage Assessment

**Test File**: `backend/tests/api/v1/endpoints/test_agents_encoding.py`

| Test Category | Tests | Coverage |
|--------------|-------|----------|
| AC1: Structured Response | 2 | ✅ Full |
| AC2: ASCII-Safe Logging | 1 | ✅ Full |
| AC3: Endpoint Coverage | 6 | ✅ Full (via source inspection) |
| AC4: Diagnostic Info | 3 | ✅ Full |
| Edge Cases | 2 | ✅ Good (empty object, out-of-bounds) |
| Cache Cleanup | 2 | ✅ Full |

**Total Tests**: 16 tests (all passing per DoD)

### Refactoring Performed

None required - implementation is clean and well-structured.

### Compliance Check

- Coding Standards: ✓ Source comments reference specs/ADRs
- Project Structure: ✓ Helper function at correct location (agents.py:175-232)
- Testing Strategy: ✓ Unit tests + source inspection for coverage verification
- All ACs Met: ✓ All 4 acceptance criteria fully satisfied

### Improvements Checklist

- [x] Helper function `_create_encoding_error_response()` implemented correctly
- [x] All 11 Agent endpoints have explicit UnicodeEncodeError handlers
- [x] Error logs use ASCII-safe format (no emoji/Unicode)
- [x] Returns structured ENCODING_ERROR response (aligned with OpenAPI schema)
- [x] Unit tests comprehensive (16 tests, edge cases covered)
- [x] OpenAPI spec updated (ENCODING_ERROR in AgentErrorType enum, diagnostic field added)
- [x] ADR-009 compliance verified (RETRYABLE category, 5xxx error code range)

### Security Review

**No Concerns**: Error handling properly sanitizes diagnostic output to ASCII-safe format, preventing:
1. Log injection attacks via Unicode
2. Information leakage of raw content
3. Secondary encoding failures

### Performance Considerations

**Minimal Impact**: The helper function adds negligible overhead (~2 string operations for diagnostic formatting).

### ADR Compliance

| ADR | Requirement | Compliance |
|-----|-------------|------------|
| ADR-009 | Error must include is_retryable field | ✅ `is_retryable: True` |
| ADR-009 | Agent errors use 5xxx code range | ✅ ENCODING_ERROR = 5001 |
| ADR-009 | Error logs use UTF-8 encoding | ✅ Combined with Story 12.J.1 logging.py config |

### Files Modified During Review

None - no modifications required.

### Gate Status

Gate: **PASS** → docs/qa/gates/12.J.4-unicode-exception-handling.yml
Risk profile: Low (defensive error handling, no behavior change for happy path)

### Recommended Status

✓ **Ready for Done** - All acceptance criteria met, tests passing, ADR compliance verified.
