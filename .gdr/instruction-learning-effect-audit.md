# Deep Research 分析请求 — Canvas Learning System 学习效果落地审计

## 项目背景

**Canvas Learning System** 是一个 Obsidian 原生的学习应用 (从 Tauri 桌面应用降级而来):

- **核心 UX 哲学**: 利用 **Obsidian 及其优秀的双向链接 (`[[wikilink]]`) 功能** 来落地学习闭环。概念通过 wikilink 互联, 学习上下文通过节点间双链关系传递, 知识图谱 (Graphiti) 异步同步 vault 内的 wikilink 关系。**用户在 Obsidian Editor + Claudian sidebar 中完成所有学习交互**, 不需要打开任何独立应用窗口。

- **技术架构**:
  - 前端: Obsidian Plugin (TypeScript) + Claudian (Skill engine, Claude Code official integration)
  - 后端: FastAPI (Python) + Neo4j (port 7691) + LanceDB (向量存储 bge-m3 1024d) + Graphiti (Episode 时序知识图谱)
  - LLM: Claude API (主) + Gemini (仅 Graphiti episode_worker)

- **设计方法**: BMAD (Story spec + Epic 9 个) + Scheme A PRD v5 (锚定文档, 7594 行, 明确"学习效果守恒 ≥85%"作为首要成功指标)

- **现状 (2026-05-24)**: Sprint v3 Day 2, 3/27 stories done (INFRA-001 EventBus 修复 / INFRA-002 app_factory 装 18 router / INFRA-004 deps), 4 MVP UAT 用户实测通过 (Story 1.16 批注 hotkey / 1.17 AI 双链文档 / 1.18 Dashboard MD MVP / 1.19 检验白板配置 Skill).

- **用户**: 非技术背景 PM + CS 61B 学生 (主要 use case), vault 装算法/数据结构概念 (BST / recursion / eigenvalue 等), 双链关系反映 prerequisite 学习链. 用户 mental model 锁定为**"两个记忆系统"**:
  - 系统 1: LanceDB vault_notes 表 (精确笔记片段检索, bge-m3 语义向量)
  - 系统 2: Graphiti (学习历程 episode, 时序 + 关系查询)

## 分析议题

宏观学习效果落地审计 — Sprint v3 的 5 个新 BMAD spec + 现有 backend 28 服务 + plugin α-5 + 4 MVP 已 done 全部落地后, **是否能实现 PRD/EPIC 锁定的 9 个核心学习效果目标**:

1. **PRD §1.1 检验白板二分法 d=1.50** (Karpicke & Blunt 2011 Retrieval Practice — 完全空白 UI + Active Recall + reference_answer=None 三重隔离)
2. **PRD §1.2/1.3 Edge 对话 EI+SE d=0.55-0.73** (Elaborative Interrogation + Self-Explanation 多轮对话)
3. **PRD §1.5 两个记忆系统** (LanceDB 精确笔记检索 + Graphiti 学习历程) — 用户 mental model 锁定
4. **PRD §1.10 元认知 2x2 校准矩阵** (Dunning-Kruger 红区警告) — 已砍 (用户 3A 决策延 400+ 题), 评估学习效果影响
5. **PRD §2.3 三路融合出题** (canvas_type concept vs problem Constructive Alignment + Bloom 分层)
6. **PRD §2.4 三重隔离保证** (reference_answer=None 不可破)
7. **EPIC 4 检验白板灵魂** - 完整 d=1.50 设计 vs Sprint v3 简化版差距
8. **EPIC 5 掌握度追踪** - BKT + FSRS 完整 vs LITE-5-4/5-5 简化
9. **用户 2026-05-13 核心闭环原话**: "批注 + 双链探索 + 个人记忆系统 + 极其针对性的考察"

**视角**: 学习科学 + 产品 UX 宏观判定, **不是技术细节是否合理**.
**重点找**: "落地后学习效果会打折扣"的**隐藏漏洞**.

## 打包内容

