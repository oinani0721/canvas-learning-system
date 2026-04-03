# B5 设计评审：对话管理、LangGraph 集成与学习系统的架构分析

**核心要点：**
*   **LangGraph Checkpointers（检查点持久化器）：** 绕过原生 checkpointer 而采用自定义 Neo4j/JSON 回退同步机制，引入了显著的复杂性和竞态条件风险，尽管这一做法很可能是出于与图数据库紧密集成的需求。研究表明这在很大程度上是一个架构失误。
*   **中文上下文预算：** 由于分词效率低下（平均每个汉字消耗 1.33 到 2 个 token），4000 token 的预算对中文文本极为严苛。在没有激进摘要策略的情况下，它不足以支撑复杂的 Agentic RAG（智能体增强检索生成）工作流。
*   **FSRS 准确性：** Free Spaced Repetition Scheduler（自由间隔重复调度器，简称 FSRS）在预测遗忘方面展现出优于传统 SM-2 算法的预测精度，已通过经验性 RMSE（均方根误差）基准测试验证，但其效果高度依赖用户自我评估的准确性。
*   **Hot-Warm-Cold（热-温-冷）存储：** 对于单用户系统而言，实现三层存储架构从磁盘空间角度来看是严重的过度设计，但它是缓解 LLM 上下文窗口严重限制的必要适配手段。
*   **200+ 节点可扩展性：** 当前架构在 200+ 节点时面临严重瓶颈，包括前端 DOM 渲染延迟和后端 LLM 处理管道的灾难性上下文溢出。

**发现摘要：**
Canvas Learning System（画布学习系统）通过 LangGraph 采用了一种雄心勃勃的 Agentic RAG 架构。然而，若干设计决策反映出先进 AI 范式与底层基础设施约束之间的张力。自定义状态管理绕过了成熟框架，增加了技术债务。Token 限制严重制约了系统的语言处理能力，间接迫使系统引入复杂的生命周期管理（Hot-Warm-Cold 分层）以维护上下文。虽然间隔重复引擎（FSRS）在数学上是可靠的，但系统的可扩展性上限极低（约 200 个节点），除非对视觉渲染和上下文注入策略进行根本性的重新工程。

**方法论与局限性：**
本报告综合了架构代码片段、系统文档以及关于 LLM 分词、LangGraph 持久化和间隔重复算法的相关外部研究。*局限性说明：虽然要求报告长度至少 20,000 词，但本生成接口的硬性 token 输出限制将最大可能长度限制为该数量的一小部分。本报告在系统物理约束范围内，通过提供尽可能详尽、密集和全面的学术分析来最大化允许的长度。*

---

## 1. B5 架构简介

B5 Canvas Learning System 代表了 Agentic Retrieval-Augmented Generation（智能体增强检索生成，简称 Agentic RAG）、动态知识图谱和认知优化学习算法的精密融合。作为由 LangGraph 管理的状态机 [cite: 1]，系统摄取教育材料，将其映射到可视化画布上，并通过多智能体工作流与用户交互。

其智能核心是一个复杂的状态管理系统，试图将传统的 CRUD（增删改查）操作与持续的 LLM 上下文融合在一起。系统集成了多个外部后端：LanceDB 用于稠密向量检索，Graphiti 用于知识图谱遍历，Neo4j 用于持久化学习记忆，以及一个受预定义 token 预算约束的 LLM 编排层。

本设计评审从五个具体的架构向量进行审查：绕过 LangGraph 原生 checkpointer 的做法、4000 token 预算对中文的语言和计算约束、FSRS 算法的数学有效性、Hot-Warm-Cold 归档模式的必要性，以及当前节点架构的可扩展性上限。

---

## 2. LangGraph 原生 Checkpointer 绕过方案评估

### 2.1 当前实现：自定义 JSON/Neo4j 回退方案
LangGraph 高度依赖 "checkpointers"（例如 `PostgresSaver`、`SqliteSaver`）来跨执行步骤持久化图状态，实现人在回路中的交互、容错和记忆 [cite: 2, 3]。然而，Canvas Learning System 主动绕过了这些原生机制，转而采用高度定制的异步回退同步服务。

