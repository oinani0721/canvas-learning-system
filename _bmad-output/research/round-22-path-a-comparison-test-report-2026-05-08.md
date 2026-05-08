---
title: "DeepTutor 路径 A 完整 Pipeline 审计 + 对照测试操作指南"
type: "design-report-and-comparison-test"
date: "2026-05-08"
trigger: "用户反馈 v2 adapter book 内容质量低，要求用 1 份原板 KB 跑路径 A 对照"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
agents_used: 3
sources_count: 50+
related_files:
  - "deeptutor-fork/deeptutor/book/engine.py:582-645"
  - "deeptutor-fork/deeptutor/book/agents/source_explorer.py:267-343"
  - "deeptutor-fork/deeptutor/book/agents/spine_synthesizer.py"
  - "deeptutor-fork/adapter/canvas_vault_adapter.py:131,164,168,186"
critical_findings:
  - "v2 adapter vault_blocks 是 DEAD-WRITE bug — page.blocks 永远是 [] BlockGenerator 走 LLM 自由发挥"
  - "EMBEDDING_API_KEY=sk-xxx 占位符 — KB RAG 全部失败"
  - "chapter.summary=body[:500] 含 frontmatter+dataviewjs 噪音污染下游 LLM prompt"
---

# Round-22 v2 路径 A 完整 Pipeline 审计 + 对照测试操作指南

> **触发**: 用户 2026-05-08 反馈 `bk_869daf0697` 章节索引和正文内容大量噪音（vault md frontmatter / dataviewjs / round-11 元 docs 被展开为章节索引）。要求用 1 份原板 KB 跑 fork 原生路径 A 对照看"DeepTutor 自己的正确路径"。
>
> **方法**: 3 agent 并行 deep explore — Agent A 审计 fork 路径 A 完整 pipeline；Agent B 写用户对照测试操作指南；Agent C 调研社区真实路径 A book 案例。

## Executive Summary

1. **致命发现**: v2 adapter 的 `chapter.vault_blocks` extra 字段是 **DEAD-WRITE bug** — `engine.py:617-625` 创建 Page 时 `blocks=[]` 写死，`compiler.py:315` 见空就走 SectionArchitect LLM 自由生成。adapter 的 TEXT/TIMELINE block **从未到达用户**。这解释了你看到的"内容没有价值" — 实际是 LLM 在用污染的 chapter.summary 自由发挥，没碰到 vault md 内容
2. **embedding 占位阻塞路径 A**: `EMBEDDING_API_KEY=sk-xxx` 占位符让 SourceExplorer 的 RAG 检索全部 401 失败 → ExplorationReport.chunks 空 → SpineSynthesizer 无 grounding。即使你切到路径 A 跑 KB，没真 embedding 也跑不出有价值的 book
3. **章节索引污染源**: `chapter.summary = body[:500]` raw preview 含 frontmatter + dataviewjs 等元 docs 噪音 → `_materialize_overview_page` 直接展示 (`engine.py:551`) + 注入 SectionArchitect prompt (`page_planner.py:243`) 双重污染
4. **路径 A 设计意图实证**: 3-8 章 × 每章 ≥1 个 1500-2500 字 section × 5-10 block (≥4 type) × FlashCards 3-8 张 × Quiz 1-8 题 × 必含 RAG citation。整本 ~10K-32K 字
5. **修复优先级**: ① 改 EMBED 切 Ollama bge-m3（你已装）→ KB RAG 通；② 跑路径 A 对照测试看 fork 设计意图；③ 修 v2 adapter DEAD-WRITE bug + chapter.summary 噪音清洗

---

## 第 1 节 · 路径 A 完整 Pipeline 数据流（Agent A）

### 1.1 5 阶段链路

