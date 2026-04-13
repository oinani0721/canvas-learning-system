---
story_id: "3.4"
epic_id: "3"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 4
depends_on: ["3.1"]
blocks: ["4.8"]
trace:
  - "FR-KG-04"
---

# Story 3.4: 书签式考中提取

Status: ready-for-dev

## Story

As a 学习者,
I want 在考察中提取新概念时不中断当前流程,
So that Active Recall 不被打断，考后可回到书签位置进行深度讨论。

## Acceptance Criteria

1. **Given** 学习者在检验白板考察中发现新概念（说"我不懂 X"）
   **When** 触发 `/extract_node` 提取操作
   **Then** 系统在当前 `exam_boards/*.md` 的 body 中插入 `[!discussion_later]+` callout：
   ```markdown
   > [!discussion_later]+ 待剖析节点
   > 在考察中发现不懂的概念：[[<new-concept-slug>]]
   > 考察结束后建议打开此节点深入讨论
   ```
   **And** 不切换 Tab，不打开新文件

2. **Given** 书签式提取触发
   **When** 系统创建新概念文件
   **Then** 仅创建 `wiki/concepts/<slug>.md` 的 frontmatter stub（title + type:concept + confidence:EXTRACTED + extracted_from.type:exam_board）
   **And** body 为占位内容"待考后填充"
   **And** 不生成完整描述（避免打断考察流程）

3. **Given** 考察过程中多次发现新概念
   **When** 多次触发书签式提取
   **Then** 每次插入独立的 `[!discussion_later]+` callout
   **And** 考察结束时系统汇总提示："你在本次考察中拉出了 N 个新节点（slug1, slug2...），建议明天打开剖析"

4. **Given** 考察结束
   **When** 学习者导航到 `[!discussion_later]+` callout 中的 wikilink
   **Then** 点击 `[[<slug>]]` 可打开对应的 `wiki/concepts/<slug>.md`
   **And** 学习者可在此文件中启动深度讨论（`/chat_with_context`）或补充内容

5. **Given** 书签式提取操作
   **When** 检查考察环境完整性
   **Then** 不泄露 wiki/concepts/ 内容到检验白板（三重保证不被破坏）
   **And** 新创建的 stub 文件不被注入到当前考察上下文
   **And** 考察进度（当前题号、已评分结果）不受影响

## Tasks / Subtasks

