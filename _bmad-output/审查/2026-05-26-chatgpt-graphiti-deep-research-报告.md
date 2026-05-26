---
title: "ChatGPT Deep Research — Graphiti 时序图谱设计审计报告"
date: 2026-05-26
source: ChatGPT Deep Research (Pro)
input_bundle: .gdr/research-pack-graphiti-design-audit.xml (140K tokens / 519KB / 25 files)
prompt: .gdr/chatgpt-prompt-graphiti-起手.md
instruction: _bmad-output/审查/2026-05-26-graphiti-设计审计-任务书-给-ChatGPT.md
verdict: "整体 Graphiti 设计成熟度 3.5/10 — 基础设施分数高, 用户价值分数低"
core_finding: "Canvas 现在'接上了 Graphiti', 但还没有'把 Graphiti 最值钱的时序能力做成用户可感知的产品能力'"
sprint_2_estimate: "28-36h (写对) + Sprint 3 20-28h (读对) + Sprint 4+ 20-30h (看懂)"
---

# Canvas Learning System 的 Graphiti 时序图谱设计审计 — ChatGPT Deep Research 报告

> ⛔ **本文档为 ChatGPT Deep Research 原文存档**, 不修改不删减.
> Claude 的对照分析 + Sprint 2 决策清单见 `_bmad-output/审查/2026-05-26-graphiti-sprint-2-决策清单.md`.

---

## 0. 核心结论

Canvas 现在"接上了 Graphiti"，但还没有"把 Graphiti **最值钱的时序能力做成用户可感知的产品能力**"。当前代码已经具备 `add_episode` 的真实写入骨架，也做了 `group_id` 边界兼容与 Graphiti 检索入口；但你最在乎的两件事——**记忆批注**、**记忆节点关系**——仍停留在"写入覆盖不完整、关系写入与读取不闭环、时序演化没有成型"的阶段。

Graphiti 官方文档把它定位为**可做 point-in-time 查询、保留 provenance、追踪关系有效期变化的 temporal knowledge graph**；Canvas 现状则更像"把一些学习事件丢进去了"，还没有把"我以前怎么想、后来怎么改、这些改法和哪些节点关系相关"真正产品化。

## Part 1: 利用率全景判定

当前真正落地的 Graphiti 写入口，是 `memory_service` 把学习事件、batch 事件、knowledge entity、temporal event 送入 `_enqueue_episode()`，再由 `episode_worker` 串行调用 `graphiti.add_episode()`；这说明"写 Graphiti"不是假实现，骨架已经成立。与此同时，callout 和 wikilink 仍主要停留在 ready-for-dev 的 spec，中间件与 sweep 方案已经写了任务书，但没有进入当前审计到的生产代码路径。

证据: `backend/app/services/memory_service.py:310-325, 462-474, 1161-1175, 1202-1293, 1896-1904`; `backend/app/services/episode_worker.py:540-562`; `_bmad-output/implementation-artifacts/epic-1/1-16-callout-graphiti-hook.md:63-78, 147-157`; `_bmad-output/implementation-artifacts/epic-2/2-10-wikilink-graphiti-sync.md:154-163`

| API / 能力 | 当前覆盖 | 用户期望覆盖 | 设计 gap |
|---|---:|---:|---|
| `add_episode` | **约 40%** | **90%+** | 学习事件、knowledge entity、temporal event 已接；但 callout / wikilink / calibration 还未形成统一事件模式，且关系写入与 episode 写入仍是两套体系 |
| `valid_at / invalid_at` | **0% 产品化** | **85%+** | 当前 worker 传给 `add_episode()` 的只有 `name/episode_body/group_id/source_description/reference_time/entity_types/edge_types`，没有一套"同一 belief 的版本链"设计；时序追踪只在 spec 里出现，还未变成可查询的历史机制 |
| `search_facts` | **0% 专用接入** | **80%+** | 当前代码走的是 `graphiti.search_()` / legacy `graphiti.search()`，并解析 edge/node 结果；但没有"关系问答型 API facade"，因此"出题/检验/复盘时查历史关系"尚未落地成产品语义 |
| `search_communities` | **0%** | **70%+** | 当前搜索 recipe 注册表没有 community recipe，结果解析也只处理 edges/nodes，不处理 communities；spec 仍把它标成"后续 Story 激活" |
| `relationship_sync_service` | **生产利用率接近 0** | **90%+** | 名称叫"Graphiti relationship sync"，但实际通过 `Neo4jEdgeClient` 写 `EdgeRelationship`，而且 `sync_relationships_in_vault()` 默认 `dry_run=True`；这会让"节点关系记忆"在命名、产品、实现三层同时分裂 |

