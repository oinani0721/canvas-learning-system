# Story 12.J.2: 前端请求 Charset 强制

**Epic**: 12.J - Windows 编码架构修复
**优先级**: P1
**状态**: Done
**预估**: 10 分钟

---

## 用户故事

作为一个 Obsidian 插件用户，
我希望前端发送的 HTTP 请求明确指定 UTF-8 编码，
以便后端能正确解析包含中文的 canvas 名称和节点内容。

---

## 背景

当前 ApiClient.ts 发送请求时，Content-Type header 只有 `application/json`，
没有明确指定 `charset=utf-8`。虽然 JSON.stringify 默认输出 UTF-8，
但明确指定 charset 是防御性编程的最佳实践。

**需修改位置**（共 2 处）:

| # | 方法 | 行号 | 用途 |
|---|------|------|------|
| 1 | `request()` | Line 178-181 | 核心请求方法，所有 API 调用经过此处 |
| 2 | `callAgentWithCancel()` | Line 726-731 | Story 12.H.4 引入的可取消请求方法 |

**当前代码** (`ApiClient.ts:178-181`):
```typescript
headers: {
  'Content-Type': 'application/json',  // 缺少 charset
  'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
  ...options?.headers,
},
```

**当前代码** (`ApiClient.ts:728-731`):
```typescript
headers: {
  'Content-Type': 'application/json',  // 缺少 charset
  'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
},
```

---

## 验收标准

- **AC1**: 所有请求包含 `Content-Type: application/json; charset=utf-8`
  - 包括 `request()` 方法发出的请求
  - 包括 `callAgentWithCancel()` 方法发出的请求
- **AC2**: 中文 canvas 名称正确传输到后端
  - 后端日志显示正确中文（非 mojibake 乱码）
  - 后端响应包含原始中文内容
  - 无 `UnicodeDecodeError` 在后端日志

---

## Tasks / Subtasks

- [x] Task 1: 修改 `request()` 方法 Content-Type (AC: 1)
  - [x] 1.1: 修改 Line 179 从 `'application/json'` 改为 `'application/json; charset=utf-8'`
- [x] Task 2: 修改 `callAgentWithCancel()` 方法 Content-Type (AC: 1)
  - [x] 2.1: 修改 Line 729 从 `'application/json'` 改为 `'application/json; charset=utf-8'`
- [x] Task 3: 构建并验证 (AC: 1, 2)
  - [x] 3.1: 执行 `npm run build` 确保编译成功
  - [x] 3.2: 部署到 Obsidian 插件目录
  - [ ] 3.3: 打开 Developer Console → Network Tab 验证请求头 (手动测试)
  - [ ] 3.4: 测试中文 canvas 名称的 Agent 调用，验证后端日志 (手动测试)

---

## 技术方案

### 修改文件

`canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`

### 代码变更 #1: request() 方法

```typescript
// Line 178-181 修改
headers: {
  'Content-Type': 'application/json; charset=utf-8',  // 添加 charset
  'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
  ...options?.headers,
},
```

### 代码变更 #2: callAgentWithCancel() 方法

```typescript
// Line 728-731 修改
headers: {
  'Content-Type': 'application/json; charset=utf-8',  // 添加 charset
  'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
},
```

---

## Dev Notes

### SDD规范参考 (必填)

本 Story 不涉及 API Schema 变更，属于前端 HTTP 请求头优化。

**相关标准**:
- **RFC 7231 Section 3.1.1.5**: Media Type (charset parameter)
  - `charset` 是 `media-type` 的可选参数
  - 格式: `type/subtype; parameter=value`
- **RFC 8259 (JSON)**: JSON 文本应使用 UTF-8 编码
  - Section 8.1: "JSON text exchanged between systems that are not part of a closed ecosystem MUST be encoded using UTF-8"
- **MDN Web Docs**: `Content-Type` header
  - [Source: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type]

**API 端点覆盖**:
- 所有 22 个 API 端点 (19 原始 + 3 RAG) 的请求都将携带 charset
- [Source: ApiClient.ts 注释 L1-17]

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| N/A | 无相关 ADR | 此为防御性编程增强，无架构约束 |

**说明**: 添加 `charset=utf-8` 参数是向后兼容的增强：
- 符合 HTTP/1.1 规范
- 不改变请求语义
- 后端 FastAPI 默认支持

**建议**: 无需创建新 ADR，此变更属于编码最佳实践。

### Testing Standards

- **测试类型**: 手动测试 (非自动化)
- **测试环境**: Obsidian Desktop + Developer Console
- **验证方式**:
  1. Network Tab → 检查 Request Headers
  2. 后端 Uvicorn 日志 → 检查中文显示
- **回归测试**: 确保现有功能不受影响

### Relevant Source Tree

```
canvas-progress-tracker/obsidian-plugin/
├── src/
│   └── api/
│       └── ApiClient.ts     # 修改目标文件 (1041行)
├── package.json
└── tsconfig.json
```

### 关联 Stories