```
POST /api/v1/book/books { user_intent, knowledge_bases[], language }
  ↓
STAGE 1 · build_book_inputs (inputs.py:308)
  4-source fusion: user_intent / chat_history / notebook_refs / question_categories
  → IdeationContext.render()
  ↓
STAGE 1.5 · IdeationAgent (1 LLM call, JSON)
  prompts/zh/ideation_agent.yaml — 限 estimated_chapters ∈ [3,8]
  → BookProposal { title, description, scope, target_level, estimated_chapters, rationale }
  ◄── 用户 confirm point
  ↓
STAGE 2 · SourceExplorer (engine.py:312-322)
  (a) _design_queries LLM #1 → 4-8 RAG 查询
  (b) For each (kb × query): rag_search() → SourceChunk[] (parallel asyncio.gather)
      ⚠️ EMBED API 必须可用！sk-xxx 占位 = 全部 401 失败 = chunks 空
  (c) + chat/notebook chunks (no RAG)
  (d) _summarise LLM #2 → summary + candidate_concepts + notes
  → ExplorationReport (持久化供后续所有 BlockGenerator 复用)
  ↓
STAGE 2.5 · SpineSynthesizer (1-3 LLM calls)
  Round 1: _draft → {concept_graph, chapters} (单 JSON 严格 schema)
  Round 2: _critique → {issues, verdict}
  Round 3: _revise (only if verdict='revise')
  Post-process: _remove_cycles + _topological_sort + _build_chapter_map
  → Spine {chapters[], concept_graph}
  ◄── 用户 confirm point
  ↓
STAGE 3 · confirm_spine (engine.py:582-645)
  - _ensure_overview_chapter (注入 ch 0)
  - For each chapter: create empty Page shell, blocks=[]
  - _materialize_overview_page (deterministic, no LLM)
  - _enqueue_pending_pages → asyncio Queue
  ↓
STAGE 4 · BookCompiler.compile_page (per page worker)
  (a) _plan_if_needed → SectionArchitect LLM
      → page.blocks = [Block shells of 5-10 BlockType]
  (b) For each block: BlockGenerator.generate(ctx)
      Section: 2-pass outline + parallel subsection fill
      其他 block: 单 LLM call grounded with cached ExplorationReport.chunks
  (c) attach_bridge_text between blocks
  ↓
Page.status = READY → frontend render
```

### 1.2 v2 adapter (路径 B) vs 路径 A 10 维对比

| # | 维度 | v2 adapter (路径 B) | 路径 A | 质量影响 |
|---|---|---|---|---|
| 1 | chapter.title | vault 文件名 / `frontmatter.board_name` | LLM 从 ExplorationReport 抽 | A 由 LLM 提炼真主题 |
| 2 | **chapter.summary** | `body[:500]` raw — **frontmatter+dataviewjs 噪音** | LLM 1-2 句总结 | **B 信息密度极低** |
| 3 | learning_objectives | **永远空** `[]` | LLM 生成 2-6 条 | B 失去章节学习引导 |
| 4 | content_type | 写死 `"concept"` | LLM 选 5 类 | B 全 CONCEPT 模板，对长 vault 笔记太薄 |
| 5 | **page.blocks** | `vault_blocks` extra **DEAD-WRITE** | SectionArchitect 选 5-10 BlockType + RAG 填 | **B 致命 bug**：vault 内容**完全不进 page** |
| 6 | source_anchors | 1 条手填 manual | LLM draft + SectionGenerator 自动补 | B 失去 RAG grounding |
| 7 | concept_graph.nodes | vault 节点 1:1 映射 | LLM 从 candidate_concepts 抽取重组 | A 抽象主题 / B 具体节点名 |
| 8 | concept_graph.edges | derived-from + wikilink | LLM 推断 + cycle 检测 | B 真实学习史 / A 逻辑依赖 |
| 9 | exploration_summary | 硬编码 stats | LLM 4-8 句反复主题 + 证据强弱 | B 没法 ground 后续 BlockGenerator |
| 10 | TIMELINE block | adapter 直接填 ## Recent Activity | 由 SectionArchitect 选 + LLM 生成 | B 真实履历（但无法到达 page）/ A 编造但符合内容 |

### 1.3 v2 adapter 三大根因

**根因 1 · vault_blocks DEAD-WRITE（最致命）**

`canvas_vault_adapter.py:168, 186` adapter 把 TEXT/TIMELINE block 塞到 `chapter.vault_blocks` extra 字段，但：
- `engine.py:617-625` 创建 Page 时 `blocks=[]` 写死
- `compiler.py:315` 看到空 blocks 就走 SectionArchitect 重新规划
- 用户 `auto_compile=True` 时实际走的是路径 A 的 SectionArchitect！
- adapter 的 vault md 内容**永远到不了 page**

