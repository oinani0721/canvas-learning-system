---
story_id: "3.1"
epic_id: "3"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["1.2"]
blocks: ["3.2", "3.3", "3.4"]
trace:
  - "FR-KG-01"
  - "FR-KG-02"
---

# Story 3.1: 概念提取 + Wikilink 创建

Status: ready-for-dev

## Story

As a 学习者,
I want 从对话或考察中提取新概念时自动创建双向链接文件并维护链接完整性,
So that 知识图谱随学习过程自然增长，概念之间的关系通过 wikilink 自动形成。

## Acceptance Criteria

1. **Given** 学习者在对话中选中一段有价值的文本
   **When** 触发 `/extract_node`（Cmd+Option+X）
   **Then** 系统调用 LLM 抽取概念名（slug 格式，如 `consistent-heuristic`）和简短描述
   **And** 在 `wiki/concepts/` 下创建新 `.md` 文件，包含 Templater 标准 frontmatter（title / slug / type:concept / subject / canvas / bkt_p_mastery:0.30 / fsrs_stability:0 / confidence:EXTRACTED / extracted_from schema）

2. **Given** 新概念文件已创建
   **When** 系统更新原笔记
   **Then** 在选中文本位置插入 `[[new-concept]]` wikilink
   **And** 在原笔记 frontmatter 的 `extracted_nodes` 列表中追加新概念 slug
   **And** Obsidian Backlinks pane 自动显示双向链接

3. **Given** 提取过程中系统检测到已有同名概念文件
   **When** `wiki/concepts/<slug>.md` 已存在
   **Then** 系统跳过文件创建，仅在原笔记中插入 wikilink
   **And** 通知学习者"概念已存在，已链接"

4. **Given** 新概念被提取
   **When** 系统分析上下文
   **Then** 自动建议与原概念的关系类型（depends_on / refines / extends / contradicts / related_to）
   **And** 在新概念文件的 `parent_concepts` 字段中记录原概念 slug
   **And** 关系建议基于 LLM 对选中文本语义的分析

5. **Given** `/extract_node` 从三种场景之一触发（对话 / 考察 / Edge 讨论）
   **When** 系统创建概念文件
   **Then** `extracted_from` schema 字段正确记录来源类型（`chat_session` / `exam_board` / `edge_discussion`）、来源文件路径和父节点 slug
   **And** 可通过 Dataview 查询 `FROM "wiki/concepts" WHERE extracted_from.type = "exam_board"` 追溯出处

6. **Given** LLM 服务不可用
   **When** 学习者触发 `/extract_node`
   **Then** 系统降级为用户手动输入概念名和描述
   **And** 仍然创建标准 frontmatter 文件和 wikilink

## Tasks / Subtasks

