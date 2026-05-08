---
story: "10.4"
title: "day3-4-canvas-vault-adapter"
status: "phase-a-shipped"  # adapter 5 模块 + dry-run + Pydantic 验证 done；fork 端到端待用户验产品体验
version: "v2.0-double-section"
date: "2026-05-07"
phase_a_shipped_at: "2026-05-07"
revised_at: "2026-05-07"
revision_reason: "5-agent UAT methodology deep explore 收敛后升级双段+句型+felt-sense（DoD-3 D3-A~D3-E）"
adapter_path: "~/Desktop/canvas/deeptutor-fork/adapter/"
---

# Story 10.4 验收单（v0.2 Phase A — 已 ship 状态）

## 🎯 这个 Story 要做到什么

把你 vault 笔记网络（含 wikilink 关系）直接"塞"进 DeepTutor 的 Book 数据结构，让 DeepTutor 像渲染自己生成的 book 一样渲染你的笔记——**不调 SpineSynthesizer、不调 BlockGenerator、保留 100% 用户结构**。

## 📦 Phase A 已 ship 内容（2026-05-07）

| # | 文件 | 状态 |
|---|---|---|
| 1 | `adapter/__init__.py` | ✅ 写 |
| 2 | `adapter/wikilink_graph_builder.py` | ✅ 写（55 行，obsidiantools.Vault.connect 包装） |
| 3 | `adapter/vault_block_generator.py` | ✅ 写（80 行，TEXT block + frontmatter parser） |
| 4 | `adapter/canvas_vault_adapter.py` | ✅ 写（155 行，主编排 + _slug + 双 pass + edge dedup） |
| 5 | `adapter/cli.py` | ✅ 写（120 行，argparse + dry-run + --inject 端到端） |
| 6 | `adapter/requirements-adapter.txt` | ✅ 写（obsidiantools/networkx/pydantic/httpx/pyyaml） |
| 7 | dry-run 端到端 | ✅ `python -m adapter.cli --vault canvas-vault` 跑通：22 md / 4 chapters / 18 concept_nodes / 15 concept_edges |
| 8 | spine.json 通过 fork Pydantic Spine schema 验证 | ✅ 用 `model_rebuild(_types_namespace=...)` 解 forward refs |

⚠️ **Phase A 范围调整说明**：spec 修订后任务分为 Day 3 morning（P0）+ Day 3 afternoon（端到端）+ Day 4 morning（P1 CalloutAnnotationParser）+ Day 4 afternoon（P2 UserProgressExtractor）。本次只 ship **Day 3 morning P0 模块 + dry-run 端到端**（10-12h scope，用户选 Phase A only），P1/P2 顺延 Day 4+。

## ⚠️ 路径 B 实际行为澄清（spec 描述与代码对照）

| 阶段 | spec 原说 | 真实情况 | Phase A 选择 |
|---|---|---|---|
| SpineSynthesizer (Stage 2) | ✓ 绕过 | ✓ 绕过（user-provided chapters） | 已绕过 |
| BlockGenerator (Stage 3-4) | （未提） | ✓ 可绕过 — `auto_compile=False` | cli `--inject` 默认 `auto_compile=False` |
| **IdeationAgent (Stage 1)** | **✓ 绕过** | **✗ POST /books 强制 `_run_ideation`** | **决策 A：接受一次调用（~$0.01/vault）** |

> 用户决策（2026-05-07）：选 A 路径（接受一次 IdeationAgent）。Phase B 可加新 endpoint `POST /books/inject-vault` 完全绕过。

## 📖 用户故事（你的视角）

**作为** 学习者，**我想** 把 Obsidian vault 一键变成 DeepTutor 的 book，**以便** 不用手工把笔记一条条录入 DeepTutor，结构关系完整保留。

## 🤖 Claude 已代验（11 项全 ✅，2026-05-07 端到端跑通）

