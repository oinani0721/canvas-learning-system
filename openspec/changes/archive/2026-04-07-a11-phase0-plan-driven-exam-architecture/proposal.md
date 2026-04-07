# Proposal: Plan-Driven Exam Architecture (A11 Phase 0)

## Why

A11.md 用户在 2026-03 提出的原始诉求至今未被解决。原话（`docs/project-status/fr-exploration/A11.md` line 1-2）：

> 节点的选择我觉得就和我们的 docs/project-status/test-infrastructure-report.md 所提到的一个构建 plan 文件一样，你要知道我是对各个节点盘过什么样的理解关系的，然后每次考察的时候可以 deep explore 生成一个 plan 文件，然后按照这个 plan 文件的方式来考察我，考察最好是有逻辑关系来逐步递进的考察我，节点选择：📊 成熟算法（三因子融合），这里的算法估计也是编的，本身没有什么可信的。除了这种出 plan 文件来考察我之外，社区上还有什么成熟高效的做法？

A11 schema drift 修复链（commits `c7215ca`..`cab015e`，2026-04-06~07，42 commits，归档 change `2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening`）解决了 `_get_kg_relevance` 永远返回 0.5 的 silent degradation bug，但**没有触及**用户原始诉求中的两个核心问题：

1. **算法可信度**：当前 `select_target_node()`（`backend/app/services/question_generator.py:103-239`）用 3 因子加权 `0.4 * (1 - p_mastery) + 0.3 * (1 - retrievability) + 0.3 * kg_relevance`（lines 202-206）选下一题。即使 schema drift 修好后 kg_relevance 现在是真实值，整个公式仍然是"黑箱权重"，用户无法审计为什么某个节点被选中。

2. **缺少 plan-driven 范式**：当前没有任何"考前生成 plan → 按 plan 执行"的流水线。每次 `select_target_node()` 调用都是孤立的"下一题贪心"，无法体现"逻辑递进"。

Deep research 报告（`docs/deep-research/07-decisions/deep-research-a11-session-review.md`，commit `8f4a3fd`，2026-04-07）从架构层进一步指出 4 个相关决策点（partial commit / KG fusion / mastery progression / doc drift），其中 D2 (KG fusion) 和 D3 (mastery progression) 直接为本 change 提供支撑性架构设计。

本 Phase 0 是**纯设计 change**，不包含任何代码改动 —— 只产出 4 份 OpenSpec artifact 来锚定后续 Phase 1+ 的实施方向。

## What Changes

本 Phase 0 change 是**纯设计**，输出 4 个 artifact，**不包含任何代码改动**：

- **NEW** capability `exam-planning`，包含 5 个 ADDED Requirements 覆盖 plan 生成、plan 文件 schema、plan-driven 题目选择、L1/L2/L3 progressive 难度、3 因子公式 deprecation 路径
- **NEW** `proposal.md` / `design.md` / `tasks.md` 三个 artifact 锚定后续 Phase 1+ 实施方向
- **DESIGN-ONLY 决策（design.md D1-D5）**：plan-driven vs mastery-based 共存策略、plan 文件格式（标记为待 UX 决策）、plan generator 实现路径（标记为待 TECH 决策）、KG relevance 在 plan generation 中的角色、3 因子公式三阶段 deprecation 路径
- **DESIGN-ONLY 引用**：在 design.md 中显式说明本 change 与 deep research D2 (KG fusion) 和 D3 (mastery progression) 的关系，以及与现有 `algo-question` capability 的低层 scoring 分层
- **不修改任何代码**：不动 `select_target_node()`、不动 `_get_kg_relevance()`、不动 `sync_service`、不加任何 lefthook hook
- **不修改任何现有 spec**：不动 `algo-question` / `algo-rag` 现有 Requirements

## Capabilities

### New Capabilities

- `exam-planning`: Deep-explore canvas understanding → generate structured exam plan file → execute exam by following the plan with logical progressive difficulty (L1 single-node → L2 dual-node relationship → L3 multi-node synthesis). 5 个 Requirements 覆盖 plan 生成、plan 文件 schema 稳定性、plan-driven 题目选择、L1/L2/L3 progressive 难度、3 因子公式 deprecation 路径。

### Modified Capabilities

无。本 Phase 0 不修改任何现有 capability 的 Requirements。

## Impact

- **Breaking changes**: 无（纯设计 change，无代码改动）
- **Migration**: 无（后续 Phase 1+ 实施时再考虑 3 因子公式 deprecation 的 migration 路径，本 change 仅在 design.md D5 给出方向）
- **Affected files**:
  - 新建：`openspec/changes/a11-phase0-plan-driven-exam-architecture/proposal.md`
  - 新建：`openspec/changes/a11-phase0-plan-driven-exam-architecture/design.md`
  - 新建：`openspec/changes/a11-phase0-plan-driven-exam-architecture/tasks.md`
  - 新建：`openspec/changes/a11-phase0-plan-driven-exam-architecture/specs/exam-planning/spec.md`
- **Design-context-only references** (no spec delta):
  - `algo-question`: 现有 Requirements 是 kg_relevance 低层 scoring 的契约。本 change 在 design.md 中说明 `exam-planning` 是高层 plan orchestration，`algo-question` 是低层 scoring，两者分层调用关系。**不修改 algo-question 任何 Requirement**。
  - `algo-rag`: deep research D2 (canvas 0.7 / semantic 0.3 显式 KG fusion) 的承接 capability。本 change 在 design.md D4 说明该 fusion 实施留到 Phase 2，**不写 spec delta**。
- **Risk**: 极低（纯文档 change，不影响 production 行为，pre-push backend-smoke A11 regression suite 30 测试不受影响）
- **Rollback**: `git revert` 单 commit 即可
- **Validation success criteria**:
  1. `npx openspec validate a11-phase0-plan-driven-exam-architecture --strict` 退出码 0
  2. `npx openspec status --change a11-phase0-plan-driven-exam-architecture` 显示 `Progress: 4/4 artifacts complete`
  3. lefthook chain (pre-commit / commit-msg / post-commit / pre-push) 全部通过
