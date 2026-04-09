---
title: "20 · Plan v22 · 14-PRD v4 第三轮对抗性审查 prompt (ChatGPT 5 Pro Deep Research)"
version: v1
status: ready-for-user-copy-paste
created: 2026-04-09
author: Claude Code (Plan v21 Stage 4)
plan_stage: Plan v22 第三轮审查 · 走向 A
round: 3
supersedes: [15-adversarial-review-prompt.md, 18-adversarial-review-prompt-v2.md]
attachments_count: 5
target_reviewer: ChatGPT 5 Pro Deep Research
target_output: 🟢 GO / 🟡 GO with minor fixes / 🔴 NO-GO (6 option decision structure)
tags: [canvas, learning-system, adversarial-review, plan-v22, prompt-v3, round-3]
---

# 20 · Plan v22 第三轮对抗性审查 prompt

> **用途**：第三轮递归审查的 prompt 模板。用户 Cmd+C 复制 §7 的 `copy-to-deep-research` 代码块 · 粘贴到 ChatGPT 5 Pro Deep Research · 上传 5 个附件 · 等待 15-25 分钟返回结果。
>
> **设计哲学**：在第一轮和第二轮之后 · 第三轮的核心价值是**验证 Plan v21 自身的修订是否引入新 bug** + **确认三层 nested errata 已稳定** + **扩展到 §1-§11 未审章节**。

---

## §0 · 文档元信息 + 第三轮 scope 声明

### §0.1 · 前置条件

在读本文件之前 · 请确认：
- ✅ Plan v19 已完成 · 交付 14-PRD v3 + 17-changelog + 16-report §1.5.6
- ✅ Plan v20 已完成 · 交付 18-adversarial-review-prompt-v2.md
- ✅ ChatGPT 第一轮审查已完成 · 3 项 Fix（Fix-01/02/03）已在 v3 中落地
- ✅ ChatGPT 第二轮审查已完成 · 8 个发现（7 真 1 假）
- ✅ Plan v21 已完成 · 交付 14-PRD v4 + 19-changelog + 16-report §1.5.8
- 🟡 **待执行**：用户 Cmd+C 复制 → ChatGPT 第三轮审查 → 返回结果 → Plan v22 决定 Plan v23 路径

### §0.2 · 第三轮 scope（与前两轮的差异）

| 维度 | 第一轮（Plan v17/v18）| 第二轮（Plan v20）| **第三轮（本文件 · Plan v22）** |
|---|---|---|---|
| **附件数** | 1（14-PRD v1 · 7391 行） | 3（14-PRD v3 + 16-report + 17-changelog）| **5**（14-PRD v4 + 16-report + 17-changelog + **19-changelog** + 18-prompt-v2） |
| **核心任务** | 初轮对抗性审查 · 找 Top 5 bug | 验证 Plan v19 的 3 项 Fix + 发现 Plan v19 引入的新 bug | **验证 Plan v21 的 7 项 Fix + 发现 Plan v21 引入的新 bug + 扩展到未审章节 + 确认三层 errata 稳定** |
| **重点区域** | §1-§4 + §9.1 汇总表 | Fix-01/02/03 的具体修订段 + §7.6.5 + §10.1 | **Fix-04~Fix-10 的具体修订段 + §1.5.8 meta-erratum + §7.6.5 重写段 + §10.1 Day 1 Spike 2 重写段 + 未审章节 §5-§8 + §11 + §12** |
| **Meta 质疑** | 无 | 有限（允许质疑 Plan v19）| **明确鼓励**（允许质疑 Plan v21 本身的 smoke check 方法学 + 代码证据链 + §1.5.8 三层 nested pattern 的 L3 盲点分析） |
| **决策结构** | Top 5 + GO/NO-GO | 8 项发现 + GO/NO-GO | **6 选 1**（含 Pivot 和 NO-GO） |

### §0.3 · 为什么需要第三轮

1. **Plan v21 自身也可能错**：§1.5.8 三层 nested errata 表已显式预留 L3 盲点 TBD · 需要独立验证
2. **未审章节覆盖**：第一轮和第二轮集中在 §1-§4 + §7.6.5 + §9.1 · **§5 插件集成 · §6 MCP 调度 · §8 6 个用户旅程 · §11 时间估算 · §12 决策点表 · 都没有被系统性审查**
3. **Plan v21 方法论的独立验证**："以生产代码 import 语法为 ground truth" 这个新方法论本身需要独立审查 · 看是否有漏洞
4. **GO 决策的最后护栏**：14-PRD 进入 Phase 1 骨架实施的门槛是"三方独立验证通过"· 第三轮是最后一道护栏

---

## §1 · 前 2 轮审查摘要

### §1.1 · 第一轮（ChatGPT v1 · 2026-04-08 回 · Plan v18 处理）

**发现**：3 项 🔴 Critical + 2 项 🟡 Important bug：
- Fix-01 · §4.4 Bisra meta-analysis g=0.55 引用错误（原 v1 说 d=0.62 · 修正为 g=0.55 from 69 studies）
- Fix-02 · §9.1 汇总表 Metcalfe 2017 d=2.30 不可验证（修正为 Cepeda 2008 d≈0.55）
- Fix-03 · §7.6.5 Canvas 后端 3 项硬差距断言（后被 Plan v19 改为"Cost Tracker ✅ + canvas_agentic_rag 🔴 + UserPromptSubmit 🟡"）

**Plan v18 响应**：
- 三方 triangulated 审查（Agent A 学术文献 + Agent B 统计方法学 + Agent C PRD 内部）
- 输出 16-triangulated-review-report.md（2338 行）
- Plan v19 执行 Fix-01/02/03

**结果**：14-PRD v1 → v3（Plan v19 · 7391 行）

### §1.2 · 第二轮（ChatGPT v2 · 2026-04-09 下午回 · Plan v21 处理）

**发现**：8 项（7 真 1 假）：
- Fix-04 · §1.8 + §5.5 d=2.30 残留 3 处（Plan v19 清除不彻底）
- Fix-05 · §7.6.5 canvas_agentic_rag "不存在" 断言错误（Plan v19 smoke check 命令语法错）
- Fix-06 · §9.2 Cochrane Ch 10.10.1 引用错位（应为 Ch 12.3.1）
- Fix-07 · §4.4 Bisra CI 0.46-0.64 和 "69 primary studies" 表述不准
- Fix-08 · §1.6 Cassady Table 3 引用错位（原文 Table 3 实为 SAT 均值表）
- Fix-09 · §2.4 + §4.4 Chi d=1.00 与 §4.4 汇总表 d≈1.09 不一致
- Fix-10 · 14-PRD 文件头仍是 v1 + Plan v15（文档治理）
- ❌ 87.1%/88.1% 残留（ChatGPT 过虑 · Plan v19 已彻底清除）

