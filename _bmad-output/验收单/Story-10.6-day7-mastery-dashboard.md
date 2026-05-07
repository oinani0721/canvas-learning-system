---
story: "10.6"
title: "day7-mastery-dashboard"
status: "ready"
version: "v0.1-spec"
date: "2026-05-13"
---

# Story 10.6 验收单（给你看的版本）

## 🎯 这个 Story 要做到什么

答完几道题后，看一份"学习成绩单"——每个概念有掌握度百分比 + FSRS 推荐下次复习时间，知道哪些掌握了哪些没。

## 📖 用户故事

**作为** 学习者，**我想** 看到自己每个概念的掌握度曲线 + 复习排程，**以便** 不用自己排计划，系统帮我定。

## 🖥️ 你会看到的交互

```
1. 答 5+ 道题（在 book/quiz/exam）
       ↓
2. 进入 Dashboard 页面
       ↓
3. 看到 4 列卡片: today_due | day_0 | day_3 | day_7
       ↓
4. 每张卡片含: 概念名 + 掌握度% + 下次复习日期
       ↓
5. 点卡片 → 看掌握度时间曲线（Recharts LineChart）
```

## ✅ 验收清单（5 步 UAT）

### 第 0 步：前置

- [ ] Story 10.5 已 done（whiteboard 节点可见）
- [ ] vault 已注入 + 至少答 5 道 quiz 题

### 第 1 步：BlockType Enum 不破裂

- [ ] 终端 `cd ~/Desktop/canvas/deeptutor-fork && pytest tests/book/`
- [ ] 全过（14 原 BlockType + 1 新 MASTERY_DASHBOARD = 15 个 enum）
- [ ] 现有 quiz/flash_cards 测试不破

### 第 2 步：Dashboard 渲染

- [ ] 浏览器 → Dashboard 菜单
- [ ] 看到 4 列布局: 今日 / Day 0 / Day 3 / Day 7
- [ ] 每列卡片显示 mastery% + next_review 日期

### 第 3 步：mastery 着色

- [ ] 至少 3 个概念显示不同颜色（≥80% 绿, 50-80% 黄, <50% 红）
- [ ] 卡片旁边小图标显示 FSRS stability

### 第 4 步：曲线图

- [ ] 点击某张卡片 → 弹出 Recharts LineChart
- [ ] X 轴时间，Y 轴 mastery (0-1)
- [ ] 至少 3 个数据点（你答的 3 题）

### 第 5 步：实时更新

- [ ] 在另一标签页继续答题
- [ ] 回 Dashboard 标签页 → 刷新或自动 polling 更新
- [ ] mastery 数字立刻变化（不需要等很久）

## 🚦 验收结果

完成后填: ✅/❌ Dashboard 显示 + 曲线 + 实时更新

## 📝 你的批注区

> [!question]+ 你对 Story 10.6 的批注

## 🔗 技术 spec

`_bmad-output/implementation-artifacts/epic-10/10-6-day7-mastery-dashboard.md`

## 下一步

→ Story 10.7 Day 8 ExamWhiteboard + ErrorCandidate（4 类错误归因）
