---
story: "10.2"
title: "day1-wikilink-frontend"
status: "done"
version: "v1.0"
date: "2026-05-06"
developer: "Claude Code (claude-opus-4-7)"
commit: "oinani0721/DeepTutor@23a2853 + tag mvp-day-1-patches"
---

# Story 10.2 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 10.2 的用户验收文档。技术 spec 在 `_bmad-output/implementation-artifacts/epic-10/10-2-day1-wikilink-frontend.md`。

---

## 🎯 这个 Story 要做到什么

在 DeepTutor 里写 `[[递归]]` 这种双方括号，会自动变成蓝色链接，点击就跳到"递归"那篇笔记。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 在 DeepTutor 写 `[[recursion]]` 自动变蓝色链接，并能点击跳转，
**以便** 笔记之间互相关联，知识网络在 DeepTutor 内自动可视化。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 进入 DeepTutor Co-Writer
       ↓
2. 写 markdown 含 `[[到我了旗舰店]]`
       ↓
3. 右侧 Preview 区显示橘红色链接 "到我了旗舰店"
       ↓
4. 点击链接 → 跳转 (404 是预期，Story 10.3-10.4 才完整)
       ↓
5. DevTools 看到 <a class="wikilink"> 渲染 ✅
```

---

## ✅ 验收清单（4 步 UAT）

> [!tip]+ 怎么用这份清单
> 每跑完一步，**点击 `- [ ]` 切换为 `[x]`**。失败时 `Cmd+Shift+A` 批注。

### 第 0 步：前置

- [x] Story 10.1 已 done（fork + baseline + double services healthy）
- [x] DeepTutor 容器跑在 :8001 + :3782
- [x] Canvas backend 跑在 :8011

### 第 1 步：进入 Co-Writer

- [x] 浏览器打开 :3782
- [x] 左侧 Sidebar 找 "Co-Writer" 菜单项
- [x] 点击 → 看到 split editor（左编辑右预览）

### 第 2 步：写 wikilink

- [x] 在编辑区输入 `[[到我了旗舰店]]`（含中文 OK）
- [x] **右侧 Preview 立即显示橘红色链接 "到我了旗舰店"**

### 第 3 步：DevTools 验证

- [x] 浏览器开 DevTools (`Cmd+Option+I` Mac / `F12` Windows)
- [x] Elements 标签 → 找到刚才的链接
- [x] 看到 HTML 是 `<a class="wikilink" href="/notes/到我了旗舰店" data-wikilink="true">到我了旗舰店</a>`

### 第 4 步：端到端 curl

- [x] 终端跑 `curl -X POST http://localhost:8001/api/v1/wikilink/build`
- [x] 返回 HTTP 200 + JSON `{"data":{"total_nodes":0,"total_edges":0,"build_time_ms":1.5}}`
- [x] 这证明：fork :8001 → wikilink_proxy → CanvasClient → host.docker.internal:8011 → Canvas backend 全链路通

### 第 5 步（可选）：点击链接

- [ ] 点击渲染的 wikilink → 浏览器 URL 变 `/notes/到我了旗舰店`
- [ ] 看到 404 "This page could not be found"（**预期失败 — Day 2 才做 `/notes/[slug]` 路由**）

---

## 🚦 验收结果

✅ **全部通过**（Day 1 完整收官）

证据:
- 浏览器 Co-Writer 渲染 `[[到我了旗舰店]]` 为橘红 wikilink
- DevTools Elements 显示 `<a class="wikilink">`
- POST :8001/api/v1/wikilink/build → 200 + JSON
- 容器 → host.docker.internal:8011 通

---

## 📝 你的批注区

> [!question]+ 你对 Story 10.2 的批注
>
> Day 1 用户实测：在 Co-Writer 写中文 `[[到我了旗舰店]]` 渲染成功，点击 404 但渲染管道完全正确。

---

## 🔗 技术 spec 参考

- **Story spec**: `_bmad-output/implementation-artifacts/epic-10/10-2-day1-wikilink-frontend.md`
- **fork commit**: `oinani0721/DeepTutor@23a2853`
- **fork tag**: `mvp-day-1-patches`
- **9 files changed, +519 -1 lines**

---

## 下一步

→ Story 10.3 Day 2 Cleanup + Vault Mount（CalloutBlock 修 + vault 数据布线）