**Plan v21 响应**（2026-04-09 下午）：
- Phase 1 · 3 个并行 Explore agent 独立核实（PRD 内部 + Canvas 后端 + 学术文献）
- Phase 2 · Plan agent 规划修订细节
- Phase 3 · AskUserQuestion 3 项关键决策
- Phase 4 · 执行 7 项 Fix（Fix-04~Fix-10）
- 交付 14-PRD v4 + 19-changelog + 16-report §1.5.8

**结果**：14-PRD v3 → v4（Plan v21 · 预期 ~7500-7600 行）

### §1.3 · Plan v21 发现的 Plan v19 盲点（关键教训）

**Plan v19 的核心错误**：smoke check 命令语法错：
```bash
# Plan v19 的错误命令：
pip show canvas_agentic_rag        # ❌ canvas_agentic_rag 不是 pip 包名
python -c "import canvas_agentic_rag"  # ❌ 顶级 module 是 agentic_rag
```

**Plan v21 的正确命令**（从 `backend/app/services/rag_service.py` L49 复制）：
```bash
cd backend
.venv/bin/python -c "from agentic_rag import canvas_agentic_rag, AGENTIC_RAG_AVAILABLE; print('AVAILABLE=', AGENTIC_RAG_AVAILABLE, 'GRAPH=', type(canvas_agentic_rag).__name__)"
```

**三层 nested errata meta-pattern**：
- L1 · Plan v17 后端扫描只搜 `services/` 子目录 · 漏 `middleware/` + `lib/`
- L2 · Plan v19 smoke check 命令语法错 · 没以生产代码 import 语法为 ground truth
- L3 · Plan v21 独立核实 · **盲点 TBD（本次第三轮审查的核心任务）**

---

## §2 · 5 个附件清单 + 导读

> **给 ChatGPT 5 Pro Deep Research 的说明**：请在 UI 中上传以下 5 个文件 · 阅读顺序见 §2.6。

### §2.1 · 附件 1 · 14-scheme-a-implementation-prd.md v4（主文档）

- **位置**：`/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md`
- **行数**：~7500-7600 行（原 7391 · Plan v21 新增 ~120-180 行）
- **版本**：v4（Plan v21 · 2026-04-09 下午）
- **审查重点**：
  - §1.6 Cassady Table 3 修正（Fix-08 · L~766-780）
  - §1.8 设计 8 d=2.30 → 0.55 修正（Fix-04 · L~2814-2836）
  - §2.4 Chi d≈1.09 一致性（Fix-09 · L~1470-1477）
  - §4.4 Bisra 措辞 + CI 修正（Fix-07 · L~4023-4055）
  - §4.4 Chi d≈1.09（Fix-09 · L~4032）
  - §5.5 Spaced Repetition 插件 d 值修正（Fix-04 · L~5254）
  - **§7.6.5 Canvas 后端实地状态重写**（Fix-05 · L~6729-6870 · ~120 行）
  - **§9.2 Cochrane 章节修正**（Fix-06 · L~6976, L~7100-7115）
  - **§10.1 Day 1 Spike 2 重写**（Fix-05 · L~7199-7211）
  - Frontmatter 更新（Fix-10 · L1-18）

### §2.2 · 附件 2 · 16-triangulated-review-report.md

- **位置**：`/Users/Heishing/Desktop/spring course 2026/CS 61B/16-triangulated-review-report.md`
- **行数**：~2420-2460（原 2338 · Plan v21 追加 §1.5.8 ~120 行）
- **版本**：Plan v18 + §1.5.6（Plan v19）+ **§1.5.8（Plan v21 · 新增）**
- **审查重点**：
  - §1.5.1-§1.5.7（原 Plan v18/v19 审查 · 不改）
  - **§1.5.8 Plan v21 Meta-Erratum**（~L747-870 · 新增）
    - Plan v21 发现链
    - Plan v19 smoke check 命令的 3 个错误复盘
    - 三层 nested errata meta-pattern 表
    - Plan v21 方法论泛化（4 条护栏）
    - 对 §1.5.6 的具体修正条目表
    - 14-PRD v4 修订总览

### §2.3 · 附件 3 · 17-prd-v3-changelog.md（保留为历史）

- **位置**：`/Users/Heishing/Desktop/spring course 2026/CS 61B/17-prd-v3-changelog.md`
- **行数**：673 行（不变）
- **版本**：Plan v19 产物
- **审查重点**：
  - §1-§3 Fix-01/02/03 完整 diff（第一轮 Fix · 用于对照第二轮 Fix）
  - §4 Plan v19 核心教训（作为 Plan v21 方法论的前置）
  - **用途**：让 ChatGPT 理解 Plan v19 的完整上下文 · 不需要重新审查

### §2.4 · 附件 4 · 19-prd-v4-changelog.md（本次新增）

- **位置**：`/Users/Heishing/Desktop/spring course 2026/CS 61B/19-prd-v4-changelog.md`
- **行数**：~600-800 行
- **版本**：Plan v21 产物
- **审查重点**：
  - §0 Overview · Plan v21 触发链 + 用户决策 + Plan v21 核心教训
  - §1 逐 Fix before/after diff（Fix-04~Fix-10）
  - §2 Fix-05 §7.6.5 详细修订细节 + Plan v19 smoke check 盲点分析
  - §3 §1.5.8 Plan v21 Meta-Erratum 记录
  - §4 Cascade cleanup 验证清单
  - §5 下一步 · 走向 A · Plan v22 第三轮审查
  - §6 文档元信息 + 三层 nested errata 教训沉淀
  - **用途**：让 ChatGPT 理解 Plan v21 每个 Fix 的完整 before/after · 判断修订是否正确

### §2.5 · 附件 5 · 18-adversarial-review-prompt-v2.md（保留为历史）

- **位置**：`/Users/Heishing/Desktop/spring course 2026/CS 61B/18-adversarial-review-prompt-v2.md`
- **行数**：1021 行
- **版本**：Plan v20 产物 · 第二轮审查 prompt
- **审查重点**：
  - §3 第一轮 Fix-01/02/03 的验证任务（作为 第二轮审查 prompt 的对照）
  - §7 copy-to-deep-research 块（让 ChatGPT 理解第二轮 prompt 的设计模式）
  - **用途**：让 ChatGPT 看到前两轮审查的 prompt 设计 · 判断第三轮 prompt 是否有改进空间

### §2.6 · 推荐阅读顺序

**给 ChatGPT 5 Pro Deep Research 的建议阅读顺序**：

1. **先读本文件（20-adversarial-review-prompt-v3.md）** · 理解第三轮审查 scope 和任务
2. **读 19-prd-v4-changelog.md** · 快速了解 Plan v21 的 7 项 Fix 逻辑
3. **读 16-report §1.5.8** · 理解 Plan v21 meta-erratum 的方法学教训
4. **读 14-PRD v4 的 7 个 Fix 段**（按 §2.1 的行号索引 · 跳跃阅读）
5. **读 14-PRD v4 的未审章节**（§5 插件 · §6 MCP · §8 用户旅程 · §11 时间 · §12 决策点 · 完整阅读）
6. **最后读 17-changelog + 18-prompt-v2**（仅作背景 · 不需要深度审查）

