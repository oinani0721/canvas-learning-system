---
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
phase: "β-1"
title: "MVP-α-5 / α-6 — Graphiti 接入 + 拆解路程上传"
status: "ready-for-dev-after-mvp-alpha-uat"
date: "2026-05-20"
parent_uat: "_bmad-output/验收单/Story-MVP-α-end-to-end-learning-loop.md (v1.2)"
triggered_by: "用户批注 2 命中: 'agent 能否清晰知道我如何剖析白板? 批注+拆解路程怎么记录在 Graphiti 后端?'"
work_estimate: "10-14h (2 Story 串行)"
priority: "β-1 (sprint-status.yaml 锁定优先级首位)"
---

# β-1 Graphiti 接入 + 拆解路程上传计划

## 1. Context (为什么要做)

MVP-α-1 (2026-05-14 ship) 为了快速跑通端到端闭环, **有意跳过了 Graphiti / KG / ACP 5-layer 复杂度**, 走最简路径: `Obsidian 批注 → frontmatter tips → backend 读 .md → LLM 直接出题`. 验收单 v1.1 表格"5 个反馈瞬间通路"声称走 Graphiti episode, 但 3 Explore agent 全链路 grep 确认 Graphiti 零调用.

用户在 v1.1 验收单批注 2 指出: *"我需要 agent 能清晰知道我是如何使用原白板剖析理解知识点的, 通过我的批注和拆解路程... 然后这个拆分路程又是怎么样的被清晰的记录在我们 Graphiti 的当前后端?"*

β-1 任务: **补完 MVP-α 跳过的 Graphiti 接入**, 让用户的批注+导航路程真实进 Graphiti, 出题时引用历史 episode.

## 2. β-1 范围 (2 Story 串行)

### Story MVP-α-5: 拆解路程上传 + Graphiti episode 写入 (~5-7h)

**目标**: plugin 端记录的 "递归 → factorial" 导航路径上传 backend, 写入 Graphiti episode.

**Tasks**:
- [ ] **α-5.1**: backend 新建 endpoint `POST /api/v1/event/navigation`
  - request: `{vault_id, from_node, to_node, click_type: "wikilink"|"backlink"|"graph", timestamp}`
  - 写入 Neo4j 关系 `(:Concept)-[:NAVIGATED_TO {clicked_at, click_type}]->(:Concept)`
  - 同时调 `graphiti_service.add_episode()` 写"导航 episode" (group_id = `vault:<vault_id>`)
- [ ] **α-5.2**: plugin `status-bar.ts:handleFileOpen` 改造
  - 现有 `buildNavPath()` 仅前端展示, 加 fetch POST 上传 backend
  - throttle 500ms 避免快速切换文件刷爆
  - 上传失败静默 (不打扰用户), console.log 即可
- [ ] **α-5.3**: episode_worker 处理 navigation episode
  - 抽取 (from_node, to_node) 节点对作为关系 fact
  - 不重复写入已有 NAVIGATED_TO 关系 (用 MERGE)
- [ ] **α-5.4**: 加 backend 测试 `tests/test_event_navigation.py` (5 用例)
  - 正常上传 200
  - 缺 from_node 422
  - Graphiti 失败 502 + 日志
  - 同一对节点多次上传只有 1 条 NAVIGATED_TO (MERGE 验证)
  - episode_worker 异步处理验证

**AC**:
- 用户在 vault 点 3 个 wikilink, Neo4j `MATCH (a:Concept)-[r:NAVIGATED_TO]->(b:Concept) RETURN count(r)` ≥ 3
- Graphiti `search_memory_facts(query="navigation", group_id="vault:cs_61b")` 返回 ≥ 3 条 episode
- plugin 端不阻塞 UI (上传失败用户无感)

### Story MVP-α-6: question_generator 接入 Graphiti search (~5-7h)

**目标**: 出题时 backend 调 Graphiti 查"用户在这个节点周围的历史拆解+错误+批注", 拼入 prompt.

