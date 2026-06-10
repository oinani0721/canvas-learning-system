# Graphiti-Native 学习记忆重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: 用 superpowers:subagent-driven-development 或 executing-plans 逐 task 实施。步骤用 `- [ ]` checkbox 追踪。
> **Plan ID:** GRAPHITI-NATIVE-MEMORY-2026-06-10 · 代码主线 = main 检出 + worktree 后端需对齐（见 §0.3）

**Goal:** 把"批注/节点增殖/错误/belief"的写入和检验白板读取，从当前裸 Neo4j（G-FAKE）改成真正落在 Graphiti canonical `:Entity`-`RELATES_TO` bitemporal 图上，让用户的时序记忆既能精确按 node 召回、又保留演化回溯。

**Architecture:** 三层——① 身份层（`node_id ↔ entity_uuid` 确定性映射，单一真相源）② 结构化 Graphiti 写入适配器（确定性 `EntityNode/EntityEdge.save` 到 `:Entity/RELATES_TO`，零 LLM）③ 读侧精确读（`EntityEdge.get_by_node_uuid` + 属性过滤 + 可选 `center_node_uuid` 局部语义扩展）。掌握度仍由 FSRS/答题闭环负责，Graphiti 只做记忆/上下文层。

**Tech Stack:** Python 3.14 / FastAPI / Neo4j 5 (bolt 7691) / graphiti-core 0.28.2 (GeminiClient) / pytest。

---

## §0 背景与裁决依据

### 0.1 为什么重构（证据链）
- 两份独立对抗审查 + ChatGPT 对抗审查 + 实读 0.28.2 源码确认：当前 G-FAKE+G-PIPE（CRITICAL）。
- 致命错配：`question_generator._get_tips` 查 `(:EpisodicNode {node_id})`，但 Graphiti 写的是 `(:Episodic)` 无 node_id（`graphiti_core/models/nodes/node_db_queries.py`）→ 检验白板读恒为空集。
- `valid_at/invalid_at` 学习链零消费（G-PIPE）；Graphiti AI(Gemini) 真写的节点零下游消费者。
- 完整诊断见 `_bmad-output/研究/2026-06-03-S2-2批注重塑认知-下一步开发计划.md` + XML 包 `.gdr/research-pack-graphiti-vs-neo4j-architecture.xml`。

### 0.2 锁定的设计决策（D1-D7）

| # | 决策 | 依据（实读源码/审查） |
|---|---|---|
| **D1** | Canonical graph = Graphiti `:Entity`-`RELATES_TO`-`:Episodic`。**禁止**用 `:EpisodicNode{node_id}` / 裸 `:CanvasNode/CANVAS_EDGE` 充当 Graphiti 记忆 | ChatGPT 裁决 + node_db_queries.py |
| **D2** | 结构化用户显式标注（tip/callout/error/relation 原因/belief 版本）走**确定性 `EntityEdge.save()` / `EntityNode.save()`**（零 LLM），**不走 `add_triplet`** | 实读 `graphiti.py:1450-1568`：add_triplet 跑 3×embedding+2×search+`resolve_extracted_edge(llm_client)`，高频成本不可接受；显式事件不需 LLM 猜矛盾 |
| **D3** | 身份层：`entity_uuid = uuid5(NAMESPACE_DNS, f"{node_id}:{group_id}")` 作为 node 的稳定身份，**单一真相源**，所有 writer/reader 共用 | 审查 M2 + ChatGPT "身份层是命门"；belief 链 `_ensure_entity_node` 已有雏形 |
| **D4** | `node_id` / `belief_key` / `source` / `event_type` / `tags` 写进 **edge/node 的 `attributes`**（Neo4j 上扁平为顶层属性可精确查） | 实读 `edges.py:359` `edge_data.update(attributes)` |
| **D5** | 读侧用 `EntityEdge.get_by_node_uuid(driver, entity_uuid)` 取节点全部边 + 应用层属性过滤；语义扩展用 `search(center_node_uuid=...)`。**禁止** `search(property_filters=...)`（D1: property_filters 声明但 search.py 不消费） | 实读 `edges.py:535 get_by_node_uuid` + ChatGPT 证实 property_filters 未消费 |
| **D6** | `episode_worker.add_episode` 收窄到**仅非结构化材料**（对话归档/会话摘要/自由文本日志/历史回灌） | ChatGPT 第三步 |
| **D7** | 删除 Fix-D（`memory_service._write_exam_queryable_episode` 裸 `:EpisodicNode`）；Fix-E1（`node_relationship_sync_service`）**降级为 `canvas_projection_sync`（显式声明"仅 UI/拓扑投影、非记忆真相源"），不删**——因 `_get_kg_relevance` 本期仍读 `CANVAS_EDGE`，删了会隐性改选题公式输入分布 | ChatGPT 计划审查（降级 not 删）|
| **D8（新增，ChatGPT 计划审查）** | 结构化 writer **必须生成 embedding**（写前调 `node.generate_name_embedding(embedder)` / `edge.generate_embedding(embedder)`），否则结构化图无 embedding → `center_node_uuid` 语义扩展失效 | 实读 `edges.py:330-367` save **不生成** embedding（只写当前值）; `graphiti.py:1453-1458` add_triplet 才生成 |
| **D9（新增，ChatGPT 计划审查）** | reader 必须 **active-only 过滤**（`e.invalid_at is None`）+ relation 边 **方向过滤**（`e.source_node_uuid == 本节点 uuid`）——因 `get_by_node_uuid` 是 undirected 返回全 incident 边、且 belief 会把旧版标 superseded | 实读 `edges.py:535` `MATCH (n)-[e:RELATES_TO]-(m)` undirected; belief 旧边 invalid_at+superseded |
| **D10（新增，ChatGPT 计划审查）** | belief 链 = **统一入口不统一内部**：`structured_writer` 对外统一门面，belief 版本链内部仍委托 `graphiti_belief_service.update_belief_version_chain`（保版本语义） | ChatGPT：别为整齐抽薄版本链 |
| **D11（新增，ChatGPT 计划审查）** | **release 顺序约束**：Phase 2(切写) 与 Phase 3(切读) **必须同一发布单元**（或 Phase 3 先做 dual-read/feature-flag 再切写），禁止 Phase 2 单独上线——否则"新写旧读"窗口 | ChatGPT：避免切换窗回归 |

