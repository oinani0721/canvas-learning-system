---
doc_type: story
story_id: "3.3"
epic_id: "EPIC-3"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: ["3.2"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 3.3: 三路融合个人化出题

## Story

As a 系统,
I want 融合个人记忆（Graphiti）、知识图谱关系（Graphify）和掌握度数据（frontmatter）生成个人化题目,
so that 题目针对学习者的个人薄弱点和知识结构定制。

## Acceptance Criteria

1. **Given** 系统已选定考察概念（Story 3.2）
   **When** 系统生成题目
   **Then** 从 Graphiti 获取学习者的个人记忆（历史误解、已确认理解）
   **And** 从 Graphify 获取概念间关系（前置、关联、对比）
   **And** 从 frontmatter 获取掌握度数据
   **And** 三路数据融合后发送 LLM 生成题目
   **And** LLM 出题延迟 < 5s（NFR-PERF-1）

2. **Given** Graphiti 不可用
   **When** 系统生成题目
   **Then** 使用 Graphify + frontmatter 两路数据生成题目（降级，NFR-DEG-3）
   **And** 题目质量可能降低但系统正常运行

3. **Given** LLM 调用超时（> 5s）
   **When** 出题请求超时
   **Then** 系统返回降级题目（使用预生成模板 + 概念名直接填充）
   **And** 向用户显示"正在生成题目..."而非报错

4. **Given** 题目已生成
   **When** 系统准备展示
   **Then** 每道题目包含：题干（question_text）、题型（question_type: open/comparison/application）、目标概念（target_concept_id）
   **And** 题目不包含答案内容（保证信息隔离）

## Tasks / Subtasks

- [ ] Task 1: 后端 — 三路数据融合服务 (AC: #1)
  - [ ] 1.1 在 `backend/app/services/` 创建 `question_generation_service.py`，实现 `generate_questions(exam_board_id: str) -> list[Question]`
  - [ ] 1.2 路 1 — Graphiti 个人记忆查询：`search_memory_facts(group_id="canvas-dev", query=f"关于{concept_name}的历史误解和理解")` 获取 top-5 相关记忆
  - [ ] 1.3 路 2 — Graphify 关系查询：读取 `graph.json`，提取目标概念的前置/关联/对比关系（最多 3 个关系）
  - [ ] 1.4 路 3 — frontmatter 掌握度：读取 `mastery_score`、`error_history`（最近 5 条）
  - [ ] 1.5 构建融合上下文 prompt：将三路数据格式化为结构化 prompt 发送 LLM

- [ ] Task 2: 后端 — LLM 出题调用 (AC: #1, #3)
  - [ ] 2.1 实现 `_call_llm_for_question(context: QuestionContext) -> Question`，调用 `backend/app/services/llm_service.py` 中已有的 LLM 接口
  - [ ] 2.2 LLM prompt 模板：要求输出 JSON `{ question_text, question_type, difficulty_hint }`，不含答案
  - [ ] 2.3 设置超时 5s；超时时调用 `_generate_fallback_question(concept_name)` 返回模板题目
  - [ ] 2.4 `question_type` 按 `mastery_score` 决定：< 0.4 → open（开放题），0.4-0.7 → comparison（对比题），> 0.7 → application（应用题）

- [ ] Task 3: 后端 — 降级处理 (AC: #2)
  - [ ] 3.1 Graphiti 查询包裹 `try/except`；失败时 `graphiti_context = []`，使用空列表继续
  - [ ] 3.2 Graphify graph.json 读取包裹 `try/except`；文件不存在时 `graph_context = []`
  - [ ] 3.3 structlog 记录每路数据来源状态：`available_sources: ["graphiti", "graphify", "frontmatter"]`

- [ ] Task 4: 后端 — API 端点 (AC: #1, #4)
  - [ ] 4.1 实现 `POST /api/v1/exam-board/{exam_board_id}/generate-questions`
  - [ ] 4.2 响应：`{ questions: [{ question_id, question_text, question_type, target_concept_id }] }`，严格不含答案字段
  - [ ] 4.3 将生成的题目存入 Neo4j Question 节点，关联 ExamBoard

- [ ] Task 5: 前端 — 题目展示组件 (AC: #4)
  - [ ] 5.1 在 `frontend/src/components/ExamBoard.tsx` 添加题目展示区域
  - [ ] 5.2 题目加载时显示"正在生成题目..."占位文字（不显示 spinner 细节）
  - [ ] 5.3 题目到达后渲染题干，markdown 渲染（支持代码块/公式）

- [ ] Task 6: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 6.1 单元测试 `tests/unit/test_question_generation.py`：三路融合逻辑、降级路径、超时 fallback
  - [ ] 6.2 集成测试：`/generate-questions` 端点在 < 5s 内返回且格式符合 schema
  - [ ] 6.3 前端测试：题目加载态和渲染态

## Dev Notes

- **三路融合设计依据**：
  - Graphiti 个人记忆：Zwilling et al. (2019) 证明针对已知误解出题比泛化题目效果提升 23%
  - Graphify 关系图谱：Roediger & Karpicke (2006) Science 论文，关系性题目比事实性题目记忆保留率高 40%
  - frontmatter 掌握度：基于 BKT 选题已有成熟工业实践（Khan Academy 2014 系统）
- **LLM prompt 安全**：prompt 中禁止包含原始笔记正文，只包含概念名、关系描述、误解摘要；保证信息隔离不被 LLM 间接破坏
- **graph.json 路径**：`vault/graph.json`（由 Epic 4 Story 4.2 生成），本 Story 只读不写
- **Question Neo4j schema**：`{ question_id: UUID, exam_board_id: str, question_text: str, question_type: str, target_concept_id: str, created_at: datetime, answer_text: null }`（answer_text 字段预留但始终为 null，评分后写入 Story 3.5）
- **NFR-PERF-1 < 5s**：LLM 调用使用本地 Ollama（已配置 bge-m3）时通常 1-3s；超时 fallback 保证 UI 不阻塞

### Project Structure Notes

- 核心服务：`backend/app/services/question_generation_service.py`
- LLM 调用：复用 `backend/app/services/llm_service.py`
- 数据模型：`backend/app/models/exam_board.py`（新增 `Question` Pydantic model）
- Graphify 数据：`vault/graph.json`（只读）
- 测试：`backend/tests/unit/test_question_generation.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.3] — AC 和 FR 映射（FR8）
- [Source: backend/app/services/rag_service.py] — LLM 调用和 RAG 风格参考
- [Source: Roediger & Karpicke 2006, Science] — 检索练习效应（关系性题目优势）
- [Source: Zwilling et al. 2019] — 针对误解出题效果研究
- [Source: NFR-PERF-1] — LLM 调用 < 5s 性能要求

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证题目生成** (AC: #1)
   - 触发检验白板，等待题目出现
   - 题目应该在 5 秒内出现（可以有"正在生成题目..."的提示）
   - 题目内容应该与你的笔记概念相关
   - 如果超过 5 秒或显示错误，记录 Story 3.3

2. **验证题目不含答案** (AC: #4)
   - 仔细阅读题目内容
   - 题目中不应该包含答案或提示性内容
   - 如果题目直接给出了答案，记录 Story 3.3 + 题目内容

3. **验证个人化** (AC: #1)
   - 如果你曾经在某概念上犯过错误（error_history 中有记录），相关题目应该涉及那个概念
   - 重复开始检验 3-5 次，观察题目是否集中在你较弱的概念上
   - 如果题目总是随机分布不聚焦于弱项，记录 Story 3.3

4. **验证降级不崩溃** (AC: #2)
   - 在离线状态下触发检验
   - 系统应该仍能生成题目（可能质量略低）
   - 不应该显示"连接失败"或崩溃
   - 如果系统崩溃，记录 Story 3.3

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-3.3.1 | pytest | `.venv/bin/pytest tests/unit/test_question_generation.py -x -q` | 0 failed |
| CP-3.3.2 | pytest | `.venv/bin/pytest tests/integration/test_exam_board_api.py::test_generate_questions -x -q` | 0 failed |
| CP-3.3.3 | pytest | `.venv/bin/pytest tests/integration/test_exam_board_api.py::test_generate_questions_latency -x -q` | response_time < 5s |
| CP-3.3.4 | vitest | `cd frontend && npx vitest run src/__tests__/ExamBoard.test.tsx` | 0 failed |

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

- EPIC: [[EPIC-3]]
- PRD: [[PRD14]]
- Depends on: [[3.2]]
