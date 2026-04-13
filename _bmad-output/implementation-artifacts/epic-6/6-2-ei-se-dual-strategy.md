---
story_id: "6.2"
epic_id: "6"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["6.1"]
blocks: []
trace:
  - "FR-EDGE-02"
---

# Story 6.2: EI+SE 双策略激活

Status: ready-for-dev

## Story

As a 系统,
I want 在 Edge 讨论中同时激活精细化追问（EI）和自我解释（SE）两种学习策略,
So that 学习者同时练习深度追问和自我解释，达到 d=0.80~1.00 的学习效果。

## Acceptance Criteria

1. **Given** Edge 讨论进行中（`/edge_discuss` 已启动）
   **When** AI 引导讨论
   **Then** 同时激活 Elaborative Interrogation（追问"为什么"）和 Self-Explanation（要求用自己的话解释）
   **And** 两种策略在对话中自然交替，不生硬切换

2. **Given** AI 运用 EI 策略
   **When** 向学习者提问
   **Then** 问题格式为"为什么你认为 X？"或"如果 Y 不成立会怎样？"等追因型问题
   **And** 问题基于学习者上一轮回答中的关键概念点展开
   **And** 问题难度匹配学习者的掌握度（低掌握度问基础"为什么"，高掌握度问边界情况和反例）

3. **Given** AI 运用 SE 策略
   **When** 要求学习者解释
   **Then** 指令格式为"请用自己的话解释 X 对 Y 的具体作用"或"想象你在向一个完全不懂的同学讲解"
   **And** 要求包含具体的类比或例子
   **And** SE 阶段不打断学习者的解释过程（不在解释进行中追加 EI 问题）

4. **Given** 一次 Edge 讨论包含 2-4 轮对话
   **When** 检查整体讨论结构
   **Then** EI 和 SE 策略至少各出现 1 次
   **And** 典型模式：EI 开场（"为什么相关？"）→ SE 深化（"用自己的话解释"）→ EI 追问（"如果不成立会怎样？"）→ SE 总结（"再解释一次完整逻辑"）
   **And** AI 不强制按固定模式，根据学习者回答质量自然选择下一策略

5. **Given** 学习者的回答质量较高（概念准确 + 有具体例子）
   **When** AI 评估回答
   **Then** AI 进入更高难度的 EI 追问（反例、边界、exceptions）
   **And** 如果学习者连续 2 轮高质量回答，AI 可主动提出结束讨论的建议

6. **Given** 学习者的回答质量较低（概念模糊 / 无具体例子）
   **When** AI 评估回答
   **Then** AI 切换为 SE 策略，要求学习者用更简单的语言重新解释
   **And** 提供脚手架式引导（"可以从 X 的定义开始..."）
   **And** 不直接告诉答案

## Tasks / Subtasks

