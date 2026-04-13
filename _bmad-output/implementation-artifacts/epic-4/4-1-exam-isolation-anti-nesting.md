---
story_id: "4.1"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 10
depends_on: ["1.1"]
blocks: ["4.2", "4.3", "4.4", "4.5"]
trace:
  - "FR-EXAM-01"
  - "FR-EXAM-10"
  - "FR-EXAM-22"
---

# Story 4.1: 信息隔离三重保证 + 防嵌套

Status: ready-for-dev

## Story
As a 学习者,
I want 检验白板打开时完全看不到笔记原文,
So that 我在纯 Active Recall 环境中学习（Karpicke & Blunt 2011, d=1.50 的 100% 等价条件）。

## Acceptance Criteria

1. **Given** 学习者触发 `/start_exam_board` skill **When** 系统读取当前活动笔记的 frontmatter **Then** 如果 `type == "exam_board"` 则立即 ABORT 并提示"当前已在检验白板，不可再生成检验白板" **And** 防嵌套检查先于所有其他操作（包括 query_mastery 和 generate_question）

2. **Given** 系统通过防嵌套检查 **When** Templater 生成 `exam_boards/*.md` 文件 **Then** body 只包含一行 `> [!exam_question]+ 等待 Agent 出题...` callout 占位符 **And** frontmatter 包含 `type: exam_board` 标记 **And** body 中零 `wiki/concepts/` 内容泄漏

3. **Given** 检验白板文件已生成 **When** Claudian sidebar 加载该文件 **Then** skill 系统 prompt 强制声明 `MUST NOT read wiki/concepts/*.md content` **And** 只允许通过 MCP 工具（query_mastery / generate_question / search_memories）间接获取 context **And** 禁止读取 `edges/*.md` 的任何文本内容

4. **Given** `generate_question` MCP 工具被调用 **When** 后端组装出题 context **Then** 返回值只包含 `question_text`、`question_id`、`bloom_level`、`pipeline_token` **And** `reference_answer` 字段强制为 `None`（exam_tools.py:348 硬约束）**And** `expected_elements` 不暴露给 skill 或用户

5. **Given** 学习者在 `exam_boards/*.md` 中答题 **When** AI sidebar 显示内容 **Then** sidebar 不显示题目/分数/提示等任何实质学习内容 **And** sidebar 仅作为 skill 触发指示器

6. **Given** 隔离保证 1（文件层）失败（模板生成异常）**When** body 意外包含 wiki/concepts 内容 **Then** 系统降级为 `[!warning]` callout 告知用户"隔离可能不完整，建议重新生成"（NFR-DEG）

## Tasks / Subtasks

