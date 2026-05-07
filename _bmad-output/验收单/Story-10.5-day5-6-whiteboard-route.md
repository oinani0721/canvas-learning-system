---
story: "10.5"
title: "day5-6-whiteboard-route"
status: "ready"
version: "v0.1-spec"
date: "2026-05-11"
---

# Story 10.5 验收单（给你看的版本）

## 🎯 这个 Story 要做到什么

加一个"白板视图"页面（`/whiteboard/:id`），全 vault 节点画在一张图上，可以点击、拖拽、缩放，节点颜色显示你的掌握度——**像 Canvas 原白板一样**。

## 📖 用户故事

**作为** 学习者，**我想** 在 DeepTutor 看到全 vault 知识地图（不限于单个 book），点节点跳详情，**以便** "原白板作为 index 呈现各节点关系" 的体验完整承载。

## 🖥️ 你会看到的交互

```
1. DeepTutor 左侧 Sidebar 多 "Whiteboard" tab
       ↓
2. 点击 → 进入 /whiteboard/<vault_book_id>
       ↓
3. 大画布显示 ≥10 节点 + 边（不是 Mermaid 静态图）
       ↓
4. 节点颜色：绿（高掌握）/ 黄 / 红（低掌握）
       ↓
5. 点节点 → 右侧 ChatPanel 打开 + 节点 metadata
       ↓
6. 拖节点 → 流畅移动
       ↓
7. 滚轮 → 缩放
```

## ✅ 验收清单（6 步 UAT）

### 第 0 步：前置

- [ ] Story 10.4 已 done（vault 注入为 book）
- [ ] vault 至少 10 个真实笔记 + 双链关系

### 第 1 步：进入 Whiteboard

- [ ] 浏览器 :3782 → 左侧 Sidebar 找 "Whiteboard" tab
- [ ] 点击 → 进入 `/whiteboard/<book_id>`（自动选第一个白板）
- [ ] **不是 404**（路由已注册）

### 第 2 步：节点渲染

- [ ] 大画布显示 ≥10 节点（圆形或矩形）
- [ ] 节点之间有连线（双链关系）
- [ ] 节点显示 label（笔记标题）

### 第 3 步：交互测试

- [ ] **点节点**（如 "recursion"）→ 右侧 ChatPanel 打开
- [ ] ChatPanel 显示节点 metadata（title, mastery%, last_review）
- [ ] **拖节点** → 节点位置移动（不卡）
- [ ] **滚轮缩放** → 画布缩放（不破裂）

### 第 4 步：节点着色（mastery）

- [ ] 至少 3 个节点显示不同颜色
- [ ] 鼠标悬停 → tooltip 显示 mastery 百分比
- [ ] 颜色映射: 绿 ≥80% / 黄 50-80% / 红 <50%

### 第 5 步：边样式（relation 类型）

- [ ] depends_on 边: 实线 + 箭头
- [ ] extends 边: 虚线 + 箭头
- [ ] related 边: 点划线（无方向）

### 第 6 步：性能

- [ ] 50 节点同时显示 → 拖拽不卡
- [ ] 浏览器 DevTools Performance → 60fps 渲染

## 🚦 验收结果

完成后填: ✅/❌ 节点交互 + mastery 着色 + 性能 ≥30fps

## 📝 你的批注区

> [!question]+ 你对 Story 10.5 的批注

## 🔗 技术 spec

`_bmad-output/implementation-artifacts/epic-10/10-5-day5-6-whiteboard-route.md`

## 下一步

→ Story 10.6 Day 7 MasteryDashboard Block（节点掌握度数据上图）