**这是结构性 bug — v2 设计假设 vault_blocks 会被 fork 读取，但 fork 后端没这条逻辑**。

**根因 2 · chapter.summary 双重污染**

`canvas_vault_adapter.py:131, 164` `preview = body[:500]`，前 500 字含：
- frontmatter `---\nyaml...\n---\n`
- dataviewjs 代码块
- callout 块标记 `> [!info]+`
- tag list

这 500 字被注入：
- (a) `_materialize_overview_page:551` 直接展示在章节索引
- (b) `page_planner.py:243` 作为 chapter_summary slot 喂给 SectionArchitect
- (c) `section.py:18` 作为风格参考喂给 SectionGenerator

**三处污染下游 LLM 全都看到 vault 元 docs 噪音**，所以 Opus 4.7 生成的 SectionBlock 也会被影响。

**根因 3 · learning_objectives + content_type 全空/全 concept**

`canvas_vault_adapter.py:158, 160` content_type 写死 concept、learning_objectives=[]。CONCEPT 模板是 `definition→mindmap→examples→flash_cards→pitfall→comparison→quiz` (`page_planner.py:147-156`)，对所有白板套同一套模板，不分 theory/derivation/history/practice。

---

## 第 2 节 · 对照测试操作指南（Agent B）

### 2.1 阻塞项：EMBEDDING_API_KEY 占位符

当前 `/Users/Heishing/Desktop/canvas/deeptutor-fork/.env:48` 写 `EMBEDDING_API_KEY=sk-xxx` 占位符 → 上传 KB 时一定 401 失败。

**推荐方案**: 切到本地 Ollama bge-m3（你已装，`ollama list` 显示 `bge-m3:latest`）

`.env` 改动 diff:
```diff
-EMBEDDING_BINDING=openai
-EMBEDDING_MODEL=text-embedding-3-large
-EMBEDDING_API_KEY=sk-xxx
-EMBEDDING_HOST=https://api.openai.com/v1/embeddings
-EMBEDDING_DIMENSION=
+EMBEDDING_BINDING=ollama
+EMBEDDING_MODEL=bge-m3
+EMBEDDING_API_KEY=
+EMBEDDING_HOST=http://host.docker.internal:11434/api/embed
+EMBEDDING_DIMENSION=1024
+EMBEDDING_SEND_DIMENSIONS=false
```

改完: `docker compose up -d --build deeptutor`（fork 是 build-baked image，restart 不重读）

### 2.2 创建对照 book step-by-step

| # | 操作 | 预期 |
|---|---|---|
| 1 | 浏览器 `http://localhost:3782` | DeepTutor workspace |
| 2 | 左侧 Sidebar 点 **Knowledge** | 跳到 /knowledge |
| 3 | 点 "+ Create knowledge base" | 弹出 CreateKbModal |
| 4 | name=`karpathy-makemore`, provider=`llamaindex`, 拖入 PDF/MD 文件 | FileDropZone 接受 |
| 5 | 点 Create | KB 后台 embedding 索引 |
| 6 | 等 KbStatusBadge 从 indexing → ready (~1-3 min for bge-m3) | 单 5MB PDF |
| 7 | 左侧 Sidebar 点 **Book** | 跳到 /book |
| 8 | 点 "+ New Book" | 进入 BookCreator |
| 9 | 填 Learning intent + 勾选 KB + Language=zh | 见下方填写参考 |
| 10 | 点 Generate proposal | IdeationAgent ~10-30s 出 BookProposal |
| 11 | 看 Proposal 满意点 Confirm proposal | SpineSynthesizer ~30-90s 出 Spine |
| 12 | 看 Spine（chapters + concept_graph）满意点 Confirm spine | BlockGenerator 异步渲染 5-15 min |

**Learning intent 填写参考**:
```
我想系统理解 makemore lecture 的字符级语言模型推导，
从 bigram 频率统计、neural network 重写、到 MLP，
需要每章配 quiz + 推导 + 代码片段。
```

### 2.3 推荐 KB（3 选项）

