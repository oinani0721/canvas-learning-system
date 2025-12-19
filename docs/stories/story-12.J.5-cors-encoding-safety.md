# Story 12.J.5: CORSExceptionMiddleware 编码安全

**Epic**: 12.J - Windows 编码架构修复
**优先级**: P1
**状态**: Complete
**预估**: 15 分钟
**完成时间**: 2025-12-17

---

## 用户故事

作为一个 FastAPI 错误处理中间件，
我希望能安全地将任何异常消息转换为 JSON 响应，
以便即使异常消息包含无法编码的字符，也不会导致级联失败。

---

## 背景

`CORSExceptionMiddleware` 是全局异常处理器。当 `str(e)` 或 JSON 序列化过程中
发生 UnicodeEncodeError，会导致整个响应失败，返回不可读的错误。

**当前代码** (`backend/app/main.py:141-207`):
```python
async def dispatch(self, request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # ...
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": str(e),  # str(e) 可能触发 UnicodeEncodeError
                "error_type": type(e).__name__,
                "bug_id": bug_id,
            }
        )
```

---

## 验收标准

- **AC1**: 任何异常消息都能安全编码到 JSON 响应
- **AC2**: 不会因为错误处理器中的编码问题导致级联失败
- **AC3**: 现有 CORS 功能保持不变

---

## Tasks / Subtasks

- [x] Task 1: 安全化 `str(e)` 调用 (AC: 1, 2)
  - [x] 添加 try-except 包装 `str(e)` 捕获 UnicodeEncodeError/UnicodeDecodeError
  - [x] 使用 `repr(e)` 作为 ASCII 安全的后备方案
- [x] Task 2: 添加 UTF-8 安全编码处理 (AC: 1)
  - [x] 使用 `encode('utf-8', errors='replace').decode('utf-8')` 处理消息
  - [x] 限制消息长度为 500 字符防止响应过大
- [x] Task 3: 安全化请求参数提取 (AC: 2)
  - [x] 添加 `_safe_extract_request_params` 方法
  - [x] 对每个字符串值进行 UTF-8 安全编码
- [x] Task 4: 更新日志输出使用安全消息 (AC: 2)
  - [x] 使用 safe_message 记录日志避免日志系统编码错误
  - [x] 限制日志消息长度为 200 字符
- [x] Task 5: 编写单元测试
  - [x] 添加 `test_exception_with_unicode_message` 测试
  - [x] 添加 `test_exception_with_unencodable_chars` 测试

---

## 技术方案

### 修改文件

`backend/app/main.py`

### 代码变更

```python
class CORSExceptionMiddleware(BaseHTTPMiddleware):
    """
    Handle exceptions with CORS headers.

    [Source: Story 12.J.5 - 编码安全增强]
    [Source: Story 21.5.1 - CORS异常中间件原始实现]
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Story 12.J.5: 安全化错误消息
            try:
                error_message = str(e)
            except (UnicodeEncodeError, UnicodeDecodeError):
                # 使用 repr() 作为 ASCII 安全的后备
                error_message = repr(e)

            # 确保消息可以安全编码为 JSON
            safe_message = error_message.encode('utf-8', errors='replace').decode('utf-8')

            # 保留现有 CORS 逻辑 (Story 21.5.1)
            origin = request.headers.get("origin", "")
            allowed_origin = origin if origin in settings.cors_origins_list else ""
            if not allowed_origin and "app://obsidian.md" in settings.cors_origins_list:
                allowed_origin = "app://obsidian.md"

            # 记录原始错误（使用安全消息）
            logger.error(
                f"[CORSExceptionMiddleware] Unhandled exception: {safe_message[:200]}",
                exc_info=True
            )

            # 构建请求参数（安全化）
            request_params = self._safe_extract_request_params(request)

            # 记录到 bug tracker
            bug_id = bug_tracker.log_error(
                endpoint=str(request.url.path),
                error=e,
                request_params=request_params,
            )

            # 返回安全的 JSON 响应
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": safe_message[:500],  # 限制长度
                    "error_type": type(e).__name__,  # 保持动态类型名
                    "bug_id": bug_id,
                },
                headers={
                    "Access-Control-Allow-Origin": allowed_origin,  # 保持动态 origin
                    "Access-Control-Allow-Credentials": "true",     # 保持 credentials
                }
            )

    def _safe_extract_request_params(self, request: Request) -> dict:
        """
        Story 12.J.5: 安全提取请求参数.

        确保所有字符串都可以安全序列化为 JSON。
        """
        try:
            query_params = dict(request.query_params)
            # 安全化每个值
            safe_params = {}
            for key, value in query_params.items():
                if isinstance(value, str):
                    safe_params[key] = value.encode('utf-8', errors='replace').decode('utf-8')
                else:
                    safe_params[key] = value
            return {
                "path": str(request.url.path),
                "method": request.method,
                "query_params": safe_params,
            }
        except Exception:
            return {
                "path": "[extraction failed]",
                "method": request.method,
                "query_params": {},
            }
```

