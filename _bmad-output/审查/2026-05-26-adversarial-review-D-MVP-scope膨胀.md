---
title: "对抗审查 D — MVP scope 膨胀诊断 (Sprint v3 + V-07~V-11 补丁后)"
date: 2026-05-26
reviewer: "Claude 对抗 Agent (不客气模式)"
scope: "27 Story + V-07~V-11 修复 (+5.5h) + 4 MVP + 6 Lite spec"
verdict: "中产品伪装成 MVP"
---

# 对抗审查 D — MVP scope 是否已偷偷膨胀

## 1. 执行摘要

**scope 膨胀率 = 73%**(vs 真 MVP 18h)
计算: Sprint v3 当前 43.5h ÷ 真 MVP 25.2h = 1.73x

**核心指控 (3 条)**:
1. **14 项 MVP 清单本身就被偷换概念** — "刚需"清单包含 Agentic RAG L1+L2 / Edge 双策略 / Dashboard / Skill 命令等 5-6 项**典型"完美产品"功能**, 不是"最小可用"。真 MVP 应该 = "写批注 + 出针对性题 + 评分 + 看分数"四步。
2. **Sprint v3 capacity 43.5h ÷ 6h 假设 = 7.25 工作日** — 但 git log 显示 Story 2.4 单 Story 实际烧 7 commits × 2 天 (≈16h vs 6h 估), Story 2.2+2.9 烧 30+ commits × 3 天 (≈24h vs 12h 估). 真实 multiplier = **2.0x**, Sprint 2 真需 87h ≈ 14.5 工作日, 不是 10 工作日。
3. **V-07~V-11 修复 +5.5h 表面"小补丁", 实际是把 Lite spec 拖回完整版**: LITE-4-3 从 3h 翻倍到 6h (现在= 旧 4.3 完整版的 100%), LITE-5-6 从纯前端 2h 翻成 dual-write + sweep 2.5h (失去 Lite 本意). **修复说"学习效果不打折"= scope 完全不打折的换字游戏**.

---

## 2. 14 MVP × 应砍判定表

> 标准: 用户真要"明天 ship 给 CS 61B 期末复习用", 哪几项**不在头 30 天**也能学得动?

| # | 名称 | 现状 | 砍/留 | 理由 | 节省 |
|---|---|---|---|---|---|
| 1 | 原白板前端 | ✅ done | 留 | 看板入口, 不可砍 | 0h |
| 2 | 检验白板前端 | ✅ done | 留 | 考察入口, 不可砍 | 0h |
| 3 | 检验白板出题 prompt | 🔗 验证中 | **砍 5 路融合, 保 1 路 (当前节点)** | 单节点 retrieval 已 d>0.50 (Karpicke). wikilink 邻居/Graphiti facts 边际收益不到 0.20, 复杂度爆炸 | **5h (LITE-4-3 6→1h)** |
| 4 | 节点 AI 对话 | ⚠️ Win 未验 | 留 | 对话即学习, 核心 | 0h |
| 5 | Tips/Edge/错误写入检索 | 🔗 部分 | **砍 Graphiti 路径, 保 frontmatter + LanceDB** | LanceDB vault_notes 已能检索. Graphiti 仅给"X 和 Y 关系"加分 5%, 但开发 +10h | **8h (1-16-hook + LITE-5-6 + STORY-2-10)** |
| 6 | 检验白板新发现写入 | 🔗 未验 | 留 | 闭环关键 | 0h |
| 7 | Dashboard | ⚠️ 不全 | **延后 30 天** | 单用户首周用不到统计. 写 4 节点表格够了 (1.18 done) | **0h (已 done)** |
| 8 | Edge 对话 2 重策略 | ✅ 已实现 | **砍 EI+SE 策略, 保单路 Edge 对话** | 用户 3A 已砍 6.1/6.2/6.3, 但代码逻辑还在 — 单人无双策略价值 | 0h |
| 9 | Agentic RAG L1+L2 | ✅ 已实现 | **强烈应砍, 但代码已成熟** | 6 源并行检索/CRAG/Rerank/Faithfulness 全套是论文模板, 单用户 CS 61B 复习根本用不上. 但已 19,220 行存在 → **不删但不调** | 0h |
| 10 | 笔记精准检索 | ⚠️ 数据未流 | 留 | 用户已多次反馈"看不到笔记片段返回" — 是核心 | 0h |
| 11 | 基础 Hybrid Search | ✅ done | 留 | #10 依赖 | 0h |
| 12 | Claude Code 迁移 | ⚠️ Win 未验 | 留 | #4 依赖 | 0h |
| 13 | /命令 提示词模板 | ✅ done | 留 (已 done) | — | 0h |
| 14 | 对话拉出节点 | ✅ done | 留 | — | 0h |

