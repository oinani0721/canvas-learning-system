---
title: "PRD / epics.md / Sprint v3 plan 对比 4 spec — 用户批注审核报告"
date: "2026-05-24"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
audience: "用户（非技术 PM）"
agents_used:
  - "Agent A (Explore): 锚定 PRD + epics.md 对齐审计"
  - "Agent B (Explore): Sprint v3 plan + 依赖链 + 估时审计"
spec_under_review:
  - "_bmad-output/implementation-artifacts/epic-4/LITE-4-3.md"
  - "_bmad-output/implementation-artifacts/epic-5/LITE-5-6.md"
  - "_bmad-output/implementation-artifacts/epic-5/LITE-5-7.md"
  - "_bmad-output/implementation-artifacts/epic-2/2-10-wikilink-graphiti-sync.md"
truth_sources:
  - "锚定 PRD: /Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md (7594 行)"
  - "epics.md: _bmad-output/planning-artifacts/epics.md (1191 行)"
  - "Sprint v3 plan: _bmad-output/research/2026-05-21-sprint-plan-v3.md"
  - "决策 v2: _bmad-output/研究/2026-05-22-3批注答疑v2-我的认知校准.md"
overall_compliance: "70-87% (Agent A 87% / Agent B 70%)"
critical_issues_count: 6
moderate_issues_count: 4
low_issues_count: 2
---

# 📊 对比报告：PRD / epics.md / Sprint v3 plan vs 4 个新 spec

> ⛔ **审核模式**：请在每个 `[!question]+` callout 写你的批注（✓ 接受 / ✗ 拒绝 / ? 商讨 + 一句话理由）
> 📝 报告基于 2 个独立 Explore agent 平行对抗审查，发现 **3 个 critical + 3 个 high + 4 个 medium** 风险

---

## 🎯 摘要（30 秒读完）

| 维度 | 分数 | 关键发现 |
|---|---|---|
| **PRD 灵魂对齐度** | 87% | canvas_type / reference_answer 隔离 / wikilink-Graphiti 保留正确 |
| **epics.md AC 覆盖率** | 90% | 5.6/5.7 超额覆盖 (含 4.9 merge / 加 callout 过滤) |
| **Sprint v3 砍点合规度** | 100% | 4 spec 都没偷偷复活 8.3 / 8.7 / Edge / Hot-Warm-Cold |
| **依赖链正确性** | 60% | 🔴 LITE-5-7 `blocks` 反向 / 🔴 STORY-2-10 缺 2.5.Y depends_on |
| **estimate_hours 可信度** | 70% | 🟡 LITE-5-6 估 2h 漏算同步逻辑 / 🟡 STORY-2-10 6h 紧 |
| **AC Given/When/Then 质量** | 80% | 🟡 LITE-4-3 AC#1 混合多约束 / 🟡 STORY-2-10 AC#4 FR+NFR 混用 |
| **决策追溯准确性** | 75% | 🔴 LITE-5-7 line 109 bug（误用"用户 1B 决策"）|

**判定**: 4 spec **可进 Sprint 2 开发，但需先修复 3 个 critical + 1 个 line bug**（30min 修完）。

---

## 🔴 表 1: PRD 灵魂设计 vs 4 spec 覆盖（Agent A）

