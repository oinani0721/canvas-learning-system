---
doc_type: story
story_id: "4.1"
epic_id: "EPIC-4"
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

# Story 4.1: 新概念提取 + wikilink 双向链接创建

## Story

As a 学习者,
I want 从对话或考察中提取新概念，系统自动创建带 [[wikilink]] 双向链接的 .md 文件,
so that 我的知识图谱随学习过程自动扩展。

## Acceptance Criteria

1. **Given** 学习者在对话或考察中识别到一个新概念
   **When** 学习者选中文本并触发"提取概念"（MCP 工具 `extract_concept`）
   **Then** 系统创建新 .md 文件，文件名为概念名
   **And** 新文件自动填入 Templater 标准 frontmatter（mastery_score、bkt_params、fsrs_params 等）
   **And** 在原笔记中插入 `[[新概念]]` wikilink
   **And** 在新文件中插入 `[[原笔记]]` 反向链接

2. **Given** 同名概念文件已存在于 vault
   **When** 学习者触发"提取概念"
   **Then** 系统不重复创建文件
   **And** 仅在原笔记中插入指向已有文件的 `[[新概念]]` wikilink
   **And** 在已有文件的末尾追加 `[[原笔记]]` 反向链接（不覆盖现有内容）

3. **Given** 新概念文件创建完成
   **When** 检查双向链接完整性
   **Then** 原笔记的 wikilink 解析可到达新文件（obsidiantools 图可遍历）
   **And** 新文件的反向链接解析可到达原笔记

## Tasks / Subtasks

- [ ] Task 1: 实现 `extract_concept` MCP 工具后端端点 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/api/v1/endpoints/` 创建 `concept_extraction.py`，定义 `POST /api/v1/concepts/extract` 端点
  - [ ] 1.2 接收参数：`concept_name: str`、`source_note_path: str`、`vault_root: str`
  - [ ] 1.3 检查 `vault_root / concept_name.md` 是否已存在；存在时跳过创建，仅追加反向链接
  - [ ] 1.4 不存在时：用 Templater 标准 frontmatter schema 生成新文件内容，写入 vault

- [ ] Task 2: 实现双向链接注入逻辑 (AC: #1, #2, #3)
  - [ ] 2.1 在 `backend/app/services/` 创建 `wikilink_service.py`
  - [ ] 2.2 实现 `insert_wikilink(note_path, concept_name)` — 在原笔记末尾（或指定位置）插入 `[[concept_name]]`
  - [ ] 2.3 实现 `append_backlink(concept_path, source_note_name)` — 在概念文件末尾追加 `[[source_note_name]]` 反向链接
  - [ ] 2.4 保证写操作原子性：先写新文件，再修改原笔记，任一失败均回滚（NFR-INT-1）

- [ ] Task 3: 注册 MCP 工具 (AC: #1)
  - [ ] 3.1 在 `backend/app/mcp/tools.py` 注册 `extract_concept` 工具定义（名称、描述、参数 schema）
  - [ ] 3.2 工具描述需清晰说明触发时机：学习者在 Claudian 对话/考察中选中文本后调用

- [ ] Task 4: 编写测试 (AC: #1, #2, #3)
  - [ ] 4.1 单元测试：`tests/unit/test_wikilink_service.py` — 验证 insert_wikilink / append_backlink 逻辑
  - [ ] 4.2 集成测试：`tests/integration/test_concept_extraction.py` — 验证端到端文件创建 + 双向链接
  - [ ] 4.3 边界测试：同名文件已存在时不重复创建，仅追加链接

## Dev Notes

- **frontmatter 安全**：新文件写入必须使用与 Story 1.1 相同的 Templater frontmatter schema（`docs/_meta/FRONTMATTER-SPEC.md`）。不可使用自定义字段名。
- **wikilink 格式**：Obsidian 接受 `[[文件名]]`（无扩展名）。写入时去掉 `.md` 后缀。
- **反向链接位置**：追加到文件末尾的 `## 来源` section 下（如 section 不存在则创建）。保持笔记正文不被污染。
- **原子性保证**：使用 Python `tempfile` + `os.replace` 原子写文件；若注入原笔记 wikilink 失败，删除已创建的概念文件（回滚）。
- **NFR-INT-1**：frontmatter 字段写入必须使用 `python-frontmatter` 库解析后再写，不可直接字符串拼接，防止 YAML 损坏。

### Project Structure Notes

- 新端点：`backend/app/api/v1/endpoints/concept_extraction.py`
- 新 service：`backend/app/services/wikilink_service.py`
- MCP 工具注册：`backend/app/mcp/tools.py`
- 测试：`backend/tests/unit/test_wikilink_service.py`、`backend/tests/integration/test_concept_extraction.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4.1] — AC 和 FR 映射
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — frontmatter 字段完整定义
- [Source: backend/app/services/rag_service.py] — 后端 service 风格参考
- [Source: backend/app/api/v1/endpoints/canvas.py] — 后端 router 风格参考
- [Source: _bmad-output/planning-artifacts/prd.md#FR15] — 原始需求

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证新概念文件创建** (AC: #1)
   - 打开 Obsidian，进入一篇笔记（例如"微积分.md"）
   - 在 Claudian 对话窗口中，选中"极限"这个词，点击"提取概念"按钮
   - 在 vault 文件列表中，应该看到一个新建的"极限.md"文件
   - 打开"极限.md"，顶部应该有 `---` 包裹的元数据区域（含 mastery_score 等字段）
   - 文件底部应该有 `[[微积分]]` 反向链接
   - 如果没有看到新文件或反向链接，记录 Story 4.1 和实际情况

2. **验证原笔记插入 wikilink** (AC: #1)
   - 回到"微积分.md"
   - 文件中应该出现 `[[极限]]` 链接（可点击跳转到极限.md）
   - 如果链接不存在或点击无法跳转，记录 Story 4.1

3. **验证同名概念不重复创建** (AC: #2)
   - 在另一篇笔记（例如"函数.md"）中再次提取"极限"
   - 不应该创建第二个"极限.md"
   - "极限.md"底部应追加了 `[[函数]]` 反向链接（不覆盖原有内容）
   - "函数.md"中应出现 `[[极限]]` wikilink
   - 如果出现第二个"极限.md"或原有内容被覆盖，记录 Story 4.1

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-4.1.1 | pytest | `.venv/bin/pytest tests/unit/test_wikilink_service.py -x -q` | 0 failed |
| CP-4.1.2 | pytest | `.venv/bin/pytest tests/integration/test_concept_extraction.py -x -q` | 0 failed |
| CP-4.1.3 | pytest | `.venv/bin/pytest tests/ -k "concept" -x -q` | 0 failed |

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
