---
doc_type: story
story_id: "6.5"
epic_id: "EPIC-6"
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

# Story 6.5: Callout 批注驱动快速考察

## Story

As a 学习者,
I want 基于笔记中的 callout 批注触发快速考察,
so that 我可以在阅读笔记时随时对标注的重点进行自测。

## Acceptance Criteria

1. **Given** 笔记中有 `> [!quiz]` 或 `> [!test]` callout 批注
   **When** 学习者点击 callout 旁的快速考察按钮或执行快速考察命令
   **Then** 系统基于 callout 内容生成 1-3 道快速题目
   **And** 题目在当前笔记旁以侧边栏或浮层形式展示（不创建完整检验白板）
   **And** 评分结果同样写入当前笔记的 frontmatter

2. **Given** 笔记中有多个 callout 批注
   **When** 学习者触发快速考察
   **Then** 仅对当前光标所在位置最近的一个 callout 生成题目
   **And** 如果光标不在任何 callout 附近（距离 > 10 行），提示选择一个 callout

3. **Given** callout 内容极短（少于 20 字）
   **When** 系统生成题目
   **Then** 自动扩展上下文：读取该 callout 所在段落的前后各 3 段作为补充上下文
   **And** 基于扩展上下文生成题目（而非直接基于 20 字内容）

4. **Given** 检验白板隔离失败（NFR-DEG-5）
   **When** 系统检测到降级场景
   **Then** 自动退回到 callout 快速考察模式作为降级路径
   **And** 学习者看到通知："检验白板暂时不可用，已切换到快速考察模式"

5. **Given** 快速考察题目展示完毕
   **When** 学习者提交答案
   **Then** 评分后 frontmatter 更新：`mastery_score` 按 BKT 更新，`error_history` 追加（如有错误）
   **And** 快速考察不触发 Graphiti 异步写入（轻量模式，不写入长期记忆）

## Tasks / Subtasks

