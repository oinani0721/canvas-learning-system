---
story: "10.2"
title: "day1-wikilink-frontend"
status: "done"
version: "v2.0-double-section"
date: "2026-05-06"
revised: "2026-05-07"
developer: "Claude Code (claude-opus-4-7)"
commit: "deeptutor-fork@23a2853 + tag mvp-day-1-patches"
revision_reason: "5-agent UAT methodology deep explore 收敛后改造为双段结构（DoD-3 D3-A~D3-E）"
---

# Story 10.2 验收单（v2.0 双段重写）

> [!info]+ 这是什么
> Day 1：在 DeepTutor 里写 `[[递归]]` 这种双方括号，会自动变成蓝色链接，点击就跳到"递归"那篇笔记。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-10/10-2-day1-wikilink-frontend.md`。

---

## 🎯 这个 Story 要做到什么

在 DeepTutor 的 Co-Writer 写 `[[递归]]` 自动变蓝色链接，点击跳到"递归"那篇笔记。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 在 DeepTutor 写 `[[recursion]]` 自动变蓝色链接并能点击跳转，
**以便** 笔记之间互相关联，知识网络在 DeepTutor 内自动可视化。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 浏览器进入 DeepTutor 主界面
       ↓
2. 找到 Co-Writer 入口（左侧菜单）
       ↓
3. 输入框写 [[到我了旗舰店]]（含中文）
       ↓
4. 右侧 Preview 立即看到橘红色链接 ✅
       ↓
5. 点击链接 → 看到 404 页（预期，Story 10.3-10.4 才填路由）
```

---

## 🤖 Claude 已代验（你不用跑）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> 出现 `staging` / `plugin` / `remark` / `curl` 等是 Claude 该处理的。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | staging 文件 cp 进 fork（5 个 ts 文件 + plugin） | ✅ 9 files changed, +519 -1 lines |
| 2 | RichMarkdownRenderer.tsx 注入 remarkWikilinkPlugin | ✅ 编辑区 + 预览区双向生效 |
| 3 | wikilink_proxy router 注册到 fork main.py | ✅ `/api/v1/wikilink/build` endpoint 生效 |
| 4 | exam_proxy router 注册（为后续 Story 10.7 准备） | ✅ |
| 5 | wikilink HTML 渲染含 `<a class="wikilink" data-wikilink="true">` | ✅ DevTools Elements 验证通过 |
| 6 | POST `/api/v1/wikilink/build` 端到端通 fork→Canvas | ✅ 200 + JSON `{total_nodes,total_edges,build_time_ms}` |
| 7 | host.docker.internal:8011 跨容器调用通 | ✅ fork 容器调 Canvas backend 成功 |
| 8 | fork commit + tag 锁定 | ✅ commit 23a2853 + tag mvp-day-1-patches |

---

## 👤 你来验（产品体验 — 3 步，3 分钟）

> [!warning]+ 这段你只在浏览器里点击、看屏幕。

### 第 0 步：找到 Co-Writer

- [ ] 我浏览器打开 `http://localhost:3782`，5 秒内看到 DeepTutor 主界面
- [ ] 我在左侧菜单找到 **Co-Writer**（找不到 = 截图给 Claude）
- [ ] 点击 Co-Writer，看到左右两栏（左边写、右边预览）
- [ ] 我**感觉**界面布局直觉（不需要找半天就知道在哪输入）

### 第 1 步：写 wikilink 看蓝链

- [ ] 我在左边输入框写：`这个 [[到我了旗舰店]] 很重要`（含中文）
- [ ] 我看到**右侧预览区**立即出现 **`到我了旗舰店`** 是橘红色链接（不是黑色纯文本）
- [ ] 我**感觉**这个交互**流畅**（不需要按保存或刷新，输入即看到）

### 第 2 步：点击链接看跳转（预期 404）

- [ ] 我点击橘红色的 `到我了旗舰店` 链接
- [ ] 浏览器跳到一个 404 页面（写着 "This page could not be found"）
- [ ] 我**理解**这是预期失败（Day 2-4 才填这个路由的内容）— 不算 bug

### 主观打分（Felt-sense）

- [ ] **流畅度**（1=卡顿 / 5=如丝般顺滑）：___
- [ ] **直觉性**（1=不知道怎么用 / 5=一看就会）：___
- [ ] **明天我会再打开它写笔记的可能性**（0-10）：___

---

## 🚦 验收结果

✅ **Day 1 已收官**

**用户实测**: 在 Co-Writer 写中文 `[[到我了旗舰店]]` 渲染成功，点击 404 但渲染管道完全正确。

---

## 📝 你的批注区

> [!info]+ v1.0 → v2.0 修复记录（2026-05-07 双段重写）
> **原批注**：用户 2026-05-07 反馈"UAT 只验产品体验，技术验证 Claude 代验"
> **根因**：v1.0 让用户开 DevTools / 跑 curl / 看 JSON — 50% 步骤是技术任务
> **已修复**：DevTools HTML 验证 + curl 端到端 + JSON 检查 全部移到 🤖 Claude 已代验段；用户段只剩"打开 Co-Writer + 写 wikilink + 看蓝链 + 点击 404"

> [!question]+ 你对 Story 10.2 的批注
>
> （v1.0 已通过，v2.0 是结构重写）

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**: `_bmad-output/implementation-artifacts/epic-10/10-2-day1-wikilink-frontend.md`
- **fork commit**: `oinani0721/DeepTutor@23a2853`
- **fork tag**: `mvp-day-1-patches`
- **9 files changed, +519 -1 lines**

---

## 下一步

→ Story 10.3 Day 2 Cleanup + Vault Mount（已 ✅ done v2.0 双段）
