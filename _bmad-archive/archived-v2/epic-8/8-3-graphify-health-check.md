---
doc_type: story
story_id: "8.3"
aliases: ["8.3"]
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
# Story 8.3: Graphify Health Check

## Story

As a 学习者,
I want 执行 Graphify health check 确认知识图谱状态正常,
so that 我可以确认 Graphify 索引没有损坏且是最新的。

## Acceptance Criteria

1. **Given** 学习者触发 Graphify health check 命令（MCP 工具 `/graphify_health` 或后端 API）
   **When** 系统执行检查
   **Then** 报告 `graph.json` 最后更新时间、节点数、边数、vault 笔记总数 vs 已索引数

2. **Given** 存在尚未被 Graphify 索引的笔记文件
   **When** health check 完成
   **Then** 报告中列出未索引文件的文件名列表（每行一个）

3. **Given** `graph.json` 文件损坏（JSON 解析失败或 schema 不符）
   **When** health check 执行时
   **Then** 报告错误："graph.json is corrupted"，并附上建议操作："Run `/graphify_rebuild` to recreate the index"
   **And** 系统不崩溃，正常返回结构化错误响应

4. **Given** Graphify 整体失败（`graph.json` 不存在或服务异常）
   **When** 系统检测到降级条件
   **Then** 自动退回到读 frontmatter + wikilinks 模式（NFR-DEG-4）
   **And** health check 结果中标注 `"degraded": true`

## Tasks / Subtasks

