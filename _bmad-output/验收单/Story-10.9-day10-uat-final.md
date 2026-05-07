---
story: "10.9"
title: "day10-uat-final"
status: "ready"
version: "v0.1-spec"
date: "2026-05-16"
---

# Story 10.9 验收单（给你看的版本，最终拍板）

> [!info]+ 这是什么
> Day 10 收官 UAT。用一天时间把 Day 1-9 做的所有功能跑一遍，5 个场景全过 = MVP 成功。

---

## 🎯 这个 Story 要做到什么

跑完 5 个 S 验证场景 + 写决策文档 + 选择后续路径（A/B/C）。

---

## 📖 用户故事

**作为** 项目主导（学习者），**我想** Day 10 跑一遍 5 个 S 验证场景全过 + 文档化决策，**以便** 投入决策（继续 fork production / 退回独立包 / 混合）有数据依据。

---

## 🖥️ 5 验证场景（按顺序跑，每个 ≤ 2 min）

```
S1 Wikilink 跳转 (Day 1)
S2 ACP Quiz 生成 (Day 4)
S3 AutoSCORE 4 维 (Day 7)
S4 Whiteboard 节点 (Day 5-6)
S5 错误推送 (Day 8)
```

---

## ✅ 5 验证矩阵（必填）

### S1 Wikilink 跳转

- [ ] 浏览器 :3782 → Co-Writer 写 `[[recursion]]`
- [ ] 渲染为蓝链 ✓
- [ ] 点击 → 跳到 recursion 笔记 < 1s
- [ ] **结果**: ✅ PASS / ❌ FAIL
- [ ] **如果 FAIL**: 描述 root cause（render 不出？跳转 404？）

### S2 ACP Quiz

- [ ] 在 callout `> [!question]+` 内右键 → "Generate Quiz via Canvas ACP"
- [ ] 后端调 `:8011/api/v1/exam/start` 返回 question + pipeline_token
- [ ] DeepTutor quiz 块渲染 question
- [ ] 答题 → mastery.value 更新
- [ ] **结果**: ✅ PASS / ❌ FAIL
- [ ] **如果 FAIL**: root cause

### S3 AutoSCORE 4 维

- [ ] 答错题
- [ ] FeedbackModal 显示 4 维分数（correctness/clarity/rigor/process）
- [ ] Dashboard mastery 趋势更新
- [ ] **结果**: ✅ PASS / ❌ FAIL
- [ ] **如果 FAIL**: root cause

### S4 Whiteboard 节点

- [ ] 进入 `/whiteboard/<vault_book_id>`
- [ ] ReactFlow 渲染 ≥10 节点 + 边
- [ ] 拖节点流畅
- [ ] 点节点 → ChatPanel 弹出
- [ ] **结果**: ✅ PASS / ❌ FAIL
- [ ] **如果 FAIL**: root cause

### S5 推送

- [ ] 答错题
- [ ] 等 30-60 秒
- [ ] 终端 `docker logs deeptutor 2>&1 | grep "REVIEW DUE"`
- [ ] 看到 `[REVIEW DUE] node_id at T+0/3/7`
- [ ] **结果**: ✅ PASS / ❌ FAIL
- [ ] **如果 FAIL**: root cause

---

## 🚦 决策矩阵（基于 5 验证 + 5 天主动用）

### 决策规则（Round-22 §七）

```
IF (S1 ✓ AND S2 ✓ AND S3 ✓ AND S4 ✓ AND S5 ✓) AND (主动用 ≥ 5 天)
    → 推荐 Path A (继续 fork)

IF (任何 ✗) OR (主动用 < 6 天)
    → 推荐 Path B (退回独立包)

IF (ALL ✓) AND (主动用 ≤ 3 cores)
    → 考虑 Path C (混合)
```

### 你的最终选择

- [ ] **Path A** — 继续 fork（4-8 周生产硬化）
- [ ] **Path B** — 退回独立包（2-4 周抽 deeptutor-canvas PyPI 包）
- [ ] **Path C** — 混合（6-10 周拆分维护）

**理由**:
（在这写为什么选这条路 — 5 验证结果 + 5 天用感受）

---

## 📋 决策文档（必写）

完成后在 fork 仓库根目录写 `DECISION-DAY-10.md`：

```markdown
# Day 10 MVP Validation Results

## 5 Scenarios
| # | 场景 | Result | Notes |
|---|---|---|---|
| S1 | Wikilink jump | ✓/✗ | ... |
| S2 | ACP quiz | ✓/✗ | ... |
| S3 | AutoSCORE | ✓/✗ | ... |
| S4 | Whiteboard | ✓/✗ | ... |
| S5 | Heartbeat | ✓/✗ | ... |

## Active Usage Days
我从 Day X 到 Day Y 主动用，共 N 天

## Decision
推荐 Path A/B/C，理由：...

## Next Milestones
（按选择路径写后续 1-2 月计划）
```

---

## 📝 commit + tag

完成后:
- [ ] `cd deeptutor-fork && git add -A`
- [ ] `git commit -m "feat: day-10 mvp-complete (S1-S5 result)\n\nPlan: EPIC1-BMAD-DEV-ASSESS-2026-04-17"`
- [ ] `git tag mvp-complete`
- [ ] **不 push upstream**（保持 fork 独立）

---

## 🚦 最终验收结果

完成后填:
- 5 验证: ✅×N / ❌×N
- 主动用天数: N
- 推荐路径: A / B / C
- 后续 1-2 月里程碑: 见 DECISION-DAY-10.md

---

## 📝 你的批注区

> [!question]+ 你对 MVP 整体的批注
>
> 这是用户最终拍板版。任何感受、改进建议、未来期望都写这里。

---

## 🔗 技术 spec

- `_bmad-output/implementation-artifacts/epic-10/10-9-day10-uat-final.md`
- `DECISION-DAY-10.md`（fork 仓库根目录，UAT 完成后写）

---

## Epic-10 完成 = Round-22 决策从计划走到落地 🎯
