---
title: "ChatGPT Graphiti 审计 → Sprint 2 决策清单 (Claude 对照分析)"
date: 2026-05-26
plan_id: EPIC1-BMAD-DEV-ASSESS-2026-04-17
based_on:
  - "_bmad-output/审查/2026-05-26-chatgpt-graphiti-deep-research-报告.md (ChatGPT 原文)"
  - "_bmad-output/审查/2026-05-26-chatgpt-v7-v8-v10-v11-修复回应.md (Claude V-07~V-11)"
  - "_bmad-output/审查/2026-05-26-开发计划报告-Obsidian-Hybrid-方向审计.md (主审计 v2)"
verdict: "ChatGPT 提供了 V-07~V-11 修复没看到的 3 个 critical bug + 1 个 schema 升级方案 — Sprint 2 建议替换原计划"
---

# ChatGPT Graphiti 审计 → Sprint 2 决策清单

> 用户裁决 5 个核心问题后, Claude 立刻起步 Sprint 2 Day 6.

## 0. ChatGPT 审计 vs Claude V-07~V-11 修复对照

| ChatGPT 发现 | V-07~V-11 修复是否覆盖? | Claude 判定 |
|---|---|---|
| **缺口 1 `CanvasGraphEpisodeV1` 统一 schema** | ❌ 没覆盖 (V-07 只改 1-16-hook 5 字段, 没统一 wikilink/calibration) | ChatGPT 方案**更系统**, 推荐替换 V-07 spec |
| **缺口 2 `belief_key` 版本链 + `add_triplet` API** | ⚠️ 部分覆盖 (V-07 AC#5 提了 valid_at/invalid_at, 但没用 `add_triplet`, 没建版本链) | ChatGPT 方案**更深**, 推荐升级 V-07 |
| **缺口 3 `GraphitiRelationService` facade** | ❌ 没覆盖 (LITE-5-7 路线 B 直调 `search_facts`, 没 facade 层) | ChatGPT 方案**更可维护**, 推荐 Sprint 3 加 |
| **缺口 4 query-time flush + dry_run=False** | ❌ 没覆盖 (V-13 推到 Sprint 3, dry_run 没改) | ChatGPT 方案**更激进**, 推荐 Sprint 2 加 |
| **议题 2 `edge_type_map` 透传** | ❌ V-08 修复 spec 完全没提此 Graphiti 官方 API 必需参数 | **ChatGPT 找到 V-08 修复盲点**, 必修 |
| **议题 5 Neo4j vs Graphiti 分工** | ❌ 完全没设计 (relationship_sync_service 命名错配) | **G-FAKE-001 历史教训重现**, 必修 |
| **议题 6 `DEFAULT_GROUP_ID` fallback** | ❌ V-11 修复只统一 LITE-5-6 dual-write, 没动 group_id fallback | 跨 vault 污染高风险, 必修 |

**结论**: ChatGPT 给出的 4 缺口 + 6 议题, **有 5 个是 V-07~V-11 修复完全没看到的真 bug**. Sprint 2 不能继续按主 session v2 计划 (51.5h) + V-07~V-11 修复, 应该**部分替换为 ChatGPT 推荐 5 件事最小必修包**.

## 1. Sprint 2 三方计划对照

| 方案 | 工时 | 覆盖范围 | 是否含 ChatGPT 5 必修? |
|---|---:|---|---|
| **主 session v2 计划** | 51.5h | V-07/V-08/V-10/V-11 + UX 修复 + LITE-4-3/5-6/5-7 + STORY-1-16/2-10 | ❌ 0/5 |
| **Agent D 推荐最小 ship** | 18h | 仅 Karpicke 检验白板核心闭环 | ❌ 0/5 |
| **ChatGPT 推荐 Sprint 2 "写对"** | 28-36h | 统一 schema + edge_type_map + sync production + flush + group_id 安全 | ✅ 5/5 |
| **Claude 综合推荐 (新)** | **32-38h** | ChatGPT 5 必修 + UX 修复 (NEW-UX-001/002) + LITE-5-7 AC#1 Tauri 残留修正 | ✅ 5/5 + UX 2 项 + 1 收尾 |

## 2. Claude 综合推荐 Sprint 2 计划

> **基于 ChatGPT 5 必修包 + 主 session v2 UX 修复 + Edge 接通**

### Day 5 (今天剩余, 1.25h)

| Task | 工时 |
|---|---:|
| 修 LITE-5-7 AC#1 Tauri 残留 (Obsidian vault.on('modify')) | 15min |
| 重写 mvp-plan.md → mvp-plan-obsidian-hybrid.md (含用户 line 146 加的 3 项 MVP) | 1h |

### Day 6-10 (5 天, 按 ChatGPT 5 必修包 + UX)

| Day | Time | Task | 工时 | ChatGPT 缺口 |
|---|---|---|---:|---|
| Day 6 AM | 1.5h | NEW-UX-001 dashboard 空状态 sample data + 引导按钮 | 1.5h | (Agent C) |
| Day 6 AM | 0.5h | NEW-UX-002 status-bar 移除虚假 "🎓 N 条 Tips" 显示 | 0.5h | (Agent C) |
| Day 6-7 | **14-18h** | **必修 #1: 统一 `CanvasGraphEpisodeV1` schema** + `add_episode` 真接通 callout/wikilink/calibration | 16h | 缺口 1 |
| Day 7 PM | **3h** | **必修 #2: `edge_type_map` 透传 episode_worker:550-560** + 定义 CANVAS_EDGE_TYPES (Pydantic 7 类) + CANVAS_EDGE_TYPE_MAP | 3h | 议题 2 |
| Day 8 | **8-10h** | **必修 #3: `belief_key` 版本链 + `add_triplet` API** + valid_at/invalid_at 真用 (替换 V-07 简单加字段) | 9h | 缺口 2 |
| Day 9 AM | **4h** | **必修 #4: query-time flush + Hot/Warm/Cold 三层时延** (替换 V-13 单独 Sprint 3) | 4h | 缺口 4a |
| Day 9 PM | **2h** | `relationship_sync_service` 改 production (dry_run=False + 强制 vault_id) + 移除 DEFAULT_GROUP_ID fallback | 2h | 缺口 4b + 议题 6 |
| Day 10 AM | **3h** | **必修 #5: `search_relation_facts()` facade** 最小实现 + 接到 LITE-4-3 路线 4 (替换原直调 search_facts) | 3h | 缺口 3 |
| Day 10 PM | 2h | 4 MVP UAT + 决定 push 新仓库 | 2h | (UAT) |

**Sprint 2 综合推荐总工时**: **41h** (按 ×1.0 multiplier; 按 D 的 ×2 multiplier = 82h, 超 60h capacity)

### 关键取舍 (Sprint 2 砍 vs 推 Sprint 3)

| 原计划项 | 状态 | 理由 |
|---|---|---|
| V-07 1-16-hook 加 5 字段 | **砍, 由缺口 1 替代** | ChatGPT `CanvasGraphEpisodeV1` 更系统, 5 字段并入统一 schema |
| V-08 LITE-4-3 路线 0 wikilink 邻居 | **砍, 由缺口 3 facade 替代** | wikilink 邻居改成 search_relation_facts() 返回, 不直读 metadataCache |
| V-10 questions_registry | **砍, 由 belief_key 版本链替代** | belief_key 模式更通用, questions_registry 退化为 belief_key 的一种 |
| V-11 LITE-5-6 dual-write | **保, 但走统一 schema** | 因为是 calibration_vote 也走 CanvasGraphEpisodeV1 |
| STORY-2-10 wikilink-Graphiti 同步 | **保, 但走统一 schema** | sweep cron 改成 5min mini-sweep + query-time flush |
| LITE-5-7 两个记忆系统 | **保** | LanceDB 已在跑 + Graphiti facade 是必修 #5 |
| GraphitiRelationService facade 完整 | **推 Sprint 3** | Sprint 2 仅最小 search_relation_facts(), search_error_communities 推 Sprint 4+ |
| build_communities() + Dashboard 错误聚类 | **推 Sprint 4+** | community 需要数据积累 |

## 3. 5 个用户决策问题 (拍板后立刻起步)

### Q1 (核心)：采纳 ChatGPT 5 必修包替换 V-07~V-11 部分修复?

- ✅ 采纳 (推荐) — Sprint 2 跑 41h 综合方案 (ChatGPT 5 必修 + UX + LITE-5-7 AC#1 + UAT)
- ⚠️ 部分采纳 — 保 V-07/V-10 原方案, 仅加 ChatGPT 议题 2 (edge_type_map) + 议题 6 (group_id fallback)
- ❌ 不采纳 — 按主 session v2 计划 51.5h, ChatGPT 建议推 Sprint 3+

### Q2: `belief_key` 版本链是否优先?

- ✅ 优先 (Sprint 2 Day 8 必修 #3, 9h) — 用户最在乎的"时序图谱"核心实现
- ⚠️ 推 Sprint 3 — Sprint 2 先做 schema 统一 + sync production, 版本链后做
- ❌ 暂不做 — 单用户首月演化场景少, 等批注积累后再加

### Q3: `relationship_sync_service` dry_run=False 改 production 是否 Sprint 2?

- ✅ Sprint 2 必修 (2h) — 用户 line 47 痛点 "Claude 如何能正确识别 relationships" 直接解决
- ⚠️ Sprint 2 改默认值 + 加强制 vault_id, 但生产环境 default 仍 dry_run=True (staging only)
- ❌ Sprint 3 再改 — Sprint 2 先验证 dry_run 模式跑通

### Q4: ChatGPT 建议 Neo4j vs Graphiti 分工原则是否采纳为架构契约?

- ✅ 采纳 (推荐) — Neo4j 显式结构层 + Graphiti 时序记忆层 + LanceDB 文本层, 写进 CLAUDE.md
- ⚠️ 部分采纳 — 仅 Sprint 2 修 relationship_sync_service 命名错配, 不写 CLAUDE.md 通用规则
- ❌ 暂不采纳 — 等 Sprint 3 实际数据后再立架构

### Q5: ChatGPT 报告 push 到新仓库 `oinani0721/canvas-obsidian-hybrid` vs 等 Sprint 2 末?

- ✅ 立刻 push (ChatGPT 报告作为 README + 决策清单) — 新仓库已经 ready, 让外部能看到完整设计
- ⚠️ Sprint 2 末 push (按主 session v2 推荐 — 等代码 + UAT 通过) — 避免 ChatGPT 看 spec 没看实际功能
- ❌ 永不 push 新仓库 — origin (canvas-learning-system) 已含 commit 16b648d, 够用

## 4. ChatGPT 5 必修包的 schema/API 速查 (供 dev 直接复制)

### 必修 #1: CanvasGraphEpisodeV1 unified schema

```json
{
  "schema_version": "CanvasGraphEpisodeV1",
  "event_id": "deterministic-id",
  "event_type": "callout_added | wikilink_added | calibration_vote | ...",
  "occurred_at": "ISO 8601",
  "vault_id": "cs_61b",
  "group_id": "vault:cs_61b:recursion",
  "canvas_path": "graphs/recursion.md",
  "node_id": "...",
  "source_node_id": "...",
  "target_node_id": "...",
  "relation_type": "prerequisite",
  "belief_key": "callout:recursion-base-case:anchor-01",
  "callout": {"anchor": "...", "type": "tip", "text": "..."},
  "context": {"source_board": "...", "path_trace": [...], "in_links": [...], "out_links": [...]},
  "narrative": "用户在 X 中沿 A→B→C 路径, 对 [[node]] 写下 tip: ..."
}
```

### 必修 #2: edge_type_map 透传 (episode_worker.py:550-560 修)

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
    edge_type_map=CANVAS_EDGE_TYPE_MAP,  # ⛔ V-08 修复 spec 缺这个!
)
```

### 必修 #3: belief_key 版本链 (add_triplet API)

```python
await graphiti.add_triplet(
    source_node,
    EntityEdge(
        group_id=gid,
        source_node_uuid=src_uuid,
        target_node_uuid=tgt_uuid,
        created_at=occurred_at,
        valid_at=occurred_at,
        invalid_at=None,  # 后续更新时 set
        name="Prerequisite",
        fact="...",
        attributes={
            "belief_key": "edge:src:prerequisite:tgt",
            "status": "active",
            "source": "frontmatter"
        }
    ),
    target_node
)
```

### 必修 #4: query-time flush

```python
await graphiti_write_facade.flush_pending(
    group_id=gid,
    canvas_path=current_canvas_path,
    max_wait_ms=1200,  # 1.2s 超时降级
)
facts = await graphiti_relation_service.search_relation_facts(
    query=f"{node_id} related concepts",
    group_id=gid,
    limit=8,
)
```

### 必修 #5: search_relation_facts facade

```python
class GraphitiRelationService:
    async def search_relation_facts(
        self,
        query: str,
        group_id: str,
        edge_types: list[str] | None = None,
        limit: int = 8,
    ) -> list[RelationFact]: ...
```

## 5. 决策追溯

- 2026-05-26 17:00-19:10: 主 session 审计 + Agent C/D/E + V-07~V-11 修复 + 报告 v1/v2
- 2026-05-26 19:30: Graphiti 设计审计任务书 ship + research-pack 140K xml 打包
- 2026-05-26 19:45: 用户拖 xml 到 ChatGPT Deep Research, 获得 7 Part 完整设计审计报告
- 2026-05-26 20:00: 本决策清单 ship — Claude 对照 ChatGPT 报告 vs V-07~V-11 修复, 发现 5 个 critical bug 未覆盖
- **下一步**: 用户回答 Q1-Q5 → Sprint 2 Day 6 起步

---

**Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**ChatGPT 原报告**: `_bmad-output/审查/2026-05-26-chatgpt-graphiti-deep-research-报告.md`
**主审计 v2**: `_bmad-output/审查/2026-05-26-开发计划报告-Obsidian-Hybrid-方向审计.md`
**前置修复**: `_bmad-output/审查/2026-05-26-chatgpt-v7-v8-v10-v11-修复回应.md`
