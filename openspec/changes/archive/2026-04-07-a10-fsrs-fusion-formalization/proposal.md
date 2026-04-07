# Proposal: Formalize FSRS Fusion Architecture (A10)

## Why

A10 的原始问题（`docs/project-status/fr-exploration/A10.md`）：「FSRS 的算法是如何和其他的算法进行融合的，没有理清楚」。通过 4 次 Explore agent + 6 次源码行号实地核验，发现一个被忽略的架构事实：

1. **`backend/app/services/mastery_fusion.py` 已经实现 5 信号融合**（BKT/FSRS/Exam/Calibration/Confidence），含动态权重归一化 — 但 `compute_fused_mastery()` 在整个 backend **零外部调用点**
2. **`verification_service._advance_concept()` (L932-945) 直接 `idx++`** 进入 concept_queue 下一个，从不读 fused_mastery
3. **`recommendation_service.py` (L134) 按 confidence 排序**（confidence = max(L1 文本相似, L2 共享邻居数 / 3.0)），完全没有 mastery 字段
4. **`question_generator.py` (L114, L202-206) 用自己的 W1/W2/W3 公式** 调用 raw `p_mastery` 而非 `fused_mastery`

这形成**三套并行加权系统互相不读取彼此结果**的隐性架构。同时 `openspec/specs/algo-fusion/` 目录在仓库中存在但 `spec.md` 文件从未被创建（空 stub），意味着这个核心融合契约**从未被形式化为 OpenSpec 规范**。

本次 change 的目标：把 5 信号融合契约形式化为 `algo-fusion` capability 的首批 requirements，让 ChatGPT Deep Research 可以基于一份正式 spec 进行 review，而后续 verification/recommendation 接入工作可以作为独立 change 落地。**这是 RFC 性质的 change — 只 codify 现状，不修改任何代码行为**。

## What Changes

- **NEW** `openspec/specs/algo-fusion/` 首次填充内容：定义 5 信号注册表、动态权重归一化算法、Reliability 字段的 Phase 1 角色、fused_mastery 输出契约
- **NEW** `openspec/changes/a10-fsrs-fusion-formalization/design.md`：完整架构梳理 + 三套并行系统的代码层证据 + 7 个 ChatGPT review 提示问题
- **NEW** `docs/project-status/fr-exploration/A10-resolution-summary.md`：ChatGPT Deep Research review 入口文档，与 design.md 互相 link
- **NO CODE CHANGES**：本次 change 只 codify 现状，不修改 backend/frontend 行为
- **OUT OF SCOPE**（明确留给后续 change）：
  - 把 KG relevance 注册为 SignalRegistry 第 6 信号
  - 改 `_advance_concept()` 用 fused_mastery 排序
  - 改 recommendation 用 fused_mastery × confidence
  - 5 信号权重 ablation 实验
  - Reliability → Beta-Bayesian 加权激活

## Capabilities

### New Capabilities

- `algo-fusion`: 5 信号节点级 mastery 融合引擎契约（BKT × FSRS × Exam × Calibration × Confidence），含动态权重归一化、Reliability Phase 1 报告语义、输出范围约束。本次 change 是该 capability 的首次填充内容（之前是空 stub 目录）

### Modified Capabilities

（无 — 本次 change 不修改任何已存在的 spec。verification-service / canvas-recommendations / algo-question 的修改等 ChatGPT review 后做后续独立 change）

## Impact

- **正面**：A10 历史架构疑问被形式化记录；`algo-fusion` capability 不再是空 stub；后续 implementation change 有了 baseline 可以走 MODIFIED Requirements 路径
- **风险**：把现状写成 spec 可能"固化"了非最优设计（例如等权重归一化 0.30/0.25/0.25/0.10/0.10）。缓解方案：design.md 的 Open Questions section 显式列出需要 ChatGPT review 的设计选择，避免给读者"这就是终态"的错觉
- **依赖**：无新依赖。本次纯文档 + spec 形式化
- **影响的代码**：无（pure documentation）。引用证据涉及 `backend/app/services/{signal_registry,mastery_fusion,verification_service,recommendation_service,question_generator}.py`，但不修改它们
- **回滚方式**：`git revert <commit>` 即可。不会触发任何运行时行为变更
