# ChatGPT Deep Research — Story 2.5 用户主权 & 多 Vault 隔离两难

> **本文档是给 ChatGPT Deep Research（或 Gemini 2.5 Pro Deep Research / Perplexity Pro Research）的提示词**。
>
> **背景**：Canvas Learning System 的 Story 2.5（错误自动提取与分类）已 ship 到 commit `0d05ad8`，ChatGPT round-5 给了 8/10。但用户在 UAT 阶段提出**两个深刻的产品质疑**，触及 AI 学习产品的核心张力：
>
> 1. **用户主权问题**：双链 / 批注是用户主动指定关系，但 Story 2.5 是 AI 自动判错。如何平衡 AI 智能 vs 用户认知主权？
> 2. **隔离架构问题**：当前是单 Neo4j 容器 + Graphiti group_id 软隔离。是否应该改为"一 vault 一 docker 容器"硬隔离？
>
> 我们已经做过 4 个并行 agent 的初步调研（见后文"Pre-research findings"段），但需要 ChatGPT 用 Deep Research 模式拉社区成熟意见和学术第二意见来 cross-check 我们的结论。
>
> **仓库 HEAD**：`oinani0721/canvas-learning-system` @ commit `0d05ad8`，分支 `worktree-feature-obsidian-hybrid-dev`
> **PRD 锚定**：`14-scheme-a-implementation-prd.md` §FR-CONV-06 / §3.2 errors[] / §7.1 #14 record_error
> **当前实现位置**：
> - `backend/app/services/error_extractor.py` — LLM 提取
> - `backend/app/services/error_classifier.py` — 4 主类分类（D 方案双标签）
> - `backend/app/services/error_writer.py` — frontmatter + Graphiti 双写
> - `backend/app/api/v1/endpoints/chat.py` — `POST /api/v1/chat/post-turn-extract`

---

## 🎯 给 ChatGPT 的明确指令

```
请用 Deep Research 模式回答下面 2 个问题。要求：

1. 必须搜索学术论文（含 DOI / 引用），不接受"业界普遍认为"这种无来源论断
2. 必须列出至少 5 个对照产品（带文档链接），不接受"我曾听说"
3. 我们已自己研究过 Bjork/Kapur/Bisra/NPJ Learning + Khoj/Mem0/LlamaIndex
   你需要给出**第二意见**：
   - 同意 / 反对我们的初步推荐？
   - 提出我们没考虑到的 trade-off？
   - 给出业界更激进 / 更保守的替代方案？
4. 回答必须分两部分：
   Part A: 用户主权回归方案
   Part B: 多 vault 隔离架构选择
5. 每部分末尾给"Decision Recommendation"（一句话推荐 + 工作量估算）
```

---

## 📦 项目上下文（给你的最小必要信息）

### 用户画像

- 中国大学生，自学 CS 61B（数据结构与算法）
- Python / React 代码完全靠 AI 生成，自己**不写代码**
- Obsidian 重度用户，工作流：
  - Cmd+Shift+A 批注（7 callout 类型：tip/error/question 等）
  - Cmd+Shift+D 派生新概念（建立 [[wikilink]]）
  - Cmd+Shift+C 节点对话（node-chat skill）
- 单机 self-host，Mac M5Max 16GB RAM
- **价值观**：学习数据应该是"我"的（用户主权），AI 是辅助工具不是裁判

### 系统架构

```
Obsidian Vault (canvas-vault/)
    ↓ Cmd+Shift+E (Story 2.1)
Backend FastAPI (uvicorn :8001)
    ├─ ErrorExtractor (LiteLLM → Gemini 3.1 Flash)
    ├─ ErrorClassifier (4 主类 + confidence)
    └─ ErrorWriter (双写)
        ├─ frontmatter errors[] (.md atomic write + per-file lock)
        └─ Graphiti async fire-and-forget
            └─ memory_service.record_knowledge_entity()
                └─ GraphitiEpisodeWorker (asyncio.Queue)
                    └─ graphiti_core.Graphiti.add_episode()
                        └─ Neo4j 5.26 community (bolt://localhost:7691)
                             group_id="cs_61b" (按学科动态)
```

### Story 2.5 当前 errors[] schema（YAML 实例）

