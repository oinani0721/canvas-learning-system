---
story_id: "2.6"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 8
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-CONV-07"
  - "FR-CONV-09"
---

# Story 2.6: 对话归档与三层消息管理

Status: ready-for-dev

## Story

As a 学习者,
I want 对话结束后自动归档到长期记忆,
So that 历史学习对话可以被检索并用于个人化出题和间隔复习。

## Acceptance Criteria

1. **Given** 对话 session 结束（学习者关闭对话窗口或显式结束）
   **When** 系统调用 `archive_conversation` MCP 工具
   **Then** 会话完整保存到 Graphiti 长期记忆（Hot 层）
   **And** 归档内容包含：session_id / node_id / 全部消息 / 提取的 Tips / 提取的错误 / 引用的补充材料
   **And** 归档同时在本地写入 `outputs/sessions/<date>-<slug>.md` 对话记录文件

2. **Given** 对话消息存储在 Hot 层（0-30 天）
   **When** 消息创建时间超过 30 天
   **Then** 系统自动将消息从 Hot 层迁移到 Warm 层
   **And** Warm 层保留：LLM 生成的对话摘要 + 结构化提取数据（Tips / errors / 关键概念）
   **And** 原始完整消息文本被移除

3. **Given** 对话消息存储在 Warm 层（30-180 天）
   **When** 消息创建时间超过 180 天
   **Then** 系统自动将消息从 Warm 层迁移到 Cold 层
   **And** Cold 层仅保留：结构化提取数据（error_type / tip_text / concept_slugs / session_metadata）
   **And** LLM 摘要也被移除

4. **Given** 归档操作触发
   **When** 系统执行归档
   **Then** 归档异步执行，不阻塞用户操作
   **And** 归档过程通过 `pipeline_token` 链路追踪（从 Step 7 传递的 token）

5. **Given** 单个节点的对话量超过 50K tokens
   **When** 容量触发条件满足
   **Then** 即使消息未满 30 天也触发 Hot→Warm 压缩
   **And** 容量触发在 structlog 中记录为 `capacity_triggered_warm`

6. **Given** Graphiti 写入失败
   **When** `archive_conversation` MCP 调用异常
   **Then** 本地 `outputs/sessions/` 文件写入仍然成功（本地优先）
   **And** 自动重试 3 次后记录 structlog error 并放弃
   **And** 下次对话启动时检查未归档 session 并尝试补归档

## Tasks / Subtasks

