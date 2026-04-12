---
doc_type: story
story_id: "8.2"
epic_id: "EPIC-8"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 8.2: Vault 内 Graphiti 操作审计日志

## Story

As a 系统,
I want 在 vault 内维护 Graphiti 操作审计日志,
so that 学习者和开发者可以审计所有 Graphiti 交互历史。

## Acceptance Criteria

1. **Given** 任何 Graphiti 读操作（`search_memory_facts`、`get_episodes` 等）发生
   **When** 操作完成（成功或失败）
   **Then** 审计日志追加一条记录到 vault 内 `_system/graphiti-audit.log`
   **And** 记录包含：ISO 8601 时间戳、操作类型 `read`、目标（`fact` 或 `episode`）、延迟（ms）、结果（`success` 或 `fail`）

2. **Given** 任何 Graphiti 写操作（`add_episode`、`add_memory` 等）发生
   **When** 操作完成（成功或失败）
   **Then** 审计日志追加一条记录到 vault 内 `_system/graphiti-audit.log`
   **And** 记录包含：ISO 8601 时间戳、操作类型 `write`、目标、延迟（ms）、结果

3. **Given** `_system/graphiti-audit.log` 文件大小超过 10MB
   **When** 下一条记录即将追加
   **Then** 现有文件重命名为 `graphiti-audit.log.1`（已有 `.1` 则推为 `.2`，最多保留 `.3`）
   **And** 新建空 `graphiti-audit.log` 继续追加

4. **Given** vault 目录 `_system/` 不存在
   **When** 第一条审计记录触发时
   **Then** 系统自动创建 `_system/` 目录和 `graphiti-audit.log` 文件（不报错）

## Tasks / Subtasks