### 0.3 ⚠️ 分支/部署前置（必须先解决）
- docker 后端挂载的是 **worktree backend**（缺 P0 批次 + S2-2 + Fix-D/E1），代码修复在 **main**。两分支大幅分叉（main..worktree backend 差 ~26000 行）。
- **本计划代码落在哪个分支需先决策**（见 §Phase -1）。在确定前，不要 docker 部署。
- belief 链（`graphiti_belief_service.py`，写 `:Entity/RELATES_TO`，**不是 G-FAKE**）是本计划的**正确范式参考**，应复用其 `_ensure_entity_node` / `EntityEdge.save` 模式。

### 0.4 精确 API 契约（实读 0.28.2，写代码直接用）
```python
from graphiti_core.nodes import EntityNode      # EntityNode(uuid=, name=, group_id=, labels=, summary=, attributes={})
from graphiti_core.edges import EntityEdge      # EntityEdge(group_id=, source_node_uuid=, target_node_uuid=, created_at=, name=, fact=, valid_at=, invalid_at=, attributes={})
# 写: await node.save(driver) / await edge.save(driver)  —— 纯写库, attributes 扁平为顶层属性 (Neo4j)
# 读: await EntityNode.get_by_uuid(driver, uuid)
#     await EntityNode.get_by_group_ids(driver, group_ids, limit=None)
#     await EntityEdge.get_by_node_uuid(driver, node_uuid)       ← 读某节点全部边 (读侧核心)
#     await EntityEdge.get_by_group_ids(driver, group_ids, limit=None)
# group_id 边界: from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
```

---

## §File Structure

| 文件 | 动作 | 责任 |
|---|---|---|
| `backend/app/graphiti/identity_registry.py` | **新建** | D3 身份层: node_id↔entity_uuid 确定性映射 + ensure_entity_node 单一入口 |
| `backend/app/services/graphiti_structured_writer.py` | **新建** | D2 结构化写入: write_callout / write_error / write_relation_reason / write_belief_version → :Entity/RELATES_TO |
| `backend/app/services/graphiti_memory_reader.py` | **新建** | D5 精确读: read_node_tips / read_node_errors / read_node_edge_reasons (get_by_node_uuid + 属性过滤) |
| `backend/app/services/memory_service.py` | **改** | record_knowledge_entity 删 neo4j.record_episode 双写 + 删 _write_exam_queryable_episode(Fix-D), 改调 structured_writer |
| `backend/app/services/question_generator.py` | **改** | _get_tips/_get_error_history/_get_edge_reasons 改调 graphiti_memory_reader |
| `backend/app/services/episode_worker.py` | **改** | D6: 加注释/守卫, 结构化 event_type 不再走此路（仅非结构化） |
| `backend/app/services/graphiti_belief_service.py` | **复用/微调** | 已是正确范式; _ensure_entity_node 抽到 identity_registry 统一 |
| `backend/app/services/node_relationship_sync_service.py` (Fix-E1) | **降级/删** | §Phase 4 决策: 删 或 改名为 canvas_projection_sync 明确声明 UI 投影 |
| `backend/scripts/verify_graphiti_native_chain.py` | **新建** | 端到端验证(替代旧 verify_targeted_exam_chain): 全程 :Entity/RELATES_TO, 断言无 :EpisodicNode{node_id} |
| `backend/tests/unit/test_identity_registry.py` 等 | **新建** | 各 Phase 单测 |

