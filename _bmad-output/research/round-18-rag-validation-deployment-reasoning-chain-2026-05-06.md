---
title: Round 18 — RAG 黑盒打开 + DeepTutor 部署澄清 + 学习推导链 + 需求对齐 Deep Research
date: 2026-05-06
trigger: round-17 line 50 + line 703 用户批注（RAG 验证黑盒 + DeepTutor 部署形态 + 推导过程存 Graphiti + 需求对齐）
agents: 4 并行 Explore Agent (Sonnet)
related:
  - _bmad-output/research/round-17-deeptutor-technical-conflicts-deep-research-2026-05-06.md
  - _bmad-output/research/round-16-deeptutor-canvas-flow-deep-explore-2026-05-06.md
  - _bmad-output/research/round-14-graphiti-retrieval-deep-explore-2026-05-05.md
status: 调研报告，待用户审计后决定 Stage 1 启动
---

# Round 18 — RAG 黑盒打开 + DeepTutor 部署澄清 + 学习推导链 + 需求对齐 Deep Research

## 元信息

| 字段 | 值 |
|---|---|
| 触发 | `round-17:50`（RAG 黑盒痛点 + 需求对齐）+ `round-17:703`（DeepTutor 部署形态 + 推导过程存 Graphiti）|
| 调研方式 | 4 并行 Explore Agent（Sonnet model）按主题分工 |
| 范围 | RAG 测试覆盖盘点 / DeepTutor 5 种部署形态 / 推导链 4 数据模型 / 7 Stage 需求对齐 |
| 报告字数 | ≈12000 字 |
| 状态 | 初稿，待用户审计 6 个决策点 |

---

## 用户原始批注（round-17）

### 批注 1（line 50）— RAG 黑盒痛点 + 需求对齐

> 但是我们的后端这些 RAG 测试，没有实际验证，对我来说像一个黑盒，是一个未知的，不一定稳定成熟的框架，所以这是让我十分痛苦的地方。**我的 Canvas learning systeam RAG 设计，有什么基准测试可以证明是有效的，而不是无意义的构造**，而且这里的 DeepTutor 的 RAG 和 Canvas learning systeam 的 RAG 使用途径是不同的吧，**我们现在主要从需求对齐出发，DeepTutor 是否可以实现 Canvas learning systeam 所列出来的学习工作流**

### 批注 2（line 703）— DeepTutor 部署 + 学习推导过程

> 1，**Deeptutor 他难道不是可以阅读本地文件的 CIL 吗？你这里说它 web app，那么他能不能访问本地的文件**；2，最重要的**用户批注来进行拆分各个节点内容进行讨论，同时把我用双向链接构建的节点之间的联系，存在后端的 Graphiti 中，这样好让 agent 检测我时知道，我的整一个学习过程的逐步推导过程**

---

## 一句话核心结论

**4 个发现颠覆了 round-17 部分判断**：

1. **Canvas RAG 黑盒评分 3/10** — 测试骨架完整但核心闭环（golden dataset、RAGAS、端到端 recall）**未接线**，**1 天内修复 → 可提升到 7/10**
2. **DeepTutor 完全可以 CLI 读本地文件** — `deeptutor kb create canvas-vault --docs-dir ~/canvas-vault/节点/` 立即可用，**round-16 把它描述为 "Web app" 不准确**（Agent-Native 多形态系统，CLI-First）
3. **学习推导链在 Graphiti 中可表达** — 4 数据模型对比，**混合模型推荐**（EpisodeTask + ReasoningStep entity + DiscussionThread 三层），**约 7.5d 实施 → 直接攻克 round-14 残缺 #4（零同步）**
4. **DeepTutor 可实现 Canvas 工作流但有 7 条红线** — Canvas 后端已实现 + 370 个测试文件覆盖核心算法（BKT/FSRS 821 行专项测试），DeepTutor **无法替代任何核心算法**；推荐架构：**Canvas = 算法 SoT / DeepTutor = 前端 UI 层 + 浅层对话**（21-28d 实施）

---

## 第一部分：Canvas RAG 黑盒打开（Agent 1）

### 1.1 一句话评估

**Canvas RAG 是半黑盒，评分 3/10**。结构性测试骨架完整，但核心 RAG 质量闭环（RAGAS 评测、golden dataset 集成 CI、端到端真实召回率）尚未完成接线。**所有"召回质量"类断言目前全部依赖合成数据或 mock**，无一条基于真实用户查询的端到端 `recall@k` 数字落地。

### 1.2 已有测试盘点（结构性骨架）

#### 有量化指标 + 真实 fixture（最具说服力）

**`backend/tests/benchmark/test_routing_accuracy.py`** — **唯一一个用真实数据集 + 量化 pass/fail 阈值的 benchmark**

- 7 个测试，验证维度：accuracy / precision / recall / F1（per-agent）
- Fixture：`backend/tests/fixtures/routing_benchmark_dataset.json`（60 条中文样本，覆盖 6 种 agent 类型）
- 硬性断言：overall accuracy ≥ 80%（line 141）/ recall ≥ 50% per agent（line 185）/ 高置信率 ≥ 70%（line 279）
- ⚠️ **关键局限**：测试的是 **L1 意图路由**（哪种 agent），**不是 RAG 召回质量**（哪个 chunk）

#### 关键缺失（"已定义未接线"）

**`tests/golden_test_set.yaml`** — **50 条 query + ground_truth，但完全未被任何 pytest 文件 import**

- 覆盖：中文 15 + 英文 15 + 混合 5 + 模糊 5 + 定位 5 + 无关 5
- 🔴 **致命问题**：未被 parametrize，无 runner 跑这 50 条并计算 recall@5
- **它是一份未激活的 specification，不是执行中的测试**
- `backend/tests/regression/ragas_eval/fixtures/` 目录下只有 `.gitkeep`（无真实案例）

**`ragas_gate.py`** — RAGAS 评测从未真实运行

- 已定义阈值（faithfulness ≥ 0.70 / relevancy ≥ 0.75 / precision ≥ 0.60）
- 🔴 `_run_evaluation()` 在 `RAGAS_EVAL_HANDLE` 不存在时直接 `return {}`，exit code 0
- **CI job 永远显示绿色但什么都没测**

**`tests/test_lancedb_poc_synthetic.py`** — LanceDB 延迟 P95 < 20ms 是 **软性目标**

- 使用 NumPy 合成向量（1536 维，**无真实 bge-m3 embedding**）
- 🔴 超过 20ms 只打 WARNING，**不会让 CI 失败**（line 126-132）
- **CI 无法发现延迟退化**