```yaml
errors:
  - id: <uuid>
    dedupe_hash: <16-char sha256>
    type: conceptual_confusion           # PRD pedagogy
    legacy_type: knowledge_gap           # Story 3.6 兼容
    legacy_remedy: backtrack_definition
    description: "学生混淆了 admissibility 和 consistency"
    context: "对话第 3 轮，学习者说 'admissibility 就是 consistent 吧'"
    raw_dialog_excerpt: "学习者: ...\nAI: ..."
    confidence: 0.85
    confidence_source: llm
    remedy_strategies: [discrimination_comparison]
    tags: [synonym_confusion]
    created_at: "2026-05-04T..."
    last_seen_at: "2026-05-04T..."
    seen_count: 1
    corrected_at: null      # ⚠️ 字段存在但无 UI 触发器填充
    corrected_by: null      # ⚠️ 同上
    # ❌ 无 user_disputed 字段
    # ❌ 无 reasoning 字段（AI 为何判这是错）
```

---

## ❓ Part A · 用户主权回归方案

### A1. 张力描述

Canvas 系统中，几乎所有用户操作都是**主动**的：

| 操作 | 主动度 | 用户感受 |
|---|---|---|
| `[[wikilink]]` 双链 | 100% 主动 | "我决定哪些概念相关" |
| `Cmd+Shift+A` 批注 callout（含 `[!error]+`） | 100% 主动 | "我标记这里是错误" |
| `Cmd+Shift+D` 派生新概念 | 100% 主动 | "我让 AI 帮我生成" |
| `Cmd+Shift+E` 启动 RAG 对话 | 100% 主动 | "我决定何时聊" |
| **Story 2.5 错误自动提取** | **0% 主动（100% AI 自动）** | ⚠️ "AI 在背后判我错" |

Story 2.5 是**唯一**的 AI 中心操作，违背产品哲学一致性。

### A2. 我们的初步研究结论（请你 cross-check）

**4 篇支持"AI 不应代替用户判错"的论文**：

1. **Bjork, E. L., Dunlosky, J., & Kornell, N. (2013)** — *Annual Review of Psychology*, Vol. 64
   DOI: 10.1146/annurev-psych-113011-143823
   要点：Self-monitoring（用户自检）比 AI 告诉用户更有效。学生发现"我不会"时学习策略调整幅度最大。

2. **Kapur, M. (2016)** — *Learning and Instruction*
   要点：Productive Failure。AI 提前纠错破坏"生产性失败"机制（d=0.80 反向效应）。

3. **Bisra, K., Liu, L., Nesbit, J. C., Salimi, D., & Winne, P. H. (2018)** — *Educational Psychology Review*, meta-analysis 64 studies
   要点：用户自己解释错误 d=+0.61 vs AI 给解释的 d=+0.30+ 损失。

4. **NPJ Science of Learning (2024)** — March 2024
   要点：元认知校准（metacognitive calibration）是错误检测前提，纯 AI 自动判错跳过用户的元认知训练。

**5 个业界标杆产品调研**（横轴：纯用户 → 纯 AI）：

| 产品 | 自动度 | 错误判断权属 | 来源 |
|---|---|---|---|
| Anki | ★☆☆☆☆ | 100% 用户（5 级 SM-2） | https://faqs.ankiweb.net/what-spaced-repetition-algorithm |
| SuperMemo | ★★☆☆☆ | 85% 用户 + 15% 系统建议 | https://supermemo.guru/wiki/Incremental_reading |
| Khan Academy Khanmigo | ★★★☆☆ | Socratic 提问 + 用户反馈 | https://www.khanacademy.org/khan-for-educators/khanmigo-for-educators |
| Duolingo | ★★★★☆ | AI 判 + 用户反馈容错 | https://blog.duolingo.com/ai-improves-education/ |
| **Canvas Story 2.5（当前）** | **★★★★★** | **100% AI** | （本项目） |

→ **Canvas 处于业界极端右值**。Khanmigo / Synthesis Tutor 等对话学习产品**全部**是双轨制。

**我们的初步推荐：方案 B（AI 建议 + Modal 确认）**

