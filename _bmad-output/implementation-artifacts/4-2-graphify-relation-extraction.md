---
doc_type: story
story_id: "4.2"
aliases: ["4.2"]
epic_id: "EPIC-4"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: []
blocks: ["4.3"]
trace:
  decisions: []
  bugs: []
---
# Story 4.2: Graphify 关系提取 + graph.json 索引

## Story

As a 系统,
I want 通过 Graphify 从笔记文本中自动提取概念关系，生成独立 AI 检索索引 graph.json,
so that AI 可以理解概念之间的关系用于出题和对话。

## Acceptance Criteria

1. **Given** vault 中有笔记内容
   **When** 系统运行 Graphify 全量提取
   **Then** 从文本中识别概念关系（前置、关联、对比、包含等关系类型）
   **And** 生成 `graph.json` 作为 AI 检索索引，存储在 vault 内约定路径
   **And** 全量索引耗时 < 30s for ~100 文件（NFR-PERF-3）

2. **Given** 学习者新建或修改了一篇笔记
   **When** 下次 Graphify 运行（手动触发或后台触发）
   **Then** 增量更新 `graph.json`（只处理变更文件，不需要全量重建）
   **And** 未修改文件的关系条目保持不变

3. **Given** Graphify 提取过程中遇到 LLM API 错误或超时
   **When** 某个文件提取失败
   **Then** 该文件跳过，记录错误日志，其余文件继续处理
   **And** 最终生成的 `graph.json` 中不包含失败文件的条目（降级行为，NFR-DEG-4）
   **And** 系统不因单文件失败而中断整个提取流程

4. **Given** `graph.json` 已生成
   **When** AI 需要查询概念关系
   **Then** 后端可通过 `GET /api/v1/graphify/query` 端点按概念名检索相关关系
   **And** 返回结果包含 relation_type、source_concept、target_concept 字段

## Tasks / Subtasks

