---
story_id: "8.7"
epic_id: "8"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 4
depends_on: ["8.6"]
blocks: []
trace:
  - "FR-OBS-03"
---

# Story 8.7: 操作审计日志

Status: ready-for-dev

## Story
As a 学习者,
I want 查看操作审计日志,
So that 遇到问题时可以排查具体是哪一步出了故障。

## Acceptance Criteria

1. **Given** 系统执行任何知识图谱操作（读取 / 写入 / 查询 / 同步）**When** 操作完成（成功或失败）**Then** 审计日志追加一行记录：`[timestamp] [type] [target] [latency_ms] [status]` **And** 日志文件为 `outputs/graphiti-audit.log`

2. **Given** 审计日志记录操作 **When** 写入日志行 **Then** 各字段定义为：
   - `timestamp`: ISO 8601 格式（`2026-04-12T15:30:45.123Z`）
   - `type`: 操作类型枚举（`READ_MEMORY` / `WRITE_MEMORY` / `UPDATE_MASTERY` / `CLASSIFY_ERROR` / `SEARCH_FACTS` / `HEARTBEAT` / `CACHE_DRAIN`）
   - `target`: 操作目标（concept slug / edge slug / session_id）
   - `latency_ms`: 操作耗时（毫秒）
   - `status`: `OK` / `RETRY` / `FAIL` / `CACHE`
   **And** 每行为 JSON 格式（方便后续解析）

3. **Given** 审计日志文件位于 vault 内 `outputs/` 目录 **When** 学习者打开该文件 **Then** Obsidian 可以直接查看日志内容（纯文本/JSON lines 格式）**And** 日志文件不被 Dataview 索引（通过 `.obsidian/plugins/dataview/` 配置排除 `outputs/`）

4. **Given** 审计日志持续增长 **When** 文件大小超过 5MB **Then** 自动轮转：当前文件重命名为 `graphiti-audit-<date>.log`，新建空的 `graphiti-audit.log` **And** 保留最近 5 个历史文件 **And** 超过 5 个的自动删除最旧的

5. **Given** Story 8.6 中写入失败累积通知包含"查看详情"链接 **When** 学习者点击 **Then** 直接打开 `outputs/graphiti-audit.log` 并滚动到最近的 FAIL 记录

6. **Given** 系统处于考察保护模式（Story 8.6 考察中断开）**When** 缓存操作执行 **Then** 审计日志记录 status 为 `CACHE`（区别于正常 OK 和失败 FAIL）

## Tasks / Subtasks

