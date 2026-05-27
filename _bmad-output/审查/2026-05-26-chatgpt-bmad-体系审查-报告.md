---
title: "ChatGPT Deep Research — BMAD spec 体系级审查报告 (原文存档)"
date: 2026-05-26
source: ChatGPT Deep Research (Pro)
input_bundle: .gdr/research-pack-bmad-system-audit.xml (1.4MB / 412K tokens / 102 files)
prompt: .gdr/chatgpt-prompt-bmad-体系审查-起手.md
instruction: _bmad-output/审查/2026-05-26-bmad-体系级审查-任务书-给-ChatGPT.md
verdict: "BMAD spec 体系健康度 4.5/10 — 设计方向不错, 但治理差 (64 ready-for-dev 假繁荣 + spec 状态树没反映代码现实)"
core_finding: "不该继续按旧 64 ready-for-dev 往下做, 应改成按一条新 live 主干 spec 树 (5-ge-1~5 Graphiti runtime) 开发"
---

# Canvas Learning System BMAD 体系级深度审查报告 — ChatGPT 原文存档

> ⛔ ChatGPT Deep Research 原文, 不修改. Claude 的决策固化清单见 `_bmad-output/审查/2026-05-26-bmad-体系决策固化清单.md`.

## Part 1: 体系健康度总览

**结论: 你们现在不该继续"按旧 64 个 ready-for-dev 往下做", 而应该改成"按一条新的 live 主干 spec 树开发".**

76 个旧 BMAD spec 重分布判定 (ChatGPT 体系级判定, 非 YAML 字面值):

| 四态重判 | 数量 | 判定口径 |
|---|---:|---|
| 真 done / 已落地待验收 | **9** | 3 个 done + 6 个 review, 至少 1.17/1.18/1.19/2.5.Y 已有代码或运行面契约可证 |
| 真 active | **3** | **1.16、2.10、LITE-4-3**, 仍与 Sprint 2 v3 新主干直接耦合 |
| 推迟 Sprint 3+ | **45** | 不是废物, 但现在做会打散主干 (尤其 Epic 3/5/7/8 大部分) |
| 砍 / 归档 | **19** | 已被 supersede/deprecated/merge, 或与单人 Obsidian Hybrid 主线脱节 |

**关键洞察 — 状态漂移**: 旧 spec 与代码现状已明显漂移:
- 1.17 spec 只是 review, 但前端已把"派生节点选关系类型 → 写 relation callout → frontmatter relationships[] → 注入 AI prompt"整条链路写出来了
- 1.18 spec 写了 Dashboard.md + ConfirmExamModal 已 ship
- 1.19 spec + 主插件代码已有 canvas:configure-whiteboard 命令 + .canvas-config.yaml 读取

**真实问题不是"缺 spec", 而是"spec 状态树没及时反映代码现实".**

**整体健康度 4.5/10** — 分低不是设计方向错, 是体系治理差: 一边 64 ready-for-dev 假繁荣, 一边 G-FAKE-001/G-PIPE-006 历史提醒. "代码有、spec 不收口; spec 在、主干不唯一" = 低健康.

## Part 2: Sprint 2 v3 活跃项验证

**核心回答: Sprint 2 v3 该按什么 spec 开发?**

> 以 `epic-5-graphiti-era` 5 个新 spec 为主干, 以 1.16/2.10/LITE-4-3 为旧体系适配器和消费方, 以 1.17/1.18/1.19 作为"已交付待验收基线"而不是再拆新开发.

**5 必修 spec 与 ChatGPT 必修项一一对应** (frontmatter 依赖顺序正确):
- 5-ge-1 → #1 unified schema + #2 edge_type_map
- 5-ge-2 → #3 belief_key + add_triplet + valid_at/invalid_at
- 5-ge-3 + 5-ge-4 → #4 query-time flush / dry_run=False / group_id
- 5-ge-5 → #5 relation facade
- 依赖: 5-ge-1 block 5-ge-2/3/5; 5-ge-5 依赖 5-ge-1+2+3

