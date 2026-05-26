---
title: "BMAD spec 体系级审查任务书 — 给 ChatGPT Deep Research"
date: 2026-05-26
plan_id: EPIC1-BMAD-DEV-ASSESS-2026-04-17
audience: ChatGPT Deep Research (o1-pro / Claude Opus 4.7 / Gemini 2.5 Pro DR)
xml_bundle: .gdr/research-pack-bmad-system-audit.xml (待 research-pack v3 生成)
verdict_target: "76 spec × 10 epic 体系健康度判定 + Sprint 2 v3 5 session 并行可行性验证 + 旧 64 ready-for-dev 砍清单"
---

# BMAD spec 体系级审查任务书

## 0. 一句话任务

**审 Canvas Learning System 整个 BMAD spec 体系 (76 spec × 10 epic) 的健康度**, 暴露死 spec / 隐藏冲突 / 多 session 并行风险, 给出**真正可执行的体系重构方案**.

## 1. 体系背景 (实证全图)

- **76 个 spec across 10 epic** (epic-1 ~ epic-10-lite + 新建 epic-5-graphiti-era)
- **状态分布**: 64 ready-for-dev / 6 review / 3 done / 2 superseded / 1 in-progress
- **真相**: 64 个 ready-for-dev 不是"准备好开发", 是"沉淀未清理". sprint-status.yaml sprint_v3 段只列 ~26 entry, 剩 38 spec 是无 sprint 归属的孤儿
- **Sprint 2 v3 真正 active**: 11 个 spec = ChatGPT 5 必修 (epic-5-graphiti-era/ 5-ge-1~5) + UX 修复 2 + LITE-4-3/5-6/5-7 部分 supersede + 4 MVP 收尾

## 2. 用户原话锚点

- 2026-05-26: "我选 Graphiti 看重时序图谱 + 记忆批注 + 记忆节点关系"
- 2026-05-26 line 47: "Edge 对话目前已经实现, 双链连节点时填关系" (ai-linked-doc.ts:14-50 已确认实现)
- 2026-05-26 line 146: "MVP 还有 3 项: 检验白板设置 + Graphiti 记忆系统 (最重要架构) + 个人笔记返回系统"
- 2026-05-26 体系疑问: "我们到底按什么 spec 开发? 旧 epic/story 哪些有用? 多 session 并行怎么干?"

## 3. 6 个体系审查议题

### 议题 1: 76 spec 健康度全图判定

- 64 ready-for-dev 中真该砍多少? (用户期望 ~50%)
- 哪些标 ready 但代码实际已实施? (G-FAKE-001 历史教训 — 名实分离)
- 哪些是 Tauri 时代残留, Obsidian Hybrid 下无法复活?

### 议题 2: 新 epic-5-graphiti-era/ 5 spec 是否真覆盖 ChatGPT 5 必修?

- 5-ge-1 (CanvasGraphEpisodeV1 + edge_type_map) 是否真覆盖必修 #1 + #2?
- 5-ge-2 (belief_key 版本链 + add_triplet) 是否真覆盖必修 #3?
- 5-ge-3/4/5 同上
- 跟旧 epic-5/ (BKT/FSRS/scoring/calibration) 接口契约是否清晰?

### 议题 3: Sprint 2 v3 5 session 并行可行性

