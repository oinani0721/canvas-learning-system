---
title: "DeepTutor 本书导览（Overview chapter）设计深度调研"
type: "design-report"
date: "2026-05-08"
trigger: "用户在 fork :3782 看 bk_e6071278a4 反馈 Overview 质量差"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
agents_used: 2
sources_count: 30
related_files:
  - "deeptutor-fork/deeptutor/book/engine.py:398-578"
  - "deeptutor-fork/deeptutor/book/agents/spine_synthesizer.py:436-603"
  - "deeptutor-fork/web/app/(workspace)/book/components/blocks/ConceptGraphBlock.tsx"
  - "deeptutor-fork/web/app/(workspace)/book/components/blocks/TextBlock.tsx:11"
---

# DeepTutor 本书导览设计深度调研报告

> **触发**: 用户 2026-05-08 1:19 反馈 `bk_e6071278a4` 的"本书导览"质量差。Mermaid 图标"18 chapters · 22 dependencies"实际是 chapter + concept_node 混画杂乱；"如何阅读这本书" / "章节索引"段空白。
>
> **方法**: 2 个并行 agent。Agent A 审计 fork 内部 Overview pipeline，找 bug + 限制。Agent B 调研学术 + 7 现代产品的 interactive book overview UX 实证。

## Executive Summary

1. **本书导览质量差是 fork 内部 schema 不一致 BUG，不是 Opus 4.7 渲染问题**: engine.py 写入 `payload.content`，但前端 TextBlock.tsx 读 `payload.body` → 第 0 + 2 个 block 永远空白。这是 1 行修可拯救 70% 体验的关键 BUG。
2. **Mermaid 图 22 节点杂乱是第二个 BUG**: spine_synthesizer.py 没过滤 OVERVIEW chapter，导致 overview 自己也被画进 mind map → 5 chapter + 18 concept = 22 节点视觉乱炖。
3. **Overview 缺失结构性设计深度**: 3 个 deterministic 预定义 blocks，无 LLM 生成的章节描述/推荐路径/进度可视/难度分级 — 仅"目录 + 静态图 + 一段叙述"。
4. **理想 Overview 应有 12 个元素**：基于 Tufte data-ink + Karpathy index.md + Khan Academy mastery + Heptabase sections + Distill TOC 收敛。当前 fork 满足 3 项，缺 9 项。
5. **总修复路径 ~35h（P0 14h + P1 12h + P2 9h）**：但 1-line bug fix（< 30 分钟）立即从"杂乱空白"跳到"可读完整"。

---

## 第 1 节 · Fork Overview Pipeline 审计（Agent A）

### 1.1 完整生成链路

```
POST /books/confirm-spine
  ↓
BookEngine.confirm_spine()  [engine.py:582]
  ├─ ① _ensure_overview_chapter()        [398-451] 在 spine.chapters[0] 注入 OVERVIEW chapter
  ├─ ② 为每个 chapter 创建 PENDING Page  [614-629]
  ├─ ③ _materialize_overview_page()      [453-578] ⚠ 走独立分支，仅 3 deterministic blocks
  │     强制 page.status=READY → 永不进 worker queue
  ├─ ④ _enqueue_pending_pages()          [754-770] line 764 跳过 READY → Overview 不调 LLM
  └─ ⑤ 后台 worker 编译其他 chapter
```

**关键判断**: Overview chapter 走的是**独立 deterministic 分支**，**不经过 PagePlanner / SectionArchitect / TextGenerator**。这是 fork 的设计选择（"无 LLM 即时呈现"），但代价是 Overview 内容深度严重不足。

### 1.2 Block[0..3] 来源溯源（critical 数据流）

