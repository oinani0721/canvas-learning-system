# Story 3.11: Crash Recovery

Status: ready-for-dev

## Story

As a 用户,
I want Claude Code 进程崩溃时自动恢复，不丢失我正在进行的对话,
so that 系统稳定可靠。

## Acceptance Criteria

1. **AC-1: 进程退出检测**
   - **Given** Claude Code 子进程正在运行
   - **When** 进程异常退出（exit code != 0 且不是 rate limit / 认证错误）
   - **Then** 插件立即检测到进程退出
   - **And** 区分异常退出（crash）vs 正常退出（消息处理完成）vs 已知错误（429/认证）

2. **AC-2: lastSentMessage 缓存**
   - **Given** 用户发送了一条消息
   - **When** 消息发送给 Claude Code 进程
   - **Then** 消息内容缓存为 `lastSentMessage`（内存 + SQLite 持久化）
   - **And** 进程正常完成后清除 `lastSentMessage`
   - **And** 进程崩溃时 `lastSentMessage` 仍可用

3. **AC-3: 自动重启进程**
   - **Given** 检测到进程异常退出
   - **When** 存在 `lastSentMessage`
   - **Then** 自动重启 Claude Code 进程
   - **And** 通过 `--resume sessionId` 恢复 session（对话历史完整）
   - **And** 重新发送 `lastSentMessage`（限一次重试）
   - **And** 对话面板显示"AI 连接中断，正在恢复..."提示

4. **AC-4: 重试限制**
   - **Given** 重试发送 lastSentMessage 后
   - **When** 进程再次崩溃
   - **Then** 不再自动重试（限一次）
   - **And** 对话面板显示"AI 暂时不可用，请稍后重试"
   - **And** 提供手动"重试"按钮

5. **AC-5: 连续 Crash 熔断**
   - **Given** 连续 3 次 crash（含初始 + 2 次重试之外的场景：如不同消息连续触发 crash）
   - **When** 第 3 次 crash 发生
   - **Then** 停止自动重试
   - **And** 通知用户"AI 暂时不可用，可能需要更新 Claude Code 或重启系统"
   - **And** 提供"检查更新"链接（指向 Claude Code 安装页面）
   - **And** 熔断状态在 5 分钟后自动解除（允许再次尝试）

## Tasks / Subtasks

