# Story 12.J.1: 完整日志 UTF-8 包装

**Epic**: 12.J - Windows 编码架构修复
**优先级**: P0 (BLOCKER)
**状态**: Complete ✅
**预估**: 15 分钟

---

## Story

**As a** Windows 环境下使用 Canvas Learning System 的开发者,
**I want** 所有日志输出（stdout 和 stderr）都使用 UTF-8 编码,
**so that** 中文和 emoji 字符能正确显示而不会导致 UnicodeEncodeError。

---

## Background

Epic 12.I 只修复了 stdout 的 UTF-8 包装，但 stderr 仍然使用 Windows 默认的 GBK 编码。
当 Uvicorn 错误日志或异常 traceback 包含中文/emoji 时，仍会触发 UnicodeEncodeError。

**当前代码位置**: `backend/app/core/logging.py:61-64`

```python
# 现状: stdout 已包装，stderr 未处理
utf8_stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
)
console_handler = logging.StreamHandler(utf8_stdout)
# stderr 未处理! ← 问题所在
```

**错误链路** (来自 Epic 12.J 诊断):
```
日志包含 emoji/中文 → logging.StreamHandler 写入 stderr
→ Windows GBK 编码无法处理 → UnicodeEncodeError
→ 异常被通用 Exception 捕获 → logger.error() 再次触发编码错误
→ 级联失败 → FastAPI 返回 HTTP 500
```

---

## Acceptance Criteria

1. **AC1**: stderr 输出在 Windows 不抛出 UnicodeEncodeError
2. **AC2**: Uvicorn 启动/关闭日志正确显示中文
3. **AC3**: 异常 traceback 包含中文时正确显示

---

## Tasks / Subtasks

- [x] **Task 1**: 添加 stderr UTF-8 包装 (AC1) ✅
  - [x] 1.1 在 `logging.py` 第 63 行后添加 `utf8_stderr` TextIOWrapper
  - [x] 1.2 创建 `error_handler` 使用 `utf8_stderr`
  - [x] 1.3 设置 `error_handler.setLevel(logging.ERROR)`
  - [x] 1.4 添加 `error_handler` 到 `root_logger`

- [x] **Task 2**: 重新配置 Uvicorn handlers (AC2) ✅
  - [x] 2.1 在 `setup_logging()` 末尾遍历 uvicorn logger handlers
  - [x] 2.2 将 StreamHandler 的 stream 替换为 `utf8_stdout`
  - [x] 2.3 覆盖 `uvicorn`, `uvicorn.error`, `uvicorn.access` 三个 logger

- [x] **Task 3**: 验证修复效果 (AC1, AC2, AC3) ✅
  - [x] 3.1 手动测试中文日志输出
  - [x] 3.2 手动测试 emoji 日志输出
  - [x] 3.3 验证 Uvicorn 启动日志显示正常

---

## Dev Notes

### SDD规范参考 (必填)

**API端点**: N/A - 此 Story 不涉及 API 变更

**数据Schema**: N/A - 此 Story 不涉及数据模型变更

**配置文件**:
- 修改文件: `backend/app/core/logging.py`
- 来源引用: `[Source: Epic 12.J - Story 12.J.1 关键文件]`

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| ADR-010 | 日志聚合方案 - structlog | 当前使用标准 logging，未来迁移到 structlog；本 Story 修复基础编码问题，与 ADR-010 迁移独立 |

**关键约束** (从 ADR-010 提取):
- 约束1: 日志文件必须使用 `encoding="utf-8"`
- 约束2: 控制台输出需要考虑 Windows 编码兼容性

**说明**: ADR-010 规划使用 structlog，但当前 `logging.py` 仍使用标准库。本 Story 修复现有配置的编码问题，不影响未来 structlog 迁移。

### 技术方案详情

**修改位置**: `backend/app/core/logging.py`

**变更 1**: 添加 stderr 包装 (第 63 行后)

```python
# 添加 stderr UTF-8 包装 [Source: Story 12.J.1]
utf8_stderr = io.TextIOWrapper(
    sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True
)

# 创建 stderr handler 用于 ERROR 级别日志
error_handler = logging.StreamHandler(utf8_stderr)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
root_logger.addHandler(error_handler)
```

**变更 2**: 重新配置 Uvicorn handlers (第 77 行后)

```python
# 重新配置 Uvicorn handlers 使用 UTF-8 stdout [Source: Story 12.J.1]
for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
    uv_logger = logging.getLogger(logger_name)
    for handler in uv_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            handler.stream = utf8_stdout
```

### Relevant Source Tree

```
backend/
└── app/
    └── core/
        └── logging.py       # 修改目标 (Line 58-77)
```

### Testing

**测试文件位置**: `backend/tests/unit/test_logging_encoding.py` (如需自动化)

**测试框架**: pytest

**手动测试步骤**:

```python
# 测试 1: 中文日志输出
import logging
logger = logging.getLogger("test")
logger.error("测试中文日志输出 🔥")  # 应正常输出，无 UnicodeEncodeError

# 测试 2: Uvicorn 启动验证
# 启动后端: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
# 观察启动日志是否正常显示中文

# 测试 3: 异常 traceback 验证
try:
    raise ValueError("错误信息包含中文 🚨")
except Exception:
    logger.exception("捕获异常")  # 应正常输出完整 traceback
```

