---
story_id: "3.3"
epic_id: "3"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["3.1"]
blocks: ["6.1"]
trace:
  - "FR-KG-06"
  - "FR-KG-07"
---

# Story 3.3: 概念关系 Frontmatter + 71x 压缩检索

Status: ready-for-dev

## Story

As a 学习者,
I want 在 concept.md frontmatter 的 relationships[] 字段中存储概念间语义关系和讨论历史，并通过图谱关系实现 71x token 压缩检索,
So that 概念间关系有结构化记录（无需独立 edge 文件），AI 检索效率大幅提升。

## Acceptance Criteria

1. **Given** 学习者确认两个概念间的关系（通过 `/extract_node` 的关系建议或 `/edge_discuss`）
   **When** 系统记录关系
   **Then** 在两端 concept.md 的 frontmatter `relationships[]` 字段中各追加一条关系记录
   **And** 每条记录包含：`target` · `semantic_type` · `rationale` · `ei_techniques[]` · `se_summary` · `confidence` · `created` · `modified`
   **And** 双向链接 `[[Concept B]]` 自动建立

2. **Given** relationships[] 已写入两端概念文件
   **When** 系统检查关系一致性
   **Then** `wiki/concepts/<A>.md` 的 relationships[] 中有指向 `[[B]]` 的记录
   **And** `wiki/concepts/<B>.md` 的 relationships[] 中有指向 `[[A]]` 的对称记录
   **And** 两端 semantic_type 互为逆关系（如 A prerequisite B ↔ B depends_on A）

3. **Given** 系统需要为对话或出题提供上下文
   **When** 调用上下文组装服务
   **Then** 优先从 `graph.json`（Graphify 输出）读取关系数据（30 token 关系描述），而非读取 wiki 全文（1500 token）
   **And** 实现约 71x token 压缩比
   **And** 对于 1-hop 邻居，用 graph.json 中的 relation + 短 description 代替完整文件内容
   **And** fallback：graph.json 不存在时从 concept.md frontmatter relationships[] 读取（约 50 tokens/关系）

4. **Given** 同一对概念已存在 relationships[] 记录
   **When** 学习者再次讨论同一对概念
   **Then** 系统在现有 relationships[] 条目中追加新的 ei_techniques / se_summary 内容
   **And** 更新 `modified` 时间戳
   **And** 不创建重复条目

5. **Given** 查询某概念的所有关系
   **When** 系统遍历 relationships[]
   **Then** 双向匹配：查 A 的 relationships 找到 B，查 B 的 relationships 也找到 A
   **And** 关系唯一性通过 target wikilink 保证（同一 target 不重复）

## Tasks / Subtasks

