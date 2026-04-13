# Story 3.2: MCP 工具暴露——后端算法接口

Status: ready-for-dev

## Story

As a AI Agent,
I want 通过 MCP 协议调用后端算法工具（query_mastery/generate_question/score_answer/search_memories/update_fsrs 等）,
so that 对话能利用后端的精通度追踪、出题、评分等算法能力。

## Acceptance Criteria

1. **AC-1: FastAPI-MCP ASGI 直连暴露**
   - **Given** FastAPI 后端运行中
   - **When** MCP 客户端连接 `http://localhost:8001/mcp`
   - **Then** 通过 FastAPI-MCP 库以 ASGI 直连方式暴露 MCP 端点（无额外 HTTP 开销）
   - **And** MCP Server 支持 JSON-RPC 2.0 协议

2. **AC-2: 10+ 标准化 MCP 工具可用**
   - **Given** MCP 连接建立
   - **When** Agent 发送 `tools/list` 请求
   - **Then** 返回 10+ 个标准化工具定义（含 JSON Schema 参数描述）
   - **And** 工具列表包含：`query_mastery`, `generate_question`, `score_answer`, `search_memories`, `update_fsrs`, `update_bkt`, `record_calibration`, `assemble_acp`, `archive_conversation`, `create_exam_node` 等
   - **And** 每个工具有清晰的中英文描述，Agent 能理解何时使用

3. **AC-3: 密码学令牌管道**
   - **Given** Agent 调用 `generate_question` 工具
   - **When** 工具执行成功
   - **Then** 返回结果中包含 `pipeline_token`
   - **And** 后续调用 `score_answer` 必须传入该 `pipeline_token`
   - **And** 跳步调用（如直接调 `update_fsrs` 不经过 `score_answer`）被拒绝（返回错误码 `PIPELINE_TOKEN_INVALID`）
   - **And** 令牌包含 HMAC 签名防止伪造

4. **AC-4: 后端审计守护层**
   - **Given** Agent 通过 MCP 执行工具调用链
   - **When** 工具调用完成
   - **Then** 后端异步审计守护层检测管道违规（信号丢失/跳步/算法未更新）
   - **And** 违规记录写入审计日志（`backend/logs/audit.jsonl`）
   - **And** 审计不阻塞正常工具调用（异步执行）

5. **AC-5: MCP 配置动态注入**
   - **Given** Story 3.1 的 ClaudeCodeEngine spawn 子进程
   - **When** 需要连接后端 MCP
   - **Then** 动态生成 `canvas-mcp.json` 配置文件
   - **And** 通过 `--mcp-config` 注入到 Claude Code 进程
   - **And** 配置中的后端地址可通过插件设置调整

## Tasks / Subtasks