---

## §Phase -1: 分支决策（阻塞，需用户拍板，0 代码）

- [ ] **Step 1: 决定代码落哪个分支 + docker 怎么对齐**
  - 选项 A: 代码继续提 main，把 docker-compose 改成挂 main backend（一次性对齐，之后单分支）。
  - 选项 B: 在 worktree 分支做，docker 直接生效，但要先把 main 的 P0 批次/S2-2 cherry-pick 进 worktree。
  - 选项 C: 先 merge/对齐两分支 backend，再单线开发。
  - **产出**: 用户确认分支策略后才进 Phase 0。本步无代码。

---

## §Phase 0: 身份层 identity_registry（基础，最高优先级）

**Files:**
- Create: `backend/app/graphiti/identity_registry.py`
- Test: `backend/tests/unit/test_identity_registry.py`

- [ ] **Step 1: 写失败测试**
```python
# test_identity_registry.py
import pytest
from app.graphiti.identity_registry import entity_uuid_for_node, IdentityRegistry

def test_entity_uuid_deterministic():
    u1 = entity_uuid_for_node("recursion-base-case", "vault__cs_61b__recursion")
    u2 = entity_uuid_for_node("recursion-base-case", "vault__cs_61b__recursion")
    assert u1 == u2 and len(u1) == 36  # uuid5 str

def test_entity_uuid_namespaced_by_group():
    a = entity_uuid_for_node("x", "vault__a")
    b = entity_uuid_for_node("x", "vault__b")
    assert a != b  # 同 node_id 不同 group → 不同身份 (防跨 vault 串)
```
- [ ] **Step 2: 跑测试确认 FAIL**
  Run: `cd backend && .venv/bin/python -m pytest tests/unit/test_identity_registry.py -x -q`  Expected: FAIL (module not found)
- [ ] **Step 3: 实现 identity_registry.py**
```python
"""D3 身份层: node_id ↔ Graphiti entity_uuid 的单一确定性映射真相源。
所有 writer/reader 必须经此取 uuid, 否则三套命名空间(Canvas node_id / belief 自造 /
add_episode LLM 抽取名)会再次分裂 (审查 M2 + ChatGPT 命门)。"""
from __future__ import annotations
from uuid import NAMESPACE_DNS, uuid5
from typing import Any
from graphiti_core.nodes import EntityNode
from graphiti_core.errors import NodeNotFoundError   # D-审查: 只捕节点不存在, 不吞驱动故障

def entity_uuid_for_node(node_id: str, sanitized_group_id: str) -> str:
    """同 (node_id, group_id) 跨 run 稳定; 不同 group 隔离。group_id 须已 sanitize。"""
    return str(uuid5(NAMESPACE_DNS, f"{node_id}:{sanitized_group_id}"))

class IdentityRegistry:
    """确保某 node_id 对应的 :Entity 节点存在并复用其 uuid (幂等)。"""
    @staticmethod
    async def ensure_entity_node(driver: Any, node_id: str, sanitized_group_id: str,
                                 embedder: Any = None, title: str = "") -> str:
        uuid = entity_uuid_for_node(node_id, sanitized_group_id)
        try:
            await EntityNode.get_by_uuid(driver, uuid)
            return uuid
        except NodeNotFoundError:   # ⚠️审查: 只捕这个, 别 except Exception (会吞驱动故障)
            node = EntityNode(uuid=uuid, name=node_id, group_id=sanitized_group_id,
                              summary=title or node_id, attributes={"node_id": node_id})
            if embedder is not None:   # D8: 生成 embedding, 否则结构化图无法语义召回
                await node.generate_name_embedding(embedder)
            await node.save(driver)
            return uuid
```
- [ ] **Step 4: 跑测试确认 PASS** — `pytest tests/unit/test_identity_registry.py -x -q`
- [ ] **Step 5: Commit** — `git commit -m "feat(graphiti): 身份层 identity_registry (node_id↔entity_uuid) [GRAPHITI-NATIVE-MEMORY-2026-06-10]"`

