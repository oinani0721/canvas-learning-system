---
story: "10.4"
title: "day3-4-canvas-vault-adapter"
status: "ready"
version: "v0.1-spec"
date: "2026-05-09"
---

# Story 10.4 验收单（给你看的版本）

## 🎯 这个 Story 要做到什么

把你 vault 笔记网络（含 wikilink 关系）直接"塞"进 DeepTutor 的 Book 数据结构，让 DeepTutor 像渲染自己生成的 book 一样渲染你的笔记——**不调 AI、不花 LLM 成本、保留 100% 用户结构**。

## 📖 用户故事（你的视角）

**作为** 学习者，**我想** 把 Obsidian vault 一键变成 DeepTutor 的 book，**以便** 不用手工把笔记一条条录入 DeepTutor，结构关系完整保留。

## 🖥️ 你会看到的交互（一步一步）

```
1. 终端跑 python -m adapter.vault_to_spine --vault canvas-vault --output spine.json
       ↓
2. 30 秒后看到 "[OK] Generated spine.json (N nodes, M edges, 0 LLM calls)"
       ↓
3. curl POST :8001/books/confirm-spine -d @spine.json
       ↓
4. 浏览器 :3782 → Books 列表 → 多一本 "我的 vault 笔记网络"
       ↓
5. 打开 → 看到 vault 节点作为 chapter ✅
```

## ✅ 验收清单（5 步 UAT）

### 第 0 步：前置

- [ ] Story 10.3 已 done（vault 已挂载，total_nodes > 0）
- [ ] Python 3.10+ 已装 + obsidiantools + networkx + pydantic

### 第 1 步：跑 adapter

- [ ] `cd ~/Desktop/canvas/deeptutor-fork`
- [ ] `pip install -r adapter/requirements-adapter.txt`
- [ ] `python -m adapter.vault_to_spine --vault ~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp/canvas-vault --output /tmp/spine.json`
- [ ] 看到 "[OK] Generated /tmp/spine.json"
- [ ] 检查 `cat /tmp/spine.json | jq '.chapters | length'` 显示 N（节点数）

### 第 2 步：注入 fork

- [ ] `curl -X POST http://localhost:8001/books/confirm-spine -H 'Content-Type: application/json' -d @/tmp/spine.json`
- [ ] 返回 200 + book_id
- [ ] 不触发 IdeationAgent（看 docker logs 不调 OpenAI）

### 第 3 步：UI 验证

- [ ] 浏览器 :3782 → Books
- [ ] **多一本 book**（标题与 vault 名字相关）
- [ ] 打开 → ConceptGraphBlock 渲染（Mermaid 静态图，Day 5 升级 ReactFlow）
- [ ] 章节数 ≈ vault 笔记数

### 第 4 步：结构保留验证

- [ ] 在 vault 写 `recursion.md` 含 `[[induction]]`
- [ ] 重跑 adapter → 注入新 spine
- [ ] book 内确认 recursion 章节有指向 induction 的边

### 第 5 步：LLM 成本验证

- [ ] `docker logs deeptutor 2>&1 | grep -i "openai\|anthropic" | head`
- [ ] **0 条 OpenAI/Anthropic 调用**（Day 3-4 期间）
- [ ] LLM cost = $0

## 🚦 验收结果

完成后填: ✅/❌ adapter 跑通 + JSON 注入 + 0 LLM cost + 结构保留

## 📝 你的批注区

> [!question]+ 你对 Story 10.4 的批注

## 🔗 技术 spec

`_bmad-output/implementation-artifacts/epic-10/10-4-day3-4-canvas-vault-adapter.md`

## 下一步

→ Story 10.5 Day 5-6 Whiteboard 路由 + ReactFlow（让注入的 vault 图可交互）