**验收检查点**:
- [ ] Windows 控制台无 UnicodeEncodeError
- [ ] 中文字符正确显示（非乱码）
- [ ] Emoji 字符正确显示或被替换（不崩溃）

---

## Risk & Mitigation

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| TextIOWrapper 性能影响 | Low | Low | 使用 `line_buffering=True` 优化 |
| Uvicorn handler 覆盖时机 | Low | Medium | 在 `setup_logging()` 末尾重新配置 |
| 与 structlog 迁移冲突 | None | None | 本 Story 修复基础编码，与迁移独立 |

**回滚计划**:
- Git revert 单个 commit 即可回滚
- 无数据库变更，无破坏性影响

---

## Definition of Done

- [x] stderr 使用 UTF-8 TextIOWrapper 包装 ✅
- [x] error_handler 添加到 root_logger ✅
- [x] Uvicorn handlers 重新配置为 UTF-8 ✅
- [x] 手动测试通过 (3 个测试场景) ✅
- [ ] Code Review 通过

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-17 | 1.0 | 初始创建 | PO Agent |
| 2025-12-17 | 1.1 | 按模板补充必填 sections (Tasks, Dev Notes, ADR) | Sarah (PO) |
| 2025-12-17 | 1.2 | 状态更新: Draft → Ready (验证通过) | Sarah (PO) |
| 2025-12-17 | 1.3 | 实施完成: Ready → Complete (所有 Tasks 完成) | James (Dev) |

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References
N/A - No errors encountered

### Completion Notes
**Date**: 2025-12-17
**Duration**: ~10 minutes
**Implementation Summary**:
1. Added `utf8_stderr` TextIOWrapper at line 69-71
2. Created `error_handler` with ERROR level at lines 77-81
3. Added error_handler to root_logger at line 85
4. Reconfigured Uvicorn handlers for UTF-8 at lines 92-98
5. Verified all 3 test scenarios pass without UnicodeEncodeError

**Test Results**:
- Chinese characters display correctly in logs
- Emoji characters display correctly (or replaced gracefully)
- Exception tracebacks with Chinese text display correctly
- No UnicodeEncodeError raised on Windows

### File List
- `backend/app/core/logging.py` - Modified (added stderr UTF-8 wrapper, error_handler, Uvicorn reconfiguration)

---

## QA Results

### Review Date: 2025-12-17

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall: Excellent (95/100)**

The implementation is clean, well-documented, and follows the Story specification precisely. All three acceptance criteria are fully implemented with proper source traceability comments.

**Implementation Highlights**:
- `backend/app/core/logging.py:69-71`: stderr UTF-8 wrapper correctly configured with `errors='replace'` for graceful fallback
- `backend/app/core/logging.py:79-81`: error_handler properly set to ERROR level
- `backend/app/core/logging.py:94-98`: Uvicorn handlers correctly reconfigured to use UTF-8 stdout

### Refactoring Performed

None required. Implementation is clean and follows established patterns.

### Compliance Check

- Coding Standards: ✓ Source comments added per Zero-Hallucination rules
- Project Structure: ✓ Changes confined to `backend/app/core/logging.py`
- Testing Strategy: ✓ Integration tests exist in `test_encoding_safety.py`
- All ACs Met: ✓ AC1 (stderr wrapper), AC2 (Uvicorn handlers), AC3 (exception traceback)

### Requirements Traceability

| AC | Implementation | Test Coverage |
|----|----------------|---------------|
| AC1: stderr UTF-8 wrapper | `logging.py:69-71, 79-81, 85` | `test_encoding_safety.py:61-71` |
| AC2: Uvicorn handler reconfiguration | `logging.py:94-98` | `test_encoding_safety.py:61-71` |
| AC3: Exception traceback handling | `errors='replace'` at line 70 | `test_encoding_safety.py:73-84` |

### Improvements Checklist

- [x] stderr UTF-8 wrapper implemented
- [x] error_handler with ERROR level added
- [x] Uvicorn handlers reconfigured
- [x] Source traceability comments added
- [ ] (Optional) Add dedicated unit test file `backend/tests/unit/test_logging_encoding.py`

### Security Review

No security concerns. Changes are limited to encoding configuration for console output. No data exposure or injection risks.

### Performance Considerations

`TextIOWrapper` with `line_buffering=True` has minimal performance overhead. The `errors='replace'` strategy ensures no exceptions are raised, preventing cascading failures.

### ADR Compliance

**ADR-010** (Logging Aggregation - structlog):
- ✅ Story correctly states independence from structlog migration
- ✅ Constraints verified: `encoding='utf-8'` and Windows compatibility addressed
- ✅ Current standard logging configuration fixed, future migration unaffected

### Files Modified During Review

None. No refactoring required.

### Gate Status

**Gate: PASS** → `docs/qa/gates/12.J.1-logging-utf8-complete.yml`

Risk profile: Low (no security/auth files, <100 LOC change, 3 ACs)
Quality Score: 95/100

### Recommended Status

✓ **Ready for Done** - All acceptance criteria met, tests passing, ADR compliant.
