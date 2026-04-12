---
doc_type: story
story_id: "4.4"
epic_id: "EPIC-4"
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

# Story 4.4: EI+SE 双策略深度讨论

## Story

As a 学习者,
I want 选中两个概念之间的关系文本启动 EI+SE 双策略深度讨论,
so that 我可以深入理解概念关系的细微差别，而不仅仅是记住定义。

## Acceptance Criteria

1. **Given** 学习者在笔记中看到两个 `[[wikilink]]` 概念
   **When** 学习者选中关系文本并通过 MCP 工具触发"深度讨论"
   **Then** AI 进入双策略讨论模式：
   - **Elaborative Interrogation（EI）**：追问"为什么"——引导学习者解释两个概念之间关系成立的原因
   - **Self-Explanation（SE）**：引导学习者用自己的话重新表述两个概念之间的关系
   **And** 对话围绕这两个概念的关系展开（不跳到其他无关概念）

2. **Given** 深度讨论进行中
   **When** AI 发出一轮追问
   **Then** 每轮追问只使用 EI 或 SE 中的一种策略（不混用），且策略在对话中交替出现
   **And** AI 不直接给出答案，而是通过追问引导学习者自己得出结论

3. **Given** 深度讨论进行了至少 2 轮对话
   **When** 学习者结束讨论（发送"结束"或触发结束 MCP 工具）
   **Then** 系统生成一段讨论摘要，包含：学习者自己表述的关系理解、AI 追问揭示的关键点
   **And** 摘要可选择性追加到原笔记的"讨论记录"section（学习者确认后写入）
   **And** 讨论作为 Graphiti episode 归档（NFR-OBS-1）

4. **Given** 选中的文本不包含两个可识别的 `[[wikilink]]`
   **When** 学习者触发深度讨论
   **Then** 系统提示"请选中包含两个 [[概念]] 的关系文本"
   **And** 不启动讨论模式

## Tasks / Subtasks