- [ ] Task 1: `/extract_node` Skill 定义与 LLM 概念抽取 (AC: #1, #4)
  - [ ] 1.1: 创建 Claudian skill 定义文件 `.claude/skills/extract-node/SKILL.md`，定义 5 步 workflow（读取上下文 → LLM 抽取 → 创建文件 → 更新原笔记 frontmatter → 插入 wikilink）
  - [ ] 1.2: 实现 Step 1 — 读取 Claudian 当前对话上下文 + 选中文本，识别当前活动笔记路径
  - [ ] 1.3: 实现 Step 2 — 调用 LLM 抽取概念名（slug 格式）+ 生成简短描述 + 推断 `parent_concepts` 和关系类型（depends_on / refines / extends / contradicts / related_to）
  - [ ] 1.4: 实现关系类型建议的 prompt 模板，基于选中文本语义分析

- [ ] Task 2: 概念文件创建与 Templater frontmatter (AC: #1, #5)
  - [ ] 2.1: 实现 Step 3 — Write `wiki/concepts/<slug>.md`，使用 `templates/concept.md` 模板生成标准 frontmatter
  - [ ] 2.2: frontmatter 包含完整字段：title / slug / type:concept / subject（从当前活动笔记继承）/ canvas / aliases / tags / parent_concepts / bkt_p_mastery:0.30 / fsrs_stability:0 / confidence:EXTRACTED
  - [ ] 2.3: 实现 `extracted_from` schema 字段，根据触发场景设置 type（chat_session / exam_board / edge_discussion）、source_file、parent_node、extracted_at
  - [ ] 2.4: 生成概念文件 body：`## 定义` 段落（LLM 生成描述）+ `## 来源对话` 段落（`[[sessions/<session-id>#^<block-id>]]` wikilink）

- [ ] Task 3: 原笔记更新与 wikilink 插入 (AC: #2, #3)
  - [ ] 3.1: 实现 Step 4 — 更新当前活动笔记 frontmatter，在 `extracted_nodes` 列表追加新概念 slug
  - [ ] 3.2: 实现 Step 5 — 在选中文本位置插入 `[[<slug>]]` wikilink
  - [ ] 3.3: 实现同名概念检测：检查 `wiki/concepts/<slug>.md` 是否已存在，存在则跳过创建，仅插入 wikilink 并通知
  - [ ] 3.4: 确保 wikilink 插入不破坏原文格式（LaTeX 公式、代码块内不插入）

- [ ] Task 4: 降级处理 (AC: #6)
  - [ ] 4.1: LLM 不可用时切换为手动模式：弹出输入框让用户输入概念名和描述
  - [ ] 4.2: 手动模式仍创建标准 frontmatter 文件（confidence 设为 EXTRACTED，extracted_from.trigger 设为 user_manual）
  - [ ] 4.3: 降级通知用户 "LLM 暂不可用，已切换为手动模式"

- [ ] Task 5: 测试 (AC: #1~#6)
  - [ ] 5.1: 单元测试 LLM 概念抽取：正常抽取、slug 格式化、关系类型建议
  - [ ] 5.2: 单元测试文件创建：frontmatter schema 完整性、extracted_from 三种场景
  - [ ] 5.3: 单元测试 wikilink 插入：正常插入、同名概念跳过、公式内不插入
  - [ ] 5.4: 集成测试：完整 5 步 workflow 从 skill 触发到双向链接形成
  - [ ] 5.5: 降级测试：LLM 不可用时手动模式完整流程

## Dev Notes

- **核心依赖**: Story 1.2（wikilink 图构建）提供 vault 目录结构和 frontmatter schema 基础
- **Anchor PRD 引用**: §1.2 Generation Effect (line 277-373) 定义了 `/extract_node` 的 5 步 workflow 和 frontmatter schema
- **Anchor PRD 引用**: §3.2 frontmatter schema (line 3341-3461) 定义了 `wiki/concepts/*.md` 的完整字段规范
- **Templater 模板**: `templates/concept.md` 是新概念文件的模板，必须包含所有 frontmatter 字段
- **extracted_from 统一 schema**: 三种场景（对话 / 考察 / Edge 讨论）共用同一个 `extracted_from` schema（PRD §1.2 Plan v16 B6 锁定）
- **slug 格式**: kebab-case，全小写，如 `consistent-heuristic`（不含中文字符，中文概念用 aliases 字段）

### Project Structure Notes

```
.claude/skills/extract-node/
  SKILL.md                           # 新增：/extract_node skill 定义
wiki/concepts/
  <slug>.md                          # 新增：提取的概念文件
templates/
  concept.md                         # 参考：概念文件模板
```

### References

- Anchor PRD §1.2 `/extract_node` workflow: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 277-373)
- Anchor PRD §3 目录结构: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3258-3461)
- BMAD PRD FR-KG-01, FR-KG-02: `_bmad-output/planning-artifacts/prd.md` (line 411-412)
- Story 1.2 wikilink 图构建: `_bmad-output/implementation-artifacts/epic-1/1-2-wikilink-graph-build.md`
- Slamecka & Graf (1978) Generation Effect, JEP:Human Learning and Memory 4(6): 592-604, d = 0.65

## UAT Script

> 1. 打开 Obsidian vault，导航到 `wiki/concepts/admissibility.md`
> 2. 在 Claudian sidebar 对话中，选中一段文字 "consistent heuristic 是 admissibility 的更强条件"
> 3. 按 Cmd+Option+X 触发 `/extract_node`
> 4. 验证 `wiki/concepts/consistent-heuristic.md` 被创建，frontmatter 包含 title / type:concept / parent_concepts:[admissibility] / confidence:EXTRACTED / extracted_from.type:chat_session
> 5. 验证 `admissibility.md` 的文本中出现了 `[[consistent-heuristic]]` wikilink
> 6. 在 `consistent-heuristic.md` 中验证 Backlinks pane 显示 `admissibility.md` 的反向引用
> 7. 再次选中相同概念触发 `/extract_node`，验证提示"概念已存在，已链接"且不重复创建文件

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| LLM 概念抽取 | unit | `pytest tests/unit/test_extract_node_skill.py::test_concept_extraction -x` | slug 正确 + 描述非空 |
| frontmatter schema | unit | `pytest tests/unit/test_extract_node_skill.py::test_frontmatter_completeness -x` | 全部必填字段存在 |
| wikilink 插入 | unit | `pytest tests/unit/test_extract_node_skill.py::test_wikilink_insertion -x` | wikilink 格式正确 |
| 同名概念检测 | unit | `pytest tests/unit/test_extract_node_skill.py::test_duplicate_detection -x` | 跳过创建 + 通知 |
| 完整 workflow | integration | `pytest tests/integration/test_extract_node_e2e.py -x` | 5 步全部完成 |
| LLM 降级 | integration | `pytest tests/integration/test_extract_node_degradation.py -x` | 手动模式可用 |

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