| PRD 章节 | 原始要求 | 我哪个 spec 覆盖 | 简化点 | 风险 |
|---|---|---|---|---|
| **§1.1 检验白板二分法 d=1.50** | 完全空白 UI + Active Recall | LITE-4-3 | 保留 reference_answer=None | 🟢 |
| **§1.3 Edge 对话 EI+SE d=0.80-1.00** | Elaborative Interrogation + Self-Explanation 多轮 | **❌ 完全缺失** | 完全砍（Sprint v3 第 2 砍掉项）| 🔴 **高 — 原白板剖析失去 d=0.80-1.00 效应量，需在 spec 标注 Sprint 3+ 加回** |
| **§2.3 Step 7 三路融合出题 5 层数据流** | Graphiti + Graphify + BKT/FSRS + canvas_type + reference_answer=None | LITE-4-3 AC#1-7 | 保留 canvas_type 分化 / 禁 Graphiti / 禁 Graphify | 🟡 |
| **§2.4 三重隔离保证 3** | MCP 工具返回值过滤：reference_answer 永不外泄 | LITE-4-3 AC#4 | 硬约束 None | 🟢 |
| **§1.5 三层记忆 LanceDB/Neo4j/Graphiti** | Layer 1 短期 + Layer 2 中期 + Layer 3 长期 调度 | LITE-5-7 | **完全禁** Layer 1/2/3 / 仅本地 N=5 callout | 🔴 **高 — 不符合 PRD §1.5 灵魂；但单用户合理砍，需 `depends_on_later` 标记 Sprint 4 补回** |
| **§1.10 元认知 2x2 矩阵** | Dunning-Kruger 红区 + confidence × actual 二维统计 | LITE-5-6 | 完全砍（用户 3A 决策）| 🟡 |
| **§2.4 校准投票 dual-write** | frontmatter + Graphiti 双写审计 | LITE-5-6 AC#3 | 改 single-write + 砍 add_episode | 🟡 |
| **wikilink-Graphiti 同步（round-13 Q4）** | Lazy + Batch hourly cron | STORY-2-10 (6h) | **完全保留** round-13 Q4 设计 | 🟢 |
| **canvas_type 分化** | Constructive Alignment + Bloom 层级 | LITE-4-3 AC#2-3 | 完全保留 | 🟢 |
| **AR-8 pipeline_token 5 步防篡改链** | token_A → score → token_B → BKT → FSRS → calibration | LITE-4-3 + LITE-5-6 | **简化为 2 步**（仅 generate + score）| 🟡 **中 — 单用户无 abuse risk 可接受，但 Sprint 4 需补完 Step 3/4/5** |
| **Graphiti group_id 隔离 (Story 2.5.Y)** | vault_id + subject_id + canvas_path 防跨 vault 泄漏 | STORY-2-10 AC#4 | 保留 `vault:{vault_id}` 规约 | 🟢 |
| **三重隔离降级策略** | §2.4 line 1638-1693, 6 scenario graceful degrade | 隐含覆盖 | 禁用路径已是"降级固化" | 🟡 |

> [!question]+ **批注 1.1 (PRD 灵魂对齐)**
>
> Edge 对话 EI+SE 完全砍 — 我应该现在加 spec 还是接受推迟 Sprint 3+ 加回？

> [!question]+ **批注 1.2 (三层记忆完全禁用)**
>
> 完整 PRD §1.5 要求 Layer 1/2/3 三层调度，我 LITE-5-7 全砍。你能接受单用户简化吗？

> [!question]+ **批注 1.3 (pipeline_token 5→2 步)**
>
> AR-8 防篡改链从 5 步简化为 2 步，Sprint 4 补回。OK 吗？

---

## 🟡 表 2: epics.md Story AC 覆盖率（Agent A）

