---
doc_type: story
story_id: "5.4"
aliases: ["5.4"]
epic_id: "EPIC-5"
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
# Story 5.4: 错误 4 类分类 + 双写存储

## Story

As a 系统,
I want 记录学习者的错误并按 4 类自动分类存储（双写到 frontmatter + Graphiti）,
so that 系统可以针对不同类型的错误提供差异化补救。

## Acceptance Criteria

1. **Given** 学习者答错一道题
   **When** 系统记录错误
   **Then** 自动分类为 4 类之一：概念性错误 / 程序性错误 / 粗心错误 / 知识空白（AR3）
   **And** 错误记录双写：frontmatter error_history 数组 + Graphiti episode
   **And** 每类错误关联差异化补救路由（AR3）

2. **Given** frontmatter 写入成功但 Graphiti 写入失败
   **When** 双写操作部分失败
   **Then** 不回滚 frontmatter 写入（frontmatter 是主存储）
   **And** Graphiti 写入进入异步重试队列（最多 3 次，详见 Story 5.8）
   **And** 错误分类结果对用户透明（不因 Graphiti 失败而卡住）

3. **Given** AI 无法确定错误类型
   **When** 分类置信度低于阈值（0.6）
   **Then** 默认归类为"知识空白"
   **And** 在错误记录中标注 `classification_confidence: low`

4. **Given** 错误已记录
   **When** 差异化补救路由触发
   **Then** 概念性错误 → 生成对比辨析题；程序性错误 → 生成步骤分解练习；粗心错误 → 标记提示"检查细节"；知识空白 → 触发概念讲解

## Tasks / Subtasks

