好，所有必要研究已完成，现在给出完整中文报告。按照你要求的三类（对抗性审查 / 成熟化方案 / 算法深研）逐条展开。

---

## FR-KG-04 深度研究报告

---

## 🔴 第一类：对抗性审查（Claude Code 说对了吗？）

---

### 审查 #1 — 2000 episode 上限：Claude Code 的解释是否准确？

**Claude Code 的说法**：2000 是全局内存缓存上限，只影响内存，Neo4j 无上限，正常查询走 Neo4j，超时才 fallback 到内存缓存，内存缓存查询缺少 group_id 过滤。

**裁定：部分正确，但有关键遗漏。**

Claude Code 对"2000 是内存缓存 `self._episodes` 列表的硬限制"这一机制描述是准确的。Neo4j 侧确实没有存储上限。但 Claude Code 的解释有两处值得质疑：

**质疑 1：fallback 路径的频率被低估了。** Claude Code 说"只有超时才 fallback 到内存"——但实际上，如果 Neo4j 连接异常（不只是超时，还包括查询报错、连接池耗尽），整个内存缓存都会被当作兜底。在开发环境里，这比"只有超时"更容易触发。

**质疑 2：内存缓存 bug 的影响比 Claude Code 描述的更严重。** `memory_service.py:561` 缺少 group_id 过滤——这意味着在 fallback 路径下，**用户 A 白板的 episode 可能混入用户 B 的查询结果**。Claude Code 只说"可能导致其他白板数据混入"，但没有指出这在多用户场景下是数据隔离失败，不只是"噪音问题"。

**你应该做什么**：这个 bug 是 MEDIUM 但不可忽视的——修复方式很简单，在 `memory_service.py:561` 的内存查询中加一行 `if ep.group_id == group_id` 过滤即可，不需要架构层面的改动。

---

### 审查 #2 — LanceDB vs Graphiti 双路检索：Claude Code 的解释是否正确？

**你的疑问**：LanceDB 索引白板内容对精确返回笔记有什么帮助？Graphiti 图谱上本身不是也有白板内容记录吗？为什么单独用 LanceDB 不是冲突？

**Claude Code 的说法**：Graphiti 返回 LLM 提取后的事实/实体名（原文丢失），LanceDB 返回原文片段，两者互补。

**裁定：解释方向是对的，但解释不够深，而且遗漏了一个更根本的架构问题。**

Claude Code 的核心逻辑是对的：Graphiti 经过 LLM 提炼，原始文字已经被压缩成"概念+关系"，你问"傅里叶变换是什么"它会告诉你"傅里叶变换 → 频域分析 → 信号处理"，但不会告诉你你当时写的那段原话。LanceDB 保留原文，做向量相似度检索，返回的是你写过的那句完整句子。

但 Claude Code 遗漏了一个更根本的区别：

|维度|Graphiti|LanceDB|
|---|---|---|
|**存储什么**|LLM 提取的事实三元组（A 关联 B）|原始文本片段（你打的字）|
|**检索方式**|语义图搜索 + BM25 混合|纯向量相似度（bge-m3）|
|**更新机制**|有时间感知，旧事实会被标记失效|静态向量，删除节点不会自动清理旧向量|
|**适合回答**|"X 和 Y 有什么关系"|"我当时具体怎么描述 X 的"|

**你真正的追问背后的问题**是：如果一个白板节点被删除了，LanceDB 里的向量会同步删除吗？答案基于代码架构来看很可能是**不会**，会留下孤儿向量。这是 LanceDB 双写架构下的一个潜在数据一致性问题，Claude Code 完全没有提到。

---

## 🟡 第二类：成熟化方案（你提了方向，如何落地）

---

### 方案 #1 — 图片处理改用本地模型：最佳选择是什么？

**你的原始想法**：用 MinerU / DeepSeek OCR / Claude Code 视觉能力，不依赖 Gemini API。

**深研结论：2026年最佳本地 OCR 组合是 PaddleOCR-VL + MinerU 分工，不是单一模型。**