- [ ] **Task 1: 进程生命周期监控** (AC: #1)
  - [ ] 1.1 扩展 `claude-code-engine.ts`（Story 3.1）添加进程退出监听
  - [ ] 1.2 监听 `child_process` 的 `exit` 和 `error` 事件
  - [ ] 1.3 分类退出原因：
    - exit code 0 → 正常完成
    - exit code 2 → 认证错误（交给 Story 3.9）
    - exit code 其他 → crash（本 Story 处理）
    - ENOENT → binary 不存在（交给 Story 3.9）
    - SIGTERM/SIGKILL → 外部终止（不自动重试）
  - [ ] 1.4 emit `process_crashed` 事件（携带 exit code + stderr 内容）

- [ ] **Task 2: lastSentMessage 机制** (AC: #2)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/services/crash-recovery.ts`
  - [ ] 2.2 实现 `CrashRecoveryManager` 类：
    ```typescript
    class CrashRecoveryManager {
      private lastSentMessage: { nodeId: string, message: string, timestamp: Date } | null;
      private crashCount: number = 0;
      private circuitOpen: boolean = false;
    }
    ```
  - [ ] 2.3 `cacheMessage(nodeId, message)`: 发送前缓存消息（内存 + SQLite `crash_recovery` 表）
  - [ ] 2.4 `clearMessage()`: 正常完成后清除缓存
  - [ ] 2.5 `getLastMessage()`: crash 后读取缓存的消息
  - [ ] 2.6 SQLite 表 `crash_recovery`：`nodeId TEXT, message TEXT, sessionId TEXT, timestamp TEXT`

- [ ] **Task 3: 自动恢复逻辑** (AC: #3, #4)
  - [ ] 3.1 监听 `process_crashed` 事件
  - [ ] 3.2 检查 `lastSentMessage` 是否存在
  - [ ] 3.3 存在且未重试过 → 执行恢复：
    - spawn 新进程 + `--resume sessionId`
    - 重新发送 `lastSentMessage`
    - 标记已重试（`retried = true`）
  - [ ] 3.4 已重试过 → 不自动重试，显示手动"重试"按钮
  - [ ] 3.5 不存在 lastSentMessage → 仅重启进程恢复 session，不重发消息

- [ ] **Task 4: 熔断器** (AC: #5)
  - [ ] 4.1 实现 crash 计数器：5 分钟滑动窗口内的 crash 次数
  - [ ] 4.2 计数 >= 3 → 熔断器打开（`circuitOpen = true`）
  - [ ] 4.3 熔断状态下：不自动重启，显示错误通知
  - [ ] 4.4 5 分钟后自动解除熔断（`setTimeout`）
  - [ ] 4.5 熔断通知包含：错误说明 + "检查更新"链接 + 手动"重试"按钮

- [ ] **Task 5: 恢复 UI 反馈** (AC: #3, #4, #5)
  - [ ] 5.1 创建 `obsidian-canvas-learning/src/components/chat/RecoveryBanner.svelte`
  - [ ] 5.2 三种状态：
    - recovering：显示"AI 连接中断，正在恢复..."（带旋转动画）
    - failed：显示"AI 暂时不可用" + 手动"重试"按钮
    - circuit_open：显示"AI 多次异常" + "检查更新"链接
  - [ ] 5.3 banner 显示在 ChatPanel 消息列表顶部（不遮挡已有消息）
  - [ ] 5.4 恢复成功后自动消失

## Dev Notes

### Crash Recovery 参考实现：Claudian

Claudian（`YishenTu/claudian`）的 crash recovery 机制：
- 缓存 `lastSentMessage`：每次发送前持久化到本地
- 进程退出检测：`child_process.on('exit', code => { ... })`
- 自动重启：spawn 新进程 + `--resume` + 重发 lastSentMessage
- 重试限制：限一次自动重试

### 退出码分类

| Exit Code | 含义 | 处理 |
|-----------|------|------|
| 0 | 正常完成 | 清除 lastSentMessage |
| 1 | 一般错误 | crash recovery |
| 2 | 认证错误 | Story 3.9 Fallback |
| ENOENT | binary 不存在 | Story 3.9 Fallback |
| SIGTERM | 外部终止 | 不重试 |
| 其他 | 未知错误 | crash recovery |

### 恢复流程图

```
进程异常退出 (exit != 0)
  ├── 认证/binary错误 → Story 3.9 Fallback
  └── 其他 crash
      ├── 熔断器已打开 → 显示错误通知，不重试
      └── 熔断器未打开
          ├── 有 lastSentMessage 且未重试
          │   └── 自动重启 + resume + 重发消息
          │       ├── 成功 → 清除 lastSentMessage，恢复正常
          │       └── 再次 crash → crashCount++ → 显示手动重试
          └── 无 lastSentMessage 或已重试
              └── 显示错误 + 手动重试按钮
```

### 关键约束

1. **限一次自动重试**：避免死循环（某个消息必然触发 crash 的情况）
2. **lastSentMessage 持久化**：不仅在内存中缓存，还写入 SQLite（防止插件崩溃丢失）
3. **熔断器 5 分钟窗口**：5 分钟内 3 次 crash → 停止重试，避免频繁 spawn
4. **不重试 SIGTERM**：用户手动终止（如重启 Obsidian）不触发自动恢复
5. **与 Story 3.9/3.10 协作**：认证错误走 Fallback，429 走额度管理，crash 走本 Story

### 不做的事项（防蔓延）

- 不实现 crash 日志上报（仅本地日志）
- 不实现 crash 原因分析（仅记录 exit code + stderr）
- 不实现 Claude Code 自动更新
- 不实现多进程心跳检测
- 不实现 crash 统计 Dashboard

### Project Structure Notes

- 前端新建：`obsidian-canvas-learning/src/services/crash-recovery.ts`
- 前端新建：`obsidian-canvas-learning/src/components/chat/RecoveryBanner.svelte`
- 扩展：`claude-code-engine.ts`（Story 3.1）添加进程退出监听
- 扩展：`ChatPanel.svelte`（Story 3.3）集成 RecoveryBanner

### References

- [Source: _decisions/ADR-001-dialogue-engine.md#风险与缓解] — session 文件 crash 导致 Claude Code 崩溃
- [Source: _decisions/ADR-001-dialogue-engine.md#参考实现] — Claudian crash recovery（缓存 lastSentMessage + 进程重启重试）
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.11] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns] — 错误处理分层 + 重试策略

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
