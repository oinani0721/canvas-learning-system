# Epic 12.J: Windows 编码架构修复 - Brownfield 增强

**创建日期**: 2025-12-17
**状态**: Ready for Implementation
**优先级**: P0 (Critical)
**类型**: Bug Fix (Brownfield Enhancement)
**前置**: Epic 12.I (部分修复)

---

## Epic 目标

解决 **Windows 环境下 Agent 端点返回 HTTP 500 错误** 的根本问题。Epic 12.I 只修复了部分编码问题（stdout UTF-8 包装），本 Epic 完成剩余的编码架构修复。

---

## Epic 描述

### 现有系统上下文

- **当前功能**: 14 个学习 Agent 通过 Obsidian 右键菜单调用后端 API
- **技术栈**:
  - 前端: TypeScript + Obsidian Plugin API
  - 后端: FastAPI + Python logging + GeminiClient
- **集成点**:
  - 日志配置: `backend/app/core/logging.py`
  - HTTP 请求: `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`
  - Agent 端点: `backend/app/api/v1/endpoints/agents.py`
  - 异常处理: `backend/app/main.py`

### 问题根源诊断 (深度调研结果)

| # | 根本原因 | 概率 | 位置 | Epic 12.I 状态 |
|---|---------|------|------|---------------|
| **1** | stderr 未包装 UTF-8 | 99% | `logging.py` | 未修复 |
| **2** | Content-Type 缺少 charset=utf-8 | 95% | `ApiClient.ts:179` | 未修复 |
| **3** | 缺少 UnicodeEncodeError 显式捕获 | 99% | `agents.py` | 未修复 |
| **4** | CORSExceptionMiddleware 编码不安全 | 90% | `main.py` | 未修复 |

### 错误链路分析

```
完整错误链路:
1. Obsidian 发送请求 (Content-Type: application/json, 无 charset)
   ↓
2. FastAPI 接收请求，Pydantic 验证 (接受 mojibake 字符串)
   ↓
3. Agent 处理请求，调用 GeminiClient
   ↓
4. 响应或日志包含 emoji/中文字符
   ↓
5. logging.StreamHandler 写入 stderr (未包装 UTF-8)
   ↓
6. Windows GBK 编码无法处理 → UnicodeEncodeError
   ↓
7. 异常被通用 Exception 捕获，logger.error() 再次触发编码错误
   ↓
8. 级联失败 → FastAPI 返回 HTTP 500
```

### 成功标准

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| Agent 端点响应 (中文内容) | HTTP 500 | HTTP 200 |
| stderr 编码错误 | UnicodeEncodeError | 无错误 |
| 无效 UTF-8 请求 | HTTP 500 | HTTP 400 |
| 中文日志显示 | 乱码/崩溃 | 正常显示 |

---

## Stories

### Story 12.J.1: 完整日志 UTF-8 包装 [P0 BLOCKER]

**优先级**: P0 (阻塞所有其他修复)
**预估**: 15 分钟
**风险**: Low

**Scope**:
1. 包装 `sys.stderr` 使用 UTF-8 编码
2. 重新配置 Uvicorn logger handlers 使用 UTF-8 stdout
3. 添加 error-level handler 专门处理 stderr

**关键文件**:
- `backend/app/core/logging.py:58-77`

**验收标准**:
- AC1: stderr 输出在 Windows 不抛出 UnicodeEncodeError
- AC2: Uvicorn 启动/关闭日志正确显示中文
- AC3: 异常 traceback 包含中文时正确显示

---

### Story 12.J.2: 前端请求 Charset 强制 [P1]

**优先级**: P1
**预估**: 10 分钟
**风险**: Very Low

**Scope**:
1. 在 Content-Type header 中添加 `charset=utf-8`
2. 确保 JSON.stringify 输出为 UTF-8