- [ ] Task 1: EI 策略 prompt 模板设计 (AC: #2)
  - [ ] 1.1: 设计 EI 问题生成 prompt 模板，输入为（学习者上一轮回答 + 两端概念 + 掌握度），输出为追因型问题
  - [ ] 1.2: 实现掌握度适配：bkt_p_mastery < 0.5 时生成基础"为什么"问题；>= 0.5 时生成反例和边界问题
  - [ ] 1.3: EI 问题模板库：至少 5 种问题模式（"为什么 X？" / "如果 X 不成立？" / "X 和 Y 的区别？" / "什么条件下 X 会失效？" / "能举一个反例吗？"）
  - [ ] 1.4: 每个 EI 问题记录到 Edge 文件 frontmatter 的 `ei_questions` 列表

- [ ] Task 2: SE 策略 prompt 模板设计 (AC: #3)
  - [ ] 2.1: 设计 SE 指令生成 prompt 模板，输入为（当前讨论阶段 + 学习者回答质量评估），输出为解释请求
  - [ ] 2.2: SE 指令模板库：至少 3 种指令模式（"用自己的话解释" / "想象向不懂的同学讲解" / "用一个类比来说明"）
  - [ ] 2.3: 实现"不打断"约束：检测学习者是否在解释中（回复长度 > 100 字符），是则不追加 EI 问题
  - [ ] 2.4: 每个 SE 回答记录到 Edge 文件 frontmatter 的 `se_answers` 列表

- [ ] Task 3: 策略交替逻辑 (AC: #1, #4)
  - [ ] 3.1: 实现 `StrategySelector` 类，维护当前对话轮次、已使用策略历史、学习者回答质量评估
  - [ ] 3.2: 策略选择规则：
    - 第 1 轮：EI 开场（"为什么相关？"）
    - 后续轮次：根据学习者回答质量选择（高质量 → EI 追问 / 低质量 → SE 脚手架）
    - 最后 1 轮：SE 总结（"再解释一次完整逻辑"）
  - [ ] 3.3: 确保 2-4 轮讨论中 EI 和 SE 各至少出现 1 次
  - [ ] 3.4: 自然交替而非机械轮换：基于回答质量动态选择，不是 EI→SE→EI→SE 固定序列

- [ ] Task 4: 回答质量评估与自适应 (AC: #5, #6)
  - [ ] 4.1: 实现回答质量快速评估（不是 AutoSCORE 级别评分，而是简单的 LLM 判断：概念准确 / 有例子 / 逻辑连贯）
  - [ ] 4.2: 高质量（3/3 维度通过）→ 升级 EI 难度（反例、exceptions）
  - [ ] 4.3: 低质量（< 2/3 维度通过）→ 切换 SE 脚手架引导
  - [ ] 4.4: 连续 2 轮高质量 → AI 建议"你的理解很好，是否要结束讨论？"
  - [ ] 4.5: 低质量时不直接给答案，仅提供脚手架（"可以从 X 的定义开始..."）

- [ ] Task 5: 测试 (AC: #1~#6)
  - [ ] 5.1: 单元测试 EI prompt 生成：不同掌握度下问题差异
  - [ ] 5.2: 单元测试 SE prompt 生成：解释请求格式正确
  - [ ] 5.3: 单元测试策略选择器：2-4 轮讨论中 EI/SE 各至少 1 次
  - [ ] 5.4: 单元测试回答质量评估：高/低质量分类准确
  - [ ] 5.5: 集成测试：完整 Edge 讨论 3 轮，验证策略自然交替
  - [ ] 5.6: 集成测试：连续高质量回答后 AI 建议结束

## Dev Notes

- **核心依赖**: Story 6.1（Edge 讨论触发）提供 `/edge_discuss` skill 和上下文注入基础
- **Anchor PRD 引用**: §1.3 Edge 对话 EI+SE (line 374-502) 定义了 EI 和 SE 的学术根据和交互示例
- **学术根据**:
  - EI: Pressley et al. (1987), JEP:General 116(3): 291-300, d = 0.80（追问"为什么"强制深度加工）
  - SE: Chi et al. (1994), Cognitive Science 18(3): 439-477, d = 1.00（自我解释构建 mental model）
- **学术边界**: Edge 对话不是 Active Recall（两端概念可见），d=1.50 归属检验白板
- **"不告诉答案"原则**: 与检验白板的渐进提示一致，SE/EI 阶段的 AI 只引导不给答案
- **讨论长度**: 典型 2-4 轮，不限制上限但 AI 会在高质量回答后建议结束

### Project Structure Notes

```
.claude/skills/edge-discuss/
  SKILL.md                           # 修改：增加 EI/SE 策略模板和交替逻辑
```

### References

- Anchor PRD §1.3 EI+SE 双策略: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 374-502)
- BMAD PRD FR-EDGE-02: `_bmad-output/planning-artifacts/prd.md` (line 372)
- Story 6.1 Edge 讨论触发: `_bmad-output/implementation-artifacts/epic-6/6-1-edge-discussion-trigger.md`
- Pressley et al. (1987) Elaborative Interrogation, JEP:General 116(3): 291-300, d = 0.80
- Chi et al. (1994) Self-Explanation, Cognitive Science 18(3): 439-477, d = 1.00

## UAT Script

> 1. 触发 `/edge_discuss`（按 Story 6.1 的方式选中含两个 wikilink 的文本）
> 2. 验证 AI 首轮用 EI 策略提问："为什么你认为 X 和 Y 相关？"
> 3. 回答后验证 AI 切换到 SE 策略："请用自己的话解释..."
> 4. 再次回答后验证 AI 回到 EI 策略提出更深入的追问（反例或边界）
> 5. 给出高质量回答（含具体例子），验证 AI 建议"你的理解很好，是否要结束讨论？"
> 6. 给出模糊回答（无例子），验证 AI 提供脚手架引导而非直接告诉答案
> 7. 验证整次讨论中 EI 和 SE 各至少出现 1 次

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| EI prompt 生成 | unit | `pytest tests/unit/test_ei_se_strategy.py::test_ei_question_generation -x` | 追因型问题格式正确 |
| SE prompt 生成 | unit | `pytest tests/unit/test_ei_se_strategy.py::test_se_instruction_generation -x` | 解释请求格式正确 |
| 策略交替 | unit | `pytest tests/unit/test_ei_se_strategy.py::test_strategy_alternation -x` | EI/SE 各 >= 1 |
| 掌握度适配 | unit | `pytest tests/unit/test_ei_se_strategy.py::test_mastery_adaptation -x` | 低/高 mastery prompt 差异 |
| 回答质量评估 | unit | `pytest tests/unit/test_ei_se_strategy.py::test_answer_quality_assessment -x` | 高/低质量分类准确 |
| 完整讨论 | integration | `pytest tests/integration/test_ei_se_discussion.py -x` | 3 轮自然交替 |

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