> ⚠️ **开放设计点（Phase 0 需确认）**: add_episode LLM 抽取的实体名与本层 node_id-uuid 不一致——是 (a) 让结构化层独占 node_id-uuid 命名空间、add_episode 节点单独存且不参与 node 精确读；还是 (b) 加一层别名/合并表。本计划默认 (a)（最简、最可控），(b) 列后续。

---

## §Phase 1: 结构化 Graphiti 写入适配器（核心）

**Files:**
- Create: `backend/app/services/graphiti_structured_writer.py`
- Test: `backend/tests/unit/test_graphiti_structured_writer.py`

设计: 每类事件 → 一条 `:Entity`-[`RELATES_TO`]->`:Entity` 边，`attributes` 带 `node_id/source/event_type/belief_key`。callout/error 自环 (src==tgt); relation 原因用真实 src/tgt。

- [ ] **Step 1: 写失败测试（用 FakeDriver 捕获 save，不连 Neo4j）**
```python
# test_graphiti_structured_writer.py — 复用 belief 测试的 FakeEdgeStore 模式
import pytest
from datetime import datetime, timezone
from graphiti_core.edges import EntityEdge
from app.services import graphiti_structured_writer as w

class FakeDriver:  # 最小 driver double
    provider = "neo4j"

async def test_write_callout_produces_relates_to_with_node_id(monkeypatch):
    saved = []
    async def fake_edge_save(self, driver): saved.append(self)
    async def fake_ensure(driver, node_id, gid, title=""): return f"uuid-{node_id}"
    monkeypatch.setattr(EntityEdge, "save", fake_edge_save)
    monkeypatch.setattr(w.IdentityRegistry, "ensure_entity_node", staticmethod(fake_ensure))
    edge = await w.write_callout(FakeDriver(), node_id="recursion", group_id="vault:cs_61b:rec",
                                 callout_type="tip", text="先想 base case",
                                 occurred_at=datetime(2026,6,1,tzinfo=timezone.utc))
    assert edge.attributes["node_id"] == "recursion"
    assert edge.attributes["source"] == "callout"
    assert edge.attributes["event_type"] == "callout_added"
    assert edge.source_node_uuid == edge.target_node_uuid  # 自环
    assert edge.name in ("SelfAnnotation",)  # :Entity-RELATES_TO, name=语义类型
```
- [ ] **Step 2: 跑确认 FAIL**
- [ ] **Step 3: 实现 graphiti_structured_writer.py**（关键函数；复用 group_id_compat + IdentityRegistry）
```python
"""D2 结构化写入: 把用户显式标注确定性写入 Graphiti :Entity/RELATES_TO (零 LLM)。
不走 add_triplet (实读 graphiti.py:1450-1568 证实其跑 LLM+2search+embedding)。"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from graphiti_core.edges import EntityEdge
from app.graphiti.identity_registry import IdentityRegistry
from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti

async def _self_loop_edge(driver, embedder, *, node_id, group_id, name, fact, occurred_at, attributes):
    gid = sanitize_group_id_for_graphiti(group_id)
    uuid = await IdentityRegistry.ensure_entity_node(driver, node_id, gid, embedder=embedder)
    edge = EntityEdge(group_id=gid, source_node_uuid=uuid, target_node_uuid=uuid,
                      created_at=occurred_at, valid_at=occurred_at, invalid_at=None,
                      name=name, fact=fact, attributes={**attributes, "node_id": node_id})
    if embedder is not None:        # D8: save 不自动生成 embedding, 必须显式生成
        await edge.generate_embedding(embedder)
    await edge.save(driver)
    return edge

# embedder 由调用方传入 (episode_worker/memory_service 持有的 self._graphiti.embedder)
async def write_callout(driver, embedder, *, node_id, group_id, callout_type, text, occurred_at):
    return await _self_loop_edge(driver, embedder, node_id=node_id, group_id=group_id,
        name="SelfAnnotation", fact=text, occurred_at=occurred_at,
        attributes={"source": "callout", "event_type": "callout_added", "callout_type": callout_type})

async def write_error(driver, embedder, *, node_id, group_id, error_type, description, occurred_at):
    return await _self_loop_edge(driver, embedder, node_id=node_id, group_id=group_id,
        name="SelfMisconception", fact=description, occurred_at=occurred_at,
        attributes={"source": "error", "event_type": "error_marked", "error_type": error_type})

async def write_relation_reason(driver, embedder, *, source_node_id, target_node_id, group_id,
                                relation_type, reason, occurred_at):
    gid = sanitize_group_id_for_graphiti(group_id)
    su = await IdentityRegistry.ensure_entity_node(driver, source_node_id, gid, embedder=embedder)
    tu = await IdentityRegistry.ensure_entity_node(driver, target_node_id, gid, embedder=embedder)
    edge = EntityEdge(group_id=gid, source_node_uuid=su, target_node_uuid=tu,
                      created_at=occurred_at, valid_at=occurred_at, invalid_at=None,
                      name=relation_type or "RelatedTo", fact=reason,
                      attributes={"node_id": source_node_id, "source": "relation",
                                  "event_type": "wikilink_added", "relation_type": relation_type})
    if embedder is not None:        # D8
        await edge.generate_embedding(embedder)
    await edge.save(driver)
    return edge
# belief 版本演化: D10 复用 graphiti_belief_service.update_belief_version_chain (已正确, 写 :Entity/RELATES_TO)
#   structured_writer 仅做统一门面转发; 不重写其旧边 supersede / as_of 版本语义。

```
- [ ] **Step 4: 跑确认 PASS**
- [ ] **Step 5: Commit** — `feat(graphiti): 结构化写入适配器 :Entity/RELATES_TO (零 LLM) [GRAPHITI-NATIVE-MEMORY-2026-06-10]`

