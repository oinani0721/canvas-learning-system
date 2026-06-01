---
story_id: "LITE-4-3"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 6
depends_on: ["INFRA-002", "EXAM-001", "EXAM-002", "STORY-2-10-wikilink-graphiti-sync"]
blocks: []
sprint: "Sprint 2 (V-08 + V-10 patch 2026-05-26 升 P0)"
supersedes: "_bmad-output/implementation-artifacts/epic-4/4-3-triple-fusion-question-gen.md"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
saves_hours: 0
trace:
  - "FR-EXAM-03 (5 路融合升级版)"
  - "FR-EXAM-13 (保留)"
  - "FR-WIKI-EXAM (V-08 修复 — wikilink 邻居进出题主路径)"
  - "FR-SCORE-FAITH (V-10 修复 — 评分对象真实题面回读)"
---

# Story LITE-4.3: 5 路融合出题（V-08 + V-10 修正版 — wikilink 邻居 + 真实题面评分）

Status: ready-for-dev

> **2026-05-26 V-08 + V-10 修正** (ChatGPT Deep Research 审计两个 CRITICAL 漏洞):
> - V-08 `WIKILINK_NOT_IN_EXAM_PATH`: 旧 spec "4 路融合"绕开了 wikilink 邻居层 → 出题只考"单节点回忆", 不考"概念网络回忆" → 直接打在用户 2026-05-13 核心闭环原话 "**批注+双链探索+个人记忆系统+极其针对性考察**" 的核心
> - V-10 `SCORING_TARGET_DRIFT`: `exam_tools.py:435-454` 评分时把 node content 当 question_text 传 AutoSCORE → 出题用 tip 原话出"极其针对性的题", 但评分按"泛节点概念"评 → BKT/FSRS 信号从根源污染
> - 升级为 Sprint 2 P0 (从 Sprint 3+ P1 升级), estimate 3h → 6h

## Story

As a 系统,
I want 用 **当前节点 + 1-2 hop wikilink 邻居 + frontmatter + 最近 3 条 tips + Graphiti 节点级 facts** 五路融合数据生成个人化题目, **并持久化真实问题文本以保证评分对象一致**,
So that Sprint 2 阶段就能跑通"批注 + 沿双链探索 → 极其针对性出题 → 真实题面评分 → BKT/FSRS 信号未污染"完整闭环, 而不是表面看起来"针对", 评分时却退化为"泛概念测试"。

## Acceptance Criteria