- [ ] Task 1: 实现深度讨论 MCP 工具后端端点 (AC: #1, #4)
  - [ ] 1.1 在 `backend/app/api/v1/endpoints/` 创建 `deep_discussion.py`
  - [ ] 1.2 定义 `POST /api/v1/discussion/start` 端点
      - 参数：`selected_text: str`、`source_note_path: str`、`vault_root: str`
      - 解析 selected_text 中的 `[[concept_a]]` 和 `[[concept_b]]`（正则提取）
      - 若解析不到两个 wikilink → 返回 400 + 提示文案
  - [ ] 1.3 定义 `POST /api/v1/discussion/{session_id}/message` — 继续对话，LLM 使用当前策略生成追问
  - [ ] 1.4 定义 `POST /api/v1/discussion/{session_id}/end` — 结束讨论，生成摘要

- [ ] Task 2: 实现 EI+SE 双策略 prompt 逻辑 (AC: #1, #2)
  - [ ] 2.1 在 `backend/app/prompts/` 创建 `ei_strategy.jinja2`（EI 策略 prompt）
      - 系统指令：你正在引导学习者解释 {{concept_a}} 和 {{concept_b}} 之间的关系成立的原因
      - 要求追问"为什么"、不给答案、引导学习者自己推导
  - [ ] 2.2 在 `backend/app/prompts/` 创建 `se_strategy.jinja2`（SE 策略 prompt）
      - 系统指令：你正在引导学习者用自己的话重新表述 {{concept_a}} 和 {{concept_b}} 的关系
      - 要求用"你能用自己的话说说..."类型的问题
  - [ ] 2.3 在 `backend/app/services/` 创建 `discussion_service.py`
      - 维护 session 状态（轮次计数 + 已用策略序列）
      - 奇数轮用 EI，偶数轮用 SE（或反之），确保交替
      - 通过 LiteLLM 层发送 prompt + 对话历史

- [ ] Task 3: 实现讨论摘要生成 (AC: #3)
  - [ ] 3.1 在 `backend/app/prompts/` 创建 `discussion_summary.jinja2`
      - 对话历史 + 两个概念 → 生成摘要（学习者理解要点 + 追问揭示的关键）
  - [ ] 3.2 `POST /api/v1/discussion/{session_id}/end` 返回：`{ summary, concept_a, concept_b, turns_count }`
  - [ ] 3.3 实现 `append_discussion_to_note(note_path, summary)` — 在原笔记末尾的 `## 讨论记录` section 追加摘要（section 不存在时创建）

- [ ] Task 4: 实现 Graphiti 归档 (AC: #3)
  - [ ] 4.1 讨论结束时调用 Graphiti 写入队列（异步，不阻塞 API 响应，FR27）
  - [ ] 4.2 episode body：`f"深度讨论 [{concept_a}] — [{concept_b}]：{summary}"`
  - [ ] 4.3 group_id 与项目约定对齐（S27 决策：group_id 按白板名）

- [ ] Task 5: 注册 MCP 工具 (AC: #1, #4)
  - [ ] 5.1 在 `backend/app/mcp/tools.py` 注册 `start_deep_discussion` 工具定义
  - [ ] 5.2 工具描述：选中笔记中两个 [[概念]] 的关系文本后调用

- [ ] Task 6: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 6.1 单元测试：`tests/unit/test_discussion_service.py`
      - 验证 wikilink 解析（正常 / 少于两个 wikilink / 无 wikilink）
      - 验证策略交替逻辑（EI → SE → EI...）
  - [ ] 6.2 集成测试：`tests/integration/test_deep_discussion_api.py`
      - start → message（2轮）→ end 完整流程
      - 验证摘要结构（含 concept_a / concept_b / summary 字段）

## Dev Notes

- **prompt 硬编码禁止**：EI / SE / summary 三个 prompt 全部用 Jinja2 模板，不可在 Python 代码内写 f-string prompt。
- **LiteLLM 层**：所有 LLM 调用走 `backend/app/llm/client.py`，不直接调 OpenAI / Anthropic SDK（AR8）。
- **会话状态**：`discussion_service.py` 用 Python dict（内存）维护 session 状态（session_id → DiscussionSession）。单进程简单实现即可；不需要 Redis 或数据库（讨论 session 是临时的，不需要持久化）。
- **Graphiti 归档**：讨论结束时 Graphiti 写入必须走异步非阻塞队列（Story 5 的 FR27 实现），不可 `await graphiti.add_episode()` 同步阻塞 API。若队列尚未实现，先用 `asyncio.create_task` 占位，不可 TODO 空函数（DD-03）。
- **概念范围约束**：LLM 在 EI/SE 追问时容易"跑题"。prompt 中明确：`你只能讨论 {{concept_a}} 和 {{concept_b}} 的关系，不要引入第三个无关概念`。
- **NFR-PERF-1**：LLM 出题/评分 < 5s P95。深度讨论追问属于"出题"范畴，LiteLLM 调用需设置 `timeout=8`（留 3s 余量给网络）。

### Project Structure Notes

- 新端点：`backend/app/api/v1/endpoints/deep_discussion.py`
- 新 service：`backend/app/services/discussion_service.py`
- 新 prompt 模板：`backend/app/prompts/ei_strategy.jinja2`、`se_strategy.jinja2`、`discussion_summary.jinja2`
- MCP 工具注册：`backend/app/mcp/tools.py`
- 测试：`backend/tests/unit/test_discussion_service.py`、`backend/tests/integration/test_deep_discussion_api.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4.4] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR4] — 原始需求（EI+SE 双策略）
- [Source: backend/app/services/rag_service.py] — 后端 service 风格参考
- [Source: backend/app/api/v1/endpoints/canvas.py] — 后端 router 风格参考
- [Source: _bmad-output/planning-artifacts/architecture.md#AR8] — LiteLLM 统一层

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证深度讨论启动** (AC: #1)
   - 打开 Obsidian，进入一篇含有两个 [[wikilink]] 概念的笔记（例如"[[指针]] 是 [[引用]] 的底层实现"）
   - 选中这段关系文本，在 Claudian 中点击"深度讨论"按钮
   - Claudian 应开始一段对话，第一条消息是关于这两个概念关系的追问（例如"你能解释一下，为什么指针是引用的底层实现吗？"）
   - 对话内容应围绕"指针"和"引用"展开，不跳到其他主题
   - 如果没有启动对话，或对话内容无关，记录 Story 4.4

2. **验证 EI 和 SE 策略交替** (AC: #2)
   - 回答 AI 的追问（任意回答即可，不需要准确）
   - 观察 AI 的第二条追问：第一轮是"为什么"类型（EI），第二轮应是"用你自己的话说说..."类型（SE）
   - 继续回答，第三轮应再次回到"为什么"类型
   - 如果所有追问都是同一类型，记录 Story 4.4

3. **验证结束生成摘要** (AC: #3)
   - 进行至少 2 轮对话后，发送"结束"或点击"结束讨论"按钮
   - Claudian 应显示一段摘要，包含"你的理解要点"和"讨论中揭示的关键点"
   - 系统应询问"是否将摘要追加到笔记？"（是/否）
   - 选择"是"后，打开原笔记，末尾应出现"## 讨论记录"section 和摘要内容
   - 如果没有摘要或笔记未更新，记录 Story 4.4

4. **验证无效选中文本的提示** (AC: #4)
   - 选中一段不含 [[wikilink]] 的普通文本，触发"深度讨论"
   - 应看到提示："请选中包含两个 [[概念]] 的关系文本"
   - 不应启动讨论对话
   - 如果错误触发了讨论，记录 Story 4.4

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-4.4.1 | pytest | `.venv/bin/pytest tests/unit/test_discussion_service.py -x -q` | 0 failed |
| CP-4.4.2 | pytest | `.venv/bin/pytest tests/integration/test_deep_discussion_api.py -x -q` | 0 failed |
| CP-4.4.3 | pytest | `.venv/bin/pytest tests/ -k "discussion" -x -q` | 0 failed |

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