---

## §Phase 2: 砍双写 + 删 Fix-D

**Files:** Modify `backend/app/services/memory_service.py`

- [ ] **Step 1: 写测试断言 record_knowledge_entity 不再调 neo4j.record_episode、改调 structured_writer**
```python
async def test_record_knowledge_entity_uses_structured_writer_not_record_episode(monkeypatch):
    # spy: structured_writer.write_callout 被调; neo4j.record_episode 不被调
    ...（捕获两者调用，断言 write_callout 调用1次、record_episode 0次）
```
- [ ] **Step 2: FAIL**
- [ ] **Step 3: 改 record_knowledge_entity** —— 删 `self.neo4j.record_episode(...)` 块（memory_service.py:~1250-1267）+ 删整个 `_write_exam_queryable_episode`(Fix-D) + 把结构化 event_type 路由到 structured_writer.write_callout/write_error；非结构化保留 _enqueue_episode。
- [ ] **Step 4: PASS + 回归 `pytest tests/unit -q` 对比基线零新增**
- [ ] **Step 5: Commit** — `refactor(memory): 删 record_episode 双写 + Fix-D 裸Cypher, 改走 Graphiti 结构化写入`

---

## §Phase 3: 读侧重写（检验白板真读 Graphiti）

**Files:** Create `backend/app/services/graphiti_memory_reader.py`; Modify `question_generator.py`

