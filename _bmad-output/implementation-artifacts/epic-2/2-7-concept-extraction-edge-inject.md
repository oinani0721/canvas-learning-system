---
story_id: "2.7"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 8
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-CONV-08"
  - "FR-CONV-10"
  - "FR-CONV-11"
---

# Story 2.7: 新概念提取 + Edge 语义注入 + 压缩保留

Status: ready-for-dev

## Story

As a 学习者,
I want 从对话中提取新概念并在上下文压缩时保留关键数据,
So that 知识图谱持续增长且重要信息不因上下文窗口限制丢失。

## Acceptance Criteria

1. **Given** 学习者在对话中选取一段内容（文字/概念描述）
   **When** 触发概念提取操作
   **Then** 系统创建新的概念文件 `wiki/concepts/<new-slug>.md`
   **And** 文件包含 Templater 标准 frontmatter（mastery_score: 0.30 / bkt_params / fsrs_params / errors: [] / tips: [] / created_at / updated_at）
   **And** 文件正文包含从对话中提取的内容
   **And** 文件末尾包含与源概念的 wikilink（`[[source-slug]]`）

2. **Given** 新概念文件已创建
   **When** 系统分析源概念与新概念的关系
   **Then** 自动建议关系类型（depends_on / prerequisite_of / related_to / contrast_with / part_of）
   **And** 提示学习者确认或修改关系类型
   **And** 确认后创建 Edge 文件 `edges/<source>--<new-slug>.md`，包含 relationship_type / rationale / confidence

3. **Given** 学习者正在讨论一个概念
   **When** 系统执行 Edge 语义检索
   **Then** 从已有 Edge 文件中检索与当前讨论相关的前序笔记讨论摘要
   **And** 检索结果注入当前对话的 LLM 上下文
   **And** 注入的摘要标明来源 Edge 和讨论日期

4. **Given** 对话上下文窗口即将超出限制
   **When** 系统执行上下文压缩
   **Then** 压缩保留优先级（从高到低）：
   - Tips（frontmatter tips[]）
   - 错误记录（frontmatter errors[]）
   - 掌握度状态（mastery_score / bkt_params）
   - 当前轮次的关键对话内容
   - 历史对话摘要
   **And** 被压缩的内容在系统消息中通知学习者（如"已压缩早期对话，保留了 N 条 Tips 和 M 条错误记录"）

5. **Given** 压缩通知已发出
   **When** 学习者继续对话
   **Then** 被保留的 Tips / errors / mastery 在后续对话中仍然可用
   **And** 被压缩移除的历史对话不再被 LLM 引用

## Tasks / Subtasks

