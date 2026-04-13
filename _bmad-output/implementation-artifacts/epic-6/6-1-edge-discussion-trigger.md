---
story_id: "6.1"
epic_id: "6"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 8
depends_on: ["2.1", "3.3"]
blocks: ["6.2", "6.3"]
trace:
  - "FR-EDGE-01"
  - "FR-EDGE-04"
---

# Story 6.1: Edge 讨论触发 + 上下文注入

Status: ready-for-dev

## Story

As a 学习者,
I want 选中两个概念间的关系启动深度讨论，系统自动注入两端概念的掌握度和历史记忆,
So that 我能基于完整上下文深入理解概念间的连接。

## Acceptance Criteria

1. **Given** 学习者在某个 `wiki/concepts/*.md` 笔记中写出包含两个 wikilink 的文本（如 `[[admissibility]] 决定了 [[a-star]] 的最优性`）
   **When** 选中这一整行并触发 `/edge_discuss`（Cmd+Option+R）
   **Then** Skill 解析选中文本，抽取 `[[A]]` 和 `[[B]]` 两个概念 slug
   **And** 启动深度讨论对话

2. **Given** `/edge_discuss` 成功解析两个概念
   **When** 系统准备讨论上下文
   **Then** 自动注入两端概念的掌握度数据（bkt_p_mastery / fsrs_stability / fsrs_difficulty）
   **And** 注入两端概念的历史记忆（通过 Graphiti 三层检索：过去的 EI/SE 问答、错误历史、讨论摘要）
   **And** 注入两端 concept.md frontmatter 中已有的 `relationships[]` 记录（如果存在指向对方的条目）

3. **Given** 上下文注入完成
   **When** AI 开始讨论
   **Then** AI 首先询问学习者"为何认为这两个概念相关"（EI 开场）
   **And** AI 的提问基于注入的掌握度数据（对低掌握度概念侧重基础澄清，对高掌握度概念侧重深度追问）
   **And** LLM 首 token 延迟 < 5s P95（NFR-PERF）

4. **Given** 选中文本中包含的 wikilink 不足 2 个
   **When** 触发 `/edge_discuss`
   **Then** 系统提示"请选中包含两个 [[概念]] 的文本"
   **And** 不启动讨论

5. **Given** 选中文本中包含超过 2 个 wikilink
   **When** 触发 `/edge_discuss`
   **Then** 系统取前两个 wikilink 作为讨论对象
   **And** 提示"检测到多个概念，将讨论 [[A]] 和 [[B]] 的关系"

6. **Given** `/chat_with_context` 对话进行中
   **When** LLM 检测到用户文本中有 `[[X]]` wikilink 且当前概念的 frontmatter relationships[] 中无指向 X 的记录
   **Then** 主动提示"发现 [[X]] 的关系尚未记录，Cmd+Option+R 可以讨论这条边"
   **And** 提示不打断当前对话流

7. **Given** Graphiti 服务不可用
   **When** 学习者触发 `/edge_discuss`
   **Then** 系统降级为仅注入 frontmatter 掌握度数据（不注入历史记忆）
   **And** 在讨论开头通知"历史记忆暂不可用，仅基于当前掌握度讨论"

## Tasks / Subtasks