- [ ] **Step 1: 写测试（seed :Entity/RELATES_TO 边 → reader 按 node_id 读到）** —— 用 FakeEdgeStore 或真实 Neo4j 集成测试
```python
async def test_read_node_tips_via_get_by_node_uuid(monkeypatch):
    # monkeypatch EntityEdge.get_by_node_uuid 返回带 attributes.source='callout' 的边
    tips = await reader.read_node_tips(driver, node_id="recursion", group_id="vault:cs_61b:rec")
    assert tips == ["先想 base case"]  # fact 提取, 按 source='callout' 过滤
```
- [ ] **Step 2: FAIL**
- [ ] **Step 3: 实现 graphiti_memory_reader.py**
```python
"""D5 精确读: node_id → entity_uuid → EntityEdge.get_by_node_uuid → 属性过滤。
不用 search(property_filters) (D1: 未消费); 语义扩展才用 search(center_node_uuid)。
⚠️D9: get_by_node_uuid 是 undirected(MATCH (n)-[e]-(m), edges.py:535) 返回【全部 incident 边】,
必须 active-only(invalid_at is None) 过滤; relation 还要方向过滤(source==本节点)对齐旧出边行为。"""
from graphiti_core.edges import EntityEdge
from graphiti_core.errors import EdgeNotFoundError
from app.graphiti.identity_registry import entity_uuid_for_node
from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti

async def _node_uuid_and_edges(driver, node_id, group_id):
    gid = sanitize_group_id_for_graphiti(group_id)
    uuid = entity_uuid_for_node(node_id, gid)
    try:
        edges = await EntityEdge.get_by_node_uuid(driver, uuid)
    except EdgeNotFoundError:
        edges = []
    # D9: active-only —— 排除被 belief 链 supersede 的旧版本
    active = [e for e in edges if e.invalid_at is None]
    return uuid, active

async def read_node_tips(driver, node_id, group_id):
    _u, edges = await _node_uuid_and_edges(driver, node_id, group_id)
    return [e.fact for e in edges if (e.attributes or {}).get("source") == "callout"]

async def read_node_errors(driver, node_id, group_id):
    _u, edges = await _node_uuid_and_edges(driver, node_id, group_id)
    return [{"error_type": (e.attributes or {}).get("error_type", "unknown"), "description": e.fact}
            for e in edges if (e.attributes or {}).get("source") == "error"]

async def read_node_edge_reasons(driver, node_id, group_id):
    uuid, edges = await _node_uuid_and_edges(driver, node_id, group_id)
    # D9 方向过滤: 旧 _get_edge_reasons 只查出边, 这里对齐 (source==本节点)
    return [e.fact for e in edges
            if (e.attributes or {}).get("source") == "relation" and e.source_node_uuid == uuid]

async def read_node_conversation_summary(driver, node_id, group_id):
    # ⚠️审查: 旧 _get_conversation_summary 也查 :EpisodicNode{node_id}(坏 schema)。
    # 裁决(默认): 归档对话时由 structured_writer 额外写一条 source='conversation' 摘要边
    # (自由文本全文仍走 add_episode 做语义), 这里按 source 读结构化摘要。
    _u, edges = await _node_uuid_and_edges(driver, node_id, group_id)
    convs = [e.fact for e in edges if (e.attributes or {}).get("source") == "conversation"]
    return convs[0] if convs else ""
```
- [ ] **Step 4: 改 question_generator** —— `_get_tips/_get_error_history/_get_edge_reasons/_get_conversation_summary` 四个改调 `graphiti_memory_reader.*`（删裸 Cypher）。`select_target_node` 选题公式不动；`_get_kg_relevance` **本期不动**（D5/D7 短期保留 CanvasNode 拓扑, 故 Fix-E1 降级不删）。
  > ⚠️审查补: `_get_conversation_summary` 当前也查 `:EpisodicNode{node_id}`（worktree question_generator.py:1111-1128），同坏 schema，本 Phase 一并迁移（见 reader 注释裁决）。
- [ ] **Step 5: PASS + Commit** — `refactor(exam): 检验白板读侧改走 Graphiti :Entity/RELATES_TO 精确读`

---

## §Phase 4: episode_worker 收窄 + Fix-E1 处置

- [ ] **Step 1: episode_worker `_process_episode` 加守卫** —— 结构化 event_type（callout/error/relation）不应再进此路（应已被 Phase 2 改走 writer）；加断言/日志，保留对话归档等非结构化。
- [ ] **Step 2: Fix-E1 降级（D7 改, 不删）** —— `node_relationship_sync_service` 改名 `canvas_projection_sync`，文件头显式声明"仅 UI/拓扑投影视图、非 Graphiti 记忆真相源"；保留到 `_get_kg_relevance` 迁移完成再考虑物理删除（删早了会隐性改选题公式输入分布）。原因边的**记忆真相**已由 Phase 1 `write_relation_reason` 进 Graphiti。
- [ ] **Step 3: Commit**

---

## §Phase 4.5: 历史数据回填（⚠️审查必加, 否则上线"记忆丢失")

**问题**: Phase 3 读侧切到 Graphiti-native 后, 旧 `:Episodic`/`:CanvasNode` 里的历史 callout/error/relation **不会自动出现** → 用户体感"升级后记忆没了"。

**本项目幸运点**: 真实 Neo4j 普查 canonical EpisodicNode=0 / CANVAS_EDGE=0(实测), 历史记忆主要在 **vault markdown**(callout + frontmatter relationships) → 回填 = 重放 vault。

- [ ] **Step 1: 写回填脚本 `backend/scripts/backfill_graphiti_structured.py`** —— 扫 vault: 每个节点的 callout([!tip]/[!question]/[!error]) → `structured_writer.write_callout/write_error`; frontmatter relationships[] → `write_relation_reason`。幂等(确定性 uuid + active 链)。
- [ ] **Step 2: dry-run 打印将写入条数, 用户确认后真跑**
- [ ] **Step 3: 跑 + 验证 read_node_tips 能读到回填的**
- [ ] **Step 4: Commit**

> 备选过渡: 若历史数据多/不在 vault, 改用 Phase 3 dual-read 过渡期(同时读新旧 schema, 灰度切)。