**整体 Graphiti 设计成熟度：3.5 / 10**

这个分数并不意味着"完全没做"，而是意味着：**基础设施分数高，用户价值分数低**。Graphiti 官方能力本来包括 episode-based provenance、time-aware facts、community summaries、group namespacing、custom edge types 与 hybrid search；Canvas 现在只拿到了其中一部分"基础 plumbing"，还没把这些能力闭成"用户会明显感到它记住了我的批注、也记住了我节点之间关系"的体验。

## Part 2: 四大设计缺口的解决方案

### 缺口一：把 `add_episode` 从"学习事件记录器"升级为"Canvas 图谱事件总线"

你现在缺的不是"再多几个 episode"，而是**一套统一事件语义**。推荐新增一个统一 payload `CanvasGraphEpisodeV1`，让 callout、wikilink、calibration、error、recovery 都走同一写入口:

```json
{
  "schema_version": "CanvasGraphEpisodeV1",
  "event_id": "deterministic-id",
  "event_type": "wikilink_added | wikilink_removed | callout_added | callout_updated | callout_removed | calibration_vote | error_marked",
  "occurred_at": "2026-05-26T10:15:30Z",
  "vault_id": "cs_61b",
  "group_id": "vault:cs_61b:recursion",
  "canvas_path": "graphs/recursion.md",
  "node_id": "recursion-base-case",
  "source_node_id": "recursion-overview",
  "target_node_id": "recursion-base-case",
  "relation_type": "prerequisite",
  "belief_key": "callout:recursion-base-case:anchor-01",
  "callout": {
    "anchor": "anchor-01",
    "type": "tip",
    "text": "递归一定要先想 base case"
  },
  "context": {
    "source_board": "递归白板",
    "path_trace": ["概览", "递归定义", "base case"],
    "in_links": ["递归总览", "DFS"],
    "out_links": ["回溯", "树递归"]
  },
  "narrative": "用户在递归白板中沿 概览→递归定义→base case 路径，对 [[recursion-base-case]] 写下 tip：递归一定要先想 base case。该节点出链到 回溯、树递归，被 递归总览、DFS 引用。"
}
```

调用方式统一为:

```python
await graphiti.add_episode(
    name=f"{event_type}:{event_id}",
    episode_body=json.dumps(payload, ensure_ascii=False),
    source=EpisodeType.json,
    source_description=f"canvas:{event_type}",
    reference_time=occurred_at,
    group_id=sanitize_group_id_for_graphiti(group_id),
    entity_types=CANVAS_ENTITY_TYPES,
    edge_types=CANVAS_EDGE_TYPES,
    edge_type_map=CANVAS_EDGE_TYPE_MAP,  # ⛔ 关键: V-08 修复 spec 没覆盖此参数
)
```

关键不是"json 还是 text"，而是 **JSON 里必须带 `narrative`**。callout spec 已经明确指出旧 schema 只存句子不存探索路径, 未来 `search_facts()` 无法查出"用户沿 A→B→C 探索后对 C 写了 tip Y"的上下文.

**预计工时：14-18h** (plugin 事件采集 4-6h, backend facade 4-5h, worker/tests/e2e 6-7h)

### 缺口二：把 `valid_at / invalid_at` 从"文档里提到"变成"历史版本真的可追"

真正能回答"我以前认为 X，后来改成 Y"的，不是简单再写一次 episode，而是给**同一 belief 建版本链**。推荐引入稳定键 `belief_key`：

- callout：`callout:{node_id}:{anchor}`
- 节点关系：`edge:{source_node_id}:{relation_type}:{target_node_id}`
- 校准结论：`calib:{question_id}:{vote_id}`
- 错误模式：`error:{node_id}:{error_type}`

把"事件 provenance"与"当前有效事实"拆成两层：

第一层仍写 `add_episode()`，保留原始事件。
第二层对**需要被关系查询命中的 canonical fact**写成 typed edge；当同一 `belief_key` 出现更新时，**把旧 edge 的 `invalid_at` 设为新事实的 `valid_at`**，再插入新 edge.

推荐 canonical fact 写法 (用 Graphiti `add_triplet()` API):