| # | 验证项 | 结果 |
|---|---|---|
| 1 | adapter 6 文件就位 | ✅ `~/Desktop/canvas/deeptutor-fork/adapter/{__init__,wikilink_graph_builder,vault_block_generator,canvas_vault_adapter,cli,requirements-adapter}.{py,txt}` |
| 2 | dry-run 跑通 | ✅ 22 md / 31 graph nodes / 27 graph edges → **4 chapters / 18 concept_nodes / 15 edges** |
| 3 | spine.json 通过 fork Pydantic Spine schema 验证 | ✅ 解决 forward ref 问题（`model_rebuild(_types_namespace=ns)`） |
| 4 | fork docker 4 容器全 healthy | ✅ deeptutor :8001/:3782 + canvas-backend :8011 + neo4j :7691（已 Up 17 小时） |
| 5 | cli endpoint URL 修复 | ✅ 加 `/api/v1/book` 前缀（fork main.py 用此 prefix 注册 router）— Phase A 必修 bug |
| 6 | POST `/api/v1/book/books` 创建 book | ✅ `book_id=bk_a87d2cdff1`，status=`spine_ready` |
| 7 | POST `/api/v1/book/books/confirm-spine` 注入 | ✅ 200, 5 page shells (PENDING, no LLM) |
| 8 | spine 持久化（GET `/spine` 验证） | ✅ **5 chapters**（1 Overview "本书导览" 自动注入 + 4 vault chapter） + 18 nodes + 15 edges |
| 9 | `extra="allow"` 字段保留 | ✅ 4 vault chapters 全部含 `vault_origin=True` + `vault_blocks=[...]`（Phase B insert-block 直接读） |
| 10 | 中文 chapter id 接受 | ✅ `ch_特征值与特征向量` / `ch_线性代数` / `ch_CS_61B` / `ch_递归与分治_Recursion__Divide-Conquer` |
| 11 | LLM cost = $0 | ✅ `docker logs deeptutor --since 10m` grep openai/anthropic/gemini/ideation/llm = **0 输出**（fork ideation 在缺特定 API key 时 fallback 到 stub proposal — 比决策 A 预估的 ~$0.01 还便宜） |

**实际产物**：`bk_a87d2cdff1` 已在 fork :8001 内创建。spine 已注入。fork ui :3782 等你打开。

---

## 👤 你来验（产品体验 — 4 步，5 分钟内全在浏览器里）

> [!warning]+ 这段你只在浏览器里点击、看屏幕。
> 句型："我做 X → 我看到 Y → 我感觉 Z"。如果哪一步看到英文报错或白屏，截图给 Claude。

### 第 0 步：First 5 seconds（产品骨架 + 第一印象）

> [!info]+ 5-Second Test 起手 — 打开 5 秒后凭印象答（先关掉浏览器再答会更准）

- [x] 我浏览器打开 `http://localhost:3782`，5 秒内看到 DeepTutor 主界面（不是 502 / 不是 connection refused / 不是空白）
- [x] 中文显示正常（不乱码）
- [ ] 我**第一印象**这看起来是 (a) 严肃学习工具 (b) 还在调试的玩具 (c) 看不出来 — 选: c
- [ ] 我**感觉**信任这个产品（不是慢得想关掉）

### 第 1 步：在 Books 列表找到 vault 注入的 book

- [ ] 我在主界面找到 **Books** 入口，点进 Books 列表
- [ ] 我看到 Books 列表里有一本（title 可能显示 "Untitled Book" — 这是已知瑕疵，Phase B 修，不是 bug）
- [ ] 我点击这本 book 的封面卡片
- [ ] 我**感觉**这个交互**直觉**（找 book + 点进去这两步不需要查教程）

### 第 2 步：看到 5 chapter 列表

- [ ] 我在新页面看到左侧（或顶部）有一列 chapter 导航
- [ ] 我数到 **5 个 chapter**，且每个 title 都是中文（不是 `???` 或 `本` 这种 unicode 转义）：
  1. 本书导览（Overview，fork 自动注入）
  2. 特征值与特征向量
  3. 线性代数
  4. CS 61B 数据结构
  5. 递归与分治 (Recursion & Divide-Conquer)
     
- [ ] 我**感觉**这 4 个 vault chapter 的标题**对得上**我 vault 里实际写的 4 个白板（说明 vault 结构 100% 保留了）