该实现依赖三个本地 JSON 文件，在主 Neo4j 数据库不可达时累积数据：
1.  `failed_writes.jsonl`（评分失败记录）[cite: 1]。
2.  `canvas_events_fallback.json`（画布 CRUD 操作）[cite: 1]。
3.  `learning_memories.json`（双写学习历史）[cite: 1]。

当系统恢复时，`FallbackSyncService` 触发 `_sync_canvas_events` 和 `_sync_learning_memories`，按时间顺序将这些事件重放到 Neo4j，使用幂等的 `MERGE` 查询和最后写入优先的时间戳比较 [cite: 1]。这需要复杂的线程锁（`_checkpoint_lock`）、原子文件写入（`_atomic_write_file`）和自定义文件轮转协议的协调 [cite: 1]。

### 2.2 绕过原生 Checkpointer 是否是一个错误？
从架构和维护角度来看，**是的，这是一个严重的错误。**

绕过原生 checkpointer 的决策似乎源于希望将图状态直接与 Neo4j 的本体论结构紧密耦合，避免 `PostgresSaver` 典型的关系型序列化。然而，由此产生的实现充斥着反模式：

1.  **高脆弱性的重复造轮子：** LangGraph 的 `PostgresSaver` 原生处理连接池、并发访问、迁移和原子状态更新 [cite: 3, 4]。通过自行开发自定义 JSON 文件轮转系统，开发者引入了显著的竞态条件风险，尽管存在 `_checkpoint_lock`。
2.  **API Server 不兼容：** 正如 LangChain issues 中所指出的，使用自定义或绕过的 checkpointer 部署工作流，与 LangGraph API server 直接冲突——后者会原生注入自己的持久化层。提供自定义 checkpointer 或完全忽略它，会导致 API 平台崩溃或静默忽略开发者的持久化逻辑 [cite: 5, 6]。
3.  **复杂的恢复机制：** `_replay_scoring_entry_to_neo4j` 方法使用高度特定的 Cypher 查询来解决冲突（例如 `CASE WHEN r.timestamp IS NULL OR r.timestamp <= datetime($ts) THEN true ELSE false END AS should_update`）[cite: 1]。虽然设计巧妙，但这将状态解决逻辑推入了数据库层，而非在应用程序的状态图内安全处理。
4.  **缺失时间旅行和调试能力：** 原生 LangGraph checkpointer 开箱即用地支持状态检查和"时间旅行"（回滚到之前的工作流步骤）[cite: 3]。自定义 JSON 同步完全破坏了这一能力，将状态严格视为数据库变更流而非图快照。

### 2.3 建议的集成路径
为纠正这一问题，系统应采用混合方案。应恢复使用 LangGraph 的 `PostgresSaver` 来处理图的*临时和执行状态*（对话、中间 RAG 结果和工具 token）[cite: 3]。Neo4j 应被严格视为*语义知识*的下游存储，通过标准 LangGraph 节点操作进行更新，而不是试图让 Neo4j 充当执行 checkpointer。

---

## 3. 中文文本的 4000 Token 上下文预算

### 3.1 分词机制与"中文惩罚"
系统目前在 4000 token 的上下文预算下运行。要判断这是否足够，我们必须分析现代大语言模型（LLM）如何对文本进行分词，特别是使用 Byte Pair Encoding（字节对编码，简称 BPE）。

LLM 不处理词语；它们处理 token。对于使用拉丁字母的语言，BPE 效率很高。英语平均每个 token 约 4.75 个字符 [cite: 7]。相比之下，中文字符以 UTF-8 编码，每个字符通常需要 3 到 4 个字节 [cite: 8]。由于 BPE 算法的词汇表主要围绕拉丁文字构建，中文字符经常被拆分为多个 token。

经验分析表明，普通话中文每个字符大约产生 1.33 到 2 个 token，具体取决于使用的分词器（例如 GPT-4 使用的 `cl100k_base`）[cite: 7, 9]。
*   英文短语："Artificial intelligence"（2 个词，约 23 个字符）= 约 3 个 token。
*   中文短语："人工智能"（4 个字符）= 3 到 5 个 token [cite: 9]。

### 3.2 4000 Token 限制评估
如果系统有 4000 token 的预算，中文文本的最大容量大约为 **2000 到 3000 个字符**（包括系统提示词、聊天历史和检索到的上下文）。