---

## §Phase 5: 端到端验证（替代旧 harness）

**Files:** Create `backend/scripts/verify_graphiti_native_chain.py`

- [ ] **Step 1: 真实 Neo4j 探针** —— 经 memory_service 写一条 callout + 一条 relation 原因 → 断言：
  (a) 图里出现 `:Entity-[:RELATES_TO {node_id, source}]->:Entity`（Graphiti canonical）；
  (b) **无** `:EpisodicNode{node_id}` 新建（证明 Fix-D 已除）；
  (c) `graphiti_memory_reader.read_node_tips/edge_reasons` 读到刚写的；
  (d) belief 版本链改 3 次 → valid_at/invalid_at 链正确（时序回溯真消费）。
- [ ] **Step 2: 跑 + 对比基线 `pytest tests/unit -q` 零新增失败**
- [ ] **Step 3: Commit + 更新 docker（按 Phase -1 决策）**

---

## §Risks（10 条，含 ChatGPT 计划审查新增 5 条）

1. **身份层不统一（最高）**: add_episode LLM 抽取名 vs node_id-uuid 两套命名空间。缓解: Phase 0 结构化层独占 node_id-uuid（"结构化 exact-read 主图" + "add_episode 语义影子图"并存，一期接受同概念裂两节点；二期再加 alias/merge）。
2. **🆕历史数据回填（高，ChatGPT）**: 读侧切 Graphiti-native 后旧数据不自动出现 = "记忆丢失"。缓解: Phase 4.5 回填脚本（重放 vault）或 dual-read 过渡。
3. **🆕切换窗回归（高，ChatGPT）**: Phase 2(切写)/Phase 3(切读) 若分两次发布 → "新写旧读"窗口。缓解: **D11 release 约束**——2+3 同发布单元 或 Phase3 先 dual-read/feature-flag。
4. **🆕embedding 缺失（高，ChatGPT）**: `.save()` 不生成 embedding（实读 edges.py:330-367）→ 结构化图无 embedding，语义扩展/hybrid search 失效。缓解: **D8** writer 显式 generate_embedding。
5. **🆕版本污染（高，ChatGPT）**: belief 把旧版标 superseded，`get_by_node_uuid` 会一起吐回。缓解: **D9** reader active-only(invalid_at is None)过滤。
6. **🆕方向语义变更（中，ChatGPT）**: `get_by_node_uuid` undirected(实读 edges.py:535)，旧 `_get_edge_reasons` 只查出边。缓解: **D9** relation 方向过滤(source==本节点)对齐旧行为。
7. **belief 链 EntityEdge.save 与 add_episode invalidation 软碰撞**（ChatGPT 升级为三重隔离）: 仅 `source` 命名不是硬隔离。真隔离=① 结构化主链不用 add_episode 写 ② 读侧只读结构化 namespace 的 active 边 ③ belief 按 belief_key 精确取链。
8. **自环边读取**: callout/error src==tgt，Phase 3/5 集成测试必须确认 `get_by_node_uuid` 返回自环边（源码 undirected pattern 理应命中，但需实测）。
9. **worktree/main 分支分叉**: Phase -1 不解决 = 改了不生效。
10. **Neo4j save edge 落库**（ChatGPT 疑点2，Neo4j 应正常但需测）: Phase 5 覆盖。

## §Verification（端到端）
- 每 Phase: 单测 green + `pytest tests/unit -q` 对比基线零新增失败。
- Phase 5 真实 Neo4j: 写→读全程 `:Entity/RELATES_TO`，`MATCH (e:EpisodicNode) WHERE e.node_id IS NOT NULL RETURN count(e)` 应为 0（Fix-D 已除）。
- LSP/ruff 每个改动文件干净（DD-03 无 mock/TODO）。

