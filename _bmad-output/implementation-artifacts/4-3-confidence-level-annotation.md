---
doc_type: story
story_id: "4.3"
epic_id: "EPIC-4"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: ["4.2"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 4.3: 三级置信度标注

## Story

As a 系统,
I want 为 Graphify 提取的每个概念关系标注三级置信度（EXTRACTED / INFERRED / AMBIGUOUS）,
so that 系统和学习者可以区分高确信的关系和需要验证的推测。

## Acceptance Criteria

1. **Given** Graphify（Story 4.2）提取了一组概念关系
   **When** 系统执行置信度标注
   **Then** 直接从文本中明确陈述的关系标注为 `EXTRACTED`
   **And** 通过逻辑推理得出的隐含关系标注为 `INFERRED`
   **And** 文本表述不确定或存在矛盾的关系标注为 `AMBIGUOUS`
   **And** 置信度信息存储在 `graph.json` 的每条 Edge 的 `confidence_level` 字段中

2. **Given** `graph.json` 中存在不同置信度的关系
   **When** AI 查询概念关系（`GET /api/v1/graphify/query`）
   **Then** 返回结果包含每条关系的 `confidence_level` 字段
   **And** 调用方可以按 confidence_level 过滤（query param: `min_confidence=EXTRACTED|INFERRED|AMBIGUOUS`）

3. **Given** 同一对概念之间存在多条关系（例如 EXTRACTED 和 INFERRED 各一条）
   **When** 系统标注置信度
   **Then** 不合并去重，保留所有条目，每条独立标注
   **And** `graph.json` 中每条 Edge 有唯一 id（source_id + target_id + relation_type 的组合 hash）

4. **Given** Graphify 运行增量更新（Story 4.2 的增量模式）
   **When** 某笔记被修改后重新提取
   **Then** 该笔记的旧关系条目被替换为新提取结果（包含新的置信度标注）
   **And** 未修改笔记的置信度标注保持不变

## Tasks / Subtasks

- [ ] Task 1: 扩展 LLM 提取 prompt 以输出置信度 (AC: #1)
  - [ ] 1.1 修改 `backend/app/prompts/graphify_extract.jinja2` — 在关系三元组输出中增加第四个字段 `confidence`
  - [ ] 1.2 prompt 指导 LLM 区分三级：
      - EXTRACTED：原文有明确表述（如"A 是 B 的前提"、"A 包含 B"）
      - INFERRED：原文暗示但未明确（如"学习 A 之前通常需要 B"）
      - AMBIGUOUS：表述含糊或与其他段落矛盾
  - [ ] 1.3 更新 `graphify_service.py` 中的响应解析逻辑，读取 confidence 字段并写入 `Edge.confidence_level`

- [ ] Task 2: 实现 Edge 唯一 ID 生成 (AC: #3)
  - [ ] 2.1 在 `backend/app/models/graph_index.py` 中为 `Edge` 添加 `edge_id: str` 字段
  - [ ] 2.2 `edge_id = sha256(f"{source_id}:{target_id}:{relation_type}")[:16]`
  - [ ] 2.3 增量更新时按 `edge_id` 匹配旧条目，替换而非追加

- [ ] Task 3: 扩展查询 API 支持置信度过滤 (AC: #2)
  - [ ] 3.1 在 `GET /api/v1/graphify/query` 增加 query param `min_confidence: Optional[str] = None`
  - [ ] 3.2 过滤优先级：EXTRACTED > INFERRED > AMBIGUOUS（传 EXTRACTED 只返回 EXTRACTED；传 INFERRED 返回 EXTRACTED + INFERRED）
  - [ ] 3.3 不传 min_confidence 时返回全部（默认行为，向后兼容）

- [ ] Task 4: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 4.1 单元测试：`tests/unit/test_confidence_annotation.py`
      - 验证 prompt 输出解析正确映射三级置信度
      - 验证 edge_id 生成唯一性（不同关系 → 不同 id）
  - [ ] 4.2 集成测试：`tests/integration/test_graphify_query_filter.py`
      - 验证 min_confidence=EXTRACTED 过滤正确
      - 验证增量更新后旧条目被替换

## Dev Notes

- **Story 4.2 依赖**：本 story 在 Story 4.2 的 `graphify_service.py` 和 `graph_index.py` 基础上修改，不新建文件。所有改动均为向前兼容扩展（新增字段，不删改现有字段）。
- **prompt 硬编码禁止**：置信度判断标准同样不可硬编码在 Python 代码中，必须在 Jinja2 模板中定义。
- **AMBIGUOUS 的处理**：AMBIGUOUS 关系对 AI 出题价值低，但保留在 graph.json 中供后续人工审核。AI 查询时默认 `min_confidence=INFERRED` 过滤掉 AMBIGUOUS（由调用方决定，不在 API 层硬编码）。
- **置信度枚举**：在 `backend/app/models/graph_index.py` 中定义 `ConfidenceLevel(str, Enum)` 枚举，避免魔术字符串。
- **LLM 输出不稳定性**：LLM 可能返回不在枚举范围内的 confidence 值。解析时若无法映射到三级枚举，默认标注为 `AMBIGUOUS`，并用 structlog 记录 warning。

### Project Structure Notes

- 修改（不新建）：`backend/app/services/graphify_service.py`
- 修改（不新建）：`backend/app/models/graph_index.py`
- 修改（不新建）：`backend/app/prompts/graphify_extract.jinja2`
- 修改（不新建）：`backend/app/api/v1/endpoints/graphify.py`
- 新增测试：`backend/tests/unit/test_confidence_annotation.py`
- 新增测试：`backend/tests/integration/test_graphify_query_filter.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4.3] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR18] — 原始需求（三级置信度）
- [Source: 4-2-graphify-relation-extraction.md] — Story 4.2 依赖，graph.json 结构定义
- [Source: backend/app/services/rag_service.py] — service 风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证三级置信度存储在 graph.json** (AC: #1)
   - 触发一次全量 Graphify 提取（同 Story 4.2 UAT 步骤 1）
   - 用文本编辑器打开 `vault/_graphify/graph.json`
   - 搜索"confidence_level"字段
   - 应看到不同关系对应不同值：`EXTRACTED`、`INFERRED` 或 `AMBIGUOUS`
   - 如果所有关系的 confidence_level 都相同（如全是 EXTRACTED），可能是标注逻辑未生效，记录 Story 4.3

2. **验证按置信度过滤查询** (AC: #2)
   - 访问 `http://localhost:8001/api/v1/graphify/query?concept_name=<概念名>&min_confidence=EXTRACTED`
   - 返回结果中所有关系的 `confidence_level` 应为 `EXTRACTED`，不应出现 `INFERRED` 或 `AMBIGUOUS`
   - 访问同一 URL 但去掉 `min_confidence` 参数，结果应比之前多（包含了所有置信度）
   - 如果过滤后仍出现其他置信度，记录 Story 4.3

3. **验证增量更新后置信度刷新** (AC: #4)
   - 修改 vault 中一篇笔记（例如修改对某个概念的描述，使关系描述更明确）
   - 触发增量提取
   - 查询该笔记中的概念关系，检查 confidence_level 是否随修改后的内容更新
   - 未修改的其他笔记的关系应保持不变
   - 如果未修改笔记的置信度发生了变化，记录 Story 4.3

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-4.3.1 | pytest | `.venv/bin/pytest tests/unit/test_confidence_annotation.py -x -q` | 0 failed |
| CP-4.3.2 | pytest | `.venv/bin/pytest tests/integration/test_graphify_query_filter.py -x -q` | 0 failed |
| CP-4.3.3 | pytest | `.venv/bin/pytest tests/ -k "confidence" -x -q` | 0 failed |

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
- Depends on: [[4.2]]
