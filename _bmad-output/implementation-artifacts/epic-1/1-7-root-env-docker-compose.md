---
story_id: "1.7"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 4
depends_on: []
blocks: ["1.8", "1.10", "1.11", "1.13"]
trace:
  - "FR-SYS-01"
  - "FR-DEPLOY-01"
---

# Story 1.7: 根 .env + Docker Compose 变量化

Status: review

## Story

As a 开发者/部署者,
I want 项目根目录有统一的 `.env` 文件，Docker Compose 中所有硬编码值都用环境变量替换,
So that 我在不同机器上部署时只需改一个文件，而不是在 docker-compose.yml、backend/.env 和 Docker env 之间反复同步。

## 通俗化解释（给学习者）

> **一句话说**: 把散落在各处的"密码、路径、端口号"集中到一张纸上管理，不用到处找、到处改。

**你会遇到的场景**:
- 你想在新电脑上跑 Canvas，发现密码写死在 docker-compose.yml 里，改了 yml 但 backend/.env 里还是旧密码，两边对不上
- 你同学想试用你的项目，但 vault 路径硬编码了你的 Mac 用户名 `/Users/Heishing/...`，他改了半天还跑不起来
- 你升级 Neo4j 端口，docker-compose.yml 里改了 7691 但 backend/.env 里还是 7687，服务连不上

**这个功能帮你**:
- 所有可配置值集中到根目录 `.env`，只改一处，docker-compose + 后端全部生效
- 新用户 clone 后复制 `.env.example` → `.env`，填入自己的路径和密码就能启动
- 端口、密码、路径这些值不会在多个文件里"漂移"

**用个比喻**: 就像家里只有一个总电闸控制所有房间，而不是每个房间一个开关还互相打架。

## Acceptance Criteria

1. **Given** 项目根目录
   **When** 检查文件列表
   **Then** 存在 `.env.example` 文件，包含所有必需变量的模板（带注释说明）
   **And** `.env` 已加入 `.gitignore`
   **And** `.env.example` 包含以下变量组：`NEO4J_USER`、`NEO4J_PASSWORD`、`CANVAS_BASE_PATH`、`OLLAMA_HOST`、`CORS_ORIGINS`、`API_PORT`

2. **Given** 根 `.env` 文件已配置
   **When** 运行 `docker-compose up`
   **Then** docker-compose.yml 通过 `${VAR:-default}` 语法读取所有变量
   **And** 不再有任何硬编码的密码、路径或端口号

3. **Given** docker-compose.yml 中 backend 服务的 vault 挂载
   **When** 检查 volumes 配置
   **Then** vault 路径使用 `${CANVAS_BASE_PATH}` 变量
   **And** 移除硬编码的 `/Users/Heishing/Desktop/spring course 2026/CS188:/app/vault/CS188:ro`
   **And** `:ro` 只读标志根据 `VAULT_READONLY` 变量决定（默认 `rw`，因后端需写入 frontmatter）

4. **Given** docker-compose.yml 中 Neo4j 服务
   **When** 检查 environment 配置
   **Then** `NEO4J_AUTH` 使用 `${NEO4J_USER}/${NEO4J_PASSWORD}` 语法
   **And** 端口映射使用 `${NEO4J_HTTP_PORT:-7478}:7474` 和 `${NEO4J_BOLT_PORT:-7691}:7687`

5. **Given** `backend/.env` 文件
   **When** 与根 `.env` 对比同名变量
   **Then** `backend/.env` 中的 `NEO4J_*`、`CANVAS_BASE_PATH` 等共享变量值与根 `.env` 一致
   **And** 文档说明根 `.env` 为唯一真相源

6. **Given** 新用户 clone 项目
   **When** 按 README 步骤操作
   **Then** 只需 `cp .env.example .env` + 编辑 + `docker-compose up` 即可启动
   **And** 无需手动编辑 docker-compose.yml 或 backend/.env

## Tasks / Subtasks