- [ ] Task 1: 后端 — 快速题目生成 API (AC: #1, #3)
  - [ ] 1.1 在 `backend/app/api/v1/endpoints/` 创建 `quick_exam.py` endpoint
  - [ ] 1.2 实现 `POST /api/v1/quiz/quick` — 接收 `{callout_content: str, context_paragraphs: list[str], concept_id: str}`
  - [ ] 1.3 当 `len(callout_content) < 20` 时，将 `context_paragraphs` 并入生成上下文
  - [ ] 1.4 调用 LLM 生成 1-3 道题目，题目类型为简答或判断题（适合快速作答）
  - [ ] 1.5 返回 schema：`{questions: [{id, question_text, question_type, callout_ref}]}`

- [ ] Task 2: 前端 — Callout 识别与触发 (AC: #1, #2)
  - [ ] 2.1 在 Obsidian 插件中注册 `quiz_from_callout` 命令（绑定 hotkey，与 FR37 hotkey 系统集成）
  - [ ] 2.2 命令触发时扫描当前编辑器：找到光标位置最近的 `[!quiz]` 或 `[!test]` callout
  - [ ] 2.3 距离 > 10 行时，用 `new Notice("请将光标移近一个 [!quiz] 或 [!test] callout")` 提示
  - [ ] 2.4 提取 callout 内容和前后 3 段段落，调用 MCP tool `quick_exam_generate`

- [ ] Task 3: 前端 — 快速考察 UI (AC: #1, #4)
  - [ ] 3.1 使用 Obsidian Modal 创建快速考察弹窗（`QuickExamModal extends Modal`）
  - [ ] 3.2 Modal 内展示题目列表（1-3 道），每题下方有 markdown 文本区域供输入答案
  - [ ] 3.3 "提交" 按钮调用评分 API，在 Modal 内显示评分结果（不跳转页面）
  - [ ] 3.4 降级通知：在 `onload` 中监听 quiz_board_failed 事件，触发时用 Notice 通知并自动调用 `quiz_from_callout`

- [ ] Task 4: 后端 — 快速考察评分与 frontmatter 写入 (AC: #5)
  - [ ] 4.1 复用 `backend/app/services/scoring_service.py` 的现有评分逻辑（轻量版：单维度评分）
  - [ ] 4.2 评分后更新 frontmatter：BKT mastery_score 更新（调用现有 `update_bkt_params()`）
  - [ ] 4.3 有错误时追加 `error_history`，错误类型由 LLM 自动分类（简化为 conceptual/recall 二分）
  - [ ] 4.4 明确**跳过** Graphiti 写入（快速考察为轻量模式，添加 `skip_graphiti=True` 标志）
  - [ ] 4.5 在 MCP server 中注册 `quick_exam_generate` 和 `quick_exam_submit` tools

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4, #5)
  - [ ] 5.1 `tests/unit/test_quick_exam_generation.py` — 验证短内容自动扩展上下文逻辑
  - [ ] 5.2 `tests/unit/test_callout_detection.py` — 验证光标距离判断和 callout 提取逻辑
  - [ ] 5.3 `tests/unit/test_quick_exam_no_graphiti.py` — 验证 skip_graphiti=True 时 Graphiti 写入被跳过
  - [ ] 5.4 `tests/integration/test_quick_exam_flow.py` — 端到端验证从 callout 到评分到 frontmatter 更新

## Dev Notes

- **轻量模式设计原则**：快速考察是"随手一测"，不需要完整检验白板的所有功能（无 4 级提示、无 FSRS 全量更新、无 Graphiti 写入）。保持轻量是设计决策
- **Obsidian Modal**：使用 `app.workspace.openModal()` 或直接 `new QuickExamModal(app).open()`。Modal 不阻塞编辑器，用户可以随时关闭
- **callout 检测正则**：`/^>\s*\[!(quiz|test)\]/m` 匹配 `[!quiz]` 和 `[!test]`（大小写不敏感）
- **前后 3 段扩展**：按空行分段（`\n\n` 分隔），不跨越标题（`## ` 开头的行作为段落边界）
- **降级路径（AC #4）**：NFR-DEG-5 规定检验白板隔离失败时退回快速考察。触发条件由检验白板 Story（Epic 3）发出事件，本 Story 只需监听并响应

### Project Structure Notes

- 后端 endpoint：`backend/app/api/v1/endpoints/quick_exam.py`（新建）
- MCP tools：`backend/app/mcp_server/tools/quick_exam_tools.py`（新建）
- 前端 Modal：`frontend/src/components/QuickExamModal.ts`（新建）
- Hotkey 集成：`frontend/src/commands/index.ts`（注册 `quiz_from_callout` 命令）
- 参考 Modal 实现：现有 `QuizBoard` 相关组件（Epic 3 实现）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.5] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#FR13] — FR13 callout 批注考察
- [Source: _bmad-output/planning-artifacts/prd.md#NFR-DEG-5] — 检验白板隔离失败降级路径
- [Source: _bmad-output/planning-artifacts/prd.md#FR37] — FR37 hotkey 自定义系统（命令注册）
- [Source: backend/app/api/v1/endpoints/canvas.py] — endpoint 风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证 callout 触发快速考察** (AC: #1)
   - 打开一个有 `> [!quiz]` 或 `> [!test]` 批注的笔记
   - 将光标移到该批注附近
   - 按快捷键（或命令面板执行"快速考察"命令）
   - 应该弹出一个小窗口，显示 1-3 道基于批注内容的题目
   - 如果没有弹出窗口，记录 Story 6.5

2. **验证只对最近的 callout 出题** (AC: #2)
   - 在有多个 callout 的笔记中，光标放在第二个 callout 旁
   - 触发快速考察
   - 题目应该基于第二个 callout 的内容，而不是第一个
   - 如果题目内容来自错误的 callout，记录 Story 6.5

3. **验证短内容自动扩展** (AC: #3)
   - 创建一个只有不到 20 个字的 callout（例如 `> [!quiz]\n> 解释递归`）
   - 触发快速考察
   - 题目应该比 callout 本身更丰富（AI 会基于周围段落生成题目）
   - 如果题目过于简单只针对 20 字内容，记录 Story 6.5

4. **验证评分后 frontmatter 更新** (AC: #5)
   - 完成一次快速考察并提交答案
   - 打开笔记顶部的元数据区域（切换到源码模式查看）
   - 应该看到 `mastery_score` 有所变化
   - 如果答错了，`error_history` 列表里应该新增一条记录
   - 如果没有变化，记录 Story 6.5

5. **验证降级模式通知** (AC: #4)
   - （此验证项由 QA 团队在检验白板功能失效时模拟测试）
   - 应该看到通知："检验白板暂时不可用，已切换到快速考察模式"

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-6.5.1 | pytest | `.venv/bin/pytest tests/unit/test_quick_exam_generation.py -x -q` | 0 failed |
| CP-6.5.2 | pytest | `.venv/bin/pytest tests/unit/test_callout_detection.py -x -q` | 0 failed |
| CP-6.5.3 | pytest | `.venv/bin/pytest tests/unit/test_quick_exam_no_graphiti.py -x -q` | 0 failed |
| CP-6.5.4 | pytest | `.venv/bin/pytest tests/integration/test_quick_exam_flow.py -x -q` | 0 failed |

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

- EPIC: [[EPIC-6]]
- PRD: [[PRD14]]
