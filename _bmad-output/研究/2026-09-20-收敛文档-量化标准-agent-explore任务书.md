# 收敛文档 · 量化标准社区调研 + Agent-Explore 任务书

> 发起：用户批注（`验收单/UAT-CARD-G8-7-2026-09-20-车道回复-2.md:32-48`）· 整理：DeepSeek 车道 · 日期：2026-09-20
> 用户逐字要点：「我会用 Obsidian **块引用**提取材料 → 用 CLS **打批注**写理解 → （必要时）**新建节点**；需要 AI **主观推断**：块引用干了什么、批注打了什么；最终要一份**设计良好的收敛文档**（**给人看，不是给 AI 看**）；两诉求 = (a) 回顾防遗忘（阅读体验只能我强化学习自评）、(b) 查漏补缺+精准推荐（AI 要明确知道我的目标）；**除主观打分外，还有什么量化标准？去社区调研**」

---

## 1. 本次要回答的 4 问

| # | 问题 | 现状 |
|---|---|---|
| Q1 | 「回顾/防遗忘」：除主观打分+RL 外，有无客观量化标准？ | 首轮已命中 4 个成熟范式（见 §2） |
| Q2 | 「查漏补缺」：覆盖度/缺口怎么量化？且必须挂"**目标基准**" | 首轮命中 PRISMA-ScR（见 §2.6） |
| Q3 | 「偏好推断+精准补充」：用户偏好怎么量化（显式/隐式）？ | 有学术面（RecSys 兴趣漂移），待 explore 深挖 |
| Q4 | 「给人看的收敛文档」：信息设计上有没有可抄的骨架与校验标准？ | 社区有大量 review 模板，待系统收编 |

## 2. 首轮社区检索已命中（种子证据 · 全部带源）

| # | 范式 | 量化标准（原文要点） | 对应 | 源 |
|---|---|---|---|---|
| 2.1 | **Progressive Summarization**（Tiago Forte） | **层数漏斗比**：L1 的 1/2 → L2；L2 的 4/5 → L3；L3 的 1/4 → L4（= 原材料的 5%）；<1% → L5；L3 层复读比 L1 **快 6–12×** | Q1/Q4 | fortelabs.com（正文 I–VI 系列） |
| 2.2 | **SuperMemo 增量阅读** | 每篇文章带 **priority**；默认目标 **95% 保留**；extract/item 优先于原文；统计页按优先级看保留率 | Q1/Q2 | help.supermemo.org（Incremental reading / Statistics） |
| 2.3 | **SuperMemo 增量写作 / consolidation** | 「**Consolidation is not measured on a single day**」；topics 应只占复习元素的少数 | Q1 | supermemo.guru（Incremental writing） |
| 2.4 | **Readwise Daily Review** | 当一条 highlight 的**回忆概率衰减到 ≤50%** 才被重浮；日回顾 ~5 分钟；"你会忘记 75%"框架 | Q1 | docs.readwise.io |
| 2.5 | **Anki True Retention / FSRS** | **true retention = 复习卡通过率**，应贴近 desired retention；看月数据不看单日 | Q1/Q3 | docs.ankiweb.net/stats.html |
| 2.6 | **PRISMA-ScR（范围综述）** | 20+2 项清单 + **流程图（识别→筛查→纳入→排除）** + PCC 框架 = 覆盖度/缺口核算的行业标准 | Q2 | prisma-statement.org/scoping |
| 2.7 | 推荐系统学术侧（候选面） | 兴趣漂移 / **兴趣遗忘** 建模、稀疏兴趣冷启动、可解释推荐（LLM-personalization） | Q3 | MDPI/arXiv/ScienceDirect 各一篇（待 explore 收窄） |

## 3. Agent-Explore 分路（4 路并行）

> **统一产出格式**（每路每条）：`方法/指标名` · 一句话定义 · **如何测量（公式或操作步骤）** · 适用哪一问 · **证据等级**（一手/官方／社区自述／二手转述） · 链接+日期 · **迁移到 CLS 的具体形态（≤2 句）** · 反例/失败边界。
> **统一边界**：⛔ 不评 CLS 设计本身、不改任何 skill/代码、不做终审、不搬运无出处的"指标"；社区自述一律标来源与日期。