- [ ] Task 1: 书签式 callout 插入逻辑 (AC: #1, #5)
  - [ ] 1.1: 在 `/extract_node` skill 中增加考察模式检测：判断当前活动笔记是否在 `exam_boards/` 目录下
  - [ ] 1.2: 考察模式下切换为书签式流程：不生成完整描述，不切换 Tab，仅插入 `[!discussion_later]+` callout
  - [ ] 1.3: callout 内容包含 `[[<slug>]]` wikilink + "考察结束后建议打开此节点深入讨论"
  - [ ] 1.4: 验证插入操作不触发上下文重新加载（不泄露 wiki/ 内容到考察环境）

- [ ] Task 2: Frontmatter stub 创建 (AC: #2)
  - [ ] 2.1: 考察模式下创建 `wiki/concepts/<slug>.md` 时仅写入 frontmatter stub
  - [ ] 2.2: frontmatter 包含：title / slug / type:concept / confidence:EXTRACTED / extracted_from.type:exam_board / extracted_from.source_file（当前 exam_boards/*.md 路径）/ extracted_from.extracted_at
  - [ ] 2.3: body 写入占位内容 `## 待剖析\n\n此概念在考察中发现，待考后深入讨论。`
  - [ ] 2.4: 不调用 LLM 生成描述（零 LLM 调用，保持考察流程不延迟）

- [ ] Task 3: 考察结束汇总提示 (AC: #3)
  - [ ] 3.1: 在 `/start_exam_board` skill 的结束步骤中扫描当前 exam_boards/*.md 的所有 `[!discussion_later]+` callout
  - [ ] 3.2: 提取 callout 中的 `[[slug]]` wikilink 列表
  - [ ] 3.3: 生成汇总提示："你在本次考察中拉出了 N 个新节点（slug1, slug2...），建议明天打开剖析"
  - [ ] 3.4: 汇总信息追加到 exam_boards/*.md 文件末尾的 `## 考察总结` 段落

- [ ] Task 4: 信息隔离验证 (AC: #5)
  - [ ] 4.1: 确保书签式提取不触发 `context_enrichment` 重新加载（不读取新创建的 stub 文件内容）
  - [ ] 4.2: 确保新 stub 文件不出现在当前考察的 LLM 上下文中
  - [ ] 4.3: 确保考察进度变量（题号、评分队列）不受提取操作影响
  - [ ] 4.4: 验证三重保证完整性：type 标记（exam_board）+ AI 上下文不注入 wiki/ + Skill prompt 约束

- [ ] Task 5: 测试 (AC: #1~#5)
  - [ ] 5.1: 单元测试考察模式检测：exam_boards/ 目录下正确触发书签模式
  - [ ] 5.2: 单元测试 callout 插入：格式正确、wikilink 有效
  - [ ] 5.3: 单元测试 stub 创建：frontmatter 完整、body 为占位内容
  - [ ] 5.4: 集成测试：考察中提取 → 考后导航 → 打开 stub → 启动深度讨论
  - [ ] 5.5: 隔离测试：提取后验证考察上下文未包含新 stub 内容

## Dev Notes

- **核心依赖**: Story 3.1（概念提取）提供 `/extract_node` 基础 workflow，本 Story 在其基础上增加考察模式分支
- **核心关联**: Story 4.8（考中书签式概念提取）是 Epic 4 侧的对应 Story，处理检验白板内的集成
- **Anchor PRD 引用**: §1.2 书签式新节点 (line 330-355) 定义了书签式 workflow 和 `[!discussion_later]+` callout 格式
- **Anchor PRD 引用**: §2.7.1 书签式工作流详细步骤 — 用户在 2026-04-09 AskUserQuestion 锁定了"书签式"方案
- **用户决策锁定**: Plan v16 Round 2 锁定书签式而非立即切换，理由：保护 Active Recall d=1.50 + 避免 Claudian Tab 切换问题
- **零 LLM 调用**: 考察模式下的 stub 创建不调用 LLM（与 Story 3.1 的正常模式不同），避免增加考察延迟
- **callout 语法**: Obsidian callout `> [!type]+` 中 `+` 表示默认展开，不带 `+` 表示默认折叠

### Project Structure Notes

```
.claude/skills/extract-node/
  SKILL.md                           # 修改：增加考察模式分支逻辑
exam_boards/
  *.md                               # 修改：插入 [!discussion_later]+ callout
wiki/concepts/
  <slug>.md                          # 新增：frontmatter stub（考后补充）
```

### References

- Anchor PRD §1.2 书签式新节点: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 330-355)
- BMAD PRD FR-KG-04: `_bmad-output/planning-artifacts/prd.md` (line 414)
- Story 3.1 概念提取: `_bmad-output/implementation-artifacts/epic-3/3-1-concept-extraction-wikilink.md`
- Story 4.8 考中书签: `_bmad-output/implementation-artifacts/epic-4/4-8-bookmark-concept-extraction.md`
- Plan v16 Round 2 用户决策: 书签式 > 立即切换（保护 Active Recall d=1.50）

## UAT Script

> 1. 启动检验白板考察（`/start_exam_board`），进入考察模式
> 2. 在考察中说"我不懂 consistent-heuristic"，触发 `/extract_node`
> 3. 验证当前 exam_boards/*.md 中出现 `[!discussion_later]+` callout，包含 `[[consistent-heuristic]]`
> 4. 验证没有切换 Tab、没有打开新文件
> 5. 验证 `wiki/concepts/consistent-heuristic.md` 被创建为 stub（仅 frontmatter，body 为占位）
> 6. 继续考察，验证考察进度不受影响
> 7. 考察结束后，验证汇总提示"拉出了 1 个新节点"
> 8. 点击 callout 中的 `[[consistent-heuristic]]` wikilink，验证可打开 stub 文件

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 考察模式检测 | unit | `pytest tests/unit/test_bookmark_extraction.py::test_exam_mode_detection -x` | exam_boards/ 路径正确识别 |
| callout 插入 | unit | `pytest tests/unit/test_bookmark_extraction.py::test_callout_format -x` | [!discussion_later]+ 格式正确 |
| stub 创建 | unit | `pytest tests/unit/test_bookmark_extraction.py::test_stub_frontmatter -x` | frontmatter 完整 + body 占位 |
| 信息隔离 | integration | `pytest tests/integration/test_bookmark_isolation.py -x` | 上下文无 stub 内容 |
| 考后汇总 | integration | `pytest tests/integration/test_bookmark_summary.py -x` | 汇总节点数正确 |

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
