---
story: "10.3"
title: "day2-cleanup-vault-mount"
status: "review"
version: "v1.0"
date: "2026-05-07"
developer: "Claude Code (claude-opus-4-7)"
phase: "Phase A only (Phase B optional, deferred)"
commit_fork: "deeptutor-fork@4a17cad"
commit_worktree: "TBD-AFTER-COMMIT"
---

# Story 10.3 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 10.3 的用户验收文档。技术 spec 在 `_bmad-output/implementation-artifacts/epic-10/10-3-day2-cleanup-vault-mount.md`。
> Story 10.3 拆 Phase A（核心修复，今天 ship） + Phase B（vault 主权升级，可选延后）。本验收单只覆盖 Phase A。

---

## 🎯 这个 Story 要做到什么

让 DeepTutor 直接读你 Canvas vault 里的 md 文件（不上传不复制），并且 callout（提示框）里写的 `[[xxx]]` 双链能渲染成蓝色链接。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 在 Obsidian / Canvas vault 里写的笔记（含 callout `> [!question]+ 看 [[递归]]` 这种），DeepTutor 打开同一篇也能识别双链 + 直接读到我的 md 文件，
**以便** 不用上传不用复制，本地写完 DeepTutor 实时看见，知识库 100% 我自己的。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. DeepTutor 后端 :8001 调 wikilink endpoint → 转发到 Canvas :8011
       ↓
2. Canvas backend 直接读你 vault 里的 31 个 md 文件（节点/原白板/根目录全扫）
       ↓
3. 构建 wikilink 图 (31 节点 / 27 双链边)
       ↓
4. 在 DeepTutor Co-Writer 写 callout：
   > [!key_idea]+ Important
   > See [[recursion]] for base case.
       ↓
5. 右侧 Preview 区：callout 框内 `[[recursion]]` 渲染成橘红色链接
       ↓
6. 同样 4 个 block 都生效：Callout / Timeline / FlashCards / DeepDive
```

---

## ✅ 验收清单（7 步 UAT）

> [!tip]+ 怎么用这份清单
> 每跑完一步，**点击 `- [ ]` 切换为 `[x]`**。失败时选中那行 `Cmd+Shift+A` 批注 ❌ 错误。

### 第 0 步：前置（必须做）

- [ ] Story 10.2 已 done（Day 1 wikilink 前端管线已激活）
- [ ] 浏览器打开 http://localhost:3782（DeepTutor frontend）
- [ ] 终端能跑 `docker ps` 看到 3 个容器：`deeptutor` / `canvas-learning-system-backend` / `canvas-learning-system-neo4j`

### 第 1 步：Canvas backend 读到你的 vault md

- [ ] 终端跑 `curl -sf -X POST http://localhost:8011/api/v1/wikilink/build -H "Content-Type: application/json" -d '{}'`
- [ ] 返回 JSON 含 `total_nodes: 31` 和 `total_edges: 27`（数字 ≥ 20 即可）
- [ ] 这证明：vault 里 `节点/`、`原白板/`、根目录的 md 文件已被扫描，wikilink 图已建好

### 第 2 步：测一个真实节点的双链邻居

- [ ] 终端跑 `curl -sf "http://localhost:8011/api/v1/wikilink/neighbors/原白板/CS%2061B.md?hop=2"`
- [ ] 返回 JSON 含 `count: 1` + neighbor `节点/cs-61b-csm`
- [ ] 这证明：双链 `[[xxx]]` 已经被识别，跨 `原白板/` 和 `节点/` 目录的关联也通

### 第 3 步：DeepTutor Co-Writer 渲染 callout 内 wikilink

- [ ] 浏览器进 DeepTutor → 左侧菜单点 "Co-Writer"
- [ ] 编辑区粘贴下面这段：
  ```
  > [!key_idea]+ Important Concept
  > To understand recursion, see [[base-case]] and [[recursion]].
  ```
- [ ] **右侧 Preview 区显示**：黄色背景 callout 框，**框内 `[[base-case]]` 和 `[[recursion]]` 是橘红色链接**（不是纯文本灰色）

### 第 4 步：DevTools 验证 callout 内 wikilink HTML

- [ ] 浏览器开 DevTools (`Cmd+Option+I`)
- [ ] Elements 标签 → 找到 callout 框内的 `[[recursion]]`
- [ ] 看到 HTML 是 `<a class="wikilink" href="/notes/recursion" data-wikilink="true">recursion</a>`（不是 `<span>` 或 `<div>` 纯文本）