```python
await graphiti.add_triplet(
    source_node,
    EntityEdge(
        group_id=gid,
        source_node_uuid=src_uuid,
        target_node_uuid=tgt_uuid,
        created_at=occurred_at,
        valid_at=occurred_at,
        invalid_at=None,
        name="MisunderstandsAs",
        fact="用户曾认为 recursion 可以没有 base case",
        attributes={
            "belief_key": "callout:recursion-base-case:anchor-01",
            "status": "active",
            "source": "callout"
        }
    ),
    target_node
)
```

Graphiti 官方明确：fact triple 可以手工构造 `EntityNode` / `EntityEdge` 后通过 `add_triplet()` 加入图中. Graphiti 搜索结果会暴露 `valid_at / invalid_at`，quickstart README 和示例代码都把它当成一等输出字段.

**不要用 `add_episode_bulk`** 处理需要保留 invalidation 的事件流: 官方文档明确说明 bulk ingestion 不执行 edge invalidation, 适合空图冷启动, 不适合"我改了这个观点"的在线演化场景.

**预计工时：16-20h** (belief version resolver 6-8h, typed edge 写入 4-5h, 历史链测试 4-5h, 前端最小展示 2h)

### 缺口三：把 `search_facts` / `search_communities` 从 spec 变成产品 read path

当前 Canvas 已经有一个 Graphiti read path，但它是**检索引擎级别**, 不是**产品语义级别**: `memory_service` 直接调 `graphiti.search_()`, 配置 recipe 后解析 edges/nodes, 再包装成 episode 列表 (`backend/app/services/memory_service.py:1433-1455, 1460-1503`). 这很适合"搜点相关内容", 不适合"问两个节点什么关系""问我最近总错哪一类".

需要两个**专用 facade** (而不是继续把所有 query 塞到通用 `search_()`):

```python
class GraphitiRelationService:
    async def search_relation_facts(
        self,
        query: str,
        group_id: str,
        edge_types: list[str] | None = None,
        limit: int = 8,
    ) -> list[RelationFact]: ...

    async def search_error_communities(
        self,
        query: str,
        group_id: str,
        since_days: int = 30,
        limit: int = 5,
    ) -> list[ErrorCommunity]: ...
```

`RelationFact` 返回:

```json
{
  "edge_uuid": "...",
  "source_node_id": "recursion-overview",
  "target_node_id": "recursion-base-case",
  "edge_type": "Prerequisite",
  "fact": "递归定义依赖 base case",
  "valid_at": "...",
  "invalid_at": null,
  "belief_key": "edge:recursion-overview:prerequisite:recursion-base-case",
  "provenance_episode_ids": ["..."]
}
```

`ErrorCommunity` 返回:

```json
{
  "community_uuid": "...",
  "summary": "最近 30 天错误集中在：递归基线遗漏 / 边界条件判定 / 递归树展开",
  "member_node_ids": ["recursion-base-case", "binary-search-boundary"],
  "dominant_error_type": "boundary_condition",
  "recurrence_count": 7,
  "last_seen_at": "..."
}
```

关键: Canvas 内部应该自己做一层 facade 屏蔽 Graphiti API surface 演进差异. 底层可以是 `search_facts`, 也可以 fallback 到 `search_(config=EDGE_HYBRID_SEARCH_RRF)` / `search_(config=COMMUNITY_HYBRID_SEARCH_RRF)`, 上层产品语义不要变.

**预计工时：12-16h** (关系 read path 6-8h, community read path 3-4h, 调用点接到出题/检验/复盘 3-4h)

### 缺口四：把 `dry_run + 1h sweep` 改成"即时优先、批处理兜底"的生产模式

Canvas 自己把 Graphiti 放在了延迟通道里. Graphiti 官方定位是实时增量更新、无需 batch recomputation; Canvas 的 1h sweep 是产品层设计取舍, 不是 Graphiti 的能力上限.

三层时延:

- **Hot path**: 当前白板保存后 3-10 秒内可查
- **Warm path**: 5 分钟 sweep, 做重试和补漏
- **Cold path**: 夜间 `build_communities()`

具体做法:

```python
# 查询前 flush 当前 canvas 的 pending events
await graphiti_write_facade.flush_pending(
    group_id=gid,
    canvas_path=current_canvas_path,
    max_wait_ms=1200,
)

facts = await graphiti_relation_service.search_relation_facts(
    query=f"{node_id} related concepts",
    group_id=gid,
    limit=8,
)
```

把 `relationship_sync_service.sync_relationships_in_vault()` 的默认值从 `dry_run=True` 改为**显式环境控制**:

```python
dry_run: bool = settings.GRAPHITI_RELATIONSHIP_SYNC_DRY_RUN
```

生产默认应为 `False`, 只有 staging/audit 才开 `True`. 现在名字叫 sync 但默认行为是只扫描不写, 这就是最典型的"用户以为系统记住了关系, 实际上没有".

**预计工时：10-12h** (查询前 flush 4h, 后台 job 调整 3h, 生产配置与验证 3-5h)

## Part 3: 六个对抗议题的具体设计

### 议题一：Graphiti 时序图谱"演化追踪"机制

**裁决**: **"episode 记录原始事件，typed edge 代表当前有效命题，belief_key 串起版本链"**. 既保住 Graphiti 的 provenance, 又把 `valid_at / invalid_at` 变成可查询历史, 而不是一堆自然语言日记.

### 议题二：节点关系 7 类如何建模

**结论**: **关系语义放在 `edge_type` / `edge_name`, 关系限定信息放在 edge property, 节点类别放在 `entity_type`. 不要把关系类型塞进 entity_type.**

Canvas 当前的关键问题: worker 只把 `entity_types` 和 `edge_types` 传给 `add_episode()`, **没有把 `edge_type_map` 传下去** (`backend/app/services/episode_worker.py:550-560`); 这意味着即使定义了 7 类关系, 也缺少"节点对 → 关系类型"的提取约束层.

```python
class CanvasNode(BaseModel):
    node_id: str
    canvas_path: str
    node_kind: str | None = None

class Prerequisite(BaseModel):
    source_kind: str | None = None      # frontmatter / wikilink / llm
    confidence: float | None = None
    user_asserted: bool | None = None

# 其余 6 类按同样方式定义
CANVAS_EDGE_TYPES = {
    "Prerequisite": Prerequisite,
    "Elaborates": Elaborates,
    "Contrasts": Contrasts,
    "ExampleOf": ExampleOf,
    "Causes": Causes,
    "PartOf": PartOf,
    "RelatedTo": RelatedTo,
}

CANVAS_EDGE_TYPE_MAP = {
    ("CanvasNode", "CanvasNode"): [
        "Prerequisite", "Elaborates", "Contrasts",
        "ExampleOf", "Causes", "PartOf", "RelatedTo"
    ]
}
```

后端要有一张前端 7 类标签到 Graphiti canonical edge type 的映射表. 前端 `ai-linked-doc` 产出什么标签, 后端做 `frontend_label -> GraphitiEdgeType` 的显式映射, 不要把"关系名"散落在 prompt、前端常量、Neo4j label、Graphiti edge_name 四处.

### 议题三：`search_communities` 的产品落地

Graphiti community: 一组强连接实体节点的聚类, 调用 `build_communities()` 生成, 底层用 Leiden algorithm, community 自带 summary.

Dashboard 设计:

```text
最近 30 天错误模式
────────────────────────
A. 递归边界条件      7 次   最近一次: 2 天前
   关联节点: recursion-base-case, dfs-stop-condition
   典型表现: 忘记 base case / 边界 off-by-one
   推荐动作: 3 题边界专项 + 1 次口述证明

B. BST 平衡判断      4 次   最近一次: 5 天前
   关联节点: bst-height, avl-rotation
   典型表现: 平衡条件与高度定义混淆

C. DP 状态转移       3 次   最近一次: 9 天前
   关联节点: knapsack-state, transition-equation
```

落地: 白天事件写入, 夜间 `build_communities(group_id=gid)`, 查询端走 `COMMUNITY_HYBRID_SEARCH_RRF` 或 facade 的 `search_error_communities()`.

### 议题四：1h sweep 延迟与即时查询之间的折中

**裁决**: **保留 sweep, 但把 sweep 从"主路径"降为"保险丝"**.

Graphiti 官方本来就是 real-time incremental updates; `add_episode_bulk` 不做 invalidation 更说明"有版本链的事件"应该尽量在线按条写.

Canvas 当前 spec 把 1-60 分钟视为可接受延迟, 对"批注+双链探索+针对性考察"闭环, 这个延迟太长了.

建议:
- 保存后立即 enqueue
- 当前画布查询前强制 flush 当前 pending events
- 5 分钟 sweep 补漏
- 夜间 build communities
- 如果 flush 超时, 就只降级当前 query, 不放弃长期写入

### 议题五：Graphiti edge vs Neo4j edge 协调