- [ ] Task 1: 实现审计日志写入器 (AC: #1, #2)
  - [ ] 创建 `backend/app/services/audit_log_service.py`
  - [ ] 定义 AuditLogEntry 数据类：timestamp / type / target / latency_ms / status
  - [ ] 实现 `log_operation(entry: AuditLogEntry)` 方法
  - [ ] JSON lines 格式写入 `outputs/graphiti-audit.log`
  - [ ] 异步写入（不阻塞主操作）

- [ ] Task 2: 在各 MCP 工具中添加审计 hook (AC: #1, #6)
  - [ ] search_memories: 包裹 timing + log READ_MEMORY
  - [ ] add_memory: 包裹 timing + log WRITE_MEMORY
  - [ ] update_mastery: 包裹 timing + log UPDATE_MASTERY
  - [ ] classify_error: 包裹 timing + log CLASSIFY_ERROR
  - [ ] heartbeat: log HEARTBEAT
  - [ ] cache drain: log CACHE_DRAIN
  - [ ] 每个 hook 记录 latency_ms 和 success/fail

- [ ] Task 3: 实现日志轮转 (AC: #4)
  - [ ] 每次写入前检查文件大小
  - [ ] > 5MB 触发轮转：rename + 新建
  - [ ] 清理超过 5 个历史文件
  - [ ] 单元测试：轮转逻辑正确性

- [ ] Task 4: 配置 Dataview 排除 outputs/ (AC: #3)
  - [ ] 在 `.obsidian/plugins/dataview/data.json` 中排除 `outputs/` 目录
  - [ ] 验证审计日志不出现在 Dataview 查询结果中

- [ ] Task 5: 实现"查看详情"链接集成 (AC: #5)
  - [ ] Story 8.6 的持久通知中添加 `app.workspace.openLinkText()` 调用
  - [ ] 打开 `outputs/graphiti-audit.log` 并定位到末尾

## Dev Notes

### Architecture
- 审计日志是可观测性的第三层（最深层），面向排查问题的高级用户
- JSON lines 格式兼容 `jq` 命令行工具和各种日志分析工具
- 异步写入确保日志不影响主操作的性能
- 日志轮转防止 vault 空间被无限增长的日志占满

### Log Entry Schema

```json
{
  "timestamp": "2026-04-12T15:30:45.123Z",
  "type": "WRITE_MEMORY",
  "target": "consistent-heuristic",
  "latency_ms": 42,
  "status": "OK"
}
```

### Type Enum

| Type | 对应操作 | 来源 |
|---|---|---|
| READ_MEMORY | search_memories / search_facts | 对话/考察前 |
| WRITE_MEMORY | add_memory | 对话/考察后 |
| UPDATE_MASTERY | update_mastery | 评分后 |
| CLASSIFY_ERROR | classify_error | 错误分类 |
| SEARCH_FACTS | search_memory_facts | 检索 |
| HEARTBEAT | 连接检测 | 30s 周期 |
| CACHE_DRAIN | 缓存重试 | 连接恢复后 |

### File Paths
- 审计日志服务：`backend/app/services/audit_log_service.py`（新建）
- 日志文件：`outputs/graphiti-audit.log`
- 历史日志：`outputs/graphiti-audit-<date>.log`
- MCP 工具 hook：`backend/app/mcp/tools/` 各文件
- Dataview 配置：`.obsidian/plugins/dataview/data.json`
- Story 8.6 通知集成：连接状态通知的"查看详情"按钮

### Testing
- 单元测试：日志条目格式化正确（JSON 可解析）
- 单元测试：日志轮转在 > 5MB 时触发
- 单元测试：历史文件超过 5 个时自动清理
- 集成测试：完整操作流程后审计日志包含预期条目

### References
- **From PRD**: §7 Graphiti 读写时序 (line 6275-6627)
- FR-OBS-03: 操作审计日志
- Story 8.5: 记忆操作摘要行（第一层可观测性）
- Story 8.6: 连接状态 + 写入失败通知（第二层可观测性）

## UAT Script

> 1. 确保 `outputs/` 目录存在
> 2. 开启一次对话，讨论某个概念
> 3. 对话结束后打开 `outputs/graphiti-audit.log`
> 4. 看到若干 JSON 行，包含 READ_MEMORY 和 WRITE_MEMORY 类型的记录
> 5. 每行包含 timestamp / type / target / latency_ms / status 字段
> 6. 断开 Neo4j，执行写入操作
> 7. 看到 status 为 FAIL 或 CACHE 的记录
> 8. 恢复 Neo4j，看到 CACHE_DRAIN 类型的记录
> 9. 在 Dashboard 中运行 Dataview 查询，确认 outputs/ 文件不出现在结果中
> 10. (可选) 生成大于 5MB 的日志文件，确认轮转正常

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 日志格式 | unit | `pytest tests/unit/test_audit_log_format.py -x` | 0 failures |
| 日志写入 | unit | `pytest tests/unit/test_audit_log_write.py -x` | 0 failures |
| 日志轮转 | unit | `pytest tests/unit/test_audit_log_rotation.py -x` | 0 failures |
| MCP hook | integration | `pytest tests/integration/test_audit_hooks.py -x` | 0 failures |
| Dataview 排除 | manual | Dataview 查询不含 outputs/ | 0 results from outputs/ |

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
