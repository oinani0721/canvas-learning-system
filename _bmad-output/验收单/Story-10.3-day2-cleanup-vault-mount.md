---
story: "10.3"
title: "day2-cleanup-vault-mount"
status: "ready"
version: "v0.1-spec"
date: "2026-05-08"
developer: "Claude Code (claude-opus-4-7)"
commit: "TBD"
---

# Story 10.3 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Day 2 工作的用户验收清单。开发完成后状态会改为 review/done。

---

## 🎯 这个 Story 要做到什么

让 DeepTutor 直接读你已有的 vault md 文件夹（不用上传不用同步），并且 callout 里写的 `[[xxx]]` 也能渲染成蓝链。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 我 Obsidian 里的 callout 笔记（`> [!question]+ 这个 [[递归]] 重要`）在 DeepTutor 也能完整渲染（含双链），
**以便** 不用切换工具，DeepTutor 直接读真相源 md 文件。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. Obsidian 笔记写 callout 含 wikilink
       > [!question]+ 这个 [[递归]] 重要
       ↓
2. DeepTutor 打开同一笔记
       ↓
3. callout 内 "[[递归]]" 渲染为蓝色链接（不是 raw 文字）
       ↓
4. 点击链接 → 跳到递归笔记 ✅
       ↓
5. Canvas backend `:8011/api/v1/wikilink/build` 返回 total_nodes > 0
```

---

## ✅ 验收清单（5 步 UAT）

### 第 0 步：前置

- [ ] Story 10.2 已 done（wikilink 渲染基础通）
- [ ] Canvas vault 路径已知（`~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp/canvas-vault/`）
- [ ] vault 内有至少 3 个真实笔记（节点/X.md 文件）

### 第 1 步：CalloutBlock 修复

- [ ] 在 Obsidian 写新 callout 含 wikilink:
  ```
  > [!question]+ 这个 [[排序算法]] 重要
  ```
- [ ] 在 DeepTutor 打开同一笔记
- [ ] **看到 callout 内 `[[排序算法]]` 渲染为蓝色链接**（不是 raw 文字 `[[排序算法]]`）
- [ ] 同样测 `[!error]+`、`[!hint]+`、`[!tip]+` 4 种 callout 都渲染 wikilink

### 第 2 步：Vault 路径挂载

- [ ] 终端 `cd canvas-worktree && cat docker-compose.canvas.yml | grep canvas-vault`
- [ ] 验证路径指向当前 worktree（不是 feature-obsidian-hybrid-dev）
- [ ] `docker compose -f docker-compose.yml -f docker-compose.canvas.yml up -d`
- [ ] 双服务都 healthy

### 第 3 步：vault 数据扫描验证

- [ ] 在 vault 写 3 个真实笔记（如 `节点/recursion.md`、`节点/induction.md`、`节点/sorting.md`）
- [ ] 笔记之间含 wikilink: `recursion.md` 写 `[[induction]]`
- [ ] 终端 `curl -X POST http://localhost:8011/api/v1/wikilink/build`
- [ ] **返回 JSON 含 `total_nodes >= 3`**（不再是 0）

### 第 4 步：neighbors path param 修复

- [ ] `curl http://localhost:8011/api/v1/wikilink/neighbors/recursion.md?hop=2`
- [ ] 返回邻居列表 JSON（含 induction）
- [ ] **不返回 422 或 404**（旧 client 用 query param 会失败）

### 第 5 步：通过 fork 转发

- [ ] `curl http://localhost:8001/api/v1/wikilink/neighbors/recursion.md?hop=2`
- [ ] 通过 fork wikilink_proxy 转发后返回相同邻居列表
- [ ] DeepTutor UI 在 recursion 笔记页能看到 induction 邻居

---

## 🚦 验收结果

完成后填:
- ✅/❌ CalloutBlock 内 wikilink 渲染
- ✅/❌ vault 路径挂载正确
- ✅/❌ total_nodes > 0
- ✅/❌ neighbors path param 工作

---

## 📝 你的批注区

> [!question]+ 你对 Story 10.3 的批注
>
> 跑完后写实测发现。

---

## 🔗 技术 spec 参考

- **Story spec**: `_bmad-output/implementation-artifacts/epic-10/10-3-day2-cleanup-vault-mount.md`
- **风险红线**: R4 (obsidiantools vault 期望) + R7 (CalloutBlock)

---

## 下一步

→ Story 10.4 Day 3-4 CanvasVaultAdapter（路径 B 注入 vault → DeepTutor）
