---
doc_type: story
story_id: "6.3"
epic_id: "EPIC-6"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: ["6.2"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 6.3: 复习时注入历史误解上下文

## Story

As a 系统,
I want 在复习时自动注入学习者的历史误解上下文,
so that AI 出题和对话时能针对性地验证误解是否已纠正。

## Acceptance Criteria

1. **Given** 学习者对某概念进行复习（通过任务列表或提醒跳转触发）
   **When** AI 准备对话或出题上下文
   **Then** 从 Graphiti 获取该概念的历史误解记录（resolved=false 的 conceptual 和 knowledge_gap 类型）
   **And** 将误解上下文注入 LLM prompt，格式："该学习者曾在 X 方面有以下误解：Y"
   **And** AI 的回答或题目有意探测该误解是否仍然存在

2. **Given** Graphiti 返回多条误解记录
   **When** 注入上下文
   **Then** 注入最近 3 条（按 occurred_at 降序），超过 3 条时截断并追加"...等 N 条历史误解"
   **And** 总注入内容不超过 500 tokens（避免稀释有效上下文）

3. **Given** Graphiti 查询超时（> 3s）或不可用
   **When** 系统降级（NFR-DEG-3）
   **Then** 跳过误解注入，使用默认先验出题
   **And** 在 Skill 末尾摘要行标注：`[Graphiti] ⚠ misconception context skipped (timeout)`

4. **Given** 该概念没有任何未关闭误解记录
   **When** AI 准备上下文
   **Then** 不注入误解段落（不添加空的占位符）
   **And** 正常进行普通复习流程

## Tasks / Subtasks

- [ ] Task 1: 后端 — 误解上下文检索 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/services/context_enrichment_service.py` 添加 `get_misconception_context(concept_id: str)` 方法
  - [ ] 1.2 调用 Graphiti `search_memory_facts(query=f"misconception concept:{concept_id}", filters={"resolved": false})` 获取历史误解
  - [ ] 1.3 按 `occurred_at` 降序排列，取最多 3 条
  - [ ] 1.4 格式化为 prompt 片段：`"该学习者曾在以下方面有误解：\n- [{error_type}] {description} (发生于 {occurred_at})\n..."`
  - [ ] 1.5 实现 token 估算（简单字符数 / 4），若超过 500 tokens 则截断最老的记录

- [ ] Task 2: 后端 — 注入到 LLM 调用链 (AC: #1, #3, #4)
  - [ ] 2.1 在 `backend/app/services/quiz_generation_service.py` 的出题逻辑中，在构造 system prompt 前调用 `get_misconception_context()`
  - [ ] 2.2 在 `backend/app/services/chat_service.py` 的对话初始化中同样注入（仅复习模式，普通对话不注入）
  - [ ] 2.3 用 `asyncio.wait_for(get_misconception_context(), timeout=3.0)` 包裹 Graphiti 调用，超时时 catch `asyncio.TimeoutError` 并降级
  - [ ] 2.4 降级时在 Graphiti 摘要行追加警告标注（调用 `append_skill_summary_note()`）

- [ ] Task 3: 后端 — 注入标记追踪 (AC: #1)
  - [ ] 3.1 在 LLM request 的 metadata 中记录 `misconception_injected: bool` 和 `misconception_count: int`
  - [ ] 3.2 此 metadata 写入 Skill 末尾摘要行（例：`[Graphiti] wrote 1 episodes, read 2 facts, injected 2 misconceptions (125ms)`）

- [ ] Task 4: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 4.1 `tests/unit/test_misconception_context.py` — 验证格式化输出、3 条截断、token 限制
  - [ ] 4.2 `tests/unit/test_misconception_timeout.py` — mock Graphiti 超时，验证降级逻辑
  - [ ] 4.3 `tests/unit/test_no_misconception.py` — 无误解时不注入任何占位符
  - [ ] 4.4 `tests/integration/test_quiz_with_misconception.py` — 端到端验证出题时 system prompt 含误解段落

## Dev Notes

- **仅在复习模式触发**：通过检查请求 context 中的 `review_mode: true` 标志区分。普通对话不注入误解上下文（避免干扰日常学习）
- **Graphiti 查询**：使用 `search_memory_facts` 而非 `get_episodes`，前者支持语义过滤。`group_id="canvas-dev"` 为项目统一 group
- **NFR-REL-5 规范**：Graphiti 读必须在 LLM 调用前完成。`get_misconception_context()` 在构造 prompt 时同步调用（await），不能用 background task
- **token 估算简化**：不调用 tiktoken（引入依赖），用 `len(text) // 4` 作为保守估算（英文比中文更保守，中文实际约 1.5 字/token）
- **与 context_enrichment 的关系**：本 Story 是在现有 context_enrichment 流程中**追加**一个注入步骤，不替换现有的 wikilink 图遍历上下文

### Project Structure Notes

- 误解上下文方法：`backend/app/services/context_enrichment_service.py`（已有文件，追加方法）
- 出题注入点：`backend/app/services/quiz_generation_service.py`（已有文件，修改 prompt 构造段）
- 对话注入点：`backend/app/services/chat_service.py`（已有文件，在复习模式下注入）
- 参考风格：`backend/app/services/rag_service.py`（service 层风格）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.3] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#FR34] — FR34 复习注入历史误解
- [Source: _bmad-output/planning-artifacts/prd.md#NFR-DEG-3] — 降级行为：Graphiti 不可用时默认先验出题
- [Source: _bmad-output/planning-artifacts/prd.md#NFR-REL-5] — Graphiti 读在 LLM 前
- [Source: backend/app/services/rag_service.py] — service 层风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证误解上下文注入** (AC: #1)
   - 通过复习任务列表或提醒点击进入一个有历史误解的概念复习
   - 启动考察或对话
   - AI 给出的题目或第一条回应中应该明显针对你的历史误解（比如你曾混淆 A 和 B，AI 会出一道辨别 A 和 B 的题）
   - 如果 AI 给的题目看起来和你的误解无关，记录 Story 6.3

2. **验证截断逻辑** (AC: #2)
   - 如果你对某个概念有很多条历史误解（4 条以上）
   - AI 在复习时应该只针对最近的 3 条误解出题
   - 观察 Skill 结束时底部的摘要行（格式类似 `[Graphiti] ... injected 3 misconceptions`）
   - 如果摘要行显示超过 3 条，记录 Story 6.3

3. **验证 Graphiti 不可用时降级** (AC: #3)
   - 断开网络连接后触发复习考察
   - 考察应该照常进行（AI 正常出题，只是不针对历史误解）
   - 考察结束时摘要行应显示 `[Graphiti] ⚠ misconception context skipped`
   - 如果考察完全无法启动，记录 Story 6.3

4. **验证无误解时正常流程** (AC: #4)
   - 找一个你从来没有答错过的概念进行复习
   - 考察应该正常进行，没有任何 "历史误解" 相关提示
   - 如果看到空的误解框或报错信息，记录 Story 6.3

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-6.3.1 | pytest | `.venv/bin/pytest tests/unit/test_misconception_context.py -x -q` | 0 failed |
| CP-6.3.2 | pytest | `.venv/bin/pytest tests/unit/test_misconception_timeout.py -x -q` | 0 failed |
| CP-6.3.3 | pytest | `.venv/bin/pytest tests/unit/test_no_misconception.py -x -q` | 0 failed |
| CP-6.3.4 | pytest | `.venv/bin/pytest tests/integration/test_quiz_with_misconception.py -x -q` | 0 failed |

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
- Depends on: [[6.2]]