- [ ] **Task 1: FastAPI-MCP Server 搭建** (AC: #1)
  - [ ] 1.1 在 `backend/requirements.txt` 添加 `fastapi-mcp` 依赖
  - [ ] 1.2 创建 `backend/app/mcp/server.py`：使用 FastAPI-MCP 的 `MCPServer` 类挂载到 FastAPI app
  - [ ] 1.3 在 `backend/app/main.py` 中注册 MCP ASGI 中间件路由（`/mcp` 路径）
  - [ ] 1.4 验证 MCP 端点可通过 `http://localhost:8001/mcp` 访问

- [ ] **Task 2: MCP 工具定义与注册** (AC: #2)
  - [ ] 2.1 创建 `backend/app/mcp/tools/` 目录
  - [ ] 2.2 创建 `backend/app/mcp/tools/mastery_tools.py`：`query_mastery`, `update_fsrs`, `update_bkt` 工具
  - [ ] 2.3 创建 `backend/app/mcp/tools/exam_tools.py`：`generate_question`, `score_answer`, `assemble_acp` 工具
  - [ ] 2.4 创建 `backend/app/mcp/tools/memory_tools.py`：`search_memories`, `record_calibration` 工具
  - [ ] 2.5 创建 `backend/app/mcp/tools/conversation_tools.py`：`archive_conversation`, `create_exam_node` 工具
  - [ ] 2.6 每个工具使用 Pydantic Model 定义输入/输出 schema
  - [ ] 2.7 在 `server.py` 中注册所有工具

- [ ] **Task 3: 密码学令牌管道实现** (AC: #3)
  - [ ] 3.1 创建 `backend/app/mcp/pipeline_token.py`
  - [ ] 3.2 实现 `PipelineTokenManager`：生成/验证 HMAC-SHA256 签名令牌
  - [ ] 3.3 令牌 payload 包含：`step_name`, `session_id`, `node_id`, `timestamp`, `expires_at`
  - [ ] 3.4 定义管道步骤顺序：`generate_question → score_answer → update_fsrs/update_bkt`
  - [ ] 3.5 在每个工具的前置检查中验证令牌有效性
  - [ ] 3.6 跳步/过期/签名不匹配 → 返回 `PIPELINE_TOKEN_INVALID` 错误

- [ ] **Task 4: 审计守护层** (AC: #4)
  - [ ] 4.1 创建 `backend/app/audit/guardian.py`
  - [ ] 4.2 实现 `AuditGuardian` 类：异步检测管道违规
  - [ ] 4.3 检测规则：信号丢失（评分后无 BKT 更新）、跳步（未评分直接更新）、时间异常（步骤间隔 > 5min）
  - [ ] 4.4 违规记录写入 `backend/logs/audit.jsonl`（JSON Lines 格式）
  - [ ] 4.5 使用 `asyncio.create_task` 异步执行审计（不阻塞工具调用）

- [ ] **Task 5: 前端 MCP 配置生成** (AC: #5)
  - [ ] 5.1 创建 `obsidian-canvas-learning/src/services/mcp-config.ts`
  - [ ] 5.2 实现 `generateMcpConfig(backendUrl: string): string`：生成 `canvas-mcp.json` 内容
  - [ ] 5.3 配置格式遵循 Claude Code `--mcp-config` 规范
  - [ ] 5.4 配置文件写入插件 data 目录（Obsidian vault `.obsidian/plugins/canvas-learning-system/`）
  - [ ] 5.5 后端地址从插件设置中读取（默认 `http://localhost:8001`）

## Dev Notes

### FastAPI-MCP 集成模式

```python
# backend/app/mcp/server.py
from fastapi_mcp import MCPServer
from app.main import app

mcp_server = MCPServer(app, name="canvas-learning-mcp")

@mcp_server.tool()
async def query_mastery(node_id: str) -> dict:
    """查询指定节点的精通度状态（BKT + FSRS）"""
    # 调用 mastery_engine 服务
    ...
```

### MCP 工具清单（10+ 个）

| 工具名 | 功能 | 管道令牌 |
|--------|------|---------|
| `query_mastery` | 查询节点精通度 | 不需要 |
| `generate_question` | 基于 ACP 数据包出题 | 产生 token_A |
| `score_answer` | AutoSCORE 评分 | 消费 token_A，产生 token_B |
| `update_fsrs` | 更新 FSRS 记忆参数 | 消费 token_B |
| `update_bkt` | 更新 BKT 掌握概率 | 消费 token_B |
| `search_memories` | 搜索 Graphiti 学习记忆 | 不需要 |
| `record_calibration` | 记录校准数据 | 不需要 |
| `assemble_acp` | 组装 ACP 考察数据包 | 不需要 |
| `archive_conversation` | 归档对话 | 不需要 |
| `create_exam_node` | 创建检验白板节点 | 不需要 |

### 密码学令牌管道流程

```
Agent 调 generate_question → 返回 {question, token_A}
Agent 调 score_answer(token=token_A, answer="...") → 返回 {score, token_B}
Agent 调 update_fsrs(token=token_B) → 完成
Agent 试图直接调 update_fsrs(无token) → 拒绝 PIPELINE_TOKEN_INVALID
```

### MCP 配置文件格式

```json
{
  "mcpServers": {
    "canvas-learning": {
      "type": "sse",
      "url": "http://localhost:8001/mcp",
      "description": "Canvas Learning System backend tools"
    }
  }
}
```

### 关键约束

1. **FastAPI-MCP ASGI 直连**：不走额外 HTTP proxy，减少延迟
2. **工具名 snake_case**：遵循架构命名规范
3. **Pydantic Schema**：每个工具必须有完整的输入/输出 JSON Schema
4. **审计不阻塞**：`asyncio.create_task` 异步执行，工具调用不等审计完成
5. **6 层防御**：此 Story 实现 Layer 0（后端算法权威）、Layer 1（密码学令牌）、Layer 4（审计守护）

### 不做的事项（防蔓延）

- 不实现 Layer 2 CLAUDE.md/AGENTS.md（文件层面，直接创建即可）
- 不实现 Layer 3 Claude Code Hooks（远期 MVP 不管替换降级）
- 不实现 Layer 5 结构化输出（由各 Story 的 prompt 设计控制）
- 不实现 MCP 工具的具体业务逻辑（`query_mastery` 调用的 `mastery_engine` 由 Story 5.1 实现）
- 不实现前端 MCP 客户端连接（Story 3.1 的 `--mcp-config` 已覆盖）

### Project Structure Notes

- 后端新建：`backend/app/mcp/server.py`, `backend/app/mcp/tools/`, `backend/app/mcp/pipeline_token.py`
- 后端新建：`backend/app/audit/guardian.py`
- 前端新建：`obsidian-canvas-learning/src/services/mcp-config.ts`
- 保持现有 `backend/app/` 目录结构不变

### References

- [Source: _decisions/ADR-001-dialogue-engine.md#具体实现方案] — MCP 注入方式
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions] — 6 层防御架构
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns] — MCP 令牌链
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — MCP 工具命名规范

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