**Tasks**:
- [ ] **α-6.1**: `question_generator.generate_question()` 升级
  - 当前签名: `(node_id, user_tips, node_text)` 已经有 tips
  - 新增内部调用: `graphiti_facts = await graphiti_service.search_memory_facts(query=node_id, group_id=..., limit=10)`
  - prompt 增加 `## 你的历史学习路程\n{facts_block}` section
- [ ] **α-6.2**: `learning_context_service._fetch_tips_and_errors` 加第 4 source
  - 当前 3 source (Neo4j Annotation + Error + .md frontmatter)
  - 新增 4th: Graphiti episode (按 group_id + concept_id 查最近 20 条 fact)
  - 跟前 3 source fusion (去重 + 时间排序)
- [ ] **α-6.3**: prompt template 显式引用 navigation
  - 当前模板: `用户在批注中提到「{tips}」, 请...`
  - β-1 模板: `用户在批注中提到「{tips}」, 并且最近从 [{from_node}] 跳到 [{this_node}], 请...`
- [ ] **α-6.4**: 加测试 `tests/test_exam_quick_graphiti.py` (5 用例)
  - mock Graphiti search 返回 N facts → prompt 包含 facts
  - Graphiti 失败 → fallback 到原 frontmatter-only 路径 (不让 β-1 接入打挂 MVP-α 已通过的闭环)
  - prompt 长度限制 (超 4K token 截断)

**AC**:
- 用户跑 v1.2 第 4 步 (Cmd+Shift+Q), 题目除了引用 tip 原话, 还能引用"你最近从 X 跳到 Y"
- backend logs 含 `graphiti_facts_used: N` (N ≥ 0)
- Graphiti 完全挂掉时, 出题仍能跑 (fallback 到 MVP-α 路径)

## 3. 参考实现 (已存在的代码)

| 需求 | 参考文件 |
|---|---|
| Graphiti search_memory_facts 调用 | `backend/app/services/question_generator.py:461-533` `generate_exam_question()` 原版 (Story 6.3) |
| Graphiti add_episode 调用 | `backend/app/services/episode_worker.py:287-394` (硬锁 Gemini, 不改) |
| group_id 规约 | `backend/app/core/subject_config.py::build_vault_group_id()` |
| Cypher 防 group_id 泄漏 | `backend/app/utils/cypher_helpers.py::cypher_with_group_filter()` |
| event 上传 endpoint 风格 | `backend/app/api/v1/endpoints/event.py` (如有 — α-5.1 沿用) |
| episode_worker MERGE 模式 | `backend/app/services/episode_worker.py` |
| plugin event 上传 (已有先例) | `frontend/obsidian-plugin/src/main.ts` 中已有 backend fetch 代码 |

## 4. 依赖关系

- **β-1 前置**: MVP-α v1.2 UAT 通过 (`status: review → done`)
- **β-1 不依赖**: 
  - BKT/FSRS 升级 (β-3)
  - 评分 rubric 升级 (β-2)
  - IRT 难度路由 (β-2)
- **β-1 阻塞**: 
  - β-2 评分 rubric 接入 attempt_history 需要 β-1 完成 episode 写入

## 5. 跟 v1.2 范围说明的对应

参考 `_bmad-output/验收单/Story-MVP-α-end-to-end-learning-loop.md` §⚠️ MVP-α 范围说明 表格:

| v1.2 范围说明项 | β-1 覆盖 | β-1 不覆盖 |
|---|---|---|
| 拆解路程记录 | ✅ MVP-α-5 全覆盖 | — |
| 批注→backend Graphiti 接入 | ✅ MVP-α-5 + α-6 覆盖 | — |
| 出题上下文 ACP 5-layer | 🟡 α-6 加 1 source (Graphiti facts), 不做全 5-layer | 三路融合 RAG 留 β-3 |
| 三路融合 RAG | ❌ β-3 | β-3 |
| 评分 rubric / 历史 / BKT | ❌ β-2 + β-3 | β-2 / β-3 |
| IRT 难度路由 | ❌ β-2 | β-2 |