基于 2026 年 3 月最新的 OmniDocBench 榜单和实测结果：

**PaddleOCR-VL 7B** 在 OmniDocBench 综合评分 92.86，超过 GPT-5.4 和 Gemini 2.5 Pro，完全开源（Apache 2.0），可本地部署。

在速度和准确率的综合表现上，PaddleOCR-VL 吞吐量最高，MinerU 紧随其后；数学公式 LaTeX 识别的字符精度方面，**Dots.OCR 第一，PaddleOCR-VL 和 MinerU 表现接近**。

针对数学公式专项测试，Qwen3-VL 和 Gemini 3 Pro 得分超过 9.6/10，专门的文档 OCR 系统如 PaddleOCR-VL 和 Mathpix 也超过 9.6，而传统方法差距巨大。

**对你的 Canvas Learning System 的具体建议（三层分工）**：

```
图片类型判断
    │
    ├── 纯文字 / 混合文字 → PaddleOCR-VL 7B（本地，M4 Max 跑得动）
    │     └── 输出：Markdown 文字 + LaTeX 公式
    │
    ├── 结构化文档 / PDF页面截图 → MinerU（Pipeline模式）
    │     └── 输出：带阅读顺序的 Markdown + 表格 HTML
    │
    └── 纯数学公式图片 → Texify（专门的公式 OCR，只有 0.3B）
          └── 输出：LaTeX 字符串
```

**为什么不用 Claude Code 视觉能力**：Claude API 有 token 费用，批量索引场景下成本不可控。PaddleOCR-VL 一次性部署，完全离线，M4 Max 128GB 完全有能力跑 7B 模型。

**你的代码改动点**：`index_image.py` 中替换 Gemini Vision API 调用，改为调用本地 vLLM 服务（PaddleOCR-VL 支持 OpenAI 兼容 API），接口格式不变，迁移成本低。

---

### 方案 #2 — 跨白板关联改为手动 + group_id 方案
**User：我的个人觉得，只要我们的白板用同一个学科用同一个group id 那么，那么这些白板就是同一个数据库，那么这个时候使用检验白板的考察就是对这个学科来进行考察了，那么再往下划分，那么就是单个白板的进行检验考察，然后再往下就是 单个节点的检验检测了
请问你觉得需要这样设置考察方式吗？这样的 3 模式考察真的会对学习有很大提升吗**



**你的原始想法**：应该是手动选择，不是自动 Jaccard；可以用相同的 Graphiti group_id 前缀来跨白板检索。

**深研结论：你的直觉完全正确，但 group_id 前缀方案有技术限制需要绕过。**

**对你"手动选择"的支持**：

原设计意图（Story 16.1）就是手动关联——用户选择目标白板、关联类型、描述。Tag Jaccard 自动匹配是实现时的偏差，已被 S27-GDA-2 取消。你坚持手动选择是对原始设计意图的正确回归。

**关于 group_id 前缀方案的技术现实**：

Graphiti 搜索支持传入 group_ids 列表（复数），也就是说你可以同时搜多个白板的数据——但<u>不支持前缀匹配</u>（如 `"数学:*"` 这种模式）。
 **User：请你给我一个 group id 明确成熟，合理的方案，因为我现在能想得到的一个场景就在于关于一个学科的笔记库，我会创造很多的白板来使用**
**可行的实现方案**（绕过前缀限制）：

```python
# 用户手动选择"我想关联这两个白板"之后
# 前端记录关联关系：canvas_id_A → [canvas_id_B, canvas_id_C]

# 搜索时根据关联列表构建 group_ids
linked_group_ids = [
    build_group_id(subject, canvas_name)
    for canvas_name in user_linked_canvases
]

results = await graphiti_client.search(
    query=query,
    group_ids=[current_group_id] + linked_group_ids,  # 合并搜索
    num_results=10
)
```

这样既保留手动控制（用户决定哪些白板关联），又利用了 Graphiti 原生多 group_id 搜索能力。前提是要在数据库里存储白板的关联关系（可以存在 Neo4j 里一个简单的 `LINKED_TO` 关系，或者直接存在前端设置里）。