- [ ] Task 1: 设计日志格式与写入器 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/core/audit_log.py` 实现 `GraphitiAuditLogger` 类
  - [ ] 1.2 定义日志行格式（NDJSON，每行一个 JSON 对象）：`{"ts": "2026-04-12T10:23:45.123Z", "op": "write", "target": "episode", "latency_ms": 312, "result": "success", "detail": ""}`
  - [ ] 1.3 实现 `GraphitiAuditLogger.log(op, target, latency_ms, result, detail="")` 异步方法，使用 `aiofiles` 追加写入
  - [ ] 1.4 使用 `asyncio.Lock` 确保并发写入不产生行混乱

- [ ] Task 2: 实现日志轮转 (AC: #3, #4)
  - [ ] 2.1 在每次追加前检查文件大小（`os.path.getsize`），超过 10MB 则触发轮转
  - [ ] 2.2 轮转逻辑：`.3` → 删除，`.2` → `.3`，`.1` → `.2`，当前 → `.1`，新建空文件
  - [ ] 2.3 若 `_system/` 目录不存在，使用 `os.makedirs(exist_ok=True)` 自动创建
  - [ ] 2.4 轮转操作原子性：先写入新文件确认成功后再执行重命名链

- [ ] Task 3: 在 Graphiti 调用点注入审计 (AC: #1, #2)
  - [ ] 3.1 修改 `backend/app/services/graphiti_service.py`：所有写入方法执行后（成功或失败）调用 `audit_logger.log(op="write", ...)`
  - [ ] 3.2 所有读取方法执行后调用 `audit_logger.log(op="read", ...)`
  - [ ] 3.3 `GraphitiAuditLogger` 作为单例注入（`backend/app/core/dependencies.py`），不重复实例化
  - [ ] 3.4 审计写入失败（如磁盘满）不可影响主流程，捕获异常后仅 `structlog.warning`

- [ ] Task 4: Vault 路径配置 (AC: #4)
  - [ ] 4.1 在 `backend/app/core/config.py` 新增 `AUDIT_LOG_PATH: Path`，默认值 `{VAULT_PATH}/_system/graphiti-audit.log`
  - [ ] 4.2 `VAULT_PATH` 从现有 Settings 读取（不新增配置项）
  - [ ] 4.3 验证 `AUDIT_LOG_PATH` 的父目录在应用启动时自动创建（startup event handler）

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 单元测试：`GraphitiAuditLogger.log()` 正常写入一条 NDJSON 记录并可反序列化
  - [ ] 5.2 单元测试：模拟文件 10MB+ 触发轮转，验证 `.1`/`.2`/`.3` 文件名顺序
  - [ ] 5.3 单元测试：`_system/` 目录不存在时自动创建
  - [ ] 5.4 集成测试：Graphiti 写操作后检查日志文件存在且含对应记录
  - [ ] 5.5 并发测试：10 个并发协程同时写入，验证所有行合法 JSON 且无混行

## Dev Notes

- **日志格式选 NDJSON**（Newline-Delimited JSON）而非纯文本：便于 `jq` 解析、Dashboard Dataview 读取以及后续程序化分析
- **`aiofiles` 依赖**：项目是否已安装 `aiofiles`？检查 `backend/pyproject.toml`；未安装则添加到 dependencies
- **NFR-OBS-3 全操作记录**：所有 Graphiti 读写都要记录，不得只记失败
- **NFR-INT-4 本地存储**：日志存储在 vault 内（`_system/` 目录），不上传任何远程服务
- **轮转上限**：最多 `.3`，超出则最老的 `.3` 被删除。总存储上限 ~40MB（4 × 10MB）
- **`_system/` 目录命名**：前缀下划线与 `_templates/` 一致，避免被 Dataview 索引为普通笔记
- **structlog 不用标准 logging**：项目规范（CLAUDE.md 约束）

### Project Structure Notes

- 新建文件：`backend/app/core/audit_log.py`
- 修改文件：`backend/app/core/config.py`（新增 `AUDIT_LOG_PATH`）
- 修改文件：`backend/app/core/dependencies.py`（注入 `GraphitiAuditLogger` 单例）
- 修改文件：`backend/app/services/graphiti_service.py`（注入审计调用）
- 修改文件：`backend/app/main.py`（startup event 创建 `_system/` 目录）
- 测试文件：`backend/tests/unit/test_audit_log.py`、`backend/tests/integration/test_graphiti_audit_integration.py`

### References

- [Source: backend/app/services/graphiti_service.py] — Graphiti 读写方法入口
- [Source: backend/app/core/config.py] — Settings 和 VAULT_PATH 定义
- [Source: _bmad-output/planning-artifacts/epics.md#Story-8.2] — AC 和 FR 映射
- [FR45] vault 内 Graphiti 操作审计日志
- [NFR-OBS-3] 审计日志全操作记录

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证日志文件生成** (AC: #1, #2, #4)
   - 执行任意一次 AI 对话或考察 Skill
   - 打开 Obsidian，在文件树左侧找到 `_system/` 文件夹（如不可见，检查 Obsidian 是否隐藏了下划线目录）
   - 用文本编辑器打开 `_system/graphiti-audit.log`
   - 应看到若干行 JSON，每行包含时间、操作类型、延迟和结果信息
   - 如果文件不存在或内容为空，记录 Story 8.2

2. **验证读写均被记录** (AC: #1, #2)
   - 日志中既应有 `"op": "read"` 的行（对话时 Graphiti 读取记忆），也应有 `"op": "write"` 的行（操作结束时写入 episode）
   - 如果只有一种，记录 Story 8.2

3. **验证轮转** (AC: #3)
   - （开发者测试）将日志文件大小手动设置为 10MB+ 后再触发一次操作
   - 应看到 `graphiti-audit.log.1` 文件出现，且 `graphiti-audit.log` 重置为新的小文件

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-8.2.1 | pytest | `.venv/bin/pytest tests/unit/test_audit_log.py -x -q` | 0 failed |
| CP-8.2.2 | pytest | `.venv/bin/pytest tests/integration/test_graphiti_audit_integration.py -x -q` | 0 failed |
| CP-8.2.3 | script | `python3 scripts/validate_audit_log.py _system/graphiti-audit.log` | "valid NDJSON" in stdout |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-8]]
- PRD: [[PRD14]]