55 个文件, ~482K tokens, 含:
- 锚定 PRD (7594 行) + epics.md (1191 行) + architecture.md + ux-design-specification.md + BMAD prd.md
- **5 个新 BMAD spec** (LITE-4-3 简化出题 / LITE-5-6 校准投票+4.9 merge / LITE-5-7 v2 两个记忆系统接通 / STORY-2-10 wikilink-Graphiti 同步 / Story 1.16-callout-graphiti-hook)
- **7 个决策追溯文档** (round-7 LanceDB 锁定 / round-9 2 系统分工 / round-12 Graphiti vs Karpathy / round-13 wikilink-Graphiti Q4 / 2026-05-13 核心闭环 / 2026-05-22 答疑 v2 / Sprint v3 plan 2026-05-21)
- **12 个 backend 关键 service** (episode_worker / context_enrichment / question_generator / learning_context / memory_service / lancedb_index / chat_context_assembler / rag_service / exam_service / exam_tools / api/v1/router)
- **7 个 plugin 关键源码** (main.ts / callout.ts / exam-quick.ts / status-bar.ts / frontmatter-tips-sync.ts / configure-whiteboard.ts / ai-linked-doc.ts)
- **8 个 UAT 验收单** (Canvas 完整学习闭环 / Story 1.16/1.17/1.18/1.19 4 MVP / Story 2.1 / Story MVP-α 端到端)
- **5 个已 done Story spec** (1.16-1.19 + 2.1)
- 2 个内部审查报告 (本次对比报告 + 既有 ChatGPT bundle)
- 配置 + BMAD CLAUDE.md + docker-compose + pyproject

## 分析方法

1. **通读 `<directory_structure>`** 建立心智模型 — Obsidian Hybrid 架构 (vault md + plugin TS + backend service + Neo4j/LanceDB/Graphiti)
2. **从 PRD §1-§2 学习科学锚点出发**, 追踪每个目标在 5 新 spec + backend service + plugin code 中的落地路径
3. **特别审 wikilink 双链的真实角色** — 是否真的承担"知识关系传递 + 学习上下文承载"，还是只是表面 UI 装饰? 验证证据:
   - LITE-4-3 出题路线 1/2 是否真用到节点 wikilink 邻居?
   - STORY-2-10 wikilink-Graphiti 同步是否激活了 wikilink 关系在 KG 中的查询?
   - Story 1.16-hook 写 callout 时是否记录了所在节点的 wikilink 出入度?
   - LITE-5-7 路线 B `search_facts(query=node_id)` 是否返回 wikilink 邻居的 facts?
4. **引用 `<file path="...">` + 行号作为证据**, 不靠假设
5. **验证发现与代码实际行为一致** (不要相信 spec 承诺, 必须读代码)

## 请分析

### a. 9 大学习效果落地度判定 (**必含**)

对每个 PRD 学习目标给:
- 落地度: ✅ 完全 / ⚠️ 部分 / ❌ 缺失 / 🔴 偏差
- 证据: `<file path="...">` + 行号
- 学习效果损失估计: 0% / 25% / 50% / 75% / 100%
- 根因: 设计层缺陷 / 实现层缺陷 / 集成层缺陷

**重点关注 Obsidian wikilink 是否真的承担"学习上下文 + 知识图谱"双重角色**, 还是只是表面 UI.

### b. 隐藏漏洞清单 (**必含**)

Claude 内部 2 Agent 已找到 **6 个已知漏洞** (见 `_bmad-output/审查/2026-05-24-prd-epic-vs-spec-对比报告.md`):
1. LITE-5-7 `blocks: ["LITE-4-3"]` 反向 (已修正 v2)
2. LITE-5-6 估时 2h 低估 (Task 3 同步逻辑漏算)
3. STORY-2-10 缺 Story 2.5.Y `depends_on` (group_id 规约)
4. LITE-5-7 v1 line 109 决策追溯 bug (已修正 v2)
5. PRD §1.5 三层记忆全砍是否过激 (已修正 v2 — 保 LanceDB + Graphiti)
6. PRD §1.3 Edge 对话 EI+SE 完全缺失 (Sprint v3 第 2 砍掉项)