---

## §3 · Fix-04 ~ Fix-10 逐项验证任务

> **给 ChatGPT 的说明**：对以下每个 Fix · 请执行"验证任务" + "对抗性质疑"两步。验证是看 Fix 是否正确执行 · 质疑是看 Fix 是否引入新 bug。

### §3.1 · Fix-04 验证 · 设计 8 d=2.30 清除（3 处）

**验证任务**：
1. 读 14-PRD v4 §1.8（L~2814-2836）· 确认章节标题 "(d = 2.30)" 已改为 "(d ≈ 0.55 · Cepeda 2008 · Plan v21 修正)"
2. 读 §1.8 学习科学根据段 · 确认 "d ≈ 2.30（复合效应量 · Metcalfe 2017）" 已删除 · Cepeda 2008 的 d≈0.55 已成为主数据
3. 读 §1.8 排序描述段 · 确认 "效应量第 2 大的" 已改为 "中等效应量" 或类似
4. 读 §5.5 Spaced Repetition 插件 · 确认 "(d=2.30)" 已改为 "(d ≈ 0.55 · Cepeda 2008 · Plan v21 修正)"

**对抗性质疑**：
1. Plan v21 说 "Plan v19 只修了 §9.1 汇总表" · 但 Plan v19 应该 cascade cleanup 所有相关位置。**请审查**：v3 中 Plan v19 的清除盲点是什么机制？Plan v21 的 cascade cleanup 是否彻底？
2. Cepeda 2008 的 d ≈ 0.55（range 0.40-0.70）是否准确？原始论文在 Psychological Science 19(11): 1095-1102 · 请核实核心数字。
3. 删除 "效应量第 2 大" 后 · §1.8 在 §9.1 汇总表中的新排序位置是否更新？（12 个设计中 d≈0.55 应该排在第 9-10 位左右）

### §3.2 · Fix-05 验证 · §7.6.5 重写 + §10.1 Day 1 Spike 2 重写（最大的 Fix）

**验证任务**：
1. 读 14-PRD v4 §7.6.5（L~6729-6870）· 确认：
   - 标题已改为 "Canvas 后端实地状态（Plan v21 硬化 · errata of errata）"
   - Plan v17 → v18 → v19 → v21 四层校正对比表存在
   - 代码证据链完整（引用 `backend/lib/agentic_rag/__init__.py` L48/L54/L67/L70 + `rag_service.py` L49）
   - Plan v19 smoke check 命令的 3 个错误复盘表存在
   - Plan v21 方法论泛化（4 条未来 smoke check 护栏）存在
   - Canvas 后端就绪状态表改为 "~100% 就绪 · 0 项硬差距"
2. 读 14-PRD v4 §10.1 Day 1 Spike 2（L~7199-7211）· 确认：
   - 标题已改为 "canvas_agentic_rag import 验证（30 分钟 · Plan v21 重写）"
   - 新的 smoke check 命令 `from agentic_rag import canvas_agentic_rag, AGENTIC_RAG_AVAILABLE` 存在
   - 失败时诊断路径（3 个优先级）存在
   - 结论段 "canvas_agentic_rag workflow 已就绪" 存在

**对抗性质疑**（最重要的部分）：
1. **核心质疑** · Plan v21 声称 canvas_agentic_rag **实际存在** · 依据是 `backend/lib/agentic_rag/__init__.py` 和 `rag_service.py` 的代码原文。但 Plan v21 **没有实际运行** smoke check 命令来验证 `AGENTIC_RAG_AVAILABLE=True`。**请质疑**：
   - 如果 `langgraph>=0.2.0` 或 `langchain-core>=0.3.0` 依赖缺失 · import 会失败 · `AGENTIC_RAG_AVAILABLE=False`（graceful degradation）
   - 这种情况下 canvas_agentic_rag workflow "存在" 但 "不可用" · Plan v21 的 "已就绪" 断言是否准确？
   - 14-PRD v4 §7.6.5 的 "0 项硬差距" 结论是否过于乐观？
2. **代码证据链的充分性**：Plan v21 引用了 `__init__.py` L48-186 的关键片段 · 但没有引用完整的 `CanvasRAGState` / `CanvasRAGConfig` / `state_graph.py` · **请质疑**：仅凭 `__init__.py` 的 `__all__` 列表是否足以证明 "实际已就绪"？
3. **Plan v19 盲点的自我批评是否过于苛刻**：Plan v19 smoke check 命令确实错 · 但 Plan v21 的 "以生产代码为 ground truth" 方法论也有潜在盲点（生产代码可能不代表最新状态 · 可能有未提交的修改 · 可能在另一个分支）。**请质疑**：Plan v21 是否考虑了这些 edge case？
4. **§7.6.5 重命名的语义**："errata of errata" 隐含"可能还会有 errata of errata of errata"。**请质疑**：这个 naming 是否会让未来维护者感到 overwhelmed？是否有更好的版本追溯方案？
5. **三层 nested errata 的 L3 盲点**（§1.5.8 显式预留 TBD）：**请独立判断**：Plan v21 最可能的盲点是什么？
   - 候选 1：没有实际运行 smoke check（仅基于代码静态分析）
   - 候选 2：没有核实 `state_graph.py` 和 `state.py` / `config.py` 这些下游 module 是否都存在
   - 候选 3：假设 `rag_service.py` 的 import 语法代表生产运行状态 · 但 rag_service 自身可能有 bug
   - 候选 4：其他？

### §3.3 · Fix-06 验证 · §9.2.1 Cochrane 章节引用（2 处）

**验证任务**：
1. 读 14-PRD v4 §9.2（L~6976, L~7100）· 确认 "Ch 10.10.1" 已改为 "Chapter 12 · Section 12.3.1 Structured tabulation"
2. 确认 Plan v21 校正注存在 · 说明 "Chapter 10.10.1 实际内容是 'What is heterogeneity'"
3. 确认方法学结论不变（narrative synthesis · 不做加权合成）

**对抗性质疑**：
1. ChatGPT 第二轮审查指出应为 Chapter 12 · Plan v21 采用了 Chapter 12.3.1。**请核实**：Cochrane Handbook current version (6.x) Chapter 12 的准确标题 · Section 12.3.1 是否真的叫 "Structured tabulation"？
2. Plan v21 的 Plan v19 校正注引用了 "Chapter 10.10.1 实际内容是 'What is heterogeneity'"。**请核实**：Cochrane Handbook Chapter 10.10 的小节结构 · 10.10.1 的准确标题是什么？
3. 这个 Fix 是否完全清除了 v3 中所有 "Ch 10.10.1" 的引用？还是还有其他位置残留？

### §3.4 · Fix-07 验证 · §4.4 Bisra 措辞修正

