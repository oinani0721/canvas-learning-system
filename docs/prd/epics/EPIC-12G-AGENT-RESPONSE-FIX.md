# Epic 12.G: Agent 响应提取修复 - 棕地增强

**创建日期**: 2025-12-16
**状态**: Draft
**优先级**: P0 (Critical)

---

## Epic 目标

修复所有 Agent 返回 **"无法从AI响应中提取有效内容"** 的错误，确保 Agent 调用链路端到端可用。

---

## Epic 描述

### 现有系统上下文

- **当前功能**: 14个学习Agent通过 Obsidian 右键菜单调用后端 API
- **技术栈**: FastAPI + GeminiClient + AgentService
- **集成点**:
  - 前端: `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`
  - 后端: `backend/app/services/agent_service.py`
  - AI Client: `backend/app/clients/gemini_client.py`

### 问题分析

**调用链路**:
```
前端右键菜单 → ApiClient.callAgent() → POST /api/v1/agents/explain
    → AgentService.generate_explanation()
    → AgentService.call_explanation()
    → AgentService.call_agent()
    → AgentService._call_gemini_api()
    → GeminiClient.call_agent()
    → Gemini API 实际调用
    ↓
返回 result.data (Dict)
    ↓
extract_explanation_text(result.data)
    ↓
如果提取失败 → "无法从AI响应中提取有效内容"
```

**可能的失败点**:

| # | 失败点 | 描述 | 影响 |
|---|--------|------|------|
| 1 | API 配置问题 | API Key 未配置或无效 | 所有 Agent 失败 |
| 2 | 响应格式问题 | AI 返回的格式与提取器不匹配 | 部分 Agent 失败 |
| 3 | 异常处理问题 | 异常时 `result.data` 为 None | 所有 Agent 失败 |
| 4 | 日志不足 | 无法定位具体失败原因 | 调试困难 |

### 关键代码位置

| 文件 | 行号 | 函数 | 作用 |
|------|------|------|------|
| `agent_service.py` | 100-163 | `extract_explanation_text()` | 从响应中提取文本 |
| `agent_service.py` | 166-230 | `create_error_response()` | 创建错误响应节点 |
| `agent_service.py` | 877-1027 | `_call_gemini_api()` | 调用 Gemini API |
| `agent_service.py` | 1203-1261 | `call_agent()` | Agent 调用入口 |
| `agent_service.py` | 1444-1533 | `call_explanation()` | 解释类 Agent 调用 |
| `agent_service.py` | 1960-1998 | `generate_explanation()` | 生成解释并写入 Canvas |
| `gemini_client.py` | 310-414 | `call_agent()` | 实际 API 调用 |

### 成功标准

- [ ] Agent 调用成功率 ≥ 95%
- [ ] 所有 12 个学习 Agent 可正常使用
- [ ] 错误信息清晰、可操作
- [ ] 添加详细日志便于调试

---

## Stories

### Story 12.G.1: 添加 API 响应详细日志 [P0 紧急]

**优先级**: P0 (阻塞问题定位)

**问题**: 当前日志不足以定位 "无法从AI响应中提取有效内容" 的具体原因。

**验收标准**:
1. 在 `_call_gemini_api` 返回前添加响应内容日志（前500字符）
2. 在 `extract_explanation_text` 添加每个提取器的尝试结果日志
3. 记录 `result.data` 的实际类型和内容预览
4. 日志级别可通过环境变量 `DEBUG_AGENT_RESPONSE=true` 配置
5. 默认关闭详细日志以避免性能影响

**技术任务**:
- [ ] 在 `_call_gemini_api` 第 1017 行后添加响应日志
- [ ] 在 `extract_explanation_text` 每个提取器后添加调试日志
- [ ] 添加 `DEBUG_AGENT_RESPONSE` 环境变量支持
- [ ] 更新 `.env.example` 文档

**关键文件**:
- `backend/app/services/agent_service.py:877-1027` (_call_gemini_api)
- `backend/app/services/agent_service.py:100-163` (extract_explanation_text)

**预计工作量**: 2小时

---

### Story 12.G.2: 增强错误处理与友好提示 [P0]

**优先级**: P0

**问题**: 所有错误都显示同一个通用消息，用户无法知道具体问题。

**验收标准**:
1. 区分不同错误类型并返回具体错误原因:

| 错误类型 | 错误消息 |
|----------|----------|
| API Key 未配置 | "请在插件设置中配置 API Key" |
| API 调用超时 | "AI 响应超时，请重试" |
| 响应格式错误 | "AI 响应格式异常: {具体信息}" |
| 网络错误 | "网络连接失败，请检查网络" |
| 模板缺失 | "Agent 模板文件缺失: {agent_type}" |

2. 错误响应包含调试信息 (在 debug 模式下)
3. 前端显示友好的中文错误提示
4. 错误节点颜色改为红色 (color="1")

**技术任务**:
- [ ] 修改 `create_error_response` 支持错误类型分类
- [ ] 在 `call_agent` 异常处理中区分错误类型
- [ ] 更新前端 `ApiClient.ts` 错误处理
- [ ] 添加错误类型枚举 `AgentErrorType`