- [ ] Task 1: 定义错误 4 类数据模型 (AC: #1, #3)
  - [ ] 1.1 在 `backend/app/schemas/error_record.py` 定义 `ErrorCategory` enum：`CONCEPTUAL = "conceptual"`, `PROCEDURAL = "procedural"`, `CARELESS = "careless"`, `KNOWLEDGE_GAP = "knowledge_gap"`
  - [ ] 1.2 定义 `ErrorRecord` Pydantic 模型：`note_id: str, question_id: str, category: ErrorCategory, error_description: str, classification_confidence: float, timestamp: datetime, remediation_triggered: bool`
  - [ ] 1.3 定义 `RemediationRoute` enum：`CONTRASTIVE_QUIZ`, `STEP_DECOMPOSITION`, `DETAIL_CHECK`, `CONCEPT_EXPLANATION`
  - [ ] 1.4 定义 `CATEGORY_TO_REMEDIATION` 映射字典

- [ ] Task 2: AI 错误分类服务 (AC: #1, #3)
  - [ ] 2.1 在 `backend/app/services/error_classification_service.py` 实现 `classify_error(question: str, student_answer: str, correct_answer: str, llm_client) -> tuple[ErrorCategory, float]`
  - [ ] 2.2 分类 prompt 模板（结构化输出）：输入题目+学生答案+正确答案，输出 JSON `{"category": "...", "confidence": 0.0-1.0, "reason": "..."}`
  - [ ] 2.3 置信度 < 0.6 时回退到 `KNOWLEDGE_GAP`（AC #3 规则）
  - [ ] 2.4 使用 `backend/app/services/llm_service.py` 中的已有 LLM 客户端（不新建连接）

- [ ] Task 3: frontmatter error_history 写入 (AC: #1, #2)
  - [ ] 3.1 扩展 `backend/app/services/frontmatter_service.py`：`append_error_record(note_path: str, record: ErrorRecord) -> None`
  - [ ] 3.2 error_history 是数组，每次 append（不是覆盖），最多保留最近 50 条（超出时删除最旧的）
  - [ ] 3.3 写入仍使用原子写（tempfile + rename）保证 NFR-INT-1
  - [ ] 3.4 每条记录的序列化格式：`{category, confidence, timestamp, note_id, question_id}`（不存储完整答案避免 frontmatter 膨胀）

- [ ] Task 4: Graphiti episode 写入 (AC: #1, #2)
  - [ ] 4.1 在 `backend/app/services/graphiti_service.py` 实现 `write_error_episode(record: ErrorRecord) -> None`（异步方法）
  - [ ] 4.2 episode 内容格式：`"学习者在[note_id]犯了[category]错误：[error_description]"`
  - [ ] 4.3 Graphiti 写入失败时加入 AsyncQueue（Story 5.8 机制），不抛出异常到调用方
  - [ ] 4.4 写入成功后 Graphiti episode UUID 反写到 frontmatter 对应记录的 `graphiti_episode_id` 字段

- [ ] Task 5: 差异化补救路由 (AC: #4)
  - [ ] 5.1 在 `backend/app/services/error_classification_service.py` 实现 `get_remediation_route(category: ErrorCategory) -> RemediationRoute`
  - [ ] 5.2 在 `POST /api/v1/mastery/record-error` 端点响应中包含 `remediation_route: RemediationRoute`
  - [ ] 5.3 前端根据 remediation_route 决定显示哪种补救 UI（前端实现在 Epic 4 Story 中）
  - [ ] 5.4 补救路由的具体 prompt 模板存储在 `backend/app/prompts/remediation/` 目录（4 个文件对应 4 类）

- [ ] Task 6: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 6.1 `tests/unit/test_error_classification.py`：验证 4 类分类的 prompt 输出解析（用固定 LLM 输出 fixture）
  - [ ] 6.2 `tests/unit/test_error_fallback.py`：验证置信度 < 0.6 时回退到 KNOWLEDGE_GAP
  - [ ] 6.3 `tests/unit/test_error_dual_write.py`：验证 Graphiti 失败时 frontmatter 写入不回滚
  - [ ] 6.4 `tests/integration/test_record_error_endpoint.py`：端到端验证 POST 错误记录流程

## Dev Notes

- **4 类分类依据**：VanLehn (1990) "Mind Bugs: The Origins of Procedural Misconceptions" 区分程序性/概念性；Careless 错误来自 Clements (1980) "Careless errors and systematic errors"
- **双写策略**：frontmatter 是主存储（快速、本地），Graphiti 是关系推理层（支持 Story 5.7 的图谱检索）。两者均成功才算完整，但 frontmatter 失败才是关键错误
- **AR3 补救路由**：AR3 定义了 4 类错误的补救差异，本 Story 实现路由层，具体题目生成由 Epic 4 负责
- **LLM 分类提示词**：需要 few-shot 示例确保稳定输出。每类错误至少 2 个示例（共 8 个 few-shot examples 写入 prompt 模板）
- **error_history 大小限制**：50 条是平衡 frontmatter 大小和历史深度的保守值；可通过配置调整

### Project Structure Notes

- 分类服务：`backend/app/services/error_classification_service.py`（新建）
- Graphiti 写入：`backend/app/services/graphiti_service.py`（已存在，扩展 write_error_episode）
- frontmatter 扩展：`backend/app/services/frontmatter_service.py`（扩展 append_error_record）
- Pydantic 模型：`backend/app/schemas/error_record.py`（新建）
- 补救 prompt：`backend/app/prompts/remediation/`（新建目录 + 4 个文件）
- API 端点：`backend/app/api/v1/endpoints/mastery.py`（新增 /record-error）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.4] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR23] — 错误分类需求
- [Source: _bmad-output/planning-artifacts/prd.md#AR3] — 差异化补救路由规则
- [Story: 5.8] — 异步重试队列机制

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证答错后看到错误类型标签** (AC: #1)
   - 答错一道题后，系统评分界面应该显示错误类型（例如："这是一个概念理解错误" 或 "看起来是粗心导致的错误"）
   - 如果没有看到错误类型说明，记录 Story 5.4

2. **验证错误分类影响后续建议** (AC: #4)
   - 观察答错后系统给出的建议或练习类型
   - "概念性错误"应出现对比辨析题
   - "粗心错误"应出现"检查细节"提醒而不是出新题
   - 如果所有错误都给出相同建议，记录 Story 5.4

3. **验证错误记录写入笔记** (AC: #1)
   - 答错后打开对应概念笔记
   - frontmatter 的 `error_history` 数组应该新增一条记录，包含分类和时间戳
   - 如果 `error_history` 为空或没有更新，记录 Story 5.4

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-5.4.1 | pytest | `.venv/bin/pytest tests/unit/test_error_classification.py -x -q` | 0 failed |
| CP-5.4.2 | pytest | `.venv/bin/pytest tests/unit/test_error_fallback.py -x -q` | 0 failed |
| CP-5.4.3 | pytest | `.venv/bin/pytest tests/unit/test_error_dual_write.py -x -q` | 0 failed |
| CP-5.4.4 | pytest | `.venv/bin/pytest tests/integration/test_record_error_endpoint.py -x -q` | 0 failed |

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

- EPIC: [[EPIC-5]]
- PRD: [[PRD14]]