- [ ] Task 1: `archive_conversation` MCP 集成到 `/chat_with_context` workflow (AC: #1)
  - [ ] 1.1: 在 skill workflow 的最后一步（Step 7/Step 9）调用 `archive_conversation` MCP 工具
  - [ ] 1.2: 传入 `session_id` / `node_id` / `messages` / `pipeline_token`
  - [ ] 1.3: 后端 `archive_conversation` 实现：将完整会话写入 Graphiti Hot 层（episode 类型）
  - [ ] 1.4: 同时写入本地文件 `outputs/sessions/<YYYY-MM-DD>-<slug>.md`，格式为 markdown 对话记录

- [ ] Task 2: Hot→Warm 层迁移 (AC: #2, #5)
  - [ ] 2.1: 扩展已有 `backend/app/services/conversation_archive.py` 的 Hot→Warm 迁移逻辑
  - [ ] 2.2: 实现 `migrate_hot_to_warm(node_id: str)` 方法：
    - 使用 LLM 对完整对话生成摘要（< 500 tokens）
    - 提取结构化数据：Tips / errors / 关键概念 slugs
    - 更新 Graphiti 中的 episode 状态为 `warm`，替换原始消息为摘要+提取数据
  - [ ] 2.3: 触发条件：消息 `created_at` > 30 天 OR 单节点对话 token 量 > 50K（双触发）
  - [ ] 2.4: 迁移后在 Graphiti 中标记原始消息 `status: archived`（不物理删除）

- [ ] Task 3: Warm→Cold 层迁移 (AC: #3)
  - [ ] 3.1: 实现 `migrate_warm_to_cold(node_id: str)` 方法：
    - 移除 LLM 摘要，仅保留结构化提取数据
    - 更新 episode 状态为 `cold`
  - [ ] 3.2: 触发条件：Warm 层消息 `created_at` > 180 天
  - [ ] 3.3: Cold 层保留字段：`error_type` / `tip_text` / `concept_slugs` / `session_id` / `session_date` / `node_id`

- [ ] Task 4: 定时调度归档迁移 (AC: #2, #3)
  - [ ] 4.1: 在 `backend/app/services/archive_scheduler.py` 中注册每日归档任务
  - [ ] 4.2: 每日凌晨（可配置时间）扫描所有节点，执行 Hot→Warm 和 Warm→Cold 迁移
  - [ ] 4.3: 批量处理：每批最多 10 个节点（`MAX_NODES_PER_BATCH`），避免瞬时负载
  - [ ] 4.4: 迁移任务异步执行，不影响前台服务

- [ ] Task 5: 异步执行与降级处理 (AC: #4, #6)
  - [ ] 5.1: 归档操作使用 `asyncio.create_task` 异步执行，不阻塞 skill 返回
  - [ ] 5.2: Graphiti 写入失败时自动重试（3 次，间隔 2s），参考 `memory_service.py` 的重试模式
  - [ ] 5.3: 记录未归档 session 到本地队列文件 `outputs/.archive_queue.json`
  - [ ] 5.4: 下次对话启动时检查队列，尝试补归档

- [ ] Task 6: 测试 (AC: #1~#6)
  - [ ] 6.1: 单元测试 `archive_conversation`：完整归档到 Hot 层 + 本地文件写入
  - [ ] 6.2: 单元测试 Hot→Warm 迁移：摘要生成、结构化提取、状态更新
  - [ ] 6.3: 单元测试 Warm→Cold 迁移：摘要移除、仅保留结构化数据
  - [ ] 6.4: 单元测试容量触发：50K tokens 阈值触发提前迁移
  - [ ] 6.5: 集成测试：完整对话 → 归档 → 模拟 30 天后 → Hot→Warm → 模拟 180 天后 → Warm→Cold

## Dev Notes

- **已有 conversation_archive.py**: `backend/app/services/conversation_archive.py` 已实现 Hot-Warm-Cold 三层模型（Story 3.8），包含 `ArchiveTier` 枚举、常量定义（HOT_TO_WARM_DAYS=30, WARM_TO_COLD_DAYS=180, CAPACITY_THRESHOLD_TOKENS=50000）。本 Story 需将其集成到 `/chat_with_context` workflow 并完善迁移调度
- **已有 archive_scheduler.py**: `backend/app/services/archive_scheduler.py` 已存在，需确认其调度逻辑是否完整
- **Anchor PRD 引用**: §4.1 Step 7 archive_conversation (line 3685-3692)，§7.1 MCP 工具表 #12 (line 6178)
- **本地文件格式**: `outputs/sessions/<date>-<slug>.md` 包含 YAML frontmatter（session_id / node_id / date / message_count）+ markdown 格式对话记录
- **消息不物理删除**: Hot→Warm 迁移时标记 `status: archived`，不删除原始数据（数据完整性保证）

### Project Structure Notes

```
backend/app/services/
  conversation_archive.py         # 已有：扩展迁移逻辑
  archive_scheduler.py            # 已有：确认/扩展每日调度
backend/tests/unit/
  test_conversation_archive_3tier.py  # 新增
backend/tests/integration/
  test_archive_lifecycle.py           # 新增
```

### References

- Anchor PRD §4.1 archive_conversation: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3685-3692)
- Anchor PRD §7.1 MCP #12 archive_conversation: (line 6178)
- 已有 conversation_archive.py: `backend/app/services/conversation_archive.py`
- 已有 archive_scheduler.py: `backend/app/services/archive_scheduler.py`
- NFR 降级 — 记忆写入失败: BMAD PRD (line 567)

## UAT Script

> 1. 打开 `wiki/concepts/admissibility.md`，启动 AI 对话
> 2. 进行 3-5 轮有意义的对话
> 3. 结束对话（关闭窗口）
> 4. 检查 `outputs/sessions/` 目录，验证新增了 `<today>-admissibility.md` 文件
> 5. 打开该文件，验证包含完整对话记录
> 6. 检查后端日志，验证 Graphiti 归档成功（或降级重试记录）

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| Hot 层归档 | unit | `pytest tests/unit/test_conversation_archive_3tier.py::test_archive_to_hot -x` | Graphiti + 本地文件 |
| Hot→Warm 迁移 | unit | `pytest tests/unit/test_conversation_archive_3tier.py::test_hot_to_warm -x` | 摘要生成 + 状态更新 |
| Warm→Cold 迁移 | unit | `pytest tests/unit/test_conversation_archive_3tier.py::test_warm_to_cold -x` | 仅保留结构化数据 |
| 容量触发 | unit | `pytest tests/unit/test_conversation_archive_3tier.py::test_capacity_trigger -x` | 50K 阈值触发 |
| 生命周期 | integration | `pytest tests/integration/test_archive_lifecycle.py -x` | Hot→Warm→Cold 完整 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
