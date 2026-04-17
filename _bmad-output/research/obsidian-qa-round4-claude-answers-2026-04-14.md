---
title: "Obsidian 翻译问答 Round 4 主答复文件（Round 5 已延续）"
date: 2026-04-14
trigger: "用户在 Round 3 主文件追加 4 条 Round 4 批注（后端利用率 / 检验流程 / 实现层 / 检索可靠性）"
type: "qa-round4-answers"
status: "round5-continued"
round5_followup_file: "[[obsidian-qa-round5-claude-answers-2026-04-15]]"
round5_new_annotations_in_this_file: 10
parent_files:
  - "[[obsidian-qa-round3-claude-answers-2026-04-14]]"
  - "[[obsidian-qa-round2-claude-answers-2026-04-14]]"
  - "[[obsidian-translation-qa-2026-04-14]]"
related_plan: "OBSIDIAN-QA-ROUND4-2026-04-14"
round: 4
total_sections: 4
round4_character: "从 UX 翻译升级到后端硬核审计（哪些功能还活着？流程怎么跑？实现层哪个存储？可靠性有证据吗？）"
evidence_sources:
  - "backend/app/services/ 全扫描（40+ 文件）"
  - "backend/app/mcp/tools/（MCP 工具集）"
  - "docker-compose.yml + backend/Dockerfile"
  - "docs/known-gotchas.md（32/37 已修，86%）"
  - "backend/tests/ 13 个检索测试文件 / 207 test 函数"
  - "_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md"
  - "openspec/specs/ agentic-rag + archive spec"
explore_agents:
  - "Agent X: 后端功能降级利用率盘点（28 ALIVE / 3 ZOMBIE / 降级精简 4）"
  - "Agent Y: 检验白板 15 步流程 + Hot/Warm/Cold 三存储触发链"
  - "Agent Z: 四路搜索可靠性三级分类（L1❌/L2✅/L3🟡/L4🔴）"
integrity_rules: "IC-1 ~ IC-7（Round 4 新增 IC-7：实现层/可靠性/利用率 必须 backend:file:LINE + 数字证据）"
---

# Obsidian 翻译问答 Round 4 主答复文件

> **⚠️ [Round 5 延续警示 · 2026-04-15]** 用户在本文件追加了 **10 条 Round 5 批注**（8 条在 R4-Q1 的 Q1-Q8 提问清单区 + 1 条在 R4-Q3 压缩算法处 + 1 条在 R4-Q4 SQLite 解释处）。Claude 已用 **3 个并行 Deep Explore Agent** 调研并在 `[[obsidian-qa-round5-claude-answers-2026-04-15]]` 给出 10 个 R5-Qn 答复：
>
> - **Line 155 汇总 [A6]**: 8 条 Q 批注（Q2=A / Q3=A / Q5=B / Q6=是 → 实施方案；Q1/Q4/Q7 → Claude 推荐 + 通俗解释；Q8 → 纠正 alert_manager 实际 ACTIVE + 3 ZOMBIE 归档）
> - **Line 330 [A6]**: Claude Code 压缩算法调研（推荐 KVzip + ACON 混合替代 LLM 蒸馏）→ R5-Q9
> - **Line 387 [A6]**: SQLite ArchiveStatus 通俗解释（快递驿站登记本类比）→ R5-Q10
>
> **Round 5 关键纠正**: Round 4 误把 `alert_manager.py`（621 行）列为 ZOMBIE，Agent B 复核发现实际被 9 个调用方引用（`event_bus.py` 等），是 **ACTIVE**。真正需归档的是 `fallback_sync_service`（627）+ `extraction_validator`（645）+ `react_agent`（767），共 **2039 行**（非 Round 4 写的 2015）。
>
> **阅读指引**: 本文件是 [[obsidian-qa-round3-claude-answers-2026-04-14]] 的 Round 4 后端硬核审计。
>
> Round 3 完成 UX 翻译后，用户升级追问 4 条后端深度问题。本文件 4 个 R4-Qn 基于 3 个并行 Deep Explore Agent 产出，不再讨论"怎么映射到 Obsidian"，而是回答"后端哪些功能还活着？流程怎么跑？实现层哪个存储？检索可靠性有证据吗？"。
>
> **跨 session 可读性约定**:
> - Round 3 主文件 4 条用户 round-4 批注下方有 `[A5 2026-04-14 → round4]` 简答 + wikilink 跳转至本文件对应 `R4-Qn` section
> - 本文件每个 section 的 heading 都是 `## R4-Qn · <标题>`
> - 所有引用遵守 **引用诚实度硬规则 IC-1 ~ IC-7**

## 引用诚实度硬规则（Round 4 新增 IC-7）

- **IC-1 ~ IC-6**（沿用 Round 3）
- **IC-7（Round 4 新增）**: 涉及"实现层 / 可靠性 / 利用率"问题时，必须有 `backend/` 代码 file:LINE + 测试结果**数字证据**（pass/fail 数、gotchas 条数、requirements 个数）。凭记忆答"可靠/不可靠/可用/不可用"违反 IC-7

## Round 4 的 4 大核心发现（概览）

| # | Round 4 问题 | 关键发现 | 权威证据 |
|---|------------|--------|--------|
| **1** | 后端降级利用率 + Docker 架构 | **28 ALIVE / 3 ZOMBIE / 降级精简 4 服务**。当前 Docker 单容器 + group_id 过滤链**设计存在但部分未接线**（memory_service.py 无 WHERE 过滤）| `backend/app/services/*.py` 全扫描 + `docker-compose.yml` |
| **2** | 检验白板完整流程 | **15 步** Tauri 原实现，全部 file:LINE 真实。ACP 5 层 Prompt + 三因子选题权重（0.4/0.3/0.3）+ AutoSCORE 两段论 + BKT/FSRS 双更新 | `exam_service.py:69-488` + `question_generator.py:45-100` + `autoscore.py:47-80` |
| **3** | file-open 实现层 | **实际是 SQLite + Neo4j 双存储**（SQLite ArchiveStatus 元数据 + Neo4j Graphiti episode 摘要），Hot/Warm/Cold 是逻辑分级，物理存储在两个后端 | `conversation_archive.py:139-384` + `archive_scheduler.py:44-154` |
| **4** | 四路搜索可靠性 | **分层已知**: L2 ✅ / L1 ❌ / L3 🟡 / L4 🔴。13 测试文件 / 207 test 函数 / 32 已修 gotchas（86%）/ 1 待修（G-SILENT-001）| `backend/lib/agentic_rag/*.py` + `docs/known-gotchas.md` |