| Epic | Story ID | epics.md AC 数 | 我 spec AC 数 | 覆盖率 | 缺失 / 超额 |
|---|---|---|---|---|---|
| Epic 4 | Story 4.3 三路融合出题 | 8 条 (FR-EXAM-03/13) | 7 条 (LITE-4-3) | 87.5% | ❌ "超时降级"隐含在 Task 4 非显式 AC |
| Epic 5 | Story 5.6 校准投票 | 6 条 (FR-MEM-02/03 + FR-EXAM-15/17) | 7 条 (LITE-5-6) | 100% | ✅ 超额加 4.9 merge sync 逻辑 |
| Epic 5 | Story 5.7 三层检索 | 5 条 (FR-MEM-04) | 7 条 (LITE-5-7) | 100% | ✅ 超额加 callout 类型过滤 (AC#7) |
| Epic 2 | STORY-2-10 wikilink-Graphiti | **新需求** (非原 epics.md) | 8 条 (AC#1-8) | N/A | round-13 Q4 决策 + 用户 1B 加速 |

---

## 🔴 表 3: 依赖链漏洞（Agent B — 最 critical）

| Spec | depends_on / blocks | 漏洞 | 影响 | 修复 |
|---|---|---|---|---|
| **LITE-4-3** | depends_on `INFRA-002, EXAM-001, EXAM-002` | 🔴 **缺 LITE-5-7** | AC#1 路线 3 调 `get_recent_context(node_id, n=3)` — 但 depends_on 没列 LITE-5-7 | depends_on 加 `"LITE-5-7"` |
| **LITE-5-7** | blocks `["LITE-4-3"]` | 🔴 **关系反向** | `blocks` 应表"我做完别人才能做"。实际 LITE-4-3 是依赖方，不是被阻塞方 | LITE-5-7 `blocks: []`（同上 LITE-4-3 加 depends_on）|
| **STORY-2-10** | depends_on `INFRA-002, PLUGIN-001` | 🔴 **缺 Story 2.5.Y depends_on** | AC#4 用 `build_vault_group_id` from Story 2.5.Y。2.5.Y 状态不明 → 跨 vault 泄漏风险 | 确认 2.5.Y 状态（CLAUDE.md 说"2026-05-05 D16 锁定"），若已 done 加 depends_on |
| **LITE-5-6** | depends_on `EXAM-001, PLUGIN-002` | 🟡 缺 frontmatter_writeback_service 来源 | AC#3 sync 用 service，没列前置 Story | 备注：复用旧 5.6 service or 新建 LITE-5-6 内自建 |

> [!question]+ **批注 2.1 (LITE-5-7 blocks 反向 — 必修)**
>
> 我把 LITE-5-7 `blocks: ["LITE-4-3"]` 写反了。正确应是 LITE-4-3 `depends_on: ["LITE-5-7"]`。立刻改？

> [!question]+ **批注 2.2 (Story 2.5.Y 是否 done)**
>
> CLAUDE.md 说 "Story 2.5.Y D16 锁定 2026-05-05"，但 sprint-status 没明确状态。请确认能让 STORY-2-10 直接复用 `build_vault_group_id()` 吗？

---

## 🟡 表 4: estimate_hours 合理性（Agent B）

| Spec | 估时 | Agent B 判定 | 风险信号 |
|---|---|---|---|
| LITE-4-3 | 3h (vs 旧 6h) | 80% 可信 | 砍 Graphiti/Graphify 确实省 ~2-3h，但前提是 LITE-5-7 ready |
| **LITE-5-6** | **2h** (vs 旧 5h + 4.9 6h) | 🔴 **严重低估** | Task 3 sync 需要源白板路径解析 + 防 YAML 破坏 + 异步重试 = 单 Task 1-1.5h；7 Task 总 2h 不够 — **建议 2.5-3h** |
| **LITE-5-7** | **2h** (vs 旧 5h) | 🟡 承诺过度 | "< 100 行 service" 算上 regex parse + 7 task + 单测 — **建议 2-2.5h** |
| **STORY-2-10** | **6h** | 🟡 偏紧 | hourly cron 新基础设施需部署验证 + Task 8 e2e "mock cron 即时触发"决策未定 — **建议 6.5-7h** |

> [!question]+ **批注 3.1 (LITE-5-6 估时改 2.5-3h)**
>
> Agent B 说同步逻辑 Task 3 单 Task 1-1.5h，整体 2h 偏紧。改 2.5h 或 3h？

> [!question]+ **批注 3.2 (STORY-2-10 估时改 6.5-7h)**
>
> 新 hourly cron 基础设施 + e2e 测试。给 0.5-1h buffer 可吗？

---

## 🟡 表 5: AC Given/When/Then 质量（Agent B）

| Spec | AC 问题 | 修复建议 |
|---|---|---|
| LITE-4-3 | AC#1 混合"3 路融合 + 禁 Graphiti/Graphify 双约束" | 拆为 2 条 AC：一个讲做什么，一个讲不做什么 |
| LITE-5-6 | AC#3 隐含假设 `source_canvas` frontmatter 字段存在 / AC#4 "unique by question_id+vote" 含歧义（vote 可改吗）| AC#3 加 fallback 路径；AC#4 显式说明 immutable |
| LITE-5-7 | AC#2 负面需求"不调 Layer 1/2/3"难自动化 | 改正面："调用 `vault.read_file()` + regex parse callout" |
| STORY-2-10 | AC#4 + AC#7 重复 "1-60 分钟" | 拆 FR（功能）vs NFR（性能 checkpoint）|

> [!question]+ **批注 4.1 (AC 质量改进)**
>
> 这 4 处 AC 改进是 nice-to-have 还是必须改？我倾向必修因为 BMAD dev-story 解析 AC 出题。

---

## 🔴 表 6: 决策追溯 bug（Agent A 发现，必修）

| Spec | 段位 | 问题 | 正确版本 |
|---|---|---|---|
| **LITE-5-7** | line 109-110 Background Decision Trace | 🔴 误用 "用户 1B 决策（2026-05-22）：WIKILINK-GRAPHITI-SYNC 加入 Sprint 2" 作为 LITE-5-7 砍层依据 | 实际 1B 决策是**加速 STORY-2-10**，LITE-5-7 砍层来自 "Sprint v3 plan 3 agent 共识：单用户样本不足 + Hot/Warm/Cold 已砍" |

> [!question]+ **批注 5.1 (LITE-5-7 line 109 决策追溯 bug — 必修)**
>
> Agent A 抓到的 spec 内部 bug。立刻修？

---

## 📋 修复优先级清单（推荐顺序）

| # | 修复项 | 工作量 | 阻塞 Sprint 2 开始？ |
|---|---|---|---|
| 1 | LITE-5-7 `blocks: []` + LITE-4-3 加 `depends_on: ["LITE-5-7"]` | 2 min | ✅ **YES** — 反向依赖造成环形等待 |
| 2 | LITE-5-7 line 109-110 决策追溯改正 | 3 min | ✅ **YES** — 误导新 session |
| 3 | 确认 Story 2.5.Y 状态 + STORY-2-10 加 depends_on | 5 min | 🟡 部分（影响 group_id 隔离）|
| 4 | LITE-5-6 估时 2h → 2.5-3h | 1 min | 🟢 NO（不影响开发，仅 sprint plan）|
| 5 | STORY-2-10 估时 6h → 6.5-7h | 1 min | 🟢 NO |
| 6 | 4 处 AC 质量改进（拆约束 / 加 fallback / 改正面 / FR+NFR 拆） | 15-20 min | 🟡 影响 dev-story 解析质量 |
| 7 | LITE-4-3 Task 5 加注 "Sprint 4 补 pipeline_token 5 步" | 1 min | 🟢 NO |
| 8 | LITE-5-7 加 `depends_on_later: ["LITE-5-9-three-layer-revival"]` | 1 min | 🟢 NO（标记 Sprint 4 补三层）|
| 9 | LITE-4-3 标记 "Edge 对话 EI+SE 推迟到 Story 6.1 Phase 2" | 2 min | 🟢 NO |
| **总** | | **~30-40 min** | |

---

## 🎯 给 ChatGPT Deep Research 的简报

> Canvas Learning System v3 Lite spec（4 个 Story，~13h 总工作量）对比锚定 PRD 灵魂对齐 87% / epics.md AC 覆盖 90%。**已修复策略**：保留检验白板 d=1.50 / canvas_type 分化 / reference_answer=None 隔离 / wikilink-Graphiti 单向 Lazy+Batch。**已知 critical 风险**：(1) LITE-5-7 `blocks` 关系反向需立刻修；(2) STORY-2-10 缺 Story 2.5.Y 显式 depends_on；(3) LITE-5-6 估时 2h 漏算源白板同步逻辑；(4) LITE-5-7 line 109 决策追溯 bug。**3 个 PRD 灵魂砍点**：Edge 对话 EI+SE / 三层记忆 Layer 1/2/3 / pipeline_token 5→2 步 — 单用户阶段合理砍，但需标记 Sprint 3+ 补回。
>
> 求 ChatGPT 审计：(a) 我对 PRD §1.5 三层记忆的全砍是否过激？(b) STORY-2-10 hourly cron 是否应改 15-30min？(c) 是否漏了 PRD 哪条灵魂设计未被我对照？

---

## 📝 用户批注总区（Cmd+Shift+A 加批注）

> [!question]+ **总批注 A — 我同意全部 6 个 critical/high 修复**
>
> 写 ✓ 或具体反对项

> [!question]+ **总批注 B — Edge 对话推迟 vs 现在加 spec**
>
> 你的判断

> [!question]+ **总批注 C — 我接受 87% PRD 灵魂对齐**
>
> ✓ 接受 / 求 100% 对齐

> [!question]+ **总批注 D — 下一步**
>
> 选 1 个: (a) 我先修 6 个 critical, 再 commit / (b) ChatGPT 审完再决定 / (c) 全 commit 当前状态 ship 给新 session

---

## 🔗 引用

- **Agent A 报告原文**: 见本 session chat history (Explore Agent A output)
- **Agent B 报告原文**: 见本 session chat history (Explore Agent B output)
- **PRD 锚定**: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md`
- **epics.md**: `_bmad-output/planning-artifacts/epics.md` (line 186-268 关键段)
- **Sprint v3 plan**: `_bmad-output/research/2026-05-21-sprint-plan-v3.md`
- **决策 v2**: `_bmad-output/研究/2026-05-22-3批注答疑v2-我的认知校准.md`
- **XML 打包**: `_bmad-output/审查/2026-05-24-deep-research-bundle.xml`（下一步生成）