```
对话结束后：
  AI 提取候选错误（带 confidence）
       ↓
  Obsidian Modal 弹出：
    "我注意到你说 admissibility = consistency。
     我把这个记录为【概念混淆】类错误，可以吗？

     [✓ 是，记录]  [✗ 否，AI 误判]  [✏️ 编辑后记录]  [跳过]"
       ↓
  根据用户选择写 frontmatter + Graphiti
       ↓
  附加字段：user_confirmed: bool, user_edit: optional[str], user_disputed: bool
```

**估算工作量：36-40h**（修改 endpoint + 新增 Modal class + Skill workflow + E2E 测试）

### A3. 给 ChatGPT 的具体问题

请回答：

**Q-A1**：我们的方案 B 对不对？还是我们应该考虑：
- **方案 D（三轨融合）**：高置信度（≥ 0.8）自动写但标 [auto-detected]；低置信度（< 0.6）才弹 modal；提供 Cmd+P `/review_errors` 手动入口
- **方案 E（仅生成 review queue）**：完全不写 frontmatter，只生成"待审错误队列"在 Dashboard，用户主动 review 后才正式记录
- **方案 F（AI 不写但提示）**：AI 检测到错误后只在对话中说"我觉得你刚才搞混了 X 和 Y，要我记录吗？"，让用户用 Cmd+Shift+A 自己批注

**Q-A2**：4 篇学术论文我们已找到。请补充：
- 2024-2026 年关于 "AI tutor + user agency" 的最新论文（特别是大模型时代的）
- 反方观点（支持纯 AI 自动判错的论文，如有）
- 教育心理学界对"AI 错误检测的双盲研究"（用户接受度量化数据）

**Q-A3**：业界 5 个产品中，**Khanmigo 和 Synthesis Tutor 在 2025-2026 的最新更新**是不是也用双轨？请提供：
- 具体 UI 截图描述（modal 长啥样）
- 用户 onboarding 怎么解释"AI 会判你错"这件事
- 用户能否关闭这个功能

**Q-A4**：从产品营销角度，"AI 全自动检测"和"AI 建议+你确认"哪个更容易被付费用户接受？有 A/B test 数据吗？

**Q-A5**：如果选方案 B，我们应该担心**用户疲劳**吗？
- 如果 AI 每对话 1 轮就弹 modal 1 次，会不会让用户烦
- 业界经验：modal 弹出频率 / 容忍度（数据点：Duolingo / Anki 评分弹窗节奏）
- 是否应该 batch（每 5 轮对话或对话结束才一次性 review）

---

## ❓ Part B · 多 Vault 隔离架构选择

### B1. 张力描述

用户问："是否一个 vault 启动一个 docker 容器来进行记录？"

这本质是**隔离粒度选择**：

```
选项 A（当前）：1 容器 + Graphiti group_id 软隔离
  Neo4j ──┬─ group_id="cs_61b"   (vault A: CS 61B)
          ├─ group_id="数学"      (vault B: Math 60)
          └─ group_id="ml"        (vault C: ML)

选项 B（用户提议）：N 容器，物理强隔离
  Neo4j-cs61b ──── vault A
  Neo4j-math  ──── vault B
  Neo4j-ml    ──── vault C
  (每容器独立内存 + 独立 docker volume + 独立端口)

选项 C：1 容器 + Neo4j 多数据库
  ❌ 不可行：Neo4j Community 不支持多数据库（Enterprise $10k+/年）
```

### B2. 我们的初步研究结论（请你 cross-check）

**5 维评估**：

| 维度 | A 单容器+group_id | B 一 vault 一容器 | C Neo4j 多库 |
|---|---|---|---|
| 隔离强度 | ⭐⭐ 软隔离 | ⭐⭐⭐⭐⭐ 物理强 | ⭐⭐⭐ 数据库级 |
| Mac M5Max 16GB 友好 | ✅ 7.3G | ⚠️ 3 vault 已 10.9G | ❌ 需 Enterprise |
| 切 vault 体验 | ✅ 无缝（API） | ❌ docker stop/start 30-60s | ✅ 无缝 |
| 端口管理 | ✅ 7691 一组 | ❌ 多 vault 端口段规划 | ✅ 一组 |
| 实现成本 | 0h | 30-50h | 不可行 |