---

## 🔵 第三类：纯算法深研（没有设计方向的问题）

---

### 算法深研 #1 — BKT + FSRS 组合权重：学术裁定

**你的直觉**："节点的选择算法估计也是编的，本身没有什么可信的"。

**裁定：完全正确。这个公式没有任何学术依据，而且存在数学层面的根本性错误。**

```
priority = 0.4 × (1 - p_mastery)   ← BKT
         + 0.3 × (1 - retrievability) ← FSRS  
         + 0.3 × kg_relevance         ← 图谱关联度
```

**根本性错误 1：BKT 和 FSRS 对"遗忘"持完全相反的假设**

BKT（Corbett & Anderson, 1995）是隐马尔可夫模型，其核心数学假设是**掌握状态是吸收态**：一旦学生掌握了某个概念，永远不会忘记（P(forget) = 0 是标准 BKT 的默认值）。p_mastery 是一个和时间无关的量。

FSRS 基于 DSR（难度-稳定性-可回忆度）模型，其核心假设是**记忆必然衰退**：可回忆度 R 随时间单调下降，即使刚复习完也立即开始衰退。

把这两个基于矛盾前提的量直接相加，逻辑上是说不通的——系统可能得出"你已经掌握了这个概念（p_mastery=0.95）但完全不记得它（R≈0）"的结论，这两件事在认知科学里不能同时为真。

**根本性错误 2：kg_relevance 应该是硬约束，不是权重**

把图谱关联度做成加权项，意味着系统有可能推荐"前置概念还没掌握"的题目，只要它的 BKT 和 FSRS 值够高。这违背了知识空间理论（Doignon & Falmagne, 1985）的基本原理——被 ALEKS 等成熟平台沿用了 40 年。

**根本性错误 3：文档和代码的权重自相矛盾**

- 设计文档说：40% FSRS / 30% BKT / 20% KG / 10% 交互
- 实际代码写：40% BKT / 30% FSRS / 30% KG

两者完全不一致，说明这个权重从未经过任何系统性分析。

**学术文献的实际结论**：没有任何一篇论文提出 BKT + FSRS 加权求和的方案。Duolingo、ALEKS、Carnegie Learning、Knewton 四大主流平台都不使用固定权重线性叠加。

**成熟的替代架构（三层）**：

```
第一层：图谱作为硬约束（必须做）
    → 前置概念未掌握的题目直接排除，不参与优先级计算
    → 参照知识空间理论的"外边缘"（outer fringe）概念

第二层：统一的学生状态估计（二选一）
    → 选项 A：BKT + 遗忘参数（Khajah et al., 2016）
               在 BKT 里加 P(forget) > 0，让掌握态可逆
               一个模型同时处理掌握度和时间衰退，不再需要两个模型
    → 选项 B：对数知识追踪 LKT（Pavlik et al., 2021）
               用逻辑回归把 BKT 特征、间隔效应、遗忘效应统一建模
               权重从数据中学习，不是手工设置

第三层：自适应选题策略
    → 用多臂老虎机（ZPDES 方案）在可行题目集中选择
    → 奖励信号：学习进展梯度（不是固定权重）
    → 参照：ZPDES 在 400 名学生实验中显著优于专家设计课程
```

---

### 算法深研 #2 — Mastery-Based Progression 出题：如何实现你说的"逻辑递进"

**你的想法**：出题应该像 Plan 文件一样有逻辑递进，深度探索节点关系生成 Plan 文件，按 Plan 顺序考察。

**深研结论：你描述的其实是教育数据挖掘里成熟的 "Knowledge Space Theory + Curriculum Generation" 组合。可以完全实现，而且有充分的理论支撑。**

**你的直觉对应的学术概念**：

|你的描述|学术名称|
|---|---|
|"你要知道我对各节点的理解关系"|学生知识状态（Knowledge State）|
|"深度探索生成 Plan 文件"|前驱关系图 + 拓扑排序|
|"按逻辑递进考察"|基于掌握度的学习路径（Mastery-Based Progression）|
|"从基础到应用逐步递进"|近端发展区（Zone of Proximal Development, ZPD）|