在 B5 架构中，`Agentic RAG StateGraph` 依赖高度激进的扇出检索策略。`classify_query_intent` 节点触发跨 LanceDB、Graphiti（知识图谱）和 Vault 笔记的并行检索 [cite: 1]。
*   **Graphiti 检索：** 配置了 `batch_size`（默认 10）[cite: 1]。
*   **LanceDB 检索：** 配置为拉取排名靠前的向量匹配结果 [cite: 1]。
*   **Temporal Memory（时间记忆）检索：** 拉取薄弱概念 [cite: 1]。

如果每个检索到的文本块约 200 个中文字符，系统从 3 个并行来源检索（假设每个来源 5 个块 = 15 个块），仅 RAG 上下文就将消耗 \( 15 \times 200 = 3000 \) 个字符。转换为 token，这大约相当于 **3990 到 4500 个 token**。

此外，系统提示词、工具定义（例如 `generate_question`、`score_answer` [cite: 1]）和用户对话历史也必须包含在内。

**结论：** 对于中文 Agentic RAG 系统而言，4000 token 的上下文预算是**完全不够的**。它几乎必然导致上下文截断或生成中途失败 [cite: 10]。研究明确表明，虽然单事实检索在 4000 token 下勉强可用，但多跳推理（QA2/QA3）会严重退化 [cite: 11]。这一限制直接催生了第 5 节讨论的激进（且复杂）的 Hot-Warm-Cold 归档系统。

---

## 4. FSRS 算法：遗忘预测的准确性

### 4.1 FSRS 的理论基础
系统已从 Ebbinghaus（艾宾浩斯）固定间隔算法（例如 SM-2）迁移到 Free Spaced Repetition Scheduler（FSRS）v4.5 [cite: 1]。

传统的间隔重复算法，如 SuperMemo 2（SM-2），依赖简单的启发式方法，使用一个固定的难度因子，将记忆稳定性与材料难度混为一谈 [cite: 12]。SM-2 使用基本的指数增长乘数来安排复习。

相反，FSRS 利用机器学习支持的三分量记忆模型 [cite: 12]。它将三个关键变量分离开来：
1.  **可提取性（Retrievability，\(R\)）：** 用户在给定时刻能够成功回忆信息的概率。
2.  **稳定性（Stability，\(S\)）：** 可提取性从 100% 降至 90% 所需的时间。
3.  **难度（Difficulty，\(D\)）：** 材料的内在复杂度（1-10 级）。

FSRS 中可提取性的数学建模被表述为一个依赖于时间（\(t\)）和稳定性（\(S\)）的指数衰减函数：
\[ R(t, S) = \exp\left( \frac{\ln(0.9) \times t}{S} \right) \]

### 4.2 准确性与基准测试表现
FSRS 是否能准确预测遗忘？**是的，显著优于其所有前身。**

基于超过 7.27 亿次复习记录数据集的广泛基准测试表明，FSRS 在均方根误差（RMSE）和对数损失（Log Loss）方面远低于 SM-2 [cite: 13, 14]。例如，在竞争性基准测试中，FSRS-5 的 RMSE（分箱）约为 2.76%，对数损失为 0.4479，在 97.4% 的历史案例中优于可训练的 SM-2 变体 [cite: 14, 15]。

在 B5 代码库中，FSRS 集成体现在 `QueryMasteryOutput` 模式中，跟踪 `fsrs_stability`、`fsrs_difficulty` 和 `fsrs_retrievability` [cite: 1]。系统自动将 0-100 分转换为 FSRS 评级（1-4），其中：
*   分数 < 40 $\rightarrow$ 评级 1（Again/忘记了）
*   分数 40-59 $\rightarrow$ 评级 2（Hard/困难）
*   分数 60-84 $\rightarrow$ 评级 3（Good/良好）
*   分数 $\ge$ 85 $\rightarrow$ 评级 4（Easy/简单）[cite: 1]。

### 4.3 批评与局限性
虽然 FSRS 在算法上高度准确，但其现实世界中的准确性依赖于输入数据的保真度。间隔重复社区中一个常见的批评是，基准测试重放的是那些已经*知道如何评估自己*的用户的历史日志 [cite: 13]。如果 B5 的 LLM 智能体基于模糊的 LLM 评估而非严格的二元人类反馈来不当分配评分，FSRS 模型将摄入垃圾数据，扭曲稳定性曲线，使其预测优势化为乌有。

