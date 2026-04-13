---
story_id: "8.6"
epic_id: "8"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["5.8"]
blocks: ["8.7"]
trace:
  - "FR-OBS-02"
  - "FR-OBS-04"
---

# Story 8.6: 连接状态指示 + 写入失败通知

Status: ready-for-dev

## Story
As a 学习者,
I want 实时看到知识图谱连接状态和写入失败通知,
So that 我知道系统是否正常工作，数据是否安全保存。

## Acceptance Criteria

1. **Given** 知识图谱服务（Neo4j + Graphiti）运行正常 **When** 系统周期性检测连接状态（每 30s heartbeat）**Then** 状态指示器显示 🟢 "正常" **And** 指示器位置在 Obsidian 状态栏（status bar）或 Dashboard 固定区域

2. **Given** 知识图谱服务响应变慢（heartbeat 延迟 > 2s）或正在重试连接 **When** 状态变化被检测到 **Then** 指示器切换为 🟡 "同步中..." **And** 切换延迟 < 1s（从检测到到 UI 更新）

3. **Given** 知识图谱服务完全断开（连续 3 次 heartbeat 失败）**When** 状态变化被检测到 **Then** 指示器切换为 🔴 "已断开" **And** 自动启动重连逻辑（指数退避：5s → 10s → 20s → 60s max）**And** 重连期间指示器保持 🔴 并显示"重连中..."

4. **Given** 知识图谱写入操作失败（add_memory / update_mastery / classify_error）**When** 失败发生 **Then** 在 < 5s 内弹出 Obsidian Notice 通知 **And** 通知文本为"知识图谱写入暂时受阻，数据已本地缓存" **And** 通知自动消失（8s timeout）**And** 不使用恐慌性措辞（"错误/失败/数据丢失"）

5. **Given** 写入失败后数据已本地缓存 **When** 连接恢复 **Then** 自动重试缓存的写入操作 **And** 重试成功后弹出"数据同步完成"通知 **And** 指示器恢复为 🟢

6. **Given** 多次写入连续失败（> 5 次）**When** 失败累积 **Then** 通知升级为持久性 Notice（不自动消失）**And** 通知文本为"多次写入受阻，建议检查 Neo4j 服务状态" **And** 提供"查看详情"按钮链接到审计日志（Story 8.7）

7. **Given** 学习者正在考察中 **When** 连接断开 **Then** 考察流程不中断 **And** 评分和掌握度更新缓存到本地 **And** 考察结束后的摘要行（Story 8.5）显示"🔴 离线（考察期间数据已缓存）"

## Tasks / Subtasks