- **Story 12.H.4**: 引入了 `callAgentWithCancel()` 方法，本 Story 需同步修改
- **Story 12.J.1**: 后端日志 UTF-8 包装（前置依赖，确保验证日志可读）

---

## 测试计划

1. 构建插件: `npm run build`
2. 部署到 Obsidian 插件目录:
   ```powershell
   Copy-Item main.js "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\" -Force
   ```
3. 重启 Obsidian 加载新插件
4. 打开 Developer Console (Ctrl+Shift+I)，切换到 Network Tab
5. 触发任意 Agent 调用（右键 Canvas 节点 → 选择 Agent）
6. 验证请求头:
   - `Content-Type: application/json; charset=utf-8` ✓
7. 验证后端日志:
   - 中文内容正确显示 ✓
   - 无 `UnicodeDecodeError` ✓

---

## 兼容性

- **向后兼容**: `charset=utf-8` 是增强，不会破坏现有功能
- **RFC 7231**: 明确允许在 application/json 中指定 charset
- **FastAPI**: 默认接受带 charset 的 Content-Type

---

## Definition of Done

- [x] `request()` 方法 Content-Type 包含 `charset=utf-8`
- [x] `callAgentWithCancel()` 方法 Content-Type 包含 `charset=utf-8`
- [x] 插件构建成功 (`npm run build` 无错误)
- [ ] Network Console 验证请求头正确 (手动测试)
- [ ] 中文 canvas 名称测试通过 (手动测试)

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-17 | 1.0 | Initial draft | SM |
| 2025-12-17 | 1.1 | 添加第二处修改位置 (callAgentWithCancel)，补充 Dev Notes | PO Validation |
| 2025-12-17 | 1.2 | 实现完成：修改两处 Content-Type，构建部署成功 | Dev (James) |

---

## QA Results

### Review Date: 2025-12-17

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Implementation is CORRECT and follows best practices.**

Both target locations have been properly updated with `charset=utf-8`:

| Location | Line | Status | Verification |
|----------|------|--------|--------------|
| `request()` | L180 | ✅ | `'Content-Type': 'application/json; charset=utf-8'` |
| `callAgentWithCancel()` | L731 | ✅ | `'Content-Type': 'application/json; charset=utf-8'` |

**Positive Observations:**
- Clear source comments referencing Story 12.J.2 at both locations
- RFC 7231 compliance for media type charset parameter
- Defensive programming approach - explicit > implicit

### Refactoring Performed

None required. Implementation is clean and well-documented.

### Compliance Check

- Coding Standards: ✓ Source comments present, follows TypeScript conventions
- Project Structure: ✓ Changes confined to `ApiClient.ts`
- Testing Strategy: ✓ Unit tests updated (L137, L903 fixed by QA)
- All ACs Met: ✓ Code changes satisfy AC1; AC2 requires manual verification

### Improvements Checklist

- [x] `request()` method Content-Type updated (L180)
- [x] `callAgentWithCancel()` method Content-Type updated (L731)
- [x] Source comments added referencing Story 12.J.2
- [x] Update `ApiClient.test.ts` to expect `charset=utf-8` (Fixed by QA)
  - L137: `'Content-Type': 'application/json; charset=utf-8'` ✓
  - L903: `'Content-Type': 'application/json; charset=utf-8'` ✓
- [ ] Manual verification: Network Console → Request Headers check
- [ ] Manual verification: Chinese canvas name test with backend log inspection

### Security Review

**PASS** - No security concerns. Adding charset is a defensive enhancement.

### Performance Considerations

**PASS** - Negligible overhead. Header value increased by ~14 bytes per request.

### Files Modified During Review

- **File**: `canvas-progress-tracker/obsidian-plugin/tests/api/ApiClient.test.ts`
  - **Change**: Updated L137 and L903 Content-Type expectations
  - **Why**: Tests expected old header value without charset
  - **How**: Changed `'application/json'` → `'application/json; charset=utf-8'`

### Test Gap Analysis

**RESOLVED** - Tests updated by QA during review.

| Test File | Line | Status | Value |
|-----------|------|--------|-------|
| `ApiClient.test.ts` | L137 | ✓ Fixed | `'Content-Type': 'application/json; charset=utf-8'` |
| `ApiClient.test.ts` | L903 | ✓ Fixed | `'Content-Type': 'application/json; charset=utf-8'` |

### Acceptance Criteria Traceability

| AC | Description | Validated | Evidence |
|----|-------------|-----------|----------|
| AC1 | All requests include `charset=utf-8` | ✅ Code | L180, L731 in ApiClient.ts |
| AC2 | Chinese canvas name transmission | ⏳ Manual | Requires manual Obsidian testing |

### Gate Status

Gate: **PASS** → `docs/qa/gates/12.J.2-frontend-charset.yml`

### Recommended Status

**✓ Ready for Done**

- Implementation verified correct
- Unit tests updated during review
- Only manual verification (AC2) remains

**Story owner: Please update File List to include test file modification, then mark Done.**