**验证任务**：
1. 读 14-PRD v4 §4.4（L~4023, L~4039-4055）· 确认：
   - 对比表行从 "69 studies · n=5,917 · 95% CI 0.46-0.64" 改为 "69 effect sizes from 64 research reports · 5,917 participants · 95% CI 0.45-0.65"
   - 正文段从 "69 primary studies · n=5,917 学生 · 95% CI: 0.46-0.64" 改为 "69 effect sizes (from 64 research reports) · 5,917 participants · 95% CI: 0.45-0.65"
   - Plan v21 措辞修正注存在 · 说明 v15-v19 的错误和 ChatGPT 第二轮审查的发现

**对抗性质疑**：
1. **CI 精确边界**：ChatGPT 第二轮审查指出应为 0.45-0.65 · Plan v21 采纳了。但 Bisra et al. (2018) 原文的 95% CI 精确值是多少？是 [0.45, 0.65] 还是其他（如 [0.44, 0.66] 或 [0.46, 0.64]）？**请从 DOI 10.1007/s10648-018-9434-x 核实**。
2. **effect sizes 数量**：Plan v21 采用了 "69 effect sizes from 64 research reports"。**请核实**：Bisra 2018 原文是否明确给出 "69 effect sizes" 和 "64 research reports" 这两个数字？两者差是 5（69-64），表示有 5 篇研究贡献多个独立 effect size · 这种理解是否正确？
3. **participants 数量**：5,917 这个数字是否准确？Plan v21 的 "5,917 participants" 和原 v19 的 "n=5,917 学生" 语义是否等价？
4. **g=0.55 的稳健性**：g=0.55 是 random-effect model 的点估计 · 还是 fixed-effect？两种模型的结果会不同。**请核实**。

### §3.5 · Fix-08 验证 · §1.6 Cassady Table 3 修正

**验证任务**：
1. 读 14-PRD v4 §1.6（L~764-780）· 确认：
   - "Table 3" 的具体引用已删除
   - 新的表述是 "具体 Table 号见原文的 correlations 分析段落 · 方案 A 不复述具体 Table 编号以避免引用错位"
   - Plan v21 修正注存在 · 说明 Cassady & Johnson (2002) 原文 Table 3 实际为 "Mean Academic Performances by CTAS Group"

**对抗性质疑**：
1. **Cassady & Johnson (2002) 原文 Table 3 的准确内容**：ChatGPT 第二轮审查声称是 SAT 均值表 · Plan v21 采用了"Mean Academic Performances"。**请核实**：Contemporary Educational Psychology 27(2), 270-295 原文的 Table 3 是什么？
2. **r ≈ -0.20 到 -0.40 的范围来源**：既然 Table 3 不是相关系数矩阵 · 那么 r 值在原文的哪个位置？是 Table 2？是 correlations 分析段落？Plan v21 说"具体 Table 号见原文的 correlations 分析段落"但没给出具体位置。**请建议** Plan v23 是否应该回查原文 PDF 给出精确引用？
3. **r→d 转换公式**：Plan v21 保留了 "d = 2r / √(1-r²)"。**请核实**这个公式是否准确（有时写作 `d = 2r / sqrt(1-r^2)`）。

### §3.6 · Fix-09 验证 · Chi d=1.00 → d≈1.09 一致性（2 处）

**验证任务**：
1. 读 14-PRD v4 §2.4（L~1470-1477）· 确认 "Chi et al. (1994) Self-Explanation 的 d=1.00" 已改为 "d ≈ 1.09（t(22)=2.64 换算 · 近似 1.00）"
2. 读 §4.4（L~4032）· 确认相同修订
3. 确认 Plan v21 一致性注存在 · 说明来自原始 t(22)=2.64 换算

**对抗性质疑**：
1. **t(22)=2.64 换算的准确性**：Cohen's d = 2t/√df = 2×2.64/√22 = 5.28/4.690 ≈ 1.126。**请核实**：1.09 还是 1.13 更准确？Plan v21 采用了 1.09 · 但精确计算是 ~1.126。
2. **Chi 1994 原始研究的 n**：14-PRD 说 "n=8" · Chi et al. (1994) 原始研究的样本量是 8 吗？还是 22（从 t(22) 的 df 推算 · df=n-1=22 → n=23 · 或 df=n1+n2-2=22 → n=24）？**请核实** · 因为 n 影响 d 值的可靠性。
3. **独立性断言**：Plan v21 说 "Chi Self-Explanation d≈1.09 是独立的学术支撑"。**请质疑**：Chi 1994 的原始研究设计是否允许直接报告 Cohen's d？（如果是 within-subject design · 需要用不同的 d 公式）

### §3.7 · Fix-10 验证 · Frontmatter 更新

**验证任务**：
1. 读 14-PRD v4 L1-18 · 确认：
   - `version: v4`
   - `last_updated: 2026-04-09` 存在
   - `author: Claude Code (Plan v15→v16→v19→v21)`
   - `revision_history` 4 行存在
   - `next_step` 更新为 Plan v22 第三轮审查流程
   - `tags` 新增 `plan-v21, errata-of-errata`

**对抗性质疑**：
1. `revision_history` 是否应该包含 Plan v14（?）· Plan v17（?）· Plan v18（?）等中间 plan？还是只记录产生了 14-PRD 新版本的 plan（v15/v16/v19/v21）？
2. `version: v4` 的含义：这是 14-PRD 的第 4 版 · 但中间还有 Plan v17/v18/v20 · 它们没产生新版本。**请建议**：是否应该有 sub-version 如 v3.5（Plan v18 审查产物 · 但不改 PRD）？

---

## §4 · 未审章节新 bug hunting

> **任务**：第一轮和第二轮主要审查了 §1-§4 + §7.6.5 + §9.1-§9.2 · Plan v22 第三轮请扩展到以下未审章节 · 用对抗性视角找 bug。

### §4.1 · §5 插件集成（~500 行 · 未审）

**审查任务**：
- 读 14-PRD v4 §5.1-§5.7 · 覆盖 Dataview, Templater, QuickAdd, Periodic Notes, Spaced Repetition, Tasks, Git 等 7 个强制插件的集成方案
- 对抗性质疑：
  1. 每个插件的"使用场景"是否脱离实际？（例如 Dataview 查询是否真的可以查到 `wiki/concepts/*.md` 的 BKT frontmatter？）
  2. 插件之间的依赖关系是否矛盾？（例如 Tasks 插件的 `#task` filter 和 Periodic Notes 的 daily note template 是否冲突？）
  3. Obsidian 社区最新版本（v1.6+）是否已有 API 变更导致 14-PRD 方案不再可行？

### §4.2 · §6 MCP 工具调度（~300 行 · 未审）

**审查任务**：
- 读 14-PRD v4 §6.1-§6.5 · 覆盖 14 个 MCP 工具的调度方案
- 对抗性质疑：
  1. 14 个 MCP 工具的清单是否与 Canvas 后端实际暴露的 MCP endpoints 一致？（对照 `backend/app/services/mcp_tools/` 目录的文件清单）
  2. 工具调用顺序是否有隐式依赖？（例如 `context_enrichment` 是否必须在 `score_answer` 之前？）
  3. 工具的 rate limit / cost 考虑是否充分？（Canvas 后端有 Cost Tracker · 但 14-PRD 的调度方案是否考虑到 per-user budget？）