**硬裁决**: **Neo4j 是"显式结构真相层", Graphiti 是"时序记忆层", 两者不能再互相冒名顶替**.

现在的 `relationship_sync_service` 文档写的是"frontmatter relationships → Graphiti edges", 但实现里却通过 `Neo4jEdgeClient` 构造 `EdgeRelationship` 并调用 `add_edge_relationship()` (`backend/app/services/relationship_sync_service.py:1-9, 138-169`). `review_service` 也有一条单独的 `add_edge_relationship + add_episode_for_edge` 路径 (`backend/app/services/review_service.py:1412-1434`).

这就是"Graphiti edge vs Neo4j edge 设计协调"问题本体: **逻辑层没分清"谁是 canonical topology, 谁是 temporal interpretation"**.

**协调规则**:

- **显式 wikilink / frontmatter / review 关系**: 先写 Neo4j 结构真相层, edge_id 稳定; 再镜像一份到 Graphiti, 但 Graphiti 的用途是时序查询、用户历史、关系检索, 不是替代 Neo4j 当拓扑主表
- **callout / error / calibration / belief correction**: 只写 Graphiti, 除非它被用户明确升级为 frontmatter 或系统判定为 canonical relation
- **同一关系跨层共享 `edge_id` / `belief_key`**, 避免漂移

`docs/known-gotchas.md` 里对 G-FAKE-001 和 G-PIPE-003 的历史记录已经提醒过: 这个项目吃过"名字像 Graphiti, 身体不是 Graphiti""桥接有了但没有形成单一主干"的亏.

### 议题六：`group_id` 隔离机制审计

**结论**: **设计方向正确, 但仍有一个高风险薄弱点: 默认 `DEFAULT_GROUP_ID`**.

Canvas 内部 group_id 规范定为 `vault:<vault_id>[:<subject_or_canvas>]`, 在 Graphiti 边界用 `sanitize_group_id_for_graphiti()` 把 `:` 变成 `__`, 这是正确做法.

问题在 `relationship_sync_service`: group_id 缺失时会回落到 `DEFAULT_GROUP_ID` (`backend/app/services/relationship_sync_service.py:133-169`).

在一个"以 vault 隔离用户图谱"为核心假设的系统里, 这不只是代码味道问题, 而是**跨图污染风险**.

应该直接改接口签名:

```python
async def sync_relationships_in_vault(
    vault_root: str | Path,
    *,
    vault_id: str,
    subject_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    group_id = build_vault_group_id(vault_id, subject_id=subject_id)
```

## Part 4: 学习科学价值评估

下面的 d 值是**产品机制推断值**, 不是 A/B 实验实测值. 用来排优先级.

| Graphiti 能力真正落地后 | 学习者可感知变化 | 预估 d 值增益 | 原因 |
|---|---|---:|---|
| **批注演化追踪** | 能看到"我以前怎么想、后来怎么改" | **+0.20 ~ +0.35** | 把纠错从一次性反馈, 升级为"可回看、可比较的概念重构史" |
| **关系级检索用于出题/检验** | 系统不只看节点文本, 而是真查"这个点与哪些点、哪类误区相关" | **+0.15 ~ +0.25** | 题目更针对"关系性薄弱点", 而不是泛泛围绕节点正文 |
| **错误模式 communities** | 能看见"我总是在哪一类题型/结构上犯错" | **+0.10 ~ +0.20** | 把离散错误折叠成可行动训练单元 |
| **三者联动** | 批注、节点关系、错误聚类形成闭环 | **+0.35 ~ +0.55** | 真正的收益不是单点, 是"写下批注 → 记住关系 → 下次按历史错因追问"的闭环 |

**当前实现的 Graphiti 学习科学收益其实很低** — 模型很强, 但停留在"记了一些 episode, 但出题、检验、复盘没有系统地按 relation / community / temporal history 去读". Graphiti 更像"后台日志"而非"学习记忆器".

## Part 5: 与现有 Canvas 设计的冲突与协调

真正健康的架构, 不是让 Graphiti 抢完所有工作, 而是把它放到**它比 Neo4j / LanceDB / RAG 其他路由明显更有优势的位置**.

