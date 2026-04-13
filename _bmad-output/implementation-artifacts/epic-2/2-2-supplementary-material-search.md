---
doc_type: story
story_id: "2.2"
aliases: ["2.2"]
epic_id: "EPIC-2"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: ["2.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 2.2: 补充学习材料搜索

## Story

As a 学习者,
I want 在对话回答中看到可点击的补充学习材料列表,
so that 我可以快速跳转到相关笔记深入学习。

## Acceptance Criteria

1. **Given** AI 生成对话回答
   **When** 回答涉及 vault 中其他笔记的主题
   **Then** 系统通过 LanceDB hybrid search 检索相关笔记
   **And** 检索后经过 reranker 精排 + Adaptive-k 筛选（AR6）
   **And** 在回答末尾展示可点击的 [[wikilink]] 列表（≤5 条）
   **And** LanceDB 增量索引 < 500ms per file（NFR-PERF-4）

## Tasks / Subtasks

- [ ] Task 1: 实现 LanceDB hybrid search 检索服务 (AC: #1)
  - [ ] 1.1 在 `backend/app/services/` 新建或扩展 `material_search_service.py`，定义 `MaterialSearchService` 类
  - [ ] 1.2 实现 `search_related(query: str, top_k: int = 20) -> List[SearchResult]`：调用 LanceDB 混合搜索（向量相似度 + BM25 全文检索）
  - [ ] 1.3 LanceDB 表结构：`note_path`（str）、`title`（str）、`content_chunk`（str）、`embedding`（vector）、`indexed_at`（timestamp）
  - [ ] 1.4 实现增量索引 `index_file(note_path: str)`：读取 `.md` 文件，分块，生成 embedding（bge-m3），写入 LanceDB；单文件 < 500ms（NFR-PERF-4）
  - [ ] 1.5 实现全量索引 `index_vault(vault_path: str)`：遍历所有 `.md` 文件调用 `index_file()`，跳过已索引且未修改的文件（mtime 对比）

- [ ] Task 2: Reranker + Adaptive-k 精排（AR6）(AC: #1)
  - [ ] 2.1 实现 `rerank(query: str, candidates: List[SearchResult]) -> List[SearchResult]`：使用 cross-encoder reranker 对候选结果精排
  - [ ] 2.2 Adaptive-k 策略：计算候选分数的 elbow point，自动截断低相关结果，最多保留 5 条
  - [ ] 2.3 reranker 模型：使用 `BAAI/bge-reranker-base`（小模型，本地 Ollama 或 transformers 直接加载）
  - [ ] 2.4 当 reranker 不可用时（模型未加载）降级到原始向量相似度排名（NFR-DEG 隐含）

- [ ] Task 3: 对话 API 集成补充材料 (AC: #1)
  - [ ] 3.1 修改 `POST /api/v1/dialog/start` endpoint（Story 2.1 实现），在 LLM 回复生成后，异步触发材料检索
  - [ ] 3.2 使用 AI 回复文本作为检索 query 调用 `MaterialSearchService.search_related()`
  - [ ] 3.3 响应体扩展：`DialogResponse` 新增 `supplementary_materials: List[MaterialLink]` 字段
  - [ ] 3.4 `MaterialLink` dataclass：`title: str`、`note_path: str`、`relevance_score: float`
  - [ ] 3.5 材料检索异步执行，不阻塞 AI 回复返回（可分两个 SSE 事件：先回复，再材料）

- [ ] Task 4: 前端材料列表展示 (AC: #1)
  - [ ] 4.1 修改 `ChatPanel.tsx`，在 AI 回复气泡末尾渲染 `SupplementaryMaterialList` 组件
  - [ ] 4.2 新建 `frontend/src/components/SupplementaryMaterialList.tsx`：展示 ≤5 条可点击的 `[[wikilink]]` 样式链接
  - [ ] 4.3 点击材料链接时，向 Tauri 发送 `open_note` 命令，在 Obsidian 中打开对应笔记
  - [ ] 4.4 材料列表加载中时显示占位符（3 条骨架行），加载完成后替换
  - [ ] 4.5 如果检索结果为空，不显示材料列表区域（不展示空列表）

- [ ] Task 5: 编写测试 (AC: #1)
  - [ ] 5.1 单元测试 `backend/tests/unit/test_material_search_service.py`：
    - `search_related()` 返回相关笔记列表
    - `rerank()` 对候选结果正确排序
    - Adaptive-k 截断：低分结果被去除，高分结果保留
  - [ ] 5.2 性能测试 `backend/tests/unit/test_material_search_perf.py`：
    - `index_file()` 单文件增量索引 < 500ms
  - [ ] 5.3 集成测试 `backend/tests/integration/test_dialog_materials.py`：
    - 完整 `POST /api/v1/dialog/start` 响应包含 `supplementary_materials` 字段
    - `supplementary_materials` 长度 ≤ 5
  - [ ] 5.4 前端测试 `frontend/src/components/__tests__/SupplementaryMaterialList.test.tsx`：
    - 空列表时不渲染组件
    - 传入材料数据后渲染 wikilink 样式链接
    - 点击链接触发 `open_note` Tauri 命令

## Dev Notes

- **LanceDB hybrid search**：同时使用 `vector_search`（embedding 相似度）和 `fts_search`（BM25 全文），通过 reciprocal rank fusion (RRF) 合并结果。LanceDB 0.8+ 原生支持 `VectorQuery.fts()` 混合检索
- **bge-m3 embedding**：项目已有 Ollama 运行 bge-m3（参考 docker-compose.yml 中 ollama service），通过 `http://host.docker.internal:11434/api/embeddings` 调用，model: `bge-m3`
- **Adaptive-k 实现**：对精排后的分数列表求一阶差分，找到差分最大的位置作为 elbow，elbow 之后的候选全部丢弃；保底返回 top-1（即使所有分数都很低）
- **材料检索异步化**：在 FastAPI 中，先 `await` LLM 调用，得到回复后用 `asyncio.create_task()` 触发后台检索；如果走 SSE 流式响应，可先 yield 回复内容，再 yield 材料列表事件
- **NFR-PERF-4 保证**：bge-m3 embedding 生成是瓶颈，通过批量请求（chunk batch size 4）可以降低单文件 embedding 时间；500ms 包含文件读取 + 分块 + embedding + LanceDB 写入

### Project Structure Notes

- 新建文件：`backend/app/services/material_search_service.py`
- 修改文件：`backend/app/api/v1/endpoints/dialog.py`（扩展响应体）
- 新建文件：`frontend/src/components/SupplementaryMaterialList.tsx`
- 修改文件：`frontend/src/components/ChatPanel.tsx`（集成材料列表）
- 测试文件：
  - `backend/tests/unit/test_material_search_service.py`
  - `backend/tests/unit/test_material_search_perf.py`
  - `backend/tests/integration/test_dialog_materials.py`
  - `frontend/src/components/__tests__/SupplementaryMaterialList.test.tsx`
- 样式参考：`backend/app/services/rag_service.py`（LanceDB 检索逻辑）、`frontend/src/components/ChatPanel.tsx`

### References

- [Source: backend/app/services/rag_service.py] — LanceDB 检索和 embedding 服务参考实现
- [Source: docker-compose.yml#ollama] — bge-m3 模型 Ollama 服务配置
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.2] — AC 原文和 FR/AR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR3-AR5-AR6] — FR3 原文：补充材料搜索；AR5：LanceDB hybrid search；AR6：reranker + Adaptive-k

## UAT Script

> 非技术用户验收脚本：只描述用户操作和预期看到的内容，不含代码术语。

1. **验证补充材料出现在回复末尾** (AC: #1)
   - 打开应用，在 AI 对话面板中针对某笔记（例如"线性代数"）提问："能给我推荐相关的学习材料吗？"
   - 点击发送，等待回复完成
   - AI 回复下方应出现一个小标题"相关笔记"或类似，下面列出最多 5 条笔记链接
   - 链接应该是蓝色可点击的样式
   - 如果没有看到材料列表，请记录 Story 2.2

2. **验证点击材料可以打开笔记** (AC: #1)
   - 在上一步看到的材料列表中，点击其中任意一条链接
   - Obsidian 应该自动切换并打开对应的笔记
   - 如果点击后什么都没发生，或者打开了错误的笔记，请记录 Story 2.2 和点击的链接名称

3. **验证材料数量不超过 5 条** (AC: #1)
   - 提问一个涉及主题广泛的问题（例如"解释一下机器学习的基础概念"）
   - 查看补充材料列表，数量应该不超过 5 条
   - 如果超过 5 条，请记录 Story 2.2 和实际条数

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-2.2.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_material_search_service.py -x -q` | 0 failed |
| CP-2.2.2 | pytest | `.venv/bin/pytest backend/tests/unit/test_material_search_perf.py -x -q -m performance` | 0 failed |
| CP-2.2.3 | pytest | `.venv/bin/pytest backend/tests/integration/test_dialog_materials.py -x -q` | 0 failed |
| CP-2.2.4 | vitest | `cd frontend && npx vitest run src/components/__tests__/SupplementaryMaterialList.test.tsx` | 0 failed |
| CP-2.2.5 | ruff | `ruff check backend/app/services/material_search_service.py` | exit 0 |

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

- EPIC: [[EPIC-2]]
- PRD: [[PRD14]]
- Depends on: [[2.1]]
