---
story_id: "1.2"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 12
depends_on: ["1.1"]
blocks: ["1.3", "2.1"]
trace:
  - "FR-ADAPT-01"
  - "FR-ADAPT-03"
---

# Story 1.2: Wikilink 图构建与邻居发现

Status: ready-for-dev

## Story

As a 系统,
I want 解析 vault 中所有 .md 文件的 [[wikilinks]] 构建双向链接图,
So that AI 对话和考察能发现概念间的邻居关系（替代降级前的 .canvas JSON 解析）。
User：1，双向链接图实时更新吗？2，概念间的邻居关系所构建的图谱，不是我在作为用户使用时进行构建吗？请你告诉我你的这一点在整一个系统中，对应的是 笔记的记忆检索，还是对应的我个人记忆系统检索
## Acceptance Criteria

1. **Given** vault 包含 ~200 个 .md 文件和 ~500 个 wikilinks
   **When** 后端启动时构建图
   **Then** 通过 obsidiantools（NetworkX-based, 4000+ GitHub stars）解析 vault 中所有 `[[wikilinks]]` 并构建双向图
   **And** 图构建完成 < 2s（NFR-PERF）
   **And** 每个节点记录：标题、文件路径、frontmatter 摘要

2. **Given** 图已构建
   **When** 查询某笔记的 N-hop 邻居（默认 N=2）
   **Then** 返回所有 N-hop 内可达的邻居列表
   **And** 每个邻居包含：标题、相对路径、hop 距离、frontmatter（mastery_score/bkt_params 等核心字段）
   **And** 2-hop 遍历 < 200ms（NFR-PERF）

3. **Given** vault 中存在循环链接（A -> B -> C -> A）
   **When** 执行 N-hop 遍历
   **Then** 不会无限循环
   **And** 每个节点在结果中最多出现一次（去重）

4. **Given** 学习者编辑 .md 文件并保存（新增/删除 wikilink）
   **When** 文件变更事件触发
   **Then** 图支持热更新（增量处理变更文件，非全量重建全部文件）
   **And** 更新后遍历结果立即反映变化
   **And** 热更新期间并发查询返回旧图数据（不抛异常，asyncio.Lock 保护）

5. **Given** 查询一个不存在的笔记路径
   **When** 调用 get_neighbors
   **Then** 返回空列表，不抛异常

## Tasks / Subtasks