#### 其他测试

**Integration（管道内部状态验证）**：
- `test_rag_quality_observability_surrogate.py`（3 个测试）— fuse_results / sharpness_report 结构正确，但**用合成数据**（"photosynthesis is..."）
- `test_crag_route_one_shot.py` — CRAG 状态机路由，mock LiteLLM
- `test_story_30_21_real_integration.py` — 真实 Neo4j 集成（需 `docker-compose up neo4j`），CI 默认跳过

**Regression**：
- `test_crag_grading_regression.py`（9 个）— CRAG prompt 版本一致性（分类一致率 ≥ 80%，触发率 15-40%）— **测的是 prompt 格式，不是召回质量**

**Unit**：
- `test_lancedb_vault_isolation.py` — vault_id table 隔离机制
- `test_fusion_report.py` — RRF 融合 metadata 正确生成

### 1.3 6 维基准测试现状

| 层级 | 现状 | 证据 |
|---|---|---|
| 意图路由准确率 | ✅ **真实 fixture（60 条）+ 硬断言 ≥ 80%** | `routing_benchmark_dataset.json` |
| CRAG 触发率 | ✅ 5 条 replay fixture + 断言 15-40% | `baseline_metadata.json:20-24` |
| **RAG 召回质量（recall@k）** | 🔴 **无**，golden_test_set.yaml 未接线 | `golden_test_set.yaml` 未被任何 py import |
| **RAGAS 评分** | 🔴 已定义阈值但 `_run_evaluation()` 占位符 | `ragas_gate.py:78-99` |
| **LanceDB 延迟** | ⚠️ 合成向量软性目标 | `test_lancedb_poc_synthetic.py:126` |
| 跨 vault 隔离 | ✅ unit test 覆盖 | `test_lancedb_vault_isolation.py:11` |

### 1.4 4 大潜在 bug / 黑盒风险

| # | 风险 | 严重度 |
|---|---|---|
| 1 | RAGAS gate 永远绿但什么都没测 | 🔴 高 |
| 2 | golden_test_set.yaml 50 条 query **悬空** | 🔴 高 |
| 3 | LanceDB P95 断言为软性，**CI 无法发现退化** | 🟠 中 |
| 4 | **bge-m3 embedding 从未在测试中实际调用**（合成 1536d 向量） | 🟠 中 |
| 5 | 4 路融合端到端 recall 完全未测（surrogate 用合成数据）| 🟠 中 |

### 1.5 5 步开盒方案

| # | 步骤 | 工程量 | 期望证据 |
|---|---|---|---|
| 1 | **激活 golden dataset CI gate** | **1d** | 50 条 query → 报告 recall@5 = X/50 |
| 2 | **修复 RAGAS gate 接线**（5-10 个 fixture）| **2d** | 首次可见真实 RAGAS 评分（faithfulness/relevancy/precision）|
| 3 | LanceDB 延迟硬断言（WARNING → assert）+ 替换 bge-m3 1024d 真实向量 | **0.5d** | P95 退化可被 CI 捕获 |
| 4 | （可选）与 LlamaIndex baseline 对照 | 3d | 在同 vault 上对比 recall@5 |
| 5 | （可选）Fusion 消融实验（4 通道）| 2d | 单路 vs RRF vs Layered-RRF 对比 |

🎯 **关键发现**：**1 天内激活 golden_test_set + 修硬 LanceDB assert，黑盒评分从 3 提升到 7**

### 1.6 与 LlamaIndex (DeepTutor) 对比

DeepTutor RAG 用 LlamaIndex + SimpleVectorStore，**LongBench 评估有公开数据**。Canvas RAG 当前**无可比较的端到端数据**。

**用户痛点核心**：用户希望"基准测试证明 Canvas RAG 有效"，**目前确实做不到**——但**1 天工程修复后可以**。

---

## 第二部分：DeepTutor 部署形态澄清（Agent 2）

### 2.1 一句话直接回答

✅ **是的，DeepTutor 完全可以 CLI 读本地文件**

```bash
deeptutor kb create canvas-vault --docs-dir ~/canvas-vault/节点/
```

立即可用，**不需要任何 Web UI**，CLI-only 模式可完全 headless 运行。

⚠️ **修正 round-16 描述**：之前把 DeepTutor 描述为"Web app（独立 Next.js）"**不准确**。DeepTutor 官方定位是 **Agent-Native 多形态系统**，**CLI-First**，Web UI 只是可选层。

### 2.2 5 种部署形态详细对比

| # | 模式 | 启动命令 | 需要前端 UI | Headless | 资源占用 | 备注 |
|---|---|---|---|---|---|---|
| 1 | **CLI-Only** ⭐ | `pip install -e ".[cli]"` + `deeptutor chat` | ❌ | ✅ 完全 | 最低（纯 Python + LLM API） | `.[cli]` extra **不含 FastAPI/uvicorn** |
| 2 | **Headless API Server** ⭐ | `deeptutor serve --port 8001` | ❌ | ✅ 完全 | 中（FastAPI + uvicorn，无 Next.js）| REST API 暴露在 `localhost:8001/docs` |
| 3 | Web App（本地）| `python scripts/start_tour.py` | ✅ Next.js 3782 | ❌ | 中高（后端 + 前端 + 向量库）| 向导式安装 |
| 4 | Docker Compose | `docker compose up -d` | 可选 | ✅ | 中（容器内）| 支持 amd64 + arm64 |
| 5 | MCP / 外部 Agent 接入 | `deeptutor serve` + SKILL.md 协议 | ❌ | ✅ | 同 API Server | JSON 输出 |

### 2.3 本地文件访问能力详解

#### CLI 模式（最直接）

```bash
# 单文件索引
deeptutor kb create my-kb --doc ~/notes/node.pdf

# 批量索引整个文件夹（含 Obsidian vault）
deeptutor kb create canvas-vault --docs-dir ~/canvas-vault/节点/

# 追加更多文件
deeptutor kb add canvas-vault --docs-dir ~/canvas-vault/原白板/

# 搜索验证
deeptutor kb search canvas-vault "admissibility 定义"
```

**关键发现**（来自 `deeptutor_cli/kb.py` 源码）：
- `--docs-dir` 调用 `FileTypeRouter.collect_supported_files(base, recursive=True)` — **递归扫描子目录**
- 支持格式：PDF / TXT / **Markdown** / DOCX / XLSX / PPTX
- 重复文件自动去重（SHA256）

