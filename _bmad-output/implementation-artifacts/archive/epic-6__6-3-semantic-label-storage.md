---
story_id: "6.3"
epic_id: "6"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 4
depends_on: ["6.1"]
blocks: []
trace:
  - "FR-EDGE-03"
---

# Story 6.3: 语义标签存储

Status: ready-for-dev

## Story

As a 系统,
I want 记录学习者对关系的解释理由并存储为结构化语义标签,
So that 关系解释可被 Graphiti 和图遍历检索，支持后续对话和出题的上下文注入。

## Acceptance Criteria

1. **Given** Edge 讨论结束（`/edge_discuss` 对话完成）
   **When** 系统存储讨论结果
   **Then** 学习者的关系解释理由存储到两端 concept.md frontmatter `relationships[]` 对应条目的 `rationale` 字段
   **And** rationale 是学习者用自己的话总结的一句话解释（非 AI 生成）

2. **Given** 讨论结果存储
   **When** 系统写入 concept.md frontmatter relationships[] 条目
   **Then** 条目包含完整的结构化语义标签：
   - `semantic_type`: 关系类型（depends_on / refines / extends / contradicts / related_to）
   - `rationale`: 学习者的一句话解释
   - `ei_techniques[]`: EI 阶段 AI 提出的所有问题列表
   - `se_summary`: SE 阶段学习者的解释总结
   - `confidence`: 置信度（EXTRACTED / INFERRED / AMBIGUOUS）
   - `discussion_rounds`: 讨论总轮数
   - `rationale_source`: user_stated / auto_extracted
   - `created` / `modified`: 时间戳

3. **Given** relationships[] 已存储
   **When** Graphiti 索引更新
   **Then** 关系的 rationale 和 semantic_type 可通过 `search_memory_facts(group_id="canvas-dev")` 检索
   **And** 搜索 "admissibility 和 a-star 的关系" 能命中对应 relationships[] 条目的 rationale

4. **Given** relationships[] 已存储
   **When** wikilink 图遍历访问该关系
   **Then** 图遍历服务可读取 concept.md frontmatter relationships[] 的 semantic_type 和 rationale
   **And** 在 `context_enrichment` 上下文组装时，语义标签作为高优先级上下文注入
   **And** 对话中 AI 可引用学习者之前的解释（"你之前说过 admissibility 保证不 overestimate..."）

5. **Given** 同一对概念进行了多次 Edge 讨论
   **When** 新讨论结束
   **Then** 在现有 relationships[] 条目中追加新的 ei_techniques / se_summary 内容
   **And** rationale 更新为最新讨论的总结（保留历史 rationale 附带时间戳）
   **And** `modified` 更新，`discussion_rounds` 累加

6. **Given** 讨论结束但学习者未给出明确的 rationale
   **When** 系统尝试提取 rationale
   **Then** 从 SE 阶段学习者最后一轮回答中自动提取核心句作为 rationale
   **And** 标记 `rationale_source: auto_extracted`（区别于 `rationale_source: user_stated`）
   **And** 在后续对话中 AI 可确认："上次讨论时系统提取了你的解释 '...'，这个理解准确吗？"

## Tasks / Subtasks