- [ ] Task 1: 对话内容提取为新概念 (AC: #1)
  - [ ] 1.1: 在 `backend/app/services/` 下创建 `concept_extractor.py`
  - [ ] 1.2: 实现 `extract_concept(selected_text: str, source_node_id: str, session_id: str) -> ConceptFile`
  - [ ] 1.3: 生成 slug：从 selected_text 提取关键词，转 kebab-case（支持中英文）
  - [ ] 1.4: 使用 Templater 标准 frontmatter 模板创建概念文件（复用 Story 1.1 定义的模板字段）
  - [ ] 1.5: 文件末尾自动添加 `## 来源\n- 从 [[source-slug]] 的对话中提取\n- 提取时间: {datetime}`

- [ ] Task 2: 关系类型建议与 Edge 文件创建 (AC: #2)
  - [ ] 2.1: 实现 `suggest_relationship(source_slug: str, target_slug: str, context: str) -> SuggestedRelation`
  - [ ] 2.2: 使用 LLM 分析两个概念的上下文，建议关系类型（5 种：depends_on / prerequisite_of / related_to / contrast_with / part_of）
  - [ ] 2.3: 返回建议结果给 skill，skill 通过对话向学习者确认（"我建议关系类型是 depends_on，你同意吗？"）
  - [ ] 2.4: 确认后创建 Edge 文件 `edges/<source>--<new-slug>.md`，frontmatter 含 `type: edge` / `from` / `to` / `relation` / `rationale` / `confidence`（参考 Story 1.1 edge.md 模板）

- [ ] Task 3: Edge 语义检索注入 (AC: #3)
  - [ ] 3.1: 在 `backend/app/services/chat_context_assembler.py`（Story 2.1）中新增 `inject_edge_summaries(node_id: str) -> str`
  - [ ] 3.2: 读取与当前节点相关的所有 Edge 文件（`edges/<slug>--*.md` 和 `edges/*--<slug>.md`）
  - [ ] 3.3: 从 Edge 文件中提取 `rationale` / `ei_questions` / `se_answers` 字段
  - [ ] 3.4: 格式化为 LLM 上下文片段：`"相关前序讨论 (Edge: {from}→{to}):\n  关系: {relation}\n  理由: {rationale}\n  讨论日期: {created_at}"`

- [ ] Task 4: 上下文压缩与保留策略 (AC: #4, #5)
  - [ ] 4.1: 在 `chat_context_assembler.py` 中扩展 `compress_context()` 方法，实现分层保留策略
  - [ ] 4.2: 保留优先级实现：为每类数据打标签（tips=P0 / errors=P0 / mastery=P1 / current_turn=P2 / history_summary=P3），按优先级从低到高移除
  - [ ] 4.3: 实现压缩通知生成：`"已压缩早期对话内容。保留了 {n_tips} 条 Tips、{n_errors} 条错误记录和当前掌握度状态。"`
  - [ ] 4.4: 通知作为 system 消息插入对话流，学习者可见

- [ ] Task 5: 测试 (AC: #1~#5)
  - [ ] 5.1: 单元测试 `extract_concept`：文件创建、frontmatter 格式、wikilink 生成
  - [ ] 5.2: 单元测试 `suggest_relationship`：5 种关系类型建议
  - [ ] 5.3: 单元测试 `inject_edge_summaries`：Edge 文件读取和格式化
  - [ ] 5.4: 单元测试压缩保留：Tips/errors 保留验证、通知文本生成
  - [ ] 5.5: 集成测试：对话中提取概念 → Edge 创建 → 新对话中验证 Edge 摘要注入

## Dev Notes

- **Edge 文件 schema**: 参考 Anchor PRD §3.4 (line 3440-3458)，frontmatter 含 `from` / `to` / `relation` / `rationale` / `confidence` / `ei_questions` / `se_answers`
- **5 种关系类型**: `depends_on`（A 依赖 B）、`prerequisite_of`（A 是 B 的前置）、`related_to`（相关）、`contrast_with`（对比）、`part_of`（A 是 B 的部分）
- **Anchor PRD 引用**: §3.4 Edge frontmatter (line 3440-3458)，§4.1 Step 7 (line 3685-3705)
- **压缩通知**: PRD FR-CONV-11 要求压缩时通知学习者，确保学习者知晓上下文变化

### Project Structure Notes

```
backend/app/services/
  concept_extractor.py            # 新增：概念提取 + 文件创建
  chat_context_assembler.py       # Story 2.1 创建，扩展 Edge 注入 + 压缩保留
backend/tests/unit/
  test_concept_extractor.py       # 新增
  test_edge_injection.py          # 新增
  test_context_compression.py     # 新增
```

### References

- Anchor PRD §3.4 Edge schema: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3440-3458)
- Story 1.1 Templater 模板: `_bmad-output/implementation-artifacts/epic-1/1-1-vault-init-templates.md`
- FR-CONV-08/10/11: BMAD PRD (line 360-363)

## UAT Script

> 1. 打开 `wiki/concepts/admissibility.md`，启动 AI 对话
> 2. 讨论过程中，AI 提到 "consistency" 概念
> 3. 选取 AI 回答中关于 consistency 的描述，触发概念提取
> 4. 系统提示建议关系类型（如 "contrast_with"），确认
> 5. 验证 `wiki/concepts/consistency.md` 已创建且包含标准 frontmatter
> 6. 验证 `edges/admissibility--consistency.md` 已创建
> 7. 进行长对话直到触发压缩，验证收到压缩通知
> 8. 压缩后提问关于 Tips 的问题，验证 Tips 仍可被 AI 引用

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 概念提取 | unit | `pytest tests/unit/test_concept_extractor.py -x` | 文件创建 + frontmatter 正确 |
| 关系建议 | unit | `pytest tests/unit/test_concept_extractor.py::test_relationship_suggestion -x` | 5 种类型 |
| Edge 注入 | unit | `pytest tests/unit/test_edge_injection.py -x` | 格式化正确 |
| 压缩保留 | unit | `pytest tests/unit/test_context_compression.py -x` | Tips/errors 保留 |
| 压缩通知 | unit | `pytest tests/unit/test_context_compression.py::test_notification -x` | 通知文本正确 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
