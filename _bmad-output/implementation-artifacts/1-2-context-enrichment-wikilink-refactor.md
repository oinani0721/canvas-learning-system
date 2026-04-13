---
doc_type: story
story_id: "1.2"
aliases: ["1.2"]
epic_id: "EPIC-1"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: ["1.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 1.2: context_enrichment 重构为 wikilink 图遍历

## Story

As a 系统,
I want 将 context_enrichment 模块从读取 .canvas JSON 重构为通过 wikilink 图解析库（obsidiantools）遍历双向链接,
so that 降级到 Obsidian Hybrid 方案后仍能发现相邻概念作为对话上下文。

## Acceptance Criteria

1. **Given** 后端 context_enrichment 模块已启动并持有 vault 路径
   **When** 系统接收一个笔记路径（`.md` 文件）作为输入
   **Then** 通过 obsidiantools 解析 vault 中的 `[[wikilinks]]`，返回 N-hop 邻居列表（默认 2-hop）
   **And** 每个邻居条目包含：标题（title）、相对路径（path）、frontmatter 摘要（mastery_score 等核心字段）
   **And** 单次 N-hop 遍历延迟 < 200ms（NFR-PERF-6）
   **And** 首次 vault wikilink 图构建耗时 < 2s（NFR-PERF-5）

2. **Given** vault 中某笔记的 `[[wikilinks]]` 发生变化（增/删链接）
   **When** 系统下次调用 context_enrichment 查询该笔记的邻居
   **Then** 图支持热更新，返回包含最新链接关系的邻居列表（NFR-REL-4）
   **And** 不需要重启后端进程

## Tasks / Subtasks

- [ ] Task 1: 引入 obsidiantools 并构建 WikilinkGraph 包装层 (AC: #1, #2)
  - [ ] 1.1 在 `backend/pyproject.toml`（或 `requirements.txt`）中添加 `obsidiantools` 依赖
  - [ ] 1.2 在 `backend/app/services/` 新建 `wikilink_graph.py`，封装 `obsidiantools.VaultStats` 的图构建逻辑
  - [ ] 1.3 实现 `WikilinkGraph.__init__(vault_path: str)`：调用 `obsidiantools.VaultStats(vault_path).connect()` 构建图，记录构建耗时（structlog）
  - [ ] 1.4 实现 `WikilinkGraph.get_neighbors(note_path: str, hop: int = 2) -> List[NeighborNote]`：通过 NetworkX BFS 遍历返回 N-hop 邻居，含标题/路径/frontmatter 摘要
  - [ ] 1.5 实现热更新：`WikilinkGraph.refresh()`，重新调用 `connect()` 重建图，线程安全（用 `asyncio.Lock`）

- [ ] Task 2: 重构 ContextEnrichmentService 使用 WikilinkGraph (AC: #1)
  - [ ] 2.1 修改 `ContextEnrichmentService.__init__` 接收 `vault_path: str` 并初始化 `WikilinkGraph`
  - [ ] 2.2 新增方法 `get_wikilink_neighbors(note_path: str, hop: int = 2) -> List[NeighborNote]`，代理到 `WikilinkGraph.get_neighbors()`
  - [ ] 2.3 在 `enrich_with_adjacent_nodes()` 中，当输入为 `.md` 文件路径时，优先调用 `get_wikilink_neighbors()` 替代原 `.canvas` JSON edges 读取逻辑
  - [ ] 2.4 保留原 `.canvas` edges 分支作为 fallback（当输入为 canvas 名而非 `.md` 路径时）
  - [ ] 2.5 `EnrichedContext.wikilink_neighbors` 新字段：存储本次遍历的邻居列表

- [ ] Task 3: NeighborNote 数据类定义 (AC: #1)
  - [ ] 3.1 在 `wikilink_graph.py` 中定义 `NeighborNote` dataclass：`title: str`、`path: str`、`hop_distance: int`、`frontmatter: Dict[str, Any]`（含 mastery_score/bkt_params 等）
  - [ ] 3.2 frontmatter 读取：通过 python-frontmatter（或 obsidiantools 内置）解析 YAML frontmatter，缺失字段返回空默认值，不抛异常

- [ ] Task 4: 热更新 API endpoint (AC: #2)
  - [ ] 4.1 在 `backend/app/api/v1/endpoints/context.py`（如不存在则新建）中添加 `POST /api/v1/context/refresh-graph` endpoint
  - [ ] 4.2 该 endpoint 调用 `WikilinkGraph.refresh()`，返回 `{"status": "ok", "build_time_ms": float}`
  - [ ] 4.3 Vault 文件变化时（文件系统 watchdog 或手动调用）触发 refresh

- [ ] Task 5: 编写测试 (AC: #1, #2)
  - [ ] 5.1 单元测试 `backend/tests/unit/test_wikilink_graph.py`：
    - 图构建后 `get_neighbors()` 返回正确的 1-hop 和 2-hop 邻居
    - 环形链接不导致无限循环
    - 不存在的笔记路径返回空列表（不抛异常）
  - [ ] 5.2 性能测试 `backend/tests/unit/test_wikilink_graph_perf.py`：
    - 100 个 `.md` 文件的 vault 构建 < 2000ms
    - 2-hop 遍历 < 200ms
  - [ ] 5.3 集成测试 `backend/tests/integration/test_context_enrichment_wikilink.py`：
    - 用真实 vault fixture（含 3 个 `.md` 文件，互相 `[[wikilink]]`）验证端到端邻居发现
    - 热更新：修改 vault fixture 中的链接后调用 `refresh()`，验证结果变化

## Dev Notes

- **为什么是 obsidiantools**：该库（PyPI: obsidiantools 0.10+，GitHub 4000+ stars）内部用 NetworkX 构建双向链接图，支持 `VaultStats.connect()` 一键解析整个 vault，正好对应本项目需求。Context7 / DD-04 要求参考成熟案例实现。
- **保留 .canvas 分支**：降级后 `.canvas` 文件已退出主流程，但旧测试依赖 `read_canvas()` 分支，不能删除。区分策略：入参为 `note_path`（.md 相对路径）时走 WikilinkGraph；入参为 `canvas_name`（无扩展名或 .canvas）时走原 CanvasService。
- **frontmatter 解析**：obsidiantools 已集成 python-frontmatter；若版本不含 frontmatter API，使用 `python-frontmatter` 包独立读取（已在 backend 依赖中）。
- **asyncio.Lock 热更新**：`refresh()` 期间图正在重建，并发查询应返回旧图数据而非抛异常。用 `asyncio.Lock` 保护 `_graph` 替换操作。
- **structlog 日志**：所有计时点（图构建耗时、遍历耗时）用 `structlog.get_logger(__name__)` 记录，字段名遵循项目规范（snake_case）。禁止使用标准 `logging`。
- **NFR-PERF-5 实测**：obsidiantools 官方 benchmark 显示 500 文件 vault 构建约 3-5s；100 文件 vault 预计 < 1s，满足 < 2s 要求。大 vault 场景可考虑增量 refresh（v1 先全量 refresh）。

### Project Structure Notes

- 新建文件：`backend/app/services/wikilink_graph.py`
- 修改文件：`backend/app/services/context_enrichment_service.py`（新增 `get_wikilink_neighbors`、修改 `__init__` 接收 `vault_path`）
- 新建/修改文件：`backend/app/api/v1/endpoints/context.py`（新增 refresh endpoint）
- 测试文件：
  - `backend/tests/unit/test_wikilink_graph.py`
  - `backend/tests/unit/test_wikilink_graph_perf.py`
  - `backend/tests/integration/test_context_enrichment_wikilink.py`
- 样式参考：`backend/app/services/rag_service.py`（service 结构）、`backend/app/api/v1/endpoints/canvas.py`（router 结构）

### References

- [Source: backend/app/services/context_enrichment_service.py#L166-262] — 现有 `extract_and_resolve_wikilinks()` regex 实现，将被 WikilinkGraph 取代
- [Source: backend/app/services/context_enrichment_service.py#L341-370] — `ContextEnrichmentService.__init__`，需新增 `vault_path` 参数
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.2] — AC 原文和 NFR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR42-FR43] — FR 原文：context_enrichment 重构 + wikilink 邻居发现
- [Source: memory/project_context_enrichment_gap.md] — 架构断层说明：降级后 .canvas 文件退出主流，context_enrichment 需跟进重构

## UAT Script

> 非技术用户验收脚本：只描述用户操作和预期看到的内容，不含代码术语。

1. **验证邻居发现** (AC: #1)
   - 打开 Obsidian，找到 vault 中任意一篇有 `[[双链]]` 引用的笔记（比如 "线性变换" 这篇笔记里写了 `[[矩阵]]`）
   - 在浏览器地址栏输入 `http://localhost:8001/api/v1/context/neighbors?note=线性变换.md&hop=2`
   - 应该看到一个 JSON 列表，包含 "矩阵" 这篇笔记的信息（标题、路径、以及 mastery_score 之类的学习数据）
   - 如果列表是空的，或者看到错误信息，请记录 Story 1.2 以及显示的内容

2. **验证热更新** (AC: #2)
   - 在 vault 中打开任意一篇笔记，新增一条 `[[新概念]]` 的双链，保存
   - 在浏览器访问 `http://localhost:8001/api/v1/context/refresh-graph`（POST 请求，可以用 Insomnia/Postman，或者请技术人员帮忙触发）
   - 刷新后，重新查询该笔记的邻居，应该能看到 "新概念" 已出现在邻居列表中
   - 如果看不到新概念，请记录 Story 1.2 和操作步骤

3. **验证性能感知** (AC: #1 NFR)
   - 首次打开后端（或重启后端）后访问任意邻居查询接口
   - 返回应在 3 秒内完成（图构建 + 首次查询）
   - 后续查询应几乎即时（< 1 秒）
   - 如果首次查询超过 5 秒，请记录 Story 1.2

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.2.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_wikilink_graph.py -x -q` | 0 failed |
| CP-1.2.2 | pytest | `.venv/bin/pytest backend/tests/unit/test_wikilink_graph_perf.py -x -q -m performance` | 0 failed |
| CP-1.2.3 | pytest | `.venv/bin/pytest backend/tests/integration/test_context_enrichment_wikilink.py -x -q` | 0 failed |
| CP-1.2.4 | pytest | `.venv/bin/pytest backend/tests/unit/test_context_enrichment_2hop.py -x -q` | 0 failed (回归，不破坏原 2-hop tests) |
| CP-1.2.5 | ruff | `ruff check backend/app/services/wikilink_graph.py backend/app/services/context_enrichment_service.py` | exit 0 |

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
- Depends on: [[1.1]]