| 层 | 该层的"真相" | 应承担的职责 | 不该承担的职责 |
|---|---|---|---|
| **Neo4j 显式结构层** | wikilink / frontmatter / review 这些显式确定关系 | 拓扑、邻居遍历、显式依赖结构 | 用户信念演化、批注历史版本 |
| **Graphiti 时序记忆层** | 用户学习事件、批注修正、错误与校准历史 | temporal facts、history-aware relation recall、error communities | 做原始整篇 md 的替代存储 |
| **LanceDB / vault_notes 文本层** | 原始节点内容与局部文本召回 | 快速读节点正文、本地上下文 | 表达"我过去曾信什么、后来怎么修正" |
| **Agentic RAG 路由层** | 问题意图判断 | 选择走"节点正文 / 显式邻居 / Graphiti facts / communities" | 自己发明一套新的持久化语义 |

**路由规则写死**:
- 问"这个节点讲了什么" → **LanceDB / raw md**
- 问"这个节点和哪些点有关" → **Neo4j 邻居 + Graphiti facts**
- 问"我以前怎么理解这个点, 后来又怎么改" → **Graphiti temporal facts**
- 问"我最近总错哪一类" → **Graphiti communities**
- 问"这道题该围绕什么薄弱点问" → **Graphiti facts + recent callouts + Neo4j explicit neighbors**

**Graphiti 不该替代六路 Agentic RAG; 它应该成为其中负责"时间"和"关系历史"的那一路**. 边界不立住, Graphiti 就会继续变成"看起来都能做, 但真正提问时经常不被调用"的背景设施.

## Part 6: Sprint 优先级

**裁决**: **Sprint 2 修"写对", Sprint 3 修"读对", Sprint 4+ 再修"看懂模式"**.

| Sprint | 必做项 | 目标 | 估时 |
|---|---|---|---:|
| **Sprint 2** | 统一 `CanvasGraphEpisodeV1`; 补 `edge_type_map` 透传; callout/wikilink/calibration 统一进 `add_episode`; `relationship_sync_service` 改生产可写; 移除 `DEFAULT_GROUP_ID` 回落; 查询前 flush 当前 canvas pending events | 先让系统**真的记住批注与关系** | **28-36h** |
| **Sprint 3** | `GraphitiRelationService.search_relation_facts()`; 把 relation recall 接进 LITE-4-3 / LITE-5-7 / 评分复盘; 建立 `belief_key` 版本链; 最小历史 UI (当前版 + 上一版) | 让系统**真的查得回历史关系与改法** | **20-28h** |
| **Sprint 4+** | `build_communities()` job; `search_error_communities()`; 错误模式 Dashboard; 历史数据 backfill; 更细粒度 edge ontology 调优 | 让系统**看得懂你反复错在哪一类** | **20-30h** |

**最小必修包 (如果必须再压缩)**:

1. **统一事件 schema + add_episode 真接通 callout/wikilink**
2. **`edge_type_map` 透传**
3. **同一 belief 的 `valid_at/invalid_at` 版本链**
4. **查询前 flush 当前 canvas pending events**
5. **`search_relation_facts()` 接到出题/检验/复盘主链**

只做这五件事, Graphiti 在 Canvas 里就会**第一次从"有"变成"有用"**.

## Part 7: 一句话产品判定

> **Graphiti 时序图谱在 Canvas 的设计, 目前还没有真正服务于用户"记忆批注 + 记忆节点关系"的核心需求; 当前主要问题是写入覆盖不完整、关系层双写失真、`valid_at/invalid_at` 没形成版本链、`search_facts/search_communities` 不在主产品读路径里; 推荐 Sprint 2 必修统一事件 schema、补 `edge_type_map`、上线 production sync、去掉 1h-only 主路径, 并把"同一 belief 的历史演化"做成可查的 canonical fact 链.**

## 开放问题与局限

这份审计的仓内证据以你上传的 XML bundle 为准; 我没有把未展开的 `ai-linked-doc.ts` 常量区逐字重抄进来, 所以"7 类关系"的最终 label 名称仍应以后端 canonical map 对齐前端实际常量为准.

另一个需要在开发时再确认的是: 当前 Graphiti 版本里若要直接更新既有 edge 的 `invalid_at`, 最终应走项目现有的 Graphiti client CRUD 封装, 或走"episode + canonical triplet rewrite"策略; 不建议把这一步留给模糊的 prompt-based 自动失效逻辑.

---

**Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**ChatGPT 引用来源**:
- Graphiti 官方文档: https://help.getzep.com/graphiti
- Graphiti GitHub: https://github.com/getzep/graphiti
- Graphiti quickstart README + 时序追踪示例
- Graphiti v3 公开 API + MCP README (search_nodes / search_facts 工具名)