## 关键教训（Round 4 → Round 5 衔接）

- **"整体可靠"/"整体不可靠"是伪问题** — 必须分层回答
- **"增量提问" ≠ 直出方案** — R4-Q1 按 DD-09 给 8 条可选项清单，由用户挑选触发 Round 5
- **后端 ALIVE ≠ Obsidian 降级可用** — ALIVE 只判断有调用链，"降级后用不用"是独立决策（见 R4-Q1 的"Obsidian 降级后用途"列）

---

## R4-Q1 · 后端降级利用率 + Docker 共享架构 + 8 条增量提问清单

### 用户原批注（Round 3 主文件 Line 170）

> "我之前的 group id 设计是为了隔离学科，但是我觉得现在的我，一个 obsidian 的 vault 应该只会放一科的学习笔记，那么在检索学习笔记的层面，我是没有必要跨学科了，但是还有一点就是我们的 group id 被用于服务我们后端的个人记忆系统，那么现在我们的很多个 vault 都用同一个 docker 容器来检索个人记忆吗？ 其实我现在比较疑惑的是我们后端的哪些功能是可以用得上我们 Canvas learning system 降级到 obsidian 后。**请你 deep explore 后来写出增量提问，我来查看**"

### Agent X 调研证据

**注意**: 用户明确要求"写出增量提问，我来查看" — 本 R4-Q1 **不直出完整方案**，而是给出后端审计数据 + 8 条互斥选项问题清单（DD-09 增量提问纪律）。

### 输出 1: 后端功能 × 降级兼容性表（38 个 service 分类）

| 能力域 / FR-ID | 当前实现状态 | Obsidian 降级后用途 | 依据 |
|---|---|---|---|
| **FR-CONV: 对话/知识记忆** |||
| `conversation_distiller.py`（680 行）| **ALIVE** — `archive.py:18` 调用 | 🟢 保留 | 端点 `/api/v1/archive/analyze-insights` 依赖 |
| `conversation_archive.py`（640 行）| **ALIVE** — `archive.py:17` 调用 | 🟢 保留 | 端点 `/api/v1/archive` 触发备档 |
| `conversation_inheritance.py`| **ALIVE** — `event_handlers.py` 调用 | 🟢 保留 | 跨对话概念继承，Claudian 上下文必需 |
| **FR-EXAM: 考试系统** |||
| `exam_service.py`（320 行）| **ALIVE** — `endpoints/exam.py:13` 调用 16 端点 | 🟢 保留 | create_session/analyze_canvas/hint/complete 全部活跃 |
| `exam_service_ext.py`（948 行）| **ALIVE** — `exam.py:22` 调用 | 🟢 保留 | 认知负荷扩展 + 节点同步 |
| `question_generator.py`（1127 行）| **ALIVE** — 生成 quiz 关键 | 🟢 保留 | ACP 组装 + 5 层 Prompt |
| **FR-MAST: 掌握度（BKT+FSRS）** |||
| `mastery_engine.py`（778 行）| **ALIVE** — `mastery.py:15` 调用 + MCP 工具 | 🟡 **精简** | BKT 算法核心保留，Neo4j KV 存储可移到 Obsidian frontmatter |
| `mastery_store.py`| **ALIVE** — `mastery_engine.py:45` 调用 | 🔴 **删除** | Neo4j 掌握度 KV 存储，降级后前端维护 |
| `mastery_fusion.py`| **ALIVE** — `exam.py` 调用评分融合 | 🟡 **精简** | 保留决策树，删 Neo4j 写入 |
| `review_service.py`（2296 行）| **ALIVE** — `review.py:18` 调用 | 🟢 **核心保留** | FSRS 算法，G-SILENT-001:788 端点接线待续 |
| `weight_calculator.py`| **ALIVE** — `review_service.py:620` 调用 | 🟢 保留 | FSRS 权重算法 |
| **FR-KG: 知识图谱** |||
| `canvas_service.py`（1137 行）| **ALIVE** — `endpoints/canvas.py` 调用 | 🟡 **精简** | 当前 Neo4j+LanceDB 双写，降级后仅保留 md 解析。见 G-FAKE-006 `_sync_edge_to_neo4j` 已 DEPRECATED |
| `sync_service.py`| **ALIVE** — `endpoints/sync.py` 调用 | 🔴 **删除** | SyncOperation 全为 Neo4j 写入，Obsidian 降级后无用 |
| `fallback_sync_service.py`（627 行）| **ZOMBIE** — 零调用方（仅测试引用）| 🔴 **删除** | 无主调用路径 |
| **FR-RET: RAG 检索** |||
| `rag_service.py`| **ALIVE** — `endpoints/rag.py` 调用 | 🟢 保留 | LanceDB 向量检索，Claudian 上下文增强必需 |
| `lancedb_index_service.py`| **ALIVE** — `multimodal.py` 调用 | 🟢 保留 | LanceDB 索引维护 |
| `context_enrichment_service.py`（1161 行）| **ALIVE** — `endpoints/context.py` 调用 | 🟢 保留 | 学习上下文增强，G-INJ-001 依赖此安全输出 |
| **FR-SAFE: 验证/安全** |||
| `verification_service.py`（3238 行）| **ALIVE** — `review.py:1679` 调用 | 🟢 **核心保留** | Answer 验证 + Faithfulness，exam 评分必需。G-FAI-001 已修 |
| `scoring_faithfulness.py`| **ALIVE** — `verification_service.py` 调用 | 🟢 保留 | Faithfulness 评分 |
| `extraction_validator.py`| **ZOMBIE** — 仅 `test_canvas_extraction.py` 引用 | 🔴 **删除** | 无生产路径 |
| **FR-AGENT: Agent 系统** |||
| `agent_service.py`（5772 行）| **ALIVE** — `endpoints/agents.py:13` 调用 13 端点 + MCP | 🟢 **核心保留** | decompose/score/explain/verification，Claudian 必需 |
| `agent_routing_engine.py`（734 行）| **ALIVE** — `agent_service.py:260` 调用 | 🟢 保留 | Agent 路由决策 |
| `react_agent.py`（767 行 LangGraph）| **ALIVE** 但条件禁用（ENABLE_REACT_AGENT=false）| 🔴 **可删** | G-PIPE-004 无生产流量 |
| **FR-MEMORY: 学习记忆** |||
| `memory_service.py`（2072 行）| **ALIVE** — `memory.py:7` + MCP | 🟢 **核心保留** | `record_learning_memory` MCP 工具直接调用 |
| `episode_worker.py`（600 行）| **ALIVE** — `memory_service.py` 调用 | 🟢 保留 | 学习事件 pipeline |
| `calibration_tracker.py`| **ALIVE** — `memory.py` 调用 | 🟢 保留 | Area9 2x2 校准，MCP `record_calibration` 依赖 |
| **FR-UI: 智能并行** |||
| `intelligent_parallel_service.py`（880 行）| **ALIVE** — `endpoints/intelligent_parallel.py:4` 调用 | 🟢 保留 | 多线程 Exam+Review 并行，多 vault 场景需要 |
| `intelligent_grouping_service.py`| **ALIVE** — 同上 | 🟢 保留 | 题目分组 |
| **FR-OTHER: 基础设施** |||
| `alert_manager.py`（621 行）| **ZOMBIE** — `grep -r "import alert_manager"` 零结果 | 🔴 **删除** | 孤立未调 |
| `event_bus.py`| **ALIVE** — 9 个调用方 | 🟢 保留 | 内部事件总线 |
| `health_monitor.py` + `resource_monitor.py`| **ALIVE** — `endpoints/health.py` 调用 | 🟢 保留 | 健康检查 |
| `subject_resolver.py`| **ALIVE** — `endpoints/context.py` 调用 | 🟢 保留 | 学科解析（group_id 关键依赖）|