**输出路径**：`data/knowledge_bases/<kb-name>/`（向量库 + 索引文件，本地落地）

#### Headless API Server 模式

```bash
deeptutor serve --host 0.0.0.0 --port 8001
# 文档：http://localhost:8001/docs（Swagger UI）
deeptutor run chat "解释 admissibility" -f json
```

- FastAPI server 独立运行
- `-f json` 输出结构化 JSON → 适合管道 / Obsidian plugin 调用

#### 文件写出能力

| 输出类型 | 命令 | 本地路径 |
|---|---|---|
| 对话记录 | `deeptutor session show <id>` | `data/user/sessions/` |
| Notebook | `deeptutor notebook add-md <id> <path>` | `data/user/notebooks/` |
| Memory 快照 | `deeptutor memory show --output <file>` | 用户指定 |
| Book Engine | `deeptutor book create <name>` | `data/books/<name>/` |
| KB 索引 | 自动 | `data/knowledge_bases/<name>/` |

### 2.4 CLI 主导的完整工作流

```
用户在 Obsidian 编辑 节点/admissibility.md
   写 [!error]+ "我总是混淆 admissibility 和 soundness"
         ↓
DeepTutor Headless（deeptutor serve --port 8001 后台常驻）
         ↓
   增量索引（deeptutor kb add canvas-vault --docs-dir ~/canvas-vault/节点/）
         ↓
用户在 Obsidian 触发 Claudian "AI 讲解"（Cmd+P）
         ↓
   路径 A（推荐）：Claudian Skill → Canvas backend
     POST /api/v1/chat/enrich-context（5 路融合 RAG）
         ↓
   路径 B（补充）：Claudian → DeepTutor REST
     POST http://localhost:8001/api/chat（JSON 返回）

整个流程：用户从未打开 DeepTutor Web UI
```

### 2.5 推荐部署形态（针对 Canvas Learning System 用户）

```
是否需要 DeepTutor 自带 Web UI？
├── 否（Canvas 有 Obsidian 界面）
│   ├── 只想批量建库 / 测试索引 → CLI-Only
│   └── 想让 Obsidian plugin 调用 → Headless API Server ⭐
└── 是（临时调试 / 查看对话历史）→ Web App（本地）
```

| 推荐路径 | 工程量 | 优缺点 |
|---|---|---|
| A. CLI-Only（最简）| 30 min | + 零配置；- 无实时 API |
| **B. Headless API Server**（推荐）⭐ | 1-2d 桥接代码 | + 完全 headless；+ REST JSON；- 与 Canvas RAG 数据双份 |
| **C. Canvas RAG 主导，DeepTutor 调 Canvas API**（最优）⭐ | 2-3d adapter | + DeepTutor 用 Canvas 5 路融合；+ 无数据冗余；- 需改 DeepTutor SmartRetriever |
| D. Docker Headless | 1h | + 环境一致性；- 资源占用高 |

**Canvas Learning System 用户最优**：**路径 C** + vault 文件夹直接由 `deeptutor kb add --docs-dir` 索引。

---

## 第三部分：学习推导过程在 Graphiti 中表达（Agent 3）

### 3.1 一句话蓝图

用户的批注（callout）、双向链接（wikilink）、节点段落修改三者映射为带 `valid_at` 时序的 **EpisodeTask 流**写入 Graphiti，同时在 Neo4j 中维护 `ReasoningStep` entity chain；agent 出题/复盘/解释时通过 MCP 工具 `get_reasoning_chain(node_id)` 拉取该链注入 ACP Layer 3，使 agent **知道用户在哪一步想明白了什么、哪一步还在疑惑**。

### 3.2 4 数据模型对比

#### 选项 A：Episode 时序流（纯 EpisodeTask）

每个用户动作 → 1 个 `EpisodeTask`，`source_description` 区分动作类型，`reference_time` = 动作时间戳。

| 优势 | 劣势 |
|---|---|
| 零扩展代价（`EpisodeTask` dataclass 已有 `reference_time` / `metadata` / `entity_types` 字段）| 无结构化链接（"上一步→下一步"靠 valid_at 推断）|
| Graphiti `valid_at` 时序语义天然对齐 | agent 拿到自然语言列表，需二次 LLM 解析得推导链 |

#### 选项 B：ReasoningStep entity chain（专用结构）

新增 `ReasoningStep` 到 `entity_types.py`：
- `step_id` / `node_id` / `action_type`（annotation_added / wikilink_added / paragraph_revised）
- `content` / `previous_step_uuid`（形成 DAG）/ `valid_at`

| 优势 | 劣势 |
|---|---|
| **BFS 可遍历**（previous_step_uuid 显式 DAG）| 每步写两次（EpisodeTask + Neo4j MERGE）|
| 与 `CANVAS_ENTITY_TYPES` 100% 兼容 | previous_step_uuid 串联需后端维护"最新一步"状态（Redis/LRU）|
| 可按语义检索（NODE_HYBRID_SEARCH_CROSS_ENCODER） | |

#### 选项 C：DiscussionThread 长 episode（聚合）

同一节点在时间窗口内的所有动作合并为 1 个长 episode。

| 优势 | 劣势 |
|---|---|
| 检索时一次 search_() 拿到完整讨论 | **丢失细粒度时序**（先疑惑→后明白演化被平铺）|
| token 消耗低 | 窗口切割引入超参（5 分钟？1 小时？）|

#### 选项 D：混合模型 ⭐ 推荐

| 层 | 机制 | 职责 | 消耗 |
|---|---|---|---|
| **原子层** | EpisodeTask（A）| 每个动作即时写，保留时序原始流 | episode_worker 队列现有路径 |
| **结构层** | ReasoningStep entity（B）| 显式 DAG，previous_step_uuid 链 | Neo4j MERGE，与 sync_service 共线程 |
| **聚合层** | 批量 episode `discussion_thread`（C）| 每节点每日批量摘要，压缩存档 | 定时任务（cron）|

**推荐理由**：原子层解决"回放"，结构层解决"推理"，聚合层解决"检索效率"。三层互补，agent 按需选用。**修复零同步的同时顺带解决"只写不读"问题**。

### 3.3 数据采集时机表

