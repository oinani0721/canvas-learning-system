---
story_id: "4.8"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["4.5", "3.4"]
blocks: []
trace:
  - "FR-EXAM-14"
  - "FR-EXAM-20"
---

# Story 4.8: 考中书签式概念提取

Status: ready-for-dev

## Story
As a 学习者,
I want 考察中发现新概念时不中断考察,
So that Active Recall 不被打断（保持 d=1.50 效应量 + 同时获得 Generation Effect d=0.65）。

## Acceptance Criteria

1. **Given** 学习者在考察中遇到不懂的概念 **When** 学习者在 md 编辑器中表达"不懂 X"（或使用快捷键触发提取）**Then** skill 在当前 exam_boards/*.md 中插入 `[!discussion_later]+` 书签 callout **And** 不切换 Tab **And** 不中断当前考察流程

2. **Given** 书签 callout 被插入 **When** 系统创建新概念节点 **Then** 在 `wiki/concepts/` 目录下创建 `<concept-slug>.md`，只含 frontmatter stub（无 body 内容）**And** frontmatter 包含 `type: concept`、`source: exam_extraction`、`extracted_at` 时间戳 **And** 自动创建从源节点到新节点的 wikilink

3. **Given** 新节点创建完成 **When** 更新 exam_boards/*.md frontmatter **Then** `new_nodes_pulled[]` 数组追加新节点的 slug **And** 考察继续原题（回到出题循环）

4. **Given** 考察结束后 **When** 学习者查看书签 **Then** 通过 `[!discussion_later]+` callout 可以快速定位所有待讨论概念 **And** 点击 wikilink 可跳转到新创建的 wiki/concepts/<slug>.md **And** 学习者可以在 wiki/concepts/ 中对新节点进行深入剖析讨论

5. **Given** 考察中学习者确认的新节点 **When** 学习者选择深入讨论 **Then** 必须在考察结束后进行（不在考察中讨论）**And** 深入讨论使用剖析模式（/start_analysis skill）而非考察模式

6. **Given** 书签式提取过程 **When** 执行 **Then** 整个过程耗时 < 2 秒（不影响考察节奏）**And** exam_boards/*.md 中的书签 callout 格式统一

## Tasks / Subtasks

- [ ] Task 1: 实现书签 callout 插入 (AC: #1)
  - [ ] 检测"不懂 X"关键词或快捷键触发
  - [ ] 在 exam_boards/*.md 当前位置插入 `[!discussion_later]+` callout
  - [ ] callout 格式：`> [!discussion_later]+ 待讨论: {concept_name}\n> 来源: 考察 Q{i}\n> [[{concept-slug}]]`
  - [ ] 确保不中断当前考察流程

- [ ] Task 2: 实现新概念节点创建 (AC: #2)
  - [ ] 在 wiki/concepts/ 下创建 `<concept-slug>.md`
  - [ ] frontmatter stub: type/source/extracted_at/status
  - [ ] 自动 wikilink 创建
  - [ ] 不含 body 内容（等考后剖析时填充）

- [ ] Task 3: 更新 exam frontmatter (AC: #3)
  - [ ] 追加 new_nodes_pulled[]
  - [ ] 考察继续不中断

- [ ] Task 4: 实现考后书签导航 (AC: #4)
  - [ ] `[!discussion_later]+` callout 可在 Obsidian 中搜索过滤
  - [ ] wikilink 跳转正常工作
  - [ ] Dataview 查询支持

- [ ] Task 5: 实现讨论时机控制 (AC: #5)
  - [ ] 考察中禁止对新节点进入剖析模式
  - [ ] 考察结束后提示可跳转到待讨论节点

- [ ] Task 6: 性能保障 (AC: #6)
  - [ ] 书签提取 < 2 秒
  - [ ] 异步创建节点文件，不阻塞 UI

## Dev Notes

### Architecture
- 书签式提取保留两个认知收益：Active Recall d=1.50（不中断考察）+ Generation Effect d=0.65（概念提取本身就是 generation）
- `[!discussion_later]+` 是 Obsidian 自定义 callout 类型
- 新节点只含 frontmatter stub，避免在考察中生成内容（防止信息泄漏到考察环境）
- 考后通过 /start_exam_board Step 10 提示用户跳转到待讨论节点
- Story 3.4 依赖：需要节点创建和 wikilink 管理的基础设施

### File Paths
- 书签 callout 插入：skill Edit 操作在 exam_boards/*.md
- 新节点创建：wiki/concepts/<slug>.md
- 节点提取逻辑：anchor PRD §2.7.1
- ExamService：`backend/app/services/exam_service.py`

### Testing
- 单元测试：书签 callout 格式、节点 stub 创建、frontmatter 更新
- 集成测试：考察中提取 → 书签插入 → 节点创建 → 考后导航完整链路
- 性能测试：提取耗时 < 2 秒

### Project Structure Notes
- new_nodes_pulled[] 只存 slug，实际文件在 wiki/concepts/
- `[!discussion_later]+` 的 "+" 保证 callout 默认展开

### References
- **From PRD**: §2.3 Step 7.8 — 书签式提取 (line 1146-1151)
- **From PRD**: §2.7.1 书签式概念提取详细设计
- FR-KG-04: 考察中提取新概念不中断流程
- Generation Effect: d=0.65 (Slamecka & Graf, 1978)

## UAT Script

> 1. 在考察中遇到不懂的概念
> 2. 在 md 编辑器中输入"不懂 consistent-heuristic"
> 3. 看到 `[!discussion_later]+` 书签 callout 被插入
> 4. 确认考察未中断，当前题目仍在
> 5. 查看 wiki/concepts/consistent-heuristic.md 已创建（只含 frontmatter）
> 6. 完成考察后，通过书签点击 wikilink 跳转到新节点
> 7. 在新节点中使用剖析模式深入讨论

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 书签 callout 格式 | unit | `pytest tests/unit/test_bookmark_callout.py -x` | 0 failures |
| 节点 stub 创建 | unit | `pytest tests/unit/test_concept_stub_creation.py -x` | 0 failures |
| Frontmatter 更新 | unit | `pytest tests/unit/test_new_nodes_pulled.py -x` | 0 failures |
| 提取性能 | perf | `pytest tests/perf/test_bookmark_extraction_time.py -x` | < 2000ms |
| 书签集成 | integration | `pytest tests/integration/test_exam_bookmark_flow.py -x` | 0 failures |

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
