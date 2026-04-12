# Story 3.1: Claude Code CLI 集成与 per-node Session

Status: ready-for-dev

## Story

As a 用户,
I want 点击白板节点时自动启动 Claude Code 对话，每个节点有独立的对话历史，切换节点时对话无缝恢复,
so that 每个知识点都有专属的 AI 助手记住我们的对话。

## Acceptance Criteria

1. **AC-1: Spawn Claude Code CLI 子进程**
   - **Given** 用户点击白板上的节点 A
   - **When** 右侧面板打开对话窗口
   - **Then** 通过 Claude Agent SDK 的自定义 spawn 回调启动官方 `claude` binary 子进程
   - **And** 传入 `--output-format stream-json` 启用流式 NDJSON 输出
   - **And** 传入 `-p "用户消息"` 发送对话消息

2. **AC-2: 认证自动继承**
   - **Given** 用户已登录 Claude Code（Max/Pro 订阅）
   - **When** spawn 子进程
   - **Then** 自动继承 `~/.claude/.credentials.json` 认证信息
   - **And** 用户无需在插件中配置 API Key 即可对话
   - **And** 认证失败时（exit code 2 / ENOENT）发出 `auth_failed` 事件供 Story 3.9 Fallback 消费

3. **AC-3: per-node 独立 Session**
   - **Given** 节点 A 已有历史对话
   - **When** 用户切换到节点 A
   - **Then** 使用 `--resume $sessionId` 恢复该节点的完整对话历史
   - **And** SQLite 存储 `node_sessions` 表：`nodeId → sessionId` 映射
   - **And** 首次对话的节点自动创建新 session（不传 --resume）

4. **AC-4: 节点切换 Session 保持**
   - **Given** 用户在节点 A 对话中
   - **When** 切换到节点 B
   - **Then** 节点 A 的 session 完整保留（不销毁进程状态）
   - **And** 节点 B 使用自己的 sessionId resume
   - **And** 再次切回节点 A 时对话历史完整可见

5. **AC-5: 引擎可替换接口解耦**
   - **Given** FR-AGENT-03 要求引擎可替换
   - **When** 实现对话引擎层
   - **Then** 定义 `DialogEngine` 接口（`sendMessage / resume / getHistory / destroy`）
   - **And** `ClaudeCodeEngine` 实现该接口（spawn CLI 方案）
   - **And** 未来可插入 `ApiKeyEngine`（API 方案）或 `AcpEngine`（ACP 方案）而不改上层代码

## Tasks / Subtasks