**业界类似产品调研（5 个）**：

| 产品 | 多 vault 方案 | 链接 |
|---|---|---|
| Khoj (Obsidian self-hosted) | 1 容器 + group_id 软隔离 | https://github.com/khoj-ai/khoj |
| Mem0 (企业 RAG) | 1 容器 + org_id 多租户 | https://github.com/mem0ai/mem0 |
| LlamaIndex + Weaviate | 1 容器 + collection schema 隔离 | https://docs.llamaindex.ai/ |
| Obsidian Smart Connections | 无容器（纯插件） | https://github.com/brianpetro/obsidian-smart-connections |
| Obsidian Copilot | 无容器，全局索引（不隔离） | https://github.com/logancyang/obsidian-copilot |

→ **零个**业界 Obsidian + 知识图谱产品采用"一 vault 一容器"。Khoj / Mem0 / LlamaIndex 都是 group_id 软隔离。

**Graphiti group_id 隔离强度调研**（5 维）：

| 维度 | 评估 | 强度 |
|---|---|---|
| Namespace 概念 | `delete_by_group_id()` 原子删除 → 是命名空间级 | ⭐⭐⭐⭐ |
| 查询过滤 | `search(query=..., group_ids=["A","B"])` 参数化绑定 | ⭐⭐⭐⭐ |
| 跨 group_id 合并查询 | 支持，但建议默认隔离 | ⭐⭐⭐ |
| 删除/修改隔离 | 强（per-group atomic） | ⭐⭐⭐⭐⭐ |
| 命名冲突 | 同名概念在不同 group_id = 不同 node UUID | ⭐⭐⭐⭐⭐ |

**真正的隔离漏洞（不是容器问题）**：

1. ⚠️ **LanceDB 向量搜索没传 group_id 过滤** → 跨 vault 数据可能在向量召回时混入
2. ⚠️ Backend 部分 Cypher 查询忘传 group_id → 跨学科污染（防御编码不严）
3. ⚠️ 项目内 group_id 命名不统一：CLAUDE.md 写 `canvas-dev`、代码默认 `cs188`、生产推断 `cs_61b`

**我们的初步推荐：维持选项 A（单容器 + group_id），但修 3 个漏洞**

**估算工作量**：
- 修 LanceDB group_id 过滤：4-6h
- Cypher 防御性 group_id 注入审计：6-8h
- group_id 命名统一：2-4h
- 总计 12-18h

### B3. 给 ChatGPT 的具体问题

请回答：

**Q-B1**：我们维持单容器 + 修漏洞的推荐对不对？还是我们应该考虑：
- **方案 D（混合）**：单容器 + group_id 隔离 + per-group 加密 key（防止管理员看其他 vault）
- **方案 E（federated）**：单容器但 Graphiti 启动多个 instance 共享 Neo4j（Graphiti MCP server 支持 `--group-id` 启动参数，每 vault 一个 MCP）
- **方案 F（local-first）**：放弃 Neo4j，用 Kuzu（嵌入式图数据库）+ DuckDB → 每 vault 一个本地数据库文件，零容器开销

**Q-B2**：Neo4j Community 在我们预期数据量级（10 vault × 100 概念 × 10 错误 = 10k node）下：
- 实际响应时间是 100ms 还是更高？
- 单容器是否会因 vault 数增加而退化（cache pollution / GC pressure）？
- 是否有真实用户跑 self-hosted Khoj/Mem0 的性能数据？

**Q-B3**：用户提到的"一 vault 一容器"在 self-hosted 圈子里有没有先例？
- Selfhosted Obsidian 圈（r/selfhosted, r/ObsidianMD）有人这么做吗？
- LangChain / LlamaIndex 的 self-hosted multi-tenant 文档怎么说？
- Zep AI（Graphiti 母公司）的企业部署是单容器还是多容器？

**Q-B4**：从备份 / 灾难恢复角度：
- 单容器 Neo4j Community 备份只能全量离线（停服）？
- 多容器是否在备份粒度上更友好？
- 用户实际丢数据风险评估（per-vault 备份 vs 全量备份的恢复时间对比）