---

## Dev Notes

### SDD规范参考 (必填)

**API端点**: N/A (中间件修改，无新端点)

**数据Schema**:
- 模型名称: Error Response
- Schema来源: `[Source: specs/data/error-response.schema.json]`
- 必填字段: `code` (integer), `message` (string)
- 可选字段: `error_type` (string), `details` (object)
- 验证规则: `additionalProperties: false`

**现有实现参考**:
- 中间件位置: `[Source: backend/app/main.py:141-207]`
- 现有测试: `[Source: backend/tests/test_cors_exception.py]`

**关键约束**:
- `error_type` 必须使用 `type(e).__name__` 保持动态值 (Schema 要求)
- CORS 响应头必须使用动态 `allowed_origin` (不能用 `*`)
- 必须保留 `Access-Control-Allow-Credentials: "true"`

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| ADR-010 | Logging聚合策略 | 使用 safe_message 记录日志，避免日志编码错误 |
| Story 21.5.1 | CORS异常中间件 | 保持现有 CORS 头逻辑不变，只增加编码安全处理 |
| Epic 12.I | Agent日志编码修复 | 与日志 UTF-8 配置协同工作 |

**关键约束**:
- 本 Story 是增量修改，不改变现有 CORS 行为
- 编码安全处理在响应生成前完成
- 与 Story 12.J.1 (日志 UTF-8 包装) 协同防止级联失败

### Testing

**测试文件位置**: `backend/tests/test_cors_exception.py` (添加到现有文件)

**测试标准**:
- 使用 pytest + pytest-asyncio
- Mock 异常端点进行隔离测试
- 验证 JSON 响应可解析性

**测试框架**:
- pytest
- unittest.mock (patch, MagicMock)
- fastapi.testclient

---

## 测试计划

```python
# 添加到 backend/tests/test_cors_exception.py

import pytest
from unittest.mock import patch, MagicMock


class TestStory12J5_EncodingSafety:
    """
    Story 12.J.5: CORSExceptionMiddleware 编码安全测试.

    验证异常消息的编码安全处理。
    [Source: docs/stories/story-12.J.5-cors-encoding-safety.md]
    """

    def test_exception_with_unicode_message(self, cors_test_client):
        """
        AC1: 包含 Unicode 的异常消息应被安全处理.

        Given: 异常消息包含中文和 emoji
        When: 中间件处理异常
        Then: 响应是有效的 JSON，包含安全编码的消息
        """
        # 使用包含 Unicode 的异常
        class UnicodeException(Exception):
            def __str__(self):
                return "测试错误 🔥 无法处理"

        with patch.object(
            cors_test_client.app,
            "route",
            side_effect=UnicodeException()
        ):
            # 此处需要根据实际测试设置调整
            pass

        # 验证响应是有效 JSON
        # assert response.status_code == 500
        # data = response.json()
        # assert "message" in data
        # assert "bug_id" in data

    def test_exception_with_unencodable_chars(self, cors_test_client):
        """
        AC1, AC2: 无法编码的字符应被替换，不导致级联失败.

        Given: 异常的 __str__ 方法抛出 UnicodeEncodeError
        When: 中间件处理异常
        Then: 使用 repr(e) 作为后备，响应是有效 JSON
        """
        class BadException(Exception):
            def __str__(self):
                raise UnicodeEncodeError('gbk', '测试', 0, 1, 'test')

        # 验证中间件不会因编码错误而崩溃
        # 响应应该是有效的 JSON
        pass

    def test_cors_headers_preserved(self, cors_test_client):
        """
        AC3: 现有 CORS 功能保持不变.

        Given: 请求来自 app://obsidian.md
        When: 端点抛出包含 Unicode 的异常
        Then: 响应包含正确的 CORS 头
        """
        response = cors_test_client.get(
            "/error-500",
            headers={"Origin": "app://obsidian.md"}
        )

        assert response.status_code == 500
        assert response.headers["access-control-allow-origin"] == "app://obsidian.md"
        assert response.headers["access-control-allow-credentials"] == "true"

        # 验证 JSON 可解析
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "error_type" in data
```

---

## Definition of Done

- [x] `str(e)` 调用被 try-except 包装
- [x] 使用 `encode/decode` 替换无法编码的字符
- [x] 错误日志使用安全消息
- [x] 保留动态 CORS origin 和 credentials
- [x] 保留动态 error_type (type(e).__name__)
- [x] 单元测试通过 (7 new tests in TestStory12J5_EncodingSafety)
- [x] 现有 test_cors_exception.py 测试仍通过 (31 tests total)

