# epic-5-graphiti-era — Graphiti 时序图谱真用 (ChatGPT 5 必修包)

> **2026-05-26 新建** — 用户 Q4 决策: 新建子 epic 隔离 ChatGPT 5 必修方案与旧 epic-5/ BKT/FSRS 体系.
>
> **缘起**: ChatGPT Deep Research (2026-05-26) 审计 Graphiti 设计成熟度 = 3.5/10. 当前 add_episode 真接通但 valid_at/invalid_at + search_facts + search_communities + relationship_sync_service 全 0% 利用. 用户原话锚定 "我选 Graphiti 看重时序图谱 + 记忆批注 + 记忆节点关系" 完全未被实现.

## 子 Epic 与旧 epic-5/ 的关系

| 维度 | 旧 epic-5/ | epic-5-graphiti-era/ (本目录) |
|---|---|---|
| **主题** | BKT/FSRS/scoring/calibration 算法层 | Graphiti 时序图谱真用 (写入 + 查询 + 时序追踪) |
| **创建时间** | Sprint 1 (~2026-04 初) | Sprint 2 (2026-05-26) |
| **状态** | 旧 5-1~5-8 大部分 ready-for-dev 但未实施; LITE-5-6/5-7 是 Sprint v3 简化版 | 5 个新 spec, ChatGPT 5 必修包整合 |
| **是否并存?** | ✅ 并存 — 旧 epic-5/ 算法层在 Sprint 3+ 激活, 不被本子 epic 替代 | 本子 epic 提供 Graphiti 基础设施, 旧 epic-5/ 算法层将基于此运行 |
| **依赖** | LITE-5-6/5-7 部分依赖本子 epic 的 CanvasGraphEpisodeV1 schema | 独立于旧 epic-5/, 不依赖 BKT/FSRS |

## 5 个 Story 速览

| Story ID | 主题 | ChatGPT 必修编号 | 工时 | Session |
|---|---|:---:|---:|:---:|
| **5-ge-1** canvas-graph-episode-v1.md | 统一事件 schema + edge_type_map 透传 | #1 + #2 | 16h | B |
| **5-ge-2** belief-key-version-chain.md | belief_key 版本链 + add_triplet API + valid_at/invalid_at | #3 | 9h | C |
| **5-ge-3** query-time-flush.md | Hot/Warm/Cold 三层时延 + flush helper | #4 (前) | 4h | C |
| **5-ge-4** relationship-sync-production.md | dry_run=False + DEFAULT_GROUP_ID 移除 | #4 (后) + 议题 6 | 2h | C |
| **5-ge-5** graphiti-relation-service-facade.md | search_relation_facts + search_error_communities facade | #5 | 3h | D |
| **总** | | | **34h** | |

## 5 session 并行 mapping

- **Session A** — UX 修复 + 收尾 (不动本子 epic)
- **Session B** — **5-ge-1** (16h, 阻塞 D)
- **Session C** — **5-ge-2 + 5-ge-3 + 5-ge-4** (15h, 顺序干)
- **Session D** — **5-ge-5** (3h, 等 B done)
- **Session E** — Plugin 端事件采集 (不动本子 epic, 但事件 schema 由 B 定义)

## 与旧 spec 的 supersede / merge 关系

| 旧 spec | 状态变更 | 新归属 |
|---|---|---|
| `epic-1/1-16-callout-graphiti-hook.md` | superseded by 5-ge-1 + 5-ge-2 | callout 是 5-ge-1 一个 event_type |
| `epic-2/2-10-wikilink-graphiti-sync.md` | superseded by 5-ge-1 + 5-ge-3 + 5-ge-4 | wikilink 是 5-ge-1 一个 event_type, sweep 由 5-ge-3 改造 |
| `epic-4/LITE-4-3.md` | partial superseded by 5-ge-5 (路线 4 改调 facade) | LITE-4-3 仍保留出题策略, 但 Graphiti 调用走 facade |
| `epic-5/LITE-5-6.md` | partial superseded by 5-ge-1 (calibration event 走 unified schema) | LITE-5-6 仍保留 dual-write 逻辑, 但 Graphiti 写入走 5-ge-1 |
| `epic-5/LITE-5-7.md` | partial superseded by 5-ge-5 (路线 B 改调 facade) | LITE-5-7 仍保留 2 系统接通, 但 Graphiti 调用走 facade |

## ChatGPT 体系审查待回答

ChatGPT Deep Research (体系审查包, 2026-05-26 launching) 应回答:
- 本子 epic 5 spec 是否真覆盖 ChatGPT 5 必修?
- 与旧 epic-5/ BKT/FSRS 接口契约是否清晰?
- 5 session 并行依赖图是否有隐藏 race?

## 决策追溯

- 2026-05-26 (ChatGPT Graphiti deep research 报告): https://help.getzep.com/graphiti + GitHub examples 实证
- 2026-05-26 (用户 Q4 决策): 新建 epic-5-graphiti-era 子 epic
- 2026-05-26 (用户 Q1 决策): ChatGPT 体系级审查 76 spec + 12 backend + 10 plugin + 4 audit 报告

## 引用

- ChatGPT 原文: `_bmad-output/审查/2026-05-26-chatgpt-graphiti-deep-research-报告.md`
- 决策清单: `_bmad-output/审查/2026-05-26-graphiti-sprint-2-决策清单.md`
- 体系全图诊断: `_bmad-output/审查/2026-05-26-bmad-spec-体系全图诊断.md`