**强烈推荐选项 C** — Karpathy makemore 5 lecture markdown：
```bash
mkdir -p /tmp/makemore-kb && cd /tmp/makemore-kb
for i in 1 2 3 4 5; do
  curl -L -o "makemore_part${i}.ipynb" \
    "https://raw.githubusercontent.com/karpathy/nn-zero-to-hero/master/lectures/makemore/makemore_part${i}_$(case $i in 1) echo bigrams;; 2) echo mlp;; 3) echo bn;; 4) echo backprop;; 5) echo wavenet;; esac).ipynb"
done
pip install nbconvert && jupyter nbconvert --to markdown *.ipynb
# 上传 *.md（5 份，~200KB 总）
```

理由：5 lecture 自带渐进式知识结构（bigram → MLP → batchnorm → backprop → wavenet），SpineSynthesizer 一定切出 5 章，验证 IdeationAgent 逻辑。教科书级内容质量，与 vault-driven 强对照。

选项 A: 你自己 CS 61B 课件 PDF（与 v2 adapter book 主题对齐，对照度最高）
选项 B: vault md 合并成 1 份 markdown（同源数据验证路径 A 跑同样数据效果）

---

## 第 3 节 · 社区案例 + 路径 A 设计意图（Agent C）

### 3.1 官方实证

**HKUDS/DeepTutor README** 仅 3 张 book 截图：Library / Reader / Animation。
**v1.2.0 release notes** 定义 5 阶段管道 + Web UI 含 BookCreator wizard / SpineEditor 拖拽 / PageReader / BookProgressTimeline / BookChatPanel / BookHealthBanner。
**arXiv 2604.26962** 强调 "every claim with citation"。
**官方 docs 站**: hkuds.github.io/DeepTutor

### 3.2 社区实证（GitHub Issues）

- **Issue #369** 中文用户 14 章 book，6 张截图：Quick Check 选项缺失 / 代码无换行 / quiz 翻译漏题 / code+flash_cards block failed
- **Issue #372** 英文用户：code/flash_cards block "LLM did not return any" 错误
- **Issue #414** DeepSeek + bge-m3 实测 3 张截图 — DeepSeek thinking mode 输出残留 ```json fences 导致 block 失败
- **Issue #430** v1.3.1+ UX 痛点清单（已知未修）
- **Issue #380** 22k stars 用户 vs NotebookLM 对比抱怨

**关键事实**: OpenAI 系列稳定 / DeepSeek thinking mode 不稳定。**用 OpenAI gpt-4o-mini 或 Claude Haiku/Opus 4.7（你的 Meridian 已通）跑路径 A 最稳**。

### 3.3 路径 A "正常" book 内容深度（从 prompts/yaml 反推）

| 维度 | 官方设计 |
|---|---|
| 章节数 | **3-8 章**（estimated_chapters） |
| 每页 block 数 | **5-10**，强制 interleave 不同 type，至少 1 个 SECTION |
| SECTION block 字数 | **1500-2500 字**，3-5 个 H3 subsections 各 280-360 字 |
| FlashCards 数 | 3-8 张 / 章 |
| Quiz 题数 | 1-8 题 / 章 |
| 总字数 / book | **~10,000 - 32,000 字** + 3-8 figure + 5-15 quiz + 10-30 flashcard |
| Citation | UI 中 page 含 source citation 回 PDF |

### 3.4 对照测试 10 项验收锚点

| # | 锚点 | 预期 | 不及格信号 |
|---|---|---|---|
| 1 | 章节数 | 3-8 章 | <3 或 >10 |
| 2 | 每章必含 5 字段 | title + objectives (3-5) + content_type + summary + source_anchors | 字段缺失 |
| 3 | ConceptGraph | 8-20 nodes，边类型有 depends_on / extends / related | 0 节点或全 related |
| 4 | SectionBlock 字数 | 每章 ≥1 section, 1500-2500 字 | <500 字 |
| 5 | Block interleave | 5-10 / page, ≥4 不同 type | 全 text/callout |
| 6 | FlashCards | 3-8 张 / 章 | "block failed" |
| 7 | Quiz | 1-8 题 / 章 完整字段 | options 缺失 |
| 8 | Citation | UI 含 source 回 PDF | 全无 |
| 9 | 进度 Timeline | BookProgressTimeline 实时 5 阶段 | 不展示 |
| 10 | Page-level chat | BookChatPanel 注入 page 上下文 | chat 不知 page |

---

## 第 4 节 · 综合判断与下一步建议

### 4.1 用户当前症状的真相