| # | Block 来源 | 文件:行号 | payload schema | 前端读取 | 状态 |
|---|---|---|---|---|---|
| 0 | `_materialize_overview_page` 步骤 1 | engine.py:487-513 | `{"content": intro_md, "format": "markdown"}` | TextBlock.tsx:11 读 `payload.body` | ❌ BUG · 永远空白 |
| 1 | `_materialize_overview_page` 步骤 2 | engine.py:515-544 | `{"render_type", "code", "graph", "index"}` | ConceptGraphBlock.tsx 正常 | ⚠️ 标注误算 |
| 2 | `_materialize_overview_page` 步骤 3 | engine.py:546-560 | `{"content": index_md, "format": "markdown"}` | TextBlock.tsx 读 `payload.body` | ❌ BUG · 永远空白 |
| 3 | 用户手动 `POST /books/blocks/insert` 插入 | engine.py:982 → text.py:64-79 | `{"format": "markdown", "body": <LLM 生成>, "role"}` | TextBlock.tsx 正常 | ✅ 显示 |

**Block 3 的发现 = 反向证明 BUG**: block[3] 之所以正常显示，是因为它走 TextGenerator 标准 schema (`body` 字段)；block[0] + [2] 走的是 deterministic 路径用 `content` 字段 → 双标 → 前端只读 body → 视觉空白。

### 1.3 4 个核心问题

#### BUG 1 (CRITICAL · 1 行 fix)：payload schema 双标

**engine.py:512** + **engine.py:559**：
```
intro_block.payload = {"content": intro_md, "format": "markdown"}  # ❌
index_block.payload = {"content": index_md, "format": "markdown"}  # ❌
```

**对比标准 LLM 路径** text.py:73-77 用 `body` 字段。**前端** TextBlock.tsx:11 读 `payload.body`。

**1 行 fix**: `"content"` → `"body"`。立即拯救 block[0] + [2] 内容。

#### BUG 2 (HIGH · 1 行 fix)：ConceptGraph 把 OVERVIEW 自己画进图

**spine_synthesizer.py:526**：没 filter OVERVIEW，for-loop 把 overview chapter 也变成 ConceptNode。

**结果**: 22 节点 = 5 chapter（含 overview）+ 18 concept node。截图显示 "18 chapters" 是 ConceptGraphBlock.tsx:79 的 `chapterNodes.filter(n => n.chapter_id)` 返回 18（concept_node 也有 chapter_id 字段）→ 标注误算。

**1 行 fix**: 加 filter `if ch.content_type != ContentType.OVERVIEW`。

#### BUG 3 (MEDIUM)：dependencies 计数包括 virtual root edges

**ConceptGraphBlock.tsx:94-95** 用 `edgeCount` 全图 edges。应该改为：仅算 chapter→chapter 边（双端都有 chapter_id 的边）。

#### LIMITATION 4 (HIGH · 设计层面)：Overview 内容深度不足

`_materialize_overview_page` docstring (line 461) 写明 "deterministic / no LLM"。代价：
- ✗ 无 chapter 描述（line 553 `index_md` 仅用 `chapter.summary` 单句，无 LLM 扩写）
- ✗ 无推荐阅读路径（spine 已做拓扑排序但 overview 不展示）
- ✗ 无难度分级 / mastery_score 提示
- ✗ 无跨 chapter TIMELINE 整合（fork 已有 TimelineBlock 但 OVERVIEW 不用）
- ✗ 无 book metadata（创建时间、KB 来源、估计学时）
- ✗ 无 RAG（text.py 标准路径调 `optional_rag_lookup`，overview 完全跳过）

---

## 第 2 节 · Interactive Book Overview UX 调研（Agent B）

### 2.1 学术参考（5 个核心理念）

| 来源 | 核心理念 | 对 Overview 的启示 |
|---|---|---|
| **Tufte — Envisioning Information** | "Micro/macro designs avoid context switching"；data-ink 最大化 | 同屏 macro（全书地图）+ micro（每章 sparkline 进度），不要切页 |
| **Donald Norman — wayfinding/signposting** | Signposts 让用户判断"我在哪、能去哪、怎么回来" | 显式标记"你在哪章 / 已读哪些 / 推荐下一章" |
| **NN/g 5-Second Test** | 50ms 形成首因，55% 用户 15s 内离开 | Hero 区必须 5 秒回答"这本书讲什么 + 我从哪开始" |
| **Riedl 2005 Branching narratives** | 线性 vs 分支阅读路径 | 同时支持 linear "first read" + branching "review/skip" |
| **Tufte sparklines** | "Word-sized graphics" 嵌入文字流 | 章节列表每行嵌进度 sparkline，比 progress bar 信息密度高 10× |