| 用户动作 | Obsidian 触发器 | 后端入口 | Graphiti 写入 |
|---|---|---|---|
| 写 `[!error]+`/`[!tip]+`/`[!question]+` | `metadataCache.on("changed")`（main.ts:140，当前只清 masteryCache）| 新增 `POST /api/v1/reasoning/annotation` | `EpisodeTask(source='annotation_added', entity_types={'ReasoningStep': ...})` |
| 加 `[[X]]` wikilink | 同上，解析 `metadataCache.resolvedLinks` | `POST /api/v1/reasoning/link` | EpisodeTask + Neo4j REFERENCES edge |
| 删除 callout / wikilink | `vault.on("modify")` diff 检测 | 同上带 action='removed' | EpisodeTask(source='annotation_removed') |
| 节点 md 段落修改（非 callout）| metadataCache.on("changed") 段落 hash diff | `POST /api/v1/reasoning/paragraph` | EpisodeTask(source='discussion_paragraph') |
| `Cmd+Shift+D` 派生 | `handleAiLinkedDoc()` | 现有 `/api/v1/wikilink/build` 加 episode 旁路 | EpisodeTask + edge DERIVED_FROM |
| 节点重命名 | `vault.on("rename")` | `POST /api/v1/reasoning/rename` | entity rename + EpisodeTask |

**前端 diff 实现**：
```typescript
// metadataCache.on("changed") 扩展
const newSections = metadataCache.getFileCache(file)?.sections
const calloutBlocks = newSections.filter(s => s.type === 'callout')
const newLinks = metadataCache.resolvedLinks
const diff = computeDiff(oldState, {calloutBlocks, newLinks})
requestUrl(settings.backendUrl + '/api/v1/reasoning/diff', diff)  // fire-and-forget
```

### 3.4 Agent 3 场景使用方式

#### 场景 1：出题（Stage F / question_generator.py）

ACP 当前抓取 6 类数据。**新增第 7 项**：

```python
acp.reasoning_chain = await self._get_reasoning_chain(node_id, days=7)
```

Layer 3 注入：

```
[用户推导过程 — 近 7 天]
- T-3d [annotation_added][!question]+: 为什么 admissibility 是 zero-knowledge 的前提？
- T-2d [wikilink_added]: [[zero-knowledge proof]]
- T-1d [discussion_paragraph]: "我现在明白了：admissibility 保证..."

[出题策略提示]
基于 T-1d 理解跃迁，出题验证此理解，陷阱点设在 T-3d 的未解疑问。
```

→ **直接提升"诱导再犯"策略有效性**

#### 场景 2：复盘（Day 3/7 错误闭环）

```
当 record_error 写入新 Misconception
→ get_reasoning_chain(node_id, days=30)
→ 找时间点最近的 ReasoningStep
→ 定位"用户在哪一步推导错了"
→ 回复："你 3 天前写 [!error]+... 说明你看到 X 概念时误以为 Y，
   这个错误源自你 T-5d 加的 [[Z]] 双链——你理解 Z 的方式有偏差"
```

→ **直接攻克 round-14 残缺 #1**（错误只写不读）

#### 场景 3：解释（chat-with-context）

```
用户在节点问"为什么 admissibility 这么重要"
→ wikilink_context_service.py 取 1-hop 邻居
→ agent 调 get_reasoning_chain(node_id, days=14)
→ 引用用户自己推导内容：

"你 5 天前在 admissibility 节点写过 [!tip]+ '关键是完整性条件'，
这正是你当时自己总结的答案——你现在只是需要把它和 heuristic consistency 连起来。"
```

→ 比 agent 重新解释概念**信息密度更高 + 强化 testing effect**

### 3.5 4 阶段工程实施

| Phase | 内容 | 工程量 |
|---|---|---|
| **Phase 1** 数据采集层 | 前端 metadataCache.on("changed") diff 扩展 + 后端 POST /api/v1/reasoning/diff + Outbox 队列异步写 episode | **2.5d** |
| **Phase 2** 数据模型扩展 | `entity_types.py` 加 `ReasoningStep` + 内存 LRU 维护"最新一步"状态 | **1.5d** |
| **Phase 3** 检索层 | `mcp/server.py` 加 `get_reasoning_chain` 工具 + REST `/api/v1/reasoning/chain` | **2d** |
| **Phase 4** 消费层 | `question_generator.py` ACP Layer 3 加 reasoning_chain 字段 + DeepTutor `deep_question.py` Drafting stage 注入 | **1.5d** |

**总工程量**：**约 7.5d**（可并行：Phase 1+2 前半并行，Phase 3+4 在 Phase 2 完成后并行）

### 3.6 与已知残缺 + DeepTutor 集成的关系

**直接攻克的残缺**：
- ✅ **残缺 #4（零同步）** — 整个 Phase 1 = "前端→Graphiti 零同步"的解法
- ✅ **残缺 #1（错误只写不读）** — `ReasoningStep` chain 的读路径提供"按节点+时间范围读取推导历史"

**间接但未解决**：
- ⚠️ 残缺 #2（group_id 旧格式）— Phase 4 补丁修复（新写入用 `vault:<id>`，历史迁移单独 script）
- ⚠️ 残缺 #3（embedding 退化）— **本方案不涉及**，需独立任务接入 bge-m3 embedding search（2-3d）

**DeepTutor 集成**（DeepTutor 完全是消费方）：
```
DeepTutor Deep Solve plan 阶段
→ HTTP GET canvas_backend/api/v1/reasoning/chain?node_id=X&days=7
→ 返回 JSON: [{step_id, action_type, content, valid_at}, ...]
→ 注入 Deep Solve prompt 的"学生推导历史"段
```

**关键前置条件**：建议实施顺序 — Phase 1（数据入库）→ 残缺 #2 group_id 迁移（1d）→ Phase 2-3（结构化+检索）→ 残缺 #3 embedding 修复（2-3d）→ Phase 4（消费层）。**修复 embedding 放在检索层之前**，确保 Layer 3 注入的推导链质量可靠。

---

## 第四部分：需求对齐 — DeepTutor 实现 Canvas 工作流可行性（Agent 4）

### 4.1 一句话总结

**⚠️ 有条件可行，但改造成本远超重写成本**。Canvas 后端核心算法层（BKT/FSRS、错误 pipeline、AutoSCORE、ACP 5 层）已深度实现 + **370 个测试文件覆盖**，DeepTutor **无法替代任何核心算法**。**最终结论**：DeepTutor 作前端 UI 层 + 浅层对话层（21-28d），Canvas 算法层完全保留。

### 4.2 7 Stage 需求映射表

#### Stage A — 学习内容输入