按 mapping (Session A/B/C/D/E), 41h 工时, 真并行还是隐藏依赖?
- A 改 plugin + Obsidian vault 文档 (不影响 backend)
- B 改 backend episode_worker + graphiti/* (核心 service)
- C 改 graphiti_belief_service + graphiti_write_facade + relationship_sync_service (3 个 service 顺序)
- D 改 graphiti_relation_service + context_enrichment_service (依赖 B done)
- E 改 plugin callout-sync / wikilink-sync (跟 A 同 plugin 目录, 但不同文件)

**重点审**:
- B 改 episode_worker.py 时, C 也改 graphiti/* 是否冲突?
- E 与 A 在 frontend/obsidian-plugin/src/ 同目录, 真不冲突?
- D 等 B done 是 Sprint 2 末才能起步, 是否拖延整体 timeline?

### 议题 4: 旧 64 ready-for-dev spec 砍清单

按 Obsidian Hybrid 适用度 + Tauri 残留判定, 推荐砍多少? 哪几个?
- Epic 3 节点对话 (Cmd+Shift+C, 6 spec) 是否还有效?
- Epic 5 旧 5-1~5-8 (BKT/FSRS, 8 spec) 是否被 epic-5-graphiti-era 替代?
- Epic 7 复习任务 (4 spec) 推 Sprint 4+?
- Epic 8 Dashboard plugin stack (8 spec) 是否大部分砍?
- Epic 9 图片考察 (2 spec) 推 Sprint 5+?

### 议题 5: Sprint 3+ 优先级 (Sprint 2 v3 ship 后)

Sprint 2 v3 完成 ChatGPT 5 必修 + UX + Edge 接通后, Sprint 3 该做什么? 具体 spec ID:
- 旧 epic-5 BKT/FSRS 激活 (5-1, 5-2, 5-3)?
- Epic 6 Edge 讨论 EI+SE (用户 line 47 说已部分实现, 接通 backend)?
- search_communities + 错误模式 Dashboard?
- V-12 TIP_RECENCY_CORRUPTION + V-13 MEMORY_TOO_LATE 修复?

### 议题 6: 多 session 协同硬规则 (避免 G-FAKE / G-PIPE 历史)

历史教训:
- G-FAKE-001: 42+ 假命名 (graphiti 名实际 Neo4j)
- G-PIPE-006: 桥接有了但没形成单一主干

多 session 并行如何避免:
- 命名约定 (Graphiti edge vs Neo4j edge 谁是真相源)
- import contract (5-ge-5 facade 是唯一 read path)
- 共享 belief_key 跨层

## 4. 期望 7 Part 输出

### Part 1: 76 spec × 4 状态分布判定 (必)

| Status | 真 done | 真 active | 推迟 Sprint 3+ | 砍 | 总 |
|---|---:|---:|---:|---:|---:|
| (按 epic 分布) | | | | | |

**整体 BMAD spec 体系健康度: X / 10**

### Part 2: Sprint 2 v3 11 active spec 验证 (必)

- 5 session 并行真不冲突? 给 import dependency 图
- 5 必修 spec 是否真覆盖 ChatGPT 7 Part Graphiti 推荐?
- 7 MVP (4 原 + 用户 line 146 加 3) 是否被 Sprint 2 v3 覆盖?

### Part 3: 旧 64 ready-for-dev 砍清单 (必)

按 epic 给具体 spec ID + 砍 / 推 Sprint 3+ / 保留 + 理由.

### Part 4: 推荐重构后的 BMAD spec 体系

- 是否需要 archive 子目录给砍掉的 spec?
- epic-5-graphiti-era 命名是否合理?
- 是否需要 epic-6-edge-revival (用户 line 47 已实现, Sprint 3 接通)?

### Part 5: 多 session 并行验证 (必)

按 §3 议题 3 给的 5 session mapping:
- 真冲突? 假冲突?
- D 等 B done 的依赖如何减少 wall time?
- 推荐并行波次序列 (波 1 / 波 2)

### Part 6: Sprint 3 具体优先级 (必)

按议题 5, 列 Sprint 3 必修 6-8 个 spec ID + 工时.

### Part 7: 一句话体系判定

"**当前 BMAD spec 体系健康度 X/10, 推荐 Sprint 2 v3 立刻起步 [...], Sprint 3 必修 [...], 砍掉 [N] 个旧 spec.**"

## 5. 严格要求

- **必给具体 spec ID + epic 编号** (不能 "Epic 8 大部分砍" 这种泛泛)
- **必给 import dependency 图** 验证 5 session 真不冲突
- **必引用 file:line 证据** 在 spec 中
- **重点**: 体系级真相 + 多 session 协同硬规则 + Sprint 3 优先级

## 6. ChatGPT 起手 prompt

```
请对我上传的 research-pack-bmad-system-audit.xml 做 Deep Research.

议题: Canvas Learning System BMAD spec 体系级审查 (76 spec × 10 epic).

用户原话锚点:
- "我们到底按什么 spec 开发? 旧 epic/story 哪些有用?"
- "多 session 并行开发, 怎么不冲突?"
- "我选 Graphiti 看重时序图谱 + 记忆批注 + 记忆节点关系"

XML 末尾 <instruction> 段是完整任务书. 必读.

6 核心议题:
1. 76 spec 健康度全图 (死/活/重复/冲突)
2. epic-5-graphiti-era 5 spec 是否覆盖 ChatGPT 5 必修
3. Sprint 2 v3 5 session 并行可行性 (import dependency)
4. 旧 64 ready-for-dev 砍清单
5. Sprint 3+ 优先级
6. 多 session 协同硬规则

请按任务书 §4 输出 7 Part, 必给具体 spec ID + file:line.

不要 "体系大致 OK, 仅需小幅调整" 这种废话.
```