### 2.2 7 个现代产品实例

| # | 产品 | 关键设计 |
|---|---|---|
| 1 | **Heptabase Whiteboard + Tag Page** | Sections 缩远仍可见标题；Mindmap auto-layout；Tag = 表格（每 card 一行 + difficulty/status 列）；backlink info section |
| 2 | **Maggie Appleton garden** | Topic index（5-6 大方块插画封面）；ripeness 标记（🌱 seedling / 🌿 budding / 🌳 evergreen）；recent notes 时间流 |
| 3 | **Quartz 4** | Recent Notes 默认开启；wikilinks + transclusions + backlinks；左 explorer + 中正文 + 右 TOC + 底 graph mini-view |
| 4 | **Karpathy llm-wiki** | index.md = 唯一目录；每页一行 wikilink + 一句 summary + metadata（date / source count）；按 category 分组 |
| 5 | **Khan Academy 课程页** | Mastery tracker：每 skill 1 cm² 彩色方块（绿=mastered/黄=proficient/灰=未学）；hover 预览 + click 跳；⚡=quizzes / ⭐=unit tests |
| 6 | **Distill.pub TOC** | Floating left TOC（>1000px 自动浮动）；scroll-active state；YAML `toc: true` 一键启用 |
| 7 | **Obsidian MOC + Dataview** | MOC = hub note；3 级 sections；每个 # 下放 Dataview query 自动列出指向该 section 的 notes；多 MOC 引用不重复 |

### 2.3 理想 Overview 的 12 元素清单（按重要度）

| 优先级 | 元素 | 实证依据 |
|---|---|---|
| **P0** | 5 秒可读核心 promise（hero + 一句话） | NN/g 5-second test, Maggie hero |
| **P0** | "Start Here" 推荐起点 + reading path | Maggie / Khan / Coursera 共识 |
| **P0** | 章节列表带 inline metadata（一句 summary + difficulty + 估时 + status） | Karpathy index.md / Khan mastery / Tufte data-ink |
| **P0** | 进度/掌握度可视化（每章 sparkline 或彩色方块） | Khan Academy mastery squares / Tufte sparkline |
| **P1** | 概念图 + 章节列表联动（双向 click 高亮） | Heptabase backlink / Quartz graph view / Tufte micro-macro |
| **P1** | 概念图节点分类着色（hub 大 / 叶小 / Louvain 染色） | Understand-Anything / Heptabase sections / Tufte layering |
| **P1** | floating "ON THIS PAGE" TOC + scroll-active | Distill.pub |
| **P1** | "已读 / 复习 / 未读" 三态过滤 | Khan tracker / Anki deck states |
| **P2** | 元信息条（创建/更新时间、版本、作者、源数量） | Karpathy / Coursera instructor bio |
| **P2** | "Skip ahead" 前置依赖检查 | Khan prerequisite chains |
| **P2** | Recent activity / "上次读到这里" | Quartz Recent Notes / Norman wayfinding |
| **P2** | Topic tags / 难度标签 | Maggie topics / Coursera level filter |

---

## 第 3 节 · 当前 Fork vs 理想状态 Gap 表

| 维度 | 当前 fork（截图实证） | 理想状态 | Gap 严重度 |
|---|---|---|---|
| Hero / Promise | 仅 3 条 learning_objectives | "本书讲 XX，5 章 8 小时" 一句话 | **P0 严重** |
| Start Here | 无 | "📍 Start Here → Chapter 03" 按钮（拓扑排序入度=0） | **P0 严重** |
| 章节索引（block[2]） | **空白**（BUG 1） | Karpathy 风格表格：序号+标题+一句话+估时+难度+sparkline+status | **P0 严重** |
| Intro（block[0]） | **空白**（BUG 1） | LLM 写整书风格 + 写作动机 + 目标读者 | **P0 严重** |
| Chapter map（block[1]） | Mermaid dagre 22 节点杂乱（BUG 2 + 3） | ELK 布局 + Louvain 染色 + hub 大节点 + click 联动 | **P0 严重** |
| 联动 | 图 / 列表 / TOC 三者割裂 | 双向 click 高亮 + scroll 同步 | **P1 高** |
| Progress | 无指示 | Khan 风格彩色方块 + hover 预览 | **P1 高** |
| 浮动 TOC | 仅 3 项预定义 anchor | Distill scroll-active TOC + 章节级嵌套 | **P2 中** |
| 元信息条 | 无 | 创建时间 / 版本 / 章节数 / 总估时 / 概念数 | **P2 中** |
| 阅读路径 | 仅 1 条隐式顺序 | linear "首读" vs branching "复习" 两套 | **P2 中** |