- [ ] Task 1: `/edge_discuss` Skill 定义与 wikilink 解析 (AC: #1, #4, #5)
  - [ ] 1.1: 创建 Claudian skill 定义文件 `.claude/skills/edge-discuss/SKILL.md`
  - [ ] 1.2: 实现选中文本的 wikilink 解析：正则匹配 `\[\[([^\]]+)\]\]` 提取所有概念 slug
  - [ ] 1.3: 验证逻辑：< 2 个 wikilink 提示重新选择；> 2 个取前两个并通知
  - [ ] 1.4: 绑定 hotkey Cmd+Option+R

- [ ] Task 2: 两端概念上下文组装 (AC: #2)
  - [ ] 2.1: 读取 `wiki/concepts/<A>.md` 和 `wiki/concepts/<B>.md` 的 frontmatter（bkt_p_mastery / fsrs_stability / fsrs_difficulty / errors[] / tips[]）
  - [ ] 2.2: 通过 Graphiti 三层检索（search_memory_facts）获取两个概念的历史记忆（过去的 EI/SE 问答、错误历史、讨论摘要）
  - [ ] 2.3: 检查两端 concept.md frontmatter relationships[] 中是否已有指向对方的记录，存在则读取 rationale / ei_techniques / se_summary 历史
  - [ ] 2.4: 组装上下文结构体 `EdgeDiscussContext`：包含两端 frontmatter + 历史记忆 + 已有 relationships[] 数据

- [ ] Task 3: AI 讨论启动与掌握度适配 (AC: #3)
  - [ ] 3.1: 构造 system prompt 模板，包含 EI 开场指令："先问学习者为何认为 {A} 和 {B} 相关"
  - [ ] 3.2: 实现掌握度适配逻辑：bkt_p_mastery < 0.5 时 prompt 偏重基础澄清；>= 0.5 时偏重深度追问和边界情况
  - [ ] 3.3: 注入 `EdgeDiscussContext` 到 LLM 上下文
  - [ ] 3.4: 添加延迟监控：记录上下文组装耗时 + LLM 首 token 耗时

- [ ] Task 4: 未记录关系的主动提示 (AC: #6)
  - [ ] 4.1: 在 `/chat_with_context` skill 中增加 wikilink 扫描逻辑：检测用户文本中的 `[[X]]`
  - [ ] 4.2: 对每个检测到的 wikilink，检查当前概念的 frontmatter relationships[] 中是否有指向 X 的记录
  - [ ] 4.3: 不存在时在 AI 响应末尾追加提示："发现 [[X]] 的关系尚未记录，Cmd+Option+R 可以讨论"
  - [ ] 4.4: 提示频率控制：同一 wikilink 在同一对话中最多提示一次

- [ ] Task 5: 降级处理 (AC: #7)
  - [ ] 5.1: Graphiti 不可用时捕获异常，返回空历史记忆
  - [ ] 5.2: 降级时仅注入 frontmatter 数据（掌握度 + Tips + errors）
  - [ ] 5.3: 在 system prompt 中追加降级通知文本

- [ ] Task 6: 测试 (AC: #1~#7)
  - [ ] 6.1: 单元测试 wikilink 解析：正常 2 个、< 2 个、> 2 个场景
  - [ ] 6.2: 单元测试上下文组装：两端 frontmatter + 历史记忆 + Edge 历史
  - [ ] 6.3: 单元测试掌握度适配：低/高 mastery 的 prompt 差异
  - [ ] 6.4: 集成测试：完整 `/edge_discuss` 从 wikilink 选取到 AI 首轮回复
  - [ ] 6.5: 降级测试：Graphiti 不可用时仍能启动讨论
  - [ ] 6.6: 集成测试：未记录 Edge 的主动提示正确触发

## Dev Notes

- **核心依赖**: Story 2.1（AI 对话 + 上下文注入）提供 `context_enrichment` 和 `ChatContextAssembler` 基础设施
- **核心依赖**: Story 3.3（概念关系 Frontmatter + 71x 压缩检索）提供 concept.md frontmatter relationships[] 结构和 71x 压缩检索
- **Anchor PRD 引用**: §1.3 Edge 对话 EI+SE (line 374-502) 定义了 `/edge_discuss` 的 workflow、frontmatter schema 和双端回引
- **Canvas 独创**: Edge 对话是 PRD 13-gap-diagnosis §5.1 Agent C 标注的"Canvas 独创，全球零竞品"功能
- **触发方式**: Obsidian 没有"点击连线"UI 事件，方案 A 用"选中含 wikilink 文本 + hotkey"替代
- **学术边界**: Edge 对话不是 Active Recall（两端概念可见），而是 EI + SE。d=1.50 归属检验白板
- **缓解可发现性损失**: `/chat_with_context` 中主动提示未记录关系（relationships[] 中无对应条目）、`/review_profile` 检测无关系记录的 wikilink
- **Graphiti 三层检索**: search_memory_facts(group_id="canvas-dev") 获取历史讨论

### Project Structure Notes

```
.claude/skills/edge-discuss/
  SKILL.md                           # 新增：/edge_discuss skill 定义
.claude/skills/chat-with-context/
  SKILL.md                           # 修改：增加未记录 Edge 提示逻辑
```

### References

- Anchor PRD §1.3 Edge 对话 EI+SE: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 374-502)
- BMAD PRD FR-EDGE-01, FR-EDGE-04: `_bmad-output/planning-artifacts/prd.md` (line 371, 374)
- Story 2.1 AI 对话: `_bmad-output/implementation-artifacts/epic-2/2-1-ai-dialog-context-injection.md`
- Story 3.3 概念关系 Frontmatter: `_bmad-output/implementation-artifacts/epic-3/3-3-edge-relationship-files.md`
- Pressley et al. (1987) Elaborative Interrogation, JEP:General 116(3): 291-300, d = 0.80
- Chi et al. (1994) Self-Explanation, Cognitive Science 18(3): 439-477, d = 1.00

## UAT Script

> 1. 打开 `wiki/concepts/admissibility.md`
> 2. 在笔记中写一行：`[[admissibility]] 决定了 [[a-star]] 的最优性`
> 3. 选中这一整行，按 Cmd+Option+R 触发 `/edge_discuss`
> 4. 验证 AI 首轮回复询问"为什么你认为 admissibility 和 a-star 相关？"
> 5. 验证 AI 回复中引用了两端概念的掌握度信息
> 6. 验证首次回复时间 < 5 秒
> 7. 尝试选中仅含 1 个 wikilink 的文本触发，验证提示"请选中包含两个概念的文本"
> 8. 在普通对话中提到 `[[consistent-heuristic]]`（且当前概念 relationships[] 中无对应记录），验证 AI 主动提示

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| wikilink 解析 | unit | `pytest tests/unit/test_edge_discuss.py::test_wikilink_parsing -x` | 正确提取 slug |
| 不足 2 个 wikilink | unit | `pytest tests/unit/test_edge_discuss.py::test_insufficient_wikilinks -x` | 提示信息正确 |
| 上下文组装 | unit | `pytest tests/unit/test_edge_discuss.py::test_context_assembly -x` | 两端数据完整 |
| 掌握度适配 | unit | `pytest tests/unit/test_edge_discuss.py::test_mastery_adaptation -x` | 低/高 mastery prompt 差异 |
| 完整讨论流程 | integration | `pytest tests/integration/test_edge_discuss_e2e.py -x` | 从触发到 AI 回复 |
| Graphiti 降级 | integration | `pytest tests/integration/test_edge_discuss_degradation.py -x` | 降级通知出现 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

**批注处理记录 (2026-04-13)**
1. **edge.md → frontmatter**: 所有 "创建 edge.md" 引用改为 "更新两端概念的 frontmatter relationships[]"。/edge_discuss Skill 仍存在但写入目标从独立文件改为 frontmatter 字段。
2. **未记录 Edge 提示**: AC #6 的检测逻辑从 "edges/ 目录下无对应 Edge 文件" 改为 "frontmatter relationships[] 中无对应记录"。

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