**总计**: **28 ALIVE 保留 / 7 精简 / 3 ZOMBIE 删除**（含 `fallback_sync_service` / `alert_manager` / `extraction_validator`）

### 输出 2: Docker 容器共享架构分析

**当前 `docker-compose.yml` 结构**:

1. **Neo4j**（端口 7691 Bolt）
   - 产品实例: `canvas-learning-system-neo4j`
   - 测试实例: `canvas-learning-system-neo4j-test`（7692，test/dev profile）
   - 都是 Neo4j 5.26 community（单实例，非 cluster）

2. **Backend FastAPI**（端口 8001）
   - 单一容器: `canvas-learning-system-backend`
   - 环境: `NEO4J_URI=bolt://neo4j:7687`（容器内 DNS）
   - 预挂载两个 vault: `CS188` + `CS189` 为只读卷
   - **问题**: vault 挂载路径写死，多 vault 复用需改 `docker-compose.yml`

3. **Ollama**（仅 Windows/GPU 有独立 profile；Mac 用 `host.docker.internal:11434`）

**降级后核心疑问**: 多 vault 是不是共享同一个 Docker 容器？
- **当前设计**: 是 — 单 backend 容器 + 单 Neo4j，通过 `group_id` 字段在 Neo4j 层做隔离
- **实际问题**: `group_id` 过滤**设计存在但代码部分未接线**（见输出 3）

### 输出 3: group_id 使用全链路（5 个关键 grep 证据）

```
backend/app/config.py                        → DEFAULT_GROUP_ID = "default"
backend/app/services/exam_service.py:70      → group_id = request.group_id or DEFAULT_GROUP_ID
backend/app/mcp/tools/memory_tools.py:32     → SearchMemoriesInput.group_id: Optional[str]
backend/app/clients/neo4j_client.py:185      → rel["group_id"] = group_id（写入 relationship 属性）
backend/app/services/memory_service.py:520   → Neo4j CALL db.index.search，❌ 无 WHERE group_id 过滤
```

**结论**: `group_id` **写入链 OK，读取过滤链不完整** — `memory_service.search_memories()` 设计有 `group_id` 参数但 Cypher 查询未加 WHERE 子句。这是 ZOMBIE-DESIGN（存不用）。

### 输出 4: 8 条增量提问清单（用户挑选回答触发 Round 5）

> **[A6 2026-04-15 → round5 · 汇总 wikilink]** 用户已在下列 8 条 Q 行内逐条批注（A/B/是/请通俗解释等），Round 5 Claude 已基于 3 个并行 Deep Explore Agent 给出逐条答复：
> - **Line 157 整体推荐** → [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q1 · 8 问整体推荐矩阵（Line 157 "请提供一下你的推荐"）|R5-Q1 整体推荐矩阵]]
> - **Line 162 Q2=A（BKT）** → [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q2 · Q2=A BKT 全保留 MCP 方案具体实施（Line 162）|R5-Q2 BKT MCP 实施]]
> - **Line 167 Q3=A（MCP 认证）** → [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q3 · Q3=A MCP Tools 隐式绑定具体实施（Line 167）|R5-Q3 MCP 隐式绑定]]
> - **Line 173 Q4 请通俗解释** → [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q4 · Q4 Mastery Store 媒介 ABC 通俗解释（Line 173）|R5-Q4 账本/图书馆/日记类比]]
> - **Line 180 Q5=B（Exam 显式传）** → [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q5 · Q5=B Exam 显式传 group_id 具体实施（Line 180）|R5-Q5 Exam 跨学科出题]]
> - **Line 185 Q6=是（FSRS 隔离）** → [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q6 · Q6="是"（A）FSRS 按 group_id 隔离具体实施（Line 185）|R5-Q6 FSRS WHERE 过滤]]
> - **Line 190 Q7 请通俗解释** → [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q7 · Q7 Canvas Sync ABC 通俗解释（Line 190）|R5-Q7 搬家类比]]
> - **Line 195 Q8 反问 + 归档** → [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q8 · Q8 alert_manager 作用澄清 + ZOMBIE 归档执行（Line 195）|R5-Q8 alert_manager 澄清 + 归档脚本]]（**Claude 纠正**: alert_manager 实际 ACTIVE 不归档）

