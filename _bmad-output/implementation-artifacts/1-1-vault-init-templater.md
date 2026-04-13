---
doc_type: story
story_id: "1.1"
aliases: ["1.1"]
epic_id: "EPIC-1"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 4
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 1.1: Vault 初始化与 Templater 标准模板

## Story

As a 学习者,
I want 在 Obsidian vault 中自动生成标准 frontmatter 模板（含掌握度、BKT 参数、FSRS 参数等字段）,
so that 每个新建笔记都有统一的元数据结构供系统读写。

## Acceptance Criteria

1. **Given** 学习者安装了 Templater 插件并配置了模板目录
   **When** 学习者在 vault 中创建新笔记
   **Then** Templater 自动注入标准 frontmatter（含 mastery_score、bkt_params、fsrs_params、error_history 等字段）
   **And** frontmatter 字段符合 PRD §4 定义的 schema

2. **Given** 学习者编辑已有笔记
   **When** 笔记缺少必要 frontmatter 字段
   **Then** 系统不自动补全（只对新笔记生效，避免意外覆盖）

3. **Given** 后端服务启动
   **When** Docker 编排执行
   **Then** 按顺序就绪：Neo4j → Ollama(bge-m3) → FastAPI → MCP 连接
   **And** 前一服务未就绪时后续服务等待（不跳过）
   **And** 全部就绪后系统标记为可用

## Tasks / Subtasks

- [ ] Task 1: 创建 Templater frontmatter 模板 (AC: #1)
  - [ ] 1.1 在 vault 模板目录创建 `_templates/note-template.md`
  - [ ] 1.2 定义标准 frontmatter schema：mastery_score(0.0), bkt_params(p_know/p_guess/p_slip/p_transit), fsrs_params(difficulty/stability/retrievability/due_date), error_history([]), confidence_level(""), last_reviewed(null), created_at(tp.date.now)
  - [ ] 1.3 配置 Templater 使用 `tp.date.now()` 自动填充创建时间
  - [ ] 1.4 编写 Templater 执行脚本确保模板只在新文件创建时触发

- [ ] Task 2: Templater 插件配置 (AC: #1, #2)
  - [ ] 2.1 配置 Templater Settings → Template Folder Location → `_templates/`
  - [ ] 2.2 启用 "Trigger Templater on new file creation"
  - [ ] 2.3 验证不对已有文件自动注入（Templater 默认行为 — 只新建时触发）
  - [ ] 2.4 创建文档说明 Templater 配置步骤（供 setup wizard 引用）

- [ ] Task 3: 验证 Docker 启动顺序 (AC: #3)
  - [ ] 3.1 确认 docker-compose.yml 中 backend depends_on neo4j(service_healthy) 已配置
  - [ ] 3.2 确认 Mac 环境 Ollama native 启动在 Docker 之前（文档化启动步骤）
  - [ ] 3.3 验证 backend healthcheck endpoint `/api/v1/health` 返回所有依赖状态
  - [ ] 3.4 编写启动脚本 `scripts/start.sh`：检查 Ollama → docker-compose up → 等待 backend healthy

- [ ] Task 4: 编写测试 (AC: #1, #2, #3)
  - [ ] 4.1 后端测试：验证 /api/v1/health 返回正确的服务状态 JSON
  - [ ] 4.2 集成测试：验证 Docker 启动后 Neo4j bolt 连接可达
  - [ ] 4.3 模板验证脚本：检查模板 frontmatter 字段完整性

## Dev Notes

- **Docker 启动顺序已基本就位**：docker-compose.yml 已配置 `depends_on: neo4j: condition: service_healthy`，backend healthcheck 用 `curl -sf http://localhost:8001/api/v1/health`
- **Mac 上 Ollama 是 native 运行**（非 Docker）：通过 `host.docker.internal:11434` 连接。Docker 内的 ollama 服务仅用于 Windows/Linux（profile: windows）
- **Neo4j 端口**：7691 (bolt) / 7478 (browser)，与其他 Neo4j 实例（7474/7687/7689）隔离
- **Templater 模板目录约定**：`_templates/` 前缀下划线确保不被 Dataview 索引
- **frontmatter 安全**：NFR-INT-1 要求 Skill 异常不可损坏 frontmatter。模板设计时字段用安全默认值

### Project Structure Notes

- 模板文件：`vault/_templates/note-template.md`（vault 内，非项目根目录）
- 启动脚本：`scripts/start.sh`
- Docker 配置：`docker-compose.yml`（已存在，验证+微调即可）
- 后端健康检查：`backend/app/api/v1/endpoints/health.py`（已存在）

### References

- [Source: docker-compose.yml#services] — Docker 服务定义和依赖关系
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — frontmatter 字段完整定义
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.1] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#§4] — frontmatter schema 定义

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证 Templater 自动注入** (AC: #1)
   - 打开 Obsidian
   - 按 Ctrl/Cmd+N 创建一个新笔记
   - 在笔记顶部应该看到一段被 `---` 包裹的元数据区域
   - 元数据中应包含 `mastery_score: 0.0`、`created_at: 今天日期` 等字段
   - 如果没看到这段元数据，记录 Story 1.1 和实际看到的内容

2. **验证已有笔记不被修改** (AC: #2)
   - 打开 vault 中一个已有的笔记（没有元数据区域的旧笔记）
   - 编辑笔记内容（随意加一个字）
   - 保存后检查：笔记顶部应该**没有**自动出现元数据区域
   - 如果旧笔记被自动加了元数据，记录 Story 1.1 和笔记名称

3. **验证系统启动** (AC: #3)
   - 双击桌面上的启动脚本（或在终端运行 `bash scripts/start.sh`）
   - 等待约 1 分钟
   - 打开浏览器访问 `http://localhost:8001/api/v1/health`
   - 应该看到一个 JSON 页面显示所有服务状态为 "healthy" 或 "ok"
   - 如果页面打不开或显示错误，记录 Story 1.1 和错误信息

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.1.1 | pytest | `.venv/bin/pytest tests/unit/test_health.py -x -q` | 0 failed |
| CP-1.1.2 | pytest | `.venv/bin/pytest tests/integration/test_docker_startup.py -x -q` | 0 failed |
| CP-1.1.3 | script | `python3 scripts/validate_template.py _templates/note-template.md` | "valid" in stdout |

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

- EPIC: [[EPIC-1]]
- PRD: [[PRD14]]
