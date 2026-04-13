# Story 3.10: 额度管理与降级

Status: ready-for-dev

## Story

As a 用户,
I want 订阅额度用完时清楚知道发生了什么，并有应对方案,
so that 我不会困惑于为什么 AI 突然不回复了。

## Acceptance Criteria

1. **AC-1: 429 Rate Limit 检测**
   - **Given** Claude Code 返回 429 Rate Limit 错误
   - **When** 插件解析 stderr 错误信息
   - **Then** 识别出额度耗尽（区分于网络错误/认证错误）
   - **And** 提取重置时间信息（如果 stderr 中包含）

2. **AC-2: 额度耗尽通知**
   - **Given** 检测到 429 Rate Limit
   - **When** 通知展示
   - **Then** 对话面板显示友好提示"本周订阅额度已用完"
   - **And** 显示倒计时（如"预计 X 天后重置"，基于周重置周期）
   - **And** 提示不使用技术术语（不显示"429"/"Rate Limit"）

3. **AC-3: 降级选项**
   - **Given** 额度耗尽提示显示中
   - **When** 用户查看选项
   - **Then** 提供两个选项：
     - "等待重置"：显示倒计时，白板/编辑/FSRS 提醒等非 AI 功能正常使用
     - "临时切换 API Key"：跳转 Settings Tab 配置 API Key → 自动切换到 ApiKeyEngine
   - **And** 选项以按钮形式展示在对话面板中

4. **AC-4: 非 AI 功能不受影响**
   - **Given** 订阅额度耗尽
   - **When** 用户使用白板功能
   - **Then** 白板浏览/编辑/节点创建/连线/缩放等操作正常
   - **And** FSRS 复习提醒正常显示
   - **And** 学习档案面板正常查看
   - **And** 仅 AI 对话相关功能受限

5. **AC-5: 额度恢复自动检测**
   - **Given** 额度耗尽状态
   - **When** 用户尝试发送新消息
   - **Then** 系统重新尝试 spawn Claude Code
   - **And** 如果额度已恢复 → 自动恢复正常对话（Notice 提示"额度已恢复"）
   - **And** 如果仍受限 → 更新倒计时

## Tasks / Subtasks

- [ ] **Task 1: 429 错误解析** (AC: #1)
  - [ ] 1.1 扩展 `claude-code-engine.ts`（Story 3.1）的 stderr 解析逻辑
  - [ ] 1.2 识别 429 相关错误模式（Claude Code 的 stderr 输出格式）
  - [ ] 1.3 提取重置时间信息（解析 `retry-after` 或自然语言提示）
  - [ ] 1.4 emit `rate_limited` 事件（携带 `retryAfter` 时间）
  - [ ] 1.5 区分 429 Rate Limit vs 其他错误（网络/认证/crash）

- [ ] **Task 2: 额度状态管理** (AC: #1, #2, #5)
  - [ ] 2.1 在 `chat-state.svelte.ts` 添加额度状态：
    ```typescript
    quotaStatus: 'available' | 'exhausted' | 'checking'
    quotaResetTime: Date | null
    ```
  - [ ] 2.2 `rate_limited` 事件 → 设置 `quotaStatus = 'exhausted'` + `quotaResetTime`
  - [ ] 2.3 用户发送新消息时：先检查 `quotaStatus`
    - available → 正常发送
    - exhausted → 尝试重新 spawn（检测是否恢复）
  - [ ] 2.4 重新 spawn 成功 → `quotaStatus = 'available'` + Notice "额度已恢复"

- [ ] **Task 3: 降级 UI** (AC: #2, #3)
  - [ ] 3.1 创建 `obsidian-canvas-learning/src/components/chat/QuotaExhausted.svelte`
  - [ ] 3.2 组件显示在 ChatPanel 消息区域底部（替代输入栏位置）
  - [ ] 3.3 内容：
    - 标题："本周订阅额度已用完"
    - 倒计时："预计 X 天 X 小时后重置"（每分钟刷新）
    - 按钮 1："等待重置"（关闭提示，恢复输入栏但发送时再次检测）
    - 按钮 2："临时使用 API Key"（跳转 Settings Tab）
  - [ ] 3.4 CSS 类名 `.cl-chat-quota-exhausted`

- [ ] **Task 4: 倒计时逻辑** (AC: #2)
  - [ ] 4.1 实现倒计时计算：基于 `quotaResetTime` 或默认周重置周期
  - [ ] 4.2 如果无法获取精确重置时间：显示"通常在每周一重置"
  - [ ] 4.3 倒计时每分钟更新一次（`setInterval`，组件销毁时清理）

- [ ] **Task 5: 降级功能隔离** (AC: #4)
  - [ ] 5.1 确认白板操作不依赖 AI 引擎状态（应已解耦）
  - [ ] 5.2 确认 FSRS 提醒独立于对话引擎（后端定时器驱动）
  - [ ] 5.3 确认学习档案面板数据来自后端 API（非 Agent 调用）
  - [ ] 5.4 ChatPanel 输入栏在 exhausted 状态下显示占位提示"额度已用完"

## Dev Notes

### Claude Code 429 错误输出格式

Claude Code 在遇到 rate limit 时，stderr 中通常包含：
```
Error: Rate limit exceeded. Please try again later.
```
或 stream-json 输出中：
```json
{"type":"error","error":{"type":"rate_limit_error","message":"..."}}
```

需要两个渠道都监听：stderr 和 stdout stream-json error 事件。

### 额度重置周期

Claude Code Max/Pro 订阅通常按周重置额度：
- Max：每周重置（具体时间取决于订阅开始日）
- Pro：每月额度 + 额外购买

由于精确重置时间依赖 Anthropic 账户信息（无 API 可查），采用保守估计：
- 有 `retry-after` → 使用精确时间
- 无 → 显示"通常在每周一重置"

### 关键约束

1. **不显示技术术语**：用户看到的是"额度用完"，不是"429 Rate Limit"
2. **降级选项简洁**：只有两个选择（等待 / API Key），不增加认知负担
3. **非 AI 功能正常**：白板操作/FSRS/档案面板完全独立于对话引擎
4. **重试策略**：不自动轮询额度恢复，用户下次尝试发消息时才检测
5. **与 Story 3.9 联动**："临时使用 API Key" 选项复用 Story 3.9 的 `EngineFallbackManager`

### 不做的事项（防蔓延）

- 不实现额度用量追踪（Anthropic 无公开 API 查询剩余额度）
- 不实现额度预警（"已用 80%"）
- 不实现自动轮询检测额度恢复
- 不实现多级降级（仅订阅→API Key 一级降级）
- 不实现 API Key 模式下的用量估算

### Project Structure Notes

- 前端新建：`obsidian-canvas-learning/src/components/chat/QuotaExhausted.svelte`
- 扩展：`claude-code-engine.ts`（Story 3.1）添加 429 解析
- 扩展：`chat-state.svelte.ts` 添加额度状态管理
- 扩展：`ChatPanel.svelte`（Story 3.3）集成 QuotaExhausted 组件

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.10] — Story 需求和 AC
- [Source: _decisions/ADR-001-dialogue-engine.md#风险与缓解] — CLI 每次 spawn 开销 + rate limit 风险
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns] — LLM 调用管理 + 离线降级策略

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