**补中真实运行时缺口**:
- 今天 EpisodeWorker 已能传 entity_types/edge_types 给 add_episode (写入主干非零起步), 但 registry 只有一个 PrerequisiteRelation → 5-ge-1 是升级而非伪需求
- 今天 MemoryService 会 enqueue 到 GraphitiEpisodeWorker, 但 context_enrichment_service 仍读 **Neo4j-backed learning memory relations, 而非 Graphiti relation facade** → 5-ge-5 闭掉"写入了但读取没统一"的断层

**"11 active spec" 校正**:
- **正式 live spec 8 个** = 5-ge-1~5 + 1.16 + 2.10 + LITE-4-3
- **活跃但不算完整 spec 的工作项 3 个** = NEW-UX-001、NEW-UX-002、LITE-5-7 的 AC#1 小补丁
- **LITE-5-6 与完整 LITE-5-7 本身都应落 Sprint 3+** (frontmatter 就是 Sprint 3+, 不该混进 Sprint 2 主干叙事)

**Sprint 2 v3 依赖图**:

```text
Wave 1
  Session A: NEW-UX-001 + NEW-UX-002 + 文档/UAT
  Session B: 5-ge-1
  Session E: 1.16 / 2.10 的前端骨架, 但只能先做 scaffold, 不得锁死 payload

Wave 2
  Session C: 5-ge-2 + 5-ge-3 + 5-ge-4   (前置: 5-ge-1)
  Session E: 对齐 5-ge-1 后, 完成 1.16 / 2.10 的 payload 与事件上报
  Session A: 收尾 1.18 / 1.19 的 UX 验证

Wave 3
  Session D: 5-ge-5                      (前置: 5-ge-1 + 5-ge-2 + 5-ge-3)
  Consumer: LITE-4-3                    (前置: 2.10 + relation facade)
  Patch only: LITE-5-7 AC#1             (不是完整 spec 开发)
```

**"5 session 并行" 校正: 不是完全不冲突, 而是低冲突波次并行.** 两个硬依赖:
- **B ↔ E 是协议依赖, 不是文件冲突**: E 可并行写 shell, 但不能在 B 的 CanvasGraphEpisodeV1 和 edge_type_map 定版前合并
- **C ↔ D 是服务依赖, 不是资源冲突**: D 读的 relation facade 依赖 C 先把 belief version / flush contract 立起来
- 假冲突: A 跟别人基本不撞文件
- 真等待: D 必等 B/C, LITE-4-3 必等 2.10 + D

## Part 3: 旧 ready-for-dev 砍清单

**两刀: 先归档 19 个高置信度废 spec, 再把剩下大多数改 deferred (不再冒充 ready).**

### 立刻砍出 live tree (高确定性归档, 13 个)

| spec ID | epic | 原因 |
|---|---|---|
| 2.2 | Epic 2 | 已被 merged rerank-evidence 替代 |
| 2.9 | Epic 2 | 已被 merged rerank-evidence 替代 |
| 4.3 | Epic 4 | 已被 LITE-4-3 supersede |
| 4.9 | Epic 4 | 已并入 LITE-5-6 |
| 5.6 | Epic 5 | spec 内已写 deprecated, Lite 替代 |
| 5.7 | Epic 5 | spec 内已写 deprecated, Lite 替代 |
| 5.8 | Epic 5 | sprint-status 明确砍 |
| 6.1 | Epic 6 | 旧 Edge 讨论套件, 单人模式价值低 |
| 6.2 | Epic 6 | 同上 |
| 6.3 | Epic 6 | 同上 |
| 8.3 | Epic 8 | sprint-status 明确砍元认知矩阵 |
| 8.7 | Epic 8 | sprint-status 明确砍操作审计日志 |
| 9.1 | Epic 9 | sprint-status 明确砍多模态考察 |

### 候选归档 (Epic 1 infra, 5 个 — 不必删但不应占 live ready 槽位)

| spec ID | epic | 原因 |
|---|---|---|
| 1.4 | Epic 1 | Excalidraw/Canvas 方向性遗留, 已不在当前主线 |
| 1.10 | Epic 1 | 平台 health infra, 与产品主干解耦 |
| 1.12 | Epic 1 | MCP/deployment tier 偏运维, 非当前 MVP |
| 1.13 | Epic 1 | 外网部署检查清单, 不应占 live 槽位 |
| 9.2 外多模态前置 | Epic 9 | 全体往后排, 留一个延后入口 |