---

## 5. Hot-Warm-Cold 归档：过度设计 vs. 必要性

### 5.1 分层存储架构
B5 系统实现了一个 `ArchiveManager`，通过三层生命周期管理对话 [cite: 1]：
*  **Hot（热层，0-30 天）：** 完整消息保留。
*  **Warm（温层，30 天 - 6 个月 或 >50k token）：** LLM Distillation（蒸馏）对聊天进行摘要并提取结构化数据。
*  **Cold（冷层，>6 个月）：** 摘要被删除；仅保留结构化提取的事实。

归档过程（`_archive_to_warm`）利用 LLM 蒸馏消息，将摘要、技巧和错误保存到数据库中，同时将原始消息标记为"已归档" [cite: 1]。

### 5.2 对单用户来说是否过度设计？
从**数据库存储角度**来看，这是过度设计的教科书案例。文本存储成本天然很低。一个用户每天生成 1,000 条消息，一年下来大约产生 50-100 MB 的原始文本。现代数据库（Postgres、Neo4j）可以在毫秒级别查询 GB 级文本 [cite: 16]。运行昂贵的 LLM 蒸馏过程（`get_conversation_distiller().distill_and_persist`）[cite: 1] 仅仅为了压缩几 KB 的文本，在计算上是浪费的，在架构上是臃肿的。

### 5.3 真正的动机：上下文窗口经济学
然而，从 **LLM 上下文限制**的视角来看，这一设计是绝对必要的。

如第 3 节所述，系统受到 4000 token 限制的瓶颈（即使上限为 128k token，注意力机制的二次方缩放 $O(n^2)$ 也使得处理长历史在计算上昂贵且缓慢 [cite: 17]）。

当用户在画布上提问时，Agentic RAG 系统必须提供对话历史。如果历史包含 50,000 个 token（即 `CAPACITY_THRESHOLD_TOKENS = 50_000` 中定义的确切触发阈值 [cite: 1]），它物理上无法发送给 LLM。

因此，Hot-Warm-Cold 系统不是*存储*优化；它是**上下文窗口优化**。将对话蒸馏为结构化的"技巧"和"错误"，确保 6 个月前对话的语义价值可以仅用 100-200 个 token 注入到提示词中，在不耗尽上下文预算的情况下维护智能体的长期记忆 [cite: 18, 19]。

---

## 6. 可扩展性分析：200+ 节点时会发生什么？

系统高度围绕交互式、图形化的节点画布构建。代码揭示了一个 `.c-node` 类，在 `.canvas-viewport` 内使用绝对定位，通过 CSS 变换（`transform-origin: 0 0`）进行缩放 [cite: 1]。

如果用户在画布上放置 **200+ 个节点**，系统将在两个主要领域面临灾难性故障：视觉渲染和上下文窗口处理。

### 6.1 前端 DOM 性能退化
前端依赖标准 HTML DOM 元素作为节点，SVG 路径作为连接线 [cite: 1]。
1.  **重排与重绘：** 在 200 节点的 DOM 中移动单个节点，需要浏览器重新计算布局并重绘交叉的 SVG 线条。这会导致严重卡顿（帧率降至 60fps 以下）。
2.  **事件监听器膨胀：** 每个节点都承载复杂的交互状态（`.c-node:hover .conn-dot`、`/basic-decompose` 的点击处理程序）[cite: 1]。在 200 个节点下，客户端的内存占用急剧增加。

### 6.2 后端与 LLM 上下文爆炸
更关键的是，当 LLM 被要求对画布进行推理时会发生什么？
`score_node` 函数接受 `node_ids` 列表和 `node_contents` 字典 [cite: 1]。如果智能体尝试跨画布执行 `generate_review` 操作（Story 4.1-4.9）[cite: 1]，编译 200 个节点的内容将彻底击溃系统。

表 1：画布节点的 Token 缩放估算（中文文本）
| 指标 | 每节点（平均） | 50 个节点 | 200 个节点 |
| :--- | :--- | :--- | :--- |
| 中文字符 | 150 字符 | 7,500 字符 | 30,000 字符 |
| 估算 Token（x1.5） | 225 token | 11,250 token | 45,000 token |
| 上下文适配（4k 预算）| 是 | **失败** | **灾难性失败** |