| 子需求 | Canvas 现状 | DeepTutor 现成支持 | 工程量 |
|---|---|---|---|
| PDF/DOCX 索引 | LanceDB + Graphiti 双写（`lancedb_index_service.py:42`）| ✅ DeepTutor `add_documents.py` 立即处理 | 1-2d 桥接 |
| vault 文件夹批量索引 | `wikilink_graph_service.py:59` obsidiantools 完整双向图 | ❌ DeepTutor 无 obsidiantools | DeepTutor 不可替代 |
| frontmatter + wikilink 解析 | Canvas `WikilinkGraphService._get_frontmatter()` | ❌ DeepTutor RAG 视为纯文本 | DeepTutor 不可替代 |
| 增量索引 | `LanceDBIndexService.schedule_debounced_index()` 防抖 | ❌ DeepTutor 无 watch 机制 | DeepTutor 不可替代 |

**结论**：DeepTutor 处理 PDF 部分可用（30%），vault md 解析 / wikilink / 增量触发 Canvas 已全量实现。**Canvas RAG pipeline 保留**。

#### Stage B — 知识拆解（原白板）

DeepTutor 无白板概念，无节点编辑 UI，无 callout 批注。

**结论**：DeepTutor 对 Stage B **贡献 0%**。Obsidian + Canvas wikilink 服务不可替代。

#### Stage C — AI 辅助理解

| 子需求 | Canvas 现状 | DeepTutor 能力 |
|---|---|---|
| chat-with-context | `POST /api/v1/chat/enrich-context` 注入邻居+错误+callout | DeepTutor Chat/Deep Solve 可用，但无此 API |
| 邻居注入 | `ChatContextAssembler.assemble_context()` | 无等价 |
| RAG 4 路融合 | LanceDB + Graphiti + BM25 + 重排序 | LlamaIndex + SimpleVectorStore 单路 |
| cite 溯源 | Canvas RAG 自动返回 source_node | DeepTutor 自动 cite 可用 |

**结论**：DeepTutor Chat/Deep Solve 可作前端对话界面（70%），调用 Canvas API 注入上下文（2-3d）。

#### Stage D — 错误捕获（progressive_confirmation）

Canvas 完整代码实证：
- 错误候选写入 `error_writer.py`
- 4 类 ErrorType 枚举（`entity_types.py:25`）：PROBLEM_FRAMING / REASONING_FALLACY / KNOWLEDGE_GAP / SUPERFICIAL
- 双层分类 `ErrorClassifier.classify_with_pedagogy()`
- 主权确认 API `POST /errors/accept-candidate` / `dismiss-candidate` / `dispute-candidate`
- Graphiti 双写 `candidate_service.py:302`

DeepTutor 完全没有候选确认 UX，无 4 类分类，无 Graphiti 写入。

**结论**：DeepTutor 对 Stage D **贡献 0%**。Canvas 错误 pipeline 完整保留。

#### Stage E — 掌握度 + FSRS

Canvas 完整代码实证：
- BKT `MasteryEngine._bkt_update()`（295 行专项测试 `test_mastery_engine_bkt.py`）
- FSRS-4.5 `FSRSManager`（526 行专项测试 `test_fsrs_manager.py`）
- **总 821 行专项测试**
- 5 信号融合 `MasteryFusionEngine.compute_fused_mastery()`
- Grade → FSRS rating 映射（1-Forgot→Again, 2-Struggled→Hard, 3-Correct→Good, 4-Fluent→Easy）

**结论**：DeepTutor 对 Stage E **贡献 0%**。迁移风险极高（损失 821 行专项测试）。

#### Stage F — 检验白板生成

Canvas 完整代码实证：
- 选薄弱节点 `select_target_node()` FSRS+BKT+KG 三因子
- ACP 装配 `assemble_acp()`（token budget 9000 chars）
- 5 层 prompt `build_5_layer_prompt()` Layer1-5
- 诱导再犯 4 种 `RemedyStrategy` 枚举 + `_determine_remediation_strategy()` 动态注入

DeepTutor `deep_question.py` 4-stage 与此架构不兼容；CONCEPT_GRAPH 是 deterministic renderer 不调 LLM。

**结论**：DeepTutor 部分贡献（Book Engine BlockType 渲染 20%），ACP 5 层出题逻辑完全 Canvas 侧，DeepTutor 作前端渲染层调用 `/api/v1/review/generate`，**8-10d**。

#### Stage G — 答题评分反馈

Canvas 完整代码实证：
- 4 维 SOLO Rubric `RUBRIC_DIMENSIONS = ["concept_accuracy", "reasoning_quality", "knowledge_coverage", "knowledge_integration"]`
- 3× 独立 LLM 投票 `_score_with_rubric()`
- 多数投票 + 低置信检测 `_majority_vote()`
- Day 0/3/7 `ArchiveScheduler` + `error_rebuild_service.py`

DeepTutor `is_correct: bool` 二元判断，完全无 Rubric / 多投票。

**结论**：DeepTutor 渲染层（10%），评分核心完全 Canvas，**6-8d** 桥接。

### 4.3 7 心头愿景 × DeepTutor 实现度

| # | 愿景 | DeepTutor 现成支持 | Canvas 现状 | 可行性 |
|---|---|---|---|---|
| 1 | Graphiti 后端 ↔ 前端批注一致 | ❌ | `candidate_service.py:302` | Canvas 独占 |
| 2 | 精确多段推理 + 批注驱动出题 | Book Engine 部分 | `question_generator.py:271` ACP + Cypher multi-hop | Canvas 上游，DeepTutor 渲染 |
| 3 | 原白板/检验白板/FSRS 三位一体 | ❌ | `review_service.py:89` + `exam_service.py` | Canvas 独占 |
| 4 | 诱导再犯策略 | ❌ | `entity_types.py:46` RemedyStrategy + Layer4 动态注入 | Canvas 独占 |
| 5 | Graphiti 关系 ↔ wikilink 一致 | ❌ | `wikilink_graph_service.py:59` obsidiantools → NetworkX | Canvas 独占 |
| 6 | AI 主动检测错误 + 增量确认 | TutorBot Heartbeat 近似 | `errors.py:79` accept/dismiss/dispute | Canvas 独占 |
| 7 | vault 笔记片段精确返回 | RAG cite 部分 | `rag_service.py:278` LanceDB + Graphiti 双路 | Canvas 4 路更精确 |

### 4.4 7 Stage 可行性评分汇总