- [ ] Task 1: 实现防嵌套检查模块 (AC: #1)
  - [ ] 在 `/start_exam_board` skill 入口最前端添加 frontmatter.type 检查
  - [ ] 实现 `check_anti_nesting(frontmatter: dict) -> bool` 函数
  - [ ] 添加 ABORT 消息的多语言支持（中/英）
  - [ ] 单元测试：type=exam_board 时 ABORT、type=concept 时放行、无 type 时放行

- [ ] Task 2: 实现保证 1 — Templater 空白 md 生成 (AC: #2)
  - [ ] 创建 `templates/exam-board.md` Templater 模板
  - [ ] frontmatter schema 实现：type/status/source_canvas/exam_mode/questions/new_nodes_pulled/canvas_writebacks
  - [ ] body 只含 `> [!exam_question]+ 等待 Agent 出题...`
  - [ ] 命名规则：`exam_boards/<source_canvas_slug>-<yyyy-mm-dd>-<hh-mm>.md`
  - [ ] 单元测试：生成文件内容不包含任何 wiki/concepts 内容

- [ ] Task 3: 实现保证 2 — Claudian context 隔离 (AC: #3)
  - [ ] 在 CLAUDE.md 的 `/start_exam_board` skill 声明中添加隔离规则
  - [ ] 清空当前挂载文件集（除新生成的 exam_boards/*.md 外）
  - [ ] 禁止 Read wiki/concepts/*.md 和 edges/*.md
  - [ ] 只允许通过 query_mastery / generate_question / search_memories 间接获取
  - [ ] 集成测试：skill 执行期间尝试 Read wiki/concepts/ 路径时被拒绝

- [ ] Task 4: 实现保证 3 — MCP 工具返回值过滤 (AC: #4)
  - [ ] 验证 exam_tools.py GenerateQuestionOutput 的 reference_answer 默认 None
  - [ ] 添加硬约束：generate_question 返回前强制清除 reference_answer
  - [ ] 添加硬约束：expected_elements 不包含在返回的 JSON 中
  - [ ] 单元测试：调用 generate_question 后返回值不含答案信息

- [ ] Task 5: 实现 sidebar 内容隔离 (AC: #5)
  - [ ] 在 exam skill prompt 中声明 sidebar 不显示题目/分数/提示
  - [ ] sidebar 仅显示 skill 状态指示（"考察进行中"/"等待答题"/"评分完成"）

- [ ] Task 6: 实现降级 callout (AC: #6)
  - [ ] 生成后验证 body 不含 wiki/concepts 关键词
  - [ ] 失败时插入 `[!warning]` callout 降级提示
  - [ ] 单元测试：模拟模板异常时降级路径正常工作

## Dev Notes

### Architecture
- 三重保证机制是 Active Recall d=1.50 效应量的根基，任一保证失败都会导致效应量降级到普通 review 的 d=0.40
- 防嵌套检查必须是 skill 的第一个操作，在任何 MCP 调用之前执行
- 5 层数据流：用户层 → Skill 层 → MCP 工具层 → 后端 Service 层 → LLM 层，每层隔离独立

### File Paths
- Templater 模板：`templates/exam-board.md`
- 生成文件目录：`exam_boards/`
- 防嵌套检查：skill 入口函数
- MCP 工具返回值：`backend/app/mcp/tools/exam_tools.py` (GenerateQuestionOutput)
- Pipeline token：`backend/app/mcp/pipeline_token.py` (PIPELINE_STEPS)
- Context enrichment：`backend/app/services/context_enrichment_service.py`

### Testing
- 单元测试覆盖三重保证的每一层
- 集成测试覆盖完整的隔离链路（skill → MCP → backend → 返回值验证）
- 回归测试：每次修改 exam 流程后验证三重保证不被破坏

### Project Structure Notes
- `exam_boards/` 是独立目录（非 `wiki/exam/`），强化"独立白板实例"语义
- frontmatter schema 定义见 anchor PRD §2.2

### References
- **From PRD**: §2 检验白板 100% 等价实现 (line 905-2743)
- **From PRD**: §2.4 完全空白 UI 的 3 重保证机制 (line 1490-1693)
- **From PRD**: §12.2 D14 答题媒介决策 (line 7479-7496)
- Karpicke & Blunt (2011): Retrieval Practice d=1.50
- `backend/app/mcp/tools/exam_tools.py`: GenerateQuestionOutput.reference_answer = None
- `backend/app/mcp/pipeline_token.py`: PIPELINE_STEPS 强制顺序

## UAT Script

> 1. 打开一个 wiki/concepts/ 下的知识笔记
> 2. 触发 `/start_exam_board`
> 3. 看到新文件 `exam_boards/<slug>-<date>.md` 被创建
> 4. 打开该文件，确认只看到一行"等待 Agent 出题"
> 5. 确认 AI sidebar 没有显示任何知识点内容
> 6. 在检验白板内再次触发 `/start_exam_board`
> 7. 看到 ABORT 提示"当前已在检验白板"
> 8. 返回原知识笔记，确认可以正常再次触发

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 防嵌套检查 | unit | `pytest tests/unit/test_exam_anti_nesting.py -x` | 0 failures |
| Templater 空白验证 | unit | `pytest tests/unit/test_exam_template.py -x` | 0 failures |
| MCP 返回值过滤 | unit | `pytest tests/unit/test_exam_tools_isolation.py -x` | 0 failures |
| 三重保证集成 | integration | `pytest tests/integration/test_exam_isolation_chain.py -x` | 0 failures |
| 降级 callout | unit | `pytest tests/unit/test_exam_degradation.py -x` | 0 failures |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