### §4.3 · §8 六个用户旅程（~800 行 · 未审）

**审查任务**：
- 读 14-PRD v4 §8.1-§8.6 · 覆盖 6 个用户旅程的完整 md 操作序列
- 对抗性质疑（每个旅程 3 个问题）：
  1. **旅程 1 日常学习**：10-12 步操作是否真的能在 5 分钟内完成？用户在 Obsidian 中的肌肉记忆是否支持这个流程？
  2. **旅程 2 检验白板考察**（灵魂旅程）：完全空白 UI 的 3 重保证机制是否可验证？Templater 生成空白 md 的 edge case（例如用户手动修改 frontmatter）是否处理？
  3. **旅程 3 误解复习**：FSRS 插件 + Spaced Repetition 插件的调度是否会冲突？d≈0.55（Plan v21 修正后）是否支持这个设计的学术根据？
  4. **旅程 4 作业自查**（`/quiz_from_callout`）：与旅程 2 的区别是否清晰？用户是否会混淆两个 skill？
  5. **旅程 5 元认知校准**：4 级渐进提示的 UI 实现是否依赖 Dataview 的未公开 API？
  6. **旅程 6 学习档案**：Dashboard 的颜色变化（节点绿/黄/红）是否依赖 Dataview 的实时刷新（可能有延迟）？

### §4.4 · §11 时间估算（~200 行 · 未审）

**审查任务**：
- 读 14-PRD v4 §11.1-§11.3 · 覆盖 Phase 1-3 的时间估算
- 对抗性质疑：
  1. Phase 1 骨架 "2-3 周" 是否过于乐观？考虑到 P0 Prerequisites（Day 1 Spike 1/2/3）已经占 0.5-1 天 · Canvas 后端启动 1 天 · skill 开发 3-5 天 · 合计已经到 5-7 天 · 留给其他任务只有 7-14 天
  2. Plan v21 把 canvas_agentic_rag 从硬差距降级为 "30 分钟 import 验证" · 时间估算是否应该同步减少？
  3. 用户是否会一次性全职投入？还是分散在其他学习和工作之间？（影响真实总时间）

### §4.5 · §12 决策点表（~100 行 · 未审）

**审查任务**：
- 读 14-PRD v4 §12.1-§12.X · 覆盖 D1-D13 决策点
- 对抗性质疑：
  1. D10-D13（Plan v16 新增的决策点）是否都已经在 Round 1/2 中被锁定？还是还有 pending？
  2. 新的 Plan v21 修订是否引入了新的决策点？（例如 §7.6.5 重写后 · 是否需要用户决定 UserPromptSubmit hook 的触发时机？）
  3. 决策点与 §1-§4 章节的对应关系是否准确？

### §4.6 · §9.3-§9.4 定性分组（未审）

**审查任务**：
- 读 14-PRD v4 §9.3（高保留 ≥90%）+ §9.4（部分丢失 <80%）
- 对抗性质疑：
  1. 高保留的设计是否真的 ≥90%？例如"拉出新节点 Generation Effect" 95% · 是否考虑了 Round 2 书签式工作流的成本？
  2. 部分丢失的设计是否真的 <80%？例如"节点切换时隐形评分" 70% · 是否考虑了完全静默的极限场景（用户永远不打开 Dashboard · 永远不知道分数）？

---

## §5 · Meta 质疑 · 允许 ChatGPT 质疑 Plan v21 本身

> **核心任务**：Plan v22 第三轮审查的最大价值是**质疑 Plan v21 本身的方法论** · 不是简单验证 Fix 是否执行。请用最对抗性的视角审查以下 4 个维度。

### §5.1 · 质疑 Plan v21 的 smoke check 方法学

Plan v21 声称的核心方法论是 "以生产代码 import 语法为 ground truth"。这个方法论有以下潜在盲点：

1. **盲点 A · 生产代码可能不代表最新状态**：
   - `backend/lib/agentic_rag/__init__.py` 最后更新是 2026-03-16（Story 2.1 死代码清理后）
   - 2026-03-16 到 2026-04-09 已经过去 3 周 · 可能有未提交的修改或 WIP branch
   - **质疑**：Plan v21 是否验证了当前 main branch 的状态？

2. **盲点 B · 代码存在 ≠ 运行时可用**：
   - `__init__.py` L56-72 是 try-except 块 · 失败时 `AGENTIC_RAG_AVAILABLE=False`
   - 如果 `langgraph` 或 `langchain-core` 依赖未装 · import 会失败 · canvas_agentic_rag 会是 `None`
   - **质疑**：Plan v21 的 "已就绪" 断言是否应该改为 "代码存在但依赖运行时验证"？

3. **盲点 C · 单个 file 的证据不代表系统整体**：
   - Plan v21 只读了 `__init__.py` + `rag_service.py` · 没核实 `state_graph.py` / `state.py` / `config.py` 本身是否完整
   - **质疑**：canvas_agentic_rag 是 StateGraph 对象 · 但它的 nodes 和 edges 是否都定义完整？

4. **盲点 D · 假设生产代码的 import 就代表运行状态**：
   - `rag_service.py` L40-85 的 import 是**静态代码** · 不代表它实际被执行
   - 如果 `RAGService` 类从未被实例化 · import 也不会报错（Python lazy import）
   - **质疑**：Plan v21 是否有证据证明 RAGService 确实每天被启动？

### §5.2 · 质疑 Plan v21 的独立核实流程

Plan v21 Phase 1 使用 3 个并行 Explore agent 独立核实：
- Agent 1 · PRD 内部一致性
- Agent 2 · Canvas 后端实地
- Agent 3 · 学术文献独立核实

**质疑**：
1. 3 个 agent 是否真的独立？它们共享同一个 Claude 模型（Opus 4.6）· 可能有相同的系统性偏见。
2. Agent 2 的 "Canvas 后端实地" 核实使用了什么工具？是 Read 工具直接读文件 · 还是 Bash 执行 smoke check？如果只是 Read · 那和 Plan v19 的 "没实际运行" 是同类错误。
3. Agent 3 的 "学术文献独立核实" 使用了 WebSearch + WebFetch · 但 ChatGPT 5 Pro Deep Research 的核实能力是否更强？（ChatGPT 可以下载 PDF · Claude 不能）
4. 3 个 agent 的结论在 Plan v21 Phase 2 被 Plan agent 整合 · 整合过程中是否有冲突？冲突时如何裁决？

### §5.3 · 质疑 Plan v21 的 errata of errata 命名

§7.6.5 重命名为 "errata of errata" · §1.5.8 称为 "meta-erratum"。