**关键文件**:
- `backend/app/services/agent_service.py:166-230` (create_error_response)
- `backend/app/services/agent_service.py:1247-1259` (call_agent 异常处理)
- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`

**预计工作量**: 3小时

---

### Story 12.G.3: API 健康检查端点 [P1]

**优先级**: P1

**问题**: 用户无法快速诊断 Agent 系统是否正常工作。

**验收标准**:
1. 添加 `GET /api/v1/agents/health` 端点
2. 检查项:
   - API Key 是否配置 (不返回实际 key)
   - GeminiClient 是否初始化
   - Agent prompt 模板是否存在 (列出缺失的)
   - 简单 API 调用测试 (可选，通过参数控制)
3. 返回详细的健康状态 JSON:
```json
{
  "status": "healthy|degraded|unhealthy",
  "checks": {
    "api_key_configured": true,
    "gemini_client_initialized": true,
    "prompt_templates": {
      "total": 12,
      "available": 12,
      "missing": []
    },
    "api_test": {
      "enabled": false,
      "result": null
    }
  },
  "timestamp": "2025-12-16T10:30:00Z"
}
```
4. 前端插件启动时自动检查并提示

**技术任务**:
- [ ] 创建 `GET /api/v1/agents/health` 端点
- [ ] 实现 `AgentService.health_check()` 方法
- [ ] 前端添加启动时健康检查
- [ ] 添加健康检查结果缓存 (60秒)

**关键文件**:
- `backend/app/api/v1/endpoints/agents.py`
- `backend/app/services/agent_service.py`
- `canvas-progress-tracker/obsidian-plugin/main.ts`

**预计工作量**: 3小时

---

### Story 12.G.4: 响应格式自适应 [P1]

**优先级**: P1

**问题**: `extract_explanation_text` 可能无法处理某些 AI 响应格式。

**验收标准**:
1. `extract_explanation_text` 支持更多响应格式:

| 格式 | 示例 | 提取路径 |
|------|------|----------|
| Gemini 原生 | `{"response": "..."}` | `response` |
| OpenAI 兼容 | `{"choices": [{"message": {"content": "..."}}]}` | `choices[0].message.content` |
| 纯文本 | `"直接文本"` | 直接返回 |
| Markdown JSON | ````json\n{...}\n```` | 解析代码块 |
| 嵌套 response | `{"response": {"text": "..."}}` | `response.text` |

2. 添加单元测试覆盖所有格式 (≥10个测试用例)
3. 日志记录实际使用的提取器名称
4. 提取失败时记录原始响应内容 (截断)

**技术任务**:
- [ ] 添加 OpenAI 兼容格式提取器
- [ ] 添加嵌套 response 提取器
- [ ] 改进 Markdown 代码块解析
- [ ] 编写单元测试
- [ ] 添加提取成功日志

**关键文件**:
- `backend/app/services/agent_service.py:100-163`
- `backend/tests/services/test_agent_service.py`

**预计工作量**: 2小时

---

### Story 12.G.5: 前端错误展示优化 [P2]

**优先级**: P2

**问题**: 错误节点信息不足，用户无法追溯和重试。

**验收标准**:
1. 错误节点显示具体错误原因（不只是通用错误）
2. 错误节点格式:
```
⚠️ Agent 调用失败

错误类型: API 配置问题
错误信息: 请在插件设置中配置 API Key

时间: 2025-12-16 10:30:00
请求ID: req_abc123

[点击重试] [复制错误信息]
```
3. 支持点击重试 (重新发送相同请求)
4. 支持复制错误信息用于反馈
5. 错误节点宽度增加到 400px 以显示完整信息

**技术任务**:
- [ ] 修改 `create_error_response` 返回更多信息
- [ ] 前端解析错误响应并格式化显示
- [ ] 添加重试按钮功能
- [ ] 添加复制功能

**关键文件**:
- `backend/app/services/agent_service.py:166-230`
- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`
- `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts`

**预计工作量**: 4小时

---

## 兼容性要求

- [x] 现有 API 接口保持不变
- [x] 现有 Agent prompt 模板无需修改
- [x] 插件向后兼容
- [x] 不影响已有的 Canvas 文件
- [x] 错误响应格式向后兼容

## 风险缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 日志过多影响性能 | 中 | 详细日志默认关闭，通过环境变量开启 |
| 健康检查端点暴露敏感信息 | 低 | 不返回 API Key，只返回配置状态 |
| 新提取器引入 bug | 中 | 完整单元测试覆盖 |

**回滚计划**:
- 所有更改通过环境变量控制
- 可随时禁用新增日志和健康检查
- Git revert 可快速回滚

---

## Definition of Done

- [ ] Story 12.G.1 完成 → 可定位具体失败原因
- [ ] Story 12.G.2 完成 → 用户看到友好错误提示
- [ ] Story 12.G.3 完成 → 可快速诊断配置问题
- [ ] Story 12.G.4 完成 → 支持多种 AI 响应格式
- [ ] Story 12.G.5 完成 → 错误可追溯和重试
- [ ] 所有 12 个学习 Agent 右键菜单功能验证通过
- [ ] Bug log 中 "无法从AI响应中提取有效内容" 错误归零
- [ ] 单元测试覆盖率 ≥ 80%

---

## Story Manager 交接

**请为此棕地 Epic 开发详细用户故事。关键考虑：**

- 这是对运行中系统的增强，技术栈为 FastAPI + TypeScript
- 集成点: `AgentService` ↔ `GeminiClient` ↔ `ApiClient`
- 需遵循的现有模式:
  - 错误响应使用 `create_error_response()`
  - 日志使用 `logger.info/warning/error`
  - 环境变量配置通过 `settings`
- 关键兼容性要求: API 接口不变、插件向后兼容
- 每个 Story 必须包含验证现有功能完整性的测试

**Epic 目标**: 修复 Agent 响应提取问题，让所有 12 个学习 Agent 恢复正常工作。

---

## 附录: 现有提取器代码分析

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
    # ... 逐个尝试提取
```

**问题**: 缺少对 OpenAI 兼容格式和嵌套响应的支持。

---

## 变更日志

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2025-12-16 | 1.0 | 初始创建 |