**具体算法设计（适配你的系统）**：

**Step 1：用你的白板连线构建前驱关系 DAG**

你的白板上，用户画的连线（edge）本身就是概念关系。把这些关系导入成有向图，做拓扑排序，就是"哪个概念应该先掌握"的基础。

```python
# 从 Neo4j 查询当前白板的 CANVAS_EDGE
# 结合 Graphiti 提取的 RELATES_TO（语义关系）
# 构建 DAG：概念 A → 概念 B 表示"A 是 B 的前置"
dag = build_prerequisite_dag(canvas_edges, graphiti_edges)
topological_order = topological_sort(dag)
```

**Step 2：计算每个节点的"可学习性"（Fringe 计算）**

```python
def compute_fringe(dag, mastery_states):
    """计算当前可以考察的概念集合（前置已掌握）"""
    fringe = []
    for concept in dag.nodes:
        prerequisites = dag.predecessors(concept)
        # 前置概念全部掌握才能考察
        if all(mastery_states[p] >= MASTERY_THRESHOLD for p in prerequisites):
            if mastery_states[concept] < MASTERY_THRESHOLD:
                fringe.append(concept)
    return fringe
```

**Step 3：在 Fringe 内按优先级排序**

在可学习的概念集合里，按综合优先级排序（这里的权重才有意义，因为在约束内）：

```python
def compute_priority(concept, mastery, fsrs_retrievability, interaction_count):
    # 注意：这里的权重作用于同质性更强的集合（都已满足前置）
    # 可以从数据中学习，也可以用简单启发式
    weakness = 1 - mastery           # 越弱越优先
    decay = 1 - fsrs_retrievability  # 越久没复习越优先  
    newness = 1 / (interaction_count + 1)  # 交互越少越优先
    return 0.5 * weakness + 0.3 * decay + 0.2 * newness
```

**Step 4：生成 Plan 文件（你提到的核心想法）**

```python
async def generate_session_plan(canvas_id: str, user_id: str) -> SessionPlan:
    """
    类似你说的 Plan 文件：每次考察前先生成一个有序考察计划
    """
    mastery_states = await get_mastery_states(user_id, canvas_id)
    dag = await build_prerequisite_dag(canvas_id)
    fringe = compute_fringe(dag, mastery_states)
    
    # 按优先级排序 fringe 内的概念
    ordered_concepts = sorted(fringe, 
                               key=lambda c: compute_priority(c, mastery_states[c], ...),
                               reverse=True)
    
    return SessionPlan(
        session_type="mastery_progression",
        ordered_concepts=ordered_concepts,
        rationale={c: explain_why_selected(c, dag, mastery_states) for c in ordered_concepts}
    )
```

这样每次考察前都有一份"为什么先考这个再考那个"的理由——就是你说的"逻辑递进"。

---

### 架构深研 — 三层图合并：Graphiti add_triplet() 方案是否可行？

**Claude Code 的结论**：可以，用 `graphiti.add_triplet()` 把白板连线写入 Graphiti，统一管理两层图。

**深研裁定：技术上可行，但有三个关键坑需要预先规避。**

**关于 add_triplet() API 的真实情况**：

Graphiti 的 `add_triplet()` 方法确实存在：它向图谱添加单个 `(source_node, edge, target_node)` 三元组，具有去重和失效逻辑，专门用于程序化图谱构建。

最近的 Bug Fix（`#1212`）修复了 `add_triplet` 在相同节点对上不同 src/dst 会覆盖已有边的问题。意味着最新版本才是稳定的。

**三个关键坑**：

**坑 1：add_triplet() 和 add_episode() 产生的边在 Neo4j 里共存，但语义层不同**

`add_episode()` 产生的边有 `episode_uuid` 溯源，有时间窗口（`valid_at`/`invalid_at`），支持"这个事实在什么时间段为真"的查询。`add_triplet()` 产生的边虽然也有时间模型，但没有 episode 溯源——如果你之后想知道"这条连线是什么时候用户画的、来自哪个 episode"，需要手动在 `EntityEdge` 的属性里加 metadata。