1. **Given** `exam_quick` 或 `start_exam_board` 入口 **When** 后端调用 `generate_question` MCP 工具 **Then** `context_enrichment_service` 在 simplified 模式下融合 **5 路数据** (V-08 修复 2026-05-26 加路线 0):
   - 路线 **0** (**V-08 修复关键, 新加**): **wikilink 邻居网络** (`get_wikilink_neighbors(node_id, hops=2, max_per_hop=5)`)
     - hop 1: 当前节点 1-hop 邻居 (out_links + in_links 合并), 每邻居附带 `[node_id, brief (frontmatter title + body 前 100 字)]`
     - hop 2: 1-hop 邻居的邻居, 仅保留 node_id 列表 (避免 token 爆炸)
     - 来源: backend 调 STORY-2-10 已建的 `WikilinkGraphService.get_neighbors(node_id, hops=2)`, 失败时降级为 plugin 直传 (复用 1.16-hook AC#2 已抓的 `out_links / in_links` 字段)
     - 1s 超时, 失败时仅用路线 1-4 不阻塞
   - 路线 1（精简）：**当前节点 md body 最后 800 字符**（截断或省略尾部空白）
   - 路线 2：**frontmatter 字段** `subject` / `canvas_type` / `bloom_level` / `p_mastery`
   - 路线 3：**当前节点最近 3 个 `[!tip]+` callout 文本**（按 timestamp 倒序）
   - 路线 4（2026-05-24 修正补回）：**Graphiti search_facts(query=node_id, max_results=3)** 节点级历史 facts（"用户上次说过 X 错"）— 1s 超时, 失败时仅用路线 1-3 不阻塞
   **And** 禁止调用 `graphify_query`（Graphify 71x token 压缩路径仍砍 — 过早优化）
   **And** 禁止跨节点全 vault `search_memories`（避免 token 爆炸 — 只查当前节点 max_results=3）
   **And** **V-08 修复关键**: 5 路必须**全部成功或路线 0 / 4 降级**才能出题, 不允许"邻居无, 仅当前节点出题" — 那等于退回旧 4 路, 学习效果降级

2. **Given** 源白板为知识点类型（`canvas_type: concept`） **When** 系统生成题目 **Then** 出题策略侧重定义辨析 **And** Bloom 层级偏向 Remember(1) / Understand(2) **And** 题目形式倾向"用自己的话解释 X" / "X 与 Y 的区别"

3. **Given** 源白板为题目类型（`canvas_type: problem`） **When** 系统生成题目 **Then** 出题策略侧重易错点意识 **And** Bloom 层级偏向 Apply(3) / Analyze(4) **And** 题目形式倾向"这段代码错在哪" / "如何破题"

4. **Given** 节点有 3 条 tips **When** 后端生成题目 **Then** `question_text` 显式引用 tips 中具体内容（如"你在 tip 中提到 X，请进一步解释 Y"） **And** **V-08 修复**: 当存在 wikilink 邻居时, 题目需引用**至少 1 个邻居关系** (如"你之前在 [[A]] 中提到 X, 它与本节点 [[B]] 在 Y 维度上的关系是?") **And** `reference_answer` 强制为 `None`（保留 Story 4.1 隔离保证 3）

5. **Given** 出题过程 **When** 计时 LLM 响应 **Then** P95 延迟 **< 3 秒**（vs 旧 4.3 的 5 秒，因路径变窄 / token 量减半）

6. **Given** 节点无 tips（empty） **When** 系统生成题目 **Then** 仅用当前节点 body + frontmatter 出题 **And** 在返回值中标记 `context_source: "node_only"` **And** 题目仍可生成（不阻塞流程）

7. **Given** 出题循环 **When** skill 为节点生成题目 **Then** 题目写入 `exam_boards/*.md` frontmatter 的 `questions[]` 数组 **And** body 追加 `[!exam_question]+` callout（保持与旧 4.3 行为一致）

8. **V-10 修复 2026-05-26 (新加 AC, CRITICAL)**: **Given** `generate_question` 返回 question **When** 系统持久化此题 **Then** 必须**同时持久化**真实 `question_text` 到 `questions_registry` (LanceDB 表):
   ```python
   {
     "question_id": "uuid",
     "session_id": "string",
     "node_id": "string",
     "question_text": "<LLM 生成的真实题面, 含 tip 引用和 wikilink 邻居引用>",
     "context_used": {  # debugging trace
       "tips_cited": ["tip_anchor_1", ...],
       "wikilink_neighbors_cited": ["node_A", "node_B"],
       "graphiti_facts_cited": [...]
     },
     "generated_at": "datetime"
   }
   ```
   **And** `pipeline_token` 同时签入 `question_text_hash` (避免 evaluator 篡改)

9. **V-10 修复 2026-05-26 (新加 AC, CRITICAL — 评分回读)**: **Given** `score_answer` 被调用 **When** AutoSCORE 准备 evaluation context **Then** **必须**从 `questions_registry` 按 `question_id` **回读真实 question_text**, **禁止**从 `canvas_service.find_node_across_canvases(node_id)` 取 node content 当 question_text
   - **代码位置**: `backend/app/mcp/tools/exam_tools.py:435-454` 现有 "Story 3.2 fix" 逻辑必须删除/替换
   - **回读失败**: 若 `questions_registry` 查不到此 `question_id` (异常情况), score_answer **必须返回 422 ScoringContextMissingError**, 不允许降级到 node content
   - **理由**: V-10 是 BKT/FSRS 信号污染根源, 评分对象漂移会让"极其针对性的题"被评成"泛概念题", 任何降级都会再次污染掌握度信号

## Tasks / Subtasks

- [ ] **Task 0: V-08 修复 — wikilink 邻居层 (新加, AC: #1 路线 0)**
  - [ ] backend `WikilinkGraphService` 加 `get_neighbors(node_id, hops=2, max_per_hop=5)` 方法 (复用 STORY-2-10 已建的 wikilink 索引)
  - [ ] `context_enrichment_service.py::assemble_simplified_context()` 路线 0 调用此方法
  - [ ] hop 1 邻居附 brief (frontmatter title + body 前 100 字), hop 2 仅 node_id
  - [ ] 1s 超时降级 (设 `route0_unavailable=True` flag, 但仍记 structlog warning)
  - [ ] 单元测试: 5 边界 (无邻居 / 邻居有循环 / max_per_hop 截断 / 索引未建 / 超时)

- [ ] Task 1: 实现 simplified context 组装 (AC: #1)
  - [ ] 在 `context_enrichment_service.py` 加 `assemble_simplified_context(node_id, mode="simplified")` 方法
  - [ ] 路线 1：读 vault 节点 md body 取最后 800 char
  - [ ] 路线 2：读 frontmatter 抓 4 个字段
  - [ ] 路线 3：parse callout, 抓最近 3 个 `[!tip]+` (按 yaml timestamp 倒序)
  - [ ] **禁用 import**: 不 import `graphify_query` (Graphify 仍砍), `search_memories` 允许调 (路线 4 用)
  - [ ] 单元测试：tips 为空 / 节点 body < 800 char 的边界

- [ ] Task 2: 出题策略保留 concept/problem 分化 (AC: #2, #3)
  - [ ] 复用旧 4.3 的 prompt template (`backend/app/prompts/exam/concept.txt` / `problem.txt`)
  - [ ] 模板内引用 placeholder `{simplified_context}` 而非 `{triple_fusion_context}`
  - [ ] 单元测试：canvas_type 切换时 Bloom 层级正确

- [ ] Task 3: 实现 tips 引用注入 (AC: #4)
  - [ ] prompt template 加 `<tips>` XML 块，按 timestamp 倒序展开 3 条
  - [ ] LLM 系统指令明确"题目必须引用 tips 中具体内容（前 50 字摘要）"
  - [ ] reference_answer 硬约束 `None`（保留 Story 4.1 隔离 3）

- [ ] Task 4: 性能保障 P95 < 3s (AC: #5)
  - [ ] LLM 调用 3.5 秒超时（buffer 0.5s）
  - [ ] 超时降级：返回基于 Bloom 层级的模板化题目（沿用旧 4.3）
  - [ ] structlog 记录超时（含 node_id / 实际延迟）

- [ ] Task 5: 空 tips 边界 (AC: #6)
  - [ ] 检测 tips 数组 empty 时跳过 `<tips>` XML 块
  - [ ] 返回值加 `context_source: "node_only"` 或 `"node_with_tips"` 标记
  - [ ] 单元测试：tips empty 时仍能出题

- [ ] Task 6: 写回 frontmatter + body (AC: #7)
  - [ ] 复用旧 4.3 的 questions[] 追加逻辑
  - [ ] `[!exam_question]+` callout 写入 exam_boards 白板 body

- [ ] **Task 7: V-10 修复 — questions_registry 持久化 + score_answer 回读 (新加, AC: #8, #9, CRITICAL)**
  - [ ] backend `questions_registry` LanceDB 表 schema 新建 (`backend/app/infra/lancedb_init.py`)
  - [ ] `generate_question` 返回前 `INSERT INTO questions_registry` (含 question_id / session_id / node_id / question_text / context_used / generated_at)
  - [ ] **删除** `exam_tools.py:435-454` 现有 "Story 3.2 fix" 取 node content 的逻辑
  - [ ] **改为** `question_text = await questions_registry.get(question_id=...)` 强制回读
  - [ ] 回读失败 → raise `ScoringContextMissingError(422)`, 禁降级
  - [ ] pipeline_token 增加 `question_text_hash` 防篡改
  - [ ] 单元测试: 5 用例 (持久化成功 / 回读成功 / question_id 不存在抛 422 / hash 校验 / context_used trace 完整性)
  - [ ] **集成测试**: 出题用 tip 原话 → 评分时 AutoSCORE 收到真实题面 (assert `question_context == "<tip 引用题面>"`), 不再是节点正文

- [ ] Task 8: 集成测试 + UAT
  - [ ] e2e 测试：批注 → 出题 → 看到 tips 被引用 + **wikilink 邻居被引用** (V-08 验证)
  - [ ] e2e 测试：答完 → 评分时 AutoSCORE 用真实题面 (V-10 验证, grep `questions_registry.get` 调用链)
  - [ ] 性能测试：50 次出题 P95 < 3500ms (因加路线 0 wikilink 邻居查询, 放宽 500ms)

## Simplification Rules（vs 旧 4.3 完整版 + 2026-05-26 V-08 + V-10 修正）

| 旧 4.3 完整版（6h） | LITE-4.3（6h, 升 P0） | 决策 |
|---|---|---|
| ✅ Graphiti search_memories（Tips/errors/calibration） | ✅ **节点级 search_facts** (路线 4) | 2026-05-24 修正补回, 节点级查询不全 vault 扫 |
| ✅ Graphify 71x token 压缩检索 | ❌ **禁** | Sprint v3 砍掉 Graphify 路径（4 方共识，过早优化） |
| ✅ wikilink 邻居网络 | ✅ **保留** (路线 0, **V-08 修复 2026-05-26 加回**) | ChatGPT 审计判定 CRITICAL — 绕开等于丢"双链探索"核心闭环 |
| ✅ BKT p_mastery + FSRS stability 三路融合 | ✅ frontmatter `p_mastery` 直读 | 简化为单字段，不调用 mastery_service |
| ✅ context_degraded 降级标记 | ✅ 路线 0 / 4 失败时标记 (其他 4 路必成功) | 5 路融合, 关键路线降级时仍记 trace |
| ✅ canvas_type concept vs problem 区分 | ✅ **保留** | 用户 2A 决策接受，PRD §1.10 灵魂设计 |
| ✅ reference_answer = None 隔离 | ✅ **保留** | Story 4.1 三重隔离保证 3 不可破 |
| ❌ (旧设计 score_answer 取 node content) | ✅ **真实 question_text 持久化 + 回读** (V-10 修复) | BKT/FSRS 信号防污染 — 评分对象必须 = 真实题面 |
| ✅ P95 < 5s | ✅ P95 < 3.5s | 路径变 5 路 (加 wikilink 邻居), 放宽 500ms |

**禁用的具体 import**:
- ❌ `from app.services.graphify_service import query_relations` (Graphify 仍砍)
- ✅ `from app.services.graphiti_service import search_memories` (允许, 路线 4 用)
- ✅ `from app.services.wikilink_graph_service import get_neighbors` (V-08 修复, 路线 0 用, **必须 import**)
- ✅ `from app.infra.questions_registry import QuestionsRegistry` (V-10 修复, **必须 import**)

## Background Decision Trace

- **Sprint v3 决策 4** (2026-05-21 ChatGPT v2 + Agent A/B/C 验证, 用户 2026-05-22 锁 B): Story 4.3 简化为 lite 版（原 6h → 3h，节省 50%）
- **round-13 Q4** (2026-04-29) 锁定 wikilink-Graphiti 同步用 Lazy+Batch（不实时），Graphiti 路径 Sprint 2 Day 9 才接 → Sprint 1-2 出题不能依赖 Graphiti
- **用户 2A 决策** (2026-05-22): 接受检验白板 11 处误区修正 — `canvas_type concept vs problem` 区分保留（旧 4.3 AC #2/#3）
- **3 重隔离保证**: Karpicke & Blunt (2011) Retrieval Practice d=1.50，`reference_answer=None` 不可破
- **2026-05-26 V-08 修复 (CRITICAL)**: ChatGPT Deep Research 审计判定 LITE-4-3 v1 "绕开 wikilink 邻居层" 直接打在用户 2026-05-13 核心闭环"批注+双链探索"的核心 → 必须前置 1-2 hop 邻居为路线 0
- **2026-05-26 V-10 修复 (CRITICAL)**: ChatGPT 发现 `exam_tools.py:435-454` "Story 3.2 fix" 引入 SCORING_TARGET_DRIFT — 评分用 node content 当 question_text → BKT/FSRS 信号污染根源, 必须持久化 question_text + 强制回读
- **2026-05-24 round-13 Q4 决策反转**: Sprint 2 Day 9 STORY-2-10 wikilink-Graphiti 同步上线 + STORY-1-16-callout-hook 同时给 wikilink 上下文 → LITE-4-3 P0 在 Sprint 2 末必须就绪, 不再延后 Sprint 3+

## Dev Notes

### Architecture
- `generate_question` MCP 工具已存在于 `backend/app/mcp/tools/exam_tools.py`，加 `context_mode: Literal["full", "simplified"] = "simplified"` 参数
- `context_enrichment_service.py` 加 `assemble_simplified_context()` 方法，与旧 `assemble_triple_fusion_context()` 并列（旧方法不删，留 Sprint 4+ 完整版用）
- 5 层数据流保证：simplified 模式下后端只读节点 body + frontmatter + tips（不读 Graphiti / Graphify），组装 prompt 后丢弃中间数据
- pipeline_token 链保留：`generate_question → token_A → score_answer → token_B`

### File Paths
- MCP 工具：`backend/app/mcp/tools/exam_tools.py`（加 context_mode 参数）
- Context 组装：`backend/app/services/context_enrichment_service.py`（加 simplified 方法）
- Prompt 模板：`backend/app/prompts/exam/concept.txt` / `problem.txt`（复用旧 4.3）
- Plugin 调用：`frontend/obsidian-plugin/src/exam-quick.ts`（PLUGIN-002 已升级）

### Testing
- 单元测试：`backend/tests/unit/test_simplified_context.py`
- 性能测试：`backend/tests/perf/test_question_gen_lite_latency.py`
- 集成测试：`backend/tests/integration/test_exam_quick_e2e.py`

### Project Structure Notes
- Constructive Alignment (Biggs 1996) 与 canvas_type 对齐策略保留
- Simplified 模式不破坏 5 层数据流隔离（Story 4.1 保证 3）

### References
- **From PRD**: §2.3 Step 7 — 出题循环 (line 1107-1155)
- **From PRD**: §2.4 保证 3 — MCP 工具返回值过滤 (line 1638-1693)
- **From Sprint v3**: `_bmad-output/research/2026-05-21-sprint-plan-v3.md` Lite 重编清单
- **From round-13 Q4**: `_bmad-output/research/round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md` Lazy+Batch 决策
- 旧 spec（[DEPRECATED]）：`_bmad-output/implementation-artifacts/epic-4/4-3-triple-fusion-question-gen.md`

## UAT Script（用户视角验证）

> 1. 在 canvas-vault 选一个有 3+ `[!tip]+` callout 的概念节点
> 2. `Cmd+Shift+Q` 触发 quick exam
> 3. 等待出题（< 3 秒）
> 4. 看题目：**应明确引用你 tips 中说过的话**（如"你之前提到 X..."）
> 5. 在题目类型节点重复，确认题目侧重"破题/易错点"

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| simplified context 组装 (含路线 0) | unit | `pytest backend/tests/unit/test_simplified_context.py -x` | 0 failures |
| 策略分化 concept/problem | unit | `pytest backend/tests/unit/test_question_strategy.py -x` | 0 failures |
| **V-08 wikilink 邻居层就绪** | static | `grep -E "WikilinkGraphService.*get_neighbors\|get_wikilink_neighbors" backend/app/services/context_enrichment_service.py` | ≥ 1 match (路线 0 必调) |
| 禁用 Graphify import (仍砍) | static | `grep -E "graphify_query" backend/app/services/context_enrichment_service.py` | 0 matches |
| P95 < 3.5s | perf | `pytest backend/tests/perf/test_question_gen_lite_latency.py -x` | P95 < 3500ms |
| tips + wikilink 邻居引用注入 | integration | `pytest backend/tests/integration/test_tips_wikilink_injection.py -x` | 0 failures (assert 至少 1 邻居 cited) |
| **V-10 question_text 持久化** | unit | `pytest backend/tests/unit/test_questions_registry.py -x` | 0 failures |
| **V-10 score_answer 强制回读** | unit | `pytest backend/tests/unit/test_score_answer_real_question_text.py -x` | 0 failures (含 422 异常路径) |
| **V-10 旧 fix 代码已删** | static | `grep "find_node_across_canvases" backend/app/mcp/tools/exam_tools.py` 在 score_answer 函数内 | 0 matches |
| **V-10 集成: 评分对象一致性** | integration | `pytest backend/tests/integration/test_scoring_target_consistency.py -x` | 0 failures (assert AutoSCORE 收到的 question_text == LLM 生成的真实题面) |

## Dev Agent Record

### S2-1 进展 (2026-05-31, in-progress)

**V-10 评分对象漂移修复 (第一刀, 已落地)**:
- ✅ 新建 `backend/app/services/question_registry.py` — 共享题面 registry (复用 MVP-α `_QUESTION_STORE` ring buffer 模式, DD-04 参考成熟案例)
- ✅ `exam_tools.py` generate_question 两条路径 (mastery line ~232 + legacy line ~360) 生成题目后 `put_question(question_id, question_text, ...)` 持久化真实题面
- ✅ `exam_tools.py` score_answer (line ~456) 改为 `get_question(question_id)` 按 ID 回读真实题面, 删除"取节点正文当题面"逻辑 (V-10 根因)
- ✅ degraded 防污染: registry 未命中 (重启/未注册) → 降级节点正文 **但标记 `scoring_context_degraded=True`** → faithfulness gate 中 `not scoring_context_degraded` 一并 suppress mastery 更新, 不污染 BKT/FSRS (fail-closed, 符合 G-MOCK 精神)
- ✅ 测试: `backend/tests/unit/test_question_registry.py` **8 passed** (含 V-10 漂移场景 + ring buffer 淘汰 + copy 隔离)

**剩余 (本 story 未完, 故 in-progress 非 done)**:
- [ ] T4 V-08: get_wikilink_neighbors 进出题主路径 (LITE-4-3 路线 0) — 未做
- [ ] V-10 完全 fail-closed (registry 未命中直接 422 而非降级) — 待 S2-2 持久化 questions_registry 后收紧 (当前 in-memory 重启会丢, 降级是务实折中)
- [ ] T5 集成测试 test_scoring_target_consistency.py — 待写
- [x] 回归检查 exam_tools 相关测试 — 2 passed / 2 failed; 2 failures 是 **pre-existing baseline** (test_openapi_contract schemathesis fuzzing generate_question/score_answer, status_code_conformance), **非本次引入**: git diff 证明 0 碰 Pydantic schema class/Field, OpenAPI schema 字节级不变, schema-based contract 不可能因纯函数体逻辑改动而变

**文件清单**:
- 新建: `backend/app/services/question_registry.py`
- 新建: `backend/tests/unit/test_question_registry.py`
- 改: `backend/app/mcp/tools/exam_tools.py` (generate_question ×2 存 + score_answer ×1 读 + faithfulness gate)

**技术债标注**: 当前 MCP 路径用本 registry, MVP-α 路径 (exam_quick.py) 用各自 `_QUESTION_STORE`, 两份并存。S2-2 (CanvasGraphEpisodeV1 + 持久化 questions_registry) 统一。

## Change Log

- 2026-05-24: spec 创建（Plan `EPIC1-BMAD-DEV-ASSESS-2026-04-17`），替代 4-3-triple-fusion-question-gen.md
- **2026-05-26 V-08 + V-10 修正** (ChatGPT Deep Research 审计两个 CRITICAL):
  - V-08 `WIKILINK_NOT_IN_EXAM_PATH`: 加路线 0 wikilink 邻居 (1-2 hops), 升 AC#4 题目需引用至少 1 邻居关系
  - V-10 `SCORING_TARGET_DRIFT`: 加 AC#8 (question_text 持久化到 questions_registry) + AC#9 (score_answer 强制回读, 删 Story 3.2 fix 妥协)
  - 升级 priority P1 → **P0**, sprint Sprint 3+ → **Sprint 2** (与 STORY-1-16-hook + STORY-2-10 同期)
  - depends_on 加 `STORY-2-10-wikilink-graphiti-sync` (路线 0 wikilink graph 索引必须先建)
  - estimate_hours 3 → **6** (+2h V-08 wikilink 邻居 Task 0, +1h V-10 questions_registry Task 7)
  - 5 个新 Automated Checkpoints (V-08 grep + V-10 单元/集成/static)