**关键文件**:
- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts:178-180`

**验收标准**:
- AC1: 所有请求包含 `Content-Type: application/json; charset=utf-8`
- AC2: 中文 canvas 名称正确传输到后端

---

### Story 12.J.3: 后端请求编码验证中间件 [P1]

**优先级**: P1
**预估**: 30 分钟
**风险**: Low

**Scope**:
1. 创建 EncodingValidationMiddleware
2. 验证 POST/PUT/PATCH 请求体的 UTF-8 编码
3. 对无效编码返回 400 Bad Request

**关键文件**:
- `backend/app/main.py` (新增中间件)

**验收标准**:
- AC1: 无效 UTF-8 请求返回 HTTP 400，不是 500
- AC2: 有效 UTF-8 请求正常处理 (无性能影响)
- AC3: 错误响应包含 ENCODING_ERROR 类型

---

### Story 12.J.4: UnicodeEncodeError 显式异常处理 [P0]

**优先级**: P0
**预估**: 30 分钟
**风险**: Medium

**Scope**:
1. 在所有 13 个 Agent 端点添加 `except UnicodeEncodeError`
2. 安全化错误日志 (避免递归编码错误)
3. 返回结构化 ENCODING_ERROR 响应

**关键文件**:
- `backend/app/api/v1/endpoints/agents.py` (13 个端点)

**验收标准**:
- AC1: UnicodeEncodeError 返回结构化错误响应
- AC2: 错误日志不触发二次编码错误
- AC3: 所有 13 个 Agent 端点都有显式处理
- AC4: 编码错误包含安全诊断信息 (hex position)

---

### Story 12.J.5: CORSExceptionMiddleware 编码安全 [P1]

**优先级**: P1
**预估**: 15 分钟
**风险**: Low

**Scope**:
1. 安全化 `str(e)` 调用 (捕获 UnicodeEncodeError)
2. 使用 `encode('utf-8', errors='replace').decode('utf-8')` 处理消息
3. 确保 JSON 响应可安全编码

**关键文件**:
- `backend/app/main.py` (CORSExceptionMiddleware)

**验收标准**:
- AC1: 任何异常消息都能安全编码到 JSON 响应
- AC2: 不会因为错误处理器中的编码问题导致级联失败
- AC3: 现有 CORS 功能保持不变

---

### Story 12.J.6: 编码安全集成测试套件 [P2]

**优先级**: P2
**预估**: 45 分钟
**风险**: None

**Scope**:
1. 创建专门的编码测试套件
2. 覆盖所有编码边界情况
3. 验证向后兼容性

**关键文件**:
- `backend/tests/integration/test_encoding_safety.py` (新建)

**测试用例**:
- `test_emoji_in_canvas_name`: emoji 不导致 500
- `test_chinese_content_roundtrip`: 中文内容正确往返
- `test_malformed_utf8_returns_400`: 无效 UTF-8 返回 400
- `test_logging_with_unicode_no_crash`: 日志中文不崩溃
- `test_exception_with_unicode_message`: Unicode 异常安全处理

**验收标准**:
- AC1: 测试套件在 Windows GBK 控制台通过
- AC2: 测试套件在 Linux/Mac 通过 (无回归)
- AC3: 所有编码边界情况覆盖

---

## 兼容性要求

- [x] 现有 API 接口保持不变
- [x] 现有 Agent 调用流程向后兼容
- [x] 日志格式保持一致
- [x] 不影响已有的 Canvas 文件
- [x] 前端插件向后兼容 (charset=utf-8 是增强，不是破坏性变更)

---

## 实施顺序

```
Story 12.J.1 (P0) ─────┐
                       ├──> Story 12.J.4 (P0) ──> Story 12.J.6 (P2)
Story 12.J.5 (P1) ─────┤
                       │
Story 12.J.2 (P1) ─────┤
                       │
Story 12.J.3 (P1) ─────┘
```

**理由**:
- 12.J.1 必须首先完成 (日志影响所有调试)
- 12.J.4 和 12.J.5 可并行 (不同文件)
- 12.J.2 和 12.J.3 是前后端配对，可并行
- 12.J.6 最后执行以验证所有修复

---

## 风险缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------||TextIOWrapper 性能影响 | 低 | 使用 line_buffering=True 优化 |
| 中间件增加请求延迟 | 低 | 仅验证 POST/PUT/PATCH，GET 请求跳过 |
| Agent 端点修改范围大 | 中 | 使用统一的 except 块模式 |

**回滚计划**:
- 所有更改可通过 Git revert 快速回滚
- 每个 Story 的修改相互独立
- 无数据库迁移或 schema 变更

---

## Definition of Done

- [ ] Story 12.J.1 完成 → stderr UTF-8 包装
- [ ] Story 12.J.2 完成 → Content-Type charset
- [ ] Story 12.J.3 完成 → 编码验证中间件
- [ ] Story 12.J.4 完成 → UnicodeEncodeError 显式捕获
- [ ] Story 12.J.5 完成 → 异常处理器编码安全
- [ ] Story 12.J.6 完成 → 集成测试
- [ ] 所有 Agent 端点在 Windows 返回 200
- [ ] 手动验证 Obsidian 中文 Canvas

---

## 变更日志

| 日期 | 版本 | 变更内容 |
|------|------|---------||2025-12-17 | 1.0 | 初始创建 (基于深度调研) |
