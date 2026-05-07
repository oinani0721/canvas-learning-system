---
story: "11.3"
title: "vault-integration-rendering"
status: "backlog"
version: "v1.0"
date: "2026-05-07"
developer: "TBD（Day 15 启动）"
commit: "TBD"
---

# Story 11.3 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 11.3 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-11/11-3-vault-integration-rendering.md`。

> [!warning]+ 此 Story 处于 backlog
> 前置：Story 11.2 完成。Day 15 启动。**核心 Story（M4 映射对最强）**。

---

## 🎯 这个 Story 要做到什么

在应用内看到 AI 生成的动画视频和图表，还能点击笔记中的链接跳转。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 在应用窗口内看到 AI 生成的动画/图表 + 点击笔记中的双链跳转，
**以便** 整个学习体验在一个窗口里完成（不弹浏览器、不切设备）。

---

## 🖥️ 你会看到的交互（一步一步）

**场景 A：Math Animator 视频**
```
1. 在应用 chat 输入框输入"讲解二次函数的顶点"
       ↓
2. 点击发送
       ↓
3. 进度条显示"生成中..."（约 30-60 秒）
       ↓
4. 完成后，结果区显示一个视频播放器
       ↓
5. 点击播放，看到数学动画（流畅播放，可拖动进度条）
```

**场景 B：Visualize 图表**
```
1. 输入"画出 y=log(x) 的函数图"
       ↓
2. 点击发送
       ↓
3. AI 完成后，结果区显示一个交互式图表
       ↓
4. 鼠标悬停可显示数值
```

**场景 C：Wikilink 导航**
```
1. 在笔记中看到 [[递归]] 文本（蓝色链接）
       ↓
2. 点击链接
       ↓
3. 应用跳转到"递归"这篇笔记，内容显示更新
       ↓
4. 导航栏显示面包屑或返回按钮
```

---

## ✅ 验收清单（15 步 UAT — 此 Story 是 M4 最强映射，必跑全清单）

### 第 0 步：前置

- [ ] Story 11.1 + 11.2 已通过
- [ ] 准备测试 vault 含 wikilink 的 .md 文件（至少 5 个相互关联）

### 第 1 步：Math Animator MP4 视频

- [ ] 输入"讲解二次函数顶点"，发送
- [ ] AI 生成视频成功（不出错）
- [ ] 视频在应用窗口内播放（**不弹出**外部播放器）
- [ ] 支持播放/暂停
- [ ] 支持拖动进度条
- [ ] 支持全屏

### 第 2 步：Visualize - SVG 图表

- [ ] 输入"画一个简单 SVG 图标"，发送
- [ ] AI 返回 SVG 代码
- [ ] 应用内显示 SVG 图形
- [ ] 图形清晰可见

### 第 3 步：Visualize - Chart.js 折线图

- [ ] 输入"画出 y=log(x) 函数图"，发送
- [ ] AI 返回 Chart.js 代码
- [ ] 应用内渲染交互式折线图
- [ ] 鼠标悬停显示数值

### 第 4 步：Visualize - Mermaid 流程图

- [ ] 输入"画一个简单的程序流程图"，发送
- [ ] AI 返回 Mermaid 代码
- [ ] 应用内渲染流程图
- [ ] 节点 + 箭头清晰可见

### 第 5 步：Visualize - HTML 图表

- [ ] 输入"用 HTML 显示一个表格"，发送
- [ ] AI 返回 HTML 代码
- [ ] 应用内显示（隔离沙箱）
- [ ] 表格样式正常

### 第 6 步：Visualize - auto 模式

- [ ] 输入"画出函数 sin(x) 的图"
- [ ] AI 自动选择最佳渲染方式
- [ ] 应用内显示对应内容

### 第 7 步：Wikilink 渲染

- [ ] 打开包含 `[[xxx]]` 的笔记
- [ ] `[[xxx]]` 渲染为蓝色可点击链接
- [ ] 鼠标悬停显示链接目标提示

### 第 8 步：Wikilink 跳转

- [ ] 点击链接 → < 100ms 跳转到目标笔记
- [ ] 目标笔记内容显示
- [ ] 导航栏更新（显示当前位置）
- [ ] 返回按钮可用

### 第 9 步：Wikilink 边界

- [ ] 点击 `[[不存在的笔记]]` → 提示"笔记不存在"（不崩溃）
- [ ] 点击中文 `[[递归]]` → 正确跳转
- [ ] Cmd/Ctrl + Click → 可在新窗口打开（如有）

### 第 10 步：网络隔离 + 离线渲染

- [ ] 断网（disable WiFi）
- [ ] Math Animator 仍可生成 MP4（FastAPI subprocess 本地）
- [ ] Visualize 仍可渲染图表
- [ ] 网络监控确认无外网请求

### 第 11 步：性能

- [ ] 笔记加载时间 < 200ms
- [ ] wikilink 跳转 < 100ms
- [ ] Math Animator 视频生成时间合理（< 90 秒）

### 第 12 步：边界 + 错误恢复

- [ ] AI 生成失败时显示友好错误（不崩溃）
- [ ] 视频加载失败时显示重试按钮
- [ ] CDN 离线时 Chart.js / Mermaid 仍可用（本地 fallback）

---

## 🚦 验收结果

**全部 ✅** → 说 "**Story 11.3 通过**"。

**有 ❌** → 批注区记录。

---

## 📝 你的批注区

> [!question]+ 你对 Story 11.3 的批注
>
> （空）

### 已知的已批注问题

（空）

---

## 🔗 技术 spec 参考

- **Story spec**: `_bmad-output/implementation-artifacts/epic-11/11-3-vault-integration-rendering.md`
- **关联 Story**: `epic-10/10-5-day5-6-whiteboard-route.md`（Math/Visualize 在 Whiteboard 集成）
- **决策批注**: `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md`
- **调研报告**: 
  - `_bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md` §六（5 render_mode 完整对照）
  - `_bmad-output/research/round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md` §五（Math/Visualize 渲染分析）
- **源代码**:
  - `desktop/web/hooks/useVaultFile.ts`
  - `desktop/web/components/whiteboard/VisualizationRenderer.tsx`
  - `desktop/web/components/whiteboard/MathAnimatorPlayer.tsx`
  - `desktop/web/components/common/RichMarkdownRenderer.tsx` (wikilink 拦截)
- **Git commit**: TBD
- **AC → 代码对应**:
  - AC #1 → `useVaultFile.ts` (hook)
  - AC #2 → `RichMarkdownRenderer.tsx` (wikilink interception)
  - AC #3 → `MathAnimatorPlayer.tsx`
  - AC #4 → `VisualizationRenderer.tsx` (5 modes)
  - AC #5 → 网络监控验证

---

## 下一步

1. **通过** → Story 11.4（跨平台发布 + 自动更新）
2. **不通过** → correct-course