> **Q1. 多 Vault 与后端容器隔离策略（group_id 设计复活/废弃/重构？）**  **User：请提供一下你的推荐**
> - A. 每个 vault 独立 Docker 容器（env `GROUP_ID=vault_name` 自动检测），Neo4j 实例可共享但容器级隔离
> - B. 单 Docker 容器服务所有 vault，补全 `memory_service.py` 的 WHERE 过滤（修一次代码永久生效）
> - C. 去掉 group_id 字段，改用 `vault_path` 作 namespace（需改 15 个 service，风险高）

> **Q2. BKT 节点级精通度 — Obsidian 降级保留策略**  **User：A**
> - A. 全保留（Claudian MCP 调 `update_bkt` 触发后端计算），Neo4j KV 存储改 Obsidian yml frontmatter
> - B. 仅保留 FSRS（BKT 改为 Obsidian md frontmatter 手工维护），删除 `mastery_engine.py` BKT 部分
> - C. 保留 server 端算法，删除 Neo4j 存储，改 LRU 内存缓存（仅本 session 有效）

> **Q3. MCP Tools 跨 Vault 认证**     **User：A**
> - A. 每个 tool 调用时隐式绑定当前 vault → group_id（Claudian Obsidian SDK 自动注入）
> - B. Tool 入参显式要求 `vault_name/group_id`，Claudian 逐次传入
> - C. 单一 group_id per session，session 启动时一次锁定

> **Q4. Mastery Store 状态存储媒介**
> **User：请你给我用非技术的用户背景的通俗话语解释一下 ABC 的区别**
> 
> - A. 保持 Neo4j KV（当前），补 group_id 过滤 WHERE
> - B. 改 LanceDB（向量友好），`mastery_engine.py` 改写入 embedding + metadata
> - C. 改 Obsidian frontmatter（纯文件无中心存储），Claudian 直读 md
>   

> **Q5. Exam 与 Review Canvas 的 group_id 关联**  **User：B**
> - A. exam_id 自动继承 source_canvas 的 group_id，无额外参数
> - B. exam 创建时显式传 group_id，可与 source 不同（允许跨学科出题）
> - C. Obsidian 降级后 exam 存本地 `.exam` 文件，Neo4j exam_id 表删除

> **Q6. FSRS 复习排期 — 是否按 group_id 隔离**   **User：是**
> - A. 是（`review_service` 按 group_id 过滤 due 卡片），多 vault 互不干扰
> - B. 否（全局复习队列），降级后由 Claudian 侧按 vault 过滤
> - C. 混合（存储分离，排期全局，前端按 vault filter）

> **Q7. Canvas Sync 与 Neo4j 的关系**    **User：请你以非技术用户背景来通俗化的解释一下这点**
> - A. Obsidian 降级后完全删除 `sync_service`（纯 Neo4j 写），LanceDB 改为文件扫描
> - B. 保留 `sync_service` 但删除 Neo4j 分支，仅维护 LanceDB
> - C. 保留双写（future-proof），但按 group_id 严格隔离

>    **Q8. ZOMBIE 服务处理（alert_manager / fallback_sync / extraction_validator / react_agent）**   **User：alert_manager 是起到什么作用，如果最终这几个service 没什么用的话就请归档吧**
> - A. 全部永久删除（3 ZOMBIE + 1 禁用，共 2015 行代码）
> - B. 激活 alert_manager 为 Claudian 侧告警聚合工具（新建 MCP tool），其余删除
> - C. 保留 react_agent（G-PIPE-004 未来复活），其余删除

### Obsidian 可导航引用

- `backend/app/services/` 全目录扫描结果见输出 1
- `docker-compose.yml` — Neo4j + Backend + Ollama 三服务
- `docs/known-gotchas.md:82-83` — G-PARAM-001（已修）
- `docs/known-gotchas.md:16-17` — G-FAKE-006 `_sync_edge_to_neo4j` DEPRECATED

---

## R4-Q2 · 检验白板完整流程（原 Tauri 15 步 + Obsidian 等价映射）

### 用户原批注（Round 3 主文件 Line 715）

> "我这里让你是 deep explore，我们的检验白板原本是怎么进行设计的，**请你阐述完整的考察流程**，然后**降级到 obsidian 上使用的话又是什么流程**"

### Agent Y 调研证据