- [ ] Task 1: 讨论结果到 concept.md frontmatter relationships[] 的存储逻辑 (AC: #1, #2)
  - [ ] 1.1: 在 `/edge_discuss` skill 的结束步骤中收集讨论数据：学习者的 rationale、EI 问题列表、SE 回答列表、讨论轮数
  - [ ] 1.2: 调用 Story 3.3 的 `add_relationship` 或 `update_relationship` 函数写入两端 concept.md frontmatter relationships[]
  - [ ] 1.3: relationships[] 条目结构化存储：semantic_type / rationale / rationale_source / ei_techniques[] / se_summary / confidence / discussion_rounds / created / modified
  - [ ] 1.4: ~~body 段落存储~~ 不再需要独立文件 body，所有数据存储在 frontmatter relationships[] 条目中

- [ ] Task 2: Rationale 提取逻辑 (AC: #1, #6)
  - [ ] 2.1: 优先使用学习者明确给出的 rationale（如果讨论中有"总结一下"类型的回答）
  - [ ] 2.2: 学习者未明确总结时，从 SE 阶段最后一轮回答中用 LLM 提取核心句（< 100 字符）
  - [ ] 2.3: 标记 `rationale_source: user_stated` 或 `rationale_source: auto_extracted`
  - [ ] 2.4: auto_extracted 的 rationale 在后续对话中供 AI 确认

- [ ] Task 3: Graphiti 索引集成 (AC: #3)
  - [ ] 3.1: relationships[] 写入后，调用 Graphiti `add_memory` 将 semantic_type + rationale 写入知识图谱
  - [ ] 3.2: add_memory 参数：group_id="canvas-dev"，name="[Relationship] <A>--<B>: <semantic_type>"，episode_body=rationale + context
  - [ ] 3.3: 验证 `search_memory_facts` 可通过自然语言查询命中关系 rationale
  - [ ] 3.4: Graphiti 不可用时降级：仅存储到 frontmatter relationships[]，不调用 add_memory，记录警告日志

- [ ] Task 4: 图遍历检索集成 (AC: #4)
  - [ ] 4.1: 在 `context_enrichment` 服务中增加 concept.md frontmatter relationships[] 读取逻辑
  - [ ] 4.2: 图遍历到某概念时，读取其 relationships[] 中的 semantic_type + rationale + discussion_rounds 作为上下文
  - [ ] 4.3: 关系语义标签在上下文组装中的优先级：高于 2-hop 邻居 frontmatter，低于 1-hop 邻居内容
  - [ ] 4.4: AI 可引用学习者之前的解释：在 prompt 中注入 "学习者在 {date} 对 {A}--{B} 的解释：{rationale}"

- [ ] Task 5: 多次讨论追加逻辑 (AC: #5)
  - [ ] 5.1: 检测 relationships[] 中是否已有指向目标概念的条目（复用 Story 3.3 的去重逻辑）
  - [ ] 5.2: 已存在时在该条目的 ei_techniques / se_summary 字段追加新内容
  - [ ] 5.3: 保留旧 rationale 附带时间戳，rationale 更新为最新讨论总结
  - [ ] 5.4: `discussion_rounds` 累加，`modified` 更新

- [ ] Task 6: 测试 (AC: #1~#6)
  - [ ] 6.1: 单元测试 relationships[] 存储：结构化字段完整
  - [ ] 6.2: 单元测试 rationale 提取：user_stated vs auto_extracted 正确分类
  - [ ] 6.3: 集成测试 Graphiti 索引：add_memory 写入 + search_memory_facts 命中
  - [ ] 6.4: 集成测试图遍历检索：context_enrichment 正确注入 Edge 语义标签
  - [ ] 6.5: 单元测试多次讨论追加：历史保留 + 最新更新
  - [ ] 6.6: 降级测试：Graphiti 不可用时仅 frontmatter 存储

## Dev Notes

- **核心依赖**: Story 6.1（Edge 讨论触发）提供 `/edge_discuss` skill 和讨论数据
- **核心依赖**: Story 3.3（概念关系 Frontmatter + 71x 压缩检索）提供 relationships[] 写入/更新的基础函数
- **Anchor PRD 引用**: §1.3 Edge 对话 (line 421-437) 定义了关系 schema（已从独立 edge.md 迁移至 concept.md frontmatter relationships[]）
- **rationale 是学习者的话**: 不是 AI 生成的总结。AI 只在 auto_extracted 场景下提取学习者回答中的核心句
- **Graphiti 双写**: 关系数据同时写入 concept.md frontmatter relationships[]（永久存储）和 Graphiti 知识图谱（检索加速）。两者互补
- **语义标签的价值**: 被 `/chat_with_context`（上下文注入）、`/start_exam_board`（出题素材）、`/review_profile`（学习档案）三个 skill 消费
- **structlog 日志**: 所有存储操作使用 `structlog.get_logger(__name__)` 记录

### Project Structure Notes

```
wiki/concepts/
  <slug>.md                          # 修改：frontmatter relationships[] 追加 EI/SE 记录和语义标签
.claude/skills/edge-discuss/
  SKILL.md                           # 修改：增加讨论结果存储逻辑（写入 frontmatter 而非独立文件）
```

### References

- Anchor PRD §1.3 Edge 文件 schema: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 421-437)
- BMAD PRD FR-EDGE-03: `_bmad-output/planning-artifacts/prd.md` (line 373)
- Story 6.1 Edge 讨论触发: `_bmad-output/implementation-artifacts/epic-6/6-1-edge-discussion-trigger.md`
- Story 3.3 概念关系 Frontmatter: `_bmad-output/implementation-artifacts/epic-3/3-3-edge-relationship-files.md`
- Story 2.1 context_enrichment: `_bmad-output/implementation-artifacts/epic-2/2-1-ai-dialog-context-injection.md`

## UAT Script

> 1. 完成一次 `/edge_discuss` 讨论（按 Story 6.1 和 6.2 的方式）
> 2. 讨论中回答"admissibility 保证 h(n) 不高于真实代价，所以 A* 不会跳过最优路径"
> 3. 讨论结束后验证 `wiki/concepts/admissibility.md` frontmatter relationships[] 已更新（包含指向 `[[a-star]]` 的条目）
> 4. 验证 relationships[] 条目包含 rationale（你的解释）/ semantic_type / ei_techniques / se_summary / discussion_rounds
> 5. 在 Claudian 中问"admissibility 和 a-star 有什么关系？"，验证 AI 回答中引用了你之前的解释
> 6. 再次对同一对概念进行 Edge 讨论，验证 relationships[] 条目被追加更新而非新建
> 7. 验证旧 rationale 被保留（附时间戳），新 rationale 成为当前值

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| relationships[] 存储 | unit | `pytest tests/unit/test_semantic_labels.py::test_relationships_structure -x` | 全部字段存在 |
| rationale 提取 | unit | `pytest tests/unit/test_semantic_labels.py::test_rationale_extraction -x` | user_stated / auto_extracted 正确 |
| Graphiti 写入 | integration | `pytest tests/integration/test_semantic_labels_graphiti.py -x` | add_memory 成功 + search 命中 |
| 图遍历检索 | integration | `pytest tests/integration/test_semantic_labels_traversal.py -x` | context 注入关系语义标签 |
| 多次追加 | unit | `pytest tests/unit/test_semantic_labels.py::test_append_discussion -x` | 历史保留 + 最新更新 |
| Graphiti 降级 | integration | `pytest tests/integration/test_semantic_labels_degradation.py -x` | 仅 frontmatter 存储 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

**批注处理记录 (2026-04-13)**
1. **存储目标变更**: 从 `edges/<from>--<to>.md` frontmatter 改为 `concept.md frontmatter relationships[].semantic_type + ei_techniques[] + se_summary`。所有 AC 和 Task 已同步更新。
2. **字段名对齐**: `relation` → `semantic_type`，`ei_questions` → `ei_techniques`，`se_answers` → `se_summary`，与 Story 1.1 的 relationships[] schema 保持一致。
3. **Graphiti 双写保留**: 关系数据仍然双写到 Graphiti 知识图谱，只是本地永久存储从独立文件改为 frontmatter 字段。

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