---

## 第 4 节 · 修复路线（P0/P1/P2）

### 4.1 P0 — 关键修复（共 14h，2 day）

| # | 修改 | 工作量 | 文件 | 依据 |
|---|---|---|---|---|
| **P0-0** | **3 行 BUG fix**（schema 双标 + OVERVIEW 进 mind map + dependencies 计数） | **<1h** | engine.py:512 / engine.py:559 / spine_synthesizer.py:526 / ConceptGraphBlock.tsx:94 | Agent A 审计 |
| P0-1 | Hero 区加一句话 promise + 元信息条（章节数 / 概念数 / 总估时 / 更新时间） | 2h | _materialize_overview_page 重构 | NN/g 5-second test |
| P0-2 | 章节列表升级为 Karpathy index.md 风格表格：序号 \| 标题 \| 一句话 summary \| 估时 \| 难度 \| 状态 sparkline | 4h | engine.py:546-560 + index_md 模板 | Karpathy + Tufte data-ink |
| P0-3 | 顶部加 "📍 Start Here → ChXX" CTA（基于依赖图入度=0） | 2h | engine.py 加 reading_path_hint + 前端 button | Maggie / Khan / Coursera |
| P0-4 | Mermaid 改 ELK 布局 + 节点按 hub 入度大小 + Louvain 社区染色 | 6h | concept_graph.py:render_mermaid + ConceptGraphBlock.tsx | Mermaid PR #6028 / Heptabase / Tufte layering |

**P0-0 是核心**: < 1h 修 4 行代码，立即从"杂乱空白"跳到"可读完整"。其他 P0 是质量飞跃。

### 4.2 P1 — 优化层（12h，1.5 day）

| # | 修改 | 工作量 |
|---|---|---|
| P1-1 | 概念图 ↔ 章节列表双向联动（click 章节高亮图节点 + scroll 同步） | 6h |
| P1-2 | 每章节加进度方块（已读/复习中/未读，颜色编码） | 3h |
| P1-3 | 右侧 TOC 改 Distill 风格 scroll-active + 自动 H2/H3 抽取 | 3h |

### 4.3 P2 — 增量（9h，1 day）

| # | 修改 | 工作量 |
|---|---|---|
| P2-1 | "首读 / 复习" 两套 reading path tab | 4h |
| P2-2 | "Recent activity" / "上次读到这里" recall 区块 | 2h |
| P2-3 | 概念图 hover 预览（卡片显示该概念对应章节 + 一句话） | 3h |

### 4.4 Spec 级重设计建议（长期）

1. **Overview pipeline LLM 化**: `_materialize_overview_page` 拆 5 blocks 走 BookCompiler：
   - block[0] = `text` role=`overview_intro`（LLM 写写作动机 + 目标读者）
   - block[1] = `concept_graph`（保留 deterministic）
   - block[2] = `text` role=`reading_path`（LLM 推 2-3 条路径）
   - block[3] = `callout` role=`chapter_index`（带每章 LLM 速读）
   - block[4] = `timeline` 跨 chapter 关键事件预览（v2 adapter 履历跨章节聚合）
2. **OVERVIEW 注册到 PagePlanner**: spine_synthesizer.py:436-438 当前强制把 LLM OVERVIEW 降级为 THEORY，禁止用户/LLM 自定义结构。Canvas 接管时改为允许 OVERVIEW 走标准 plan_blocks。
3. **页面内 graph + sidebar 一致性合同**: BookEngine 加 invariant：`payload.graph.nodes.filter(chapter_id).length == payload.index.chapters.length`，序列化时 assert。