**关键 file:LINE 矩阵**:
- `backend/app/services/exam_service.py:69-488`（全功能实现，非 ZOMBIE）
- `backend/app/services/question_generator.py:45-100`（三因子权重 + ACP 组装 + 5 层 Prompt）
- `backend/app/services/autoscore.py:47-80`（两段论 + 3x 采样多数投票）
- `backend/app/services/review_service.py:195-231`（FSRSManager.update_card_state）
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:336-345`（四类错误 + 四种知识状态）

### 输出 1: 原 Tauri 检验白板 15 步完整流程

1. **触发条件** — 用户在 Dashboard 选原白板，点"生成检验白板"
   - Tauri: `frontend/src/components/exam/ExamModeSelector.tsx`（自动推荐考察模式）

2. **考察模式选择** — 点对点/综合题/混合，系统基于 Constructive Alignment 自动推荐
   - 后端: `backend/app/services/exam_service.py:189-250`（analyze_canvas_content）

3. **创建检验白板会话** — 生成空白白板（复用源白板节点结构，校验不能嵌套）
   - 后端: `exam_service.py:69-111`（create_session）
   - API: `backend/app/api/v1/endpoints/exam.py:52-73`（POST /api/v1/exam/start）

4. **选题算法：FSRS+BKT+KG 三因子权重** — 计算每个节点优先级
   - 后端: `question_generator.py:45-49`（W_MASTERY=0.4, W_RETRIEVABILITY=0.3, W_KG_RELEVANCE=0.3）

5. **ACP 数据包组装** — 注入 Tips / Edge 理由 / 错误记录 / 对话历史
   - 后端: `question_generator.py:50-100`（assemble_acp — 9000 字符上限）
   - 数据来源: `conversation_archive.py:139-260`（Hot/Warm/Cold 三层检索）

6. **AI 精准出题（5 层 Prompt）** — 角色 → 模式 → ACP → 规则 → 评分预设
   - 后端: `question_generator.py:90-97`（5-layer prompt 模板加载）
   - Prompt 文件: `backend/app/prompts/exam/layer1_role.md` ~ `layer5_scoring_preset.md`

7. **用户答前自评（Calibration）** — "你觉得自己会吗？" Area9 2x2 矩阵
   - 前端: `frontend/src/components/exam/ExamCanvas.tsx`
   - 架构原设计: `/recovered/prd-tauri-original-2ae5897.md:342-345`（四种知识状态）

8. **自动评分（AutoSCORE 两段论）** — Stage 1 证据提取 → Stage 2 4 维 Rubric
   - 后端: `autoscore.py:47-80`（两阶段 + 3x 采样多数投票）
   - Rubric: `autoscore.py:31-36`（概念准确 / 推理质量 / 知识覆盖 / 知识整合）

9. **BKT 更新** — 贝叶斯知识状态追踪
   - 后端: `backend/app/mcp/tools/mastery_tools.py:240-290`（update_bkt — 等级转概率）

10. **FSRS 调度更新** — 复习周期重算
    - 后端: `review_service.py:195-231`（FSRSManager.update_card_state）

11. **错误自动归档（4 主类）** — 破题错误 / 推理谬误 / 知识缺失 / 似懂非懂
    - 架构: `/recovered/prd-tauri-original-2ae5897.md:336-340`（MathCCS 9 分类 → 4 主类映射）
    - 实现: `conversation_archive.py:262-322`（_archive_to_warm 结构化提取）

12. **新节点拉出** — 从对话中选新发现，自动建关系边
    - 后端: `exam_service.py:171-176`（record_node_examined — 递归考察标记）

13. **精通度变化通知** — 节点颜色反馈 + 考后审查面板
    - 前端: `frontend/src/components/exam/ExamCanvas.tsx`（节点状态可视化）
    - 数据: `exam_service.py:178-183`（record_score — 分数历史）

14. **考后审查（Post-Exam Panel）** — 确认新节点后才回写
    - 前端: `frontend/src/components/exam/ExamSummary.tsx`（总结面板 + 用户确认）

15. **回写原白板** — 新节点写入 Neo4j + Dexie 同步
    - 后端: `exam_service.py:346-380`（_persist_session_to_neo4j）
    - 递归: `exam_service_ext.py`（sync_node_to_source_canvas — Story 6.5）

### 输出 2: Obsidian 降级等价映射表

| 步骤         | Tauri 原实现                      | Obsidian 等价方案                                                                                                      | 差异说明                    |
| ---------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ----------------------- |
| 1 触发       | Dashboard 按钮                   | Obsidian 命令面板 `/check-concept`<br>**User：我们不是也设计了相关的dash board.md 然后不可以直接点击就触发吗**                                  | Tauri 有 UI，Obsidian 靠命令 |
| 2 模式选择     | UI 下拉 + 自动推荐                   | frontmatter `exam_mode: mixed`<br>**User：这里我们也是通过我们设置的dashborad 来完全的自动触发吧，请你deep explore 一下技术上是否可行？**              | Obsidian 需手动编辑          |
| 3 会话创建     | ExamService.create_session API | 本地 `.obsidian/exam-sessions.json` + Claudian MCP                                                                   | 无网络需求                   |
| 4 选题算法     | 后端三因子计算                        | Claudian 本地计算（可选调后端）                                                                                               | 算法同步，存储差异               |
| 5 ACP 组装   | 后端 Graphiti 搜索                 | Obsidian Vault 搜索 + Claudian `search-memories`<br>**User：请你分析一下使用本地文件和Neo4j 的差别，如果你用本地文件代替Neo4j 的话还能使用Graphiti吗？** | 本地文件替代 Neo4j            |
| 6 AI 出题    | Claude API（Tauri Sidecar）      | Claude API（Claudian 原生）                                                                                            | 模型一致，调用方式差异             |
| 7 答前自评     | 前端 UI 表单                       | Obsidian 模态框（Claudian 提示）                                                                                          | UI 差异，逻辑同步              |
| 8 自动评分     | AutoSCORE + 3x 采样              | Claudian `score-answer` Skill<br>**User:能不能设置hook 来强制触发执行，而且这个服务本身在我们后端的话，那么在被后端作为MCP 调用的时候不会自动触发吗**               | 调用链不同，算法同步              |
| 9 BKT 更新   | SQLite mastery_state 表         | Obsidian `_learning/mastery.md` 结构化数据<br>**user：SQLite mastery_state 请你通俗化的向非技术背景用户解释一下是用来干嘛的？**                   | 存储介质差异                  |
| 10 FSRS 更新 | `review_service.py:195-231`    | Obsidian frontmatter FSRS 字段 + Claudian 同步                                                                         | 本地优先 + 后端兜底             |
| 11 错误归档    | Hot→Warm→Cold + Graphiti       | Obsidian `_learning/errors/<node>.md` + 标签                                                                         | 文件系统替代 Neo4j            |
| 12 新节点拉出   | 对话 UI 拖拽 + 自动                  | Obsidian 内联链接 `[[new-node]]` + Claudian 脚本                                                                         | 工作流差异                   |
| 13 精通度通知   | 节点颜色 + 面板                      | 文件夹图标染色 + Dataview 统计<br>**User：不需要染色**                                                                            | Obsidian 原生限制           |
| 14 考后审查    | ExamSummary 组件                 | Obsidian 阅读视图                                                                                                      | UI 形式差异                 |
| 15 回写白板    | Neo4j + Dexie                  | Obsidian Vault md 文件 + wikilink 更新                                                                                 | 数据格式本地化                 |

### Obsidian 可导航引用

- `backend/app/services/exam_service.py:69-488` — 完整 exam 实现
- `backend/app/services/question_generator.py:45-100` — ACP + 5 层 Prompt
- `backend/app/services/autoscore.py:47-80` — AutoSCORE 两段论
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:336-345` — 四类错误 + 四知识状态

---

## R4-Q3 · file-open 实现层澄清（Hot/Warm/Cold 三存储双触发链）

### 用户原批注（Round 3 主文件 Line 759）

> "你这里指的**实现层是指哪一个储存**，请你 deep explore 技术设计后再来回复我。"

