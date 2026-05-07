---
story_id: "10.9"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["10.8"]
blocks: []
trace: ["FR-DEEP-09", "S1-S5"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 10"
target_date: "2026-05-16"
final_tag: "mvp-complete"
go_no_go_decision: "A/B/C 三选一"
uat_sheet: "_bmad-output/验收单/Story-10.9-day10-uat-final.md"
---

# Story 10.9: Day 10 UAT 收官 + go/no-go 决策

**Status**: ready-for-dev (target Day 10, 2026-05-16)

## Story（用户故事）

As a project lead, I want all 5 validation scenarios (S1-S5) to pass end-to-end so that the MVP is ready for go/no-go decision: continue fork (A) / fall back to independent package (B) / hybrid (C).

> **映射对**: 5 验证场景全部 + 决策矩阵（Round-22 §七）

## 通俗化解释（给学习者）

> **一句话说**: 用一天时间把 Day 1-9 做的所有功能跑一遍，5 个场景全过 = MVP 成功；用户写一份"决定文档"决定后续路径。

**你会遇到的场景**:
- 跟着 5 个 UAT 验收单（Story 10.1 - 10.8）逐项点击操作
- 每个场景标 ✓ 或 ✗
- 全部 ✓ + 你 5 天都在用 → 路径 A（继续 fork production）
- 任何 ✗ 或用 < 6 天 → 路径 B（独立包重做）
- 5 个核心只用 2-3 个 → 路径 C（混合）

**这个功能帮你**:
- 验证 10 天投入是否真的解决了你的痛点
- 避免"做了但没人用"的浪费
- 给后续 1-2 月路径选择决策依据

**用个比喻**: 🏁 就像高考完出成绩单——5 个 S 是 5 门科目，全过 = 上"继续 fork"那条赛道，挂科 = 转独立包赛道。

## Acceptance Criteria

### AC #1: 5 验证场景全过

- **Given** Day 1-9 全部 commit + tag
- **When** 跑 UAT 矩阵（手工 + curl + 浏览器）
- **Then** S1 wikilink 跳转 < 1s ✓
- **And** S2 ACP quiz → mastery 更新 ✓
- **And** S3 AutoSCORE 4 维分数显示 ✓
- **And** S4 Whiteboard ≥10 节点 + 边渲染 ✓
- **And** S5 答错 → Day 0/3/7 推送 console ✓

### AC #2: 代码质量

- **Given** Day 10 收官前
- **When** 跑测试套件
- **Then** `pytest deeptutor-fork/tests/` 全过（不破现有功能）
- **And** `npm run build` 无 TypeScript 错误
- **And** 0 hardcoded credentials in code（全部 .env）

### AC #3: 决策文档 + 推荐

- **Given** 5 验证矩阵填完
- **When** 写 `DECISION-DAY-10.md`
- **Then** 含决策矩阵（A/B/C 三路径 + 当前条件）
- **And** 推荐路径 + 理由（基于 5 验证 + 5 天主动用）
- **And** 后续 1-2 月里程碑（A=4-8 周生产硬化 / B=2-4 周独立包 / C=6-10 周拆分）

### AC #4: Final commit + tag

- **Given** Day 10 收官
- **When** 提交所有改动
- **Then** fork commit msg 含 `EPIC1-BMAD-DEV-ASSESS-2026-04-17` Plan ID
- **And** 打 tag `mvp-complete`
- **And** 不 push upstream（NEG-3）

## Tasks / Subtasks

### Validation 矩阵（手工跑）

- [ ] Task 1: S1 Wikilink 端到端
  - [ ] 1.1: 浏览器 :3782 → Co-Writer 写 `[[recursion]]`
  - [ ] 1.2: 渲染为蓝链 ✓
  - [ ] 1.3: 点击 → 跳转 < 1s ✓
  - [ ] 1.4: callout 内 `[[xxx]]` 也渲染（Story 10.3 修复后）

- [ ] Task 2: S2 ACP Quiz
  - [ ] 2.1: 右键 callout → "Generate Quiz via Canvas ACP"
  - [ ] 2.2: 后端调 `:8011/api/v1/exam/start` 返回 question + pipeline_token
  - [ ] 2.3: DeepTutor quiz 块渲染 question
  - [ ] 2.4: 答题 → mastery 更新

- [ ] Task 3: S3 AutoSCORE
  - [ ] 3.1: 答错题
  - [ ] 3.2: Canvas `/exam/score` 返回 4 维（correctness/clarity/rigor/process）
  - [ ] 3.3: FeedbackModal 显示 4 维分数
  - [ ] 3.4: Dashboard mastery 趋势更新

- [ ] Task 4: S4 Whiteboard
  - [ ] 4.1: 进入 `/whiteboard/<vault_book_id>`
  - [ ] 4.2: ReactFlow 渲染 ≥10 节点 + 边
  - [ ] 4.3: 拖节点流畅
  - [ ] 4.4: 点节点 → ChatPanel 弹出

- [ ] Task 5: S5 推送
  - [ ] 5.1: 答错题
  - [ ] 5.2: Canvas error_loop 落库
  - [ ] 5.3: APScheduler 每分钟拉 Canvas due
  - [ ] 5.4: console 显示 `[REVIEW DUE] node_id at T+0/3/7`

### 测试 + 质量

- [ ] Task 6: 跑全套测试
  - [ ] 6.1: `cd deeptutor-fork && pytest tests/` 全过
  - [ ] 6.2: `cd web && npm run build` 无错
  - [ ] 6.3: `grep -rn "sk-xxx\|TODO\|FIXME" .` 检查残留 mock

- [ ] Task 7: 性能 smoke
  - [ ] 7.1: Whiteboard 50 节点 → 不卡
  - [ ] 7.2: 10 quiz 连续答题 → 响应 < 1s
  - [ ] 7.3: DevTools Memory 无 leak

### 决策文档

- [ ] Task 8: 写 DECISION-DAY-10.md (AC: #3)
  - [ ] 8.1: 在 fork 仓库根目录新建 `DECISION-DAY-10.md`
  - [ ] 8.2: 填写 5 场景结果表（PASS / FAIL + root cause）
  - [ ] 8.3: 决策矩阵评估（A/B/C 三选项条件）
  - [ ] 8.4: 推荐路径 + 1-2 月后续里程碑

### Commit + Tag (AC: #4)

- [ ] Task 9: Final commit
  - [ ] 9.1: `git add -A`（除 .env 在 .gitignore）
  - [ ] 9.2: `git commit -m "feat: day-10 mvp-complete (5/5 scenarios pass)\n\nPlan: EPIC1-BMAD-DEV-ASSESS-2026-04-17"`
  - [ ] 9.3: `git tag mvp-complete`
  - [ ] 9.4: `git log --oneline | head -5` 验证 commit

- [ ] Task 10: Canvas worktree 同步收官
  - [ ] 10.1: Canvas worktree 也 commit 整 epic-10 + 验收单 + 决策批注
  - [ ] 10.2: tag `epic-10-mvp-complete` (区别 fork 仓库的 tag)

## Validation Matrix

| # | 场景 | Pre-condition | Action | Expected | Result | Notes |
|---|---|---|---|---|---|---|
| **S1** | Wikilink 跳转 | DeepTutor 笔记含 `[[recursion]]` | 点击链接 | 跳到 recursion < 1s | TBD | wikilink render OK? |
| **S2** | ACP → mastery | 答对 quiz 题 | 提交答案 | Canvas `/mastery` 被调，mastery.value↑ | TBD | 后端代理通？ |
| **S3** | AutoSCORE | 答错 quiz 题 | 提交错误答案 | 4 维分数面板显示 | TBD | callout 修复 OK? |
| **S4** | Whiteboard | Day 4 vault 已注入 | `/whiteboard/:id` | ≥10 节点 + 边，拖拽 OK | TBD | ReactFlow 性能 OK? |
| **S5** | Heartbeat | 答错题，等待 | console 检查 | `[REVIEW DUE]` 推送 | TBD | 推送通道通？ |

## 决策矩阵（Round-22 §七）

```
默认决策规则:
- IF (S1 ✓ AND S2 ✓ AND S3 ✓ AND S4 ✓ AND S5 ✓)
  AND (用户主动用 ≥ 5 days)
  THEN 推荐 Path A (继续 fork)

- IF (任何 scenario ✗) OR (用户用 < 6 days)
  THEN 推荐 Path B (退回独立包)

- IF (ALL scenarios ✓) AND (用户只用 ≤ 3 cores)
  THEN 考虑 Path C (混合)
```

### 后续路径里程碑

**Path A（5 ✓ + 5 天主动用）**：
- Week 2-5: Production hardening（UI polish + error handling）
- Week 6-8: Upstream sync 策略 + test suite 完整化
- Week 9+: Monthly maintenance + features
- Deliverable: `oinani0721/DeepTutor` 生产 fork

**Path B（任何 ✗ 或 < 6 天用）**：
- Week 1-2: 抽核心逻辑 → `deeptutor-canvas` PyPI package
- Week 3-4: Package tests + docs
- Deliverable: 独立 Python package，零 fork 维护

**Path C（≤ 3 cores 用）**：
- Week 1-3: 拆出高价值 modules（如 CanvasVaultAdapter）
- Week 4-10: 分别维护 fork lite + package 增强
- Deliverable: fork lite + package 混合方案

## Dev Notes

### 5 验证场景的诚实判定
- 每个 ✓ 必须有截图或 curl 输出证据
- 失败时记录 root cause（不是简单"过/不过"）
- 用户连续 5 天主动用 = 真实价值验证（非工程指标）

### 不 push upstream（NEG-3）
- MVP 期间 fork 仅 push 到 oinani0721/DeepTutor（个人 GitHub）
- 不 push 到 HKUDS/DeepTutor（不打扰原作者）
- Day 10 后再决定 path A 是否提 PR 给上游

### 决策文档的工程价值
- 给 1-2 月后的"为什么我们当时做了 X 选择"留存证据
- 包含失败 root cause = 诚实回顾，避免后续浪费

## UAT 验收

详见 `_bmad-output/验收单/Story-10.9-day10-uat-final.md`（用户最终拍板版）

## References

- Round-22 主报告 §四 5 验证场景
- Round-22 主报告 §七 决策矩阵
- Deep Explore §3.3 完整 Day 10 路线
- 所有前置 Story 10.1 ~ 10.8

## 收官后

- 整合 5 个 UAT 结果到决策文档
- 用户做最终路径选择（A/B/C）
- 启动后续 1-2 月计划

**Epic-10 完成 = Round-22 决策从计划走到落地。** 🎯
