---
story_id: "1.11"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 3
depends_on: ["1.7"]
blocks: []
trace:
  - "FR-SYS-01"
  - "FR-OPS-02"
---

# Story 1.11: 配置统一 + 漂移防护

Status: ready-for-dev

## Story

As a 开发者,
I want 配置值有唯一真相源（根 `.env`），系统能检测到配置漂移并提前警告,
So that 我不会因为根 `.env`、`backend/.env`、Docker env 三处配置不一致而花半天排查连接不上的 bug。

## 通俗化解释（给学习者）

> **一句话说**: 系统帮你盯着各处的配置是否一致，不一致就提前报警，不用你自己一个个对比。

**你会遇到的场景**:
- 你在根 `.env` 改了 Neo4j 密码，但忘了同步到 `backend/.env`，后端连不上数据库
- Docker Compose 里的 `NEO4J_PASSWORD=password` 和 `backend/.env` 里的 `NEO4J_PASSWORD=mypass123` 不一样，你排查了一小时才发现
- 你升级了端口号但只改了一处，另一处还是旧的，偶尔正常偶尔报错

**这个功能帮你**:
- 启动时自动检测三处配置源（根 .env / backend/.env / Docker env）是否一致
- 发现不一致时直接告诉你"NEO4J_PASSWORD 在根 .env 是 A，在 backend/.env 是 B，请修正"
- 提供一键同步命令，从根 .env 覆盖到 backend/.env

**用个比喻**: 就像银行对账 — 如果你的记账本和银行流水对不上，系统立刻标红告诉你哪笔不对，而不是等你月底发现钱少了。

## Acceptance Criteria

1. **Given** 后端启动
   **When** `config.py` 加载配置
   **Then** 按优先级读取：环境变量 > 根 `.env` > `backend/.env`（Pydantic Settings 原生行为）
   **And** 日志记录最终生效的配置源

2. **Given** 根 `.env` 存在（Story 1.7 创建）
   **When** `backend/.env` 中的 `NEO4J_PASSWORD` 与根 `.env` 不同
   **Then** 启动时 structlog 发出 `WARNING` 级别日志：`config.drift_detected key=NEO4J_PASSWORD root_value=*** backend_value=*** effective=***`
   **And** 不阻止启动（只警告，不报错）

3. **Given** 配置漂移检测
   **When** 调用 `GET /api/v1/system/config-check`
   **Then** 返回所有共享变量的对比结果：`{"drifts": [{"key": "NEO4J_PASSWORD", "root": "***", "backend": "***", "effective": "***"}], "synced": ["CORS_ORIGINS", ...]}`
   **And** 密码类变量值脱敏显示（只显示前 2 + 后 2 字符）

4. **Given** 检测到配置漂移
   **When** 运行 `scripts/sync-env.sh`
   **Then** 根 `.env` 中的共享变量覆盖 `backend/.env` 中的同名变量
   **And** backend 独有变量保留不变
   **And** 操作前备份 `backend/.env.backup.{timestamp}`

5. **Given** Pydantic BaseSettings 加载
   **When** `backend/.env` 使用 `load_dotenv` 和 `SettingsConfigDict(env_file=".env")`
   **Then** 明确文档化加载顺序和覆盖规则
   **And** `config.py` 中的注释说明：根 .env 为唯一真相源

## Tasks / Subtasks