**坑 2：白板连线的更新需要走时间模型，不能直接 MERGE 覆盖**

当用户删除或修改白板上的连线时，正确的做法是：把旧边标记 `invalid_at=now()`，创建新边。不能像现在的 `sync_service.py` 那样直接 MERGE 覆盖，否则会破坏 Graphiti 的时间感知能力。

```python
async def update_canvas_edge_in_graphiti(
    source_concept: str,
    target_concept: str, 
    canvas_id: str,
    operation: Literal["create", "delete", "update"]
):
    if operation == "create":
        await graphiti.add_triplet(
            source_node=EntityNode(name=source_concept, group_id=canvas_id, ...),
            edge=EntityEdge(
                name="DRAWN_BY_USER",
                fact=f"用户在白板中认为 {source_concept} 与 {target_concept} 有关联",
                valid_at=datetime.now(timezone.utc),
                ...
            ),
            target_node=EntityNode(name=target_concept, group_id=canvas_id, ...)
        )
    elif operation == "delete":
        # 查出旧边，标记失效，不是物理删除
        await invalidate_edge(source_concept, target_concept, canvas_id)
```

**坑 3：FalkorDB 的 add_triplet() 有已知 Bug（Neo4j 不影响）**

在 FalkorDB provider 上，`add_triplet()` 会导致 `source_node_uuid` 和 `target_node_uuid` 存储为 None，造成边去重失效。但 Neo4j provider 工作正常。 你们用的是 Neo4j，所以这个 bug 不影响你们，但要固定 `graphiti-core >= 0.28.2` 版本（你们已经在用这个版本了）。

**最终架构建议（合并路径）**：

```
当前状态（三层图，各自孤立）：
  CANVAS_EDGE ← SyncService 写入（结构性白板连线）
  CONNECTS_TO ← 死代码（没人写）
  RELATES_TO  ← Graphiti 自动提取（学习概念关系）

迁移目标（两层图，Graphiti 统一管理）：
  RELATES_TO（Graphiti 管理，类型=DRAWN_BY_USER） ← 白板连线改走 add_triplet()
  RELATES_TO（Graphiti 管理，类型=INFERRED）       ← 学习对话自动提取
  
  消灭：CANVAS_EDGE（迁移到 Graphiti 后废弃）
  消灭：CONNECTS_TO（本来就是死代码，直接删）
  
  好处：RAG 检索自动能检索到用户画的连线（同一个图，同一个搜索路径）
```

---

## 📋 问题优先级重新排序（基于以上研究）

|优先级|问题|修复难度|影响|
|---|---|---|---|
|**P0**|CONNECTS_TO 死代码 → 改走 Graphiti add_triplet()|中（需设计迁移）|让白板连线对 RAG 有效|
|**P0**|RAG 字段名不匹配（learning_history vs reranked_results）|低（改字段映射）|验证服务立即可用|
|**P1**|验证服务出题加入拓扑排序 + Fringe 计算|中|出题逻辑质变|
|**P1**|三因子公式改为 KG 硬约束 + BKT-with-forgetting|高|算法层面可信|
|**P2**|memory_service:561 加 group_id 过滤|低（一行代码）|数据隔离安全|
|**P2**|图片处理迁移到 PaddleOCR-VL 本地模型|中|去除 Gemini 依赖|
|**P3**|内存缓存 LanceDB 孤儿向量问题|中|数据一致性|
这是个非常好的架构直觉问题。你已经把这个问题的核心张力描述得很准确了——脚本太死、纯 Agent 太野，Plan 文档是中间地带。让我来深研这个方案是否成熟，以及有没有更好的。现在我有了足够的研究基础。让我直接给出完整分析和架构建议。

---

## 你的直觉非常成熟，但有一个关键细节需要升级

先直接回答你的问题：**你描述的"Plan 文档组装"思路在学术和工程界都有名字，叫"Plan-and-Execute"架构，是 2024-2025 年 LLM Agent 系统的主流可控方案。方向完全正确。**