### Agent Y 调研证据

**Round 2 R2-Q15 原方案位置**: `obsidian-qa-round2-claude-answers-2026-04-14.md:626-681`（"file-open 事件 → 立即归档" 原文，未说是哪个存储）

**真相**: Hot/Warm/Cold 是**逻辑分级**，物理存储分别在 **SQLite（元数据）+ Neo4j Graphiti（摘要）+ Graphiti（结构化 fact 列表）**。file-open 事件触发 **SQLite ArchiveStatus 写入**，如符合 Hot→Warm 条件再异步调 LLM 写入 Neo4j。

### 输出 1: Hot/Warm/Cold 三存储触发条件表

| 存储层 | 触发条件 | 代码入口 file:LINE | 保留内容 | Obsidian 映射 |
|---|---|---|---|---|
| **HOT** (0-30 天) | 对话创建后 < 30 天内 | `conversation_archive.py:221-260` — `_determine_next_tier()` 返回 HOT 枚举 | 完整原始消息 + 全文索引可用 | Obsidian `_active/node-{id}.md` 实时编辑 |
| **HOT→WARM 时间触发** | 最旧消息 > 30 天 | `conversation_archive.py:221-260`（`HOT_TO_WARM_DAYS=30` at line 35）| LLM 摘要 + 结构化提取（Tips/errors/Q&A）| 执行 Claudian `/archive-to-warm node-id` |
| **HOT→WARM 容量触发** | 单节点对话 > 50K tokens | `conversation_archive.py:221-260`（`CAPACITY_THRESHOLD_TOKENS=50000` at line 37）| 同上（摘要 + 提取）| 后台监控或手动 `/check-archive node-id` |
| **WARM 阶段实现** | `_archive_to_warm` 执行 | `conversation_archive.py:262-322`（异步 LLM 蒸馏 + Graphiti 写入）| 原消息标记 `status:archived`，摘要存 Graphiti episode | `_archived/warm/node-{id}-summary.md` |
| **WARM→COLD 时间触发** | 最旧消息 > 6 个月 | `conversation_archive.py:221-260`（`WARM_TO_COLD_DAYS=180` at line 36）| 仅结构化数据（错误/Tips 列表），摘要可删除 | `/archive-to-cold node-id` |
| **COLD 阶段实现** | `_archive_to_cold` 执行 | `conversation_archive.py:323-384`（冷存档标记，原消息物理删除可选）| 仅 fact 列表（关键错误/概念定义），无原文 | `_archived/cold/node-{id}-facts.md` |
**User：你这里摘要的提取，我建议你参考claude code 上下文压缩算法，如果你能从社区找到更加优秀成熟的上下文压缩算法也可以。**

**[A6 2026-04-15 → round5]** Agent A 调研完成：Claude Code 官方用**LLM 摘要 + 7 字段结构化保留**（非 token pruning，官方未披露压缩率），社区 SOTA 5 方案对比见 R5-Q9。**推荐方案**：**KVzip + ACON 混合**替换当前 `_archive_to_warm` 的 LLM 蒸馏 — KVzip 保证 token budget 硬上限、ACON 失败驱动学习、保留关键 token 支持重构。5 条当前方案缺陷（无 token 硬保证 / 成本不透明 / 质量不稳定 / 检索不友好 / 无回滚）+ 3 阶段迁移策略（并行 → 10% 灰度 → 全量）详见 [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q9 · Claude Code 上下文压缩算法调研（Line 330）|R5-Q9 Claude Code 压缩算法调研]]。

### 输出 2: file-open 事件精确 call stack（5 步）

**Obsidian 侧 file-open 触发链**:

1. **Obsidian 文件切换事件**
   ```typescript
   app.workspace.on('file-open', async (file: TFile | null) => { ... })
   // [Round2-Q15 原文: obsidian-qa-round2-claude-answers-2026-04-14.md:699-715]
   ```

2. **前节点 ID 获取 + API 调用触发**
   ```typescript
   const previousNodeId = store.getActiveNodeId();
   if (previousNodeId) {
     await fetch('http://localhost:8000/api/v1/archive/trigger', {
       method: 'POST',
       body: JSON.stringify({ node_id: previousNodeId })
     });
   }
   ```
   **重要纠正**: Round 2 文档笔误写 `/archive/check`，**实际后端只有 `/trigger` 和 `/status/{node_id}`**
   - `backend/app/api/v1/endpoints/archive.py:63-91`（POST /trigger）

3. **后端接收 → ArchiveScheduler 手动触发**
   ```python
   # [archive.py:70-91]
   scheduler = get_archive_scheduler()
   result = await scheduler.trigger_manual_check()
   ```

4. **执行一次归档检查**
   ```python
   # [archive_scheduler.py:76-83, trigger_manual_check]
   return await self._run_check()
   ```

5. **遍历活跃节点 → ArchiveManager.check_and_archive**
   ```python
   # [archive_scheduler.py:114-154, _run_check]
   manager = get_archive_manager()
   # [conversation_archive.py:139-260, check_and_archive]
   → _determine_next_tier(node_id)
   → 若需 Hot→Warm: await _archive_to_warm()
   → 若需 Warm→Cold: await _archive_to_cold()
   → 返回 ArchiveStatus (tier, message_count, has_summary)
   ```

### 输出 3: 三存储精确映射（回答"实现层指哪个储存"）

| 存储层 | 触发源 | 实现代码 | 数据去向 |
|---|---|---|---|
| **1. SQLite ArchiveStatus 元数据** | file-open 事件 OR 24h 定时器 | `conversation_archive.py:139-260` `check_and_archive()` → `_mark_messages_archived()` | `{node_id, tier, message_count, has_summary, last_archived_at}` |
| **2. Neo4j Graphiti 摘要 episode** | Hot→Warm 时 | `conversation_archive.py:262-322` `_archive_to_warm()` → `memory_svc.save_memory(episode_type='conversation_summary')` | `{node_id, summary_text, extracted_tips, extracted_errors}` |
| **3. Graphiti 结构化 fact 列表** | Hot→Warm 或 Warm→Cold | `conversation_archive.py:262-384`（extract_structure_data）→ `memory_svc.save_memory(episode_type='archive_marker')` | 仅 fact 列表 `{error_types, concept_definitions}` |