- [ ] Task 1: 实现 Graphify 提取核心逻辑 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/services/` 创建 `graphify_service.py`
  - [ ] 1.2 实现 `extract_relations_from_note(note_path, vault_root) -> List[Relation]`
      - 读取笔记文本（去掉 frontmatter）
      - 调用 LLM（通过 LiteLLM 层，AR8）提取关系三元组：(source, relation_type, target)
      - relation_type 枚举：prerequisite / related / contrast / contains / derived_from
  - [ ] 1.3 实现 `run_full_extraction(vault_root) -> GraphIndex` — 遍历所有 .md 文件，调用 1.2
  - [ ] 1.4 实现 `run_incremental_extraction(vault_root, changed_files) -> GraphIndex` — 只处理变更文件，合并现有 graph.json

- [ ] Task 2: 实现 graph.json 读写 (AC: #1, #2)
  - [ ] 2.1 定义 `GraphIndex` Pydantic 模型：`{ nodes: List[Node], edges: List[Edge], metadata: IndexMeta }`
      - `Node`: `{ id, label, note_path, confidence_level }`
      - `Edge`: `{ source_id, target_id, relation_type, confidence_level, extracted_from }`
      - `IndexMeta`: `{ version, last_updated, total_files, failed_files }`
  - [ ] 2.2 实现 `save_graph_index(graph, output_path)` — 原子写入（tempfile + os.replace）
  - [ ] 2.3 实现 `load_graph_index(path) -> GraphIndex` — 文件不存在时返回空 GraphIndex
  - [ ] 2.4 `graph.json` 默认存储路径：`vault_root/_graphify/graph.json`

- [ ] Task 3: 实现增量更新（content_hash 去重）(AC: #2)
  - [ ] 3.1 `IndexMeta` 中增加 `file_hashes: Dict[str, str]`（文件路径 → MD5 哈希）
  - [ ] 3.2 `run_incremental_extraction` 时先比较 hash，hash 未变的文件直接复用现有条目

- [ ] Task 4: 实现 API 端点 (AC: #4)
  - [ ] 4.1 在 `backend/app/api/v1/endpoints/` 创建 `graphify.py`
  - [ ] 4.2 `POST /api/v1/graphify/run` — 触发全量或增量提取（body: `{ vault_root, mode: "full"|"incremental" }`）
  - [ ] 4.3 `GET /api/v1/graphify/query` — 按 concept 名检索关系（query param: `concept_name`）
  - [ ] 4.4 `GET /api/v1/graphify/health` — 返回 graph.json 存在性、条目数、最后更新时间

- [ ] Task 5: 降级处理（单文件失败不中断）(AC: #3)
  - [ ] 5.1 `extract_relations_from_note` 用 try/except 包裹 LLM 调用，捕获 APIError / Timeout
  - [ ] 5.2 失败时 structlog 记录 `event="graphify_file_failed"` + 文件路径 + 错误类型
  - [ ] 5.3 `IndexMeta.failed_files` 记录本次失败的文件列表

- [ ] Task 6: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 6.1 单元测试：`tests/unit/test_graphify_service.py` — 关系提取、增量逻辑、graph.json 读写
  - [ ] 6.2 集成测试：`tests/integration/test_graphify_api.py` — 端点调用 + 结果校验
  - [ ] 6.3 性能测试注释：注明 NFR-PERF-3 要求（< 30s / 100 文件），待 CI 中实测

## Dev Notes

- **LLM 提取 prompt**：不可硬编码 prompt（S27 决策禁止 prompt 硬编码）。prompt 模板存放在 `backend/app/prompts/graphify_extract.jinja2`，运行时加载。
- **LiteLLM 层**：所有 LLM 调用必须通过 `backend/app/llm/client.py` 的 LiteLLM 统一层（AR8），不直接调用 OpenAI / Anthropic SDK。
- **structlog**：日志使用 structlog（不用标准 logging），字段名用 snake_case。
- **NFR-PERF-3 实现路径**：100 文件 < 30s 意味着单文件平均 < 300ms。LLM 调用使用 `asyncio.gather` 并发提取（上限 10 并发，防 rate limit），不用串行循环。
- **graph.json 位置**：`vault_root/_graphify/graph.json`。`_graphify/` 前缀下划线确保不被 Dataview 索引。
- **增量触发时机**：Story 4.2 只实现提取核心和 API；触发时机（文件变更监听）由 Epic 8 的系统健康 story 负责。本 story 只需提供手动触发端点。
- **Story 4.3 依赖**：置信度标注（EXTRACTED / INFERRED / AMBIGUOUS）由 Story 4.3 实现并写入 Edge.confidence_level。本 story 提取时 confidence_level 字段留空或默认 "EXTRACTED"，4.3 上线后填充。

### Project Structure Notes

- 新 service：`backend/app/services/graphify_service.py`
- 新端点：`backend/app/api/v1/endpoints/graphify.py`
- Pydantic 模型：`backend/app/models/graph_index.py`
- Prompt 模板：`backend/app/prompts/graphify_extract.jinja2`
- 测试：`backend/tests/unit/test_graphify_service.py`、`backend/tests/integration/test_graphify_api.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4.2] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR17] — 原始需求
- [Source: backend/app/services/rag_service.py] — 后端 service 风格参考（AR5 增量索引模式）
- [Source: backend/app/api/v1/endpoints/canvas.py] — 后端 router 风格参考
- [Source: _bmad-output/planning-artifacts/architecture.md#AR8] — LiteLLM 统一层

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证全量提取生成 graph.json** (AC: #1)
   - 打开终端，运行 `bash scripts/start.sh`，等待系统就绪
   - 在 Claudian 或直接访问 `http://localhost:8001/api/v1/graphify/run`（POST，body: `{"vault_root": "<你的vault路径>", "mode": "full"}`）
   - 在 vault 文件列表中应看到 `_graphify/graph.json` 文件被创建或更新
   - 访问 `http://localhost:8001/api/v1/graphify/health`，应看到 `total_files` 大于 0 且 `last_updated` 为当前时间
   - 如果没有看到 graph.json 文件，记录 Story 4.2 和错误信息

2. **验证概念关系可查询** (AC: #4)
   - 访问 `http://localhost:8001/api/v1/graphify/query?concept_name=<你vault中存在的一个概念>`
   - 应看到一个 JSON 结果列出与该概念相关的关系（包含 relation_type、source_concept、target_concept）
   - 如果返回空列表而 vault 中确实有相关内容，记录 Story 4.2 和概念名

3. **验证增量更新不重建全部** (AC: #2)
   - 修改 vault 中一篇笔记的内容（加一行文字）
   - 再次触发 `POST /api/v1/graphify/run`，使用 `"mode": "incremental"`
   - 检查 `graph.json` 的 `last_updated` 已更新
   - 检查 `metadata.failed_files` 为空（无失败文件）
   - 如果每次增量都明显很慢（接近全量时间），记录 Story 4.2

4. **验证单文件失败不中断** (AC: #3)
   - 在 vault 中放入一个空白 .md 文件（0 字节）
   - 触发全量提取
   - 检查最终 `graph.json` 中其余笔记的条目仍然存在
   - `metadata.failed_files` 中应包含该空白文件名
   - 如果整个提取中断或 graph.json 不存在，记录 Story 4.2

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-4.2.1 | pytest | `.venv/bin/pytest tests/unit/test_graphify_service.py -x -q` | 0 failed |
| CP-4.2.2 | pytest | `.venv/bin/pytest tests/integration/test_graphify_api.py -x -q` | 0 failed |
| CP-4.2.3 | pytest | `.venv/bin/pytest tests/ -k "graphify" -x -q` | 0 failed |

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

- EPIC: [[EPIC-4]]
- PRD: [[PRD14]]
- Blocks: [[4.3]]