**请找 #7+ 新漏洞**, 不重复已知. 特别关注:
- Graphiti `add_episode` 框架就绪 (episode_worker.py:562) 但 codebase 0 业务调用 — Story 2-10 + 1.16-hook 是否真能激活?
- LanceDB `vault_notes` 索引在跑, 但 LITE-4-3 / LITE-5-7 是否真用到了用户的笔记片段?
- `reference_answer=None` 隔离铁律是否在代码中有硬约束 (assert / hook), 还是只是 spec 文字?
- canvas_type concept vs problem 路由是否真有"易错点 prompt 模板", 还是只是 prompt 文件路径切换?

### c. 优先级评分 (**必含**)

每个漏洞给:
- 严重度: CRITICAL (学习闭环断裂) / HIGH (核心 d 值损失) / MEDIUM (UX 打折) / LOW (cosmetic)
- 学习效果损失估计 %
- 影响范围: 哪些 PRD 目标 / 哪些 Story 受波及

### d. 与学习科学社区最佳实践差距 (**必含**)

对照:
- **Karpicke (2011)** — Retrieval Practice d=1.50 (检验白板灵魂)
- **Roediger & Pyc (2012)** — Mixed Practice + Spacing 学习设计原则
- **Dunlosky (2013)** — 5 效果量最高学习技术 (PRACTICE TESTING + DISTRIBUTED PRACTICE + ELABORATIVE INTERROGATION + SELF-EXPLANATION + INTERLEAVED PRACTICE)
- **Nuthall (2007)** — 学习课堂数据 (Hidden Lives of Learners)
- **Bjork's Desirable Difficulty** — 难度阈值理论 (LITE-4-11 IRT 砍是否破坏此原则)

**判定**: 我设计的"妥协版" (5 个 Lite spec + 已 done 4 MVP) 是否仍能维持 d > 0.50 学习效应量?

### e. 可落地改善建议 (**必含**)

对每个漏洞给:
- spec 修改方向 (改哪个文件哪个 AC)
- 工作量估计 (h)
- 是否需新 Story (含建议命名)
- 是否影响 Sprint 2 交付时间表 (Day 9 必 ship)
- 优先级: 立刻 (Sprint 2 内) / Sprint 3 / Sprint 4+ / 永不做

### f. 量化指标建议

Sprint v3 后 4 周, 用户该如何**实证验证**学习效果实际达成? 设计 **3-5 个可观察指标**, 例如:
- "首次答对率提升 X% (基线 → Week 4)"
- "校准误差降低 Y% (用户 confidence vs 实际得分)"
- "Tips → Errors 反演率 (用户写过 Tip 的概念后续 Error 率)"
- "wikilink 双链密度增长率 (用户 vault 学习活跃度)"

## 额外上下文 (用户特别强调)

### ⭐ **Obsidian 双向链接是落地工具**

用户原话: "**我们现在的 Canvas Learning System 是用 Obsidian 及其其优秀的双向链接功能来落地**".

请重点审查:
1. **wikilink 在 LITE-4-3 出题上下文中**: 当系统调 `generate_question(node_id)`, 它是否真利用了节点的 wikilink 邻居 (前序概念 / 后续应用) 来增强题目个性化?
2. **wikilink 在 STORY-2-10 同步中**: 用户保存 md 后, wikilink 关系 (added / removed) 是否真正写入 Graphiti 知识图谱? 后续 `search_facts("X 和 Y 的关系")` 能否返回这个关系?
3. **wikilink 在 Story 1.16-hook 中**: 用户写一个 callout (`[!tip]+`), Graphiti episode 是否记录了这条 callout 所在节点的 wikilink 上下文 (它链向哪些其他节点)?
4. **wikilink 在 LITE-5-7 路线 B 中**: `search_facts(query=node_id)` 是否能找到通过 wikilink 互联的兄弟节点的历史 facts?

**核心问题**: 如果以上 4 处中**任何 1 处** wikilink 没被有效利用, 那"用 Obsidian 双链落地"就是空话, 学习效果会大幅打折.

### CS 61B 学生场景