- [ ] Task 1: Frontmatter relationships[] 写入逻辑 (AC: #1, #5)
  - [ ] 1.1: 实现 `add_relationship(concept_path, target_slug, semantic_type, rationale, confidence)` 函数
  - [ ] 1.2: 写入当前概念 frontmatter 的 `relationships[]` 字段，包含 target / semantic_type / rationale / ei_techniques / se_summary / confidence / created / modified
  - [ ] 1.3: 同步写入目标概念的 frontmatter，建立对称关系记录
  - [ ] 1.4: 去重逻辑：同一 target 不重复创建，已存在时走追加更新路径

- [ ] Task 2: 双端关系一致性维护 (AC: #2)
  - [ ] 2.1: 写入 A → B 关系时，自动在 B 的 relationships[] 中写入 B → A 的对称关系
  - [ ] 2.2: 对称 semantic_type 映射：prerequisite ↔ depends_on、extends ↔ extended_by、其他保持 related_to
  - [ ] 2.3: 更新关系时同步更新两端，保证一致性
  - [ ] 2.4: 删除关系时同步删除两端记录

- [ ] Task 3: 71x token 压缩检索集成 (AC: #3)
  - [ ] 3.1: 在上下文组装服务中优先读取 `outputs/graphify-out/graph.json` 的关系数据
  - [ ] 3.2: 对 1-hop 邻居，用 graph.json 中的 `{relation} + {短描述}` 格式（约 30 tokens）替代读取完整 wiki 文件（约 1500 tokens）
  - [ ] 3.3: 实现 fallback：graph.json 不存在时降级为读取 concept.md frontmatter relationships[]（约 50 tokens/关系），再降级为读取完整 wiki 文件
  - [ ] 3.4: 在日志中记录实际压缩比（tokens_saved / tokens_original）

- [ ] Task 4: relationships[] 追加更新 (AC: #4)
  - [ ] 4.1: 检测目标概念是否已在 relationships[] 中存在
  - [ ] 4.2: 已存在时在该条目的 ei_techniques / se_summary 字段追加新内容
  - [ ] 4.3: 更新 `modified` 时间戳
  - [ ] 4.4: rationale 更新为最新讨论总结

- [ ] Task 5: 测试 (AC: #1~#5)
  - [ ] 5.1: 单元测试 relationships[] 写入：frontmatter 字段完整性、schema 正确
  - [ ] 5.2: 单元测试双端一致性：A→B 和 B→A 对称记录正确
  - [ ] 5.3: 单元测试 71x 压缩：graph.json 读取 vs 全文读取的 token 对比
  - [ ] 5.4: 集成测试：完整关系创建 → 双端同步 → 压缩检索流程
  - [ ] 5.5: 单元测试追加更新：已存在关系的正确追加

## Dev Notes

- **核心依赖**: Story 3.1（概念提取）提供 `wiki/concepts/*.md` 文件和 `extracted_from` schema
- **Anchor PRD 引用**: §1.3 Edge 对话 EI+SE (line 374-502) 定义了关系的 schema（已从独立 edge.md 迁移至 concept.md frontmatter relationships[]）
- **Anchor PRD 引用**: §6.4 71x token 减少 (line 5911-5923) 定义了压缩检索的应用场景
- **设计变更（用户确认 2026-04-13）**: 取消独立 edges/ 目录和 edge.md 文件，改为 concept.md frontmatter relationships[] 字段。原因：双向链接 + Tag 已足够定义关系，独立文件增加不必要的复杂度
- **Graphify graph.json 互补**: graph.json 提供 71x 压缩的关系数据，concept.md relationships[] 提供完整的 EI/SE 问答历史。两者服务不同场景
- **去重规则**: relationships[] 中按 target wikilink 去重，同一 target 只有一条记录（追加更新而非新建）

### Project Structure Notes

```
wiki/concepts/
  <slug>.md                          # 修改：frontmatter 新增 relationships[] 字段
                                     # （替代原 edges/ 目录方案）
```

### References

- Anchor PRD §1.3 Edge 对话: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 374-502)
- Anchor PRD §3.1 目录结构: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3258-3333)
- Anchor PRD §6.4 71x token 减少: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 5911-5923)
- BMAD PRD FR-KG-06, FR-KG-07: `_bmad-output/planning-artifacts/prd.md` (line 416-417)
- Story 3.1 概念提取: `_bmad-output/implementation-artifacts/epic-3/3-1-concept-extraction-wikilink.md`
- Story 3.2 Graphify: `_bmad-output/implementation-artifacts/epic-3/3-2-graphify-relation-extraction.md`

## UAT Script

> 1. 确保 `wiki/concepts/admissibility.md` 和 `wiki/concepts/a-star.md` 存在
> 2. 通过 `/edge_discuss` 讨论两个概念的关系（后续 Story 6.1 实现触发，本 Story 测试 frontmatter 写入）
> 3. 验证 `wiki/concepts/admissibility.md` frontmatter 的 relationships[] 中有指向 `[[a-star]]` 的记录
> 4. 验证该记录包含 semantic_type / rationale / confidence / created 字段
> 5. 验证 `wiki/concepts/a-star.md` frontmatter 的 relationships[] 中有对称的指向 `[[admissibility]]` 的记录
> 6. 再次讨论同一对概念，验证 relationships[] 条目被追加更新而非重复创建

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| relationships[] 写入 | unit | `pytest tests/unit/test_concept_relationships.py::test_add_relationship -x` | frontmatter 完整 |
| 双端一致性 | unit | `pytest tests/unit/test_concept_relationships.py::test_bidirectional_consistency -x` | 两端对称记录 |
| 去重逻辑 | unit | `pytest tests/unit/test_concept_relationships.py::test_deduplication -x` | 同 target 不重复 |
| 71x 压缩 | unit | `pytest tests/unit/test_concept_relationships.py::test_token_compression -x` | 压缩比 > 50x |
| 追加更新 | unit | `pytest tests/unit/test_concept_relationships.py::test_append_to_existing -x` | 追加不重复 |
| 完整流程 | integration | `pytest tests/integration/test_relationship_creation_e2e.py -x` | 创建 → 双端同步 → 检索 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

**批注处理记录 (2026-04-13)**
1. **edge.md 取消** (用户确认): 独立 edges/ 目录和 edge.md 文件方案全面替换为 concept.md frontmatter relationships[] 字段。原因：双向链接 + Tag 已足够定义关系，独立文件增加不必要复杂度。
2. **Story 标题变更**: "Edge 关系文件 + 71x 压缩检索" → "概念关系 Frontmatter + 71x 压缩检索"。71x 压缩检索部分（Graphify graph.json）保持不变。
3. **双端一致性**: 新增 AC #2 关于 relationships[] 双端对称记录的要求，替代原来的 edges 文件回引机制。

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