## 6. 工作量分解

| Task | 估时 | 风险点 |
|---|---|---|
| α-5.1 endpoint | 1.5h | 用既有 event pattern, 风险低 |
| α-5.2 plugin throttle | 1h | throttle 容易写出 bug, 用 lodash 或手写 |
| α-5.3 episode_worker MERGE | 1.5h | Graphiti add_episode 异步队列, 需用现有 worker pattern |
| α-5.4 测试 | 1.5h | mock Graphiti 服务 |
| α-6.1 generate_question 升级 | 2h | 改现成的 5 行 prompt, 风险低 |
| α-6.2 learning_context 4th source | 2h | 跟前 3 source fusion 需用 RRF 或 score 排序 |
| α-6.3 prompt template | 0.5h | 文本改动 |
| α-6.4 测试 | 2h | 含 fallback 路径验证 |
| 总计 | **12h** | 在 10-14h 估计内 |

## 7. 验收方式 (β-1 总验收)

跟 v1.2 UAT 类似的 hands-on 流程, 额外验证:

1. 用户在 vault 跑完 v1.2 6 步 UAT (5 个反馈瞬间)
2. backend logs 含:
   - `[α-5] navigation event received: from=base-case to=recursion`
   - `[α-5] graphiti episode added: vault:cs_61b`
   - `[α-6] graphiti_facts_used: 7` (出题时)
3. 用户在 Cmd+Shift+Q 触发的题目里, 看到 *"你最近从 [[base-case]] 跳到 [[recursion]], 并在 [[recursion]] 批注「{tip}」, 请..."* 这样的引用
4. Neo4j 查询: `MATCH (a)-[r:NAVIGATED_TO]->(b) RETURN a.id, b.id, r.clicked_at ORDER BY r.clicked_at DESC LIMIT 10` 返回真实数据
5. Graphiti search 验证: `search_memory_facts(query="recursion", group_id="vault:cs_61b")` 返回含 navigation 类型 episode

## 8. 决策回看

| 决策 | 选择 | 理由 |
|---|---|---|
| 是否在 MVP-α 阶段就接 Graphiti | ❌ 不在 | 闭环优先于精度 (MVP-α-1 注释), v1.2 用户已确认 Option C 推迟到 β |
| 是否做完整 ACP 5-layer | ❌ 部分 (1 source) | β-1 控制范围, 完整 ACP 拆到 β-3 |
| episode_worker 是否改 Gemini 锁定 | ❌ 不改 | episode_worker.py:287-394 已硬锁 Gemini, 不动 |
| navigation throttle 用什么库 | lodash.throttle | 已经在 plugin deps 里 (验证 package.json) |
| 上传失败处理 | 静默 console.log | 不打扰用户 hands-on UAT |

## 9. 不在范围

明确**β-1 不做**的事 (避免范围蔓延):
- ❌ ACP 完整 5-layer (留 β-3)
- ❌ 三路融合 RAG (Neo4j + LanceDB + Grep) (留 β-3)
- ❌ 评分 rubric 升级 (留 β-2)
- ❌ BKT / FSRS / IRT (留 β-2/β-3)
- ❌ attempt_history 表 (留 β-2)
- ❌ episode_worker 模型换 (永远不做, 已硬锁 Gemini)
- ❌ 多 vault 跨学科推理 (留 v2)

---

**下一步**:
1. v1.2 UAT 通过 → mark MVP-α `done`
2. 立即 create MVP-α-5 / α-6 Story spec (用 bmad-bmm-create-story Skill)
3. 加入 `_bmad-output/implementation-artifacts/sprint-status.yaml` β-1 优先级首位
4. 用户人工批注 Story spec
5. 跑 bmad-bmm-dev-story Skill 实施