用户主要 use case 是 CS 61B (UC Berkeley 数据结构与算法). vault 节点示例:
- `节点/recursion.md` — wikilink 到 `[[base-case]]`, `[[stack-frame]]`, `[[tail-recursion]]`
- `节点/BST.md` — wikilink 到 `[[binary-tree]]`, `[[in-order-traversal]]`, `[[avl-tree]]`
- `节点/eigenvalue.md` — wikilink 到 `[[linear-algebra]]`, `[[matrix-decomposition]]`

**关键学习路径**: 用户在 `BST.md` 写 `[!error]+` 说"我搞混了 in-order 和 pre-order" → 系统应该 (a) 写 Graphiti episode (Story 1.16-hook), (b) 出题时 (LITE-4-3) 引用此错误 + 触及 `binary-tree` 邻居 + `in-order-traversal` 双链, (c) 评分后 (LITE-5-6) 校准投票回写 Graphiti.

### 时间压力

- **Sprint 2 必须 ship** (Day 9 + Day 10 用户 UAT 截止), 不能再延期
- 修复建议要务实区分 "立刻修 (Sprint 2 内)" vs "Sprint 3 加" vs "永不做"

### 你不审什么

- ❌ Sprint v3 plan 整体合理性 (既有 ChatGPT v2 2026-05-21 已审过)
- ❌ Sprint 1 接通任务 (INFRA-001~007 / EXAM-001~003) 的技术合理性
- ❌ 已 done 4 MVP 的 UAT 重审 (用户已验收通过)

**你专注审**: **5 个新 Lite/新需求 spec + 已有架构落地后的学习效果是否达成**.

## 输出格式

### Part 1: 学习效果守恒矩阵 (必含)

| # | PRD 目标 | d 值 | 落地度 | 证据 (file:line) | 漏洞 | 学习效果损失 % | 修复建议 |
|---|---|---|---|---|---|---|---|
| 1 | §1.1 检验白板 | 1.50 | ✅/⚠️/❌/🔴 | ... | ... | 0-100% | ... |
| 2 | §1.3 Edge EI+SE | 0.55-0.73 | ... | ... | ... | ... | ... |
| 3 | §1.5 两记忆系统 | n/a | ... | ... | ... | ... | ... |
| 4 | §1.10 元认知矩阵 | n/a | ... | ... | ... | ... | ... |
| 5 | §2.3 三路融合出题 | n/a | ... | ... | ... | ... | ... |
| 6 | §2.4 三重隔离 | 灵魂 | ... | ... | ... | ... | ... |
| 7 | EPIC 4 检验白板 | n/a | ... | ... | ... | ... | ... |
| 8 | EPIC 5 BKT+FSRS | n/a | ... | ... | ... | ... | ... |
| 9 | 用户核心闭环 | n/a | ... | ... | ... | ... | ... |

### Part 2: 新漏洞清单 (#7+)

每个含: ID / 严重度 / 影响目标 / 学习效果损失 % / 证据 / 修复

### Part 3: 学习科学社区最佳实践差距

对照 Karpicke / Roediger / Dunlosky / Nuthall / Bjork 等学者实验, 给出"我们的设计能维持多少 d 值"判断

### Part 4: 改善建议清单

按 "Sprint 2 立刻修 / Sprint 3 加 / Sprint 4+ / 永不做" 分组

### Part 5: 量化验证指标 (3-5 个)

Sprint v3 后 4 周用户测什么

### Part 6: 执行总结 (300 字)

- 整体学习效果落地度 % (单数字)
- 必须 Sprint 2 修复的 critical 数
- 可推迟到 Sprint 3+ 的 medium 数
- **给用户一句话的"产品能否 ship 给 CS 61B 学生用"判断**

## 输出文体偏好

- 用中文回复 (用户母语)
- 表格 + 详细 narrative 解释每个 ⚠️/❌/🔴 行的原因
- 引用 `<file path="..."> + 行号` 作为证据 (不要泛泛而谈)
- **必须给数字** (学习效果损失 %, 工作量 h, 优先级排序) — 避免模糊的 "可能" / "也许"

—— END instruction ——
