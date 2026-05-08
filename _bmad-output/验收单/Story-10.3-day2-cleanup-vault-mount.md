---
story: "10.3"
title: "day2-cleanup-vault-mount"
status: "review"
version: "v2.0-double-section"
date: "2026-05-07"
revised: "2026-05-07"
developer: "Claude Code (claude-opus-4-7)"
phase: "Phase A only (Phase B optional, deferred)"
commit_fork: "deeptutor-fork@4a17cad"
commit_worktree: "2fe058d"
revision_reason: "5-agent UAT methodology deep explore 收敛后改造为双段结构（DoD-3 D3-A~D3-E）"
---

# Story 10.3 验收单（v2.0 双段重写）

> [!info]+ 这是什么
> Day 2 Phase A：让 DeepTutor 直接读你 Canvas vault 里的 md 文件（不上传不复制），并且 callout 框里写的 `[[xxx]]` 双链能渲染成蓝色链接。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-10/10-3-day2-cleanup-vault-mount.md`。

---

## 🎯 这个 Story 要做到什么

让 DeepTutor 直接读你 vault 里的 md 文件（vault 里 31 个文件全扫描），并且你写的 callout 框里的 `[[xxx]]` 双链能渲染成蓝色链接。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 在 vault 里写的笔记（含 callout `> [!question]+ 看 [[递归]]` 这种），DeepTutor 打开同一篇也能识别双链 + 直接读到我的 md 文件，
**以便** 不用上传不用复制，本地写完 DeepTutor 实时看见，知识库 100% 我自己的。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 我在 Co-Writer 写一段 callout 含 [[recursion]]
       ↓
2. 右侧预览区出现黄色 callout 框
       ↓
3. callout 框内的 [[recursion]] 是橘红色链接（不是纯文本）
       ↓
4. 点击 [[recursion]] → 跳到 404（预期，Day 4 Story 10.4 才填路由）
       ↓
5. 没写 wikilink 的 callout 也正常渲染（不破裂、不报错）
```

---

## 🤖 Claude 已代验（你不用跑）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> 出现 `vault mount` / `volume` / `path param` / `curl` 等是 Claude 该处理的。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | vault 直挂到容器 `/vault`（worktree docker-compose volumes） | ✅ `./canvas-vault:/vault:rw` 落地 |
| 2 | Canvas backend 扫描 vault 全部 31 个 md 文件（节点/原白板/根目录） | ✅ POST `:8011/api/v1/wikilink/build` 返回 `total_nodes:31, total_edges:27, build_time_ms:196.5` |
| 3 | 跨目录双链识别（`原白板/CS 61B.md` ↔ `节点/cs-61b-csm.md`） | ✅ GET `/wikilink/neighbors/原白板/CS%2061B.md?hop=2` → count:1 + 邻居命中 |
| 4 | `节点/Fundamentals.md` 多跳邻居正确（2 个邻居：Eigenvalues + Characteristic-Equation） | ✅ count:2 |
| 5 | CalloutBlock 修复（1 行改：`<div>{body}</div>` → `<MarkdownRenderer content={body} />`） | ✅ callout 内 wikilink 蓝链 |
| 6 | TimelineBlock + FlashCardsBlock + DeepDiveBlock 同步修复 | ✅ 4 个 block 全 wikilink-aware |
| 7 | client.py path param 修复（`{note_path:path}` 而非 query string） | ✅ 中文路径 URL encode 正确 |
| 8 | docker-compose.canvas.yml 路径参数化（不再硬编码旧 worktree 路径） | ✅ 用 `${CANVAS_WORKTREE_PATH}` |
| 9 | CORS_ORIGINS 加 fork 端口（:3782 :8001 :5173）触发跨域允许 | ✅ |
| 10 | callout 内 wikilink HTML 含 `<a class="wikilink" data-wikilink="true">` | ✅ DevTools Elements 验证通过 |

---

## 👤 你来验（产品体验 — 3 步，3 分钟）

> [!warning]+ 这段你只在浏览器里点击、看屏幕。

### 第 0 步：进入 Co-Writer

- [ ] 我浏览器打开 `http://localhost:3782`
- [ ] 我点击左侧菜单 **Co-Writer**，看到左右两栏（左边写、右边预览）
- [ ] 我**感觉**界面打开速度可以接受（不卡顿）

### 第 1 步：写 callout 看 callout 框 + 框内蓝链

- [ ] 我在左边输入框粘贴这段：
  ```
  > [!key_idea]+ Important Concept
  > To understand recursion, see [[base-case]] and [[recursion]].
  ```
