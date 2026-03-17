# Story 3.9: 引擎 Fallback 机制

Status: ready-for-dev

## Story

As a 用户,
I want 当 Claude Code spawn 失败时系统自动切换到 API Key 模式,
so that 即使订阅认证不可用，我的对话功能不中断。

## Acceptance Criteria

1. **AC-1: Spawn 失败检测**
   - **Given** ClaudeCodeEngine 尝试 spawn Claude Code CLI 子进程
   - **When** spawn 返回 exit code 2（认证错误）或 ENOENT（binary 不存在）
   - **Then** 插件检测到 spawn 失败
   - **And** 不再重复尝试 spawn（避免循环失败）

2. **AC-2: 用户通知**
   - **Given** spawn 失败被检测到
   - **When** 错误事件触发
   - **Then** 弹出 Obsidian Notice "订阅认证不可用，切换到 API Key 模式"
   - **And** 通知持续显示直到用户确认或自动消失（10s）
   - **And** 通知中包含"配置 API Key"按钮，点击跳转到 Settings Tab

3. **AC-3: 自动切换到 API Key 模式**
   - **Given** spawn 失败且用户已在 Settings Tab 配置了备用 API Key
   - **When** Fallback 触发
   - **Then** 自动切换 DialogEngine 实现从 `ClaudeCodeEngine` 到 `ApiKeyEngine`
   - **And** 使用 Claude Agent SDK 直接 API 调用模式（不经过 CLI）
   - **And** 切换过程对用户透明（对话窗口不关闭不刷新）

4. **AC-4: 对话历史不丢失**
   - **Given** 引擎从 ClaudeCode 切换到 ApiKey
   - **When** 用户继续对话
   - **Then** 对话历史完整保留（SQLite 中的消息不受引擎切换影响）
   - **And** session 数据保持一致（同一 nodeId 的对话上下文不断裂）

5. **AC-5: Settings Tab 备用 API Key 配置**
   - **Given** 用户打开 Settings Tab → Canvas Learning System
   - **When** 在"备用 API Key"区域
   - **Then** 可以输入 Anthropic API Key
   - **And** API Key 不明文显示（密码输入框 + 显示/隐藏切换）
   - **And** 提供"测试连接"按钮验证 Key 有效性
   - **And** API Key 存储在 Obsidian 本地插件配置中

## Tasks / Subtasks

- [ ] **Task 1: ApiKeyEngine 实现** (AC: #3)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/services/api-key-engine.ts`
  - [ ] 1.2 实现 `DialogEngine` 接口（Story 3.1 定义）
  - [ ] 1.3 使用 `@anthropic-ai/sdk` 直接 API 调用（非 spawn CLI）
  - [ ] 1.4 实现流式输出：`client.messages.stream()` → 转换为 `StreamEvent`
  - [ ] 1.5 session 管理：通过 conversation history 数组维护上下文（非 --resume）
  - [ ] 1.6 MCP 工具注入：通过 SDK 的 `tools` 参数注入（非 --mcp-config）

- [ ] **Task 2: Fallback 切换逻辑** (AC: #1, #3, #4)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/services/engine-fallback.ts`
  - [ ] 2.2 实现 `EngineFallbackManager`：
    - 监听 `ClaudeCodeEngine.onError` 的 `auth_failed` / `spawn_failed` 事件
    - 检查是否有备用 API Key 配置
    - 有 Key → 自动切换到 `ApiKeyEngine`
    - 无 Key → 提示用户配置
  - [ ] 2.3 切换时：替换 `chat-state.svelte.ts` 中的 `activeEngine` 引用
  - [ ] 2.4 切换后：已有对话历史从 SQLite 加载（不依赖引擎状态）
  - [ ] 2.5 记录引擎状态到插件设置：`currentEngine: 'claude-code' | 'api-key'`

- [ ] **Task 3: 用户通知与引导** (AC: #2, #5)
  - [ ] 3.1 Fallback 触发时使用 `new Notice()` 显示切换提示
  - [ ] 3.2 Notice 内容：状态说明 + "配置 API Key" 按钮
  - [ ] 3.3 扩展 Settings Tab（Story 1.3）添加"备用 API Key"配置区域
  - [ ] 3.4 API Key 输入框：`type="password"` + 显示/隐藏切换按钮
  - [ ] 3.5 "测试连接"按钮：调用 Anthropic API `messages.create` 验证 Key

- [ ] **Task 4: 引擎状态 UI 指示** (AC: #2)
  - [ ] 4.1 ChatPanel 标题栏显示当前引擎状态：
    - "Claude Code (订阅)" — 正常
    - "API Key (备用)" — Fallback 模式
  - [ ] 4.2 状态文字使用不同颜色区分
  - [ ] 4.3 点击状态文字可手动切换引擎（如用户修复订阅后切回）

## Dev Notes

### Fallback 决策树

```
spawn Claude Code CLI
  ├── 成功 → 使用 ClaudeCodeEngine（正常模式）
  └── 失败
      ├── exit code 2 (认证错误) → 检查备用 API Key
      │   ├── 有 Key → 切换 ApiKeyEngine + Notice
      │   └── 无 Key → Notice 提示配置 + 跳转 Settings
      ├── ENOENT (binary 不存在) → 同上
      └── 其他错误 → Story 3.11 Crash Recovery 处理
```

### ApiKeyEngine vs ClaudeCodeEngine 差异

| 维度 | ClaudeCodeEngine | ApiKeyEngine |
|------|-----------------|-------------|
| 认证 | ~/.claude/.credentials.json | 用户配置的 API Key |
| 费用 | 订阅额度（免费） | API 按量付费 |
| Session | --resume（Claude Code 管理） | 手动维护 messages 数组 |
| MCP | --mcp-config（配置文件） | SDK tools 参数注入 |
| 上下文 | --append-system-prompt | system message 参数 |
| 流式 | stream-json NDJSON | SDK messages.stream() |

### API Key 安全

- 存储在 `this.loadData()` → Obsidian 本地 `data.json`（不入 git）
- 显示时用 `type="password"`，不明文
- 不写入日志文件（NFR-SEC-02）
- 仅在 API 调用时读取，不缓存到内存变量

### 关键约束

1. **不主动检测**：不在启动时预检 Claude Code 可用性，首次使用时才检测
2. **切换透明**：UI 层面对话窗口不关闭不刷新，只是底层引擎替换
3. **session 不互通**：ClaudeCode session（CLI 管理）和 ApiKey session（手动 messages 数组）不互通，但对话历史（SQLite）共享
4. **手动切回**：用户修复订阅后可在 UI 中手动切回 ClaudeCodeEngine

### 不做的事项（防蔓延）

- 不实现 ACP 引擎（远期）
- 不实现多 API Key 轮换
- 不实现 API Key 成本估算/预算控制（Story 7.2 的 Token 追踪覆盖）
- 不实现自动检测订阅恢复后切回（需用户手动）
- 不实现其他 LLM 提供商的 Fallback（仅 Anthropic API）

### Project Structure Notes

- 前端新建：`obsidian-canvas-learning/src/services/api-key-engine.ts`
- 前端新建：`obsidian-canvas-learning/src/services/engine-fallback.ts`
- 扩展：`chat-state.svelte.ts` 添加引擎切换逻辑
- 扩展：Settings Tab（Story 1.3）添加备用 API Key 配置区域
- 扩展：`ChatPanel.svelte`（Story 3.3）标题栏显示引擎状态

### References

- [Source: _decisions/ADR-001-dialogue-engine.md#Fallback 策略] — Fallback 策略设计
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.9] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions] — FR-AGENT-03 引擎可替换

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
