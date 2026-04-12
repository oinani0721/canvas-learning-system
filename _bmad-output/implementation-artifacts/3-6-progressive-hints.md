---
doc_type: story
story_id: "3.6"
epic_id: "EPIC-3"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: ["3.4"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 3.6: 4 级渐进提示

## Story

As a 学习者,
I want 在答不出时请求 4 级渐进提示（方向 → 关键词 → 框架 → 脚手架）,
so that 我可以在不同程度的帮助下逐步找到答案。

## Acceptance Criteria

1. **Given** 学习者正在作答一道题目
   **When** 学习者点击"提示"按钮
   **Then** 系统按顺序给出 4 级渐进提示：
     - 级别 1：方向提示（指明思考方向，不给具体内容）
     - 级别 2：关键词提示（给出核心关键词）
     - 级别 3：框架提示（给出答案框架/结构）
     - 级别 4：脚手架提示（给出接近完整的答案骨架）
   **And** 每次点击只展示下一级，不跳级

2. **Given** 学习者已使用了提示
   **When** 评分时
   **Then** 提示使用次数记录在 frontmatter `hint_count` 字段中
   **And** `hint_count` 纳入后续掌握度计算参考（不直接扣分，只作为信号）

3. **Given** 学习者已到达第 4 级提示（脚手架）
   **When** 学习者再次点击"提示"
   **Then** 按钮变为禁用状态，文字改为"已达最高提示级别"
   **And** 不产生额外 LLM 调用

4. **Given** 学习者已提交答案（编辑器只读）
   **When** 学习者查看提示区域
   **Then** 提示按钮隐藏（提交后不可再请求提示）

## Tasks / Subtasks

- [ ] Task 1: 后端 — 4 级提示生成 (AC: #1)
  - [ ] 1.1 在 `backend/app/services/hint_service.py` 实现 `generate_hint(question_id: str, hint_level: int) -> HintResult`（`hint_level` 1-4）
  - [ ] 1.2 4 级提示的 LLM prompt 模板（各级别严格差异化）：
    - 级别 1：`"给出一个方向性提示，不超过 1 句话，不提及具体内容，只指明思考方向"`
    - 级别 2：`"给出 2-3 个核心关键词，不给出解释"`
    - 级别 3：`"给出答案的结构框架（如步骤/要点列表），不填写内容"`
    - 级别 4：`"给出一个接近完整的答案骨架，学习者只需填入细节"`
  - [ ] 1.3 `HintResult`：`{ hint_id, hint_level, hint_text, question_id, generated_at }`
  - [ ] 1.4 实现 `POST /api/v1/exam-board/{exam_board_id}/hint`：接收 `{ question_id, hint_level }`，返回 `HintResult`

- [ ] Task 2: 后端 — 提示使用记录 (AC: #2)
  - [ ] 2.1 每次成功返回提示时，在 Neo4j 中记录 HintUsage 节点：`{ answer_id, hint_level, used_at }`
  - [ ] 2.2 评分完成后，`autoscore_service.py` 读取本次答题的 hint_count（HintUsage 节点数量）
  - [ ] 2.3 在 frontmatter 原子写入（Story 3.5）时，追加 `hint_count: N` 到当次 error_history 条目中

- [ ] Task 3: 前端 — 提示按钮与渐进展示 (AC: #1, #3, #4)
  - [ ] 3.1 在 `ExamBoard.tsx` 中添加"提示"按钮，位于答案编辑器旁（不遮挡编辑区）
  - [ ] 3.2 在 `exam-board-store.ts` 添加：`currentHintLevel: 0`（0 = 未使用），`hints: HintResult[]`（累积展示）
  - [ ] 3.3 点击"提示"时：`currentHintLevel += 1`，调用后端 `/hint` API，将返回的提示 append 到 `hints` 数组
  - [ ] 3.4 前端累积展示：之前级别的提示保持可见，新提示追加到下方（不替换）
  - [ ] 3.5 `currentHintLevel >= 4` 时：按钮 `disabled = true`，文字改为"已达最高提示级别"
  - [ ] 3.6 `answerEditorMode === "readonly"` 时隐藏提示按钮

- [ ] Task 4: 前端 — HintDisplay 组件 (AC: #1)
  - [ ] 4.1 创建 `frontend/src/components/HintDisplay.tsx`，接收 `hints: HintResult[]` 渲染
  - [ ] 4.2 每条提示用不同样式区分级别（级别 1 最淡，级别 4 最明显）
  - [ ] 4.3 提示内容支持 markdown 渲染（复用 AnswerEditor 的 markdown 渲染器）

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 后端单元测试 `tests/unit/test_hint_service.py`：4 级 prompt 各不相同、hint_count 记录正确
  - [ ] 5.2 前端测试 `HintDisplay.test.tsx`：顺序展示、第 4 级后禁用、提交后隐藏

## Dev Notes

- **4 级提示设计依据**：基于 Aleven et al. (2009) "Help Seeking in Intelligent Tutoring Systems" 研究，渐进提示（scaffolded hints）比一次性完整提示对学习效果更好（20% 更高的保留率）；4 级对应教育学 ZPD（最近发展区）理论中的 4 个支架层级
- **禁止跳级实现**：前端 `hint_level` 只允许递增 1，后端也验证请求的 `hint_level` 必须等于 `current_hint_level + 1`（防止客户端绕过）
- **提示不纳入直接扣分**：按 FR11 规定，`hint_count` 只作为辅助信号传递给 5 信号融合（Story 5.3），不直接修改本次 BKT 更新公式
- **累积展示原因**：学习者可能需要参照之前级别的提示来理解更高级提示，不应隐藏已展示的低级提示
- **LLM 调用**：提示生成也使用本地 Ollama，每级提示独立调用（不批量）；若调用失败，返回预设的降级文本

### Project Structure Notes

- 核心服务：`backend/app/services/hint_service.py`
- 前端展示：`frontend/src/components/HintDisplay.tsx`
- store 扩展：`frontend/src/stores/exam-board-store.ts`
- 测试：`backend/tests/unit/test_hint_service.py`、`frontend/src/__tests__/HintDisplay.test.tsx`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.6] — AC 和 FR 映射（FR11）
- [Source: Aleven et al. 2009] — 渐进提示 scaffolded hints 教育学依据
- [Source: frontend/src/components/ChatPanel.tsx] — 前端组件风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证 4 级顺序提示** (AC: #1)
   - 在检验白板答题时，点击"提示"按钮
   - 第 1 次点击：应该看到简短的方向提示（一句话，不含具体内容）
   - 第 2 次点击：应该看到几个关键词（不含解释）
   - 第 3 次点击：应该看到答案结构框架（如步骤列表，但没有填写内容）
   - 第 4 次点击：应该看到接近完整的答案骨架
   - 每级提示都应该保留在页面上（不消失）
   - 如果级别顺序乱了或跳级，记录 Story 3.6

2. **验证第 4 级后禁用** (AC: #3)
   - 点击 4 次"提示"后
   - 按钮应该变为灰色且显示"已达最高提示级别"
   - 再次点击应该没有反应
   - 如果可以继续点击，记录 Story 3.6

3. **验证提交后隐藏** (AC: #4)
   - 提交答案后
   - "提示"按钮应该不再显示
   - 如果提交后仍显示"提示"按钮，记录 Story 3.6

4. **验证提示使用记录** (AC: #2)
   - 使用了 2 次提示后提交答案
   - 打开对应笔记的 frontmatter（元数据区域）
   - 最新的 error_history 条目中应该包含 `hint_count: 2`
   - 如果没有记录，记录 Story 3.6

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-3.6.1 | pytest | `.venv/bin/pytest tests/unit/test_hint_service.py -x -q` | 0 failed |
| CP-3.6.2 | vitest | `cd frontend && npx vitest run src/__tests__/HintDisplay.test.tsx` | 0 failed |
| CP-3.6.3 | pytest | `.venv/bin/pytest tests/integration/test_exam_board_api.py::test_hint_endpoint -x -q` | 0 failed |
| CP-3.6.4 | lint | `cd frontend && npx tsc --noEmit` | 0 errors |

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
- Depends on: [[3.4]]