| Stage | DeepTutor 贡献 | Canvas 必须保留 | 整体结论 |
|---|---|---|---|
| A 内容输入 | 30%（PDF）| 70%（vault/wikilink/增量）| 可行，Canvas 主导 |
| B 原白板 | 0% | 100%（Obsidian + WikilinkGraphService）| 可行，Canvas+Obsidian 独占 |
| C AI 辅助 | 70%（Chat UI + Deep Solve）| 30%（enrich-context 桥接）| 可行，DeepTutor 作前端 |
| D 错误捕获 | 0% | 100% | 可行，Canvas 独占 |
| E 掌握度 + FSRS | 0% | 100%（821 行测试）| 可行，Canvas 独占，迁移风险极高 |
| F 检验白板 | 20%（BlockType 渲染）| 80%（ACP+FSRS+诱导）| 重度桥接（8-10d）|
| G 答题评分 | 10%（展示）| 90%（AutoSCORE+Day 0/3/7）| 重度桥接（6-8d）|

### 4.5 7 条红线（不可妥协的 Canvas 需求）

以下功能在代码库中均有完整实现 + 专项测试，**DeepTutor 完全不具备替代能力**：

1. **错误 4 类分类 + 双层分类 + 主权确认** — `entity_types.py:25` + `error_classifier.py:148` + `errors.py:79`
2. **BKT + FSRS-4.5 掌握度算法** — `mastery_engine.py:216` + `fsrs_manager.py:92` + **821 行专项测试**
3. **AutoSCORE 4 维 SOLO Rubric × 3 投票** — `autoscore.py:31` + `_score_with_rubric()` + `_majority_vote()`
4. **ACP 5 层 prompt + 诱导再犯**（Layer4 动态注入）— `question_generator.py:417` + `_determine_remediation_strategy()`
5. **Graphiti 时序 KG 双写** — `candidate_service.py:302` — 用户选 Graphiti 的根本理由
6. **obsidiantools wikilink 图 + frontmatter 解析** — `wikilink_graph_service.py:59`
7. **三白板隔离**（原白板/检验白板/FSRS 时序）— `exam_service.py:78` + `review_service.py` — D14 哲学底线

### 4.6 推荐架构（最终结论）

```
用户
  ↓
DeepTutor UI (Chat/Deep Solve/Book Engine 渲染)
  ↓ REST/WebSocket 桥接层
Canvas Backend (FastAPI) — 唯一算法 SoT
  ├── /api/v1/chat/enrich-context      ← Stage C
  ├── /api/v1/errors/accept-candidate  ← Stage D
  ├── /api/v1/mastery/{node_id}        ← Stage E
  ├── /api/v1/review/generate          ← Stage F
  └── /api/v1/score/autoscore          ← Stage G
  ↓
Graphiti (Neo4j) + LanceDB + Obsidian vault
```

**总工程量**：

| 阶段 | 内容 | 工程量 |
|---|---|---|
| Stage A 桥接（PDF → DeepTutor + vault Canvas）| | 2-3d |
| Stage C UI 桥接（DeepTutor Chat 调 enrich-context）| | 2-3d |
| Stage F 渲染层（DeepTutor Book ← Canvas review/generate）| | 8-10d |
| Stage G 展示层（DeepTutor 展示 AutoSCORE 结果）| | 4-5d |
| 格式适配 + 测试 | | 5-7d |
| **总计** | | **21-28d** |

**前提**：Canvas 后端所有算法层原封不动保留。

⚠️ **如果尝试将算法层迁入 DeepTutor**（BKT/FSRS/AutoSCORE/ACP/错误 pipeline），工程量 **>50d** 且失去 370 个已通过测试，**强烈不推荐**。

---

## 第五部分：综合实施路线图

### 5.1 4 Agent 发现汇总

| Agent | 兼容度 / 评分 | 关键发现 |
|---|---|---|
| 1. RAG 黑盒诊断 | 3/10 → **1d 修复 → 7/10** | golden_test_set.yaml 悬空 + RAGAS gate 占位符 + LanceDB 软性断言 |
| 2. DeepTutor 部署 | ✅ CLI 完全可用 | Agent-Native 多形态系统，**修正 round-16 描述错误**；推荐 Headless API Server |
| 3. 推导链 Graphiti | 7.5d 实施 | 混合模型（EpisodeTask + ReasoningStep + DiscussionThread）**直接攻克残缺 #4** |
| 4. 需求对齐 | 21-28d | Canvas 算法层完全保留 + DeepTutor 作前端，**7 条红线不可妥协** |

### 5.2 5 阶段联合实施路线图

#### Stage 0：RAG 开盒 + 数据基础修复（3-5d）⭐ 必先做

| 项 | 工程量 | 来源 |
|---|---|---|
| 激活 golden_test_set.yaml CI gate | 1d | Agent 1 |
| 修复 RAGAS gate 接线 | 2d | Agent 1 |
| LanceDB 延迟硬断言 + bge-m3 1024d 真实向量替换合成 | 0.5d | Agent 1 |
| Canvas group_id 迁移（cs188 → vault:<id>）| 1d | round-14 残缺 #2 |

**目标**：RAG 黑盒打开（评分 3→7），group_id 现代化。

#### Stage 1：学习推导链（7.5d）⭐ 高 ROI

| 项 | 工程量 | 来源 |
|---|---|---|
| Phase 1 数据采集层（metadataCache.on("changed") diff + 后端端点 + Outbox）| 2.5d | Agent 3 |
| Phase 2 ReasoningStep entity 注册 + 内存 LRU | 1.5d | Agent 3 |
| Phase 3 `get_reasoning_chain` MCP 工具 + REST 端点 | 2d | Agent 3 |
| Phase 4 ACP Layer 3 注入推导链 + DeepTutor 消费 | 1.5d | Agent 3 |

**目标**：直接攻克残缺 #4（零同步）+ 间接修复 #1（错误只写不读）。

#### Stage 2：DeepTutor 浅层桥接（5-7d）

| 项 | 工程量 | 来源 |
|---|---|---|
| DeepTutor Headless 部署（`deeptutor serve --port 8001`）| 0.5d | Agent 2 |
| `deeptutor kb create canvas-vault --docs-dir` 索引 vault | 0.5d | Agent 2 |
| 路径 C：DeepTutor SmartRetriever 代理 Canvas `/api/v1/rag/search` | 2-3d | Agent 2 + round-17 |
| Canvas Reranker 接入 DeepTutor + LanceDBVectorStore 切换 + EmbeddingSignature | 1.5d | round-17 |
| Canvas MCP 18 工具桥接到 DeepTutor agent | 1d | Agent 4 |

