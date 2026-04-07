## Context

A11.md 用户 vision（"deep-explore 生成 plan 文件 → 按 plan 考察 → 逻辑递进"）+ deep research 4 决策点（D1-D4）的交叉分析（详见 `proposal.md` Why 段）。本 design 聚焦"如何把 plan-driven exam 落地为可实施的架构"，以及"deep research 的 D2/D3 在 plan-driven 框架下的位置"。

### 关键名词

- **Plan-driven exam**：考前 Claude（或算法）对 canvas 做深度理解，产出一个结构化的 exam plan file（节点序列 + 每节点的题型 + 进入下一节点的条件），整个 exam session 严格按 plan 执行，不在 session 中临时改变顺序。
- **Plan file**：人类可读的结构化文档（候选格式：Markdown / YAML / JSON tree / Mermaid），包含 metadata (canvas_id, generated_at, generator_version)、节点序列、题型、进度条件。
- **L1/L2/L3 难度递进**：单节点题（L1，"什么是 X"）→ 双节点关系题（L2，"X 和 Y 的关系是什么"）→ 多节点综合题（L3，"用 X+Y+Z 解释一个新场景"）。Graphiti 已有 L1/L2/L3 question system 的概念基础。
- **Mastery-based progression**：deep research D3 推荐的 in-exam adaptation 策略，根据实时 mastery 分数决定下一题的难度。**与 plan-driven 不同**：plan-driven 是 pre-exam planning，mastery-based 是 in-exam scoring。

### Phase 1 Deep Explore 关键发现（3 个并行 agent 调研结论）

1. **A11.md 的"plan-driven exam"和 deep research 的"mastery-based progression"是不同概念**：
   - Plan-driven exam = **pre-exam planning phase**（考前生成结构化 plan 文件）
   - Mastery-based progression = **in-exam adaptation**（考试中根据实时分数调节）
   - 两者都需要，但 Phase 0 主线应该是前者（用户原话）
2. **D1（segment commit）已经在 commit `e999dc8` 完整实现**：`_partition_by_entity_type` + `_SEGMENT_ORDER_UPSERT = ("board", "node", "edge")` + 各段独立 commit + `SyncErrorClass` 三值枚举 + 前端 sync-engine 已消费。**只剩"跨 batch 幂等去重"残余 gap**，不在本 Phase 0 范围。
3. **D2（KG fusion）当前是隐式融合**：`_get_kg_relevance` 在单个 Cypher 查询里 SUM(CASE type(r) ...) 把 CANVAS_EDGE 1.0 + RELATES_TO 0.7 混在一起。Deep research 推荐**显式分离**两个 score（canvas vs semantic）再按 0.7/0.3 融合。本 Phase 0 在 D4 决策中给出"先确定 plan generator 的接口需求，再优化 kg_relevance 输出格式"的反向设计原则。
4. **D3（progressive examination）当前完全没实现**：仅有 3 因子公式，无 topological ordering，无 mastery-only 模式，无 plan generation pipeline。
5. **D4（doc drift）是误报**：sync_router 在 `backend/app/api/v1/router.py:43,355-363` 已正确注册；FR-KG-04 docs 里的 "Orphaned" 标记是**自我纠正注释**，不是真的 orphaned。本 Phase 0 不处理。

### Constraints

- **Phase 0 = 纯设计**：本 change 不允许任何代码改动。所有实现 task 留到 Phase 1+。
- **不破坏现有回归**：A11 regression suite (30 tests, `test_kg_relevance_weighted.py` + `test_a11_kg_relevance_e2e.py`) 必须保持 green。本 change 不动后端代码所以默认 pass。
- **必须能通过 `npx openspec validate --strict`**：4 artifact 完整，spec scenario 用 4-hashtag header，proposal 用 `## Why` 而非 `## What & Why`。

## Goals / Non-Goals

**Goals:**