- [ ] Task 1: 配置漂移检测 (AC: #1, #2)
  - [ ] 1.1: 在 `config.py` 中新增 `detect_config_drift() -> List[ConfigDrift]` 函数
  - [ ] 1.2: 比较根 `.env`（`../../.env` 相对 backend/）和 `backend/.env` 的共享变量
  - [ ] 1.3: 在 Settings `__init__` 后自动调用，结果写入 structlog WARNING
  - [ ] 1.4: 定义共享变量白名单：`NEO4J_USER`, `NEO4J_PASSWORD`, `CANVAS_BASE_PATH`, `OLLAMA_HOST`, `CORS_ORIGINS`

- [ ] Task 2: 配置检查 API (AC: #3)
  - [ ] 2.1: 在 `system.py` 端点中新增 `GET /system/config-check`
  - [ ] 2.2: 返回漂移列表 + 已同步列表
  - [ ] 2.3: 密码类变量脱敏（`mask_sensitive(value) -> str`）

- [ ] Task 3: 同步脚本 (AC: #4)
  - [ ] 3.1: 创建 `scripts/sync-env.sh`
  - [ ] 3.2: 读取根 `.env` 的共享变量，写入 `backend/.env`（保留 backend 独有变量）
  - [ ] 3.3: 执行前自动备份

- [ ] Task 4: 测试 (AC: #1, #2, #3)
  - [ ] 4.1: `backend/tests/unit/test_config_drift.py` — 漂移检测 + 脱敏 + 白名单
  - [ ] 4.2: 无漂移时返回空列表
  - [ ] 4.3: 根 .env 不存在时优雅降级（不报错，记日志）

## Dev Notes

- **三源冲突**: R12 [I3] 记录 — root `.env`（Story 1.7 新建）/ `backend/.env`（已有）/ Docker Compose `environment:` 三处可能配置同一变量
- **Pydantic Settings 加载顺序**: 环境变量 > init 参数 > `.env` 文件 > 默认值。`SettingsConfigDict(env_file=".env")` 读取的是**相对于 CWD** 的文件
- **config.py 现状**: `config.py:782-784` 使用 `SettingsConfigDict(env_file=".env")`，当 CWD = `backend/` 时读 `backend/.env`，不会自动读根 `.env`
- **load_dotenv**: 如果代码中同时有 `load_dotenv("../../.env")` + Pydantic `env_file=".env"`，加载顺序需要明确文档化
- **密码脱敏**: `NEO4J_PASSWORD=mySecretPwd` → 显示为 `my*****wd`
- **structlog**: 使用 `structlog.get_logger(__name__)` + `logger.warning("config.drift_detected", key=..., ...)`
- **QA 来源**: R12 [I3]（配置漂移 3 源冲突）+ R10 Gotcha 4（NEO4J_PASSWORD 不一致）

### Project Structure Notes

- 修改文件: `backend/app/config.py`（新增漂移检测函数）
- 新建文件: `scripts/sync-env.sh`
- 修改文件: `backend/app/api/v1/endpoints/system.py`（新增 config-check 端点）
- 测试文件: `backend/tests/unit/test_config_drift.py`

### References

- [Source: backend/app/config.py:782-784] — BaseSettings + env_file 配置
- [Source: backend/.env] — 现有后端配置文件
- [Source: docker-compose.yml:145-153] — Docker Compose 环境变量
- [Source: _bmad-output/research/obsidian-qa-round13-claude-answers-2026-04-16.md] — R12 [I3]

## UAT Script

### 【B 层】双角色验收

#### 开发者执行（需命令行）

1. **[开发者] 验证漂移检测** (AC: #2)
   - 故意在 `backend/.env` 中把 `NEO4J_PASSWORD` 改成跟根 `.env` 不一样的值
   - 重启后端，确认启动时有 WARNING 提示配置不一致（不阻止启动）

2. **[开发者] 验证同步脚本** (AC: #4)
   - 运行 `scripts/sync-env.sh`
   - 确认 `backend/.env` 的共享变量已与根 `.env` 同步
   - 确认 `backend/.env.backup.*` 备份文件已生成

3. **[开发者] 验证配置一致时无警告** (AC: #1)
   - 确保配置同步后重启，不再有漂移警告

#### 学习者确认（开发者完成后）

4. **[学习者确认] 系统正常运行**
   - **你要做的**：开发者完成配置统一后，打开 Obsidian，在 Claudian 中正常对话
   - **你应该看到**：AI 对话、笔记检索等功能全部正常，不出现连接错误
   - **如果不对劲**：记录 Story 1.11 + 你实际看到的情况

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.11.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_config_drift.py -x -q` | 0 failed |
| CP-1.11.2 | shellcheck | `shellcheck scripts/sync-env.sh` | exit 0 |
| CP-1.11.3 | ruff | `ruff check backend/app/config.py` | exit 0 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**QA 来源追溯**:
1. **R12 [I3]**: 承认配置漂移 3 源冲突问题 — root .env / backend/.env / Docker env 可能不一致
2. **R10 Gotcha 4**: NEO4J_PASSWORD 不一致 — docker-compose 和 backend/.env 写了不同密码

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