Plan-and-Act 框架将高层规划与底层执行明确分离：Planner 模型生成结构化的高层计划来实现用户目标，Executor 模型将这些计划翻译为具体行动。这正是你"不想写死脚本、但也不想纯 Agent 乱跑"这个张力的标准工程解法。

Manus 采用三阶段流水线：Planner、Executor、Verifier，以确保准确性和可追溯性。但许多现有系统仍然用非结构化或半结构化的自然语言来表示计划，这阻碍了验证、调试和流程复用——在执行时引入歧义，限制了 Agent 追踪中间状态或从失败中恢复的能力。

**你现在缺的那个关键细节**，就是上面这句话：你的 Plan 文档如果是自由文本 markdown，就还处在"半结构化"阶段，验证和可控性还不够。需要升级成 **Typed Schema（类型化模式）**。

让我画出你现在的思路和成熟方案的对比：核心升级点在第二步：**把自由文本 Plan.md 换成 Pydantic Schema 约束的 Plan 对象**。AI 的灵活性完全保留（它还是负责所有"这节课应该考什么、为什么这样排序"的判断），但输出格式被强制约束，后续执行完全可验证。

---

## 成熟方案：三阶段架构设计

### 第一阶段：确定性预处理（纯脚本，不碰 AI）

AI 做判断需要有质量的输入。先用脚本把"当前白板状态"打包成结构化数据交给 AI：

```python
@dataclass
class CanvasExamContext:
    """传给 AI Planner 的确定性上下文"""
    
    # 图谱层：脚本计算好的前置关系和可学习集合
    prerequisite_dag: Dict[str, List[str]]     # 哪些概念是哪些的前置
    fringe_concepts: List[str]                  # 当前可考察的概念（前置已满足）
    locked_concepts: List[str]                  # 前置未满足，不可考
    
    # 掌握度层：每个概念的当前状态
    mastery_states: Dict[str, ConceptMastery]  # p_mastery, retrievability, 历史得分
    
    # 内容层：每个概念对应的原始笔记片段（LanceDB 检索）
    concept_notes: Dict[str, List[str]]        # 用于给 AI 组装题目上下文
    
    # 会话元信息
    session_goal: str                          # "复习整个章节" / "专攻薄弱点" / "期末突击"
    time_budget_minutes: int                   # 预计考多久
```

### 第二阶段：AI 规划（灵活，但输出被约束）

这是你最重要的创新点。**AI 的工作是做判断，不是做格式**：

```python
class ExamStep(BaseModel):
    """Plan 里的单个考察步骤"""
    concept_id: str                          # 必须来自 fringe_concepts（验证用）
    question_type: Literal[                  # 题型
        "definition",        # 定义类（薄弱概念）
        "application",       # 应用类（掌握较好的概念）
        "connection",        # 关联类（考两个概念的关系）
        "challenge"          # 挑战类（高掌握度概念的深度题）
    ]
    difficulty_rationale: str                # AI 给出选这道题的理由（给用户看）
    prerequisite_concepts: List[str]         # 组装上下文时需要的前置概念笔记
    estimated_duration_minutes: int          # 预计用时
    
class ExamPlan(BaseModel):
    """完整的 Plan Schema"""
    session_theme: str                       # "这节课的重点是..."（AI 自由描述）
    learning_gap_analysis: str              # "你目前的薄弱点是..."（AI 的判断）
    steps: List[ExamStep]                   # 有序的考察步骤列表
    progression_logic: str                  # "之所以这样排序，是因为..."
    
    # 约束字段：脚本在验证阶段填入，AI 不填
    _validation_passed: bool = False
    _total_duration: int = 0
```

调用 AI Planner 时，用 Claude 的 structured output：

