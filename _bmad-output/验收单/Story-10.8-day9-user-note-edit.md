---
story: "10.8"
title: "day9-user-note-edit"
status: "ready"
version: "v0.1-spec"
date: "2026-05-15"
---

# Story 10.8 验收单（给你看的版本）

## 🎯 这个 Story 要做到什么

在 DeepTutor 阅读 book 或看 whiteboard 节点详情时，能现场写自己的笔记（不用切到 Obsidian），写完自动保存，下次回来还在。

## 📖 用户故事

**作为** 学习者，**我想** 思考的瞬间能在 DeepTutor 写笔记并自动保存到 vault md，**以便** 不打断学习流程，笔记永远是 Obsidian 真相源。

## 🖥️ 你会看到的交互

```
1. 在 whiteboard 看节点详情（ChatPanel）或 book 阅读
       ↓
2. 找 "+ 添加笔记" 按钮
       ↓
3. 点击 → 出现 textarea 编辑器
       ↓
4. 输入笔记 (markdown 格式)
       ↓
5. 点击外面或 Cmd+S → 自动保存（debounce 500ms）
       ↓
6. 笔记立即显示在页面上
       ↓
7. 关闭浏览器 + 重开 → 笔记还在
       ↓
8. 检查 vault md 文件 → 看到 annotation 已写入 ✅
```

## ✅ 验收清单（6 步 UAT）

### 第 0 步：前置

- [ ] Story 10.7 已 done
- [ ] whiteboard / book 都可见 + 至少 1 个节点

### 第 1 步：找编辑入口

- [ ] 进入 whiteboard → 点节点 → ChatPanel
- [ ] 看到 "+ 添加笔记" 按钮（或类似入口）
- [ ] 点击 → textarea 出现

### 第 2 步：写笔记

- [ ] 输入 "这个跟昨天学的 X 类似 - 都是 [[递归]] 思想"
- [ ] markdown 渲染应支持基础语法（`**粗体**` `[[wikilink]]`）
- [ ] 输入流畅（无 lag）

### 第 3 步：自动保存

- [ ] 点击 textarea 外面（blur）
- [ ] 看到 "Saving..." 然后变 "Saved"
- [ ] textarea 关闭，渲染笔记内容

### 第 4 步：持久化验证

- [ ] 关闭浏览器（完全退出）
- [ ] 重开 :3782
- [ ] 回到同节点 → **笔记还在**

### 第 5 步：vault 真相源同步

- [ ] 终端 `cat ~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp/canvas-vault/节点/<node_name>.md`
- [ ] **md 文件含你刚写的 annotation**（vault 是真相源）

### 第 6 步：离线 + 同步

- [ ] 断 wifi
- [ ] 写笔记 → blur
- [ ] 看到 "Saved offline (will sync)" 提示
- [ ] 接 wifi → 5 秒内自动同步

## 🚦 验收结果

完成后填: ✅/❌ 编辑流畅 + 自动保存 + 持久化 + vault 同步 + 离线兜底

## 📝 你的批注区

> [!question]+ 你对 Story 10.8 的批注
>
> 验证 UX-1（批注是核心）+ UX-4（Graphiti 同步）

## 🔗 技术 spec

`_bmad-output/implementation-artifacts/epic-10/10-8-day9-user-note-edit.md`

## 下一步

→ Story 10.9 Day 10 UAT 收官 + go/no-go 决策