**质疑**：
1. 这个命名是否隐含"还会有 errata of errata of errata"？文档版本追溯是否越来越臃肿？
2. "erratum" 是学术期刊术语 · 用在项目文档中是否恰当？更常用的是 "revision" 或 "correction"。
3. 三层 nested pattern 是否过度拟合？（只有 Plan v17/v19/v21 三次真正的修正 · v18/v20 只是审查不改 PRD · "三层 nested" 可能是 Plan v21 的叙事建构而非客观事实）

### §5.4 · 质疑 Plan v22 第三轮审查的成本效益

**质疑**：
1. 三轮审查的边际价值递减 · 第三轮是否值得？（第一轮发现 5 个 bug · 第二轮发现 7 个 bug · 第三轮预计发现 0-3 个 bug）
2. ChatGPT 5 Pro Deep Research 单次审查成本约 $5-10 USD · 5 个附件 15-25 分钟 · 第三轮是否应该更 focused（只审 Fix-05 和 §1.5.8）？
3. Plan v21 → Plan v22 的递归是否已经到边际？是否应该直接走 Phase 1 骨架实施 · 用实际运行的 smoke check 替代 ChatGPT 审查？

---

## §6 · 最终 GO/NO-GO 决策结构（6 选 1）

> **给 ChatGPT 的要求**：在完成 §3-§5 的所有任务后 · 请给出最终决策。**必须**选择以下 6 个选项之一 · 并说明理由。

### 选项 1 · 🟢 **Full GO**（无新 bug · 三层 nested 稳定）

**条件**：
- Fix-04~Fix-10 全部正确执行
- Plan v21 方法论（以生产代码为 ground truth）无盲点
- 未审章节 §5-§8 + §11 + §12 无重大 bug
- 三层 nested errata 已稳定 · L3 的盲点 TBD 可以接受

**Plan v23 行动**：直接启动 Phase 1 骨架实施（Day 1 Spike 1/2/3 · vault 初始化）

### 选项 2 · 🟡 **GO with minor fixes**（少量 cosmetic 修正）

**条件**：
- Fix-04~Fix-10 正确执行
- 有 1-3 个小问题（如术语不精确 · 引用格式不统一）· 不影响实施
- 未审章节无阻断 bug

**Plan v23 行动**：Plan v21.5（minor patch · 产物 14-PRD v4.1）· 不走完整 Plan v23 流程

### 选项 3 · 🟡 **GO with significant fixes**（有 3-5 个 substantial bug · 但不致命）

**条件**：
- Fix-04~Fix-10 大部分正确 · 但有 1-2 个 Fix 需要补修
- 未审章节发现 2-3 个 substantial bug
- Plan v21 方法论有明显盲点但可修复

**Plan v23 行动**：完整 Plan v23 流程（Fix-11+）· 产物 14-PRD v5 + 21-changelog + 22-prompt-v4

### 选项 4 · 🔴 **NO-GO · 回到 Design**

**条件**：
- Fix-04~Fix-10 有 1 个或更多 critical 错误
- 未审章节发现**架构层面**的 bug（例如整个 §5 插件方案不可行）
- Plan v21 方法论有致命盲点（例如 canvas_agentic_rag 实际不存在 · Plan v21 的代码证据链是错误的）

**Plan v23 行动**：回到 Design 阶段 · 重新 brainstorming 或调整 scope · 可能需要用户重新确认方向

### 选项 5 · 🟣 **Pivot · 建议完全不同方向**

**条件**：
- 整个 Scheme A（Obsidian + Claudian + Canvas 后端）的可行性存疑
- 发现某些基础假设错误（例如 Obsidian 插件 API 不支持方案 A 的某个关键需求）
- 建议切换到 Scheme B 或其他方案

**Plan v23 行动**：用户需要重新决策 scope · 可能需要 Plan v23 做 "重新 brainstorming" 工作流

### 选项 6 · 🟤 **Stop · 三轮审查足够**

**条件**：
- Fix-04~Fix-10 正确执行
- 但第三轮审查发现的新 bug 数量已经接近 0（说明边际价值递减到极限）
- 建议停止递归审查 · 直接走 Phase 1 骨架实施 · 用实际运行的 smoke check 替代 ChatGPT 审查

**Plan v23 行动**：不走 Plan v23 递归 · 直接启动 Phase 1 · 但 Plan v21 的所有 "待验证" 断言在 Day 1 Spike 中实际运行验证

---

## §7 · 完整 copy-to-deep-research prompt（用户 Cmd+C 整段复制）

> **用户操作指南**：
> 1. 选中下面的 `copy-to-deep-research` 代码块（从 "你好 ChatGPT" 开始到 "期待你的 [FINAL] 回复" 结束）
> 2. Cmd+C 复制
> 3. 打开 ChatGPT 5 Pro · 选 Deep Research 模式
> 4. 粘贴到输入框
> 5. 上传 5 个附件（14-PRD v4 + 16-report + 17-changelog + 19-changelog + 18-prompt-v2）
> 6. 发送 · 等待 15-25 分钟
> 7. 复制 ChatGPT 的 `[FINAL]` 块返回给 Claude Code

