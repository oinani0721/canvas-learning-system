---
story_id: "4.11"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 8
depends_on: ["4.3"]
blocks: []
trace:
  - "FR-EXAM-19"
  - "FR-EXAM-09"
superseded_by: "sprint-status.yaml::sprint_v3_obsidian_hybrid.STORY-LITE-4-11"
sprint_v3_status: "deprecated-by-lite-simplification"
deprecated_date: "2026-05-24"
deprecated_plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

> ⛔ **[DEPRECATED] 2026-05-24 Sprint v3 简化决策** — Lite 版替代此完整 spec
>
> - **替代 entry**: `sprint-status.yaml::sprint_v3_obsidian_hybrid.STORY-LITE-4-11`（entry-only，无独立 spec — 简化规则在 entry `simplification` 字段）
> - **简化原因**: 完整 4h 版含 IRT (Item Response Theory) 连续难度算法 — Sprint v3 **保留 callout 快速入口，砍 IRT 连续校准算法** (1h)
> - ⚠️ **新 session 警告**: 看到此 marker → 不读下方 AC，改读 sprint-status entry simplification 字段
> - **Plan**: `EPIC1-BMAD-DEV-ASSESS-2026-04-17`

# Story 4.11: IRT 连续难度匹配 + Callout 批注快速考察

Status: ready-for-dev

## Story
As a 学习者,
I want 题目难度匹配我的掌握水平，且可以从批注触发快速考察,
So that 考察既不太简单也不太难，且可以精准复习特定批注。

## Acceptance Criteria

1. **Given** 系统为节点生成题目 **When** 计算目标难度 **Then** 采用连续 IRT（Item Response Theory）difficulty 参数 **And** 不使用离散分级（Easy/Medium/Hard）**And** difficulty 参数范围 [0.0, 1.0]，基于学习者当前 effective_proficiency 计算

2. **Given** IRT difficulty 计算完成 **When** 传递给 generate_question **Then** LLM prompt 中包含具体的 difficulty 参数指导 **And** 题目难度与学习者掌握度的匹配率 >= 70% **And** 匹配率 = 答对率落在 [difficulty - 0.15, difficulty + 0.15] 区间内的比例

3. **Given** 匹配率统计 **When** 积累足够样本（>= 30 题）**Then** 计算实际匹配率并记录到 structlog **And** 如果匹配率 < 70% 则触发难度校准调整 **And** 校准调整通过 Bayesian 方法更新 difficulty 映射函数

4. **Given** 学习者在知识笔记中选中一个 callout 批注 **When** 触发 `/quiz_from_callout` skill **Then** 基于该批注内容生成针对性题目 **And** 题目紧密关联批注中的知识点 **And** 不需要启动完整的 /start_exam_board 流程（轻量级入口）

5. **Given** callout 快速考察 **When** 生成题目 **Then** 使用该批注所在节点的 effective_proficiency 作为 IRT difficulty 基准 **And** 题目 Bloom 层级 >= 批注对应的认知层级 **And** 答题和评分流程复用 Story 4.5 和 4.6 的 md 编辑器 + 静默评分

6. **Given** callout 快速考察完成 **When** 评分结果更新 **Then** 掌握度更新同正常考察流程（BKT + FSRS）**And** 评分结果记录在当前笔记的 frontmatter 中（非 exam_boards 目录）**And** 可作为 few-shot 校准样本

7. **Given** 难度匹配计算 **When** 首次使用（无历史数据）**Then** difficulty 默认为 0.50（中等）**And** 随着答题积累自动校准

## Tasks / Subtasks

