---
story_id: "1.8"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 6
depends_on: ["1.7"]
blocks: ["1.9", "1.12"]
trace:
  - "FR-SYS-01"
  - "FR-DEPLOY-02"
---

# Story 1.8: Vault Switch Runtime API

Status: ready-for-dev

## Story

As a 学习者,
I want 在不重启后端的情况下切换到不同课程的 vault（如从 CS188 切到 CS61B）,
So that 我可以在 Claudian 中无缝切换学习科目，而不需要改配置文件再重启 Docker。

## 通俗化解释（给学习者）

> **一句话说**: 学不同课时一键切换笔记库，不用关机重开。

**你会遇到的场景**:
- 你上午复习 CS188 AI 课，下午要切到 CS61B 数据结构，现在得改 `.env` 里的路径 → 重启 Docker → 等 2 分钟冷启动
- 你在 Claudian 里聊着 CS188 的搜索算法，突然想看看 CS61B 里链表的笔记，但两个 vault 的数据是分开的
- 你改了 `.env` 但忘了重启，结果后端还在用旧 vault 的数据回答问题，答案驴唇不对马嘴

**这个功能帮你**:
- Claudian 自动检测你在 Obsidian 打开了哪个 vault，后端跟着切换
- 或者你手动调一个 API 说"我要切到 CS61B"，后端立刻生效
- 切换过程中有状态提示（"正在切换到 CS61B vault..."→"切换完成"）

**用个比喻**: 就像电视遥控器换台 — 按一下就从 CCTV1 切到 CCTV6，不用关电视拔线再开。

## Acceptance Criteria

1. **Given** 后端正在运行（当前 vault = CS188）
   **When** 发送 `POST /api/v1/vault/switch` 请求，body = `{"vault_path": "/path/to/CS61B"}`
   **Then** 后端立即切换到 CS61B vault
   **And** `get_settings().CANVAS_BASE_PATH` 返回新路径
   **And** 不需要重启 Docker 容器

2. **Given** vault 切换请求
   **When** 新 vault 路径不存在或不是有效的 Obsidian vault
   **Then** 返回 `400 Bad Request`，body 含 `{"error": "vault_not_found", "detail": "路径不存在或非有效 vault"}`
   **And** 当前 vault 不受影响

3. **Given** vault 切换成功
   **When** 查询 `GET /api/v1/vault/current`
   **Then** 返回当前活跃 vault 信息：`{"vault_path": "...", "vault_name": "CS61B", "switched_at": "..."}`

4. **Given** `@lru_cache` 缓存了旧的 Settings
   **When** vault 切换 API 被调用
   **Then** `get_settings.cache_clear()` 被调用
   **And** 新的 `Settings()` 实例使用更新后的 `CANVAS_BASE_PATH`

5. **Given** Claudian 在 Obsidian 中运行
   **When** 用户在 Obsidian 打开不同 vault
   **Then** Claudian 通过 MCP 自动检测 vault 变化并调用 `POST /api/v1/vault/switch`（MCP tool 由 Story 1.12 实现）

6. **Given** vault 切换过程中
   **When** 有正在进行的 RAG 查询或 KG 写入
   **Then** 当前请求完成后再切换（不中断正在进行的操作）
   **And** 切换期间新请求返回 `503 Service Unavailable` 直到切换完成

7. **Given** vault 切换完成
   **When** 后端重新初始化
   **Then** LanceDB 索引路径更新到新 vault 的命名空间（由 Story 1.9 实现具体隔离）
   **And** 结构化日志记录切换事件：`vault.switched from=CS188 to=CS61B duration_ms=...`

## Tasks / Subtasks