1. 定义 plan-driven exam 的**接口契约**（plan file schema + Plan generation API + Plan execution API），让后续 Phase 1 实现有明确目标。
2. 把 deep research D2 (KG fusion) 和 D3 (mastery progression) 锚定到本架构的具体位置，避免"4 个独立决策互相冲突"。
3. 为现有 3 因子公式给出**可逆 deprecation 路径**（不是直接删除）。
4. 区分本 Phase 0 的产出（4 份 spec 文档）和后续 Phase 的实现任务（仅在 tasks.md 列入口，不执行）。
5. 显式标注后续需要触发的 UX/TECH 决策点，方便 Phase 0 commit 后立即用 AskUserQuestion / ChatGPT Deep Research 推进。

**Non-Goals:**

- 不实现任何 plan 生成代码
- 不修改 `select_target_node()` 或 `_get_kg_relevance()`
- 不动 sync_service / segment commit / SyncErrorClass
- 不加 lefthook hook 检查 doc drift
- 不写 Phase 1 的实现 tasks（只列出 phase 入口，标记为 NOT executed）
- 不修改 `algo-question` 现有 Requirement
- 不写 `algo-rag` 的 spec delta
- 不锁定 plan 文件格式、生成方式、存储位置（这些是后续 UX/TECH 决策）

## Decisions

### D1: Plan-driven exam vs mastery-based progression — 共存而非互斥

**Choice**: 两者是不同 layer，plan-driven 是高层 orchestration，mastery-based 是 plan 生成时可选的一种 strategy。

**Rationale**:

- Phase 1 Deep Explore Agent C 验证发现这两个概念在 timing/inputs/outputs/purpose 上完全不同：
  - Plan-driven = pre-exam, 输入 canvas, 产出 plan file, 目的是 transparency
  - Mastery-based = in-exam, 输入实时分数, 产出 next-question 决定, 目的是 adaptation
- 用户在 A11.md 明确要求 plan-driven 形式（"按 plan 文件考察"），因此 plan-driven 是 Phase 0 主线。
- Deep research D3 推荐的 mastery-based progression 在 plan-driven 框架下变成"plan 生成器的一种 strategy 选项"（除此还有 topological / random / user-curated 等）。

**Alternatives considered**:

- **(A) 选 plan-driven 作为唯一范式**：排除 mastery-based 的学术成熟度，违反 deep research D3 建议 → **拒绝**
- **(B) 选 mastery-based 为主**：偏离用户原话 A11.md 直接诉求 → **拒绝**
- **(C) 共存（采用）**：plan-driven 高层 + mastery-based 低层 strategy → **采用**

**Trade-offs**: 略增加架构复杂度（需要 strategy 抽象层），但换来更高的 vision-fit。

### D2: Plan file format — Markdown vs YAML vs JSON tree vs Mermaid

**Choice**: 这是 UX 决策，**待 Phase 0 commit 落地后用 AskUserQuestion 向用户确认**。本 design 暂以 Markdown 为推荐起点（最人类可读，符合用户"plan 文件"的语义直觉）。

**Rationale 起点**:

- Markdown：最人类可读，符合用户"plan 文件"的直觉，git diff 友好
- YAML：结构化数据，机器可解析，但语法可能需要解释
- JSON tree：完全机器友好，但人类可读性差
- Mermaid diagram：可视化优先，但需要渲染器

**Marker**: `[DECISION-UX:a11-phase0/plan-file-format]` — 在 Phase 0 commit 后的 follow-up session 中触发 AskUserQuestion。

### D3: Plan generation approach — LLM-based vs algorithmic vs hybrid

**Choice**: 这是 TECH 决策，**待 Phase 0 commit 落地后通过 ChatGPT Deep Research 验证最佳实践**。本 design 推荐 hybrid（LLM 生成 + 算法 fallback）作为起点。

**Rationale 起点**:

- **纯 LLM**：成本高、不可控、用户不信任 → 但能利用 canvas 理解
- **纯算法**（拓扑排序 / 度数排序 / mastery 排序）：便宜、可审计，但对边语义敏感、可能"算法估计也是编的"
- **Hybrid**（推荐起点）：LLM 生成草稿 + 算法验证 + 必要时算法 fallback → 取两者之长

**Alternatives considered**:

- **(A) 纯 LLM**：用户在 A11.md 明确表达对"算法"不信任，但纯 LLM 也是"编的"，且成本+可审计性差 → **拒绝作为唯一方案**
- **(B) 纯算法**：可审计，但与用户原话"deep explore 生成 plan"的语义不符 → **拒绝**
- **(C) Hybrid（采用起点）**：LLM 做创造性生成，算法做 verification + fallback，最大化各自优势 → **采用为起点，待 ChatGPT Deep Research 验证**

**Marker**: `[DECISION-TECH:a11-phase0/plan-generation-approach]` — Phase 0 commit 后 follow-up session 触发 ChatGPT Deep Research 双向通信协议。

### D4: KG relevance 在 plan generation 中的角色（承接 deep research D2）

**Choice**: KG relevance 是 plan generator 的**输入信号之一**，不是直接决定题目顺序的因子。Plan generator 可以用 KG relevance 来：

1. 找到 canvas 的"中心节点"作为 plan 起点
2. 按 connectivity 决定 L1 → L2 → L3 的过渡时机
3. 标记 plan 中的 "high-uncertainty" 节点（`kg_relevance_degraded != None`）

**Rationale**: 倒过来设计——先确定 plan generator 的接口需求，再去优化 kg_relevance 的输出格式，避免"先优化下层 → 上层用不上 → 返工"。Deep research D2（canvas 0.7 + semantic 0.3 显式融合）的实施留到 Phase 2，**前置依赖**是本 Phase 0 先确定 plan generator 怎么消费 KG signal。

**Alternatives considered**:

- **(A) 先实施 D2 显式 fusion，再设计 plan generator**：bottom-up 设计，可能产出 plan generator 用不上的 fusion 输出 → **拒绝**
- **(B) Plan generator 不消费 KG signal，只用 mastery 信号**：违反 A11.md 用户原话"deep explore 理解关系" → **拒绝**
- **(C) Top-down 设计：先定 plan generator 接口，KG fusion 反向适配**：避免返工 → **采用**

### D5: 3 因子公式的 deprecation 路径

**Choice**: 三阶段 deprecation：

1. **Phase 0（本 change）**：在 spec 中标注 3 因子公式为 "legacy fallback"，记录 deprecation rationale。
2. **Phase 1**：在 `select_target_node()` 加 feature flag，默认关闭（保持现状），但允许实验性开启 plan-driven 模式。
3. **Phase 2+**：plan-driven 验证可用后，把 3 因子公式降级为"plan 生成失败时的 fallback strategy"。

**永不删除**：3 因子公式作为 last-resort fallback 永久保留，避免 plan generator 完全失败时考试无法进行。

**Rationale**: 用户在 A11.md 表达了对 3 因子的不信任，但完全删除会破坏现有 e2e 测试（`test_a11_kg_relevance_e2e.py` 7 个 e2e + `test_kg_relevance_weighted.py` 18 个 unit 都依赖该公式）。降级而非删除既尊重用户意见，又保护现有 regression 守护。

**Alternatives considered**:

- **(A) 直接删除 3 因子公式**：破坏 30 个 A11 regression tests，违反 DD-03 不破坏现有回归原则 → **拒绝**
- **(B) 平行存在 plan-driven 和 3 因子两套，永不 deprecate**：用户长期不知道哪个生效，增加困惑 → **拒绝**
- **(C) 三阶段 deprecation（采用）**：可逆、有 fallback、tests 受保护 → **采用**

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Phase 0 设计太抽象，Phase 1 无法直接实施 | tasks.md 中明确列出 Phase 1 entry points；spec scenarios 用具体 WHEN/THEN，每个 Requirement 有 scenario 当作 contract test 模板 |
| 用户读完 spec 觉得"还是没解决问题" | proposal.md 的 Why 段直接引用 A11.md 原话；design.md D5 显式说明 3 因子 deprecation 路径 |
| `exam-planning` capability 名字和 `algo-question` 重叠 | design.md D1 + Context 显式画出"高层 planning vs 低层 scoring"分层关系 |
| Plan 生成依赖 LLM 调用，成本高 | D3 推荐 hybrid，允许算法 fallback；具体 LLM prompt 设计留到 Phase 1 |
| 后续 phase 不实施，本 change 沦为僵尸文档 | tasks.md 列出 trigger conditions（用户验收 Phase 0 spec 后启动 Phase 1） + UX/TECH 决策 marker，Phase 0 commit 后立即追问推进 |
| `exam-planning` 名字和未来其他 change 冲突 | Phase 0 commit 后立即在 Graphiti 记录 `[Decision] exam-planning capability claimed by a11-phase0` 占位 |
| 用户跳过 D2/D3 决策直接想看到代码 | tasks.md 0.6 明确 follow-up 决策为 Phase 1 前置依赖；不允许跳过 |