### defer (不砍, 改 deferred) — 4 大组
- **Epic 3 全部**: 节点 AI 对话应建立在 Sprint 2 Graphiti runtime 稳定之后
- **旧 Epic 5 的 5.1/5.2/5.3/5.4/5.5 + LITE-5-6/LITE-5-7**: 算法层和调度层, 非当前 runtime 主干
- **Epic 7 全部**: 依赖 FSRS/掌握度输出成熟
- **Epic 8 除被砍项外**: 等真实数据量上来

### 旧 spec 真正仍"有用"的
- 1.17/1.18/1.19 = 已交付待验收 Obsidian surface
- 2.5.Y = group_id/vault 隔离核心契约
- 1.16/2.10 = 新 Graphiti runtime 的旧入口适配层
- LITE-4-3/LITE-5-6/LITE-5-7 = Sprint 2~3 消费方桥接 spec
- 5.1/5.2/5.3 = Sprint 3 之后重新启用的学习算法层

## Part 4: BMAD 体系重构建议

**从"按历史 epic 堆文件"改成"按主干层次分 live tree".** 保留旧文件, 目录重构成 live/ + archive/ 两棵树.

| 新 live 组 | 应含 spec | 说明 |
|---|---|---|
| **obsidian-surface** | 1.17 / 1.18 / 1.19 / NEW-UX-001 / NEW-UX-002 | 用户可见入口与配置面 |
| **graph-ingest-runtime** | 1.16 / 2.10 / 5-ge-1 | 所有 callout/wikilink/calibration/error 统一入图层 |
| **graph-belief-and-retrieval** | 5-ge-2 / 5-ge-3 / 5-ge-4 / 5-ge-5 / LITE-5-7 | belief version、flush、relation facade、个人笔记返回 |
| **assessment-loop** | EXAM-001 / EXAM-002 / EXAM-003 / LITE-4-3 / LITE-5-6 | 检验白板、校准、生成与回写 |
| **mastery-and-review** | 5.1 / 5.2 / 5.3 / Epic 7 | BKT/FSRS/review queue, 留 Sprint 3+ |
| **platform-hardening** | 2.5.Y + 必要 infra | group_id/vault 隔离/auth/config 收口 |

**3 个接口契约必须显式化**:
1. **写入契约**: 所有学习事件必须通过 5-ge-1 统一 episode schema 入图, 禁止各 story 各自发散 payload
2. **读取契约**: LITE-4-3 与 LITE-5-7 不再直调 Neo4j learning memory 或底层 search_facts, 统一过 5-ge-5 facade
3. **隔离契约**: group_id 在 Canvas 侧统一用 build_vault_group_id(), Graphiti 边界统一用 sanitize shim, 禁止偷用 DEFAULT_GROUP_ID

**命名建议: epic-5-graphiti-era → `epic-5a-graphiti-runtime`**
- 理由: 它不是旧 Epic 5 的替代品, 是旧 Epic 5 的**上游 runtime**
- 旧 Epic 5 的 5.1/5.2/5.3 负责"掌握度/FSRS/融合决策"(下游), 5-ge 负责"时序 episode、belief version、关系检索契约先做对"(上游)

**支持新建小 `epic-6-edge-revival`**, 但不沿用旧 Epic 6 LMS 大叙事, 只做一件事: 把已存在的 1.17 关系输入 + Graphiti relation/runtime 完整接通 (用户锚点: "Edge 对话已实现, 双链连节点时填关系").

## Part 5: 多 session 并行验证

**5 session 并行可行, 但前提不是"分文件开发", 而是"先锁契约, 再分波次".** 历史有 G-FAKE-001 (名字像 Graphiti 身体不是) + G-PIPE-006 (桥有了但没单一主干), 不先锁契约会重演.

| 波次 | Session | 可以做 | 不能做 |
|---|---|---|---|
| **波一** | A | UX 修复、UAT、Dashboard 空态、status-bar 清理 | 不改 Graphiti 协议 |
|  | B | 5-ge-1 统一 schema / edge_type_map / event path | 不把未定 schema 推给前端 |
|  | E | 只写 scaffold: 1.16/2.10 前端采集壳 | 不得先行固定 payload |
| **波二** | C | 5-ge-2/3/4: belief/flush/relationship sync | 不越过 5-ge-1 自造 contract |
|  | D | 5-ge-5 facade 与 consumer 接口 | 必须等 B + C 定完 |
|  | Consumer | LITE-4-3、LITE-5-7 的调用改造 | 必须走 facade, 不得直调底层 |