- [ ] Task 1: 引入 obsidiantools 并创建 WikilinkGraphService (AC: #1, #2, #5)
  - [ ] 1.1: 在 `backend/requirements.txt` 中添加 `obsidiantools>=0.10` 依赖
  - [ ] 1.2: 创建 `backend/app/services/wikilink_graph_service.py`
  - [ ] 1.3: 实现 `WikilinkGraphService.__init__(vault_path: str)`：调用 `obsidiantools.Vault(vault_path).connect()` 构建图，用 structlog 记录构建耗时
  - [ ] 1.4: 定义 `NeighborNote` dataclass：`title: str` · `path: str` · `hop_distance: int` · `frontmatter: Dict[str, Any]`
  - [ ] 1.5: 实现 `get_neighbors(note_path: str, hop: int = 2) -> List[NeighborNote]`：通过 NetworkX BFS 遍历，visited set 防循环，frontmatter 通过 python-frontmatter 解析

- [ ] Task 2: 循环链接防护与边界处理 (AC: #3, #5)
  - [ ] 2.1: BFS 遍历使用 `visited: Set[str]` 跟踪已访问节点，发现循环时跳过
  - [ ] 2.2: 不存在的笔记路径返回空 `[]`，structlog 记录 warning
  - [ ] 2.3: frontmatter 解析失败时返回空 dict 默认值，不抛异常

- [ ] Task 3: 热更新机制 (AC: #4)
  - [ ] 3.1: 实现 `refresh(changed_files: Optional[List[str]] = None)` 方法
  - [ ] 3.2: 当 `changed_files` 提供时，仅重新解析这些文件的 wikilinks 并更新图（增量）
  - [ ] 3.3: 当 `changed_files=None` 时，全量重建（fallback）
  - [ ] 3.4: 使用 `asyncio.Lock` 保护图替换操作：更新期间并发查询读旧图
  - [ ] 3.5: 新增 REST endpoint `POST /api/v1/context/refresh-graph` 接收 `{"changed_files": ["path1.md"]}` 或空 body（全量）

- [ ] Task 4: 性能验证 (AC: #1, #2)
  - [ ] 4.1: 图构建后用 structlog 记录：`graph_build_time_ms`、`total_nodes`、`total_edges`
  - [ ] 4.2: 每次 get_neighbors 调用记录：`traversal_time_ms`、`hop`、`neighbor_count`
  - [ ] 4.3: 编写性能基准测试验证 NFR-PERF 指标

- [ ] Task 5: 测试 (AC: #1, #2, #3, #4, #5)
  - [ ] 5.1: `backend/tests/unit/test_wikilink_graph_service.py` — 图构建、N-hop 遍历、循环链接、空路径处理
  - [ ] 5.2: `backend/tests/unit/test_wikilink_graph_perf.py` — 200 文件构建 < 2s、2-hop 遍历 < 200ms
  - [ ] 5.3: `backend/tests/integration/test_wikilink_graph_integration.py` — 用真实 vault fixture 验证端到端、热更新后结果变化

## Dev Notes

- **为什么 obsidiantools**: PyPI `obsidiantools>=0.10`，GitHub 4000+ stars，内部使用 NetworkX 构建双向链接图，支持 `Vault(path).connect()` 一键解析。DD-04 要求参考成熟案例。
- **Service 风格**: 参考 `backend/app/services/rag_service.py` 的 structlog + 类型标注 + docstring 模式
- **现有 context_enrichment**: `backend/app/services/context_enrichment_service.py` 中有 `extract_and_resolve_wikilinks()` 正则实现（L166-262），本 service 将替代该逻辑，Story 1.3 负责集成
- **frontmatter 解析**: obsidiantools 内置 frontmatter 支持；如版本不含则使用 `python-frontmatter`（已在 backend 依赖中）
- **asyncio.Lock**: refresh 期间图正在重建，并发 get_neighbors 应返回旧图数据而非阻塞或抛异常
- **增量 vs 全量**: v1 优先实现可靠的全量 refresh + 增量接口；obsidiantools 的 `Vault.connect()` 是全量的，增量需手动更新 NetworkX 图的边
- **Neo4j 无关**: 本 service 仅处理 vault 文件系统的 wikilink 图，与 Neo4j 知识图谱独立（Graphify 负责 Neo4j 侧图索引）

### Project Structure Notes

- 新建文件：`backend/app/services/wikilink_graph_service.py`
- 修改文件：`backend/requirements.txt`（添加 obsidiantools）
- 修改文件：`backend/app/api/v1/endpoints/context.py`（新增 refresh-graph endpoint）
- 测试文件：`backend/tests/unit/test_wikilink_graph_service.py`
- 测试文件：`backend/tests/unit/test_wikilink_graph_perf.py`
- 测试文件：`backend/tests/integration/test_wikilink_graph_integration.py`
- 测试 fixture：`backend/tests/fixtures/vault/` — 含 3+ .md 文件互相 wikilink

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-ADAPT-01] — 双向链接图遍历发现邻居关系
- [Source: _bmad-output/planning-artifacts/prd.md#FR-ADAPT-03] — 图热更新（增量重建）
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.2] — AC 原文和 NFR 映射
- [Source: backend/app/services/context_enrichment_service.py#L166-262] — 现有 wikilink 正则实现，将被 WikilinkGraphService 替代
- [Source: backend/app/services/rag_service.py] — Service 风格参考
- [Source: docs/architecture.md#Agentic-RAG] — 系统整体架构

## UAT Script

> 非技术用户验收脚本

1. **验证图构建** (AC: #1)
   - 启动后端服务
   - 在浏览器访问 `http://localhost:8001/api/v1/context/graph-stats`
   - 应该看到图的统计信息：节点数量（约等于 vault 中 .md 文件数）和边数量
   - 构建时间应该在 2 秒以内

2. **验证邻居发现** (AC: #2, #3)
   - 找到 vault 中一篇有多个 `[[双链]]` 引用的笔记
   - 访问 `http://localhost:8001/api/v1/context/neighbors?note=笔记名.md&hop=2`
   - 应该看到邻居列表，包含标题、路径、距离和学习数据
   - 如果笔记互相引用形成环路，每个笔记只出现一次

3. **验证热更新** (AC: #4)
   - 在 Obsidian 中编辑一篇笔记，新增一个 `[[新链接]]`，保存
   - 在浏览器用 POST 请求触发 `http://localhost:8001/api/v1/context/refresh-graph`
   - 重新查询该笔记的邻居，应该能看到新链接的目标已出现

4. **验证性能** (AC: #1, #2)
   - 首次启动后端后，观察终端日志中的图构建时间（应 < 2 秒）
   - 查询邻居时，响应应几乎即时（< 1 秒体感）

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.2.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_wikilink_graph_service.py -x -q` | 0 failed |
| CP-1.2.2 | pytest | `.venv/bin/pytest backend/tests/unit/test_wikilink_graph_perf.py -x -q` | 0 failed |
| CP-1.2.3 | pytest | `.venv/bin/pytest backend/tests/integration/test_wikilink_graph_integration.py -x -q` | 0 failed |
| CP-1.2.4 | ruff | `ruff check backend/app/services/wikilink_graph_service.py` | exit 0 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes
<!-- Auto-filled -->

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