- [ ] Task 1: 实现 Graphify health check 核心逻辑 (AC: #1, #2, #3)
  - [ ] 1.1 在 `backend/app/services/graphify_service.py` 实现 `health_check() -> GraphifyHealthReport` 方法
  - [ ] 1.2 定义 `GraphifyHealthReport` Pydantic 模型：`last_updated: datetime | None`、`node_count: int`、`edge_count: int`、`total_notes: int`、`indexed_notes: int`、`unindexed_files: list[str]`、`corrupted: bool`、`degraded: bool`、`error_message: str | None`
  - [ ] 1.3 读取 `graph.json`：尝试 JSON 解析，失败则设 `corrupted=True`，并生成重建建议
  - [ ] 1.4 统计 vault 中 `.md` 文件数（排除 `_templates/`、`_system/` 等下划线目录）
  - [ ] 1.5 对比 `graph.json` 中的已索引文件列表与实际 vault 文件，输出未索引列表
  - [ ] 1.6 从 `graph.json` 元数据中读取节点数、边数、最后更新时间

- [ ] Task 2: 降级检测与处理 (AC: #4)
  - [ ] 2.1 若 `graph.json` 不存在，设 `degraded=True`，写入 structlog warning
  - [ ] 2.2 降级时触发 `GraphifyFallbackService.use_frontmatter_wikilinks()`（已有服务，此处集成调用）
  - [ ] 2.3 health check 响应中 `degraded=True` 时，在报告顶部标注："⚠ Graphify degraded: using frontmatter + wikilinks fallback"
  - [ ] 2.4 降级不影响 health check 结果的返回，始终返回结构化 JSON

- [ ] Task 3: 暴露 MCP 工具和 API 端点 (AC: #1)
  - [ ] 3.1 在 `backend/app/api/v1/endpoints/health.py` 新增 `GET /api/v1/graphify/health` 端点，返回 `GraphifyHealthReport`
  - [ ] 3.2 在 MCP 工具定义文件中注册 `graphify_health` 工具，调用 `GET /api/v1/graphify/health`
  - [ ] 3.3 工具描述文本：`"执行 Graphify 知识图谱健康检查，返回索引状态、节点/边数量及未索引笔记列表"`
  - [ ] 3.4 验证 `/api/v1/health` 主健康端点（已有）中包含 Graphify 子状态（`graphify: ok/degraded`）

- [ ] Task 4: 格式化输出（学习者可读报告） (AC: #1, #2, #3)
  - [ ] 4.1 在前端/Claudian 端将 `GraphifyHealthReport` 格式化为可读文本：
    ```
    Graphify Index Status
    Last updated: 2026-04-12 10:23
    Nodes: 142  Edges: 89
    Coverage: 38/40 notes indexed
    Unindexed: ProjectA.md, Ch5-Summary.md
    ```
  - [ ] 4.2 损坏时追加红色警告文本（Claudian 支持 ANSI 颜色）
  - [ ] 4.3 降级时追加黄色提示文本

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 单元测试：`health_check()` 在 `graph.json` 正常时返回正确节点数/边数
  - [ ] 5.2 单元测试：`graph.json` 损坏时设 `corrupted=True`，含 rebuild 建议
  - [ ] 5.3 单元测试：`graph.json` 不存在时设 `degraded=True`
  - [ ] 5.4 单元测试：未索引文件列表正确（vault 有 40 个文件，graph.json 记录 38 个，unindexed 应为 2 个）
  - [ ] 5.5 集成测试：`GET /api/v1/graphify/health` 返回 200 且 schema 合法

## Dev Notes

- **`graph.json` 路径**：从 `backend/app/core/config.py` 读取 `GRAPHIFY_GRAPH_PATH`（已有配置项，确认路径）
- **vault 文件扫描排除规则**：排除 `_templates/`、`_system/`、`.obsidian/`、`_bmad-output/` 等系统目录，只统计学习者的笔记
- **NFR-DEG-4**：`Graphify 失败 → 读 frontmatter + wikilinks`。降级服务已在 `graphify_service.py` 中有实现，此 Story 是集成调用，不重写降级逻辑
- **NFR-PERF-3**：Graphify 全量索引 `< 30s for ~100 文件`。health check 本身只读 `graph.json` 元数据，不重跑索引，速度应远快于 30s
- **structlog 而非标准 logging**：项目规范
- **MCP 工具命名**：`graphify_health`（下划线风格，与现有工具命名一致）

### Project Structure Notes

- 修改文件：`backend/app/services/graphify_service.py`（新增 `health_check()` 方法）
- 新增 Pydantic 模型：`backend/app/models/graphify.py`（新建 `GraphifyHealthReport`）
- 修改文件：`backend/app/api/v1/endpoints/health.py`（新增 `/graphify/health` 端点）
- 修改文件：MCP 工具定义（注册 `graphify_health` 工具）
- 测试文件：`backend/tests/unit/test_graphify_health.py`、`backend/tests/integration/test_graphify_health_api.py`

### References

- [Source: backend/app/services/graphify_service.py] — Graphify 服务入口
- [Source: backend/app/api/v1/endpoints/health.py] — 主健康检查端点（已有）
- [Source: backend/app/core/config.py] — GRAPHIFY_GRAPH_PATH 等配置
- [Source: _bmad-output/planning-artifacts/epics.md#Story-8.3] — AC 和 FR 映射
- [FR40] Graphify health check
- [NFR-DEG-4] Graphify 失败 → 读 frontmatter + wikilinks

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证 Health Check 报告** (AC: #1, #2)
   - 在 Obsidian 中调用 `/graphify_health` 命令（通过 Claudian 对话输入）
   - 应看到一段报告，包含：最后更新时间、节点数量、边数量、已索引笔记数 vs 总笔记数
   - 如果有未索引的笔记，报告中应列出文件名
   - 如果看不到这段报告，记录 Story 8.3 和实际看到的内容

2. **验证损坏检测** (AC: #3)
   - （需开发者手动破坏 graph.json）
   - 破坏后执行 `/graphify_health`
   - 应看到："graph.json is corrupted，建议执行 /graphify_rebuild"
   - 且程序没有崩溃，仍然正常响应

3. **验证降级提示** (AC: #4)
   - 临时删除或重命名 graph.json 文件
   - 执行 `/graphify_health`
   - 应看到：`⚠ Graphify degraded: using frontmatter + wikilinks fallback`
   - 且其他 AI 功能（如对话）仍然可用（只是使用了降级来源）

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-8.3.1 | pytest | `.venv/bin/pytest tests/unit/test_graphify_health.py -x -q` | 0 failed |
| CP-8.3.2 | pytest | `.venv/bin/pytest tests/integration/test_graphify_health_api.py -x -q` | 0 failed |
| CP-8.3.3 | curl | `curl -sf http://localhost:8001/api/v1/graphify/health | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'node_count' in d"` | exit 0 |

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