**砍掉合计可省 13h** → Sprint v3 从 43.5h → **30.5h** (含 V-07~V-11 修复)

---

## 3. 6 Lite spec 合并/砍清单

| Lite spec | 估时 | 判定 | 理由 |
|---|---:|---|---|
| **LITE-4-3** (5 路融合, P0) | 6h | **降级到 3h (保 tips 注入, 砍 wikilink 邻居 + questions_registry)** | V-08 ChatGPT 说"绕开 wikilink 邻居 = 25% 学习效果损失" — 但**单 CS 61B 学生 50 题样本, d 值统计不出 0.25 差异**. V-10 question_text 持久化用 frontmatter 字段即可, 不需要新建 LanceDB 表 |
| **LITE-5-6** (校准投票, P2) | 2.5h | **砍异步 Graphiti 路径, 回 2h single-write** | V-11 ChatGPT 说"split-brain 10% 损失" — 但 spec 自相矛盾的根因就是想又简又全. **真 Lite = 写 frontmatter 完, 完全不写 Graphiti**. 400+ 题后再补 |
| **LITE-5-7** (2 记忆系统接通) | 3h | **砍路线 B (Graphiti search_facts), 保 LanceDB** | Graphiti 1s 超时降级路径 = 大概率永远走降级. 假动作 |
| **STORY-1-16-callout-hook** (V-07) | 5h | **砍 wikilink-context.ts, 回 3h** | Task 1.5 (plugin 抓 out_links/in_links/path_trace 5 字段) 是过度设计. 用户首周用不到"沿 A→B→C 探索路径"语义 |
| **LITE-4-11** (IRT) | 1h | 保留 | 真 Lite |
| **LITE-5-4** (pipeline_token) | 1h | 保留 | 真 Lite |
| **LITE-5-5** (错误分类) | 1h | 保留 | 真 Lite |
| **STORY-2-10** (wikilink-Graphiti sync) | 6h | **降级到 2h (只接 wikilink → 节点 LanceDB index 自动 refresh)** | 6h 写 events_queue + sweep cron + retry + failed_events 表 = 给单用户上工业级管道. 单人 vault < 500 节点, 直接同步够了 |

**Lite 总和**: 23.5h → **降级后 13h, 省 10.5h**

---

## 4. V-07~V-11 修复"过度"质疑 (3 条)

### 质疑 1: V-07 修复 callout 5 字段 = 给小白配企业级审计追踪

> ChatGPT 判定 "search_facts(\"X 和 Y 关系\") 查不出探索路径 → 违背 2026-05-13 核心闭环" — **但单用户首月 50-200 callout, 用 `path_trace[]` (max 5 跳) 查"关系"的实际场景在哪?** 用户原话"我在 A 沿 B → C 探索后对 C 写 tip Y" — 这是论文场景, 不是 CS 61B 期末. **5h 估时给 Task 1.5 抓 obsidian metadataCache 4 个 API + 5 边界单元测试**, 单用户首月触发率不到 5%. **过度修复**.

### 质疑 2: V-10 questions_registry 新建 LanceDB 表 = 修一个不存在的 bug