- [ ] **Task 1: DialogEngine 接口定义** (AC: #5)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/services/dialog-engine.ts`：定义 `DialogEngine` 接口
    ```typescript
    interface DialogEngine {
      sendMessage(nodeId: string, message: string): AsyncIterable<StreamEvent>;
      resume(sessionId: string): Promise<void>;
      getSessionId(nodeId: string): Promise<string | null>;
      destroy(nodeId: string): Promise<void>;
      onError: EventEmitter<EngineError>;
    }
    ```
  - [ ] 1.2 定义 `StreamEvent` 类型（text / tool_use / tool_result / error / done）
  - [ ] 1.3 定义 `EngineError` 类型（auth_failed / spawn_failed / rate_limited / crash）

- [ ] **Task 2: ClaudeCodeEngine 实现** (AC: #1, #2)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/services/claude-code-engine.ts`
  - [ ] 2.2 实现 `spawnClaudeCode(args: string[])`：使用 Node.js `child_process.spawn` 启动 `claude` binary
  - [ ] 2.3 参考 Claudian(`YishenTu/claudian`) `customSpawn.ts` 的 spawn 模式实现进程管理
  - [ ] 2.4 实现 stream-json NDJSON 解析：逐行读取 stdout，解析为 `StreamEvent`
  - [ ] 2.5 实现认证检测：捕获 exit code 2 / ENOENT，emit `auth_failed` 事件
  - [ ] 2.6 实现 `--resume sessionId` 参数传递

- [ ] **Task 3: Session 管理（SQLite）** (AC: #3, #4)
  - [ ] 3.1 创建 `obsidian-canvas-learning/src/services/session-store.ts`
  - [ ] 3.2 使用 Obsidian 插件 data 目录下的 SQLite 文件存储 session 映射
  - [ ] 3.3 实现 `node_sessions` 表 schema：`nodeId TEXT PRIMARY KEY, sessionId TEXT NOT NULL, createdAt TEXT, lastActiveAt TEXT`
  - [ ] 3.4 实现 `getSessionId(nodeId)` / `createSession(nodeId, sessionId)` / `updateLastActive(nodeId)` 方法
  - [ ] 3.5 session ID 使用 Claude Code 自动生成的 session ID（首次对话后从 stream 中提取）

- [ ] **Task 4: 节点对话入口集成** (AC: #1, #3, #4)
  - [ ] 4.1 在 `chat-state.svelte.ts` 中新增 `activeNodeId` 和 `activeEngine` 状态
  - [ ] 4.2 实现 `openNodeChat(nodeId)` 方法：查询 sessionId → resume 或 new → 更新 Store
  - [ ] 4.3 实现 `switchNode(newNodeId)` 方法：保存当前 → 切换 → resume 新节点
  - [ ] 4.4 节点切换时不销毁旧 session（只是停止监听流）

- [ ] **Task 5: MCP 配置预留** (AC: #1)
  - [ ] 5.1 spawn 时传入 `--mcp-config ./canvas-mcp.json`（配置文件路径由 Task 3.2 提供）
  - [ ] 5.2 创建 MCP 配置生成逻辑（根据后端地址动态生成 `canvas-mcp.json`）
  - [ ] 5.3 MCP 工具的具体暴露由 Story 3.2 实现，此处仅预留配置注入点

## Dev Notes

### 对话引擎架构（ADR-001 确认）

```
Obsidian Plugin (Svelte UI)
  → DialogEngine 接口
    → ClaudeCodeEngine (spawn 模式，MVP)
      → child_process.spawn('claude', [...args])
        → --resume $nodeSessionId
        → --mcp-config ./canvas-mcp.json
        → --append-system-prompt $nodeContext (Story 3.4)
        → --output-format stream-json
    → ApiKeyEngine (Fallback, Story 3.9)
    → AcpEngine (远期)
  → StreamEvent → Svelte Store → UI
```

### 参考实现

- **Claudian**（`YishenTu/claudian`）：spawn 模式核心参考。`customSpawn.ts` 管理进程生命周期，`MessageChannel.ts` 处理 NDJSON 流，`SessionManager.ts` 管理 per-conversation session
- **Pencil**：验证 "Connected via subscription" 模式可行
- **opencode-claude-max-proxy**：验证 CLI proxy 模式可行

### Claude Code CLI 关键参数

| 参数 | 用途 | 示例 |
|------|------|------|
| `-p "message"` | 发送单条消息（非交互模式） | `claude -p "解释贝叶斯定理"` |
| `--resume $id` | 恢复指定 session | `claude --resume abc123 -p "继续"` |
| `--output-format stream-json` | NDJSON 流式输出 | 每行一个 JSON 对象 |
| `--mcp-config path` | 注入 MCP 工具配置 | `--mcp-config ./canvas-mcp.json` |
| `--append-system-prompt` | 追加系统提示 | Story 3.4 使用 |

### stream-json NDJSON 格式

```jsonl
{"type":"assistant","message":{"content":[{"type":"text","text":"你好"}]}}
{"type":"result","subtype":"success","session_id":"abc123","cost_usd":0.001}
```

### 关键约束

1. **Electron 环境**：Obsidian 运行在 Electron 中，`child_process` 可用（Node.js API）
2. **进程生命周期**：每次 `sendMessage` spawn 一个短生命周期进程（`-p` 模式），非长连接
3. **Session 文件**：Claude Code 将 session 数据存在 `~/.claude/projects/` 下，`--resume` 从该目录恢复
4. **并发控制**：同一节点同时只允许一个 spawn 进程（防止重复发送）
5. **认证文件路径**：`~/.claude/.credentials.json`（Windows: `%USERPROFILE%\.claude\.credentials.json`）

### 不做的事项（防蔓延）

- 不实现 ChatPanel UI（Story 3.3）
- 不实现 MCP 工具暴露（Story 3.2）
- 不实现 --append-system-prompt 上下文注入（Story 3.4）
- 不实现 /命令技能集成（Story 3.5）
- 不实现 Fallback 引擎切换（Story 3.9）
- 不实现 Crash Recovery（Story 3.11）
- 不实现对话消息持久化到本地（ChatPanel 层面，Story 3.3 负责）

### Project Structure Notes

- 新建文件在 `obsidian-canvas-learning/src/services/` 目录下
- `dialog-engine.ts`、`claude-code-engine.ts`、`session-store.ts` 三个文件
- 遵循 kebab-case.ts 命名规范
- Store 更新通过 `chat-state.svelte.ts` 方法，不直接操作

### References

- [Source: _decisions/ADR-001-dialogue-engine.md] — 对话引擎选型决策全文
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions] — Mode D 架构决策
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns] — MCP 通信模式
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — 前端目录结构

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