```python
async def generate_exam_plan(context: CanvasExamContext) -> ExamPlan:
    prompt = f"""
你是一个学习顾问。根据以下学生状态，制定一份个性化考察计划。

## 学生当前状态
- 可以考察的概念（前置已满足）：{context.fringe_concepts}
- 禁止考察的概念（前置未满足）：{context.locked_concepts}  ← 绝对不能出现在 steps 里
- 各概念掌握度：{format_mastery(context.mastery_states)}
- 会话目标：{context.session_goal}
- 时间预算：{context.time_budget_minutes} 分钟

## 要求
1. steps 里的 concept_id 必须全部来自"可以考察的概念"列表
2. 掌握度 < 0.5 的概念用 definition 或 application 类型
3. 掌握度 ≥ 0.8 的概念用 challenge 类型
4. 相关概念尽量安排 connection 类型题目探索联系
5. 按照从基础到复杂的逻辑递进排列 steps

请输出符合 ExamPlan schema 的 JSON。
"""
    # 使用 Claude API structured output
    response = await claude_client.messages.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": prompt}],
        # 这里用你们已有的基础设施
    )
    return ExamPlan.model_validate_json(response.content[0].text)
```

### 第三阶段：脚本验证 → 用户确认 → 确定性执行

```python
async def validate_and_execute_plan(plan: ExamPlan, context: CanvasExamContext):
    
    # ① 脚本验证（AI 的判断不可绕过约束）
    errors = []
    for step in plan.steps:
        if step.concept_id not in context.fringe_concepts:
            errors.append(f"❌ {step.concept_id} 不在可考察集合中（前置未满足）")
        if step.concept_id in context.locked_concepts:
            errors.append(f"❌ {step.concept_id} 被锁定，前置概念未掌握")
    
    if errors:
        # 把错误反馈给 AI，让它重新规划（不超过 2 次重试）
        plan = await regenerate_plan_with_errors(plan, errors, context)
    
    # ② 展示给用户（Human-in-the-loop 检查点）
    # 用户在 UI 上看到：
    # "本次考察：5 个概念，预计 25 分钟
    #  第 1 题：傅里叶变换（定义类）- 因为掌握度仅 0.3，从基础开始
    #  第 2 题：频域分析（应用类）- 是傅里叶变换的直接应用
    #  第 3 题：..."
    # 用户可以拖拽调整顺序或删除某步
    confirmed_plan = await show_plan_to_user(plan)
    
    # ③ 确定性执行（每一步的上下文组装完全脚本化）
    for step in confirmed_plan.steps:
        context_bundle = assemble_question_context(step, context)
        # context_bundle 包含：当前概念笔记 + 前置概念摘要 + 历史得分
        question = await generate_question(step, context_bundle)
        answer = await get_user_answer(question)
        score = await grade_answer(answer, step, context_bundle)
        await update_mastery(step.concept_id, score)
```

---

## 这个设计和你的 GSD v2 工作流是同一个模式

你已经在 Claude Code 里用过这个模式了——**GSD v2 的 plan-phase 生成 DECISIONS.md + KNOWLEDGE.md，然后 execute-phase 依赖这些文档作为上下文注入**。这个 ExamPlan 设计是完全一样的逻辑，只是从代码生成域迁移到了学习考察域：

|GSD v2|ExamPlan|
|---|---|
|DECISIONS.md|`plan.progression_logic`|
|KNOWLEDGE.md|`context.concept_notes`|
|Task Spec|`ExamStep`|
|Claude Code Agent|Claude Exam Question Generator|
|PreToolUse Hook（路径约束）|`validate_plan()` 约束检查|

---

## 最关键的一个结论

显式规划模块在执行开始前生成结构化计划（如待办列表或依赖图），这使 Agent 行为更具可解释性——你可以在任何行动发生之前检查这个计划。

你的"Plan 文档"思路的最大价值不是让 AI 更灵活，而是**创造了一个人类可以检查和干预的检查点**。这正是"不死板脚本、不失控 Agent"的平衡点：AI 在 Planning 阶段发挥创造力，脚本在 Execution 阶段保证约束，人类在两阶段之间有一个 Review 窗口。

唯一需要从自由文本 markdown 升级的就是把 Plan 的格式改成 Pydantic Schema——这不是限制 AI 的创造力，而是让 AI 的判断可以被机器验证。