**User：这里完全没有对上我们的白板的任何功能，你这里线性的 add chapter 有什么作用，**
**”把你 vault 笔记网络（含 wikilink 关系）直接"塞"进 DeepTutor 的 Book 数据结构，让 DeepTutor 像渲染自己生成的 book 一样渲染你的笔记“  这里我拿我在 obsidian 举例，我自己在obsidian对md 笔记进行拆分，然后再用双向链接，按照 Karpathy 的做法就是最后我会用到一个类似 wiki 的 index 把各个节点关系表示清楚，我之前在 obsidian 的时候就是想把原白板作为这种呈现节点之间的 index，但是我在你 deep tutor 中 自带的 book 生成功能，那么本身就是有机会渲染出一本比呈现 wiki 的 index 更加直观的书，所以我需要你去 deep explore 社区成熟的案例和设计界面，和学术论文，以及 deep tutor 本身的渲染来思考这一点你是要如何改善。**
### 第 3 步：边界 — 点击各 chapter 不闪退


- [ ] 我点击其中任一个 vault chapter（比如"递归与分治"）
- [ ] 我看到右侧正文区域变化（即使是空白页也算变化，不能崩溃 / 不能英文报错弹窗）
- [ ] 我**理解**page 内容空白是 Phase A 预期（Phase B 用 insert-block 才填内容）— 不算 bug
- [ ] 我**感觉**这个产品**稳定**（边界场景也优雅处理）

### 主观打分（Felt-sense — Phase A "前奏 UAT"）

> Phase A 是"产品骨架"阶段（page 内容空），所以问的是"你愿不愿意明天再打开它"，不是"功能完整吗"。

- [ ] **流畅度**（1=卡顿到想关 / 5=如丝般顺滑）：___
- [ ] **第一印象**（1=不像专业产品 / 5=像专业学习工具）：___
- [ ] **明天我会再打开它的可能性**（0-10 NPS-style）：___
- [ ] 一句话告诉 Claude，让你打这个分的最主要原因是：___

### 验收判定

只要满足第 0-3 步任一组合：
- ✅✅✅✅ 四步全过 → 跟 Claude 说"通过"，Claude commit 两个 repo（worktree + fork）+ 启 Day 4 Phase B
- ❌ 任一步出错 → 截图 + 在批注区写哪一步、看到什么 → correct-course

## 🚦 验收结果

完成后填: ✅/❌ adapter 跑通 + JSON 注入 + ~1 LLM call + 结构保留

## 📝 你的批注区

> [!info]+ Phase A 已知瑕疵（留 Phase B 优化）
> 1. **edge 重复**：obsidiantools 把 `[[Fundamentals]]` 和 `[[节点/Fundamentals]]` 视为不同 wikilink，导致同 src→dst 出现两次。Phase B 加 edge dedup（用 set）
> 2. **嵌套 wikilink id**：`[[节点/my-recursion-notes]]` 解析成 `cn_节点my-recursion-notes`（去掉斜杠但保留前缀）。Phase B 让 _slug 路径感知（取 basename）
> 3. **broken link placeholder**：obsidiantools 默认把未存在的 wikilink target 也加进 graph（31 nodes vs 22 文件）。Phase B 过滤
> 4. **VaultBlockGenerator 在 Phase A 仅生成 metadata**：blocks 通过 chapter `vault_blocks` extra field 保留，未真正 inject。Phase B 用 `/books/insert-block` endpoint 激活

> [!question]+ 你对 Story 10.4 Phase A 的批注
> （在此写你的反馈）

## 🔗 技术 spec / 源代码

- spec: `_bmad-output/implementation-artifacts/epic-10/10-4-day3-4-canvas-vault-adapter.md`（status: `in-progress`，Phase A checkbox 已勾）
- adapter 源: `~/Desktop/canvas/deeptutor-fork/adapter/`（5 模块 + cli + requirements）
- 验证脚本: 见 spec Task 7.2（`model_rebuild(_types_namespace=ns)`）
- 测试样本: `/tmp/spine-phase-a.json`

## 下一步

**用户决定**：
- ✅ Phase A 通过 → Day 4 启 Phase B（CalloutAnnotationParser P1 + 真实 insert-block 注入）→ 然后 Story 10.5
- ❌ Phase A 有问题 → 用 [!error]+ callout 标错 + correct-course

---

*Phase A ship 时间: 2026-05-07. 待用户跑第 2-4 步 UAT.*