**6 条协同硬规则 (固化, 避免 G-FAKE/G-PIPE 重演)**:
1. 每个 Session 必须绑定 spec_path + changed_files. 没有 spec_path 的工作项不能直接进 live 分支
2. 任何 supersede 必须同 commit 改旧 spec 状态. 新 spec 合并时旧 spec 不允许继续挂 ready-for-dev
3. 产品读写路径不允许双主干. 写统一走 episode runtime, 读统一走 relation facade
4. 所有 group_id 相关改动必须同时过 subject_config.py 与 group_id_compat.py
5. dry_run=True 只允许出现在恢复/批量重建工具, 不允许默默成为生产默认
6. D 不是与 B/C 并行, 而是"等待依赖完成后的快速收口 Session"

**规则 5 尤其重要**: 当前 relationship_sync_service 与 /relationships/vault endpoint 都把 dry_run=True 作默认; 不显式翻转, 用户会误以为"边关系接通了", 其实只是扫描统计.

## Part 6: Sprint 3 优先级

**Sprint 2 v3 ship 后, Sprint 3 不该立刻扩 surface, 而应补"学习闭环".** 按"先闭环、后算法、再队列"排序:

| 优先级 | spec ID | 工时 | 为什么 Sprint 3 必修 |
|---|---|---:|---|
| P0 | **LITE-5-7** | 3h | 把"个人笔记返回系统"补成最小可用 (用户剩余 MVP 之一) |
| P0 | **LITE-5-6** | 2.5h | 校准投票 dual-write, 补 exam → Graphiti 回写闭环 |
| P1 | **5.1** | 8h | 掌握度更新, 给后续调度提供状态量 |
| P1 | **5.2** | 8h | FSRS 间隔, 形成可执行 review scheduling |
| P1 | **5.3** | 10h | 五信号融合, 把 Graphiti/Exam/复习状态汇总成决策层 |
| P1 | **2.5.Y** | 30h | group_id/vault 隔离做成生产契约, 防多 session 多 vault 污染 |

**逻辑**: Sprint 2 做 Graphiti runtime; Sprint 3 做 learning loop. 先做 LITE-5-7+LITE-5-6+5.1/5.2/5.3 连成: Graphiti 记忆系统 + 个人笔记返回 + 检验白板投票/掌握度更新.

**补充**: 如果 2.5.Y 在 Sprint 2 期间随 Graphiti runtime 一并收口, 可从 Sprint 3 下掉换 Epic 7 review queue 首 spec. 但就 bundle 证据看, 宁可顶在优先列表, 不建议过早开 Epic 7 (group_id 半拉子会让所有 BKT/FSRS 建在脏命名空间上).

## Part 7: 一句话体系判定

> 当前 BMAD spec 体系健康度 **4.5/10**: 真正该开发的不是"旧 64 ready-for-dev", 而是 5-ge-1~5 这条新 Graphiti runtime 主干, 外加 1.16+2.10+LITE-4-3 三个旧 spec 适配/消费点; 1.17/1.18/1.19/2.5.Y 属于"已落地待验收或硬化收口", 5.1/5.2/5.3/LITE-5-6/LITE-5-7 才是 Sprint 3 的学习闭环主菜; 旧 spec 里至少 **19 个应立刻归档**, 其余大部分应改 deferred, 绝不能再让 ready-for-dev 冒充真实开发队列.

## 限制说明

判断基于 102 个文件. 证据最强: 任务书、sprint-status、5-ge 新 spec、1.17/1.18/1.19、2.5.Y、关键后端/前端实现. 对 2.3、2.5.X 等部分 review 项, bundle 内实现证据没有 1.17/1.18/1.19 那么直接, 在"真 done"口径上已尽量保守.

---

**Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**决策固化清单**: `_bmad-output/审查/2026-05-26-bmad-体系决策固化清单.md`
**前置**: `_bmad-output/审查/2026-05-26-bmad-spec-体系全图诊断.md` (Claude 初判) + `_bmad-output/审查/2026-05-26-chatgpt-graphiti-deep-research-报告.md`