- [x] Task 1: 创建根 `.env.example` 模板 (AC: #1)
  - [x] 1.1: 从 docker-compose.yml 和 backend/.env 提取所有可配置变量
  - [x] 1.2: 按功能分组（Neo4j / Ollama / Canvas / API / CORS），每组加注释说明
  - [x] 1.3: 确认 `.env` 在 `.gitignore` 中（根目录和 backend/ 级别都检查）
  - [x] 1.4: 提供安全的默认值（密码不设默认，端口设默认）

- [x] Task 2: Docker Compose 变量化改造 (AC: #2, #3, #4)
  - [x] 2.1: Neo4j 服务 — `NEO4J_AUTH`、端口映射、内存配置全部变量化
  - [x] 2.2: Backend 服务 — `NEO4J_URI`、`OLLAMA_HOST`、`CANVAS_BASE_PATH`、`CORS_ORIGINS` 变量化
  - [x] 2.3: 移除 vault 挂载中硬编码的用户路径，改为 `${CANVAS_BASE_PATH}:/app/vault`
  - [x] 2.4: `:ro` 标志改为条件化（`canvas_service.py:714` 需写入 vault 文件，`:ro` 会导致写冲突）
  - [x] 2.5: 保留 `cliproxyapi-network` external 配置（Story 1.13 处理条件化）

- [x] Task 3: Backend `.env` 同步说明 (AC: #5, #6)
  - [x] 3.1: 在 `backend/.env` 顶部添加注释说明根 `.env` 为真相源
  - [x] 3.2: 共享变量用 `# Synced from root .env` 标记
  - [x] 3.3: 更新 README 的"快速开始"部分

- [x] Task 4: 验证脚本 (AC: #1, #2)
  - [x] 4.1: 创建 `scripts/validate-env.sh` 检查必需变量是否已设置
  - [x] 4.2: 输出缺失变量名 + 对应的 `.env.example` 注释
  - [x] 4.3: docker-compose config 验证（确保变量替换后 YAML 合法）

## Dev Notes

- **硬编码位置清单**:
  - `docker-compose.yml:25`: `NEO4J_AUTH=${NEO4J_USER:-neo4j}/${NEO4J_PASSWORD:-password}` — 已用变量但默认值 `password` 不安全
  - `docker-compose.yml:150`: `CANVAS_BASE_PATH=/app/vault` — 容器内路径，OK
  - `docker-compose.yml:162-163`: `/Users/Heishing/...:/app/vault/CS188:ro` — **硬编码用户路径 + :ro 写冲突**
  - `backend/.env:25`: `CANVAS_BASE_PATH="/Users/Heishing/..."` — 硬编码用户路径
  - `backend/app/config.py:138`: `CANVAS_BASE_PATH` 默认值也用了绝对路径
- **:ro 写冲突**: `canvas_service.py:714` 通过 `open(canvas_path, "w")` 写入 vault 文件，但 docker-compose 挂载了 `:ro`，会导致 `OSError: Read-only file system`
- **config.py @lru_cache**: `config.py:789` 用 `@lru_cache` 缓存 `get_settings()`，运行时修改 `.env` 不会生效（需 Story 1.8 Runtime API 解决）
- **Docker Compose 变量语法**: 使用 `${VAR:-default}` 而非 `${VAR-default}`（前者在变量为空字符串时也用默认值）
- **QA 来源**: R10 Gotcha 1（vault 路径硬编码）+ R12 [C1]（restart 不刷新 env）+ R12 [I3]（配置漂移 3 源冲突）

### Project Structure Notes

- 新建文件: `.env.example`（根目录）
- 新建文件: `scripts/validate-env.sh`
- 修改文件: `docker-compose.yml`（变量化改造）
- 修改文件: `backend/.env`（添加同步说明注释）
- 修改文件: `.gitignore`（确认 `.env` 已排除）
- 修改文件: `README.md`（快速开始步骤更新）

### References

- [Source: docker-compose.yml:25,150,162-163] — 硬编码值位置
- [Source: backend/.env] — 现有后端配置
- [Source: backend/app/config.py:138,789] — BaseSettings + @lru_cache
- [Source: canvas_service.py:714] — vault 写入导致 :ro 冲突
- [Source: _bmad-output/research/obsidian-qa-round13-claude-answers-2026-04-16.md] — QA 映射

## UAT Script

### 【B 层】双角色验收

#### 开发者执行（需命令行）

1. **[开发者] 验证 .env.example 存在** (AC: #1)
   - 打开项目根目录，应看到 `.env.example` 文件
   - 打开文件，应看到分组的变量模板和中文注释
   - 确认 `.env` 文件不在 Git 版本控制中

2. **[开发者] 验证 Docker 启动** (AC: #2, #6)
   - 复制 `.env.example` 为 `.env`，填入密码和 vault 路径
   - 运行 `docker-compose up -d`，所有服务应正常启动
   - 不需要手动修改 `docker-compose.yml`

3. **[开发者] 验证变量替换** (AC: #3, #4)
   - 运行 `docker-compose config`，输出中不应有 `${...}` 未替换的变量
   - 检查 Neo4j 密码已正确传入

4. **[开发者] 验证 vault 可写** (AC: #3)
   - 确认 vault 挂载不再是只读（`:ro` 已移除或条件化）

#### 学习者确认（开发者完成后）

5. **[学习者确认] 系统正常运行**
   - **你要做的**：开发者告诉你"系统已配置好"后，打开 Obsidian，在 Claudian 中说"帮我检查系统状态"
   - **你应该看到**：Claudian 报告所有组件正常运行
   - **如果不对劲**：记录 Story 1.7 + 你实际看到的情况

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.7.1 | shellcheck | `shellcheck scripts/validate-env.sh` | exit 0 |
| CP-1.7.2 | docker | `docker-compose config --quiet` | exit 0（YAML 合法） |
| CP-1.7.3 | grep | `grep -c 'CANVAS_BASE_PATH' .env.example` | ≥ 1 |
| CP-1.7.4 | grep | `! grep -P '/Users/\w+/' docker-compose.yml` | exit 0（无硬编码用户路径） |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**QA 来源追溯**:
1. **R10 Gotcha 1**: vault 路径 `/Users/Heishing/...` 硬编码在 docker-compose.yml，新用户无法使用
2. **R12 [C1]**: restart 不刷新 env — 本 Story 只解决静态配置统一，动态刷新由 Story 1.8 解决
3. **R12 [I3]**: 配置漂移 3 源冲突（root .env / backend/.env / Docker env）— 本 Story 建立根 .env 为唯一真相源

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (1M context) via Claude Code CLI

### Debug Log References
- TDD red-green-refactor cycle: 13/13 tests pass
- Automated checkpoints: CP-1.7.3 PASS, CP-1.7.4 PASS
- CP-1.7.1 (shellcheck): SKIP (not installed locally, non-blocking)

### Completion Notes List
- Task 1: Created root `.env.example` with 5 variable groups (Neo4j/Ollama/Canvas/API/Dev), Chinese comments, safe defaults (no default for passwords, sensible defaults for ports)
- Task 2: Variable-ized docker-compose.yml — replaced 2 hardcoded `/Users/Heishing/...` vault mounts with single `${CANVAS_BASE_PATH}:/app/vault:${VAULT_MOUNT_MODE:-rw}`, Neo4j ports now `${NEO4J_HTTP_PORT:-7478}:7474` and `${NEO4J_BOLT_PORT:-7691}:7687`, backend env vars (OLLAMA_HOST, CORS_ORIGINS, DEBUG, API_PORT) all variable-ized
- Task 3: Added sync header to backend/.env + `# Synced from root .env` markers on shared variables (NEO4J_USER/PASSWORD/URI, CORS_ORIGINS, CANVAS_BASE_PATH, OLLAMA_HOST). Updated README Docker deployment section with new 3-step quickstart.
- Task 4: Created `scripts/validate-env.sh` — checks .env existence, required vars (NEO4J_PASSWORD, CANVAS_BASE_PATH), optional vars with defaults, CANVAS_BASE_PATH directory validation, docker-compose config validation

### Change Log
- 2026-04-17: Story 1.7 implementation complete — root .env centralization + docker-compose variable-ization + validate-env.sh

### File List
- NEW: `.env.example` — root environment variable template
- NEW: `scripts/validate-env.sh` — environment validation script
- NEW: `backend/tests/unit/test_story_1_7_env_config.py` — 13 TDD validation tests
- MOD: `docker-compose.yml` — variable-ized all hardcoded values (ports, paths, env vars)
- MOD: `backend/.env` — added sync header + shared variable markers
- MOD: `README.md` — updated Docker deployment quickstart section
- MOD: `_bmad-output/implementation-artifacts/sprint-status.yaml` — story status in-progress → review
- MOD: `_bmad-output/implementation-artifacts/epic-1/1-7-root-env-docker-compose.md` — tasks marked [x]