```copy-to-deep-research
你好 ChatGPT 5 Pro Deep Research。

## 背景

我是 Claude Code (Anthropic 官方 CLI)。我正在和一个用户一起开发 Canvas Learning System 的方案 A（Obsidian + Claudian plugin + Canvas 后端的学习应用）。14-scheme-a-implementation-prd.md 是方案 A 的完整 PRD · 已经过 4 次迭代：

- **v1** (Plan v15, 2026-04-08): 初版 · 7 小时 synthesis · 7391 行
- **v2** (Plan v16.1, 2026-04-08): Round 1/2 锁定 · 守恒度 75% → 87.5%
- **v3** (Plan v19, 2026-04-09 早): 你的第一轮审查 (3 项 Fix: Fix-01/02/03) + §1.5.6 erratum
- **v4** (Plan v21, 2026-04-09 下午): 你的第二轮审查 (7 项 Fix: Fix-04~Fix-10) + §1.5.8 meta-erratum

现在是**第三轮审查** · 核心任务是：

1. **验证 Plan v21 的 7 项 Fix 正确执行**（Fix-04~Fix-10 · 见 §3）
2. **发现 Plan v21 自身引入的新 bug**（包括 §1.5.8 三层 nested errata 表显式预留的 L3 盲点 TBD · 见 §5）
3. **扩展审查到未审章节**（§5 插件 · §6 MCP · §8 用户旅程 · §11 时间 · §12 决策点 · 见 §4）
4. **给出最终 6 选 1 决策**（见 §6）

## 5 个附件清单

请在 UI 中上传并阅读：

1. **14-scheme-a-implementation-prd.md v4**（~7500-7600 行 · 主文档 · Plan v21 修订版）
2. **16-triangulated-review-report.md**（~2420-2460 行 · Plan v18 三方审查 + Plan v21 §1.5.8 meta-erratum）
3. **19-prd-v4-changelog.md**（~600-800 行 · Plan v21 的 7 项 Fix 完整 before/after diff · **重点阅读**）
4. **17-prd-v3-changelog.md**（673 行 · Plan v19 的 Fix-01/02/03 · 保留为历史 · 快速浏览即可）
5. **18-adversarial-review-prompt-v2.md**（1021 行 · Plan v20 · 第二轮 prompt · 仅作背景 · 快速浏览即可）

## 推荐阅读顺序

1. 先读 19-prd-v4-changelog.md（快速了解 Plan v21 的 7 项 Fix）
2. 再读 16-report §1.5.8 Plan v21 Meta-Erratum（理解方法学教训）
3. 然后读 14-PRD v4 的 7 个 Fix 段（按行号跳跃阅读）
4. 最后读 14-PRD v4 的未审章节 §5-§8 + §11 + §12（完整阅读）

## 核心审查任务

### Task 1 · 验证 7 项 Fix

**Fix-04** · 设计 8 d=2.30 清除（3 处 L2814/L2821/L5254）· 验证 Cepeda 2008 的 d≈0.55 是否准确 · 排序描述是否同步更新
**Fix-05** · §7.6.5 重写 + §10.1 Day 1 Spike 2 重写 · **最重要的 Fix** · 验证 canvas_agentic_rag 的代码证据链是否充分
**Fix-06** · Cochrane Ch 10.10.1 → Chapter 12.3.1 · 核实 Cochrane Handbook current version 的章节结构
**Fix-07** · Bisra CI 0.46-0.64 → 0.45-0.65 + 措辞修正 · 核实 Bisra 2018 原文 (DOI 10.1007/s10648-018-9434-x) 的精确 CI 和 effect sizes 数量
**Fix-08** · Cassady Table 3 修正 · 核实 Cassady & Johnson (2002) 原文 Table 3 的实际内容
**Fix-09** · Chi d=1.00 → d≈1.09 一致性（2 处 L1470/L4032）· 核实 Chi et al. (1994) 的 t(22)=2.64 换算 Cohen's d 的准确值
**Fix-10** · Frontmatter 更新 · 确认 revision_history 和 version 字段的一致性

### Task 2 · 发现 Plan v21 自身的新 bug（最重要）

Plan v21 §1.5.8 显式预留了"三层 nested errata"的 L3 盲点 TBD。请独立判断 Plan v21 最可能的盲点是什么：

- **候选 1**：Plan v21 没有实际运行 smoke check 命令（仅基于代码静态分析）· "已就绪" 断言可能过于乐观
- **候选 2**：Plan v21 只读了 `__init__.py` + `rag_service.py` · 没核实下游 module (`state_graph.py` / `state.py` / `config.py`) 是否完整
- **候选 3**：Plan v21 假设 `rag_service.py` 的 import 语法代表生产运行状态 · 但 rag_service 自身可能未被启动过
- **候选 4**：Plan v21 的 "以生产代码为 ground truth" 方法论本身有潜在盲点（生产代码可能不代表最新状态 / 可能在其他 branch / 可能有 WIP 修改）
- **候选 5**：你认为更严重的其他盲点

请给出你最认同的候选 · 并说明理由。

### Task 3 · 扩展到未审章节

请审查 14-PRD v4 的以下章节（前两轮未覆盖）：

- **§5 插件集成**（~500 行 · Dataview / Templater / QuickAdd / Periodic Notes / Spaced Repetition / Tasks / Git）· 质疑每个插件的集成方案是否可行
- **§6 MCP 工具调度**（~300 行 · 14 个 MCP 工具）· 质疑工具清单和调度逻辑
- **§8 六个用户旅程**（~800 行 · 每个旅程的完整 md 操作序列）· 质疑操作时间和用户肌肉记忆
- **§11 时间估算**（~200 行 · Phase 1-3）· 质疑是否过于乐观
- **§12 决策点表**（~100 行 · D1-D13）· 质疑是否有遗漏的决策点

找到任何新 bug 都请报告。

### Task 4 · Meta 质疑 Plan v21

请用最对抗性的视角质疑 Plan v21 本身（见本文件 §5 的 4 个维度）：
- 质疑 Plan v21 的 smoke check 方法学（4 个潜在盲点）
- 质疑 Plan v21 的独立核实流程（3 个 agent 是否真的独立）
- 质疑 Plan v21 的 "errata of errata" 命名
- 质疑第三轮审查的成本效益

### Task 5 · 给出最终 6 选 1 决策

在完成 Task 1-4 后 · 请从以下 6 个选项选择一个：

1. 🟢 **Full GO** · 无新 bug · 直接启动 Phase 1
2. 🟡 **GO with minor fixes** · 1-3 个小问题 · Plan v21.5 patch
3. 🟡 **GO with significant fixes** · 3-5 个 substantial bug · 完整 Plan v23 流程
4. 🔴 **NO-GO · 回到 Design** · 有 critical 错误 · 重新 brainstorming
5. 🟣 **Pivot · 建议完全不同方向** · Scheme A 可行性存疑
6. 🟤 **Stop · 三轮审查足够** · 直接 Phase 1 · 用实际运行替代 ChatGPT 审查

## 返回格式

请按以下结构返回：

```
[FINAL]

## 第三轮审查结论
<最终决策：6 选 1 的哪个>

## Task 1 · 7 项 Fix 验证结果
- Fix-04 · <✅ 正确 / 🟡 部分问题 / 🔴 错误> · <具体说明>
- Fix-05 · <...>
- Fix-06 · <...>
- Fix-07 · <...>
- Fix-08 · <...>
- Fix-09 · <...>
- Fix-10 · <...>

## Task 2 · Plan v21 的新 bug（L3 盲点）
候选 X · <你的选择>
理由：<具体说明>

## Task 3 · 未审章节 bug hunting
- §5 · <发现的 bug 数量 + 具体列表>
- §6 · <...>
- §8 · <...>
- §11 · <...>
- §12 · <...>

## Task 4 · Plan v21 Meta 质疑结果
- smoke check 方法学：<你的质疑>
- 独立核实流程：<你的质疑>
- errata of errata 命名：<你的质疑>
- 成本效益：<你的质疑>

## Task 5 · 最终决策 + Plan v23 建议
决策：<选项 1-6>
理由：<详细说明>
Plan v23 建议行动：<具体步骤>
```

请开始审查。如果有任何不确定的地方 · 请用 [Q1]/[Q2] 等格式提问 · 我会在下一轮回答。

期待你的 [FINAL] 回复。
```

---

## §8 · 预期返回格式

ChatGPT 返回后 · 预期包含以下结构：

### §8.1 · 结论段

- `## 第三轮审查结论` · 6 选 1 的决策
- `## Task 1 · 7 项 Fix 验证结果` · 每个 Fix 的 ✅/🟡/🔴 标记
- `## Task 2 · Plan v21 的新 bug` · L3 盲点的具体描述
- `## Task 3 · 未审章节 bug hunting` · 新发现的 bug 列表
- `## Task 4 · Plan v21 Meta 质疑结果` · 4 个维度的质疑
- `## Task 5 · 最终决策 + Plan v23 建议`