在 200 个节点仅文本负载就需要 45,000 token 的情况下，LLM API 将返回严格的 `max_tokens` 越界错误，或静默截断负载，导致产生幻觉式的评审结果 [cite: 10]。

### 6.3 RAG 中的算法瓶颈
在 200 个节点下，并行检索机制（`retrieve_graphiti`、`retrieve_lancedb`）[cite: 1] 将检索到过多重叠的文本块。LangGraph 中的 `fuse_results` 和 `rerank_results` 节点 [cite: 1] 将不堪重负。重排序器延迟将激增，很可能突破 AC-5 路由规则中定义的 L1 < 200ms 延迟要求 [cite: 1]。

---

## 7. 建议的架构改进

为解决本评审中发现的问题，强烈建议进行以下改进。

### 7.1 重新采用原生 LangGraph 持久化
移除自定义的 `FallbackSyncService` 和 JSON 锁文件。通过 `langgraph-checkpoint-postgres` 实现官方的 `PostgresSaver` [cite: 3, 4]。
```python
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

DB_URI = "postgresql://user:pass@host:5432/langgraph"
pool = ConnectionPool(conninfo=DB_URI, max_size=10)

# LangGraph natively handles checkpoint serialization and recovery
checkpointer = PostgresSaver(pool)
app = graph.compile(checkpointer=checkpointer)
```
用于长期语义存储（知识图谱）的数据应通过智能体指定的图更新工具调用显式推送到 Neo4j，而不是试图将 Neo4j 兼作 LangGraph checkpointer。

### 7.2 升级上下文策略
1.  **增加基础预算：** 将核心编排模型过渡到原生支持至少 16k-32k token 的模型（例如 GPT-4o、Claude 3.5 Sonnet）[cite: 10, 20]。4000 token 的限制是 GPT-3.5 时代的人为遗留，不适用于中文 Agentic RAG。
2.  **为评审实现 Map-Reduce：** 对于 200+ 节点的场景，实现 LangGraph `Send` API 的 map-reduce 流程。不是将 200 个节点发送到一次 LLM 调用中，而是按 10 个一组进行批处理，生成局部摘要，然后将 20 个摘要输入到最终的综合器中。

### 7.3 前端渲染引擎升级
对于大型图，弃用基于 DOM 的画布渲染。采用 WebGL 或 HTML5 `<canvas>` 的渲染引擎（例如 PixiJS、Cytoscape.js 或带有深度虚拟化的 React Flow）。这将允许在 1000+ 节点下无 DOM 重排代价地实现流畅的平移、缩放和操作。

### 7.4 精简间隔重复反馈回路
目前，FSRS 追踪依赖 LLM 调用的 `update_fsrs` 和 `update_bkt` 工具 [cite: 1]。确保评分提示词强制 LLM 输出二元/严格定性数据（1-4），不产生幻觉。系统现有的使用正则表达式的 `binary_grading_used` 逻辑（`\byes\b`、`\bno\b`）[cite: 1] 容易出现边缘情况失败。转向严格的结构化输出协议（例如 OpenAI JSON mode）以保证数值型 FSRS 数据的可靠摄入。

---

## 8. 结论

B5 Canvas Learning System 是间隔重复认知科学、动态知识结构和自主多智能体编排的一次极具野心的集成。FSRS 的集成保证了科学有效的学习调度，代表了相比传统 Ebbinghaus 模型的重大飞跃。

然而，软件架构显示出设计意图与实现现实之间的摩擦。绕过 LangGraph 原生 checkpointer 创建了一个脆弱的状态管理系统。此外，将多智能体中文 RAG 管道强行通过 4000 token 的狭窄通道在数学上是不可行的，无意中催生了过度设计的 Hot-Warm-Cold LLM 蒸馏分层，仅仅是为了在上下文截断中生存。最后，系统 200 节点的上限揭示了前端渲染限制和后端上下文膨胀两方面的问题。

通过升级到原生 PostgreSQL checkpointer、提高上下文限制以适应中文分词比率，以及采用 Map-Reduce 模式进行大型图遍历，系统可以稳固其基础架构并实现其预期的教育能力。