### 路线 A · 「回顾/防遗忘」的量化标准（Q1）
- **搜索面**：SuperMemo / Anki / Readwise 官方文档与统计页；r/Anki、forum.obsidian.md、zettelkasten.de；学术：spacing effect、retrieval practice、desirable difficulty
- **关键词**：retention rate 公式 / true retention / review load / backlog / lapse rate / 间隔效应 / 回忆通过率 / 复习负担
- **底线产出**：≥6 条量化标准，其中 **≥2 条可直接搬进收敛文档当页头指标**

### 路线 B · 「查漏补缺」的覆盖度量化（Q2）
- **搜索面**：PRISMA-ScR / JBI / Cochrane（一手）；Rayyan、Covidence（工具）；"gap map / evidence gap map"；Obsidian 侧：Dataview 未链接提及（unlinked mentions）、孤儿笔记
- **底线产出**：≥5 条；并给出「**目标基准**」的 3 种可行来源（你的 research_questions／板的目标段／外部对照语料）

### 路线 C · 「偏好推断 + 精准补充」的量化（Q3）
- **搜索面**：RecSys（兴趣漂移/冷启动/可解释）；LLM-personalization；Readwise、Matter、Reflect 等"**什么被重浮**"的机制；HCI 的 PIM/re-finding 研究
- **底线产出**：≥5 条；并明确区分「**你能接受的最小显式打分**」（1–5 / 三元 / 二元）与「**纯隐式信号**」（停留、重读、块引用、批注类型）的**成本与偏差**各一条

### 路线 D · 「给人看的收敛文档」信息设计（Q4）
- **搜索面**：weekly review 模板（GTD / Things / Obsidian 社区）；实验室笔记规范；review article 写法；Readwise / Reflect 的回顾页实拍
- **底线产出**：≥5 个可抄的版面骨架 + 各自适配的阅读时长（≤90 秒 / 5 分钟 / 深读），并标"哪一版最省脑力"

## 4. 收口要求（explore 汇总时）
1. **总表**：指标 × 定义 × 测量 × 对应问题 × 证据等级 × 是否建议进 MVP；
2. **诚实边界**：明确哪些**只能自评**（R5 精神），哪些可用客观指标**代理**；
3. **反例清单**：社区里"折腾了指标但失败"的案例 ≥3 条（防指标崇拜）。

## 5. 启动方式（复制即用）
- 每路一段 prompt（建议模板）：

```
你是 CLS「收敛文档」设计的探索 agent（路线 X：<A|B|C|D>）。
目标问题：<粘贴 §1 的 Qn>。
产出格式（每条）: 方法/指标名 · 定义 · 如何测量 · 适用问题 · 证据等级 · 链接+日期 · 迁移到 CLS 的具体形态 · 反例。
边界：只收集、不评设计、不写代码；社区自述标来源与日期；无出处的不写。
写入：_bmad-output/审查/evidence-conv-<A|B|C|D>/<topic>.md（只写自己目录）。
```

- **harness**：Claude Code / Codex / pi 任一皆可（并行 4 路）；
- **汇总**：车道（DeepSeek）汇总 → GLM-5.3 复核（专门检查"指标崇拜"与出处）。

## 6. 车道对你 4 点批注的初步答复
1. **你的拆分流程**（块引用 → 批注 → 新节点）链路成立。要让 AI 推断「块引用干了什么」，需要把**块引用痕迹**固化成可解析字段：节点内 `[[file#^block]]` / `![[file#^block]]` 的出现 + 批注 callout + 派生关系（`derived-from`）——这就是三期适配的**输入面**。
2. **"给人看，不是给 AI 看"** 已写为硬要求：收敛文档第一读者 = 你；AI 只读它的摘要/指标（双面文档）。
3. **Q1 有客观标准可借**（2.1/2.2/2.4/2.5）；建议 MVP 先用三件：**重浮率 + 保留率 + 漏斗比**，其余等 explore 结论。
4. **Q2/Q3 都缺"目标基准"**：你已给出一个（research_questions/目标段）；PRISMA-ScR 的覆盖核算 + RecSys 的兴趣漂移建模是两条候选主线。
