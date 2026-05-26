---
title: "Graphiti 时序图谱设计审计 — 给 ChatGPT Deep Research 的对抗审查任务书"
date: 2026-05-26
plan_id: EPIC1-BMAD-DEV-ASSESS-2026-04-17
audience: ChatGPT Deep Research (o1-pro / Claude Opus 4.7 / Gemini 2.5 Pro Deep Research)
target_repo: https://github.com/oinani0721/canvas-learning-system (origin, 已 push commit 16b648d)
xml_bundle: .gdr/research-pack-graphiti-design-audit.xml (research-pack skill 生成)
user_intent_anchor: 用户 2026-05-26 原话 "我选择 Graphiti, 是看重了它的时序图谱, 所以我觉得它记忆我的批注, 以及记忆我节点和节点之间的关系有优势"
---

# Graphiti 时序图谱设计审计 — 给 ChatGPT Deep Research 的对抗审查任务书

## 0. 一句话任务

**审查 Canvas Learning System 的 Graphiti 时序知识图谱设计**, 找出 "用户期望 vs 实际利用率" 的设计层落差, 给出**真正有用的设计完善建议** (不是工程细节, 是产品 + 学习科学层面的架构裁决).

## 1. 用户期望 (锚定原话, 不可妥协)

### 用户 2026-05-26 原话
> "我选择 **Graphiti**, 是看重了它的**时序图谱**, 所以我觉得它记忆我的**批注**, 以及记忆我**节点和节点之间的关系**有优势."

### 用户 2026-05-13 核心闭环原话
> "**批注是核心**, 我需要用我的**个人记忆系统**充分理解我使用原白板的**学习过程**."

### 翻译 (产品层):
- **时序图谱**: 用户希望 Graphiti 不只是"现在知识快照", 而是"知识如何演化" — 我以前认为 X, 后来改成 Y, Graphiti 应能回放
- **批注记忆**: callout (tip/error/question/hint) 4 类应该被 Graphiti 当作 episode 记下, 未来出题时能用上"我以前说过 X"
- **节点关系记忆**: ai-linked-doc 时用户选的 7 类关系 (prerequisite / depends_on / refines / extends / example_of / contradicts / related_to) + 自由描述, 应该被 Graphiti 当作 edge 记下, 未来能查 "X 和 Y 的关系是什么"

## 2. Graphiti 5 大核心能力 vs Canvas 实际使用 (实证全图)

| Graphiti API | 设计能力 | 用户期望对应 | Canvas 实际使用 | 利用率 |
|---|---|---|---|---:|
| `add_episode` | 时序化事件记录 | 批注 + 关系变更 | ✅ `episode_worker.py:562` + `review_service.py:1423` + `memory_service.py:462` | **40%** (只写 callout/edge, 没写 wikilink) |
| `valid_at / invalid_at` | **时序追踪 (知识演化)** | 用户最在乎 "我以前认为 X, 现在改成 Y" | ⛔ **0 处真用** (episode_worker:52 仅有 `reference_time` 创建时间字段, 没 invalidation) | **0%** |
| `search_facts` | 关系查询 "X 和 Y 的关系" | 用户期望出题时引用历史关系 | ⛔ **0 处调用** (LITE-5-7 路线 B / LITE-4-3 路线 4 准备用, 但代码层 0%) | **0%** |
| `search_communities` | **错误模式聚类** | 用户期望 "我反复在哪类问题上犯错" | ⛔ **0 处调用** (社区聚类完全没用) | **0%** |
| `search_nodes` | 节点检索 | 节点级语义查询 | ✅ 2 处 (memory_service) | **30%** |

### Graphiti 写入路径已建 vs 实际接通

| 来源 | spec/code | 实际写入 Graphiti? |
|---|---|---|
| **Callout (tip/error/question/hint)** | STORY-1-16-callout-graphiti-hook (新 spec, V-07 修复) | ⛔ **0%** (spec ready-for-dev, 代码未实施) |
| **Wikilink 变更** | STORY-2-10-wikilink-graphiti-sync (新 spec) | ⛔ **0%** (spec ready-for-dev, 代码未实施) |
| **节点关系 (ai-linked-doc 7 类)** | `relationship_sync_service.py` (Round-23 Story 8.4) | ⚠️ **dry_run=True 默认** (line 193) — **已建但不真写** |
| **Calibration 投票** | LITE-5-6 V-11 修复后 dual-write | ⛔ **0%** (spec ready-for-dev, 代码未实施) |
| **检验白板答题** | review_service.py:1423 `add_episode_for_edge` | ✅ **100%** (G-PIPE-006 已修, Verification → Retrieval 闭环) |

## 3. 4 大设计层缺口 (希望 ChatGPT 给意见)

### 缺口 #1 时序图谱 0% 利用 (用户最在乎的能力完全没真用)