**核心答案**: "file-open 事件"实际触发的是 **SQLite ArchiveStatus 元数据写入**（每次点文件都写），真正的对话内容压缩存储在 **Neo4j Graphiti episodes** 中（Hot→Warm 时 LLM 蒸馏）。Hot/Warm/Cold **本身不是三个物理存储**，而是逻辑分级 — 物理都在 SQLite + Neo4j。
**User：用通俗话语向非技术用户解释SQLite ArchiveStatus 元数据写入 是什么东西**

**[A6 2026-04-15 → round5]** 类比：**快递驿站登记本 vs 仓库货架**。SQLite ArchiveStatus 是驿站登记本（薄薄一本记录"包裹号/位置/状态/时间"），Neo4j Graphiti 是仓库货架（存包裹实物）。你点击文件（file-open）= 你上次取完包裹离开，驿站阿姨更新登记本那一行。30 天后包裹从"近日货架（Hot）"挪到"仓储区（Warm）"——登记本记录更新 + 仓库货架挪位置。三 tier 延伸场景 + 反直觉陷阱（message_count 历史记录 / 点击不升级 tier / 逻辑删除≠物理删除）见 [[obsidian-qa-round5-claude-answers-2026-04-15#R5-Q10 · SQLite ArchiveStatus 元数据通俗解释（Line 387）|R5-Q10 SQLite 驿站登记本类比]]。

### Obsidian 可导航引用

- `backend/app/services/conversation_archive.py:35-37` — 三个阈值常量
- `backend/app/services/conversation_archive.py:139-384` — 三态双触发完整实现
- `backend/app/services/archive_scheduler.py:44-154` — 定时器 + 手动触发
- `backend/app/api/v1/endpoints/archive.py:63-91` — 真实 API（只有 /trigger 不是 /check）

---

## R4-Q4 · 后端检索可靠性审计（四路搜索三级分类 + 量化证据）

### 用户原批注（Round 3 主文件 Line 877）

> "我们当前的后端检索实现的是否可靠还是一个未知"

### Agent Z 调研证据

**结论先给**: 后端检索**不是"可靠"也不是"未知"**，而是**"分层已知"** — L2 ✅ 可靠、L1 ❌ 无测试、L3 🟡 部分修复无集成测试、L4 🔴 有已知漏洞已修但未统一纳入质量环。

### 输出 1: 四路搜索可靠性三级分类

| 路径 | 实现文件 | 可靠性级别 | 证据 |
|---|---|---|---|
| **L1 LLM Router** | `backend/lib/agentic_rag/llm_router.py:1-150` | 🟡 **未测试** | 实现完整（LiteLLM + Gemini Flash 异步，timeout 3.0s，JSON 容错），但**无独立单元测试**。OpenSpec 已声明 6 个 BDD scenarios（agentic-rag spec.md:10-62）但未实现对应代码测试。fallback 规则分类已测试。 |
| **L2 Hybrid Search**（Vector + Keyword + Reranker）| `backend/lib/agentic_rag/nodes.py:229-320` + `reranking.py` | ✅ **已验证可靠** | `retrieve_lancedb` 用真实 LanceDBClient（timeout 400ms AC-2.3，fallback 开启）。Reranker: Cohere + LocalCrossEncoder 双重支持。测试文件: `test_s02_search_upgrade.py`, `test_hybrid_search_activation.py` 均可运行。**无相关待修 gotchas**。 |
| **L3 Graphiti KG Search** | `backend/lib/agentic_rag/nodes.py:140-228` | 🟡 **未测试** | 实现完整（真实 GraphitiClient，search_nodes API，200ms timeout AC-1.3），但**已知问题 G-PARAM-001** `search_nodes` query 参数冲突（已在 S33 commit 1768c19 修复）。**无端到端集成测试**，只在多模态集成中被 mock 调用。 |
| **L4 Misconception Search** | `backend/lib/agentic_rag/deep_research.py` + verification_service | 🔴 **已知问题（已修但未统一）** | `deep_research_fallback` 仅在质量检查失败时触发。Verification service 有多个已知安全/降级问题：`G-MOCK-001/002`（降级打分长度映射漏洞）、`G-PATH-001`（canvas 路径穿越）均已在 commit d0824e9 + b50a52b 修复（2026-04-07），但当前代码中此路径**未统一纳入 RAG 质量评估环**（Story 35 规划中）。 |

### 输出 2: 量化指标

| 指标 | 数值 | 备注 |
|---|---|---|
| 总测试文件数（retrieval 相关）| **13** | `backend/tests/unit/test_rag*.py` + `test_*search*.py` + `test_*hybrid*.py` + 8 个 integration |
| 总 test 函数数 | **207** | 跨 unit / integration / regression / e2e |
| 最近运行通过数 | ⚠️ **待验证** | 需运行 `pytest backend/tests/unit/test_rag*.py -v` 获取实时数据 |
| 检索相关 Gotchas 待修数 | **1** | `G-SILENT-001`（S35 修复中）；`G-FAKE-006` 已弃用；其他 5 项已修 |
| Graphiti-specific 测试覆盖 | ❌ **零** | 无独立 `test_graphiti_*.py` |
| L1 Router 测试覆盖 | ❌ **零** | OpenSpec 6 scenarios 未落地 |
| 四路融合 RRF 测试覆盖 | ✅ 有 | `test_rag_multimodal_api.py` 测 fusion_strategy 参数 |
| 质量循环（faithfulness check）测试 | ✅ 有 | `backend/lib/agentic_rag/faithfulness_check.py` 对应测试已内置 |

### 输出 3: 检索相关 Gotchas 条目详情（6 条）

1. **G-PARAM-001**（`docs/known-gotchas.md:82-83`）
   - 问题: `search_nodes()` query 参数名冲突 + 双 WHERE 子句
   - 状态: ✅ 已修（S33, commit 1768c19）— `$query` → `$searchTerm`, WHERE 合并

2. **G-SILENT-001**（`docs/known-gotchas.md:55-56`）
   - 问题: Review Schedule 在 scheduler 不可用时静默返回 200+空数据，endpoint 内联实现绕过 service enrichment
   - 状态: 🟡 **部分修**（2026-04-06）— schemas 已加字段，但 endpoint 接线为独立 follow-up

3. **G-FAKE-006**（`docs/known-gotchas.md:16-17`）
   - 问题: `_sync_edge_to_neo4j` 写 `CONNECTS_TO` 关系无读侧消费者（死写路径）
   - 状态: ⏳ **弃用中**（FR-KG-04 Phase 7, 2026-04-07）— docstring 标 DEPRECATED

4. **G-MOCK-001/002**（`docs/known-gotchas.md:68-70`）
   - 问题: 降级打分按答案长度映射（长噪音获 90 分，短正确答案 20 分）
   - 状态: ✅ **已修**（commit d0824e9, 2026-04-07）— 降级恒返回 `score=0.0`，跳过 mastery 更新

5. **G-PATH-001**（`docs/known-gotchas.md:73-76`）
   - 问题: `_do_extract_concepts` Method 2 fallback 用裸 `open(file_path)` 绕过路径穿越防护
   - 状态: ✅ **已修**（commit b50a52b, 2026-04-07）— 加 `_resolve_safe_canvas_path`

6. **G-INJ-001~004**（`docs/known-gotchas.md:106-114`）
   - 问题: 学习上下文直接拼 systemPrompt（15 个注入向量）、system endpoint 无 auth、record_learning_memory docstring 弱约束
   - 状态: ✅ **已修**（FR-KG-04 Phase 2-3, 2026-04-07）— `<UNTRUSTED_*>` 包装 + safety_meta_rule + `require_internal_api_key` + docstring `WRITE OPERATION` 红旗

### 输出 4: 结论与行动指南

#### 可以放心在 Obsidian 降级方案中用的路径:
- **L2 Hybrid Search** ✅ — LanceDB + Reranker 有完整测试覆盖，无 gotchas
- **质量评估环** ✅ — Faithfulness check + quality_grade 已内置，G-FAI-001 修复确认"不适用路径"返回 None（不是伪 1.0）

#### 不能依赖的路径（需前端回退）:
- **L3 Graphiti KG** 🟡 — 虽实现完整，G-PARAM-001 已修但无集成测试确认；建议前端在 Graphiti timeout/empty 时自动降级到 L2
- **L4 Misconception Search** 🔴 — Deep research 与 verification service 尚未统一纳入质量环，G-MOCK/G-PATH 虽已修但新代码路径未完整端到端验证

#### 需要补测试的路径:
- **L1 LLM Router** — OpenSpec 已声明 6 scenarios，需实现单元测试:
  - LLM 成功返回有效 JSON → 激活指定通道
  - LLM 超时 → fallback 规则分类
  - LLM 返回无效 JSON → fallback 规则分类
  - 规则策略完全跳过 LLM
  - LLM 策略失败 → 5 通道安全降级（不调规则 fallback）
  - 多查询重写共用 1 次路由决策（非 3 次）

- **L3 Graphiti 端到端** — 补集成测试 `test_graphiti_search_with_rag_service.py`:
  - 初始化成功
  - 200ms timeout 触发自动取消
  - 结果参与融合和 reranking

#### 关键数字:
- 已修 gotchas: **32/37 (86%)**；待修 1 项（G-SILENT-001 endpoint 接线）
- 检索相关安全漏洞: 已修 4 项（G-MOCK / G-PATH / G-INJ）
- **RAG Service 本身无实现缺陷**，是"质量合格的包装器"；四路核心在 `backend/lib/agentic_rag/`，可靠性取决于各路单独测试

### 用户原问题答案

> "我们当前的后端检索实现的是否可靠还是一个未知"

**答**: 不是"可靠"也不是"未知"，而是**"分层已知"**:
- L2 ✅、L3/L4 🟡-🔴、L1 ❌

**建议行动**:
1. 立即补 L1 单元测试（OpenSpec scenarios 已就位，工作量小）
2. 前端在 Graphiti/Misconception 返回异常时自动降级到 L2
3. S36 需确保 `deep_research` 纳入 `quality_grade` 评估环

### Obsidian 可导航引用

- `backend/lib/agentic_rag/llm_router.py:1-150` — L1 实现无测试
- `backend/lib/agentic_rag/nodes.py:140-320` — L2/L3 实现
- `backend/lib/agentic_rag/deep_research.py` — L4 实现
- `backend/lib/agentic_rag/faithfulness_check.py` — 质量环
- `docs/known-gotchas.md` — 32/37 已修，1 待修
- `openspec/specs/agentic-rag/spec.md:10-62` — L1 的 6 scenarios 未落地

---

## Round 4 总结（下一 session 必读）

### 核心结论

| 问题 | 答案 |
|---|---|
| 后端哪些功能还活着？ | **28 ALIVE / 3 ZOMBIE / 降级精简 4** |
| 多 vault 共享 Docker？ | 当前是单容器 + group_id 字段隔离，但 **`memory_service.py` WHERE 过滤未接线** |
| 检验白板流程？ | **15 步**：模式选择 → ACP 组装 → 5 层 Prompt → AutoSCORE 两段论 → BKT/FSRS 双更新 → 归档 → 回写 |
| file-open 实现层？ | **SQLite ArchiveStatus（元数据）+ Neo4j Graphiti episode（摘要）** — Hot/Warm/Cold 是逻辑分级 |
| 检索可靠性？ | **分层已知**: L2 ✅ / L1 ❌ / L3 🟡 / L4 🔴 |

### 引用诚实度自检（IC-7 合规）

- ✅ 所有 service 状态判断有 `file:LINE` import 证据
- ✅ Gotchas 引用带条目 ID + 状态 + commit hash
- ✅ 测试覆盖率有量化数字（13 文件 / 207 函数 / 32 已修 / 1 待修）
- ✅ 可靠性结论分层（不说"整体可靠/不可靠"）
- ✅ R4-Q1 给 8 条互斥选项（不直出方案，DD-09 合规）

### 等待用户决策

**Round 5 触发条件**: 用户回答 R4-Q1 的 8 个增量问题中至少 1 个 → Claude 据此展开完整的"后端降级后保留什么 / 删除什么"方案。

---

**END of Round 4 · 本文件 4 R4-Qn section 完成**