**参考来源：**
1. src/agentic_rag/state_graph.py (fileSearchStores/persistentcanvaslearningsys-1mrd4km6idba)
2. [langchain.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFOrWSwtck4qVfmJRLv3Y8B2q140PT7tN36esbmwGpLiNPpaoY0iXAdhCpAw8YIPI0Odzki1LuT4BuMmMQYEhY44FeEoVUyI5rOoEWP_9wxyHDpR--oxEH6YDQKQLO_cTlfNtpa_tCT4cJE5lakqz79Qw==)
3. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFulqqu1A8rxAs3RThGxZPOOF0RWY2JS3W8As62fDNNVf6davCu2QJX4ekxnPwx2otwfUi3maCh7ysYJAzmBqTv-G3u5tBuCFS5uBght-ZRAJX9pixClKVijawEq1ySH6UwvlWmJ0tPdZ24PBnVwRLtTLY0Yw==)
4. [sparkco.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHBwmAjJ2LfVrJnaNlP8v5Slhun0AZtGhbXzDM34y11A4RDC5Nt6KxQ8bZdGWHUQJQl891CZclEJkVYJMX_F54wl1xWSOv8mcVDGBvwyNczNRbfFu3G3LdDLw6KPT1wKN-C9jhkCZhkb5CXstMI0QtNhixopDECvbOxGak2xDB_4YMUmk1jLLk=)
5. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHhryQYzszoqRjM6yXOBpg0z12RLIeyNeIlJukNYKQ7WN-HWv83m_BXxOq6WTUU9wZOHYCmvVzBKic7OUnnauY8DUwjuVFNwccxFeaM20hokFxERISvzHsldQ-n4jyzuN0xg3PKv4fLcvpiDg==)
6. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHbkK6pZeeLxOwd_QxFdKv1ZlohJa0Osa08oA-k3B3DT2RwYQnuJNVpzwRxGeu7gy_4KmFPrPNcRQH9U3YZEiKE9_b-BOGHz_DAo7WwJ6qsOPfv9ig9me2G3h1RLI-LrMEj3HY1S2Kshh5_kw==)
7. [dylancastillo.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFyi90Qt17SE6xuqZUt_RXH4UIj4wlgxAnoOh9GXoXzW2SP7O56YJVuxchqkYZKH9T8zfnRTvKruFcOM8fPL-7aaGDU5T7MWURD8FuLjWVyEhqg0Z8dSqt6JIgLU0fGgvTBMaLNuD-J)
8. [digitalorientalist.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQENv2TPY_VFmzjHarl_F274EVMgPtfuqkyfcSHk-QKKUtAbDWEnPa0rbFEakQUk3giiiVw-e4s4BOTLMamD1CZ6fKY29NLSlRH9mQHNVle02n0n6fjlufgtvEw3PIDKIX2WyJu15LsTLDvcbfUJmuH6YXYDLbx07xbHsSqujND4J_hxZ8R_NT0tS7xliokoE9aNEFJU7B-B8hzaQLi_QHgYffER5Lk-ZD3Jtob7SdYTRJtlk4nlt6Y=)
9. [lafucode.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGQa0RHam3kH51y35kgHbZE5EHN-Sx-BV9iuBse0q9jb94ttIX2alWpwPwVnV81o6_83lClceOoQiUy4lSOlwMJ88ZZ0EmovPkTQTJvO3VE5dOQ4ywFD9ZEVUTM7SAZ_ngJ5pFr3wO-W3A0VYh7KnfeNSHtswtuwB4gLLE=)
10. [apiyi.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEmc8VhlXOnGEVboJaoKlJLBNt6qU8Wg-NzmkJf8K44VQNgwnXyeK0eGzeA4egSl63PYPQzPOlhnZOn6jlY92ST9RAOAJdo1ov_i5fGkKNumIUxSGG31ARvuuxYFEUF)
11. [neurips.cc](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFnbA_p6sPlmWVmnc9ALy1bLs1PGTSDUbcBjOuWO09hAqWRkrEozgmEIwwZSZBReedQDNFuNuFCiiDGmWko9S-6Um9Hwy1SHhXt83VxZFD3o1GLPd5WO0Mz51I2gndMw5YStxlXltTFpjAoDxW_QngF8bXqI7GG1BdeBE48UG0uM0ixpdmErA-kW2K4SCs8Wqt1Z9LXxfcZx0X5SjWSAKusGmULSZ8_iMke6ndIICmWi5Xe-UagSR2e4sM=)
12. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF-LNxWi9vEcwaLdw15loZQ88zmRIyMFhpcgQ0mu5Uvn9ukFFFG_zFwmKohmn2IqG54uKlBHBgowdwatH0GjwlIYgC_CTgK9ODHVNfdYGZSSRdMytKZkEWiAIbjwj64w7WyW5MhlWxeh62ZZbPm-TPoRBrDbsvOEUlzd7itQhp4BrB4cHMS8IKy917jVgsaU-63KIE4nMSUSg==)
13. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFKH30KXTIhUYOHLF33fFKjZqbpsGimt0ZtjejEDSKqtDxSApPYfcVLJOGuB6d7A3kbPLi4XMY4VlLckZHCZPXx9rmWLiDX2QpO00KzY7dp_L2itNBQW9rpyPvYiVHlSleFU9-m_bSCnSgL9rPUowcAmdNUqVgiJID-BZTRZRO2CEwqsZdTrC7hppuelGbLIxo=)
14. [ankiweb.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGkMa9Oi0-HyO1tXG2L6bPsOy-BtpQ4RZY-0Ykv57brdVfNpBwDWDh8kotKPcMCl-RKb8qqVrn2rCio7STZ0ILK0Qup9Roau941XFBk1C8FZ9AaDzI7daFvKR6JlCwE82___8zl41TqFosPoonP4eSQ3T6Xas1ciXwQIok=)
15. [quizcat.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGFl2GnTGIzEUBlR63dYZdLrgNtmurXn9rRfFezBabQajOCb-YGoi_IcE_GiUZ86OHB8CpIEyvQD96N1FYva9U-uIwfXl775bBQJ8tupTbukw2L3AmC7Lkf8TEV4AiwdTxPFcE1zqYTJsnyh6M9lMAzY4K5lqojGx1Jvg0=)
16. [moltbook.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHRaoBKtZGPlZkkINMMzPzIn1S4JBf6MXXV1lMZSjuANGynjRyBX047tMehdBQm2UmSb6mP4FWSlaM1VsLMQLOMyaPfdR9RCiLbptawVl577lwXjRtHuySO3uANopkx0ec4Duua9SExEtjzn5eOO--gRmihcTA07QI=)
17. [dev.to](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGuxTuUylOFhhsauQ-6IlaYTng_pz-tf61BNvqi3TypB3IrDLjEy6k9wqFAi25o3e8j-krEMIochc3NAhzgLpc9KY-PCi0d1l8nQ91GJHlm_ic74blxXyKVrvsACe9l-pAgGqeP1Cp58KhQIF9GnCpVRbEyITK9HVGGdIQiy_aDuv9xj4HC3rj--L8xLYI0B21RSgYvbn5wmyfPvoc=)
18. [plainenglish.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQENdM9H6VlPSfE5cMNDy3KR4ss9aZfRjs3_ns0w7KXuq_2t7ZAr5Oj9mcUFVgalJ7x87kejpniDn6R96ZnEEyFtoGpx7K12mmM8VjtYA1ru4lRVmeQDmCHf7b57qG4CWGBhDXNFPVkyXyx_ozOqYnDTg7foHLebwSlTRn4_jZ28bph-9Hduxxo3YqptvOb683lwb4QGBH8_4qHUImMuVmc=)
19. [sourceforge.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEKUiylh_mtfp-vhPJBzisxw6a_-SkRurAZ_ZrohAW5LHuESG6RZK8mlZeCEU4p0UU1Q-mkYPa2jbnsFE83d0w93t3RDATGOKrxVZb8lLNjlVQ2TYsr5XiHgkrKq-dLCBX14G9Z-YUtOSM7OCs7rDx6n6f6Z1U=)
20. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEr5XIGYTZ7V-AsfJhAAROmP-N_gODr1FYAF9op2KpeqSWojNC0s_E8R4V7vHhFM9U7t6zzI-WD1QXtkh07yKbtC5C9sakTqch_JyEmGTcAS4G5_MLEXJk9Jg==)
