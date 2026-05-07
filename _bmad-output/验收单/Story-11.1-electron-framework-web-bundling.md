---
story: "11.1"
title: "electron-framework-web-bundling"
status: "backlog"
version: "v1.0"
date: "2026-05-07"
developer: "TBD（Day 11 启动）"
commit: "TBD"
---

# Story 11.1 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 11.1 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-11/11-1-electron-framework-web-bundling.md`（Claude 读的）。

> [!warning]+ 此 Story 处于 backlog
> 触发条件：Epic-10 Day 10 UAT 5 验证场景全 PASS（Path A 选定）。
> Day 11 实际启动日期由用户确认。

---

## 🎯 这个 Story 要做到什么

看到 DeepTutor 应用在你的电脑上作为独立窗口打开，而不是浏览器标签页。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 双击一个应用图标就启动 DeepTutor，
**以便** 不需要每次都开浏览器、记 localhost:3782 这个奇怪的地址。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 打开 macOS Dock / Windows 任务栏 / Linux 应用菜单
       ↓
2. 找到 DeepTutor 图标
       ↓
3. 双击图标
       ↓
4. 等待 2-3 秒（启动中）
       ↓
5. 看到一个独立窗口打开（不是浏览器）
       ↓
6. 窗口内显示熟悉的 DeepTutor UI（导航栏 + 内容区）
```

---

## ✅ 验收清单（10 步 UAT — 你一步步跑，勾掉每一项）

> [!tip]+ 怎么用这份清单
> 每跑完一步，**点击对应的 `- [ ]` 切换为 `[x]`**（Obsidian 原生支持）。
> 发现不对劲 → **选中那一行 → `Cmd+Shift+A` → ❌ 错误 + ❓ 不懂**，把问题批到这个文档里。

### 第 0 步：前置（必须做）

- [ ] Epic-10 Day 10 UAT 全 PASS（5 验证场景 S1-S5）
- [ ] 用户已确认选择 Path A（继续 fork 桌面化）
- [ ] DeepTutor fork Next.js build 产物可用（`npm run build` 已成功）

### 第 1 步：找到应用图标

- [ ] macOS: 在 Applications 文件夹看到 DeepTutor.app
- [ ] Windows: 在开始菜单看到 DeepTutor 快捷方式
- [ ] Linux: 在应用菜单看到 DeepTutor

### 第 2 步：启动应用

- [ ] 双击图标后，等待 2-3 秒，应用启动
- [ ] 启动时间不超过 3 秒（冷启动）
- [ ] 没有黑屏，没有崩溃

### 第 3 步：窗口外观

- [ ] 看到一个**独立窗口**（不是浏览器标签页）
- [ ] 窗口标题是 "DeepTutor" 或类似
- [ ] 窗口尺寸合理（约 1200x800，能看到全部内容）
- [ ] 窗口可以拖动、最小化、最大化

### 第 4 步：UI 完整性

- [ ] 看到熟悉的 DeepTutor 导航栏（Co-Writer / Books 等按钮）
- [ ] CSS 布局正确（颜色、字体、间距正常）
- [ ] 没有"裸 HTML"的样子（说明 Next.js 资源加载成功）
- [ ] 浏览器开发工具（F12 / Cmd+Option+I）可打开（dev mode）

### 第 5 步：基础交互

- [ ] 点击导航栏按钮 → 页面切换正常
- [ ] 刷新页面（Cmd+R / Ctrl+R）→ 内容重新加载
- [ ] 没有控制台报错（DevTools 看 Console 是空的或仅 info）

### 第 6 步：关闭测试

- [ ] 点击窗口关闭按钮（红圆 / X）→ 应用退出
- [ ] 任务管理器检查 → 没有僵尸进程残留
- [ ] 重新打开 → 正常启动（多次启动稳定）

### 第 7 步：边界测试

- [ ] macOS: Cmd+Q 完全退出 vs 仅关闭窗口（应该有区别）
- [ ] 多窗口：不需要支持，但不能崩溃
- [ ] 高分屏（Retina）：UI 清晰不模糊

---

## 🚦 验收结果

**如果所有步骤 ✅**：告诉我 "**Story 11.1 通过**"，Claude 会 mark as **done**。

**如果有任何一步 ❌**：在下面批注区写出具体哪一步 + 你看到的实际现象。

---

## 📝 你的批注区

> [!question]+ 你对 Story 11.1 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

（空 - Day 11 启动前无批注）

<!--
Claude 在 correct-course 后在此处追加 [!error]+ callout:

> [!error]+ {YYYY-MM-DD} — v{N}→v{N+1} 修复记录
> **你的原批注**：{USER_ANNOTATION_VERBATIM}
> **根因**：{ROOT_CAUSE_ANALYSIS_PLAIN_LANGUAGE}
> **已修复**：{FIX_SUMMARY_WHAT_CHANGED}
-->

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**: `_bmad-output/implementation-artifacts/epic-11/11-1-electron-framework-web-bundling.md`
- **Epic 总览**: `_bmad-output/implementation-artifacts/epic-11/_README.md`
- **决策批注**: `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md`
- **调研报告**: `_bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md` §四
- **源代码**: `~/Desktop/canvas/deeptutor-fork/desktop/` (Day 11 创建)
- **Git commit**: TBD（Day 12 完成时填）
- **AC → 代码对应**:
  - AC #1 → `desktop/src/main/main.ts` (BrowserWindow + app events)
  - AC #2 → `desktop/electron-builder.yml` (Next.js standalone bundle)
  - AC #3 → `desktop/src/main/preload.ts` (contextBridge)
  - AC #4 → `desktop/electron-builder.yml` (mac signing config)

---

## 下一步

1. **全部 ✅** → 说 "Story 11.1 通过" → Claude mark done → 启动 Story 11.2 (IPC Bridge)
2. **部分 ❌** → 批注区写清楚，Claude 跑 `bmad-bmm-correct-course` 调整