## Migration Plan

本 Phase 0 不涉及任何代码 migration（纯文档 change）。

**Rollback**:

```bash
git revert <phase0-commit>
```

回退后 `openspec/changes/a11-phase0-plan-driven-exam-architecture/` 整个目录消失，没有任何代码副作用。

**后续 Phase migration 路径**（仅作参考，不在本 Phase 0 执行）：

1. Phase 1 启动前，先解决本 Phase 0 commit 后的 7 个 follow-up 决策（4 UX + 3 TECH，详见 tasks.md 0.6 + Open Questions §1）
2. Phase 1 实施 plan generator + plan executor + feature flag（默认关闭）
3. Phase 2+ 实施 D2 KG fusion + mastery strategy 选项 + 3 因子降级为 fallback-only

## Open Questions

### §1. 待 Phase 0 commit 后用 AskUserQuestion 触发的 UX 决策（4 项）

- **`[DECISION-UX:a11-phase0/plan-file-format]`** — Plan 文件格式选择：Markdown / YAML / JSON tree / Mermaid diagram?
- **`[DECISION-UX:a11-phase0/plan-visibility]`** — 用户能不能看到 plan 文件：始终展示 / 默认隐藏可展开 / 完全隐藏?
- **`[DECISION-UX:a11-phase0/plan-editability]`** — 用户能不能编辑 plan：只读 / 内联编辑 / 重新生成?
- **`[DECISION-UX:a11-phase0/plan-regeneration-trigger]`** — 何时触发 plan 重新生成：每次 exam / 仅 canvas 改动后 / 仅用户明确请求?

### §2. 待 Phase 0 commit 后用 ChatGPT Deep Research 触发的 TECH 决策（3 项）

- **`[DECISION-TECH:a11-phase0/plan-generation-approach]`** — Plan 生成方式：纯 LLM / 纯算法 / Hybrid?
- **`[DECISION-TECH:a11-phase0/plan-storage]`** — Plan 存储位置：文件系统 / Neo4j episode / SQLite / In-memory?
- **`[DECISION-TECH:a11-phase0/plan-execution-statefulness]`** — Plan 执行模型：服务端状态机 / 客户端 replay / Hybrid?

### §3. Phase 1 启动前必须明确的细节

- L1/L2/L3 题目模板的具体 prompt 由谁起草？（考虑复用 Graphiti 既有 L1/L2/L3 question system）
- Plan generator 的成本上限（如选 LLM-based 或 hybrid，需明确每次 plan 生成的 token 预算）
- Feature flag 命名规范（`exam_plan_driven` vs `plan_driven_exam` vs `EXAM_PLANNING_ENABLED`）

## Deferred (out of Phase 0 scope)

以下 5 项在 Phase 1 Deep Explore 中被识别为相关，但**不在本 Phase 0 范围**，留作独立 change：

- **D1 sync idempotent consumer**：`_deduplicate_by_operation_id` 已在 commit `e999dc8` 实现 batch 内去重，跨 batch 幂等留给独立 change `data-sync-cross-batch-idempotency`
- **D4 doc drift CI**：调研发现 sync_router 实际已注册，"Orphaned" 是自我纠正注释。独立 change `repo-compliance-doc-drift-hook` 处理（如果用户要做的话）
- **Plan generation 的具体 LLM prompt 模板**：留到 Phase 1
- **Plan execution 的状态机实现**：留到 Phase 1
- **3 因子公式的 feature flag 实现**：留到 Phase 1