**Q-B5**：未来 cloud sync 场景（用户从 Mac 迁到 Windows + iPad）：
- 单容器 group_id 隔离能不能直接挪到 cloud？
- 多容器在 cloud 上是否反而更简单（每用户一个 Neo4j AuraDB instance）？

---

## 📐 Desired Output Format

请按以下结构输出：

```markdown
# ChatGPT Deep Research Reply — Story 2.5 Sovereignty + Isolation

## Part A · 用户主权回归

### A1. 我们方案 B 的评估
- 同意 / 反对 / 部分同意：______
- 主要理由：______

### A2. 你建议的方案
- 推荐方案：B / D / E / F / 其他 _____
- 推荐理由（2-3 句）：______
- 实施工作量估算：____ h

### A3. 学术论文补充（2024-2026 最新）
- 论文 1：[作者, 年] - [标题] - [DOI/URL]
  - 关键发现：______
- 论文 2：______
- 反方观点（如有）：______

### A4. 业界产品最新动态（2025-2026）
- Khanmigo 最新双轨 UI：______
- Synthesis Tutor 最新策略：______
- 其他值得参考的产品：______

### A5. 用户疲劳风险评估
- 风险等级：低 / 中 / 高
- 缓解措施：______

### A · Decision Recommendation
> 一句话：______（含工作量）

---

## Part B · 多 Vault 隔离

### B1. 我们方案 A（单容器+修漏洞）的评估
- 同意 / 反对 / 部分同意：______
- 主要理由：______

### B2. 你建议的方案
- 推荐方案：A / D / E / F / 其他 ______
- 推荐理由：______

### B3. 性能数据
- 10k node 响应时间：______
- Khoj/Mem0 真实用户数据：______

### B4. self-hosted 圈先例
- 一容器一 vault 是否有人做：______
- Zep AI 企业部署：______

### B5. 备份 / 云同步
- 单容器备份策略：______
- 云同步迁移路径：______

### B · Decision Recommendation
> 一句话：______（含工作量）

---

## 总体建议（一段话总结）

______
```

---

## 🚧 我们已确认的 hard constraints（不要建议改这些）

1. ⛔ Obsidian + Markdown vault 是不可变的载体（不接受 Notion / 私有云）
2. ⛔ 后端必须 Python FastAPI async（不接受重写为 Node.js / Go）
3. ⛔ Neo4j 不接受换成 ArangoDB / FalkorDB（已锁 Graphiti SDK 依赖）
4. ⛔ LLM 必须支持 LiteLLM（不绑死单一 provider）
5. ⛔ Graphiti 内部 LLM 硬锁 Gemini（episode_worker.py:287-394）
6. ⛔ self-host 优先，cloud 是 Phase 3 才考虑

---

## 🔗 给 ChatGPT 的可 fetch URL

```
# Story 2.5 后端核心代码（最新 ship commit 0d05ad8）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/backend/app/services/error_extractor.py
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/backend/app/services/error_classifier.py
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/backend/app/services/error_writer.py
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/backend/app/api/v1/endpoints/chat.py
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/backend/app/graphiti/entity_types.py

# Story 2.5 UAT 验收单
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/_bmad-output/验收单/Story-2.5-error-extraction.md

# docker-compose.yml（多容器架构问题相关）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/docker-compose.yml

# CLAUDE.md（用户哲学和约束）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/CLAUDE.md
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/0d05ad8/_bmad-output/.claude/CLAUDE.md
```

---

## 📅 时间盒

请在 30-45 分钟内完成 Deep Research，预算：
- 学术论文搜索：10-15 篇 abstracts
- 业界产品文档：5-10 个
- self-hosted 论坛搜索：3-5 个 thread

**预计返回长度**：3000-5000 字。

**审查后的下一步**：用户基于 ChatGPT 反馈在 §12 决策区批注 D15 决策，Claude Code 据此 ship Story 2.5.X（用户主权回归）+ Story 2.5.Y（隔离漏洞修复）。

---

> **生成时间**：2026-05-04
> **生成人**：Claude Code (Opus 4.7)
> **触发原因**：用户在 Story 2.5 UAT 阶段提出 2 个核心质疑，4 并行 Explore agent 已完成初步调研，需 ChatGPT 给第二意见 cross-check
> **关联 commit**：`0d05ad8`（最新 ship HEAD）