**现状**:
- `episode_worker.py:52` 有 `reference_time: datetime` 字段
- `episode_worker.py:78` 序列化 ISO 字符串
- **但没用 `valid_at` (知识起始有效时间) + `invalid_at` (知识失效时间)** — Graphiti 的核心时序追踪

**用户场景**:
- 2026-05-01: 用户写 callout "BST 平衡性是 O(log n) 平均"
- 2026-05-20: 用户改 callout "BST 最坏情况是 O(n), 必须用 AVL/红黑树才保证 O(log n)" — 这是**知识演化**
- Graphiti 应能: `search_facts("BST 平衡性", as_of="2026-05-10")` 返回旧观点; `as_of="2026-05-25"` 返回新观点

**问题**:
- 当前设计 (1-16-hook AC#5) 说 "用 valid_at / invalid_at 表达版本演化", 但 episode_worker 代码完全没处理这两个字段
- spec 跟代码脱节, dev 接手时**不知道如何实现 valid_at**

**希望 ChatGPT 回答**:
1. Graphiti `valid_at` / `invalid_at` 的正确 API 用法 (查 Zep 官方文档)
2. 如何在 Canvas 这种"用户每天编辑 vault"的场景下, 让 Graphiti **自动判定** 旧 episode 何时 invalid (而不是 dev 手动 mark)
3. UI 层如何让用户感知"时序回放" — Dataview Plot? 时间轴 callout?

### 缺口 #2 search_facts / search_communities 0 调用 (Graphiti 当前 "只写不读")

**现状**:
- add_episode 路径有 3 个 (callout / edge / memory), 但 **search_facts 0 处调用**
- search_communities 0 处调用 — 用户期望的 "我反复在哪类问题上犯错" 完全没实现

**用户场景**:
- 检验白板时, 系统应该自动调 `search_facts("recursion 边界条件", group_id="vault:cs61b")` 返回"用户上次说过 X 错"
- Dashboard 应该自动调 `search_communities()` 返回 "你最近 1 个月 3 个错误集中在: 递归基线 / BST 平衡 / 动态规划状态转移"

**问题**:
- LITE-4-3 路线 4 + LITE-5-7 路线 B 都准备用 search_facts, 但仅 spec, 0 代码
- search_communities 在任何 spec 都没提到 — **完全没人计划用**

**希望 ChatGPT 回答**:
1. search_communities 的 input/output 实际是什么 (查 Zep 文档 + GitHub examples)
2. 在 Canvas 错误分析场景, search_communities 的 query 应该怎么构造?
3. 是否需要专门的 community detection 配置 (algorithm: leiden? louvain?)
4. search_facts vs search_nodes 在 "X 和 Y 的关系" 查询上谁更合适?

### 缺口 #3 节点关系同步 dry-run (用户最在乎的 7 类关系完全没真写 Graphiti)

**现状**:
- `frontend/obsidian-plugin/src/ai-linked-doc.ts` 完整实现 7 类关系选择 + Modal 描述
- `backend/app/services/relationship_sync_service.py` 有 sync function, 但 `dry_run=True` 默认
- 没有任何 cron / 触发点真实把 frontmatter `relationships[]` 同步到 Graphiti edges

**用户场景**:
- 用户 Cmd+Shift+D 派生节点 → Modal 选 "prerequisite" → Modal 填 "学 BST 前必须懂二叉树遍历" → 写入新节点 frontmatter
- **预期**: Graphiti 应有 edge `[[new_node]] --prerequisite--> [[binary_tree_traversal]]`, 含 description
- **实际**: frontmatter 写了, Graphiti 0 edge (因为 sync 是 dry-run)

**希望 ChatGPT 回答**:
1. 时机决策: relationship sync 应该实时 (frontmatter 改 → 立刻 sync) 还是 batch (cron hourly)? 用户写 1 条关系马上想被 search_facts 查到, 但 cron 是 1h 延迟
2. 7 类关系 (prerequisite / depends_on / refines / extends / example_of / contradicts / related_to) 在 Graphiti edge 模型中**最佳表达方式**:
   - 用 edge name 区分 (edge_name="prerequisite")?
   - 用 edge property 区分 (edge.relation_type="prerequisite")?
   - 用不同 entity_type 区分?
3. 用户填的自由描述 (Modal 2 "学 BST 前必须懂二叉树遍历") 如何在 Graphiti 中可被 search_facts 模糊查询?
4. 双向 vs 单向: prerequisite (A 是 B 的先修) 应该写 1 个 edge 还是 2 个 edge (A→B + B←A)?

### 缺口 #4 1h sweep 延迟 vs 用户期望的"即时"

**现状**:
- STORY-2-10 设计 hourly cron sweep (wikilink_events → batch add_episode)
- STORY-1-16-hook 复用同 sweep cron (callout_events 并列)
- LITE-5-6 V-11 修复 calibration_events 也走同 sweep
- **用户写 callout/关系 → 1-60 分钟后才入 Graphiti → 立刻 search_facts 查不到**

**用户场景**:
- 用户写 callout "二分查找的边界条件容易错"
- 用户**立刻** Cmd+Shift+Q 触发 quick exam
- **预期**: 题目应反映"二分查找边界条件" tip
- **实际**: callout 还在 events_queue, 没入 Graphiti, search_facts 查不到, 题目只用 LanceDB tips

**希望 ChatGPT 回答**:
1. 1h sweep 是否合理? 业界 (Zep / mem0) 实践是 batch 还是即时?
2. 折中方案: 用户主动触发 quick exam 时, 是否应**先 flush pending events** 再调 search_facts?
3. query-time flush 的实现风险: race condition? 性能? 

## 4. 6 个对抗审查议题 (希望 ChatGPT 给具体设计方案)

### 议题 1: Graphiti 时序图谱的"演化追踪"机制设计

**问题**: Canvas 当前 episode_worker 只记 `reference_time` (创建时间), 没记 `valid_at`/`invalid_at`. 用户期望"知识演化"(我以前认为 X, 现在改成 Y) 完全没实现.

**希望输出**: 具体 episode_body schema + valid_at/invalid_at 写入策略 + UI 时序回放 mockup.

### 议题 2: 节点关系 (7 类 + 自由描述) → Graphiti edge 的最佳建模

**问题**: ai-linked-doc relationships 7 类 + description 已写 frontmatter, 但 relationship_sync_service dry-run, 0 edge. 怎么建模才能让 search_facts("X 和 Y 的关系") 真返回 description?

**希望输出**: edge_name / edge.property / entity_type 三选一推荐 + 完整 schema + dry-run → production 迁移路径.

### 议题 3: 错误模式聚类 search_communities 的产品落地

**问题**: search_communities 0 调用. 用户期望 "Dashboard 显示我最近 1 个月反复在哪类问题上犯错" 完全没设计.

**希望输出**: search_communities query 构造 + 输出渲染 mockup (Dataview / mermaid?) + community detection algorithm 选型.

### 议题 4: 1h sweep 延迟 vs 即时查询的折中

**问题**: 用户写完 callout 立刻想被考察到, 但 sweep 是 1-60 min 延迟. query-time flush 设计有 race condition.

**希望输出**: 3 个备选方案 (即时双写 / query-time flush / 5-min mini-sweep) 各自利弊 + 推荐.

### 议题 5: Graphiti 与 Neo4j edge 的设计协调 (历史 G-FAKE-001 教训)

**问题**: 历史上 42+ 函数名含 "graphiti" 但实际写 Neo4j (G-FAKE-001 已修). 现在 relationship_sync_service 准备真写 Graphiti edge — 是否会跟现有 Neo4j edge 冲突? 双写? 单写?

**希望输出**: Graphiti edge ↔ Neo4j edge 设计契约 + 谁是真相源 + 同步策略.

### 议题 6: Graphiti group_id 隔离机制是否真生效

**问题**: Story 2.5.Y 锁定 group_id 规约 `vault:<vault_id>`, 但 episode_worker / memory_service 是否所有 add_episode / search 都真用了 build_vault_group_id? 跨 vault 泄漏风险?

**希望输出**: group_id 隔离审计清单 + 缺口修复.

## 5. 7 个具体输出格式要求

请用中文回复, 给出 7 个 Part:

### Part 1: Graphiti 利用率全景判定 (必)

| API | 当前利用 % | 用户期望覆盖 % | 设计 gap |
|---|---:|---:|---|
| add_episode | 40% | ? | ? |
| valid_at/invalid_at | 0% | ? | ? |
| search_facts | 0% | ? | ? |
| search_communities | 0% | ? | ? |
| relationship sync | 0% (dry-run) | ? | ? |

**整体 Graphiti 设计成熟度**: X / 10

### Part 2: 4 大设计缺口的解决方案 (必)

每个缺口给出: 推荐方案 / 备选方案 / 实施路径 / 工时估算 (Sprint 几).

### Part 3: 6 议题的具体设计方案 (必)

每个议题给出: schema / API 调用 / 数据流 / mockup. 必须引用 Zep 官方文档或 GitHub examples.

### Part 4: Graphiti 学习科学价值评估

- 时序图谱 (valid_at/invalid_at) 对 Karpicke d=1.50 / EI+SE d=0.80 的实际增益预估
- search_communities 对元认知 2x2 (Dunning-Kruger) 的设计支持

### Part 5: 与现有 Canvas 设计的冲突 / 协调

- Graphiti edge vs Neo4j edge (G-FAKE 历史)
- Graphiti episode vs LanceDB vault_notes
- Graphiti search_facts vs Agentic RAG 6 路并行

### Part 6: 推荐的 Sprint 优先级

- Sprint 2 (Day 6-10) 应该先做哪个?
- Sprint 3 应该补哪个?
- Sprint 4+ 可推迟哪个?

### Part 7: 一句话产品判定

"**Graphiti 时序图谱在 Canvas 的设计 [是否] 真正服务于用户'记忆批注 + 记忆节点关系' 的核心需求? 当前主要问题是 [...], 推荐 Sprint 2 必修 [...].**"

## 6. 必读文件锚定 (XML bundle 内)

### 用户原话证据链
- `_bmad-output/研究/2026-05-22-3批注答疑v2-我的认知校准.md` (用户答疑 v2)
- `_bmad-output/research/round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md` (round-13 Q4 决策原文)
- `_bmad-output/research/round-9-*` (round-9 Q1 表格分工)

### 当前 Graphiti 设计 spec
- `_bmad-output/implementation-artifacts/epic-1/1-16-callout-graphiti-hook.md` (V-07 修复后, callout → Graphiti)
- `_bmad-output/implementation-artifacts/epic-2/2-10-wikilink-graphiti-sync.md` (wikilink → Graphiti)
- `_bmad-output/implementation-artifacts/epic-5/LITE-5-7.md` (两个记忆系统接通)
- `_bmad-output/implementation-artifacts/epic-5/LITE-5-6.md` (V-11 修复后 dual-write)
- `_bmad-output/implementation-artifacts/epic-4/LITE-4-3.md` (V-08+V-10 修复后, 路线 4 用 search_facts)

### 当前 Graphiti 实际代码
- `backend/app/services/episode_worker.py` (add_episode 异步队列)
- `backend/app/services/memory_service.py` (3 处 add_episode 调用)
- `backend/app/services/review_service.py` (add_episode_for_edge G-PIPE-006 闭环)
- `backend/app/services/relationship_sync_service.py` (Round-23 Story 8.4, dry-run)
- `backend/app/graphiti/entity_types.py` + `group_id_compat.py`
- `frontend/obsidian-plugin/src/ai-linked-doc.ts` (7 关系类型定义)
- `backend/app/core/subject_config.py::build_vault_group_id` (Story 2.5.Y)

### 历史决策 + gotcha
- `docs/known-gotchas.md` (G-FAKE-001 42+ 假命名修复历史)
- `_bmad-output/审查/2026-05-26-chatgpt-v7-v8-v10-v11-修复回应.md` (V-07~V-11 修复)
- `_bmad-output/审查/2026-05-26-开发计划报告-Obsidian-Hybrid-方向审计.md` (主审计报告, 含用户 line 47/146 批注)

### Graphiti 官方参考 (ChatGPT 必查)
- https://github.com/getzep/graphiti
- https://help.getzep.com/graphiti
- Graphiti 时序图谱论文 (search_facts vs search_nodes 用法)

## 7. 严格要求

- **必给具体设计**, 不能 "建议加强" 或 "需要改进"
- **必引用 Zep 官方文档 + GitHub examples** 作为依据
- **必给 file:line 证据** 在 Canvas codebase 中
- **避免**: "Canvas 整体架构良好, 仅需小幅优化" — 这是无信息回答
- **重点**: **设计层** 真相 + **产品层** 用户感知 + **学习科学层** d 值影响

## 8. ChatGPT 起手 prompt (复制粘贴)

```
请对我上传的 research-pack-graphiti-design-audit.xml 做 Deep Research 深度分析.

议题: Canvas Learning System 的 Graphiti 时序图谱设计审计.

用户原话锚点 (不可妥协):
"我选择 Graphiti, 是看重了它的时序图谱, 所以我觉得它记忆我的批注, 以及记忆我节点和节点之间的关系有优势."

XML 末尾的 <instruction> 段是完整任务书. 必读.

核心议题:
1. valid_at/invalid_at 时序图谱在 Canvas 完全 0% 利用, 怎么设计才能真用?
2. search_facts / search_communities 0 调用, 怎么落地 "节点关系查询" 和 "错误模式聚类"?
3. relationship_sync_service dry-run, 怎么让 ai-linked-doc 7 类关系真写 Graphiti edges?
4. 1h sweep 延迟 vs 用户期望即时, 怎么折中?

请按任务书 §3-§5 输出 7 个 Part, 必引用 file:line + Zep 官方文档/GitHub examples.

不要 "整体设计合理" 这种废话, 要具体的 schema + API 调用 + 工时估算.
```

---

**Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**前置审计**: `_bmad-output/审查/2026-05-26-开发计划报告-Obsidian-Hybrid-方向审计.md`
**新仓库 (备份)**: https://github.com/oinani0721/canvas-obsidian-hybrid
**Origin (主)**: https://github.com/oinani0721/canvas-learning-system (含 commit 16b648d)