## §开放设计问题（✅ 全部已拍板 2026-06-10，可执行）
1. **Phase -1 分支策略 = C**（✅用户确认）：先对齐 main/worktree 两分支 backend 再单线开发。
2. **Phase 0 add_episode 节点合并 = 本轮不合并**（✅采纳 ChatGPT）：结构化 exact-read 主图 + add_episode 语义影子图并存，二期再 alias/merge。
3. **Phase 4 Fix-E1 = 降级为 canvas_projection_sync 不删**（✅采纳 ChatGPT，已改 D7）。
4. **belief 链 = 统一入口不统一内部**（✅采纳 ChatGPT，已改 D10）。
5. **embedding 策略 = D8 writer 生成 embedding**（✅用户确认）：核实结论——Graphiti 高层 API(add_episode/add_triplet) 管线自动 embed，但底层 `.save()` 纯持久化不 embed（0.28.2 与最新 v0.29.1 行为一致）；D2 选 `.save()` 路径故必须显式 `generate_embedding`（embedding 调用便宜，非 LLM 推理）。
6. **conversation_summary = 归档时写 source='conversation' 摘要边**（✅用户确认）：内容 = AI 在 `archive_conversation(node_id, summary)` 归档对话时生成的对话摘要（conversation_tools.py:33/87-146）；对话全文仍走 add_episode 非结构化通道。改造点：`conversation_tools.archive_conversation` 在 `record_knowledge_entity` 之外/之内增调 `structured_writer.write_conversation_summary`（自环边, fact=summary）。

## §执行完成记录（2026-06-10）

**✅ 全部 Phase 完成, e2e 10 断言全过（真实 Neo4j）, 109 单测 green。**

| Phase | commit | 要点 |
|---|---|---|
| -1 分支对齐 C | 3202142/d27a5e8/712e406/4333c97 + 4ae070a | cherry-pick 4, SKIP P0批次+Fix-D, 基线零新增失败 |
| 0 身份层 | (identity_registry) | uuid5 单一真相源, 7 tests |
| 1 structured_writer | — | 4 writer + belief 门面 + 确定性边 uuid 幂等, 10 tests |
| 2 删双写+路由 | 3d9da86 | record_episode 假写删除, 结构化→writer 主路径, 9 tests |
| 3 读侧重写 | (memory_reader) | 4 读取器→Graphiti 精确读 (D9), 6 tests |
| 4 守卫+降级 | 735c6f6 | D6 守卫 + Fix-E1→canvas_projection_sync |
| 4.5 回填 | (vault_backfill) | 用户真实 vault: 17 批注+4 原因 0 失败已进图 |
| 5 e2e+belief 适配 | 321f27d | verify_graphiti_native_chain 10/10; belief 链首次真实 Neo4j 跑通 |

**实测新发现并修复（计划外, 真实 Neo4j 才现形）**:
- F1: Neo4j save 无 embedding 必 NPE (setNodeVectorProperty) → D8 升级为硬前提
- F2: GeminiEmbedder 默认模型 text-embedding-001 已 404 → 须配 gemini-embedding-001
- F3: get_by_node_uuid undirected 把锚点恒映射为 source → 方向判定改用 attributes.node_id
- F4: belief 链读回旧边无向量, supersede save 会 NPE → load_fact_embedding 回载+embedder 兜底
- F5: 回填 skip 插件模板 callout (💬 围绕这个概念讨论), 已清 4 条噪声边

**遗留**: ⚠️ docker 后端容器需重启加载新代码 (D11: Phase2+3 已同库, 重启即整体生效)。
conversation_tools.archive_conversation 调 write_conversation_summary 的接线由
memory_service 路由覆盖 (event_type=conversation_archive 自动走)。

## §总判定
**✅ 可执行（2026-06-10 终版）**。ChatGPT 计划审查 7 项修正已全部落入（release 约束 D11 / active+方向过滤 D9 / conversation_summary 迁移 / embedding D8 / 回填 Phase 4.5 / Fix-E1 降级 D7 / 三重隔离 risk 7）；3 项核实全部对着 0.28.2 源码确认；§开放问题 6 项全部拍板（分支 C / 不合并 / 降级 / 统一入口 / D8 embed / conversation 摘要边）。**下一步 = Phase -1 执行分支对齐（C），然后 Phase 0 身份层。**

---

## §Self-Review（计划对照裁决）
- D1-D7 每条 → 有对应 Phase（D1=全程；D2=Phase1；D3=Phase0；D4=Phase1 attributes；D5=Phase3；D6=Phase4；D7=Phase2+4）✅
- ChatGPT 优先级（删双写最高 → 结构化 writer → 读侧重写 → 身份层 → episode 收窄 → kg_relevance 最后）→ 本计划顺序 Phase0(身份层提前为基础) → 1(writer) → 2(删双写) → 3(读) → 4(episode) → 5(验证)。**注**: ChatGPT 把"删双写"列最高，本计划把身份层提到 Phase 0 因后续都依赖它；删双写在 Phase 2（writer 就绪后才能安全删，否则写入断流）。此调整理由充分。
- 无占位符: 关键 Phase(0/1/3) 含完整代码; Phase 2/4/5 含明确动作+命令（部分 step 待 Phase -1 分支决策后补 exact 行号，已标注）。