**目标**：DeepTutor 立即可调 Canvas RAG，无 Web UI 依赖。

#### Stage 3：Book Engine + 出题流水线（10-12d）

| 项 | 工程量 |
|---|---|
| Bridge API 4 端点（vault/notes_context + autoscore + error_candidate + fsrs/due）| 1.5d |
| QUIZ block 扩展 + ExamSession→Book adapter | 1.5d |
| **deep_question 替换为 Canvas question_generator + self-check** | 2d |
| is_correct → AutoSCORE 桥接 + DeepTutor UI 4 维展示 | 1.5d |
| FSRSManager 复制到 DeepTutor + Record schema 扩展 + Due Today UI | 4.5d |
| Claudian Skill 调 Deep Solve（MCP 代理工具）| 1d |

**目标**：Stage F+G 完整闭环。

#### Stage 4：高级特性（11-15d，可推迟）

- CONCEPT_GRAPH block 接 Cypher 子图（multi-hop + Mermaid 转换器）— 2.5d
- TIMELINE block 接 FSRS Day 0/3/7 闭环 — 1d
- TutorBot Heartbeat + Canvas FSRS due-today — 3d
- Telegram + Obsidian Notice 双通道推送 — 2d
- Deep Research 加 canvas_vault 第 4 源 — 2d
- SkillExecutor（YAML frontmatter 解析）— 4d
- SSE↔WebSocket 适配器 — 1d

**目标**：完整愿景闭环。

### 5.3 总工程量

| Stage | 内容 | 工程量 |
|---|---|---|
| **Stage 0** RAG 开盒 + 数据基础 | 必先做 | **3-5d** |
| **Stage 1** 学习推导链 | 高 ROI | **7.5d** |
| **Stage 2** DeepTutor 浅层桥接 | | **5-7d** |
| **Stage 3** Book Engine + 出题流水线 | 核心闭环 | **10-12d** |
| **Stage 4** 高级特性 | 可推迟 | **11-15d** |
| **总计** | | **36-46d**（约 7-9 周）|

**优化（去重 + 并行）**：**30-38d**（约 6-8 周）。

2 人并行 Stage 1-3 → **4-5 周达到核心闭环**。

### 5.4 关键依赖图

```
Stage 0（RAG 开盒 + 数据基础）
  │
  ├─► Stage 1（学习推导链 — 攻克零同步）
  │     │
  │     └─► Stage 3（Book Engine — ACP Layer 3 需推导链数据）
  │
  └─► Stage 2（DeepTutor 浅层桥接 — 需 group_id 现代化）
        │
        └─► Stage 3（Book Engine — 需 DeepTutor 桥接就位）
              │
              └─► Stage 4（高级特性）
```

**Stage 0 是硬依赖**。Stage 1+2 可并行。

---

## 第六部分：6 个决策点（请用户审计）

### Decision 1：Stage 0 RAG 开盒是否优先做？

**Claude 推荐**：✅ 优先做（1d 投资 + 3→7 评分提升）

**选项**：
- A. **Stage 0 优先（3-5d）**⭐ → 黑盒打开，RAG 评分 7/10，后续工作有信心
- B. 跳过 Stage 0，直接 Stage 1 推导链 → 短期看到推导链，但 RAG 仍黑盒
- C. Stage 0 与 Stage 1 并行（人力允许）→ 节省 2-3d

### Decision 2：DeepTutor 部署形态选择

**Claude 推荐**：Headless API Server（`deeptutor serve --port 8001`）

**选项**：
- A. CLI-Only（最简，30 min 配置）
- **B. Headless API Server**（1-2d 桥接，REST JSON 接口）⭐
- C. Docker Headless（1h，环境一致性）
- D. Web App（需 Next.js port 3782，不推荐）

### Decision 3：推导链数据模型选择

**Claude 推荐**：混合模型 D（EpisodeTask + ReasoningStep + DiscussionThread 三层）

**选项**：
- A. 纯 Episode 时序流（最简，0d 扩展）→ 失去结构化推理
- B. ReasoningStep entity chain（结构化但无时序）
- C. DiscussionThread 长 episode（聚合但失去细粒度）
- **D. 混合模型**（7.5d，三层互补）⭐

### Decision 4：DeepTutor 算法层迁入 vs 桥接

**Claude 推荐**：完全保留 Canvas 算法层（21-28d 桥接 vs >50d 迁入）

**选项**：
- A. **完全保留 Canvas 算法层**（21-28d，DeepTutor 作前端 UI 层）⭐
- B. 部分迁入（FSRS 复制到 DeepTutor，错误 pipeline 保留 Canvas）→ 工程量增加
- C. 完全迁入 DeepTutor → >50d + 失去 370 测试，**强烈不推荐**

### Decision 5：CONCEPT_GRAPH multi-hop 实施时机

**Claude 推荐**：Stage 4 实施（不阻塞 Stage 1-3）

**选项**：
- A. Stage 3 内做（提前 multi-hop 推理，但增加工程量 2.5d）
- **B. Stage 4 推迟**（先验证 Stage 1-3 价值，再决定）⭐
- C. 等 LightRAG 集成（ETA 不确定）

### Decision 6：是否同步修复 round-14 残缺 #3（embedding 退化）

**Claude 推荐**：Stage 1 后插入修复（2-3d）

**背景**：`neo4j_edge_client.py:235` `search_nodes` 用 Cypher CONTAINS（关键词搜索），真正 bge-m3 embedding search 在 `lib/agentic_rag` 独立 lib 但**未接入主管道**。

**选项**：
- **A. Stage 1 后插入修复**（确保 Layer 3 推导链质量）⭐
- B. Stage 3 内修复（推迟）
- C. 不修复，用 Cypher CONTAINS 兜底

---

## 附录 A：4 Agent 引用文件清单

### Agent 1（Canvas RAG 黑盒诊断）
- `backend/tests/benchmark/test_routing_accuracy.py`（60 条 fixture + 80% accuracy 硬断言）
- `tests/golden_test_set.yaml`（50 条 query 悬空）
- `backend/tests/regression/ragas_eval/ragas_gate.py:78-99`（占位符）
- `tests/test_lancedb_poc_synthetic.py:126-132`（软性 P95 断言）
- `backend/tests/integration/test_rag_quality_observability_surrogate.py`（合成数据）
- `backend/tests/integration/test_crag_route_one_shot.py`（mock LiteLLM）