- [ ] Task 1: Vault Switch API 端点 (AC: #1, #2, #3)
  - [ ] 1.1: 创建 `backend/app/api/v1/endpoints/vault.py`，实现 `POST /vault/switch` 和 `GET /vault/current`
  - [ ] 1.2: 请求 schema: `VaultSwitchRequest(vault_path: str)`
  - [ ] 1.3: 响应 schema: `VaultSwitchResponse(vault_path, vault_name, switched_at, previous_vault)`
  - [ ] 1.4: 验证 vault 路径存在且包含 `.obsidian/` 目录（Obsidian vault 标志）
  - [ ] 1.5: 在 `backend/app/api/v1/router.py` 注册新 router

- [ ] Task 2: Settings 热重载机制 (AC: #4)
  - [ ] 2.1: 在 `config.py` 中新增 `reload_settings(overrides: dict)` 函数
  - [ ] 2.2: 调用 `get_settings.cache_clear()` 清除 `@lru_cache`
  - [ ] 2.3: 通过环境变量 `os.environ["CANVAS_BASE_PATH"] = new_path` 注入新值
  - [ ] 2.4: 重新调用 `get_settings()` 让 Pydantic BaseSettings 重新加载

- [ ] Task 3: 切换协调（优雅切换） (AC: #6, #7)
  - [ ] 3.1: 实现 `VaultSwitchCoordinator` 类，管理切换状态（idle / switching / ready）
  - [ ] 3.2: 切换时设置 `is_switching = True`，新请求返回 503
  - [ ] 3.3: 等待当前活跃请求完成（使用 asyncio.Event 或 counter）
  - [ ] 3.4: 切换完成后发出 structlog 事件

- [ ] Task 4: 测试 (AC: #1, #2, #4, #6)
  - [ ] 4.1: `backend/tests/unit/test_vault_switch.py` — 正常切换 + 路径验证 + 缓存清除
  - [ ] 4.2: `backend/tests/unit/test_vault_switch_coordinator.py` — 并发请求期间切换的 503 行为
  - [ ] 4.3: 集成测试：切换后 RAG 查询指向新 vault 数据

## Dev Notes

- **@lru_cache 问题**: `config.py:789-802` 用 `@lru_cache` 缓存 Settings 单例，运行时修改 `.env` **不会**生效。必须调用 `get_settings.cache_clear()` + 修改 `os.environ` + 重新 `get_settings()`
- **R12 [C1] 否定了 restart 方案**: R11 提出的 "改 .env + restart" 被 R12 证伪 — Docker restart 不会重新读取 `.env`（Docker Compose 只在 `up` 时读取），必须走 Runtime API
- **canvas_service.py:714**: 写入 vault 文件用 `open(path, "w")`，切换 vault 后必须确保新路径可写（Story 1.7 已解决 `:ro` 问题）
- **metadata.py:445-599**: vault 索引 API 直接读取 `CANVAS_BASE_PATH` 构建文件列表，切换后需重新扫描
- **Pydantic Settings 热重载**: BaseSettings 不原生支持热重载，通过清除 lru_cache + 修改 os.environ 实现（FastAPI 官方推荐模式）
- **structlog**: 使用 `structlog.get_logger(__name__)` 记录切换事件，禁止标准 `logging`
- **QA 来源**: R12 修正方案（Runtime API 替代 restart）+ 用户批注 L128（Claudian 自动检测 vault）

### Project Structure Notes

- 新建文件: `backend/app/api/v1/endpoints/vault.py`
- 新建文件: `backend/app/services/vault_switch_coordinator.py`
- 修改文件: `backend/app/config.py`（新增 `reload_settings` 函数）
- 修改文件: `backend/app/api/v1/router.py`（注册 vault router）
- 测试文件: `backend/tests/unit/test_vault_switch.py`
- 测试文件: `backend/tests/unit/test_vault_switch_coordinator.py`

### References

- [Source: backend/app/config.py:789-802] — @lru_cache + get_settings()
- [Source: backend/app/services/canvas_service.py:714] — vault 文件写入
- [Source: _bmad-output/research/obsidian-qa-round13-claude-answers-2026-04-16.md] — R12 修正方案
- [Source: _bmad-output/planning-artifacts/prd.md#FR-SYS-01] — 系统配置
- [Source: docs/architecture.md] — 后端架构

## UAT Script

### 【A 层】学习者验收
> 你可以独立完成以下步骤。只需要：Obsidian + Claudian。

1. **验证 vault 切换** (AC: #1, #3)
   - **你要做的**：在 Claudian 中说"帮我看看现在用的是哪个课程的笔记库"
   - **你应该看到**：Claudian 报告当前 vault 信息（如 CS188）
   - **如果不对劲**：记录 Story 1.8 + 你实际看到的情况

2. **验证切换到另一门课** (AC: #1, #5)
   - **你要做的**：在 Obsidian 中打开另一个 vault（如 CS61B），然后在 Claudian 中说"帮我切换到 CS61B"
   - **你应该看到**：弹出授权确认 → 确认后 Claudian 报告"已切换到 CS61B"
   - **如果不对劲**：记录 Story 1.8 + 你实际看到的情况

3. **验证切换后内容正确** (AC: #1, #4)
   - **你要做的**：切换到 CS61B 后，在 Claudian 中问一个 CS61B 的概念问题（如"帮我看看链表的笔记"）
   - **你应该看到**：AI 回答引用的是 CS61B vault 的笔记内容，而非旧 vault 的
   - **如果不对劲**：记录 Story 1.8 + 你实际看到的情况

4. **验证无效路径拒绝** (AC: #2)
   - **你要做的**：在 Claudian 中说"帮我切换到一个不存在的课程目录"
   - **你应该看到**：Claudian 报告"路径不存在或不是有效的 Obsidian vault"，当前 vault 不受影响
   - **如果不对劲**：记录 Story 1.8 + 你实际看到的情况

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.8.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_vault_switch.py -x -q` | 0 failed |
| CP-1.8.2 | pytest | `.venv/bin/pytest backend/tests/unit/test_vault_switch_coordinator.py -x -q` | 0 failed |
| CP-1.8.3 | ruff | `ruff check backend/app/api/v1/endpoints/vault.py backend/app/services/vault_switch_coordinator.py` | exit 0 |
| CP-1.8.4 | curl | `curl -sf http://localhost:8001/api/v1/vault/current` | HTTP 200 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**QA 来源追溯**:
1. **R11 .env + restart 方案**: 被 R12 [C1] 否定 — Docker restart 不重新读 `.env`，必须 Runtime API
2. **R12 修正方案**: Claudian 自动检测 Obsidian 活跃 vault → `POST /vault/switch`（本 Story 实现 API 端，MCP tool 由 1.12 实现）
3. **用户批注 L128**: 确认 Claudian 应自动检测 vault 变化

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