---

## Change Log

| 日期 | 版本 | 描述 | 作者 |
|------|------|------|------|
| 2025-12-17 | 1.0 | 初始创建 | PO |
| 2025-12-17 | 1.1 | 验证修复: 添加必填章节, 修复 CORS/error_type 冲突 | PO (Sarah) |

---

## Conflict Resolutions (Step 8d)

| # | 冲突 | 决定 | 变更 | 解决者 | 时间 |
|---|------|------|------|--------|------|
| 1 | Story CORS 用 `*` vs 当前用动态 origin | 接受当前代码模式 | 更新代码示例保留动态 CORS | 用户 | 2025-12-17 |
| 2 | Story error_type 硬编码 vs Schema 期望动态 | 接受 SoT 层级 | 更新代码示例用 `type(e).__name__` | 用户 | 2025-12-17 |

---

## QA Results

### Review Date: 2025-12-17

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall: EXCELLENT**

实现代码完全符合 Story 要求，采用了防御性编程模式，具有多层编码安全机制：

1. **异常消息安全化** (`main.py:265-274`):
   - `str(e)` 被 try-except 包装，捕获 `UnicodeEncodeError`/`UnicodeDecodeError`
   - 使用 `repr(e)` 作为 ASCII 安全的后备方案
   - 使用 `encode('utf-8', errors='replace').decode('utf-8')` 确保 JSON 安全

2. **请求参数安全提取** (`main.py:204-237`):
   - `_safe_extract_request_params` 方法实现正确
   - 对每个字符串值进行 UTF-8 安全编码
   - 异常时返回安全的后备值

3. **长度限制**:
   - 响应消息限制 500 字符 (`main.py:297`)
   - 日志消息限制 200 字符 (`main.py:289`)

4. **CORS 头保持动态** (`main.py:256-264, 301-304`):
   - 动态 origin 处理保持不变
   - `Access-Control-Allow-Credentials: "true"` 保持不变

### Refactoring Performed

无需重构 - 代码质量已符合标准。

### Requirements Traceability Matrix

| AC | 描述 | 测试覆盖 | 实现位置 | 状态 |
|----|------|----------|----------|------|
| AC1 | 任何异常消息都能安全编码到 JSON 响应 | `test_exception_with_unicode_message`, `test_exception_with_unencodable_chars`, `test_message_length_limited_to_500`, `test_json_response_always_valid` | `main.py:265-274, 297` | PASS |
| AC2 | 不会因为错误处理器中的编码问题导致级联失败 | `test_exception_with_unencodable_chars`, `TestStory12J5_SafeExtractRequestParams` | `main.py:204-237, 279, 288-291` | PASS |
| AC3 | 现有 CORS 功能保持不变 | `test_cors_headers_preserved_with_unicode_error`, `test_normal_request_not_affected` | `main.py:256-264, 301-304` | PASS |

### Compliance Check

- Coding Standards: [x] 符合 - 代码有 `[Source: ...]` 注释，引用 Story 和 ADR
- Project Structure: [x] 符合 - 修改在正确的文件位置
- Testing Strategy: [x] 符合 - 使用 pytest + TestClient，Given-When-Then 文档模式
- All ACs Met: [x] 符合 - 所有 3 个 AC 都有完整的测试覆盖

### Improvements Checklist

- [x] 代码实现符合所有 AC 要求
- [x] 测试覆盖完整 (7 个新测试)
- [x] 现有测试仍通过 (31 tests total)
- [x] 代码注释引用 Story 和 ADR
- [x] 无安全漏洞
- [x] 无性能问题

### Security Review

**Status: PASS**

- 防止级联失败：错误处理器本身不会因编码问题崩溃
- 信息泄露控制：消息被截断为 500 字符，避免过大的错误响应
- CORS 安全：动态 origin 验证保持不变，不使用 `*`

### Performance Considerations

**Status: PASS**

- 无阻塞操作
- 字符串 encode/decode 操作开销可忽略 (微秒级)
- 长度限制减少响应大小

### NFR Validation Summary

| NFR 类别 | 状态 | 说明 |
|----------|------|------|
| Security | PASS | 防止级联失败，不暴露敏感信息 |
| Performance | PASS | 无阻塞操作，开销可忽略 |
| Reliability | PASS | 多层后备机制，错误处理器本身不会失败 |
| Maintainability | PASS | 良好的注释和文档引用 |

### Files Modified During Review

无 - 代码质量已符合标准，无需修改。

### Gate Status

**Gate: PASS** -> `docs/qa/gates/12.J.5-cors-encoding-safety.yml`

**Quality Score: 100** (0 FAILs, 0 CONCERNS)

### Recommended Status

[x] Ready for Done

所有验收标准完全满足，测试覆盖完整，代码质量优秀。Story 可以标记为 Done。