### Agent 2（DeepTutor 部署形态）
- `deeptutor_cli/kb.py`（FileTypeRouter.collect_supported_files）
- `https://hkuds.github.io/DeepTutor/guide/getting-started.html`（CLI-First 定位）
- `deeptutor_cli/__init__.py`（CLI 命令注册）
- DeepTutor SKILL.md（MCP 协议接口）

### Agent 3（推导链 Graphiti 表达）
- `backend/app/services/episode_worker.py:44-57`（EpisodeTask dataclass）
- `backend/app/graphiti/entity_types.py:360-369`（CANVAS_ENTITY_TYPES 注册点）
- `backend/app/services/wikilink_graph_service.py:30, 59`（NetworkX BFS）
- `frontend/obsidian-plugin/src/main.ts:139-145, 582, 1168`（钩子 + diff 实现位置）
- `backend/app/services/question_generator.py:271, 283-326`（ACP 组装 7 类数据）

### Agent 4（需求对齐）[[111]]
- `backend/app/services/lancedb_index_service.py:42, 80`（双写 + 防抖）
- `backend/app/services/wikilink_graph_service.py:59`（obsidiantools）
- `backend/app/graphiti/entity_types.py:25, 46`（4 类 ErrorType + 4 种 RemedyStrategy）
- `backend/app/services/error_classifier.py:148, 201`（双层分类）
- `backend/app/api/v1/endpoints/errors.py:79`（accept/dismiss/dispute）
- `backend/app/services/mastery_engine.py:153, 216`（BKT + grade 映射）
- `backend/lib/memory/temporal/fsrs_manager.py:92`（FSRS 完整实现）
- `backend/app/services/mastery_fusion.py:46`（5 信号融合）
- `backend/app/services/question_generator.py:271, 376, 408, 417`（ACP + RemedyStrategy + 5 层）
- `backend/app/services/autoscore.py:31, 39, 176, 411`（4 维 + Grade + 3 投票 + majority vote）
- `backend/tests/`（370 个测试文件）+ `test_mastery_engine_bkt.py`（295 行）+ `test_fsrs_manager.py`（526 行）

---

## 附录 B：用户 2 条新批注 ↔ 调研发现对照

| 批注 | round-17 行号 | 调研发现 | 行动 |
|---|---|---|---|
| RAG 像黑盒，没有实际验证 | line 50 | Agent 1：评分 3/10，1d 修复 → 7/10 | Stage 0 优先 |
| 需求对齐 — DeepTutor 能否实现 Canvas 工作流 | line 50 | Agent 4：⚠️ 有条件可行（21-28d，Canvas 算法层完全保留）| Stage 2-4 实施 |
| DeepTutor 是否 CLI 可读本地文件？还是 Web app？ | line 703 | Agent 2：✅ CLI 完全可用，**修正 round-16 描述错误** | 用 Headless API Server |
| 用户批注 + 双链构建 → Graphiti → agent 知道整个学习推导过程 | line 703 | Agent 3：混合模型 7.5d 实施 | Stage 1 高 ROI |

---

## 状态

- **报告生成**：2026-05-06 ≈04:00
- **下一步**：等用户审计 6 个决策点
- **建议起点**：Decision 1（Stage 0 是否优先）+ Decision 2（DeepTutor 部署形态）即可启动 Stage 1
- **已累计决策点**：round-14 4 + round-15 4 + round-16 5 + round-17 8 + round-18 6 = **27 个待用户审定**
- **后续动作**：用户审定后，转 `_decisions/` + 起草 Stage 0-4 各阶段 Story spec


User： 1,DeepTutor 的 readme 有提到 **测验生成** 这一点是对应我的检验白板；**数学动画** 和 **可视化** 是我欣赏 的讲题方式。


2，**“给 DeepTutor 一个主题，指向你的知识库，即可产出一本结构化、可交互的书 —— 不是静态导出物，而是你可以阅读、自测、并在上下文中讨论的活文档。**

**幕后由多智能体流水线驱动：提案大纲、知识库深度检索、章节树合成、页面规划、逐块编译。你始终掌控全局 —— 审阅提案、拖拽调整章节、在任意页面旁聊天。**

**页面由 14 种块类型拼装：文本、提示、测验、闪卡、代码、图表、深入解读、动画、交互演示、时间线、概念图、章节、用户笔记与占位符 —— 每种都有专属交互组件。实时进度时间线让你见证编译过程。”**  （我觉得他这里提供的工具是可以满足我们原白板的拆解和批注的学习方式，对于自己感兴趣的内容提取讨论，并且能标记出各个点的理解程度，然后我的原白板各个批注和点的拆解和链接，也是同步到后端的 Graphiti 上表示我拆解的逻辑方式，我原白板的核心：1，能用批注标记理解程度；2，能用批注和拆解 展现出我的推导过程。）

   3，- **知识库 — 上传 PDF、TXT、Markdown，形成可检索、RAG 就绪的集合；可增量追加。**
- **笔记本 — 跨会话整理学习记录；聊天、Co-Writer、Book、深度研究的洞见可按色分类保存。**
- **题库 — 浏览并回顾所有生成的测验题目；可收藏，并在聊天中 @-引用以回顾历史表现。**
- **Skills — 通过 `SKILL.md` 创建自定义教学人设：定义名称、描述、可选触发词与 Markdown 正文，激活后注入聊天系统提示 —— 让 DeepTutor 变身苏格拉底导师、同伴学习者、科研助手或你设计的任何角色。**

**知识库不是冷存储 —— 它主动参与每次对话、研究与学习路径。**  

（我希望我们的知识库不用上传文件，而是指定直接访问我们的指定文件夹，然后我们和前端 UI 交互可以直接修改到我们的本地文件）


**4，- Soul 模板 — 通过可编辑 Soul 文件定义人格、语气与教学理念；可选内置原型或完全自定义。**
- **独立工作区 — 每实例独立目录：记忆、会话、技能与配置隔离，仍可访问 DeepTutor 共享知识层。**
- **主动心跳 — 不止被动回复：心跳系统支持定期学习提醒、复习与计划任务。**
- **完整工具 — RAG、代码执行、联网、论文检索、深度推理、头脑风暴。**
- **技能扩展 — 在工作区添加技能文件即可教会新能力。**
- **多通道 — 可接 Telegram、Discord、Slack、飞书、企业微信、钉钉、邮件等。**
- **团队与子智能体 — 后台子任务或多智能体协作，应对长程复杂任务。**

（这里的主动心跳不就是可以对应我们的 FSRS 告诉我们什么时候该复习什么吗？）