你看到的"内容没有价值"= **三层叠加失效**：
1. v2 adapter 注入的 vault TEXT/TIMELINE block 实际**没用到**（DEAD-WRITE）
2. fork 后端实际跑的是 SectionArchitect LLM **自由生成**
3. SectionArchitect 用的 chapter.summary 是**含元 docs 噪音的 vault md preview**

所以 Opus 4.7 在用"被污染的章节摘要 + 没有 KB grounding"自由发挥，写出来的就是空泛章节文字。

### 4.2 对照测试的真实价值

跑路径 A 1 份 PDF 后，你会看到：
- **如果路径 A 出来质量好** → 证明 fork 设计意图正确，v2 adapter 三大根因（DEAD-WRITE + summary 污染 + content_type 单一）是修复方向
- **如果路径 A 出来质量也差** → 可能是 fork prompt 设计问题或 KB 太短，对照点更聚焦在"prompt + RAG grounding"上

### 4.3 推荐执行顺序

| 阶段 | 时长 | 内容 |
|---|---|---|
| **1. EMBED 切 Ollama** | 5 min（含 docker rebuild） | 改 .env 5 行 + docker compose up --build deeptutor |
| **2. 验证 embedding 通** | 1 min | curl test bge-m3 + fork health |
| **3. 准备 KB**（推荐 Karpathy 5 lecture） | 5 min | curl + nbconvert |
| **4. 跑路径 A 对照测试** | 10-20 min（含 BlockGenerator） | UI 上传 KB → New Book → IdeationAgent → Spine → 等 BlockGenerator |
| **5. 截图对比 v2 adapter book** | 10 min | 按 10 项验收锚点对比 |
| **6. 决定 v2 adapter 修复方向** | — | 基于对照结果选择修 DEAD-WRITE / 噪音清洗 / 完全重设计 |

总耗时 ~30-45 min（不含等 BlockGenerator 渲染时间）。

### 4.4 v2 adapter 后续修复建议（按 ROI）

| # | 修复 | 工作量 | 影响 |
|---|---|---|---|
| 修复 1 | chapter.summary 干净化（strip frontmatter + dataviewjs + tags） | 5 行 | 立即修章节索引噪音 |
| 修复 2 | chapter.summary LLM 化（每章调一次 LLM 出 100-200 字总结） | 10 行 | 对齐路径 A summary 质量 |
| 修复 3 | vault_blocks 真正生效（confirm_spine 检测 extra 直接用） | 30 行 fork 后端联动 | 修 DEAD-WRITE 致命 bug |
| 修复 4 | learning_objectives 从 vault frontmatter 提取 | 10 行 | 让 SectionArchitect 知道章节目标 |
| 修复 5 | content_type 智能选择（按 vault 内容判断） | 15 行 | 不全 CONCEPT 模板 |

---

## Sources

**Fork 关键代码**:
- engine.py:200-273（create_book）/ 312-322（SourceExplorer）/ 582-645（confirm_spine）/ 617-625（DEAD-WRITE 证据）
- agents/source_explorer.py:267-343（RAG 检索）/ 280（rag_search 调用）
- agents/spine_synthesizer.py:180-247（draft+critique+revise）
- agents/page_planner.py:233-348（5-10 block 选择）/ 74-156（fallback 模板）
- blocks/section.py:71-76（RAG grounding）/ 99-110（parallel subsection fill）
- compiler.py:88-190（compile_page）/ 305-344（_plan_if_needed）
- prompts/zh/{ideation_agent, source_explorer, spine_synthesizer, page_planner, section}.yaml

**v2 adapter bug 证据**:
- adapter/canvas_vault_adapter.py:131,164（chapter.summary preview）/ 168,186（vault_blocks DEAD-WRITE）/ 158,160（content_type 写死 + objectives 空）

**社区实证**:
- HKUDS/DeepTutor README + 3 张 book 截图
- Issue #369（中文 14 章实测，6 截图）
- Issue #372（block failed 截图）
- Issue #414（DeepSeek 不稳定 + bge-m3 实测）
- arXiv 2604.26962（"every claim with citation"）

**Embedding 配置**:
- .env:46-61（fork embedding 配置）
- services/embedding/.env.example:48-64（Ollama bge-m3 模板）

---

*Round-22 v2 路径 A 对照测试报告。3 agent 并行 deep explore 收敛。等用户决定执行顺序。*