- [ ] Task 1: 实现 IRT 连续难度计算 (AC: #1, #7)
  - [ ] 基于 effective_proficiency 计算 target_difficulty
  - [ ] 映射函数：difficulty = f(effective_proficiency, interaction_count, error_history)
  - [ ] 无历史数据时默认 0.50
  - [ ] 单元测试：各掌握度水平对应的 difficulty 合理性

- [ ] Task 2: 实现难度匹配率验证 (AC: #2, #3)
  - [ ] 匹配率计算：答对率落在 [difficulty - 0.15, difficulty + 0.15] 区间
  - [ ] >= 30 题后开始统计
  - [ ] 匹配率 < 70% 时触发 Bayesian 校准
  - [ ] structlog 记录匹配率和校准事件

- [ ] Task 3: 扩展 generate_question 支持 IRT difficulty (AC: #2)
  - [ ] 添加 difficulty 参数到 GenerateQuestionInput
  - [ ] LLM prompt 中注入 difficulty 指导
  - [ ] 题目生成考虑 difficulty 参数

- [ ] Task 4: 实现 `/quiz_from_callout` skill (AC: #4, #5)
  - [ ] 检测用户选中的 callout 内容
  - [ ] 基于 callout 内容 + 所在节点的 mastery 生成题目
  - [ ] 轻量级流程（无需防嵌套检查、模式选择等）
  - [ ] Bloom 层级 >= 批注认知层级
  - [ ] Hotkey 绑定（与 /start_exam_board 不同的 hotkey）

- [ ] Task 5: 实现 callout 考察的答题评分复用 (AC: #5, #6)
  - [ ] 复用 Story 4.5 的 md 编辑器答题（callout 格式在当前笔记追加）
  - [ ] 复用 Story 4.6 的静默评分（pipeline_token 链）
  - [ ] 评分结果写入当前笔记 frontmatter（非 exam_boards/）
  - [ ] 掌握度更新同正常考察

- [ ] Task 6: 实现 Bayesian 难度校准 (AC: #3)
  - [ ] 基于答题历史更新 difficulty 映射函数
  - [ ] 校准样本权重：recent > old
  - [ ] 校准频率：每 10 题重新计算一次
  - [ ] 单元测试：校准后匹配率提升

## Dev Notes

### Architecture
- IRT (Item Response Theory) 使用连续参数而非离散分级，提供更精准的难度匹配
- difficulty 参数范围 [0.0, 1.0] 与 effective_proficiency [0.0, 1.0] 对齐
- `/quiz_from_callout` 是 `/start_exam_board` 的轻量级姐妹 skill（anchor PRD §4.4）
- Self-Explanation (Chi 1994) 的 d=1.09 是独立于 Active Recall 的学术支撑
- callout 考察不需要信息隔离（信息可见），因此不需要 Story 4.1 的三重保证

### File Paths
- IRT 难度计算：新建 `backend/app/services/irt_difficulty.py`
- quiz_from_callout skill：`.claude/skills/quiz-from-callout/SKILL.md`
- generate_question 扩展：`backend/app/mcp/tools/exam_tools.py`

### Testing
- 单元测试：IRT 难度计算、匹配率验证、Bayesian 校准
- 集成测试：callout 选中 → 出题 → 答题 → 评分 → 掌握度更新
- 统计测试：30+ 题后匹配率 >= 70%

### Project Structure Notes
- `/quiz_from_callout` 是 "第二考察入口"（PRD L785），便利性设计
- callout 考察的题目记录在当前笔记 frontmatter 中，不在 exam_boards/ 目录
- IRT 校准数据可存储在 Graphiti 知识图谱中供跨 session 使用

### References
- **From PRD**: §4.4 `/quiz_from_callout` 大改
- **From PRD**: FR-EXAM-09 批注驱动出题
- **From PRD**: FR-EXAM-19 IRT 连续难度匹配
- Chi et al. (1994): Self-Explanation, d=1.09
- Bisra et al. (2018): Self-Explanation meta-analysis, g=0.55 (n=5,917)
- IRT (Item Response Theory): Hambleton & Swaminathan (1985)

## UAT Script

> 1. 打开一个有多次考察历史的节点
> 2. 触发 `/start_exam_board`
> 3. 观察生成的题目难度是否与自己的掌握水平匹配
> 4. 完成 30+ 题后查看 structlog 中的匹配率统计
> 5. 在知识笔记中选中一个 `[!question]+` callout 批注
> 6. 触发 `/quiz_from_callout`
> 7. 看到基于该批注内容生成的针对性题目
> 8. 在当前笔记中写答案并提交
> 9. 确认评分结果记录在当前笔记 frontmatter 中
> 10. 确认掌握度数据已更新

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| IRT 难度计算 | unit | `pytest tests/unit/test_irt_difficulty.py -x` | 0 failures |
| 匹配率验证 | unit | `pytest tests/unit/test_difficulty_matching_rate.py -x` | >= 70% |
| Bayesian 校准 | unit | `pytest tests/unit/test_bayesian_calibration.py -x` | 0 failures |
| Callout 出题 | unit | `pytest tests/unit/test_quiz_from_callout.py -x` | 0 failures |
| Callout 集成 | integration | `pytest tests/integration/test_callout_exam_flow.py -x` | 0 failures |
| 难度匹配统计 | statistical | `pytest tests/statistical/test_irt_matching_rate.py -x` | rate >= 0.70 |

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