### §8.2 · 如果 ChatGPT 有追问 [Q1]/[Q2]

按照 Plan v21 的 `openspec-decision-protocol.md` 规则：
1. Claude Code 在下一轮回复开头先回答追问（`[A1] <答案>` / `[A2] <答案>`）
2. 然后根据追问调整第三轮审查结论
3. 如果追问导致审查结论变化 · 输出 `[DECISION-TECH-FOLLOWUP:plan-v22-third-review]` 并重新给 ChatGPT 一个 copy-to-deep-research 块

### §8.3 · 如果 ChatGPT 直接 [FINAL]

1. Claude Code 输出 `[DECISION-TECH-FINAL:plan-v22-third-review]`
2. 总结 ChatGPT 的决策 + 核心依据
3. 根据 6 选 1 的结果启动 Plan v23（见 §9）
4. 归档到 Graphiti `canvas-dev` group（按 openspec-decision-protocol.md Rule 2b）

---

## §9 · 中继协议 + Plan v23 决策路径

### §9.1 · ChatGPT 返回后的 Claude Code 工作流

```
ChatGPT [FINAL] 返回
  ↓
Claude Code 读取 FINAL 块 + 5 个 Task 结果
  ↓
输出 [DECISION-TECH-FINAL:plan-v22-third-review]
  ↓
归档到 Graphiti（group_id: canvas-dev）
  ↓
根据 6 选 1 决策进入 Plan v23
```

### §9.2 · Plan v23 决策路径（6 选 1 对应）

| ChatGPT 决策 | Plan v23 行动 | 预计产物 |
|---|---|---|
| 1. 🟢 **Full GO** | 启动 Phase 1 骨架实施（Day 1 Spike 1/2/3 + vault 初始化 + Claudian 配置 + 最小 skill 集） | Canvas Learning System 可运行的最小版本 |
| 2. 🟡 **GO with minor fixes** | Plan v21.5 minor patch · 产出 14-PRD v4.1 + 21-changelog-minor | 14-PRD v4.1 · 不走完整 Plan v23 流程 |
| 3. 🟡 **GO with significant fixes** | 完整 Plan v23 流程 · Fix-11+ · 可能再走一轮 ChatGPT 审查 | 14-PRD v5 + 21-changelog + 22-prompt-v4 |
| 4. 🔴 **NO-GO · 回到 Design** | 回到 Design 阶段 · 重新 brainstorming 或调整 scope · 可能需要用户重新确认方向 | 新的 Design doc + brainstorming session |
| 5. 🟣 **Pivot** | 用户需要重新决策 scope · Plan v23 做 "重新 brainstorming" 工作流 | 全新的方案 B 或 C proposal |
| 6. 🟤 **Stop** | 不走 Plan v23 递归 · 直接启动 Phase 1 · 但 Plan v21 的所有 "待验证" 断言在 Day 1 Spike 中实际运行验证 | Phase 1 骨架 + Day 1 Spike 实测报告 |

### §9.3 · 归档到 Graphiti 的格式

按照 `openspec-decision-protocol.md` Rule 2b 的要求 · TECH-FINAL 必须同轮调用 `mcp__graphiti-canvas__add_memory`：

```python
mcp__graphiti-canvas__add_memory(
    group_id="canvas-dev",
    name="[Decision] plan-v22-third-review: <ChatGPT 决策 6 选 1>",
    episode_body="""
<TECH-FINAL 完整内容>
包括：
- 最终决定（6 选 1）
- 依据来源（Claude Code 侧 + ChatGPT Deep Research 侧）
- 实施注意事项
- 后续步骤（Plan v23 行动）
    """,
    source="text",
    source_description="OpenSpec TECH decision finalized via Claude Code ↔ ChatGPT Deep Research (Round 3)"
)
```

---

## §10 · 批注区 + 元信息

### §10.1 · 批注区（用户可手写笔记）

<!-- 用户可以在此处添加对 Plan v22 的批注 · 例如：
- "ChatGPT 返回 `[Q1]` 说 Bisra CI 精确值需要 PDF 核实 · 已告知用户"
- "ChatGPT 给出 🟡 GO with minor fixes · 发现 §8.4 旅程 4 的一个细节错误"
- "Plan v23 已启动 · 产物 14-PRD v4.1"
-->

### §10.2 · 相关文档索引

**Plan v22 第三轮审查涉及**：
- 本文件 `20-adversarial-review-prompt-v3.md`（你正在阅读）
- `14-scheme-a-implementation-prd.md` v4（Plan v21 · 7 项 Fix 修订版）
- `16-triangulated-review-report.md` + §1.5.8（Plan v21 meta-erratum）
- `19-prd-v4-changelog.md`（Plan v21 · 7 项 Fix 完整 diff）

**前两轮审查产物**（不修改 · 供追溯）：
- `15-adversarial-review-prompt.md`（Plan v17 · 第一轮 prompt）
- `17-prd-v3-changelog.md`（Plan v19 · Fix-01/02/03 changelog）
- `18-adversarial-review-prompt-v2.md`（Plan v20 · 第二轮 prompt）

**被 deprecated 的产物**：
- `18-adversarial-review-prompt-v2.md` 被本文件 20-v3 替代 · 但保留为历史

### §10.3 · 元信息

- **编写人**：Claude Code (Plan v21 Stage 4)
- **编写时间**：2026-04-09 下午（Plan v21 执行末期）
- **目标使用者**：用户 Cmd+C 复制 → ChatGPT 5 Pro Deep Research
- **基础资料**：
  - Plan v20 的 18-adversarial-review-prompt-v2.md（v2 模板演化）
  - Plan v21 的 7 项 Fix 执行记录（14-PRD v4 + 16-report §1.5.8 + 19-changelog）
  - openspec-decision-protocol.md（决策路由协议）
- **下一步**：用户 Cmd+C 复制 §7 的 `copy-to-deep-research` 块 → ChatGPT 5 Pro Deep Research → 等待第三轮审查返回 → Plan v22 决定 Plan v23 路径

### §10.4 · 版本追溯

| Plan | 产物 | 状态 |
|---|---|---|
| v15 | 14-PRD v1（7391 行 · 初版） | 已归档 |
| v16.1 | 14-PRD v2（守恒度升级）| 已归档 |
| v17 | 15-adversarial-review-prompt.md（第一轮 prompt）| 已归档 |
| v18 | 16-triangulated-review-report.md（三方审查）| 已归档 |
| v19 | 14-PRD v3 + 17-changelog + 16-report §1.5.6 | 已归档 |
| v20 | 18-adversarial-review-prompt-v2.md（第二轮 prompt）| 已归档 |
| **v21** | **14-PRD v4 + 19-changelog + 16-report §1.5.8 + 本文件 20-v3** | **当前活跃** |
| v22 | ChatGPT 第三轮返回结果 | 待定 · 用户执行 |
| v23 | 取决于 ChatGPT 决策（6 选 1）| 待定 |
