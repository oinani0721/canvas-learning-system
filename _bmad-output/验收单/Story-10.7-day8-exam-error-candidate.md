---
story: "10.7"
title: "day8-exam-error-candidate"
status: "ready"
version: "v0.1-spec"
date: "2026-05-14"
---

# Story 10.7 验收单（给你看的版本）

## 🎯 这个 Story 要做到什么

答错题后，**你自己选**是哪种错（不是 AI 替你判断）：不懂概念 / 粗心 / 算错 / 手滑——4 选项中选一个。

## 📖 用户故事

**作为** 学习者，**我想** 答错题时系统问"你觉得是哪种错"，让我自我归因，**以便** 错题分类不被 AI 误判，长期收集错误模式精准刷题。

## 🖥️ 你会看到的交互

```
1. 进入 Exam Whiteboard（独立全屏，不嵌套 OriginWhiteboard）
       ↓
2. 答错题 → 提交
       ↓
3. 弹出对话框 4 个明显按钮:
   - PROBLEM_FRAMING（不懂概念）
   - REASONING_FALLACY（推理错）
   - KNOWLEDGE_GAP（知识空白）
   - SUPERFICIAL（粗心/手滑）
       ↓
4. 选一个 → 可选写 user_note
       ↓
5. 提交 → 看到 4 维分数面板（correctness/clarity/rigor/process）
       ↓
6. 30 秒后 console 显示 [REVIEW DUE] 推送 (S5 通过)
```

## ✅ 验收清单（6 步 UAT）

### 第 0 步：前置

- [ ] Story 10.6 已 done（mastery dashboard）
- [ ] BlockType Enum 加 EXAM_WHITEBOARD + ERROR_CANDIDATE = 17 个 enum

### 第 1 步：BlockType Enum 第 2 批不破裂（R1 缓解）

- [ ] `pytest deeptutor-fork/tests/book/`
- [ ] **17 个 BlockType 全可用**（14 原 + 3 新）
- [ ] 现有 quiz/flash_cards/concept_graph 渲染不破

### 第 2 步：进入 Exam Whiteboard

- [ ] 在 book 找 EXAM_WHITEBOARD 块（或独立 exam 模式）
- [ ] **全屏或 modal 布局**（不在 PageReader 流中嵌入）
- [ ] 显示 question + 答案输入框

### 第 3 步：故意答错

- [ ] 输入明显错误答案
- [ ] 点提交
- [ ] **弹出对话框** 4 选项可见

### 第 4 步：错误分类

- [ ] 4 选项明显不是 dropdown（按钮）
- [ ] 鼠标悬停每个选项有解释（i 图标 hover）
- [ ] 选 `KNOWLEDGE_GAP`
- [ ] 可选写 user_note "我不懂递归终止条件"
- [ ] 提交 → 对话框关闭

### 第 5 步：4 维评分

- [ ] FeedbackModal 显示 4 维分数
- [ ] correctness / clarity / rigor / process 都有数字
- [ ] diff 视图: 用户答案 vs 标准答案

### 第 6 步：S5 推送验证

- [ ] 等 30-60 秒
- [ ] 终端 `docker logs deeptutor 2>&1 | grep -i "REVIEW DUE"`
- [ ] **看到 `[REVIEW DUE] node_id at T+0/3/7` 消息**

## 🚦 验收结果

完成后填: ✅/❌ 4 选项对话框 + 4 维评分 + REVIEW DUE 推送

## 📝 你的批注区

> [!question]+ 你对 Story 10.7 的批注
>
> 验证 UX-6 落地（Agent 询问而非替决定）

## 🔗 技术 spec

`_bmad-output/implementation-artifacts/epic-10/10-7-day8-exam-error-candidate.md`

## 下一步

→ Story 10.8 Day 9 UserNote 现场编辑
