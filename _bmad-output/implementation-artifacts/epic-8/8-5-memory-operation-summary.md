---
story_id: "8.5"
epic_id: "8"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 4
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-OBS-01"
---

# Story 8.5: 记忆操作摘要行

Status: ready-for-dev

## Story
As a 学习者,
I want 每次对话或考察结束时看到记忆操作摘要,
So that 我知道系统在后台做了什么（透明度），但不被原始分数干扰学习。

## Acceptance Criteria

1. **Given** 一次 AI 对话结束（学习者关闭对话或切换笔记）**When** 系统完成所有后台操作（记忆加载 + 数据保存 + 图谱同步）**Then** 在对话末尾追加一行摘要 callout：`> [!info]- 记忆操作 · 已加载 N 条记忆 · 已保存 M 条记录 · 🟢 连接正常` **And** callout 默认折叠（`-` 标记），学习者主动展开才看到详情

2. **Given** 一次考察结束（最后一题评分完成）**When** 系统完成所有后台操作 **Then** 在考察记录末尾追加同格式摘要 callout **And** 摘要中 N = 考察前加载的记忆条数（用于出题）、M = 考察后写入的记录条数（评分/错误分类/掌握度更新）

3. **Given** 摘要行展示操作计数 **When** 渲染内容 **Then** 只显示操作统计（N 条加载、M 条保存）**And** 不显示具体的掌握度分数或评分结果 **And** 不显示具体的错误内容或正确答案 **And** 这是"透明度分层"原则：状态可见，分数隐藏

4. **Given** 摘要行展示连接状态 **When** 知识图谱连接正常 **Then** 显示 "🟢 连接正常" **When** 连接重试中 **Then** 显示 "🟡 同步中..." **When** 连接断开 **Then** 显示 "🔴 离线（数据已缓存，恢复后自动同步）"

5. **Given** 后台写入操作部分失败 **When** 生成摘要 **Then** 显示实际成功数："已保存 M/T 条记录（T 条中 M 条成功）" **And** 失败的操作在展开详情中列出（不在折叠标题中暴露）

6. **Given** 系统在对话/考察过程中完成了 0 次记忆加载或 0 次保存 **When** 生成摘要 **Then** 对应项显示 "0" 而非省略 **And** 即使全为 0 也生成摘要行（确保学习者知道系统尝试过）

## Tasks / Subtasks

- [ ] Task 1: 实现操作计数器 (AC: #1, #2, #6)
  - [ ] 在 MCP 工具层添加操作计数 hook：每次 search_memories 调用时 loaded_count += 1
  - [ ] 每次 add_memory / update_mastery / classify_error 调用时 saved_count += 1
  - [ ] 计数器绑定到当前 session（对话或考察 session）
  - [ ] session 结束时读取计数并重置

- [ ] Task 2: 实现摘要 callout 生成 (AC: #1, #2, #3)
  - [ ] 格式化摘要文本：`已加载 {loaded} 条记忆 · 已保存 {saved} 条记录 · {connection_status}`
  - [ ] callout 类型：`[!info]-`（默认折叠）
  - [ ] 展开详情：各操作类型的明细（N 次记忆检索、M 次掌握度更新、K 次错误分类...）
  - [ ] 禁止在摘要中包含分数/答案/错误内容

- [ ] Task 3: 实现连接状态读取 (AC: #4)
  - [ ] 从 graphiti_service 获取当前连接状态
  - [ ] 三态映射：🟢 正常 / 🟡 同步中 / 🔴 离线
  - [ ] 离线时追加说明"数据已缓存，恢复后自动同步"

- [ ] Task 4: 实现部分失败处理 (AC: #5)
  - [ ] 统计成功/失败次数：saved_success / saved_total
  - [ ] 折叠标题显示 M/T 格式
  - [ ] 展开详情列出失败的操作（类型 + 错误简述）
  - [ ] 不在折叠标题暴露失败详情

- [ ] Task 5: 集成到对话和考察流程 (AC: #1, #2)
  - [ ] 对话结束 hook：调用摘要生成并追加到对话文件末尾
  - [ ] 考察结束 hook：调用摘要生成并追加到 exam_boards/*.md 末尾
  - [ ] 确保摘要追加不影响 frontmatter

## Dev Notes

### Architecture
- 摘要行是可观测性的第一层：对所有学习者可见，但不暴露原始分数
- "透明度分层"设计：Layer 1 摘要行（所有人）→ Layer 2 连接状态指示器（Story 8.6）→ Layer 3 审计日志（Story 8.7，高级用户）
- 操作计数器在 MCP 工具层实现，不侵入 service 层逻辑
- 摘要追加到 md 文件末尾，利用 Obsidian 的 callout 折叠机制

### Transparency Layering Principle

| 信息层级 | 可见性 | 内容 | 目的 |
|---|---|---|---|
| 摘要行 | 所有学习者 | 操作计数 + 连接状态 | "系统在工作" |
| 展开详情 | 主动展开 | 操作类型明细 | "做了什么" |
| 审计日志 | 高级用户 | 时间戳 + 延迟 + 状态码 | "排查问题" |
| 原始分数 | 隐藏 | mastery/score/error | "不干扰学习" |

### File Paths
- MCP 操作计数：`backend/app/mcp/tools/` 各工具文件中添加 hook
- 摘要生成：`backend/app/services/observability_service.py`（新建）
- 连接状态：`backend/app/services/graphiti_service.py`（get_connection_status）
- 对话文件追加：skill 结束 hook
- 考察文件追加：exam skill 结束 hook

### Testing
- 单元测试：操作计数器在各种操作组合下正确统计
- 单元测试：摘要文本格式化正确 + 不包含禁止内容（分数/答案）
- 集成测试：完整对话流程后摘要行正确追加

### References
- **From PRD**: §7 Graphiti 读写时序 (line 6275-6627) — 可观测性需求
- FR-OBS-01: 记忆操作摘要
- NFR-OBS: 可观测性非功能需求

## UAT Script

> 1. 开启一次 AI 对话，讨论某个概念
> 2. 对话结束后，看到文件末尾有折叠 callout"记忆操作 · 已加载 N 条记忆 · 已保存 M 条记录 · 🟢 连接正常"
> 3. 展开 callout，看到操作明细（不含分数）
> 4. 开启一次考察并完成，看到 exam_boards/ 文件末尾有同格式摘要
> 5. 断开 Neo4j 服务，重新对话
> 6. 看到摘要中显示"🔴 离线（数据已缓存，恢复后自动同步）"
> 7. 确认摘要中没有暴露任何掌握度分数或评分结果

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 操作计数器 | unit | `pytest tests/unit/test_operation_counter.py -x` | 0 failures |
| 摘要格式化 | unit | `pytest tests/unit/test_summary_format.py -x` | 0 failures |
| 禁止内容检查 | unit | `pytest tests/unit/test_summary_no_scores.py -x` | 0 failures |
| 连接状态读取 | unit | `pytest tests/unit/test_connection_status.py -x` | 0 failures |
| 对话流程集成 | integration | `pytest tests/integration/test_dialog_summary.py -x` | 0 failures |

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