- [ ] 我看到右侧预览区出现一个**黄色背景的 callout 框**（不是纯文本）
- [ ] 框内的 **`[[base-case]]` 和 `[[recursion]]` 是橘红色链接**（不是黑色纯文本灰色）
- [ ] 我**感觉**渲染**流畅**（不需要刷新就立即出现）

### 第 2 步：点击链接看跳转（预期 404）+ 边界

- [ ] 我点击 callout 内的 `[[recursion]]`
- [ ] 浏览器跳到 404 页面（"This page could not be found"）
- [ ] 我**理解**这是预期失败（Story 10.4 才填这个路由）— 不是 bug
- [ ] 我回退浏览器，再粘贴一段**没有 wikilink 的 callout**：
  ```
  > [!common_pitfall]+ Watch out
  > No links here, just text.
  ```
- [ ] 我看到红色背景 callout 框 + 纯文本（**不破裂、不报错、不闪退**）
- [ ] 我**感觉**这个产品**稳定**（边界场景也能优雅处理）

### 主观打分（Felt-sense）

- [ ] **流畅度**（1=卡顿 / 5=如丝般顺滑）：___
- [ ] **稳定性**（1=容易崩 / 5=很稳）：___
- [ ] **明天我会再打开它写带 callout 的笔记的可能性**（0-10）：___

---

## 🚦 验收结果

**全部 ✅** → 说"Story 10.3 通过"，Claude mark `done`，启动 Story 10.4 Day 3-4 CanvasVaultAdapter（路径 B：vault → Spine JSON 注入）。

**任何一步 ❌** → 在批注区写哪一步 + 实际现象，Claude 跑 `bmad-bmm-correct-course` 调整。

---

## 📝 你的批注区

> [!info]+ v1.0 → v2.0 修复记录（2026-05-07 双段重写）
> **原批注**：用户 2026-05-07 反馈"UAT 只验产品体验，技术验证 Claude 代验"
> **根因**：v1.0 让用户跑 curl + 开 DevTools 看 HTML — 45% 步骤是技术任务
> **已修复**：vault 扫描验证 + 跨目录双链 + DevTools HTML 检查 全部移到 🤖 Claude 已代验段；用户段只剩"打开 Co-Writer + 写 callout + 看蓝链 + 边界（无 wikilink callout 也正常）"

> [!info]+ Phase B 不在本验收单
> Story 10.3 spec 拆 Phase A（核心，本次完成）+ Phase B（VaultMonitor daemon 实时监听 + vault_mode 不上传 + 文件锁原子写入）。
> Phase B 是**可选**升级（spec 标注 6-9h），用户可在 Day 2 完整收官后或 Day 3 morning 再决定。
> 当前 Phase A 已能让 DeepTutor 直接读 vault md，Phase B 升级的是"自动同步 + 写入安全"。

> [!info]+ DeepDiveBlock + FlashCardsBlock 的 HTML5 警告（不影响功能）
> 这两个 block 的 wikilink 渲染嵌在 button 元素里，浏览器 console 可能看到 a-in-button 警告。**功能正常**，浏览器实际渲染兼容。后续 epic 可重构。

> [!question]+ 你对 Story 10.3 的批注
>
> （等你跑完 UAT 后写）

### 历史追溯（v2.0 首次双段重写）

无（首次重写，无更早历史批注）。

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-10/10-3-day2-cleanup-vault-mount.md`
- **fork 端改动**（6 文件）：
  - CalloutBlock.tsx / TimelineBlock.tsx / FlashCardsBlock.tsx / DeepDiveBlock.tsx — 接 MarkdownRenderer
  - `deeptutor/services/canvas/client.py` — path param 修复 + URL encode
  - `docker-compose.canvas.yml` — 路径参数化
- **worktree 端改动**（1 文件）：
  - `docker-compose.yml` — 加 vault 直挂 + 路径变量 + CORS 加 fork 端口
- **AC → 实施对应**：
  - AC #1 (CalloutBlock + 3 兄弟) → 4 block tsx 文件
  - AC #2 (vault 挂载) → 双 docker-compose volumes 段
  - AC #3 (path param) → client.py:63-78
  - AC #4 (compose 路径) → docker-compose.canvas.yml line 18, 32
- **commit**: worktree `2fe058d` + fork `4a17cad`

---

## 下一步

→ Story 10.4 Day 3-4 CanvasVaultAdapter（vault → Spine JSON，路径 B 绕过 AI 推断，让 vault 结构 100% 保留作为 Book 章节）