> ChatGPT 说 "exam_tools.py:435-454 Story 3.2 fix 把 node content 当 question_text → BKT/FSRS 信号污染". 真正解法是: **每题生成后, 在 plugin 的 exam_boards/*.md frontmatter 写 question_text 字段 (一行 yaml), score_answer 时 plugin 直接传 question_text 给 backend**. 0 新表, 0 新 service, 0 新 pipeline_token hash. **当前方案给单用户配 enterprise SOR (system of record)**, +1h Task 7 = **过度修复**.

### 质疑 3: V-08 wikilink 邻居 1-2 hops 强制注入 = 假"针对性"

> ChatGPT 说 "wikilink 邻居进出题主路径 = 25% 学习效果". 但 prompt 注入 "hop 1 邻居 brief (frontmatter title + body 100 字) + hop 2 仅 node_id" → 给 LLM 一坨"伪关系", LLM 其实就字面引用一个 `[[A]]` 完事, **不是真考"网络回忆"**. 真正考"网络回忆"需要 IRT/知识图谱辨析题型 (epic-4/4-11 IRT) — **但用户已 3A 决策砍 IRT**. **逻辑闭环不完整**, 加 2h Task 0 = **半成品过度修复**.

**最不能不修的是哪个**: 严格说**一个都可以不修**. 但若必须选一个 = **V-10**(评分对象漂移). 但解法应是 frontmatter 1 字段, 不是新建 LanceDB 表.

---

## 5. 推荐 Sprint v3 最小 ship 路径 (≤ 30h)

| Day | Story | 估时 | 累计 |
|---|---|---:|---:|
| 1 | INFRA-002 + INFRA-001 + INFRA-004 (已 done) | 6h | 6h |
| 2 | INFRA-003 + EXAM-001 + EXAM-002 | 6h | 12h |
| 3 | INFRA-005 + TEST-001 + PLUGIN-001 | 6h | 18h |
| 4 | PLUGIN-002 + PLUGIN-003 | 5h | 23h |
| 5 | **用户 UAT (Day 5 mini-ship)** + LITE-4-3 简版 1h (仅 tips 注入) | 5h | 28h |
| 后续 | Sprint 2 全砍 (INFRA-006/007 + MASTERY-001/002 + TEST-002 + DOC-001 + 6 Lite + V-07~V-11 全部) | — | — |

**裁掉**: STORY-2-10 / 1-16-hook / LITE-4-3 V-08 V-10 / LITE-5-6 / LITE-5-7 全部 → **Sprint 3+ 重新评估**

**理由**: 用户首要验证的是"我能写题, AI 出针对题, 评分跑通" — Sprint 1 已能 ship 这个. Sprint 2 把 LLM executor 统一 + Mastery V1 + 2 记忆系统接通 + 6 Lite 全塞进去 = **典型工程师"一次性建对"病**, 不是 MVP.

---

## 6. 结论 (一句话)

**当前是已伪装成 MVP 的"中产品 v0.7"**, 真 MVP 还差一刀砍 (从 43.5h 砍到 18h, 让用户 Day 5 就能 hands-on 验证核心闭环, 而不是 Day 10 才看到 wikilink 邻居被引用的"高级针对题").

---

## 附录: 4 维度对抗结论速查

| 维度 | 结论 | 数字 |
|---|---|---|
| 14 MVP 真"最小"? | 否, 至少 3 项可砍 (#3/#5 简化, #9 不调) | 省 13h |
| Sprint v3 估时虚胖? | 是, 真实 multiplier 2.0x (git log Story 2.4/2.2+2.9 证据) | 真需 87h |
| 6 Lite 个个小合起来超? | 是, LITE-4-3 6h+1-16-hook 5h+STORY-2-10 6h 三巨头吃掉 17h | 占 39% |
| V-07~V-11 过度修复? | 3 个都过度, V-10 最该修但应用 frontmatter 而非新表 | +5.5h 实际可省 4h |