- [ ] Task 1: 实现 heartbeat 连接检测 (AC: #1, #2, #3)
  - [ ] 在 `backend/app/services/graphiti_service.py` 中添加 `heartbeat()` 方法
  - [ ] 每 30s 发送一次 Neo4j bolt 连接检测
  - [ ] 三态判断：正常 (< 2s) / 慢 (> 2s) / 断开 (3 次连续失败)
  - [ ] 状态变化事件发射（供前端/插件消费）

- [ ] Task 2: 实现状态指示器 UI (AC: #1, #2, #3)
  - [ ] Obsidian status bar item 或 Dashboard 固定区域
  - [ ] 三态图标：🟢 / 🟡 / 🔴
  - [ ] 状态文本：正常 / 同步中... / 已断开
  - [ ] 重连期间显示"重连中..."

- [ ] Task 3: 实现指数退避重连 (AC: #3)
  - [ ] 重连间隔序列：5s → 10s → 20s → 60s（max）
  - [ ] 重连成功后恢复正常 heartbeat 间隔
  - [ ] 重连尝试次数记录到审计日志

- [ ] Task 4: 实现写入失败通知 (AC: #4, #6)
  - [ ] 写入操作 try/except 包裹，失败时触发通知
  - [ ] Obsidian Notice API 弹出通知（< 5s 延迟）
  - [ ] 正常失败：8s 自动消失
  - [ ] 累积失败（> 5 次）：持久 Notice + "查看详情"按钮
  - [ ] 措辞要求：不使用"错误/失败/数据丢失"

- [ ] Task 5: 实现本地缓存与自动重试 (AC: #5, #7)
  - [ ] 写入失败时将操作缓存到本地队列（SQLite 或 JSON 文件）
  - [ ] 连接恢复后自动 drain 缓存队列
  - [ ] 重试成功后弹出"数据同步完成"通知
  - [ ] 考察期间断开不中断流程

- [ ] Task 6: 实现考察保护模式 (AC: #7)
  - [ ] 考察期间的写入失败静默缓存（不弹通知打断考察）
  - [ ] 考察结束后统一报告缓存情况
  - [ ] 与 Story 8.5 摘要行集成

## Dev Notes

### Architecture
- 连接状态检测是独立的后台任务，不阻塞任何前台操作
- heartbeat 使用 Neo4j bolt driver 的 `session.run("RETURN 1")` 轻量查询
- 本地缓存使用 `outputs/write_cache.json` 或 SQLite，确保 vault 可移植性
- 考察保护模式确保学习体验不被技术问题打断

### State Machine

```
     heartbeat OK           heartbeat slow (>2s)
  ┌──────────────┐     ┌─────────────────────┐
  │   🟢 正常     │────→│    🟡 同步中          │
  │              │←────│                     │
  └──────────────┘     └─────────────────────┘
         │                       │
         │ 3x fail               │ 3x fail
         ↓                       ↓
  ┌──────────────────────────────────────────┐
  │              🔴 已断开                    │
  │   指数退避重连: 5s → 10s → 20s → 60s     │
  │   重连成功 → 🟢                           │
  └──────────────────────────────────────────┘
```

### File Paths
- Heartbeat 检测：`backend/app/services/graphiti_service.py`（heartbeat 方法）
- 写入缓存：`outputs/write_cache.json`
- 审计日志集成：`outputs/graphiti-audit.log`（Story 8.7）
- 状态指示器 UI：Claudian plugin 或 Obsidian status bar API
- 通知 API：Obsidian `new Notice()` 调用

### Testing
- 单元测试：heartbeat 三态判断逻辑
- 单元测试：指数退避间隔序列正确性
- 单元测试：写入缓存的 enqueue/dequeue 正确性
- 集成测试：断开 Neo4j → 写入缓存 → 恢复 → 自动重试 → 通知

### References
- **From PRD**: §7 Graphiti 读写时序 (line 6275-6627)
- FR-OBS-02: 知识图谱连接状态展示
- FR-OBS-04: 写入失败通知与自动重试
- NFR-DEG: 降级策略（Graphiti 不可用时）
- Story 8.5: 记忆操作摘要行（连接状态集成）

## UAT Script

> 1. 确保 Neo4j 正常运行，打开 Dashboard 或任意笔记
> 2. 确认状态指示器显示 🟢 "正常"
> 3. 停止 Neo4j 服务（`neo4j stop`）
> 4. 等待 < 2 分钟，看到指示器变为 🔴 "已断开"
> 5. 在断开状态下发起对话，确认对话正常进行
> 6. 对话结束后看到"知识图谱写入暂时受阻，数据已本地缓存"通知
> 7. 重启 Neo4j 服务（`neo4j start`）
> 8. 等待指示器恢复为 🟢，看到"数据同步完成"通知
> 9. 在考察中断开 Neo4j，确认考察不中断
> 10. 考察结束后摘要行显示"🔴 离线（考察期间数据已缓存）"

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| Heartbeat 三态 | unit | `pytest tests/unit/test_heartbeat.py -x` | 0 failures |
| 指数退避 | unit | `pytest tests/unit/test_exponential_backoff.py -x` | 0 failures |
| 写入缓存 | unit | `pytest tests/unit/test_write_cache.py -x` | 0 failures |
| 通知延迟 | integration | 断开 Neo4j 后写入操作 | 通知 < 5s 弹出 |
| 自动重试 | integration | 恢复 Neo4j 后检查缓存清空 | 缓存队列为空 |
| 考察保护 | integration | 考察中断开 Neo4j | 考察不中断 |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