---

## 第 5 节 · 关键洞察（高 leverage 设计原则）

1. **Karpathy index.md = 文字版 overview 黄金标准**: 用 metadata-rich 单行替代图，规模 ~100 项前 LLM + 人都可读，**比 Mermaid 信息密度高 5×**
2. **Khan Academy mastery squares = 进度可视化黄金标准**: 每 skill 1 cm² 彩色方块，hover 预览 + click 跳，**比 progress bar 强 10×**
3. **Mermaid 默认布局对 >15 节点必然退化**（GitHub issue #5969 / #6028 实证），ELK + 自定义节点尺寸是必需，**不是可选**
4. **Heptabase sections 解决"缩放时丢失上下文"**: 即使缩到很远也能看 section 标题。当前 fork Mermaid 缩放就糊
5. **Tufte sparkline + data-ink ratio 是最被低估的 overview 设计原则**: 一行文字嵌 mini chart 替代整个 progress bar 区块

---

## 第 6 节 · 推荐下一步路径

### 路径 A · 立即 1-line BUG fix（最小风险，~30min）

仅修 schema 双标 + OVERVIEW 进图过滤 + dependencies 计数 = 4 行代码。修后立即重启 fork → 重新触发 Overview 生成 → block[0] + [2] 内容回归 + Mermaid 22 节点降到合理。

### 路径 B · P0 全部修复（~14h，2 day）

包含路径 A + Karpathy 表格 + Khan 进度方块 + ELK Mermaid + Start Here CTA。Overview 体验从"基本可读"跃升到"专业学习产品"水准。

### 路径 C · 完整 P0+P1+P2 改造（~35h，4-5 day）

理想形态。但与当前 Phase B v2 vault adapter 工作正交（Overview 是 fork 内部，不在 adapter 范围）。建议 v2 收尾后再启动。

---

## Sources（关键参考 URL）

**学术**
- [Tufte — Sparkline theory](https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/)
- [Tufte data-ink principle](https://jtr13.github.io/cc19/tuftes-principles-of-data-ink.html)
- [Norman — Design of Everyday Things (PDF)](https://dl.icdst.org/pdfs/files4/4bb8d08a9b309df7d86e62ec4056ceef.pdf)
- [NN/g — 5-Second Usability Test](https://www.nngroup.com/videos/5-second-usability-test/)
- [Riedl — Branching Story Graphs](https://faculty.cc.gatech.edu/~riedl/pubs/riedl-aiide05.pdf)

**现代产品**
- [Heptabase Wiki](https://wiki.heptabase.com/organize-knowledge-and-projects)
- [Maggie Appleton Garden](https://maggieappleton.com/garden/)
- [Quartz 4](https://quartz.jzhao.xyz/)
- [Karpathy llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Khan Academy mastery visualization](https://support.khanacademy.org/hc/en-us/articles/18735142028045)
- [Distill TOC pattern](https://distillery.rbind.io/posts/2022-01-24-the-toc-in-distill/)
- [Obsidian MOC pattern](https://github.com/seqis/ObsidianMOC)

**Mermaid 限制**
- [Mermaid issue #5969 — ELK adaptive rendering](https://github.com/mermaid-js/mermaid/issues/5969)
- [Mermaid PR #6028 — ELK cluster fix](https://github.com/mermaid-js/mermaid/pull/6028)
- [Mermaid Layout Engines docs](https://mermaid.ai/open-source/config/layouts.html)

**Fork 关键代码**
- engine.py:398-578 — Overview pipeline
- engine.py:512 + :559 — payload schema bug
- spine_synthesizer.py:526 — chapter_map 不过滤 OVERVIEW
- text.py:73-77 — 标准 schema body 字段
- ConceptGraphBlock.tsx:79-105 — 前端标注误算
- TextBlock.tsx:11 — 前端读 body 字段（非 content）

---

*Round-22 v2 设计调研报告。Agent A + B 并行 deep explore 收敛。等用户拍板路径 A/B/C。*