### 第 5 步：边界 — 点击链接不报错

- [ ] 点击 callout 内的 `[[recursion]]` 链接
- [ ] 浏览器 URL 变成 `/notes/recursion`
- [ ] 看到 404 页 "This page could not be found"（**预期失败** — Day 4 Story 10.4 才做 `/notes/[slug]` 完整路由）

### 第 6 步：边界 — 不带 wikilink 的 callout 仍正常

- [ ] 编辑区粘贴：`> [!common_pitfall]+ Watch out` 接换行 `> No links here, just text.`
- [ ] Preview 显示：红色背景 callout 框 + 纯文本（不破裂、不报错）

---

## 🚦 验收结果

**全部 ✅** → 说"Story 10.3 通过"，Claude mark `done`，启动 Story 10.4 Day 3-4 CanvasVaultAdapter（路径 B：vault → Spine JSON 注入，让 DeepTutor 把你 vault 当 Book 加载）。

**任何一步 ❌** → 在批注区写哪一步 + 实际现象，Claude 跑 `bmad-bmm-correct-course` 调整。

---

## 📝 你的批注区

> [!question]+ 你对 Story 10.3 的批注
>
> （空 — 等你跑完 UAT 后写）

### 已知偏离 / Phase B 延后说明

> [!info]+ Phase B 不在本验收单
> Story 10.3 spec 拆 Phase A（核心，本次完成）+ Phase B（VaultMonitor daemon 实时监听 vault 变化 + vault_mode 不上传 + 文件锁原子写入）。
> Phase B 是 **可选**升级（spec 标注 6-9h 工作量），用户可以在 Day 2 完整收官后或 Day 3 morning 再决定要不要做。
> 当前 Phase A 已能让 DeepTutor 直接读 vault md（容器内 `/vault` 直挂 worktree `canvas-vault/`），Phase B 升级的是"自动同步 + 写入安全"。

> [!info]+ DeepDiveBlock + FlashCardsBlock 的 HTML5 警告（不影响功能）
> 这两个 block 的 `[[wikilink]]` 渲染嵌在 `<button>` 里，浏览器 DevTools Console 可能看到 a-in-button 警告。**功能正常**，浏览器实际渲染兼容。后续 epic 可重构 button 为 div + role="button" 消除警告。

### 历史追溯（v1.0 首次 ship）

无（首次实施，无历史批注）。

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-10/10-3-day2-cleanup-vault-mount.md`
- **fork 端改动**（6 文件）：
  - `~/Desktop/canvas/deeptutor-fork/web/app/(workspace)/book/components/blocks/CalloutBlock.tsx`（接 MarkdownRenderer）
  - `.../blocks/TimelineBlock.tsx`（同）
  - `.../blocks/FlashCardsBlock.tsx`（同）
  - `.../blocks/DeepDiveBlock.tsx`（同）
  - `~/Desktop/canvas/deeptutor-fork/deeptutor/services/canvas/client.py`（path param 修复 + URL encode 保险）
  - `~/Desktop/canvas/deeptutor-fork/docker-compose.canvas.yml`（worktree 路径修正）
- **worktree 端改动**（1 文件）：
  - `docker-compose.yml`（加 `./canvas-vault:/vault:rw` 直挂 + `CANVAS_BASE_PATH=/vault` + `VAULT_PATH=/vault` + CORS 加 fork 端口）
- **AC → 实施对应**：
  - AC #1 (CalloutBlock + 3 兄弟) → 4 block tsx 文件 body/description/rationale/front-back 段
  - AC #2 (vault 挂载) → worktree docker-compose.yml volumes 段 + fork docker-compose.canvas.yml
  - AC #3 (path param) → client.py:63-78
  - AC #4 (compose 路径) → fork docker-compose.canvas.yml line 18, 32
- **后端验证证据**：
  - `POST :8011/api/v1/wikilink/build` → `{total_nodes: 31, total_edges: 27, build_time_ms: 196.5}`
  - `GET :8011/api/v1/wikilink/neighbors/原白板/CS 61B.md?hop=2` → `count: 1` + `节点/cs-61b-csm`
  - `GET :8011/api/v1/wikilink/neighbors/节点/Fundamentals.md?hop=2` → `count: 2` + `Eigenvalues + Characteristic-Equation`

---

## 下一步

→ Story 10.4 Day 3-4 CanvasVaultAdapter（vault → Spine JSON，绕过 DeepTutor AI 推断，让你的 wiki 结构 100% 保留作为 Book 的章节）
